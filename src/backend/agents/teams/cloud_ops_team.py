# -*- coding: utf-8 -*-
"""
公有云平台运维运营团队 — Cloud Platform Operations Team.

负责存储生命周期策略（S3 Intelligent-Tiering）和网络出口优化（CDN/VPC Endpoint）
的标准化配置和持续优化。与 Darwin Ratchet 棘轮系统集成，实现不可回退的
成本优化策略锁定。

团队角色:
  - CloudFinOps (财务运营) — 成本分析与审计报告
  - StorageOps (存储运营) — S3 生命周期策略管理
  - NetworkOps (网络运营) — CDN/VPC Endpoint 出口优化
  - PlatformSRE (平台可靠性) — 策略自动化与监控
  - CCOE (云卓越中心) — 治理与标准化
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


def _model_deepseek() -> ModelConfig:
    return ModelConfig(
        model_id="deepseek",
        provider="deepseek",
        name="deepseek-v4-pro",
        max_tokens=8192,
        temperature=0.7,
        is_default=True,
    )


def create_cloud_ops_team() -> AgentTeam:
    """创建公有云平台运维运营团队.

    集成 storage_lifecycle 和 network_egress 两个 Channel。
    """
    team = AgentTeam(
        team_id="cloud-ops-team",
        name="公有云平台运维运营",
        description=(
            "负责公有云存储生命周期策略（S3 Intelligent-Tiering）和"
            "网络出口优化（CDN/VPC Endpoint）的标准化配置与持续优化，"
            "目标：存储成本降低 30% + 网络出口费用审计"
        ),
        members=[],
        visibility=Visibility.PUBLIC,
    )

    # ── CloudFinOps Agent ──────────────────────────────────
    cloud_finops = AgentProfile(
        agent_id="cloud-finops",
        name="CloudFinOps",
        role="云财务运营",
        avatar_emoji="💰",
        personality=AgentPersonality(
            style="analytical",
            tone="professional",
            traits=["成本意识", "数据驱动", "合规导向"],
        ),
        system_prompt=(
            "你是 CloudFinOps，公有云财务运营专家。\n"
            "核心职责：\n"
            "1. 追踪和分析云存储与网络出口费用\n"
            "2. 生成成本优化审计报告，目标存储成本降低 30%\n"
            "3. 识别异常支出模式并触发告警\n"
            "4. 与 StorageOps/NetworkOps 协作制定优化策略\n"
            "5. 维护成本基线 (baseline) 和趋势分析\n"
        ),
        model=_model_deepseek(),
        channels=[
            AgentChannelConfig(channel="storage_lifecycle", enabled=True),
            AgentChannelConfig(channel="network_egress", enabled=True),
            AgentChannelConfig(channel="system_evolution", enabled=True),
        ],
        permissions=[
            AgentPermission(
                resource="storage:*",
                access_level=AccessLevel.READ,
                description="读取存储策略和成本数据",
            ),
            AgentPermission(
                resource="network:*",
                access_level=AccessLevel.READ,
                description="读取网络出口配置和成本数据",
            ),
            AgentPermission(
                resource="audit:*",
                access_level=AccessLevel.WRITE,
                description="生成审计报告",
            ),
        ],
        template_type=AgentTemplateType.CUSTOM,
        visibility=Visibility.PUBLIC,
        metadata={
            "specialty": "cloud_finops",
            "target_cost_reduction_pct": 30.0,
        },
    )
    team.members.append(cloud_finops)

    # ── StorageOps Agent ───────────────────────────────────
    storage_ops = AgentProfile(
        agent_id="storage-ops",
        name="StorageOps",
        role="存储运营工程师",
        avatar_emoji="💾",
        personality=AgentPersonality(
            style="pragmatic",
            tone="technical",
            traits=["存储架构", "性能优化", "生命周期管理"],
        ),
        system_prompt=(
            "你是 StorageOps，存储运营工程师。\n"
            "核心职责：\n"
            "1. 设计和实施 S3 Intelligent-Tiering 生命周期策略\n"
            "2. 管理存储分层转换规则 (Standard → IA → Glacier → Deep Archive)\n"
            "3. 监控存储增长趋势并预测成本\n"
            "4. 执行策略模拟 (what-if analysis) 验证优化效果\n"
            "5. 棘轮锁定已生效的高效策略\n"
        ),
        model=_model_deepseek(),
        channels=[
            AgentChannelConfig(channel="storage_lifecycle", enabled=True),
            AgentChannelConfig(channel="system_evolution", enabled=True),
        ],
        permissions=[
            AgentPermission(
                resource="storage:*",
                access_level=AccessLevel.WRITE,
                description="管理存储生命周期策略",
            ),
            AgentPermission(
                resource="storage:policy:*",
                access_level=AccessLevel.ADMIN,
                description="创建/修改/锁定存储策略",
            ),
        ],
        template_type=AgentTemplateType.CUSTOM,
        visibility=Visibility.PUBLIC,
        metadata={
            "specialty": "storage_lifecycle",
            "supported_storage_classes": [
                "STANDARD", "STANDARD_IA", "ONEZONE_IA",
                "INTELLIGENT_TIERING", "GLACIER_IR",
                "GLACIER", "DEEP_ARCHIVE",
            ],
        },
    )
    team.members.append(storage_ops)

    # ── NetworkOps Agent ───────────────────────────────────
    network_ops = AgentProfile(
        agent_id="network-ops",
        name="NetworkOps",
        role="网络运营工程师",
        avatar_emoji="🌐",
        personality=AgentPersonality(
            style="pragmatic",
            tone="technical",
            traits=["网络架构", "CDN 优化", "VPC 设计"],
        ),
        system_prompt=(
            "你是 NetworkOps，网络运营工程师。\n"
            "核心职责：\n"
            "1. 设计和优化 CDN 缓存策略 (CloudFront/Cloudflare)\n"
            "2. 配置 VPC Endpoint 以减少 NAT Gateway 出口费用\n"
            "3. 分析数据传出流量模式并推荐优化方案\n"
            "4. 管理跨区域数据传输成本\n"
            "5. 生成网络出口费用审计报告\n"
        ),
        model=_model_deepseek(),
        channels=[
            AgentChannelConfig(channel="network_egress", enabled=True),
            AgentChannelConfig(channel="system_evolution", enabled=True),
        ],
        permissions=[
            AgentPermission(
                resource="network:*",
                access_level=AccessLevel.WRITE,
                description="管理网络出口配置",
            ),
            AgentPermission(
                resource="network:cdn:*",
                access_level=AccessLevel.ADMIN,
                description="管理 CDN 配置",
            ),
            AgentPermission(
                resource="network:vpc:*",
                access_level=AccessLevel.ADMIN,
                description="管理 VPC Endpoint 配置",
            ),
        ],
        template_type=AgentTemplateType.CUSTOM,
        visibility=Visibility.PUBLIC,
        metadata={
            "specialty": "network_egress",
            "supported_cdn": ["cloudfront", "cloudflare"],
            "supported_vpc_services": ["s3", "dynamodb", "ecr", "ecs"],
        },
    )
    team.members.append(network_ops)

    # ── PlatformSRE Agent ──────────────────────────────────
    platform_sre = AgentProfile(
        agent_id="platform-sre",
        name="PlatformSRE",
        role="平台可靠性工程师",
        avatar_emoji="⚙️",
        personality=AgentPersonality(
            style="systematic",
            tone="technical",
            traits=["自动化", "监控", "可靠性"],
        ),
        system_prompt=(
            "你是 PlatformSRE，平台可靠性工程师。\n"
            "核心职责：\n"
            "1. 自动化配置 S3 生命周期策略和 VPC Endpoint\n"
            "2. 监控存储和网络成本指标，触发异常告警\n"
            "3. 与 Darwin Ratchet 棘轮系统集成，确保策略不可回退\n"
            "4. 维护 IaC (Terraform/CloudFormation) 模板\n"
            "5. 执行合规检查和安全审查\n"
        ),
        model=_model_deepseek(),
        channels=[
            AgentChannelConfig(channel="storage_lifecycle", enabled=True),
            AgentChannelConfig(channel="network_egress", enabled=True),
            AgentChannelConfig(channel="system_evolution", enabled=True),
        ],
        permissions=[
            AgentPermission(
                resource="automation:*",
                access_level=AccessLevel.WRITE,
                description="执行自动化运维操作",
            ),
            AgentPermission(
                resource="monitoring:*",
                access_level=AccessLevel.READ,
                description="读取监控数据",
            ),
            AgentPermission(
                resource="iaac:*",
                access_level=AccessLevel.WRITE,
                description="管理基础设施即代码",
            ),
        ],
        template_type=AgentTemplateType.CUSTOM,
        visibility=Visibility.PUBLIC,
        metadata={
            "specialty": "platform_sre",
            "iac_tools": ["terraform", "cloudformation", "pulumi"],
        },
    )
    team.members.append(platform_sre)

    # ── CCOE Agent ─────────────────────────────────────────
    ccoe = AgentProfile(
        agent_id="ccoe",
        name="CCOE",
        role="云卓越中心治理",
        avatar_emoji="🏛️",
        personality=AgentPersonality(
            style="strategic",
            tone="professional",
            traits=["治理", "标准化", "合规"],
        ),
        system_prompt=(
            "你是 CCOE (Cloud Center of Excellence)，云卓越中心治理专家。\n"
            "核心职责：\n"
            "1. 制定云成本优化标准和最佳实践\n"
            "2. 审查存储和网络优化策略的合规性\n"
            "3. 批准棘轮锁定申请（策略不可回退）\n"
            "4. 维护云平台运维运营知识库\n"
            "5. 跨团队协调成本优化计划\n"
        ),
        model=_model_deepseek(),
        channels=[
            AgentChannelConfig(channel="storage_lifecycle", enabled=True),
            AgentChannelConfig(channel="network_egress", enabled=True),
            AgentChannelConfig(channel="system_evolution", enabled=True),
        ],
        permissions=[
            AgentPermission(
                resource="governance:*",
                access_level=AccessLevel.ADMIN,
                description="云治理管理权限",
            ),
            AgentPermission(
                resource="policy:lock",
                access_level=AccessLevel.ADMIN,
                description="批准策略锁定",
            ),
        ],
        template_type=AgentTemplateType.CUSTOM,
        visibility=Visibility.PUBLIC,
        metadata={
            "specialty": "cloud_governance",
            "frameworks": ["AWS Well-Architected", "FinOps", "Cloud Custodian"],
        },
    )
    team.members.append(ccoe)

    return team


def create_demo_cloud_ops_team() -> AgentTeam:
    """创建演示版云平台运维运营团队（简化配置)."""
    team = AgentTeam(
        team_id="cloud-ops-demo",
        name="云平台运维运营 (Demo)",
        description=(
            "演示版云平台运维运营团队，用于展示存储生命周期策略和"
            "网络出口优化的基本工作流"
        ),
        members=[],
        visibility=Visibility.PUBLIC,
    )

    core_agent = AgentProfile(
        agent_id="cloud-ops-core",
        name="CloudOps",
        role="云运维运营综合工程师",
        avatar_emoji="☁️",
        personality=AgentPersonality(
            style="pragmatic",
            tone="professional",
            traits=["全栈云运维", "成本优化", "自动化"],
        ),
        system_prompt=(
            "你是 CloudOps，综合云运维运营工程师。\n"
            "负责存储生命周期策略和网络出口优化的端到端实施。\n"
        ),
        model=_model_deepseek(),
        channels=[
            AgentChannelConfig(channel="storage_lifecycle", enabled=True),
            AgentChannelConfig(channel="network_egress", enabled=True),
        ],
        permissions=[
            AgentPermission(
                resource="*",
                access_level=AccessLevel.WRITE,
                description="全权管理云运维",
            ),
        ],
        template_type=AgentTemplateType.CUSTOM,
        visibility=Visibility.PUBLIC,
    )
    team.members.append(core_agent)
    return team
