"""Memory runtime: prepare_context, record_task, inject, auto-compress."""

from __future__ import annotations

from pathlib import Path

from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore
from agents.agent_memory_lifecycle import AgentMemoryLifecycle
from agents.agent_memory_runtime import (
    inject_memory_into_messages,
    prepare_memory_system_addon,
    record_perception,
    record_task_outcome,
)


def test_prepare_and_inject(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    # patch global store used by prepare if needed — pass store via core writes then prepare uses get_memory_store
    # Use isolated store by temporarily writing through store path and AgentMemoryCore with store=
    team, agent = "t-rt", "ag-rt"
    lc_local = AgentMemoryLifecycle(store=store)
    lc_local.transition(team, agent, "bind")
    lc_local.set_persona(team, agent, "xiaoman")
    core = AgentMemoryCore(team, agent, store=store)
    core.log.append(
        {
            "action": "扩容",
            "detail": "ElasticSearch 集群扩容观察",
            "importance": 8,
            "tags": ["es"],
        }
    )
    core.affect.feel("谨慎", 0.5, valence=-0.1)

    # prepare uses get_memory_store by default — inject store via monkeypatch style:
    # call with store= parameter
    addon = prepare_memory_system_addon(team, agent, query="ES 扩容", store=store)
    assert "[AG_MEMORY]" in addon
    assert "语气" in addon or "谨慎" in addon or "相关记忆" in addon

    msgs = [{"role": "system", "content": "You are agent."}, {"role": "user", "content": "hi"}]
    out = inject_memory_into_messages(msgs, addon)
    assert "[AG_MEMORY]" in out[0]["content"]
    # second inject replaces, no double
    out2 = inject_memory_into_messages(out, addon + "\nEXTRA")
    assert out2[0]["content"].count("[AG_MEMORY]") == 1


def test_record_task_and_compress(tmp_path: Path, monkeypatch):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    team, agent = "t2", "a2"
    lc.transition(team, agent, "bind")
    lc.set_persona(
        team,
        agent,
        "xiaoman",
        autonomy={
            "auto_log_on_task": True,
            "auto_perceive_on_tool": True,
            "auto_compress_threshold": 3,
            "auto_feel_on_outcome": True,
            "auto_recall_on_chat": True,
            "recall_min_importance": 1,
        },
    )

    r = record_task_outcome(
        team, agent, task_id="tsk1", title="修告警", success=True, store=store
    )
    assert r["ok"] is True
    core = AgentMemoryCore(team, agent, store=store)
    assert any(e.get("action") == "任务成功" for e in core.log.events)

    for i in range(3):
        record_perception(
            team, agent, modality="tool", payload={"i": i, "summary": f"step{i}"}, store=store
        )
    core2 = AgentMemoryCore(team, agent, store=store)
    # threshold 3 → compress emptied buffer
    assert core2.perception.summarize()["count"] == 0
    assert any(e.get("action") == "感知压缩" for e in core2.log.events)


def test_destroyed_skips(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    lc.transition("t", "dead", "bind")
    lc.transition("t", "dead", "destroy")
    r = record_task_outcome("t", "dead", task_id="x", success=True, store=store)
    assert r["ok"] is False
    addon = prepare_memory_system_addon("t", "dead", query="x", store=store)
    assert addon == ""


def test_auto_bind_and_chat_turn(tmp_path: Path):
    from agents.agent_memory_runtime import ensure_memory_ready, record_chat_turn

    store = AgentMemoryStore(tmp_path)
    # unbound → auto bind
    r = ensure_memory_ready("t-ab", "newbie", store=store, auto_bind=True)
    assert r["ok"] is True
    assert r.get("auto_bound") is True

    r2 = record_chat_turn(
        "t-ab",
        "newbie",
        user_text="如何扩容 ES？",
        assistant_text="先看 CPU 与存储水位。",
        session_id="s1",
        store=store,
    )
    assert r2["ok"] is True
    core = AgentMemoryCore("t-ab", "newbie", store=store)
    assert any(e.get("action") == "对话" for e in core.log.events)
    assert any(p.get("modality") == "dialogue" for p in core.perception.buffer) or any(
        e.get("action") == "感知压缩" for e in core.log.events
    )


def test_reflect_shenmian(tmp_path: Path):
    from agents.agent_memory_runtime import maybe_reflect

    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    lc.transition("t-r", "sage", "bind")
    lc.set_persona("t-r", "sage", "shenmian")
    core = AgentMemoryCore("t-r", "sage", store=store)
    for i in range(4):
        core.log.append({"action": f"步骤{i}", "detail": f"做了事情{i}", "importance": 6 + i % 3})
    ok = maybe_reflect("t-r", "sage", store=store, core=core, force=True)
    assert ok is True
    assert any(e.get("action") == "反思固化" for e in core.log.events)


def test_aas_bridge(tmp_path: Path, monkeypatch):
    from types import SimpleNamespace

    from agents.agent_memory_runtime import bridge_aas_experience

    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    lc.transition("t-aas", "twin-bot", "bind")
    exp = SimpleNamespace(
        agent_id="twin-bot",
        team_id="t-aas",
        situation="集群 CPU 告警",
        action_taken="缩容评估",
        outcome="success",
        reward=0.9,
        reflection="先看水位再动",
        session_id="sess1",
        experience_id="ex1",
        metadata={"bridge_to_memory": True},
    )
    r = bridge_aas_experience(exp, store=store)
    assert r["ok"] is True
    core = AgentMemoryCore("t-aas", "twin-bot", store=store)
    assert any("孪生经验" in (e.get("action") or "") for e in core.log.events)

    # off without flag
    exp2 = SimpleNamespace(
        agent_id="twin-bot",
        team_id="t-aas",
        situation="x",
        action_taken="y",
        outcome="failure",
        reward=0,
        reflection="",
        session_id="",
        experience_id="ex2",
        metadata={},
    )
    monkeypatch.delenv("AG_MEMORY_AAS_BRIDGE", raising=False)
    r2 = bridge_aas_experience(exp2, store=store)
    assert r2["ok"] is False and r2["reason"] == "bridge_off"
