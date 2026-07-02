# SECSOptimize — sandbox-twin.html 功能手册 & 优化清单

> 最后更新：2026-06-07 · 关联文件：`src/frontend/sandbox-twin.html` / `.css` / `.js`
>
> 设计语言：Fathom Information Design（信息建筑派 #04，huashu-design）

---

## 一、页面功能使用方法

### 一句话理解

> 页面主语：「在孪生环境里演练 Agent 协作」— Agent 是演员，Skill 是道具，沙箱是舞台，四层是导演流程。

### 1-1 页面结构（从上到下 7 层）

| # | 层 | 作用 | 操作 |
|---|---|---|---|
| ① | **演练导航** | 「演练」组（沙箱/孪生）「资产」组（智能体/技能/广场）「观测」组（演进/成本） | 点击跳转 |
| ② | **KPI 状态条** | 沙箱会话 / 总仿真步 / 提取 SOP / 最优评分 / 运行时状态 | 自动刷新（30s），右上角 ⏱ 闪动 |
| ③ | **四层 Pipeline** | L1 MADTwin → L2 AAS → L3 TwinLoop → L4 MADCG → 回流进化 | **点击任意节点**：自动切到对应 Output tab + 滚动定位 |
| ④ | **沙箱 ID + I/O 镜像** | 左 Input（4 tab）右 Output（4 tab） | 启动仿真后自动填充 Input 任务；Output 实时滚动 |
| ⑤ | **Agent 协作图 5v7** | Planner / Coordinator / Critic / Retriever / Executor，7 边，粒子动画 | hover 节点高亮关联边；msg 超过 5 时变热力图 |
| ⑥ | **辅助区** | L1 环境详情（Agent 节点） + 演练历史（近 20 次） | — |
| ⑦ | **Runtime 抽屉** | ready / mode / docker / image / mem / last-check | 点击「🛡️ Runtime 抽屉」展开详情，内部有自检/刷新按钮 |

### 1-2 核心工作流

```
① 设置参数 → Input → params tab
② 选种子技能 → Input → seed tab → 加载技能库 → 选卡
③ 点击「▶ 启动仿真」
④ 观察 Output → reward tab 看 SVG 收益曲线 + 步骤时间线
⑤ 协作图自动驱动：节点激活 → msg 计数 → 粒子沿边流 → 进度环填充
⑥ 仿真结束后，Output → critic tab 看评分 + 建议；sop tab 看提取的 SOP
⑦ 可点击「💉 注入」把最优 SOP 注回沙箱
```

### 1-3 I/O 镜像的 4 个 Tab

**Input Tab：**

| Tab | 内容 | 数据源 |
|---|---|---|
| 任务 | 仿真触发描述 + session ID | 启动仿真后自动填入 |
| 环境 | 孪生环境初始 Agent 集合 | L1 MADTwin 同步 |
| 种子技能 | 技能卡片列表（可加载/选择/注入） | `/api/v1/skill-router/browse` |
| 运行参数 | mode / max_steps / speed / branches | 表单数据 |

**Output Tab：**

| Tab | 内容 | 数据源 |
|---|---|---|
| 收益曲线 | SVG 折线图 + 元数据（步数/最大收益/趋势 ↑↓→） | SSE stream step 事件 |
| 执行日志 | 实时滚动步骤列表 | SSE stream step 事件 |
| 提取 SOP | SOP 卡片列表（名称/奖励/成功率/状态） | `/api/v1/sandbox/sops` |
| 评分/建议 | 6 维评分条 + 推荐文字 | `/api/v1/sandbox/sessions/{id}` 结束返回 |

### 1-4 协作图 5v7 的行为

| 行为 | 说明 |
|---|---|
| **节点激活** | 首次收到该 Agent 的 step 事件时激活 |
| **消息计数** | 节点下方显示该 Agent 累计收发 msg 数 |
| **进度环** | 节点外圈圆弧，按 msg 数 / 20 填充 |
| **边激活** | step 事件的 agent_actions 中 2 个 key 之间触发 recordCollabEvent |
| **边 msg 徽章** | 边中点显示该边的累计 msg 数 |
| **热力升级** | 当 msg ≥ 5 时，边变橙（amber gradient） |
| **冲突标记** | 冲突边变红色虚线 + dashoffset 流动动画 |
| **流动粒子** | msg 每 2 轮新增 1 个光点，沿贝塞尔曲线从 from 飘到 to |
| **hover 高亮** | hover 节点时，关联边全亮 1.0、非关联边 0.08 |
| **重置按钮** | 清空所有计数/粒子/进度环 → 恢复初始状态 |

### 1-5 快捷键 & 联动

| 触发 | 效果 |
|---|---|
| 点击 Pipeline L1 | 滚到 L1 Agent 节点区 |
| 点击 Pipeline L2 | 切 Output → sop tab |
| 点击 Pipeline L3 | 切 Output → reward tab |
| 点击 Pipeline L4 | 切 Output → critic tab |
| 仿真启动 | 自动高亮 L3 |
| 仿真完成 | 自动跳到 L4 |

---

## 二、API 对接清单（等 M3 写完后验证）

以下列出前端调用 → 后端端点的完整映射，M3 改完后逐项验证即可。

### 2-1 前端调用的所有 API（`sandbox-twin.js`）

| # | 前端调用 | 方法 | 后端端点 | 前端 MIME | 状态 |
|---|---|---|---|---|---|
| 1 | `apiFetch('/stats')` | GET | `/api/v1/sandbox/stats` | JSON | ✅ |
| 2 | `apiFetch('/sops')` | GET | `/api/v1/sandbox/sops` | JSON | ✅ |
| 3 | `apiFetch('/runtime-status')` | GET | `/api/v1/sandbox/runtime-status` | JSON | ✅ |
| 4 | `apiFetch('/runtime-self-check', {method:'POST'})` | POST | `/api/v1/sandbox/runtime-self-check` | JSON | ✅ |
| 5 | `apiFetch('/sessions', {method:'POST', body})` | POST | `/api/v1/sandbox/sessions` | JSON | ✅ |
| 6 | `apiFetch('/sessions/'+sid+'/run', {method:'POST'})` | POST | `/api/v1/sandbox/sessions/{id}/run` | JSON | ✅ |
| 7 | `apiFetch('/sessions/'+sid+'/inject', {method:'POST', body:{confirm:true}})` | POST | `/api/v1/sandbox/sessions/{id}/inject` | JSON | ✅ |
| 8 | `apiFetch('/sessions/'+sid+'/stop', {method:'POST'})` | POST | ⚠️ **后端尚未实现** `/sessions/{id}/stop` | JSON | 🔴 待 M3 补 |
| 9 | `new EventSource(API + '/sessions/' + sid + '/stream')` | GET | `/api/v1/sandbox/sessions/{id}/stream` | SSE | ✅ |
| 10 | `_af('/api/v1/skill-router/browse')` | GET | `/api/v1/skill-router/browse` | JSON | ✅ |
| 11 | `fetch('/api/v1/auth/csrf-token')` | GET | `/api/v1/auth/csrf-token` | JSON | ✅ |

### 2-2 前端消费的数据字段

#### 2-2-1 `/stats` → `loadStats()`

| 前端使用 | 后端字段路径 | 用途 |
|---|---|---|
| `kpi-sessions` | `stats.twin_loop.total_sessions` | KPI 条 |
| `kpi-steps` | `stats.twin_loop.total_steps` | KPI 条 |
| `kpi-sops` | `stats.zero_exp.total_sops` | KPI 条 |
| `kpi-score` | `stats.critic.max_score` | KPI 条 |

#### 2-2-2 SSE `/stream` → `connectStream()`

| 事件 type | 消费字段 | 用途 |
|---|---|---|
| `step` | `data.step_id` / `data.global_reward` / `data.agent_actions` | 时间线 + 曲线 + Agent 节点状态 + 驱动协作图 |
| `complete` | `data.total_steps` | 完成状态 + 切到 L4 |

#### 2-2-3 `/run` 返回 → `createAndRun()`

| 字段 | 用途 |
|---|---|
| `result.alignment.evaluation.{global_score, task_completion, ...}` | 填充评分面板 |
| `result.total_steps` | 状态栏显示 |
| `result.alignment.best_sop` | 判断是否启用注入按钮 |

#### 2-2-4 `/sops` → `renderSOPs()`

| 字段 | 用途 |
|---|---|
| `sop.name` | SOP 卡片标题 |
| `sop.avg_reward` | 卡片奖励值 |
| `sop.success_rate` | 卡片成功率 % |
| `sop.status` | 颜色标记（validated=绿，其余=橙） |

#### 2-2-5 `/runtime-status` → `renderRuntimeStatus()`

| 字段 | 用途 | 渲染位置 |
|---|---|---|
| `runtime.mode` | 页脚 chip | `rt-mode` |
| `runtime.docker_available` | 页脚 chip | `rt-docker` |
| `runtime.image_available` | 页脚 chip | `rt-image` |
| `runtime.ready` | 页脚 chip 颜色 | `rt-ready` |
| `limits.memory_limit_mb` | 页脚 chip | `rt-mem` |
| `lastCheck.ok` | 页脚 chip | `rt-lastcheck` |
| `lastCheck.checks` | 展开抽屉详情 | `runtime-drawer__inner` |

### 2-3 需要 M3 对齐的点

| # | 问题 | 说明 |
|---|---|---|
| P0 | **`POST /sessions/{id}/stop` 不存在** | 前端 `stopSimulation()` 调用此端点，目前 fallback 到本地关闭 SSE |
| P0 | **协作图 agent_id 映射** | `mapAgentId()` 用字符串匹配推断角色（plan→planner, coord→coordinator...），如果后端返回的 agent id 格式变化需同步更新映射表 |
| P1 | **SSE step 事件的 `agent_actions` 格式** | 目前前端假设 `{ "twin-xxx": "action", ...}` 的 key-value 结构。如果改成数组 `[{agent_id, action}]` 需改 `addTimelineStep` + `driveCollabFromStep` |
| P1 | **`/sessions` 列表（全部会话）** | 目前前端只用单 session 流，但 `session-list` 面板依赖 `addSessionToHistory`（前端本地维护）。可以用后端 `GET /sessions` 替换本地状态，数据更可靠 |
| P2 | **无 `last_self_check` 返回** | 当前 lite mode 返回 `"last_self_check": {}`，前端判空跳过了。如果 docker mode 返回不一样的结构，`renderRuntimeStatus` 里的 `lastCheck.ok` 可能取不到 |

---

## 三、沙箱页面剩余优化清单

按优先级排序 ↓

### 🔴 P0 — 功能缺陷（影响可用性）

| # | 项目 | 现状 | 优化方案 |
|---|---|---|---|
| P0-1 | **停止仿真后端端点** | `POST /sessions/{id}/stop` 未实现，前端只能本地关闭 SSE | 后端新增 `/stop` 端点，终止 TwinLoop 运行 → 返回已执行步骤数 |
| P0-2 | **Agent 网格静态写死** | `agent-grid` 只显示 5 个固定角色，不反映实际孪生环境中的 Agent | 调用 `/sync-from-dt` 或 `/world/sync` 返回的 `agent_ids` 动态渲染 |
| P0-3 | **I/O 镜像没有回显实际数据** | Input「任务」tab 在仿真启动后只显示 `session_id` 和参数，缺少任务描述 | `/run` 返回中增加 `task_description` 字段，前端渲染到 input-content-task |

### 🟡 P1 — 体验提升（影响感知质量）

| # | 项目 | 现状 | 优化方案 |
|---|---|---|---|
| P1-1 | **Agent 协作图映射不准** | `mapAgentId()` 用 contains 匹配，容易漏掉或误匹配 | 后端 `/stream` step 事件增加 `agent_roles` 字段 `{"agent-x": "coordinator", ...}`，前端直接用 |
| P1-2 | **SOP tab 空状态太弱** | 只显示 "尚未提取 SOP"，与当前仿真的 I/O 叙事无关 | 显示「本次仿真尚未提取 SOP，查看历史 SOP 点 → sop tab」或直接列出缓存 SOP |
| P1-3 | **演练历史无详情跳转** | session-list 只显示 ID/步数/评分，点击无反应 | 点击历史项跳转到 `output-content-critic` 并尝试 `GET /sessions/{id}` 回填评分面板 |
| P1-4 | **无仿真进度百分比** | 只有步数计数器，看不出还差多少 | SSE step 事件增加 `total_steps` 字段；Pipeline L3 节点显示 `当前/总步数` 进度条 |

### 🟢 P2 — 锦上添花（长期方向）

| # | 项目 | 现状 | 优化方案 |
|---|---|---|---|
| P2-1 | **Input env tab 全空** | 永远是 "孪生环境初始 Agent 集合" 占位 | 启动仿真前调用 `/sync-from-dt`，展示实际同步到的 Agent 列表 |
| P2-2 | **评分面板无历史对比** | 每次只显示最新评分，无趋势对比 | 保存最近 3 次评分 → critic tab 底部加迷你趋势线 |
| P2-3 | **协作图支持导出** | 纯 SVG 展示，不可导出 | 加「📸 截图」按钮 → 触发 `navigator.clipboard` 或 `canvas.toDataURL` |
| P2-4 | **Pipeline 节点悬浮提示太简单** | 只有 layer 名 + 模块名 | hover 显示更多层职责摘要（从设计文档静态注入） |
| P2-5 | **Runtime 抽屉内容格式** | 纯 text 罗列，无视觉层级 | docker info 做 key-value 表；自检结果做绿色√红色✕列表 |
| P2-6 | **移动端适配** | CSS 有 `@media` 但未实际测试 | 调 grid 列数 + 折叠 Pipeline 为垂直列表 + 协作图降为 3 列 |

---

## 四、文件清单

| 文件 | 路径 | 行数 | 职责 |
|---|---|---|---|
| HTML | `src/frontend/sandbox-twin.html` | ~300 | 7 域 DOM 结构 |
| CSS | `src/frontend/css/sandbox-twin.css` | ~1300 | Wabi-Sabi + Fathom 协作图 + I/O + 状态条 |
| JS | `src/frontend/js/sandbox-twin.js` | ~860 | API 调用 + SSE + IO tab + 协作图渲染 + 数据绑定 |
| API | `src/backend/sandbox/api.py` | — | 15 个端点（含 stats/sessions/SSE/runtime/inject） |

---

> M3 改完后端告诉我就行，我会按上面 2-3 的清单逐项验证对接。
