# -*- coding: utf-8 -*-
"""全局 G-3 技能路由试炼测试 — routing_strategy 策略化决策."""

import asyncio
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def _make_engine(routing: str, priors=None, seed: int = 7, max_steps: int = 30):
    from sandbox.twin_loop import TwinLoopEngine
    from sandbox.memory_system import MemoryPool
    from sandbox.world_state import WorldStateManager
    from sandbox.models import SimulationMode

    random.seed(seed)
    ws = WorldStateManager()
    # a1 同时会两个 skill，但 fast_skill 熟练度高、slow_skill 熟练度低
    ws.sync_agent_state("a1", {"role": "dev", "state": "idle",
                               "skills": ["fast_skill", "slow_skill"], "tools": []})
    # 注意: t-slow 故意放在首位 — 无策略时稳定排序会先认领它，
    # proficiency_first/cost_aware 应跳过它选择 t-fast（这就是策略差异）
    tasks = [
        {"id": "t-slow", "title": "低熟练度任务", "assigned_to": None, "required_roles": [],
         "required_skills": ["slow_skill"], "required_tools": [], "priority": 1,
         "base_duration_steps": 8},
        {"id": "t-fast", "title": "高熟练度任务", "assigned_to": None, "required_roles": [],
         "required_skills": ["fast_skill"], "required_tools": [], "priority": 2,
         "base_duration_steps": 2},
    ]
    ws.sync_tasks(tasks)
    engine = TwinLoopEngine(ws, MemoryPool())
    session = engine.create_session(team_id="teamA", mode=SimulationMode.WHAT_IF,
                                    max_steps=max_steps, speed_factor=10000.0)
    session.routing_strategy = routing
    engine.set_proficiency_priors(session.session_id, {
        "a1": priors or {"fast_skill": 0.95, "slow_skill": 0.1},
    })
    return engine, session


def _first_claimed_task(session):
    for step in session.steps:
        for action in step.agent_actions.values():
            if action.get("action") == "claim_task":
                return action.get("task")
    return None


def test_session_carries_routing_strategy_to_twins():
    engine, session = _make_engine("proficiency_first", max_steps=5)
    asyncio.run(engine.run_simulation(session.session_id))
    assert all(t.strategy_params.get("routing_strategy") == "proficiency_first"
               for t in session.twins)


def test_proficiency_first_prefers_high_proficiency_task():
    engine, session = _make_engine("proficiency_first", max_steps=10)
    asyncio.run(engine.run_simulation(session.session_id))
    assert _first_claimed_task(session) == "t-fast"


def test_cost_aware_prefers_short_high_yield_task():
    engine, session = _make_engine("cost_aware", max_steps=10)
    asyncio.run(engine.run_simulation(session.session_id))
    # fast_skill: prof 0.95 / dur 2 = 0.475 vs slow: 0.1/8 → 选 t-fast
    assert _first_claimed_task(session) == "t-fast"


def test_strategies_produce_divergent_choices():
    """同一世界，不同策略 → 任务选择/收益可分化（路由对照的意义所在）."""
    rewards = {}
    for strategy in ("proficiency_first", "round_robin", ""):
        engine, session = _make_engine(strategy, seed=7, max_steps=20)
        asyncio.run(engine.run_simulation(session.session_id))
        rewards[strategy] = round(sum(s.global_reward for s in session.steps), 4)
    # 至少有策略间产生差异（保护性弱断言，避免随机碰撞）
    assert len(set(rewards.values())) >= 2, rewards


def test_round_robin_is_deterministic():
    a = []
    for _ in range(2):
        engine, session = _make_engine("round_robin", seed=7, max_steps=10)
        asyncio.run(engine.run_simulation(session.session_id))
        a.append(_first_claimed_task(session))
    assert a[0] == a[1]  # crc32 打散是确定性的


def test_empty_strategy_keeps_legacy_behavior():
    engine, session = _make_engine("", max_steps=10)
    asyncio.run(engine.run_simulation(session.session_id))
    # 旧行为: 仅按匹配度排序（两任务都全匹配 → 稳定排序保持原序，先认领 t-slow）
    assert session.total_steps_executed > 0
    assert _first_claimed_task(session) == "t-slow"
