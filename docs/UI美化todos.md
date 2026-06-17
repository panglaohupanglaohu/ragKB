# UI 美化与优化 Todos（事无巨细 · 含伪代码）

> 配套文档：`UI美化优化plan.md`（策略与现状）
> 范围：`src/frontend/` 13 页 + 共享 CSS/JS
> 约定标记：**【Claude】**=沙箱可做（纯 CSS/HTML/JS，vitest/node 可验）；**【Reasonix】**=本机/浏览器（起服务、视觉回归、Lighthouse）
> 每个 Todo 形如 `[P0/A1]` = 优先级 / 阶段编号。✅ 框为验收点。

---

## 阶段 A · 设计基建（地基，不改任何页面 DOM，零功能风险）

### [P0/A1] 合并共享 CSS 为三层结构  【Claude】

**目标**：把 `variables.css` + `ws-theme-bridge.css` + `openbridge-theme.css` 重构为清晰三层，删除空文件与死文件。

**步骤**：
```pseudo
1. 新建 css/base.css
   - 从 variables.css 拷入：全部 :root 颜色/字体/布局 token
   - 加入全局 reset（现散落在 openbridge-theme.css 的 *,*::before reset）
   - 加入 body / html 基础排版（font-family: var(--font-sans); color: var(--text); bg: var(--bg)）
   - 加入 body::before 和紙噪点纹理（现 4 处重复，统一 1 处）
   - 加入 ::-webkit-scrollbar 样式 + oklch fallback（见 A5）

2. 新建 css/theme.css
   - 合并 ws-theme-bridge.css 的 4 套 [data-obc-theme=...] 变量
   - 合并 openbridge-theme.css 的 4 套 --ob-* 主题变量
   - 去重：同一颜色只保留一份定义，--ob-* 中与 --shironeri 等重复的改为 var() 引用
     例：--ob-bg-body: var(--shironeri);  而非再写一遍 #1A1F25

3. css/components.css —— 见 A3 单独建

4. 归档：
   - git mv css/variables.css css/variables.legacy.css（保留一版，不立即删）
   - git mv css/ws-theme-bridge.css css/ws-theme-bridge.legacy.css
   - rm css/tasks-ws.css            # 仅 14 行，空壳，tasks.html 引用改为 components.css
   - rm js/global-nav.js.bak         # 死文件

5. 暂不改动任何 .html 的 <link>（A6 统一改），保证此步可独立 commit
```
✅ 验收：`base.css` + `theme.css` 内容 = 原 3 文件并集去重；`grep -c` 无重复 token 定义；`npm run build` 通过。

---

### [P0/A2] 补全 token 体系（圆角/间距/阴影/动效/z-index）  【Claude】

**目标**：补齐设计 token，收口 OpenBridge 直角 vs Wabi-Sabi 圆角冲突。

**步骤**：
```pseudo
在 css/base.css 的 :root 追加：

  /* ── 圆角 ── */
  --radius-sm: 3px;
  --radius-md: 6px;     # 见 §决策1：若选直角工业风则改 0
  --radius-lg: 10px;
  --radius-pill: 999px;

  /* ── 间距（8pt grid）── */
  --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px;
  --sp-5: 24px; --sp-6: 32px; --sp-8: 48px;

  /* ── 阴影（统一命名，对接已有 --ws-shadow*）── */
  --shadow-sm: 0 1px 2px var(--ws-shadow, rgba(0,0,0,.2));
  --shadow-md: 0 2px 4px var(--ws-shadow-md, rgba(0,0,0,.3));
  --shadow-lg: 0 4px 16px var(--ws-shadow-lg, rgba(0,0,0,.4));

  /* ── 动效 ── */
  --ease: cubic-bezier(.4, 0, .2, 1);
  --dur-fast: .12s;  --dur: .18s;  --dur-slow: .3s;

  /* ── z-index 层级表 ── */
  --z-base: 0;  --z-dropdown: 100;  --z-sticky: 200;
  --z-overlay: 1000;  --z-modal: 1100;  --z-toast: 1200;

  /* ── 字号尺度 ── */
  --fs-eyebrow: 10px;  --fs-caption: 11px;  --fs-body: 13px;
  --fs-body-lg: 14px;  --fs-h4: 15px;  --fs-h3: 17px;
  --fs-h2: 20px;       --fs-h1: 24px;  --fs-display: 32px;
  --fs-data: 24px;     # readout 大数字

# OpenBridge 圆角变量改为引用（不再硬 0px）：
# 在 theme.css 中
  --ob-radius-sm: var(--radius-sm);
  --ob-radius-md: var(--radius-md);
  --ob-radius-lg: var(--radius-lg);
  --ob-radius-xl: var(--radius-lg);
  --ob-radius-round: var(--radius-pill);
```
✅ 验收：`grep 'radius' theme.css` 全为 `var(--radius-*)`；`.ob-card` 渲染圆角随 `--radius-md` 变。

---

### [P0/A3] 建立 css/components.css 公共组件库  【Claude】

**目标**：从各页内联抽出公共组件，单一实现、全用 token。

**步骤（逐组件，从各页归纳 → 写入 components.css）**：

```pseudo
# ── 按钮 ──（合并 .ob-btn* 与各页自定义 button）
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  gap: var(--sp-2); padding: var(--sp-2) var(--sp-4);
  border: 1px solid var(--groove); border-radius: var(--radius-sm);
  background: var(--hai); color: var(--sumi);
  font: 500 var(--fs-body)/1 var(--font-mono); letter-spacing: .5px;
  cursor: pointer; text-decoration: none;
  transition: background var(--dur) var(--ease), border-color var(--dur) var(--ease);
}
.btn:hover  { background: var(--kabe); }
.btn:active { transform: translateY(1px); box-shadow: inset 0 2px 4px rgba(0,0,0,.12); }
.btn:focus-visible { outline: 2px solid var(--koke); outline-offset: 2px; }
.btn--primary { background: var(--koke); color: var(--shironeri); border-color: var(--koke); }
.btn--primary:hover { background: color-mix(in srgb, var(--koke) 85%, #000); }
.btn--ghost   { background: transparent; }
.btn--danger  { color: var(--shu); border-color: var(--shu); }
.btn--sm      { padding: var(--sp-1) var(--sp-3); font-size: var(--fs-caption); }

# ── 卡片 ──（合并 .ob-card* + plaza .left/.right panel）
.card { background: var(--panel2); border: 1px solid var(--groove); border-radius: var(--radius-lg); overflow: hidden; }
.card__header { display:flex; align-items:center; justify-content:space-between;
  padding: var(--sp-3) var(--sp-4); border-bottom: 1px solid var(--groove); gap: var(--sp-2); }
.card__title  { font: 600 var(--fs-h4)/1 var(--font-serif); color: var(--sumi); letter-spacing: .5px; }
.card__body   { padding: var(--sp-4); }

# ── 表单 ──（合并各页 .form-input/.form-label）
.field { margin-bottom: var(--sp-5); }
.field__label { display:block; font-size: var(--fs-caption); color: var(--sumi-3);
  margin-bottom: var(--sp-1); text-transform:uppercase; letter-spacing:.5px; font-weight:500; }
.input, .textarea, .select {
  width:100%; padding: var(--sp-3) var(--sp-4);
  background: var(--bg); border: 1px solid var(--groove);
  color: var(--sumi); font: 400 var(--fs-body-lg) var(--font-sans);
  border-radius: var(--radius-sm); transition: border-color var(--dur), box-shadow var(--dur);
}
.input:focus, .textarea:focus, .select:focus {
  outline: none; border-color: var(--koke);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--koke) 18%, transparent);
}
.input::placeholder { color: var(--sumi-3); }

# ── 徽章 ──（合并 .ob-badge* + 散落 badge）
.badge { display:inline-flex; align-items:center; gap:4px; font: 570 var(--fs-caption) var(--font-sans);
  padding: 2px var(--sp-2); border-radius: var(--radius-pill); white-space:nowrap; }
.badge--ok      { background: color-mix(in srgb, var(--koke) 12%, transparent); color: var(--koke); }
.badge--warn    { background: color-mix(in srgb, var(--kitsune) 12%, transparent); color: var(--kitsune); }
.badge--danger  { background: color-mix(in srgb, var(--shu) 12%, transparent); color: var(--shu); }
.badge--neutral { background: var(--ridge); color: var(--sumi-2); }

# ── 状态点 ──
.dot { display:inline-block; width:8px; height:8px; border-radius:50%; background: var(--sumi-3); flex-shrink:0; }
.dot--ok { background: var(--koke); }
.dot--warn { background: var(--kitsune); }
.dot--danger { background: var(--shu); }

# ── 表格 ──（合并 .ob-table）
.table { width:100%; border-collapse:collapse; font-size: var(--fs-body); }
.table th { text-align:left; font-weight:570; padding: var(--sp-2) var(--sp-3);
  color: var(--sumi-3); border-bottom:1px solid var(--groove);
  font-size: var(--fs-caption); text-transform:uppercase; letter-spacing:.04em; }
.table td { padding: var(--sp-2) var(--sp-3); border-bottom:1px solid var(--ridge); color: var(--sumi); }
.table tr:hover td { background: var(--ridge); }

# ── 进度条 ──
.progress { width:100%; height:6px; border-radius: var(--radius-pill);
  background: var(--ridge); overflow:hidden; }
.progress__bar { height:100%; border-radius:inherit; background: var(--koke);
  transition: width var(--dur-slow) var(--ease); }
.progress__bar.is-warn { background: var(--kitsune); }
.progress__bar.is-danger { background: var(--shu); }

# ── 骨架屏（新增，配合加载态）──
.skeleton { background: linear-gradient(90deg, var(--ridge) 25%, var(--groove) 37%, var(--ridge) 63%);
  background-size: 400% 100%; animation: skeleton-shimmer 1.4s ease infinite; border-radius: var(--radius-sm); }
@keyframes skeleton-shimmer { 0%{background-position:100% 50%} 100%{background-position:0 50%} }

# ── 空态（新增）──
.empty-state { display:flex; flex-direction:column; align-items:center; justify-content:center;
  padding: var(--sp-8) var(--sp-4); text-align:center; gap: var(--sp-2); color: var(--sumi-3); }
.empty-state__icon { font-size: 40px; opacity:.5; }
.empty-state__title { font: 600 var(--fs-h4) var(--font-serif); color: var(--sumi-2); }
.empty-state__desc { font-size: var(--fs-body); max-width: 320px; }

# ── Toast（统一，取代各页 inline）──
.toast { position: fixed; right: var(--sp-4); bottom: var(--sp-4); z-index: var(--z-toast);
  padding: var(--sp-3) var(--sp-4); border-radius: var(--radius-md);
  background: var(--ws-toast-bg, var(--panel2)); border:1px solid var(--groove);
  font-size: var(--fs-body); box-shadow: var(--shadow-lg); max-width: 380px; }
.toast--error   { background: var(--ws-toast-error-bg); border-color: var(--shu); color: var(--shu); }
.toast--success { background: var(--ws-toast-success-bg); border-color: var(--koke); color: var(--koke); }
.toast--warn    { background: var(--ws-toast-warn-bg); border-color: var(--kitsune); color: var(--kitsune); }

# ── 模态（统一，含无障碍）──
.modal { position:fixed; inset:0; z-index: var(--z-modal); display:none;
  align-items:center; justify-content:center; }
.modal.is-open { display:flex; }
.modal__overlay { position:absolute; inset:0; background: rgba(0,0,0,.5); }
.modal__panel { position:relative; z-index:1; background: var(--panel2);
  border:1px solid var(--groove); border-radius: var(--radius-lg);
  max-width: 520px; width:90%; max-height:85vh; overflow:auto;
  box-shadow: var(--shadow-lg); }
.modal__header { display:flex; align-items:center; justify-content:space-between;
  padding: var(--sp-4); border-bottom:1px solid var(--groove); }
.modal__close { background:none; border:none; color: var(--sumi-3);
  font-size:20px; cursor:pointer; }
.modal__close:hover { color: var(--shu); }
.modal__body { padding: var(--sp-4); }
# 配合 JS：role="dialog", aria-modal="true", aria-labelledby, 打开时焦点陷阱、Esc 关闭
```
✅ 验收：`components.css` 内 `grep '#[0-9a-fA-F]'` 应只在 `color-mix` 与 `rgba(0,0,0,.5)` overlay 出现，无裸品牌色 hex。

---

### [P1/A4] 统一导航外壳 + 单一导航数据源  【Claude】

**目标**：全站统一为 `topbar-ws` 横向顶栏；新建 `js/nav.js` 取代 `global-nav.js` + `nav-sidebar.js` 的双轨。

> ⚠️ **回归教训（bug-021）**：本任务把顶栏统一为普通流 `.topbar-ws`(position:relative,56px)，但 `plaza.html` 等页面的 `.layout` 还保留着为「固定/绝对定位顶栏」时代写的 `margin-top:56px`（叠加 `height:calc(100vh-56px)` 会溢出视口 56px，把底部按钮挤出屏幕）。**改顶栏前必须先做下面的步骤 0 审计。**

**步骤**：
```pseudo
0. 【必做·先于一切】审计各页对固定顶栏的布局假设：
   grep -rn 'margin-top:\s*56px\|padding-top:\s*56px\|top:\s*56px\|calc(100vh' src/frontend/*.html src/frontend/css/*.css
   - 顶栏既然是普通流(自然占 56px)，这些为固定顶栏预留的偏移多半要删/改
   - 每改一页，浏览器实测：底部控件 inView、内容不溢出视口、不被顶栏遮挡

1. 新建 js/nav.js（单一数据源）
   const PAGES = [
     {id:'agents',     label:'智能体团队', href:'/agent-team-config.html'},
     {id:'plaza',      label:'议事广场',   href:'/plaza.html'},
     {id:'skill-extract', label:'技能萃取/赋予', href:'/skill-extract.html'},
     {id:'digital-twin',  label:'数字孪生',   href:'/Agent-digital-twin.html'},
     {id:'evolution',  label:'系统演进',   href:'/system-evolution.html'},
     {id:'cost',       label:'成本监控',   href:'/cost-dashboard.html'},
   ];
   function renderNav(currentId){ /* 填充 .topbar-ws__nav，当前页加 .cur */ }
   # 用户/登出：从 localStorage('ag-user') 渲染到 .topbar-ws__user
   # 主题切换 + 语言切换：从 nav-sidebar.js 迁移逻辑到 nav.js（按钮放顶栏右侧）

2. 各页 <script src="/js/nav.js" data-page="xxx"></script>
   - 替换 global-nav.js 引用（datacenter-ratchet-evolution / extraction-pipeline）
   - 替换 nav-sidebar.js 引用（若有页面用）

3. nav-sidebar.js 处理：
   - 移除 21 个占位项（captain/navigation/dp/... 实际不存在的页面）
   - 文件保留为「可选侧栏模式」，不在任何页默认注入（init 里的自动 wrap 移除）

4. global-nav.js：标记 deprecated，逻辑并入 nav.js 后清空引用
```
✅ 验收：`grep -rl 'global-nav.js\|nav-sidebar.js' src/frontend/*.html` 命中数为 0；每页顶栏 6 个真实链接 + 当前页高亮；**且每页在浏览器实测：底部控件 inView、内容不溢出视口、不被普通流顶栏遮挡（步骤 0 防 bug-021 回归）。**

---

### [P1/A5] 滚动条 + oklch/color-mix fallback 统一  【Claude】

**目标**：滚动条统一 8px 可读，补全 oklch fallback；night 主题滚动条隐入。

**步骤**：
```pseudo
# 在 css/base.css 末尾
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--nezumi); border-radius: var(--radius-pill); }
::-webkit-scrollbar-thumb:hover { background: var(--sumi-3); }

# Firefox
* { scrollbar-width: thin; scrollbar-color: var(--nezumi) transparent; }

# night 主题：滚动条隐入
[data-obc-theme='night'] ::-webkit-scrollbar-thumb { background: rgba(71,71,0,.3); }

# oklch fallback（thumb 颜色）
@supports not (color: oklch(0 0 0)) {
  ::-webkit-scrollbar-thumb { background: #64707A; }
}

# color-mix fallback 已在 variables.css 有，核对覆盖所有用到处（C3 再扫）
```
✅ 验收：Chrome/Safari/Firefox 三浏览器滚动条一致；关掉 oklch 支持（DevTools）不报错。

---

### [P0/A6] 全页 <link> 统一到新三层  【Claude】

**目标**：所有 13 页的 `<head>` 统一引用同一套 CSS 子集。

**步骤**：
```pseudo
对每个 *.html：
  <link rel="stylesheet" href="/css/base.css">
  <link rel="stylesheet" href="/css/theme.css">
  <link rel="stylesheet" href="/css/components.css">
  <link rel="stylesheet" href="/css/topbar-ws.css">
  # 页面专属 css 保留（如 css/agent-team-config.css），但删去对 variables.css/ws-theme-bridge.css/openbridge-theme.css 的直接引用（已并入 base+theme）

# 批量替换（sed 或手动，逐页确认）：
  删除：href="/css/variables.css"
  删除：href="/css/ws-theme-bridge.css"
  删除：href="/css/openbridge-theme.css"
  新增：base.css + theme.css + components.css（置于 topbar-ws.css 之前）

# 注意 CSP meta：每个 <head> 已有 CSP，无需改（同源 css）
```
✅ 验收：`grep -l 'variables.css\|ws-theme-bridge.css\|openbridge-theme.css' src/frontend/*.html` = 空；每页 head 顺序一致。

---

## 阶段 B · 逐页迁移（消灭内联 style，按量从大到小）

> 每页通用迁移套路（B1~B8 重复使用）：
> ```pseudo
> function migratePage(htmlFile, inlineStyleBlock, newCssFile):
>   1. 把 htmlFile 的 <style>...</style> 内容剪切到 newCssFile
>   2. 在 htmlFile <head> 加 <link href="/css/{newCssFile}">
>   3. 扫 newCssFile 所有 #hex / rgb() 字面量 → 换成 var(--token):
>        sed: s/#1A1F25/var(--shironeri)/g  等（按 token 映射表）
>   4. 能用 components.css 组件类的，替换 class 名:
>        .form-input → .input ; .form-label → .field__label
>        各页自定义 button → .btn 系列
>        panel/card → .card 系列
>   5. vitest run 回归
>   6. 浏览器逐页核对（Reasonix）
> ```

### [P0/B1] Agent-digital-twin.html（内联 657 行，72 hex）  【Claude + Reasonix】

```pseudo
# 这页最重。分两步：
# B1a. 颜色 token 化（优先）
  建映射表（72 处 hex → token）：
    #fbbf24(amber数据) → var(--kitsune)
    #a78bfa(purple)    → 新增 token --fuji: #a78bfa  （若数字孪生场景需要第4语义色，写入 base.css）
    #22d3ee(cyan)      → var(--koke)  # 或新增 --mizui:#22d3ee 作为 cyan 区别于 lime
    #f87171(red)       → var(--shu)
    #34d399(green)     → var(--koke)
    #111820/#0d1117(深底) → var(--shironeri) / var(--concrete-deep)
    #e2e8f0(浅字)      → var(--sumi)
  # 关键决策：cyan(#22d3ee) vs lime(#6bc47f) 当前 --koke 是 lime。
  #   若数字孪生需要 cyan 与 green 区分，新增 --mizui:#22d3ee 作为 cyan 语义色。

# B1b. 抽出到 css/digital-twin.css（657 行 → 外部文件）
  migratePage('Agent-digital-twin.html', inlineBlock, 'css/digital-twin.css')
```
✅ 验收：`grep -oE '#[0-9a-fA-F]{6}' Agent-digital-twin.html` 内联区 = 0；主题切换 3D 配色随变（§4）。

---

### [P0/B2] digital-twin-cli.html（内联 320 行，42 hex）  【Claude】

```pseudo
# 同 B1。#22d3ee/#34d399 套色 → token（--mizui/--koke 或合并）
migratePage('digital-twin-cli.html', inlineBlock, 'css/digital-twin-cli.css')
# 这页还有 topbar-ws(9 引用) + 内联并存，迁移后内联清空
```
✅ 验收：内联 `<style>` < 30 行（仅保留无法外置的页面唯一样式）。

---

### [P1/B3] login.html（内联 261 行）  【Claude】

```pseudo
# 登录页最该用组件库。重写内联为：
  .login-wrap { min-height:100vh; display:flex; align-items:center; justify-content:center; padding: var(--sp-6); }
  .login-card { extends .card; max-width:420px; padding: var(--sp-8) var(--sp-6); }  # 用 .card
  .login-brand .seal { ...用 token... }
  # 表单全用 .field / .input / .btn--primary
# 抽出 css/login.css 或直接清空内联（若全可由 components 覆盖）
```
✅ 验收：login 页全部元素用组件类；无内联 `<style>`（或 < 20 行）。

---

### [P1/B4] plaza.html（内联 255 行，安藤忠雄混凝土自体系）  【Claude + Reasonix】

```pseudo
# plaza 自定义一套 --concrete* token，映射进 theme.css：
  --concrete       → var(--shironeri)   # 实际值相同 #1A1F25/#23282E 已接近
  --concrete-light → var(--kabe)
  --concrete-pale  → var(--hai)
  --concrete-dark  → var(--shironeri)
  --surface        → var(--panel2)
  --slit-light/glow→ var(--sumi-2)
  --bronze*        → var(--nezumi)
  --ink            → var(--sumi)
# 语音气泡 color-mix 保留（高级特性），但颜色来源变量化：
  --bubble-color: var(--koke);  /* 默认，JS 可覆盖 */
# 63 处 hex：#F0A050→var(--kitsune-ish,#F0A050 可作 --terracotta) ; #5b9bd5→var(--mizui); #E25555→var(--shu)
# 抽出 css/plaza.css
migratePage('plaza.html', inlineBlock, 'css/plaza.css')
```
✅ 验收：plaza 内联 < 30 行（仅 three-canvas 容器等必要项）；主题切换混凝土色调随之变。

---

### [P2/B5] system-evolution.html（内联 197 行）  【Claude】
```pseudo
migratePage('system-evolution.html', inlineBlock, 'css/system-evolution.css')
# 进化时间轴抽 .timeline / .timeline__item 组件进 components.css（若复用）
```

### [P2/B6] extraction-pipeline.html（内联 110 行）  【Claude】
```pseudo
migratePage('extraction-pipeline.html', inlineBlock, 'css/extraction-pipeline.css')
# 接入 topbar-ws + nav.js（当前无导航外壳）
```

### [P2/B7] datacenter-ratchet-evolution.html（内联 118 行）  【Claude】
```pseudo
migratePage('datacenter-ratchet-evolution.html', inlineBlock, 'css/datacenter.css')
# 替换 global-nav.js → nav.js + topbar-ws
```

### [P2/B8] tasks.html（内联 31 行）  【Claude】
```pseudo
# 删 css/tasks-ws.css（已在 A1 删）。内联 31 行清空 → 全用 components.css
# tasks 表格用 .table，状态用 .badge/.dot
```

### [P2/B9] 已外部 CSS 的页面：agent-team-config / cost-dashboard / sandbox-twin / skill-extract  【Claude】
```pseudo
# 这 4 页无内联，只做：
#   - token 对齐（外部 css 里的 hex → var）
#   - 组件类替换（.ob-btn → .btn 等，保留 .ob-* 别名避免 JS 依赖断裂）
#   - 每页单独 commit
```

---

## 阶段 C · 视觉精修（美化本体）

### [P1/C1] 排版层级统一  【Claude】
```pseudo
# 定义标题类（components.css）
.eyebrow { font: 600 var(--fs-eyebrow) var(--font-sans); letter-spacing:.18em;
  text-transform:uppercase; color: var(--kitsune); }
.h1/.h2/.h3/.h4 { font-family: var(--font-serif); color: var(--sumi); }
.h1{font-size:var(--fs-h1);font-weight:600} .h2{font-size:var(--fs-h2)} ...
.mono-label { font: 400 var(--fs-caption) var(--font-mono); letter-spacing:1.5px;
  text-transform:uppercase; color: var(--sumi-3); }  # 取代各页散落的 sec-title
# 全页核对：h1~h4 字号字重一致，三声部（serif标题/sans正文/mono数据）清晰
```

### [P1/C2] 间距节奏统一到 8pt  【Claude】
```pseudo
# 扫所有 css 的 padding/margin/gap 字面量
# 凡 4/8/12/16/24/32/48 → var(--sp-1..8)
# 凡奇数值（5/10/14/20）→ 归一到最近 sp token（10→sp-2 或 sp-3 按语境）
# 重点：内容区 padding 统一 var(--sp-4)，卡片 gap 统一 var(--sp-4)
```

### [P0/C3] 微交互 + focus-visible 无障碍  【Claude】
```pseudo
# 所有可交互元素补：
  :focus-visible { outline: 2px solid var(--koke); outline-offset: 2px; }
# hover/active 过渡统一用 var(--dur) var(--ease)
# 按钮/卡片/列表项 hover 态已在 components.css 定义，核对各页覆盖一致
# 扫 color-mix 所有用法，补 @supports not fallback（variables.css 已有模板）
```
✅ 验收：Tab 键遍历每页，焦点环清晰可见。

### [P1/C4] 加载/空/错误态 UI 统一  【Claude + Reasonix】
```pseudo
# api() 已统一 try/catch + toast。前端补：
#   - 列表加载中：渲染 .skeleton 占位（取代空白）
#   - 列表空：渲染 .empty-state（图标+标题+文案+CTA）
#   - 请求失败：.empty-state + 重试按钮
# 每个列表页（plaza/tasks/agent-team-config/cost-dashboard）统一三态
```

### [P2/C5] 滚动条美化  【Claude】 — 已在 A5 完成，此处核对全页生效。

### [P0/C6] 暗色对比度达标  【Reasonix + Claude】
```pseudo
# 用 Lighthouse / axe 核对：
#   --sumi-3 / --muted (#7C8792) 对 --shironeri (#1A1F25) 背景对比度
#   计算：约 4.6:1，刚好 AA（正文 4.5）。若 --sumi-3 用于小字，需提到 --sumi-2(#A2ABB4)
# 调整 token：小号 caption/muted 文本统一用 --sumi-2 而非 --sumi-3
# day/bright 主题同样核对
```
✅ 验收：Lighthouse Accessibility 全页 ≥ 95。

---

## 阶段 D · 性能与可访问性收尾

### [P2/D1] 字体加载优化  【Claude + Reasonix】
```pseudo
# 当前每页 <link href="fonts.googleapis.com/...Noto Sans/Serif SC + JetBrains Mono">
# 优化：
#   1. <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>（部分页已有，补全）
#   2. font-display: swap（Google CSS 已带，确认）
#   3. 可选：自托管字体子集（中文按页用字 subset），减少首屏阻塞
#      工具：pyftsubset / fontmin，按每页实际出现的汉字生成 woff2
```

### [P1/D2] 无障碍基线  【Claude】
```pseudo
# 顶栏：<nav class="topbar-ws__nav" aria-label="主导航">
# 模态：role="dialog" aria-modal="true" aria-labelledby=<title-id>
#   + 焦点陷阱（Tab/Esc 处理）—— JS 在 nav.js 或 utils.js 提供 trapFocus(modal)
# 3D canvas：<canvas aria-label="数字孪生三维场景" role="img">
# 图标按钮（关闭/删除）：aria-label 描述动作
# 颜色非唯一信息载体：状态除颜色外加文字/图标（.badge 已带文字，核对 .dot 处补 title）
```

### [P2/D3] console 收敛 + 时钟性能  【Claude】
```pseudo
# nav-sidebar.js 的 setInterval(updateClock, 1000)：已是 textContent 赋值，轻量，保留
#   但若移除 nav-sidebar（A4），则时钟逻辑迁 nav.js
# 各页 console.log/warn 收敛到 DEBUG 开关：
#   window.DEBUG || console.log → 封装 utils.js log()/dbg()
```

### [P1/D4] Lighthouse 基线与目标  【Reasonix】
```pseudo
# 对 13 页跑 Lighthouse（Mobile + Desktop），记录：
#   Performance / Accessibility / Best Practices / SEO
# 目标：Accessibility ≥ 95（C6 达成），Best Practices ≥ 95
# Performance 视 Three.js 页面而定（3D 重，不强求满分）
# 结果写入 docs/reports/ui-lighthouse-baseline.md
```

### [P0/D5] 颜色字面量 lint 门禁  【Claude】
```pseudo
# 在 scripts/ 加 lint 脚本 check-no-inline-color.sh：
  #!/usr/bin/env bash
  # 扫 src/frontend/*.html 的 <style> 块内 #hex/rgb 字面量（排除 3D canvas 例外）
  set -e
  for f in src/frontend/*.html; do
    hits=$(sed -n '/<style>/,/<\/style>/p' "$f" | grep -cE '#[0-9a-fA-F]{6}|rgba?\([0-9]' || true)
    [ "$hits" -gt 0 ] && echo "WARN $f: $hits color literals in inline style"
  done
# 可接入 CI（.github/workflows）作为防回归
```
✅ 验收：脚本在迁移完成后对 13 页 0 命中（3D 例外白名单）。

---

## 全局验收清单（Definition of Done）

- [ ] `grep -rE '#[0-9a-fA-F]{6}' src/frontend/*.html`（限 `<style>` 块）= 0（3D 例外）
- [ ] 13 页内联 `<style>` 总行数 < 200（基线 ~1950）
- [ ] 每页 `<head>` 引用同一套 base+theme+components+topbar-ws
- [ ] 导航统一 topbar-ws + nav.js，无 global-nav/nav-sidebar 默认注入
- [ ] 4 主题（day/dusk/night/bright）在 13 页切换无残色、无对比度故障
- [ ] `npx vitest run` 全绿
- [ ] Lighthouse Accessibility 全页 ≥ 95（docs/reports 记录）
- [ ] 死文件清理：tasks-ws.css / global-nav.js.bak 已删；legacy css 归档

---

## 执行顺序建议（依赖关系）

```
A1 → A2 → A3 ─┐
A4 ────────────┤
A5 ────────────┼→ A6（全页换 link）→ B1..B9（逐页，可并行多 commit）→ C1..C6 → D1..D5
```
- A1~A5 互不依赖页面，可快速连做；A6 是「基建→页面」的切换点。
- B1~B9 每页独立，可分派给多次会话，互不阻塞。
- C/D 是精修，可按优先级穿插。
