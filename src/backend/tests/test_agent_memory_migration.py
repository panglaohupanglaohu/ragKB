# -*- coding: utf-8 -*-
"""Agent memory migration v2 / will / rollback / half-life evidence tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from agents.agent_memory_core import (
    AFFECT_HALF_LIFE_MS,
    AgentMemoryCore,
    AgentMemoryStore,
)
from agents.agent_memory_migration import (
    EXPORT_SCHEMA_V2,
    MemoryMigrationError,
    build_export_v2,
    create_will,
    execute_will,
    import_transaction,
    inherited_hits_for_recall,
    load_inherited,
    load_tx_record,
    load_will,
    preflight_will,
    sha256_json,
    snapshot_exact_files,
    snapshot_hash,
    validate_export_v2,
)
from agents.agent_memory_runtime import prepare_memory_system_addon
from agents.agent_memory_transfer import AgentMemoryTransfer
from agents.agent_memory_lifecycle import AgentMemoryLifecycle, MemoryLifecycleError


def _seed(core: AgentMemoryCore, tag: str = "A") -> None:
    core.bind(True)
    core.log.append(
        {
            "action": f"决策{tag}",
            "detail": f"关键扩容决策 {tag}",
            "importance": 8,
            "tags": ["扩容", tag],
        }
    )
    core.perception.perceive({"modality": "system", "payload": f"alert-{tag}"})
    core.intentions.add({"instruction": f"复查 RI {tag}", "trigger": "周一"})
    core.semantic.add(f"规则-{tag}", strength=0.6, tags=[tag])
    core.affect.feel("谨慎", 1.0, valence=-0.2, arousal=0.4)


def test_export_v2_hash_stable_and_tamper_rejected(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("t", "src", store=store)
    _seed(core, "X")
    exp = build_export_v2(core)
    assert exp["schema_version"] == EXPORT_SCHEMA_V2
    assert validate_export_v2(exp).ok

    # key order independence
    layers_reordered = {
        "semantic": exp["layers"]["semantic"],
        "affect": exp["layers"]["affect"],
        "log": exp["layers"]["log"],
        "intentions": exp["layers"]["intentions"],
        "perception": exp["layers"]["perception"],
    }
    assert sha256_json(layers_reordered["log"]) == exp["content_hashes"]["layers"]["log"]

    # tamper log content
    bad = dict(exp)
    bad_layers = dict(exp["layers"])
    bad_log = list(bad_layers["log"])
    bad_log[0] = dict(bad_log[0], detail="TAMPERED")
    bad_layers["log"] = bad_log
    bad["layers"] = bad_layers
    r = validate_export_v2(bad)
    assert not r.ok
    assert any("hash_mismatch:log" in e for e in r.errors)

    # tamper count
    bad2 = dict(exp)
    bad2["record_counts"] = dict(exp["record_counts"], log=999)
    r2 = validate_export_v2(bad2)
    assert not r2.ok
    assert any("count_mismatch:log" in e for e in r2.errors)

    # drop a layer
    bad3 = dict(exp)
    bad3["layers"] = {k: v for k, v in exp["layers"].items() if k != "semantic"}
    r3 = validate_export_v2(bad3)
    assert not r3.ok


def test_legacy_v1_marked_weak(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    a = AgentMemoryCore("t", "a", store=store)
    _seed(a)
    v1 = a.export_all()
    report = validate_export_v2(v1)
    assert report.ok
    assert report.validation_strength == "legacy_weak"


def test_unknown_schema_is_not_treated_as_legacy_v1():
    payload = {
        "schema": "evil.memory/v999",
        "layers": {
            "log": [],
            "perception": [],
            "intentions": [],
            "affect": {},
            "semantic": [],
        },
    }
    report = validate_export_v2(payload)
    assert report.ok is False
    assert report.errors == ["unknown_schema:evil.memory/v999"]


@pytest.mark.parametrize("fail_after", [1, 3, "last"])
def test_import_failure_restores_exact_hashes(tmp_path: Path, fail_after):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    dst = AgentMemoryCore("t", "dst", store=store)
    _seed(src, "S")
    dst.bind(True)
    dst.log.append({"action": "本地", "detail": "受益方本地经历", "importance": 7})
    before = snapshot_exact_files(store, "t", "dst")
    before_h = snapshot_hash(before)
    bundle = build_export_v2(src)
    with pytest.raises(MemoryMigrationError):
        import_transaction(dst, bundle, strategy="merge", fail_after=fail_after)
    after = snapshot_exact_files(store, "t", "dst")
    assert snapshot_hash(after) == before_h
    # local log preserved
    dst2 = AgentMemoryCore("t", "dst", store=store)
    assert any("本地" in (e.get("detail") or "") for e in dst2.log.events)


@pytest.mark.parametrize("strategy", ["replace_all", "merge", "selective"])
def test_each_strategy_preserves_expected_target_data(tmp_path: Path, strategy):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    dst = AgentMemoryCore("t", "dst", store=store)
    _seed(src, "S")
    dst.bind(True)
    dst.log.append({"action": "本地", "detail": "keep-me", "importance": 9})
    local_n = len(dst.log.events)
    bundle = build_export_v2(src)
    selected = ["log", "semantic"] if strategy == "selective" else None
    result = import_transaction(
        dst, bundle, strategy=strategy, selected_layers=selected, transfer_id=f"tx_{strategy}"
    )
    assert result["ok"] and result["state"] == "committed"
    dst2 = AgentMemoryCore("t", "dst", store=store)
    if strategy == "merge" or strategy == "selective":
        # local active memory untouched
        assert any((e.get("detail") == "keep-me") for e in dst2.log.events)
        assert len(dst2.log.events) == local_n
        inh = load_inherited(store, "t", "dst")
        assert any(p.get("transfer_id") == f"tx_{strategy}" for p in inh["partitions"])
        part = next(p for p in inh["partitions"] if p.get("transfer_id") == f"tx_{strategy}")
        for item in part["layers"].get("log") or []:
            assert (item.get("origin") or {}).get("kind") == "inherited"
            assert (item.get("origin") or {}).get("source_agent", {}).get("agent_id") == "src"
    else:
        # replace_all overwrites active log
        assert any("关键扩容" in (e.get("detail") or "") for e in dst2.log.events)


def test_same_transfer_id_is_idempotent(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    dst = AgentMemoryCore("t", "dst", store=store)
    _seed(src)
    dst.bind(True)
    bundle = build_export_v2(src)
    r1 = import_transaction(dst, bundle, strategy="merge", transfer_id="tx_idem")
    r2 = import_transaction(dst, bundle, strategy="merge", transfer_id="tx_idem")
    assert r2.get("idempotent") is True
    inh = load_inherited(store, "t", "dst")
    assert sum(1 for p in inh["partitions"] if p.get("transfer_id") == "tx_idem") == 1


def test_source_not_sealed_when_beneficiary_commit_fails(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    dst = AgentMemoryCore("t", "dst", store=store)
    _seed(src)
    dst.bind(True)
    will = create_will(
        store,
        "t",
        "src",
        {"beneficiary": "dst", "strategy": "merge", "layers": ["log", "semantic"]},
    )
    preflight_will(store, will["will_id"])
    with pytest.raises(MemoryMigrationError):
        execute_will(store, will["will_id"], fail_after=1)
    src2 = AgentMemoryCore("t", "src", store=store)
    assert not src2.is_sealed()
    meta = store.load("t", "src", "meta", {}) or {}
    assert meta.get("state") != "archived"


def test_failed_will_does_not_bind_unbound_beneficiary(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    _seed(src)
    lc = AgentMemoryLifecycle(store=store)
    assert lc.resolve_state("t", "dst") == "unbound"
    will = create_will(
        store,
        "t",
        "src",
        {"beneficiary": "dst", "strategy": "merge", "layers": ["log"]},
    )
    preflight_will(store, will["will_id"])
    with pytest.raises(MemoryMigrationError):
        execute_will(store, will["will_id"], lifecycle=lc, fail_after=1)
    assert lc.resolve_state("t", "dst") == "unbound"
    assert store.load("t", "dst", "meta", {}) == {}


def test_source_finalize_failure_rolls_back_both_sides(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    dst = AgentMemoryCore("t", "dst", store=store)
    _seed(src)
    dst.bind(True)
    dst.log.append({"action": "本地", "detail": "must-survive", "importance": 8})
    dst_before = snapshot_exact_files(store, "t", "dst")

    will = create_will(
        store,
        "t",
        "src",
        {"beneficiary": "dst", "strategy": "merge", "layers": ["log"]},
    )
    preflight_will(store, will["will_id"])

    class FailingLifecycle(AgentMemoryLifecycle):
        def transition(self, team_id, agent_id, action, **kwargs):
            if team_id == "t" and agent_id == "src" and action == "seal":
                raise MemoryLifecycleError("seal_failed", "injected seal failure")
            return super().transition(team_id, agent_id, action, **kwargs)

    with pytest.raises(MemoryMigrationError) as exc:
        execute_will(
            store,
            will["will_id"],
            lifecycle=FailingLifecycle(store=store),
        )
    assert exc.value.code == "source_finalize_failed"
    assert snapshot_hash(snapshot_exact_files(store, "t", "dst")) == snapshot_hash(dst_before)
    assert AgentMemoryLifecycle(store=store).resolve_state("t", "src") == "active"
    assert load_will(store, will["will_id"])["status"] == "failed"
    assert load_tx_record(store, will["will_id"])["state"] == "rolled_back"


@pytest.mark.parametrize(
    ("policy", "expected", "needs_confirmation"),
    [("drop", 0, False), ("auto", 1, False), ("ask_new_owner", 1, True)],
)
def test_handover_intention_policy_is_applied(
    tmp_path: Path, policy: str, expected: int, needs_confirmation: bool
):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    dst = AgentMemoryCore("t", "dst", store=store)
    src.bind(True)
    pending = src.intentions.add({"instruction": "交接任务", "trigger": "周一"})
    confirmed = src.intentions.add({"instruction": "已完成任务"})
    src.intentions.confirm(confirmed["id"])
    dst.bind(True)
    will = create_will(
        store,
        "t",
        "src",
        {
            "beneficiary": "dst",
            "strategy": "merge",
            "layers": ["intentions"],
            "handover_intentions": policy,
            "keep_memorial": False,
        },
    )
    preflight_will(store, will["will_id"])
    execute_will(store, will["will_id"])
    part = load_inherited(store, "t", "dst")["partitions"][0]
    inherited = part["layers"]["intentions"]
    assert len(inherited) == expected
    if inherited:
        assert inherited[0]["id"] != pending["id"]
        assert bool(inherited[0].get("requires_confirmation")) is needs_confirmation
        assert inherited[0]["handover"]["policy"] == policy


def test_explicit_affect_will_does_not_false_positive_source_change(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    dst = AgentMemoryCore("t", "dst", store=store)
    src.bind(True)
    src.affect.feel("谨慎", 0.8, valence=-0.2, arousal=0.5)
    dst.bind(True)
    will = create_will(
        store,
        "t",
        "src",
        {
            "beneficiary": "dst",
            "strategy": "merge",
            "layers": ["affect"],
            "keep_memorial": False,
        },
    )
    assert preflight_will(store, will["will_id"])["ok"]
    result = execute_will(store, will["will_id"])
    assert result["state"] == "executed"
    affect = load_inherited(store, "t", "dst")["partitions"][0]["layers"]["affect"]
    assert affect.get("labels", {}).get("谨慎", 0) > 0


def test_will_execute_merge_and_seal_source(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    src = AgentMemoryCore("t", "src", store=store)
    dst = AgentMemoryCore("t", "dst", store=store)
    _seed(src, "W")
    dst.bind(True)
    dst.log.append({"action": "本地", "detail": "dst-local", "importance": 6})
    will = create_will(
        store,
        "t",
        "src",
        {
            "beneficiary": "dst",
            "strategy": "merge",
            "layers": ["log", "perception", "intentions", "semantic"],
            "keep_memorial": True,
        },
    )
    report = preflight_will(store, will["will_id"])
    assert report["ok"] is True
    result = execute_will(store, will["will_id"])
    assert result["ok"] and result["state"] == "executed"
    # source sealed/archived
    meta = store.load("t", "src", "meta", {}) or {}
    assert meta.get("sealed") or AgentMemoryCore("t", "src", store=store).is_sealed()
    # dst local preserved
    dst2 = AgentMemoryCore("t", "dst", store=store)
    assert any(e.get("detail") == "dst-local" for e in dst2.log.events)
    # inherited present
    inh = load_inherited(store, "t", "dst")
    assert inh["partitions"]


def test_transfer_adapter_uses_will_engine(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    xfer = AgentMemoryTransfer(store=store, lifecycle=lc)
    src = AgentMemoryCore("t", "from_a", store=store)
    dst = AgentMemoryCore("t", "to_b", store=store)
    _seed(src, "T")
    dst.bind(True)
    out = xfer.execute("t", "from_a", "to_b", strategy="merge", keep_memorial=True)
    assert out["ok"]
    assert out.get("will") or out.get("transfer")
    assert load_inherited(store, "t", "to_b")["partitions"]


def test_affect_half_life_72h(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("t", "a", store=store)
    core.affect.state = {"valence": 0.0, "arousal": 0.0, "labels": {"x": 1.0}, "updatedAt": 1_000_000}
    core.affect._decay_to(1_000_000 + AFFECT_HALF_LIFE_MS)
    assert abs(core.affect.state["labels"]["x"] - 0.5) < 1e-9
    core.affect.state = {"valence": 0.0, "arousal": 0.0, "labels": {"x": 1.0}, "updatedAt": 1_000_000}
    core.affect._decay_to(1_000_000 + 2 * AFFECT_HALF_LIFE_MS)
    assert abs(core.affect.state["labels"]["x"] - 0.25) < 1e-9


def test_update_from_evidence_progresses_intentions(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("t", "a", store=store)
    core.bind(True)
    it = core.intentions.add({"instruction": "完成迁移演练", "trigger": "今晚"})
    other = core.intentions.add({"instruction": "无关任务", "trigger": "明年"})
    result = core.update_from_evidence(
        {
            "source_type": "task",
            "source_id": "task-1",
            "agent_id": "a",
            "summary": "完成迁移演练 成功",
            "success": True,
            "intention_match": "迁移演练",
            "provenance": {"source_type": "task", "source_id": "task-1", "agent_id": "a"},
        }
    )
    assert result["ok"]
    assert result["provenance"]["source_type"] == "task"
    statuses = {i["id"]: i["status"] for i in core.intentions.items}
    assert statuses[it["id"]] == "confirmed"
    assert statuses[other["id"]] == "pending"
    stored = next(e for e in core.log.events if e.get("id") == result["event_id"])
    assert stored["origin"]["source_type"] == "task"
    assert stored["origin"]["source_id"] == "task-1"


def test_two_transfers_do_not_lose_updates(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    a = AgentMemoryCore("t", "a", store=store)
    b = AgentMemoryCore("t", "b", store=store)
    c = AgentMemoryCore("t", "c", store=store)
    _seed(a, "A")
    b.bind(True)
    c.bind(True)
    b.log.append({"action": "b-local", "detail": "b1", "importance": 5})
    import_transaction(b, build_export_v2(a), strategy="merge", transfer_id="tx1")
    # b gains more local after first transfer
    b.log.append({"action": "b-local", "detail": "b2-after", "importance": 6})
    _seed(c, "C")
    import_transaction(b, build_export_v2(c), strategy="merge", transfer_id="tx2")
    b2 = AgentMemoryCore("t", "b", store=store)
    details = [e.get("detail") for e in b2.log.events]
    assert "b1" in details and "b2-after" in details
    inh = load_inherited(store, "t", "b")
    assert len(inh["partitions"]) == 2


def test_inherited_hits_soft_match_chinese_title_not_exact_substring(tmp_path: Path):
    """Regression: Chinese scene titles must still recall inherited es_scale memories."""
    store = AgentMemoryStore(tmp_path)
    mentor = AgentMemoryCore("ops", "mentor", store=store)
    mentor.bind(True)
    mentor.log.append(
        {
            "action": "关键决策",
            "detail": "成功处理 es_scale：采用分批与监控，先小流量验证再扩面",
            "importance": 9,
            "tags": ["扩容", "es", "IO", "分批", "good"],
        }
    )
    mentor.semantic.add(
        "规则：es_scale 必须分批+监控+可回滚",
        strength=0.85,
        tags=["扩容", "es", "good"],
    )
    heir = AgentMemoryCore("ops", "heir", store=store)
    heir.bind(True)
    result = import_transaction(
        heir,
        build_export_v2(mentor),
        strategy="merge",
        transfer_id="tx-soft-recall",
    )
    assert result["ok"]
    title = "Elasticsearch 集群高峰扩容"
    hits = inherited_hits_for_recall(store, "ops", "heir", title, k=3)
    assert hits, "soft match must return inherited hits for Chinese title query"
    assert any("分批" in (h.get("summary") or "") or "es_scale" in (h.get("summary") or "") for h in hits)
    addon = prepare_memory_system_addon(
        "ops",
        "heir",
        query=title,
        store=store,
        include_inherited=True,
        max_chars=1200,
    )
    assert "继承" in addon
    assert len(addon) > 80


def test_concurrent_transfers_to_same_beneficiary_keep_both_partitions(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    target = AgentMemoryCore("t", "target", store=store)
    target.bind(True)
    sources = []
    for agent_id in ("src-a", "src-b"):
        source = AgentMemoryCore("t", agent_id, store=store)
        _seed(source, agent_id)
        sources.append(source)

    def transfer(source: AgentMemoryCore):
        return import_transaction(
            AgentMemoryCore("t", "target", store=store),
            build_export_v2(source),
            strategy="merge",
            transfer_id=f"tx-{source.agent_id}",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(transfer, sources))
    assert all(result["ok"] for result in results)
    partitions = load_inherited(store, "t", "target")["partitions"]
    assert {part["transfer_id"] for part in partitions} == {"tx-src-a", "tx-src-b"}


def test_will_api_http_roundtrip(tmp_path: Path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import agents.agent_memory_core as core_module
    import agents.agent_memory_lifecycle as lifecycle_module
    import agents.agent_memory_migration as migration_module
    import agents.agent_memory_transfer as transfer_module
    from agents.agent_memory_migration import MemoryMigrationService
    from agents.agent_memory_routes import hub_router
    from agents.agent_memory_transfer import AgentMemoryTransfer

    store = AgentMemoryStore(tmp_path)
    lifecycle = AgentMemoryLifecycle(store=store)
    service = MemoryMigrationService(store=store, lifecycle=lifecycle)
    transfer = AgentMemoryTransfer(store=store, lifecycle=lifecycle, migration=service)
    monkeypatch.setattr(core_module, "_store", store)
    monkeypatch.setattr(lifecycle_module, "_lifecycle", lifecycle)
    monkeypatch.setattr(migration_module, "_migration", service)
    monkeypatch.setattr(transfer_module, "_transfer", transfer)

    source = AgentMemoryCore("t", "src", store=store)
    _seed(source, "HTTP")

    app = FastAPI()
    app.include_router(hub_router)
    client = TestClient(app)
    created = client.post(
        "/api/v1/agent-memory/t/src/wills",
        json={
            "beneficiary": "dst",
            "strategy": "merge",
            "layers": ["log", "semantic"],
            "keep_memorial": False,
        },
    )
    assert created.status_code == 200
    will_id = created.json()["will"]["will_id"]
    preflight = client.post(f"/api/v1/agent-memory/wills/{will_id}/preflight")
    assert preflight.status_code == 200 and preflight.json()["report"]["ok"]
    fetched = client.get(f"/api/v1/agent-memory/wills/{will_id}")
    assert fetched.status_code == 200
    assert fetched.json()["will"]["will_id"] == will_id
    executed = client.post(
        f"/api/v1/agent-memory/wills/{will_id}/execute",
        json={"idempotency_key": will_id},
    )
    assert executed.status_code == 200 and executed.json()["state"] == "executed"
    inherited = client.get("/api/v1/agent-memory/t/dst/inherited")
    assert inherited.status_code == 200
    assert inherited.json()["inherited"]["partitions"]
