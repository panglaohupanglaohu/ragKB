# -*- coding: utf-8 -*-
"""团队持久化存储 — 将团队配置序列化到 JSON 文件."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from .models import (
    AccessLevel,
    AgentChannelConfig,
    AgentPermission,
    AgentPersonality,
    AgentProfile,
    AgentState,
    AgentTeam,
    AgentTemplateType,
    HermesAgentConfig,
    ModelConfig,
    SkillCategory,
    SkillDefinition,
    ToolCategory,
    ToolDefinition,
    ToolsetDistribution,
    Visibility,
)

logger = logging.getLogger(__name__)

STORAGE_PATH = Path(__file__).resolve().parents[3] / "storage" / "teams" / "teams.json"


class TeamStore:
    """JSON 文件持久化: storage/teams/teams.json"""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or STORAGE_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # ── 保存 ─────────────────────────────────────────────

    def save_all(self, teams: Dict[str, AgentTeam]):
        """保存所有团队到 JSON."""
        data = {tid: self._serialize_team(t) for tid, t in teams.items()}
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.debug(f"💾 团队已保存: {len(teams)} 个团队")

    # ── 加载 ─────────────────────────────────────────────

    def load_all(self) -> Dict[str, AgentTeam]:
        """加载所有团队."""
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            teams: Dict[str, AgentTeam] = {}
            for tid, tdata in data.items():
                teams[tid] = self._deserialize_team(tdata)
            logger.info(f"📂 团队加载: {len(teams)} 个团队")
            return teams
        except Exception as e:
            logger.warning(f"加载团队失败: {e}")
            return {}

    # ── 反序列化 ──────────────────────────────────────────

    @staticmethod
    def _serialize_team(team: AgentTeam) -> dict:
        data = team.to_dict()
        data["skills"] = {
            sid: TeamStore._serialize_skill(skill)
            for sid, skill in team.skills.items()
        }
        return data

    @staticmethod
    def _serialize_skill(skill: SkillDefinition) -> dict:
        return {
            "skill_id": skill.skill_id,
            "name": skill.name,
            "description": skill.description,
            "category": skill.category.value if hasattr(skill.category, "value") else skill.category,
            "required": skill.required,
            "enabled": skill.enabled,
            "icon": skill.icon,
            "config_schema": skill.config_schema,
            "config": skill.config,
            "is_default": skill.is_default,
            "source": skill.source,
            "slug": skill.slug,
            "required_tools": skill.required_tools,
            "instructions": skill.instructions,
            "lifecycle_stage": getattr(skill.lifecycle_stage, "value", skill.lifecycle_stage),
            "quality_score": skill.quality_score,
            "visibility": getattr(skill.visibility, "value", skill.visibility),
            "version": skill.version,
            "usage_count": skill.usage_count,
            "success_count": skill.success_count,
            "fail_count": skill.fail_count,
            "effectiveness": skill.effectiveness,
            "last_used_at": skill.last_used_at,
            "adopted_by": list(skill.adopted_by),
            "origin_team_id": skill.origin_team_id,
            "lineage": skill.lineage,
            "schema_version": skill.schema_version,
            "evidence_sessions": list(skill.evidence_sessions),
        }

    @staticmethod
    def _deserialize_team(data: dict) -> AgentTeam:
        team = AgentTeam(
            team_id=data.get("team_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            visibility=Visibility(data.get("visibility", "private")),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {}),
        )
        # Agents
        for aid, adata in data.get("agents", {}).items():
            team.agents[aid] = TeamStore._deserialize_agent(adata)
        # Models (skip api_key masked values)
        for mid, mdata in data.get("models", {}).items():
            team.models[mid] = TeamStore._deserialize_model(mdata)
        # Tools
        for tool_id, tdata in data.get("tools", {}).items():
            team.tools[tool_id] = TeamStore._deserialize_tool(tdata)
        # Skills
        for sid, sdata in data.get("skills", {}).items():
            team.skills[sid] = TeamStore._deserialize_skill(sdata)
        return team

    @staticmethod
    def _deserialize_agent(data: dict) -> AgentProfile:
        personality_data = data.get("personality", {})
        personality = AgentPersonality(
            tone=personality_data.get("tone", "professional"),
            language=personality_data.get("language", "zh-CN"),
            expertise_areas=personality_data.get("expertise_areas", []),
            response_style=personality_data.get("response_style", "concise"),
            creativity=personality_data.get("creativity", 0.5),
        )
        permissions = [
            AgentPermission(
                resource=p.get("resource", ""),
                access_level=AccessLevel(p.get("access_level", "read")),
                channels=p.get("channels", []),
                allowed_tools=p.get("allowed_tools", []),
            )
            for p in data.get("permissions", [])
        ]
        channels = [
            AgentChannelConfig(
                channel_name=c.get("channel_name", ""),
                subscribe=c.get("subscribe", True),
                publish=c.get("publish", False),
                priority=c.get("priority", 0),
            )
            for c in data.get("channels", [])
        ]
        hermes_config = None
        if data.get("hermes_config"):
            hc = data["hermes_config"]
            td = hc.get("toolset_distribution", {})
            hermes_config = HermesAgentConfig(
                max_iterations=hc.get("max_iterations", 90),
                iteration_budget=hc.get("iteration_budget", 90),
                toolset_distribution=ToolsetDistribution(
                    name=td.get("name", "default"),
                    description=td.get("description", ""),
                    toolsets=td.get("toolsets", {}),
                ),
                enabled_toolsets=hc.get("enabled_toolsets", []),
                disabled_toolsets=hc.get("disabled_toolsets", []),
                memory_enabled=hc.get("memory_enabled", True),
                session_search_enabled=hc.get("session_search_enabled", True),
                skill_auto_create=hc.get("skill_auto_create", True),
                soul_md=hc.get("soul_md", ""),
                context_files=hc.get("context_files", []),
                can_delegate=hc.get("can_delegate", False),
                max_subagents=hc.get("max_subagents", 3),
                platform=hc.get("platform", "cli"),
            )

        agent = AgentProfile(
            agent_id=data.get("agent_id", ""),
            name=data.get("name", ""),
            role=data.get("role", ""),
            description=data.get("description", ""),
            template_type=AgentTemplateType(data.get("template_type", "custom")),
            state=AgentState(data.get("state", "idle")),
            model_id=data.get("model_id", ""),
            system_prompt=data.get("system_prompt", ""),
            personality=personality,
            permissions=permissions,
            channels=channels,
            tools=data.get("tools", []),
            skills=data.get("skills", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            hermes_config=hermes_config,
        )
        return agent

    @staticmethod
    def _deserialize_model(data: dict) -> ModelConfig:
        return ModelConfig(
            model_id=data.get("model_id", ""),
            provider=data.get("provider", "anthropic"),
            name=data.get("name", ""),
            max_tokens=data.get("max_tokens", 65536),
            temperature=data.get("temperature", 0.7),
            is_default=data.get("is_default", False),
            enabled=data.get("enabled", True),
            api_key="",  # never restore masked keys
            api_base_url=data.get("api_base_url", ""),
        )

    @staticmethod
    def _deserialize_tool(data: dict) -> ToolDefinition:
        return ToolDefinition(
            tool_id=data.get("tool_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=ToolCategory(data.get("category", "general")),
            enabled=data.get("enabled", True),
            requires_approval=data.get("requires_approval", False),
            parameters=data.get("parameters", {}),
            icon=data.get("icon", "🔧"),
            config_schema=data.get("config_schema", {}),
            config=data.get("config", {}),
            is_default=data.get("is_default", False),
            source=data.get("source", "builtin"),
        )

    @staticmethod
    def _deserialize_skill(data: dict) -> SkillDefinition:
        return SkillDefinition(
            skill_id=data.get("skill_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=SkillCategory(data.get("category", "general")),
            required=data.get("required", False),
            enabled=data.get("enabled", True),
            icon=data.get("icon", "⚡"),
            config_schema=data.get("config_schema", {}),
            config=data.get("config", {}),
            is_default=data.get("is_default", False),
            source=data.get("source", "builtin"),
            slug=data.get("slug", ""),
            required_tools=data.get("required_tools", []),
            instructions=data.get("instructions", ""),
            lifecycle_stage=data.get("lifecycle_stage", "draft"),
            quality_score=data.get("quality_score", 0.0),
            visibility=data.get("visibility", "private"),
            version=data.get("version", 1),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
            fail_count=data.get("fail_count", 0),
            effectiveness=data.get("effectiveness", 0.0),
            last_used_at=data.get("last_used_at", ""),
            adopted_by=data.get("adopted_by", []),
            origin_team_id=data.get("origin_team_id", ""),
            lineage=data.get("lineage", ""),
            schema_version=data.get("schema_version", 1),
            evidence_sessions=data.get("evidence_sessions", []),
        )
