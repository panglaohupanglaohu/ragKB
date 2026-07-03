---
name: agent-digital-twin-button-level-refactor
overview: 按 P0→P3 四阶段递进改造数字孪生系统：P0 修复地基让孪生可观测可控，P1 构建混沌试错引擎让 Agent 在沙箱中犯错，P2 实现达尔文棘轮进化引擎让 Agent 只进不退，P3 强化可视化与持久化让进化看得见留得住。
todos:
  - id: p0-runtime-state
    content: P0-1 运行时状态机重构：实现 connecting/online/offline/error 四态，离线可点击重连，移除 [object Object] 脏输出
    status: completed
  - id: p0-selfcheck-sync
    content: P0-2 自检按钮 CLI 逐行诊断流（数据源/仿真引擎/渲染器/存储）+ 刷新按钮强制 world/sync
    status: completed
    dependencies:
      - p0-runtime-state
  - id: p0-step-timeline
    content: P0-3 后端 step 间加入 await sleep(baseInterval/rate) 延迟 + 前端速度滑块读取，让过程肉眼可见
    status: completed
  - id: p0-report-fix
    content: P0-4 报告链路修复：历史记录完整持久化 + 分项评分渲染为 SVG 柱状图 + 报告图标按 id 取回数据
    status: completed
  - id: p1-chaos-injection
    content: P1-1 混沌注入激活：故障下线Agent/任务突变/智能体离开真实扰动沙箱，收益曲线可见波动
    status: completed
    dependencies:
      - p0-step-timeline
  - id: p1-triple-link
    content: P1-2 团队-环境-配置三向联动：左侧卡片同步右侧选择器+环境空间Fly-to，场景选中触发布局重置
    status: completed
  - id: p1-parallel-branches
    content: P1-3 What-if 平行分支：并行3分支各持不同 strategy_params，收益曲线三条线对比
    status: completed
    dependencies:
      - p0-step-timeline
  - id: p1-failure-attribution
    content: P1-4 失败归因：Agent 崩溃/超时如实记录 failed，报告增加失败归因板块
    status: completed
    dependencies:
      - p1-chaos-injection
  - id: p2-evolutionary-loop
    content: P2-1 达尔文棘轮：evolutionary 模式每代适应度驱动变异，保留高分个体，评分只进不退
    status: completed
    dependencies:
      - p1-parallel-branches
  - id: p2-sop-extraction
    content: P2-2 SOP 萃取固化：最优交互序列萃取为结构化 SOP 对象（步骤+触发条件+预期收益）
    status: completed
    dependencies:
      - p2-evolutionary-loop
  - id: p2-strategy-feedback
    content: P2-3 进化反哺：报告底部 [注入优化策略] 将 SOP 写回 Agent 初始配置，下一轮自动加载
    status: completed
    dependencies:
      - p2-sop-extraction
  - id: p2-twinloop-switch
    content: P2-4 TwinLoop 回环开关：L3 节点成为真实开关，自动模拟-评估-变异-再模拟连续迭代
    status: completed
    dependencies:
      - p2-evolutionary-loop
  - id: p3-visual-persist
    content: P3 可视化与持久化：3D空间实时移动 + 速度滑块 + 单步调试 + IndexedDB 结果持久化
    status: completed
    dependencies:
      - p2-twinloop-switch
---

## 产品定位

将 Agent-digital-twin.html 从静态仿真看板重构为真正的智能体进化实验室。核心原则：让 Agent 在场景里能犯错、能感知后果、能在下一步改变自己。

## 四阶段目标

### P0 - 修复地基：可观测、可控制

- **运行时状态机**：connecting → online / offline / error 三态，离线可点击重连，移除 `[object Object]` 脏输出
- **自检/刷新按钮**：自检在CLI逐行打印诊断流（数据源/仿真引擎/渲染器/本地存储），异常项给出可执行修复指令；刷新调用 `/api/v1/sandbox/world/sync` 强制同步
- **演练步进时间轴**：后端 step 间加入 `await sleep(baseInterval / rate)`，让过程肉眼可见
- **报告链路修复**：历史记录完整持久化、报告图标按ID取回数据、分项评分用雷达图/柱状图呈现

### P1 - 试错引擎：混沌沙箱

- **混沌注入激活**：故障注入真实下线Agent（如Architect不可用5步）、任务变更随机修改需求向量、智能体离开动态缩减Agent池
- **三向联动**：左侧团队卡片→同步右侧选择器+环境空间预设；场景选择→布局重置+Agent房间分配
- **What-if平行分支**：并行分支:3 各持不同策略参数（激进/保守/均衡），收益曲线三条线对比
- **失败也是结果**：Agent崩溃/超时/死锁如实记录为 failed，报告增加失败归因板块

### P2 - 进化引擎：达尔文棘轮

- **适应度驱动策略变异**：evolutionary模式每代基于收益曲线作为适应度函数，保留高分个体，棘轮效应只进不退
- **SOP萃取固化**：最优交互序列萃取为结构化SOP对象（步骤+触发条件+预期收益），SOP计数不再恒为0
- **进化反哺**：报告底部 [⬆ 注入优化策略] 将SOP写回Agent初始配置，下一轮自动加载进化后策略
- **TwinLoop回环开关**：L3节点成为真实开关，开启后自动模拟→评估→变异→再模拟连续迭代

### P3 - 可视化与持久化

- 3D环境空间Agent节点真实移动、连线随交互频次动态变粗
- 加速倍率实时滑块拖动即时改变演练速度
- 新增单步调试按钮逐步观察决策变化
- IndexedDB持久化演练结果与进化轨迹，刷新不丢失

## 技术方案

### P0-1 运行时状态机重构

**现状**：`loadRuntimeStatus()` 行886-895，仅成功/失败两分支，标签硬编码"加载中"。

**改造**：新增 `_runtimeState = { status: 'connecting'|'online'|'offline'|'error', retryCount: 0 }`：

- `connecting`：显示 spinner + "连接中..."
- `online`：绿色圆点 + "{mode} - 在线"
- `offline`：黄色圆点 + "离线"（可点击），点击触发重连
- `error`：红色圆点 + 错误信息
- 新增 `_autoPollRuntime()`：`online` 后每30秒自动检测，异常时降级为 `offline` 并启动5秒重试定时器

**文件**：`Agent-digital-twin.html` 内联JS，修改 `loadRuntimeStatus()` 函数

### P0-2 自检/刷新按钮

**自检诊断流**：`runRuntimeSelfCheck()` 改用 `async/await` 逐步输出：

```
step1: await fetch(SECS+'/runtime-status') ← 数据源
step2: await fetch(SECS+'/stats') ← 仿真引擎
step3: document.getElementById('env-3d-canvas') ← 渲染器
step4: localStorage可用性检测 ← 本地存储
```

每步 `_logConsole()` 输出结果，异常时输出 `<span class="cmd">fix --xxx</span>`。

**刷新同步**：新增 `forceSyncWorld()`，调用 `POST /api/v1/sandbox/world/sync`，成功后刷新 stats+history+agent-list。

### P0-3 演练步进时间轴

**后端改造**（`twin_loop.py`）：

- `_run_sequential()` 和 `_run_parallel()` 的 step 循环中加入：

```python
if speed_factor > 0:
    base_interval = 0.1  # 基础100ms
    await asyncio.sleep(base_interval / speed_factor)
```

- speed_factor 通过 session 参数传入

**前端**：`sexyCreateAndRun()` 行1268 将 `var speed = 10` 改为读取滑块值 `var speed = parseInt(document.getElementById('secs-speed-slider').value) || 10`

### P0-4 报告链路修复

**问题1**：`_populateScorePanel()` 行1582 在 evaluation 为 number 时无 breakdown。修复：后端 `run_full_pipeline()` 确保 evaluation 为对象 `{global_score, breakdown: {task_completion, communication, resource, ...}}`；前端 `_populateScorePanel()` 用 breakdown 生成 SVG 柱状图。

**问题2**：历史记录点击报告图标。现有 `loadExerciseHistory()` 行1807-1834 点击整体行调用 `openSimReport(sessionId)`，正确。但需确保 `openSimReport()` 始终 fetch 最新数据（当前已有，行1635-1651）。

**增强**：`_secsShowReport()` 中，将分项评分渲染为内联 SVG 柱状图（5根柱：任务完成/通信效率/资源利用/冲突避免/收敛速度），替代文字列表。

### P1-1 混沌注入激活

**后端改造**（`twin_loop.py`）：

- 新增 `chaos_state = {}` 字典，session 级别持久化
- `inject_chaos_event(session_id, event_type, payload)`:
- `agent_failure`：`chaos_state["disabled_agents"] = {agent_id: disabled_until_step}`
- `task_mutation`：`chaos_state["mutated_tasks"] = True`，随机修改 pending_tasks 的 required_skills
- `agent_leave`：从 twins 列表移除指定 agent
- `_execute_step_with_twins()` 检查 `chaos_state["disabled_agents"]`，跳过禁用 agents
- `_calculate_reward()` 感知 `chaos_state`，注入后步的奖励降低 0.1~0.3

**前端**：注入按钮 `_doInjectEvent()` 行1713-1740 保持现有逻辑，新增视觉反馈——`_logConsole('⚠️ 混沌注入: Architect 下线, 预计5步后恢复', 'warn')`

### P1-2 三向联动

**前端改造**：

- 左侧团队卡片点击（`digital-twin-cli.js` 中 `toggleTeam()`）→ 在回调中调用 `sexySelectTeam(teamId, teamName)` 和 `_executeSceneScript(sceneId)`
- 场景选择 `sexySelectScene()` 行1154-1181 已在调用 `_executeSceneScript(sceneId)`，增强为同时调用 `switchRoom(focusRoom)`
- 新增 `_updateLaunchButton()`：`_selectedTeamId && _selectedSceneId` 时才启用「启动演练」按钮

### P1-3 What-if 平行分支

**后端改造**（`twin_loop.py`）：

- `_run_parallel()` 的每个分支注入不同 `strategy_params`：
- branch 0: `{collaboration_weight: 0.8, exploration_rate: 0.4, label: '激进协作'}`
- branch 1: `{collaboration_weight: 0.5, exploration_rate: 0.5, label: '均衡'}`
- branch 2: `{collaboration_weight: 0.2, exploration_rate: 0.3, label: '保守审查'}`
- `_default_decision()` 读取 `twin.strategy_params` 影响动作选择

**前端**：`_finalizeSimFromSession()` 中，若 `branches_results` 存在，绘制多线适应度图（`_updateFitnessChart(branches)`），每分支不同颜色 `<polyline>`。

### P1-4 失败归因

**后端**：`_calculate_reward()` 返回 `{reward, failed: bool, fail_reason: str}`。Agent 连续3步 reward < 0 标记为 failed。`_run_sequential()` 结束后统计 failed agents。

**前端**：`_secsShowReport()` 中若 `session.evaluation.failed_agents` 存在，渲染失败归因表格：Agent名 / 失败步 / 原因 / 后续恢复状态。

### P2-1 达尔文棘轮

**后端新方法** `_run_evolutionary(session)`：

```python
for gen in range(max_generations):
    twins = spawn_or_mutate(prev_best_twins, generation=gen)
    steps = await _run_sequential_with_twins(twins)
    scores = evaluate_twins(twins, steps)
    best_twins = select_top_50_percent(twins, scores)
    if gen_score <= prev_best_score: break  # 棘轮
    prev_best_score = gen_score
```

- `_mutate_strategy(twin)`：对 strategy_weights 做 ±0.05 随机扰动

### P2-2 SOP萃取

**后端**：`run_full_pipeline()` 结束后，若 `best_sop.avg_reward > 0.4`，序列化 SOP 为 `{steps, trigger_conditions, expected_reward, source_generation}`。写入 session 的 `sops_extracted` 列表。

**前端**：SOP 标签页 (`sub-sop`) 渲染 SOP 卡片：步骤列表 + 触发条件 + 预期收益值。

### P2-3 进化反哺

**前端**：报告底部新增按钮 `⬆ 注入优化策略`，onclick 调用：

1. 获取 `session.best_sop`
2. 调用 `POST /api/v1/sandbox/sessions/{new_id}/inject` 将 SOP 作为 seed_skill 注入
3. 同时自动填入 CLI 命令：`pipeline apply --sop {sop_id}`

### P2-4 TwinLoop回环

**前端**：L3 节点 `onclick="toggleTwinLoop()"`:

- 开启：显示 spinner，自动调用 `sexyCreateAndRun(evolutionary_mode=True)`
- 运行中节点高亮动画（CSS pulse）
- 每代完成 SSE 事件 `type: 'generation_complete'` 更新进度

**后端**：`/api/v1/sandbox/sessions/{id}/run` 支持 `twin_loop: true` 参数，循环调用 `_run_evolutionary()` 直到收敛。

### P3-1~P3-4

- **3D移动**：在 `_handleSSEMessage()` step 事件中调用 `sw3dOnStep(agent_positions)`
- **速度滑块**：HTML 新增 `<input type="range" id="secs-speed-slider" min="1" max="20" value="10">`
- **单步调试**：新增 `sexyStepOnce()` 函数，调用 `POST /sessions/{id}/step` 执行单步
- **IndexedDB**：`_saveToIndexedDB(session)` / `_loadFromIndexedDB(sessionId)` 封装

## 目录结构

```
src/backend/sandbox/
├── twin_loop.py           # [MODIFY] 核心改造
│   ├── _run_evolutionary()        # [NEW] 达尔文棘轮世代进化 (~60行)
│   ├── _run_sequential()          # [MODIFY] 加入步间延迟 (~5行)
│   ├── _run_parallel()            # [MODIFY] 注入分支策略参数 (~15行)
│   ├── _default_decision()        # [MODIFY] 感知 strategy_params (~20行)
│   ├── _calculate_reward()        # [MODIFY] 返回失败标记 (~10行)
│   ├── inject_chaos_event()       # [NEW] 混沌注入扰动 (~50行)
│   ├── _mutate_strategy()         # [NEW] 策略变异 (~25行)
│   └── _spawn_twins_with_genes()  # [NEW] 种子技能注入 (~20行)
├── models.py              # [MODIFY] AgentTwin新增 disabled/disabled_until/generation/strategy_weights
├── orchestrator.py        # [MODIFY] run_full_pipeline 支持 evolutionary/twin_loop 模式
└── api.py                 # [MODIFY] SSE新增 generation_start/generation_complete/chaos_injected 事件

src/frontend/
└── Agent-digital-twin.html  # [MODIFY] 主要前端改造
    ├── HTML结构新增：速度滑块(行627附近)、单步按钮(行643附近)
    ├── CSS新增：状态机样式(.runtime-offline/.runtime-error)、柱状图样式、世代进度条
    └── JS新增/修改：状态机(~50行)、自检诊断(~40行)、三向联动(~30行)、
        多线适应度图(~40行)、失败归因渲染(~25行)、SOP卡片(~30行)、
        进化反哺按钮(~15行)、TwinLoop开关(~25行)、IndexedDB封装(~40行)
```