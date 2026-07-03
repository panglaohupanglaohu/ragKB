# 任务执行：协作化改造 + 防卡死 — 规划与 TODOS（自包含·带伪代码）

> 版本：v1.0 · 日期：2026-06-15
> 配套：`docs/任务执行优化todos.md`（原始痛点清单，本文件是其可执行展开版）
> 状态标记：`[ ]` 未开始 / `[~]` 已落地待本机验证 / `[x]` 已验收
> **本文件刻意不打"由谁执行"的标签——任何工具/人均可按伪代码接续。**
> **环境约束**：当前执行沙箱无 fastapi/pytest（pip 被代理 403），够不到真 LLM 域名 / 本机 8080 / 浏览器。
> 故：后端改动只能 `python3 -m py_compile` 验证；运行时/接口/LLM/浏览器验收必须在本机 `rtk` 环境。

---

## 0. 背景与目标

**痛点**：并发任务页大量任务长期"执行中"不收敛。根因两层：
1. 任务执行的 LLM **写死本地 Claude CLI / `~/.claude/settings.json`**，本地不可达时会话无限挂起；
2. 执行模型是**线性单会话流水线**（PM→研究→架构→开发→测试→部署→文档），每步起一个孤立 LLM 会话，agent 间无真实协作；且缺**步骤级墙钟超时 + 启动对账**，会话挂起即永久 `running`。

**目标**：
- A. 任务 LLM 改读**系统配置的模型**（"模型与连接页" → ChatHarness → `model_pool.json`），与本地 claude 脱钩。（已完成，见 §2）
- B. 新增**协作模式**：任务可走"智能体广场多轮讨论 → 共识 → 产物"，与线性流水线**并存**（默认仍线性，零回归）。（后端已落地，见 §2；前端 + 验证待办，见 §3）
- C. **防卡死**：步骤级墙钟超时、启动 orphan 对账、无 LLM 配置 fail-fast、卡死可观测 + 人工解卡按钮。（待办，见 §3）

---

## 1. 现状代码事实基线（落点锚，改前先 grep 核对行号可能漂移）

文件：`src/backend/agents/api.py`（除非另注）

| 符号 | 约行 | 作用 |
|---|---|---|
| `SubmitTaskRequest` | 2288 | 任务创建请求模型；已加 `execution_mode` |
| `submit_task`（端点） | 3165 | `POST /teams/{team_id}/tasks`；已把 execution_mode 并入 metadata |
| `_submit_internal_task` | 2919 | 统一创建+bootstrap；`auto_start` 分支按 execution_mode 选路 |
| `_start_task_workflow` | 2884 | 线性流水线：起首步会话 + 挂 monitor |
| `_start_task_collaboration` | 2919 前 | **新增**：广场协作执行（§2.B） |
| `advance_workflow` | 3672 后 | 推进步骤；已在激活步骤打 `started_at`（T1.0） |
| `_harness_monitor` | 4073 | 监控线程：轮询 active 步会话状态→推进/重试/失败 |
| `_HARNESS_POLL_SEC` | 3882 | 轮询间隔 5s |
| `_HARNESS_STALL_SEC` / `_HARNESS_MAX_RETRIES` / `_HARNESS_RETRY_DELAY` | 附近 | 停滞阈值 / 最大重试 / 重试间隔 |
| monitor `sess_status=="running"` 分支 | 4217 | **已有 stall 检测**（无输出超 STALL→failed）；**缺墙钟硬超时** |
| `_start_claude_session` | 6432 | 起执行会话（tool-loop / 直连 / 本地 CLI 三路） |
| `_get_deepseek_credentials` | 6355 | 取 LLM 凭据；**已改为优先 harness 配置** |
| `_harness_provider_credentials` | 6355 前 | **新增**：读系统配置 provider |
| `_should_use_direct_api` | 6408 | 选直连 vs 本地 CLI；**已加 provider 非 anthropic→直连** |
| `_annotate_stuck` / `_TASK_STUCK_SEC=1800` | 3227 / 3214 | 任务列表只读标注 stuck（T1.0，不改状态） |
| 任务列表端点 | 3249 | `get_team_tasks` → `_annotate_stuck` |
| `_finalize_task_terminal_state(task,*,force_status,error)` | 2844 | 落终态（complete/fail）+ 证据 + evolution 同步 |
| `_emit_pipeline_event(task_id,type,data)` | 3785 | SSE/事件推送 |

广场（`plaza_engine.py`）：`get_plaza_engine()`（1245 单例）、`create_plaza`、`add_participant(plaza_id,agent_id,name,role,team_id,SeatTier,NicheRole)`、`create_discussion(plaza_id,topic,description,moderator_agent_id,max_rounds)`、`async run_discussion(plaza_id,discussion_id)→Discussion(.summary/.key_conclusions/.messages/.status)`。`SeatTier/NicheRole` 在 `agents/plaza.py`。`main.py:468` 启动已 `set_chat_fn(harness.chat)`（广场用系统配置 LLM）。

---

## 2. 已完成（本轮，`py_compile` 通过，待本机运行验证）

### [~] A. 任务 LLM 改读系统配置（脱离本地 claude）
- `_harness_provider_credentials()`：读 `get_chat_harness().get_provider_config()` →
  `(api_key, resolve_base_url(), model, provider_value)`，无 key 返回四元 None。
- `_get_deepseek_credentials()`：①优先 harness 配置 ②回退 `~/.claude/settings.json`+RTK。
- `_should_use_direct_api(role)`：配置 provider 非 anthropic → 返回 True（直连，绕开本地 CLI）。
- 效果：三条执行路径（tool-loop / 直连 / CLI）的凭据都经此函数；配了非 Anthropic 模型时本地 `claude` 子进程不再启动。

### [~] B. 协作模式后端（广场驱动，与线性并存）
- `SubmitTaskRequest.execution_mode: "linear"|"collaborative"`（默认 linear）；`submit_task` 把它并入 `metadata.execution_mode`。
- `_submit_internal_task` 的 `auto_start` 分支：`metadata.execution_mode=="collaborative"` → `_start_task_collaboration(task, team_id)`，否则 `_start_task_workflow(...)`。
- `_start_task_collaboration(task, team_id)`：兜底 `set_chat_fn(harness.chat)` → 取团队全员 → `create_plaza` → 逐个 `add_participant(...SeatTier.MIDDLE, NicheRole.OBSERVER)` → `create_discussion(topic=任务标题, max_rounds=metadata.collab_max_rounds 默认4)` → 写 `task.metadata.collaboration={plaza_id,discussion_id,...}` → `start_task` → `_emit_pipeline_event("collaboration_started")` → **后台 `asyncio.create_task`** 跑 `run_discussion` → 完成回写 `summary/key_conclusions/message_count` + `artifacts[kind=collaboration_summary]` → `_finalize_task_terminal_state(task)`；异常 `force_status="failed"`。

---

## 3. 待办 TODOS（按优先级；每条含 落点 / 伪代码 / 验收）

### P1 — 协作模式收尾

#### [ ] T5.3 协作模式端到端本机验证
- 落点：运行时验证，无代码改动（除非发现 bug）。
- 步骤：
  1. "模型与连接页"配好可用模型（如 codebuddy/deepseek-v4-pro）。
  2. 起后端：`bash start.sh`（确保 8080 健康）。
  3. 提交协作任务：
     ```bash
     curl -sS -b "$JAR" -H 'content-type: application/json' -H "X-CSRF-Token: $CSRF" \
       -d '{"title":"给协作图加图例说明","description":"...","execution_mode":"collaborative"}' \
       http://localhost:8080/api/v1/agent-config/teams/build_system/tasks
     ```
  4. 断言：广场真实产生**多轮发言**（走配置模型，非本地 claude）；任务最终 `completed`；
     `task.metadata.collaboration` 带 `summary` + `key_conclusions`；`artifacts` 含 `collaboration_summary`。
  5. 回归：再提一个**不带** execution_mode 的任务 → 仍走线性流水线、正常完成。
- 验收：上述断言全过；把 task_id / discussion_id 记入本文件。

#### [ ] T5.4 批量/队列路径支持协作模式（可选增强）
- 现状：`_real_task_executor`（约 2972）与 `submit_batch_tasks`（约 3184）仍只走线性。
- 落点：`_real_task_executor`。
- 伪代码：
  ```python
  async def _real_task_executor(task):
      if (task.metadata or {}).get("execution_mode") == "collaborative":
          await _start_task_collaboration(task, task.team_id)
          return  # 协作模式自管终态
      ... 现有线性逻辑 ...
  ```
  并在 `SubmitBatchRequest`/批量构建 task 时透传 `execution_mode`（item.metadata 已含则无需改）。
- 验收：批量提交带 `execution_mode:"collaborative"` 的任务也走广场。

#### [~] T5.5 前端：执行模式选择 + 协作任务详情  `agent-team-config.html:tk-exec-mode` + `tasks-view.js:submit+collabInfo` node--check✓
- 落点：任务创建表单 + 任务详情视图（`src/frontend/` 下并发任务页，grep `tasks` / `submit` / `execution_mode` 定位；可能在 `agent-team-config.html` 或专门的并发任务 JS）。
- 改动：
  1. 创建表单加单选："执行模式 = 线性流水线 / 智能体协作"，提交时带 `execution_mode`。
  2. 任务卡/详情：当 `metadata.collaboration` 存在时，展示 `discussion_id`（可链到 plaza 页）+ `key_conclusions` 摘要 + 参与人数。
- 伪代码（提交）：
  ```js
  body.execution_mode = form.execMode.value || 'linear';
  await api('POST', `/teams/${teamId}/tasks`, body);
  // 详情渲染
  if (task.metadata?.collaboration) {
    renderCollabSummary(task.metadata.collaboration); // discussion_id + 结论 + 链接 /plaza?d=<id>
  }
  ```
- 验收：`node --check` 通过；vitest（若沙箱可跑则 `npx vitest run <file>`，否则本机）；浏览器手测两种模式。

### P2 — 防卡死（任务永不无限 running）

#### [~] T1.1 步骤级墙钟硬超时（补 stall 之外的总时长上限）  `api.py:_harness_monitor+常量区` py_compile✓
- 现状：monitor 在 `sess_status=="running"` 分支**只有 stall 检测**（无新输出超 `_HARNESS_STALL_SEC` → failed）。慢速持续滴输出、或会话线程永不置状态的情况不被 stall 捕获。
- 落点：`_harness_monitor`，`if sess_status == "running":` 分支内（约 4217），在 stall 检测**之前或之后**加墙钟检查。新增常量靠近 `_HARNESS_POLL_SEC`（约 3882）：`_STEP_WALL_TIMEOUT_SEC = 1200`。
- 伪代码：
  ```python
  # 常量区
  _STEP_WALL_TIMEOUT_SEC = 1200   # 单步最长墙钟时长（秒），超过即判失败

  # _harness_monitor 的 sess_status=="running" 分支内：
  step_started = active_step.get("started_at") or session.get("started_at", 0)
  if step_started and (_time.time() - step_started) > _STEP_WALL_TIMEOUT_SEC:
      _harness_log.warning(f"[Harness] Step {active_step['key']} 墙钟超时 "
                           f"{_STEP_WALL_TIMEOUT_SEC}s → failed")
      session["lines"].append(f"\n⏱️ 步骤墙钟超时 ({_STEP_WALL_TIMEOUT_SEC}s)，判失败\n")
      session["status"] = "failed"; session["exit_code"] = -2
      session["error"] = "step_wall_timeout"
      active_step["failure_reason"] = "step_wall_timeout"
      sess_status = "failed"      # 落到下方既有 retry/advance 逻辑（retry<MAX 则重试，否则跳过）
      # 杀掉可能仍在跑的子进程，避免泄漏
      proc = session.get("proc")
      if proc and proc.poll() is None:
          try: proc.kill()
          except Exception: pass
  ```
  注：复用既有 `if sess_status == "failed" and retry_count < _HARNESS_MAX_RETRIES:`（约 4247）做重试，超过则按既有逻辑标 step failed 并推进，最终 `_finalize_task_terminal_state` 收口。
- 验收（本机）：断开/配错 LLM → 起任务 → 单步在 `_STEP_WALL_TIMEOUT_SEC` 内转 failed/重试，**任务最终 failed 而非无限 running**；正常 LLM 下不误杀（超时值 > 正常单步耗时）。

#### [~] T4.2 无 LLM 配置时 fail-fast（不静默起本地 CLI 空等）  `api.py:_start_claude_session/_run()` py_compile✓
- 落点：`_start_claude_session`（6432）`_run()` 起始处；或更前置在 `_submit_internal_task`/`_start_task_workflow` 入口。
- 伪代码（放 `_run()` 顶部，最小侵入）：
  ```python
  # 既无系统配置 provider，又无 ~/.claude/settings.json 凭据 → 直接失败，别起本地 CLI 空等
  _hk, _, _, _ = _harness_provider_credentials()
  _lk, _, _ = (_get_deepseek_credentials() if not _hk else (_hk, None, None))
  if not _hk and not _lk:
      session["status"] = "failed"; session["exit_code"] = 1
      session["error"] = "no_llm_configured"
      session["lines"].append("\n❌ 未配置任何可用 LLM（模型与连接页为空）→ 跳过执行\n")
      return
  ```
- 验收：清空模型配置 → 起任务 → 会话立即 `failed(no_llm_configured)`，任务 failed，无本地 claude 子进程、无空等。

#### [~] T2.1 启动时 orphan 对账  `api.py:_reconcile_orphan_tasks+init_agent_config` py_compile✓
- 目标：进程重启后，残留 `running` 但其会话/monitor 已不存在、或超最大运行时长的任务 → 置 `failed(orphaned)`。
- 落点：后端启动钩子（`main.py` startup，或 `api.py` 的 `_load_*` 初始化处，grep `startup`/`on_event`/`_load_model_pool`）。新增 `_reconcile_orphan_tasks()` 并在 startup 调一次。
- 伪代码：
  ```python
  _TASK_MAX_RUN_SEC = 3 * 3600  # 任务最长运行时长上限
  def _reconcile_orphan_tasks():
      eng = _te()
      for task in eng.list_all_tasks():           # 若无此 API：遍历各 team get_team_tasks
          if task.status.value != "running":
              continue
          started = _ts_to_epoch(task.started_at or task.created_at)
          has_monitor = task.task_id in _harness_threads
          wf = (task.metadata or {}).get("workflow", [])
          active = next((s for s in wf if s.get("status") == "active"), None)
          sid = active.get("session_id") if active else None
          alive = bool(sid and sid in _claude_sessions
                       and _claude_sessions[sid].get("status") == "running")
          collab = (task.metadata or {}).get("collaboration")
          # 协作任务的"活性"另判：discussion 未 CLOSED 且引擎在跑（保守起见仅按时长判）
          too_old = started and (_time.time() - started) > _TASK_MAX_RUN_SEC
          if (not has_monitor and not alive and not collab) or too_old:
              task.error = "orphaned"; eng._store.save_task(task)
              asyncio.create_task(_finalize_task_terminal_state(
                  task, force_status="failed", error="orphaned"))
  ```
  注意：startup 同步上下文里若无事件循环，用 `asyncio.run(...)` 或把对账排进 startup 协程。grep 现有 startup 写法对齐。
- 验收：制造一个 `running` 残留任务（改存储或杀进程重启）→ 启动后被标 `failed(orphaned)`，不再常驻"执行中"。

#### [ ] T2.2 "清理"按钮扩展到超时 running
- 现状：核查前端 `🧹 清理` 是否只清完成/失败。落点：清理端点（grep `cleanup`/`clear` in api.py）+ 前端按钮。
- 伪代码（后端新增/扩展端点）：
  ```python
  @router.post("/teams/{team_id}/tasks/cleanup")
  async def cleanup_tasks(team_id, req: {"include_stuck_running": bool=False}):
      removed, failed_stuck = [], []
      for t in _te().get_team_tasks(team_id):
          if t.status.value in ("completed","failed","cancelled"):
              _te()._store.delete_task(t.task_id); removed.append(t.task_id)
          elif req.include_stuck_running and _annotate_stuck(t.to_dict()).get("stuck"):
              await _finalize_task_terminal_state(t, force_status="failed", error="manual_cleanup_stuck")
              failed_stuck.append(t.task_id)
      return {"removed": removed, "failed_stuck": failed_stuck}
  ```
- 前端：清理按钮加二次确认 + 勾选"同时清理疑似卡死的执行中任务"。
- 验收：卡死 running 任务可经清理转 failed 并消失；正常 running 不受影响（需勾选 + 确认）。

### P3 — 可观测 + 人工解卡

#### [~] T3.1 任务卡展示运行时长/当前步骤/最近活动 + 卡死高亮  `api.py:_annotate_stuck` + `tasks-view.js:loadTasks` py_compile✓ node--check✓
- 数据已有：列表端点已 `_annotate_stuck`（含 `elapsed_sec`/`stuck`/`stuck_threshold_sec`）。再补"当前步骤 + 最近活动时间"。
- 落点：`_annotate_stuck`（3227）补字段 + 前端任务卡渲染。
- 伪代码（后端补字段）：
  ```python
  def _annotate_stuck(item):
      ... 现有 elapsed/stuck ...
      wf = (item.get("metadata") or {}).get("workflow", [])
      active = next((s for s in wf if s.get("status")=="active"), None)
      item["current_step"] = active.get("key") if active else (
          "collaboration" if (item.get("metadata") or {}).get("collaboration") else "")
      sid = active.get("session_id") if active else None
      sess = _claude_sessions.get(sid) if sid else None
      item["last_activity_sec"] = (_time.time() - sess.get("_last_activity", sess.get("started_at",0))) if sess else None
      return item
  ```
- 前端：`stuck==true` 红色高亮 + "可能卡死"badge；展示 `current_step` 与"已运行 Xs / 最近活动 Ys 前"。
- 验收：浏览器看到时长/步骤/活动；卡死项红色。

#### [~] T3.2 单步 重试 / 跳过 / 终止 按钮  `tasks-view.js:retryStep/skipStep` node--check✓
- 现有：已有 `set_workflow_step_status`（约 3613，可设 completed/active/skipped/pending）、`run_claude_for_task`（约 3636 手动起当前步）、任务级 cancel。
- 落点：复用上面两个端点 + 任务 cancel；前端加按钮。
- 映射：
  - **跳过** → `POST .../workflow/{idx}/status {status:"skipped"}` 然后 `advance_workflow`（或直接置 skipped 并触发推进）。
  - **重试** → 置该步 `active` + 清 `session_id`/`_retries` → `run_claude_for_task`。
  - **终止** → 任务级 cancel 端点（grep `cancel`）。
- 伪代码（前端）：
  ```js
  retryStep(taskId, idx){ api('POST',`/teams/${tid}/tasks/${taskId}/workflow/${idx}/status`,{status:'active'})
                          .then(()=>api('POST',`/teams/${tid}/tasks/${taskId}/workflow/run-claude`,{})); }
  skipStep(taskId, idx){ api('POST',`.../workflow/${idx}/status`,{status:'skipped'}); }
  terminate(taskId){ api('POST',`.../tasks/${taskId}/cancel`,{}); }
  ```
- 验收：卡死步骤可人工重试/跳过/终止，任务能脱困到终态。

---

## 4. 数据结构 / 字段约定（落盘于 `task.metadata`）

```
task.metadata = {
  "execution_mode": "linear" | "collaborative",
  "workflow": [ {index,key,label,agent_id,agent_role,status,started_at,session_id,artifact,_retries,failure_reason} ],  # 线性
  "collaboration": {            # 协作模式
     "mode": "plaza",
     "plaza_id": str, "discussion_id": str,
     "participant_count": int,
     "summary": str, "key_conclusions": [str], "message_count": int
  },
  "artifacts": [ {"kind":"collaboration_summary","discussion_id":str,"summary":str,"key_conclusions":[...]} ],
  "failure_reason": str         # step_wall_timeout | no_llm_configured | orphaned | collaboration_* ...
}
```
新增常量：`_STEP_WALL_TIMEOUT_SEC=1200`、`_TASK_MAX_RUN_SEC=10800`（靠近 `_HARNESS_POLL_SEC`/`_TASK_STUCK_SEC` 定义处，便于调参）。

---

## 5. 本机验收清单（一次跑全）

1. `python3 -m py_compile src/backend/agents/api.py` → 通过（每次后端改动后）。
2. `rtk pytest tests/ -q`（或定向：`tests/test_task_engine.py`、`tests/test_api_*`）→ 无回归。
3. 起后端 `bash start.sh`，配好模型连接：
   - linear 任务：正常完成。
   - collaborative 任务：广场多轮发言、completed、带 summary/结论（T5.3）。
   - 断开/配错 LLM：任务在墙钟超时内 failed，非无限 running（T1.1）；清空配置则即时 `no_llm_configured`（T4.2）。
   - 重启后残留 running 被对账为 orphaned（T2.1）。
   - 前端：执行模式可选、卡死高亮、单步重试/跳过/终止可用（T3/T5.5）。
4. 前端单测：`npx vitest run <改动相关测试>`（沙箱补 `@rollup/rollup-linux-*`/`@esbuild/linux-*` 后亦可跑）。

---

## 6. 风险与回滚

- **零回归保证**：`execution_mode` 默认 `linear`，不传即旧行为；协作模式全程 opt-in。
- **墙钟超时误杀**：`_STEP_WALL_TIMEOUT_SEC` 必须 > 正常单步最大耗时（直连 64K 输出可能数百秒），默认 1200s 偏保守；调小前先观测真实分布。
- **orphan 对账误伤**：协作任务活性判定保守（仅按 `_TASK_MAX_RUN_SEC` 时长），避免把正在讨论的任务误标。
- **回滚**：所有改动集中在 `api.py` 少数函数 + 前端任务页；按本文件 §2/§3 的函数名定位，`git revert` 或删除对应分支即可。每次回写 todos 时附 file:func 证据，便于审计。

---

## 7. 进度回写规则

每完成一条：把对应 `[ ]→[~]`（落地待验）或 `[~]→[x]`（本机验收过），并在行尾补：`文件:函数` + 验证命令/结果。跨文档同步 `docs/任务执行优化todos.md` 对应项。
