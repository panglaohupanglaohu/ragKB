# -*- coding: utf-8 -*-
"""交配门禁测试.

对应 docs/Agent仿生生态运行时todos.md P4-1。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agents.models import AgentProfile
from agents.runtime.health_ledger import HealthLedger, HealthState


def _add_agent(team_manager, team_id: str, agent_id: str) -> AgentProfile:
    team_manager.create_team(name="交配测试团队", team_id=team_id)
    agent = AgentProfile(agent_id=agent_id, name="亲代", role="worker")
    team_manager.add_agent_to_team(team_id, agent)
    return agent


class TestCanMate:
    def test_allowed_when_health_above_threshold(self, team_manager):
        state = HealthState(agent_id="a1", health=80.0, health_max=100.0, status="active")
        allowed, reason = team_manager.can_mate(state, saturation_threshold=0.7)
        assert allowed is True
        assert reason == "ok"

    def test_rejected_when_health_below_threshold(self, team_manager):
        state = HealthState(agent_id="a1", health=50.0, health_max=100.0, status="active")
        allowed, reason = team_manager.can_mate(state, saturation_threshold=0.7)
        assert allowed is False
        assert "insufficient_saturation" in reason

    def test_rejected_when_dormant(self, team_manager):
        state = HealthState(agent_id="a1", health=100.0, health_max=100.0, status="dormant")
        allowed, reason = team_manager.can_mate(state)
        assert allowed is False
        assert reason == "dormant_cannot_mate"

    def test_rejected_when_no_health_state(self, team_manager):
        allowed, reason = team_manager.can_mate(None)
        assert allowed is False
        assert reason == "no_health_state"

    def test_accepts_dict_shaped_health_state(self, team_manager):
        """鸭子类型：dict 结构也应被接受（不强制依赖 HealthState 类型）."""
        state = {"health": 90.0, "health_max": 100.0, "status": "active"}
        allowed, reason = team_manager.can_mate(state, saturation_threshold=0.7)
        assert allowed is True

    def test_boundary_exact_threshold_allowed(self, team_manager):
        state = HealthState(agent_id="a1", health=70.0, health_max=100.0, status="active")
        allowed, reason = team_manager.can_mate(state, saturation_threshold=0.7)
        assert allowed is True


class TestMate:
    def test_mate_rejected_when_health_insufficient(self, team_manager):
        _add_agent(team_manager, "t1", "a1")
        state = HealthState(agent_id="a1", health=10.0, health_max=100.0, status="active")
        result = team_manager.mate("t1", "a1", health_state=state)
        assert result is None
        # 未复制成功，团队里应只有 1 个 agent
        assert len(team_manager.list_agents("t1")) == 1

    def test_mate_succeeds_when_health_sufficient(self, team_manager):
        _add_agent(team_manager, "t1", "a1")
        state = HealthState(agent_id="a1", health=90.0, health_max=100.0, status="active")
        new_agent = team_manager.mate("t1", "a1", health_state=state)
        assert new_agent is not None
        assert len(team_manager.list_agents("t1")) == 2

    def test_mate_records_lineage_metadata(self, team_manager):
        _add_agent(team_manager, "t1", "a1")
        state = HealthState(agent_id="a1", health=90.0, health_max=100.0, status="active")
        new_agent = team_manager.mate("t1", "a1", health_state=state)
        assert new_agent.metadata["lineage"]["parent_agent_id"] == "a1"
        assert new_agent.metadata["lineage"]["generation"] == 1

    def test_mate_generation_increments_across_lineage(self, team_manager):
        _add_agent(team_manager, "t1", "a1")
        state = HealthState(agent_id="a1", health=90.0, health_max=100.0, status="active")
        child = team_manager.mate("t1", "a1", health_state=state)
        assert child.metadata["lineage"]["generation"] == 1

        # 第二代交配：以 child 为亲代
        grandchild_state = HealthState(agent_id=child.agent_id, health=90.0, health_max=100.0, status="active")
        grandchild = team_manager.mate("t1", child.agent_id, health_state=grandchild_state)
        assert grandchild.metadata["lineage"]["generation"] == 2
        assert grandchild.metadata["lineage"]["parent_agent_id"] == child.agent_id

    def test_mate_unknown_agent_returns_none(self, team_manager):
        team_manager.create_team(name="T", team_id="t1")
        state = HealthState(agent_id="ghost", health=90.0, health_max=100.0, status="active")
        assert team_manager.mate("t1", "ghost", health_state=state) is None

    def test_mate_end_to_end_with_real_ledger(self, team_manager):
        """整合真实 HealthLedger 而非手造 HealthState."""
        _add_agent(team_manager, "t1", "a1")
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = HealthLedger(team_id="t1", ledger_dir=Path(tmpdir))
            state = ledger.get_or_create("a1", health_max=100.0, metabolic_rate=1.0)
            # 保持满血（模拟长期饱暖）
            new_agent = team_manager.mate("t1", "a1", health_state=state)
            assert new_agent is not None


# ── ND-3: 双亲 skill 交叉遗传测试 ──────────────────────────────


def _add_agent_with_skills(team_manager, team_id, agent_id, skills):
    """添加带 skills 的 Agent 到团队（团队不存在时创建）."""
    if team_manager.get_team(team_id) is None:
        team_manager.create_team(name="交叉测试团队", team_id=team_id)
    agent = AgentProfile(agent_id=agent_id, name=agent_id, role="worker", skills=skills)
    team_manager.add_agent_to_team(team_id, agent)
    return agent


class TestMateCrossover:
    """ND-3.1: 双亲 skill 交叉遗传 — 后代 genome = 双亲交叉，谱系可追双亲."""

    def test_crossover_offspring_has_skills_from_both_parents(self, team_manager):
        _add_agent_with_skills(team_manager, "cx1", "parent_a", ["skill_a1", "skill_a2", "skill_a3", "skill_a4"])
        _add_agent_with_skills(team_manager, "cx1", "parent_b", ["skill_b1", "skill_b2", "skill_b3", "skill_b4"])
        state = HealthState(agent_id="parent_a", health=90.0, health_max=100.0, status="active")
        offspring = team_manager.mate("cx1", "parent_a", health_state=state, partner_agent_id="parent_b")
        assert offspring is not None
        # 后代 skills 应来自双亲（交叉子集）
        parent_a_skills = {"skill_a1", "skill_a2", "skill_a3", "skill_a4"}
        parent_b_skills = {"skill_b1", "skill_b2", "skill_b3", "skill_b4"}
        offspring_set = set(offspring.skills)
        # 至少有一个来自双亲各一方
        assert offspring_set & parent_a_skills, "后代缺少亲代 A 的 skill"
        assert offspring_set & parent_b_skills, "后代缺少亲代 B 的 skill"
        # 所有 skill 都应来自双亲并集
        assert offspring_set <= (parent_a_skills | parent_b_skills)

    def test_crossover_lineage_records_both_parents(self, team_manager):
        _add_agent_with_skills(team_manager, "cx2", "pa", ["s1", "s2"])
        _add_agent_with_skills(team_manager, "cx2", "pb", ["s3", "s4"])
        state = HealthState(agent_id="pa", health=90.0, health_max=100.0, status="active")
        offspring = team_manager.mate("cx2", "pa", health_state=state, partner_agent_id="pb")
        assert offspring is not None
        lineage = offspring.metadata["lineage"]
        assert lineage["parent_agent_id"] == "pa"
        assert lineage["partner_agent_id"] == "pb"
        assert lineage["crossover"] is True
        assert lineage["generation"] == 1

    def test_no_partner_still_works_single_parent(self, team_manager):
        """不传 partner_agent_id 时退回单亲复制（向后兼容）."""
        _add_agent_with_skills(team_manager, "cx3", "solo", ["s1", "s2"])
        state = HealthState(agent_id="solo", health=90.0, health_max=100.0, status="active")
        offspring = team_manager.mate("cx3", "solo", health_state=state)
        assert offspring is not None
        # 单亲模式：skills 完全继承
        assert set(offspring.skills) == {"s1", "s2"}
        lineage = offspring.metadata["lineage"]
        assert "partner_agent_id" not in lineage
        assert "crossover" not in lineage

    def test_crossover_unknown_partner_falls_back_to_single_parent(self, team_manager):
        """partner_agent_id 不存在时，退回单亲复制（不报错）."""
        _add_agent_with_skills(team_manager, "cx4", "real", ["s1", "s2"])
        state = HealthState(agent_id="real", health=90.0, health_max=100.0, status="active")
        offspring = team_manager.mate("cx4", "real", health_state=state, partner_agent_id="ghost")
        assert offspring is not None
        # 退回单亲
        assert set(offspring.skills) == {"s1", "s2"}

    def test_crossover_generation_increments(self, team_manager):
        _add_agent_with_skills(team_manager, "cx5", "gen0_a", ["s1", "s2"])
        _add_agent_with_skills(team_manager, "cx5", "gen0_b", ["s3", "s4"])
        state = HealthState(agent_id="gen0_a", health=90.0, health_max=100.0, status="active")
        child = team_manager.mate("cx5", "gen0_a", health_state=state, partner_agent_id="gen0_b")
        assert child.metadata["lineage"]["generation"] == 1

        # 第二代
        _add_agent_with_skills(team_manager, "cx5", "gen1_b", ["s5", "s6"])
        child_state = HealthState(agent_id=child.agent_id, health=90.0, health_max=100.0, status="active")
        grandchild = team_manager.mate("cx5", child.agent_id, health_state=child_state, partner_agent_id="gen1_b")
        assert grandchild.metadata["lineage"]["generation"] == 2
