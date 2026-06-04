# OptimizePlan — 前后端整体优化总看板

> 更新日期：2026-06-04
> 覆盖范围：`src/frontend/` + `src/backend/` + AI runtime / Plaza / Evolution / Sandbox / Skill  
> 输入材料：`FrontBackEndOptimize.md`、`FrontBackEndTodos.md`、`OptimizePlan1.md`、`OptimizePlan1Todos.md`、当前前后端代码。  
> 说明：仓库中未找到用户提到的 `FrontEndOptimize.md`，本版用现有前端专项内容和当前代码状态补齐。  
> 原则：不再按 Week 排期；全部事项转为可执行 TODO，看代码完成到哪里，就同步更新本文件状态。

---

## 0. 当前结论

这个项目已经完成了两条很重要的地基：

1. **AI runtime 主链**已经从“模块很多但闭环偏软”推进到可追踪、可验证、可前端观察：
   - Plaza 计划可派发到真实 Task 链。
   - Task 产物、diff、test_result、trace 会回写。
   - Evolution 不再自动假闭环，Plaza 派生项可同步验证状态。
   - Agent / Skill 绑定、permissions、secrets、budget、sandbox 都已有主链能力。
   - 共识度量、状态机、Channel bridge、可选 OTel tracing 模块都已开始成型。

2. **前端工程化**已经从“大量内联脚本 + 页面重复逻辑”推进到更清晰的多页模块体系：
   - 统一 API 客户端、全局导航、共享 utils、CSS variables 已出现。
   - 多个大页面 JS 已外抽。
   - Plaza / Sandbox / Evolution / Agent Team / PortRuntime 已开始消费后端运行时能力。

但还不能宣布“整体优化完成”。当前真正剩下的高价值缺口是：

- 安全：cookie-only auth、CSRF token 生命周期、API Key 传输安全、速率限制仍需收口。
- 运行时：Docker sandbox 需要实机验证；AgentLoop 入口已经统一到共享 runtime，但状态机 / channels 还未完全成为核心运行机制。
- 前端：模块化已经做了大半，但全局状态、i18n key-based、测试面扩张、Plaza 3D 浏览器实测仍需继续。
- 后端：分页主链已基本落地，但 Pydantic 校验、通用限流与集成测试仍不完整。
- 可观测：trace 已有查询和导出，但还不是 OpenTelemetry / request_id / 生产日志体系。

---

## 1. 当前验收快照

| 维度 | 当前状态 | 说明 |
|------|:--------:|------|
| 前端构建 | ✅ 通过 | 本轮验证：`./scripts/frontend_build.sh` 通过；当前通过 bundled-node fallback 绕开本机 Rollup 原生模块签名问题 |
| 前端单测 | ✅ 通过 | 本轮验证：`./scripts/frontend_test.sh src/frontend/__tests__/digital-twin-cli-pagination.test.js src/frontend/__tests__/agent-team-config-pagination.test.js src/frontend/__tests__/wizard-pagination.test.js src/frontend/__tests__/agent-detail-pagination.test.js src/frontend/__tests__/tasks-pagination.test.js src/frontend/__tests__/plaza-pagination.test.js src/frontend/__tests__/tools-skills.test.js src/frontend/__tests__/api.test.js src/frontend/__tests__/system-evolution.test.js` → `22 passed`；此前 `21 passed` 与 `19 passed`；可通过 bundled-node fallback 稳定执行 |
| 浏览器 smoke | ✅ 通过（P0 范围） | 本轮验证：cookie-only 模式下 `agent-team-config.html?view=skills`、`skill-extract.html`、`sandbox-twin.html`、`datacenter-ratchet-evolution.html`、`plaza.html`、`system-evolution.html` 已在登录态逐页打开；登出后重新打开上述 6 个受保护页均会被 401 踢回 `login.html?next=...`；其中 `plaza.html` 已再次实测“新建讨论 → 开始讨论”可跑通，`system-evolution.html` 已再次实测 `运行审查` 与 `演进周期` 可跑通，`datacenter-ratchet-evolution.html` 保持 `TICK` 后 `PUE 1.850 -> 1.838`、`heritage 0 -> 1`、`WS LIVE` |
| 后端定向回归 | ✅ 通过 | 本轮验证：`test_api_integration_extended.py` → `40 passed`，覆盖 auth/info/health/teams/agents/tools/skills/digital-twin/evolution 扩展 HTTP 集成测试；`test_start_script_auth_bootstrap.py` + `test_auth_csrf.py` → `23 passed`，覆盖 `./start.sh` 本地开发 admin 初始化与认证/CSRF 主链；此前 `test_startup_validator.py` + `test_auth_csrf.py` → `22 passed`，覆盖启动验证适配受保护 API 与 `/api/v1/info` 公开发现；`test_api_handler_integration.py` + `test_core_api_smoke.py` → `10 passed`；`test_request_models.py` + `test_ab_testing.py` + `test_sandbox_security.py` → `80 passed`；Plaza 主链专项保持 `39 passed` |
| 后端全量 | ✅ 通过 | 最新稳定基线：`./venv/bin/python -m pytest -q src/backend/tests` → `906 passed, 4 skipped` |
| Cookie-only / Sandbox 定向回归 | ✅ 通过 | 最近一次更广覆盖：`test_frontend_auth_contract.py` + `test_auth_csrf.py` + `test_sandbox_security.py` + `test_sandbox_smoke.py` + `test_sandbox_docker.py` → `37 passed, 3 skipped`；随后又验证：`test_auth_csrf.py` + `test_frontend_auth_contract.py` → `24 passed`，`test_sandbox_security.py` → `19 passed`，覆盖缺 Docker 时的 blocked/self-check 语义以及 lite 模式自检成功；远端 `Sandbox Docker Self Check` 已跑通真容器路径 |
| 前端规模 | 19 JS / 11 HTML / 6 CSS | 以当前 `src/frontend` 文件统计为准 |
| 后端规模 | 147 Python / 25 backend tests | 以当前 `src/backend` 文件统计为准 |
| `.huashu-skills` | 不纳入 | 用户明确要求一直不动 |

已知验证阻塞 / warning：

- 本机 `node_modules` 仍存在 Rollup 原生模块签名 / optional dependency 问题：`@rollup/rollup-darwin-arm64`，当前已通过 bundled-node fallback 绕开。
- 多个 HTML 页面仍有非 `type="module"` 脚本不能被 Vite bundle 的 warning。
- 当前 CSS minify 阶段仍有一处语法 warning：`Expected ":"`，需在后续前端 CSS 收口时定位。

---

## 2. 已完成铺垫

### 2.1 AI Runtime / Plaza / Evolution

| 编号 | 状态 | 内容 | 主要验证 |
|------|:----:|------|----------|
| R-01 | DONE | Plaza 计划可结构化派发到真实 Task 提交链 | Plaza dispatch 回归 |
| R-02 | DONE | Evolution 去掉 `DISPATCHED -> VERIFY_PENDING` 假闭环 | `test_plaza_evolution_bridge.py` |
| R-03 | DONE | Task 执行产物回写到 task metadata，并同步 EvolutionItem | `test_plaza_task_artifact_bridge.py` |
| R-04 | DONE | Task 终态补 `diff_by_file` / `patch_preview` | artifact bridge 回归 |
| R-05 | DONE | Plaza 派生且测试通过的演进项可 auto verify / close | artifact bridge 回归 |
| R-06 | DONE | 显式 verify test 保持 pending，并暴露 verification queue / alerts | Plaza / Evolution 回归 |
| R-07 | DONE | Plaza discussion SSE 推送 `verification_state_updated` | Plaza SSE 回归 |
| R-08 | DONE | Agent / Skill 绑定支持持久化、运行时解析、required_tools 注入 | `test_agent_skill_binding.py` |
| R-09 | DONE | permissions 接入 tool schema、AgentLoop、ToolExecutor | `test_permissions_and_secrets.py` |
| R-10 | DONE | secrets 本地 Fernet 加密，支持旧明文迁移 | `test_permissions_and_secrets.py` |
| R-11 | DONE | 共享 tool runtime + plan runtime 已落地；同步 tool-loop 调用面已统一到 `run_tool_loop_sync_with_provider`，`AgentLoop` 仅保留兼容 shim，chat / task / plan 入口均已委托共享 runtime | `test_unified_tool_loop.py`, `test_plan_loop_runtime.py` |
| R-12 | WIP | token budget / usage 已接入 chat / stream，并有 API 与前端面板 | `test_token_budget.py` |
| R-13 | WIP | LiteSandbox + DockerSandbox 入口、limits、runtime status、self-check 脚本、sandbox smoke、自检 API、docker 集成测试与专用 GitHub workflow 已接通；缺 Docker 时 `runtime-self-check` 现会显式返回 blocked reason 而不是盲跑失败，lite 模式会复用当前解释器保证 `pytest` 自检可通过；当前机器仍缺 docker，待远端首轮执行 / 本机复验 | `test_sandbox_security.py`, `test_sandbox_docker.py` |
| R-14 | WIP | 统一状态机 + TimeoutWatchdog 模块与测试已落地，运行时主链尚未完全切换到它 | `test_state_machine.py` |
| R-15 | WIP | ChannelEventBridge 已实现 EventBus ↔ Channel 桥接，并支持 agent message / trigger task | `test_channel_event_bridge.py` |
| R-16 | WIP | Plaza 共识度量、反方检测与 `/consensus` API 已落地；动态退出尚未接入讨论主循环 | `test_plaza_consensus.py` |
| R-17 | WIP | 可选 OpenTelemetry tracing 模块、NoOp fallback、FastAPI startup hook 已落地；真实 exporter smoke 待补 | 代码接线已完成 |

### 2.2 前端工程化

| 编号 | 状态 | 内容 | 说明 |
|------|:----:|------|------|
| FE-DONE-01 | DONE | XSS 修复覆盖多处 innerHTML 拼接 | `escapeHtml()` / `esc()` 已广泛使用 |
| FE-DONE-02 | DONE | 统一 API 客户端 `src/frontend/js/api.js` | CSRF-ready、cookie auth 兼容、离线检测、分页辅助、`X-Request-ID` 透传/缓存、错误文案拼接 helper |
| FE-DONE-16 | DONE | 主要运行页错误提示已附带 request_id | Agent Team / Plaza / System Evolution 的错误 toast 可直接回溯 |
| FE-DONE-03 | DONE | 全局导航 `src/frontend/js/global-nav.js` | 多页面不再重复硬编码导航 |
| FE-DONE-04 | DONE | CSS variables 提取 | `src/frontend/css/variables.css` |
| FE-DONE-05 | DONE | 多个大页面 JS 外抽 | Plaza / Sandbox / System Evolution / Skill Extract / Digital Twin 等 |
| FE-DONE-06 | DONE | CSP meta、client error tracking、可访问性与 i18n 基础增强 | 仍需 key-based i18n |
| FE-DONE-07 | DONE | Plaza 前端消费 verification queue / alerts / SSE broadcast | 可在计划面板运行验证队列 |
| FE-DONE-08 | DONE | Sandbox 前端消费 runtime-status / runtime-self-check | 可看 readiness、limits、自检、Docker Binary、自检命令与最近自检结果 |
| FE-DONE-09 | DONE | Evolution 前端展示 verify detail / retry / escalation | 演进条目表可见 |
| FE-DONE-10 | DONE | Agent Team 前端展示 budget / alerts / trends / trace / drill-down | 支持 NDJSON 导出、task 级 trace 明细与 request_id 显示 |
| FE-DONE-11 | DONE | PortRuntime 前端展示 Agent Loop plan / runtime events | 可直接看共享 runtime 事件序列 |
| FE-DONE-12 | DONE | Plaza → 技能萃取会优先落到讨论主持团队，并默认选中对应团队智能体上下文 | `extract-routing` helper + Vitest 回归 |
| FE-DONE-13 | DONE | Agent Team 侧栏已开始接入 `data-i18n` 与 `window.t(key)` 兼容层 | `agent-team-config.html`, `i18n.js` |
| FE-DONE-14 | DONE | 全局导航已接入统一登出动作 | `global-nav.js` + `api.logout()` |
| FE-DONE-15 | DONE | Plaza 计划面板已展示 verification / consensus / escalations，并可在讨论维度处理升级项 | `plaza.js`, `plaza.html` |
| FE-DONE-17 | DONE | Agent Detail / Tasks View / Wizard / Agent Team Config 的高频写请求已显式收口到 `_agFetch` | cookie-only / CSRF 主链不再依赖隐式全局 `fetch` 包装 |
| FE-DONE-18 | DONE | Datacenter Ratchet / Token Factory / Plaza TTS 的剩余 POST 写请求已切到 `_agFetch`，并纳入前端 auth contract | cookie-only 收尾时不再留后门页面 |
| FE-DONE-19 | DONE | `api.js` 现已支持同主机跨端口绝对 URL 的 CSRF + cookie（如 `127.0.0.1:5173 -> 127.0.0.1:8080`），并新增 Datacenter Ratchet 最小后端契约 | datacenter 页面从 `404/403` 恢复到浏览器实测可用 |
| FE-DONE-20 | DONE | 共享 API 客户端已在收到 “CSRF token invalid or expired” 时自动刷新 token 并重试一次；Plaza 新建讨论回到共享客户端 | `api.test.js`, 浏览器 smoke |
| FE-DONE-21 | DONE | System Evolution 页面已修复 evolution 前缀常量、分页 envelope 消费，以及顶层 `api()` 对共享 `window.api` 的覆盖问题 | `system-evolution.test.js`, 浏览器 smoke |
| FE-DONE-22 | DONE | Plaza → Task → Evolution → verification queue 的后端 happy path 已有端到端回归，覆盖讨论演化、任务产物回写、人工验证项关闭 | `test_plaza_evolution_bridge.py` |
| FE-DONE-24 | DONE | `agent-team-config` 与 `datacenter-ratchet-evolution` 已补显式 auth guard，cookie-only 高优先级受保护页浏览器 smoke 覆盖完成 | 登录态 6 页打开 + 登出后 6 页回跳登录 |
| FE-DONE-23 | DONE | 共享 API 客户端在受保护 API 返回 401 时会统一跳回 `login.html?next=...`，登录页支持回跳原页面 | `api.test.js`, 浏览器 smoke |

### 2.3 后端平台质量

| 编号 | 状态 | 内容 | 说明 |
|------|:----:|------|------|
| BE-DONE-01 | DONE | CSRF token endpoint + middleware 已存在 | `/api/v1/auth/csrf-token` |
| BE-DONE-02 | DONE | login/register/logout/auth_me 已统一 auth mode、httpOnly `ag-token` cookie 与 token revoke；`/api/v1/**` 已补统一鉴权中间件；`./start.sh` 已补本地开发 admin 初始化，未登录访问受保护页依赖的 API 会返回 401，前端会回跳登录页 | 默认仍保留 token JSON 兼容旧客户端；固定 `admin123` 仅在显式 `AG_ALLOW_DEFAULT_ADMIN` 时启用 |
| BE-DONE-03 | DONE | health check 可注册子检查 | `/api/v1/health` |
| BE-DONE-04 | DONE | 分页 helper 与所有主要列表分页已落地 | 所有主要 list API 已覆盖 `limit/offset` |
| BE-DONE-05 | DONE | `src/backend/config.py` 已被 `main.py` 全面复用，支持 .env | 包含 server/auth/CORS/pagination/paths/logging/rate-limit 常量 |
| BE-DONE-07 | DONE | 安全响应头中间件 | X-Content-Type-Options / X-Frame-Options / Referrer-Policy / Permissions-Policy / HSTS |
| BE-DONE-08 | DONE | 结构化日志 + request_id middleware | `AG_LOG_FORMAT=json` + `X-Request-ID` 响应头 |
| BE-DONE-09 | DONE | Plaza 重试 + 失败升级 | LLM 3次重试+指数退避 + `_escalation_queue` + `/plaza/escalations` API |
| BE-DONE-06 | DONE | 后端默认测试入口已纳入核心测试 | 之前已解决 `src/backend/tests` 漏跑问题 |
| BE-DONE-10 | DONE | login/register 已有首批内存限流 | `test_auth_csrf.py` |
| BE-DONE-12 | DONE | 通用写请求 60/min + 敏感路由独立 bucket 已落地 | `test_api_rate_limit.py` |
| BE-DONE-11 | DONE | `main.py` 已接入可选 OTel tracing 初始化 | `monitoring/tracing.py` + startup hook |
| BE-DONE-13 | DONE | 本地快速启动会生成/复用 `config/.dev_admin_password` 并通过 `ADMIN_PASSWORD` 初始化 admin，避免 `./start.sh` 后登录 401 | `test_start_script_auth_bootstrap.py`, `bash -n start.sh` |

---

## 3. 总看板

状态定义：

- `DONE`：代码已落地，并至少有构建或测试护栏。
- `WIP`：主链已落地，但仍有明显验收缺口。
- `READY`：问题明确，下一步可直接开工。
- `BACKLOG`：确认存在，但优先级靠后。

| ID | 领域 | 状态 | 优先级 | 当前结论 | 下一步完成定义 |
|----|------|:----:|:------:|----------|----------------|
| SEC-01 | CSRF + Cookie Auth | DONE | P0 | cookie-only 模式、logout revoke、`X-AG-Auth-Mode` / token deprecation header、全局导航登出按钮、localStorage 清理、前端写请求 `_agFetch` 收口与 cookie-only 契约测试已落地；Datacenter Ratchet / Token Factory / Plaza TTS 的遗留 POST 也已补齐；高优先级受保护页的登录态 / 登出回跳浏览器 smoke 已完成；启动验证已适配受保护 API，`/api/v1/info` 保持公开发现；`./start.sh` 已补本地开发 admin bootstrap，避免快速启动后无账号可登录 | 低频页面继续随常规回归覆盖 |
| SEC-02 | API Key 传输安全 + 安全响应头 | DONE | P0 | 安全响应头中间件已落地（X-Content-Type-Options / X-Frame-Options / Referrer-Policy / Permissions-Policy / HSTS）；本地 at-rest 加密已完成 | 前端 API Key 输入 type=password、响应头断言测试 |
| SEC-03 | API Rate Limit | DONE | P1 | login/register 5/min、通用写请求 60/min、敏感路由独立 bucket 与回归测试均已落地 | 维持默认阈值，并在后续按生产流量再调参 |
| RUN-01 | Docker Sandbox 实机收口 | DONE | P0 | docker mode、Dockerfile、limits、runtime status、`build_sandbox_image.sh --self-check`、sandbox smoke、`test_sandbox_docker.py` 与专用 GitHub Actions workflow 均已落地；远端 `Sandbox Docker Self Check` 首轮运行已成功执行 image build、self-check、`DockerSandbox.run_python()` 与 `run_pytest()` 集成测试；缺 Docker 时 runtime status 仍会暴露 `docker_binary_path/self_check_blocked/ready_reason`，lite 模式 `runtime-self-check` 也已在当前解释器上通过 | 当前机器无 Docker，仅保留本地不可执行的环境说明；维持 fail-closed 与 blocked diagnostics |
| RUN-02 | 统一 AgentLoop 收口 | DONE | P0 | 共享 plan/tool runtime 已落地；同步 tool-loop 入口已统一到 `run_tool_loop_sync_with_provider`，旧 `AgentLoop` 已收窄成真正 shim；chat / task / plan 入口已有契约测试证明均复用共享 runtime | 保持兼容 shim 极薄，不再回退到第二套循环 |
| RUN-03 | State Machine + Watchdog | WIP | P1 | 独立状态机与 watchdog 模块已落地，但尚未成为所有 runtime 的唯一状态源 | 将 task/session/agent 主链切到统一状态机，并补 SSE 状态事件 |
| RUN-04 | Channels 真正消费 | WIP | P1 | Event bridge 已有，但 ChannelBus 还没成为默认协作通路 | 至少 2 个 Agent 通过 ChannelBus 自主对话并触发任务 |
| PLAZA-01 | Plaza 执行闭环 | DONE | P0 | 讨论 -> 任务 -> 产物 -> Evolution 已通；LLM 3次重试+指数退避；失败升级队列+API 已落地；计划面板已可见验证/升级状态；创建讨论 / 重新讨论 / 启动讨论已有生命周期回归测试；后端端到端 happy path 回归已补齐 | 继续保持浏览器 smoke 覆盖 |
| PLAZA-02 | Plaza 共识机制 | WIP | P2 | 共识分数、趋势、反方检测、`/consensus` API 已落地，前端计划面板已可见 | 把动态退出与 planner / 主讨论循环接起来 |
| PLAN-01 | UltraPlan / Planner | BACKLOG | P2 | 规则式 plan builder 仍偏硬编码 | 引入 LLM-driven / hybrid planner，失败可降级规则 |
| FE-01 | 前端运行时可见性 | WIP | P0 | Runtime / budget / trace / verification / Plaza consensus / escalations 已能从页面看到；主要错误 toast 和 trace drill-down 已可见 request_id；Datacenter Ratchet 页面后端契约已补齐并浏览器实测可用；高频受保护页 cookie-only 浏览器 smoke 已覆盖 6 页 | 继续补更细过滤、趋势图、跨页面上下文统一 |
| FE-02 | 前端模块边界 | WIP | P1 | 大页面大多已外抽；`agent-team-config.js` 已把 `tid/aid/wzD/wzS` 等历史裸全局切到 `window.AG.state` 属性代理，减少双向同步漂移 | 继续移除剩余裸全局别名，收口到少量公共 API |
| FE-03 | Plaza 3D 回流 | WIP | P1 | 气泡定位已改成仅在 camera/target 变化、文本变化、resize 时重排，并缓存容器/气泡尺寸 | 还需浏览器 smoke 验证长讨论场景下无漂移 |
| FE-04 | i18n key-based | WIP | P2 | `data-i18n` 与 `window.t(key)` 已开始接入，但 text-walker 仍是主机制 | 扩大 key-based 覆盖，逐步收缩 text-walker |
| FE-05 | Frontend Unit Tests | WIP | P1 | `api.js` 首批 Vitest 已补上，且 `scripts/frontend_build.sh` / `scripts/frontend_test.sh` 已恢复本机构建与测试可执行性 | 扩到 `utils.js`、Plaza 数据归一化、登录链和更多共享 helper |
| BE-01 | 列表 API 分页全覆盖 | DONE | P0 | 所有主要 list endpoint 已有 `limit/offset`；`skill-extract.js`、`system-evolution.js`、`tools-skills.js`、`plaza.js`、`tasks-view.js`、`agent-detail.js`、`agent-team-config.js`、`wizard.js` 与 `digital-twin-cli.js` 已切到共享 `api.list()` 或等价分页 helper，覆盖团队/智能体/技能/工具/任务、广场/讨论、SECS 团队任务与 evolution items 等主要分页读路径 | 维持统一消费方式，新增分页列表默认复用 `api.list()` |
| BE-02 | Pydantic 校验全面化 | DONE | P1 | `agent_team_api.py` 11 个 handler、`agents/api.py` 5 个 handler、`k8s_webhook_handler.py` 1 个 handler 已迁到 Pydantic request model；新增 request-model 回归覆盖约束、alias 与 dry-run 语义 | 后续新增 state-changing 路由默认沿用 request model |
| BE-03 | 配置集中管理 | DONE | P1 | `main.py` 已全部通过 `CONFIG_*` 引用 `config.py`；.env 支持已加 | 维护即可 |
| BE-04 | 后端测试覆盖提升 | WIP | P1 | 后端全量已恢复到可稳定跑通，GitHub Actions 已接上 `npm run test:backend`；`agent-team` 演化入口、`digital-twin` 主写接口、`health / teams / evolution / plaza` 主路径 HTTP smoke 已补齐；`test_api_integration_extended.py` 现已覆盖 auth/info/health/teams/agents/tools/skills/digital-twin/evolution 扩展 HTTP 契约，并修正了共享 TestClient 下 cookie / rate-limit 污染 | 继续补齐更深层的 auth/teams/plaza/evolution 集成测试 |
| OBS-01 | 结构化日志 + request_id | DONE | P1 | JSON 日志格式 (`AG_LOG_FORMAT=json`)、request_id middleware 已落地；前端 API 客户端已自动透传并缓存 `X-Request-ID`，主要页面错误 toast 与 trace drill-down 已显示 request_id | 继续扩大到更多页面和错误面板 |
| OBS-02 | OpenTelemetry / OTel Export | WIP | P2 | OTel tracing 模块、optional deps 与 startup hook 已落地；真实 exporter smoke 未做 | OTel span 在真实环境导出到 Jaeger/OTLP 并补测试 |
| DATA-01 | 会话存储升级 | BACKLOG | P2 | JSON 文件 / 内存状态仍多 | SQLite + 索引 + 后续向量检索 |
| DEPLOY-01 | 多实例部署 | BACKLOG | P3 | 进程内事件总线和内存状态限制横向扩展 | 外部 MQ / Redis PubSub / DB-backed session |

---

## 4. P0 出关条件

P0 不要求“全项目完美”，但要求下面几件事可靠：

| 条件 | 当前状态 | 出关标准 |
|------|:--------:|----------|
| 安全认证 | DONE | cookie-only 模式可开启；CSRF 对 state-changing 请求稳定生效；旧 token 返回可关闭；本地快速启动可获得可登录 admin；高优先级受保护页登录态 / 登出回跳浏览器 smoke 已完成 |
| 沙箱执行 | DONE | docker image 可构建；`run_python/run_pytest` 已在 docker 模式通过远端 workflow 集成测试 |
| Runtime 单一入口 | DONE | 旧 AgentLoop 已不再保留独立逻辑；chat / task / plan 入口统一复用共享 runtime，并有回归测试护栏 |
| Plaza/Evolution 闭环 | DONE | 成功、失败、人工验证、重试耗尽都有状态、trace、前端可见；浏览器端已再次跑通 Plaza 新建讨论/开始讨论 与 Evolution 审查/周期 |
| 列表分页 | DONE | 所有主要无限增长列表接口都有硬上限与 `limit/offset` |
| 前端可验收 | WIP | 页面主路径已可见 budget、trace、runtime、verification；本机 build/vitest 已可通过 bundled-node fallback 运行，剩更多前端测试扩面 |

当前判断：**P0 功能主链已完成**。Docker 沙箱远端首轮 workflow 已跑通真容器路径，认证、Plaza / Evolution 浏览器 smoke 和分页主链也都已完成 P0 范围收口。后续重点转到 P1：补测试、收全局状态、把状态机与 ChannelBus 真正接进主 runtime。

---

## 5. 下一批连续执行队列

### 5.1 立即执行（P1）

| 顺序 | ID | 任务 | 涉及文件 | 验证 |
|------|----|------|----------|------|
| 1 | BE-04 | 后端 API handler 测试扩面 | `src/backend/tests/*`, `src/backend/agents/api.py`, `src/backend/agent_team_api.py` | `pytest src/backend/tests --maxfail=1` |
| 2 | FE-02 | 全局状态清理 | `src/frontend/js/agent-team-config.js`, `src/frontend/js/*.js` | `frontend_build.sh` + 页面 smoke |

### 5.2 紧接执行（P1）

| ID | 任务 | 完成定义 |
|----|------|----------|
| BE-02 | Pydantic 校验全面化 | 所有 state-changing handler 有 request model |
| BE-04 | 后端 API handler 测试 | auth/health/teams/plaza/evolution 主接口有集成测试 |
| FE-02 | 全局状态清理 | `agent-team-config.js` 只暴露少量公共 API |
| FE-05 | Vitest 测试扩面并恢复本机执行 | 先修复 Rollup 原生模块阻塞，再扩到 `utils.js`、登录链、Plaza helper |
| OBS-01 | JSON log + request_id | 前端请求已透传 `X-Request-ID`；Agent Team / Plaza / Evolution 错误提示和 Agent Team trace drill-down 已可见 |
| RUN-03 | 状态机接入主 runtime | task/session/agent 生命周期统一走状态机与 watchdog |

### 5.3 后续增强（P2/P3）

| ID | 任务 | 价值 |
|----|------|------|
| PLAN-01 | Hybrid Planner | 让 AgentLoop 从规则式计划升级为可解释规划 |
| PLAZA-02 | Plaza 共识机制 | 把共识分数真正用于动态退出与 planner 决策 |
| FE-04 | key-based i18n | 用 `data-i18n` / `window.t()` 逐步替代 text-walker |
| OBS-02 | OpenTelemetry | 真实 exporter smoke、span 命名规范与部署文档 |
| RUN-04 | ChannelBus 演示闭环 | 做出 2-agent 自主对话 / 触发任务的端到端演示 |
| DATA-01 | SQLite session store | 长期会话、检索、性能 |
| DEPLOY-01 | 多实例支持 | 横向扩展 |

---

## 6. 前端优化总表

| 分类 | 已完成 | 剩余 |
|------|--------|------|
| 安全 | XSS 转义、CSRF-ready API、CSP、client error tracking | cookie-only auth UI 收口、API Key 传输策略 |
| 架构 | 多页面 JS 外抽、共享 API、共享导航、CSS variables | 全局状态收口、继续拆大型模块 |
| 可见性 | Plaza/Sandbox/Evolution/AgentTeam/PortRuntime 已消费运行时能力；Plaza 计划面板已显示 verification / consensus / escalations；Agent Team trace 面板已可展开 task 明细 | 更细 trace 过滤、更长趋势、跨页统一 drill-down |
| 性能 | hidden 检查、部分增量刷新、sandbox resize 优化 | Plaza 3D 回流、overview 聚合端点 |
| 可访问性 | skip-link、aria-current、aria-live、部分 role | 全页面统一 audit |
| i18n | `data-i18n` / `window.t(key)` 已开始接入 | 逐步替换 text-walker 主路径 |
| 测试 | `api.js` / `csrf-pages` / `extract-routing` / `agent-config` 测试文件已在仓库，且可通过 bundled-node fallback 稳定执行 | 继续扩到 `utils.js`、登录链、Plaza helper |

---

## 7. 后端优化总表

| 分类 | 已完成 | 剩余 |
|------|--------|------|
| Auth | PBKDF2、users 持久化、httpOnly cookie、CSRF endpoint/middleware、cookie-only 开关、logout revoke、全局导航登出按钮 | cookie-only 模式全页面验收与生产 secure-cookie rollout |
| 安全执行 | LiteSandbox、DockerSandbox scaffold、permissions 执行前拦截、安全响应头中间件、通用 API rate limit | docker 实机验证 |
| Runtime | 共享 plan/tool runtime、events、budget、trace、状态机与 watchdog 模块 | 旧 AgentLoop shim 收束、状态机接入主 runtime、ChannelBus 主链化 |
| Plaza/Evolution | task/artifact/diff/test_result/verification 回写、LLM 重试+退避+失败升级队列 | 前端升级状态面板、浏览器 smoke |
| API 质量 | 全部分页、健康检查增强、配置模块完成、.env 支持 | Pydantic 全面化 |
| Observability | trace JSONL、recent/export API、JSON 结构化日志、request_id middleware、前端 `X-Request-ID` 透传、可选 OTel tracing 模块 | OTel exporter smoke、页面级展示 request_id |
| 测试 | 后端测试基线已全绿过 | 新增 auth/pagination/runtime/e2e 覆盖 |

---

## 8. 风险与回滚

| 风险 | 触发场景 | 回滚策略 |
|------|----------|----------|
| cookie-only auth 影响旧页面 | 旧页面仍读 JSON token | 保留兼容开关 `AG_AUTH_RETURN_TOKEN_JSON=1`，逐页迁移后关闭 |
| Docker sandbox 在本机不可用 | 未安装 Docker 或镜像缺失 | `lite` 作为开发模式，生产 `docker` fail-closed |
| 统一 AgentLoop 引入回归 | 旧调用依赖同步行为 | 旧 `AgentLoop` 文件保留薄 shim，测试覆盖入口行为 |
| 分页改动破坏前端 | 前端仍假设数组返回 | API 短期支持 `{items,total}` 与旧数组兼容层 |
| Plaza 3D 性能优化影响气泡定位 | camera / resize 事件未覆盖 | 保留手动 `positionAllBubbles()` fallback |
| 本机前端验证环境漂移 | `node_modules` 中 Rollup 原生模块签名 / optional dependency 异常 | 当前已通过 bundled-node fallback 绕过；后续再决定是否重装 `node_modules` / 修复系统 Node 工具链 |
| 后端回归缺少远端护栏 | 本地回归绿、远端无人看守 | GitHub Actions 已接入 `npm run test:backend`，继续观察首轮远端执行结果 |

---

## 9. 维护规则

1. 每完成一个 TODO，立即更新本文件对应状态。
2. 新增工作项必须有：`ID / 状态 / 优先级 / 涉及文件 / 验收方式`。
3. 不再新增按 Week 的排期；只维护连续执行队列。
4. 提交前至少运行：

```bash
rtk npm run build
rtk npx vitest run src/frontend/__tests__/api.test.js
rtk python3 -m pytest -q src/backend/tests --maxfail=1
```

5. `.huashu-skills` 不纳入此计划，不提交、不修改。

---

## 10. 本轮整合记录

- 合并 `FrontBackEndOptimize.md` 的问题分类与旧风险。
- 合并 `FrontBackEndTodos.md` 的已完成前端工程化结果。
- 合并 `OptimizePlan1.md` 的前后端全貌、S1/S2/S3 待办。
- 合并 `OptimizePlan1Todos.md` 的 FE/BE 任务编号。
- 结合当前代码核对了 CSRF、cookie auth、pagination、health、frontend runtime visibility、Plaza/Evolution trace 等实际状态。
- `FrontEndOptimize.md` 未在仓库中找到，已在文档顶部注明。
- 本轮新增了 cookie-only auth 回归、前端 cookie-only 契约测试、高频写请求 `_agFetch` 收口、sandbox smoke / docker integration / GitHub Actions workflow，以及 `api.js` 的 Vitest 护栏。
- 本轮补齐了成本域与模板变体测试的当前契约，并恢复后端全量基线；当前最新稳定基线为 `906 passed, 4 skipped`。
- 本轮新增 GitHub Actions 后端回归工作流，使用 `npm run test:backend` 作为远端护栏入口。
- 本轮确认 `Sandbox Docker Self Check` 远端首轮运行成功，P0 的 Docker 真容器验收已完成；同时补齐了 BE-02 的 request-model 回归，并把 `agent-team-config.js` 的历史裸全局切到 `window.AG.state` 属性代理。
- 本轮为 `agent-team` 演化入口和 `digital-twin` 主写接口补上了 HTTP 级集成测试，并在测试夹具里清理全局 channel/rate-limit 状态，避免污染后续后端测试模块。
- 本轮继续扩面 `BE-04`：新增 `health / teams / evolution / plaza` 主路径 HTTP smoke，验证未登录 401、登录后 200，以及 Plaza 创建的最短正向路径。
- 本轮继续扩面 `BE-04`：补上 logout 后受保护接口重新 401、`evolution/audit` 与 `evolution/cycle` 的写路径，以及 Plaza discussion 创建/summary 的 HTTP 级正向链路，并在测试结束后清理临时广场。
- 本轮推进 `BE-P0-01` 收尾：`system-evolution.js` 已改用共享 `api.list()` 消费 `items / rules / audit-trail / history / optimize-runs` 分页接口，并补上前端回归，避免再次手写 `?limit=` 拼接。
- 本轮继续推进 `BE-P0-01` 收尾：`tools-skills.js` 已改用共享 `api.list()` 消费团队工具、团队技能与全局技能/工具列表，并新增前端回归，避免再次直接依赖全量数组响应。
- 本轮继续推进 `BE-P0-01` 收尾：`plaza.js` 已改用共享 `api.list()` 消费广场列表、团队树与讨论列表，并新增最小前端回归，避免再次直接手写分页或依赖详情接口内嵌列表。
- 本轮继续推进 `BE-P0-01` 收尾：`tasks-view.js` 已改用共享 `api.list()` 消费团队任务列表，覆盖工作流轮询、任务表加载与批量清理前置读取，并新增最小前端回归，避免再次直接依赖全量数组响应。
- 本轮继续推进 `BE-P0-01` 收尾：`agent-detail.js` 已改用共享 `api.list()` 消费工具、团队技能与会话列表，并新增最小前端回归；`logs` 仍保留单独读法，因为后端返回的是 `{agent_id, logs}` 而不是标准分页 envelope。
- 本轮继续推进 `BE-P0-01` 收尾：`agent-team-config.js` 已改用共享 `api.list()` 消费团队列表、嵌入式 evolution 的 items/rules、LLM 会话、模型列表，以及导出配置所需的 models/tools/skills；`wizard.js` 也已切到共享 `api.list()` 消费团队、模型、技能和工具列表，并补上两条最小前端回归。
- 本轮修复启动验证：`/api/v1/info` 已加入 auth exempt，用于系统发现；`startup_validator` 对受保护的 Agent Config / Bridge Chat / Evolution API 不再把 `401` 误判为模块失败，而是回退到公开 `/api/v1/health` 的服务注册状态。
- 本轮修复本地登录初始化：`./start.sh` 会生成/复用 `config/.dev_admin_password`，并通过 `ADMIN_PASSWORD` 初始化 `admin`，避免快速启动后登录接口因无 admin 账号返回 `401`；固定 `admin123` 仍只在显式 `AG_ALLOW_DEFAULT_ADMIN` 时启用。
- 本轮补齐 `digital-twin-cli.js` 的分页消费收口：广场列表与讨论列表已切到共享分页 helper，连同原先已接好的团队/智能体/技能/工具/任务/evolution/SECS 列表一起，把前端主要分页读路径统一到 `api.list()` 语义，并新增 `digital-twin-cli-pagination.test.js` 回归。
- 本轮收口 `test_api_integration_extended.py`：通过清理共享 TestClient 下的 cookie / rate-limit 状态，修正匿名保护断言与注册限流串扰；同时把 `health` 断言对齐到真实 payload，并补了 `/api/v1/info` 公开发现与 `auth/me` 匿名/已登录主路径检查。
