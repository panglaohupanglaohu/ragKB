# -*- coding: utf-8 -*-
"""Eco Drill v2 — 物竞天择数字孪生演练：自然选择生境内核.

对应 docs/物竞天择数字孪生演练plan.md v2 §3 / todos XT-1。

核心立场（用户世界观）：Agent 不是人类的模仿——它有自己的生态环境，以自己
独有的方式（信号协议）沟通、繁衍、生活与成长；背后的演化规律是物竞天择。
不写"Agent 应该如何协作"的规则，只构建
  代谢红线 + 受限感知 + 生存博弈 + 可遗传的协作倾向 + 流动环境
的闭环，让 Skill 与协作协议**被环境选择出来**。生存时长（survival_ticks）
是唯一隐式适应度，没有上帝视角人工评分。

v2 新增（在 CodeBuddy ND-1~ND-6 基座上）：
  - CollabGenome 协作基因（share/signal/follow/choosiness，可遗传可变异）
  - 信号协议 FOOD/HELP/COURT（Agent 独有沟通方式，受限视野内可感知）
  - 盲目学习（REST 时随机习得 skill，环境判决有用与否；基因携带代谢成本）
  - 流动环境 EnvState（生态位漂移 + 捕食压力 + 丰饶度）
  - timeline 时间线记录（前端剧场回放的数据基础）
  - 修复 v1 重复方法定义缺陷（ratchet_lock / inject_predator_pressure ×2）
  - gene_pool_snapshot 语义化（dominant=存活高频，deprecated=随死者消亡）

编排既有零件（不重造）：
  - 感知 + H/F/L 意图仲裁 → agents.runtime.eco_loop（Claude 已有）
  - 代谢红线 + 生存时长 → agents.runtime.health_ledger（Claude 已有）
  - 阈值参数 → agents.runtime.eco_runtime_config（Claude 已有）
  - 世代最优锁定 → agents.ratchet_ledger（CodeBuddy）
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── 代谢/觅食模型常量（生产参数走 eco_runtime_config，见 run_drill_via_trial）──
FORAGE_GAIN = 6.0          # 觅食命中（有匹配 skill）获得的能量（×abundance）
FORAGE_MISS_PENALTY = 2.0  # 觅食未命中的额外代谢惩罚（能效低者被"饿死"的机制）
AVOID_COST = 0.5           # 避险动作低代谢（躲藏）
REST_COST = 0.0            # 静息只承受基础代谢
FEAR_WINDOW = 8            # 恐惧计算的近期窗口
SIGNAL_COST = 0.3          # 发一次信号的代谢成本（协作是有代价的，才可能被淘汰）
SHARE_FRACTION = 0.4       # 分享时让渡给求助者的收益比例
FOLLOW_BONUS = 0.15        # 跟随 FOOD 信号的觅食成功率加成（信息优势）
HELP_HUNGER = 0.75         # 饥饿超过此值才会发 HELP 信号
TIMELINE_MAX_FRAMES = 600  # timeline 帧数上限（超出等距采样）

# 捕食压力：模块级默认概率（军备竞赛动态选择压力，plan §3.3 / todos XT-1.5）
_PREDATOR_PRESSURE_PROB = 0.3

# eco_loop 意图 → twin_loop strategy_params 偏置（复用 twin_loop 动作分派）
# 意图不直接写"如何协作"，只偏置 twin 的协作权重/探索率，让协作靠涌现。
_INTENTION_STRATEGY_BIAS: Dict[str, Dict[str, float]] = {
    "avoid":        {"collaboration_weight": 0.2, "exploration_rate": 0.1},
    "forage":       {"collaboration_weight": 0.4, "exploration_rate": 0.6},
    "mate":         {"collaboration_weight": 0.8, "exploration_rate": 0.2},
    "rest_explore": {"collaboration_weight": 0.5, "exploration_rate": 0.8},
}


@dataclass
class EcoTwinState:
    """生境中一个孪生的运行时状态快照——供选择/繁衍按 survival_ticks 排序."""

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
class CollabGenome:
    """协作基因 — 可遗传的协作【倾向】向量，不是协作规则（plan 原则 5）.

    协作模式（分享/信号/跟随/择偶）由这些倾向的概率表达涌现，
    其存续由环境判决：严酷环境下利他救群，宽松环境下利他是负担。
    """

    share_tendency: float = 0.5    # 觅食盈余分享倾向（利他）
    signal_tendency: float = 0.5   # 发信号倾向（发现机会时广播）
    follow_tendency: float = 0.5   # 响应他人信号的倾向（跟随）
    mate_choosiness: float = 0.5   # 择偶挑剔度

    def to_dict(self) -> Dict[str, float]:
        return {
            "share_tendency": round(self.share_tendency, 3),
            "signal_tendency": round(self.signal_tendency, 3),
            "follow_tendency": round(self.follow_tendency, 3),
            "mate_choosiness": round(self.mate_choosiness, 3),
        }

    @classmethod
    def random_init(cls, rng: Optional[random.Random] = None) -> "CollabGenome":
        """随机初始化——保证初代种群协作基因多样，选择才有原料。"""
        r = rng or random
        return cls(
            share_tendency=round(r.random(), 3),
            signal_tendency=round(r.random(), 3),
            follow_tendency=round(r.random(), 3),
            mate_choosiness=round(r.random(), 3),
        )

    @classmethod
    def crossover(cls, a: "CollabGenome", b: "CollabGenome",
                  rng: random.Random, sigma: float = 0.05) -> "CollabGenome":
        """每维随机取一亲 + 高斯微变异（clip 0~1）。"""
        def _mix(x: float, y: float) -> float:
            v = (x if rng.random() < 0.5 else y) + rng.gauss(0.0, sigma)
            return round(max(0.0, min(1.0, v)), 3)
        return cls(
            share_tendency=_mix(a.share_tendency, b.share_tendency),
            signal_tendency=_mix(a.signal_tendency, b.signal_tendency),
            follow_tendency=_mix(a.follow_tendency, b.follow_tendency),
            mate_choosiness=_mix(a.mate_choosiness, b.mate_choosiness),
        )


@dataclass
class EnvState:
    """流动环境 — 生态位漂移 + 捕食压力 + 丰饶度（plan §3.3）.

    环境不流动就没有持续选择：上一代最优基因不保证下一代最优。
    """

    demanded_skills: List[str] = field(default_factory=list)
    drift_prob: float = 0.0        # 每 epoch 生态位漂移概率
    predator_pressure: float = 0.0  # 每 tick 捕食事件概率（0=关闭）
    abundance: float = 1.0         # 丰饶度：觅食收益倍率
    niche_capacity: int = 0        # 「物竞」：每 tick 生态位可供成功觅食的名额（0=不限，兼容旧行为）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "demanded_skills": list(self.demanded_skills),
            "drift_prob": self.drift_prob,
            "predator_pressure": self.predator_pressure,
            "abundance": self.abundance,
            "niche_capacity": self.niche_capacity,
        }


@dataclass
class Creature:
    """生境中的一个生物 = Agent 的孪生 + 可遗传双基因（skill + collab）."""

    agent_id: str
    role: str = ""
    population: str = ""   # v2.3 多种群同场竞争：所属种群（团队）标签
    skill_genome: List[str] = field(default_factory=list)   # 技能基因型
    skill_proficiency: Dict[str, float] = field(default_factory=dict)
    collab_genome: CollabGenome = field(default_factory=CollabGenome.random_init)
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    alive: bool = True
    recent_outcomes: List[bool] = field(default_factory=list)  # True=觅食成功

    def recent_fail_rate(self) -> float:
        window = self.recent_outcomes[-FEAR_WINDOW:]
        if not window:
            return 0.0
        fails = sum(1 for ok in window if not ok)
        return fails / len(window)


class EcoDrill:
    """自然选择生境引擎 v2.

    environment: 环境每步"需求"的 skill（生态位）——生物必须有匹配 skill 才能觅食成功。
    这直接实现"代谢红线"：基因不匹配生态位的生物持续觅食失败 → 净代谢为负 → 饿死。

    显式入参优先原则：构造参数缺省值保守（blind_learning/carry_cost/drift/predation 均 0），
    生产调用方（run_drill_via_trial）从 eco_runtime_config 读好再传入——
    既有单元测试与调用方行为零回归。
    """

    PREDATOR_PRESSURE_PROB = 0.08   # 手动注入捕食的默认概率（兼容 v1 测试契约）

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
        blind_learning_rate: float = 0.0,
        genome_carry_cost: float = 0.0,
        drift_prob: float = 0.0,
        predator_pressure: float = 0.0,
        abundance: float = 1.0,
        niche_capacity: int = 0,
        learning_pool: Optional[List[str]] = None,
        record_timeline: bool = True,
        economics: Optional[Dict[str, float]] = None,
    ) -> None:
        self._creatures: Dict[str, Creature] = {c.agent_id: c for c in creatures}
        self._rng = random.Random(seed)
        self._step_index = 0
        self._mate_fn = mate_fn or self._default_crossover

        # 觅食/协作经济学（可被 drill_economics 配置覆盖；默认=模块常量，测试零回归）
        self._econ: Dict[str, float] = {
            "forage_gain": FORAGE_GAIN,
            "forage_miss_penalty": FORAGE_MISS_PENALTY,
            "avoid_cost": AVOID_COST,
            "signal_cost": SIGNAL_COST,
            "share_fraction": SHARE_FRACTION,
            "follow_bonus": FOLLOW_BONUS,
            "help_hunger": HELP_HUNGER,
        }
        if economics:
            for k, v in economics.items():
                if k in self._econ:
                    try:
                        self._econ[k] = float(v)
                    except (TypeError, ValueError):
                        pass

        self.env = EnvState(
            demanded_skills=list(demanded_skills) or ["generic"],
            drift_prob=drift_prob,
            predator_pressure=predator_pressure,
            abundance=abundance,
            niche_capacity=max(0, int(niche_capacity)),
        )
        self._blind_learning_rate = blind_learning_rate
        self._genome_carry_cost = genome_carry_cost
        # 盲目学习的技能池：全池（不是只有生态位需求——学习是盲目的）
        pool = set(learning_pool or [])
        pool.update(self.env.demanded_skills)
        for c in creatures:
            pool.update(c.skill_genome)
        self._learning_pool: List[str] = sorted(pool)

        # 信号板：上一 tick 发出的信号，本 tick 视野内可感知（受限感知：只读上一帧）
        self._signal_board: List[Dict[str, Any]] = []
        # 求偶登记：agent_id -> 最近一次 COURT 的 step（epoch 配对时用）
        self._court_log: Dict[str, int] = {}
        # 分享转移缓冲：recipient -> 下一 tick 结算的额外回血（避免对同一 tick 双重代谢）
        self._pending_rewards: Dict[str, float] = {}

        # timeline（回放数据基础，plan §3.5）
        self._record_timeline = record_timeline
        self.timeline: Dict[str, List[Dict[str, Any]]] = {"steps": [], "epochs": []}

        # Health 账本：优先注入（测试），否则用独立内存账本（不落盘，避免污染生产 storage）
        if ledger is not None:
            self._ledger = ledger
        else:
            from agents.runtime.health_ledger import HealthLedger
            import tempfile
            from pathlib import Path
            self._ledger = HealthLedger(team_id="__eco_drill__", ledger_dir=Path(tempfile.mkdtemp()))

        self._health_max = health_max
        self._metabolic_rate = metabolic_rate

        # 意图阈值从配置读（配置不可用时回退内置默认）
        from agents.runtime.eco_loop import IntentionThresholds
        try:
            self._thresholds = IntentionThresholds.from_config()
        except Exception:
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
        """一个生境 tick：受限感知（含信号板）→ H/F/L 意图 → 行为表达 → 代谢结算 → 死亡淘汰."""
        from agents.runtime.eco_loop import (
            WorldView, MentalState, IntentionType,
            compute_hunger, compute_fear, compute_libido, generate_intention,
        )

        demand = self.env.demanded_skills[self._step_index % len(self.env.demanded_skills)]
        deaths: List[str] = []
        new_signals: List[Dict[str, Any]] = []
        step_summary: Dict[str, Any] = {
            "step": self._step_index, "demand": demand, "actions": {},
        }
        board = self._signal_board  # 上一 tick 的信号（受限感知窗口）
        food_signals = [s for s in board if s["type"] == "food"]
        help_signals = [s for s in board if s["type"] == "help"]

        # ── 第一阶段：感知 + 意图（全部生物先"想"，再一起"竞"）──
        plans: List[Dict[str, Any]] = []
        for c in self.living():
            hs = self._ledger.get(c.agent_id)
            hunger = compute_hunger(hs.health, hs.health_max)
            recent = c.recent_outcomes[-FEAR_WINDOW:]
            fear = compute_fear(sum(1 for ok in recent if not ok), len(recent), is_blocked=False)
            sustained = 1.0 if (hs.health / max(hs.health_max, 1e-9)) >= 0.7 else 0.0
            libido = compute_libido(hunger, sustained)
            state = MentalState(hunger=hunger, fear=fear, libido=libido)

            can_serve = demand in c.skill_genome
            view = WorldView(
                agent_id=c.agent_id,
                own_backlog=1,
                recent_success_count=sum(1 for ok in recent if ok),
                recent_fail_count=sum(1 for ok in recent if not ok),
                visible_unclaimed_tasks=(1 if can_serve else 0) + len(food_signals),
                visible_peer_count=len(self.living()) - 1,
            )
            intention = generate_intention(state, view, self._thresholds)
            plans.append({"c": c, "hunger": hunger, "can_serve": can_serve,
                          "intention": intention, "outcompeted": False})

        # ── 「物竞」：生态位容量竞争（同一 tick 食物名额有限，plan v2.2 §3.3b）──
        # 竞争力 = 熟练度 + 随机波动；败者本 tick 无法进食且白耗代谢——竞争本身有代价。
        capacity = self.env.niche_capacity
        if capacity > 0:
            contenders = [p for p in plans
                          if p["intention"].type == IntentionType.FORAGE and p["can_serve"]]
            if len(contenders) > capacity:
                contenders.sort(
                    key=lambda p: p["c"].skill_proficiency.get(demand, 0.5)
                    + self._rng.uniform(0, 0.3),
                    reverse=True,
                )
                for loser in contenders[capacity:]:
                    loser["outcompeted"] = True

        # ── 第二阶段：行为表达 + 代谢结算 ──
        for p in plans:
            c = p["c"]
            hunger = p["hunger"]
            can_serve = p["can_serve"]
            intention = p["intention"]

            emitted: List[str] = []
            shared_to: Optional[str] = None
            action_cost = 0.0
            reward = self._pending_rewards.pop(c.agent_id, 0.0)  # 上一 tick 收到的分享
            outcome: Optional[bool] = None  # None=非觅食步(不计入恐惧窗口)

            # ── 行为表达（意图 → 概率化动作，无协作规则分支）──
            if intention.type == IntentionType.FORAGE:
                followed = (not can_serve or self._rng.random() < c.collab_genome.follow_tendency) \
                    and any(s["from"] != c.agent_id for s in food_signals)
                if p["outcompeted"]:
                    # 竞争失败：有能力但没抢到生态位名额（物竞的代价）。
                    # 注意 outcome 保持 None——被挤掉不是能力失败，不入恐惧窗口，
                    # 否则会触发"恐惧螺旋→全员 avoid→集体饿死"的病态吸收态。
                    action_cost += self._econ["forage_miss_penalty"] * 0.75
                elif can_serve:
                    prof = c.skill_proficiency.get(demand, 0.5)
                    p_ok = 0.3 + 0.6 * prof + (self._econ["follow_bonus"] if followed else 0.0)
                    if self._rng.random() < max(0.25, min(0.97, p_ok)):
                        reward += self._econ["forage_gain"] * self.env.abundance
                        outcome = True
                        c.skill_proficiency[demand] = min(0.98, prof + 0.02)  # session 内练熟
                    else:
                        action_cost += self._econ["forage_miss_penalty"]
                        outcome = False
                else:
                    # 基因不匹配生态位：白费力气；若跟随了信号，浪费减半（信息价值）
                    action_cost += self._econ["forage_miss_penalty"] * (0.5 if followed else 1.0)
                    outcome = False
            elif intention.type == IntentionType.AVOID:
                action_cost += self._econ["avoid_cost"]
                # v2.3 恐惧消退：躲藏时最旧的失败记忆逐 tick 淡出。
                # 否则恐惧窗口只在觅食尝试时更新——一旦连败进入 AVOID，窗口冻结、
                # 恐惧永不下降（滞回出口永远达不到），个体锁死在躲藏里活活饿死，
                # 任何丰饶度都救不回来（沙箱实验：全参数组合系统性全灭的真凶）。
                if c.recent_outcomes:
                    c.recent_outcomes.pop(0)
            elif intention.type == IntentionType.MATE:
                # 求偶展示：登记 COURT（epoch 配对依据），发信号有代谢成本
                self._court_log[c.agent_id] = self._step_index
                new_signals.append({"type": "court", "from": c.agent_id, "step": self._step_index})
                emitted.append("COURT")
                action_cost += self._econ["signal_cost"]
            else:  # REST_EXPLORE：静息 + 盲目学习掷骰（世界观 §4：学习是盲目的）
                action_cost += REST_COST
                if self._blind_learning_rate > 0 and self._learning_pool \
                        and self._rng.random() < self._blind_learning_rate:
                    learned = self._rng.choice(self._learning_pool)
                    if learned not in c.skill_genome:
                        c.skill_genome.append(learned)
                        c.skill_proficiency.setdefault(learned, 0.2)
                        emitted.append(f"LEARN@{learned}")

            # ── 信号阶段（倾向概率表达，发信号有成本）──
            if can_serve and self._rng.random() < c.collab_genome.signal_tendency:
                new_signals.append({"type": "food", "skill": demand,
                                    "from": c.agent_id, "step": self._step_index})
                emitted.append(f"FOOD@{demand}")
                action_cost += self._econ["signal_cost"]
            if hunger > self._econ["help_hunger"] and self._rng.random() < c.collab_genome.signal_tendency:
                new_signals.append({"type": "help", "from": c.agent_id, "step": self._step_index})
                emitted.append("HELP")
                action_cost += self._econ["signal_cost"] * 0.5

            # ── 分享（利他基因的表达：让渡收益给求助者，下一 tick 结算）──
            if reward > 0 and help_signals and self._rng.random() < c.collab_genome.share_tendency:
                needy = [s["from"] for s in help_signals if s["from"] != c.agent_id]
                needy = [n for n in needy if n in self._creatures and self._creatures[n].alive]
                if needy:
                    recipient = self._rng.choice(needy)
                    donated = reward * self._econ["share_fraction"]
                    reward -= donated
                    self._pending_rewards[recipient] = self._pending_rewards.get(recipient, 0.0) + donated
                    shared_to = recipient

            # ── 基因携带成本：技能囤积被环境惩罚（世界观 §4）──
            if self._genome_carry_cost > 0:
                action_cost += self._genome_carry_cost * len(c.skill_genome)

            result = self._ledger.tick(c.agent_id, action_cost=action_cost, reward=reward)
            # 只有觅食尝试(成功/失败)才计入恐惧窗口；休息/避险不算"失败"，避免恐惧误升。
            if outcome is not None:
                c.recent_outcomes.append(outcome)
            step_summary["actions"][c.agent_id] = {
                "intention": intention.type.value,
                "can_serve": can_serve,
                "outcome": "outcompeted" if p["outcompeted"] else ("success" if outcome else "miss/idle"),
                "health": round(result.health_after, 2),
                "survival_ticks": result.survival_ticks,
                "signals": emitted,
                "shared_to": shared_to,
            }
            if result.became_dormant:
                c.alive = False
                deaths.append(c.agent_id)

        # ── 环境捕食压力（每 tick 概率事件，plan §3.3）──
        predated: List[str] = []
        if self.env.predator_pressure > 0 and self.living() \
                and self._rng.random() < self.env.predator_pressure:
            target = self._rng.choice(self.living())
            result = self._ledger.tick(target.agent_id, action_cost=20.0, reward=0.0)
            predated.append(target.agent_id)
            if result.became_dormant:
                target.alive = False
                deaths.append(target.agent_id)

        self._signal_board = new_signals
        self._step_index += 1
        step_summary["deaths"] = deaths
        step_summary["predated"] = predated
        step_summary["living"] = len(self.living())
        if self._record_timeline:
            self.timeline["steps"].append(step_summary)
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
                "population": c.population,
                "survival_ticks": hs.survival_ticks if hs else 0,
                "alive": c.alive,
                "generation": c.generation,
                "skill_genome": list(c.skill_genome),
                "collab_genome": c.collab_genome.to_dict(),
                "health": round(hs.health, 2) if hs else 0.0,
            })
        rows.sort(key=lambda r: r["survival_ticks"], reverse=True)
        return rows

    # ── 世代循环（epoch）──
    def run_epoch(self, reproduce_top_k: int = 2, mutation_rate: float = 0.1) -> Dict[str, Any]:
        """一个世代：按生存时长选择 → 择偶配对 → 双基因交叉 → 变异 → 生态位漂移.

        基因抹除（v1 ND-4 语义保留）：只有存活或生存时长排名靠前者进入繁衍；
        死亡个体双基因（skill + collab）均不遗传。
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
                p2 = self._pick_mate(p1, parents)
                child = self._mate_fn(p1, p2, gen)
                if mutation_rate > 0 and self._rng.random() < mutation_rate and self.env.demanded_skills:
                    # 变异（次要探索来源；主要来源是盲目学习）：随机注入一个生态位需求 skill
                    new_skill = self._rng.choice(self.env.demanded_skills)
                    if new_skill not in child.skill_genome:
                        child.skill_genome.append(new_skill)
                offspring.append(child)
                self._creatures[child.agent_id] = child
                self._ledger.get_or_create(child.agent_id, health_max=self._health_max,
                                           metabolic_rate=self._metabolic_rate)

        drift = self._maybe_drift(gen)
        epoch_rec = {
            "generation": gen,
            "parents": [p["agent_id"] for p in parents],
            "offspring": [c.agent_id for c in offspring],
            "offspring_genomes": {c.agent_id: list(c.skill_genome) for c in offspring},
            "offspring_collab": {c.agent_id: c.collab_genome.to_dict() for c in offspring},
            "deaths": [r["agent_id"] for r in ranking if not r["alive"]],
            "drift": drift,
        }
        if self._record_timeline:
            self.timeline["epochs"].append(epoch_rec)
        return epoch_rec

    def _pick_mate(self, p1: Creature, parents: List[Dict[str, Any]]) -> Creature:
        """择偶：候选限于亲本池（保持"后代基因只来自适者"不变式）.

        choosiness 高 → 倾向选池内生存排名最高的异体；低 → 池内随机。
        COURT 登记者优先（求偶展示是有代价的诚实信号）。
        """
        others = [p for p in parents if p["agent_id"] != p1.agent_id]
        if not others:
            return p1
        courted = [p for p in others if p["agent_id"] in self._court_log]
        pool = courted or others
        if self._rng.random() < p1.collab_genome.mate_choosiness:
            chosen = pool[0]  # ranking 已按 survival_ticks 降序
        else:
            chosen = self._rng.choice(pool)
        return self._creatures[chosen["agent_id"]]

    def _maybe_drift(self, gen: int) -> Optional[Dict[str, Any]]:
        """生态位漂移：随机替换一个需求 skill（环境流动，plan §3.3/原则 7）。"""
        if self.env.drift_prob <= 0 or self._rng.random() >= self.env.drift_prob:
            return None
        old = self._rng.choice(self.env.demanded_skills)
        candidates = [s for s in self._learning_pool if s not in self.env.demanded_skills]
        new = self._rng.choice(candidates) if candidates else f"emergent_niche_g{gen}"
        idx = self.env.demanded_skills.index(old)
        self.env.demanded_skills[idx] = new
        if new not in self._learning_pool:
            self._learning_pool.append(new)
        logger.info("⚡ 生态位漂移 gen%d: %s → %s", gen, old, new)
        return {"generation": gen, "removed": old, "added": new}

    # ── 捕食压力手动注入（v1 契约保留：无参调用返回受影响列表）──
    def inject_predator_pressure(self, intensity: float = 0.0) -> List[str]:
        """随机对一个存活生物施加捕食伤害（模拟被捕食），返回被影响的 agent_id 列表.

        intensity>0 时用作触发概率，否则用 PREDATOR_PRESSURE_PROB。
        环境级持续捕食走 EnvState.predator_pressure（step 内自动结算），
        本方法保留给混沌注入/前端按钮等手动通道。
        """
        living = self.living()
        if not living:
            return []
        prob = intensity if intensity > 0 else self.PREDATOR_PRESSURE_PROB
        if self._rng.random() > prob:
            return []
        target = self._rng.choice(living)
        result = self._ledger.tick(target.agent_id, action_cost=20.0, reward=0.0)
        if result.became_dormant:
            target.alive = False
            logger.info("🦅 捕食压力 → %s 被捕食死亡", target.agent_id[:8])
        return [target.agent_id]

    # ── 棘轮锁定世代最优（只进不退）──
    def ratchet_lock(self, team_id: str, best_survival: int, gen: int) -> Dict[str, Any]:
        """把世代最优生存时长写入全局棘轮账本（只进不退）."""
        try:
            from agents.ratchet_ledger import get_ratchet_ledger
            return get_ratchet_ledger().advance(
                metric_key=f"eco_survival:{team_id}",
                value=float(best_survival),
                evidence={"generation": gen, "source": "eco_drill"},
            )
        except Exception as e:  # pragma: no cover - 账本不可用时不阻断
            logger.warning("棘轮锁定失败: %s", e)
            return {"advanced": False, "current": 0.0, "reason": str(e)}

    # ── 基因池快照（v2 语义化：dominant=存活高频 / deprecated=随死者消亡）──
    def gene_pool_snapshot(self) -> Dict[str, Any]:
        """当前基因池：dominant / deprecated / neutral skill 分布 + 协作基因均值."""
        living = self.living()
        living_skills: Dict[str, int] = {}
        dead_skills: Dict[str, int] = {}
        for c in self._creatures.values():
            bucket = living_skills if c.alive else dead_skills
            for skill in c.skill_genome:
                bucket[skill] = bucket.get(skill, 0) + 1

        n_living = max(len(living), 1)
        dominant = [
            {"skill": s, "carriers": n, "freq": round(n / n_living, 3)}
            for s, n in sorted(living_skills.items(), key=lambda kv: -kv[1])
            if n / n_living >= 0.5
        ]
        deprecated = [
            {"skill": s, "carriers": n, "freq": 0.0}
            for s, n in sorted(dead_skills.items(), key=lambda kv: -kv[1])
            if s not in living_skills
        ]
        neutral = [
            {"skill": s, "carriers": n, "freq": round(n / n_living, 3)}
            for s, n in sorted(living_skills.items(), key=lambda kv: -kv[1])
            if n / n_living < 0.5
        ]
        return {
            "dominant": dominant,
            "deprecated": deprecated,
            "neutral": neutral,
            "total_creatures": len(self._creatures),
            "living": len(living),
            "collab_profile": self.collab_profile(),
        }

    def collab_profile(self) -> Dict[str, Any]:
        """种群协作基因画像：存活个体的均值（协作协议被选择的方向读数）。"""
        living = self.living()
        if not living:
            return {"living": 0}
        dims = ["share_tendency", "signal_tendency", "follow_tendency", "mate_choosiness"]
        means = {}
        for d in dims:
            vals = [getattr(c.collab_genome, d) for c in living]
            means[d] = round(sum(vals) / len(vals), 3)
        return {"living": len(living), "means": means}

    def _default_crossover(self, p1: Creature, p2: Creature, generation: int) -> Creature:
        """默认双基因交叉遗传：skill 交叉（复合型 Skill）+ collab 逐维混合变异。"""
        pool = list(dict.fromkeys([*p1.skill_genome, *p2.skill_genome]))
        # skill 交叉：随机取双亲基因的一半以上，保证至少 1 个
        k = max(1, len(pool) // 2 + self._rng.randint(0, len(pool) - len(pool) // 2)) if pool else 0
        genome = self._rng.sample(pool, min(k, len(pool))) if pool else []
        child_id = f"{p1.agent_id[:4]}x{p2.agent_id[:4]}_g{generation}_{self._rng.randint(100, 999)}"
        prof = {}
        for s in genome:
            prof[s] = max(p1.skill_proficiency.get(s, 0.5), p2.skill_proficiency.get(s, 0.5))
        return Creature(
            agent_id=child_id,
            role=p1.role or p2.role,
            population=p1.population or p2.population,   # 后代归属主亲种群
            skill_genome=genome,
            skill_proficiency=prof,
            collab_genome=CollabGenome.crossover(p1.collab_genome, p2.collab_genome, self._rng),
            generation=generation,
            parent_ids=[p1.agent_id, p2.agent_id],
        )

    def population_stats(self) -> Dict[str, Dict[str, Any]]:
        """v2.3 多种群对比：按种群统计 存活/总数/平均与最长生存——团队协作竞争力的读数。"""
        stats: Dict[str, Dict[str, Any]] = {}
        for r in self.survival_ranking():
            pop = r.get("population") or "_default"
            s = stats.setdefault(pop, {"total": 0, "alive": 0, "sum_ticks": 0, "best": 0})
            s["total"] += 1
            s["alive"] += 1 if r["alive"] else 0
            s["sum_ticks"] += r["survival_ticks"]
            s["best"] = max(s["best"], r["survival_ticks"])
        for pop, s in stats.items():
            s["avg_survival_ticks"] = round(s["sum_ticks"] / max(s["total"], 1), 2)
            del s["sum_ticks"]
        return stats


def sample_timeline(timeline: Dict[str, List[Dict[str, Any]]],
                    max_frames: int = TIMELINE_MAX_FRAMES) -> Dict[str, List[Dict[str, Any]]]:
    """timeline 采样到 ≤max_frames 帧（保序；epochs 全保留）。

    v2.3 事件保真采样：死亡/捕食帧**必须保留**——否则 3D 回放里被淘汰的个体
    永远等不到自己的死亡帧，动画与淘汰过程对不上（用户 2026-07-11 反馈）。
    规则：先锁定全部事件帧（deaths/predated 非空），剩余配额在非事件帧上等距分布。
    """
    steps = timeline.get("steps", [])
    if len(steps) > max_frames:
        event_idx = [i for i, s in enumerate(steps)
                     if s.get("deaths") or s.get("predated")]
        event_set = set(event_idx[:max_frames])   # 极端情况下事件帧本身超限则截断
        quota = max_frames - len(event_set)
        plain_idx = [i for i in range(len(steps)) if i not in event_set]
        picked = set(event_set)
        if quota > 0 and plain_idx:
            stride = len(plain_idx) / quota
            for k in range(quota):
                picked.add(plain_idx[int(k * stride)])
        steps = [steps[i] for i in sorted(picked)]
    return {"steps": steps, "epochs": list(timeline.get("epochs", []))}


# ═══════════════════════════════════════════════════════════════
# Trial API 适配层 — 把 EcoDrill 接入 trial_api 的演练路由
# ═══════════════════════════════════════════════════════════════


async def _generate_cat_commentary(gen_rec: Dict[str, Any]) -> str:
    """XB-3.1: 猫解说——ChatHarness 可用时 LLM 生成 ≤30 字拟态播报；否则降级模板.

    降级模板：`第N代·存活X·最佳Y ticks·新生Z·棘轮↑/=`
    """
    fallback = "第{g}代·存活{l}·最佳{b} ticks·新生{n}·棘轮{r}".format(
        g=gen_rec.get("generation", 0), l=gen_rec.get("living", 0),
        b=gen_rec.get("best_survival_ticks", 0), n=gen_rec.get("births", 0),
        r="↑" if gen_rec.get("ratchet_advanced") else "=",
    )
    try:
        from agents.chat_harness import get_chat_harness
        harness = get_chat_harness()
        prompt = (
            "你是数字办公室里的猫解说员小虎。用不超过30个汉字、拟猫语气播报这段自然选择世代摘要，"
            "不要标点堆砌：" + fallback
        )
        reply = await harness.chat(prompt)  # type: ignore[misc]
        text = (reply or "").strip() if isinstance(reply, str) else ""
        return text[:60] if text else fallback
    except Exception:
        return fallback


def _habitat_params() -> Dict[str, Any]:
    """从 eco_runtime_config 读生产生境参数（缺配置时用保守内置默认）。"""
    params: Dict[str, Any] = {
        "health_max": 100.0, "metabolic_rate": 1.0,
        "blind_learning_rate": 0.1, "genome_carry_cost": 0.05,
        "drift_prob": 0.3, "predator_pressure": 0.08, "abundance": 1.0,
        "niche_capacity": 3,
        "economics": {},
    }
    try:
        from agents.runtime.eco_runtime_config import get_eco_runtime_config
        cfg = get_eco_runtime_config()
        meta = cfg.get_section("metabolism")
        learn = cfg.get_section("learning")
        hab = cfg.get_section("habitat")
        params.update({
            "health_max": float(meta.get("health_max", 100.0)),
            "metabolic_rate": float(meta.get("metabolic_rate", 1.0)),
            "blind_learning_rate": float(learn.get("blind_learning_rate", 0.1)),
            "genome_carry_cost": float(learn.get("genome_carry_cost", 0.05)),
            "drift_prob": float(hab.get("drift_prob", 0.3)),
            "predator_pressure": float(hab.get("predator_pressure", 0.08)),
            "abundance": float(hab.get("abundance", 1.0)),
            "niche_capacity": int(hab.get("niche_capacity", 2)),
            "economics": dict(cfg.get_section("drill_economics")),
        })
    except Exception as e:  # pragma: no cover - 配置不可用不阻断
        logger.warning("habitat 配置读取失败，用内置默认: %s", e)
    return params


async def run_drill_via_trial(
    trial_id: str,
    branch_id: str,
    session_id: str,
    team_id: str,
    max_steps: int = 150,
    max_generations: int = 3,
    on_step: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_epoch: Optional[Callable[[Dict[str, Any]], None]] = None,
    mate_fn: Optional[Callable[[Creature, Creature, int], Creature]] = None,
    write_lineage: bool = False,
    extra_team_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """trial_api.branch_run 调用的入口：从团队构建 creatures → 跑多代生境 → 返回结果 + timeline.

    on_step/on_epoch（XB-2.1 SSE 直播）：每步/每世代回调，供 trial_api 推 ECO_STEP/ECO_EPOCH 事件；
    回调异常不阻断演练。timeline 回放作为无 SSE 时的兜底（plan §3.5）。
    mate_fn/write_lineage（XB-4.1）：可注入 team_manager.mate 作繁衍实现；
    write_lineage=True 时后代谱系写回 AgentProfile.metadata.lineage（source="eco_drill"），
    默认 False——演练不动真身。
    """
    import asyncio

    def _safe(cb: Optional[Callable[[Dict[str, Any]], None]], payload: Dict[str, Any]) -> None:
        if cb is None:
            return
        try:
            cb(payload)
        except Exception as e:  # pragma: no cover - 观测层不阻塞业务
            logger.debug("eco_drill 事件回调失败: %s", e)

    # 从团队构建 creatures
    try:
        from agents.api import _team_manager
    except Exception:
        _team_manager = None
    if _team_manager is None:
        return {"error": "team_manager_not_ready", "trial_id": trial_id}

    # v2.3 多种群同场竞争：主团队 + 对比种群共同入场（同一生境、同一生态位、同一淘汰规则）
    team_ids: List[str] = [team_id] + [t for t in (extra_team_ids or []) if t and t != team_id]
    creatures: List[Creature] = []
    all_skills: List[str] = []
    loaded_teams: List[str] = []
    for tid in team_ids:
        team = _team_manager.get_team(tid)
        if team is None:
            if tid == team_id:
                return {"error": "team_not_found", "team_id": tid}
            logger.warning("对比种群 %s 不存在，跳过", tid)
            continue
        loaded_teams.append(tid)
        # 收集生态位需求：优先团队级 skill，不足时从 agent skill 汇总
        team_skills = list(team.skills.keys()) if team.skills else []
        agents = team.agents.values() if isinstance(team.agents, dict) else (team.agents or [])
        for agent in agents:
            if not team_skills:
                all_skills.extend(agent.skills or [])
            creatures.append(Creature(
                agent_id=agent.agent_id,
                role=agent.role,
                population=tid,
                skill_genome=list(agent.skills) if agent.skills else [],
                skill_proficiency={s: 0.5 for s in (agent.skills or [])},
            ))
        all_skills.extend(team_skills)
    all_skills = list(set(all_skills)) or ["generic"]
    if not creatures:
        return {"error": "no_creatures", "trial_id": trial_id}

    hp = _habitat_params()
    drill = EcoDrill(
        creatures=creatures,
        demanded_skills=all_skills,
        health_max=hp["health_max"],
        metabolic_rate=hp["metabolic_rate"],
        blind_learning_rate=hp["blind_learning_rate"],
        genome_carry_cost=hp["genome_carry_cost"],
        drift_prob=hp["drift_prob"],
        predator_pressure=hp["predator_pressure"],
        abundance=hp["abundance"],
        niche_capacity=int(hp.get("niche_capacity", 0)),
        economics=hp.get("economics") or None,
        mate_fn=mate_fn,
    )

    # 多代演化
    generations: List[Dict[str, Any]] = []
    prev_best = -1

    for gen in range(max_generations):
        # 逐步推进（每步回调 SSE；每 10 步让出事件循环）
        steps_executed = 0
        for i in range(max_steps):
            if drill.is_extinct():
                break
            step_summary = drill.step()
            # v2.3: 世代号直接盖在帧上（step() 返回的是 timeline 中同一 dict 对象，
            # 因此 timeline 帧也带上 generation——回放的世代边界不再靠均分猜测）
            step_summary["generation"] = gen
            steps_executed += 1
            _safe(on_step, step_summary)
            if i % 10 == 9:
                await asyncio.sleep(0)
        run_result = {
            "steps_executed": steps_executed,
            "extinct": drill.is_extinct(),
            "ranking": drill.survival_ranking(),
        }
        ranking = run_result.get("ranking", [])

        if ranking:
            best_survival = ranking[0].get("survival_ticks", 0)
            avg_survival = sum(r.get("survival_ticks", 0) for r in ranking) / len(ranking)
        else:
            best_survival = 0
            avg_survival = 0.0

        ratchet_result = drill.ratchet_lock(team_id, best_survival, gen)

        births = 0
        drift = None
        if not drill.is_extinct() and len(drill.living()) >= 2:
            epoch_result = drill.run_epoch(reproduce_top_k=2, mutation_rate=0.15)
            births = len(epoch_result.get("offspring", []))
            drift = epoch_result.get("drift")
            _safe(on_epoch, {**epoch_result, "gen_index": gen})

        gen_rec = {
            "generation": gen,
            "steps_executed": run_result.get("steps_executed", 0),
            "extinct": run_result.get("extinct", False),
            "living": len(drill.living()),
            "avg_survival_ticks": round(avg_survival, 2),
            "best_survival_ticks": best_survival,
            "births": births,
            "drift": drift,
            "ratchet_advanced": ratchet_result.get("advanced", False),
            "ratchet_value": ratchet_result.get("current", 0.0),
        }
        # v2.3 多种群：每代记录各种群统计（前端世代曲线做种群对比）
        gen_rec["population_stats"] = drill.population_stats()
        # XB-3.1: 猫解说（LLM 可用时拟态播报，否则降级模板）
        gen_rec["cat_commentary"] = await _generate_cat_commentary(gen_rec)
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

        await asyncio.sleep(0)  # 让出事件循环

    # XB-4.1: 谱系落盘（默认关闭——演练不动真身）
    lineage_records: List[Dict[str, Any]] = []
    for c in drill._creatures.values():
        if c.generation > 0 and c.parent_ids:
            lineage_records.append({
                "child": c.agent_id, "parents": list(c.parent_ids),
                "generation": c.generation, "skill_genome": list(c.skill_genome),
                "source": "eco_drill", "trial_id": trial_id,
            })
    if write_lineage and lineage_records:
        try:
            for rec in lineage_records:
                agent_obj = None
                try:
                    agent_obj = _team_manager.get_agent(rec["child"])  # type: ignore[union-attr]
                except Exception:
                    agent_obj = None
                if agent_obj is not None and hasattr(agent_obj, "metadata"):
                    meta = agent_obj.metadata or {}
                    meta.setdefault("lineage", []).append(rec)
                    agent_obj.metadata = meta
        except Exception as e:  # pragma: no cover
            logger.warning("lineage 写回失败（不阻断）: %s", e)

    return {
        "trial_id": trial_id,
        "drill_kind": "natural_selection",
        "generations": generations,
        "final_ranking": drill.survival_ranking(),
        "gene_pool": drill.gene_pool_snapshot(),
        "collab_profile": drill.collab_profile(),
        "env": drill.env.to_dict(),
        "populations": loaded_teams,
        "population_stats": drill.population_stats(),
        "timeline": sample_timeline(drill.timeline),
        "lineage": lineage_records,
        "lineage_written": bool(write_lineage and lineage_records),
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
