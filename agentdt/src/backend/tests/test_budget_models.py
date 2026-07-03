# -*- coding: utf-8 -*-
"""Regression tests for token budget data models."""

from __future__ import annotations

from agents.budget.models import BudgetEvent, TokenBudget, UsageRecord


def test_token_budget_to_dict_preserves_public_shape():
    budget = TokenBudget(
        per_session_max=1,
        per_agent_daily_max=2,
        per_team_daily_max=3,
        on_exceed="warn",
        alert_threshold=0.75,
    )

    assert budget.to_dict() == {
        "per_session_max": 1,
        "per_agent_daily_max": 2,
        "per_team_daily_max": 3,
        "on_exceed": "warn",
        "alert_threshold": 0.75,
    }


def test_usage_record_date_uses_utc_timestamp():
    record = UsageRecord(
        session_id="sess-1",
        agent_id="agent-1",
        team_id="team-1",
        model="deepseek-v4-pro",
        total_tokens=100,
        timestamp=1782432000.0,
    )

    assert record.date == "2026-06-26"
    assert record.phase == "task"
    assert record.skill_id == ""
    assert record.scenario_id == ""
    assert record.run_id == ""


def test_budget_event_date_uses_utc_timestamp():
    event = BudgetEvent(
        scope="session",
        scope_id="sess-1",
        level="halt",
        value=120,
        limit=100,
        message="over budget",
        timestamp=1782432000.0,
    )

    assert event.date == "2026-06-26"
    assert event.scope == "session"
    assert event.level == "halt"
