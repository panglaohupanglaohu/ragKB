# -*- coding: utf-8 -*-
"""
Network Egress Optimization Channel — CDN/VPC Endpoint 配置标准化

实现网络出口成本优化管理:
  - CDN (CloudFront/Cloudflare) 缓存策略优化
  - VPC Endpoint (S3/DynamoDB) 路由优化
  - NAT Gateway → VPC Endpoint 迁移成本分析
  - 网络出口费用审计报告

Architecture:
  NetworkEgressChannel (MarineChannel)
    ├── EgressConfig           — 出口配置
    ├── CDNConfig              — CDN 配置
    ├── VPCEndpointConfig      — VPC Endpoint 配置
    └── EgressAuditReport      — 出口费用审计报告
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .marine_base import (
    ChannelHealth,
    ChannelMetrics,
    ChannelPriority,
    ChannelStatus,
    MarineChannel,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════

class EgressType:
    """出口流量类型."""

    NAT_GATEWAY = "nat_gateway"
    INTERNET_GATEWAY = "internet_gateway"
    S3_PUBLIC = "s3_public"
    S3_VPC_ENDPOINT = "s3_vpc_endpoint"
    DYNAMODB_PUBLIC = "dynamodb_public"
    DYNAMODB_VPC_ENDPOINT = "dynamodb_vpc_endpoint"
    CLOUDFRONT = "cloudfront"
    CLOUDFLARE = "cloudflare"
    DIRECT_CONNECT = "direct_connect"
    TRANSIT_GATEWAY = "transit_gateway"

    # 出口成本系数 ($/GB, 估算)
    COST_PER_GB: Dict[str, float] = {
        "nat_gateway": 0.045,
        "internet_gateway": 0.09,
        "s3_public": 0.00,  # 同 region S3 免费，跨 region $0.02/GB
        "s3_cross_region": 0.02,
        "s3_vpc_endpoint": 0.01,
        "dynamodb_public": 0.00,
        "dynamodb_vpc_endpoint": 0.01,
        "cloudfront": 0.085,
        "cloudflare": 0.05,
        "direct_connect": 0.02,
        "transit_gateway": 0.02,
        "data_transfer_out": 0.09,  # 通用出站
    }

    # VPC Endpoint 小时费 ($/hour)
    ENDPOINT_HOURLY: Dict[str, float] = {
        "s3_vpc_endpoint": 0.01,
        "dynamodb_vpc_endpoint": 0.01,
    }


@dataclass
class CDNConfig:
    """CDN 配置."""

    cdn_id: str
    provider: str = "cloudfront"  # cloudfront, cloudflare, akamai
    origin_domain: str = ""
    cache_ttl_seconds: int = 86400  # 默认 24h
    compress_enabled: bool = True
    minify_enabled: bool = False
    enabled: bool = True
    estimated_monthly_gb: float = 0.0
    estimated_monthly_cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cdn_id": self.cdn_id,
            "provider": self.provider,
            "origin_domain": self.origin_domain,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "compress_enabled": self.compress_enabled,
            "minify_enabled": self.minify_enabled,
            "enabled": self.enabled,
            "estimated_monthly_gb": self.estimated_monthly_gb,
            "estimated_monthly_cost_usd": self.estimated_monthly_cost_usd,
        }


@dataclass
class VPCEndpointConfig:
    """VPC Endpoint 配置."""

    endpoint_id: str
    service: str = "s3"  # s3, dynamodb, ecr, ecs, ...
    endpoint_type: str = "gateway"  # gateway, interface
    region: str = "us-east-1"
    vpc_id: str = ""
    route_table_ids: List[str] = field(default_factory=list)
    enabled: bool = True
    estimated_monthly_gb: float = 0.0
    estimated_monthly_cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint_id": self.endpoint_id,
            "service": self.service,
            "endpoint_type": self.endpoint_type,
            "region": self.region,
            "vpc_id": self.vpc_id,
            "route_table_ids": self.route_table_ids,
            "enabled": self.enabled,
            "estimated_monthly_gb": self.estimated_monthly_gb,
            "estimated_monthly_cost_usd": self.estimated_monthly_cost_usd,
        }


@dataclass
class EgressBaseline:
    """网络出口基线."""

    baseline_id: str
    created_at: datetime = field(default_factory=datetime.now)
    total_monthly_gb: float = 0.0
    total_monthly_cost: float = 0.0
    breakdown: Dict[str, float] = field(default_factory=dict)  # egress_type → cost
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "created_at": self.created_at.isoformat(),
            "total_monthly_gb": self.total_monthly_gb,
            "total_monthly_cost": self.total_monthly_cost,
            "breakdown": self.breakdown,
            "notes": self.notes,
        }


@dataclass
class EgressAuditReport:
    """网络出口费用审计报告."""

    report_id: str
    created_at: datetime = field(default_factory=datetime.now)
    baseline_cost: float = 0.0
    current_cost: float = 0.0
    optimized_cost: float = 0.0
    cdn_savings: float = 0.0
    vpc_endpoint_savings: float = 0.0
    total_saving_pct: float = 0.0
    target_saving_pct: float = 30.0
    target_met: bool = False
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at.isoformat(),
            "baseline_cost": self.baseline_cost,
            "current_cost": self.current_cost,
            "optimized_cost": self.optimized_cost,
            "cdn_savings": self.cdn_savings,
            "vpc_endpoint_savings": self.vpc_endpoint_savings,
            "total_saving_pct": self.total_saving_pct,
            "target_saving_pct": self.target_saving_pct,
            "target_met": self.target_met,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


# ═══════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════

def estimate_nat_savings(data_transfer_gb: float) -> Dict[str, float]:
    """估算 NAT Gateway → VPC Endpoint 迁移节省.

    NAT Gateway: $0.045/GB 数据处理 + $0.045/h 小时费
    VPC Endpoint: $0.01/GB 数据处理 + $0.01/h 小时费

    典型场景: 10TB/month 数据经 NAT 访问 S3
    """
    nat_data_cost = data_transfer_gb * 0.045
    nat_hourly = 0.045 * 730  # ~$32.85/m
    nat_total = nat_data_cost + nat_hourly

    vpc_data_cost = data_transfer_gb * 0.01
    vpc_hourly = 0.01 * 730  # ~$7.30/m
    vpc_total = vpc_data_cost + vpc_hourly

    return {
        "nat_total_usd": round(nat_total, 2),
        "vpc_endpoint_total_usd": round(vpc_total, 2),
        "monthly_saving_usd": round(nat_total - vpc_total, 2),
        "yearly_saving_usd": round((nat_total - vpc_total) * 12, 2),
        "saving_pct": round((1 - vpc_total / nat_total) * 100, 1) if nat_total > 0 else 0.0,
    }


def estimate_cdn_savings(monthly_gb: float,
                          current_cost_per_gb: float = 0.09,
                          optimized_cost_per_gb: float = 0.05) -> Dict[str, float]:
    """估算 CDN 迁移节省."""
    current = monthly_gb * current_cost_per_gb
    optimized = monthly_gb * optimized_cost_per_gb
    return {
        "current_monthly_usd": round(current, 2),
        "optimized_monthly_usd": round(optimized, 2),
        "monthly_saving_usd": round(current - optimized, 2),
        "yearly_saving_usd": round((current - optimized) * 12, 2),
        "saving_pct": round((1 - optimized / current) * 100, 1) if current > 0 else 0.0,
    }


# ═══════════════════════════════════════════════════════════
# Network Egress Channel
# ═══════════════════════════════════════════════════════════

class NetworkEgressChannel(MarineChannel):
    """网络出口优化 Channel.

    管理 CDN 和 VPC Endpoint 配置，追踪出口费用，
    产出网络出口费用审计报告。
    """

    name: str = "network_egress"
    description: str = (
        "网络出口优化 — CDN 缓存策略 + VPC Endpoint 路由优化 + "
        "出口费用审计报告"
    )
    version: str = "1.0.0"
    priority: ChannelPriority = ChannelPriority.P1
    dependencies: List[str] = []

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._cdn_configs: Dict[str, CDNConfig] = {}
        self._vpc_endpoints: Dict[str, VPCEndpointConfig] = {}
        self._baselines: List[EgressBaseline] = []
        self._audit_reports: List[EgressAuditReport] = []
        self._initialized = False
        self._event_counter: int = 0

    # ── MarineChannel 接口 ──────────────────────────────────

    def initialize(self) -> bool:
        """初始化网络出口 Channel."""
        try:
            # 加载默认 CDN 配置
            default_cdn = CDNConfig(
                cdn_id="cdn-default",
                provider="cloudfront",
                origin_domain="api.agentsgroup.example.com",
                cache_ttl_seconds=3600,
                compress_enabled=True,
            )
            self._cdn_configs[default_cdn.cdn_id] = default_cdn

            # 加载默认 VPC Endpoint 配置
            default_vpc = VPCEndpointConfig(
                endpoint_id="vpc-s3-default",
                service="s3",
                endpoint_type="gateway",
                region="us-east-1",
            )
            self._vpc_endpoints[default_vpc.endpoint_id] = default_vpc

            self._initialized = True
            self._set_health(ChannelStatus.OK,
                             f"已加载 {len(self._cdn_configs)} CDN + "
                             f"{len(self._vpc_endpoints)} VPC Endpoint")
            logger.info("NetworkEgressChannel 初始化完成")
            return True
        except Exception as e:
            self._set_health(ChannelStatus.ERROR, f"初始化失败: {e}")
            logger.exception("NetworkEgressChannel 初始化异常")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取 Channel 运行状态."""
        cdn_status = [
            {"cdn_id": c.cdn_id, "provider": c.provider, "enabled": c.enabled}
            for c in self._cdn_configs.values()
        ]
        vpc_status = [
            {"endpoint_id": e.endpoint_id, "service": e.service, "enabled": e.enabled}
            for e in self._vpc_endpoints.values()
        ]

        return {
            "name": self.name,
            "version": self.version,
            "priority": self.priority.name,
            "cdn_count": len(self._cdn_configs),
            "vpc_endpoint_count": len(self._vpc_endpoints),
            "baselines_count": len(self._baselines),
            "reports_count": len(self._audit_reports),
            "cdns": cdn_status,
            "vpc_endpoints": vpc_status,
            "event_counter": self._event_counter,
        }

    def shutdown(self) -> bool:
        """关闭 Channel."""
        logger.info("NetworkEgressChannel 关闭")
        self._initialized = False
        return True

    # ── 事件处理 ──────────────────────────────────────────

    def process_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """处理网络出口管理事件.

        支持的事件:
          - add_cdn: 添加 CDN 配置
          - update_cdn: 更新 CDN 配置
          - add_vpc_endpoint: 添加 VPC Endpoint
          - update_vpc_endpoint: 更新 VPC Endpoint
          - take_baseline: 记录出口流量基线
          - generate_report: 生成审计报告
          - estimate_nat_to_vpc: NAT→VPC 迁移估算
          - estimate_cdn: CDN 迁移估算
          - list_all: 列出所有配置
        """
        self._event_counter += 1

        handlers = {
            "add_cdn": self._handle_add_cdn,
            "update_cdn": self._handle_update_cdn,
            "add_vpc_endpoint": self._handle_add_vpc_endpoint,
            "update_vpc_endpoint": self._handle_update_vpc_endpoint,
            "take_baseline": self._handle_take_baseline,
            "generate_report": self._handle_generate_report,
            "estimate_nat_to_vpc": self._handle_estimate_nat_to_vpc,
            "estimate_cdn": self._handle_estimate_cdn,
            "list_all": self._handle_list_all,
        }

        handler = handlers.get(event_type)
        if handler is None:
            return {"ok": False, "error": f"Unknown event_type: {event_type}"}

        try:
            result = handler(payload)
            self._metrics.calls_total += 1
            self._metrics.calls_success += 1
            return {"ok": True, "event": event_type, **result}
        except Exception as e:
            self._metrics.calls_total += 1
            self._metrics.calls_failed += 1
            logger.exception(f"事件处理失败: {event_type}")
            return {"ok": False, "error": str(e)}

    # ── CDN 处理器 ────────────────────────────────────────

    def _handle_add_cdn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cdn_id = payload["cdn_id"]
        if cdn_id in self._cdn_configs:
            raise ValueError(f"CDN 已存在: {cdn_id}")

        cdn = CDNConfig(
            cdn_id=cdn_id,
            provider=payload.get("provider", "cloudfront"),
            origin_domain=payload.get("origin_domain", ""),
            cache_ttl_seconds=payload.get("cache_ttl_seconds", 86400),
            compress_enabled=payload.get("compress_enabled", True),
            minify_enabled=payload.get("minify_enabled", False),
            estimated_monthly_gb=payload.get("monthly_gb", 0.0),
        )
        cdn.estimated_monthly_cost_usd = round(
            cdn.estimated_monthly_gb * EgressType.COST_PER_GB.get(cdn.provider, 0.09), 2
        )
        self._cdn_configs[cdn_id] = cdn
        return {"cdn": cdn.to_dict()}

    def _handle_update_cdn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cdn_id = payload["cdn_id"]
        cdn = self._cdn_configs.get(cdn_id)
        if cdn is None:
            raise ValueError(f"CDN 不存在: {cdn_id}")

        for field_name in ("cache_ttl_seconds", "compress_enabled",
                           "minify_enabled", "origin_domain", "enabled",
                           "estimated_monthly_gb"):
            if field_name in payload:
                setattr(cdn, field_name, payload[field_name])

        cdn.estimated_monthly_cost_usd = round(
            cdn.estimated_monthly_gb * EgressType.COST_PER_GB.get(cdn.provider, 0.09), 2
        )
        return {"cdn": cdn.to_dict()}

    # ── VPC Endpoint 处理器 ────────────────────────────────

    def _handle_add_vpc_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        endpoint_id = payload["endpoint_id"]
        if endpoint_id in self._vpc_endpoints:
            raise ValueError(f"VPC Endpoint 已存在: {endpoint_id}")

        service = payload.get("service", "s3")
        endpoint = VPCEndpointConfig(
            endpoint_id=endpoint_id,
            service=service,
            endpoint_type=payload.get("endpoint_type", "gateway"),
            region=payload.get("region", "us-east-1"),
            vpc_id=payload.get("vpc_id", ""),
            route_table_ids=payload.get("route_table_ids", []),
            estimated_monthly_gb=payload.get("monthly_gb", 0.0),
        )

        # 估算月成本 = 数据处理费 + 小时费
        data_cost = endpoint.estimated_monthly_gb * EgressType.COST_PER_GB.get(
            f"{service}_vpc_endpoint", 0.01
        )
        hourly_cost = EgressType.ENDPOINT_HOURLY.get(
            f"{service}_vpc_endpoint", 0.01
        ) * 730
        endpoint.estimated_monthly_cost_usd = round(data_cost + hourly_cost, 2)

        self._vpc_endpoints[endpoint_id] = endpoint
        return {"vpc_endpoint": endpoint.to_dict()}

    def _handle_update_vpc_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        endpoint_id = payload["endpoint_id"]
        endpoint = self._vpc_endpoints.get(endpoint_id)
        if endpoint is None:
            raise ValueError(f"VPC Endpoint 不存在: {endpoint_id}")

        for field_name in ("vpc_id", "route_table_ids", "estimated_monthly_gb",
                           "enabled", "region"):
            if field_name in payload:
                setattr(endpoint, field_name, payload[field_name])

        data_cost = endpoint.estimated_monthly_gb * EgressType.COST_PER_GB.get(
            f"{endpoint.service}_vpc_endpoint", 0.01
        )
        hourly_cost = EgressType.ENDPOINT_HOURLY.get(
            f"{endpoint.service}_vpc_endpoint", 0.01
        ) * 730
        endpoint.estimated_monthly_cost_usd = round(data_cost + hourly_cost, 2)

        return {"vpc_endpoint": endpoint.to_dict()}

    # ── 基线与报告 ────────────────────────────────────────

    def _handle_take_baseline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        total_gb = payload.get("total_monthly_gb", 0.0)
        breakdown = payload.get("breakdown", {})

        total_cost = 0.0
        for egress_type, gb in breakdown.items():
            rate = EgressType.COST_PER_GB.get(egress_type, 0.09)
            total_cost += gb * rate

        baseline = EgressBaseline(
            baseline_id=f"egr-bl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            total_monthly_gb=total_gb,
            total_monthly_cost=round(total_cost, 2),
            breakdown=breakdown,
            notes=payload.get("notes", ""),
        )
        self._baselines.append(baseline)
        return {"baseline": baseline.to_dict()}

    def _handle_generate_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        baseline_cost = payload.get("baseline_cost", 0.0)
        if not baseline_cost and self._baselines:
            baseline_cost = self._baselines[-1].total_monthly_cost

        # 计算当前成本
        current_cost = 0.0
        for cdn in self._cdn_configs.values():
            current_cost += cdn.estimated_monthly_cost_usd
        for vpc in self._vpc_endpoints.values():
            current_cost += vpc.estimated_monthly_cost_usd

        # 计算优化后成本 (假设 CDN → Cloudflare, NAT → VPC Endpoint)
        optimized = 0.0
        cdn_savings = 0.0
        vpc_savings = 0.0

        for cdn in self._cdn_configs.values():
            opt_gb_cost = cdn.estimated_monthly_gb * 0.05  # Cloudflare
            optimized += opt_gb_cost
            cdn_savings += cdn.estimated_monthly_cost_usd - opt_gb_cost

        for vpc in self._vpc_endpoints.values():
            optimized += vpc.estimated_monthly_cost_usd
            # NAT savings estimate
            if vpc.service == "s3":
                est = estimate_nat_savings(vpc.estimated_monthly_gb)
                vpc_savings += est["monthly_saving_usd"]

        total_saving = cdn_savings + vpc_savings
        saving_pct = round((total_saving / baseline_cost) * 100, 1) if baseline_cost > 0 else 0.0
        target_met = saving_pct >= payload.get("target_pct", 30.0)

        issues = []
        recommendations = []

        if not self._cdn_configs:
            issues.append("未配置任何 CDN")
            recommendations.append("为静态资源启用 CloudFront 或 Cloudflare CDN")

        if not self._vpc_endpoints:
            issues.append("未配置任何 VPC Endpoint")
            recommendations.append("为 S3/DynamoDB 配置 VPC Gateway Endpoint 消除 NAT 费用")

        if saving_pct < 30:
            issues.append(f"成本节省 {saving_pct}% 未达 30% 目标")
            recommendations.append("考虑将更多流量迁移到 VPC Endpoint 或启用 CDN 压缩")

        report = EgressAuditReport(
            report_id=f"egr-rpt-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            baseline_cost=baseline_cost,
            current_cost=round(current_cost, 2),
            optimized_cost=round(optimized, 2),
            cdn_savings=round(cdn_savings, 2),
            vpc_endpoint_savings=round(vpc_savings, 2),
            total_saving_pct=saving_pct,
            target_saving_pct=payload.get("target_pct", 30.0),
            target_met=target_met,
            issues=issues,
            recommendations=recommendations,
        )
        self._audit_reports.append(report)
        return {"report": report.to_dict()}

    # ── 估算处理器 ────────────────────────────────────────

    def _handle_estimate_nat_to_vpc(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        gb = payload.get("data_transfer_gb", 1000.0)
        return estimate_nat_savings(gb)

    def _handle_estimate_cdn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        gb = payload.get("monthly_gb", 1000.0)
        current_rate = payload.get("current_cost_per_gb", 0.09)
        optimized_rate = payload.get("optimized_cost_per_gb", 0.05)
        return estimate_cdn_savings(gb, current_rate, optimized_rate)

    def _handle_list_all(self, _payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "cdns": [c.to_dict() for c in self._cdn_configs.values()],
            "vpc_endpoints": [v.to_dict() for v in self._vpc_endpoints.values()],
            "baselines": [b.to_dict() for b in self._baselines[-10:]],
            "reports": [r.to_dict() for r in self._audit_reports[-10:]],
        }

    # ── 辅助方法 ──────────────────────────────────────────

    def get_latest_report(self) -> Optional[EgressAuditReport]:
        """获取最新审计报告."""
        return self._audit_reports[-1] if self._audit_reports else None

    def get_total_monthly_cost(self) -> float:
        """获取当前月总成本."""
        total = 0.0
        for cdn in self._cdn_configs.values():
            total += cdn.estimated_monthly_cost_usd
        for vpc in self._vpc_endpoints.values():
            total += vpc.estimated_monthly_cost_usd
        return round(total, 2)
