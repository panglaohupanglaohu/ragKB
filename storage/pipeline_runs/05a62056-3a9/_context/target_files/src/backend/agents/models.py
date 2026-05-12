# -*- coding: utf-8 -*-
"""AgentsGroup2026 Agent Team Framework — Core Data Models.

Inspired by Clawith platform architecture:
- AgentTeam = Company (team-level resource sharing)
- AgentProfile = Employee (individual agent with personality/skills/permissions)
- ModelConfig = Model Pool entry
- ToolDefinition = Tool catalog entry
- SkillDefinition = Skill catalog entry
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ──────────────────────────────────────────────────────────────────


class AgentState(Enum):
    """Agent lifecycle states."""

    IDLE = "idle"
    WORKING = "working"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class ToolCategory(Enum):
    """Tool classification categories."""

    GENERAL = "general"
    BROWSER = "browser"
    CODE_EXECUTION = "code_execution"
    COMMUNICATION = "communication"
    FILE_OPERATION = "file_operation"
    TRIGGERS = "triggers"
    DISCOVERY = "discovery"
    DIGITAL_TWIN = "digital_twin"
    # Hermes-style tool categories
    WEB = "web"
    VISION = "vision"
    MEMORY = "memory"
    SKILLS = "skills"
    DELEGATION = "delegation"


class SkillCategory(Enum):
    """Skill classification categories."""

    GENERAL = "general"
    DIGITAL_TWIN = "digital_twin"
    AUTOMATION = "automation"
    # Hermes-style skill categories
    RESEARCH = "research"
    DOMAIN_KNOWLEDGE = "domain_knowledge"


class SkillLifecycleStage(Enum):
    """技能生命周期阶段 — 映射到Three.js结晶外观."""

    DRAFT = "draft"                # 胚胎: 半透明闪烁虚影球
    TEAM_LOCAL = "team_local"      # 新生: 微弱发光实体球
    PUBLISHED = "published"        # 发布: 明亮脉动球+光环
    VERIFIED = "verified"          # 验证: 稳定明亮+绿色验证环
    SOLIDIFIED = "solidified"      # 固化: 晶莹剔透+几何切面
    DEGRADED = "degraded"          # 退化: 暗淡+表面裂纹


class Visibility(Enum):
    """Visibility level for teams/agents."""

    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class AccessLevel(Enum):
    """Permission access levels."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class AgentTemplateType(Enum):
    """Predefined agent template types."""

    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    ENGINEER = "engineer"
    COORDINATOR = "coordinator"
    CUSTOM = "custom"
    # Hermes-style agent types
    HERMES_RESEARCHER = "hermes_researcher"
    HERMES_DEVELOPER = "hermes_developer"
    HERMES_CREATIVE = "hermes_creative"


# ── Dataclasses ────────────────────────────────────────────────────────────


@dataclass
class ModelConfig:
    """LLM model configuration entry."""

    model_id: str = ""
    provider: str = "anthropic"
    name: str = "claude-sonnet-4-20250514"
    max_tokens: int = 65536
    temperature: float = 0.7
    is_default: bool = False
    enabled: bool = True
    api_key: str = ""
    api_base_url: str = ""

    def __post_init__(self) -> None:
        if not self.model_id:
            self.model_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "name": self.name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "is_default": self.is_default,
            "enabled": self.enabled,
            "api_key": ("****" + self.api_key[-4:]) if len(self.api_key) >= 4 else ("****" if self.api_key else ""),
            "api_base_url": self.api_base_url,
            "has_api_key": bool(self.api_key),
        }


@dataclass
class ToolDefinition:
    """Tool catalog entry."""

    tool_id: str = ""
    name: str = ""
    description: str = ""
    category: ToolCategory = ToolCategory.BROWSER
    enabled: bool = True
    requires_approval: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)
    icon: str = "🔧"
    config_schema: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    is_default: bool = False
    source: str = "builtin"

    def __post_init__(self) -> None:
        if not self.tool_id:
            self.tool_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "enabled": self.enabled,
            "requires_approval": self.requires_approval,
            "parameters": self.parameters,
            "icon": self.icon,
            "config_schema": self.config_schema,
            "config": self.config,
            "is_default": self.is_default,
            "source": self.source,
        }


@dataclass
class SkillDefinition:
    """Skill catalog entry — with schema_version for cross-version compatibility."""

    skill_id: str = ""
    name: str = ""
    description: str = ""
    category: SkillCategory = SkillCategory.GENERAL
    required: bool = False
    enabled: bool = True
    icon: str = "⚡"
    config_schema: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    is_default: bool = False
    source: str = "builtin"
    slug: str = ""
    required_tools: List[str] = field(default_factory=list)
    instructions: str = ""
    schema_version: int = 2  # bumped to v2 for lifecycle/effectiveness fields

    # ── Lifecycle & Visibility (Phase 2/3) ─────────────────────────
    lifecycle_stage: SkillLifecycleStage = SkillLifecycleStage.DRAFT
    origin_team_id: str = ""          # 创建此技能的团队
    origin_agent_id: str = ""         # 创建此技能的智能体
    visibility: str = "private"       # private / shared / public
    adopted_by: List[str] = field(default_factory=list)   # 引入了此技能的团队ID列表
    quality_score: float = 0.0        # 综合质量分 (0-1)

    # ── Effectiveness Metrics (Phase 4) ────────────────────────────
    usage_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    effectiveness: float = 0.0        # success_count / usage_count
    avg_latency_ms: float = 0.0
    last_used_at: str = ""

    # ── Evolution / Lineage (Phase 5) ──────────────────────────────
    lineage: str = ""                 # 父技能ID（演化谱系）
    version: int = 1
    evidence_sessions: List[str] = field(default_factory=list)  # 关联的会话ID列表

    def __post_init__(self) -> None:
        if not self.skill_id:
            self.skill_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "required": self.required,
            "enabled": self.enabled,
            "icon": self.icon,
            "config_schema": self.config_schema,
            "config": self.config,
            "is_default": self.is_default,
            "source": self.source,
            "slug": self.slug,
            "required_tools": self.required_tools,
            "has_instructions": bool(self.instructions),
            "schema_version": self.schema_version,
            # Lifecycle
            "lifecycle_stage": self.lifecycle_stage.value,
            "origin_team_id": self.origin_team_id,
            "origin_agent_id": self.origin_agent_id,
            "visibility": self.visibility,
            "adopted_by": self.adopted_by,
            "quality_score": self.quality_score,
            # Effectiveness
            "usage_count": self.usage_count,
            "effectiveness": self.effectiveness,
            "last_used_at": self.last_used_at,
            # Lineage
            "lineage": self.lineage,
            "version": self.version,
        }


@dataclass
class AgentPersonality:
    """Agent personality and behavior configuration."""

    tone: str = "professional"
    language: str = "zh-CN"
    expertise_areas: List[str] = field(default_factory=list)
    response_style: str = "concise"
    creativity: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tone": self.tone,
            "language": self.language,
            "expertise_areas": self.expertise_areas,
            "response_style": self.response_style,
            "creativity": self.creativity,
        }


@dataclass
class ToolsetDistribution:
    """Hermes-style probabilistic toolset distribution.

    Each toolset has a % probability of being available per turn.
    Inspired by NousResearch/hermes-agent toolset_distributions.py.
    """

    name: str = "default"
    description: str = ""
    toolsets: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "toolsets": self.toolsets,
        }


@dataclass
class HermesAgentConfig:
    """Hermes-style agent configuration — extends AgentProfile with
    learning loop, memory, skills, toolsets, and context management.

    Inspired by NousResearch/hermes-agent architecture:
    - Closed learning loop (skills from experience)
    - Persistent memory across sessions
    - Toolset distributions for probabilistic tool access
    - SOUL.md persona
    - Context files (AGENTS.md, HERMES.md)
    - Session search (cross-session recall)
    - Delegate/subagent parallelization
    """

    # Agent loop parameters
    max_iterations: int = 90
    iteration_budget: int = 90

    # Toolset distribution (Hermes-style probabilistic tool selection)
    toolset_distribution: ToolsetDistribution = field(
        default_factory=lambda: ToolsetDistribution(name="default")
    )
    enabled_toolsets: List[str] = field(default_factory=list)
    disabled_toolsets: List[str] = field(default_factory=list)

    # Memory & learning
    memory_enabled: bool = True
    session_search_enabled: bool = True
    skill_auto_create: bool = True
    soul_md: str = ""
    context_files: List[str] = field(default_factory=list)

    # Delegation
    can_delegate: bool = False
    max_subagents: int = 3

    # Platform
    platform: str = "cli"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_iterations": self.max_iterations,
            "iteration_budget": self.iteration_budget,
            "toolset_distribution": self.toolset_distribution.to_dict(),
            "enabled_toolsets": self.enabled_toolsets,
            "disabled_toolsets": self.disabled_toolsets,
            "memory_enabled": self.memory_enabled,
            "session_search_enabled": self.session_search_enabled,
            "skill_auto_create": self.skill_auto_create,
            "soul_md": self.soul_md,
            "context_files": self.context_files,
            "can_delegate": self.can_delegate,
            "max_subagents": self.max_subagents,
            "platform": self.platform,
        }


@dataclass
class AgentPermission:
    """Agent access permission."""

    resource: str = ""
    access_level: AccessLevel = AccessLevel.READ
    channels: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource": self.resource,
            "access_level": self.access_level.value,
            "channels": self.channels,
        }


@dataclass
class AgentChannelConfig:
    """Channel subscription configuration for an agent."""

    channel_name: str = ""
    subscribe: bool = True
    publish: bool = False
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_name": self.channel_name,
            "subscribe": self.subscribe,
            "publish": self.publish,
            "priority": self.priority,
        }


@dataclass
class AgentProfile:
    """Individual agent profile — the Employee equivalent."""

    agent_id: str = ""
    name: str = ""
    role: str = ""
    description: str = ""
    template_type: AgentTemplateType = AgentTemplateType.CUSTOM
    state: AgentState = AgentState.IDLE
    model_id: str = ""
    system_prompt: str = ""
    personality: AgentPersonality = field(default_factory=AgentPersonality)
    permissions: List[AgentPermission] = field(default_factory=list)
    channels: List[AgentChannelConfig] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Hermes-style agent config (optional — non-None means Hermes mode)
    hermes_config: Optional[HermesAgentConfig] = None

    def __post_init__(self) -> None:
        if not self.agent_id:
            self.agent_id = str(uuid.uuid4())[:8]

    @property
    def is_hermes_agent(self) -> bool:
        return self.hermes_config is not None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "template_type": self.template_type.value,
            "state": self.state.value,
            "model_id": self.model_id,
            "system_prompt": self.system_prompt,
            "personality": self.personality.to_dict(),
            "permissions": [p.to_dict() for p in self.permissions],
            "channels": [c.to_dict() for c in self.channels],
            "tools": self.tools,
            "skills": self.skills,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "is_hermes_agent": self.is_hermes_agent,
        }
        if self.hermes_config is not None:
            d["hermes_config"] = self.hermes_config.to_dict()
        return d


@dataclass
class AgentTeam:
    """Agent team — the Company equivalent. Holds shared resources."""

    team_id: str = ""
    name: str = ""
    description: str = ""
    visibility: Visibility = Visibility.PRIVATE
    agents: Dict[str, AgentProfile] = field(default_factory=dict)
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    tools: Dict[str, ToolDefinition] = field(default_factory=dict)
    skills: Dict[str, SkillDefinition] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.team_id:
            self.team_id = str(uuid.uuid4())[:8]

    def add_agent(self, agent: AgentProfile) -> None:
        self.agents[agent.agent_id] = agent

    def remove_agent(self, agent_id: str) -> Optional[AgentProfile]:
        return self.agents.pop(agent_id, None)

    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        return self.agents.get(agent_id)

    def add_model(self, model: ModelConfig) -> None:
        self.models[model.model_id] = model

    def remove_model(self, model_id: str) -> Optional[ModelConfig]:
        return self.models.pop(model_id, None)

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        return self.models.get(model_id)

    def add_tool(self, tool: ToolDefinition) -> None:
        self.tools[tool.tool_id] = tool

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self.tools.get(tool_id)

    def add_skill(self, skill: SkillDefinition) -> None:
        self.skills[skill.skill_id] = skill

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self.skills.get(skill_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
            "visibility": self.visibility.value,
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "models": {k: v.to_dict() for k, v in self.models.items()},
            "tools": {k: v.to_dict() for k, v in self.tools.items()},
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
