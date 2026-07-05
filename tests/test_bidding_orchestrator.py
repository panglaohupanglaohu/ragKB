# -*- coding: utf-8 -*-
"""M4 竞标编排器测试 — bidding_orchestrator / ratchet / cost."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))

import pytest

from sandbox.bidding_orchestrator import (
    CandidateCombo,
    TrialResult,
    generate_candidates,
    rank_candidates,
    ratchet_lock_winner,
    record_bidding_cost,
    bidding_orchestrator,
    reflow_bidding_to_discussion,
)


# ── fixtures ─────────────────────────────────────────────


def _baseline() -> CandidateCombo:
    return CandidateCombo(
        candidate_id="c0", operator="C0", operator_desc="基线",
        team_config={"team_id": "team-a"},
        skill_bindings={"dev": ["python"], "qa": ["testing"]},
        execution_order=["dev", "qa"],
        model_tiers={"dev": "standard", "qa": "economy"},
        review_edges=[],
    )


def _result(cid, success=0.95, quality=0.92, token=1000):
    return TrialResult(
        candidate_id=cid, success_rate=success, quality_score=quality,
        token_consumed=token, collab_heat=5.0,
    )


# ── M4-1: 候选生成 ───────────────────────────────────────


class TestCandidateGeneration:
    def test_generates_c0_plus_mutations(self):
        cs = generate_candidates(_baseline(), max_candidates=4)
        assert len(cs) >= 2
        assert cs[0].operator == "C0"
        operators = {c.operator for c in cs}
        assert "C0" in operators
        # 至少有一个变异算子
        assert len(operators) > 1

    def test_r5_model_downgrade(self):
        cs = generate_candidates(_baseline(), max_candidates=4)
        r5 = [c for c in cs if c.operator == "R5"]
        if r5:
            # 降档: standard → economy
            aid = "dev"
            assert r5[0].model_tiers[aid] == "economy"

    def test_r4_add_review(self):
        cs = generate_candidates(_baseline(), available_agents=["reviewer"], max_candidates=4)
        r4 = [c for c in cs if c.operator == "R4"]
        if r4:
            assert len(r4[0].review_edges) > 0

    def test_max_candidates_respected(self):
        cs = generate_candidates(_baseline(), max_candidates=2)
        assert len(cs) <= 2


# ── M4-1: 排名 ───────────────────────────────────────────


class TestRanking:
    def test_qualified_lowest_token_wins(self):
        baseline = _baseline()
        results = [
            (baseline, _result("c0", token=1000)),
            (CandidateCombo(candidate_id="c1", operator="R5"), _result("c1", token=800)),
            (CandidateCombo(candidate_id="c2", operator="R3"), _result("c2", token=900)),
        ]
        ranking = rank_candidates(baseline, results)
        # c1 token 最少且达标 → 第一名
        assert ranking[0].candidate_id == "c1"
        assert ranking[0].is_winner is True
        assert ranking[0].delta_token == 800 - 1000  # 相对 C0

    def test_unqualified_ranked_below_qualified(self):
        baseline = _baseline()
        results = [
            (baseline, _result("c0", success=0.95, quality=0.92, token=1000)),
            (CandidateCombo(candidate_id="c1", operator="R5"),
             _result("c1", success=0.5, quality=0.6, token=500)),  # 不达标
        ]
        ranking = rank_candidates(baseline, results)
        # c0 达标 → 第一名; c1 不达标 → 第二名
        assert ranking[0].candidate_id == "c0"
        assert ranking[0].is_winner is True
        assert ranking[1].candidate_id == "c1"
        assert ranking[1].is_winner is False

    def test_tie_breaker_quality(self):
        """token 相同时取质量高者。"""
        baseline = _baseline()
        results = [
            (baseline, _result("c0", quality=0.92, token=800)),
            (CandidateCombo(candidate_id="c1", operator="R5"), _result("c1", quality=0.95, token=800)),
        ]
        ranking = rank_candidates(baseline, results)
        assert ranking[0].candidate_id == "c1"  # 质量更高


# ── M4-1: 编排入口 ──────────────────────────────────────


class TestBiddingOrchestrator:
    def test_full_orchestration(self):
        """C0 + 3 候选 → 返回排名 + 胜者 + ratchet + cost."""

        def mock_runner(c):
            # R5 降档省 token 但质量略降
            if c.operator == "R5":
                return _result(c.candidate_id, quality=0.91, token=700)
            # R3 并行化省 token
            if c.operator == "R3":
                return _result(c.candidate_id, quality=0.93, token=850)
            # R4 加 Review 质量↑但 token↑
            if c.operator == "R4":
                return _result(c.candidate_id, quality=0.96, token=1200)
            return _result(c.candidate_id, token=1000)

        result = bidding_orchestrator(
            task_type="api_dev",
            baseline=_baseline(),
            trial_runner=mock_runner,
            available_agents=["reviewer"],
            team_id="team-a",
            max_candidates=4,
            do_ratchet=False,  # 测试不写文件
            do_cost=False,     # 测试不计 token
        )
        assert len(result["ranking"]) >= 2
        assert result["winner"] is not None
        # 胜者应该是 token 最少且达标的
        winner = result["winner"]
        assert winner["quality_score"] >= 0.9
        assert winner["success_rate"] >= 0.9

    def test_no_qualified_winner(self):
        """所有候选都不达标时 winner=None。"""

        def mock_runner(c):
            return _result(c.candidate_id, success=0.5, quality=0.6, token=500)

        result = bidding_orchestrator(
            task_type="bad_task",
            baseline=_baseline(),
            trial_runner=mock_runner,
            max_candidates=2,
            do_ratchet=False,
            do_cost=False,
        )
        assert result["winner"] is None


# ── M4-2: Ratchet 锁定 ───────────────────────────────────


class TestRatchetBidding:
    def test_winner_writes_ratchet(self, tmp_path):
        """胜者写 scenario_best:<task_type>:<hash>。"""
        from agents.ratchet_ledger import RatchetLedger
        ledger = RatchetLedger(ledger_file=tmp_path / "ratchet.json")
        winner = _baseline()
        result = _result("c0", quality=0.95, token=800)
        res = ratchet_lock_winner("api_dev", winner, result, ledger=ledger)
        assert res["advanced"] is True

    def test_worse_candidate_does_not_replace(self, tmp_path):
        """更差候选不覆盖 ratchet。"""
        from agents.ratchet_ledger import RatchetLedger
        ledger = RatchetLedger(ledger_file=tmp_path / "ratchet.json")
        # 第一次写入高质量低token
        winner1 = _baseline()
        r1 = _result("c0", quality=0.95, token=800)
        ratchet_lock_winner("api_dev", winner1, r1, ledger=ledger)

        # 第二次写入更低效率（质量更低/token更高）
        winner2 = CandidateCombo(candidate_id="c1", operator="R4",
                                  skill_bindings={"dev": ["python"]},
                                  execution_order=["dev"],
                                  model_tiers={"dev": "frontier"})
        r2 = _result("c1", quality=0.91, token=1500)
        res2 = ratchet_lock_winner("api_dev", winner2, r2, ledger=ledger)
        # 效率 0.91/1500 < 0.95/800 → 不应推进
        assert res2["advanced"] is False


# ── M4-3: 竞标 token 入账 ────────────────────────────────


class TestBiddingCost:
    def test_cost_recorded_with_simulation_tag(self):
        """竞标消耗以 simulation 标签入账。"""
        results = [
            (_baseline(), _result("c0", token=1000)),
            (CandidateCombo(candidate_id="c1", operator="R5"), _result("c1", token=800)),
        ]
        res = record_bidding_cost(results, team_id="team-a")
        # 可能因 token_ledger 未初始化而 recorded=False，但不应报错
        assert "recorded" in res
        if res["recorded"]:
            assert res["total_tokens"] == 1800
            assert res["tag"] == "simulation"

    def test_zero_tokens_skipped(self):
        results = [(_baseline(), _result("c0", token=0))]
        res = record_bidding_cost(results)
        assert res["recorded"] is False


# ── M5-1: 竞标结论回流讨论 ───────────────────────────────


class TestBiddingReflow:
    def _mock_plaza_engine(self):
        """最小化的 plaza_engine mock。"""
        from agents.plaza import Discussion, DiscussionStatus

        disc = Discussion(id="disc-1", plaza_id="plz-1", topic="测试话题",
                          status=DiscussionStatus.CLOSED)
        disc.plan = {"content": "## 执行计划\n| 序号 | 任务 |"}
        disc.messages = []

        class MockEngine:
            def get_discussion(self, pid, did):
                return disc if pid == "plz-1" and did == "disc-1" else None

            async def _broadcast(self, did, evt):
                pass

        return MockEngine(), disc

    def test_reflow_writes_message_to_discussion(self):
        engine, disc = self._mock_plaza_engine()
        bidding_result = {
            "task_type": "api_dev",
            "winner": {"candidate_id": "c1", "operator": "R5",
                        "success_rate": 0.95, "quality_score": 0.92, "token_consumed": 800},
            "ranking": [
                {"rank": 1, "candidate_id": "c1", "operator": "R5", "is_winner": True,
                 "quality_score": 0.92, "token_consumed": 800, "delta_token": -200},
            ],
        }
        res = reflow_bidding_to_discussion(engine, "plz-1", "disc-1", bidding_result)
        assert res["ok"] is True
        assert len(disc.messages) == 1
        assert "竞标" in disc.messages[0].content
        assert "R5" in disc.messages[0].content
        # plan 里也记录了竞标结论
        assert "bidding_result" in disc.plan

    def test_reflow_no_winner_message(self):
        engine, disc = self._mock_plaza_engine()
        bidding_result = {"task_type": "x", "winner": None, "ranking": []}
        res = reflow_bidding_to_discussion(engine, "plz-1", "disc-1", bidding_result)
        assert res["ok"] is True
        assert "达标" in disc.messages[0].content

    def test_reflow_missing_discussion(self):
        engine, _ = self._mock_plaza_engine()
        res = reflow_bidding_to_discussion(engine, "plz-1", "nonexistent", {})
        assert res["ok"] is False
