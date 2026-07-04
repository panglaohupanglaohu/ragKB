# -*- coding: utf-8 -*-
"""P5-1/P6-2/P5-2: 结构化执行计划契约 + 落地性审查 + 派发闭环 测试."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agents import plaza_engine as plaza_engine_module
from agents import plaza_routes
from agents.execution_plan import (
    ExecutionPlan,
    PlanStep,
    build_plan_from_text,
    load_plan_from_discussion,
    save_plan_to_discussion,
    validate_plan,
)
from agents.plaza_engine import PlazaEngine
from agents.plaza_store import PlazaStore


GOOD_PLAN = (
    "## 执行计划\n"
    "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
    "|---|---|---|---|---|---|\n"
    "| 1 | 调研现状并整理约束 | researcher | P0 | 无 | 调研报告 |\n"
    "| 2 | 设计并实现方案 | developer | P1 | 1 | 可运行补丁 |\n"
    "| 3 | 回归验证 | qa | P1 | 2 | pytest 报告 |\n"
)

BAD_PLAN = (
    "## 执行计划\n"
    "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
    "|---|---|---|---|---|---|\n"
    "| 1 | 做点什么 |  | P0 | 9 |  |\n"
)


@pytest.fixture
def isolated_plaza_engine(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        engine = PlazaEngine()
        engine._store = PlazaStore(base_dir=Path(tmpdir))
        engine._plazas = {}
        monkeypatch.setattr(plaza_engine_module, "_engine", engine)
        yield engine


def _seed(engine, plan_text=GOOD_PLAN):
    plaza = engine.create_plaza("契约广场", "plan")
    disc = engine.create_discussion(plaza.id, "把计划变成任务", "plan", "", 3)
    disc.plan = {"revision": 2, "content": plan_text}
    engine._store.save_plaza(plaza)
    return plaza, disc


class TestPlanContract:
    def test_build_from_text_produces_structured_steps(self):
        plan = build_plan_from_text(GOOD_PLAN, topic="t", goal="g")
        assert len(plan.steps) == 3
        s2 = plan.steps[1]
        assert s2.title == "设计并实现方案"
        assert s2.responsible_role == "developer"
        assert s2.acceptance == "可运行补丁"
        assert s2.dependencies == ["1"]
        assert plan.status == "draft"

    def test_validate_good_plan_passes(self):
        assert validate_plan(build_plan_from_text(GOOD_PLAN)) == []

    def test_validate_flags_missing_fields_and_bad_deps(self):
        issues = validate_plan(build_plan_from_text(BAD_PLAN))
        fields = {i["field"] for i in issues}
        assert "responsible_role" in fields
        assert "acceptance" in fields
        assert "dependencies" in fields  # 依赖 9 无法解析

    def test_validate_empty_plan(self):
        issues = validate_plan(ExecutionPlan())
        assert issues and issues[0]["field"] == "steps"

    def test_roundtrip_serialization(self):
        plan = build_plan_from_text(GOOD_PLAN, plaza_id="p", discussion_id="d")
        clone = ExecutionPlan.from_dict(plan.to_dict())
        assert clone.to_dict() == plan.to_dict()

    def test_refresh_status_completes_when_all_steps_done(self):
        plan = build_plan_from_text(GOOD_PLAN)
        plan.status = "dispatched"
        for s in plan.steps:
            s.status = "completed"
        plan.refresh_status()
        assert plan.status == "completed"


class TestPlanEndpoints:
    @pytest.mark.asyncio
    async def test_get_builds_and_persists_structured_plan(self, isolated_plaza_engine):
        plaza, disc = _seed(isolated_plaza_engine)
        resp = await plaza_routes.get_execution_plan(plaza.id, disc.id)
        assert resp["issues"] == []
        assert len(resp["plan"]["steps"]) == 3
        assert resp["dispatchable"] is False  # 未批准
        assert load_plan_from_discussion(disc) is not None

    @pytest.mark.asyncio
    async def test_approve_rejects_infeasible_plan(self, isolated_plaza_engine):
        plaza, disc = _seed(isolated_plaza_engine, BAD_PLAN)
        await plaza_routes.get_execution_plan(plaza.id, disc.id)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await plaza_routes.approve_execution_plan(
                plaza.id, disc.id, plaza_routes.ApprovePlanRequest(),
            )
        assert exc.value.status_code == 422
        assert exc.value.detail["issues"]

    @pytest.mark.asyncio
    async def test_dispatch_requires_approval_then_binds_tasks(
        self, isolated_plaza_engine, monkeypatch,
    ):
        plaza, disc = _seed(isolated_plaza_engine)
        await plaza_routes.get_execution_plan(plaza.id, disc.id)

        created = []

        async def fake_submit_internal_task(team_id, **kwargs):
            from agents.task_engine import AgentTask
            task = AgentTask(team_id=team_id, title=kwargs.get("title", ""))
            created.append(task)
            return task

        from agents import api as api_module
        monkeypatch.setattr(api_module, "_submit_internal_task", fake_submit_internal_task)

        # 未批准 → 派发被落地性关卡拦下
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await plaza_routes._dispatch_discussion_tasks(
                plaza.id, disc, "team-x", auto_start=False,
            )
        assert "尚未批准" in str(exc.value.detail)

        # 批准 → 派发成功，步骤↔任务绑定，计划进入 dispatched
        await plaza_routes.approve_execution_plan(
            plaza.id, disc.id, plaza_routes.ApprovePlanRequest(approved_by="owner"),
        )
        tasks = await plaza_routes._dispatch_discussion_tasks(
            plaza.id, disc, "team-x", auto_start=False,
        )
        assert len(tasks) == 3
        plan = load_plan_from_discussion(disc)
        assert plan.status == "dispatched"
        assert all(s.status == "dispatched" and s.task_id for s in plan.steps)

    @pytest.mark.asyncio
    async def test_step_status_feedback_completes_plan(self, isolated_plaza_engine):
        plaza, disc = _seed(isolated_plaza_engine)
        resp = await plaza_routes.get_execution_plan(plaza.id, disc.id)
        plan = load_plan_from_discussion(disc)
        plan.status = "dispatched"
        for s in plan.steps:
            s.status = "dispatched"
        save_plan_to_discussion(disc, plan)

        step_ids = [s["step_id"] for s in resp["plan"]["steps"]]
        for sid in step_ids[:-1]:
            out = await plaza_routes.update_plan_step_status(
                plaza.id, disc.id, sid,
                plaza_routes.PlanStepStatusRequest(status="completed"),
            )
            assert out["plan_status"] == "dispatched"
        out = await plaza_routes.update_plan_step_status(
            plaza.id, disc.id, step_ids[-1],
            plaza_routes.PlanStepStatusRequest(status="completed", task_id="t-9"),
        )
        assert out["plan_status"] == "completed"

    @pytest.mark.asyncio
    async def test_step_status_rejects_illegal_value(self, isolated_plaza_engine):
        plaza, disc = _seed(isolated_plaza_engine)
        resp = await plaza_routes.get_execution_plan(plaza.id, disc.id)
        sid = resp["plan"]["steps"][0]["step_id"]
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await plaza_routes.update_plan_step_status(
                plaza.id, disc.id, sid,
                plaza_routes.PlanStepStatusRequest(status="doing"),
            )
        assert exc.value.status_code == 400
