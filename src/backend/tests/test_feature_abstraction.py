# -*- coding: utf-8 -*-
"""特征抽象触发条件测试（Health 净收益驱动 skill 提炼建议）.

对应 docs/Agent仿生生态运行时todos.md P3-2。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agents.runtime.health_ledger import HealthLedger, should_solidify


@pytest.fixture
def tmp_ledger():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield HealthLedger(team_id="feature-test", ledger_dir=Path(tmpdir))


def _mock_usage(agent_id: str, skill_name: str, reward_delta: float) -> dict:
    return {"agent_id": agent_id, "skill_name": skill_name, "reward_delta": reward_delta}


class TestNetGainBySkill:
    def test_positive_net_gain_aggregation(self, tmp_ledger: HealthLedger):
        records = [
            _mock_usage("a1", "coding", 1.0),
            _mock_usage("a1", "coding", 0.5),
            _mock_usage("a1", "coding", -0.2),
            _mock_usage("a1", "review", 5.0),   # 不同 skill，不应计入
            _mock_usage("a2", "coding", 3.0),   # 不同 agent，不应计入
        ]
        result = tmp_ledger.net_gain_by_skill("a1", "coding", records)
        assert result["usage_count"] == 3
        assert result["net_gain"] == pytest.approx(1.3)
        assert result["avg_gain"] == pytest.approx(1.3 / 3)

    def test_no_matching_records_returns_zero(self, tmp_ledger: HealthLedger):
        result = tmp_ledger.net_gain_by_skill("ghost", "nothing", [])
        assert result["usage_count"] == 0
        assert result["net_gain"] == 0.0
        assert result["avg_gain"] == 0.0

    def test_negative_net_gain(self, tmp_ledger: HealthLedger):
        records = [
            _mock_usage("a1", "coding", -1.0),
            _mock_usage("a1", "coding", -0.5),
        ]
        result = tmp_ledger.net_gain_by_skill("a1", "coding", records)
        assert result["net_gain"] == pytest.approx(-1.5)


class TestShouldSolidify:
    def test_true_when_positive_gain_and_enough_uses(self):
        assert should_solidify(net_gain=2.0, usage_count=10, min_uses=5, min_gain=0.0) is True

    def test_false_when_usage_count_below_min(self):
        assert should_solidify(net_gain=2.0, usage_count=3, min_uses=5, min_gain=0.0) is False

    def test_false_when_net_gain_negative(self):
        assert should_solidify(net_gain=-0.5, usage_count=10, min_uses=5, min_gain=0.0) is False

    def test_false_when_net_gain_below_min_gain_threshold(self):
        assert should_solidify(net_gain=0.05, usage_count=10, min_uses=5, min_gain=0.1) is False

    def test_boundary_usage_count_equal_to_min(self):
        assert should_solidify(net_gain=1.0, usage_count=5, min_uses=5, min_gain=0.0) is True

    def test_end_to_end_with_ledger(self, tmp_ledger: HealthLedger):
        """整合：先聚合净收益，再判定是否建议提炼."""
        records = [_mock_usage("a1", "coding", 0.8) for _ in range(6)]
        gain_info = tmp_ledger.net_gain_by_skill("a1", "coding", records)
        assert should_solidify(gain_info["net_gain"], gain_info["usage_count"]) is True

        # 反例：使用次数够但净收益转负
        bad_records = [_mock_usage("a1", "coding", -0.5) for _ in range(6)]
        bad_gain = tmp_ledger.net_gain_by_skill("a1", "coding", bad_records)
        assert should_solidify(bad_gain["net_gain"], bad_gain["usage_count"]) is False
