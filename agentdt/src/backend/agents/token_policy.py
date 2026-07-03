"""TokenBudgetEngine — Token 策略引擎（Cost Gate 的 Token 语义版）。

替代 Terraform 资源成本策略，专注 LLM Token 效率。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

logger = logging.getLogger(__name__)


class TokenViolationType(str, Enum):
    TOKEN_OVER_BUDGET = "token_over_budget"        # 本次 run token 超预算
    LOW_TOKEN_EFFICIENCY = "low_token_efficiency"  # score/1k 低于阈值
    REDUNDANT_LLM_CALLS = "redundant_llm_calls"    # 同意图重复 LLM，可萃取 skill
    SKILL_ROUTING_MISS = "skill_routing_miss"      # 有可复用 skill 却走原始 LLM
    DRILL_TOKEN_BURST = "drill_token_burst"        # 演练 token 速率突增


@dataclass
class TokenBudget:
    max_tokens: int = 0          # 0=不限
    min_efficiency: float = 0.0  # 0=不检
    max_burst_per_min: int = 0


@dataclass
class TokenBudgetEngine:
    """纯函数 Token 策略评估引擎。"""

    def evaluate(self, run: dict, budget: TokenBudget) -> dict:
        """评估一次 run 的 Token 消耗是否合规。

        Args:
            run: run 数据（来自 LEDGER.run），含 total/score/dup_intent_calls 等
            budget: Token 预算配置

        Returns:
            {decision, efficiency, violations}
        """
        violations: List[Tuple[str, str]] = []  # (violation_type, severity)
        total = run.get("total", 0)
        score = run.get("score", 0)
        calls = run.get("calls", 0)

        eff = _token_efficiency(score, total)

        if budget.max_tokens and total > budget.max_tokens:
            _add_violation(violations, TokenViolationType.TOKEN_OVER_BUDGET, "critical")

        if budget.min_efficiency and eff < budget.min_efficiency:
            _add_violation(violations, TokenViolationType.LOW_TOKEN_EFFICIENCY, "high")

        dup_calls = run.get("dup_intent_calls", 0)
        if dup_calls >= 2:
            _add_violation(violations, TokenViolationType.REDUNDANT_LLM_CALLS, "medium")

        if run.get("skill_available") and run.get("used_raw_llm"):
            _add_violation(violations, TokenViolationType.SKILL_ROUTING_MISS, "medium")

        burst_rate = run.get("burst_rate", 0)
        if budget.max_burst_per_min and burst_rate > budget.max_burst_per_min:
            _add_violation(violations, TokenViolationType.DRILL_TOKEN_BURST, "high")

        return {
            "decision": _decision_from_violations(violations),
            "efficiency": round(eff, 4),
            "total_tokens": total,
            "calls": calls,
            "violations": [{"type": t, "severity": s} for t, s in violations],
        }


def _token_efficiency(score: float, total_tokens: int) -> float:
    if total_tokens <= 0:
        return 0.0
    return score / max(total_tokens / 1000, 1e-6)


def _add_violation(
    violations: List[Tuple[str, str]],
    violation_type: TokenViolationType,
    severity: str,
) -> None:
    violations.append((violation_type.value, severity))


def _decision_from_violations(violations: List[Tuple[str, str]]) -> str:
    severities = {severity for _, severity in violations}
    if severities & {"critical", "high"}:
        return "block"
    if violations:
        return "warn"
    return "pass"


ENGINE = TokenBudgetEngine()
