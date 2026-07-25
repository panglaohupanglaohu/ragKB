# -*- coding: utf-8 -*-
"""Agent 记忆生命周期状态机 · 审计 · 墓碑.

状态: unbound → active → shared|sealed|transferring|destroyed
      sealed → transferring|archived|destroyed
      transferring → archived|active(受益方)|destroyed
      archived → destroyed

destroy 写 tombstone，禁止静默 rehydrate（对齐 skill 删除墓碑教训）。
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .agent_memory_core import (
    AgentMemoryCore,
    AgentMemoryStore,
    get_memory_store,
    _now_ms,
    _safe_team_agent,
)

logger = logging.getLogger(__name__)

STATES = (
    "unbound",
    "active",
    "shared",
    "sealed",
    "transferring",
    "archived",
    "destroyed",
)

# action → (from_states, to_state)
TRANSITIONS: Dict[str, Tuple[Set[str], str]] = {
    "bind": ({"unbound", "active"}, "active"),
    "unbind": ({"active", "shared"}, "unbound"),
    "share": ({"active", "shared"}, "shared"),
    "unshare": ({"shared"}, "active"),
    "seal": ({"active", "shared"}, "sealed"),
    "unseal": ({"sealed"}, "active"),  # 显式仪式
    "transfer_start": ({"active", "shared", "sealed"}, "transferring"),
    "transfer_complete_archive": ({"transferring"}, "archived"),
    "transfer_complete_active": ({"transferring"}, "active"),  # 受益方侧
    "destroy": (
        {"unbound", "active", "shared", "sealed", "transferring", "archived"},
        "destroyed",
    ),
}

PERSONAS = ("xiaoman", "shenmian", "hybrid")


def memory_key(team_id: str, agent_id: str) -> str:
    t, a = _safe_team_agent(team_id, agent_id)
    return f"{t}:{a}"


class MemoryLifecycleError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail or code
        super().__init__(self.detail)


class AgentMemoryLifecycle:
    def __init__(self, store: Optional[AgentMemoryStore] = None):
        self.store = store or get_memory_store()

    def _tombstone_path(self) -> Path:
        p = self.store.root / "_tombstones.json"
        return p

    def list_tombstones(self) -> List[str]:
        p = self._tombstone_path()
        if not p.is_file():
            return []
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return list(data.get("keys") or [])
        except Exception:
            return []

    def is_tombstoned(self, team_id: str, agent_id: str) -> bool:
        return memory_key(team_id, agent_id) in self.list_tombstones()

    def add_tombstone(self, team_id: str, agent_id: str, reason: str = "") -> None:
        keys = set(self.list_tombstones())
        k = memory_key(team_id, agent_id)
        keys.add(k)
        payload = {
            "keys": sorted(keys),
            "entries": {
                **(self._tombstone_entries()),
                k: {"at": _now_ms(), "reason": reason or "destroy"},
            },
        }
        p = self._tombstone_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)

    def _tombstone_entries(self) -> Dict[str, Any]:
        p = self._tombstone_path()
        if not p.is_file():
            return {}
        try:
            return dict(json.loads(p.read_text(encoding="utf-8")).get("entries") or {})
        except Exception:
            return {}

    def _load_meta(self, team_id: str, agent_id: str) -> Dict[str, Any]:
        data = self.store.load(team_id, agent_id, "meta", {})
        return data if isinstance(data, dict) else {}

    def _save_meta(self, team_id: str, agent_id: str, meta: Dict[str, Any]) -> None:
        self.store.save(team_id, agent_id, "meta", meta)

    def _append_audit(self, team_id: str, agent_id: str, entry: Dict[str, Any]) -> None:
        d = self.store.agent_dir(team_id, agent_id)
        path = d / "audit.jsonl"
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(line)

    def resolve_state(self, team_id: str, agent_id: str) -> str:
        if self.is_tombstoned(team_id, agent_id):
            return "destroyed"
        meta = self._load_meta(team_id, agent_id)
        explicit = meta.get("state")
        if explicit in STATES:
            return str(explicit)
        # 从遗留字段推导
        if self.store.exists_layer(team_id, agent_id, "legacy") or meta.get("sealed"):
            return "sealed"
        if meta.get("bound") is False:
            return "unbound"
        # 显式绑定过 / shared 标记
        if meta.get("bound") is True or meta.get("bound_at") or meta.get("shared"):
            if meta.get("shared"):
                return "shared"
            return "active"
        # 已有四层数据（旧数据兼容）→ active
        for layer in ("log", "perception", "intentions", "affect"):
            if self.store.exists_layer(team_id, agent_id, layer):
                return "active"
        return "unbound"

    def assert_readable(self, team_id: str, agent_id: str) -> None:
        if self.is_tombstoned(team_id, agent_id):
            raise MemoryLifecycleError("memory_destroyed", "记忆已销毁（tombstone）")

    def assert_writable(self, team_id: str, agent_id: str) -> None:
        self.assert_readable(team_id, agent_id)
        st = self.resolve_state(team_id, agent_id)
        if st in ("sealed", "archived", "transferring", "unbound", "destroyed"):
            raise MemoryLifecycleError(
                "memory_not_writable",
                f"当前状态 {st} 不可写（需 active/shared）",
            )

    def get_status(self, team_id: str, agent_id: str) -> Dict[str, Any]:
        meta = self._load_meta(team_id, agent_id)
        state = self.resolve_state(team_id, agent_id)
        persona = meta.get("persona") or "hybrid"
        if persona not in PERSONAS:
            persona = "hybrid"
        autonomy = dict(meta.get("autonomy") or {})
        return {
            "team_id": team_id,
            "agent_id": agent_id,
            "state": state,
            "persona": persona,
            "autonomy": autonomy,
            "bound": state not in ("unbound", "destroyed"),
            "sealed": state in ("sealed", "archived"),
            "destroyed": state == "destroyed",
            "tombstoned": self.is_tombstoned(team_id, agent_id),
            "schema": "ag.memory.lifecycle/v1",
        }

    def set_persona(
        self,
        team_id: str,
        agent_id: str,
        persona: str = "hybrid",
        autonomy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.assert_readable(team_id, agent_id)
        if persona not in PERSONAS:
            raise MemoryLifecycleError("invalid_persona", f"persona must be one of {PERSONAS}")
        meta = self._load_meta(team_id, agent_id)
        meta["persona"] = persona
        if autonomy is not None:
            meta["autonomy"] = dict(autonomy)
        else:
            # 切换 Persona 时重置为该预设默认自主策略
            meta["autonomy"] = _default_autonomy(persona)
        # 拟生拓扑随 Persona 重置（动态架构）
        try:
            from .agent_memory_core import AgentMemoryCore

            meta["topology"] = AgentMemoryCore._default_topology(persona)
        except Exception:
            pass
        self._save_meta(team_id, agent_id, meta)
        self._append_audit(
            team_id,
            agent_id,
            {"t": _now_ms(), "action": "set_persona", "persona": persona},
        )
        return self.get_status(team_id, agent_id)

    def transition(
        self,
        team_id: str,
        agent_id: str,
        action: str,
        *,
        force: bool = False,
        reason: str = "",
    ) -> Dict[str, Any]:
        action = (action or "").strip().lower()
        if action not in TRANSITIONS and action != "save":
            raise MemoryLifecycleError("unknown_action", f"unknown action: {action}")

        if self.is_tombstoned(team_id, agent_id) and action != "destroy":
            raise MemoryLifecycleError("memory_destroyed", "记忆已销毁")

        # save = 固化（不改 state，仅 compress + audit）
        if action == "save":
            self.assert_writable(team_id, agent_id)
            core = AgentMemoryCore(team_id, agent_id, store=self.store)
            comp = core.perception.compress(core.log)
            consolidated = core.consolidate_tick(max_new=5)
            forgotten = core.forget_tick()
            reflected = False
            try:
                from .agent_memory_runtime import maybe_reflect

                reflected = maybe_reflect(
                    team_id,
                    agent_id,
                    store=self.store,
                    core=core,
                    status=self.get_status(team_id, agent_id),
                    force=True,
                )
            except Exception:
                reflected = False
            self._append_audit(
                team_id,
                agent_id,
                {
                    "t": _now_ms(),
                    "action": "save",
                    "compressed": bool(comp and comp.get("event")),
                    "consolidated": (consolidated or {}).get("consolidated"),
                    "forgotten": (forgotten or {}).get("forgotten"),
                    "reflected": reflected,
                    "reason": reason,
                },
            )
            return {
                "ok": True,
                "action": "save",
                "state": self.resolve_state(team_id, agent_id),
                "consolidated": consolidated,
                "forgotten": forgotten,
                "compressed": bool(comp),
                "reflected": reflected,
                "detail": (comp or {}).get("detail"),
                "status": self.get_status(team_id, agent_id),
            }

        allowed_from, to_state = TRANSITIONS[action]
        cur = self.resolve_state(team_id, agent_id)
        if cur == "destroyed" and action == "destroy":
            return {
                "ok": True,
                "action": "destroy",
                "state": "destroyed",
                "already": True,
                "status": self.get_status(team_id, agent_id),
            }
        if cur not in allowed_from and not force:
            raise MemoryLifecycleError(
                "illegal_transition",
                f"不能从 {cur} 执行 {action}（允许: {sorted(allowed_from)}）",
            )

        meta = self._load_meta(team_id, agent_id)
        now = _now_ms()

        if action == "bind":
            meta["bound"] = True
            meta.setdefault("bound_at", now)
            meta.setdefault("persona", "hybrid")
            meta.setdefault("autonomy", _default_autonomy("hybrid"))
        elif action == "unbind":
            meta["bound"] = False
            meta["unbound_at"] = now
        elif action == "seal":
            core = AgentMemoryCore(team_id, agent_id, store=self.store)
            core.seal(now)
            meta["sealed"] = True
            meta["sealed_at"] = now
        elif action == "unseal":
            # 移除 legacy 写锁标记，保留快照文件为 history_legacy 可选
            meta["sealed"] = False
            meta["unsealed_at"] = now
            # 将 legacy 改名为 history 以免 is_sealed 仍为 true
            legacy_path = self.store.path(team_id, agent_id, "legacy")
            if legacy_path.is_file():
                hist = self.store.path(team_id, agent_id, f"legacy_history_{now}")
                try:
                    legacy_path.replace(hist)
                except Exception:
                    legacy_path.unlink(missing_ok=True)
        elif action == "share":
            meta["shared"] = True
        elif action == "unshare":
            meta["shared"] = False
        elif action == "destroy":
            self._destroy_files(team_id, agent_id)
            self.add_tombstone(team_id, agent_id, reason=reason or "destroy")
            meta = {
                "state": "destroyed",
                "destroyed_at": now,
                "bound": False,
                "sealed": False,
            }
            # 仍写一个空 meta 目录？destroy 已删目录，tombstone 足够
            self._append_audit_global(
                {
                    "t": now,
                    "action": "destroy",
                    "team_id": team_id,
                    "agent_id": agent_id,
                    "reason": reason,
                }
            )
            return {
                "ok": True,
                "action": "destroy",
                "state": "destroyed",
                "status": {
                    "team_id": team_id,
                    "agent_id": agent_id,
                    "state": "destroyed",
                    "destroyed": True,
                    "tombstoned": True,
                },
            }

        meta["state"] = to_state
        meta["last_transition"] = {"action": action, "from": cur, "to": to_state, "t": now}
        self._save_meta(team_id, agent_id, meta)
        self._append_audit(
            team_id,
            agent_id,
            {
                "t": now,
                "action": action,
                "from": cur,
                "to": to_state,
                "reason": reason,
            },
        )
        return {
            "ok": True,
            "action": action,
            "from": cur,
            "to": to_state,
            "state": to_state,
            "status": self.get_status(team_id, agent_id),
        }

    def _destroy_files(self, team_id: str, agent_id: str) -> None:
        d = self.store.agent_dir(team_id, agent_id)
        if d.is_dir():
            try:
                shutil.rmtree(d)
            except Exception as e:
                logger.warning("destroy memory dir failed %s: %s", d, e)

    def _append_audit_global(self, entry: Dict[str, Any]) -> None:
        path = self.store.root / "_global_audit.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_audit(self, team_id: str, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        path = self.store.agent_dir(team_id, agent_id) / "audit.jsonl"
        if not path.is_file():
            return []
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        out = []
        for line in lines[-max(1, limit) :]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def team_overview(self, team_id: str, agents: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """汇总团队下 agents 的记忆状态。"""
        rows = []
        agents = agents or []
        for a in agents:
            aid = a.get("agent_id") or a.get("id") or ""
            if not aid:
                continue
            try:
                st = self.get_status(team_id, aid)
                counts = {}
                health = 0
                memory_style = {}
                dynamic_state = {}
                if st["state"] not in ("destroyed",):
                    try:
                        self.assert_readable(team_id, aid)
                        core = AgentMemoryCore(team_id, aid, store=self.store)
                        counts = core.counts()
                        memory_style = core.memory_style()
                        dynamic_state = core.dynamic_state()
                        # 简易健康分 0–100：有绑定+有日志+有意图/感知/语气
                        health = 20 if st.get("bound") else 0
                        if counts.get("log", 0) > 0:
                            health += min(40, 10 + counts["log"] * 2)
                        if counts.get("perception", 0) > 0:
                            health += min(15, 5 + counts["perception"])
                        if counts.get("intentions_pending", 0) > 0:
                            health += 10
                        if counts.get("affect_labels", 0) > 0:
                            health += 10
                        if st.get("persona") in ("xiaoman", "shenmian", "hybrid"):
                            health += 5
                        if st.get("state") == "sealed":
                            health = min(health, 70)  # 封存后不再成长
                        health = max(0, min(100, health))
                    except MemoryLifecycleError:
                        pass
                rows.append(
                    {
                        **st,
                        "name": a.get("name") or aid,
                        "role": a.get("role") or "",
                        "counts": counts,
                        "health": health,
                        "memory_style": memory_style if st["state"] not in ("destroyed",) else {},
                        "dynamic_state": dynamic_state if st["state"] not in ("destroyed",) else {},
                    }
                )
            except Exception as e:
                rows.append({"agent_id": aid, "error": str(e), "health": 0})
        by_state: Dict[str, int] = {}
        by_persona: Dict[str, int] = {}
        healths = [int(r.get("health") or 0) for r in rows if "error" not in r]
        for r in rows:
            by_state[r.get("state") or "?"] = by_state.get(r.get("state") or "?", 0) + 1
            by_persona[r.get("persona") or "hybrid"] = by_persona.get(r.get("persona") or "hybrid", 0) + 1
        t_clean, _ = _safe_team_agent(team_id, "x")
        tombs = [k for k in self.list_tombstones() if k.startswith(f"{t_clean}:")]
        return {
            "team_id": team_id,
            "agents": rows,
            "by_state": by_state,
            "by_persona": by_persona,
            "tombstones": tombs,
            "health_avg": round(sum(healths) / len(healths), 1) if healths else 0,
            "active_memory_agents": by_state.get("active", 0) + by_state.get("shared", 0),
        }


def _default_autonomy(persona: str) -> Dict[str, Any]:
    if persona == "xiaoman":
        return {
            "auto_log_on_task": True,
            "auto_perceive_on_tool": True,
            "auto_compress_threshold": 40,
            "auto_recall_on_chat": True,
            "auto_feel_on_outcome": True,
            "reflection_interval_hours": 0,
            "recall_min_importance": 1,
        }
    if persona == "shenmian":
        return {
            "auto_log_on_task": True,
            "auto_perceive_on_tool": False,
            "auto_compress_threshold": 80,
            "auto_recall_on_chat": True,
            "auto_feel_on_outcome": False,
            "reflection_interval_hours": 24,
            "recall_min_importance": 6,
        }
    # hybrid
    return {
        "auto_log_on_task": True,
        "auto_perceive_on_tool": True,
        "auto_compress_threshold": 50,
        "auto_recall_on_chat": True,
        "auto_feel_on_outcome": True,
        "reflection_interval_hours": 48,
        "recall_min_importance": 3,
    }


_lifecycle: Optional[AgentMemoryLifecycle] = None


def get_memory_lifecycle() -> AgentMemoryLifecycle:
    global _lifecycle
    if _lifecycle is None:
        _lifecycle = AgentMemoryLifecycle()
    return _lifecycle
