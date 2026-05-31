# OptimizePlan — 前后端统一 TODOs

> 基于 `OptimizePlan.md`（总看板）+ 当前代码状态生成的最新待办清单。
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

---

## P0 — 安全与运行时底座

> 这些是出关必要条件，不完成就不能说系统可用。

### RUN-01 🔴 Docker Sandbox 实机收口

```
位置: src/backend/sandbox/, docker/sandbox/, scripts/
难度: ⚡⚡ 大   优先级: P0
状态: WIP — docker mode、Dockerfile、limits、self-check 已有，缺实机验收
```

- [ ] CI/本机能 build sandbox docker image
- [ ] `run_python` / `run_pytest` 在 docker 模式跑通所有安全测试
- [ ] 缺 docker 时自动 fallback 到 `lite` 模式 + 日志告警
- [ ] 添加 `test_sandbox_docker.py` 集成测试
- [ ] 前端 sandbox 页面显示当前 sandbox mode（lite/docker）

### SEC-01 🔴 Cookie-Only Auth 收口

```
位置: src/backend/main.py, src/frontend/login.html, src/frontend/js/api.js
难度: ⚡ 中   优先级: P0
状态: WIP — httpOnly cookie 已建立，仍返回 token JSON 兼容旧客户端
```

- [ ] 添加 `AG_AUTH_RETURN_TOKEN_JSON` 环境变量（默认 `1` 保持兼容）
- [ ] 添加 `/api/v1/auth/logout` 端点（删除 cookie + 清除服务端 token）
- [ ] 添加 `login.html` 中的「注销登录」按钮
- [ ] 验证所有页面在 cookie-only 模式下正常工作
- [ ] 添加 auth/csrf 回归测试
- [ ] 旧 `localStorage.getItem('ag-token')` 引用清理确认

### RUN-02 🔴 统一 AgentLoop 收窄

```
位置: src/backend/agents/agent_loop.py, src/backend/agents/runtime/*, src/backend/agents/chat_harness.py
难度: ⚡⚡ 大   优先级: P0
状态: WIP — 共享 plan/tool runtime 已落地，旧 `agent_loop.py` 仍保留独立逻辑
```

- [ ] 旧 `AgentLoop` 类只保留薄 shim 调用统一 runtime
- [ ] 所有入口（chat / task / plan）只复用 `runtime/plan_loop.py` + `runtime/tool_loop.py`
- [ ] 旧 `agent_loop.py` 标注 `@deprecated`
- [ ] 覆盖所有入口行为的回归测试

### BE-P0-01 🔴 列表 API 分页全覆盖（存量补缺）

```
位置: src/backend/agents/api.py
难度: ⚡ 小   优先级: P0
状态: WIP — evolution/plaza 已分页，`agents/api.py` 中列表端点需确认
```

- [ ] 审查 `agents/api.py` 中所有返回 list 的端点
- [ ] 确认 `tasks` / `sessions` / `models` / `tools` / `skills` 列表有分页参数
- [ ] 前端 `api.list()` 在分页 API 上统一使用

---

## P1 — 质量加固

### SEC-03 🟡 API 限流

```
位置: src/backend/main.py
难度: ⚡ 中   优先级: P1
```

- [ ] 添加速率限制中间件（slowapi 或自定义实现）
- [ ] 登录/注册端点限流（5 次/分钟）
- [ ] 通用 API 限流（60 次/分钟）
- [ ] 限流测试覆盖

### BE-04 🟡 后端测试覆盖提升

```
位置: src/backend/tests/
难度: ⚡ 中   优先级: P1
```

- [ ] 审查 25 个现有测试文件的覆盖范围
- [ ] 补充 API handler 集成测试（login, register, health, teams, plaza, evolution）
- [ ] 补充 auth/csrf 回归测试（cookie-only + token 兼容）
- [ ] 补充分页 API 测试
- [ ] CI 配置 `npm run test:backend`

### BE-03 🟡 main.py 常量迁移到 config.py

```
位置: src/backend/main.py, src/backend/config.py
难度: ⚡ 小   优先级: P1
```

- [ ] `main.py` 中 `_DEFAULT_CORS_ORIGINS` → `from config import ALLOWED_ORIGINS`
- [ ] `main.py` 中 `_PBKDF2_ITERATIONS` → `from config import PBKDF2_ITERATIONS`
- [ ] `main.py` 中 `_TOKEN_TTL` → `from config import TOKEN_TTL`
- [ ] `main.py` 中 `_CSRF_TTL` → `from config import CSRF_TTL`
- [ ] 添加 `.env` 文件支持（python-dotenv）

### BE-06 🟡 Pydantic 校验全面化

```
位置: 各 route 文件
难度: ⚡ 中   优先级: P1
```

- [ ] 审查所有 POST/PUT/PATCH handler 的请求体
- [ ] 替换剩余原始 dict 访问为 Pydantic model
- [ ] 确保所有查询参数有类型注解和校验

### FE-10 🔵 单元测试框架搭建

```
位置: JS 文件
难度: ⚡⚡ 大   优先级: P1
```

- [ ] 安装 Vitest：`npm install -D vitest`
- [ ] 创建 `vitest.config.mjs`
- [ ] 为 `utils.js` 的核心函数（escapeHtml, toast, debounce, fmtNum）添加测试
- [ ] 为 `api.js` 的请求函数添加 mock 测试
- [ ] CI 配置 `npm run test:frontend`

### OBS-01 🟡 结构化日志 + request_id

```
位置: src/backend/main.py 等
难度: ⚡ 中   优先级: P1
```

- [ ] 日志格式改为 JSON 行输出（用于日志聚合系统）
- [ ] 日志级别通过环境变量配置（已支持 `config.py` 中 `LOG_LEVEL`）
- [ ] 为每个请求添加 request_id（FastAPI middleware）
- [ ] 单次请求可串联到后端 log、trace、前端错误

---

## P2 — 体验增强

### FE-08 🟡 i18n 绑定到 UI

```
位置: 多个 JS 文件
难度: ⚡ 中   优先级: P2
```

- [ ] 在提取模块的模板字符串中使用 `data-i18n` 属性标记
- [ ] 创建运行时翻译函数 `window.t(key)` 用于动态字符串
- [ ] 为常用 UI 字符串添加 `data-i18n` 翻译属性

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
位置: src/backend/agents/runtime/
难度: ⚡ 中   优先级: P2
```

- [ ] 统一状态机定义（AgentState / TaskState / SessionState）
- [ ] 超时 watchdog（task / session / agent 超时自动转换状态）
- [ ] SSE 状态变更事件

### SEC-02 🟡 API Key 传输安全

```
位置: 部署配置 + 前端 API 调用
难度: ⚡ 小   优先级: P2
```

- [ ] 明确 HTTPS 强制要求（文档 + 部署脚本）
- [ ] 生产安全头（HSTS / CSP / X-Frame-Options）
- [ ] 前端 API Key 输入使用 `type="password"` 且永不暴露在 URL 中

### PLAZA-02 🔵 Plaza 共识机制

```
位置: src/backend/agents/plaza.py, plaza_engine.py
难度: ⚡⚡ 大   优先级: P2
```

- [ ] 共识度量（当前讨论收敛程度分数）
- [ ] 反方意见机制（自动检测不同观点并突出显示）
- [ ] 动态退出（参与者可在一定条件下自动离场）

### OBS-02 🔵 OpenTelemetry / OTel Export

```
位置: src/backend/
难度: ⚡⚡ 大   优先级: P2
```

- [ ] OTel span 覆盖 LLM / tool / task / plaza 调用
- [ ] 支持 Jaeger / OTLP 导出
- [ ] 保留本地 JSONL trace 作为降级

---

## 阶段看板

### P0 进度

```
RUN-01 [ ] Docker Sandbox 实机收口 .............. ⏳
SEC-01 [ ] Cookie-Only Auth 收口 ................ ⏳
RUN-02 [ ] 统一 AgentLoop 收窄 .................. ⏳
BE-P0-01 [ ] 分页全覆盖（存量补缺） .............. ⏳
```

### P1 进度

```
SEC-03 [ ] API 限流 ........................... ⏳
BE-04  [ ] 测试覆盖提升 ....................... ⏳
BE-03  [ ] main.py 常量 → config.py ............ ⏳
BE-06  [ ] Pydantic 校验全面化 ................. ⏳
FE-10  [ ] 单元测试框架搭建（Vitest） .......... ⏳
OBS-01 [ ] 结构化日志 + request_id ............ ⏳
```

### P2 进度

```
FE-08  [ ] i18n 绑定到 UI ...................... ⏳
FE-11  [ ] 国际化引擎升级 ...................... ⏳
FE-09  [ ] SPA 单页应用评估 .................... ⏳
RUN-03 [ ] State Machine + Watchdog ............ ⏳
SEC-02 [ ] API Key 传输安全 .................... ⏳
PLAZA-02 [ ] Plaza 共识机制 .................... ⏳
OBS-02 [ ] OpenTelemetry / OTel Export ......... ⏳
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

> 最后更新：2026-05-31  
> 基于 `OptimizePlan.md` 总看板 + 当前代码状态生成
