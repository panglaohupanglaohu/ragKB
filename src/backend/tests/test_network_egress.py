# -*- coding: utf-8 -*-
"""Network Egress Channel — 单元测试.

Tests:
  - MarineChannel 接口合规
  - CDNConfig / VPCEndpointConfig 数据模型
  - EgressBaseline / EgressAuditReport
  - process_event (add_cdn, add_vpc_endpoint, take_baseline, generate_report)
  - estimate_nat_savings / estimate_cdn_savings 工具函数
"""

from __future__ import annotations

import pytest

from channels.network_egress import (
    CDNConfig,
    EgressAuditReport,
    EgressBaseline,
    EgressType,
    NetworkEgressChannel,
    VPCEndpointConfig,
    estimate_cdn_savings,
    estimate_nat_savings,
)
from channels.marine_base import ChannelPriority, ChannelStatus


# ── Fixtures ────────────────────────────────────────────


@pytest.fixture
def channel():
    """创建并初始化 NetworkEgressChannel."""
    ch = NetworkEgressChannel()
    ch.initialize()
    yield ch
    ch.shutdown()


# ── Model Tests ─────────────────────────────────────────


class TestEgressType:
    def test_cost_per_gb(self):
        assert "nat_gateway" in EgressType.COST_PER_GB
        assert "cloudfront" in EgressType.COST_PER_GB
        assert EgressType.COST_PER_GB["s3_public"] == 0.0

    def test_endpoint_hourly(self):
        assert "s3_vpc_endpoint" in EgressType.ENDPOINT_HOURLY
        assert EgressType.ENDPOINT_HOURLY["s3_vpc_endpoint"] == 0.01


class TestCDNConfig:
    def test_create(self):
        c = CDNConfig(cdn_id="cdn-1", provider="cloudfront")
        assert c.cdn_id == "cdn-1"
        assert c.provider == "cloudfront"
        assert c.cache_ttl_seconds == 86400

    def test_to_dict(self):
        c = CDNConfig(cdn_id="cdn-1", origin_domain="cdn.example.com")
        d = c.to_dict()
        assert d["cdn_id"] == "cdn-1"
        assert d["origin_domain"] == "cdn.example.com"


class TestVPCEndpointConfig:
    def test_create(self):
        v = VPCEndpointConfig(endpoint_id="vpce-1", service="s3")
        assert v.endpoint_id == "vpce-1"
        assert v.service == "s3"

    def test_to_dict(self):
        v = VPCEndpointConfig(endpoint_id="vpce-1", region="ap-east-1")
        d = v.to_dict()
        assert d["endpoint_id"] == "vpce-1"
        assert d["region"] == "ap-east-1"


class TestEgressBaseline:
    def test_create(self):
        b = EgressBaseline(
            baseline_id="bl-1",
            total_monthly_gb=1000.0,
            total_monthly_cost=90.0,
        )
        assert b.baseline_id == "bl-1"
        assert b.total_monthly_cost == 90.0

    def test_to_dict(self):
        b = EgressBaseline(baseline_id="bl-1", total_monthly_gb=500.0)
        d = b.to_dict()
        assert "created_at" in d


class TestEgressAuditReport:
    def test_create(self):
        r = EgressAuditReport(
            report_id="rpt-1",
            baseline_cost=100.0,
            current_cost=80.0,
            optimized_cost=60.0,
            total_saving_pct=40.0,
        )
        assert r.report_id == "rpt-1"
        assert r.total_saving_pct == 40.0

    def test_to_dict(self):
        r = EgressAuditReport(report_id="rpt-1")
        d = r.to_dict()
        assert d["report_id"] == "rpt-1"
        assert "recommendations" in d


# ── Utility Function Tests ──────────────────────────────


class TestEstimateNATSavings:
    def test_typical_10tb(self):
        result = estimate_nat_savings(10000.0)
        assert result["nat_total_usd"] > 0
        assert result["vpc_endpoint_total_usd"] > 0
        assert result["monthly_saving_usd"] > 0
        assert result["yearly_saving_usd"] > result["monthly_saving_usd"]
        assert result["saving_pct"] > 0

    def test_zero_data(self):
        result = estimate_nat_savings(0.0)
        assert result["nat_total_usd"] == 32.85  # hourly cost only
        assert result["vpc_endpoint_total_usd"] == 7.3


class TestEstimateCDNSavings:
    def test_typical_5tb(self):
        result = estimate_cdn_savings(5000.0)
        assert result["current_monthly_usd"] > 0
        assert result["optimized_monthly_usd"] > 0
        assert result["monthly_saving_usd"] > 0
        assert result["saving_pct"] > 40

    def test_zero(self):
        result = estimate_cdn_savings(0.0)
        assert result["current_monthly_usd"] == 0.0


# ── Channel Tests ───────────────────────────────────────


class TestNetworkEgressChannel:
    def test_channel_metadata(self):
        assert NetworkEgressChannel.name == "network_egress"
        assert NetworkEgressChannel.version == "1.0.0"
        assert NetworkEgressChannel.priority == ChannelPriority.P1
        assert "CDN" in NetworkEgressChannel.description

    def test_initialize(self, channel):
        assert channel._initialized
        status = channel.get_status()
        assert status["cdn_count"] >= 1
        assert status["vpc_endpoint_count"] >= 1

    def test_get_status(self, channel):
        s = channel.get_status()
        assert "cdns" in s
        assert "vpc_endpoints" in s

    def test_shutdown(self, channel):
        assert channel.shutdown()
        assert not channel._initialized

    def test_check(self, channel):
        status, message = channel.check()
        assert status == "ok"

    def test_get_total_monthly_cost(self, channel):
        cost = channel.get_total_monthly_cost()
        assert cost >= 0


class TestProcessEvent:
    def test_list_all(self, channel):
        result = channel.process_event("list_all", {})
        assert result["ok"]
        assert "cdns" in result
        assert "vpc_endpoints" in result

    def test_add_cdn(self, channel):
        result = channel.process_event("add_cdn", {
            "cdn_id": "test-cdn",
            "provider": "cloudflare",
            "origin_domain": "test.example.com",
            "monthly_gb": 1000.0,
        })
        assert result["ok"]
        assert result["cdn"]["cdn_id"] == "test-cdn"
        assert result["cdn"]["estimated_monthly_cost_usd"] > 0

    def test_add_cdn_duplicate(self, channel):
        channel.process_event("add_cdn", {"cdn_id": "dup-cdn"})
        result = channel.process_event("add_cdn", {"cdn_id": "dup-cdn"})
        assert not result["ok"]

    def test_update_cdn(self, channel):
        channel.process_event("add_cdn", {
            "cdn_id": "upd-cdn", "monthly_gb": 500.0,
        })
        result = channel.process_event("update_cdn", {
            "cdn_id": "upd-cdn",
            "cache_ttl_seconds": 3600,
            "compress_enabled": True,
        })
        assert result["ok"]
        assert result["cdn"]["cache_ttl_seconds"] == 3600

    def test_add_vpc_endpoint(self, channel):
        result = channel.process_event("add_vpc_endpoint", {
            "endpoint_id": "test-vpce",
            "service": "s3",
            "monthly_gb": 5000.0,
            "vpc_id": "vpc-abc123",
        })
        assert result["ok"]
        assert result["vpc_endpoint"]["service"] == "s3"
        assert result["vpc_endpoint"]["estimated_monthly_cost_usd"] > 0

    def test_update_vpc_endpoint(self, channel):
        channel.process_event("add_vpc_endpoint", {
            "endpoint_id": "upd-vpce", "service": "s3",
        })
        result = channel.process_event("update_vpc_endpoint", {
            "endpoint_id": "upd-vpce",
            "monthly_gb": 10000.0,
        })
        assert result["ok"]

    def test_take_baseline(self, channel):
        result = channel.process_event("take_baseline", {
            "total_monthly_gb": 15000.0,
            "breakdown": {
                "nat_gateway": 8000.0,
                "s3_public": 5000.0,
                "cloudfront": 2000.0,
            },
        })
        assert result["ok"]
        assert result["baseline"]["total_monthly_gb"] == 15000.0
        assert result["baseline"]["total_monthly_cost"] > 0

    def test_generate_report(self, channel):
        # Add CDN and VPC to have data
        channel.process_event("add_cdn", {
            "cdn_id": "rpt-cdn", "monthly_gb": 5000.0,
        })
        channel.process_event("add_vpc_endpoint", {
            "endpoint_id": "rpt-vpce", "service": "s3", "monthly_gb": 10000.0,
        })
        result = channel.process_event("generate_report", {
            "baseline_cost": 500.0,
            "target_pct": 30.0,
        })
        assert result["ok"]
        report = result["report"]
        assert report["baseline_cost"] == 500.0
        assert "cdn_savings" in report
        assert "vpc_endpoint_savings" in report
        assert "recommendations" in report

    def test_generate_report_no_data(self, channel):
        # Clear defaults and generate report
        channel._cdn_configs.clear()
        channel._vpc_endpoints.clear()
        result = channel.process_event("generate_report", {
            "baseline_cost": 100.0,
        })
        assert result["ok"]
        assert len(result["report"]["issues"]) > 0  # no CDN/VPC configured

    def test_estimate_nat_to_vpc(self, channel):
        result = channel.process_event("estimate_nat_to_vpc", {
            "data_transfer_gb": 10000.0,
        })
        assert result["ok"]
        assert result["monthly_saving_usd"] > 300

    def test_estimate_cdn(self, channel):
        result = channel.process_event("estimate_cdn", {
            "monthly_gb": 5000.0,
        })
        assert result["ok"]
        assert result["monthly_saving_usd"] > 100

    def test_unknown_event(self, channel):
        result = channel.process_event("bad_event", {})
        assert not result["ok"]
