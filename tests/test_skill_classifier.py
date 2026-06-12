# -*- coding: utf-8 -*-
"""全局 G-2 技能三类分类器测试 (G2-5)."""

import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

NOW = datetime(2026, 6, 12, tzinfo=timezone.utc)


def _skill(**kw):
    base = {"skill_id": "sk1", "name": "coding", "effectiveness": 0.7,
            "lifecycle_stage": "verified", "adopted_by": [], "origin_team_id": "teamA",
            "last_used_at": NOW.isoformat(), "usage_count": 20}
    base.update(kw)
    return base


# ── 即时分类 classify ───────────────────────────────────────

def test_exclusive_classification():
    from agents.skill_classifier import classify
    r = classify(_skill(), {"team_usage": {"teamA": 18, "teamB": 2}},
                 {"meets_rubric": True}, now=NOW)
    assert r["classification"] == "exclusive"
    assert any("90%" in x or "占比" in x for x in r["reasons"])


def test_exclusive_requires_rubric():
    from agents.skill_classifier import classify
    r = classify(_skill(), {"team_usage": {"teamA": 18, "teamB": 2}},
                 {"meets_rubric": False}, now=NOW)
    assert r["classification"] == "reserve"


def test_general_by_multi_team_adoption():
    from agents.skill_classifier import classify
    r = classify(_skill(adopted_by=["teamB", "teamC"]),
                 {"team_usage": {"teamA": 5, "teamB": 5, "teamC": 5}},
                 {"gate_ok": True}, now=NOW)
    assert r["classification"] == "general"


def test_general_by_multi_category_pass():
    from agents.skill_classifier import classify
    r = classify(_skill(), {"team_usage": {"teamA": 10}},
                 {"gate_ok": True,
                  "category_pass": {"customer_service": True, "incident": True}}, now=NOW)
    assert r["classification"] == "general"


def test_general_requires_gate():
    from agents.skill_classifier import classify
    r = classify(_skill(adopted_by=["teamB", "teamC"]),
                 {"team_usage": {"teamA": 5, "teamB": 5}},
                 {"gate_ok": False, "meets_rubric": False}, now=NOW)
    assert r["classification"] == "reserve"


def test_reserve_new_skill_default():
    from agents.skill_classifier import classify
    r = classify(_skill(usage_count=0), {"team_usage": {}}, {}, now=NOW)
    assert r["classification"] == "reserve"
    assert any("新技能" in x for x in r["reasons"])


def test_reserve_low_effectiveness():
    from agents.skill_classifier import classify
    r = classify(_skill(effectiveness=0.2), {"team_usage": {"teamA": 10}},
                 {"meets_rubric": True}, now=NOW)
    assert r["classification"] == "reserve"


def test_reserve_degraded_and_stale():
    from agents.skill_classifier import classify
    assert classify(_skill(lifecycle_stage="degraded"),
                    {"team_usage": {"teamA": 10}}, {}, now=NOW)["classification"] == "reserve"
    old = (NOW - timedelta(days=120)).isoformat()
    assert classify(_skill(last_used_at=old),
                    {"team_usage": {"teamA": 10}}, {}, now=NOW)["classification"] == "reserve"


# ── 防抖 classify_with_history ─────────────────────────────

def test_graduation_needs_two_streaks():
    from agents.skill_classifier import classify_with_history
    usage = {"team_usage": {"teamA": 18, "teamB": 2}}
    trial = {"meets_rubric": True}
    # 第一次达标: 不毕业，streak=1
    r1 = classify_with_history(None, _skill(), usage, trial, now=NOW)
    assert r1["classification"] == "reserve" and r1["streak"] == 1 and r1["event"] is None
    # 第二次连续达标: 毕业
    r2 = classify_with_history(r1, _skill(), usage, trial, now=NOW)
    assert r2["classification"] == "exclusive"
    assert r2["event"]["type"] == "graduate"


def test_demotion_has_grace_period():
    from agents.skill_classifier import classify_with_history
    prev = {"classification": "exclusive", "streak": 0, "grace": 0}
    bad_usage = {"team_usage": {"teamA": 10}}
    # 第一次不达标: 宽限，保持 exclusive
    r1 = classify_with_history(prev, _skill(effectiveness=0.2), bad_usage, {}, now=NOW)
    assert r1["classification"] == "exclusive" and r1["grace"] == 1
    # 第二次仍不达标: 降级，且建议进化
    r2 = classify_with_history(r1, _skill(effectiveness=0.2), bad_usage, {}, now=NOW)
    assert r2["classification"] == "reserve"
    assert r2["event"]["type"] == "demote"
    assert r2["event"]["suggest_evolution"] is True


def test_streak_resets_when_back_to_normal():
    from agents.skill_classifier import classify_with_history
    usage_good = {"team_usage": {"teamA": 18, "teamB": 2}}
    r1 = classify_with_history(None, _skill(), usage_good, {"meets_rubric": True}, now=NOW)
    assert r1["streak"] == 1
    # 中断（回到 reserve 即时分类）→ streak 清零
    r2 = classify_with_history(r1, _skill(usage_count=0), {"team_usage": {}}, {}, now=NOW)
    assert r2["streak"] == 0 and r2["classification"] == "reserve"


# ── 批量重算 + 持久化 ───────────────────────────────────────

def test_reclassify_team_pools_and_events():
    from agents.skill_classifier import ClassificationStore
    with tempfile.TemporaryDirectory() as tmp:
        store = ClassificationStore(store_dir=Path(tmp))
        skills = [
            _skill(skill_id="s_good", name="good_skill"),
            _skill(skill_id="s_new", name="new_skill", usage_count=0),
            _skill(skill_id="s_weak", name="weak_skill", effectiveness=0.1),
        ]

        def ev(skill):
            if skill["skill_id"] == "s_good":
                return ({"team_usage": {"teamA": 18, "teamB": 2}}, {"meets_rubric": True})
            if skill["skill_id"] == "s_weak":
                return ({"team_usage": {"teamA": 10}}, {})
            return ({"team_usage": {}}, {})

        # 周期1: 全部 reserve（毕业需 2 连击）
        r1 = store.reclassify_team("teamA", skills, evidence_fn=ev, now=NOW)
        assert r1["pools"]["reserve"] == 3 and not r1["changes"]
        # 周期2: s_good 毕业为 exclusive
        r2 = store.reclassify_team("teamA", skills, evidence_fn=ev, now=NOW)
        assert r2["pools"]["exclusive"] == 1
        assert r2["changes"][0]["type"] == "graduate"
        assert r2["changes"][0]["skill_id"] == "s_good"
        # 视图与历史
        view = store.get_view("teamA")
        assert len(view["pools"]["exclusive"]) == 1
        hist = store.get_history("teamA", "s_good")
        assert hist and hist[0]["type"] == "graduate"
        # 持久化重载
        store2 = ClassificationStore(store_dir=Path(tmp))
        assert len(store2.get_view("teamA")["pools"]["exclusive"]) == 1


def test_skill_classifier_routes_smoke():
    fastapi = __import__("pytest").importorskip("fastapi")
    from fastapi.testclient import TestClient
    from agents.skill_classifier import reset_classification_store
    from agents.skill_classifier_routes import router

    with tempfile.TemporaryDirectory() as tmp:
        reset_classification_store(store_dir=Path(tmp))
        app = fastapi.FastAPI()
        app.include_router(router)
        client = TestClient(app)

        view = client.get("/api/v1/skill-classification/teams/teamA")
        assert view.status_code == 200
        assert set(view.json()["pools"]) == {"exclusive", "general", "reserve"}
        assert client.post("/api/v1/skill-classification/teams/teamA/reclassify").status_code == 200
        assert client.get("/api/v1/skill-classification/teams/teamA/history").status_code == 200


def test_seed_reserve_from_extraction_idempotent():
    from agents.skill_classifier import ClassificationStore
    with tempfile.TemporaryDirectory() as tmp:
        store = ClassificationStore(store_dir=Path(tmp))
        skill = {"skill_id": "sk_seed", "name": "seeded_skill", "effectiveness": 0.33}

        first = store.seed_reserve_from_extraction("teamA", skill, source="unit_test", now=NOW)
        assert first["created"] is True

        view = store.get_view("teamA")
        reserve_ids = {s["skill_id"] for s in view["pools"]["reserve"]}
        assert "sk_seed" in reserve_ids

        hist = store.get_history("teamA", "sk_seed")
        assert hist and hist[-1]["type"] == "seed_reserve"

        second = store.seed_reserve_from_extraction("teamA", skill, source="unit_test", now=NOW)
        assert second["created"] is False
