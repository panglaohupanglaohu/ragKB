# -*- coding: utf-8 -*-
"""Scenario Models — 业务场景模型 (v4 A-1).

场景 = 可实例化的孪生环境模板，五要素:
world(房间/资源/约束) + taskflow(任务DAG) + roles(角色要求)
+ chaos_script(扰动剧本) + rubric(验收标准)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RoomSpec:
    """房间即业务阶段状态机节点."""
    room_id: str = ""
    name: str = ""
    icon: str = "🏠"
    capacity: int = 6
    stage: int = 0  # 业务阶段序号，Agent 只能沿阶段顺序迁移/回退

    def to_dict(self) -> Dict[str, Any]:
        return {"room_id": self.room_id, "name": self.name, "icon": self.icon,
                "capacity": self.capacity, "stage": self.stage}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RoomSpec":
        return cls(room_id=d.get("room_id", ""), name=d.get("name", ""),
                   icon=d.get("icon", "🏠"), capacity=int(d.get("capacity", 6)),
                   stage=int(d.get("stage", 0)))


@dataclass
class ScenarioWorld:
    """场景世界定义 — 对齐 world_state 同步入参."""
    rooms: List[RoomSpec] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    global_metrics_init: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"rooms": [r.to_dict() for r in self.rooms],
                "resources": self.resources, "constraints": self.constraints,
                "global_metrics_init": self.global_metrics_init}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScenarioWorld":
        return cls(rooms=[RoomSpec.from_dict(r) for r in d.get("rooms", [])],
                   resources=d.get("resources", []),
                   constraints=d.get("constraints", []),
                   global_metrics_init=d.get("global_metrics_init", {}))


@dataclass
class ScenarioTask:
    """业务任务流节点 (DAG)."""
    task_id: str = ""
    name: str = ""
    room_id: str = ""
    required_skills: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    base_duration_steps: int = 3
    reward: float = 0.5
    failure_penalty: float = 0.1
    optional: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self.task_id, "name": self.name, "room_id": self.room_id,
                "required_skills": self.required_skills, "depends_on": self.depends_on,
                "base_duration_steps": self.base_duration_steps, "reward": self.reward,
                "failure_penalty": self.failure_penalty, "optional": self.optional}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScenarioTask":
        return cls(task_id=d.get("task_id", ""), name=d.get("name", ""),
                   room_id=d.get("room_id", ""),
                   required_skills=d.get("required_skills", []),
                   depends_on=d.get("depends_on", []),
                   base_duration_steps=int(d.get("base_duration_steps", 3)),
                   reward=float(d.get("reward", 0.5)),
                   failure_penalty=float(d.get("failure_penalty", 0.1)),
                   optional=bool(d.get("optional", False)))


@dataclass
class RoleRequirement:
    """场景角色要求 — 用于真实团队匹配度计算."""
    role: str = ""
    min_count: int = 1
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "min_count": self.min_count,
                "required_skills": self.required_skills,
                "preferred_skills": self.preferred_skills}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RoleRequirement":
        return cls(role=d.get("role", ""), min_count=int(d.get("min_count", 1)),
                   required_skills=d.get("required_skills", []),
                   preferred_skills=d.get("preferred_skills", []))


@dataclass
class ChaosPhase:
    """扰动剧本阶段 — step 区间内按概率注入事件."""
    from_step: int = 0
    to_step: int = 0
    # events: [{event_type, probability_per_step, payload}]
    events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"from_step": self.from_step, "to_step": self.to_step, "events": self.events}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ChaosPhase":
        return cls(from_step=int(d.get("from_step", 0)),
                   to_step=int(d.get("to_step", 0)),
                   events=d.get("events", []))


@dataclass
class ScenarioRubric:
    """验收标准."""
    kpi_targets: Dict[str, float] = field(default_factory=dict)
    dimension_weights: Dict[str, float] = field(default_factory=dict)
    # skill_name -> 期望成功率（进化触发阈值依据）
    skill_expectations: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"kpi_targets": self.kpi_targets,
                "dimension_weights": self.dimension_weights,
                "skill_expectations": self.skill_expectations}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScenarioRubric":
        return cls(kpi_targets=d.get("kpi_targets", {}),
                   dimension_weights=d.get("dimension_weights", {}),
                   skill_expectations=d.get("skill_expectations", {}))


VALID_CATEGORIES = {"customer_service", "data_pipeline", "marketing", "code_delivery", "incident", "general"}
VALID_CHAOS_EVENTS = {"network_delay", "agent_leave", "task_change", "skill_degraded",
                      "model_hallucination", "logic_deadlock", "agent_failure", "task_mutation"}


@dataclass
class ScenarioSpec:
    """业务场景 — 可实例化的孪生环境模板."""
    scenario_id: str = field(default_factory=lambda: f"scn_{str(uuid.uuid4())[:8]}")
    name: str = ""
    category: str = "general"
    description: str = ""
    version: int = 1

    world: ScenarioWorld = field(default_factory=ScenarioWorld)
    taskflow: List[ScenarioTask] = field(default_factory=list)
    roles: List[RoleRequirement] = field(default_factory=list)
    chaos_script: List[ChaosPhase] = field(default_factory=list)
    rubric: ScenarioRubric = field(default_factory=ScenarioRubric)

    tags: List[str] = field(default_factory=list)
    difficulty: int = 1  # 1-5
    recommended_max_steps: int = 150
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    source: str = "builtin"  # builtin | custom | llm_generated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id, "name": self.name,
            "category": self.category, "description": self.description,
            "version": self.version,
            "world": self.world.to_dict(),
            "taskflow": [t.to_dict() for t in self.taskflow],
            "roles": [r.to_dict() for r in self.roles],
            "chaos_script": [c.to_dict() for c in self.chaos_script],
            "rubric": self.rubric.to_dict(),
            "tags": self.tags, "difficulty": self.difficulty,
            "recommended_max_steps": self.recommended_max_steps,
            "created_at": self.created_at, "updated_at": self.updated_at,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScenarioSpec":
        return cls(
            scenario_id=d.get("scenario_id") or f"scn_{str(uuid.uuid4())[:8]}",
            name=d.get("name", ""), category=d.get("category", "general"),
            description=d.get("description", ""), version=int(d.get("version", 1)),
            world=ScenarioWorld.from_dict(d.get("world", {})),
            taskflow=[ScenarioTask.from_dict(t) for t in d.get("taskflow", [])],
            roles=[RoleRequirement.from_dict(r) for r in d.get("roles", [])],
            chaos_script=[ChaosPhase.from_dict(c) for c in d.get("chaos_script", [])],
            rubric=ScenarioRubric.from_dict(d.get("rubric", {})),
            tags=d.get("tags", []), difficulty=int(d.get("difficulty", 1)),
            recommended_max_steps=int(d.get("recommended_max_steps", 150)),
            created_at=d.get("created_at", _now()), updated_at=d.get("updated_at", _now()),
            source=d.get("source", "builtin"),
        )


def validate_scenario(d: Dict[str, Any]) -> List[str]:
    """schema 校验 — 返回字段级错误列表，空列表表示通过."""
    errors: List[str] = []
    if not d.get("name"):
        errors.append("name: 必填")
    if d.get("category") and d["category"] not in VALID_CATEGORIES:
        errors.append(f"category: 必须是 {sorted(VALID_CATEGORIES)} 之一")

    world = d.get("world", {})
    rooms = world.get("rooms", [])
    if not rooms:
        errors.append("world.rooms: 至少需要 1 个房间")
    room_ids = set()
    for i, r in enumerate(rooms):
        if not r.get("room_id"):
            errors.append(f"world.rooms[{i}].room_id: 必填")
        elif r["room_id"] in room_ids:
            errors.append(f"world.rooms[{i}].room_id: 重复 ({r['room_id']})")
        else:
            room_ids.add(r["room_id"])

    taskflow = d.get("taskflow", [])
    if not taskflow:
        errors.append("taskflow: 至少需要 1 个任务")
    task_ids = set()
    for i, t in enumerate(taskflow):
        tid = t.get("task_id", "")
        if not tid:
            errors.append(f"taskflow[{i}].task_id: 必填")
        elif tid in task_ids:
            errors.append(f"taskflow[{i}].task_id: 重复 ({tid})")
        else:
            task_ids.add(tid)
        if t.get("room_id") and t["room_id"] not in room_ids:
            errors.append(f"taskflow[{i}].room_id: 引用不存在的房间 ({t['room_id']})")
    # 依赖引用 + 环检测
    for i, t in enumerate(taskflow):
        for dep in t.get("depends_on", []):
            if dep not in task_ids:
                errors.append(f"taskflow[{i}].depends_on: 引用不存在的任务 ({dep})")
    cycle = _find_cycle(taskflow)
    if cycle:
        errors.append(f"taskflow: 存在环依赖 ({' -> '.join(cycle)})")

    for i, c in enumerate(d.get("chaos_script", [])):
        if int(c.get("from_step", 0)) > int(c.get("to_step", 0)):
            errors.append(f"chaos_script[{i}]: from_step > to_step")
        for j, e in enumerate(c.get("events", [])):
            et = e.get("event_type", "")
            if et not in VALID_CHAOS_EVENTS:
                errors.append(f"chaos_script[{i}].events[{j}].event_type: 非法 ({et})")
            p = float(e.get("probability_per_step", 0))
            if not (0 <= p <= 1):
                errors.append(f"chaos_script[{i}].events[{j}].probability_per_step: 必须在 [0,1]")

    return errors


def _find_cycle(taskflow: List[Dict[str, Any]]) -> Optional[List[str]]:
    """DFS 环检测，返回环路径或 None."""
    graph = {t.get("task_id", ""): t.get("depends_on", []) for t in taskflow}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    path: List[str] = []

    def dfs(node: str) -> Optional[List[str]]:
        color[node] = GRAY
        path.append(node)
        for dep in graph.get(node, []):
            if dep not in graph:
                continue
            if color[dep] == GRAY:
                return path[path.index(dep):] + [dep]
            if color[dep] == WHITE:
                found = dfs(dep)
                if found:
                    return found
        path.pop()
        color[node] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE:
            found = dfs(node)
            if found:
                return found
    return None
