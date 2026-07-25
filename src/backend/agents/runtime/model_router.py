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

重要：档位默认模型必须跟随全局 LLM 配置。若用户网关只有 glm-5.1
（如 SJTU/codebuddy），绝不能硬编码改写成 deepseek-v4-pro，否则上游
返回 team_model_access_denied / 403。
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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


def _resolve_primary_model() -> Tuple[str, str]:
    """读取全局默认模型名与 provider（env > settings.json > deepseek 兜底）。"""
    env_m = (os.getenv("AG_LLM_MODEL") or "").strip()
    env_p = (os.getenv("AG_LLM_PROVIDER") or "").strip()
    if env_m:
        return env_m, env_p or "openai"
    try:
        path = Path(__file__).resolve().parents[4] / "config" / "settings.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            llm = data.get("llm") or {}
            model = str(llm.get("model") or "").strip()
            provider = str(llm.get("provider") or "").strip()
            if model:
                return model, provider or "openai"
    except Exception as e:
        logger.debug("resolve primary model from settings failed: %s", e)
    return "deepseek-v4-pro", "deepseek"


def resolve_live_primary_model() -> Tuple[str, str]:
    """运行时权威源：ChatHarness 全局连接 > env/settings。

    用户在 UI「同步到全局默认」后，应以 harness 当前 model 为准，
    而不是仅磁盘 settings（可能滞后）或硬编码档位。
    """
    try:
        # 延迟导入，避免与 chat_harness 循环依赖
        from ..chat_harness import _harness  # type: ignore
        if _harness is not None:
            cfg = _harness.get_provider_config()
            model = str(getattr(cfg, "model", "") or "").strip()
            if model:
                prov = getattr(cfg, "provider", "")
                provider = str(getattr(prov, "value", prov) or "").strip()
                return model, provider or "openai"
    except Exception:
        pass
    return _resolve_primary_model()


def _is_deepseek_multi_tier(model: str, provider: str, base_url: str = "") -> bool:
    """仅当全局就是 deepseek 多档体系时，才启用 flash/pro 分档。"""
    m = (model or "").lower()
    p = (provider or "").lower()
    b = (base_url or "").lower()
    if "api.deepseek.com" in b:
        return True
    if "deepseek" in p:
        return True
    if m.startswith("deepseek"):
        return True
    return False


def prefer_global_model() -> bool:
    """只要「模型与连接」配置了全局 LLM，就强制全局为主；其它路由一律不改 model 名。

    未配置全局 LLM 时，默认仍锁定 settings/连接 model（避免 deepseek-v4-pro 硬编码）。
    仅当未设全局 且 AG_MODEL_ROUTE_ALLOW_SWITCH=1 时，才允许 deepseek 多档改名。
    """
    try:
        from ..chat_harness import _harness  # type: ignore
        if _harness is not None and getattr(_harness, "has_global_llm", lambda: False)():
            return True
    except Exception:
        pass
    v = (os.getenv("AG_MODEL_ROUTE_ALLOW_SWITCH") or "").strip().lower()
    return v not in ("1", "true", "yes", "on")


def clamp_model_to_global(
    routed: str,
    *,
    config_model: str = "",
    config_provider: str = "",
    base_url: str = "",
) -> str:
    """将 model_route 结果钳制到全局/连接模型。

    规则：配置了全局 LLM 或默认 prefer_global → 永远返回全局 model，
    禁止把 deepseek-v4-pro 等写进上游。
    """
    primary = (config_model or "").strip()
    provider = (config_provider or "").strip()
    if not primary:
        primary, provider = resolve_live_primary_model()
    routed = (routed or "").strip()
    if not primary:
        return routed
    if prefer_global_model():
        return primary
    if not _is_deepseek_multi_tier(primary, provider, base_url):
        return primary
    return routed or primary


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
        primary, provider = _resolve_primary_model()
        # 单模型网关（SJTU glm / qwen / codebuddy 等）：三档同名，避免改写成无权访问的 deepseek-*
        if not _is_deepseek_multi_tier(primary, provider):
            return {
                ModelTier.ECONOMY: TierConfig(
                    tier=ModelTier.ECONOMY, model=primary,
                    provider=provider or "openai", max_tokens=4096, temperature=0.5,
                ),
                ModelTier.STANDARD: TierConfig(
                    tier=ModelTier.STANDARD, model=primary,
                    provider=provider or "openai", max_tokens=8192, temperature=0.3,
                ),
                ModelTier.FRONTIER: TierConfig(
                    tier=ModelTier.FRONTIER, model=primary,
                    provider=provider or "openai", max_tokens=16384, temperature=0.2,
                ),
            }
        return {
            ModelTier.ECONOMY: TierConfig(
                tier=ModelTier.ECONOMY, model="deepseek-v4-flash",
                provider="deepseek", max_tokens=4096, temperature=0.5,
            ),
            ModelTier.STANDARD: TierConfig(
                tier=ModelTier.STANDARD, model=primary or "deepseek-v4-pro",
                provider="deepseek", max_tokens=8192, temperature=0.3,
            ),
            ModelTier.FRONTIER: TierConfig(
                tier=ModelTier.FRONTIER, model="glm-5.1",
                provider="codebuddy", max_tokens=16384, temperature=0.2,
            ),
        }

    def apply_primary_model(self, model: str, provider: str = "") -> None:
        """全局默认模型变更时同步三档（非 deepseek 多档时三档同名）。"""
        model = (model or "").strip()
        if not model:
            return
        provider = (provider or "").strip()
        changed = False
        if not _is_deepseek_multi_tier(model, provider):
            for tier, cfg in self.tiers.items():
                if cfg.model != model or (provider and cfg.provider != provider):
                    changed = True
                cfg.model = model
                if provider:
                    cfg.provider = provider
            if changed:
                logger.info(
                    "ModelRouter tiers synced to primary model=%s provider=%s",
                    model, provider or "-",
                )
            return
        # deepseek 多档：standard 跟随 primary，其余保留分档
        std = self.tiers.get(ModelTier.STANDARD)
        if std is not None:
            if std.model != model or (provider and std.provider != provider):
                changed = True
            std.model = model
            if provider:
                std.provider = provider
            if changed:
                logger.info(
                    "ModelRouter standard tier synced to model=%s provider=%s",
                    model, provider or "-",
                )

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

    def prefer_tier(self, target: ModelTier, reason: str = "cost_tier") -> None:
        """External cost-tier hint (Flowork-style). Respect sticky failures."""
        if self.state.consecutive_failures >= self.state.failure_threshold_up:
            return
        if self.state.sticky_remaining > 0 and target != self.state.current_tier:
            # still allow downgrade to economy for savings
            if not (target == ModelTier.ECONOMY and self.state.current_tier != ModelTier.ECONOMY):
                return
        self._switch_tier(target, reason)

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
    """返回路由器；每次取用时按全局配置软同步档位模型名。"""
    global _router
    if _router is None:
        _router = ModelRouter()
    else:
        try:
            m, p = resolve_live_primary_model()
            std = _router.tiers.get(ModelTier.STANDARD)
            if m and (std is None or std.model != m or not _is_deepseek_multi_tier(m, p)):
                # 非 deepseek 网关：始终对齐三档；deepseek 时仅当 standard 漂移才同步
                if not _is_deepseek_multi_tier(m, p) or (std and std.model != m):
                    _router.apply_primary_model(m, p)
        except Exception:
            pass
    return _router


def resync_model_router_from_primary(model: str = "", provider: str = "") -> None:
    """供 chat_harness 更新全局 provider 后调用，避免进程内仍持有 deepseek-v4-pro 档位。"""
    m = (model or "").strip()
    p = (provider or "").strip()
    if not m:
        m, p = resolve_live_primary_model()
    get_model_router().apply_primary_model(m, p)
