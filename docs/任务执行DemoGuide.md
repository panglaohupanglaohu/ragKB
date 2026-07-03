# 任务执行：协作化 + 防卡死 演示手册

> 日期：2026-06-15
> 演示主线：提交任务 → 两种执行模式（线性 / 协作）→ 防卡死四道闸 → 人工解卡
> 建议时长：15-25 分钟
> 配套规划：`docs/任务执行协作化plan与todos.md`
> 演示 ID 约定：任务标题都带 `TASK-DEMO-YYYYMMDD-HHMM`，便于回溯和一键清理。

这份手册不是接口验证清单，而是一条「让任务永不无限 running」的产品故事：你提交任务，系统用**两种执行模式**完成它（线性流水线 / 智能体广场协作），并通过**四道防卡死闸**（墙钟超时、无 LLM fail-fast、启动对账、人工解卡）保证任何异常都收敛到终态，全程在前端可观测。

---

## 0. 演示故事设定

### 0.1 场景

并发任务页上经常堆着一片「执行中」的僵尸任务——LLM 配错、会话挂起、进程重启后残留，没人知道它们还活着没。这次演示要证明：**无论后端怎么抽风，任务都不会永远卡在 running**，而且操作员能在前端一眼看出谁卡死了、并一键解卡。

### 0.2 本次演示要证明什么

- 任务执行的 LLM **跟随系统配置**（模型与连接页），与本地 claude 脱钩。
- 任务支持**两种模式**：线性流水线（默认，零回归）/ 智能体协作（广场多轮讨论 → 共识 → 产物）。
- **四道防卡死闸**任意一道都能把异常任务收敛到 `failed`：
  1. 步骤墙钟硬超时（T1.1）
  2. 无 LLM 配置 fail-fast（T4.2）
  3. 启动 orphan 对账（T2.1）
  4. 卡死高亮 + 单步重试/跳过/终止（T3.1/T3.2）
- 前端能展示**运行时长 / 当前步骤 / 最近活动**，卡死项红色高亮。

---

## 1. 准备阶段

### 1.1 启动与登录

1. 起后端：`bash start.sh`（确保 `http://127.0.0.1:8080/` 健康）。
2. 打开并发任务页：`http://127.0.0.1:8080/agent-team-config.html` → 选团队（如 `build_system`）→ 「📋 并发任务」标签。

验收观察：页面无 401/403；能看到「＋ 提交任务」「📦 批量提交」「🧹 清理」按钮和任务表。

### 1.2 LLM 连接预检

页面：`/agent-team-config.html` → 模型与连接区域。

1. 配好一个可用模型（如 `codebuddy` / `deepseek-v4-pro`，provider 非 anthropic）。
2. 记下它——后面「断开 LLM」演示要把它清掉再恢复。

> 关键点：任务执行的凭据来自这里（`get_chat_harness().get_provider_config()`），**不再**读 `~/.claude/settings.json`。配了非 Anthropic 模型时，本地 `claude` 子进程根本不启动。

---

## 2. 主线一：两种执行模式

### 2.1 线性流水线（默认，证明零回归）

操作：

1. 点「＋ 提交任务」。
2. 填：
   - 标题：`TASK-DEMO-<ID> 给协作图加图例`
   - 描述：随意一句需求
   - **执行模式：线性流水线**（默认值）
3. 提交。

演示看点：

- 任务进入 running，任务卡出现 **workflow 步骤条**（PM→研究→架构→开发→测试→部署→文档）。
- 任务卡实时显示 `已完成 N/总数` 进度 + `⏱ Xm · 当前步骤 · 活动 Ys 前`。
- 步骤逐个推进，最终任务 `completed`。

> 话术：「这是原来就有的线性模式，默认不变——我们没有动它的行为，只是把卡死兜底补齐了。」

### 2.2 智能体协作（广场多轮讨论）

操作：

1. 再点「＋ 提交任务」。
2. 填：
   - 标题：`TASK-DEMO-<ID> 协作版：给协作图加图例`
   - **执行模式：智能体协作（广场讨论）**
3. 提交。

演示看点：

- 任务卡出现 **🤝 协作 · N 条** badge。
- 切到「智能体广场」页（或 `/plaza`）能看到这个讨论**真实产生多轮发言**（走系统配置的 LLM，不是本地 claude）。
- 讨论收敛后，任务 `completed`，`task.metadata.collaboration` 带 `summary` + `key_conclusions`，`artifacts` 含 `collaboration_summary`。

> 话术：「同一个任务，换一种执行模式——不再是单会话流水线，而是让团队成员在广场里真的讨论出共识，再落成产物。两种模式并存，提交时一个下拉切换。」

CLI 旁证（可选，投屏命令行更有说服力）：

```bash
JAR=/tmp/ag.jar  # 你的登录会话
curl -sS -b "$JAR" -H 'content-type: application/json' -H "X-CSRF-Token: $CSRF" \
  -d '{"title":"TASK-DEMO 协作","description":"...","execution_mode":"collaborative"}' \
  http://localhost:8080/api/v1/agent-config/teams/build_system/tasks
```

---

## 3. 主线二：四道防卡死闸（演示重头戏）

### 3.1 闸一 · 无 LLM fail-fast（最直观）

操作：

1. 到模型与连接页，**清空 / 禁用所有模型**（模拟没配 LLM）。
2. 回任务页提交一个线性任务。

演示看点：

- 任务**几乎立刻** `failed`，会话日志写 `❌ 未配置任何可用 LLM（模型与连接页为空）→ 跳过执行`。
- **不会**有本地 claude 子进程被拉起空等。

> 话术：「以前没配模型，它会默默起本地 CLI 然后永远挂着。现在是立刻失败、给明确原因。」

演示后记得把模型配回去。

### 3.2 闸二 · 步骤墙钟硬超时

操作（任选其一制造「会话挂起」）：

- 把模型连接配成一个**能连上但不返回**的错误端点；或
- 演示时直接讲解 + 给一个已超时的历史任务截图。

演示看点：

- 单步在 `_STEP_WALL_TIMEOUT_SEC`（默认 1200s）内转 `failed`，日志写 `⏱️ 步骤墙钟超时 (1200s)，判失败`。
- 触发既有重试逻辑（retry < 2 则重试），最终任务收敛为 `failed` 而非无限 running。

> 话术：「monitor 本来就有「无输出停滞」检测，但慢速滴输出或线程僵死它抓不到。墙钟超时是兜底的总时长上限——单步超过它，无条件判失败。」
>
> 提示：墙钟值默认 1200s 偏保守（直连 64K 输出可能数百秒），演示时若想快速复现，可临时调小 `_STEP_WALL_TIMEOUT_SEC` 再起后端。

### 3.3 闸三 · 启动 orphan 对账

操作：

1. 让一个任务处于 running（或直接改存储造一个残留 running 任务）。
2. **重启后端**（`Ctrl-C` 后再 `bash start.sh`）。

演示看点：

- 启动日志出现 `[Orphan] Task <id> marked orphaned`。
- 该任务在列表里变成 `failed`（error=orphaned），不再常驻「执行中」。

> 话术：「进程一重启，之前的 monitor 线程和会话全没了，老任务就成了僵尸。启动时自动对账：没有活监控、没有活会话、又不是协作中的任务，或者跑超过 3 小时——一律判 orphaned。」

### 3.4 闸四 · 卡死高亮 + 单步解卡（人工兜底）

操作：

1. 找一个 running 超过 30 分钟（`_TASK_STUCK_SEC`）的任务，或临时调小阈值制造一个。
2. 观察任务卡。

演示看点：

- 任务卡出现 **⚠ 可能卡死** 红色 badge，整行淡红底高亮。
- running 任务行显示 `⏱ 运行时长 · 当前步骤 · 最近活动 Ys 前`。
- active 步骤旁出现 **🔄 重试 / ⏭ 跳过** 按钮，加上 **⏹ 取消** 终止。

操作演示：

- 点 **🔄** → 当前步骤重置为 active 并重新起会话。
- 点 **⏭** → 跳过当前步骤、流程继续推进。
- 点 **⏹ 取消** → 整个任务终止到终态。

> 话术：「自动闸兜底之外，操作员永远有最后一手：看到红的，直接重试/跳过/终止，任务立刻脱困。」

---

## 4. 收尾 · 清理

- 点「🧹 清理」按二次确认清掉 demo 产生的 completed/failed 任务（按标题里的 `TASK-DEMO-<ID>` 辨认）。

---

## 5. 演示节奏建议（15 分钟版）

| 时间 | 段落 | 一句话 |
|---|---|---|
| 0-2min | 1. 准备 + LLM 预检 | 「执行用的是系统配置的模型，不是本地 claude」 |
| 2-5min | 2.1 线性 + 2.2 协作 | 「同一个任务，下拉切两种执行模式」 |
| 5-7min | 3.1 无 LLM fail-fast | 「没配模型 → 立刻失败，不空等」 |
| 7-9min | 3.2 墙钟超时 | 「单步超时无条件判败」 |
| 9-11min | 3.3 orphan 对账 | 「重启后僵尸任务自动收尾」 |
| 11-14min | 3.4 高亮 + 解卡 | 「红的一眼看到，一键重试/跳过/终止」 |
| 14-15min | 4. 清理 | 「按 demo ID 一键清场」 |

---

## 6. 落点速查（讲解时被追问可对照）

| 演示点 | 代码落点 |
|---|---|
| 执行模式选择器 | `src/frontend/agent-team-config.html` `#tk-exec-mode` |
| 提交带 execution_mode + 协作 badge | `src/frontend/js/tasks-view.js` submit / loadTasks |
| 墙钟超时 | `src/backend/agents/api.py` `_harness_monitor` + `_STEP_WALL_TIMEOUT_SEC` |
| 无 LLM fail-fast | `api.py` `_start_claude_session/_run()` |
| orphan 对账 | `api.py` `_reconcile_orphan_tasks` + `init_agent_config` |
| 卡死高亮字段 | `api.py` `_annotate_stuck`（current_step/last_activity_sec）|
| 单步重试/跳过 | `tasks-view.js` `retryStep` / `skipStep` |
| LLM 凭据来源 | `api.py` `_harness_provider_credentials` / `_get_deepseek_credentials` |

---

## 7. 演示前自检（沙箱可做）

```bash
python3 -m py_compile src/backend/agents/api.py        # 后端语法
node --check src/frontend/js/tasks-view.js             # 前端语法
```

> 真正的运行时演示（起后端 / 真 LLM / 浏览器）必须在本机 `rtk` 环境，沙箱够不到 LLM 域名和 8080。
