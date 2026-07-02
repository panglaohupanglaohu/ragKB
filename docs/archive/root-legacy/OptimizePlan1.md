# OptimizePlan1 — 前后端全貌优化方案

> 最终版本 · 2026-05-31  
> 基于 10 轮连续分析 + 重构 + 修复后的代码库  
> 覆盖：前端 `src/frontend/`（19 JS + 11 HTML + 5 CSS）+ 后端 `src/backend/`（121 Python 核心 + 25 测试）

---

## 目录

1. [代码库现状总览](#1-代码库现状总览)
2. [已完成工作（10 轮总结）](#2-已完成工作10-轮总结)
3. [前端剩余待办](#3-前端剩余待办)
4. [后端剩余待办](#4-后端剩余待办)
5. [阶段性路线图](#5-阶段性路线图)
6. [附录：文件清单](#6-附录文件清单)

---

## 1. 代码库现状总览

### 1.1 规模指标

| 指标 | 数值 |
|------|:----:|
| **前端 JS** | 19 文件 / 16,403 行 |
| **前端 HTML** | 11 页面 / 5,090 行 |
| **前端 CSS** | 5 文件 / 1,875 行 |
| **后端 Python 核心** | 121 文件 |
| **后端 Python 测试** | 25 文件 |
| **构建产出** | Vite 794ms → 1.2MB dist/（11 HTML + 8 JS chunks + 4 CSS）|
| **语法通过率** | 16/16 CommonJS + 3 ES Modules + Python ✅ |

### 1.2 架构

```
src/frontend/js/
  Shared Core (3):
    utils.js (205)       — 工具库（escapeHtml, toast, modal, loading, debounce）
    api.js (136)         — 统一 API 客户端（CSRF-ready, 离线检测, 分页）
    global-nav.js (49)   — 全局导航组件

  Main App (1):
    agent-team-config.js (800)  ← 2249 → 800 (-64%)

  Extracted Modules (6):
    tools-skills.js (217)      — 工具/技能管理
    wizard.js (136)            — 新建智能体向导
    tasks-view.js (356)        — 并发任务 + 工作流
    agent-detail.js (212)      — Agent 详情视图
    sessions-runtime.js (142)  — 会话存档 + PortRuntime
    token-factory.js (213)     — Token Factory 控制台

  Externalized Pages (6):
    plaza.js (1704)            — 广场 3D 场景 (ES module)
    system-evolution.js (1055) — 系统演进面板
    sandbox-twin.js (382)      — SECS 沙箱
    digital-twin-cli.js (2427) — 数字孪生主逻辑
    digital-twin-cli-3d.js (1093) — 数字孪生 3D (ES module)
    skill-extract.js (5038)    — 技能萃取 (ES module)
    skill-extract-timeline.js (572) — 技能萃取时间线

  Infrastructure (2):
    i18n.js (1372)             — 国际化（~700 条翻译）
    nav-sidebar.js (294)       — OpenBridge 侧栏导航
```

---

## 2. 已完成工作（10 轮总结）

### 🔐 安全（8/11 项完成）

| 项目 | 状态 | 说明 |
|------|:----:|------|
| XSS 注入修复（20+ 处） | ✅ | `escapeHtml()` + `esc()` 覆盖所有提取模块 |
| SSE 资源泄漏修复 | ✅ | 切换 plaza 广场时关闭旧 EventSource |
| SSE 指数退避重连 | ✅ | `createReconnectingSSE()` 全局工具函数 |
| CSP meta 标签 | ✅ | 全部 11 个 HTML 页面 |
| 客户端错误追踪 | ✅ | `window.onerror` + `unhandledrejection` → 后端 /api/v1/log/client-error |
| 后端统一异常处理 | ✅ | HTTPException / PydanticValidationError / 通用兜底 |
| `digital-twin-cli.js` XSS | ✅ | 13 处添加 `esc()` 保护 |
| `sandbox-twin.js` XSS | ✅ | `sop.name`, `sop.status`, 错误消息 |
| **CSRF 防护** | ❌ | 前端 API 客户端已就绪 (`setCsrfToken()`, `initCsrfFromMeta()`)，需后端配合 |
| **Auth token 迁移** | ❌ | 前端 login 已用 `api.js`，但 token 仍存 localStorage；需后端 httpOnly cookie |
| **API Key 加密传输** | ❌ | 依赖 HTTPS 部署；前端侧可加对称加密 |

### 📦 架构（8/10 项完成）

| 项目 | 状态 | 说明 |
|------|:----:|------|
| `agent-team-config.js` 模块化拆分 | ✅ | 2249→800 行，提取 6 个独立模块 |
| 内联脚本外抽（全部 7 页面） | ✅ | sandbox-twin / plaza / system-evolution / skill-extract / digital-twin-cli（主+3D）|
| 三个 `api()` 合并 | ✅ | 创建统一 `js/api.js`，所有页面引用 |
| 导航栏集中管理 | ✅ | `js/global-nav.js` → 6 个页面统一 |
| CSS 公共变量文件 | ✅ | `css/variables.css` 共享设计 token |
| 空值保护 | ✅ | 15 处 `.slice()`/`.toFixed()`/`.toLocaleString()` 保护 |
| 无引用 demo 文件清理 | ✅ | 删除 7 个废弃文件（plaza-old/wabisabi* + demo-*）|
| **全局作用域污染** | ❌ | 提取模块已用 IIFE，但 `agent-team-config.js` 仍有全局变量 |
| **SPA 迁移** | ❌ | 目前仍是多页 HTML，导航栏虽集中但每页独立加载 |

### 🎨 CSS / 前端体验（9/11 项完成）

| 项目 | 状态 | 说明 |
|------|:----:|------|
| CSS minified 展开 | ✅ | `agent-team-config.css` 首行格式化 |
| `!important` 减少 | ✅ | 14 → 8（仅保留合理位置：hidden, focus, reduced-motion）|
| 重复 :root 块清理 | ✅ | `ws-theme-bridge.css` 移除重复定义 |
| Google Fonts `display=swap` | ✅ | 全部字体 URL 添加 |
| `@import` → `<link>` | ✅ | `openbridge-theme.css` 移除 @import |
| `oklch()`/`color-mix()` 回退 | ✅ | `@supports not` 块提供 hex/rgb 后备 |
| `es-module-shims` polyfill | ✅ | `plaza.html` + `skill-extract.html` 添加 |
| Three.js 更新 | ✅ | 0.170.0 → 0.184.0（匹配 npm 包）|
| **agent-team-config 全局命名** | ❌ | `tid`, `aid`, `wzD`, `wzS` 仍为全局 |
| **strict 模式** | ❌ | 部分模块有 `'use strict'`，但不是全部 |

### ♿ 可访问性 / i18n（5/7 项完成）

| 项目 | 状态 | 说明 |
|------|:----:|------|
| i18n 核心 UI 字符串 | ✅ | 新增 146 条翻译（累计 ~700 条）|
| ARIA `role=switch` | ✅ | 全部 custom checkbox toggle |
| `aria-live="polite"` | ✅ | Toast 组件 |
| `aria-current` / skip-link | ✅ | 导航栏 + 键盘跳转 |
| 登录页优化 | ✅ | autocomplete, form role, aria-label |
| **i18n 全模块覆盖** | ❌ | 提取模块字符串在 `i18n.js` 但 UI 未绑定 `data-i18n` |
| **key-based 翻译引擎** | ❌ | 目前仍是 DOM text-walker 模式 |

### ⚡ 性能（5/7 项完成）

| 项目 | 状态 | 说明 |
|------|:----:|------|
| Overview 增量刷新 | ✅ | 10s 定时器改为仅 refreshBudgetPanel + refreshTracePanel |
| `nav-sidebar.js` hidden 检查 | ✅ | 时钟 1s + 健康检查 10s 均加 `document.hidden` |
| `nav-sidebar.js` 健康检查路径 | ✅ | `/health` → `/api/v1/health` |
| sandbox chart resize 优化 | ✅ | 避免每步 resize canvas |
| 空值保护 | ✅ | 15 处跨模块修复 |
| **Plaza 3D 每帧回流** | ❌ | `positionSpeechBubble()` 在 `animate()` 中每帧执行（已有 camera 移动判断优化但未完全解决）|
| **Overview 全量拉动** | ❌ | 已改为增量，但 loadOverview 本身仍拉 ~6 个 API |

### 🛠️ 构建管道（全部完成）

| 项目 | 状态 | 说明 |
|------|:----:|------|
| Vite 配置 | ✅ | root / proxy / rollup input 完整 |
| Chunk 分割 | ✅ | `three-core` 独立 chunk（554KB）|
| 构建时间 | ✅ | 794ms |
| 产出大小 | ✅ | 1.2MB（11 HTML + 8 JS chunks + CSS）|
| Vite 配置清理 | ✅ | 移除已删除页面引用 |

### 🐍 后端（3/6 项完成）

| 项目 | 状态 | 说明 |
|------|:----:|------|
| 统一异常处理 | ✅ | 3 个异常处理器 + `PaginationParams` + `paginate()` 辅助 |
| API 版本前缀 | ✅ | 审计确认所有路由使用 `/api/v1/` |
| 分页辅助函数 | ✅ | `paginate()` + `PaginationParams` + `DEFAULT_PAGE_SIZE` |
| **实际分页落地** | ❌ | 辅助函数已就绪，但各 store 方法未使用 |
| **测试覆盖提升** | ❌ | 25 个测试文件，覆盖率需评估 |
| **配置集中管理** | ❌ | `pyproject.toml` + `main.py` 中的硬编码常量 |

---

## 3. 前端剩余待办

### P0 — 关键（建议 1-2 天）

| ID | 问题 | 位置 | 难度 | 影响 |
|:--:|------|------|:----:|:----:|
| FE-01 | **CSRF 前端配合**：`login.html` 后端返回 CSRF token 后调用 `api.setCsrfToken()` | `login.html` + `api.js` | ⚡ 小 | 安全兜底 |
| FE-02 | **loadOverview 瀑布请求**：6 个并行 API 可合并或懒加载 | `agent-team-config.js:162` | ⚡ 小 | 性能 |
| FE-03 | **overview 递归刷新**：`setInterval` 在页面不可见时仍调度下一次 | `agent-team-config.js:193` | ⚡ 极小 | CPU/网络 |

### P1 — 重要（建议 3-5 天）

| ID | 问题 | 位置 | 难度 | 影响 |
|:--:|------|------|:----:|:----:|
| FE-04 | **skill-extract.html 仍较大**：1471 行内联样式 + 内联错误追踪，可继续外抽 | `skill-extract.html` | ⚡ 中 | 可维护性 |
| FE-05 | **Plaza 3D 回流**：`positionSpeechBubble` 每帧 `getBoundingClientRect()` | `plaza.js` | ⚡ 中 | 性能 |
| FE-06 | **全局变量**：`tid`, `aid`, `wzD`, `wzS` 等仍挂 window | `agent-team-config.js:1-8` | ⚡ 中 | 架构质量 |
| FE-07 | **strict mode 统一**：部分 IIFE 模块无 `'use strict'` | 多个 JS 文件 | ⚡ 小 | 代码质量 |
| FE-08 | **i18n 绑定**：提取模块字符串在 i18n.js 但 UI 未用 `data-i18n` | 多个 JS 文件 | ⚡ 中 | 国际化 |

### P2 — 增强（建议 5-7 天）

| ID | 问题 | 位置 | 难度 | 影响 |
|:--:|------|------|:----:|:----:|
| FE-09 | **SPA 单页应用迁移**：将所有页面合并为 SPA，减少全页加载 | 全部 | ⚡⚡ 大 | UX/架构 |
| FE-10 | **单元测试**：JSDoc 已完整，可开始加 Vitest 测试 | JS 文件 | ⚡⚡ 大 | 质量保障 |
| FE-11 | **国际化引擎升级**：从 text-walker 改为 key-based `data-i18n` | `i18n.js` | ⚡⚡ 大 | 国际化质量 |
| FE-12 | **alert() 收尾确认**：已替换 6 处，确保无遗漏 | `agent-team-config.js` | ⚡ 小 | UX |

---

## 4. 后端剩余待办

### P0 — 关键（建议 2-3 天）

| ID | 问题 | 位置 | 难度 | 影响 |
|:--:|------|------|:----:|:----:|
| BE-01 | **CSRF token 端点**：实现 `GET /api/v1/auth/csrf-token` 返回 token | `main.py` | ⚡ 小 | 安全 |
| BE-02 | **httpOnly cookie 认证**：login/register 返回 Set-Cookie 而非 JSON token | `main.py` | ⚡ 中 | 安全 |
| BE-03 | **列表 API 分页落地**：将 `paginate()` 应用到所有返回列表的路由 | `agent_team_api.py`, `plaza_routes.py` 等 | ⚡ 中 | 性能/安全 |

### P1 — 重要（建议 3-5 天）

| ID | 问题 | 位置 | 难度 | 影响 |
|:--:|------|------|:----:|:----:|
| BE-04 | **测试覆盖提升**：补充 API handler 集成测试 | `tests/` | ⚡ 中 | 质量保障 |
| BE-05 | **配置集中管理**：从 `pyproject.toml` + 环境变量统一读取 | `main.py` | ⚡ 中 | 可维护性 |
| BE-06 | **Pydantic 校验全面化**：所有请求体使用 Pydantic model 而非原始 dict | 各 route 文件 | ⚡ 中 | 安全 |

### P2 — 增强（建议 5-7 天）

| ID | 问题 | 位置 | 难度 | 影响 |
|:--:|------|------|:----:|:----:|
| BE-07 | **日志系统升级**：结构化日志（JSON 格式）+ 日志级别配置 | `main.py` 等 | ⚡ 中 | 运维 |
| BE-08 | **API 限流**：添加速率限制中间件 | `main.py` | ⚡ 中 | 安全 |
| BE-09 | **健康检查增强**：`/api/v1/health` 纳入各子系统详细状态 | `main.py` | ⚡ 小 | 可观测性 |

---

## 5. 阶段性路线图

### S1：安全收尾（2-3 天）

```
优先级: P0
目标: 完成最终安全防线

FE-01  CSRF 前端配合          (api.js + login.html)   ⚡ 0.5天
BE-01  CSRF token 端点        (main.py)               ⚡ 0.5天
BE-02  httpOnly cookie 认证    (main.py)               ⚡ 1天
BE-03  列表 API 分页落地       (各 route)              ⚡ 1天
FE-02  loadOverview 优化       (agent-team-config.js)  ⚡ 0.5天
```

### S2：质量加固（3-5 天）

```
优先级: P1
目标: 消除架构债务，提升代码质量

FE-04  skill-extract.html 继续外抽       ⚡ 1天
FE-05  Plaza 3D 回流优化                 ⚡ 1天
FE-06  全局变量作用域清理                 ⚡ 1天
FE-07  strict mode 统一                   ⚡ 0.5天
BE-04  测试覆盖提升                       ⚡ 2天
BE-05  配置集中管理                       ⚡ 1天
BE-06  Pydantic 校验全面化                ⚡ 1天
```

### S3：体验增强（5-7 天）

```
优先级: P2
目标: 提升用户体验和可维护性

FE-08  i18n 绑定到 UI                     ⚡ 1天
FE-09  SPA 单页应用评估/启动              ⚡ 3-5天
FE-10  单元测试框架搭建（Vitest）         ⚡ 2天
FE-11  国际化引擎升级                      ⚡ 2天
BE-07  结构化日志                         ⚡ 1天
BE-08  API 限流                           ⚡ 1天
BE-09  健康检查增强                       ⚡ 0.5天
```

### 时间预估总表

| 阶段 | 内容 | 预估工期 | 前置依赖 |
|------|------|:--------:|----------|
| **S1** | 安全收尾 | 2-3 天 | 无 |
| **S2** | 质量加固 | 3-5 天 | S1 完成 |
| **S3** | 体验增强 | 5-7 天 | S2 完成 |
| **总计** | | **10-15 天** | |

---

## 6. 附录：文件清单

### 6.1 前端 JS 文件（19）

```
 核心共享层
   utils.js (205)        ← 工具函数库
   api.js (136)          ← API 客户端（CSRF-ready）
   global-nav.js (49)    ← 全局导航组件

 主应用
   agent-team-config.js (800)  ← 团队管理主应用

 提取模块（agent-team-config 子模块）
   tools-skills.js (217)       ← 工具/技能管理
   wizard.js (136)             ← 新建智能体向导
   tasks-view.js (356)         ← 并发任务
   agent-detail.js (212)       ← Agent 详情
   sessions-runtime.js (142)   ← 会话存档 + PortRuntime
   token-factory.js (213)      ← Token Factory

 外抽页面
   plaza.js (1704)             ← 广场 3D（ES module）
   system-evolution.js (1055)  ← 系统演进
   sandbox-twin.js (382)       ← SECS 沙箱
   digital-twin-cli.js (2427)   ← 数字孪生
   digital-twin-cli-3d.js (1093) ← 数字孪生 3D（ES module）
   skill-extract.js (5038)     ← 技能萃取（ES module）
   skill-extract-timeline.js (572) ← 技能萃取时间线

 基础设施
   i18n.js (1372)              ← 国际化
   nav-sidebar.js (294)        ← OpenBridge 侧导航
```

### 6.2 前端 HTML 页面（11）

```
  agent-team-config.html (275)       — 团队管理主页面
  plaza.html (379)                   — 议事广场 3D
  system-evolution.html (582)        — 系统演进
  skill-extract.html (1471)          — 技能萃取（最大页面）
  digital-twin-cli.html (610)        — 数字孪生 CLI
  sandbox-twin.html (520)            — SECS 沙箱
  login.html (515)                   — 登录/注册
  tasks.html (210)                   — 任务面板
  extraction-pipeline.html (626)     — 萃取管线
  datacenter-ratchet-evolution.html (709) — 数据中心演进
  index.html (33)                    — 重定向到 login
```

### 6.3 前端 CSS 文件（5）

```
  agent-team-config.css (338)    — 主应用样式
  openbridge-theme.css (791)     — OpenBridge 主题
  ws-theme-bridge.css (225)      — Wabi-Sabi 主题桥接
  variables.css (97)             — 共享设计 token
  skill-extract-timeline.css (424) — 时间线样式
```

### 6.4 后端 Python（146）

```
  核心模块: 121 文件
  测试模块: 25 文件
  入口点: main.py
  主要路由: agent_team_api.py, plaza_routes.py, extraction_routes.py, sandbox/api.py
```

---

> **文档维护：** 当完成任一待办项时，更新本文件的 ✅ 状态标记。  
> **文件约定：** `FE-XX` = 前端待办 · `BE-XX` = 后端待办 · `SX` = 阶段编号  
> **更新日期：** 2026-05-31
