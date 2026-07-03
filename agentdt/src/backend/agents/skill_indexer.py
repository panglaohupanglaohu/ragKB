# -*- coding: utf-8 -*-
"""SkillIndexer — 异步 Indexing Worker，消费领域事件构建向量索引。

工作原理:
1. 订阅 EventBus 的 skill.* 事件
2. 接收 SkillSnapshot（完整上下文，无需回查数据库）
3. 提取文本特征 → 构建轻量向量索引 (TF-IDF + Cosine Similarity)
4. 支持批量重索引 (rebuild) 和增量更新

向量索引策略 (MVP):
- 使用 sklearn TfidfVectorizer 提取特征
- 余弦相似度进行检索排序
- 内存索引，启动时从 SkillStore 重建
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .domain_events import DomainEvent, EventType, SkillSnapshot
from .event_bus import EventBus, get_event_bus

logger = logging.getLogger(__name__)


class SkillIndexer:
    """技能向量索引器 — 消费事件构建 / 更新向量索引.

    用法:
        indexer = SkillIndexer(bus)

        # 从 SkillStore 初始化全量索引
        await indexer.rebuild(skill_records)

        # 启动后台监听
        await indexer.start()
        # ... 事件自动处理 ...
        await indexer.stop()

        # 检索
        results = indexer.search("code review automation", top_k=5)
    """

    def __init__(self, bus: Optional[EventBus] = None):
        self._bus = bus or get_event_bus()
        self._running = False
        self._lock = asyncio.Lock()

        # 索引存储
        self._documents: Dict[str, SkillSnapshot] = {}  # skill_id → snapshot
        self._index_ready = False

        # TF-IDF 组件 (lazy init)
        self._vectorizer = None
        self._tfidf_matrix = None
        self._skill_ids: List[str] = []  # 与 tfidf_matrix 行对应

        # 统计
        self._stats = {
            "indexed_count": 0,
            "updated_count": 0,
            "deleted_count": 0,
            "last_indexed_at": "",
        }

    # ── 生命周期 ────────────────────────────────────────────────────

    async def start(self) -> None:
        """启动 Indexing Worker，订阅事件."""
        if self._running:
            return
        self._running = True
        self._bus.subscribe(EventType.SKILL_CREATED, self._on_skill_created)
        self._bus.subscribe(EventType.SKILL_UPDATED, self._on_skill_updated)
        self._bus.subscribe(EventType.SKILL_DELETED, self._on_skill_deleted)
        logger.info("🔍 SkillIndexer 启动，已订阅 skill.* 事件")

    async def stop(self) -> None:
        """停止 Indexing Worker，取消订阅."""
        self._running = False
        self._bus.unsubscribe(EventType.SKILL_CREATED, self._on_skill_created)
        self._bus.unsubscribe(EventType.SKILL_UPDATED, self._on_skill_updated)
        self._bus.unsubscribe(EventType.SKILL_DELETED, self._on_skill_deleted)
        logger.info("🔍 SkillIndexer 已停止")

    # ── 事件处理器 ──────────────────────────────────────────────────

    async def _on_skill_created(self, event: DomainEvent) -> None:
        """处理 skill.created 事件."""
        async with self._lock:
            snapshot = self._extract_snapshot(event)
            if snapshot:
                self._documents[snapshot.skill_id] = snapshot
                self._stats["indexed_count"] += 1
                self._stats["last_indexed_at"] = datetime.now(timezone.utc).isoformat()
                self._invalidate_matrix()
                logger.debug(f"📄 索引新增: {snapshot.skill_id} ({snapshot.name})")

    async def _on_skill_updated(self, event: DomainEvent) -> None:
        """处理 skill.updated 事件."""
        async with self._lock:
            snapshot = self._extract_snapshot(event)
            if snapshot:
                self._documents[snapshot.skill_id] = snapshot
                self._stats["updated_count"] += 1
                self._stats["last_indexed_at"] = datetime.now(timezone.utc).isoformat()
                self._invalidate_matrix()
                logger.debug(f"📄 索引更新: {snapshot.skill_id} ({snapshot.name})")

    async def _on_skill_deleted(self, event: DomainEvent) -> None:
        """处理 skill.deleted 事件."""
        async with self._lock:
            snapshot = self._extract_snapshot(event)
            if snapshot:
                self._documents.pop(snapshot.skill_id, None)
                self._stats["deleted_count"] += 1
                self._stats["last_indexed_at"] = datetime.now(timezone.utc).isoformat()
                self._invalidate_matrix()
                logger.debug(f"🗑️ 索引删除: {snapshot.skill_id}")

    def _extract_snapshot(self, event: DomainEvent) -> Optional[SkillSnapshot]:
        """从事件中提取 SkillSnapshot."""
        payload = event.payload
        if isinstance(payload, SkillSnapshot):
            return payload
        if isinstance(payload, dict):
            return SkillSnapshot(
                skill_id=payload.get("skill_id", ""),
                name=payload.get("name", ""),
                description=payload.get("description", ""),
                category=payload.get("category", "general"),
                required=payload.get("required", False),
                enabled=payload.get("enabled", True),
                icon=payload.get("icon", "⚡"),
                slug=payload.get("slug", ""),
                source=payload.get("source", "builtin"),
                required_tools=payload.get("required_tools", []),
                instructions=payload.get("instructions", ""),
                config_schema=payload.get("config_schema", {}),
                config=payload.get("config", {}),
                is_default=payload.get("is_default", False),
                metadata=payload.get("metadata", {}),
            )
        return None

    # ── 全量重建 ────────────────────────────────────────────────────

    async def rebuild(self, records: List[Any]) -> int:
        """从 SkillStore 记录全量重建索引.

        Args:
            records: SkillRecord 列表 (来自 SkillStore.list_all())

        Returns:
            索引的技能数量
        """
        async with self._lock:
            self._documents.clear()
            for rec in records:
                snapshot = rec.snapshot if hasattr(rec, "snapshot") else rec
                if isinstance(snapshot, SkillSnapshot):
                    self._documents[snapshot.skill_id] = snapshot
                elif isinstance(snapshot, dict):
                    sid = snapshot.get("skill_id", rec.skill_id if hasattr(rec, "skill_id") else "")
                    self._documents[sid] = SkillSnapshot(
                        skill_id=sid,
                        name=snapshot.get("name", ""),
                        description=snapshot.get("description", ""),
                        category=snapshot.get("category", "general"),
                        required=snapshot.get("required", False),
                        enabled=snapshot.get("enabled", True),
                        icon=snapshot.get("icon", "⚡"),
                        slug=snapshot.get("slug", ""),
                        source=snapshot.get("source", "builtin"),
                        required_tools=snapshot.get("required_tools", []),
                        instructions=snapshot.get("instructions", ""),
                        config_schema=snapshot.get("config_schema", {}),
                        config=snapshot.get("config", {}),
                        is_default=snapshot.get("is_default", False),
                        metadata=snapshot.get("metadata", {}),
                    )
            self._stats["indexed_count"] = len(self._documents)
            self._stats["last_indexed_at"] = datetime.now(timezone.utc).isoformat()
            self._invalidate_matrix()
            self._index_ready = True
            logger.info(f"📚 SkillIndexer 全量重建完成: {len(self._documents)} 个技能")
            return len(self._documents)

    # ── TF-IDF 矩阵 ─────────────────────────────────────────────────

    def _invalidate_matrix(self) -> None:
        """标记矩阵需重建."""
        self._tfidf_matrix = None
        self._skill_ids = []
        self._index_ready = bool(self._documents)

    def _ensure_matrix(self) -> None:
        """确保 TF-IDF 矩阵已构建."""
        if self._tfidf_matrix is not None and len(self._skill_ids) == len(self._documents):
            return

        if not self._documents:
            self._tfidf_matrix = None
            self._skill_ids = []
            return

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError:
            logger.warning("⚠️ sklearn 不可用，降级为关键词匹配")
            self._tfidf_matrix = None
            self._skill_ids = list(self._documents.keys())
            return

        self._vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self._skill_ids = list(self._documents.keys())
        corpus = [
            self._doc_to_text(self._documents[sid])
            for sid in self._skill_ids
        ]
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)
        logger.debug(f"📐 TF-IDF 矩阵: {self._tfidf_matrix.shape}")

    def _doc_to_text(self, snapshot: SkillSnapshot) -> str:
        """将 SkillSnapshot 转为可索引文本."""
        parts = [
            snapshot.name,
            snapshot.name,  # 名称权重 ×2
            snapshot.description,
            snapshot.category,
            snapshot.slug,
            " ".join(snapshot.required_tools),
            snapshot.instructions[:500] if snapshot.instructions else "",
            snapshot.source,
        ]
        return " ".join(p for p in parts if p)

    # ── 检索 ────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 10,
        category_filter: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[Tuple[SkillSnapshot, float]]:
        """检索技能索引.

        Args:
            query: 查询文本
            top_k: 返回前 k 个结果
            category_filter: 可选类别筛选
            min_score: 最低相似度阈值 (0-1)

        Returns:
            [(SkillSnapshot, score), ...] 按相似度降序
        """
        if not self._documents:
            return []

        # 如果 sklearn 不可用，降级为关键词匹配
        if self._vectorizer is None:
            return self._keyword_search(query, top_k, category_filter, min_score)

        self._ensure_matrix()

        if self._tfidf_matrix is None or self._tfidf_matrix.shape[0] == 0:
            return []

        try:
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            return self._keyword_search(query, top_k, category_filter, min_score)

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        results = []
        for idx, score in enumerate(scores):
            if score <= min_score:
                continue
            if idx >= len(self._skill_ids):
                continue
            sid = self._skill_ids[idx]
            snapshot = self._documents.get(sid)
            if snapshot is None:
                continue
            if category_filter and snapshot.category != category_filter:
                continue
            results.append((snapshot, float(score)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _keyword_search(
        self,
        query: str,
        top_k: int,
        category_filter: Optional[str],
        min_score: float,
    ) -> List[Tuple[SkillSnapshot, float]]:
        """降级关键词匹配 (无 sklearn 时使用)."""
        query_terms = query.lower().split()
        results = []

        for snapshot in self._documents.values():
            if category_filter and snapshot.category != category_filter:
                continue
            text = self._doc_to_text(snapshot).lower()
            score = sum(1.0 for t in query_terms if t in text) / max(len(query_terms), 1)
            if score > min_score:
                results.append((snapshot, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    # ── 统计 ────────────────────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "documents_in_index": len(self._documents),
            "index_ready": self._index_ready,
            "running": self._running,
        }
