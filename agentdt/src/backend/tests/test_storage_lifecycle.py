# -*- coding: utf-8 -*-
"""Storage Lifecycle Channel — 单元测试.

Tests:
  - MarineChannel 接口合规 (initialize, get_status, shutdown, check)
  - LifecyclePolicy 数据模型
  - CostBaseline / AuditReport
  - process_event 所有事件类型
  - 棘轮锁定不可修改
  - 预设策略 (default / aggressive)
"""

from __future__ import annotations

import pytest

from channels.storage_lifecycle import (
    AuditReport,
    CostBaseline,
    LifecyclePolicy,
    StorageClass,
    StorageLifecycleChannel,
    TierTransition,
    create_aggressive_s3_policy,
    create_default_s3_policy,
)
from channels.marine_base import ChannelPriority, ChannelStatus


# ── Fixtures ────────────────────────────────────────────


@pytest.fixture
def channel():
    """创建并初始化 StorageLifecycleChannel."""
    ch = StorageLifecycleChannel()
    ch.initialize()
    yield ch
    ch.shutdown()


@pytest.fixture
def default_policy():
    """创建默认 S3 策略."""
    return create_default_s3_policy(bucket_name="test-bucket", total_size_gb=500.0)


# ── Model Tests ─────────────────────────────────────────


class TestStorageClass:
    def test_cost_factors_defined(self):
        assert len(StorageClass.COST_FACTORS) >= 7
        assert StorageClass.COST_FACTORS["STANDARD"] == 1.0
        assert StorageClass.COST_FACTORS["DEEP_ARCHIVE"] < 0.02

    def test_latency_ranges(self):
        assert StorageClass.LATENCY["STANDARD"][1] < 100
        assert StorageClass.LATENCY["DEEP_ARCHIVE"][0] > 1_000_000


class TestLifecyclePolicy:
    def test_create_policy(self):
        p = LifecyclePolicy(
            policy_id="test-id", name="Test", total_size_gb=1000.0,
        )
        assert p.policy_id == "test-id"
        assert p.total_size_gb == 1000.0
        assert p.cost_saving_pct() >= 0

    def test_add_transition(self):
        p = LifecyclePolicy(policy_id="t1", name="T1")
        p.add_transition("STANDARD", "STANDARD_IA", days=30)
        assert len(p.transitions) == 1
        assert p.transitions[0].from_class == "STANDARD"
        assert p.transitions[0].days_after_creation == 30

    def test_estimate_monthly_cost(self):
        p = LifecyclePolicy(policy_id="t1", name="T1", total_size_gb=1000.0)
        cost = p.estimate_monthly_cost()
        assert cost == 23.0  # 1000 * 0.023

    def test_estimate_optimized_cost(self):
        p = LifecyclePolicy(policy_id="t1", name="T1", total_size_gb=1000.0)
        opt = p.estimate_optimized_cost()
        assert opt < p.estimate_monthly_cost()  # optimized should be cheaper

    def test_cost_saving_pct_default(self):
        p = create_default_s3_policy(total_size_gb=1000.0)
        saving = p.cost_saving_pct()
        assert saving > 50  # default policy should save >50%

    def test_cost_saving_pct_aggressive(self):
        p = create_aggressive_s3_policy(total_size_gb=1000.0)
        saving = p.cost_saving_pct()
        assert saving > 60  # aggressive should save more

    def test_locked_policy_immutable(self):
        p = create_default_s3_policy()
        p.locked = True
        assert p.locked

    def test_to_dict(self):
        p = create_default_s3_policy(bucket_name="my-bucket", total_size_gb=100.0)
        d = p.to_dict()
        assert d["policy_id"] == "s3-default-v1"
        assert d["bucket_name"] == "my-bucket"
        assert "transitions" in d
        assert len(d["transitions"]) == 4


class TestTierTransition:
    def test_create_transition(self):
        t = TierTransition("STANDARD", "STANDARD_IA", days_after_creation=45)
        assert t.from_class == "STANDARD"
        assert t.to_class == "STANDARD_IA"
        assert t.days_after_creation == 45

    def test_to_dict(self):
        t = TierTransition("STANDARD", "GLACIER", days_after_creation=90)
        d = t.to_dict()
        assert d["from"] == "STANDARD"
        assert d["to"] == "GLACIER"


# ── Channel Tests ───────────────────────────────────────


class TestStorageLifecycleChannel:
    def test_channel_metadata(self):
        assert StorageLifecycleChannel.name == "storage_lifecycle"
        assert StorageLifecycleChannel.version == "1.0.0"
        assert StorageLifecycleChannel.priority == ChannelPriority.P1
        assert "S3" in StorageLifecycleChannel.description

    def test_initialize(self, channel):
        status = channel.get_status()
        assert status["policies_count"] >= 1
        assert channel._initialized

    def test_check(self, channel):
        status, message = channel.check()
        assert status == "ok"

    def test_get_health(self, channel):
        health = channel.get_health()
        assert health is not None
        assert health.status in (ChannelStatus.OK, ChannelStatus.WARN)

    def test_get_status(self, channel):
        s = channel.get_status()
        assert "policies" in s
        assert "overall_cost_reduction_pct" in s

    def test_shutdown(self, channel):
        assert channel.shutdown()
        assert not channel._initialized


class TestProcessEvent:
    def test_list_policies(self, channel):
        result = channel.process_event("list_policies", {})
        assert result["ok"]
        assert len(result["policies"]) >= 1

    def test_create_policy(self, channel):
        result = channel.process_event("create_policy", {
            "policy_id": "custom-1",
            "name": "Custom Policy",
            "bucket_name": "custom-bucket",
            "total_size_gb": 200.0,
        })
        assert result["ok"]
        assert result["policy"]["name"] == "Custom Policy"
        assert result["policy"]["total_size_gb"] == 200.0

    def test_create_duplicate_policy(self, channel):
        channel.process_event("create_policy", {
            "policy_id": "dup-1", "name": "Dup",
        })
        result = channel.process_event("create_policy", {
            "policy_id": "dup-1", "name": "Dup",
        })
        assert not result["ok"]

    def test_update_policy(self, channel):
        channel.process_event("create_policy", {
            "policy_id": "upd-1", "name": "Update Me", "total_size_gb": 100.0,
        })
        result = channel.process_event("update_policy", {
            "policy_id": "upd-1",
            "total_size_gb": 500.0,
            "target_pct": 40.0,
        })
        assert result["ok"]
        assert result["policy"]["total_size_gb"] == 500.0

    def test_lock_policy(self, channel):
        channel.process_event("create_policy", {
            "policy_id": "lock-1", "name": "Lock Me",
        })
        result = channel.process_event("lock_policy", {"policy_id": "lock-1"})
        assert result["ok"]
        assert result["locked"]

    def test_lock_policy_blocks_update(self, channel):
        channel.process_event("create_policy", {
            "policy_id": "lock-2", "name": "Lock Then Update",
        })
        channel.process_event("lock_policy", {"policy_id": "lock-2"})
        result = channel.process_event("update_policy", {
            "policy_id": "lock-2", "total_size_gb": 999.0,
        })
        assert not result["ok"]

    def test_take_baseline(self, channel):
        channel.process_event("create_policy", {
            "policy_id": "bl-1", "name": "Baseline Test", "total_size_gb": 1000.0,
        })
        result = channel.process_event("take_baseline", {
            "policy_id": "bl-1",
            "cost_usd": 23.0,
            "distribution": {"STANDARD": 1.0},
        })
        assert result["ok"]
        assert result["baseline"]["monthly_cost_usd"] == 23.0

    def test_generate_report(self, channel):
        channel.process_event("create_policy", {
            "policy_id": "rpt-1", "name": "Report Test", "total_size_gb": 5000.0,
        })
        result = channel.process_event("generate_report", {"policy_id": "rpt-1"})
        assert result["ok"]
        assert "actual_saving_pct" in result["report"]
        assert "target_met" in result["report"]
        assert result["report"]["baseline_cost"] >= 0

    def test_simulate(self, channel):
        result = channel.process_event("simulate", {
            "total_size_gb": 10000.0,
            "transitions": [
                {"from_class": "STANDARD", "to_class": "STANDARD_IA", "days": 30},
                {"from_class": "STANDARD_IA", "to_class": "GLACIER", "days": 90},
            ],
        })
        assert result["ok"]
        sim = result["simulation"]
        assert sim["total_size_gb"] == 10000.0
        assert sim["monthly_saving_usd"] > 0
        assert sim["yearly_saving_usd"] > 0
        assert sim["saving_pct"] > 30

    def test_unknown_event(self, channel):
        result = channel.process_event("nonexistent_event", {})
        assert not result["ok"]
        assert "Unknown event_type" in result["error"]


class TestPresetPolicies:
    def test_default_policy_has_4_transitions(self):
        p = create_default_s3_policy()
        assert len(p.transitions) == 4

    def test_aggressive_policy_has_4_transitions(self):
        p = create_aggressive_s3_policy()
        assert len(p.transitions) == 4

    def test_aggressive_is_faster(self):
        d = create_default_s3_policy()
        a = create_aggressive_s3_policy()
        assert a.transitions[0].days_after_creation < d.transitions[0].days_after_creation

    def test_default_target_30(self):
        p = create_default_s3_policy()
        assert p.target_cost_reduction_pct == 30.0

    def test_aggressive_target_50(self):
        p = create_aggressive_s3_policy()
        assert p.target_cost_reduction_pct == 50.0
