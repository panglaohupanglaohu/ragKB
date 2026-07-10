# -*- coding: utf-8 -*-
"""探索期衰减曲线测试.

对应 docs/Agent仿生生态运行时todos.md P3-1。
"""

from __future__ import annotations

import pytest

from sandbox.twin_loop import compute_exploration_rate


class TestExplorationDecay:
    def test_zero_ticks_returns_base_rate(self):
        assert compute_exploration_rate(0, base_rate=0.7, half_life=50) == pytest.approx(0.7)

    def test_negative_ticks_returns_base_rate(self):
        assert compute_exploration_rate(-5, base_rate=0.7, half_life=50) == pytest.approx(0.7)

    def test_half_life_tick_halves_rate(self):
        assert compute_exploration_rate(50, base_rate=0.7, half_life=50) == pytest.approx(0.35)

    def test_two_half_lives_quarters_rate(self):
        assert compute_exploration_rate(100, base_rate=0.7, half_life=50) == pytest.approx(0.175)

    def test_monotonically_decreasing(self):
        rates = [compute_exploration_rate(t, base_rate=0.7, half_life=50) for t in range(0, 300, 10)]
        for a, b in zip(rates, rates[1:]):
            assert b <= a

    def test_clamped_to_zero_one_range(self):
        rate = compute_exploration_rate(10, base_rate=1.5, half_life=50)  # 异常输入 base_rate>1
        assert 0.0 <= rate <= 1.0

    def test_zero_half_life_defensive_fallback(self):
        # half_life<=0 是异常配置，防御性返回 base_rate，不除零崩溃
        assert compute_exploration_rate(10, base_rate=0.7, half_life=0) == pytest.approx(0.7)

    def test_default_parameters_usable(self):
        # 不传 base_rate/half_life 时用模块默认值，函数应正常工作
        rate = compute_exploration_rate(50)
        assert 0.0 <= rate <= 1.0
