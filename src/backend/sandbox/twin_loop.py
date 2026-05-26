# -*- coding: utf-8 -*-
"""TwinLoop Engine — 策略试错实验层 (仿真在环控制).

核心职责:
1. snapshot_world() — 二次映射快照
2. spawn_twins() — 创建智能体沙箱副本
3. run_simulation(max_steps, speed_factor) — 并行 What-if 推演
4. evaluate_outcomes() — 评估策略得分
5. inject_best_strategy() — 闭环注入

触发式仿真: 一旦检测到"环境偏移"，自动触发 Simulation-in-the-loop。
"""

from __future__ import annotations

import asyncio
import copy
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from .models import (
    AgentTwin,
    CollaborationSOP,
    DriftEvent,
    SandboxSession,
    SandboxStatus,
    SimulationMode,
    SimulationStep,
    StrategyStatus,
    WorldStateSnapshot,
)
from .memory_system import AgentMemory, MemoryPool
from .world_state import WorldStateManager

logger = logging.getLogger(__name__)


# 默认决策函数类型
DecisionFunc = Callable[[AgentTwin, WorldStateSnapshot, List[AgentTwin]], Dict[str, Any]]


class TwinLoopEngine:
    """TwinLoop 仿真引擎 — 策略试错实验的核心运行中枢.

    支持:
    - 单场景 What-if 推演
    - 并行多策略对比
    - 演化搜索最优策略
    """

    def __init__(
        self,
        world_state: WorldStateManager,
        memory_pool: MemoryPool,
        decision_func: Optional[DecisionFunc] = None,
    ):
        self._world_state = world_state
        self._memory_pool = memory_pool
        self._decision_func = decision_func or self._default_decision
        # 活跃会话
        self._sessions: Dict[str, SandboxSession] = {}
        # 仿真事件回调
        self._step_callbacks: List[Callable] = []
        # 并发控制
        self._semaphore = asyncio.Semaphore(5)

    # ── 会话管理 ────────────────────────────────────────────────

    def create_session(
        self,
        team_id: str,
        mode: SimulationMode = SimulationMode.WHAT_IF,
        max_steps: int = 100,
        speed_factor: float = 10.0,
        parallel_branches: int = 3,
        trigger_drift: Optional[DriftEvent] = None,
        trigger_description: str = "",
    ) -> SandboxSession:
        """创建新的沙箱会话."""
        session = SandboxSession(
            team_id=team_id,
            mode=mode,
            max_steps=max_steps,
            speed_factor=speed_factor,
            parallel_branches=parallel_branches,
            trigger_drift=trigger_drift,
            trigger_description=trigger_description,
        )
        self._sessions[session.session_id] = session
        logger.info(f"🏖️ 沙箱会话创建: {session.session_id[:8]}... mode={mode.value}")
        return session

    def get_session(self, session_id: str) -> Optional[SandboxSession]:
        """获取会话."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话摘要."""
        return [
            {
                "session_id": s.session_id,
                "status": s.status.value,
                "mode": s.mode.value,
                "team_id": s.team_id,
                "steps": s.total_steps_executed,
                "created_at": s.created_at,
            }
            for s in self._sessions.values()
        ]

    # ── 仿真执行 ────────────────────────────────────────────────

    async def run_simulation(self, session_id: str) -> SandboxSession:
        """执行仿真循环.

        流程:
        1. 快照当前世界状态
        2. 生成孪生智能体
        3. 迭代执行仿真步骤
        4. 返回包含完整结果的会话
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        async with self._semaphore:
            try:
                # Step 1: 快照
                session.status = SandboxStatus.SNAPSHOTTING
                snapshot = self._world_state.take_snapshot()
                session.initial_snapshot = snapshot
                session.snapshots.append(snapshot.snapshot_id)

                # Step 2: 生成孪生体
                session.twins = self._spawn_twins(snapshot)
                session.status = SandboxStatus.RUNNING

                # Step 3: 仿真循环
                if session.mode == SimulationMode.PARALLEL:
                    await self._run_parallel(session, snapshot)
                else:
                    await self._run_sequential(session, snapshot)

                # Step 4: 标记完成
                session.status = SandboxStatus.EVALUATING
                session.updated_at = datetime.now(timezone.utc).isoformat()

            except Exception as e:
                session.status = SandboxStatus.FAILED
                logger.error(f"❌ 仿真失败: {e}")
                raise

        return session

    async def _run_sequential(self, session: SandboxSession, snapshot: WorldStateSnapshot) -> None:
        """顺序执行仿真步骤."""
        sim_state = copy.deepcopy(snapshot)

        for step_num in range(session.max_steps):
            step = await self._execute_step(session, sim_state, step_num)
            session.steps.append(step)
            session.total_steps_executed += 1

            # 通知回调
            for cb in self._step_callbacks:
                try:
                    await cb(session.session_id, step)
                except Exception:
                    pass

            # 检查是否所有任务完成
            if self._check_convergence(session, step):
                logger.info(f"✅ 仿真收敛于步骤 {step_num}")
                break

            # 加速仿真（跳过等待）
            await asyncio.sleep(0.01 / session.speed_factor)

    async def _run_parallel(self, session: SandboxSession, snapshot: WorldStateSnapshot) -> None:
        """并行执行多策略分支."""
        branches: List[List[SimulationStep]] = []

        async def run_branch(branch_id: int, strategy_params: Dict[str, Any]):
            """运行单个策略分支."""
            sim_state = copy.deepcopy(snapshot)
            branch_steps = []
            # 应用策略参数到孪生体
            twins = copy.deepcopy(session.twins)
            for twin in twins:
                twin.strategy_params = strategy_params

            for step_num in range(session.max_steps):
                step = await self._execute_step_with_twins(twins, sim_state, step_num)
                branch_steps.append(step)
                if self._check_convergence_from_steps(branch_steps):
                    break
                await asyncio.sleep(0.01 / session.speed_factor)

            return branch_steps

        # 生成不同策略参数
        strategies = self._generate_strategy_variants(session.parallel_branches)

        # 并行执行
        tasks = [
            run_branch(i, strat) for i, strat in enumerate(strategies)
        ]
        results = await asyncio.gather(*tasks)

        # 选择最优分支
        best_idx = 0
        best_reward = -float("inf")
        for idx, branch_steps in enumerate(results):
            total_reward = sum(s.global_reward for s in branch_steps)
            if total_reward > best_reward:
                best_reward = total_reward
                best_idx = idx
            branches.append(branch_steps)

        session.steps = branches[best_idx] if branches else []
        session.total_steps_executed = len(session.steps)
        logger.info(f"🏆 最优分支: #{best_idx} reward={best_reward:.2f}")

    async def _execute_step(
        self, session: SandboxSession, sim_state: WorldStateSnapshot, step_num: int
    ) -> SimulationStep:
        """执行单个仿真步骤."""
        return await self._execute_step_with_twins(session.twins, sim_state, step_num)

    async def _execute_step_with_twins(
        self, twins: List[AgentTwin], sim_state: WorldStateSnapshot, step_num: int
    ) -> SimulationStep:
        """使用指定孪生体执行单步."""
        step = SimulationStep(step_id=step_num)
        agent_actions: Dict[str, Dict[str, Any]] = {}
        messages: List[Dict[str, Any]] = []
        step_rewards: Dict[str, float] = {}

        for twin in twins:
            # 获取智能体记忆
            memory = self._memory_pool.get_or_create(twin.source_agent_id)
            # 决策
            action = self._decision_func(twin, sim_state, twins)
            agent_actions[twin.twin_id] = action

            # 计算奖励
            reward = self._calculate_reward(twin, action, sim_state)
            step_rewards[twin.twin_id] = reward
            twin.rewards_collected += reward
            twin.actions_taken += 1

            # 记录通信
            if action.get("message"):
                messages.append({
                    "from": twin.twin_id,
                    "to": action.get("target", "broadcast"),
                    "content": action["message"],
                    "type": action.get("message_type", "info"),
                })
                twin.messages_sent += 1

            # 更新孪生体状态
            twin.state = action.get("next_state", "idle")
            twin.current_task = action.get("task")

        # 应用状态变化到仿真环境
        state_changes = self._apply_actions(sim_state, agent_actions)

        step.agent_actions = agent_actions
        step.messages = messages
        step.step_rewards = step_rewards
        step.state_changes = state_changes
        step.global_reward = sum(step_rewards.values()) / max(len(step_rewards), 1)

        return step

    # ── 闭环注入 ────────────────────────────────────────────────

    async def inject_strategy(self, session_id: str) -> Dict[str, Any]:
        """将最优策略注入真实环境.

        只有沙箱验证通过的策略才会被同步回真实的数字执行层。
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "session_not_found"}
        if session.status not in (SandboxStatus.EVALUATING, SandboxStatus.COMPLETED):
            return {"error": f"invalid_status: {session.status.value}"}

        if not session.best_sop:
            return {"error": "no_validated_strategy"}

        # 标记注入
        session.status = SandboxStatus.INJECTING
        session.best_sop.status = StrategyStatus.INJECTED
        session.injected = True
        session.injection_time = datetime.now(timezone.utc).isoformat()
        session.status = SandboxStatus.COMPLETED

        # 固化经验到长期记忆
        for twin in session.twins:
            memory = self._memory_pool.get_or_create(twin.source_agent_id)
            memory.consolidate()
            memory.save()

        logger.info(f"💉 策略注入完成: session={session_id[:8]} sop={session.best_sop.name}")
        return {
            "injected": True,
            "sop_id": session.best_sop.sop_id,
            "sop_name": session.best_sop.name,
            "injection_time": session.injection_time,
        }

    # ── 辅助方法 ────────────────────────────────────────────────

    def _spawn_twins(self, snapshot: WorldStateSnapshot) -> List[AgentTwin]:
        """从世界快照生成孪生智能体."""
        twins = []
        for agent_id, state in snapshot.agent_states.items():
            twin = AgentTwin(
                source_agent_id=agent_id,
                role=state.get("role", "general"),
                skills=state.get("skills", []),
                state="idle",
                current_task=state.get("current_task"),
                strategy_params={},
            )
            twins.append(twin)
        return twins

    def _default_decision(
        self, twin: AgentTwin, world: WorldStateSnapshot, all_twins: List[AgentTwin]
    ) -> Dict[str, Any]:
        """默认决策函数 — 基于规则的简单策略.

        后续可替换为 LLM 驱动的决策。
        """
        # 基础规则引擎
        if twin.current_task:
            return {
                "action": "work_on_task",
                "task": twin.current_task,
                "next_state": "working",
                "message": None,
            }

        # 查找可认领的任务
        available_tasks = [
            t for t in world.pending_tasks
            if t.get("assigned_to") is None and twin.role in t.get("required_roles", [twin.role])
        ]

        if available_tasks:
            task = available_tasks[0]
            return {
                "action": "claim_task",
                "task": task.get("id", "unknown"),
                "next_state": "working",
                "message": f"认领任务: {task.get('title', 'unknown')}",
                "message_type": "claim",
                "target": "broadcast",
            }

        # 协助其他智能体
        busy_twins = [t for t in all_twins if t.state == "working" and t.twin_id != twin.twin_id]
        if busy_twins:
            return {
                "action": "offer_help",
                "next_state": "waiting",
                "message": f"可协助: {busy_twins[0].role}",
                "target": busy_twins[0].twin_id,
            }

        return {"action": "idle", "next_state": "idle", "message": None}

    def _calculate_reward(
        self, twin: AgentTwin, action: Dict[str, Any], world: WorldStateSnapshot
    ) -> float:
        """计算单步奖励."""
        reward = 0.0
        action_type = action.get("action", "idle")

        if action_type == "work_on_task":
            reward += 0.3
        elif action_type == "claim_task":
            reward += 0.2
        elif action_type == "offer_help":
            reward += 0.1
        elif action_type == "idle":
            reward -= 0.05

        # 通信奖励
        if action.get("message"):
            reward += 0.05

        return reward

    def _apply_actions(
        self, sim_state: WorldStateSnapshot, actions: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """应用动作到仿真状态，返回状态变化."""
        changes = []
        for twin_id, action in actions.items():
            if action.get("action") == "claim_task":
                task_id = action.get("task")
                for task in sim_state.pending_tasks:
                    if task.get("id") == task_id:
                        task["assigned_to"] = twin_id
                        changes.append({"type": "task_assigned", "task": task_id, "agent": twin_id})
                        break
        return changes

    def _check_convergence(self, session: SandboxSession, step: SimulationStep) -> bool:
        """检查仿真是否收敛."""
        # 所有任务已分配且无空闲智能体
        idle_count = sum(1 for t in session.twins if t.state == "idle")
        if idle_count == 0 and step.global_reward > 0.2:
            return True
        # 连续低奖励则提前停止
        if len(session.steps) > 10:
            recent_rewards = [s.global_reward for s in session.steps[-5:]]
            if all(r < 0.01 for r in recent_rewards):
                return True
        return False

    def _check_convergence_from_steps(self, steps: List[SimulationStep]) -> bool:
        """从步骤列表判断收敛."""
        if len(steps) > 10:
            recent = [s.global_reward for s in steps[-5:]]
            if all(r < 0.01 for r in recent):
                return True
        return False

    def _generate_strategy_variants(self, count: int) -> List[Dict[str, Any]]:
        """生成策略变体用于并行对比."""
        variants = []
        base_strategies = [
            {"collaboration_weight": 0.8, "exploration_rate": 0.2, "name": "collaborative"},
            {"collaboration_weight": 0.3, "exploration_rate": 0.7, "name": "explorative"},
            {"collaboration_weight": 0.5, "exploration_rate": 0.5, "name": "balanced"},
            {"collaboration_weight": 0.9, "exploration_rate": 0.1, "name": "conservative"},
            {"collaboration_weight": 0.1, "exploration_rate": 0.9, "name": "aggressive"},
        ]
        for i in range(min(count, len(base_strategies))):
            variants.append(base_strategies[i])
        return variants

    # ── 事件注册 ────────────────────────────────────────────────

    def on_step(self, callback: Callable) -> None:
        """注册仿真步骤回调."""
        self._step_callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """获取引擎全局统计."""
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": sum(
                1 for s in self._sessions.values() if s.status == SandboxStatus.RUNNING
            ),
            "completed_sessions": sum(
                1 for s in self._sessions.values() if s.status == SandboxStatus.COMPLETED
            ),
            "total_steps": sum(s.total_steps_executed for s in self._sessions.values()),
        }
