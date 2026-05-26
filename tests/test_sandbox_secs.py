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
