# -*- coding: utf-8 -*-
"""Agent 记忆运行时挂钩 — 自主 prepare / record / compress.

- prepare_context: 聊天前注入 tone_hint + recall（受 Persona autonomy 控制）
- record_task_outcome: 任务完成/失败写运行日志 + 可选情绪
- record_perception: tool/步骤噪声 → 感知流，达阈值自动 compress
- EventBus 订阅 TASK_COMPLETED / TASK_FAILED
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .agent_memory_core import AgentMemoryCore, AgentMemoryStore, get_memory_store
from .agent_memory_lifecycle import (
    AgentMemoryLifecycle,
    MemoryLifecycleError,
    get_memory_lifecycle,
)

logger = logging.getLogger(__name__)

# 跳过记忆注入的 agent_id（系统内部）
_SKIP_AGENTS = frozenset({
    "skill_extractor",
    "tse_skill_extractor",
    "tse_silver",
    "__model_test__",
    "skill_verifier",
})


def _lc(store: Optional[AgentMemoryStore] = None) -> AgentMemoryLifecycle:
    if store is not None:
        return AgentMemoryLifecycle(store=store)
    return get_memory_lifecycle()


def _autonomy(meta_status: Dict[str, Any]) -> Dict[str, Any]:
    a = dict(meta_status.get("autonomy") or {})
    # 缺省：hybrid 行为
    a.setdefault("auto_log_on_task", True)
    a.setdefault("auto_perceive_on_tool", True)
    a.setdefault("auto_compress_threshold", 50)
    a.setdefault("auto_recall_on_chat", True)
    a.setdefault("auto_feel_on_outcome", True)
    a.setdefault("recall_min_importance", 3)
    a.setdefault("recall_k", 5)
    return a


def ensure_memory_ready(
    team_id: str,
    agent_id: str,
    *,
    store: Optional[AgentMemoryStore] = None,
    auto_bind: bool = True,
) -> Dict[str, Any]:
    """Ensure agent memory is usable; optionally auto-bind on first use."""
    if not team_id or not agent_id or agent_id in _SKIP_AGENTS:
        return {"ok": False, "reason": "skip"}
    store = store or get_memory_store()
    lc = _lc(store)
    if lc.is_tombstoned(team_id, agent_id):
        return {"ok": False, "reason": "destroyed"}
    st = lc.get_status(team_id, agent_id)
    state = st.get("state") or "unbound"
    if state == "unbound" and auto_bind:
        try:
            r = lc.transition(team_id, agent_id, "bind", reason="auto_first_use")
            return {"ok": True, "auto_bound": True, "status": r.get("status")}
        except MemoryLifecycleError as e:
            return {"ok": False, "reason": e.code}
    if state in ("destroyed",):
        return {"ok": False, "reason": state}
    return {"ok": True, "auto_bound": False, "status": st}


def prepare_memory_system_addon(
    team_id: str,
    agent_id: str,
    query: str = "",
    *,
    store: Optional[AgentMemoryStore] = None,
    max_chars: int = 1800,
    include_inherited: bool = True,
) -> str:
    """Return a short system-addon string for chat injection (may be empty).

    仅面向该 agent 的私有上下文；继承分区条目带「继承自…」来源，不伪装本地经历。
    """
    if not team_id or not agent_id or agent_id in _SKIP_AGENTS:
        return ""
    store = store or get_memory_store()
    # 首次对话/任务自动 bind，避免「有 Agent 无记忆」静默空注入
    ready = ensure_memory_ready(team_id, agent_id, store=store, auto_bind=True)
    if not ready.get("ok"):
        return ""
    lc = _lc(store)
    try:
        lc.assert_readable(team_id, agent_id)
    except MemoryLifecycleError:
        return ""
    st = lc.get_status(team_id, agent_id)
    if st.get("state") in ("unbound", "destroyed", "transferring"):
        return ""
    auto = _autonomy(st)
    if not auto.get("auto_recall_on_chat", True):
        # 仍可只给 tone
        pass

    try:
        core = AgentMemoryCore(team_id, agent_id, store=store)
    except Exception:
        return ""

    parts: List[str] = [
        "[AG_MEMORY]",
        "以下为该智能体拟生记忆提供的上下文（痕迹+语义+电荷；非用户原文）：",
    ]
    if core.is_sealed():
        parts.append("披露：这是回放，不是本人")

    # 语气（电荷场）
    try:
        tone = core.affect.tone_hint()
        if tone:
            parts.append(f"语气提示：{tone}")
    except Exception:
        pass

    # 情节检索
    if auto.get("auto_recall_on_chat", True) and (query or "").strip():
        try:
            k = int(auto.get("recall_k") or 5)
            min_imp = int(auto.get("recall_min_importance") or 1)
            hits = core.log.recall(query=query.strip(), k=max(1, min(k, 8)))
            lines = []
            for h in hits:
                e = h.get("event") or {}
                if int(e.get("importance") or 0) < min_imp:
                    continue
                lines.append(
                    f"- [{e.get('importance', 5)}] {e.get('action') or ''}: "
                    f"{(e.get('detail') or '')[:160]}"
                )
            if lines:
                parts.append("相关情节：")
                parts.extend(lines[:k])
        except Exception as e:
            logger.debug("memory recall skip: %s", e)

    # 语义核
    if auto.get("auto_recall_on_chat", True):
        try:
            sem_hits = core.semantic.recall(query=(query or "").strip(), k=3)
            if sem_hits:
                parts.append("语义核：")
                for h in sem_hits:
                    c = h.get("claim") or {}
                    parts.append(f"- {c.get('claim') or ''}")
        except Exception as e:
            logger.debug("semantic recall skip: %s", e)

    # 前瞻意图过程（非记忆层）
    try:
        pending = core.intentions.pending()[:3]
        if pending:
            parts.append("前瞻意图（过程缓冲）：")
            for it in pending:
                parts.append(
                    f"- {it.get('instruction') or ''} "
                    f"({it.get('dueLabel') or it.get('trigger') or 'pending'})"
                )
    except Exception:
        pass

    # 工作台（当前关注）
    try:
        slots = core._working_slots()[:4]
        if slots:
            parts.append("工作台：")
            for s in slots:
                parts.append(f"- {s.get('text') or ''}")
    except Exception:
        pass

    # 继承分区（带来源，不可伪装本地）
    if include_inherited and auto.get("auto_recall_on_chat", True):
        try:
            from .agent_memory_migration import inherited_hits_for_recall

            inh = inherited_hits_for_recall(
                store, team_id, agent_id, query=query or "", k=3
            )
            if inh:
                parts.append("继承记忆（非本地经历）：")
                for h in inh:
                    src = ((h.get("origin") or {}).get("source_agent") or {})
                    who = src.get("agent_id") or "?"
                    parts.append(f"- [继承自 {who}] {(h.get('summary') or '')[:140]}")
        except Exception as e:
            logger.debug("inherited recall skip: %s", e)

    text = "\n".join(parts)
    if len(parts) <= 2:
        return ""  # only header, no real content
    if len(text) > max_chars:
        text = text[: max_chars - 20] + "\n…(记忆截断)"
    return text


def update_agent_memory(
    team_id: str,
    agent_id: str,
    evidence: Dict[str, Any],
    *,
    store: Optional[AgentMemoryStore] = None,
) -> Dict[str, Any]:
    """统一证据写入口（Plaza/任务/用量/人工干预）。"""
    if not team_id or not agent_id or agent_id in _SKIP_AGENTS:
        return {"ok": False, "reason": "skip"}
    store = store or get_memory_store()
    ready = ensure_memory_ready(team_id, agent_id, store=store, auto_bind=True)
    if not ready.get("ok"):
        return {"ok": False, "reason": ready.get("reason") or "not_ready"}
    lc = _lc(store)
    try:
        lc.assert_writable(team_id, agent_id)
    except MemoryLifecycleError as e:
        return {"ok": False, "reason": e.code}
    core = AgentMemoryCore(team_id, agent_id, store=store)
    payload = dict(evidence or {})
    payload.setdefault("agent_id", agent_id)
    try:
        return core.update_from_evidence(payload)
    except Exception as e:
        logger.debug("update_agent_memory failed: %s", e)
        return {"ok": False, "reason": str(e)}


def after_agent_plaza_message(
    discussion: Any,
    participant: Any,
    message: Any,
    turn_result: Optional[Any] = None,
    *,
    store: Optional[AgentMemoryStore] = None,
) -> Dict[str, Any]:
    """Plaza 发言后写回该参与者的协商/用量/失败/人工干预证据。"""
    team_id = getattr(participant, "team_id", None) or ""
    agent_id = getattr(participant, "agent_id", None) or ""
    if not team_id or not agent_id:
        return {"ok": False, "reason": "no_participant"}

    meta = {}
    if hasattr(message, "metadata") and isinstance(message.metadata, dict):
        meta = message.metadata
    elif isinstance(message, dict):
        meta = message.get("metadata") or {}

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    seq = getattr(message, "seq", None)
    if seq is None and isinstance(message, dict):
        seq = message.get("seq")
    round_number = getattr(message, "round_number", None)
    if round_number is None and isinstance(message, dict):
        round_number = message.get("round_number")

    disc_id = getattr(discussion, "id", None) or getattr(discussion, "discussion_id", "") or ""
    usage = None
    failure = None
    if turn_result is not None:
        if isinstance(turn_result, dict):
            usage = turn_result.get("usage") or turn_result.get("usage_evidence")
            failure = turn_result.get("failure_type") or turn_result.get("error")
        else:
            usage = getattr(turn_result, "usage", None)
            failure = getattr(turn_result, "error", None) or getattr(turn_result, "failure_type", None)
    if usage is None and isinstance(meta.get("usage"), dict):
        usage = meta.get("usage")
    if isinstance(usage, dict):
        usage = {
            **usage,
            "discussion_id": disc_id,
            "agent_id": agent_id,
            "run_id": meta.get("run_id") or usage.get("run_id") or f"{disc_id}:{seq}",
        }

    human = meta.get("human_intervention") or meta.get("interjection")
    evidence = {
        "source_type": "plaza_turn",
        "source_id": f"{disc_id}:{seq}",
        "agent_id": agent_id,
        "action": "广场发言",
        "summary": (str(content or ""))[:240],
        "importance": 6,
        "deliberation_state": {
            "discussion_id": disc_id,
            "round": round_number,
            "phase": meta.get("orid_phase") or meta.get("phase") or "",
            "position": (str(content or ""))[:400],
        },
        "usage_evidence": usage,
        "failure_type": failure,
        "human_intervention": human,
        "provenance": {
            "source_type": "plaza_turn",
            "source_id": f"{disc_id}:{seq}",
            "agent_id": agent_id,
            "discussion_id": disc_id,
            "timestamp": meta.get("timestamp"),
        },
        "tags": ["plaza", "deliberation"],
    }
    return update_agent_memory(team_id, agent_id, evidence, store=store)


def _read_survival_ticks(team_id: str, agent_id: str) -> Optional[float]:
    """Best-effort eco_collab.survival_ticks from team agent profile."""
    try:
        from . import api as agent_api

        tm = getattr(agent_api, "_team_manager", None)
        if not tm:
            return None
        team = tm.get_team(team_id)
        if not team:
            return None
        agent = None
        if hasattr(tm, "get_agent"):
            agent = tm.get_agent(team_id, agent_id)
        if agent is None:
            agents = getattr(team, "agents", None) or {}
            if isinstance(agents, dict):
                agent = agents.get(agent_id)
        if agent is None:
            return None
        meta = getattr(agent, "metadata", None) or {}
        if isinstance(agent, dict):
            meta = agent.get("metadata") or {}
        if not isinstance(meta, dict):
            return None
        eco = meta.get("eco_collab") if isinstance(meta.get("eco_collab"), dict) else {}
        st = eco.get("survival_ticks")
        if st is None:
            st = meta.get("survival_ticks")
        return float(st) if st is not None else None
    except Exception:
        return None


def record_task_outcome(
    team_id: str,
    agent_id: str,
    *,
    task_id: str = "",
    title: str = "",
    success: bool = True,
    detail: str = "",
    store: Optional[AgentMemoryStore] = None,
    survival_ticks: Optional[float] = None,
) -> Dict[str, Any]:
    """Write episodic log (+ optional feel) for a finished task."""
    if not team_id or not agent_id or agent_id in _SKIP_AGENTS:
        return {"ok": False, "reason": "skip"}
    store = store or get_memory_store()
    ready = ensure_memory_ready(team_id, agent_id, store=store, auto_bind=True)
    if not ready.get("ok"):
        return {"ok": False, "reason": ready.get("reason") or "not_ready"}
    lc = _lc(store)
    try:
        lc.assert_writable(team_id, agent_id)
    except MemoryLifecycleError as e:
        return {"ok": False, "reason": e.code}

    st = lc.get_status(team_id, agent_id)
    auto = _autonomy(st)
    if not auto.get("auto_log_on_task", True):
        return {"ok": False, "reason": "auto_log_off"}

    core = AgentMemoryCore(team_id, agent_id, store=store)
    action = "任务成功" if success else "任务失败"
    importance = 7 if success else 8
    event = core.log.append(
        {
            "subject": agent_id,
            "action": action,
            "detail": (detail or title or task_id or "")[:800],
            "place": f"task:{task_id}" if task_id else "",
            "importance": importance,
            "tags": ["任务", "自主", "成功" if success else "失败"]
            + ([task_id] if task_id else []),
        }
    )
    # 工作台：当前任务关注点
    try:
        core.push_working(
            {
                "text": (title or detail or task_id or action)[:200],
                "source": "task",
                "ref": task_id or "",
            }
        )
    except Exception:
        pass

    surv = survival_ticks if survival_ticks is not None else _read_survival_ticks(team_id, agent_id)

    felt = None
    fit = None
    if auto.get("auto_feel_on_outcome", True):
        try:
            # 感情 = 适应度选择压：成败 + eco survival → 电荷 + 拓扑漂移
            fit = core.apply_fitness(
                success=success,
                magnitude=0.45 if success else 0.6,
                survival_ticks=surv,
                drift=True,
            )
            felt = fit.get("affect")
        except Exception:
            pass

    compressed = _maybe_compress(core, auto)
    consolidated = None
    forgotten = None
    try:
        consolidated = core.consolidate_tick(max_new=3 if success else 2)
        forgotten = core.forget_tick()
    except Exception as e:
        logger.debug("consolidate/forget skip: %s", e)
    reflected = maybe_reflect(team_id, agent_id, store=store, core=core, status=st)
    return {
        "ok": True,
        "event_id": event.get("id"),
        "felt": bool(felt),
        "compressed": compressed,
        "consolidated": consolidated,
        "forgotten": forgotten,
        "reflected": reflected,
        "fitness": fit,
        "survival_ticks": surv,
    }


def record_chat_turn(
    team_id: str,
    agent_id: str,
    *,
    user_text: str = "",
    assistant_text: str = "",
    session_id: str = "",
    store: Optional[AgentMemoryStore] = None,
) -> Dict[str, Any]:
    """Persist a light chat memory (小满偏感知；混合/沈弥安写低重要度日志摘要)."""
    if not team_id or not agent_id or agent_id in _SKIP_AGENTS:
        return {"ok": False, "reason": "skip"}
    store = store or get_memory_store()
    ready = ensure_memory_ready(team_id, agent_id, store=store, auto_bind=True)
    if not ready.get("ok"):
        return ready
    lc = _lc(store)
    try:
        lc.assert_writable(team_id, agent_id)
    except MemoryLifecycleError as e:
        return {"ok": False, "reason": e.code}
    st = lc.get_status(team_id, agent_id)
    auto = _autonomy(st)
    persona = st.get("persona") or "hybrid"
    core = AgentMemoryCore(team_id, agent_id, store=store)

    # 感知：用户话 / 助手回复摘要
    if auto.get("auto_perceive_on_tool", True) or persona == "xiaoman":
        core.perception.perceive(
            {
                "modality": "dialogue",
                "payload": {
                    "user": (user_text or "")[:200],
                    "assistant": (assistant_text or "")[:200],
                    "session": session_id,
                },
            }
        )
        _maybe_compress(core, auto)

    # 日志：仅当对话有实质内容
    if (user_text or "").strip():
        core.log.append(
            {
                "subject": agent_id,
                "action": "对话",
                "detail": f"用户: {(user_text or '')[:120]} → 回复: {(assistant_text or '')[:120]}"[:500],
                "place": f"chat:{session_id}" if session_id else "chat",
                "importance": 4 if persona != "shenmian" else 5,
                "tags": ["对话", "自主", persona],
            }
        )
    # 沈弥安：对话后按间隔尝试反思（不 force，尊重 hours 门槛）
    reflected = False
    if persona == "shenmian":
        try:
            reflected = maybe_reflect(team_id, agent_id, store=store, core=core, status=st)
        except Exception:
            reflected = False
    return {"ok": True, "persona": persona, "reflected": reflected}


def maybe_reflect(
    team_id: str,
    agent_id: str,
    *,
    store: Optional[AgentMemoryStore] = None,
    core: Optional[AgentMemoryCore] = None,
    status: Optional[Dict[str, Any]] = None,
    force: bool = False,
) -> bool:
    """沈弥安/混合：按间隔把近期日志凝成一条高重要度反思事件."""
    store = store or get_memory_store()
    lc = _lc(store)
    st = status or lc.get_status(team_id, agent_id)
    persona = st.get("persona") or "hybrid"
    auto = _autonomy(st)
    hours = float(auto.get("reflection_interval_hours") or 0)
    if not force:
        if persona == "xiaoman":
            return False
        if hours <= 0 and persona != "shenmian":
            return False
        if persona == "shenmian" and hours <= 0:
            hours = 24
    meta = store.load(team_id, agent_id, "meta", {}) or {}
    if not isinstance(meta, dict):
        meta = {}
    last = int(meta.get("last_reflection_at") or 0)
    import time
    now = int(time.time() * 1000)
    if not force and hours > 0 and last and (now - last) < hours * 3_600_000:
        return False

    core = core or AgentMemoryCore(team_id, agent_id, store=store)
    recent = core.log.replay()[-12:]
    if len(recent) < 3:
        return False
    # 简单聚类：取高重要度动作摘要
    tops = sorted(recent, key=lambda e: int(e.get("importance") or 0), reverse=True)[:5]
    bullets = []
    for e in tops:
        bullets.append(f"{e.get('action') or '?'}:{(e.get('detail') or '')[:80]}")
    detail = "反思固化（自主）：" + " | ".join(bullets)
    core.log.append(
        {
            "subject": agent_id,
            "action": "反思固化",
            "detail": detail[:800],
            "importance": 9,
            "tags": ["反思", "沈弥安" if persona == "shenmian" else "自主", "固化"],
        }
    )
    meta["last_reflection_at"] = now
    store.save(team_id, agent_id, "meta", meta)
    return True


def record_perception(
    team_id: str,
    agent_id: str,
    *,
    modality: str = "metric",
    payload: Any = None,
    store: Optional[AgentMemoryStore] = None,
) -> Dict[str, Any]:
    if not team_id or not agent_id or agent_id in _SKIP_AGENTS:
        return {"ok": False, "reason": "skip"}
    store = store or get_memory_store()
    lc = _lc(store)
    try:
        lc.assert_writable(team_id, agent_id)
    except MemoryLifecycleError as e:
        return {"ok": False, "reason": e.code}
    st = lc.get_status(team_id, agent_id)
    auto = _autonomy(st)
    if not auto.get("auto_perceive_on_tool", True):
        return {"ok": False, "reason": "auto_perceive_off"}

    core = AgentMemoryCore(team_id, agent_id, store=store)
    item = core.perception.perceive({"modality": modality or "metric", "payload": payload})
    compressed = _maybe_compress(core, auto)
    return {"ok": True, "item": item, "compressed": compressed}


def _maybe_compress(core: AgentMemoryCore, auto: Dict[str, Any]) -> bool:
    thr = int(auto.get("auto_compress_threshold") or 50)
    if thr <= 0:
        return False
    n = len(core.perception.buffer)
    if n < thr:
        return False
    try:
        r = core.perception.compress(core.log)
        return bool(r)
    except Exception as e:
        logger.debug("auto compress failed: %s", e)
        return False


def inject_memory_into_messages(
    messages: List[Dict[str, Any]],
    addon: str,
) -> List[Dict[str, Any]]:
    """Non-mutating-ish: return new messages list with memory addon on system."""
    if not addon or not messages:
        return messages
    tag = "[AG_MEMORY]"
    out = list(messages)
    if out[0].get("role") == "system":
        sys = str(out[0].get("content") or "")
        # 避免同 session 重复叠加：替换旧 AG_MEMORY 段
        if tag in sys:
            head = sys.split(tag)[0].rstrip()
            sys = head
        out[0] = {**out[0], "content": (sys + "\n\n" + addon).strip()}
    else:
        out.insert(0, {"role": "system", "content": addon})
    return out


# ── EventBus hooks ─────────────────────────────────────────────


def emit_eco_survival(
    team_id: str,
    agent_id: str,
    *,
    survival_ticks: float = 0.0,
    fitness_delta: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Publish ECO_SURVIVAL_UPDATED so memory hooks can drift topology / charge."""
    if not team_id or not agent_id:
        return False
    try:
        from .domain_events import DomainEvent, EcoSurvivalSnapshot, EventType
        from .event_bus import get_event_bus

        snap = EcoSurvivalSnapshot(
            team_id=team_id,
            agent_id=agent_id,
            survival_ticks=float(survival_ticks or 0),
            fitness_delta=float(fitness_delta or 0),
            metadata=dict(metadata or {}),
        )
        ev = DomainEvent.create(
            EventType.ECO_SURVIVAL_UPDATED,
            snap,
            source="eco_runtime",
        )
        get_event_bus().publish(ev)
        return True
    except Exception as e:
        logger.debug("emit_eco_survival failed: %s", e)
        return False


def apply_eco_survival_to_memory(
    team_id: str,
    agent_id: str,
    *,
    survival_ticks: float = 0.0,
    fitness_delta: float = 0.0,
    store: Optional[AgentMemoryStore] = None,
) -> Dict[str, Any]:
    """Direct path (also used by EventBus handler): survival → fitness/topology."""
    if not team_id or not agent_id or agent_id in _SKIP_AGENTS:
        return {"ok": False, "reason": "skip"}
    store = store or get_memory_store()
    ready = ensure_memory_ready(team_id, agent_id, store=store, auto_bind=True)
    if not ready.get("ok"):
        return {"ok": False, "reason": ready.get("reason")}
    try:
        core = AgentMemoryCore(team_id, agent_id, store=store)
        # 相对上次 survival 的归一化 Δ
        meta = core._load_meta()
        prev = float((meta.get("topology") or {}).get("last_survival_ticks") or 0)
        surv = float(survival_ticks or 0)
        if fitness_delta:
            fd = float(fitness_delta)
        elif prev > 0:
            fd = max(-1.0, min(1.0, (surv - prev) / max(prev, 1.0)))
        else:
            fd = 0.15 if surv > 0 else 0.0
        success = fd >= 0
        fit = core.apply_fitness(
            success=success,
            magnitude=min(0.8, abs(fd) + 0.2),
            survival_ticks=surv,
            drift=True,
            label_success="生机",
            label_fail="衰微",
        )
        # 工作台记一笔物竞关注
        try:
            core.push_working(
                {
                    "text": f"物竞存活 T={int(surv)} Δ={fd:+.2f}",
                    "source": "eco",
                    "ref": f"T:{surv}",
                }
            )
        except Exception:
            pass
        return {"ok": True, "fitness": fit, "survival_ticks": surv}
    except Exception as e:
        logger.debug("apply_eco_survival_to_memory: %s", e)
        return {"ok": False, "reason": str(e)}


class MemoryRuntimeHooks:
    def __init__(self, store: Optional[AgentMemoryStore] = None):
        self.store = store or get_memory_store()
        self._subscribed = False

    def start(self) -> None:
        if self._subscribed:
            return
        try:
            from .domain_events import EventType
            from .event_bus import get_event_bus

            bus = get_event_bus()
            bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
            bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)
            bus.subscribe(EventType.ECO_SURVIVAL_UPDATED, self._on_eco_survival)
            self._subscribed = True
            logger.info("MemoryRuntimeHooks started (TASK_*/ECO_SURVIVAL)")
        except Exception as e:
            logger.warning("MemoryRuntimeHooks start failed: %s", e)

    def stop(self) -> None:
        if not self._subscribed:
            return
        try:
            from .domain_events import EventType
            from .event_bus import get_event_bus

            bus = get_event_bus()
            bus.unsubscribe(EventType.TASK_COMPLETED, self._on_task_completed)
            bus.unsubscribe(EventType.TASK_FAILED, self._on_task_failed)
            bus.unsubscribe(EventType.ECO_SURVIVAL_UPDATED, self._on_eco_survival)
        except Exception:
            pass
        self._subscribed = False

    async def _on_task_completed(self, event) -> None:
        self._handle(event, success=True)

    async def _on_task_failed(self, event) -> None:
        self._handle(event, success=False)

    async def _on_eco_survival(self, event) -> None:
        try:
            p = event.payload
            team_id = getattr(p, "team_id", None) or ""
            agent_id = getattr(p, "agent_id", None) or ""
            surv = float(getattr(p, "survival_ticks", 0) or 0)
            fd = float(getattr(p, "fitness_delta", 0) or 0)
            if isinstance(p, dict):
                team_id = p.get("team_id") or team_id
                agent_id = p.get("agent_id") or agent_id
                surv = float(p.get("survival_ticks") or surv)
                fd = float(p.get("fitness_delta") or fd)
            apply_eco_survival_to_memory(
                team_id,
                agent_id,
                survival_ticks=surv,
                fitness_delta=fd,
                store=self.store,
            )
        except Exception as e:
            logger.debug("eco survival hook: %s", e)

    def _handle(self, event, success: bool) -> None:
        try:
            payload = event.payload
            task_id = getattr(payload, "task_id", None) or ""
            team_id = getattr(payload, "team_id", None) or ""
            title = getattr(payload, "title", None) or ""
            metadata = getattr(payload, "metadata", None) or {}
            if not isinstance(metadata, dict):
                metadata = {}
            team_id = team_id or metadata.get("team_id") or ""

            agent_ids: List[str] = []
            aid0 = getattr(payload, "agent_id", None) or ""
            if aid0:
                agent_ids.append(str(aid0))
            for key in ("assigned_agent", "champion_agent", "locked_agent_id"):
                v = metadata.get(key)
                if v:
                    agent_ids.append(str(v))
            for key in ("assigned_agents", "agent_ids"):
                assigned = metadata.get(key) or []
                if isinstance(assigned, list):
                    agent_ids.extend(str(x) for x in assigned if x)

            agent_ids = list(dict.fromkeys([a for a in agent_ids if a]))
            if not team_id or not agent_ids:
                return

            detail = title
            err = getattr(payload, "error", None) or metadata.get("error") or ""
            if not success and err:
                detail = f"{title} · {err}"[:500]

            for aid in agent_ids[:5]:
                record_task_outcome(
                    team_id,
                    aid,
                    task_id=str(task_id),
                    title=str(title),
                    success=success,
                    detail=str(detail),
                    store=self.store,
                )
        except Exception as e:
            logger.debug("MemoryRuntimeHooks handle skip: %s", e)


_hooks: Optional[MemoryRuntimeHooks] = None


def get_memory_runtime_hooks() -> MemoryRuntimeHooks:
    global _hooks
    if _hooks is None:
        _hooks = MemoryRuntimeHooks()
    return _hooks


def start_memory_runtime_hooks() -> None:
    get_memory_runtime_hooks().start()


def bridge_aas_experience(
    experience: Any,
    *,
    team_id: str = "",
    store: Optional[AgentMemoryStore] = None,
) -> Dict[str, Any]:
    """可选：将沙箱 AAS ExperienceEntry 同步进 Agent 四层日志.

    开启条件（任一）：
    - 环境变量 AG_MEMORY_AAS_BRIDGE=1
    - experience 带 metadata.bridge_to_memory=True

    team_id 来源：参数 > experience.team_id > metadata.team_id > AG_TEAM_ID
    """
    import os

    meta = getattr(experience, "metadata", None) or {}
    if not isinstance(meta, dict):
        meta = {}
    env_on = os.environ.get("AG_MEMORY_AAS_BRIDGE", "").strip() in ("1", "true", "yes", "on")
    flag = bool(meta.get("bridge_to_memory")) or env_on
    if not flag:
        return {"ok": False, "reason": "bridge_off"}

    agent_id = str(getattr(experience, "agent_id", None) or meta.get("agent_id") or "")
    team = (
        team_id
        or str(getattr(experience, "team_id", None) or "")
        or str(meta.get("team_id") or "")
        or os.environ.get("AG_TEAM_ID")
        or ""
    )
    if not agent_id or not team:
        return {"ok": False, "reason": "missing_team_or_agent"}

    store = store or get_memory_store()
    lc = _lc(store)
    try:
        lc.assert_writable(team, agent_id)
    except MemoryLifecycleError as e:
        return {"ok": False, "reason": e.code}

    outcome = getattr(experience, "outcome", None)
    outcome_s = outcome.value if hasattr(outcome, "value") else str(outcome or "")
    reward = float(getattr(experience, "reward", 0) or 0)
    success = outcome_s in ("success", "SUCCESS") or reward >= 0.5
    importance = 8 if success else (6 if outcome_s in ("partial", "PARTIAL") else 7)
    situation = str(getattr(experience, "situation", None) or "")[:400]
    action = str(getattr(experience, "action_taken", None) or "AAS经验")[:80]
    reflection = str(getattr(experience, "reflection", None) or "")[:300]
    detail = situation
    if reflection:
        detail = f"{situation} · 反思: {reflection}"[:800]

    core = AgentMemoryCore(team, agent_id, store=store)
    event = core.log.append(
        {
            "subject": agent_id,
            "action": f"孪生经验·{action}"[:40],
            "detail": detail,
            "place": f"aas:{getattr(experience, 'session_id', '') or getattr(experience, 'experience_id', '')}",
            "importance": importance,
            "tags": ["AAS", "孪生", "经验", "成功" if success else "失败"],
        }
    )
    return {"ok": True, "event_id": event.get("id"), "team_id": team, "agent_id": agent_id}
