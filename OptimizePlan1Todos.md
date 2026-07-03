# OptimizePlan1 — 前后端统一 TODOs

> 基于 `OptimizePlan1.md` 提取的完整任务清单，按阶段（S1/S2/S3）和优先级（P0/P1/P2）组织。
> 含前置依赖和完成状态追踪。

---

## 如何阅读

```
[ ] FE-01 任务描述 ........................ ⚡难度 位置
  └─ 具体步骤
```

- **FE-XX** = 前端 · **BE-XX** = 后端
- **⚡ 极小/小/中/大** = 实现难度
- **S1/S2/S3** = 阶段编号
- `[x]` = 已完成

---

## S1：安全收尾（P0）

> 目标：完成最终安全防线，前置依赖：无

### FE-01 🔴 CSRF 前端配合

```
位置: login.html + api.js
难度: ⚡ 小    阶段: S1
```

- [ ] `login.html` 登录成功后调用 `window.api.setCsrfToken(data.csrf_token)`
- [ ] 验证所有 POST/PUT/DELETE 请求自动携带 `X-CSRF-Token` header
- [ ] 验证 `api.initCsrfFromMeta()` 在页面加载时自动从 `<meta name="csrf-token">` 读取

### BE-01 🔴 CSRF token 端点

```
位置: main.py
难度: ⚡ 小    阶段: S1
```

- [ ] 新增 `GET /api/v1/auth/csrf-token` 端点，`SameSite=Strict` cookie 中返回 token
- [ ] POST/PUT/DELETE 请求校验 `X-CSRF-Token` header
- [ ] 前端 `<meta name="csrf-token">` 由后端渲染时注入

### BE-02 🔴 httpOnly cookie 认证

```
位置: main.py
难度: ⚡ 中    阶段: S1
```

- [ ] `/api/v1/auth/login` 登录成功返回 `Set-Cookie: ag-token=...; HttpOnly; SameSite=Strict`
- [ ] `/api/v1/auth/register` 注册成功同样返回 httpOnly cookie
- [ ] 移除 `login.html` 中的 `localStorage.setItem('ag-token', ...)`
- [ ] 后端增加 cookie 鉴权中间件（检查 cookie 而非 `Authorization` header）
- [ ] 保持向后兼容：同时支持 `Authorization: Bearer` header 一段时间

### BE-03 🟠 列表 API 分页落地

```
位置: agent_team_api.py, plaza_routes.py, 各 store
难度: ⚡ 中    阶段: S1
```

- [ ] `getTeamsList()` 等团队列表 API 应用 `paginate()` 辅助函数
- [ ] trace events / summaries 列表 API 添加分页参数
- [ ] evolution items / rules 列表 API 添加分页
- [ ] 前端 `api.list()` 在分页 API 上统一使用
- [ ] 设置 `DEFAULT_PAGE_SIZE=50`, `MAX_PAGE_SIZE=200`

### FE-02 🟡 loadOverview 瀑布请求优化

```
位置: agent-team-config.js:162
难度: ⚡ 小    阶段: S1
```

- [ ] 将 6 个并行 API 调用合并为更少的批量请求（如后端新增聚合端点）
- [ ] 或使用请求优先级：用户可见数据优先加载，次要数据延迟加载
- [ ] 考虑添加请求缓存，避免相同数据重复请求

### FE-03 🟢 overview 递归刷新防抖

```
位置: agent-team-config.js:193
难度: ⚡ 极小  阶段: S1
```

- [ ] 在 `setInterval` 回调顶部增加 `document.hidden` 检查，跳过不可见时的调度
- [ ] 页面重新可见时（`visibilitychange` 事件）立即执行一次刷新

---

## S2：质量加固（P1）

> 目标：消除架构债务，提升代码质量，前置依赖：S1 完成

### FE-04 🟡 skill-extract.html 继续外抽

```
位置: skill-extract.html
难度: ⚡ 中    阶段: S2
```

- [ ] 将内联 `<style>` 块（`skill-extract.html` 前半部分）抽到独立 CSS 文件
- [ ] 将错误追踪 `<script>` 移至 `utils.js` 统一管理（已在 CSP 中，确认重复）
- [ ] 检查是否存在其他遗留内联代码

### FE-05 🟠 Plaza 3D 回流优化

```
位置: plaza.js
难度: ⚡ 中    阶段: S2
```

- [ ] `positionSpeechBubble()` 从 `animate()` 每帧调用改为 ResizeObserver + camera change listener
- [ ] 使用 `requestAnimationFrame` 节流，至少间隔 16ms 执行一次
- [ ] `getBoundingClientRect()` 缓存到气泡数据中，只在内容变化时重新读取

### FE-06 🟡 全局变量作用域清理

```
位置: agent-team-config.js:1-8
难度: ⚡ 中    阶段: S2
```

- [ ] `tid`, `aid` 等全局变量封装到命名空间（如 `window.AG.state = {}`）
- [ ] `wzD`, `wzS` 等向导状态移到 `wizard.js` 内部
- [ ] `_offline`, `_teamsListCache` 等内部状态移到 `api.js` 或模块内部
- [ ] 在 `agent-team-config.js` 顶部只保留最小必要全局引用

### FE-07 🟢 strict mode 统一

```
位置: 多个 JS 文件
难度: ⚡ 小    阶段: S2
```

- [ ] 检查所有 IIFE 包裹的模块是否含有 `'use strict';`
- [ ] 缺失的文件：`nav-sidebar.js`（已有）、`i18n.js`（已有）、`agent-detail.js` 等提取模块
- [ ] 为缺失的模块添加 `'use strict';`

### BE-04 🟡 测试覆盖提升

```
位置: src/backend/tests/
难度: ⚡ 中    阶段: S2
```

- [ ] 审查 25 个现有测试文件的覆盖范围
- [ ] 补充 API handler 集成测试（login, register, health, teams）
- [ ] 补充前端 JS 模块的测试（Vite + Vitest 环境搭建，见 FE-10）
- [ ] CI 配置 `npm run test:backend` 和 `npm run test:frontend`

### BE-05 🟡 配置集中管理

```
位置: main.py, pyproject.toml
难度: ⚡ 中    阶段: S2
```

- [ ] 创建 `src/backend/config.py` 统一读取环境变量和 `pyproject.toml`
- [ ] 将 `main.py` 中的硬编码常量（`_DEFAULT_CORS_ORIGINS`, `_PBKDF2_ITERATIONS`, `_TOKEN_TTL` 等）移到配置模块
- [ ] 支持 `.env` 文件（python-dotenv）

### BE-06 🟡 Pydantic 校验全面化

```
位置: 各 route 文件
难度: ⚡ 中    阶段: S2
```

- [ ] 审查所有 POST/PUT/PATCH handler 的请求体
- [ ] 替换原始 dict 访问为 Pydantic model
- [ ] 确保所有查询参数有类型注解和校验

---

## S3：体验增强（P2）

> 目标：提升用户体验和可维护性，前置依赖：S2 完成

### FE-08 🟡 i18n 绑定到 UI

```
位置: 多个 JS 文件
难度: ⚡ 中    阶段: S3
```

- [ ] 在提取模块的模板字符串中使用 `data-i18n` 属性标记
- [ ] 创建运行时翻译函数 `window.t(key)` 用于动态字符串
- [ ] 为常用 UI 字符串添加 `data-i18n` 翻译属性

### FE-09 🔵 SPA 单页应用评估/启动

```
位置: 全部页面
难度: ⚡⚡ 大  阶段: S3
```

- [ ] 评估迁移到 SPA 的 ROI（当前多页架构如果运行良好可不迁移）
- [ ] 如决定迁移：合并 `agent-team-config.js` 为主应用，其他页面提取为视图组件
- [ ] 使用 `hashchange` 或 History API 做客户端路由

### FE-10 🔵 单元测试框架搭建

```
位置: JS 文件
难度: ⚡⚡ 大  阶段: S3
```

- [ ] 安装 Vitest：`npm install -D vitest`
- [ ] 创建 `vitest.config.mjs`
- [ ] 为 `utils.js` 的核心函数（escapeHtml, toast, debounce, fmtNum）添加测试
- [ ] 为 `api.js` 的请求函数添加 mock 测试

### FE-11 🔵 国际化引擎升级

```
位置: i18n.js
难度: ⚡⚡ 大  阶段: S3
```

- [ ] 从 DOM text-walker 改为 key-based 方案
- [ ] 创建 `data-i18n` 属性翻译引擎
- [ ] 保留 TEXT_MAP 作为向后兼容，新增 `window.t(key)` API

### FE-12 🟢 alert() 收尾确认

```
位置: agent-team-config.js
难度: ⚡ 小    阶段: S3
```

- [ ] 全局搜索 `alert(` 确认无遗漏
- [ ] 如发现新的 alert 调用，替换为 `showInfoModal()`

### BE-07 🟡 结构化日志

```
位置: main.py 等
难度: ⚡ 中    阶段: S3
```

- [ ] 日志格式改为 JSON 行输出（用于日志聚合系统）
- [ ] 日志级别通过环境变量配置（`LOG_LEVEL=INFO`）
- [ ] 为每个请求添加 request_id 用于追踪

### BE-08 🟡 API 限流

```
位置: main.py
难度: ⚡ 中    阶段: S3
```

- [ ] 添加速率限制中间件（slowapi 或自定义实现）
- [ ] 登录/注册端点限流（5 次/分钟）
- [ ] 通用 API 限流（60 次/分钟）

### BE-09 🟢 健康检查增强

```
位置: main.py
难度: ⚡ 小    阶段: S3
```

- [ ] `/api/v1/health` 返回每个子系统的详细状态（数据库连接、LLM 可用性等）
- [ ] 添加组件健康检查函数列表，可注册新的检查项

---

## 阶段看板

### S1 进度

```
FE-01 [x] CSRF 前端配合 .............. ✅
BE-01 [x] CSRF token 端点 ............. ✅
BE-02 [x] httpOnly cookie 认证 ........ ✅
BE-03 [x] 列表 API 分页落地 ........... ✅
FE-02 [x] loadOverview 优化 ........... ✅
FE-03 [x] overview 刷新防抖 ........... ✅
```

### S2 进度

```
FE-04 [x] skill-extract.html 外抽 ..... ✅
FE-05 [x] Plaza 3D 回流优化 ........... ✅
FE-06 [x] 全局变量作用域清理 ........... ✅
FE-07 [x] strict mode 统一 ............ ✅
BE-04 [ ] 测试覆盖提升 ............... ⏳
BE-05 [x] 配置集中管理 ............... ✅
BE-06 [ ] Pydantic 校验全面化 ......... ⏳
```

### S3 进度

```
FE-08 [ ] i18n 绑定到 UI ............. ⏳
FE-09 [ ] SPA 单页应用评估 ........... ⏳
FE-10 [ ] 单元测试框架搭建 ........... ⏳
FE-11 [ ] 国际化引擎升级 ............. ⏳
FE-12 [x] alert() 收尾确认 ........... ✅
BE-07 [ ] 结构化日志 ................. ⏳
BE-08 [ ] API 限流 .................. ⏳
BE-09 [x] 健康检查增强 ............... ✅
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

> 最后更新：2026-05-31  
> 基于 `OptimizePlan1.md` 提取
