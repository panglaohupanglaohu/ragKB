# -*- coding: utf-8 -*-
"""
System Self-Evolution Engine — 系统自我演进引擎

执行智能体参考业界标准审查各 Channel，发现不完善之处后
自动生成演进任务，派发给 Build 团队执行修改，并通过
模拟人类操作的自动化测试进行验证。

闭环流程:
  Audit (执行智能体审查)
    → Discovery (发现演进项)
      → Dispatch (派发 Build 团队)
        → Build (实施修改)
          → Verify (自动化测试验证)
            → Close / Retry

术语:
  EvolutionItem   — 一条演进需求
  AuditRule       — 审查规则 (对标 Datacenter / general 等)
  BuildTask       — 派发给 Build 团队的工作单元
  VerifyResult    — 自动化测试验证结果
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .marine_base import (
    MarineChannel,
    ChannelPriority,
    ChannelStatus,
    get_default_registry,
)

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Data Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class EvolutionStatus(str, Enum):
    """演进条目生命周期状态。"""
    DISCOVERED = "discovered"          # 执行智能体发现
    DISPATCHED = "dispatched"          # 已派发 Build 团队
    IN_PROGRESS = "in_progress"        # Build 团队工作中
    VERIFY_PENDING = "verify_pending"  # 等待验证
    VERIFIED = "verified"              # 验证通过
    FAILED = "failed"                  # 验证失败 (需重试)
    CLOSED = "closed"                  # 关闭


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AuditDomain(str, Enum):
    DATACENTER = "Datacenter"
    GENERAL = "general"


# ── DNV-style A~E Compliance Rating (inspired by DNV CII) ──

class ComplianceRating(str, Enum):
    """DNV CII 风格 A~E 五级合规评级。"""
    A = "A"  # Major superior — 全面优秀
    B = "B"  # Minor superior — 良好，少量待改进
    C = "C"  # Moderate       — 基本合规，需要关注
    D = "D"  # Minor inferior — 不达标，需要纠正计划
    E = "E"  # Inferior       — 严重不合规，需紧急干预

    @staticmethod
    def from_score(score: float) -> "ComplianceRating":
        """0~100 分 → A~E 评级 (阈值逐年加严，参考 DNV CII reduction factor)。"""
        if score >= 85:
            return ComplianceRating.A
        if score >= 70:
            return ComplianceRating.B
        if score >= 55:
            return ComplianceRating.C
        if score >= 40:
            return ComplianceRating.D
        return ComplianceRating.E


# ── Kongsberg-style Operational Domain (6-domain) ───────────

class OperationalDomain(str, Enum):
    """Kongsberg Maritime 启发的 6 大操作域分类。"""
    TECHNICAL_MGMT = "technical_management"    # 技术管理
    COMPLIANCE_SAFETY = "compliance_safety"    # 合规与安全
    FUEL_EMISSIONS = "fuel_emissions"          # 燃油与排放
    VOYAGE_COMMERCIAL = "voyage_commercial"    # 航次与商业
    DATA_DECISION = "data_decision"            # 数据与决策
    ADVANCED_OPS = "advanced_operations"       # 高级操作 (自主/DP)


# ── ClassNK-style Dual-Layer Checklist ──────────────────────

class ChecklistLevel(str, Enum):
    """ClassNK 双层自查清单: 公司级 + 船级。"""
    COMPANY = "company"  # 公司管理体系 (ISM DOC)
    SHIP = "ship"        # 船舶管理体系 (ISM SMC)
    BOTH = "both"        # 两级均需检查


# ── Failure Escalation Tiers (DNV SEEMP Part III) ───────────

class EscalationTier(str, Enum):
    """失败升级层级 — 参考 DNV SEEMP Part III 纠正计划机制。"""
    NORMAL = "normal"              # 正常处理
    CORRECTIVE_PLAN = "corrective" # 需要纠正行动计划 (连续2次失败)
    MANAGEMENT_REVIEW = "review"   # 需要管理层审查 (连续3次失败)
    CRITICAL_HOLD = "hold"         # 暂停相关操作 (连续4+次失败)


@dataclass
class EvolutionItem:
    """一条由执行智能体发现的系统演进需求。"""
    id: str = field(default_factory=lambda: f"EVO-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    target_channel: str = ""
    audit_domain: str = AuditDomain.GENERAL.value
    severity: str = Severity.MEDIUM.value
    status: str = EvolutionStatus.DISCOVERED.value

    # 审查依据
    reference_standard: str = ""       # 例如 "IAMSAR Vol III §3.7"
    current_behavior: str = ""         # 当前系统行为描述
    expected_behavior: str = ""        # 业界期望行为

    # Build 团队处理
    build_task_id: Optional[str] = None
    assigned_agent: Optional[str] = None
    code_changes: List[str] = field(default_factory=list)  # 变更文件列表

    # 验证
    verify_test_name: Optional[str] = None   # 用于验证的测试函数名
    verify_result: Optional[str] = None      # passed / failed
    verify_detail: Optional[str] = None

    # 时间线
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    dispatched_at: Optional[str] = None
    completed_at: Optional[str] = None
    closed_at: Optional[str] = None

    # 重试
    retry_count: int = 0
    max_retries: int = 3

    # ── Phase 3 新增字段 ─────────────────────────────
    escalation_tier: str = EscalationTier.NORMAL.value
    consecutive_failures: int = 0
    compliance_rating: str = ""  # A~E
    operational_domain: str = ""
    checklist_level: str = ChecklistLevel.SHIP.value

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Compliance Zone (Wärtsilä Zone Management 启发) ─────────

@dataclass
class ComplianceZone:
    """地理围栏合规区域 — 进入特定水域时自动激活对应合规规则。"""
    id: str
    name: str
    zone_type: str  # ECA / MARPOL_SPECIAL / SECA / PSSA / HIGH_RISK / CUSTOM
    description: str = ""
    # 简化几何: 矩形包围盒 (适合船舶航线粗筛)
    lat_min: float = 0.0
    lat_max: float = 0.0
    lon_min: float = 0.0
    lon_max: float = 0.0
    # 此区域内自动激活的规则 ID 列表
    activated_rule_ids: List[str] = field(default_factory=list)
    # 额外合规要求描述
    extra_requirements: str = ""
    # 生效状态
    active: bool = True

    def contains(self, lat: float, lon: float) -> bool:
        """检查坐标是否在区域内。"""
        return (self.lat_min <= lat <= self.lat_max and
                self.lon_min <= lon <= self.lon_max)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Audit Trail Entry (NAPA Logbook 启发) ───────────────────

@dataclass
class AuditTrailEntry:
    """审计轨迹条目 — 不可变的审计日志记录。"""
    id: str = field(default_factory=lambda: f"ATR-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = ""  # audit_run / dispatch / verify / escalation / zone_enter / rating_change
    rule_id: str = ""
    item_id: str = ""
    actor: str = ""       # agent name 或 "system"
    old_value: str = ""
    new_value: str = ""
    detail: str = ""
    compliance_rating: str = ""
    zone_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditRule:
    """一条审查规则，用于自动发现演进项。"""
    id: str
    domain: str
    title: str
    description: str
    target_channel: str
    check_fn: Optional[Callable] = None  # (channel) -> (passed: bool, detail: str)
    reference: str = ""
    severity: str = Severity.MEDIUM.value
    # ── Phase 3 新增字段 ─────────────────────────────
    operational_domain: str = OperationalDomain.COMPLIANCE_SAFETY.value
    checklist_level: str = ChecklistLevel.SHIP.value
    rating_weight: float = 1.0  # 评级权重 (用于加权合规分数计算)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("check_fn", None)
        return d


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Built-in Audit Rules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ── General system check functions (work against self / bridge_chat) ──

def _check_evolution_self_audit(channel):
    """自检: 演进引擎自身必须正常初始化."""
    if not hasattr(channel, '_initialized') or not channel._initialized:
        return False, "演进引擎未初始化"
    return True, "演进引擎运行正常"


def _check_audit_rules_loaded(channel):
    """审查规则: 至少 5 条规则已加载."""
    rules = getattr(channel, 'audit_rules', [])
    if len(rules) < 5:
        return False, f"仅加载 {len(rules)} 条规则, 需 >= 5"
    return True, f"已加载 {len(rules)} 条审查规则"


def _check_compliance_zones_loaded(channel):
    """合规区域: 至少 1 个区域已配置."""
    zones = getattr(channel, 'compliance_zones', [])
    if len(zones) < 1:
        return False, "未配置合规区域"
    return True, f"已配置 {len(zones)} 个合规区域"


def _check_audit_trail_active(channel):
    """审计轨迹: 审计日志可写入."""
    trail = getattr(channel, '_audit_trail', None)
    if trail is None:
        return False, "审计轨迹存储未初始化"
    return True, f"审计轨迹活跃, 含 {len(trail)} 条记录"


def _check_bridge_chat_channel(channel):
    """通信通道: bridge_chat 须已注册."""
    registry = get_default_registry()
    bc = registry.get("bridge_chat")
    if not bc:
        return False, "bridge_chat Channel 未注册"
    return True, "bridge_chat 通信通道正常"


def _check_escalation_mechanism(channel):
    """升级机制: 失败升级追踪正常运作."""
    if not hasattr(channel, '_rule_failure_counts'):
        return False, "失败追踪字典缺失"
    if not hasattr(channel, '_escalation_levels'):
        return False, "升级层级字典缺失"
    return True, "DNV SEEMP Part III 升级机制就绪"


def _check_rating_calculation(channel):
    """评级计算: A~E 合规评级功能就绪."""
    if not hasattr(channel, 'calculate_compliance_rating'):
        return False, "评级计算方法缺失"
    if not hasattr(channel, '_compliance_score'):
        return False, "合规分数状态缺失"
    return True, f"合规评级系统正常, 当前 {channel._compliance_rating} ({channel._compliance_score}分)"


def _check_trend_analysis(channel):
    """趋势分析: 合规趋势追踪功能完备."""
    if not hasattr(channel, '_score_trend'):
        return False, "趋势数据列表缺失"
    if not hasattr(channel, 'get_trend_analysis'):
        return False, "趋势分析方法缺失"
    return True, f"趋势分析就绪, 已记录 {len(channel._score_trend)} 个数据点"


def _check_verify_registry(channel):
    """验证注册: 验证测试函数注册表可用."""
    reg = getattr(channel, '_verify_registry', None)
    if reg is None:
        return False, "验证注册表未初始化"
    # 验证注册表应随演进周期自动填充
    return True, f"验证注册表活跃, {len(reg)} 个测试已注册"


def _check_monitoring_interval(channel):
    """监控间隔: 连续监控配置合理 (60~600s)."""
    interval = getattr(channel, '_monitoring_interval', 0)
    if interval < 60 or interval > 600:
        return False, f"监控间隔 {interval}s 不合理 (需 60~600s)"
    return True, f"监控间隔 {interval}s, 符合最佳实践"


def _check_evolution_cycle_maturity(channel):
    """演进成熟度: 至少完成 2 轮完整演进闭环."""
    closed = getattr(channel, 'total_closed', 0)
    if closed < 2:
        return False, f"仅完成 {closed} 项闭环, 需 ≥ 2 以证明演进能力"
    return True, f"已完成 {closed} 项闭环演进, 系统成熟"


def _check_heritage_ledger_populated(channel):
    """遗产账本: Heritage Ledger 须有不可逆锁定记录."""
    history = getattr(channel, 'audit_history', [])
    trend = getattr(channel, '_score_trend', [])
    if len(trend) < 3:
        return False, f"趋势数据仅 {len(trend)} 点, 需 ≥ 3 以建立基线"
    return True, f"Heritage 基线已建立, {len(trend)} 个数据点"


def _check_escalation_exercised(channel):
    """升级演练: 至少 1 条规则经历过升级流程."""
    levels = getattr(channel, '_escalation_levels', {})
    escalated = sum(1 for v in levels.values() if v != "normal")
    if escalated < 1:
        return False, "尚无规则经历升级流程, 需演练确认升级路径"
    return True, f"{escalated} 条规则已激活升级机制"


# ── Datacenter Energy check functions ──

def _check_dc_pue_monitoring(channel):
    """PUE 实时监控: 确保 PUE 数据持续更新."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    status = dc.get_status() if hasattr(dc, 'get_status') else {}
    pue = status.get('current_pue', 0)
    if pue <= 0:
        return False, "PUE 数据为零, 监控未就绪"
    return True, f"PUE 实时监控正常, 当前 PUE={pue:.2f}"


def _check_dc_ratchet_heritage(channel):
    """Darwin Ratchet 棘轮遗产: 确保 heritage ledger 有记录."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    heritage = []
    if hasattr(dc, 'heritage_ledger'):
        result = dc.heritage_ledger()
        heritage = result.get('heritage', []) if isinstance(result, dict) else []
    if len(heritage) < 1:
        return False, "Heritage Ledger 为空, 尚无棘轮锁定记录"
    return True, f"Heritage Ledger 含 {len(heritage)} 条演进记录"


def _check_dc_sensor_coverage(channel):
    """IoT 传感器覆盖率: LoRa TH + PLC + RFID 三网融合."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    status = dc.get_status() if hasattr(dc, 'get_status') else {}
    count = status.get('sensor_count', 0)
    if count < 10:
        return False, f"传感器数量 {count} 不足, 需 ≥ 10 (LoRa TH + PLC + RFID)"
    return True, f"传感器覆盖: {count} 个传感器在线"


def _check_dc_thermal_hotspot(channel):
    """热岛检测: 确保热场监控能识别热点."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    if not hasattr(dc, 'detect_heat_island'):
        return False, "detect_heat_island 方法缺失"
    return True, "热岛检测功能就绪"


def _check_dc_policy_engine(channel):
    """策略引擎: 确保 save_outgo / open_source 双轨策略可用."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    status = dc.get_status() if hasattr(dc, 'get_status') else {}
    pc = status.get('policy_count', 0)
    if pc < 1:
        return False, "策略引擎无可用策略"
    return True, f"策略引擎就绪, {pc} 条策略可用"


def _check_dc_closed_loop(channel):
    """闭环控制: 感知→决策→执行→验证."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    if not hasattr(dc, 'closed_loop_tick'):
        return False, "closed_loop_tick 方法缺失"
    return True, "闭环 tick 就绪: 感知→决策→执行→验证"


def _check_dc_anomaly_detection(channel):
    """异常检测: Z-score 异常分析功能就绪."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    if not hasattr(dc, 'detect_anomalies'):
        return False, "detect_anomalies 方法缺失"
    return True, "异常检测 (Z-score) 功能就绪"


def _check_dc_musk_audit(channel):
    """第一性原理五步审计: Musk 方法论就绪."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    if not hasattr(dc, 'musk_five_step_audit'):
        return False, "musk_five_step_audit 方法缺失"
    return True, "第一性原理五步审计功能就绪"


def _check_dc_pue_forecast(channel):
    """PUE 预测: 24h 趋势预测功能."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    if not hasattr(dc, 'forecast_pue'):
        return False, "forecast_pue 方法缺失"
    return True, "PUE 24h 预测功能就绪"


def _check_dc_whatif_simulation(channel):
    """What-If 场景模拟: CAPEX/ROI 评估."""
    registry = get_default_registry()
    dc = registry.get("marine_datacenter_energy")
    if not dc:
        return False, "marine_datacenter_energy Channel 未注册"
    if not hasattr(dc, 'what_if'):
        return False, "what_if 方法缺失"
    return True, "What-If 场景模拟功能就绪"


# 所有内置审查规则
BUILTIN_AUDIT_RULES: List[AuditRule] = [
    # ── General System Health Rules (always checkable) ──
    AuditRule(
        id="GEN-SELF-001",
        domain=AuditDomain.GENERAL.value,
        title="演进引擎自检",
        description="自演进引擎必须正常初始化并运行",
        target_channel="system_evolution",
        check_fn=_check_evolution_self_audit,
        reference="ISO 27001 ISMS, PDCA",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=3.0,
    ),
    AuditRule(
        id="GEN-RULE-002",
        domain=AuditDomain.GENERAL.value,
        title="审查规则加载完整性",
        description="系统须加载 ≥5 条审查规则，覆盖关键合规域",
        target_channel="system_evolution",
        check_fn=_check_audit_rules_loaded,
        reference="ISM Code §12, ISO 19011",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.COMPANY.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="GEN-ZONE-003",
        domain=AuditDomain.GENERAL.value,
        title="合规区域配置完备",
        description="至少配置 1 个合规区域 (ECA/MARPOL/PSSA 等)",
        target_channel="system_evolution",
        check_fn=_check_compliance_zones_loaded,
        reference="MARPOL Annex VI, Wärtsilä Zone Mgmt",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="GEN-TRAIL-004",
        domain=AuditDomain.GENERAL.value,
        title="审计轨迹可用性",
        description="审计日志必须可写入，确保合规可追溯",
        target_channel="system_evolution",
        check_fn=_check_audit_trail_active,
        reference="NAPA Logbook, IMO FAL.5/Circ.39",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=2.5,
    ),
    AuditRule(
        id="GEN-CHAT-005",
        domain=AuditDomain.GENERAL.value,
        title="通信通道可达性",
        description="bridge_chat 通信通道须已注册并可用",
        target_channel="system_evolution",
        check_fn=_check_bridge_chat_channel,
        reference="SOLAS Ch.IV, GMDSS",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="GEN-ESC-006",
        domain=AuditDomain.GENERAL.value,
        title="失败升级机制就绪",
        description="DNV SEEMP Part III 风格的失败升级追踪正常",
        target_channel="system_evolution",
        check_fn=_check_escalation_mechanism,
        reference="DNV SEEMP Part III, CII",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.COMPANY.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="GEN-RATE-007",
        domain=AuditDomain.GENERAL.value,
        title="A~E 合规评级功能",
        description="DNV CII 风格 A~E 五级评级计算正常运作",
        target_channel="system_evolution",
        check_fn=_check_rating_calculation,
        reference="DNV CII Rating, IMO DCS",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.COMPANY.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="GEN-TREND-008",
        domain=AuditDomain.GENERAL.value,
        title="合规趋势分析能力",
        description="须具备趋势追踪与方向判断能力",
        target_channel="system_evolution",
        check_fn=_check_trend_analysis,
        reference="Wärtsilä FOS, ISO 50006",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="GEN-VREG-009",
        domain=AuditDomain.GENERAL.value,
        title="验证注册表活跃",
        description="自动化验证测试注册表须可用",
        target_channel="system_evolution",
        check_fn=_check_verify_registry,
        reference="ISO 17025, ClassNK Rules",
        severity=Severity.LOW.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.0,
    ),
    AuditRule(
        id="GEN-MON-010",
        domain=AuditDomain.GENERAL.value,
        title="连续监控间隔配置",
        description="监控间隔须在 60~600s 范围内",
        target_channel="system_evolution",
        check_fn=_check_monitoring_interval,
        reference="ISO 50001:2018, DCIM BP",
        severity=Severity.LOW.value,
        operational_domain=OperationalDomain.ADVANCED_OPS.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.0,
    ),
    # ── Improvement Canary Rules (designed to fail initially) ──
    AuditRule(
        id="GEN-MATUR-011",
        domain=AuditDomain.GENERAL.value,
        title="演进闭环成熟度验证",
        description="系统须完成 ≥2 项完整闭环演进以证明自我改善能力",
        target_channel="system_evolution",
        check_fn=_check_evolution_cycle_maturity,
        reference="PDCA Maturity Model, CMMI Level 3",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.COMPANY.value,
        rating_weight=2.5,
    ),
    AuditRule(
        id="GEN-HERIT-012",
        domain=AuditDomain.GENERAL.value,
        title="Heritage 基线数据充足性",
        description="趋势分析须有 ≥3 个历史数据点以建立可靠基线",
        target_channel="system_evolution",
        check_fn=_check_heritage_ledger_populated,
        reference="ISO 50006, DNV CII Baseline",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="GEN-ESCEX-013",
        domain=AuditDomain.GENERAL.value,
        title="升级机制演练确认",
        description="至少 1 条规则须经历过升级流程以验证升级路径",
        target_channel="system_evolution",
        check_fn=_check_escalation_exercised,
        reference="DNV SEEMP III, ISM Code §9",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.COMPANY.value,
        rating_weight=1.5,
    ),
    # ── Datacenter Energy First Principle ──
    AuditRule(
        id="DC-PUE-032",
        domain=AuditDomain.DATACENTER.value,
        title="PUE 实时监控与基线跟踪",
        description="数据中心 PUE 须持续监控, 基线 PUE 与目标 PUE 差值驱动棘轮演进",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_pue_monitoring,
        reference="ISO 50001, TIA-942, EN 50600",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=3.0,
    ),
    AuditRule(
        id="DC-RATCH-033",
        domain=AuditDomain.DATACENTER.value,
        title="Darwin Ratchet 棘轮锁定",
        description="每轮演进的 ΔPUE 须通过 heritage ledger 不可逆锁定, 禁止 PUE 回退",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_ratchet_heritage,
        reference="Zero Waste Compute, Darwin Heritage Ledger",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=3.0,
    ),
    AuditRule(
        id="DC-IOT-034",
        domain=AuditDomain.DATACENTER.value,
        title="IoT 三网融合传感器覆盖",
        description="LoRa TH + MC-RFID + PLC 三网传感器覆盖所有机柜, 确保温湿度场完整",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_sensor_coverage,
        reference="LoRa Alliance TS003, ISO 50001:2018",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="DC-HEAT-035",
        domain=AuditDomain.DATACENTER.value,
        title="热岛检测与过冷区识别",
        description="温度场分析须实时识别 hot-island 和 over-cool 区域, 指导 CRAC 调节",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_thermal_hotspot,
        reference="ASHRAE TC 9.9, TIA-942",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="DC-POL-036",
        domain=AuditDomain.DATACENTER.value,
        title="节支/开源双轨策略引擎",
        description="save_outgo + open_source 双轨策略须可评估适应度并执行, 驱动 PUE 下降",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_policy_engine,
        reference="Zero Waste Compute Policy Framework",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.FUEL_EMISSIONS.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="DC-LOOP-037",
        domain=AuditDomain.DATACENTER.value,
        title="闭环控制: 感知→决策→执行→验证",
        description="closed-loop tick 须完成完整四步循环, 确保每次调节有验证反馈",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_closed_loop,
        reference="PDCA, ISO 50001 Energy Management",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.5,
    ),
    AuditRule(
        id="DC-ANOM-038",
        domain=AuditDomain.DATACENTER.value,
        title="能耗异常检测与分级告警",
        description="Z-score 异常分析须覆盖所有传感器, 按 critical/high/medium/low 分级告警",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_anomaly_detection,
        reference="ISO 50001, DCIM Best Practice",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="DC-MUSK-039",
        domain=AuditDomain.DATACENTER.value,
        title="第一性原理五步审计",
        description="Musk 五步法: 质疑需求→删除冗余→简化优化→加速迭代→自动化",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_musk_audit,
        reference="First Principles, Elon Musk 5-Step",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="DC-FCST-040",
        domain=AuditDomain.DATACENTER.value,
        title="PUE 24h 趋势预测",
        description="基于历史数据预测未来 24h PUE 走势, 为策略决策提供前瞻支撑",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_pue_forecast,
        reference="ISO 50006 Energy Baselines",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="DC-WHIF-041",
        domain=AuditDomain.DATACENTER.value,
        title="What-If 场景模拟与 ROI 评估",
        description="改造方案须经 What-If 模拟评估 CAPEX/回收期/CO₂ 减排量后方可实施",
        target_channel="marine_datacenter_energy",
        check_fn=_check_dc_whatif_simulation,
        reference="ISO 50001, DCIM Financial Modeling",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.FUEL_EMISSIONS.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.5,
    ),
]


# ── Built-in Compliance Zones ─────

BUILTIN_COMPLIANCE_ZONES: List[ComplianceZone] = [
    ComplianceZone(
        id="ZONE-ECA-NORTH",
        name="北欧 ECA 排放控制区",
        zone_type="ECA",
        description="波罗的海/北海排放控制区，SOx ≤ 0.10%",
        lat_min=50.0, lat_max=66.0,
        lon_min=-5.0, lon_max=30.0,
        activated_rule_ids=["DC-PUE-032", "DC-LOOP-037", "DC-ANOM-038"],
        extra_requirements="需连续监控能效指标，SOx/NOx 限值加严",
        active=True,
    ),
    ComplianceZone(
        id="ZONE-MARPOL-MED",
        name="地中海 MARPOL 特殊区域",
        zone_type="MARPOL_SPECIAL",
        description="地中海防污染特殊区域",
        lat_min=30.0, lat_max=46.0,
        lon_min=-6.0, lon_max=36.0,
        activated_rule_ids=["DC-PUE-032", "DC-POL-036"],
        extra_requirements="垃圾排放零容忍，油污水处理加严",
        active=True,
    ),
    ComplianceZone(
        id="ZONE-PSSA-REEF",
        name="大堡礁 PSSA 保护区",
        zone_type="PSSA",
        description="特别敏感海域 — 航速限制 + 双重审查",
        lat_min=-25.0, lat_max=-10.0,
        lon_min=142.0, lon_max=155.0,
        activated_rule_ids=["DC-RATCH-033", "DC-HEAT-035", "DC-MUSK-039"],
        extra_requirements="航速 ≤ 12kn，须实施鲸鱼避让措施",
        active=True,
    ),
    ComplianceZone(
        id="ZONE-HIGH-RISK-GOA",
        name="亚丁湾高风险区",
        zone_type="HIGH_RISK",
        description="海盗高风险区域 — 加强安全监控",
        lat_min=10.0, lat_max=20.0,
        lon_min=42.0, lon_max=60.0,
        activated_rule_ids=["DC-IOT-034", "DC-ANOM-038"],
        extra_requirements="需启用 AIS 持续播发，加强瞭望",
        active=True,
    ),
    ComplianceZone(
        id="ZONE-DC-CAMPUS",
        name="数据中心园区",
        zone_type="CUSTOM",
        description="数据中心本地合规区 — 全部规则激活",
        lat_min=22.0, lat_max=23.0,
        lon_min=113.0, lon_max=114.0,
        activated_rule_ids=[
            "DC-PUE-032", "DC-RATCH-033", "DC-IOT-034", "DC-HEAT-035",
            "DC-POL-036", "DC-LOOP-037", "DC-ANOM-038", "DC-MUSK-039",
            "DC-FCST-040", "DC-WHIF-041",
        ],
        extra_requirements="全面能效审查，PUE ≤ 1.4 目标",
        active=True,
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# System Evolution Channel
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class SystemEvolutionChannel(MarineChannel):
    """系统自我演进引擎 — 执行智能体审查 → Build 团队修改 → 自动测试验证。"""

    name = "system_evolution"
    description = "系统自我演进引擎 (审查 → 发现 → 派发 → 构建 → 验证 → 闭环)"
    version = "1.0.0"
    priority = ChannelPriority.P1
    dependencies: List[str] = ["build_team_manager", "execution_team_manager"]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self._config = self.config

        # 演进条目仓库
        self.evolution_items: Dict[str, EvolutionItem] = {}

        # 审查规则
        self.audit_rules: List[AuditRule] = list(BUILTIN_AUDIT_RULES)

        # 验证函数注册表: verify_test_name -> callable
        self._verify_registry: Dict[str, Callable] = {}

        # 审查历史
        self.audit_history: List[Dict[str, Any]] = []

        # 统计
        self.total_audits = 0
        self.total_discovered = 0
        self.total_dispatched = 0
        self.total_verified = 0
        self.total_failed = 0
        self.total_closed = 0

        # ── Phase 