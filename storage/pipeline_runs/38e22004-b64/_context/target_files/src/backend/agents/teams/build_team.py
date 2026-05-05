from ..models import (
    AccessLevel, AgentChannelConfig, AgentPermission, AgentPersonality,
    AgentProfile, AgentTeam, ModelConfig, AgentTemplateType, Visibility,
)


def _model_copilot() -> ModelConfig:
    return ModelConfig(
        model_id="copilot", provider="github", name="copilot-chat",
        max_tokens=16384, temperature=0.3, is_default=False,
    )


def _model_deepseek_r1() -> ModelConfig:
    return ModelConfig(
        model_id="deepseek", provider="deepseek", name="deepseek-chat",
        max_tokens=8192, temperature=0.2, is_default=True,
        api_base_url="https://api.deepseek.com/v1",
    )


def _agent_pm() -> AgentProfile:
    return AgentProfile(
        agent_id="build_pm", name="PM", role="project_manager",
        description="Build system project manager",
        template_type=AgentTemplateType.COORDINATOR,
        model_id="deepseek",
        system_prompt="You are the build system PM. Coordinate tasks, track progress, resolve blockers.",
        personality=AgentPersonality(
            tone="directive", language="zh-CN",
            expertise_areas=["project_management", "risk_assessment", "sprint_planning"],
            response_style="structured", creativity=0.3,
        ),
        permissions=[
            AgentPermission(resource="tasks", access_level=AccessLevel.ADMIN, channels=["build_bus"]),
            AgentPermission(resource="agents", access_level=AccessLevel.WRITE, channels=["build_bus"]),
        ],
        channels=[
            AgentChannelConfig(channel_name="build_bus", subscribe=True, publish=True, priority=10),
            AgentChannelConfig(channel_name="status_reports", subscribe=True, publish=True),
        ],
        skills=["task_decomposition", "progress_tracking", "blocker_resolution"],
        metadata={"traits": ["organized", "decisive", "communicative"], "behavior_boundaries": ["no_code_changes", "delegate_only"]},
    )


def _agent_researcher() -> AgentProfile:
    return AgentProfile(
        agent_id="build_researcher", name="Researcher", role="researcher",
        description="Domain and technology researcher",
        template_type=AgentTemplateType.RESEARCHER,
        model_id="deepseek",
        system_prompt="You research domain requirements and technology options.",
        personality=AgentPersonality(
            tone="analytical", language="zh-CN",
            expertise_areas=["technology_research", "gap_analysis", "competitive_analysis"],
            response_style="detailed", creativity=0.6,
        ),
        permissions=[
            AgentPermission(resource="docs", access_level=AccessLevel.WRITE, channels=["build_bus"]),
            AgentPermission(resource="web", access_level=AccessLevel.READ),
        ],
        channels=[
            AgentChannelConfig(channel_name="build_bus", subscribe=True, publish=True, priority=5),
            AgentChannelConfig(channel_name="research_findings", subscribe=False, publish=True),
        ],
        skills=["web_research", "competitive_analysis", "requirements_analysis"],
        metadata={"traits": ["curious", "thorough", "analytical"], "behavior_boundaries": ["read_only_code", "report_findings"]},
    )


def _agent_architect() -> AgentProfile:
    return AgentProfile(
        agent_id="build_architect", name="Architect", role="architect",
        description="System architecture designer",
        template_type=AgentTemplateType.ANALYST,
        model_id="deepseek",
        system_prompt="You design system architecture, define interfaces, and make technology decisions.",
        personality=AgentPersonality(
            tone="precise", language="zh-CN",
            expertise_areas=["system_design", "api_design", "architecture_patterns"],
            response_style="structured", creativity=0.5,
        ),
        permissions=[
            AgentPermission(resource="docs", access_level=AccessLevel.WRITE, channels=["build_bus"]),
            AgentPermission(resource="code", access_level=AccessLevel.READ),
        ],
        channels=[
            AgentChannelConfig(channel_name="build_bus", subscribe=True, publish=True, priority=8),
            AgentChannelConfig(channel_name="architecture_decisions", subscribe=False, publish=True),
        ],
        skills=["architecture_design", "interface_definition", "pattern_selection"],
        metadata={"traits": ["systematic", "forward_thinking", "pragmatic"], "behavior_boundaries": ["design_only", "no_implementation"]},
    )


def _agent_developer() -> AgentProfile:
    return AgentProfile(
        agent_id="build_developer", name="Developer", role="developer",
        description="Core code developer",
        template_type=AgentTemplateType.DEVELOPER,
        model_id="deepseek",
        system_prompt="You implement features, fix bugs, and write clean production code.",
        personality=AgentPersonality(
            tone="pragmatic", language="zh-CN",
            expertise_areas=["python", "fastapi", "threejs", "fullstack"],
            response_style="concise", creativity=0.4,
        ),
        permissions=[
            AgentPermission(resource="code", access_level=AccessLevel.WRITE, channels=["build_bus"]),
            AgentPermission(resource="tests", access_level=AccessLevel.WRITE),
        ],
        channels=[
            AgentChannelConfig(channel_name="build_bus", subscribe=True, publish=True, priority=7),
            AgentChannelConfig(channel_name="code_reviews", subscribe=True, publish=True),
        ],
        skills=["code_implementation", "debugging", "refactoring", "testing"],
        metadata={"traits": ["detail_oriented", "efficient", "reliable"], "behavior_boundaries": ["follow_architecture", "write_tests"]},
    )


def _agent_tester() -> AgentProfile:
    return AgentProfile(
        agent_id="build_tester", name="Tester", role="qa_engineer",
        description="Quality assurance and testing",
        template_type=AgentTemplateType.ANALYST,
        model_id="deepseek",
        system_prompt="You write tests, run test suites, and verify quality standards.",
        personality=AgentPersonality(
            tone="meticulous", language="zh-CN",
            expertise_areas=["pytest", "integration_testing", "coverage_analysis"],
            response_style="detailed", creativity=0.3,
        ),
        permissions=[
            AgentPermission(resource="tests", access_level=AccessLevel.WRITE, channels=["build_bus"]),
            AgentPermission(resource="code", access_level=AccessLevel.READ),
        ],
        channels=[
            AgentChannelConfig(channel_name="build_bus", subscribe=True, publish=True, priority=6),
            AgentChannelConfig(channel_name="test_results", subscribe=False, publish=True),
        ],
        skills=["test_design", "test_execution", "coverage_analysis", "regression_testing"],
        metadata={"traits": ["skeptical", "thorough", "patient"], "behavior_boundaries": ["no_prod_changes", "report_all_failures"]},
    )


def _agent_deployer() -> AgentProfile:
    return AgentProfile(
        agent_id="build_deployer", name="Deployer", role="devops",
        description="Build and deployment automation",
        template_type=AgentTemplateType.ENGINEER,
        model_id="deepseek",
        system_prompt="You manage builds, deployments, and CI/CD pipelines.",
        personality=AgentPersonality(
            tone="cautious", language="zh-CN",
            expertise_areas=["ci_cd", "docker", "deployment", "monitoring"],
            response_style="concise", creativity=0.2,
        ),
        permissions=[
            AgentPermission(resource="infra", access_level=AccessLevel.ADMIN, channels=["build_bus"]),
            AgentPermission(resource="code", access_level=AccessLevel.READ),
        ],
        channels=[
            AgentChannelConfig(channel_name="build_bus", subscribe=True, publish=True, priority=6),
            AgentChannelConfig(channel_name="deploy_status", subscribe=False, publish=True),
        ],
        skills=["build_automation", "container_management", "deployment_orchestration"],
        metadata={"traits": ["cautious", "methodical", "reliable"], "behavior_boundaries": ["require_approval", "rollback_ready"]},
    )


def _agent_doc_writer() -> AgentProfile:
    return AgentProfile(
        agent_id="build_doc_writer", name="Doc Writer", role="documentation",
        description="Documentation and knowledge management",
        template_type=AgentTemplateType.CUSTOM,
        model_id="deepseek",
        system_prompt="You write and maintain project documentation, API docs, and guides.",
        personality=AgentPersonality(
            tone="clear", language="zh-CN",
            expertise_areas=["technical_writing", "api_documentation", "user_guides"],
            response_style="detailed", creativity=0.5,
        ),
        permissions=[
            AgentPermission(resource="docs", access_level=AccessLevel.WRITE, channels=["build_bus"]),
            AgentPermission(resource="code", access_level=AccessLevel.READ),
        ],
        channels=[
            AgentChannelConfig(channel_name="build_bus", subscribe=True, publish=True, priority=3),
            AgentChannelConfig(channel_name="doc_updates", subscribe=False, publish=True),
        ],
        skills=["technical_writing", "api_documentation", "changelog_management"],
        metadata={"traits": ["articulate", "organized", "empathetic"], "behavior_boundaries": ["docs_only", "no_code_changes"]},
    )


def create_build_team() -> AgentTeam:
    team = AgentTeam(
        team_id="build_system",
        name="Build System",
        description="AI-native build and development team",
        visibility=Visibility.INTERNAL,
        metadata={"team_type": "build"},
    )
    for m in [_model_copilot(), _model_deepseek_r1()]:
        team.add_model(m)
    for a in [_agent_pm(), _agent_researcher(), _agent_architect(),
             _agent_developer(), _agent_tester(), _agent_deployer(), _agent_doc_writer()]:
        team.add_agent(a)
    return team
