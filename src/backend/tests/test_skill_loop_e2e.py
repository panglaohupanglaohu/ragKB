"""P2-1 skill closed loop E2E (no live LLM):

extract-like skill create → verify evidence + last_verify → publish gate
→ library publish → skill router can route with lifecycle boost.
"""

from __future__ import annotations

from agents import evidence_store as evidence_store_module
from agents.evidence_store import EvidenceRun, EvidenceStore
from agents.models import SkillDefinition, SkillLifecycleStage
from agents.skill_library import SkillLibrary
from agents.skill_router import SkillRouter


class FakeAgent:
    def __init__(self, agent_id: str, name: str = "") -> None:
        self.agent_id = agent_id
        self.name = name or agent_id
        self.skills: list = []


class FakeTeam:
    def __init__(self, team_id: str, skills: dict) -> None:
        self.team_id = team_id
        self.name = team_id
        self.skills = skills
        self.agents = {"agent-1": FakeAgent("agent-1", "Ops Agent")}


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


def _distilled_skill() -> SkillDefinition:
    """Simulate skill_extractor approve → team skill (candidate)."""
    return SkillDefinition(
        skill_id="skill-es-autoscale",
        name="ES 集群自动扩缩容",
        description="根据负载自动扩缩 Elasticsearch 集群节点",
        instructions=(
            "1. 检查集群 CPU/JVM 水位\n"
            "2. 评估扩缩容条件与冷却时间\n"
            "3. 执行扩缩并验证健康检查\n"
            "4. 输出回滚点"
        ),
        source="distilled",
        lifecycle_stage=SkillLifecycleStage.TEAM_LOCAL,
        quality_score=0.0,
        visibility="private",
        origin_team_id="aws-ops",
        usage_count=0,
        config={"skill_type": "reserve"},
    )


def test_skill_loop_e2e_verify_gate_publish_route(monkeypatch, tmp_path):
    skill = _distilled_skill()
    team = FakeTeam("aws-ops", {skill.skill_id: skill})
    team_manager = FakeTeamManager(team)

    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)

    library = SkillLibrary(team_manager=team_manager)
    monkeypatch.setattr(library, "_snapshot_path", lambda: tmp_path / "skill_versions.json")
    library._version_snapshots = {}

    # ── Phase 0: candidate cannot publish ──
    blocked = library.publish("aws-ops", skill.skill_id)
    assert blocked["error"] == "publish_gate_blocked"
    assert blocked["gate"]["reason"] == "missing_verification_evidence"
    assert skill.lifecycle_stage == SkillLifecycleStage.TEAM_LOCAL
    assert skill.visibility == "private"

    # ── Phase 1: verifier-like evidence + last_verify (semantic+sandbox+twin) ──
    skill.lifecycle_stage = SkillLifecycleStage.VERIFIED
    skill.quality_score = 0.88
    skill.config = {
        **(skill.config or {}),
        "last_verify": {
            "status": "verified",
            "pass_rate": 0.9,
            "passed": 9,
            "failed": 1,
            "error_detail": "",
            "failed_checks": [],
            "twin_ab": {
                "status": "ok",
                "skipped": False,
                "passed": True,
                "target_gain": 0.11,
                "target_gain_pp": 11.0,
                "gain_threshold": 0.05,
                "n_seeds": 5,
            },
            "skill_version": 1,
        },
    }
    evidence = EvidenceRun.create(
        evidence_type="skill_verify",
        status="verified",
        team_id="aws-ops",
        skill_id=skill.skill_id,
        runtime={"mode": "lite", "ready": True},
        command="sandbox.run_python artifact=verification_runner.py",
        exit_code=0,
        artifact_dir=str(tmp_path / "artifact"),
        metrics_after={
            "pass_rate": 0.9,
            "passed": 9,
            "failed": 1,
            "total_tests": 10,
            "twin_ran": True,
            "twin_skipped": False,
            "twin_status": "ok",
            "twin_passed": True,
            "twin_target_gain": 0.11,
            "twin_target_gain_pp": 11.0,
            "twin_gain_threshold": 0.05,
            "twin_n_seeds": 5,
        },
        detail={
            "twin_ab": {
                "status": "ok",
                "skipped": False,
                "passed": True,
                "target_gain": 0.11,
                "target_gain_pp": 11.0,
                "gain_threshold": 0.05,
            }
        },
    )
    evidence_store.append_evidence_sync(evidence)

    # ── Phase 2: gate preview ok, then publish ──
    gate = library.evaluate_publish_gate("aws-ops", skill.skill_id)
    assert gate["ok"] is True
    assert gate.get("candidate_held") is False
    names = {c["name"]: c["passed"] for c in gate["checks"]}
    assert names.get("pass_rate") is True
    assert names.get("min_samples") is True
    assert names.get("twin_ab_gain") is True

    published = library.publish("aws-ops", skill.skill_id)
    assert published["status"] == "published"
    assert skill.lifecycle_stage == SkillLifecycleStage.PUBLISHED
    assert skill.visibility == "public"
    assert team_manager.persisted is True

    # ── Phase 3: router can retrieve published skill with lifecycle mult ──
    router = SkillRouter(skill_library=library, team_manager=team_manager)
    session = router.route(
        query="Elasticsearch 集群自动扩缩容 负载过高",
        team_id="aws-ops",
        agent_id="agent-1",
        top_k=5,
    )
    assert session.pool_size >= 1
    ids = [r.skill_id for r in session.results]
    assert skill.skill_id in ids
    hit = next(r for r in session.results if r.skill_id == skill.skill_id)
    assert hit.lifecycle_stage == "published"
    assert hit.lifecycle_mult >= 1.0


def test_skill_loop_e2e_holds_candidate_when_twin_fails(monkeypatch, tmp_path):
    skill = _distilled_skill()
    skill.lifecycle_stage = SkillLifecycleStage.VERIFIED
    skill.quality_score = 0.9
    team = FakeTeam("aws-ops", {skill.skill_id: skill})
    team_manager = FakeTeamManager(team)

    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)
    library = SkillLibrary(team_manager=team_manager)
    monkeypatch.setattr(library, "_snapshot_path", lambda: tmp_path / "skill_versions.json")
    library._version_snapshots = {}

    evidence_store.append_evidence_sync(
        EvidenceRun.create(
            evidence_type="skill_verify",
            status="verified",
            team_id="aws-ops",
            skill_id=skill.skill_id,
            runtime={"mode": "lite", "ready": True},
            command="x",
            exit_code=0,
            artifact_dir=str(tmp_path / "a"),
            metrics_after={
                "pass_rate": 0.95,
                "passed": 19,
                "failed": 1,
                "total_tests": 20,
                "twin_ran": True,
                "twin_status": "ok",
                "twin_passed": False,
                "twin_target_gain": 0.01,
                "twin_target_gain_pp": 1.0,
                "twin_gain_threshold": 0.05,
            },
        )
    )

    result = library.publish("aws-ops", skill.skill_id)
    assert result["error"] == "publish_gate_blocked"
    assert result["gate"]["reason"] == "twin_ab_gain_below_threshold"
    assert result["gate"]["candidate_held"] is True
    assert skill.visibility == "private"
    assert skill.lifecycle_stage == SkillLifecycleStage.VERIFIED
