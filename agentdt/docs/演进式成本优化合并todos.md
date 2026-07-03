<!-- docs-signoff: author="CodeBuddy (GLM-5.2)" kind="llm" doc="todos" ts="2026-06-18T12:50:00Z" -->

# 演进式成本优化 — 合并实施 TODOS

> **本文件元信息**：由 CodeBuddy (GLM-5.2) 于 2026-06-18 12:50 UTC 创建。签名块见第一行。

## Phase 1: 后端清理 — 移除无用 API（可选，低优先）

- [ ] **1.1** 保留后端 API 不动（演进条目/审计/趋势的 API 保留，前端不调用即可）
  - 理由：后端 API 可能被其他地方引用，先只做前端合并
  - 伪代码：无变更

## Phase 2: 页面标题与导航

- [ ] **2.1** 修改 `cost-dashboard.html` 的 `<title>` 和页面标题
  - 当前：`<title>成本监控</title>` → 新：`<title>演进式成本优化</title>`
  - 当前页面内标题：`成本监控` → `演进式成本优化`
  - 伪代码：
    ```html
    <!-- cost-dashboard.html -->
    <title>演进式成本优化</title>
    ...
    <h1>演进式成本优化</h1>
    <div class="subtitle">Token 最小化 · 棘轮演进 · 治理闭环</div>
    ```

- [ ] **2.2** 修改全局 topbar 导航，移除「系统演进」入口
  - 涉及文件：所有包含 topbar 的 HTML 页面中的导航链接
  - 伪代码：
    ```javascript
    // 在每个 HTML 的 topbar 中：
    // 删除 <a href="/system-evolution.html">系统演进</a>
    // 修改 <a href="/cost-dashboard.html">成本监控</a> → <a href="/cost-dashboard.html">演进式成本优化</a>
    ```

- [ ] **2.3** 在 `cost-dashboard.html` 中引入 `system-evolution.js`
  - 伪代码：
    ```html
    <!-- cost-dashboard.html 底部 -->
    <script src="/js/system-evolution.js"></script>
    ```

## Phase 3: 治理动作菜单上移

- [ ] **3.1** 找到 cost-dashboard 中的「治理动作」菜单当前位置
  - 伪代码：
    ```javascript
    // cost-dashboard.html 中搜索 "治理动作" 或 "governance"
    // 确认其当前在页面的哪个区域（通常是底部或侧栏）
    ```

- [ ] **3.2** 将治理动作菜单移到页面顶部操作栏
  - 伪代码：
    ```html
    <!-- 页面顶部新增操作栏 -->
    <div class="action-bar" style="display:flex;gap:8px;padding:12px 16px;border-bottom:1px solid var(--line)">
      <button onclick="evaluateCostGate()">🚦 成本门禁评估</button>
      <button onclick="generateGovernanceGoals()">🎯 生成治理目标</button>
      <button onclick="runSustainabilityCheck()">📈 可持续性检查</button>
    </div>
    ```

## Phase 4: 移入演进概览

- [ ] **4.1** 从 `system-evolution.html` 提取 `panel-overview` 的 HTML 结构
  - 包含：合规评级、演进统计、棘轮迷你图、最近条目
  - 伪代码：
    ```html
    <!-- cost-dashboard.html 新增右侧面板 -->
    <div class="evolution-panel">
      <h2>演进概览</h2>
      <div id="ov-rating"><!-- 合规评级 SVG 环 --></div>
      <div id="ov-stats"><!-- 演进统计卡片 --></div>
      <div id="ov-ratchet"><!-- 棘轮迷你4步图 --></div>
      <div id="ov-items"><!-- 最近10条演进条目 --></div>
    </div>
    ```

- [ ] **4.2** 移植 `system-evolution.js` 中加载概览数据的函数
  - 函数名：`loadOverview()` 或类似
  - 伪代码：
    ```javascript
    // system-evolution.js 中已有的函数，确保在 cost-dashboard 页面加载时也调用
    function loadEvolutionOverview() {
      fetch('/api/v1/agent-teams/evolution/audit')
        .then(r => r.json())
        .then(data => {
          renderRating('#ov-rating', data.rating);
          renderStats('#ov-stats', data.stats);
          renderRatchetMini('#ov-ratchet', data.ratchet);
          renderRecentItems('#ov-items', data.items);
        });
    }
    // 在 cost-dashboard 的 init 中调用
    ```

## Phase 5: 移入达尔文棘轮

- [ ] **5.1** 从 `system-evolution.html` 提取 `panel-ratchet` 的 HTML 结构
  - 包含：5步闭环流程图、遗产账本
  - 伪代码：
    ```html
    <div class="ratchet-panel">
      <h2>达尔文棘轮 — 不可逆演进</h2>
      <div id="ratchet-flow"><!-- 5步流程图 --></div>
      <div id="ratchet-ledger-metrics"><!-- 全局棘轮指标 --></div>
      <div id="heritage-list"><!-- 遗产账本列表 --></div>
      <button onclick="runCycleOnRatchet()">▶ 运行完整周期</button>
    </div>
    ```

- [ ] **5.2** 移植棘轮相关 JS 函数
  - 函数：`runCycleOnRatchet()`、`runAuditOnly()`、`loadRatchetMetrics()`、`loadHeritageLedger()`
  - 伪代码：
    ```javascript
    // 确保这些函数在 system-evolution.js 中已定义为全局函数
    // cost-dashboard 页面加载时自动调用 loadRatchetMetrics() 和 loadHeritageLedger()
    ```

## Phase 6: 删除废弃 Tab

- [ ] **6.1** 从 `system-evolution.js` 中删除以下 Tab 的渲染逻辑
  - `panel-evolve-lab`（技能演化）— 删除 `loadEvolveLab()` 等函数
  - `panel-rules-zones`（规则与区域）— 删除 `loadRules()`、`loadZones()` 等
  - `panel-items`（演进条目）— 删除 `loadItems()` 等
  - `panel-trail`（审计轨迹）— 删除 `loadTrail()` 等
  - `panel-trend`（趋势分析）— 删除 `loadTrend()` 等
  - 伪代码：
    ```javascript
    // system-evolution.js 中删除：
    // - loadEvolveLab 及其子函数 (runAutoTriage, loadEvolveTeams, loadEvolveSkills 等)
    // - loadRules, loadZones
    // - loadItems, renderItemDetail
    // - loadTrail
    // - loadTrend, renderTrendChart
    // 保留：loadOverview, loadRatchetMetrics, loadHeritageLedger, runCycleOnRatchet, runAuditOnly
    ```

## Phase 7: 新增 Token 优化建议区

- [ ] **7.1** 在页面底部新增「Token 优化建议」区域
  - 展示当前 token 消耗最高的团队/任务，并给出 skill 萃取/路由建议
  - 伪代码：
    ```html
    <div class="token-optimization-panel">
      <h2>💡 Token 优化建议</h2>
      <div id="token-hotspots"><!-- token 消耗 Top 5 团队/任务 --></div>
      <div id="skill-suggestions"><!-- 技能萃取/路由建议 --></div>
    </div>
    ```

- [ ] **7.2** 新增 JS 函数加载优化建议
  - 伪代码：
    ```javascript
    async function loadTokenOptimization() {
      const cost = await fetch('/api/v1/cost/by-team').then(r => r.json());
      const hotspots = cost.teams.sort((a, b) => b.tokens - a.tokens).slice(0, 5);
      document.getElementById('token-hotspots').innerHTML = hotspots.map(t => 
        `<div>${t.name}: ${t.tokens} tokens — 建议萃取技能减少重复调用</div>`
      ).join('');
    }
    ```

## Phase 8: CSS 整合

- [ ] **8.1** 从 `system-evolution.html` 提取演进概览和棘轮的 CSS 样式
  - 伪代码：
    ```css
    /* cost-dashboard.css 追加 */
    .evolution-panel { /* 演进概览容器 */ }
    .ratchet-panel { /* 棘轮容器 */ }
    .ratchet-flow-step { /* 5步流程节点 */ }
    .heritage-item { /* 遗产账本条目 */ }
    ```

## Phase 9: 布局调整

- [ ] **9.1** 将 cost-dashboard 改为左右分栏布局
  - 左侧：成本监控（原有内容）
  - 右侧：演进概览 + 棘轮
  - 伪代码：
    ```css
    .main-layout {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    ```

## Phase 10: 测试与验证

- [ ] **10.1** 验证页面加载无报错
  - 伪代码：
    ```bash
    curl -s http://localhost:5173/cost-dashboard.html | grep -c "演进式成本优化"
    # 应返回 1
    ```

- [ ] **10.2** 验证演进概览数据加载
  - 伪代码：
    ```javascript
    // 浏览器控制台执行
    fetch('/api/v1/agent-teams/evolution/audit').then(r => r.json()).then(console.log)
    // 应返回 rating 和 stats 数据
    ```

- [ ] **10.3** 验证棘轮数据加载
  - 伪代码：
    ```javascript
    fetch('/api/v1/ratchet/metrics').then(r => r.json()).then(console.log)
    // 应返回棘轮指标
    ```

- [ ] **10.4** 验证治理动作按钮可点击
  - 伪代码：手动点击顶部操作栏的三个按钮，确认有响应

## Phase 11: 清理

- [ ] **11.1** 删除 `system-evolution.html`（合并完成后）
  - 伪代码：`rm src/frontend/system-evolution.html`

- [ ] **11.2** 清理 `system-evolution.js` 中无用的导入和函数
  - 伪代码：删除 Phase 6 中标记的所有废弃函数

- [ ] **11.3** 更新 vite.config.mjs 中的页面入口
  - 伪代码：
    ```javascript
    // vite.config.mjs 中删除 systemEvolution 入口
    // input: { ... systemEvolution: page('system-evolution.html'), ... }
    // 改为不包含 systemEvolution
    ```
