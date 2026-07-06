"""
ModelRouter — 三档模型路由（economy/standard/frontier）

决策日志写 cost_aggregator，接 tool_loop 与 chat_harness。
- economy: 低成本快速模型（日常对话、简单工具调用）
- standard: 标准模型（常规任务执行）
- frontier: 高能力模型（复杂推理、代码生成）

路由策略:
1. 预算耗尽 → 降档
2. 连续失败 → 升档
3. 档位粘滞（hysteresis）：避免频繁切换
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    FRONTIER = "frontier"


# 档位优先级（高→低）
_TIER_ORDER = [ModelTier.FRONTIER, ModelTier.STANDARD, ModelTier.ECONOMY]


@dataclass
class TierConfig:
    """单个档位的模型配置."""
    tier: ModelTier
    model: str = ""
    provider: str = ""
    max_tokens: int = 8192
    temperature: float = 0.3


@dataclass
class RouteDecision:
    """路由决策结果."""
    tier: ModelTier
    model: str
    reason: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class RouterState:
    """路由器运行时状态."""
    current_tier: ModelTier = ModelTier.STANDARD
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_budget: int = 0
    used_budget: int = 0
    # 档位粘滞：切换后至少 N 次调用不再次切换
    sticky_remaining: int = 0
    sticky_count: int = 3
    # 降档阈值
    budget_threshold_down: float = 0.85   # 预算用 85% → 降档
    # 升档阈值
    failure_threshold_up: int = 2         # 连续 2 次失败 → 升档


class ModelRouter:
    """三档模型路由器."""

    def __init__(
        self,
        tiers: Optional[Dict[ModelTier, TierConfig]] = None,
        initial_tier: ModelTier = ModelTier.STANDARD,
        total_budget: int = 0,
    ) -> None:
        self.tiers = tiers or self._default_tiers()
        self.state = RouterState(
            current_tier=initial_tier,
            total_budget=total_budget,
        )

    @staticmethod
    def _default_tiers() -> Dict[ModelTier, TierConfig]:
        return {
            ModelTier.ECONOMY: TierConfig(
                tier=ModelTier.ECONOMY, model="deepseek-v4-flash",
                provider="deepseek", max_tokens=4096, temperature=0.5,
            ),
            ModelTier.STANDARD: TierConfig(
                tier=ModelTier.STANDARD, model="deepseek-v4-pro",
                provider="deepseek", max_tokens=8192, temperature=0.3,
            ),
            ModelTier.FRONTIER: TierConfig(
                tier=ModelTier.FRONTIER, model="glm-5.1",
                provider="codebuddy", max_tokens=16384, temperature=0.2,
            ),
        }

    def route(self, *, tokens_estimated: int = 0) -> RouteDecision:
        """根据当前状态决定使用哪个档位。返回 RouteDecision。"""
        # 1. 预算检查：剩余预算不足 → 降档
        if self.state.total_budget > 0:
            remaining = self.state.total_budget - self.state.used_budget
            if remaining < self.state.total_budget * (1 - self.state.budget_threshold_down):
                self._switch_tier(ModelTier.ECONOMY, "budget_low")
            # 预算恢复（用于测试重置）
            elif remaining > self.state.total_budget * 0.5 and self.state.current_tier == ModelTier.ECONOMY:
                self._switch_tier(ModelTier.STANDARD, "budget_recovered")

        # 2. 连续失败 → 升档
        if (self.state.consecutive_failures >= self.state.failure_threshold_up
                and self.state.sticky_remaining <= 0):
            self._upgrade_tier()

        # 3. 连续成功 → 降档（省钱）
        if (self.state.consecutive_successes >= 5
                and self.state.sticky_remaining <= 0
                and self.state.current_tier != ModelTier.ECONOMY):
            self._downgrade_tier()

        # 粘滞计数递减
        if self.state.sticky_remaining > 0:
            self.state.sticky_remaining -= 1

        tier_cfg = self.tiers.get(self.state.current_tier)
        if not tier_cfg:
            tier_cfg = self.tiers[ModelTier.STANDARD]
            self.state.current_tier = ModelTier.STANDARD

        self.state.used_budget += tokens_estimated

        return RouteDecision(
            tier=self.state.current_tier,
            model=tier_cfg.model,
            reason=f"tier={self.state.current_tier.value} failures={self.state.consecutive_failures} budget={self.state.used_budget}/{self.state.total_budget}",
        )

    def record_success(self, tokens_used: int = 0) -> None:
        """记录一次成功调用."""
        self.state.consecutive_successes += 1
        self.state.consecutive_failures = 0
        self.state.used_budget += tokens_used

    def record_failure(self) -> None:
        """记录一次失败调用."""
        self.state.consecutive_failures += 1
        self.state.consecutive_successes = 0

    def _switch_tier(self, target: ModelTier, reason: str) -> None:
        if self.state.current_tier == target:
            return
        logger.info("ModelRouter: %s → %s (%s)", self.state.current_tier.value, target.value, reason)
        self.state.current_tier = target
        self.state.sticky_remaining = self.state.sticky_count

    def _upgrade_tier(self) -> None:
        idx = _TIER_ORDER.index(self.state.current_tier)
        if idx > 0:
            self._switch_tier(_TIER_ORDER[idx - 1], "failures_escalation")

    def _downgrade_tier(self) -> None:
        idx = _TIER_ORDER.index(self.state.current_tier)
        if idx < len(_TIER_ORDER) - 1:
            self._switch_tier(_TIER_ORDER[idx + 1], "successes_cost_save")

    def get_state_dict(self) -> Dict[str, Any]:
        return {
            "current_tier": self.state.current_tier.value,
            "consecutive_failures": self.state.consecutive_failures,
            "consecutive_successes": self.state.consecutive_successes,
            "used_budget": self.state.used_budget,
            "total_budget": self.state.total_budget,
            "sticky_remaining": self.state.sticky_remaining,
        }


# 单例
_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
