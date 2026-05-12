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
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 后端搭建萃取管线状态机，实现四阶段流转、事件溯源存储、阶段门禁校验（含交叉复核人数与身份检查），并暴露状态迁移和Todo驱动的API
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: e10c3af8-71f
  🤖 Agent: Researcher (researcher)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 Researcher (researcher)。
    请执行以下开发任务:
    
    你是技术研究员。请对以下任务进行技术调研:
    
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
        build_research
  ...(截断)
  
  ## ⚠️ 重要提示
  上方 📂 项目上下文 包含了任务相关的实际源文件。
  请基于这些文件设计方案，不要引用不存在的文件。
  
  ## 要求
  1. 基于调研结果和实际源码，设计详细技术方案
  2. 明确指出需要修改的文件和具体修改内容
  3. 定义接口规范（如有新增 API）
  4. 为开发工程师提供逐步实施指南
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
⚡ 使用 DeepSeek V4 直连 (64K 输出, 流式)...

🔗 API: api.deepseek.com | 模型: deepseek-v4-pro
────────────────────────────────────────────────────────────

# 萃取管线状态机 — 技术设计方案

## 1. 概述
本方案为 AgentsGroup2026 系统新增「知识萃取管线（Extraction Pipeline）」模块，实现带四阶段流转、事件溯源存储、阶段门禁校验的全栈功能。后端基于 Python FastAPI，前端采用原生 HTML + JS，与现有智能体团队框架无缝集成。

**四大阶段**（可根据业务调整）：

| 阶段 | 名称 | 说明 |
|------|------|------|
| `COLLECTION` | 资料汇集 | 数据输入、文档上传、原始信息收集 |
| `EXTRACTION` | 内容提取 | 智能体/人工从原料中提取结构化知识点 |
| `REVIEW` | 交叉复核 | 多人（多智能体）按规则复核提取结果 |
| `ARCHIVE` | 归档发布 | 通过复核后永久存储，进入知识库 |

## 2. 核心设计

### 2.1 事件溯源（Event Sourcing）
- 所有状态变更记录为领域事件（`PipelineEvent`），不可变、顺序追加。
- 项目当前状态通过重放事件流计算得出，不存储可变状态快照。
- 事件存储使用现有 `audit_store.py` 或新建轻量级 JSON 行文件（每行一个事件），保证顺序和可审计性。

### 2.2 阶段门禁（Gate Check）
每次尝试进入下一阶段时，执行门禁检查：
- **交叉复核人数**：`REVIEW` 阶段前，需至少 N 位具备特定角色的复核者提交有效评审（可配置）。
- **身份检查**：复核者须属于指定团队或拥有指定权限（复用 `AgentPermission` 和 `review_service` 的身份验证）。
- **前置条件**：阶段依赖的前置任务必须完成（如所有提取任务结果就绪）。
门禁检查可扩展为插件式规则，方便后续调整。

### 2.3 待办事项驱动（Todo‑Driven）
每个阶段暴露需要人工/智能体干预的待办列表，例如：
- `COLLECTION` → 「请上传指定文档」
- `EXTRACTION` → 「请确认提取结果」
- `REVIEW` → 「请进行交叉复核」
前端通过 API 获取当前管线的待办清单，并展示操作按钮。

## 3. 技术架构

```
┌─────────────────┐      ┌──────────────────────────────┐
│   Frontend       │      │   Backend API (FastAPI)      │
│ extraction-      │◄────►│   pipeline_routes.py         │
│ pipeline.html    │      └──────────┬───────────────────┘
└─────────────────┘                 │
                      ┌─────────────▼────────────────────┐
                      │  PipelineEngine (状态机核心)      │
                      │  - 四阶段流转逻辑                 │
                      │  - GateEvaluator (门禁)           │
                      │  - EventStream 重放               │
                      └─────────────┬────────────────────┘
                                    │
                      ┌─────────────▼────────────────────┐
                      │  PipelineStore (事件持久化)       │
                      └──────────────────────────────────┘
                      ┌─────────────▼────────────────────┐
                      │  ReviewService (复用)             │
                      └──────────────────────────────────┘
```

- **复用组件**：`review_service` / `review_models` 提供复核人数、身份校验能力；`event_bus` 发布域事件；`task_store` 风格的事件存储模式。
- **新增组件**：`pipeline_engine.py`、`pipeline_store.py`、`pipeline_routes.py`、`pipeline_models.py`。

## 4. 文件变更清单

### 4.1 新增文件

| 文件 | 职责 |
|------|------|
| `src/backend/agents/pipeline_models.py` | 枚举、Pydantic 模型（Phase, PipelineEvent, PipelineState, GateRule, TodoItem） |
| `src/backend/agents/pipeline_engine.py` | 状态机核心，包含状态迁移、门禁评估、事件溯源重放 |
| `src/backend/agents/pipeline_store.py` | 事件持久化（JSON行文件或沿用 `task_store` 模式） |
| `src/backend/agents/pipeline_routes.py` | FastAPI 路由：CRUD、状态迁移、待办查询 |
| `src/frontend/extraction-pipeline.html` | 前端管线管理界面（列表、详情、迁移按钮） |
| `src/frontend/js/extraction-pipeline.js` | 前端交互逻辑 |
| `tests/test_pipeline_engine.py` | 单元测试（状态机、门禁） |

### 4.2 需修改的现有文件

| 文件 | 修改点 |
|------|--------|
| `src/backend/main.py` | 注册 `pipeline_routes` 路由器，并调用 `init_pipeline_engine(...)` 注入依赖 |
| `src/backend/agents/__init__.py` | 可选：导出新模块关键类 |
| `src/frontend/index.html` 或导航栏配置文件 | 添加指向 `extraction-pipeline.html` 的链接 |

## 5. 接口规范（API）

所有端点挂载于 `/api/v1/pipelines`。

### 5.1 管线管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/pipelines` | 分页查询所有管线项目（可选 `?status=` 过滤当前阶段） |
| `POST` | `/pipelines` | 创建新管线项目（body: `{title, description, initial_data?}`） |
| `GET` | `/pipelines/{pipeline_id}` | 获取项目详情，包括当前阶段、所有事件、待办项 |
| `DELETE` | `/pipelines/{pipeline_id}` | 软删除（追加 deleted 事件） |

### 5.2 状态迁移

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/pipelines/{pipeline_id}/transition` | 尝试推进到下一阶段（body: `{target_phase?}`, 默认自动计算下一阶段） |

响应示例（成功）：
```json
{
  "pipeline_id": "pip-123",
  "previous_phase": "EXTRACTION",
  "current_phase": "REVIEW",
  "gate_check": {
    "passed": true,
    "reasons": []
  },
  "events_applied": 1
}
```
失败时返回 400 + 门禁未通过原因：
```json
{
  "detail": "门禁校验失败",
  "gate_check": {
    "passed": false,
    "reasons": ["至少需要 2 名复核者，当前仅 1 名", "缺失角色: senior_reviewer"]
  }
}
```

### 5.3 待办事项（Todo‑Driven）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/pipelines/{pipeline_id}/todos` | 返回当前阶段需要完成的待办列表 |

响应示例：
```json
{
  "pipeline_id": "pip-123",
  "current_phase": "REVIEW",
  "todos": [
    {
      "type": "review",
      "description": "需角色 senior_reviewer 进行复核",
      "assigned_to_teams": ["ai_coding_team"],
      "completed": false
    }
  ]
}
```

### 5.4 门禁规则配置（可选）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/pipelines/gate-rules` | 获取当前生效的门禁规则 |
| `PUT` | `/pipelines/gate-rules` | 更新规则（body: `{rules: [...]}`） |

## 6. 数据模型设计

### 6.1 PipelinePhase（枚举）
```python
class PipelinePhase(str, Enum):
    COLLECTION = "collection"
    EXTRACTION = "extraction"
    REVIEW = "review"
    ARCHIVE = "archive"
```

### 6.2 PipelineEvent（Pydantic）
```python
class PipelineEvent(BaseModel):
    event_id: str          # uuid
    pipeline_id: str
    event_type: str        # "created", "phase_changed", "todo_added", "deleted"
    phase: PipelinePhase   # 事件发生时的阶段
    timestamp: datetime
    actor: str             # 触发者（用户或 agent_id）
    payload: dict          # 自由数据（如原因、备注）
    version: int           # 事件序号
```

### 6.3 PipelineState（运行时状态，由事件重放得出）
```python
@dataclass
class PipelineState:
    pipeline_id: str
    title: str
    description: str
    current_phase: PipelinePhase
    todos: List[TodoItem]
    history: List[PipelineEvent]
    created_at: datetime
    deleted: bool = False
```

### 6.4 GateRule（门禁规则定义）
```python
class GateRule(BaseModel):
    from_phase: PipelinePhase
    to_phase: PipelinePhase
    min_reviewers: int = 1
    required_roles: List[str] = []   # e.g. ["senior_reviewer"]
    required_teams: List[str] = []   # 允许执行复核的团队ID
    precondition_checks: List[str] = []  # 自定义检查函数名
```

## 7. 实现细节

### 7.1 状态机核心逻辑（`pipeline_engine.py`）

```python
class PipelineEngine:
    def __init__(self, store: PipelineStore, review_service, gate_rules: List[GateRule]):
        self.store = store
        self.review_service = review_service
        self.gate_rules = gate_rules

    async def build_state(self, pipeline_id) -> PipelineState:
        events = await self.store.load_events(pipeline_id)
        return self._apply_events(events)

    def _apply_events(self, events) -> PipelineState:
        # 逐个事件重放，构建当前状态
        ...

    async def attempt_transition(self, pipeline_id, target_phase=None) -> Tuple[bool, str]:
        state = await self.build_state(pipeline_id)
        next_phase = target_phase or self._next_phase(state.current_phase)
        if next_phase is None:
            return False, "已是最终阶段"
        # 执行门禁
        gate_result = await self.evaluate_gate(state, next_phase)
        if not gate_result.passed:
            return False, gate_result.reasons
        # 创建事件并存储
        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            pipeline_id=pipeline_id,
            event_type="phase_changed",
            phase=next_phase,
            timestamp=datetime.now(timezone.utc),
            actor="system",  # 暂时
            payload={"reason": "manual transition"},
            version=len(state.history)+1
        )
        await self.store.append_event(event)
        return True, "迁移成功"
```

### 7.2 事件存储（`pipeline_store.py`）
考虑轻量级实现，使用单个 JSON 行文件（`data/pipeline_events.jsonl`），追加写入，读取时按 `pipeline_id` 过滤。
```python
class PipelineStore:
    def __init__(self, filepath="data/pipeline_events.jsonl"):
        self.filepath = filepath
        # 线程安全锁...

    async def load_events(self, pipeline_id: str) -> List[dict]:
        events = []
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                for line in f:
                    try:
                        evt = json.loads(line)
                        if evt["pipeline_id"] == pipeline_id:
                            events.append(PipelineEvent(**evt))
                    except:
                        pass
        return sorted(events, key=lambda e: e.version)

    async def append_event(self, event: PipelineEvent):
        with open(self.filepath, "a") as f:
            f.write(event.json() + "\n")
```

### 7.3 门禁评估（复用 `review_service`）
```python
async def evaluate_gate(self, state, next_phase):
    # 查找匹配规则
    rule = next((r for r in self.gate_rules if r.from_phase==state.current_phase and r.to_phase==next_phase), None)
    if rule is None:
        return GateResult(passed=True)  # 无规则限制

    reasons = []
    # 复核人数检查
    reviews = await self.review_service.get_reviews_for_pipeline(state.pipeline_id)
    if len(reviews) < rule.min_reviewers:
        reasons.append(f"至少需要 {rule.min_reviewers} 名复核者，当前 {len(reviews)}")
    # 角色检查
    if rule.required_roles:
        reviewer_roles = {r.reviewer_role for r in reviews}
        missing = set(rule.required_roles) - reviewer_roles
        if missing:
            reasons.append(f"缺失角色: {', '.join(missing)}")
    # 团队检查
    if rule.required_teams:
        ...
    return GateResult(passed=len(reasons)==0, reasons=reasons)
```

### 7.4 API 路由（`pipeline_routes.py`）
示例：
```python
router = APIRouter(prefix="/api/v1/pipelines", tags=["extraction-pipeline"])

@router.post("")
async def create_pipeline(body: dict, engine: PipelineEngine = Depends(...)):
    ...

@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str, engine: PipelineEngine = Depends(...)):
    state = await engine.build_state(pipeline_id)
    return state.dict()

@router.post("/{pipeline_id}/transition")
async def transition(pipeline_id: str, body: dict, engine: PipelineEngine = Depends(...)):
    ...
```

## 8. 前端设计（`extraction-pipeline.html`）
基于现有 `monitoring.html` 风格，使用相同 CSS 变量和布局：

- 左侧管线列表（卡片式），显示标题、当前阶段、最后更新时间。
- 点击进入详情：展示阶段流转时间线、待办事项列表、操作按钮（推进/取消）。
- 使用 Fetch API 调用后端，自动刷新状态。
- 门禁失败时弹出具体原因。

关键交互：
```javascript
async function doTransition(pipelineId) {
  const res = await fetch(`/api/v1/pipelines/${pipelineId}/transition`, {method:'POST'});
  if (res.ok) {
    refreshDetail();
  } else {
    const err = await res.json();
    alert(err.detail);
  }
}
```

## 9. 实施步骤（面向开发工程师）

1. **创建数据模型**  
   - 编写 `pipeline_models.py`，定义枚举、事件、状态、门禁规则模型。

2. **实现事件存储**  
   - 编写 `pipeline_store.py`，使用 JSONL 文件实现事件的追加和加载。

3. **构建状态机引擎**  
   - 编写 `pipeline_engine.py`，实现状态重放、迁移接口、门禁评估。  
   - 集成 `review_service`（通过依赖注入），按 pipeline_id 查询复核数据。

4. **编写 REST API**  
   - 编写 `pipeline_routes.py`，实现所有端点，并接入 FastAPI 依赖注入。  
   - 在 `main.py` 中初始化 `PipelineEngine`，注册路由。

5. **编写自动化测试**  
   - `test_pipeline_engine.py`：验证状态迁移、门禁检查、事件溯源正确性。

6. **创建前端界面**  
   - `extraction-pipeline.html` + 配套 JS，提供管线列表、详情、迁移按钮。  
   - 添加导航链接。

7. **集成与验证**  
   - 启动应用，手动创建管线项目，测试四阶段流转和门禁失败场景。  
   - 确认待办项能够根据阶段正确展示。

## 10. 扩展性考虑
- 门禁规则可通过管理界面或配置文件动态调整，不影响代码。
- 事件存储可轻松切换为数据库（SQLite / PostgreSQL）只需实现相同接口。
- 未来可加入自动化流转（如定时任务检查门禁并自动推进）。

---

> 此方案已充分考虑与现有系统（agent 管理、复核服务、事件总线）的集成，提供可落地的开发蓝图。如有需要，可进一步交流每个模块的详细实现代码。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
