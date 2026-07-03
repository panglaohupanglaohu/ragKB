# -*- coding: utf-8 -*-
"""Cost Monitor Channel — 成本异常监控与 SLO 告警 Channel.

将 LLM Token 消耗与任务执行成本纳入 SLO 监控体系:
- 对接现有 budget 系统 (UsageStore / BudgetGuard)
- 基于 EWMA 动态阈值的成本异常检测
- 多级告警规则 (INFO / WARNING / CRITICAL)
- 成本趋势分析与预测

告警规则:
  WARNING  — 日预算消耗 ≥ 80%
  CRITICAL — 日预算消耗 ≥ 95%
  BURST    — 短时间 token 消耗速率超过阈值
  ANOMALY  — EWMA 检测到异常成本模式

用法:
    >>> from channels.cost_monitor import CostMonitorChannel
    >>> channel = CostMonitorChannel()
    >>> channel.initialize()
    >>> alerts = channel.check_cost_slo()
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .marine_base import (
    MarineChannel,
    ChannelPriority,
    ChannelStatus,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# 枚举与数据模型
# ══════════════════════════════════════════════════════════════════


class AlertSeverity(str, Enum):
    """告警严重级别."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CostAlertType(str, Enum):
    """成本告警类型."""
    BUDGET_WARNING = "budget_warning"       # 预算消耗达 80%
    BUDGET_CRITICAL = "budget_critical"     # 预算消耗达 95%
    BUDGET_EXCEEDED = "budget_exceeded"     # 预算超支
    BURST_DETECTED = "burst_detected"       # 突发高消耗
    ANOMALY_DETECTED = "anomaly_detected"   # EWMA 异常检测
    TREND_SPIKE = "trend_spike"             # 成本趋势尖峰


class RollbackLevel(str, Enum):
    """回滚等级."""
    L1_WARNING = "L1_warning"       # 预警: 通知 + 限速
    L2_SEVERE = "L2_severe"         # 严重: 暂停非关键任务
    L3_CRITICAL = "L3_critical"     # 紧急: 停止所有 LLM 调用


@dataclass
class CostSLO:
    """成本 SLO 定义.

    Attributes:
        daily_budget_usd: 每日预算上限 (美元)
        per_agent_daily_usd: 每 Agent 每日预算上限
        per_task_max_usd: 单任务最大成本
        burst_threshold_tokens_per_min: 突发 token 速率阈值 (tokens/min)
        burst_window_seconds: 突发检测窗口 (秒)
        ewma_alpha: EWMA 平滑因子
        anomaly_sigma: 异常检测标准差倍数
        min_samples: EWMA 最小样本数
    """
    daily_budget_usd: float = 10.0
    per_agent_daily_usd: float = 3.0
    per_task_max_usd: float = 1.0
    burst_threshold_tokens_per_min: float = 100_000.0
    burst_window_seconds: float = 60.0
    ewma_alpha: float = 0.3
    anomaly_sigma: float = 3.0
    min_samples: int = 10

    # Derived thresholds
    warn_ratio: float = 0.80
    critical_ratio: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        return {
            "daily_budget_usd": self.daily_budget_usd,
            "per_agent_daily_usd": self.per_agent_daily_usd,
            "per_task_max_usd": self.per_task_max_usd,
            "burst_threshold_tokens_per_min": self.burst_threshold_tokens_per_min,
            "burst_window_seconds": self.burst_window_seconds,
            "ewma_alpha": self.ewma_alpha,
            "anomaly_sigma": self.anomaly_sigma,
            "min_samples": self.min_samples,
            "warn_ratio": self.warn_ratio,
            "critical_ratio": self.critical_ratio,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CostSLO:
        return cls(
            daily_budget_usd=data.get("daily_budget_usd", 10.0),
            per_agent_daily_usd=data.get("per_agent_daily_usd", 3.0),
            per_task_max_usd=data.get("per_task_max_usd", 1.0),
            burst_threshold_tokens_per_min=data.get("burst_threshold_tokens_per_min", 100_000.0),
            burst_window_seconds=data.get("burst_window_seconds", 60.0),
            ewma_alpha=data.get("ewma_alpha", 0.3),
            anomaly_sigma=data.get("anomaly_sigma", 3.0),
            min_samples=data.get("min_samples", 10),
            warn_ratio=data.get("warn_ratio", 0.80),
            critical_ratio=data.get("critical_ratio", 0.95),
        )


@dataclass
class CostSnapshot:
    """成本快照 — 某一时刻的成本状态.

    Attributes:
        timestamp: 采样时间
        daily_cost_usd: 当日累计成本
        daily_tokens: 当日累计 token
        hourly_cost_usd: 过去一小时成本
        burst_tokens_per_min: 当前突发速率
        active_agent_count: 活跃 Agent 数
        active_task_count: 活跃任务数
    """
    timestamp: float = 0.0
    daily_cost_usd: float = 0.0
    daily_tokens: int = 0
    hourly_cost_usd: float = 0.0
    burst_tokens_per_min: float = 0.0
    active_agent_count: int = 0
    active_task_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "daily_cost_usd": round(self.daily_cost_usd, 6),
            "daily_tokens": self.daily_tokens,
            "hourly_cost_usd": round(self.hourly_cost_usd, 6),
            "burst_tokens_per_min": round(self.burst_tokens_per_min, 1),
            "active_agent_count": self.active_agent_count,
            "active_task_count": self.active_task_count,
        }


@dataclass
class CostAlert:
    """成本告警.

    Attributes:
        alert_id: 告警唯一 ID
        alert_type: 告警类型
        severity: 严重级别
        message: 告警消息
        detail: 详细描述
        triggered_at: 触发时间
        snapshot: 触发时的成本快照
        recommended_level: 推荐回滚等级
        acknowledged: 是否已确认
    """
    alert_id: str = ""
    alert_type: CostAlertType = CostAlertType.BUDGET_WARNING
    severity: AlertSeverity = AlertSeverity.INFO
    message: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)
    triggered_at: float = 0.0
    snapshot: Optional[CostSnapshot] = None
    recommended_level: RollbackLevel = RollbackLevel.L1_WARNING
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "detail": self.detail,
            "triggered_at": self.triggered_at,
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
            "recommended_level": self.recommended_level.value,
            "acknowledged": self.acknowledged,
        }


# ══════════════════════════════════════════════════════════════════
# EWMA 成本异常检测器
# ══════════════════════════════════════════════════════════════════


class CostEWMADetector:
    """基于 EWMA 的成本异常检测器.

    使用指数加权移动平均追踪成本速率，当当前速率超过
    EWMA + N*σ 时触发异常告警。
    """

    def __init__(self, alpha: float = 0.3, anomaly_sigma: float = 3.0, min_samples: int = 10):
        self.alpha = alpha
        self.anomaly_sigma = anomaly_sigma
        self.min_samples = min_samples
        self._ewma: float = 0.0
        self._ewmvar: float = 0.0
        self._sample_count: int = 0
        self._last_value: float = 0.0

    def update(self, value: float) -> Tuple[float, bool]:
        """更新 EWMA 并检测异常.

        Args:
            value: 当前观测值 (如每分钟成本).

        Returns:
            (当前阈值, 是否异常).
        """
        self._last_value = value
        if self._sample_count == 0:
            self._ewma = value
            self._sample_count = 1
            return (value * 3.0, False)

        self._sample_count += 1
        alpha = self.alpha

        prev_ewma = self._ewma
        self._ewma = alpha * value + (1 - alpha) * self._ewma
        diff = value - prev_ewma
        self._ewmvar = (1 - alpha) * (self._ewmvar + alpha * diff * diff)

        if self._sample_count < self.min_samples:
            return (self._ewma * 3.0, False)

        std_dev = math.sqrt(max(self._ewmvar, 1e-9))
        threshold = self._ewma + self.anomaly_sigma * std_dev
        is_anomaly = value > threshold

        return (threshold, is_anomaly)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "ewma": round(self._ewma, 6),
            "std_dev": round(math.sqrt(max(self._ewmvar, 1e-9)), 6),
            "sample_count": self._sample_count,
            "last_value": round(self._last_value, 6),
            "threshold": round(self._ewma + self.anomaly_sigma * math.sqrt(max(self._ewmvar, 1e-9)), 6),
        }

    def reset(self) -> None:
        self._ewma = 0.0
        self._ewmvar = 0.0
        self._sample_count = 0
        self._last_value = 0.0


# ══════════════════════════════════════════════════════════════════
# Cost Monitor Channel
# ══════════════════════════════════════════════════════════════════


class CostMonitorChannel(MarineChannel):
    """成本异常监控与 SLO 告警 Channel.

    持续监控系统 Token 消耗与 LLM 调用成本，
    基于 SLO 阈值生成分级告警，联动回滚 Channel。
    """

    name: str = "cost_monitor"
    description: str = "成本异常监控与 SLO 告警 (Cost Monitor)"
    version: str = "1.0.0"
    priority: ChannelPriority = ChannelPriority.P1

    def __init__(
        self,
        slo: Optional[CostSLO] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._slo: CostSLO = slo or CostSLO()
        self._ewma_detector: CostEWMADetector = CostEWMADetector(
            alpha=self._slo.ewma_alpha,
            anomaly_sigma=self._slo.anomaly_sigma,
            min_samples=self._slo.min_samples,
        )
        # 历史快照 (最近 100 个)
        self._snapshots: List[CostSnapshot] = []
        self._max_snapshots: int = 100
        # 告警历史
        self._alerts: List[CostAlert] = []
        self._max_alerts: int = 200
        # 突发检测
        self._token_burst_buffer: List[Tuple[float, int]] = []  # (timestamp, tokens)
        # 计数器
        self._monitor_cycles: int = 0
        # 本地累计 (当日)
        self._today_tokens: int = 0
        self._today_cost_usd: float = 0.0
        self._today_date: str = ""
        # 回调 — 当触发告警时通知
        self._alert_callbacks: List[Callable[[CostAlert], None]] = []
        # 回滚 Channel 引用 (延迟绑定)
        self._rollback_channel: Optional[Any] = None

    # ── MarineChannel 接口 ─────────────────────────────────

    def initialize(self) -> bool:
        """初始化成本监控 Channel."""
        try:
            self._today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            self._today_tokens = 0
            self._today_cost_usd = 0.0
            self._set_health(ChannelStatus.OK, "Cost Monitor 就绪")
            self._initialized = True
            logger.info(f"✅ {self.name} 初始化完成 (日预算: ${self._slo.daily_budget_usd})")
            return True
        except Exception as e:
            self._set_health(ChannelStatus.ERROR, f"初始化失败: {e}")
            logger.error(f"❌ {self.name} 初始化失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取成本监控状态."""
        latest_snapshot = self._snapshots[-1] if self._snapshots else None
        active_alerts = [a for a in self._alerts if not a.acknowledged]
        return {
            "name": self.name,
            "status": self._health.status.value,
            "slo": self._slo.to_dict(),
            "latest_snapshot": latest_snapshot.to_dict() if latest_snapshot else None,
            "active_alerts": len(active_alerts),
            "total_alerts": len(self._alerts),
            "monitor_cycles": self._monitor_cycles,
            "ewma_stats": self._ewma_detector.get_stats(),
            "today_tokens": self._today_tokens,
            "today_cost_usd": round(self._today_cost_usd, 6),
        }

    def shutdown(self) -> bool:
        """关闭成本监控 Channel."""
        self._set_health(ChannelStatus.OFF, "Shutdown")
        logger.info(f"🛑 {self.name} 已关闭")
        return True

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """处理外部事件."""
        event_type = event.get("type", "")
        if event_type == "cost_check":
            return await self.run_cost_check()
        elif event_type == "record_usage":
            return self.record_usage(
                tokens=event.get("tokens", 0),
                cost_usd=event.get("cost_usd", 0.0),
                agent_id=event.get("agent_id", ""),
                model=event.get("model", ""),
            )
        elif event_type == "acknowledge_alert":
            return self.acknowledge_alert(event.get("alert_id", ""))
        elif event_type == "get_runbook":
            return self.get_runbook()
        else:
            return {"status": "unknown_event", "type": event_type}

    # ── 核心: 成本检查 ─────────────────────────────────

    async def run_cost_check(self) -> Dict[str, Any]:
        """执行一轮完整的成本 SLO 检查.

        Returns:
            检查结果，包含所有触发的告警.
        """
        self._monitor_cycles += 1
        now = time.time()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 日期翻转重置
        if today != self._today_date:
            self._today_date = today
            self._today_tokens = 0
            self._today_cost_usd = 0.0

        # 采集成本数据
        snapshot = self._collect_snapshot(now)
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

        triggered_alerts: List[CostAlert] = []

        # 1. 预算消耗检查
        budget_alerts = self._check_budget_thresholds(snapshot)
        triggered_alerts.extend(budget_alerts)

        # 2. 突发检测
        burst_alerts = self._check_burst(snapshot)
        triggered_alerts.extend(burst_alerts)

        # 3. EWMA 异常检测
        anomaly_alerts = self._check_anomaly(snapshot)
        triggered_alerts.extend(anomaly_alerts)

        # 4. 趋势分析
        trend_alerts = self._check_trend(snapshot)
        triggered_alerts.extend(trend_alerts)

        # 存储告警 & 触发回调
        for alert in triggered_alerts:
            self._alerts.append(alert)
            if len(self._alerts) > self._max_alerts:
                self._alerts = self._alerts[-self._max_alerts:]
            self._fire_alert_callbacks(alert)

        # 更新健康状态
        has_critical = any(a.severity == AlertSeverity.CRITICAL for a in triggered_alerts)
        has_warning = any(a.severity == AlertSeverity.WARNING for a in triggered_alerts)
        if has_critical:
            self._set_health(ChannelStatus.ERROR, "成本 CRITICAL 告警触发")
        elif has_warning:
            self._set_health(ChannelStatus.WARN, "成本 WARNING 告警触发")
        elif self._health.status != ChannelStatus.OFF:
            self._set_health(ChannelStatus.OK, "成本正常")

        return {
            "status": "completed",
            "cycle": self._monitor_cycles,
            "snapshot": snapshot.to_dict(),
            "alerts_triggered": [a.to_dict() for a in triggered_alerts],
            "alert_count": len(triggered_alerts),
            "health": self._health.status.value,
        }

    # ── 用量记录 ───────────────────────────────────────

    def record_usage(
        self,
        tokens: int = 0,
        cost_usd: float = 0.0,
        agent_id: str = "",
        model: str = "",
    ) -> Dict[str, Any]:
        """记录一次 LLM 用量.

        Args:
            tokens: 消耗的 token 数.
            cost_usd: 估算成本 (美元).
            agent_id: 发起调用的 Agent ID.
            model: 使用的模型名称.

        Returns:
            记录结果.
        """
        now = time.time()
        self._today_tokens += tokens
        self._today_cost_usd += cost_usd

        # 突发缓冲
        self._token_burst_buffer.append((now, tokens))
        # 清理过期缓冲
        cutoff = now - self._slo.burst_window_seconds
        self._token_burst_buffer = [
            (ts, tk) for ts, tk in self._token_burst_buffer if ts > cutoff
        ]

        return {
            "status": "recorded",
            "today_tokens": self._today_tokens,
            "today_cost_usd": round(self._today_cost_usd, 6),
            "entry_tokens": tokens,
            "entry_cost_usd": round(cost_usd, 6),
            "agent_id": agent_id,
            "model": model,
        }

    # ── 告警管理 ───────────────────────────────────────

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """确认告警.

        Args:
            alert_id: 告警 ID.

        Returns:
            确认结果.
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return {"status": "acknowledged", "alert_id": alert_id}
        return {"status": "not_found", "alert_id": alert_id}

    def get_active_alerts(self) -> List[CostAlert]:
        """获取所有未确认的活跃告警."""
        return [a for a in self._alerts if not a.acknowledged]

    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取告警历史."""
        return [a.to_dict() for a in self._alerts[-limit:]]

    def register_alert_callback(self, callback: Callable[[CostAlert], None]) -> None:
        """注册告警回调."""
        self._alert_callbacks.append(callback)

    def set_rollback_channel(self, channel: Any) -> None:
        """绑定回滚 Channel."""
        self._rollback_channel = channel

    # ── Runbook 生成 ────────────────────────────────────

    def get_runbook(self) -> Dict[str, Any]:
        """生成成本应急回滚操作手册.

        Returns:
            包含完整 runbook 的字典.
        """
        snapshot = self._snapshots[-1] if self._snapshots else None
        active_alerts = self.get_active_alerts()
        daily_pct = (self._today_cost_usd / max(self._slo.daily_budget_usd, 0.01)) * 100

        return {
            "runbook_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "current_status": {
                "daily_cost_usd": round(self._today_cost_usd, 6),
                "daily_budget_usd": self._slo.daily_budget_usd,
                "daily_usage_pct": round(daily_pct, 1),
                "active_alerts": len(active_alerts),
                "health": self._health.status.value,
            },
            "escalation_levels": {
                "L1_warning": {
                    "trigger": f"日消耗 ≥ {self._slo.warn_ratio * 100:.0f}% 或突发检测触发",
                    "actions": [
                        "1. 通知值班人员检查成本仪表盘",
                        "2. 限制非关键 Agent 并发数降至 50%",
                        "3. 暂停低优先级 (P2) 任务队列",
                        "4. 向团队 Slack/钉钉发送预警通知",
                        "5. 记录成本异常事件到 audit_store",
                    ],
                    "auto_actions": [
                        "reduce_concurrency(factor=0.5)",
                        "pause_priority(ChannelPriority.P2)",
                    ],
                },
                "L2_severe": {
                    "trigger": f"日消耗 ≥ {self._slo.critical_ratio * 100:.0f}% 或 EWMA 异常",
                    "actions": [
                        "1. 🚨 立即通知事件指挥官 (Incident Commander)",
                        "2. 暂停所有非 P0 的 evolution executor 任务",
                        "3. 暂停所有 plaza discussion 自动派发",
                        "4. 将 LLM 模型从高成本切换到低成本 (如 gpt-4 → deepseek)",
                        "5. 启动成本回滚 Channel 进入 L2 状态",
                        "6. 通知财务/预算负责人",
                    ],
                    "auto_actions": [
                        "halt_evolution_non_p0()",
                        "pause_plaza_dispatch()",
                        "switch_model_tier(to='economy')",
                    ],
                },
                "L3_critical": {
                    "trigger": "日消耗 ≥ 100% 预算或 10 分钟内连续 CRITICAL",
                    "actions": [
                        "1. 🔴 紧急: 停止所有 LLM 调用 (除安全相关)",
                        "2. 冻结所有 agent_loop 执行",
                        "3. 保留当前状态快照用于事后分析",
                        "4. 通知 CTO / 技术 VP",
                        "5. 启动事后复盘 (Post-Incident Review) 流程",
                        "6. 记录完整审计日志 (不可变)",
                    ],
                    "auto_actions": [
                        "halt_all_llm_calls()",
                        "freeze_agent_loops()",
                        "snapshot_system_state()",
                        "notify_executive_chain()",
                    ],
                },
            },
            "rollback_procedures": {
                "immediate": [
                    {
                        "step": 1,
                        "action": "设置 BUDGET_HALT=true 环境变量",
                        "effect": "BudgetGuard 将拒绝所有非安全 LLM 请求",
                        "reversible": True,
                    },
                    {
                        "step": 2,
                        "action": "调用 CostRollbackChannel.trigger_rollback(level=L3_CRITICAL)",
                        "effect": "系统进入紧急回滚模式",
                        "reversible": True,
                    },
                    {
                        "step": 3,
                        "action": "在 config/settings.json 中设置 daily_budget 为当前已消耗值",
                        "effect": "阻止进一步消耗",
                        "reversible": True,
                    },
                ],
                "gradual": [
                    {
                        "step": 1,
                        "action": "降低 agent_loop 并发: MAX_CONCURRENT_EXECUTIONS = 2",
                        "effect": "减缓 token 消耗速率约 60-80%",
                        "reversible": True,
                    },
                    {
                        "step": 2,
                        "action": "切换模型到 economy 层级",
                        "effect": "单次调用成本降低约 80-90%",
                        "reversible": True,
                    },
                    {
                        "step": 3,
                        "action": "暂停 evolution 自动审批流程",
                        "effect": "停止自动派发新任务",
                        "reversible": True,
                    },
                ],
                "recovery": [
                    {
                        "step": 1,
                        "action": "确认成本恢复正常 (< 50% 日预算)",
                        "effect": "满足恢复条件",
                    },
                    {
                        "step": 2,
                        "action": "逐步恢复 P1 任务 (每 10 分钟恢复 25%)",
                        "effect": "渐进式恢复避免二次冲击",
                    },
                    {
                        "step": 3,
                        "action": "解除模型限制, 恢复原始配置",
                        "effect": "完全恢复",
                    },
                ],
            },
            "latest_snapshot": snapshot.to_dict() if snapshot else None,
            "active_alerts": [a.to_dict() for a in active_alerts],
        }

    # ── 内部方法 ───────────────────────────────────────

    def _collect_snapshot(self, now: float) -> CostSnapshot:
        """采集当前成本快照."""
        # 计算突发速率
        burst_tokens = sum(
            tk for ts, tk in self._token_burst_buffer
            if ts > now - self._slo.burst_window_seconds
        )
        burst_rate = burst_tokens / max(self._slo.burst_window_seconds / 60.0, 0.01)

        # 尝试获取 UsageStore 数据
        try:
            from agents.budget.store import get_usage_store
            store = get_usage_store()
            today_records = store.query_today()
            db_today_tokens = sum(r.total_tokens for r in today_records)
            db_today_cost = sum(r.cost_usd for r in today_records)
            active_agents = len(set(r.agent_id for r in today_records if r.agent_id))
        except Exception:
            db_today_tokens = self._today_tokens
            db_today_cost = self._today_cost_usd
            active_agents = 0

        return CostSnapshot(
            timestamp=now,
            daily_cost_usd=max(db_today_cost, self._today_cost_usd),
            daily_tokens=max(db_today_tokens, self._today_tokens),
            burst_tokens_per_min=burst_rate,
            active_agent_count=active_agents,
            active_task_count=0,  # 由 task_engine 注入
        )

    def _check_budget_thresholds(self, snapshot: CostSnapshot) -> List[CostAlert]:
        """检查预算阈值."""
        alerts: List[CostAlert] = []
        budget = self._slo.daily_budget_usd
        if budget <= 0:
            return alerts

        ratio = snapshot.daily_cost_usd / budget
        now = time.time()
        alert_id_base = f"cost-{int(now)}"

        if ratio >= 1.0:
            alerts.append(CostAlert(
                alert_id=f"{alert_id_base}-exceeded",
                alert_type=CostAlertType.BUDGET_EXCEEDED,
                severity=AlertSeverity.CRITICAL,
                message=f"🚨 日预算已超支! ${snapshot.daily_cost_usd:.4f} / ${budget:.2f} ({ratio * 100:.1f}%)",
                detail={
                    "daily_cost_usd": snapshot.daily_cost_usd,
                    "daily_budget_usd": budget,
                    "ratio": round(ratio, 4),
                    "daily_tokens": snapshot.daily_tokens,
                },
                triggered_at=now,
                snapshot=snapshot,
                recommended_level=RollbackLevel.L3_CRITICAL,
            ))
        elif ratio >= self._slo.critical_ratio:
            alerts.append(CostAlert(
                alert_id=f"{alert_id_base}-critical",
                alert_type=CostAlertType.BUDGET_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                message=f"🔴 日预算消耗达临界值! ${snapshot.daily_cost_usd:.4f} / ${budget:.2f} ({ratio * 100:.1f}%)",
                detail={
                    "daily_cost_usd": snapshot.daily_cost_usd,
                    "daily_budget_usd": budget,
                    "ratio": round(ratio, 4),
                    "remaining_usd": round(budget - snapshot.daily_cost_usd, 6),
                },
                triggered_at=now,
                snapshot=snapshot,
                recommended_level=RollbackLevel.L2_SEVERE,
            ))
        elif ratio >= self._slo.warn_ratio:
            alerts.append(CostAlert(
                alert_id=f"{alert_id_base}-warning",
                alert_type=CostAlertType.BUDGET_WARNING,
                severity=AlertSeverity.WARNING,
                message=f"⚠️ 日预算消耗达预警线! ${snapshot.daily_cost_usd:.4f} / ${budget:.2f} ({ratio * 100:.1f}%)",
                detail={
                    "daily_cost_usd": snapshot.daily_cost_usd,
                    "daily_budget_usd": budget,
                    "ratio": round(ratio, 4),
                },
                triggered_at=now,
                snapshot=snapshot,
                recommended_level=RollbackLevel.L1_WARNING,
            ))

        return alerts

    def _check_burst(self, snapshot: CostSnapshot) -> List[CostAlert]:
        """检查突发消耗."""
        alerts: List[CostAlert] = []
        if snapshot.burst_tokens_per_min > self._slo.burst_threshold_tokens_per_min:
            now = time.time()
            alerts.append(CostAlert(
                alert_id=f"burst-{int(now)}",
                alert_type=CostAlertType.BURST_DETECTED,
                severity=AlertSeverity.WARNING,
                message=f"⚡ 检测到突发高消耗! {snapshot.burst_tokens_per_min:,.0f} tokens/min (阈值: {self._slo.burst_threshold_tokens_per_min:,.0f})",
                detail={
                    "burst_rate": snapshot.burst_tokens_per_min,
                    "threshold": self._slo.burst_threshold_tokens_per_min,
                    "window_seconds": self._slo.burst_window_seconds,
                },
                triggered_at=now,
                snapshot=snapshot,
                recommended_level=RollbackLevel.L1_WARNING,
            ))
        return alerts

    def _check_anomaly(self, snapshot: CostSnapshot) -> List[CostAlert]:
        """EWMA 异常检测."""
        alerts: List[CostAlert] = []
        cost_per_min = snapshot.daily_cost_usd / max(
            (datetime.now(timezone.utc).hour * 60 + datetime.now(timezone.utc).minute), 1
        ) * 60  # 估算每分钟成本

        threshold, is_anomaly = self._ewma_detector.update(cost_per_min)
        if is_anomaly:
            now = time.time()
            alerts.append(CostAlert(
                alert_id=f"anomaly-{int(now)}",
                alert_type=CostAlertType.ANOMALY_DETECTED,
                severity=AlertSeverity.WARNING,
                message=f"📊 EWMA 检测到成本异常! 当前速率 ${cost_per_min:.6f}/min > 阈值 ${threshold:.6f}/min",
                detail={
                    "current_rate": round(cost_per_min, 6),
                    "threshold": round(threshold, 6),
                    "ewma_stats": self._ewma_detector.get_stats(),
                },
                triggered_at=now,
                snapshot=snapshot,
                recommended_level=RollbackLevel.L2_SEVERE,
            ))
        return alerts

    def _check_trend(self, snapshot: CostSnapshot) -> List[CostAlert]:
        """趋势分析 — 检测成本尖峰."""
        alerts: List[CostAlert] = []
        if len(self._snapshots) < 3:
            return alerts

        recent = self._snapshots[-3:]
        costs = [s.daily_cost_usd for s in recent]
        if costs[0] > 0 and costs[-1] > costs[0] * 2.0:
            now = time.time()
            alerts.append(CostAlert(
                alert_id=f"trend-{int(now)}",
                alert_type=CostAlertType.TREND_SPIKE,
                severity=AlertSeverity.INFO,
                message=f"📈 成本趋势上升: ${costs[0]:.4f} → ${costs[-1]:.4f} (增长 {(costs[-1] / max(costs[0], 0.0001) - 1) * 100:.0f}%)",
                detail={
                    "cost_sequence": [round(c, 6) for c in costs],
                    "growth_pct": round((costs[-1] / max(costs[0], 0.0001) - 1) * 100, 1),
                },
                triggered_at=now,
                snapshot=snapshot,
                recommended_level=RollbackLevel.L1_WARNING,
            ))
        return alerts

    def _fire_alert_callbacks(self, alert: CostAlert) -> None:
        """触发所有告警回调."""
        for cb in self._alert_callbacks:
            try:
                cb(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")

    def _set_health(self, status: ChannelStatus, message: str) -> None:
        """更新健康状态."""
        from .marine_base import ChannelHealth
        self._health = ChannelHealth(
            status=status,
            message=message,
        )

    # ── SLO 配置管理 ──────────────────────────────────

    def update_slo(self, slo: CostSLO) -> None:
        """更新 SLO 配置."""
        self._slo = slo
        self._ewma_detector = CostEWMADetector(
            alpha=slo.ewma_alpha,
            anomaly_sigma=slo.anomaly_sigma,
            min_samples=slo.min_samples,
        )
        logger.info(f"📝 SLO 配置已更新: 日预算 ${slo.daily_budget_usd}")

    def get_slo(self) -> CostSLO:
        """获取当前 SLO 配置."""
        return self._slo


# ══════════════════════════════════════════════════════════════════
# 模块级单例
# ══════════════════════════════════════════════════════════════════

_cost_monitor: Optional[CostMonitorChannel] = None


def get_cost_monitor() -> CostMonitorChannel:
    """获取 CostMonitorChannel 单例."""
    global _cost_monitor
    if _cost_monitor is None:
        _cost_monitor = CostMonitorChannel()
    return _cost_monitor
