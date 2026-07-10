# -*- coding: utf-8 -*-
"""TeamManager × HealthLedger 事件映射测试.

对应 docs/Agent仿生生态运行时todos.md P2-2。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agents.models import AgentProfile, AgentState
from agents.runtime.health_ledger import HealthLedger


def _add_agent(team_manager, team_id: str, agent_id: str) -> AgentProfile:
    team_manager.create_team(name="生态测试团队", team_id=team_id)
    agent = AgentProfile(agent_id=agent_id, name="测试体", role="worker")
    team_manager.add_agent_to_team(team_id, agent)
    return agent


class TestApplyHealthEvent:
    def test_dormant_event_sets_stopped_state(self, team_manager):
        _add_agent(team_manager, "t1", "a1")
        updated = team_manager.apply_health_event("t1", "a1", "dormant")
        assert updated is not None
        assert updated.state == AgentState.STOPPED

    def test_revived_event_sets_idle_state(self, team_manager):
        _add_agent(team_manager, "t1", "a1")
        team_manager.apply_health_event("t1", "a1", "dormant")
        updated = team_manager.apply_health_event("t1", "a1", "revived")
        assert updated.state == AgentState.IDLE

    def test_unknown_event_does_not_change_state(self, team_manager):
        agent = _add_agent(team_manager, "t1", "a1")
        original_state = agent.state
        updated = team_manager.apply_health_event("t1", "a1", "mystery_event")
        assert updated.state == original_state

    def test_unknown_team_returns_none(self, team_manager):
        assert team_manager.apply_health_event("ghost-team", "a1", "dormant") is None

    def test_unknown_agent_returns_none(self, team_manager):
        team_manager.create_team(name="T", team_id="t1")
        assert team_manager.apply_health_event("t1", "ghost-agent", "dormant") is None


class TestReviveAgent:
    def test_revive_agent_without_health_ledger(self, team_manager):
        _add_agent(team_manager, "t1", "a1")
        team_manager.apply_health_event("t1", "a1", "dormant")
        revived = team_manager.revive_agent("t1", "a1")
        assert revived.state == AgentState.IDLE

    def test_revive_agent_with_health_ledger_linked(self, team_manager):
        _add_agent(team_manager, "t1", "a1")
        team_manager.apply_health_event("t1", "a1", "dormant")

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = HealthLedger(team_id="t1", ledger_dir=Path(tmpdir))
            ledger.get_or_create("a1", health_max=10.0, metabolic_rate=10.0)
            ledger.tick("a1")  # 触发 dormant
            assert ledger.get("a1").status == "dormant"

            revived = team_manager.revive_agent("t1", "a1", health_ledger=ledger, revive_ratio=0.5)
            assert revived.state == AgentState.IDLE
            assert ledger.get("a1").status == "active"
            assert ledger.get("a1").health == pytest.approx(5.0)

    def test_revive_agent_health_ledger_failure_does_not_block_state_revival(self, team_manager):
        """Health 联动异常不应阻断状态复活本身（防御性设计）."""
        _add_agent(team_manager, "t1", "a1")
        team_manager.apply_health_event("t1", "a1", "dormant")

        class _BrokenLedger:
            def revive(self, *args, **kwargs):
                raise RuntimeError("boom")

        revived = team_manager.revive_agent("t1", "a1", health_ledger=_BrokenLedger())
        assert revived.state == AgentState.IDLE

    def test_revive_unknown_agent_returns_none(self, team_manager):
        team_manager.create_team(name="T", team_id="t1")
        assert team_manager.revive_agent("t1", "ghost") is None
