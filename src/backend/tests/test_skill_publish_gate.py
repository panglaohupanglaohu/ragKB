"""Skill publish quality gate regressions."""

from __future__ import annotations

from agents import evidence_store as evidence_store_module
from agents.evidence_store import EvidenceRun, EvidenceStore
from agents.models import SkillDefinition, SkillLifecycleStage
from agents.skill_library import SkillLibrary


class FakeTeam:
    def __init__(self, skill: SkillDefinition) -> None:
        self.team_id = "cloud_ops"
        self.name = "Cloud Ops"
        self.skills = {skill.skill_id: skill}


class FakeTeamManager:
    def __init__(self, team: FakeTeam) -> None:
        self.team = team
        self.persisted = False

    def get_team(self, team_id: str):
        return self.team if team_id == self.team.team_id else None

    def list_teams(self):
        return [self.team]

    def _persist(self) -> None:
        self.persisted = True


def _make_skill() -> SkillDefinition:
    return SkillDefinition(
        skill_id="skill-cost-runbook",
        name="Cost Runbook",
        description="Investigate cloud cost alerts",
        instructions="步骤: 检查成本异常，验证标签，输出修复计划。",
        source="distilled",
        lifecycle_stage=SkillLifecycleStage.VERIFIED,
        quality_score=0.9,
        origin_team_id="cloud_ops",
    )


def test_publish_blocks_without_verification_evidence(monkeypatch, tmp_path):
    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)
    skill = _make_skill()
    team_manager = FakeTeamManager(FakeTeam(skill))
    library = SkillLibrary(team_manager=team_manager)

    result = library.publish("cloud_ops", "skill-cost-runbook")

    assert result["error"] == "publish_gate_blocked"
    assert result["gate"]["reason"] == "missing_verification_evidence"
    assert skill.visibility == "private"
    assert team_manager.persisted is False


def test_publish_allows_recent_verified_evidence(monkeypatch, tmp_path):
    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)
    skill = _make_skill()
    team_manager = FakeTeamManager(FakeTeam(skill))
    library = SkillLibrary(team_manager=team_manager)
    evidence = EvidenceRun.create(
        evidence_type="skill_verify",
        status="verified",
        team_id="cloud_ops",
        skill_id="skill-cost-runbook",
        runtime={"mode": "lite", "ready": True},
        command="sandbox.run_python artifact=verification_runner.py",
        exit_code=0,
        artifact_dir=str(tmp_path / "artifact"),
        metrics_after={"pass_rate": 0.9},
    )
    evidence_store.append_evidence_sync(evidence)

    result = library.publish("cloud_ops", "skill-cost-runbook")

    assert result["status"] == "published"
    assert result["gate"]["ok"] is True
    assert result["gate"]["latest_evidence"]["evidence_id"] == evidence.evidence_id
    assert skill.visibility == "public"
    assert skill.lifecycle_stage == SkillLifecycleStage.PUBLISHED
    assert team_manager.persisted is True
