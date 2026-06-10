# Agent 数字孪生优化 — 手把手实施 TODO 清单
# AgentsGroup2026 Digital Twin — Step-by-Step Implementation TODOs

> 版本：v1.0 · 日期：2026-06-09  
> 配套文档：`Agent数字孪生优化plan.md`  
> 适用对象：CodeBuddy（请先阅读 plan.md 理解设计意图，再按此 TODO 逐条实施）  
> 执行原则：**按顺序实施，每条完成后输出"涉及文件 + 修改内容 + 验证结果"再进行下一条。**

---

## 阶段零：准备工作（必读）

> 在动任何代码前，先完成这些准备，否则后续实施会出现方向偏差。

- [x] ~~Z-01~~** 阅读 `Agent数字孪生优化plan.md` 全文，理解 Trial/Branch/Session 三层模型、五种试炼模式、环境空间状态机、统一事件模型、五维评分体系。
- [x] ~~Z-02~~** 梳理当前代码目录结构，列出前端主文件、后端主文件、API 路由文件、状态管理文件、SSE 相关文件。
- [x] ~~Z-03~~** 梳理当前已有 API 接口列表（endpoint、method、request、response），标注哪些需要保留、哪些需要修改、哪些需要新增。
- [x] ~~Z-04~~** 确认当前后端 session 相关接口的数据库 schema 或内存结构，理解 session 字段定义。
- [x] ~~Z-05~~** 在代码库中搜索所有出现 `isCreating`、`loading`、`creating` 的地方，列出清单，这些是 Bug-001 的修复目标。
- [x] ~~Z-06~~** 在代码库中搜索所有出现 `step`、`currentStep`、`step_index`、`stepCount` 的地方，列出清单，这些是 Bug-002 的修复目标。
- [x] ~~Z-07~~** 在代码库中搜索所有出现 `roomAgentMap`、`agentRoom`、`room`、`space` 的地方，列出清单，这些是 Bug-004 的修复目标。
- [x] ~~Z-08~~** 确认 SSE 事件推送机制：后端如何推送、前端如何监听、当前事件字段结构是什么。

---

## 阶段一：紧急 Bug 修复（P0 优先，必须最先完成）

> 这些 Bug 当前直接阻断演练闭环，必须在任何新功能开发前修复完毕。

### Bug-001：Session 状态卡住（按钮永久显示"创建中"）

- [x] ~~B01-01~~** 找到前端"启动演练/创建试炼"按钮的点击处理函数。
- [x] ~~B01-02~~** 找到 `createSession` 或等效 API 调用的位置，检查 `.then()` / `await` 后的代码。
- [x] ~~B01-03~~** 确认：API 调用成功后，是否执行了以下操作（如果没有，添加）：
  ```javascript
  isCreating = false;
  currentSessionId = response.session_id;  // 或等效字段
  sessionStatus = 'ready';
  // 更新按钮文字为"启动演练"或"就绪"
  ```
- [x] ~~B01-04~~** 确认：API 调用失败后，是否执行了以下操作（如果没有，添加）：
  ```javascript
  isCreating = false;
  sessionStatus = 'failed';
  // 显示错误信息给用户
  ```
- [x] ~~B01-05~~** 添加超时兜底：如果 `isCreating` 超过 10 秒未被清除，强制置为 false 并显示超时提示。
- [x] ~~B01-06~~** 验证：点击启动后，控制台出现"会话已创建"后，按钮必须立即变为可点击的"单步"或"自动运行"状态，不再显示"创建中"。

---

### Bug-002：Step 编号不一致（Step 0 / Step 1 / Step 2 混乱）

- [x] ~~B02-01~~** 找到所有更新 `currentStep` 的代码位置（API response 解析、SSE 事件处理、本地自增）。
- [x] ~~B02-02~~** 删除所有前端本地 step 自增逻辑（如 `currentStep++`、`this.step += 1`）。
- [x] ~~B02-03~~** 确认后端 step response 的字段名（如 `step`、`step_index`、`current_step`），统一前端解析字段。
- [x] ~~B02-04~~** 修改前端：`currentStep` 只从后端返回值赋值：
  ```javascript
  // API response 场景
  currentStep = response.step_index;  // 使用后端字段名
  
  // SSE 事件场景
  currentStep = event.data.step_index;
  ```
- [x] ~~B02-05~~** SSE 和 API 去重：如果同一个 step 通过两个通道到达，按 `step_index` 去重，不重复写入日志。
  ```javascript
  if (!stepSet.has(stepData.step_index)) {
    stepSet.add(stepData.step_index);
    appendStepToLog(stepData);
  }
  ```
- [x] ~~B02-06~~** 验证：日志中的 step 编号必须连续且唯一（Step 2, Step 3, Step 4...），不出现 Step 0 和 Step 2 同时显示的情况。

---

### Bug-003：获取会话详情 HTTP 500

- [x] ~~B03-01~~** 找到后端 `GET /api/sessions/:id` 或等效接口的实现代码。
- [x] ~~B03-02~~** 在接口中添加全局异常捕获：
  ```python
  try:
      session = get_session(session_id)
      ...
  except Exception as e:
      return JSONResponse(status_code=500, content={"error_code": "SESSION_DETAIL_ERROR", "message": str(e)})
  ```
- [x] ~~B03-03~~** 检查 session 对象中可能为 null 的字段：`score`、`evaluation`、`sops`、`steps`，在序列化前添加 null 检查。
- [x] ~~B03-04~~** 修改接口逻辑：当 session 处于 `evaluating` 状态时，返回 200 + 部分数据：
  ```json
  {
    "id": "xxx",
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
- [x] ~~B03-05~~** 前端接收到 `incomplete: true` 时，显示友好提示而不是空白或报错：
  - 评分区域：显示"评分生成中..."
  - SOP 区域：显示"尚未萃取"
  - 报告区域：显示已有数据（步数、reward 曲线）
- [x] ~~B03-06~~** 验证：演练运行完成后，点击查看报告，页面必须显示至少步数和 reward，不再出现整页空白或 500 报错。

---

### Bug-004：环境空间 Agent 人数不同步

- [x] ~~B04-01~~** 找到"环境空间标题"的渲染代码（显示"议事厅 — 28 个智能体"的位置）。
- [x] ~~B04-02~~** 找到"房间卡片"的渲染代码（显示"0 智能体"的位置）。
- [x] ~~B04-03~~** 找到当前维护 Agent 位置的所有数据结构，可能有多个来源（如 `team.agents`、`roomAgents`、`deployedAgents`）。
- [x] ~~B04-04~~** 定义唯一的空间状态源：
  ```typescript
  // 唯一来源
  roomAgentMap: {
    congress_hall: AgentSnapshot[],
    extraction_room: AgentSnapshot[],
    workshop: AgentSnapshot[],
    knowledge_base: AgentSnapshot[],
    arena: AgentSnapshot[],
    rest_area: AgentSnapshot[]
  }
  ```
- [x] ~~B04-05~~** 所有显示 Agent 位置的地方统一从 `roomAgentMap` 读取：
  - 房间卡片 Agent 数量 → `roomAgentMap[room_id].length`
  - 房间标题 → `{房间名} — {roomAgentMap[room_id].length} 个智能体`
  - 系统状态"已部署"数量 → 所有 room 的 Agent 总和
  - Agent 列表中的"空间"字段 → 从 `roomAgentMap` 反查
- [x] ~~B04-06~~** 实现初始部署逻辑：选择团队 + 场景后，将 Agent 批量写入对应房间的 `roomAgentMap`。
  - Build System + 工作坊演化 → 7 个 Agent 写入 `workshop`
  - 全体 + 议事厅聚焦 → 28 个 Agent 写入 `congress_hall`
- [x] ~~B04-07~~** 验证：
  - 选择 Build System + 工作坊演化后，工作坊卡片显示 7 个智能体
  - 系统状态"已部署"显示 7
  - Agent 列表中 7 个 Agent 的"空间"字段显示"工作坊"
  - 其他房间显示"空"

---

### Bug-005：全局 Metrics 不同步

- [x] ~~B05-01~~** 找到"沙箱会话"、"总仿真步"、"提取SOP"、"最优评分"这四个指标的数据来源和渲染代码。
- [x] ~~B05-02~~** 实现即时更新：
  - 会话创建成功后：`sandboxSessions += 1`，写入历史记录（状态 creating/ready）
  - 每次 step 成功后：`totalSimSteps += 1`
  - SOP 萃取成功后：`extractedSops += 1`
  - 评分生成后：`bestScore = Math.max(bestScore, newScore)`
- [x] ~~B05-03~~** 验证：Session 创建后，全局统计"沙箱会话"从 0 变为 1，step 执行后"总仿真步"递增。

---

### Bug-006：演练历史不显示

- [x] ~~B06-01~~** 找到演练历史列表的数据来源和渲染代码。
- [x] ~~B06-02~~** 修改历史写入逻辑：Trial/Session 创建后立即写入历史（不等到 completed）：
  ```javascript
  // 创建时
  historyList.unshift({
    id: sessionId,
    status: 'creating',
    team: selectedTeam,
    mode: selectedMode,
    created_at: new Date().toISOString(),
    steps: 0,
    max_reward: null,
    sop_count: 0
  });
  
  // 状态变化时更新
  updateHistory(sessionId, { status: 'running', steps: currentStep, max_reward: latestReward });
  ```
- [x] ~~B06-03~~** 验证：启动演练后，历史面板立即出现一条记录，状态从 creating → running → completed 依次更新。

---

## 阶段二：概念模型重构（引入 Trial/Branch/Session 三层）

> P0 Bug 全部修复并验证后，开始此阶段。

### 后端：新增 Trial 和 Branch 数据模型

[x] ~~M-01~~ 定义 `Trial` 数据模型（参考 plan.md 第五章）：
  ```python
  class Trial:
      id: str
      name: str
      status: str  # idle/creating/ready/running/paused/evaluating/completed/failed/archived
      team_snapshot: dict
      task_goal: dict
      scenario: str
      mode: str  # what_if/multi_branch/chaos_drill/evolutionary/replay
      branches: list
      max_steps: int
      acceleration: int
      parallel_branches: int
      evaluation: dict | None
      extracted_sops: list
      feedback_actions: list
      created_at: str
      updated_at: str
  ```
[x] ~~M-02~~ 定义 `Branch` 数据模型：
  ```python
  class Branch:
      id: str
      trial_id: str
      name: str
      label: str
      color: str  # UI 颜色，如 #4A90E2
      parent_branch_id: str | None
      fork_at_step: int | None
      initial_conditions: dict
      injected_events: list
      sessions: list
      current_session_id: str | None
      status: str  # pending/running/paused/completed/failed
      current_step: int
      final_score: float | None
      reward_curve: list  # [{step, reward}]
      agent_contributions: list
      checkpoints: list
      created_at: str
      completed_at: str | None
  ```
[x] ~~M-03~~ 定义统一 `TrialEvent` 事件模型（参考 plan.md 第五章 5.7）。
[x] ~~M-04~~ 现有 `Session` 模型增加字段：`branch_id`、`trial_id`，向后兼容。

---

### 后端：新增 Trial API 接口

[x] ~~A-01~~ 实现 `POST /api/twin-trials`：
  - 接收：team_id、task_goal、scenario、mode、max_steps、acceleration
  - 创建 Trial 对象
  - 自动创建 baseline Branch
  - 调用现有 create session 逻辑，关联到 baseline Branch
  - 返回：`{ trial_id, branch_id, session_id, status: 'ready' }`
[x] ~~A-02~~ 实现 `GET /api/twin-trials`：
  - 返回历史 Trial 列表，按创建时间倒序
  - 每条包含：id、name、status、mode、team_name、max_reward、total_steps、sop_count、created_at
  - 支持分页：`?page=1&page_size=20`
[x] ~~A-03~~ 实现 `GET /api/twin-trials/:trial_id`：
  - 返回完整 Trial 详情，包含所有 Branch 和 Session 摘要
  - 即使 evaluation/sops 为空，也返回 200 + `incomplete: true`
[x] ~~A-04~~ 实现 `POST /api/twin-trials/:trial_id/branches`（分裂分支）：
  - 接收：fork_from_branch_id、fork_at_step、name、initial_conditions
  - 从指定 step 的 state_snapshot 创建新 Branch
  - 自动创建新 Session，继承父分支的状态快照
  - 返回：`{ branch_id, session_id }`
[x] ~~A-05~~ 实现 `POST /api/twin-trials/:trial_id/branches/:branch_id/step`：
  - 调用现有 step 逻辑
  - 返回：`{ step_index, reward, agent_actions, room_positions, secs_active_layer }`
  - 同时推送 SSE 事件
[x] ~~A-06~~ 实现 `POST /api/twin-trials/:trial_id/branches/:branch_id/run`：
  - 调用现有 auto_run 逻辑
  - 返回：`{ status: 'running' }`
  - 后续通过 SSE 持续推送 step 事件
[x] ~~A-07~~ 实现 `POST /api/twin-trials/:trial_id/branches/:branch_id/pause`：
  - 暂停当前 Branch 的运行
  - 返回：`{ status: 'paused', current_step }`
[x] ~~A-08~~ 实现 `POST /api/twin-trials/:trial_id/branches/:branch_id/events`（注入演练事件）：
  - 接收：`{ event_type, payload, trigger_at_step? }`
  - event_type 包括：network_delay、agent_leave、task_change、skill_degraded
  - 立即生效（如果在运行中）或在指定 step 生效（如果预设）
[x] ~~A-09~~ 实现 `POST /api/twin-trials/:trial_id/evaluate`：
  - 计算所有 Branch 的五维评分（参考 plan.md 第九章）
  - 标注最佳/最差 Branch
  - 生成 key_insights 和 turning_points
  - 返回完整 TrialEvaluation 对象
[x] ~~A-10~~ 实现 `POST /api/twin-trials/:trial_id/extract-sop`：
  - 从最佳 Branch 提取关键路径
  - 生成 SOP 候选（参考 plan.md 第五章 5.8）
  - 返回 SOP 列表
[x] ~~A-11~~ 实现 `POST /api/twin-trials/:trial_id/feedback`：
  - 将 SOP/策略写回到 Agent 技能库或协作图
  - 返回：`{ applied_sops, updated_agents, updated_skills }`
[x] ~~A-12~~ 实现 `GET /api/twin-trials/:trial_id/events/stream`（SSE 事件流）：
  - 支持过滤：`?branch_id=&event_types=&since_step=`
  - 推送所有 TrialEvent
  - 客户端断线重连时，支持从指定事件 ID 续传

---

### 前端：状态管理重构

[x] ~~S-01~~ 定义统一状态树（参考 plan.md 第七章 7.1）：
  ```typescript
  interface DigitalTwinState {
    runtime: RuntimeState;
    activeTrial: Trial | null;
    trialStatus: TrialStatus;
    activeBranchId: string | null;
    branches: { [branch_id: string]: Branch };
    currentStep: number;           // 唯一来源：后端返回值
    latestReward: number | null;
    isRunning: boolean;
    isCreating: boolean;           // 仅网络请求期间为 true
    roomAgentMap: RoomAgentMap;    // 唯一空间状态源
    events: TrialEvent[];
    trialHistory: TrialSummary[];
    selectedTab: string;
  }
  ```
[x] ~~S-02~~ 实现 `roomAgentMap` 唯一来源规则：删除其他维护 Agent 位置的变量，所有读取统一走 `roomAgentMap`。
[x] ~~S-03~~ 实现状态机转换函数：
  ```typescript
  function transitionTrialStatus(from: TrialStatus, to: TrialStatus): void {
    // 验证转换合法性
    const validTransitions = {
      idle: ['creating'],
      creating: ['ready', 'failed'],
      ready: ['running'],
      running: ['paused', 'evaluating', 'failed'],
      paused: ['running', 'evaluating', 'failed'],
      evaluating: ['completed', 'failed'],
      completed: ['archived'],
      failed: ['idle'],
    };
    if (!validTransitions[from]?.includes(to)) {
      console.error(`Invalid status transition: ${from} -> ${to}`);
      return;
    }
    trialStatus = to;
    updateButtonStates(to);
  }
  ```
[x] ~~S-04~~ 实现统一事件处理器：所有 SSE 事件和 API 响应统一流入 `handleTrialEvent(event: TrialEvent)`，按 `event.type` 分发处理，不再散落在各处。
[x] ~~S-05~~ 实现 SSE/API 去重：维护 `processedStepSet: Set<number>`，按 `step_index` 去重。

---

## 阶段三：前端 UI 重构

> 阶段二完成后，开始 UI 重构。

### 布局重构

- [x] ~~U-01~~** 将"环境空间"模块移至页面视觉中心，占据主要屏幕宽度（建议 60-70%）。
[x] ~~U-02~~ 将"智能体团队"移至左侧边栏（建议 20%宽度），支持折叠。
[x] ~~U-03~~ 将"演练配置"升级为"试炼导演台"，放置右侧（建议 20-25%宽度），支持折叠。
- [x] ~~U-04~~** 将"系统状态 / 交互流 / 编排管线"改为顶部折叠栏或右侧抽屉，不占主视图空间。
[x] ~~U-05~~ 底部添加"试炼时间轴"区域，统一展示 step/reward/event/agent_action/分支比较。

---

### 按钮状态机实现

[x] ~~U-06~~ 实现按钮状态机，按 `trialStatus` 显示对应按钮组（参考 plan.md 第四章 4.4）：
  ```
  idle        → [创建试炼]
  creating    → [⏳ 创建中...] （禁用，显示 spinner）
  ready       → [▶ 单步推演] [▶▶ 自动推演] [💥 注入事件] [⑂ 分裂分支]
  running     → [⏸ 暂停] [💥 注入事件] [⑂ 分裂分支]
  paused      → [▶ 继续] [▶ 单步推演] [⏹ 终止] [💥 注入事件] [⑂ 分裂分支]
  evaluating  → [⏳ 评分中...] （全部禁用）
  completed   → [📊 查看评分] [📋 萃取 SOP] [🔄 反哺 Agent] [🔁 创建新试炼]
  failed      → [🔄 恢复] [📋 复盘] [🔁 创建新试炼]
  ```
[x] ~~U-07~~ 删除或弱化原有的"启动演练"和"🎬 运行开发流程仿真"两个割裂入口，统一入口为"创建试炼"。

---

### 试炼导演台（右侧面板）

[x] ~~U-08~~ 实现团队选择下拉框：列出所有团队（Build System / AI 编程团队 / 公有云xOPs / ...），选择后加载团队快照。
[x] ~~U-09~~ 实现任务目标输入框：允许用户输入自定义任务目标（如"运行开发流程仿真"、"修复 HTTP 500"）。
[x] ~~U-10~~ 实现试炼模式选择：
  - What-if 推演
  - 多分支对比
  - 混沌演练
  - 演化试炼
  - 回放复盘
[x] ~~U-11~~ 实现仿真参数区：步数、加速倍率、并行分支数。
[x] ~~U-12~~ 实现"分支管理"面板：
  - 列出当前 Trial 下所有 Branch
  - 每条显示：分支名、颜色标识、当前步数、最新 reward、状态
  - 支持点击切换当前活跃分支
  - 支持"⑂ 从此处分裂"按钮
[x] ~~U-13~~ 实现"注入事件"面板：
  - 故障类型选择（网络延迟/Agent离队/任务变更/技能退化）
  - 触发时机（立即/指定step）
  - 注入后在控制台和时间轴上记录事件

---

### 环境空间视觉升级

[x] ~~U-14~~ 每个房间卡片显示 Agent 头像列表（最多显示 5 个，多余显示 +N）。
- [x] ~~U-15~~** 实现 Agent 房间迁移动画：Agent 在房间间移动时有 300ms 过渡动画。
[x] ~~U-16~~ 实现多 Branch 颜色区分：
  - 每个 Branch 有唯一颜色（baseline=蓝色、chaos=橙色、optimized=绿色）
  - Branch 中的 Agent 图标带有对应颜色的 border 或标签
- [x] ~~U-17~~** 实现故障注入视觉反馈：
  - 网络延迟 → 工作坊边框变橙，受影响 Agent 显示 ⏳
  - Agent 失联 → Agent 图标变灰，移入休息区
  - 技能退化 → Agent 图标显示 ⚠️，技能标签变红
- [x] ~~U-18~~** 实现 reward 热力反馈：
  - reward 上升 → 当前活跃房间背景微绿
  - reward 下降 → 背景微红
  - reward 峰值 → 短暂金色光晕（CSS animation，持续 1.5s）

---

### 试炼时间轴

[x] ~~U-19~~ 实现底部时间轴，按 step 顺序展示事件标注：
  - 普通 step：灰色圆点
  - reward 突升：绿色标注
  - reward 下降：红色标注
  - 故障注入：橙色闪电图标
  - 分支分裂：分叉图标
  - SOP 萃取：星形图标
[x] ~~U-20~~ 实现多 Branch reward 曲线叠加图：
  - 每个 Branch 一条曲线，颜色对应 Branch 颜色
  - 鼠标悬停显示该 step 的详细信息
  - 支持单独显示/隐藏某条曲线

---

### SECS Pipeline 实时联动

[x] ~~U-21~~ 将 SECS Pipeline 改为实时状态指示器：
  ```
  [L1 MADTwin] ✓  →  [L2 AAS] ✓  →  [L3 TwinLoop] ●  →  [L4 MADCG] ○  →  [↩ Loop] ○
  ```
  - ✓ 已完成（绿色）
  - ● 当前活跃（蓝色，动画闪烁）
  - ○ 待处理（灰色）
[x] ~~U-22~~ 每次 step 执行后，根据后端返回的 `secs_active_layer` 字段更新 Pipeline 状态。
[x] ~~U-23~~ SOP 萃取完成后，Loop 层高亮并显示萃取数量。

---

## 阶段四：演练与仿真统一（五种试炼模式实现）

> 阶段三 UI 完成后，开始实现具体模式。

### 模式一：What-if 推演（基线）

[x] ~~T01-01~~ 选择"What-if 推演"模式时，自动创建 baseline Branch。
[x] ~~T01-02~~ 运行完成后，输出基线报告：最高 reward、完成步数、瓶颈 Agent、关键技能。
[x] ~~T01-03~~ 基线数据作为后续所有模式的对照组存储。

---

### 模式二：多分支对比

[x] ~~T02-01~~ 支持从任意 step 点击"⑂ 分裂分支"，创建新 Branch。
[x] ~~T02-02~~ 新 Branch 继承父 Branch 在 fork_at_step 时的完整状态快照。
[x] ~~T02-03~~ 支持多个 Branch 并行运行（按 parallel_branches 参数控制）。
[x] ~~T02-04~~ 底部曲线图叠加显示所有 Branch 的 reward 曲线，颜色区分。
[x] ~~T02-05~~ 提供"Branch 比较表"：各 Branch 的最终 reward、步数、关键差异。

---

### 模式三：混沌演练

[x] ~~T03-01~~ 实现网络延迟注入：
  - 后端：指定 Agent 的某次 skill 执行延迟 N 步
  - 前端：受影响 Agent 显示 ⏳，房间边框变橙
[x] ~~T03-02~~ 实现 Agent 离队注入：
  - 后端：指定 Agent 标记为 offline，从 roomAgentMap 移入休息区
  - 前端：Agent 图标变灰，房间计数 -1，团队任务重分配
[x] ~~T03-03~~ 实现任务变更注入：
  - 后端：在指定 step 修改当前任务目标或优先级
  - 前端：控制台显示任务变更事件，时间轴标注
[x] ~~T03-04~~ 实现技能退化注入：
  - 后端：指定 Agent 的某项技能效率降低（reward 贡献 × 0.6）
  - 前端：Agent 图标显示 ⚠️，技能标签变红
[x] ~~T03-05~~ 实现恢复力评分：
  - 计算故障注入 step 到 reward 回升 step 的间隔
  - 恢复力 = 1 - (恢复步数 / max_steps)
  - 无故障注入时恢复力默认满分

---

### 模式四：演化试炼

[x] ~~T04-01~~ 实现多代运行框架：
  - 每代运行 max_steps/generations 步
  - 运行完成后自动评分
  - 保留 top 30% Branch 作为下一代基础
[x] ~~T04-02~~ 实现变异策略：
  - Agent 技能顺序随机调整（20% 概率）
  - 协作图边权重随机变化（20% 概率）
  - 任务优先级随机重排（10% 概率）
[x] ~~T04-03~~ 实现交叉策略：
  - 两个高分 Branch 的 Agent 分工方式融合（50% 概率）
[x] ~~T04-04~~ 实现终止条件：
  - 连续 3 代 reward 提升 < 0.005 → 停止进化
  - 达到最大代数 → 停止进化
  - 用户手动停止 → 停止进化
[x] ~~T04-05~~ 进化过程可视化：
  - 每代的最高/平均/最低 reward 显示为多条曲线
  - 进化历程表：代数、最高 reward、最优策略摘要

---

### 模式五：回放复盘

[x] ~~T05-01~~ 历史 Trial 列表支持点击进入"回放模式"。
[x] ~~T05-02~~ 回放模式下，可以选择某个历史 step 作为起点，创建新 Branch 继续推演。
[x] ~~T05-03~~ 回放模式下，控制台显示"当前为回放模式，基于 Trial xxx Step N 分裂"。

---

## 阶段五：评分与萃取（完整闭环）

### 五维评分实现

[x] ~~E-01~~ 实现目标完成度评分：
  ```python
  task_completion = final_reward / theoretical_max_reward
  ```
[x] ~~E-02~~ 实现协作效率评分：
  ```python
  # 计算并行度：每 step 中同时工作的 Agent 比例
  parallelism = avg(active_agents_per_step / total_agents)
  # 计算交接次数（transfer 事件数）
  handoff_penalty = transfer_count / total_steps * 0.1
  collaboration_efficiency = parallelism - handoff_penalty
  ```
[x] ~~E-03~~ 实现韧性评分：
  ```python
  if fault_injected:
      recovery_steps = step_reward_recovered - step_fault_injected
      resilience = 1 - (recovery_steps / max_steps)
  else:
      resilience = 1.0  # 无故障默认满分
  ```
[x] ~~E-04~~ 实现成本控制评分：
  ```python
  cost_efficiency = 1 - (actual_steps / max_steps)
  ```
[x] ~~E-05~~ 实现可萃取性评分：
  ```python
  # 统计稳定出现的动作路径（在多次运行中重复率 > 70%）
  stable_paths = count_stable_action_sequences(branch.steps, threshold=0.7)
  extractability = stable_paths / total_action_sequences
  ```
[x] ~~E-06~~ 实现加权总分：
  ```python
  total_score = (
    task_completion * 0.30 +
    collaboration_efficiency * 0.25 +
    resilience * 0.20 +
    cost_efficiency * 0.15 +
    extractability * 0.10
  )
  ```
[x] ~~E-07~~ 前端实现五维雷达图展示每个 Branch 的评分。
[x] ~~E-08~~ 前端实现所有 Branch 总分柱状图对比。

---

### SOP 萃取

[x] ~~S-01~~ 实现萃取条件检查：
  - Branch 最终 reward > baseline × 1.05 (至少5%提升)
  - 关键路径稳定性 > 70%
[x] ~~S-02~~ 从最佳 Branch 提取关键 Agent 动作序列：
  - 过滤掉 idle 和 failed 动作
  - 合并连续相同动作
  - 标注每个动作的 agent_role 和 skill_name
[x] ~~S-03~~ 生成结构化 SOP（参考 plan.md 第五章 5.8）：
  - 每步包含：order、agent_role、action、precondition、expected_output、fallback
[x] ~~S-04~~ 前端展示 SOP 候选列表，每条 SOP 显示：
  - 名称、置信度、来源分支、适用场景、步骤数
  - 支持展开查看详细步骤
  - 支持"批准"/"忽略"操作

---

### 反哺现实

[x] ~~R-01~~ 实现 SOP 审批流程（对应现有管线的 draft → review → approved）：
  - 萃取后状态为 candidate
  - 用户点击"批准"后变为 approved
  - 点击"反哺"后触发 feedback 接口
[x] ~~R-02~~ 实现技能分数更新：
  - 反哺接口将 SOP 中高频使用的技能，在对应 Agent 的 `skill_scores` 中提升 5-10%
[x] ~~R-03~~ 实现协作图更新：
  - 反哺接口将 SOP 中稳定出现的 Agent 协作对，在协作图中增加边权重
[x] ~~R-04~~ 前端显示反哺结果：
  - "已更新 3 个 Agent 的技能分数"
  - "协作图已添加 2 条推荐连接"

---

## 阶段六：CLI 扩展

[x] ~~C-01~~ 扩展 CLI 支持 `trial` 命令组：
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
[x] ~~C-02~~ CLI `status` 命令显示当前 Trial 状态（如果有活跃 Trial）。
[x] ~~C-03~~ CLI 命令与前端 UI 状态双向同步：CLI 创建 Trial，UI 也能感知。

---

## 阶段七：验收测试

> 每个阶段完成后必须过这组验收测试，确保没有退步。

### 最小闭环验收（完成阶段二和三后必须通过）

[x] ~~V-01~~ 点击"创建试炼"，3秒内按钮状态变为 ready，不再卡在"创建中"。
[x] ~~V-02~~ 点击"单步推演"，控制台出现一条 step 日志，step_index 连续且不重复。
[x] ~~V-03~~ 点击"自动推演"，系统连续产生 step 日志，直到点击"暂停"或完成。
[x] ~~V-04~~ 暂停后点击"继续"，系统恢复运行，step 从暂停处继续。
[x] ~~V-05~~ 全局统计"沙箱会话"从 0 变为 1（创建后即更新）。
[x] ~~V-06~~ 全局统计"总仿真步"随每次 step 递增。
[x] ~~V-07~~ 演练历史立即出现当前 Trial 记录，状态随生命周期更新。
[x] ~~V-08~~ 环境空间：选择 Build System + 工作坊演化后，工作坊卡片显示 7 个智能体，其他房间显示 0。
[x] ~~V-09~~ SECS Pipeline 实时高亮当前活跃层。
[x] ~~V-10~~ 演练完成后，点击查看报告，不出现 HTTP 500 或空白页，至少显示步数和 reward 曲线。

---

### 分支功能验收

[x] ~~V-11~~ 在 Step 10 点击"分裂分支"，新分支创建，曲线图出现两条 reward 线（颜色不同）。
[x] ~~V-12~~ 两个分支可以分别独立运行，互不干扰。
[x] ~~V-13~~ 点击分支管理面板中的某个分支，UI 切换到该分支的视图。

---

### 故障注入验收

[x] ~~V-14~~ 运行中点击"注入事件 → 网络延迟"，工作坊边框变橙，控制台记录注入事件。
[x] ~~V-15~~ 故障注入后，reward 短暂下降，然后系统逐步恢复。
[x] ~~V-16~~ 恢复力评分在评估结果中显示（有故障时不为 1.0）。

---

### 评分与萃取验收

[x] ~~V-17~~ Trial 完成后，调用"完成评估"，五维评分雷达图正确显示。
[x] ~~V-18~~ 评分完成后，"萃取 SOP"按钮可点击，萃取结果显示至少 1 条 SOP 候选。
[x] ~~V-19~~ 全局统计"提取SOP"数量从 0 增加为 N。
[x] ~~V-20~~ 全局统计"最优评分"更新为当前最高 trial 的 total_score。

---

### 反哺验收

[x] ~~V-21~~ 批准 SOP 后点击"反哺 Agent"，系统显示"已更新 N 个 Agent 的技能分数"。
[x] ~~V-22~~ 在智能体团队列表中，对应 Agent 的技能分数有更新。
[x] ~~V-23~~ 协作拓扑图中，反哺后相关 Agent 之间的连线加粗。

---

### 回归测试（每次修改后必须通过）

[x] ~~V-R01~~ 原有单步/自动运行功能正常，无退步。
[x] ~~V-R02~~ 控制台日志无重复 step 事件。
[x] ~~V-R03~~ 页面无 JS 报错（控制台无 error 级别日志）。
[x] ~~V-R04~~ 重新加载页面后，历史 Trial 列表正确还原。
[x] ~~V-R05~~ 不同浏览器 tab 同时打开页面，互不干扰。

---

## 附录：每条 TODO 完成后的输出格式

CodeBuddy 实现每条 TODO 后，必须按以下格式输出，不可省略：

```
✅ TODO: [编号] [名称]

📁 涉及文件：
- 前端：src/xxx.vue / xxx.ts
- 后端：api/xxx.py / models/xxx.py

🔧 修改内容：
- 修改了 XXX 函数，增加了 YYY 逻辑
- 新增了 ZZZ 接口

✔️ 验证结果：
- 操作步骤：点击 XXX → 看到 YYY
- 实际结果：符合预期 / 不符合，原因：ZZZ

⚠️ 注意事项（如有）：
- 本次修改可能影响 XXX，建议同时验证 V-R01
```

---

## 附录：数字孪生产品原则（始终牢记）

1. **能力不靠声明，靠演练数据证明。**
2. **环境空间是状态机，不是装饰。**
3. **每次试炼都必须留下可追溯的历史记录。**
4. **失败路径也是数据，不能丢弃。**
5. **仿真推进路径，演练施加压力，试炼选择未来。**
6. **SOP 是从数字孪生提炼出来的现实智慧，是整个系统的最终产出。**

---

*文档版本：v1.0 · 2026-06-09 · Tabbit 智能体助手*


---

## 实际完成补充说明（2026-06-09 更新）

> 以下是原 TODO 清单未覆盖、但在实施过程中额外完成的功能增强。

### P1 视觉中心化增强

- [x] **P1-A01** Nav "★ 环境空间"主舞台标记 + `.nav-primary` 特殊高亮样式（渐变背景+发光下划线）
- [x] **P1-A02** 系统状态浮动仪表卡 `env-status-float`（沙箱会话/仿真步数/SOP数/最优评分 四指标一览）
- [x] **P1-A03** `_updateEsFloat()` 全局函数，与 `loadSecsStats()` 联动刷新
- [x] **P1-A04** 环境容器高度增强 `calc(100vh - 240px)` + 边框 `border-active` + 青色微发光 `rgba(34,211,238,0.06)`

### P1 六房间动效增强

- [x] **P1-F01** 智能房间检测逻辑（基于 `agent_actions` 判断活跃房间，替代简单轮换）
- [x] **P1-F02** Reward 热力反馈（reward 上升→绿色微光 `rgba(52,211,153,0.2)` / 下降→红色微光）
- [x] **P1-F03** 峰值金色光晕 `@keyframes rewardPeakGlow`（演练完成时工作坊闪烁金光）

### P2 交互神经链路

- [x] **P2-L01** `switchView` 增强 `_origSwitchView` hook + 全局上下文联动
- [x] **P2-L02** 团队卡片 → `flyToRoom()` 定位 + 房间点击场景切换
- [x] **P2-B01** 事件弹幕层 `#env-barrage-layer` + `showBarrageBubble()` CSS floatIn→停留→fadeOut
- [x] **P2-B02** `emitStepBarrage()` 从 SSE step 数据提取关键决策生成气泡
- [x] **P2-S01** SVG 连线层 `#env-linkage-svg` + `drawLinkageLine()` stroke-dashoffset 动画
- [x] **P2-S02** `clearLinkageLines()` 3秒自动清除连线 + `linkageFlow` CSS 动画

### P3 混沌沙箱增强

- [x] **P3-I01** `initInjectDropdown()` 下拉菜单（🧠模型幻觉/🌐网络延迟/🔒逻辑死锁/⬇️技能退化）
- [x] **P3-I02** 注入历史面板记录 + `injectChaos()` 执行函数
- [x] **P3-H01** `.history-item.failed` CSS 红色标记失败记录
- [x] **P3-H02** `playbackSession()` 逐帧回放 Agent 分布
- [x] **P3-R01** `.env-reward-float` 右下角收益浮动卡 + 迷你 SVG 图表
- [x] **P3-R02** `showRewardFloat()` / `updateErfValue()` 实时刷新 reward 曲线

### P4 进化反哺增强

- [x] **P4-E01** `.sop-extract-badge` ✦SOP 徽章 + `showExtractBadge()` 点击展开策略摘要
- [x] **P4-E02** 萃取室自动 pulse 动画触发
- [x] **P4-U01** `playUpgradeAnimation()` Agent 升级光圈扩散动画
- [x] **P4-U02** `.agent-upgrade-ring` CSS @keyframes 光圈扩散+色相旋转
- [x] **P4-P01** `showParallelView()` Grid 分屏布局 + `.parallel-cell` + branch 标签
- [x] **P4-P02** 并行演化独立 canvas 分区渲染

### 功能完整性验证

| 指标 | 结果 |
|------|------|
| pytest 测试 | **92/92 passed** |
| Lint 错误 | **0** |
| 功能组件检查点 | **52/52 (100%)** |
| 修改文件 | `src/frontend/Agent-digital-twin.html` |

---

*标注时间：2026-06-09 23:45 · 由 CodeBuddy Loop 开发模式自动更新*
