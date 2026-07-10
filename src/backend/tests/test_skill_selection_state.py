# -*- coding: utf-8 -*-
"""Skill dominant/deprecated 选择状态机测试.

对应 docs/Agent仿生生态运行时todos.md P4-2。
"""

from __future__ import annotations

from agents.models import SkillDefinition, SkillLifecycleStage
from agents.skill_library import SkillLibrary


class FakeTeam:
    def __init__(self, skill: SkillDefinition) -> None:
        self.team_id = "eco_team"
        self.name = "Eco Team"
        self.skills = {skill.skill_id: skill}


class FakeTeamManager:
    def __init__(self, team: FakeTeam) -> None:
        self.team = team
        self.persisted = False

    def get_team(self, team_id: str):
        return self.team if team_id == self.team.team_id else None

    def list_teams(self):
        return [self.team]

    def save(self) -> None:
        self.persisted = True

    def _persist(self) -> None:
        self.persisted = True


def _make_skill(skill_id: str = "skill-forage") -> SkillDefinition:
    return SkillDefinition(
        skill_id=skill_id,
        name="Forage Skill",
        description="觅食技能",
        instructions="按代价函数选择最优任务",
        source="evolved",
        lifecycle_stage=SkillLifecycleStage.TEAM_LOCAL,
        origin_team_id="eco_team",
    )


class TestEvaluateSelectionState:
    def _library(self):
        return SkillLibrary(team_manager=None)  # 纯函数测试不需要真实 team_manager

    def test_dominant_when_consistently_positive_and_enough_total(self):
        library = self._library()
        # 12 次记录，最近 3 次为正，总次数达标 (>=10)
        history = [0.5] * 12
        state = library.evaluate_selection_state(
            "skill-1", "team-1", history, min_streak=3, dominant_usage_threshold=10
        )
        assert state == "dominant"

    def test_neutral_when_total_below_dominant_threshold(self):
        library = self._library()
        # 最近 3 次为正但总次数只有 5，未达 dominant_usage_threshold=10
        history = [0.5] * 5
        state = library.evaluate_selection_state(
            "skill-1", "team-1", history, min_streak=3, dominant_usage_threshold=10
        )
        assert state == "neutral"

    def test_deprecated_when_consistently_negative(self):
        library = self._library()
        history = [-0.3, -0.2, -0.5, -0.1]
        state = library.evaluate_selection_state("skill-1", "team-1", history, min_streak=3)
        assert state == "deprecated"

    def test_neutral_when_history_too_short(self):
        library = self._library()
        history = [0.5, 0.5]  # 少于 min_streak=3
        state = library.evaluate_selection_state("skill-1", "team-1", history, min_streak=3)
        assert state == "neutral"

    def test_neutral_when_mixed_signal_no_false_positive(self):
        """防误杀：不因单次波动跳变——最近 min_streak 内有一次异号即判 neutral."""
        library = self._library()
        history = [0.5, 0.5, -0.1]  # 最近3次有一次为负，不该判 dominant
        state = library.evaluate_selection_state(
            "skill-1", "team-1", history, min_streak=3, dominant_usage_threshold=1
        )
        assert state == "neutral"

    def test_single_bad_datapoint_does_not_deprecate(self):
        """单次失败不淘汰：混合信号应为 neutral，不是 deprecated."""
        library = self._library()
        history = [-0.5, 0.3, -0.2]  # 最近3次有正有负
        state = library.evaluate_selection_state("skill-1", "team-1", history, min_streak=3)
        assert state == "neutral"


class TestApplySelectionState:
    def test_dominant_calls_solidify_and_sets_solidified_stage(self):
        skill = _make_skill()
        team_manager = FakeTeamManager(FakeTeam(skill))
        library = SkillLibrary(team_manager=team_manager)
        library._version_snapshots = {}
        # 避免真实文件写入
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            library._snapshot_path = lambda: Path(tmpdir) / "skill_versions.json"

            result = library.apply_selection_state("eco_team", skill.skill_id, "dominant")
            assert result["status"] == "solidified"
            assert skill.lifecycle_stage == SkillLifecycleStage.SOLIDIFIED

    def test_deprecated_sets_degraded_stage(self):
        skill = _make_skill()
        team_manager = FakeTeamManager(FakeTeam(skill))
        library = SkillLibrary(team_manager=team_manager)

        result = library.apply_selection_state("eco_team", skill.skill_id, "deprecated")
        assert result["status"] == "deprecated"
        assert skill.lifecycle_stage == SkillLifecycleStage.DEGRADED

    def test_neutral_does_not_change_stage(self):
        skill = _make_skill()
        original_stage = skill.lifecycle_stage
        team_manager = FakeTeamManager(FakeTeam(skill))
        library = SkillLibrary(team_manager=team_manager)

        result = library.apply_selection_state("eco_team", skill.skill_id, "neutral")
        assert result["status"] == "neutral"
        assert skill.lifecycle_stage == original_stage

    def test_deprecated_unknown_skill_returns_error(self):
        skill = _make_skill()
        team_manager = FakeTeamManager(FakeTeam(skill))
        library = SkillLibrary(team_manager=team_manager)

        result = library.apply_selection_state("eco_team", "ghost-skill", "deprecated")
        assert "error" in result

    def test_deprecated_is_reversible_via_existing_evolve_reset(self):
        """软淘汰可恢复：DEGRADED 不是硬删除，skill_evolver.apply_evolution 已有
        的 TEAM_LOCAL 重置路径（既有代码）依然可以把技能拉回来，这里只验证
        DEGRADED 状态本身不影响 skill 对象的存在性（未被从库中移除）。"""
        skill = _make_skill()
        team_manager = FakeTeamManager(FakeTeam(skill))
        library = SkillLibrary(team_manager=team_manager)

        library.apply_selection_state("eco_team", skill.skill_id, "deprecated")
        assert skill.skill_id in team_manager.team.skills  # 仍在库中，未被删除
        assert skill.lifecycle_stage == SkillLifecycleStage.DEGRADED
