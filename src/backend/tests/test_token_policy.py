# -*- coding: utf-8 -*-
"""Regression tests for the token policy engine."""

from __future__ import annotations

from agents.token_policy import TokenBudget, TokenBudgetEngine, TokenViolationType


def test_token_policy_passes_when_no_budget_limits_are_hit():
    result = TokenBudgetEngine().evaluate(
        {"total": 500, "score": 2.5, "calls": 1},
        TokenBudget(max_tokens=1000, min_efficiency=1.0, max_burst_per_min=100),
    )

    assert result == {
        "decision": "pass",
        "efficiency": 5.0,
        "total_tokens": 500,
        "calls": 1,
        "violations": [],
    }


def test_token_policy_warns_for_medium_only_violations():
    result = TokenBudgetEngine().evaluate(
        {
            "total": 500,
            "score": 2.5,
            "calls": 3,
            "dup_intent_calls": 2,
            "skill_available": True,
            "used_raw_llm": True,
        },
        TokenBudget(max_tokens=1000, min_efficiency=1.0, max_burst_per_min=100),
    )

    assert result["decision"] == "warn"
    assert result["violations"] == [
        {"type": TokenViolationType.REDUNDANT_LLM_CALLS.value, "severity": "medium"},
        {"type": TokenViolationType.SKILL_ROUTING_MISS.value, "severity": "medium"},
    ]


def test_token_policy_blocks_for_high_or_critical_violations():
    result = TokenBudgetEngine().evaluate(
        {
            "total": 1500,
            "score": 0.3,
            "calls": 4,
            "dup_intent_calls": 2,
            "skill_available": True,
            "used_raw_llm": True,
            "burst_rate": 250,
        },
        TokenBudget(max_tokens=1000, min_efficiency=1.0, max_burst_per_min=100),
    )

    assert result["decision"] == "block"
    assert result["efficiency"] == 0.2
    assert result["violations"] == [
        {"type": TokenViolationType.TOKEN_OVER_BUDGET.value, "severity": "critical"},
        {"type": TokenViolationType.LOW_TOKEN_EFFICIENCY.value, "severity": "high"},
        {"type": TokenViolationType.REDUNDANT_LLM_CALLS.value, "severity": "medium"},
        {"type": TokenViolationType.SKILL_ROUTING_MISS.value, "severity": "medium"},
        {"type": TokenViolationType.DRILL_TOKEN_BURST.value, "severity": "high"},
    ]


def test_token_policy_keeps_zero_token_efficiency_at_zero():
    result = TokenBudgetEngine().evaluate(
        {"total": 0, "score": 5, "calls": 0},
        TokenBudget(min_efficiency=1.0),
    )

    assert result["decision"] == "block"
    assert result["efficiency"] == 0.0
    assert result["violations"] == [
        {"type": TokenViolationType.LOW_TOKEN_EFFICIENCY.value, "severity": "high"},
    ]
