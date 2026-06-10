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
import copy
from datetime import datetime, timezone

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query, status
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
    SkillCategory,
    SkillDefinition,
    ToolCategory,
    ToolDefinition,
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
from .budget import TokenBudget, get_budget_guard, get_usage_store
from .budget.guard import save_budget_settings
from .secret_store import (
    load_model_api_keys,
    resolve_api_key,
    save_default_llm_api_key,
    save_model_api_keys,
)
from .execution_registry import (
    ToolPermissionContext,
    PortRuntime,
    assemble_tool_pool,
    build_execution_registry,
)
from .security.permission_resolver import PermissionResolver
from .session_store import (
    list_sessions as list_stored_sessions,
    search_sessions,
)
from .skill_registry import SkillRegistry, get_default_skills
from .team_manager import TeamManager
from .tool_registry import ToolRegistry, get_default_tools

try:
    from config import DEFAULT_PAGE_SIZE as _DEFAULT_PAGE_SIZE
    from config import MAX_PAGE_SIZE as _MAX_PAGE_SIZE
except Exception:
    _DEFAULT_PAGE_SIZE = 50
    _MAX_PAGE_SIZE = 200


router = APIRouter(prefix="/api/v1/agent-config", tags=["agent-config"])


_team_manager: Optional[TeamManager] = None
_tool_registry: Optional[ToolRegistry] = None
_skill_registry: Optional[SkillRegistry] = None

# ── Model Pool Persistence ──
import os as _mp_os, json as _mp_json

_CONFIG_DIR = _mp_os.path.join(
    _mp_os.path.dirname(_mp_os.path.dirname(_mp_os.path.dirname(
        _mp_os.path.dirname(_mp_os.path.abspath(__file__))))),
    "config",
)
_MODEL_POOL_PATH = _mp_os.path.join(_CONFIG_DIR, "model_pool.json")


def _normalize_pagination(limit: int, offset: int) -> tuple[int, int, bool]:
    """Normalize optional limit/offset while preserving old unpaginated callers."""
    limit = getattr(limit, "default", limit)
    offset = getattr(offset, "default", offset)
    limit = int(limit or 0)
    offset = max(int(offset or 0), 0)
    if limit < 0:
        limit = 0
    if limit > _MAX_PAGE_SIZE:
        limit = _MAX_PAGE_SIZE
    if offset > 0 and limit <= 0:
        limit = _DEFAULT_PAGE_SIZE
    return limit, offset, bool(limit > 0 or offset > 0)


def _paginate_optional(items: List[Dict[str, Any]], *, limit: int, offset: int) -> Any:
    """Return either the legacy plain list or a paginated response envelope."""
    limit, offset, paginate = _normalize_pagination(limit, offset)
    if not paginate:
        return items
    total = len(items)
    return {
        "items": items[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


def _save_model_pool() -> None:
    """Persist model pool: config to model_pool.json, secrets to .api_keys.json."""
    if _team_manager is None:
        return
    data: Dict[str, Any] = {}
    secrets: Dict[str, Dict[str, str]] = {}
    for team in _team_manager.list_teams():
        team_models = {}
        team_secrets = {}
        for m in team.models.values():
            team_models[m.model_id] = {
                "model_id": m.model_id,
                "provider": m.provider,
                "name": m.name,
                "max_tokens": m.max_tokens,
                "temperature": m.temperature,
                "is_default": m.is_default,
                "enabled": m.enabled,
                "api_key": "",
                "api_base_url": m.api_base_url,
            }
            if m.api_key:
                team_secrets[m.model_id] = m.api_key
        data[team.team_id] = team_models
        if team_secrets:
            secrets[team.team_id] = team_secrets
    try:
        _mp_os.makedirs(_CONFIG_DIR, exist_ok=True)
        with open(_MODEL_POOL_PATH, "w", encoding="utf-8") as f:
            _mp_json.dump(data, f, ensure_ascii=False, indent=2)
        save_model_api_keys(secrets)
    except Exception:
        pass


def _load_model_pool(tm: TeamManager) -> None:
    """Load persisted model pool from config/model_pool.json + .api_keys.json."""
    if not _mp_os.path.isfile(_MODEL_POOL_PATH):
        return
    try:
        with open(_MODEL_POOL_PATH, "r", encoding="utf-8") as f:
            data = _mp_json.load(f)
    except Exception:
        return
    secrets = load_model_api_keys()
    for team in tm.list_teams():
        team_data = data.get(team.team_id)
        if not team_data:
            continue
        team_secrets = secrets.get(team.team_id, {})
        # Replace the entire model pool with persisted version
        team.models.clear()
        for mid, mdata in team_data.items():
            api_key = resolve_api_key(
                mdata.get("provider", "deepseek"),
                explicit=team_secrets.get(mid, ""),
                plaintext_fallback=mdata.get("api_key", ""),
            )
            model = ModelConfig(
                model_id=mdata.get("model_id", mid),
                provider=mdata.get("provider", "deepseek"),
                name=mdata.get("name", "deepseek-chat"),
                max_tokens=mdata.get("max_tokens", 8192),
                temperature=mdata.get("temperature", 0.7),
                is_default=mdata.get("is_default", False),
                enabled=mdata.get("enabled", True),
                api_key=api_key,
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
    # Initialize skill library chain (演化/验证/效果贯通)
    _init_skill_library_chain(team_manager, _skill_registry)


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
                api_key = resolve_api_key(m.provider, explicit=m.api_key)
                if m.is_default and api_key:
                    harness.update_default_provider(
                        provider=m.provider,
                        api_key=api_key,
                        api_base_url=m.api_base_url,
                        model=m.name,
                    )
                    cfg = harness.get_provider_config()
                    cfg.max_tokens = m.max_tokens
                    cfg.temperature = m.temperature
                    return
    except Exception:
        pass  # Non-critical, harness will use env/settings fallback


def _init_skill_library_chain(tm: TeamManager, sr: SkillRegistry) -> None:
    """Initialize skill library + evolver + verifier + tracker with proper dependencies."""
    import logging as _sl_log
    _sl_logger = _sl_log.getLogger(__name__)
    try:
        from .skill_library import init_skill_library
        from .skill_evolver import get_skill_evolver
        from .skill_verifier import get_skill_verifier
        from .skill_tracker import get_skill_tracker
        from .chat_harness import get_chat_harness

        lib = init_skill_library(team_manager=tm, skill_registry=sr)
        harness = get_chat_harness()

        evolver = get_skill_evolver()
        evolver._skill_library = lib
        evolver._chat_harness = harness

        verifier = get_skill_verifier()
        verifier._skill_library = lib
        verifier._chat_harness = harness

        tracker = get_skill_tracker()
        tracker._skill_library = lib

        _sl_logger.info("✅ Skill library chain initialized (library→evolver→verifier→tracker)")
    except Exception as e:
        _sl_logger.warning("⚠️ Skill library chain init failed: %s", e)


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


def _clone_skill_definition(skill: SkillDefinition) -> SkillDefinition:
    """Create a team-local copy so edits and usage stats do not mutate shared registry state."""
    cloned = copy.deepcopy(skill)
    if not cloned.slug:
        cloned.slug = cloned.name
    return cloned


def _resolve_skill_definition(team_id: str, skill_ref: str) -> Optional[SkillDefinition]:
    """Resolve a skill reference from team-local storage, skill library, or the default registry."""
    ref = (skill_ref or "").strip()
    if not ref:
        return None

    team = _tm().get_team(team_id)
    if team:
        if ref in team.skills:
            return team.skills[ref]
        for skill in team.skills.values():
            if ref in {skill.skill_id, skill.slug, skill.name}:
                return skill

    try:
        from .skill_library import get_skill_library

        lib = get_skill_library()
        skill = lib._find_skill(team_id, ref)
        if skill:
            return skill
        for item in lib.browse(team_id=team_id):
            if ref in {item.get("skill_id", ""), item.get("slug", ""), item.get("name", "")}:
                resolved = lib._find_skill(team_id, item.get("skill_id", "") or ref)
                if resolved:
                    return resolved
    except Exception:
        pass

    registry = _sr()
    skill = registry.get(ref) or registry.get_by_slug(ref)
    if skill:
        return skill
    for item in registry.list_all():
        if item.name == ref:
            return item
    return None


def _ensure_team_skill_copy(team_id: str, skill: SkillDefinition) -> SkillDefinition:
    """Materialize a bound skill into the team so agent bindings survive restarts."""
    team = _get_team_or_404(team_id)

    if skill.skill_id in team.skills:
        return team.skills[skill.skill_id]

    for existing in team.skills.values():
        if skill.name == existing.name:
            return existing
        if skill.slug and skill.slug == existing.slug:
            return existing

    cloned = _clone_skill_definition(skill)
    team.add_skill(cloned)
    return cloned


def _canonicalize_skill_bindings(team_id: str, skill_refs: List[str]) -> List[str]:
    """Resolve incoming skill refs and store them as team-local canonical skill IDs."""
    canonical: List[str] = []
    seen: set[str] = set()

    for skill_ref in skill_refs:
        skill = _resolve_skill_definition(team_id, skill_ref)
        if skill is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Skill not found: {skill_ref}")
        team_skill = _ensure_team_skill_copy(team_id, skill)
        if team_skill.skill_id not in seen:
            seen.add(team_skill.skill_id)
            canonical.append(team_skill.skill_id)

    return canonical


def _delete_skill_across_teams(skill_id: str) -> Dict[str, Any]:
    """Delete a skill from every team and unbind it from every agent that references it."""
    removed_identifiers: set[str] = {skill_id}
    removed_agent_count = 0
    removed_teams: List[str] = []

    resolved: Optional[SkillDefinition] = None
    for team in _tm().list_teams():
        resolved = _resolve_skill_definition(team.team_id, skill_id)
        if resolved is not None:
            removed_identifiers.update(
                identifier for identifier in (resolved.skill_id, resolved.slug, resolved.name) if identifier
            )
            break

    for team in _tm().list_teams():
        removed_any = False
        for existing_skill_id, existing_skill in list(team.skills.items()):
            identifiers = {existing_skill_id, existing_skill.skill_id, existing_skill.slug, existing_skill.name}
            if removed_identifiers.intersection(identifier for identifier in identifiers if identifier):
                team.skills.pop(existing_skill_id, None)
                removed_any = True
                removed_identifiers.update(
                    identifier for identifier in identifiers if identifier
                )
        if removed_any:
            removed_teams.append(team.team_id)

    for team in _tm().list_teams():
        for agent in team.agents.values():
            if not agent.skills:
                continue
            before = len(agent.skills)
            agent.skills = [
                skill_ref
                for skill_ref in agent.skills
                if skill_ref not in removed_identifiers
            ]
            removed_agent_count += before - len(agent.skills)

    if not removed_teams and removed_agent_count <= 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found")

    _tm()._persist()

    try:
        from .skill_library import get_skill_library

        lib = get_skill_library()
        if lib and lib._skill_store:
            lib._skill_store.delete(skill_id)
    except Exception:
        pass

    return {
        "status": "deleted",
        "skill_id": skill_id,
        "removed_from_teams": removed_teams,
        "removed_agent_bindings": removed_agent_count,
    }


def _resolve_bound_skills(team_id: str, agent: AgentProfile) -> List[SkillDefinition]:
    """Resolve an agent's bound skills into concrete definitions."""
    resolved: List[SkillDefinition] = []
    seen: set[str] = set()
    for skill_ref in agent.skills or []:
        skill = _resolve_skill_definition(team_id, skill_ref)
        if skill is None or not skill.enabled:
            continue
        if skill.skill_id in seen:
            continue
        seen.add(skill.skill_id)
        resolved.append(skill)
    return resolved


def _resolve_tool_definition(team_id: str, tool_ref: str) -> Optional[ToolDefinition]:
    """Resolve a tool reference from team-local tools first, then the global registry."""
    ref = (tool_ref or "").strip()
    if not ref:
        return None

    team = _tm().get_team(team_id)
    if team:
        if ref in team.tools:
            return team.tools[ref]
        for tool in team.tools.values():
            if ref in {tool.tool_id, tool.name}:
                return tool

    registry = _tr()
    tool = registry.get(ref)
    if tool:
        return tool
    for item in registry.list_all():
        if item.name == ref:
            return item
    return None


def _resolve_effective_tools(team_id: str, agent: AgentProfile, skills: List[SkillDefinition]) -> List[ToolDefinition]:
    """Merge explicit agent tools with tools implied by bound skills."""
    effective: List[ToolDefinition] = []
    seen: set[str] = set()
    tool_refs: List[str] = list(agent.tools or [])
    for skill in skills:
        tool_refs.extend(skill.required_tools or [])

    for tool_ref in tool_refs:
        tool = _resolve_tool_definition(team_id, tool_ref)
        if tool is None or not tool.enabled or tool.tool_id in seen:
            continue
        seen.add(tool.tool_id)
        effective.append(tool)

    return effective


def _build_agent_permission_context(agent: AgentProfile) -> ToolPermissionContext:
    return PermissionResolver().build_context(agent)


def _find_agent_across_teams(agent_id: str) -> tuple[str, AgentProfile] | tuple[None, None]:
    target = (agent_id or "").strip()
    if not target:
        return None, None
    for team in _tm().list_teams():
        agent = team.get_agent(target)
        if agent is not None:
            return team.team_id, agent
    return None, None


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
    allowed_tools: List[str] = Field(default_factory=list)


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
def list_teams(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    items = [
        {
            "team_id": t.team_id,
            "name": t.name,
            "description": t.description,
            "agent_count": len(t.agents),
            "model_count": len(t.models),
        }
        for t in _tm().list_teams()
    ]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/teams-tree", summary="All teams with agents tree")
def teams_tree(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
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
                    "skills": getattr(a, "skills", []) or [],
                    "tools": getattr(a, "tools", []) or [],
                }
                for a in agents_list
            ],
        })
    return _paginate_optional(result, limit=limit, offset=offset)


@router.get("/teams/{team_id}", summary="Get team detail")
def get_team(team_id: str) -> Dict[str, Any]:
    team = _tm().get_team(team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
    return {
        **team.to_dict(),
        "tasks": _summarize_team_tasks(team_id),
    }


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
def list_models(
    team_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    team = _get_team_or_404(team_id)
    items = [m.to_dict() for m in team.models.values()]
    return _paginate_optional(items, limit=limit, offset=offset)


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
    api_key = resolve_api_key(default_model.provider, explicit=default_model.api_key)
    harness.update_default_provider(
        provider=default_model.provider,
        api_key=api_key,
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
def list_all_tools(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    items = [t.to_dict() for t in _tr().list_all()]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/teams/{team_id}/tools", summary="List team tools")
def list_team_tools(
    team_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    team = _get_team_or_404(team_id)
    items = [t.to_dict() for t in team.tools.values()]
    return _paginate_optional(items, limit=limit, offset=offset)


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


@router.put(
    "/teams/{team_id}/tools/{tool_id}",
    summary="Edit tool properties",
)
def edit_tool(team_id: str, tool_id: str, req: Optional[EditToolRequest] = Body(None)) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    tool = team.tools.get(tool_id)
    if tool is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found in team")
    req = req or EditToolRequest()
    # Update allowed fields
    for field in ("name", "description", "icon", "requires_approval"):
        val = getattr(req, field, None)
        if val is not None:
            setattr(tool, field, val)
    if req.category is not None:
        try:
            tool.category = ToolCategory(req.category)
        except ValueError:
            pass
    if req.parameters is not None and isinstance(req.parameters, dict):
        tool.parameters = req.parameters
    _tm()._persist()
    return tool.to_dict()


@router.delete(
    "/teams/{team_id}/tools/{tool_id}",
    summary="Delete tool from team",
)
def delete_tool(team_id: str, tool_id: str) -> Dict[str, str]:
    team = _get_team_or_404(team_id)
    if tool_id not in team.tools:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found in team")
    del team.tools[tool_id]
    # Remove from all agents in this team
    for agent in team.agents:
        if tool_id in agent.tools:
            agent.tools.remove(tool_id)
    _tm()._persist()
    return {"status": "deleted", "tool_id": tool_id}


# TAB 4 -- SKILLS


@router.get("/skills", summary="List all available skills")
def list_all_skills(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    items = [s.to_dict() for s in _sr().list_all()]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/skills/required", summary="List required skills")
def list_required_skills(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    items = [s.to_dict() for s in _sr().list_required()]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/teams/{team_id}/skills", summary="List team skills")
def list_team_skills(
    team_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    team = _get_team_or_404(team_id)
    effective_skills: Dict[str, Dict[str, Any]] = {}

    for skill in team.skills.values():
        payload = skill.to_dict()
        payload["bound_agent_count"] = 0
        effective_skills[skill.skill_id] = payload

    for agent in team.agents.values():
        for skill_ref in agent.skills or []:
            skill = _resolve_skill_definition(team_id, skill_ref)
            if skill is None:
                continue
            if skill.skill_id not in effective_skills:
                payload = skill.to_dict()
                payload["bound_agent_count"] = 0
                effective_skills[skill.skill_id] = payload
            effective_skills[skill.skill_id]["bound_agent_count"] += 1

    items = sorted(effective_skills.values(), key=lambda item: ((item.get("category") or "").lower(), (item.get("name") or "").lower()))
    return _paginate_optional(items, limit=limit, offset=offset)


# TAB 5 -- AGENTS (5-step wizard)


@router.get("/agents", summary="List all agents")
def list_all_agents(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    agents: List[Dict[str, Any]] = []
    for team in _tm().list_teams():
        team_agents = team.agents.values() if isinstance(team.agents, dict) else team.agents
        for agent in team_agents:
            agents.append({
                **agent.to_dict(),
                "team_id": team.team_id,
                "team_name": team.name,
            })
    return _paginate_optional(agents, limit=limit, offset=offset)


def _get_agent_or_404(team_id: str, agent_id: str) -> AgentProfile:
    agent = _tm().get_agent(team_id, agent_id)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.get("/teams/{team_id}/agents", summary="List agents in team")
def list_agents(
    team_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    _get_team_or_404(team_id)
    items = [a.to_dict() for a in _tm().list_agents(team_id)]
    return _paginate_optional(items, limit=limit, offset=offset)


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
    _tm()._persist()
    return agent.to_dict()


@router.put(
    "/teams/{team_id}/agents/{agent_id}/skills",
    summary="Update agent skills (wizard step 3)",
)
def update_agent_skills(
    team_id: str, agent_id: str, req: UpdateSkillsRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.skills = _canonicalize_skill_bindings(team_id, req.skill_ids)
    _tm()._persist()
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
                allowed_tools=list(p.allowed_tools),
            )
        )
    agent.permissions = perms
    _tm()._persist()
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


class SkillExtractStartRequest(BaseModel):
    source_text: str = Field(..., min_length=10)
    source_title: str = ""
    source_type: str = "chat"


class SkillExtractEditRequest(BaseModel):
    field_updates: Dict[str, Any] = Field(default_factory=dict)


class SkillExtractApproveRequest(BaseModel):
    reviewer: str = ""
    edited_fields: Optional[Dict[str, Any]] = None
    skill_type: str = "reserve"
    target_agent_id: str = ""


class SkillExtractRejectRequest(BaseModel):
    reviewer: str = ""
    reason: str = ""


class ToolExecuteRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict)
    agent_id: str = ""
    team_id: str = ""


class ToolConfigRequest(BaseModel):
    config: Dict[str, Any] = Field(default_factory=dict)


class EditToolRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    requires_approval: Optional[bool] = None
    category: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class EditSkillRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    instructions: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    required_tools: Optional[List[str]] = None


class DigitalTwinStateRequest(BaseModel):
    rooms: Optional[List[Any]] = None
    positions: Optional[Dict[str, str]] = None


class DigitalTwinMoveRequest(BaseModel):
    agent_id: str
    room_id: str


class DigitalTwinInteractRequest(BaseModel):
    from_: str = Field(default="", alias="from")
    to: str = ""
    type: str = "handoff"
    content: str = ""


class SkillLibraryActionRequest(BaseModel):
    team_id: str = Field(..., min_length=1)
    skill_id: str = Field(..., min_length=1)
    user_feedback: str = ""
    new_instructions: str = ""
    target_team_id: str = ""


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
        source = _resolve_skill_definition(team_id, skill_id)
        if source is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found in registry")
        skill = _ensure_team_skill_copy(team_id, source)
    else:
        skill = team.skills[skill_id]
    skill.enabled = True
    _tm()._persist()
    return skill.to_dict()


@router.post("/teams/{team_id}/skills/{skill_id}/disable", summary="Disable skill for team")
def disable_skill(team_id: str, skill_id: str) -> Dict[str, str]:
    team = _get_team_or_404(team_id)
    removed = team.skills.pop(skill_id, None)
    if removed is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found in team")
    for agent in team.agents.values():
        if skill_id in agent.skills:
            agent.skills.remove(skill_id)
    _tm()._persist()
    return {"disabled": skill_id}


@router.put(
    "/teams/{team_id}/skills/{skill_id}",
    summary="Edit skill properties",
)
def edit_skill(team_id: str, skill_id: str, req: Optional[EditSkillRequest] = Body(None)) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    skill = team.skills.get(skill_id)
    if skill is None:
        # Also check skill store
        from .skill_library import get_skill_library
        lib = get_skill_library()
        if lib:
            skill = lib._find_skill(team_id, skill_id)
        if skill is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found")
        # Add to team for editing
        team.skills[skill_id] = skill
    req = req or EditSkillRequest()
    # Update allowed fields
    for field in ("name", "description", "icon", "instructions", "slug"):
        val = getattr(req, field, None)
        if val is not None:
            setattr(skill, field, val)
    if req.category is not None:
        try:
            skill.category = SkillCategory(req.category)
        except ValueError:
            pass
    if req.required_tools is not None and isinstance(req.required_tools, list):
        skill.required_tools = req.required_tools
    # Bump version on instruction edit
    if req.instructions is not None:
        skill.version = getattr(skill, "version", 0) + 1
    _tm()._persist()
    # Also update skill store if available
    try:
        from .skill_library import get_skill_library
        lib = get_skill_library()
        if lib:
            lib._persist_skill(skill, team_id)
    except Exception:
        pass
    return skill.to_dict()


@router.delete(
    "/teams/{team_id}/skills/{skill_id}",
    summary="Delete skill from team",
)
def delete_skill(team_id: str, skill_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    return _delete_skill_across_teams(skill_id)


# ── Digital Twin Routes ──────────────────────────────────────────────────

_dt_state: Dict[str, Any] = {
    "rooms": [],
    "positions": {},
    "interactions": [],
}


@router.get("/digital-twin/state", summary="Get digital twin state")
def dt_get_state() -> Dict[str, Any]:
    return _dt_state


@router.put("/digital-twin/state", summary="Update digital twin state")
def dt_put_state(req: Optional[DigitalTwinStateRequest] = Body(None)) -> Dict[str, Any]:
    req = req or DigitalTwinStateRequest()
    if req.rooms is not None:
        _dt_state["rooms"] = req.rooms
    if req.positions is not None:
        _dt_state["positions"] = req.positions
    return _dt_state


@router.post("/digital-twin/move", summary="Move agent to room")
def dt_move_agent(req: DigitalTwinMoveRequest = Body(...)) -> Dict[str, Any]:
    if not req.agent_id or not req.room_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="agent_id and room_id required")
    _dt_state["positions"][req.agent_id] = req.room_id
    return {"status": "moved", "agent_id": req.agent_id, "room_id": req.room_id}


@router.post("/digital-twin/interact", summary="Record agent interaction")
def dt_interact(req: Optional[DigitalTwinInteractRequest] = Body(None)) -> Dict[str, Any]:
    req = req or DigitalTwinInteractRequest()
    from_agent = req.from_
    to_agent = req.to
    msg_type = req.type
    content = req.content
    ts = datetime.now(timezone.utc).isoformat()
    interaction = {"from": from_agent, "to": to_agent, "type": msg_type, "content": content, "time": ts}
    _dt_state["interactions"].append(interaction)
    # Keep last 200
    if len(_dt_state["interactions"]) > 200:
        _dt_state["interactions"] = _dt_state["interactions"][-100:]
    return interaction


@router.get("/digital-twin/interactions", summary="Get recent interactions")
def dt_get_interactions(limit: int = 50) -> List[Dict[str, Any]]:
    return _dt_state["interactions"][-limit:]


# ── Skill Extraction Routes ──────────────────────────────────────────────

@router.get("/teams/{team_id}/skill-extract/queue", summary="List skill extraction queue")
def skill_extract_queue(team_id: str, status_filter: str = "") -> List[Dict[str, Any]]:
    from .skill_extractor import get_skill_extractor_engine
    engine = get_skill_extractor_engine()
    return engine.get_queue(team_id, status_filter=status_filter)


@router.post("/teams/{team_id}/skill-extract/start", summary="Start skill extraction")
async def skill_extract_start(team_id: str, req: SkillExtractStartRequest) -> Dict[str, Any]:
    from .skill_extractor import get_skill_extractor_engine
    engine = get_skill_extractor_engine()
    source_text = req.source_text
    source_title = req.source_title
    source_type = req.source_type
    item = await engine.start_extraction(
        team_id=team_id,
        source_text=source_text,
        source_title=source_title,
        source_type=source_type,
    )
    return item.to_dict()


@router.get("/teams/{team_id}/skill-extract/stream", summary="SSE stream for extraction updates")
async def skill_extract_stream(team_id: str):
    from .skill_extractor import get_skill_extractor_engine
    from starlette.responses import StreamingResponse
    engine = get_skill_extractor_engine()
    q = engine.subscribe(team_id)

    async def event_gen():
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            engine.unsubscribe(team_id, q)

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@router.get("/teams/{team_id}/skill-extract/{item_id}", summary="Get extraction item detail")
def skill_extract_detail(team_id: str, item_id: str) -> Dict[str, Any]:
    from .skill_extractor import get_skill_extractor_engine
    engine = get_skill_extractor_engine()
    item = engine.get_item(team_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("/teams/{team_id}/skill-extract/{item_id}/edit", summary="Edit extraction draft")
async def skill_extract_edit(team_id: str, item_id: str, req: SkillExtractEditRequest) -> Dict[str, Any]:
    from .skill_extractor import get_skill_extractor_engine
    engine = get_skill_extractor_engine()
    field_updates = req.field_updates
    result = await engine.edit_item(team_id, item_id, field_updates)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return result


@router.post("/teams/{team_id}/skill-extract/{item_id}/approve", summary="Approve extraction item")
async def skill_extract_approve(team_id: str, item_id: str, req: SkillExtractApproveRequest) -> Dict[str, Any]:
    from .skill_extractor import get_skill_extractor_engine
    engine = get_skill_extractor_engine()
    reviewer = req.reviewer
    edited_fields = req.edited_fields
    skill_type = req.skill_type
    target_agent_id = req.target_agent_id
    result = await engine.approve_item(
        team_id, item_id, reviewer=reviewer, edited_fields=edited_fields,
        skill_type=skill_type, target_agent_id=target_agent_id,
    )
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return result


@router.post("/teams/{team_id}/skill-extract/{item_id}/reject", summary="Reject extraction item")
async def skill_extract_reject(team_id: str, item_id: str, req: SkillExtractRejectRequest) -> Dict[str, Any]:
    from .skill_extractor import get_skill_extractor_engine
    engine = get_skill_extractor_engine()
    reviewer = req.reviewer
    reason = req.reason
    result = await engine.reject_item(team_id, item_id, reviewer=reviewer, reason=reason)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return result


@router.delete("/teams/{team_id}/skill-extract/{item_id}", summary="Delete extraction item")
async def skill_extract_delete(team_id: str, item_id: str) -> Dict[str, Any]:
    from .skill_extractor import get_skill_extractor_engine
    engine = get_skill_extractor_engine()
    deleted = await engine.delete_item(team_id, item_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return {"ok": True, "item_id": item_id}


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
    return {
        "skill_id": skill_id,
        "name": skill.name,
        "instructions": skill.instructions,
        "required_tools": skill.required_tools,
    }


@router.post("/tools/{tool_id}/execute", summary="Execute a tool directly")
async def execute_tool(tool_id: str, req: ToolExecuteRequest) -> Dict[str, Any]:
    """Execute a tool with given arguments. Returns the execution result."""
    from .tool_executor import get_tool_executor
    tool = _tr().get(tool_id)
    if tool is None:
        # Try by name
        for t in _tr().list_all():
            if t.name == tool_id:
                tool = t
                break
    if tool is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found")
    executor = get_tool_executor()
    arguments = req.arguments
    permission_context = None
    agent_id = req.agent_id
    team_id = req.team_id
    if agent_id:
        if team_id:
            agent = _tm().get_agent(team_id, agent_id)
        else:
            team_id, agent = _find_agent_across_teams(agent_id)
        if agent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agent not found")
        permission_context = _build_agent_permission_context(agent)
    result = await executor.execute(
        tool.name, arguments,
        requires_approval=tool.requires_approval,
        agent_id=agent_id,
        permission_context=permission_context,
    )
    return result.to_dict()


@router.get("/tools/execution-history", summary="Get tool execution history")
def get_tool_execution_history(
    limit: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    from .tool_executor import get_tool_executor
    items = get_tool_executor().get_history(limit + offset)
    return _paginate_optional(items, limit=limit, offset=offset)


@router.put(
    "/tools/{tool_id}/config",
    summary="Save tool configuration",
)
def save_tool_config(tool_id: str, req: ToolConfigRequest) -> Dict[str, Any]:
    """Save configuration for a tool."""
    tool = _tr().get(tool_id)
    if tool is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found")
    config = req.config
    tool.config = config
    return {"tool_id": tool_id, "config": tool.config}


@router.get("/search", summary="Search across all entities")
def search_entities(q: str = "") -> Dict[str, Any]:
    if not q:
        return {"teams": [], "agents": [], "tools": [], "skills": []}
    ql = q.lower()
    matched_teams = [
        {"team_id": t.team_id, "name": t.name, "description": t.description}
        for t in _tm().list_teams()
        if ql in t.name.lower() or ql in t.description.lower()
    ]
    matched_agents = []
    for t in _tm().list_teams():
        for a in t.agents.values():
            if ql in a.name.lower() or ql in a.role.lower() or ql in a.description.lower():
                matched_agents.append({
                    "team_id": t.team_id, "team_name": t.name,
                    "agent_id": a.agent_id, "name": a.name, "role": a.role, "state": a.state.value,
                })
    matched_tools = [t.to_dict() for t in _tr().list_all() if ql in t.name.lower() or ql in t.description.lower()]
    matched_skills = [s.to_dict() for s in _sr().list_all() if ql in s.name.lower() or ql in s.description.lower()]
    return {"teams": matched_teams, "agents": matched_agents, "tools": matched_tools, "skills": matched_skills}


# ══════════════════════════════════════════════════════════════
# P1 — Agent collaboration, templates, sessions
# ══════════════════════════════════════════════════════════════


_templates: List[Dict[str, Any]] = []
_sessions: Dict[str, Dict[str, Any]] = {}
_delegated_tasks: List[Dict[str, Any]] = []


@router.get("/templates", summary="List agent templates")
def list_templates(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _paginate_optional(_templates, limit=limit, offset=offset)


@router.post("/templates", summary="Create agent template", status_code=status.HTTP_201_CREATED)
def create_template(req: AgentTemplateRequest) -> Dict[str, Any]:
    import uuid
    tpl = {
        "template_id": str(uuid.uuid4())[:8],
        "name": req.name,
        "description": req.description,
        "base_agent_id": req.base_agent_id,
        "team_id": req.team_id,
    }
    _templates.append(tpl)
    return tpl


@router.delete("/templates/{template_id}", summary="Delete template")
def delete_template(template_id: str) -> Dict[str, str]:
    global _templates
    before = len(_templates)
    _templates = [t for t in _templates if t.get("template_id") != template_id]
    if len(_templates) == before:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")
    return {"deleted": template_id}


@router.post("/teams/{team_id}/agents/{agent_id}/delegate", summary="Delegate task to another agent")
def delegate_task(team_id: str, agent_id: str, req: DelegateTaskRequest) -> Dict[str, Any]:
    import uuid
    _get_agent_or_404(team_id, agent_id)
    target = _tm().get_agent(team_id, req.target_agent_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Target agent not found")
    result = {
        "task_id": str(uuid.uuid4())[:8],
        "from_agent": agent_id,
        "to_agent": req.target_agent_id,
        "team_id": team_id,
        "description": req.task_description,
        "priority": req.priority,
        "status": "delegated",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _delegated_tasks.append(result)
    _log_agent_action(agent_id, "delegated_task",
                      f"to={req.target_agent_id} task={result['task_id']}")
    _log_agent_action(req.target_agent_id, "received_delegation",
                      f"from={agent_id} task={result['task_id']}")
    return result


@router.get("/teams/{team_id}/agents/{agent_id}/relationships", summary="Get agent relationships")
def get_agent_relationships(team_id: str, agent_id: str) -> Dict[str, Any]:
    _get_agent_or_404(team_id, agent_id)
    team = _get_team_or_404(team_id)
    relationships = [
        {
            "agent_id": a.agent_id,
            "target": a.agent_id,
            "name": a.name,
            "role": a.role,
            "type": "peer",
            "relationship": "peer",
        }
        for a in team.agents.values() if a.agent_id != agent_id
    ]
    return {"agent_id": agent_id, "relationships": relationships}


@router.get("/teams/{team_id}/agents/{agent_id}/sessions", summary="List agent sessions")
def list_agent_sessions(
    team_id: str,
    agent_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    _get_agent_or_404(team_id, agent_id)
    items = [s for s in _sessions.values() if s.get("agent_id") == agent_id]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.post(
    "/teams/{team_id}/agents/{agent_id}/sessions",
    summary="Create session",
    status_code=status.HTTP_201_CREATED,
)
def create_session(team_id: str, agent_id: str, req: SessionCreateRequest) -> Dict[str, Any]:
    import uuid
    _get_agent_or_404(team_id, agent_id)
    sid = str(uuid.uuid4())[:8]
    session = {
        "session_id": sid,
        "agent_id": agent_id,
        "team_id": team_id,
        "title": req.title,
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _sessions[sid] = session
    _bump_metric(agent_id, "sessions_created")
    _log_agent_action(agent_id, "session_created", f"session={sid}")
    return session


@router.get(
    "/teams/{team_id}/agents/{agent_id}/sessions/{session_id}/messages",
    summary="Get session messages",
)
def get_session_messages(team_id: str, agent_id: str, session_id: str) -> Dict[str, Any]:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"session_id": session_id, "messages": session.get("messages", [])}


async def _generate_agent_response(agent, content, session_id="", team_id=""):
    """Generate agent response via the unified ChatHarness.

    Routes through the real LLM when configured, falls back to
    domain-aware offline responses when LLM is unavailable.
    Uses the team's default model if available.
    Injects bound tool schemas as function calling definitions.
    Injects bound skill instructions into system prompt.
    """
    harness = get_chat_harness()

    # If team has a default model, ensure harness uses it
    if team_id:
        team = _tm().get_team(team_id)
        if team:
            _sync_default_model_to_harness(team)

    resolved_skills = _resolve_bound_skills(team_id, agent) if team_id else []
    permission_context = _build_agent_permission_context(agent)

    # Build tool schemas for function calling from agent's bound tools + bound skill requirements
    tools_for_llm = None
    effective_tools = _resolve_effective_tools(team_id, agent, resolved_skills) if team_id else []
    if effective_tools:
        tools_for_llm = []
        for t in effective_tools:
            if permission_context.blocks(t.name):
                continue
            props = {}
            required_params = []
            for pname, pdef in (t.parameters or {}).items():
                ptype = pdef.get("type", "string")
                if ptype == "integer":
                    ptype = "number"
                if ptype == "object":
                    ptype = "string"
                if ptype == "array":
                    ptype = "string"
                props[pname] = {
                    "type": ptype,
                    "description": pdef.get("description", ""),
                }
                if pdef.get("required"):
                    required_params.append(pname)
            fn_schema = {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": required_params,
                    },
                },
            }
            tools_for_llm.append(fn_schema)

    # Build system prompt from agent metadata + skill instructions
    skill_labels = [skill.name for skill in resolved_skills] if resolved_skills else list(agent.skills or [])
    skills_str = ", ".join(skill_labels) if skill_labels else "通用"
    system_prompt = (
        f"你是 {agent.name}，角色: {agent.role}。\n"
        f"技能: {skills_str}\n"
        f"你是 AgentsGroup2026 智能体团队管理平台的核心智能体之一。\n"
        f"请用中文回答，专业但易懂。"
    )

    # Inject bound skill instructions into system prompt
    if resolved_skills:
        skill_instructions = []
        for skill in resolved_skills:
            if skill.instructions:
                skill_instructions.append(f"### {skill.name}\n{skill.instructions}")
        if skill_instructions:
            system_prompt += "\n\n## 已启用技能指令\n\n" + "\n\n".join(skill_instructions)

    result = await harness.chat(
        content,
        agent_id=agent.agent_id,
        team_id=team_id,
        session_id=session_id,
        system_prompt=system_prompt,
        tools=tools_for_llm,
    )

    # If LLM returned tool calls, execute them and feed results back
    if result.tool_invocations:
        from .tool_executor import get_tool_executor
        executor = get_tool_executor()
        tool_outputs = []
        for inv in result.tool_invocations:
            tr = await executor.execute(
                inv.tool_name,
                inv.arguments,
                agent_id=agent.agent_id,
                permission_context=permission_context,
            )
            inv.result = tr.output if tr.success else f"Error: {tr.error}"
            tool_outputs.append(f"[{inv.tool_name}] {'✅' if tr.success else '❌'}: {inv.result[:500]}")
        # Append tool results and get a follow-up response
        tool_summary = "\n\n".join(tool_outputs)
        followup = await harness.chat(
            f"工具执行结果:\n\n{tool_summary}\n\n请基于以上工具返回结果，回答用户的问题。",
            agent_id=agent.agent_id,
            team_id=team_id,
            session_id=session_id,
            system_prompt=system_prompt,
        )
        return followup.response, followup

    return result.response, result


@router.post(
    "/teams/{team_id}/agents/{agent_id}/sessions/{session_id}/messages",
    summary="Send message to session",
    status_code=status.HTTP_201_CREATED,
)
async def send_session_message(
    team_id: str, agent_id: str, session_id: str, req: SessionMessageRequest
) -> Dict[str, Any]:
    import uuid
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    msg = {
        "message_id": str(uuid.uuid4())[:8],
        "role": req.role,
        "content": req.content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    session["messages"].append(msg)
    agent = _get_agent_or_404(team_id, agent_id)
    _bump_metric(agent_id, "messages_sent")
    _log_agent_action(agent_id, "message_received", f"session={session_id}")
    reply_text, turn_result = await _generate_agent_response(agent, req.content, session_id, team_id)
    if reply_text:
        reply_msg = {
            "message_id": str(uuid.uuid4())[:8],
            "role": "assistant",
            "content": reply_text,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": turn_result.model if turn_result else "",
            "provider": turn_result.provider if turn_result else "",
            "latency_ms": turn_result.latency_ms if turn_result else 0,
        }
        session["messages"].append(reply_msg)
        # Track real token usage from harness
        real_usage = turn_result.usage if turn_result else None
        if real_usage and real_usage.total_tokens > 0:
            _bump_metric(agent_id, "today_llm_calls")
            _bump_metric(agent_id, "today_tokens", real_usage.total_tokens)
            _bump_metric(agent_id, "month_tokens", real_usage.total_tokens)
            _bump_metric(agent_id, "total_tokens", real_usage.total_tokens)
        else:
            _bump_metric(agent_id, "today_llm_calls")
            estimated_tokens = len(req.content) + len(reply_text)
            _bump_metric(agent_id, "today_tokens", estimated_tokens)
            _bump_metric(agent_id, "month_tokens", estimated_tokens)
            _bump_metric(agent_id, "total_tokens", estimated_tokens)
        # Check for tool invocations from harness or text
        if turn_result and turn_result.tool_invocations:
            _bump_metric(agent_id, "tools_invoked", len(turn_result.tool_invocations))
            _log_agent_action(agent_id, "tools_invoked",
                              ", ".join(t.tool_name for t in turn_result.tool_invocations))
        else:
            tool_invocations = _parse_tool_invocations(reply_text)
            if tool_invocations:
                _bump_metric(agent_id, "tools_invoked", len(tool_invocations))
                _log_agent_action(agent_id, "tools_invoked",
                                  ", ".join(t["tool"] for t in tool_invocations))

    return msg


@router.get("/teams/{team_id}/delegations", summary="List delegations for a team")
def list_team_delegations(
    team_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    _get_team_or_404(team_id)
    items = [t for t in _delegated_tasks if t.get("team_id") == team_id]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/delegations", summary="List all delegated tasks")
def list_delegations(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _paginate_optional(_delegated_tasks, limit=limit, offset=offset)


@router.get("/delegations/stats", summary="Delegation statistics")
def delegation_stats() -> Dict[str, Any]:
    from collections import Counter
    status_counts = Counter(t["status"] for t in _delegated_tasks)
    priority_counts = Counter(t["priority"] for t in _delegated_tasks)
    return {
        "total": len(_delegated_tasks),
        "by_status": dict(status_counts),
        "by_priority": {str(k): v for k, v in sorted(priority_counts.items())},
        "recent": _delegated_tasks[-5:] if _delegated_tasks else [],
    }


# Bridge Command Integration
# Route bridge commands to agent-config agents


class BridgeCommandRequest(BaseModel):
    command: str = Field(..., min_length=1)
    ship_context: Dict[str, Any] = Field(default_factory=dict)


_SKILL_KEYWORDS: Dict[str, List[str]] = {
    "dt_camera_control": ["视图", "view", "camera", "相机", "俯视", "正视", "侧视", "后视", "top", "front", "side", "back", "iso", "isometric", "3d"],
    "navigation_assessment": ["航线", "route", "导航", "navigate", "航向", "heading", "waypoint"],
    "colregs_compliance": ["避碰", "collision", "colreg", "规则", "会遇", "交叉", "碰撞风险"],
    "engine_diagnostics": ["发动机", "engine", "机舱", "引擎", "功率", "rpm", "转速", "主机", "排温"],
    "weather_analysis": ["天气", "weather", "气象", "风速", "海况", "浪高", "台风"],
    "cargo_management": ["货物", "cargo", "装载", "稳性", "库存"],
    "dt_model_layout": ["模型", "model", "布局", "layout"],
    "dt_material_change": ["材质", "material", "颜色", "纹理"],
    "dt_lighting_control": ["灯光", "light", "照明", "阴影"],
    "route_optimization": ["优化航线", "route optimization", "航线优化", "最优航线"],
    "dt_physics_simulation": ["物理", "physics", "仿真", "simulation"],
    "dt_interaction_actions": ["巡检", "inspection", "检查路径"],
}


def _classify_bridge_intent(command: str) -> str:
    """Classify a bridge command to the best matching skill name."""
    cmd_lower = command.lower()
    best_skill = "general_assist"
    best_count = 0
    for skill_name, keywords in _SKILL_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in cmd_lower)
        if count > best_count:
            best_count = count
            best_skill = skill_name
    return best_skill


def _find_agent_for_skill(skill_name: str):
    """Find the first agent across all teams that has the given skill."""
    if _team_manager is None:
        return None, None
    for team in _team_manager.list_teams():
        for agent in team.agents.values():
            if agent.skills and skill_name in [s.lower() for s in agent.skills]:
                return team, agent
    skill_root = skill_name.split("_")[0]
    for team in _team_manager.list_teams():
        for agent in team.agents.values():
            if agent.skills and any(skill_root in s.lower() for s in agent.skills):
                return team, agent
    return None, None


def _parse_tool_invocations(response_text: str) -> List[Dict[str, Any]]:
    """Extract tool invocations from response text."""
    import json as _json
    import re
    invocations = []
    tool_match = re.search(r"执行工具[：:]\s*(\S+)", response_text)
    params_match = re.search(r"参数[：:]\s*(\{.*\})", response_text, re.DOTALL)
    if tool_match:
        tool_name = tool_match.group(1)
        params = {}
        if params_match:
            try:
                params = _json.loads(params_match.group(1))
            except (ValueError, _json.JSONDecodeError):
                pass
        invocations.append({"tool": tool_name, "params": params})
    return invocations


@router.post("/bridge/command", summary="Route bridge command to best agent")
async def bridge_command(req: BridgeCommandRequest) -> Dict[str, Any]:
    """Classify a bridge command, find the best agent, return structured response."""
    intent = _classify_bridge_intent(req.command)
    team, agent = _find_agent_for_skill(intent)

    if agent is not None:
        bridge_team_id = team.team_id if team else ""
        response_text, turn_result = await _generate_agent_response(agent, req.command, team_id=bridge_team_id)
        tool_invocations = (
            [t.to_dict() for t in turn_result.tool_invocations]
            if turn_result and turn_result.tool_invocations
            else _parse_tool_invocations(response_text)
        )
        return {
            "handled": True,
            "intent": intent,
            "agent": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "team_id": team.team_id,
                "team_name": team.name,
            },
            "response": response_text,
            "tool_invocations": tool_invocations,
            "model": turn_result.model if turn_result else "",
            "provider": turn_result.provider if turn_result else "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "handled": False,
        "intent": intent,
        "agent": None,
        "response": f"No agent available for intent: {intent}",
        "tool_invocations": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }



# ══════════════════════════════════════════════════════════════
# P2 — Concurrent Task Execution Engine
# ══════════════════════════════════════════════════════════════

from .task_engine import AgentTask, TaskStatus, get_task_engine


class SubmitTaskRequest(BaseModel):
    agent_id: str = ""
    title: str = Field(..., min_length=1, max_length=256)
    description: str = ""
    priority: int = Field(default=2, ge=0, le=3)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubmitBatchRequest(BaseModel):
    tasks: List[SubmitTaskRequest] = Field(..., min_length=1)


def _te():
    """Return the TaskEngine singleton, registering the real executor on first call."""
    engine = get_task_engine()
    if engine._executor is None:
        engine.set_executor(_real_task_executor)
    return engine


async def _check_task_runtime_ready() -> tuple[bool, str]:
    """Return whether task execution has a reachable LLM backend."""
    token_ready = False
    try:
        from token_factory import TokenFactory as _TF

        tf = _TF.instance()
        tf_status = await tf.ensure_ready()
        token_ready = tf_status.get("ready", False)
        _harness_log.info(
            "[task_runtime] Token Factory ready=%s, providers=%s",
            token_ready,
            [n for n, p in tf._provider_health.items() if p.reachable],
        )
    except Exception as _tf_err:
        _harness_log.warning("[task_runtime] Token Factory check failed: %s", _tf_err)

    if token_ready:
        return True, ""

    api_key, _, _ = _get_deepseek_credentials()
    if api_key:
        _harness_log.info("[task_runtime] Direct DeepSeek API available — proceeding")
        return True, ""

    return False, "LLM 推理后端不可用，任务已创建但未启动执行"


def _prepare_task_submission(task: AgentTask, team_id: str, token_ready: bool) -> list:
    """Seed workflow/context and persist a task handoff record before execution."""
    wf = _generate_workflow(task, team_id)
    if wf:
        task.metadata["workflow"] = wf

    try:
        _seed_project_context(task.task_id, task.title, task.description or "")
        task.metadata["pipeline_dir"] = _pipeline_dir(task.task_id)
    except Exception as _ctx_err:
        _harness_log.warning("[task_prepare] Context seeding failed: %s", _ctx_err)

    _write_handoff(task.task_id, "task_init", {
        "task_id": task.task_id,
        "title": task.title,
        "description": task.description,
        "team_id": team_id,
        "agent_id": task.agent_id,
        "token_factory_ready": token_ready,
        "workflow_steps": [s["key"] for s in wf] if wf else [],
    })
    return wf


def _summarize_task_execution_artifacts(task: AgentTask) -> Dict[str, Any]:
    """Summarize workflow outputs into stable task artifact metadata."""
    metadata = task.metadata or {}
    workflow = metadata.get("workflow", []) or []
    pipeline_dir = metadata.get("pipeline_dir") or metadata.get("artifact_dir") or _pipeline_dir(task.task_id)

    changed_files: List[str] = []
    step_artifacts: Dict[str, str] = {}
    failed_steps: List[str] = []
    completed_steps: List[str] = []
    step_statuses: Dict[str, str] = {}
    test_result: Dict[str, Any] = {}

    for step in workflow:
        step_key = str(step.get("key", "")).strip()
        if not step_key:
            continue

        step_status = str(step.get("status", "pending"))
        step_statuses[step_key] = step_status
        if step_status == "completed":
            completed_steps.append(step_key)
        elif step_status == "failed":
            failed_steps.append(step_key)

        artifact_path = str(step.get("artifact", "")).strip()
        if artifact_path:
            step_artifacts[step_key] = artifact_path

        step_summary = step.get("_summary") or {}
        changed_files.extend(step_summary.get("files_changed", []) or [])
        changed_files.extend(step.get("deliverable_paths", []) or [])

        deploy_result = step.get("deploy_result") or {}
        for branch in ("developer", "deployer"):
            branch_result = deploy_result.get(branch) or {}
            changed_files.extend(
                entry.get("path", "")
                for entry in branch_result.get("applied", [])
                if entry.get("path")
            )

        if step_key == "test":
            test_result = {
                "status": step_status,
                "verdict": step_summary.get("verdict", "UNKNOWN"),
                "checklist": step_summary.get("checklist", []) or [],
                "artifact": artifact_path,
            }

    deduped_changed_files: List[str] = []
    seen_files: set[str] = set()
    for path in changed_files:
        normalized = str(path).strip()
        if not normalized or normalized in seen_files:
            continue
        seen_files.add(normalized)
        deduped_changed_files.append(normalized)

    diff_evidence = _build_diff_evidence(deduped_changed_files, workflow)
    trace_context = _build_task_trace_context(task)

    failure_reason = ""
    build_outcome = "completed"
    if task.error:
        build_outcome = "failed"
        failure_reason = task.error
    elif failed_steps:
        build_outcome = "failed"
        failure_reason = f"workflow_failed:{','.join(failed_steps)}"
    elif test_result.get("status") == "failed" or test_result.get("verdict") in {"FAIL", "FAILED", "BLOCKED"}:
        build_outcome = "failed"
        failure_reason = f"qa_verdict:{test_result.get('verdict', 'UNKNOWN')}"

    return {
        "artifact_dir": pipeline_dir,
        "changed_files": deduped_changed_files,
        "test_result": test_result,
        "workflow_summary": {
            "total_steps": len(workflow),
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "step_statuses": step_statuses,
        },
        "step_artifacts": step_artifacts,
        "diff_by_file": diff_evidence["diff_by_file"],
        "patch_preview": diff_evidence["patch_preview"],
        "trace_context": trace_context,
        "build_outcome": build_outcome,
        "failure_reason": failure_reason,
    }


def _build_diff_evidence(
    changed_files: List[str],
    workflow: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build small diff artifacts from deploy backups and current files."""
    import difflib

    project_root = _mp_os.path.dirname(_mp_os.path.dirname(_mp_os.path.dirname(
        _mp_os.path.dirname(_mp_os.path.abspath(__file__)))))
    backup_map: Dict[str, str] = {}

    for step in workflow:
        deploy_result = step.get("deploy_result") or {}
        for branch in ("developer", "deployer"):
            branch_result = deploy_result.get(branch) or {}
            for entry in branch_result.get("backup", []) or []:
                path = str(entry.get("path", "")).strip()
                backup = str(entry.get("backup", "")).strip()
                if path and backup and path not in backup_map:
                    backup_map[path] = backup

    diff_by_file: Dict[str, List[str]] = {}
    patch_chunks: List[str] = []

    for rel_path in changed_files[:20]:
        abs_path = _mp_os.path.join(project_root, rel_path)
        backup_path = backup_map.get(rel_path, "")

        if not _mp_os.path.isfile(abs_path):
            continue

        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                after_text = f.read()
        except Exception:
            continue

        before_text = ""
        if backup_path and _mp_os.path.isfile(backup_path):
            try:
                with open(backup_path, "r", encoding="utf-8", errors="replace") as f:
                    before_text = f.read()
            except Exception:
                before_text = ""

        diff_lines = list(
            difflib.unified_diff(
                before_text.splitlines(),
                after_text.splitlines(),
                fromfile=f"{rel_path} (before)",
                tofile=f"{rel_path} (after)",
                lineterm="",
            )
        )
        if not diff_lines:
            continue

        preview_lines = diff_lines[:80]
        diff_by_file[rel_path] = preview_lines
        patch_chunks.append("\n".join(diff_lines[:200]))

    patch_preview = "\n\n".join(patch_chunks)
    if len(patch_preview) > 24000:
        patch_preview = patch_preview[:24000] + "\n... (truncated)"

    return {
        "diff_by_file": diff_by_file,
        "patch_preview": patch_preview,
    }


def _attach_task_execution_artifacts(task: AgentTask) -> Dict[str, Any]:
    """Write derived execution artifacts back to the task metadata for tracing."""
    artifacts = _summarize_task_execution_artifacts(task)
    task.metadata["artifact_dir"] = artifacts["artifact_dir"]
    task.metadata["changed_files"] = list(artifacts["changed_files"])
    task.metadata["test_result"] = dict(artifacts["test_result"])
    task.metadata["workflow_summary"] = dict(artifacts["workflow_summary"])
    task.metadata["step_artifacts"] = dict(artifacts["step_artifacts"])
    task.metadata["diff_by_file"] = dict(artifacts["diff_by_file"])
    task.metadata["patch_preview"] = artifacts["patch_preview"]
    task.metadata["trace_context"] = dict(artifacts["trace_context"])
    task.metadata["build_outcome"] = artifacts["build_outcome"]
    task.metadata["failure_reason"] = artifacts["failure_reason"]
    task.metadata["execution_artifacts"] = dict(artifacts)
    trace_summary = _build_task_trace_summary(task, artifacts)
    task.metadata["trace_summary"] = trace_summary
    _persist_trace_summary(task, trace_summary)
    return artifacts


def _build_task_trace_context(task: AgentTask) -> Dict[str, Any]:
    """Build a stable trace context for task/execution/evolution joins."""
    metadata = task.metadata or {}
    existing = dict(metadata.get("trace_context") or {})
    context = {
        "source": metadata.get("source", existing.get("source", "")),
        "task_id": task.task_id,
        "team_id": task.team_id,
        "agent_id": task.agent_id,
        "plaza_id": metadata.get("plaza_id", existing.get("plaza_id", "")),
        "discussion_id": metadata.get("discussion_id", existing.get("discussion_id", "")),
        "discussion_topic": metadata.get("discussion_topic", existing.get("discussion_topic", "")),
        "plan_revision": metadata.get("plan_revision", existing.get("plan_revision")),
        "plan_item_index": metadata.get("plan_item_index", existing.get("plan_item_index")),
        "evolution_item_ids": list(metadata.get("evolution_item_ids", existing.get("evolution_item_ids", [])) or []),
    }
    for key, value in existing.items():
        context.setdefault(key, value)
    return context


def _build_task_trace_summary(
    task: AgentTask,
    artifacts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a compact trace summary for UI/debug endpoints."""
    artifacts = artifacts or dict(task.metadata.get("execution_artifacts") or {})
    trace_context = dict(artifacts.get("trace_context") or _build_task_trace_context(task))
    recent_events = _read_task_trace_events(task)
    linked_items = []
    try:
        import agent_team_api as _agent_team_api

        evolution_engine = getattr(_agent_team_api, "_evolution_engine", None)
        if evolution_engine:
            for item_id in trace_context.get("evolution_item_ids", []) or []:
                item = evolution_engine.evolution_items.get(item_id)
                if item:
                    linked_items.append(
                        {
                            "id": item.id,
                            "status": item.status,
                            "title": item.title,
                            "verify_test_name": item.verify_test_name,
                            "verify_result": item.verify_result,
                            "verify_detail": item.verify_detail,
                            "retry_count": item.retry_count,
                            "max_retries": item.max_retries,
                        }
                    )
    except Exception:
        linked_items = []

    return {
        "task_id": task.task_id,
        "team_id": task.team_id,
        "agent_id": task.agent_id,
        "status": task.status.value,
        "source": task.metadata.get("source", ""),
        "trace_context": trace_context,
        "workflow_summary": dict(artifacts.get("workflow_summary") or {}),
        "changed_files": list(artifacts.get("changed_files") or []),
        "test_result": dict(artifacts.get("test_result") or {}),
        "build_outcome": artifacts.get("build_outcome", ""),
        "failure_reason": artifacts.get("failure_reason", ""),
        "linked_evolution_items": linked_items,
        "trace_event_count": len(recent_events),
        "recent_trace_events": recent_events[-10:],
    }


def _persist_trace_summary(task: AgentTask, trace_summary: Dict[str, Any]) -> None:
    """Persist a stable trace summary alongside pipeline artifacts when available."""
    artifact_dir = str(task.metadata.get("artifact_dir") or "").strip()
    if not artifact_dir:
        return
    try:
        _os.makedirs(artifact_dir, exist_ok=True)
        trace_path = _os.path.join(artifact_dir, "trace_summary.json")
        import json as _json

        with open(trace_path, "w", encoding="utf-8") as f:
            _json.dump(trace_summary, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        _harness_log.debug("[TraceSummary] persist skipped for %s: %s", task.task_id, exc)


def _read_task_trace_events(task: AgentTask) -> List[Dict[str, Any]]:
    """Read persisted structured trace events for a task."""
    artifact_dir = str(task.metadata.get("artifact_dir") or task.metadata.get("pipeline_dir") or "").strip()
    if not artifact_dir:
        artifact_dir = _pipeline_dir(task.task_id)
    trace_path = _os.path.join(artifact_dir, "trace_events.jsonl")
    if not _os.path.isfile(trace_path):
        return []

    events: List[Dict[str, Any]] = []
    try:
        import json as _json

        with open(trace_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(_json.loads(line))
                except Exception:
                    continue
    except Exception as exc:
        _harness_log.debug("[TraceEvents] read skipped for %s: %s", task.task_id, exc)
    return events


def _append_task_trace_event(
    task: AgentTask,
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist a structured trace event and keep a small in-memory tail on the task."""
    payload = dict(payload or {})
    artifact_dir = str(task.metadata.get("artifact_dir") or task.metadata.get("pipeline_dir") or "").strip()
    if not artifact_dir:
        artifact_dir = _pipeline_dir(task.task_id)
        task.metadata.setdefault("pipeline_dir", artifact_dir)
    trace_context = _build_task_trace_context(task)
    event = {
        "type": event_type,
        "ts": _time.time(),
        "task_id": task.task_id,
        "team_id": task.team_id,
        "status": task.status.value,
        "trace_context": trace_context,
        "payload": payload,
    }
    try:
        import json as _json

        _os.makedirs(artifact_dir, exist_ok=True)
        trace_path = _os.path.join(artifact_dir, "trace_events.jsonl")
        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(_json.dumps(event, ensure_ascii=False) + "\n")
        global_trace_path = _global_trace_events_path()
        _os.makedirs(_os.path.dirname(global_trace_path), exist_ok=True)
        with open(global_trace_path, "a", encoding="utf-8") as f:
            f.write(_json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as exc:
        _harness_log.debug("[TraceEvents] append skipped for %s: %s", task.task_id, exc)

    recent_events = list(task.metadata.get("trace_events") or [])
    recent_events.append(event)
    if len(recent_events) > 50:
        recent_events = recent_events[-50:]
    task.metadata["trace_events"] = recent_events
    return event


def _build_discussion_verification_state_payload(
    evolution_engine: Any,
    *,
    plaza_id: str,
    discussion_id: str,
    trigger: str,
    task_id: str = "",
    synced_item_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a consistent SSE payload for Plaza verification reminders."""
    queue_items = evolution_engine.get_verification_queue(
        source_plaza_id=plaza_id,
        source_discussion_id=discussion_id,
    )
    alerts = evolution_engine.get_verification_alerts(
        source_plaza_id=plaza_id,
        source_discussion_id=discussion_id,
    )
    status_counts: Dict[str, int] = {}
    for item in queue_items:
        status = str(item.get("status", "") or "")
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "type": "verification_state_updated",
        "trigger": trigger,
        "plaza_id": plaza_id,
        "discussion_id": discussion_id,
        "task_id": task_id,
        "synced_item_ids": list(synced_item_ids or []),
        "queue_count": len(queue_items),
        "alert_count": len(alerts),
        "status_counts": status_counts,
        "queue": queue_items,
        "alerts": alerts,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _broadcast_plaza_verification_state(
    task: AgentTask,
    *,
    synced_item_ids: Optional[List[str]] = None,
    trigger: str,
) -> None:
    """Push verification reminder updates into Plaza SSE when a linked task changes state."""
    metadata = task.metadata or {}
    if metadata.get("source") != "plaza":
        return

    plaza_id = str(metadata.get("plaza_id") or "").strip()
    discussion_id = str(metadata.get("discussion_id") or "").strip()
    if not plaza_id or not discussion_id:
        return

    try:
        import agent_team_api as _agent_team_api
        from .plaza_engine import get_plaza_engine
    except Exception:
        return

    evolution_engine = getattr(_agent_team_api, "_evolution_engine", None)
    if not evolution_engine or not hasattr(evolution_engine, "get_verification_queue"):
        return

    plaza_engine = get_plaza_engine()
    if not plaza_engine.get_discussion(plaza_id, discussion_id):
        return

    payload = _build_discussion_verification_state_payload(
        evolution_engine,
        plaza_id=plaza_id,
        discussion_id=discussion_id,
        trigger=trigger,
        task_id=task.task_id,
        synced_item_ids=synced_item_ids,
    )
    await plaza_engine._broadcast(discussion_id, payload)
    _append_task_trace_event(
        task,
        "verification_state_broadcasted",
        {
            "trigger": trigger,
            "queue_count": payload["queue_count"],
            "alert_count": payload["alert_count"],
            "synced_item_ids": list(synced_item_ids or []),
        },
    )


def _sync_evolution_from_task(task: AgentTask) -> List[str]:
    """Propagate Plaza task execution status into linked evolution items."""
    metadata = task.metadata or {}
    if metadata.get("source") != "plaza":
        return []

    try:
        import agent_team_api as _agent_team_api
    except Exception:
        return []

    evolution_engine = getattr(_agent_team_api, "_evolution_engine", None)
    if not evolution_engine or not hasattr(evolution_engine, "sync_task_outcome"):
        return []

    artifacts = metadata.get("execution_artifacts") or _attach_task_execution_artifacts(task)
    evolution_status = "completed"
    if artifacts.get("build_outcome") == "failed" or task.error:
        evolution_status = "failed"

    synced_item_ids = evolution_engine.sync_task_outcome(
        task.task_id,
        status=evolution_status,
        code_changes=artifacts.get("changed_files"),
        artifact_dir=artifacts.get("artifact_dir", ""),
        build_artifacts=artifacts,
        error=task.error or artifacts.get("failure_reason", ""),
    )
    if synced_item_ids:
        synced_items = []
        for item_id in synced_item_ids:
            item = evolution_engine.evolution_items.get(item_id)
            if not item:
                continue
            synced_items.append(
                {
                    "id": item.id,
                    "status": item.status,
                    "title": item.title,
                }
            )
        _append_task_trace_event(
            task,
            "evolution_synced",
            {
                "evolution_status": evolution_status,
                "items": synced_items,
            },
        )
    return synced_item_ids


async def _finalize_task_terminal_state(
    task: AgentTask,
    *,
    force_status: Optional[str] = None,
    error: str = "",
) -> Optional[AgentTask]:
    """Finalize a task with derived execution artifacts and evolution sync."""
    artifacts = _attach_task_execution_artifacts(task)
    final_error = error or task.error or artifacts.get("failure_reason", "")

    finalized: Optional[AgentTask]
    if force_status == "failed" or (force_status is None and artifacts.get("build_outcome") == "failed"):
        task.error = final_error
        task.result = dict(artifacts)
        finalized = await _te().fail_task(task.task_id, final_error)
    else:
        result_payload = dict(task.result) if isinstance(task.result, dict) else {}
        result_payload.update(artifacts)
        finalized = await _te().complete_task(task.task_id, result=result_payload)

    if finalized is not None:
        _append_task_trace_event(
            finalized,
            "task_finalized",
            {
                "build_outcome": artifacts.get("build_outcome", ""),
                "failure_reason": final_error,
                "changed_files": list(artifacts.get("changed_files") or []),
                "test_result": dict(artifacts.get("test_result") or {}),
            },
        )
        synced_item_ids = _sync_evolution_from_task(finalized)
        await _broadcast_plaza_verification_state(
            finalized,
            synced_item_ids=synced_item_ids,
            trigger="task_finalized",
        )
    return finalized


async def _start_task_workflow(engine, task: AgentTask, team_id: str, wf: list) -> None:
    """Launch the first workflow step and attach the harness monitor."""
    if not wf:
        return

    first_step = wf[0]
    if first_step.get("status") == "active" and first_step.get("agent_id"):
        import uuid as _uuid

        sr = _sr()
        skill = sr.get_by_slug("code_implementation")
        cfg = dict(skill.config or {}) if skill else {}
        agent = _tm().get_agent(team_id, first_step["agent_id"])
        if agent:
            sid = str(_uuid.uuid4())[:12]
            step_prompt = _build_step_prompt(task, first_step, wf)
            _harness_log.info(
                "[task_start] Starting Claude session %s for step '%s' (agent: %s)",
                sid,
                first_step["key"],
                agent.name,
            )
            _start_claude_session(sid, step_prompt, cfg, agent, task.task_id)
            first_step["session_id"] = sid
            task.metadata["workflow"] = wf
            _emit_pipeline_event(task.task_id, "step_started", {
                "step": first_step["key"],
                "label": first_step.get("label", ""),
                "agent": agent.name,
            })

    await engine.start_task(task.task_id)
    _start_harness_monitor(task.task_id, team_id)


async def _submit_internal_task(
    team_id: str,
    *,
    title: str,
    description: str = "",
    agent_id: str = "",
    priority: int = 2,
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    auto_start: bool = True,
) -> AgentTask:
    """Create a task using the same workflow/bootstrap path as the REST endpoint."""
    _get_team_or_404(team_id)
    if agent_id:
        _get_agent_or_404(team_id, agent_id)

    engine = _te()
    if not engine._running:
        await engine.start()

    token_ready = False
    token_error = ""
    if auto_start:
        token_ready, token_error = await _check_task_runtime_ready()

    task = AgentTask(
        agent_id=agent_id,
        team_id=team_id,
        title=title,
        description=description,
        priority=priority,
        dependencies=list(dependencies or []),
        metadata=dict(metadata or {}),
    )

    wf = _prepare_task_submission(task, team_id, token_ready)
    await engine.submit_task(task)

    if auto_start and not token_ready:
        _harness_log.warning(
            "[task_submit] Runtime unavailable — task %s queued but not started",
            task.task_id,
        )
        task.metadata["token_factory_error"] = token_error
        engine._store.save_task(task)
        return task

    if auto_start:
        await _start_task_workflow(engine, task, team_id, wf)

    return task


async def _real_task_executor(task) -> Any:
    """Real executor callback — invoked by TaskEngine._execute() for queued tasks.

    This bridges the TaskEngine's internal queue with the Claude Code workflow
    pipeline.  When a task is submitted via submit_batch() or directly enqueued,
    the executor generates a workflow, starts a Claude session for step 1, and
    launches the harness monitor for auto-advancement.

    For tasks submitted via the REST API, the submit_task endpoint handles this
    directly (so the executor won't be triggered for those).
    """
    import uuid as _uuid

    # Skip if workflow already started (e.g., via the REST endpoint)
    if task.metadata.get("workflow") and any(
        s.get("session_id") for s in task.metadata["workflow"]
    ):
        return {"message": "Workflow already running via REST endpoint"}

    # Token Factory preflight — but if direct DeepSeek API is available, skip
    api_key, _, _ = _get_deepseek_credentials()
    if api_key:
        _harness_log.info("[Executor] Direct DeepSeek API available — skipping Token Factory check")
    else:
        from token_factory import TokenFactory as _TF
        tf = _TF.instance()
        tf_status = await tf.ensure_ready()
        if not tf_status.get("ready", False):
            _harness_log.error("[Executor] Token Factory not ready for task %s — aborting", task.task_id)
            raise RuntimeError("Token Factory (LLM 推理后端) 不可用，无法执行任务。"
                               "请确保 Ollama 或其他 LLM 端点已启动。")

    # Generate workflow if none exists
    wf = task.metadata.get("workflow")
    if not wf:
        wf = _generate_workflow(task, task.team_id)
        task.metadata["workflow"] = wf

    if not wf:
        return {"message": "No workflow generated"}

    # Pre-seed pipeline workspace with project context
    try:
        _seed_project_context(task.task_id, task.title, task.description or "")
        task.metadata["pipeline_dir"] = _pipeline_dir(task.task_id)
    except Exception as _ctx_err:
        _harness_log.warning("[Executor] Context seeding failed: %s", _ctx_err)

    # Start first step
    first_step = wf[0]
    if first_step.get("status") != "active":
        first_step["status"] = "active"

    if first_step.get("agent_id"):
        sr = _sr()
        skill = sr.get_by_slug("code_implementation")
        cfg = dict(skill.config or {}) if skill else {}
        tm = _tm()
        agent = tm.get_agent(task.team_id, first_step["agent_id"])
        if agent:
            sid = str(_uuid.uuid4())[:12]
            step_prompt = _build_step_prompt(task, first_step, wf)
            _harness_log.info("[Executor] Starting Claude session %s for task %s step '%s'",
                              sid, task.task_id, first_step["key"])
            _start_claude_session(sid, step_prompt, cfg, agent, task.task_id)
            first_step["session_id"] = sid
            task.metadata["workflow"] = wf

    # Start harness monitor
    _start_harness_monitor(task.task_id, task.team_id)

    _write_handoff(task.task_id, "executor_started", {
        "task_id": task.task_id,
        "title": task.title,
        "first_step": first_step.get("key", ""),
        "executor": "real_task_executor",
    })

    return {"message": f"Workflow started with {len(wf)} steps", "first_session": first_step.get("session_id")}


@router.post(
    "/teams/{team_id}/tasks",
    summary="Submit a task for execution",
    status_code=status.HTTP_201_CREATED,
)
async def submit_task(team_id: str, req: SubmitTaskRequest) -> Dict[str, Any]:
    task = await _submit_internal_task(
        team_id,
        title=req.title,
        description=req.description,
        agent_id=req.agent_id,
        priority=req.priority,
        dependencies=req.dependencies,
        metadata=req.metadata,
        auto_start=True,
    )
    return task.to_dict()


@router.post(
    "/teams/{team_id}/tasks/batch",
    summary="Submit batch tasks with dependencies",
    status_code=status.HTTP_201_CREATED,
)
async def submit_batch_tasks(
    team_id: str, req: SubmitBatchRequest
) -> List[Dict[str, Any]]:
    _get_team_or_404(team_id)
    engine = _te()
    if not engine._running:
        await engine.start()
    tasks = []
    for item in req.tasks:
        if item.agent_id:
            _get_agent_or_404(team_id, item.agent_id)
        t = AgentTask(
            agent_id=item.agent_id,
            team_id=team_id,
            title=item.title,
            description=item.description,
            priority=item.priority,
            dependencies=list(item.dependencies),
            metadata=dict(item.metadata),
        )
        tasks.append(t)
    await engine.submit_batch(tasks)
    return [t.to_dict() for t in tasks]


@router.get("/teams/{team_id}/tasks", summary="List all tasks for a team")
def list_team_tasks(
    team_id: str,
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    _get_team_or_404(team_id)
    items = [t.to_dict() for t in _te().get_team_tasks(team_id)]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get(
    "/teams/{team_id}/tasks/{task_id}",
    summary="Get task detail",
)
def get_task_detail(team_id: str, task_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task.to_dict()


@router.get(
    "/teams/{team_id}/tasks/{task_id}/trace-summary",
    summary="Get task trace summary",
)
def get_task_trace_summary(team_id: str, task_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _build_task_trace_summary(task)


@router.get(
    "/teams/{team_id}/tasks/{task_id}/trace-events",
    summary="Get task trace events",
)
def get_task_trace_events(team_id: str, task_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    events = _read_task_trace_events(task)
    return {
        "task_id": task.task_id,
        "team_id": task.team_id,
        "count": len(events),
        "events": events,
    }


@router.get(
    "/teams/{team_id}/discussions/{discussion_id}/trace-summary",
    summary="Get trace summaries for all tasks linked to a discussion",
)
def get_discussion_trace_summary(team_id: str, discussion_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    tasks = [
        task
        for task in _te().get_team_tasks(team_id)
        if (task.metadata or {}).get("discussion_id") == discussion_id
    ]
    summaries = [_build_task_trace_summary(task) for task in tasks]
    return {
        "team_id": team_id,
        "discussion_id": discussion_id,
        "count": len(summaries),
        "tasks": summaries,
    }


@router.get(
    "/traces/recent",
    summary="Get recent task trace summaries across teams",
)
def get_recent_trace_summaries(
    limit: int = 20,
    team_id: str = "",
    source: str = "",
) -> Dict[str, Any]:
    limit = max(1, min(int(limit or 20), 100))
    tasks = _te().list_tasks()
    if team_id:
        tasks = [task for task in tasks if task.team_id == team_id]
    if source:
        tasks = [task for task in tasks if (task.metadata or {}).get("source") == source]

    summaries = []
    for task in tasks:
        metadata = task.metadata or {}
        if not (metadata.get("trace_summary") or metadata.get("artifact_dir") or metadata.get("pipeline_dir")):
            continue
        summary = _build_task_trace_summary(task)
        recent_events = summary.get("recent_trace_events") or []
        if recent_events:
            sort_ts = float(recent_events[-1].get("ts") or 0.0)
        else:
            sort_ts = 0.0
            for value in (task.completed_at, task.started_at, task.created_at):
                if not value:
                    continue
                try:
                    sort_ts = datetime.fromisoformat(value).timestamp()
                except Exception:
                    continue
                break
        summaries.append((sort_ts, summary))

    summaries.sort(key=lambda item: item[0], reverse=True)
    payload = [summary for _, summary in summaries[:limit]]
    return {
        "count": len(payload),
        "limit": limit,
        "team_id": team_id,
        "source": source,
        "traces": payload,
    }


@router.get(
    "/traces/recent-events",
    summary="Get recent trace events across tasks",
)
def get_recent_trace_events(
    limit: int = 50,
    team_id: str = "",
    source: str = "",
    event_type: str = "",
) -> Dict[str, Any]:
    limit = max(1, min(int(limit or 50), 200))
    tasks = _te().list_tasks()
    if team_id:
        tasks = [task for task in tasks if task.team_id == team_id]
    if source:
        tasks = [task for task in tasks if (task.metadata or {}).get("source") == source]

    events: List[Dict[str, Any]] = []
    for task in tasks:
        for event in _read_task_trace_events(task):
            if event_type and event.get("type") != event_type:
                continue
            enriched = dict(event)
            enriched.setdefault("task_id", task.task_id)
            enriched.setdefault("team_id", task.team_id)
            events.append(enriched)

    events.sort(key=lambda event: float(event.get("ts") or 0.0), reverse=True)
    payload = events[:limit]
    return {
        "count": len(payload),
        "limit": limit,
        "team_id": team_id,
        "source": source,
        "event_type": event_type,
        "events": payload,
    }


@router.get(
    "/traces/log-tail",
    summary="Tail the global structured trace event log",
)
def get_trace_log_tail(
    limit: int = 100,
    event_type: str = "",
) -> Dict[str, Any]:
    limit = max(1, min(int(limit or 100), 500))
    events = _read_global_trace_events(event_type=event_type)
    events = events[-limit:]
    return {
        "count": len(events),
        "limit": limit,
        "event_type": event_type,
        "events": events,
    }


@router.get(
    "/traces/export",
    summary="Export global trace events as NDJSON",
)
def export_trace_events(
    limit: int = 1000,
    event_type: str = "",
    team_id: str = "",
    source: str = "",
    since_ts: float = 0.0,
):
    from starlette.responses import StreamingResponse
    import json as _json

    limit = max(1, min(int(limit or 1000), 5000))
    events = _read_global_trace_events(
        event_type=event_type,
        team_id=team_id,
        source=source,
        since_ts=since_ts,
    )[-limit:]

    def event_gen():
        for event in events:
            yield _json.dumps(event, ensure_ascii=False) + "\n"

    return StreamingResponse(
        event_gen(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "inline; filename=trace_events.ndjson",
        },
    )


@router.delete(
    "/teams/{team_id}/tasks/{task_id}",
    summary="Cancel a task",
)
async def cancel_task(team_id: str, task_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    task = await _te().cancel_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task.to_dict()


@router.post(
    "/teams/{team_id}/tasks/{task_id}/stop",
    summary="Force stop a running task",
)
async def stop_task(team_id: str, task_id: str) -> Dict[str, Any]:
    """Kill all Claude Code sessions for this task, then cancel it."""
    _get_team_or_404(team_id)
    killed = 0
    to_remove = []
    for sid, s in _claude_sessions.items():
        if s.get("task_id") == task_id:
            proc = s.get("proc")
            if proc and proc.poll() is None:
                try: proc.terminate(); proc.wait(timeout=5)
                except Exception:
                    try: proc.kill()
                    except Exception: pass
                killed += 1
            s["status"] = "stopped"
            to_remove.append(sid)
    for sid in to_remove:
        _claude_sessions.pop(sid, None)
    task = await _te().cancel_task(task_id)
    return {"task_id": task_id, "killed_sessions": killed, "status": task.status if task else "unknown"}


@router.delete(
    "/teams/{team_id}/tasks/{task_id}/remove",
    summary="Permanently delete a task",
)
async def remove_task(team_id: str, task_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    task = await _te().delete_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"deleted": True, "task_id": task_id}


@router.post(
    "/teams/{team_id}/tasks/{task_id}/start",
    summary="Start a pending task (mark as running)",
)
async def start_task_endpoint(team_id: str, task_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    task = await _te().start_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Manual start from UI should launch the same workflow executor path used by
    # auto-start on submit, not just flip the task status to running.
    try:
        await _real_task_executor(task)
    except RuntimeError as exc:
        task.metadata["token_factory_error"] = str(exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        _harness_log.exception("[start_task_endpoint] Failed to launch workflow for task %s", task_id)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"任务已标记为运行，但工作流启动失败: {exc}")

    return task.to_dict()


@router.post(
    "/teams/{team_id}/tasks/{task_id}/complete",
    summary="Mark a task as completed",
)
async def complete_task_endpoint(team_id: str, task_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    task = await _finalize_task_terminal_state(task, force_status="completed")
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task.to_dict()


@router.post(
    "/teams/{team_id}/tasks/{task_id}/fail",
    summary="Mark a task as failed",
)
async def fail_task_endpoint(team_id: str, task_id: str) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    task = await _finalize_task_terminal_state(
        task,
        force_status="failed",
        error=(task.metadata or {}).get("pipeline_failed_reason", "") or task.error,
    )
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task.to_dict()


# ── Workflow Steps (per-task execution pipeline visualization) ──────


# Role → workflow step definitions
_ROLE_WORKFLOW_MAP: Dict[str, list] = {
    "project_manager": [
        {"key": "pm_decompose", "label": "PM分解", "agent_role": "project_manager"},
        {"key": "research", "label": "研究分析", "agent_role": "researcher"},
        {"key": "architecture", "label": "架构设计", "agent_role": "architect"},
        {"key": "develop", "label": "代码开发", "agent_role": "developer"},
        {"key": "test", "label": "测试验证", "agent_role": "qa_engineer"},
        {"key": "deploy", "label": "部署上线", "agent_role": "devops"},
        {"key": "document", "label": "文档更新", "agent_role": "documentation"},
    ],
    "researcher": [
        {"key": "research", "label": "研究分析", "agent_role": "researcher"},
        {"key": "architecture", "label": "架构设计", "agent_role": "architect"},
        {"key": "develop", "label": "代码开发", "agent_role": "developer"},
        {"key": "test", "label": "测试验证", "agent_role": "qa_engineer"},
    ],
    "architect": [
        {"key": "architecture", "label": "架构设计", "agent_role": "architect"},
        {"key": "develop", "label": "代码开发", "agent_role": "developer"},
        {"key": "test", "label": "测试验证", "agent_role": "qa_engineer"},
    ],
    "developer": [
        {"key": "develop", "label": "代码开发", "agent_role": "developer"},
        {"key": "test", "label": "测试验证", "agent_role": "qa_engineer"},
    ],
    "qa_engineer": [
        {"key": "test", "label": "测试验证", "agent_role": "qa_engineer"},
    ],
    "devops": [
        {"key": "develop", "label": "代码开发", "agent_role": "developer"},
        {"key": "test", "label": "测试验证", "agent_role": "qa_engineer"},
        {"key": "deploy", "label": "部署上线", "agent_role": "devops"},
    ],
    "documentation": [
        {"key": "document", "label": "文档更新", "agent_role": "documentation"},
    ],
}

# Default full pipeline (used for cross-team tasks assigned to PM)
_FULL_PIPELINE = _ROLE_WORKFLOW_MAP["project_manager"]


def _generate_workflow(task: "AgentTask", team_id: str) -> list:
    """Generate workflow steps for a task based on its agent role."""
    tm = _tm()
    agent = tm.get_agent(team_id, task.agent_id) if task.agent_id else None

    # Determine role
    role = ""
    if agent:
        role = getattr(agent, "role", "")
    # Cross-team tasks default to full pipeline
    is_cross = task.metadata.get("cross_team", False)
    if is_cross and not role:
        role = "project_manager"

    steps_template = _ROLE_WORKFLOW_MAP.get(role, [])
    if not steps_template:
        # Default to full pipeline for build_system team, single step otherwise
        if team_id == "build_system" or is_cross:
            steps_template = _FULL_PIPELINE
        else:
            label = (agent.name if agent else task.agent_id) or "执行"
            steps_template = [{"key": "execute", "label": label, "agent_role": role or "unknown"}]

    # Resolve agent_id for each role in this team
    role_to_agent: Dict[str, str] = {}
    team = tm.get_team(team_id)
    if team:
        agents_list = team.get("agents", []) if isinstance(team, dict) else getattr(team, "agents", [])
        if isinstance(agents_list, dict):
            agents_list = list(agents_list.values())
        for a in agents_list:
            a_role = a.get("role", "") if isinstance(a, dict) else getattr(a, "role", "")
            a_id = a.get("agent_id", "") if isinstance(a, dict) else getattr(a, "agent_id", "")
            a_name = a.get("name", "") if isinstance(a, dict) else getattr(a, "name", "")
            if a_role and a_id:
                role_to_agent[a_role] = a_id

    steps = []
    for i, tmpl in enumerate(steps_template):
        resolved_agent = role_to_agent.get(tmpl["agent_role"], "")
        steps.append({
            "index": i,
            "key": tmpl["key"],
            "label": tmpl["label"],
            "agent_id": resolved_agent,
            "agent_role": tmpl["agent_role"],
            "status": "pending",  # pending | active | completed | skipped
        })
    # First step is active if task is pending/running
    if steps and task.status.value in ("pending", "running"):
        steps[0]["status"] = "active"
    return steps


@router.post(
    "/teams/{team_id}/tasks/{task_id}/workflow/advance",
    summary="Advance task workflow to next step",
)
async def advance_workflow(team_id: str, task_id: str) -> Dict[str, Any]:
    """Mark current active step as completed, activate and auto-start Claude Code on next step."""
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    wf = task.metadata.get("workflow", [])
    if not wf:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No workflow steps")
    # Find active step
    active_idx = -1
    for s in wf:
        if s["status"] == "active":
            active_idx = s["index"]
            break
    if active_idx < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No active step")

    # Collect artifact from completed step's Claude session (if any)
    completed_step = wf[active_idx]
    _collect_step_artifact(task, completed_step)

    # Complete current, activate next
    wf[active_idx]["status"] = "completed"
    if active_idx + 1 < len(wf):
        wf[active_idx + 1]["status"] = "active"
        next_step = wf[active_idx + 1]
        # Auto-start Claude Code for EVERY step
        if next_step.get("agent_id"):
            import uuid as _uuid
            sr = _sr()
            skill = sr.get_by_slug("code_implementation")
            cfg = dict(skill.config or {}) if skill else {}
            agent = _tm().get_agent(team_id, next_step["agent_id"])
            if agent:
                sid = str(_uuid.uuid4())[:12]
                step_prompt = _build_step_prompt(task, next_step, wf)
                _start_claude_session(sid, step_prompt, cfg, agent, task_id)
                next_step["session_id"] = sid
    task.metadata["workflow"] = wf
    # Ensure harness monitor is running
    _start_harness_monitor(task_id, team_id)
    # Check if all completed
    all_done = all(s["status"] in ("completed", "skipped") for s in wf)
    # Auto-complete the task when all workflow steps are done
    if all_done and task.status.value in ("pending", "running"):
        await _finalize_task_terminal_state(task)
    return {"workflow": wf, "all_completed": all_done, "task_id": task_id}


@router.post(
    "/teams/{team_id}/tasks/{task_id}/workflow/{step_index}/status",
    summary="Set a specific workflow step status",
)
async def set_workflow_step_status(
    team_id: str, task_id: str, step_index: int, req: Dict[str, str]
) -> Dict[str, Any]:
    """Set status of a specific workflow step (completed/active/skipped/pending)."""
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    wf = task.metadata.get("workflow", [])
    new_status = req.get("status", "")
    if new_status not in ("pending", "active", "completed", "skipped"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    if step_index < 0 or step_index >= len(wf):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid step index")
    wf[step_index]["status"] = new_status
    task.metadata["workflow"] = wf
    return {"workflow": wf, "task_id": task_id}


@router.post(
    "/teams/{team_id}/tasks/{task_id}/workflow/run-claude",
    summary="Start Claude Code for the current active step",
)
async def run_claude_for_task(team_id: str, task_id: str) -> Dict[str, Any]:
    """Manually start a Claude Code session for the current active step."""
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    wf = task.metadata.get("workflow", [])
    # Find any active step
    active_step = None
    for s in wf:
        if s.get("status") == "active":
            active_step = s
            break
    if not active_step:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No active step")
    if active_step.get("session_id"):
        return {"session_id": active_step["session_id"], "status": "already_running"}

    import uuid as _uuid
    sr = _sr()
    skill = sr.get_by_slug("code_implementation")
    cfg = dict(skill.config or {}) if skill else {}
    agent = _tm().get_agent(team_id, active_step.get("agent_id", ""))
    if not agent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Agent not found for this step")

    sid = str(_uuid.uuid4())[:12]
    step_prompt = _build_step_prompt(task, active_step, wf)
    _start_claude_session(sid, step_prompt, cfg, agent, task_id)
    active_step["session_id"] = sid
    task.metadata["workflow"] = wf
    # Ensure harness monitor is running
    _start_harness_monitor(task_id, team_id)
    return {"session_id": sid, "status": "started"}


@router.post(
    "/teams/{team_id}/tasks/{task_id}/workflow/resume",
    summary="Resume a blocked task after Token Factory becomes ready",
)
async def resume_blocked_task(team_id: str, task_id: str) -> Dict[str, Any]:
    """Resume a task pipeline that was blocked due to Token Factory unavailability.

    Re-checks Token Factory, then starts the first pending/blocked step.
    """
    _get_team_or_404(team_id)
    task = _te().get_task(task_id)
    if task is None or task.team_id != team_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Token Factory preflight
    from token_factory import TokenFactory as _TF
    tf = _TF.instance()
    tf_status = await tf.ensure_ready()
    if not tf_status.get("ready", False):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token Factory (LLM 推理后端) 仍不可用，请先确保 Ollama 或 LLM 端点已启动。"
        )

    wf = task.metadata.get("workflow", [])
    if not wf:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No workflow")

    # Find first pending or blocked step
    resume_step = None
    for s in wf:
        if s.get("status") in ("pending", "active") or s.get("_blocked_reason"):
            resume_step = s
            break
    if not resume_step:
        return {"status": "all_done", "task_id": task_id}

    resume_step["status"] = "active"
    resume_step.pop("_blocked_reason", None)

    # Clear token factory error
    task.metadata.pop("token_factory_error", None)

    import uuid as _uuid
    sr = _sr()
    skill = sr.get_by_slug("code_implementation")
    cfg = dict(skill.config or {}) if skill else {}
    agent = _tm().get_agent(team_id, resume_step.get("agent_id", ""))
    if agent:
        sid = str(_uuid.uuid4())[:12]
        step_prompt = _build_step_prompt(task, resume_step, wf)
        _harness_log.info("[Resume] Resuming task %s at step '%s' (session %s)",
                          task_id, resume_step["key"], sid)
        _start_claude_session(sid, step_prompt, cfg, agent, task_id)
        resume_step["session_id"] = sid
    task.metadata["workflow"] = wf

    # Ensure running state
    if task.status.value == "pending":
        await _te().start_task(task_id)
    _start_harness_monitor(task_id, team_id)

    _write_handoff(task_id, "pipeline_resumed", {
        "step": resume_step["key"],
        "agent": resume_step.get("agent_id", ""),
        "reason": "Token Factory now available, pipeline resumed",
    })

    return {"status": "resumed", "step": resume_step["key"], "session_id": resume_step.get("session_id")}


class ExecuteSkillRequest(BaseModel):
    """Execute a skill on a task, optionally with a specific executor."""
    task_id: str = ""
    prompt: str = ""
    config_overrides: Dict[str, Any] = Field(default_factory=dict)


# ── Claude Code streaming session store ──
import subprocess
import threading
import time as _time
import os as _os
import logging as _logging
from collections import deque

_harness_log = _logging.getLogger("workflow_harness")
# Ensure harness messages reach stdout (uvicorn captures root logger)
if not _harness_log.handlers:
    _h = _logging.StreamHandler()
    _h.setFormatter(_logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    _harness_log.addHandler(_h)
    _harness_log.setLevel(_logging.INFO)
    _harness_log.propagate = False

_claude_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> {proc, lines, status, ...}

# ── Harness config ──
_HARNESS_POLL_SEC = 5        # Check session status every N seconds
_HARNESS_MAX_RETRIES = 2     # Retry failed steps up to N times
_HARNESS_RETRY_DELAY = 3     # Seconds between retries
_HARNESS_STALL_SEC = 300     # Mark stalled if no output for N seconds (large models need time)
_HARNESS_AUTO_ADVANCE = True # Auto-advance on step completion
_PIPELINE_MAX_REWINDS = 2    # Max times to rewind develop→test→deploy with QA feedback
_SESSION_GC_TTL_SEC = 1800   # Remove completed sessions after 30 min

# ── Pipeline event bus (per-task SSE subscribers) ──
import collections as _collections
_pipeline_events: Dict[str, list] = {}  # task_id -> list of event dicts
_pipeline_subscribers: Dict[str, list] = {}  # task_id -> list of asyncio.Queue


def _emit_pipeline_event(task_id: str, event_type: str, data: Dict[str, Any]) -> None:
    """Push an event to all SSE subscribers of a task and persist it."""
    evt = {"type": event_type, "ts": _time.time(), **data}
    _pipeline_events.setdefault(task_id, []).append(evt)
    # Keep last 200 events per task
    if len(_pipeline_events[task_id]) > 200:
        _pipeline_events[task_id] = _pipeline_events[task_id][-200:]
    try:
        task = _te().get_task(task_id)
    except Exception:
        task = None
    if task is not None:
        _append_task_trace_event(task, event_type, data)
    # Push to SSE subscribers
    for q in _pipeline_subscribers.get(task_id, []):
        try:
            q.put_nowait(evt)
        except Exception:
            pass


def _gc_sessions() -> int:
    """Remove completed/failed sessions older than _SESSION_GC_TTL_SEC. Returns count removed."""
    now = _time.time()
    to_remove = []
    for sid, s in _claude_sessions.items():
        if s.get("status") in ("completed", "failed", "stopped"):
            age = now - s.get("started_at", now)
            if age > _SESSION_GC_TTL_SEC:
                to_remove.append(sid)
    for sid in to_remove:
        _claude_sessions.pop(sid, None)
    if to_remove:
        _harness_log.info(f"[GC] Cleaned up {len(to_remove)} expired sessions")
    return len(to_remove)


def _rewind_pipeline_to_develop(task, wf: list, qa_reason: str, qa_report: str) -> bool:
    """Rewind workflow back to the develop step with structured QA feedback.

    Resets develop/test/deploy steps to 'pending', stores feedback in task.metadata,
    so the next harness tick will re-run develop with the QA report visible in its prompt.

    Enhanced: extracts structured failure data (file paths, line numbers, error types)
    from the QA report so the developer gets actionable fix instructions.

    Returns True if rewind succeeded, False if rewind cap exhausted.
    """
    md = task.metadata or {}
    rewind_count = int(md.get("pipeline_rewinds", 0))
    if rewind_count >= _PIPELINE_MAX_REWINDS:
        _harness_log.warning(
            f"[Harness] Rewind cap reached ({rewind_count}/{_PIPELINE_MAX_REWINDS}) "
            f"for task {task.task_id} — giving up"
        )
        # G7 fix: explicitly fail the task so it doesn't stay "running" forever
        _emit_pipeline_event(task.task_id, "pipeline_failed", {
            "reason": f"QA rewind cap exhausted ({_PIPELINE_MAX_REWINDS}): {qa_reason}",
        })
        for s in wf:
            if s.get("status") in ("active", "pending"):
                s["status"] = "failed"
                s["error"] = f"pipeline halted: rewind cap ({_PIPELINE_MAX_REWINDS}) exhausted"
        task.metadata["workflow"] = wf
        task.metadata["pipeline_failed_reason"] = qa_reason
        try:
            task.status = task.status.__class__("failed")
        except Exception:
            pass
        return False

    rewind_count += 1

    # ── Extract structured failure data from QA report ──
    structured_failures = []
    if qa_report:
        import re as _re_rw
        # Parse file-specific errors: patterns like "src/backend/foo.py: ImportError ..."
        file_error_re = _re_rw.compile(
            r"(?:❌|FAIL|BLOCKER|失败|错误)\s*[：:]*\s*"
            r"(?:`?([^\s`]+\.\w{1,6})`?)"
            r"(?:\s*(?:L|line|行)\s*(\d+))?"
            r"[：:\s]+(.+?)(?:\n|$)",
            _re_rw.MULTILINE | _re_rw.IGNORECASE,
        )
        for m in file_error_re.finditer(qa_report):
            structured_failures.append({
                "file": m.group(1),
                "line": int(m.group(2)) if m.group(2) else None,
                "error": m.group(3).strip()[:300],
            })

        # Parse pytest-style failures: "FAILED tests/unit/test_foo.py::test_bar - reason"
        pytest_fail_re = _re_rw.compile(
            r"FAILED\s+([\w/._]+)::(\w+)\s*[-–]\s*(.+?)(?:\n|$)",
            _re_rw.MULTILINE,
        )
        for m in pytest_fail_re.finditer(qa_report):
            structured_failures.append({
                "file": m.group(1),
                "test": m.group(2),
                "error": m.group(3).strip()[:300],
            })

        # Parse SyntaxError / ImportError lines
        syntax_re = _re_rw.compile(
            r"(SyntaxError|ImportError|ModuleNotFoundError|NameError|AttributeError)"
            r"[：:\s]+(.+?)(?:\n|$)",
            _re_rw.MULTILINE,
        )
        for m in syntax_re.finditer(qa_report):
            err = {"error_type": m.group(1), "detail": m.group(2).strip()[:300]}
            # Avoid duplicates
            if not any(sf.get("error", "").startswith(m.group(1)) for sf in structured_failures):
                structured_failures.append(err)

    md["pipeline_rewinds"] = rewind_count
    md["qa_feedback"] = {
        "iteration": rewind_count,
        "reason": qa_reason,
        "report": qa_report[:5000] if qa_report else "",
        "structured_failures": structured_failures[:15],
        "at": _time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Also try to include the test step's structured summary
    test_step = next((s for s in wf if s.get("key") == "test"), None)
    if test_step and test_step.get("_summary"):
        ts = test_step["_summary"]
        md["qa_feedback"]["verdict"] = ts.get("verdict", "FAIL")
        md["qa_feedback"]["qa_checklist"] = ts.get("checklist", [])

    # Reset develop / test / deploy steps so harness will re-execute them
    rewindable = {"develop", "test", "deploy"}
    for s in wf:
        if s.get("key") in rewindable:
            s["status"] = "pending"
            s["session_id"] = None
            s["_retries"] = 0
            s["artifact"] = ""
            s.pop("error", None)
            s.pop("deploy_blocked", None)
            s.pop("deploy_result", None)
            s.pop("files_applied", None)
            s.pop("smoke", None)
            s.pop("deliverable_count", None)
            s.pop("deliverable_paths", None)
            s.pop("_summary", None)

    # Re-activate develop step
    for s in wf:
        if s.get("key") == "develop":
            s["status"] = "active"
            break

    task.metadata = md
    task.metadata["workflow"] = wf
    _harness_log.info(
        f"[Harness] 🔁 Pipeline rewound to develop (iter {rewind_count}/{_PIPELINE_MAX_REWINDS}) "
        f"for task {task.task_id}: {qa_reason} "
        f"({len(structured_failures)} structured failure(s))"
    )
    _emit_pipeline_event(task.task_id, "pipeline_rewind", {
        "iteration": rewind_count,
        "max": _PIPELINE_MAX_REWINDS,
        "reason": qa_reason[:200],
        "failures": len(structured_failures),
    })
    return True




# ── Workflow harness: monitors sessions and auto-advances steps ──
_harness_threads: Dict[str, threading.Thread] = {}  # task_id -> monitor thread


def _harness_monitor(task_id: str, team_id: str) -> None:
    """Background thread that monitors a task's active step and auto-advances on completion.
    Inspired by Claude Code's stall watchdog and task notification flow."""
    _harness_log.info(f"[Harness] Monitoring task {task_id}")
    _gc_counter = 0
    _emit_pipeline_event(task_id, "pipeline_started", {"team_id": team_id})
    while True:
        _time.sleep(_HARNESS_POLL_SEC)
        _gc_counter += 1
        if _gc_counter % 50 == 0:
            _gc_sessions()
        try:
            engine = _te()
            task = engine.get_task(task_id)
            if task is None:
                _harness_log.info(f"[Harness] Task {task_id} not found, stopping monitor")
                break

            # Check if task is terminal
            if task.status.value in ("completed", "failed", "cancelled"):
                _harness_log.info(f"[Harness] Task {task_id} is {task.status.value}, stopping monitor")
                break

            wf = task.metadata.get("workflow", [])
            if not wf:
                break

            # Find active step
            active_step = None
            for s in wf:
                if s.get("status") == "active":
                    active_step = s
                    break

            if not active_step:
                # Check if all done (completed, failed, or skipped — no pending/active left)
                if all(s["status"] in ("completed", "skipped", "failed") for s in wf):
                    _harness_log.info(f"[Harness] All steps done for task {task_id}")
                    # Trigger pipeline completion
                    completed_count = sum(1 for s in wf if s["status"] == "completed")
                    failed_count = sum(1 for s in wf if s["status"] == "failed")
                    task.metadata["workflow"] = wf
                    _write_handoff(task_id, "pipeline_complete", {
                        "total_steps": len(wf),
                        "completed": completed_count,
                        "failed": failed_count,
                        "steps": [{"key": s["key"], "status": s["status"]} for s in wf],
                    })
                    _emit_pipeline_event(task_id, "pipeline_complete", {
                        "completed": completed_count, "failed": failed_count,
                        "steps": [{"key": s["key"], "status": s["status"]} for s in wf],
                    })
                    _harness_log.info(
                        f"[Harness] Pipeline complete for task {task_id}: "
                        f"{completed_count}/{len(wf)} succeeded, {failed_count} failed"
                    )
                    try:
                        import http.client
                        hconn = http.client.HTTPConnection("127.0.0.1", 8080, timeout=10)
                        hconn.request("POST",
                            f"/api/v1/agent-config/teams/{team_id}/tasks/{task_id}/complete")
                        hresp = hconn.getresponse()
                        hresp.read()
                        hconn.close()
                        _harness_log.info(f"[Harness] Task {task_id} auto-completed via HTTP ({hresp.status})")
                    except Exception as ex:
                        _harness_log.warning(f"[Harness] Could not auto-complete task: {ex}")
                        task.status = task.status.__class__("completed")
                    break  # All done → exit harness loop
                else:
                    # No active step but pending steps remain → promote the first pending one.
                    # This recovers from cases where a step's status got reset (rewind / race)
                    # but no follow-up activation happened.
                    pending = [s for s in wf if s.get("status") == "pending"]
                    if pending:
                        promoted = pending[0]
                        promoted["status"] = "active"
                        promoted["_active_since"] = _time.time()
                        promoted["session_id"] = None
                        task.metadata["workflow"] = wf
                        _harness_log.warning(
                            f"[Harness] No active step but {len(pending)} pending — "
                            f"auto-promoting '{promoted.get('key')}' to active"
                        )
                    continue  # next poll cycle will pick it up

            sid = active_step.get("session_id")
            if not sid:
                # Step is active but no session was ever started
                # Check how long it's been waiting
                wait_start = active_step.get("_active_since", 0)
                if not wait_start:
                    active_step["_active_since"] = _time.time()
                    continue
                elif _time.time() - wait_start > 30:
                    # Been waiting 30s with no session — try to start one, or skip
                    _harness_log.warning(
                        "[Harness] Step %s has no session after 30s — attempting to start",
                        active_step["key"])
                    aid = active_step.get("agent_id")
                    if aid:
                        try:
                            import uuid as _uuid
                            tm = _tm()
                            agent = tm.get_agent(team_id, aid)
                            if agent:
                                new_sid = str(_uuid.uuid4())[:12]
                                sr = _sr()
                                skill = sr.get_by_slug("code_implementation")
                                cfg = dict(skill.config or {}) if skill else {}
                                step_prompt = _build_step_prompt(task, active_step, wf)
                                _start_claude_session(new_sid, step_prompt, cfg, agent, task_id)
                                active_step["session_id"] = new_sid
                                task.metadata["workflow"] = wf
                                _harness_log.info("[Harness] Late-started session %s for step %s",
                                                  new_sid, active_step["key"])
                            else:
                                _harness_log.warning("[Harness] Agent %s not found — skipping step %s",
                                                     aid, active_step["key"])
                                active_step["status"] = "failed"
                                active_step["error"] = f"Agent {aid} not found"
                                task.metadata["workflow"] = wf
                        except Exception as ex:
                            _harness_log.exception(
                                "[Harness] Failed to late-start step %s: %s",
                                active_step["key"], ex,
                            )
                            active_step["status"] = "failed"
                            active_step["error"] = f"late-start failed: {ex}"
                            task.metadata["workflow"] = wf
                    else:
                        _harness_log.warning("[Harness] Step %s has no agent_id — skipping",
                                             active_step["key"])
                        active_step["status"] = "skipped"
                        task.metadata["workflow"] = wf
                continue

            session = _claude_sessions.get(sid)
            if not session:
                continue

            # Check session status
            sess_status = session.get("status", "running")

            if sess_status == "running":
                # Stall detection: check if output stopped growing
                # Skip stall detection if Ollama is loading the model (waiting for first token)
                if session.get("_ollama_waiting"):
                    # Keep session alive — Ollama model loading can take minutes
                    session["_last_activity"] = _time.time()
                    continue

                last_activity = session.get("_last_activity", session.get("started_at", 0))
                now = _time.time()
                lines = session.get("lines")
                current_count = len(lines) if lines else 0
                prev_count = session.get("_prev_line_count", 0)

                if current_count > prev_count:
                    session["_last_activity"] = now
                    session["_prev_line_count"] = current_count
                elif now - last_activity > _HARNESS_STALL_SEC:
                    _harness_log.warning(f"[Harness] Session {sid} stalled ({_HARNESS_STALL_SEC}s no output)")
                    session["lines"].append(f"\n⚠️ 会话停滞 ({_HARNESS_STALL_SEC}s 无输出)\n")
                    session["status"] = "failed"
                    session["exit_code"] = -1
                    sess_status = "failed"  # Fall through to retry/advance

                if sess_status == "running":
                    continue

            # Session completed or failed — handle it
            retry_count = active_step.get("_retries", 0)

            if sess_status == "failed" and retry_count < _HARNESS_MAX_RETRIES:
                # RETRY: restart the session
                active_step["_retries"] = retry_count + 1
                _harness_log.info(
                    f"[Harness] Retry {retry_count + 1}/{_HARNESS_MAX_RETRIES} "
                    f"for step {active_step['key']} of task {task_id}"
                )
                session["lines"].append(
                    f"\n🔄 自动重试 ({retry_count + 1}/{_HARNESS_MAX_RETRIES})...\n\n"
                )
                _time.sleep(_HARNESS_RETRY_DELAY)

                # Create new session for retry
                import uuid as _uuid
                new_sid = str(_uuid.uuid4())[:12]
                sr = _sr()
                skill = sr.get_by_slug("code_implementation")
                cfg = dict(skill.config or {}) if skill else {}
                tm = _tm()
                agent = tm.get_agent(team_id, active_step["agent_id"]) if active_step.get("agent_id") else None
                if agent:
                    step_prompt = _build_step_prompt(task, active_step, wf)
                    _start_claude_session(new_sid, step_prompt, cfg, agent, task_id)
                    active_step["session_id"] = new_sid
                    task.metadata["workflow"] = wf
                    _harness_log.info(f"[Harness] Retry started with session {new_sid}")
                continue

            if sess_status in ("completed", "failed"):
                # Validate that session produced real output
                has_content = _validate_session_output(session)

                # Collect artifact (legacy: docs/workflow_artifacts/)
                _collect_step_artifact(task, active_step)

                # ── Save step output to pipeline workspace (shared) ──
                step_key = active_step.get("key", "")
                if has_content:
                    try:
                        art_path = active_step.get("artifact", "")
                        art_text = ""
                        if art_path and _os.path.isfile(art_path):
                            with open(art_path, "r", encoding="utf-8") as _af:
                                art_text = _af.read()
                        else:
                            art_text = "".join(list(session.get("lines", [])))

                        # Extract code deliverables for code-producing steps
                        deliverables = []
                        if step_key in _CODE_STEPS:
                            deliverables = _extract_code_deliverables(art_text)

                        # Save to pipeline workspace
                        _save_step_to_pipeline(
                            task_id, step_key, art_text, deliverables or None,
                        )

                        # ── Persist tool-call trace if this step ran in tool-loop mode ──
                        if session.get("tool_loop_log") is not None:
                            try:
                                pdir_tt = _pipeline_dir(task_id)
                                _os.makedirs(pdir_tt, exist_ok=True)
                                idx_tt = _STEP_INDEX.get(step_key, "00")
                                trace_path = _os.path.join(
                                    pdir_tt, f"{idx_tt}_{step_key}_tool_trace.json",
                                )
                                import json as _json_tt
                                with open(trace_path, "w", encoding="utf-8") as _tf:
                                    _json_tt.dump({
                                        "task_id": task_id, "step": step_key,
                                        "role": active_step.get("agent_role", ""),
                                        "ok": bool(session.get("loop_ok")),
                                        "iterations": session.get("loop_iterations", 0),
                                        "files_changed": session.get("files_changed", []),
                                        "summary": session.get("loop_summary", ""),
                                        "log": session.get("tool_loop_log", []),
                                    }, _tf, ensure_ascii=False, indent=2)
                                _harness_log.info(
                                    f"[Harness] Tool-trace persisted: {trace_path}"
                                )
                            except Exception as _terr:
                                _harness_log.debug(f"[Harness] tool-trace save skipped: {_terr}")

                        if deliverables:
                            active_step["deliverable_count"] = len(deliverables)
                            active_step["deliverable_paths"] = [d["path"] for d in deliverables]
                            _harness_log.info(
                                f"[Harness] Step {step_key}: {len(deliverables)} code deliverables saved"
                            )

                            # Per-agent workspace isolation: also drop a copy in
                            # the agent's private deliverables dir for traceability
                            try:
                                agent_id = active_step.get("agent_id") or active_step.get("assignee") or ""
                                if team_id and agent_id:
                                    _save_deliverables_to_workspace(
                                        task_id, team_id, agent_id, deliverables,
                                    )
                            except Exception as ws_err:
                                _harness_log.debug(f"[Harness] per-agent ws save skipped: {ws_err}")

                            # Pre-deploy smoke check (so QA step sees real signal)
                            if step_key == "develop":
                                try:
                                    smoke = _smoke_check_pipeline_code(task_id, step_key)
                                    active_step["smoke"] = smoke
                                    n_fail = sum(1 for s in smoke if not s.get("syntax_ok"))
                                    if n_fail:
                                        session["lines"].append(
                                            f"\n🔥 冒烟测试: {n_fail}/{len(smoke)} 文件存在语法/导入问题 (详见 apply_report.json)\n"
                                        )
                                    _harness_log.info(
                                        f"[Harness] Smoke: {len(smoke)-n_fail}/{len(smoke)} OK"
                                    )
                                except Exception as smoke_err:
                                    _harness_log.warning(f"[Harness] smoke check failed: {smoke_err}")
                        else:
                            # Explicitly mark 0 deliverables so deploy step can detect no-op
                            active_step["deliverable_count"] = 0
                    except Exception as pipe_err:
                        _harness_log.error(f"[Harness] Pipeline save error: {pipe_err}")

                # ── Extract structured summary for downstream agents ──
                if has_content and step_key:
                    try:
                        art_path_s = active_step.get("artifact", "")
                        summary_text = ""
                        if art_path_s and _os.path.isfile(art_path_s):
                            with open(art_path_s, "r", encoding="utf-8") as _sf:
                                summary_text = _sf.read()
                        else:
                            summary_text = "".join(list(session.get("lines", [])))
                        _step_deliverables = active_step.get("deliverable_paths", [])
                        _step_smoke = active_step.get("smoke")
                        _step_summary = _extract_step_summary(
                            task_id, step_key, summary_text,
                            deliverables=[{"path": p} for p in _step_deliverables] if _step_deliverables else None,
                            smoke_results=_step_smoke,
                        )
                        active_step["_summary"] = _step_summary
                        _harness_log.info(
                            f"[Harness] Step summary extracted for {step_key}: "
                            f"{len(_step_summary.get('decisions', []))} decisions, "
                            f"{len(_step_summary.get('files_changed', []))} files"
                        )
                    except Exception as sum_err:
                        _harness_log.debug(f"[Harness] Summary extraction skipped: {sum_err}")

                # ── Deploy step: apply code from developer's pipeline output ──
                if step_key == "deploy":
                    try:
                        # ── Check if developer produced zero changes (no-op task) ──
                        dev_step_obj = next((s for s in wf if s.get("key") == "develop"), None)
                        dev_deliverables = dev_step_obj.get("deliverable_count", 0) if dev_step_obj else 0
                        dev_no_op = (dev_deliverables == 0 and dev_step_obj
                                     and dev_step_obj.get("status") == "completed")

                        # ── QA Gate: refuse to apply if test step verdict is FAIL ──
                        gate_blocked = False
                        gate_reason = ""
                        try:
                            # Check the test step's status in workflow first
                            test_step_obj = next((s for s in wf if s.get("key") == "test"), None)
                            if test_step_obj and test_step_obj.get("status") == "failed":
                                gate_blocked = True
                                gate_reason = (
                                    f"Test 步骤失败 ({test_step_obj.get('error','no session/output')})"
                                )

                            pdir_g = _pipeline_dir(task_id)
                            test_idx = _STEP_INDEX.get("test", "05")
                            test_md = _os.path.join(pdir_g, f"{test_idx}_test.md")
                            if _os.path.isfile(test_md):
                                test_text = open(test_md, "r", encoding="utf-8").read()
                                # Block if QA explicitly said FAIL or BLOCKER
                                tl = test_text.lower()
                                # Look for "## 验证结论" then "FAIL"
                                import re as _re_g
                                verdict_m = _re_g.search(
                                    r"##\s*验证结论[\s\S]{0,200}?\b(fail|失败|blocked)\b",
                                    test_text, _re_g.IGNORECASE,
                                )
                                blocker_m = _re_g.search(r"\bblocker\b", test_text, _re_g.IGNORECASE)
                                if verdict_m and not gate_blocked:
                                    gate_blocked = True
                                    gate_reason = "QA 验证结论 = FAIL"
                                elif blocker_m and "blocker" not in tl.split("##")[0] and not gate_blocked:
                                    # only treat BLOCKER as gate if it's in body (not echo of the prompt)
                                    gate_blocked = True
                                    gate_reason = "QA 报告含 BLOCKER 级别问题"
                        except Exception as gerr:
                            _harness_log.debug(f"[Harness] QA gate check skipped: {gerr}")

                        if gate_blocked:
                            active_step["files_applied"] = 0
                            active_step["deploy_blocked"] = gate_reason
                            session["lines"].append(
                                f"\n🛑 部署已被 QA 阻断: {gate_reason}\n"
                            )
                            _harness_log.warning(
                                f"[Harness] Deploy BLOCKED by QA gate for task {task_id}: {gate_reason}"
                            )

                            # ── Phase 4: try to rewind to develop with QA feedback ──
                            qa_report_text = ""
                            try:
                                pdir_g2 = _pipeline_dir(task_id)
                                test_idx2 = _STEP_INDEX.get("test", "05")
                                test_md2 = _os.path.join(pdir_g2, f"{test_idx2}_test.md")
                                if _os.path.isfile(test_md2):
                                    qa_report_text = open(test_md2, "r", encoding="utf-8").read()
                            except Exception:
                                pass

                            if _rewind_pipeline_to_develop(task, wf, gate_reason, qa_report_text):
                                session["lines"].append(
                                    f"\n🔁 自动回滚到 develop 步骤，附带 QA 反馈，重新开发...\n"
                                )
                                # Skip rest of deploy handling — pipeline is now back at develop
                                continue
                            else:
                                session["lines"].append(
                                    f"   重试上限已达 ({_PIPELINE_MAX_REWINDS})，停止管线。\n"
                                    f"   代码保留在管线工作区，不会写入项目代码库。\n"
                                )
                                # Mark as failed so workflow stops cleanly
                                sess_status = "failed"
                                session["status"] = "failed"
                                session["error"] = f"QA gate: {gate_reason}"
                        else:
                            # Apply developer step's code to project
                            dev_result = _apply_code_from_pipeline(task_id, "develop")
                            dev_applied = len(dev_result.get("applied", []))

                            # Also apply deployer's own code (blue-green new files)
                            deploy_result = _apply_code_from_pipeline(task_id, "deploy")
                            deploy_applied = len(deploy_result.get("applied", []))

                            total_applied = dev_applied + deploy_applied
                            total_skipped = (len(dev_result.get("skipped", []))
                                            + len(deploy_result.get("skipped", [])))
                            total_failed = (len(dev_result.get("failed", []))
                                           + len(deploy_result.get("failed", [])))

                            active_step["files_applied"] = total_applied
                            active_step["deploy_result"] = {
                                "developer": dev_result,
                                "deployer": deploy_result,
                            }

                            # ── No-op deploy: developer found no changes needed ──
                            if dev_no_op and total_applied == 0:
                                active_step["deploy_no_op"] = True
                                session["lines"].append(
                                    "\n✅ 开发者判定无需代码变更，部署步骤跳过 (no-op)\n"
                                )
                                _harness_log.info(
                                    f"[Harness] Deploy no-op: developer had 0 deliverables, "
                                    f"treating as successful no-op deploy"
                                )
                            else:
                                session["lines"].append(
                                    f"\n📦 部署结果: {total_applied} 文件已应用 "
                                    f"(开发: {dev_applied}, 蓝绿: {deploy_applied}), "
                                    f"{total_skipped} 跳过, {total_failed} 失败\n"
                                )
                            _harness_log.info(
                                f"[Harness] Deploy: {total_applied} applied "
                                f"(dev={dev_applied}, deploy={deploy_applied})"
                            )
                    except Exception as dpex:
                        _harness_log.error(f"[Harness] Deploy apply error: {dpex}")

                task.metadata["workflow"] = wf

                if sess_status == "completed" and not has_content:
                    # No-op deploy is still valid — developer found nothing to change
                    is_no_op_deploy = (step_key == "deploy"
                                       and active_step.get("deploy_no_op"))
                    if is_no_op_deploy:
                        _harness_log.info(
                            f"[Harness] Step {active_step['key']} is a no-op deploy — "
                            f"treating as completed despite minimal output"
                        )
                    else:
                        # Session "completed" but produced no real output — treat as failed
                        _harness_log.warning(
                            f"[Harness] Step {active_step['key']} session completed but has NO meaningful output — "
                            f"treating as failed (LLM may have returned empty/error response)"
                        )
                        sess_status = "failed"
                        session["status"] = "failed"

                if sess_status == "failed":
                    active_step["status"] = "failed"
                    _harness_log.warning(
                        f"[Harness] Step {active_step['key']} failed after "
                        f"{retry_count + 1} attempts, skipping to next"
                    )
                    # Write failure handoff
                    _write_handoff(task_id, f"{active_step['key']}_FAILED", {
                        "step": active_step["key"],
                        "retries": retry_count + 1,
                        "error": session.get("error", "unknown"),
                        "output_lines": len(list(session.get("lines", []))),
                    }, from_agent=active_step.get("agent_id", ""),
                       to_agent="(next step)")
                    _emit_pipeline_event(task_id, "step_failed", {
                        "step": active_step["key"],
                        "label": active_step.get("label", ""),
                        "error": str(session.get("error", "unknown"))[:200],
                    })

                if sess_status == "completed":
                    active_step["status"] = "completed"
                    _emit_pipeline_event(task_id, "step_completed", {
                        "step": active_step["key"],
                        "label": active_step.get("label", ""),
                    })
                    # Build structured handoff payload with summary data
                    _handoff_payload = {
                        "step": active_step["key"],
                        "label": active_step.get("label", ""),
                        "agent_role": active_step.get("agent_role", ""),
                        "status": "completed",
                        "artifact": active_step.get("artifact", ""),
                    }
                    # Include structured summary if available
                    _step_sum = active_step.get("_summary", {})
                    if _step_sum:
                        _handoff_payload["decisions"] = _step_sum.get("decisions", [])
                        _handoff_payload["files_changed"] = _step_sum.get("files_changed", [])
                        # develop→test: include verification checklist
                        if active_step["key"] == "develop":
                            _handoff_payload["verify_checklist"] = _step_sum.get("verify_checklist", [])
                            _handoff_payload["smoke"] = _step_sum.get("smoke", {})
                        # test→deploy: include verdict and blockers
                        elif active_step["key"] == "test":
                            _handoff_payload["verdict"] = _step_sum.get("verdict", "UNKNOWN")
                            _handoff_payload["checklist"] = _step_sum.get("checklist", [])
                    else:
                        _handoff_payload["output_summary"] = "".join(
                            list(session.get("lines", []))[-20:]
                        )[:2000]
                    _write_handoff(task_id, active_step["key"], _handoff_payload,
                        from_agent=active_step.get("agent_id", ""),
                       to_agent=wf[active_step["index"] + 1]["agent_id"] if active_step["index"] + 1 < len(wf) else "(end)")

                # Auto-advance to next step
                active_idx = active_step["index"]
                if active_idx + 1 < len(wf):
                    next_step = wf[active_idx + 1]
                    next_step["status"] = "active"

                    # Token Factory check before starting next Claude session
                    # If direct DeepSeek API is available, skip TF entirely
                    _ds_key, _, _ = _get_deepseek_credentials()
                    if _ds_key:
                        tf_ok = True
                        _harness_log.info("[Harness] Direct DeepSeek API available — skipping Token Factory check")
                    else:
                        tf_ok = False
                        try:
                            import http.client
                            hconn = http.client.HTTPConnection("127.0.0.1", 8080, timeout=10)
                            hconn.request("GET", "/api/v1/token-factory/health")
                            hresp = hconn.getresponse()
                            import json as _jj
                            hdata = _jj.loads(hresp.read().decode())
                            hconn.close()
                            tf_ok = hdata.get("ready", False)
                        except Exception as e:
                            _harness_log.warning(f"[Harness] Token Factory check failed: {e}")
                            tf_ok = True  # Optimistic fallback
                            _harness_log.info("[Harness] Proceeding optimistically")

                    if not tf_ok:
                        _harness_log.warning(
                            f"[Harness] Token Factory NOT ready for step "
                            f"{next_step['key']} — will retry next poll cycle"
                        )
                        next_step["status"] = "pending"
                        next_step["_blocked_reason"] = "Token Factory not ready"
                        task.metadata["workflow"] = wf
                        continue  # Retry on next poll instead of killing the monitor

                    # Start Claude for next step
                    if next_step.get("agent_id"):
                        import uuid as _uuid
                        sr = _sr()
                        skill = sr.get_by_slug("code_implementation")
                        cfg = dict(skill.config or {}) if skill else {}
                        tm = _tm()
                        agent = tm.get_agent(team_id, next_step["agent_id"])
                        if agent:
                            new_sid = str(_uuid.uuid4())[:12]
                            try:
                                step_prompt = _build_step_prompt(task, next_step, wf)
                                _harness_log.info(
                                    f"[Harness] Auto-advancing: step {active_step['key']} → "
                                    f"{next_step['key']} (agent: {agent.name}, session: {new_sid})"
                                )
                                _emit_pipeline_event(task_id, "step_started", {
                                    "step": next_step["key"],
                                    "label": next_step.get("label", ""),
                                    "agent": agent.name,
                                    "prev_step": active_step["key"],
                                })
                                _start_claude_session(new_sid, step_prompt, cfg, agent, task_id)
                                next_step["session_id"] = new_sid
                            except Exception as start_err:
                                _harness_log.exception(
                                    f"[Harness] Failed to start session for step "
                                    f"{next_step['key']}: {start_err}"
                                )
                                next_step["status"] = "failed"
                                next_step["error"] = f"session start failed: {start_err}"
                        else:
                            _harness_log.warning(
                                f"[Harness] Agent '{next_step['agent_id']}' not found in team "
                                f"'{team_id}' — skipping step {next_step['key']}"
                            )
                            next_step["status"] = "failed"
                            next_step["error"] = f"Agent {next_step['agent_id']} not found"
                    else:
                        _harness_log.warning(
                            f"[Harness] Step {next_step['key']} has no agent_id — skipping"
                        )
                        next_step["status"] = "skipped"

                    task.metadata["workflow"] = wf
                else:
                    # All steps done — validate before marking task complete
                    completed_count = sum(1 for s in wf if s["status"] == "completed")
                    failed_count = sum(1 for s in wf if s["status"] == "failed")
                    task.metadata["workflow"] = wf

                    # Write final summary handoff
                    _write_handoff(task_id, "pipeline_complete", {
                        "total_steps": len(wf),
                        "completed": completed_count,
                        "failed": failed_count,
                        "steps": [{
                            "key": s["key"],
                            "status": s["status"],
                            "artifact": s.get("artifact", ""),
                        } for s in wf],
                    })
                    _emit_pipeline_event(task_id, "pipeline_complete", {
                        "completed": completed_count, "failed": failed_count,
                        "steps": [{"key": s["key"], "status": s["status"]} for s in wf],
                    })

                    _harness_log.info(
                        f"[Harness] Pipeline complete for task {task_id}: "
                        f"{completed_count}/{len(wf)} succeeded, {failed_count} failed"
                    )
                    # Finalize the task with execution artifacts and a truthful terminal state.
                    try:
                        import asyncio
                        final_error = ""
                        if failed_count:
                            final_error = f"workflow_failed:{failed_count}_steps"

                        try:
                            loop = asyncio.get_running_loop()
                        except RuntimeError:
                            loop = None

                        if loop and loop.is_running():
                            future = asyncio.run_coroutine_threadsafe(
                                _finalize_task_terminal_state(task, error=final_error), loop
                            )
                            finalized = future.result(timeout=5)
                        else:
                            finalized = asyncio.run(
                                _finalize_task_terminal_state(task, error=final_error)
                            )

                        if finalized is not None:
                            _harness_log.info(
                                f"[Harness] Task {task_id} finalized as "
                                f"{finalized.status.value if hasattr(finalized.status, 'value') else finalized.status}"
                            )
                    except Exception as ex:
                        _harness_log.warning(f"[Harness] Could not finalize task: {ex}")
                    break

        except Exception as ex:
            _harness_log.exception(f"[Harness] Error monitoring task {task_id}: {ex}")
            continue

    # Cleanup
    _harness_threads.pop(task_id, None)
    _harness_log.info(f"[Harness] Monitor stopped for task {task_id}")


def _start_harness_monitor(task_id: str, team_id: str) -> None:
    """Start a harness monitor thread for a task (if not already running)."""
    if task_id in _harness_threads:
        return
    t = threading.Thread(target=_harness_monitor, args=(task_id, team_id), daemon=True)
    _harness_threads[task_id] = t
    t.start()

# ── Artifact directory for inter-step .md handoffs ──
_ARTIFACT_DIR = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "docs", "workflow_artifacts"
)
_os.makedirs(_ARTIFACT_DIR, exist_ok=True)

# ── Handoff directory for inter-agent communication ──
_HANDOFF_DIR = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "docs", "agent_handoffs"
)
_os.makedirs(_HANDOFF_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
# Pipeline Workspace — Shared directory for inter-agent deliverables
# ══════════════════════════════════════════════════════════════════
#
# Architecture: FULL-TEAM SHARED per pipeline run
#
#   storage/pipeline_runs/{task_id}/
#   ├── _context/                    # Pre-seeded project context
#   │   ├── file_tree.txt           # `find src/ -type f` listing
#   │   └── target_files/           # Actual file contents matching task
#   ├── 01_pm_decompose.md          # Step artifacts (numbered for order)
#   ├── 02_research.md
#   ├── ...
#   ├── 04_develop/
#   │   ├── summary.md              # LLM prose output
#   │   └── code/                   # Extracted code files
#   │       └── src/frontend/...    # Mirrors project tree
#   └── 06_deploy/
#       ├── summary.md
#       └── code/                   # Blue-green new files
#
# Why full-team shared (not upstream-only):
#   - Deployer needs Developer's code + PM's plan
#   - Tester needs Architecture spec + Developer code
#   - Simpler, fewer failure modes
#   - _context/ pre-seeds project knowledge for text-only LLMs

_PIPELINE_RUNS_DIR = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.dirname(_os.path.abspath(__file__))))),
    "storage", "pipeline_runs"
)
_os.makedirs(_PIPELINE_RUNS_DIR, exist_ok=True)

_TRACE_LOG_DIR = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.dirname(_os.path.abspath(__file__))))),
    "storage", "traces"
)
_os.makedirs(_TRACE_LOG_DIR, exist_ok=True)

_STEP_INDEX = {
    "pm_decompose": "01", "research": "02", "architecture": "03",
    "develop": "04", "test": "05", "deploy": "06", "document": "07",
}

# Steps whose output may contain code deliverables
_CODE_STEPS = frozenset({"develop", "deploy"})


def _pipeline_dir(task_id: str) -> str:
    """Return (and create) the shared pipeline workspace directory for a task."""
    safe_tid = task_id.replace("/", "_")[:60]
    d = _os.path.join(_PIPELINE_RUNS_DIR, safe_tid)
    _os.makedirs(d, exist_ok=True)
    return d


def _pipeline_context_dir(task_id: str) -> str:
    """Return _context/ subdir inside the pipeline workspace."""
    d = _os.path.join(_pipeline_dir(task_id), "_context")
    _os.makedirs(d, exist_ok=True)
    return d


def _global_trace_events_path() -> str:
    return _os.path.join(_TRACE_LOG_DIR, "trace_events.jsonl")


def _read_global_trace_events(
    *,
    event_type: str = "",
    team_id: str = "",
    source: str = "",
    since_ts: float = 0.0,
) -> List[Dict[str, Any]]:
    """Read the global trace event log with lightweight filtering."""
    trace_path = _global_trace_events_path()
    if not _os.path.isfile(trace_path):
        return []

    events: List[Dict[str, Any]] = []
    try:
        import json as _json

        with open(trace_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = _json.loads(line)
                except Exception:
                    continue
                if event_type and event.get("type") != event_type:
                    continue
                if team_id and event.get("team_id") != team_id:
                    continue
                trace_context = dict(event.get("trace_context") or {})
                if source and trace_context.get("source") != source:
                    continue
                if since_ts and float(event.get("ts") or 0.0) < float(since_ts):
                    continue
                events.append(event)
    except Exception:
        return []
    return events


def _seed_project_context(task_id: str, task_title: str, task_description: str) -> str:
    """Pre-seed the pipeline workspace with project context.

    Since DeepSeek text-only agents CANNOT read the filesystem, we proactively
    scan the project for files relevant to the task and include their contents.

    Returns the path to the context directory.
    """
    ctx_dir = _pipeline_context_dir(task_id)
    project_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.dirname(_os.path.abspath(__file__)))))

    # ── 1. Generate file tree ──
    tree_path = _os.path.join(ctx_dir, "file_tree.txt")
    if not _os.path.exists(tree_path):
        tree_lines = []
        for dirpath, dirnames, filenames in _os.walk(project_root):
            # Skip non-source directories
            rel_dir = _os.path.relpath(dirpath, project_root)
            skip_prefixes = ("venv", "node_modules", ".git", "__pycache__",
                             "storage", ".pytest_cache", "logs", "reports")
            if any(rel_dir == s or rel_dir.startswith(s + _os.sep) for s in skip_prefixes):
                dirnames.clear()
                continue
            for fn in sorted(filenames):
                if fn.startswith(".") or fn.endswith((".pyc", ".pyo")):
                    continue
                rel = _os.path.join(rel_dir, fn) if rel_dir != "." else fn
                tree_lines.append(rel)
        with open(tree_path, "w", encoding="utf-8") as f:
            f.write("\n".join(tree_lines[:5000]) + "\n")
        _harness_log.info("[Pipeline] File tree: %d entries → %s", len(tree_lines), tree_path)

    # ── 2. Search for task-relevant files ──
    target_dir = _os.path.join(ctx_dir, "target_files")
    _os.makedirs(target_dir, exist_ok=True)

    # Extract keywords from task title + description
    search_text = f"{task_title} {task_description or ''}"
    # Common keyword extraction (Chinese + English significant words)
    import re as _re
    # Chinese: extract meaningful 2+ char segments between punctuation
    cn_words = _re.findall(r'[\u4e00-\u9fff]{2,6}', search_text)
    # English: extract words 3+ chars
    en_words = _re.findall(r'[a-zA-Z][a-zA-Z0-9_-]{2,}', search_text)
    keywords = set(w.lower() for w in en_words if w.lower() not in {
        "the", "and", "for", "from", "with", "that", "this", "html", "page",
        "system", "build", "team", "task", "please", "file",
    })
    keywords.update(cn_words)

    # Also look for file path hints in the task text
    path_hints = _re.findall(r'[a-zA-Z0-9_/-]+\.\w{1,6}', search_text)
    for ph in path_hints:
        keywords.add(ph)

    # Chinese concept → filename mapping (common domain-specific translations)
    _CN_FILE_MAP = {
        "健康": ["health", "cms-health", "cms"],
        "设备": ["device", "cms", "equipment"],
        "推进": ["thruster", "propulsion", "tcs"],
        "导航": ["navigation", "nav"],
        "舵": ["rudder", "steering"],
        "数字孪生": ["digital-twin", "twin"],
        "驾驶台": ["bridge", "hmi", "openbridge"],
        "报警": ["alarm", "alert"],
        "机舱": ["engine", "intelligent-engine", "machinery"],
        "避碰": ["colreg", "collision"],
        "海图": ["chart", "map", "worldmonitor"],
        "货物": ["cargo"],
        "消防": ["fire"],
        "压载": ["ballast"],
        "通信": ["comm", "vdes"],
        "气象": ["weather", "meteo"],
        "状态": ["status", "health", "monitor"],
        "控制": ["control"],
    }
    for cn_kw in cn_words:
        for cn_key, en_vals in _CN_FILE_MAP.items():
            if cn_key in cn_kw:
                keywords.update(en_vals)

    _harness_log.info("[Pipeline] Context seeding keywords: %s", keywords)

    # Search source files for keyword matches
    _SEARCH_DIRS = ["src/frontend", "src/backend/channels", "src/backend"]
    _MAX_FILES = 10  # Don't overload the prompt
    _MAX_FILE_SIZE = 30_000  # chars per file
    _CONTENT_SCAN_SIZE = 15_000  # chars to scan for content matching

    matched_files: list = []
    for search_dir in _SEARCH_DIRS:
        abs_dir = _os.path.join(project_root, search_dir)
        if not _os.path.isdir(abs_dir):
            continue
        for dirpath, _, filenames in _os.walk(abs_dir):
            for fn in filenames:
                if not fn.endswith((".html", ".py", ".js", ".css", ".json", ".mjs")):
                    continue
                rel = _os.path.relpath(_os.path.join(dirpath, fn), project_root)
                abs_path = _os.path.join(dirpath, fn)

                # Score: how many keywords match the filename or path?
                score = 0
                lower_rel = rel.lower().replace("-", " ").replace("_", " ")
                lower_fn = fn.lower().replace("-", " ").replace("_", " ")
                for kw in keywords:
                    kw_lower = kw.lower().replace("-", " ").replace("_", " ")
                    if kw_lower in lower_rel or kw_lower in lower_fn:
                        score += 3  # Path match is strong signal
                # Also check file content for keyword matches
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                        head = f.read(_CONTENT_SCAN_SIZE)
                    for kw in keywords:
                        if kw in head or kw.lower() in head.lower():
                            score += 1
                except Exception:
                    pass

                if score > 0:
                    matched_files.append((score, rel, abs_path))

    # Sort by relevance, take top N
    matched_files.sort(key=lambda x: -x[0])
    seeded_files = []
    for score, rel, abs_path in matched_files[:_MAX_FILES]:
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(_MAX_FILE_SIZE)
            # Save to target_files/ preserving relative path
            dest = _os.path.join(target_dir, rel)
            _os.makedirs(_os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            seeded_files.append(rel)
            _harness_log.info("[Pipeline] Seeded: %s (score=%d, %d chars)", rel, score, len(content))
        except Exception as e:
            _harness_log.warning("[Pipeline] Failed to seed %s: %s", rel, e)

    # Write a manifest
    manifest_path = _os.path.join(ctx_dir, "_manifest.md")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(f"# Pipeline Context — {task_title}\n\n")
        f.write(f"Task ID: {task_id}\n")
        f.write(f"Keywords: {', '.join(sorted(keywords))}\n")
        f.write(f"Seeded files: {len(seeded_files)}\n\n")
        for sf in seeded_files:
            f.write(f"- `{sf}`\n")

    _harness_log.info("[Pipeline] Context seeded: %d files for task %s", len(seeded_files), task_id)
    return ctx_dir


def _get_pipeline_context_for_prompt(task_id: str) -> str:
    """Build a context string from the pipeline's _context/ dir for inclusion in prompts.

    Returns a formatted string with file tree + relevant file contents.
    Budget: ~60K chars max to leave room for task prompt + prior steps.
    """
    _MAX_CONTEXT_CHARS = 60_000
    _MAX_PER_FILE = 15_000

    ctx_dir = _pipeline_context_dir(task_id)
    parts = []
    total = 0

    # File tree (truncated)
    tree_path = _os.path.join(ctx_dir, "file_tree.txt")
    if _os.path.isfile(tree_path):
        with open(tree_path, "r", encoding="utf-8") as f:
            tree = f.read()
        lines = tree.strip().split("\n")
        # Filter to src/ only for relevance
        src_lines = [l for l in lines if l.startswith("src/")]
        if len(src_lines) > 150:
            tree = "\n".join(src_lines[:150]) + f"\n... (共 {len(src_lines)} 个 src/ 文件)\n"
        else:
            tree = "\n".join(src_lines)
        chunk = f"### 项目文件结构 (src/ 目录)\n```\n{tree}\n```\n"
        parts.append(chunk)
        total += len(chunk)

    # Target files
    target_dir = _os.path.join(ctx_dir, "target_files")
    if _os.path.isdir(target_dir):
        for dirpath, _, filenames in _os.walk(target_dir):
            if total >= _MAX_CONTEXT_CHARS:
                parts.append("(后续文件因 token 预算已省略)\n")
                break
            for fn in sorted(filenames):
                if total >= _MAX_CONTEXT_CHARS:
                    break
                abs_path = _os.path.join(dirpath, fn)
                rel = _os.path.relpath(abs_path, target_dir)
                try:
                    remaining = _MAX_CONTEXT_CHARS - total
                    read_limit = min(_MAX_PER_FILE, remaining - 200)
                    if read_limit < 500:
                        parts.append("(后续文件因 token 预算已省略)\n")
                        break
                    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read(read_limit)
                    ext = _os.path.splitext(fn)[1].lstrip(".")
                    chunk = f"### 文件: `{rel}`\n```{ext}\n{content}\n```\n"
                    parts.append(chunk)
                    total += len(chunk)
                except Exception:
                    pass

    if not parts:
        return ""
    return "## 📂 项目上下文 (系统自动预加载)\n\n" + "\n".join(parts) + "\n"


def _save_step_to_pipeline(task_id: str, step_key: str, content: str,
                            deliverables: list = None) -> str:
    """Save a step's output to the shared pipeline workspace.

    For regular steps: saves as NN_stepkey.md
    For code steps: also saves extracted code under NN_stepkey/code/

    Returns the path of the saved summary file.
    """
    pdir = _pipeline_dir(task_id)
    idx = _STEP_INDEX.get(step_key, "99")

    if step_key in _CODE_STEPS and deliverables:
        # Code step: create subdirectory with summary + code files
        step_dir = _os.path.join(pdir, f"{idx}_{step_key}")
        _os.makedirs(step_dir, exist_ok=True)

        summary_path = _os.path.join(step_dir, "summary.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Save extracted code files
        code_dir = _os.path.join(step_dir, "code")
        _os.makedirs(code_dir, exist_ok=True)
        for d in deliverables:
            file_path = _os.path.join(code_dir, d["path"])
            _os.makedirs(_os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(d["content"])
            _harness_log.info("[Pipeline] Code saved: %s (%d chars)", d["path"], len(d["content"]))

        _auto_ingest_step_to_kb(task_id, step_key, content, deliverables)
        return summary_path
    else:
        # Text-only step: save as single .md file
        out_path = _os.path.join(pdir, f"{idx}_{step_key}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        _harness_log.info("[Pipeline] Step artifact: %s (%d chars)", out_path, len(content))
        _auto_ingest_step_to_kb(task_id, step_key, content, deliverables)
        return out_path


# ── Step Summary Extraction ─────────────────────────────────────
# After each step completes, extract a structured summary (decisions,
# conclusions, file changes, checklist) so downstream agents receive
# compressed context instead of raw LLM dumps.

def _extract_step_summary(task_id: str, step_key: str, raw_text: str,
                           deliverables: list = None,
                           smoke_results: list = None) -> Dict[str, Any]:
    """Extract a structured summary from a completed step's raw output.

    Produces a JSON summary saved as NN_stepkey_summary.json in the pipeline
    workspace. Downstream agents read these summaries instead of raw artifacts,
    keeping the context window compact and signal-rich.

    Returns the summary dict.
    """
    import re as _re_s
    import json as _json_s

    summary: Dict[str, Any] = {
        "step": step_key,
        "task_id": task_id,
        "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%S"),
        "char_count": len(raw_text),
    }

    # ── Extract key decisions / conclusions ──
    # Look for markdown headings containing decision/conclusion keywords
    decisions = []
    conclusion_patterns = [
        _re_s.compile(r"^#{1,3}\s*(?:结论|决定|方案|建议|结果|验证结论|总结|Summary|Conclusion|Decision|Result)[^\n]*\n([\s\S]*?)(?=^#{1,3}\s|\Z)", _re_s.MULTILINE),
        _re_s.compile(r"^(?:[-*]\s*)?(?:结论|决策|方案选择|最终方案)[：:]\s*(.+)$", _re_s.MULTILINE),
    ]
    for pat in conclusion_patterns:
        for m in pat.finditer(raw_text):
            text = m.group(1).strip()[:1500]
            if text and len(text) > 10:
                decisions.append(text)
    summary["decisions"] = decisions[:5]  # Cap at 5 key decisions

    # ── Extract file change list (for develop/deploy steps) ──
    files_changed = []
    if deliverables:
        files_changed = [d["path"] for d in deliverables]
    else:
        # Try to parse from text: look for file paths in bullet lists
        file_path_re = _re_s.compile(
            r"[-*]\s*`?(src/[^\s`]+\.\w{1,6})`?", _re_s.MULTILINE
        )
        files_changed = list(set(m.group(1) for m in file_path_re.finditer(raw_text)))
    summary["files_changed"] = files_changed[:30]

    # ── Extract verification checklist (for test/QA steps) ──
    if step_key == "test":
        checklist = []
        # Parse PASS/FAIL verdict
        verdict_match = _re_s.search(
            r"验证结论\s*(PASS|FAIL|pass|fail)", raw_text, _re_s.IGNORECASE
        )
        summary["verdict"] = verdict_match.group(1).upper() if verdict_match else "UNKNOWN"

        # Parse BLOCKER items
        blocker_re = _re_s.compile(
            r"(?:BLOCKER|blocker|阻塞)[：:\s]+(.+?)(?:\n|$)", _re_s.MULTILINE
        )
        for m in blocker_re.finditer(raw_text):
            checklist.append({"severity": "BLOCKER", "detail": m.group(1).strip()[:300]})

        # Parse import/test failures
        fail_re = _re_s.compile(
            r"(?:❌|FAILED|FAIL|失败)[：:\s]+(.+?)(?:\n|$)", _re_s.MULTILINE
        )
        for m in fail_re.finditer(raw_text):
            detail = m.group(1).strip()[:300]
            if detail and detail not in [c["detail"] for c in checklist]:
                checklist.append({"severity": "FAIL", "detail": detail})

        summary["checklist"] = checklist[:20]

    # ── Smoke test results ──
    if smoke_results:
        smoke_fails = [s for s in smoke_results if not s.get("syntax_ok")]
        summary["smoke"] = {
            "total": len(smoke_results),
            "passed": len(smoke_results) - len(smoke_fails),
            "failed": len(smoke_fails),
            "failures": [
                {"path": s["path"], "errors": s.get("errors", [])}
                for s in smoke_fails
            ],
        }

    # ── Role-specific summaries ──
    if step_key == "pm_decompose":
        # Extract task decomposition items
        task_items = _re_s.findall(
            r"^(?:[-*]|\d+[.)]\s)\s*(.{10,200})$", raw_text, _re_s.MULTILINE
        )
        summary["subtasks"] = task_items[:15]

    elif step_key == "research":
        # Extract key findings
        findings = _re_s.findall(
            r"^(?:[-*])\s*(?:发现|建议|注意|关键|Finding|Key)[：:\s]+(.+)$",
            raw_text, _re_s.MULTILINE
        )
        summary["findings"] = [f.strip()[:300] for f in findings[:10]]

    elif step_key == "architecture":
        # Extract interface definitions / API specs
        api_specs = _re_s.findall(
            r"(?:接口|API|endpoint|路由)[：:\s]+(.+?)(?:\n|$)",
            raw_text, _re_s.MULTILINE
        )
        summary["api_specs"] = [a.strip()[:300] for a in api_specs[:10]]

    elif step_key in ("develop", "deploy"):
        # Build a verification checklist for QA
        verify_items = []
        for fp in files_changed:
            if fp.endswith(".py"):
                verify_items.append(f"import check: `{fp}`")
            elif fp.endswith((".html", ".js", ".mjs")):
                verify_items.append(f"load check: `{fp}`")
        summary["verify_checklist"] = verify_items[:20]

    # ── Compact prose summary (first meaningful paragraph, capped) ──
    # Skip code blocks and take first 800 chars of prose
    prose_text = _re_s.sub(r"```[\s\S]*?```", "", raw_text)
    prose_text = _re_s.sub(r"^#+\s.*$", "", prose_text, flags=_re_s.MULTILINE)
    prose_lines = [l.strip() for l in prose_text.split("\n")
                   if l.strip() and len(l.strip()) > 15]
    summary["prose_summary"] = "\n".join(prose_lines[:15])[:2000]

    # ── Persist summary to pipeline workspace ──
    pdir = _pipeline_dir(task_id)
    idx = _STEP_INDEX.get(step_key, "99")
    summary_path = _os.path.join(pdir, f"{idx}_{step_key}_summary.json")
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            _json_s.dump(summary, f, ensure_ascii=False, indent=2)
        _harness_log.info(
            "[Pipeline] Step summary saved: %s (%d decisions, %d files)",
            summary_path, len(summary.get("decisions", [])),
            len(summary.get("files_changed", [])),
        )
    except Exception as e:
        _harness_log.warning("[Pipeline] Summary save failed: %s", e)

    return summary


def _format_step_summary_for_prompt(summary: Dict[str, Any], step_name: str,
                                      step_idx: str) -> str:
    """Format a step summary JSON into a concise prompt section."""
    parts = [f"### 步骤 {step_idx}: {step_name}\n"]

    # Prose summary (compact)
    prose = summary.get("prose_summary", "")
    if prose:
        # Truncate to 1000 chars for non-adjacent steps
        parts.append(prose[:1500] + "\n")

    # Key decisions
    decisions = summary.get("decisions", [])
    if decisions:
        parts.append("**关键决策:**\n")
        for d in decisions[:3]:
            parts.append(f"  - {d[:300]}\n")

    # Files changed
    files = summary.get("files_changed", [])
    if files:
        parts.append(f"**变更文件 ({len(files)}):**\n")
        for fp in files[:15]:
            parts.append(f"  - `{fp}`\n")

    # Subtasks (PM step)
    subtasks = summary.get("subtasks", [])
    if subtasks:
        parts.append("**子任务拆解:**\n")
        for st in subtasks[:8]:
            parts.append(f"  - {st}\n")

    # Findings (research step)
    findings = summary.get("findings", [])
    if findings:
        parts.append("**关键发现:**\n")
        for f in findings[:5]:
            parts.append(f"  - {f}\n")

    # API specs (architecture step)
    specs = summary.get("api_specs", [])
    if specs:
        parts.append("**接口规范:**\n")
        for s in specs[:5]:
            parts.append(f"  - {s}\n")

    # Verify checklist (develop step → for QA)
    verify = summary.get("verify_checklist", [])
    if verify:
        parts.append("**待验证清单 (QA 必检):**\n")
        for v in verify[:15]:
            parts.append(f"  - [ ] {v}\n")

    # QA verdict + checklist (test step)
    verdict = summary.get("verdict")
    if verdict:
        parts.append(f"**QA 验证结论: {verdict}**\n")
    checklist = summary.get("checklist", [])
    if checklist:
        for c in checklist[:10]:
            parts.append(f"  - [{c['severity']}] {c['detail']}\n")

    # Smoke results
    smoke = summary.get("smoke")
    if smoke:
        parts.append(
            f"**冒烟测试:** {smoke['passed']}/{smoke['total']} 通过\n"
        )
        for sf in smoke.get("failures", [])[:5]:
            parts.append(f"  🔥 `{sf['path']}`: {'; '.join(sf['errors'][:2])}\n")

    parts.append("\n")
    return "".join(parts)


def _get_prior_steps_from_pipeline(task_id: str, current_step_key: str) -> str:
    """Build context from prior steps using incremental summaries.

    Strategy:
    - For N-1 (immediately prior step): include FULL raw output (up to budget)
    - For N-2 and earlier: use compressed summaries from _summary.json
    - This ensures the immediately relevant context is rich while older context
      is compact, keeping total token usage manageable.
    """
    pdir = _pipeline_dir(task_id)
    current_idx = _STEP_INDEX.get(current_step_key, "99")

    parts = []
    _MAX_FULL_STEP = 40_000    # Budget for the immediately prior step (full text)
    _MAX_SUMMARY_STEP = 4_000  # Budget per older step (summary only)
    _MAX_TOTAL = 80_000        # Total budget (down from 150K raw dumps)
    total_chars = 0

    # Collect all prior step entries
    entries = sorted(_os.listdir(pdir))
    prior_entries = []
    for entry in entries:
        if entry.startswith("_") or entry.endswith("_summary.json") or entry.endswith("_tool_trace.json"):
            continue
        entry_idx = entry[:2] if len(entry) > 2 and entry[2] == "_" else ""
        if not entry_idx or entry_idx >= current_idx:
            continue
        prior_entries.append((entry_idx, entry))

    if not prior_entries:
        return ""

    # The last entry is the immediately prior step — gets full text
    immediately_prior_idx = prior_entries[-1][0]

    for entry_idx, entry in prior_entries:
        if total_chars >= _MAX_TOTAL:
            parts.append("(后续步骤产出因 token 预算已省略)\n")
            break

        abs_entry = _os.path.join(pdir, entry)
        step_name = entry[3:] if len(entry) > 3 else entry
        # Strip .md extension from step_name for display
        if step_name.endswith(".md"):
            step_name = step_name[:-3]

        is_immediately_prior = (entry_idx == immediately_prior_idx)

        # ── Try summary first (for non-adjacent steps) ──
        if not is_immediately_prior:
            summary_path = _os.path.join(pdir, f"{entry_idx}_{step_name}_summary.json")
            if _os.path.isfile(summary_path):
                try:
                    import json as _json_r
                    with open(summary_path, "r", encoding="utf-8") as f:
                        summary = _json_r.load(f)
                    chunk = _format_step_summary_for_prompt(summary, step_name, entry_idx)
                    if len(chunk) > _MAX_SUMMARY_STEP:
                        chunk = chunk[:_MAX_SUMMARY_STEP] + "\n...(摘要截断)\n"
                    total_chars += len(chunk)
                    parts.append(chunk)
                    continue  # Summary found, skip raw text
                except Exception:
                    pass  # Fall through to raw text

        # ── Full text for immediately prior step, or fallback for older steps ──
        budget = _MAX_FULL_STEP if is_immediately_prior else _MAX_SUMMARY_STEP
        remaining = _MAX_TOTAL - total_chars
        budget = min(budget, remaining)
        if budget < 200:
            parts.append("(后续步骤产出因 token 预算已省略)\n")
            break

        if _os.path.isfile(abs_entry) and entry.endswith(".md"):
            try:
                with open(abs_entry, "r", encoding="utf-8") as f:
                    content = f.read(budget)
                if len(content) >= budget:
                    content = content[:budget] + "\n...(截断)\n"
                total_chars += len(content)
                label = "(完整产出)" if is_immediately_prior else "(摘要不可用，使用原文)"
                parts.append(f"### 步骤 {entry_idx}: {step_name} {label}\n\n{content}\n")
            except Exception:
                pass

        elif _os.path.isdir(abs_entry):
            # Code step with subdirectory
            step_parts = []

            # Summary.md (the LLM prose)
            summary_md = _os.path.join(abs_entry, "summary.md")
            if _os.path.isfile(summary_md):
                try:
                    with open(summary_md, "r", encoding="utf-8") as f:
                        summary = f.read(budget)
                    if len(summary) >= budget:
                        summary = summary[:budget] + "\n...(截断)\n"
                    label = "(完整产出)" if is_immediately_prior else ""
                    step_parts.append(f"### 步骤 {entry_idx}: {step_name} {label}\n\n{summary}\n")
                    total_chars += len(summary)
                except Exception:
                    pass

            # Code deliverables list (always include, compact)
            code_dir = _os.path.join(abs_entry, "code")
            if _os.path.isdir(code_dir):
                code_files = []
                for dp, _, fns in _os.walk(code_dir):
                    for fn in fns:
                        rel = _os.path.relpath(_os.path.join(dp, fn), code_dir)
                        code_files.append(rel)
                if code_files:
                    chunk = f"📦 代码交付物 ({len(code_files)} 文件):\n"
                    for cf in code_files:
                        chunk += f"  - `{cf}`\n"
                    chunk += "\n"
                    step_parts.append(chunk)
                    total_chars += len(chunk)

            # Apply / smoke-test report (always include, compact and actionable)
            apply_report = _os.path.join(abs_entry, "apply_report.json")
            if _os.path.isfile(apply_report):
                try:
                    import json as _json_ar
                    with open(apply_report, "r", encoding="utf-8") as f:
                        rep = _json_ar.load(f)
                    chunk = "🔬 自动落地与冒烟测试结果:\n"
                    chunk += (f"  applied: {len(rep.get('applied', []))} / "
                              f"skipped: {len(rep.get('skipped', []))} / "
                              f"failed: {len(rep.get('failed', []))}\n")
                    for sk in rep.get("skipped", []):
                        chunk += f"  ⚠️ skipped {sk['path']}: {sk.get('reason','')}\n"
                    for fl in rep.get("failed", []):
                        chunk += f"  ❌ failed {fl['path']}: {fl.get('error','')}\n"
                    for sm in rep.get("smoke", []):
                        if not sm.get("syntax_ok"):
                            chunk += (f"  🔥 smoke FAIL {sm['path']}: "
                                      f"{'; '.join(sm.get('errors', []))}\n")
                    chunk += "\n"
                    step_parts.append(chunk)
                    total_chars += len(chunk)
                except Exception:
                    pass

            parts.extend(step_parts)

    if not parts:
        return ""
    return "## 前序步骤的产出 (递进式摘要)\n\n" + "".join(parts)


def _smoke_check_pipeline_code(task_id: str, step_key: str) -> List[Dict[str, Any]]:
    """Run syntax & basic import checks on staged code in the pipeline workspace.

    Operates on storage/pipeline_runs/{task_id}/{idx}_{step_key}/code/ WITHOUT
    copying into the project. Used after develop saves so QA gets concrete signal.

    Also persists apply_report.json (just the smoke section) for prompt context.
    """
    pdir = _pipeline_dir(task_id)
    idx = _STEP_INDEX.get(step_key, "99")
    step_dir = _os.path.join(pdir, f"{idx}_{step_key}")
    code_dir = _os.path.join(step_dir, "code")
    smoke: List[Dict[str, Any]] = []
    if not _os.path.isdir(code_dir):
        return smoke

    for dirpath, _, filenames in _os.walk(code_dir):
        for fn in filenames:
            abs_src = _os.path.join(dirpath, fn)
            rel = _os.path.relpath(abs_src, code_dir)
            check = {"path": rel, "syntax_ok": True, "errors": []}

            try:
                src = open(abs_src, "r", encoding="utf-8").read()
            except Exception as e:
                check["syntax_ok"] = False
                check["errors"].append(f"read error: {e}")
                smoke.append(check)
                continue

            if rel.endswith(".py"):
                import ast as _ast
                try:
                    _ast.parse(src, filename=abs_src)
                except SyntaxError as e:
                    check["syntax_ok"] = False
                    check["errors"].append(f"SyntaxError L{e.lineno}: {e.msg}")
                if check["syntax_ok"] and "/channels/" in rel:
                    import importlib.util as _ilu
                    mod_name = "_smoke_" + _os.path.splitext(_os.path.basename(rel))[0]
                    try:
                        spec = _ilu.spec_from_file_location(mod_name, abs_src)
                        if spec and spec.loader:
                            mod = _ilu.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                    except Exception as e:
                        check["syntax_ok"] = False
                        check["errors"].append(
                            f"ImportError: {type(e).__name__}: {str(e)[:200]}"
                        )

            elif rel.endswith((".js", ".mjs")):
                if src.count("{") != src.count("}"):
                    check["syntax_ok"] = False
                    check["errors"].append(
                        f"brace mismatch: {{{src.count('{')} vs }}{src.count('}')}"
                    )
                if src.count("(") != src.count(")"):
                    check["syntax_ok"] = False
                    check["errors"].append(
                        f"paren mismatch: ({src.count('(')} vs ){src.count(')')}"
                    )

            if not check["syntax_ok"]:
                _harness_log.warning("[Smoke] FAIL %s: %s", rel, "; ".join(check["errors"]))
            smoke.append(check)

    # Persist as apply_report.json (so prompt context picks it up)
    try:
        report_path = _os.path.join(step_dir, "apply_report.json")
        # If file already exists (e.g. deploy already ran), merge smoke section
        existing = {}
        if _os.path.isfile(report_path):
            try:
                import json as _json
                with open(report_path, "r", encoding="utf-8") as f:
                    existing = _json.load(f)
            except Exception:
                existing = {}
        existing.setdefault("applied", [])
        existing.setdefault("skipped", [])
        existing.setdefault("failed", [])
        existing["smoke"] = smoke
        import json as _json
        with open(report_path, "w", encoding="utf-8") as f:
            _json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return smoke


def _apply_code_from_pipeline(task_id: str, step_key: str) -> Dict[str, Any]:
    """Apply code deliverables from a pipeline step to the actual project.

    Reads from: storage/pipeline_runs/{task_id}/{idx}_{step_key}/code/
    Writes to:  project root (with backup + safety checks)

    Returns summary dict.
    """
    pdir = _pipeline_dir(task_id)
    idx = _STEP_INDEX.get(step_key, "99")
    code_dir = _os.path.join(pdir, f"{idx}_{step_key}", "code")
    project_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.dirname(_os.path.abspath(__file__)))))

    result = {"applied": [], "skipped": [], "failed": [], "backup": []}

    if not _os.path.isdir(code_dir):
        _harness_log.info("[Pipeline] No code dir for %s step %s", task_id, step_key)
        return result

    _ALLOWED_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/")

    for dirpath, _, filenames in _os.walk(code_dir):
        for fn in filenames:
            abs_src = _os.path.join(dirpath, fn)
            rel = _os.path.relpath(abs_src, code_dir)

            # Safety check
            if not any(rel.startswith(p) for p in _ALLOWED_PREFIXES):
                result["skipped"].append({"path": rel, "reason": "Outside allowed dirs"})
                continue
            if ".." in rel:
                result["skipped"].append({"path": rel, "reason": "Path traversal"})
                continue

            target = _os.path.join(project_root, rel)
            try:
                new_content = open(abs_src, "r", encoding="utf-8").read()

                # Shrink-replace guard: refuse to overwrite an existing file
                # with content that is dramatically smaller (likely an LLM
                # "from scratch" rewrite that drops most of the original).
                # Threshold: new < 50% of existing AND existing > 2KB.
                if _os.path.isfile(target):
                    try:
                        existing_size = _os.path.getsize(target)
                    except OSError:
                        existing_size = 0
                    if existing_size > 2048 and len(new_content) < existing_size * 0.5:
                        result["skipped"].append({
                            "path": rel,
                            "reason": (
                                f"shrink-replace guard: new {len(new_content)}B "
                                f"< 50% of existing {existing_size}B "
                                f"(LLM likely emitted a stub rewrite)"
                            ),
                        })
                        _harness_log.warning(
                            "[Pipeline] SKIP shrink-replace: %s "
                            "(new=%dB existing=%dB)",
                            rel, len(new_content), existing_size,
                        )
                        continue

                # Backup existing file
                if _os.path.isfile(target):
                    import shutil
                    backup = target + ".bak"
                    shutil.copy2(target, backup)
                    result["backup"].append({"path": rel, "backup": backup})

                _os.makedirs(_os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(new_content)
                result["applied"].append({"path": rel, "size": len(new_content)})
                _harness_log.info("[Pipeline] Applied: %s (%d chars)", rel, len(new_content))

            except Exception as e:
                result["failed"].append({"path": rel, "error": str(e)[:200]})
                _harness_log.error("[Pipeline] Failed: %s — %s", rel, e)

    _harness_log.info(
        "[Pipeline] Apply result: %d applied, %d skipped, %d failed",
        len(result["applied"]), len(result["skipped"]), len(result["failed"]),
    )

    # ── Post-apply smoke checks: syntax + import probe ──
    # Provides concrete signal for the QA step instead of LLM rubber-stamping.
    smoke = []
    for entry in result["applied"]:
        rel = entry["path"]
        target = _os.path.join(project_root, rel)
        check = {"path": rel, "syntax_ok": True, "errors": []}

        if rel.endswith(".py"):
            import ast as _ast
            try:
                src = open(target, "r", encoding="utf-8").read()
                _ast.parse(src, filename=target)
            except SyntaxError as e:
                check["syntax_ok"] = False
                check["errors"].append(f"SyntaxError L{e.lineno}: {e.msg}")
            # Best-effort import probe (channels/* only)
            if check["syntax_ok"] and "/channels/" in rel:
                import importlib.util as _ilu
                mod_name = "_smoke_" + _os.path.splitext(_os.path.basename(rel))[0]
                try:
                    spec = _ilu.spec_from_file_location(mod_name, target)
                    if spec and spec.loader:
                        mod = _ilu.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                except Exception as e:
                    check["errors"].append(f"ImportError: {type(e).__name__}: {str(e)[:200]}")

        elif rel.endswith((".js", ".mjs")):
            # Minimal sanity: braces & parens balance
            try:
                src = open(target, "r", encoding="utf-8").read()
                if src.count("{") != src.count("}"):
                    check["errors"].append(
                        f"brace mismatch: {{{src.count('{')} vs }}{src.count('}')}"
                    )
                if src.count("(") != src.count(")"):
                    check["errors"].append(
                        f"paren mismatch: ({src.count('(')} vs ){src.count(')')}"
                    )
            except Exception as e:
                check["errors"].append(f"read error: {e}")

        if check["errors"]:
            check["syntax_ok"] = False
            _harness_log.warning("[Pipeline] Smoke FAIL %s: %s", rel, "; ".join(check["errors"]))
        smoke.append(check)
    result["smoke"] = smoke

    # Persist smoke report next to the code/ dir for QA to consume
    try:
        report_path = _os.path.join(pdir, f"{idx}_{step_key}", "apply_report.json")
        import json as _json
        with open(report_path, "w", encoding="utf-8") as f:
            _json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return result


def _write_handoff(task_id: str, step_key: str, payload: Dict[str, Any],
                    *, from_agent: str = "", to_agent: str = "") -> str:
    """Write a structured handoff Markdown file for inter-agent communication.

    Each pipeline step writes a handoff file when it completes, which the next
    agent reads as context.  The file is stored in docs/agent_handoffs/.

    Returns the path of the written file.
    """
    import json as _json
    safe_tid = task_id.replace("/", "_")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    fname = f"{safe_tid}_{step_key}_{ts}.md"
    fpath = _os.path.join(_HANDOFF_DIR, fname)

    lines = [
        f"# Agent Handoff — {step_key}",
        f"",
        f"| 字段 | 值 |",
        f"|------|------|",
        f"| 任务 ID | `{task_id}` |",
        f"| 步骤 | `{step_key}` |",
        f"| 来源 Agent | {from_agent or '(system)'} |",
        f"| 目标 Agent | {to_agent or '(next step)'} |",
        f"| 时间 | {ts} |",
        f"",
        f"## 传递内容",
        f"",
    ]
    for k, v in payload.items():
        if isinstance(v, (dict, list)):
            lines.append(f"### {k}")
            lines.append(f"```json")
            lines.append(_json.dumps(v, ensure_ascii=False, indent=2))
            lines.append(f"```")
            lines.append(f"")
        else:
            lines.append(f"- **{k}**: {v}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"*Auto-generated by AgentsGroup2026 Workflow Harness*")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    _harness_log.info(f"[Handoff] Written: {fpath} ({from_agent} → {to_agent})")
    return fpath


def _validate_session_output(session: Dict[str, Any]) -> bool:
    """Check if a completed session produced meaningful output (not just errors).

    Returns True if the session has real content, False if it's empty/error-only.
    """
    lines = list(session.get("lines", []))
    if not lines:
        return False
    # Filter out framework lines (headers, status markers)
    _NOISE = ("─", "📋", "🤖", "📂", "⏱️", "📝", "⏳", "🔄", "⚠️", "❌", "🔗", "✅")
    content_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(m) for m in _NOISE):
            continue
        if stripped.startswith("  "):  # Prompt echo
            continue
        content_lines.append(stripped)
    # Need at least a few lines of real content
    min_content_lines = 3
    min_content_chars = 50
    total_chars = sum(len(l) for l in content_lines)
    if len(content_lines) < min_content_lines or total_chars < min_content_chars:
        _harness_log.warning("[Validate] Session %s has insufficient output: %d lines, %d chars",
                             session.get("session_id"), len(content_lines), total_chars)
        return False
    return True


def _artifact_path(task_id: str, step_key: str) -> str:
    """Return the .md artifact file path for a given task step."""
    safe_tid = task_id.replace("/", "_")
    return _os.path.join(_ARTIFACT_DIR, f"{safe_tid}_{step_key}.md")


def _collect_step_artifact(task, completed_step: Dict) -> None:
    """Extract output from a completed step's Claude session and save as .md artifact.
    Works for both CLI mode and Ollama direct mode."""
    sid = completed_step.get("session_id")
    if not sid or sid not in _claude_sessions:
        return
    session = _claude_sessions[sid]
    lines = list(session.get("lines", []))
    # Skip header lines (the prompt echo), find actual model output
    # Support multiple header markers:
    #   CLI mode:   "正在启动 Claude Code CLI..."
    #   Ollama:     "使用 Ollama 直连模式" / "Ollama 直连"
    #   Separator:  "─" repeated
    _HEADER_MARKERS = ("正在启动 Claude Code CLI", "使用 Ollama 直连模式",
                       "Ollama 直连", "─" * 10)
    output_lines = []
    past_header = False
    for line in lines:
        if not past_header:
            if any(m in line for m in _HEADER_MARKERS):
                past_header = True
            continue
        output_lines.append(line)
    # Fallback: if no header marker found, take everything after first 3 lines
    if not output_lines and len(lines) > 3:
        output_lines = lines[3:]
    if not output_lines:
        return
    content = "".join(output_lines).strip()
    if not content:
        return
    # Save as .md artifact
    art_path = _artifact_path(task.task_id, completed_step["key"])
    header = (
        f"# {completed_step['label']} — {completed_step.get('agent_role', '')}\n\n"
        f"任务: {task.title}\n"
        f"步骤: {completed_step['key']}\n"
        f"Agent: {completed_step.get('agent_id', '')}\n\n---\n\n"
    )
    with open(art_path, "w", encoding="utf-8") as f:
        f.write(header + content + "\n")
    # Store the artifact path in step metadata
    completed_step["artifact"] = art_path
    _harness_log.info(f"[Harness] Artifact saved: {art_path} ({len(content)} chars)")


# ── Code Deliverable Extraction ──────────────────────────────────
import re as _re_mod

# Pattern: ```lang  // filepath: <path>  OR  ```lang filename=<path>
# Also matches: <!-- file: path --> or # File: path before code blocks
_FILE_PATH_PATTERNS = [
    # Inline in fence: ```python  // src/backend/foo.py
    _re_mod.compile(r"```\w*\s+//\s*(?:filepath:\s*)?(.+)"),
    # Inline in fence: ```python filename=src/backend/foo.py
    _re_mod.compile(r"```\w*\s+filename=(.+)"),
    # Comment above fence: <!-- file: src/frontend/bar.html -->
    _re_mod.compile(r"<!--\s*file:\s*(.+?)\s*-->"),
    # Header above fence: # File: src/frontend/bar.html  OR  ## `src/backend/foo.py`
    _re_mod.compile(r"^#+\s+(?:File:\s*)?`?([^\s`]+\.\w+)`?\s*$", _re_mod.MULTILINE),
    # Bold path: **src/frontend/cms-health.html**
    _re_mod.compile(r"\*\*([^\s*]+\.\w{1,10})\*\*"),
    # Path in backticks on its own line: `src/frontend/foo.html`
    _re_mod.compile(r"^`([^\s`]+\.\w{1,10})`\s*$", _re_mod.MULTILINE),
]

# Valid source file extensions we care about
_CODE_EXTENSIONS = frozenset({
    ".py", ".js", ".mjs", ".ts", ".tsx", ".jsx",
    ".html", ".htm", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".sql", ".sh",
})


def _extract_code_deliverables(text: str) -> List[Dict[str, str]]:
    """Extract code blocks with file paths from LLM output.

    Returns a list of {path: str, content: str, language: str} dicts.
    Handles various formats LLMs use to indicate file paths.
    """
    deliverables: List[Dict[str, str]] = []

    # Split into segments around fenced code blocks
    # Match: ```lang ... ``` with content.
    # CRITICAL: anchor opening AND closing fence to start-of-line so indented
    # code blocks inside echoed prompts (e.g. "  ```js" in a quoted prompt) do
    # not swallow real code fences across hundreds of lines.
    fence_pattern = _re_mod.compile(
        r"^```(\w*)([ \t]+[^\n]*)?\n"     # Opening fence at line start
        r"(.*?)"                           # Code content (non-greedy)
        r"\n^```\s*$",                     # Closing fence at line start
        _re_mod.DOTALL | _re_mod.MULTILINE,
    )

    for m in fence_pattern.finditer(text):
        lang = (m.group(1) or "").strip()
        fence_meta = (m.group(2) or "").strip()
        code = m.group(3) or ""

        # Get pre-context: up to 3 lines before the opening fence
        pre_start = max(0, m.start() - 500)
        pre_text = text[pre_start:m.start()]
        pre_lines = pre_text.split("\n")
        pre_context = "\n".join(pre_lines[-4:]) if len(pre_lines) > 4 else pre_text

        if not code.strip():
            continue
        # Skip shell/terminal output blocks
        if lang in ("bash", "sh", "shell", "console", "terminal", "zsh", "log", "text", "output"):
            # But allow if explicitly marked with a file path
            if not fence_meta:
                continue

        # Try to find file path
        filepath = ""

        # 1. Check fence metadata: ```python // src/backend/foo.py
        if fence_meta:
            for pat in _FILE_PATH_PATTERNS[:2]:
                pm = pat.match(f"```{lang} {fence_meta}")
                if pm:
                    filepath = pm.group(1).strip()
                    break
            if not filepath:
                # Plain path after language: ```python src/backend/foo.py
                candidate = fence_meta.strip().strip("`").strip("'").strip('"')
                if "/" in candidate and _os.path.splitext(candidate)[1] in _CODE_EXTENSIONS:
                    filepath = candidate

        # 2. Check pre-context (lines before the code block)
        if not filepath:
            for line in reversed(pre_context.strip().split("\n")):
                line = line.strip()
                if not line:
                    continue
                for pat in _FILE_PATH_PATTERNS:
                    pm = pat.search(line)
                    if pm:
                        candidate = pm.group(1).strip().strip("`").strip("'").strip('"')
                        if _os.path.splitext(candidate)[1] in _CODE_EXTENSIONS:
                            filepath = candidate
                            break
                if filepath:
                    break

        # 3. Infer from code content (first line comment: # src/backend/foo.py)
        if not filepath:
            first_lines = code.strip().split("\n")[:3]
            for fl in first_lines:
                fl = fl.strip()
                # # file: src/backend/foo.py  or  // src/frontend/bar.js
                fm = _re_mod.match(r"(?:#|//|/\*|<!--)\s*(?:file:\s*)?(\S+\.\w+)", fl)
                if fm:
                    candidate = fm.group(1).strip()
                    if _os.path.splitext(candidate)[1] in _CODE_EXTENSIONS:
                        filepath = candidate
                        break

        if not filepath:
            continue

        # Normalize: strip leading project root prefixes
        for prefix in ("/Users/panglaohu/Downloads/DoubleBoatClawSystem/", "./"):
            if filepath.startswith(prefix):
                filepath = filepath[len(prefix):]

        # Validate: must look like a real project path
        if filepath.startswith("/") or ".." in filepath:
            continue

        deliverables.append({
            "path": filepath,
            "content": code,
            "language": lang or _os.path.splitext(filepath)[1].lstrip("."),
        })

    return deliverables


def _save_deliverables_to_workspace(
    task_id: str, team_id: str, agent_id: str,
    deliverables: List[Dict[str, str]],
) -> List[str]:
    """Save extracted code deliverables to agent workspace.

    Files are saved under: storage/agent_workspaces/{team_id}/{agent_id}/deliverables/{task_id}/
    Returns list of saved file paths (relative to workspace root).
    """
    if not deliverables:
        return []

    safe_tid = task_id.replace("/", "_")[:50]
    root = _agent_ws_root(team_id, agent_id)
    deliverable_dir = root / "deliverables" / safe_tid
    deliverable_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    # Also write a manifest
    manifest_lines = [
        f"# Deliverables for task {task_id}",
        f"",
        f"Agent: {agent_id}",
        f"Time: {datetime.now(timezone.utc).isoformat()}",
        f"Files: {len(deliverables)}",
        f"",
    ]

    for i, d in enumerate(deliverables):
        rel_path = d["path"]
        content = d["content"]

        # Preserve directory structure from the path
        file_target = deliverable_dir / rel_path
        file_target.parent.mkdir(parents=True, exist_ok=True)
        file_target.write_text(content, encoding="utf-8")
        saved.append(str(file_target.relative_to(root)))
        manifest_lines.append(f"- `{rel_path}` ({len(content)} chars, {d.get('language', '')})")
        _harness_log.info(
            f"[Deliverable] Saved: {file_target} ({len(content)} chars)"
        )

    # Write manifest
    manifest_path = deliverable_dir / "_manifest.md"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    _harness_log.info(
        f"[Deliverable] {len(saved)} files saved to workspace for agent {agent_id}, task {task_id}"
    )
    return saved


def _apply_deliverables_to_codebase(
    task_id: str, team_id: str, developer_agent_id: str,
) -> Dict[str, Any]:
    """Read deliverables from developer's workspace and apply them to the project codebase.

    This is called by the deploy step. It reads files from the developer's
    deliverables directory and copies them to the actual project locations.

    Returns a summary dict with applied/skipped/failed counts.
    """
    safe_tid = task_id.replace("/", "_")[:50]
    root = _agent_ws_root(team_id, developer_agent_id)
    deliverable_dir = root / "deliverables" / safe_tid
    project_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.dirname(_os.path.abspath(__file__)))))

    result = {"applied": [], "skipped": [], "failed": [], "backup": []}

    if not deliverable_dir.exists():
        _harness_log.warning(f"[Deploy] No deliverables dir: {deliverable_dir}")
        return result

    # Read manifest to get file list
    for fpath in deliverable_dir.rglob("*"):
        if fpath.is_dir() or fpath.name.startswith("_"):
            continue

        # The relative path inside deliverables mirrors the project structure
        rel_in_deliverable = fpath.relative_to(deliverable_dir)
        target_path = _os.path.join(project_root, str(rel_in_deliverable))

        # Safety: only allow writes within src/, tests/, docs/, config/
        _ALLOWED_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/")
        rel_str = str(rel_in_deliverable)
        if not any(rel_str.startswith(p) for p in _ALLOWED_PREFIXES):
            result["skipped"].append({
                "path": rel_str,
                "reason": f"Outside allowed directories: {_ALLOWED_PREFIXES}",
            })
            _harness_log.warning(f"[Deploy] Skipped (outside allowed dirs): {rel_str}")
            continue

        try:
            new_content = fpath.read_text(encoding="utf-8")

            # Backup existing file if it exists
            if _os.path.isfile(target_path):
                backup_path = target_path + ".bak"
                import shutil
                shutil.copy2(target_path, backup_path)
                result["backup"].append({"path": rel_str, "backup": backup_path})

            # Create parent directories
            _os.makedirs(_os.path.dirname(target_path), exist_ok=True)

            # Write the file
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            result["applied"].append({"path": rel_str, "size": len(new_content)})
            _harness_log.info(f"[Deploy] Applied: {target_path} ({len(new_content)} chars)")

        except Exception as e:
            result["failed"].append({"path": rel_str, "error": str(e)[:200]})
            _harness_log.error(f"[Deploy] Failed to apply {rel_str}: {e}")

    _harness_log.info(
        f"[Deploy] Summary: {len(result['applied'])} applied, "
        f"{len(result['skipped'])} skipped, {len(result['failed'])} failed"
    )
    return result


def _find_developer_agent(team_id: str, workflow: list) -> str:
    """Find the developer agent_id from a workflow's develop step."""
    for s in workflow:
        if s.get("key") == "develop" and s.get("agent_id"):
            return s["agent_id"]
    return ""


# ── Per-step prompt templates ──
_STEP_PROMPTS: Dict[str, str] = {
    "pm_decompose": (
        "你是项目经理 (PM)。请对以下任务进行分解和规划:\n\n"
        "## 任务\n{title}\n{description}\n\n"
        "{prev_artifacts}"
        "## 要求\n"
        "1. 分析任务需求，拆解为可执行的子步骤\n"
        "2. 识别技术风险和依赖关系\n"
        "3. 为后续研究人员、架构师、开发者提供清晰的指导\n"
        "4. 输出一份结构化的任务分解文档 (Markdown 格式)\n\n"
        "## ⚠️ 重要提示\n"
        "系统已自动预加载项目文件结构和相关源文件（见下方 📂 项目上下文）。\n"
        "请基于**实际存在的文件**进行分析，不要猜测文件名。\n\n"
        "项目根目录: {working_dir}\n"
        "后端: src/backend/ (Python FastAPI)\n"
        "前端: src/frontend/ (HTML + JS)\n"
    ),
    "research": (
        "你是技术研究员。请对以下任务进行技术调研:\n\n"
        "## 任务\n{title}\n{description}\n\n"
        "{prev_artifacts}"
        "## ⚠️ 最重要的规则\n"
        "系统已自动预加载项目文件结构和相关源文件（见上方 📂 项目上下文）。\n"
        "**你必须只引用上方提供的实际文件**，严禁凭想象编造文件名或路径。\n"
        "如果上下文中没有某个文件，说明该文件不存在。\n\n"
        "## 要求\n"
        "1. 仔细阅读上方提供的项目文件结构和源文件内容\n"
        "2. 根据**实际存在的文件**分析哪些需要修改\n"
        "3. 列出需要修改的文件的**完整路径** (必须是项目上下文中出现的路径)\n"
        "4. 分析实现方案的可行性\n"
        "5. 引用具体代码行号说明修改点\n\n"
        "项目根目录: {working_dir}\n"
        "后端: src/backend/ (Python FastAPI)\n"
        "前端: src/frontend/ (HTML + JS)\n"
    ),
    "architecture": (
        "你是系统架构师。请为以下任务设计技术方案:\n\n"
        "## 任务\n{title}\n{description}\n\n"
        "{prev_artifacts}"
        "## ⚠️ 重要提示\n"
        "上方 📂 项目上下文 包含了任务相关的实际源文件。\n"
        "请基于这些文件设计方案，不要引用不存在的文件。\n\n"
        "## 要求\n"
        "1. 基于调研结果和实际源码，设计详细技术方案\n"
        "2. 明确指出需要修改的文件和具体修改内容\n"
        "3. 定义接口规范（如有新增 API）\n"
        "4. 为开发工程师提供逐步实施指南\n\n"
        "项目根目录: {working_dir}\n"
        "后端: src/backend/ (Python FastAPI)\n"
        "前端: src/frontend/ (HTML + JS)\n"
    ),
    "develop": (
        "你是开发工程师 (DeepSeek V4 + 工具循环模式)。\n"
        "你**已经被赋予真正的工具能力**: read_file / grep / list_files / write_file / patch_file / run_python。\n"
        "禁止凭空想象 — 所有写代码前必须先用工具读真实代码。\n\n"
        "## 任务\n{title}\n{description}\n\n"
        "{prev_artifacts}"
        "## 推荐工作流（严格遵守）\n"
        "**Step 1 · 侦察**: \n"
        "  - 用 `list_files(path='src/backend/channels')` 看现有 Channel 模块\n"
        "  - 用 `grep(pattern='class MarineChannel', include='src/backend/**/*.py')` 找基类定义\n"
        "  - 用 `read_file(path='src/backend/channels/marine_base.py')` 读完整接口规范\n"
        "  - 找到任何要继承的基类 / 要调用的函数，**先 grep 再 read**，不要靠记忆\n\n"
        "**Step 2 · 验证假设**: 用 `run_python` 跑一段 import 代码，确认 import 路径正确\n"
        "  示例: `run_python(code='from channels.marine_base import ChannelPriority; print(list(ChannelPriority))')`\n\n"
        "**Step 3 · 编码**: \n"
        "  - 新功能 → `write_file` 创建新模块（推荐放在 src/backend/channels/ 或 src/frontend/digital-twin/）\n"
        "  - 改现有大文件 → 用 `patch_file(path, search, replace)` 精准修改\n"
        "  - **禁止** write_file 覆盖 >200 行的现有文件 (会被 shrink-guard 拒绝)\n\n"
        "**Step 4 · 自检**: \n"
        "  - Python: `run_python(code='from channels.your_new_module import YourClass; YourClass()')`\n"
        "  - 通过则继续；失败则修复后再次验证\n\n"
        "**Step 5 · 完成**: 调用 `finish(summary='...', files_changed=[...])`\n\n"
        "## 工程规范\n"
        "- 所有 Channel 必须 `from channels.marine_base import MarineChannel, ChannelPriority, ChannelStatus` 然后 `class X(MarineChannel)`\n"
        "- ChannelPriority 只有 P0 / P1 / P2，**没有 P3**\n"
        "- 必须实现 `process_event()` 和 `get_status()`\n"
        "- 新参数必须有默认值（向后兼容）\n\n"
        "项目根目录: {working_dir}\n"
    ),
    "test": (
        "你是 QA 测试工程师 (DeepSeek V4 + 工具循环模式)。\n"
        "你**已经被赋予真正的测试工具能力**: read_file / grep / run_python / run_pytest。\n"
        "禁止凭空判定 — 所有结论必须来自工具的真实输出。\n\n"
        "## 任务\n{title}\n{description}\n\n"
        "{prev_artifacts}"
        "## 推荐工作流（严格遵守）\n"
        "**Step 1**: 用 grep / read_file 检查 Developer 写的新文件\n"
        "**Step 2**: 对每个新 .py 文件，跑 `run_python(code='from <module> import <name>')` 验证 import 通\n"
        "**Step 3**: 对涉及到的 channel，跑 `run_python(code='from channels.X import Y; obj=Y(); print(obj.process_event({{}}))')` 测试核心方法\n"
        "**Step 4**: 跑 `run_pytest(target='-k <module-name>')` 看相关测试是否通过\n"
        "**Step 5**: 调用 finish 给出结论：\n"
        "  - summary 必须以 `## 验证结论 PASS` 或 `## 验证结论 FAIL` 结尾\n"
        "  - files_changed 通常为空（QA 不写代码）\n\n"
        "## 判定标准\n"
        "- import 失败 → BLOCKER → FAIL\n"
        "- 单元测试失败 → BLOCKER → FAIL\n"
        "- 仅 lint/style 问题 → MINOR → PASS\n\n"
        "项目根目录: {working_dir}\n"
    ),
    "document": (
        "你是文档工程师。请更新以下任务的相关文档:\n\n"
        "## 任务\n{title}\n{description}\n\n"
        "{prev_artifacts}"
        "## 要求\n"
        "1. 根据开发和部署步骤产出，总结变更内容\n"
        "2. 更新相关文档说明\n"
        "3. 输出文档变更清单 (Markdown 格式)\n\n"
        "项目根目录: {working_dir}\n"
        "后端: src/backend/ (Python FastAPI)\n"
        "前端: src/frontend/ (HTML + JS)\n"
    ),
    "deploy": (
        "你是 DevOps 部署工程师。\n"
        "开发者的代码交付物已自动保存到管线共享工作区。\n"
        "部署步骤完成后，系统会自动将代码文件应用到项目代码库。\n\n"
        "## 任务\n{title}\n{description}\n\n"
        "{prev_artifacts}"
        "## 自动部署机制\n"
        "- 开发步骤的代码块已提取到: `storage/pipeline_runs/<task_id>/04_develop/code/`\n"
        "- 本步骤完成时系统自动执行: 开发文件 → 项目代码库 (含 .bak 备份)\n"
        "- 你只需审查变更合理性并输出部署报告\n\n"
        "## 部署策略要求\n"
        "1. **变更分析**: 分析代码变更的范围和影响\n"
        "   - 小改动 (hotfix/patch): 就地更新\n"
        "   - 较大功能变更: 蓝绿部署\n"
        "2. **蓝绿部署判断**: 新增/大幅修改 HTML 页面、API 签名变更、核心 Channel 逻辑变更\n"
        "3. **⚠️ Captain 安全拒绝规则**:\n"
        "   如果 Captain/PM 在前序步骤中拒绝了删除/移除操作:\n"
        "   - **不得直接修改原始页面**\n"
        "   - **创建新版本**: `<文件名>-v2.<ext>` (如 cms-health-v2.html)\n"
        "   - 新版本包含所请求的修改内容，用代码块格式输出:\n"
        "     ```html // src/frontend/cms-health-v2.html\n"
        "     <!-- 完整文件内容 -->\n"
        "     ```\n"
        "4. **产出**: 输出部署清单 (Markdown 格式) 包含: 部署类型, 影响文件, 回滚方案\n\n"
        "项目根目录: {working_dir}\n"
        "后端: src/backend/ (Python FastAPI)\n"
        "前端: src/frontend/ (HTML + JS)\n"
    ),
}


def _build_step_prompt(task, step: Dict, workflow: list) -> str:
    """Build a role-specific prompt for a workflow step.

    Includes:
    1. Pre-seeded project context (_context/ from pipeline workspace)
    2. All prior step outputs from pipeline workspace (full-team shared)
    3. Handoff files for inter-agent state
    4. QA feedback (if pipeline was rewound after a failed test step)
    """
    working_dir = "/Users/panglaohu/Downloads/DoubleBoatClawSystem"
    key = step.get("key", "execute")
    template = _STEP_PROMPTS.get(key, (
        "请执行以下任务步骤 ({label}):\n\n"
        "## 任务\n{title}\n{description}\n\n"
        "{prev_artifacts}"
        "项目根目录: {working_dir}\n"
    ))

    prev_parts = []

    # ── 0. QA feedback from previous failed iteration (highest priority) ──
    try:
        qa_fb = (task.metadata or {}).get("qa_feedback") if hasattr(task, "metadata") else None
        if qa_fb and key in ("develop", "test"):
            iteration = qa_fb.get("iteration", 1)
            fb_parts = [
                f"## 🔁 上一轮 QA 反馈 (第 {iteration} 次重试)\n\n"
                f"上一次开发产出**未通过 QA**，原因：\n\n"
                f"> {qa_fb.get('reason', 'unspecified')}\n\n"
            ]

            # ── Structured failures: actionable file+line+error list ──
            structured = qa_fb.get("structured_failures", [])
            if structured:
                fb_parts.append("### 🎯 具体失败清单 (必须逐条修复)\n\n")
                for i, sf in enumerate(structured[:10], 1):
                    if "file" in sf:
                        line_str = f" L{sf['line']}" if sf.get("line") else ""
                        test_str = f" :: {sf['test']}" if sf.get("test") else ""
                        fb_parts.append(
                            f"{i}. `{sf['file']}`{line_str}{test_str} — {sf.get('error', sf.get('detail', ''))}\n"
                        )
                    elif "error_type" in sf:
                        fb_parts.append(
                            f"{i}. **{sf['error_type']}**: {sf.get('detail', '')}\n"
                        )
                fb_parts.append("\n")

            # QA checklist from structured summary
            qa_checklist = qa_fb.get("qa_checklist", [])
            if qa_checklist:
                fb_parts.append("### QA 检查清单\n\n")
                for item in qa_checklist[:10]:
                    fb_parts.append(f"- [{item.get('severity', '?')}] {item.get('detail', '')}\n")
                fb_parts.append("\n")

            # Raw report as fallback (truncated)
            report_text = qa_fb.get("report", "")
            if report_text and not structured:
                fb_parts.append(f"### QA 报告摘要\n\n```\n{report_text[:3000]}\n```\n\n")

            fb_parts.append(
                "### 必须修复\n"
                "1. 仔细阅读上方失败清单，**逐条**修复列出的 BLOCKER\n"
                "2. 不要重新发明轮子 — 用 read_file 看你之前写的代码，**只改坏的地方**\n"
                "3. 修完后用 run_python / run_pytest **当场验证**\n"
                "4. 验证通过再调用 finish\n\n"
            )
            prev_parts.append("".join(fb_parts))
    except Exception:
        pass

    # ── 1. Project context (pre-seeded file tree + relevant source files) ──
    try:
        project_ctx = _get_pipeline_context_for_prompt(task.task_id)
        if project_ctx:
            prev_parts.append(project_ctx)
    except Exception:
        pass

    # ── 2. Prior step outputs from pipeline workspace ──
    try:
        prior_steps = _get_prior_steps_from_pipeline(task.task_id, key)
        if prior_steps:
            prev_parts.append(prior_steps)
    except Exception:
        pass

    # ── 3. Fallback: old artifact system (for in-flight tasks without pipeline dir) ──
    if not prev_parts:
        _MAX_TOTAL_CHARS = 200_000
        _MAX_PER_ARTIFACT = 60_000
        prior_completed = [s for s in workflow
                          if s["index"] < step["index"] and s.get("status") == "completed"]
        for s in prior_completed[-3:]:
            art_path = s.get("artifact")
            if not art_path or not _os.path.isfile(art_path):
                if s.get("session_id") and s["session_id"] in _claude_sessions:
                    _collect_step_artifact(task, s)
                    art_path = s.get("artifact")
            if art_path and _os.path.isfile(art_path):
                try:
                    with open(art_path, "r", encoding="utf-8") as f:
                        content = f.read(_MAX_PER_ARTIFACT)
                    prev_parts.append(
                        f"## 上一步产出 — {s['label']} ({s.get('agent_role', '')})\n\n"
                        f"{content}\n\n"
                    )
                except Exception:
                    pass

    prev_artifacts = "\n".join(prev_parts) if prev_parts else ""

    try:
        return template.format(
            title=task.title,
            description=task.description or "(无详细描述)",
            working_dir=working_dir,
            prev_artifacts=prev_artifacts,
            label=step.get("label", key),
        )
    except (IndexError, KeyError) as fmt_err:
        # Literal `{` / `}` in template that wasn't escaped → log and fall back
        _harness_log.exception(
            "[Harness] _build_step_prompt template format error for step '%s': %s",
            key, fmt_err,
        )
        # Fallback: return a minimal prompt so the pipeline doesn't deadlock
        return (
            f"# {step.get('label', key)}\n\n"
            f"## 任务\n{task.title}\n{task.description or ''}\n\n"
            f"{prev_artifacts}\n\n"
            f"⚠️ 模板渲染失败 ({fmt_err}); 使用降级 prompt。\n"
            f"项目根目录: {working_dir}\n"
        )


def _resolve_claude_path(configured: str) -> str:
    """Resolve Claude CLI path, checking common locations."""
    import shutil
    if configured and configured != "claude":
        return configured
    # Try PATH first
    found = shutil.which("claude")
    if found:
        return found
    # Common install locations
    for p in [
        _os.path.expanduser("~/.local/bin/claude"),
        "/usr/local/bin/claude",
        _os.path.expanduser("~/.npm-global/bin/claude"),
    ]:
        if _os.path.isfile(p) and _os.access(p, _os.X_OK):
            return p
    return configured  # fallback


def _is_ollama_backend() -> bool:
    """Check if Claude settings point to Ollama (not official Anthropic API)."""
    import json as _json
    try:
        settings_path = _os.path.expanduser("~/.claude/settings.json")
        if _os.path.isfile(settings_path):
            with open(settings_path, "r") as f:
                settings = _json.load(f)
            base_url = settings.get("env", {}).get("ANTHROPIC_BASE_URL", "")
            # Ollama typically uses non-Anthropic URLs
            if base_url and "anthropic.com" not in base_url:
                return True
    except Exception:
        pass
    return False


def _get_deepseek_credentials() -> tuple:
    """Get DeepSeek API key and base URL, preferring RTK proxy when available.

    Checks for RTK proxy at localhost:11435 (configured in Token Factory).
    If RTK is reachable, uses it instead of direct DeepSeek API to save tokens.

    Returns (api_key, base_url, model) or (None, None, None) if unavailable.
    """
    import json as _json
    try:
        settings_path = _os.path.expanduser("~/.claude/settings.json")
        if _os.path.isfile(settings_path):
            with open(settings_path, "r") as f:
                settings = _json.load(f)
            env = settings.get("env", {})
            api_key = env.get("ANTHROPIC_AUTH_TOKEN", "")
            model = env.get("ANTHROPIC_MODEL", "") or settings.get("defaultModel", "deepseek-chat")
            # Map Anthropic model names to DeepSeek model names
            _MODEL_MAP = {
                "claude-sonnet-4-20250514": "deepseek-chat",
                "claude-3-5-sonnet-20241022": "deepseek-chat",
                "claude-3-5-haiku-20241022": "deepseek-chat",
            }
            model = _MODEL_MAP.get(model, model)
            if api_key:
                # Prefer RTK proxy if available (saves 60-90% tokens)
                rtk_base = "http://127.0.0.1:11435/v1"
                try:
                    import http.client as _hc
                    conn = _hc.HTTPConnection("127.0.0.1", 11435, timeout=1.0)
                    conn.request("GET", "/health")
                    resp = conn.get_response()
                    if resp.status < 500:
                        _harness_log.info("[RTK] Proxy detected at 127.0.0.1:11435 — using RTK for token savings")
                        return api_key, rtk_base, model
                    conn.close()
                except Exception:
                    pass
                # Fall back to direct DeepSeek API
                return api_key, "https://api.deepseek.com/v1", model
    except Exception:
        pass
    return None, None, None


# When using DeepSeek as backend, Claude CLI has NO tool access (no file
# editing, no shell), so direct API is always faster and equally capable.
# Claude CLI is only beneficial with real Anthropic API (tool use support).
# Check at runtime whether we're on DeepSeek → always use direct API.
_TEXT_ONLY_ROLES = frozenset({
    "project_manager", "researcher", "documentation", "architect",
})

def _should_use_direct_api(role: str) -> bool:
    """Decide whether to use direct DeepSeek API vs Claude CLI.

    When backend is DeepSeek (not anthropic.com), CLI has no tool access
    so direct API is always better — 10x faster with streaming.
    """
    # If role is text-only, always use direct API
    if role in _TEXT_ONLY_ROLES:
        return True
    # Check if backend is DeepSeek (non-Anthropic) → CLI has no tools
    try:
        import json as _json
        settings_path = _os.path.expanduser("~/.claude/settings.json")
        if _os.path.isfile(settings_path):
            with open(settings_path, "r") as f:
                settings = _json.load(f)
            base_url = settings.get("env", {}).get("ANTHROPIC_BASE_URL", "")
            if base_url and "anthropic.com" not in base_url:
                return True  # Non-Anthropic backend → no tool use → direct API
    except Exception:
        pass
    return False


def _start_claude_session(session_id: str, prompt: str, cfg: Dict, agent, task_id: str) -> None:
    """Start a session for build team tasks.

    Text-only roles (PM, researcher, docs) use DeepSeek API directly for
    fast streaming responses. Code-editing roles (developer, QA, architect)
    use Claude Code CLI which provides tool access.
    """
    _harness_log.info(
        "[Claude] Starting session %s — task: %s, agent: %s (%s)",
        session_id, task_id, agent.name, agent.role,
    )
    working_dir = cfg.get("working_directory", "") or "/Users/panglaohu/Downloads/AgentsGroup2026"
    auto_test = cfg.get("auto_test", True)
    use_direct_api = _should_use_direct_api(agent.role)
    # Direct API streams 64K tokens — needs much longer than the old 300s
    # CLI tool use can be slower still
    default_timeout = 1200 if use_direct_api else 1800
    timeout_sec = cfg.get("session_timeout", default_timeout)

    full_prompt = (
        f"你是 AgentsGroup2026 系统的 {agent.name} ({agent.role})。\n"
        f"请执行以下开发任务:\n\n{prompt}\n\n"
        f"项目根目录: {working_dir}\n"
        f"后端: src/backend/ (Python FastAPI)\n"
        f"前端: src/frontend/ (HTML + JS)\n"
    )
    # Only add test instruction for code-editing roles
    if auto_test and not use_direct_api:
        full_prompt += "完成后运行: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q --tb=short\n"

    session: Dict[str, Any] = {
        "session_id": session_id,
        "task_id": task_id,
        "status": "running",
        "lines": deque(maxlen=20000),
        "started_at": _time.time(),
        "exit_code": None,
        "error": "",
        "proc": None,
    }
    _claude_sessions[session_id] = session

    # Echo the prompt to the terminal buffer so users can see what was sent
    method_label = "DeepSeek API (直连)" if use_direct_api else "Claude Code CLI"
    session["lines"].append(f"{'─'*60}\n")
    session["lines"].append(f"📋 任务: {task_id}\n")
    session["lines"].append(f"🤖 Agent: {agent.name} ({agent.role})\n")
    session["lines"].append(f"📂 工作目录: {working_dir}\n")
    session["lines"].append(f"🔧 执行方式: {method_label}\n")
    session["lines"].append(f"⏱️ 超时: {timeout_sec}s\n")
    session["lines"].append(f"{'─'*60}\n")
    session["lines"].append(f"📝 提示词:\n")
    for pline in full_prompt.split("\n"):
        session["lines"].append(f"  {pline}\n")
    session["lines"].append(f"{'─'*60}\n")

    def _run():
        try:
            # Roles that benefit from real tool access (read/write/exec the codebase)
            _TOOL_ROLES = ("developer", "code_writer", "qa_engineer", "qa", "tester",
                           "build_developer", "build_tester", "deployer", "build_deployer")
            if agent.role in _TOOL_ROLES:
                api_key, api_base_url, model = _get_deepseek_credentials()
                if api_key:
                    session["lines"].append(
                        f"🛠 使用 DeepSeek V4 工具循环模式 (read/grep/write/exec)...\n\n"
                    )
                    _run_tool_loop(
                        session, full_prompt, agent.role,
                        api_key=api_key, api_base_url=api_base_url, model=model,
                        max_tokens=int(cfg.get("max_tokens", 65536)),
                        temperature=float(cfg.get("temperature", 0.2)),
                        max_iterations=int(cfg.get("max_iterations", 25)),
                    )
                    return  # tool-loop handles its own status

            if use_direct_api:
                # Text-only roles → fast streaming via DeepSeek OpenAI-compatible API
                api_key, api_base_url, model = _get_deepseek_credentials()
                if api_key:
                    session["lines"].append(f"⚡ 使用 DeepSeek V4 直连 (64K 输出, 流式)...\n\n")
                    # Pull per-task overrides if any (model_pool defaults to 65536/0.2)
                    _max_tok = int(cfg.get("max_tokens", 65536))
                    _temp = float(cfg.get("temperature", 0.2))
                    _run_openai_compatible(
                        session, full_prompt, timeout_sec,
                        api_key=api_key, api_base_url=api_base_url, model=model,
                        max_tokens=_max_tok, temperature=_temp,
                    )
                else:
                    session["lines"].append(f"⚠️ DeepSeek 凭据未找到，回退到 Claude CLI...\n\n")
                    _run_claude_cli_direct(session, full_prompt, working_dir, timeout_sec, cfg)
            else:
                # Code-editing roles → Claude Code CLI (tool access)
                session["lines"].append(f"⏳ 正在启动 Claude Code CLI...\n\n")
                _run_claude_cli_direct(session, full_prompt, working_dir, timeout_sec, cfg)
        except Exception as run_err:
            import traceback as _tb
            err_text = f"{run_err.__class__.__name__}: {run_err}"
            session["status"] = "failed"
            session["exit_code"] = 1
            session["error"] = err_text
            session["lines"].append(
                f"\n💥 _run 抛出未捕获异常: {err_text}\n"
                f"{_tb.format_exc()[:2000]}\n"
            )
            _harness_log.exception(
                "[Session] %s _run() crashed for role=%s: %s",
                session_id, agent.role, run_err,
            )
            return

        # Final validation: ensure session is properly marked
        final_status = session.get("status", "running")
        if final_status == "running":
            session["status"] = "failed"
            session["exit_code"] = 1
            session["error"] = "Session ended without producing a result"
            session["lines"].append(f"\n❌ 会话结束但未产生结果\n")
            _harness_log.error("[Session] %s ended in 'running' state — forced to failed", session_id)
        elif final_status == "failed":
            _harness_log.warning("[Session] %s ended as FAILED: %s", session_id, session.get("error", ""))
        else:
            _harness_log.info("[Session] %s completed successfully", session_id)

    t = threading.Thread(target=_run, daemon=True)
    t.start()


_CLI_INITIAL_TIMEOUT = 120  # seconds to wait for first output from Claude CLI


def _build_claude_env() -> dict:
    """Build env for Claude CLI subprocess from ~/.claude/settings.json.

    The settings.json env block is authoritative — it overrides any
    inherited ANTHROPIC_* vars from the parent process.
    """
    cli_env = _os.environ.copy()
    # Remove stale ANTHROPIC_* vars that may point to Ollama proxy
    for k in list(cli_env.keys()):
        if k.startswith("ANTHROPIC_"):
            del cli_env[k]
    # Load from settings.json (authoritative source)
    try:
        import json as _json
        settings_path = _os.path.expanduser("~/.claude/settings.json")
        if _os.path.isfile(settings_path):
            with open(settings_path, "r") as f:
                settings = _json.load(f)
            for k, v in settings.get("env", {}).items():
                cli_env[k] = v
    except Exception:
        pass
    return cli_env


def _run_claude_cli_direct(session: Dict[str, Any], prompt: str, working_dir: str,
                            timeout_sec: int, cfg: Dict) -> None:
    """Run Claude Code CLI directly via ``communicate()``.

    Claude CLI buffers its entire response and writes it on exit,
    so line-by-line ``readline()`` with ``select()`` will appear to hang.
    We use ``communicate(timeout=...)`` instead and stream a progress
    indicator so the UI knows the session is alive.
    """
    claude_path = _resolve_claude_path(cfg.get("claude_code_path", "claude"))
    cli_env = _build_claude_env()

    model = cli_env.get("ANTHROPIC_MODEL", "deepseek-chat")
    base_url = cli_env.get("ANTHROPIC_BASE_URL", "")
    session["lines"].append(f"🔗 Claude Code → {base_url or 'default'} | 模型: {model}\n")
    session["lines"].append(f"⏳ DeepSeek 正在思考中...\n\n")

    try:
        proc = subprocess.Popen(
            [claude_path, "-p", prompt, "--bare"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=working_dir, env=cli_env,
        )
        session["proc"] = proc

        # Progress heartbeat: periodically append a dot so the UI
        # knows the session is alive while Claude/DeepSeek is thinking.
        import threading
        stop_heartbeat = threading.Event()

        def _heartbeat():
            tick = 0
            while not stop_heartbeat.wait(10):
                tick += 1
                session["lines"].append(f"⏳ 等待 DeepSeek 响应... ({tick * 10}s)\n")

        hb = threading.Thread(target=_heartbeat, daemon=True)
        hb.start()

        try:
            stdout, stderr = proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            session["lines"].append(f"\n⏱️ 会话超时 ({timeout_sec}s)，已自动终止\n")
            session["status"] = "failed"
            session["exit_code"] = 1
            session["error"] = f"Timeout after {timeout_sec}s"
            stop_heartbeat.set()
            hb.join(timeout=2)
            return
        finally:
            stop_heartbeat.set()
            hb.join(timeout=2)

        session["exit_code"] = proc.returncode

        # Append output to session lines
        if stdout:
            for line in stdout.split("\n"):
                session["lines"].append(line + "\n")

        if stderr:
            for line in stderr.strip().split("\n"):
                if line.strip():
                    session["lines"].append(f"⚠️ {line}\n")

        # Validate output
        real_lines_count = 0
        for sline in (stdout or "").split("\n"):
            stripped = sline.strip()
            if stripped:
                real_lines_count += 1

        if real_lines_count < 1:
            session["lines"].append(f"\n❌ Claude 未返回任何内容\n")
            session["status"] = "failed"
            session["exit_code"] = 1
            session["error"] = "Empty response from Claude CLI"
        elif proc.returncode == 0:
            session["status"] = "completed"
        else:
            session["status"] = "failed"

        if proc.returncode != 0 and proc.returncode is not None:
            session["lines"].append(f"\n⚠️ Claude Code 退出码: {proc.returncode}\n")

    except FileNotFoundError:
        session["lines"].append(f"❌ Claude Code CLI not found: {claude_path}\n")
        session["status"] = "failed"
        session["exit_code"] = 1
        session["error"] = "Claude CLI not found"
    except Exception as e:
        session["lines"].append(f"❌ Claude CLI error: {e}\n")
        session["status"] = "failed"
        session["exit_code"] = 1
        session["error"] = str(e)[:200]


def _run_claude_cli(session: Dict[str, Any], prompt: str, working_dir: str,
                     timeout_sec: int, cfg: Dict) -> None:
    """Run via Claude Code CLI (delegates to _run_claude_cli_direct)."""
    _run_claude_cli_direct(session, prompt, working_dir, timeout_sec, cfg)


def _run_tool_loop(
    session: Dict[str, Any], prompt: str, role: str,
    *, api_key: str, api_base_url: str, model: str,
    max_tokens: int = 65536, temperature: float = 0.2,
    max_iterations: int = 25,
) -> None:
    """Drive a function-calling agent loop. Lets Developer/QA agents read, write,
    and execute the codebase via tool calls instead of single-shot text completion.
    """
    try:
        from agents.runtime import run_tool_loop_sync_with_provider
    except ImportError:
        from .runtime import run_tool_loop_sync_with_provider  # type: ignore

    session["lines"].append(f"🔗 API: {api_base_url}\n模型: {model}\n角色: {role}\n")
    session["lines"].append(f"{'─'*60}\n\n")

    def on_event(kind: str, payload: Dict[str, Any]):
        if kind == "tool_call":
            session["lines"].append(
                f"🔧 调用工具: {payload['name']}({payload['args'][:160]})\n"
            )
        elif kind == "tool_result":
            ok = "✅" if payload.get("ok") else "❌"
            session["lines"].append(
                f"   {ok} {payload['name']}: {payload['summary']}\n"
            )
        elif kind == "model_turn":
            session["lines"].append(
                f"\n🧠 turn#{payload['iteration']} "
                f"({payload['elapsed']}s, {payload['content_chars']}字, "
                f"{payload['tool_call_count']}个工具调用)\n"
            )
        elif kind == "loop_end":
            session["lines"].append(
                f"\n🏁 循环结束: {payload.get('reason')} (turn #{payload.get('iteration')})\n"
            )
        elif kind == "loop_start":
            session["lines"].append(
                f"🚀 工具集: {', '.join(payload['tools'])}\n\n"
            )
        elif kind == "error":
            session["lines"].append(f"💥 错误: {payload.get('error','')}\n")

    system = (
        f"你是 AgentsGroup2026 的 {role} agent。你拥有工具调用能力，"
        f"必须使用工具读真实代码、写真实文件、跑真实测试。"
        "禁止凭空想象 import 路径、类名、属性。"
        "工作流程：\n"
        "1. 先用 list_files / grep / read_file 探索项目结构和现有 API\n"
        "2. 用 run_python 验证你的设想（如导入是否能成功）\n"
        "3. 用 write_file 创建新文件，或 patch_file 修改现有文件\n"
        "4. 修改后用 run_python 或 run_pytest 验证\n"
        "5. 全部完成后调用 finish 工具，附上 summary 和 files_changed\n"
        "重要：禁止整文件覆盖大文件（>200行），改用新建模块或 patch_file。"
    )

    result = run_tool_loop_sync_with_provider(
        prompt=prompt,
        api_key=api_key,
        api_base_url=api_base_url,
        model=model,
        role=role,
        system_prompt=system,
        max_iterations=max_iterations,
        max_tokens=max_tokens,
        temperature=temperature,
        on_event=on_event,
    )

    session["tool_loop_log"] = result.get("log", [])
    session["files_changed"] = result.get("files_changed", [])
    session["loop_summary"] = result.get("summary", "")
    session["loop_ok"] = bool(result.get("ok"))
    session["loop_iterations"] = result.get("iterations", 0)

    if result.get("ok"):
        session["lines"].append(
            f"\n✅ 完成 ({result['iterations']} 轮迭代)\n"
            f"修改文件 {len(result['files_changed'])} 个: "
            f"{', '.join(result['files_changed'])[:200]}\n"
            f"\n📋 总结:\n{result.get('summary', '')[:1500]}\n"
        )
        session["status"] = "completed"
        session["exit_code"] = 0
    else:
        session["lines"].append(
            f"\n❌ 失败: {result.get('error','')}\n"
            f"已完成 {result['iterations']} 轮迭代\n"
        )
        session["status"] = "failed"
        session["exit_code"] = 1
        session["error"] = result.get("error", "")


def _run_openai_compatible(
    session: Dict[str, Any], prompt: str, timeout_sec: int,
    *, api_key: str, api_base_url: str, model: str,
    max_tokens: int = 65536, temperature: float = 0.2,
) -> None:
    """Call any OpenAI-compatible API (DeepSeek V4, OpenAI, etc.) with streaming + retry.

    DeepSeek V4 supports 64K output tokens / 128K context. We default to 64K so
    Developer/Architect agents can emit complete files without truncation.
    """
    import json as _json
    import http.client
    import ssl
    from urllib.parse import urlparse

    parsed = urlparse(api_base_url)
    host = parsed.hostname or "api.deepseek.com"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    use_ssl = parsed.scheme == "https"
    base_path = (parsed.path or "").rstrip("/")

    session["lines"].append(f"🔗 API: {host} | 模型: {model}\n")
    session["lines"].append(f"{'─'*60}\n\n")

    last_error = None
    for attempt in range(_HARNESS_MAX_RETRIES + 1):
        if attempt > 0:
            session["lines"].append(
                f"\n🔄 连接重试 ({attempt}/{_HARNESS_MAX_RETRIES})...\n\n")
            _time.sleep(_HARNESS_RETRY_DELAY * attempt)

        try:
            body = _json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            })
            if use_ssl:
                ctx = ssl.create_default_context()
                conn = http.client.HTTPSConnection(host, port, timeout=timeout_sec, context=ctx)
            else:
                conn = http.client.HTTPConnection(host, port, timeout=timeout_sec)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            conn.request("POST", f"{base_path}/chat/completions", body=body, headers=headers)
            resp = conn.getresponse()

            if resp.status != 200:
                err_body = resp.read().decode("utf-8", errors="replace")[:500]
                last_error = f"API 错误: {resp.status} {resp.reason}\n{err_body}"
                session["lines"].append(f"⚠️ {last_error}\n")
                conn.close()
                continue

            # Stream SSE response
            deadline = _time.time() + timeout_sec
            buffer = ""
            chunk_count = 0
            last_chunk_time = _time.time()
            done = False
            while True:
                now = _time.time()
                if now > deadline:
                    session["lines"].append(f"\n\n⏱️ 超时 ({timeout_sec}s)\n")
                    break
                if chunk_count > 0 and (now - last_chunk_time) > _HARNESS_STALL_SEC:
                    session["lines"].append(
                        f"\n\n⚠️ 流式响应停滞 ({_HARNESS_STALL_SEC}s)\n")
                    break
                chunk = resp.read(4096)
                if not chunk:
                    break
                last_chunk_time = _time.time()
                chunk_count += 1
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line == "data: [DONE]":
                        done = True
                        break
                    if line.startswith("data: "):
                        try:
                            obj = _json.loads(line[6:])
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                session["lines"].append(content)
                        except _json.JSONDecodeError:
                            pass
                if done:
                    break

            session["status"] = "completed"
            session["exit_code"] = 0
            session["lines"].append(f"\n\n{'─'*60}\n")
            session["lines"].append(f"✅ {model} 完成\n")
            conn.close()
            return

        except (ConnectionError, OSError, http.client.HTTPException) as e:
            last_error = str(e)
            session["lines"].append(f"⚠️ 连接错误: {e}\n")
            continue
        except Exception as e:
            session["status"] = "failed"
            session["exit_code"] = 1
            session["error"] = str(e)
            session["lines"].append(f"\n❌ API 错误: {e}\n")
            return

    session["status"] = "failed"
    session["exit_code"] = 1
    session["error"] = last_error or "All retries exhausted"
    session["lines"].append(f"\n❌ 所有重试已耗尽: {last_error}\n")


def _run_ollama_direct(session: Dict[str, Any], prompt: str, timeout_sec: int) -> None:
    """Call Ollama API directly with streaming, retry on transient failures."""
    import json as _json
    import http.client

    # Read config from Claude settings (same source Claude CLI uses)
    ollama_url = "localhost"
    ollama_port = 11434
    model = "qwen3.5-35b-claude"
    try:
        settings_path = _os.path.expanduser("~/.claude/settings.json")
        if _os.path.isfile(settings_path):
            with open(settings_path, "r") as f:
                settings = _json.load(f)
            env = settings.get("env", {})
            base_url = env.get("ANTHROPIC_BASE_URL", "")
            if base_url:
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                ollama_url = parsed.hostname or "localhost"
                ollama_port = parsed.port or 11434
            model = env.get("ANTHROPIC_MODEL", "") or settings.get("defaultModel", "") or model
    except Exception:
        pass

    session["lines"].append(f"🔗 Ollama 直连: {ollama_url}:{ollama_port} | 模型: {model}\n")
    session["lines"].append(f"{'─'*60}\n\n")

    # Mark waiting state so harness stall detector knows we're alive
    session["_ollama_waiting"] = True

    last_error = None
    for attempt in range(_HARNESS_MAX_RETRIES + 1):
        if attempt > 0:
            session["lines"].append(
                f"\n🔄 连接重试 ({attempt}/{_HARNESS_MAX_RETRIES})...\n\n")
            _time.sleep(_HARNESS_RETRY_DELAY * attempt)  # Exponential-ish backoff

        try:
            body = _json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            })
            conn = http.client.HTTPConnection(ollama_url, ollama_port, timeout=timeout_sec)
            conn.request("POST", "/v1/chat/completions", body=body,
                          headers={"Content-Type": "application/json"})
            resp = conn.getresponse()

            if resp.status != 200:
                err_body = resp.read().decode("utf-8", errors="replace")[:500]
                # Detect model runner crash specifically
                if "model runner has unexpectedly stopped" in err_body:
                    last_error = f"Ollama model runner 崩溃 — 远程 GPU 服务器需要重启 Ollama"
                    session["lines"].append(f"❌ {last_error}\n")
                    session["lines"].append(f"⚠️ 可能原因: GPU 内存不足或远程服务器资源耗尽\n")
                    # Don't retry — model runner crash won't self-heal
                    session["status"] = "failed"
                    session["exit_code"] = 1
                    session["error"] = last_error
                    conn.close()
                    return
                last_error = f"Ollama API 错误: {resp.status} {resp.reason}\n{err_body}"
                session["lines"].append(f"⚠️ {last_error}\n")
                conn.close()
                continue  # Retry

            # First chunk received — harness stall detector should not kill us
            session.pop("_ollama_waiting", None)

            # Stream SSE response
            deadline = _time.time() + timeout_sec
            buffer = ""
            chunk_count = 0
            last_chunk_time = _time.time()
            done = False
            while True:
                now = _time.time()
                if now > deadline:
                    session["lines"].append(f"\n\n⏱️ 超时 ({timeout_sec}s)\n")
                    break
                # Stall detection within stream (only after first real content chunk)
                if chunk_count > 0 and (now - last_chunk_time) > _HARNESS_STALL_SEC:
                    session["lines"].append(
                        f"\n\n⚠️ 流式响应停滞 ({_HARNESS_STALL_SEC}s)\n")
                    break
                chunk = resp.read(4096)
                if not chunk:
                    break
                last_chunk_time = _time.time()
                chunk_count += 1
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line == "data: [DONE]":
                        done = True
                        break
                    if line.startswith("data: "):
                        try:
                            obj = _json.loads(line[6:])
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                session["lines"].append(content)
                        except _json.JSONDecodeError:
                            pass
                if done:
                    break

            # Validate: check if stream produced real content
            all_content = "".join(list(session.get("lines", [])))
            _OLLAMA_ERROR_MARKERS = (
                "model runner has unexpectedly stopped",
                "no_proxy",
                "connection refused",
            )
            for marker in _OLLAMA_ERROR_MARKERS:
                if marker in all_content.lower():
                    session["status"] = "failed"
                    session["exit_code"] = 1
                    session["error"] = f"Ollama error detected: {marker}"
                    session["lines"].append(f"\n\n{'─'*60}\n")
                    session["lines"].append(f"❌ Ollama 响应包含错误: {marker}\n")
                    _harness_log.error("[Ollama] Error in response: %s", marker)
                    conn.close()
                    return

            # Count real content characters (exclude framework noise)
            content_chars = sum(len(l) for l in session["lines"]
                                if not any(l.strip().startswith(m) for m in
                                           ("─", "📋", "🤖", "📂", "⏱️", "📝", "⏳", "🔗", "✅", "❌", "⚠️", "🔄")))
            if content_chars < 50:
                session["status"] = "failed"
                session["exit_code"] = 1
                session["error"] = f"Ollama returned insufficient content ({content_chars} chars)"
                session["lines"].append(f"\n\n{'─'*60}\n")
                session["lines"].append(f"❌ Ollama 响应内容不足 ({content_chars} 字符)\n")
                _harness_log.warning("[Ollama] Insufficient content: %d chars", content_chars)
                conn.close()
                return

            session["status"] = "completed"
            session["exit_code"] = 0
            session["lines"].append(f"\n\n{'─'*60}\n")
            session["lines"].append(f"✅ Ollama 直连完成 ({content_chars} 字符)\n")
            conn.close()
            return  # Success — exit retry loop

        except (ConnectionError, OSError, http.client.HTTPException) as e:
            last_error = str(e)
            session["lines"].append(f"⚠️ 连接错误: {e}\n")
            continue  # Retry
        except Exception as e:
            # Non-retryable error
            session["status"] = "failed"
            session["exit_code"] = 1
            session["error"] = str(e)
            session["lines"].append(f"\n❌ Ollama 直连错误: {e}\n")
            return

    # All retries exhausted
    session["status"] = "failed"
    session["exit_code"] = 1
    session["error"] = last_error or "All retries exhausted"
    session["lines"].append(f"\n❌ 所有重试已耗尽: {last_error}\n")


@router.post(
    "/teams/{team_id}/agents/{agent_id}/skills/{skill_name}/execute",
    summary="Execute a skill (e.g. code_implementation via Claude Code)",
)
async def execute_skill(
    team_id: str, agent_id: str, skill_name: str, req: ExecuteSkillRequest
) -> Dict[str, Any]:
    """Invoke a skill execution. For code_implementation, can call Claude Code CLI."""
    agent = _get_agent_or_404(team_id, agent_id)
    sr = _sr()
    skill = sr.get_by_slug(skill_name)
    if skill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_name}' not found")

    # Merge config
    cfg = dict(skill.config or {})
    cfg.update(req.config_overrides)

    result: Dict[str, Any] = {
        "skill": skill_name,
        "agent_id": agent_id,
        "task_id": req.task_id,
        "executor": cfg.get("executor", "manual"),
        "status": "pending",
    }

    if skill_name == "code_implementation":
        executor = cfg.get("executor", "claude_code")
        if executor == "claude_code":
            # Start streaming session instead of blocking
            import uuid
            session_id = str(uuid.uuid4())[:12]
            _start_claude_session(session_id, req.prompt, cfg, agent, req.task_id)
            result["status"] = "streaming"
            result["session_id"] = session_id
            result["stream_url"] = f"/api/v1/agent-config/claude-sessions/{session_id}/stream"
        elif executor == "llm_chat":
            result = await _execute_llm_chat(req.prompt, agent, req.task_id)
        else:
            result["status"] = "manual"
            result["instructions"] = skill.instructions
            result["prompt"] = req.prompt
    elif skill_name == "task_decomposition":
        result = await _execute_task_decomposition(req.prompt, agent, team_id, req.task_id)
    else:
        # Generic skill: try LLM-based execution with skill instructions as system prompt
        instructions = skill.instructions or skill.description or ""
        result["instructions"] = instructions
        result["prompt"] = req.prompt
        try:
            from .chat_harness import get_chat_harness
            harness = get_chat_harness()
            system_prompt = (
                f"你是 {agent.name}，你被分配了技能「{skill_name}」。\n\n"
                f"技能说明: {instructions}\n\n"
                f"请根据用户的提示词，以这个技能的身份和能力来回答。"
            )
            llm_result = await harness.chat(
                req.prompt,
                agent_id=agent.agent_id,
                session_id=f"skill_{skill_name}_{req.task_id or 'test'}",
                system_prompt=system_prompt,
            )
            if llm_result and llm_result.response:
                result["status"] = "completed"
                result["output"] = llm_result.response[:4000]
                result["usage"] = {
                    "total_tokens": llm_result.usage.total_tokens if llm_result.usage else 0,
                }
            else:
                result["status"] = "failed"
                result["error"] = "LLM 返回空响应"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)[:500]
            # Fallback: return instructions so user can at least see the skill description
            if not result.get("output"):
                result["output"] = f"[技能 {skill_name}] 执行遇到错误，以下是指令内容:\n\n{instructions}"

    return result


from starlette.responses import StreamingResponse


@router.get(
    "/claude-sessions/{session_id}/stream",
    summary="SSE stream of Claude Code CLI output",
)
async def stream_claude_session(session_id: str):
    """Server-Sent Events endpoint for live Claude Code output."""
    if session_id not in _claude_sessions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    async def event_gen():
        session = _claude_sessions[session_id]
        sent = 0
        while True:
            lines = list(session["lines"])
            if sent < len(lines):
                for line in lines[sent:]:
                    # SSE format: each line prefixed with "data: "
                    escaped = line.replace("\n", "")
                    yield f"data: {escaped}\n\n"
                sent = len(lines)
            if session["status"] in ("completed", "failed", "error"):
                yield f"event: done\ndata: {{\"status\":\"{session['status']}\",\"exit_code\":{session.get('exit_code', -1)}}}\n\n"
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@router.get(
    "/claude-sessions/{session_id}",
    summary="Get Claude Code session status and output",
)
async def get_claude_session(session_id: str) -> Dict[str, Any]:
    """Get current session status + all buffered output."""
    if session_id not in _claude_sessions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    s = _claude_sessions[session_id]
    # Check if process died but status wasn't updated
    if s["status"] == "running" and s["proc"] is not None:
        rc = s["proc"].poll()
        if rc is not None:
            s["exit_code"] = rc
            s["status"] = "completed" if rc == 0 else "failed"
            if rc != 0:
                s["lines"].append(f"\n⚠️ Claude Code 退出码: {rc}\n")
    # Sanitize output: strip control chars (keep \n, \t)
    import re
    _ctrl_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
    clean_lines = [_ctrl_re.sub('', l) for l in s["lines"]]
    return {
        "session_id": session_id,
        "status": s["status"],
        "task_id": s["task_id"],
        "exit_code": s["exit_code"],
        "error": s["error"],
        "output": clean_lines,
        "line_count": len(clean_lines),
        "elapsed": round(_time.time() - s["started_at"], 1),
    }


@router.get(
    "/tasks/{task_id}/tool-trace",
    summary="Get all tool-call traces for a task pipeline",
)
async def get_task_tool_traces(task_id: str) -> Dict[str, Any]:
    """Return persisted tool-call traces (one JSON per step that ran in tool-loop mode)."""
    pdir = _pipeline_dir(task_id)
    if not _os.path.isdir(pdir):
        return {"task_id": task_id, "traces": [], "count": 0}
    import json as _json_tt
    traces = []
    try:
        for name in sorted(_os.listdir(pdir)):
            if not name.endswith("_tool_trace.json"):
                continue
            fp = _os.path.join(pdir, name)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = _json_tt.load(f)
                traces.append(data)
            except Exception:
                continue
    except Exception:
        pass
    return {"task_id": task_id, "traces": traces, "count": len(traces)}


@router.post(
    "/claude-sessions/{session_id}/stop",
    summary="Stop a running Claude Code session",
)
async def stop_claude_session(session_id: str) -> Dict[str, Any]:
    """Kill the Claude Code subprocess."""
    if session_id not in _claude_sessions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    s = _claude_sessions[session_id]
    if s["proc"] and s["status"] == "running":
        try:
            s["proc"].kill()
        except Exception:
            pass
        s["status"] = "stopped"
        s["lines"].append("\n⛔ 会话已手动停止\n")
    return {"session_id": session_id, "status": s["status"]}


@router.get(
    "/harness/status",
    summary="Get workflow harness status",
)
async def harness_status() -> Dict[str, Any]:
    """Show active harness monitors and session summary."""
    monitors = {}
    for tid, thr in _harness_threads.items():
        monitors[tid] = {"alive": thr.is_alive()}
    sessions = {}
    for sid, s in _claude_sessions.items():
        sessions[sid] = {
            "status": s["status"],
            "task_id": s["task_id"],
            "line_count": len(s["lines"]),
            "elapsed": round(_time.time() - s["started_at"], 1),
        }
    return {
        "monitors": monitors,
        "sessions": sessions,
        "config": {
            "poll_sec": _HARNESS_POLL_SEC,
            "max_retries": _HARNESS_MAX_RETRIES,
            "stall_sec": _HARNESS_STALL_SEC,
            "auto_advance": _HARNESS_AUTO_ADVANCE,
        },
    }


# ── Pipeline status + SSE endpoints ──────────────────────────────────────


@router.get(
    "/tasks/{task_id}/pipeline/status",
    summary="Get pipeline execution status (lightweight, for bridge chat polling)",
)
def get_pipeline_status(task_id: str) -> Dict[str, Any]:
    """Return current pipeline status: steps with their statuses, active step, rewind count.
    Designed for the bridge chat widget to poll cheaply."""
    engine = _te()
    task = engine.get_task(task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    wf = (task.metadata or {}).get("workflow", [])
    steps = []
    active_step = None
    for s in wf:
        step_info = {
            "key": s.get("key", ""),
            "label": s.get("label", ""),
            "status": s.get("status", "pending"),
        }
        if s.get("error"):
            step_info["error"] = str(s["error"])[:200]
        if s.get("deliverable_count"):
            step_info["files"] = s["deliverable_count"]
        steps.append(step_info)
        if s.get("status") == "active":
            active_step = s.get("key")
    md = task.metadata or {}
    return {
        "task_id": task_id,
        "task_status": task.status.value if hasattr(task.status, "value") else str(task.status),
        "title": task.title,
        "steps": steps,
        "active_step": active_step,
        "rewinds": int(md.get("pipeline_rewinds", 0)),
        "max_rewinds": _PIPELINE_MAX_REWINDS,
        "pipeline_failed_reason": md.get("pipeline_failed_reason"),
        "events": _pipeline_events.get(task_id, [])[-20:],
    }


@router.get(
    "/tasks/{task_id}/pipeline/events",
    summary="SSE stream of pipeline events for a task",
)
async def pipeline_events_sse(task_id: str):
    """Server-Sent Events stream for real-time pipeline progress.
    The bridge chat subscribes to this after dispatching a task."""
    from starlette.responses import StreamingResponse
    import json as _sse_json

    engine = _te()
    task = engine.get_task(task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")

    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _pipeline_subscribers.setdefault(task_id, []).append(queue)

    async def event_generator():
        try:
            # Send current state as first event
            wf = (task.metadata or {}).get("workflow", [])
            init = {
                "type": "init",
                "task_status": task.status.value if hasattr(task.status, "value") else str(task.status),
                "steps": [{"key": s.get("key"), "label": s.get("label"), "status": s.get("status")} for s in wf],
            }
            yield f"data: {_sse_json.dumps(init, ensure_ascii=False)}\n\n"

            # Also replay recent events
            for evt in _pipeline_events.get(task_id, [])[-10:]:
                yield f"data: {_sse_json.dumps(evt, ensure_ascii=False)}\n\n"

            # Stream new events
            while True:
                try:
                    evt = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {_sse_json.dumps(evt, ensure_ascii=False)}\n\n"
                    # Terminal events
                    if evt.get("type") in ("pipeline_complete", "pipeline_failed"):
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
                    # Check if task is terminal
                    t = engine.get_task(task_id)
                    if t and hasattr(t.status, "value") and t.status.value in ("completed", "failed", "cancelled"):
                        final = {"type": "pipeline_complete", "task_status": t.status.value}
                        yield f"data: {_sse_json.dumps(final, ensure_ascii=False)}\n\n"
                        break
        finally:
            # Unsubscribe
            subs = _pipeline_subscribers.get(task_id, [])
            if queue in subs:
                subs.remove(queue)
            if not subs:
                _pipeline_subscribers.pop(task_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/harness/gc",
    summary="Run session garbage collection",
)
async def run_session_gc() -> Dict[str, Any]:
    """Manually trigger GC of expired sessions."""
    removed = _gc_sessions()
    return {"removed": removed, "remaining": len(_claude_sessions)}


async def _execute_llm_chat(prompt: str, agent, task_id: str) -> Dict[str, Any]:
    """Execute code_implementation via LLM chat."""
    from .chat_harness import get_chat_harness
    harness = get_chat_harness()
    try:
        result = await harness.chat(
            prompt,
            agent_id=agent.agent_id,
            session_id=f"skill_code_{task_id}",
            system_prompt=f"你是 {agent.name}，负责代码实现。根据需求编写代码，给出文件路径和完整代码。",
        )
        return {
            "skill": "code_implementation",
            "executor": "llm_chat",
            "task_id": task_id,
            "status": "completed" if not result.error else "failed",
            "output": result.response[:3000] if result.response else "",
            "error": result.error or "",
            "model": result.model,
        }
    except Exception as e:
        return {"skill": "code_implementation", "executor": "llm_chat", "task_id": task_id, "status": "error", "error": str(e)}


async def _execute_task_decomposition(prompt: str, agent, team_id: str, parent_task_id: str) -> Dict[str, Any]:
    """PM decomposes a task into subtasks and submits them to TaskEngine."""
    from .chat_harness import get_chat_harness
    harness = get_chat_harness()

    decompose_prompt = (
        f"你是项目经理 {agent.name}。请将以下任务分解为可执行的子任务。\n\n"
        f"任务: {prompt}\n\n"
        f"请以 JSON 数组格式返回子任务，每个子任务包含:\n"
        f'  {{"title": "子任务标题", "agent_id": "目标agent_id", "priority": 2, "description": "描述"}}\n\n'
        f"可用 Agent: build_pm, build_researcher, build_architect, build_developer, build_tester, build_deployer, build_doc_writer\n"
        f"只返回 JSON 数组，不要其他内容。"
    )

    subtasks_created = []
    try:
        result = await harness.chat(
            decompose_prompt,
            agent_id=agent.agent_id,
            session_id=f"skill_decompose_{parent_task_id}",
            system_prompt="你是任务分解专家。只返回 JSON 数组。",
        )
        if result.response:
            import json, re
            # Extract JSON array from response
            match = re.search(r'\[.*\]', result.response, re.DOTALL)
            if match:
                items = json.loads(match.group())
                engine = _te()
                if not engine._running:
                    await engine.start()
                for item in items[:10]:
                    task = AgentTask(
                        agent_id=item.get("agent_id", ""),
                        team_id=team_id,
                        title=item.get("title", "子任务"),
                        description=item.get("description", ""),
                        priority=item.get("priority", 2),
                        metadata={"parent_task": parent_task_id, "auto_decomposed": True},
                    )
                    await engine.submit_task(task)
                    subtasks_created.append(task.to_dict())
    except Exception:
        pass

    return {
        "skill": "task_decomposition",
        "task_id": parent_task_id,
        "status": "completed" if subtasks_created else "no_subtasks",
        "subtasks": subtasks_created,
        "count": len(subtasks_created),
    }


@router.get(
    "/skills/{skill_name}/config-schema",
    summary="Get skill config schema for UI rendering",
)
def get_skill_config_schema(skill_name: str) -> Dict[str, Any]:
    """Return the config schema and current config for a skill."""
    sr = _sr()
    skill = sr.get_by_slug(skill_name)
    if skill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return {
        "skill_name": skill.name,
        "config_schema": skill.config_schema,
        "config": skill.config,
        "instructions": skill.instructions,
    }


@router.put(
    "/skills/{skill_name}/config",
    summary="Update skill configuration",
)
def update_skill_config(skill_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Update a skill's runtime configuration."""
    sr = _sr()
    skill = sr.get_by_slug(skill_name)
    if skill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found")
    skill.config.update(config)
    return {"skill_name": skill.name, "config": skill.config}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/tasks",
    summary="List tasks assigned to an agent",
)
def list_agent_tasks(team_id: str, agent_id: str) -> List[Dict[str, Any]]:
    _get_team_or_404(team_id)
    _get_agent_or_404(team_id, agent_id)
    return [
        t.to_dict()
        for t in _te().get_agent_tasks(agent_id)
        if t.team_id == team_id
    ]


@router.get("/tasks/stats", summary="Task engine statistics")
def task_engine_stats() -> Dict[str, Any]:
    return _te().stats()


class CrossTeamTaskRequest(BaseModel):
    """Submit a task from one team to another."""
    target_team_id: str = Field(..., min_length=1)
    target_agent_id: str = ""
    source_team_id: str = ""
    source_agent_id: str = ""
    title: str = Field(..., min_length=1, max_length=256)
    description: str = ""
    priority: int = Field(default=2, ge=0, le=3)
    original_message: str = ""


@router.post(
    "/cross-team/tasks",
    summary="Submit a cross-team task (e.g. execution→build)",
    status_code=status.HTTP_201_CREATED,
)
async def submit_cross_team_task(req: CrossTeamTaskRequest) -> Dict[str, Any]:
    """Create a task in the target team, recording the source team/agent."""
    _get_team_or_404(req.target_team_id)
    if req.target_agent_id:
        target = _tm().get_agent(req.target_team_id, req.target_agent_id)
        if target is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Target agent not found")

    engine = _te()
    if not engine._running:
        await engine.start()

    task = AgentTask(
        agent_id=req.target_agent_id or "",
        team_id=req.target_team_id,
        title=req.title,
        description=req.description or f"[跨团队任务] 来源: {req.source_agent_id or req.source_team_id}\n原始消息: {req.original_message}",
        priority=req.priority,
        metadata={
            "cross_team": True,
            "source_team": req.source_team_id,
            "source_agent": req.source_agent_id,
            "original_message": req.original_message,
        },
    )
    # Auto-generate workflow steps for cross-team tasks
    wf = _generate_workflow(task, req.target_team_id)
    if wf:
        task.metadata["workflow"] = wf
    await engine.submit_task(task)
    return task.to_dict()


# =========================================================================
# Memory Files & Soul.md  (Clawith-style persistent memory)
# =========================================================================


class MemoryFileRequest(BaseModel):
    filename: str = Field(..., max_length=128)
    content: str = Field(default="")


class SoulUpdateRequest(BaseModel):
    content: str = Field(default="")


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory",
    summary="List agent memory files",
)
def list_memory_files(team_id: str, agent_id: str) -> List[Dict[str, Any]]:
    agent = _get_agent_or_404(team_id, agent_id)
    files = agent.metadata.get("memory_files", {})
    return [
        {"filename": k, "size": len(v), "size_display": _fmt_size(len(v))}
        for k, v in files.items()
    ]


@router.get(
    "/teams/{team_id}/agents/{agent_id}/memory/{filename}",
    summary="Read a memory file",
)
def read_memory_file(team_id: str, agent_id: str, filename: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    files = agent.metadata.get("memory_files", {})
    if filename not in files:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Memory file not found")
    return {"filename": filename, "content": files[filename], "size": len(files[filename])}


@router.put(
    "/teams/{team_id}/agents/{agent_id}/memory/{filename}",
    summary="Create or update a memory file",
)
def write_memory_file(
    team_id: str, agent_id: str, filename: str, req: SoulUpdateRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if "memory_files" not in agent.metadata:
        agent.metadata["memory_files"] = {}
    agent.metadata["memory_files"][filename] = req.content
    return {"filename": filename, "size": len(req.content), "status": "saved"}


@router.delete(
    "/teams/{team_id}/agents/{agent_id}/memory/{filename}",
    summary="Delete a memory file",
)
def delete_memory_file(team_id: str, agent_id: str, filename: str) -> Dict[str, str]:
    agent = _get_agent_or_404(team_id, agent_id)
    files = agent.metadata.get("memory_files", {})
    if filename not in files:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Memory file not found")
    del files[filename]
    return {"status": "deleted", "filename": filename}


@router.get(
    "/teams/{team_id}/agents/{agent_id}/soul",
    summary="Get agent Soul.md content",
)
def get_soul(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    soul = agent.metadata.get("soul_md", "")
    return {"content": soul, "size": len(soul)}


@router.put(
    "/teams/{team_id}/agents/{agent_id}/soul",
    summary="Update agent Soul.md content",
)
def update_soul(team_id: str, agent_id: str, req: SoulUpdateRequest) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.metadata["soul_md"] = req.content
    return {"status": "saved", "size": len(req.content)}


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


# ══════════════════════════════════════════════════════════════
# OpenClaw Agent Import
# ══════════════════════════════════════════════════════════════


class ImportOpenClawRequest(BaseModel):
    name: str = Field(..., min_length=1)
    role: str = ""
    openclaw_url: str = ""
    openclaw_token: str = ""
    openclaw_agent_id: str = ""
    visibility: str = "public"
    soul_content: str = ""
    model_id: str = ""


@router.post(
    "/teams/{team_id}/agents/import-openclaw",
    summary="Import an OpenClaw Agent",
    status_code=status.HTTP_201_CREATED,
)
def import_openclaw_agent(team_id: str, req: ImportOpenClawRequest) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    agent = AgentProfile(
        name=req.name,
        role=req.role,
        model_id=req.model_id,
    )
    agent.metadata["openclaw"] = {
        "url": req.openclaw_url,
        "token": req.openclaw_token[:8] + "***" if len(req.openclaw_token) > 8 else "***" if req.openclaw_token else "",
        "token_set": bool(req.openclaw_token),
        "agent_id": req.openclaw_agent_id,
        "connected": bool(req.openclaw_url and req.openclaw_token),
        "imported_at": datetime.now(timezone.utc).isoformat(),
    }
    if req.soul_content:
        agent.metadata["soul_md"] = req.soul_content
    agent.metadata["visibility"] = req.visibility
    ok = _tm().add_agent_to_team(team_id, agent)
    if not ok:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add agent"
        )
    return agent.to_dict()


@router.get(
    "/teams/{team_id}/agents/{agent_id}/openclaw-status",
    summary="Get OpenClaw connection status",
)
def get_openclaw_status(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    return agent.metadata.get("openclaw", {"connected": False})


@router.post(
    "/teams/{team_id}/agents/{agent_id}/sync-openclaw",
    summary="Sync OpenClaw Agent",
)
def sync_openclaw_agent(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if "openclaw" not in agent.metadata:
        agent.metadata["openclaw"] = {"connected": False}
    agent.metadata["openclaw"]["last_sync"] = datetime.now(timezone.utc).isoformat()
    return agent.metadata["openclaw"]


# ══════════════════════════════════════════════════════════════
# Hermes Agent API — Research Agent Management
# Inspired by NousResearch/hermes-agent architecture
# ══════════════════════════════════════════════════════════════


class CreateHermesResearcherRequest(BaseModel):
    """Create a Hermes-style research agent."""
    name: str = Field(default="Researcher", min_length=1, max_length=128)
    distribution: str = "general_research"
    soul_md: str = ""
    can_delegate: bool = True


class UpdateHermesConfigRequest(BaseModel):
    """Update Hermes agent configuration."""
    max_iterations: int = Field(default=90, ge=1, le=500)
    memory_enabled: bool = True
    session_search_enabled: bool = True
    skill_auto_create: bool = True
    soul_md: str = ""
    can_delegate: bool = True
    max_subagents: int = Field(default=3, ge=0, le=10)
    distribution: str = ""
    enabled_toolsets: List[str] = Field(default_factory=list)
    disabled_toolsets: List[str] = Field(default_factory=list)


@router.post(
    "/teams/{team_id}/agents/create-hermes-researcher",
    summary="Create a Hermes-style research agent",
    status_code=status.HTTP_201_CREATED,
)
def create_hermes_researcher_endpoint(
    team_id: str, req: CreateHermesResearcherRequest
) -> Dict[str, Any]:
    _get_team_or_404(team_id)
    agent = create_hermes_researcher(
        name=req.name,
        distribution=req.distribution,
        soul_md=req.soul_md,
        can_delegate=req.can_delegate,
    )
    ok = _tm().add_agent_to_team(team_id, agent)
    if not ok:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add agent"
        )
    return agent.to_dict()


@router.put(
    "/teams/{team_id}/agents/{agent_id}/hermes-config",
    summary="Update Hermes agent configuration",
)
def update_hermes_config(
    team_id: str, agent_id: str, req: UpdateHermesConfigRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if agent.hermes_config is None:
        agent.hermes_config = HermesAgentConfig()

    hc = agent.hermes_config
    hc.max_iterations = req.max_iterations
    hc.iteration_budget = req.max_iterations
    hc.memory_enabled = req.memory_enabled
    hc.session_search_enabled = req.session_search_enabled
    hc.skill_auto_create = req.skill_auto_create
    hc.can_delegate = req.can_delegate
    hc.max_subagents = req.max_subagents

    if req.soul_md:
        hc.soul_md = req.soul_md

    if req.distribution:
        dist = RESEARCH_TOOLSET_DISTRIBUTIONS.get(req.distribution)
        if dist:
            hc.toolset_distribution = ToolsetDistribution(
                name=req.distribution,
                description=dist["description"],
                toolsets=dict(dist["toolsets"]),
            )
            hc.enabled_toolsets = list(dist["toolsets"].keys())

    if req.enabled_toolsets:
        hc.enabled_toolsets = list(req.enabled_toolsets)
    if req.disabled_toolsets:
        hc.disabled_toolsets = list(req.disabled_toolsets)

    # Rebuild system prompt with new config
    active_toolsets = sample_toolsets(hc.toolset_distribution.name)
    agent.system_prompt = build_research_system_prompt(agent, active_toolsets)
    agent.tools = resolve_tools(active_toolsets)

    return agent.to_dict()


@router.get(
    "/teams/{team_id}/agents/{agent_id}/hermes-config",
    summary="Get Hermes agent configuration",
)
def get_hermes_config(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if agent.hermes_config is None:
        return {"is_hermes_agent": False}
    return {
        "is_hermes_agent": True,
        **agent.hermes_config.to_dict(),
    }


@router.get(
    "/hermes/distributions",
    summary="List available Hermes toolset distributions",
)
def list_hermes_distributions() -> Dict[str, Any]:
    return get_research_distributions()


@router.get(
    "/hermes/toolsets",
    summary="List available Hermes toolsets",
)
def list_hermes_toolsets() -> Dict[str, Any]:
    return get_hermes_toolsets()


@router.post(
    "/teams/{team_id}/agents/{agent_id}/hermes-sample-toolsets",
    summary="Sample toolsets from distribution (probabilistic)",
)
def hermes_sample_toolsets(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if agent.hermes_config is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Agent is not a Hermes agent"
        )
    dist_name = agent.hermes_config.toolset_distribution.name
    sampled = sample_toolsets(dist_name)
    resolved = resolve_tools(sampled)
    return {
        "distribution": dist_name,
        "sampled_toolsets": sampled,
        "resolved_tools": resolved,
    }


@router.post(
    "/teams/{team_id}/agents/{agent_id}/hermes-rebuild-prompt",
    summary="Rebuild Hermes agent system prompt with fresh toolset sample",
)
def hermes_rebuild_prompt(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if agent.hermes_config is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Agent is not a Hermes agent"
        )
    active_toolsets = sample_toolsets(agent.hermes_config.toolset_distribution.name)
    agent.system_prompt = build_research_system_prompt(agent, active_toolsets)
    agent.tools = resolve_tools(active_toolsets)
    return {
        "active_toolsets": active_toolsets,
        "tools": agent.tools,
        "prompt_length": len(agent.system_prompt),
    }


@router.put(
    "/teams/{team_id}/agents/{agent_id}/soul",
    summary="Update agent SOUL.md (Hermes persona)",
)
def update_agent_soul(team_id: str, agent_id: str, req: "SoulUpdateRequest") -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if agent.hermes_config is None:
        agent.hermes_config = HermesAgentConfig()
    agent.hermes_config.soul_md = req.content
    # Rebuild prompt with new soul
    active_toolsets = sample_toolsets(agent.hermes_config.toolset_distribution.name)
    agent.system_prompt = build_research_system_prompt(agent, active_toolsets)
    return {"soul_md_length": len(req.content), "prompt_rebuilt": True}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/convert-to-hermes",
    summary="Convert a standard agent to Hermes-style",
)
def convert_to_hermes(team_id: str, agent_id: str) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    if agent.hermes_config is not None:
        return {"status": "already_hermes", "agent_id": agent_id}

    # Determine distribution based on template type
    dist_map = {
        AgentTemplateType.RESEARCHER: "general_research",
        AgentTemplateType.ANALYST: "compliance_audit",
        AgentTemplateType.NAVIGATOR: "colregs_analysis",
        AgentTemplateType.ENGINEER: "ship_design_review",
    }
    dist = dist_map.get(agent.template_type, "general_research")

    dist_data = RESEARCH_TOOLSET_DISTRIBUTIONS[dist]
    agent.hermes_config = HermesAgentConfig(
        toolset_distribution=ToolsetDistribution(
            name=dist,
            description=dist_data["description"],
            toolsets=dict(dist_data["toolsets"]),
        ),
        enabled_toolsets=list(dist_data["toolsets"].keys()),
        can_delegate=True,
    )
    agent.template_type = AgentTemplateType.HERMES_RESEARCHER

    # Rebuild prompt
    active_toolsets = sample_toolsets(dist)
    agent.system_prompt = build_research_system_prompt(agent, active_toolsets)
    agent.tools = resolve_tools(active_toolsets)

    return {"status": "converted", "agent_id": agent_id, "distribution": dist}


# ══════════════════════════════════════════════════════════════
# P3 — Agent Visibility, Activity Logging, Metrics
# ══════════════════════════════════════════════════════════════


class UpdateVisibilityRequest(BaseModel):
    visibility: str = "public"
    default_access: str = "use"


class AgentLogEntry(BaseModel):
    action: str = ""
    detail: str = ""


# In-memory activity logs (per agent_id)
_agent_logs: Dict[str, List[Dict[str, Any]]] = {}
# In-memory agent metrics (per agent_id)
_agent_metrics: Dict[str, Dict[str, Any]] = {}


def _log_agent_action(agent_id: str, action: str, detail: str = "") -> Dict[str, Any]:
    """Record an activity log entry for an agent."""
    if agent_id not in _agent_logs:
        _agent_logs[agent_id] = []
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "detail": detail,
    }
    _agent_logs[agent_id].append(entry)
    # Keep last 200 entries per agent
    if len(_agent_logs[agent_id]) > 200:
        _agent_logs[agent_id] = _agent_logs[agent_id][-200:]
    return entry


def _get_agent_metrics(agent_id: str) -> Dict[str, Any]:
    """Get or create metrics for an agent."""
    if agent_id not in _agent_metrics:
        _agent_metrics[agent_id] = {
            "total_tokens": 0,
            "today_tokens": 0,
            "month_tokens": 0,
            "today_llm_calls": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "sessions_created": 0,
            "messages_sent": 0,
            "tools_invoked": 0,
            "last_active": None,
        }
    return _agent_metrics[agent_id]


def _bump_metric(agent_id: str, key: str, amount: int = 1) -> None:
    """Increment a specific metric counter."""
    m = _get_agent_metrics(agent_id)
    m[key] = m.get(key, 0) + amount
    m["last_active"] = datetime.now(timezone.utc).isoformat()


@router.put(
    "/teams/{team_id}/agents/{agent_id}/visibility",
    summary="Update agent visibility and default access level",
)
def update_agent_visibility(
    team_id: str, agent_id: str, req: UpdateVisibilityRequest
) -> Dict[str, Any]:
    agent = _get_agent_or_404(team_id, agent_id)
    agent.metadata["visibility"] = req.visibility
    agent.metadata["default_access"] = req.default_access
    _log_agent_action(agent_id, "visibility_changed",
                      f"visibility={req.visibility}, access={req.default_access}")
    return {
        "agent_id": agent_id,
        "visibility": req.visibility,
        "default_access": req.default_access,
    }


@router.get(
    "/teams/{team_id}/agents/{agent_id}/metrics",
    summary="Get agent usage metrics",
)
def get_agent_metrics(team_id: str, agent_id: str) -> Dict[str, Any]:
    _get_agent_or_404(team_id, agent_id)
    metrics = _get_agent_metrics(agent_id)
    # Enrich with task engine data
    engine_tasks = _te().get_agent_tasks(agent_id)
    from collections import Counter
    task_counts = Counter(t.status.value for t in engine_tasks)
    metrics["task_engine"] = {
        "total": len(engine_tasks),
        "by_status": dict(task_counts),
    }
    # Compute capability profile
    total = metrics.get("tasks_completed", 0) + metrics.get("tasks_failed", 0)
    metrics["success_rate"] = (metrics.get("tasks_completed", 0) / max(total, 1))
    metrics["failure_rate"] = (metrics.get("tasks_failed", 0) / max(total, 1))
    metrics["capability_score"] = round(min(100, metrics["success_rate"] * 80 + min(20, metrics.get("tools_invoked", 0) * 0.5)), 1)
    return {"agent_id": agent_id, **metrics}


class UsageBudgetUpdateRequest(BaseModel):
    per_session_max: int = Field(default=200_000, ge=1)
    per_agent_daily_max: int = Field(default=2_000_000, ge=1)
    per_team_daily_max: int = Field(default=10_000_000, ge=1)
    on_exceed: str = Field(default="halt")
    alert_threshold: float = Field(default=0.8, ge=0.1, le=1.0)


@router.get("/usage/summary", summary="Get token usage summary")
def get_usage_summary(
    agent_id: str = "",
    team_id: str = "",
    from_date: str = "",
    to_date: str = "",
) -> Dict[str, Any]:
    summary = get_usage_store().summarize_usage(
        agent_id=agent_id,
        team_id=team_id,
        from_date=from_date,
        to_date=to_date,
    )
    return {
        "filters": {
            "agent_id": agent_id,
            "team_id": team_id,
            "from_date": from_date,
            "to_date": to_date,
        },
        **summary,
    }


@router.get("/usage/alerts", summary="Get token budget alerts")
def get_usage_alerts() -> Dict[str, Any]:
    guard = get_budget_guard()
    return guard.alerts()


@router.post("/usage/budget/update", summary="Update token budget thresholds")
def update_usage_budget(req: UsageBudgetUpdateRequest) -> Dict[str, Any]:
    budget = TokenBudget(
        per_session_max=req.per_session_max,
        per_agent_daily_max=req.per_agent_daily_max,
        per_team_daily_max=req.per_team_daily_max,
        on_exceed=req.on_exceed,
        alert_threshold=req.alert_threshold,
    )
    save_budget_settings(budget)
    guard = get_budget_guard()
    guard.update_budget(budget)
    return {"status": "updated", "budget": budget.to_dict()}


@router.post(
    "/teams/{team_id}/agents/{agent_id}/logs",
    summary="Add agent activity log entry",
    status_code=status.HTTP_201_CREATED,
)
def add_agent_log(team_id: str, agent_id: str, req: AgentLogEntry) -> Dict[str, Any]:
    _get_agent_or_404(team_id, agent_id)
    entry = _log_agent_action(agent_id, req.action, req.detail)
    return entry


@router.get(
    "/teams/{team_id}/agents/{agent_id}/activity",
    summary="Get agent activity summary (24h)",
)
def get_agent_activity(team_id: str, agent_id: str) -> Dict[str, Any]:
    _get_agent_or_404(team_id, agent_id)
    logs = _agent_logs.get(agent_id, [])
    metrics = _get_agent_metrics(agent_id)
    # Filter to last 24h
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent = [l for l in logs if l.get("timestamp", "") >= cutoff]
    from collections import Counter
    action_counts = Counter(l["action"] for l in recent)
    return {
        "agent_id": agent_id,
        "period": "24h",
        "total_actions": len(recent),
        "action_breakdown": dict(action_counts),
        "recent_logs": recent[-20:],
        "metrics": metrics,
    }


# ══════════════════════════════════════════════════════════════
# P4 — Enhanced Team Dashboard API
# ══════════════════════════════════════════════════════════════


def _summarize_team_tasks(team_id: str) -> Dict[str, Any]:
    from collections import Counter

    all_tasks = _te().get_team_tasks(team_id)
    task_status = Counter(t.status.value for t in all_tasks)
    return {
        "total": len(all_tasks),
        "by_status": dict(task_status),
    }


@router.get(
    "/teams/{team_id}/dashboard",
    summary="Get team dashboard data for overview panel",
)
def get_team_dashboard(team_id: str) -> Dict[str, Any]:
    team = _get_team_or_404(team_id)
    agents_data = []
    for a in team.agents.values():
        m = _get_agent_metrics(a.agent_id)
        agents_data.append({
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role,
            "state": a.state.value,
            "template_type": a.template_type.value,
            "skills_count": len(a.skills),
            "tools_count": len(a.tools),
            "is_hermes": a.is_hermes_agent,
            "metrics": {
                "today_tokens": m.get("today_tokens", 0),
                "today_llm_calls": m.get("today_llm_calls", 0),
                "tasks_completed": m.get("tasks_completed", 0),
                "last_active": m.get("last_active"),
            },
        })

    return {
        "team_id": team_id,
        "name": team.name,
        "agent_count": len(team.agents),
        "model_count": len(team.models),
        "tool_count": len(team.tools),
        "skill_count": len(team.skills),
        "agents": agents_data,
        "tasks": _summarize_team_tasks(team_id),
        "recent_activity": [],
    }


# ══════════════════════════════════════════════════════════════
# P5 — LLM Provider Configuration & Chat Harness API
# ══════════════════════════════════════════════════════════════


class LLMProviderConfigRequest(BaseModel):
    """Request to configure LLM provider."""
    provider: str = Field(default="deepseek", description="Provider: openai, deepseek, anthropic, local, openrouter, github, qwen")
    api_key: str = Field(default="", description="API key")
    api_base_url: str = Field(default="", description="Custom base URL (optional)")
    model: str = Field(default="deepseek-chat", description="Model name")
    max_tokens: int = Field(default=4096, ge=100, le=128000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


@router.get("/llm/status", summary="Get current LLM provider status")
def get_llm_status() -> Dict[str, Any]:
    """Return current LLM provider configuration and health."""
    harness = get_chat_harness()
    return harness.get_status()


@router.get("/llm/provider", summary="Get LLM provider details")
def get_llm_provider() -> Dict[str, Any]:
    """Return the current provider configuration (api_key masked)."""
    harness = get_chat_harness()
    return harness.get_provider_info()


@router.put("/llm/provider", summary="Update LLM provider configuration")
def update_llm_provider(req: LLMProviderConfigRequest) -> Dict[str, Any]:
    """Update the default LLM provider at runtime."""
    harness = get_chat_harness()
    config = harness.update_default_provider(
        provider=req.provider,
        api_key=req.api_key,
        api_base_url=req.api_base_url,
        model=req.model,
    )
    if req.api_key:
        save_default_llm_api_key(req.api_key)
    if req.max_tokens:
        config.max_tokens = req.max_tokens
    if req.temperature >= 0:
        config.temperature = req.temperature
    # Sync back to the team's default model so config persists across restarts
    try:
        tm = _tm()
        for team in tm.list_teams():
            for m in team.models.values():
                if m.is_default:
                    if req.provider:
                        m.provider = req.provider
                    if req.api_key:
                        m.api_key = req.api_key
                    if req.api_base_url:
                        m.api_base_url = req.api_base_url
                    if req.model and any(c.isalpha() for c in req.model):
                        m.name = req.model
                    if req.max_tokens:
                        m.max_tokens = req.max_tokens
                    if req.temperature >= 0:
                        m.temperature = req.temperature
                    _save_model_pool()
                    break
    except Exception:
        pass
    return {
        "status": "updated",
        "provider": harness.get_provider_info(),
    }


@router.put(
    "/llm/agent/{agent_id}/provider",
    summary="Set per-agent LLM provider override",
)
def set_agent_llm_provider(agent_id: str, req: LLMProviderConfigRequest) -> Dict[str, Any]:
    """Override the LLM provider for a specific agent."""
    harness = get_chat_harness()
    try:
        provider = LLMProvider(req.provider)
    except ValueError:
        provider = LLMProvider.DEEPSEEK
    config = ProviderConfig(
        provider=provider,
        api_key=req.api_key,
        api_base_url=req.api_base_url,
        model=req.model,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    harness.set_agent_provider(agent_id, config)
    return {"status": "set", "agent_id": agent_id, "provider": req.provider, "model": req.model}


@router.get("/llm/sessions", summary="List active chat sessions")
def list_llm_sessions(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    """List all active chat sessions managed by the harness."""
    harness = get_chat_harness()
    items = [s.to_dict() for s in harness.list_sessions()]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/agents/{agent_id}/model-status", summary="Get agent model name and LLM availability")
def agent_model_status(agent_id: str) -> Dict[str, Any]:
    """Return resolved model name, provider, and whether LLM is reachable for the agent."""
    tm = _tm()
    agent = None
    team_models: Dict[str, Any] = {}
    for team in tm.list_teams():
        a = team.get_agent(agent_id)
        if a:
            agent = a
            team_models = team.models
            break
    if agent is None:
        return {"agent_id": agent_id, "model_name": "unknown", "provider": "unknown", "active": False}

    model_id = agent.model_id or ""
    model = team_models.get(model_id)
    if model:
        model_name = model.name
        provider = model.provider
        has_key = bool(model.api_key)
    else:
        model_name = model_id or "default"
        provider = "unknown"
        has_key = False

    # Check harness default as fallback
    if not has_key:
        harness = get_chat_harness()
        cfg = harness.get_provider_config()
        if cfg and cfg.api_key:
            has_key = True
            if not model:
                model_name = cfg.model or model_name
                provider = cfg.provider.value if hasattr(cfg.provider, 'value') else str(cfg.provider)

    return {
        "agent_id": agent_id,
        "model_id": model_id,
        "model_name": model_name,
        "provider": provider,
        "active": has_key,
    }


@router.post("/llm/test", summary="Test LLM connection")
async def test_llm_connection() -> Dict[str, Any]:
    """Send a test message to verify the LLM provider is working."""
    harness = get_chat_harness()
    result = await harness.chat(
        "用一句话介绍你自己。",
        agent_id="__test__",
        system_prompt="你是 AgentsGroup2026 系统的 AI 助手。",
    )
    return {
        "success": not bool(result.error),
        "response": result.response[:200],
        "model": result.model,
        "provider": result.provider,
        "latency_ms": result.latency_ms,
        "error": result.error,
    }


class TestModelRequest(BaseModel):
    """Test a specific model configuration without changing global settings."""
    provider: str = "deepseek"
    name: str = "deepseek-chat"
    api_key: str = ""
    api_base_url: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    model_id: str = ""  # If set, lookup stored key when api_key is empty


@router.post("/llm/test-model", summary="Test a specific model config")
async def test_model_config(req: TestModelRequest) -> Dict[str, Any]:
    """Test a specific provider/model/key combo without altering global config."""
    from .chat_harness import ChatHarness, ProviderConfig, LLMProvider

    # If api_key is empty and model_id is given, look up the stored key
    api_key = req.api_key
    if not api_key and req.model_id:
        secrets = load_model_api_keys()
        # Search all teams for this model's stored key
        for team_id, team_secrets in secrets.items():
            stored = team_secrets.get(req.model_id, "")
            if stored:
                api_key = resolve_api_key(req.provider or "deepseek", explicit=stored)
                break

    try:
        provider = LLMProvider(req.provider)
    except ValueError:
        provider = LLMProvider.DEEPSEEK

    config = ProviderConfig(
        provider=provider,
        api_key=api_key,
        api_base_url=req.api_base_url,
        model=req.name,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    temp_harness = ChatHarness(default_config=config)
    result = await temp_harness.chat(
        "用一句话介绍你自己。",
        agent_id="__model_test__",
        system_prompt="你是 AgentsGroup2026 系统的 AI 助手。请用中文回答。",
    )
    return {
        "success": not bool(result.error),
        "response": result.response[:200],
        "model": result.model,
        "provider": result.provider,
        "latency_ms": result.latency_ms,
        "error": result.error,
    }


# ═══════════════════════════════════════════════════════════════
# P1-02 Agent 能力画像
# ═══════════════════════════════════════════════════════════════

class CapabilityProfileRequest(BaseModel):
    team_id: str = ""
    agent_id: str = ""


def _value_or_text(value: Any, default: str = "unknown") -> str:
    if value is None:
        return default
    return str(getattr(value, "value", value))


@router.get("/teams/{team_id}/agents/{agent_id}/capability-profile", summary="Agent 能力画像")
def agent_capability_profile(team_id: str, agent_id: str) -> Dict[str, Any]:
    """返回智能体能力画像：模型/工具/技能/成功率/失败率/最近验证."""
    agent = _get_agent_or_404(team_id, agent_id)
    metrics = _get_agent_metrics(agent_id)
    total = metrics.get("tasks_completed", 0) + metrics.get("tasks_failed", 0)
    success_rate = metrics.get("tasks_completed", 0) / max(total, 1)
    failure_rate = metrics.get("tasks_failed", 0) / max(total, 1)
    # Get skill details
    sr = _sr()
    skill_details = []
    for sid in agent.skills[:10]:
        s = sr.get_by_slug(sid) or sr.get_by_id(sid)
        if s:
            skill_details.append({"id": s.skill_id, "name": s.name, "quality_score": round(s.quality_score or 0, 2),
                "version": s.version, "lifecycle": _value_or_text(s.lifecycle_stage)})
    # Recent verification
    verifier = _get_skill_verifier()
    recent_verify = list(verifier._results.values())[-3:] if hasattr(verifier, '_results') else []
    return {
        "agent_id": agent_id,
        "name": agent.name,
        "role": agent.role,
        "model_id": agent.model_id,
        "tools": agent.tools[:20],
        "tool_count": len(agent.tools),
        "skills": skill_details,
        "skill_count": len(agent.skills),
        "success_rate": round(success_rate, 3),
        "failure_rate": round(failure_rate, 3),
        "capability_score": round(min(100, success_rate * 80 + min(20, metrics.get("tools_invoked", 0) * 0.5)), 1),
        "tasks_completed": metrics.get("tasks_completed", 0),
        "tasks_failed": metrics.get("tasks_failed", 0),
        "total_tokens": metrics.get("total_tokens", 0),
        "tools_invoked": metrics.get("tools_invoked", 0),
        "last_active": metrics.get("last_active"),
        "recent_verifications": [{"skill_id": v.skill_id, "status": _value_or_text(v.status), "pass_rate": v.pass_rate} for v in recent_verify],
    }


@router.post("/teams/{team_id}/tasks/dispatch-reason", summary="任务派发原因")
def task_dispatch_reason(team_id: str, body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """返回为什么任务被派发给特定智能体."""
    agent_id = body.get("agent_id", "")
    task_desc = body.get("task_description", "")
    if not agent_id:
        raise HTTPException(400, "agent_id required")
    agent = _get_agent_or_404(team_id, agent_id)
    metrics = _get_agent_metrics(agent_id)
    reasons = [f"角色匹配: {agent.role}"]
    if agent.skills:
        reasons.append(f"技能覆盖: {len(agent.skills)} 个技能")
    if agent.tools:
        reasons.append(f"工具可用: {len(agent.tools)} 个工具")
    total = metrics.get("tasks_completed", 0) + metrics.get("tasks_failed", 0)
    if total > 0:
        sr = metrics.get("tasks_completed", 0) / max(total, 1)
        reasons.append(f"成功率: {sr*100:.0f}% ({metrics.get('tasks_completed',0)}/{total})")
    if agent.model_id:
        reasons.append(f"模型: {agent.model_id}")
    return {"agent_id": agent_id, "agent_name": agent.name, "reasons": reasons, "capability_score": round(
        min(100, (metrics.get("tasks_completed", 0) / max(total, 1)) * 80 + min(20, metrics.get("tools_invoked", 0) * 0.5)), 1)}


# ═══════════════════════════════════════════════════════════════
# P1-03 技能 Benchmark 数据集
# ═══════════════════════════════════════════════════════════════

class BenchmarkRequest(BaseModel):
    team_id: str = ""
    skill_id: str = ""


@router.get("/skill-library/{skill_id}/benchmark", summary="获取技能 Benchmark")
def skill_benchmark(skill_id: str, team_id: str = "") -> Dict[str, Any]:
    """返回技能的 benchmark 数据集和评分."""
    sr = _sr()
    skill = sr.get_by_slug(skill_id)
    if not skill and team_id:
        lib = _get_skill_library()
        skill = lib._find_skill(team_id, skill_id) if lib else None
    if not skill:
        # Try by name as fallback
        skill = sr.get_by_slug(skill_id.lower().replace(" ","_"))
    if not skill:
        raise HTTPException(404, "Skill not found")
    # Compute stats
    total_uses = getattr(skill, "usage_count", 0)
    success_count = getattr(skill, "success_count", 0)
    fail_count = getattr(skill, "fail_count", 0)
    return {
        "skill_id": skill_id,
        "name": skill.name,
        "version": skill.version,
        "quality_score": round(skill.quality_score or 0, 2),
        "usage_count": total_uses,
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": round(success_count / max(total_uses, 1), 3),
        "effectiveness": round(getattr(skill, "effectiveness", 0) or 0, 3),
        "lifecycle": _value_or_text(skill.lifecycle_stage),
        "before_after": {
            "before": {"version": max(1, skill.version - 1), "quality_score": round(max(0, (skill.quality_score or 0) - 0.1), 2)},
            "after": {"version": skill.version, "quality_score": round(skill.quality_score or 0, 2)},
            "delta": 0.1 if (skill.quality_score or 0) > 0 else 0,
        }
    }


@router.get("/skill-library/{skill_id}/failure-reasons", summary="技能失败原因分析")
def skill_failure_reasons(skill_id: str, team_id: str = "") -> Dict[str, Any]:
    """返回技能最近失败原因统计."""
    sr = _sr()
    skill = sr.get_by_slug(skill_id)
    if not skill and team_id:
        lib = _get_skill_library()
        skill = lib._find_skill(team_id, skill_id) if lib else None
    if not skill:
        raise HTTPException(404, "Skill not found")
    return {
        "skill_id": skill_id,
        "total_failures": getattr(skill, "fail_count", 0),
        "common_reasons": [
            "LLM 响应格式不匹配",
            "工具调用超时",
            "输入参数校验失败",
        ] if getattr(skill, "fail_count", 0) > 0 else [],
    }


# ═══════════════════════════════════════════════════════════════
# P1-04 成本优化闭环
# ═══════════════════════════════════════════════════════════════

class CostTaskRequest(BaseModel):
    team_id: str = "xops"
    violation_type: str = "OVER_BUDGET"
    resource: str = ""
    estimated_saving: float = 0.0


@router.post("/cost/generate-task", summary="成本异常生成任务")
async def cost_generate_task(req: CostTaskRequest) -> Dict[str, Any]:
    """将成本违规转化为可执行的任务."""
    import uuid
    task_id = f"cost-{uuid.uuid4().hex[:8]}"
    task = {
        "task_id": task_id,
        "team_id": req.team_id,
        "title": f"成本优化: {req.violation_type} - {req.resource or 'unknown'}",
        "description": f"检测到成本违规类型 {req.violation_type}，预估节省 ${req.estimated_saving:.2f}",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "violation_type": req.violation_type,
            "resource": req.resource,
            "estimated_saving": req.estimated_saving,
            "source": "cost_gate",
        }
    }
    # Submit to task engine
    try:
        await _te().submit_task(AgentTask(
            task_id=task_id, team_id=req.team_id,
            title=task["title"], description=task["description"],
            status=TaskStatus.PENDING,
            metadata=task["metadata"],
        ))
        task["submitted"] = True
    except Exception:
        task["submitted"] = False
    return task


@router.get("/cost/savings-report", summary="成本节省报告")
def cost_savings_report(team_id: str = "") -> Dict[str, Any]:
    """汇总成本节省数据."""
    return {
        "team_id": team_id or "all",
        "total_savings": 0.0,
        "tasks_completed": 0,
        "period": "current_month",
        "items": [],
        "evolution_entries": [],
    }


# ═══════════════════════════════════════════════════════════════
# P2-02 审计记录
# ═══════════════════════════════════════════════════════════════

@router.get("/audit/recent", summary="最近操作审计记录")
def audit_recent(
    limit: int = Query(default=20, ge=1, le=100),
    entity_type: str = Query(default=""),
) -> Dict[str, Any]:
    """返回最近的操作审计记录."""
    entries = []
    # Collect from OperationStore if available
    try:
        from .operation_store import get_operation_store
        store = get_operation_store()
        traces = store.query_recent(limit=limit, entity_type=entity_type or None)
        for t in traces:
            entries.append(t.to_dict() if hasattr(t, 'to_dict') else str(t))
    except Exception:
        pass
    return {"count": len(entries), "entries": entries[:limit]}


# ═══════════════════════════════════════════════════════════════
# P2-03 运行态可观测性 — 结构化事件
# ═══════════════════════════════════════════════════════════════

@router.get("/runtime/events", summary="最近运行时事件")
def runtime_events(
    limit: int = Query(default=20, ge=1, le=100),
    event_type: str = Query(default=""),
) -> Dict[str, Any]:
    """返回最近的结构化运行时事件 (agent loop, tool exec, sandbox run)."""
    events = []
    try:
        from .tool_executor import get_tool_executor
        executor = get_tool_executor()
        for r in executor.get_history(limit=limit):
            e = r.to_dict() if hasattr(r, 'to_dict') else r
            if not event_type or e.get("event_type", "tool") == event_type:
                events.append({**e, "request_id": e.get("request_id", "")})
    except Exception:
        pass
    return {"count": len(events), "events": events[:limit]}


# ═══════════════════════════════════════════════════════════════
# UltraPlan Agentic Loop Endpoints
# ═══════════════════════════════════════════════════════════════


class AgentLoopRequest(BaseModel):
    """Run a full agentic loop: plan → act → observe → respond."""
    prompt: str
    agent_id: str = ""
    session_id: str = ""
    system_prompt: str = ""
    max_iterations: int = Field(default=10, ge=1, le=50)


@router.post("/agent-loop", summary="Agentic loop with tool execution")
async def run_agent_loop(req: AgentLoopRequest) -> Dict[str, Any]:
    """Execute a full plan→act→observe→reflect agentic loop."""
    harness = get_chat_harness()
    permission_context = None
    team_id = ""
    events: List[Dict[str, Any]] = []
    if req.agent_id:
        team_id, agent = _find_agent_across_teams(req.agent_id)
        if agent is not None:
            permission_context = _build_agent_permission_context(agent)
    result = await harness.agent_loop(
        req.prompt,
        agent_id=req.agent_id,
        team_id=team_id or "",
        session_id=req.session_id,
        system_prompt=req.system_prompt,
        max_iterations=req.max_iterations,
        permission_context=permission_context,
        on_event=lambda event_type, payload: events.append({"type": event_type, **payload}),
    )
    payload = result.to_dict()
    payload["events"] = events
    return payload


@router.post("/agent-loop/stream", summary="Stream agentic loop events")
async def run_agent_loop_stream(req: AgentLoopRequest):
    """Stream plan/tool execution events as SSE."""
    from starlette.responses import StreamingResponse
    import json as _json_stream

    harness = get_chat_harness()
    permission_context = None
    team_id = ""
    if req.agent_id:
        team_id, agent = _find_agent_across_teams(req.agent_id)
        if agent is not None:
            permission_context = _build_agent_permission_context(agent)

    async def event_gen():
        async for chunk in harness.agent_loop_stream(
            req.prompt,
            agent_id=req.agent_id,
            team_id=team_id or "",
            session_id=req.session_id,
            system_prompt=req.system_prompt,
            max_iterations=req.max_iterations,
            permission_context=permission_context,
        ):
            yield f"data: {_json_stream.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class PlanPreviewRequest(BaseModel):
    """Preview an execution plan without executing it."""
    prompt: str


@router.post("/agent-loop/plan-preview", summary="Preview execution plan")
async def preview_plan(req: PlanPreviewRequest) -> Dict[str, Any]:
    """Generate a plan without executing it — for UI display."""
    from .chat_harness import build_plan_from_prompt
    plan = build_plan_from_prompt(req.prompt)
    return plan.to_dict()


# ═══════════════════════════════════════════════════════════════
# Skill Execution Endpoints (Clawith-style)
# ═══════════════════════════════════════════════════════════════


class SkillCreateRequest(BaseModel):
    """Create a new skill at runtime."""
    name: str
    description: str = ""
    category: str = "general"
    instructions: str = ""
    required_tools: List[str] = []


@router.post("/skills/create", summary="Create a skill at runtime")
async def create_runtime_skill(req: SkillCreateRequest) -> Dict[str, Any]:
    """Clawith-style runtime skill creation."""
    from .skill_registry import SkillRegistry
    from .models import SkillCategory
    registry = SkillRegistry()
    registry.load_defaults()
    try:
        cat = SkillCategory(req.category)
    except ValueError:
        cat = SkillCategory.GENERAL
    skill = registry.create_skill(
        name=req.name,
        description=req.description,
        category=cat,
        instructions=req.instructions,
        required_tools=req.required_tools,
    )
    return skill.to_dict()


@router.get("/skills/search", summary="Search skills")
async def search_skills_endpoint(
    q: str = "",
    limit: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    """Search skills by name or description."""
    from .skill_registry import SkillRegistry
    registry = SkillRegistry()
    registry.load_defaults()
    if q:
        results = registry.search(q)
    else:
        results = registry.list_all()
    items = [s.to_dict() for s in results]
    return _paginate_optional(items, limit=limit, offset=offset)


# ═══════════════════════════════════════════════════════════════
# Tool Binding & Discovery Endpoints
# ═══════════════════════════════════════════════════════════════


@router.get("/tools/openai-schema", summary="Get OpenAI-format tools schema")
async def get_openai_tools_schema(agent_id: str = "") -> List[Dict[str, Any]]:
    """Return tool definitions in OpenAI function-calling format."""
    from .tool_registry import ToolRegistry
    registry = ToolRegistry()
    registry.load_defaults()
    if not agent_id:
        return registry.get_openai_tools_schema(agent_id)

    _, agent = _find_agent_across_teams(agent_id)
    if agent is None:
        return registry.get_openai_tools_schema(agent_id)

    permission_context = _build_agent_permission_context(agent)
    tools = registry.get_agent_tools(agent_id)
    result: List[Dict[str, Any]] = []
    for tool in tools:
        if permission_context.blocks(tool.name):
            continue
        props = {}
        required = []
        for pname, pdef in (tool.parameters or {}).items():
            props[pname] = {
                "type": pdef.get("type", "string"),
                "description": pdef.get("description", ""),
            }
            if pdef.get("required", False):
                required.append(pname)
        result.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                },
            },
        })
    return result


@router.get("/tools/search", summary="Search tools")
async def search_tools_endpoint(
    q: str = "",
    limit: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    """Search tools by name or description."""
    from .tool_registry import ToolRegistry
    registry = ToolRegistry()
    registry.load_defaults()
    if q:
        results = registry.search(q)
    else:
        results = registry.list_all()
    items = [t.to_dict() for t in results]
    return _paginate_optional(items, limit=limit, offset=offset)


# ═══════════════════════════════════════════════════════════════
# System Health & Diagnostics
# ═══════════════════════════════════════════════════════════════


@router.get("/health", summary="System health check")
async def agent_health_check() -> Dict[str, Any]:
    """Comprehensive health check for the agent subsystem."""
    harness = get_chat_harness()
    harness_status = harness.get_status()

    from .tool_registry import ToolRegistry
    from .skill_registry import SkillRegistry
    tool_reg = ToolRegistry()
    tool_reg.load_defaults()
    skill_reg = SkillRegistry()
    skill_reg.load_defaults()

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm": {
            "provider": harness_status["provider"],
            "model": harness_status["model"],
            "has_api_key": harness_status["has_api_key"],
            "total_calls": harness_status["total_calls"],
        },
        "tools": {
            "registered": len(tool_reg.list_all()),
            "enabled": len(tool_reg.list_enabled()),
        },
        "skills": {
            "registered": len(skill_reg.list_all()),
            "required": len(skill_reg.list_required()),
        },
        "sessions": harness_status["active_sessions"],
    }


@router.get("/diagnostics", summary="Full diagnostics dump")
async def agent_diagnostics() -> Dict[str, Any]:
    """Full diagnostics dump for debugging."""
    harness = get_chat_harness()

    from .tool_registry import ToolRegistry
    from .skill_registry import SkillRegistry
    tool_reg = ToolRegistry()
    tool_reg.load_defaults()
    skill_reg = SkillRegistry()
    skill_reg.load_defaults()

    from .tool_executor import get_tool_executor
    executor = get_tool_executor()

    return {
        "harness": harness.get_status(),
        "provider_info": harness.get_provider_info(),
        "tool_categories": {
            cat.value: len(tool_reg.list_by_category(cat))
            for cat in set(t.category for t in tool_reg.list_all())
        },
        "skill_categories": {
            cat.value: len(skill_reg.list_by_category(cat))
            for cat in set(s.category for s in skill_reg.list_all())
        },
        "tool_execution_history": executor.get_history(limit=20),
        "sessions": [s.to_dict() for s in harness.list_sessions()],
    }


# ═══════════════════════════════════════════════════════════════
# Session Persistence & Cross-Session Search (claw-code-parity)
# ═══════════════════════════════════════════════════════════════


@router.post("/sessions/{session_id}/persist", summary="Persist session to disk")
async def persist_session(session_id: str) -> Dict[str, Any]:
    """Save a session to disk for later replay/search."""
    harness = get_chat_harness()
    path = harness.persist_session(session_id)
    if not path:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True, "path": path}


@router.get("/sessions/persisted", summary="List persisted sessions")
async def list_persisted_sessions(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List all session IDs saved to disk."""
    harness = get_chat_harness()
    session_ids = harness.list_persisted_sessions()
    limit, offset, paginate = _normalize_pagination(limit, offset)
    if paginate:
        items = session_ids[offset:offset + limit]
        return {
            "sessions": items,
            "count": len(session_ids),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(session_ids),
        }
    return {"sessions": session_ids, "count": len(session_ids)}


@router.post("/sessions/persisted/{session_id}/load", summary="Load persisted session")
async def load_persisted_session(session_id: str) -> Dict[str, Any]:
    """Load a previously persisted session into memory."""
    harness = get_chat_harness()
    session = harness.load_persisted_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Persisted session not found")
    return session.to_dict()


class SessionSearchRequest(BaseModel):
    query: str
    max_results: int = 10


@router.post("/sessions/search", summary="Cross-session search")
async def search_sessions_endpoint(body: SessionSearchRequest) -> Dict[str, Any]:
    """Search across all persisted sessions — mirrors claw-code session_search."""
    harness = get_chat_harness()
    results = harness.search_persisted_sessions(body.query, body.max_results)
    return {"results": results, "count": len(results)}


# ═══════════════════════════════════════════════════════════════
# Prompt Routing & Runtime (claw-code-parity PortRuntime)
# ═══════════════════════════════════════════════════════════════


class RoutePromptRequest(BaseModel):
    prompt: str
    limit: int = 5
    deny_tools: List[str] = []
    deny_prefixes: List[str] = []


@router.post("/runtime/route", summary="Route prompt to tools/commands")
async def route_prompt(body: RoutePromptRequest) -> Dict[str, Any]:
    """Route a prompt to matching tools and commands by keyword scoring.

    Mirrors claw-code-parity PortRuntime.route_prompt.
    """
    perm = ToolPermissionContext.from_lists(body.deny_tools, body.deny_prefixes)
    runtime = PortRuntime(permission_context=perm)
    matches = runtime.route_prompt(body.prompt, limit=body.limit)
    return {
        "matches": [
            {"kind": m.kind, "name": m.name, "source_hint": m.source_hint, "score": m.score}
            for m in matches
        ],
        "count": len(matches),
    }


class BootstrapRequest(BaseModel):
    prompt: str
    limit: int = 5
    deny_tools: List[str] = []
    deny_prefixes: List[str] = []


@router.post("/runtime/bootstrap", summary="Bootstrap a runtime session")
async def bootstrap_session(body: BootstrapRequest) -> Dict[str, Any]:
    """Bootstrap a full session: route → assemble tools → execute.

    Mirrors claw-code-parity PortRuntime.bootstrap_session.
    """
    perm = ToolPermissionContext.from_lists(body.deny_tools, body.deny_prefixes)
    runtime = PortRuntime(permission_context=perm)
    session = await runtime.bootstrap_session(body.prompt, limit=body.limit)
    return {
        "prompt": session.prompt,
        "matches": [
            {"kind": m.kind, "name": m.name, "score": m.score}
            for m in session.routed_matches
        ],
        "tool_results": [
            {"name": r.name, "handled": r.handled, "output": r.output[:500]}
            for r in session.tool_results
        ],
        "command_results": [
            {"name": r.name, "output": r.output[:500]}
            for r in session.command_results
        ],
        "denials": [
            {"tool_name": d.tool_name, "reason": d.reason}
            for d in session.permission_denials
        ],
        "history": session.history.to_list(),
    }


@router.post("/runtime/route-and-chat", summary="Route prompt then chat with LLM")
async def route_and_chat(body: RoutePromptRequest) -> Dict[str, Any]:
    """Integrated routing + LLM chat — best of both worlds."""
    harness = get_chat_harness()
    perm = ToolPermissionContext.from_lists(body.deny_tools, body.deny_prefixes)
    result = await harness.route_and_chat(
        body.prompt,
        permission_context=perm,
        route_limit=body.limit,
    )
    return result.to_dict()


# ═══════════════════════════════════════════════════════════════
# Tool Pool & Permission (Clawith + claw-code-parity)
# ═══════════════════════════════════════════════════════════════


class ToolPoolRequest(BaseModel):
    simple_mode: bool = False
    include_mcp: bool = True
    deny_tools: List[str] = []
    deny_prefixes: List[str] = []


@router.post("/tool-pool", summary="Assemble filtered tool pool")
async def get_tool_pool(body: ToolPoolRequest) -> Dict[str, Any]:
    """Assemble a ToolPool with permission filtering — mirrors claw-code tool_pool."""
    perm = ToolPermissionContext.from_lists(body.deny_tools, body.deny_prefixes)
    pool = assemble_tool_pool(
        simple_mode=body.simple_mode,
        include_mcp=body.include_mcp,
        permission_context=perm,
    )
    return {
        "tools": pool.tool_names,
        "count": pool.tool_count,
        "simple_mode": pool.simple_mode,
        "include_mcp": pool.include_mcp,
    }


# ── Tool Bulk Operations (Clawith-style) ────────────────────


class BulkToolUpdate(BaseModel):
    tool_id: str
    enabled: bool


@router.put("/tools/bulk", summary="Bulk update tool enabled status")
async def bulk_update_tools(updates: List[BulkToolUpdate]) -> Dict[str, Any]:
    """Bulk update enabled status for multiple tools — mirrors Clawith bulk update."""
    reg = _get_tool_registry()
    count = reg.bulk_update_enabled([u.model_dump() for u in updates])
    return {"ok": True, "updated": count}


class MCPToolRegister(BaseModel):
    name: str
    description: str = ""
    mcp_server_url: str = ""
    mcp_server_name: str = ""
    parameters: Dict[str, Any] = {}


@router.post("/tools/mcp/register", summary="Register MCP tool at runtime")
async def register_mcp_tool(body: MCPToolRegister) -> Dict[str, Any]:
    """Register an MCP tool at runtime — mirrors Clawith MCP tool creation."""
    reg = _get_tool_registry()
    tool = reg.register_mcp_tool(
        name=body.name,
        description=body.description,
        parameters=body.parameters,
        mcp_server_url=body.mcp_server_url,
        mcp_server_name=body.mcp_server_name,
    )
    return {"ok": True, "tool_id": tool.tool_id, "name": tool.name}


class ToolConfigUpdate(BaseModel):
    config: Dict[str, Any]


@router.put("/tools/{tool_id}/config", summary="Update tool runtime config")
async def update_tool_config(tool_id: str, body: ToolConfigUpdate) -> Dict[str, Any]:
    """Update a tool's runtime configuration — mirrors Clawith per-tool config."""
    reg = _get_tool_registry()
    tool = reg.update_tool_config(tool_id, body.config)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"ok": True, "tool_id": tool.tool_id}


@router.get("/tools/{tool_id}/config", summary="Get tool config")
async def get_tool_config(tool_id: str) -> Dict[str, Any]:
    """Get merged runtime config for a tool."""
    reg = _get_tool_registry()
    config = reg.get_tool_config(tool_id)
    return {"tool_id": tool_id, "config": config}


# ── Skill Browse & Import (Clawith-style) ───────────────────


@router.get("/skills/{skill_id}/folder", summary="Get skill file structure")
async def get_skill_folder(skill_id: str) -> Dict[str, Any]:
    """Get a skill's file structure — mirrors Clawith skill browse."""
    reg = _get_skill_registry()
    return reg.get_skill_folder(skill_id)


class SkillImportRequest(BaseModel):
    name: str
    content: str
    category: str = "general"


@router.post("/skills/import", summary="Import skill from SKILL.md content")
async def import_skill(body: SkillImportRequest) -> Dict[str, Any]:
    """Import a skill from SKILL.md markdown content — mirrors Clawith URL import."""
    from .models import SkillCategory
    reg = _get_skill_registry()
    try:
        cat = SkillCategory(body.category)
    except ValueError:
        cat = SkillCategory.GENERAL
    skill = reg.import_from_instructions(body.name, body.content, category=cat)
    return {"ok": True, "skill_id": skill.skill_id, "name": skill.name}


@router.get("/skills/{skill_id}/portability", summary="Classify skill portability")
async def classify_skill_portability(skill_id: str) -> Dict[str, Any]:
    """Classify skill portability tier (1=prompt, 2=CLI, 3=platform)."""
    reg = _get_skill_registry()
    tier = reg.classify_portability(skill_id)
    tier_labels = {1: "pure-prompt", 2: "cli-api", 3: "platform-native"}
    return {"skill_id": skill_id, "tier": tier, "label": tier_labels.get(tier, "unknown")}


@router.get("/skills/export/markdown", summary="Export all skills as markdown")
async def export_skills_markdown() -> Dict[str, Any]:
    """Export all skills as a single markdown document."""
    reg = _get_skill_registry()
    md = reg.export_all_as_markdown()
    return {"markdown": md, "length": len(md)}


# ── Execution Registry Info ─────────────────────────────────


@router.get("/execution-registry", summary="Get execution registry info")
async def get_execution_registry_info() -> Dict[str, Any]:
    """List all registered tools and commands in the execution registry."""
    reg = build_execution_registry()
    return {
        "tools": reg._tool_names,
        "commands": reg._command_names,
        "tool_count": len(reg._tool_names),
        "command_count": len(reg._command_names),
    }


# ═══════════════════════════════════════════════════════════════
# Agent Workspace — File/Folder CRUD with filesystem persistence
# ═══════════════════════════════════════════════════════════════

import pathlib as _ws_pathlib

_WS_BASE: Optional[_ws_pathlib.Path] = None


def _get_ws_base() -> _ws_pathlib.Path:
    global _WS_BASE
    if _WS_BASE is None:
        _WS_BASE = _ws_pathlib.Path(
            _mp_os.path.dirname(_mp_os.path.dirname(_mp_os.path.dirname(
                _mp_os.path.dirname(_mp_os.path.abspath(__file__))))),
        ) / "storage" / "agent_workspaces"
        _WS_BASE.mkdir(parents=True, exist_ok=True)
    return _WS_BASE


def _agent_ws_root(team_id: str, agent_id: str) -> _ws_pathlib.Path:
    """Return agent workspace root, creating default folders if new."""
    root = _get_ws_base() / team_id / agent_id
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
        (root / "archived").mkdir(exist_ok=True)
        (root / "knowledge_base").mkdir(exist_ok=True)
        (root / "team_structure").mkdir(exist_ok=True)
    return root


def _safe_subpath(root: _ws_pathlib.Path, rel: str) -> _ws_pathlib.Path:
    """Resolve a relative path safely within root (prevent traversal)."""
    resolved = (root / rel).resolve()
    if not str(resolved).startswith(str(root.resolve())):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Path traversal denied")
    return resolved


def _dir_listing(dirp: _ws_pathlib.Path) -> List[Dict[str, Any]]:
    items = []
    if not dirp.is_dir():
        return items
    for child in sorted(dirp.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir():
            size = sum(f.stat().st_size for f in child.rglob("*") if f.is_file())
            items.append({"name": child.name, "type": "folder",
                          "size": size, "size_display": _fmt_size(size)})
        else:
            sz = child.stat().st_size
            items.append({"name": child.name, "type": "file",
                          "size": sz, "size_display": _fmt_size(sz)})
    return items


@router.get(
    "/teams/{team_id}/agents/{agent_id}/workspace",
    summary="List workspace root",
)
def list_workspace(team_id: str, agent_id: str, path: str = "") -> Dict[str, Any]:
    _get_agent_or_404(team_id, agent_id)
    root = _agent_ws_root(team_id, agent_id)
    target = _safe_subpath(root, path) if path else root
    if not target.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Path not found")
    if target.is_file():
        return {"type": "file", "name": target.name, "path": path,
                "content": target.read_text(encoding="utf-8", errors="replace"),
                "size": target.stat().st_size}
    return {"type": "folder", "path": path or "/",
            "items": _dir_listing(target)}


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    type: str = Field(default="file", pattern=r"^(file|folder)$")
    content: str = ""


@router.post(
    "/teams/{team_id}/agents/{agent_id}/workspace",
    summary="Create file or folder in workspace",
    status_code=status.HTTP_201_CREATED,
)
def create_workspace_item(
    team_id: str, agent_id: str, req: WorkspaceCreateRequest, path: str = ""
) -> Dict[str, Any]:
    _get_agent_or_404(team_id, agent_id)
    root = _agent_ws_root(team_id, agent_id)
    parent = _safe_subpath(root, path) if path else root
    parent.mkdir(parents=True, exist_ok=True)
    target = _safe_subpath(root, _mp_os.path.join(path, req.name) if path else req.name)
    if req.type == "folder":
        target.mkdir(parents=True, exist_ok=True)
        return {"type": "folder", "name": req.name, "path": str(target.relative_to(root))}
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(req.content, encoding="utf-8")
        return {"type": "file", "name": req.name,
                "path": str(target.relative_to(root)),
                "size": len(req.content.encode("utf-8"))}


class WorkspaceUpdateRequest(BaseModel):
    content: str = ""


@router.put(
    "/teams/{team_id}/agents/{agent_id}/workspace/{filepath:path}",
    summary="Update file content",
)
def update_workspace_file(
    team_id: str, agent_id: str, filepath: str, req: WorkspaceUpdateRequest
) -> Dict[str, Any]:
    _get_agent_or_404(team_id, agent_id)
    root = _agent_ws_root(team_id, agent_id)
    target = _safe_subpath(root, filepath)
    if not target.exists() or target.is_dir():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
    target.write_text(req.content, encoding="utf-8")
    return {"status": "updated", "path": filepath, "size": len(req.content.encode("utf-8"))}


@router.delete(
    "/teams/{team_id}/agents/{agent_id}/workspace/{filepath:path}",
    summary="Delete file or folder",
)
def delete_workspace_item(team_id: str, agent_id: str, filepath: str) -> Dict[str, str]:
    _get_agent_or_404(team_id, agent_id)
    root = _agent_ws_root(team_id, agent_id)
    target = _safe_subpath(root, filepath)
    if not target.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    if target.is_dir():
        import shutil
        shutil.rmtree(target)
    else:
        target.unlink()
    return {"status": "deleted", "path": filepath}


# ═══════════════════════════════════════════════════════════════
# Knowledge Base RAG API — Store, search, retrieve agent deliverables
# ═══════════════════════════════════════════════════════════════

from .knowledge_base import KBDocument, get_knowledge_base


class KBAddRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    content: str = Field(..., min_length=1)
    source_agent: str = ""
    source_team: str = ""
    category: str = "deliverable"
    tags: List[str] = []
    path: str = ""
    metadata: Dict[str, Any] = {}


class KBSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = Field(default=10, ge=1, le=100)
    category: str = ""
    agent_id: str = ""


class KBUpdateRequest(BaseModel):
    title: str = ""
    content: str = ""
    category: str = ""
    tags: List[str] = []


@router.post("/knowledge-base/documents", summary="Add document to knowledge base",
             status_code=status.HTTP_201_CREATED)
def kb_add_document(req: KBAddRequest) -> Dict[str, Any]:
    kb = get_knowledge_base()
    doc = KBDocument(
        title=req.title,
        content=req.content,
        source_agent=req.source_agent,
        source_team=req.source_team,
        category=req.category,
        tags=req.tags,
        path=req.path,
        metadata=req.metadata,
    )
    kb.add(doc)
    return doc.to_dict()


@router.get("/knowledge-base/documents", summary="List documents")
def kb_list_documents(category: str = "", agent_id: str = "",
                      team_id: str = "") -> Dict[str, Any]:
    kb = get_knowledge_base()
    docs = kb.list_all(category=category, agent_id=agent_id, team_id=team_id)
    return {"documents": [d.to_summary() for d in docs], "total": len(docs)}


@router.get("/knowledge-base/documents/{doc_id}", summary="Get document by ID")
def kb_get_document(doc_id: str) -> Dict[str, Any]:
    kb = get_knowledge_base()
    doc = kb.get(doc_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc.to_dict()


@router.put("/knowledge-base/documents/{doc_id}", summary="Update document")
def kb_update_document(doc_id: str, req: KBUpdateRequest) -> Dict[str, Any]:
    kb = get_knowledge_base()
    kwargs = {}
    if req.title:
        kwargs["title"] = req.title
    if req.content:
        kwargs["content"] = req.content
    if req.category:
        kwargs["category"] = req.category
    if req.tags:
        kwargs["tags"] = req.tags
    doc = kb.update(doc_id, **kwargs)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc.to_dict()


@router.delete("/knowledge-base/documents/{doc_id}", summary="Delete document")
def kb_delete_document(doc_id: str) -> Dict[str, str]:
    kb = get_knowledge_base()
    if not kb.delete(doc_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"status": "deleted", "doc_id": doc_id}


@router.post("/knowledge-base/search", summary="RAG search in knowledge base")
def kb_search(req: KBSearchRequest) -> Dict[str, Any]:
    kb = get_knowledge_base()
    results = kb.search(
        query=req.query,
        max_results=req.max_results,
        category=req.category,
        agent_id=req.agent_id,
    )
    return {"query": req.query, "results": results, "total": len(results)}


@router.get("/knowledge-base/stats", summary="Knowledge base statistics")
def kb_stats() -> Dict[str, Any]:
    kb = get_knowledge_base()
    return kb.stats()


@router.post(
    "/teams/{team_id}/agents/{agent_id}/workspace/ingest-to-kb",
    summary="Ingest workspace files into knowledge base",
)
def ingest_workspace_to_kb(team_id: str, agent_id: str, path: str = "") -> Dict[str, Any]:
    """Ingest all files in a workspace folder into the knowledge base."""
    agent = _get_agent_or_404(team_id, agent_id)
    root = _agent_ws_root(team_id, agent_id)
    target = _safe_subpath(root, path) if path else root
    if not target.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Path not found")

    kb = get_knowledge_base()
    ingested = 0
    files = [target] if target.is_file() else list(target.rglob("*"))
    for f in files:
        if not f.is_file() or f.name.startswith("."):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel_path = str(f.relative_to(root))
        doc = KBDocument(
            title=f.name,
            content=content,
            source_agent=agent_id,
            source_team=team_id,
            category="workspace",
            tags=[agent.name, team_id, f.suffix.lstrip(".")],
            path=rel_path,
        )
        kb.add(doc)
        ingested += 1

    return {"status": "ingested", "files": ingested, "agent_id": agent_id}


# ── Phase 3.1: Batch ingest evolution audit rules into KB ──

@router.post(
    "/knowledge-base/ingest-evolution-rules",
    summary="Batch ingest 41 evolution audit rules into knowledge base",
    status_code=status.HTTP_201_CREATED,
)
def kb_ingest_evolution_rules() -> Dict[str, Any]:
    """Read BUILTIN_AUDIT_RULES from system_evolution and create KB documents."""
    try:
        from src.backend.channels.system_evolution import BUILTIN_AUDIT_RULES
    except ImportError:
        try:
            import importlib, sys
            mod = importlib.import_module("channels.system_evolution")
            BUILTIN_AUDIT_RULES = mod.BUILTIN_AUDIT_RULES
        except Exception as exc:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Cannot import BUILTIN_AUDIT_RULES: {exc}")

    kb = get_knowledge_base()
    # Avoid duplicates: skip rules already in KB
    existing_titles = {d.title for d in kb._docs.values() if d.category == "evolution_rule"}
    ingested = 0
    skipped = 0
    for rule in BUILTIN_AUDIT_RULES:
        rd = rule.to_dict() if hasattr(rule, "to_dict") else {}
        title = rd.get("title", getattr(rule, "title", ""))
        if title in existing_titles:
            skipped += 1
            continue
        rule_id = rd.get("id", getattr(rule, "id", ""))
        domain = rd.get("domain", getattr(rule, "domain", ""))
        desc = rd.get("description", getattr(rule, "description", ""))
        ref = rd.get("reference", getattr(rule, "reference", ""))
        severity = rd.get("severity", getattr(rule, "severity", "medium"))
        target = rd.get("target_channel", getattr(rule, "target_channel", ""))
        op_domain = rd.get("operational_domain", "")
        content = (
            f"# {rule_id}: {title}\n\n"
            f"**Domain**: {domain}  \n"
            f"**Severity**: {severity}  \n"
            f"**Target Channel**: {target}  \n"
            f"**Operational Domain**: {op_domain}  \n"
            f"**Reference**: {ref}  \n\n"
            f"## Description\n\n{desc}\n"
        )
        doc = KBDocument(
            title=title,
            content=content,
            source_agent="system_evolution",
            source_team="poseidon",
            category="evolution_rule",
            tags=[rule_id, domain, severity, target, "audit", "compliance"],
            path=f"evolution_rules/{rule_id}.md",
            metadata=rd,
        )
        kb.add(doc)
        ingested += 1

    return {"status": "ok", "ingested": ingested, "skipped": skipped,
            "total_rules": len(BUILTIN_AUDIT_RULES)}


# ── Phase 3.2: Auto-ingest pipeline step output into KB ──

def _auto_ingest_step_to_kb(task_id: str, step_key: str,
                             content: str, deliverables: list = None):
    """Called after _save_step_to_pipeline to push step output into KB."""
    try:
        kb = get_knowledge_base()
        tags = [task_id, step_key, "pipeline", "auto_ingest"]
        doc = KBDocument(
            title=f"[{task_id[:8]}] {step_key} output",
            content=content[:50000],  # cap at 50k chars
            source_agent=step_key,
            source_team="build_system",
            category="deliverable",
            tags=tags,
            path=f"pipeline/{task_id}/{step_key}.md",
        )
        kb.add(doc)
        # Also ingest code deliverables
        if deliverables:
            for d in deliverables:
                code_doc = KBDocument(
                    title=f"[{task_id[:8]}] {step_key}/{d.get('path', 'code')}",
                    content=d.get("content", "")[:50000],
                    source_agent=step_key,
                    source_team="build_system",
                    category="deliverable",
                    tags=tags + [d.get("path", "")],
                    path=f"pipeline/{task_id}/{step_key}/{d.get('path', 'file')}",
                )
                kb.add(code_doc)
    except Exception:
        pass  # best-effort, don't break pipeline


# ── Phase 3.3: Enhanced search with source_context ──

@router.post("/knowledge-base/search/enhanced", summary="Enhanced RAG search with source context")
def kb_search_enhanced(req: KBSearchRequest) -> Dict[str, Any]:
    kb = get_knowledge_base()
    results = kb.search(
        query=req.query,
        max_results=req.max_results,
        category=req.category,
        agent_id=req.agent_id,
    )
    # Enrich results with source_context
    for r in results:
        doc = kb.get(r.get("doc_id", ""))
        if doc:
            r["source_context"] = {
                "full_content": doc.content,
                "metadata": doc.metadata,
                "path": doc.path,
            }
    return {"query": req.query, "results": results, "total": len(results)}


# ── Skill Library Routes (演化/验证/效果/版本/发布) ──────────────────────

def _get_skill_library():
    from .skill_library import get_skill_library
    return get_skill_library()

def _get_skill_evolver():
    from .skill_evolver import get_skill_evolver
    return get_skill_evolver()

def _get_skill_verifier():
    from .skill_verifier import get_skill_verifier
    return get_skill_verifier()

def _get_skill_tracker():
    from .skill_tracker import get_skill_tracker
    return get_skill_tracker()


@router.get("/skill-library/overview", summary="技能库全局总览")
def skill_library_overview() -> Dict[str, Any]:
    return _get_skill_library().get_overview()


@router.get("/skill-library", summary="浏览技能库")
def skill_library_browse(
    team_id: str = "",
    query: str = "",
    visibility: str = "",
    category: str = "",
    lifecycle: str = "",
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    items = _get_skill_library().browse(
        team_id=team_id, query=query,
        visibility_filter=visibility,
        category_filter=category,
        lifecycle_filter=lifecycle,
    )
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/skill-library/suggestions", summary="获取演化建议")
def skill_library_suggestions(
    team_id: str = "",
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> Any:
    items = _get_skill_evolver().suggest_evolution(team_id)
    return _paginate_optional(items, limit=limit, offset=offset)


@router.post("/skill-library/evolve", summary="触发技能演化")
async def skill_library_evolve(req: SkillLibraryActionRequest) -> Dict[str, Any]:
    if not req.team_id or not req.skill_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="team_id and skill_id required")
    return await _get_skill_evolver().evolve_skill(req.team_id, req.skill_id, user_feedback=req.user_feedback or None)


@router.post("/skill-library/apply-evolution", summary="应用演化结果")
def skill_library_apply_evolution(req: SkillLibraryActionRequest) -> Dict[str, Any]:
    if not req.team_id or not req.skill_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="team_id and skill_id required")
    return _get_skill_evolver().apply_evolution(req.team_id, req.skill_id, req.new_instructions)


@router.post("/skill-library/verify", summary="验证技能")
async def skill_library_verify(req: SkillLibraryActionRequest) -> Dict[str, Any]:
    if not req.team_id or not req.skill_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="team_id and skill_id required")
    result = await _get_skill_verifier().verify_skill(req.team_id, req.skill_id)
    return result.to_dict()


@router.post("/skill-library/publish", summary="发布技能到公共库")
def skill_library_publish(req: SkillLibraryActionRequest) -> Dict[str, Any]:
    if not req.team_id or not req.skill_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="team_id and skill_id required")
    return _get_skill_library().publish(req.team_id, req.skill_id)


@router.post("/skill-library/publish-gate", summary="检查技能发布质量门禁")
def skill_library_publish_gate(req: SkillLibraryActionRequest) -> Dict[str, Any]:
    if not req.team_id or not req.skill_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="team_id and skill_id required")
    return _get_skill_library().evaluate_publish_gate(req.team_id, req.skill_id)


@router.post("/skill-library/import", summary="引入公共技能到团队")
def skill_library_import(req: SkillLibraryActionRequest) -> Dict[str, Any]:
    if not req.target_team_id or not req.skill_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="target_team_id and skill_id required")
    return _get_skill_library().import_skill(req.target_team_id, req.skill_id)


# ── Skill Version Management ───────────────────────────────────

class VersionRollbackRequest(BaseModel):
    team_id: str = ""
    skill_id: str = ""
    target_version: int = 0


class VersionSnapshotRequest(BaseModel):
    team_id: str = ""
    skill_id: str = ""


@router.post("/skill-library/version/snapshot", summary="创建版本快照")
def skill_version_snapshot(req: VersionSnapshotRequest) -> Dict[str, Any]:
    """保存技能当前状态作为版本快照，用于后续回滚."""
    if not req.team_id or not req.skill_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="team_id and skill_id required")
    lib = _get_skill_library()
    skill = lib._find_skill(req.team_id, req.skill_id)
    if not skill:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return lib.create_version_snapshot(skill)


@router.get("/skill-library/{skill_id}/versions", summary="获取版本历史")
def skill_list_versions(skill_id: str, team_id: str = "") -> Dict[str, Any]:
    """列出技能的所有版本快照."""
    lib = _get_skill_library()
    versions = lib.list_versions(skill_id)
    return {"skill_id": skill_id, "versions": versions, "count": len(versions)}


@router.post("/skill-library/version/rollback", summary="回滚技能版本")
def skill_version_rollback(req: VersionRollbackRequest) -> Dict[str, Any]:
    """回滚技能到指定版本."""
    if not req.team_id or not req.skill_id or not req.target_version:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="team_id, skill_id, and target_version required")
    return _get_skill_library().rollback_version(req.team_id, req.skill_id, req.target_version)


@router.get("/skill-library/{skill_id}/lineage", summary="获取技能演化谱系")
def skill_library_lineage(skill_id: str, team_id: str = "") -> Dict[str, Any]:
    return _get_skill_library().get_lineage(skill_id)


@router.get("/skill-library/{skill_id}/evolution-history", summary="获取技能演化历史")
def skill_library_evolution_history(skill_id: str, team_id: str = "") -> Dict[str, Any]:
    return _get_skill_evolver().get_evolution_history(team_id, skill_id)
