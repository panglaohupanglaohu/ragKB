# -*- coding: utf-8 -*-
"""AWS 运维降本增效团队 — Phase 11 G1 静态模板.

一条可复现的「角色对齐 → 迭代萃取特有技能 → 孪生协作 → 真实降本锁棘轮」链路
所需的 6 角色 AWS 运维团队。AWS 只是业务域，度量标准仍是 Token（G4 用 tokens_per_goal 降 20%）。

与既有团队防冲突：
  - team_id = "aws-ops"（≠ cloud-ops-team / d083a568(xops) / build_system / ai_coding / energy_first_principle）
  - 覆盖 ES(Elasticsearch) 缩放这一 cloud-ops/xops 未专门承载的领域场景。

每个角色绑定的工具必须是 tool_registry 已注册的真实 name（已核实存在，杜绝绑不存在的工具）；
技能为本 Phase 新建的领域 skill（与模板自洽，萃取入口可产 trait 技能）。
设计依据：docs/superpowers/specs/2026-06-22-phase11-aws-costdown-best-practice-design.md §7.2（已对照代码修正工具绑定）。
"""

from ..models import (
    AccessLevel,
    AgentChannelConfig,
    AgentPermission,
    AgentPersonality,
    AgentProfile,
    AgentTeam,
    AgentTemplateType,
    ModelConfig,
    Visibility,
)

# team_id 与既有团队显式隔离（防幻影 / 防冲突，见 bug-049）
TEAM_ID = "aws-ops"

# ── 角色模板表：(role_name, agent_id, tools[已注册], skills[新建领域]) ──
# 工具全部来自 tool_registry 已注册 name（§7.2 核实清单）。
# skills 为本 Phase 新建的领域技能名，与工具区分开（compliance_region_guard 仅作技能）。
AWS_OPS_ROLES = [
    ("运维Leader", "aws_lead",
     ["run_shell", "delegate_task"],
     ["aws_es_scaling_orchestration"]),
    ("上云架构师", "aws_arch",
     ["run_shell", "read_file"],
     ["aws_es_capacity_planning"]),
    ("运维操作员", "aws_oper",
     ["run_shell", "run_python"],
     ["aws_cli_script_authoring"]),
    ("巡检监控员", "aws_mon",
     ["run_shell", "set_alarm", "watch_file"],
     ["monitor_alarms_setup"]),
    ("成本优化成员", "aws_cost",
     ["run_shell", "run_python"],
     ["cost_ri_advisor"]),
    ("北美AI项目运维员", "aws_region",
     ["run_shell", "search_files"],
     ["compliance_region_guard"]),
]


def _model_deepseek() -> ModelConfig:
    return ModelConfig(
        model_id="deepseek",
        provider="deepseek",
        name="deepseek-v4-pro",
        max_tokens=8192,
        temperature=0.2,
        is_default=True,
        api_base_url="https://api.deepseek.com",
    )


def _build_agent(agent_id: str, role: str, tools: list, skills: list) -> AgentProfile:
    """按 role 名构造 AgentProfile，统一绑定 aws_ops_bus 频道 + 工具 + 领域技能."""
    return AgentProfile(
        agent_id=agent_id,
        name=role,
        role=role,
        description=f"AWS 运维团队 · {role}",
        template_type=AgentTemplateType.CUSTOM,
        model_id="deepseek",
        system_prompt=(
            f"你是 AWS 运维团队的{role}。\n"
            "团队目标：用最少 Token 完成 AWS 运维降本增效任务（如 Elasticsearch 实例缩放）。\n"
            "请用中文回答，注重可执行的 shell + aws-cli 脚本与成本可控。\n"
        ),
        personality=AgentPersonality(
            tone="professional", language="zh-CN",
            expertise_areas=["aws", "cost_optimization", "operations"],
            response_style="technical", creativity=0.3,
        ),
        permissions=[
            AgentPermission(resource="aws", access_level=AccessLevel.WRITE, channels=["aws_ops_bus"]),
        ],
        channels=[
            AgentChannelConfig(channel_name="aws_ops_bus", subscribe=True, publish=True),
        ],
        tools=list(tools),
        skills=list(skills),
        metadata={"team_type": "aws_ops", "role": role},
    )


def create_aws_ops_team() -> AgentTeam:
    """创建 AWS 运维降本增效团队（6 角色 × 真实工具 + 领域技能）."""
    team = AgentTeam(
        team_id=TEAM_ID,
        name="AWS 运维团队",
        description=(
            "AWS 运维降本增效团队，6 角色覆盖 ES 缩放编排/容量规划/脚本编写/"
            "巡检监控/成本优化/区域合规。Phase 11 降本增效最佳实践 Case 的载体。"
        ),
        visibility=Visibility.INTERNAL,
        metadata={"team_type": "aws_ops"},
    )
    team.add_model(_model_deepseek())
    for role, aid, tools, skills in AWS_OPS_ROLES:
        team.add_agent(_build_agent(aid, role, tools, skills))
    return team
