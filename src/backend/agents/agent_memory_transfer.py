# -*- coding: utf-8 -*-
"""Agent 记忆传递：执行遗嘱 — 复制到受益方 + 意图交接 + 可选凭吊.

原则：传递 = 复制；原件默认可凭吊（keep_memorial）；不静默销毁。
handover_intentions: ask_new_owner | auto | drop
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_memory_core import (
    AgentMemoryCore,
    AgentMemoryStore,
    MEMORY_SCHEMA,
    get_memory_store,
    _now_ms,
)
from .agent_memory_lifecycle import (
    AgentMemoryLifecycle,
    MemoryLifecycleError,
)

HANDOVER = ("ask_new_owner", "auto", "drop")


class AgentMemoryTransfer:
    def __init__(
        self,
        store: Optional[AgentMemoryStore] = None,
        lifecycle: Optional[AgentMemoryLifecycle] = None,
    ):
        self.store = store or get_memory_store()
        self.lc = lifecycle or AgentMemoryLifecycle(store=self.store)

    def _transfer_dir(self) -> Path:
        d = self.store.root / "_transfers"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def execute(
        self,
        team_id: str,
        from_agent_id: str,
        to_agent_id: str,
        *,
        handover_intentions: str = "ask_new_owner",
        keep_memorial: bool = True,
        layers: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        if not to_agent_id or to_agent_id == from_agent_id:
            raise MemoryLifecycleError("invalid_beneficiary", "受益者必须是其他 agent")
        self.lc.assert_readable(team_id, from_agent_id)
        if self.lc.is_tombstoned(team_id, to_agent_id):
            raise MemoryLifecycleError("beneficiary_destroyed", "受益者记忆已销毁")

        ho = handover_intentions if handover_intentions in HANDOVER else "ask_new_owner"
        layer_set = layers or ["log", "perception", "intentions", "affect"]
        now = _now_ms()
        transfer_id = f"tr_{uuid.uuid4().hex[:12]}"

        cur = self.lc.resolve_state(team_id, from_agent_id)
        if cur not in ("active", "shared", "sealed", "transferring"):
            raise MemoryLifecycleError(
                "illegal_transition",
                f"状态 {cur} 不可发起传递",
            )

        src = AgentMemoryCore(team_id, from_agent_id, store=self.store)
        blob = src.export_all()
        layers_data = blob.get("layers") or {}

        # 受益方确保 active
        to_state = self.lc.resolve_state(team_id, to_agent_id)
        if to_state == "destroyed":
            raise MemoryLifecycleError("beneficiary_destroyed", "受益者已销毁")
        if to_state in ("unbound",):
            try:
                self.lc.transition(team_id, to_agent_id, "bind", reason="transfer_beneficiary")
            except MemoryLifecycleError:
                pass

        dst = AgentMemoryCore(team_id, to_agent_id, store=self.store)

        # 3) 复制各层（merge：追加而非整盘覆盖，避免抹掉受益方已有记忆）
        copied = {}
        if "log" in layer_set:
            events = list(layers_data.get("log") or [])
            for e in events:
                e = dict(e)
                e["id"] = e.get("id") or f"ev_xfer_{uuid.uuid4().hex[:8]}"
                tags = list(e.get("tags") or [])
                if "传递继承" not in tags:
                    tags.append("传递继承")
                e["tags"] = tags
                e["place"] = (e.get("place") or "") + f" [from:{from_agent_id}]"
                dst.log.events.append(e)
            dst.log._save()
            copied["log"] = len(events)

        if "perception" in layer_set:
            buf = list(layers_data.get("perception") or [])
            for item in buf:
                dst.perception.buffer.append(dict(item))
            if len(dst.perception.buffer) > 500:
                dst.perception.buffer = dst.perception.buffer[-500:]
            dst.perception._save()
            copied["perception"] = len(buf)

        pending_for_ask: List[Dict[str, Any]] = []
        if "intentions" in layer_set:
            intentions = list(layers_data.get("intentions") or [])
            if ho == "drop":
                copied["intentions"] = 0
                copied["intentions_dropped"] = len(intentions)
            else:
                n = 0
                for it in intentions:
                    it = dict(it)
                    if it.get("status") != "pending":
                        continue
                    it["id"] = f"in_xfer_{uuid.uuid4().hex[:8]}"
                    it["creator"] = it.get("creator") or from_agent_id
                    it["handover"] = {
                        "from": from_agent_id,
                        "policy": ho,
                        "transferred_at": now,
                    }
                    if ho == "ask_new_owner":
                        it["status"] = "pending"
                        it["trigger"] = (it.get("trigger") or "") + " [待新主人确认]"
                        pending_for_ask.append(it)
                    # auto & ask: both copy as pending
                    dst.intentions.items.append(it)
                    n += 1
                dst.intentions._save()
                copied["intentions"] = n

        if "affect" in layer_set:
            aff = layers_data.get("affect") or {}
            if isinstance(aff, dict) and (aff.get("labels") or aff.get("valence")):
                # 合并标签（取 max 强度）
                cur_aff = dst.affect.state
                for lab, inten in (aff.get("labels") or {}).items():
                    prev = float((cur_aff.get("labels") or {}).get(lab) or 0)
                    cur_aff.setdefault("labels", {})[lab] = max(prev, float(inten or 0))
                cur_aff["valence"] = (
                    float(cur_aff.get("valence") or 0) * 0.5
                    + float(aff.get("valence") or 0) * 0.5
                )
                cur_aff["arousal"] = (
                    float(cur_aff.get("arousal") or 0) * 0.5
                    + float(aff.get("arousal") or 0) * 0.5
                )
                cur_aff["updatedAt"] = now
                dst.affect._save()
                copied["affect"] = True
            else:
                copied["affect"] = False

        # 受益方记录继承日志
        dst.log.append(
            {
                "subject": to_agent_id,
                "action": "记忆继承",
                "detail": f"自 {from_agent_id} 传递接收；策略={ho}；{note}"[:500],
                "importance": 9,
                "tags": ["传递", "继承", from_agent_id],
            }
        )

        # 4) 源：先封存（若需凭吊），再标记 archived
        if keep_memorial:
            st_now = self.lc.resolve_state(team_id, from_agent_id)
            if st_now in ("active", "shared") and not src.is_sealed():
                try:
                    self.lc.transition(team_id, from_agent_id, "seal", reason="transfer_memorial")
                except MemoryLifecycleError:
                    src.seal(now)
            elif not src.is_sealed():
                src.seal(now)
            # 直接落 archived（传递完成）
            meta = self.store.load(team_id, from_agent_id, "meta", {}) or {}
            if not isinstance(meta, dict):
                meta = {}
            meta["state"] = "archived"
            meta["sealed"] = True
            meta["transferred_to"] = to_agent_id
            meta["transfer_id"] = transfer_id
            meta["transferred_at"] = now
            self.store.save(team_id, from_agent_id, "meta", meta)
        else:
            meta = self.store.load(team_id, from_agent_id, "meta", {}) or {}
            if not isinstance(meta, dict):
                meta = {}
            meta["state"] = "sealed" if src.is_sealed() else "active"
            meta["transferred_to"] = to_agent_id
            meta["transfer_id"] = transfer_id
            meta["transferred_at"] = now
            self.store.save(team_id, from_agent_id, "meta", meta)

        # 受益方 state active
        meta_b = self.store.load(team_id, to_agent_id, "meta", {}) or {}
        if isinstance(meta_b, dict):
            meta_b["state"] = "active"
            meta_b["bound"] = True
            meta_b["inherited_from"] = from_agent_id
            meta_b["transfer_id"] = transfer_id
            self.store.save(team_id, to_agent_id, "meta", meta_b)

        record = {
            "transfer_id": transfer_id,
            "team_id": team_id,
            "from": from_agent_id,
            "to": to_agent_id,
            "handover_intentions": ho,
            "keep_memorial": keep_memorial,
            "layers": layer_set,
            "copied": copied,
            "pending_confirm_intentions": len(pending_for_ask),
            "note": note,
            "at": now,
            "schema": "ag.transfer/v1",
            "disclosure": "这是回放，不是本人" if keep_memorial else None,
        }
        path = self._transfer_dir() / f"{transfer_id}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        self.lc._append_audit(
            team_id,
            from_agent_id,
            {"t": now, "action": "transfer_out", "to": to_agent_id, "transfer_id": transfer_id},
        )
        self.lc._append_audit(
            team_id,
            to_agent_id,
            {"t": now, "action": "transfer_in", "from": from_agent_id, "transfer_id": transfer_id},
        )

        return {
            "ok": True,
            "transfer": record,
            "memorial_path": f"/api/v1/agent-memory/{team_id}/{from_agent_id}"
            if keep_memorial
            else None,
            "beneficiary_status": self.lc.get_status(team_id, to_agent_id),
            "source_status": self.lc.get_status(team_id, from_agent_id),
        }

    def list_transfers(self, team_id: str = "", limit: int = 30) -> List[Dict[str, Any]]:
        rows = []
        d = self._transfer_dir()
        files = sorted(d.glob("tr_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files[:limit]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if team_id and data.get("team_id") != team_id:
                    continue
                rows.append(data)
            except Exception:
                continue
        return rows


_transfer: Optional[AgentMemoryTransfer] = None


def get_memory_transfer() -> AgentMemoryTransfer:
    global _transfer
    if _transfer is None:
        _transfer = AgentMemoryTransfer()
    return _transfer
