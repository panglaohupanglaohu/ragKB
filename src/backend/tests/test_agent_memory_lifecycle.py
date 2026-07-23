"""Memory lifecycle: bind/seal/destroy/tombstone/illegal transitions."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore
from agents.agent_memory_lifecycle import (
    AgentMemoryLifecycle,
    MemoryLifecycleError,
)


def test_bind_save_seal_destroy(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    team, agent = "t-life", "ag-life"

    r = lc.transition(team, agent, "bind")
    assert r["to"] == "active"
    assert lc.resolve_state(team, agent) == "active"

    core = AgentMemoryCore(team, agent, store=store)
    core.log.append({"action": "测试", "detail": "生命周期", "importance": 7})
    core.perception.perceive({"modality": "alert", "payload": "ping"})

    saved = lc.transition(team, agent, "save")
    assert saved["ok"] is True
    # 重新加载 store 视图（内存中的 core 缓冲可能仍是旧引用）
    core2 = AgentMemoryCore(team, agent, store=store)
    assert core2.perception.summarize()["count"] == 0
    assert len(core2.log.events) >= 2

    sealed = lc.transition(team, agent, "seal")
    assert sealed["to"] == "sealed"
    with pytest.raises(MemoryLifecycleError) as ei:
        lc.assert_writable(team, agent)
    assert "sealed" in ei.value.detail or "不可写" in ei.value.detail

    destroyed = lc.transition(team, agent, "destroy", reason="test")
    assert destroyed["state"] == "destroyed"
    assert lc.is_tombstoned(team, agent)
    with pytest.raises(MemoryLifecycleError):
        lc.assert_readable(team, agent)


def test_illegal_unbind_from_sealed(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    lc.transition("t", "a", "bind")
    lc.transition("t", "a", "seal")
    with pytest.raises(MemoryLifecycleError) as ei:
        lc.transition("t", "a", "unbind")
    assert ei.value.code == "illegal_transition"


def test_persona_presets(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    lc.transition("t", "p", "bind")
    st = lc.set_persona("t", "p", "xiaoman")
    assert st["persona"] == "xiaoman"
    assert st["autonomy"].get("auto_perceive_on_tool") is True
    st2 = lc.set_persona("t", "p", "shenmian")
    assert st2["persona"] == "shenmian"
    assert st2["autonomy"].get("recall_min_importance") == 6
