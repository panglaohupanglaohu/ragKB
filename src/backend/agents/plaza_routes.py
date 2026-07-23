# -*- coding: utf-8 -*-
"""智能体广场 API 路由 + SSE 实时推送."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from channels.system_evolution import EvolutionStatus

from .plaza import PRESET_TOPICS, SeatTier, NicheRole, DiscussionStatus
from .plaza_engine import get_plaza_engine
from .plaza_stream import (
    build_stream_heartbeat_event as _build_stream_heartbeat_event,
    build_stream_status_event as _build_stream_status_event,
    format_live_stream_event as _format_live_stream_event,
    format_sse_event as _format_sse_event,
    is_discussion_end_event as _is_discussion_end_event,
    iter_closed_discussion_events as _iter_closed_discussion_events,
    iter_replay_message_events as _iter_replay_message_events,
    parse_last_event_id as _parse_last_event_id,
    subscribe_discussion_stream as _subscribe_discussion_stream,
    unsubscribe_discussion_stream as _unsubscribe_discussion_stream,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plaza", tags=["Plaza"])

try:
    from config import DEFAULT_PAGE_SIZE as _DEFAULT_PAGE_SIZE
    from config import MAX_PAGE_SIZE as _MAX_PAGE_SIZE
except Exception:
    _DEFAULT_PAGE_SIZE = 50
    _MAX_PAGE_SIZE = 200


# ── Request Models ────────────────────────────────────────

class SelectedAgent(BaseModel):
    agent_id: str
    agent_name: str = ""
    role: str = ""
    team_id: str = ""


class CreatePlazaRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    selected_agents: List[SelectedAgent] = Field(default_factory=list)
    chairperson_agent_id: str = Field(default="")


class AddParticipantRequest(BaseModel):
    agent_id: str
    agent_name: str = ""
    role: str = ""
    team_id: str = ""
    seat_tier: str = Field(default="middle")
    niche_role: str = Field(default="observer")


class CreateDiscussionRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    goal: str = Field(default="", max_length=500)
    moderator_agent_id: str = ""
    max_rounds: int = Field(default=3, ge=1, le=10)


class SetVisualModeRequest(BaseModel):
    mode: str = Field(default="modern")  # modern | rome_320ad | senedd


class DiscussionOutputRequest(BaseModel):
    output_type: str = Field(..., min_length=1, max_length=50)
    target_ids: List[str] = Field(default_factory=list)
    team_id: str = Field(default="")
    status_value: str = Field(default="created")


_ALLOWED_DISCUSSION_OUTPUT_TYPES = {
    "task",
    "task_execution",
    "evolution_item",
    "skill_candidate",
    "cost_governance",
}


def _paginate_optional(items: List[Dict[str, Any]], *, limit: int, offset: int) -> Any:
    """Keep old array responses by default, but support stable optional pagination."""
    limit = getattr(limit, "default", limit)
    offset = getattr(offset, "default", offset)
    limit = int(limit or 0)
    offset = max(int(offset or 0), 0)
    if limit <= 0 and offset <= 0:
        return items
    if limit <= 0:
        limit = _DEFAULT_PAGE_SIZE
    limit = min(limit, _MAX_PAGE_SIZE)
    total = len(items)
    return {
        "items": items[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


def _participant_team_ids(plaza) -> List[str]:
    """Return discussion participant team IDs in stable first-seen order."""
    team_ids: List[str] = []
    for participant in getattr(plaza, "participants", {}).values():
        team_id = getattr(participant, "team_id", "") or ""
        if team_id and team_id not in team_ids:
            team_ids.append(team_id)
    return team_ids


def _discussion_summary_text(disc) -> str:
    """Pick the best short conclusion text for downstream output tracing."""
    if getattr(disc, "summary", ""):
        return str(disc.summary)[:1000]
    conclusions = getattr(disc, "key_conclusions", []) or []
    if conclusions:
        return "\n".join(str(item) for item in conclusions[:5])[:1000]
    plan = getattr(disc, "plan", {}) or {}
    if plan.get("content"):
        return str(plan["content"])[:1000]
    return str(getattr(disc, "description", "") or getattr(disc, "topic", ""))[:1000]


def _record_discussion_output(
    plaza,
    disc,
    *,
    output_type: str,
    target_ids: List[str],
    team_id: str = "",
    status_value: str = "created",
) -> Dict[str, Any]:
    """Record a structured downstream object created from a Plaza discussion."""
    clean_targets = [target_id for target_id in target_ids if target_id]
    output = {
        "id": f"{disc.id}:{output_type}:{':'.join(clean_targets) or team_id or 'none'}",
        "type": output_type,
        "status": status_value,
        "target_ids": clean_targets,
        "team_id": team_id or getattr(disc, "assigned_team_id", ""),
        "source": {
            "type": "plaza_discussion",
            "plaza_id": getattr(plaza, "id", ""),
            "discussion_id": disc.id,
            "topic": disc.topic,
            "summary": _discussion_summary_text(disc),
            "participant_team_ids": _participant_team_ids(plaza),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if not disc.plan:
        disc.plan = {"content": _discussion_summary_text(disc)}
    outputs = list(disc.plan.get("outputs") or [])
    outputs = [item for item in outputs if item.get("id") != output["id"]]
    outputs.append(output)
    disc.plan["outputs"] = outputs[-20:]
    return output


def _get_plan_source(disc) -> str:
    """Return the current discussion plan text, falling back to the summary."""
    if disc.plan and disc.plan.get("content"):
        return str(disc.plan["content"])
    if disc.summary:
        return disc.summary
    return ""


def _get_plan_revision(disc) -> int:
    """Return the discussion plan revision, defaulting to the first version."""
    if not disc.plan:
        return 1
    try:
        return int(disc.plan.get("revision", 1) or 1)
    except (TypeError, ValueError):
        return 1


def _build_plaza_task_metadata(
    *,
    plaza_id: str,
    discussion_id: str,
    discussion_topic: str,
    team_id: str,
    plan_revision: int,
    plan_item_index: int,
    responsible_role: str = "",
    acceptance_test: str = "",
    expected_artifacts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Normalize plaza-origin task metadata for tracing and later evolution."""
    inferred_skills = _infer_skills_from_role(responsible_role)
    trace_context = {
        "source": "plaza",
        "plaza_id": plaza_id,
        "discussion_id": discussion_id,
        "discussion_topic": discussion_topic,
        "team_id": team_id,
        "plan_revision": plan_revision,
        "plan_item_index": plan_item_index,
        "responsible_role": responsible_role,
    }
    return {
        "source": "plaza",
        "plaza_id": plaza_id,
        "discussion_id": discussion_id,
        "discussion_topic": discussion_topic,
        "team_id": team_id,
        "plan_revision": plan_revision,
        "plan_item_index": plan_item_index,
        "responsible_role": responsible_role,
        "acceptance_test": acceptance_test,
        "expected_artifacts": list(expected_artifacts or []),
        "skills_used": inferred_skills,
        "trace_context": trace_context,
    }


def _infer_skills_from_role(responsible_role: str) -> List[str]:
    """Infer likely skill evidence from the role assigned in the discussion plan."""
    role = (responsible_role or "").strip().lower()
    if not role:
        return []

    role_skill_hints = (
        (("developer", "engineer", "开发", "实现"), ["code_implementation", "debugging"]),
        (("qa", "tester", "test", "测试"), ["testing", "test_execution", "regression_testing"]),
        (("architect", "架构"), ["architecture_design", "interface_definition"]),
        (("research", "analyst", "研究", "分析"), ["web_research", "requirements_analysis"]),
        (("pm", "manager", "协调", "项目"), ["task_decomposition", "progress_tracking"]),
        (("deploy", "ops", "devops", "运维"), ["build_automation", "deployment_orchestration"]),
    )

    for keywords, skills in role_skill_hints:
        if any(keyword in role for keyword in keywords):
            return list(skills)
    return []


def _resolve_responsible_agent(team_id: str, responsible: str) -> str:
    """将执行计划中的"负责角色"文本解析为团队中具体 agent 的 ID.

    匹配优先级: agent.name 精确匹配 → agent.name 含关键词 → agent.role 匹配
    → 角色关键词交叉匹配 → 语义近似匹配（architect↔架构师等）
    均失败时返回空字符串，任务将分配给整个团队。
    """
    responsible = (responsible or "").strip()
    if not responsible or not team_id:
        return ""
    try:
        from .api import _team_manager
        if not _team_manager:
            return ""
        agents = _team_manager.list_agents(team_id)
        if not agents:
            return ""
        # 1) 精确名称匹配
        for a in agents:
            if a.name == responsible:
                return a.agent_id
        # 2) 名称含关键词（任一方向）
        resp_lower = responsible.lower()
        for a in agents:
            a_lower = a.name.lower()
            if resp_lower in a_lower or a_lower in resp_lower:
                return a.agent_id
        # 3) 角色匹配
        for a in agents:
            if a.role and responsible in a.role:
                return a.agent_id
        # 4) 角色关键词交叉匹配
        resp_keywords = set(responsible.split())
        for a in agents:
            role_words = set((a.role or "").lower().replace("_", " ").split())
            if resp_keywords & role_words:
                return a.agent_id
        # 5) 语义近似匹配 — 中英文角色名映射
        ROLE_SYNONYMS = {
            "architect": ["架构师", "架构", "architect"],
            "developer": ["开发", "开发者", "编程", "developer", "全栈"],
            "researcher": ["研究", "研究员", "researcher", "调研"],
            "qa_engineer": ["测试", "质检", "qa", "tester", "review"],
            "devops": ["运维", "部署", "devops", "deployer", "操作员"],
            "project_manager": ["项目经理", "pm", "leader", "协调"],
            "documentation": ["文档", "doc", "writer"],
            "finops": ["成本", "费用", "账单", "cost", "finops"],
            "monitor": ["监控", "巡检", "monitor", "sre"],
            "compliance": ["合规", "compliance", "区域"],
        }
        resp_lower_for_match = resp_lower
        for a in agents:
            role = (a.role or "").lower()
            for eng_role, synonyms in ROLE_SYNONYMS.items():
                if role == eng_role or eng_role in role:
                    if any(syn in resp_lower_for_match for syn in synonyms):
                        return a.agent_id
        # 6) Build System 团队特殊处理：Build System → build_pm
        if "build system" in resp_lower:
            for a in agents:
                if a.role == "project_manager":
                    return a.agent_id
            if agents:
                return agents[0].agent_id
        logger.info("未找到 agent 匹配 responsible=%s 在团队 %s 中，任务将分配至团队级", responsible[:30], team_id[:12])
    except Exception as e:
        logger.warning("解析负责 agent 失败: %s", e)
    return ""


async def _dispatch_discussion_tasks(
    plaza_id: str,
    disc,
    team_id: str,
    *,
    auto_start: bool,
) -> List[Dict[str, Any]]:
    """Materialize discussion plan items into concrete tasks."""
    plan_source = _get_plan_source(disc)
    if not plan_source:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "尚无执行计划，请先完成讨论或生成计划")

    # P6-2 落地性关卡: 结构化计划存在时，审查未过或未经人批准 → 不允许派发。
    # （无结构化计划的旧流程不受影响，保持向后兼容。）
    structured_plan = load_plan_from_discussion(disc)
    if structured_plan is not None:
        plan_issues = validate_plan(structured_plan)
        if plan_issues:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={"error": "落地性审查未通过，不允许派发", "issues": plan_issues},
            )
        if structured_plan.status not in ("approved", "dispatched"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={"error": "执行计划尚未批准，请先 POST .../execution-plan/approve"},
            )

    tasks_data = _parse_plan_table(plan_source)
    if not tasks_data or (len(tasks_data) == 1 and tasks_data[0].get("title") == "演化需求"):
        from .chat_harness import get_chat_harness

        harness = get_chat_harness()
        parse_prompt = (
            "你是任务拆解助手。请分析以下执行计划，提取可执行的任务列表。\n"
            "严格按照 JSON 数组格式输出，每项包含: title, description, priority (1-3, 1最高)\n"
            "只输出 JSON 数组，不要任何其他文字。\n\n"
            f"讨论话题: {disc.topic}\n\n"
            f"执行计划:\n{plan_source}\n"
        )
        try:
            result = await harness.chat(parse_prompt, system_prompt="你是一个任务拆解专家，只输出JSON。")
            llm_reply = result.response
            import re

            json_match = re.search(r'\[.*\]', llm_reply, re.DOTALL)
            if not json_match:
                raise ValueError("LLM 未返回有效 JSON 数组")
            tasks_data = json.loads(json_match.group())
        except Exception as e:
            logger.warning("LLM 任务拆解失败: %s，回退为单任务", e)
            tasks_data = [{
                "title": f"[广场计划] {disc.topic[:80]}",
                "description": f"来自广场讨论「{disc.topic}」的执行任务。讨论产生 {len(disc.messages)} 条消息。",
                "priority": 2,
                "responsible": "",
                "dependencies": "",
                "expected_artifact": "执行结果记录",
            }]

    from .api import _submit_internal_task

    created_tasks: List[Dict[str, Any]] = []
    plan_revision = _get_plan_revision(disc)
    for index, td in enumerate(tasks_data[:10]):
        title_raw = str(td.get("title", f"任务 {index + 1}"))
        # 质量校验：跳过明显的无效标题
        if not _is_valid_task_title(title_raw):
            logger.warning("派发跳过无效任务标题: %s", title_raw[:80])
            continue
        expected_artifact = str(td.get("expected_artifact", "")).strip()
        responsible_role = str(td.get("responsible", "")).strip()
        # 解析负责角色，匹配团队中具体智能体
        resolved_agent_id = _resolve_responsible_agent(team_id, responsible_role)
        description_lines = []
        if td.get("description"):
            description_lines.append(str(td["description"]).strip())
        if responsible_role:
            description_lines.append(f"负责角色: {responsible_role}")
            if resolved_agent_id:
                description_lines.append(f"执行智能体: {resolved_agent_id[:12]}")
        if td.get("dependencies"):
            description_lines.append(f"依赖: {str(td['dependencies']).strip()}")
        if expected_artifact:
            description_lines.append(f"预期产出: {expected_artifact}")

        task = await _submit_internal_task(
            team_id,
            agent_id=resolved_agent_id,  # 将任务分配给具体智能体
            title=title_raw[:120],
            description="\n".join(line for line in description_lines if line)[:2000],
            priority=int(td.get("priority", 2)),
            metadata=_build_plaza_task_metadata(
                plaza_id=plaza_id,
                discussion_id=disc.id,
                discussion_topic=disc.topic,
                team_id=team_id,
                plan_revision=plan_revision,
                plan_item_index=index,
                responsible_role=responsible_role,
                acceptance_test=str(td.get("acceptance_test", "")).strip(),
                expected_artifacts=[expected_artifact] if expected_artifact else [],
            ),
            auto_start=auto_start,
        )
        created_tasks.append(task.to_dict())

    disc.assigned_team_id = team_id
    if not disc.plan:
        disc.plan = {
            "revision": plan_revision,
            "revision_reason": "从讨论总结补建执行计划",
            "revised_at": "",
            "content": plan_source,
        }
    disc.plan["task_ids"] = [task["task_id"] for task in created_tasks]
    disc.plan["task_count"] = len(created_tasks)
    disc.plan["team_id"] = team_id
    disc.plan["dispatched_at"] = datetime.now(timezone.utc).isoformat()

    # P5-2: 步骤 ↔ 任务 绑定（1 步骤 1 任务），执行状态可回流到计划。
    if structured_plan is not None:
        by_title = {s.title: s for s in structured_plan.steps}
        pending_steps = [s for s in structured_plan.steps if s.status == "pending"]
        for i, task in enumerate(created_tasks):
            title = str(task.get("title", "")).strip()
            step = by_title.get(title) or by_title.get(title[:120])
            if step is None and i < len(pending_steps):
                step = pending_steps[i]  # 同一解析器同序兜底
            if step is not None and step.status == "pending":
                step.status = "dispatched"
                step.task_id = task.get("task_id", "")
        structured_plan.status = "dispatched"
        save_plan_to_discussion(disc, structured_plan)
    return created_tasks


def _link_tasks_to_evolution_items(
    plaza_id: str,
    discussion_id: str,
    evolution_item_ids: List[str],
    task_ids: List[str],
) -> None:
    """Backfill task metadata so task -> evolution tracing is explicit."""
    if not evolution_item_ids or not task_ids:
        return

    from .api import _te

    engine = _te()
    for task_id in task_ids:
        task = engine.get_task(task_id)
        if task is None:
            continue
        metadata = task.metadata or {}
        metadata["evolution_item_ids"] = list(evolution_item_ids)
        trace_context = dict(metadata.get("trace_context") or {})
        trace_context.setdefault("source", metadata.get("source", "plaza"))
        trace_context["plaza_id"] = plaza_id
        trace_context["discussion_id"] = discussion_id
        trace_context["task_id"] = task.task_id
        trace_context["evolution_item_ids"] = list(evolution_item_ids)
        metadata["trace_context"] = trace_context
        task.metadata = metadata
        engine._store.save_task(task)


def _build_discussion_verification_state_payload(
    evolution_engine,
    *,
    plaza_id: str,
    discussion_id: str,
    trigger: str,
    synced_item_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    queue = evolution_engine.get_verification_queue(
        source_plaza_id=plaza_id,
        source_discussion_id=discussion_id,
    )
    alerts = evolution_engine.get_verification_alerts(
        source_plaza_id=plaza_id,
        source_discussion_id=discussion_id,
    )
    status_counts: Dict[str, int] = {}
    for item in queue:
        item_status = str(item.get("status", ""))
        status_counts[item_status] = status_counts.get(item_status, 0) + 1
    return {
        "type": "verification_state_updated",
        "plaza_id": plaza_id,
        "discussion_id": discussion_id,
        "trigger": trigger,
        "synced_item_ids": list(synced_item_ids or []),
        "status_counts": status_counts,
        "queue_count": len(queue),
        "alert_count": len(alerts),
        "alerts": alerts,
    }


# ── 广场 CRUD ──────────────────────────────────────────────

@router.post("", summary="创建广场", status_code=status.HTTP_201_CREATED)
async def create_plaza(req: CreatePlazaRequest) -> Dict[str, Any]:
    engine = get_plaza_engine()
    if req.chairperson_agent_id:
        selected_ids = {agent.agent_id for agent in req.selected_agents}
        if req.chairperson_agent_id not in selected_ids:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "议事长必须来自已选择的智能体",
            )

    plaza = engine.create_plaza(req.name, req.description)

    # 如果指定了智能体列表，直接入座
    for sa in req.selected_agents:
        is_chair = (sa.agent_id == req.chairperson_agent_id)
        engine.add_participant(
            plaza.id,
            sa.agent_id,
            sa.agent_name,
            sa.role,
            sa.team_id,
            SeatTier.INNER if is_chair else SeatTier.MIDDLE,
            NicheRole.MODERATOR if is_chair else NicheRole.OBSERVER,
        )

    return plaza.to_dict(include_details=True)


@router.get("", summary="列出所有广场")
async def list_plazas(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    engine = get_plaza_engine()
    items = [p.to_dict() for p in engine.list_plazas()]
    sliced = items[offset:offset + limit]
    return {
        "items": sliced,
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < len(items),
    }


@router.get("/presets", summary="获取预设话题模板")
async def get_preset_topics() -> List[Dict[str, str]]:
    return PRESET_TOPICS


# NOTE: 必须在 /{plaza_id} 之前注册，否则 GET /escalations 会被 /{plaza_id} 吞掉
# (plaza_id="escalations") → 404「广场不存在」。FastAPI 按注册顺序匹配。
@router.get("/escalations", summary="获取失败升级队列")
async def get_escalation_queue(
    plaza_id: str = Query(default="", description="按广场过滤"),
    discussion_id: str = Query(default="", description="按讨论过滤"),
    entry_status: str = Query(default="", alias="status", description="按状态过滤"),
) -> Dict[str, Any]:
    """Return all pending escalation entries for human review."""
    engine = get_plaza_engine()
    queue = [
        {"index": index, **entry}
        for index, entry in enumerate(engine.get_escalation_queue())
    ]
    if plaza_id:
        queue = [entry for entry in queue if entry.get("plaza_id") == plaza_id]
    if discussion_id:
        queue = [entry for entry in queue if entry.get("discussion_id") == discussion_id]
    if entry_status:
        queue = [entry for entry in queue if entry.get("status") == entry_status]
    pending = [e for e in queue if e.get("status") == "pending"]
    return {
        "items": queue,
        "total": len(queue),
        "pending_count": len(pending),
    }


@router.get("/{plaza_id}", summary="获取广场详情")
async def get_plaza(plaza_id: str) -> Dict[str, Any]:
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    return plaza.to_dict(include_details=True)


@router.delete("/{plaza_id}", summary="删除广场")
async def delete_plaza(plaza_id: str) -> Dict[str, str]:
    engine = get_plaza_engine()
    if not engine.delete_plaza(plaza_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    return {"status": "deleted"}


@router.put("/{plaza_id}/visual-mode", summary="切换视觉模式")
async def set_visual_mode(plaza_id: str, req: SetVisualModeRequest) -> Dict[str, Any]:
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    if req.mode not in ("modern", "rome_320ad", "senedd"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "无效的视觉模式")
    plaza.visual_mode = req.mode
    return {"status": "updated", "visual_mode": plaza.visual_mode}


# ── 参与者管理 ──────────────────────────────────────────────

@router.post("/{plaza_id}/participants", summary="添加参与者", status_code=201)
async def add_participant(plaza_id: str, req: AddParticipantRequest) -> Dict[str, Any]:
    engine = get_plaza_engine()
    try:
        tier = SeatTier(req.seat_tier)
    except ValueError:
        tier = SeatTier.MIDDLE
    try:
        niche = NicheRole(req.niche_role)
    except ValueError:
        niche = NicheRole.OBSERVER
    p = engine.add_participant(
        plaza_id, req.agent_id, req.agent_name, req.role, req.team_id,
        tier, niche,
    )
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    return p.to_dict()


@router.delete("/{plaza_id}/participants/{agent_id}", summary="移除参与者")
async def remove_participant(plaza_id: str, agent_id: str) -> Dict[str, str]:
    engine = get_plaza_engine()
    if not engine.remove_participant(plaza_id, agent_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "参与者不存在")
    return {"status": "removed"}


@router.post("/{plaza_id}/participants/batch", summary="批量添加参与者", status_code=201)
async def batch_add_participants(
    plaza_id: str, participants: List[AddParticipantRequest]
) -> List[Dict[str, Any]]:
    engine = get_plaza_engine()
    results = []
    for req in participants:
        try:
            tier = SeatTier(req.seat_tier)
        except ValueError:
            tier = SeatTier.MIDDLE
        try:
            niche = NicheRole(req.niche_role)
        except ValueError:
            niche = NicheRole.OBSERVER
        p = engine.add_participant(
            plaza_id, req.agent_id, req.agent_name, req.role, req.team_id,
            tier, niche,
        )
        if p:
            results.append(p.to_dict())
    return results


# ── 讨论管理 ──────────────────────────────────────────────

@router.post("/{plaza_id}/discussions", summary="创建讨论", status_code=201)
async def create_discussion(
    plaza_id: str, req: CreateDiscussionRequest,
) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.create_discussion(
        plaza_id, req.topic, req.description,
        req.moderator_agent_id, req.max_rounds,
    )
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc.goal = req.goal
    # 关联发起团队（如成本治理按团队创建话题）→ 讨论归属该团队，可按团队过滤
    if getattr(req, "team_id", ""):
        disc.assigned_team_id = req.team_id
    try:
        engine._store.save_plaza(engine._plazas[plaza_id])
    except Exception:
        pass
    return disc.to_dict()


@router.get("/{plaza_id}/discussions", summary="列出讨论")
async def list_discussions(
    plaza_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    engine = get_plaza_engine()
    items = [d.to_dict() for d in engine.list_discussions(plaza_id)]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/{plaza_id}/discussions/{disc_id}", summary="获取讨论详情")
async def get_discussion(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    return disc.to_dict(include_messages=True)


@router.get("/{plaza_id}/discussions/{disc_id}/summary", summary="获取讨论总结")
async def get_discussion_summary(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    return {
        "discussion_id": disc.id,
        "topic": disc.topic,
        "status": disc.status.value,
        "summary": disc.summary,
        "key_conclusions": disc.key_conclusions,
        "message_count": len(disc.messages),
        "rounds": disc.current_round,
        "plan": disc.plan,
        "plan_revision": _get_plan_revision(disc),
        "task_ids": list((disc.plan or {}).get("task_ids", []) or []),
        "task_count": int((disc.plan or {}).get("task_count", 0) or 0),
        "goal": disc.goal,
        "assigned_team_id": disc.assigned_team_id,
    }


@router.get("/{plaza_id}/discussions/{disc_id}/tasks", summary="获取讨论关联任务")
async def get_discussion_tasks(
    plaza_id: str,
    disc_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    from .api import _te

    tasks = [
        task.to_dict()
        for task in _te().list_tasks()
        if task.metadata.get("source") == "plaza"
        and task.metadata.get("plaza_id") == plaza_id
        and task.metadata.get("discussion_id") == disc_id
    ]
    tasks.sort(key=lambda item: item.get("metadata", {}).get("plan_item_index", 0))
    paged = _paginate_optional(tasks, limit=limit, offset=offset)
    if isinstance(paged, list):
        paged_tasks = paged
        pagination = {}
    else:
        paged_tasks = paged["items"]
        pagination = {
            "limit": paged["limit"],
            "offset": paged["offset"],
            "has_more": paged["has_more"],
        }
    return {
        "discussion_id": disc_id,
        "plaza_id": plaza_id,
        "task_count": len(tasks),
        "tasks": paged_tasks,
        **pagination,
    }


@router.delete("/{plaza_id}/discussions/{disc_id}", summary="删除讨论")
async def delete_discussion(plaza_id: str, disc_id: str) -> Dict[str, str]:
    engine = get_plaza_engine()
    if not engine.delete_discussion(plaza_id, disc_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    return {"status": "deleted", "discussion_id": disc_id}


# ── 自动入座 (所有团队智能体) ──────────────────────────────

@router.post("/{plaza_id}/auto-seat", summary="全部智能体自动入座", status_code=200)
async def auto_seat_all_agents(plaza_id: str) -> Dict[str, Any]:
    """从所有团队拉取智能体自动入座广场，按团队分区."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")

    # 获取 TeamManager
    try:
        from agents.api import _team_manager
    except ImportError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "TeamManager 不可用")

    added = []
    teams = _team_manager.list_teams() if _team_manager else []
    for team in teams:
        agents = team.agents
        if isinstance(agents, dict):
            agents = list(agents.values())
        for a in agents:
            if a.agent_id in plaza.participants:
                continue
            p = engine.add_participant(
                plaza_id, a.agent_id, a.name or a.agent_id,
                a.role or "", team.team_id,
                SeatTier.MIDDLE, NicheRole.OBSERVER,
            )
            if p:
                added.append(p.to_dict())

    return {"added": len(added), "total": len(plaza.participants), "participants": added}


# ── 计划指派给团队 ──────────────────────────────────────────

class AssignPlanRequest(BaseModel):
    team_id: str
    task_name: str = ""
    task_description: str = ""


@router.post("/{plaza_id}/discussions/{disc_id}/assign", summary="将讨论计划指派给团队")
async def assign_plan_to_team(
    plaza_id: str, disc_id: str, req: AssignPlanRequest,
) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    disc.assigned_team_id = req.team_id

    try:
        from .api import _submit_internal_task

        task_name = req.task_name or f"[广场计划] {disc.topic[:50]}"
        task_desc = req.task_description or _get_plan_source(disc) or disc.topic
        submitted = await _submit_internal_task(
            req.team_id,
            title=task_name,
            description=task_desc[:2000],
            metadata=_build_plaza_task_metadata(
                plaza_id=plaza_id,
                discussion_id=disc.id,
                discussion_topic=disc.topic,
                team_id=req.team_id,
                plan_revision=_get_plan_revision(disc),
                plan_item_index=0,
                expected_artifacts=["执行结果记录"],
            ),
            auto_start=False,
        )
        if not disc.plan:
            disc.plan = {
                "revision": _get_plan_revision(disc),
                "revision_reason": "指派团队时补建执行计划",
                "revised_at": "",
                "content": task_desc,
            }
        disc.plan["task_ids"] = [submitted.task_id]
        disc.plan["task_count"] = 1
        disc.plan["team_id"] = req.team_id
        engine._store.save_plaza(engine._plazas[plaza_id])
        return {"status": "assigned", "team_id": req.team_id, "task_id": submitted.task_id}
    except Exception as e:
        logger.warning("创建任务失败: %s", e)
        return {"status": "assigned_no_task", "team_id": req.team_id, "error": str(e)}


# ── 讨论输出对象记录 ──────────────────────────────────────

@router.post("/{plaza_id}/discussions/{disc_id}/outputs", summary="记录讨论结论输出到下游对象")
async def record_discussion_output(
    plaza_id: str, disc_id: str, req: DiscussionOutputRequest,
) -> Dict[str, Any]:
    """Persist the downstream object selected from a Plaza conclusion."""
    if req.output_type not in _ALLOWED_DISCUSSION_OUTPUT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不支持的输出类型")

    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    output = _record_discussion_output(
        plaza,
        disc,
        output_type=req.output_type,
        target_ids=req.target_ids,
        team_id=req.team_id,
        status_value=req.status_value,
    )
    engine._store.save_plaza(engine._plazas[plaza_id])
    return {"status": "recorded", "output": output, "outputs": [output]}


# ── 讨论→任务批量派发 ──────────────────────────────────────

class DispatchTasksRequest(BaseModel):
    team_id: str = Field(..., min_length=1)


@router.post("/{plaza_id}/discussions/{disc_id}/dispatch", summary="从讨论结论自动拆解并派发任务")
async def dispatch_tasks_from_discussion(
    plaza_id: str, disc_id: str, req: DispatchTasksRequest,
) -> Dict[str, Any]:
    """解析执行计划中的任务表格，为每行创建独立的可追踪任务."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    created_tasks = await _dispatch_discussion_tasks(plaza_id, disc, req.team_id, auto_start=False)
    output = _record_discussion_output(
        plaza,
        disc,
        output_type="task",
        target_ids=[task.get("task_id", "") for task in created_tasks],
        team_id=req.team_id,
        status_value="dispatched",
    )
    engine._store.save_plaza(engine._plazas[plaza_id])

    return {
        "status": "dispatched",
        "team_id": req.team_id,
        "task_count": len(created_tasks),
        "tasks": created_tasks,
        "output": output,
        "outputs": [output],
    }


# ── 刷新执行计划（议事长重新小结） ─────────────────────────

@router.post("/{plaza_id}/discussions/{disc_id}/refresh-plan", summary="议事长根据对话重新生成执行计划")
async def refresh_plan(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    """让议事长回顾全部对话，重新输出执行计划."""
    engine = get_plaza_engine()
    result = await engine.regenerate_plan(plaza_id, disc_id)
    if "error" in result:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


# ── P5-1/P6-2/P5-2: 结构化执行计划（集体智慧的产出契约） ─────────


class ApprovePlanRequest(BaseModel):
    approved_by: str = ""
    force: bool = False   # 显式跳过落地性审查（保留人的最终决定权）


class PlanStepStatusRequest(BaseModel):
    status: str = "completed"
    task_id: str = ""


def _resolve_plaza_discussion(engine, plaza_id: str, disc_id: str):
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    return plaza, disc


@router.get(
    "/{plaza_id}/discussions/{disc_id}/execution-plan",
    summary="获取结构化执行计划 + 落地性审查结果 (P5-1/P6-2)",
)
async def get_execution_plan(plaza_id: str, disc_id: str, rebuild: bool = False) -> Dict[str, Any]:
    engine = get_plaza_engine()
    plaza, disc = _resolve_plaza_discussion(engine, plaza_id, disc_id)
    plan = None if rebuild else load_plan_from_discussion(disc)
    if plan is None:
        source = _get_plan_source(disc)
        if not source:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "尚无执行计划，请先完成讨论或生成计划")
        plan = build_plan_from_text(
            source,
            plaza_id=plaza_id,
            discussion_id=disc_id,
            topic=disc.topic,
            goal=getattr(disc, "goal", "") or "",
            revision=_get_plan_revision(disc),
        )
        save_plan_to_discussion(disc, plan)
        engine._store.save_plaza(plaza)
    issues = validate_plan(plan)
    return {
        "plan": plan.to_dict(),
        "issues": issues,
        "dispatchable": (not issues) and plan.status in ("approved", "dispatched"),
    }


@router.post(
    "/{plaza_id}/discussions/{disc_id}/execution-plan/approve",
    summary="人批准执行计划（落地性审查关卡，过关才可派发）",
)
async def approve_execution_plan(
    plaza_id: str, disc_id: str, req: ApprovePlanRequest,
) -> Dict[str, Any]:
    engine = get_plaza_engine()
    plaza, disc = _resolve_plaza_discussion(engine, plaza_id, disc_id)
    plan = load_plan_from_discussion(disc)
    if plan is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "尚无结构化计划，请先 GET .../execution-plan 生成",
        )
    issues = validate_plan(plan)
    if issues and not req.force:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "落地性审查未通过", "issues": issues},
        )
    plan.status = "approved"
    plan.approved_by = req.approved_by or "user"
    save_plan_to_discussion(disc, plan)
    engine._store.save_plaza(plaza)
    await engine._broadcast(disc.id, {
        "type": "plan_approved",
        "plan_id": plan.plan_id,
        "approved_by": plan.approved_by,
        "forced": bool(issues),
    })
    return {"status": "approved", "plan": plan.to_dict(), "issues": issues}


@router.post(
    "/{plaza_id}/discussions/{disc_id}/execution-plan/steps/{step_id}/status",
    summary="步骤执行状态回流（任务完成/失败 → 计划进度，P5-2）",
)
async def update_plan_step_status(
    plaza_id: str, disc_id: str, step_id: str, req: PlanStepStatusRequest,
) -> Dict[str, Any]:
    engine = get_plaza_engine()
    plaza, disc = _resolve_plaza_discussion(engine, plaza_id, disc_id)
    plan = load_plan_from_discussion(disc)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "尚无结构化计划")
    step = plan.get_step(step_id)
    if step is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"步骤 {step_id} 不存在")
    if req.status not in STEP_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"非法状态 {req.status}，允许: {STEP_STATUSES}",
        )
    step.status = req.status
    if req.task_id:
        step.task_id = req.task_id
    plan.refresh_status()
    save_plan_to_discussion(disc, plan)
    engine._store.save_plaza(plaza)
    await engine._broadcast(disc.id, {
        "type": "plan_step_updated",
        "plan_id": plan.plan_id,
        "step_id": step_id,
        "step_status": step.status,
        "plan_status": plan.status,
    })
    if plan.status == "completed":
        await engine._broadcast(disc.id, {
            "type": "plan_completed", "plan_id": plan.plan_id,
        })
    return {"plan_status": plan.status, "step": step.to_dict()}


# ── 派发并立即执行 ──────────────────────────────────────────


# 计划解析唯一实现已迁至 execution_plan.py（P5-1），此处保留同名别名兼容既有调用与测试。
from .execution_plan import (
    STEP_STATUSES,
    build_plan_from_text,
    is_valid_task_title as _is_valid_task_title,
    load_plan_from_discussion,
    parse_plan_table as _parse_plan_table,
    save_plan_to_discussion,
    validate_plan,
)


@router.post("/{plaza_id}/discussions/{disc_id}/dispatch-and-execute", summary="拆解任务并立即启动执行")
async def dispatch_and_execute(
    plaza_id: str, disc_id: str, req: DispatchTasksRequest,
) -> Dict[str, Any]:
    """拆解执行计划为任务，并立即触发自动执行流水线."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    created_tasks = await _dispatch_discussion_tasks(plaza_id, disc, req.team_id, auto_start=True)
    output = _record_discussion_output(
        plaza,
        disc,
        output_type="task_execution",
        target_ids=[task.get("task_id", "") for task in created_tasks],
        team_id=req.team_id,
        status_value="executing",
    )
    engine._store.save_plaza(engine._plazas[plaza_id])
    return {
        "status": "executing",
        "team_id": req.team_id,
        "task_count": len(created_tasks),
        "tasks": created_tasks,
        "output": output,
        "outputs": [output],
    }


# ── 进入演化 ──────────────────────────────────────────────

class EvolveRequest(BaseModel):
    team_id: str = Field(default="")


@router.post("/{plaza_id}/discussions/{disc_id}/evolve", summary="将讨论结论注入系统演化引擎")
async def evolve_from_discussion(
    plaza_id: str, disc_id: str, req: EvolveRequest,
) -> Dict[str, Any]:
    """将讨论中的执行计划转化为系统演化需求，注入演化引擎自动迭代."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    plan_source = _get_plan_source(disc)
    if not plan_source:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "尚无执行计划")

    # 解析为演化需求项并注入 SystemEvolutionChannel
    from channels.system_evolution import EvolutionItem
    from agent_team_api import _evolution_engine

    if not _evolution_engine:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "演化引擎未初始化")

    dispatched_tasks = []
    if req.team_id:
        try:
            dispatched_tasks = await _dispatch_discussion_tasks(
                plaza_id,
                disc,
                req.team_id,
                auto_start=False,
            )
            engine._store.save_plaza(engine._plazas[plaza_id])
        except Exception as e:
            logger.warning("演化前派发失败: %s", e)

    source_task_ids = [task.get("task_id", "") for task in dispatched_tasks if task.get("task_id")]

    # 从计划中提取任务，转为演化项
    tasks_data = _parse_plan_table(plan_source)
    evolution_items = []

    for i, td in enumerate(tasks_data[:8]):
        item = EvolutionItem(
            title=str(td.get("title", f"演化项 {i+1}"))[:100],
            description=str(td.get("description", ""))[:500],
            target_channel=f"plaza:{plaza_id}/discussion:{disc.id}",
            severity="high" if td.get("priority", 2) <= 1 else "medium",
            source_plaza_id=plaza_id,
            source_discussion_id=disc.id,
            source_task_ids=source_task_ids,
            artifact_dir=f"storage/evolution_runs/{disc.id}",
            trace_context={
                "source": "plaza",
                "plaza_id": plaza_id,
                "discussion_id": disc.id,
                "plan_revision": _get_plan_revision(disc),
                "source_task_ids": list(source_task_ids),
            },
        )
        _evolution_engine.evolution_items[item.id] = item
        evolution_items.append({
            "id": item.id,
            "title": item.title,
            "status": item.status,
            "priority": td.get("priority", 2),
            "source_discussion_id": item.source_discussion_id,
            "source_task_ids": item.source_task_ids,
            "trace_context": dict(item.trace_context),
        })

    evolution_item_ids = [item["id"] for item in evolution_items]
    _link_tasks_to_evolution_items(plaza_id, disc.id, evolution_item_ids, source_task_ids)
    for task in dispatched_tasks:
        metadata = dict(task.get("metadata") or {})
        metadata["evolution_item_ids"] = list(evolution_item_ids)
        trace_context = dict(metadata.get("trace_context") or {})
        trace_context["task_id"] = task.get("task_id", "")
        trace_context["evolution_item_ids"] = list(evolution_item_ids)
        metadata["trace_context"] = trace_context
        task["metadata"] = metadata

    # 触发演化周期
    cycle_result = _evolution_engine.run_evolution_cycle()
    payload = _build_discussion_verification_state_payload(
        _evolution_engine,
        plaza_id=plaza_id,
        discussion_id=disc.id,
        trigger="discussion_evolved",
        synced_item_ids=evolution_item_ids,
    )
    payload["cycle_result"] = cycle_result
    await engine._broadcast(disc.id, payload)
    output = _record_discussion_output(
        plaza,
        disc,
        output_type="evolution_item",
        target_ids=evolution_item_ids,
        team_id=req.team_id,
        status_value="evolving",
    )
    engine._store.save_plaza(engine._plazas[plaza_id])

    return {
        "status": "evolving",
        "evolution_items": len(evolution_items),
        "items": evolution_items,
        "cycle_result": cycle_result,
        "tasks": dispatched_tasks,
        "task_count": len(dispatched_tasks),
        "output": output,
        "outputs": [output],
    }


@router.get(
    "/{plaza_id}/discussions/{disc_id}/verification-queue",
    summary="查看当前讨论关联的演进验证队列",
)
async def get_discussion_verification_queue(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    """Return linked evolution items, prioritizing entries still waiting on verification."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    from agent_team_api import _evolution_engine

    if not _evolution_engine:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "演化引擎未初始化")

    items = _evolution_engine.get_verification_queue(
        source_plaza_id=plaza_id,
        source_discussion_id=disc_id,
    )
    return {
        "plaza_id": plaza_id,
        "discussion_id": disc_id,
        "count": len(items),
        "items": items,
    }


@router.get(
    "/{plaza_id}/discussions/{disc_id}/verification-alerts",
    summary="查看当前讨论关联的验证告警",
)
async def get_discussion_verification_alerts(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    """Return only verification items that currently require follow-up."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    from agent_team_api import _evolution_engine

    if not _evolution_engine:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "演化引擎未初始化")

    alerts = _evolution_engine.get_verification_alerts(
        source_plaza_id=plaza_id,
        source_discussion_id=disc_id,
    )
    return {
        "plaza_id": plaza_id,
        "discussion_id": disc_id,
        "count": len(alerts),
        "alerts": alerts,
    }


@router.post(
    "/{plaza_id}/discussions/{disc_id}/verification-queue/run",
    summary="运行当前讨论关联的验证队列",
)
async def run_discussion_verification_queue(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    """Run verify tests for the discussion's pending evolution items and close passes."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    from agent_team_api import _evolution_engine

    if not _evolution_engine:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "演化引擎未初始化")

    verify_result = _evolution_engine.verify_pending_items(
        source_plaza_id=plaza_id,
        source_discussion_id=disc_id,
    )
    closed = _evolution_engine.close_verified_items(
        source_plaza_id=plaza_id,
        source_discussion_id=disc_id,
    )
    alerts = _evolution_engine.get_verification_alerts(
        source_plaza_id=plaza_id,
        source_discussion_id=disc_id,
    )
    payload = _build_discussion_verification_state_payload(
        _evolution_engine,
        plaza_id=plaza_id,
        discussion_id=disc_id,
        trigger="verification_queue_run",
    )
    payload["verify"] = verify_result
    payload["closed"] = closed
    await engine._broadcast(disc.id, payload)
    return {
        "plaza_id": plaza_id,
        "discussion_id": disc_id,
        "verify": verify_result,
        "closed": closed,
        "alerts": alerts,
    }


# ── 用户插话（发给议事长判断） ──────────────────────────────

class InterjectRequest(BaseModel):
    message: str = Field(..., min_length=1)


@router.post("/{plaza_id}/discussions/{disc_id}/interject", summary="用户向议事长提问/建议")
async def interject_to_moderator(
    plaza_id: str, disc_id: str, req: InterjectRequest,
) -> Dict[str, Any]:
    """用户发送建议/问题给议事长，议事长判断是否需要发起新一轮讨论或直接回复解释."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    # 找到议事长
    moderator = None
    if disc.moderator_agent_id:
        moderator = plaza.participants.get(disc.moderator_agent_id)
    if not moderator:
        for p in plaza.participants.values():
            if p.niche_role == NicheRole.MODERATOR:
                moderator = p
                break
    if not moderator:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "广场没有议事长")

    # 先广播用户消息
    from .plaza import PlazaMessage
    user_msg = PlazaMessage(
        discussion_id=disc.id,
        agent_id="__user__",
        agent_name="用户",
        role="human",
        niche_role="human",
        content=req.message,
        round_number=disc.current_round,
    )
    user_msg.seq = len(disc.messages)
    disc.messages.append(user_msg)
    await engine._broadcast(disc.id, {
        "type": "message",
        "message": user_msg.to_dict(),
    })

    if disc.status == DiscussionStatus.IN_PROGRESS:
        correction = await engine.handle_live_interjection(
            plaza_id,
            disc_id,
            req.message,
            user_msg.id,
        )
        return {
            "action": "redirect",
            "user_message": user_msg.to_dict(),
            "moderator_reply": correction["moderator_reply"].to_dict() if correction.get("moderator_reply") else None,
            "nominated_reply": correction["nominated_reply"].to_dict() if correction.get("nominated_reply") else None,
            "extra_replies": [m.to_dict() for m in correction.get("extra_replies", [])],
            "moderator_resume": correction["moderator_resume"].to_dict() if correction.get("moderator_resume") else None,
            "new_discussion": None,
        }

    new_disc = None

    if not engine._chat_fn:
        reply_content = f"收到您的建议。关于「{req.message[:30]}」，我会在后续讨论中纳入考虑。"
        action = "reply"
    else:
        recent = engine._format_recent(disc, limit=8)
        prompt = (
            f"你是本场讨论的议事长（主持人）。\n"
            f"讨论话题: 「{disc.topic}」\n"
            f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n\n"
            f"最近对话:\n{recent}\n\n"
            f"现在，观察者（用户）向你提出了建议/问题:\n"
            f"「{req.message}」\n\n"
            f"分诊判据——满足以下任意一条，就必须发起新一轮团队讨论（格式 A）:\n"
            f"1. 用户的问题会推翻或实质修改已形成的结论/执行计划；\n"
            f"2. 回答需要多个专业角色的视角（技术/成本/风险等），你一个人答会以偏概全；\n"
            f"3. 用户提出了讨论中未覆盖的新约束、新目标或新信息；\n"
            f"4. 你对答案没有把握，或团队内本就存在分歧。\n"
            f"只有当问题是澄清性、解释性的（问「为什么」「什么意思」，答案已在讨论中）才直接答复（格式 B）。\n\n"
            f"严格遵守下面格式之一:\n"
            f"格式 A：发起新一轮团队讨论\n"
            f"[NEW_DISCUSSION]\n"
            f"TOPIC: 新讨论标题\n"
            f"GOAL: 新讨论要收敛的问题\n"
            f"REPLY: 你对用户的简短说明（告知已发起团队讨论及原因）\n\n"
            f"格式 B：仅当问题是澄清性的\n"
            f"REPLY: 直接解释，简洁有力，2-4 句\n\n"
            f"- 不要客套，像苏格拉底一样直接"
        )
        decision_text = await engine._generate_agent_content(moderator, prompt)
        action = "new_discussion" if "[NEW_DISCUSSION]" in decision_text else "reply"

        topic = ""
        goal = ""
        reply_lines = []
        for raw_line in decision_text.splitlines():
            line = raw_line.strip()
            if not line or line == "[NEW_DISCUSSION]":
                continue
            if line.startswith("TOPIC:"):
                topic = line.split(":", 1)[1].strip()
                continue
            if line.startswith("GOAL:"):
                goal = line.split(":", 1)[1].strip()
                continue
            if line.startswith("REPLY:"):
                reply_lines.append(line.split(":", 1)[1].strip())
                continue
            reply_lines.append(line)

        reply_content = "\n".join(line for line in reply_lines if line).strip()
        if not reply_content:
            reply_content = "这个追问我先收下。"

        if action == "new_discussion":
            new_disc = engine.create_discussion(
                plaza_id,
                topic or f"追问：{req.message[:24]}",
                f"由用户追问触发，来源讨论：{disc.topic}\n\n用户追问：{req.message}",
                moderator.agent_id,
                2,
            )
            if new_disc:
                new_disc.goal = goal or req.message
                # 修复: 议事长决定开新讨论后必须真正启动它——此前只创建不启动，
                # 新讨论停在 OPEN 状态，用户以为团队在讨论实际无事发生。
                _schedule_discussion_run(engine, plaza_id, new_disc.id)

    mod_msg = PlazaMessage(
        discussion_id=disc.id,
        agent_id=moderator.agent_id,
        agent_name=moderator.agent_name or moderator.agent_id,
        role=moderator.role,
        niche_role="moderator",
        content=reply_content,
        round_number=disc.current_round,
        reply_to=user_msg.id,
    )
    mod_msg.seq = len(disc.messages)
    disc.messages.append(mod_msg)
    await engine._broadcast(disc.id, {
        "type": "message",
        "message": mod_msg.to_dict(),
    })

    engine._store.save_plaza(plaza)

    return {
        "action": action,
        "user_message": user_msg.to_dict(),
        "moderator_reply": mod_msg.to_dict(),
        "new_discussion": new_disc.to_dict() if new_disc else None,
    }


# ── 启动讨论 + SSE 流 ──────────────────────────────────────

@router.post("/{plaza_id}/discussions/{disc_id}/start", summary="启动讨论")
async def start_discussion(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    engine = get_plaza_engine()
    _resolve_startable_discussion(engine, plaza_id, disc_id)
    _schedule_discussion_run(engine, plaza_id, disc_id)
    return {"status": "started", "discussion_id": disc_id}


def _resolve_startable_discussion(engine, plaza_id: str, disc_id: str):
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    if disc.status == DiscussionStatus.CLOSED:
        disc = engine.reset_discussion(plaza_id, disc_id)
    elif disc.status != DiscussionStatus.OPEN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"讨论状态为 {disc.status}，无法启动")
    return disc


def _schedule_discussion_run(engine, plaza_id: str, disc_id: str):
    asyncio.create_task(engine.run_discussion(plaza_id, disc_id))


@router.get("/{plaza_id}/discussions/{disc_id}/stream", summary="SSE 实时消息流")
async def stream_discussion(plaza_id: str, disc_id: str, request: Request):
    """Server-Sent Events 实时推送讨论消息.

    通过穹顶 Oculus 高速数据通道实时传输讨论流。
    支持 Last-Event-ID 头：仅重放断点之后的消息，消除重连重放风暴。
    """
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    q = _subscribe_discussion_stream(engine, disc_id)

    # 断点续传：只重放 Last-Event-ID 之后的消息
    last_seq = _parse_last_event_id(request.headers.get("Last-Event-ID", ""))

    async def event_stream():
        try:
            # 先推送已有消息（支持中途接入，跳过已收消息）
            for event in _iter_replay_message_events(disc, last_seq):
                yield event

            # 推送当前状态（给跳过的 seq 使用虚拟 id）
            status_seq, status_event = _build_stream_status_event(disc)
            yield status_event

            # 如果讨论已结束，推送合成的 plan_updated + discussion_end 事件
            # （SSE 连接时讨论可能已经跑完，需确保前端知道结果）
            if disc.status == DiscussionStatus.CLOSED:
                for event in _iter_closed_discussion_events(disc, status_seq):
                    yield event
                # 讨论已结束，不需要等待实时事件
                return

            # 实时推送新消息
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield _format_live_stream_event(event)
                    if _is_discussion_end_event(event):
                        break
                except asyncio.TimeoutError:
                    yield _build_stream_heartbeat_event()
        finally:
            _unsubscribe_discussion_stream(engine, disc_id, q)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ══════════════════════════════════════════════════════════════
# 监控与遥测 API
# ══════════════════════════════════════════════════════════════

# 全局监控 Channel 引用（在 main.py startup 时注入）
_plaza_monitor_channel = None


def set_plaza_monitor(channel):
    """注入 PlazaMonitorChannel 实例."""
    global _plaza_monitor_channel
    _plaza_monitor_channel = channel


@router.get("/monitoring/status", summary="获取监控状态")
async def monitoring_status() -> Dict[str, Any]:
    """获取广场监控 Channel 状态."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    return _plaza_monitor_channel.get_status()


@router.get("/monitoring/metrics", summary="获取监控指标")
async def monitoring_metrics() -> Dict[str, Any]:
    """获取采集器指标."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    return _plaza_monitor_channel.get_metrics()


@router.get("/monitoring/telemetry", summary="获取遥测记录")
async def monitoring_telemetry(limit: int = 100) -> List[Dict[str, Any]]:
    """获取遥测记录，用于 CI/CD 门禁校验."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    return _plaza_monitor_channel.get_telemetry(limit=limit)


@router.get("/monitoring/active-discussions", summary="获取活跃讨论")
async def monitoring_active_discussions() -> Dict[str, Any]:
    """获取当前活跃的讨论列表."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    return _plaza_monitor_channel.get_active_discussions()


@router.post("/monitoring/degradation", summary="切换降级模式")
async def monitoring_set_degradation(active: bool = True) -> Dict[str, str]:
    """激活或关闭降级模式（全量采集）. """
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    _plaza_monitor_channel.set_degradation_mode(active)
    return {"status": "degradation_activated" if active else "degradation_deactivated"}


@router.post("/monitoring/config", summary="热更新采样策略")
async def monitoring_update_config(config: Dict[str, Any]) -> Dict[str, str]:
    """热更新采样策略配置."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    _plaza_monitor_channel.update_sampling_config(config)
    return {"status": "config_updated"}


@router.get("/monitoring/sampler-stats", summary="获取采样器统计")
async def monitoring_sampler_stats() -> Dict[str, Any]:
    """获取自适应采样器统计."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    collector = _plaza_monitor_channel.get_collector()
    if not collector:
        return {"error": "collector_not_available"}
    return collector.get_sampler_stats()


@router.post("/monitoring/event", summary="手动上报事件")
async def monitoring_report_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """手动上报一个监控事件."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    result = _plaza_monitor_channel.process_event(event)
    if result is None:
        return {"handled": False, "reason": f"未知事件类型: {event.get('type', '')}"}
    return result


# ══════════════════════════════════════════════════════════════════
# Escalation Queue (失败升级)
# ══════════════════════════════════════════════════════════════════

# get_escalation_queue 已上移到 /{plaza_id} 之前（修复路由吞噬 404）。

@router.post("/escalations/{index}/resolve", summary="解决升级项")
async def resolve_escalation(index: int) -> Dict[str, Any]:
    """Mark an escalation entry as resolved by a human operator."""
    engine = get_plaza_engine()
    if engine.resolve_escalation(index):
        return {"status": "resolved", "index": index}
    raise HTTPException(status.HTTP_404_NOT_FOUND, "升级项不存在")


# ══════════════════════════════════════════════════════════════════
# Consensus Measurement (共识度量)
# ══════════════════════════════════════════════════════════════════

@router.get(
    "/{plaza_id}/discussions/{disc_id}/consensus",
    summary="获取讨论共识度",
)
async def get_discussion_consensus(
    plaza_id: str,
    disc_id: str,
    round_number: Optional[int] = Query(None, description="仅分析指定轮次"),
) -> Dict[str, Any]:
    """返回讨论的五指共识（Fist-to-Five）结果。

    共识在 ORID 第四层（决策承诺）产生并存入 discussion.metadata。为兼容既有
    前端共识面板，这里将五指结果适配为原有字段（score/trend/dissenting）。
    """
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    fist = (disc.metadata or {}).get("fist_to_five")
    consensus, dissents = _adapt_fist_to_five(fist)
    return {
        "discussion_id": disc_id,
        "round_number": round_number,
        "consensus": consensus,
        "dissenting_messages": dissents,
        "fist_to_five": fist,
        "fist_to_five_summary": (disc.metadata or {}).get("fist_to_five_summary", ""),
    }


def _adapt_fist_to_five(
    fist: Optional[Dict[str, Any]],
) -> tuple[Dict[str, Any], list]:
    """把五指结果映射到旧共识面板字段。无投票时返回中性 pending 态。"""
    if not fist:
        return {
            "score": 0.5, "agreement_count": 0, "disagreement_count": 0,
            "neutral_count": 0, "dissenting_agents": [],
            "convergence_trend": "stable", "can_early_exit": False,
        }, []

    votes = fist.get("votes", [])
    supportive = [v for v in votes if v.get("fingers", 0) >= 4]
    accepting = [v for v in votes if v.get("fingers", 0) == 3]
    dissenting = [v for v in votes if v.get("fingers", 0) <= 2]
    blocking_ids = fist.get("blocking_agents", [])
    level = fist.get("consensus_level", "none")
    trend = {"strong": "rising", "weak": "stable", "blocked": "falling"}.get(level, "stable")

    consensus = {
        "score": round(float(fist.get("mean_fingers", 0.0)) / 5.0, 3),
        "agreement_count": len(supportive),
        "disagreement_count": len(dissenting),
        "neutral_count": len(accepting),
        "dissenting_agents": blocking_ids,
        "convergence_trend": trend,
        "can_early_exit": bool(fist.get("consensus_reached", False)),
    }
    dissents = [
        {
            "agent_id": v.get("agent_id", ""),
            "agent_name": v.get("agent_name", ""),
            "content_preview": f"{v.get('fingers', 0)}指 · {v.get('reason', '')}"[:150],
            "round_number": 4,
        }
        for v in votes if v.get("fingers", 0) == 1
    ]
    return consensus, dissents
