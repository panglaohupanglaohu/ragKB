# -*- coding: utf-8 -*-
"""全局 G-4 正向棘轮账本测试 (G4-5)."""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def _ledger(tmp):
    from agents.ratchet_ledger import RatchetLedger
    return RatchetLedger(ledger_file=Path(tmp) / "ledger.json")


def test_first_record_advances():
    with tempfile.TemporaryDirectory() as tmp:
        led = _ledger(tmp)
        r = led.advance("scenario_best:s1:teamA", 0.5)
        assert r["advanced"] and r["generation"] == 1 and r["reason"] == "first_record"


def test_improvement_advances_generation():
    with tempfile.TemporaryDirectory() as tmp:
        led = _ledger(tmp)
        led.advance("m", 0.5)
        r = led.advance("m", 0.6)
        assert r["advanced"] and r["generation"] == 2
        assert "0.5000 → 0.6000" in r["reason"]


def test_regression_rejected_with_reason():
    with tempfile.TemporaryDirectory() as tmp:
        led = _ledger(tmp)
        led.advance("m", 0.6)
        r = led.advance("m", 0.4)
        assert not r["advanced"]
        assert "regression" in r["reason"]
        assert led.get("m")["value"] == 0.6  # 当前值不被污染


def test_equal_value_advances_with_zero_min_delta():
    """min_delta=0 时持平可推进（默认宽松棘轮）."""
    with tempfile.TemporaryDirectory() as tmp:
        led = _ledger(tmp)
        led.advance("m", 0.5)
        r = led.advance("m", 0.5)
        assert r["advanced"] and r["generation"] == 2


def test_min_delta_blocks_marginal_gain():
    with tempfile.TemporaryDirectory() as tmp:
        led = _ledger(tmp)
        led.advance("m", 0.50)
        r = led.advance("m", 0.51, min_delta=0.05)
        assert not r["advanced"] and r.get("held")


def test_tolerance_holds_small_dip():
    """cost 类指标: 容忍区间内小幅回落 → held 而非 rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        led = _ledger(tmp)
        led.advance("cost_efficiency:teamA", 1.0)
        r = led.advance("cost_efficiency:teamA", 0.99, tolerance=0.02)
        assert not r["advanced"] and r.get("held")
        r2 = led.advance("cost_efficiency:teamA", 0.90, tolerance=0.02)
        assert not r2["advanced"] and not r2.get("held")
        assert "regression_rejected" in r2["reason"]


def test_force_reset_leaves_trace():
    with tempfile.TemporaryDirectory() as tmp:
        led = _ledger(tmp)
        led.advance("m", 0.8)
        r = led.force_reset("m", "场景 rubric 大改，历史分不可比")
        assert r["ok"] and r["previous_value"] == 0.8
        # 重置后可以从低值重新推进
        r2 = led.advance("m", 0.3)
        assert r2["advanced"]
        # 历史中留有重置痕迹
        hist = led.history("m")
        assert any(h.get("evidence", {}).get("force_reset") for h in hist)
        # 不存在的指标
        assert not led.force_reset("ghost", "x")["ok"]


def test_persistence_reload():
    with tempfile.TemporaryDirectory() as tmp:
        led = _ledger(tmp)
        led.advance("a", 0.5)
        led.advance("a", 0.7)
        led.advance("b", 0.3)
        led2 = _ledger(tmp)
        assert led2.get("a")["generation"] == 2
        assert led2.get("a")["value"] == 0.7
        assert len(led2.list_metrics()) == 2
        assert len(led2.list_metrics(prefix="a")) == 1
        assert len(led2.history("a")) == 2


def test_evolution_bridge_ratchet_gate_blocks_regression():
    """G4-3: skill_effectiveness 棘轮退步时阻断 apply_winner 写回（mock）."""
    from agents.ratchet_ledger import reset_ratchet_ledger
    from sandbox.models import EvolutionRun
    from sandbox.evolution_bridge import EvolutionBridge

    with tempfile.TemporaryDirectory() as tmp:
        ledger = reset_ratchet_ledger(ledger_file=Path(tmp) / "ledger.json")
        # 历史最佳 fitness=0.9
        ledger.advance("skill_effectiveness:coding:teamA", 0.9)

        class FakeSkill:
            skill_id = "sk-coding"; name = "coding"; slug = "coding"
            instructions = "x"; version = 1

        class FakeLib:
            def _find_skill(self, t, s): return FakeSkill() if s in ("coding", "sk-coding") else None
            def browse(self, team_id=""): return [{"skill_id": "sk-coding", "name": "coding"}]
            def create_version_snapshot(self, *a, **k): return {"ok": True, "version": 1}
            def evaluate_publish_gate(self, t, s): return {"ok": True}

        class FakeEvolver:
            def apply_evolution(self, t, s, i): return {"status": "evolved", "version": 2}

        bridge = EvolutionBridge(skill_library=FakeLib(), skill_evolver=FakeEvolver())
        run = EvolutionRun(team_id="teamA", scenario_id="scn")
        # 本次 fitness 0.6 < 历史 0.9 → 应被棘轮阻断
        run.winner = {"skill_name": "coding", "instructions": "new", "fitness": 0.6}
        result = bridge.apply_winner(run)
        assert not result["ok"]
        assert "ratchet_blocked" in result["error"]
        # fitness 0.95 > 0.9 → 放行
        run.winner = {"skill_name": "coding", "instructions": "new", "fitness": 0.95}
        result2 = bridge.apply_winner(run)
        assert result2["ok"], result2

        reset_ratchet_ledger()  # 还原单例，避免污染其他测试
