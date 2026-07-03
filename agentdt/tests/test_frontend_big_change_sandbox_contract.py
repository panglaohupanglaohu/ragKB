# -*- coding: utf-8 -*-
"""frontendBigChange sandbox contract checks.

These tests cover the machine-verifiable part of the F1/F5 "20-step
sandbox-twin rehearsal": the backend must produce step data rich enough for
the frontend collaboration graph to stay populated.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


@pytest.mark.asyncio
async def test_sandbox_twenty_steps_emit_collab_graph_contract():
    from sandbox.models import SimulationMode
    from sandbox.twin_loop import TwinLoopEngine
    from sandbox.world_state import WorldStateManager
    from sandbox.memory_system import MemoryPool

    wsm = WorldStateManager()
    wsm.sync_agents_from_team({
        "agents": [
            {"id": "planner", "role": "planner", "skills": ["planning", "coordination"]},
            {"id": "retriever", "role": "retriever", "skills": ["search", "kb"]},
            {"id": "coordinator", "role": "coordinator", "skills": ["coordination"]},
            {"id": "executor", "role": "executor", "skills": ["coding", "testing"]},
            {"id": "critic", "role": "critic", "skills": ["review", "evaluation"]},
        ]
    })
    wsm.sync_tasks([
        {
            "id": "task_api",
            "title": "实现 API",
            "required_roles": ["executor"],
            "required_skills": ["coding"],
        },
        {
            "id": "task_review",
            "title": "评审与回归",
            "required_roles": ["critic"],
            "required_skills": ["review"],
        },
    ])

    engine = TwinLoopEngine(wsm, MemoryPool())
    session = engine.create_session(
        team_id="frontend-big-change",
        mode=SimulationMode.WHAT_IF,
        max_steps=20,
        speed_factor=10000.0,
    )

    result = await engine.run_simulation(session.session_id)

    assert result.total_steps_executed == 20
    assert len(result.steps) == 20
    assert len(result.twins) == 5

    role_map = {t.source_agent_id: t.role for t in result.twins}
    assert {"planner", "retriever", "coordinator", "executor", "critic"} <= set(role_map)

    actionable_steps = [step for step in result.steps if step.agent_actions]
    assert len(actionable_steps) == 20

    sse_like_events = []
    for step in result.steps:
        event = {
            "type": "step",
            "step_id": step.step_id,
            "global_reward": step.global_reward,
            "agent_actions": {
                k: v.get("action", "unknown")
                for k, v in step.agent_actions.items()
                if isinstance(v, dict)
            },
            "messages_count": len(step.messages),
            "agent_roles": role_map,
        }
        sse_like_events.append(event)

    assert all(event["agent_roles"] for event in sse_like_events)
    assert all(len(event["agent_actions"]) >= 5 for event in sse_like_events)
    assert sum(event["messages_count"] for event in sse_like_events) > 0
