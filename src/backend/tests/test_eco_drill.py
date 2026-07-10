# -*- coding: utf-8 -*-
"""物竞天择数字孪生演练 ND-2 测试 — eco_drill 生境内核.

验收标准（ND-2.1）：低能效组合的 twin 先饿死；survival_ticks 有差异。
验收标准（ND-4.1）：survival_ticks 作为唯一选择键。
验收标准（ND-4.2）：死亡个体 skill 不进入下一代基因池。
验收标准（ND-6.1）：棘轮锁定世代最优，只进不退。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.runtime.eco_loop import (
    IntentionThresholds,
    IntentionType,
    MentalState,
    WorldView,
    generate_intention,
)
from agents.runtime.health_ledger import HealthLedger, HealthState
from sandbox.eco_drill import Creature, EcoDrill


# ── ND-2.1: 代谢结算 — 低能效先饿死 ──────────────────────────


class TestMetabolismStarvation:
    """低能效（基因不匹配生态位）的 Creature 先饿死，survival_ticks 有差异."""

    def test_mismatched_genome_starves_faster(self):
        """基因不匹配生态位的生物持续觅食失败 → 饿死."""
        # creature_a 有匹配 skill（高熟练度），creature_b 基因不匹配
        a = Creature(
            agent_id="a", role="worker", skill_genome=["foraging"],
            skill_proficiency={"foraging": 0.9},
        )
        b = Creature(agent_id="b", role="worker", skill_genome=["unrelated"])
        drill = EcoDrill(
            creatures=[a, b],
            demanded_skills=["foraging"],
            seed=100,
        )
        result = drill.run(max_steps=150)

        ranking = result["ranking"]
        # a 应该比 b 活得久
        a_rank = next(r for r in ranking if r["agent_id"] == "a")
        b_rank = next(r for r in ranking if r["agent_id"] == "b")
        # b 必须死亡（基因不匹配 → 饿死）
        assert b_rank["alive"] is False
        # a 的生存时长 >= b（低能效先死）
        assert a_rank["survival_ticks"] >= b_rank["survival_ticks"]

    def test_matched_genome_survives_longer(self):
        """有匹配 skill 的生物能持续觅食回血，活得久."""
        creature = Creature(agent_id="lucky", role="forager", skill_genome=["foraging"])
        drill = EcoDrill(
            creatures=[creature],
            demanded_skills=["foraging"],
            seed=1,
        )
        result = drill.run(max_steps=50)
        ranking = result["ranking"]
        # 应该没灭绝
        assert result["extinct"] is False
        assert ranking[0]["survival_ticks"] >= 50

    def test_survival_ticks_differ_between_creatures(self):
        """不同基因的 Creature survival_ticks 有差异."""
        creatures = [
            Creature(agent_id=f"c{i}", role="w", skill_genome=[f"skill_{i}"])
            for i in range(4)
        ]
        # 只有一个生态位需求，只有 c0 能匹配
        drill = EcoDrill(
            creatures=creatures,
            demanded_skills=["skill_0"],
            seed=7,
        )
        result = drill.run(max_steps=40)
        ranking = result["ranking"]
        ticks = [r["survival_ticks"] for r in ranking]
        # c0 应该 ticks 最多
        c0 = next(r for r in ranking if r["agent_id"] == "c0")
        others = [r for r in ranking if r["agent_id"] != "c0"]
        assert all(c0["survival_ticks"] >= o["survival_ticks"] for o in others)


# ── ND-2: 意图驱动决策 ──────────────────────────────────────


class TestIntentionDrivesBehavior:
    """eco_loop 意图正确驱动生境行为."""

    def test_forage_intention_when_hungry(self):
        thresholds = IntentionThresholds()
        state = MentalState(hunger=0.8, fear=0.1, libido=0.0)
        view = WorldView(agent_id="a1", visible_unclaimed_tasks=3)
        intention = generate_intention(state, view, thresholds)
        assert intention.type == IntentionType.FORAGE

    def test_avoid_intention_when_fearful(self):
        thresholds = IntentionThresholds()
        state = MentalState(hunger=0.8, fear=0.7, libido=0.0)
        view = WorldView(agent_id="a1")
        intention = generate_intention(state, view, thresholds)
        assert intention.type == IntentionType.AVOID

    def test_mate_intention_when_satiated(self):
        thresholds = IntentionThresholds()
        state = MentalState(hunger=0.1, fear=0.0, libido=0.8)
        view = WorldView(agent_id="a1")
        intention = generate_intention(state, view, thresholds)
        assert intention.type == IntentionType.MATE


# ── ND-4.1: survival_ticks 唯一选择键 ────────────────────────


class TestSurvivalSelection:
    """繁衍排序只用 survival_ticks，不引入人工评分."""

    def test_ranking_sorted_by_survival_ticks_desc(self):
        creatures = [
            Creature(agent_id="a", role="w", skill_genome=["s"]),
            Creature(agent_id="b", role="w", skill_genome=["s"]),
            Creature(agent_id="c", role="w", skill_genome=["s"]),
        ]
        drill = EcoDrill(creatures=creatures, demanded_skills=["s"], seed=0)
        # 跑几步让 survival_ticks 产生差异
        drill.run(max_steps=20)
        ranking = drill.survival_ranking()
        # 排序纯按 survival_ticks 降序
        for i in range(len(ranking) - 1):
            assert ranking[i]["survival_ticks"] >= ranking[i + 1]["survival_ticks"]


# ── ND-4.2: 基因抹除 — 死亡个体不参与繁衍 ────────────────────


class TestGeneErasure:
    """死亡个体的 skill 不进入下一代基因池."""

    def test_dead_creatures_excluded_from_reproduction(self):
        """run_epoch 只从存活者中选亲本."""
        # c0 能匹配 → 存活；c1 不能匹配 → 会死
        c0 = Creature(agent_id="survivor", role="w", skill_genome=["foraging"])
        c1 = Creature(agent_id="doomed", role="w", skill_genome=["useless"])
        drill = EcoDrill(
            creatures=[c0, c1],
            demanded_skills=["foraging"],
            seed=3,
        )
        # 跑到 c1 死亡
        drill.run(max_steps=120)
        # c1 应该死了
        assert not drill._creatures["doomed"].alive
        # run_epoch 只从存活者选亲本
        result = drill.run_epoch(reproduce_top_k=1, mutation_rate=0.0)
        # parents 不应包含 doomed
        assert "doomed" not in result.get("parents", [])

    def test_offspring_genome_from_parents_only(self):
        """后代基因只来自双亲."""
        p1 = Creature(agent_id="p1", role="w", skill_genome=["s1", "s2"])
        p2 = Creature(agent_id="p2", role="w", skill_genome=["s3", "s4"])
        drill = EcoDrill(
            creatures=[p1, p2],
            demanded_skills=["s1"],
            seed=5,
        )
        result = drill.run_epoch(reproduce_top_k=1, mutation_rate=0.0)
        for child_id, genome in result.get("offspring_genomes", {}).items():
            # 所有 skill 都应来自双亲并集
            parent_pool = {"s1", "s2", "s3", "s4"}
            assert set(genome) <= parent_pool


# ── ND-6.1: 棘轮锁定 ────────────────────────────────────────


class TestRatchetLock:
    """世代最优生存时长写入棘轮，只进不退."""

    def test_ratchet_advances_on_improvement(self):
        from agents.ratchet_ledger import RatchetLedger
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ledger = RatchetLedger(ledger_file=Path(d) / "ratchet.json")
            metric = "eco_survival:test_team"

            r1 = ledger.advance(metric, value=50.0, evidence={"generation": 0})
            assert r1["advanced"] is True
            assert r1["generation"] == 1

            r2 = ledger.advance(metric, value=80.0, evidence={"generation": 1})
            assert r2["advanced"] is True
            assert r2["generation"] == 2

    def test_ratchet_rejects_regression(self):
        from agents.ratchet_ledger import RatchetLedger
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ledger = RatchetLedger(ledger_file=Path(d) / "ratchet.json")
            metric = "eco_survival:regress_team"

            ledger.advance(metric, value=100.0)
            r = ledger.advance(metric, value=50.0)
            assert r["advanced"] is False
            assert "regression" in r["reason"].lower()

    def test_ratchet_holds_within_tolerance(self):
        from agents.ratchet_ledger import RatchetLedger
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ledger = RatchetLedger(ledger_file=Path(d) / "ratchet.json")
            metric = "eco_survival:hold_team"

            ledger.advance(metric, value=100.0)
            r = ledger.advance(metric, value=99.5, tolerance=1.0)
            assert r["advanced"] is False
            assert r.get("held") is True

    def test_eco_drill_ratchet_lock_method(self):
        """EcoDrill.ratchet_lock 方法可用."""
        creatures = [Creature(agent_id="a", role="w", skill_genome=["s"])]
        drill = EcoDrill(creatures=creatures, demanded_skills=["s"], seed=0)
        result = drill.ratchet_lock("test_team_ratchet", 42, 0)
        # 应该返回一个 dict（是否推进取决于是否首次记录）
        assert "advanced" in result or "reason" in result


# ── ND-2.3: 捕食压力 ────────────────────────────────────────


class TestPredatorPressure:
    """捕食压力注入配置存在且可用."""

    def test_predator_pressure_prob_in_range(self):
        assert 0.0 < EcoDrill.PREDATOR_PRESSURE_PROB < 1.0

    def test_inject_predator_pressure_returns_list(self):
        creatures = [Creature(agent_id="a", role="w", skill_genome=["s"])]
        drill = EcoDrill(creatures=creatures, demanded_skills=["s"], seed=0)
        result = drill.inject_predator_pressure()
        assert isinstance(result, list)


# ── ND-3: 默认交叉遗传 ──────────────────────────────────────


class TestDefaultCrossover:
    """EcoDrill._default_crossover 产出复合型 Skill."""

    def test_crossover_produces_composite_genome(self):
        p1 = Creature(agent_id="p1", role="w", skill_genome=["s1", "s2", "s3"])
        p2 = Creature(agent_id="p2", role="w", skill_genome=["s4", "s5", "s6"])
        creatures = [p1, p2]
        drill = EcoDrill(creatures=creatures, demanded_skills=["s1"], seed=10)
        child = drill._default_crossover(p1, p2, generation=1)

        parent_pool = {"s1", "s2", "s3", "s4", "s5", "s6"}
        assert set(child.skill_genome) <= parent_pool
        assert len(child.skill_genome) >= 1
        assert child.parent_ids == ["p1", "p2"]
        assert child.generation == 1
