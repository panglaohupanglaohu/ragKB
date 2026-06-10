# Agent 数字孪生 — 按钮级功能 TODO（代码对齐版）
# AgentsGroup2026 Digital Twin — Button-Level TODO (Code-Grounded)

> 版本：v3.0 · 日期：2026-06-10
> 配套文档：`Agent数字孪生优化plan.md`（v3.0）
> 主页面：`src/frontend/Agent-digital-twin.html`
> 关联脚本：`src/frontend/js/digital-twin-cli.js`
> 目标：把"做完了却还在报错"变成"可验证完成"

---

## 0. 状态完整性规则（先看这个）

### 0.1 `[x]` 的唯一合法条件（四门齐过）

某条任务只能标 `[x]`，当且仅当同时满足：

1. **函数存在门**：`grep` 能查到真实函数定义（含文件+行号）。
2. **接口通路门**：点击后网络请求命中目标端点，返回 2xx。
3. **状态一致门**：关键状态字段按预期变化（以 `_sx` 为准）。
4. **手工 UI 门**：按验收步骤操作，界面可见结果正确。

任一门失败：
- 可运行但有明显缺陷/风险 → `[~]`
- 不可运行或逻辑错误 → `[ ]`

### 0.2 本版状态语义

- `[x]` 已通过四门
- `[~]` 已实现主通路，但存在明确 bug/风险
- `[ ]` 未实现、不可用或关键逻辑错误

### 0.3 单一数据源约束

当前代码还未完成收敛，仍是 `_DTS` + `_sx` + `window._currentSessionId` 三套并存。

本 TODO 的执行目标是：

1. `_sx` 成为唯一真实存储
2. `_DTS` 与 `window._currentSessionId` 仅作别名/兼容层
3. 环境空间位置统一到 `_sx.roomAgentMap`（由 `S.positions` 迁移）

---

## 1. 已核实函数/端点对照（作为所有按钮任务的事实基线）

> 下表来自对 `Agent-digital-twin.html` 的实际 `grep + read`，替代旧文档中的不准确信息。

| 函数 | 行号（约） | 当前状态 | 端点 |
|---|---|---|---|
| `createTrial` | 3267 | `[x]` | `POST /api/v1/twin-trials` |
| `stepOnce` | 3268 | `[x]` | `POST /api/v1/sandbox/sessions/{sid}/step` |
| `autoRun` | 3269 | `[x]` | 委托 `sexyAutoRun` → `/run` |
| `pauseSim` | 3270 | `[x]` | `POST /api/v1/sandbox/sessions/{sid}/pause` |
| `terminate` | 3271 | `[x]` | `sexyStopSim` + `/stop` |
| `forkBranch` | 3283 | `[~]` | `POST /api/v1/twin-trials/{tid}/branches` |
| `showInjectDropdown` | 3284 | `[x]` | 前端切换（BUG-A 已修复） |
| `doInjectEvent` | 3285 | `[~]` | `POST /api/v1/twin-trials/{tid}/branches/{bid}/events` |
| `evaluateTrial` | 3286 | `[x]` | `POST /api/v1/twin-trials/{tid}/evaluate` |
| `extractSop` | 3287 | `[x]` | `POST /api/v1/twin-trials/{tid}/extract-sop` |
| `feedbackAgents` | 3288 | `[x]` | `POST /api/v1/twin-trials/{tid}/feedback`（BUG-D 已修复） |
| `viewReport` | 3289 | `[x]` | 前端调用 `evaluateTrial`（BUG-C 已修复） |
| `resetForNew` | 3290 | `[x]` | 前端重置 |
| `selectMode` | 3291 | `[x]` | 前端模式高亮 |
| `showBranchManager` | 3293 | `[x]` | `GET /api/v1/twin-trials/{tid}/branches`（BUG-B 已修复） |
| `transitionTrialStatus` | 3314 | `[x]` | 前端状态机 |
| `handleTrialEvent` | 3333 | `[x]` | 前端事件日志 |
| `_updateButtonStates` | 3353 | `[x]` | 前端按钮组渲染 |

---

## 2. P0 — 状态收敛（必须先做）

> 目标：把三套状态收敛为 `_sx` 单源，避免按钮状态和内部状态再次分裂。

### P0-01 统一 sessionId 单源

- 状态：`[x]` ← P0 已完成
- 位置：`Agent-digital-twin.html` 全局
- 现状：`_sx.sessionId`、`window._currentSessionId` 并存。
- 要做：
  1. 将 `window._currentSessionId` 改为 `_sx.sessionId` 的 getter/setter 别名。 ✅
  2. 新代码禁止直接写 `window._currentSessionId = ...`（过渡期保留旧写法，但底层落 `_sx.sessionId`）。 ✅
- 验收：
  1. 创建试炼后，`_sx.sessionId` 与 `window._currentSessionId` 完全一致。
  2. `step/run/pause/stop` 读取同一值。

### P0-02 统一试炼/分支 id 单源

- 状态：`[x]` ← P0 已完成
- 现状：`_DTS.activeTrialId/activeBranchId` 与 `_sx` 未统一。
- 要做：
  1. 新增 `_sx.trialId`、`_sx.branchId`。
  2. `_DTS.activeTrialId/activeBranchId` 改为别名。
- 验收：
  1. `createTrial` 后 `_sx.trialId/_sx.branchId` 有值。
  2. `forkBranch` 后 `_sx.branchId` 可切换。

### P0-03 统一 step 单源

- 状态：`[x]` ← P0 已完成
- 现状：`_sx.steps`、`_DTS.currentStep`、后端 step 返回混用。
- 要做：
  1. 统一为 `_sx.currentStep`。 ✅
  2. 仅从 step 响应 / SSE 写入；禁止前端自增。 ✅
- 验收：
  1. 单步后 `_sx.currentStep == step_index`。
  2. 自动运行期间 step 单调递增且不重复。

### P0-04 统一运行态单源

- 状态：`[x]` ← P0 已完成
- 现状：`_DTS.trialStatus`、`_sx.simRunning`、`_paused` 并存。
- 要做：
  1. `_sx.status` 作为唯一状态机。 ✅
  2. `simRunning/_paused` 由 `_sx.status` 派生。 ✅（_DTS.trialStatus 已别名到 _sx.status）
- 验收：
  1. 任意时刻按钮组与 `_sx.status` 一致。
  2. 不再出现"按钮暂停，内部还在跑"。

### P0-05 环境空间位置单源（迁移项）

- 状态：`[ ]`
- 现状：真实代码使用 `S.positions`，旧文档虚构了 `roomAgentMap`。
- 要做：
  1. 在 `_sx` 新增 `roomAgentMap`。
  2. 从 `S.positions` 迁移并保持兼容映射。
- 验收：
  1. 空间标题、房间卡片、Agent 列表均读同一源。
  2. 修复"标题 28 / 卡片 0"类错位。

---

## 3. P1 — 核心运行闭环（创建→运行→暂停→终止→完成）

### P1-01 `createTrial` 创建试炼

- 状态：`[x]`
- 函数：`createTrial`（L3267）
- 端点：`POST /api/v1/twin-trials`
- 已验证行为：
  1. 未选团队时 toast 警告并回退 `creating→idle`。
  2. 有 15 秒 `AbortController` 超时保护。
  3. 成功后写 trial_id / branch_id / session_id。

### P1-02 `stepOnce` 单步推演

- 状态：`[x]` ← 已完成
- 函数：`stepOnce`（L3268）
- 端点：`POST /api/v1/sandbox/sessions/{sid}/step`
- 已完成：已补齐 `_sx.currentStep` 同步（P0-03）。

### P1-03 `autoRun` 自动推演

- 状态：`[x]`
- 函数：`autoRun`（L3269）+ `sexyAutoRun`（约 L1840）
- 端点：`POST /api/v1/sandbox/sessions/{sid}/run`
- 已验证行为：
  1. `ready/paused` 可进入 `running`。
  2. 运行结束桥接 `transitionTrialStatus('running','completed')`。

### P1-04 `pauseSim` 暂停

- 状态：`[x]`
- 函数：`pauseSim`（L3270）
- 端点：`POST /api/v1/sandbox/sessions/{sid}/pause`
- 已验证行为：暂停后状态转 `running→paused`。

### P1-05 `terminate` 终止

- 状态：`[x]`
- 函数：`terminate`（L3271）
- 端点：`POST /api/v1/sandbox/sessions/{sid}/stop`
- 已验证行为：
  1. 中止导演台 abortController。
  2. 调用 `sexyStopSim` 同步清理。
  3. 转 `terminated`。

### P1-06 状态机按钮渲染 `_updateButtonStates`

- 状态：`[x]`
- 函数：`_updateButtonStates`（L3353）
- 已验证行为：根据状态渲染不同按钮组。
- 备注：`terminated` 未单独定义按钮组，回退 `idle` 可接受，后续可补显式组。

---

## 4. P2 — 演练注入闭环（故障注入 + 恢复力）

### P2-01 注入面板展开 `showInjectDropdown`

- 状态：`[x]` ← 已完成
- 函数：`showInjectDropdown`（L3284）
- 问题：BUG-A 已修复。
- 验收：
  1. `ready` 点 `💥 注入` 能展开。
  2. 再点一次能收起。

### P2-02 六类故障注入 `doInjectEvent`

- 状态：`[~]`
- 函数：`doInjectEvent`（L3285）
- 端点：`POST /api/v1/twin-trials/{tid}/branches/{bid}/events`
- 已接线事件：
  1. `network_delay`
  2. `agent_leave`
  3. `task_change`
  4. `skill_degraded`
  5. `model_hallucination`
  6. `logic_deadlock`
- 风险：`activeTrialId/activeBranchId` 为空时直接 return（用户无反馈）。
- 完成标准：空 id 时 toast；成功时写入注入历史。

### P2-03 注入历史面板

- 状态：`[ ]`
- 要做：增加 `inject-history` 区块，记录时间、event_type、branch、step。
- 验收：连续注入 3 次，列表新增 3 条。

### P2-04 韧性评分联动

- 状态：`[ ]`
- 端点：`POST /api/v1/twin-trials/{tid}/evaluate`
- 要做：评分结果中 `resilience` 与故障恢复步数联动展示。
- 验收：有故障注入与无故障注入的 resilience 可区分。

---

## 5. P3 — 环境空间（主舞台）

### P3-01 视图切换 `switchEnvMode`

- 状态：`[x]`
- 文件：`digital-twin-cli.js` L1112
- 验收：平面/网格切换成功，不丢当前房间上下文。

### P3-02 创建空间 `createRoom`

- 状态：`[x]`
- 文件：`digital-twin-cli.js` L383
- 验收：输入名称后新增房间并持久化。

### P3-03 统一房间人数数据源

- 状态：`[ ]`
- 现状：`S.positions` 驱动，且多个显示位存在潜在多源读取。
- 要做：迁移到 `_sx.roomAgentMap` 单源（P0-05 依赖）。
- 验收：标题、卡片、Agent 列表显示一致。

### P3-04 Reward 热力反馈

- 状态：`[ ]`
- 要做：reward 上升房间微绿，下降微红，峰值金色光晕。
- 验收：自动运行中可观察颜色变化。

### P3-05 Agent 迁移动画

- 状态：`[ ]`
- 要做：房间变更时 300ms ease 过渡。
- 验收：如 `agent_leave` 注入后，工作坊减少，休息区增加，动画可见。

---

## 6. P4 — 分支 / 报告 / SOP / 反哺闭环

### P4-01 分支列表 `showBranchManager`

- 状态：`[x]` ← 已完成
- 函数：`showBranchManager`（L3293）
- 端点：`GET /api/v1/twin-trials/{tid}/branches`
- 问题：BUG-B 已修复（补了 `await`）。
- 修复后验收：
  1. 创建试炼后能显示 baseline 分支。
  2. 分裂后出现新分支条目。

### P4-02 分裂分支 `forkBranch`

- 状态：`[~]`
- 函数：`forkBranch`（L3283）
- 端点：`POST /api/v1/twin-trials/{tid}/branches`
- 现状：请求已发出；但分裂后视图切换功能弱。
- 完成标准：
  1. `switchBranch` 切换后刷新曲线/事件/状态。
  2. 可见多分支差异。

### P4-03 查看评分 `viewReport`

- 状态：`[x]` ← 已完成
- 函数：`viewReport`（L3289）
- 问题：BUG-C 已修复，直接调用 `evaluateTrial()`。
- 验收：点 `📊 评分` 必定触发评估并渲染图表。

### P4-04 SOP 提取 `extractSop`

- 状态：`[x]`
- 函数：`extractSop`（L3287）
- 端点：`POST /api/v1/twin-trials/{tid}/extract-sop`
- 验收：`#sop-list-area` 渲染候选列表或"暂无SOP"。

### P4-05 反哺 `feedbackAgents`

- 状态：`[x]` ← 已完成
- 函数：`feedbackAgents`（L3288）
- 端点：`POST /api/v1/twin-trials/{tid}/feedback`
- 问题：BUG-D 已修复，改为 toast + 日志。
- 完成标准：改为 toast + 结果写日志区。

---

## 7. P5 — 后端持久化（新增阶段，已决策）

> 目标：试炼数据从内存落地到 `storage/trials/`，避免重启丢失。

### P5-01 新建 `TrialStore`

- 状态：`[ ]`
- 新文件：`src/backend/sandbox/trial_store.py`
- 要求：严格复用 `src/backend/agents/audit_store.py` 模式
  1. `STORAGE_DIR = ... / storage / trials`
  2. `asyncio.Lock`
  3. `.tmp` 原子写 + `.bak` 备份
  4. 主文件损坏时从备份自愈

### P5-02 `trial_api.py` 替换内存 dict

- 状态：`[ ]`
- 位置：`_trials/_branches/_trial_events`（L32-34）
- 要做：改由 `TrialStore` 读写。

### P5-03 变更后即保存

- 状态：`[ ]`
- 触发点：create / fork / step / evaluate / extract-sop / feedback
- 验收：任一动作后，`storage/trials/*.json` 更新时间变化。

### P5-04 `evaluate` 状态保护

- 状态：`[ ]`
- 位置：`trial_api.py` L571
- 要做：try-finally，确保异常时不锁死 `EVALUATING`。

### P5-05 时间戳写法去 hack

- 状态：`[ ]`
- 位置：`trial_api.py` L404/L725
- 要做：把 `Trial.__dataclass_fields__["updated_at"].default_factory()` 改为 `datetime.now(timezone.utc).isoformat()`。

---

## 8. P6 — 次要面板与补完

### P6-01 导航子面板功能齐全

- 状态：`[~]`
- 范围：系统状态（仪表盘/拓扑）、交互流（过滤器/时间线/序列图）
- 验收：每个按钮切换后有真实数据变化，不是空壳。

### P6-02 CLI 快捷命令

- 状态：`[~]`
- 范围：`status/agents/skills/rooms/pipeline/...` + `trial create/list/show/fork/inject/eval/extract-sop/feedback/archive`
- 验收：命令触发后终端有对应输出。

### P6-03 顶栏导入/导出/登出

- 状态：`[~]`
- 验收：
  1. 导入恢复团队/空间状态
  2. 导出下载 JSON
  3. 登出清理状态并跳登录页

---

## 9. 验收矩阵（最小闭环）

### 9.1 Trial 最小闭环

1. 选团队 + 模式，点击 `🧪 创建试炼`，3 秒内进入 `ready`
2. `▶ 单步` 产生 step，`_sx.currentStep` 与返回 `step_index` 一致
3. `▶▶ 自动` 进入 `running`
4. `⏸ 暂停` 停止推进
5. `▶ 继续` 可恢复
6. `⏹ 终止` 回到可重新创建态
7. 自动运行结束后 `completed`
8. `📊 评分`、`📋 SOP`、`🔄 反哺` 全部可触发

### 9.2 演练最小闭环

1. 运行中展开注入面板（修 BUG-A 后）
2. 任一事件注入成功并记录历史
3. 评分中 `resilience` 有可解释变化

### 9.3 数据一致性回归

1. sessionId 仅一份真实值（`_sx.sessionId`）
2. step 仅后端驱动，不自增
3. 空间标题与房间卡片数量一致
4. 无重复 step 日志
5. 页面无 error 级 JS 报错

---

## 10. 当前统计（v3.0 基线）

> 统计口径：以本文件第 1 节对照表 + 各阶段条目为准，不沿用旧版数字。

| 类别 | 数量 |
|---|---|
| 已有函数（含导演台核心） | 18 |
| 其中可直接判定 `[x]` | 15（+5 本轮修复） |
| 其中 `[~]`（可用但有缺陷） | 2（forkBranch, doInjectEvent） |
| 其中 `[ ]`（关键错误/未完成） | 1（无；4个bug已全部修复） |
| 已确认关键 bug | 0（A/B/C/D 已全部修复） |
| 已确认关键风险 | 2（E/F — 待后续 P3 处理） |

---

*文档版本：v3.0 · 2026-06-10 · 以真实代码行为为准重写，替换旧版 v2.0。*
