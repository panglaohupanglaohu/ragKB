# -*- coding: utf-8 -*-
"""v4 场景系统测试 — scenario_models / scenario_store / scenario_compiler (C-1.5)."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


# ── 模型与校验 ──────────────────────────────────────────────

def test_validate_minimal_scenario_ok():
    from sandbox.scenario_models import validate_scenario
    spec = {
        "name": "t", "category": "general",
        "world": {"rooms": [{"room_id": "r1", "name": "R1"}]},
        "taskflow": [{"task_id": "t1", "name": "T1", "room_id": "r1"}],
    }
    assert validate_scenario(spec) == []


def test_validate_detects_cycle():
    from sandbox.scenario_models import validate_scenario
    spec = {
        "name": "t",
        "world": {"rooms": [{"room_id": "r1", "name": "R1"}]},
        "taskflow": [
            {"task_id": "a", "name": "A", "depends_on": ["b"]},
            {"task_id": "b", "name": "B", "depends_on": ["a"]},
        ],
    }
    errors = validate_scenario(spec)
    assert any("环依赖" in e for e in errors)


def test_validate_detects_missing_fields_and_bad_refs():
    from sandbox.scenario_models import validate_scenario
    errors = validate_scenario({
        "name": "",
        "world": {"rooms": []},
        "taskflow": [{"task_id": "t1", "name": "T", "room_id": "ghost",
                      "depends_on": ["nope"]}],
        "chaos_script": [{"from_step": 10, "to_step": 5,
                          "events": [{"event_type": "alien_attack", "probability_per_step": 2}]}],
    })
    joined = "\n".join(errors)
    assert "name" in joined
    assert "rooms" in joined
    assert "ghost" in joined
    assert "nope" in joined
    assert "from_step > to_step" in joined
    assert "alien_attack" in joined
    assert "probability_per_step" in joined


def test_spec_roundtrip():
    from sandbox.scenario_models import ScenarioSpec
    d = {
        "scenario_id": "x1", "name": "X", "category": "incident",
        "world": {"rooms": [{"room_id": "r1", "name": "R1", "stage": 0}]},
        "taskflow": [{"task_id": "t1", "name": "T1", "room_id": "r1",
                      "required_skills": ["s1"], "reward": 0.6}],
        "rubric": {"skill_expectations": {"s1": 0.7}},
    }
    spec = ScenarioSpec.from_dict(d)
    d2 = spec.to_dict()
    assert d2["scenario_id"] == "x1"
    assert d2["taskflow"][0]["required_skills"] == ["s1"]
    assert d2["rubric"]["skill_expectations"]["s1"] == 0.7


# ── 场景库 ──────────────────────────────────────────────────

def test_store_loads_five_builtin_seeds():
    from sandbox.scenario_store import ScenarioStore
    store = ScenarioStore()
    ids = {s.scenario_id for s in store.list()}
    expected = {"cs_ticket_surge", "data_pipeline_recovery", "marketing_campaign",
                "code_review_delivery", "capacity_incident"}
    assert expected.issubset(ids), f"缺少种子场景: {expected - ids}"
    assert store.load_errors == []


def test_store_source_filter_partitions_builtin_and_plan():
    """M1-1: source 过滤区分内置样例与讨论产出计划场景。"""
    from sandbox.scenario_store import ScenarioStore
    from sandbox.scenario_models import ScenarioSpec, RoomSpec, ScenarioTask, ScenarioWorld
    store = ScenarioStore()
    # 内置样例: 5 个种子
    builtin = store.list(source="builtin")
    assert len(builtin) >= 5
    assert all(s.source == "builtin" for s in builtin)
    # 讨论产出: 初始为空
    assert store.list(source="plan") == []
    # 注入一个 plan 来源场景后，只在 source=plan 出现，不污染 builtin
    plan_spec = ScenarioSpec(
        scenario_id="plan_demo", name="计划演练demo", source="plan",
        world=ScenarioWorld(rooms=[RoomSpec(room_id="r1", name="调研", stage=0)]),
        taskflow=[ScenarioTask(task_id="t1", name="调研", room_id="r1")],
    )
    store._scenarios[plan_spec.scenario_id] = plan_spec
    assert [s.scenario_id for s in store.list(source="plan")] == ["plan_demo"]
    assert "plan_demo" not in {s.scenario_id for s in store.list(source="builtin")}
    # all / 空 → 全部
    assert store.list(source="all") == store.list()
    assert "plan_demo" in {s.scenario_id for s in store.list()}



def test_seed_scenarios_all_compile():
    from sandbox.scenario_store import ScenarioStore
    from sandbox.scenario_compiler import compile_scenario, build_chaos_timeline
    store = ScenarioStore()
    for spec in store.list():
        compiled = compile_scenario(spec, {})
        assert len(compiled["pending_tasks"]) >= 6, spec.scenario_id
        assert len(compiled["rooms"]) >= 4, spec.scenario_id
        assert len(build_chaos_timeline(spec)) >= 2, spec.scenario_id
        assert spec.rubric.skill_expectations, spec.scenario_id


def test_store_save_delete_custom_and_protect_builtin():
    from sandbox.scenario_store import ScenarioStore
    from sandbox.scenario_models import ScenarioSpec
    with tempfile.TemporaryDirectory() as tmp:
        store = ScenarioStore(custom_dir=Path(tmp))
        spec = ScenarioSpec.from_dict({
            "scenario_id": "custom_x", "name": "自定义", "category": "general",
            "world": {"rooms": [{"room_id": "r1", "name": "R1"}]},
            "taskflow": [{"task_id": "t1", "name": "T1", "room_id": "r1"}],
            "source": "custom",
        })
        assert store.save(spec)["ok"]
        assert store.get("custom_x") is not None
        assert (Path(tmp) / "custom_x.json").exists()
        # builtin 不可删
        assert not store.delete("cs_ticket_surge")["ok"]
        # custom 可删
        assert store.delete("custom_x")["ok"]
        assert store.get("custom_x") is None


def test_store_rejects_invalid_custom():
    from sandbox.scenario_store import ScenarioStore
    from sandbox.scenario_models import ScenarioSpec
    with tempfile.TemporaryDirectory() as tmp:
        store = ScenarioStore(custom_dir=Path(tmp))
        bad = ScenarioSpec(name="")  # 无房间无任务
        result = store.save(bad)
        assert not result["ok"]
        assert result.get("errors")


# ── 编译器 ──────────────────────────────────────────────────

def test_compile_failure_on_cycle():
    from sandbox.scenario_models import ScenarioSpec
    from sandbox.scenario_compiler import compile_scenario, ScenarioCompileError
    spec = ScenarioSpec.from_dict({
        "name": "bad",
        "world": {"rooms": [{"room_id": "r1", "name": "R1"}]},
        "taskflow": [
            {"task_id": "a", "name": "A", "room_id": "r1", "depends_on": ["b"]},
            {"task_id": "b", "name": "B", "room_id": "r1", "depends_on": ["a"]},
        ],
    })
    try:
        compile_scenario(spec, {})
        assert False, "应抛出 ScenarioCompileError"
    except ScenarioCompileError as e:
        assert e.details


def test_compile_marks_blocked_tasks():
    from sandbox.scenario_store import ScenarioStore
    from sandbox.scenario_compiler import compile_scenario
    spec = ScenarioStore().get("cs_ticket_surge")
    compiled = compile_scenario(spec, {})
    by_id = {t["id"]: t for t in compiled["pending_tasks"]}
    assert by_id["t1"]["blocked"] is False  # 无依赖
    assert by_id["t2"]["blocked"] is True   # 依赖 t1
    assert compiled["room_stages"]["intake"] == 0
    assert compiled["room_stages"]["callback"] == 4


def test_match_team_reports_missing_skills():
    from sandbox.scenario_store import ScenarioStore
    from sandbox.scenario_compiler import match_team
    spec = ScenarioStore().get("cs_ticket_surge")
    team = {"agents": [
        {"id": "a1", "role": "客服专员", "skills": ["ticket_intake", "reply_writing"]},
        {"id": "a2", "role": "分类专家", "skills": ["ticket_triage", "kb_search"]},
    ]}
    m = match_team(spec, team)
    assert 0 < m["match_rate"] < 1
    assert "escalation" in m["missing_skills"]
    assert any(r["role"] == "值班主管" and not r["satisfied"] for r in m["role_coverage"])


def test_room_stage_move_validation():
    from sandbox.world_state import WorldStateManager
    w = WorldStateManager()
    # 未设置 → 全放行
    assert w.validate_move("a", "b")["allowed"]
    w.set_room_stages({"intake": 0, "triage": 1, "reply": 3})
    assert w.validate_move("intake", "triage")["allowed"]
    assert w.validate_move("triage", "intake")["allowed"]   # 回退一步允许
    assert not w.validate_move("intake", "reply")["allowed"]  # 跳级禁止
    assert not w.validate_move("intake", "ghost")["allowed"]  # 不存在的房间
