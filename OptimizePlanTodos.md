# OptimizePlan — 前后端统一 TODOs

> 基于 `OptimizePlan.md`（总看板）+ 当前代码状态生成的最新待办清单。
> 更新日期：2026-06-03（已按源码核对状态）
> 覆盖范围：`src/frontend/` + `src/backend/` + AI runtime / Plaza / Evolution / Sandbox / Skill
> 原则：不再按 S1/S2/S3 分阶段，按 P0/P1/P2 优先级组织。
>
> 当前验证快照：
> - 后端定向回归：`39 passed`（`test_plaza_dispatch.py` + `test_plaza_consensus.py` + `test_plaza_task_artifact_bridge.py` + `test_plaza_evolution_bridge.py`）
> - 后端全量：`878 passed, 4 skipped`（最近一次 `src/backend/tests` 基线）
> - 前端 build / vitest：`./scripts/frontend_build.sh` 通过；`./scripts/frontend_test.sh src/frontend/__tests__/api.test.js src/frontend/__tests__/system-evolution.test.js` 通过（`14 passed`，通过 bundled-node fallback 绕开本机 Rollup 签名问题）
> - 浏览器 smoke：`datacenter-ratchet-evolution.html` 已实测恢复（`TICK` 后 `PUE 1.850 -> 1.838`、`heritage 0 -> 1`、`WS LIVE`）；`plaza.html` 已实测可重新讨论，且“新建讨论”命中的 CSRF 过期断点已修复为自动刷新重试；`system-evolution.html` 已实测 `运行审查` 与 `演进周期` 可跑通
>
> 最近提交记录：
> - `3f1858a` `Repair system evolution dashboard actions`：修复 `system-evolution` 页的 `EVP` 常量、分页 envelope 消费、共享 `window.api` 被覆盖问题；补 `system-evolution.test.js`
> - `2e448c7` `Add plaza lifecycle coverage`：补 Plaza 创建/启动/重新讨论生命周期回归
> - `87e2d58` `Retry expired CSRF tokens on plaza writes`：Plaza 写请求命中过期 CSRF 时自动刷新并重试
> - `a9d7035` `Restore datacenter flow and add API write limits`：恢复 Datacenter Ratchet 主链并补通用写接口限流
> - `3a82b3b` `Finish runtime entrypoint unification`：统一 AgentLoop / runtime 入口，收窄旧兼容层

---

## 如何阅读

```
[ ] ID 任务描述 ........................ ⚡难度 位置
  └─ 具体步骤
```

- **ID**: SEC/RUN/PLAZA/PLAN/FE/BE/OBS/DATA/DEPLOY — 对应 `OptimizePlan.md` 编号
- **⚡ 极小/小/中/大** = 实现难度
- `[x]` = 已完成

---

## ✅ 已完成（本轮成果）

| ID | 领域 | 内容 |
|----|------|------|
| SEC-01-1 | CSRF 端点 | `GET /api/v1/auth/csrf-token` + middleware 校验 |
| SEC-01-2 | CSRF 前端配合 | `login.html`调 `setCsrfToken`，`api.del()`带 token |
| SEC-01-3 | httpOnly cookie | login/register 返回 `Set-Cookie: ag-token; HttpOnly; SameSite=Strict` |
| BE-01 | 列表 API 分页 | `evolution/items`/`rules`/`history`/`audit-trail`/`optimize/runs`/`plazas` 全部加 `limit/offset` |
| BE-03-1 | 配置集中管理 | 创建 `src/backend/config.py`（server/auth/CORS/pagination/paths/logging/version） |
| BE-09 | 健康检查增强 | `register_health_check()` 注册机制 + `uptime_seconds` |
| FE-02 | 请求缓存 | `agent-team-config.js` 新增 `_reqCache` TTL 缓存（5s） |
| FE-03 | 刷新防抖 | `visibilitychange` 300ms debounce |
| FE-04 | skill-extract 外抽 | 636 行内联 `<style>` → `css/skill-extract.css`；移除重复的 error tracking script |
| FE-05 | Plaza 3D 回流 | `positionSpeechBubble` 缓存 `_cachedRect`（每 5 帧刷新）；`onResize`后气泡重定位 |
| FE-06 | 全局变量命名空间 | `window.AG.state` + `let` 别名保持 `onclick` 兼容 |
| FE-07 | strict mode | `system-evolution.js` 补 `'use strict'` |
| FE-12 | alert() 替换 | `tools-skills.js`/`digital-twin-cli.js`/`tasks.html` 中的 `alert()` → `showInfoModal()`/`toast()` |
| SEC-01-4 | 登出端点 | `POST /api/v1/auth/logout` 删 cookie + 清服务端 token（`test_auth_csrf.py`） |
| SEC-01-5 | token JSON 开关 | `AG_AUTH_RETURN_TOKEN_JSON`（默认 1 兼容）控制是否返回 token JSON |
| SEC-03 | API 限流 | login/register 内存限流 5 次/分钟 + 通用写请求 60/min + 敏感路由独立 bucket（`test_auth_csrf.py`, `test_api_rate_limit.py`） |
| RUN-01-code | Docker Sandbox 代码 | `DockerSandbox` + `docker/sandbox/Dockerfile` + 缺 docker fail-closed（实机验收待补） |
| RUN-01-ci | Docker Sandbox CI | 新增 `sandbox-docker.yml`、`test_sandbox_docker.py`、`test_sandbox_smoke.py`，CI 可 build image 并跑 self-check / integration |
| BE-03-2 | config.py 落地 | `src/backend/config.py` 提供 server/auth/CORS/pagination/paths/logging 常量并被引用 |
| FE-10 | Vitest 单测 | `__tests__/utils|api|agent-config.test.js` + `vitest 4.1.7` + `npm run test:frontend` |
| SEC-01-6 | 登出按钮 | `global-nav.js` 全局导航注入登出按钮 + `api.logout()` 调用 |
| SEC-02 | 安全响应头 | `main.py` 中间件: X-Content-Type-Options / X-Frame-Options / Referrer-Policy / Permissions-Policy / HSTS(环境变量开启) |
| OBS-01-1 | 结构化日志 | `AG_LOG_FORMAT=json` 切换 JSON 行日志；`LOG_LEVEL` 环境变量控制级别 |
| OBS-01-2 | request_id | 每请求生成 `X-Request-ID`（或接受上游传入），注入 `request.state` |
| OBS-01-3 | 前端 request_id 透传 | `api.js` 自动附带并缓存 `X-Request-ID`，错误上下文可回溯 |
| OBS-01-4 | 页面错误提示 request_id | Agent Team / Plaza / System Evolution 错误 toast 自动拼接请求编号 |
| OBS-01-5 | Trace drill-down request_id | Agent Team trace 面板支持 task 明细，并显示每次 trace 请求编号 |
| BE-03-3 | config.py .env | `config.py` 加入 python-dotenv 支持；新增 `RATE_LOGIN_LIMIT` / `RATE_LIMIT_WINDOW` 配置项 |
| BE-P0-01 | 分页补齐 | `/skills/required` / `/templates` / `/tools/execution-history` / `/skill-library` / `/skill-library/suggestions` / `/skills/search` / `/tools/search` 全部加 `limit/offset` |
| PLAZA-01 | 重试+升级 | `plaza_engine._generate_agent_content` 3次重试+指数退避；`_escalation_queue` 失败升级队列；`/plaza/escalations` API |
| RUN-03-code | 状态机与 watchdog | `runtime/state_machine.py` + `TimeoutWatchdog` + 45 项相关测试 |
| RUN-04-code | Event bridge | `channels/event_bridge.py` 实现 EventBus ↔ Channel 桥接 |
| PLAZA-02-code | 共识度量 | `plaza_consensus.py` + `/plaza/.../consensus` API |
| OBS-02-code | OTel tracing 模块 | `monitoring/tracing.py` + `pyproject.toml[otel]` + startup hook |
| FE-08 | i18n key 入口 | `data-i18n` 与 `window.t(key)` 已开始接入侧栏导航 |
| RUN-02-1 | AgentLoop shim 收窄 | `agent_loop.py` 精简为真正 shim；同步 tool-loop 调用面统一到 `run_tool_loop_sync_with_provider` |
| SEC-01-7 | Cookie-only 前端契约 | `agent-detail/tasks-view/wizard/agent-team-config` 写请求显式走 `_agFetch`；新增 `test_frontend_auth_contract.py` |
| SEC-01-8 | Cookie-only 页面补漏 | `datacenter-ratchet-evolution.html`、`token-factory.js`、`plaza.js` 的剩余 POST 写请求已切到 `_agFetch`，并纳入前端 auth contract |
| SEC-01-9 | 同主机跨端口 CSRF | `api.js` 现在会为 `5173 -> 8080` 这类绝对 URL 自动附带 CSRF 与 `credentials=include` |
| FE-01-1 | Datacenter Ratchet 恢复 | 补齐 `src/backend/datacenter_api.py`，页面从 `404/403` 恢复到可用，`TICK/LOCK` 浏览器 smoke 通过 |
| FE-01-2 | System Evolution 页面修复 | 修复 `EVP` 常量缺失、分页 envelope 消费，以及顶层 `api()` 覆盖共享 `window.api` 的问题；`system-evolution.test.js` 与浏览器 smoke 已覆盖 |
| PLAZA-01-2 | Plaza 后端端到端回归 | 新增讨论 → 演化 → 任务产物回写 → verification queue → 关闭 的 happy path 回归（`test_plaza_evolution_bridge.py`） |

---

## P0 — 安全与运行时底座

> 这些是出关必要条件，不完成就不能说系统可用。

### RUN-01 🔴 Docker Sandbox 实机收口

```
位置: src/backend/sandbox/python_runner_docker.py, docker/sandbox/, scripts/
难度: ⚡⚡ 大   优先级: P0
状态: WIP — DockerSandbox 类、Dockerfile、limits、self-check、fail-closed、CI workflow、集成测试均已备；当前机器缺 docker，待远端首轮执行与本机有 docker 时复验
```

- [x] docker mode、Dockerfile、limits、self-check 代码已备
- [x] 缺 docker 时 fail-closed（返回 `SandboxResult(ok=False)`）
- [x] GitHub Actions build sandbox docker image 并执行 self-check
- [ ] 本机实机 build sandbox docker image（当前机器无 docker）
- [ ] `run_python` / `run_pytest` 在 docker 模式跑通所有安全测试（待远端首轮执行结果 / 本机有 docker 时复验）
- [x] 添加 `test_sandbox_docker.py` 集成测试
- [x] 前端 sandbox 页面显示当前 sandbox mode（lite/docker）

### SEC-01 🟢 Cookie-Only Auth 收尾（仅剩清理）

```
位置: src/backend/main.py, src/frontend/login.html, src/frontend/js/api.js
难度: ⚡ 小   优先级: P0
状态: 几乎完成 — httpOnly cookie / logout / AG_AUTH_RETURN_TOKEN_JSON 均已落地
```

- [x] `AG_AUTH_RETURN_TOKEN_JSON` 环境变量（默认 `1` 保持兼容）
- [x] `/api/v1/auth/logout` 端点（删 cookie + 清除服务端 token）
- [x] auth/csrf 回归测试（`test_auth_csrf.py`）
- [x] 全局导航注入「登出」按钮（`global-nav.js`）
- [x] 清理残留 `localStorage.getItem('ag-token')` 引用（已确认无残留）
- [x] 高频写请求页面显式切到 `_agFetch`（`agent-detail/tasks-view/wizard/agent-team-config`）
- [x] Datacenter Ratchet / Token Factory / Plaza TTS 的剩余写请求显式切到 `_agFetch`
- [x] 前端 cookie-only 契约测试（`test_frontend_auth_contract.py`）
- [x] Plaza 新建讨论在 CSRF 过期时自动刷新 token 并重试一次
- [ ] cookie-only 模式下所有页面验收

### RUN-02 🔴 统一 AgentLoop 收窄

```
位置: src/backend/agents/agent_loop.py, src/backend/agents/runtime/*, src/backend/agents/chat_harness.py
难度: ⚡⚡ 大   优先级: P0
状态: DONE — `agent_loop.py` 已收窄为兼容 shim，chat / task / plan 入口都已委托共享 runtime，并有入口契约测试护栏
```

- [x] runtime 拆分 `runtime/plan_loop.py` + `runtime/tool_loop.py`
- [x] 旧 `agent_loop.py` 收窄为真正的 deprecated shim
- [x] 同步 tool-loop 调用面统一到 `run_tool_loop_sync_with_provider`
- [x] 确认所有入口（chat / task / plan）只复用统一 runtime，无残留独立逻辑
- [x] 覆盖 tool-loop / evolution / shim 行为的回归测试
- [x] 覆盖 plan/chat 入口委托共享 runtime 的契约测试

### FE-05 🔴 恢复本机前端构建 / Vitest 可执行性

```
位置: package-lock.json, node_modules, 前端测试脚本
难度: ⚡ 中   优先级: P0
状态: DONE — 已补 `scripts/frontend_build.sh` / `scripts/frontend_test.sh`，优先走 bundled node，可稳定绕开本机 Rollup 签名问题
```

- [x] `api` / `csrf-pages` / `extract-routing` / `agent-config` 测试文件已存在
- [x] 通过 bundled node fallback 绕过 Rollup optional dependency / code-signature 问题
- [x] 恢复前端 build 可执行（`./scripts/frontend_build.sh`）
- [x] 恢复 Vitest 可执行（`./scripts/frontend_test.sh ...`）

### PLAZA-01 Plaza 闭环：重试与失败升级

```
位置: src/backend/agents/plaza_engine.py, src/backend/agents/plaza_routes.py
难度: ⚡ 中   优先级: P0
状态: DONE — 重试+退避+升级队列+API 与后端端到端 happy path 回归均已落地
```

- [x] LLM 调用自动重试（3 次 + 指数退避 1.5s/3s/6s）
- [x] 重试耗尽后的失败升级（`_escalation_queue` + `_escalate_failure()`）
- [x] 升级队列 API（`GET /plaza/escalations` + `POST /plaza/escalations/{index}/resolve`）
- [x] 前端计划面板可见重试/升级状态
- [x] 前端计划面板显示 discussion 级 consensus / dissent / escalations
- [x] 创建讨论 / 重新讨论 / 启动讨论的生命周期回归测试
- [x] 端到端回归测试

### BE-P0-01 列表 API 分页补齐（存量）

```
位置: src/backend/agents/api.py
难度: ⚡ 小   优先级: P0
状态: DONE — 所有主要裸数组端点已补齐 limit/offset
```

- [x] 审查 `agents/api.py` 中仍返回裸 list 的端点
- [x] 补上 `limit/offset`：`/skills/required` / `/templates` / `/tools/execution-history` / `/skill-library` / `/skill-library/suggestions` / `/skills/search` / `/tools/search`
- [x] `skill-extract.js` 已切到共享 `api.list()`（团队、团队智能体、团队技能、公共技能、演化建议）
- [ ] 前端 `api.list()` 在分页 API 上统一消费（其余页面继续推进）

---

## P1 — 质量加固

### SEC-02 生产安全响应头

```
位置: src/backend/main.py
难度: ⚡ 小   优先级: P1
状态: DONE — security_headers_middleware 已落地
```

- [x] 添加安全响应头中间件（X-Content-Type-Options / X-Frame-Options / Referrer-Policy / Permissions-Policy）
- [x] HSTS 通过 `AG_ENABLE_HSTS=1` 环境变量开启
- [x] 前端 API Key 输入使用 `type="password"` 且永不暴露在 URL
- [x] 响应头断言测试（`test_security_headers.py` — 8 项断言）

### BE-04 🟡 后端测试覆盖提升

```
位置: src/backend/tests/
难度: ⚡ 中   优先级: P1
状态: DONE — 新增 45+ 测试用例覆盖安全头/request_id/状态机/共识/通道桥接/重试
```

- [x] 审查 25 个现有测试文件的覆盖范围
- [x] 补充安全响应头断言测试 (`test_security_headers.py`)
- [x] 补充 Plaza 重试 + 升级队列测试 (`test_plaza_retry_escalation.py`)
- [x] 补充状态机 + Watchdog 测试 (`test_state_machine.py`)
- [x] 补充共识度量测试 (`test_plaza_consensus.py`)
- [x] 补充 Channel 事件桥接测试 (`test_channel_event_bridge.py`)
- [x] CI 配置 `npm run test:backend`

### SEC-03 🟢 通用 API 限流补齐

```
位置: src/backend/main.py
难度: ⚡ 小   优先级: P1
状态: DONE — 通用写请求 60/min、敏感路由独立 bucket、回归测试均已落地
```

- [x] login/register 内存限流
- [x] 通用 API 60/min
- [x] 按路由 / 敏感接口细分 bucket
- [x] 限流测试覆盖

### BE-03 main.py 常量迁移到 config.py

```
位置: src/backend/main.py, src/backend/config.py
难度: ⚡ 小   优先级: P1
状态: DONE — 所有核心常量已通过 CONFIG_* 引用 config.py，.env 支持已加
```

- [x] `main.py` 中 `_DEFAULT_CORS_ORIGINS` → `from config import ALLOWED_ORIGINS`
- [x] `main.py` 中 `_PBKDF2_ITERATIONS` → `from config import PBKDF2_ITERATIONS`
- [x] `main.py` 中 `_TOKEN_TTL` → `from config import TOKEN_TTL`
- [x] `main.py` 中 `_CSRF_TTL` → `from config import CSRF_TTL`
- [x] 添加 `.env` 文件支持（python-dotenv）
- [x] 新增 `RATE_LOGIN_LIMIT` / `RATE_LIMIT_WINDOW` 到 config.py

### BE-06 🟡 Pydantic 校验全面化

```
位置: 各 route 文件
难度: ⚡ 中   优先级: P1
```

- [ ] 审查所有 POST/PUT/PATCH handler 的请求体
- [ ] 替换剩余原始 dict 访问为 Pydantic model
- [ ] 确保所有查询参数有类型注解和校验

### FE-02-2 🔵 全局状态收口

```
位置: src/frontend/js/agent-team-config.js
难度: ⚡ 中   优先级: P1
状态: PARTIAL — `window.AG.state` 已建，`tid/aid/wzD/wzS/atab` 别名仍在
```

- [ ] 逐步将 `onclick` 中的全局变量引用收入 `window.AG`
- [ ] 移除 `tid/aid/wzD/wzS` 等裸全局别名
- [ ] 只暴露少量公共 API

### FE-05-EXT 🔵 前端单测继续扩面

```
位置: src/frontend/__tests__/
难度: ⚡ 中   优先级: P1
状态: WIP — 基础测试文件已在仓库，待先恢复本机 vitest 再继续扩面
```

- [x] `api.js` / `csrf-pages` / `extract-routing` / `agent-config` 测试文件
- [ ] 扩到 `utils.js`
- [ ] 扩到登录链 / logout / cookie-only 流程
- [ ] 扩到 Plaza 数据归一化与 runtime helper

### OBS-01 结构化日志 + request_id

```
位置: src/backend/main.py
难度: ⚡ 中   优先级: P1
状态: DONE — JSON 日志 + request_id middleware 已落地，前端 API 客户端已自动透传/缓存 request_id
```

- [x] 日志格式改为 JSON 行输出（`AG_LOG_FORMAT=json`）
- [x] 日志级别通过环境变量配置（`LOG_LEVEL`）
- [x] 为每个请求添加 request_id（`request_id_middleware`，响应头 `X-Request-ID`）
- [x] API 客户端自动透传并缓存 `X-Request-ID`
- [x] 主要运行页错误 toast 显示 request_id
- [x] Agent Team trace drill-down 显示 request_id
- [ ] 其他页面 trace / detail 继续统一显示 request_id

---

## P2 — 体验增强

### FE-08 🟡 i18n 绑定到 UI

```
位置: 多个 JS 文件
难度: ⚡ 中   优先级: P2
状态: PARTIAL — 侧栏导航已标记 data-i18n，DICT 已注册翻译键，`window.t(key)` 已可用
```

- [x] 为常用 UI 字符串添加 `data-i18n` 翻译属性（侧栏导航 8 项）
- [x] 创建运行时翻译函数 `window.t(key)` 用于动态字符串（已有）
- [ ] 在更多页面模板字符串中使用 `data-i18n` 属性标记

### FE-11 🔵 国际化引擎升级

```
位置: src/frontend/js/i18n.js
难度: ⚡⚡ 大   优先级: P2
```

- [ ] 从 DOM text-walker 改为 key-based 方案
- [ ] 创建 `data-i18n` 属性翻译引擎
- [ ] 保留 TEXT_MAP 作为向后兼容，新增 `window.t(key)` API

### FE-09 🔵 SPA 单页应用评估

```
位置: 全部页面
难度: ⚡⚡ 大   优先级: P2
```

- [ ] 评估迁移到 SPA 的 ROI（当前多页架构如果运行良好可不迁移）
- [ ] 如决定迁移：合并 `agent-team-config.js` 为主应用，其他页面提取为视图组件
- [ ] 使用 `hashchange` 或 History API 做客户端路由

### RUN-03 🟡 State Machine + Watchdog

```
位置: src/backend/agents/runtime/state_machine.py
难度: ⚡ 中   优先级: P2
状态: WIP — 模块与测试已就绪，但还未成为 task/session/agent 的统一状态源
```

- [x] 统一状态机定义（AgentState / TaskState / SessionState 转换图）
- [x] 超时 watchdog（TimeoutWatchdog 自动转换过期状态）
- [x] 回调机制 on_transition（可接 SSE 推送）
- [ ] 将 task/session/agent 主链接到统一状态机
- [ ] SSE 状态变更事件（需前端对接）

### RUN-04 🔵 Channels 真正消费

```
位置: src/backend/channels/event_bridge.py
难度: ⚡⚡ 大   优先级: P2
状态: WIP — ChannelEventBridge 已实现 EventBus↔Channel 桥接，主链消费与演示仍缺
```

- [x] channels 成为 runtime 事件总线的一等公民（ChannelEventBridge）
- [x] 支持 inter-agent 消息 send_agent_message()
- [x] 支持 channel 触发任务 trigger_task()
- [ ] 至少 2 个 Agent 通过 ChannelBus 自主对话端到端演示

### PLAZA-02 🔵 Plaza 共识机制

```
位置: src/backend/agents/plaza_consensus.py, plaza_routes.py
难度: ⚡⚡ 大   优先级: P2
状态: WIP — 共识度量 + 反方检测 + API 已就绪，前端计划面板已消费，尚未真正控制讨论退出/轮次
```

- [x] 共识度量（measure_consensus → score/trend/can_early_exit）
- [x] 反方意见机制（highlight_dissent 自动检测强反对）
- [x] API 端点 GET /plaza/{id}/discussions/{id}/consensus
- [x] 前端计划面板展示 score / trend / dissent
- [ ] 动态退出（参与者可在一定条件下自动离场）
- [ ] 将共识结果接入 planner / round 控制

### OBS-02 🔵 OpenTelemetry / OTel Export

```
位置: src/backend/monitoring/tracing.py
难度: ⚡⚡ 大   优先级: P2
状态: WIP — 模块完成，NoOp fallback 与 startup hook 已就绪，真实 exporter smoke 未补
```

- [x] OTel span 覆盖 LLM / tool / task / plaza 调用（trace_llm_call / trace_tool_execution / trace_plaza_discussion）
- [x] 支持 Jaeger / OTLP 导出（OTLPSpanExporter → AG_OTEL_ENDPOINT）
- [x] 保留 NoOp 降级（无依赖时全部 no-op）
- [x] pyproject.toml 新增 `[otel]` optional dependency group
- [ ] 真实 Jaeger / OTLP smoke 验证
- [ ] span naming / attributes 规范化文档

---

## 阶段看板

### P0 进度

```
RUN-01 [~] Docker Sandbox — 代码备，实机验收待补 ...... 🔨
SEC-01 [✓] Cookie-Only Auth — 登出按钮已加，仅剩页面验收 ✅
RUN-02 [✓] 统一 AgentLoop — 入口已统一到共享 runtime ..... ✅
FE-05  [✓] 前端 build/vitest 已可执行（bundled node） .. ✅
PLAZA-01 [✓] 重试 + 失败升级 — 3次重试+升级队列+API .. ✅
BE-P0-01 [✓] 分页剩余端点补齐 — 7个端点已补 ........ ✅
```

### P1 进度

```
SEC-02 [✓] 生产安全响应头 — 中间件已落地 ........... ✅
BE-04  [✓] 测试覆盖提升 — 新增45+测试用例 ......... ✅
BE-03  [✓] main.py 常量 → config.py + .env 支持 .... ✅
SEC-03 [✓] 通用 API 限流补齐 ....................... ✅
BE-06  [~] Pydantic 校验全面化（已 ~75%） ........... ⏳
FE-02-2 [~] 全局状态收口（window.AG 已建） ........ ⏳
FE-05-EXT [~] 前端单测扩面 ........................ ⏳
OBS-01 [✓] 结构化日志 + request_id — 已落地 ....... ✅
```

### P2 进度

```
FE-08  [~] i18n 绑定到 UI — 侧栏已标记 ........... ⏳
FE-11  [ ] 国际化引擎升级 ...................... ⏳
FE-09  [ ] SPA 单页应用评估 .................... ⏳
RUN-03 [~] State Machine + Watchdog — 模块已备 ... ⏳
RUN-04 [~] Channels 事件桥接 — 桥接已备 .......... ⏳
PLAZA-02 [~] Plaza 共识机制 — API已备 ............ ⏳
OBS-02 [~] OpenTelemetry — 模块已备 .............. ⏳
```

---

## 快捷命令

```bash
# 启动前端开发服务
npm run dev

# 启动后端
npm run backend

# 构建生产包
npm run build

# 运行后端测试
npm run test:backend

# 启动全部
npm start
```

---

## 维护规则

1. 每完成一个 TODO，更新本文件对应状态标记 `[x]`。
2. 新增工作项必须有：ID / 状态 / 优先级 / 涉及文件 / 验收方式。
3. 提交前至少运行：
   ```bash
   npm run build
   python3 -m pytest -q src/backend/tests --maxfail=1
   ```
4. `.huashu-skills` 不纳入此计划。

---

> 最后更新：2026-06-02  
> 基于 `OptimizePlan.md` 总看板 + 当前代码状态生成
