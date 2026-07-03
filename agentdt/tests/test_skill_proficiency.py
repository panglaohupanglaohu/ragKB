# -*- coding: utf-8 -*-
"""v4 技能熟练度测试 — proficiency_store + twin_loop 熟练度结算 (C-2.6)."""

import asyncio
import os
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


# ── ProficiencyStore ────────────────────────────────────────

def _mk_record(agent="a1", skill="coding", outcome="success", reward=0.4, step=0):
    from sandbox.models import SkillUsageRecord
    return SkillUsageRecord(agent_id=agent, agent_role="dev", skill_name=skill,
                            outcome=outcome, reward_delta=reward, step_index=step,
                            failure_reason="" if outcome == "success" else "low_proficiency: 测试")


def test_usage_append_load_aggregate():
    from sandbox.proficiency_store import ProficiencyStore
    with tempfile.TemporaryDirectory() as tmp:
        store = ProficiencyStore(usage_dir=Path(tmp) / "u", prof_dir=Path(tmp) / "p")
        records = [_mk_record(outcome="success"), _mk_record(outcome="failure"),
                   _mk_record(skill="testing", outcome="success")]
        assert store.append_usages("trial1", records) == 3
        loaded = store.load_usages("trial1")
        assert len(loaded) == 3
        stats = store.aggregate_trial("trial1")
        by_name = {s["skill_name"]: s for s in stats}
        assert by_name["coding"]["total_uses"] == 2
        assert by_name["coding"]["success_rate"] == 0.5
        assert len(by_name["coding"]["failure_samples"]) == 1
        assert by_name["testing"]["success_rate"] == 1.0


def test_proficiency_update_and_trend():
    from sandbox.proficiency_store import ProficiencyStore
    with tempfile.TemporaryDirectory() as tmp:
        store = ProficiencyStore(usage_dir=Path(tmp) / "u", prof_dir=Path(tmp) / "p")
        # trial1: 1/2 成功
        store.append_usages("t1", [_mk_record(), _mk_record(outcome="failure")])
        store.update_from_trial("teamA", "t1", "code_delivery")
        prof = store.get_agent_proficiency("teamA", "a1")
        assert prof["coding"] == 0.5
        # trial2: 2/2 成功 → 累计 3/4
        store.append_usages("t2", [_mk_record(), _mk_record()])
        store.update_from_trial("teamA", "t2", "code_delivery")
        prof = store.get_agent_proficiency("teamA", "a1")
        assert prof["coding"] == 0.75
        data = store.load_proficiency("teamA")
        key = "a1::coding"
        assert data[key]["trend"] == [0.5, 1.0]
        # query 接口
        items = store.query("teamA", "code_delivery")
        assert len(items) == 1


def test_rebuild_idempotent():
    from sandbox.proficiency_store import ProficiencyStore
    with tempfile.TemporaryDirectory() as tmp:
        store = ProficiencyStore(usage_dir=Path(tmp) / "u", prof_dir=Path(tmp) / "p")
        store.append_usages("t1", [_mk_record()])
        store.update_from_trial("teamA", "t1")
        r = store.rebuild("teamA", ["t1"])
        assert r["rebuilt"]
        prof = store.get_agent_proficiency("teamA", "a1")
        assert prof["coding"] == 1.0


# ── TwinLoop 熟练度结算 ──────────────────────────────────────

def _make_engine_and_session(proficiency: float, max_steps: int = 40, seed: int = 42):
    from sandbox.twin_loop import TwinLoopEngine
    from sandbox.memory_system import MemoryPool
    from sandbox.world_state import WorldStateManager
    from sandbox.models import SimulationMode

    random.seed(seed)
    ws = WorldStateManager()
    for aid, skills in (("a1", ["coding"]), ("a2", ["testing"])):
        ws.sync_agent_state(aid, {"role": "dev", "state": "idle", "skills": skills, "tools": []})
    tasks = []
    for i in range(8):
        tasks.append({"id": f"task-{i}", "title": f"T{i}", "assigned_to": None,
                      "required_roles": [], "required_skills": ["coding" if i % 2 == 0 else "testing"],
                      "required_tools": [], "priority": i})
    ws.sync_tasks(tasks)

    engine = TwinLoopEngine(ws, MemoryPool())
    session = engine.create_session(team_id="teamA", mode=SimulationMode.WHAT_IF,
                                    max_steps=max_steps, speed_factor=10000.0)
    engine.set_proficiency_priors(session.session_id, {
        "a1": {"coding": proficiency}, "a2": {"testing": proficiency},
    })
    return engine, session


def test_high_proficiency_outperforms_low():
    """C-2.6: 固定种子下，高熟练度团队总分显著更高."""
    engine_hi, s_hi = _make_engine_and_session(0.95, seed=42)
    asyncio.run(engine_hi.run_simulation(s_hi.session_id))
    reward_hi = sum(st.global_reward for st in s_hi.steps)

    engine_lo, s_lo = _make_engine_and_session(0.05, seed=42)
    asyncio.run(engine_lo.run_simulation(s_lo.session_id))
    reward_lo = sum(st.global_reward for st in s_lo.steps)

    assert reward_hi > reward_lo * 1.1, f"hi={reward_hi:.3f} lo={reward_lo:.3f}"


def test_usage_records_buffered_and_drained():
    engine, session = _make_engine_and_session(0.5, max_steps=30)
    asyncio.run(engine.run_simulation(session.session_id))
    records = engine.drain_usage_records(session.session_id)
    assert len(records) > 0
    r = records[0]
    assert r.skill_name in ("coding", "testing")
    assert r.outcome in ("success", "failure")
    assert r.agent_id in ("a1", "a2")
    # drain 后缓冲清空
    assert engine.drain_usage_records(session.session_id) == []
    # 失败记录必须带 failure_reason
    failures = [x for x in records if x.outcome == "failure"]
    for f in failures:
        assert f.failure_reason


def test_twin_spawn_loads_priors():
    engine, session = _make_engine_and_session(0.9, max_steps=10)
    asyncio.run(engine.run_simulation(session.session_id))
    twin = next(t for t in session.twins if t.source_agent_id == "a1")
    # 初始 0.9，成功会 +0.02 漂移，但应远高于默认 0.5
    assert twin.skill_proficiency.get("coding", 0) >= 0.9


def test_chaos_timeline_auto_injection():
    """C-2.3: 概率 1.0 的剧本事件必然注入."""
    engine, session = _make_engine_and_session(0.5, max_steps=25)
    engine.set_chaos_timeline(session.session_id, [
        {"from_step": 5, "to_step": 5, "event_type": "network_delay",
         "probability_per_step": 1.0, "payload": {}},
        {"from_step": 100, "to_step": 200, "event_type": "agent_leave",
         "probability_per_step": 1.0, "payload": {}},  # 超出 max_steps，不应触发
    ])
    asyncio.run(engine.run_simulation(session.session_id))
    chaos = engine._chaos_states.get(session.session_id, {})
    events = chaos.get("events", [])
    assert any(e["type"] == "network_delay" for e in events)
    assert not any(e["type"] == "agent_leave" for e in events)


def test_chaos_timeline_probability_bounds():
    """概率 0 永不注入."""
    engine, session = _make_engine_and_session(0.5, max_steps=20)
    engine.set_chaos_timeline(session.session_id, [
        {"from_step": 0, "to_step": 19, "event_type": "agent_failure",
         "probability_per_step": 0.0, "payload": {}},
    ])
    asyncio.run(engine.run_simulation(session.session_id))
    chaos = engine._chaos_states.get(session.session_id, {})
    assert not any(e["type"] == "agent_failure" for e in chaos.get("events", []))
