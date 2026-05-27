# -*- coding: utf-8 -*-
"""SECS Orchestrator — 系统编排器.

将四维一体的组件统一编排:
- WorldStateManager (MADTwin)
- MemoryPool + ZeroExpEngine (AAS)
- TwinLoopEngine (TwinLoop)
- GlobalCritic + StrategyAligner (DT-MADDPG)

提供统一的高层 API 供路由层调用。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .models import (
    SandboxSession,
    SandboxStatus,
    SimulationMode,
)
from .world_state import WorldStateManager
from .memory_system import MemoryPool
from .twin_loop import TwinLoopEngine
from .zero_exp_engine import ZeroExpEngine
from .drift_detector import DriftDetector
from .global_critic import GlobalCritic
from .strategy_aligner import StrategyAligner
from .llm_decision import llm_decision

logger = logging.getLogger(__name__)


class SECSOrchestrator:
    """SECS 系统编排器 — 四维一体统一入口."""

    def __init__(self):
        # Layer 1: 环境语义映射
        self.world_state = WorldStateManager()
        # Layer 2: 认知进化循环
        self.memory_pool = MemoryPool()
        self.zero_exp = ZeroExpEngine(self.memory_pool)
        # Layer 3: 策略试错实验
        self.twin_loop = TwinLoopEngine(self.world_state, self.memory_pool)
        self.drift_detector = DriftDetector()
        # Layer 4: 集体智慧对齐
        self.critic = GlobalCritic()
        self.aligner = StrategyAligner(self.critic, self.zero_exp)

        # LLM 模式标志
        self._llm_mode = False

        # 注册偏移触发回调
        self.drift_detector.on_drift_trigger(self._on_drift_trigger)

        logger.info("🚀 SECS 编排器初始化完成")

    # ── 会话管理 ────────────────────────────────────────────────

    def create_session(
        self,
        team_id: str = "default",
        mode: SimulationMode = SimulationMode.WHAT_IF,
        max_steps: int = 50,
        speed_factor: float = 10.0,
        parallel_branches: int = 3,
        trigger_description: str = "",
        use_llm: bool = False,
    ) -> SandboxSession:
        """创建沙箱会话."""
        # 如果启用 LLM 模式，注入 LLM 决策函数
        if use_llm or self._llm_mode:
            self.twin_loop._decision_func = self._llm_decision_wrapper
        else:
            self.twin_loop._decision_func = self.twin_loop._default_decision

        return self.twin_loop.create_session(
            team_id=team_id,
            mode=mode,
            max_steps=max_steps,
            speed_factor=speed_factor,
            parallel_branches=parallel_branches,
            trigger_description=trigger_description,
        )

    def set_llm_mode(self, enabled: bool) -> None:
        """启用/禁用 LLM 驱动的决策模式."""
        self._llm_mode = enabled
        if enabled:
            self.twin_loop._decision_func = self._llm_decision_wrapper
            logger.info("🧠 SECS 切换到 LLM 决策模式")
        else:
            self.twin_loop._decision_func = self.twin_loop._default_decision
            logger.info("📏 SECS 切换到规则决策模式")

    def _llm_decision_wrapper(self, twin, world, all_twins):
        """同步包装异步 LLM 决策 (兼容同步调用场景)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # 如果已在事件循环中，创建 task 并发执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run, llm_decision(twin, world, all_twins)
                )
                return future.result(timeout=10)
        except RuntimeError:
            # 没有运行中的事件循环
            return asyncio.run(llm_decision(twin, world, all_twins))

    def get_session(self, session_id: str) -> Optional[SandboxSession]:
        """获取会话."""
        return self.twin_loop.get_session(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出会话."""
        return self.twin_loop.list_sessions()

    # ── 世界状态同步 ────────────────────────────────────────────

    def sync_world(
        self,
        team_id: str = "default",
        agents: List[Dict] = None,
        resources: List[Dict] = None,
        tasks: List[Dict] = None,
        constraints: List[Dict] = None,
        workflow_edges: List[Dict] = None,
    ) -> None:
        """同步世界状态."""
        if agents:
            self.world_state.sync_agents_from_team({"agents": agents})
        if resources:
            self.world_state.sync_resources(resources)
        if tasks:
            self.world_state.sync_tasks(tasks)
        if constraints:
            self.world_state.sync_constraints(constraints)
        if workflow_edges:
            self.world_state.sync_workflow(workflow_edges)

    def get_world_summary(self) -> Dict[str, Any]:
        """获取世界状态摘要."""
        return self.world_state.to_dict()

    # ── 完整流水线 ──────────────────────────────────────────────

    async def run_full_pipeline(self, session_id: str) -> Dict[str, Any]:
        """执行完整的 SECS 流水线.

        流程: 快照 → 仿真 → 评估 → 对齐 → 输出

        Returns:
            包含仿真结果、评估得分、最优SOP的完整结果
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "session_not_found"}

        try:
            # Step 1: 执行仿真
            session = await self.twin_loop.run_simulation(session_id)

            # Step 2: 对齐（包含评估 + 演化循环 + SOP提取）
            alignment_result = await self.aligner.align_session(session)

            return {
                "session_id": session.session_id,
                "status": session.status.value,
                "total_steps": session.total_steps_executed,
                "alignment": alignment_result,
            }

        except Exception as e:
            logger.error(f"❌ 流水线执行失败: {e}")
            return {"error": str(e), "session_id": session_id}

    # ── 策略注入 ────────────────────────────────────────────────

    async def inject_strategy(self, session_id: str) -> Dict[str, Any]:
        """注入最优策略到真实环境."""
        return await self.twin_loop.inject_strategy(session_id)

    # ── 偏移处理 ────────────────────────────────────────────────

    def check_drift(self) -> List[Dict[str, Any]]:
        """检测环境偏移."""
        snapshot = self.world_state.take_snapshot()
        drifts = self.drift_detector.detect(snapshot)
        return [
            {
                "drift_id": d.drift_id,
                "type": d.drift_type.value,
                "severity": d.severity,
                "triggered": d.trigger_sandbox,
            }
            for d in drifts
        ]

    def _on_drift_trigger(self, drift) -> None:
        """偏移触发回调 — 自动创建仿真会话."""
        logger.warning(f"⚡ 自动触发仿真: {drift.drift_type.value}")
        session = self.create_session(
            trigger_description=drift.description,
            mode=SimulationMode.PARALLEL,
        )
        session.trigger_drift = drift
        # 注意: 实际执行需要异步，这里只创建会话
        # 真正的自动执行在 channel 的定期检查中触发

    # ── 查询 ────────────────────────────────────────────────────

    def get_drift_history(self) -> List[Dict[str, Any]]:
        """获取偏移历史."""
        return self.drift_detector.get_drift_history()

    def get_sop_library(self) -> List[Dict[str, Any]]:
        """获取 SOP 库."""
        return self.zero_exp.get_sop_library()

    def get_agent_memory_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体记忆统计."""
        memory = self.memory_pool.get_or_create(agent_id)
        return memory.get_stats()

    def get_global_stats(self) -> Dict[str, Any]:
        """获取系统全局统计."""
        return {
            "twin_loop": self.twin_loop.get_stats(),
            "zero_exp": self.zero_exp.get_stats(),
            "critic": self.critic.get_stats(),
            "aligner": self.aligner.get_stats(),
            "drift_detector": self.drift_detector.get_stats(),
            "world_state": self.world_state.to_dict(),
            "memory_pool": self.memory_pool.get_global_stats(),
        }
