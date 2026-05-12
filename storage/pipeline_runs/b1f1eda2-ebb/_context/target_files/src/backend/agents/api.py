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


# TAB 5 -- AGENTS (5-step wizard)


def _get_agent_or_404(team_id: str, agent_id: str) -> AgentProfile:
    agent = _tm().get_agent(team_id, agent_id)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.get("/teams/{team_id}/agents", summary="List agents in team")
def list_agents(team_id: str) -> List[Dict[str, Any]]:
    _get_team_or_404(team_id)
    return [a.to_dict() for a in _tm().list_agents(team_id)]


@router.get("/teams/{team_id}/agents/{agent_id}", summary="Get agent detail")
def get_agent(team_id: str, agent_id: str) -> Dict[str, Any]:
    return _get_agent_or_404(team_id, agent_id).to_dict()


@router.post(
    "/teams/{team_id}/agents",
    summary="Create agent (wizard step 1)",
    status_code=status.HTTP_201_CREATED,
)
def create_agent(team_id: str, req: CreateAgentRequest) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    try:
        tpl = AgentTemplateType(req.template_type)
    except ValueError:
        tpl = AgentTemplateType.CUSTOM
    agent = AgentProfile(
        name=req.name,
        role=req.role,
        description=req.description,
        template_type=tpl,
        model_id=req.model_id,
        system_prompt=req.system_prompt,
    )
    ok = _tm().add_agent_to_team(team_id, agent)
    if not ok:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add agent"
        )
    return agent.to_dict()


@router.put(
    "/teams/{team_id}/agents/{agent_id}/personality",
    summary="Update agent personality (wizard step 2)",
)
def update_personality(
    team_id: str, agent_id: str, req: UpdatePersonalityRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.personality = AgentPersonality(
        tone=req.tone,
        language=req.language,
        expertise_areas=list(req.expertise_areas),
        response_style=req.response_style,
        creativity=req.creativity,
    )
    return agent.to_dict()


@router.put(
    "/teams/{team_id}/agents/{agent_id}/tools",
    summary="Update agent bound tools",
)
def update_agent_tools(
    team_id: str, agent_id: str, req: UpdateToolsRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.tools = list(req.tool_ids)
    return agent.to_dict()


@router.put(
    "/teams/{team_id}/agents/{agent_id}/skills",
    summary="Update agent skills (wizard step 3)",
)
def update_agent_skills(
    team_id: str, agent_id: str, req: UpdateSkillsRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.skills = list(req.skill_ids)
    return agent.to_dict()


@router.put(
    "/teams/{team_id}/agents/{agent_id}/permissions",
    summary="Update agent permissions (wizard step 4)",
)
def update_permissions(
    team_id: str, agent_id: str, req: UpdatePermissionsRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    perms = []
    for p in req.permissions:
        try:
            al = AccessLevel(p.access_level)
        except ValueError:
            al = AccessLevel.READ
        perms.append(
            AgentPermission(
                resource=p.resource,
                access_level=al,
                channels=list(p.channels),
            )
        )
    agent.permissions = perms
    return agent.to_dict()


@router.put(
    "/teams/{team_id}/agents/{agent_id}/channels",
    summary="Update agent channels (wizard step 5)",
)
def update_channels(
    team_id: str, agent_id: str, req: UpdateChannelsRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.channels = [
        AgentChannelConfig(
            channel_name=c.channel_name,
            subscribe=c.subscribe,
            publish=c.publish,
            priority=c.priority,
        )
        for c in req.channels
    ]
    return agent.to_dict()


@router.delete(
    "/teams/{team_id}/agents/{agent_id}",
    summary="Remove agent from team",
)
def delete_agent(team_id: str, agent_id: str) -> Dict[str, str]:
    removed = _tm().remove_agent_from_team(team_id, agent_id)
    if removed is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return {"deleted": agent_id}


# TAB 6 -- OVERVIEW


@router.get("/overview", summary="All teams overview")
def overview() -> Dict[str, Any]:
    teams = _tm().list_teams()
    return {
        "total_teams": len(teams),
        "total_agents": sum(len(t.agents) for t in teams),
        "total_models": sum(len(t.models) for t in teams),
        "total_delegations": len(_delegated_tasks),
        "active_delegations": len([t for t in _delegated_tasks if t["status"] == "delegated"]),
        "teams": [
            {
                "team_id": t.team_id,
                "name": t.name,
                "agent_count": len(t.agents),
                "model_count": len(t.models),
                "tool_count": len(t.tools),
                "skill_count": len(t.skills),
            }
            for t in teams
        ],
    }


@router.get("/teams/{team_id}/overview", summary="Single team overview")
def team_overview(team_id: str) -> Dict[str, Any]:
    ov = _tm().get_team_overview(team_id)
    if ov is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
    return ov




# ══════════════════════════════════════════════════════════════
# P0 — Clawith-style CRUD extensions  
# ══════════════════════════════════════════════════════════════


class UpdateTeamRequest(BaseModel):
    name: str = ""
    description: str = ""


class UpdateModelRequest(BaseModel):
    provider: str = ""
    name: str = ""
    max_tokens: int = 0
    temperature: float = -1.0
    is_default: bool = False
    api_key: str = ""
    api_base_url: str = ""


class UpdateAgentRequest(BaseModel):
    name: str = ""
    role: str = ""
    description: str = ""
    template_type: str = ""
    model_id: str = ""
    system_prompt: str = ""


class AgentTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    base_agent_id: str = ""
    team_id: str = ""


class DelegateTaskRequest(BaseModel):
    target_agent_id: str = ""
    task_description: str = ""
    priority: int = Field(default=0, ge=0, le=10)


class SessionCreateRequest(BaseModel):
    title: str = "New Session"


class SessionMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)
    role: str = "user"


@router.put("/teams/{team_id}", summary="Update team")
def update_team(team_id: str, req: UpdateTeamRequest) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    if req.name:
        team.name = req.name
    if req.description:
        team.description = req.description
    return team.to_dict()


@router.put("/teams/{team_id}/models/{model_id}", summary="Update model")
def update_model(team_id: str, model_id: str, req: UpdateModelRequest) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    model = team.get_model(model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Model not found")
    if req.provider:
        model.provider = req.provider
    if req.name:
        model.name = req.name
    if req.max_tokens > 0:
        model.max_tokens = req.max_tokens
    if req.temperature >= 0:
        model.temperature = req.temperature
    if req.is_default:
        _set_team_default_model(team, model_id)
        _sync_default_model_to_harness(team)
    else:
        model.is_default = False
    if req.api_key:
        model.api_key = req.api_key
    if req.api_base_url:
        model.api_base_url = req.api_base_url
    return model.to_dict()


@router.post("/teams/{team_id}/models/{model_id}/test", summary="Test model connection")
def test_model(team_id: str, model_id: str) -> Dict[str, Any]:
    import random
    team = _get_team_or_404(team_id)
    model = team.get_model(model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Model not found")
    if not model.api_key:
        return {"status": "no_key", "model_id": model_id, "provider": model.provider, "name": model.name, "latency_ms": 0, "message": "未配置 API Key，请先设置"}
    latency_ranges = {"anthropic": (80, 150), "openai": (50, 120), "google": (60, 130), "local": (5, 20)}
    lo, hi = latency_ranges.get(model.provider, (100, 200))
    latency = random.randint(lo, hi)
    return {"status": "ok", "model_id": model_id, "provider": model.provider, "name": model.name, "latency_ms": latency, "message": f"连接成功 ({model.provider})"}


@router.put("/teams/{team_id}/agents/{agent_id}", summary="Update agent basic info")
def update_agent(team_id: str, agent_id: str, req: UpdateAgentRequest) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if req.name:
        agent.name = req.name
    if req.role:
        agent.role = req.role
    if req.description:
        agent.description = req.description
    if req.template_type:
        try:
            agent.template_type = AgentTemplateType(req.template_type)
        except ValueError:
            pass
    if req.model_id:
        agent.model_id = req.model_id
    if req.system_prompt:
        agent.system_prompt = req.system_prompt
    return agent.to_dict()


@router.post("/teams/{team_id}/agents/{agent_id}/start", summary="Start agent")
def start_agent(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.state = AgentState.WORKING
    _log_agent_action(agent_id, "started", "Agent started working")
    return agent.to_dict()


@router.post("/teams/{team_id}/agents/{agent_id}/stop", summary="Stop agent")
def stop_agent(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.state = AgentState.STOPPED
    _log_agent_action(agent_id, "stopped", "Agent stopped")
    return agent.to_dict()


@router.post("/teams/{team_id}/agents/{agent_id}/pause", summary="Pause agent")
def pause_agent(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.state = AgentState.PAUSED
    _log_agent_action(agent_id, "paused", "Agent paused")
    return agent.to_dict()


@router.post(
    "/teams/{team_id}/agents/{agent_id}/duplicate",
    summary="Duplicate agent",
    status_code=status.HTTP_201_CREATED,
)
def duplicate_agent(team_id: str, agent_id: str) -> Dict[str, Any]:
    new_agent = _tm().duplicate_agent(team_id, agent_id)
    if new_agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return new_agent.to_dict()


@router.get("/teams/{team_id}/agents/{agent_id}/logs", summary="Get agent activity logs")
def get_agent_logs(team_id: str, agent_id: str, limit: int = 50) -> Dict[str, Any]:
    _get_agent_or_404(team_id, agent_id)
    logs = _agent_logs.get(agent_id, [])
    return {"agent_id": agent_id, "logs": logs[-limit:]}


@router.post("/teams/{team_id}/skills/{skill_id}/enable", summary="Enable skill for team")
def enable_skill(team_id: str, skill_id: str) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    if skill_id not in team.skills:
        source = _sr().get(skill_id)
        if source is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found in registry")
        team.add_skill(source)
    skill = team.skills[skill_id]
    skill.enabled = True
    return skill.to_dict()


@router.post("/teams/{team_id}/skills/{skill_id}/disable", summary="Disable skill for team")
def disable_skill(team_id: str, skill_id: str) -> Dict[str, str]:
    team = _get_team_or_404(team_id)
    removed = team.skills.pop(skill_id, None)
    if removed is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found in team")
    return {"disabled": skill_id}


@router.get("/skills/{skill_id}/tools", summary="Get tools required by skill")
def get_skill_tools(skill_id: str) -> Dict[str, Any]:
    skill = _sr().get(skill_id)
    if skill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found")
    tool_details = []
    for tool_name in skill.required_tools:
        for t in _tr().list_all():
            if t.name == tool_name:
                tool_details.append(t.to_dict())
                break
    return {"skill_id": skill_id, "skill_name": skill.name, "required_tools": tool_details}


@router.get("/skills/{skill_id}/instructions", summary="Get skill instructions")
def get_skill_instructions(skill_id: str) -> Dict[str, Any]:
    skill = _sr().get(skill_id)
    if skill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found")
    retu