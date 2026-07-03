# -*- coding: utf-8 -*-
"""试炼存储 — JSON 文件持久化，幂等写入.

设计原则:
  - 轻量级: 单 JSON 文件，无需外部数据库
  - 线程安全: asyncio.Lock 保护并发写入
  - 原子写: .tmp 原子写 + .bak 备份
  - 自愈: 文件损坏自动从备份恢复

严格复用 src/backend/agents/audit_store.py 模式.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "trials"
STORAGE_FILE = STORAGE_DIR / "trials.json"
BACKUP_FILE = STORAGE_DIR / "trials.json.bak"


class TrialStore:
    """试炼数据 JSON 文件持久化存储.

    用法:
        store = TrialStore()
        await store.initialize()

        # 试炼 CRUD
        await store.save_trial(trial_id, trial_data)
        trial = await store.get_trial(trial_id)
        all_trials = await store.list_trials()

        # 分支操作
        await store.save_branch(branch_id, branch_data)
        branch = await store.get_branch(branch_id)

        # 事件操作
        await store.append_event(trial_id, event_data)
        events = await store.get_events(trial_id)
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._trials: Dict[str, Dict[str, Any]] = {}
        self._branches: Dict[str, Dict[str, Any]] = {}
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False

    # ── 生命周期 ──────────────────────────────────────────

    async def initialize(self) -> bool:
        """初始化存储 — 确保目录存在 & 加载已有数据."""
        try:
            STORAGE_DIR.mkdir(parents=True, exist_ok=True)

            if STORAGE_FILE.exists():
                await self._load()
            else:
                await self._save()

            self._initialized = True
            logger.info(f"📁 TrialStore 初始化完成: {len(self._trials)} 个试炼, {len(self._branches)} 个分支")
            return True
        except Exception as e:
            logger.error(f"❌ TrialStore 初始化失败: {e}")
            if BACKUP_FILE.exists():
                try:
                    await self._load_from_backup()
                    self._initialized = True
                    logger.warning("⚠️ 从备份恢复 TrialStore")
                    return True
                except Exception as be:
                    logger.error(f"❌ 备份恢复也失败: {be}")
            return False

    async def _load(self) -> None:
        """从主文件加载数据."""
        content = STORAGE_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        self._trials = data.get("trials", {})
        self._branches = data.get("branches", {})
        self._events = data.get("events", {})
        logger.debug(f"📖 加载 {len(self._trials)} 个试炼, {len(self._branches)} 个分支")

    async def _load_from_backup(self) -> None:
        """从备份文件恢复."""
        content = BACKUP_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        self._trials = data.get("trials", {})
        self._branches = data.get("branches", {})
        self._events = data.get("events", {})

    async def _save(self) -> None:
        """保存数据到文件 (先写回备份)."""
        data = {
            "trials": self._trials,
            "branches": self._branches,
            "events": self._events,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        json_text = json.dumps(data, ensure_ascii=False, indent=2)

        # 先备份旧文件
        if STORAGE_FILE.exists():
            try:
                STORAGE_FILE.rename(BACKUP_FILE)
            except OSError:
                pass

        # 原子写入
        tmp_file = STORAGE_FILE.with_suffix(".tmp")
        tmp_file.write_text(json_text, encoding="utf-8")
        tmp_file.rename(STORAGE_FILE)

    # ── Trial CRUD ────────────────────────────────────────

    async def save_trial(self, trial_id: str, trial_data: Dict[str, Any]) -> None:
        """保存试炼数据."""
        async with self._lock:
            self._trials[trial_id] = trial_data
            await self._save()
            logger.debug(f"💾 保存试炼: {trial_id}")

    async def get_trial(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """获取单个试炼."""
        async with self._lock:
            return self._trials.get(trial_id)

    async def list_trials(self) -> Dict[str, Dict[str, Any]]:
        """获取所有试炼."""
        async with self._lock:
            return dict(self._trials)

    async def delete_trial(self, trial_id: str) -> bool:
        """删除试炼 (同时清理关联分支和事件)."""
        async with self._lock:
            if trial_id not in self._trials:
                return False
            # 清理关联分支
            trial = self._trials[trial_id]
            for bid in trial.get("branches", []):
                self._branches.pop(bid, None)
            # 清理事件
            self._events.pop(trial_id, None)
            # 删除试炼
            del self._trials[trial_id]
            await self._save()
            logger.info(f"🗑️ 删除试炼: {trial_id}")
            return True

    # ── Branch CRUD ────────────────────────────────────────

    async def save_branch(self, branch_id: str, branch_data: Dict[str, Any]) -> None:
        """保存分支数据."""
        async with self._lock:
            self._branches[branch_id] = branch_data
            await self._save()
            logger.debug(f"💾 保存分支: {branch_id}")

    async def get_branch(self, branch_id: str) -> Optional[Dict[str, Any]]:
        """获取单个分支."""
        async with self._lock:
            return self._branches.get(branch_id)

    async def list_branches_for_trial(self, trial_id: str) -> Dict[str, Dict[str, Any]]:
        """获取某试炼下的所有分支."""
        async with self._lock:
            trial = self._trials.get(trial_id, {})
            branch_ids = trial.get("branches", [])
            return {bid: self._branches[bid] for bid in branch_ids if bid in self._branches}

    # ── Event CRUD ─────────────────────────────────────────

    async def append_event(self, trial_id: str, event_data: Dict[str, Any]) -> None:
        """追加试炼事件."""
        async with self._lock:
            if trial_id not in self._events:
                self._events[trial_id] = []
            self._events[trial_id].append(event_data)
            await self._save()
            logger.debug(f"📝 追加事件: trial={trial_id}")

    async def get_events(self, trial_id: str) -> List[Dict[str, Any]]:
        """获取试炼所有事件."""
        async with self._lock:
            return list(self._events.get(trial_id, []))

    # ── 序列化/反序列化辅助 ──────────────────────────────

    def _serialize_trial(self, trial) -> Dict[str, Any]:
        """将 Trial 对象转为可 JSON 序列化的 dict."""
        return {
            "id": trial.id,
            "name": trial.name,
            "team_id": trial.team_id,
            "task_goal": trial.task_goal,
            "scenario": trial.scenario,
            # v4 A-2.6: 场景化 + 代际
            "scenario_id": getattr(trial, "scenario_id", ""),
            "generation": getattr(trial, "generation", 0),
            "parent_trial_id": getattr(trial, "parent_trial_id", ""),
            "mode": trial.mode.value if hasattr(trial.mode, "value") else str(trial.mode),
            "max_steps": trial.max_steps,
            "acceleration": trial.acceleration,
            "parallel_branches": trial.parallel_branches,
            "status": trial.status.value if hasattr(trial.status, "value") else str(trial.status),
            "total_sessions": trial.total_sessions,
            "total_steps": trial.total_steps,
            "best_score": trial.best_score,
            "branches": trial.branches or [],
            "evaluation": trial.evaluation,
            "extracted_sops": trial.extracted_sops or [],
            "feedback_actions": trial.feedback_actions or [],
            "created_at": trial.created_at,
            "updated_at": trial.updated_at,
        }

    def _serialize_branch(self, branch) -> Dict[str, Any]:
        """将 Branch 对象转为可 JSON 序列化的 dict."""
        return {
            "id": branch.id,
            "trial_id": branch.trial_id,
            "name": branch.name,
            "label": branch.label,
            "color": branch.color,
            "status": branch.status.value if hasattr(branch.status, "value") else str(branch.status),
            "parent_branch_id": branch.parent_branch_id,
            "fork_at_step": branch.fork_at_step,
            "initial_conditions": branch.initial_conditions,
            "sessions": branch.sessions or [],
            "current_session_id": branch.current_session_id,
            "current_step": branch.current_step,
            "final_score": branch.final_score,
            "reward_curve": branch.reward_curve or [],
            "injected_events": branch.injected_events or [],
        }

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def trial_count(self) -> int:
        return len(self._trials)

    @property
    def branch_count(self) -> int:
        return len(self._branches)


# ── 全局单例 ───────────────────────────────────────────────

_global_trial_store: Optional[TrialStore] = None


async def get_trial_store() -> TrialStore:
    """获取全局 TrialStore 单例."""
    global _global_trial_store
    if _global_trial_store is None:
        _global_trial_store = TrialStore()
        await _global_trial_store.initialize()
    return _global_trial_store


async def reset_trial_store() -> TrialStore:
    """重置全局单例 (测试用)."""
    global _global_trial_store
    _global_trial_store = TrialStore()
    await _global_trial_store.initialize()
    return _global_trial_store
