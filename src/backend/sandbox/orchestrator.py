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
        """同步包装异步 LLM 决策 (兼容同步调用场景).

        P4 修复: ThreadPoolExecutor 不会自动传播 contextvar，
        必须显式 copy_context() 跨线程透传 token_scope，
        否则孪生 LLM 决策的 token 归因全部丢失。
        """
        import asyncio
        import contextvars
        import concurrent.futures
        ctx = contextvars.copy_context()  # 捕获主线程的 token_scope
        def _run():
            return ctx.run(asyncio.run, llm_decision(twin, world, all_twins))
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(_run)
                return future.result(timeout=10)
        except RuntimeError:
            return ctx.run(asyncio.run, llm_decision(twin, world, all_twins))

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

    def sync_from_digital_twin(self, dt_state: Dict[str, Any]) -> Dict[str, Any]:
        """从数字孪生状态同步场景到 SECS 世界.

        将 DT 的 rooms/positions/interactions 转换为
        SECS 的 agents/resources/workflow_edges。
        """
        rooms = dt_state.get("rooms", [])
        positions = dt_state.get("positions", {})
        interactions = dt_state.get("interactions", [])

        # rooms → 资源 (每个房间是一个空间资源)
        resources = [
            {"id": r.get("id", f"room-{i}"), "type": "room",
             "capacity": r.get("capacity", 5.0), "utilization": 0.0,
             "available": True, "metadata": {"name": r.get("name", f"Room {i}")}}
            for i, r in enumerate(rooms)
        ]

        # positions → agent 状态 (agent 在哪个房间, 含真实 skills)
        agents = []
        for agent_id, room_id in positions.items():
            # 尝试从 TeamManager 获取真实 skills
            skills = []
            tools = []
            role = "general"
            if _team_manager:
                try:
                    for team in _team_manager.list_teams():
                        for agent in (team.agents if isinstance(team.agents, list) else team.agents.values() if isinstance(team.agents, dict) else []):
                            if (getattr(agent, 'agent_id', None) == agent_id):
                                role = getattr(agent, 'role', 'general')
                                skills = getattr(agent, 'skills', []) or []
                                tools = getattr(agent, 'tools', []) or []
                                break
                except Exception:
                    pass
            agents.append({
                "id": agent_id, "name": agent_id, "role": role,
                "state": "idle", "room": room_id or "",
                "skills": skills, "tools": tools,
            })

        # interactions → workflow edges (谁和谁通信过)
        edges = []
        seen = set()
        for ix in interactions:
            key = (ix.get("from", ""), ix.get("to", ""))
            if key not in seen and key[0] and key[1]:
                seen.add(key)
                edges.append({
                    "source": ix["from"], "target": ix["to"],
                    "channel": "direct", "message_type": ix.get("type", "handoff"),
                    "weight": 1.0,
                })

        # 同步到世界状态
        self.sync_world(
            agents=agents,
            resources=resources,
            workflow_edges=edges,
        )

        summary = {
            "synced_agents": len(agents),
            "synced_rooms": len(resources),
            "synced_edges": len(edges),
            "agent_ids": [a["id"] for a in agents],
        }
        logger.info(f"🔄 DT→SECS 同步完成: {summary['synced_agents']} agents, "
                    f"{summary['synced_rooms']} rooms, {summary['synced_edges']} edges")
        return summary

    def get_world_summary(self) -> Dict[str, Any]:
        """获取世界状态摘要."""
        return self.world_state.to_dict()

    # ── 完整流水线 ──────────────────────────────────────────────

    async def run_full_pipeline(self, session_id: str) -> Dict[str, Any]:
        """执行完整的 SECS 流水线.

        流程: 快照 → 仿真 → 评估 → 对齐 → 输出

        P4: 包裹 token_scope，使孪生演练的 LLM token 归因到 run_id。
        容错保证: 无论评估/对齐是否成功，session 状态都不会卡在 EVALUATING。

        Returns:
            包含仿真结果、评估得分、最优SOP的完整结果
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "session_not_found"}

        # P4: 注入 token 归因上下文
        from agents.token_context import token_scope, new_run_id
        run_id = new_run_id("drill")
        session._token_run_id = run_id  # 附着到 session 供后续查询

        try:
            with token_scope(run_id=run_id, phase="drill",
                             scenario_id=session_id, team_id=session.team_id):
                # Step 1: 执行仿真
                session = await self.twin_loop.run_simulation(session_id)

                # 检查是否被用户中断（stop_event / pause）
                if session.status != SandboxStatus.RUNNING:
                    # 被 stop/pause 中断 → 跳过后续对齐，直接返回
                    logger.info("⏹ 仿真被中断 (status=%s)，跳过对齐与 Gate", session.status.value)
                    return {
                        "session_id": session.session_id,
                        "status": session.status.value,
                        "total_steps": session.total_steps_executed,
                        "alignment": None,
                        "token_run_id": run_id,
                        "interrupted": True,
                    }

                # Step 2: 对齐（包含评估 + 演化循环 + SOP提取）
                alignment_result = await self.aligner.align_session(session)

            # P4.2: passed→ratchet-lock 前调 Token Gate
            gate_report: Dict[str, Any] = {}
            ratchet_locked = False
            try:
                from agents.token_ledger import LEDGER
                from agents.token_policy import ENGINE, TokenBudget
                run_data = LEDGER.run(run_id)
                # 孪生演练默认预算：max_tokens=100000, min_efficiency=0.0
                budget = TokenBudget(max_tokens=100000, min_efficiency=0.0)
                gate_report = ENGINE.evaluate(run_data, budget)
                decision = gate_report.get("decision", "pass")
                if decision == "block":
                    # block 不锁定棘轮 — 记录原因但流程继续
                    logger.warning(
                        "🚫 Drill run %s Token Gate BLOCK — 棘轮锁定被拦截: %s",
                        run_id, gate_report.get("violations", []),
                    )
                elif decision == "warn":
                    logger.info("⚠️ Drill run %s Token Gate WARN: %s", run_id, gate_report)
                else:
                    ratchet_locked = True
                    # P4.3: 达标 token 节省 push ratchet（只进不退）
                    self._push_drill_ratchet(session, run_data, gate_report)
            except Exception as ge:
                logger.warning("Drill Token Gate 评估失败（不阻断）: %s", ge)

            return {
                "session_id": session.session_id,
                "status": session.status.value,
                "total_steps": session.total_steps_executed,
                "alignment": alignment_result,
                "token_run_id": run_id,
                "gate": gate_report,
                "ratchet_locked": ratchet_locked,
            }

        except Exception as e:
            logger.error(f"❌ 流水线执行失败: {e}")
            # [fix] 确保状态不会卡在 EVALUATING: 任何异常都回退到 COMPLETED
            if session.status == SandboxStatus.EVALUATING:
                session.status = SandboxStatus.COMPLETED
                logger.info(f"🔄 状态回退: EVALUATING → COMPLETED (因异常)")
            return {"error": str(e), "session_id": session_id, "status": session.status.value, "token_run_id": run_id}

    # ── 策略注入 ────────────────────────────────────────────────

    def _push_drill_ratchet(self, session, run_data: Dict[str, Any], gate_report: Dict[str, Any]) -> None:
        """P4.3: 达标的 token 效率推进 cost_efficiency:{team_id} 棘轮（只进不退）.

        metric = score / max(tokens/1000, 1e-6)
        """
        try:
            from agents.ratchet_ledger import get_ratchet_ledger
            team_id = getattr(session, "team_id", "") or "default"
            tokens = float(run_data.get("total", 0) or 0)
            # 从 session 的 evaluation 取 score
            score = 0.0
            eval_data = getattr(session, "evaluation", {}) or {}
            if isinstance(eval_data, dict):
                score = float(eval_data.get("total_score", 0) or 0)
            if tokens <= 0:
                return
            efficiency = score / max(tokens / 1000.0, 1e-6)
            ratchet = get_ratchet_ledger()
            result = ratchet.advance(
                f"cost_efficiency:{team_id}",
                efficiency,
                evidence={
                    "run_id": run_data.get("run_id", ""),
                    "tokens": tokens,
                    "score": score,
                    "gate": gate_report.get("decision", "pass"),
                    "scenario_id": getattr(session, "session_id", ""),
                },
            )
            logger.info(
                "🔒 Drill ratchet push cost_efficiency:%s → %.4f (advanced=%s)",
                team_id, efficiency, result.get("advanced"),
            )
        except Exception as e:
            logger.warning("Drill ratchet push 失败（非致命）: %s", e)

    async def inject_strategy(self, session_id: str) -> Dict[str, Any]:
        """注入最优策略到真实环境."""
        return await self.twin_loop.inject_strategy(session_id)

    async def inject_chaos_event(
        self,
        session_id: str,
        event_type: str,
        target_agent: Optional[str] = None,
        skill_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """注入混沌事件到运行中的沙箱."""
        return await self.twin_loop.inject_chaos_event(
            session_id=session_id,
            event_type=event_type,
            target_agent=target_agent,
            skill_id=skill_id,
        )

    def stop_simulation(self, session_id: str) -> Dict[str, Any]:
        """停止正在运行的仿真."""
        return self.twin_loop.stop_simulation(session_id)

    async def step_once(self, session_id: str) -> Dict[str, Any]:
        """单步执行仿真."""
        return await self.twin_loop.step_once(session_id)

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
