# -*- coding: utf-8 -*-
"""M1-3 计划→场景编译桥 回归测试."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))

import pytest

from agents.execution_plan import ExecutionPlan, PlanStep
from sandbox.plan_scenario_bridge import (
    compile_plan_to_scenario, PlanCompileError,
    validate_plan_feasibility, assign_plan_to_twin,
    compile_task_to_scenario, assign_task_to_twin,
)
from sandbox.scenario_models import validate_scenario


def _plan() -> ExecutionPlan:
    plan = ExecutionPlan(
        plan_id="plan-abc123", plaza_id="plz-1", discussion_id="disc-1",
        topic="容量扩容评审", goal="安全完成扩容并通过评审",
    )
    plan.steps = [
        PlanStep(step_id="plan-abc123-s1", index=1, title="调研现状",
                 responsible_role="researcher", acceptance="现状报告",
                 dependencies=[], required_skills=["analysis"]),
        PlanStep(step_id="plan-abc123-s2", index=2, title="实施扩容",
                 responsible_role="engineer", acceptance="扩容完成",
                 dependencies=["1"], required_skills=["terraform", "analysis"]),
        PlanStep(step_id="plan-abc123-s3", index=3, title="评审交付",
                 responsible_role="reviewer", acceptance="评审通过",
                 dependencies=["步骤2"], required_skills=["code_review"]),
    ]
    return plan


def test_compile_plan_produces_valid_scenario():
    spec = compile_plan_to_scenario(_plan().to_dict())
    assert spec.source == "plan"
    assert spec.scenario_id == "plan_plan-abc123"
    # 三步 → 三房间(阶段递增) + 三任务
    assert len(spec.world.rooms) == 3
    assert [r.stage for r in spec.world.rooms] == [1, 2, 3]
    assert len(spec.taskflow) == 3
    # 编译产物必须自洽（无环 / 引用合法）
    assert validate_scenario(spec.to_dict()) == []


def test_dependencies_resolved_to_earlier_step_ids():
    spec = compile_plan_to_scenario(_plan().to_dict())
    tasks = {t.task_id: t for t in spec.taskflow}
    # 数字序号 "1" 与 "步骤2" 都被解析成上游 step_id
    assert tasks["plan-abc123-s2"].depends_on == ["plan-abc123-s1"]
    assert tasks["plan-abc123-s3"].depends_on == ["plan-abc123-s2"]
    # 角色按 responsible_role 聚合，技能并入
    roles = {r.role: r for r in spec.roles}
    assert set(roles) == {"researcher", "engineer", "reviewer"}
    assert "terraform" in roles["engineer"].required_skills


def test_origin_carried_in_tags():
    spec = compile_plan_to_scenario(_plan().to_dict())
    assert "source:plan" in spec.tags
    assert "plaza:plz-1" in spec.tags
    assert "discussion:disc-1" in spec.tags
    assert "plan:plan-abc123" in spec.tags


def test_forward_and_cyclic_dependencies_dropped():
    """依赖指向自身/更后步骤 → 丢弃，保证无环。"""
    plan = ExecutionPlan(plan_id="p2", topic="t", goal="g")
    plan.steps = [
        PlanStep(step_id="p2-s1", index=1, title="A", responsible_role="r1",
                 dependencies=["2"], required_skills=[]),          # 依赖更后步骤 → 丢
        PlanStep(step_id="p2-s2", index=2, title="B", responsible_role="r2",
                 dependencies=["1", "2"], required_skills=[]),     # 自依赖 "2" → 丢，保留 "1"
    ]
    spec = compile_plan_to_scenario(plan.to_dict())
    tasks = {t.task_id: t for t in spec.taskflow}
    assert tasks["p2-s1"].depends_on == []
    assert tasks["p2-s2"].depends_on == ["p2-s1"]
    assert validate_scenario(spec.to_dict()) == []


def test_empty_plan_raises():
    plan = ExecutionPlan(plan_id="empty", topic="t", goal="g")
    with pytest.raises(PlanCompileError):
        compile_plan_to_scenario(plan.to_dict())


# ── M1-2 落地性审查 ──────────────────────────────────────────

def test_feasibility_gate_flags_missing_fields():
    """缺 负责角色/验收/技能 的步骤被逐项标记。"""
    plan = ExecutionPlan(plan_id="p3", topic="t", goal="g")
    plan.steps = [
        PlanStep(step_id="p3-s1", index=1, title="残缺步",
                 responsible_role="", acceptance="", required_skills=[]),
    ]
    issues = validate_plan_feasibility(plan.to_dict())
    fields = {i["field"] for i in issues}
    assert fields == {"responsible_role", "acceptance", "required_skills"}


def test_feasibility_gate_passes_complete_plan():
    issues = validate_plan_feasibility(_plan().to_dict())
    assert issues == []


def test_feasibility_empty_plan():
    issues = validate_plan_feasibility(ExecutionPlan(plan_id="e").to_dict())
    assert issues and issues[0]["field"] == "steps"


# ── M1-4 派发到孪生 ──────────────────────────────────────────

class _MemStore:
    """内存 store 桩，复刻 save() 的 source 保留语义。"""
    def __init__(self):
        self.saved = {}

    def save(self, spec):
        self.saved[spec.scenario_id] = spec
        return {"ok": True, "scenario_id": spec.scenario_id}


def test_assign_plan_to_twin_gates_infeasible():
    plan = ExecutionPlan(plan_id="bad")
    plan.steps = [PlanStep(step_id="bad-s1", index=1, title="残缺",
                           responsible_role="", acceptance="", required_skills=[])]
    store = _MemStore()
    res = assign_plan_to_twin(plan.to_dict(), store=store)
    assert res["ok"] is False
    assert res["stage"] == "feasibility"
    assert res["issues"]
    assert store.saved == {}          # 审查不过不落库


def test_assign_plan_to_twin_compiles_and_persists():
    store = _MemStore()
    res = assign_plan_to_twin(_plan().to_dict(), store=store)
    assert res["ok"] is True
    assert res["scenario_id"] == "plan_plan-abc123"
    assert res["source"] == "plan"
    spec = store.saved["plan_plan-abc123"]
    assert spec.source == "plan"
    assert validate_scenario(spec.to_dict()) == []


# ── M1-6 任务→场景入口 ───────────────────────────────────────


def _task(status="completed", **kw):
    base = {
        "task_id": "t-run-001", "title": "实现 API 接口",
        "description": "用 Python FastAPI 实现 /api/v1/users 接口并写测试",
        "status": status, "team_id": "team-a", "agent_id": "dev-1",
        "metadata": {"plan_id": "plan-xyz", "step_id": "plan-xyz-s2",
                      "responsible_role": "developer", "required_skills": ["python", "testing"]},
    }
    base.update(kw)
    return base


def test_compile_task_produces_valid_scenario():
    spec = compile_task_to_scenario(_task())
    assert spec.source == "plan"
    assert spec.scenario_id == "task_t-run-001"
    assert len(spec.world.rooms) == 1
    assert len(spec.taskflow) == 1
    assert validate_scenario(spec.to_dict()) == []


def test_compile_task_origin_carried_in_tags():
    spec = compile_task_to_scenario(_task())
    assert "source:task" in spec.tags
    assert "task:t-run-001" in spec.tags
    assert "plan:plan-xyz" in spec.tags
    assert "step:plan-xyz-s2" in spec.tags
    assert "team:team-a" in spec.tags


def test_compile_task_rejects_unrun_task():
    """未运行过的任务被拒并提示先派发。"""
    with pytest.raises(PlanCompileError, match="未运行过"):
        compile_task_to_scenario(_task(status="pending"))


def test_compile_task_skill_inference_from_description():
    """metadata 无 required_skills 时从描述推断。"""
    task = _task(metadata={"plan_id": "p1"})
    spec = compile_task_to_scenario(task)
    skills = spec.taskflow[0].required_skills
    assert "testing" in skills


def test_assign_task_to_twin_compiles_and_persists():
    store = _MemStore()
    res = assign_task_to_twin(_task(), store=store)
    assert res["ok"] is True
    assert res["scenario_id"] == "task_t-run-001"
    assert res["source"] == "plan"
    spec = store.saved["task_t-run-001"]
    assert validate_scenario(spec.to_dict()) == []

