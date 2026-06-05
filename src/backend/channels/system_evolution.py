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


class AwaitableDict(dict):
    """Dictionary result that can also be awaited by async callers."""

    def __await__(self):
        async def _wrap():
            return self

        return _wrap().__await__()


class EvolutionItemList:
    """List-style compatibility view over the evolution item dictionary."""

    def __init__(self, items: Dict[str, "EvolutionItem"]) -> None:
        self._items = items

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items.values())

    def __getitem__(self, index):
        values = list(self._items.values())
        return values[index]

    def append(self, item: "EvolutionItem") -> None:
        self._items[item.id] = item


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
    domain: str = ""
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
    build_artifacts: Dict[str, Any] = field(default_factory=dict)
    build_error: str = ""
    source_plaza_id: str = ""
    source_discussion_id: str = ""
    source_task_ids: List[str] = field(default_factory=list)
    artifact_dir: str = ""
    trace_context: Dict[str, Any] = field(default_factory=dict)

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

    def __post_init__(self) -> None:
        if self.domain and (
            not self.audit_domain or self.audit_domain == AuditDomain.GENERAL.value
        ):
            self.audit_domain = self.domain
        elif self.audit_domain and not self.domain:
            self.domain = self.audit_domain

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


# ── Skill Router / Extraction Audit Rules (SKILL domain) ──

def _get_skill_router():
    """Get SkillRouter instance via sys.modules (avoids relative import issues)."""
    import sys
    mod = sys.modules.get('agents.skill_router')
    if mod and hasattr(mod, 'get_skill_router'):
        return mod.get_skill_router()
    return None


def _get_team_manager():
    """Get TeamManager instance via SkillRouter or main module."""
    import sys
    # Try via skill_router (which holds a reference)
    sr = _get_skill_router()
    if sr and hasattr(sr, '_team_manager') and sr._team_manager:
        return sr._team_manager
    # Fallback: try main module
    main_mod = sys.modules.get('__main__')
    if main_mod and hasattr(main_mod, '_team_manager'):
        return main_mod._team_manager
    # Fallback: agents.api module
    api_mod = sys.modules.get('agents.api')
    if api_mod and hasattr(api_mod, '_team_manager'):
        return api_mod._team_manager
    return None


def _check_skill_pool_size(channel) -> Tuple[bool, str]:
    """Check that skill pool has sufficient coverage for routing quality."""
    try:
        sr = _get_skill_router()
        if not sr:
            return False, "SkillRouter 未初始化"
        skills = sr._get_skill_pool("") if sr._skill_library else []
        if not skills:
            skills = sr._get_skill_pool("build_system")
        count = len(skills)
        if count < 10:
            return False, f"技能池仅 {count} 项，需 ≥10 以保证路由覆盖度"
        return True, f"技能池 {count} 项，覆盖充足"
    except Exception as e:
        return False, f"技能池检查异常: {e}"


def _check_skill_categories_coverage(channel) -> Tuple[bool, str]:
    """Check that skills span at least 3 categories for diverse routing."""
    try:
        sr = _get_skill_router()
        if not sr:
            return False, "SkillRouter 未初始化"
        skills = sr._get_skill_pool("") or sr._get_skill_pool("build_system")
        categories = set(s.get("category", "general") for s in skills)
        if len(categories) < 3:
            return False, f"仅 {len(categories)} 个类别，需 ≥3 保证多样性"
        return True, f"{len(categories)} 个技能类别，多样性良好"
    except Exception as e:
        return False, f"类别检查异常: {e}"


def _check_agent_skill_assignment(channel) -> Tuple[bool, str]:
    """Check that agents have skills assigned (not all empty)."""
    try:
        tm = _get_team_manager()
        if not tm:
            return False, "TeamManager 不可用"
        teams = tm.list_teams() if hasattr(tm, 'list_teams') else []
        total_agents = 0
        agents_with_skills = 0
        for team in teams:
            t = tm.get_team(team.get("team_id", "")) if isinstance(team, dict) else team
            if not t or not hasattr(t, 'agents'):
                continue
            for aid, agent in t.agents.items():
                total_agents += 1
                skills = getattr(agent, 'skills', None) or []
                if skills:
                    agents_with_skills += 1
        if total_agents == 0:
            return False, "无智能体注册"
        coverage = agents_with_skills / total_agents
        if coverage < 0.3:
            return False, f"仅 {agents_with_skills}/{total_agents} 智能体有技能赋予 ({coverage:.0%})，需 ≥30%"
        return True, f"{agents_with_skills}/{total_agents} 智能体已赋予技能 ({coverage:.0%})"
    except Exception as e:
        return False, f"技能赋予检查异常: {e}"


def _check_skill_instructions_quality(channel) -> Tuple[bool, str]:
    """Check that skills have non-empty instructions (body) for deep matching."""
    try:
        sr = _get_skill_router()
        if not sr:
            return False, "SkillRouter 未初始化"
        skills = sr._get_skill_pool("") or sr._get_skill_pool("build_system")
        if not skills:
            return False, "技能池为空"
        with_instructions = sum(1 for s in skills if s.get("has_instructions") or s.get("instructions", "").strip())
        ratio = with_instructions / len(skills)
        if ratio < 0.5:
            return False, f"仅 {with_instructions}/{len(skills)} 技能有详细 instructions ({ratio:.0%})，影响深度匹配"
        return True, f"{with_instructions}/{len(skills)} 技能含详细 instructions ({ratio:.0%})"
    except Exception as e:
        return False, f"instructions 质量检查异常: {e}"


def _check_router_latency(channel) -> Tuple[bool, str]:
    """Check that router performance is within acceptable bounds."""
    try:
        sr = _get_skill_router()
        if not sr:
            return False, "SkillRouter 未初始化"
        sessions = list(sr._sessions.values())
        if not sessions:
            return True, "无路由历史，延迟基准待建立"
        avg_ms = sum(s.duration_ms for s in sessions) / len(sessions)
        if avg_ms > 500:
            return False, f"平均路由延迟 {avg_ms:.0f}ms，超过 500ms 阈值"
        return True, f"平均路由延迟 {avg_ms:.1f}ms，性能良好"
    except Exception as e:
        return False, f"延迟检查异常: {e}"


def _check_routing_feedback_loop(channel) -> Tuple[bool, str]:
    """Check that feedback mechanism is active and informing routing."""
    try:
        sr = _get_skill_router()
        if not sr:
            return False, "SkillRouter 未初始化"
        total_feedback = sum(len(v) for v in sr._feedback.values())
        if total_feedback == 0:
            return False, "无反馈数据，路由质量无法闭环优化"
        boosts = len(sr._affinity_boosts)
        return True, f"已收集 {total_feedback} 条反馈，{boosts} 项亲和度调整生效"
    except Exception as e:
        return False, f"反馈检查异常: {e}"


# 所有内置审查规则
BUILTIN_AUDIT_RULES: List[AuditRule] = [
    # ── Skill Router & Extraction Rules (SKILL domain) ──
    AuditRule(
        id="SKILL-POOL-050",
        domain=AuditDomain.GENERAL.value,
        title="技能池规模达标",
        description="技能池需 ≥10 项以保证路由检索的召回率",
        target_channel="system_evolution",
        check_fn=_check_skill_pool_size,
        reference="SkillRouter Paper §3.2 — Pool Size vs Recall",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.5,
    ),
    AuditRule(
        id="SKILL-CAT-051",
        domain=AuditDomain.GENERAL.value,
        title="技能类别多样性",
        description="技能须覆盖 ≥3 个类别，避免路由偏向单一领域",
        target_channel="system_evolution",
        check_fn=_check_skill_categories_coverage,
        reference="Diversity Index for Skill Taxonomies",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="SKILL-ASSIGN-052",
        domain=AuditDomain.GENERAL.value,
        title="智能体技能赋予覆盖率",
        description="≥30% 智能体应有至少 1 项技能赋予",
        target_channel="system_evolution",
        check_fn=_check_agent_skill_assignment,
        reference="Agent Capability Matrix Coverage",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=2.5,
    ),
    AuditRule(
        id="SKILL-INST-053",
        domain=AuditDomain.GENERAL.value,
        title="技能 Instructions 充实度",
        description="≥50% 技能须含详细 instructions 以支撑深度语义匹配",
        target_channel="system_evolution",
        check_fn=_check_skill_instructions_quality,
        reference="SkillRouter Stage2 — Instructions Field Weight",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="SKILL-PERF-054",
        domain=AuditDomain.GENERAL.value,
        title="路由引擎延迟达标",
        description="平均路由延迟应 ≤500ms (Stage1+Stage2 合计)",
        target_channel="system_evolution",
        check_fn=_check_router_latency,
        reference="SkillRouter SLA — P95 < 1s",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.ADVANCED_OPS.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="SKILL-FDBK-055",
        domain=AuditDomain.GENERAL.value,
        title="路由质量反馈闭环",
        description="需有反馈数据驱动路由亲和度学习",
        target_channel="system_evolution",
        check_fn=_check_routing_feedback_loop,
        reference="Reinforcement from Human Feedback (RLHF)",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.SHIP.value,
        rating_weight=2.0,
    ),
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

    @property
    def discovered_items(self) -> EvolutionItemList:
        """Legacy list-style view of discovered evolution items."""
        return EvolutionItemList(self.evolution_items)

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
            channel = self if rule.target_channel == self.name else registry.get(rule.target_channel)
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

        result = AwaitableDict({
            "audit_run": self.total_audits,
            "rules_checked": len(results),
            "passed": sum(1 for r in results if r.get("passed")),
            "failed": sum(1 for r in results if r.get("passed") is False),
            "skipped": sum(1 for r in results if r.get("status") == "skip"),
            "new_items_created": new_items,
            "details": results,
        })

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

    async def dispatch_item(self, item_id: str) -> Optional[EvolutionItem]:
        """Async compatibility helper to dispatch a single evolution item."""
        item = self.evolution_items.get(item_id)
        if item is None:
            return None
        status = item.status.value if isinstance(item.status, EvolutionStatus) else item.status
        if status == EvolutionStatus.DISCOVERED.value:
            item.status = EvolutionStatus.DISPATCHED.value
            item.dispatched_at = datetime.now().isoformat()
            self.total_dispatched += 1
            self._record_trail(
                "dispatch",
                item_id=item.id,
                actor="system",
                old_value=EvolutionStatus.DISCOVERED.value,
                new_value=EvolutionStatus.DISPATCHED.value,
                detail=f"单项派发: {item.title}",
            )
        return item

    def mark_in_progress(self, item_id: str) -> bool:
        """Build 团队标记开始工作。"""
        item = self.evolution_items.get(item_id)
        if not item:
            return False
        item.status = EvolutionStatus.IN_PROGRESS.value
        return True

    def mark_build_complete(
        self,
        item_id: str,
        code_changes: Optional[List[str]] = None,
        artifact_dir: str = "",
    ) -> bool:
        """Build 团队标记修改完成，进入待验证。"""
        item = self.evolution_items.get(item_id)
        if not item:
            return False
        if code_changes:
            item.code_changes = code_changes
        if artifact_dir:
            item.artifact_dir = artifact_dir
        if not item.code_changes and not item.artifact_dir:
            logger.warning("Build complete rejected for %s: no artifacts recorded", item_id)
            return False
        item.status = EvolutionStatus.VERIFY_PENDING.value
        return True

    def sync_task_outcome(
        self,
        task_id: str,
        *,
        status: str,
        code_changes: Optional[List[str]] = None,
        artifact_dir: str = "",
        build_artifacts: Optional[Dict[str, Any]] = None,
        error: str = "",
    ) -> List[str]:
        """Sync Plaza-origin task execution results back into linked evolution items."""
        synced: List[str] = []
        normalized_changes = list(dict.fromkeys(code_changes or []))

        for item in self.evolution_items.values():
            if task_id not in item.source_task_ids:
                continue

            if normalized_changes:
                item.code_changes = list(dict.fromkeys(item.code_changes + normalized_changes))
            if artifact_dir:
                item.artifact_dir = artifact_dir
            if build_artifacts:
                item.build_artifacts = dict(build_artifacts)
                trace_context = build_artifacts.get("trace_context") or {}
                if trace_context:
                    merged = dict(item.trace_context)
                    merged.update(trace_context)
                    merged.setdefault("evolution_item_id", item.id)
                    item.trace_context = merged
            if error:
                item.build_error = error

            if status == EvolutionStatus.FAILED.value or status == "failed":
                self._update_item_escalation(item, False)
                item.status = EvolutionStatus.FAILED.value
            else:
                if item.status == EvolutionStatus.DISPATCHED.value:
                    item.status = EvolutionStatus.IN_PROGRESS.value
                if self._can_auto_close_from_artifacts(item, build_artifacts):
                    self._update_item_escalation(item, True)
                    now = datetime.now().isoformat()
                    if item.status not in {EvolutionStatus.VERIFIED.value, EvolutionStatus.CLOSED.value}:
                        self.total_verified += 1
                    if item.status != EvolutionStatus.CLOSED.value:
                        self.total_closed += 1
                    item.verify_result = "passed"
                    item.verify_detail = "Auto-verified from task test results"
                    item.completed_at = item.completed_at or now
                    item.closed_at = now
                    item.status = EvolutionStatus.CLOSED.value
                elif item.code_changes or item.artifact_dir:
                    if item.verify_test_name:
                        item.verify_result = "pending"
                        item.verify_detail = f"Awaiting verify test: {item.verify_test_name}"
                    item.status = EvolutionStatus.VERIFY_PENDING.value

            synced.append(item.id)

        return synced

    def _can_auto_close_from_artifacts(
        self,
        item: EvolutionItem,
        build_artifacts: Optional[Dict[str, Any]],
    ) -> bool:
        """Allow Plaza-derived items with passing task evidence to close automatically."""
        if not build_artifacts:
            return False
        if item.verify_test_name:
            return False
        if self._get_rule_by_id(item.build_task_id):
            return False
        test_result = build_artifacts.get("test_result") or {}
        verdict = str(test_result.get("verdict", "")).upper()
        test_status = str(test_result.get("status", "")).lower()
        return (
            build_artifacts.get("build_outcome") == "completed"
            and test_status == "completed"
            and verdict in {"PASS", "PASSED", "OK"}
        )

    # ── 验证: 通过模拟人类操作的自动化测试 ─────────────────────

    def register_verify_test(self, test_name: str, test_fn: Callable) -> None:
        """注册一个验证测试函数。test_fn() -> (passed: bool, detail: str)"""
        self._verify_registry[test_name] = test_fn

    def verify_all_pending(self) -> Dict[str, Any]:
        """运行所有待验证项的自动化测试。"""
        return self.verify_pending_items()

    def _update_item_escalation(self, item: EvolutionItem, passed: bool) -> None:
        """Update per-item escalation state based on consecutive failures."""
        if passed:
            item.consecutive_failures = 0
            item.escalation_tier = EscalationTier.NORMAL.value
            return

        item.consecutive_failures += 1
        if item.consecutive_failures >= 4:
            item.escalation_tier = EscalationTier.CRITICAL_HOLD.value
        elif item.consecutive_failures >= 3:
            item.escalation_tier = EscalationTier.MANAGEMENT_REVIEW.value
        elif item.consecutive_failures >= 2:
            item.escalation_tier = EscalationTier.CORRECTIVE_PLAN.value
        else:
            item.escalation_tier = EscalationTier.NORMAL.value

    def _record_evolution_verify_evidence(
        self,
        item: EvolutionItem,
        *,
        status: str,
        detail: str,
        exit_code: Optional[int],
    ) -> str:
        """Persist an evolution verification attempt as EvidenceRun."""
        try:
            from agents.evidence_store import EvidenceRun, get_evidence_store

            run = EvidenceRun.create(
                evidence_type="evolution_verify",
                status=status,
                summary=f"演进验证: {item.id} -> {status}",
                team_id="build_team",
                agent_id=item.assigned_agent or "system_evolution",
                task_id=item.build_task_id,
                evolution_item_id=item.id,
                plaza_topic_id=item.source_plaza_id or None,
                request_id=f"evolution-verify:{item.id}:{datetime.now().isoformat()}",
                runtime={
                    "mode": "in_process",
                    "component": "system_evolution",
                    "verify_test_name": item.verify_test_name,
                    "target_channel": item.target_channel,
                },
                command=f"system_evolution.verify:{item.verify_test_name or item.build_task_id or 'unregistered'}",
                exit_code=exit_code,
                artifact_dir=item.artifact_dir,
                metrics_after={
                    "retry_count": item.retry_count,
                    "max_retries": item.max_retries,
                    "consecutive_failures": item.consecutive_failures,
                    "escalation_tier": item.escalation_tier,
                },
                detail={
                    "verify_detail": detail,
                    "verify_result": item.verify_result,
                    "item_status": item.status,
                    "item": item.to_dict(),
                },
            )
            get_evidence_store().append_evidence_sync(run)
            return run.evidence_id
        except Exception as exc:
            logger.warning("Failed to record evolution verification EvidenceRun: %s", exc)
            return ""

    def verify_pending_items(
        self,
        *,
        item_ids: Optional[List[str]] = None,
        source_plaza_id: str = "",
        source_discussion_id: str = "",
    ) -> Dict[str, Any]:
        """Run verification for a filtered set of pending items."""
        results: List[Dict[str, Any]] = []
        item_id_filter = set(item_ids or [])

        for item in self.evolution_items.values():
            if item.status != EvolutionStatus.VERIFY_PENDING.value:
                continue
            if item_id_filter and item.id not in item_id_filter:
                continue
            if source_plaza_id and item.source_plaza_id != source_plaza_id:
                continue
            if source_discussion_id and item.source_discussion_id != source_discussion_id:
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
                evidence_run_id = self._record_evolution_verify_evidence(
                    item,
                    status="blocked",
                    detail=f"验证函数 '{item.verify_test_name}' 未注册",
                    exit_code=None,
                )
                results.append({
                    "item_id": item.id, "status": "skip",
                    "reason": f"验证函数 '{item.verify_test_name}' 未注册",
                    "evidence_run_id": evidence_run_id,
                })
                continue

            try:
                passed, detail = test_fn()
            except Exception as exc:
                passed, detail = False, f"验证异常: {exc}"

            item.verify_result = "passed" if passed else "failed"
            item.verify_detail = detail
            self._update_item_escalation(item, passed)

            if passed:
                item.status = EvolutionStatus.VERIFIED.value
                item.completed_at = datetime.now().isoformat()
                self.total_verified += 1
            else:
                item.retry_count += 1
                if item.retry_count >= item.max_retries:
                    item.status = EvolutionStatus.FAILED.value
                    item.verify_detail = f"{detail} (max retries exhausted)"
                    self.total_failed += 1
                else:
                    # 退回给 Build 团队重做
                    item.status = EvolutionStatus.DISPATCHED.value
                    item.verify_detail = (
                        f"{detail} (retry queued {item.retry_count}/{item.max_retries})"
                    )

            evidence_run_id = self._record_evolution_verify_evidence(
                item,
                status="passed" if passed else "failed",
                detail=detail,
                exit_code=0 if passed else 1,
            )
            results.append({
                "item_id": item.id, "passed": passed, "detail": detail,
                "retry_count": item.retry_count,
                "evidence_run_id": evidence_run_id,
            })

        return {"verified": results, "count": len(results)}

    def _build_verification_alert(self, item: EvolutionItem) -> Optional[Dict[str, Any]]:
        """Summarize verification follow-up required for an evolution item."""
        alert_level = ""
        next_action = ""
        if item.status == EvolutionStatus.FAILED.value:
            alert_level = "critical"
            next_action = "manual_intervention"
        elif item.status == EvolutionStatus.VERIFY_PENDING.value and item.verify_test_name:
            alert_level = "warning"
            next_action = f"run_verify_test:{item.verify_test_name}"
        elif item.status == EvolutionStatus.DISPATCHED.value and item.retry_count > 0:
            alert_level = "warning"
            next_action = "redispatch_build"
        elif item.retry_count > 0:
            alert_level = "info"
            next_action = "inspect_retry_state"

        if not alert_level:
            return None

        return {
            "item_id": item.id,
            "title": item.title,
            "status": item.status,
            "verify_test_name": item.verify_test_name,
            "verify_result": item.verify_result,
            "verify_detail": item.verify_detail,
            "retry_count": item.retry_count,
            "max_retries": item.max_retries,
            "retries_remaining": max(item.max_retries - item.retry_count, 0),
            "consecutive_failures": item.consecutive_failures,
            "escalation_tier": item.escalation_tier,
            "escalation_label": self._escalation_label(item.escalation_tier),
            "alert_level": alert_level,
            "next_action": next_action,
            "source_plaza_id": item.source_plaza_id,
            "source_discussion_id": item.source_discussion_id,
            "source_task_ids": list(item.source_task_ids),
        }

    def get_verification_alerts(
        self,
        *,
        source_plaza_id: str = "",
        source_discussion_id: str = "",
    ) -> List[Dict[str, Any]]:
        """Return pending/failing verification items that need follow-up."""
        alerts: List[Dict[str, Any]] = []
        for item in self.evolution_items.values():
            if source_plaza_id and item.source_plaza_id != source_plaza_id:
                continue
            if source_discussion_id and item.source_discussion_id != source_discussion_id:
                continue
            alert = self._build_verification_alert(item)
            if alert:
                alerts.append(alert)
        alerts.sort(
            key=lambda alert: (
                0 if alert["alert_level"] == "critical" else 1,
                0 if alert["status"] == EvolutionStatus.VERIFY_PENDING.value else 1,
                alert["item_id"],
            )
        )
        return alerts

    def get_verification_queue(
        self,
        *,
        source_plaza_id: str = "",
        source_discussion_id: str = "",
    ) -> List[Dict[str, Any]]:
        """Return linked evolution items, prioritizing entries still waiting on verification."""
        items: List[Dict[str, Any]] = []
        for item in self.evolution_items.values():
            if source_plaza_id and item.source_plaza_id != source_plaza_id:
                continue
            if source_discussion_id and item.source_discussion_id != source_discussion_id:
                continue
            items.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "status": item.status,
                    "verify_test_name": item.verify_test_name,
                    "verify_result": item.verify_result,
                    "verify_detail": item.verify_detail,
                    "retry_count": item.retry_count,
                    "max_retries": item.max_retries,
                    "source_task_ids": list(item.source_task_ids),
                    "requires_manual_verify": bool(
                        item.verify_test_name and item.status == EvolutionStatus.VERIFY_PENDING.value
                    ),
                    "consecutive_failures": item.consecutive_failures,
                    "escalation_tier": item.escalation_tier,
                    "escalation_label": self._escalation_label(item.escalation_tier),
                }
            )

        items.sort(
            key=lambda item: (
                0 if item["requires_manual_verify"] else 1,
                0 if item["status"] == EvolutionStatus.VERIFY_PENDING.value else 1,
                item["id"],
            )
        )
        return items

    def close_verified(self) -> List[str]:
        """关闭所有已验证通过的演进项。"""
        return self.close_verified_items()

    def close_verified_items(
        self,
        *,
        item_ids: Optional[List[str]] = None,
        source_plaza_id: str = "",
        source_discussion_id: str = "",
    ) -> List[str]:
        """Close a filtered set of verified items."""
        closed: List[str] = []
        item_id_filter = set(item_ids or [])
        for item in self.evolution_items.values():
            if item.status == EvolutionStatus.VERIFIED.value:
                if item_id_filter and item.id not in item_id_filter:
                    continue
                if source_plaza_id and item.source_plaza_id != source_plaza_id:
                    continue
                if source_discussion_id and item.source_discussion_id != source_discussion_id:
                    continue
                item.status = EvolutionStatus.CLOSED.value
                item.closed_at = datetime.now().isoformat()
                self.total_closed += 1
                closed.append(item.id)
        return closed

    def _get_rule_by_id(self, rule_id: Optional[str]) -> Optional[AuditRule]:
        if not rule_id:
            return None
        for rule in self.audit_rules:
            if rule.id == rule_id:
                return rule
        return None

    # ── 完整演进周期 ──────────────────────────────────────────

    def run_evolution_cycle(self) -> Dict[str, Any]:
        """一键运行完整的审查→派发→验证→关闭循环。"""
        audit_result = self.run_full_audit()
        dispatch_result = self.dispatch_all_pending()

        verify_result = self.verify_all_pending()
        closed = self.close_verified()

        return {
            "cycle": self.total_audits,
            "audit": audit_result,
            "dispatch": dispatch_result,
            "verify": verify_result,
            "closed": closed,
            "summary": self.get_evolution_summary(),
        }

    # ── 查询接口 ──────────────────────────────────────────────

    def get_evolution_items(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取演进项列表，可按状态过滤。"""
        items = self.evolution_items.values()
        if status:
            items = [i for i in items if i.status == status]
        return [i.to_dict() for i in items]

    def get_evolution_summary(self) -> Dict[str, Any]:
        """演进状态汇总。"""
        by_status: Dict[str, int] = {}
        by_domain: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        by_operational_domain: Dict[str, int] = {}
        by_checklist_level: Dict[str, int] = {}
        for item in self.evolution_items.values():
            by_status[item.status] = by_status.get(item.status, 0) + 1
            by_domain[item.audit_domain] = by_domain.get(item.audit_domain, 0) + 1
            by_severity[item.severity] = by_severity.get(item.severity, 0) + 1
            od = item.operational_domain or "unknown"
            by_operational_domain[od] = by_operational_domain.get(od, 0) + 1
            cl = item.checklist_level or "ship"
            by_checklist_level[cl] = by_checklist_level.get(cl, 0) + 1

        return {
            "total_items": len(self.evolution_items),
            "by_status": by_status,
            "by_domain": by_domain,
            "by_severity": by_severity,
            "by_operational_domain": by_operational_domain,
            "by_checklist_level": by_checklist_level,
            "audit_rules_count": len(self.audit_rules),
            "verify_tests_registered": len(self._verify_registry),
            "compliance_rating": self._compliance_rating,
            "compliance_score": self._compliance_score,
            "active_zones": len(self._active_zone_ids),
            "zones_total": len(self.compliance_zones),
        }

    def add_audit_rule(self, rule: AuditRule) -> None:
        """动态添加审查规则。"""
        self.audit_rules.append(rule)

    def get_audit_history(self) -> List[Dict[str, Any]]:
        """返回审查历史记录列表 (最近 50 次)。"""
        return list(reversed(self.audit_history))

    # ══════════════════════════════════════════════════════════
    # Phase 3: A~E 合规评级系统 (DNV CII 风格)
    # ══════════════════════════════════════════════════════════

    def calculate_compliance_rating(self, audit_details: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        基于审查结果计算加权合规分数和 A~E 评级。
        权重: critical=4x, high=3x, medium=2x, low=1x, 乘以 rule.rating_weight。
        """
        if audit_details is None:
            # 使用最近一次审查结果
            if not self.audit_history:
                return {"score": 100.0, "rating": "A", "detail": "尚未运行审查"}
            # 运行一次快速审查获取结果
            result = self._quick_score_audit()
            audit_details = result

        severity_weight = {
            Severity.CRITICAL.value: 4.0,
            Severity.HIGH.value: 3.0,
            Severity.MEDIUM.value: 2.0,
            Severity.LOW.value: 1.0,
        }

        total_weight = 0.0
        earned_weight = 0.0
        details_by_domain: Dict[str, Dict] = {}

        for rule in self.audit_rules:
            sev_w = severity_weight.get(rule.severity, 1.0)
            rule_w = rule.rating_weight
            w = sev_w * rule_w
            total_weight += w

            # 查找此规则的审查结果
            result_entry = None
            for d in audit_details:
                if d.get("rule") == rule.id:
                    result_entry = d
                    break

            if result_entry and result_entry.get("passed") is True:
                earned_weight += w
            elif result_entry and result_entry.get("status") == "skip":
                # 跳过的规则不扣分也不加分
                total_weight -= w

            # 按操作域汇总
            od = rule.operational_domain
            if od not in details_by_domain:
                details_by_domain[od] = {"total": 0.0, "earned": 0.0, "count": 0, "passed": 0}
            details_by_domain[od]["total"] += w
            details_by_domain[od]["count"] += 1
            if result_entry and result_entry.get("passed") is True:
                details_by_domain[od]["earned"] += w
                details_by_domain[od]["passed"] += 1

        score = (earned_weight / total_weight * 100) if total_weight > 0 else 100.0
        rating = ComplianceRating.from_score(score)

        # 更新内部状态
        old_rating = self._compliance_rating
        self._compliance_score = round(score, 1)
        self._compliance_rating = rating.value

        # 记录评级变化
        record = {
            "time": datetime.now().isoformat(),
            "score": self._compliance_score,
            "rating": rating.value,
        }
        self._rating_history.append(record)
        if len(self._rating_history) > 100:
            self._rating_history = self._rating_history[-100:]

        # 趋势记录
        self._score_trend.append({
            "time": datetime.now().isoformat(),
            "score": self._compliance_score,
            "rating": rating.value,
            "passed": sum(1 for d in audit_details if d.get("passed") is True),
            "failed": sum(1 for d in audit_details if d.get("passed") is False),
        })
        if len(self._score_trend) > 50:
            self._score_trend = self._score_trend[-50:]

        # 审计轨迹
        if old_rating != rating.value:
            self._record_trail("rating_change", detail=f"评级变化 {old_rating} → {rating.value}",
                               old_value=old_rating, new_value=rating.value,
                               compliance_rating=rating.value)

        # 域级评分
        domain_scores: Dict[str, Dict] = {}
        for od, dd in details_by_domain.items():
            ds = (dd["earned"] / dd["total"] * 100) if dd["total"] > 0 else 100.0
            domain_scores[od] = {
                "score": round(ds, 1),
                "rating": ComplianceRating.from_score(ds).value,
                "rules_total": dd["count"],
                "rules_passed": dd["passed"],
            }

        return {
            "score": self._compliance_score,
            "rating": rating.value,
            "rating_label": self._rating_label(rating.value),
            "total_weight": round(total_weight, 1),
            "earned_weight": round(earned_weight, 1),
            "domain_scores": domain_scores,
            "rating_history": self._rating_history[-10:],
        }

    @staticmethod
    def _rating_label(rating: str) -> str:
        labels = {
            "A": "Major Superior — 全面优秀",
            "B": "Minor Superior — 良好",
            "C": "Moderate — 基本合规",
            "D": "Minor Inferior — 需纠正计划",
            "E": "Inferior — 需紧急干预",
        }
        return labels.get(rating, rating)

    def _quick_score_audit(self) -> List[Dict]:
        """快速运行审查仅获取 pass/fail 结果 (不创建 EvolutionItem)。"""
        registry = get_default_registry()
        results: List[Dict[str, Any]] = []
        for rule in self.audit_rules:
            channel = registry.get(rule.target_channel)
            if not channel:
                results.append({"rule": rule.id, "status": "skip"})
                continue
            if rule.check_fn is None:
                results.append({"rule": rule.id, "status": "skip"})
                continue
            try:
                passed, detail = rule.check_fn(channel)
            except Exception:
                passed = False
                detail = "check exception"
            results.append({"rule": rule.id, "passed": passed, "detail": detail})
        return results

    def get_compliance_rating(self) -> Dict[str, Any]:
        """获取当前合规评级 (不会重新审查)。"""
        return {
            "score": self._compliance_score,
            "rating": self._compliance_rating,
            "rating_label": self._rating_label(self._compliance_rating),
            "trend": self._score_trend[-10:],
        }

    # ══════════════════════════════════════════════════════════
    # Phase 3: 双层自查清单 (ClassNK 风格)
    # ══════════════════════════════════════════════════════════

    def get_checklist(self, level: Optional[str] = None) -> Dict[str, Any]:
        """获取按 ClassNK 双层模型组织的自查清单。"""
        company_rules = []
        ship_rules = []

        for rule in self.audit_rules:
            entry = {
                "id": rule.id,
                "title": rule.title,
                "domain": rule.domain,
                "severity": rule.severity,
                "reference": rule.reference,
                "operational_domain": rule.operational_domain,
            }
            if rule.checklist_level in (ChecklistLevel.COMPANY.value, ChecklistLevel.BOTH.value):
                company_rules.append(entry)
            if rule.checklist_level in (ChecklistLevel.SHIP.value, ChecklistLevel.BOTH.value):
                ship_rules.append(entry)

        result: Dict[str, Any] = {"total_rules": len(self.audit_rules)}

        if level is None or level == ChecklistLevel.COMPANY.value:
            result["company_checklist"] = {
                "level": "company",
                "label": "公司安全管理体系自查 (ISM DOC)",
                "count": len(company_rules),
                "items": company_rules,
            }
        if level is None or level == ChecklistLevel.SHIP.value:
            result["ship_checklist"] = {
                "level": "ship",
                "label": "船舶安全管理体系自查 (ISM SMC)",
                "count": len(ship_rules),
                "items": ship_rules,
            }

        return result

    # ══════════════════════════════════════════════════════════
    # Phase 3: 地理围栏合规 (Wärtsilä Zone Management)
    # ══════════════════════════════════════════════════════════

    def update_vessel_position(self, lat: float, lon: float) -> Dict[str, Any]:
        """更新船舶位置，自动检测进入/离开合规区域。"""
        old_active = set(self._active_zone_ids)
        self._vessel_position = {"lat": lat, "lon": lon}

        new_active: List[str] = []
        for zone in self.compliance_zones:
            if zone.active and zone.contains(lat, lon):
                new_active.append(zone.id)

        self._active_zone_ids = new_active
        new_active_set = set(new_active)

        entered = new_active_set - old_active
        exited = old_active - new_active_set

        events: List[Dict] = []
        for zid in entered:
            zone = self._get_zone(zid)
            if zone:
                events.append({
                    "event": "zone_enter",
                    "zone_id": zid,
                    "zone_name": zone.name,
                    "zone_type": zone.zone_type,
                    "activated_rules": zone.activated_rule_ids,
                    "extra_requirements": zone.extra_requirements,
                })
                self._record_trail("zone_enter", zone_id=zid,
                                   detail=f"进入合规区域: {zone.name} ({zone.zone_type})")

        for zid in exited:
            zone = self._get_zone(zid)
            if zone:
                events.append({
                    "event": "zone_exit",
                    "zone_id": zid,
                    "zone_name": zone.name,
                })
                self._record_trail("zone_exit", zone_id=zid,
                                   detail=f"离开合规区域: {zone.name}")

        return {
            "position": self._vessel_position,
            "active_zones": new_active,
            "entered": list(entered),
            "exited": list(exited),
            "events": events,
        }

    def get_active_zones(self) -> List[Dict[str, Any]]:
        """获取当前激活的合规区域列表。"""
        result = []
        for zid in self._active_zone_ids:
            zone = self._get_zone(zid)
            if zone:
                result.append(zone.to_dict())
        return result

    def get_zone_activated_rules(self) -> List[str]:
        """获取当前区域内激活的所有规则 ID (去重)。"""
        rule_ids: set = set()
        for zid in self._active_zone_ids:
            zone = self._get_zone(zid)
            if zone:
                rule_ids.update(zone.activated_rule_ids)
        return sorted(rule_ids)

    def get_all_zones(self) -> List[Dict[str, Any]]:
        """获取所有注册的合规区域。"""
        return [z.to_dict() for z in self.compliance_zones]

    def _get_zone(self, zone_id: str) -> Optional[ComplianceZone]:
        for z in self.compliance_zones:
            if z.id == zone_id:
                return z
        return None

    # ══════════════════════════════════════════════════════════
    # Phase 3: 失败升级机制 (DNV SEEMP Part III)
    # ══════════════════════════════════════════════════════════

    def _update_escalation(self, rule_id: str, passed: bool) -> Optional[str]:
        """更新规则失败计数和升级层级。返回新的升级层级或 None。"""
        if passed:
            # 通过时重置
            self._rule_failure_counts[rule_id] = 0
            old_level = self._escalation_levels.get(rule_id, EscalationTier.NORMAL.value)
            self._escalation_levels[rule_id] = EscalationTier.NORMAL.value
            if old_level != EscalationTier.NORMAL.value:
                self._record_trail("escalation_reset", rule_id=rule_id,
                                   old_value=old_level, new_value=EscalationTier.NORMAL.value,
                                   detail=f"规则 {rule_id} 通过，升级层级重置")
            return None

        count = self._rule_failure_counts.get(rule_id, 0) + 1
        self._rule_failure_counts[rule_id] = count

        old_level = self._escalation_levels.get(rule_id, EscalationTier.NORMAL.value)
        if count >= 4:
            new_level = EscalationTier.CRITICAL_HOLD.value
        elif count >= 3:
            new_level = EscalationTier.MANAGEMENT_REVIEW.value
        elif count >= 2:
            new_level = EscalationTier.CORRECTIVE_PLAN.value
        else:
            new_level = EscalationTier.NORMAL.value

        self._escalation_levels[rule_id] = new_level
        if new_level != old_level and new_level != EscalationTier.NORMAL.value:
            self._record_trail("escalation", rule_id=rule_id,
                               old_value=old_level, new_value=new_level,
                               detail=f"规则 {rule_id} 连续失败 {count} 次，升级至 {new_level}")
            logger.warning("🚨 Escalation: rule %s → %s (consecutive failures: %d)",
                           rule_id, new_level, count)
        return new_level

    def get_escalation_status(self) -> Dict[str, Any]:
        """获取所有规则的升级状态。"""
        escalated = {}
        for rule_id, level in self._escalation_levels.items():
            if level != EscalationTier.NORMAL.value:
                escalated[rule_id] = {
                    "level": level,
                    "consecutive_failures": self._rule_failure_counts.get(rule_id, 0),
                    "label": self._escalation_label(level),
                }
        return {
            "escalated_count": len(escalated),
            "rules": escalated,
            "total_tracked": len(self._rule_failure_counts),
        }

    @staticmethod
    def _escalation_label(level: str) -> str:
        labels = {
            EscalationTier.NORMAL.value: "正常",
            EscalationTier.CORRECTIVE_PLAN.value: "需纠正行动计划",
            EscalationTier.MANAGEMENT_REVIEW.value: "需管理层审查",
            EscalationTier.CRITICAL_HOLD.value: "暂停相关操作",
        }
        return labels.get(level, level)

    # ══════════════════════════════════════════════════════════
    # Phase 3: 审计轨迹 (NAPA Logbook)
    # ══════════════════════════════════════════════════════════

    def _record_trail(self, event_type: str, rule_id: str = "", item_id: str = "",
                      actor: str = "system", old_value: str = "", new_value: str = "",
                      detail: str = "", compliance_rating: str = "", zone_id: str = "") -> None:
        """记录一条不可变的审计轨迹。"""
        entry = AuditTrailEntry(
            event_type=event_type, rule_id=rule_id, item_id=item_id,
            actor=actor, old_value=old_value, new_value=new_value,
            detail=detail, compliance_rating=compliance_rating or self._compliance_rating,
            zone_id=zone_id,
        )
        self._audit_trail.append(entry)
        if len(self._audit_trail) > self._max_trail_entries:
            self._audit_trail = self._audit_trail[-self._max_trail_entries:]

    def get_audit_trail(self, event_type: Optional[str] = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """获取审计轨迹，可按事件类型过滤。"""
        trail = self._audit_trail
        if event_type:
            trail = [e for e in trail if e.event_type == event_type]
        return [e.to_dict() for e in trail[-limit:]]

    # ══════════════════════════════════════════════════════════
    # Phase 3: 连续监控 + 趋势分析 (Wärtsilä FOS)
    # ══════════════════════════════════════════════════════════

    def get_trend_analysis(self) -> Dict[str, Any]:
        """获取合规评级趋势分析数据。"""
        trend = self._score_trend
        if len(trend) < 2:
            return {
                "data_points": len(trend),
                "trend_direction": "insufficient_data",
                "current_score": self._compliance_score,
                "current_rating": self._compliance_rating,
                "scores": trend,
            }

        recent = trend[-5:]
        scores = [t["score"] for t in recent]
        avg_recent = sum(scores) / len(scores)

        if len(trend) > 5:
            earlier = trend[-10:-5]
            avg_earlier = sum(t["score"] for t in earlier) / len(earlier)
            delta = avg_recent - avg_earlier
        else:
            delta = 0.0

        if delta > 3:
            direction = "improving"
        elif delta < -3:
            direction = "degrading"
        else:
            direction = "stable"

        return {
            "data_points": len(trend),
            "trend_direction": direction,
            "trend_delta": round(delta, 1),
            "current_score": self._compliance_score,
            "current_rating": self._compliance_rating,
            "avg_recent_5": round(avg_recent, 1),
            "scores": trend[-20:],
            "rating_history": self._rating_history[-10:],
        }

    def get_monitoring_status(self) -> Dict[str, Any]:
        """获取连续监控状态。"""
        now = time.time()
        since_last = now - self._last_monitoring_time if self._last_monitoring_time else None
        return {
            "interval_seconds": self._monitoring_interval,
            "seconds_since_last": round(since_last, 1) if since_last else None,
            "active_zones": len(self._active_zone_ids),
            "vessel_position": self._vessel_position,
            "compliance_rating": self._compliance_rating,
            "compliance_score": self._compliance_score,
            "escalated_rules": sum(1 for v in self._escalation_levels.values()
                                   if v != EscalationTier.NORMAL.value),
        }

    # ── Build 团队反馈接收 ────────────────────────────────────

    def accept_build_feedback(
        self, item_id: str, success: bool,
        code_changes: Optional[List[str]] = None, detail: str = "",
    ) -> Dict[str, Any]:
        """Build 团队完成修改后回调。"""
        item = self.evolution_items.get(item_id)
        if not item:
            return {"status": "error", "reason": f"Item {item_id} not found"}

        if success:
            item.status = EvolutionStatus.VERIFY_PENDING.value
            if code_changes:
                item.code_changes = code_changes
            return {"status": "verify_pending", "item_id": item_id}
        else:
            self._update_item_escalation(item, False)
            item.retry_count += 1
            if item.retry_count >= item.max_retries:
                item.status = EvolutionStatus.FAILED.value
                self.total_failed += 1
            else:
                item.status = EvolutionStatus.DISPATCHED.value
            return {
                "status": item.status, "item_id": item_id,
                "retry": item.retry_count, "detail": detail,
            }


__all__ = [
    "SystemEvolutionChannel",
    "EvolutionItem",
    "EvolutionStatus",
    "Severity",
    "AuditDomain",
    "AuditRule",
    "ComplianceRating",
    "OperationalDomain",
    "ChecklistLevel",
    "EscalationTier",
    "ComplianceZone",
    "AuditTrailEntry",
    "BUILTIN_AUDIT_RULES",
    "BUILTIN_COMPLIANCE_ZONES",
]
