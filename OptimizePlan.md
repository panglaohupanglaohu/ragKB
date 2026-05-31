# OptimizePlan — 前后端整体优化总看板

> 更新日期：2026-05-31  
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

2. **前端工程化**已经从“大量内联脚本 + 页面重复逻辑”推进到更清晰的多页模块体系：
   - 统一 API 客户端、全局导航、共享 utils、CSS variables 已出现。
   - 多个大页面 JS 已外抽。
   - Plaza / Sandbox / Evolution / Agent Team / PortRuntime 已开始消费后端运行时能力。

但还不能宣布“整体优化完成”。当前真正剩下的高价值缺口是：

- 安全：cookie-only auth、CSRF token 生命周期、API Key 传输安全、速率限制仍需收口。
- 运行时：Docker sandbox 需要实机验证；AgentLoop 仍有兼容层；channels / state watchdog 还未完全成为核心运行机制。
- 前端：模块化已经做了大半，但全局状态、i18n key-based、Vitest、Plaza 3D 回流仍需继续。
- 后端：分页落地不均匀；Pydantic 校验和结构化日志还不完整。
- 可观测：trace 已有查询和导出，但还不是 OpenTelemetry / request_id / 生产日志体系。

---

## 1. 当前验收快照

| 维度 | 当前状态 | 说明 |
|------|:--------:|------|
| 前端构建 | ✅ 通过 | 本轮验证：`rtk npm run build` 通过；仍有 Vite warning |
| 后端测试 | ✅ 已有基线 | 最近已知后端全量：`613 passed`；当前有后端文件变更，提交前需重跑 |
| 前端规模 | 19 JS / 11 HTML / 6 CSS | 以当前 `src/frontend` 文件统计为准 |
| 后端规模 | 147 Python / 25 backend tests | 以当前 `src/backend` 文件统计为准 |
| `.huashu-skills` | 不纳入 | 用户明确要求一直不动 |

已知构建 warning：

- 多个 HTML 页面仍有非 `type="module"` 脚本不能被 Vite bundle 的 warning。
- 当前 CSS minify 阶段有一处语法 warning：`Expected ":"`，需在后续前端 CSS 收口时定位。

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
| R-11 | WIP | 共享 tool runtime + plan runtime 已落地，旧入口仍有兼容层 | `test_unified_tool_loop.py`, `test_plan_loop_runtime.py` |
| R-12 | WIP | token budget / usage 已接入 chat / stream，并有 API 与前端面板 | `test_token_budget.py` |
| R-13 | WIP | LiteSandbox + DockerSandbox 入口、limits、self-check 已有；docker 实机验证待补 | `test_sandbox_security.py` |

### 2.2 前端工程化

| 编号 | 状态 | 内容 | 说明 |
|------|:----:|------|------|
| FE-DONE-01 | DONE | XSS 修复覆盖多处 innerHTML 拼接 | `escapeHtml()` / `esc()` 已广泛使用 |
| FE-DONE-02 | DONE | 统一 API 客户端 `src/frontend/js/api.js` | CSRF-ready、离线检测、分页辅助 |
| FE-DONE-03 | DONE | 全局导航 `src/frontend/js/global-nav.js` | 多页面不再重复硬编码导航 |
| FE-DONE-04 | DONE | CSS variables 提取 | `src/frontend/css/variables.css` |
| FE-DONE-05 | DONE | 多个大页面 JS 外抽 | Plaza / Sandbox / System Evolution / Skill Extract / Digital Twin 等 |
| FE-DONE-06 | DONE | CSP meta、client error tracking、可访问性与 i18n 基础增强 | 仍需 key-based i18n |
| FE-DONE-07 | DONE | Plaza 前端消费 verification queue / alerts / SSE broadcast | 可在计划面板运行验证队列 |
| FE-DONE-08 | DONE | Sandbox 前端消费 runtime-status / runtime-self-check | 可看 readiness、limits、自检 |
| FE-DONE-09 | DONE | Evolution 前端展示 verify detail / retry / escalation | 演进条目表可见 |
| FE-DONE-10 | DONE | Agent Team 前端展示 budget / alerts / trends / trace / drill-down | 支持 NDJSON 导出和 deep-link |
| FE-DONE-11 | DONE | PortRuntime 前端展示 Agent Loop plan / runtime events | 可直接看共享 runtime 事件序列 |

### 2.3 后端平台质量

| 编号 | 状态 | 内容 | 说明 |
|------|:----:|------|------|
| BE-DONE-01 | DONE | CSRF token endpoint + middleware 已存在 | `/api/v1/auth/csrf-token` |
| BE-DONE-02 | WIP | login/register 设置 httpOnly `ag-token` cookie | 仍返回 token JSON 兼容旧客户端 |
| BE-DONE-03 | DONE | health check 可注册子检查 | `/api/v1/health` |
| BE-DONE-04 | WIP | 分页 helper 与部分列表分页已落地 | 仍需覆盖所有列表 API |
| BE-DONE-05 | WIP | `src/backend/config.py` 已出现 | `main.py` 仍有重复常量 |
| BE-DONE-06 | DONE | 后端默认测试入口已纳入核心测试 | 之前已解决 `src/backend/tests` 漏跑问题 |

---

## 3. 总看板

状态定义：

- `DONE`：代码已落地，并至少有构建或测试护栏。
- `WIP`：主链已落地，但仍有明显验收缺口。
- `READY`：问题明确，下一步可直接开工。
- `BACKLOG`：确认存在，但优先级靠后。

| ID | 领域 | 状态 | 优先级 | 当前结论 | 下一步完成定义 |
|----|------|:----:|:------:|----------|----------------|
| SEC-01 | CSRF + Cookie Auth | WIP | P0 | CSRF endpoint/middleware 与 httpOnly cookie 已有；仍返回 token JSON 兼容旧客户端 | 增加 cookie-only 模式、logout、token JSON deprecation 开关和回归测试 |
| SEC-02 | API Key 传输安全 | READY | P0 | 本地 at-rest 加密已完成；传输层仍依赖部署 HTTPS | 明确 HTTPS 强制、生产安全头、必要时加前端 envelope encryption |
| SEC-03 | API Rate Limit | READY | P1 | 登录/注册和通用 API 还没有统一限流 | login/register 5/min；通用 API 60/min；测试覆盖 |
| RUN-01 | Docker Sandbox 实机收口 | WIP | P0 | docker mode、Dockerfile、limits、self-check 已有 | CI/本机能 build image 并跑安全用例；缺 docker 时 fail-closed |
| RUN-02 | 统一 AgentLoop 收口 | WIP | P0 | 共享 plan/tool runtime 已落地；兼容 shim 仍存在 | 所有入口只复用统一 runtime，旧类薄封装并标 deprecation |
| RUN-03 | State Machine + Watchdog | READY | P1 | state 字段仍偏松散 | 统一状态机、超时 watchdog、SSE 状态变更事件 |
| RUN-04 | Channels 真正消费 | BACKLOG | P1 | channels 定义仍未成为跨 Agent 消息总线核心 | 至少 2 个 Agent 通过 ChannelBus 自主对话并触发任务 |
| PLAZA-01 | Plaza 执行闭环 | WIP | P0 | 讨论 -> 任务 -> 产物 -> Evolution 已通 | 补自动重试策略、失败升级 UI、更多端到端测试 |
| PLAZA-02 | Plaza 共识机制 | BACKLOG | P2 | 当前仍偏轮播讨论 | 加共识度量、反方意见、动态退出 |
| PLAN-01 | UltraPlan / Planner | BACKLOG | P2 | 规则式 plan builder 仍偏硬编码 | 引入 LLM-driven / hybrid planner，失败可降级规则 |
| FE-01 | 前端运行时可见性 | WIP | P0 | Runtime / budget / trace / verification 已能从页面看到 | 继续补 drill-down 过滤、趋势图、跨页面上下文统一 |
| FE-02 | 前端模块边界 | WIP | P1 | 大页面大多已外抽；仍有全局状态和大型模块 | 收口 `tid/aid/wzD/wzS` 等全局变量，统一 namespace |
| FE-03 | Plaza 3D 回流 | READY | P1 | 当前仍可见每帧 `positionSpeechBubble()` | 只在 camera/内容变化时更新，缓存 `getBoundingClientRect()` |
| FE-04 | i18n key-based | READY | P2 | 已有大量翻译，但 text-walker 仍是主机制 | 引入 `data-i18n` + `window.t(key)`，保留旧 map 兼容 |
| FE-05 | Frontend Unit Tests | READY | P1 | 还没有 Vitest 护栏 | Vitest + `utils.js` / `api.js` 首批测试 |
| BE-01 | 列表 API 分页全覆盖 | WIP | P0 | 部分 Evolution / Plaza / Operation API 已分页 | 所有 list endpoint 有 `limit/offset` 或 cursor，前端分页消费 |
| BE-02 | Pydantic 校验全面化 | READY | P1 | 仍有 route 使用 raw dict | POST/PUT/PATCH 全部 request model 化 |
| BE-03 | 配置集中管理 | WIP | P1 | `config.py` 已有，`main.py` 仍重复常量 | `main.py` 常量迁移到 `config.py`，`.env` 支持 |
| BE-04 | 后端测试覆盖提升 | READY | P1 | 25 个测试文件，API handler 覆盖仍不均匀 | login/register/health/teams/plaza/evolution 集成测试补齐 |
| OBS-01 | 结构化日志 + request_id | READY | P1 | trace events 已有，应用日志仍非 JSON 标准 | JSON log、request_id、错误脱敏、前后端关联 |
| OBS-02 | OpenTelemetry / OTel Export | BACKLOG | P2 | 目前是本地 JSONL trace | OTel span 覆盖 LLM/tool/task/plaza，支持 Jaeger/OTLP |
| DATA-01 | 会话存储升级 | BACKLOG | P2 | JSON 文件 / 内存状态仍多 | SQLite + 索引 + 后续向量检索 |
| DEPLOY-01 | 多实例部署 | BACKLOG | P3 | 进程内事件总线和内存状态限制横向扩展 | 外部 MQ / Redis PubSub / DB-backed session |

---

## 4. P0 出关条件

P0 不要求“全项目完美”，但要求下面几件事可靠：

| 条件 | 当前状态 | 出关标准 |
|------|:--------:|----------|
| 安全认证 | WIP | cookie-only 模式可开启；CSRF 对 state-changing 请求稳定生效；旧 token 返回可关闭 |
| 沙箱执行 | WIP | docker image 可构建；`run_python/run_pytest` 在 docker 模式跑通安全测试 |
| Runtime 单一入口 | WIP | 旧 AgentLoop 不再有独立逻辑，只保留兼容调用 |
| Plaza/Evolution 闭环 | WIP | 成功、失败、人工验证、重试耗尽都有状态、trace、前端可见 |
| 列表分页 | WIP | 所有可能无限增长的列表接口有硬上限 |
| 前端可验收 | WIP | 不手调 API 也能从页面看到 budget、trace、runtime、verification 状态 |

当前判断：**P0 约 75%-85% 完成**。剩余卡点主要是 docker 实机验收、cookie-only auth 收口、分页全覆盖、旧 AgentLoop compatibility 收束。

---

## 5. 下一批连续执行队列

### 5.1 立即执行（P0）

| 顺序 | ID | 任务 | 涉及文件 | 验证 |
|------|----|------|----------|------|
| 1 | RUN-01 | Docker sandbox 实机验证与脚本收口 | `docker/sandbox/*`, `scripts/build_sandbox_image.sh`, `src/backend/sandbox/*` | sandbox security tests + self-check |
| 2 | SEC-01 | cookie-only auth 模式 + logout + token JSON deprecation 开关 | `src/backend/main.py`, `src/frontend/login.html`, `src/frontend/js/api.js` | auth/CSRF 回归 |
| 3 | BE-01 | 所有 list API 分页全覆盖 | `src/backend/agent_team_api.py`, `src/backend/agents/api.py`, `src/backend/agents/plaza_routes.py` | API tests |
| 4 | RUN-02 | 收窄旧 AgentLoop shim | `src/backend/agents/agent_loop.py`, `src/backend/agents/runtime/*`, `src/backend/agents/chat_harness.py` | runtime tests |
| 5 | FE-03 | Plaza 3D 回流优化 | `src/frontend/js/plaza.js` | build + 浏览器 smoke |

### 5.2 紧接执行（P1）

| ID | 任务 | 完成定义 |
|----|------|----------|
| BE-02 | Pydantic 校验全面化 | 所有 state-changing handler 有 request model |
| BE-03 | 配置集中管理 | `main.py` 不再重复核心配置常量 |
| BE-04 | 后端 API handler 测试 | auth/health/teams/plaza/evolution 主接口有集成测试 |
| FE-02 | 全局状态清理 | `agent-team-config.js` 只暴露少量公共 API |
| FE-05 | Vitest 首批测试 | `utils.js`、`api.js` 有 mock 测试 |
| OBS-01 | JSON log + request_id | 单次请求可串到后端 log、trace、前端错误 |
| SEC-03 | API rate limit | 登录/注册和通用 API 有限流 |

### 5.3 后续增强（P2/P3）

| ID | 任务 | 价值 |
|----|------|------|
| PLAN-01 | Hybrid Planner | 让 AgentLoop 从规则式计划升级为可解释规划 |
| PLAZA-02 | Plaza 共识机制 | 减少无效轮播，提高协作质量 |
| FE-04 | key-based i18n | 翻译质量和维护性 |
| OBS-02 | OpenTelemetry | 生产级调用链 |
| DATA-01 | SQLite session store | 长期会话、检索、性能 |
| DEPLOY-01 | 多实例支持 | 横向扩展 |

---

## 6. 前端优化总表

| 分类 | 已完成 | 剩余 |
|------|--------|------|
| 安全 | XSS 转义、CSRF-ready API、CSP、client error tracking | cookie-only auth UI 收口、API Key 传输策略 |
| 架构 | 多页面 JS 外抽、共享 API、共享导航、CSS variables | 全局状态收口、继续拆大型模块 |
| 可见性 | Plaza/Sandbox/Evolution/AgentTeam/PortRuntime 已消费运行时能力 | 更细 trace 过滤、更长趋势、跨页统一 drill-down |
| 性能 | hidden 检查、部分增量刷新、sandbox resize 优化 | Plaza 3D 回流、overview 聚合端点 |
| 可访问性 | skip-link、aria-current、aria-live、部分 role | 全页面统一 audit |
| i18n | 字典扩展 | key-based 绑定 |
| 测试 | 构建通过 | Vitest 未建 |

---

## 7. 后端优化总表

| 分类 | 已完成 | 剩余 |
|------|--------|------|
| Auth | PBKDF2、users 持久化、httpOnly cookie、CSRF endpoint/middleware | cookie-only 模式、logout、token JSON 下线策略 |
| 安全执行 | LiteSandbox、DockerSandbox scaffold、permissions 执行前拦截 | docker 实机验证、API rate limit |
| Runtime | 共享 plan/tool runtime、events、budget、trace | 旧 AgentLoop shim 收束、state watchdog |
| Plaza/Evolution | task/artifact/diff/test_result/verification 回写 | 自动重试策略、失败升级策略继续补强 |
| API 质量 | 部分分页、健康检查增强、配置模块起步 | 分页全覆盖、Pydantic 全面化、配置完全迁移 |
| Observability | trace JSONL、recent/export API、前端消费 | JSON logging、request_id、OTel |
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

---

## 9. 维护规则

1. 每完成一个 TODO，立即更新本文件对应状态。
2. 新增工作项必须有：`ID / 状态 / 优先级 / 涉及文件 / 验收方式`。
3. 不再新增按 Week 的排期；只维护连续执行队列。
4. 提交前至少运行：

```bash
rtk npm run build
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
