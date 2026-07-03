# -*- coding: utf-8 -*-
"""任务持久化存储 — 将任务序列化到 JSON 文件."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from .task_engine import AgentTask, TaskStatus

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "tasks"


class TaskStore:
    """JSON 文件持久化: storage/tasks/{task_id}.json"""

    def __init__(self, base_dir: Optional[Path] = None):
        self._dir = base_dir or STORAGE_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def save_task(self, task: AgentTask):
        self._write_task_file(task.task_id, task.to_dict())

    def delete_task(self, task_id: str):
        path = self._task_path(task_id)
        if path.exists():
            path.unlink()

    def load_all(self) -> Dict[str, AgentTask]:
        tasks: Dict[str, AgentTask] = {}
        for path in self._dir.glob("*.json"):
            try:
                data = self._read_task_file(path)
                tasks[data["task_id"]] = self._deserialize(data)
            except Exception as e:
                logger.warning(f"加载任务失败 {path.name}: {e}")
        if tasks:
            logger.info(f"📂 任务加载: {len(tasks)} 个任务")
        return tasks

    def _task_path(self, task_id: str) -> Path:
        return self._dir / f"{task_id}.json"

    def _write_task_file(self, task_id: str, data: dict) -> None:
        self._task_path(task_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _read_task_file(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _deserialize(data: dict) -> AgentTask:
        return AgentTask(
            task_id=data.get("task_id", ""),
            agent_id=data.get("agent_id", ""),
            team_id=data.get("team_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=data.get("priority", 2),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
            result=data.get("result"),
            error=data.get("error", ""),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
        )
