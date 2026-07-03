# -*- coding: utf-8 -*-
"""审核服务 — ReviewService 幂等记录审核动作并回写版本增量.

核心职责:
  1. submit()        — 提交门禁评估结果到审核队列
  2. perform_action() — 执行审核操作 (approve/reject/request_changes)
  3. Idempotency:     — 相同 idempotency_key 不重复处理
  4. Version increment: — 每次操作递增 entry.version 和 entity_version

生命周期:
  PENDING → APPROVED / REJECTED / CHANGES_REQUESTED → CLOSED

幂等保证:
  - 每次 perform_action 传入 idempotency_key
  - 相同 key 的重复调用返回已有结果
  - 版本号递增确保无丢失更新
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .audit_store import AuditStore, get_audit_store
from .gate_evaluator import evaluate, evaluate_from_dict
from .review_models import (
    GateEvaluationContext,
    GateEvaluationResult,
    GateLevel,
    ReviewAction,
    ReviewEntry,
    ReviewQueue,
    ReviewStatus,
)

logger = logging.getLogger(__name__)


class _MemoryAuditStore:
    """In-memory audit store for isolated ReviewService instances."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._idempotency_keys: Dict[str, str] = {}

    async def initialize(self) -> bool:
        return True

    async def upsert(self, entry: ReviewEntry) -> ReviewEntry:
        async with self._lock:
            if entry.idempotency_key:
                existing_id = self._idempotency_keys.get(entry.idempotency_key)
                if existing_id and existing_id != entry.id:
                    return ReviewEntry(**self._entries[existing_id])
            self._entries[entry.id] = entry.model_dump()
            if entry.idempotency_key:
                self._idempotency_keys[entry.idempotency_key] = entry.id
            return entry

    async def get(self, entry_id: str) -> Optional[ReviewEntry]:
        async with self._lock:
            data = self._entries.get(entry_id)
            return ReviewEntry(**data) if data else None

    async def list_entries(
        self,
        status: Optional[ReviewStatus] = None,
        entity_id: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ReviewEntry]:
        async with self._lock:
            entries = []
            for data in self._entries.values():
                if status and data.get("status") != status.value:
                    continue
                if entity_id and data.get("entity_id") != entity_id:
                    continue
                if domain and data.get("domain") != domain:
                    continue
                entries.append(ReviewEntry(**data))
            entries.sort(key=lambda e: e.created_at, reverse=True)
            return entries[offset:offset + limit]

    async def get_queue(self) -> ReviewQueue:
        entries = await self.list_entries(limit=100000)
        queue = ReviewQueue(entries=entries)
        queue.refresh_stats()
        return queue

    async def count_by_status(self) -> Dict[str, int]:
        async with self._lock:
            counts: Dict[str, int] = {}
            for data in self._entries.values():
                status = data.get("status", ReviewStatus.PENDING.value)
                counts[status] = counts.get(status, 0) + 1
            return counts


class ReviewService:
    """审核服务 — 管理审核队列的完整生命周期.

    用法:
        svc = ReviewService(store)
        result = evaluate(context)
        entry = await svc.submit("EVO-1", result, context_dict)

        # 操作员审批
        updated = await svc.perform_action(
            entry_id=entry.id,
            action=ReviewAction.APPROVE,
            reviewer="officer_wang",
            comment="合规检查通过",
            idempotency_key="op-abc-001",
        )
    """

    def __init__(self, store: Optional[AuditStore] = None):
        self._store = store
        self._lock = asyncio.Lock()

    async def _get_store(self):
        if self._store is None:
            self._store = _MemoryAuditStore()
            await self._store.initialize()
        return self._store

    # ── 提交 ──────────────────────────────────────────────

    async def submit(
        self,
        entity_id: str,
        result: GateEvaluationResult,
        context: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        entity_type: str = "evolution_item",
        entity_name: str = "",
        domain: str = "general",
        severity: str = "medium",
        reviewer: str = "system",
        submitter: str = "",
        **kwargs,
    ) -> ReviewEntry:
        """提交门禁评估结果到审核队列.

        如果 idempotency_key 已存在，返回已有条目 (幂等)。
        如果 reviewer == submitter，抛出 ValueError (禁止自审)。
        """
        store = await self._get_store()

        # 自审保护
        if submitter and reviewer and submitter == reviewer:
            raise ValueError(f"禁止自审: reviewer={reviewer} 不能审核自己提交的内容")

        async with self._lock:
            # 幂等检查
            if idempotency_key:
                existing = await self._find_by_idempotency_key(idempotency_key)
                if existing:
                    logger.info(f"🔄 幂等提交: key={idempotency_key} → {existing.id}")
                    return existing

            # 创建新条目
            entry = ReviewEntry(
                entity_id=entity_id,
                entity_type=entity_type,
                entity_name=entity_name,
                evaluation_score=result.score,
                evaluation_level=result.level,
                evaluation_passed=result.passed,
                status=ReviewStatus.PENDING,
                idempotency_key=idempotency_key,
                version=1,
                entity_version=1,
                reviewer=reviewer,
                comment=f"自动评估: {', '.join(result.reasons[:3])}",
                domain=domain,
                severity=severity,
                source_evaluation_context=context,
                **kwargs,
            )

            saved = await store.upsert(entry)
            logger.info(f"📝 创建审核条目: {saved.id} score={saved.evaluation_score} level={saved.evaluation_level}")
            return saved

    # ── 审核操作 ──────────────────────────────────────────

    async def perform_action(
        self,
        entry_id: str,
        action: ReviewAction,
        reviewer: str = "system",
        comment: str = "",
        idempotency_key: Optional[str] = None,
    ) -> ReviewEntry:
        """执行审核动作 — 幂等记录并回写版本增量.

        Args:
            entry_id: 审核条目ID
            action: 审核操作 (approve/reject/request_changes/close)
            reviewer: 操作人标识
            comment: 审核评论
            idempotency_key: 幂等键，防止重复处理同一操作

        Returns:
            更新后的 ReviewEntry

        Raises:
            ValueError: 条目不存在或状态不允许操作
        """
        store = await self._get_store()

        async with self._lock:
            # 幂等检查
            if idempotency_key:
                existing = await self._find_by_idempotency_key(idempotency_key)
                if existing and existing.id == entry_id:
                    logger.info(f"🔄 幂等操作: key={idempotency_key} → {entry_id}")
                    return existing

            # 获取当前条目
            current = await store.get(entry_id)
            if current is None:
                raise ValueError(f"审核条目未找到: {entry_id}")

            # 自审保护: 审核人不能审核自己提交的内容
            if reviewer and current.reviewer and reviewer == current.reviewer:
                raise ValueError(f"禁止自审: reviewer={reviewer} 不能审核自己提交的内容 (original reviewer={current.reviewer})")

            # 状态机验证
            new_status = self._transition_status(current.status, action)
            if new_status == current.status and action != ReviewAction.COMMENT:
                raise ValueError(
                    f"无效状态转换: {current.status} → {action.value}"
                )

            # 计算新版本号
            new_version = current.version + 1
            new_entity_version = current.entity_version + 1

            # 更新条目
            updated = ReviewEntry(
                id=current.id,
                entity_id=current.entity_id,
                entity_type=current.entity_type,
                entity_name=current.entity_name,
                evaluation_score=current.evaluation_score,
                evaluation_level=current.evaluation_level,
                evaluation_passed=current.evaluation_passed,
                status=new_status,
                current_action=action,
                idempotency_key=idempotency_key,
                version=new_version,
                entity_version=new_entity_version,
                reviewer=current.reviewer,
                comment=comment,
                domain=current.domain,
                severity=current.severity,
                source_evaluation_context=current.source_evaluation_context,
                tags=current.tags,
                created_at=current.created_at,
                updated_at=datetime.now(timezone.utc).isoformat(),
                resolved_at=(
                    datetime.now(timezone.utc).isoformat()
                    if new_status in (ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.CLOSED)
                    else current.resolved_at
                ),
            )

            saved = await store.upsert(updated)
            logger.info(
                f"⚡ 审核操作: {entry_id} {current.status}→{new_status} "
                f"v{current.version}→v{new_version} by {reviewer}"
            )
            return saved

    # ── 查询 ──────────────────────────────────────────────

    async def get_entry(self, entry_id: str) -> Optional[ReviewEntry]:
        store = await self._get_store()
        return await store.get(entry_id)

    async def get_queue(self) -> ReviewQueue:
        store = await self._get_store()
        return await store.get_queue()

    async def list_entries(
        self,
        status: Optional[ReviewStatus] = None,
        entity_id: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ReviewEntry]:
        store = await self._get_store()
        return await store.list_entries(
            status=status, entity_id=entity_id, domain=domain,
            limit=limit, offset=offset,
        )

    async def get_pending_count(self) -> int:
        store = await self._get_store()
        counts = await store.count_by_status()
        return counts.get("pending", 0)

    # ── 辅助 ──────────────────────────────────────────────

    async def _find_by_idempotency_key(self, key: str) -> Optional[ReviewEntry]:
        """通过幂等键查找已有条目."""
        store = await self._get_store()
        # 遍历查找 (store 内部维护 idempotency_keys map)
        all_entries = await store.list_entries()
        for e in all_entries:
            if e.idempotency_key == key:
                return e
        return None

    @staticmethod
    def _transition_status(current: ReviewStatus, action: ReviewAction) -> ReviewStatus:
        """状态机转换表."""
        transitions = {
            (ReviewStatus.PENDING, ReviewAction.APPROVE): ReviewStatus.APPROVED,
            (ReviewStatus.PENDING, ReviewAction.REJECT): ReviewStatus.REJECTED,
            (ReviewStatus.PENDING, ReviewAction.REQUEST_CHANGES): ReviewStatus.CHANGES_REQUESTED,
            (ReviewStatus.PENDING, ReviewAction.CLOSE): ReviewStatus.CLOSED,
            (ReviewStatus.CHANGES_REQUESTED, ReviewAction.APPROVE): ReviewStatus.APPROVED,
            (ReviewStatus.CHANGES_REQUESTED, ReviewAction.REJECT): ReviewStatus.REJECTED,
            (ReviewStatus.CHANGES_REQUESTED, ReviewAction.CLOSE): ReviewStatus.CLOSED,
            (ReviewStatus.APPROVED, ReviewAction.CLOSE): ReviewStatus.CLOSED,
            (ReviewStatus.REJECTED, ReviewAction.CLOSE): ReviewStatus.CLOSED,
            (ReviewStatus.CHANGES_REQUESTED, ReviewAction.COMMENT): ReviewStatus.CHANGES_REQUESTED,
            (ReviewStatus.PENDING, ReviewAction.COMMENT): ReviewStatus.PENDING,
            (ReviewStatus.APPROVED, ReviewAction.COMMENT): ReviewStatus.APPROVED,
            (ReviewStatus.REJECTED, ReviewAction.COMMENT): ReviewStatus.REJECTED,
        }
        return transitions.get((current, action), current)


# ── 全局单例 ───────────────────────────────────────────────

_global_review_service: Optional[ReviewService] = None


async def get_review_service() -> ReviewService:
    """获取全局 ReviewService 单例."""
    global _global_review_service
    if _global_review_service is None:
        store = await get_audit_store()
        _global_review_service = ReviewService(store=store)
    return _global_review_service


async def reset_review_service() -> ReviewService:
    """重置全局单例 (测试用)."""
    global _global_review_service
    from .audit_store import reset_audit_store
    store = await reset_audit_store()
    _global_review_service = ReviewService(store=store)
    return _global_review_service
