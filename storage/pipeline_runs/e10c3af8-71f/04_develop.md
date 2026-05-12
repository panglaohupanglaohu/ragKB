# 代码开发 — developer

任务: 后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
步骤: develop
Agent: build_developer

---

📋 任务: e10c3af8-71f
🤖 Agent: Developer (developer)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 Developer (developer)。
  请执行以下开发任务:
  
  你是开发工程师 (DeepSeek V4 + 工具循环模式)。
  你**已经被赋予真正的工具能力**: read_file / grep / list_files / write_file / patch_file / run_python。
  禁止凭空想象 — 所有写代码前必须先用工具读真实代码。
  
  ## 任务
  后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
  全栈开发
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/demo-fieldio-particles.html
  src/frontend/demo-lupi-data-humanism.html
  src/frontend/demo-takram-biosynthetic.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/monitoring.html
  src/frontend/plaza-dark.html
  src/frontend/plaza-old.html
  src/frontend/plaza-wabisabi-v2.html
  src/frontend/plaza-wabisabi.html
  src/frontend/plaza.html
  src/frontend/skill-extract.html
  src/frontend/system-evolution.html
  src/frontend/tasks.html
  src/frontend/css/agent-team-config.css
  src/frontend/css/openbridge-theme.css
  src/frontend/css/ws-theme-bridge.css
  src/frontend/js/agent-team-config.js
  src/frontend/js/i18n.js
  src/frontend/js/nav-sidebar.js
  src/backend/__init__.py
  src/backend/agent_team_api.py
  src/backend/main.py
  src/backend/main.py.bak
  src/backend/startup_check.py
  src/backend/startup_validator.py
  src/backend/tests/__init__.py
  src/backend/tests/conftest.py
  src/backend/tests/conftest.py.bak
  src/backend/tests/test_ab_testing.py
  src/backend/tests/test_agent_toolbox.py
  src/backend/tests/test_evolution_race.py
  src/backend/tests/test_evolution_race.py.bak
  src/backend/tests/test_fingerprint.py
  src/backend/tests/test_fingerprint.py.bak
  src/backend/tests/test_gate_evaluator.py
  src/backend/tests/test_gate_evaluator.py.bak
  src/backend/tests/test_merge_plugin.py
  src/backend/tests/test_merge_plugin.py.bak
  src/backend/tests/test_models.py
  src/backend/tests/test_models.py.bak
  src/backend/tests/test_qa_gate_pipeline.py
  src/backend/tests/test_qa_gate_pipeline.py.bak
  src/backend/tests/test_task_engine.py
  src/backend/tests/test_task_engine.py.bak
  src/backend/tests/test_team_manager.py
  src/backend/tests/test_team_manager.py.bak
  src/backend/tests/test_template_variants.py
  src/backend/tests/test_template_variants.py.bak
  src/backend/agents/__init__.py
  src/backend/agents/ab_testing.py
  src/backend/agents/agent_loop.py
  src/backend/agents/agent_toolbox.py
  src/backend/agents/api.py
  src/backend/agents/api.py.bak
  src/backend/agents/audit_store.py
  src/backend/agents/chat_harness.py
  src/backend/agents/domain_events.py
  src/backend/agents/domain_events.py.bak
  src/backend/agents/event_bus.py
  src/backend/agents/execution_registry.py
  src/backend/agents/fingerprint.py
  src/backend/agents/fingerprint.py.bak
  src/backend/agents/gate_evaluator.py
  src/backend/agents/hermes_research.py
  src/backend/agents/knowledge_base.py
  src/backend/agents/merge_engine.py
  src/backend/agents/merge_models.py
  src/backend/agents/models.py
  src/backend/agents/models.py.bak
  src/backend/agents/plaza.py
  src/backend/agents/plaza_engine.py
  src/backend/agents/plaza_routes.py
  src/backend/agents/plaza_routes.py.bak
  src/backend/agents/plaza_store.py
  src/backend/agents/review_models.py
  src/backend/agents/review_routes.py
  src/backend/agents/review_service.py
  src/backend/agents/session_store.py
  src/backend/agents/similarity_engine.py
  src/backend/agents/skill_evolver.py
  src/backend/agents/skill_extractor.py
  src/backend/agents/skill_indexer.py
  src/backend/agents/skill_library.py
  src/backend/agents/skill_querier.py
  src/backend/agents/skill_registry.py
  src/backend/agents/skill_store.py
  src/backend/agents/skill_tracker.py
  src/backend/agents/skill_verifier.py
  src/backend/agents/task_engine.py
  src/backend/agents/task_engine.py.bak
  src/backend/agents/task_store.py
  src/backend/agents/team_manager.py
  src/backend/agents/team_manager.py.bak
  src/backend/agents/team_store.py
  src/backend/agents/tool_executor.py
  src/backend/agents/tool_registry.py
  src/backend/agents/trajectory_analyzer.py
  src/backend/agents/tts_routes.py
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/greeting.py
  src/backend/agents/skills/hello.py
  src/backend/scripts/__init__.py
  src/backend/scripts/migrate.py
  src/backend/scripts/validate_startup.py
  src/backend/scripts/validate_telemetry.py
  src/backend/monitoring/__init__.py
  src/backend/monitoring/__init__.py.bak
  src/backend/monitoring/aggregation_window.py
  src/backend/monitoring/aggregation_window.py.bak
  src/backend/monitoring/collector.py
  src/backend/monitoring/collector.py.bak
  src/backend/monitoring/fingerprint_bypass.py
  src/backend/monitoring/models.py
  src/backend/monitoring/models.py.bak
  src/backend/monitoring/monitoring_routes.py
  src/backend/monitoring/plaza_monitor.py
  src/backend/monitoring/plaza_monitor.py.bak
  src/backend/monitoring/sampler.py
  src/backend/monitoring/trace_bridge.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/evolution_executor.py
  src/backend/channels/marine_base.py
  src/backend/channels/merge_channel.py
  src/backend/channels/openclaw_sync.py
  src/backend/channels/openclaw_sync.py.bak
  src/backend/channels/system_evolution.py
  src/docs/agent_handoffs/01d37305-090_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0261754d-288_executor_started_20260509T073231.md
  src/docs/agent_handoffs/05014547-ce8_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0597d622-ad4_executor_started_20260509T073232.md
  src/docs/agent_handoffs/06d3f2a5-82c_executor_started_20260509T073231.md
  src/docs/agent_handoffs/073864e5-58b_executor_started_20260509T073231.md
  src/docs/agent_handoffs/073a3fe7-4d5_executor_started_20260509T073232.md
  src/docs/agent_handoffs/09ff3a16-710_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0a242acf-f52_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0af6e1cb-61c_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0c263083-1c8_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0f6d4e48-ea3_executor_started_20260509T073232.md
  src/docs/agent_handoffs/10857dbb-a51_executor_started_20260509T073231.md
  src/docs/agent_handoffs/11e9b4b9-283_architecture_20260509T075556.md
  src/docs/agent_handoffs/11e9b4b9-283_deploy_20260509T081242.md
  src/docs/agent_handoffs/11e9b4b9-283_develop_20260509T080722.md
  src/docs/agent_handoffs/11e9b4b9-283_document_20260509T081332.md
  ... (共 725 个 src/ 文件)
  
  ```
  
  ### 文件: `src/frontend/monitoring.html`
  ```html
  <!DOCTYPE html>
  <html lang="zh-CN">
  <head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgentsGroup2026 — 可观测性监控面板</title>
  <style>
    :root {
      --bg: #0a0e14;
      --panel-bg: #131820;
      --border: #1e2a3a;
      --text: #c9d1d9;
      --text-dim: #8b949e;
      --accent: #58a6ff;
      --accent2: #3fb950;
      --warn: #d29922;
      --error: #f85149;
      --p0: #f85149;
      --p1: #d29922;
      --p2: #58a6ff;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: "SF Mono","Menlo","Consolas",monospace;
      background: var(--bg);
      color: var(--text);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    /* Header */
    .header {
      background: var(--panel-bg);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      flex-shrink: 0;
    }
    .header h1 {
      font-size: 16px;
      font-weight: 600;
      color: var(--accent);
      margin-right: auto;
    }
    .header .status-dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: var(--accent2);
      display: inline-block;
    }
    .header .status-dot.warn { background: var(--warn); }
    .header .status-dot.error { background: var(--error); }
    .header .stat {
      font-size: 12px;
      color: var(--text-dim);
    }
    .header .stat span {
      color: var(--text);
      font-weight: 600;
    }
  
    /* Main Grid */
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 1fr 1fr;
      gap: 8px;
      padding: 8px;
      flex: 1;
      overflow: hidden;
    }
    .panel {
      background: var(--panel-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .panel-header {
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    .panel-header .badge {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 3px;
      background: var(--border);
    }
    .panel-body {
      flex: 1;
      overflow-y: auto;
      padding: 12px 14px;
      font-size: 12px;
      line-height: 1.5;
    }
  
    /* Fingerprint Panel */
    .fp-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .fp-card {
      background: rgba(255,255,255,0.03);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 10px;
    }
    .fp-card .label {
      font-size: 10px;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .fp-card .value {
      font-size: 20px;
      font-weight: 700;
      margin: 4px 0;
    }
    .fp-card .value.p0 { color: var(--p0); }
    .fp-card .value.p1 { color: var(--p1); }
    .fp-card .value.p2 { color: var(--p2); }
    .fp-card .value.ok { color: var(--accent2); }
    .fp-card .trend {
      font-size: 10px;
      color: var(--text-dim);
    }
    .fp-card .trend.up { color: var(--error); }
    .fp-card .trend.down { color: var(--accent2); }
  
    /* Trace Panel */
    .trace-list-item {
      padding: 6px 8px;
      border-left: 3px solid var(--border);
      margin-bottom: 6px;
      font-size: 11px;
      transition: border-color 0.2s;
    }
    .trace-list-item:hover { border-left-color: var(--accent); }
    .trace-list-item .tid {
      color: var(--accent);
      font-family: monospace;
    }
    .trace-list-item .meta {
      color: var(--text-dim);
      font-size: 10px;
    }
    .trace-list-item .type-badge {
      font-size: 9px;
      padding: 1px 4px;
      border-radius: 2px;
      background: var(--border);
      margin-left: 6px;
    }
    .trace-list-item .type-badge.plaza { background: #1a3a5c; color: #58a6ff; }
    .trace-list-item .type-badge.handoff { background: #3a2a1a; color: #d29922; }
    .trace-list-item .type-badge.task { background: #1a3a2a; color: #3fb950; }
    .trace-list-item .type-badge.tool { background: #2a1a3a; color: #a371f7; }
  
    /* Topology Panel */
    .topo-canvas {
      width: 100%;
      height: 100%;
      min-height: 200px;
    }
  
    /* Alerts Panel */
    .alert-item {
      padding: 6px 8px;
      border-radius: 4px;
      margin-bottom: 4px;
      font-size: 11px;
      border-left: 3px solid transparent;
    }
    .alert-item.p0 { border-left-color: var(--p0); background: rgba(248,81,73,0.08); }
    .alert-item.p1 { border-left-color: var(--p1); background: rgba(210,153,34,0.08); }
    .alert-item .time {
      font-size: 9px;
      color: var(--text-dim);
    }
  
    /* Bottom bar */
    .bottom-bar {
      background: var(--panel-bg);
      border-top: 1px solid var(--border);
      padding: 8px 16px;
      display: flex;
      gap: 16px;
      align-items: center;
      font-size: 11px;
      color: var(--text-dim);
      flex-shrink: 0;
    }
    .bottom-bar .refresh {
      color: var(--accent);
      cursor: pointer;
    }
    .bottom-bar .refresh:hover { text-decoration: underline; }
  
    /* Tab buttons */
    .tab-row {
      display: flex;
      gap: 4px;
      margin-bottom: 8px;
    }
    .tab-btn {
      font-size: 11px;
      padding: 4px 10px;
      border: 1px solid var(--border);
      border-radius: 3px;
      background: transparent;
      color: var(--text-dim);
      cursor: pointer;
      transition: all 0.2s;
    }
    .tab-btn:hover { border-color: var(--accent); color: var(--text); }
    .tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  
    /* SVG topology */
    .topo-node { fill: var(--accent); }
    .topo-node.agent { fill: #3fb950; }
    .topo-node.discussion { fill: #58a6ff; }
    .topo-node.task { fill: #d29922; }
    .topo-node.tool { fill: #a371f7; }
    .topo-link { stroke: var(--border); stroke-width: 1; }
    .topo-label { fill: var(--text-dim); font-size: 9px; }
  
    /* Responsive */
    @media (max-width: 900px) {
      .main-grid {
        grid-template-columns: 1fr;
        grid-template-rows: auto;
      }
    }
  </style>
  </head>
  <body>
  
  <div class="header">
    <span class="status-dot" id="statusDot"></span>
    <h1>🔍 可观测性监控面板 · AgentsGroup2026</h1>
    <div class="stat">Trace 数: <span id="statTraces">0</span></div>
    <div class="stat">链路节点: <span id="statNodes">0</span></div>
    <div class="stat">指纹采集: <span id="statFingerprints">0</span></div>
    <div class="stat">异常: <span id="statAnomaly">否</span></div>
  </div>
  
  <div class="main-grid">
    <!-- Panel 1: 行为指纹遥测 -->
    <div class="panel">
      <div class="panel-header">
        🧬 行为指纹遥测旁路
        <span class="badge" style="background:var(--p1);color:#fff">P0/P1</span>
        <span style="font-size:10px;color:var(--text-dim);margin-left:auto" id="fpUpdated">—</span>
      </div>
      <div class="panel-body" id="fingerprintPanel">
        <div class="fp-grid">
          <div class="fp-card">
            <div class="label">假升级率 (false_upgrade)</div>
            <div class="value p0" id="fpFalseUpgrade">—</div>
            <div class="trend" id="fpFalseUpgradeTrend">—</div>
          </div>
          <div class="fp-card">
            <div class="label">行为指纹突变率</div>
            <div class="value p0" id="fpMutationRate">—</div>
            <div class="trend" id="fpMutationTrend">—</div>
          </div>
          <div class="fp-card">
            <div class="label">异常传播深度</div>
            <div class="value p1" id="fpAnomalyDepth">—</div>
            <div class="trend" id="fpAnomalyDepthTrend">—</div>
          </div>
          <div class="fp-card">
            <div class="label">预测错误率</div>
            <div class="value p1" id="fpPredError">—</div>
            <div class="trend" id="fpPredErrorTrend">—</div>
          </div>
          <div class="fp-card">
            <div class="label">资源增量 %</div>
            <div class="value p2" id="fpResourcePct">—</div>
            <div class="trend" id="fpResourceTrend">—</div>
          </div>
          <div class="fp-card">
            <div class="label">能耗增量 %</div>
            <div class="value p2" id="fpEnergyPct">—</div>
            <div class="trend" id="fpEnergyTrend">—</div>
          </div>
          <div class="fp-card">
            <div class="label">策略评估延迟 (ms)</div>
            <div class="value p2" id="fpPolicyLatency">—</div>
            <div class="trend" id="fpPolicyLatencyTrend">—</div>
          </div>
          <div class="fp-card">
            <div class="label">进化停滞率</div>
            <div class="value p2" id="fpStagnation">—</div>
            <div class="trend" id="fpStagnationTrend">—</div>
          </div>
        </div>
      </div>
    </div>
  
    <!-- Panel 2: 聚合链路 Trace ID 关联 -->
    <div class="panel">
      <div class="panel-header">
        🔗 聚合链路 Trace 关联
        <span class="badge" style="background:var(--p0);color:#fff">P0</span>
        <div class="tab-row" style="margin:0 0 0 auto;">
          <button class="tab-btn active" onclick="switchTraceTab('list')">链路列表</button>
          <button class="tab-btn" onclick="switchTraceTab('topo')">拓扑图</button>
        </div>
      </div>
      <div class="panel-body" id="tracePanel">
        <div id="traceListView"></div>
        <div id="traceTopoView" style="display:none;">
          <svg class="topo-canvas" id="topoSvg"></svg>
        </div>
      </div>
    </div>
  
    <!-- Panel 3: 讨论监控 (Plaza Monitor) -->
    <div class="panel">
      <div class="panel-header">
        🏛️ Plaza 讨论监控
        <span class="badge" style="background:var(--p0);color:#fff">P0</span>
      </div>
      <div class="panel-body" id="plazaPanel">
        <div style="color:var(--text-dim);text-align:center;padding:20px;">等待数据...</div>
      </div>
    </div>
  
    <!-- Panel 4: 告警与事件 -->
    <div class="panel">
      <div class="panel-header">
        ⚠️ 实时告警
        <span class="badge" style="background:var(--error);color:#fff" id="alertCount">0</span>
      </div>
      <div class="panel-body" id="alertsPanel">
        <div style="color:var(--text-dim);text-align:center;padding:20px;">无告警</div>
      </div>
    </div>
  </div>
  
  <div class="bottom-bar">
    <span>⏱ 自动刷新: <span id="refreshCountdown">5</span>s</span>
    <span class="refresh" onclick="forceRefresh()">🔄 立即刷新</span>
    <span style="margin-left:auto;">API: <span id="apiStatus">连接中...</span></span>
  </div>
  
  <script>
  // ═══════════════════════════════════════════════
  // 监控面板 JavaScript
  // ═══════════════════════════════════════════════
  
  const API_BASE = '/api/v1/agent-config';
  let traceTab = 'list';
  let refreshTimer = null;
  let countdownTimer = null;
  let countdown = 5;
  let prevFingerprints = {};
  
  // ── 初始化 ────────────────────────────────────
  
  document.addEventListener('DOMContentLoaded', () => {
    fetchAll();
    startRefresh();
  });
  
  function startRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    if (countdownTimer) clearInterval(countdownTimer);
  
    refreshTimer = setInterval(() => {
      fetchAll();
      countdown = 5;
      updateCountdown();
    }, 5000);
  
    countdownTimer = setInterval(() => {
      countdown--;
      updateCountdown();
      if (countdown <= 0) countdown = 5;
    }, 1000);
  }
  
  function updateCountdown() {
    document.getElementById('refreshCountdown').textContent = countdown;
  }
  
  function forceRefresh() {
    countdown = 5;
    updateCountdown();
    fetchAll();
  }
  
  // ── 数据获取 ──────────────────────────────────
  
  async function fetchAll() {
    try {
      await Promise.all([
        fetchFingerprints(),
        fetchTraceLinks(),
        fetchPlazaStatus(),
        fetchDashboard(),
      ]);
      document.getElementById('apiStatus').textContent = '✅ 已连接';
      document.getElementById('apiStatus').style.color = 'var(--accent2)';
      document.getElementById('statusDot').className = 'status-dot';
    } catch (e) {
      console.error('Fetch error:', e);
      document.getElementById('apiStatus').textContent = '❌ 连接失败';
      document.getElementById('apiStatus').style.color = 'var(--error)';
      document.getElementById('statusDot').className = 'status-dot error';
    }
  }
  
  async function fetchFingerprints() {
    try {
      const resp = await fetch(`${API_BASE}/monitoring/fingerprints?limit=10`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      renderFingerprints(data);
    } catch (e) {
      console.warn('Fingerprints fetch:', e.message);
    }
  }
  
  async function fetchTraceLinks() {
    try {
      const resp = await fetch(`${API_BASE}/monitoring/traces?limit=30`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      renderTraceLinks(data);
  
      // fetch topology separately
      const topoResp = await fetch(`${API_BASE}/monitoring/topology`);
      if (topoResp.ok) {
        const topoData = await topoResp.json();
        renderTopology(topoData);
      }
    } catch (e) {
      console.warn('Trace links fetch:', e.message);
    }
  }
  
  async function fetchPlazaStatus() {
    try {
      const resp = await fetch(`${API_BASE}/plaza/plazas`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      renderPlazaStatus(data);
    } catch (e) {
      console.warn('Plaza status fetch:', e.message);
    }
  }
  
  async function fetchDashboard() {
    try {
      const resp = await fetch(`${API_BASE}/monitoring/dashboard`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      renderDashboard(data);
    } catch (e) {
      console.warn('Dashboard fetch:', e.message);
    }
  }
  
  // ── 指纹渲染 ──────────────────────────────────
  
  function renderFingerprints(data) {
    const fps = data.fingerprints || [];
    const stats = data.stats || {};
    const latest = fps.length > 0 ? fps[fps.length - 1] : null;
  
    if (latest) {
      updateFpValue('fpFalseUpgrade', latest.false_upgrade_rate, '%', 'p0', 'fpFalseUpgradeTrend');
      updateFpValue('fpMutationRate', latest.behavior_fingerprint_mutation_rate, '%', 'p0', 'fpMutationTrend');
      updateFpValue('fpAnomalyDepth', latest.anomaly_propagation_depth, '', 'p1', 'fpAnomalyDepthTrend');
      updateFpValue('fpPredError', latest.prediction_error_rate, '%', 'p1', 'fpPredErrorTrend');
      updateFpValue('fpResourcePct', latest.resource_increase_pct, '%', 'p2', 'fpResourceTrend');
      updateFpValue('fpEnergyPct', latest.energy_increase_pct, '%', 'p2', 'fpEnergyTrend');
      updateFpValue('fpPolicyLatency', latest.policy_evaluation_latency_ms, 'ms', 'p2', 'fpPolicyLatencyTrend');
      updateFpValue('fpStagnation', latest.evolution_stagnation_rate, '%', 'p2', 'fpStagnationTrend');
  
      document.getElementById('fpUpdated').textContent =
        '更新于 ' + new Date(latest.collected_at).toLocaleTimeString();
    }
  
    document.getElementById('statFingerprints').textContent = stats.total_collected || fps.length;
    document.getElementById('statAnomaly').textContent = stats.anomaly_detected ? '⚠️ 是' : '否';
    if (stats.anomaly_detected) {
      document.getElementById('statAnomaly').style.color = 'var(--error)';
    } else {
      document.getElementById('statAnomaly').style.color = 'var(--text)';
    }
  }
  
  function updateFpValue(id, value, suffix, cssClass, trendId) {
    const el = document.getElementById(id);
    if (value === undefined || value === null) { el.textContent = '—'; return; }
    const displayVal = typeof value === 'number' ? value.toFixed(3) : value;
    el.textContent = displayVal + suffix;
    el.className = 'value ' + cssClass;
  
    // Trend
    const trendEl = document.getElement
  ```
  
  ### 文件: `src/backend/agent_team_api.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  Agent Team API Routes - 双团队管理 REST API
  
  提供构建团队 & 执行团队的状态查询、KPI 考核、
  任务分配、报告查询等端点。挂载至 FastAPI 的 router。
  """
  
  from __future__ import annotations
  
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel
  from typing import Any, Dict, List, Optional
  
  router = APIRouter(prefix="/api/v1/agent-teams", tags=["Agent Teams"])
  
  
  # ---------------------------------------------------------------------------
  # 全局引用（在 main.py startup 时注入）
  # ---------------------------------------------------------------------------
  _build_team = None
  _execution_team = None
  _scheduler = None
  _evolution_engine = None
  
  
  def set_teams(build_team, execution_team, scheduler, evolution_engine=None):
      """在应用启动时由 main.py 调用，注入团队实例."""
      global _build_team, _execution_team, _scheduler, _evolution_engine
      _build_team = build_team
      _execution_team = execution_team
      _scheduler = scheduler
      _evolution_engine = evolution_engine
  
  
  # ---------------------------------------------------------------------------
  # Request / Response Models
  # ---------------------------------------------------------------------------
  
  class TaskAssignment(BaseModel):
      agent_id: str
      task: str
  
  class FeedbackSubmission(BaseModel):
      category: str = "optimization"
      severity: str = "medium"
      title: str
      detail: str
  
  
  # ---------------------------------------------------------------------------
  # Scheduler
  # ---------------------------------------------------------------------------
  
  @router.get("/scheduler/status")
  async def scheduler_status():
      if not _scheduler:
          raise HTTPException(503, "Scheduler not initialized")
      return _scheduler.get_status()
  
  
  @router.post("/scheduler/report")
  async def scheduler_generate_report():
      if not _scheduler:
          raise HTTPException(503, "Scheduler not initialized")
      return _scheduler.generate_report_now()
  
  
  @router.post("/scheduler/tick")
  async def scheduler_tick_once():
      """手动触发一次调度 tick (调试用)."""
      if not _scheduler:
          raise HTTPException(503, "Scheduler not initialized")
      return _scheduler.tick_once()
  
  
  # ---------------------------------------------------------------------------
  # Build Team
  # ---------------------------------------------------------------------------
  
  @router.get("/build/status")
  async def build_team_status():
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      return _build_team.get_status()
  
  
  @router.get("/build/kpis")
  async def build_team_kpis():
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      return _build_team.get_agent_kpis()
  
  
  @router.get("/build/agents/{agent_id}")
  async def build_agent_detail(agent_id: str):
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      agent = _build_team.agents.get(agent_id)
      if not agent:
          raise HTTPException(404, f"Agent '{agent_id}' not found")
      return agent.to_dict()
  
  
  @router.post("/build/assign")
  async def build_assign_task(body: TaskAssignment):
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      ok = _build_team.assign_task(body.agent_id, body.task)
      if not ok:
          raise HTTPException(404, f"Agent '{body.agent_id}' not found")
      return {"status": "assigned", "agent_id": body.agent_id, "task": body.task}
  
  
  @router.get("/build/reports")
  async def build_reports(limit: int = 10):
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      reports = _build_team.hourly_reports[-limit:]
      return [r.to_dict() for r in reports]
  
  
  @router.get("/build/issues")
  async def build_issues():
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      return _build_team.issue_backlog
  
  
  # ---------------------------------------------------------------------------
  # Execution Team
  # ---------------------------------------------------------------------------
  
  @router.get("/execution/status")
  async def execution_team_status():
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      return _execution_team.get_status()
  
  
  @router.get("/execution/agents/{agent_id}")
  async def execution_agent_detail(agent_id: str):
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      agent = _execution_team.agents.get(agent_id)
      if not agent:
          raise HTTPException(404, f"Agent '{agent_id}' not found")
      return agent.to_dict()
  
  
  @router.get("/execution/reports")
  async def execution_reports(limit: int = 10):
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      reports = _execution_team.execution_reports[-limit:]
      return [r.to_dict() for r in reports]
  
  
  @router.get("/execution/feedback")
  async def execution_feedback():
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      return [item.to_dict() for item in _execution_team.feedback_queue]
  
  
  @router.post("/execution/feedback")
  async def submit_feedback(body: FeedbackSubmission):
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      item = _execution_team.submit_feedback(
          category=body.category,
          severity=body.severity,
          title=body.title,
          detail=body.detail,
      )
      return item.to_dict()
  
  
  # ---------------------------------------------------------------------------
  # Combined
  # ---------------------------------------------------------------------------
  
  @router.get("/overview")
  async def teams_overview():
      """一站式获取双团队全局概览."""
      result: Dict[str, Any] = {}
      if _build_team:
          bs = _build_team.get_status()
          result["build_team"] = {
              "health": bs["health"],
              "agent_count": bs["agent_count"],
              "metrics": bs["metrics"],
          }
      if _execution_team:
          es = _execution_team.get_status()
          result["execution_team"] = {
              "health": es["health"],
              "agent_count": es["agent_count"],
              "metrics": es["metrics"],
          }
      if _scheduler:
          result["scheduler"] = _scheduler.get_status()
      if _evolution_engine:
          result["evolution"] = _evolution_engine.get_status()
      return result
  
  
  # ---------------------------------------------------------------------------
  # System Evolution (自我演进引擎)
  # ---------------------------------------------------------------------------
  
  @router.get("/evolution/status")
  async def evolution_status():
      """获取自我演进引擎状态。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_status()
  
  
  @router.get("/evolution/summary")
  async def evolution_summary():
      """获取演进项汇总。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_evolution_summary()
  
  
  @router.get("/evolution/items")
  async def evolution_items(status: Optional[str] = None):
      """获取演进项列表，可按状态过滤。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_evolution_items(status=status)
  
  
  @router.get("/evolution/rules")
  async def evolution_rules():
      """获取审查规则列表。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return [r.to_dict() for r in _evolution_engine.audit_rules]
  
  
  @router.post("/evolution/rules/from-task")
  async def evolution_add_rule_from_task(body: dict):
      """从议事厅任务导入为审查规则。body: {title, description, severity?, task_id?, team_id?}"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      if not body.get("title"):
          raise HTTPException(400, "title is required")
      return _evolution_engine.add_rule_from_task(body)
  
  
  @router.delete("/evolution/rules/{rule_id}")
  async def evolution_delete_rule(rule_id: str):
      """删除指定审查规则。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      result = _evolution_engine.delete_audit_rule(rule_id)
      if result.get("status") == "not_found":
          raise HTTPException(404, result.get("message", "规则不存在"))
      return result
  
  
  @router.put("/evolution/rules/{rule_id}")
  async def evolution_update_rule(rule_id: str, body: dict):
      """更新指定审查规则。body: {title?, description?, severity?, reference?, domain?, rating_weight?}"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      result = _evolution_engine.update_audit_rule(rule_id, body)
      if result.get("status") == "not_found":
          raise HTTPException(404, result.get("message", "规则不存在"))
      return result
  
  
  @router.post("/evolution/audit")
  async def evolution_run_audit():
      """手动触发一次审查。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.run_full_audit()
  
  
  @router.post("/evolution/cycle")
  async def evolution_run_cycle():
      """运行完整演进周期（审查→派发→验证→关闭）。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.run_evolution_cycle()
  
  
  @router.post("/evolution/dispatch")
  async def evolution_dispatch():
      """派发所有待处理演进项给 Build 团队。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.dispatch_all_pending()
  
  
  @router.post("/evolution/verify")
  async def evolution_verify():
      """验证所有待验证项。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.verify_all_pending()
  
  
  @router.get("/evolution/items/{item_id}")
  async def evolution_item_detail(item_id: str):
      """获取单个演进项详情。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      item = _evolution_engine.evolution_items.get(item_id)
      if not item:
          raise HTTPException(404, f"Item '{item_id}' not found")
      return item.to_dict()
  
  
  @router.post("/evolution/items/{item_id}/progress")
  async def evolution_mark_progress(item_id: str):
      """标记演进项为进行中。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      ok = _evolution_engine.mark_in_progress(item_id)
      if not ok:
          raise HTTPException(404, f"Item '{item_id}' not found")
      return {"status": "ok", "item_id": item_id, "new_status": "in_progress"}
  
  
  @router.post("/evolution/items/{item_id}/complete")
  async def evolution_mark_complete(item_id: str):
      """标记演进项构建完成，进入待验证。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      ok = _evolution_engine.mark_build_complete(item_id)
      if not ok:
          raise HTTPException(404, f"Item '{item_id}' not found")
      return {"status": "ok", "item_id": item_id, "new_status": "verify_pending"}
  
  
  @router.delete("/evolution/items/{item_id}")
  async def evolution_delete_item(item_id: str):
      """删除指定演进条目。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      result = _evolution_engine.delete_evolution_item(item_id)
      if result.get("status") == "not_found":
          raise HTTPException(404, result.get("message", "条目不存在"))
      return result
  
  
  @router.put("/evolution/items/{item_id}")
  async def evolution_update_item(item_id: str, body: dict):
      """更新指定演进条目。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      result = _evolution_engine.update_evolution_item(item_id, body)
      if result.get("status") == "not_found":
          raise HTTPException(404, result.get("message", "条目不存在"))
      return result
  
  
  @router.get("/evolution/executor/status")
  async def evolution_executor_status():
      """获取演进执行器状态 (正在执行的任务等)."""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      executor = _evolution_engine._get_executor()
      return executor.get_status()
  
  
  @router.get("/evolution/items/{item_id}/execution-log")
  async def evolution_item_execution_log(item_id: str):
      """获取演进项的 AgentLoop 执行事件日志."""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      executor = _evolution_engine._get_executor()
      log = executor.get_event_log(item_id)
      result = executor.get_result(item_id)
      return {
          "item_id": item_id,
          "is_running": executor.is_running(item_id),
          "events": log,
          "result": result,
      }
  
  
  @router.delete("/evolution/zones/{zone_id}")
  async def evolution_delete_zone(zone_id: str):
      """删除指定合规区域。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      result = _evolution_engine.delete_compliance_zone(zone_id)
      if result.get("status") == "not_found":
          raise HTTPException(404, result.get("message", "区域不存在"))
      return result
  
  
  @router.put("/evolution/zones/{zone_id}")
  async def evolution_update_zone(zone_id: str, body: dict):
      """更新指定合规区域。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      result = _evolution_engine.update_compliance_zone(zone_id, body)
      if result.get("status") == "not_found":
          raise HTTPException(404, result.get("message", "区域不存在"))
      return result
  
  
  @router.post("/evolution/close-verified")
  async def evolution_close_verified():
      """关闭所有已验证通过的演进项。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      closed = _evolution_engine.close_verified()
      return {"closed": closed, "count": len(closed)}
  
  
  @router.post("/evolution/close")
  async def evolution_close():
      """关闭所有已验证通过的演进项 (close-verified 别名)。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      closed = _evolution_engine.close_verified()
      return {"closed": closed, "count": len(closed)}
  
  
  @router.get("/evolution/history")
  async def evolution_audit_history():
      """获取审查历史记录。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      raw = _evolution_engine.get_audit_history()
      # Normalize field names for frontend (expects timestamp, total)
      result = []
      for h in raw:
          entry = dict(h)
          entry.setdefault("timestamp", entry.pop("time", None))
          entry.setdefault("total", (entry.get("passed") or 0) + (entry.get("failed") or 0) + (entry.get("skipped") or 0))
          result.append(entry)
      return result
  
  
  @router.get("/evolution/analytics")
  async def evolution_analytics():
      """获取演进分析数据 (域覆盖、严重度分布、趋势)。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      summary = _evolution_engine.get_evolution_summary()
      history = _evolution_engine.get_a
  ```
  
  ### 文件: `src/backend/agents/api.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Agent Team Framework -- REST API Router.
  
  Clawith-style CRUD API for teams, agents, models, tools, skills.
  Tab-based organization:
    1. Team Info
    2. Model Pool
    3. Tools
    4. Skills
    5. Agents -- 5-step wizard
    6. Overview
  """
  
  from __future__ import annotations
  
  import asyncio
  import json
  from datetime import datetime, timezone
  
  from typing import Any, Dict, List, Optional
  
  from fastapi import APIRouter, HTTPException, status
  from pydantic import BaseModel, Field
  
  from .models import (
      AccessLevel,
      AgentState,
      AgentChannelConfig,
      AgentPermission,
      AgentPersonality,
      AgentProfile,
      AgentTemplateType,
      HermesAgentConfig,
      ModelConfig,
      ToolsetDistribution,
  )
  from .hermes_research import (
      RESEARCH_TOOLSET_DISTRIBUTIONS,
      HERMES_TOOLSETS,
      create_hermes_researcher,
      build_research_system_prompt,
      sample_toolsets,
      resolve_tools,
      get_research_distributions,
      get_hermes_toolsets,
  )
  from .chat_harness import (
      ChatHarness,
      LLMProvider,
      ProviderConfig,
      get_chat_harness,
  )
  from .execution_registry import (
      ToolPermissionContext,
      PortRuntime,
      assemble_tool_pool,
      build_execution_registry,
  )
  from .session_store import (
      list_sessions as list_stored_sessions,
      search_sessions,
  )
  from .skill_registry import SkillRegistry, get_default_skills
  from .team_manager import TeamManager
  from .tool_registry import ToolRegistry, get_default_tools
  
  
  router = APIRouter(prefix="/api/v1/agent-config", tags=["agent-config"])
  
  
  _team_manager: Optional[TeamManager] = None
  _tool_registry: Optional[ToolRegistry] = None
  _skill_registry: Optional[SkillRegistry] = None
  
  # ── Model Pool Persistence ──
  import os as _mp_os, json as _mp_json
  
  _MODEL_POOL_PATH = _mp_os.path.join(
      _mp_os.path.dirname(_mp_os.path.dirname(_mp_os.path.dirname(
          _mp_os.path.dirname(_mp_os.path.abspath(__file__))))),
      "config", "model_pool.json"
  )
  
  
  def _save_model_pool() -> None:
      """Persist all teams' model pool to config/model_pool.json."""
      if _team_manager is None:
          return
      data: Dict[str, Any] = {}
      for team in _team_manager.list_teams():
          team_models = {}
          for m in team.models.values():
              team_models[m.model_id] = {
                  "model_id": m.model_id,
                  "provider": m.provider,
                  "name": m.name,
                  "max_tokens": m.max_tokens,
                  "temperature": m.temperature,
                  "is_default": m.is_default,
                  "enabled": m.enabled,
                  "api_key": m.api_key,
                  "api_base_url": m.api_base_url,
              }
          data[team.team_id] = team_models
      try:
          _mp_os.makedirs(_mp_os.path.dirname(_MODEL_POOL_PATH), exist_ok=True)
          with open(_MODEL_POOL_PATH, "w", encoding="utf-8") as f:
              _mp_json.dump(data, f, ensure_ascii=False, indent=2)
      except Exception:
          pass
  
  
  def _load_model_pool(tm: TeamManager) -> None:
      """Load persisted model pool from config/model_pool.json, overriding defaults."""
      if not _mp_os.path.isfile(_MODEL_POOL_PATH):
          return
      try:
          with open(_MODEL_POOL_PATH, "r", encoding="utf-8") as f:
              data = _mp_json.load(f)
      except Exception:
          return
      for team in tm.list_teams():
          team_data = data.get(team.team_id)
          if not team_data:
              continue
          # Replace the entire model pool with persisted version
          team.models.clear()
          for mid, mdata in team_data.items():
              model = ModelConfig(
                  model_id=mdata.get("model_id", mid),
                  provider=mdata.get("provider", "deepseek"),
                  name=mdata.get("name", "deepseek-chat"),
                  max_tokens=mdata.get("max_tokens", 8192),
                  temperature=mdata.get("temperature", 0.7),
                  is_default=mdata.get("is_default", False),
                  enabled=mdata.get("enabled", True),
                  api_key=mdata.get("api_key", ""),
                  api_base_url=mdata.get("api_base_url", ""),
              )
              team.add_model(model)
  
  
  def init_agent_config(team_manager: TeamManager) -> None:
      """Inject the TeamManager instance at startup."""
      global _team_manager, _tool_registry, _skill_registry
      _team_manager = team_manager
      _tool_registry = ToolRegistry()
      _tool_registry.load_defaults()
      _skill_registry = SkillRegistry()
      _skill_registry.load_defaults()
      # Load persisted model pool (overrides hardcoded defaults)
      _load_model_pool(team_manager)
      # Sync any existing default model to the chat harness
      _init_harness_from_teams(team_manager)
      # Initialize skill extractor engine
      init_skill_extractor()
      # Initialize skill library
      from .skill_library import init_skill_library, get_skill_library
      from .skill_store import SkillStore
      _skill_store = SkillStore()
      init_skill_library(
          team_manager=team_manager,
          skill_registry=_skill_registry,
          skill_store=_skill_store,
      )
      # Initialize skill tracker, evolver, verifier
      from .skill_tracker import init_skill_tracker
      from .skill_evolver import init_skill_evolver
      from .skill_verifier import init_skill_verifier
      _lib = get_skill_library()
      init_skill_tracker(skill_library=_lib)
      init_skill_evolver(skill_library=_lib, chat_harness=None)
      init_skill_verifier(skill_library=_lib, chat_harness=None)
  
  
  def _get_tool_registry() -> ToolRegistry:
      """Get or create the global ToolRegistry."""
      global _tool_registry
      if _tool_registry is None:
          _tool_registry = ToolRegistry()
          _tool_registry.load_defaults()
      return _tool_registry
  
  
  def _get_skill_registry() -> SkillRegistry:
      """Get or create the global SkillRegistry."""
      global _skill_registry
      if _skill_registry is None:
          _skill_registry = SkillRegistry()
          _skill_registry.load_defaults()
      return _skill_registry
  
  
  def _init_harness_from_teams(tm: TeamManager) -> None:
      """On startup, push the first team's default model into the chat harness."""
      try:
          harness = get_chat_harness()
          for team in tm.list_teams():
              for m in team.models.values():
                  if m.is_default and m.api_key:
                      harness.update_default_provider(
                          provider=m.provider,
                          api_key=m.api_key,
                          api_base_url=m.api_base_url,
                          model=m.name,
                      )
                      cfg = harness.get_provider_config()
                      cfg.max_tokens = m.max_tokens
                      cfg.temperature = m.temperature
                      return
      except Exception:
          pass  # Non-critical, harness will use env/settings fallback
  
  
  def _tm() -> TeamManager:
      if _team_manager is None:
          raise HTTPException(
              status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
              detail="Agent config service not initialized",
          )
      return _team_manager
  
  
  def _tr() -> ToolRegistry:
      if _tool_registry is None:
          raise HTTPException(
              status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
              detail="Tool registry not initialized",
          )
      return _tool_registry
  
  
  def _sr() -> SkillRegistry:
      if _skill_registry is None:
          raise HTTPException(
              status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
              detail="Skill registry not initialized",
          )
      return _skill_registry
  
  
  # Request / Response Models
  
  
  class CreateTeamRequest(BaseModel):
      name: str = Field(..., min_length=1, max_length=128)
      description: str = ""
  
  
  class CreateModelRequest(BaseModel):
      provider: str = "anthropic"
      name: str = "claude-sonnet-4-20250514"
      max_tokens: int = Field(default=8192, ge=1, le=200000)
      temperature: float = Field(default=0.7, ge=0.0, le=2.0)
      is_default: bool = False
      api_key: str = ""
      api_base_url: str = ""
  
  
  class CreateAgentRequest(BaseModel):
      """Step 1 of agent wizard -- basic info."""
      name: str = Field(..., min_length=1, max_length=128)
      role: str = ""
      description: str = ""
      template_type: str = "custom"
      model_id: str = ""
      system_prompt: str = ""
  
  
  class UpdatePersonalityRequest(BaseModel):
      """Step 2 -- personality config."""
      tone: str = "professional"
      language: str = "zh-CN"
      expertise_areas: List[str] = Field(default_factory=list)
      response_style: str = "concise"
      creativity: float = Field(default=0.5, ge=0.0, le=1.0)
  
  
  class UpdateToolsRequest(BaseModel):
      """Assign tools to an agent."""
      tool_ids: List[str] = Field(default_factory=list)
  
  
  class UpdateSkillsRequest(BaseModel):
      """Step 3 -- assign skills."""
      skill_ids: List[str] = Field(default_factory=list)
  
  
  class PermissionItem(BaseModel):
      resource: str = ""
      access_level: str = "read"
      channels: List[str] = Field(default_factory=list)
  
  
  class UpdatePermissionsRequest(BaseModel):
      """Step 4 -- permissions."""
      permissions: List[PermissionItem] = Field(default_factory=list)
  
  
  class ChannelItem(BaseModel):
      channel_name: str = ""
      subscribe: bool = True
      publish: bool = False
      priority: int = 0
  
  
  class UpdateChannelsRequest(BaseModel):
      """Step 5 -- channel subscriptions."""
      channels: List[ChannelItem] = Field(default_factory=list)
  
  
  # TAB 1 -- TEAM INFO
  
  
  @router.get("/teams", summary="List all teams")
  def list_teams() -> List[Dict[str, Any]]:
      return [
          {
              "team_id": t.team_id,
              "name": t.name,
              "description": t.description,
              "agent_count": len(t.agents),
              "model_count": len(t.models),
          }
          for t in _tm().list_teams()
      ]
  
  
  @router.get("/teams-tree", summary="All teams with agents tree")
  def teams_tree() -> List[Dict[str, Any]]:
      """返回团队→智能体树状结构，供广场选人使用."""
      result = []
      for t in _tm().list_teams():
          agents_list = t.agents
          if isinstance(agents_list, dict):
              agents_list = list(agents_list.values())
          result.append({
              "team_id": t.team_id,
              "name": t.name,
              "agents": [
                  {
                      "agent_id": a.agent_id,
                      "name": a.name or a.agent_id,
                      "role": a.role or "",
                  }
                  for a in agents_list
              ],
          })
      return result
  
  
  @router.get("/teams/{team_id}", summary="Get team detail")
  def get_team(team_id: str) -> Dict[str, Any]:
      team = _tm().get_team(team_id)
      if team is None:
          raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
      return team.to_dict()
  
  
  @router.post(
      "/teams",
      summary="Create team",
      status_code=status.HTTP_201_CREATED,
  )
  def create_team(req: CreateTeamRequest) -> Dict[str, Any]:
      team = _tm().create_team(name=req.name, description=req.description)
      return team.to_dict()
  
  
  @router.delete("/teams/{team_id}", summary="Delete team")
  def delete_team(team_id: str) -> Dict[str, str]:
      removed = _tm().delete_team(team_id)
      if removed is None:
          raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
      return {"deleted": team_id}
  
  
  # TAB 2 -- MODEL POOL
  
  
  def _get_team_or_404(team_id: str):
      team = _tm().get_team(team_id)
      if team is None:
          raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
      return team
  
  
  @router.get("/teams/{team_id}/models", summary="List team models")
  def list_models(team_id: str) -> List[Dict[str, Any]]:
      team = _get_team_or_404(team_id)
      return [m.to_dict() for m in team.models.values()]
  
  
  @router.post(
      "/teams/{team_id}/models",
      summary="Add model to team",
      status_code=status.HTTP_201_CREATED,
  )
  def add_model(team_id: str, req: CreateModelRequest) -> Dict[str, Any]:
      team = _get_team_or_404(team_id)
      model = ModelConfig(
          provider=req.provider,
          name=req.name,
          max_tokens=req.max_tokens,
          temperature=req.temperature,
          is_default=req.is_default,
          api_key=req.api_key,
          api_base_url=req.api_base_url,
      )
      team.add_model(model)
      if req.is_default:
          _set_team_default_model(team, model.model_id)
          _sync_default_model_to_harness(team)
      _save_model_pool()
      return model.to_dict()
  
  
  @router.put(
      "/teams/{team_id}/models/{model_id}",
      summary="Update a model in the team pool",
  )
  def update_model(team_id: str, model_id: str, req: CreateModelRequest) -> Dict[str, Any]:
      """Edit an existing model's configuration."""
      team = _get_team_or_404(team_id)
      model = team.get_model(model_id)
      if model is None:
          raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Model not found")
      model.provider = req.provider
      model.name = req.name
      model.max_tokens = req.max_tokens
      model.temperature = req.temperature
      if req.api_key:
          model.api_key = req.api_key
      if req.api_base_url:
          model.api_base_url = req.api_base_url
      if req.is_default:
          _set_team_default_model(team, model_id)
      else:
          model.is_default = False
      # Sync to chat harness
      _sync_default_model_to_harness(team)
      _save_model_pool()
      return model.to_dict()
  
  
  @router.put(
      "/teams/{team_id}/models/{model_id}/default",
      summary="Set a model as team default",
  )
  def set_default_model(team_id: str, model_id: str) -> Dict[str, Any]:
      """Set one model as the team default; clears default on all others."""
      team = _get_team_or_404(team_id)
      model = team.get_model(model_id)
      if model is None:
          raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Model not found")
      _set_team_default_model(team, model_id)
      # Sync to chat harness
      _sync_default_model_to_harness(team)
      _save_model_pool()
      return {"model_id": model_id, "is_default": True}
  
  
  def _set_team_default_model(team, model_id: str) -> None:
      """Clear is_default on all models, then set the specified one.
  
      Also migrates agents whose model_id was the old default to the new one,
      so that agent settings pages always reflect the current default model.
      """
      # Find old default model_id
      old_default_id: str | None = None
      for m in team.models.values():
          if m.is_default:
              old_default_id = m.model_id
              break
  
      # Toggle is_default flag
      for m in team.models.values():
          m.is_default = (m.model_id == model_id)
  
      # Propagate: agents using old default → new default
      if old_default_id and old_default_id != model_id:
          for agent in team.agents.values():
              if agent.model_id == old_default_id:
                  agent.model_id = model_id
  
  
  def _sync_default_model_to_harness(team) -> None:
      """Push the team's default model config into the ChatHarness."""
      harness = get_chat_harness()
      default_model = None
      for m
  ```
  
  ### 文件: `src/backend/monitoring/__init__.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  智能体广场实时监控与自动化质量保障系统 — 监控模块
  
  基于统一 traceId 的全链路可观测体系，支持：
  - W3C Trace Context 标准
  - P0/P1/P2 三级埋点字段分层采集
  - 自适应采样（基于 anomalyScore 动态调整）
  - 本地缓冲与异步上报
  - 降级场景全量采集
  - ConfigMap 热更新采样策略
  - 指纹遥测旁路 (非侵入式行为指纹异步采集)
  - 聚合链路 Trace ID 关联 (跨 Plaza/Handoff/Task 全链路追踪)
  - 面板监控 API (前端实时指标看板)
  """
  
  from __future__ import annotations
  
  from .models import (
      TraceSpan,
      TraceContext,
      SpanPriority,
      SamplingDecision,
      SamplingConfig,
      MonitoringMetrics,
      PlazaEventType,
      TelemetryRecord,
  )
  from .sampler import AdaptiveSampler
  from .collector import TraceCollector
  from .plaza_monitor import PlazaMonitorChannel
  from .fingerprint_bypass import (
      FingerprintTelemetryChannel,
      BehaviorFingerprint,
      FingerprintBuffer,
      get_fingerprint_channel,
  )
  from .trace_bridge import (
      TraceBridge,
      TraceBridgeChannel,
      TraceLink,
      TraceTopologyNode,
      get_trace_bridge,
      get_trace_bridge_channel,
      generate_trace_id,
      generate_span_id,
      make_trace_context,
  )
  from .monitoring_routes import router as monitoring_router
  
  __all__ = [
      "TraceSpan",
      "TraceContext",
      "SpanPriority",
      "SamplingDecision",
      "SamplingConfig",
      "MonitoringMetrics",
      "PlazaEventType",
      "TelemetryRecord",
      "AdaptiveSampler",
      "TraceCollector",
      "PlazaMonitorChannel",
      # Fingerprint Telemetry Bypass
      "FingerprintTelemetryChannel",
      "BehaviorFingerprint",
      "FingerprintBuffer",
      "get_fingerprint_channel",
      # Trace Bridge
      "TraceBridge",
      "TraceBridgeChannel",
      "TraceLink",
      "TraceTopologyNode",
      "get_trace_bridge",
      "get_trace_bridge_channel",
      "generate_trace_id",
      "generate_span_id",
      "make_trace_context",
      # Monitoring Routes
      "monitoring_router",
  ]
  
  ```
  
  ### 文件: `src/backend/monitoring/collector.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  Trace 采集器 — 本地缓冲 + 异步上报.
  
  负责:
  1. 接收 TraceSpan 并做采样决策
  2. 本地缓冲已采样数据
  3. 异步批量上报
  4. 降级场景强制全量采集
  """
  
  from __future__ import annotations
  
  import asyncio
  import json
  import logging
  import os
  from datetime import datetime, timezone
  from typing import Any, Callable, Dict, List, Optional
  
  from .models import (
      MonitoringMetrics,
      SamplingConfig,
      SpanPriority,
      TelemetryRecord,
      TraceSpan,
  )
  from .sampler import AdaptiveSampler
  
  logger = logging.getLogger(__name__)
  
  
  class TraceCollector:
      """Trace 采集器 — 本地缓冲 + 异步上报.
  
      使用 asyncio 实现非阻塞采集，支持自定义上报回调函数。
      """
  
      def __init__(
          self,
          sampler: Optional[AdaptiveSampler] = None,
          config: Optional[SamplingConfig] = None,
          upload_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
      ):
          self._sampler = sampler or AdaptiveSampler(config or SamplingConfig())
          self._upload_callback = upload_callback
          self._buffer: List[Dict[str, Any]] = []
          self._p2_buffer: List[Dict[str, Any]] = []
          self._metrics = MonitoringMetrics()
          self._running = False
          self._flush_task: Optional[asyncio.Task] = None
          self._lock = asyncio.Lock()
  
          # 用于 CI/CD 校验的遥测记录
          self._telemetry_records: List[TelemetryRecord] = []
  
      @property
      def sampler(self) -> AdaptiveSampler:
          return self._sampler
  
      @property
      def metrics(self) -> MonitoringMetrics:
          return self._metrics
  
      @property
      def config(self) -> SamplingConfig:
          return self._sampler.config
  
      def update_config(self, config_dict: dict):
          """热更新采样策略."""
          self._sampler.update_from_dict(config_dict)
          logger.info(f"📋 采集器配置已更新: {config_dict}")
  
      async def start(self):
          """启动异步刷新任务."""
          if self._running:
              return
          self._running = True
          self._flush_task = asyncio.create_task(self._flush_loop())
          logger.info("📡 TraceCollector 已启动")
  
      async def stop(self):
          """停止采集器并刷新剩余数据."""
          self._running = False
          if self._flush_task:
              self._flush_task.cancel()
              try:
                  await self._flush_task
              except asyncio.CancelledError:
                  pass
          await self._flush_now()
          logger.info("📡 TraceCollector 已停止")
  
      async def record(self, span: TraceSpan) -> bool:
          """记录一个 TraceSpan.
  
          流程:
          1. 采样决策
          2. 如果采样 → 加入缓冲
          3. 更新指标
  
          Returns:
              True 如果被采样并加入缓冲
          """
          decision = self._sampler.decide(span)
          self._metrics.total_spans += 1
  
          if not decision.should_sample:
              return False
  
          # 更新指标
          self._metrics.sampled_spans += 1
          if decision.priority == SpanPriority.P0:
              self._metrics.p0_spans += 1
          elif decision.priority == SpanPriority.P1:
              self._metrics.p1_spans += 1
          else:
              self._metrics.p2_spans += 1
  
          if span.status in ("error", "critical"):
              self._metrics.error_spans += 1
  
          if span.event_type == "fallback_triggered":
              self._metrics.fallback_count += 1
  
          # 更新平均异常评分和耗时
          n = self._metrics.total_spans
          self._metrics.avg_anomaly_score += (
              span.anomaly_score - self._metrics.avg_anomaly_score
          ) / n
          self._metrics.avg_duration_ms += (
              span.duration_ms - self._metrics.avg_duration_ms
          ) / n
  
          # 降级场景或高异常 → 全量采集
          include_all = (
              self._sampler.config.degradation_mode
              or span.anomaly_score >= self._sampler.config.anomaly_threshold_high
              or span.event_type == "fallback_triggered"
          )
  
          span_dict = span.to_dict(include_all=include_all)
  
          # 记录遥测记录（用于 CI/CD 校验）
          p0_fields = list(span.get_p0_fields().keys())
          p1_fields = list(span.get_p1_fields().keys())
          p2_fields = list(span.get_p2_fields().keys())
          all_expected = p0_fields + (p1_fields if include_all else []) + (p2_fields if include_all else [])
          fields_present = [k for k in all_expected if k in span_dict]
          fields_missing = [k for k in all_expected if k not in span_dict]
  
          record = TelemetryRecord(
              trace_id=span.trace_id,
              span_id=span.span_id,
              event_type=span.event_type,
              timestamp=span.timestamp,
              sampled=True,
              priority=decision.priority.value,
              fields_present=fields_present,
              fields_missing=fields_missing,
              anomaly_score=span.anomaly_score,
              status=span.status,
              duration_ms=span.duration_ms,
          )
          self._telemetry_records.append(record)
  
          # 加入缓冲
          async with self._lock:
              if decision.priority == SpanPriority.P2:
                  self._p2_buffer.append(span_dict)
              else:
                  self._buffer.append(span_dict)
  
              # 缓冲上限保护
              max_size = self._sampler.config.max_buffer_size
              if len(self._buffer) > max_size:
                  overflow = self._buffer[:-max_size]
                  self._buffer = self._buffer[-max_size:]
                  logger.warning(f"⚠️ 缓冲溢出，丢弃 {len(overflow)} 条记录")
  
          return True
  
      async def _flush_loop(self):
          """定时刷新循环."""
          interval = self._sampler.config.flush_interval_s
          while self._running:
              try:
                  await asyncio.sleep(interval)
                  await self._flush_now()
              except asyncio.CancelledError:
                  break
              except Exception as e:
                  logger.error(f"❌ 刷新循环异常: {e}")
  
      async def _flush_now(self):
          """立即刷新缓冲数据."""
          async with self._lock:
              if not self._buffer and not self._p2_buffer:
                  return
              batch = list(self._buffer)
              p2_batch = list(self._p2_buffer)
              self._buffer.clear()
              self._p2_buffer.clear()
  
          all_data = batch + p2_batch
          if not all_data:
              return
  
          self._metrics.last_flush_timestamp = datetime.now(timezone.utc).isoformat()
          self._metrics.buffer_usage_pct = 0.0
  
          if self._upload_callback:
              try:
                  if asyncio.iscoroutinefunction(self._upload_callback):
                      await self._upload_callback(all_data)
                  else:
                      self._upload_callback(all_data)
                  logger.debug(f"📤 上报 {len(all_data)} 条追踪数据")
              except Exception as e:
                  logger.error(f"❌ 上报失败: {e}")
                  # 上报失败重新入队
                  async with self._lock:
                      self._buffer.extend(batch)
                      self._p2_buffer.exte
  ```
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
  步骤: pm_decompose
  📋 任务: e10c3af8-71f
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/frontend/monitoring.html`
  ### 文件: `src/backend/agent_team_api.py`
  ### 文件: `src/backend/agents/api.py`
  **子任务拆解:**
    - *项目名称**：AgentsGroup2026 萃取管线状态机（全栈）  
    - *文档版本**：v1.0  
    - *创建日期**：2026-05-10  
    - *负责人**：项目经理（AgentsGroup2026 PM）  
    - *状态**：规划中  
    - `agents/task_engine.py` — 任务引擎；
    - `agents/task_store.py` — 任务持久化；
    - `agents/review_service.py`、`review_models.py`、`review_routes.py` — 复核逻辑与服务；
  
  ### 步骤 02: research
  任务: 后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
  Agent: build_researcher
  📋 任务: e10c3af8-71f
  🤖 Agent: Researcher (researcher)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 Researcher (researcher)。
  你是技术研究员。请对以下任务进行技术调研:
  后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/frontend/monitoring.html`
  ### 文件: `src/backend/agent_team_api.py`
  ### 文件: `src/backend/agents/api.py`
  **变更文件 (2):**
    - `src/frontend/tasks.html`
    - `src/frontend/js/agent-team-config.js`
  
  ### 步骤 03: architecture (完整产出)
  
  # 架构设计 — architect
  
  任务: 后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
  步骤: architecture
  Agent: build_architect
  
  ---
  
  📋 任务: e10c3af8-71f
  🤖 Agent: Architect (architect)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 Architect (architect)。
    请执行以下开发任务:
    
    你是系统架构师。请为以下任务设计技术方案:
    
    ## 任务
    后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
    全栈开发
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
    src/frontend/demo-fieldio-particles.html
    src/frontend/demo-lupi-data-humanism.html
    src/frontend/demo-takram-biosynthetic.html
    src/frontend/index.html
    src/frontend/login.html
    src/frontend/monitoring.html
    src/frontend/plaza-dark.html
    src/frontend/plaza-old.html
    src/frontend/plaza-wabisabi-v2.html
    src/frontend/plaza-wabisabi.html
    src/frontend/plaza.html
    src/frontend/skill-extract.html
    src/frontend/system-evolution.html
    src/frontend/tasks.html
    src/frontend/css/agent-team-config.css
    src/frontend/css/openbridge-theme.css
    src/frontend/css/ws-theme-bridge.css
    src/frontend/js/agent-team-config.js
    src/frontend/js/i18n.js
    src/frontend/js/nav-sidebar.js
    src/backend/__init__.py
    src/backend/agent_team_api.py
    src/backend/main.py
    src/backend/main.py.bak
    src/backend/startup_check.py
    src/backend/startup_validator.py
    src/backend/tests/__init__.py
    src/backend/tests/conftest.py
    src/backend/tests/conftest.py.bak
    src/backend/tests/test_ab_testing.py
    src/backend/tests/test_agent_toolbox.py
    src/backend/tests/test_evolution_race.py
    src/backend/tests/test_evolution_race.py.bak
    src/backend/tests/test_fingerprint.py
    src/backend/tests/test_fingerprint.py.bak
    src/backend/tests/test_gate_evaluator.py
    src/backend/tests/test_gate_evaluator.py.bak
    src/backend/tests/test_merge_plugin.py
    src/backend/tests/test_merge_plugin.py.bak
    src/backend/tests/test_models.py
    src/backend/tests/test_models.py.bak
    src/backend/tests/test_qa_gate_pipeline.py
    src/backend/tests/test_qa_gate_pipeline.py.bak
    src/backend/tests/test_task_engine.py
    src/backend/tests/test_task_engine.py.bak
    src/backend/tests/test_team_manager.py
    src/backend/tests/test_team_manager.py.bak
    src/backend/tests/test_template_variants.py
    src/backend/tests/test_template_variants.py.bak
    src/backend/agents/__init__.py
    src/backend/agents/ab_testing.py
    src/backend/agents/agent_loop.py
    src/backend/agents/agent_toolbox.py
    src/backend/agents/api.py
    src/backend/agents/api.py.bak
    src/backend/agents/audit_store.py
    src/backend/agents/chat_harness.py
    src/backend/agents/domain_events.py
    src/backend/agents/domain_events.py.bak
    src/backend/agents/event_bus.py
    src/backend/agents/execution_registry.py
    src/backend/agents/fingerprint.py
    src/backend/agents/fingerprint.py.bak
    src/backend/agents/gate_evaluator.py
    src/backend/agents/hermes_research.py
    src/backend/agents/knowledge_base.py
    src/backend/agents/merge_engine.py
    src/backend/agents/merge_models.py
    src/backend/agents/models.py
    src/backend/agents/models.py.bak
    src/backend/agents/plaza.py
    src/backend/agents/plaza_engine.py
    src/backend/agents/plaza_routes.py
    src/backend/agents/plaza_routes.py.bak
    src/backend/agents/plaza_store.py
    src/backend/agents/review_models.py
    src/backend/agents/review_routes.py
    src/backend/agents/review_service.py
    src/backend/agents/session_store.py
    src/backend/agents/similarity_engine.py
    src/backend/agents/skill_evolver.py
    src/backend/agents/skill_extractor.py
    src/backend/agents/skill_indexer.py
    src/backend/agents/skill_library.py
    src/backend/agents/skill_querier.py
    src/backend/agents/skill_registry.py
    src/backend/agents/skill_store.py
    src/backend/agents/skill_tracker.py
    src/backend/agents/skill_verifier.py
    src/backend/agents/task_engine.py
    src/backend/agents/task_engine.py.bak
    src/backend/agents/task_store.py
    src/backend/agents/team_manager.py
    src/backend/agents/team_manager.py.bak
    src/backend/agents/team_store.py
    src/backend/agents/tool_executor.py
    src/backend/agents/tool_registry.py
    src/backend/agents/trajectory_analyzer.py
    src/backend/agents/tts_routes.py
    src/backend/agents/teams/__init__.py
    src/backend/agents/teams/ai_coding_team.py
    src/backend/agents/teams/build_team.py
    src/backend/agents/teams/energy_team.py
    src/backend/agents/skills/__init__.py
    src/backend/agents/skills/greeting.py
    src/backend/agents/skills/hello.py
    src/backend/scripts/__init__.py
    src/backend/scripts/migrate.py
    src/backend/scripts/validate_startup.py
    src/backend/scripts/validate_telemetry.py
    src/backend/monitoring/__init__.py
    src/backend/monitoring/__init__.py.bak
    src/backend/monitoring/aggregation_window.py
    src/backend/monitoring/aggregation_window.py.bak
    src/backend/monitoring/collector.py
    src/backend/monitoring/collector.py.bak
    src/backend/monitoring/fingerprint_bypass.py
    src/backend/monitoring/models.py
    src/backend/monitoring/models.py.bak
    src/backend/monitoring/monitoring_routes.py
    src/backend/monitoring/plaza_monitor.py
    src/backend/monitoring/plaza_monitor.py.bak
    src/backend/monitoring/sampler.py
    src/backend/monitoring/trace_bridge.py
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/evolution_executor.py
    src/backend/channels/marine_base.py
    src/backend/channels/merge_channel.py
    src/backend/channels/openclaw_sync.py
    src/backend/channels/openclaw_sync.py.bak
    src/backend/channels/system_evolution.py
    src/docs/agent_handoffs/01d37305-090_executor_started_20260509T073232.md
    src/docs/agent_handoffs/0261754d-288_executor_started_20260509T073231.md
    src/docs/agent_handoffs/05014547-ce8_executor_started_20260509T073232.md
    src/docs/agent_handoffs/0597d622-ad4_executor_started_20260509T073232.md
    src/docs/agent_handoffs/06d3f2a5-82c_executor_started_20260509T073231.md
    src/docs/agent_handoffs/073864e5-58b_executor_started_20260509T073231.md
    src/docs/agent_handoffs/073a3fe7-4d5_executor_started_20260509T073232.md
    src/docs/agent_handoffs/09ff3a16-710_executor_started_20260509T073231.md
    src/docs/agent_handoffs/0a242acf-f52_executor_started_20260509T073232.md
    src/docs/agent_handoffs/0af6e1cb-61c_executor_started_20260509T073231.md
    src/docs/agent_handoffs/0c263083-1c8_executor_started_20260509T073231.md
    src/docs/agent_handoffs/0f6d4e48-ea3_executor_started_20260509T073232.md
    src/docs/agent_handoffs/10857dbb-a51_executor_started_20260509T073231.md
    src/docs/agent_handoffs/11e9b4b9-283_architecture_20260509T075556.md
    src/docs/agent_handoffs/11e9b4b9-283_deploy_20260509T081242.md
    src/docs/agent_handoffs/11e9b4b9-283_develop_20260509T080722.md
    src/docs/agent_handoffs/11e9b4b9-283_document_20260509T081332.md
    ... (共 725 个 src/ 文件)
    
    ```
    
    ### 文件: `src/frontend/monitoring.html`
    ```html
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentsGroup2026 — 可观测性监控面板</title>
    <style>
      :root {
        --bg: #0a0e14;
        --panel-bg: #131820;
        --border: #1e2a3a;
        --text: #c9d1d9;
        --text-dim: #8b949e;
        --accent: #58a6ff;
        --accent2: #3fb950;
        --warn: #d29922;
        --error: #f85149;
        --p0: #f85149;
        --p1: #d29922;
        --p2: #58a6ff;
      }
      * { margin:0; padding:0; box-sizing:border-box; }
      body {
        font-family: "SF Mono","Menlo","Consolas",monospace;
        background: var(--bg);
        color: var(--text);
        height: 100vh;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      /* Header */
      .header {
        background: var(--panel-bg);
        border-bottom: 1px solid var(--border);
        padding: 12px 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        flex-shrink: 0;
      }
      .header h1 {
        font-size: 16px;
        font-weight: 600;
        color: var(--accent);
        margin-right: auto;
      }
      .header .status-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: var(--accent2);
        display: inline-block;
      }
      .header .status-dot.warn { background: var(--warn); }
      .header .status-dot.error { background: var(--error); }
      .header .stat {
        font-size: 12px;
        color: var(--text-dim);
      }
      .header .stat span {
        color: var(--text);
        font-weight: 600;
      }
    
      /* Main Grid */
      .main-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-template-rows: 1fr 1fr;
        gap: 8px;
        padding: 8px;
        flex: 1;
        overflow: hidden;
      }
      .panel {
        background: var(--panel-bg);
        border: 1px solid var(--border);
        border-radius: 6px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      .panel-header {
        padding: 10px 14px;
        border-bottom: 1px solid var(--border);
        font-size: 13px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
      }
      .panel-header .badge {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 3px;
        background: var(--border);
      }
      .panel-body {
        flex: 1;
        overflow-y: auto;
        padding: 12px 14px;
        font-size: 12px;
        line-height: 1.5;
      }
    
      /* Fingerprint Panel */
      .fp-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
      }
      .fp-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 10px;
      }
      .fp-card .label {
        font-size: 10px;
        color: var(--text-dim);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .fp-card .value {
        font-size: 20px;
        font-weight: 700;
        margin: 4px 0;
      }
      .fp-card .value.p0 { color: var(--p0); }
      .fp-card .value.p1 { color: var(--p1); }
      .fp-card .value.p2 { color: var(--p2); }
      .fp-card .value.ok { color: var(--accent2); }
      .fp-card .trend {
        font-size: 10px;
        color: var(--text-dim);
      }
      .fp-card .trend.up { color: var(--error); }
      .fp-card .trend.down { color: var(--accent2); }
    
      /* Trace Panel */
      .trace-list-item {
        padding: 6px 8px;
        border-left: 3px solid var(--border);
        margin-bottom: 6px;
        font-size: 11px;
        transition: border-color 0.2s;
      }
      .trace-list-item:hover { border-left-color: var(--accent); }
      .trace-list-item .tid {
        color: var(--accent);
        font-family: monospace;
      }
      .trace-list-item .meta {
        color: var(--text-dim);
        font-size: 10px;
      }
      .trace-list-item .type-badge {
        font-size: 9px;
        padding: 1px 4px;
        border-radius: 2px;
        background: var(--border);
        margin-left: 6px;
      }
      .trace-list-item .type-badge.plaza { background: #1a3a5c; color: #58a6ff; }
      .trace-list-item .type-badge.handoff { background: #3a2a1a; color: #d29922; }
      .trace-list-item .type-badge.task { background: #1a3a2a; color: #3fb950; }
      .trace-list-item .type-badge.tool { background: #2a1a3a; color: #a371f7; }
    
      /* Topology Panel */
      .topo-canvas {
        width: 100%;
        height: 100%;
        min-height: 200px;
      }
    
      /* Alerts Panel */
      .alert-item {
        padding: 6px 8px;
        border-radius: 4px;
        margin-bottom: 4px;
        font-size: 11px;
        border-left: 3px solid transparent;
      }
      .alert-item.p0 { border-left-color: var(--p0); background: rgba(248,81,73,0.08); }
      .alert-item.p1 { border-left-color: var(--p1); background: rgba(210,153,34,0.08); }
      .alert-item .time {
        font-size: 9px;
        color: var(--text-dim);
      }
    
      /* Bottom bar */
      .bottom-bar {
        background: var(--panel-bg);
        border-top: 1px solid var(--border);
        padding: 8px 16px;
        display: flex;
        gap: 16px;
        align-items: center;
        font-size: 11px;
        color: var(--text-dim);
        flex-shrink: 0;
      }
      .bottom-bar .refresh {
        color: var(--accent);
        cursor: pointer;
      }
      .bottom-bar .refresh:hover { text-decoration: underline; }
    
      /* Tab buttons */
      .tab-row {
        display: flex;
        gap: 4px;
        margin-bottom: 8px;
      }
      .tab-btn {
        font-size: 11px;
        padding: 4px 10px;
        border: 1px solid var(--border);
        border-radius: 3px;
        background: transparent;
        color: var(--text-dim);
        cursor: pointer;
        transition: all 0.2s;
      }
      .tab-btn:hover { border-color: var(--accent); color: var(--text); }
      .tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
    
      /* SVG topology */
      .topo-node { fill: var(--accent); }
      .topo-node.agent { fill: #3fb950; }
      .topo-node.discussion { fill: #58a6ff; }
      .topo-node.task { fill: #d29922; }
      .topo-node.tool { fill: #a371f7; }
      .topo-link { stroke: var(--border); stroke-width: 1; }
      .topo-label { fill: var(--text-dim); font-size: 9px; }
    
      /* Responsive */
      @media (max-width: 900px) {
        .main-grid {
          grid-template-columns: 1fr;
          grid-template-rows: auto;
        }
      }
    </style>
    </head>
    <body>
    
    <div class="header">
      <span class="status-dot" id="statusDot"></span>
      <h1>🔍 可观测性监控面板 · AgentsGroup2026</h1>
      <div class="stat">Trace 数: <span id="statTraces">0</span></div>
      <div class="stat">链路节点: <span id="statNodes">0</span></div>
      <div class="stat">指纹采集: <span id="statFingerprints">0</span></div>
      <div class="stat">异常: <span id="statAnomaly">否</span></div>
    </div>
    
    <div class="main-grid">
      <!-- Panel 1: 行为指纹遥测 -->
      <div class="panel">
        <div class="panel-header">
          🧬 行为指纹遥测旁路
          <span class="badge" style="background:var(--p1);color:#fff">P0/P1</span>
          <span style="font-size:10px;color:var(--text-dim);margin-left:auto" id="fpUpdated">—</span>
        </div>
        <div class="panel-body" id="fingerprintPanel">
          <div class="fp-grid">
            <div class="fp-card">
              <div class="label">假升级率 (false_upgrade)</div>
              <div class="value p0" id="fpFalseUpgrade">—</div>
              <div class="trend" id="fpFalseUpgradeTrend">—</div>
            </div>
            <div class="fp-card">
              <div class="label">行为指纹突变率</div>
              <div class="value p0" id="fpMutationRate">—</div>
              <div class="trend" id="fpMutationTrend">—</div>
            </div>
            <div class="fp-card">
              <div class="label">异常传播深度</div>
              <div class="value p1" id="fpAnomalyDepth">—</div>
              <div class="trend" id="fpAnomalyDepthTrend">—</div>
            </div>
            <div class="fp-card">
              <div class="label">预测错误率</div>
              <div class="value p1" id="fpPredError">—</div>
              <div class="trend" id="fpPredErrorTrend">—</div>
            </div>
            <div class="fp-card">
              <div class="label">资源增量 %</div>
              <div class="value p2" id="fpResourcePct">—</div>
              <div class="trend" id="fpResourceTrend">—</div>
            </div>
            <div class="fp-card">
              <div class="label">能耗增量 %</div>
              <div class="value p2" id="fpEnergyPct">—</div>
              <div class="trend" id="fpEnergyTrend">—</div>
            </div>
            <div class="fp-card">
              <div class="label">策略评估延迟 (ms)</div>
              <div class="value p2" id="fpPolicyLatency">—</div>
              <div class="trend" id="fpPolicyLatencyTrend">—</div>
            </div>
            <div class="fp-card">
              <div class="label">进化停滞率</div>
              <div class="value p2" id="fpStagnation">—</div>
              <div class="trend" id="fpStagnationTrend">—</div>
            </div>
          </div>
        </div>
      </div>
    
      <!-- Panel 2: 聚合链路 Trace ID 关联 -->
      <div class="panel">
        <div class="panel-header">
          🔗 聚合链路 Trace 关联
          <span class="badge" style="background:var(--p0);color:#fff">P0</span>
          <div class="tab-row" style="margin:0 0 0 auto;">
            <button class="tab-btn active" onclick="switchTraceTab('list')">链路列表</button>
            <button class="tab-btn" onclick="switchTraceTab('topo')">拓扑图</button>
          </div>
        </div>
        <div class="panel-body" id="tracePanel">
          <div id="traceListView"></div>
          <div id="traceTopoView" style="display:none;">
            <svg class="topo-canvas" id="topoSvg"></svg>
          </div>
        </div>
      </div>
    
      <!-- Panel 3: 讨论监控 (Plaza Monitor) -->
      <div class="panel">
        <div class="panel-header">
          🏛️ Plaza 讨论监控
          <span class="badge" style="background:var(--p0);color:#fff">P0</span>
        </div>
        <div class="panel-body" id="plazaPanel">
          <div style="color:var(--text-dim);text-align:center;padding:20px;">等待数据...</div>
        </div>
      </div>
    
      <!-- Panel 4: 告警与事件 -->
      <div class="panel">
        <div class="panel-header">
          ⚠️ 实时告警
          <span class="badge" style="background:var(--error);color:#fff" id="alertCount">0</span>
        </div>
        <div class="panel-body" id="alertsPanel">
          <div style="color:var(--text-dim);text-align:center;padding:20px;">无告警</div>
        </div>
      </div>
    </div>
    
    <div class="bottom-bar">
      <span>⏱ 自动刷新: <span id="refreshCountdown">5</span>s</span>
      <span class="refresh" onclick="forceRefresh()">🔄 立即刷新</span>
      <span style="margin-left:auto;">API: <span id="apiStatus">连接中...</span></span>
    </div>
    
    <script>
    // ═══════════════════════════════════════════════
    // 监控面板 JavaScript
    // ═══════════════════════════════════════════════
    
    const API_BASE = '/api/v1/agent-config';
    let traceTab = 'list';
    let refreshTimer = null;
    let countdownTimer = null;
    let countdown = 5;
    let prevFingerprints = {};
    
    // ── 初始化 ────────────────────────────────────
    
    document.addEventListener('DOMContentLoaded', () => {
      fetchAll();
      startRefresh();
    });
    
    function startRefresh() {
      if (refreshTimer) clearInterval(refreshTimer);
      if (countdownTimer) clearInterval(countdownTimer);
    
      refreshTimer = setInterval(() => {
        fetchAll();
        countdown = 5;
        updateCountdown();
      }, 5000);
    
      countdownTimer = setInterval(() => {
        countdown--;
        updateCountdown();
        if (countdown <= 0) countdown = 5;
      }, 1000);
    }
    
    function updateCountdown() {
      document.getElementById('refreshCountdown').textContent = countdown;
    }
    
    function forceRefresh() {
      countdown = 5;
      updateCountdown();
      fetchAll();
    }
    
    // ── 数据获取 ──────────────────────────────────
    
    async function fetchAll() {
      try {
        await Promise.all([
          fetchFingerprints(),
          fetchTraceLinks(),
          fetchPlazaStatus(),
          fetchDashboard(),
        ]);
        document.getElementById('apiStatus').textContent = '✅ 已连接';
        document.getElementById('apiStatus').style.color = 'var(--accent2)';
        document.getElementById('statusDot').className = 'status-dot';
      } catch (e) {
        console.error('Fetch error:', e);
        document.getElementById('apiStatus').textContent = '❌ 连接失败';
        document.getElementById('apiStatus').style.color = 'var(--error)';
        document.getElementById('statusDot').className = 'status-dot error';
      }
    }
    
    async function fetchFingerprints() {
      try {
        const resp = await fetch(`${API_BASE}/monitoring/fingerprints?limit=10`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        renderFingerprints(data);
      } catch (e) {
        console.warn('Fingerprints fetch:', e.message);
      }
    }
    
    async function fetchTraceLinks() {
      try {
        const resp = await fetch(`${API_BASE}/monitoring/traces?limit=30`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        renderTraceLinks(data);
    
        // fetch topology separately
        const topoResp = await fetch(`${API_BASE}/monitoring/topology`);
        if (topoResp.ok) {
          const topoData = await topoResp.json();
          renderTopology(topoData);
        }
      } catch (e) {
        console.warn('Trace links fetch:', e.message);
      }
    }
    
    async function fetchPlazaStatus() {
      try {
        const resp = await fetch(`${API_BASE}/plaza/plazas`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        renderPlazaStatus(data);
      } catch (e) {
        console.warn('Plaza status fetch:', e.message);
      }
    }
    
    async function fetchDashboard() {
      try {
        const resp = await fetch(`${API_BASE}/monitoring/dashboard`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        renderDashboard(data);
      } catch (e) {
        console.warn('Dashboard fetch:', e.message);
      }
    }
    
    // ── 指纹渲染 ──────────────────────────────────
    
    function renderFingerprints(data) {
      const fps = data.fingerprints || [];
      const stats = data.stats || {};
      const latest = fps.length > 0 ? fps[fps.length - 1] : null;
    
      if (latest) {
        updateFpValue('fpFalseUpgrade', latest.false_upgrade_rate, '%', 'p0', 'fpFalseUpgradeTrend');
        updateFpValue('fpMutationRate', latest.behavior_fingerprint_mutation_rate, '%', 'p0', 'fpMutationTrend');
        updateFpValue('fpAnomalyDepth', latest.anomaly_propagation_depth, '', 'p1', 'fpAnomalyDepthTrend');
        updateFpValue('fpPredError', latest.prediction_error_rate, '%', 'p1', 'fpPredErrorTrend');
        updateFpValue('fpResourcePct', latest.resource_increase_pct, '%', 'p2', 'fpResourceTrend');
        updateFpValue('fpEnergyPct', latest.energy_increase_pct, '%', 'p2', 'fpEnergyTrend');
        updateFpValue('fpPolicyLatency', latest.policy_evaluation_latency_ms, 'ms', 'p2', 'fpPolicyLatencyTrend');
        updateFpValue('fpStagnation', latest.evolution_stagnation_rate, '%', 'p2', 'fpStagnationTrend');
    
        document.getElementById('fpUpdated').textContent =
          '更新于 ' + new Date(latest.collected_at).toLocaleTimeString();
      }
    
      document.getElementById('statFingerprints').textContent = stats.total_collected || fps.length;
      document.getElementById('statAnomaly').textContent = stats.anomaly_detected ? '⚠️ 是' : '否';
      if (stats.anomaly_detected) {
        document.getElementById('statAnomaly').style.color = 'var(--error)';
      } else {
        document.getElementById('statAnomaly').style.color = 'var(--text)';
      }
    }
    
    function updateFpValue(id, value, suffix, cssClass, trendId) {
      const el = document.getElementById(id);
      if (value === undefined || value === null) { el.textContent = '—'; return; }
      const displayVal = typeof value === 'number' ? value.toFixed(3) : value;
      el.textContent = displayVal + suffix;
      el.className = 'value ' + cssClass;
    
      // Trend
      const trendEl = document.getElement
    ```
    
    ### 文件: `src/backend/agent_team_api.py`
    ```py
    # -*- coding: utf-8 -*-
    """
    Agent Team API Routes - 双团队管理 REST API
    
    提供构建团队 & 执行团队的状态查询、KPI 考核、
    任务分配、报告查询等端点。挂载至 FastAPI 的 router。
    """
    
    from __future__ import annotations
    
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    from typing import Any, Dict, List, Optional
    
    router = APIRouter(prefix="/api/v1/agent-teams", tags=["Agent Teams"])
    
    
    # ---------------------------------------------------------------------------
    # 全局引用（在 main.py startup 时注入）
    # ---------------------------------------------------------------------------
    _build_team = None
    _execution_team = None
    _scheduler = None
    _evolution_engine = None
    
    
    def set_teams(build_team, execution_team, scheduler, evolution_engine=None):
        """在应用启动时由 main.py 调用，注入团队实例."""
        global _build_team, _execution_team, _scheduler, _evolution_engine
        _build_team = build_team
        _execution_team = execution_team
        _scheduler = scheduler
        _evolution_engine = evolution_engine
    
    
    # ---------------------------------------------------------------------------
    # Request / Response Models
    # ---------------------------------------------------------------------------
    
    class TaskAssignment(BaseModel):
        agent_id: str
        task: str
    
    class FeedbackSubmission(BaseModel):
        category: str = "optimization"
        severity: str = "medium"
        title: str
        detail: str
    
    
    # ---------------------------------------------------------------------------
    # Scheduler
    # ---------------------------------------------------------------------------
    
    @router.get("/scheduler/status")
    async def scheduler_status():
        if not _scheduler:
            raise HTTPException(503, "Scheduler not initialized")
        return _scheduler.get_status()
    
    
    @router.post("/scheduler/report")
    async def scheduler_generate_report():
        if not _scheduler:
            raise HTTPException(503, "Scheduler not initialized")
        return _scheduler.generate_report_now()
    
    
    @router.post("/scheduler/tick")
    async def scheduler_tick_once():
        """手动触发一次调度 tick (调试用)."""
        if not _scheduler:
            raise HTTPException(503, "Scheduler not initialized")
        return _scheduler.tick_once()
    
    
    # ---------------------------------------------------------------------------
    # Build Team
    # ---------------------------------------------------------------------------
    
    @router.get("/build/status")
    async def build_team_status():
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        return _build_team.get_status()
    
    
    @router.get("/build/kpis")
    async def build_team_kpis():
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        return _build_team.get_agent_kpis()
    
    
    @router.get("/build/agents/{agent_id}")
    async def build_agent_detail(agent_id: str):
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        agent = _build_team.agents.get(agent_id)
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found")
        return agent.to_dict()
    
    
    @router.post("/build/assign")
    async def build_assign_task(body: TaskAssignment):
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        ok = _build_team.assign_task(body.agent_id, body.task)
        if not ok:
            raise HTTPException(404, f"Agent '{body.agent_id}' not found")
        return {"status": "assigned", "agent_id": body.agent_id, "task": body.task}
    
    
    @router.get("/build/reports")
    async def build_reports(limit: int = 10):
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        reports = _build_team.hourly_reports[-limit:]
        return [r.to_dict() for r in reports]
    
    
    @router.get("/build/issues")
    async def build_issues():
        if not _build_team:
            raise HTTPException(503, "Build team not initialized")
        return _build_team.issue_backlog
    
    
    # ---------------------------------------------------------------------------
    # Execution Team
    # ---------------------------------------------------------------------------
    
    @router.get("/execution/status")
    async def execution_team_status():
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        return _execution_team.get_status()
    
    
    @router.get("/execution/agents/{agent_id}")
    async def execution_agent_detail(agent_id: str):
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        agent = _execution_team.agents.get(agent_id)
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found")
        return agent.to_dict()
    
    
    @router.get("/execution/reports")
    async def execution_reports(limit: int = 10):
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        reports = _execution_team.execution_reports[-limit:]
        return [r.to_dict() for r in reports]
    
    
    @router.get("/execution/feedback")
    async def execution_feedback():
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        return [item.to_dict() for item in _execution_team.feedback_queue]
    
    
    @router.post("/execution/feedback")
    async def submit_feedback(body: FeedbackSubmission):
        if not _execution_team:
            raise HTTPException(503, "Execution team not initialized")
        item = _execution_team.submit_feedback(
            category=body.category,
            severity=body.severity,
            title=body.title,
            detail=body.detail,
        )
        return item.to_dict()
    
    
    # ---------------------------------------------------------------------------
    # Combined
    # ---------------------------------------------------------------------------
    
    @router.get("/overview")
    async def teams_overview():
        """一站式获取双团队全局概览."""
        result: Dict[str, Any] = {}
        if _build_team:
            bs = _build_team.get_status()
            result["build_team"] = {
                "health": bs["health"],
                "agent_count": bs["agent_count"],
                "metrics": bs["metrics"],
            }
        if _execution_team:
            es = _execution_team.get_status()
            result["execution_team"] = {
                "health": es["health"],
                "agent_count": es["agent_count"],
                "metrics": es["metrics"],
            }
        if _scheduler:
            result["scheduler"] = _scheduler.get_status()
        if _evolution_engine:
            result["evolution"] = _evolution_engine.get_status()
        return result
    
    
    # ---------------------------------------------------------------------------
    # System Evolution (自我演进引擎)
    # ---------------------------------------------------------------------------
    
    @router.get("/evolution/status")
    async def evolution_status():
        """获取自我演进引擎状态。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_status()
    
    
    @router.get("/evolution/summary")
    async def evolution_summary():
        """获取演进项汇总。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_evolution_summary()
    
    
    @router.get("/evolution/items")
    async def evolution_items(status: Optional[str] = None):
        """获取演进项列表，可按状态过滤。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.get_evolution_items(status=status)
    
    
    @router.get("/evolution/rules")
    async def evolution_rules():
        """获取审查规则列表。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return [r.to_dict() for r in _evolution_engine.audit_rules]
    
    
    @router.post("/evolution/rules/from-task")
    async def evolution_add_rule_from_task(body: dict):
        """从议事厅任务导入为审查规则。body: {title, description, severity?, task_id?, team_id?}"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        if not body.get("title"):
            raise HTTPException(400, "title is required")
        return _evolution_engine.add_rule_from_task(body)
    
    
    @router.delete("/evolution/rules/{rule_id}")
    async def evolution_delete_rule(rule_id: str):
        """删除指定审查规则。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        result = _evolution_engine.delete_audit_rule(rule_id)
        if result.get("status") == "not_found":
            raise HTTPException(404, result.get("message", "规则不存在"))
        return result
    
    
    @router.put("/evolution/rules/{rule_id}")
    async def evolution_update_rule(rule_id: str, body: dict):
        """更新指定审查规则。body: {title?, description?, severity?, reference?, domain?, rating_weight?}"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        result = _evolution_engine.update_audit_rule(rule_id, body)
        if result.get("status") == "not_found":
            raise HTTPException(404, result.get("message", "规则不存在"))
        return result
    
    
    @router.post("/evolution/audit")
    async def evolution_run_audit():
        """手动触发一次审查。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.run_full_audit()
    
    
    @router.post("/evolution/cycle")
    async def evolution_run_cycle():
        """运行完整演进周期（审查→派发→验证→关闭）。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.run_evolution_cycle()
    
    
    @router.post("/evolution/dispatch")
    async def evolution_dispatch():
        """派发所有待处理演进项给 Build 团队。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.dispatch_all_pending()
    
    
    @router.post("/evolution/verify")
    async def evolution_verify():
        """验证所有待验证项。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        return _evolution_engine.verify_all_pending()
    
    
    @router.get("/evolution/items/{item_id}")
    async def evolution_item_detail(item_id: str):
        """获取单个演进项详情。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        item = _evolution_engine.evolution_items.get(item_id)
        if not item:
            raise HTTPException(404, f"Item '{item_id}' not found")
        return item.to_dict()
    
    
    @router.post("/evolution/items/{item_id}/progress")
    async def evolution_mark_progress(item_id: str):
        """标记演进项为进行中。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        ok = _evolution_engine.mark_in_progress(item_id)
        if not ok:
            raise HTTPException(404, f"Item '{item_id}' not found")
        return {"status": "ok", "item_id": item_id, "new_status": "in_progress"}
    
    
    @router.post("/evolution/items/{item_id}/complete")
    async def evolution_mark_complete(item_id: str):
        """标记演进项构建完成，进入待验证。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        ok = _evolution_engine.mark_build_complete(item_id)
        if not ok:
            raise HTTPException(404, f"Item '{item_id}' not found")
        return {"status": "ok", "item_id": item_id, "new_status": "verify_pending"}
    
    
    @router.delete("/evolution/items/{item_id}")
    async def evolution_delete_item(item_id: str):
        """删除指定演进条目。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        result = _evolution_engine.delete_evolution_item(item_id)
        if result.get("status") == "not_found":
            raise HTTPException(404, result.get("message", "条目不存在"))
        return result
    
    
    @router.put("/evolution/items/{item_id}")
    async def evolution_update_item(item_id: str, body: dict):
        """更新指定演进条目。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        result = _evolution_engine.update_evolution_item(item_id, body)
        if result.get("status") == "not_found":
            raise HTTPException(404, result.get("message", "条目不存在"))
        return result
    
    
    @router.get("/evolution/executor/status")
    async def evolution_executor_status():
        """获取演进执行器状态 (正在执行的任务等)."""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        executor = _evolution_engine._get_executor()
        return executor.get_status()
    
    
    @router.get("/evolution/items/{item_id}/execution-log")
    async def evolution_item_execution_log(item_id: str):
        """获取演进项的 AgentLoop 执行事件日志."""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        executor = _evolution_engine._get_executor()
        log = executor.get_event_log(item_id)
        result = executor.get_result(item_id)
        return {
            "item_id": item_id,
            "is_running": executor.is_running(item_id),
            "events": log,
            "result": result,
        }
    
    
    @router.delete("/evolution/zones/{zone_id}")
    async def evolution_delete_zone(zone_id: str):
        """删除指定合规区域。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        result = _evolution_engine.delete_compliance_zone(zone_id)
        if result.get("status") == "not_found":
            raise HTTPException(404, result.get("message", "区域不存在"))
        return result
    
    
    @router.put("/evolution/zones/{zone_id}")
    async def evolution_update_zone(zone_id: str, body: dict):
        """更新指定合规区域。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        result = _evolution_engine.update_compliance_zone(zone_id, body)
        if result.get("status") == "not_found":
            raise HTTPException(404, result.get("message", "区域不存在"))
        return result
    
    
    @router.post("/evolution/close-verified")
    async def evolution_close_verified():
        """关闭所有已验证通过的演进项。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        closed = _evolution_engine.close_verified()
        return {"closed": closed, "count": len(closed)}
    
    
    @router.post("/evolution/close")
    async def evolution_close():
        """关闭所有已验证通过的演进项 (close-verified 别名)。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        closed = _evolution_engine.close_verified()
        return {"closed": closed, "count": len(closed)}
    
    
    @router.get("/evolution/history")
    async def evolution_audit_history():
        """获取审查历史记录。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        raw = _evolution_engine.get_audit_history()
        # Normalize field names for frontend (expects timestamp, total)
        result = []
        for h in raw:
            entry = dict(h)
            entry.setdefault("timestamp", entry.pop("time", None))
            entry.setdefault("total", (entry.get("passed") or 0) + (entry.get("failed") or 0) + (entry.get("skipped") or 0))
            result.append(entry)
        return result
    
    
    @router.get("/evolution/analytics")
    async def evolution_analytics():
        """获取演进分析数据 (域覆盖、严重度分布、趋势)。"""
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        summary = _evolution_engine.get_evolution_summary()
        history = _evolution_engine.get_a
    ```
    
    ### 文件: `src/backend/agents/api.py`
    ```py
    # -*- coding: utf-8 -*-
    """AgentsGroup2026 Agent Team Framework -- REST API Router.
    
    Clawith-style CRUD API for teams, agents, models, tools, skills.
    Tab-based organization:
      1. Team Info
      2. Model Pool
      3. Tools
      4. Skills
      5. Agents -- 5-step wizard
      6. Overview
    """
    
    from __future__ import annotations
    
    import asyncio
    import json
    from datetime import datetime, timezone
    
    from typing import Any, Dict, List, Optional
    
    from fastapi import APIRouter, HTTPException, status
    from pydantic import BaseModel, Field
    
    from .models import (
        AccessLevel,
        AgentState,
        AgentChannelConfig,
        AgentPermission,
        AgentPersonality,
        AgentProfile,
        AgentTemplateType,
        HermesAgentConfig,
        ModelConfig,
        ToolsetDistribution,
    )
    from .hermes_research import (
        RESEARCH_TOOLSET_DISTRIBUTIONS,
        HERMES_TOOLSETS,
        create_hermes_researcher,
        build_research_s
  ...(截断)
  
  ## 推荐工作流（严格遵守）
  **Step 1 · 侦察**: 
    - 用 `list_files(path='src/backend/channels')` 看现有 Channel 模块
    - 用 `grep(pattern='class MarineChannel', include='src/backend/**/*.py')` 找基类定义
    - 用 `read_file(path='src/backend/channels/marine_base.py')` 读完整接口规范
    - 找到任何要继承的基类 / 要调用的函数，**先 grep 再 read**，不要靠记忆
  
  **Step 2 · 验证假设**: 用 `run_python` 跑一段 import 代码，确认 import 路径正确
    示例: `run_python(code='from channels.marine_base import ChannelPriority; print(list(ChannelPriority))')`
  
  **Step 3 · 编码**: 
    - 新功能 → `write_file` 创建新模块（推荐放在 src/backend/channels/ 或 src/frontend/digital-twin/）
    - 改现有大文件 → 用 `patch_file(path, search, replace)` 精准修改
    - **禁止** write_file 覆盖 >200 行的现有文件 (会被 shrink-guard 拒绝)
  
  **Step 4 · 自检**: 
    - Python: `run_python(code='from channels.your_new_module import YourClass; YourClass()')`
    - 通过则继续；失败则修复后再次验证
  
  **Step 5 · 完成**: 调用 `finish(summary='...', files_changed=[...])`
  
  ## 工程规范
  - 所有 Channel 必须 `from channels.marine_base import MarineChannel, ChannelPriority, ChannelStatus` 然后 `class X(MarineChannel)`
  - ChannelPriority 只有 P0 / P1 / P2，**没有 P3**
  - 必须实现 `process_event()` 和 `get_status()`
  - 新参数必须有默认值（向后兼容）
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
🛠 使用 DeepSeek V4 工具循环模式 (read/grep/write/exec)...

🔗 API: https://api.deepseek.com/v1
模型: deepseek-v4-pro
角色: developer
────────────────────────────────────────────────────────────

🚀 工具集: read_file, grep, list_files, write_file, patch_file, run_python, finish


🧠 turn#0 (14.61s, 0字, 3个工具调用)
🔧 调用工具: list_files({"path": "src/backend/channels", "max_depth": 2})
   ✅ list_files: 7 files
🔧 调用工具: grep({"pattern": "class.*Channel|class.*MarineChannel|class.*StateMachine|class.*Pipeline", "include": "src/backend/**/*.py"})
   ✅ grep: 23 hits
🔧 调用工具: read_file({"path": "src/backend/channels/marine_base.py"})
   ✅ read_file: 467 lines, 12121 chars

🧠 turn#1 (7.47s, 0字, 3个工具调用)
🔧 调用工具: read_file({"path": "src/backend/agents/task_engine.py"})
   ✅ read_file: 399 lines, 15098 chars
🔧 调用工具: read_file({"path": "src/backend/agents/task_store.py"})
   ✅ read_file: 63 lines, 2147 chars
🔧 调用工具: read_file({"path": "src/backend/agents/review_models.py"})
   ✅ read_file: 184 lines, 6717 chars

🧠 turn#2 (6.21s, 0字, 3个工具调用)
🔧 调用工具: read_file({"path": "src/backend/agents/review_service.py"})
   ✅ read_file: 290 lines, 9975 chars
🔧 调用工具: read_file({"path": "src/backend/agents/gate_evaluator.py"})
   ✅ read_file: 243 lines, 7007 chars
🔧 调用工具: read_file({"path": "src/backend/agents/domain_events.py"})
   ✅ read_file: 313 lines, 10117 chars

🧠 turn#3 (8.69s, 0字, 3个工具调用)
🔧 调用工具: read_file({"path": "src/backend/agents/review_routes.py"})
   ✅ read_file: 321 lines, 9523 chars
🔧 调用工具: read_file({"path": "src/backend/agents/audit_store.py"})
   ✅ read_file: 242 lines, 7865 chars
🔧 调用工具: read_file({"path": "src/backend/agents/event_bus.py"})
   ✅ read_file: 175 lines, 5322 chars

🧠 turn#4 (7.74s, 0字, 2个工具调用)
🔧 调用工具: read_file({"path": "src/backend/main.py"})
   ✅ read_file: 678 lines, 22982 chars
🔧 调用工具: read_file({"path": "src/frontend/tasks.html", "start_line": 1, "end_line": 100})
   ✅ read_file: 176 lines, 4708 chars

🧠 turn#5 (24.37s, 86字, 1个工具调用)
🔧 调用工具: run_python({"code": "\n# Verify key imports\nfrom agents.domain_events import DomainEvent, EventType\nfrom agents.event_bus import EventBus, get_event_bus\nfrom agents.rev)
   ✅ run_python: exit=0, 0.16s

🧠 turn#6 (7.46s, 0字, 2个工具调用)
🔧 调用工具: read_file({"path": "src/backend/agents/domain_events.py", "start_line": 1, "end_line": 50})
   ✅ read_file: 313 lines, 1359 chars
🔧 调用工具: read_file({"path": "src/backend/agents/review_models.py", "start_line": 1, "end_line": 80})
   ✅ read_file: 184 lines, 2762 chars

🧠 turn#7 (92.37s, 106字, 1个工具调用)
🔧 调用工具: write_file({"path": "src/backend/agents/extraction_models.py", "content": "# -*- coding: utf-8 -*-\n\"\"\"萃取管线状态机 — 数据模型 (Extraction Pipeline State Machine Models).\n\n定义:)
   ✅ write_file: 9716 bytes

🧠 turn#8 (115.63s, 0字, 1个工具调用)
🔧 调用工具: write_file({"content": "# -*- coding: utf-8 -*-\n\"\"\"萃取管线事件溯源存储 — Append-only Event Store.\n\n基于 JSON 文件的轻量级事件溯源存储：\n- 追加写入（不可变事件流）\n- 按 pipeline_id 分区\n- 支持事件回放重建管线状态\n)
   ✅ write_file: 15286 bytes

🧠 turn#9 (125.78s, 48字, 1个工具调用)
🔧 调用工具: write_file({"content": "# -*- coding: utf-8 -*-\n\"\"\"萃取管线状态机 — Pipeline State Machine + Gate Validation.\n\n核心职责:\n1. 四阶段流转控制 (DRAFT → REVIEW → APPROVAL → PUBLISHED)\n2.)
   ✅ write_file: 15497 bytes

🧠 turn#10 (120.57s, 24字, 1个工具调用)
🔧 调用工具: write_file({"content": "# -*- coding: utf-8 -*-\n\"\"\"萃取管线 REST API — State Transitions + Todo-driven API.\n\n端点:\n  CRUD:\n    POST   /api/v1/extraction/pipelines       )
   ✅ write_file: 14306 bytes

🧠 turn#11 (23.14s, 53字, 1个工具调用)
🔧 调用工具: run_python({"code": "\n# Test extraction_models imports\nfrom agents.extraction_models import (\n    PipelineStage, TransitionType, ReviewerIdentity, TodoStatus,\n    Gate)
   ✅ run_python: exit=0, 0.16s

🧠 turn#12 (38.99s, 0字, 1个工具调用)
🔧 调用工具: run_python({"code": "\n# Test extraction_store imports and basic operations\nimport asyncio\nimport tempfile\nfrom pathlib import Path\n\nfrom agents.extraction_store impo)
   ✅ run_python: exit=0, 0.18s

🧠 turn#13 (50.36s, 0字, 1个工具调用)
🔧 调用工具: run_python({"code": "\n# Test extraction_pipeline engine: gate validation + state transitions\nimport asyncio\nimport tempfile\nfrom pathlib import Path\n\nasync def test_)
   ✅ run_python: exit=1, 0.29s

🧠 turn#14 (13.9s, 65字, 1个工具调用)
🔧 调用工具: patch_file({"path": "src/backend/agents/extraction_pipeline.py", "search": "    async def get_all_todos(\n        self,\n        assignee_id: Optional[str] = None,\n      )
   ✅ patch_file: 15612 bytes

🧠 turn#15 (31.35s, 0字, 1个工具调用)
🔧 调用工具: run_python({"code": "\nimport asyncio, tempfile\nfrom pathlib import Path\n\nasync def test_engine():\n    from agents.extraction_store import ExtractionStore\n    from ag)
   ✅ run_python: exit=0, 0.18s

🧠 turn#16 (4.88s, 95字, 1个工具调用)
🔧 调用工具: grep({"pattern": "include_router|app\\.include_router", "include": "src/backend/main.py"})
   ✅ grep: 8 hits

🧠 turn#17 (5.52s, 0字, 1个工具调用)
🔧 调用工具: read_file({"path": "src/backend/main.py", "start_line": 235, "end_line": 275})
   ✅ read_file: 702 lines, 1697 chars

🧠 turn#18 (4.87s, 0字, 1个工具调用)
🔧 调用工具: read_file({"end_line": 280, "path": "src/backend/main.py", "start_line": 260})
   ✅ read_file: 702 lines, 628 chars

🧠 turn#19 (12.61s, 0字, 1个工具调用)
🔧 调用工具: patch_file({"path": "src/backend/main.py", "search": "        except Exception as e:\n            logger.warning(f\"⚠️ TTS API failed: {e}\")\n\n    except Exception as e:)
   ✅ patch_file: 24712 bytes

🧠 turn#20 (245.99s, 57字, 1个工具调用)
🔧 调用工具: write_file({"content": "<!DOCTYPE html>\n<html lang=\"zh-CN\" data-obc-theme=\"dusk\">\n<head>\n<meta charset=\"UTF-8\">\n<meta name=\"viewport\" content=\"width=device-wi)
   ✅ write_file: 24813 bytes

🧠 turn#21 (34.64s, 78字, 1个工具调用)
🔧 调用工具: run_python({"code": "\n# Full integration test: routes, store, engine\nimport asyncio, tempfile\nfrom pathlib import Path\n\nasync def full_integration_test():\n    # 1. T)
   ✅ run_python: exit=0, 0.32s

🧠 turn#22 (5.9s, 50字, 1个工具调用)
🔧 调用工具: grep({"include": "src/backend/main.py", "pattern": "Extraction Pipeline|extraction_router|extraction_store|extraction_engine"})
   ✅ grep: 8 hits

🧠 turn#23 (16.34s, 63字, 1个工具调用)
🔧 调用工具: run_python({"code": "\n# Quick smoke test: verify all existing modules still import\nimports_to_test = [\n    (\"agents.models\", \"from agents.models import AgentProfile,)
   ✅ run_python: exit=0, 0.49s

🧠 turn#24 (33.13s, 67字, 1个工具调用)
🔧 调用工具: finish({"summary": "\n## 萃取管线状态机 — 全栈开发完成\n\n### 后端 (4 个新文件 + 1 个修改)\n\n**1. `agents/extraction_models.py`** — 数据模型层\n- `PipelineStage` 枚举：四阶段 DRAFT → REVIEW → APPROVA)

🏁 循环结束: finish_called (turn #24)

✅ 完成 (25 轮迭代)
修改文件 6 个: src/backend/agents/extraction_models.py, src/backend/agents/extraction_store.py, src/backend/agents/extraction_pipeline.py, src/backend/agents/extraction_routes.py, src/backend/main.py, src/frontend/e

📋 总结:

## 萃取管线状态机 — 全栈开发完成

### 后端 (4 个新文件 + 1 个修改)

**1. `agents/extraction_models.py`** — 数据模型层
- `PipelineStage` 枚举：四阶段 DRAFT → REVIEW → APPROVAL → PUBLISHED
- `TransitionType`：advance / reject / reset / archive
- `ReviewerIdentity`：8 种身份类型 (peer, senior, lead, architect, qa, external…)
- `GateRequirement`：门禁配置 (最少复核人数、必填身份、同意票/否决票、自审禁止、跨团队要求)
- `GateCheckResult`：门禁检查结果
- `StageTransition`：事件溯源迁移记录
- `TodoItem` / `TodoStatus`：待办驱动模型
- `ExtractionPipeline`：聚合根实体
- `default_gate_requirements()`：默认三阶段门禁 (REVIEW需peer+senior 2人; APPROVAL需lead; PUBLISHED需architect)

**2. `agents/extraction_store.py`** — 事件溯源存储
- Append-only JSONL 事件流 (不可变)
- JSON 快照缓存加速读取
- asyncio.Lock 线程安全
- 完整 CRUD + 事件回放 (replay_events)
- Reviewer / Todo 管理
- 全局单例模式

**3. `agents/extraction_pipeline.py`** — 状态机引擎
- `check_gate()`：6 项门禁检查 (人数/身份/同意票/否决票/自审/跨团队)
- `advance()`：推进到下一阶段（门禁校验 + 事件溯源）
- `reject()` / `reset()`：打回/重置
- `submit_review()`：提交复核（含自审拦截 + auto_advance）
- `resolve_todo()`：解决待办并自动尝试推进
- `_generate_stage_todos()` / `_generate_gate_todos()`：根据缺口自动生成待办
- `GateValidationError`：门禁失败异常（含完整结果）

**4. `agents/extraction_routes.py`** — REST API (18 个端点)
- CRUD: `POST/GET/PATCH/DELETE /api/v1/extraction/pipelines`
- 状态迁移: `/advance`, `/reject`, `/reset`, `/check-gate`
- 复核: `POST/GET /reviewers`
- 待办: `GET /todos`, 创建/更新/解决
- 事件: `GET /events` (事件溯源回放)
- 统计: `GET /stats`, `GET /enums`

**5. `main.py`** — 路由注册 (patch)
- 在 Agent Config 初始化块中注册 Extraction Pipeline API

### 前端 (1 个新文件)

**6. `frontend/extraction
