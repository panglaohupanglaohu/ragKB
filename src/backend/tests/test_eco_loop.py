# -*- coding: utf-8 -*-
"""Eco Loop 基座测试 — H/F/L 生理状态纯函数 + 意图仲裁 + 局部感知约束.

对应 docs/Agent仿生生态运行时todos.md P1-1。
"""

from __future__ import annotations

import dataclasses

import pytest

from agents.runtime.eco_loop import (
    Intention,
    IntentionAgent,
    IntentionThresholds,
    IntentionType,
    MentalState,
    WorldView,
    compute_fear,
    compute_hunger,
    compute_libido,
    generate_intention,
)


class TestMentalStateFormulas:
    """三个纯函数的边界值测试."""

    def test_hunger_zero_when_full_health(self):
        assert compute_hunger(100.0, 100.0) == 0.0

    def test_hunger_one_when_health_zero(self):
        assert compute_hunger(0.0, 100.0) == 1.0

    def test_hunger_half(self):
        assert compute_hunger(50.0, 100.0) == 0.5

    def test_hunger_defensive_when_health_max_zero(self):
        # health_max<=0 是异常配置，防御性返回 1（视为已饿死）
        assert compute_hunger(10.0, 0.0) == 1.0

    def test_hunger_clamped_when_overhealed(self):
        # health > health_max 的异常情况不应产生负值 hunger
        assert compute_hunger(150.0, 100.0) == 0.0

    def test_fear_zero_when_no_history_and_not_blocked(self):
        assert compute_fear(0, 0, False) == 0.0

    def test_fear_from_fail_rate(self):
        assert compute_fear(3, 10, False) == pytest.approx(0.3)

    def test_fear_blocked_bonus(self):
        assert compute_fear(0, 0, True) == 0.5

    def test_fear_capped_at_one(self):
        assert compute_fear(10, 10, True) == 1.0

    def test_libido_suppressed_by_high_hunger(self):
        # hunger=1（饿死边缘）时 libido 恒为 0，不管 health_sustained_ratio 多高
        assert compute_libido(hunger=1.0, health_sustained_ratio=1.0) == 0.0

    def test_libido_positive_when_low_hunger_and_sustained_health(self):
        val = compute_libido(hunger=0.1, health_sustained_ratio=1.0)
        assert val == pytest.approx(0.9)

    def test_libido_zero_when_never_sustained(self):
        val = compute_libido(hunger=0.0, health_sustained_ratio=0.0)
        assert val == 0.0


class TestIntentionArbitration:
    """意图仲裁优先级：avoid > forage > mate > rest_explore."""

    def _thresholds(self) -> IntentionThresholds:
        return IntentionThresholds(fear_escape=0.55, fear_calm=0.35, hunger_threshold=0.4, libido_threshold=0.6)

    def test_fear_triggers_avoid(self):
        state = MentalState(hunger=0.9, fear=0.8, libido=0.0)
        view = WorldView(agent_id="a1")
        intention = generate_intention(state, view, self._thresholds())
        assert intention.type == IntentionType.AVOID

    def test_hunger_triggers_forage_when_no_fear(self):
        state = MentalState(hunger=0.6, fear=0.1, libido=0.0)
        view = WorldView(agent_id="a1", visible_unclaimed_tasks=2)
        intention = generate_intention(state, view, self._thresholds())
        assert intention.type == IntentionType.FORAGE
        assert intention.target == "unclaimed_task"

    def test_libido_triggers_mate_when_satiated_and_calm(self):
        state = MentalState(hunger=0.1, fear=0.05, libido=0.7)
        view = WorldView(agent_id="a1")
        intention = generate_intention(state, view, self._thresholds())
        assert intention.type == IntentionType.MATE

    def test_default_rest_explore(self):
        state = MentalState(hunger=0.1, fear=0.05, libido=0.1)
        view = WorldView(agent_id="a1")
        intention = generate_intention(state, view, self._thresholds())
        assert intention.type == IntentionType.REST_EXPLORE

    def test_hunger_beats_libido(self):
        # 两者都超阈值时 forage 优先于 mate
        state = MentalState(hunger=0.6, fear=0.1, libido=0.7)
        view = WorldView(agent_id="a1")
        intention = generate_intention(state, view, self._thresholds())
        assert intention.type == IntentionType.FORAGE

    def test_avoid_hysteresis_stays_until_calm(self):
        """恐惧降到 escape 阈值以下但还没到 calm 阈值时，应继续 avoid（防抖）."""
        thresholds = self._thresholds()
        state_high_fear = MentalState(hunger=0.1, fear=0.8, libido=0.0)
        view = WorldView(agent_id="a1")
        first = generate_intention(state_high_fear, view, thresholds)
        assert first.type == IntentionType.AVOID

        # fear 降到 0.4（低于 escape=0.55 但高于 calm=0.35）→ 仍应保持 avoid
        state_mid_fear = MentalState(hunger=0.1, fear=0.4, libido=0.0)
        second = generate_intention(state_mid_fear, view, thresholds, previous=first)
        assert second.type == IntentionType.AVOID

    def test_avoid_interrupt_and_restore_memory(self):
        """avoid 打断 forage 后，恐惧解除应恢复 forage，而不是直接掉回 rest_explore."""
        thresholds = self._thresholds()
        view = WorldView(agent_id="a1", visible_unclaimed_tasks=1)

        # Step 1: 正常觅食
        forage_state = MentalState(hunger=0.6, fear=0.1, libido=0.0)
        forage_intention = generate_intention(forage_state, view, thresholds)
        assert forage_intention.type == IntentionType.FORAGE

        # Step 2: 突然恐惧升高，打断觅食 → avoid，记忆里存着 forage
        fear_state = MentalState(hunger=0.6, fear=0.9, libido=0.0)
        avoid_intention = generate_intention(fear_state, view, thresholds, previous=forage_intention)
        assert avoid_intention.type == IntentionType.AVOID
        assert avoid_intention.memory is not None
        assert avoid_intention.memory.type == IntentionType.FORAGE

        # Step 3: 恐惧降到 calm 以下 → 应恢复 forage，不是掉回 rest_explore
        calm_state = MentalState(hunger=0.6, fear=0.1, libido=0.0)
        restored = generate_intention(calm_state, view, thresholds, previous=avoid_intention)
        assert restored.type == IntentionType.FORAGE


class TestIntentionAgentTick:
    """IntentionAgent 基类的 tick 闭环."""

    class _FixedViewAgent(IntentionAgent):
        def __init__(self, agent_id: str, view: WorldView):
            super().__init__(agent_id)
            self._view = view

        def perceive(self, ctx):
            return self._view

    def test_tick_produces_intention_without_side_effects(self):
        view = WorldView(agent_id="fish-1", visible_unclaimed_tasks=1)
        agent = self._FixedViewAgent("fish-1", view)
        intention = agent.tick(ctx=None, health=20.0, health_max=100.0)
        # health=20/100 → hunger=0.8 → 应触发 forage（无恐惧无阻塞）
        assert intention.type == IntentionType.FORAGE
        assert agent.mental_state.hunger == pytest.approx(0.8)

    def test_perceive_not_implemented_on_base_class(self):
        base = IntentionAgent(agent_id="base")
        with pytest.raises(NotImplementedError):
            base.perceive(ctx=None)


class TestLocalPerceptionConstraint:
    """硬约束校验：WorldView 不应包含任何"全局"字段（自组织分工的架构前提）."""

    def test_world_view_has_no_global_fields(self):
        field_names = {f.name for f in dataclasses.fields(WorldView)}
        forbidden_markers = ("global", "all_agents", "optimal", "assignment")
        for name in field_names:
            lowered = name.lower()
            for marker in forbidden_markers:
                assert marker not in lowered, (
                    f"WorldView 字段 '{name}' 疑似包含全局信息标记 '{marker}'，"
                    "违反局部感知约束（plan §7）"
                )

    def test_world_view_to_dict_is_agent_scoped(self):
        view = WorldView(agent_id="a1", visible_peer_count=3, visible_peer_roles=["b", "c"])
        d = view.to_dict()
        # 只应包含摘要计数/角色标签，不应包含其他 agent 的完整状态
        assert d["visible_peer_count"] == 3
        assert "visible_peer_roles" in d
        assert all(isinstance(r, str) for r in d["visible_peer_roles"])
