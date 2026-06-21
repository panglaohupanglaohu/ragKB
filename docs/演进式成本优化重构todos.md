<!-- docs-signoff: author="GitHub Copilot" kind="llm" doc="todos" ts="2026-06-18T16:41:30Z" -->

# 演进式成本优化 — 页面重构 TODOS（在 GLM-5.2 合并基础上的优化）

> 目标：本页面通过 **skill 萃取 · skill 路由 · Agent 协同**，让系统完成特定业务场景任务时
> 耗费的 **token 最少**。本轮在 GLM 合并版本上做"聚焦重构"：删数据堆砌、修样式错配、降级无意义告警。

## 根因（GLM 合并版本的 3 个问题）

1. **右侧丑** — `system-evolution.js` 的 `loadOverview / buildMiniRatchet / loadRatchetMetrics / loadHeritageLedger`
   渲染的 class（`stat-card / gauge-ring / ratchet-node / tbl / heritage-item / ratchet-ledger-grid`）
   定义在 `system-evolution.css`，而本页 **从未加载该 CSS**；GLM 内联 `<style>` 用的是 `ev-*` 另一套命名 → 永不匹配 → 裸样式。
2. **顶部红条无意义** — `cost-dashboard.js` 在 OpenCost 无数据（本机常态）时 `showAlert(...)` 弹顶部红条 + 请求ID，
   喧宾夺主于"token 最小化"主题。
3. **范围蔓延** — 用户要删的数据堆砌面板（遗产账本 / 全局棘轮指标 / 域·严重度·运营域 / 演进条目表）GLM 全留了。

---

## Phase 1 · 样式系统对齐（cost-dashboard.html `<style>`）

- [x] **1.1** 删除错配/无用内联样式：`ev-heritage-item`、`ev-card-grid`、`main-split`、`.ev-panel`（旧）。
- [x] **1.2** 新增对齐 `--ob-*` 设计 token 的样式：`.ev-band / .ev-tag / .ev-overview-grid / .ev-stat-card /
      .ev-gauge-card / .ev-gauge / .ev-ratchet-*（用 --koke/--shu/--ob-border）/ .ev-cycle-log / .token-suggest`。
  - 伪代码（关键）：
    ```css
    .ev-band{display:grid;grid-template-columns:1.05fr .95fr;gap:20px}
    @media(max-width:1100px){.ev-band{grid-template-columns:1fr}}
    .ev-ratchet-dot{border:2px solid var(--ob-border);background:var(--ob-bg-section)}
    .ev-ratchet-dot.active{border-color:var(--koke);box-shadow:0 0 0 3px rgba(107,196,127,.18);animation:ev-pulse 2s infinite}
    .ev-ratchet-dot.done{border-color:var(--koke);background:rgba(107,196,127,.12);color:var(--koke)}
    .ev-ratchet-connector.done{background:var(--koke)}
    ```

## Phase 2 · 降级告警（顶部红条 → 面板内联状态）

- [x] **2.1** 删除 `<div id="dashboard-alert">` 顶部告警容器。
  - `cost-dashboard.js#showAlert` 已 `if(!alert) return;` → 删容器即静默降级，无需改 JS。
- [x] **2.2** OpenCost 状态由 `cost-header` 内的状态点 + `治理动作` 面板承载（内联、不抢镜）。
  - 伪代码：`updateStatus()` 已把 `#status-text` 写为 "无数据/已连接"，作为唯一的内联状态提示。

## Phase 3 · 布局重构（删堆砌，单列叙事）

- [x] **3.1** 删除右列 5 个面板：旧"演进概览"、棘轮迷你流程、最近演进条目表、达尔文棘轮详情(重复)、
      全局棘轮指标、遗产账本。
- [x] **3.2** 改为自上而下 token 叙事：
      `KPI 概览 → [演进概览 + 达尔文棘轮]band → 效率视角 → Token 优化建议 → 成本图表 → Pod 明细 → 治理动作`。
- [x] **3.3** 全部演进区块改用本页设计系统的 `.panel / .panel__head / .panel__sub`，保留唯一一条
      已可正常动画的 5 步棘轮 `#ratchet-flow`（`r-audit/r-dispatch/r-verify/r-close/r-lock` + `rc-1..4`）。

## Phase 4 · 自包含渲染（不依赖 system-evolution.js 的破损渲染器）

- [x] **4.1** 新增 `renderEvOverview()`（内联脚本），直接拉 `EVP/summary` + `EVP/compliance-rating`，
      用 `ev-gauge-card / ev-stat-card` 渲染合规评级仪表 + 审查规则/验证函数/演进项统计。无 `panel-badge`、无数据堆砌。
  - 伪代码：
    ```js
    async function renderEvOverview(){
      const [summary, compliance] = await Promise.all([get('/.../summary'), get('/.../compliance-rating')]);
      let html='';
      if(compliance){ const s=clamp(compliance.score,0,100), col=gradeColor(compliance.grade);
        const C=2*PI*30, dash=s/100*C;
        html+=gaugeCard(compliance.grade, s, col, dash, compliance); }   // SVG 环形仪表
      if(summary){ html+=statCard('审查规则',summary.audit_rules_count)
                       + statCard('验证函数',summary.verify_tests_registered)
                       + statCard('演进项 共'+summary.total_items, byStatusText(summary.by_status)); }
      host.innerHTML = html ? `<div class="ev-overview-grid">${html}</div>` : muted('演进概览暂不可用');
    }
    ```
- [x] **4.2** `loadEvolutionPanels()` 仅调 `renderEvOverview()`；移除 `loadOverview/loadRatchetMetrics/loadHeritageLedger`。
- [x] **4.3** 覆写 `window.runCycleOnRatchet`：先把 `r-*/rc-*` 复位为 `ev-ratchet-*`（保留本页样式），
      再走 `RatchetAnimator.runCycle`（只 add active/done，兼容 ev 样式），`onComplete → renderEvOverview()`（替换原 `loadHeritage`）。
  - 伪代码：
    ```js
    window.runCycleOnRatchet = async () => {
      resetEv(['r-audit','r-dispatch','r-verify','r-close','r-lock'],'ev-ratchet-dot');
      resetEv(['rc-1','rc-2','rc-3','rc-4'],'ev-ratchet-connector');
      await RatchetAnimator.runCycle({ dotIds:[...], connIds:[...], lockId:'r-lock',
                                       logEl:'ratchet-log', onComplete: renderEvOverview });
    };
    ```
- [x] **4.4** 保留 `loadTokenOptimization()`（`/api/v1/cost/by-team` → token 热点 + skill 萃取/路由建议）。

## Phase 5 · 安全性确认（无破坏既有页面）

- [x] **5.1** 不改 `system-evolution.js`（`system-evolution.html` 仍依赖它）；仅在本页内联覆写 `runCycleOnRatchet`。
- [x] **5.2** 模块加载期自动 `loadOverview()` 在本页因缺 `ov-*` 元素而 `renderError/renderEmpty` 已 `if(!c)return` → 安全空操作。
- [x] **5.3** `_startSSE()` 回退轮询检查 `.tab-panel.active`（本页无）→ 不触发任何渲染，安全。

## 验证清单

- [x] `node --check` 等价校验：编辑器 `get_errors` 对 `cost-dashboard.html` 无报错。
- [ ] 浏览器自检：OpenCost 无数据时无顶部红条；右侧演进概览有样式（仪表 + 统计卡）；点"运行棘轮演进周期"动画沿 ev 样式推进并锁定。
- [ ] 回归：`scripts/regression-smoke.cjs`（若覆盖该页）通过。
