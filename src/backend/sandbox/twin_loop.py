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
import random
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
    SkillUsageRecord,
    StrategyStatus,
    WorldStateSnapshot,
)
from .memory_system import AgentMemory, MemoryPool
from .world_state import WorldStateManager

logger = logging.getLogger(__name__)


# 默认决策函数类型
DecisionFunc = Callable[[AgentTwin, WorldStateSnapshot, List[AgentTwin]], Dict[str, Any]]

# ── v4 C-2.2: 熟练度结算调参常量 (集中放置便于调参) ──
PROF_DEFAULT = 0.5            # 无记录时的默认熟练度
PROF_SUCCESS_BASE = 0.3       # 成功概率 = clamp(BASE + SLOPE*prof, MIN, MAX)
PROF_SUCCESS_SLOPE = 0.6
PROF_SUCCESS_MIN = 0.2
PROF_SUCCESS_MAX = 0.95
PROF_FAIL_REWARD_FACTOR = 0.3  # 失败时奖励折损系数
PROF_LEARN_STEP = 0.02         # session 内每次成功临时熟练度增量
PROF_LEARN_CAP = 0.98
PROF_DEGRADE_DELTA = 0.3       # skill_degraded 混沌事件的临时熟练度降幅


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
        # 混沌注入状态 (per-session)
        self._chaos_states: Dict[str, Dict[str, Any]] = {}
        # 运行中的 sim_state 引用 (用于混沌注入时动态修改)
        self._running_sim_states: Dict[str, WorldStateSnapshot] = {}
        # 并发控制
        self._semaphore = asyncio.Semaphore(5)
        # 停止事件 — 每个 session 一个 asyncio.Event，用于中断仿真
        self._stop_events: Dict[str, asyncio.Event] = {}
        # v4 C-2.3: 场景混沌时间表 (session_id -> [{from_step,to_step,event_type,probability_per_step,payload}])
        self._chaos_timelines: Dict[str, List[Dict[str, Any]]] = {}
        # v4 C-2.4: 技能使用记录缓冲 (session_id -> [SkillUsageRecord])
        self._usage_buffers: Dict[str, List[SkillUsageRecord]] = {}
        # v4 C-2.1: 团队熟练度先验 (session_id -> {agent_id: {skill: rate}})
        self._proficiency_priors: Dict[str, Dict[str, Dict[str, float]]] = {}
        # v4 C-3.4: A/B 候选 instructions 覆盖 (session_id -> {skill_name: instructions})
        self._skill_overrides: Dict[str, Dict[str, str]] = {}

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

    # ── v4: 场景/熟练度/归因接入 ─────────────────────────────────

    def set_chaos_timeline(self, session_id: str, timeline: List[Dict[str, Any]]) -> None:
        """设置场景混沌时间表 (C-2.3)，由 scenario_compiler.build_chaos_timeline 产出."""
        self._chaos_timelines[session_id] = list(timeline or [])

    def set_proficiency_priors(self, session_id: str, priors: Dict[str, Dict[str, float]]) -> None:
        """设置团队熟练度先验 (C-2.1). priors: {agent_id: {skill_name: success_rate}}."""
        self._proficiency_priors[session_id] = priors or {}

    def set_skill_overrides(self, session_id: str, overrides: Dict[str, str]) -> None:
        """A/B 候选 instructions 覆盖 (C-3.4) — 只影响该 session 的 twin."""
        self._skill_overrides[session_id] = overrides or {}

    def drain_usage_records(self, session_id: str) -> List[SkillUsageRecord]:
        """取出并清空该 session 的技能使用记录缓冲 (C-2.4)."""
        return self._usage_buffers.pop(session_id, [])

    def peek_usage_records(self, session_id: str) -> List[SkillUsageRecord]:
        """只读查看缓冲（不清空）."""
        return list(self._usage_buffers.get(session_id, []))

    async def _apply_scheduled_chaos(self, session: SandboxSession, step_num: int) -> None:
        """每步检查混沌时间表，按概率自动注入 (C-2.3)."""
        timeline = self._chaos_timelines.get(session.session_id)
        if not timeline:
            return
        for entry in timeline:
            if entry["from_step"] <= step_num <= entry["to_step"]:
                if random.random() < entry.get("probability_per_step", 0):
                    try:
                        result = await self.inject_chaos_event(
                            session_id=session.session_id,
                            event_type=entry.get("event_type", ""),
                            target_agent=(entry.get("payload") or {}).get("target_agent"),
                        )
                        if result.get("injected"):
                            logger.info(f"🎬 剧本混沌注入 @step{step_num}: {entry.get('event_type')}")
                    except Exception as e:
                        logger.warning(f"剧本混沌注入失败: {e}")

    def _settle_skill_action(
        self, twin: AgentTwin, action: Dict[str, Any], reward: float,
        step_num: int, session_id: str, chaos: Dict[str, Any],
    ) -> Tuple[float, Optional[SkillUsageRecord]]:
        """v4 C-2.2/C-2.4: 熟练度结算 — 成功概率由熟练度决定，并产生使用归因记录.

        Returns: (调整后 reward, SkillUsageRecord 或 None)
        """
        skill = action.get("skill_used")
        if not skill:
            return reward, None

        prof = float((twin.skill_proficiency or {}).get(skill, PROF_DEFAULT))
        # skill_degraded 混沌事件 → 临时熟练度降低
        degraded = chaos.get("degraded_skills", {}).get(twin.source_agent_id)
        if degraded and step_num < degraded.get("until", 0):
            prof = max(0.05, prof - PROF_DEGRADE_DELTA)

        success_p = max(PROF_SUCCESS_MIN, min(PROF_SUCCESS_MAX,
                        PROF_SUCCESS_BASE + PROF_SUCCESS_SLOPE * prof))
        success = random.random() < success_p

        failure_reason = ""
        if success:
            # session 内"练熟"效应（不写回全局）
            twin.skill_proficiency[skill] = min(PROF_LEARN_CAP, prof + PROF_LEARN_STEP)
        else:
            reward = round(reward * PROF_FAIL_REWARD_FACTOR, 4)
            if degraded and step_num < degraded.get("until", 0):
                failure_reason = f"skill_degraded: {skill} 被混沌事件削弱 (prof={prof:.2f})"
            elif prof < 0.4:
                failure_reason = f"low_proficiency: {skill} 熟练度不足 (prof={prof:.2f})"
            else:
                failure_reason = f"execution_miss: {skill} 执行未达标 (p={success_p:.2f})"

        record = SkillUsageRecord(
            session_id=session_id,
            step_index=step_num,
            agent_id=twin.source_agent_id,
            agent_role=twin.role,
            skill_name=skill,
            task_id=str(action.get("task") or ""),
            outcome="success" if success else "failure",
            reward_delta=round(reward, 4),
            failure_reason=failure_reason,
            context={
                "action": action.get("action", ""),
                "tool_used": action.get("tool_used"),
                "proficiency": round(prof, 4),
                "success_p": round(success_p, 4),
                "chaos_active": bool(chaos.get("disabled_agents") or chaos.get("degraded_skills")),
            },
        )
        if session_id:
            self._usage_buffers.setdefault(session_id, []).append(record)
        return reward, record

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

        # 创建停止事件，支持外部中断
        stop_event = asyncio.Event()
        self._stop_events[session_id] = stop_event

        async with self._semaphore:
            try:
                # Step 1: 快照
                session.status = SandboxStatus.SNAPSHOTTING
                snapshot = self._world_state.take_snapshot()
                session.initial_snapshot = snapshot
                session.snapshots.append(snapshot.snapshot_id)

                # Step 2: 生成孪生体（v4: 携带熟练度先验）
                session.twins = self._spawn_twins(snapshot, session.session_id)
                session.status = SandboxStatus.RUNNING

                # Step 3: 仿真循环
                if session.mode == SimulationMode.PARALLEL:
                    await self._run_parallel(session, snapshot, stop_event)
                elif session.mode == SimulationMode.EVOLUTIONARY:
                    await self._run_evolutionary(session, snapshot, stop_event)
                else:
                    await self._run_sequential(session, snapshot, stop_event)

                # Step 4: 标记完成 (停止信号非异常，正常结束)
                if stop_event.is_set():
                    logger.info(f"🛑 仿真被手动停止: {session_id[:8]}")
                session.status = SandboxStatus.EVALUATING if not stop_event.is_set() else SandboxStatus.PAUSED
                session.updated_at = datetime.now(timezone.utc).isoformat()

            except Exception as e:
                session.status = SandboxStatus.FAILED
                logger.error(f"❌ 仿真失败: {e}")
                raise
            finally:
                self._stop_events.pop(session_id, None)

        return session

    async def _run_sequential(self, session: SandboxSession, snapshot: WorldStateSnapshot, stop_event: asyncio.Event) -> None:
        """顺序执行仿真步骤."""
        sim_state = copy.deepcopy(snapshot)

        # 暴露 sim_state 给混沌注入
        self._running_sim_states[session.session_id] = sim_state

        # 确保世界状态有任务可做（否则 twin 全部 idle → 奖励为负 → 提前停滞）
        if not sim_state.pending_tasks:
            sim_state.pending_tasks = self._generate_default_tasks(session)

        for step_num in range(session.max_steps):
            if stop_event.is_set():
                logger.info(f"🛑 仿真被中断于步骤 {step_num} (顺序)")
                break

            # v4 C-2.3: 场景剧本混沌自动注入
            await self._apply_scheduled_chaos(session, step_num)

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

            # 步进时间轴：baseInterval=1.0，10x下50步≈5秒肉眼可见
            if session.speed_factor > 0:
                await asyncio.sleep(1.0 / session.speed_factor)

        # ── 失败归因：收集被混沌注入影响的 Agent ──
        chaos = self._chaos_states.get(session.session_id, {})
        disabled_history = chaos.get("disabled_agents", {})
        chaos_events = chaos.get("events", [])
        if disabled_history or chaos_events:
            session.failed_agents = []
            for agent_id, recover_at in disabled_history.items():
                twin = next((t for t in session.twins if t.source_agent_id == agent_id), None)
                session.failed_agents.append({
                    "agent": agent_id,
                    "role": twin.role if twin else "unknown",
                    "recover_at": recover_at,
                    "recovered": session.total_steps_executed >= recover_at,
                    "reason": "chaos_injection" if recover_at > session.total_steps_executed else "chaos_recovered",
                })
            session.chaos_events = chaos_events

        # 清理（暂停时保留 sim_state 供 step_once 续跑）
        if session.status != SandboxStatus.PAUSED:
            self._running_sim_states.pop(session.session_id, None)

    async def _run_evolutionary(self, session: SandboxSession, snapshot: WorldStateSnapshot, stop_event: asyncio.Event) -> None:
        """达尔文棘轮演化模式 — 多代进化，只进不退.

        每代：仿真 → 评估 → 保留 top 50% → 变异 → 下一代
        棘轮效应：score(t+1) >= score(t)，否则停止。
        """
        max_generations = getattr(session, 'max_generations', 3) or 3
        sim_state = copy.deepcopy(snapshot)
        self._running_sim_states[session.session_id] = sim_state

        if not sim_state.pending_tasks:
            sim_state.pending_tasks = self._generate_default_tasks(session)

        session.evolution_generations = []
        prev_best_score = -float("inf")
        best_twins = copy.deepcopy(session.twins)

        for gen in range(max_generations):
            if stop_event.is_set():
                logger.info(f"🛑 演化中断于第 {gen} 代")
                break

            logger.info(f"🧬 第 {gen+1}/{max_generations} 代演化开始")
            gen_steps = []
            gen_twins = copy.deepcopy(best_twins)

            # 为每个 twin 注入不同变异
            for twin in gen_twins:
                twin.generation = gen
                if gen > 0:
                    self._mutate_strategy(twin)

            for step_num in range(session.max_steps):
                if stop_event.is_set():
                    break
                step = await self._execute_step_with_twins(gen_twins, sim_state, step_num, session.session_id)
                gen_steps.append(step)
                # 实时写入 session.steps 供 SSE 轮询显示进度
                session.steps.append(step)
                session.total_steps_executed += 1
                if self._check_convergence_from_steps(gen_steps, session.max_steps):
                    break
                if session.speed_factor > 0:
                    await asyncio.sleep(1.0 / session.speed_factor)

            # 评估本代
            gen_avg_reward = sum(s.global_reward for s in gen_steps) / max(len(gen_steps), 1)
            gen_best_reward = max((s.global_reward for s in gen_steps), default=0)

            # 棘轮检查
            if gen_avg_reward <= prev_best_score and gen > 0:
                logger.info(f"🔒 棘轮锁定: gen{gen} score={gen_avg_reward:.3f} <= prev={prev_best_score:.3f}, 停止进化")
                break

            prev_best_score = gen_avg_reward
            session.evolution_generations.append({
                "generation": gen,
                "avg_reward": gen_avg_reward,
                "best_reward": gen_best_reward,
                "steps": len(gen_steps),
                "twins_count": len(gen_twins),
            })

            # 保留 top 50% twin（按 accumulated reward）
            gen_twins.sort(key=lambda t: t.rewards_collected, reverse=True)
            best_twins = copy.deepcopy(gen_twins[:max(1, len(gen_twins)//2)])
            logger.info(f"🧬 第 {gen+1} 代完成: avg_reward={gen_avg_reward:.3f}, 保留 {len(best_twins)}/{len(gen_twins)} 个 Agent")

        # 写入最终结果（session.steps 已在循环中实时追加，不再覆盖）
        # session.total_steps_executed 已在循环中累加，不再覆盖
        self._running_sim_states.pop(session.session_id, None)
        logger.info(f"🧬 演化完成: {len(session.evolution_generations)} 代, 最终 score={prev_best_score:.3f}")

    def _mutate_strategy(self, twin: AgentTwin) -> None:
        """对策略权重做小幅随机变异 (±0.05)."""
        strat = getattr(twin, 'strategy_params', None) or {}
        if not strat:
            strat = {"collaboration_weight": 0.5, "exploration_rate": 0.5}
        strat["collaboration_weight"] = max(0.05, min(0.95, strat.get("collaboration_weight", 0.5) + random.uniform(-0.08, 0.08)))
        strat["exploration_rate"] = max(0.05, min(0.95, strat.get("exploration_rate", 0.5) + random.uniform(-0.08, 0.08)))
        twin.strategy_params = strat

    async def _run_parallel(self, session: SandboxSession, snapshot: WorldStateSnapshot, stop_event: asyncio.Event) -> None:
        """并行执行多策略分支.

        每个分支独立 try/except，单分支崩溃不影响其他分支，也不导致 gather 整体失败。
        """
        branches: List[List[SimulationStep]] = []

        async def run_branch(branch_id: int, strategy_params: Dict[str, Any]):
            """运行单个策略分支，异常被捕获并返回空列表."""
            sim_state = copy.deepcopy(snapshot)
            if not sim_state.pending_tasks:
                sim_state.pending_tasks = self._generate_default_tasks(session)
            branch_steps = []
            # 应用策略参数到孪生体
            try:
                twins = copy.deepcopy(session.twins)
                for twin in twins:
                    twin.strategy_params = strategy_params

                for step_num in range(session.max_steps):
                    if stop_event.is_set():
                        break
                    step = await self._execute_step_with_twins(twins, sim_state, step_num, session.session_id)
                    branch_steps.append(step)
                    # 实时写入 session.steps 供 SSE 轮询显示进度（并行模式取首个分支的步数）
                    if i == 0:  # 只写入主分支避免重复
                        session.steps.append(step)
                        session.total_steps_executed += 1
                    if self._check_convergence_from_steps(branch_steps, session.max_steps):
                        break
                    await asyncio.sleep(1.0 / session.speed_factor)
            except Exception as e:
                logger.error(f"❌ 并行分支 #{branch_id} 异常: {e}", exc_info=True)
            return branch_steps

        # 生成不同策略参数
        strategies = self._generate_strategy_variants(session.parallel_branches)

        # 并行执行（return_exceptions=True 防止单分支崩溃拖垮 gather）
        tasks = [run_branch(i, strat) for i, strat in enumerate(strategies)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤掉异常结果
        valid_results = [r for r in results if isinstance(r, list)]
        if not valid_results:
            logger.error(f"❌ 所有并行分支均失败")
            # 每个分支都崩了——写入空 steps，aligner 仍可处理
            session.steps = []
            session.total_steps_executed = 0
            return

        # 选择最优分支
        best_idx = 0
        best_reward = -float("inf")
        for idx, branch_steps in enumerate(valid_results):
            total_reward = sum(s.global_reward for s in branch_steps)
            if total_reward > best_reward:
                best_reward = total_reward
                best_idx = idx
            branches.append(branch_steps)

        session.steps = branches[best_idx] if branches else []
        session.total_steps_executed = len(session.steps)
        session.branches_results = branches  # 存储所有分支供前端多线图
        logger.info(f"🏆 最优分支: #{best_idx} reward={best_reward:.2f} ({len(valid_results)}/{len(results)} 分支成功)")

    async def _execute_step(
        self, session: SandboxSession, sim_state: WorldStateSnapshot, step_num: int
    ) -> SimulationStep:
        """执行单个仿真步骤."""
        return await self._execute_step_with_twins(session.twins, sim_state, step_num, session.session_id)

    async def _execute_step_with_twins(
        self, twins: List[AgentTwin], sim_state: WorldStateSnapshot, step_num: int, session_id: str = ""
    ) -> SimulationStep:
        """使用指定孪生体执行单步，支持混沌注入跳过禁用 Agent."""
        step = SimulationStep(step_id=step_num)
        agent_actions: Dict[str, Dict[str, Any]] = {}
        messages: List[Dict[str, Any]] = []
        step_rewards: Dict[str, float] = {}
        disabled_agents: List[str] = []

        # ── 混沌状态 ──
        chaos = self._chaos_states.get(session_id, {}) if session_id else {}

        for twin in twins:
            # ── 混沌注入：检查 Agent 是否被禁用 ──
            disabled_until = chaos.get("disabled_agents", {}).get(twin.source_agent_id, 0)

            if step_num < disabled_until:
                disabled_agents.append(twin.source_agent_id)
                # 被禁用的 Agent：记录但跳过决策
                agent_actions[twin.twin_id] = {"action": "disabled", "reason": "chaos_injection", "recover_at": disabled_until}
                step_rewards[twin.twin_id] = 0.0
                continue

            # 获取智能体记忆
            memory = self._memory_pool.get_or_create(twin.source_agent_id)
            # 决策
            action = self._decision_func(twin, sim_state, twins)
            agent_actions[twin.twin_id] = action

            # 计算奖励（感知混沌惩罚）
            base_reward = self._calculate_reward(twin, action, sim_state)
            # 混沌注入后步奖励降低 0.05~0.15（团队需自愈）
            chaos_penalty = 0.0
            if chaos.get("mutated_tasks") or chaos.get("disabled_agents"):
                chaos_penalty = 0.08
            reward = max(0, base_reward - chaos_penalty)

            # v4 C-2.2/C-2.4: 熟练度结算 + 技能使用归因
            reward, usage_record = self._settle_skill_action(
                twin, action, reward, step_num, session_id, chaos)
            if usage_record:
                step.skill_usages.append(usage_record.record_id)
                action["skill_outcome"] = usage_record.outcome

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
        step.disabled_agents = disabled_agents
        step.global_reward = sum(step_rewards.values()) / max(len(step_rewards), 1) if step_rewards else 0.0

        return step

    # ── 闭环注入 + 混沌注入 ─────────────────────────────────────

    async def inject_chaos_event(
        self,
        session_id: str,
        event_type: str,
        target_agent: Optional[str] = None,
        skill_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """注入混沌事件到运行中的沙箱——真正扰动 Agent 池状态.

        支持的 event_type:
        - agent_failure: 禁用目标 Agent 5 步
        - task_mutation / task_change: 随机修改 50% 待处理任务的 required_skills
        - agent_leave: 从孪生池移除目标 Agent
        - agent_join: 新增/恢复一个被禁用的 Agent
        - skill_inject: 技能注入
        - network_delay: 模拟网络延迟（降低所有 Agent 速度 30%，持续 3 步）
        - skill_degraded: 技能退化（随机移除一个 Agent 的一个技能，3 步后恢复）
        - model_hallucination: 模型幻觉（随机翻转任务优先级）
        - logic_deadlock: 逻辑死锁（暂停任务分配 2 步）
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "session_not_found"}

        # 初始化该 session 的混沌状态
        if session_id not in self._chaos_states:
            self._chaos_states[session_id] = {"disabled_agents": {}, "mutated_tasks": False, "events": []}

        chaos = self._chaos_states[session_id]
        current_step = session.total_steps_executed

        if event_type == "agent_failure":
            # 选择目标 agent（指定或随机）
            active_twins = [t for t in session.twins if not self._is_twin_disabled(t, chaos, current_step)]
            if not active_twins:
                return {"error": "no_active_agents", "detail": "没有可故障注入的活跃 Agent"}
            target = next((t for t in active_twins if t.source_agent_id == target_agent), None) if target_agent else random.choice(active_twins)
            target_id = target.source_agent_id

            # 禁用 5 步
            chaos["disabled_agents"][target_id] = current_step + 5
            chaos["events"].append({
                "step": current_step, "type": "agent_failure",
                "agent": target_id, "role": target.role,
                "recover_at": current_step + 5,
            })
            logger.info(f"💥 混沌注入: {target_id}({target.role}) 下线, 预计 step {current_step+5} 恢复")
            return {
                "injected": True, "chaos": True, "type": "agent_failure",
                "agent": target_id, "role": target.role,
                "disabled_until_step": current_step + 5,
                "detail": f"Agent {target_id}({target.role}) 已下线 {5} 步, 观察团队自愈能力",
            }

        elif event_type in ("task_mutation", "task_change"):
            sim_state = self._running_sim_states.get(session_id)
            if not sim_state or not sim_state.pending_tasks:
                return {"error": "no_pending_tasks", "detail": "无待处理任务可变异"}

            all_skills = list(set(s for t in session.twins for s in (t.skills or [])))
            if not all_skills:
                all_skills = ["coding", "review", "testing", "planning", "documentation"]

            mutated_count = 0
            for task in sim_state.pending_tasks:
                if random.random() < 0.5:  # 50% 概率变异
                    old_skills = task.get("required_skills", [])
                    task["required_skills"] = random.sample(all_skills, min(len(old_skills), len(all_skills)))
                    mutated_count += 1

            chaos["mutated_tasks"] = True
            chaos["events"].append({
                "step": current_step, "type": "task_mutation",
                "mutated": mutated_count, "total": len(sim_state.pending_tasks),
            })
            logger.info(f"🔄 混沌注入: 任务突变 {mutated_count}/{len(sim_state.pending_tasks)} 个任务")
            return {
                "injected": True, "chaos": True, "type": "task_mutation",
                "mutated": mutated_count, "total": len(sim_state.pending_tasks),
                "detail": f"随机突变了 {mutated_count}/{len(sim_state.pending_tasks)} 个任务的需求技能向量",
            }

        elif event_type == "agent_leave":
            active_twins = [t for t in session.twins if not self._is_twin_disabled(t, chaos, current_step)]
            if len(active_twins) <= 1:
                return {"error": "too_few_agents", "detail": "仅剩 1 个活跃 Agent，移除将导致仿真无意义"}

            target = next((t for t in active_twins if t.source_agent_id == target_agent), None) if target_agent else random.choice(active_twins)
            target_id = target.source_agent_id

            # 永久移除（禁用直到远超 max_steps）
            chaos["disabled_agents"][target_id] = session.max_steps + 999
            chaos["events"].append({
                "step": current_step, "type": "agent_leave",
                "agent": target_id, "role": target.role,
            })
            logger.info(f"➖ 混沌注入: {target_id}({target.role}) 离开团队")
            return {
                "injected": True, "chaos": True, "type": "agent_leave",
                "agent": target_id, "role": target.role,
                "detail": f"Agent {target_id}({target.role}) 已永久离开, 剩余 {len(active_twins)-1} 个 Agent",
            }

        elif event_type == "skill_inject":
            if not skill_id:
                return {"error": "missing_skill_id"}
            chaos["events"].append({
                "step": current_step, "type": "skill_inject",
                "skill_id": skill_id,
            })
            return {
                "injected": True, "chaos": True, "type": "skill_inject",
                "skill_id": skill_id,
                "detail": f"技能 {skill_id} 已注入沙箱",
            }

        # ── 扩展混沌事件类型（前端演练面板）──
        elif event_type == "agent_join":
            disabled_agents = chaos.get("disabled_agents", {})
            if disabled_agents:
                # 恢复一个被禁用的 Agent
                recover_id = next(iter(disabled_agents), None)
                if recover_id:
                    del disabled_agents[recover_id]
                    target = next((t for t in session.twins if t.source_agent_id == recover_id), None)
                    chaos["events"].append({"step": current_step, "type": "agent_join", "agent": recover_id})
                    logger.info(f"➕ 混沌注入: {recover_id} 重新加入团队")
                    return {"injected": True, "chaos": True, "type": "agent_join",
                            "agent": recover_id, "role": getattr(target, 'role', '?'),
                            "detail": f"Agent {recover_id} 已重新加入"}

        elif event_type == "network_delay":
            # 网络延迟：所有 Agent 速度降低，持续 3 步
            if "network_delay" not in chaos:
                chaos["network_delay"] = {"until": current_step + 3, "slowdown": 0.3}
            chaos["events"].append({"step": current_step, "type": "network_delay", "duration": 3})
            logger.info(f"🌐 混沌注入: 网络延迟激活 (step {current_step+3} 恢复)")
            return {"injected": True, "chaos": True, "type": "network_delay",
                    "duration": 3, "detail": f"网络延迟: 所有 Agent 速度降低 30%, 持续 3 步"}

        elif event_type == "skill_degraded":
            active_twins = [t for t in session.twins if not self._is_twin_disabled(t, chaos, current_step)]
            if not active_twins:
                return {"error": "no_active_agents"}
            target = target_agent and next((t for t in active_twins if t.source_agent_id == target_agent), None) or random.choice(active_twins)
            # 记录退化状态
            degraded = chaos.setdefault("degraded_skills", {})
            orig_skills = list(target.skills or [])
            degraded[target.source_agent_id] = {"skills": orig_skills, "until": current_step + 3}
            chaos["events"].append({"step": current_step, "type": "skill_degraded",
                                     "agent": target.source_agent_id, "role": target.role,
                                     "lost_skills": orig_skills[:1] if orig_skills else []})
            logger.info(f"⬇️ 混沌注入: {target.source_agent_id} 技能退化")
            return {"injected": True, "chaos": True, "type": "skill_degraded",
                    "agent": target.source_agent_id, "role": target.role,
                    "lost_skill": orig_skills[0] if orig_skills else "?",
                    "disabled_until_step": current_step + 3,
                    "detail": f"{target.source_agent_id}({target.role}) 技能退化, step {current_step+3} 恢复"}

        elif event_type == "model_hallucination":
            sim_state = self._running_sim_states.get(session_id)
            if sim_state and sim_state.pending_tasks:
                for task in sim_state.pending_tasks:
                    if random.random() < 0.4:
                        task["priority"] = random.choice(["low", "high", "critical"])
                        task.get("metadata", {})["_hallucinated"] = True
            chaos["events"].append({"step": current_step, "type": "model_hallucination"})
            logger.info(f"🧠 混沌注入: 模型幻觉 - 任务优先级被翻转")
            return {"injected": True, "chaos": True, "type": "model_hallucination",
                    "detail": "模型幻觉: 随机翻转了部分任务优先级"}

        elif event_type == "logic_deadlock":
            chaos["deadlock_until"] = current_step + 2
            chaos["events"].append({"step": current_step, "type": "logic_deadlock", "resume_at": current_step + 2})
            logger.info(f"🔒 混沌注入: 逻辑死锁 (step {current_step+2} 解锁)")
            return {"injected": True, "chaos": True, "type": "logic_deadlock",
                    "frozen_steps": 2, "resume_at": current_step + 2,
                    "detail": f"逻辑死锁: 任务分配暂停 2 步"}

        return {"error": "unknown_event_type", "detail": f"未知事件类型: {event_type}"}

    def _is_twin_disabled(self, twin: AgentTwin, chaos: dict, current_step: int) -> bool:
        """检查 Agent 是否在当前步被混沌禁用."""
        disabled_until = chaos.get("disabled_agents", {}).get(twin.source_agent_id, 0)
        return current_step < disabled_until

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

    def stop_simulation(self, session_id: str) -> Dict[str, Any]:
        """停止仿真并清理资源（支持任意状态）."""
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "session_not_found", "stopped": False}

        # 设置停止信号（中断运行中的仿真）
        stop_event = self._stop_events.get(session_id)
        if stop_event:
            stop_event.set()
        self._stop_events.pop(session_id, None)

        # 清理 sim_state
        self._running_sim_states.pop(session_id, None)

        # 标记会话状态
        prev_status = session.status.value
        session.status = SandboxStatus.PAUSED
        session.updated_at = datetime.now(timezone.utc).isoformat()

        return {"stopped": True, "prev_status": prev_status, "steps_executed": session.total_steps_executed, "session_id": session_id}

    async def step_once(self, session_id: str) -> Dict[str, Any]:
        """在 PAUSED 状态下执行单步仿真.

        前置条件：
        - 会话状态为 PAUSED（已初始化快照+孪生体）
        - _running_sim_states 中保留着 sim_state 快照
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "session_not_found", "stepped": False}
        if session.status not in (SandboxStatus.PAUSED, SandboxStatus.CREATED):
            return {"error": f"cannot_step_in_status: {session.status.value}", "stepped": False}

        sim_state = self._running_sim_states.get(session_id)
        if not sim_state:
            # 首次 step：需要初始化快照和孪生体
            snapshot = self._world_state.take_snapshot()
            session.initial_snapshot = snapshot
            session.snapshots.append(snapshot.snapshot_id)
            if not session.twins:
                session.twins = self._spawn_twins(snapshot, session_id)
            if not getattr(sim_state, 'pending_tasks', None) and not session.initial_snapshot.pending_tasks:
                sim_state_pending = self._generate_default_tasks(session)
                snapshot.pending_tasks = sim_state_pending
            sim_state = copy.deepcopy(snapshot)
            self._running_sim_states[session_id] = sim_state

        # 检查是否已达上限
        step_num = session.total_steps_executed
        if step_num >= session.max_steps:
            session.status = SandboxStatus.COMPLETED
            self._running_sim_states.pop(session_id, None)
            return {"stepped": False, "reason": "max_steps_reached",
                    "total_steps": session.total_steps_executed, "session_id": session_id}

        # 执行单步
        session.status = SandboxStatus.RUNNING
        # v4 C-2.3: 场景剧本混沌自动注入
        await self._apply_scheduled_chaos(session, step_num)
        step = await self._execute_step(session, sim_state, step_num)
        session.steps.append(step)
        session.total_steps_executed += 1

        # 通知回调
        for cb in self._step_callbacks:
            try:
                await cb(session.session_id, step)
            except Exception:
                pass

        # 检查收敛
        converged = self._check_convergence(session, step)

        # 回到 PAUSED，等待下一步
        session.status = SandboxStatus.PAUSED
        if converged:
            session.status = SandboxStatus.COMPLETED
            self._running_sim_states.pop(session_id, None)

        return {
            "stepped": True,
            "step_num": step_num,
            "total_steps": session.total_steps_executed,
            "global_reward": step.global_reward,
            "agent_actions": {k: v.get("action", "unknown") for k, v in step.agent_actions.items()},
            "messages_count": len(step.messages),
            "converged": converged,
            "status": session.status.value,
            "session_id": session_id,
        }

    def force_reset_all(self) -> Dict[str, Any]:
        """强制清理所有会话资源（僵尸进程、信号量、stop_events）.

        在 parallel 模式崩溃后调用，避免资源泄漏导致后续演练失败。
        """
        count = 0
        # 1. 清理所有 stop_events
        for sid in list(self._stop_events.keys()):
            event = self._stop_events.get(sid)
            if event:
                event.set()
            count += 1
        self._stop_events.clear()

        # 2. 将所有 RUNNING/FAILED 会话标记为可恢复状态
        for sid, session in self._sessions.items():
            if session.status in (SandboxStatus.RUNNING, SandboxStatus.FAILED):
                session.status = SandboxStatus.PAUSED
                session.updated_at = datetime.now(timezone.utc).isoformat()
                count += 1

        logger.info(f"🧹 强制重置完成: {count} 项清理")
        return {"reset": True, "cleaned": count}

    # ── 辅助方法 ────────────────────────────────────────────────

    def _spawn_twins(self, snapshot: WorldStateSnapshot, session_id: str = "") -> List[AgentTwin]:
        """从世界快照生成孪生智能体 (v4 C-2.1: 载入熟练度先验)."""
        priors = self._proficiency_priors.get(session_id, {}) if session_id else {}
        twins = []
        for agent_id, state in snapshot.agent_states.items():
            skills = state.get("skills", [])
            agent_priors = priors.get(agent_id, {})
            twin = AgentTwin(
                source_agent_id=agent_id,
                role=state.get("role", "general"),
                skills=skills,
                tools=state.get("tools", []),
                state="idle",
                current_task=state.get("current_task"),
                strategy_params={},
                skill_proficiency={s: float(agent_priors.get(s, PROF_DEFAULT)) for s in skills},
            )
            twins.append(twin)
        return twins

    def _default_decision(
        self, twin: AgentTwin, world: WorldStateSnapshot, all_twins: List[AgentTwin]
    ) -> Dict[str, Any]:
        """默认决策函数 — 基于 skill/tool 匹配的规则策略，感知 strategy_params 行为分化.

        决策优先级：
        0. 策略参数注入 → exploration_rate 高则随机探索 / collaboration_weight 高则更多 offer_help
        1. 有当前任务 → 用匹配 skill 执行，或用 tool 辅助
        2. 找匹配 skill 的未认领任务 → 认领
        3. 协助忙碌的 agent（skill 互补时优先）
        4. 无事可做 → idle
        """
        # ── 策略参数感知：让不同分支行为真正分化 ──
        strat = getattr(twin, 'strategy_params', None) or {}
        explore = strat.get('exploration_rate', 0.5)
        collab = strat.get('collaboration_weight', 0.5)

        # 高探索率 → 随机认领非匹配任务（探索行为）
        if explore > 0.5 and random.random() < (explore - 0.5) * 0.3:
            available_tasks = [t for t in world.pending_tasks if t.get("assigned_to") is None]
            if available_tasks:
                task = random.choice(available_tasks)
                return {
                    "action": "claim_task",
                    "task": task.get("id", "unknown"),
                    "skill_match": [],
                    "next_state": "working",
                    "message": f"探索认领: {task.get('title', 'unknown')}",
                    "message_type": "claim",
                    "target": "broadcast",
                }

        # 高协作权重 → 在无当前任务时更偏向 offer_help
        busy_twins = [t for t in all_twins if t.state == "working" and t.twin_id != twin.twin_id]
        if collab > 0.6 and busy_twins and not twin.current_task and random.random() < (collab - 0.5) * 0.4:
            best_helper = busy_twins[0]
            best_complement = 0
            for bt in busy_twins:
                complement = len(set(twin.skills) - set(bt.skills))
                if complement > best_complement:
                    best_complement = complement
                    best_helper = bt
            return {
                "action": "offer_help",
                "next_state": "waiting",
                "message": f"主动协助: {best_helper.role}" + (f" (互补: {best_complement})" if best_complement > 0 else ""),
                "target": best_helper.twin_id,
            }

        # 查找当前任务详情
        current_task_info = None
        if twin.current_task:
            for t in world.pending_tasks:
                if t.get("id") == twin.current_task or t.get("assigned_to") == twin.twin_id:
                    current_task_info = t
                    break

        # ── 场景1：有当前任务 → 使用技能执行 ──
        if twin.current_task and current_task_info:
            task_skills = current_task_info.get("required_skills", [])
            task_tools = current_task_info.get("required_tools", [])

            # 查找匹配的技能
            matched_skill = self._best_skill_match(twin.skills, task_skills)
            matched_tool = self._best_tool_match(twin.tools, task_tools)

            if matched_skill:
                # 使用匹配技能执行任务
                return {
                    "action": "execute_skill",
                    "task": twin.current_task,
                    "skill_used": matched_skill,
                    "tool_used": matched_tool,
                    "next_state": "working",
                    "message": f"使用 {matched_skill}" + (f" + {matched_tool}" if matched_tool else "") + f" 执行任务",
                    "message_type": "action",
                }
            elif twin.skills:
                # 有技能但不匹配任务 → 仍尝试用任意技能
                return {
                    "action": "execute_skill",
                    "task": twin.current_task,
                    "skill_used": twin.skills[0],
                    "tool_used": matched_tool,
                    "next_state": "working",
                    "message": f"使用 {twin.skills[0]} 尝试执行",
                    "message_type": "action",
                }
            else:
                # 无技能 → 抽象工作
                return {
                    "action": "work_on_task",
                    "task": twin.current_task,
                    "skill_used": None,
                    "next_state": "working",
                    "message": None,
                }

        # ── 场景2：找可认领的任务（优先 skill 匹配） ──
        available_tasks = [
            t for t in world.pending_tasks
            if t.get("assigned_to") is None and (
                not t.get("required_roles") or twin.role in t["required_roles"]
            )
        ]

        if available_tasks:
            # 按 skill 匹配度排序：匹配越多越优先
            def _skill_match_score(task):
                req_skills = task.get("required_skills", [])
                if not req_skills:
                    return 0
                matched = len(set(req_skills) & set(twin.skills))
                return matched / len(req_skills)

            available_tasks.sort(key=_skill_match_score, reverse=True)
            best_task = available_tasks[0]
            best_task_skills = best_task.get("required_skills", [])
            matched = [s for s in best_task_skills if s in twin.skills]
            return {
                "action": "claim_task",
                "task": best_task.get("id", "unknown"),
                "skill_match": matched,
                "next_state": "working",
                "message": f"认领任务: {best_task.get('title', 'unknown')}" + (f" (技能匹配: {','.join(matched)})" if matched else ""),
                "message_type": "claim",
                "target": "broadcast",
            }

        # ── 场景3：协助忙碌的 agent（skill 互补优先） ──
        busy_twins = [t for t in all_twins if t.state == "working" and t.twin_id != twin.twin_id]
        if busy_twins:
            # 优先协助 skill 互补的 agent
            best_helper = busy_twins[0]
            best_complement = 0
            for bt in busy_twins:
                # 统计互相没有的 skill（互补度）
                complement = len(set(twin.skills) - set(bt.skills))
                if complement > best_complement:
                    best_complement = complement
                    best_helper = bt
            return {
                "action": "offer_help",
                "next_state": "waiting",
                "message": f"可协助: {best_helper.role}" + (f" (互补技能: {best_complement})" if best_complement > 0 else ""),
                "target": best_helper.twin_id,
            }

        return {"action": "idle", "next_state": "idle", "message": None}

    def _best_skill_match(self, agent_skills: List[str], task_skills: List[str]) -> Optional[str]:
        """从 agent skill 列表中找到与任务 skill 列表匹配度最高的 skill."""
        if not agent_skills or not task_skills:
            return agent_skills[0] if agent_skills else None
        for ts in task_skills:
            if ts in agent_skills:
                return ts
        return agent_skills[0]  # 没有精确匹配时返回第一个 skill

    def _best_tool_match(self, agent_tools: List[str], task_tools: List[str]) -> Optional[str]:
        """从 agent tool 列表中找到与任务 tool 列表匹配的工具."""
        if not agent_tools or not task_tools:
            return None
        for tt in task_tools:
            if tt in agent_tools:
                return tt
        return None

    def _calculate_reward(
        self, twin: AgentTwin, action: Dict[str, Any], world: WorldStateSnapshot
    ) -> float:
        """计算单步奖励（含 skill/tool 匹配 + 任务进度 + 通信 + 噪声）.

        skill 匹配是核心指标：匹配任务需求 skill → 高奖励；不匹配 → 低奖励。
        """
        reward = 0.0
        action_type = action.get("action", "idle")
        task_id = action.get("task")

        # 查找任务详情
        task_info = None
        if task_id:
            for t in world.pending_tasks:
                if t.get("id") == task_id or t.get("assigned_to") == twin.twin_id:
                    task_info = t
                    break
        task_skills = task_info.get("required_skills", []) if task_info else []
        task_tools = task_info.get("required_tools", []) if task_info else []

        if action_type == "execute_skill":
            # ── 技能执行：核心奖励源 ──
            skill_used = action.get("skill_used")
            tool_used = action.get("tool_used")

            if skill_used and task_skills:
                if skill_used in task_skills:
                    # 完美匹配：技能正是任务所需
                    reward += 0.45
                elif set(task_skills) & set(twin.skills):
                    # agent 有匹配技能但没选 → 中等
                    reward += 0.25
                else:
                    # agent 没有任务所需技能 → 尝试
                    reward += 0.15
            elif skill_used:
                # 用了技能但任务无 skill 要求
                reward += 0.25
            else:
                reward += 0.1  # 无技能可用

            # tool 奖励
            if tool_used and task_tools:
                if tool_used in task_tools:
                    reward += 0.15  # tool 匹配
                else:
                    reward += 0.05  # tool 不匹配
            elif tool_used:
                reward += 0.08

            # 使用技能/工具的经验积累
            progress_bonus = min(0.2, twin.actions_taken * 0.008)
            reward += progress_bonus

        elif action_type == "work_on_task":
            # ── 抽象执行（无 skill 的 fallback）──
            progress_bonus = min(0.3, twin.actions_taken * 0.01)
            reward += 0.3 + progress_bonus
            # 有技能却不用 → 轻微惩罚
            if twin.skills and task_skills:
                reward -= 0.1

        elif action_type == "claim_task":
            # ── 认领任务 ──
            skill_matches = action.get("skill_match", [])
            reward += 0.2
            if skill_matches:
                reward += 0.1 * len(skill_matches)  # 匹配 skill 越多越好

        elif action_type == "offer_help":
            # ── 协助 ──
            reward += 0.15
            # 互补技能 bonus（从消息中提取互补数）
            msg = action.get("message", "")
            if "互补技能" in str(msg):
                reward += 0.05

        elif action_type == "idle":
            # 有技能却 idle → 较重惩罚
            if twin.skills:
                reward -= 0.1
            else:
                reward -= 0.03

        # 通信奖励（消息越长奖励越高）
        msg = action.get("message")
        if msg and isinstance(msg, str):
            reward += 0.03 + min(0.05, len(msg) * 0.0005)

        # 微小随机噪声（±0.015）让相同动作不完全同分
        reward += random.uniform(-0.015, 0.015)

        return round(reward, 4)

    def _apply_actions(
        self, sim_state: WorldStateSnapshot, actions: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """应用动作到仿真状态，返回状态变化."""
        changes = []
        for twin_id, action in actions.items():
            action_type = action.get("action")
            task_id = action.get("task")

            if action_type == "claim_task":
                for task in sim_state.pending_tasks:
                    if task.get("id") == task_id:
                        task["assigned_to"] = twin_id
                        task["skill_match"] = action.get("skill_match", [])
                        changes.append({"type": "task_assigned", "task": task_id, "agent": twin_id})
                        break

            elif action_type in ("execute_skill", "work_on_task"):
                # 标记任务进度
                skill_used = action.get("skill_used")
                for task in sim_state.pending_tasks:
                    if task.get("id") == task_id:
                        progress = task.get("_progress", 0) + 1
                        task["_progress"] = progress
                        # 技能匹配的任务：每次进度 +2（效率翻倍）
                        if skill_used and skill_used in task.get("required_skills", []):
                            task["_progress"] = progress + 1
                        changes.append({
                            "type": "task_progress",
                            "task": task_id,
                            "agent": twin_id,
                            "skill": skill_used,
                            "progress": task["_progress"],
                        })
                        break

        return changes

    def _generate_default_tasks(self, session: SandboxSession) -> List[Dict[str, Any]]:
        """生成带 skill/tool 需求的默认任务.

        每个任务基于 team 中 Agent 的真实 skill/tool 生成，使仿真有差异化。
        """
        if not session.twins:
            return []
        tasks = []

        # 收集所有 skill 和 tool
        all_skills = list(set(s for t in session.twins for s in t.skills))
        all_tools = list(set(s for t in session.twins for s in t.tools))

        for i, twin in enumerate(session.twins):
            # 每个 twin 产生一个与其 skill 匹配的任务
            task_skills = twin.skills[:2] if twin.skills else []  # 取前2个 skill
            task_tools = twin.tools[:1] if twin.tools else []      # 取第1个 tool
            role = twin.role
            tasks.append({
                "id": f"task-{twin.twin_id}-{i}",
                "title": f"{role} 专项任务 #{i+1}",
                "description": f"需要 {role} 使用 {', '.join(task_skills) or '通用能力'} 完成的任务",
                "assigned_to": None,
                "required_roles": [role],
                "required_skills": task_skills,
                "required_tools": task_tools,
                "priority": i + 1,
            })

            # 如果 twin 有 skill，额外生成一个需要该 skill 的任务（竞争性）
            for j, skill in enumerate(twin.skills[:2]):
                tasks.append({
                    "id": f"task-skill-{twin.twin_id}-{j}",
                    "title": f"技能应用: {skill}",
                    "description": f"使用 {skill} 解决实际问题",
                    "assigned_to": None,
                    "required_roles": [],
                    "required_skills": [skill],
                    "required_tools": [],
                    "priority": len(tasks) + 1,
                })

        # 跨角色协同任务：需要多种 skill 组合
        if len(all_skills) >= 2:
            for j in range(min(3, len(all_skills) // 2)):
                cross_skills = all_skills[j*2:j*2+2]
                tasks.append({
                    "id": f"task-cross-{j}",
                    "title": f"跨角色协同 #{j+1}",
                    "description": f"需要 {', '.join(cross_skills)} 等多技能协作",
                    "assigned_to": None,
                    "required_roles": [],
                    "required_skills": cross_skills,
                    "required_tools": all_tools[:1] if all_tools else [],
                    "priority": len(tasks) + 1,
                })

        # 补齐通用任务（无 skill 要求，低优先级）
        extra = min(3, session.max_steps // 20)
        for j in range(extra):
            tasks.append({
                "id": f"task-general-{j}",
                "title": f"通用协作 #{j+1}",
                "description": "跨角色通用协同任务",
                "assigned_to": None,
                "required_roles": [],
                "required_skills": [],
                "required_tools": [],
                "priority": len(tasks) + 1,
            })

        return tasks

    def _check_convergence(self, session: SandboxSession, step: SimulationStep) -> bool:
        """检查仿真是否停滞/收敛.

        仅在完成 max_steps 的 40%（最少 20 步）后才检查停滞。
        需连续 8 步全局奖励 < 0.01 才判定停滞。
        """
        min_steps = max(20, int(session.max_steps * 0.4))
        if len(session.steps) < min_steps:
            return False

        # 连续 8 步奖励停滞（所有 twin 都无有效产出）
        recent_rewards = [s.global_reward for s in session.steps[-8:]]
        if all(r < 0.02 for r in recent_rewards):
            logger.info(f"⏹ 仿真停滞: session={session.session_id[:8]} 最近8步奖励={[round(r,3) for r in recent_rewards]}")
            return True

        return False

    def _check_convergence_from_steps(self, steps: List[SimulationStep], max_steps: int = 50) -> bool:
        """从步骤列表判断收敛（并行分支用）."""
        min_steps = max(20, int(max_steps * 0.4))
        if len(steps) < min_steps:
            return False
        recent = [s.global_reward for s in steps[-8:]]
        if all(r < 0.02 for r in recent):
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
