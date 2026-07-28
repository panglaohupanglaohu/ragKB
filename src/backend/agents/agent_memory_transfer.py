# -*- coding: utf-8 -*-
"""Agent 记忆传递：薄适配层 → Will / 迁移引擎.

旧 execute() API 保留，内部改为 create_will → preflight → execute_will。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_memory_core import AgentMemoryStore, get_memory_store
from .agent_memory_lifecycle import (
    AgentMemoryLifecycle,
    MemoryLifecycleError,
)
from .agent_memory_migration import (
    MemoryMigrationError,
    MemoryMigrationService,
    get_memory_migration,
    list_migration_txs,
)


class AgentMemoryTransfer:
    def __init__(
        self,
        store: Optional[AgentMemoryStore] = None,
        lifecycle: Optional[AgentMemoryLifecycle] = None,
        migration: Optional[MemoryMigrationService] = None,
    ):
        self.store = store or get_memory_store()
        self.lc = lifecycle or AgentMemoryLifecycle(store=self.store)
        self.migration = migration or MemoryMigrationService(store=self.store, lifecycle=self.lc)

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
        strategy: str = "merge",
    ) -> Dict[str, Any]:
        if not to_agent_id or to_agent_id == from_agent_id:
            raise MemoryLifecycleError("invalid_beneficiary", "受益者必须是其他 agent")
        self.lc.assert_readable(team_id, from_agent_id)
        if self.lc.is_tombstoned(team_id, to_agent_id):
            raise MemoryLifecycleError("beneficiary_destroyed", "受益者记忆已销毁")

        cur = self.lc.resolve_state(team_id, from_agent_id)
        if cur not in ("active", "shared", "sealed", "transferring"):
            raise MemoryLifecycleError(
                "illegal_transition",
                f"状态 {cur} 不可发起传递",
            )

        try:
            result = self.migration.transfer_via_will(
                team_id,
                from_agent_id,
                to_agent_id,
                handover_intentions=handover_intentions,
                keep_memorial=keep_memorial,
                layers=layers,
                strategy=strategy or "merge",
                note=note,
            )
        except MemoryMigrationError as e:
            raise MemoryLifecycleError(e.code, e.detail) from e

        transfer = result.get("transfer") or {}
        # enrich narrative for UI compatibility
        from .agent_memory_core import AgentMemoryCore

        src = AgentMemoryCore(team_id, from_agent_id, store=self.store)
        narrative = src.transfer_narrative(
            persona=(self.lc.get_status(team_id, from_agent_id).get("persona") or "hybrid"),
            to_agent_id=to_agent_id,
            copied=transfer.get("copied") or {},
            keep_memorial=keep_memorial,
        )
        if isinstance(transfer, dict):
            transfer = dict(transfer)
            transfer["narrative"] = narrative
            transfer["disclosure"] = "这是回放，不是本人" if keep_memorial else None
            path = self._transfer_dir() / f"{transfer.get('transfer_id')}.json"
            if path.is_file():
                try:
                    disk = json.loads(path.read_text(encoding="utf-8"))
                    disk["narrative"] = narrative
                    path.write_text(json.dumps(disk, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    pass

        return {
            "ok": True,
            "transfer": transfer,
            "will": result.get("will"),
            "execution": result.get("execution"),
            "memorial_path": f"/api/v1/agent-memory/{team_id}/{from_agent_id}"
            if keep_memorial
            else None,
            "beneficiary_status": self.lc.get_status(team_id, to_agent_id),
            "source_status": self.lc.get_status(team_id, from_agent_id),
        }

    def list_transfers(self, team_id: str = "", limit: int = 30) -> List[Dict[str, Any]]:
        rows = []
        d = self._transfer_dir()
        files = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files[: limit * 2]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if team_id and data.get("team_id") != team_id:
                    continue
                rows.append(data)
            except Exception:
                continue
            if len(rows) >= limit:
                break
        return rows

    def list_migration_audit(self, limit: int = 30) -> List[Dict[str, Any]]:
        return list_migration_txs(self.store, limit=limit)


_transfer: Optional[AgentMemoryTransfer] = None


def get_memory_transfer() -> AgentMemoryTransfer:
    global _transfer
    if _transfer is None:
        _transfer = AgentMemoryTransfer()
    return _transfer
