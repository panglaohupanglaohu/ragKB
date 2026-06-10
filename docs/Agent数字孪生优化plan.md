# Agent 数字孪生优化计划
# AgentsGroup2026 Digital Twin — Architecture & Design Plan

> 版本：v1.0 · 日期：2026-06-09  
> 作者：Tabbit 智能体浏览器助手  
> 适用对象：CodeBuddy / 开发团队  
> 文档目的：从产品理念到系统架构，完整描述数字孪生的重构方向，作为所有开发工作的总纲。

---

## 一、核心理念：数字孪生不是监控面板

### 1.1 现有系统的本质问题

当前页面已经具备大量基础能力：智能体团队列表、环境空间六房间、SECS Pipeline、仿真演练按钮、收益曲线、CLI 终端。但如果用一句话描述现有系统的感受，用户会说：

> "它像一个监控面板，加了一个仿真按钮。"

这不是数字孪生。数字孪生的核心价值是：

> **脱离现实的代价，获得进化的智慧。**  
> 让 Agent 在虚拟世界中试错、失败、演化、萃取 SOP，再把经验反哺给现实团队。

数字孪生不是"看到现实在发生什么"，而是"在虚拟世界中制造并比较多个未来，从中选出最优路径并写回现实"。

### 1.2 数字孪生的三层能力

| 层级 | 能力 | 当前状态 |
|---|---|---|
| L1 镜像 | 把现实团队/技能/空间/任务复制到沙箱 | 部分具备，状态不同步 |
| L2 试验 | 在沙箱中运行、注入扰动、多分支对比 | 部分具备，演练/仿真割裂 |
| L3 进化 | 萃取最优路径为 SOP，反哺现实 Agent | 基本缺失，SOP 为 0 |

**重构目标：打通三层，让 L1→L2→L3→L1 形成闭环。**

### 1.3 产品核心原则（不可违背）

1. **能力不靠声明，靠演练数据证明。** Agent 的技能价值由试炼 reward 决定，不由介绍文字决定。
2. **环境空间是状态机，不是装饰。** Agent 在哪个房间 = 任务处于哪个阶段。
3. **试炼产生可追溯历史。** 每次试炼都必须留下记录：步数、评分、分支、SOP 候选。
4. **失败也是数据。** 失败路径必须被记录、可复盘、可分析，不能被丢弃。
5. **仿真和演练是同一件事的两个维度。** 仿真负责推进路径，演练负责施加压力，两者统一在"孪生试炼"中。

---

## 二、统一概念：孪生试炼系统（Twin Trial System）

### 2.1 为什么要引入 Trial 概念

当前系统围绕 `Session` 建模。Session 是技术概念，代表"一次运行"，但用户真正关心的是"一次完整试炼"——它可能包含多个运行分支、多次重启、注入多个故障、最后萃取出 SOP。

建议引入三层对象模型：

```
Trial（孪生试炼）
  └── Branch（试验分支）
        └── Run / Session（具体运行）
```

- **Trial**：一次完整的孪生试炼实验。有明确的任务目标、团队快照、模式选择，产出评分和 SOP。
- **Branch**：Trial 下的一条实验路径。可以是基线、故障注入版本、策略变体，拥有独立 reward 曲线。
- **Run/Session**：Branch 中的一次具体执行流水，记录 step、agent action、event、state snapshot。

### 2.2 孪生试炼完整闭环

```
镜像现实 → 生成分支 → 沙箱试炼 → 评分评审 → 萃取反哺 → 镜像现实（下一代）
```

详细展开：

| 阶段 | 输入 | 输出 | 涉及系统 |
|---|---|---|---|
| 镜像现实 | 当前团队、技能、任务、空间布局 | 团队快照（Team Snapshot） | MADTwin (L1) |
| 生成分支 | 团队快照 + 试炼模式 + 条件变体 | 多个 Branch | MADCG (L4) |
| 沙箱试炼 | Branch 初始状态 | Step/Reward/Event 序列 | TwinLoop (L3) + AAS (L2) |
| 评分评审 | 所有 Branch 的运行结果 | 五维评分 + 最佳/失败分支标注 | 评分引擎 |
| 萃取反哺 | 最佳 Branch 的关键路径 | SOP 候选 + 技能升级建议 | 萃取室 |
| 镜像现实（下代） | SOP + 升级建议 | 更新后的 Agent 技能、协作图 | 反哺接口 |

---

## 三、五种试炼模式

### 3.1 What-if 推演（单分支基线）

**用途**：快速验证一个方案，生成基线 reward 曲线。  
**特点**：无故障注入，正常运行，产出对照组数据。  
**价值**：所有后续演练的参照基准。

运行示例：
```
Step 0  团队快照进入工作坊
Step 1  PM claim_task
Step 2  7 Agent 各自认领技能
Step 3  task_decomposition / web_research / architecture_design ...
Step 37 reward 峰值 0.696
       → 输出基线 SOP 候选
```

### 3.2 多分支对比（策略比较）

**用途**：比较同一任务下的不同策略。  
**特点**：从某个 step 分裂出多条 Branch，并行推进，最终对比评分。  
**价值**：找到更优协作图或技能配置。

运行示例：
```
Branch A（基线）：默认协作图
Branch B（优化）：Architect 前置，先完成接口边界再给 Developer
Branch C（并行）：Tester 提前介入，在代码实现前生成测试假设

对比结果：
  Branch A  reward 0.696
  Branch B  reward 0.741 ← 推荐
  Branch C  reward 0.712
```

### 3.3 混沌演练（韧性测试）

**用途**：在运行中注入扰动，测试团队恢复能力。  
**特点**：定时或手动触发故障事件，观察团队如何响应。  
**价值**：测量恢复力（Resilience），发现单点失败风险。

故障事件分类（三级）：
```
一级：网络延迟 / 工具超时 / 轻微技能退化
二级：Agent 临时失联 / 任务中途变更 / 知识库不可用
三级：核心 Agent 离队 / 模型幻觉导致错误决策 / 逻辑死锁
```

运行示例：
```
Step 8  注入：网络延迟 → Researcher 输出延迟
Step 9  Architect 改用本地知识库
Step 10 PM 重排任务优先级
Step 11 reward 从 0.52 回升到 0.57
       → 恢复力得分：83/100（8步内恢复，调用了替代策略）
```

### 3.4 演化试炼（多代进化）

**用途**：自动寻找更优 SOP，让系统自我进化。  
**特点**：多代运行，保留高分策略，淘汰低分策略，再微调继续迭代。  
**价值**：无需人工干预地发现最优协作路径。

进化示例：
```
Generation 1  默认协作图          reward 0.46
Generation 2  Architect 前置      reward 0.55
Generation 3  Tester 早期介入      reward 0.63
Generation 4  Deployer 并行检查    reward 0.70
Generation 5  组合优化             reward 0.74 → 萃取 SOP
```

进化策略参数：
- 保留率：top 30% Branch 进入下一代
- 变异率：20% 的 Agent 技能/顺序随机变异
- 交叉率：50% 的高分 Branch 相互融合
- 终止条件：连续 3 代 reward 不增 or 达到最大代数

### 3.5 回放复盘（历史重演）

**用途**：从历史 Trial 的关键 step 回放或重新分裂。  
**特点**：基于已有 Trial 数据，不需要重新运行全程。  
**价值**：定位失败原因，验证改进假设。

---

## 四、页面架构重构

### 4.1 三层布局

```
┌─────────────────────────────────────────────────────────────────┐
│  顶部全局状态栏                                                    │
│  运行时状态 · 当前 Trial · 最优评分 · SOP 数量 · 沙箱会话          │
├──────────────┬──────────────────────────────┬───────────────────┤
│ 左侧         │ 中央：环境空间（主舞台）        │ 右侧              │
│ 团队与       │                               │ 试炼导演台         │
│ Agent 池     │ 议事厅 萃取室 工作坊           │                   │
│              │ 知识库 演练场 休息区           │ 团队选择           │
│ 团队卡片      │                               │ 任务目标           │
│ Agent 列表   │ Agent 在房间之间实时移动        │ 试炼模式           │
│ 技能标签      │ 分支以颜色区分                │ 分支管理           │
│ 部署按钮      │ 故障注入有视觉反馈             │ 故障注入           │
│              │ reward 变化反映在房间颜色      │ 运行控制           │
├──────────────┴──────────────────────────────┴───────────────────┤
│  底部试炼时间轴                                                    │
│  step · reward 曲线 · event 标注 · agent action · 分支比较        │
├─────────────────────────────────────────────────────────────────┤
│  结果层（试炼完成后展开）                                           │
│  五维评分 · 最佳分支 · 失败分支 · SOP 候选 · 反哺建议              │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 模块职责重定义

| 模块 | 当前问题 | 重构后职责 |
|---|---|---|
| 环境空间 | 仅显示房间列表，Agent 人数不同步 | **主舞台**，显示 Agent 实时位置、分支轨迹、故障状态、reward 热力 |
| 智能体团队 | 侧边列表，与空间脱钩 | 团队池，支持快速部署/召回到环境空间 |
| SECS Pipeline | 静态说明文字 | 成为试炼运行时的活动状态指示器，每步高亮当前处于哪一层 |
| 演练配置 | 和"仿真"并列，两套入口 | 合并为"试炼导演台"，统一控制 |
| 收益曲线 | 仅显示当前 session | 支持多 Branch 叠加显示 |
| 执行日志 | 多源混杂，Step 0/Step 2 不一致 | 统一事件流，按类型过滤 |
| CLI | 独立终端 | 可与 Trial 命令集成，如 `trial create`、`branch fork` |
| 系统状态 | 独立面板，指标孤立 | 改为可折叠顶部栏，集成当前 Trial 核心指标 |

### 4.3 环境空间：从房间变成状态机

每个房间对应一个 Agent 活动阶段：

| 房间 | 对应阶段 | Agent 进入条件 |
|---|---|---|
| 议事厅 | 任务拆解、角色分配、冲突协商 | Trial 创建后，任务分配阶段 |
| 工作坊 | 开发、构建、测试、交付 | 技能执行阶段 |
| 知识库 | 检索历史 SOP、调用技能库 | 需要外部知识时 |
| 演练场 | 分支对抗、故障注入、韧性测试 | 混沌演练模式 / 分支分裂时 |
| 萃取室 | SOP 萃取、经验压缩、技能升级 | Trial 完成评估后 |
| 休息区 | 失败恢复、冷却、替补待机 | Agent 失败/退出/暂时离队 |

Agent 房间迁移规则：
```
Trial 开始     → 所有 Agent 进入 议事厅
任务分配完成    → PM 留在议事厅，其他 Agent 进入 工作坊 或 知识库
故障注入触发    → 受影响 Agent 进入 休息区（暂时）或 演练场（参与对抗）
评估开始        → 一个代表 Agent 进入 萃取室
SOP 萃取完成   → 所有 Agent 回到 工作坊 或 休息区（待机）
```

### 4.4 按钮状态机

不能再让按钮状态和内部状态不一致。统一按钮生命周期：

```
状态: idle
  按钮: [创建试炼]

状态: creating_trial
  按钮: [⏳ 创建中...]（仅在创建网络请求期间，≤3秒）

状态: ready
  按钮: [▶ 单步推演] [▶▶ 自动推演] [💥 注入事件] [⑂ 分裂分支]

状态: running
  按钮: [⏸ 暂停] [💥 注入事件] [⑂ 分裂分支]

状态: paused
  按钮: [▶ 继续] [▶ 单步推演] [⏹ 终止] [💥 注入事件] [⑂ 分裂分支]

状态: evaluating
  按钮: [⏳ 评分中...] （不可操作）

状态: completed
  按钮: [📊 查看评分] [📋 萃取 SOP] [🔄 反哺 Agent] [🔁 创建新试炼]

状态: failed
  按钮: [🔄 恢复] [📋 复盘] [🔁 创建新试炼]
```

**绝对不允许**：按钮显示"创建中"但内部已完成 step 执行。状态机转换必须和 UI 同步。

---

## 五、数据结构设计

### 5.1 Trial（孪生试炼）

```typescript
interface Trial {
  id: string;                        // UUID
  name: string;                      // 用户可命名，如 "Build System 开发流程演化 v1"
  created_at: string;                // ISO 时间
  updated_at: string;
  status: TrialStatus;               // 见状态枚举
  
  // 镜像现实
  team_snapshot: TeamSnapshot;       // 创建时的团队快照
  task_goal: TaskGoal;               // 试炼目标
  scenario: string;                  // 场景：workshop_evolution / arena_competition / etc.
  mode: TrialMode;                   // What-if / MultiBranch / Chaos / Evolutionary / Replay
  
  // 运行
  branches: Branch[];                // 试验分支列表
  current_branch_id: string | null;  // 当前活跃分支
  
  // 参数
  max_steps: number;                 // 最大步数
  acceleration: number;              // 加速倍率
  parallel_branches: number;         // 最大并行分支数
  
  // 结果
  evaluation: TrialEvaluation | null;
  extracted_sops: SOP[];
  feedback_actions: FeedbackAction[];
  
  // 元信息
  tags: string[];
  notes: string;
}

type TrialStatus = 
  | 'idle' 
  | 'creating' 
  | 'ready' 
  | 'running' 
  | 'paused' 
  | 'evaluating' 
  | 'completed' 
  | 'failed' 
  | 'archived';

type TrialMode = 
  | 'what_if'         // 单分支基线
  | 'multi_branch'    // 多分支对比
  | 'chaos_drill'     // 混沌演练
  | 'evolutionary'    // 演化试炼
  | 'replay';         // 回放复盘
```

### 5.2 Branch（试验分支）

```typescript
interface Branch {
  id: string;
  trial_id: string;
  name: string;                      // "baseline" / "chaos_network_delay" / "optimized_v2"
  label: string;                     // 显示标签
  color: string;                     // UI 颜色标识（用于曲线、空间标注）
  
  // 来源
  parent_branch_id: string | null;   // 从哪个分支分裂而来
  fork_at_step: number | null;       // 在哪一步分裂
  
  // 初始条件
  initial_conditions: BranchConditions;
  injected_events: InjectedEvent[];  // 预设注入事件
  
  // 运行
  sessions: Session[];               // 该分支下的 Session 列表
  current_session_id: string | null;
  
  // 状态
  status: BranchStatus;
  current_step: number;
  
  // 结果
  final_score: number | null;
  reward_curve: RewardPoint[];       // 完整 reward 序列
  agent_contributions: AgentContribution[];
  skill_usage: SkillUsage[];
  checkpoints: Checkpoint[];         // 关键帧
  
  // 时间
  created_at: string;
  completed_at: string | null;
}

type BranchStatus = 
  | 'pending' 
  | 'running' 
  | 'paused' 
  | 'completed' 
  | 'failed';
```

### 5.3 Session / Run（具体运行）

```typescript
interface Session {
  id: string;                        // 后端沙箱 session_id
  branch_id: string;
  trial_id: string;
  
  status: SessionStatus;
  current_step: number;
  max_steps: number;
  
  // 步骤记录
  steps: StepRecord[];
  
  // 实时状态
  latest_reward: number | null;
  latest_agent_actions: AgentAction[];
  
  // 元信息
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  
  // 原始后端数据
  raw_session_id: string;            // 对应后端 session.id
}

type SessionStatus = 
  | 'created' 
  | 'ready' 
  | 'running' 
  | 'paused' 
  | 'completed' 
  | 'failed' 
  | 'evaluating';
```

### 5.4 StepRecord（步骤记录）

```typescript
interface StepRecord {
  step_index: number;                // 统一编号：从后端返回的 step number，唯一来源
  timestamp: string;
  reward: number;
  delta_reward: number;              // 与上一步的差值
  
  agent_actions: AgentAction[];
  events: TrialEvent[];              // 本步发生的事件（包括注入）
  
  state_snapshot: AgentStateSnapshot[]; // 每个 Agent 的状态
  room_positions: RoomPositionMap;   // 每个 Agent 的房间位置
  
  collaboration_graph: CollaborationEdge[]; // 当前协作拓扑
  
  // SECS 层状态
  secs_active_layer: 'L1' | 'L2' | 'L3' | 'L4' | 'Loop';
}

interface AgentAction {
  agent_id: string;
  agent_name: string;
  action_type: 'claim_task' | 'execute_skill' | 'transfer' | 'broadcast' | 'idle' | 'failed';
  skill_name: string | null;
  target_agent_id: string | null;
  result: 'success' | 'failure' | 'pending';
  detail: string;
}

type RoomPositionMap = {
  [agent_id: string]: 'congress_hall' | 'extraction_room' | 'workshop' | 'knowledge_base' | 'arena' | 'rest_area';
};
```

### 5.5 TeamSnapshot（团队快照）

```typescript
interface TeamSnapshot {
  snapshot_at: string;
  team_id: string;
  team_name: string;
  agents: AgentSnapshot[];
  collaboration_graph: CollaborationEdge[];
  room_positions: RoomPositionMap;
}

interface AgentSnapshot {
  id: string;
  name: string;
  role: string;
  skills: string[];
  skill_scores: { [skill_name: string]: number }; // 当前技能得分
  room: string;
  status: 'active' | 'idle' | 'offline';
  history_performance: number;       // 历史平均 reward 贡献
}
```

### 5.6 TrialEvaluation（试炼评分）

```typescript
interface TrialEvaluation {
  trial_id: string;
  evaluated_at: string;
  
  // 分支比较
  branch_scores: BranchScore[];
  best_branch_id: string;
  worst_branch_id: string;
  
  // 关键发现
  key_insights: string[];
  turning_points: TurningPoint[];    // 关键转折 step
  bottleneck_agents: string[];
  bottleneck_skills: string[];
  
  // 总体推荐
  recommended_strategy: string;
  sop_candidates: SOPCandidate[];
  feedback_suggestions: FeedbackSuggestion[];
}

interface BranchScore {
  branch_id: string;
  branch_name: string;
  
  // 五维评分（0-1）
  task_completion: number;           // 目标完成度
  collaboration_efficiency: number;  // 协作效率
  resilience: number;                // 韧性
  cost_efficiency: number;           // 成本控制
  extractability: number;            // 可萃取性
  
  total_score: number;               // 加权总分
  max_reward: number;
  final_reward: number;
  total_steps: number;
  recovery_steps: number | null;     // 混沌演练专用：故障后恢复步数
}
```

### 5.7 TrialEvent（统一事件模型）

```typescript
interface TrialEvent {
  id: string;
  trial_id: string;
  branch_id: string;
  session_id: string;
  step_index: number;
  timestamp: string;
  
  type: TrialEventType;
  source: 'system' | 'user' | 'agent' | 'backend';
  payload: Record<string, any>;      // 事件特定数据
  
  // UI 显示
  display_level: 'info' | 'warning' | 'error' | 'success';
  display_text: string;
  is_milestone: boolean;             // 是否在时间轴上标注
}

type TrialEventType =
  | 'trial_created'
  | 'branch_created'
  | 'branch_forked'
  | 'session_started'
  | 'agent_moved'
  | 'skill_selected'
  | 'step_executed'
  | 'reward_updated'
  | 'fault_injected'
  | 'fault_recovered'
  | 'task_changed'
  | 'agent_joined'
  | 'agent_left'
  | 'collaboration_graph_updated'
  | 'checkpoint_created'
  | 'branch_completed'
  | 'evaluation_started'
  | 'evaluation_completed'
  | 'score_generated'
  | 'sop_extracted'
  | 'feedback_applied'
  | 'trial_completed'
  | 'trial_failed';
```

### 5.8 SOP（标准操作程序）

```typescript
interface SOP {
  id: string;
  name: string;
  created_at: string;
  source_trial_id: string;
  source_branch_id: string;
  source_steps: number[];            // 从哪些 step 萃取
  
  // 内容
  description: string;
  trigger_condition: string;         // 什么情况下触发此 SOP
  steps: SOPStep[];
  expected_reward_gain: number;      // 预期 reward 提升
  
  // 适用范围
  applicable_teams: string[];
  applicable_scenarios: string[];
  applicable_skills: string[];
  
  // 状态
  status: 'candidate' | 'reviewed' | 'approved' | 'applied' | 'deprecated';
  confidence: number;                // 0-1，基于来源 Trial 的置信度
  
  // 元信息
  version: number;
  tags: string[];
}

interface SOPStep {
  order: number;
  agent_role: string;
  action: string;
  precondition: string | null;
  expected_output: string;
  fallback: string | null;
}
```

---

## 六、后端 API 设计

### 6.1 Trial API

```
POST   /api/twin-trials
       创建 Trial，返回 trial_id、默认 baseline branch_id、session_id

GET    /api/twin-trials
       获取历史 Trial 列表（支持分页、过滤）

GET    /api/twin-trials/:trial_id
       获取完整 Trial 详情

PATCH  /api/twin-trials/:trial_id
       更新 Trial 名称、备注、标签

DELETE /api/twin-trials/:trial_id
       归档 Trial（软删除）
```

### 6.2 Branch API

```
POST   /api/twin-trials/:trial_id/branches
       从当前 step 或指定 checkpoint 分裂新分支
       body: { fork_from_branch_id, fork_at_step, name, initial_conditions }

GET    /api/twin-trials/:trial_id/branches
       获取 Trial 下所有分支

GET    /api/twin-trials/:trial_id/branches/:branch_id
       获取分支详情

POST   /api/twin-trials/:trial_id/branches/:branch_id/step
       单步推演
       body: { }
       response: { step_index, reward, agent_actions, events, room_positions }

POST   /api/twin-trials/:trial_id/branches/:branch_id/run
       自动推演
       body: { until_step?, acceleration? }

POST   /api/twin-trials/:trial_id/branches/:branch_id/pause
       暂停推演

POST   /api/twin-trials/:trial_id/branches/:branch_id/resume
       恢复推演

POST   /api/twin-trials/:trial_id/branches/:branch_id/events
       注入演练事件
       body: { event_type, payload, trigger_at_step? }
```

### 6.3 评估与萃取 API

```
POST   /api/twin-trials/:trial_id/evaluate
       评估所有 Branch，生成五维评分和比较结果

POST   /api/twin-trials/:trial_id/extract-sop
       从最佳 Branch 萃取 SOP 候选
       body: { branch_id?, min_confidence? }

POST   /api/twin-trials/:trial_id/feedback
       将 SOP/策略反哺到 Agent 或技能库
       body: { sop_ids, target_agents?, target_skills? }
```

### 6.4 流式事件 API

```
GET    /api/twin-trials/:trial_id/events/stream
       SSE 事件流，推送所有 TrialEvent
       query: { branch_id?, event_types?, since_step? }
```

### 6.5 兼容性要求

- 保留现有 `/api/sessions/:session_id` 接口，但标记为 deprecated。
- 新接口内部可以复用 session 逻辑，但对外暴露 Trial/Branch 抽象。
- Session ID 仍然保留，但作为 Branch 的内部实现细节，不直接暴露给前端主流程。

### 6.6 错误处理规范

所有接口必须：
- 返回 4xx（业务错误）或 5xx（系统错误）时，携带 `{ error_code, message, detail }` JSON body。
- **绝对不允许**返回 HTTP 500 时 body 为空或非 JSON 格式。
- Session/Branch 详情接口在数据不完整（评分生成中、SOP 未萃取）时，返回 200 + 部分数据 + `incomplete` 标志，而不是 500。

示例容错响应：
```json
{
  "id": "6fa8248f",
  "status": "evaluating",
  "current_step": 37,
  "max_reward": 0.696,
  "evaluation": null,
  "evaluation_status": "pending",
  "extracted_sops": [],
  "incomplete": true,
  "incomplete_reason": "evaluation_in_progress"
}
```

---

## 七、前端状态管理设计

### 7.1 核心状态树

```typescript
interface DigitalTwinState {
  // 全局运行时
  runtime: RuntimeState;
  
  // 当前 Trial
  activeTrial: Trial | null;
  trialStatus: TrialStatus;
  
  // 当前 Branch
  activeBranchId: string | null;
  branches: { [branch_id: string]: Branch };
  
  // 实时运行
  currentStep: number;             // 唯一来源：后端返回的 step_index
  latestReward: number | null;
  isRunning: boolean;
  isCreating: boolean;             // 仅在创建 Trial 的网络请求期间为 true
  
  // 环境空间
  roomAgentMap: RoomAgentMap;      // 唯一空间状态源
  
  // 事件流
  events: TrialEvent[];            // 统一事件列表
  
  // 历史
  trialHistory: TrialSummary[];
  
  // UI
  selectedTab: 'reward_curve' | 'event_log' | 'console' | 'sop' | 'score';
  isRightPanelExpanded: boolean;
  isResultPanelVisible: boolean;
}
```

### 7.2 状态同步规则

1. **`currentStep` 唯一来源**：只从后端 step 响应或 SSE 事件中提取，前端不自增。
2. **`isCreating` 严格范围**：只在 `POST /twin-trials` 的网络请求 pending 期间为 true，收到响应（成功或失败）立即置为 false。
3. **`roomAgentMap` 唯一来源**：所有显示 Agent 位置的地方（房间卡片、Agent 列表、空间标题、已部署数量）都从 `roomAgentMap` 读取，不允许多源。
4. **`trialHistory` 即时更新**：创建 Trial 后立即写入 history（状态 creating），不等到完成再写。
5. **SSE 与 API 响应去重**：step 执行可能同时通过 API response 和 SSE 两个通道到达，必须按 `step_index` 去重，不能重复写入。

### 7.3 SECS Pipeline 实时联动

SECS Pipeline 不再是静态说明文字，而是实时指示当前 step 处于哪一层：

| step 行为 | 激活层 |
|---|---|
| 创建 Trial，镜像团队 | L1 MADTwin |
| AAS 选择技能组合 | L2 AAS |
| 执行 step，推进仿真 | L3 TwinLoop |
| 协作图动态重构 | L4 MADCG |
| 萃取 SOP，反哺 Agent | Loop ↩ |

---

## 八、环境空间视觉设计

### 8.1 Agent 位置显示

- 每个房间卡片显示：房间名、当前 Agent 数量、Agent 头像列表。
- Agent 图标在房间之间移动时有过渡动画（300ms ease）。
- 不同 Branch 的 Agent 用对应 Branch 颜色区分（Border / 背景色 / 标签）。

### 8.2 故障注入视觉反馈

| 故障类型 | 视觉效果 |
|---|---|
| 网络延迟 | 工作坊房间边框变橙色，受影响 Agent 图标上出现 ⏳ |
| Agent 失联 | Agent 图标变灰，移入休息区，房间计数 -1 |
| 技能退化 | Agent 图标上出现 ⚠️，技能标签变红 |
| 逻辑死锁 | 议事厅/工作坊出现 🔴 标注，reward 曲线停滞高亮 |

### 8.3 Reward 热力反馈

- reward 上升时，当前活跃房间（工作坊/演练场）背景微微泛绿。
- reward 下降时，背景微微泛红。
- reward 峰值时，对应房间出现短暂金色光晕。
- 多 Branch 对比时，每个 Branch 的热力色叠加显示（透明度区分）。

### 8.4 空间标题同步规则

- 空间标题显示格式：`{房间名} — {Agent 数} 个智能体`
- 数据来源：`roomAgentMap[room_id].length`
- 当没有 Agent 时显示：`{房间名} — 空`
- 不允许显示"议事厅 — 28 个智能体"但房间卡片显示 0（当前 bug）

---

## 九、评分系统设计

### 9.1 五维评分

| 维度 | 权重 | 计算方式 |
|---|---|---|
| 目标完成度 Task Completion | 30% | 最终 reward / 理论最大 reward |
| 协作效率 Collaboration Efficiency | 25% | 并行度、交接次数、阻塞时间 |
| 韧性 Resilience | 20% | 故障后恢复步数比例（无故障时默认满分） |
| 成本控制 Cost Efficiency | 15% | 1 - (实际步数 / 最大步数) |
| 可萃取性 Extractability | 10% | 稳定重复路径比例 |

### 9.2 评分展示

- 每个 Branch 独立显示五维雷达图。
- 所有 Branch 的总分对比显示为柱状图。
- 最佳 Branch 标注 ⭐，失败/最差 Branch 标注 ⚠️。
- 关键转折点（reward 突变 step）在时间轴上标红。

### 9.3 SOP 萃取逻辑

从最佳 Branch 萃取 SOP 的条件：
1. Branch 最终 reward > 基线 Branch 最终 reward × 1.05（至少 5% 提升）
2. 关键路径步骤在多次运行中稳定出现（重复率 > 70%）
3. 每个 SOP 步骤必须有明确的 `agent_role`、`action`、`expected_output`

---

## 十、SECS 系统集成

### 10.1 SECS 四层的试炼职责

| SECS 层 | 在试炼中的角色 | 前端表现 |
|---|---|---|
| L1 MADTwin | 创建团队快照，实时镜像空间状态 | Trial 创建时高亮，空间同步时活跃 |
| L2 AAS | 为每步的 Agent 选择最优技能 | 每 step 显示技能选择结果 |
| L3 TwinLoop | 执行仿真循环，校验状态 | 自动运行期间持续活跃 |
| L4 MADCG | 动态更新协作拓扑图 | 协作图变更时高亮 |
| Loop ↩ | SOP 萃取和反哺回现实 | 萃取完成后高亮 |

### 10.2 SECS 状态指示器

Pipeline 展示方式：

```
当前状态：L3 TwinLoop 运行中

[L1 MADTwin] ✓  →  [L2 AAS] ✓  →  [L3 TwinLoop] ●  →  [L4 MADCG] ○  →  [↩ Loop] ○
```

- ✓ 已完成
- ● 当前活跃（动画闪烁）
- ○ 待处理

---

## 十一、当前已知 Bug 清单

### Bug-001：Session 状态卡住（优先级：P0）
- **现象**：点击启动后，控制台显示"会话已创建，等待指令"，按钮卡在"创建中"。
- **根因**：create session 成功后，前端未清除 `isCreating` 状态，未切换 sessionStatus 到 ready，未继续调用 run/step。
- **修复**：create session 成功后立即清除 creating 状态，设置 currentSessionId，切换 UI 到 ready。

### Bug-002：Step 编号不一致（优先级：P0）
- **现象**：日志同时出现 Step 0 / Step 1 / Step 2，含义不同。
- **根因**：前端本地计数器、后端返回 step number、SSE event step 三套来源混用。
- **修复**：统一使用后端返回的 step_index，前端不自行维护 step 计数。

### Bug-003：获取会话详情 HTTP 500（优先级：P0）
- **现象**：演练完成后，"获取会话详情"接口返回 500，评分和 SOP 无法显示。
- **根因**：后端 session details 接口在 evaluating 状态时崩溃，可能因评分字段为 null 导致序列化失败。
- **修复**：增加 null 检查，evaluating 状态时返回 200 + 部分数据 + incomplete 标志。

### Bug-004：空间状态不同步（优先级：P1）
- **现象**：环境空间标题显示"28 个智能体"，但各房间卡片显示 0。
- **根因**：标题和卡片读取的数据源不一致，roomAgentMap 未被正确维护。
- **修复**：统一所有空间显示都从 roomAgentMap 读取，清除其他来源。

### Bug-005：Metrics 不同步（优先级：P1）
- **现象**：session 已创建、step 已执行，但全局统计仍显示"沙箱会话 0、总仿真步 0"。
- **根因**：session 创建后未写入 metrics，或 metrics 轮询未被正确触发。
- **修复**：session 创建后立即递增 metrics 计数，step 执行后立即更新总仿真步。

### Bug-006：演练历史不显示（优先级：P1）
- **现象**：Trial 已在运行，历史面板显示"暂无演练记录"。
- **根因**：历史记录只在 completed 状态写入，不记录 running/paused 状态。
- **修复**：Trial 创建后立即写入历史，记录完整生命周期状态。

### Bug-007：SSE/API 事件重复（优先级：P2）
- **现象**：日志出现两条相似日志（一条来自 API response，一条来自 SSE）。
- **根因**：step 执行通过 API response 和 SSE 两个通道同时到达，前端未去重。
- **修复**：按 step_index 去重，统一合并到事件流。

---

## 十二、SECS 演练 Pipeline 配置（现有逻辑保留并增强）

当前 SECS Pipeline 配置：

```
L1 MADTwin   多智能体数字孪生：实时镜像团队状态
L2 AAS       自适应技能选择：结合环境上下文自动匹配技能
L3 TwinLoop  孪生回环：在数字孪生中持续模拟、校验、修正
L4 MADCG     多智能体自适应协作图：动态构建协作拓扑并生成执行计划
Loop ↩       萃取反哺
```

增强方向：
1. 每层增加"本次 Trial 该层处于何种状态"的实时标注。
2. L4 MADCG 的协作图要在空间视图中实时渲染，而不只是文字说明。
3. Loop 阶段要触发萃取室空间激活，Agent 进入萃取室可见。

---

## 十三、CLI 命令扩展

现有 CLI 已支持：`status agents skills rooms pipeline flow last simulate stress discuss config export`

建议扩展支持 Trial 相关命令：

```
trial create --team "Build System" --mode evolutionary --steps 200
trial list
trial show <trial_id>
trial fork <branch_id> --at-step 10 --name "chaos_v2"
trial inject <trial_id> --event network_delay --at-step 8
trial eval <trial_id>
trial extract-sop <trial_id>
trial feedback <trial_id> --sops all
trial archive <trial_id>
```

---

## 十四、最终产品体验目标

用户站在这个页面前，应该感受到：

> 我不是在操作一个控制台。  
> 我是在管理一个虚拟组织实验室。  
> 我可以把真实团队复制进去，给它一个任务。  
> 从某个关键节点分裂出多个未来。  
> 给某条未来注入故障，看它能不能活下来。  
> 最后选出最优路径，把它变成现实团队的 SOP。

这就是数字孪生中"尝试及模拟"的真正本领：
**不是预测一个结果，而是制造多个可验证的未来，从中训练现实系统。**

---

*文档版本：v1.0 · 2026-06-09 · Tabbit 智能体助手*
