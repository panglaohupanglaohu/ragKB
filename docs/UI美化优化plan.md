# UI 美化与优化 Plan（全局设计系统统一 + 页面视觉升级）

> 范围：`src/frontend/` 全部 13 个 HTML 页面 + 共享 CSS（`css/*.css`）+ 共享 JS（导航类）
> 构建：Vite（`npm run dev` → `localhost:5173`），无前端框架，原生 HTML/CSS/JS + Three.js
> 编写日期：2026-06-16
> 验证手段：`npx vitest run`（`__tests__/`）+ 浏览器视觉冒烟（起服务后逐页核对）+ Lighthouse
> 分派约定：**【Claude(沙箱可做)】** = 纯 CSS/HTML/JS 改动，可 vitest / node --check 验证；**【Reasonix(本机/浏览器)】** = 起服务、跨页视觉回归、Lighthouse、真机响应式

---

## 0. 现状结论（先摸清，再动手）

对 `src/frontend/` 做了静态盘点（文件行数、CSS/JS 引用矩阵、内联样式块、颜色字面量、导航外壳使用情况），核心结论：

### 0.1 已有不错的基础，但存在「三套皮并存」的割裂

项目存在 **三套并行的设计语言 / 导航外壳**，且同一页面经常混用：

| 外壳 / 体系 | 来源 CSS | 用在哪 | 状态 |
|---|---|---|---|
| **OpenBridge (`.ob-*`)** | `openbridge-theme.css` (791行) | 经 `nav-sidebar.js` 注入的侧边栏 shell；`agent-team-config` / `cost-dashboard` / `tasks` 引了主题 | 较完整，但 `--ob-radius-*` 全为 `0px`（纯直角，工业风） |
| **Wabi-Sabi topbar (`.topbar-ws`)** | `topbar-ws.css` (243行) | 9 个页面用 `topbar-ws`，搭配 `variables.css` token | 设计语言最克制、最统一，是事实主样式 |
| **global-nav (`.global-nav`)** | `global-nav.js` (68行) 内联 | `datacenter-ratchet-evolution` / `extraction-pipeline` 等 | 只生成一组平铺链接，无样式系统 |

**导航页项不一致**：`nav-sidebar.js` 有 21 个导航项（含很多占位 `captain/navigation/dp...` 实际不存在的页面），而 `global-nav.js` 只有 6 个真实页面项。用户在页与页之间跳转时，顶/侧栏长不一样、可用链接也不一样。

### 0.2 内联样式泛滥（最大的可维护性债务）

8 个页面共 **约 1950 行 `<style>` 内联 CSS**，其中 `Agent-digital-twin.html` 单页内联 657 行、`digital-twin-cli.html` 320 行、`login.html` 261 行、`plaza.html` 255 行。后果：
- 相同样式在各页重复（`body::before` 和紙噪点纹理在 4 处各写一遍）；
- 无法被设计 token 统一收口（见下）。

### 0.3 颜色字面量（off-palette）散落，破坏主题切换

设计 token（`variables.css` + `ws-theme-bridge.css`）定义了 4 套主题（day/dusk/night/bright）并随 `data-obc-theme` 切换。但页面内联里大量写死颜色：

- `Agent-digital-twin.html`：72 处 hex（`#fbbf24`×9、`#a78bfa`×4、`#22d3ee`×4、`#f87171`×3、`#34d399`×3 …）
- `plaza.html`：63 处 hex（`#F0A050`、`#C05C5C`、`#5b9bd5`、`#E25555` …）
- `digital-twin-cli.html`：42 处 hex，含 `#22d3ee`/`#34d399` 这套**完全不在 token 里**的 cyan/green
- 另有 `rgba(34,211,238,*)` / `rgba(52,211,153,*)` 等同色系字面量散布

这些写死颜色 **不随主题切换变化**——切到 day/bright 主题时，深色页面会残留亮色字面量的局部亮块；切到 night（IMO 夜视）时，非 amber/green 的彩色会破坏夜视安全。

### 0.4 其它明确问题

- **`--ob-radius-*` 全为 0**：OpenBridge 组件全是直角，而 Wabi-Sabi 卡片有 `border-radius`，两者同页时圆角不统一。
- **`tasks-ws.css` 只有 14 行**：几乎空文件，tasks 页实际样式靠内联 + openbridge。
- **`global-nav.js.bak`** 残留在 `js/` 目录（死文件）。
- **可访问性缺口**：多数 `topbar-ws__nav` 是 `<a>/<span>` 无 `role`；模态缺 `role="dialog"`/焦点陷阱（已在各页 plan 中分散提及，本 plan 做**全局统一基线**）。
- **滚动条**：`openbridge-theme.css` 定义了 4px 极细滚动条，但用 `oklch()` thumb 在不支持的浏览器无 fallback（`variables.css` 有 oklch fallback，但 scrollbar 那条没有）。
- **首屏字体闪烁**：Google Fonts (`Noto Sans/Serif SC` + `JetBrains Mono`) 每页 `<link>` 同步加载，无 `font-display: swap` 之外的预加载优化。

---

## 1. 总体策略：统一到「Wabi-Sabi token 单一来源」+ 组件库收口

**一句话**：把所有页面收敛到 `variables.css`(+`ws-theme-bridge.css`) 这一套 token，OpenBridge 作为「组件层」复用其类名但变量全部指向同一套；消灭内联 `<style>`，建立 `css/components.css` 公共组件库；导航统一为单一外壳。

### 1.1 设计原则（沿用 AGENTS.md：简单优先、外科手术）
1. **Token 单一来源**：任何颜色/间距/圆角/字号必须引用 CSS 变量，禁止页面内再写 hex/rgba 字面量（3D/Three.js 场景色除外，见 §4 例外）。
2. **组件优先于页面样式**：重复的卡片/按钮/表格/输入/徽章/空态/骨架屏抽到 `css/components.css`，页面只写布局。
3. **不破坏现有功能**：JS 行为、API、数据结构零改动；纯视觉 + 结构层。每步都可 vitest 回归。
4. **主题完整**：4 套主题（day/dusk/night/bright）在每个改动后都必须可读。
5. **渐进迁移**：按「先基建（token + 公共 CSS）→ 再逐页迁移」顺序，每页一个独立可回滚 commit。

### 1.2 目标成功标准（可验证）
- [ ] `grep -rE '#[0-9a-fA-F]{6}' src/frontend/*.html` 在 HTML 内联 `<style>` 中 **0 命中**（3D canvas 内联除外）。
- [ ] 所有页面内联 `<style>` 总行数 **< 200 行**（从 ~1950 降下来）。
- [ ] 所有页面加载同一套 `css/base.css`（合并 variables+reset+滚动条+噪点）+ `css/components.css` + `css/topbar-ws.css`，不再按页拼不同子集。
- [ ] 导航外壳统一为一种（推荐 `topbar-ws` 横向顶栏，因 9/13 页已用它）。
- [ ] 4 套主题在 13 页全部切换无残色、无对比度故障（Lighthouse Accessibility ≥ 95）。
- [ ] `npx vitest run` 全绿（现有 __tests__ 不回归）。

---

## 2. 分阶段计划

### 阶段 A — 设计基建（地基，最高优先，全页受益）

**A1. 合并/重写共享 CSS 为清晰的三层**
```
css/base.css         ← variables.css(原) + 全局 reset + 滚动条 + body::before 噪点 + oklch/color-mix fallback
css/theme.css        ← ws-theme-bridge.css(原) + openbridge-theme.css 的 4 主题变量（合并去重）
css/components.css   ← 新建：从各页内联抽出的公共组件（见 A3）
css/topbar-ws.css    ← 保留（顶栏导航，主外壳）
```
- 删除/归档 `tasks-ws.css`(14行空文件)、`global-nav.js.bak`。
- 旧文件保留为 `*.legacy.css` 一版本以便回滚，不立即删（surgical 原则）。

**A2. 补全 token 体系（圆角 / 间距 / 阴影 / 动效）**
当前 token 只有颜色 + 字体 + 侧栏宽。补：
```css
:root{
  /* 圆角：统一 OpenBridge(0) 与 Wabi-Sabi 的冲突 */
  --radius-sm: 3px;  --radius-md: 6px;  --radius-lg: 10px;  --radius-pill: 999px;
  /* 间距尺度（8pt grid） */
  --sp-1:4px; --sp-2:8px; --sp-3:12px; --sp-4:16px; --sp-5:24px; --sp-6:32px; --sp-8:48px;
  /* 阴影（已有 --ws-shadow*，统一命名） */
  --shadow-sm / -md / -lg;
  /* 动效 */
  --ease: cubic-bezier(.4,0,.2,1);  --dur-fast: .12s;  --dur: .18s;  --dur-slow: .3s;
  /* z-index 层级表 */
  --z-base:0; --z-dropdown:100; --z-sticky:200; --z-overlay:1000; --z-modal:1100; --z-toast:1200;
}
```
- 统一 OpenBridge 的 `--ob-radius-*` 也指向这套 `--radius-*`（不再硬 `0px`），让 `.ob-card` 与 Wabi-Sabi 卡片圆角一致。
- **判定**：是否给全站引入「微圆角 6px」而非纯直角 —— 这是审美方向选择（见 §6 待决策）。

**A3. 建立 `css/components.css` 公共组件库**
从各页内联归纳、去重，提供单一实现的组件类（全用 token）：
- `.btn` / `.btn--primary` / `.btn--ghost` / `.btn--danger` / `.btn--sm`（取代 `.ob-btn` + 各页自定义 button）
- `.card` / `.card__header` / `.card__body` / `.card__title`（取代 `.ob-card*` + plaza 的 panel）
- `.input` / `.textarea` / `.select` / `.field` / `.field__label`（取代各页 `.form-input`）
- `.badge` / `.badge--ok|--warn|--danger|--neutral`（取代 `.ob-badge*` + 各页散落徽章）
- `.table`（取代 `.ob-table`）
- `.dot` / `.dot--ok|--warn|--danger`（状态点）
- `.progress` / `.progress__bar`
- `.skeleton`（骨架屏，新增，配合加载态）
- `.empty-state`（空态：图标 + 标题 + 文案 + CTA，新增）
- `.toast` / `.toast--error|--success|--warn`（统一，取代各页 inline toast）
- `.modal` / `.modal__overlay` / `.modal__panel` / `.modal__header` / `.modal__close`（统一模态，含 `role="dialog"` / aria / 焦点陷阱 hooks）

**A4. 统一导航外壳**
- **决策推荐**：全站用 **`topbar-ws` 横向顶栏**（9/13 页已用，迁移量最小），废弃 `nav-sidebar.js`(OpenBridge 侧栏) 与 `global-nav.js`(平铺) 两套。
- `nav-sidebar.js` 保留为「可折叠侧栏」可选模式（不默认注入），或直接移除引用、保留文件备用。
- 重写一份 **单一导航数据源** `js/nav.js`：6 个真实页面 + 用户/登出 + 主题切换 + 语言切换，供 `topbar-ws` 渲染。
- 清理 `nav-sidebar.js` 里 21 个指向不存在页面的占位项。

### 阶段 B — 逐页迁移（消灭内联 style，迁移到 token + 组件）

按「内联量从大到小」迁移，每页一个 commit、可独立回滚、vitest 回归：

| 顺序 | 页面 | 内联行数 | 迁移重点 |
|---|---|---|---|
| B1 | `Agent-digital-twin.html` | 657 | 抽出 72 处 hex → token；拆 `.digital-twin.css`；3D 配色见 §4 |
| B2 | `digital-twin-cli.html` | 320 | 42 处 hex（含 `#22d3ee`/`#34d399` 套色）→ token；拆 `.digital-twin-cli.css` |
| B3 | `login.html` | 261 | 登录卡片全部用组件库（`.card`/`.field`/`.btn`）；居中布局 |
| B4 | `plaza.html` | 255 | 安藤忠雄混凝土 token 已自成一套（`--concrete*`），映射进 `theme.css`；语音气泡 color-mix 保留但变量化 |
| B5 | `system-evolution.html` | 197 | 进化时间轴抽组件 |
| B6 | `extraction-pipeline.html` | 110 | 管道流式布局组件化 |
| B7 | `datacenter-ratchet-evolution.html` | 118 | 接入 topbar-ws（当前用 global-nav） |
| B8 | `tasks.html` | 31 | 删空 `tasks-ws.css`，全用组件库 |
| B9 | 其余（`agent-team-config`/`cost-dashboard`/`sandbox-twin`/`skill-extract`） | 0 内联 | 这几页已是外部 CSS，只做 token 对齐 + 组件类替换 |

### 阶段 C — 视觉精修与一致性（美化本体）

**C1. 排版层级**：统一标题尺度（h1~h4 / eyebrow / caption / mono-label），字号用 token `--fs-*`，字重遵循现有「serif 标题 + sans 正文 + mono 数据」三声部。
**C2. 间距节奏**：全站内容区 padding/gap 统一到 `--sp-*` 8pt 栅格，消除各页手写 `12px/14px/16px` 混用。
**C3. 微交互**：统一 hover/active/focus 过渡（`--dur` + `--ease`）；所有可交互元素补 `:focus-visible` 描边（无障碍）。
**C4. 加载/空/错误态**：列表页统一骨架屏 + 空态 + 错误重试（`api()` 层已统一，前端补 UI）。
**C5. 滚动条统一**：8px 语义滚动条（dusk 可见、night 隐入），补 oklch fallback。
**C6. 暗色对比度**：核对 `--sumi-3`/`--muted` 在 dusk 下对正文背景对比度 ≥ 4.5:1（WCAG AA）。

### 阶段 D — 性能与可访问性收尾

- **D1. 字体加载**：`<link rel="preload" as="style">` + `font-display: swap`（已有），考虑自托管字体子集（中文字体大，可按页用到的字做 subset）。
- **D2. 移除 `nav-sidebar.js` 的 1s 时钟 setInterval 全量刷新**：改 `requestAnimationFrame` 节流或每秒 textContent 赋值已够轻（实际已是 textContent，保留，但确认无强制重排）。
- **D3. 无障碍**：顶栏 `<nav aria-label>`；模态焦点陷阱；3D canvas `aria-label`；颜色非唯一信息载体。
- **D4. Lighthouse**：每页跑 Accessibility/Best-Practices，记录基线与目标。

---

## 3. 主题切换完整性方案

当前 4 主题在「token 层」是完整的（`ws-theme-bridge.css` 四套都写了），问题只在「页面写死颜色绕过了 token」。因此：

- **规则**：页面/组件 CSS **只能**用 `var(--xxx)`；任何 `#hex`/`rgb()` 进 CSS 视为 bug（lint 阶段 D5 检查）。
- **例外（§4）**：Three.js 3D 场景内的材质颜色，因为需要 JS 动态计算且常需 color-mix/lerp，允许在 JS 里以「读 token → 转 THREE.Color」的方式，**但颜色来源仍是 token**，不写死裸 hex。
- **night 主题（IMO 夜视）安全**：所有彩色 token 在 night 下已降为 amber/green 系；页面只要不写死颜色即自动合规。

---

## 4. 3D / Three.js 场景的配色策略（例外区）

`plaza.html`(three-canvas)、`Agent-digital-twin.html`、`digital-twin-cli.html`、`sandbox-twin.html` 用 Three.js。这些页内联里的 hex 多半是 3D 材质/粒子色。

**策略**：
- 3D 配色集中到一份 `js/scene-palette.js`（或各页 `*_3d.js` 头部），从 `getComputedStyle(document.documentElement).getPropertyValue('--koke')` **读 token**，转 `THREE.Color`。
- 主题切换时监听 `data-obc-theme` 变化，重算场景色（已有先例：部分页 CSS 变量驱动）。
- 这样 3D 也会随主题变，不再有「页面切亮、3D 还是暗色」或夜视违规。

---

## 5. 风险与回滚

- **风险1：迁移破坏页面布局**。**缓解**：每页独立 commit；保留 `*.legacy.css`；vitest + 浏览器逐页核对；先做基建（阶段A）不改任何页面 DOM，零风险。
- **风险2：OpenBridge 组件类名被 JS 依赖**。**缓解**：保留 `.ob-*` 类作别名指向新组件，先双名共存，最后再清理。
- **风险3：导航统一后用户找不到页**。**缓解**：新 `nav.js` 含全部 6 个真实页面 + 当前页高亮，迁移前后链接集合不变。

---

## 6. 待用户决策（影响实现方向）

1. **圆角方向**：全站统一微圆角（`--radius-md:6px`）还是保留 OpenBridge 纯直角工业风？（影响 A2）
2. **导航外壳**：确认统一为 `topbar-ws` 横向顶栏（推荐），还是改为 `nav-sidebar` 侧栏？
3. **OpenBridge 体系去留**：OpenBridge（`.ob-*`）是收敛进 components.css 作底层，还是逐步替换为 Wabi-Sabi 组件类？

> 详细的、带伪代码的逐项任务清单见同目录 **`UI美化todos.md`**。
