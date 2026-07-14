# -*- coding: utf-8 -*-
"""物竞天择 v2 测试 — 协作基因/信号协议/盲目学习/流动环境/时间线 (todos XT-1/XT-2).

验收对应 plan v2 §7：
  XT-1.2 CollabGenome 可序列化、初代多样
  XT-1.3 严酷环境下利他种群平均生存 > 纯自利种群
  XT-1.4 盲目学习习得生态位外 skill；基因携带成本惩罚囤积
  XT-1.5 生态位漂移替换需求；丰饶度影响死亡率
  XT-1.6 双基因交叉：collab 各维在双亲±变异带内
  XT-1.7 timeline 帧上限 600、字段齐备
  XT-2.1 eco_runtime_config habitat/drill_economics 节
"""

from __future__ import annotations

import pytest

from sandbox.eco_drill import (
    CollabGenome, Creature, EcoDrill, EnvState, sample_timeline,
    TIMELINE_MAX_FRAMES,
)


def _pop(collab: CollabGenome, n=4, skills=("s1", "s2")):
    """构造种群：每个生物只带一个 skill（半数时刻错配 → 有饥饿者可救）."""
    return [
        Creature(
            agent_id=f"c{i}",
            role="w",
            skill_genome=[skills[i % len(skills)]],
            skill_proficiency={skills[i % len(skills)]: 0.6},
            collab_genome=CollabGenome(
                share_tendency=collab.share_tendency,
                signal_tendency=collab.signal_tendency,
                follow_tendency=collab.follow_tendency,
                mate_choosiness=collab.mate_choosiness,
            ),
        )
        for i in range(n)
    ]


class TestCollabGenome:
    def test_serializable_in_ranking(self):
        drill = EcoDrill(creatures=_pop(CollabGenome()), demanded_skills=["s1", "s2"], seed=1)
        drill.run(max_steps=10)
        row = drill.survival_ranking()[0]
        assert set(row["collab_genome"].keys()) == {
            "share_tendency", "signal_tendency", "follow_tendency", "mate_choosiness"}

    def test_random_init_diverse(self):
        import random
        rng = random.Random(7)
        genomes = [CollabGenome.random_init(rng) for _ in range(8)]
        shares = {g.share_tendency for g in genomes}
        assert len(shares) > 1  # 初代非同质

    def test_crossover_within_band(self):
        import random
        rng = random.Random(3)
        a = CollabGenome(0.9, 0.9, 0.9, 0.9)
        b = CollabGenome(0.1, 0.1, 0.1, 0.1)
        for _ in range(20):
            child = CollabGenome.crossover(a, b, rng)
            for dim in ("share_tendency", "signal_tendency", "follow_tendency", "mate_choosiness"):
                v = getattr(child, dim)
                assert 0.0 <= v <= 1.0
                # 每维来自某一亲 ± 3σ 变异带
                assert abs(v - 0.9) < 0.2 or abs(v - 0.1) < 0.2


class TestAltruismSelection:
    """XT-1.3: 协作是被环境选择的——严酷环境下利他种群整体活得更久."""

    def _mean_survival(self, collab, seed):
        drill = EcoDrill(
            creatures=_pop(collab, n=6),
            demanded_skills=["s1", "s2"],
            seed=seed,
            abundance=0.9,
        )
        drill.run(max_steps=250)
        rows = drill.survival_ranking()
        return sum(r["survival_ticks"] for r in rows) / len(rows)

    def test_altruists_outlive_egoists_in_harsh_env(self):
        altruist = CollabGenome(share_tendency=0.95, signal_tendency=0.7,
                                follow_tendency=0.8, mate_choosiness=0.5)
        egoist = CollabGenome(share_tendency=0.0, signal_tendency=0.0,
                              follow_tendency=0.0, mate_choosiness=0.5)
        # 多 seed 取均值，避免单次随机波动
        seeds = [11, 22, 33, 44, 55]
        alt = sum(self._mean_survival(altruist, s) for s in seeds) / len(seeds)
        ego = sum(self._mean_survival(egoist, s) for s in seeds) / len(seeds)
        assert alt > ego, f"利他 {alt:.1f} 应 > 自利 {ego:.1f}"


class TestBlindLearning:
    def test_learns_off_niche_skill(self):
        c = Creature(agent_id="learner", role="w", skill_genome=["s1"],
                     skill_proficiency={"s1": 0.9},
                     collab_genome=CollabGenome(0, 0, 0, 0))
        drill = EcoDrill(
            creatures=[c], demanded_skills=["s1"], seed=5,
            blind_learning_rate=1.0,
            learning_pool=["s1", "useless_a", "useless_b"],
        )
        drill.run(max_steps=200)
        # REST 时必然掷骰学习 → 基因组内出现初始没有的 skill
        assert len(c.skill_genome) > 1

    def test_genome_carry_cost_punishes_hoarders(self):
        hoarder = Creature(agent_id="hoard", role="w",
                           skill_genome=[f"junk{i}" for i in range(10)],
                           collab_genome=CollabGenome(0, 0, 0, 0))
        lean = Creature(agent_id="lean", role="w", skill_genome=["junk0"],
                        collab_genome=CollabGenome(0, 0, 0, 0))
        drill = EcoDrill(
            creatures=[hoarder, lean], demanded_skills=["never_served"],
            seed=9, genome_carry_cost=0.6,
        )
        drill.run(max_steps=200)
        rows = {r["agent_id"]: r for r in drill.survival_ranking()}
        assert rows["hoard"]["survival_ticks"] < rows["lean"]["survival_ticks"]


class TestFluidEnvironment:
    def test_drift_replaces_demand(self):
        drill = EcoDrill(
            creatures=_pop(CollabGenome(), n=4),
            demanded_skills=["s1"],
            seed=2, drift_prob=1.0,
            learning_pool=["s1", "s2", "s3"],
        )
        drill.run(max_steps=5)
        ep = drill.run_epoch(reproduce_top_k=2, mutation_rate=0.0)
        assert ep["drift"] is not None
        assert ep["drift"]["removed"] == "s1"
        assert ep["drift"]["added"] != "s1"
        assert ep["drift"]["added"] in drill.env.demanded_skills

    def test_low_abundance_raises_mortality(self):
        def deaths(abundance, seed=13):
            drill = EcoDrill(creatures=_pop(CollabGenome(0, 0, 0, 0), n=6),
                             demanded_skills=["s1", "s2"], seed=seed,
                             abundance=abundance)
            drill.run(max_steps=300)
            return sum(1 for r in drill.survival_ranking() if not r["alive"])
        assert deaths(0.3) >= deaths(1.8)

    def test_env_predation_can_kill(self):
        drill = EcoDrill(creatures=_pop(CollabGenome(), n=4),
                         demanded_skills=["s1", "s2"], seed=4,
                         predator_pressure=0.9)
        out = drill.run(max_steps=200)
        assert any(s > 0 for s in [len(st.get("predated", []))
                                   for st in drill.timeline["steps"]])
        assert out["steps_executed"] > 0


class TestTimeline:
    def test_frame_fields(self):
        drill = EcoDrill(creatures=_pop(CollabGenome(0.9, 0.9, 0.9, 0.5), n=4),
                         demanded_skills=["s1", "s2"], seed=6)
        drill.run(max_steps=30)
        frame = drill.timeline["steps"][0]
        action = list(frame["actions"].values())[0]
        for key in ("intention", "health", "survival_ticks", "signals"):
            assert key in action
        assert "demand" in frame and "living" in frame

    def test_sample_timeline_caps_frames(self):
        steps = [{"step": i} for i in range(2000)]
        sampled = sample_timeline({"steps": steps, "epochs": []})
        assert len(sampled["steps"]) <= TIMELINE_MAX_FRAMES
        idx = [s["step"] for s in sampled["steps"]]
        assert idx == sorted(idx)  # 保序

    def test_epoch_records_offspring_collab(self):
        drill = EcoDrill(creatures=_pop(CollabGenome(), n=4),
                         demanded_skills=["s1", "s2"], seed=8)
        drill.run(max_steps=20)
        ep = drill.run_epoch(reproduce_top_k=2, mutation_rate=0.0)
        if ep["offspring"]:
            child = ep["offspring"][0]
            assert child in ep["offspring_collab"]
            assert "share_tendency" in ep["offspring_collab"][child]


class TestGenePoolSemantics:
    """XT-1.1 G7: dominant=存活高频 / deprecated=随死者消亡."""

    def test_dominant_and_deprecated(self):
        a = Creature(agent_id="a", role="w", skill_genome=["good"], alive=True)
        b = Creature(agent_id="b", role="w", skill_genome=["good"], alive=True)
        d = Creature(agent_id="d", role="w", skill_genome=["bad"], alive=True)
        drill = EcoDrill(creatures=[a, b, d], demanded_skills=["good"], seed=1)
        d.alive = False  # 模拟死亡
        pool = drill.gene_pool_snapshot()
        assert any(g["skill"] == "good" for g in pool["dominant"])
        assert any(g["skill"] == "bad" for g in pool["deprecated"])
        assert "collab_profile" in pool


class TestEconomicsOverride:
    def test_economics_injectable(self):
        drill = EcoDrill(creatures=_pop(CollabGenome(), n=2),
                         demanded_skills=["s1"], seed=1,
                         economics={"forage_gain": 12.0, "unknown_key": 99})
        assert drill._econ["forage_gain"] == 12.0
        assert "unknown_key" not in drill._econ


class TestHabitatConfig:
    """XT-2.1: eco_runtime_config 新 habitat / drill_economics 节."""

    def test_defaults_present(self, tmp_path):
        from agents.runtime.eco_runtime_config import EcoRuntimeConfig
        cfg = EcoRuntimeConfig(config_path=str(tmp_path / "cfg.json"))
        hab = cfg.get_section("habitat")
        # 2026-07-14 加压默认：略降丰饶、略升捕食，避免「苟活」吸收态
        assert hab["drift_prob"] == pytest.approx(0.2)
        assert hab["predator_pressure"] == pytest.approx(0.12)
        assert hab["abundance"] == pytest.approx(0.7)
        econ = cfg.get_section("drill_economics")
        assert econ["forage_gain"] == pytest.approx(9.0)  # v2.3+ 平衡 + 加压
        assert "skill_idle_penalty" in econ
        assert cfg.get_section("habitat")["niche_capacity"] == 3
        evo = cfg.get_section("evolution_pressure")
        assert evo["predator_bias_unskilled"] >= 0
        learn = cfg.get_section("learning")
        assert learn["blind_learning_rate"] == pytest.approx(0.1)
        assert learn["genome_carry_cost"] == pytest.approx(0.05)

    def test_partial_update_persists(self, tmp_path):
        from agents.runtime.eco_runtime_config import EcoRuntimeConfig
        p = str(tmp_path / "cfg.json")
        cfg = EcoRuntimeConfig(config_path=p)
        cfg.update({"habitat": {"abundance": 1.6, "bogus": 1}})
        again = EcoRuntimeConfig(config_path=p)
        hab = again.get_section("habitat")
        assert hab["abundance"] == pytest.approx(1.6)
        assert hab["drift_prob"] == pytest.approx(0.2)  # 未动的键保默认
        assert "bogus" not in hab


class TestNicheCompetition:
    """v2.2「物竞」：生态位容量竞争（同 tick 食物名额有限）."""

    def _pop(self, n=6):
        return [Creature(agent_id=f"c{i}", role="w", skill_genome=["s1"],
                         skill_proficiency={"s1": 0.3 + 0.1 * i},
                         collab_genome=CollabGenome(0.3, 0.3, 0.3, 0.5))
                for i in range(n)]

    def test_scarcity_produces_competition_and_differentiation(self):
        drill = EcoDrill(creatures=self._pop(), demanded_skills=["s1"],
                         seed=7, niche_capacity=1)
        drill.run(max_steps=200)
        outc = sum(1 for st in drill.timeline["steps"]
                   for a in st["actions"].values() if a["outcome"] == "outcompeted")
        succ = sum(1 for st in drill.timeline["steps"]
                   for a in st["actions"].values() if a["outcome"] == "success")
        ranking = drill.survival_ranking()
        alive = sum(1 for r in ranking if r["alive"])
        ticks = [r["survival_ticks"] for r in ranking]
        assert outc > 10, "稀缺名额下必须发生竞争"
        assert succ > 20, "赢家必须能进食"
        assert 0 < alive < 6, "必须出现分化（有人存活有人淘汰）"
        assert max(ticks) - min(ticks) > 30, "生存时长必须拉开差距"

    def test_zero_capacity_is_legacy_behavior(self):
        drill = EcoDrill(creatures=self._pop(), demanded_skills=["s1"], seed=7)
        drill.run(max_steps=200)
        assert not any(a["outcome"] == "outcompeted"
                       for st in drill.timeline["steps"]
                       for a in st["actions"].values())

    def test_outcompeted_does_not_feed_fear_spiral(self):
        """被挤掉不入恐惧窗口——否则全员 avoid 集体饿死（病态吸收态）."""
        drill = EcoDrill(creatures=self._pop(), demanded_skills=["s1"],
                         seed=7, niche_capacity=1)
        drill.run(max_steps=200)
        succ = sum(1 for st in drill.timeline["steps"]
                   for a in st["actions"].values() if a["outcome"] == "success")
        assert succ > 0, "存在成功觅食者（未坍缩为全员躲避）"


class TestFearDecay:
    """v2.3: 躲藏时恐惧记忆消退——修复 avoid 永锁吸收态（全参数组合系统性全灭的真凶）."""

    def test_avoidance_is_not_absorbing(self):
        """连败个体进入 AVOID 后应能随恐惧消退重新觅食，而非锁死饿死."""
        c = Creature(agent_id="a", role="w", skill_genome=["s1"],
                     skill_proficiency={"s1": 0.6},
                     collab_genome=CollabGenome(0, 0, 0, 0))
        # 人为塞满失败记忆 → fear=1 → 首帧必 AVOID
        c.recent_outcomes = [False] * 8
        drill = EcoDrill(creatures=[c], demanded_skills=["s1"], seed=1)
        drill.run(max_steps=120)
        intents = [st["actions"]["a"]["intention"]
                   for st in drill.timeline["steps"] if "a" in st["actions"]]
        assert "avoid" in intents, "初期应处于躲藏"
        assert "forage" in intents, "恐惧消退后必须重新觅食（不是锁死到饿死）"

    def test_population_survivable_under_default_balance(self):
        """v2.3 平衡定档：默认经济学下（gain=8）混合种群不应必然全灭."""
        import random as _r
        survivors = 0
        for sd in (1, 2, 3, 4, 5):
            rng = _r.Random(sd)
            skills = [f"sk{i}" for i in range(4)]
            pop = []
            for i in range(7):
                mine = rng.sample(skills, rng.randint(1, 2))
                pop.append(Creature(agent_id=f"a{i}", role="w", skill_genome=list(mine),
                                    skill_proficiency={s: 0.5 for s in mine},
                                    collab_genome=CollabGenome.random_init(rng)))
            drill = EcoDrill(creatures=pop, demanded_skills=skills, seed=sd,
                             niche_capacity=3, blind_learning_rate=0.1,
                             genome_carry_cost=0.05,
                             economics={"forage_gain": 8.0})
            drill.run(max_steps=150)
            survivors += sum(1 for r in drill.survival_ranking() if r["alive"])
        assert survivors > 0, "五个 seed 全灭 —— 默认平衡失效"
