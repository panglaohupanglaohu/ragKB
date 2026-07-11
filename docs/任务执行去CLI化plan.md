<!-- docs-signoff: author="Fable 5" kind="llm" doc="plan" ts="2026-07-11T00:00:00Z" -->
# 任务执行去 CLI 化 Plan — 工作区驱动的多 Agent 任务流水线

> 版本：v1.0 · 日期：2026-07-11 · 作者：Fable 5（规划）· **实施：CodeBuddy**
> 用户需求（2026-07-11 原话）："任务里面，不要使用本地的 claude。改成使用配置好的模型，工作流程以 Agent 之间的工作区目录为基础进行文件的阅读及数据的交换，但是部署类型的 Agent 与其他有差异，他需要文件读取部署能力。"
> 现场证据：任务详情「部署上线-deployer」步骤日志仍显示 `正在启动 Claude Code CLI... Claude Code → default | 模型: deepseek-chat`，随后长时间等待。

---

## 1. 目标（三句话）

1. **模型统一**：任务执行的所有 LLM 调用一律走「模型与连接」页配置的 ChatHarness provider（权威来源，见 cerebrum），**默认彻底不再启动本地 Claude Code CLI 子进程**。
2. **工作区交换**：Agent 之间的数据交换以**任务工作区目录**为唯一媒介——上游把产物写成文件，下游通过文件读取工具消费；不再依赖对话上下文串行传递大块内容。
3. **部署角色差异化**：部署类 Agent（devops/deployer）在「只读工作区」之上额外获得**受控的部署执行能力**（白名单命令 + dry-run 预演 + 演练门禁 + 审计），与代码/文本角色权限分层。

---

## 2. 现状盘点（代码已核对）

### 2.1 执行路径（`src/backend/agents/api.py`）

| 路径 | 触发条件 | 现状 |
|---|---|---|
| `_run_tool_loop`（runtime/tool_loop.py 共享工具环） | tool 角色 | ✅ 已走 harness 模型，保留 |
| `_run_openai_compatible` | `_TEXT_ONLY_ROLES`（PM/researcher/docs/architect） | ✅ 已走 harness 模型，保留 |
| `_run_claude_cli` / `_run_claude_cli_direct`（约 L5930/L6030） | 其余角色且 `_should_use_direct_api()` 为 False | ❌ 本地 CLI 子进程 + 读 `~/.claude/settings.json`——**要拆除的路径** |

- `_should_use_direct_api()`（L5749）仍读 `~/.claude/settings.json` 判断——历史遗留（bug-003 只改了凭据优先级，没拆路径）。
- 截图中 deploy 步骤走的就是 CLI 分支（devops 不在 `_TEXT_ONLY_ROLES`）。
- 关联端点/文案：`/workflow/run-claude` 端点（L2929）、`_HEADER_MARKERS` 里的 "正在启动 Claude Code CLI"（L4966）、前端 tasks-view「运行」按钮。

### 2.2 工作区雏形（已存在，本 plan 收编扩展）

| 原语 | 位置 | 现状 |
|---|---|---|
| `_pipeline_dir(task_id)` → `storage/pipeline_runs/{task_id}/` | api.py L3981 | ✅ 每任务共享目录 |
| `_pipeline_context_dir` → `_context/` | L3991 | ✅ 任务上下文种子（`_seed_project_context`） |
| `_write_handoff(task_id, step_key, payload)` | L4871 | ✅ 步骤交接 JSON |
| `agent_toolbox`（read_file/grep/list_files/dispatch） | agents/agent_toolbox.py | ✅ 工具环可用的文件读取 |
| 沙箱执行 | sandbox/python_runner*.py | ✅ pytest/python 隔离运行 |

**缺口**：产物没有 per-step 目录约定；下游步骤靠 prompt 里塞文本交接而非读文件；没有写文件白名单；deployer 无受控执行工具。

---

## 3. 设计

### 3.1 D1 — 执行引擎统一（去 CLI）

```
所有 workflow 步骤执行:
  role ∈ _TEXT_ONLY_ROLES        → _run_openai_compatible（harness provider）
  其余全部角色（含 devops）      → _run_tool_loop（harness provider + 角色工具集，见 D3）
本地 CLI（_run_claude_cli*）:
  默认不可达；仅当环境变量 AG_ENABLE_LOCAL_CLI=1 时作为显式逃生舱保留
  _should_use_direct_api() 删除（决策不再存在）；~/.claude/settings.json 依赖全部移除
```

- 模型/密钥唯一来源：`get_chat_harness().get_provider_config()`（cerebrum 权威路径）；每模型覆盖走 team model 的 `resolve_api_key`。
- 超时/流式：沿用 `_run_openai_compatible` 的流式与超时参数；工具环沿用 tool_loop 的多轮上限。

### 3.2 D2 — 工作区契约（Workspace Contract）

```
storage/pipeline_runs/{task_id}/
  _context/                 # 任务上下文（已有）
  handoffs/                 # 步骤交接 JSON（_write_handoff 收敛至此，保留旧位置兼容读）
  steps/
    develop/                # developer 产物：变更说明.md、补丁/新文件副本、self_report.json
    test/                   # tester 产物：test_report.md、junit.xml/summary.json
    deploy/                 # deployer 产物：deploy_plan.md、dry_run.log、deploy_result.json、rollback.md
  MANIFEST.json             # 工作区清单：每步骤产物文件列表 + 摘要 + 哈希（下游发现文件的入口）
```

- **上游写**：每步骤完成时，执行器把产物落盘到 `steps/{step_key}/` 并更新 `MANIFEST.json`（append-only，含 `{step, files:[{path,size,sha1,summary}], ts}`）。
- **下游读**：步骤启动 prompt 只注入「MANIFEST 摘要 + 关键文件路径」，Agent 通过工具 `read_file/list_files/grep` 自己按需读取——上下文不再塞全文（token 纪律，符合两阶段经济学铁律：执行期成本可控）。
- **写白名单**：工具环新增 `write_file(path, content)`，路径必须位于 ①本任务工作区 或 ②项目源码目录（developer/tester 角色）；越界拒绝并审计。
- 兼容：旧 `_write_handoff` 语义不变；`MANIFEST.json` 缺失时下游回退到现行 prompt 交接（灰度可逆）。

### 3.3 D3 — 角色能力分层（部署 Agent 的差异）

| 角色层 | 工具集 | 说明 |
|---|---|---|
| 文本层（PM/researcher/docs/architect） | read_file / list_files / grep | 只读工作区+项目；无写、无执行 |
| 代码层（developer/tester/qa） | 文本层 + write_file + run_tests（python_runner 沙箱） | 写限工作区+源码目录；测试在沙箱跑 |
| **部署层（devops/deployer）** | 文本层 + `deploy_exec` | **文件读取 + 部署能力**（用户要求的差异点） |

`deploy_exec(command, dry_run=True)` 设计：
1. **白名单**：仅允许 `scripts/*.sh`、`kubectl`、`docker`、`aws`、`terraform plan/apply`、`./start.sh` 等预注册命令模板（config/deploy_allowlist.json，可编辑）。
2. **默认 dry-run**：真实执行需任务 `metadata.approve_deploy == true`（由人工或上游 QA gate 写入）。
3. **演练门禁**：接既有数字孪生演练结论——`metadata.twin_drill_passed != true` 时拒绝真实执行（呼应广场补充观察："数字孪生演练通过后再进入真实执行"）。
4. **审计**：每次调用写 `steps/deploy/exec_audit.jsonl`（command/dry_run/exit_code/stdout 摘要）+ handoff。
5. 复用 `execution_registry`/`tool_executor` 的执行通道与 `permission_resolver` 权限过滤，不新造执行器。

### 3.4 D4 — 端点与前端观测

- `/workflow/run-claude` → 语义改为「运行当前步骤」，新增别名路由 `/workflow/run-step`（旧路由保留转发，前端逐步切换）。
- 步骤日志头文案去 CLI 化：`_HEADER_MARKERS` 及相关输出改为 `正在调用配置模型 (provider/model)…`。
- 任务详情新增「📁 工作区」标签：列 `pipeline_runs/{task_id}` 文件树（复用现有静态文件读取端点或新增只读浏览 API），点击预览文本文件——让工作区交换可观测。

---

## 4. 验收标准

| # | 验收 |
|---|---|
| A1 | 默认配置下执行完整 develop→test→deploy 工作流，后端日志/步骤输出**零** "Claude Code CLI" 字样；`ps` 无 claude 子进程 |
| A2 | 各步骤 LLM 调用的 provider/model 与「模型与连接」页配置一致（哪怕 ~/.claude/settings.json 不存在/被改名） |
| A3 | develop 产物落盘 `steps/develop/` 且 MANIFEST 更新；test 步骤 prompt 中不含 develop 全文、Agent 通过 read_file 读到产物并在报告中引用 |
| A4 | deployer：dry_run 默认；未 approve_deploy 时真实执行被拒并审计；白名单外命令被拒；`twin_drill_passed` 缺失时真实执行被拒 |
| A5 | 文本/代码/部署三层角色的工具集经 permission_resolver 过滤后与 D3 表一致（pytest 断言） |
| A6 | 全量 pytest 回归无新增失败；旧 run-claude 路由仍可用（转发） |

---

## 5. 风险与回滚

- CLI 逃生舱：`AG_ENABLE_LOCAL_CLI=1` 可临时恢复旧路径（一个 release 周期后删除）。
- MANIFEST 缺失自动回退 prompt 交接，工作区契约灰度可逆。
- deploy_exec 白名单文件热加载，误配可即时修正；默认 dry-run 保证不误伤生产。

---

*执行清单：[`任务执行去CLI化todos.md`](任务执行去CLI化todos.md)（全部任务归 CodeBuddy）*
