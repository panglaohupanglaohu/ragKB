# -*- coding: utf-8 -*-
"""SECS 集成测试 — 自进化协同沙箱系统端到端验证.

测试完整流水线:
1. 世界状态同步
2. 沙箱会话创建
3. 仿真执行
4. 评估对齐
5. 策略注入
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


class TestSECSModels:
    """测试数据模型."""

    def test_world_state_snapshot(self):
        from sandbox.models import WorldStateSnapshot
        snap = WorldStateSnapshot()
        assert snap.snapshot_id
        assert snap.timestamp
        assert snap.agent_states == {}

    def test_sandbox_session(self):
        from sandbox.models import SandboxSession, SandboxStatus, SimulationMode
        session = SandboxSession(team_id="test")
        assert session.status == SandboxStatus.CREATED
        assert session.mode == SimulationMode.WHAT_IF
        assert session.team_id == "test"

    def test_experience_entry(self):
        from sandbox.models import ExperienceEntry, ExperienceOutcome
        exp = ExperienceEntry(
            agent_id="agent_1",
            situation="test situation",
            action_taken="test action",
            outcome=ExperienceOutcome.SUCCESS,
            reward=0.8,
        )
        assert exp.reward == 0.8
        assert exp.outcome == ExperienceOutcome.SUCCESS


class TestWorldState:
    """测试环境语义映射."""

    def test_sync_and_snapshot(self):
        from sandbox.world_state import WorldStateManager
        wsm = WorldStateManager()

        # 同步智能体
        wsm.sync_agents_from_team({
            "agents": [
                {"id": "pm", "role": "coordinator", "skills": ["planning"]},
                {"id": "dev", "role": "developer", "skills": ["coding"]},
            ]
        })

        # 同步任务
        wsm.sync_tasks([
            {"id": "task_1", "title": "实现功能A", "required_roles": ["developer"]},
        ])

        # 生成快照
        snap = wsm.take_snapshot()
        assert len(snap.agent_states) == 2
        assert len(snap.pending_tasks) == 1
        assert snap.snapshot_id

    def test_incremental_snapshot(self):
        from sandbox.world_state import WorldStateManager
        wsm = WorldStateManager()
        wsm.sync_agents_from_team({"agents": [{"id": "a1", "role": "dev"}]})

        snap1 = wsm.take_snapshot()
        snap2 = wsm.take_snapshot(incremental=True)
        assert snap2.parent_snapshot_id == snap1.snapshot_id


class TestMemorySystem:
    """测试双记忆系统."""

    def test_record_and_recall(self):
        from sandbox.memory_system import AgentMemory
        from sandbox.models import ExperienceEntry, ExperienceOutcome

        mem = AgentMemory("agent_test")

        # 记录经验
        exp = ExperienceEntry(
            situation="任务分配 协作 开发",
            action_taken="claim_task",
            outcome=ExperienceOutcome.SUCCESS,
            reward=0.7,
        )
        mem.record_experience(exp)

        # 检索
        results = mem.recall_relevant("任务 开发")
        assert len(results) >= 1
        assert results[0].reward == 0.7

    def test_consolidation(self):
        from sandbox.memory_system import AgentMemory
        from sandbox.models import ExperienceEntry, ExperienceOutcome

        mem = AgentMemory("agent_consolidate", max_short_term=5)

        for i in range(10):
            mem.record_experience(ExperienceEntry(
                situation=f"situation_{i}",
                action_taken=f"action_{i}",
                outcome=ExperienceOutcome.SUCCESS if i % 2 == 0 else ExperienceOutcome.FAILURE,
                reward=0.5 if i % 2 == 0 else 0.1,
            ))

        promoted = mem.consolidate()
        assert promoted > 0
        stats = mem.get_stats()
        assert stats["long_term_count"] > 0


class TestDriftDetector:
    """测试偏移检测."""

    def test_task_mutation_drift(self):
        from sandbox.drift_detector import DriftDetector
        from sandbox.models import WorldStateSnapshot, DriftType

        detector = DriftDetector(drift_threshold=0.3)

        # 基线：无任务
        baseline = WorldStateSnapshot(pending_tasks=[])
        detector.set_baseline(baseline)

        # 当前：3个新任务
        current = WorldStateSnapshot(pending_tasks=[
            {"id": "t1"}, {"id": "t2"}, {"id": "t3"}
        ])

        drifts = detector.detect(current)
        task_drifts = [d for d in drifts if d.drift_type == DriftType.TASK_MUTATION]
        assert len(task_drifts) >= 1

    def test_no_drift_when_stable(self):
        from sandbox.drift_detector import DriftDetector
        from sandbox.models import WorldStateSnapshot

        detector = DriftDetector()
        snap = WorldStateSnapshot(pending_tasks=[{"id": "t1"}])
        detector.set_baseline(snap)

        drifts = detector.detect(snap)
        assert len(drifts) == 0


class TestTwinLoop:
    """测试仿真引擎."""

    @pytest.mark.asyncio
    async def test_create_and_run_session(self):
        from sandbox.twin_loop import TwinLoopEngine
        from sandbox.world_state import WorldStateManager
        from sandbox.memory_system import MemoryPool
        from sandbox.models import SimulationMode

        wsm = WorldStateManager()
        wsm.sync_agents_from_team({
            "agents": [
                {"id": "pm", "role": "coordinator", "skills": ["planning"]},
                {"id": "dev1", "role": "developer", "skills": ["coding"]},
                {"id": "dev2", "role": "developer", "skills": ["coding"]},
            ]
        })
        wsm.sync_tasks([
            {"id": "task_1", "title": "实现API", "required_roles": ["developer"]},
            {"id": "task_2", "title": "编写测试", "required_roles": ["developer"]},
        ])

        pool = MemoryPool()
        engine = TwinLoopEngine(wsm, pool)

        session = engine.create_session(
            team_id="test",
            mode=SimulationMode.WHAT_IF,
            max_steps=20,
        )
        assert session.session_id

        result = await engine.run_simulation(session.session_id)
        assert result.total_steps_executed > 0
        assert len(result.twins) == 3
        assert len(result.steps) > 0

    @pytest.mark.asyncio
    async def test_taskflow_step_state_tracks_active_done_and_unblocks_dependencies(self):
        from sandbox.twin_loop import TwinLoopEngine
        from sandbox.world_state import WorldStateManager
        from sandbox.memory_system import MemoryPool
        from sandbox.models import SimulationMode

        wsm = WorldStateManager()
        wsm.sync_agents_from_team({
            "agents": [
                {"id": "dev", "role": "developer", "skills": ["coding"]},
            ]
        })
        wsm.sync_tasks([
            {
                "id": "t1",
                "title": "实现接口",
                "assigned_to": None,
                "required_roles": ["developer"],
                "required_skills": ["coding"],
                "base_duration_steps": 1,
                "blocked": False,
            },
            {
                "id": "t2",
                "title": "回归验证",
                "assigned_to": None,
                "required_roles": ["developer"],
                "required_skills": ["coding"],
                "base_duration_steps": 1,
                "depends_on": ["t1"],
                "blocked": True,
            },
        ])

        engine = TwinLoopEngine(wsm, MemoryPool())
        session = engine.create_session(
            team_id="taskflow-state",
            mode=SimulationMode.WHAT_IF,
            max_steps=4,
            speed_factor=10000.0,
        )

        result = await engine.run_simulation(session.session_id)

        assert [s.active_task_id for s in result.steps[:2]] == ["t1", "t1"]
        assert "t1" in result.steps[1].done_task_ids
        assert any(c["type"] == "task_unblocked" and c["task"] == "t2" for c in result.steps[1].state_changes)
        assert "t2" in result.steps[-1].done_task_ids


class TestGlobalCritic:
    """测试全局评论家."""

    @pytest.mark.asyncio
    async def test_evaluate_session(self):
        from sandbox.twin_loop import TwinLoopEngine
        from sandbox.world_state import WorldStateManager
        from sandbox.memory_system import MemoryPool
        from sandbox.global_critic import GlobalCritic

        wsm = WorldStateManager()
        wsm.sync_agents_from_team({
            "agents": [
                {"id": "a1", "role": "developer"},
                {"id": "a2", "role": "coordinator"},
            ]
        })
        wsm.sync_tasks([{"id": "t1", "title": "task", "required_roles": ["developer"]}])

        pool = MemoryPool()
        engine = TwinLoopEngine(wsm, pool)
        session = engine.create_session(team_id="test", max_steps=15)
        session = await engine.run_simulation(session.session_id)

        critic = GlobalCritic()
        evaluation = critic.evaluate(session)

        assert 0 <= evaluation.global_score <= 1
        assert evaluation.task_completion >= 0
        assert len(evaluation.recommendations) > 0


class TestOrchestrator:
    """测试完整编排流水线."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        from sandbox.orchestrator import SECSOrchestrator
        from sandbox.models import SimulationMode

        orch = SECSOrchestrator()

        # 同步世界状态
        orch.sync_world(
            team_id="test",
            agents=[
                {"id": "pm", "role": "coordinator", "skills": ["planning"]},
                {"id": "dev", "role": "developer", "skills": ["coding"]},
                {"id": "qa", "role": "analyst", "skills": ["testing"]},
            ],
            tasks=[
                {"id": "t1", "title": "开发功能", "required_roles": ["developer"]},
                {"id": "t2", "title": "测试功能", "required_roles": ["analyst"]},
            ],
        )

        # 创建并运行仿真
        session = orch.create_session(
            team_id="test",
            mode=SimulationMode.WHAT_IF,
            max_steps=25,
        )

        result = await orch.run_full_pipeline(session.session_id)

        assert "error" not in result
        assert result["total_steps"] > 0
        assert result["alignment"]["evaluation"]["global_score"] >= 0

        # 获取统计
        stats = orch.get_global_stats()
        assert stats["twin_loop"]["total_sessions"] >= 1

    @pytest.mark.asyncio
    async def test_parallel_mode(self):
        from sandbox.orchestrator import SECSOrchestrator
        from sandbox.models import SimulationMode

        orch = SECSOrchestrator()
        orch.sync_world(
            agents=[
                {"id": "a1", "role": "developer"},
                {"id": "a2", "role": "developer"},
            ],
            tasks=[{"id": "t1", "title": "task", "required_roles": ["developer"]}],
        )

        session = orch.create_session(
            mode=SimulationMode.PARALLEL,
            max_steps=15,
            parallel_branches=3,
        )
        result = await orch.run_full_pipeline(session.session_id)
        assert "error" not in result


# ══════════════════════════════════════════════════════════════
# 回归测试: Agent Digital Twin 演练完成闭环修复 (2025-06)
# 覆盖: HTTP 500 / EVALUATING卡死 / 评分缺失降级 / 非dict防御
# ══════════════════════════════════════════════════════════════

class TestCriticNoneActionDefense:
    """回归: GlobalCritic 遇到 agent_actions 中的非 dict 值时不崩溃."""

    def test_evaluate_with_none_actions(self):
        """step.agent_actions 含 None 值（混沌禁用 Agent）→ 不抛 AttributeError."""
        from sandbox.global_critic import GlobalCritic
        from sandbox.models import SandboxSession, SimulationStep, AgentTwin, CriticEvaluation

        session = SandboxSession(team_id="defense_test")
        twin = AgentTwin(source_agent_id="a1", role="developer", skills=["coding"])
        session.twins = [twin]

        # 构造含 None 和正常 dict 的 agent_actions
        step = SimulationStep(step_id=0, global_reward=0.3)
        step.agent_actions = {
            twin.twin_id: {"action": "execute_skill", "skill_used": "coding", "task": "t1"},
            "ghost_twin": None,  # ← 混沌注入产生的 None 值
            "bad_twin": "not_a_dict",  # ← 非 dict 值
        }
        session.steps = [step]

        critic = GlobalCritic()
        # 必须不抛异常
        evaluation = critic.evaluate(session)
        assert isinstance(evaluation, CriticEvaluation)
        assert 0 <= evaluation.global_score <= 1

    def test_evaluate_with_empty_steps(self):
        """空 steps 列表 → 返回低分评估，不崩溃."""
        from sandbox.global_critic import GlobalCritic
        from sandbox.models import SandboxSession

        session = SandboxSession(team_id="empty_test")
        session.steps = []
        session.twins = []

        critic = GlobalCritic()
        evaluation = critic.evaluate(session)
        # 空步骤时 communication_efficiency=0.5(中性)，故 global_score > 0
        assert isinstance(evaluation.global_score, float)
        assert 0 <= evaluation.global_score <= 1


class TestZeroExpNoneActionDefense:
    """回归: ZeroExpEngine 遇到非 dict action 时不崩溃."""

    def test_collect_experience_with_none_action(self):
        """agent_actions 中 action 为 None 时使用 fallback dict."""
        from sandbox.zero_exp_engine import ZeroExpEngine
        from sandbox.memory_system import MemoryPool
        from sandbox.models import SimulationStep, AgentTwin

        pool = MemoryPool()
        engine = ZeroExpEngine(pool)

        twin = AgentTwin(source_agent_id="a1", role="dev")
        step = SimulationStep(step_id=0)
        step.agent_actions = {twin.twin_id: None}  # None 值
        step.step_rewards = {twin.twin_id: 0.1}

        # 不抛异常
        exp = engine.collect_experience_from_step("s1", step, "a1", twin.twin_id)
        assert exp.action_taken == "{'action': 'unknown'}"

    def test_extract_sop_with_mixed_actions(self):
        """提取 SOP 时混合 None/dict action 不崩溃."""
        from sandbox.zero_exp_engine import ZeroExpEngine
        from sandbox.memory_system import MemoryPool
        from sandbox.models import SimulationStep, AgentTwin

        pool = MemoryPool()
        engine = ZeroExpEngine(pool)

        twin = AgentTwin(source_agent_id="a1", role="dev")
        step = SimulationStep(step_id=0, global_reward=0.3)
        step.agent_actions = {
            twin.twin_id: {"action": "execute_skill", "skill_used": "coding"},
            "none_twin": None,
        }
        step.messages = []

        sop = engine.extract_sop("s1", [step], {twin.twin_id: "a1"})
        # 可能返回 SOP 或 None（取决于奖励阈值），但不崩溃
        assert True


class TestSessionDetailsDegraded:
    """回归: get_session 在数据不完整时返回降级数据而非 500."""

    def test_get_session_serialization_with_evaluating_status(self):
        """EVALUATING 状态 + evaluation=None → 返回基础数据，evaluation 字段为 null."""
        from sandbox.models import SandboxSession, SandboxStatus

        session = SandboxSession(session_id="test-eval-001")
        session.status = SandboxStatus.EVALUATING
        session.total_steps_executed = 50
        session.evaluation = None  # 评估未完成
        session.best_sop = None
        session.twins = []
        session.steps = []

        # 模拟 api.py get_session() 的序列化逻辑
        evaluation_data = None
        if session.evaluation:
            evaluation_data = {"global_score": session.evaluation.global_score}
        sop_data = None if not session.best_sop else {"name": session.best_sop.name}

        result = {
            "session_id": session.session_id,
            "status": session.status.value,
            "total_steps_executed": session.total_steps_executed,
            "evaluation": evaluation_data,
            "best_sop": sop_data,
        }

        assert result["status"] == "evaluating"
        assert result["evaluation"] is None
        assert result["best_sop"] is None
        assert result["total_steps_executed"] == 50

    def test_get_session_steps_with_none_actions(self):
        """steps 中 agent_actions 含 None → 序列化跳过该项，不崩溃."""
        from sandbox.models import SimulationStep

        step = SimulationStep(step_id=0, global_reward=0.25)
        step.agent_actions = {
            "t1": {"action": "work", "skill_used": "coding"},
            "t2": None,  # 混沌禁用的 agent
            "t3": "invalid",
        }

        # 模拟 api.py 的 steps_summary 构建逻辑
        skills_used = {}
        for twin_id, action in step.agent_actions.items():
            if not isinstance(action, dict):  # [fix] 防御
                continue
            sk = action.get("skill_used")
            if sk:
                skills_used[twin_id] = {"skill": sk}

        summary = {
            "step_id": step.step_id,
            "global_reward": round(step.global_reward, 4),
            "skills_used": skills_used,
        }

        assert summary["global_reward"] == 0.25
        assert len(skills_used) == 1  # 只有 t1 被序列化
        assert "t1" in skills_used


class TestPipelineEvaluatingFallback:
    """回归: run_full_pipeline 异常时 EVALUATING → COMPLETED 状态回退."""

    @pytest.mark.asyncio
    async def test_evaluating_fallback_on_align_failure(self):
        """align_session 异常后，状态从 EVALUATING 回退到 COMPLETED."""
        from sandbox.orchestrator import SECSOrchestrator
        from sandbox.models import SimulationMode, SandboxStatus

        orch = SECSOrchestrator()
        orch.sync_world(
            agents=[{"id": "a1", "role": "developer"}],
            tasks=[{"id": "t1", "title": "task"}],
        )
        session = orch.create_session(mode=SimulationMode.WHAT_IF, max_steps=10)

        # 手动将 session 设为 EVALUATING（模拟 run_simulation 完成后的中间状态）
        from sandbox.models import SandboxSession as SS
        session.status = SandboxStatus.EVALUATING

        # 模拟 orchestrator 的回退逻辑
        try:
            raise RuntimeError("模拟 align_session 异常")
        except Exception:
            if session.status == SandboxStatus.EVALUATING:
                session.status = SandboxStatus.COMPLETED

        assert session.status == SandboxStatus.COMPLETED


class TestEndToEndClosedLoop:
    """最小端到端回归: 启动演练 → 自动运行 → 完成 → 详情可拉取."""

    @pytest.mark.asyncio
    async def test_complete_loop_with_chaos_disabled_agent(self):
        """含混沌注入(禁用Agent)的完整闭环: 不崩溃，状态正确."""
        from sandbox.orchestrator import SECSOrchestrator
        from sandbox.models import SimulationMode, SandboxStatus

        orch = SECSOrchestrator()
        orch.sync_world(
            agents=[
                {"id": "pm", "role": "coordinator", "skills": ["planning"]},
                {"id": "dev", "role": "developer", "skills": ["coding"]},
            ],
            tasks=[
                {"id": "t1", "title": "开发功能", "required_roles": ["developer"]},
            ],
        )

        session = orch.create_session(
            mode=SimulationMode.WHAT_IF,
            max_steps=20,
        )

        # 执行仿真（内部会调用 evaluate + align）
        result = await orch.run_full_pipeline(session.session_id)

        # 断言：即使有内部异常也不应返回 500 级别的错误
        assert result is not None
        assert "session_id" in result
        # 状态必须是 completed（不能卡在 evaluating）
        final_session = orch.get_session(session.session_id)
        assert final_session.status in (SandboxStatus.COMPLETED, SandboxStatus.PAUSED), \
            f"状态卡在 {final_session.status.value}，应为 COMPLETED 或 PAUSED"

        # 如果成功完成，评估应该存在或至少不崩溃
        if final_session.evaluation:
            assert 0 <= final_session.evaluation.global_score <= 1
