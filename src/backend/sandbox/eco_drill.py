# -*- coding: utf-8 -*-
"""Eco Drill — 物竞天择数字孪生演练：自然选择生境内核.

对应 docs/物竞天择数字孪生演练plan.md §4 / todos ND-2。

核心立场（用户设计）：不写"Agent 应该如何协作"的规则，只构建
  代谢红线 + 受限感知 + 生存博弈 + 随机繁衍
的闭环，让 Skill 与协作协议**被环境选择出来**。生存时长（survival_ticks）
是唯一隐式适应度，没有上帝视角人工评分。

编排既有零件（不重造）：
  - 感知 + H/F/L 意图仲裁 → agents.runtime.eco_loop（Claude 已有）
  - 代谢红线 + 生存时长 → agents.runtime.health_ledger（Claude 已有）
  - 阈值参数 → agents.runtime.eco_runtime_config（Claude 已有）
  - 繁衍（skill 交叉遗传）→ 默认内置 crossover，可注入 team_manager.mate（ND-3）
  - 世代最优锁定 → agents.ratchet_ledger（CodeBuddy，ND-6 接线）
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── 代谢/觅食模型常量（可被 eco_runtime_config 覆盖的部分走 HealthLedger）──
FORAGE_GAIN = 6.0          # 觅食命中（有匹配 skill）获得的能量
FORAGE_MISS_PENALTY = 2.0  # 觅食未命中的额外代谢惩罚（能效低者被"饿死"的机制）
AVOID_COST = 0.5           # 避险动作低代谢（躲藏）
REST_COST = 0.0            # 静息只承受基础代谢
FEAR_WINDOW = 8            # 恐惧计算的近期窗口

# 捕食压力：每世代注入捕食事件的概率（军备竞赛动态选择压力，plan §2.1 / todos ND-2.3）
_PREDATOR_PRESSURE_PROB = 0.3

# eco_loop 意图 → twin_loop strategy_params 偏置（复用 twin_loop 动作分派，plan §4）
# 意图不直接写"如何协作"，只偏置 twin 的协作权重/探索率，让协作靠涌现。
_INTENTION_STRATEGY_BIAS: Dict[str, Dict[str, float]] = {
    "avoid":        {"collaboration_weight": 0.2, "exploration_rate": 0.1},
    "forage":       {"collaboration_weight": 0.4, "exploration_rate": 0.6},
    "mate":         {"collaboration_weight": 0.8, "exploration_rate": 0.2},
    "rest_explore": {"collaboration_weight": 0.5, "exploration_rate": 0.8},
}


@dataclass
class EcoTwinState:
    """生境中一个孪生的运行时状态快照——供选择/繁衍按 survival_ticks 排序.

    与 twin_loop.AgentTwin 解耦的轻量记录：只保留自然选择关心的字段
    （生存时长=适应度、alive=是否入基因池、skills=基因）。
    """

    twin_id: str = ""
    agent_id: str = ""
    skills: List[str] = field(default_factory=list)
    survival_ticks: int = 0
    health: float = 0.0
    alive: bool = True
    generation: int = 0

    def intention_bias(self, intention: str) -> Dict[str, float]:
        """把当前意图映射为 twin_loop 策略偏置（复用现有决策分派）。"""
        return dict(_INTENTION_STRATEGY_BIAS.get(intention, _INTENTION_STRATEGY_BIAS["rest_explore"]))


@dataclass
class Creature:
    """生境中的一个生物 = Agent 的孪生 + 可遗传基因（skill_genome）."""

    agent_id: str
    role: str = ""
    skill_genome: List[str] = field(default_factory=list)   # 基因型 = skill_id 集合
    skill_proficiency: Dict[str, float] = field(default_factory=dict)
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    alive: bool = True
    recent_outcomes: List[bool] = field(default_factory=list)  # True=成功 觅食

    def recent_fail_rate(self) -> float:
        window = self.recent_outcomes[-FEAR_WINDOW:]
        if not window:
            return 0.0
        fails = sum(1 for ok in window if not ok)
        return fails / len(window)


class EcoDrill:
    """自然选择生境引擎.

    environment: 环境每步"需求"的 skill（生态位）——生物必须有匹配 skill 才能觅食成功。
    这直接实现"代谢红线"：基因不匹配生态位的生物持续觅食失败 → 净代谢为负 → 饿死。
    """

    def __init__(
        self,
        creatures: List[Creature],
        demanded_skills: List[str],
        *,
        health_max: float = 100.0,
        metabolic_rate: float = 1.0,
        seed: Optional[int] = None,
        ledger: Any = None,
        mate_fn: Optional[Callable[[Creature, Creature, int], Creature]] = None,
    ) -> None:
        self._creatures: Dict[str, Creature] = {c.agent_id: c for c in creatures}
        self._demanded = list(demanded_skills) or ["generic"]
        self._rng = random.Random(seed)
        self._step_index = 0
        self._mate_fn = mate_fn or self._default_crossover

        # Health 账本：优先注入（测试），否则用独立内存账本（不落盘，避免污染生产 storage）
        if ledger is not None:
            self._ledger = ledger
        else:
            from agents.runtime.health_ledger import HealthLedger
            import tempfile
            from pathlib import Path
            self._ledger = HealthLedger(team_id="__eco_drill__", ledger_dir=Path(tempfile.mkdtemp()))

        # 显式入参优先（生产调用方从 eco_runtime_config 读好再传入，见 plan ND-6）。
        # 不在此处用 config 覆盖入参——否则会盖掉调用方/测试的显式代谢设置。
        self._health_max = health_max
        self._metabolic_rate = metabolic_rate

        # 意图阈值从配置读
        try:
            from agents.runtime.eco_loop import IntentionThresholds
            self._thresholds = IntentionThresholds.from_config()
        except Exception:
            from agents.runtime.eco_loop import IntentionThresholds
            self._thresholds = IntentionThresholds()

        # 初始化每个生物的 Health
        for c in self._creatures.values():
            self._ledger.get_or_create(c.agent_id, health_max=self._health_max,
                                       metabolic_rate=self._metabolic_rate)

    # ── 存活种群 ──
    def living(self) -> List[Creature]:
        return [c for c in self._creatures.values() if c.alive]

    def is_extinct(self) -> bool:
        return len(self.living()) == 0

    # ── 单步生境 tick ──
    def step(self) -> Dict[str, Any]:
        """一个生境 tick：受限感知 → H/F/L 意图 → 觅食/避险 → 代谢结算 → 死亡淘汰."""
        from agents.runtime.eco_loop import (
            WorldView, MentalState, IntentionType,
            compute_hunger, compute_fear, generate_intention,
        )

        demand = self._demanded[self._step_index % len(self._demanded)]
        deaths: List[str] = []
        step_summary: Dict[str, Any] = {"step": self._step_index, "demand": demand, "actions": {}}

        for c in self.living():
            hs = self._ledger.get(c.agent_id)
            hunger = compute_hunger(hs.health, hs.health_max)
            recent = c.recent_outcomes[-FEAR_WINDOW:]
            fear = compute_fear(sum(1 for ok in recent if not ok), len(recent), is_blocked=False)
            state = MentalState(hunger=hunger, fear=fear, libido=0.0)

            can_serve = demand in c.skill_genome
            view = WorldView(
                agent_id=c.agent_id,
                own_backlog=1,
                recent_success_count=sum(1 for ok in recent if ok),
                recent_fail_count=sum(1 for ok in recent if not ok),
                visible_unclaimed_tasks=1 if can_serve else 0,
            )
            intention = generate_intention(state, view, self._thresholds)

            # 动作结算 → 代谢成本/回血（代谢红线的落点）
            action_cost = 0.0
            reward = 0.0
            outcome: Optional[bool] = None  # None=非觅食步(不计入恐惧窗口)
            if intention.type == IntentionType.FORAGE:
                if can_serve:
                    prof = c.skill_proficiency.get(demand, 0.5)
                    # 熟练度决定觅食成功概率（复用仿生"练熟"思想）
                    if self._rng.random() < max(0.25, min(0.95, 0.3 + 0.6 * prof)):
                        reward = FORAGE_GAIN
                        outcome = True
                        # session 内练熟
                        c.skill_proficiency[demand] = min(0.98, prof + 0.02)
                    else:
                        action_cost = FORAGE_MISS_PENALTY
                        outcome = False
                else:
                    # 基因不匹配生态位：白费力气，纯消耗（能效低→被饿死）
                    action_cost = FORAGE_MISS_PENALTY
                    outcome = False
            elif intention.type == IntentionType.AVOID:
                action_cost = AVOID_COST
            else:  # REST_EXPLORE / MATE(生境内不在 step 触发)
                action_cost = REST_COST

            result = self._ledger.tick(c.agent_id, action_cost=action_cost, reward=reward)
            # 只有觅食尝试(成功/失败)才计入恐惧窗口；休息/避险不算"失败"，避免恐惧误升。
            if outcome is not None:
                c.recent_outcomes.append(outcome)
            step_summary["actions"][c.agent_id] = {
                "intention": intention.type.value,
                "can_serve": can_serve,
                "outcome": "success" if outcome else "miss/idle",
                "health": round(result.health_after, 2),
                "survival_ticks": result.survival_ticks,
            }
            if result.became_dormant:
                c.alive = False
                deaths.append(c.agent_id)

        self._step_index += 1
        step_summary["deaths"] = deaths
        step_summary["living"] = len(self.living())
        return step_summary

    def run(self, max_steps: int = 100) -> Dict[str, Any]:
        """跑一场生境，直到 max_steps 或全灭。返回每个生物的生存时长排名。"""
        steps = []
        for _ in range(max_steps):
            if self.is_extinct():
                break
            steps.append(self.step())
        return {
            "steps_executed": len(steps),
            "extinct": self.is_extinct(),
            "ranking": self.survival_ranking(),
        }

    def survival_ranking(self) -> List[Dict[str, Any]]:
        """按生存时长（隐式适应度）降序排名——唯一的适者标准。"""
        rows = []
        for c in self._creatures.values():
            hs = self._ledger.get(c.agent_id)
            rows.append({
                "agent_id": c.agent_id,
                "survival_ticks": hs.survival_ticks if hs else 0,
                "alive": c.alive,
                "generation": c.generation,
                "skill_genome": list(c.skill_genome),
                "health": round(hs.health, 2) if hs else 0.0,
            })
        rows.sort(key=lambda r: r["survival_ticks"], reverse=True)
        return rows

    # ── 世代循环（epoch）──
    def run_epoch(self, reproduce_top_k: int = 2, mutation_rate: float = 0.1) -> Dict[str, Any]:
        """一个世代：按生存时长选择 top-K，交配（skill 交叉遗传）产生下一代.

        基因抹除（ND-4）：只有存活或生存时长排名靠前者进入繁衍；死亡个体基因不遗传。
        """
        ranking = self.survival_ranking()
        # 选择：只从"活着或生存最久"的个体里挑亲本（死者基因被抹除）
        eligible = [r for r in ranking if r["alive"]] or ranking[:reproduce_top_k]
        parents = eligible[:max(2, reproduce_top_k)]
        offspring: List[Creature] = []
        gen = max((c.generation for c in self._creatures.values()), default=0) + 1

        if len(parents) >= 2:
            for i in range(reproduce_top_k):
                p1 = self._creatures[parents[i % len(parents)]["agent_id"]]
                p2 = self._creatures[parents[(i + 1) % len(parents)]["agent_id"]]
                child = self._mate_fn(p1, p2, gen)
                if mutation_rate > 0 and self._rng.random() < mutation_rate and self._demanded:
                    # 变异：随机注入一个生态位需求 skill（探索新解）
                    new_skill = self._rng.choice(self._demanded)
                    if new_skill not in child.skill_genome:
                        child.skill_genome.append(new_skill)
                offspring.append(child)
                self._creatures[child.agent_id] = child
                self._ledger.get_or_create(child.agent_id, health_max=self._health_max,
                                           metabolic_rate=self._metabolic_rate)

        return {
            "generation": gen,
            "parents": [p["agent_id"] for p in parents],
            "offspring": [c.agent_id for c in offspring],
            "offspring_genomes": {c.agent_id: list(c.skill_genome) for c in offspring},
        }

    # ── ND-2.3: 捕食压力（军备竞赛动态选择压力）──
    def inject_predator_pressure(self, intensity: float = 0.0) -> List[str]:
        """对存活种群随机施加捕食压力：被选中的生物额外扣一次代谢（模拟被捕食消耗）。

        返回本次受压的 agent_id 列表。intensity<=0 时用 `_PREDATOR_PRESSURE_PROB`。
        这是"军备竞赛"的动态压力：未演化出高效生存策略的分支被持续剪掉。
        """
        prob = intensity if intensity > 0 else _PREDATOR_PRESSURE_PROB
        hit: List[str] = []
        for c in self.living():
            if self._rng.random() < prob:
                result = self._ledger.tick(c.agent_id, action_cost=FORAGE_MISS_PENALTY, reward=0.0)
                hit.append(c.agent_id)
                if result.became_dormant:
                    c.alive = False
        return hit

    # ── ND-6.1: 棘轮锁定世代最优（只进不退）──
    def ratchet_lock(self, team_id: str = "eco_drill") -> Dict[str, Any]:
        """把当前种群的最长生存时长写入全局棘轮账本（只进不退）。"""
        ranking = self.survival_ranking()
        best = ranking[0]["survival_ticks"] if ranking else 0
        try:
            from agents.ratchet_ledger import get_ratchet_ledger
            return get_ratchet_ledger().advance(
                f"eco_survival:{team_id}", float(best),
                evidence={"generation": max((c.generation for c in self._creatures.values()), default=0)},
            )
        except Exception as e:  # pragma: no cover - 账本不可用时不阻断
            logger.warning("ratchet_lock 跳过: %s", e)
            return {"advanced": False, "reason": f"ratchet_unavailable: {e}"}

    def _default_crossover(self, p1: Creature, p2: Creature, generation: int) -> Creature:
        """默认 skill 交叉遗传：双亲基因并集去重的一个子集（复合型 Skill）。

        ND-3 会用 team_manager.mate 的更完整交叉替换本默认实现（通过 mate_fn 注入）。
        """
        pool = list(dict.fromkeys([*p1.skill_genome, *p2.skill_genome]))
        # 交叉：随机取双亲基因的一半以上，保证至少 1 个
        k = max(1, len(pool) // 2 + self._rng.randint(0, len(pool) - len(pool) // 2)) if pool else 0
        genome = self._rng.sample(pool, min(k, len(pool))) if pool else []
        child_id = f"{p1.agent_id[:4]}x{p2.agent_id[:4]}_g{generation}_{self._rng.randint(100, 999)}"
        prof = {}
        for s in genome:
            prof[s] = max(p1.skill_proficiency.get(s, 0.5), p2.skill_proficiency.get(s, 0.5))
        return Creature(
            agent_id=child_id,
            role=p1.role or p2.role,
            skill_genome=genome,
            skill_proficiency=prof,
            generation=generation,
            parent_ids=[p1.agent_id, p2.agent_id],
        )

    # ── ND-6.1: 棘轮锁定世代最优 ────────────────────────────

    def ratchet_lock(self, team_id: str, best_survival: int, gen: int) -> Dict[str, Any]:
        """棘轮锁定世代最优生存时长 — 只进不退."""
        try:
            from agents.ratchet_ledger import get_ratchet_ledger
            ledger = get_ratchet_ledger()
            metric_key = f"eco_survival:{team_id}"
            return ledger.advance(
                metric_key=metric_key,
                value=float(best_survival),
                evidence={"generation": gen, "source": "eco_drill"},
            )
        except Exception as e:
            logger.warning("棘轮锁定失败: %s", e)
            return {"advanced": False, "current": 0.0, "reason": str(e)}

    # ── ND-2.3: 捕食压力注入 ────────────────────────────────

    PREDATOR_PRESSURE_PROB = 0.08

    def inject_predator_pressure(self) -> List[str]:
        """随机禁用一个存活生物（模拟被捕食），返回被影响的 agent_id 列表."""
        living = self.living()
        if not living:
            return []
        if self._rng.random() > self.PREDATOR_PRESSURE_PROB:
            return []
        target = self._rng.choice(living)
        # 捕食压力：直接扣大量 Health（模拟被捕食伤害）
        hs = self._ledger.get(target.agent_id)
        if hs:
            result = self._ledger.tick(target.agent_id, action_cost=20.0, reward=0.0)
            if result.became_dormant:
                target.alive = False
                logger.info("🦅 捕食压力 → %s 被捕食死亡", target.agent_id[:8])
            return [target.agent_id]
        return []

    # ── 基因池快照 ─────────────────────────────────────────

    def gene_pool_snapshot(self) -> Dict[str, Any]:
        """构建当前基因池快照：dominant/deprecated/neutral skill 分布."""
        dominant: List[Dict[str, Any]] = []
        deprecated: List[Dict[str, Any]] = []
        neutral: List[Dict[str, Any]] = []
        for c in self._creatures.values():
            for skill in c.skill_genome:
                entry = {
                    "skill": skill,
                    "agent_id": c.agent_id,
                    "proficiency": c.skill_proficiency.get(skill, 0.5),
                    "alive": c.alive,
                }
                if c.alive:
                    neutral.append(entry)
                else:
                    deprecated.append(entry)
        return {
            "dominant": dominant,
            "deprecated": deprecated,
            "neutral": neutral,
            "total_creatures": len(self._creatures),
            "living": len(self.living()),
        }


# ═══════════════════════════════════════════════════════════════
# Trial API 适配层 — 把 EcoDrill 接入 trial_api 的演练路由
# ═══════════════════════════════════════════════════════════════


async def run_drill_via_trial(
    trial_id: str,
    branch_id: str,
    session_id: str,
    team_id: str,
    max_steps: int = 150,
    max_generations: int = 3,
) -> Dict[str, Any]:
    """trial_api.branch_run 调用的入口：从团队构建 creatures → 跑多代生境 → 返回结果.

    ND-1.2 路由：eco 团队的 trial 创建后，branch_run 调本函数而非 orch.run_full_pipeline。
    """
    import asyncio

    # 从团队构建 creatures
    try:
        from agents.api import _team_manager
    except Exception:
        _team_manager = None
    if _team_manager is None:
        return {"error": "team_manager_not_ready", "trial_id": trial_id}

    team = _team_manager.get_team(team_id)
    if team is None:
        return {"error": "team_not_found", "team_id": team_id}

    # 收集所有 skill 作为生态位需求
    all_skills = list(team.skills.keys()) if team.skills else []
    if not all_skills:
        all_skills = ["generic"]

    # 从 team agents 构建 creatures
    creatures: List[Creature] = []
    agents = team.agents.values() if isinstance(team.agents, dict) else (team.agents or [])
    for agent in agents:
        c = Creature(
            agent_id=agent.agent_id,
            role=agent.role,
            skill_genome=list(agent.skills) if agent.skills else [],
            skill_proficiency={s: 0.5 for s in (agent.skills or [])},
        )
        creatures.append(c)

    if not creatures:
        return {"error": "no_creatures", "trial_id": trial_id}

    # 构建引擎
    drill = EcoDrill(
        creatures=creatures,
        demanded_skills=all_skills,
    )

    # 多代演化
    generations: List[Dict[str, Any]] = []
    prev_best = -1

    for gen in range(max_generations):
        # 跑一代
        run_result = drill.run(max_steps=max_steps)
        ranking = run_result.get("ranking", [])

        if ranking:
            best_survival = ranking[0].get("survival_ticks", 0)
            avg_survival = sum(r.get("survival_ticks", 0) for r in ranking) / len(ranking)
        else:
            best_survival = 0
            avg_survival = 0.0

        # 棘轮锁定
        ratchet_result = drill.ratchet_lock(team_id, best_survival, gen)

        # 繁衍
        births = 0
        if not drill.is_extinct() and len(drill.living()) >= 2:
            epoch_result = drill.run_epoch(reproduce_top_k=2, mutation_rate=0.15)
            births = len(epoch_result.get("offspring", []))

        gen_rec = {
            "generation": gen,
            "steps_executed": run_result.get("steps_executed", 0),
            "extinct": run_result.get("extinct", False),
            "living": len(drill.living()),
            "avg_survival_ticks": round(avg_survival, 2),
            "best_survival_ticks": best_survival,
            "births": births,
            "ratchet_advanced": ratchet_result.get("advanced", False),
            "ratchet_value": ratchet_result.get("current", 0.0),
        }
        generations.append(gen_rec)
        logger.info(
            "🧬 gen%d: living=%d best=%d avg=%.1f births=%d ratchet=%s",
            gen, gen_rec["living"], best_survival, avg_survival,
            births, "↑" if ratchet_result.get("advanced") else "=",
        )

        # 棘轮未推进且非首代 → 停止
        if gen > 0 and not ratchet_result.get("advanced", False):
            if best_survival <= prev_best:
                logger.info("🔒 棘轮锁定: gen%d best=%d <= prev=%d", gen, best_survival, prev_best)
                break

        prev_best = best_survival

        if drill.is_extinct():
            logger.info("💀 种群全灭于 gen%d", gen)
            break

        # 让出事件循环（避免阻塞）
        await asyncio.sleep(0)

    return {
        "trial_id": trial_id,
        "drill_kind": "natural_selection",
        "generations": generations,
        "final_ranking": drill.survival_ranking(),
        "gene_pool": drill.gene_pool_snapshot(),
        "best_survival_ticks": prev_best if prev_best > 0 else 0,
        "total_generations": len(generations),
    }


# ── 单例适配（trial_api.branch_run 通过 get_eco_drill().run_drill 调用）──

class _EcoDrillAdapter:
    """适配 trial_api 的调用约定：run_drill(trial_id, ...) → run_drill_via_trial."""

    async def run_drill(self, **kwargs) -> Dict[str, Any]:
        return await run_drill_via_trial(**kwargs)


_eco_drill_adapter: Optional[_EcoDrillAdapter] = None


def get_eco_drill() -> _EcoDrillAdapter:
    global _eco_drill_adapter
    if _eco_drill_adapter is None:
        _eco_drill_adapter = _EcoDrillAdapter()
    return _eco_drill_adapter
