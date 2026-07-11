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
    tools: List[str] = field(default_factory=list)
    # 当前状态
    state: str = "idle"  # idle, thinking, acting, waiting
    current_task: Optional[str] = None
    # 决策策略参数
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    # 演化代数
    generation: int = 0
    # 仿真统计
    actions_taken: int = 0
    rewards_collected: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    # v4 A-2.3: 技能熟练度先验 (skill_name -> 成功率, 默认 0.5)
    skill_proficiency: Dict[str, float] = field(default_factory=dict)
    # 混沌注入的增援 Agent 标记 — 非真实团队成员，仿真结束后清理
    is_reinforcement: bool = False


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
    # 混沌注入：当前步被禁用的 Agent
    disabled_agents: List[str] = field(default_factory=list)
    # v4 A-2.4: 本步产生的技能使用记录 ID 引用
    skill_usages: List[str] = field(default_factory=list)
    # 场景 taskflow 节点状态（供前端编排管线精确高亮）
    active_task_id: str = ""
    active_task_ids: List[str] = field(default_factory=list)
    done_task_ids: List[str] = field(default_factory=list)


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
    # 并行模式的所有分支结果（前端多线图）
    branches_results: List[List[SimulationStep]] = field(default_factory=list)
    # 演化模式的多代记录
    evolution_generations: List[Dict[str, Any]] = field(default_factory=list)
    max_generations: int = 3

    # 注入状态
    injected: bool = False
    injection_time: Optional[str] = None
    # 失败归因
    failed_agents: List[Dict[str, Any]] = field(default_factory=list)
    chaos_events: List[Dict[str, Any]] = field(default_factory=list)

    # ── Trial/Branch 关联字段 (M-04: 向后兼容) ──
    branch_id: Optional[str] = None       # 所属 Branch ID
    trial_id: Optional[str] = None        # 所属 Trial ID

    # ── 全局 G3-1: 技能路由策略 ──
    # "" | proficiency_first | affinity_first | round_robin | cost_aware
    routing_strategy: str = ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Trial / Branch / Event — 数字孪生试炼三层模型 (阶段二)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TrialStatus(str, Enum):
    """试炼生命周期状态."""
    IDLE = "idle"
    CREATING = "creating"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class BranchStatus(str, Enum):
    """分支状态."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TrialEventType(str, Enum):
    """统一事件类型."""
    STEP = "step"                    # 仿真步进
    BRANCH_CREATED = "branch_created"   # 分支创建
    BRANCH_FORKED = "branch_forked"     # 分支分裂
    CHAOS_INJECTED = "chaos_injected"   # 混沌注入
    REWARD_UPDATE = "reward_update"     # 奖励更新
    SESSION_COMPLETE = "session_complete"  # 会话完成
    TRIAL_COMPLETE = "trial_complete"    # 试练完成
    EVALUATION_DONE = "evaluation_done"  # 评估完成
    SOP_EXTRACTED = "sop_extracted"      # SOP萃取
    FEEDBACK_APPLIED = "feedback_applied"# 反哺完成
    AGENT_MOVE = "agent_move"            # Agent移动
    FAULT_RECOVERED = "fault_recovered"  # 故障恢复
    # v4 A-3.2: 进化与技能事件
    SKILL_USAGE = "skill_usage"              # 技能使用记录
    EVOLUTION_STARTED = "evolution_started"  # 进化运行开始
    EVOLUTION_PHASE = "evolution_phase"      # 进化阶段推进
    EVOLUTION_APPLIED = "evolution_applied"  # 进化结果已写回
    EVOLUTION_REJECTED = "evolution_rejected"# 进化结果被拒绝
    EVOLUTION_SUGGESTED = "evolution_suggested"  # 建议进化（评分低于 rubric）
    # XB-2.1: eco 生境事件
    ECO_STEP = "eco_step"                # 生境单步（health/survival/intention）
    ECO_EPOCH = "eco_epoch"              # 世代结算（births/deaths/ratchet）
    ECO_PREDATOR = "eco_predator"        # 捕食压力


class TrialMode(str, Enum):
    """五种试炼模式."""
    WHAT_IF = "what_if"               # What-if 推演
    MULTI_BRANCH = "multi_branch"      # 多分支对比
    CHAOS_DRILL = "chaos_drill"        # 混沌演练
    EVOLUTIONARY = "evolutionary"      # 演化试炼
    REPLAY = "replay"                  # 回放复盘


@dataclass
class Trial:
    """试炼 — 数字孪生的顶级实验单元 (M-01)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    status: TrialStatus = TrialStatus.IDLE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 配置
    team_id: str = ""
    team_snapshot: Dict[str, Any] = field(default_factory=dict)
    task_goal: Dict[str, Any] = field(default_factory=dict)
    scenario: str = ""          # 场景名 (legacy 字符串字段，保留兼容)
    # v4 A-2.6: 场景化 + 代际
    scenario_id: str = ""       # 关联 ScenarioSpec
    generation: int = 0         # 代际编号
    parent_trial_id: str = ""   # 上一代试炼
    mode: TrialMode = TrialMode.WHAT_IF
    max_steps: int = 100
    acceleration: int = 1       # 加速倍率
    parallel_branches: int = 1

    # 分支列表
    branches: List[str] = field(default_factory=list)  # branch_id 列表

    # 评估结果
    evaluation: Optional[Dict[str, Any]] = None
    extracted_sops: List[Dict[str, Any]] = field(default_factory=list)
    feedback_actions: List[Dict[str, Any]] = field(default_factory=list)

    # 统计
    total_sessions: int = 0
    total_steps: int = 0
    best_score: Optional[float] = None
    # ── 物竞天择 ND-1.2: 演练引擎路由 ("secs"=现有SECS / "natural_selection"=自然选择生境) ──
    drill_kind: str = "secs"


@dataclass
class Branch:
    """分支 — 试炼内的独立运行线 (M-02)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trial_id: str = ""
    name: str = ""
    label: str = ""              # 显示标签，如 "baseline", "chaos-v1", "optimized"
    color: str = "#4A90E2"       # UI 颜色

    parent_branch_id: Optional[str] = None
    fork_at_step: Optional[int] = None
    initial_conditions: Dict[str, Any] = field(default_factory=dict)
    injected_events: List[Dict[str, Any]] = field(default_factory=list)

    sessions: List[str] = field(default_factory=list)  # session_id 列表
    current_session_id: Optional[str] = None
    status: BranchStatus = BranchStatus.PENDING
    current_step: int = 0
    final_score: Optional[float] = None
    reward_curve: List[Dict[str, Any]] = field(default_factory=list)  # [{step, reward}]
    agent_contributions: List[Dict[str, Any]] = field(default_factory=list)

    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


@dataclass
class TrialEvent:
    """统一事件模型 (M-03)."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    event_type: TrialEventType = TrialEventType.STEP
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 关联
    trial_id: str = ""
    branch_id: Optional[str] = None
    session_id: Optional[str] = None

    # 数据负载
    data: Dict[str, Any] = field(default_factory=dict)

    # 元信息
    source: str = "system"       # system | user | agent
    processed: bool = False


@dataclass
class TrialEvaluation:
    """五维评分结果."""
    eval_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    trial_id: str = ""
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 五维评分 (0~1)
    task_completion: float = 0.0           # 目标完成度 (权重30%)
    collaboration_efficiency: float = 0.0  # 协作效率 (权重25%)
    resilience: float = 0.0                # 韧性评分 (权重20%)
    cost_efficiency: float = 0.0           # 成本控制 (权重15%)
    extractability: float = 0.0            # 可萃取性 (权重10%)

    # 加权总分
    total_score: float = 0.0

    # 各分支评分
    branch_scores: Dict[str, float] = field(default_factory=dict)

    # 分析
    best_branch_id: Optional[str] = None
    worst_branch_id: Optional[str] = None
    key_insights: List[str] = field(default_factory=list)
    turning_points: List[Dict[str, Any]] = field(default_factory=list)
    # v4 A-2.5: per-skill 归因 (结构对齐 evolution/fitness.SkillFitnessReport.to_dict())
    skill_breakdown: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SOPCandidate:
    """SOP 萃取候选."""
    sop_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    confidence: float = 0.0
    source_branch_id: str = ""
    applicable_scenarios: List[str] = field(default_factory=list)
    steps_count: int = 0
    steps: List[Dict[str, Any]] = field(default_factory=list)  # [{order, agent_role, action, precondition, expected_output, fallback}]

    status: str = "candidate"  # candidate | approved | rejected | applied
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# v4: 技能使用归因 + 熟练度 + 进化运行 (场景化演练 × 技能进化)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class SkillUsageRecord:
    """技能使用记录 — 演练中每次 skill 使用的归因数据 (v4 A-2.1)."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    session_id: str = ""
    branch_id: str = ""
    trial_id: str = ""
    step_index: int = 0
    agent_id: str = ""
    agent_role: str = ""
    skill_name: str = ""
    skill_id: Optional[str] = None
    skill_version: Optional[int] = None
    task_id: str = ""
    outcome: str = "success"  # success | failure | partial
    duration_steps: int = 1
    reward_delta: float = 0.0
    failure_reason: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id, "session_id": self.session_id,
            "branch_id": self.branch_id, "trial_id": self.trial_id,
            "step_index": self.step_index, "agent_id": self.agent_id,
            "agent_role": self.agent_role, "skill_name": self.skill_name,
            "skill_id": self.skill_id, "skill_version": self.skill_version,
            "task_id": self.task_id, "outcome": self.outcome,
            "duration_steps": self.duration_steps,
            "reward_delta": self.reward_delta,
            "failure_reason": self.failure_reason,
            "context": self.context, "timestamp": self.timestamp,
        }


@dataclass
class SkillProficiency:
    """技能熟练度聚合视图 (v4 A-2.2)."""
    skill_name: str = ""
    agent_id: str = ""
    scenario_category: str = "general"
    total_uses: int = 0
    success_count: int = 0
    success_rate: float = 0.5
    avg_reward_delta: float = 0.0
    trend: List[float] = field(default_factory=list)  # 最近若干 trial 的成功率序列
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name, "agent_id": self.agent_id,
            "scenario_category": self.scenario_category,
            "total_uses": self.total_uses, "success_count": self.success_count,
            "success_rate": round(self.success_rate, 4),
            "avg_reward_delta": round(self.avg_reward_delta, 4),
            "trend": self.trend, "last_updated": self.last_updated,
        }


class EvolutionRunStatus(str, Enum):
    """进化运行状态机 (v4 A-3.1)."""
    IDENTIFYING = "identifying"
    REFLECTING = "reflecting"
    MUTATING = "mutating"
    AB_TESTING = "ab_testing"
    GATING = "gating"
    APPLIED = "applied"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class EvolutionRun:
    """进化运行 — 演练数据驱动的 skill 进化编排单元 (v4 A-3.1)."""
    run_id: str = field(default_factory=lambda: f"evo_{str(uuid.uuid4())[:8]}")
    team_id: str = ""
    scenario_id: str = ""
    target_skills: List[Dict[str, Any]] = field(default_factory=list)
    status: EvolutionRunStatus = EvolutionRunStatus.IDENTIFYING
    reflection: Dict[str, Any] = field(default_factory=dict)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    winner: Optional[Dict[str, Any]] = None
    baseline_trial_id: str = ""
    ab_trial_ids: List[str] = field(default_factory=list)
    triggered_by: str = "manual"  # manual | auto_low_score | nightly
    auto_apply: bool = False
    error: str = ""
    error_detail: Dict[str, Any] = field(default_factory=dict)  # C-2.1: {reason, scanned_trials, usages}
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    cost_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id, "team_id": self.team_id,
            "scenario_id": self.scenario_id, "target_skills": self.target_skills,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "reflection": self.reflection, "candidates": self.candidates,
            "winner": self.winner, "baseline_trial_id": self.baseline_trial_id,
            "ab_trial_ids": self.ab_trial_ids, "triggered_by": self.triggered_by,
            "auto_apply": self.auto_apply, "error": self.error,
            "error_detail": self.error_detail,
            "created_at": self.created_at, "completed_at": self.completed_at,
            "cost_tokens": self.cost_tokens,
        }
