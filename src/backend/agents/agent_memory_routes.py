# -*- coding: utf-8 -*-
"""Agent 四层记忆 API — 绑定在 /api/v1/agent-config/teams/{team}/agents/{agent}/memory-core"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Query, status

from .agent_memory_core import AgentMemoryCore
from .agent_memory_lifecycle import (
    AgentMemoryLifecycle,
    MemoryLifecycleError,
    get_memory_lifecycle,
)
from .agent_memory_share import AgentMemoryShare, get_memory_share
from .agent_memory_transfer import AgentMemoryTransfer, get_memory_transfer

router = APIRouter(tags=["agent-memory"])
# 站级前缀 /api/v1/agent-memory（main 挂载）
hub_router = APIRouter(prefix="/api/v1/agent-memory", tags=["agent-memory-hub"])


def _core(team_id: str, agent_id: str) -> AgentMemoryCore:
    if not team_id or not agent_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="team_id and agent_id required")
    lc = get_memory_lifecycle()
    try:
        lc.assert_readable(team_id, agent_id)
    except MemoryLifecycleError as e:
        raise HTTPException(status.HTTP_410_GONE, detail=e.detail)
    return AgentMemoryCore(team_id, agent_id)


def _lc() -> AgentMemoryLifecycle:
    return get_memory_lifecycle()


def _share() -> AgentMemoryShare:
    return get_memory_share()


def _xfer() -> AgentMemoryTransfer:
    return get_memory_transfer()


def _http_lc(e: MemoryLifecycleError) -> HTTPException:
    code = status.HTTP_400_BAD_REQUEST
    if e.code in ("illegal_transition", "not_shareable", "share_denied"):
        code = status.HTTP_409_CONFLICT
    if e.code in ("memory_destroyed", "beneficiary_destroyed"):
        code = status.HTTP_410_GONE
    if e.code in ("grant_not_found",):
        code = status.HTTP_404_NOT_FOUND
    return HTTPException(code, detail=e.detail)


def _team_manager():
    """Resolve the live TeamManager used by agent-config (not a second empty instance)."""
    try:
        from . import api as agent_api

        tm = getattr(agent_api, "_team_manager", None)
        if tm is not None:
            return tm
    except Exception:
        pass
    return None


def _list_team_agents(team_id: str) -> list:
    """Return [{agent_id, name, role}, ...] for a team."""
    agents: list = []
    tm = _team_manager()
    if not tm or not team_id:
        return agents
    try:
        team = tm.get_team(team_id)
    except Exception:
        team = None
    if not team:
        return agents
    raw = getattr(team, "agents", None) or {}
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        items = [
            (getattr(a, "agent_id", None) or getattr(a, "id", str(i)), a)
            for i, a in enumerate(raw)
        ]
    else:
        return agents
    for aid, ag in items:
        if not aid:
            continue
        if isinstance(ag, dict):
            agents.append(
                {
                    "agent_id": str(aid),
                    "name": ag.get("name") or str(aid),
                    "role": ag.get("role") or ag.get("template_type") or "",
                }
            )
        else:
            agents.append(
                {
                    "agent_id": str(aid),
                    "name": getattr(ag, "name", None) or str(aid),
                    "role": getattr(ag, "role", "") or getattr(ag, "template_type", "") or "",
                }
            )
    return agents


def _writable(team_id: str, agent_id: str) -> AgentMemoryCore:
    try:
        _lc().assert_writable(team_id, agent_id)
    except MemoryLifecycleError as e:
        code = status.HTTP_409_CONFLICT
        if e.code == "memory_destroyed":
            code = status.HTTP_410_GONE
        raise HTTPException(code, detail=e.detail)
    return _core(team_id, agent_id)


def _ensure_agent(team_id: str, agent_id: str) -> None:
    """Best-effort existence check; memory may still attach offline / orphan ids."""
    try:
        from .team_store import get_team_manager

        tm = get_team_manager()
        team = tm.get_team(team_id) if tm else None
        if team is None:
            return
        agents = getattr(team, "agents", None) or {}
        if isinstance(agents, dict) and agents and agent_id not in agents:
            # soft: still allow (agent 可能刚删或 id 别名)；仅提示级
            return
    except Exception:
        pass


def _mark_agent_metadata(team_id: str, agent_id: str, patch: Dict[str, Any]) -> None:
    try:
        from .team_store import get_team_manager

        tm = get_team_manager()
        team = tm.get_team(team_id) if tm else None
        if not team:
            return
        agent = team.agents.get(agent_id) if isinstance(getattr(team, "agents", None), dict) else None
        if not agent:
            return
        meta = dict(getattr(agent, "metadata", None) or {})
        bind = dict(meta.get("memory_bind") or {})
        bind.update(patch)
        meta["memory_bind"] = bind
        agent.metadata = meta
        if hasattr(tm, "save_team"):
            tm.save_team(team)
        elif hasattr(tm, "update_team"):
            tm.update_team(team)
        elif hasattr(tm, "_persist"):
            tm._persist()
    except Exception:
        pass


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core",
    summary="记忆绑定总览（四层）",
)
def memory_overview(team_id: str, agent_id: str) -> Dict[str, Any]:
    _ensure_agent(team_id, agent_id)
    return _core(team_id, agent_id).overview()


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/meta",
    summary="绑定状态与计数",
)
def memory_meta(team_id: str, agent_id: str) -> Dict[str, Any]:
    return _core(team_id, agent_id).meta()


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/bind",
    summary="绑定 / 解绑记忆核心",
)
def memory_bind(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    _ensure_agent(team_id, agent_id)
    enabled = body.get("enabled", True)
    if isinstance(enabled, str):
        enabled = enabled.lower() not in ("0", "false", "no", "off")
    core = _core(team_id, agent_id)
    meta = core.bind(bool(enabled))
    _mark_agent_metadata(
        team_id,
        agent_id,
        {
            "enabled": bool(enabled),
            "bound_at": meta.get("bound_at"),
            "schema": meta.get("schema"),
        },
    )
    return meta


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/log",
    summary="追加运行日志",
)
def memory_log_append(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    event = core.log.append(body or {})
    return {"ok": True, "event": event, "counts": core.counts()}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/log",
    summary="运行日志列表或三因子检索",
)
def memory_log_list(
    team_id: str,
    agent_id: str,
    query: str = Query(default=""),
    k: int = Query(default=20, ge=1, le=100),
    recall: bool = Query(default=False),
) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    if recall or query:
        hits = core.log.recall(query=query, k=k)
        return {"ok": True, "mode": "recall", "hits": hits, "query": query}
    events = core.log.replay()
    return {"ok": True, "mode": "replay", "events": events[-k:], "total": len(events)}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/perception",
    summary="注入感知",
)
def memory_perceive(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    item = core.perception.perceive(body or {})
    return {"ok": True, "item": item, "summary": core.perception.summarize()}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/perception/compress",
    summary="感知压缩固化到运行日志",
)
def memory_compress(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    result = core.perception.compress(core.log)
    if not result:
        return {"ok": True, "compressed": False, "detail": "感知缓冲为空"}
    return {"ok": True, "compressed": True, **result, "counts": core.counts()}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/intentions",
    summary="新建前瞻意图（过程缓冲·非记忆层）",
)
def memory_intention_add(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    if not (body or {}).get("instruction"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="instruction required")
    it = core.intentions.add(body or {})
    return {
        "ok": True,
        "intention": it,
        "pending": core.intentions.pending(),
        "system": "prospective",
        "kind": "process",
        "note": "前瞻意图不是记忆层",
    }


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/consolidate",
    summary="巩固：情节→语义核",
)
def memory_consolidate(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    max_new = int((body or {}).get("max_new") or 5)
    result = core.consolidate_tick(max_new=max_new)
    return {"ok": True, **result, "counts": core.counts(), "semantic": core.semantic.active()[-10:]}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/forget",
    summary="遗忘引擎 tick（soft-forget 低分情节）",
)
def memory_forget(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    hard_cap = (body or {}).get("hard_cap")
    result = core.forget_tick(hard_cap=int(hard_cap) if hard_cap is not None else None)
    return {"ok": True, **result, "counts": core.counts()}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/systems",
    summary="拟生系统视图（层/场/过程）",
)
def memory_systems(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    return {"ok": True, **core.systems_view()}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/forgotten",
    summary="soft-forget 审计列表",
)
def memory_forgotten(
    team_id: str,
    agent_id: str,
    limit: int = Query(default=30, ge=1, le=200),
) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    rows = core.forgotten_audit(limit=limit)
    return {"ok": True, "forgotten": rows, "count": len(rows)}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/working",
    summary="工作台槽位",
)
def memory_working_list(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    return {
        "ok": True,
        "working": core._working_slots(),
        "topology": core.topology(),
    }


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/working",
    summary="推入工作台",
)
def memory_working_push(
    team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})
) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    slots = core.push_working(body or {})
    return {"ok": True, "working": slots}


@router.delete(
    "/teams/{team_id}/agents/{agent_id}/memory-core/working",
    summary="清空工作台",
)
def memory_working_clear(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    core.clear_working()
    return {"ok": True, "working": []}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/drift",
    summary="拓扑慢漂移 tick（force 可测）",
)
def memory_drift(
    team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})
) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    fd = float((body or {}).get("fitness_delta") or 0)
    surv = (body or {}).get("survival_ticks")
    force = bool((body or {}).get("force", True))
    topo = core.drift_topology(
        fitness_delta=fd,
        survival_ticks=float(surv) if surv is not None else None,
        force=force,
    )
    return {"ok": True, "topology": topo}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/intentions/{intention_id}/confirm",
    summary="确认意图",
)
def memory_intention_confirm(team_id: str, agent_id: str, intention_id: str) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    it = core.intentions.confirm(intention_id)
    if not it:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="intention_not_found_or_not_pending")
    return {"ok": True, "intention": it}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/intentions/{intention_id}/drop",
    summary="放弃意图",
)
def memory_intention_drop(team_id: str, agent_id: str, intention_id: str) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    it = core.intentions.drop(intention_id)
    if not it:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="intention_not_found_or_not_pending")
    return {"ok": True, "intention": it}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/affect",
    summary="注入情绪电荷（场·非事实层）",
)
def memory_feel(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    label = (body or {}).get("label") or ""
    if not label:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="label required")
    residue = core.affect.feel(
        label=label,
        intensity=float((body or {}).get("intensity", 0.5)),
        valence=float((body or {}).get("valence", 0)),
        arousal=float((body or {}).get("arousal", 0.5)),
    )
    return {"ok": True, "affect": residue, "tone_hint": core.affect.tone_hint()}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/affect/tone",
    summary="语气提示（供对话注入）",
)
def memory_tone(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    return {"ok": True, "tone_hint": core.affect.tone_hint(), "affect": core.affect.residue()}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/at",
    summary="共享时间轴切片",
)
def memory_at(
    team_id: str,
    agent_id: str,
    t: Optional[int] = Query(default=None),
    window_ms: int = Query(default=60_000, ge=1000, le=3_600_000),
) -> Dict[str, Any]:
    import time

    core = _core(team_id, agent_id)
    ts = int(t) if t is not None else int(time.time() * 1000)
    return {"ok": True, "slice": core.at(ts, window_ms)}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/seal",
    summary="封存（仪式性只读快照）",
)
def memory_seal(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    snap = core.seal()
    _mark_agent_metadata(team_id, agent_id, {"sealed": True, "sealed_at": snap.get("sealedAt")})
    return {
        "ok": True,
        "sealed": True,
        "snapshot": snap,
        "disclosure": "这是回放，不是本人",
    }


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/memorial",
    summary="凭吊只读视图",
)
def memory_memorial(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    snap = core.memorial()
    if not snap:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not_sealed")
    return {
        "ok": True,
        "disclosure": "这是回放，不是本人",
        "memorial": snap,
    }


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/export",
    summary="导出整只记忆",
)
def memory_export(team_id: str, agent_id: str) -> Dict[str, Any]:
    return _core(team_id, agent_id).export_all()


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/import",
    summary="导入整只记忆（覆盖四层）",
)
def memory_import(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    ok = core.import_all(body)
    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_memory_payload")
    _mark_agent_metadata(team_id, agent_id, {"enabled": True, "imported": True})
    return {"ok": True, "meta": core.meta(), "counts": core.counts()}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/will",
    summary="遗嘱草稿（协议 define-only）",
)
def memory_will(team_id: str, agent_id: str) -> Dict[str, Any]:
    return _core(team_id, agent_id).draft_will()


# ── 生命周期（旧 path 兼容 + 新 hub）──────────────────────────


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/lifecycle",
    summary="生命周期动作 bind|seal|unseal|save|destroy|share|unshare",
)
def memory_lifecycle_action(
    team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})
) -> Dict[str, Any]:
    action = (body or {}).get("action") or ""
    reason = (body or {}).get("reason") or ""
    try:
        result = _lc().transition(team_id, agent_id, action, reason=reason)
    except MemoryLifecycleError as e:
        code = status.HTTP_400_BAD_REQUEST
        if e.code == "illegal_transition":
            code = status.HTTP_409_CONFLICT
        if e.code == "memory_destroyed":
            code = status.HTTP_410_GONE
        raise HTTPException(code, detail=e.detail)
    st = result.get("status") or {}
    _mark_agent_metadata(
        team_id,
        agent_id,
        {
            "state": st.get("state"),
            "enabled": st.get("bound"),
            "sealed": st.get("sealed"),
            "persona": st.get("persona"),
        },
    )
    return result


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/lifecycle",
    summary="生命周期状态",
)
def memory_lifecycle_status(team_id: str, agent_id: str) -> Dict[str, Any]:
    return _lc().get_status(team_id, agent_id)


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory-core/audit",
    summary="生命周期审计",
)
def memory_audit(team_id: str, agent_id: str, limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return {"ok": True, "audit": _lc().read_audit(team_id, agent_id, limit=limit)}


@router.put(
    "/teams/{team_id}/agents/{agent_id}/memory-core/persona",
    summary="设置记忆 Persona：xiaoman|shenmian|hybrid",
)
def memory_set_persona(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    persona = (body or {}).get("persona") or "hybrid"
    autonomy = (body or {}).get("autonomy")
    try:
        st = _lc().set_persona(team_id, agent_id, persona=persona, autonomy=autonomy)
    except MemoryLifecycleError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=e.detail)
    _mark_agent_metadata(team_id, agent_id, {"persona": persona})
    return {"ok": True, "status": st}


# ── Hub router: /api/v1/agent-memory ───────────────────────────


@hub_router.get("/overview", summary="团队记忆总览")
def hub_overview(team_id: str = Query(...)) -> Dict[str, Any]:
    return _lc().team_overview(team_id, _list_team_agents(team_id))


@hub_router.get("/systems-catalog", summary="拟生记忆系统目录（层/场/过程）")
def hub_systems_catalog() -> Dict[str, Any]:
    from .agent_memory_core import systems_catalog

    return {"ok": True, **systems_catalog()}


# 静态/更具体路径必须注册在 /{team_id}/{agent_id} 之前
@hub_router.get("/transfers", summary="传递记录")
def hub_list_transfers(
    team_id: str = Query(default=""),
    limit: int = Query(default=30, ge=1, le=100),
) -> Dict[str, Any]:
    return {"ok": True, "transfers": _xfer().list_transfers(team_id=team_id, limit=limit)}


@hub_router.get("/{team_id}/share-matrix", summary="团队共享矩阵")
def hub_share_matrix(team_id: str) -> Dict[str, Any]:
    agent_ids = [a["agent_id"] for a in _list_team_agents(team_id)]
    return _share().matrix(team_id, agent_ids)


@hub_router.get("/{team_id}/{agent_id}", summary="记忆总览")
def hub_agent_overview(team_id: str, agent_id: str) -> Dict[str, Any]:
    return memory_overview(team_id, agent_id)


@hub_router.post("/{team_id}/{agent_id}/lifecycle", summary="生命周期动作")
def hub_lifecycle(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    return memory_lifecycle_action(team_id, agent_id, body)


@hub_router.get("/{team_id}/{agent_id}/lifecycle", summary="生命周期状态")
def hub_lifecycle_get(team_id: str, agent_id: str) -> Dict[str, Any]:
    return memory_lifecycle_status(team_id, agent_id)


@hub_router.put("/{team_id}/{agent_id}/persona", summary="Persona")
def hub_persona(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    return memory_set_persona(team_id, agent_id, body)


@hub_router.get("/{team_id}/{agent_id}/memory-style", summary="Agent 独有记忆方式")
def hub_memory_style_get(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    return {"ok": True, "memory_style": core.memory_style(), "dynamic_state": core.dynamic_state()}


@hub_router.put("/{team_id}/{agent_id}/memory-style", summary="调整 Agent 独有记忆方式")
def hub_memory_style_put(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    style = core.set_memory_style(body or {})
    _lc()._append_audit(team_id, agent_id, {"t": __import__("time").time_ns() // 1_000_000, "action": "set_memory_style", "version": style.get("version")})
    return {"ok": True, "memory_style": style, "dynamic_state": core.dynamic_state()}


@hub_router.get("/{team_id}/{agent_id}/audit", summary="审计")
def hub_audit(team_id: str, agent_id: str, limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return memory_audit(team_id, agent_id, limit=limit)


@hub_router.post("/{team_id}/{agent_id}/destroy", summary="销毁记忆")
def hub_destroy(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    body = dict(body or {})
    body["action"] = "destroy"
    return memory_lifecycle_action(team_id, agent_id, body)


@hub_router.post(
    "/{team_id}/{agent_id}/runtime/recall",
    summary="运行时检索包（tone+recall+intentions）",
)
def hub_runtime_recall(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    from .agent_memory_runtime import prepare_memory_system_addon

    q = (body or {}).get("query") or (body or {}).get("prompt") or ""
    addon = prepare_memory_system_addon(team_id, agent_id, query=q)
    return {"ok": True, "addon": addon, "chars": len(addon)}


@hub_router.post(
    "/{team_id}/{agent_id}/runtime/record",
    summary="运行时写入（task outcome / perception）",
)
def hub_runtime_record(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    from .agent_memory_runtime import record_perception, record_task_outcome

    kind = (body or {}).get("kind") or "task"
    if kind == "perception":
        return record_perception(
            team_id,
            agent_id,
            modality=(body or {}).get("modality") or "metric",
            payload=(body or {}).get("payload"),
        )
    return record_task_outcome(
        team_id,
        agent_id,
        task_id=str((body or {}).get("task_id") or ""),
        title=str((body or {}).get("title") or ""),
        success=bool((body or {}).get("success", True)),
        detail=str((body or {}).get("detail") or ""),
    )


# ── Share ──────────────────────────────────────────────────────


@hub_router.get("/{team_id}/{agent_id}/shares", summary="列出对外授权")
def hub_list_shares(team_id: str, agent_id: str) -> Dict[str, Any]:
    try:
        grants = _share().list_grants(team_id, agent_id)
    except MemoryLifecycleError as e:
        raise _http_lc(e)
    return {"ok": True, "grants": grants}


@hub_router.post("/{team_id}/{agent_id}/share", summary="授权共享")
def hub_share(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    grantee = (body or {}).get("grantee") or (body or {}).get("grantee_agent_id") or ""
    role = (body or {}).get("role") or "reader"
    layers = (body or {}).get("layers")
    note = (body or {}).get("note") or ""
    try:
        return _share().grant(
            team_id, agent_id, grantee, role=role, layers=layers, note=note
        )
    except MemoryLifecycleError as e:
        raise _http_lc(e)


@hub_router.delete(
    "/{team_id}/{agent_id}/share/{grantee}",
    summary="撤销共享",
)
def hub_revoke_share(team_id: str, agent_id: str, grantee: str) -> Dict[str, Any]:
    try:
        return _share().revoke(team_id, agent_id, grantee)
    except MemoryLifecycleError as e:
        raise _http_lc(e)


@hub_router.get(
    "/{team_id}/{reader}/shared-with-me",
    summary="我可读的他人记忆授权",
)
def hub_shared_with_me(team_id: str, reader: str) -> Dict[str, Any]:
    agent_ids = [a["agent_id"] for a in _list_team_agents(team_id)]
    return {"ok": True, "grants": _share().shared_with_me(team_id, reader, agent_ids)}


@hub_router.get(
    "/{team_id}/{owner}/shared/{reader}/{layer}",
    summary="按授权读取某层",
)
def hub_read_shared(
    team_id: str,
    owner: str,
    reader: str,
    layer: str,
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    try:
        return _share().read_shared_layer(team_id, owner, reader, layer, limit=limit)
    except MemoryLifecycleError as e:
        raise _http_lc(e)


@hub_router.post(
    "/{team_id}/{owner}/shared/{writer}/log",
    summary="co_writer 向 owner 日志协作写入",
)
def hub_cowrite_log(
    team_id: str,
    owner: str,
    writer: str,
    body: Dict[str, Any] = Body(default={}),
) -> Dict[str, Any]:
    try:
        return _share().write_shared_log(team_id, owner, writer, event=body or {})
    except MemoryLifecycleError as e:
        raise _http_lc(e)


@hub_router.post("/{team_id}/{agent_id}/transfer", summary="执行记忆传递")
def hub_transfer(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    to_id = (body or {}).get("to") or (body or {}).get("beneficiary") or ""
    try:
        return _xfer().execute(
            team_id,
            agent_id,
            to_id,
            handover_intentions=(body or {}).get("handover_intentions") or "ask_new_owner",
            keep_memorial=bool((body or {}).get("keep_memorial", True)),
            layers=(body or {}).get("layers"),
            note=(body or {}).get("note") or "",
        )
    except MemoryLifecycleError as e:
        raise _http_lc(e)


# 兼容旧 path
@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/share",
    summary="授权共享（兼容）",
)
def memory_share_compat(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    return hub_share(team_id, agent_id, body)


@router.post(
    "/teams/{team_id}/agents/{agent_id}/memory-core/transfer",
    summary="记忆传递（兼容）",
)
def memory_transfer_compat(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    return hub_transfer(team_id, agent_id, body)
