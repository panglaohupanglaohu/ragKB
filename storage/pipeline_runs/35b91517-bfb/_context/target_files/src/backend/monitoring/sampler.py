# -*- coding: utf-8 -*-
"""
自适应采样决策模块 — 基于 anomalyScore 动态调整采样率.

核心逻辑:
- anomalyScore >= 0.7: 全量采集 (P0 + P1 + P2)
- anomalyScore >= 0.3: 条件采样 (P0 + P1)
- anomalyScore < 0.3: 基础采样 (仅 P0)
- 降级模式 (degradation_mode): 全量采集所有字段
"""

from __future__ import annotations

import hashlib
import logging
import random
from typing import Optional

from .models import SamplingConfig, SamplingDecision, SpanPriority, TraceSpan

logger = logging.getLogger(__name__)


class AdaptiveSampler:
    """自适应采样器 — 基于 anomalyScore 动态调整采样率.

    支持 ConfigMap 热更新采样策略。
    使用一致性哈希确保同一 traceId 的采样标记一致。
    """

    def __init__(self, config: Optional[SamplingConfig] = None):
        self._config = config or SamplingConfig()
        self._total_decisions = 0
        self._sampled_count = 0

    @property
    def config(self) -> SamplingConfig:
        return self._config

    def update_config(self, new_config: SamplingConfig):
        """热更新采样策略."""
        old_version = self._config.schema_version
        self._config = new_config
        logger.info(
            f"🔄 采样策略更新: schema {old_version} → {new_config.schema_version}, "
            f"base_rate={new_config.base_sample_rate}, "
            f"degradation={new_config.degradation_mode}"
        )

    def update_from_dict(self, config_dict: dict):
        """从字典热更新采样策略."""
        new_config = SamplingConfig.from_dict(config_dict)
        self.update_config(new_config)

    def decide(self, span: TraceSpan) -> SamplingDecision:
        """对单个 span 做出采样决策.

        决策流程:
        1. 降级模式 → 全量采集
        2. anomalyScore >= 0.7 → 全量采集
        3. anomalyScore >= 0.3 → 条件采样 (P0 + P1)
        4. 一致性哈希决定是否采样
        5. 默认 → 基础采样 (仅 P0)
        """
        self._total_decisions += 1

        # 降级模式: 全量采集
        if self._config.degradation_mode:
            self._sampled_count += 1
            return SamplingDecision(
                should_sample=True,
                priority=SpanPriority.P0,
                sample_rate=1.0,
                reason="degradation_mode_forced",
            )

        # 高异常评分: 全量采集
        if span.anomaly_score >= self._config.anomaly_threshold_high:
            self._sampled_count += 1
            return SamplingDecision(
                should_sample=True,
                priority=SpanPriority.P0,
                sample_rate=self._config.high_anomaly_rate,
                reason=f"high_anomaly_score_{span.anomaly_score:.2f}",
            )

        # 中异常评分: 条件采样
        if span.anomaly_score >= self._config.anomaly_threshold_medium:
            # 一致性哈希确保同一 traceId 采样一致
            if self._consistent_hash(span.trace_id, self._config.medium_anomaly_rate):
                self._sampled_count += 1
                return SamplingDecision(
                    should_sample=True,
                    priority=SpanPriority.P1,
                    sample_rate=self._config.medium_anomaly_rate,
                    reason=f"medium_anomaly_score_{span.anomaly_score:.2f}",
                )
            return SamplingDecision(
                should_sample=False,
                priority=SpanPriority.P1,
                sample_rate=self._config.medium_anomaly_rate,
                reason="medium_anomaly_not_sampled",
            )

        # 低异常评分: 基础采样
        if self._consistent_hash(span.trace_id, self._config.base_sample_rate):
            self._sampled_count += 1
            return SamplingDecision(
                should_sample=True,
                priority=SpanPriority.P0,
                sample_rate=self._config.base_sample_rate,
                reason="base_sampling",
            )

        return SamplingDecision(
            should_sample=False,
            priority=SpanPriority.P2,
            sample_rate=self._config.base_sample_rate,
            reason="not_sampled",
        )

    def get_stats(self) -> dict:
        """获取采样统计."""
        return {
            "total_decisions": self._total_decisions,
            "sampled_count": self._sampled_count,
            "sample_rate_actual": round(
                self._sampled_count / max(self._total_decisions, 1), 4
            ),
            "config": self._config.to_dict(),
        }

    @staticmethod
    def _consistent_hash(trace_id: str, rate: float) -> bool:
        """一致性哈希 — 确保同一 traceId 的采样标记一致.

        使用 trace_id 的 hash 值映射到 [0, 1) 区间，
        如果小于 rate 则采样。
        """
        if rate >= 1.0:
            return True
        if rate <= 0.0:
            return False
        hash_val = int(hashlib.md5(trace_id.encode()).hexdigest()[:8], 16)
        normalized = hash_val / 0xFFFFFFFF
        return normalized < rate
