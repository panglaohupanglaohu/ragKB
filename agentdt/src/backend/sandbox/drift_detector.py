# -*- coding: utf-8 -*-
"""Drift Detector — 环境偏移检测与仿真触发.

实时监控数字世界状态变化，当检测到显著偏移时
自动触发 TwinLoop 仿真在环过程。

偏移类型:
- 任务目标突变 (task_mutation)
- 资源冲突 (resource_conflict)
- 智能体故障 (agent_failure)
- 约束变更 (constraint_change)
- 性能衰退 (performance_decay)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .models import DriftEvent, DriftType, WorldStateSnapshot

logger = logging.getLogger(__name__)


class DriftDetector:
    """环境偏移检测器."""

    def __init__(
        self,
        drift_threshold: float = 0.3,
        auto_trigger: bool = True,
    ):
        self._drift_threshold = drift_threshold
        self._auto_trigger = auto_trigger
        # 基线快照
        self._baseline: Optional[WorldStateSnapshot] = None
        # 偏移历史
        self._drift_history: List[DriftEvent] = []
        # 触发回调
        self._trigger_callbacks: List[Callable[[DriftEvent], Any]] = []

    def set_baseline(self, snapshot: WorldStateSnapshot) -> None:
        """设置基线快照（正常状态参考）."""
        self._baseline = snapshot
        logger.info(f"📐 基线设置: {snapshot.snapshot_id[:8]}...")

    def on_drift_trigger(self, callback: Callable[[DriftEvent], Any]) -> None:
        """注册偏移触发回调."""
        self._trigger_callbacks.append(callback)

    # ── 偏移检测 ────────────────────────────────────────────────

    def detect(self, current: WorldStateSnapshot) -> List[DriftEvent]:
        """检测当前状态与基线的偏移.

        Returns:
            检测到的偏移事件列表
        """
        if not self._baseline:
            self._baseline = current
            return []

        drifts: List[DriftEvent] = []

        # 1. 任务突变检测
        task_drift = self._detect_task_mutation(current)
        if task_drift:
            drifts.append(task_drift)

        # 2. 资源冲突检测
        resource_drift = self._detect_resource_conflict(current)
        if resource_drift:
            drifts.append(resource_drift)

        # 3. 智能体故障检测
        agent_drift = self._detect_agent_failure(current)
        if agent_drift:
            drifts.append(agent_drift)

        # 4. 约束变更检测
        constraint_drift = self._detect_constraint_change(current)
        if constraint_drift:
            drifts.append(constraint_drift)

        # 5. 性能衰退检测
        perf_drift = self._detect_performance_decay(current)
        if perf_drift:
            drifts.append(perf_drift)

        # 记录并触发
        for drift in drifts:
            self._drift_history.append(drift)
            if drift.trigger_sandbox and self._auto_trigger:
                self._fire_trigger(drift)

        return drifts

    def _detect_task_mutation(self, current: WorldStateSnapshot) -> Optional[DriftEvent]:
        """检测任务目标突变."""
        baseline_tasks = set(t.get("id", "") for t in self._baseline.pending_tasks)
        current_tasks = set(t.get("id", "") for t in current.pending_tasks)

        new_tasks = current_tasks - baseline_tasks
        if not new_tasks:
            return None

        severity = min(1.0, len(new_tasks) / max(len(baseline_tasks), 1))
        if severity < self._drift_threshold:
            return None

        return DriftEvent(
            drift_type=DriftType.TASK_MUTATION,
            severity=severity,
            description=f"新增 {len(new_tasks)} 个任务",
            affected_agents=[],  # 所有智能体受影响
            trigger_sandbox=severity > 0.5,
        )

    def _detect_resource_conflict(self, current: WorldStateSnapshot) -> Optional[DriftEvent]:
        """检测资源冲突."""
        overloaded = [
            r for r in current.resources
            if r.utilization > 0.9 or not r.available
        ]
        if not overloaded:
            return None

        severity = len(overloaded) / max(len(current.resources), 1)
        if severity < self._drift_threshold:
            return None

        affected = []
        for r in overloaded:
            affected.extend(r.metadata.get("users", []))

        return DriftEvent(
            drift_type=DriftType.RESOURCE_CONFLICT,
            severity=severity,
            description=f"{len(overloaded)} 个资源过载或不可用",
            affected_agents=list(set(affected)),
            trigger_sandbox=severity > 0.4,
        )

    def _detect_agent_failure(self, current: WorldStateSnapshot) -> Optional[DriftEvent]:
        """检测智能体故障."""
        failed_agents = []
        for agent_id, state in current.agent_states.items():
            baseline_state = self._baseline.agent_states.get(agent_id, {})
            if state.get("state") == "error" and baseline_state.get("state") != "error":
                failed_agents.append(agent_id)

        if not failed_agents:
            return None

        severity = len(failed_agents) / max(len(current.agent_states), 1)

        return DriftEvent(
            drift_type=DriftType.AGENT_FAILURE,
            severity=max(severity, 0.5),  # 智能体故障至少中等严重
            description=f"{len(failed_agents)} 个智能体进入错误状态",
            affected_agents=failed_agents,
            trigger_sandbox=True,  # 智能体故障总是触发沙箱
        )

    def _detect_constraint_change(self, current: WorldStateSnapshot) -> Optional[DriftEvent]:
        """检测约束变更."""
        baseline_constraints = {c.name for c in self._baseline.constraints}
        current_constraints = {c.name for c in current.constraints}

        added = current_constraints - baseline_constraints
        removed = baseline_constraints - current_constraints

        if not added and not removed:
            return None

        total_change = len(added) + len(removed)
        severity = min(1.0, total_change / max(len(baseline_constraints), 1))
        if severity < self._drift_threshold:
            return None

        return DriftEvent(
            drift_type=DriftType.CONSTRAINT_CHANGE,
            severity=severity,
            description=f"约束变更: +{len(added)} -{len(removed)}",
            affected_agents=[],
            trigger_sandbox=severity > 0.5,
        )

    def _detect_performance_decay(self, current: WorldStateSnapshot) -> Optional[DriftEvent]:
        """检测性能衰退."""
        baseline_metrics = self._baseline.global_metrics
        current_metrics = current.global_metrics

        if not baseline_metrics or not current_metrics:
            return None

        # 比较共有指标
        decay_count = 0
        total_compared = 0
        affected = []

        for key in baseline_metrics:
            if key in current_metrics:
                total_compared += 1
                if current_metrics[key] < baseline_metrics[key] * 0.7:  # 下降超过30%
                    decay_count += 1

        if total_compared == 0 or decay_count == 0:
            return None

        severity = decay_count / total_compared
        if severity < self._drift_threshold:
            return None

        return DriftEvent(
            drift_type=DriftType.PERFORMANCE_DECAY,
            severity=severity,
            description=f"{decay_count}/{total_compared} 项指标衰退超30%",
            affected_agents=affected,
            trigger_sandbox=severity > 0.4,
        )

    # ── 触发 ────────────────────────────────────────────────────

    def _fire_trigger(self, drift: DriftEvent) -> None:
        """触发沙箱仿真."""
        logger.warning(f"⚡ 偏移触发沙箱: {drift.drift_type.value} severity={drift.severity:.2f}")
        for cb in self._trigger_callbacks:
            try:
                cb(drift)
            except Exception as e:
                logger.error(f"触发回调失败: {e}")

    # ── 查询 ────────────────────────────────────────────────────

    def get_drift_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取偏移历史."""
        return [
            {
                "drift_id": d.drift_id,
                "type": d.drift_type.value,
                "severity": d.severity,
                "description": d.description,
                "timestamp": d.timestamp,
                "triggered": d.trigger_sandbox,
            }
            for d in self._drift_history[-limit:]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """获取检测器统计."""
        type_counts: Dict[str, int] = {}
        for d in self._drift_history:
            t = d.drift_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_drifts": len(self._drift_history),
            "triggered_count": sum(1 for d in self._drift_history if d.trigger_sandbox),
            "by_type": type_counts,
            "has_baseline": self._baseline is not None,
        }
