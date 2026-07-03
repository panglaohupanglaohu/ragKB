# -*- coding: utf-8 -*-
"""Sandbox Channel — MarineChannel 集成.

将 SECS 系统作为标准 Channel 接入现有的 Marine Channel 注册表,
支持健康检查、状态报告和定期偏移检测。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from channels.marine_base import (
    MarineChannel,
    ChannelHealth,
    ChannelMetrics,
    ChannelPriority,
    ChannelStatus,
)
from .orchestrator import SECSOrchestrator

logger = logging.getLogger(__name__)


class SandboxChannel(MarineChannel):
    """SECS 沙箱 Channel — 自进化协同沙箱系统的 Channel 接口.

    职责:
    - 提供标准化的 Channel 健康检查
    - 定期执行环境偏移检测
    - 上报仿真统计到 Channel 注册表
    """

    name = "sandbox_secs"
    description = "自进化协同沙箱系统 (SECS) — 智能体数字孪生预演场"
    version = "1.0.0"
    priority = ChannelPriority.P1
    dependencies: List[str] = []

    def __init__(self):
        self._orchestrator: Optional[SECSOrchestrator] = None
        self._health = ChannelHealth(
            status=ChannelStatus.OFF, message="未初始化"
        )
        self._metrics = ChannelMetrics()
        self._initialized = False
        self._drift_check_task: Optional[asyncio.Task] = None

    # ── MarineChannel 接口实现 ──────────────────────────────────

    def initialize(self) -> bool:
        """初始化 SECS 系统."""
        try:
            self._orchestrator = SECSOrchestrator()
            self._health = ChannelHealth(
                status=ChannelStatus.OK,
                message="SECS 系统运行中",
                last_check=datetime.now(),
            )
            self._initialized = True
            logger.info("✅ SandboxChannel 初始化成功")
            return True
        except Exception as e:
            self._health = ChannelHealth(
                status=ChannelStatus.ERROR,
                message=f"初始化失败: {e}",
                last_check=datetime.now(),
            )
            logger.error(f"❌ SandboxChannel 初始化失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """返回 Channel 状态报告."""
        stats = self._orchestrator.get_global_stats() if self._orchestrator else {}
        return {
            "name": self.name,
            "version": self.version,
            "status": self._health.status.value,
            "message": self._health.message,
            "initialized": self._initialized,
            "stats": stats,
            "metrics": {
                "calls_total": self._metrics.calls_total,
                "calls_success": self._metrics.calls_success,
                "calls_failed": self._metrics.calls_failed,
                "avg_latency_ms": self._metrics.avg_latency_ms,
            },
        }

    def check(self) -> Tuple[ChannelStatus, str]:
        """健康检查."""
        if not self._initialized or not self._orchestrator:
            return ChannelStatus.OFF, "未初始化"

        try:
            stats = self._orchestrator.get_global_stats()
            return ChannelStatus.OK, f"运行中 | 会话={stats['twin_loop']['total_sessions']}"
        except Exception as e:
            return ChannelStatus.ERROR, str(e)

    def shutdown(self) -> None:
        """关闭 Channel."""
        if self._drift_check_task and not self._drift_check_task.done():
            self._drift_check_task.cancel()
        # 持久化记忆
        if self._orchestrator:
            self._orchestrator.memory_pool.save_all()
        self._initialized = False
        self._health.status = ChannelStatus.OFF
        logger.info("🛑 SandboxChannel 已关闭")

    # ── 编排器访问 ──────────────────────────────────────────────

    def get_orchestrator(self) -> Optional[SECSOrchestrator]:
        """获取编排器实例."""
        return self._orchestrator

    # ── 定期偏移检测 ────────────────────────────────────────────

    async def start_drift_monitoring(self, interval_seconds: float = 60.0) -> None:
        """启动定期偏移监控."""
        if not self._orchestrator:
            return

        async def _monitor_loop():
            while self._initialized:
                try:
                    drifts = self._orchestrator.check_drift()
                    if drifts:
                        triggered = [d for d in drifts if d.get("triggered")]
                        if triggered:
                            logger.warning(f"⚡ 检测到 {len(triggered)} 个触发级偏移")
                except Exception as e:
                    logger.error(f"偏移检测异常: {e}")
                await asyncio.sleep(interval_seconds)

        self._drift_check_task = asyncio.create_task(_monitor_loop())
        logger.info(f"🔍 偏移监控已启动 (间隔={interval_seconds}s)")

    # ── 指标更新 ────────────────────────────────────────────────

    def record_call(self, success: bool, latency_ms: float) -> None:
        """记录一次 API 调用指标."""
        self._metrics.calls_total += 1
        if success:
            self._metrics.calls_success += 1
        else:
            self._metrics.calls_failed += 1

        # 更新延迟统计
        n = self._metrics.calls_total
        self._metrics.avg_latency_ms = (
            (self._metrics.avg_latency_ms * (n - 1) + latency_ms) / n
        )
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)
        if latency_ms < self._metrics.min_latency_ms:
            self._metrics.min_latency_ms = latency_ms
        self._metrics.last_call_time = datetime.now()
