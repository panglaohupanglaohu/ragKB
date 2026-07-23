"""Agent four-layer memory core + bind/seal regressions."""

from __future__ import annotations

from pathlib import Path

from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore


def test_bind_log_recall_and_seal(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("team-a", "agent-x", store=store)
    meta = core.bind(True)
    assert meta["bound"] is True
    assert meta["agent_id"] == "agent-x"

    e = core.log.append(
        {
            "subject": "agent-x",
            "action": "扩容",
            "detail": "ElasticSearch 集群纵向扩容观察 IO",
            "place": "aws-ops",
            "importance": 8,
            "tags": ["es", "扩容"],
        }
    )
    assert e["id"]
    hits = core.log.recall("扩容", k=3)
    assert hits and hits[0]["parts"]["relevance"] > 0

    core.perception.perceive({"modality": "vision", "payload": {"fear": 0.2, "obj": "告警"}})
    core.perception.perceive({"modality": "audition", "payload": "pager duty"})
    comp = core.perception.compress(core.log)
    assert comp and comp["event"]["action"] == "感知压缩"
    assert core.perception.summarize()["count"] == 0

    it = core.intentions.add(
        {
            "creator": "ops-lead",
            "instruction": "下周复查 RI 覆盖率",
            "trigger": "周一例会",
            "timeoutPolicy": "escalate",
        }
    )
    assert it["status"] == "pending"
    assert core.intentions.confirm(it["id"])["status"] == "confirmed"

    core.affect.feel("谨慎", 0.6, valence=-0.2, arousal=0.4)
    tone = core.affect.tone_hint()
    assert "谨慎" in tone or "语气" in tone

    snap = core.seal()
    assert snap["schema"] == "ag.legacy/v1"
    assert core.is_sealed()
    mem = core.memorial()
    assert mem and mem["agent_id"] == "agent-x"

    # sealed still readable for memorial; export works
    exp = core.export_all()
    assert exp["schema"] == "ag.memory/v1"
    assert len(exp["layers"]["log"]) >= 2


def test_import_export_roundtrip(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    a = AgentMemoryCore("t1", "a1", store=store)
    a.log.append({"action": "对话", "detail": "关于迁移方案", "importance": 6, "tags": ["迁移"]})
    a.affect.feel("牵挂", 0.5, valence=0.1)
    blob = a.export_all()

    b = AgentMemoryCore("t1", "a2", store=store)
    assert b.import_all(blob) is True
    assert len(b.log.events) == 1
    assert b.log.events[0]["detail"] == "关于迁移方案"


def test_shared_timeline_at(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("t", "ag", store=store)
    t0 = 1_700_000_000_000
    core.log.append({"t": t0, "action": "路过", "detail": "溪边"})
    core.perception.perceive({"t": t0 + 100, "modality": "smell", "payload": "梅香"})
    core.intentions.add({"instruction": "提醒复查", "tCreated": t0 - 10})
    slice_ = core.at(t0, window_ms=1000)
    assert len(slice_["log"]) == 1
    assert len(slice_["perception"]) == 1
    assert len(slice_["intentions"]) == 1
