# -*- coding: utf-8 -*-
"""萃取管线事件溯源存储 — Append-only Event Store.

基于 JSON 文件的轻量级事件溯源存储：
- 追加写入（不可变事件流）
- 按 pipeline_id 分区
- 支持事件回放重建管线状态
- 线程安全（asyncio.Lock）
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .extraction_models import (
    ExtractionPipeline,
    PipelineStage,
    StageTransition,
    TransitionType,
    GateCheckResult,
    TodoItem,
    ReviewerRecord,
    default_gate_requirements,
)

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "extraction_pipelines"


class ExtractionStore:
    """事件溯源存储 — JSON 文件持久化 + 事件流."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self._dir = storage_dir or STORAGE_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

        # 内存缓存: pipeline_id → ExtractionPipeline
        self._cache: Dict[str, ExtractionPipeline] = {}

    # ── File paths ──────────────────────────────────────

    def _pipeline_file(self, pipeline_id: str) -> Path:
        return self._dir / f"{pipeline_id}.json"

    def _events_file(self, pipeline_id: str) -> Path:
        return self._dir / f"{pipeline_id}_events.jsonl"

    # ── Load / Save ─────────────────────────────────────

    def _load_pipeline(self, pipeline_id: str) -> Optional[ExtractionPipeline]:
        """从 JSON 文件加载管线快照."""
        fpath = self._pipeline_file(pipeline_id)
        if not fpath.is_file():
            return None
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            # Reconstruct enums
            data["current_stage"] = PipelineStage(data["current_stage"])
            gr = data.get("gate_requirements", {})
            from .extraction_models import GateRequirement, ReviewerIdentity
            data["gate_requirements"] = {
                PipelineStage(k): GateRequirement(**v)
                for k, v in gr.items()
            }
            data["reviewers"] = [ReviewerRecord(**r) for r in data.get("reviewers", [])]
            data["transitions"] = [StageTransition(**t) for t in data.get("transitions", [])]
            data["todos"] = [TodoItem(**td) for td in data.get("todos", [])]
            return ExtractionPipeline(**data)
        except Exception as e:
            logger.error(f"Failed to load pipeline {pipeline_id}: {e}")
            return None

    def _save_pipeline(self, pipeline: ExtractionPipeline) -> None:
        """保存管线快照（非事件溯源，仅用作缓存加速）."""
        fpath = self._pipeline_file(pipeline.pipeline_id)
        data = pipeline.model_dump()
        data["current_stage"] = pipeline.current_stage.value
        data["gate_requirements"] = {
            k.value: v.model_dump() for k, v in pipeline.gate_requirements.items()
        }
        data["reviewers"] = [r.model_dump() for r in pipeline.reviewers]
        data["transitions"] = [t.model_dump() for t in pipeline.transitions]
        data["todos"] = [t.model_dump() for t in pipeline.todos]
        fpath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_event(self, pipeline_id: str, event: StageTransition) -> None:
        """追加事件到 JSONL 事件流 (不可变)."""
        fpath = self._events_file(pipeline_id)
        event_dict = event.model_dump()
        event_dict["from_stage"] = event.from_stage.value
        event_dict["to_stage"] = event.to_stage.value
        with open(fpath, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")

    def _load_events(self, pipeline_id: str) -> List[StageTransition]:
        """加载指定管线的所有事件."""
        fpath = self._events_file(pipeline_id)
        if not fpath.is_file():
            return []
        events = []
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    d["from_stage"] = PipelineStage(d["from_stage"])
                    d["to_stage"] = PipelineStage(d["to_stage"])
                    if d.get("gate_result"):
                        d["gate_result"] = GateCheckResult(**d["gate_result"])
                    events.append(StageTransition(**d))
                except Exception as e:
                    logger.warning(f"Skip corrupt event line: {e}")
        return events

    # ── CRUD ────────────────────────────────────────────

    async def create_pipeline(
        self,
        name: str = "Untitled Pipeline",
        description: str = "",
        team_id: str = "",
        created_by: str = "",
        tags: Optional[list] = None,
        gate_requirements: Optional[Dict[PipelineStage, Any]] = None,
    ) -> ExtractionPipeline:
        """创建新萃取管线."""
        async with self._lock:
            pipeline = ExtractionPipeline(
                name=name,
                description=description,
                team_id=team_id,
                created_by=created_by,
                tags=tags or [],
                gate_requirements=gate_requirements or default_gate_requirements(),
            )
            self._save_pipeline(pipeline)
            self._cache[pipeline.pipeline_id] = pipeline
            logger.info(f"📋 Pipeline created: {pipeline.pipeline_id} [{pipeline.name}]")
            return pipeline

    async def get_pipeline(self, pipeline_id: str) -> Optional[ExtractionPipeline]:
        """获取管线."""
        if pipeline_id in self._cache:
            return self._cache[pipeline_id]
        pipeline = self._load_pipeline(pipeline_id)
        if pipeline:
            self._cache[pipeline_id] = pipeline
        return pipeline

    async def list_pipelines(
        self,
        stage: Optional[PipelineStage] = None,
        team_id: Optional[str] = None,
    ) -> List[ExtractionPipeline]:
        """列出管线（支持按阶段/团队过滤）."""
        results = []
        for fpath in sorted(self._dir.glob("*.json")):
            if "_events" in fpath.name:
                continue
            pid = fpath.stem
            pipeline = await self.get_pipeline(pid)
            if pipeline is None:
                continue
            if stage and pipeline.current_stage != stage:
                continue
            if team_id and pipeline.team_id != team_id:
                continue
            results.append(pipeline)
        return results

    async def update_pipeline(self, pipeline_id: str, updates: Dict[str, Any]) -> Optional[ExtractionPipeline]:
        """更新管线元数据（不触发阶段迁移）."""
        async with self._lock:
            pipeline = await self.get_pipeline(pipeline_id)
            if pipeline is None:
                return None

            # 可安全更新的字段
            safe_fields = {"name", "description", "team_id", "tags", "payload"}
            for k, v in updates.items():
                if k in safe_fields and hasattr(pipeline, k):
                    setattr(pipeline, k, v)
                elif k == "gate_requirements" and isinstance(v, dict):
                    # 合并而非覆盖
                    from .extraction_models import GateRequirement
                    for stage_key, gr_data in v.items():
                        if isinstance(stage_key, str):
                            stage_key = PipelineStage(stage_key)
                        if isinstance(gr_data, dict):
                            pipeline.gate_requirements[stage_key] = GateRequirement(**gr_data)
                        else:
                            pipeline.gate_requirements[stage_key] = gr_data

            pipeline.version += 1
            pipeline.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_pipeline(pipeline)
            self._cache[pipeline_id] = pipeline
            return pipeline

    async def delete_pipeline(self, pipeline_id: str) -> bool:
        """删除管线及其事件流."""
        async with self._lock:
            pipeline_file = self._pipeline_file(pipeline_id)
            events_file = self._events_file(pipeline_id)
            existed = pipeline_file.is_file()
            if existed:
                pipeline_file.unlink(missing_ok=True)
            if events_file.is_file():
                events_file.unlink(missing_ok=True)
            self._cache.pop(pipeline_id, None)
            return existed

    # ── Event Sourcing: Transition ──────────────────────

    async def record_transition(
        self,
        pipeline_id: str,
        from_stage: PipelineStage,
        to_stage: PipelineStage,
        transition_type: TransitionType,
        triggered_by: str = "system",
        gate_result: Optional[GateCheckResult] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[StageTransition]:
        """记录阶段迁移事件并更新管线状态."""
        async with self._lock:
            pipeline = await self.get_pipeline(pipeline_id)
            if pipeline is None:
                logger.warning(f"Pipeline {pipeline_id} not found for transition")
                return None

            # 验证迁移合法性
            if pipeline.current_stage != from_stage:
                logger.warning(
                    f"Stage mismatch: pipeline is {pipeline.current_stage.value}, "
                    f"transition from {from_stage.value}"
                )
                return None

            # 创建事件
            event = StageTransition(
                pipeline_id=pipeline_id,
                from_stage=from_stage,
                to_stage=to_stage,
                transition_type=transition_type,
                triggered_by=triggered_by,
                gate_result=gate_result,
                metadata=metadata or {},
            )

            # 更新管线状态
            pipeline.current_stage = to_stage
            pipeline.transitions.append(event)
            pipeline.version += 1
            pipeline.updated_at = event.occurred_at

            # 持久化
            self._save_pipeline(pipeline)
            self._append_event(pipeline_id, event)
            self._cache[pipeline_id] = pipeline

            logger.info(
                f"🔄 Pipeline {pipeline_id}: {from_stage.value} → {to_stage.value} "
                f"[{transition_type.value}] by {triggered_by}"
            )
            return event

    async def replay_events(self, pipeline_id: str) -> List[StageTransition]:
        """回放事件流 — 返回所有历史迁移事件."""
        return self._load_events(pipeline_id)

    # ── Reviewers ───────────────────────────────────────

    async def add_reviewer(self, pipeline_id: str, reviewer: ReviewerRecord) -> Optional[ExtractionPipeline]:
        """添加复核记录."""
        async with self._lock:
            pipeline = await self.get_pipeline(pipeline_id)
            if pipeline is None:
                return None

            # 幂等：同一 reviewer_id + 同一 pipeline 只能有一条 active 记录
            existing = [r for r in pipeline.reviewers if r.reviewer_id == reviewer.reviewer_id]
            if existing:
                # 更新已有记录
                for r in existing:
                    r.action = reviewer.action
                    r.comment = reviewer.comment
                    r.identity = reviewer.identity
                    r.reviewed_at = datetime.now(timezone.utc).isoformat()
            else:
                reviewer.reviewed_at = datetime.now(timezone.utc).isoformat()
                pipeline.reviewers.append(reviewer)

            pipeline.version += 1
            pipeline.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_pipeline(pipeline)
            self._cache[pipeline_id] = pipeline
            return pipeline

    # ── Todos ───────────────────────────────────────────

    async def add_todo(self, pipeline_id: str, todo: TodoItem) -> Optional[ExtractionPipeline]:
        """添加待办事项."""
        async with self._lock:
            pipeline = await self.get_pipeline(pipeline_id)
            if pipeline is None:
                return None
            pipeline.todos.append(todo)
            pipeline.version += 1
            pipeline.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_pipeline(pipeline)
            self._cache[pipeline_id] = pipeline
            return pipeline

    async def update_todo(
        self, pipeline_id: str, todo_id: str, updates: Dict[str, Any]
    ) -> Optional[TodoItem]:
        """更新待办事项."""
        async with self._lock:
            pipeline = await self.get_pipeline(pipeline_id)
            if pipeline is None:
                return None
            for td in pipeline.todos:
                if td.todo_id == todo_id:
                    for k, v in updates.items():
                        if hasattr(td, k):
                            setattr(td, k, v)
                    pipeline.version += 1
                    pipeline.updated_at = datetime.now(timezone.utc).isoformat()
                    self._save_pipeline(pipeline)
                    self._cache[pipeline_id] = pipeline
                    return td
            return None

    async def get_todos(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
    ) -> List[TodoItem]:
        """获取待办列表."""
        from .extraction_models import TodoStatus
        results = []

        if pipeline_id:
            pipeline = await self.get_pipeline(pipeline_id)
            if pipeline:
                for td in pipeline.todos:
                    if status and td.status.value != status:
                        continue
                    if assignee_id and td.assignee_id != assignee_id:
                        continue
                    results.append(td)
        else:
            # 搜索所有管线
            pipelines = await self.list_pipelines()
            for p in pipelines:
                for td in p.todos:
                    if status and td.status.value != status:
                        continue
                    if assignee_id and td.assignee_id != assignee_id:
                        continue
                    results.append(td)

        return results

    # ── Stats ───────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """获取管线统计."""
        pipelines = await self.list_pipelines()
        stats = {
            "total_pipelines": len(pipelines),
            "by_stage": {},
            "total_todos": 0,
            "pending_todos": 0,
            "total_reviewers": 0,
        }
        for p in pipelines:
            stage_key = p.current_stage.value
            stats["by_stage"][stage_key] = stats["by_stage"].get(stage_key, 0) + 1
            stats["total_todos"] += len(p.todos)
            stats["pending_todos"] += sum(1 for t in p.todos if t.status.value == "pending")
            stats["total_reviewers"] += len(p.reviewers)
        return stats


# ── Global singleton ────────────────────────────────────

_store: Optional[ExtractionStore] = None


def get_extraction_store() -> ExtractionStore:
    global _store
    if _store is None:
        _store = ExtractionStore()
    return _store


def init_extraction_store(storage_dir: Optional[Path] = None) -> ExtractionStore:
    global _store
    _store = ExtractionStore(storage_dir=storage_dir)
    return _store
