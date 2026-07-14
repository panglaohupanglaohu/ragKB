# -*- coding: utf-8 -*-
"""Eco Drill 生境引擎测试 (Claude 侧, EcoDrill/Creature) — 与 CodeBuddy 的 test_eco_drill.py 并存.

覆盖: 代谢红线致死 + 生存时长适应度 + 世代繁衍(skill 交叉) + 基因抹除。
（CodeBuddy 的 test_eco_drill.py 覆盖 EcoTwinState/意图偏置/棘轮/捕食压力常量，两者互补。）
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agents.runtime.health_ledger import HealthLedger
from sandbox.eco_drill import Creature, EcoDrill, EcoTwinState, _INTENTION_STRATEGY_BIAS, _PREDATOR_PRESSURE_PROB


def _ledger():
    return HealthLedger(team_id="t", ledger_dir=Path(tempfile.mkdtemp()))


class TestMetabolicRedLine:
    def test_mismatched_genome_starves_first(self):
        fit = Creature(agent_id="fit", skill_genome=["coding"], skill_proficiency={"coding": 0.9})
        unfit = Creature(agent_id="unfit", skill_genome=["painting"], skill_proficiency={"painting": 0.9})
        drill = EcoDrill([fit, unfit], demanded_skills=["coding"],
                         health_max=20.0, metabolic_rate=1.0, seed=42, ledger=_ledger())
        drill.run(max_steps=200)
        ranking = {r["agent_id"]: r for r in drill.survival_ranking()}
        assert ranking["fit"]["survival_ticks"] > ranking["unfit"]["survival_ticks"]

    def test_survival_time_is_fitness(self):
        c1 = Creature(agent_id="a", skill_genome=["coding"], skill_proficiency={"coding": 0.95})
        c2 = Creature(agent_id="b", skill_genome=[], skill_proficiency={})
        drill = EcoDrill([c1, c2], demanded_skills=["coding"],
                         health_max=15.0, metabolic_rate=1.0, seed=7, ledger=_ledger())
        drill.run(max_steps=200)
        assert drill.survival_ranking()[0]["agent_id"] == "a"

    def test_predator_bias_prefers_unskilled(self):
        """predator_bias_unskilled>0 时无法 serve 的个体更易成为捕食目标。"""
        fit = Creature(agent_id="fit", skill_genome=["coding"], skill_proficiency={"coding": 0.95})
        unfit = Creature(agent_id="unfit", skill_genome=["paint"], skill_proficiency={"paint": 0.95})
        drill = EcoDrill(
            [fit, unfit], demanded_skills=["coding"],
            health_max=100.0, metabolic_rate=0.01, seed=11, ledger=_ledger(),
            predator_pressure=0.0,
            economics={"predator_bias_unskilled": 50.0},
        )
        picks = [drill._pick_predator_target().agent_id for _ in range(80)]
        assert picks.count("unfit") > picks.count("fit")

    def test_same_pop_share_bias(self):
        a = Creature(agent_id="a1", skill_genome=["coding"], population="teamA")
        b = Creature(agent_id="b1", skill_genome=["coding"], population="teamB")
        drill = EcoDrill(
            [a, b], demanded_skills=["coding"],
            health_max=100.0, metabolic_rate=0.01, seed=3, ledger=_ledger(),
            economics={"same_pop_share_bias": 1.0},
        )
        # donor a1 总应偏向同队；此处 needy 含 b1 与假想 a2——只测同队优先路径
        c2 = Creature(agent_id="a2", skill_genome=["coding"], population="teamA")
        drill._creatures["a2"] = c2
        picks = [drill._pick_share_recipient(a, ["b1", "a2"]) for _ in range(40)]
        assert picks.count("a2") >= 30


class TestExtinctionAndDeath:
    def test_no_matching_skill_population_goes_extinct(self):
        c = Creature(agent_id="doomed", skill_genome=["x"], skill_proficiency={})
        drill = EcoDrill([c], demanded_skills=["y"], health_max=10.0, metabolic_rate=1.0, seed=1, ledger=_ledger())
        assert drill.run(max_steps=100)["extinct"] is True

    def test_dead_creature_marked_not_alive(self):
        c = Creature(agent_id="d", skill_genome=[], skill_proficiency={})
        drill = EcoDrill([c], demanded_skills=["z"], health_max=5.0, metabolic_rate=1.0, seed=1, ledger=_ledger())
        drill.run(max_steps=50)
        assert drill._creatures["d"].alive is False


class TestEpochReproduction:
    def test_epoch_produces_crossover_offspring(self):
        p1 = Creature(agent_id="p1aaaa", skill_genome=["coding", "review"], skill_proficiency={"coding": 0.9})
        p2 = Creature(agent_id="p2bbbb", skill_genome=["testing", "coding"], skill_proficiency={"testing": 0.8})
        drill = EcoDrill([p1, p2], demanded_skills=["coding"],
                         health_max=100.0, metabolic_rate=1.0, seed=3, ledger=_ledger())
        drill.run(max_steps=5)
        epoch = drill.run_epoch(reproduce_top_k=2)
        assert len(epoch["offspring"]) >= 1
        pool = set(p1.skill_genome) | set(p2.skill_genome) | set(drill.env.demanded_skills)
        for genome in epoch["offspring_genomes"].values():
            assert set(genome).issubset(pool)

    def test_offspring_generation_incremented(self):
        p1 = Creature(agent_id="aaaa", skill_genome=["coding"], skill_proficiency={"coding": 0.9})
        p2 = Creature(agent_id="bbbb", skill_genome=["coding"], skill_proficiency={"coding": 0.9})
        drill = EcoDrill([p1, p2], demanded_skills=["coding"],
                         health_max=100.0, metabolic_rate=1.0, seed=5, ledger=_ledger())
        drill.run(max_steps=3)
        assert drill.run_epoch(reproduce_top_k=1)["generation"] == 1


class TestGeneErasureEngine:
    def test_dead_genome_not_used_as_parent_when_survivors_exist(self):
        alive = Creature(agent_id="alive1", skill_genome=["coding"], skill_proficiency={"coding": 0.95})
        alive2 = Creature(agent_id="alive2", skill_genome=["coding"], skill_proficiency={"coding": 0.95})
        dead = Creature(agent_id="deadone", skill_genome=["deadskill"], skill_proficiency={})
        drill = EcoDrill([alive, alive2, dead], demanded_skills=["coding"],
                         health_max=30.0, metabolic_rate=1.0, seed=11, ledger=_ledger())
        drill.run(max_steps=100)
        epoch = drill.run_epoch(reproduce_top_k=2)
        assert "deadone" not in epoch["parents"]
        for genome in epoch["offspring_genomes"].values():
            assert "deadskill" not in genome


class TestCodeBuddyContractSymbols:
    """确认 CodeBuddy test_eco_drill.py 依赖的符号已在同一模块提供（收敛）。"""

    def test_intention_bias_covers_all(self):
        for intent in ("avoid", "forage", "mate", "rest_explore"):
            assert intent in _INTENTION_STRATEGY_BIAS
            assert "collaboration_weight" in _INTENTION_STRATEGY_BIAS[intent]
            assert "exploration_rate" in _INTENTION_STRATEGY_BIAS[intent]

    def test_predator_pressure_prob_in_range(self):
        assert 0.0 < _PREDATOR_PRESSURE_PROB < 1.0

    def test_eco_twin_state_sorts_by_survival(self):
        states = [
            EcoTwinState(twin_id="a", agent_id="a", survival_ticks=50, health=80, alive=True),
            EcoTwinState(twin_id="b", agent_id="b", survival_ticks=100, health=30, alive=True),
        ]
        assert sorted(states, key=lambda s: s.survival_ticks, reverse=True)[0].agent_id == "b"
