# -*- coding: utf-8 -*-
"""Agent 记忆共享 ACL.

grant: owner team/agent → grantee agent（同 team 为主）
role: reader | co_writer
layer_mask: 可共享的层；默认不含 affect（沈弥安隐私边界）
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .agent_memory_core import (
    AgentMemoryCore,
    AgentMemoryStore,
    get_memory_store,
    _now_ms,
)
from .agent_memory_lifecycle import (
    AgentMemoryLifecycle,
    MemoryLifecycleError,
    get_memory_lifecycle,
)

LAYERS = ("log", "perception", "intentions", "affect")
ROLES = ("reader", "co_writer")
DEFAULT_LAYERS = ("log", "perception", "intentions")  # 默认不共享 affect
NEVER_DEFAULT = ("affect",)


class AgentMemoryShare:
    def __init__(
        self,
        store: Optional[AgentMemoryStore] = None,
        lifecycle: Optional[AgentMemoryLifecycle] = None,
    ):
        self.store = store or get_memory_store()
        self.lc = lifecycle or AgentMemoryLifecycle(store=self.store)

    def _load_shares(self, team_id: str, agent_id: str) -> List[Dict[str, Any]]:
        data = self.store.load(team_id, agent_id, "shares", [])
        return list(data) if isinstance(data, list) else []

    def _save_shares(self, team_id: str, agent_id: str, grants: List[Dict[str, Any]]) -> None:
        self.store.save(team_id, agent_id, "shares", grants)

    def list_grants(self, team_id: str, agent_id: str) -> List[Dict[str, Any]]:
        self.lc.assert_readable(team_id, agent_id)
        return self._load_shares(team_id, agent_id)

    def grant(
        self,
        team_id: str,
        owner_agent_id: str,
        grantee_agent_id: str,
        *,
        role: str = "reader",
        layers: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        if not grantee_agent_id or grantee_agent_id == owner_agent_id:
            raise MemoryLifecycleError("invalid_grantee", "grantee 必须是其他 agent")
        self.lc.assert_readable(team_id, owner_agent_id)
        st = self.lc.resolve_state(team_id, owner_agent_id)
        if st in ("unbound", "destroyed"):
            raise MemoryLifecycleError("not_shareable", f"状态 {st} 不可共享")

        role = role if role in ROLES else "reader"
        mask = [L for L in (layers or list(DEFAULT_LAYERS)) if L in LAYERS]
        if not mask:
            mask = list(DEFAULT_LAYERS)

        # 沈弥安：若 persona 要求 never share affect，强制剥离
        meta = self.store.load(team_id, owner_agent_id, "meta", {}) or {}
        persona = (meta.get("persona") if isinstance(meta, dict) else None) or "hybrid"
        privacy = (meta.get("privacy") if isinstance(meta, dict) else None) or {}
        never = set(privacy.get("never_share_layers") or [])
        if persona == "shenmian":
            never.add("affect")
        mask = [L for L in mask if L not in never]
        if not mask:
            raise MemoryLifecycleError("empty_layer_mask", "可共享层为空（隐私策略拦截）")

        grants = self._load_shares(team_id, owner_agent_id)
        grants = [g for g in grants if g.get("grantee") != grantee_agent_id]
        entry = {
            "grantee": grantee_agent_id,
            "role": role,
            "layers": mask,
            "note": (note or "")[:200],
            "granted_at": _now_ms(),
        }
        grants.append(entry)
        self._save_shares(team_id, owner_agent_id, grants)

        # 生命周期标记 shared
        try:
            cur = self.lc.resolve_state(team_id, owner_agent_id)
            if cur == "active":
                self.lc.transition(team_id, owner_agent_id, "share", reason="grant")
        except MemoryLifecycleError:
            pass

        self.lc._append_audit(
            team_id,
            owner_agent_id,
            {
                "t": _now_ms(),
                "action": "share_grant",
                "grantee": grantee_agent_id,
                "role": role,
                "layers": mask,
            },
        )
        return {"ok": True, "grant": entry, "grants": grants}

    def revoke(self, team_id: str, owner_agent_id: str, grantee_agent_id: str) -> Dict[str, Any]:
        self.lc.assert_readable(team_id, owner_agent_id)
        grants = self._load_shares(team_id, owner_agent_id)
        new_grants = [g for g in grants if g.get("grantee") != grantee_agent_id]
        if len(new_grants) == len(grants):
            raise MemoryLifecycleError("grant_not_found", "未找到对该 grantee 的授权")
        self._save_shares(team_id, owner_agent_id, new_grants)
        if not new_grants:
            try:
                if self.lc.resolve_state(team_id, owner_agent_id) == "shared":
                    self.lc.transition(team_id, owner_agent_id, "unshare", reason="revoke_last")
            except MemoryLifecycleError:
                pass
        self.lc._append_audit(
            team_id,
            owner_agent_id,
            {"t": _now_ms(), "action": "share_revoke", "grantee": grantee_agent_id},
        )
        return {"ok": True, "grants": new_grants}

    def can_access(
        self,
        team_id: str,
        owner_agent_id: str,
        reader_agent_id: str,
        layer: str,
        *,
        need_write: bool = False,
    ) -> bool:
        if owner_agent_id == reader_agent_id:
            return True
        for g in self._load_shares(team_id, owner_agent_id):
            if g.get("grantee") != reader_agent_id:
                continue
            if layer not in (g.get("layers") or []):
                return False
            if need_write and g.get("role") != "co_writer":
                return False
            return True
        return False

    def read_shared_layer(
        self,
        team_id: str,
        owner_agent_id: str,
        reader_agent_id: str,
        layer: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        self.lc.assert_readable(team_id, owner_agent_id)
        if not self.can_access(team_id, owner_agent_id, reader_agent_id, layer):
            raise MemoryLifecycleError("share_denied", f"无权读取 {owner_agent_id}.{layer}")
        core = AgentMemoryCore(team_id, owner_agent_id, store=self.store)
        if layer == "log":
            data = core.log.replay()[-limit:]
        elif layer == "perception":
            data = core.perception.to_json()[-limit:]
        elif layer == "intentions":
            data = core.intentions.all()[-limit:]
        elif layer == "affect":
            data = core.affect.residue()
        else:
            raise MemoryLifecycleError("invalid_layer", layer)
        return {
            "ok": True,
            "owner": owner_agent_id,
            "reader": reader_agent_id,
            "layer": layer,
            "data": data,
        }

    def write_shared_log(
        self,
        team_id: str,
        owner_agent_id: str,
        writer_agent_id: str,
        event: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """co_writer 向 owner 的 log 层追加一条事件（带 provenance）."""
        event = event or {}
        self.lc.assert_readable(team_id, owner_agent_id)
        st = self.lc.resolve_state(team_id, owner_agent_id)
        if st in ("sealed", "archived", "destroyed", "unbound", "transferring"):
            raise MemoryLifecycleError("not_writable", f"owner 状态 {st} 不可写")
        if not self.can_access(
            team_id, owner_agent_id, writer_agent_id, "log", need_write=True
        ):
            raise MemoryLifecycleError(
                "share_denied", f"无权协作写 {owner_agent_id}.log（需 co_writer）"
            )
        core = AgentMemoryCore(team_id, owner_agent_id, store=self.store)
        payload = {
            "subject": event.get("subject") or writer_agent_id,
            "action": event.get("action") or "协作写入",
            "detail": (event.get("detail") or "")[:800],
            "place": event.get("place") or f"share:{writer_agent_id}",
            "importance": max(1, min(10, int(event.get("importance") or 5))),
            "tags": list(event.get("tags") or []) + ["共享协作", writer_agent_id],
        }
        # 去重 tags
        seen = set()
        tags = []
        for t in payload["tags"]:
            s = str(t)
            if s and s not in seen:
                seen.add(s)
                tags.append(s)
        payload["tags"] = tags
        written = core.log.append(payload)
        self.lc._append_audit(
            team_id,
            owner_agent_id,
            {
                "t": _now_ms(),
                "action": "share_cowrite",
                "writer": writer_agent_id,
                "event_id": written.get("id"),
            },
        )
        return {"ok": True, "event": written}

    def matrix(self, team_id: str, agent_ids: List[str]) -> Dict[str, Any]:
        """owner × grantee 授权摘要，供共享矩阵 UI。"""
        cells = []
        for owner in agent_ids:
            try:
                if self.lc.is_tombstoned(team_id, owner):
                    continue
                grants = self._load_shares(team_id, owner)
            except Exception:
                grants = []
            for g in grants:
                cells.append(
                    {
                        "owner": owner,
                        "grantee": g.get("grantee"),
                        "role": g.get("role"),
                        "layers": g.get("layers") or [],
                        "granted_at": g.get("granted_at"),
                    }
                )
        return {"team_id": team_id, "cells": cells, "layers": list(LAYERS)}

    def shared_with_me(self, team_id: str, reader_agent_id: str, agent_ids: List[str]) -> List[Dict]:
        out = []
        for owner in agent_ids:
            if owner == reader_agent_id:
                continue
            grants = self._load_shares(team_id, owner)
            for g in grants:
                if g.get("grantee") == reader_agent_id:
                    out.append({"owner": owner, **g})
        return out


_share: Optional[AgentMemoryShare] = None


def get_memory_share() -> AgentMemoryShare:
    global _share
    if _share is None:
        _share = AgentMemoryShare()
    return _share
