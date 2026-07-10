# -*- coding: utf-8 -*-
"""Eco Loop — 生态运行时基座：感知 · H/F/L 生理状态 · 意图仲裁.

对应 docs/Agent仿生生态运行时plan.md §1~2, §7。

核心立场：Agent 不是为了执行任务而存在，任务执行是它在环境中觅食/避险/协作的
副产品。本模块只负责"感知 → 生理状态更新 → 意图仲裁"这一段决策链路，
不执行任何真实动作（执行动作是上层调用方的职责，如 PetEcosystem/chat_harness）。

硬约束（plan §7 自组织分工）：
    `perceive()` 的实现只能返回该 Agent 自身可见范围内的摘要信息
    （WorldView 里不允许出现"全局最优分配"或"其他 Agent 完整状态快照"字段）。
    分工必须是多个 Agent 各自独立 tick 的涌现结果，不能由外部裁决者指定。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# 感知快照（局部视野，不含全局信息）
# ═══════════════════════════════════════════════════════════════


@dataclass
class WorldView:
    """Agent 的局部感知快照 — 只包含"该 Agent 自己可见"的摘要信息.

    硬约束：这里的字段必须都是"以该 Agent 为中心"的局部信息。
    不允许添加类似 all_agents_global_state / optimal_assignment 之类的字段。
    """

    agent_id: str = ""
    # 自己的待处理/进行中任务数量与紧迫度（不是全局任务队列）
    own_backlog: int = 0
    own_deadline_urgency: float = 0.0
    # 近期（窗口内）自己相关的成功/失败计数
    recent_success_count: int = 0
    recent_fail_count: int = 0
    # 自己当前是否处于阻塞状态
    is_blocked: bool = False
    # 自己可见的、尚未被分配的任务数（可觅食资源，不是全局最优解）
    visible_unclaimed_tasks: int = 0
    # 附近协作伙伴的摘要计数（不是完整状态，只是数量与角色标签）
    visible_peer_count: int = 0
    visible_peer_roles: List[str] = field(default_factory=list)
    # 资源约束
    token_budget_used_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "own_backlog": self.own_backlog,
            "own_deadline_urgency": self.own_deadline_urgency,
            "recent_success_count": self.recent_success_count,
            "recent_fail_count": self.recent_fail_count,
            "is_blocked": self.is_blocked,
            "visible_unclaimed_tasks": self.visible_unclaimed_tasks,
            "visible_peer_count": self.visible_peer_count,
            "visible_peer_roles": list(self.visible_peer_roles),
            "token_budget_used_ratio": self.token_budget_used_ratio,
        }


# ═══════════════════════════════════════════════════════════════
# 生理状态 H/F/L（plan §2）
# ═══════════════════════════════════════════════════════════════


@dataclass
class MentalState:
    """三个生理驱动变量，均 ∈ [0, 1]."""

    hunger: float = 0.0
    fear: float = 0.0
    libido: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {"hunger": self.hunger, "fear": self.fear, "libido": self.libido}


def compute_hunger(health: float, health_max: float) -> float:
    """H = 1 - health/health_max. health<=0 时恒为 1；health_max<=0 时恒为 1（防御性兜底）."""
    if health_max <= 0:
        return 1.0
    ratio = max(0.0, min(1.0, health / health_max))
    return round(1.0 - ratio, 6)


def compute_fear(recent_fail_count: int, recent_total: int, is_blocked: bool) -> float:
    """F = min(1, fail_rate + blocked_bonus).

    recent_total<=0（无近期记录）时 fail_rate 记 0，仅由 is_blocked 贡献。
    """
    fail_rate = 0.0
    if recent_total > 0:
        fail_rate = recent_fail_count / recent_total
    blocked_bonus = 0.5 if is_blocked else 0.0
    return round(min(1.0, fail_rate + blocked_bonus), 6)


def compute_libido(hunger: float, health_sustained_ratio: float, saturation: float = 1.0) -> float:
    """L = max(0, saturation - hunger) * health_sustained_ratio.

    hunger 越高，libido 越被压制（hunger>=saturation 时 libido=0）。
    health_sustained_ratio ∈ [0,1] 表示"持续处于饱暖状态"的程度（由上层传入，
    例如最近 N tick 里 health 高于阈值的比例），本函数不负责统计窗口计算。
    """
    base = max(0.0, saturation - hunger)
    ratio = max(0.0, min(1.0, health_sustained_ratio))
    return round(base * ratio, 6)


# ═══════════════════════════════════════════════════════════════
# 意图（头等公民）
# ═══════════════════════════════════════════════════════════════


class IntentionType(str, Enum):
    AVOID = "avoid"                # 恐惧压倒一切：避险/求助/降级
    FORAGE = "forage"               # 饥饿驱动觅食：认领/执行任务
    MATE = "mate"                   # 温饱后的交配意图
    REST_EXPLORE = "rest_explore"   # 空闲：盲目学习探索 or 静息


@dataclass
class Intention:
    type: IntentionType
    priority: float = 0.0
    target: Optional[str] = None
    memory: Optional["Intention"] = None  # 单项短期记忆：被打断的上一个意图

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "priority": self.priority,
            "target": self.target,
            "has_memory": self.memory is not None,
        }


# ═══════════════════════════════════════════════════════════════
# 意图仲裁配置（阈值可被进化/沙箱扰动，参照 pet_ecosystem 的默认合并模式）
# ═══════════════════════════════════════════════════════════════


@dataclass
class IntentionThresholds:
    fear_escape: float = 0.55
    fear_calm: float = 0.35       # 滞回：恐惧降到此值以下才允许离开 avoid
    hunger_threshold: float = 0.4
    libido_threshold: float = 0.6

    @classmethod
    def from_config(cls) -> "IntentionThresholds":
        """从 EcoRuntimeConfig 的 mental_state 段读取当前生效阈值.

        配置不可用时回退到内置默认（不破坏无配置环境/单元测试）。
        """
        try:
            from .eco_runtime_config import get_eco_runtime_config
            s = get_eco_runtime_config().get_section("mental_state")
            return cls(
                fear_escape=float(s.get("fear_escape", 0.55)),
                fear_calm=float(s.get("fear_calm", 0.35)),
                hunger_threshold=float(s.get("hunger_threshold", 0.4)),
                libido_threshold=float(s.get("libido_threshold", 0.6)),
            )
        except Exception:
            return cls()


def generate_intention(
    state: MentalState,
    view: WorldView,
    thresholds: IntentionThresholds,
    previous: Optional[Intention] = None,
) -> Intention:
    """H/F/L 三变量仲裁：avoid > forage > mate > rest_explore.

    带滞回 + 单项短期记忆防抖（参照 pet-behavior.js 的 avoid 打断/恢复设计）：
    - 若上一个意图是 avoid 且当前 fear 还没降到 fear_calm 以下，继续 avoid（不抖动）。
    - avoid 解除时，如果被打断前有记忆意图，优先恢复记忆而不是直接掉回 rest_explore。
    """
    # 滞回：仍在 avoid 状态且 fear 未降到 calm 阈值以下 → 继续 avoid
    if previous is not None and previous.type == IntentionType.AVOID and state.fear >= thresholds.fear_calm:
        return Intention(type=IntentionType.AVOID, priority=state.fear, memory=previous.memory)

    if state.fear > thresholds.fear_escape:
        # 打断：把当前候选意图压入 memory，供恐惧解除后恢复
        memory = previous if (previous is not None and previous.type != IntentionType.AVOID) else (
            previous.memory if previous is not None else None
        )
        return Intention(type=IntentionType.AVOID, priority=state.fear, memory=memory)

    # 恐惧已解除：若之前被打断，优先恢复记忆意图（避免直接掉回 rest_explore 抖动）
    if previous is not None and previous.type == IntentionType.AVOID and previous.memory is not None:
        restored = previous.memory
        return Intention(type=restored.type, priority=restored.priority, target=restored.target)

    if state.hunger > thresholds.hunger_threshold:
        target = "unclaimed_task" if view.visible_unclaimed_tasks > 0 else None
        return Intention(type=IntentionType.FORAGE, priority=state.hunger, target=target)

    if state.libido > thresholds.libido_threshold:
        return Intention(type=IntentionType.MATE, priority=state.libido)

    return Intention(type=IntentionType.REST_EXPLORE, priority=0.0)


# ═══════════════════════════════════════════════════════════════
# IntentionAgent 基类
# ═══════════════════════════════════════════════════════════════


class IntentionAgent:
    """感知 → 生理状态 → 意图仲裁 的基类.

    子类需重写 `perceive(ctx)`；`tick()` 本身不执行任何真实动作，
    只产出 Intention 供上层调用方（PetEcosystem/eco_loop 的执行侧）分派。
    """

    def __init__(
        self,
        agent_id: str,
        thresholds: Optional[IntentionThresholds] = None,
    ) -> None:
        self.agent_id = agent_id
        self.thresholds = thresholds or IntentionThresholds()
        self.mental_state = MentalState()
        self.intention: Optional[Intention] = None
        # 基因型：skill_id 集合（复用 AgentProfile.skills 语义，此处独立持有便于测试）
        self.skill_genome: List[str] = []

    def perceive(self, ctx: Any) -> WorldView:
        """子类重写：只返回局部感知信息，不得包含全局最优解."""
        raise NotImplementedError

    def update_mental_state(self, view: WorldView, health: float, health_max: float,
                             health_sustained_ratio: float = 0.0) -> MentalState:
        """用感知信息 + 当前健康值更新 H/F/L（纯函数组合，无副作用地写回 self.mental_state）."""
        hunger = compute_hunger(health, health_max)
        recent_total = view.recent_success_count + view.recent_fail_count
        fear = compute_fear(view.recent_fail_count, recent_total, view.is_blocked)
        libido = compute_libido(hunger, health_sustained_ratio)
        self.mental_state = MentalState(hunger=hunger, fear=fear, libido=libido)
        return self.mental_state

    def generate_intention(self, view: WorldView) -> Intention:
        """基于当前 mental_state 仲裁意图（带单项记忆防抖）."""
        previous = self.intention
        intention = generate_intention(self.mental_state, view, self.thresholds, previous)
        self.intention = intention
        return intention

    def tick(self, ctx: Any, health: float, health_max: float,
              health_sustained_ratio: float = 0.0) -> Intention:
        """感知 → 生理状态更新 → 意图仲裁。不执行动作，返回 Intention 供上层分派。"""
        view = self.perceive(ctx)
        self.update_mental_state(view, health, health_max, health_sustained_ratio)
        return self.generate_intention(view)
