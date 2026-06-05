# -*- coding: utf-8 -*-
"""Unified evidence run storage for verifiable agent/system execution.

EvidenceRun is the shared proof object used by skill verification, agent loops,
evolution validation, and cost gates. It is intentionally append-only: callers
create evidence records and query them later by object ids.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "evidence_runs"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _atomic_write(path: Path, data: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(data, encoding="utf-8")
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _month_dir(base_dir: Path, timestamp: Optional[str] = None) -> Path:
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    return base_dir / dt.strftime("%Y-%m")


@dataclass(frozen=True)
class EvidenceRun:
    """Append-only proof record for one verification or execution run."""

    evidence_id: str
    evidence_type: str
    status: str
    created_at: str
    summary: str = ""
    team_id: Optional[str] = None
    agent_id: Optional[str] = None
    skill_id: Optional[str] = None
    task_id: Optional[str] = None
    evolution_item_id: Optional[str] = None
    cost_target_id: Optional[str] = None
    plaza_topic_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    operation_id: Optional[str] = None
    runtime: Dict[str, Any] = field(default_factory=dict)
    command: str = ""
    exit_code: Optional[int] = None
    artifact_dir: str = ""
    stdout: str = ""
    stderr: str = ""
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    metrics_after: Dict[str, Any] = field(default_factory=dict)
    detail: Dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_hash:
            object.__setattr__(self, "evidence_hash", self._compute_hash())

    def _compute_hash(self) -> str:
        payload = self.to_dict(include_hash=False)
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def verify_integrity(self) -> bool:
        return self.evidence_hash == self._compute_hash()

    def to_dict(self, *, include_hash: bool = True) -> Dict[str, Any]:
        data = {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "status": self.status,
            "created_at": self.created_at,
            "summary": self.summary,
            "team_id": self.team_id,
            "agent_id": self.agent_id,
            "skill_id": self.skill_id,
            "task_id": self.task_id,
            "evolution_item_id": self.evolution_item_id,
            "cost_target_id": self.cost_target_id,
            "plaza_topic_id": self.plaza_topic_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "operation_id": self.operation_id,
            "runtime": self.runtime,
            "command": self.command,
            "exit_code": self.exit_code,
            "artifact_dir": self.artifact_dir,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "detail": self.detail,
            "schema_version": self.schema_version,
        }
        if include_hash:
            data["evidence_hash"] = self.evidence_hash
        return data

    @classmethod
    def create(
        cls,
        *,
        evidence_type: str,
        status: str,
        summary: str = "",
        evidence_id: str = "",
        created_at: str = "",
        **kwargs: Any,
    ) -> "EvidenceRun":
        return cls(
            evidence_id=evidence_id or f"EV-{uuid.uuid4().hex[:10]}",
            evidence_type=evidence_type,
            status=status,
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
            summary=summary,
            **kwargs,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceRun":
        return cls(
            evidence_id=data.get("evidence_id", ""),
            evidence_type=data.get("evidence_type", ""),
            status=data.get("status", ""),
            created_at=data.get("created_at", ""),
            summary=data.get("summary", ""),
            team_id=data.get("team_id"),
            agent_id=data.get("agent_id"),
            skill_id=data.get("skill_id"),
            task_id=data.get("task_id"),
            evolution_item_id=data.get("evolution_item_id"),
            cost_target_id=data.get("cost_target_id"),
            plaza_topic_id=data.get("plaza_topic_id"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            operation_id=data.get("operation_id"),
            runtime=data.get("runtime") or {},
            command=data.get("command", ""),
            exit_code=data.get("exit_code"),
            artifact_dir=data.get("artifact_dir", ""),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            metrics_before=data.get("metrics_before") or {},
            metrics_after=data.get("metrics_after") or {},
            detail=data.get("detail") or {},
            schema_version=data.get("schema_version", 1),
            evidence_hash=data.get("evidence_hash", ""),
        )


@dataclass
class EvidenceQuery:
    evidence_type: Optional[str] = None
    status: Optional[str] = None
    team_id: Optional[str] = None
    agent_id: Optional[str] = None
    skill_id: Optional[str] = None
    task_id: Optional[str] = None
    evolution_item_id: Optional[str] = None
    cost_target_id: Optional[str] = None
    plaza_topic_id: Optional[str] = None
    request_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100
    offset: int = 0

    def matches(self, run: EvidenceRun) -> bool:
        for field_name in (
            "evidence_type",
            "status",
            "team_id",
            "agent_id",
            "skill_id",
            "task_id",
            "evolution_item_id",
            "cost_target_id",
            "plaza_topic_id",
            "request_id",
        ):
            expected = getattr(self, field_name)
            if expected and getattr(run, field_name) != expected:
                return False
        if self.start_time and run.created_at < self.start_time:
            return False
        if self.end_time and run.created_at > self.end_time:
            return False
        return True


_OBJECT_FIELD_ALIASES = {
    "agent": "agent_id",
    "team": "team_id",
    "skill": "skill_id",
    "task": "task_id",
    "evolution": "evolution_item_id",
    "evolution_item": "evolution_item_id",
    "cost": "cost_target_id",
    "cost_target": "cost_target_id",
    "plaza": "plaza_topic_id",
    "plaza_topic": "plaza_topic_id",
    "request": "request_id",
}


class EvidenceStore:
    """JSON-backed append-only EvidenceRun store."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        self._base_dir = Path(base_dir) if base_dir else STORAGE_DIR
        self._lock = asyncio.Lock()
        self._cache: List[EvidenceRun] = []
        self._max_cache = 1000

    async def append_evidence(self, run: EvidenceRun) -> bool:
        async with self._lock:
            return self._append_unlocked(run)

    def append_evidence_sync(self, run: EvidenceRun) -> bool:
        """Synchronously append evidence from non-async channels."""
        return self._append_unlocked(run)

    def _append_unlocked(self, run: EvidenceRun) -> bool:
        month_dir = _month_dir(self._base_dir, run.created_at)
        _ensure_dir(month_dir)
        evidence_file = month_dir / f"{run.evidence_id}.json"
        _atomic_write(evidence_file, json.dumps(run.to_dict(), ensure_ascii=False, indent=2))
        self._cache.append(run)
        if len(self._cache) > self._max_cache:
            self._cache = self._cache[-self._max_cache:]
        logger.info("EvidenceRun recorded: %s type=%s status=%s", run.evidence_id, run.evidence_type, run.status)
        return True

    async def get_evidence(self, evidence_id: str) -> Optional[EvidenceRun]:
        for run in self._cache:
            if run.evidence_id == evidence_id:
                return run
        return await self._load_from_disk(evidence_id)

    async def query_evidence(self, q: EvidenceQuery) -> List[EvidenceRun]:
        if not q.start_time and not q.end_time:
            cached = [run for run in reversed(self._cache) if q.matches(run)]
            if len(cached) >= q.limit + q.offset:
                return cached[q.offset:q.offset + q.limit]
        results = await self._scan(q)
        return results[q.offset:q.offset + q.limit] if q.offset else results[:q.limit]

    def query_evidence_sync(self, q: EvidenceQuery) -> List[EvidenceRun]:
        """Synchronously query evidence from non-async services."""
        if not q.start_time and not q.end_time:
            cached = [run for run in reversed(self._cache) if q.matches(run)]
            if len(cached) >= q.limit + q.offset:
                return cached[q.offset:q.offset + q.limit]
        results = self._scan_sync(q)
        return results[q.offset:q.offset + q.limit] if q.offset else results[:q.limit]

    async def query_for_object(
        self,
        entity_type: str,
        entity_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EvidenceRun]:
        field_name = _OBJECT_FIELD_ALIASES.get(entity_type)
        if not field_name:
            return []
        q = EvidenceQuery(limit=limit, offset=offset)
        setattr(q, field_name, entity_id)
        return await self.query_evidence(q)

    async def verify_all(self) -> Dict[str, Any]:
        result = {"total": 0, "corrupt": 0, "details": []}
        if not self._base_dir.exists():
            return result
        for month_dir in sorted(d for d in self._base_dir.iterdir() if d.is_dir()):
            for evidence_file in month_dir.iterdir():
                if evidence_file.suffix != ".json":
                    continue
                try:
                    run = EvidenceRun.from_dict(json.loads(evidence_file.read_text(encoding="utf-8")))
                    result["total"] += 1
                    if not run.verify_integrity():
                        result["corrupt"] += 1
                        result["details"].append({
                            "file": str(evidence_file),
                            "evidence_id": run.evidence_id,
                            "error": "hash mismatch",
                        })
                except Exception as exc:
                    result["corrupt"] += 1
                    result["details"].append({"file": str(evidence_file), "error": str(exc)})
        return result

    async def _load_from_disk(self, evidence_id: str) -> Optional[EvidenceRun]:
        if not self._base_dir.exists():
            return None
        for month_dir in self._base_dir.iterdir():
            if not month_dir.is_dir():
                continue
            evidence_file = month_dir / f"{evidence_id}.json"
            if not evidence_file.exists():
                continue
            try:
                return EvidenceRun.from_dict(json.loads(evidence_file.read_text(encoding="utf-8")))
            except Exception as exc:
                logger.error("Failed to load EvidenceRun %s: %s", evidence_file, exc)
                return None
        return None

    async def _scan(self, q: EvidenceQuery) -> List[EvidenceRun]:
        results: List[EvidenceRun] = []
        if not self._base_dir.exists():
            return results
        months = sorted((d for d in self._base_dir.iterdir() if d.is_dir()), reverse=True)
        for month_dir in months:
            for evidence_file in sorted(month_dir.iterdir(), reverse=True):
                if evidence_file.suffix != ".json":
                    continue
                try:
                    run = EvidenceRun.from_dict(json.loads(evidence_file.read_text(encoding="utf-8")))
                except Exception:
                    continue
                if q.matches(run):
                    results.append(run)
                    if len(results) >= q.limit + q.offset:
                        return results
        return results

    def _scan_sync(self, q: EvidenceQuery) -> List[EvidenceRun]:
        results: List[EvidenceRun] = []
        if not self._base_dir.exists():
            return results
        months = sorted((d for d in self._base_dir.iterdir() if d.is_dir()), reverse=True)
        for month_dir in months:
            for evidence_file in sorted(month_dir.iterdir(), reverse=True):
                if evidence_file.suffix != ".json":
                    continue
                try:
                    run = EvidenceRun.from_dict(json.loads(evidence_file.read_text(encoding="utf-8")))
                except Exception:
                    continue
                if q.matches(run):
                    results.append(run)
                    if len(results) >= q.limit + q.offset:
                        return results
        return results


_evidence_store: Optional[EvidenceStore] = None


def get_evidence_store() -> EvidenceStore:
    global _evidence_store
    if _evidence_store is None:
        _evidence_store = EvidenceStore()
    return _evidence_store


def reset_evidence_store() -> None:
    global _evidence_store
    _evidence_store = None
