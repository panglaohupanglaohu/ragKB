# -*- coding: utf-8 -*-
"""Token budget and usage tracking regression tests."""

from __future__ import annotations

import json

import pytest

from agents import api as api_module
from agents.budget.guard import BudgetGuard, TokenBudget
from agents.budget.models import UsageRecord
from agents.budget.store import UsageStore
from agents.chat_harness import ChatHarness, LLMClient, ProviderConfig


@pytest.fixture
def temp_budget_env(monkeypatch, tmp_path):
    from agents.budget import guard as guard_module
    from agents.budget import store as store_module

    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "llm": {"provider": "deepseek", "model": "deepseek-v4-pro"},
                "budget": {
                    "per_session_max": 200_000,
                    "per_agent_daily_max": 2_000_000,
                    "per_team_daily_max": 10_000_000,
                    "on_exceed": "halt",
                    "alert_threshold": 0.8,
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(store_module, "_DB_PATH", tmp_path / "usage.db")
    monkeypatch.setattr(store_module, "_usage_store", None)
    monkeypatch.setattr(guard_module, "_SETTINGS_PATH", settings_path)
    monkeypatch.setattr(guard_module, "_budget_guard", None)

    return {
        "settings_path": settings_path,
        "db_path": tmp_path / "usage.db",
    }


class TestTokenBudget:
    def test_usage_store_summarizes_records(self, temp_budget_env):
        store = UsageStore(temp_budget_env["db_path"])
        store.record_usage(
            UsageRecord(
                session_id="sess-1",
                agent_id="agent-1",
                team_id="team-1",
                model="deepseek-v4-pro",
                input_tokens=120,
                output_tokens=30,
                total_tokens=150,
            )
        )
        store.record_usage(
            UsageRecord(
                session_id="sess-2",
                agent_id="agent-1",
                team_id="team-1",
                model="deepseek-v4-pro",
                input_tokens=80,
                output_tokens=20,
                total_tokens=100,
            )
        )

        summary = store.summarize_usage(agent_id="agent-1")

        assert summary["record_count"] == 2
        assert summary["input_tokens"] == 200
        assert summary["output_tokens"] == 50
        assert summary["total_tokens"] == 250
        assert len(summary["daily"]) == 1

    def test_budget_guard_blocks_session_overage_and_records_event(self, temp_budget_env):
        store = UsageStore(temp_budget_env["db_path"])
        store.record_usage(
            UsageRecord(
                session_id="sess-1",
                agent_id="agent-1",
                team_id="team-1",
                model="deepseek-v4-pro",
                total_tokens=90,
            )
        )
        guard = BudgetGuard(
            TokenBudget(
                per_session_max=100,
                per_agent_daily_max=1_000,
                per_team_daily_max=10_000,
                on_exceed="halt",
                alert_threshold=0.8,
            ),
            store=store,
        )

        result = guard.check(
            session_id="sess-1",
            agent_id="agent-1",
            team_id="team-1",
            estimated_tokens=20,
        )

        assert result.allowed is False
        assert any(event.level == "halt" for event in result.events)
        events = store.recent_events(limit=10)
        assert events[0]["scope"] == "session"
        assert events[0]["level"] == "halt"

    def test_budget_guard_warns_at_threshold_without_blocking(self, temp_budget_env):
        store = UsageStore(temp_budget_env["db_path"])
        guard = BudgetGuard(
            TokenBudget(
                per_session_max=100,
                per_agent_daily_max=1_000,
                per_team_daily_max=10_000,
                on_exceed="halt",
                alert_threshold=0.8,
            ),
            store=store,
        )

        result = guard.check(
            session_id="sess-threshold",
            agent_id="agent-threshold",
            team_id="team-threshold",
            estimated_tokens=80,
        )

        assert result.allowed is True
        assert result.events[0].scope == "session"
        assert result.events[0].level == "warn"
        assert result.events[0].message == "session token budget nearing limit: 80 / 100"

    def test_budget_guard_warn_mode_allows_overage(self, temp_budget_env):
        store = UsageStore(temp_budget_env["db_path"])
        guard = BudgetGuard(
            TokenBudget(
                per_session_max=100,
                per_agent_daily_max=1_000,
                per_team_daily_max=10_000,
                on_exceed="warn",
                alert_threshold=0.8,
            ),
            store=store,
        )

        result = guard.check(
            session_id="sess-warn",
            agent_id="agent-warn",
            team_id="team-warn",
            estimated_tokens=101,
        )

        assert result.allowed is True
        assert result.events[0].scope == "session"
        assert result.events[0].level == "warn"
        assert result.events[0].message == "session token budget exceeded: 101 > 100"

    def test_budget_guard_skips_empty_scope_and_disabled_limits(self, temp_budget_env):
        store = UsageStore(temp_budget_env["db_path"])
        guard = BudgetGuard(
            TokenBudget(
                per_session_max=0,
                per_agent_daily_max=100,
                per_team_daily_max=-1,
                on_exceed="halt",
                alert_threshold=0.8,
            ),
            store=store,
        )

        result = guard.check(
            session_id="sess-disabled",
            agent_id="",
            team_id="team-disabled",
            estimated_tokens=1_000,
        )

        assert result.allowed is True
        assert result.events == []
        assert store.recent_events(limit=10) == []

    def test_budget_guard_preserves_session_agent_team_event_order(self, temp_budget_env):
        store = UsageStore(temp_budget_env["db_path"])
        guard = BudgetGuard(
            TokenBudget(
                per_session_max=10,
                per_agent_daily_max=10,
                per_team_daily_max=10,
                on_exceed="halt",
                alert_threshold=0.8,
            ),
            store=store,
        )

        result = guard.check(
            session_id="sess-order",
            agent_id="agent-order",
            team_id="team-order",
            estimated_tokens=11,
        )

        assert result.allowed is False
        assert [event.scope for event in result.events] == ["session", "agent", "team"]

    @pytest.mark.asyncio
    async def test_chat_halts_before_llm_call_when_budget_exceeded(self, temp_budget_env, monkeypatch):
        store = UsageStore(temp_budget_env["db_path"])
        guard = BudgetGuard(
            TokenBudget(
                per_session_max=10,
                per_agent_daily_max=100,
                per_team_daily_max=100,
                on_exceed="halt",
                alert_threshold=0.8,
            ),
            store=store,
        )
        monkeypatch.setattr("agents.chat_harness.get_budget_guard", lambda: guard)

        called = {"value": False}

        async def fake_chat_completion(self, *args, **kwargs):
            called["value"] = True
            return {"choices": [{"message": {"content": "should not happen"}}], "usage": {}}

        monkeypatch.setattr(LLMClient, "chat_completion", fake_chat_completion)

        harness = ChatHarness(
            default_config=ProviderConfig(model="deepseek-v4-pro", max_tokens=100)
        )
        result = await harness.chat(
            "请帮我做一个非常长的分析。" * 20,
            agent_id="agent-1",
            team_id="team-1",
            session_id="sess-1",
        )

        assert called["value"] is False
        assert result.stop_reason == "budget_exceeded"
        assert "预算限制" in result.response

    def test_update_usage_budget_persists_settings_and_summary_endpoint(self, temp_budget_env, monkeypatch):
        from agents.budget import guard as guard_module
        from agents.budget import store as store_module

        store = UsageStore(temp_budget_env["db_path"])
        store.record_usage(
            UsageRecord(
                session_id="sess-1",
                agent_id="agent-1",
                team_id="team-1",
                model="deepseek-v4-pro",
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
            )
        )
        monkeypatch.setattr(api_module, "get_usage_store", lambda: store)
        monkeypatch.setattr(
            api_module,
            "get_budget_guard",
            lambda: guard_module.BudgetGuard(
                TokenBudget(),
                store=store,
            ),
        )

        result = api_module.update_usage_budget(
            api_module.UsageBudgetUpdateRequest(
                per_session_max=1234,
                per_agent_daily_max=5678,
                per_team_daily_max=9999,
                on_exceed="warn",
                alert_threshold=0.9,
            )
        )
        summary = api_module.get_usage_summary(agent_id="agent-1")

        saved = json.loads(temp_budget_env["settings_path"].read_text(encoding="utf-8"))
        assert result["budget"]["per_session_max"] == 1234
        assert saved["budget"]["on_exceed"] == "warn"
        assert summary["total_tokens"] == 75
        assert summary["filters"]["agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_stream_chat_records_estimated_usage_when_provider_omits_usage(self, temp_budget_env, monkeypatch):
        store = UsageStore(temp_budget_env["db_path"])
        guard = BudgetGuard(TokenBudget(), store=store)
        monkeypatch.setattr("agents.chat_harness.get_budget_guard", lambda: guard)

        async def fake_stream(self, messages, *, model=""):
            yield {"choices": [{"delta": {"content": "hello "}}]}
            yield {"choices": [{"delta": {"content": "world"}}]}

        monkeypatch.setattr(LLMClient, "stream_chat_completion", fake_stream)

        harness = ChatHarness(
            default_config=ProviderConfig(model="deepseek-v4-pro", max_tokens=100)
        )
        chunks = [
            chunk
            async for chunk in harness.stream_chat(
                "请用一句英文问候我。",
                agent_id="agent-1",
                team_id="team-1",
                session_id="sess-stream-1",
            )
        ]

        summary = store.summarize_usage(agent_id="agent-1")

        assert summary["record_count"] == 1
        assert summary["total_tokens"] > 0
        assert chunks[-1]["type"] == "message_stop"
        assert chunks[-1]["usage"]["total_tokens"] == summary["total_tokens"]

    @pytest.mark.asyncio
    async def test_stream_chat_prefers_provider_usage_payload(self, temp_budget_env, monkeypatch):
        store = UsageStore(temp_budget_env["db_path"])
        guard = BudgetGuard(TokenBudget(), store=store)
        monkeypatch.setattr("agents.chat_harness.get_budget_guard", lambda: guard)

        async def fake_stream(self, messages, *, model=""):
            yield {"choices": [{"delta": {"content": "hi"}}]}
            yield {"usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17}}

        monkeypatch.setattr(LLMClient, "stream_chat_completion", fake_stream)

        harness = ChatHarness(
            default_config=ProviderConfig(model="deepseek-v4-pro", max_tokens=100)
        )
        chunks = [
            chunk
            async for chunk in harness.stream_chat(
                "say hi",
                agent_id="agent-2",
                team_id="team-2",
                session_id="sess-stream-2",
            )
        ]

        summary = store.summarize_usage(agent_id="agent-2")

        assert summary["record_count"] == 1
        assert summary["total_tokens"] == 17
        assert chunks[-1]["usage"]["input_tokens"] == 12
        assert chunks[-1]["usage"]["output_tokens"] == 5
