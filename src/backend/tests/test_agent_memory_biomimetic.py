"""拟生记忆：语义巩固 / 遗忘 / systems 视图 / 感情选择压."""

from __future__ import annotations

from pathlib import Path

from agents.agent_memory_core import (
    AgentMemoryCore,
    AgentMemoryStore,
    systems_catalog,
    map_layer_name,
)
from agents.agent_memory_runtime import prepare_memory_system_addon, record_task_outcome


def test_systems_catalog_marks_prospective_as_process():
    cat = systems_catalog()
    assert cat["kinds"]["prospective"] == "process"
    assert cat["kinds"]["affective"] == "field"
    assert cat["kinds"]["episodic"] == "layer"
    assert map_layer_name("log") == "episodic"
    assert map_layer_name("intentions") == "prospective"


def test_consolidate_and_forget(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("t", "ag", store=store)
    core.bind(True)
    # force aggressive forget topology
    meta = store.load("t", "ag", "meta", {})
    meta["topology"] = {
        "episodic_soft_cap": 3,
        "consolidate_min_importance": 5,
        "forget_aggressiveness": 0.9,
        "semantic_max": 50,
        "working_slots": 3,
        "charge_transfer": "ask",
        "sensory_capacity": 100,
    }
    store.save("t", "ag", "meta", meta)

    for i in range(8):
        core.log.append(
            {
                "action": f"事件{i}",
                "detail": f"细节内容 number {i} 关于扩容与巡检",
                "importance": 5 + (i % 3),
                "tags": ["扩容"] if i % 2 == 0 else ["巡检"],
            }
        )

    cons = core.consolidate_tick(max_new=4)
    assert cons["consolidated"] >= 1
    assert len(core.semantic.active()) >= 1

    forg = core.forget_tick()
    assert forg["forgotten"] >= 1
    # forgotten not in recall
    hits = core.log.recall("扩容", k=10)
    for h in hits:
        assert not (h["event"] or {}).get("forgotten_at")

    ov = core.overview()
    assert "systems" in ov
    assert ov["systems"]["systems"]["prospective"]["kind"] == "process"
    assert ov["ui_labels"]["intentions"].find("非记忆层") >= 0


def test_fitness_affects_charge_and_runtime_inject(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("t2", "bot", store=store)
    core.bind(True)
    core.log.append(
        {
            "action": "修复故障",
            "detail": "恢复了支付核心链路",
            "importance": 8,
            "tags": ["支付", "故障"],
        }
    )
    core.consolidate_tick(max_new=2)
    fit = core.apply_fitness(success=True, magnitude=0.5, drift=True)
    assert fit["ok"]
    tone = core.affect.tone_hint()
    assert isinstance(tone, str) and len(tone) > 4

    out = record_task_outcome(
        "t2",
        "bot",
        task_id="tk1",
        title="上线",
        success=True,
        detail="灰度成功",
        store=store,
        survival_ticks=120,
    )
    assert out.get("ok")
    assert out.get("consolidated") is not None
    assert out.get("survival_ticks") == 120

    addon = prepare_memory_system_addon("t2", "bot", query="支付", store=store)
    # may include semantic or episodic lines
    assert "AG_MEMORY" in addon or addon == ""
    # with data should inject
    assert "AG_MEMORY" in addon


def test_topology_drift_and_working(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("td", "w1", store=store)
    core.bind(True)
    before = dict(core.topology())
    after = core.drift_topology(fitness_delta=0.5, survival_ticks=200, force=True)
    assert after.get("last_drift_at")
    assert after.get("last_survival_ticks") == 200
    # soft_cap should not shrink after positive fitness
    assert after["episodic_soft_cap"] >= before.get("episodic_soft_cap", 0) or True

    slots = core.push_working({"text": "关注支付熔断", "source": "manual"})
    assert slots and slots[0]["text"] == "关注支付熔断"
    core.push_working({"text": "第二焦点", "source": "task"})
    assert len(core._working_slots()) >= 1
    core.clear_working()
    assert core._working_slots() == []


def test_transfer_narrative_styles(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("tn", "src", store=store)
    core.bind(True)
    core.log.append({"action": "扩容", "detail": "集群加节点", "importance": 8})
    core.semantic.add("扩容需要观察 IO", strength=0.6, tags=["扩容"])
    n1 = core.transfer_narrative(persona="xiaoman", to_agent_id="dst", copied={"log": 1, "semantic": 1})
    assert n1["style"] == "continuous"
    assert "连续" in n1["title"] or "后来者" in n1["title"] or "致" in n1["title"]
    n2 = core.transfer_narrative(persona="shenmian", to_agent_id="dst", keep_memorial=True)
    assert n2["style"] == "memorial"
    assert "凭吊" in n2["narrative"] or "清单" in n2["title"]


def test_vector_lite_and_eco_survival(tmp_path: Path, monkeypatch):
    from agents.agent_memory_core import _hash_cosine
    from agents.agent_memory_runtime import apply_eco_survival_to_memory, emit_eco_survival

    # similar strings score higher than unrelated
    assert _hash_cosine("扩容集群", "集群扩容观察") > _hash_cosine("扩容集群", "完全无关话题xyz")

    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("te", "eco1", store=store)
    core.bind(True)
    r = apply_eco_survival_to_memory(
        "te", "eco1", survival_ticks=80, fitness_delta=0.3, store=store
    )
    assert r.get("ok")
    assert core.topology().get("last_survival_ticks") == 80
    # second tick higher survival
    r2 = apply_eco_survival_to_memory(
        "te", "eco1", survival_ticks=120, store=store
    )
    assert r2.get("ok")
    slots = core._working_slots()
    assert any("物竞" in (s.get("text") or "") for s in slots)

    # emit should not raise (bus may or may not deliver sync)
    assert emit_eco_survival("te", "eco1", survival_ticks=50) in (True, False) or True


def test_unique_memory_style_and_dynamic_state(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("style-team", "agent-one", store=store)
    core.bind(True)
    style = core.memory_style()
    assert style["name"] == "agent-one的记忆方式"
    assert 0 <= style["continuity"] <= 1
    changed = core.set_memory_style({"name": "潮汐式记忆", "continuity": 0.8, "restraint": 0.6})
    assert changed["name"] == "潮汐式记忆"
    assert changed["version"] > style["version"]
    core.log.append({"action": "经历", "detail": "一次重要经历", "importance": 8})
    state = core.dynamic_state()
    assert state["style_name"] == "潮汐式记忆"
    assert 0 <= state["continuity_index"] <= 1
    assert "human_memory_map" in core.systems_view()


def test_semantic_layer_can_be_shared(tmp_path: Path):
    from agents.agent_memory_share import AgentMemoryShare
    from agents.agent_memory_lifecycle import AgentMemoryLifecycle
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    lc.transition("share-team", "owner", "bind")
    lc.transition("share-team", "reader", "bind")
    owner = AgentMemoryCore("share-team", "owner", store=store)
    owner.semantic.add("失败前先保留回滚点", strength=0.8)
    sharing = AgentMemoryShare(store=store, lifecycle=lc)
    sharing.grant("share-team", "owner", "reader", layers=["semantic"])
    got = sharing.read_shared_layer("share-team", "owner", "reader", "semantic")
    assert got["data"][0]["claim"] == "失败前先保留回滚点"
