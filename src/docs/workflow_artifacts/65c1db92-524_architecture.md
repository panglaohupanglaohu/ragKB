# 架构设计 — architect

任务: 实现侵入式溯因与维度断路器/修复模板绑定，触发告警后自动生成专项 Backlog 并冻结非关键调用
步骤: architecture
Agent: build_architect

---

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
      """Skill catalog entry."""
  
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
  
  ```
  
  ### 文件: `src/backend/agents/plaza_engine.py`
  ```py
  # -*- coding: utf-8 -*-
  """智能体广场引擎 — 讨论编排与多 Agent 协同.
  
  核心编排逻辑:
  1. Moderator（主持人壁龛）提出子话题，引导讨论方向
  2. 每轮: 各参与者按座席层级依次发言（内圈→中圈→外圈）
  3. Moderator 总结本轮关键观点
  4. 最终轮: Moderator 生成全局总结 + 关键结论
  
  消息通过 asyncio.Queue 实时推送给 SSE 订阅者。
  """
  
  from __future__ import annotations
  
  import asyncio
  import json
  import logging
  import re
  from datetime import datetime, timezone
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional
  from uuid import uuid4
  
  from .plaza import (
      Discussion, DiscussionStatus, NicheRole, Participant,
      Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
  )
  from .plaza_store import PlazaStore
  
  logger = logging.getLogger(__name__)
  
  _ROUND_SPEAKER_LIMIT = 5
  _EXCHANGES_PER_ROUND = 2  # 每轮内交锋次数
  _SPEAKERS_PER_EXCHANGE = 3  # 每次交锋参与人数
  _CORE_ROLE_PRIORITY = {
      "architect": 0,
      "researcher": 1,
      "developer": 2,
      "qa_engineer": 3,
      "qa": 3,
      "tester": 3,
      "devops": 4,
      "project_manager": 5,
      "documentation": 6,
  }
  
  
  class PlazaEngine:
      """广场引擎 — 管理广场、参与者和讨论编排."""
  
      def __init__(self):
          self._store = PlazaStore()
          self._plazas: Dict[str, Plaza] = self._store.load_all()
          self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
          self._discussion_locks: Dict[str, asyncio.Lock] = {}
          self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference
  
      def set_chat_fn(self, fn: Callable):
          """注入 ChatHarness.chat 异步函数."""
          self._chat_fn = fn
  
      def _get_agent_profile(self, agent_id: str):
          """从 TeamManager 获取完整 AgentProfile，用于注入个性."""
          try:
              from agents.api import _team_manager
              if _team_manager:
                  for team in _team_manager.list_teams():
                      agent = team.get_agent(agent_id)
                      if agent:
                          return agent
          except Exception:
              pass
          return None
  
      def _build_agent_system_prompt(self, participant: Participant) -> str:
          """根据 AgentProfile 构建有个性的 system prompt."""
          profile = self._get_agent_profile(participant.agent_id)
          if profile:
              expertise = "、".join(profile.personality.expertise_areas) if profile.personality.expertise_areas else ""
              traits = "、".join(profile.metadata.get("traits", [])) if profile.metadata else ""
              parts = [
                  f"你是 {profile.name}，职责: {profile.role}。",
                  f"专长: {expertise}。" if expertise else "",
                  f"性格特质: {traits}。" if traits else "",
                  f"你的工作方式: {profile.system_prompt}" if profile.system_prompt else "",
                  f"\n你正在一个智能体广场的讨论中发言。",
                  f"请用自然的方式说话，像一个真实的专业人士在开会讨论。",
                  f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。",
                  f"不需要客套寒暄，但要说人话，不要像电报一样压缩。",
              ]
              return "".join(p for p in parts if p)
          # 回退到基础信息
          return (
              f"你是 {participant.agent_name}，职责: {participant.role}。"
              f"你正在一个智能体广场的讨论中发言。"
              f"请用自然的方式说话，像一个真实的专业人士在开会讨论。"
              f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。"
          )
  
      # ── 广场 CRUD ──────────────────────────────────────────
  
      def create_plaza(self, name: str, description: str = "") -> Plaza:
          plaza = Plaza(name=name, description=description)
          self._plazas[plaza.id] = plaza
          self._store.save_plaza(plaza)
          logger.info(f"🏛️ 广场创建: {name} ({plaza.id})")
          return plaza
  
      def get_plaza(self, plaza_id: str) -> Optional[Plaza]:
          return self._plazas.get(plaza_id)
  
      def list_plazas(self) -> List[Plaza]:
          return list(self._plazas.values())
  
      def delete_plaza(self, plaza_id: str) -> bool:
          if plaza_id in self._plazas:
              del self._plazas[plaza_id]
              self._store.delete_plaza(plaza_id)
              return True
          return False
  
      # ── 参与者管理 ──────────────────────────────────────────
  
      def add_participant(
          self, plaza_id: str, agent_id: str, agent_name: str = "",
          role: str = "", team_id: str = "",
          seat_tier: SeatTier = SeatTier.MIDDLE,
          niche_role: NicheRole = NicheRole.OBSERVER,
      ) -> Optional[Participant]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          # 分配壁龛编号 (动态扩展)
          used_niches = {p.niche_index for p in plaza.participants.values() if p.niche_index >= 0}
          niche_index = len(used_niches)
          # 自动扩展壁龛数
          if niche_index >= plaza.niche_count:
              plaza.niche_count = niche_index + 1
          p = Participant(
              agent_id=agent_id, agent_name=agent_name, role=role,
              team_id=team_id, seat_tier=seat_tier, niche_role=niche_role,
              niche_index=niche_index,
          )
          plaza.participants[agent_id] = p
          self._store.save_plaza(plaza)
          logger.info(f"🪑 参与者加入广场 {plaza_id}: {agent_name} (壁龛 #{niche_index})")
          return p
  
      def remove_participant(self, plaza_id: str, agent_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if plaza and agent_id in plaza.participants:
              del plaza.participants[agent_id]
              self._store.save_plaza(plaza)
              return True
          return False
  
      # ── 讨论管理 ──────────────────────────────────────────
  
      def create_discussion(
          self, plaza_id: str, topic: str, description: str = "",
          moderator_agent_id: str = "", max_rounds: int = 5,
      ) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          disc = Discussion(
              plaza_id=plaza_id, topic=topic, description=description,
              moderator_agent_id=moderator_agent_id, max_rounds=max_rounds,
          )
          plaza.discussions[disc.id] = disc
          self._store.save_plaza(plaza)
          logger.info(f"💬 讨论创建: {topic[:40]} ({disc.id})")
          return disc
  
      def get_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          return plaza.discussions.get(discussion_id)
  
      def list_discussions(self, plaza_id: str) -> List[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return []
          return list(plaza.discussions.values())
  
      def delete_discussion(self, plaza_id: str, discussion_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if not plaza or discussion_id not in plaza.discussions:
              return False
          del plaza.discussions[discussion_id]
          self._sse_queues.pop(discussion_id, None)
          self._store.save_plaza(plaza)
          return True
  
      def reset_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          """重置已结束讨论，保留话题本身以便重新讨论。"""
          disc = self.get_discussion(plaza_id, discussion_id)
          if not disc:
              return None
          disc.status = DiscussionStatus.OPEN
          disc.current_round = 0
          disc.messages.clear()
          disc.summary = ""
          disc.key_conclusions.clear()
          disc.plan.clear()
          disc.assigned_team_id = ""
          disc.started_at = None
          disc.ended_at = None
          plaza = self._plazas.get(plaza_id)
          if plaza:
              self._store.save_plaza(plaza)
          return disc
  
      # ── SSE 订阅管理 ──────────────────────────────────────
  
      def subscribe(self, discussion_id: str) -> asyncio.Queue:
          q: asyncio.Queue = as
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 实现侵入式溯因与维度断路器/修复模板绑定，触发告警后自动生成专项 Backlog 并冻结非关键调用
  步骤: pm_decompose
  📋 任务: 65c1db92-524
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  实现侵入式溯因与维度断路器/修复模板绑定，触发告警后自动生成专项 Backlog 并冻结非关键调用
  Developer + Tester
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/agent_team_api.py`
  ### 文件: `src/backend/agents/agent_toolbox.py`
  **变更文件 (3):**
    - `src/frontend/system-evolution.html`
    - `src/frontend/js/agent-team-config.js`
    - `src/backend/agent_team_api.py`
  **子任务拆解:**
    - **侵入式溯因**：自动分析告警根因
    - **维度断路器绑定**：将告警与断路器机制关联
    - **修复模板绑定**：自动匹配修复方案
    - **自动生成专项 Backlog**：创建修复任务
    - **冻结非关键调用**：降低系统负载
    - *文件路径**: `src/backend/monitoring/abduction_engine.py`
    - 接收告警事件，自动注入探测点
    - 收集相关维度的上下文数据
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 实现侵入式溯因与维度断路器/修复模板绑定，触发告警后自动生成专项 Backlog 并冻结非关键调用
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: 65c1db92-524
  🤖 Agent: Researcher (researcher)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 Researcher (researcher)。
    请执行以下开发任务:
    
    你是技术研究员。请对以下任务进行技术调研:
    
    ## 任务
    实现侵入式溯因与维度断路器/修复模板绑定，触发告警后自动生成专项 Backlog 并冻结非关键调用
    Developer + Tester
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
    src/frontend/datacenter-ratchet-evolution.html
    src/frontend/index.html
    src/frontend/login.html
    src/frontend/plaza-dark.html
    src/frontend/plaza-old.html
    src/frontend/plaza-wabisabi-v2.html
    src/frontend/plaza-wabisabi.html
    src/frontend/plaza.html
    src/frontend/system-evolution.html
    src/frontend/tasks.html
    src/frontend/css/agent-team-config.css
    src/frontend/css/openbridge-theme.css
    src/frontend/css/ws-theme-bridge.css
    src/frontend/js/agent-team-config.js
    src/frontend/js/i18n.js
    src/frontend/js/nav-sidebar.js
    src/backend/__init__.py
    src/backend/agent_team_api.py
    src/backend/main.py
    src/backend/main.py.bak
    src/backend/startup_check.py
    src/backend/startup_validator.py
    src/backend/agents/__init__.py
    src/backend/agents/ab_testing.py
    src/backend/agents/agent_loop.py
    src/backend/agents/agent_toolbox.py
    src/backend/agents/api.py
    src/backend/agents/chat_harness.py
    src/backend/agents/execution_registry.py
    src/backend/agents/hermes_research.py
    src/backend/agents/knowledge_base.py
    src/backend/agents/models.py
    src/backend/agents/plaza.py
    src/backend/agents/plaza_engine.py
    src/backend/agents/plaza_routes.py
    src/backend/agents/plaza_routes.py.bak
    src/backend/agents/plaza_store.py
    src/backend/agents/session_store.py
    src/backend/agents/skill_registry.py
    src/backend/agents/task_engine.py
    src/backend/agents/task_store.py
    src/backend/agents/team_manager.py
    src/backend/agents/team_store.py
    src/backend/agents/tool_executor.py
    src/backend/agents/tool_registry.py
    src/backend/agents/tts_routes.py
    src/backend/agents/teams/__init__.py
    src/backend/agents/teams/ai_coding_team.py
    src/backend/agents/teams/build_team.py
    src/backend/agents/teams/energy_team.py
    src/backend/agents/skills/__init__.py
    src/backend/agents/skills/greeting.py
    src/backend/agents/skills/hello.py
    src/backend/scripts/__init__.py
    src/backend/scripts/validate_startup.py
    src/backend/scripts/validate_telemetry.py
    src/backend/monitoring/__init__.py
    src/backend/monitoring/collector.py
    src/backend/monitoring/models.py
    src/backend/monitoring/plaza_monitor.py
    src/backend/monitoring/plaza_monitor.py.bak
    src/backend/monitoring/sampler.py
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/marine_base.py
    src/backend/channels/openclaw_sync.py
    src/backend/channels/openclaw_sync.py.bak
    src/backend/channels/system_evolution.py
    src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
    src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
    src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
    src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
    src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
    src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
    src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
    src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
    src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
    src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
    src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
    src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
    src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
    src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
    src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T004102.md
    src/docs/agent_handoffs/6f911ba3-822_architecture_20260507T003740.md
    src/docs/agent_handoffs/6f911ba3-822_deploy_FAILED_20260507T004337.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T003806.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004113.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004235.md
    src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
    src/docs/agent_handoffs/6f911ba3-822_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/6f911ba3-822_research_20260507T003550.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T003827.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004134.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004311.md
    src/docs/agent_handoffs/7c934759-39e_architecture_20260505T010014.md
    src/docs/agent_handoffs/7c934759-39e_develop_20260505T010359.md
    src/docs/agent_handoffs/7c934759-39e_develop_20260505T012357.md
    src/docs/agent_handoffs/7c934759-39e_develop_FAILED_20260505T011447.md
    src/docs/agent_handoffs/7c934759-39e_executor_started_20260505T005814.md
    src/docs/agent_handoffs/7c934759-39e_pm_decompose_20260505T005849.md
    src/docs/agent_handoffs/7c934759-39e_research_20260505T005919.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011016.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011949.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T012853.md
    src/docs/agent_handoffs/8665633b-cad_executor_started_20260507T031444.md
    src/docs/agent_handoffs/8a5071c5-834_architecture_20260507T003655.md
    src/docs/agent_handoffs/8a5071c5-834_deploy_FAILED_20260507T004051.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003716.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003903.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T004005.md
    src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
    src/docs/agent_handoffs/8a5071c5-834_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/8a5071c5-834_research_20260507T003540.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003737.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003929.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T004031.md
    src/docs/agent_handoffs/a77bd3b9-2db_architecture_20260507T003625.md
    src/docs/agent_handoffs/a77bd3b9-2db_deploy_FAILED_20260507T004102.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003646.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003838.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T004005.md
    src/docs/agent_handoffs/a77bd3b9-2db_executor_started_20260507T003435.md
    src/docs/agent_handoffs/a77bd3b9-2db_pm_decompose_20260507T003515.md
    src/docs/agent_handoffs/a77bd3b9-2db_research_20260507T003545.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003712.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003904.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T004042.md
    src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
    src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
    src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
    src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
    src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
    ... (共 257 个 src/ 文件)
    
    ```
    
    ### 文件: `src/backend/agent_team_api.py`
    ```py
    # -*- coding: utf-8 -*-
    """
    Agent Team API Routes - 双团队管理 REST API
    
    提供构建团队 & 执行团队的状态查询、KPI 考核、
    任务分配、报告查询等端点。挂载至 FastAPI 的 router。
    """
    
    from __future__ import annotations
    
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    from typing import Any, Dict, List, Optional
    
    router = APIRouter(prefix="/api/v1/agent-teams", tags=["Agent Teams"])
    
    
    # ---------------------------------------------------------------------------
    # 全局引用（在 main.py startup 时注入）
    # ---------------------------------------------------------------------------
    _build_team = None
    _execution_team = None
    _scheduler = None
    _evolution_engine = None
    
    
    def set_teams(build_team, execution_team, scheduler, evolution_engine=None):
        """在应用启动时由 main.py 调用，注入团队实例."""
        global _build_team, _execution_team, _scheduler, _evolution_engine
        _build_team = build_team
        _execution_team = execution_team
        _scheduler = scheduler
        _evolution_engine = evolution_engine
    
    
    # ---------------------------------------------------------------------------
    # Request / Response Models
    # ---------------------------------------------------------------------------
    
    class TaskAssignment(BaseModel):
        agent_id: str
        task: str
    
    class FeedbackSubmission(BaseModel):
        category: str = "optimization"
        severity: str = "medium"
        title: str
        detail: str
    
    
    # ---------------------------------------------------------------------------
    # Scheduler
    # ---------------------------------------------------------------------------
    
    @router.get("/scheduler/status")
    async def scheduler_status():
        if not _scheduler:
            raise HTTPException(503, "Scheduler not initialized")
        return _scheduler.get_status()
    
    
    @router.post("/scheduler/report")
    async def scheduler_generate_report():
        if not _scheduler:
            raise HTTPException(503, "Scheduler not initialized")
        return _scheduler.generate_report_now()
    
    
    @router.post("/scheduler/tick")
    async def scheduler_tick_once():
        """手动触发一次调度 tick (调试用)."""
        if not _scheduler:
            raise HTTPException(503, "Scheduler not initialized")
        return _scheduler.tick_once()
    
    
    # ---------------------------------------------------------------------------
    # Build Team
    # ---------------------------------------------------------------------------
    
    @router.get("/build/status")
    async def build_team_status():
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        return _build_team.get_status()
    
    
    @router.get("/build/kpis")
    async def build_team_kpis():
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        return _build_team.get_agent_kpis()
    
    
    @router.get("/build/agents/{agent_id}")
    async def build_agent_detail(agent_id: str):
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        agent = _build_team.agents.get(agent_id)
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found")
        return agent.to_dict()
    
    
    @router.post("/build/assign")
    async def build_assign_task(body: TaskAssignment):
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        ok = _build_team.assign_task(body.agent_id, body.task)
        if not ok:
            raise HTTPException(404, f"Agent '{body.agent_id}' not found")
        return {"status": "assigned", "agent_id": body.agent_id, "task": body.task}
    
    
    @router.get("/build/reports")
    async def build_reports(limit: int = 10):
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        reports = _build_team.hourly_reports[-limit:]
        return [r.to_dict() for r in reports]
    
    
    @router.get("/build/issues")
    async def build_issues():
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        return _build_team.issue_backlog
    
    
    # ---------------------------------------------------------------------------
    # Execution Team
    # ---------------------------------------------------------------------------
    
    @router.get("/execution/status")
    async def execution_team_status():
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        return _execution_team.get_status()
    
    
    @router.get("/execution/agents/{agent_id}")
    async def execution_agent_detail(agent_id: str):
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        agent = _execution_team.agents.get(agent_id)
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found")
        return agent.to_dict()
    
    
    @router.get("/execution/reports")
    async def execution_reports(limit: int = 10):
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        reports = _execution_team.execution_reports[-limit:]
        return [r.to_dict() for r in reports]
    
    
    @router.get("/execution/feedback")
    async def execution_feedback():
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        return [item.to_dict() for item in _execution_team.feedback_queue]
    
    
    @router.post("/execution/feedback")
    async def submit_feedback(body: FeedbackSubmission):
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        item = _execution_team.submit_feedback(
            category=body.category,
            severity=body.severity,
            title=body.title,
            detail=body.detail,
        )
        return item.to_dict()
    
    
    # ---------------------------------------------------------------------------
    # Combined
    # ---------------------------------------------------------------------------
    
    @router.get("/overview")
    async def teams_overview():
        """一站式获取双团队全局概览."""
        result: Dict[str, Any] = {}
        if _build_team:
            bs = _build_team.get_status()
            result["build_team"] = {
                "health": bs["health"],
                "agent_count": bs["agent_count"],
                "metrics": bs["metrics"],
            }
        if _execution_team:
            es = _execution_team.get_status()
            result["execution_team"] = {
                "health": es["health"],
                "agent_count": es["agent_count"],
                "metrics": es["metrics"],
            }
        if _scheduler:
            result["scheduler"] = _scheduler.get_status()
        if _evolution_engine:
            result["evolution"] = _evolution_engine.get_status()
        return result
    
    
    # ---------------------------------------------------------------------------
    # System Evolution (自我演进引擎)
    # ---------------------------------------------------------------------------
    
    @router.get("/evolution/status")
    async def evolution_status():
        """获取自我演进引擎状态。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_status()
    
    
    @router.get("/evolution/summary")
    async def evolution_summary():
        """获取演进项汇总。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_evolution_summary()
    
    
    @router.get("/evolution/items")
    async def evolution_items(status: Optional[str] = None):
        """获取演进项列表，可按状态过滤。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_evolution_items(status=status)
    
    
    @router.get("/evolution/rules")
    async def evolution_rules():
        """获取审查规则列表。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return [r.to_dict() for r in _evolution_engine.audit_rules]
    
    
    @router.post("/evolution/audit")
    async def evolution_run_audit():
        """手动触发一次审查。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.run_full_audit()
    
    
    @router.post("/evolution/cycle")
    async def evolution_run_cycle():
        """运行完整演进周期（审查→派发→验证→关闭）。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.run_evolution_cycle()
    
    
    @router.post("/evolution/dispatch")
    async def evolution_dispatch():
        """派发所有待处理演进项给 Build 团队。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.dispatch_all_pending()
    
    
    @router.post("/evolution/verify")
    async def evolution_verify():
        """验证所有待验证项。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.verify_all_pending()
    
    
    @router.get("/evolution/items/{item_id}")
    async def evolution_item_detail(item_id: str):
        """获取单个演进项详情。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        item = _evolution_engine.evolution_items.get(item_id)
        if not item:
            raise HTTPException(404, f"Item '{item_id}' not found")
        return item.to_dict()
    
    
    @router.post("/evolution/items/{item_id}/progress")
    async def evolution_mark_progress(item_id: str):
        """标记演进项为进行中。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        ok = _evolution_engine.mark_in_progress(item_id)
        if not ok:
            raise HTTPException(404, f"Item '{item_id}' not found")
        return {"status": "ok", "item_id": item_id, "new_status": "in_progress"}
    
    
    @router.post("/evolution/items/{item_id}/complete")
    async def evolution_mark_complete(item_id: str):
        """标记演进项构建完成，进入待验证。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        ok = _evolution_engine.mark_build_complete(item_id)
        if not ok:
            raise HTTPException(404, f"Item '{item_id}' not found")
        return {"status": "ok", "item_id": item_id, "new_status": "verify_pending"}
    
    
    @router.post("/evolution/close-verified")
    async def evolution_close_verified():
        """关闭所有已验证通过的演进项。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        closed = _evolution_engine.close_verified()
        return {"closed": closed, "count": len(closed)}
    
    
    @router.post("/evolution/close")
    async def evolution_close():
        """关闭所有已验证通过的演进项 (close-verified 别名)。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        closed = _evolution_engine.close_verified()
        return {"closed": closed, "count": len(closed)}
    
    
    @router.get("/evolution/history")
    async def evolution_audit_history():
        """获取审查历史记录。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        raw = _evolution_engine.get_audit_history()
        # Normalize field names for frontend (expects timestamp, total)
        result = []
        for h in raw:
            entry = dict(h)
            entry.setdefault("timestamp", entry.pop("time", None))
            entry.setdefault("total", (entry.get("passed") or 0) + (entry.get("failed") or 0) + (entry.get("skipped") or 0))
            result.append(entry)
        return result
    
    
    @router.get("/evolution/analytics")
    async def evolution_analytics():
        """获取演进分析数据 (域覆盖、严重度分布、趋势)。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        summary = _evolution_engine.get_evolution_summary()
        history = _evolution_engine.get_audit_history()
        status = _evolution_engine.get_status()
    
        return {
            "summary": summary,
            "history": history,
            "stats": status.get("stats", {}),
            "items_by_status": status.get("items_by_status", {}),
            "rules_count": status.get("audit_rules_count", 0),
        }
    
    
    # ---------------------------------------------------------------------------
    # Phase 3: 业界标准化改进 API
    # ---------------------------------------------------------------------------
    
    @router.get("/evolution/compliance-rating")
    async def evolution_compliance_rating():
        """获取 DNV CII 风格 A~E 合规评级。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        data = _evolution_engine.get_compliance_rating()
        # Add aliases expected by frontend
        data["grade"] = data.get("rating", "?")
        data["description"] = data.get("rating_label", "")
        escalation = _evolution_engine.get_escalation_status()
        if escalation.get("escalated_count", 0) > 0:
            data["escalation_tier"] = "corrective"
        else:
            data["escalation_tier"] = "normal"
        return data
    
    
    @router.post("/evolution/compliance-rating/calculate")
    async def evolution_calculate_rating():
        """重新计算合规评级 (运行快速审查)。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.calculate_compliance_rating()
    
    
    @router.get("/evolution/checklist")
    async def evolution_checklist(level: Optional[str] = None):
        """获取 ClassNK 双层自查清单 (company/ship)。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_checklist(level=level)
    
    
    @router.get("/evolution/zones")
    async def evolution_zones():
        """获取所有合规区域。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_all_zones()
    
    
    @router.get("/evolution/zones/active")
    async def evolution_active_zones():
        """获取当前激活的合规区域。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_active_zones()
    
    
    @router.post("/evolution/zones/update-position")
    async def evolution_update_position(lat: float = 0.0, lon: float = 0.0):
        """更新船舶位置，自动检测合规区域进入/离开。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.update_vessel_position(lat, lon)
    
    
    @router.get("/evolution/escalation")
    async def evolution_escalation():
        """获取失败升级状态 (DNV SEEMP Part III 风格)。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_escalation_status()
    
    
    @router.get("/evolution/trend")
    async def evolution_trend():
        """获取合规评级趋势分析。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        data = _evolution_engine.get_trend_analysis()
        # Frontend expects improvement_rate
        delta = data.get("trend_delta", 0.0)
        data["improvement_rate"] = round(delta, 1)
        return data
    
    
    @router.get("/evolution/monitoring")
    async def evolution_monitoring():
        """获取连续监控状态。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        data = _evolution_engine.get_monitoring_status()
        # Frontend expects 'active' bool and 'last_check' timestamp
        data["active"] = True
        if _evolution_engine._last_monitoring_time:
            from datetime import datetime as _dt
            data["last_check"] = _dt.fromtimestamp(_evolution_engine._last_monitoring_time).isoformat()
        else:
            data["last_check"] = None
        return data
    
    
    @router.get("/evolution/audit-trail")
    async 
    ```
    
    ### 文件: `src/backend/agents/agent_toolbox.py`
    ```py
    """AgentToolbox — function-calling tools for code-aware agents.
    
    Gives Developer / QA agents the ability to read, grep, write, and execute code
    in the project so they don't have to hallucinate file contents.
    
    All tool calls are scoped to the project root and write operations are
    restricted to a safe allowlist (src/, tests/, docs/, config/, public/).
    
    Each tool returns a JSON-serializable dict suitable for OpenAI/DeepSeek
    function-calling protocol.
    """
    from __future__ import annotations
    
    import json
    import logging
    import os
    import re
    import shlex
    import subprocess
    import time
    from pathlib import Path
    from typing import Any, Dict, List, Optional, Tuple
    
    logger = logging.getLogger("AgentToolbox")
    
    PROJECT_ROOT = Path(__file__).resolve().parents[3]  # src/backend/agents/ -> root
    ALLOWED_WRITE_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/",
                               "storage/agent_workspaces/", "storage/pipeline_runs/")
    MAX_FILE_BYTES = 256 * 1024   # 256KB per read
    MAX_GREP_HITS = 200
    MAX_EXEC_OUTPUT = 32 * 1024   # 32KB stdout/stderr cap
    
    
    # ═════════════════════════════════════════════════════════════════
    # OpenAI / DeepSeek function-calling tool schema (V4 supports this)
    # ═════════════════════════════════════════════════════════════════
    
    TOOL_SCHEMA: List[Dict[str, Any]] = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": (
                    "读取项目里某个文件的内容。优先使用此工具理解现有代码，再基于实际代码做修改。"
                    "只能读取项目根目录下的文件。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "项目相对路径，如 src/backend/channels/marine_base.py",
                        },
                        "start_line": {"type": "integer", "description": "起始行 (1-based, 可选)", "default": 1},
                        "end_line": {"type": "integer", "description": "结束行 (1-based, 可选)", "default": 0},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "grep",
                "description": (
                    "在项目中按正则搜索文本。用于查找类/函数/枚举值的真实定义位置。"
                    "返回每个匹配的文件路径、行号、行内容。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "正则表达式"},
                        "include": {
                            "type": "string",
                            "description": "glob 限定，如 src/backend/**/*.py",
                            "default": "**/*",
                        },
                        "max_hits": {"type": "integer", "default": 50},
                    },
                    "required": ["pattern"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "列出某个目录下的所有文件（递归）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "项目相对目录"},
                        "max_depth": {"type": "integer", "default": 3},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": (
                    "向项目写入或新建文件。只能写入 src/, tests/, docs/, config/, public/ 下。"
                    "如果目标已存在，旧内容会先备份为 .bak。优先创建新文件而非整文件覆盖大文件。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "项目相对路径"},
                        "content": {"type": "string", "description": "完整文件内容"},
                        "create_only": {
                            "type": "boolean",
                            "description": "为 true 时仅在文件不存在时写入",
                            "default": False,
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "patch_file",
                "description": (
                    "对已有文件做精准搜索-替换。比 write_file 安全，因为它要求你先看到原文。"
                    "search 必须是文件中存在的、唯一的连续片段。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "search": {"type": "string", "description": "要被替换的原文片段（必须唯一）"},
                        "replace": {"type": "string", "description": "替换为的新内容"},
                    },
                    "required": ["path", "search", "replace"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_python",
                "description": (
                    "在项目 venv 中执行一段 Python 代码（cwd=src/backend）。"
                    "用于验证 import 是否成功、检查类的属性等。最长执行 30s。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "要执行的 Python 代码"},
                        "timeout": {"type": "integer", "default": 30},
                    },
                    "required": ["code"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_pytest",
                "description": (
                    "运行 pytest，可指定路径或 -k 表达式。仅 QA agent 使用。"
                    "返回最后 60 行输出。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "测试路径或 -k 表达式", "default": ""},
                        "timeout": {"type": "integer", "default": 120},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "finish",
                "description": (
                    "声明任务完成。Agent 调用此工具表示完成本步骤的所有工作，并附上简短总结。"
                    "调用后循环终止。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "本步骤完成情况的简短总结"},
                        "files_changed": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "本步骤修改/新建的文件路径列表",
                            "default": [],
                        },
                    },
                    "required": ["summary"],
                },
            },
        },
    ]
    
    
    def _safe_path(rel: str) -> Path:
        """Resolve a project-relative path, refusing escapes."""
        if not rel:
            raise ValueError("empty path")
        p = (PROJECT_ROOT / rel).resolve()
        try:
            p.relative_to(PROJECT_ROOT)
        except ValueError:
            raise PermissionError(f"path escapes project root: {rel}")
        return p
    
    
    def _is_allowed_write(rel: str) -> bool:
        rel = rel.replace("\\", "/")
        return any(rel.startswith(p) for p in ALLOWED_WRITE_PREFIXES)
    
    
    # ═════════════════════════════════════════════════════════════════
    # Tool implementations
    # ═════════════════════════════════════════════════════════════════
    
    def tool_read_file(path: str, start_line: int = 1, end_line: int = 0) -> Dict[str, Any]:
        try:
            p = _safe_path(path)
            if not p.is_file():
                return {"ok": False, "error": f"not a file: {path}"}
            size = p.stat().st_size
            if size > MAX_FILE_BYTES * 4:
                return {
                    "ok": False,
                    "error": f"file too large ({size}B). Use grep to find the relevant section first.",
                }
            text = p.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            total = len(lines)
            if end_line and end_line > 0:
                lines = lines[max(0, start_line - 1):end_line]
            elif start_line > 1:
                lines = lines[start_line - 1:]
            out = "\n".join(lines)
            if len(out) > MAX_FILE_BYTES:
                out = out[:MAX_FILE_BYTES] + "\n…(truncated)"
            return {"ok": True, "path": path, "total_lines": total, "content": out}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def tool_grep(pattern: str, include: str = "**/*", max_hits: int = 50) -> Dict[str, Any]:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return {"ok": False, "error": f"bad regex: {e}"}
        max_hits = min(max_hits, MAX_GREP_HITS)
        hits: List[Dict[str, Any]] = []
        for fp in PROJECT_ROOT.glob(include):
            if not fp.is_file():
                continue
            # Skip irrelevant
            rel = str(fp.relative_to(PROJECT_ROOT))
            if any(seg in rel for seg in ("/node_modules/", "/.git/", "/__pycache__/", "/venv/", ".bak")):
                continue
            try:
                with fp.open("r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            hits.append({"path": rel, "line": i, "text": line.rstrip()[:200]})
                            if len(hits) >= max_hits:
                                return {"ok": True, "hits": hits, "truncated": True}
            except Exception:
                continue
        return {"ok": True, "hits": hits, "truncated": False}
    
    
    def tool_list_files(path: str, max_depth: int = 3) -> Dict[str, Any]:
        try:
            p = _safe_path(path)
            if not p.is_dir():
                return {"ok": False, "error": f"not a directory: {path}"}
            out: List[str] = []
            base_depth = len(p.parts)
            for root, dirs, files in os.walk(p):
                depth = len(Path(root).parts) - base_depth
                if depth > max_depth:
                    dirs[:] = []
                    continue
                dirs[:] = [d for d in dirs
                           if not d.startswith(".")
                           and d not in ("node_modules", "__pycache__", "venv")]
                for f in files:
                    if f.endswith((".pyc", ".bak")):
                        continue
                    rel = str((Path(root) / f).relative_to(PROJECT_ROOT))
                    out.append(rel)
                    if len(out) >= 500:
                        return {"ok": True, "files": out, "truncated": True}
            return {"ok": True, "files": out, "truncated": False}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def tool_write_file(path: str, content: str, create_only: bool = False) -> Dict[str, Any]:
        try:
            if not _is_allowed_write(path):
                return {"ok": False, "error": f"write denied (outside allowed dirs): {path}"}
            p = _safe_path(path)
            if p.exists() and create_only:
                return {"ok": False, "error": f"file exists and create_only=True: {path}"}
            # Shrink-replace guard
            if p.is_file():
                old_size = p.stat().st_size
                if old_size > 2048 and len(content) < old_size * 0.5:
                    return {
                        "ok": False,
                        "error": (
                            f"shrink-replace blocked: new {len(content)}B "
                            f"< 50% of existing {old_size}B. "
                            f"Use patch_file for incremental edits, or write a new file."
                        ),
                    }
                # Backup
                bak = p.with_suffix(p.suffix + ".bak")
                try:
                    bak.write_bytes(p.read_bytes())
                except Exception:
                    pass
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"ok": True, "path": path, "bytes": len(content), "created": not p.exists()}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def tool_patch_file(path: str, search: str, replace: str) -> Dict[str, Any]:
        try:
            if not _is_allowed_write(path):
                return {"ok": False, "error": f"write denied: {path}"}
            p = _safe_path(path)
            if not p.is_file():
                return {"ok": False, "error": f"file not found: {path}"}
            text = p.read_text(encoding="utf-8")
            cnt = text.count(search)
            if cnt == 0:
                return {"ok": False, "error": "search pattern not found in file"}
            if cnt > 1:
                return {
                    "ok": False,
                    "error": f"search pattern matches {cnt} times — must be unique. Add more context.",
                }
            new_text = text.replace(search, replace, 1)
            bak = p.with_suffix(p.suffix + ".bak")
            try:
                bak.write_text(text, encoding="utf-8")
            except Exception:
                pass
            p.write_text(new_text, encoding="utf-8")
            return {"ok": True, "path": path, "old_bytes": len(text), "new_bytes": len(new_text)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def _run_subprocess(cmd: List[str], cwd: Path, timeout: int) -> Dict[str, Any]:
        start = time.time()
        try:
            proc = subprocess.run(
                cmd, cwd=str(cwd), capture_output=True, text=True,
                timeout=timeout,
                env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
            )
            elapsed = time.time() - start
            out = proc.stdout or ""
            err = proc.stderr or ""
            if len(out) > MAX_EXEC_OUTPUT:
                out = "…(truncated)\n" + out[-MAX_EXEC_OUTPUT:]
            if len(err) > MAX_EXEC_OUTPUT:
                err = "…(truncated)\n" + err[-MAX_EXEC_OUTPUT:]
            return {
                "ok": True,
                "exit_code": proc.returncode,
                "stdout": out,
                "stderr": err,
                "elapsed_sec": round(elapsed, 2),
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"timeout after {timeout}s"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def tool_run_python(code: str, timeout: int = 30) -> Dict[str, Any]:
        venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
        py = str(venv_py) if venv_py.exists() else "python3"
        cwd = PROJECT_ROOT / "src" / "backend"
        return _run_subprocess([py, "-c", code], cwd, timeout)
    
    
    def tool_run_pytest(target: str = "", timeout: int = 120) -> Dict[str, Any]:
        venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
      
  ...(截断)
  
  ## ⚠️ 重要提示
  上方 📂 项目上下文 包含了任务相关的实际源文件。
  请基于这些文件设计方案，不要引用不存在的文件。
  
  ## 要求
  1. 基于调研结果和实际源码，设计详细技术方案
  2. 明确指出需要修改的文件和具体修改内容
  3. 定义接口规范（如有新增 API）
  4. 为开发工程师提供逐步实施指南
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
⚡ 使用 DeepSeek V4 直连 (64K 输出, 流式)...

🔗 API: api.deepseek.com | 模型: deepseek-chat
────────────────────────────────────────────────────────────

# 技术方案设计 — 侵入式溯因与维度断路器/修复模板绑定

## 1. 概述

### 1.1 目标
实现一个**告警驱动的自动修复系统**，当监控系统检测到异常时：
1. **侵入式溯因**：自动注入探测点，收集多维上下文数据，分析根因
2. **维度断路器绑定**：将告警与断路器机制关联，自动熔断异常维度
3. **修复模板绑定**：根据根因匹配预定义的修复模板
4. **自动生成专项 Backlog**：创建修复任务并分配给 Build 团队
5. **冻结非关键调用**：降低系统负载，防止雪崩

### 1.2 核心概念
- **侵入式溯因 (Intrusive Abduction)**：在告警触发后，主动向相关组件注入探测代码，收集运行时上下文数据，通过逆向推理定位根因
- **维度断路器 (Dimension Circuit Breaker)**：按维度（服务、API、数据源等）隔离故障，当某个维度异常率超过阈值时自动熔断
- **修复模板 (Repair Template)**：预定义的修复方案模板，包含修复步骤、验证条件和回滚策略

## 2. 系统架构

### 2.1 新增模块

```
src/backend/monitoring/
├── __init__.py
├── collector.py          # 已有：指标采集
├── models.py             # 已有：数据模型
├── plaza_monitor.py      # 已有：广场监控
├── sampler.py            # 已有：采样器
├── abduction_engine.py   # 新增：侵入式溯因引擎
├── circuit_breaker.py    # 新增：维度断路器管理器
├── repair_templates.py   # 新增：修复模板仓库
├── backlog_generator.py  # 新增：Backlog 自动生成器
└── call_freeze.py        # 新增：调用冻结管理器
```

### 2.2 数据流

```
[监控告警] → [侵入式溯因引擎] → [根因分析结果]
                    ↓
            [维度断路器管理器] → [断路器状态更新]
                    ↓
            [修复模板匹配] → [匹配的修复方案]
                    ↓
            [Backlog 生成器] → [专项 Backlog 任务]
                    ↓
            [调用冻结管理器] → [冻结非关键调用]
```

## 3. 详细设计

### 3.1 侵入式溯因引擎 (`abduction_engine.py`)

```python
# src/backend/monitoring/abduction_engine.py

"""
侵入式溯因引擎

功能：
1. 接收告警事件，自动注入探测点
2. 收集相关维度的上下文数据
3. 通过逆向推理定位根因
4. 生成根因分析报告
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class AbductionSeverity(Enum):
    """溯因严重度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProbeType(Enum):
    """探测点类型"""
    LOG_INSPECTION = "log_inspection"       # 日志检查
    METRIC_ANALYSIS = "metric_analysis"     # 指标分析
    TRACE_INJECTION = "trace_injection"     # 链路追踪注入
    DEPENDENCY_CHECK = "dependency_check"   # 依赖检查
    CONFIG_AUDIT = "config_audit"           # 配置审计
    PERFORMANCE_SAMPLE = "performance_sample"  # 性能采样


@dataclass
class AbductionProbe:
    """探测点定义"""
    probe_id: str = ""
    probe_type: ProbeType = ProbeType.LOG_INSPECTION
    target_component: str = ""          # 目标组件
    target_dimension: str = ""          # 目标维度
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 30
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.probe_id:
            self.probe_id = str(uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "probe_type": self.probe_type.value,
            "target_component": self.target_component,
            "target_dimension": self.target_dimension,
            "parameters": self.parameters,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
        }


@dataclass
class AbductionEvidence:
    """溯因证据"""
    evidence_id: str = ""
    probe_id: str = ""
    source: str = ""                    # 证据来源
    content: str = ""                   # 证据内容
    confidence: float = 0.0             # 置信度 0.0-1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "probe_id": self.probe_id,
            "source": self.source,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


@dataclass
class RootCause:
    """根因分析结果"""
    cause_id: str = ""
    description: str = ""               # 根因描述
    dimension: str = ""                 # 关联维度
    severity: AbductionSeverity = AbductionSeverity.MEDIUM
    confidence: float = 0.0             # 置信度
    evidence: List[AbductionEvidence] = field(default_factory=list)
    suggested_repair_template: str = "" # 建议的修复模板 ID
    affected_components: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cause_id": self.cause_id,
            "description": self.description,
            "dimension": self.dimension,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "suggested_repair_template": self.suggested_repair_template,
            "affected_components": self.affected_components,
            "created_at": self.created_at,
        }


@dataclass
class AbductionReport:
    """溯因分析报告"""
    report_id: str = ""
    alert_id: str = ""                  # 触发告警 ID
    alert_type: str = ""                # 告警类型
    alert_severity: str = ""            # 告警严重度
    probes_deployed: List[AbductionProbe] = field(default_factory=list)
    root_causes: List[RootCause] = field(default_factory=list)
    primary_cause: Optional[RootCause] = None
    analysis_duration_ms: int = 0
    status: str = "pending"             # pending, analyzing, completed, failed
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "alert_severity": self.alert_severity,
            "probes_deployed": [p.to_dict() for p in self.probes_deployed],
            "root_causes": [rc.to_dict() for rc in self.root_causes],
            "primary_cause": self.primary_cause.to_dict() if self.primary_cause else None,
            "analysis_duration_ms": self.analysis_duration_ms,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class AbductionEngine:
    """侵入式溯因引擎"""

    def __init__(self):
        self._reports: Dict[str, AbductionReport] = {}
        self._probe_registry: Dict[str, AbductionProbe] = {}
        self._chat_fn = None

    def set_chat_fn(self, fn):
        """注入 ChatHarness.chat 用于 LLM 辅助分析"""
        self._chat_fn = fn

    def register_probe(self, probe: AbductionProbe) -> str:
        """注册探测点"""
        self._probe_registry[probe.probe_id] = probe
        return probe.probe_id

    def get_probe(self, probe_id: str) -> Optional[AbductionProbe]:
        return self._probe_registry.get(probe_id)

    async def analyze_alert(self, alert_data: Dict[str, Any]) -> AbductionReport:
        """分析告警，执行侵入式溯因"""
        report = AbductionReport(
            alert_id=alert_data.get("alert_id", ""),
            alert_type=alert_data.get("type", "unknown"),
            alert_severity=alert_data.get("severity", "medium"),
        )
        self._reports[report.report_id] = report
        start_time = time.time()

        try:
            report.status = "analyzing"

            # 1. 根据告警类型部署探测点
            probes = self._deploy_probes(alert_data)
            report.probes_deployed = probes

            # 2. 执行探测，收集证据
            evidence_list = await self._execute_probes(probes, alert_data)

            # 3. 分析根因
            root_causes = self._analyze_root_causes(evidence_list, alert_data)
            report.root_causes = root_causes

            # 4. 确定主要根因
            if root_causes:
                report.primary_cause = max(root_causes, key=lambda rc: rc.confidence)

            report.status = "completed"

        except Exception as e:
            logger.error(f"Abduction analysis failed: {e}")
            report.status = "failed"

        report.analysis_duration_ms = int((time.time() - start_time) * 1000)
        report.completed_at = datetime.now(timezone.utc).isoformat()
        return report

    def _deploy_probes(self, alert_data: Dict[str, Any]) -> List[AbductionProbe]:
        """根据告警类型部署探测点"""
        alert_type = alert_data.get("type", "")
        probes = []

        # 通用探测点
        probes.append(AbductionProbe(
            probe_type=ProbeType.LOG_INSPECTION,
            target_component=alert_data.get("component", ""),
            target_dimension=alert_data.get("dimension", ""),
            parameters={"time_range_minutes": 30, "log_level": "ERROR"},
        ))

        # 根据告警类型添加特定探测点
        if "performance" in alert_type.lower():
            probes.append(AbductionProbe(
                probe_type=ProbeType.PERFORMANCE_SAMPLE,
                target_component=alert_data.get("component", ""),
                target_dimension=alert_data.get("dimension", ""),
                parameters={"sample_count": 100, "metric": "response_time"},
            ))
        elif "error_rate" in alert_type.lower():
            probes.append(AbductionProbe(
                probe_type=ProbeType.DEPENDENCY_CHECK,
                target_component=alert_data.get("component", ""),
                target_dimension=alert_data.get("dimension", ""),
                parameters={"check_downstream": True},
            ))
        elif "resource" in alert_type.lower():
            probes.append(AbductionProbe(
                probe_type=ProbeType.METRIC_ANALYSIS,
                target_component=alert_data.get("component", ""),
                target_dimension=alert_data.get("dimension", ""),
                parameters={"metrics": ["cpu", "memory", "disk", "network"]},
            ))

        return probes

    async def _execute_probes(
        self, probes: List[AbductionProbe], alert_data: Dict[str, Any]
    ) -> List[AbductionEvidence]:
        """执行探测点，收集证据"""
        evidence_list = []
        for probe in probes:
            try:
                evidence = await self._execute_single_probe(probe, alert_data)
                if evidence:
                    evidence_list.append(evidence)
            except Exception as e:
                logger.warning(f"Probe {probe.probe_id} failed: {e}")
        return evidence_list

    async def _execute_single_probe(
        self, probe: AbductionProbe, alert_data: Dict[str, Any]
    ) -> Optional[AbductionEvidence]:
        """执行单个探测点"""
        # 这里实现具体的探测逻辑
        # 实际实现时会调用监控系统的 API 或直接读取日志/指标
        evidence = AbductionEvidence(
            probe_id=probe.probe_id,
            source=f"{probe.target_component}/{probe.probe_type.value}",
            content=f"Probe executed on {probe.target_component} dimension {probe.target_dimension}",
            confidence=0.7,
        )
        return evidence

    def _analyze_root_causes(
        self, evidence_list: List[AbductionEvidence], alert_data: Dict[str, Any]
    ) -> List[RootCause]:
        """分析根因"""
        # 使用 LLM 辅助分析（如果配置了 chat_fn）
        if self._chat_fn and evidence_list:
            return self._llm_assisted_analysis(evidence_list, alert_data)

        # 基于规则的简单分析
        return self._rule_based_analysis(evidence_list, alert_data)

    def _rule_based_analysis(
        self, evidence_list: List[AbductionEvidence], alert_data: Dict[str, Any]
    ) -> List[RootCause]:
        """基于规则的根因分析"""
        root_causes = []
        alert_type = alert_data.get("type", "")
        dimension = alert_data.get("dimension", "")

        # 简单规则匹配
        if "error_rate" in alert_type.lower():
            root_causes.append(RootCause(
                description=f"High error rate detected in dimension {dimension}",
                dimension=dimension,
                severity=AbductionSeverity.HIGH,
                confidence=0.6,
                evidence=evidence_list,
                suggested_repair_template="error_rate_recovery",
                affected_components=[alert_data.get("component", "")],
            ))

        return root_causes

    def _llm_assisted_analysis(
        self, evidence_list: List[AbductionEvidence], alert_data: Dict[str, Any]
    ) -> List[RootCause]:
        """LLM 辅助的根因分析"""
        # 构建分析提示
        prompt = self._build_analysis_prompt(evidence_list, alert_data)
        # 调用 LLM 分析
        # 实际实现时调用 self._chat_fn
        return []

    def _build_analysis_prompt(
        self, evidence_list: List[AbductionEvidence], alert_data: Dict[str, Any]
    ) -> str:
        """构建 LLM 分析提示"""
        evidence_text = "\n".join([
            f"- [{e.source}] {e.content} (confidence: {e.confidence})"
            for e in evidence_list
        ])
        return f"""
You are a root cause analysis expert. Analyze the following alert and evidence to identify root causes.

Alert:
- Type: {alert_data.get('type', 'unknown')}
- Severity: {alert_data.get('severity', 'medium')}
- Component: {alert_data.get('component', 'unknown')}
- Dimension: {alert_data.get('dimension', 'unknown')}
- Message: {alert_data.get('message', '')}

Evidence collected:
{evidence_text}

Please identify the most likely root cause(s) and suggest repair actions.
"""

    def get_report(self, report_id: str) -> Optional[AbductionReport]:
        return self._reports.get(report_id)

    def list_reports(self, limit: int = 20) -> List[AbductionReport]:
        reports = list(self._reports.values())
        reports.sort(key=lambda r: r.created_at, reverse=True)
        return reports[:limit]
```

### 3.2 维度断路器管理器 (`circuit_breaker.py`)

```python
# src/backend/monitoring/circuit_breaker.py

"""
维度断路器管理器

功能：
1. 按维度（服务、API、数据源等）管理断路器状态
2. 根据异常率自动触发熔断
3. 支持半开状态自动恢复
4. 与溯因引擎联动，根据根因调整熔断策略
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """断路器状态"""
    CLOSED = "closed"           # 正常
    OPEN = "open"               # 熔断
    HALF_OPEN = "half_open"     # 半开（尝试恢复）
    DISABLED = "disabled"       # 禁用


@dataclass
class CircuitBreakerConfig:
    """断路器配置"""
    failure_threshold: int = 5          # 失败次数阈值
    success_threshold: int = 3          # 半开状态下成功次数阈值
    timeout_seconds: int = 30           # 熔断超时时间
    half_open_timeout: int = 10         # 半开超时时间
    consecutive_failures: int = 0       # 当前连续失败次数
    consecutive_successes: int = 0      # 当前连续成功次数
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None


@dataclass
class DimensionBreaker:
    """维度断路器"""
    breaker_id: str = ""
    dimension: str = ""                 # 维度标识（如 service:api-gateway）
    dimension_type: str = ""            # 维度类型（service, api, datasource, etc.）
    state: CircuitState = CircuitState.CLOSED
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    metrics: Dict[str, Any] = field(default_factory=dict)
    linked_abduction_report_id: Optional[str] = None  # 关联的溯因报告
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_state_change: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.breaker_id:
            self.breaker_id = str(uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "breaker_id": self.breaker_id,
            "dimension": self.dimension,
            "dimension_type": self.dimension_type,
            "state": self.state.value,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "half_open_timeout": self.config.half_open_timeout,
                "consecutive_failures": self.config.consecutive_failures,
                "consecutive_successes": self.config.consecutive_successes,
            },
            "metrics": self.metrics,
            "linked_abduction_report_id": self.linked_abduction_report_id,
            "created_at": self.created_at,
            "last_state_change": self.last_state_change,
        }


class CircuitBreakerManager:
    """断路器管理器"""

    def __init__(self):
        self._breakers: Dict[str, DimensionBreaker] = {}
        self._dimension_index: Dict[str, str] = {}  # dimension -> breaker_id
        self._state_change_callbacks: List[Callable] = []

    def register_callback(self, callback: Callable):
        """注册状态变更回调"""
        self._state_change_callbacks.append(callback)

    def get_or_create_breaker(self, dimension: str, dimension_type: str = "service") -> DimensionBreaker:
        """获取或创建维度断���器"""
        if dimension in self._dimension_index:
            breaker_id = self._dimension_index[dimension]
            return self._breakers[breaker_id]

        breaker = DimensionBreaker(
            dimension=dimension,
            dimension_type=dimension_type,
        )
        self._breakers[breaker.breaker_id] = breaker
        self._dimension_index[dimension] = breaker.breaker_id
        return breaker

    def get_breaker(self, dimension: str) -> Optional[DimensionBreaker]:
        if dimension in self._dimension_index:
            return self._breakers.get(self._dimension_index[dimension])
        return None

    def record_success(self, dimension: str) -> Dict[str, Any]:
        """记录成功调用"""
        breaker = self.get_or_create_breaker(dimension)
        now = time.time()

        if breaker.state == CircuitState.HALF_OPEN:
            breaker.config.consecutive_successes += 1
            if breaker.config.consecutive_successes >= breaker.config.success_threshold:
                self._transition_to(breaker, CircuitState.CLOSED)
        elif breaker.state == CircuitState.CLOSED:
            breaker.config.consecutive_failures = 0
            breaker.config.consecutive_successes += 1

        breaker.config.last_success_time = now
        return breaker.to_dict()

    def record_failure(self, dimension: str) -> Dict[str, Any]:
        """记录失败调用"""
        breaker = self.get_or_create_breaker(dimension)
        now = time.time()

        breaker.config.consecutive_failures += 1
        breaker.config.consecutive_successes = 0
        breaker.config.last_failure_time = now

        if breaker.state == CircuitState.CLOSED:
            if breaker.config.consecutive_failures >= breaker.config.failure_threshold:
                self._transition_to(breaker, CircuitState.OPEN)
        elif breaker.state == CircuitState.HALF_OPEN:
            self._transition_to(breaker, CircuitState.OPEN)

        return breaker.to_dict()

    def _transition_to(self, breaker: DimensionBreaker, new_state: CircuitState):
        """状态转换"""
        old_state = breaker.state
        breaker.state = new_state
        breaker.last_state_change = datetime.now(timezone.utc).isoformat()

        if new_state == CircuitState.OPEN:
            breaker.config.consecutive_failures = 0
            breaker.config.consecutive_successes = 0
        elif new_state == CircuitState.HALF_OPEN:
            breaker.config.consecutive_failures = 0
            breaker.config.consecutive_successes = 0
        elif new_state == CircuitState.CLOSED:
            breaker.config.consecutive_failures = 0

        # 触发回调
        for callback in self._state_change_callbacks:
            try:
                callback(breaker, old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback failed: {e}")

    def check_state(self, dimension: str) -> CircuitState:
        """检查维度状态，自动处理超时恢复"""
        breaker = self.get_breaker(dimension)
        if not breaker:
            return CircuitState.CLOSED

        now = time.time()

        if breaker.state == CircuitState.OPEN:
            if breaker.config.last_failure_time:
                elapsed = now - breaker.config.last_failure_time
                if elapsed >= breaker.config.timeout_seconds:
                    self._transition_to(breaker, CircuitState.HALF_OPEN)

        return breaker.state

    def is_allowed(self, dimension: str) -> bool:
        """检查是否允许调用"""
        state = self.check_state(dimension)
        return state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def link_abduction_report(self, dimension: str, report_id: str):
        """关联溯因报告"""
        breaker = self.get_breaker(dimension)
        if breaker:
            breaker.linked_abduction_report_id = report_id

    def get_all_breakers(self) -> List[DimensionBreaker]:
        return list(self._breakers.values())

    def get_open_breakers(self) -> List[DimensionBreaker]:
        return [b for b in self._breakers.values() if b.state == CircuitState.OPEN]

    def reset_breaker(self, dimension: str) -> bool:
        """手动重置断路器"""
        breaker = self.get_breaker(dimension)
        if breaker:
            self._transition_to(breaker, CircuitState.CLOSED)
            return True
        return False
```

### 3.3 修复模板仓库 (`repair_templates.py`)

```python
# src/backend/monitoring/repair_templates.py

"""
修复模板仓库

功能：
1. 管理预定义的修复模板
2. 根据根因自动匹���修复方案
3. 支持模板参数化
4. 记录修复执行历史
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class RepairActionType(Enum):
    """修复动作类型"""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    CLEAR_CACHE = "clear_cache"
    ROLLBACK_CONFIG = "rollback_config"
    RECONNECT_DATASOURCE = "reconnect_datasource"
    RATE_LIMIT = "rate_limit"
    CIRCUIT_BREAK = "circuit_break"
    EXECUTE_SCRIPT = "execute_script"
    NOTIFY_ADMIN = "notify_admin"


@dataclass
class RepairAction:
    """修复动作"""
    action_id: str = ""
    action_type: RepairActionType = RepairActionType.NOTIFY_ADMIN
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    rollback_action: Optional[str] = None  # 回滚动作 ID

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "description": self.description,
            "parameters": self.parameters,
            "order": self.order,
            "rollback_action": self.rollback_action,
        }


@dataclass
class RepairTemplate:
    """修复模板"""
    template_id: str = ""
    name: str = ""
    description: str = ""
    category: str = ""                  # 分类（performance, error, resource, etc.）
    severity: str = "medium"            # 适用严重度
    match_rules: Dict[str, Any] = field(default_factory=dict)  # 匹配规则
    actions: List[RepairAction] = field(default_factory=list)
    verification_steps: List[str] = field(default_factory=list)  # 验证步骤
    rollback_steps: List[str] = field(default_factory=list)      # 回滚步骤
    timeout_minutes: int = 30
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.template_id:
            self.template_id = str(uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "match_rules": self.match_rules,
            "actions": [a.to_dict() for a in self.actions],
            "verification_steps": self.verification_steps,
            "rollback_steps": self.rollback_steps,
            "timeout_minutes": self.timeout_minutes,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class RepairExecution:
    """修复执行记录"""
    execution_id: str = ""
    template_id: str = ""
    alert_id: str = ""
    abduction_report_id: str = ""
    dimension: str = ""
    status: str = "pending"             # pending, running, success, failed, rolled_back
    actions_executed: List[Dict[str, Any]] = field(default_factory=list)
    result: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "template_id": self.template_id,
            "alert_id": self.alert_id,
            "abduction_report_id": self.abduction_report_id,
            "dimension": self.dimension,
            "status": self.status,
            "actions_executed": self.actions_executed,
            "result": self.result,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class RepairTemplateRepository:
    """修复模板仓库"""

    def __init__(self):
        self._templates: Dict[str, RepairTemplate] = {}
        self._executions: Dict[str, RepairExecution] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认修复模板"""
        # 错误率恢复模板
        error_rate_template = RepairTemplate(
            name="error_rate_recovery",
            description="High error rate recovery - restart and clear cache",
            category="error",
            severity="high",
            match_rules={
                "alert_types": ["error_rate", "error_rate_spike"],
                "dimension_types": ["service", "api"],
            },
            actions=[
                RepairAction(
                    action_type=RepairActionType.CLEAR_CACHE,
                    description="Clear service cache",
                    parameters={"cache_type": "all"},
                    order=1,
                ),
                RepairAction(
                    action_type=RepairActionType.RESTART_SERVICE,
                    description="Restart affected service",
                    parameters={"graceful": True, "timeout": 30},
                    order=2,
                ),
            ],
            verification_steps=[
                "Check error rate dropped below threshold",
                "Verify service health endpoint returns 200",
            ],
            rollback_steps=[
                "Restore previous service version",
                "Restore cache configuration",
            ],
        )
        self.register_template(error_rate_template)

        # 性能退化模板
        performance_template = RepairTemplate(
            name="performance_degradation",
            description="Performance degradation - scale up and optimize",
            category="performance",
            severity="medium",
            match_rules={
                "alert_types": ["response_time", "latency", "performance"],
                "dimension_types": ["service", "api"],
            },
            actions=[
                RepairAction(
                    action_type=RepairActionType.SCALE_UP,
                    description="Scale up service instances",
                    parameters={"scale_factor": 1.5, "max_instances": 10},
                    order=1,
                ),
                RepairAction(
                    action_type=RepairActionType.RATE_LIMIT,
                    description="Apply rate limiting",
                    parameters={"rate_per_second": 100, "burst": 50},
                    order=2,
                ),
            ],
            verification_steps=[
                "Check response time returned to normal",
                "Verify no new performance alerts",
            ],
            rollback_steps=[
                "Scale down to original instance count",
                "Remove rate limiting",
            ],
        )
        self.register_template(performance_template)

        # 资源耗尽模板
        resource_template = RepairTemplate(
            name="resource_exhaustion",
            description="Resource exhaustion - scale up and cleanup",
            category="resource",
            severity="critical",
            match_rules={
                "alert_types": ["cpu_high", "memory_high", "disk_full", "resource"],
                "dimension_types": ["service", "system"],
            },
            actions=[
                RepairAction(
                    action_type=RepairActionType.EXECUTE_SCRIPT,
                    description="Run cleanup script",
                    parameters={"script": "cleanup_resources.sh", "args": ["--aggressive"]},
                    order=1,
                ),
                RepairAction(
                    action_type=RepairActionType.SCALE_UP,
                    description="Scale up resources",
                    parameters={"scale_factor": 2.0, "max_instances": 20},
                    order=2,
                ),
            ],
            verification_steps=[
                "Check resource usage dropped below 80%",
                "Verify system stability",
            ],
            rollback_steps=[
                "Scale down to original resource allocation",
            ],
        )
        self.register_template(resource_template)

    def register_template(self, template: RepairTemplate) -> str:
        """注册修复模板"""
        self._templates[template.template_id] = template
        return template.template_id

    def get_template(self, template_id: str) -> Optional[RepairTemplate]:
        return self._templates.get(template_id)

    def match_template(self, root_cause: Dict[str, Any]) -> Optional[RepairTemplate]:
        """根据根因匹配修复模板"""
        suggested_id = root_cause.get("suggested_repair_template", "")
        if suggested_id and suggested_id in self._templates:
            return self._templates[suggested_id]

        # 基于规则匹配
        dimension_type = root_cause.get("dimension_type", "")
        severity = root_cause.get("severity", "medium")
        alert_type = root_cause.get("alert_type", "")

        for template in self._templates.values():
            if not template.is_active:
                continue
            rules = template.match_rules
            # 检查告警类型
            if "alert_types" in rules:
                if not any(at in alert_type for at in rules["alert_types"]):
                    continue
            # 检查维度类型
            if "dimension_types" in rules:
                if dimension_type not in rules["dimension_types"]:
                    continue
            return template

        return None

    def create_execution(
        self, template_id: str, alert_id: str,
        abduction_report_id: str, dimension: str
    ) -> RepairExecution:
        """创建修复执行记录"""
        execution = RepairExecution(
            template_id=template_id,
            alert_id=alert_id,
            abduction_report_id=abduction_report_id,
            dimension=dimension,
        )
        self._executions[execution.execution_id] = execution
        return execution

    def update_execution_status(self, execution_id: str, status: str, result: str = ""):
        """更新执行状态"""
        execution = self._executions.get(execution_id)
        if execution:
            execution.status = status
            execution.result = result
            if status in ("success", "failed", "rolled_back"):
                execution.completed_at = datetime.now(timezone.utc).isoformat()

    def get_execution(self, execution_id: str) -> Optional[RepairExecution]:
        return self._executions.get(execution_id)

    def list_templates(self) -> List[RepairTemplate]:
        return list(self._templates.values())

    def list_executions(self, limit: int = 20) -> List[RepairExecution]:
        executions = list(self._executions.values())
        executions.sort(key=lambda e: e.started_at, reverse=True)
        return executions[:limit]
```

### 3.4 Backlog 自动生成器 (`backlog_generator.py`)

```python
# src/backend/monitoring/backlog_generator.py

"""
Backlog 自动生成器

功能：
1. 根据溯因报告和修复模板自动生成 Backlog 任务
2. 将任务分配给 Build 团队
3. 设置任务优先级和依赖关系
4. 生成任务描述和验收标准
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class BacklogTask:
    """Backlog 任务"""
    task_id: str = ""
    title: str = ""
    description: str = ""
    priority: str = "medium"            # critical, high, medium, low
    status: str = "pending"             # pending, assigned, in_progress, completed, cancelled
    category: str = "repair"            # repair, optimization, feature, bugfix
    source_alert_id: str = ""           # 来源告警 ID
    source_report_id: str = ""          # 来源溯因报告 ID
    dimension: str = ""                 # 关联维度
    assigned_agent_id: str = ""         # 分配的 Agent ID
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # 依赖任务 ID
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "category": self.category,
            "source_alert_id": self.source_alert_id,
            "source_report_id": self.source_report_id,
            "dimension": self.dimension,
            "assigned_agent_id": self.assigned_agent_id,
            "acceptance_criteria": self.acceptance_criteria,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class BacklogGenerator:
    """Backlog 自动生成器"""

    def __init__(self):
        self._tasks: Dict[str, BacklogTask] = {}
        self._build_team = None

    def set_build_team(self, build_team):
        """注入 Build 团队实例"""
        self._build_team = build_team

    def generate_from_abduction(
        self,
        abduction_report: Dict[str, Any],
        repair_template: Optional[Dict[str, Any]] = None,
    ) -> List[BacklogTask]:
        """根据溯因报告生成 Backlog 任务"""
        tasks = []

        # 1. 创建主要修复任务
        primary_cause = abduction_report.get("primary_cause", {})
        if primary_cause:
            main_task = self._create_repair_task(
                title=f"Fix: {primary_cause.get('description', 'Unknown issue')}",
                description=self._build_task_description(primary_cause, repair_template),
                priority=self._map_severity_to_priority(primary_cause.get("severity", "medium")),
                source_alert_id=abduction_report.get("alert_id", ""),
                source_report_id=abduction_report.get("report_id", ""),
                dimension=primary_cause.get("dimension", ""),
                acceptance_criteria=self._build_acceptance_criteria(primary_cause, repair_template),
            )
            tasks.append(main_task)

        # 2. 创建预防性任务
        prevention_task = self._create_prevention_task(
            abduction_report=abduction_report,
            root_causes=abduction_report.get("root_causes", []),
        )
        if prevention_task:
            tasks.append(prevention_task)

        # 3. 创建监控增强任务
        monitoring_task = self._create_monitoring_task(abduction_report)
        if monitoring_task:
            tasks.append(monitoring_task)

        # 注册任务
        for task in tasks:
            self._tasks[task.task_id] = task

        # 分配给 Build 团队
        self._assign_to_build_team(tasks)

        return tasks

    def _create_repair_task(
        self, title: str, description: str, priority: str,
        source_alert_id: str, source_report_id: str,
        dimension: str, acceptance_criteria: List[str],
    ) -> BacklogTask:
        """创建修复任务"""
        return BacklogTask(
            title=title,
            description=description,
            priority=priority,
            category="repair",
            source_alert_id=source_alert_id,
            source_report_id=source_report_id,
            dimension=dimension,
            acceptance_criteria=acceptance_criteria,
        )

    def _create_prevention_task(
        self, abduction_report: Dict[str, Any],
        root_causes: List[Dict[str, Any]],
    ) -> Optional[BacklogTask]:
        """创建预防性任务"""
        if not root_causes:
            return None

        # 从根因中提取预防措施
        prevention_measures = []
        for rc in root_causes:
            if rc.get("suggested_repair_template"):
                prevention_measures.append(
                    f"Implement proactive monitoring for {rc.get('dimension', 'unknown')}"
                )

        if not prevention_measures:
            return None

        return BacklogTask(
            title=f"Preventive: Add safeguards for {abduction_report.get('alert_type', 'unknown')}",
            description="\n".join(prevention_measures),
            priority="medium",
            category="optimization",
            source_alert_id=abduction_report.get("alert_id", ""),
            source_report_id=abduction_report.get("report_id", ""),
            dimension="",
            acceptance_criteria=[
                "Preventive measures implemented",
                "No regression in existing functionality",
            ],
        )

    def _create_monitoring_task(self, abduction_report: Dict[str, Any]) -> Optional[BacklogTask]:
        """创建监控增强任务"""
        alert_type = abduction_report.get("alert_type", "")
        dimension = abduction_report.get("primary_cause", {}).get("dimension", "")

        if not dimension:
            return None

        return BacklogTask(
            title=f"Monitoring: Enhance alerting for {dimension}",
            description=(
                f"Based on abduction analysis of alert type '{alert_type}', "
                f"enhance monitoring coverage for dimension '{dimension}'.\n\n"
                f"Add additional metrics and alert rules to detect similar issues earlier."
            ),
            priority="low",
            category="optimization",
            source_alert_id=abduction_report.get("alert_id", ""),
            source_report_id=abduction_report.get("report_id", ""),
            dimension=dimension,
            acceptance_criteria=[
                "New monitoring metrics added",
                "Alert rules configured",
                "Test alert triggered successfully",
            ],
        )

    def _build_task_description(
        self, root_cause: Dict[str, Any],
        repair_template: Optional[Dict[str, Any]] = None,
    ) -> str:
        """构建任务描述"""
        parts = [
            f"Root Cause: {root_cause.get('description', 'Unknown')}",
            f"Dimension: {root_cause.get('dimension', 'Unknown')}",
            f"Confidence: {root_cause.get('confidence', 0.0)}",
            f"Affected Components: {', '.join(root_cause.get('affected_components', []))}",
        ]

        if repair_template:
            parts.append(f"\nRepair Template: {repair_template.get('name', 'Unknown')}")
            actions = repair_template.get("actions", [])
            if actions:
                parts.append("\nRecommended Actions:")
                for action in actions:
                    parts.append(f"  - {action.get('description', 'Unknown action')}")

        return "\n".join(parts)

    def _build_acceptance_criteria(
        self, root_cause: Dict[str, Any],
        repair_template: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """构建验收标准"""
        criteria = [
            f"Issue in dimension '{root_cause.get('dimension', 'unknown')}' is resolved",
            "No new alerts triggered for the same issue",
            "System performance returned to normal levels",
        ]

        if repair_template:
            criteria.extend(repair_template.get("verification_steps", []))

        return criteria

    def _map_severity_to_priority(self, severity: str) -> str:
        """映射严重度到优先级"""
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }
        return mapping.get(severity, "medium")

    def _assign_to_build_team(self, tasks: List[BacklogTask]):
        """将任务分配给 Build 团队"""
        if not self._build_team or not tasks:
            return

        for task in tasks:
            try:
                # 找到空闲的 Agent
                agent = self._find_idle_agent()
                if agent:
                    task.assigned_agent_id = agent.agent_id
                    task.status = "assigned"
                    self._build_team.assign_task(agent.agent_id, task.to_dict())
                    logger.info(f"Task {task.task_id} assigned to agent {agent.agent_id}")
            except Exception as e:
                logger.error(f"Failed to assign task {task.task_id}: {e}")

    def _find_idle_agent(self):
        """找到空闲的 Build Agent"""
        if not self._build_team:
            return None
        for agent_id, agent in self._build_team.agents.items():
            if agent.state.value == "idle":
                return agent
        return None

    def get_task(self, task_id: str) -> Optional[BacklogTask]:
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[str] = None) -> List[BacklogTask]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks

    def update_task_status(self, task_id: str, status: str) -> bool:
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            if status == "completed":
                task.completed_at = datetime.now(timezone.utc).isoformat()
            return True
        return False
```

### 3.5 调用冻结管理器 (`call_freeze.py`)

```python
# src/backend/monitoring/call_freeze.py

"""
调用冻结管理器

功能：
1. 根据告警严重度冻结非关键调用
2. 管理冻结策略（按维度、按调用类型）
3. 自动恢复冻结
4. 与断路器联动
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class FreezeLevel(Enum):
    """冻结级别"""
    NONE = "none"                   # 无冻结
    LIGHT = "light"                 # 轻度冻结（仅非关键调用）
    MODERATE = "moderate"           # 中度冻结（非关键 + 低优先级）
    AGGRESSIVE = "aggressive"       # 激进冻结（除核心外全部冻结）
    TOTAL = "total"                 # 完全冻结


@dataclass
class FreezeRule:
    """冻结规则"""
    rule_id: str = ""
    name: str = ""
    description: str = ""
    freeze_level: FreezeLevel = FreezeLevel.LIGHT
    target_dimensions: List[str] = field(default_factory=list)  # 目标维度
    target_call_types: List[str] = field(default_factory=list)  # 目标调用类型
    exclude_dimensions: List[str] = field(default_factory=list)  # 排除维度
    duration_minutes: int = 15
    auto_recover: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "freeze_level": self.freeze_level.value,
            "target_dimensions": self.target_dimensions,
            "target_call_types": self.target_call_types,
            "exclude_dimensions": self.exclude_dimensions,
            "duration_minutes": self.duration_minutes,
            "auto_recover": self.auto_recover,
        }


@dataclass
class FreezeState:
    """冻结状态"""
    freeze_id: str = ""
    rule_id: str = ""
    alert_id: str = ""
    freeze_level: FreezeLevel = FreezeLevel.NONE
    affected_dimensions: List[str] = field(default_factory=list)
    frozen_calls: int = 0
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scheduled_recovery_at: Optional[str] = None
    recovered_at: Optional[str] = None
    status: str = "active"  # active, recovering, recovered

    def to_dict(self) -> Dict[str, Any]:
        return {
            "freeze_id": self.freeze_id,
            "rule_id": self.rule_id,
            "alert_id": self.alert_id,
            "freeze_level": self.freeze_level.value,
            "affected_dimensions": self.affected_dimensions,
            "frozen_calls": self.frozen_calls,
            "started_at": self.started_at,
            "scheduled_recovery_at": self.scheduled_recovery_at,
            "recovered_at": self.recovered_at,
            "status": self.status,
        }


class CallFreezeManager:
    """调用冻结管理器"""

    def __init__(self):
        self._rules: Dict[str, FreezeRule] = {}
        self._active_freezes: Dict[str, FreezeState] = {}
        self._frozen_call_counters: Dict[str, int] = {}  # dimension -> count
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认冻结规则"""
        # 轻度冻结规则
        light_rule = FreezeRule(
            name="light_freeze_non_critical",
            description="Freeze non-critical calls during medium severity alerts",
            freeze_level=FreezeLevel.LIGHT,
            target_call_types=["analytics", "reporting", "logging", "notification"],
            exclude_dimensions=["core_api", "auth", "payment"],
            duration_minutes=15,
        )
        self.register_rule(light_rule)

        # 中度冻结规则
        moderate_rule = FreezeRule(
            name="moderate_freeze_low_priority",
            description="Freeze non-critical and low priority calls during high severity alerts",
            freeze_level=FreezeLevel.MODERATE,
            target_call_types=["analytics", "reporting", "logging", "notification", "background_job"],
            exclude_dimensions=["core_api", "auth", "payment", "user_service"],
            duration_minutes=30,
        )
        self.register_rule(moderate_rule)

        # 激进冻结规则
        aggressive_rule = FreezeRule(
            name="aggressive_freeze_all_non_core",
            description="Freeze all non-core calls during critical alerts",
            freeze_level=FreezeLevel.AGGRESSIVE,
            target_dimensions=["*"],
            exclude_dimensions=["core_api", "auth", "payment", "user_service", "health_check"],
            duration_minutes=60,
        )
        self.register_rule(aggressive_rule)

    def register_rule(self, rule: FreezeRule) -> str:
        """注册冻结规则"""
        self._rules[rule.rule_id] = rule
        return rule.rule_id

    def get_rule(self, rule_id: str) -> Optional[FreezeRule]:
        return self._rules.get(rule_id)

    def apply_freeze(self, alert_data: Dict[str, Any]) -> Optional[FreezeState]:
        """根据告警应用冻结"""
        severity = alert_data.get("severity", "medium")
        dimension = alert_data.get("dimension", "")

        # 根据严重度选择冻结级别
        freeze_level = self._determine_freeze_level(severity)
        if freeze_level == FreezeLevel.NONE:
            return None

        # 找到匹配的规则
        rule = self._find_matching_rule(freeze_level, dimension)
        if not rule:
            return None

        # 创建冻结状态
        freeze = FreezeState(
            rule_id=rule.rule_id,
            alert_id=alert_data.get("alert_id", ""),
            freeze_level=freeze_level,
            affected_dimensions=self._get_affected_dimensions(rule, dimension),
        )

        # 计算恢复时间
        from datetime import timedelta
        start = datetime.fromisoformat(freeze.started_at)
        freeze.scheduled_recovery_at = (start + timedelta(minutes=rule.duration_minutes)).isoformat()

        self._active_freezes[freeze.freeze_id] = freeze
        logger.info(
            f"Freeze applied: level={freeze_level.value}, "
            f"dimensions={freeze.affected_dimensions}, "
            f"duration={rule.duration_minutes}min"
        )

        return freeze

    def _determine_freeze_level(self, severity: str) -> FreezeLevel:
        """根据严重度确定冻结级别"""
        mapping = {
            "critical": FreezeLevel.AGGRESSIVE,
            "high": FreezeLevel.MODERATE,
            "medium": FreezeLevel.LIGHT,
            "low": FreezeLevel.NONE,
        }
        return mapping.get(severity, FreezeLevel.NONE)

    def _find_matching_rule(self, freeze_level: FreezeLevel, dimension: str) -> Optional[FreezeRule]:
        """找到匹配的冻结规则"""
        for rule in self._rules.values():
            if rule.freeze_level == freeze_level:
                # 检查维度是否在排除列表
                if dimension in rule.exclude_dimensions:
                    continue
                # 检查维度是否在目标列表（如果目标列表不为空）
                if rule.target_dimensions and rule.target_dimensions != ["*"]:
                    if dimension not in rule.target_dimensions:
                        continue
                return rule
        return None

    def _get_affected_dimensions(self, rule: FreezeRule, alert_dimension: str) -> List[str]:
        """获取受影响的维度列表"""
        if rule.target_dimensions == ["*"]:
            # 所有维度（排除列表除外）
            return ["all_non_core"]
        return rule.target_dimensions

    def is_call_frozen(self, call_type: str, dimension: str) -> bool:
        """检查调用是否被冻结"""
        for freeze in self._active_freezes.values():
            if freeze.status != "active":
                continue

            rule = self._rules.get(freeze.rule_id)
            if not rule:
                continue

            # 检查维度是否在排除列表
            if dimension in rule.exclude_dimensions:
                continue

            # 检查调用类型
            if rule.target_call_types:
                if call_type in rule.target_call_types:
                    # 记录冻结的调用
                    key = f"{dimension}:{call_type}"
                    self._frozen_call_counters[key] = self._frozen_call_counters.get(key, 0) + 1
                    freeze.frozen_calls += 1
                    return True

            # 检查维度
            if rule.target_dimensions:
                if rule.target_dimensions == ["*"] or dimension in rule.target_dimensions:
                    key = f"{dimension}:{call_type}"
                    self._frozen_call_counters[key] = self._frozen_call_counters.get(key, 0) + 1
                    freeze.frozen_calls += 1
                    return True

        return False

    def recover_freeze(self, freeze_id: str) -> bool:
        """恢复冻结"""
        freeze = self._active_freezes.get(freeze_id)
        if not freeze:
            return False

        freeze.status = "recovering"
        freeze.recovered_at = datetime.now(timezone.utc).isoformat()
        freeze.status = "recovered"

        logger.info(f"Freeze recovered: {freeze_id}")
        return True

    def recover_all(self) -> int:
        """恢复所有活跃冻结"""
        count = 0
        for freeze_id in list(self._active_freezes.keys()):
            if self._active_freezes[freeze_id].status == "active":
                self.recover_freeze(freeze_id)
                count += 1
        return count

    def check_auto_recovery(self):
        """检查并自动恢复过期冻结"""
        now = datetime.now(timezone.utc)
        for freeze_id, freeze in list(self._active_freezes.items()):
            if freeze.status != "active":
                continue
            if freeze.scheduled_recovery_at:
                recovery_time = datetime.fromisoformat(freeze.scheduled_recovery_at)
                if now >= recovery_time:
                    self.recover_freeze(freeze_id)

    def get_active_freezes(self) -> List[FreezeState]:
        return [f for f in self._active_freezes.values() if f.status == "active"]

    def get_freeze_stats(self) -> Dict[str, Any]:
        return {
            "active_freezes": len(self.get_active_freezes()),
            "total_frozen_calls": sum(f.frozen_calls for f in self._active_freezes.values()),
            "frozen_calls_by_dimension": dict(self._frozen_call_counters),
        }
```

### 3.6 集成管理器 (`auto_recovery_orchestrator.py`)

```python
# src/backend/monitoring/auto_recovery_orchestrator.py

"""
自动恢复编排器

功能：
1. 协调溯因引擎、断路器、修复模板、Backlog 生成器和冻结管理器
2. 提供统一的告警处理入口
3. 管理整个自动恢复流程
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .abduction_engine import AbductionEngine, AbductionReport
from .circuit_breaker import CircuitBreakerManager, CircuitState
from .repair_templates import RepairTemplateRepository
from .backlog_generator import BacklogGenerator, BacklogTask
from .call_freeze import CallFreezeManager, FreezeLevel

logger = logging.getLogger(__name__)


@dataclass
class RecoveryPipeline:
    """恢复流水线记录"""
    pipeline_id: str = ""
    alert_id: str = ""
    alert_data: Dict[str, Any] = field(default_factory=dict)
    abduction_report: Optional[AbductionReport] = None
    circuit_breaker_state: Optional[str] = None
    repair_execution_id: Optional[str] = None
    backlog_tasks: List[BacklogTask] = field(default_factory=list)
    freeze_state: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, analyzing, repairing, recovering, completed, failed
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "alert_id": self.alert_id,
            "alert_data": self.alert_data,
            "abduction_report": self.abduction_report.to_dict() if self.abduction_report else None,
            "circuit_breaker_state": self.circuit_breaker_state,
            "repair_execution_id": self.repair_execution_id,
            "backlog_tasks": [t.to_dict() for t in self.backlog_tasks],
            "freeze_state": self.freeze_state,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class AutoRecoveryOrchestrator:
    """自动恢复编排器"""

    def __init__(
        self,
        abduction_engine: AbductionEngine,
        circuit_breaker: CircuitBreakerManager,
        repair_templates: RepairTemplateRepository,
        backlog_generator: BacklogGenerator,
        call_freeze: CallFreezeManager,
    ):
        self._abduction_engine = abduction_engine
        self._circuit_breaker = circuit_breaker
        self._repair_templates = repair_templates
        self._backlog_generator = backlog_generator
        self._call_freeze = call_freeze
        self._pipelines: Dict[str, RecoveryPipeline] = {}
        self._alert_callbacks: List[Callable] = []

    def register_alert_callback(self, callback: Callable):
        """注册告警回调"""
        self._alert_callbacks.append(callback)

    async def handle_alert(self, alert_data: Dict[str, Any]) -> RecoveryPipeline:
        """处理告警 - 主入口"""
        pipeline = RecoveryPipeline(
            alert_id=alert_data.get("alert_id", str(uuid4())[:8]),
            alert_data=alert_data,
        )
        self._pipelines[pipeline.pipeline_id] = pipeline

        try:
            # 1. 触发告警回调
            for callback in self._alert_callbacks:
                try:
                    callback(alert_data)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")

            # 2. 应用调用冻结
            pipeline.status = "analyzing"
            freeze_state = self._call_freeze.apply_freeze(alert_data)
            if freeze_state:
                pipeline.freeze_state = freeze_state.to_dict()
                logger.info(f"Freeze applied: {freeze_state.freeze_level.value}")

            # 3. 执行侵入式溯因
            abduction_report = await self._abduction_engine.analyze_alert(alert_data)
            pipeline.abduction_report = abduction_report

            if abduction_report.status != "completed":
                pipeline.status = "failed"
                pipeline.completed_at = datetime.now(timezone.utc).isoformat()
                return pipeline

            # 4. 更新断路器状态
            pipeline.status = "repairing"
            primary_cause = abduction_report.primary_cause
            if primary_cause:
                dimension = primary_cause.dimension
                # 记录失败到断路器
                self._circuit_breaker.record_failure(dimension)
                # 关联溯因报告
                self._circuit_breaker.link_abduction_report(
                    dimension, abduction_report.report_id
                )
                pipeline.circuit_breaker_state = self._circuit_breaker.check_state(dimension).value

            # 5. 匹配修复模板
            if primary_cause:
                template = self._repair_templates.match_template(primary_cause.to_dict())
                if template:
                    # 创建修复执行
                    execution = self._repair_templates.create_execution(
                        template_id=template.template_id,
                        alert_id=alert_data.get("alert_id", ""),
                        abduction_report_id=abduction_report.report_id,
                        dimension=primary_cause.dimension,
                    )
                    pipeline.repair_execution_id = execution.execution_id

                    # 执行修复动作
                    await self._execute_repair_actions(execution, template)

            # 6. 生成 Backlog 任务
            pipeline.status = "recovering"
            template_dict = template.to_dict() if template else None
            backlog_tasks = self._backlog_generator.generate_from_abduction(
                abduction_report.to_dict(),
                template_dict,
            )
            pipeline.backlog_tasks = backlog_tasks

            # 7. 完成
            pipeline.status = "completed"

        except Exception as e:
            logger.error(f"Auto recovery pipeline failed: {e}")
            pipeline.status = "failed"

        pipeline.completed_at = datetime.now(timezone.utc).isoformat()
        return pipeline

    async def _execute_repair_actions(self, execution, template):
        """执行修复动作"""
        from .repair_templates import RepairActionType

        execution.status = "running"
        actions_executed = []

        for action in sorted(template.actions, key=lambda a: a.order):
            try:
                result = await self._execute_single_action(action)
                actions_executed.append({
                    "action_id": action.action_id,
                    "action_type": action.action_type.value,
                    "status": "success" if result else "failed",
                })
            except Exception as e:
                actions_executed.append({
                    "action_id": action.action_id,
                    "action_type": action.action_type.value,
                    "status": "failed",
                    "error": str(e),
                })

        execution.actions_executed = actions_executed
        all_success = all(a["status"] == "success" for a in actions_executed)
        execution.status = "success" if all_success else "failed"
        execution.result = "All actions completed" if all_success else "Some actions failed"

        self._repair_templates.update_execution_status(
            execution.execution_id, execution.status, execution.result
        )

    async def _execute_single_action(self, action) -> bool:
        """执行单个修复动作"""
        from .repair_templates import RepairActionType

        action_type = action.action_type
        params = action.parameters

        try:
            if action_type == RepairActionType.CLEAR_CACHE:
                # 实现缓存清理逻辑
                logger.info(f"Clearing cache: {params}")
                return True

            elif action_type == RepairActionType.RESTART_SERVICE:
                # 实现服务重启逻辑
                logger.info(f"Restarting service: {params}")
                return True

            elif action_type == RepairActionType.SCALE_UP:
                # 实现扩容逻辑
                logger.info(f"Scaling up: {params}")
                return True

            elif action_type == RepairActionType.RATE_LIMIT:
                # 实现限流逻辑
                logger.info(f"Applying rate limit: {params}")
                return True

            elif action_type == RepairActionType.EXECUTE_SCRIPT:
                # 实现脚本执行逻辑
                logger.info(f"Executing script: {params}")
                return True

            elif action_type == RepairActionType.NOTIFY_ADMIN:
                # 实现通知逻辑
                logger.info(f"Notifying admin: {params}")
                return True

            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return False

    def get_pipeline(self, pipeline_id: str) -> Optional[RecoveryPipeline]:
        return self._pipelines.get(pipeline_id)

    def list_pipelines(self, limit: int = 20) -> List[RecoveryPipeline]:
        pipelines = list(self._pipelines.values())
        pipelines.sort(key=lambda p: p.started_at, reverse=True)
        return pipelines[:limit]
```

## 4. API 接口设计

### 4.1 新增 API 端点

在 `src/backend/agent_team_api.py` 中添加：

```python
# 在文件末尾添加

# ---------------------------------------------------------------------------
# Auto Recovery API
# ---------------------------------------------------------------------------

@router.get("/recovery/status")
async def recovery_status():
    """获取自动恢复系统状态"""
    if not _auto_recovery:
        raise HTTPException(404, "Auto recovery not initialized")
    return {
        "active_pipelines": len(_auto_recovery.list_pipelines()),
        "active_freezes": len(_call_freeze.get_active_freezes()),
        "open_breakers": len(_circuit_breaker.get_open_breakers()),
        "pending_tasks": len(_backlog_generator.list_tasks(status="pending")),
    }


@router.get("/recovery/pipelines")
async def recovery_pipelines(limit: int = 20):
    """获取恢复流水线列表"""
    if not _auto_recovery:
        raise HTTPException(404, "Auto recovery not initialized")
    return [p.to_dict() for p in _auto_recovery.list_pipelines(limit=limit)]


@router.get("/recovery/pipelines/{pipeline_id}")
async def recovery_pipeline_detail(pipeline_id: str):
    """获取恢复流水线详情"""
    if not _auto_recovery:
        raise HTTPException(404, "Auto recovery not initialized")
    pipeline = _auto_recovery.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"Pipeline '{pipeline_id}' not found")
    return pipeline.to_dict()


@router.post("/recovery/trigger")
async def trigger_recovery(alert_data: Dict[str, Any]):
    """手动触发自动恢复流程"""
    if not _auto_recovery:
        raise HTTPException(404, "Auto recovery not initialized")
    pipeline = await _auto_recovery.handle_alert(alert_data)
    return pipeline.to_dict()


# ---------------------------------------------------------------------------
# Circuit Breaker API
# ---------------------------------------------------------------------------

@router.get("/circuit-breaker/breakers")
async def list_breakers():
    """获取所有断路器状态"""
    if not _circuit_breaker:
        raise HTTPException(404, "Circuit breaker not initialized")
    return [b.to_dict() for b in _circuit_breaker.get_all_breakers()]


@router.get("/circuit-breaker/breakers/{dimension}")
async def get_breaker(dimension: str):
    """获取指定维度的断路器状态"""
    if not _circuit_breaker:
        raise HTTPException(404, "Circuit breaker not initialized")
    breaker = _circuit_breaker.get_breaker(dimension)
    if not breaker:
        raise HTTPException(404, f"Breaker for dimension '{dimension}' not found")
    return breaker.to_dict()


@router.post("/circuit-breaker/breakers/{dimension}/reset")
async def reset_breaker(dimension: str):
    """手动重置断路器"""
    if not _circuit_breaker:
        raise HTTPException(404, "Circuit breaker not initialized")
    ok = _circuit_breaker.reset_breaker(dimension)
    if not ok:
        raise HTTPException(404, f"Breaker for dimension '{dimension}' not found")
    return {"status": "reset", "dimension": dimension}


# ---------------------------------------------------------------------------
# Repair Templates API
# ---------------------------------------------------------------------------

@router.get("/repair-templates")
async def list_repair_templates():
    """获取所有修复模板"""
    if not _repair_templates:
        raise HTTPException(404, "Repair templates not initialized")
    return [t.to_dict() for t in _repair_templates.list_templates()]


@router.get("/repair-templates/{template_id}")
async def get_repair_template(template_id: str):
    """获取修复模板详情"""
    if not _repair_templates:
        raise HTTPException(404, "Repair templates not initialized")
    template = _repair_templates.get_template(template_id)
    if not template:
        raise HTTPException(404, f"Template '{template_id}' not found")
    return template.to_dict()


@router.get("/repair-templates/executions")
async def list_repair_executions(limit: int = 20):
    """获取修复执行记录"""
    if not _repair_templates:
        raise HTTPException(404, "Repair templates not initialized")
    return [e.to_dict() for e in _repair_templates.list_executions(limit=limit)]


# ---------------------------------------------------------------------------
# Backlog Tasks API
# ---------------------------------------------------------------------------

@router.get("/backlog/tasks")
async def list_backlog_tasks(status: Optional[str] = None):
    """获取 Backlog 任务列表"""
    if not _backlog_generator:
        raise HTTPException(404, "Backlog generator not initialized")
    return [t.to_dict() for t in _backlog_generator.list_tasks(status=status)]


@router.get("/backlog/tasks/{task_id}")
async def get_backlog_task(task_id: str):
    """获取 Backlog 任务详情"""
    if not _backlog_generator:
        raise HTTPException(404, "Backlog generator not initialized")
    task = _backlog_generator.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task.to_dict()


@router.post("/backlog/tasks/{task_id}/status")
async def update_backlog_task_status(task_id: str, status: str = "completed"):
    """更新 Backlog 任务状态"""
    if not _backlog_generator:
        raise HTTPException(404, "Backlog generator not initialized")
    ok = _backlog_generator.update_task_status(task_id, status)
    if not ok:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return {"status": "updated", "task_id": task_id, "new_status": status}


# ---------------------------------------------------------------------------
# Call Freeze API
# ---------------------------------------------------------------------------

@router.get("/call-freeze/status")
async def call_freeze_status():
    """获取调用冻结状态"""
    if not _call_freeze:
        raise HTTPException(404, "Call freeze not initialized")
    return {
        "active_freezes": [f.to_dict() for f in _call_freeze.get_active_freezes()],
        "stats": _call_freeze.get_freeze_stats(),
    }


@router.post("/call-freeze/recover-all")
async def recover_all_freezes():
    """恢复所有冻结"""
    if not _call_freeze:
        raise HTTPException(404, "Call freeze not initialized")
    count = _call_freeze.recover_all()
    return {"status": "recovered", "count": count}


# ---------------------------------------------------------------------------
# Abduction Reports API
# ---------------------------------------------------------------------------

@router.get("/abduction/reports")
async def list_abduction_reports(limit: int = 20):
    """获取溯因报告列表"""
    if not _abduction_engine:
        raise HTTPException(404, "Abduction engine not initialized")
    return [r.to_dict() for r in _abduction_engine.list_reports(limit=limit)]


@router.get("/abduction/reports/{report_id}")
async def get_abduction_report(report_id: str):
    """获取溯因报告详情"""
    if not _abduction_engine:
        raise HTTPException(404, "Abduction engine not initialized")
    report = _abduction_engine.get_report(report_id)
    if not report:
        raise HTTPException(404, f"Report '{report_id}' not found")
    return report.to_dict()
```

### 4.2 全局变量注入

在 `agent_team_api.py` 中添加全局变量：

```python
# 在文件顶部添加
_auto_recovery = None
_circuit_breaker = None
_repair_templates = None
_backlog_generator = None
_call_freeze = None
_abduction_engine = None
```

更新 `set_teams` 函数：

```python
def set_teams(build_team, execution_team, scheduler, evolution_engine=None,
              auto_recovery=None, circuit_breaker=None, repair_templates=None,
              backlog_generator=None, call_freeze=None, abduction_engine=None):
    """在应用启动时由 main.py 调用，注入团队实例."""
    global _build_team, _execution_team, _scheduler, _evolution_engine
    global _auto_recovery, _circuit_breaker, _repair_templates
    global _backlog_generator, _call_freeze, _abduction_engine
    _build_team = build_team
    _execution_team = execution_team
    _scheduler = scheduler
    _evolution_engine = evolution_engine
    _auto_recovery = auto_recovery
    _circuit_breaker = circuit_breaker
    _repair_templates = repair_templates
    _backlog_generator = backlog_generator
    _call_freeze = call_freeze
    _abduction_engine = abduction_engine
```

## 5. 需要修改的文件

### 5.1 新增文件

1. **`src/backend/monitoring/abduction_engine.py`** - 侵入式溯因引擎
2. **`src/backend/monitoring/circuit_breaker.py`** - 维度断路器管理器
3. **`src/backend/monitoring/repair_templates.py`** - 修复模板仓库
4. **`src/backend/monitoring/backlog_generator.py`** - Backlog 自动生成器
5. **`src/backend/monitoring/call_freeze.py`** - 调用冻结管理器
6. **`src/backend/monitoring/auto_recovery_orchestrator.py`** - 自动恢复编排器

### 5.2 修改文件

1. **`src/backend/agent_team_api.py`** - 添加自动恢复相关 API 端点
2. **`src/backend/main.py`** - 初始化自动恢复组件并注入
3. **`src/backend/monitoring/__init__.py`** - 导出新模块

## 6. 实施步骤

### 步骤 1: 创建基础数据模型
- 实现 `abduction_engine.py` 中的 `AbductionProbe`, `AbductionEvidence`, `RootCause`, `AbductionReport`
- 实现 `circuit_breaker.py` 中的 `CircuitBreakerConfig`, `DimensionBreaker`
- 实现 `repair_templates.py` 中的 `RepairAction`, `RepairTemplate`, `RepairExecution`
- 实现 `backlog_generator.py` 中的 `BacklogTask`
- 实现 `call_freeze.py` 中的 `FreezeRule`, `FreezeState`

### 步骤 2: 实现核心逻辑
- 实现 `AbductionEngine` 的告警分析流程
- 实现 `CircuitBreakerManager` 的断路器状态管理
- 实现 `RepairTemplateRepository` 的模板匹配逻辑
- 实现 `BacklogGenerator` 的任务生成逻辑
- 实现 `CallFreezeManager` 的冻结管理逻辑

### 步骤 3: 实现编排器
- 实现 `AutoRecoveryOrchestrator` 的告警处理流水线
- 集成所有组件

### 步骤 4: 添加 API 端点
- 在 `agent_team_api.py` 中添加所有新端点
- 更新 `set_teams` 函数

### 步骤 5: 更新 main.py
- 初始化所有新组件
- 注入到 API 路由

### 步骤 6: 测试
- 编写单元测试
- 编写集成测试
- 测试端到端流程

## 7. 测试计划

### 7.1 单元测试

```python
# tests/test_abduction_engine.py
# tests/test_circuit_breaker.py
# tests/test_repair_templates.py
# tests/test_backlog_generator.py
# tests/test_call_freeze.py
# tests/test_auto_recovery_orchestrator.py
```

### 7.2 集成测试

```python
# tests/test_auto_recovery_integration.py
```

测试场景：
1. 模拟告警触发 → 溯因分析 → 断路器触发 → 修复模板匹配 → Backlog 生成 → 调用冻结
2. 断路器自动恢复
3. 冻结自动恢复
4. 修复模板匹配失败时的降级处理
5. 并发告警处理

## 8. 前端集成

在 `src/frontend/system-evolution.html` 中添加自动恢复监控面板：

```html
<!-- 在 system-evolution.html 中添加 -->
<div class="auto-recovery-panel">
    <h3>自动恢复系统</h3>
    <div class="recovery-stats">
        <div class="stat-card">
            <span class="stat-label">活跃流水线</span>
            <span class="stat-value" id="active-pipelines">0</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">活跃冻结</span>
            <span class="stat-value" id="active-freezes">0</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">开启断路器</span>
            <span class="stat-value" id="open-breakers">0</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">待处理任务</span>
            <span class="stat-value" id="pending-tasks">0</span>
        </div>
    </div>
</div>
```

在 `src/frontend/js/agent-team-config.js` 中添加自动恢复 API 调用：

```javascript
// 在 agent-team-config.js 中添加
async function loadAutoRecoveryStatus() {
    try {
        const response = await fetch('/api/v1/agent-teams/recovery/status');
        const data = await response.json();
        document.getElementById('active-pipelines').textContent = data.active_pipelines;
        document.getElementById('active-freezes').textContent = data.active_freezes;
        document.getElementById('open-breakers').textContent = data.open_breakers;
        document.getElementById('pending-tasks').textContent = data.pending_tasks;
    } catch (error) {
        console.error('Failed to load auto recovery status:', error);
    }
}
```

## 9. 总结

本方案实现了完整的告警驱动自动修复系统：

1. **侵入式溯因**：通过部署探测点收集多维上下文数据，使用规则和 LLM 辅助分析根因
2. **维度断路器**：按维度管理断路器状态，自动熔断异常维度
3. **修复模板绑定**：根据根因自动匹配预定义的修复模板
4. **自动生成 Backlog**：创建修复任务并分配给 Build 团队
5. **冻结非关键调用**：根据告警严重度自动冻结非关键调用

系统通过 `AutoRecoveryOrchestrator` 统一协调各组件，提供完整的告警处理流水线。

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
