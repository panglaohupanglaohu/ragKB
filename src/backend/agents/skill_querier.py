# -*- coding: utf-8 -*-
"""SkillQuerier — 技能检索器，带衰减策略与相关性排序。

核心特性:
1. **多策略检索**: TF-IDF 向量检索 + 关键词匹配双模式
2. **时间衰减**: 最近更新 / 使用的技能获得更高权重 (exponential decay)
3. **频率增强**: 高频使用技能获得 boost
4. **类别加权**: 根据查询意图对特定类别加权
5. **可组合过滤器**: category / enabled / source 等

衰减公式:
    final_score = similarity_score × decay_factor × frequency_boost

    其中:
    - decay_factor = e^(-λ × age_days)  (λ 可配置，默认 0.01)
    - frequency_boost = 1 + α × log(1 + use_count)  (α 可配置，默认 0.2)
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .domain_events import SkillSnapshot
from .skill_indexer import SkillIndexer

logger = logging.getLogger(__name__)


class SkillQuerier:
    """技能检索器 — 封装 Indexer + 衰减策略.

    用法:
        indexer = SkillIndexer()
        querier = SkillQuerier(indexer)

        # 记录技能使用 (用于频率增强)
        querier.record_use("skill_001")

        # 检索
        results = querier.query("code review", top_k=5)
        for snapshot, score in results:
            print(f"{snapshot.name}: {score:.3f}")
    """

    def __init__(
        self,
        indexer: SkillIndexer,
        decay_lambda: float = 0.01,  # 时间衰减系数 (每天)
        frequency_alpha: float = 0.2,  # 频率增强系数
        recency_weight: float = 0.3,  # 时效性权重 (0=纯相似度, 1=纯时间)
    ):
        self._indexer = indexer
        self._decay_lambda = decay_lambda
        self._frequency_alpha = frequency_alpha
        self._recency_weight = recency_weight

        # 使用统计: skill_id → {use_count, last_used_at, first_used_at}
        self._usage: Dict[str, Dict[str, Any]] = {}
        # 上次更新记录时间 (用于时间衰减计算)
        self._updated_at: Dict[str, str] = {}

    # ── 使用记录 ────────────────────────────────────────────────────

    def record_use(self, skill_id: str) -> None:
        """记录技能被使用，用于频率增强."""
        now = datetime.now(timezone.utc).isoformat()
        if skill_id not in self._usage:
            self._usage[skill_id] = {
                "use_count": 1,
                "last_used_at": now,
                "first_used_at": now,
            }
        else:
            self._usage[skill_id]["use_count"] += 1
            self._usage[skill_id]["last_used_at"] = now

    def record_update(self, skill_id: str, updated_at: str = "") -> None:
        """记录技能更新时间，用于时间衰减."""
        self._updated_at[skill_id] = updated_at or datetime.now(timezone.utc).isoformat()

    def get_usage_stats(self, skill_id: str) -> Dict[str, Any]:
        """获取技能使用统计."""
        return self._usage.get(skill_id, {
            "use_count": 0,
            "last_used_at": "",
            "first_used_at": "",
        })

    # ── 衰减计算 ────────────────────────────────────────────────────

    def _compute_decay_factor(self, snapshot: SkillSnapshot) -> float:
        """计算时间衰减因子.

        decay_factor = e^(-λ × age_days)

        最近更新的技能衰减更少，得分更高。
        """
        updated_at = self._updated_at.get(snapshot.skill_id, "")
        if not updated_at:
            return 1.0  # 无更新时间，不衰减

        try:
            updated_dt = datetime.fromisoformat(updated_at)
            now = datetime.now(timezone.utc)
            age_days = (now - updated_dt).total_seconds() / 86400.0
            age_days = max(0, age_days)
            return math.exp(-self._decay_lambda * age_days)
        except (ValueError, TypeError):
            return 1.0

    def _compute_frequency_boost(self, skill_id: str) -> float:
        """计算频率增强因子.

        frequency_boost = 1 + α × log(1 + use_count)
        """
        stats = self._usage.get(skill_id, {})
        use_count = stats.get("use_count", 0)
        if use_count <= 0:
            return 1.0
        return 1.0 + self._frequency_alpha * math.log(1 + use_count)

    def _compute_final_score(self, similarity: float, snapshot: SkillSnapshot) -> float:
        """综合计算最终得分:
        final_score = similarity × [decay × recency_weight + (1 - recency_weight)]
                       × frequency_boost
        """
        decay = self._compute_decay_factor(snapshot)
        time_factor = decay * self._recency_weight + (1.0 - self._recency_weight)
        boost = self._compute_frequency_boost(snapshot.skill_id)
        return similarity * time_factor * boost

    # ── 查询接口 ────────────────────────────────────────────────────

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        category_filter: Optional[str] = None,
        enabled_only: bool = True,
        source_filter: Optional[str] = None,
        min_similarity: float = 0.0,
        apply_decay: bool = True,
    ) -> List[Tuple[SkillSnapshot, float]]:
        """检索技能并应用衰减策略.

        Args:
            query_text: 查询文本
            top_k: 返回结果数
            category_filter: 可选类别筛选 (如 "general", "research")
            enabled_only: 仅返回启用的技能
            source_filter: 可选来源筛选 (如 "builtin", "custom")
            min_similarity: 最低原始相似度阈值
            apply_decay: 是否应用衰减策略

        Returns:
            [(SkillSnapshot, final_score), ...] 按最终得分降序
        """
        # Step 1: 从 Indexer 获取原始相似度结果
        raw_results = self._indexer.search(
            query=query_text,
            top_k=top_k * 3,  # 多取一些，留给衰减过滤空间
            category_filter=category_filter,
            min_score=min_similarity,
        )

        if not raw_results:
            return []

        # Step 2: 应用过滤器
        filtered = []
        for snapshot, sim_score in raw_results:
            if enabled_only and not snapshot.enabled:
                continue
            if source_filter and snapshot.source != source_filter:
                continue
            filtered.append((snapshot, sim_score))

        # Step 3: 应用衰减 + 增强
        if apply_decay:
            scored = []
            for snapshot, sim_score in filtered:
                final_score = self._compute_final_score(sim_score, snapshot)
                scored.append((snapshot, final_score))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]
        else:
            return filtered[:top_k]

    def query_by_intent(
        self,
        query_text: str,
        intent: str = "general",
        top_k: int = 10,
    ) -> List[Tuple[SkillSnapshot, float]]:
        """基于意图的检索 — 对不同意图应用类别优先策略.

        意图映射:
            "code" → 优先 GENERAL (代码实现/测试/调试等)
            "research" → 优先 RESEARCH
            "build" → 优先 GENERAL (构建自动化)
            "analyze" → 优先 GENERAL (数据分析)
            "monitor" → 优先 AUTOMATION
        """
        # 意图到优先类别的映射
        intent_category_map = {
            "code": "general",
            "research": "research",
            "build": "general",
            "analyze": "general",
            "monitor": "automation",
            "general": None,
        }

        category = intent_category_map.get(intent, None)

        # 先按意图类别搜索
        results = self.query(
            query_text=query_text,
            top_k=top_k,
            category_filter=category,
            enabled_only=True,
            apply_decay=True,
        )

        # 如果意图类别结果不足，补充通用结果
        if len(results) < top_k and category is not None:
            general_results = self.query(
                query_text=query_text,
                top_k=top_k - len(results),
                enabled_only=True,
                apply_decay=True,
            )
            # 去重合并
            seen_ids = {r[0].skill_id for r in results}
            for snapshot, score in general_results:
                if snapshot.skill_id not in seen_ids:
                    results.append((snapshot, score))
                    seen_ids.add(snapshot.skill_id)

            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:top_k]

        return results

    def get_recommendations(
        self,
        agent_role: str = "",
        team_context: Optional[List[str]] = None,
        top_k: int = 8,
    ) -> List[Tuple[SkillSnapshot, float]]:
        """基于 Agent 角色和团队上下文推荐技能.

        Args:
            agent_role: Agent 角色 (如 "developer", "architect")
            team_context: 团队已有技能ID列表，用于去重
        """
        # 角色到推荐查询的映射
        role_queries = {
            "developer": "code implementation debugging refactoring testing",
            "architect": "architecture design pattern interface definition",
            "researcher": "research analysis requirements cross session",
            "qa": "test design execution coverage regression",
            "qa_engineer": "test design execution coverage regression",
            "tester": "test design execution coverage regression",
            "devops": "build automation container deployment",
            "deployer": "build automation container deployment monitoring",
            "project_manager": "task decomposition progress tracking blocker resolution",
        }

        query = role_queries.get(agent_role, "general purpose skill")

        # 去重团队已有技能
        exclude_ids = set(team_context or [])
        results = self.query(query_text=query, top_k=top_k * 2, enabled_only=True)

        filtered = [
            (snap, score) for snap, score in results
            if snap.skill_id not in exclude_ids
        ]
        return filtered[:top_k]

    # ── 批量操作 ────────────────────────────────────────────────────

    def batch_record_use(self, skill_ids: List[str]) -> None:
        """批量记录技能使用."""
        for sid in skill_ids:
            self.record_use(sid)

    def reset_usage_stats(self) -> None:
        """重置所有使用统计."""
        self._usage.clear()
        self._updated_at.clear()

    def export_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """导出使用统计 (用于持久化)."""
        return {
            "usage": dict(self._usage),
            "updated_at": dict(self._updated_at),
            "decay_lambda": self._decay_lambda,
            "frequency_alpha": self._frequency_alpha,
            "recency_weight": self._recency_weight,
        }

    def import_usage_stats(self, data: Dict[str, Any]) -> None:
        """导入使用统计."""
        self._usage = data.get("usage", {})
        self._updated_at = data.get("updated_at", {})
        self._decay_lambda = data.get("decay_lambda", self._decay_lambda)
        self._frequency_alpha = data.get("frequency_alpha", self._frequency_alpha)
        self._recency_weight = data.get("recency_weight", self._recency_weight)
