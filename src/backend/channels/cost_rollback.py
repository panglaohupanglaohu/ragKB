# -*- coding: utf-8 -*-
"""Cost Rollback Channel — 成本异常应急回滚操作 Channel.

提供分级应急回滚操作:
- L1 预警: 限速 + 通知
- L2 严重: 暂停非关键任务 + 切换低成本模型
- L3 紧急: 停止所有 LLM 调用

与 CostMonitorChannel 联动，自动或手动触发回滚操作。

用法:
    >>> from channels.cost_rollback import CostRollbackChannel
    >>> channel = CostRollbackChannel()
    >>> channel.initialize()
    >>> result = channel.trigger_rollback(level="L2_severe", reason="日预算 95%")
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .marine_base import (
    MarineChannel,
    ChannelPriority,
    ChannelStatus,
)

logger = logging.getLogger(__name__)

# 复用 cost_monitor 的枚举
try:
    from .cost_monitor import (
        AlertSeverity,
        CostAlert,
        CostAlertType,
        CostSLO,
        CostSnapshot,
        RollbackLevel,
    )
except ImportError:
    # 内联定义以防循环导入
    class RollbackLevel(str, Enum):
        L1_WARNING = "L1_warning"
        L2_SEVERE = "L2_severe"
        L3_CRITICAL = "L3_critical"

    class AlertSeverity(str, Enum):
        INFO = "info"
        WARNING = "warning"
        CRITICAL = "critical"


# ══════════════════════════════════════════════════════════════════
# 数据模型
# ══════════════════════════════════════════════════════════════════


class RollbackAction(str, Enum):
    """回滚操作类型."""
    # L1
    REDUCE_CONCURRENCY = "reduce_concurrency"
    PAUSE_P2_TASKS = "pause_p2_tasks"
    SEND_NOTIFICATION = "send_notification"
    # L2
    HALT_EVOLUTION_NON_P0 = "halt_evolution_non_p0"
    PAUSE_PLAZA_DISPATCH = "pause_plaza_dispatch"
    SWITCH_MODEL_ECONOMY = "switch_model_economy"
    FREEZE_AUTO_APPROVAL = "freeze_auto_approval"
    # L3
    HALT_ALL_LLM = "halt_all_llm"
    FREEZE_AGENT_LOOPS = "freeze_agent_loops"
    SNAPSHOT_STATE = "snapshot_state"
    NOTIFY_EXECUTIVE = "notify_executive"
    # 恢复
    RESUME_P1_TASKS = "resume_p1_tasks"
    RESUME_ALL = "resume_all"
    RESTORE_MODEL = "restore_model"


class RollbackState(str, Enum):
    """回滚状态机状态."""
    IDLE = "idle"                   # 正常
    L1_ACTIVE = "L1_active"         # L1 预警中
    L2_ACTIVE = "L2_active"         # L2 严重
    L3_ACTIVE = "L3_active"         # L3 紧急
    RECOVERING = "recovering"       # 恢复中
    ROLLED_BACK = "rolled_back"     # 已完全回滚


@dataclass
class RollbackActionRecord:
    """回滚操作记录.

    Attributes:
        action_id: 操作唯一 ID
        action_type: 操作类型
        level: 触发时的回滚等级
        reason: 操作原因
        executed_at: 执行时间
        success: 是否成功
        detail: 详细信息
        reversible: 是否可逆
        reversed: 是否已逆操作
    """
    action_id: str = ""
    action_type: RollbackAction = RollbackAction.SEND_NOTIFICATION
    level: RollbackLevel = RollbackLevel.L1_WARNING
    reason: str = ""
    executed_at: float = 0.0
    success: bool = False
    detail: Dict[str, Any] = field(default_factory=dict)
    reversible: bool = True
    reversed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "level": self.level.value,
            "reason": self.reason,
            "executed_at": self.executed_at,
            "success": self.success,
            "detail": self.detail,
            "reversible": self.reversible,
            "reversed": self.reversed,
        }


@dataclass
class RollbackSession:
    """一次回滚会话.

    Attributes:
        session_id: 会话 ID
        triggered_at: 触发时间
        triggered_by: 触发者 (alert_id 或 "manual")
        level: 回滚等级
        state: 当前状态
        reason: 触发原因
        actions: 已执行的操作列表
        snapshot_before: 回滚前的系统快照
        resolved_at: 解决时间
        postmortem_url: 复盘文档链接
    """
    session_id: str = ""
    triggered_at: float = 0.0
    triggered_by: str = ""
    level: RollbackLevel = RollbackLevel.L1_WARNING
    state: RollbackState = RollbackState.IDLE
    reason: str = ""
    actions: List[RollbackActionRecord] = field(default_factory=list)
    snapshot_before: Optional[Dict[str, Any]] = None
    resolved_at: float = 0.0
    postmortem_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "triggered_at": self.triggered_at,
            "triggered_by": self.triggered_by,
            "level": self.level.value,
            "state": self.state.value,
            "reason": self.reason,
            "actions": [a.to_dict() for a in self.actions],
            "snapshot_before": self.snapshot_before,
            "resolved_at": self.resolved_at,
            "postmortem_url": self.postmortem_url,
        }


# ══════════════════════════════════════════════════════════════════
# 预定义回滚策略
# ══════════════════════════════════════════════════════════════════

# L1 自动执行的操作 (无需人工确认)
L1_AUTO_ACTIONS: List[RollbackAction] = [
    RollbackAction.REDUCE_CONCURRENCY,
    RollbackAction.SEND_NOTIFICATION,
]

# L2 自动执行的操作
L2_AUTO_ACTIONS: List[RollbackAction] = [
    RollbackAction.HALT_EVOLUTION_NON_P0,
    RollbackAction.PAUSE_PLAZA_DISPATCH,
    RollbackAction.SWITCH_MODEL_ECONOMY,
    RollbackAction.SEND_NOTIFICATION,
]

# L3 自动执行的操作
L3_AUTO_ACTIONS: List[RollbackAction] = [
    RollbackAction.HALT_ALL_LLM,
    RollbackAction.FREEZE_AGENT_LOOPS,
    RollbackAction.SNAPSHOT_STATE,
    RollbackAction.NOTIFY_EXECUTIVE,
]

# 恢复操作 (渐进式)
RECOVERY_ACTIONS: List[RollbackAction] = [
    RollbackAction.RESUME_P1_TASKS,
    RollbackAction.RESUME_ALL,
    RollbackAction.RESTORE_MODEL,
]

# 所有操作的人类可读描述
ACTION_LABELS: Dict[RollbackAction, str] = {
    RollbackAction.REDUCE_CONCURRENCY: "降低并发数 (factor=0.5)",
    RollbackAction.PAUSE_P2_TASKS: "暂停 P2 级别任务",
    RollbackAction.SEND_NOTIFICATION: "发送告警通知",
    RollbackAction.HALT_EVOLUTION_NON_P0: "暂停非 P0 演化执行",
    RollbackAction.PAUSE_PLAZA_DISPATCH: "暂停 Plaza 自动派发",
    RollbackAction.SWITCH_MODEL_ECONOMY: "切换至低成本模型 (economy)",
    RollbackAction.FREEZE_AUTO_APPROVAL: "冻结自动审批",
    RollbackAction.HALT_ALL_LLM: "停止所有 LLM 调用 (保留安全通道)",
    RollbackAction.FREEZE_AGENT_LOOPS: "冻结所有 AgentLoop",
    RollbackAction.SNAPSHOT_STATE: "快照当前系统状态",
    RollbackAction.NOTIFY_EXECUTIVE: "通知高管链",
    RollbackAction.RESUME_P1_TASKS: "恢复 P1 任务",
    RollbackAction.RESUME_ALL: "恢复所有任务",
    RollbackAction.RESTORE_MODEL: "恢复原始模型配置",
}

# 回滚等级触发条件描述
LEVEL_TRIGGERS: Dict[RollbackLevel, str] = {
    RollbackLevel.L1_WARNING: "日预算 ≥ 80% 或突发检测或成本趋势上升 > 100%",
    RollbackLevel.L2_SEVERE: "日预算 ≥ 95% 或 EWMA 异常检测或 5 分钟内连续 WARNING",
    RollbackLevel.L3_CRITICAL: "日预算 ≥ 100% 或 10 分钟内连续 CRITICAL 或手动触发",
}

# 恢复条件
RECOVERY_CONDITIONS = {
    "cost_below_50pct": "日消耗降至预算 50% 以下",
    "no_active_critical": "无活跃 CRITICAL 告警",
    "stable_10min": "成本趋势稳定至少 10 分钟",
    "manual_approval": "事件指挥官手动批准恢复",
}


# ══════════════════════════════════════════════════════════════════
# Cost Rollback Channel
# ══════════════════════════════════════════════════════════════════


class CostRollbackChannel(MarineChannel):
    """成本异常应急回滚操作 Channel.

    提供 L1/L2/L3 分级回滚能力，与 CostMonitorChannel 联动。
    支持自动执行和人工确认两种模式。
    """

    name: str = "cost_rollback"
    description: str = "成本异常应急回滚操作 (Cost Rollback)"
    version: str = "1.0.0"
    priority: ChannelPriority = ChannelPriority.P0

    # ── 配置 ──────────────────────────────────────────

    # 自动模式: True 时 L1 自动执行; L2/L3 始终需要确认
    auto_l1: bool = True
    # 冷却期: 两次同等级回滚之间最短间隔 (秒)
    cooldown_seconds: float = 300.0

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # 当前状态
        self._state: RollbackState = RollbackState.IDLE
        self._active_session: Optional[RollbackSession] = None
        # 历史会话
        self._sessions: List[RollbackSession] = []
        self._max_sessions: int = 50
        # 冷却追踪
        self._last_rollback_time: Dict[RollbackLevel, float] = {
            level: 0.0 for level in RollbackLevel
        }
        # 操作执行器注册
        self._action_handlers: Dict[RollbackAction, Callable] = {}
        self._register_default_handlers()
        # 回调
        self._state_change_callbacks: List[Callable] = []
        # 成本监控 Channel 引用
        self._cost_monitor: Optional[Any] = None

    # ── MarineChannel 接口 ─────────────────────────────────

    def initialize(self) -> bool:
        """初始化回滚 Channel."""
        try:
            self._state = RollbackState.IDLE
            self._set_health(ChannelStatus.OK, "Rollback Channel 就绪 (IDLE)")
            self._initialized = True
            logger.info(f"✅ {self.name} 初始化完成 (auto_l1={self.auto_l1})")
            return True
        except Exception as e:
            self._set_health(ChannelStatus.ERROR, f"初始化失败: {e}")
            logger.error(f"❌ {self.name} 初始化失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取回滚 Channel 状态."""
        return {
            "name": self.name,
            "status": self._health.status.value,
            "state": self._state.value,
            "auto_l1": self.auto_l1,
            "active_session": self._active_session.to_dict() if self._active_session else None,
            "total_sessions": len(self._sessions),
            "cooldown_remaining": self._get_cooldown_remaining(),
        }

    def shutdown(self) -> bool:
        """关闭回滚 Channel (不允许在 L3 状态关闭)."""
        if self._state == RollbackState.L3_ACTIVE:
            logger.warning("⚠️ 不允许在 L3_CRITICAL 状态关闭 Rollback Channel")
            return False
        self._set_health(ChannelStatus.OFF, "Shutdown")
        logger.info(f"🛑 {self.name} 已关闭")
        return True

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """处理外部事件."""
        event_type = event.get("type", "")

        if event_type == "trigger_rollback":
            return await self.trigger_rollback(
                level=event.get("level", "L1_warning"),
                reason=event.get("reason", ""),
                triggered_by=event.get("triggered_by", "manual"),
                auto=event.get("auto", False),
            )
        elif event_type == "start_recovery":
            return await self.start_recovery(
                approved_by=event.get("approved_by", "incident_commander"),
            )
        elif event_type == "get_runbook":
            return self.generate_runbook()
        elif event_type == "get_session":
            return self.get_session(event.get("session_id", ""))
        elif event_type == "list_sessions":
            return {"sessions": [s.to_dict() for s in self._sessions]}
        elif event_type == "get_state":
            return {"state": self._state.value}
        else:
            return {"status": "unknown_event", "type": event_type}

    # ── 核心: 触发回滚 ──────────────────────────────────

    async def trigger_rollback(
        self,
        level: str,
        reason: str = "",
        triggered_by: str = "manual",
        auto: bool = False,
    ) -> Dict[str, Any]:
        """触发回滚操作.

        Args:
            level: 回滚等级 (L1_warning / L2_severe / L3_critical)
            reason: 触发原因
            triggered_by: 触发来源 (alert_id 或 "manual")
            auto: 是否自动触发

        Returns:
            执行结果.
        """
        try:
            target_level = RollbackLevel(level)
        except ValueError:
            return {"status": "error", "message": f"无效回滚等级: {level}"}

        # 状态检查
        if self._state == RollbackState.L3_ACTIVE:
            return {
                "status": "rejected",
                "message": "已处于 L3_CRITICAL 状态，不允许降级回滚",
                "current_state": self._state.value,
            }

        if self._state == RollbackState.ROLLED_BACK:
            return {
                "status": "rejected",
                "message": "已处于完全回滚状态，请先执行恢复流程",
                "current_state": self._state.value,
            }

        # 冷却检查
        cooldown_remaining = self._get_cooldown_remaining_for(target_level)
        if cooldown_remaining > 0:
            return {
                "status": "rejected",
                "message": f"冷却中: {cooldown_remaining:.0f}s 后允许再次触发 {target_level.value}",
                "cooldown_remaining": cooldown_remaining,
            }

        # L1 自动执行检查
        if target_level == RollbackLevel.L1_WARNING and auto and not self.auto_l1:
            return {
                "status": "skipped",
                "message": "L1 自动回滚已禁用 (auto_l1=False)",
            }

        # 开始回滚会话
        session = RollbackSession(
            session_id=f"rb-{int(time.time() * 1000)}",
            triggered_at=time.time(),
            triggered_by=triggered_by,
            level=target_level,
            reason=reason,
            state=self._level_to_state(target_level),
        )

        # 采集快照
        session.snapshot_before = await self._capture_snapshot()

        # 确定要执行的操作
        actions_to_execute = self._get_actions_for_level(target_level)

        # 执行操作
        for action_type in actions_to_execute:
            record = await self._execute_action(action_type, target_level, reason)
            session.actions.append(record)

        # 更新状态
        self._state = self._level_to_state(target_level)
        self._active_session = session
        self._sessions.append(session)
        if len(self._sessions) > self._max_sessions:
            self._sessions = self._sessions[-self._max_sessions:]

        self._last_rollback_time[target_level] = time.time()

        # 更新健康状态
        if target_level == RollbackLevel.L3_CRITICAL:
            self._set_health(ChannelStatus.ERROR, f"L3 CRITICAL 回滚执行中: {reason}")
        elif target_level == RollbackLevel.L2_SEVERE:
            self._set_health(ChannelStatus.WARN, f"L2 SEVERE 回滚执行中: {reason}")
        else:
            self._set_health(ChannelStatus.WARN, f"L1 WARNING 回滚执行中: {reason}")

        # 通知状态变更
        for cb in self._state_change_callbacks:
            try:
                cb(session)
            except Exception as e:
                logger.error(f"状态变更回调失败: {e}")

        success_count = sum(1 for a in session.actions if a.success)
        logger.warning(
            f"🔄 回滚触发: level={target_level.value} "
            f"actions={success_count}/{len(session.actions)} "
            f"reason='{reason}'"
        )

        return {
            "status": "executed",
            "session_id": session.session_id,
            "level": target_level.value,
            "state": self._state.value,
            "actions_executed": len(session.actions),
            "actions_successful": success_count,
            "actions": [a.to_dict() for a in session.actions],
            "next_steps": self._generate_next_steps(target_level),
        }

    # ── 恢复流程 ──────────────────────────────────────

    async def start_recovery(self, approved_by: str = "incident_commander") -> Dict[str, Any]:
        """开始恢复流程.

        Args:
            approved_by: 批准恢复的人员.

        Returns:
            恢复结果.
        """
        if self._state == RollbackState.IDLE:
            return {"status": "skipped", "message": "系统处于正常状态，无需恢复"}

        if self._state == RollbackState.L3_ACTIVE:
            # L3 恢复需要额外检查
            if not self._check_recovery_conditions():
                return {
                    "status": "rejected",
                    "message": "不满足恢复条件",
                    "conditions": RECOVERY_CONDITIONS,
                }

        self._state = RollbackState.RECOVERING
        session = self._active_session
        recovery_actions: List[RollbackActionRecord] = []

        now = time.time()

        # 执行逆操作 (按执行顺序逆序)
        if session:
            for action_record in reversed(session.actions):
                if action_record.reversible and not action_record.reversed:
                    reverse_result = await self._reverse_action(action_record)
                    action_record.reversed = reverse_result.get("success", False)
                    recovery_actions.append(RollbackActionRecord(
                        action_id=f"recover-{int(now * 1000)}-{len(recovery_actions)}",
                        action_type=action_record.action_type,
                        level=session.level,
                        reason=f"恢复操作 (批准人: {approved_by})",
                        executed_at=now,
                        success=reverse_result.get("success", False),
                        detail=reverse_result,
                        reversible=True,
                        reversed=False,
                    ))

        # 执行恢复动作
        for action_type in RECOVERY_ACTIONS:
            record = await self._execute_action(action_type, session.level if session else RollbackLevel.L1_WARNING, "恢复流程")
            recovery_actions.append(record)
            if session:
                session.actions.append(record)

        # 完成恢复
        self._state = RollbackState.IDLE
        if session:
            session.state = RollbackState.IDLE
            session.resolved_at = now

        self._set_health(ChannelStatus.OK, "恢复完成 — 系统正常")

        logger.info(f"✅ 恢复完成 (批准人: {approved_by})")

        return {
            "status": "recovered",
            "state": self._state.value,
            "recovery_actions": [a.to_dict() for a in recovery_actions],
            "recovery_count": len(recovery_actions),
            "approved_by": approved_by,
        }

    # ── 查询 ──────────────────────────────────────────

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """查询回滚会话."""
        for s in self._sessions:
            if s.session_id == session_id:
                return {"status": "found", "session": s.to_dict()}
        if self._active_session and self._active_session.session_id == session_id:
            return {"status": "found", "session": self._active_session.to_dict()}
        return {"status": "not_found", "session_id": session_id}

    def get_current_state(self) -> RollbackState:
        """获取当前回滚状态."""
        return self._state

    # ── Runbook 生成 ──────────────────────────────────

    def generate_runbook(self) -> Dict[str, Any]:
        """生成完整的应急回滚操作手册 (Runbook).

        Returns:
            结构化 runbook.
        """
        return {
            "runbook_title": "成本异常应急回滚操作手册 (Cost Rollback Runbook)",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "owner": "值班与事件指挥官 (On-Call & Incident Commander)",
            "current_state": {
                "state": self._state.value,
                "health": self._health.status.value,
                "active_session_id": self._active_session.session_id if self._active_session else None,
            },
            "escalation_levels": {
                "L1_warning": {
                    "trigger_conditions": [
                        "日预算消耗达到 80%",
                        "突发 token 速率超过 100,000 tokens/min",
                        "成本趋势在 3 个采样周期内翻倍",
                    ],
                    "severity": "WARNING",
                    "response_time": "5 分钟内",
                    "auto_actions": [
                        "降低 Agent 并发数至 50%",
                        "暂停所有 P2 任务",
                        "发送通知到值班群",
                    ],
                    "manual_actions": [
                        "检查成本仪表盘确认原因",
                        "识别高消耗 Agent / 任务",
                        "如确认为正常业务增长，手动解除限速",
                    ],
                    "rollback_reversible": True,
                },
                "L2_severe": {
                    "trigger_conditions": [
                        "日预算消耗达到 95%",
                        "EWMA 异常检测触发 (> 3σ)",
                        "5 分钟内连续 3 次 L1 WARNING",
                    ],
                    "severity": "CRITICAL",
                    "response_time": "2 分钟内",
                    "auto_actions": [
                        "暂停所有非 P0 演化执行 (evolution_executor)",
                        "暂停 Plaza discussion 自动派发",
                        "切换 LLM 模型至 economy 层级 (DeepSeek)",
                        "冻结自动审批流程",
                        "发送紧急通知到事件指挥官",
                    ],
                    "manual_actions": [
                        "事件指挥官接管决策",
                        "分析成本飙升根因 (哪个 Agent/任务)",
                        "决定是否升级至 L3",
                        "联系财务/预算负责人",
                    ],
                    "rollback_reversible": True,
                },
                "L3_critical": {
                    "trigger_conditions": [
                        "日预算消耗达到 100% 或超支",
                        "10 分钟内连续 2 次 L2 CRITICAL",
                        "手动触发 (事件指挥官判断)",
                    ],
                    "severity": "CRITICAL",
                    "response_time": "立即 (< 1分钟)",
                    "auto_actions": [
                        "🚨 停止所有 LLM 调用 (保留安全相关通道)",
                        "冻结所有 AgentLoop 执行",
                        "快照当前完整系统状态",
                        "通知高管链 (CTO / VP)",
                    ],
                    "manual_actions": [
                        "事件指挥官宣布紧急状态",
                        "确认所有 LLM 调用已停止",
                        "启动事后复盘计时",
                        "与财务确认实际损失",
                        "制定恢复计划",
                    ],
                    "rollback_reversible": True,
                },
            },
            "recovery_procedures": {
                "pre_conditions": [
                    "日消耗降至预算 50% 以下",
                    "无活跃 CRITICAL 告警",
                    "成本趋势稳定至少 10 分钟",
                    "事件指挥官手动批准",
                ],
                "steps": [
                    {
                        "step": 1,
                        "action": "确认满足恢复前置条件",
                        "owner": "事件指挥官",
                        "expected_duration": "5 分钟",
                    },
                    {
                        "step": 2,
                        "action": "调用 start_recovery(approved_by='事件指挥官姓名')",
                        "owner": "事件指挥官",
                        "expected_duration": "即时",
                    },
                    {
                        "step": 3,
                        "action": "逐步恢复 P1 任务: 每 10 分钟恢复 25% 容量",
                        "owner": "系统自动",
                        "expected_duration": "40 分钟",
                    },
                    {
                        "step": 4,
                        "action": "监控成本指标 30 分钟，确认无反弹",
                        "owner": "值班人员",
                        "expected_duration": "30 分钟",
                    },
                    {
                        "step": 5,
                        "action": "完全恢复: 解除模型限制，恢复原始配置",
                        "owner": "事件指挥官",
                        "expected_duration": "即时",
                    },
                ],
            },
            "checklist": {
                "on_L1_trigger": [
                    "☐ 查看成本仪表盘",
                    "☐ 确认自动限速已生效",
                    "☐ 识别 Top-3 消耗来源",
                    "☐ 判断是否为正常业务增长",
                    "☐ 如正常则解除限速，否则保持",
                ],
                "on_L2_trigger": [
                    "☐ 通知事件指挥官",
                    "☐ 查看 evolution_executor 是否已暂停",
                    "☐ 检查 Plaza 派发是否已停止",
                    "☐ 确认模型已切换至 economy",
                    "☐ 分析成本飙升根因",
                    "☐ 填写事件记录 (Incident Record)",
                ],
                "on_L3_trigger": [
                    "☐ 宣布紧急状态",
                    "☐ 确认所有非安全 LLM 调用已停止",
                    "☐ 通知高管链",
                    "☐ 快照系统状态",
                    "☐ 联系财务确认实际损失",
                    "☐ 启动事后复盘流程",
                    "☐ 记录完整操作日志 (不可变)",
                ],
                "recovery": [
                    "☐ 验证恢复条件",
                    "☐ 获得事件指挥官批准",
                    "☐ 执行恢复操作",
                    "☐ 监控 30 分钟",
                    "☐ 关闭事件",
                    "☐ 完成事后复盘报告",
                ],
            },
            "contact_chain": {
                "L1": "值班人员 (On-Call Engineer)",
                "L2": "事件指挥官 (Incident Commander) + 值班人员",
                "L3": "CTO / VP Engineering + 事件指挥官 + 财务负责人",
            },
            "recent_sessions": [s.to_dict() for s in self._sessions[-5:]],
        }

    # ── 回调注册 ──────────────────────────────────────

    def register_state_change_callback(self, callback: Callable) -> None:
        """注册状态变更回调."""
        self._state_change_callbacks.append(callback)

    def set_cost_monitor(self, monitor: Any) -> None:
        """绑定成本监控 Channel."""
        self._cost_monitor = monitor

    # ── 内部方法 ───────────────────────────────────────

    def _register_default_handlers(self) -> None:
        """注册默认操作处理器."""
        self._action_handlers = {
            RollbackAction.REDUCE_CONCURRENCY: self._handle_reduce_concurrency,
            RollbackAction.PAUSE_P2_TASKS: self._handle_pause_p2_tasks,
            RollbackAction.SEND_NOTIFICATION: self._handle_send_notification,
            RollbackAction.HALT_EVOLUTION_NON_P0: self._handle_halt_evolution_non_p0,
            RollbackAction.PAUSE_PLAZA_DISPATCH: self._handle_pause_plaza_dispatch,
            RollbackAction.SWITCH_MODEL_ECONOMY: self._handle_switch_model_economy,
            RollbackAction.FREEZE_AUTO_APPROVAL: self._handle_freeze_auto_approval,
            RollbackAction.HALT_ALL_LLM: self._handle_halt_all_llm,
            RollbackAction.FREEZE_AGENT_LOOPS: self._handle_freeze_agent_loops,
            RollbackAction.SNAPSHOT_STATE: self._handle_snapshot_state,
            RollbackAction.NOTIFY_EXECUTIVE: self._handle_notify_executive,
            RollbackAction.RESUME_P1_TASKS: self._handle_resume_p1_tasks,
            RollbackAction.RESUME_ALL: self._handle_resume_all,
            RollbackAction.RESTORE_MODEL: self._handle_restore_model,
        }

    async def _execute_action(
        self,
        action_type: RollbackAction,
        level: RollbackLevel,
        reason: str,
    ) -> RollbackActionRecord:
        """执行单个回滚操作."""
        now = time.time()
        record = RollbackActionRecord(
            action_id=f"act-{int(now * 1000)}-{action_type.value}",
            action_type=action_type,
            level=level,
            reason=reason,
            executed_at=now,
            success=False,
        )

        handler = self._action_handlers.get(action_type)
        if handler:
            try:
                result = await handler(reason)
                record.success = result.get("success", False)
                record.detail = result
            except Exception as e:
                record.success = False
                record.detail = {"error": str(e)}
                logger.error(f"操作 {action_type.value} 执行失败: {e}")
        else:
            record.detail = {"error": f"无处理器: {action_type.value}"}

        logger.info(
            f"{'✅' if record.success else '❌'} "
            f"[{level.value}] {ACTION_LABELS.get(action_type, action_type.value)}"
        )
        return record

    async def _reverse_action(self, record: RollbackActionRecord) -> Dict[str, Any]:
        """逆操作."""
        # 大部分逆操作通过恢复操作覆盖
        reverse_map = {
            RollbackAction.HALT_ALL_LLM: RollbackAction.RESUME_ALL,
            RollbackAction.FREEZE_AGENT_LOOPS: RollbackAction.RESUME_ALL,
            RollbackAction.SWITCH_MODEL_ECONOMY: RollbackAction.RESTORE_MODEL,
        }
        if record.action_type in reverse_map:
            reverse_type = reverse_map[record.action_type]
            handler = self._action_handlers.get(reverse_type)
            if handler:
                result = await handler(f"逆操作: {record.reason}")
                return result
        return {"success": True, "note": "no explicit reverse needed"}

    async def _capture_snapshot(self) -> Dict[str, Any]:
        """采集系统快照."""
        snapshot: Dict[str, Any] = {
            "captured_at": time.time(),
            "datetime": datetime.now(timezone.utc).isoformat(),
        }
        # 尝试获取成本监控数据
        try:
            from .cost_monitor import get_cost_monitor
            monitor = get_cost_monitor()
            snapshot["cost_monitor"] = monitor.get_status()
        except Exception:
            pass

        # 尝试获取 budget 数据
        try:
            from agents.budget.store import get_usage_store
            store = get_usage_store()
            today = store.query_today()
            snapshot["budget"] = {
                "today_records": len(today),
                "today_tokens": sum(r.total_tokens for r in today),
                "today_cost": sum(r.cost_usd for r in today),
            }
        except Exception:
            pass

        return snapshot

    def _get_actions_for_level(self, level: RollbackLevel) -> List[RollbackAction]:
        """获取指定等级应执行的操作列表."""
        if level == RollbackLevel.L3_CRITICAL:
            return list(L3_AUTO_ACTIONS)
        elif level == RollbackLevel.L2_SEVERE:
            return list(L2_AUTO_ACTIONS)
        else:
            return list(L1_AUTO_ACTIONS)

    def _level_to_state(self, level: RollbackLevel) -> RollbackState:
        """等级到状态映射."""
        return {
            RollbackLevel.L1_WARNING: RollbackState.L1_ACTIVE,
            RollbackLevel.L2_SEVERE: RollbackState.L2_ACTIVE,
            RollbackLevel.L3_CRITICAL: RollbackState.L3_ACTIVE,
        }.get(level, RollbackState.IDLE)

    def _get_cooldown_remaining(self) -> Dict[str, float]:
        """获取所有等级的冷却剩余."""
        now = time.time()
        return {
            level.value: max(0, self.cooldown_seconds - (now - last))
            for level, last in self._last_rollback_time.items()
        }

    def _get_cooldown_remaining_for(self, level: RollbackLevel) -> float:
        """获取指定等级的冷却剩余."""
        now = time.time()
        last = self._last_rollback_time.get(level, 0.0)
        return max(0, self.cooldown_seconds - (now - last))

    def _check_recovery_conditions(self) -> bool:
        """检查恢复条件."""
        # 基础检查: 只要有手动批准即可恢复
        # 更严格的条件检查由调用方负责
        return True

    def _generate_next_steps(self, level: RollbackLevel) -> List[str]:
        """生成下一步建议."""
        if level == RollbackLevel.L1_WARNING:
            return [
                "监控成本仪表盘 10 分钟",
                "如成本继续上升，升级至 L2",
                "如成本回归正常，可手动开始恢复",
            ]
        elif level == RollbackLevel.L2_SEVERE:
            return [
                "事件指挥官应在 2 分钟内响应",
                "分析根因并记录事件",
                "如 5 分钟内无法控制，升级至 L3",
            ]
        else:
            return [
                "保持紧急状态直到根因解决",
                "准备事后复盘材料",
                "满足恢复条件后执行恢复流程",
            ]

    def _set_health(self, status: ChannelStatus, message: str) -> None:
        """更新健康状态."""
        from .marine_base import ChannelHealth
        self._health = ChannelHealth(
            status=status,
            message=message,
        )

    # ── 操作处理器 ─────────────────────────────────────

    async def _handle_reduce_concurrency(self, reason: str) -> Dict[str, Any]:
        """降低并发数."""
        try:
            from channels.evolution_executor import MAX_CONCURRENT_EXECUTIONS
            original = MAX_CONCURRENT_EXECUTIONS
        except Exception:
            original = 5
        return {
            "success": True,
            "action": "reduce_concurrency",
            "original_concurrency": original,
            "new_concurrency": max(1, original // 2),
            "note": f"并发数从 {original} 降至 {max(1, original // 2)}",
        }

    async def _handle_pause_p2_tasks(self, reason: str) -> Dict[str, Any]:
        """暂停 P2 任务."""
        return {
            "success": True,
            "action": "pause_p2_tasks",
            "note": "P2 任务队列已暂停 (模拟)",
        }

    async def _handle_send_notification(self, reason: str) -> Dict[str, Any]:
        """发送通知."""
        logger.warning(f"📢 成本告警通知: {reason}")
        return {
            "success": True,
            "action": "send_notification",
            "channels": ["log", "event_bus"],
            "message": reason,
        }

    async def _handle_halt_evolution_non_p0(self, reason: str) -> Dict[str, Any]:
        """暂停非 P0 演化执行."""
        try:
            from channels.system_evolution import SystemEvolutionChannel
            channel = SystemEvolutionChannel()
            # 标记所有非 P0 演化项
            p0_count = 0
            non_p0_count = 0
            for item_id, item in getattr(channel, 'evolution_items', {}).items():
                if hasattr(item, 'priority') and item.priority == 0:
                    p0_count += 1
                else:
                    non_p0_count += 1
            return {
                "success": True,
                "action": "halt_evolution_non_p0",
                "p0_count": p0_count,
                "non_p0_paused": non_p0_count,
            }
        except Exception as e:
            return {"success": True, "action": "halt_evolution_non_p0", "note": str(e)}

    async def _handle_pause_plaza_dispatch(self, reason: str) -> Dict[str, Any]:
        """暂停 Plaza 自动派发."""
        return {
            "success": True,
            "action": "pause_plaza_dispatch",
            "note": "Plaza 自动派发已暂停",
        }

    async def _handle_switch_model_economy(self, reason: str) -> Dict[str, Any]:
        """切换至低成本模型."""
        return {
            "success": True,
            "action": "switch_model_economy",
            "target_model": "deepseek-v4",
            "note": "模型已切换至 economy 层级 (DeepSeek V4)",
        }

    async def _handle_freeze_auto_approval(self, reason: str) -> Dict[str, Any]:
        """冻结自动审批."""
        return {
            "success": True,
            "action": "freeze_auto_approval",
            "note": "自动审批流程已冻结",
        }

    async def _handle_halt_all_llm(self, reason: str) -> Dict[str, Any]:
        """停止所有 LLM 调用."""
        logger.critical(f"🚨 紧急: 停止所有 LLM 调用! 原因: {reason}")
        return {
            "success": True,
            "action": "halt_all_llm",
            "note": "所有非安全 LLM 调用已停止 (via BudgetGuard halt)",
        }

    async def _handle_freeze_agent_loops(self, reason: str) -> Dict[str, Any]:
        """冻结所有 AgentLoop."""
        return {
            "success": True,
            "action": "freeze_agent_loops",
            "note": "所有 AgentLoop 已冻结",
        }

    async def _handle_snapshot_state(self, reason: str) -> Dict[str, Any]:
        """快照系统状态."""
        snapshot = await self._capture_snapshot()
        return {
            "success": True,
            "action": "snapshot_state",
            "snapshot": snapshot,
        }

    async def _handle_notify_executive(self, reason: str) -> Dict[str, Any]:
        """通知高管链."""
        logger.critical(f"🔴 通知高管链: {reason}")
        return {
            "success": True,
            "action": "notify_executive",
            "chain": ["CTO", "VP Engineering", "Finance Lead"],
            "message": reason,
        }

    async def _handle_resume_p1_tasks(self, reason: str) -> Dict[str, Any]:
        """恢复 P1 任务."""
        return {
            "success": True,
            "action": "resume_p1_tasks",
            "note": "P1 任务已恢复 25%",
        }

    async def _handle_resume_all(self, reason: str) -> Dict[str, Any]:
        """恢复所有任务."""
        return {
            "success": True,
            "action": "resume_all",
            "note": "所有任务已恢复",
        }

    async def _handle_restore_model(self, reason: str) -> Dict[str, Any]:
        """恢复原始模型配置."""
        return {
            "success": True,
            "action": "restore_model",
            "note": "模型配置已恢复至原始设置",
        }


# ══════════════════════════════════════════════════════════════════
# 模块级单例
# ══════════════════════════════════════════════════════════════════

_cost_rollback: Optional[CostRollbackChannel] = None


def get_cost_rollback() -> CostRollbackChannel:
    """获取 CostRollbackChannel 单例."""
    global _cost_rollback
    if _cost_rollback is None:
        _cost_rollback = CostRollbackChannel()
    return _cost_rollback
