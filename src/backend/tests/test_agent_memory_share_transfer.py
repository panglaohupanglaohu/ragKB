"""Share ACL + transfer will execution."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore
from agents.agent_memory_lifecycle import AgentMemoryLifecycle, MemoryLifecycleError
from agents.agent_memory_share import AgentMemoryShare
from agents.agent_memory_transfer import AgentMemoryTransfer


def test_share_acl_and_deny_affect(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    sh = AgentMemoryShare(store=store, lifecycle=lc)
    team = "t-share"
    a, b = "alice", "bob"

    lc.transition(team, a, "bind")
    lc.set_persona(team, a, "shenmian")
    core = AgentMemoryCore(team, a, store=store)
    core.log.append({"action": "运维", "detail": "扩容 ES", "importance": 8, "tags": ["es"]})
    core.affect.feel("谨慎", 0.7, valence=-0.2)

    # 沈弥安：请求含 affect 会被剥离
    r = sh.grant(team, a, b, role="reader", layers=["log", "affect"])
    assert "log" in r["grant"]["layers"]
    assert "affect" not in r["grant"]["layers"]

    assert sh.can_access(team, a, b, "log") is True
    assert sh.can_access(team, a, b, "affect") is False

    data = sh.read_shared_layer(team, a, b, "log")
    assert data["ok"] and len(data["data"]) >= 1

    with pytest.raises(MemoryLifecycleError) as ei:
        sh.read_shared_layer(team, a, b, "affect")
    assert ei.value.code == "share_denied"

    sh.revoke(team, a, b)
    assert sh.can_access(team, a, b, "log") is False


def test_cowrite_requires_co_writer(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    sh = AgentMemoryShare(store=store, lifecycle=lc)
    team, a, b = "t-cw", "own", "peer"
    lc.transition(team, a, "bind")
    sh.grant(team, a, b, role="reader", layers=["log"])
    with pytest.raises(MemoryLifecycleError) as ei:
        sh.write_shared_log(team, a, b, {"detail": "不应成功"})
    assert ei.value.code == "share_denied"

    sh.grant(team, a, b, role="co_writer", layers=["log"])
    r = sh.write_shared_log(team, a, b, {"action": "协作", "detail": "补了一条共享笔记"})
    assert r["ok"] is True
    core = AgentMemoryCore(team, a, store=store)
    assert any("共享笔记" in (e.get("detail") or "") for e in core.log.events)


def test_transfer_copies_and_memorial(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    xfer = AgentMemoryTransfer(store=store, lifecycle=lc)
    team = "t-xfer"
    old, new = "senior", "junior"

    lc.transition(team, old, "bind")
    src = AgentMemoryCore(team, old, store=store)
    src.log.append({"action": "经验", "detail": "生产事故复盘", "importance": 9})
    src.intentions.add(
        {"creator": "ops", "instruction": "下周复查 RI", "trigger": "周一", "timeoutPolicy": "keep"}
    )
    src.affect.feel("牵挂", 0.5, valence=0.1)

    result = xfer.execute(
        team,
        old,
        new,
        handover_intentions="auto",
        keep_memorial=True,
        note="交接给新人",
        strategy="merge",
    )
    assert result["ok"] is True
    copied = result["transfer"].get("copied") or {}
    assert int(copied.get("log") or 0) >= 1
    assert int(copied.get("intentions") or 0) >= 1

    # merge 默认写入继承分区，不覆盖受益方本地活动记忆
    from agents.agent_memory_migration import load_inherited

    inh = load_inherited(store, team, new)
    assert inh["partitions"]
    logs = []
    intentions = []
    for p in inh["partitions"]:
        logs.extend((p.get("layers") or {}).get("log") or [])
        intentions.extend((p.get("layers") or {}).get("intentions") or [])
        assert (p.get("layers") or {}).get("affect") == {}
    assert any("生产事故" in (e.get("detail") or "") for e in logs)
    assert any((i.get("origin") or {}).get("kind") == "inherited" for i in logs)
    assert any(i.get("status") == "pending" for i in intentions)
    assert lc.resolve_state(team, old) == "archived"
    assert lc.resolve_state(team, new) in ("active", "unbound", "shared")
    # 凭吊可读
    assert AgentMemoryCore(team, old, store=store).memorial() is not None

    rows = xfer.list_transfers(team_id=team)
    assert len(rows) >= 1
