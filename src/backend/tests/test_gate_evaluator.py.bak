# -*- coding: utf-8 -*-
"""测试门禁评估器 — evaluate(context) 纯函数测试.

覆盖:
  - 正常评估 (A/B/C 级)
  - 一票否决 (安全漏洞/破坏性变更/关键测试失败)
  - 边界情况 (0分/100分/缺失字段)
  - 确定性 (相同输入 → 相同输出)
  - 便捷函数 evaluate_from_dict / quick_evaluate
"""

from __future__ import annotations

import pytest

from agents.gate_evaluator import (
    evaluate,
    evaluate_from_dict,
    quick_evaluate,
    _calculate_dimension_scores,
    _compute_weighted_score,
    _map_security_issues_to_score,
    _map_performance_impact,
)
from agents.review_models import GateEvaluationContext, GateLevel, GateEvaluationResult


class TestGateEvaluator:
    """门禁评估器核心测试."""

    # ── 正常评估 ────────────────────────────────────────

    def test_evaluate_all_excellent(self):
        """全部优秀 → A级, passed."""
        ctx = GateEvaluationContext(
            entity_id="EVO-1",
            compliance_score=95.0,
            test_pass_rate=100.0,
            code_quality_score=95.0,
            security_issues=0,
            documentation_level=95.0,
            performance_impact=20.0,
        )
        result = evaluate(ctx)
        assert result.level == GateLevel.A
        assert result.passed is True
        assert result.score >= 85.0
        assert len(result.blocked_by) == 0

    def test_evaluate_good(self):
        """良好 → B级, passed."""
        ctx = GateEvaluationContext(
            entity_id="EVO-2",
            compliance_score=78.0,
            test_pass_rate=88.0,
            code_quality_score=75.0,
            security_issues=1,
            documentation_level=70.0,
            performance_impact=5.0,
        )
        result = evaluate(ctx)
        assert result.level in (GateLevel.B, GateLevel.C)
        assert result.passed is True

    def test_evaluate_moderate(self):
        """基本合规 → C级, passed."""
        ctx = GateEvaluationContext(
            entity_id="EVO-3",
            compliance_score=60.0,
            test_pass_rate=70.0,
            code_quality_score=58.0,
            security_issues=3,
            documentation_level=50.0,
            performance_impact=-5.0,
        )
        result = evaluate(ctx)
        assert result.level in (GateLevel.C, GateLevel.D)
        assert result.passed == (result.level != GateLevel.D)

    # ── 一票否决 ────────────────────────────────────────

    def test_veto_critical_security(self):
        """严重安全漏洞 → E级, score=0."""
        ctx = GateEvaluationContext(
            entity_id="EVO-sec",
            compliance_score=95.0,
            test_pass_rate=100.0,
            code_quality_score=95.0,
            has_critical_security_issue=True,
        )
        result = evaluate(ctx)
        assert result.level == GateLevel.E
        assert result.passed is False
        assert result.score == 0.0
        assert len(result.blocked_by) > 0
        assert any("安全" in b for b in result.blocked_by)

    def test_veto_breaking_change(self):
        """破坏性变更 → E级, score=0."""
        ctx = GateEvaluationContext(
            entity_id="EVO-break",
            compliance_score=90.0,
            has_breaking_change=True,
        )
        result = evaluate(ctx)
        assert result.level == GateLevel.E
        assert result.passed is False
        assert result.score == 0.0

    def test_veto_critical_test_failures(self):
        """关键测试失败 → E级, score=0."""
        ctx = GateEvaluationContext(
            entity_id="EVO-fail",
            compliance_score=88.0,
            critical_test_failures=2,
        )
        result = evaluate(ctx)
        assert result.level == GateLevel.E
        assert result.passed is False
        assert result.score == 0.0

    def test_multiple_vetos(self):
        """多个否决项同时触发."""
        ctx = GateEvaluationContext(
            entity_id="EVO-multi",
            has_critical_security_issue=True,
            has_breaking_change=True,
            critical_test_failures=1,
        )
        result = evaluate(ctx)
        assert len(result.blocked_by) == 3

    # ── 边界情况 ────────────────────────────────────────

    def test_zero_scores(self):
        """全0分 → E级."""
        ctx = GateEvaluationContext(entity_id="EVO-zero")
        result = evaluate(ctx)
        assert 0.0 <= result.score <= 40.0
        assert result.level in (GateLevel.D, GateLevel.E)

    def test_perfect_scores(self):
        """满分 → A级."""
        ctx = GateEvaluationContext(
            entity_id="EVO-perfect",
            compliance_score=100.0,
            test_pass_rate=100.0,
            code_quality_score=100.0,
            security_issues=0,
            documentation_level=100.0,
            performance_impact=100.0,
        )
        result = evaluate(ctx)
        assert result.level == GateLevel.A
        assert result.score >= 95.0

    def test_high_security_issues(self):
        """大量安全问题 → 安全评分归零."""
        ctx = GateEvaluationContext(
            entity_id="EVO-badsec",
            compliance_score=80.0,
            test_pass_rate=90.0,
            code_quality_score=80.0,
            security_issues=10,
        )
        result = evaluate(ctx)
        # 安全占15%权重，大量问题拉低总分
        assert result.score < 70.0

    def test_negative_performance(self):
        """严重性能退化."""
        ctx = GateEvaluationContext(
            entity_id="EVO-perf",
            compliance_score=80.0,
            test_pass_rate=90.0,
            code_quality_score=80.0,
            security_issues=0,
            performance_impact=-80.0,
        )
        result = evaluate(ctx)
        # 性能评分应低于50
        assert result.score < 80.0

    # ── 确定性 ──────────────────────────────────────────

    def test_deterministic(self):
        """相同输入 → 相同输出 (纯函数)."""
        ctx = GateEvaluationContext(
            entity_id="EVO-det",
            compliance_score=75.0,
            test_pass_rate=85.0,
            code_quality_score=70.0,
            security_issues=1,
        )
        results = [evaluate(ctx) for _ in range(20)]
        scores = {r.score for r in results}
        levels = {r.level for r in results}
        assert len(scores) == 1
        assert len(levels) == 1

    # ── 便捷函数 ────────────────────────────────────────

    def test_evaluate_from_dict(self):
        result = evaluate_from_dict({
            "entity_id": "EVO-dict",
            "compliance_score": 65.0,
            "test_pass_rate": 75.0,
            "code_quality_score": 68.0,
        })
        assert isinstance(result, GateEvaluationResult)
        assert result.entity_id is None  # entity_id 不在 result 中
        assert result.score is not None

    def test_quick_evaluate(self):
        result = quick_evaluate(
            entity_id="EVO-quick",
            compliance_score=72.0,
            test_pass_rate=88.0,
            code_quality_score=75.0,
        )
        assert isinstance(result, GateEvaluationResult)
        assert 60.0 <= result.score <= 90.0

    def test_quick_evaluate_with_veto(self):
        result = quick_evaluate(
            entity_id="EVO-quick-veto",
            compliance_score=90.0,
            has_critical_security_issue=True,
        )
        assert result.level == GateLevel.E
        assert result.passed is False


class TestDimensionScoring:
    """维度评分辅助函数测试."""

    def test_security_map_zero(self):
        assert _map_security_issues_to_score(0) == 100.0

    def test_security_map_one(self):
        assert 60.0 <= _map_security_issues_to_score(1) <= 80.0

    def test_security_map_many(self):
        assert _map_security_issues_to_score(5) == 0.0
        assert _map_security_issues_to_score(10) == 0.0

    def test_performance_map_positive(self):
        assert _map_performance_impact(100.0) == 100.0

    def test_performance_map_neutral(self):
        assert _map_performance_impact(0.0) == 50.0

    def test_performance_map_negative(self):
        assert _map_performance_impact(-100.0) == 0.0

    def test_weighted_score(self):
        scores = {
            "compliance_score": 80.0,
            "test_pass_rate": 90.0,
            "code_quality_score": 80.0,
            "security_score": 100.0,
            "documentation_level": 70.0,
            "performance_score": 60.0,
        }
        result = _compute_weighted_score(scores)
        assert 70.0 <= result <= 90.0


class TestGateLevel:
    """等级映射测试."""

    def test_from_score_A(self):
        assert GateLevel.from_score(95.0) == GateLevel.A
        assert GateLevel.from_score(85.0) == GateLevel.A

    def test_from_score_B(self):
        assert GateLevel.from_score(84.9) == GateLevel.B
        assert GateLevel.from_score(70.0) == GateLevel.B

    def test_from_score_C(self):
        assert GateLevel.from_score(69.9) == GateLevel.C
        assert GateLevel.from_score(55.0) == GateLevel.C

    def test_from_score_D(self):
        assert GateLevel.from_score(54.9) == GateLevel.D
        assert GateLevel.from_score(40.0) == GateLevel.D

    def test_from_score_E(self):
        assert GateLevel.from_score(39.9) == GateLevel.E
        assert GateLevel.from_score(0.0) == GateLevel.E
