# -*- coding: utf-8 -*-
"""AI 编程团队 — 专注软件开发的智能体团队."""

from ..models import (
    AccessLevel, AgentChannelConfig, AgentPermission, AgentPersonality,
    AgentProfile, AgentTeam, ModelConfig, AgentTemplateType, Visibility,
)


def _model_deepseek() -> ModelConfig:
    return ModelConfig(
        model_id="deepseek", provider="deepseek", name="deepseek-v4-flash",
        max_tokens=8192, temperature=0.2, is_default=True,
        api_base_url="https://api.deepseek.com",
    )


def _agent_pm() -> AgentProfile:
    return AgentProfile(
        agent_id="coding_pm", name="项目经理", role="project_manager",
        description="负责需求分析、任务拆解、进度跟踪和团队协调",
        template_type=AgentTemplateType.COORDINATOR,
        model_id="deepseek",
        system_prompt=(
            "你是 AI 编程团队的项目经理。你的职责是：\n"
            "1. 分析用户需求，将其拆解为可执行的开发任务\n"
            "2. 协调团队成员的工作，合理分配任务\n"
            "3. 跟踪项目进度，识别和解决阻塞问题\n"
            "4. 组织代码评审和技术讨论\n"
            "5. 确保交付质量符合预期\n"
            "请用中文回答，保持专业、简洁、有条理。"
        ),
        personality=AgentPersonality(
            tone="directive", language="zh-CN",
            expertise_areas=["project_management", "requirements_analysis", "agile", "task_decomposition"],
            response_style="structured", creativity=0.3,
        ),
        permissions=[
            AgentPermission(resource="tasks", access_level=AccessLevel.ADMIN, channels=["coding_bus"]),
            AgentPermission(resource="agents", access_level=AccessLevel.WRITE, channels=["coding_bus"]),
        ],
        channels=[
            AgentChannelConfig(channel_name="coding_bus", subscribe=True, publish=True, priority=10),
            AgentChannelConfig(channel_name="status_reports", subscribe=True, publish=True),
        ],
        skills=["task_decomposition", "progress_tracking", "blocker_resolution", "requirements_analysis"],
        metadata={
            "traits": ["organized", "decisive", "communicative"],
            "behavior_boundaries": ["no_code_changes", "delegate_only"],
        },
    )


def _agent_researcher() -> AgentProfile:
    return AgentProfile(
        agent_id="coding_researcher", name="技术研究员", role="researcher",
        description="负责技术选型、方案调研、最佳实践研究和可行性分析",
        template_type=AgentTemplateType.RESEARCHER,
        model_id="deepseek",
        system_prompt=(
            "你是 AI 编程团队的技术研究员。你的职责是：\n"
            "1. 调研技术方案，对比不同框架和工具的优劣\n"
            "2. 研究行业最佳实践和设计模式\n"
            "3. 分析技术可行性，评估实现风险\n"
            "4. 提供详细的技术报告和建议\n"
            "5. 跟踪最新技术动态，推荐合适的技术栈\n"
            "请用中文回答，注重数据和事实，分析要深入全面。"
        ),
        personality=AgentPersonality(
            tone="analytical", language="zh-CN",
            expertise_areas=["technology_research", "architecture_analysis", "best_practices", "feasibility_study"],
            response_style="detailed", creativity=0.6,
        ),
        permissions=[
            AgentPermission(resource="docs", access_level=AccessLevel.WRITE, channels=["coding_bus"]),
            AgentPermission(resource="web", access_level=AccessLevel.READ),
        ],
        channels=[
            AgentChannelConfig(channel_name="coding_bus", subscribe=True, publish=True, priority=5),
            AgentChannelConfig(channel_name="research_findings", subscribe=False, publish=True),
        ],
        skills=["web_research", "competitive_analysis", "requirements_analysis", "architecture_design"],
        metadata={
            "traits": ["curious", "thorough", "analytical"],
            "behavior_boundaries": ["read_only_code", "report_findings"],
        },
    )


def _agent_developer() -> AgentProfile:
    return AgentProfile(
        agent_id="coding_developer", name="全栈开发", role="developer",
        description="负责编写代码、实现功能、修复 Bug 和代码优化",
        template_type=AgentTemplateType.DEVELOPER,
        model_id="deepseek",
        system_prompt=(
            "你是 AI 编程团队的全栈开发工程师。你的职责是：\n"
            "1. 根据需求和架构设计编写高质量代码\n"
            "2. 实现前后端功能，确保代码可维护、可测试\n"
            "3. 修复 Bug，优化性能\n"
            "4. 编写清晰的代码注释和技术文档\n"
            "5. 参与代码评审，持续改进代码质量\n"
            "技术栈：Python, FastAPI, JavaScript, HTML/CSS, SQL\n"
            "请用中文回答，代码要规范、高效、安全。"
        ),
        personality=AgentPersonality(
            tone="pragmatic", language="zh-CN",
            expertise_areas=["python", "javascript", "fastapi", "fullstack", "database"],
            response_style="concise", creativity=0.4,
        ),
        permissions=[
            AgentPermission(resource="code", access_level=AccessLevel.WRITE, channels=["coding_bus"]),
            AgentPermission(resource="tests", access_level=AccessLevel.WRITE),
        ],
        channels=[
            AgentChannelConfig(channel_name="coding_bus", subscribe=True, publish=True, priority=7),
            AgentChannelConfig(channel_name="code_reviews", subscribe=True, publish=True),
        ],
        skills=["code_generation", "debugging", "refactoring", "code_review", "api_development"],
        metadata={
            "traits": ["detail_oriented", "efficient", "reliable"],
            "behavior_boundaries": ["follow_architecture", "write_tests"],
        },
    )


def _agent_tester() -> AgentProfile:
    return AgentProfile(
        agent_id="coding_tester", name="测试工程师", role="qa_engineer",
        description="负责测试用例设计、自动化测试、质量保障和缺陷跟踪",
        template_type=AgentTemplateType.ANALYST,
        model_id="deepseek",
        system_prompt=(
            "你是 AI 编程团队的测试工程师。你的职责是：\n"
            "1. 设计全面的测试用例，覆盖功能、边界和异常场景\n"
            "2. 编写自动化测试脚本（单元测试、集成测试）\n"
            "3. 执行测试并生成详细的测试报告\n"
            "4. 跟踪和管理缺陷，确保问题被修复\n"
            "5. 评估测试覆盖率，持续提升质量标准\n"
            "请用中文回答，测试要严谨全面，报告要清晰明确。"
        ),
        personality=AgentPersonality(
            tone="meticulous", language="zh-CN",
            expertise_areas=["testing", "pytest", "automation", "quality_assurance"],
            response_style="detailed", creativity=0.3,
        ),
        permissions=[
            AgentPermission(resource="tests", access_level=AccessLevel.WRITE, channels=["coding_bus"]),
            AgentPermission(resource="code", access_level=AccessLevel.READ),
        ],
        channels=[
            AgentChannelConfig(channel_name="coding_bus", subscribe=True, publish=True, priority=6),
            AgentChannelConfig(channel_name="test_results", subscribe=False, publish=True),
        ],
        skills=["test_design", "test_execution", "coverage_analysis", "regression_testing", "debugging"],
        metadata={
            "traits": ["skeptical", "thorough", "patient"],
            "behavior_boundaries": ["no_prod_changes", "report_all_failures"],
        },
    )


def create_ai_coding_team() -> AgentTeam:
    """创建 AI 编程团队."""
    team = AgentTeam(
        team_id="ai_coding",
        name="AI 编程团队",
        description="专注软件开发的智能体团队，包含项目经理、技术研究员、全栈开发和测试工程师",
        visibility=Visibility.INTERNAL,
        metadata={"team_type": "coding"},
    )
    team.add_model(_model_deepseek())
    for a in [_agent_pm(), _agent_researcher(), _agent_developer(), _agent_tester()]:
        team.add_agent(a)
    return team
