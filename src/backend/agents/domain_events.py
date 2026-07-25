# -*- coding: utf-8 -*-
"""Domain Events — 领域事件定义，携带完整上下文而非仅 ID。

每个事件携带发生时的完整实体快照 (full context snapshot)，
下游消费者无需回查数据库即可处理事件。
支持 schema_version 用于跨版本兼容。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════════════

class EventType(str, Enum):
    """领域事件类型枚举."""

    # ── Skill events ──
    SKILL_CREATED = "skill.created"
    SKILL_UPDATED = "skill.updated"
    SKILL_DELETED = "skill.deleted"
    SKILL_ACTIVATED = "skill.activated"
    SKILL_DEACTIVATED = "skill.deactivated"

    # ── Agent events ──
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_STATE_CHANGED = "agent.state_changed"

    # ── Team events ──
    TEAM_CREATED = "team.created"
    TEAM_DELETED = "team.deleted"
    AGENT_ADDED_TO_TEAM = "agent.added_to_team"
    AGENT_REMOVED_FROM_TEAM = "agent.removed_from_team"

    # ── Task events ──
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # ── Eco / 物竞 ──
    ECO_SURVIVAL_UPDATED = "eco.survival_updated"


# ══════════════════════════════════════════════════════════════════════
# Event Payloads — 携带完整实体快照 (full context)
# ══════════════════════════════════════════════════════════════════════

@dataclass
class SkillSnapshot:
    """Skill 实体完整快照."""
    skill_id: str = ""
    name: str = ""
    description: str = ""
    category: str = "general"  # SkillCategory.value
    required: bool = False
    enabled: bool = True
    icon: str = "⚡"
    slug: str = ""
    source: str = "builtin"
    required_tools: List[str] = field(default_factory=list)
    instructions: str = ""
    config_schema: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    is_default: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_skill_definition(cls, skill_def) -> "SkillSnapshot":
        """从 SkillDefinition (models.py) 构建快照."""
        return cls(
            skill_id=skill_def.skill_id,
            name=skill_def.name,
            description=skill_def.description,
            category=skill_def.category.value if hasattr(skill_def.category, "value") else str(skill_def.category),
            required=skill_def.required,
            enabled=skill_def.enabled,
            icon=skill_def.icon,
            slug=skill_def.slug,
            source=skill_def.source,
            required_tools=list(skill_def.required_tools),
            instructions=skill_def.instructions,
            config_schema=dict(skill_def.config_schema),
            config=dict(skill_def.config),
            is_default=skill_def.is_default,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "required": self.required,
            "enabled": self.enabled,
            "icon": self.icon,
            "slug": self.slug,
            "source": self.source,
            "required_tools": self.required_tools,
            "instructions": self.instructions,
            "config_schema": self.config_schema,
            "config": self.config,
            "is_default": self.is_default,
            "metadata": self.metadata,
        }


@dataclass
class AgentSnapshot:
    """Agent 实体完整快照."""
    agent_id: str
    name: str
    role: str
    description: str
    state: str  # AgentState.value
    team_id: str = ""
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_agent_profile(cls, profile, team_id: str = "") -> "AgentSnapshot":
        """从 AgentProfile (models.py) 构建快照."""
        return cls(
            agent_id=profile.agent_id,
            name=profile.name,
            role=profile.role,
            description=profile.description,
            state=profile.state.value if hasattr(profile.state, "value") else str(profile.state),
            team_id=team_id,
            tools=list(profile.tools) if profile.tools else [],
            skills=list(profile.skills) if profile.skills else [],
            metadata=dict(profile.metadata) if profile.metadata else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "state": self.state,
            "team_id": self.team_id,
            "tools": self.tools,
            "skills": self.skills,
            "metadata": self.metadata,
        }


@dataclass
class TeamSnapshot:
    """Team 实体完整快照."""
    team_id: str
    name: str
    description: str
    visibility: str = "private"
    agent_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_agent_team(cls, team) -> "TeamSnapshot":
        """从 AgentTeam (models.py) 构建快照."""
        return cls(
            team_id=team.team_id,
            name=team.name,
            description=team.description,
            visibility=team.visibility.value if hasattr(team.visibility, "value") else str(team.visibility),
            agent_ids=list(team.agents.keys()) if team.agents else [],
            metadata=dict(team.metadata) if team.metadata else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
            "visibility": self.visibility,
            "agent_ids": self.agent_ids,
            "metadata": self.metadata,
        }


@dataclass
class TaskSnapshot:
    """Task 实体完整快照."""
    task_id: str
    agent_id: str
    team_id: str
    title: str
    description: str
    status: str  # TaskStatus.value
    priority: int = 2
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_agent_task(cls, task) -> "TaskSnapshot":
        """从 AgentTask (task_engine.py) 构建快照."""
        return cls(
            task_id=task.task_id,
            agent_id=task.agent_id,
            team_id=task.team_id,
            title=task.title,
            description=task.description,
            status=task.status.value if hasattr(task.status, "value") else str(task.status),
            priority=task.priority,
            dependencies=list(task.dependencies) if task.dependencies else [],
            result=task.result,
            error=task.error,
            metadata=dict(task.metadata) if task.metadata else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "team_id": self.team_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class EcoSurvivalSnapshot:
    """物竞存活写回快照 — 喂给拟生记忆 fitness/拓扑漂移."""

    team_id: str = ""
    agent_id: str = ""
    survival_ticks: float = 0.0
    fitness_delta: float = 0.0  # 相对上次写回的归一化变化，可选
    source: str = "eco_collab"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "agent_id": self.agent_id,
            "survival_ticks": self.survival_ticks,
            "fitness_delta": self.fitness_delta,
            "source": self.source,
            "metadata": self.metadata,
        }


# ══════════════════════════════════════════════════════════════════════
# Domain Event — 统一事件信封
# ══════════════════════════════════════════════════════════════════════

@dataclass
class DomainEvent:
    """领域事件信封 — 携带完整上下文。

    设计原则:
    - event_id: 唯一事件ID，用于幂等和去重
    - event_type: 事件类型 (EventType)
    - schema_version: 事件结构版本号，支持跨版本兼容
    - payload: 携带完整实体快照 (SkillSnapshot / AgentSnapshot / ...)
    - timestamp: 事件发生时间
    - source: 事件来源模块标识
    - correlation_id: 关联ID，用于追踪同一业务流程的多个事件
    """

    event_id: str
    event_type: EventType
    schema_version: int
    payload: Any  # SkillSnapshot | AgentSnapshot | TeamSnapshot | TaskSnapshot
    timestamp: str
    source: str
    correlation_id: str = ""

    def __post_init__(self) -> None:
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @classmethod
    def create(
        cls,
        event_type: EventType,
        payload: Any,
        schema_version: int = 1,
        source: str = "agents",
        correlation_id: str = "",
    ) -> "DomainEvent":
        """工厂方法 — 创建领域事件."""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            schema_version=schema_version,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            correlation_id=correlation_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        payload_dict = self.payload.to_dict() if hasattr(self.payload, "to_dict") else self.payload
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if hasattr(self.event_type, "value") else str(self.event_type),
            "schema_version": self.schema_version,
            "payload": payload_dict,
            "timestamp": self.timestamp,
            "source": self.source,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """从字典反序列化."""
        return cls(
            event_id=data.get("event_id", ""),
            event_type=EventType(data["event_type"]),
            schema_version=data.get("schema_version", 1),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", ""),
            source=data.get("source", "agents"),
            correlation_id=data.get("correlation_id", ""),
        )
