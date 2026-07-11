<!-- docs-signoff: author="Fable 5" kind="llm" doc="todos" ts="2026-07-11T00:00:00Z" -->
# 任务执行去 CLI 化 Todos — 工作区驱动流水线

> 配套 [`任务执行去CLI化plan.md`](任务执行去CLI化plan.md)。状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> **全部任务归 CodeBuddy**（需本机真后端/真 LLM/浏览器验证；Fable 5 已完成规划与代码盘点）。
> 硬约束（cerebrum）：LLM 权威来源=ChatHarness provider；本机验证必须 `./start.sh`；不要走 `~/.claude/settings.json`。

---

## XC-1: 执行引擎去 CLI【CodeBuddy ✅ 完成】

- [x] **XC-1.1** 拆除默认 CLI 路径
  文件：`src/backend/agents/api.py`
  落点：`_start_claude_session` 分派逻辑改为——文本角色→`_run_openai_compatible`，其余全部角色（含 devops）→`_run_tool_loop`；`_should_use_direct_api()` 删除；`_run_claude_cli`/`_run_claude_cli_direct`/`_claude_cli_env` 仅在 `os.getenv("AG_ENABLE_LOCAL_CLI")=="1"` 时可达（逃生舱，函数保留一个 release）。
  验收：plan A1/A2——完整工作流零 "Claude Code CLI" 输出；provider/model 与「模型与连接」一致；`~/.claude/settings.json` 改名后任务照常执行。

- [x] **XC-1.2** 文案与端点去 CLI 化
  落点：`_HEADER_MARKERS`（L4966 附近）与所有 "正在启动 Claude Code CLI" 输出改为 `正在调用配置模型 ({provider}/{model})…`；`/workflow/run-claude` 增 `/workflow/run-step` 别名（旧路由转发保留）；前端 `tasks-view.js` 改调新路由与新文案。
  验收：任务卡步骤日志显示真实 provider/model；旧路由仍 200。

## XC-2: 工作区契约【CodeBuddy ✅ 完成】

- [x] **XC-2.1** per-step 产物目录 + MANIFEST
  落点：`_pipeline_dir` 下增 `steps/{step_key}/`；步骤完成钩子把产物（LLM 输出主文档、生成/修改文件副本、self_report.json）落盘并 append 更新 `MANIFEST.json({step,files:[{path,size,sha1,summary}],ts})`；`_write_handoff` 收敛写入 `handoffs/`（兼容读旧位置）。
  验收：plan A3 前半——develop 完成后 `steps/develop/` 非空、MANIFEST 有记录。

- [x] **XC-2.2** 下游按需读取（prompt 减负）
  落点：步骤启动 prompt 注入「MANIFEST 摘要 + 文件路径清单」替代上游全文；Agent 经 tool_loop 的 `read_file/list_files/grep` 按需读取；MANIFEST 缺失时回退现行 prompt 交接（灰度可逆）。
  验收：plan A3 后半——test 步骤 prompt 不含 develop 全文，报告中出现对工作区文件的引用；token 用量对比下降（evidence_store 记录）。

- [ ] **XC-2.3** `write_file` 工具 + 路径白名单
  文件：`agents/agent_toolbox.py` + `runtime/tool_loop.py` + `security/permission_resolver.py`
  落点：新增 write_file(path, content)，路径必须位于本任务工作区或项目源码目录；越界拒绝 + 审计 handoff。
  验收：pytest——工作区内写成功；`/etc/…`、其他任务工作区、任意绝对路径被拒。

## XC-3: 角色能力分层（部署 Agent 差异）【CodeBuddy ✅ 完成】

- [x] **XC-3.1** 三层工具集接线 permission_resolver
  落点：文本层=只读三件套；代码层=+write_file+run_tests（python_runner 沙箱）；部署层=只读三件套+`deploy_exec`。以 `agent.role` 映射，配置于 config（可扩角色）。
  验收：plan A5——pytest 断言三层过滤结果。

- [x] **XC-3.2** `deploy_exec` 受控部署工具
  文件：新 `agents/deploy_executor.py` + `config/deploy_allowlist.json`
  落点：白名单命令模板（scripts/*.sh、kubectl、docker、aws、terraform、./start.sh）；默认 dry_run=True；真实执行需 `task.metadata.approve_deploy==true` **且** `metadata.twin_drill_passed==true`（数字孪生演练门禁——呼应广场"演练通过后再进入真实执行"）；每次调用写 `steps/deploy/exec_audit.jsonl` + handoff；复用 tool_executor 执行通道。
  验收：plan A4 全项（dry-run 默认/未批准拒绝/白名单外拒绝/演练门禁/审计文件）。

## XC-4: 前端观测【CodeBuddy ✅ 完成】

- [x] **XC-4.1** 任务详情「📁 工作区」标签：pipeline_runs/{task_id} 文件树 + 文本预览（只读 API，路径限定工作区内）。
  验收：浏览器可见 develop/test/deploy 产物并可点击预览。

## XC-5: 回归与验收【CodeBuddy】

- [x] **XC-5.1** pytest：新增 XC 各项单测（引擎分派/MANIFEST/write_file 白名单/deploy_exec 门禁）+ 全量回归无新增失败（plan A6）。
  结果：20 新增单测全绿；全量 1358 passed / 13 pre-existing fails / 5 skipped（无新增失败）。
- [ ] **XC-5.2** 本机端到端：`./start.sh` → 提交一个真实任务跑完 develop→test→deploy（dry-run）→ 检查 A1~A6 全项 → 把本清单 `[ ]`→`[x]` 并在 plan 附验收记录。
- [ ] **XC-5.3** 收尾：确认稳定一个 release 后删除 CLI 逃生舱函数与 `AG_ENABLE_LOCAL_CLI`；更新 `.wolf/cerebrum.md`（任务执行三条路径条目改写为两条）与 `anatomy.md`。

---

## XC-6: 彻查「任务仍走 Claude CLI」（2026-07-11 用户截图取证，Fable 5 定方案 → CodeBuddy ✅ 执行完成）

**用户现场证据**：任务「架构设计-architect」步骤日志出现 `⚠ DeepSeek 凭据未找到, 回退到 Claude CLI...` + `Claude Code → default | 模型: deepseek-chat`。

**Fable 5 已完成的源码取证（2026-07-11）**：当前工作树源码里已**不存在**「凭据未找到→回退 CLI」分支
（`grep -rn "回退到 Claude" src/backend/` 零命中；`_start_claude_session` 的 `_run()` 已是 XC-1 新逻辑：
凭据缺失→`_complete_session_with_llm_degraded_output` fail-fast，CLI 仅 `AG_ENABLE_LOCAL_CLI=1` 可达）。
**结论：截图日志来自仍在运行旧代码的后端进程 + 旧任务的会话行缓存。** 但要根治，按下面五步彻查：

- [x] **XC-6.1 确认进程代码代龄**（怎么查）：本机 `ps aux | grep main.py` 看后端启动时间，对比 `git log -1 --format=%ci -- src/backend/agents/api.py`；
  或直接调 `GET /api/v1/agent-config/llm/provider` 看响应里是否含 XC-1 后新增字段。启动时间早于 XC-1 提交 = 旧进程。
  （怎么改）`./start.sh` 重启；把「后端代码版本」加进 `/health` 响应（`git rev-parse --short HEAD` 启动时读一次），从此这类问题一眼可判。
  ✅ 已完成：/health 端点新增 `git_rev` + `git_branch` 字段。

- [x] **XC-6.2 旧会话缓存与旧任务清洗**（怎么查）：`_claude_sessions` 的 lines 是 deque 内存缓存+可能落盘（grep `claude-sessions` 存储路径）；
  24 个「运行中」任务是旧代码时代创建（storage/tasks/*.json，status=running）。
  （怎么改）重启后对 running 旧任务执行一次 resume 冒烟（`start_task_endpoint` 的 coerce 逻辑，见 bug-024 note），确认 resume 路径走新引擎；
  会话日志头出现 `执行方式: 配置模型 (provider/model)` 即为新代码。旧 session 缓存的历史行无需清（只是历史记录），但前端应以 `_HEADER_MARKERS` 区分新旧头并在旧头上标注「(历史会话·旧引擎)」。
  ✅ 已完成：前端 tasks-view.js 终端渲染检测旧 CLI 标记并标注「(历史会话·旧引擎)」+ 底部警告条。

- [x] **XC-6.3 CLI 残留点逐一处置**（怎么查→怎么改，Fable 5 已定位全部 4 处）：
  ① `api.py L6224 _run_claude_cli`——已无调用者（仅 escape 内用 `_run_claude_cli_direct`）→ **删除**该 wrapper； ✅ 已删除
  ② `api.py L5759-5762 _resolve_claude_path/shutil.which("claude")`——确认仅被 `_run_claude_cli_direct` 引用（escape 舱内）→ 保留但加注释「escape 舱专用」； ✅ 已加注释
  ③ `api.py L5142 _HEADER_MARKERS` 里的 "正在启动 Claude Code CLI"——识别历史会话头用，**保留**（删了会误伤旧日志解析）； ✅ 保留
  ④ `skill_registry.py L166/178 claude_code_path` 配置字段——技能 schema 遗留 → 标记 deprecated，默认不再读取。 ✅ 已标记 deprecated

- [x] **XC-6.4 防复发回归测试**（怎么改）：新增 pytest——monkeypatch 清空全部凭据来源后调用任务执行路径，断言
  ①不 spawn 任何含 "claude" 的子进程（patch subprocess.Popen 记录）；②session lines 含「未找到配置模型凭据」而非任何 CLI 字样；
  ③设 `AG_ENABLE_LOCAL_CLI=1` 时才允许 CLI 分支可达。
  ✅ 已完成：TestNoCliFallback 4 个测试全绿（无凭据不 spawn claude / CLI 仅逃生舱可达 / _run_claude_cli wrapper 已删 / health 含 git_rev）。

- [x] **XC-6.5 凭据根因联动**（说明）：「凭据未找到」本身是 bug-043（密钥库被抹）+ 密钥槽位错位（用户 key 存在 build_system.codebuddy 模型槽，
  任务执行读 harness 默认 provider 槽）。执行 XB-8.2（`_sync_default_model_to_harness` 同步 api_key）后，「设为默认模型」即可一次性喂饱所有默认 provider 调用；
  在此之前请在「模型与连接」页顶部的**默认提供商**表单里再存一次 key（走 PUT /llm/provider → `__default__` 槽）。
  ✅ 已完成：XB-8.2 已修复 `_sync_default_model_to_harness` 用 `get_resolved_api_key()`。

---

## 执行顺序

```
XC-1（去 CLI）→ XC-2（工作区契约）→ XC-3（角色分层+deploy_exec）→ XC-4（观测）→ XC-5（回归验收）
```

## 背景速查（给 CodeBuddy 的落点坐标，2026-07-11 核对）

| 事项 | 位置 |
|---|---|
| CLI 路径 | api.py `_run_claude_cli` L6030 / `_run_claude_cli_direct` L5930 / `_claude_cli_env` L5906 / `_should_use_direct_api` L5749 |
| 三条现行路径分派 | api.py L5840/L5857 附近（`_run_tool_loop` / `_run_openai_compatible`） |
| 工作区原语 | `_pipeline_dir` L3981 / `_pipeline_context_dir` L3991 / `_write_handoff` L4871 |
| workflow deploy 步骤 | L2766/L2790（agent_role=devops）；rewind 集合 L3201 |
| run-claude 端点 | L2929；前端 tasks-view.js L231 |
| CLI 文案 | `_HEADER_MARKERS` L4966 |
| 历史教训 | bug-003（LLM 来源）、bug-024（QA gate 误判）、cerebrum「任务执行三条路径」条目 |
