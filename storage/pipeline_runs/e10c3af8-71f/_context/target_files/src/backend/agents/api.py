# -*- coding: utf-8 -*-
"""AgentsGroup2026 Agent Team Framework -- REST API Router.

Clawith-style CRUD API for teams, agents, models, tools, skills.
Tab-based organization:
  1. Team Info
  2. Model Pool
  3. Tools
  4. Skills
  5. Agents -- 5-step wizard
  6. Overview
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from .models import (
    AccessLevel,
    AgentState,
    AgentChannelConfig,
    AgentPermission,
    AgentPersonality,
    AgentProfile,
    AgentTemplateType,
    HermesAgentConfig,
    ModelConfig,
    ToolsetDistribution,
)
from .hermes_research import (
    RESEARCH_TOOLSET_DISTRIBUTIONS,
    HERMES_TOOLSETS,
    create_hermes_researcher,
    build_research_system_prompt,
    sample_toolsets,
    resolve_tools,
    get_research_distributions,
    get_hermes_toolsets,
)
from .chat_harness import (
    ChatHarness,
    LLMProvider,
    ProviderConfig,
    get_chat_harness,
)
from .execution_registry import (
    ToolPermissionContext,
    PortRuntime,
    assemble_tool_pool,
    build_execution_registry,
)
from .session_store import (
    list_sessions as list_stored_sessions,
    search_sessions,
)
from .skill_registry import SkillRegistry, get_default_skills
from .team_manager import TeamManager
from .tool_registry import ToolRegistry, get_default_tools


router = APIRouter(prefix="/api/v1/agent-config", tags=["agent-config"])


_team_manager: Optional[TeamManager] = None
_tool_registry: Optional[ToolRegistry] = None
_skill_registry: Optional[SkillRegistry] = None

# ── Model Pool Persistence ──
import os as _mp_os, json as _mp_json

_MODEL_POOL_PATH = _mp_os.path.join(
    _mp_os.path.dirname(_mp_os.path.dirname(_mp_os.path.dirname(
        _mp_os.path.dirname(_mp_os.path.abspath(__file__))))),
    "config", "model_pool.json"
)


def _save_model_pool() -> None:
    """Persist all teams' model pool to config/model_pool.json."""
    if _team_manager is None:
        return
    data: Dict[str, Any] = {}
    for team in _team_manager.list_teams():
        team_models = {}
        for m in team.models.values():
            team_models[m.model_id] = {
                "model_id": m.model_id,
                "provider": m.provider,
                "name": m.name,
                "max_tokens": m.max_tokens,
                "temperature": m.temperature,
                "is_default": m.is_default,
                "enabled": m.enabled,
                "api_key": m.api_key,
                "api_base_url": m.api_base_url,
            }
        data[team.team_id] = team_models
    try:
        _mp_os.makedirs(_mp_os.path.dirname(_MODEL_POOL_PATH), exist_ok=True)
        with open(_MODEL_POOL_PATH, "w", encoding="utf-8") as f:
            _mp_json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _load_model_pool(tm: TeamManager) -> None:
    """Load persisted model pool from config/model_pool.json, overriding defaults."""
    if not _mp_os.path.isfile(_MODEL_POOL_PATH):
        return
    try:
        with open(_MODEL_POOL_PATH, "r", encoding="utf-8") as f:
            data = _mp_json.load(f)
    except Exception:
        return
    for team in tm.list_teams():
        team_data = data.get(team.team_id)
        if not team_data:
            continue
        # Replace the entire model pool with persisted version
        team.models.clear()
        for mid, mdata in team_data.items():
            model = ModelConfig(
                model_id=mdata.get("model_id", mid),
                provider=mdata.get("provider", "deepseek"),
                name=mdata.get("name", "deepseek-chat"),
                max_tokens=mdata.get("max_tokens", 8192),
                temperature=mdata.get("temperature", 0.7),
                is_default=mdata.get("is_default", False),
                enabled=mdata.get("enabled", True),
                api_key=mdata.get("api_key", ""),
                api_base_url=mdata.get("api_base_url", ""),
            )
            team.add_model(model)


def init_agent_config(team_manager: TeamManager) -> None:
    """Inject the TeamManager instance at startup."""
    global _team_manager, _tool_registry, _skill_registry
    _team_manager = team_manager
    _tool_registry = ToolRegistry()
    _tool_registry.load_defaults()
    _skill_registry = SkillRegistry()
    _skill_registry.load_defaults()
    # Load persisted model pool (overrides hardcoded defaults)
    _load_model_pool(team_manager)
    # Sync any existing default model to the chat harness
    _init_harness_from_teams(team_manager)
    # Initialize skill extractor engine
    init_skill_extractor()
    # Initialize skill library
    from .skill_library import init_skill_library, get_skill_library
    from .skill_store import SkillStore
    _skill_store = SkillStore()
    init_skill_library(
        team_manager=team_manager,
        skill_registry=_skill_registry,
        skill_store=_skill_store,
    )
    # Initialize skill tracker, evolver, verifier
    from .skill_tracker import init_skill_tracker
    from .skill_evolver import init_skill_evolver
    from .skill_verifier import init_skill_verifier
    _lib = get_skill_library()
    init_skill_tracker(skill_library=_lib)
    init_skill_evolver(skill_library=_lib, chat_harness=None)
    init_skill_verifier(skill_library=_lib, chat_harness=None)


def _get_tool_registry() -> ToolRegistry:
    """Get or create the global ToolRegistry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        _tool_registry.load_defaults()
    return _tool_registry


def _get_skill_registry() -> SkillRegistry:
    """Get or create the global SkillRegistry."""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
        _skill_registry.load_defaults()
    return _skill_registry


def _init_harness_from_teams(tm: TeamManager) -> None:
    """On startup, push the first team's default model into the chat harness."""
    try:
        harness = get_chat_harness()
        for team in tm.list_teams():
            for m in team.models.values():
                if m.is_default and m.api_key:
                    harness.update_default_provider(
                        provider=m.provider,
                        api_key=m.api_key,
                        api_base_url=m.api_base_url,
                        model=m.name,
                    )
                    cfg = harness.get_provider_config()
                    cfg.max_tokens = m.max_tokens
                    cfg.temperature = m.temperature
                    return
    except Exception:
        pass  # Non-critical, harness will use env/settings fallback


def _tm() -> TeamManager:
    if _team_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent config service not initialized",
        )
    return _team_manager


def _tr() -> ToolRegistry:
    if _tool_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tool registry not initialized",
        )
    return _tool_registry


def _sr() -> SkillRegistry:
    if _skill_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Skill registry not initialized",
        )
    return _skill_registry


# Request / Response Models


class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""


class CreateModelRequest(BaseModel):
    provider: str = "anthropic"
    name: str = "claude-sonnet-4-20250514"
    max_tokens: int = Field(default=8192, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    is_default: bool = False
    api_key: str = ""
    api_base_url: str = ""


class CreateAgentRequest(BaseModel):
    """Step 1 of agent wizard -- basic info."""
    name: str = Field(..., min_length=1, max_length=128)
    role: str = ""
    description: str = ""
    template_type: str = "custom"
    model_id: str = ""
    system_prompt: str = ""


class UpdatePersonalityRequest(BaseModel):
    """Step 2 -- personality config."""
    tone: str = "professional"
    language: str = "zh-CN"
    expertise_areas: List[str] = Field(default_factory=list)
    response_style: str = "concise"
    creativity: float = Field(default=0.5, ge=0.0, le=1.0)


class UpdateToolsRequest(BaseModel):
    """Assign tools to an agent."""
    tool_ids: List[str] = Field(default_factory=list)


class UpdateSkillsRequest(BaseModel):
    """Step 3 -- assign skills."""
    skill_ids: List[str] = Field(default_factory=list)


class PermissionItem(BaseModel):
    resource: str = ""
    access_level: str = "read"
    channels: List[str] = Field(default_factory=list)


class UpdatePermissionsRequest(BaseModel):
    """Step 4 -- permissions."""
    permissions: List[PermissionItem] = Field(default_factory=list)


class ChannelItem(BaseModel):
    channel_name: str = ""
    subscribe: bool = True
    publish: bool = False
    priority: int = 0


class UpdateChannelsRequest(BaseModel):
    """Step 5 -- channel subscriptions."""
    channels: List[ChannelItem] = Field(default_factory=list)


# TAB 1 -- TEAM INFO


@router.get("/teams", summary="List all teams")
def list_teams() -> List[Dict[str, Any]]:
    return [
        {
            "team_id": t.team_id,
            "name": t.name,
            "description": t.description,
            "agent_count": len(t.agents),
            "model_count": len(t.models),
        }
        for t in _tm().list_teams()
    ]


@router.get("/teams-tree", summary="All teams with agents tree")
def teams_tree() -> List[Dict[str, Any]]:
    """返回团队→智能体树状结构，供广场选人使用."""
    result = []
    for t in _tm().list_teams():
        agents_list = t.agents
        if isinstance(agents_list, dict):
            agents_list = list(agents_list.values())
        result.append({
            "team_id": t.team_id,
            "name": t.name,
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "name": a.name or a.agent_id,
                    "role": a.role or "",
                }
                for a in agents_list
            ],
        })
    return result


@router.get("/teams/{team_id}", summary="Get team detail")
def get_team(team_id: str) -> Dict[str, Any]:
    team = _tm().get_team(team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team.to_dict()


@router.post(
    "/teams",
    summary="Create team",
    status_code=status.HTTP_201_CREATED,
)
def create_team(req: CreateTeamRequest) -> Dict[str, Any]:
    team = _tm().create_team(name=req.name, description=req.description)
    return team.to_dict()


@router.delete("/teams/{team_id}", summary="Delete team")
def delete_team(team_id: str) -> Dict[str, str]:
    removed = _tm().delete_team(team_id)
    if removed is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
    return {"deleted": team_id}


# TAB 2 -- MODEL POOL


def _get_team_or_404(team_id: str):
    team = _tm().get_team(team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.get("/teams/{team_id}/models", summary="List team models")
def list_models(team_id: str) -> List[Dict[str, Any]]:
    team = _get_team_or_404(team_id)
    return [m.to_dict() for m in team.models.values()]


@router.post(
    "/teams/{team_id}/models",
    summary="Add model to team",
    status_code=status.HTTP_201_CREATED,
)
def add_model(team_id: str, req: CreateModelRequest) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    model = ModelConfig(
        provider=req.provider,
        name=req.name,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        is_default=req.is_default,
        api_key=req.api_key,
        api_base_url=req.api_base_url,
    )
    team.add_model(model)
    if req.is_default:
        _set_team_default_model(team, model.model_id)
        _sync_default_model_to_harness(team)
    _save_model_pool()
    return model.to_dict()


@router.put(
    "/teams/{team_id}/models/{model_id}",
    summary="Update a model in the team pool",
)
def update_model(team_id: str, model_id: str, req: CreateModelRequest) -> Dict[str, Any]:
    """Edit an existing model's configuration."""
    team = _get_team_or_404(team_id)
    model = team.get_model(model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Model not found")
    model.provider = req.provider
    model.name = req.name
    model.max_tokens = req.max_tokens
    model.temperature = req.temperature
    if req.api_key:
        model.api_key = req.api_key
    if req.api_base_url:
        model.api_base_url = req.api_base_url
    if req.is_default:
        _set_team_default_model(team, model_id)
    else:
        model.is_default = False
    # Sync to chat harness
    _sync_default_model_to_harness(team)
    _save_model_pool()
    return model.to_dict()


@router.put(
    "/teams/{team_id}/models/{model_id}/default",
    summary="Set a model as team default",
)
def set_default_model(team_id: str, model_id: str) -> Dict[str, Any]:
    """Set one model as the team default; clears default on all others."""
    team = _get_team_or_404(team_id)
    model = team.get_model(model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Model not found")
    _set_team_default_model(team, model_id)
    # Sync to chat harness
    _sync_default_model_to_harness(team)
    _save_model_pool()
    return {"model_id": model_id, "is_default": True}


def _set_team_default_model(team, model_id: str) -> None:
    """Clear is_default on all models, then set the specified one.

    Also migrates agents whose model_id was the old default to the new one,
    so that agent settings pages always reflect the current default model.
    """
    # Find old default model_id
    old_default_id: str | None = None
    for m in team.models.values():
        if m.is_default:
            old_default_id = m.model_id
            break

    # Toggle is_default flag
    for m in team.models.values():
        m.is_default = (m.model_id == model_id)

    # Propagate: agents using old default → new default
    if old_default_id and old_default_id != model_id:
        for agent in team.agents.values():
            if agent.model_id == old_default_id:
                agent.model_id = model_id


def _sync_default_model_to_harness(team) -> None:
    """Push the team's default model config into the ChatHarness."""
    harness = get_chat_harness()
    default_model = None
    for m in team.models.values():
        if m.is_default:
            default_model = m
            break
    if default_model is None:
        return
    harness.update_default_provider(
        provider=default_model.provider,
        api_key=default_model.api_key,
        api_base_url=default_model.api_base_url,
        model=default_model.name,
    )
    cfg = harness.get_provider_config()
    cfg.max_tokens = default_model.max_tokens
    cfg.temperature = default_model.temperature


@router.delete(
    "/teams/{team_id}/models/{model_id}",
    summary="Remove model from team",
)
def remove_model(team_id: str, model_id: str) -> Dict[str, str]:
    removed = _tm().remove_model_from_team(team_id, model_id)
    if removed is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Model not found")
    _save_model_pool()
    return {"deleted": model_id}


# TAB 3 -- TOOLS


@router.get("/tools", summary="List all available tools")
def list_all_tools() -> List[Dict[str, Any]]:
    return [t.to_dict() for t in _tr().list_all()]


@router.get("/teams/{team_id}/tools", summary="List team tools")
def list_team_tools(team_id: str) -> List[Dict[str, Any]]:
    team = _get_team_or_404(team_id)
    return [t.to_dict() for t in team.tools.values()]


@router.post(
    "/teams/{team_id}/tools/{tool_id}/enable",
    summary="Enable a tool for team",
)
def enable_tool(team_id: str, tool_id: str) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    if tool_id not in team.tools:
        source = _tr().get(tool_id)
        if source is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Tool not found in registry"
            )
        team.add_tool(source)
    tool = team.tools[tool_id]
    tool.enabled = True
    _tm()._persist()
    return tool.to_dict()


@router.post(
    "/teams/{team_id}/tools/{tool_id}/disable",
    summary="Disable a tool for team",
)
def disable_tool(team_id: str, tool_id: str) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    tool = team.tools.get(tool_id)
    if tool is None:
        # Auto-add tool from registry then disable (symmetric with enable)
        source = _tr().get(tool_id)
        if source is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Tool not found in registry"
            )
        team.add_tool(source)
        tool = team.tools[tool_id]
    tool.enabled = False
    _tm()._persist()
    return tool.to_dict()


# TAB 4 -- SKILLS


@router.get("/skills", summary="List all available skills")
def list_all_skills() -> List[Dict[str, Any]]:
    return [s.to_dict() for s in _sr().list_all()]


@router.get("/skills/required", summary="List required skills")
def list_required_skills() -> List[Dict[str, Any]]:
    return [s.to_dict() for s in _sr().list_required()]


@router.get("/teams/{team_id}/skills", summary="List team skills")
def list_team_skills(team_id: str) -> List[Dict[str, Any]]:
    team = _get_team_or_404(team_id)
    return [s.to_dict() for s in team.skills.values()]


# ── Skill Distillation / Extraction ─────────────────────────────────────
# Import the skill extractor engine

from .skill_extractor import (
    SkillReviewItem, SkillReviewStatus, SkillExtractorEngine,
    get_skill_extractor_engine, init_skill_extractor,
    status_traffic_light, status_icon, status_label,
)


def _broadcast_cross_team(origin_team_id: str, event_type: str, data: Dict[str, Any]):
    """Broadcast SSE event to all teams except the origin team."""
    import json as _json
    engine = get_skill_extractor_engine()
    for team_id, qs in engine._sse_queues.items():
        if team_id == origin_team_id:
            continue
        payload = _json.dumps({"type": event_type, **data}, ensure_ascii=False)
        dead = []
        for q in qs:
            try:
                q.put_nowait(payload)
            except Exception:
                dead.append(q)
        for q in dead:
            qs.remove(q)


class StartExtractionRequest(BaseModel):
    source_text: str = Field(..., min_length=10, max_length=200000)
    source_title: str = ""
    source_type: str = "chat"


class EditDraftRequest(BaseModel):
    field_updates: Dict[str, Any] = Field(default_factory=dict)


class ReviewActionRequest(BaseModel):
    reviewer: str = ""
    reason: str = ""
    edited_fields: Optional[Dict[str, Any]] = None


@router.post(
    "/teams/{team_id}/skill-extract/start",
    summary="Start skill extraction from raw text (async LLM pre-fill)",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_skill_extraction(team_id: str, req: StartExtractionRequest) -> Dict[str, Any]:
    """Create a queue item and trigger async LLM pre-fill.
    Returns immediately; subscribe to SSE for status updates."""
    _get_team_or_404(team_id)
    engine = get_skill_extractor_engine()
    item = await engine.start_extraction(
        team_id=team_id,
        source_text=req.source_text,
        source_title=req.source_title,
        source_type=req.source_type,
    )
    return item.to_dict()


@router.get("/teams/{team_id}/skill-extract/queue", summary="Get pending review queue")
def get_extract_queue(
    team_id: str,
    status_filter: str = "",
) -> List[Dict[str, Any]]:
    """Return review queue items. Filter by status: pending, ready_for_review, approved, rejected."""
    _get_team_or_404(team_id)
    engine = get_skill_extractor_engine()
    return engine.get_queue(team_id, status_filter=status_filter)


@router.get("/teams/{team_id}/skill-extract/stream", summary="SSE stream for skill extraction events")
async def stream_skill_extract(team_id: str):
    """SSE endpoint: pushes real-time events for skill extraction queue changes.
    Events: item_created, item_status_changed, item_edited, skill_approved, skill_rejected, item_deleted."""
    from fastapi.responses import StreamingResponse

    engine = get_skill_extractor_engine()
    q = engine.subscribe(team_id)

    async def event_stream():
        try:
            # Send initial state
            initial = json.dumps({
                "type": "connected",
                "team_id": team_id,
                "queue": engine.get_queue(team_id),
            }, ensure_ascii=False)
            yield f"data: {initial}\n\n"

            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            engine.unsubscribe(team_id, q)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/teams/{team_id}/skill-extract/{item_id}", summary="Get review item detail with diff view")
def get_extract_item(team_id: str, item_id: str) -> Dict[str, Any]:
    """Get full item detail including source_text and llm_raw_response for comparison view."""
    _get_team_or_404(team_id)
    engine = get_skill_extractor_engine()
    item = engine.get_item(team_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review item not found")
    return item


@router.post(
    "/teams/{team_id}/skill-extract/{item_id}/approve",
    summary="Approve skill and write to main table (SkillApproved event)",
)
async def approve_skill_item(
    team_id: str, item_id: str, req: ReviewActionRequest = ReviewActionRequest()
) -> Dict[str, Any]:
    """Approve the skill draft, optionally with edited fields. Fires SkillApproved event."""
    _get_team_or_404(team_id)
    engine = get_skill_extractor_engine()
    result = await engine.approve_item(
        team_id=team_id,
        item_id=item_id,
        reviewer=req.reviewer,
        edited_fields=req.edited_fields,
    )
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review item not found")
    return result


@router.post(
    "/teams/{team_id}/skill-extract/{item_id}/reject",
    summary="Reject skill draft",
)
async def reject_skill_item(
    team_id: str, item_id: str, req: ReviewActionRequest = ReviewActionRequest()
) -> Dict[str, Any]:
    """Reject the skill draft with optional reason."""
    _get_team_or_404(team_id)
    engine = get_skill_extractor_engine()
    result = await engine.reject_item(
        team_id=team_id,
        item_id=item_id,
        reviewer=req.reviewer,
        reason=req.reason,
    )
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review item not found")
    return result


@router.post(
    "/teams/{team_id}/skill-extract/{item_id}/edit",
    summary="Edit draft fields before approval",
)
async def edit_skill_draft(
    team_id: str, item_id: str, req: EditDraftRequest
) -> Dict[str, Any]:
    """Edit one or more draft fields before final approval."""
    _get_team_or_404(team_id)
    engine = get_skill_extractor_engine()
    result = await engine.edit_item(
        team_id=team_id,
        item_id=item_id,
        field_updates=req.field_updates,
    )
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review item not found")
    return result


@router.delete(
    "/teams/{team_id}/skill-extract/{item_id}",
    summary="Delete a review queue item",
)
async def delete_extract_item(team_id: str, item_id: str) -> Dict[str, str]:
    """Remove an item from the review queue."""
    _get_team_or_404(team_id)
    engine = get_skill_extractor_engine()
    deleted = await engine.delete_item(team_id, item_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review item not found")
    return {"deleted": item_id}


# ═══════════════════════════════════════════════════════════════════
# SKILL LIBRARY — 统一技能库 API
# ═══════════════════════════════════════════════════════════════════

from .skill_library import get_skill_library


@router.get("/skill-library", summary="Browse unified skill library")
def browse_skill_library(
    team_id: str = "",
    query: str = "",
    visibility: str = "",
    category: str = "",
    lifecycle: str = "",
) -> List[Dict[str, Any]]:
    lib = get_skill_library()
    return lib.browse(
        team_id=team_id,
        query=query,
        visibility_filter=visibility,
        category_filter=category,
        lifecycle_filter=lifecycle,
    )


@router.get("/skill-library/overview", summary="Global skill library overview")
def skill_library_overview() -> Dict[str, Any]:
    lib = get_skill_library()
    return lib.get_overview()


class PublishRequest(BaseModel):
    team_id: str
    skill_id: str


@router.post("/skill-library/publish", summary="Publish skill to public library")
def publish_skill(req: PublishRequest) -> Dict[str, Any]:
    lib = get_skill_library()
    result = lib.publish(req.team_id, req.skill_id)
    if "error" in result:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result["error"])
    # Cross-team SSE notification: broadcast publish event to all teams
    skill = lib._find_skill(req.team_id, req.skill_id)
    if skill:
        _broadcast_cross_team(req.team_id, "skill_published", {
            "origin_team_id": req.team_id,
            "skill_id": req.skill_id,
            "skill_name": skill.name,
            "skill_icon": skill.icon,
        })
    return result


class ImportRequest(BaseModel):
    target_team_id: str
    skill_id: str


@router.post("/skill-library/import", summary="Import skill to team")
def import_skill(req: ImportRequest) -> Dict[str, Any]:
    lib = get_skill_library()
    result = lib.import_skill(req.target_team_id, req.skill_id)
    if "error" in result:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/skill-library/find-duplicates", summary="Find duplicate skills across teams")
def find_skill_duplicates(threshold: float = 0.85) -> List[Dict[str, Any]]:
    lib = get_skill_library()
    return lib.find_duplicates(threshold)


class MergeRequest(BaseModel):
    skill_ids: List[str]
    strategy: str = "keep_longest"


@router.post("/skill-library/merge", summary="Merge duplicate skills")
def merge_skills(req: MergeRequest) -> Dict[str, Any]:
    # Placeholder — will be wired to MergeEngine in Phase 4
    return {"status": "merge_not_implemented_yet", "skill_ids": req.skill_ids}


@router.get("/skill-library/{skill_id}/lineage", summary="Get skill evolution lineage")
def get_skill_lineage(skill_id: str) -> Dict[str, Any]:
    lib = get_skill_library()
    return lib.get_lineage(skill_id)


class SolidifyRequest(BaseModel):
    team_id: str
    skill_id: str


@router.post("/skill-library/solidify", summary="Solidify skill and push to adopted teams")
def solidify_skill(req: SolidifyRequest) -> Dict[str, Any]:
    lib = get_skill_library()
    result = lib.solidify(req.team_id, req.skill_id)
    if "error" in result:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


# ── Evolution & Tracking API ─────────────────────────────────────

from .skill_evolver import get_skill_evolver
from .skill_tracker import get_skill_tracker


@router.get("/skill-library/suggestions", summary="Get evolution suggestions")
def get_evolution_suggestions(team_id: str = "") -> List[Dict[str, Any]]:
    evolver = get_skill_evolver()
    return evolver.suggest_evolution(team_id)


class EvolveRequest(BaseModel):
    team_id: str
    skill_id: str
    evidence_sessions: List[str] = []


@router.post("/skill-library/evolve", summary="Trigger skill evolution")
async def evolve_skill(req: EvolveRequest) -> Dict[str, Any]:
    evolver = get_skill_evolver()
    result = await evolver.evolve_skill(req.team_id, req.skill_id, req.evidence_sessions or None)
    if "error" in result:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


class ApplyEvolutionRequest(BaseModel):
    team_id: str
    skill_id: str
    new_instructions: str


@router.post("/skill-library/apply-evolution", summary="Apply evolution after review")
def apply_evolution(req: ApplyEvolutionRequest) -> Dict[str, Any]:
    evolver = get_skill_evolver()
    result = evolver.apply_evolution(req.team_id, req.skill_id, req.new_instructions)
    if "error" in result:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/skill-library/{skill_id}/evolution-history", summary="Get evolution history")
def get_evolution_history(skill_id: str, team_id: str = "") -> Dict[str, Any]:
    evolver = get_skill_evolver()
    return evolver.get_evolution_history(team_id, skill_id)


# ── Verification API ──────────────────────────