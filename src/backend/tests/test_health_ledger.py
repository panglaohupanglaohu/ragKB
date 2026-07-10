# -*- coding: utf-8 -*-
"""Health Ledger 测试 — 代谢消耗/回血/dormant 转换/持久化.

对应 docs/Agent仿生生态运行时todos.md P2-1。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agents.runtime.health_ledger import HealthLedger, HealthState


@pytest.fixture
def tmp_ledger():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield HealthLedger(team_id="test-team", ledger_dir=Path(tmpdir))


class TestMetabolismWithoutIncome:
    def test_pure_metabolism_eventually_dormant(self, tmp_ledger: HealthLedger):
        """纯代谢无产出，N tick 后必然 dormant."""
        tmp_ledger.get_or_create("agent-1", health_max=10.0, metabolic_rate=1.0)
        became_dormant_at = None
        for i in range(1, 30):
            result = tmp_ledger.tick("agent-1")
            if result.became_dormant:
                became_dormant_at = i
                break
        assert became_dormant_at is not None
        assert tmp_ledger.get("agent-1").status == "dormant"

    def test_health_never_negative(self, tmp_ledger: HealthLedger):
        tmp_ledger.get_or_create("agent-1", health_max=5.0, metabolic_rate=2.0)
        for _ in range(20):
            tmp_ledger.tick("agent-1")
        assert tmp_ledger.get("agent-1").health >= 0.0


class TestRewardOffsetsMetabolism:
    def test_task_reward_offsets_metabolism(self, tmp_ledger: HealthLedger):
        """任务回血能抵消代谢，health 保持在合理范围（不必然走向 0）."""
        tmp_ledger.get_or_create("agent-1", health_max=100.0, metabolic_rate=1.0)
        for _ in range(50):
            # 每 tick 完成任务获得等于代谢的回报 → 应大致持平
            tmp_ledger.tick("agent-1", action_cost=0.0, reward=1.0)
        state = tmp_ledger.get("agent-1")
        assert state.status == "active"
        assert state.health == pytest.approx(100.0)  # clamp 到 health_max，不会溢出

    def test_positive_net_gain_keeps_agent_alive_longer(self, tmp_ledger: HealthLedger):
        tmp_ledger.get_or_create("agent-2", health_max=20.0, metabolic_rate=1.0)
        for _ in range(15):
            tmp_ledger.tick("agent-2", reward=1.5)  # 净收益为正
        assert tmp_ledger.get("agent-2").status == "active"
        assert tmp_ledger.get("agent-2").health > 0.0


class TestSurvivalTicksFreezeAtDormant:
    def test_survival_ticks_stop_growing_after_dormant(self, tmp_ledger: HealthLedger):
        tmp_ledger.get_or_create("agent-1", health_max=3.0, metabolic_rate=1.0)
        for _ in range(3):
            tmp_ledger.tick("agent-1")
        assert tmp_ledger.get("agent-1").status == "dormant"
        frozen_ticks = tmp_ledger.get("agent-1").survival_ticks

        # 继续 tick 不应再增加 survival_ticks（定格）
        for _ in range(5):
            result = tmp_ledger.tick("agent-1")
            assert result.became_dormant is False

        assert tmp_ledger.get("agent-1").survival_ticks == frozen_ticks

    def test_became_dormant_flag_only_fires_once(self, tmp_ledger: HealthLedger):
        tmp_ledger.get_or_create("agent-1", health_max=2.0, metabolic_rate=1.0)
        results = [tmp_ledger.tick("agent-1") for _ in range(5)]
        dormant_flags = [r.became_dormant for r in results]
        assert dormant_flags.count(True) == 1


class TestRevive:
    def test_revive_resets_to_partial_health(self, tmp_ledger: HealthLedger):
        tmp_ledger.get_or_create("agent-1", health_max=10.0, metabolic_rate=5.0)
        tmp_ledger.tick("agent-1")
        tmp_ledger.tick("agent-1")
        assert tmp_ledger.get("agent-1").status == "dormant"

        revived = tmp_ledger.revive("agent-1", revive_ratio=0.5)
        assert revived.status == "active"
        assert revived.health == pytest.approx(5.0)

    def test_revive_unknown_agent_returns_none(self, tmp_ledger: HealthLedger):
        assert tmp_ledger.revive("nonexistent") is None


class TestPersistence:
    def test_save_and_reload_state_consistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            ledger1 = HealthLedger(team_id="persist-team", ledger_dir=path)
            ledger1.get_or_create("agent-1", health_max=50.0, metabolic_rate=2.0)
            ledger1.tick("agent-1", reward=1.0)
            ledger1.tick("agent-1", reward=1.0)
            ledger1.save()

            ledger2 = HealthLedger(team_id="persist-team", ledger_dir=path)
            reloaded = ledger2.get("agent-1")
            original = ledger1.get("agent-1")
            assert reloaded is not None
            assert reloaded.health == pytest.approx(original.health)
            assert reloaded.survival_ticks == original.survival_ticks
            assert reloaded.health_max == pytest.approx(50.0)


class TestSustainedRatio:
    def test_sustained_ratio_one_when_above_threshold(self, tmp_ledger: HealthLedger):
        tmp_ledger.get_or_create("agent-1", health_max=100.0)
        assert tmp_ledger.sustained_ratio("agent-1", saturation_threshold=0.7) == 1.0

    def test_sustained_ratio_zero_when_below_threshold(self, tmp_ledger: HealthLedger):
        tmp_ledger.get_or_create("agent-1", health_max=100.0, metabolic_rate=50.0)
        tmp_ledger.tick("agent-1")  # health 从 100 掉到 50 → ratio=0.5 < 0.7
        assert tmp_ledger.sustained_ratio("agent-1", saturation_threshold=0.7) == 0.0

    def test_sustained_ratio_unknown_agent_is_zero(self, tmp_ledger: HealthLedger):
        assert tmp_ledger.sustained_ratio("ghost") == 0.0
