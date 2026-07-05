# -*- coding: utf-8 -*-
"""Plan → Scenario 编译桥 (数字办公室协作演练 M1-3).

把 Plaza 讨论收敛出的 ExecutionPlan(dict) 编译为可被孪生演练的 ScenarioSpec，
source='plan'，让「讨论产出的计划」而非硬编码测试样例成为孪生的演练目标。

设计约束（对齐 scenario_models.validate_scenario）:
  - 每个 PlanStep → 一个业务阶段房间(stage=index) + 一个 taskflow 任务。
  - 依赖只解析到 index 更小的步骤 → 天然无环，通过 validate_scenario 的环检测。
  - 角色按 responsible_role 聚合为 RoleRequirement（真实团队匹配度用）。
  - origin 暂存于 tags（["source:plan","plaza:<id>",...]），M1-1 落地 origin 字段后可提升。

无跨层耦合: 只 import sandbox.scenario_models，输入是 plan dict（ExecutionPlan.to_dict()）。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .scenario_models import (
    RoleRequirement,
    RoomSpec,
    ScenarioRubric,
    ScenarioSpec,
    ScenarioTask,
    ScenarioWorld,
    validate_scenario,
)


class PlanCompileError(Exception):
    """计划编译为场景失败（带字段级错误）."""

    def __init__(self, message: str, errors: List[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


def validate_plan_feasibility(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """M1-2 落地性审查（对齐 P6-2）——委托唯一实现 execution_plan.validate_plan(profile='twin').

    Review 修复(1): 曾与 agents/execution_plan.validate_plan 并存两套规则（本处不查
    依赖悬空/标题有效性，彼处不查技能），必然漂移。现统一: 基础规则 + twin 档叠加
    required_skills。本函数仅做 dict→ExecutionPlan 适配与 issue 形状映射（兼容既有调用）。
    """
    from agents.execution_plan import ExecutionPlan, validate_plan as _validate_plan

    ep = plan if isinstance(plan, ExecutionPlan) else ExecutionPlan.from_dict(plan or {})
    return [
        {"step": i.get("step_id") or None, "field": i["field"], "issue": i["message"]}
        for i in _validate_plan(ep, profile="twin")
    ]


def assign_plan_to_twin(plan: Dict[str, Any], store: Any = None) -> Dict[str, Any]:
    """M1-4 派发到孪生: 落地性审查 → 编译 → 落库 → 返回 scenario_id。

    审查不过/编译失败/落库失败均返回 {ok:False, stage, issues|errors}，不写库。
    """
    issues = validate_plan_feasibility(plan)
    if issues:
        return {"ok": False, "stage": "feasibility", "issues": issues}
    try:
        spec = compile_plan_to_scenario(plan)
    except PlanCompileError as e:
        return {"ok": False, "stage": "compile", "error": str(e), "errors": e.errors}
    if store is None:
        from .scenario_store import get_scenario_store
        store = get_scenario_store()
    res = store.save(spec)
    if not res.get("ok"):
        return {"ok": False, "stage": "persist", **res}
    return {"ok": True, "scenario_id": res["scenario_id"], "source": "plan"}


def _resolve_dep_indices(dep_tokens: List[str], by_index: Dict[str, dict],
                         by_title: Dict[str, dict]) -> List[int]:
    """把一步的依赖 token（序号/标题）解析为被依赖步骤的 index 列表."""
    resolved: List[int] = []
    for tok in dep_tokens or []:
        t = str(tok).strip()
        if not t:
            continue
        # 优先数字序号（"步骤1" / "1" / "S1" 都能抽出 1）
        m = re.search(r"\d+", t)
        target = None
        if m and m.group(0) in by_index:
            target = by_index[m.group(0)]
        elif t in by_title:
            target = by_title[t]
        if target is not None:
            idx = int(target.get("index", 0))
            if idx and idx not in resolved:
                resolved.append(idx)
    return resolved


def compile_plan_to_scenario(plan: Dict[str, Any]) -> ScenarioSpec:
    """ExecutionPlan(dict) → ScenarioSpec(source='plan').

    Raises:
        PlanCompileError: 计划无步骤，或编译产物未通过 validate_scenario。
    """
    steps = list(plan.get("steps", []) or [])
    if not steps:
        raise PlanCompileError("计划无步骤，无法编译为场景")

    # 稳定 index：缺失或重复的 index 用序位补齐，保证房间 stage / 依赖解析可用
    for i, s in enumerate(steps):
        if not s.get("index"):
            s["index"] = i + 1
    steps.sort(key=lambda s: int(s.get("index", 0)))

    by_index = {str(int(s.get("index", 0))): s for s in steps}
    by_title = {str(s.get("title", "")).strip(): s for s in steps if s.get("title")}

    plan_id = plan.get("plan_id", "") or "plan"
    plaza_id = plan.get("plaza_id", "")
    discussion_id = plan.get("discussion_id", "")

    def step_key(s: dict) -> str:
        return s.get("step_id") or f"{plan_id}-s{int(s.get('index', 0))}"

    rooms: List[RoomSpec] = []
    tasks: List[ScenarioTask] = []
    roles_map: Dict[str, RoleRequirement] = {}

    for s in steps:
        key = step_key(s)
        idx = int(s.get("index", 0))
        title = s.get("title", "") or f"步骤{idx}"
        skills = list(s.get("required_skills", []) or [])

        rooms.append(RoomSpec(room_id=key, name=title, stage=idx))

        # 依赖只连到 index 更小的步骤（无环保证）
        dep_indices = [d for d in _resolve_dep_indices(
            list(s.get("dependencies", []) or []), by_index, by_title) if d < idx]
        depends_on = [step_key(by_index[str(d)]) for d in dep_indices if str(d) in by_index]

        tasks.append(ScenarioTask(
            task_id=key, name=title, room_id=key,
            required_skills=skills, depends_on=depends_on,
            base_duration_steps=3, reward=0.5, failure_penalty=0.1,
        ))

        role = (s.get("responsible_role", "") or "").strip()
        if role:
            rr = roles_map.get(role)
            if rr is None:
                rr = roles_map[role] = RoleRequirement(role=role, min_count=1)
            for sk in skills:
                if sk not in rr.required_skills:
                    rr.required_skills.append(sk)

    name = plan.get("topic") or plan.get("goal") or f"计划演练 {plan_id}"
    description = (plan.get("goal") or plan.get("topic") or "").strip() \
        or f"由 Plaza 讨论计划 {plan_id} 编译而来的孪生演练场景。"

    origin_tags = ["source:plan", f"plan:{plan_id}"]
    if plaza_id:
        origin_tags.append(f"plaza:{plaza_id}")
    if discussion_id:
        origin_tags.append(f"discussion:{discussion_id}")

    spec = ScenarioSpec(
        scenario_id=f"plan_{plan_id}",
        name=str(name)[:80],
        category="general",
        description=description,
        world=ScenarioWorld(rooms=rooms),
        taskflow=tasks,
        roles=list(roles_map.values()),
        rubric=ScenarioRubric(),
        tags=origin_tags,
        source="plan",
        recommended_max_steps=max(30, len(steps) * 20),
    )

    errors = validate_scenario(spec.to_dict())
    if errors:
        raise PlanCompileError(f"计划 {plan_id} 编译产物非法", errors)
    return spec


# ── M1-6: 任务→场景入口 ──────────────────────────────────────


def compile_task_to_scenario(task: Dict[str, Any]) -> ScenarioSpec:
    """M1-6: 从一个运行过的任务编译为可演练场景。

    演练对象是「执行计划对应的任务」——凡在智能体团队运行过的任务
    （task_engine 有运行记录）皆可进入演练。

    从任务的 metadata（plan_id/step_id/trace_context）+ 描述 +
    所属团队实际构型编译场景；批准门天然满足（运行过⇒已批准派发）。

    Raises:
        PlanCompileError: 任务未运行过 / 无有效字段。
    """
    task_id = task.get("task_id", "") or ""
    status = task.get("status", "") or ""
    if status not in ("running", "completed", "failed", "cancelled"):
        raise PlanCompileError(
            f"任务 {task_id} 未运行过（status={status}），请先派发到团队执行",
        )

    title = task.get("title", "") or task_id or "任务演练"
    description = task.get("description", "") or title
    team_id = task.get("team_id", "") or ""
    agent_id = task.get("agent_id", "") or ""
    metadata = task.get("metadata", {}) or {}

    # 溯源元数据
    plan_id = str(metadata.get("plan_id", "") or "")
    step_id = str(metadata.get("step_id", "") or "")
    responsible_role = str(metadata.get("responsible_role", "") or metadata.get("role", "") or "")

    # 所需技能：从 metadata 或任务描述中提取
    required_skills = list(metadata.get("required_skills", []) or [])
    if not required_skills:
        # 兜底：从 description 关键词推断
        desc_lower = description.lower()
        skill_hints = {
            "code_review": ["review", "审查", "评审"],
            "analysis": ["分析", "调研", "research"],
            "terraform": ["terraform", "基础设施"],
            "testing": ["测试", "test", "qa"],
            "deployment": ["部署", "deploy", "发布"],
        }
        for skill, keywords in skill_hints.items():
            if any(kw in desc_lower for kw in keywords):
                required_skills.append(skill)

    # 编译为单任务场景
    room_id = f"task_{task_id}"
    origin_tags = ["source:task", f"task:{task_id}"]
    if plan_id:
        origin_tags.append(f"plan:{plan_id}")
    if step_id:
        origin_tags.append(f"step:{step_id}")
    if team_id:
        origin_tags.append(f"team:{team_id}")

    role_label = responsible_role or agent_id or "executor"
    roles_map: Dict[str, RoleRequirement] = {
        role_label: RoleRequirement(role=role_label, min_count=1, required_skills=required_skills)
    }

    spec = ScenarioSpec(
        scenario_id=f"task_{task_id}",
        name=str(title)[:80],
        category="general",
        description=description[:200],
        world=ScenarioWorld(rooms=[RoomSpec(room_id=room_id, name=title[:40], stage=1)]),
        taskflow=[ScenarioTask(
            task_id=room_id, name=title, room_id=room_id,
            required_skills=required_skills, depends_on=[],
            base_duration_steps=5, reward=0.5, failure_penalty=0.1,
        )],
        roles=list(roles_map.values()),
        rubric=ScenarioRubric(),
        tags=origin_tags,
        source="plan",  # 复用 source=plan 菜单分区
        recommended_max_steps=40,
    )

    errors = validate_scenario(spec.to_dict())
    if errors:
        raise PlanCompileError(f"任务 {task_id} 编译产物非法", errors)
    return spec


def assign_task_to_twin(task: Dict[str, Any], store: Any = None) -> Dict[str, Any]:
    """M1-6: 任务→孪生入口: 编译 → 落库 → 返回 scenario_id。

    运行过的任务天然满足批准门，无需审查。
    """
    try:
        spec = compile_task_to_scenario(task)
    except PlanCompileError as e:
        return {"ok": False, "stage": "compile", "error": str(e), "errors": e.errors}
    if store is None:
        from .scenario_store import get_scenario_store
        store = get_scenario_store()
    res = store.save(spec)
    if not res.get("ok"):
        return {"ok": False, "stage": "persist", **res}
    return {"ok": True, "scenario_id": res["scenario_id"], "source": "plan"}
