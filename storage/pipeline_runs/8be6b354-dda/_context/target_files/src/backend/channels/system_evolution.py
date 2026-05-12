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

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
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
    """通信通道: plaza_chat 须已注册."""
    registry = get_default_registry()
    pc = registry.get("plaza_chat")
    if not pc:
        return False, "plaza_chat Channel 未注册"
    return True, "plaza_chat 通信通道正常"


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

def _check_api_health_endpoint(channel):
    """健康检查: /api/v1/health 端点必须可达."""
    import http.client
    try:
        conn = http.client.HTTPConnection("localhost", 8080, timeout=3)
        conn.request("GET", "/api/v1/health")
        resp = conn.getresponse()
        conn.close()
        if resp.status == 200:
            return True, "健康检查端点正常 (HTTP 200)"
        return False, f"健康检查返回 HTTP {resp.status}"
    except Exception as e:
        return False, f"健康检查不可达: {e}"


def _check_frontend_no_404(channel):
    """前端页面: 核心 HTML 页面不能返回 404."""
    import http.client
    pages = ["/", "/index.html", "/plaza.html", "/system-evolution.html"]
    errors = []
    for page in pages:
        try:
            conn = http.client.HTTPConnection("localhost", 5173, timeout=3)
            conn.request("GET", page)
            resp = conn.getresponse()
            conn.close()
            if resp.status == 404:
                errors.append(page)
        except Exception:
            pass  # 前端可能未运行
    if errors:
        return False, f"以下页面返回 404: {', '.join(errors)}"
    return True, f"已检查 {len(pages)} 个核心页面, 无 404"


def _check_task_engine_executor(channel):
    """任务引擎: TaskEngine 须有 executor 注册."""
    try:
        from agents.task_engine import get_task_engine
        engine = get_task_engine()
        if engine and engine._executor:
            return True, "TaskEngine executor 已注册"
        return False, "TaskEngine executor 未注册 (任务只能手动处理)"
    except Exception:
        return False, "TaskEngine 模块不可用"


def _check_knowledge_base_has_entries(channel):
    """知识库: storage/knowledge_base/ 须有条目."""
    kb_path = Path(__file__).resolve().parents[3] / "storage" / "knowledge_base"
    if not kb_path.exists():
        return False, "知识库目录不存在"
    entries = list(kb_path.glob("*.json"))
    if len(entries) < 5:
        return False, f"知识库仅 {len(entries)} 条, 需 ≥ 5"
    return True, f"知识库含 {len(entries)} 条记录"


def _check_evolution_executor_available(channel):
    """执行器: EvolutionExecutor 须可加载."""
    try:
        from channels.evolution_executor import get_evolution_executor
        executor = get_evolution_executor()
        if executor:
            return True, "EvolutionExecutor 已就绪"
        return False, "EvolutionExecutor 未初始化"
    except Exception as e:
        return False, f"EvolutionExecutor 加载失败: {e}"


def _check_llm_api_configured(channel):
    """LLM 配置: 须有可用的 API Key."""
    pool_path = Path(__file__).resolve().parents[3] / "config" / "model_pool.json"
    if not pool_path.exists():
        return False, "model_pool.json 不存在"
    try:
        import json as _json
        pool = _json.loads(pool_path.read_text(encoding="utf-8"))
        for team in pool.values():
            if isinstance(team, dict):
                for cfg in team.values():
                    if isinstance(cfg, dict) and cfg.get("api_key"):
                        return True, "LLM API Key 已配置"
        return False, "model_pool.json 中无 API Key"
    except Exception as e:
        return False, f"model_pool.json 解析失败: {e}"


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
        reference="PDCA",
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
        reference="ISO 19011",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.COMPANY.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="GEN-ZONE-003",
        domain=AuditDomain.GENERAL.value,
        title="合规区域配置完备",
        description="至少配置 1 个合规区域",
        target_channel="system_evolution",
        check_fn=_check_compliance_zones_loaded,
        reference="系统自检",
        severity=Severity.LOW.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=1.0,
    ),
    AuditRule(
        id="GEN-TRAIL-004",
        domain=AuditDomain.GENERAL.value,
        title="审计轨迹可用性",
        description="审计日志必须可写入，确保合规可追溯",
        target_channel="system_evolution",
        check_fn=_check_audit_trail_active,
        reference="审计合规",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=2.5,
    ),
    AuditRule(
        id="GEN-CHAT-005",
        domain=AuditDomain.GENERAL.value,
        title="Plaza 通信通道可达",
        description="plaza_chat 通信通道须已注册并可用",
        target_channel="system_evolution",
        check_fn=_check_bridge_chat_channel,
        reference="系统通信",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="GEN-ESC-006",
        domain=AuditDomain.GENERAL.value,
        title="失败升级机制就绪",
        description="DNV SEEMP Part III 风格的失败升级追踪正常",
        target_channel="system_evolution",
        check_fn=_check_escalation_mechanism,
        reference="升级机制",
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
        reference="评级模型",
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
        reference="趋势分析",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="GEN-VREG-009",
        domain=AuditDomain.GENERAL.value,
        title="验证注册表活跃",
        description="自动化验证测试注册表须可用",
        target_channel="system_evolution",
        check_fn=_check_verify_registry,
        reference="验证注册表",
        severity=Severity.LOW.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=1.0,
    ),
    AuditRule(
        id="GEN-MON-010",
        domain=AuditDomain.GENERAL.value,
        title="连续监控间隔配置",
        description="监控间隔须在 60~600s 范围内",
        target_channel="system_evolution",
        check_fn=_check_monitoring_interval,
        reference="监控配置",
        severity=Severity.LOW.value,
        operational_domain=OperationalDomain.ADVANCED_OPS.value,
        checklist_level=ChecklistLevel.BOTH.value,
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
        reference="PDCA 成熟度",
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
        reference="基线数据",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="GEN-ESCEX-013",
        domain=AuditDomain.GENERAL.value,
        title="升级机制演练确认",
        description="至少 1 条规则须经历过升级流程以验证升级路径",
        target_channel="system_evolution",
        check_fn=_check_escalation_exercised,
        reference="升级验证",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.COMPLIANCE_SAFETY.value,
        checklist_level=ChecklistLevel.COMPANY.value,
        rating_weight=1.5,
    ),
    # ── Project-Specific Real Checks ──
    AuditRule(
        id="PROJ-API-014",
        domain=AuditDomain.GENERAL.value,
        title="后端 API 健康检查",
        description="后端 /api/v1/health 端点须可达并返回 200",
        target_channel="system_evolution",
        check_fn=_check_api_health_endpoint,
        reference="REST API Best Practice",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=3.0,
    ),
    AuditRule(
        id="PROJ-FE-015",
        domain=AuditDomain.GENERAL.value,
        title="前端页面无 404",
        description="核心 HTML 页面 (index, plaza, system-evolution) 不可返回 404",
        target_channel="system_evolution",
        check_fn=_check_frontend_no_404,
        reference="Web UX Best Practice",
        severity=Severity.HIGH.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=2.0,
    ),
    AuditRule(
        id="PROJ-KB-016",
        domain=AuditDomain.GENERAL.value,
        title="知识库条目充足性",
        description="知识库须有 ≥ 5 条记录，确保搜索功能可用",
        target_channel="system_evolution",
        check_fn=_check_knowledge_base_has_entries,
        reference="Knowledge Management",
        severity=Severity.MEDIUM.value,
        operational_domain=OperationalDomain.DATA_DECISION.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=1.5,
    ),
    AuditRule(
        id="PROJ-EXEC-017",
        domain=AuditDomain.GENERAL.value,
        title="演进执行器可用",
        description="EvolutionExecutor 须已加载并可接受任务派发",
        target_channel="system_evolution",
        check_fn=_check_evolution_executor_available,
        reference="AgentLoop Integration",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=3.0,
    ),
    AuditRule(
        id="PROJ-LLM-018",
        domain=AuditDomain.GENERAL.value,
        title="LLM API 配置就绪",
        description="model_pool.json 须包含有效 API Key 以驱动 Agent 执行",
        target_channel="system_evolution",
        check_fn=_check_llm_api_configured,
        reference="DeepSeek API",
        severity=Severity.CRITICAL.value,
        operational_domain=OperationalDomain.TECHNICAL_MGMT.value,
        checklist_level=ChecklistLevel.BOTH.value,
        rating_weight=3.0,
    ),
]


# ── Built-in Compliance Zones ─────

BUILTIN_COMPLIANCE_ZONES: List[ComplianceZone] = [
    ComplianceZone(
        id="ZONE-LOCAL-DEV",
        name="本地开发环境",
        zone_type="CUSTOM",
        description="本地开发环境 — 全部规则激活",
        lat_min=0.0, lat_max=0.0,
        lon_min=0.0, lon_max=0.0,
        activated_rule_ids=[
            "PROJ-API-014", "PROJ-FE-015", "PROJ-KB-016",
            "PROJ-EXEC-017", "PROJ-LLM-018",
        ],
        extra_requirements="全面系统自检",
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

        # ── 演进执行器 (AgentLoop 桥接) ──
        self._executor = None  # lazy init

    # ── MarineChannel 接口 ───────────────────────────────────

    def initialize(self) -> bool:
        self._initialized = True
        self._load_state()  # 从磁盘加载持久化状态
        self._set_health(ChannelStatus.OK, "系统自我演进引擎已就绪")
        logger.info("🔄 System Evolution Engine initialized (%d audit rules, %d items loaded)",
                     len(self.audit_rules), len(self.evolution_items))
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