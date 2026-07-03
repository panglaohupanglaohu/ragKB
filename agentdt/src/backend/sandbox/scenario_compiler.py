# -*- coding: utf-8 -*-
"""Scenario Compiler — 场景实例化引擎 (v4 C-1).

ScenarioSpec → 初始世界状态(任务流/资源/约束) + 混沌时间表 + 角色匹配.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .scenario_models import (
    ScenarioSpec, ScenarioTask, validate_scenario, _find_cycle,
)

logger = logging.getLogger(__name__)


class ScenarioCompileError(Exception):
    """场景编译错误 — 带定位信息."""

    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(message)
        self.details = details or []


def compile_scenario(spec: ScenarioSpec, team_snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """编译场景为可注入 WorldStateManager 的世界定义 (C-1.1).

    Returns:
        {
          "pending_tasks": [...],     # 对齐 world_state pending_tasks 格式
          "resources": [...],         # 对齐 sync_resources 入参
          "constraints": [...],
          "rooms": [...],             # 房间定义（前端渲染 + 状态机）
          "room_stages": {room_id: stage},
          "global_metrics": {...},
          "role_match": {...},        # 团队角色匹配报告
        }
    """
    # C-1.2: 校验
    errors = validate_scenario(spec.to_dict())
    if errors:
        raise ScenarioCompileError(f"场景 {spec.scenario_id} 校验失败", errors)

    cycle = _find_cycle([t.to_dict() for t in spec.taskflow])
    if cycle:
        raise ScenarioCompileError(f"场景 {spec.scenario_id} 任务流存在环依赖", [" -> ".join(cycle)])

    # 任务 DAG → pending_tasks（依赖未满足的标记 blocked）
    task_ids = {t.task_id for t in spec.taskflow}
    pending_tasks: List[Dict[str, Any]] = []
    for i, t in enumerate(spec.taskflow):
        pending_tasks.append({
            "id": t.task_id,
            "title": t.name,
            "description": f"[{spec.name}] {t.name}",
            "assigned_to": None,
            "required_roles": [],
            "required_skills": list(t.required_skills),
            "required_tools": [],
            "priority": i + 1,
            "room_id": t.room_id,
            "depends_on": list(t.depends_on),
            "blocked": bool(t.depends_on),  # 有依赖即初始 blocked，依赖完成后解锁
            "base_duration_steps": t.base_duration_steps,
            "reward": t.reward,
            "failure_penalty": t.failure_penalty,
            "optional": t.optional,
            "scenario_id": spec.scenario_id,
        })

    # 团队角色匹配 (C-1.2 覆盖检查 + B-1.5 数据)
    role_match = match_team(spec, team_snapshot or {})

    return {
        "pending_tasks": pending_tasks,
        "resources": spec.world.resources,
        "constraints": spec.world.constraints,
        "rooms": [r.to_dict() for r in spec.world.rooms],
        "room_stages": {r.room_id: r.stage for r in spec.world.rooms},
        "global_metrics": dict(spec.world.global_metrics_init),
        "role_match": role_match,
    }


def match_team(spec: ScenarioSpec, team_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """计算真实团队与场景角色要求的匹配度 (B-1.5)."""
    agents = team_snapshot.get("agents", []) or []
    team_skills: set = set()
    team_roles: Dict[str, int] = {}
    for a in agents:
        for s in (a.get("skills") or []):
            team_skills.add(s)
        r = a.get("role", "")
        if r:
            team_roles[r] = team_roles.get(r, 0) + 1

    required_skills: set = set()
    for t in spec.taskflow:
        required_skills.update(t.required_skills)
    for r in spec.roles:
        required_skills.update(r.required_skills)

    missing_skills = sorted(required_skills - team_skills)
    covered = len(required_skills) - len(missing_skills)
    skill_match_rate = covered / len(required_skills) if required_skills else 1.0

    role_coverage = []
    for req in spec.roles:
        have = team_roles.get(req.role, 0)
        role_coverage.append({
            "role": req.role, "required": req.min_count, "have": have,
            "satisfied": have >= req.min_count,
        })
    roles_ok = sum(1 for r in role_coverage if r["satisfied"])
    role_match_rate = roles_ok / len(role_coverage) if role_coverage else 1.0

    return {
        "match_rate": round(0.6 * skill_match_rate + 0.4 * role_match_rate, 4),
        "skill_match_rate": round(skill_match_rate, 4),
        "role_match_rate": round(role_match_rate, 4),
        "missing_skills": missing_skills,
        "role_coverage": role_coverage,
        "agent_count": len(agents),
    }


def build_chaos_timeline(spec: ScenarioSpec) -> List[Dict[str, Any]]:
    """展开扰动剧本为 per-step 概率表 (C-1.3).

    Returns: [{from_step, to_step, event_type, probability_per_step, payload}]
    交给 twin_loop 每步按概率判定注入。
    """
    timeline: List[Dict[str, Any]] = []
    for phase in spec.chaos_script:
        for e in phase.events:
            timeline.append({
                "from_step": phase.from_step,
                "to_step": phase.to_step,
                "event_type": e.get("event_type", ""),
                "probability_per_step": float(e.get("probability_per_step", 0)),
                "payload": e.get("payload", {}),
            })
    return timeline


# ── LLM 生成场景草稿 (C-1.4) ──────────────────────────────

GENERATE_SYSTEM_PROMPT = """你是业务场景设计师。根据用户的业务描述，生成一个数字孪生演练场景的严格 JSON。
JSON schema（不要输出任何其他内容，不要 markdown 代码块）:
{
  "name": "场景名", "category": "customer_service|data_pipeline|marketing|code_delivery|incident|general",
  "description": "一段话描述", "difficulty": 1-5, "recommended_max_steps": 100-200, "tags": ["..."],
  "world": {"rooms": [{"room_id":"slug","name":"中文名","icon":"emoji","capacity":6,"stage":0}], "resources": [], "constraints": [], "global_metrics_init": {}},
  "taskflow": [{"task_id":"slug","name":"中文名","room_id":"房间slug","required_skills":["skill_slug"],"depends_on":[],"base_duration_steps":3,"reward":0.5,"failure_penalty":0.1,"optional":false}],
  "roles": [{"role":"角色名","min_count":1,"required_skills":[],"preferred_skills":[]}],
  "chaos_script": [{"from_step":20,"to_step":40,"events":[{"event_type":"network_delay","probability_per_step":0.05,"payload":{}}]}],
  "rubric": {"kpi_targets":{"total_score":0.6},"dimension_weights":{},"skill_expectations":{}}
}
要求: 4-6 个房间(stage 递增表示业务阶段)，6-10 个任务(形成 DAG 无环)，2-3 个混沌阶段。
event_type 只能用: network_delay, agent_leave, task_change, skill_degraded, model_hallucination, logic_deadlock, agent_failure, task_mutation"""


async def generate_from_description(text: str, team_id: str = "", chat_harness=None) -> Optional[ScenarioSpec]:
    """LLM 生成场景草稿，三次重试 + schema 校验，失败返回 None (C-1.4)."""
    if chat_harness is None:
        try:
            from agents.chat_harness import get_chat_harness
            chat_harness = get_chat_harness()
        except Exception as e:
            logger.warning(f"chat_harness 不可用: {e}")
            return None

    for attempt in range(3):
        try:
            result = await chat_harness.chat(
                prompt=f"业务描述: {text}\n团队: {team_id or '未指定'}",
                system_prompt=GENERATE_SYSTEM_PROMPT,
                agent_id="scenario_generator",
            )
            resp = getattr(result, "response", None) or ""
            resp = resp.strip()
            if resp.startswith("```"):
                resp = resp.split("\n", 1)[1]
                if resp.endswith("```"):
                    resp = resp[:-3]
                resp = resp.strip()
            data = json.loads(resp)
            errors = validate_scenario(data)
            if errors:
                logger.warning(f"场景生成第 {attempt+1} 次校验失败: {errors[:3]}")
                continue
            spec = ScenarioSpec.from_dict(data)
            spec.source = "llm_generated"
            return spec
        except json.JSONDecodeError as e:
            logger.warning(f"场景生成第 {attempt+1} 次 JSON 解析失败: {e}")
        except Exception as e:
            logger.warning(f"场景生成第 {attempt+1} 次失败: {e}")
    return None
