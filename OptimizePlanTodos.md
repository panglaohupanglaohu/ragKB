# OptimizePlan — 前后端统一 TODOs

> 基于 `OptimizePlan.md`（总看板）+ 当前代码状态生成的最新待办清单。
> 更新日期：2026-06-02（已按源码核对状态）
> 覆盖范围：`src/frontend/` + `src/backend/` + AI runtime / Plaza / Evolution / Sandbox / Skill
> 原则：不再按 S1/S2/S3 分阶段，按 P0/P1/P2 优先级组织。

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
| SEC-03 | API 限流 | login/register 内存限流 5 次/分钟（`test_auth_csrf.py`） |
| RUN-01-code | Docker Sandbox 代码 | `DockerSandbox` + `docker/sandbox/Dockerfile` + 缺 docker fail-closed（实机验收待补） |
| BE-03-2 | config.py 落地 | `src/backend/config.py` 提供 server/auth/CORS/pagination/paths/logging 常量并被引用 |
| FE-10 | Vitest 单测 | `__tests__/utils|api|agent-config.test.js` + `vitest 4.1.7` + `npm run test:frontend` |
| SEC-01-6 | 登出按钮 | `global-nav.js` 全局导航注入登出按钮 + `api.logout()` 调用 |
| SEC-02 | 安全响应头 | `main.py` 中间件: X-Content-Type-Options / X-Frame-Options / Referrer-Policy / Permissions-Policy / HSTS(环境变量开启) |
| OBS-01-1 | 结构化日志 | `AG_LOG_FORMAT=json` 切换 JSON 行日志；`LOG_LEVEL` 环境变量控制级别 |
| OBS-01-2 | request_id | 每请求生成 `X-Request-ID`（或接受上游传入），注入 `request.state` |
| BE-03-3 | config.py .env | `config.py` 加入 python-dotenv 支持；新增 `RATE_LOGIN_LIMIT` / `RATE_LIMIT_WINDOW` 配置项 |
| BE-P0-01 | 分页补齐 | `/skills/required` / `/templates` / `/tools/execution-history` / `/skill-library` / `/skill-library/suggestions` / `/skills/search` / `/tools/search` 全部加 `limit/offset` |
| PLAZA-01 | 重试+升级 | `plaza_engine._generate_agent_content` 3次重试+指数退避；`_escalation_queue` 失败升级队列；`/plaza/escalations` API |

---

## P0 — 安全与运行时底座

> 这些是出关必要条件，不完成就不能说系统可用。

### RUN-01 🔴 Docker Sandbox 实机收口

```
位置: src/backend/sandbox/python_runner_docker.py, docker/sandbox/, scripts/
难度: ⚡⚡ 大   优先级: P0
状态: WIP — DockerSandbox 类、Dockerfile、limits、self-check、fail-closed 均已有，缺实机验收
```

- [x] docker mode、Dockerfile、limits、self-check 代码已备
- [x] 缺 docker 时 fail-closed（返回 `SandboxResult(ok=False)`）
- [ ] CI/本机实机 build sandbox docker image
- [ ] `run_python` / `run_pytest` 在 docker 模式跑通所有安全测试
- [ ] 添加 `test_sandbox_docker.py` 集成测试
- [ ] 前端 sandbox 页面显示当前 sandbox mode（lite/docker）

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
- [ ] cookie-only 模式下所有页面验收

### RUN-02 🔴 统一 AgentLoop 收窄

```
位置: src/backend/agents/agent_loop.py, src/backend/agents/runtime/*, src/backend/agents/chat_harness.py
难度: ⚡⚡ 大   优先级: P0
状态: WIP — `agent_loop.py` 已标注 deprecated 薄 shim，runtime 拆分已完成，需最后确认无残留逻辑
```

- [x] runtime 拆分 `runtime/plan_loop.py` + `runtime/tool_loop.py`
- [x] 旧 `agent_loop.py` 标注 deprecated shim
- [ ] 确认所有入口（chat / task / plan）只复用统一 runtime，无残留独立逻辑
- [ ] 覆盖所有入口行为的回归测试

### PLAZA-01 � Plaza 闭环：重试与失败升级

```
位置: src/backend/agents/plaza_engine.py, src/backend/agents/plaza_routes.py
难度: ⚡ 中   优先级: P0
状态: DONE — 重试+退避+升级队列+API 已落地
```

- [x] LLM 调用自动重试（3 次 + 指数退避 1.5s/3s/6s）
- [x] 重试耗尽后的失败升级（`_escalation_queue` + `_escalate_failure()`）
- [x] 升级队列 API（`GET /plaza/escalations` + `POST /plaza/escalations/{index}/resolve`）
- [ ] 前端计划面板可见重试/升级状态
- [ ] 端到端回归测试

### BE-P0-01 � 列表 API 分页补齐（存量）

```
位置: src/backend/agents/api.py
难度: ⚡ 小   优先级: P0
状态: DONE — 所有主要裸数组端点已补齐 limit/offset
```

- [x] 审查 `agents/api.py` 中仍返回裸 list 的端点
- [x] 补上 `limit/offset`：`/skills/required` / `/templates` / `/tools/execution-history` / `/skill-library` / `/skill-library/suggestions` / `/skills/search` / `/tools/search`
- [ ] 前端 `api.list()` 在分页 API 上统一消费

---

## P1 — 质量加固

### SEC-02 � 生产安全响应头

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
- [ ] CI 配置 `npm run test:backend`

### BE-03 � main.py 常量迁移到 config.py

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

### OBS-01 � 结构化日志 + request_id

```
位置: src/backend/main.py
难度: ⚡ 中   优先级: P1
状态: DONE — JSON 日志 + request_id middleware 已落地
```

- [x] 日志格式改为 JSON 行输出（`AG_LOG_FORMAT=json`）
- [x] 日志级别通过环境变量配置（`LOG_LEVEL`）
- [x] 为每个请求添加 request_id（`request_id_middleware`，响应头 `X-Request-ID`）
- [ ] 单次请求可串联到后端 log、trace、前端错误（需前端传递 request_id）

---

## P2 — 体验增强

### FE-08 🟡 i18n 绑定到 UI

```
位置: 多个 JS 文件
难度: ⚡ 中   优先级: P2
状态: PARTIAL — 侧栏导航已标记 data-i18n，DICT 已注册翻译键
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
状态: DONE — 统一状态机 + TimeoutWatchdog + 测试
```

- [x] 统一状态机定义（AgentState / TaskState / SessionState 转换图）
- [x] 超时 watchdog（TimeoutWatchdog 自动转换过期状态）
- [x] 回调机制 on_transition（可接 SSE 推送）
- [ ] SSE 状态变更事件（需前端对接）

### RUN-04 🔵 Channels 真正消费

```
位置: src/backend/channels/event_bridge.py
难度: ⚡⚡ 大   优先级: P2
状态: DONE — ChannelEventBridge 实现 EventBus↔Channel 桥接
```

- [x] channels 成为 runtime 事件总线的一等公民（ChannelEventBridge）
- [x] 支持 inter-agent 消息 send_agent_message()
- [x] 支持 channel 触发任务 trigger_task()
- [ ] 至少 2 个 Agent 通过 ChannelBus 自主对话端到端演示

### PLAZA-02 🔵 Plaza 共识机制

```
位置: src/backend/agents/plaza_consensus.py, plaza_routes.py
难度: ⚡⚡ 大   优先级: P2
状态: DONE — 共识度量 + 反方检测 + API 端点
```

- [x] 共识度量（measure_consensus → score/trend/can_early_exit）
- [x] 反方意见机制（highlight_dissent 自动检测强反对）
- [x] API 端点 GET /plaza/{id}/discussions/{id}/consensus
- [ ] 动态退出（参与者可在一定条件下自动离场）

### OBS-02 🔵 OpenTelemetry / OTel Export

```
位置: src/backend/monitoring/tracing.py
难度: ⚡⚡ 大   优先级: P2
状态: DONE — 模块完成，NoOp fallback，AG_OTEL_ENABLED=1 激活
```

- [x] OTel span 覆盖 LLM / tool / task / plaza 调用（trace_llm_call / trace_tool_execution / trace_plaza_discussion）
- [x] 支持 Jaeger / OTLP 导出（OTLPSpanExporter → AG_OTEL_ENDPOINT）
- [x] 保留 NoOp 降级（无依赖时全部 no-op）
- [x] pyproject.toml 新增 `[otel]` optional dependency group

---

## 阶段看板

### P0 进度

```
RUN-01 [~] Docker Sandbox — 代码备，实机验收待补 ...... 🔨
SEC-01 [✓] Cookie-Only Auth — 登出按钮已加，仅剩页面验收 ✅
RUN-02 [~] 统一 AgentLoop — shim 已备，待收束 ........... ⏳
PLAZA-01 [✓] 重试 + 失败升级 — 3次重试+升级队列+API .. ✅
BE-P0-01 [✓] 分页剩余端点补齐 — 7个端点已补 ........ ✅
```

### P1 进度

```
SEC-02 [✓] 生产安全响应头 — 中间件已落地 ........... ✅
BE-04  [✓] 测试覆盖提升 — 新增45+测试用例 ......... ✅
BE-03  [✓] main.py 常量 → config.py + .env 支持 .... ✅
BE-06  [~] Pydantic 校验全面化（已 ~75%） ........... ⏳
FE-02-2 [~] 全局状态收口（window.AG 已建） ........ ⏳
OBS-01 [✓] 结构化日志 + request_id — 已落地 ....... ✅
```

### P2 进度

```
FE-08  [~] i18n 绑定到 UI — 侧栏已标记 ........... ⏳
FE-11  [ ] 国际化引擎升级 ...................... ⏳
FE-09  [ ] SPA 单页应用评估 .................... ⏳
RUN-03 [✓] State Machine + Watchdog — 已落地 ..... ✅
RUN-04 [✓] Channels 事件桥接 — EventBridge 已落地 . ✅
PLAZA-02 [✓] Plaza 共识机制 — 度量+反方检测 ..... ✅
OBS-02 [✓] OpenTelemetry — 模块+NoOp降级 ....... ✅
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
