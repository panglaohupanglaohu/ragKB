---
name: agent-digital-twin-button-level-refactor
overview: 将 Agent-digital-twin.html 从"可视化监控面板"重构为真正的"智能体进化实验室"。核心改造：混沌注入产生真实行为扰动、平行分支对比不同策略基因、达尔文棘轮锁定进化参数、SOP萃取生成可复用基因片段、TwinLoop实现现实↔模拟闭环。
todos:
  - id: evolve-models
    content: 扩展 AgentTwin/SimulationStep/SandboxSession 数据模型，为进化与混沌注入提供数据结构支撑
    status: pending
  - id: evolve-decision
    content: 改造 _default_decision() 感知 strategy_params，让不同策略分支真正行为分化
    status: pending
    dependencies:
      - evolve-models
  - id: evolve-evolutionary-loop
    content: 新增 _run_evolutionary() 方法，实现达尔文棘轮世代进化
    status: pending
    dependencies:
      - evolve-models
      - evolve-decision
  - id: evolve-chaos-injection
    content: 混沌注入真实扰动 Agent 池，支持故障下线/任务突变/资源耗尽
    status: pending
    dependencies:
      - evolve-models
  - id: evolve-sop-gene
    content: SOP 基因片段萃取后自动反哺到下一轮仿真作为种子技能
    status: pending
    dependencies:
      - evolve-evolutionary-loop
  - id: evolve-sse-events
    content: SSE 流扩展进化/混沌事件，前端实时捕获代际切换和注入结果
    status: pending
    dependencies:
      - evolve-evolutionary-loop
      - evolve-chaos-injection
  - id: evolve-frontend-lab
    content: 前端面板重构为进化实验台，展示适应度多线图/世代进度/分支对比/基因卡片/雷达图
    status: pending
    dependencies:
      - evolve-sse-events
      - evolve-sop-gene
---

## 产品定位

将 Agent-digital-twin.html 从"仿真看板"重构为"智能体进化实验室"——Agent 在数字孪生中以零代价试错、通过达尔文棘轮自我进化、产出可复用基因片段（SOP）反哺下一代。

## 核心功能

### 一、后端进化引擎实现（让 Agent 真正进化）

**1. 决策函数感知策略参数**

- 当前 `strategy_params`（collaboration_weight, exploration_rate）被设到 twin 上，但 `_default_decision()` 完全忽略它们，导致平行分支所有分支行为完全相同
- 改造 `_default_decision()` 读取 `twin.strategy_params`：
- collaboration_weight 高 → 提高 offer_help 概率，减少 claim_task 阈值
- exploration_rate 高 → 随机认领不匹配的任务，产生探索行为
- 结果：并行模式下5个分支真正产生行为差异

**2. 达尔文棘轮演化模式**

- 新增 `_run_evolutionary()` 方法，替代当前演化模式复用 sequential 的问题
- 世代循环（默认3代，每代 max_steps 步）：每代结束后评估→保留 top 50% Agent 的 strategy_params → 交叉变异产生下一代 → 只保留改进（棘轮效应）
- AgentTwin 新增 `strategy_weights` 字段用于跨代继承

**3. 混沌注入真实扰动**

- 当前 `inject_strategy()` 只标记 INJECTED 状态
- 改造为 `inject_chaos_event()`：
- agent_failure：将指定 twin 的 disabled=True，5步不可用，观察团队自愈
- task_mutation：随机修改 pending_tasks 中 50% 的任务 required_skills
- resource_depletion：降低 resource 可用性，迫使 agent 寻找替代方案
- `_execute_step_with_twins()` 支持跳过 disabled twins

**4. SOP 基因闭环

- `run_full_pipeline()` 结束后，若 best_sop 评分 > 0.4，自动将 SOP 作为 seed 注入 memory_pool
- `_spawn_twins()` 读取种子经验，赋予 twin 初始行为偏好
- 前端提供"将SOP注入下一轮"按钮

**5. 策略评估与建议结构化**

- `GlobalCritic._generate_recommendations()` 输出结构化参数而非纯文本
- 建议包含：`strategy_adjustments: {collaboration_weight: +0.1, exploration_rate: -0.05}`

### 二、前端进化实验台（看见 Agent 在进化）

**1. 适应度曲线升级**

- 从单线 reward 曲线改为多分支对比曲线（并行模式多条不同颜色折线）
- 演化模式显示代际对比：每代最佳适应度 vs 上一代

**2. 平行分支对比卡片**

- 并行仿真完成时，展示每个策略策略的得分/步数/特征标签
- 高亮最优分支，并标识"✅ 策略已采纳"

**3. 棘轮世代进度**

- 演化模式运行时，显示"第 N/5 代"进度条
- 每代结束后展示：保留 Agent 列表 + 策略权重变化 + 代际提升幅度

**4. SOP 基因卡片**

- 将 CollaborationSOP 的 steps 列表渲染为可折叠步骤卡片
- 支持"注入为种子技能"按钮，将 SOP 注入下一轮仿真

**5. 混沌注入面板升级**

- 实时显示 Agent 池状态（可用/禁用/自愈中）
- 注入故障时显示受影响 Agent 及预计恢复步数

**6. 报告增强**

- 分项评分 SVG 雷达图（5维度）
- 下载 JSON 结果 + 再次运行此配置 + 注入优化策略 → CLI 指令

### 三、基础交互修复（原计划的低优先级项）

- 运行时三态管理（在线/离线/加载中）
- 团队-场景全局联动（左侧卡片选团队同步右侧）
- 加速倍率滑块 1x-20x
- 启动按钮 disabled 状态管理
- 控制台流式输出确保

## 技术选型

- 前端：纯 HTML/CSS/JS，不引入框架，SVG 原生操作
- 后端：Python + FastAPI，复用现有 SECS 四维架构
- 实时通信：SSE (Server-Sent Events)，已有基础设施

## 实现方案

### 关键架构决策

**决策1：后端优先，前端跟进**
当前核心瓶颈在后端——演化模式、策略感知、混沌注入这些都没有真正实现。前端绘制的图表只是"空壳"。先让后端 Turing-complete，前端自然能展示进化过程。

**决策2：复用现有枚举和模型扩展，不另起炉灶**
SimulationMode.EVOLUTIONARY 已定义，AgentTwin 已有 strategy_params，CriticEvaluation 已有 recommendations。在现有骨架上生长，只增加必要字段。

**决策3：前端进化可视化分步渐进**
先实现适应度多线图和代际对比，再实现 SOP 卡片，最后是混沌面板。不一次追求完美，每步可独立验证。

### 数据结构扩展

**AgentTwin 新增字段：**

```
disabled: bool = False          # 混沌注入：是否被禁用
disabled_until_step: int = 0    # 自动恢复到哪一步
strategy_weights: Dict = {}     # 进化权重（跨代继承）
generation: int = 0             # 所属代数
```

**SimulationStep 新增字段：**

```
branch_id: int = 0              # 并行分支ID
generation: int = 0             # 演化代数
disabled_agents: List[str] = [] # 当前步被禁用的 Agent
```

**SandboxSession 新增字段：**

```
generation: int = 0             # 当前演化代数
max_generations: int = 5        # 最大演化代数
branches_results: List[Dict] = [] # 并行各分支完整结果
chaos_events: List[Dict] = []   # 注入的混沌事件记录
```

### 关键实现流程

**演化模式流程：**

```
run_evolutionary(session):
  for gen in range(max_generations):
    twins = spawn_or_mutate_twins(prev_best_twins)
    run_sequential_with_twins(twins)
    evaluation = critic.evaluate(gen_steps)
    best_twins = select_top_50_percent(twins, evaluation.agent_scores)
    if evaluation.global_score <= prev_best_score:
      break  # 棘轮：不再改进则停止
    prev_best_score = evaluation.global_score
    prev_best_twins = best_twins
```

**决策感知策略参数（_default_decision 改造）：**

```
if twin.strategy_params:
    collab = twin.strategy_params.get("collaboration_weight", 0.5)
    explore = twin.strategy_params.get("exploration_rate", 0.5)
    
    # exploration_rate 高 → 可能随机认领非匹配任务
    if explore > 0.5 and random.random() < explore - 0.5:
        return claim_random_task(twin, world)
    
    # collaboration_weight 高 → 增加 offer_help 概率
    if collab > 0.6 and random.random() < collab - 0.5:
        return offer_help_to_random_busy(twin, all_twins)
```

**混沌注入流程：**

```
inject_chaos_event(session, event_type, target_agent):
  if event_type == "agent_failure":
    twin.disabled = True
    twin.disabled_until_step = session.total_steps_executed + 5
    # 其他 agent 可能通过 offer_help 接管该 agent 的任务
    
  if event_type == "task_mutation":
    for task in sim_state.pending_tasks:
      if random.random() < 0.5:
        # 随机修改 required_skills
        task["required_skills"] = random.sample(all_skills, len(task["required_skills"]))
```

### 前端适应度多线图实现

```
function _updateFitnessChart(branchesData):
  // branchesData = [{label: "激进", color: "#...", rewards: [0.1, 0.2, ...]}, ...]
  const svg = SVG element with multiple <polyline> elements
  每条折线不同颜色 + stroke-dasharray 样式区分
  X轴=步数, Y轴=适应度
  底部图例标注各分支名称
```

### 前端棘轮世代进度实现

```
渲染一个横向进度条：
[Gen 1 ✓ 0.452] → [Gen 2 ✓ 0.523] → [Gen 3 ▶ 运行中...] → [Gen 4] → [Gen 5]
每代显示最高适应度得分，当前代高亮动画
```

## 目录结构

```
src/backend/sandbox/
├── twin_loop.py           # [MODIFY] 核心改造文件
│   ├── _run_evolutionary()  # [NEW] 演化模式实现（~80行）
│   ├── _default_decision()  # [MODIFY] 感知 strategy_params（~30行修改）
│   ├── _execute_step_with_twins() # [MODIFY] 支持 disabled_twins（~10行修改）
│   ├── inject_chaos_event() # [NEW] 混沌注入实现（~60行）
│   └── _mutate_strategy()   # [NEW] 策略变异函数（~30行）
├── models.py              # [MODIFY] AgentTwin/SimulationStep/SandboxSession 扩展
├── orchestrator.py        # [MODIFY] run_full_pipeline 支持演化+注入
├── strategy_aligner.py    # [MODIFY] 批量平行分支对齐
├── global_critic.py       # [MODIFY] 结构化 recommendations
├── zero_exp_engine.py     # [MODIFY] SOP 基因注入 memory_pool
└── api.py                 # [MODIFY] SSE 事件扩展：branch_result/chaos_event/generation

src/frontend/
├── Agent-digital-twin.html  # [MODIFY] 前端进化实验台
│   ├── SECS面板HTML结构     # [MODIFY] 新增演化进度条+分支对比卡片+混沌面板
│   ├── 内联CSS              # [MODIFY] 新增多线图/雷达图/进度条/基因卡片样式
│   └── 内联JS (~400行新增)  # [MODIFY] 适应度多线图+平行分支对比+棘轮进度+报告雷达图+混沌注入面板
```

## 实施要点

**性能注意：**

- 演化模式多代仿真，SSE 流中增加 `generation` 字段，前端按代分组显示
- 平行分支最多5个，每个分支步骤共享同一次 SSE 连接
- 适应度多线图使用 `<polyline>` 而非 Canvas，减少重绘开销

**向后兼容：**

- 新增字段均为 optional，不影响已有 what-if 和 parallel 模式的现有行为
- 前端通过检查 `session.mode === 'evolutionary'` 决定是否显示进化 UI

**日志与调试：**

- 每个代际切换时 `_logConsole('══ 第N代完成，保留X个Agent ══', 'header')`
- 混沌注入事件在控制台用红色 `err` 级别输出，确保可见
- SSE 事件新增 `type: 'generation_start'` / `type: 'chaos_injected'` 前端实时捕获