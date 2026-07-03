---
name: sandbox-twin-optimization
overview: 全面优化 sandbox-twin.html 页面：修复 subscribeStream bug、补全缺失 CSS token、将 Canvas 折线图升级为 SVG、添加 count-up 动画与 toast 通知、提取独立 CSS 文件、加 session 历史面板与取消按钮、统一 Wabi-Sabi 视觉风格。
todos:
  - id: fix-stream-bug
    content: 修复 P0 Bug：sandbox-twin.js 第385行 subscribeStream 改为 connectStream
    status: pending
  - id: fix-css-tokens
    content: 修复 P0 Bug：引入 openbridge-theme.css + 将 :root 色板对齐 Wabi-Sabi token
    status: pending
  - id: fix-canvas-scale
    content: 修复 P0 Bug：drawChart 中 ctx.scale 之前加 setTransform 重置变换
    status: pending
  - id: extract-css
    content: 新建 sandbox-twin.css，从 HTML 抽取全部内联样式
    status: pending
    dependencies:
      - fix-css-tokens
  - id: add-toast
    content: 添加 toast 通知系统（HTML 增加 toast-host + JS 增加 toast 函数）
    status: pending
    dependencies:
      - extract-css
  - id: add-countup
    content: stat 卡片增加 count-up 数字滚动动画
    status: pending
    dependencies:
      - add-toast
  - id: session-history
    content: 添加 session 历史列表（可折叠、可点击恢复）
    status: pending
    dependencies:
      - extract-css
  - id: stop-button
    content: 添加「停止仿真」按钮 + 停止逻辑
    status: pending
  - id: svg-chart
    content: Canvas 折线图替换为 SVG 折线图（对标 cost-dashboard 质量）
    status: pending
    dependencies:
      - fix-canvas-scale
  - id: polish-details
    content: 打磨细节：自动刷新指示器、SOP 空状态美化、Runtime 面板简化
    status: pending
    dependencies:
      - session-history
      - stop-button
      - svg-chart
  - id: build-verify
    content: vite build 生产构建 + 用 [skill:playwright-cli] 浏览器截图验证
    status: pending
    dependencies:
      - polish-details
---

## 产品概述

对 sandbox-twin.html（SECS 自进化协同沙箱）页面进行全面优化：修复 3 个关键 Bug、抽取内联 CSS 到独立文件、对齐 Wabi-Sabi 侘寂设计主题、增加 toast 通知/count-up 动画等交互增强，以及补充 session 历史列表、停止仿真按钮等功能。

## 核心功能

### P0 Bug 修复（阻塞级）

1. **修复 `subscribeStream` → `connectStream` 函数名错误**：第385行调用了不存在的 `subscribeStream`，导致技能注入后 SSE 实时流不会启动
2. **补全缺失的 CSS token**：引入 `openbridge-theme.css`，将页面自定义的深色调色板对齐项目统一的 Wabi-Sabi 侘寂 token
3. **修复 Canvas 累积缩放 bug**：`drawChart()` 每次调用 `ctx.scale(2,2)` 累积叠加，需增加 `setTransform` 重置

### P1 交互增强

4. **抽取独立 CSS 文件 `sandbox-twin.css`**：将 HTML 中 329 行内联 `<style>` 移出
5. **添加 toast 通知系统**：替换单行 `<div id="sim-status">` 为右下角浮层 toast（与 cost-dashboard 一致模式）
6. **stat 卡片数字 count-up 动画**：6 个统计卡加载时数字滚动
7. **Runtime 面板视觉简化**：减少 inline style 字符串拼接，改用 CSS 类

### P2 功能增强

8. **添加 session 历史列表**：展示最近沙箱会话，可查看/恢复
9. **添加「停止仿真」按钮**：运行中的 session 可主动停止
10. **添加自动刷新指示器**：显示下次自动刷新倒计时
11. **SOP 库空状态美化**：从一行灰字改为引导性占位卡片
12. **仿真时间线折线图升级为 SVG 折线图**：对标 cost-dashboard 的 SVG 折线图质量

## 技术栈

- 前端：原生 HTML + CSS + JavaScript（与项目现有架构一致）
- 主题：Wabi-Sabi 侘寂风（复用 `variables.css` + `openbridge-theme.css`）
- 后端 API：复用已有 `/api/v1/sandbox` 端点

## 实现方案

### 1. P0 Bug 修复

**Bug #1**: `sandbox-twin.js` 第385行将 `subscribeStream` 改为 `connectStream`（与第206行函数定义一致），一行改动。

**Bug #2**: `sandbox-twin.html` 引入 `<link rel="stylesheet" href="/css/openbridge-theme.css">`（参照 cost-dashboard.html / tasks.html 模式），然后从 `:root` 块移除自定义硬编码色值（`--bg: #0d1117` 等），改用现有 token 别名：

- 原 `--bg` → `--ob-bg-global`
- 原 `--panel` / `--panel2` / `--panel3` → `--ob-bg-panel` / `--ob-bg-section`
- 原 `--border` / `--text` / `--muted` / `--dim` → `--ob-border` / `--ob-text-primary` / `--ob-text-tertiary` / `--ob-text-disabled`
- 原 `--cyan` / `--green` / `--amber` / `--red` → `--koke` / `--koke` / `--kitsune` / `--shu`
- 原 `--mono` → `--ob-font-mono`

**Bug #3**: `drawChart()` 第506行 `ctx.scale(2,2)` 之前加入 `ctx.setTransform(1,0,0,1,0,0)` 重置当前变换矩阵。

### 2. CSS 抽取

新建 `src/frontend/css/sandbox-twin.css`，包含以下模块：

- 布局 (.main-grid, .panel, .full-width, .stats-row)
- 组件 (.agent-node, .timeline-step, .score-item, .stat-card, .btn, .runtime-card)
- 状态 (.status-dot, .agent-node.working/thinking/error, .skill-card)
- 控制 (.control-form, .form-group)

HTML 中仅保留 topbar-ws 专属的 header 结构样式和必要的页面级样式。

### 3. Toast 通知

参照 `cost-dashboard.js` 模式：在 HTML 加 `<div class="cost-toast-host" id="toast-host">`，在 JS 新增 `toast(msg, opts)` 函数（kind: success/warn/error，auto-dismiss 3.5s）。所有 `setStatus()` 调用同时触发 toast。

### 4. Count-Up 动画

参照 `cost-dashboard.js` 中的 `countUp(el, finalText, duration)` 函数（easeOutCubic 插值 + requestAnimationFrame），在 `loadStats()` 渲染完 6 个 stat 值后逐元素触发。

### 5. Session 历史列表

在仿真控制面板下方新增可折叠区域，调用 `/api/v1/sandbox/sessions` 列出最近 10 个 session，每个显示 session_id、模式、创建时间、状态，点击可恢复（设置 `currentSessionId` 并重连 SSE）。

### 6. 停止仿真按钮

在仿真控制面板的"启动仿真"按钮旁加"停止"按钮，调用后端新端点或通过关闭 EventSource + 标记 `aborted` 语义实现。后端 `/api/v1/sandbox/sessions/{id}/run` 响应中检查 abort 标志。

### 7. SVG 折线图

将 Canvas `<canvas>` 替换为 `<svg>`，参照 `cost-dashboard.js` 的 `lineChartSvg()` 模式生成折线图。好处：更清晰、支持 tooltip、与侘寂主题颜色一致、不需要处理 HiDPI。

### 性能考虑

- CSS 抽取不增加额外请求（vite build 会自动内联/合并）
- Toast 复用已有的 CSS 动画模式（无重排）
- SVG 折线图比 Canvas 更适合少量数据点（<200 点）的场景
- Count-up 仅在 loadStats 时触发，不影响 30s 定时器性能

## 目录结构

```
src/frontend/
├── sandbox-twin.html          # [MODIFY] 删除内联 <style>，引入 openbridge-theme.css + sandbox-twin.css
├── css/
│   └── sandbox-twin.css       # [NEW] 抽取出全部组件样式 (~250行)
└── js/
    └── sandbox-twin.js         # [MODIFY] Bug修复 + toast + countUp + session历史 + 停止 + SVG折线图
```

## 关键代码结构

### Toast 函数签名

```js
function toast(message, opts) {
  // opts: { kind: 'success'|'warn'|'error', title: '...', duration: 3500 }
  // 创建 <div class="cost-toast cost-toast--{kind}"> 插入 #toast-host
  // auto-dismiss 后 remove
}
```

### Count-Up 函数复用

```js
// 从 cost-dashboard.js 迁移，签名不变
function countUp(target, finalText, duration) { ... }
```

### SVG 折线图函数签名

```js
function drawRewardChart() {
  // 替代原 drawChart()
  // 读取 rewardHistory 数组，生成 SVG line-chart markup
  // 写入 #reward-chart 容器，grid + area + line + dots
}
```

## 使用的 Agent Extensions

### Skill

- **playwright-cli**
- 用途: 优化完成后，用 Puppeteer/Playwright 打开 http://localhost:5173/sandbox-twin.html 截图验证所有改动
- 预期结果: 截图显示修复后的页面布局正确、toast 通知可见、折线图正常渲染、session 历史面板存在