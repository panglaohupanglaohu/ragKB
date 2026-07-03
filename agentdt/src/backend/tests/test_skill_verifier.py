"""SkillVerifier sandbox evidence regressions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.models import SkillDefinition, SkillLifecycleStage
from agents import skill_verifier as skill_verifier_module
from agents import evidence_store as evidence_store_module
from agents.evidence_store import EvidenceStore
from agents.skill_verifier import SkillVerifier
from sandbox.python_runner_lite import LiteSandbox, SandboxResult
import sandbox.python_runner as sandbox_runner


class FakeSkillLibrary:
    def __init__(self, skill: SkillDefinition | None):
        self.skill = skill
        self.persisted = False

    def _find_skill(self, team_id: str, skill_id: str):
        if self.skill and self.skill.skill_id == skill_id:
            return self.skill
        return None

    def _persist_skill(self, skill: SkillDefinition, team_id: str) -> None:
        self.persisted = True
        self.skill = skill


def _runtime_payload(mode: str = "lite", ready: bool = True) -> dict:
    return {
        "mode": mode,
        "ready": ready,
        "ready_reason": "lite sandbox active" if ready else "docker executable missing",
        "docker_image": "agentsgroup-sandbox:python3.11",
        "docker_available": ready and mode == "docker",
        "image_available": ready and mode == "docker",
        "self_check_blocked": not ready,
    }


@pytest.mark.asyncio
async def test_verify_skill_runs_lite_sandbox_and_persists_evidence(monkeypatch, tmp_path):
    skill = SkillDefinition(
        skill_id="skill-runbook",
        name="Incident Runbook",
        description="Handle cloud incident triage",
        instructions="步骤: 读取告警输入，检查影响范围，验证恢复条件，输出处理建议和回滚步骤。",
    )
    library = FakeSkillLibrary(skill)
    monkeypatch.setattr(skill_verifier_module, "_ARTIFACT_ROOT", tmp_path)
    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)
    monkeypatch.setattr(sandbox_runner, "describe_sandbox_runtime", lambda: _runtime_payload("lite", True))
    monkeypatch.setattr(sandbox_runner, "get_sandbox", lambda: LiteSandbox())

    result = await SkillVerifier(skill_library=library).verify_skill("cloud_ops", "skill-runbook")

    assert result.status == "verified"
    assert result.runtime_mode == "lite"
    assert result.runtime_ready is True
    assert result.exit_code == 0
    assert result.command.startswith("sandbox.run_python")
    assert result.artifact_dir
    assert result.evidence_run_id.startswith("EV-")
    assert result.verification_evidence["sandbox_ok"] is True
    assert result.verification_evidence["evidence_run_id"] == result.evidence_run_id
    assert result.verification_evidence["runtime"]["mode"] == "lite"
    assert result.total_tests >= 4
    assert result.pass_rate >= 0.7
    assert library.persisted is True
    assert skill.lifecycle_stage == SkillLifecycleStage.VERIFIED

    artifact_dir = Path(result.artifact_dir)
    assert (artifact_dir / "verification_runner.py").exists()
    evidence_path = artifact_dir / "verification_result.json"
    assert evidence_path.exists()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["command"].startswith("sandbox.run_python")
    assert evidence["checks"]

    stored_evidence = await evidence_store.get_evidence(result.evidence_run_id)
    assert stored_evidence is not None
    assert stored_evidence.evidence_type == "skill_verify"
    assert stored_evidence.status == "verified"
    assert stored_evidence.team_id == "cloud_ops"
    assert stored_evidence.skill_id == "skill-runbook"
    assert stored_evidence.runtime["mode"] == "lite"
    assert stored_evidence.command.startswith("sandbox.run_python")
    assert stored_evidence.metrics_after["pass_rate"] >= 0.7


@pytest.mark.asyncio
async def test_verify_skill_reports_blocked_docker_runtime_without_false_success(monkeypatch, tmp_path):
    skill = SkillDefinition(
        skill_id="skill-docker",
        name="Docker Required Skill",
        description="Requires runtime verification",
        instructions="步骤: 输入配置，执行验证，输出结果。",
    )
    library = FakeSkillLibrary(skill)

    class BlockedSandbox:
        def run_python(self, code: str, *, cwd: Path, timeout: int = 30) -> SandboxResult:
            return SandboxResult(ok=False, exit_code=-1, error="docker executable not found")

    monkeypatch.setattr(skill_verifier_module, "_ARTIFACT_ROOT", tmp_path)
    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)
    monkeypatch.setattr(sandbox_runner, "describe_sandbox_runtime", lambda: _runtime_payload("docker", False))
    monkeypatch.setattr(sandbox_runner, "get_sandbox", lambda: BlockedSandbox())

    result = await SkillVerifier(skill_library=library).verify_skill("cloud_ops", "skill-docker")

    assert result.status == "failed"
    assert result.runtime_mode == "docker"
    assert result.runtime_ready is False
    assert result.verification_evidence["runtime"]["self_check_blocked"] is True
    assert result.verification_evidence["sandbox_ok"] is False
    assert "docker executable not found" in result.error_detail
    assert library.persisted is False

    stored_evidence = await evidence_store.get_evidence(result.evidence_run_id)
    assert stored_evidence is not None
    assert stored_evidence.status == "failed"
    assert stored_evidence.runtime["mode"] == "docker"
    assert stored_evidence.runtime["ready"] is False
    assert stored_evidence.detail["sandbox_ok"] is False
