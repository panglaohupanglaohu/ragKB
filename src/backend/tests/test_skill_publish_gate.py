"""Skill publish quality gate regressions (pass_rate / twin gain / samples)."""

from __future__ import annotations

from agents import evidence_store as evidence_store_module
from agents.evidence_store import EvidenceRun, EvidenceStore
from agents.models import SkillDefinition, SkillLifecycleStage
from agents.skill_library import SkillLibrary
from agents.skill_publish_gate import evaluate_publish_gate, gate_thresholds


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


def _make_skill(**kwargs) -> SkillDefinition:
    base = dict(
        skill_id="skill-cost-runbook",
        name="Cost Runbook",
        description="Investigate cloud cost alerts",
        instructions="步骤: 检查成本异常，验证标签，输出修复计划。",
        source="distilled",
        lifecycle_stage=SkillLifecycleStage.VERIFIED,
        quality_score=0.9,
        origin_team_id="cloud_ops",
        usage_count=0,
    )
    base.update(kwargs)
    return SkillDefinition(**base)


def _library(skill, tmp_path, monkeypatch):
    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)
    team_manager = FakeTeamManager(FakeTeam(skill))
    library = SkillLibrary(team_manager=team_manager)
    monkeypatch.setattr(library, "_snapshot_path", lambda: tmp_path / "skill_versions.json")
    library._version_snapshots = {}
    return library, team_manager, evidence_store


def _append_evidence(
    evidence_store: EvidenceStore,
    tmp_path,
    *,
    status="verified",
    pass_rate=0.9,
    total_tests=5,
    twin_metrics=None,
    ready=True,
    exit_code=0,
):
    metrics = {
        "pass_rate": pass_rate,
        "passed": int(round(pass_rate * total_tests)),
        "failed": total_tests - int(round(pass_rate * total_tests)),
        "total_tests": total_tests,
    }
    if twin_metrics:
        metrics.update(twin_metrics)
    evidence = EvidenceRun.create(
        evidence_type="skill_verify",
        status=status,
        team_id="cloud_ops",
        skill_id="skill-cost-runbook",
        runtime={"mode": "lite", "ready": ready},
        command="sandbox.run_python artifact=verification_runner.py",
        exit_code=exit_code,
        artifact_dir=str(tmp_path / "artifact"),
        metrics_after=metrics,
        detail={"twin_ab": twin_metrics.get("twin_ab") if twin_metrics else {}},
    )
    evidence_store.append_evidence_sync(evidence)
    return evidence


def test_publish_blocks_without_verification_evidence(monkeypatch, tmp_path):
    skill = _make_skill()
    library, team_manager, _ = _library(skill, tmp_path, monkeypatch)

    result = library.publish("cloud_ops", "skill-cost-runbook")

    assert result["error"] == "publish_gate_blocked"
    assert result["gate"]["reason"] == "missing_verification_evidence"
    assert result["gate"].get("candidate_held") is True
    assert skill.visibility == "private"
    assert team_manager.persisted is False


def test_publish_allows_recent_verified_evidence(monkeypatch, tmp_path):
    skill = _make_skill()
    library, team_manager, evidence_store = _library(skill, tmp_path, monkeypatch)
    evidence = _append_evidence(evidence_store, tmp_path)

    result = library.publish("cloud_ops", "skill-cost-runbook")

    assert result["status"] == "published"
    assert result["gate"]["ok"] is True
    assert result["gate"]["latest_evidence"]["evidence_id"] == evidence.evidence_id
    assert result["rollback_target_version"] == 1
    assert result["version_snapshot"]["ok"] is True
    versions = library.list_versions("skill-cost-runbook")
    assert versions[0]["reason"] == "pre_production_publish"
    assert versions[0]["metadata"]["latest_evidence_id"] == evidence.evidence_id
    assert skill.visibility == "public"
    assert skill.lifecycle_stage == SkillLifecycleStage.PUBLISHED
    assert team_manager.persisted is True


def test_publish_blocks_low_pass_rate(monkeypatch, tmp_path):
    skill = _make_skill(quality_score=0.4)
    library, _, evidence_store = _library(skill, tmp_path, monkeypatch)
    _append_evidence(evidence_store, tmp_path, pass_rate=0.4, total_tests=5)

    result = library.publish("cloud_ops", "skill-cost-runbook")

    assert result["error"] == "publish_gate_blocked"
    assert result["gate"]["ok"] is False
    assert any(c["name"] == "pass_rate" and not c["passed"] for c in result["gate"]["checks"])
    assert skill.lifecycle_stage == SkillLifecycleStage.VERIFIED  # stays candidate-ish


def test_publish_blocks_insufficient_samples(monkeypatch, tmp_path):
    skill = _make_skill()
    library, _, evidence_store = _library(skill, tmp_path, monkeypatch)
    _append_evidence(evidence_store, tmp_path, pass_rate=1.0, total_tests=1)

    result = library.publish("cloud_ops", "skill-cost-runbook")

    assert result["error"] == "publish_gate_blocked"
    assert result["gate"]["reason"] == "insufficient_samples"
    assert any(c["name"] == "min_samples" and not c["passed"] for c in result["gate"]["checks"])


def test_publish_blocks_twin_gain_below_threshold(monkeypatch, tmp_path):
    skill = _make_skill()
    skill.config = {
        "last_verify": {
            "status": "verified",
            "pass_rate": 0.9,
            "passed": 4,
            "failed": 1,
            "twin_ab": {
                "status": "ok",
                "skipped": False,
                "passed": False,
                "target_gain": 0.02,
                "target_gain_pp": 2.0,
                "gain_threshold": 0.05,
            },
        }
    }
    library, _, evidence_store = _library(skill, tmp_path, monkeypatch)
    _append_evidence(
        evidence_store,
        tmp_path,
        twin_metrics={
            "twin_ran": True,
            "twin_skipped": False,
            "twin_status": "ok",
            "twin_passed": False,
            "twin_target_gain": 0.02,
            "twin_target_gain_pp": 2.0,
            "twin_gain_threshold": 0.05,
        },
    )

    result = library.publish("cloud_ops", "skill-cost-runbook")

    assert result["error"] == "publish_gate_blocked"
    assert result["gate"]["reason"] == "twin_ab_gain_below_threshold"
    assert any(c["name"] == "twin_ab_gain" and not c["passed"] for c in result["gate"]["checks"])


def test_publish_allows_when_twin_gain_ok(monkeypatch, tmp_path):
    skill = _make_skill()
    library, team_manager, evidence_store = _library(skill, tmp_path, monkeypatch)
    _append_evidence(
        evidence_store,
        tmp_path,
        twin_metrics={
            "twin_ran": True,
            "twin_skipped": False,
            "twin_status": "ok",
            "twin_passed": True,
            "twin_target_gain": 0.12,
            "twin_target_gain_pp": 12.0,
            "twin_gain_threshold": 0.05,
            "twin_n_seeds": 5,
        },
    )

    result = library.publish("cloud_ops", "skill-cost-runbook")

    assert result["status"] == "published"
    assert result["gate"]["ok"] is True
    assert any(c["name"] == "twin_ab_gain" and c["passed"] for c in result["gate"]["checks"])
    assert team_manager.persisted is True


def test_evaluate_publish_gate_pure_unit_no_evidence():
    skill = _make_skill(lifecycle_stage=SkillLifecycleStage.TEAM_LOCAL)
    gate = evaluate_publish_gate(skill, None)
    assert gate["ok"] is False
    assert gate["reason"] == "missing_verification_evidence"
    thr = gate_thresholds()
    assert thr["pass_rate_min"] == 0.70
    assert thr["min_samples"] == 3
    assert thr["twin_gain_min"] == 0.05
