# OptimizePlan — 前后端统一 TODOs

> 基于 `OptimizePlan.md`（总看板）+ 当前代码状态生成的最新待办清单。
> 更新日期：2026-06-04（已按源码核对状态）
> 覆盖范围：`src/frontend/` + `src/backend/` + AI runtime / Plaza / Evolution / Sandbox / Skill
> 原则：不再按 S1/S2/S3 分阶段，按 P0/P1/P2 优先级组织。
>
> 当前验证快照：
> - 后端定向回归：`48 passed`（`test_api_integration_extended.py`，现覆盖 auth/info/health/teams/agents/tools/skills/digital-twin/plaza/evolution 扩展 HTTP 集成测试，含 plaza list/detail/discussions/tasks/verification/consensus 与 evolution analytics/compliance/checklist/zones/escalation/trend/monitoring/audit-trail/optimize-runs）；`23 passed`（`test_start_script_auth_bootstrap.py` + `test_auth_csrf.py`，覆盖 `./start.sh` 本地开发 admin 初始化与认证/CSRF 主链）；此前 `22 passed`（`test_startup_validator.py` + `test_auth_csrf.py`，覆盖启动验证适配受保护 API 与 `/api/v1/info` 公开发现）；`10 passed`（`test_api_handler_integration.py` + `test_core_api_smoke.py`）；`80 passed`（`test_request_models.py` + `test_ab_testing.py` + `test_sandbox_security.py`）；Plaza 主链专项保持 `39 passed`
> - 后端全量：`906 passed, 4 skipped`（最新 `src/backend/tests` 基线）
> - 前端 build / vitest：`./scripts/frontend_build.sh` 通过；`./scripts/frontend_test.sh src/frontend/__tests__/digital-twin-cli-pagination.test.js src/frontend/__tests__/agent-team-config-pagination.test.js src/frontend/__tests__/wizard-pagination.test.js src/frontend/__tests__/agent-detail-pagination.test.js src/frontend/__tests__/tasks-pagination.test.js src/frontend/__tests__/plaza-pagination.test.js src/frontend/__tests__/tools-skills.test.js src/frontend/__tests__/api.test.js src/frontend/__tests__/system-evolution.test.js` → `22 passed`；此前 `./scripts/frontend_test.sh src/frontend/__tests__/agent-team-config-pagination.test.js src/frontend/__tests__/wizard-pagination.test.js src/frontend/__tests__/agent-detail-pagination.test.js src/frontend/__tests__/tasks-pagination.test.js src/frontend/__tests__/plaza-pagination.test.js src/frontend/__tests__/tools-skills.test.js src/frontend/__tests__/api.test.js src/frontend/__tests__/system-evolution.test.js` → `21 passed`；再此前 `19 passed`（通过 bundled-node fallback 绕开本机 Rollup 签名问题）
> - 浏览器 smoke：cookie-only 模式下 `agent-team-config.html?view=skills`、`skill-extract.html`、`sandbox-twin.html`、`datacenter-ratchet-evolution.html`、`plaza.html`、`system-evolution.html` 已实测登录态可打开；登出后重新打开上述 6 个受保护页均会被 401 踢回 `login.html?next=...`；其中 `plaza.html` 已再次实测“新建讨论 → 开始讨论”可跑通，`system-evolution.html` 已再次实测 `运行审查` 与 `演进周期` 可跑通，`datacenter-ratchet-evolution.html` 保持 `TICK` 后 `PUE 1.850 -> 1.838`、`heritage 0 -> 1`、`WS LIVE`
> - RUN-01 定向回归：`./venv/bin/python -m pytest -q src/backend/tests/test_sandbox_security.py` → `19 passed`，新增缺 Docker 时的 blocked/self-check 语义覆盖，并验证 lite 模式 `runtime-self-check` 可通过；远端 GitHub Actions `Sandbox Docker Self Check` 已成功执行 docker image build、self-check、`DockerSandbox.run_python()` 与 `run_pytest()` 集成测试
>
> 最近提交记录：
> - `Plaza and evolution read-route coverage`：`test_api_integration_extended.py` 已继续扩面到 plaza list/detail/discussions/tasks/verification/consensus，以及 evolution analytics/compliance/checklist/zones/escalation/trend/monitoring/audit-trail/optimize-runs
> - `Extended backend integration coverage`：`test_api_integration_extended.py` 已稳定通过，补齐 auth/info/health/teams/agents/tools/skills/digital-twin/plaza/evolution 的扩展 HTTP 集成覆盖，并修正共享 TestClient 下的 cookie / rate-limit 污染
> - `Digital twin pagination consumers`：`digital-twin-cli.js` 已把广场列表与讨论列表读口切到共享分页 helper，避免继续手写 `_af(.../plaza)`；对应 Vitest 已补齐
> - `Local dev admin bootstrap`：`./start.sh` 在本地快速启动时会生成/复用 `config/.dev_admin_password`，通过 `ADMIN_PASSWORD` 创建可登录 admin，避免服务启动后登录 401；固定 `admin123` 仍只在显式 `AG_ALLOW_DEFAULT_ADMIN` 时启用
> - `b3c51c2` `Stabilize sandbox self-check visibility`：沙箱页补展示 `Docker Binary / 最近自检 / 自检命令`，缺 Docker 时的 blocked 诊断继续保留；lite 模式 `runtime-self-check` 改为复用当前解释器，`pytest_collect` 可通过
> - `Complete protected-page cookie-only smoke`：补 `agent-team-config` / `datacenter-ratchet-evolution` 鉴权守卫，完成 6 个高优先级受保护页的登录态与登出回跳浏览器 smoke，并再次跑通 Plaza / Evolution 正向动作
> - `3f1858a` `Repair system evolution dashboard actions`：修复 `system-evolution` 页的 `EVP` 常量、分页 envelope 消费、共享 `window.api` 被覆盖问题；补 `system-evolution.test.js`
> - `2e448c7` `Add plaza lifecycle coverage`：补 Plaza 创建/启动/重新讨论生命周期回归
> - `87e2d58` `Retry expired CSRF tokens on plaza writes`：Plaza 写请求命中过期 CSRF 时自动刷新并重试
> - `a9d7035` `Restore datacenter flow and add API write limits`：恢复 Datacenter Ratchet 主链并补通用写接口限流

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
| RUN-01-code | Docker Sandbox 代码 | `DockerSandbox` + `docker/sandbox/Dockerfile` + 缺 docker fail-closed + blocked diagnostics；远端真容器路径已验收 |
| RUN-01-ci | Docker Sandbox CI | 新增 `sandbox-docker.yml`、`test_sandbox_docker.py`、`test_sandbox_smoke.py`；CI 已成功 build image 并跑 self-check / integration |
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
| SEC-01-10 | 受保护 API 统一鉴权 | `/api/v1/**` 增加统一 auth middleware；无 cookie 访问 Plaza / Evolution 返回 `401`，浏览器端自动回跳登录页 |
| SEC-01-11 | 登录回跳 | `login.html` 支持消费 `?next=`，在 cookie-only 401 回登录后可返回原目标页面 |
| SEC-01-12 | 受保护页显式鉴权守卫 | `agent-team-config.js` 与 `datacenter-ratchet-evolution.html` 增加 `auth/me` 守卫，修复登出后假活 |
| SEC-01-13 | 启动验证适配鉴权 | `/api/v1/info` 保持公开发现；`startup_validator` 遇到受保护 API 的 `401` 时通过 `/health` 服务状态确认模块在线 |
| SEC-01-14 | 本地开发 admin 初始化 | `./start.sh` 在缺少显式 `ADMIN_PASSWORD` 且没有 admin 账号时生成 `config/.dev_admin_password`，并用该密码启动后端，避免本地登录 401 |
| FE-01-3 | 高优先级受保护页 smoke | 登录态 6 页打开 + 登出后 6 页回跳登录；Plaza / Evolution 动作再次冒烟 |
| RUN-01-3 | Docker 缺失诊断 | `runtime-status` 暴露 `docker_binary_path/self_check_blocked`；`runtime-self-check` 在缺 Docker / 缺镜像时显式返回 blocked reason |

---

## P0 — 安全与运行时底座

> 这些是出关必要条件，不完成就不能说系统可用。

### RUN-01 🔴 Docker Sandbox 实机收口

```
位置: src/backend/sandbox/python_runner_docker.py, docker/sandbox/, scripts/
难度: ⚡⚡ 大   优先级: P0
状态: DONE — DockerSandbox 类、Dockerfile、limits、self-check、fail-closed、CI workflow、集成测试均已备；缺 Docker 时的 blocked/self-check 语义也已补齐，lite 模式自检现已可通过；远端 GitHub Actions `Sandbox Docker Self Check` 首轮运行已成功完成 image build、self-check、`run_python` 与 `run_pytest` 集成测试；当前机器仍缺 docker，但本地环境差异不再阻塞 P0 关闭
```

- [x] docker mode、Dockerfile、limits、self-check 代码已备
- [x] 缺 docker 时 fail-closed（返回 `SandboxResult(ok=False)`）
- [x] 缺 docker / 缺镜像时 `runtime-self-check` 返回 blocked reason，`runtime-status` 暴露 `docker_binary_path/self_check_blocked`
- [x] lite 模式 `runtime-self-check` 复用当前解释器，`pytest_collect` 可通过
- [x] GitHub Actions build sandbox docker image 并执行 self-check
- [x] 远端 GitHub Actions 首轮真实执行 docker image build + self-check + `run_python` / `run_pytest` 集成测试
- [ ] 本机实机 build sandbox docker image（当前机器无 docker，仅保留环境差异说明）
- [x] 添加 `test_sandbox_docker.py` 集成测试
- [x] 前端 sandbox 页面显示当前 sandbox mode（lite/docker）

### SEC-01 🟢 Cookie-Only Auth 收尾（仅剩清理）

```
位置: src/backend/main.py, src/frontend/login.html, src/frontend/js/api.js
难度: ⚡ 小   优先级: P0
状态: DONE — 高优先级受保护页的登录态 / 登出回跳浏览器 smoke 已补齐；`./start.sh` 已补本地开发 admin 初始化，避免快速启动后无账号可登录
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
- [x] 登出后重新访问 Plaza / System Evolution 会命中后端 401，并回到 `login.html?next=...`
- [x] `agent-team-config` / `skill-extract` / `sandbox-twin` / `datacenter-ratchet-evolution` / `plaza` / `system-evolution` 的登录态打开与登出回跳浏览器 smoke
- [x] `./start.sh` 在本地快速启动时生成/复用 `config/.dev_admin_password`，并通过 `ADMIN_PASSWORD` 初始化 `admin` 登录；`config/.dev_admin_password` 已加入 `.gitignore`

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
- [x] `system-evolution.js` 已切到共享 `api.list()`（items / rules / history / audit-trail / optimize-runs）
- [x] `tools-skills.js` 已切到共享 `api.list()`（团队工具、团队技能、全局技能/工具列表）
- [x] `plaza.js` 已切到共享 `api.list()`（广场列表、团队树、讨论列表）
- [x] `tasks-view.js` 已切到共享 `api.list()`（团队任务列表）
- [x] `agent-detail.js` 已切到共享 `api.list()`（工具、团队技能、会话列表）
- [x] `agent-team-config.js` 已切到共享 `api.list()`（团队列表、演进 items/rules、LLM 会话、模型列表、导出配置所需的 models/tools/skills）
- [x] `wizard.js` 已切到共享 `api.list()`（团队、模型、技能、工具）
- [x] `digital-twin-cli.js` 已切到共享分页 helper（团队、团队智能体、技能、工具、任务、演进项、SECS 团队/任务/智能体，以及广场/讨论列表）
- [x] 前端 `api.list()` 在分页 API 上统一消费（当前已覆盖所有主要分页列表读路径）

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
状态: WIP — 已有安全头/request_id/状态机/共识/通道桥接/重试等回归；`agent-team` 演化入口、`digital-twin` 主写接口、`health / teams / evolution / plaza` 主路径 HTTP smoke 与扩展集成测试已补齐，并覆盖匿名/已登录 `auth/me`、`/api/v1/info` 公开发现、teams/agents/tools/skills/digital-twin/plaza/evolution 主接口，以及 Plaza discussion 只读子视图与 Evolution dashboard 只读子接口；后续转向更长尾 domain/API 组合覆盖
```

- [x] 审查 25 个现有测试文件的覆盖范围
- [x] 补充安全响应头断言测试 (`test_security_headers.py`)
- [x] 补充 Plaza 重试 + 升级队列测试 (`test_plaza_retry_escalation.py`)
- [x] 补充状态机 + Watchdog 测试 (`test_state_machine.py`)
- [x] 补充共识度量测试 (`test_plaza_consensus.py`)
- [x] 补充 Channel 事件桥接测试 (`test_channel_event_bridge.py`)
- [x] CI 配置 `npm run test:backend`
- [x] 补充 `agent-team` 演化入口与 `digital-twin` 主写接口 HTTP 集成测试 (`test_api_handler_integration.py`)
- [x] 补充 `health / teams / evolution / plaza` 主路径 HTTP smoke (`test_core_api_smoke.py`)
- [x] 补充 logout 失效、`evolution/audit` / `evolution/cycle`、plaza discussion create/summary HTTP 正向链路 (`test_core_api_smoke.py`)
- [x] 补充 auth/info/health/teams/agents/tools/skills/digital-twin/evolution 扩展 HTTP 集成测试 (`test_api_integration_extended.py`)
- [x] 继续补 auth/health/teams/plaza/evolution 主接口集成测试（已覆盖 plaza list/detail/discussions/tasks/verification/consensus 与 evolution analytics/compliance/checklist/zones/escalation/trend/monitoring/audit-trail/optimize-runs）

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

### BE-06 🟢 Pydantic 校验全面化

```
位置: 各 route 文件
难度: ⚡ 中   优先级: P1
状态: DONE — 17 个 handler 已从 `Dict[str, Any]` 迁移到 Pydantic model，并新增 request-model 回归覆盖 bounds、alias 与 dry-run 语义
```

- [x] 审查所有 POST/PUT/PATCH handler 的请求体
- [x] `agent_team_api.py` 11 个 handler → OptimizeRequest/AutoTriageRequest/Dataset*Request/Step*Request 等
- [x] `agents/api.py` 5 个 handler → EditToolRequest/EditSkillRequest/DigitalTwin*Request
- [x] `agents/k8s_webhook_handler.py` 1 个 handler → DryRunLabelInjectionRequest
- [x] `test_request_models.py` 覆盖 top_n/count/max_examples 约束、digital twin alias、dry-run 语义
- [x] 确保所有查询参数有类型注解和校验

### FE-02-2 🔵 全局状态收口

```
位置: src/frontend/js/agent-team-config.js
难度: ⚡ 中   优先级: P1
状态: PARTIAL — `window.AG.state` 已建；`agent-team-config.js` 已把 `tid/aid/wzD/wzS/atab` 等历史裸全局改成 `window.AG.state` 属性代理，移除了轮询式双向同步；其余页面仍待继续收口
```

- [ ] 逐步将 `onclick` 中的全局变量引用收入 `window.AG`
- [~] `agent-team-config.js` 已将 `tid/aid/wzD/wzS` 等裸全局改为 `window.AG.state` 属性代理；其余页面继续收口
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
RUN-01 [✓] Docker Sandbox — 远端 workflow 已跑通真容器路径 .. ✅
SEC-01 [✓] Cookie-Only Auth — 6 页登录/登出 smoke 已补齐 .. ✅
RUN-02 [✓] 统一 AgentLoop — 入口已统一到共享 runtime ..... ✅
FE-05  [✓] 前端 build/vitest 已可执行（bundled node） .. ✅
PLAZA-01 [✓] 重试 + 失败升级 — 3次重试+升级队列+API .. ✅
BE-P0-01 [✓] 分页剩余端点补齐 — 页面消费已统一收口 .. ✅
```

### P1 进度

```
SEC-02 [✓] 生产安全响应头 — 中间件已落地 ........... ✅
BE-04  [~] 测试覆盖提升 — 主接口集成测试继续扩面 ... ⏳
BE-03  [✓] main.py 常量 → config.py + .env 支持 .... ✅
SEC-03 [✓] 通用 API 限流补齐 ....................... ✅
BE-06  [✓] Pydantic 校验全面化 .................. ✅
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
