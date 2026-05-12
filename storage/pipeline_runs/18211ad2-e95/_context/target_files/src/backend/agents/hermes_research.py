# -*- coding: utf-8 -*-
"""AgentsGroup2026 — Hermes-style Research Agent Module.

Transforms the Research Agent from a read-only advisory role into a
self-improving research agent inspired by NousResearch/hermes-agent:

Architecture mapping (Hermes → AgentsGroup2026):
  - AIAgent class         → HermesResearchAgent
  - run_conversation()    → agent_loop()
  - toolsets.py           → RESEARCH_TOOLSET_DISTRIBUTIONS
  - prompt_builder.py     → build_research_system_prompt()
  - SOUL.md               → agent.hermes_config.soul_md
  - Memory/Skills nudge   → MEMORY_GUIDANCE / SKILLS_GUIDANCE
  - Delegate subagents    → delegate_task()
  - Session search        → session_search()

Key Hermes characteristics adopted:
  1. Closed learning loop — auto-create skills from complex research
  2. Persistent memory — save research findings across sessions
  3. Probabilistic toolset distribution — web 90%, browser 70%, vision 50%
  4. SOUL.md — research persona
  5. Context files — AGENTS.md project context
  6. Tool-use enforcement — tools must be used, not just described
  7. Session search — cross-session recall of past research
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import (
    AgentProfile,
    AgentTemplateType,
    AgentPersonality,
    HermesAgentConfig,
    ToolsetDistribution,
)


# ══════════════════════════════════════════════════════════════
# Hermes-style Toolset Distributions
# Inspired by NousResearch/hermes-agent/toolset_distributions.py
# ══════════════════════════════════════════════════════════════

RESEARCH_TOOLSET_DISTRIBUTIONS: Dict[str, Dict[str, Any]] = {
    "general_research": {
        "description": "General domain research — literature review, data analysis, technical investigation",
        "toolsets": {
            "web": 90,
            "browser": 70,
            "vision": 50,
            "file": 80,
            "research": 95,
            "memory": 100,
            "skills": 100,
            "delegation": 30,
        },
    },
    "deep_analysis": {
        "description": "Deep analysis — systematic review, data verification, cross-referencing",
        "toolsets": {
            "web": 60,
            "file": 95,
            "research": 100,
            "code_execution": 80,
            "memory": 100,
            "vision": 40,
        },
    },
    "compliance_audit": {
        "description": "Standards and compliance verification",
        "toolsets": {
            "web": 85,
            "browser": 65,
            "file": 90,
            "research": 100,
            "code_execution": 70,
            "memory": 100,
        },
    },
    "technical_review": {
        "description": "Technical design review, architecture analysis, code review",
        "toolsets": {
            "web": 50,
            "file": 95,
            "code_execution": 90,
            "research": 100,
            "vision": 70,
            "memory": 100,
        },
    },
    "general_research": {
        "description": "General web research with all tools available",
        "toolsets": {
            "web": 90,
            "browser": 70,
            "vision": 50,
            "memory": 100,
            "skills": 100,
            "file": 60,
            "code_execution": 30,
        },
    },
}

# ══════════════════════════════════════════════════════════════
# Hermes-style Toolset Definitions
# Inspired by NousResearch/hermes-agent/toolsets.py
# ══════════════════════════════════════════════════════════════

HERMES_TOOLSETS: Dict[str, Dict[str, Any]] = {
    "web": {
        "description": "Web research and content extraction",
        "tools": ["web_search", "extract_content"],
    },
    "browser": {
        "description": "Browser automation for deep research",
        "tools": ["navigate_url", "screenshot", "click_element", "fill_form", "extract_content", "web_search"],
    },
    "file": {
        "description": "File read/write/search operations",
        "tools": ["read_file", "write_file", "list_directory", "search_files"],
    },
    "code_execution": {
        "description": "Run Python/shell for analysis and calculation",
        "tools": ["run_python", "run_shell"],
    },
    "vision": {
        "description": "Image/chart analysis for technical documents",
        "tools": ["screenshot"],
    },
    "research": {
        "description": "Research-specific tools — search, analysis, data retrieval",
        "tools": ["search_query", "data_lookup", "info_fetch", "analysis_engine"],
    },
    "memory": {
        "description": "Persistent memory and session search",
        "tools": ["memory_save", "memory_read", "session_search"],
    },
    "skills": {
        "description": "Skill management — list, view, create, patch",
        "tools": ["skill_list", "skill_view", "skill_manage"],
    },
    "delegation": {
        "description": "Spawn subagents for parallel research tasks",
        "tools": ["delegate_task"],
    },
}


def sample_toolsets(distribution_name: str) -> List[str]:
    """Sample toolsets based on distribution probabilities.

    Each toolset rolls independently — multiple can be active.
    Mirrors NousResearch/hermes-agent/toolset_distributions.py logic.
    """
    dist = RESEARCH_TOOLSET_DISTRIBUTIONS.get(distribution_name)
    if not dist:
        dist = RESEARCH_TOOLSET_DISTRIBUTIONS["general_research"]

    selected = []
    for toolset_name, probability in dist["toolsets"].items():
        if random.random() * 100 < probability:
            selected.append(toolset_name)

    # Ensure at least one toolset
    if not selected and dist["toolsets"]:
        highest = max(dist["toolsets"].items(), key=lambda x: x[1])
        selected.append(highest[0])

    return selected


def resolve_tools(toolset_names: List[str]) -> List[str]:
    """Resolve toolset names to individual tool IDs."""
    tools: set[str] = set()
    for name in toolset_names:
        ts = HERMES_TOOLSETS.get(name)
        if ts:
            tools.update(ts["tools"])
    return sorted(tools)


# ══════════════════════════════════════════════════════════════
# Hermes-style System Prompt Builder
# Inspired by NousResearch/hermes-agent/agent/prompt_builder.py
# ══════════════════════════════════════════════════════════════

MARINE_RESEARCHER_IDENTITY = (
    "You are AgentsGroup2026 Research Agent, an intelligent research agent "
    "built on the Hermes Agent architecture from Nous Research. "
    "You are a self-improving researcher with a closed learning loop — "
    "you create skills from experience, improve them during use, persist knowledge, "
    "and build deepening expertise across research sessions.\n\n"
    "Your research expertise includes:\n"
    "- Literature review, systematic analysis, and cross-referencing\n"
    "- Technical standards research and compliance verification\n"
    "- Data analysis, formula validation, and computational verification\n"
    "- Architecture review, design pattern analysis, and best practices\n"
    "- Multi-source information synthesis and knowledge extraction\n\n"
    "You communicate in Chinese with English technical terms preserved."
)

MEMORY_GUIDANCE = (
    "You have persistent memory across sessions. Save durable facts using the memory "
    "tool: research findings, domain conventions, technical citations, calculation results. "
    "Memory is injected into every turn, so keep it compact and focused on facts that "
    "will still matter later.\n"
    "Prioritize what reduces future user steering — the most valuable memory is one "
    "that prevents the user from having to correct or remind you again. "
    "Technical standards, validated formulas, and verified references are high-value.\n"
    "Do NOT save task progress, session outcomes, or temporary TODO state to memory; "
    "use session_search to recall those from past transcripts."
)

SKILLS_GUIDANCE = (
    "After completing a complex research task (5+ tool calls), validating a formula, "
    "or discovering a non-trivial analysis workflow, save the approach as a "
    "skill with skill_manage so you can reuse it next time.\n"
    "When using a skill and finding it outdated or wrong, "
    "patch it immediately with skill_manage(action='patch').\n"
    "Skills to prioritize: standard lookup workflows, calculation verification, "
    "literature review patterns, compliance audit procedures."
)

SESSION_SEARCH_GUIDANCE = (
    "When the user references something from a past research session or you suspect "
    "relevant cross-session context exists, use session_search to recall it before "
    "asking them to repeat themselves."
)

TOOL_USE_ENFORCEMENT = (
    "# Tool-use enforcement\n"
    "You MUST use your tools to take action — do not describe what you would do "
    "or plan to do without actually doing it. When you say you will perform a "
    "research action (e.g. 'I will check the standard', 'Let me verify the formula'), "
    "you MUST immediately make the corresponding tool call in the same response.\n"
    "Every response should either (a) contain tool calls that make progress, or "
    "(b) deliver a final research result to the user."
)


def build_research_system_prompt(
    agent: AgentProfile,
    active_toolsets: Optional[List[str]] = None,
) -> str:
    """Build the full Hermes-style system prompt for a research agent.

    Assembles: identity → memory guidance → skills guidance → tool enforcement
    → context files → SOUL.md persona.

    Mirrors NousResearch/hermes-agent/agent/prompt_builder.py structure.
    """
    sections: List[str] = []

    # 1. Identity (SOUL.md or default)
    hc = agent.hermes_config
    if hc and hc.soul_md:
        sections.append(hc.soul_md)
    else:
        sections.append(MARINE_RESEARCHER_IDENTITY)

    # 2. Memory guidance
    if hc and hc.memory_enabled:
        sections.append(MEMORY_GUIDANCE)

    # 3. Session search guidance
    if hc and hc.session_search_enabled:
        sections.append(SESSION_SEARCH_GUIDANCE)

    # 4. Skills guidance
    if hc and hc.skill_auto_create:
        sections.append(SKILLS_GUIDANCE)

    # 5. Tool-use enforcement
    sections.append(TOOL_USE_ENFORCEMENT)

    # 6. Available toolsets
    if active_toolsets:
        ts_lines = ["## Active Toolsets"]
        for ts_name in active_toolsets:
            ts = HERMES_TOOLSETS.get(ts_name)
            if ts:
                ts_lines.append(f"- **{ts_name}**: {ts['description']} — tools: {', '.join(ts['tools'])}")
        sections.append("\n".join(ts_lines))

    # 7. Context files
    if hc and hc.context_files:
        context_header = "## Project Context\nThe following project context files are loaded:\n"
        sections.append(context_header + "\n".join(f"- {f}" for f in hc.context_files))

    # 8. Research reference files
    sections.append(
        "## Key Research Reference Files\n"
        "- `docs/requirements_analysis.md` — Project requirements and specifications\n"
        "- `docs/gap_analysis.md` — Gap analysis and improvement areas\n"
        "- `docs/architecture.md` — System architecture documentation\n"
        "- `config/settings.json` — System configuration and parameters"
    )

    return "\n\n".join(sections)


# ══════════════════════════════════════════════════════════════
# Hermes-style Agent Factory
# ══════════════════════════════════════════════════════════════

# Default SOUL.md for the research agent
MARINE_RESEARCHER_SOUL = """# Research Agent

You are AgentsGroup2026's research specialist, powered by Hermes Agent architecture.

## Core Identity
I am a domain expert in systematic research, technical analysis, and knowledge synthesis.
I research, validate, and advise — producing rigorous analysis backed by authoritative sources.

## Personality
- Rigorous and methodical — every claim must cite a source or provide evidence
- Proactive learner — after solving a complex problem, I save it as a skill
- Memory-driven — I persist key findings so I never repeat the same research twice
- Collaborative — I can delegate sub-research tasks to specialized agents

## Research Domains
1. **Literature Review** — systematic search, source evaluation, cross-referencing
2. **Technical Analysis** — architecture review, design patterns, best practices
3. **Data Verification** — formula validation, calculation checking, data integrity
4. **Standards Compliance** — industry standards, regulatory requirements, audit
5. **Knowledge Synthesis** — multi-source integration, summary generation, insight extraction

## Behavioral Rules
- Always cite specific sources, standards, or evidence
- Never guess parameter ranges — look them up
- After 5+ tool calls on a complex task, offer to save as a reusable skill
- Write in Chinese, keep English for technical terms
"""


def create_hermes_researcher(
    name: str = "Research Agent",
    distribution: str = "general_research",
    soul_md: str = "",
    can_delegate: bool = True,
) -> AgentProfile:
    """Create a Hermes-style research agent.

    Returns an AgentProfile with HermesAgentConfig attached,
    pre-configured with the research toolset distribution,
    SOUL.md persona, and self-improving skill/memory capabilities.
    """
    dist = RESEARCH_TOOLSET_DISTRIBUTIONS.get(distribution)
    if not dist:
        dist = RESEARCH_TOOLSET_DISTRIBUTIONS["general_research"]

    hermes_config = HermesAgentConfig(
        max_iterations=90,
        iteration_budget=90,
        toolset_distribution=ToolsetDistribution(
            name=distribution,
            description=dist["description"],
            toolsets=dict(dist["toolsets"]),
        ),
        enabled_toolsets=list(dist["toolsets"].keys()),
        disabled_toolsets=[],
        memory_enabled=True,
        session_search_enabled=True,
        skill_auto_create=True,
        soul_md=soul_md or MARINE_RESEARCHER_SOUL,
        context_files=[
            "AGENTS.md",
            "docs/SJTU_REQUIREMENTS_ANALYSIS.md",
            "docs/requirements_analysis.md",
            "docs/gap_analysis.md",
        ],
        can_delegate=can_delegate,
        max_subagents=3,
        platform="cli",
    )

    agent = AgentProfile(
        name=name,
        role="研究员 (Hermes Agent)",
        description=(
            "Hermes-style self-improving research agent — "
            "literature review, technical analysis, data verification, "
            "standards compliance, and knowledge synthesis. "
            "Closed learning loop with skills, memory, and session search."
        ),
        template_type=AgentTemplateType.HERMES_RESEARCHER,
        system_prompt="",  # Built dynamically via build_research_system_prompt()
        personality=AgentPersonality(
            tone="professional",
            language="zh-CN",
            expertise_areas=[
                "literature review",
                "technical analysis",
                "data verification",
                "standards compliance",
                "knowledge synthesis",
                "cross-referencing",
            ],
            response_style="rigorous",
            creativity=0.3,
        ),
        tools=[],  # Resolved dynamically from toolset distribution
        skills=[],  # Populated from research skill registry
        hermes_config=hermes_config,
    )

    # Build the initial system prompt
    active_toolsets = sample_toolsets(distribution)
    agent.system_prompt = build_research_system_prompt(agent, active_toolsets)
    agent.tools = resolve_tools(active_toolsets)

    return agent


# ══════════════════════════════════════════════════════════════
# Hermes-style Agent Loop (simplified)
# Inspired by NousResearch/hermes-agent/run_agent.py AIAgent class
# ══════════════════════════════════════════════════════════════

@dataclass
class AgentTurn:
    """A single turn in the agent conversation loop."""
    role: str = "user"
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentSession:
    """Hermes-style conversation session for the research agent."""
    session_id: str = ""
    agent_id: str = ""
    messages: List[AgentTurn] = field(default_factory=list)
    api_call_count: int = 0
    max_iterations: int = 90
    skills_created: List[str] = field(default_factory=list)
    memories_saved: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "turn_count": len(self.messages),
            "api_call_count": self.api_call_count,
            "max_iterations": self.max_iterations,
            "skills_created": self.skills_created,
            "memories_saved": self.memories_saved,
        }


def get_research_distributions() -> Dict[str, Dict[str, Any]]:
    """Return all available research toolset distributions."""
    return {k: {"description": v["description"], "toolsets": v["toolsets"]}
            for k, v in RESEARCH_TOOLSET_DISTRIBUTIONS.items()}


def get_hermes_toolsets() -> Dict[str, Dict[str, Any]]:
    """Return all Hermes-style toolset definitions."""
    return {k: {"description": v["description"], "tools": v["tools"]}
            for k, v in HERMES_TOOLSETS.items()}
