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

BUILTIN_COMPLIANCE_ZONES: List[ComplianceZone] = []


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

        # ── Phase 3: 新增状态 ────────────────────────────
        # A~E 合规评级 (DNV CII 风格)
        self._compliance_score: float = 100.0
        self._compliance_rating: str = ComplianceRating.A.value
        self._rating_history: List[Dict[str, Any]] = []

        # 地理围栏合规区域 (Wärtsilä Zone Management)
        self.compliance_zones: List[ComplianceZone] = list(BUILTIN_COMPLIANCE_ZONES)
        self._active_zone_ids: List[str] = []
        self._vessel_position: Dict[str, float] = {"lat": 0.0, "lon": 0.0}

        # 持久化审计轨迹 (NAPA Logbook)
        self._audit_trail: List[AuditTrailEntry] = []
        self._max_trail_entries: int = 500

        # 规则失败跟踪 (用于升级机制)
        self._rule_failure_counts: Dict[str, int] = {}  # rule_id -> consecutive failures
        self._escalation_levels: Dict[str, str] = {}    # rule_id -> EscalationTier

        # 连续监控间隔 (秒)
        self._monitoring_interval: int = 300  # 5分钟
        self._last_monitoring_time: float = 0.0

        # 趋势分析数据
        self._score_trend: List[Dict[str, Any]] = []  # [{time, score, rating, passed, failed}]

    # ── MarineChannel 接口 ───────────────────────────────────

    def initialize(self) -> bool:
        self._initialized = True
        self._set_health(ChannelStatus.OK, "系统自我演进引擎已就绪")
        logger.info("🔄 System Evolution Engine initialized (%d audit rules)", len(self.audit_rules))
        return True

    def shutdown(self) -> bool:
        self._initialized = False
        self._set_health(ChannelStatus.OFF, "Shutdown")
        return True

    async def process_event(self, event: dict) -> dict:
        event_type = event.get("type", "")
        if event_type == "run_audit":
            return self.run_full_audit()
        if event_type == "dispatch_all":
            return self.dispatch_all_pending()
        if event_type == "verify_all":
            return self.verify_all_pending()
        if event_type == "evolution_cycle":
            return self.run_evolution_cycle()
        return {"status": "ignored", "reason": f"Unknown event: {event_type}"}

    def get_status(self) -> Dict[str, Any]:
        by_status = {}
        for item in self.evolution_items.values():
            by_status[item.status] = by_status.get(item.status, 0) + 1
        return {
            "name": self.name,
            "initialized": self._initialized,
            "health": self._health.status.value,
            "audit_rules_count": len(self.audit_rules),
            "evolution_items_count": len(self.evolution_items),
            "items_by_status": by_status,
            "compliance_rating": self._compliance_rating,
            "compliance_score": self._compliance_score,
            "active_zones": len(self._active_zone_ids),
            "escalated_rules": sum(1 for v in self._escalation_levels.values()
                                   if v != EscalationTier.NORMAL.value),
            "stats": {
                "total_audits": self.total_audits,
                "total_discovered": self.total_discovered,
                "total_dispatched": self.total_dispatched,
                "total_verified": self.total_verified,
                "total_failed": self.total_failed,
                "total_closed": self.total_closed,
            },
        }

    # ── 审查: 执行智能体参照业界标准发现演进项 ────────────────

    def run_full_audit(self) -> Dict[str, Any]:
        """运行全部审查规则，发现不达标项自动创建 EvolutionItem。"""
        registry = get_default_registry()
        self.total_audits += 1
        results: List[Dict[str, Any]] = []
        new_items: List[str] = []

        for rule in self.audit_rules:
            channel = registry.get(rule.target_channel)
            if not channel:
                results.append({
                    "rule": rule.id, "status": "skip",
                    "reason": f"Channel '{rule.target_channel}' 未注册",
                })
                continue

            if rule.check_fn is None:
                results.append({"rule": rule.id, "status": "skip", "reason": "无检查函数"})
                continue

            try:
                passed, detail = rule.check_fn(channel)
            except Exception as exc:
                passed, detail = False, f"审查异常: {exc}"

            results.append({
                "rule": rule.id, "passed": passed, "detail": detail,
            })

            # ── Phase 3: 升级机制跟踪 ──
            self._update_escalation(rule.id, passed)

            if not passed:
                # 避免重复创建
                existing = self._find_item_by_rule(rule.id)
                if existing and existing.status not in (
                    EvolutionStatus.CLOSED.value, EvolutionStatus.FAILED.value
                ):
                    continue

                item = EvolutionItem(
                    title=rule.title,
                    description=rule.description,
                    target_channel=rule.target_channel,
                    audit_domain=rule.domain,
                    severity=rule.severity,
                    reference_standard=rule.reference,
                    current_behavior=detail,
                    expected_behavior=rule.description,
                    verify_test_name=f"test_evo_{rule.id.lower().replace('-', '_')}",
                )
                item.build_task_id = rule.id
                self.evolution_items[item.id] = item
                self.total_discovered += 1
                new_items.append(item.id)

        result = {
            "audit_run": self.total_audits,
            "rules_checked": len(results),
            "passed": sum(1 for r in results if r.get("passed")),
            "failed": sum(1 for r in results if r.get("passed") is False),
            "skipped": sum(1 for r in results if r.get("status") == "skip"),
            "new_items_created": new_items,
            "details": results,
        }

        # ── Phase 3: 计算合规评级 ──
        rating_result = self.calculate_compliance_rating(results)
        result["compliance_rating"] = rating_result["rating"]
        result["compliance_score"] = rating_result["score"]
        result["domain_scores"] = rating_result.get("domain_scores", {})
        result["escalation"] = self.get_escalation_status()

        # 记录审计轨迹
        self._record_trail(
            "audit_run",
            detail=f"审查 #{self.total_audits}: {result['passed']} pass, "
                   f"{result['failed']} fail, 评级 {rating_result['rating']} "
                   f"({rating_result['score']}分)",
            compliance_rating=rating_result["rating"],
        )
        self._last_monitoring_time = time.time()

        # Record in history
        self.audit_history.append({
            "run": self.total_audits,
            "time": datetime.now().isoformat(),
            "passed": result["passed"],
            "failed": result["failed"],
            "skipped": result["skipped"],
            "new_items": len(new_items),
        })
        # Keep last 50 audits
        if len(self.audit_history) > 50:
            self.audit_history = self.audit_history[-50:]

        return result

    def _find_item_by_rule(self, rule_id: str) -> Optional[EvolutionItem]:
        for item in self.evolution_items.values():
            if item.build_task_id == rule_id:
                return item
        return None

    # ── 派发: 将演进需求发送给 Build 团队 ─────────────────────

    def dispatch_all_pending(self) -> Dict[str, Any]:
        """将所有 DISCOVERED 状态的演进项派发给 Build 团队。"""
        dispatched: List[str] = []
        registry = get_default_registry()
        build_mgr = registry.get("build_team_manager")

        # Agent assignment strategy based on domain and severity
        _AGENT_MAP = {
            AuditDomain.DATACENTER.value: "code_writer",
            AuditDomain.GENERAL.value: "dev_lead",
        }
        _SEVERITY_OVERRIDE = {
            Severity.CRITICAL.value: "chief_director",  # Critical → 总监亲自跟踪
        }
        # Per-rule agent override for balanced distribution
        _RULE_AGENT_OVERRIDE: Dict[str, str] = {}

        for item in self.evolution_items.values():
            if item.status != EvolutionStatus.DISCOVERED.value:
                continue

            item.status = EvolutionStatus.DISPATCHED.value
            item.dispatched_at = datetime.now().isoformat()
            self.total_dispatched += 1

            # Assign agent: per-rule override > severity override > domain map
            if item.build_task_id in _RULE_AGENT_OVERRIDE:
                item.assigned_agent = _RULE_AGENT_OVERRIDE[item.build_task_id]
            elif item.severity == Severity.CRITICAL.value:
                item.assigned_agent = _SEVERITY_OVERRIDE[item.severity]
            else:
                item.assigned_agent = _AGENT_MAP.get(item.audit_domain, "code_writer")

            # 如果 Build 团队 Channel 存在，下发任务
            if build_mgr and hasattr(build_mgr, "assign_task"):
                task_desc = f"evolution_fix:{item.build_task_id}:{item.title}"
                build_mgr.assign_task(item.assigned_agent, task_desc)

            dispatched.append(item.id)

        return {"dispatched": dispatched, "count": len(dispatched)}

    def mark_in_progress(self, item_id: str) -> bool:
        """Build 团队标记开始工作。"""
        item = self.evolution_items.get(item_id)
        if not item:
            return False
        item.status = EvolutionStatus.IN_PROGRESS.value
        return True

    def mark_build_complete(self, item_id: str, code_changes: Optional[List[str]] = None) -> bool:
        """Build 团队标记修改完成，进入待验证。"""
        item = self.evolution_items.get(item_id)
        if not item:
            return False
        item.status = EvolutionStatus.VERIFY_PENDING.value
        if code_changes:
            item.code_changes = code_changes
        return True

    # ── 验证: 通过模拟人类操作的自动化测试 ─────────────────────

    def register_verify_test(self, test_name: str, test_fn: Callable) -> None:
        """注册一个验证测试函数。test_fn() -> (passed: bool, detail: str)"""
        self._verify_registry[test_name] = test_fn

    def verify_all_pending(self) -> Dict[str, Any]:
        """运行所有待验证项的自动化测试。"""
        results: List[Dict[str, Any]] = []

        for item in self.evolution_items.values():
            if item.status != EvolutionStatus.VERIFY_PENDING.value:
                continue

            test_fn = self._verify_registry.get(item.verify_test_name)
            if test_fn is None:
                # 也可以回退到重新运行 audit rule
                rule = self._get_rule_by_id(item.build_task_id)
                if rule and rule.check_fn:
                    channel = get_default_registry().get(item.target_channel)
                    if channel:
                        test_fn = lambda ch=channel, fn=rule.check_fn: fn(ch)

            if test_fn is None:
                results.append({
                    "item_id": item.id, "status": "skip",
                    "reason": f"验证函数 '{item.verify_test_name}' 未注册",
                })
                continue

            try:
                passed, detail = test_fn()
            except Exception as exc:
                passed, detail = False, f"验证异常: {exc}"

            item.verify_result = "passed" if passed else "failed"
            item.verify_detail = detail

            if passed:
                item.status = EvolutionStatus.VERIFIED.value
                item.completed_at = datetime.now().isoformat()
                self.total_verified += 1
            else:
                item.retry_count += 1
                if item.retry_count >= item.max_retries:
                    item.status = EvolutionStatus.FAILED.value
                    self.total_failed += 1
                else:
                    # 退回给 Build 团队重做
                    item.status = EvolutionStatus.DISPATCHED.value

            results.append({
                "item_id": item.id, "passed": passed, "detail": detail,
                "retry_count": item.retry_count,
            })

        return {"verified": results, "count": len(results)}

    def close_verified(self) -> List[str]:
        """关