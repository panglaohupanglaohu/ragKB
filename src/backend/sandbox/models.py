# -*- coding: utf-8 -*-
"""SECS Core Data Models — 自进化协同沙箱核心数据模型.

定义沙箱系统的全部数据结构，涵盖四维一体架构的所有层次。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Enums
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class SandboxStatus(str, Enum):
    """沙箱会话生命周期状态."""
    CREATED = "created"
    SNAPSHOTTING = "snapshotting"
    RUNNING = "running"
    PAUSED = "paused"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    INJECTING = "injecting"
    FAILED = "failed"


class SimulationMode(str, Enum):
    """仿真模式."""
    WHAT_IF = "what_if"           # What-if 单场景推演
    PARALLEL = "parallel"         # 并行多策略对比
    EVOLUTIONARY = "evolutionary"  # 演化搜索最优


class DriftType(str, Enum):
    """环境偏移类型."""
    TASK_MUTATION = "task_mutation"        # 任务目标突变
    RESOURCE_CONFLICT = "resource_conflict"  # 资源冲突
    AGENT_FAILURE = "agent_failure"        # 智能体故障
    CONSTRAINT_CHANGE = "constraint_change"  # 约束变更
    PERFORMANCE_DECAY = "performance_decay"  # 性能衰退


class MemoryType(str, Enum):
    """记忆类型."""
    SHORT_TERM = "short_term"  # 短期记忆（当前会话）
    LONG_TERM = "long_term"    # 长期记忆（跨会话持久）


class ExperienceOutcome(str, Enum):
    """经验结果."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class StrategyStatus(str, Enum):
    """策略状态."""
    CANDIDATE = "candidate"    # 候选策略
    VALIDATED = "validated"    # 沙箱验证通过
    INJECTED = "injected"      # 已注入真实环境
    REJECTED = "rejected"      # 被评论家否决


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 1: 环境语义映射 (MADTwin)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class ResourceState:
    """资源状态."""
    resource_id: str
    resource_type: str  # "llm", "tool", "channel", "memory"
    capacity: float = 1.0
    utilization: float = 0.0
    available: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEdge:
    """工作流语义边."""
    source_agent_id: str
    target_agent_id: str
    channel: str
    message_type: str  # "request", "response", "broadcast", "delegate"
    weight: float = 1.0  # 通信频率权重


@dataclass
class EnvironmentConstraint:
    """环境约束."""
    constraint_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    constraint_type: str = "permission"  # "permission", "rate_limit", "dependency", "ordering"
    target_agents: List[str] = field(default_factory=list)
    rule: str = ""  # 约束规则描述
    active: bool = True


@dataclass
class WorldStateSnapshot:
    """环境二次映射快照 — MADTwin 全要素建模.

    捕获数字世界在某一时刻的完整语义状态。
    """
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 智能体状态
    agent_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # 资源状态
    resources: List[ResourceState] = field(default_factory=list)
    # 工作流拓扑
    workflow_edges: List[WorkflowEdge] = field(default_factory=list)
    # 环境约束
    constraints: List[EnvironmentConstraint] = field(default_factory=list)
    # 待处理任务队列
    pending_tasks: List[Dict[str, Any]] = field(default_factory=list)
    # 全局指标
    global_metrics: Dict[str, float] = field(default_factory=dict)

    # 增量标记
    parent_snapshot_id: Optional[str] = None
    delta_only: bool = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 2: 认知进化循环 (AAS Zero-Exp)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class ExperienceEntry:
    """经验库条目 — 记录一次试错的完整上下文."""
    experience_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str = ""
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 上下文
    situation: str = ""  # 触发情境描述
    action_taken: str = ""  # 执行的动作
    outcome: ExperienceOutcome = ExperienceOutcome.FAILURE
    reward: float = 0.0

    # 反思
    reflection: str = ""  # 反思总结
    lessons_learned: List[str] = field(default_factory=list)
    # 适用条件
    applicable_conditions: List[str] = field(default_factory=list)

    # 记忆分类
    memory_type: MemoryType = MemoryType.SHORT_TERM
    access_count: int = 0
    last_accessed: Optional[str] = None


@dataclass
class ReflectionEntry:
    """反思记录 — 从经验中提炼的元认知."""
    reflection_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 反思内容
    trigger: str = ""  # 触发反思的事件
    analysis: str = ""  # 分析过程
    conclusion: str = ""  # 结论
    new_heuristic: str = ""  # 提炼的新启发式规则

    # 来源经验
    source_experiences: List[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class CollaborationSOP:
    """协作标准操作程序 — 从仿真中提取的最优协作模式."""
    sop_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    description: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 参与者
    agent_roles: List[str] = field(default_factory=list)
    # 步骤序列
    steps: List[Dict[str, Any]] = field(default_factory=list)
    # 通信协议
    communication_protocol: Dict[str, Any] = field(default_factory=dict)

    # 评估
    success_rate: float = 0.0
    avg_reward: float = 0.0
    validated_count: int = 0
    status: StrategyStatus = StrategyStatus.CANDIDATE


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 3: 策略试错实验 (TwinLoop)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class AgentTwin:
    """智能体孪生副本 — 沙箱中的虚拟代理."""
    twin_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    source_agent_id: str = ""
    role: str = ""
    skills: List[str] = field(default_factory=list)
    # 当前状态
    state: str = "idle"  # idle, thinking, acting, waiting
    current_task: Optional[str] = None
    # 决策策略参数
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    # 仿真统计
    actions_taken: int = 0
    rewards_collected: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0


@dataclass
class SimulationStep:
    """仿真步骤记录."""
    step_id: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # 触发
    trigger: str = ""  # 触发该步骤的事件
    # 各智能体动作
    agent_actions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # 环境变化
    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    # 通信记录
    messages: List[Dict[str, Any]] = field(default_factory=list)
    # 步骤奖励
    step_rewards: Dict[str, float] = field(default_factory=dict)
    global_reward: float = 0.0


@dataclass
class DriftEvent:
    """环境偏移事件."""
    drift_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    drift_type: DriftType = DriftType.TASK_MUTATION
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    severity: float = 0.5  # 0~1
    description: str = ""
    affected_agents: List[str] = field(default_factory=list)
    # 触发仿真的阈值
    trigger_sandbox: bool = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 4: 集体智慧对齐 (DT-MADDPG)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class CriticEvaluation:
    """全局评论家评估结果."""
    eval_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 评估维度 (0~1)
    task_completion: float = 0.0      # 任务完成率
    communication_efficiency: float = 0.0  # 通信效率
    resource_utilization: float = 0.0  # 资源利用率
    conflict_avoidance: float = 0.0   # 冲突避免度
    convergence_speed: float = 0.0    # 策略收敛速度
    # 综合得分
    global_score: float = 0.0

    # 各智能体得分
    agent_scores: Dict[str, float] = field(default_factory=dict)
    # 改进建议
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AlignmentProtocol:
    """对齐协议 — 多智能体通信与分工约定."""
    protocol_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    # 角色分配
    role_assignments: Dict[str, str] = field(default_factory=dict)
    # 通信规则
    communication_rules: List[Dict[str, Any]] = field(default_factory=list)
    # 冲突解决策略
    conflict_resolution: str = "priority"  # "priority", "voting", "delegation"
    # 适用场景
    applicable_scenarios: List[str] = field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 顶层会话模型
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class SandboxSession:
    """沙箱会话 — SECS 系统的顶层运行实体."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 状态
    status: SandboxStatus = SandboxStatus.CREATED
    mode: SimulationMode = SimulationMode.WHAT_IF

    # 配置
    team_id: str = ""
    max_steps: int = 100
    speed_factor: float = 10.0  # 仿真加速倍率
    parallel_branches: int = 3  # 并行策略分支数

    # 触发信息
    trigger_drift: Optional[DriftEvent] = None
    trigger_description: str = ""

    # 快照链
    initial_snapshot: Optional[WorldStateSnapshot] = None
    snapshots: List[str] = field(default_factory=list)  # snapshot_id list

    # 仿真结果
    twins: List[AgentTwin] = field(default_factory=list)
    steps: List[SimulationStep] = field(default_factory=list)
    total_steps_executed: int = 0

    # 评估结果
    evaluation: Optional[CriticEvaluation] = None
    best_sop: Optional[CollaborationSOP] = None

    # 注入状态
    injected: bool = False
    injection_time: Optional[str] = None
