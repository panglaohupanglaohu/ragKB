"""Unified EvidenceRun storage regressions."""

from __future__ import annotations

import pytest

from agents.evidence_store import EvidenceQuery, EvidenceRun, EvidenceStore


@pytest.mark.asyncio
async def test_evidence_store_records_and_queries_by_object(tmp_path):
    store = EvidenceStore(str(tmp_path / "evidence_runs"))
    run = EvidenceRun.create(
        evidence_type="skill_verify",
        status="verified",
        summary="skill evidence",
        team_id="cloud_ops",
        skill_id="skill-001",
        runtime={"mode": "lite", "ready": True},
        command="sandbox.run_python artifact=verification_runner.py",
        exit_code=0,
        artifact_dir=str(tmp_path / "artifact"),
        metrics_after={"pass_rate": 1.0},
    )

    assert await store.append_evidence(run) is True

    loaded = await store.get_evidence(run.evidence_id)
    assert loaded is not None
    assert loaded.verify_integrity() is True
    assert loaded.evidence_type == "skill_verify"
    assert loaded.runtime["mode"] == "lite"

    by_skill = await store.query_evidence(EvidenceQuery(skill_id="skill-001"))
    assert [item.evidence_id for item in by_skill] == [run.evidence_id]

    by_object = await store.query_for_object("skill", "skill-001")
    assert [item.evidence_id for item in by_object] == [run.evidence_id]

    verification = await store.verify_all()
    assert verification["total"] == 1
    assert verification["corrupt"] == 0
