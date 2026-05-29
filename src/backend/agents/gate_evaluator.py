# -*- coding: utf-8 -*-
"""门禁评估器 — 无状态纯函数 evaluate(context) → {score, level}.

设计原则:
  - **纯函数**: 零外部依赖、零副作用、零 I/O
  - **确定性**: 相同输入产生相同输出
  - **幂等**: 多次调用结果一致

评分算法:
  综合评分 = 加权平均(维度分数) − 否决项扣分

维度权重 (对标 DNV CII 框架):
  - compliance_score:  25%  (合规评分)
  - test_pass_rate:     20%  (测试通过率)
  - code_quality_score: 20%  (代码质量)
  - security_issues:    15%  (安全扣分 → 线性映射)
  - documentation_level: 10% (文档完善度)
  - performance_impact:  10% (性能影响)

否决项 (一票否决, score 强制 ≤ 39 = E 级):
  - has_critical_security_issue → 自动 E 级
  - has_breaking_change        → 自动 E 级
  - critical_test_failures > 0 → 自动 E 级
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from .review_models import GateEvaluationContext, GateEvaluationResult, GateLevel


# ── 维度权重 (sum = 1.0) ────────────────────────────────────

_DIMENSION_WEIGHTS: Dict[str, float] = {
    "compliance_score": 0.25,
    "test_pass_rate": 0.20,
    "code_quality_score": 0.20,
    "security_score": 0.15,          # security_issues 映射为安全分
    "documentation_level": 0.10,
    "performance_score": 0.10,       # performance_impact 映射
}

# 安全扣分阶梯 (security_issues → security_score)
_SECURITY_PENALTY_MAP: Dict[int, float] = {
    0: 100.0,
    1: 70.0,
    2: 50.0,
    3: 30.0,
    4: 15.0,
}
_SECURITY_PENALTY_DEFAULT = 0.0  # ≥5 → 0 分

# 性能影响映射 (-100~+100 → 0~100)
#   +100 → 100 (显著优化)
#     0 →  50 (中性)
#   -100 →  0 (严重劣化)


def evaluate(context: GateEvaluationContext) -> GateEvaluationResult:
    """门禁评估纯函数 — 根据上下文产出评分与等级.

    Args:
        context: 评估上下文，包含所有评估维度的量化数据

    Returns:
        GateEvaluationResult: {score, level, passed, reasons, warnings, blocked_by}

    使用示例:
        ctx = GateEvaluationContext(
            entity_id="EVO-1",
            compliance_score=88.0,
            test_pass_rate=95.0,
            code_quality_score=82.0,
        )
        result = evaluate(ctx)
        print(f"评分: {result.score}, 等级: {result.level}, 通过: {result.passed}")
    """
    reasons: List[str] = []
    warnings: List[str] = []
    blocked_by: List[str] = []

    # ── 第一步: 检查否决项 ─────────────────────────────────
    if context.has_critical_security_issue:
        blocked_by.append("存在严重安全漏洞 (has_critical_security_issue=True)")
    if context.has_breaking_change or context.breaking_changes:
        blocked_by.append("breaking_changes: 存在破坏性变更")
    if context.critical_test_failures > 0:
        blocked_by.append(f"关键测试失败 {context.critical_test_failures} 项")

    if blocked_by:
        return GateEvaluationResult(
            score=0.0,
            level=GateLevel.E,
            passed=False,
            reasons=[f"一票否决: {', '.join(blocked_by)}"],
            warnings=warnings,
            blocked_by=blocked_by,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ── 第二步: 计算各维度评分 ─────────────────────────────
    dim_scores, dim_reasons = _calculate_dimension_scores(context)

    # ── 第三步: 加权综合 ───────────────────────────────────
    weighted_score = _compute_weighted_score(dim_scores)
    score = round(weighted_score, 1)

    # Clamp to [0, 100]
    score = max(0.0, min(100.0, score))

    # ── 第四步: 确定等级与判定 ─────────────────────────────
    level = GateLevel.from_score(score)
    passed = level in (GateLevel.A, GateLevel.B, GateLevel.C)  # C 及以上通过

    # ── 第五步: 汇总理由与警告 ─────────────────────────────
    reasons.extend(dim_reasons)
    reasons.append(f"综合评分={score:.1f}, 等级={level.value}")

    if not passed:
        warnings.append(f"门禁未通过: 等级 {level.value} 低于 C 级，需改进后重审")
    if level == GateLevel.C:
        warnings.append("等级 C: 基本合规但存在改进空间")
    if level == GateLevel.D:
        warnings.append("等级 D: 多项不达标，强烈建议整改")
    if level == GateLevel.E:
        warnings.append("等级 E: 严重不合规，必须阻止上线")

    return GateEvaluationResult(
        score=score,
        level=level,
        passed=passed,
        reasons=reasons,
        warnings=warnings,
        blocked_by=blocked_by,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _calculate_dimension_scores(ctx: GateEvaluationContext) -> Tuple[Dict[str, float], List[str]]:
    """计算各维度标准化分数 (0~100) 及详细理由."""
    scores: Dict[str, float] = {}
    reasons: List[str] = []

    # 合规评分 (直接使用)
    compliance_score = _clamp(ctx.compliance_score)
    scores["compliance_score"] = compliance_score
    reasons.append(f"合规评分={compliance_score:.1f}")

    # 测试通过率
    test_pass_rate = _clamp(ctx.test_pass_rate)
    scores["test_pass_rate"] = test_pass_rate
    reasons.append(f"测试通过率={test_pass_rate:.1f}%")

    # 代码质量
    code_quality_score = _clamp(ctx.code_quality_score)
    scores["code_quality_score"] = code_quality_score
    reasons.append(f"代码质量={code_quality_score:.1f}")

    # 安全问题 → 评分 (低分是好)
    security_issues = max(0, int(ctx.security_issues))
    sec_score = _map_security_issues_to_score(security_issues)
    scores["security_score"] = sec_score
    reasons.append(f"安全问题={security_issues} → 安全评分={sec_score:.1f}")

    # 文档完善度
    documentation_level = _clamp(ctx.documentation_level)
    scores["documentation_level"] = documentation_level
    reasons.append(f"文档完善度={documentation_level:.1f}")

    # 性能影响映射
    raw_impact = ctx.performance_impact if ctx.performance_impact else ctx.evolution_impact
    perf_score = _map_performance_impact(raw_impact)
    scores["performance_score"] = perf_score
    reasons.append(f"性能影响={raw_impact:.1f} → 性能评分={perf_score:.1f}")

    return scores, reasons


def _compute_weighted_score(dim_scores: Dict[str, float]) -> float:
    """加权求和."""
    aliases = {
        "compliance_score": "compliance",
        "test_pass_rate": "test_pass",
        "code_quality_score": "code_quality",
        "security_score": "security",
        "documentation_level": "documentation",
    }
    total = 0.0
    for dim, weight in _DIMENSION_WEIGHTS.items():
        value = dim_scores.get(dim)
        if value is None and dim in aliases:
            value = dim_scores.get(aliases[dim])
        total += _clamp(value or 0.0) * weight
    return total


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Clamp numeric inputs to the scoring range."""
    if math.isnan(float(value)):
        return low
    return max(low, min(high, float(value)))


def _map_security_issues_to_score(count: int) -> float:
    """安全问题数 → 安全评分 (0~100)."""
    if count == 0:
        return 100.0
    # 使用阶梯映射
    if count <= 1:
        return 70.0
    if count <= 2:
        return 50.0
    if count <= 3:
        return 30.0
    if count <= 4:
        return 15.0
    return 0.0  # 5+ → 0


def _map_performance_impact(raw: float) -> float:
    """性能影响 (-100~+100) → 性能评分 (0~100).

    +100 (显著优化)  → 100
       0 (中性)      →  50
    -100 (严重劣化)  →   0
    """
    # 将 [-100, 100] 线性映射到 [0, 100]
    return max(0.0, min(100.0, (raw + 100.0) / 2.0))


# ── 便捷函数 ────────────────────────────────────────────────


def evaluate_from_dict(data: dict) -> GateEvaluationResult:
    """从字典创建评估上下文并评估 — 方便与其他系统对接."""
    ctx = GateEvaluationContext(**data)
    return evaluate(ctx)


def quick_evaluate(
    entity_id: str,
    compliance_score: float = 0.0,
    test_pass_rate: float = 100.0,
    code_quality_score: float = 0.0,
    security_issues: int = 0,
    has_critical_security_issue: bool = False,
    has_breaking_change: bool = False,
    critical_test_failures: int = 0,
    **kwargs,
) -> GateEvaluationResult:
    """快速评估 — 最简调用."""
    ctx = GateEvaluationContext(
        entity_id=entity_id,
        compliance_score=compliance_score,
        test_pass_rate=test_pass_rate,
        code_quality_score=code_quality_score,
        security_issues=security_issues,
        has_critical_security_issue=has_critical_security_issue,
        has_breaking_change=has_breaking_change,
        critical_test_failures=critical_test_failures,
        **kwargs,
    )
    return evaluate(ctx)
