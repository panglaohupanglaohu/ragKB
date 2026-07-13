# -*- coding: utf-8 -*-
"""Plan → TaskHabitatContract — 物竞天择 v4 XG-2.

把 Plaza ExecutionPlan（或已派发任务列表）编译为物竞生境契约：
  步骤 → 有序生态位 + 步数/世代预算 + skill_universe
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agents.execution_plan import (
    ExecutionPlan,
    PlanStep,
    infer_skills_for_step,
)


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def _base_ticks(n_skills: int) -> int:
    return max(8, 12 + 4 * max(n_skills, 1))


@dataclass
class NicheWindow:
    step_id: str = ""
    index: int = 0
    title: str = ""
    demanded_skills: List[str] = field(default_factory=list)
    responsible_role: str = ""
    acceptance: str = ""
    base_ticks: int = 12
    depends_on: List[str] = field(default_factory=list)
    inferred_skills: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "index": self.index,
            "title": self.title,
            "demanded_skills": list(self.demanded_skills),
            "responsible_role": self.responsible_role,
            "acceptance": self.acceptance,
            "base_ticks": self.base_ticks,
            "depends_on": list(self.depends_on),
            "inferred_skills": self.inferred_skills,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NicheWindow":
        return cls(
            step_id=str(d.get("step_id", "")),
            index=int(d.get("index", 0) or 0),
            title=str(d.get("title", "")),
            demanded_skills=list(d.get("demanded_skills") or []),
            responsible_role=str(d.get("responsible_role", "")),
            acceptance=str(d.get("acceptance", "")),
            base_ticks=int(d.get("base_ticks", 12) or 12),
            depends_on=list(d.get("depends_on") or []),
            inferred_skills=bool(d.get("inferred_skills", False)),
        )


@dataclass
class TaskHabitatContract:
    plan_id: str = ""
    plaza_id: str = ""
    discussion_id: str = ""
    topic: str = ""
    goal: str = ""
    revision: int = 1
    niches: List[NicheWindow] = field(default_factory=list)
    step_budget: Dict[str, Any] = field(default_factory=dict)
    skill_universe: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plaza_id": self.plaza_id,
            "discussion_id": self.discussion_id,
            "topic": self.topic,
            "goal": self.goal,
            "revision": self.revision,
            "niches": [n.to_dict() for n in self.niches],
            "step_budget": dict(self.step_budget),
            "skill_universe": list(self.skill_universe),
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TaskHabitatContract":
        niches = [NicheWindow.from_dict(x) for x in (d.get("niches") or [])]
        return cls(
            plan_id=str(d.get("plan_id", "")),
            plaza_id=str(d.get("plaza_id", "")),
            discussion_id=str(d.get("discussion_id", "")),
            topic=str(d.get("topic", "")),
            goal=str(d.get("goal", "")),
            revision=int(d.get("revision", 1) or 1),
            niches=niches,
            step_budget=dict(d.get("step_budget") or {}),
            skill_universe=list(d.get("skill_universe") or []),
            provenance=dict(d.get("provenance") or {}),
        )


def _fingerprint(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _topo_sort_steps(steps: List[PlanStep]) -> List[PlanStep]:
    """按依赖拓扑序；无依赖或解析失败时按 index 稳定排序."""
    by_index = {str(s.index): s for s in steps}
    by_title = {s.title: s for s in steps if s.title}
    by_id = {s.step_id: s for s in steps if s.step_id}

    def resolve_dep(tok: str) -> Optional[str]:
        t = str(tok).strip()
        if t in by_id:
            return by_id[t].step_id
        if t in by_title:
            return by_title[t].step_id
        m = re.search(r"\d+", t)
        if m and m.group(0) in by_index:
            return by_index[m.group(0)].step_id
        return None

    deps: Dict[str, List[str]] = {}
    for s in steps:
        sid = s.step_id or f"s{s.index}"
        resolved = []
        for d in s.dependencies or []:
            r = resolve_dep(d)
            if r and r != sid:
                resolved.append(r)
        deps[sid] = resolved

    remaining = {s.step_id or f"s{s.index}": s for s in steps}
    ordered: List[PlanStep] = []
    while remaining:
        ready = [
            sid for sid, s in remaining.items()
            if all(d not in remaining for d in deps.get(sid, []))
        ]
        if not ready:
            # 环：按 index 排出剩余
            ordered.extend(sorted(remaining.values(), key=lambda x: int(x.index or 0)))
            break
        ready.sort(key=lambda sid: int(remaining[sid].index or 0))
        for sid in ready:
            ordered.append(remaining.pop(sid))
    return ordered


def compile_plan_to_habitat_contract(
    plan: Any,
    *,
    extra_skills: Optional[List[str]] = None,
) -> TaskHabitatContract:
    """ExecutionPlan 或 plan dict → TaskHabitatContract."""
    if isinstance(plan, ExecutionPlan):
        ep = plan
    else:
        ep = ExecutionPlan.from_dict(plan or {})
    if not ep.steps:
        raise ValueError("计划无步骤，无法编译为 TaskHabitatContract")

    ordered = _topo_sort_steps(list(ep.steps))
    niches: List[NicheWindow] = []
    universe: List[str] = []
    for s in ordered:
        explicit = list(s.required_skills or [])
        skills, inferred = infer_skills_for_step(
            title=s.title,
            description=s.description,
            responsible_role=s.responsible_role,
            explicit=explicit or None,
        )
        # 若已有 skills 且不是纯 generic 推断误伤：explicit 优先
        if explicit:
            skills, inferred = explicit, False
        bt = _base_ticks(len(skills))
        niches.append(NicheWindow(
            step_id=s.step_id,
            index=int(s.index or 0),
            title=s.title,
            demanded_skills=skills,
            responsible_role=s.responsible_role,
            acceptance=s.acceptance,
            base_ticks=bt,
            depends_on=list(s.dependencies or []),
            inferred_skills=inferred,
        ))
        for sk in skills:
            if sk not in universe:
                universe.append(sk)

    for sk in extra_skills or []:
        if sk and sk not in universe:
            universe.append(sk)

    total_ticks = sum(n.base_ticks for n in niches) or 40
    max_steps = _clamp(total_ticks, 40, 500)
    max_gens = _clamp(2 + math.ceil(len(niches) / 3), 1, 10)

    body = {
        "plan_id": ep.plan_id,
        "revision": ep.revision,
        "niches": [(n.step_id, n.demanded_skills, n.base_ticks) for n in niches],
    }
    fp = _fingerprint(body)

    return TaskHabitatContract(
        plan_id=ep.plan_id,
        plaza_id=ep.plaza_id,
        discussion_id=ep.discussion_id,
        topic=ep.topic,
        goal=ep.goal,
        revision=ep.revision,
        niches=niches,
        step_budget={
            "max_steps_per_generation": max_steps,
            "max_generations": max_gens,
            "era": {},
        },
        skill_universe=universe,
        provenance={
            "source": "plan",
            "fingerprint": fp,
            "n_niches": len(niches),
        },
    )


def compile_tasks_to_habitat_contract(
    tasks: List[Dict[str, Any]],
    *,
    agent_skills_map: Optional[Dict[str, List[str]]] = None,
    team_skill_ids: Optional[List[str]] = None,
) -> TaskHabitatContract:
    """从 AgentTask 字典列表反编译（metadata.plan/step/skills）.

    agent_skills_map: {agent_id: [skill_id,...]} — 优先用执行人真实基因组作 demand，
    使生境选择压力对准团队已有 skill（闭环关键，避免启发式 skill 名对不上 genome）。
    """
    if not tasks:
        raise ValueError("任务列表为空")

    agent_skills_map = agent_skills_map or {}
    niches: List[NicheWindow] = []
    universe: List[str] = []
    plan_id = ""
    plaza_id = ""
    discussion_id = ""
    topic = ""

    for i, t in enumerate(tasks):
        meta = t.get("metadata") or {}
        plan_id = plan_id or str(meta.get("plan_id") or "")
        plaza_id = plaza_id or str(meta.get("plaza_id") or "")
        discussion_id = discussion_id or str(meta.get("discussion_id") or "")
        topic = topic or str(meta.get("discussion_topic") or t.get("title") or "")
        skills = list(meta.get("required_skills") or meta.get("skills_used") or t.get("required_skills") or [])
        role = str(meta.get("responsible_role") or meta.get("role") or "")
        title = str(t.get("title") or f"任务{i + 1}")
        agent_id = str(t.get("agent_id") or meta.get("agent_id") or "")
        inferred = False
        # 1) 执行人 genome 2) 显式 skills 3) 角色/标题启发式
        if not skills and agent_id and agent_skills_map.get(agent_id):
            skills = list(agent_skills_map[agent_id])[:4]
            inferred = True
        if not skills:
            skills, inferred = infer_skills_for_step(
                title=title, description=str(t.get("description") or ""),
                responsible_role=role,
            )
        # 过滤空壳 generic-only 若团队有 skill 池可叠加
        if skills == ["generic"] and team_skill_ids:
            skills = list(team_skill_ids)[:3]
            inferred = True
        bt = _base_ticks(len(skills))
        niches.append(NicheWindow(
            step_id=str(meta.get("step_id") or t.get("task_id") or f"task-{i + 1}"),
            index=i + 1,
            title=title,
            demanded_skills=skills,
            responsible_role=role or agent_id,
            acceptance=str(meta.get("acceptance_test") or meta.get("expected_artifacts") or ""),
            base_ticks=bt,
            depends_on=list(t.get("dependencies") or []),
            inferred_skills=inferred,
        ))
        for sk in skills:
            if sk not in universe:
                universe.append(sk)

    for sk in team_skill_ids or []:
        if sk and sk not in universe:
            universe.append(sk)

    total_ticks = sum(n.base_ticks for n in niches) or 40
    max_steps = _clamp(total_ticks, 40, 500)
    max_gens = _clamp(2 + math.ceil(len(niches) / 3), 1, 10)
    fp = _fingerprint({"plan_id": plan_id, "niches": [n.to_dict() for n in niches]})

    return TaskHabitatContract(
        plan_id=plan_id or f"tasks-{fp}",
        plaza_id=plaza_id,
        discussion_id=discussion_id,
        topic=topic,
        goal=topic,
        niches=niches,
        step_budget={
            "max_steps_per_generation": max_steps,
            "max_generations": max_gens,
            "era": {},
        },
        skill_universe=universe,
        provenance={
            "source": "tasks",
            "fingerprint": fp,
            "n_niches": len(niches),
            "used_agent_skills": bool(agent_skills_map),
        },
    )


def validate_habitat_contract(contract: TaskHabitatContract) -> List[Dict[str, str]]:
    """空 niches 失败；技能可空但标记."""
    issues: List[Dict[str, str]] = []
    if not contract.niches:
        issues.append({"field": "niches", "message": "契约无生态位（niches 为空）"})
        return issues
    for n in contract.niches:
        if not n.demanded_skills:
            issues.append({
                "field": "demanded_skills",
                "step_id": n.step_id,
                "message": f"步骤「{n.title}」无 demanded_skills",
            })
    return issues
