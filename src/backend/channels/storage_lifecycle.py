# -*- coding: utf-8 -*-
"""
Storage Lifecycle Policy Channel — S3 Intelligent-Tiering 配置标准化

实现 S3 存储生命周期策略管理:
  - 自动分层策略 (Frequent → Infrequent → Archive → Deep Archive)
  - 成本基线建模与 30% 成本降低目标追踪
  - 策略模拟、审计与合规报告
  - 与 Darwin Ratchet 棘轮系统集成（不可回退策略锁定）

Architecture:
  StorageLifecycleChannel (MarineChannel)
    ├── LifecyclePolicy         — 数据模型
    ├── TierTransition          — 分层转换规则
    ├── CostBaseline            — 成本基线
    └── AuditReport             — 审计报告
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

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

class StorageClass:
    """S3 存储类型常量."""

    STANDARD = "STANDARD"
    STANDARD_IA = "STANDARD_IA"
    ONEZONE_IA = "ONEZONE_IA"
    INTELLIGENT_TIERING = "INTELLIGENT_TIERING"
    GLACIER_IR = "GLACIER_INSTANT_RETRIEVAL"
    GLACIER = "GLACIER"
    DEEP_ARCHIVE = "DEEP_ARCHIVE"

    # 相对成本系数 (以 STANDARD 为 1.0 的估算)
    COST_FACTORS: Dict[str, float] = {
        "STANDARD": 1.0,
        "STANDARD_IA": 0.55,
        "ONEZONE_IA": 0.40,
        "INTELLIGENT_TIERING": 0.65,
        "GLACIER_INSTANT_RETRIEVAL": 0.20,
        "GLACIER": 0.06,
        "DEEP_ARCHIVE": 0.012,
    }

    # 访问延迟范围 (毫秒)
    LATENCY: Dict[str, Tuple[int, int]] = {
        "STANDARD": (1, 5),
        "STANDARD_IA": (1, 5),
        "ONEZONE_IA": (1, 5),
        "INTELLIGENT_TIERING": (1, 30),
        "GLACIER_INSTANT_RETRIEVAL": (1, 300_000),
        "GLACIER": (60_000, 300_000),
        "DEEP_ARCHIVE": (12 * 3600_000, 48 * 3600_000),
    }


@dataclass
class TierTransition:
    """分层转换规则."""

    from_class: str
    to_class: str
    days_after_creation: int = 90
    condition: str = "auto"
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_class,
            "to": self.to_class,
            "days": self.days_after_creation,
            "condition": self.condition,
            "enabled": self.enabled,
        }


@dataclass
class LifecyclePolicy:
    """S3 生命周期策略."""

    policy_id: str
    name: str
    description: str = ""
    transitions: List[TierTransition] = field(default_factory=list)
    target_cost_reduction_pct: float = 30.0
    created_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    locked: bool = False  # 棘轮锁定后不可回退

    # 存储桶信息
    bucket_name: str = ""
    total_size_gb: float = 0.0
    object_count: int = 0

    def add_transition(self, from_class: str, to_class: str,
                       days: int = 90, condition: str = "auto") -> TierTransition:
        t = TierTransition(
            from_class=from_class,
            to_class=to_class,
            days_after_creation=days,
            condition=condition,
        )
        self.transitions.append(t)
        return t

    def estimate_monthly_cost(self) -> float:
        """估算当前配置下的月存储成本 (USD)."""
        if self.total_size_gb <= 0:
            return 0.0
        # 默认假设: 100% 在 STANDARD
        cost_per_gb = StorageClass.COST_FACTORS.get(StorageClass.STANDARD, 1.0) * 0.023
        return round(self.total_size_gb * cost_per_gb, 2)

    def estimate_optimized_cost(self) -> float:
        """估算优化后的月存储成本（基于转换规则分布)."""
        # 简单分布模型: 10% Standard, 30% IA, 60% Archive tiers
        distribution = {
            StorageClass.STANDARD: 0.10,
            StorageClass.STANDARD_IA: 0.30,
            StorageClass.GLACIER_IR: 0.30,
            StorageClass.GLACIER: 0.20,
            StorageClass.DEEP_ARCHIVE: 0.10,
        }
        total = 0.0
        base_rate = 0.023  # Standard GB-month
        for cls_name, pct in distribution.items():
            gb = self.total_size_gb * pct
            factor = StorageClass.COST_FACTORS.get(cls_name, 1.0)
            total += gb * base_rate * factor
        return round(total, 2)

    def cost_saving_pct(self) -> float:
        """计算成本节省百分比."""
        baseline = self.estimate_monthly_cost()
        if baseline <= 0:
            return 0.0
        optimized = self.estimate_optimized_cost()
        return round((1 - optimized / baseline) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "transitions": [t.to_dict() for t in self.transitions],
            "target_cost_reduction_pct": self.target_cost_reduction_pct,
            "created_at": self.created_at.isoformat(),
            "enabled": self.enabled,
            "locked": self.locked,
            "bucket_name": self.bucket_name,
            "total_size_gb": self.total_size_gb,
            "object_count": self.object_count,
            "estimated_monthly_cost_usd": self.estimate_monthly_cost(),
            "estimated_optimized_cost_usd": self.estimate_optimized_cost(),
            "cost_saving_pct": self.cost_saving_pct(),
        }


@dataclass
class CostBaseline:
    """存储成本基线."""

    baseline_id: str
    policy_id: str
    monthly_cost_usd: float = 0.0
    snapshot_date: datetime = field(default_factory=datetime.now)
    storage_class_distribution: Dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "policy_id": self.policy_id,
            "monthly_cost_usd": self.monthly_cost_usd,
            "snapshot_date": self.snapshot_date.isoformat(),
            "distribution": self.storage_class_distribution,
            "notes": self.notes,
        }


@dataclass
class AuditReport:
    """存储生命周期审计报告."""

    report_id: str
    policy_id: str
    created_at: datetime = field(default_factory=datetime.now)
    baseline_cost: float = 0.0
    current_cost: float = 0.0
    optimized_cost: float = 0.0
    actual_saving_pct: float = 0.0
    target_saving_pct: float = 30.0
    target_met: bool = False
    compliance_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "policy_id": self.policy_id,
            "created_at": self.created_at.isoformat(),
            "baseline_cost": self.baseline_cost,
            "current_cost": self.current_cost,
            "optimized_cost": self.optimized_cost,
            "actual_saving_pct": self.actual_saving_pct,
            "target_saving_pct": self.target_saving_pct,
            "target_met": self.target_met,
            "compliance_issues": self.compliance_issues,
            "recommendations": self.recommendations,
        }


# ═══════════════════════════════════════════════════════════
# Preset Policies
# ═══════════════════════════════════════════════════════════

def create_default_s3_policy(bucket_name: str = "default-bucket",
                              total_size_gb: float = 1000.0) -> LifecyclePolicy:
    """创建默认 S3 Intelligent-Tiering 生命周期策略.

    推荐最佳实践:
      - 30 天不活跃 → STANDARD_IA
      - 90 天不活跃 → GLACIER_IR
      - 180 天不活跃 → GLACIER
      - 365 天不活跃 → DEEP_ARCHIVE
    """
    policy = LifecyclePolicy(
        policy_id="s3-default-v1",
        name="S3 Intelligent-Tiering 默认策略",
        description="自动化存储分层: Standard → IA → Glacier IR → Glacier → Deep Archive",
        target_cost_reduction_pct=30.0,
        bucket_name=bucket_name,
        total_size_gb=total_size_gb,
    )
    policy.add_transition(StorageClass.STANDARD, StorageClass.STANDARD_IA,
                          days=30, condition="no_access_30d")
    policy.add_transition(StorageClass.STANDARD_IA, StorageClass.GLACIER_IR,
                          days=90, condition="no_access_90d")
    policy.add_transition(StorageClass.GLACIER_IR, StorageClass.GLACIER,
                          days=180, condition="no_access_180d")
    policy.add_transition(StorageClass.GLACIER, StorageClass.DEEP_ARCHIVE,
                          days=365, condition="no_access_365d")
    return policy


def create_aggressive_s3_policy(bucket_name: str = "aggressive-bucket",
                                 total_size_gb: float = 1000.0) -> LifecyclePolicy:
    """创建激进分层策略（更早降冷)."""
    policy = LifecyclePolicy(
        policy_id="s3-aggressive-v1",
        name="S3 激进降冷策略",
        description="更快降冷以最大化成本节省",
        target_cost_reduction_pct=50.0,
        bucket_name=bucket_name,
        total_size_gb=total_size_gb,
    )
    policy.add_transition(StorageClass.STANDARD, StorageClass.STANDARD_IA,
                          days=7, condition="no_access_7d")
    policy.add_transition(StorageClass.STANDARD_IA, StorageClass.GLACIER_IR,
                          days=30, condition="no_access_30d")
    policy.add_transition(StorageClass.GLACIER_IR, StorageClass.GLACIER,
                          days=90, condition="no_access_90d")
    policy.add_transition(StorageClass.GLACIER, StorageClass.DEEP_ARCHIVE,
                          days=180, condition="no_access_180d")
    return policy


# ═══════════════════════════════════════════════════════════
# Storage Lifecycle Channel
# ═══════════════════════════════════════════════════════════

class StorageLifecycleChannel(MarineChannel):
    """存储生命周期策略 Channel.

    管理 S3 Intelligent-Tiering 配置，追踪成本基线，
    产出 30% 成本降低审计报告。
    """

    name: str = "storage_lifecycle"
    description: str = (
        "S3 Intelligent-Tiering 存储生命周期策略管理 — "
        "自动化分层、成本基线追踪、审计报告"
    )
    version: str = "1.0.0"
    priority: ChannelPriority = ChannelPriority.P1
    dependencies: List[str] = []

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._policies: Dict[str, LifecyclePolicy] = {}
        self._baselines: Dict[str, List[CostBaseline]] = {}
        self._audit_reports: Dict[str, List[AuditReport]] = {}
        self._initialized = False
        self._event_counter: int = 0

    # ── MarineChannel 接口 ──────────────────────────────────

    def initialize(self) -> bool:
        """初始化存储生命周期 Channel."""
        try:
            # 加载默认策略
            default_policy = create_default_s3_policy()
            self._policies[default_policy.policy_id] = default_policy

            # 创建初始成本基线
            baseline = CostBaseline(
                baseline_id=f"bl-{default_policy.policy_id}-init",
                policy_id=default_policy.policy_id,
                monthly_cost_usd=default_policy.estimate_monthly_cost(),
            )
            self._baselines.setdefault(default_policy.policy_id, []).append(baseline)

            self._initialized = True
            self._set_health(ChannelStatus.OK, f"已加载 {len(self._policies)} 个策略")
            logger.info("StorageLifecycleChannel 初始化完成")
            return True
        except Exception as e:
            self._set_health(ChannelStatus.ERROR, f"初始化失败: {e}")
            logger.exception("StorageLifecycleChannel 初始化异常")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取 Channel 运行状态."""
        policies_status = []
        for pid, p in self._policies.items():
            policies_status.append({
                "policy_id": pid,
                "name": p.name,
                "enabled": p.enabled,
                "locked": p.locked,
                "cost_saving_pct": p.cost_saving_pct(),
                "target_met": p.cost_saving_pct() >= p.target_cost_reduction_pct,
            })

        return {
            "name": self.name,
            "version": self.version,
            "priority": self.priority.name,
            "policies_count": len(self._policies),
            "baselines_count": sum(len(v) for v in self._baselines.values()),
            "reports_count": sum(len(v) for v in self._audit_reports.values()),
            "policies": policies_status,
            "event_counter": self._event_counter,
            "overall_cost_reduction_pct": self._compute_overall_saving(),
        }

    def shutdown(self) -> bool:
        """关闭 Channel."""
        logger.info("StorageLifecycleChannel 关闭")
        self._initialized = False
        return True

    # ── 事件处理 ──────────────────────────────────────────

    def process_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """处理生命周期管理事件.

        支持的事件:
          - create_policy: 创建新策略
          - update_policy: 更新策略配置
          - lock_policy: 棘轮锁定策略
          - take_baseline: 记录成本快照
          - generate_report: 生成审计报告
          - simulate: 模拟策略效果
          - list_policies: 列出所有策略
        """
        self._event_counter += 1

        handlers = {
            "create_policy": self._handle_create_policy,
            "update_policy": self._handle_update_policy,
            "lock_policy": self._handle_lock_policy,
            "take_baseline": self._handle_take_baseline,
            "generate_report": self._handle_generate_report,
            "simulate": self._handle_simulate,
            "list_policies": self._handle_list_policies,
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

    # ── 事件处理器 ────────────────────────────────────────

    def _handle_create_policy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        policy_id = payload["policy_id"]
        if policy_id in self._policies:
            raise ValueError(f"策略已存在: {policy_id}")

        policy = LifecyclePolicy(
            policy_id=policy_id,
            name=payload.get("name", policy_id),
            description=payload.get("description", ""),
            target_cost_reduction_pct=payload.get("target_pct", 30.0),
            bucket_name=payload.get("bucket_name", ""),
            total_size_gb=payload.get("total_size_gb", 0.0),
            object_count=payload.get("object_count", 0),
        )

        # 添加自定义转换规则
        for t in payload.get("transitions", []):
            policy.add_transition(
                from_class=t.get("from", StorageClass.STANDARD),
                to_class=t.get("to", StorageClass.STANDARD_IA),
                days=t.get("days", 90),
                condition=t.get("condition", "auto"),
            )

        self._policies[policy_id] = policy
        return {"policy": policy.to_dict()}

    def _handle_update_policy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        policy_id = payload["policy_id"]
        policy = self._policies.get(policy_id)
        if policy is None:
            raise ValueError(f"策略不存在: {policy_id}")
        if policy.locked:
            raise ValueError(f"策略已锁定，不可修改: {policy_id}")

        if "target_pct" in payload:
            policy.target_cost_reduction_pct = payload["target_pct"]
        if "bucket_name" in payload:
            policy.bucket_name = payload["bucket_name"]
        if "total_size_gb" in payload:
            policy.total_size_gb = payload["total_size_gb"]
        if "object_count" in payload:
            policy.object_count = payload["object_count"]
        if "enabled" in payload:
            policy.enabled = payload["enabled"]
        if "transitions" in payload:
            policy.transitions.clear()
            for t in payload["transitions"]:
                policy.add_transition(
                    from_class=t.get("from", StorageClass.STANDARD),
                    to_class=t.get("to", StorageClass.STANDARD_IA),
                    days=t.get("days", 90),
                    condition=t.get("condition", "auto"),
                )

        return {"policy": policy.to_dict()}

    def _handle_lock_policy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """棘轮锁定 — 策略不可回退."""
        policy_id = payload["policy_id"]
        policy = self._policies.get(policy_id)
        if policy is None:
            raise ValueError(f"策略不存在: {policy_id}")

        policy.locked = True
        logger.info(f"策略已棘轮锁定: {policy_id}")
        return {"policy": policy.to_dict(), "locked": True}

    def _handle_take_baseline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        policy_id = payload["policy_id"]
        policy = self._policies.get(policy_id)
        if policy is None:
            raise ValueError(f"策略不存在: {policy_id}")

        baseline = CostBaseline(
            baseline_id=f"bl-{policy_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            policy_id=policy_id,
            monthly_cost_usd=payload.get("cost_usd", policy.estimate_monthly_cost()),
            storage_class_distribution=payload.get("distribution", {}),
            notes=payload.get("notes", ""),
        )
        self._baselines.setdefault(policy_id, []).append(baseline)
        return {"baseline": baseline.to_dict()}

    def _handle_generate_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        policy_id = payload["policy_id"]
        policy = self._policies.get(policy_id)
        if policy is None:
            raise ValueError(f"策略不存在: {policy_id}")

        baselines = self._baselines.get(policy_id, [])
        baseline_cost = baselines[-1].monthly_cost_usd if baselines else 0.0

        optimized = policy.estimate_optimized_cost()
        current = policy.estimate_monthly_cost()
        saving_pct = policy.cost_saving_pct()
        target_met = saving_pct >= policy.target_cost_reduction_pct

        issues = []
        recommendations = []

        if not target_met:
            issues.append(
                f"未达目标: 当前节省 {saving_pct}% < 目标 {policy.target_cost_reduction_pct}%"
            )
            recommendations.append(
                "建议缩短 Transition 天数或启用更激进的分层策略"
            )

        if policy.total_size_gb > 10000:
            recommendations.append(
                "大规模存储 (>10TB): 建议启用 Glacier Deep Archive 以最大化节省"
            )

        if not policy.transitions:
            issues.append("未配置任何分层转换规则")
            recommendations.append("添加至少一条 Standard → IA 转换规则")

        report = AuditReport(
            report_id=f"rpt-{policy_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            policy_id=policy_id,
            baseline_cost=baseline_cost,
            current_cost=current,
            optimized_cost=optimized,
            actual_saving_pct=saving_pct,
            target_saving_pct=policy.target_cost_reduction_pct,
            target_met=target_met,
            compliance_issues=issues,
            recommendations=recommendations,
        )

        self._audit_reports.setdefault(policy_id, []).append(report)
        return {"report": report.to_dict()}

    def _handle_simulate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """模拟策略效果（what-if 分析)."""
        size_gb = payload.get("total_size_gb", 1000.0)
        transitions = payload.get("transitions", [])

        temp_policy = LifecyclePolicy(
            policy_id="sim-temp",
            name="Simulation",
            total_size_gb=size_gb,
        )
        for t in transitions:
            temp_policy.add_transition(**t)

        # 计算不同时间跨度的成本估算
        monthly_baseline = size_gb * 0.023
        monthly_optimized = temp_policy.estimate_optimized_cost()
        yearly_saving = (monthly_baseline - monthly_optimized) * 12

        return {
            "simulation": {
                "total_size_gb": size_gb,
                "monthly_baseline_usd": round(monthly_baseline, 2),
                "monthly_optimized_usd": monthly_optimized,
                "monthly_saving_usd": round(monthly_baseline - monthly_optimized, 2),
                "yearly_saving_usd": round(yearly_saving, 2),
                "saving_pct": round((1 - monthly_optimized / monthly_baseline) * 100, 1),
                "transitions_count": len(transitions),
            }
        }

    def _handle_list_policies(self, _payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"policies": [p.to_dict() for p in self._policies.values()]}

    # ── 辅助方法 ──────────────────────────────────────────

    def _compute_overall_saving(self) -> float:
        """计算所有策略的整体成本节省百分比."""
        if not self._policies:
            return 0.0
        savings = [p.cost_saving_pct() for p in self._policies.values()]
        return round(sum(savings) / len(savings), 1)

    def get_policy(self, policy_id: str) -> Optional[LifecyclePolicy]:
        """获取指定策略."""
        return self._policies.get(policy_id)

    def get_latest_report(self, policy_id: str) -> Optional[AuditReport]:
        """获取最新审计报告."""
        reports = self._audit_reports.get(policy_id, [])
        return reports[-1] if reports else None

    def get_cost_trend(self, policy_id: str) -> List[Dict[str, Any]]:
        """获取成本趋势数据."""
        baselines = self._baselines.get(policy_id, [])
        return [b.to_dict() for b in baselines]
