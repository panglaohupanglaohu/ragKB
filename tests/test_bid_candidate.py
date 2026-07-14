# -*- coding: utf-8 -*-
"""物竞 × 成本 BidCandidate（先适者后省钱）."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def _result():
    return {
        "final_ranking": [
            {
                "agent_id": "aws_mon",
                "survival_ticks": 80,
                "population": "aws-ops",
                "attr_skill_share": 0.2,
                "attr_collab_share": 0.15,
                "attr_residual_share": 0.65,
                "collab_genome": {"share_tendency": 0.8},
            }
        ],
        "contract": {
            "plan_id": "plan_x",
            "task_id": "task_demo",
            "topic": "ES 缩容",
            "niches": [{"index": 0, "title": "巡检", "demanded_skills": ["monitor"]}],
            "provenance": {"fingerprint": "fp_demo"},
        },
        "integration": {"dominant_skills": ["monitor"]},
        "survival_attribution": {
            "aws_mon": {"skill_share": 0.2, "collab_share": 0.15, "residual_share": 0.65},
        },
    }


def test_create_requires_task_and_feedback():
    from sandbox.bid_candidate import build_candidate_from_result, apply_quality_check

    doc = build_candidate_from_result(
        team_id="aws-ops",
        result=_result(),
        feedback={"feedback": "done", "skill_applied": True},
        task_id="task_demo",
    )
    assert doc["quality_status"] == "quality_passed"
    assert doc["best_T"] == 80
    assert doc["champion_agent_id"] == "aws_mon"

    r = _result()
    r["contract"] = {"plan_id": "p", "niches": [], "provenance": {}}
    bad = build_candidate_from_result(
        team_id="aws-ops",
        result=r,
        feedback={"feedback": "done"},
        task_id="",
    )
    bad = apply_quality_check(bad)
    assert bad["quality_status"] == "quality_failed"
    assert any("Q1" in r for r in bad["quality_reasons"])


def test_persist_list_and_lock():
    from sandbox.bid_candidate import (
        build_candidate_from_result,
        list_candidates,
        save_candidate,
        try_lock_candidate,
        patch_candidate,
    )

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        doc = build_candidate_from_result(
            team_id="aws-ops",
            result=_result(),
            feedback={"feedback": "done", "skill_applied": True, "fingerprint": "fp1"},
            task_id="task_demo",
        )
        save_candidate(doc, base=base)
        items = list_candidates(team_id="aws-ops", task_id="task_demo", base=base)
        assert len(items) == 1
        cid = items[0]["candidate_id"]

        # 无 token 也可 lock（quality_passed）
        locked = try_lock_candidate("aws-ops", cid, base=base)
        assert locked["ok"] is True
        assert locked["candidate"]["ratchet_state"] == "locked"

        # token 更差不可锁
        doc2 = build_candidate_from_result(
            team_id="aws-ops",
            result=_result(),
            feedback={"feedback": "done", "skill_applied": True},
            task_id="task_demo",
            candidate_id="bid_second",
        )
        save_candidate(doc2, base=base)
        patch_candidate(
            "aws-ops", "bid_second",
            {"tokens_baseline": 100, "tokens_candidate": 200},
            base=base,
        )
        fail = try_lock_candidate("aws-ops", "bid_second", base=base)
        assert fail["ok"] is False
        assert fail["error"] == "token_not_better"


def test_confirm_style_no_task_create_policy():
    """无 task 的文档 quality_failed（推送 API 层也会硬拒）."""
    from sandbox.bid_candidate import build_candidate_from_result, apply_quality_check

    r = _result()
    r["contract"] = {"plan_id": "p", "niches": []}
    doc = build_candidate_from_result(
        team_id="t",
        result=r,
        feedback={"feedback": "skipped", "reason": "test"},
        task_id="",
    )
    doc = apply_quality_check(doc)
    assert doc["quality_status"] == "quality_failed"


def test_production_config_from_locked():
    from sandbox.bid_candidate import (
        apply_locked_config_to_task,
        build_candidate_from_result,
        list_locked_candidates,
        resolve_production_config,
        save_candidate,
        try_lock_candidate,
    )

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        doc = build_candidate_from_result(
            team_id="aws-ops",
            result=_result(),
            feedback={"feedback": "done", "skill_applied": True},
            task_id="task_demo",
        )
        save_candidate(doc, base=base)
        cid = doc["candidate_id"]
        assert try_lock_candidate("aws-ops", cid, base=base)["ok"]

        locked = list_locked_candidates("aws-ops", task_id="task_demo", base=base)
        assert len(locked) == 1
        cfg = resolve_production_config("aws-ops", task_id="task_demo", base=base)
        assert cfg and cfg["bid_candidate_id"] == cid
        assert "monitor" in (cfg.get("required_skills") or [])

        out = apply_locked_config_to_task(
            "aws-ops",
            agent_id="",
            metadata={"task_id": "task_demo"},
            base=base,
            bind_skills=False,  # 无真 team_manager 时跳过 router
        )
        assert out["applied"] is True
        assert out["agent_id"] == "aws_mon"
        assert out["metadata"]["eco_bid_locked"] is True
        assert "monitor" in out["metadata"]["required_skills"]

        # skip flag
        skip = apply_locked_config_to_task(
            "aws-ops",
            metadata={"skip_locked_bid": True, "task_id": "task_demo"},
            base=base,
        )
        assert skip["applied"] is False


def test_bind_locked_skills_via_router_mock(monkeypatch):
    from sandbox import bid_candidate as bc

    class _FakeRouter:
        def assign(self, team_id, agent_id, skill_ids, session_id=""):
            assert team_id == "aws-ops"
            assert agent_id == "aws_mon"
            assert "monitor" in skill_ids
            return {
                "status": "ok",
                "assigned": ["monitor"],
                "assigned_count": 1,
                "already_has": [],
                "proficiency_boosted": {"monitor": 0.8},
                "agent_skills_count": 1,
            }

    monkeypatch.setattr(
        "agents.skill_router.get_skill_router",
        lambda: _FakeRouter(),
        raising=False,
    )
    # patch import path used inside function
    import agents.skill_router as sr
    monkeypatch.setattr(sr, "get_skill_router", lambda: _FakeRouter())

    out = bc.bind_locked_skills_via_router(
        "aws-ops", "aws_mon", ["monitor"], bid_candidate_id="bid_x",
    )
    assert out["ok"] is True
    assert out["assigned"] == ["monitor"]

    # apply_locked_config_to_task 会调 bind
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        doc = bc.build_candidate_from_result(
            team_id="aws-ops",
            result=_result(),
            feedback={"feedback": "done", "skill_applied": True},
            task_id="task_demo",
        )
        bc.save_candidate(doc, base=base)
        bc.try_lock_candidate("aws-ops", doc["candidate_id"], base=base)
        applied = bc.apply_locked_config_to_task(
            "aws-ops",
            metadata={"task_id": "task_demo"},
            base=base,
            bind_skills=True,
        )
        assert applied["applied"] is True
        assert applied["skill_bind"] and applied["skill_bind"].get("ok") is True
        assert applied["metadata"]["eco_bid_skill_bind"]["ok"] is True
