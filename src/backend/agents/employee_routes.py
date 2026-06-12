# -*- coding: utf-8 -*-
"""Employee Routes — 数字员工档案 API (AgentsGroupConfig E-E).

prefix /api/v1/agent-employee
覆盖: 四件套文件 / 组织上下文预览 / Trigger CRUD / 关系网络 / 治理参数 / 唤醒日志
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .agent_relationships import (
    AgentRelationship, check_can_communicate, get_relationship_store,
    relationship_gate_mode,
)
from .agent_triggers import (
    AgentTrigger, compute_next_fire, get_trigger_daemon, get_trigger_store,
    validate_trigger,
)
from .employee_profile import (
    FILE_KINDS, build_organizational_context, check_token_budget,
    get_employee_store,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-employee", tags=["agent-employee"])


# ── Request models ─────────────────────────────────────────

class WriteFileRequest(BaseModel):
    content: str = ""


class AppendMemoryRequest(BaseModel):
    entry: str = ""
    source: str = "human"


class TriggerRequest(BaseModel):
    trigger_type: str = "cron"
    enabled: bool = True
    focus_item: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)


class RelationshipRequest(BaseModel):
    kind: str = "agent_agent"
    source_agent_id: str = ""
    target_id: str = ""
    rel_type: str = "collaborator"
    note: str = ""
    created_by: str = "human"


class GovernanceRequest(BaseModel):
    autonomy_level: Optional[int] = Field(default=None, ge=1, le=4)
    token_budget: Optional[int] = Field(default=None, ge=0)
    fallback_model_id: Optional[str] = None


def _find_agent(team_id: str, agent_id: str):
    """取 AgentProfile（404 语义），团队/Agent 不存在时返回 None 容错."""
    try:
        from .api import _tm
        team = _tm().get_team(team_id)
        if not team:
            return None, None
        return team, team.get_agent(agent_id)
    except Exception as e:
        logger.debug(f"team_manager 不可用: {e}")
        return None, None


# ── EE-1: 四件套 ───────────────────────────────────────────

@router.get("/agents/{agent_id}/files/{kind}")
async def get_employee_file(agent_id: str, kind: str) -> Dict[str, Any]:
    if kind not in FILE_KINDS:
        raise HTTPException(status_code=404, detail=f"kind 必须是 {FILE_KINDS}")
    store = get_employee_store()
    store.ensure_defaults(agent_id)
    return store.read_file(agent_id, kind)


@router.put("/agents/{agent_id}/files/{kind}")
async def put_employee_file(agent_id: str, kind: str, req: WriteFileRequest) -> Dict[str, Any]:
    if kind not in FILE_KINDS:
        raise HTTPException(status_code=404, detail=f"kind 必须是 {FILE_KINDS}")
    if kind == "memory":
        raise HTTPException(status_code=405,
                            detail="memory.md 只追加不整写，请用 POST .../files/memory/append")
    result = get_employee_store().write_file(agent_id, kind, req.content)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/agents/{agent_id}/files/memory/append")
async def append_memory(agent_id: str, req: AppendMemoryRequest) -> Dict[str, Any]:
    result = get_employee_store().append_memory(agent_id, req.entry, req.source)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/agents/{agent_id}/files/heartbeat/reset")
async def reset_heartbeat(agent_id: str) -> Dict[str, Any]:
    return get_employee_store().reset_heartbeat(agent_id)


@router.get("/agents/{agent_id}/focus-items")
async def list_focus_items(agent_id: str) -> Dict[str, Any]:
    store = get_employee_store()
    store.ensure_defaults(agent_id)
    return {"agent_id": agent_id, "items": store.parse_focus_items(agent_id)}


# ── EE-2: 组织上下文预览 ───────────────────────────────────

@router.get("/teams/{team_id}/agents/{agent_id}/context")
async def preview_context(team_id: str, agent_id: str) -> Dict[str, Any]:
    store = get_employee_store()
    _, agent = _find_agent(team_id, agent_id)
    store.ensure_defaults(agent_id, agent.to_dict() if agent else {})
    return build_organizational_context(team_id, agent_id, store)


# ── EE-3: Trigger CRUD ─────────────────────────────────────

@router.get("/teams/{team_id}/agents/{agent_id}/triggers")
async def list_triggers(team_id: str, agent_id: str) -> Dict[str, Any]:
    triggers = get_trigger_store().list_for_agent(team_id, agent_id)
    return {"triggers": [t.to_dict() for t in triggers], "total": len(triggers)}


@router.post("/teams/{team_id}/agents/{agent_id}/triggers")
async def create_trigger(team_id: str, agent_id: str, req: TriggerRequest) -> Dict[str, Any]:
    trigger = AgentTrigger(agent_id=agent_id, team_id=team_id,
                           trigger_type=req.trigger_type, enabled=req.enabled,
                           focus_item=req.focus_item, config=req.config)
    store = get_employee_store()
    store.ensure_defaults(agent_id)
    errors = validate_trigger(trigger, focus_checker=store.focus_item_exists)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    get_trigger_store().add(trigger)
    return trigger.to_dict()


@router.put("/teams/{team_id}/triggers/{trigger_id}")
async def update_trigger(team_id: str, trigger_id: str, req: TriggerRequest) -> Dict[str, Any]:
    trg = get_trigger_store().get(team_id, trigger_id)
    if not trg:
        raise HTTPException(status_code=404, detail="trigger not found")
    trg.trigger_type = req.trigger_type
    trg.enabled = req.enabled
    trg.focus_item = req.focus_item
    trg.config = req.config
    store = get_employee_store()
    errors = validate_trigger(trg, focus_checker=store.focus_item_exists)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    nxt = compute_next_fire(trg)
    trg.next_fire_at = nxt.isoformat() if nxt else None
    get_trigger_store().update(trg)
    return trg.to_dict()


@router.post("/teams/{team_id}/triggers/{trigger_id}/toggle")
async def toggle_trigger(team_id: str, trigger_id: str) -> Dict[str, Any]:
    trg = get_trigger_store().get(team_id, trigger_id)
    if not trg:
        raise HTTPException(status_code=404, detail="trigger not found")
    trg.enabled = not trg.enabled
    get_trigger_store().update(trg)
    return {"trigger_id": trigger_id, "enabled": trg.enabled}


@router.delete("/teams/{team_id}/triggers/{trigger_id}")
async def delete_trigger(team_id: str, trigger_id: str) -> Dict[str, Any]:
    if not get_trigger_store().delete(team_id, trigger_id):
        raise HTTPException(status_code=404, detail="trigger not found")
    return {"deleted": True}


# ── EE-4: 关系网络 ─────────────────────────────────────────

@router.get("/teams/{team_id}/relationships")
async def list_relationships(team_id: str, agent_id: str = Query(default="")) -> Dict[str, Any]:
    store = get_relationship_store()
    rels = (store.list_for_agent(team_id, agent_id) if agent_id
            else store.list_team(team_id))
    return {
        "relationships": [r.to_dict() for r in rels],
        "total": len(rels),
        "gate_mode": relationship_gate_mode(),
    }


@router.post("/teams/{team_id}/relationships")
async def create_relationship(team_id: str, req: RelationshipRequest) -> Dict[str, Any]:
    rel = AgentRelationship(team_id=team_id, kind=req.kind,
                            source_agent_id=req.source_agent_id,
                            target_id=req.target_id, rel_type=req.rel_type,
                            note=req.note, created_by=req.created_by)
    result = get_relationship_store().add(rel)
    if not result.get("ok"):
        code = 409 if result.get("error") == "duplicate" else 422
        raise HTTPException(status_code=code, detail=result)
    return rel.to_dict()


@router.delete("/teams/{team_id}/relationships/{rel_id}")
async def delete_relationship(team_id: str, rel_id: str) -> Dict[str, Any]:
    if not get_relationship_store().remove(team_id, rel_id):
        raise HTTPException(status_code=404, detail="relationship not found")
    return {"deleted": True}


@router.get("/teams/{team_id}/agents/{agent_id}/can-communicate")
async def can_communicate(team_id: str, agent_id: str,
                          target: str = Query(default="")) -> Dict[str, Any]:
    if not target:
        raise HTTPException(status_code=400, detail="target 必填")
    return check_can_communicate(team_id, agent_id, target)


# ── EE-5: 治理参数 ─────────────────────────────────────────

@router.get("/teams/{team_id}/agents/{agent_id}/governance")
async def get_governance(team_id: str, agent_id: str) -> Dict[str, Any]:
    _, agent = _find_agent(team_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")
    return {
        "agent_id": agent_id,
        "autonomy_level": getattr(agent, "autonomy_level", 2),
        "token_budget": getattr(agent, "token_budget", 0),
        "fallback_model_id": getattr(agent, "fallback_model_id", ""),
        "budget_status": check_token_budget(agent),
    }


@router.put("/teams/{team_id}/agents/{agent_id}/governance")
async def put_governance(team_id: str, agent_id: str, req: GovernanceRequest) -> Dict[str, Any]:
    team, agent = _find_agent(team_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")
    if req.autonomy_level is not None:
        agent.autonomy_level = req.autonomy_level
    if req.token_budget is not None:
        agent.token_budget = req.token_budget
    if req.fallback_model_id is not None:
        agent.fallback_model_id = req.fallback_model_id
    try:
        from .api import _tm
        _tm()._persist()
    except Exception as e:
        logger.warning(f"治理参数持久化失败 (非致命): {e}")
    return await get_governance(team_id, agent_id)


# ── EE-6: 唤醒日志 ─────────────────────────────────────────

@router.get("/teams/{team_id}/agents/{agent_id}/wake-log")
async def wake_log(team_id: str, agent_id: str,
                   limit: int = Query(default=20, ge=1, le=100)) -> Dict[str, Any]:
    events = get_trigger_daemon().read_wake_log(agent_id=agent_id, limit=limit)
    return {"events": events, "total": len(events)}
