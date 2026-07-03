# -*- coding: utf-8 -*-
"""全局 G-5 Token 可持续性评估器测试 (G5-5)."""

import os
import sys
import asyncio

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def _usage(**kw):
    from agents.sustainability import TeamUsage
    base = dict(
        team_id="teamA",
        tokens_consumed=10000,
        trials=[{"trial_id": "t1", "scenario_id": "s1", "total_score": 0.7, "tokens": 5000},
                {"trial_id": "t2", "scenario_id": "s1", "total_score": 0.8, "tokens": 5000}],
        model_tier="standard", agent_count=3, scenario_role_demand=3,
        budget_tokens=50000,
    )
    base.update(kw)
    return TeamUsage.from_dict(base)


def test_efficiency_calculation():
    from agents.sustainability import evaluate_team
    r = evaluate_team(_usage())
    # 1.5 score / 10 (k tokens) = 0.15
    assert abs(r["token_efficiency"] - 0.15) < 1e-6
    assert r["data_quality"] == "measured"
    assert 0 <= r["sustainability_score"] <= 1
    assert r["grade"] in "ABCD"


def test_grade_boundaries():
    from agents.sustainability import evaluate_team
    # 高效 + 高余量 + 设定上升趋势 → A
    good = evaluate_team(_usage(
        tokens_consumed=2000, budget_tokens=100000, previous_efficiency=0.3,
        trials=[{"trial_id": "t", "scenario_id": "s", "total_score": 0.9, "tokens": 2000}]))
    assert good["grade"] in ("A", "B")
    # 极低效 + 超预算 → D
    bad = evaluate_team(_usage(
        tokens_consumed=100000, budget_tokens=100000, previous_efficiency=1.0,
        trials=[{"trial_id": "t", "scenario_id": "s", "total_score": 0.1, "tokens": 100000}]))
    assert bad["grade"] == "D"
    assert good["sustainability_score"] > bad["sustainability_score"]


def test_estimation_fallback_marks_quality():
    from agents.sustainability import evaluate_team
    r = evaluate_team(_usage(
        tokens_consumed=0,
        trials=[{"trial_id": "t", "scenario_id": "s", "total_score": 0.5, "steps": 100}]))
    assert r["data_quality"] == "estimated"
    assert r["tokens_consumed"] == 100 * 800  # STEP_TOKEN_ESTIMATE


def test_collect_team_usage_async_reads_cost_aggregator():
    pytest.importorskip("pydantic")  # cost_models 依赖 pydantic（离线沙箱无网络时跳过）
    import agents.cost_aggregator as cost_aggregator
    from agents.cost_models import PodCostItem
    from agents.sustainability import collect_team_usage_async, evaluate_team

    previous = cost_aggregator._aggregator
    try:
        agg = cost_aggregator.CostAggregator()
        agg._cache.update([
            PodCostItem(
                pod="worker-1",
                total_cost=12.5,
                labels={"team": "team_cost", "service": "trial-worker"},
            )
        ], window_start="7d", window_end="now")
        cost_aggregator._aggregator = agg

        usage = asyncio.run(collect_team_usage_async("team_cost"))
        result = evaluate_team(usage)

        assert usage.cost_usd == 12.5
        assert result["cost_usd"] == 12.5
        assert result["data_sources"]["cost_aggregator"] == "measured"
    finally:
        cost_aggregator._aggregator = previous


def test_recommendation_model_downgrade():
    from agents.sustainability import evaluate_team
    r = evaluate_team(_usage(
        model_tier="opus", tokens_consumed=100000,
        trials=[{"trial_id": "t", "scenario_id": "s", "total_score": 0.5, "tokens": 100000}]))
    assert any(x["type"] == "model_downgrade" and "sonnet" in x["detail"]
               for x in r["recommendations"])


def test_recommendation_team_downsize():
    from agents.sustainability import evaluate_team
    r = evaluate_team(_usage(agent_count=6, scenario_role_demand=4))
    assert any(x["type"] == "team_downsize" and "2 人" in x["detail"]
               for x in r["recommendations"])


def test_recommendation_reduce_drills_on_low_headroom():
    from agents.sustainability import evaluate_team
    r = evaluate_team(_usage(tokens_consumed=45000, budget_tokens=50000))
    assert any(x["type"] == "reduce_drills" for x in r["recommendations"])


def test_recommendation_skill_route_or_evolve():
    from agents.sustainability import evaluate_team
    r = evaluate_team(_usage(skill_stats=[
        {"skill_name": "kb_search", "total_uses": 20, "success_rate": 0.3},
        {"skill_name": "reply_writing", "total_uses": 20, "success_rate": 0.9},
    ]))
    recs = [x for x in r["recommendations"] if x["type"] == "skill_route_or_evolve"]
    assert len(recs) == 1 and "kb_search" in recs[0]["detail"]


def test_healthy_team_gets_healthy_recommendation():
    from agents.sustainability import evaluate_team
    r = evaluate_team(_usage(
        tokens_consumed=2000, budget_tokens=100000,
        trials=[{"trial_id": "t", "scenario_id": "s", "total_score": 0.9, "tokens": 2000}]))
    assert any(x["type"] == "healthy" for x in r["recommendations"])


def test_group_ranking_and_reallocation():
    from agents.sustainability import evaluate_group
    high = _usage(team_id="alpha", tokens_consumed=2000, budget_tokens=100000,
                  previous_efficiency=0.2,
                  trials=[{"trial_id": "t", "scenario_id": "s", "total_score": 0.9, "tokens": 2000}])
    low = _usage(team_id="omega", tokens_consumed=100000, budget_tokens=100000,
                 previous_efficiency=1.0,
                 trials=[{"trial_id": "t", "scenario_id": "s", "total_score": 0.05, "tokens": 100000}])
    g = evaluate_group([low, high])
    assert g["ranking"][0] == "alpha"
    assert g["reallocations"], "D 级团队应产生再分配建议"
    realloc = g["reallocations"][0]
    assert realloc["from_team"] == "omega" and realloc["to_team"] == "alpha"
    assert realloc["tokens"] == 20000  # 20% of 100k


def test_weekly_plaza_topics_endpoint_dry_run(monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from agents import sustainability_routes

    async def fake_team_ids():
        return ["omega"]

    async def fake_usage(team_id):
        return _usage(
            team_id=team_id,
            tokens_consumed=100000,
            budget_tokens=100000,
            previous_efficiency=1.0,
            trials=[{"trial_id": "t", "scenario_id": "s", "total_score": 0.05, "tokens": 100000}],
        )

    monkeypatch.setattr(sustainability_routes, "list_known_team_ids", fake_team_ids)
    monkeypatch.setattr(sustainability_routes, "collect_team_usage_async", fake_usage)

    app = fastapi.FastAPI()
    app.include_router(sustainability_routes.router)
    client = TestClient(app)

    r = client.post("/api/v1/sustainability/weekly-plaza-topics", json={"dry_run": True})
    assert r.status_code == 200
    data = r.json()
    assert data["dry_run"] is True
    assert data["topics"]
    assert "omega" in data["topics"][0]["topic"]


def test_e2e_mock_chain_trial_to_sustainability():
    """GE-2: 评分→棘轮→分类→可持续 全链路 mock 串联."""
    import tempfile
    from pathlib import Path
    from agents.ratchet_ledger import RatchetLedger
    from agents.skill_classifier import ClassificationStore
    from agents.sustainability import evaluate_team

    with tempfile.TemporaryDirectory() as tmp:
        # 1) trial 评分 0.72 → 棘轮推进
        ledger = RatchetLedger(ledger_file=Path(tmp) / "ledger.json")
        r1 = ledger.advance("scenario_best:cs_ticket_surge:teamA", 0.72,
                            evidence={"trial_id": "t1"})
        assert r1["advanced"]

        # 2) 演练证据驱动分类: 技能毕业为特有
        store = ClassificationStore(store_dir=Path(tmp) / "cls")
        skill = {"skill_id": "sk1", "name": "reply_writing", "effectiveness": 0.75,
                 "lifecycle_stage": "verified", "adopted_by": [],
                 "origin_team_id": "teamA", "last_used_at": "2026-06-12T00:00:00+00:00",
                 "usage_count": 30}
        ev = lambda s: ({"team_usage": {"teamA": 30}}, {"meets_rubric": True})  # noqa: E731
        store.reclassify_team("teamA", [skill], evidence_fn=ev)
        result = store.reclassify_team("teamA", [skill], evidence_fn=ev)
        assert result["pools"]["exclusive"] == 1

        # 3) 可持续评估给出建议 + 推进 cost 棘轮
        sus = evaluate_team(_usage(trials=[
            {"trial_id": "t1", "scenario_id": "cs_ticket_surge",
             "total_score": 0.72, "tokens": 10000}]))
        assert sus["recommendations"]
        r2 = ledger.advance("cost_efficiency:teamA", sus["token_efficiency"])
        assert r2["advanced"] and r2["generation"] == 1
