# 架构设计 — architect

任务: 前端实现技能萃取页面框架：时间轴组件展示操作日志节点，每个节点挂接补全卡片（含实时记录与回顾注释字段），基于WebSocket实时更新卡片状态，阶段步骤卡带进度锁
步骤: architecture
Agent: build_architect

---

📋 任务: 8be6b354-dda
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
  前端实现技能萃取页面框架：时间轴组件展示操作日志节点，每个节点挂接补全卡片（含实时记录与回顾注释字段），基于WebSocket实时更新卡片状态，阶段步骤卡带进度锁
  Developer
  
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
  ... (共 726 个 src/ 文件)
  
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
  
  ### 文件: `src/frontend/js/i18n.js`
  ```js
  /**
   * AgentsGroup2026 — i18n Internationalization Module v2
   * DOM text-walker approach: walks all text nodes and replaces Chinese↔English.
   * Usage: <script src="/js/i18n.js"></script>
   * Pages can extend via: PX_I18N.addTexts({ '中文': 'English', ... })
   */
  (function () {
    'use strict';
  
    const LANGS = ['zh', 'en'];
    const STORAGE_KEY = 'px-lang';
  
    /* ── Shared text map: zh → en ── */
    const TEXT_MAP = new Map([
      // ─── Index / Home page ───
      ['深海远洋双体船舶智能综合信息系统', 'Deep-Sea Ocean-Going Catamaran Intelligent Information System'],
      ['船长中控台', 'Captain Cockpit'],
      ['智能导航', 'Smart Navigation'],
      ['数据中心孪生', 'DC Digital Twin'],
      ['态势感知', 'Situation Awareness'],
      ['船岸通信', 'Ship-Shore Link'],
      ['气象海况', 'Weather & Sea'],
      ['海上作业', 'Offshore Operations'],
      ['进入系统', 'Enter System'],
  
      // ─── Page titles ───
      ['船长智能中控台', 'Captain Cockpit'],
      ['船长驾驶舱', 'Captain Cockpit'],
      ['导航与操纵', 'Navigation & Maneuvering'],
      ['动力定位', 'DP Control'],
      ['推进控制', 'Thruster Control'],
      ['全船监控', 'Full Ship Monitor'],
      ['设备健康', 'CMS Health'],
      ['控制台', 'HMI Console'],
      ['海工特种作业', 'Offshore Operations'],
      ['海工特種作业', 'Offshore Operations'],
      ['气象海洋', 'Weather & Ocean'],
      ['船员管理', 'Crew Management'],
      ['仿真训练', 'Simulation & Training'],
      ['能效合规', 'Energy Compliance'],
      ['船载数据中心', 'Marine Datacenter'],
      ['安全应急', 'Safety & Emergency'],
      ['船岸协同', 'Ship-Shore Sync'],
      ['数字孪生', 'Digital Twin'],
      ['智能体', 'AI Agents'],
      ['系统自我演进', 'System Self-Evolution'],
      ['系统演进', 'System Evolution'],
      ['知识库', 'Knowledge Base'],
      ['系统配置', 'System Configuration'],
      ['全球船舶监控平台', 'Global Ship Monitoring'],
      ['船舶避免碰撞增强现实系统', 'Ship Collision Avoidance AR System'],
  
      // ─── Nav sidebar ───
      ['船长总览', 'Captain'],
      ['导航', 'Navigation'],
      ['全船监控', 'Monitor'],
      ['海工作业', 'Offshore Ops'],
      ['船员管理', 'Crew Mgmt'],
  
      // ─── Common status / UI ───
      ['正常', 'Normal'],
      ['报警', 'Alarm'],
      ['警告', 'Warning'],
      ['离线', 'Offline'],
      ['在线', 'Online'],
      ['已连接', 'Connected'],
      ['待命', 'Standby'],
      ['就绪', 'Ready'],
      ['待确认', 'Pending'],
      ['已执行', 'Executed'],
      ['已确认', 'Confirmed'],
      ['已接收', 'Received'],
      ['已批准', 'Approved'],
      ['已提交', 'Submitted'],
      ['有效', 'Valid'],
      ['即将到期', 'Expiring Soon'],
      ['检修中', 'Under Maintenance'],
      ['加载中', 'Loading'],
      ['初始化中', 'Initializing'],
      ['搜索', 'Search'],
      ['保存', 'Save'],
      ['取消', 'Cancel'],
      ['确认', 'Confirm'],
      ['关闭', 'Close'],
      ['刷新', 'Refresh'],
      ['导出', 'Export'],
      ['状态', 'Status'],
      ['设置', 'Settings'],
      ['提交', 'Submit'],
      ['返回', 'Back'],
      ['折叠', 'Collapse'],
      ['全屏', 'Fullscreen'],
      ['隐藏', 'Hide'],
      ['开始', 'Start'],
      ['暂停', 'Pause'],
      ['重置', 'Reset'],
      ['清空', 'Clear'],
      ['添加', 'Add'],
      ['保存配置', 'Save Config'],
      ['刷新全部', 'Refresh All'],
  
      // ─── Captain cockpit ───
      ['快捷指令', 'Quick Commands'],
      ['拋錨', 'Drop Anchor'],
      ['抛锚', 'Drop Anchor'],
      ['响笛', 'Sound Horn'],
      ['紧急停车', 'Emergency Stop'],
      ['信号灯', 'Signal Light'],
      ['信号燈', 'Signal Light'],
      ['航行日志', 'Navigation Log'],
      ['航行日誌', 'Navigation Log'],
      ['系统设置', 'System Settings'],
      ['性能报告', 'Performance Report'],
      ['气象更新', 'Weather Update'],
      ['操作日志', 'Operation Log'],
      ['操作日誌', 'Operation Log'],
      ['操作人', 'Operator'],
      ['事件', 'Event'],
      ['结果', 'Result'],
      ['完成', 'Complete'],
      ['大副', 'Chief Officer'],
      ['轮机长', 'Chief Engineer'],
      ['船长', 'Captain'],
      ['调整航向', 'Adjust Heading'],
      ['主机转速', 'M/E RPM'],
      ['确认航线', 'Confirm Route'],
      ['您好', 'Hello'],
      ['当前航行状态如何', 'Current navigation status?'],
      ['当前航速', 'Current Speed'],
      ['航向', 'Heading'],
      ['主机功率', 'M/E Power'],
      ['子系统全部在线', 'All subsystems online'],
      ['抵达下一航路点', 'ETA next waypoint'],
      ['首页', 'Home'],
      ['中控台', 'Control Center'],
      ['广播', 'Broadcast'],
  
      // ─── Safety & Emergency ───
      ['消防区域矩阵', 'Fire Zone Matrix'],
      ['救生设备清单', 'Life Saving Equipment'],
      ['应急预案', 'Emergency Plans'],
      ['集合站点', 'Muster Stations'],
      ['正常区域', 'Normal Zones'],
      ['注意区域', 'Caution Zones'],
      ['报警区域', 'Alarm Zones'],
      ['救生设备', 'Life Saving Equip.'],
      ['预案就绪', 'Plans Ready'],
      ['设备', 'Equipment'],
      ['数量', 'Qty'],
      ['容量', 'Capacity'],
      ['检验日期', 'Inspection Date'],
      ['救生艇', 'Lifeboat'],
      ['救生筏', 'Life Raft'],
      ['救生圈', 'Life Buoy'],
      ['救生衣', 'Life Jacket'],
      ['发光', 'Illuminated'],
      ['烟雾', 'Smoke Signal'],
      ['火灾', 'Fire'],
      ['弃船', 'Abandon Ship'],
      ['人落水', 'Man Overboard'],
      ['碰撞', 'Collision'],
      ['搁浅', 'Grounding'],
      ['进水', 'Flooding'],
      ['污染', 'Pollution'],
      ['医疗', 'Medical'],
      ['机舱', 'Engine Room'],
      ['货舱', 'Cargo Hold'],
      ['住舱', 'Accommodation'],
      ['驾驶', 'Bridge'],
      ['甲板', 'Deck'],
      ['左舷甲板', 'Port Deck'],
      ['右舷甲板', 'Starboard Deck'],
      ['驾驶台', 'Bridge'],
      ['机舱控制室', 'Engine Control Room'],
      ['人已到', 'Arrived'],
  
      // ─── Ship-Shore ───
      ['通信链路', 'Communication Links'],
      ['数据同步', 'Data Sync'],
      ['岸基指令历史', 'Shore Command History'],
      ['远程数据流', 'Remote Data Flow'],
      ['上行', 'Uplink'],
      ['下行', 'Downlink'],
      ['延迟', 'Latency'],
      ['航行数据', 'Navigation Data'],
      ['实时', 'Real-time'],
      ['岸基', 'Shore'],
      ['云存储', 'Cloud Storage'],
      ['云存儲', 'Cloud Storage'],
      ['视频监控', 'Video Monitor'],
      ['視频监控', 'Video Monitor'],
      ['岸基指令', 'Shore Command'],
      ['船端', 'Ship-side'],
      ['时间', 'Time'],
      ['来源', 'Source'],
      ['指令', 'Command'],
      ['航速调整', 'Speed Adjustment'],
      ['进港航道确认', 'Port Channel Confirm'],
      ['台风预警转发', 'Typhoon Alert Forward'],
      ['优化建议下发', 'Optimization Advice'],
      ['沿海', 'Coastal'],
      ['双频', 'Dual Freq'],
  
      // ─── Simulation & Training ───
      ['综合评分', 'Overall Score'],
      ['綜合評分', 'Overall Score'],
      ['训练次数', 'Training Count'],
      ['本月', 'This Month'],
      ['累计时长', 'Total Duration'],
      ['船员排名', 'Crew Ranking'],
      ['场景配置', 'Scenario Config'],
      ['训练场景', 'Training Scenario'],
      ['故障注入', 'Fault Injection'],
      ['训练日志', 'Training Log'],
      ['训练日誌', 'Training Log'],
      ['能力评估雷达图', 'Competency Radar'],
      ['能力評估雷达图', 'Competency Radar'],
      ['成绩详情', 'Score Details'],
      ['成績详情', 'Score Details'],
      ['评分趋势', 'Score Trend'],
      ['評分趨勢', 'Score Trend'],
      ['避碰判断', 'Collision Avoidance'],
      ['导航精度', 'Navigation Accuracy'],
      ['通信规范', 'Communication Standards'],
      ['应急反应', 'Emergency Response'],
      ['操纵技能', 'Maneuvering Skills'],
      ['团队协作', 'Teamwork'],
      ['平均反应时间', 'Avg. Response Time'],
      ['天气', 'Weather'],
      ['海况', 'Sea State'],
      ['交通密度', 'Traffic Density'],
      ['能见度', 'Visibility'],
      ['模拟时间', 'Simulation Time'],
      ['主机故障', 'M/E Failure'],
      ['舵机故障', 'Rudder Lock'],
      ['雷达故障', 'Radar Fail'],
      ['通信中断', 'Comms Down'],
      ['电力丧失', 'Blackout'],
      ['优秀', 'Excellent'],
      ['合格', 'Pass'],
      ['失败', 'Fail'],
      ['晴朗', 'Clear'],
      ['多云', 'Cloudy'],
      ['暴雨', 'Storm'],
      ['台风', 'Typhoon'],
      ['轻浪', 'Slight'],
      ['大浪', 'Rough'],
      ['狂浪', 'Very Rough'],
      ['狂涛', 'High'],
      ['蒲氏风级', 'Beaufort Scale'],
      ['评价', 'Grade'],
      ['右舷让路避让', 'Starboard Give-way'],
      ['雷达标绘', 'Radar Plotting'],
      ['联络确认', 'Communication Confirm'],
      ['狭水道右舷通行', 'Narrow Channel Starboard'],
      ['应急舵切换', 'Emergency Steering Switch'],
      ['追越船避让', 'Overtaking Avoidance'],
      ['避碰', 'COLREG Avoidance'],
      ['分道通航', 'TSS'],
      ['港口进出', 'Port Entry/Exit'],
      ['应急操纵', 'Emergency Maneuvering'],
      ['锚泊作业', 'Anchoring Ops'],
  
      // ─── System Evolution ───
      ['达尔文棘轮', 'Darwin Ratchet'],
      ['自然选择', 'Natural Selection'],
      ['棘轮机制', 'Ratchet Mechanism'],
      ['演进时间线', 'Evolution Timeline'],
      ['初始化棘轮引擎中', 'Initializing Ratchet Engine'],
      ['演进流水线', 'Evolution Pipeline'],
      ['演进操作', 'Evolution Ops'],
      ['演进趋势', 'Evolution Trend'],
      ['域覆盖雷达', 'Domain Radar'],
      ['审查热力图', 'Audit Heatmap'],
      ['合规评级', 'Compliance Rating'],
      ['合规区域', 'Compliance Zones'],
      ['升级仪表板', 'Upgrade Dashboard'],
      ['双重检查单', 'Double Checklist'],
      ['公司级', 'Company Level'],
      ['船舶级', 'Vessel Level'],
      ['审计轨迹', 'Audit Trail'],
      ['审查规则库', 'Audit Rules'],
      ['演进条目', 'Evolution Entries'],
      ['审查历史', 'Audit History'],
      ['运行审查', 'Runtime Audit'],
      ['派发', 'Dispatch'],
      ['验证', 'Verify'],
      ['完整周期', 'Full Cycle'],
      ['已锁定的演化特性只增不减', 'Locked traits only grow, never regress'],
      ['永不回退', 'Never Rollback'],
      ['系统自我演进引擎就绪', 'Self-Evolution Engine Ready'],
      ['正在加载演进数据', 'Loading evolution data'],
      ['活跃', 'Active'],
  
      // ─── Thruster Control ───
      ['机舱综合状态', 'Engine Room Overview'],
      ['机舱綜合狀态', 'Engine Room Overview'],
      ['功率趋势', 'Power Trend'],
      ['功率趨勢', 'Power Trend'],
      ['振动频谱', 'Vibration Spectrum'],
      ['振动频譜', 'Vibration Spectrum'],
      ['缸温分布', 'Cylinder Temp Distribution'],
      ['缸溫分布', 'Cylinder Temp Distribution'],
      ['燃油流量', 'Fuel Flow'],
      ['能效指标', 'Efficiency Indicators'],
      ['额定', 'Rated'],
      ['负荷', 'Load'],
      ['燃油压力', 'Fuel Pressure'],
      ['排气温度', 'Exhaust Temp'],
      ['振动水平', 'Vibration Level'],
      ['舱底水位', 'Bilge Water Level'],
      ['推进效率', 'Propulsion Efficiency'],
      ['总运行时', 'Total Runtime'],
      ['下次保养', 'Next Maintenance'],
      ['高级控制', 'Advanced Control'],
      ['限值', 'Limit'],
      ['滑油温度', 'Lube Oil Temp'],
      ['冷却水温', 'Cooling Water Temp'],
      ['车钟', 'Telegraph'],
      ['车鐘', 'Telegraph'],
  
      // ─── Weather & Ocean ───
      ['风场', 'Wind Field'],
      ['風场', 'Wind Field'],
      ['海浪谱', 'Wave Spectrum'],
      ['海浪譜', 'Wave Spectrum'],
      ['海况综合', 'Sea Conditions'],
      ['海況綜合', 'Sea Conditions'],
      ['道格拉斯海况', 'Douglas Sea State'],
      ['蒲福风级', 'Beaufort Scale'],
      ['气温', 'Air Temp'],
      ['水温', 'Water Temp'],
      ['气压', 'Pressure'],
      ['湿度', 'Humidity'],
      ['洋流', 'Current'],
      ['涌浪', 'Swell'],
      ['表面流速', 'Surface Current Speed'],
      ['流向', 'Current Direction'],
      ['涌浪评估', 'Swell Assessment'],
      ['适航', 'Seaworthy'],
      ['潮汐', 'Tide'],
      ['当前潮高', 'Current Tide Height'],
      ['气象预警', 'Weather Warning'],
      ['大风蓝色预警', 'Blue Gale Warning'],
      ['天气窗口', 'Weather Window'],
      ['可作业', 'Operable'],
      ['航线天气评估', 'Route Weather Assessment'],
      ['良好', 'Good'],
      ['预报', 'Forecast'],
      ['方向', 'Direction'],
      ['风速', 'Wind Speed'],
      ['风向', 'Wind Dir'],
      ['浪高', 'Wave Height'],
  
      // ─── Offshore Operations ───
      ['作业状态', 'Operation Status'],
      ['作业狀态', 'Operation Status'],
      ['作业类型', 'Operation Type'],
      ['起重吊装', 'Crane Lifting'],
      ['许可状态', 'Permit Status'],
      ['許可狀态', 'Permit Status'],
      ['作业区域', 'Work Zone'],
      ['客户', 'Client'],
      ['起重机状态', 'Crane Status'],
      ['起重机狀态', 'Crane Status'],
      ['臂仰角', 'Boom Angle'],
      ['回转角', 'Slew Angle'],
      ['吃钩高度', 'Hook Height'],
      ['吃鉤高度', 'Hook Height'],
      ['环境条件', 'Environment Conditions'],
      ['环境條件', 'Environment Conditions'],
      ['作业限制', 'Op. Limits'],
      ['未超限', 'Within Limits'],
      ['安全检查单', 'Safety Checklist'],
      ['安全检查單', 'Safety Checklist'],
      ['系统状态确认', 'System Status Confirmed'],
      ['系统狀态确认', 'System Status Confirmed'],
      ['通信链路测试', 'Comms Link Test'],
      ['通信链路测試', 'Comms Link Test'],
      ['人员就位确认', 'Personnel Positioned'],
      ['气象窗口核实', 'Weather Window Verified'],
      ['应急预案就绪', 'Emergency Plan Ready'],
      ['应急预案就緒', 'Emergency Plan Ready'],
      ['吊具检验合格', 'Rigging Inspection Pass'],
      ['吊具检驗合格', 'Rigging Inspection Pass'],
      ['安全区域清场', 'Safety Zone Cleared'],
      ['平台东南侧', 'Platform SE Side'],
      ['平台東南側', 'Platform SE Side'],
  
      // ─── Crew Management ───
      ['总船员', 'Total Crew'],
      ['当值', 'On Watch'],
      ['休息', 'Off Watch'],
      ['疲劳预警', 'Fatigue Alert'],
      ['疲勞预警', 'Fatigue Alert'],
      ['证书到期', 'Certificate Expiring'],
      ['证書到期', 'Certificate Expiring'],
      ['船员花名册', 'Crew Roster'],
      ['船员花名冊', 'Crew Roster'],
      ['休息时间合规', 'Work/Rest Compliance'],
      ['休息时間合规', 'Work/Rest Compliance'],
      ['疲劳风险', 'Fatigue Risk'],
      ['疲勞風险', 'Fatigue Risk'],
      ['船舶评分', 'Vessel Score'],
      ['高风险人员', 'High Risk Personnel'],
      ['达标', 'Compliant'],
      ['证书监控', 'Certificate Monitor'],
      ['证書监控', 'Certificate Monitor'],
      ['应急演练记录', 'Emergency Drill Records'],
      ['值班安排', 'Watch Schedule'],
      ['当前班次', 'Current Watch'],
      ['甲班', 'Watch A'],
      ['下次换班', 'Next Changeover'],
      ['大管轮', 'Second Engineer'],
      ['水手长', 'Bosun'],
      ['机工', 'Motorman'],
  
      // ─── Energy Compliance ───
      ['当前', 'Current'],
      ['年度评级', 'Annual Rating'],
      ['年度轨迹', 'Annual Trajectory'],
      ['实时追踪', 'Real-time Tracking'],
      ['月度燃油消耗', 'Monthly Fuel Consumption'],
      ['排放监测', 'Emissions Monitoring'],
      ['二氧化碳', 'CO₂'],
      ['年度申报', 'Annual Declaration'],
      ['硫氧化物', 'SOx'],
      ['氮氧化物', 'NOx'],
      ['颗粒物', 'Particulate Matter'],
      ['合规文档', 'Compliance Documents'],
      ['文档名称', 'Document Name'],
      ['编号', 'Number'],
      ['有效期', 'Validity'],
      ['更新日期', 'Update Date'],
      ['审核机构', 'Audit Authority'],
      ['技术档案', 'Technical File'],
      ['改善方案', 'Improvement Plan'],
      ['国际能效证书', 'International Energy Cert.'],
      ['排放合规声明', 'Emission Compliance Decl.'],
      ['年报', 'Annual Report'],
      ['合规', 'Compliant'],
  
      // ─── Navigation ───
      ['电子海图', 'ECDIS'],
      ['航线路径点', 'Route Waypoints'],
      ['气象数据', 'Weather Data'],
      ['叠加层', 'Overlays'],
      ['目标', 'Targets'],
      ['雷达回波', 'Radar Echo'],
      ['安全等深线', 'Safety Contour'],
      ['追踪', 'Tracking'],
      ['航线进度', 'Route Progress'],
      ['航速', 'Speed'],
  
      // ─── Knowledge Base ───
      ['文档', 'Documents'],
      ['向量', 'Vectors'],
      ['领域', 'Domains'],
      ['領域', 'Domains'],
      ['全部', 'All'],
      ['法规', 'Regulations'],
      ['程序', 'Procedures'],
      ['技术', 'Technical'],
      ['培训', 'Training'],
      ['清单', 'Checklist'],
      ['清單', 'Checklist'],
      ['添加知识文档', 'Add Knowledge Document'],
      ['标题', 'Title'],
      ['标題', 'Title'],
      ['类别', 'Category'],
      ['类別', 'Category'],
      ['标签', 'Tags'],
      ['标籤', 'Tags'],
      ['逗号分隔', 'Comma separated'],
      ['内容', 'Content'],
      ['內容', 'Content'],
  
      // ─── Config page ───
      ['船舶信息', 'Ship Info'],
      ['船名', 'Ship Name'],
      ['船型', 'Ship Type'],
      ['穿浪双体船', 'Wave-Piercing Catamaran'],
      ['集装箱船', 'Container Ship'],
      ['散货船', 'Bulk Carrier'],
      ['油轮', 'Tanker'],
      ['总吨', 'Gross Tonnage'],
      ['功能开关', 'Feature Toggles'],
      ['决策辅助', 'Decision Aid'],
      ['決策輔助', 'Decision Aid'],
      ['启用', 'Enable'],
      ['自动避碰', 'Auto COLREG'],
      ['气象航线优化', 'Weather Route Optimization'],
      ['船员疲劳监控', 'Crew Fatigue Monitor'],
      ['船员疲勞监控', 'Crew Fatigue Monitor'],
      ['闭环审查', 'Closed-loop Audit'],
      ['构建', 'Build'],
      ['数据存储', 'Data Storage'],
      ['数据存儲', 'Data Storage'],
      ['访问控制', 'Access Control'],
      ['认证', 'Authentication'],
      ['端口控制', 'Port Control'],
      ['未授权', 'Unauthorized'],
      ['审查日志', 'Audit Log'],
      ['審查日誌', 'Audit Log'],
      ['记录所有系统配置变更', 'Log all config changes'],
      ['系统运行状态', 'System Runtime Status'],
      ['系统运行狀态', 'System Runtime Status'],
      ['运行时间', 'Uptime'],
      ['使用率', 'Usage'],
      ['内存使用', 'Memory Usage'],
      ['健康', 'Healt
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
                      self._p2_buffer.extend(p2_batch)
          else:
              logger.debug(f"📤 (无回调) 缓冲 {len(all_data)} 条追踪数据")
  
      async def flush(self) -> int:
          """手动触发刷新，返回刷新的记录数."""
          await self._flush_now()
          return len(self._buffer) + len(self._p2_buffer)
  
      def record_fingerprint_stability(self, stability_report: Dict[str, Any]) -> None:
          """记录指纹稳定性监控埋点.
  
          由 agents.fingerprint 模块在计算指纹后调用,
          将稳定性数据纳入监控体系。
  
          Args:
              stability_report: FingerprintEngine.get_stability_report() 的返回值
          """
          self._metrics.fingerprint_mutation_rate = stability_report.get(
              "mutation_rate", 0.0
          )
          self._metrics.fingerprint_is_stable = stability_report.get(
              "is_stable", True
          )
          self._metrics.fingerprint_total = stability_report.get(
              "total_fingerprints", 0
          )
  
          # 变异率超阈值时记录告警事件
          threshold = stability_report.get("alert_threshold", 0.05)
          mutation_rate = stability_report.get("mutation_rate", 0.0)
          if mutation_rate > threshold:
              logger.warning(
                  "⚠️ 指纹变异率 %.4f 超过阈值 %.4f (total=%d)",
                  mutation_rate, threshold,
                  stability_report.get("total_fingerprints", 0),
              )
              self._metrics.fingerprint_alert_count += 1
  
          logger.debug(
              "📊 指纹稳定性埋点: mutation_rate=%.4f stable=%s",
              mutation_rate, stability_report.get("is_stable"),
          )
  
      def get_telemetry_records(
          self, limit: int = 100, status_filter: Optional[str] = None
      ) -> List[Dict[str, Any]]:
          """获取遥测记录（用于 CI/CD 门禁校验）."""
          records = self._telemetry_records[-limit:]
          if status_filter:
              records = [r for r in records if r.status == status_filter]
          return [r.to_dict() for r in records]
  
      def get_metrics(self) -> Dict[str, Any]:
          """获取当前指标."""
          self._metrics.buffer_usage_pct = round(
              (len(self._buffer) + len(self._p2_buffer))
              / max(self._sampler.config.max_buffer_size, 1) * 100,
              2,
          )
          return self._metrics.to_dict()
  
      def get_sampler_stats(self) -> dict:
          """获取采样器统计."""
          return self._sampler.get_stats()
  
  ```
  
  ### 文件: `src/backend/monitoring/fingerprint_bypass.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  指纹遥测旁路 Channel — 非侵入式行为指纹异步采集.
  
  基于 MarineChannel 实现，在不干扰主业务流程的前提下:
  1. 定期快照 A/B 测试行为指纹 (突变率、升级异常等)
  2. 异步采集 Agent 执行日志中的指纹信号
  3. 将指纹数据推入 TraceCollector 供后续分析与面板展示
  4. 支持 ConfigMap 热更新采样策略
  
  设计原则:
  - 旁路 (bypass): 永不阻塞主业务，所有采集走 asyncio 后台任务
  - 采样优先: 正常模式下仅 P0 字段实时采集，P1/P2 降频
  - 降级全量: 异常检测触发时自动提升为全量采集
  """
  
  from __future__ import annotations
  
  import asyncio
  import logging
  import time
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from typing import Any, Dict, List, Optional
  from uuid import uuid4
  
  from channels.marine_base import (
      ChannelPriority,
      ChannelStatus,
      ChannelEvent,
      MarineChannel,
  )
  
  from .models import (
      MonitoringMetrics,
      SamplingConfig,
      SamplingDecision,
      SpanPriority,
      TraceContext,
      TraceSpan,
  )
  
  logger = logging.getLogger(__name__)
  
  
  # ── Fingerprint Data Models ──────────────────────────────────────────────
  
  
  @dataclass
  class BehaviorFingerprint:
      """Agent 行为指纹快照 — 从 A/B 测试指标中提取的关键信号."""
  
      fingerprint_id: str = ""
      agent_id: str = ""
      team_id: str = ""
      trace_id: str = ""
  
      # 核心指纹字段 (P0 — 实时必采)
      false_upgrade_rate: float = 0.0
      behavior_fingerprint_mutation_rate: float = 0.0
      anomaly_propagation_depth: float = 0.0
      prediction_error_rate: float = 0.0
  
      # 扩展指纹字段 (P1 — 条件采样)
      resource_increase_pct: float = 0.0
      energy_increase_pct: float = 0.0
      policy_evaluation_latency_ms: float = 0.0
      evolution_stagnation_rate: float = 0.0
  
      # 衍生指纹 (P2 — 离线批量)
      temperature_slope: float = 0.0
      anomaly_score: float = 0.0
      ewma_threshold_breach: bool = False
  
      # 元数据
      collected_at: str = ""
      source: str = "fingerprint_bypass"
      extra: Dict[str, Any] = field(default_factory=dict)
  
      def __post_init__(self) -> None:
          if not self.fingerprint_id:
              self.fingerprint_id = str(uuid4())[:8]
          if not self.collected_at:
              self.collected_at = datetime.now(timezone.utc).isoformat()
  
      def to_metrics(self) -> MonitoringMetrics:
          """转换为 MonitoringMetrics 供 TraceCollector 消费."""
          return MonitoringMetrics(
              span_id=self.fingerprint_id,
              trace_id=self.trace_id,
              span_name="behavior_fingerprint",
              false_upgrade_rate=self.false_upgrade_rate,
              resource_increase_pct=self.resource_increase_pct,
              behavior_fingerprint_mutation_rate=self.behavior_fingerprint_mutation_rate,
              anomaly_propagation_depth=self.anomaly_propagation_depth,
              prediction_error_rate=self.prediction_error_rate,
              energy_increase_pct=self.energy_increase_pct,
              temperature_slope=self.temperature_slope,
              policy_evaluation_latency_ms=self.policy_evaluation_latency_ms,
              evolution_stagnation_rate=self.evolution_stagnation_rate,
              anomaly_score=self.anomaly_score,
          )
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "fingerprint_id": self.fingerprint_id,
              "agent_id": self.agent_id,
              "team_id": self.team_id,
              "trace_id": self.trace_id,
              "false_upgrade_rate": self.false_upgrade_rate,
              "behavior_fingerprint_mutation_rate": self.behavior_fingerprint_mutation_rate,
              "anomaly_propagation_depth": self.anomaly_propagation_depth,
              "prediction_error_rate": self.prediction_error_rate,
              "resource_increase_pct": self.resource_increase_pct,
              "energy_increase_pct": self.energy_increase_pct,
              "policy_evaluation_latency_ms": self.policy_evaluation_latency_ms,
              "evolution_stagnation_rate": self.evolution_stagnation_rate,
              "temperature_slope": self.temperature_slope,
              "anomaly_score": self.anomaly_score,
              "ewma_threshold_breach": self.ewma_threshold_breach,
              "collected_at": self.collected_at,
              "source": self.source,
              "extra": self.extra,
          }
  
  
  @dataclass
  class FingerprintBuffer:
      """指纹遥测本地缓冲 — 环形队列，避免内存无限增长."""
  
      max_size: int = 1000
      fingerprints: List[BehaviorFingerprint] = field(default_factory=list)
      _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
  
      async def push(self, fp: BehaviorFingerprint) -> None:
          async with self._lock:
              self.fingerprints.append(fp)
              if len(self.fingerprints) > self.max_size:
                  self.fingerprints = self.fingerprints[-self.max_size:]
  
      async def drain(self, limit: int = 100) -> List[BehaviorFingerprint]:
          """取出并清空缓冲中的指纹."""
          async with self._lock:
              drained = self.fingerprints[:limit]
              self.fingerprints = self.fingerprints[limit:]
              return drained
  
      async def snapshot(self) -> List[BehaviorFingerprint]:
          """获取当前快照 (不清空)."""
          async with self._lock:
              return list(self.fingerprints)
  
      @property
      async def size(self) -> int:
          async with self._lock:
              return len(self.fingerprints)
  
  
  # ── Fingerprint Telemetry Bypass Channel ──────────────────────────────────
  
  
  class FingerprintTelemetryChannel(MarineChannel):
      """指纹遥测旁路 Channel — 非侵入式行为指纹采集.
  
      继承 MarineChannel，实现 process_event / get_status。
      不做任何阻塞主业务的操作，所有采集走 asyncio 后台循环。
      """
  
      channel_name: str = "fingerprint_telemetry"
      priority: ChannelPriority = ChannelPriority.P1
  
      def __init__(self, sampling_config: Optional[SamplingConfig] = None):
          super().__init__(name=self.channel_name, priority=self.priority)
          self._buffer = FingerprintBuffer()
          self._sampling_config = sampling_config or SamplingConfig()
          self._collect_task: Optional[asyncio.Task] = None
          self._snapshot_interval: float = 5.0  # 快照间隔 (秒)
          self._last_snapshot_time: float = 0.0
          self._fingerprints_collected: int = 0
          self._fingerprints_dropped: int = 0
          self._anomaly_detected: bool = False
  
      # ── MarineChannel 接口 ──────────────────────────────────────────────
  
      def initialize(self) -> None:
          """初始化 Channel，启动后台采集循环."""
          self.status = ChannelStatus.OK
          self._collect_task = asyncio.ensure_future(self._collection_loop())
          logger.info("🔍 FingerprintTelemetryChannel initialized — bypass mode active")
  
      async def process_event(self, event: ChannelEvent) -> bool:
          """处理遥测事件 — 从主业务旁路接收指纹信号.
  
          事件类型:
          - agent_loop_iteration: Agent 循环迭代事件 (携带 A/B 指标)
          - plaza_discussion_turn: 广场讨论轮次事件
          - ewma_breach: EWMA 阈值突破事件 (触发降级全量)
          - handoff_executed: Agent 交接事件
          """
          try:
              if event.event_type == "ewma_breach":
                  self._anomaly_detected = True
                  logger.warning("⚠️ EWMA breach detected — enabling full fingerprint collection")
  
              elif event.event_type == "agent_loop_iteration":
                  await self._collect_from_agent_loop(event)
  
              elif event.event_type in ("plaza_discussion_turn", "handoff_executed"):
                  await self._collect_from_collaboration(event)
  
              elif event.event_type == "reset_anomaly":
                  self._anomaly_detected = False
                  logger.info("✅ Anomaly cleared — resuming normal fingerprint sampling")
  
              return True
          except Exception as e:
              logger.error(f"FingerprintTelemetryChannel process_event error: {e}", exc_info=True)
              return False
  
      def get_status(self) -> Dict[str, Any]:
          """返回 Channel 运行状态."""
          return {
              "channel": self.channel_name,
              "status": self.status.value,
              "priority": self.priority.value,
              "fingerprints_collected": self._fingerprints_collected,
              "fingerprints_dropped": self._fingerprints_dropped,
              "buffer_size": len(self._buffer.fingerprints),
              "anomaly_detected": self._anomaly_detected,
              "snapshot_interval_s": self._snapshot_interval,
              "sampling_config": {
                  "p0_rate": self._sampling_config.p0_sample_rate,
                  "p1_rate": self._sampling_config.p1_sample_rate,
                  "p2_rate": self._sampling_config.p2_sample_rate,
                  "degradation_mode": self._sampling_config.degradation_mode,
              },
          }
  
      async def shutdown(self) -> None:
          """优雅关闭 — 取消后台任务."""
          if self._collect_task:
              self._collect_task.cancel()
              try:
                  await self._collect_task
              except asyncio.CancelledError:
                  pass
          self.status = ChannelStatus.OFF
          logger.info("FingerprintTelemetryChannel shutdown complete")
  
      # ── 采集逻辑 ───────────────────────────────────────────────────────
  
      async def _collection_loop(self) -> None:
          """后台采集循环 — 定期快照 + 异步上报."""
          while self.status != ChannelStatus.OFF:
              try:
                  await asyncio.sleep(self._snapshot_interval)
                  if self.status == ChannelStatus.OFF:
                      break
                  await self._periodic_snapshot()
              except asyncio.CancelledError:
                  break
              except Exception as e:
                  logger.error(f"Fingerprint collection loop error: {e}", exc_info=True)
                  await asyncio.sleep(1.0)
  
      async def _periodic_snapshot(self) -> None:
          """定期快照: 将缓冲中的指纹推入 TraceCollector."""
          try:
              from .collector import TraceCollector, get_collector
              collector = get_collector()
          except Exception:
              logger.debug("TraceCollector not available, skipping snapshot")
              return
  
          fps = await self._buffer.drain(limit=50)
          for fp in fps:
              try:
                  trace_ctx = TraceContext(
                      trace_id=fp.trace_id or str(uuid4()),
                      parent_span_id="",
                      span_id=fp.fingerprint_id,
                  )
                  span = TraceSpan(
                      span_id=fp.fingerprint_id,
                      trace_id=trace_ctx.trace_id,
                      parent_span_id="",
                      span_name="behavior_fingerprint",
                      priority=SpanPriority.P0 if self._anomaly_detected else SpanPriority.P1,
                      metrics=fp.to_metrics(),
                      tags={
                          "agent_id": fp.agent_id,
                          "team_id": fp.team_id,
                          "source": fp.source,
                          "bypass": "true",
                      },
                  )
                  collector.ingest(span)
              except Exception as e:
                  logger.debug(f"Failed to push fingerprint to collector: {e}")
  
      async def _collect_from_agent_loop(self, event: ChannelEvent) -> None:
          """从 Agent 循环迭代事件中提取指纹."""
          data = event.data or {}
          fp = BehaviorFingerprint(
              agent_id=data.get("agent_id", ""),
              team_id=data.get("team_id", ""),
              trace_id=data.get("trace_id", ""),
              false_upgrade_rate=data.get("false_upgrade_rate", 0.0),
              behavior_fingerprint_mutation_rate=data.get("behavior_fingerprint_mutation_rate", 0.0),
              anomaly_propagation_depth=data.get("anomaly_propagation_depth", 0.0),
              prediction_error_rate=data.get("prediction_error_rate", 0.0),
              resource_increase_pct=data.get("resource_increase_pct", 0.0),
              energy_increase_pct=data.get("energy_increase_pct", 0.0),
              policy_evaluation_latency_ms=data.get("policy_evaluation_latency_ms", 0.0),
              evolution_stagnation_rate=data.get("evolution_stagnation_rate", 0.0),
              temperature_slope=data.get("temperature_slope", 0.0),
              anomaly_score=data.get("anomaly_score", 0.0),
              ewma_threshold_breach=data.get("ewma_threshold_breach", False),
              extra=data.get("extra", {}),
          )
          await self._buffer.push(fp)
          self._fingerprints_collected += 1
  
      async def _collect_from_collaboration(self, event: ChannelEvent) -> None:
          """从协作事件 (Plaza / Handoff) 中提取指纹."""
          data = event.data or {}
          fp = BehaviorFingerprint(
              agent_id=data.get("agent_id", ""),
              team_id=data.get("team_id", ""),
              trace_id=data.get("trace_id", ""),
              behavior_fingerprint_mutation_rate=data.get("mutation_rate", 0.0),
              anomaly_propagation_depth=data.get("propagation_depth", 0.0),
              prediction_error_rate=data.get("error_rate", 0.0),
              extra={
                  "event_type": event.event_type,
                  "discussion_id": data.get("discussion_id", ""),
                  "plaza_id": data.get("plaza_id", ""),
              },
          )
          await self._buffer.pus
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 前端实现技能萃取页面框架：时间轴组件展示操作日志节点，每个节点挂接补全卡片（含实时记录与回顾注释字段），基于WebSocket实时更新卡片状态，阶段步骤卡带进度锁
  步骤: pm_decompose
  📋 任务: 8be6b354-dda
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  前端实现技能萃取页面框架：时间轴组件展示操作日志节点，每个节点挂接补全卡片（含实时记录与回顾注释字段），基于WebSocket实时更新卡片状态，阶段步骤卡带进度锁
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/frontend/monitoring.html`
  ### 文件: `src/frontend/js/i18n.js`
  ### 文件: `src/backend/monitoring/__init__.py`
  **子任务拆解:**
    - *目标**：在现有 `src/frontend/skill-extract.html` 基础上，实现一个**技能萃取过程可视化页面**，使用时间轴展示操作日志节点，每个节点支持展开/挂接补全卡片（含实时记录与回顾注释字段），通过 WebSocket 实时更新卡片状态，并包含阶段步骤卡（带进度锁机制）。所有交互均需保持与现有页面风格一致（暗色主题，原生 HTML+JS，无重框架）。
    - 后端已有技能萃取相关模块（`agents/skill_extractor.py`、`skill_store.py` 等），可提供操作日志数据和 WebSocket 推送。
    - 前端已有 `monitoring.html` 中类似的实时刷新机制（轮询），但需升级为 WebSocket 以获得更低延迟的状态同步。
    - 当前 `skill-extract.html` 可能是占位页，需从零搭建框架。
    - 前端技术栈：HTML5 + CSS3 + 原生 JavaScript（ES6+），无构建工具。
    - 使用原生 `WebSocket` API 与后端通信。
    - 时间轴、卡片等组件采用自定义 DOM 操作，不引入第三方组件库。
    - 国际化的字符串需同步到 `js/i18n.js`。
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 前端实现技能萃取页面框架：时间轴组件展示操作日志节点，每个节点挂接补全卡片（含实时记录与回顾注释字段），基于WebSocket实时更新卡片状态，阶段步骤卡带进度锁
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: 8be6b354-dda
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
    前端实现技能萃取页面框架：时间轴组件展示操作日志节点，每个节点挂接补全卡片（含实时记录与回顾注释字段），基于WebSocket实时更新卡片状态，阶段步骤卡带进度锁
    Developer
    
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
    ... (共 726 个 src/ 文件)
    
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
    
    ### 文件: `src/frontend/js/i18n.js`
    ```js
    /**
     * AgentsGroup2026 — i18n Internationalization Module v2
     * DOM text-walker approach: walks all text nodes and replaces Chinese↔English.
     * Usage: <script src="/js/i18n.js"></script>
     * Pages can extend via: PX_I18N.addTexts({ '中文': 'English', ... })
     */
    (function () {
      'use strict';
    
      const LANGS = ['zh', 'en'];
      const STORAGE_KEY = 'px-lang';
    
      /* ── Shared text map: zh → en ── */
      const TEXT_MAP = new Map([
        // ─── Index / Home page ───
        ['深海远洋双体船舶智能综合信息系统', 'Deep-Sea Ocean-Going Catamaran Intelligent Information System'],
        ['船长中控台', 'Captain Cockpit'],
        ['智能导航', 'Smart Navigation'],
        ['数据中心孪生', 'DC Digital Twin'],
        ['态势感知', 'Situation Awareness'],
        ['船岸通信', 'Ship-Shore Link'],
        ['气象海况', 'Weather & Sea'],
        ['海上作业', 'Offshore Operations'],
        ['进入系统', 'Enter System'],
    
        // ─── Page titles ───
        ['船长智能中控台', 'Captain Cockpit'],
        ['船长驾驶舱', 'Captain Cockpit'],
        ['导航与操纵', 'Navigation & Maneuvering'],
        ['动力定位', 'DP Control'],
        ['推进控制', 'Thruster Control'],
        ['全船监控', 'Full Ship Monitor'],
        ['设备健康', 'CMS Health'],
        ['控制台', 'HMI Console'],
        ['海工特种作业', 'Offshore Operations'],
        ['海工特種作业', 'Offshore Operations'],
        ['气象海洋', 'Weather & Ocean'],
        ['船员管理', 'Crew Management'],
        ['仿真训练', 'Simulation & Training'],
        ['能效合规', 'Energy Compliance'],
        ['船载数据中心', 'Marine Datacenter'],
        ['安全应急', 'Safety & Emergency'],
        ['船岸协同', 'Ship-Shore Sync'],
        ['数字孪生', 'Digital Twin'],
        ['智能体', 'AI Agents'],
        ['系统自我演进', 'System Self-Evolution'],
        ['系统演进', 'System Evolution'],
        ['知识库', 'Knowledge Base'],
        ['系统配置', 'System Configuration'],
        ['全球船舶监控平台', 'Global Ship Monitoring'],
        ['船舶避免碰撞增强现实系统', 'Ship Collision Avoidance AR System'],
    
        // ─── Nav sidebar ───
        ['船长总览', 'Captain'],
        ['导航', 'Navigation'],
        ['全船监控', 'Monitor'],
        ['海工作业', 'Offshore Ops'],
        ['船员管理', 'Crew Mgmt'],
    
        // ─── Common status / UI ───
        ['正常', 'Normal'],
        ['报警', 'Alarm'],
        ['警告', 'Warning'],
        ['离线', 'Offline'],
        ['在线', 'Online'],
        ['已连接', 'Connected'],
        ['待命', 'Standby'],
        ['就绪', 'Ready'],
        ['待确认', 'Pending'],
        ['已执行', 'Executed'],
        ['已确认', 'Confirmed'],
        ['已接收', 'Received'],
        ['已批准', 'Approved'],
        ['已提交', 'Submitted'],
        ['有效', 'Valid'],
        ['即将到期', 'Expiring Soon'],
        ['检修中', 'Under Maintenance'],
        ['加载中', 'Loading'],
        ['初始化中', 'Initializing'],
        ['搜索', 'Search'],
        ['保存', 'Save'],
        ['取消', 'Cancel'],
        ['确认', 'Confirm'],
        ['关闭', 'Close'],
        ['刷新', 'Refresh'],
        ['导出', 'Export'],
        ['状态', 'Status'],
        ['设置', 'Settings'],
        ['提交', 'Submit'],
        ['返回', 'Back'],
        ['折叠', 'Collapse'],
        ['全屏', 'Fullscreen'],
        ['隐藏', 'Hide'],
        ['开始', 'Start'],
        ['暂停', 'Pause'],
        ['重置', 'Reset'],
        ['清空', 'Clear'],
        ['添加', 'Add'],
        ['保存配置', 'Save Config'],
        ['刷新全部', 'Refresh All'],
    
        // ─── Captain cockpit ───
        ['快捷指令', 'Quick Commands'],
        ['拋錨', 'Drop Anchor'],
        ['抛锚', 'Drop Anchor'],
        ['响笛', 'Sound Horn'],
        ['紧急停车', 'Emergency Stop'],
        ['信号灯', 'Signal Light'],
        ['信号燈', 'Signal Light'],
        ['航行日志', 'Navigation Log'],
        ['航行日誌', 'Navigation Log'],
        ['系统设置', 'System Settings'],
        ['性能报告', 'Performance Report'],
        ['气象更新', 'Weather Update'],
        ['操作日志', 'Operation Log'],
        ['操作日誌', 'Operation Log'],
        ['操作人', 'Operator'],
        ['事件', 'Event'],
        ['结果', 'Result'],
        ['完成', 'Complete'],
        ['大副', 'Chief Officer'],
        ['轮机长', 'Chief Engineer'],
        ['船长', 'Captain'],
        ['调整航向', 'Adjust Heading'],
        ['主机转速', 'M/E RPM'],
        ['确认航线', 'Confirm Route'],
        ['您好', 'Hello'],
        ['当前航行状态如何', 'Current navigation status?'],
        ['当前航速', 'Current Speed'],
        ['航向', 'Heading'],
        ['主机功率', 'M/E Power'],
        ['子系统全部在线', 'All subsystems online'],
        ['抵达下一航路点', 'ETA next waypoint'],
        ['首页', 'Home'],
        ['中控台', 'Control Center'],
        ['广播', 'Broadcast'],
    
        // ─── Safety & Emergency ───
        ['消防区域矩阵', 'Fire Zone Matrix'],
        ['救生设备清单', 'Life Saving Equipment'],
        ['应急预案', 'Emergency Plans'],
        ['集合站点', 'Muster Stations'],
        ['正常区域', 'Normal Zones'],
        ['注意区域', 'Caution Zones'],
        ['报警区域', 'Alarm Zones'],
        ['救生设备', 'Life Saving Equip.'],
        ['预案就绪', 'Plans Ready'],
        ['设备', 'Equipment'],
        ['数量', 'Qty'],
        ['容量', 'Capacity'],
        ['检验日期', 'Inspection Date'],
        ['救生艇', 'Lifeboat'],
        ['救生筏', 'Life Raft'],
        ['救生圈', 'Life Buoy'],
        ['救生衣', 'Life Jacket'],
        ['发光', 'Illuminated'],
        ['烟雾', 'Smoke Signal'],
        ['火灾', 'Fire'],
        ['弃船', 'Abandon Ship'],
        ['人落水', 'Man Overboard'],
        ['碰撞', 'Collision'],
        ['搁浅', 'Grounding'],
        ['进水', 'Flooding'],
        ['污染', 'Pollution'],
        ['医疗', 'Medical'],
        ['机舱', 'Engine Room'],
        ['货舱', 'Cargo Hold'],
        ['住舱', 'Accommodation'],
        ['驾驶', 'Bridge'],
        ['甲板', 'Deck'],
        ['左舷甲板', 'Port Deck'],
        ['右舷甲板', 'Starboard Deck'],
        ['驾驶台', 'Bridge'],
        ['机舱控制室', 'Engine Control Room'],
        ['人已到', 'Arrived'],
    
        // ─── Ship-Shore ───
        ['通信链路', 'Communication Links'],
        ['数据同步', 'Data Sync'],
        ['岸基指令历史', 'Shore Command History'],
        ['远程数据流', 'Remote Data Flow'],
        ['上行', 'Uplink'],
        ['下行', 'Downlink'],
        ['延迟', 'Latency'],
        ['航行数据', 'Navigation Data'],
        ['实时', 'Real-time'],
        ['岸基', 'Shore'],
        ['云存储', 'Cloud Storage'],
        ['云存儲', 'Cloud Storage'],
        ['视频监控', 'Video Monitor'],
        ['視频监控', 'Video Monitor'],
        ['岸基指令', 'Shore Command'],
        ['船端', 'Ship-side'],
        ['时间', 'Time'],
        ['来源', 'Source'],
        ['指令', 'Command'],
        ['航速调整', 'Speed Adjustment'],
        ['进港航道确认', 'Port Channel Confirm'],
        ['台风预警转发', 'Typhoon Alert Forward'],
        ['优化建议下发', 'Optimization Advice'],
        ['沿海', 'Coastal'],
        ['双频', 'Dual Freq'],
    
        // ─── Simulation & Training ───
        ['综合评分', 'Overall Score'],
        ['綜合評分', 'Overall Score'],
        ['训练次数', 'Training Count'],
        ['本月', 'This Month'],
        ['累计时长', 'Total Duration'],
        ['船员排名', 'Crew Ranking'],
        ['场景配置', 'Scenario Config'],
        ['训练场景', 'Training Scenario'],
        ['故障注入', 'Fault Injection'],
        ['训练日志', 'Training Log'],
        ['训练日誌', 'Training Log'],
        ['能力评估雷达图', 'Competency Radar'],
        ['能力評估雷达图', 'Competency Radar'],
        ['成绩详情', 'Score Details'],
        ['成績详情', 'Score Details'],
        ['评分趋势', 'Score Trend'],
        ['評分趨勢', 'Score Trend'],
        ['避碰判断', 'Collision Avoidance'],
        ['导航精度', 'Navigation Accuracy'],
        ['通信规范', 'Communication Standards'],
        ['应急反应', 'Emergency Response'],
        ['操纵技能', 'Maneuvering Skills'],
        ['团队协作', 'Teamwork'],
        ['平均反应时间', 'Avg. Response Time'],
        ['天气', 'Weather'],
        ['海况', 'Sea State'],
        ['交通密度', 'Traffic Density'],
        ['能见度', 'Visibility'],
        ['模拟时间', 'Simulation Time'],
        ['主机故障', 'M/E Failure'],
        ['舵机故障', 'Rudder Lock'],
        ['雷达故障', 'Radar Fail'],
        ['通信中断', 'Comms Down'],
        ['电力丧失', 'Blackout'],
        ['优秀', 'Excellent'],
        ['合格', 'Pass'],
        ['失败', 'Fail'],
        ['晴朗', 'Clear'],
        ['多云', 'Cloudy'],
        ['暴雨', 'Storm'],
        ['台风', 'Typhoon'],
        ['轻浪', 'Slight'],
        ['大浪', 'Rough'],
        ['狂浪', 'Very Rough'],
        ['狂涛', 'High'],
        ['蒲氏风级', 'Beaufort Scale'],
        ['评价', 'Grade'],
        ['右舷让路避让', 'Starboard Give-way'],
        ['雷达标绘', 'Radar Plotting'],
        ['联络确认', 'Communication Confirm'],
        ['狭水道右舷通行', 'Narrow Channel Starboard'],
        ['应急舵切换', 'Emergency Steering Switch'],
        ['追越船避让', 'Overtaking Avoidance'],
        ['避碰', 'COLREG Avoidance'],
        ['分道通航', 'TSS'],
        ['港口进出', 'Port Entry/Exit'],
        ['应急操纵', 'Emergency Maneuvering'],
        ['锚泊作业', 'Anchoring Ops'],
    
        // ─── System Evolution ───
        ['达尔文棘轮', 'Darwin Ratchet'],
        ['自然选择', 'Natural Selection'],
        ['棘轮机制', 'Ratchet Mechanism'],
        ['演进时间线', 'Evolution Timeline'],
        ['初始化棘轮引擎中', 'Initializing Ratchet Engine'],
        ['演进流水线', 'Evolution Pipeline'],
        ['演进操作', 'Evolution Ops'],
        ['演进趋势', 'Evolution Trend'],
        ['域覆盖雷达', 'Domain Radar'],
        ['审查热力图', 'Audit Heatmap'],
        ['合规评级', 'Compliance Rating'],
        ['合规区域', 'Compliance Zones'],
        ['升级仪表板', 'Upgrade Dashboard'],
        ['双重检查单', 'Double Checklist'],
        ['公司级', 'Company Level'],
        ['船舶级', 'Vessel Level'],
        ['审计轨迹', 'Audit Trail'],
        ['审查规则库', 'Audit Rules'],
        ['演进条目', 'Evolution Entries'],
        ['审查历史', 'Audit History'],
        ['运行审查', 'Runtime Audit'],
        ['派发', 'Dispatch'],
        ['验证', 'Verify'],
        ['完整周期', 'Full Cycle'],
        ['已锁定的演化特性只增不减', 'Locked traits only grow, never regress'],
        ['永不回退', 'Never Rollback'],
        ['系统自我演进引擎就绪', 'Self-Evolution Engine Ready'],
        ['正在加载演进数据', 'Loading evolution data'],
        ['活跃', 'Active'],
    
        // ─── Thruster Control ───
        ['机舱综合状态', 'Engine Room Overview'],
        ['机舱綜合狀态', 'Engine Room Overview'],
        ['功率趋势', 'Power Trend'],
        ['功率趨勢', 'Power Trend'],
        ['振动频谱', 'Vibration Spectrum'],
        ['振动频譜', 'Vibration Spectrum'],
        ['缸温分布', 'Cylinder Temp Distribution'],
        ['缸溫分布', 'Cylinder Temp Distribution'],
        ['燃油流量', 'Fuel Flow'],
        ['能效指标', 'Efficiency Indicators'],
        ['额定', 'Rated'],
        ['负荷', 'Load'],
        ['燃油压力', 'Fuel Pressure'],
        ['排气温度', 'Exhaust Temp'],
        ['振动水平', 'Vibration Level'],
        ['舱底水位', 'Bilge Water Level'],
        ['推进效率', 'Propulsion Efficiency'],
        ['总运行时', 'Total Runtime'],
        ['下次保养', 'Next Maintenance'],
        ['高级控制', 'Advanced Control'],
        ['限值', 'Limit'],
        ['滑油温度', 'Lube Oil Temp'],
        ['冷却水温', 'Cooling Water Temp'],
        ['车钟', 'Telegraph'],
        ['车鐘', 'Telegraph'],
    
        // ─── Weather & Ocean ───
        ['风场', 'Wind Field'],
        ['風场', 'Wind Field'],
        ['海浪谱', 'Wave Spectrum'],
        ['海浪譜', 'Wave Spectrum'],
        ['海况综合', 'Sea Conditions'],
        ['海況綜合', 'Sea Conditions'],
        ['道格拉斯海况', 'Douglas Sea State'],
        ['蒲福风级', 'Beaufort Scale'],
        ['气温', 'Air Temp'],
        ['水温', 'Water Temp'],
        ['气压', 'Pressure'],
        ['湿度', 'Humidity'],
        ['洋流', 'Current'],
        ['涌浪', 'Swell'],
        ['表面流速', 'Surface Current Speed'],
        ['流向', 'Current Direction'],
        ['涌浪评估', 'Swell Assessment'],
        ['适航', 'Seaworthy'],
        ['潮汐', 'Tide'],
        ['当前潮高', 'Current Tide Height'],
        ['气象预警', 'Weather Warning'],
        ['大风蓝色预警', 'Blue Gale Warning'],
        ['天气窗口', 'Weather Window'],
        ['可作业', 'Operable'],
        ['航线天气评估', 'Route Weather Assessment'],
        ['良好', 'Good'],
        ['预报', 'Forecast'],
        ['方向', 'Direction'],
        ['风速', 'Wind Speed'],
        ['风向', 'Wind Dir'],
        ['浪高', 'Wave Height'],
    
        // ─── Offshore Operations ───
        ['作业状态', 'Operation Status'],
        ['作业狀态', 'Operation Status'],
        ['作业类型', 'Operation Type'],
        ['起重吊装', 'Crane Lifting'],
        ['许可状态', 'Permit Status'],
        ['許可狀态', 'Permit Status'],
        ['作业区域', 'Work Zone'],
        ['客户', 'Client'],
        ['起重机状态', 'Crane Status'],
        ['起重机狀态', 'Crane Status'],
        ['臂仰角', 'Boom Angle'],
        ['回转角', 'Slew Angle'],
        ['吃钩高度', 'Hook Height'],
        ['吃鉤高度', 'Hook Height'],
        ['环境条件', 'Environment Conditions'],
        ['环境條件', 'Environment Conditions'],
        ['作业限制', 'Op. Limits'],
        ['未超限', 'Within Limits'],
        ['安全检查单', 'Safety Checklist'],
        ['安全检查單', 'Safety Checklist'],
        ['系统状态确认', 'System Status Confirmed'],
        ['系统狀态确认', 'System Status Confirmed'],
        ['通信链路测试', 'Comms Link Test'],
        ['通信链路测試', 'Comms Link Test'],
        ['人员就位确认', 'Personnel Positioned'],
        ['气象窗口核实', 'Weather Window Verified'],
        ['应急预案就绪', 'Emergency Plan Ready'],
        ['应急预案就緒', 'Emergency Plan Ready'],
        ['吊具检验合格', 'Rigging Inspection Pass'],
        ['吊具检驗合格', 'Rigging Inspection Pass'],
        ['安全区域清场', 'Safety Zone Cleared'],
        ['平台东南侧', 'Platform SE Side'],
        ['平台東南側', 'Platform SE Side'],
    
        // ─── Crew Management ───
        ['总船员', 'Total Crew'],
        ['当值', 'On Watch'],
        ['休息', 'Off Watch'],
        ['疲劳预警', 'Fatigue Alert'],
        ['疲勞预警', 'Fatigue Alert'],
        ['证书到期', 'Certificate Expiring'],
        ['证書到期', 'Certificate Expiring'],
        ['船员花名册', 'Crew Roster'],
        ['船员花名冊', 'Crew Roster'],
        ['休息时间合规', 'Work/Rest Compliance'],
        ['休息时間合规', 'Work/Rest Compliance'],
        ['疲劳风险', 'Fatigue Risk'],
        ['疲勞風险', 'Fatigue Risk'],
        ['船舶评分', 'Vessel Score'],
        ['高风险人员', 'High Risk Personnel'],
        ['达标', 'Compliant'],
        ['证书监控', 'Certificate Monitor'],
        ['证書监控', 'Certificate Monitor'],
        ['应急演练记录', 'Emergency Drill Records'],
        ['值班安排', 'Watch Schedule'],
        ['当前班次', 'Current Watch'],
        ['甲班', 'Watch A'],
        ['下次换班', 'Next Changeover'],
        ['大管轮', 'Second Engineer'],
        ['水手长', 'Bosun'],
        ['机工', 'Motorman'],
    
        // ─── Energy Compliance ───
        ['当前', 'Current'],
        ['年度评级', 'Annual Rating'],
        ['年度轨迹', 'Annual Trajectory'],
        ['实时追踪', 'Real-time Tracking'],
        ['月度燃油消耗', 'Monthly Fuel Consumption'],
        ['排放监测', 'Emissions Monitoring'],
        ['二氧化碳', 'CO₂'],
        ['年度申报', 'Annual Declaration'],
        ['硫氧化物', 'SOx'],
        ['氮氧化物', 'NOx'],
        ['颗粒物', 'Particulate Matter'],
        ['合规文档', 'Compliance Documents'],
        ['文档名称', 'Document Name'],
        ['编号', 'Number'],
        ['有效期', 'Validity'],
        ['更新日期', 'Update Date'],
        ['审核机构', 'Audit Authority'],
        ['技术档案', 'Technical File'],
        ['改善方案', 'Improvement Plan'],
        ['国际能效证书', 'International Energy Cert.'],
        ['排放合规声明', 'Emission Compliance Decl.'],
        ['年报', 'Annual Report'],
        ['合规', 'Compliant'],
    
        // ─── Navigation ───
        ['电子海图', 'ECDIS'],
        ['航线路径点', 'Route Waypoints'],
        ['气象数据', 'Weather Data'],
        ['叠加层', 'Overlays'],
        ['目标', 'Targets'],
        ['雷达回波', 'Radar Echo'],
        ['安全等深线', 'Safety Contour'],
        ['追踪', 'Tracking'],
        ['航线进度', 'Route Progress'],
        ['航速', 'Speed'],
    
        // ─── Knowledge Base ───
        ['文档', 'Documents'],
        ['向量', 'Vectors'],
        ['领域', 'Domains'],
        ['領域', 'Domains'],
        ['全部', 'All'],
        ['法规', 'Regulations'],
        ['程序', 'Procedures'],
        ['技术', 'Technical'],
        ['培训', 'Training'],
        ['清单', 'Checklist'],
        ['清單', 'Checklist'],
        ['添加知识文档', 'Add Knowledge Document'],
        ['标题', 'Title'],
        ['标題', 'Title'],
        ['类别', 'Category'],
        ['类別', 'Category'],
        ['标签', 'Tags'],
        ['标籤', 'Tags'],
        ['逗号分隔', 'Comma separated'],
        ['内容', 'Content'],
        ['內容', 'Content'],
    
        // ─── Config page ───
        ['船舶信息', 'Ship Info'],
        ['船名', 'Ship Name'],
        ['船型', 'Ship Type'],
        ['穿浪双体船', 'Wave-Piercing Catamaran'],
        ['集装箱船', 'Container Ship'],
        ['散货船', 'Bulk Carrier'],
        ['油轮', 'Tanker'],
        ['总吨', 'Gross Tonnage'],
        ['功能开关', 'Feature Toggles'],
        ['决策辅助', 'Decision Aid'],
        ['決策輔助', 'Decision Aid'],
        ['启用', 'Enable'],
        ['自动避碰', 'Auto COLREG'],
        ['气象航线优化', 'Weather Route Optimization'],
        ['船员疲劳监控', 'Crew Fatigue Monitor'],
        ['船员疲勞监控', 'Crew Fatigue Monitor'],
        ['闭环审查', 'Closed-loop Audit'],
        ['构建', 'Build'],
        ['数据存储', 'Data Storage'],
        ['数据存儲', 'Data Storage'],
        ['访问控制', 'Access Control'],
        ['认证', 'Authentication'],
        ['端口控制', 'Port Control'],
        ['未授权', 'Unauthorized'],
        ['审查日志', 'Audit Log'],
        ['審查日誌', 'Audit Log'],
        ['记录所有系统配置变更', 'Log all config changes'],
        ['系统运行状态', 'System Runtime Status'],
        ['系统运行狀态', 'System Runtime Status'],
        ['运行时间', 'Uptime'],
        ['使用率', 'Usage'],
        ['内存使用', 'Memory Usage'],
        ['健康', 'Healt
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
        F
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

# 技能萃取页面前端架构设计方案

## 1. 概述
本项目在现有 `skill-extract.html` 基础上，实现**技能萃取过程可视化**单页应用。  
核心功能：
- 垂直时间轴展示操作日志节点
- 每个节点可展开「补全卡片」，卡片内包含**实时记录**（只读，由系统推送）与**回顾注释**（可编辑，提交后持久化）
- 右侧面板展示**阶段步骤卡**，带进度锁（前一阶段未完成时，后续阶段自动锁定）
- 所有实时数据通过 **WebSocket** 推送，保证低延迟与双向交互

技术约束：
- 纯原生 HTML5 / CSS3 / ES6 JavaScript
- 暗色主题（沿用项目 `monitoring.html` 的 CSS 变量体系）
- 不引入任何前端框架或构建工具
- 支持 i18n 国际化（中/英）
- 后端已有 `skill_extractor.py` 等模块，需新增 WebSocket 端点与少量 REST 接口

## 2. 页面布局

采用 **左右分栏** 布局（左侧为主时间轴区，右侧为阶段步骤面板），整体结构如下：

```
┌─────────────────────────────────────────────────────┐
│  Header (标题栏，与 monitoring.html 同风格)           │
├─────────────────────────┬───────────────────────────┤
│                         │                           │
│  时间轴容器             │  阶段步骤卡面板            │
│  (scrollable)           │  (含进度锁示意)            │
│                         │                           │
│   [节点1] ─────        │  ┌─ 步骤1: 数据采集 ✅     │
│         卡片(可展开)    │  ├─ 步骤2: 预处理   🔄     │
│   [节点2] ─────        │  ├─ 步骤3: 特征提取 🔒     │
│                         │  └─ 步骤4: 验证     🔒     │
│                         │                           │
│                         │                           │
│                         │                           │
├─────────────────────────┴───────────────────────────┤
│  WebSocket 连接状态 & 全局操作                        │
└─────────────────────────────────────────────────────┘
```

- **Header**：标题、WebSocket 连接指示器、任务选择器（如有多个萃取任务）
- **时间轴区**：占据约 65% 宽度，内部滚动
- **步骤面板**：占据约 35% 宽度，固定高度，显示步骤状态与进度锁
- 移动端响应式：小屏幕时步骤面板移至底部或隐藏

## 3. 组件设计

### 3.1 时间轴节点
每个节点对应一次后端推送的操作日志条目。

**视觉结构**：
- 左侧竖线（时间轴连线）
- 节点圆点（颜色表示状态：`ok`/`warn`/`error`/`pending`）
- 节点主体：
  - 时间戳 `HH:mm:ss`
  - 事件类型标签（如：步骤开始、萃取输出、异常）
  - 简要描述（最多两行）
  - 展开/折叠箭头

**交互**：
- 单击节点主体 → 在节点下方插入/移除对应的补全卡片（手风琴样式）
- 高亮当前选中节点，右侧步骤面板联动高亮所属步骤

### 3.2 补全卡片
节点展开后显示的详细面板，包含两个区域：

```
┌──────────────────────────────────┐
│  📋 实时记录                      │
│  [系统自动填充的 Markdown 文本]    │
│  (只读，通过 WebSocket 更新)      │
├──────────────────────────────────┤
│  ✍️ 回顾注释                      │
│  [textarea]                      │
│  [保存按钮]  [最后保存时间]       │
└──────────────────────────────────┘
```

- **实时记录**：`<div>` 内容直接由 WebSocket 推送更新，使用 `node.realtime_record` 数据渲染（支持换行和简单标记）
- **回顾注释**：`<textarea>` 初始化时填入已有注释，用户编辑后点击保存，调用 REST API 提交；保存成功后更新状态提示

### 3.3 阶段步骤卡
显示当前技能萃取任务的所有阶段（从后端配置或固定流程），每个阶段有：
- 步骤名称
- 状态图标：`🔒` 锁定 / `⏳` 待执行 / `🔄` 进行中 / `✅` 完成 / `❌` 失败
- 进度条（0-100%）—— 对于进行中步骤，显示百分比
- 颜色区分

**进度锁机制**：
- 后端维护步骤顺序和依赖关系，前端只做展示与简单的前置判断。
- 前端逻辑：
  1. 从 WebSocket 接收 `step_update` 消息，更新步骤状态数组
  2. 当某步骤状态为 `completed` 时，下一级步骤状态可由 `locked` 自动转为 `pending`（前端仅视觉反映，能否开始由后端控制）
  3. 若某步骤失败，则后续步骤保持锁定
- 视觉表现：
  - 锁定步骤：半透明，进度条灰色，无操作按钮
  - 待执行/进行中：正常颜色，可显示“开始”按钮（但实际触发由后端负责，前端可不提供触发按钮，避免误操作）

## 4. 数据模型与 WebSocket 协议

### 4.1 操作日志节点对象 (OperationNode)
```json
{
  "node_id": "uuid",
  "timestamp": "2026-05-09T08:12:03Z",
  "event_type": "step_start | step_end | extraction_output | info | warning | error",
  "description": "步骤1：数据采集开始",
  "status": "ok | warn | error | pending",
  "step_ref": "step1",
  "realtime_record": "多行文本，可能包含 markdown",
  "review_note": "用户添加的回顾注释",
  "review_note_updated_at": "2026-05-09T08:15:00Z",
  "review_note_updated_by": "user_id"
}
```

### 4.2 阶段步骤对象 (Step)
```json
{
  "step_id": "step1",
  "name": "数据采集",
  "status": "locked | pending | active | completed | failed",
  "progress": 75,
  "order": 1
}
```

### 4.3 WebSocket 消息格式
统一使用 JSON 文本帧。

**服务端 → 客户端**
```json
{
  "type": "log_update",
  "data": { <OperationNode> }
}
```
```json
{
  "type": "step_update",
  "data": { <Step> }   // 只发送变更的步骤
}
```
```json
{
  "type": "task_status",
  "data": {
    "task_id": "...",
    "status": "running | completed | failed",
    "message": "..."
  }
}
```
```json
{
  "type": "init_snapshot",
  "data": {
    "logs": [<OperationNode>],
    "steps": [<Step>],
    "task_status": "..."
  }
}
```

**客户端 → 服务端**（可选，用于后续扩展）
- 前端目前只接收更新，仅通过 REST 保存注释，因此不需要 WebSocket 发送数据。

### 4.4 REST API（新增）
| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/v1/skill-extract/{task_id}/logs` | 获取所有操作日志（初始化时使用） |
| `POST` | `/api/v1/skill-extract/{task_id}/notes/{node_id}` | 更新某个节点的回顾注释 |
| `GET` | `/api/v1/skill-extract/{task_id}/steps` | 获取当前任务的所有步骤定义与状态 |

*注：初始化时可用 REST 拉取快照，然后 WebSocket 增量更新，以减少首次连接压力。*

## 5. 文件修改清单

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| `src/frontend/skill-extract.html` | **重写** | 成为完整页面，包含 HTML 结构、内联 CSS 样式、引入 JS |
| `src/frontend/js/skill-extract.js` | **新建** | 核心交互逻辑：WebSocket、时间轴渲染、步骤锁、注释保存 |
| `src/frontend/js/i18n.js` | **修改** | 添加萃取页面相关中英文字符串 |
| `src/backend/agents/skill_extractor.py` | 可能需要添加 WebSocket 端点 | 架构设计暂不涉及，此处仅定义接口 |
| `src/backend/main.py` | 注册新路由 | 需要开发协同 |

## 6. 前端详细实施步骤（开发者指南）

### 6.1 搭建页面骨架（skill-extract.html）
- 复制 `monitoring.html` 的 `<head>` 结构，保留 CSS 变量、基础重置样式
- 引用 `js/i18n.js`、`js/nav-sidebar.js`（如有侧栏）以及新建的 `js/skill-extract.js`
- HTML 主体：
  - `#header`：标题 `🧬 技能萃取流程监控`，连接状态点，任务下拉栏（暂时只支持单个任务）
  - `#main-container`：flex 布局
    - `#timeline-panel`：`<div class="panel"><div class="panel-header">...</div><div class="panel-body" id="timelineContainer"></div></div>`
    - `#steps-panel`：`<div class="panel"><div class="panel-header">...</div><div class="panel-body" id="stepsContainer"></div></div>`
  - `#footer`：显示 WebSocket 连接状态、自动重连提示

### 6.2 CSS 样式设计
- 沿用 `monitoring.html` 的 CSS 变量（`--bg`, `--panel-bg`, `--border`, `--text`, `--accent`, `--accent2`, `--warn`, `--error`）
- 时间轴节点样式：
  ```css
  .timeline-line { position: absolute; left: 16px; top: 0; bottom: 0; width: 2px; background: var(--border); }
  .timeline-item { display: flex; gap: 12px; cursor: pointer; padding: 8px 0; }
  .timeline-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--text-dim); flex-shrink: 0; margin-top: 4px; }
  .timeline-dot.ok { background: var(--accent2); }
  .timeline-dot.warn { background: var(--warn); }
  .timeline-dot.error { background: var(--error); }
  .timeline-content { ... }
  .completion-card { background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 4px; padding: 12px; margin-top: 8px; }
  ```
- 阶段步骤卡片样式：
  ```css
  .step-item { display: flex; align-items: center; gap: 10px; padding: 8px; border-left: 4px solid var(--border); ... }
  .step-item.locked { opacity: 0.4; }
  .step-item.completed { border-left-color: var(--accent2); }
  .step-progress { width: 100px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
  .step-progress-fill { height: 100%; background: var(--accent); transition: width 0.3s; }
  ```
- 动画：节点高亮、卡片展开/收起使用 `max-height` 过渡。

### 6.3 JavaScript 核心实现（skill-extract.js）
采用模块模式（IIFE）包裹，避免全局污染。

**主要模块**：

#### a. WebSocket 管理器
```js
const wsManager = {
  ws: null,
  taskId: getTaskIdFromURL(),
  onMessage: null,
  connect() {
    this.ws = new WebSocket(`ws://${location.host}/ws/skill-extract?task_id=${this.taskId}`);
    this.ws.onopen = () => updateConnectionStatus(true);
    this.ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (this.onMessage) this.onMessage(msg);
    };
    this.ws.onclose = () => { updateConnectionStatus(false); /* 自动重连 */ };
  }
};
```

#### b. 数据模型（内存状态）
```js
const store = {
  logs: [],        // 按时间排序的节点数组
  steps: [],       // 按 order 排序
  taskStatus: 'running',
  // 方法：更新节点、更新步骤
};
```

#### c. 渲染函数
- `renderTimeline()`：全量重绘时间轴，或增量 `updateNode(node_id)`
- `renderSteps()`：绘制步骤面板，根据状态施加 locked 样式
- `toggleCard(nodeId)`：展开/折叠补全卡片，并绑定注释保存按钮

#### d. WebSocket 消息处理
```js
function handleMessage(msg) {
  switch(msg.type) {
    case 'init_snapshot':
      store.logs = msg.data.logs;
      store.steps = msg.data.steps;
      renderAll();
      break;
    case 'log_update':
      const idx = store.logs.findIndex(n => n.node_id === msg.data.node_id);
      if (idx >= 0) store.logs[idx] = msg.data;
      else store.logs.push(msg.data);
      renderTimeline(); // 可优化为局部更新
      break;
    case 'step_update':
      const stepIdx = store.steps.findIndex(s => s.step_id === msg.data.step_id);
      if (stepIdx >= 0) store.steps[stepIdx] = msg.data;
      renderSteps();
      break;
    case 'task_status':
      store.taskStatus = msg.data.status;
      // 更新 header 状态
      break;
  }
}
```

#### e. 步骤锁逻辑
- 步骤顺序由 `steps` 数组维护。
- 渲染时，遍历步骤，对于非第一步骤，判断前一步是否 `completed`；若否，则强制设置该步骤为 `locked`。（前端只做视觉锁，不做业务控制）
- 进度条从 `step.progress` 取值。

#### f. 回顾注释保存
```js
async function saveNote(nodeId, content) {
  const resp = await fetch(`/api/v1/skill-extract/${wsManager.taskId}/notes/${nodeId}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ review_note: content })
  });
  if (resp.ok) {
    // 更新本地节点对象的 review_note 和时间
    const node = store.logs.find(n => n.node_id === nodeId);
    if (node) {
      node.review_note = content;
      node.review_note_updated_at = new Date().toISOString();
      renderTimeline(); // 刷新显示
    }
  }
}
```

#### g. i18n 集成
- 所有中文界面文本通过 `PX_I18N.translate()` 函数动态翻译（i18n.js 已提供的全局实例）。
- 在 i18n.js 的 `TEXT_MAP` 中新增条目（见第 7 节）

### 6.4 初始化流程
1. 页面加载，读取 URL 参数 `task_id`，若无则使用默认测试任务。
2. 显示 `loading` 状态，建立 WebSocket 连接。
3. WebSocket 连接成功，等待 `init_snapshot` 消息，或主动发起 REST 请求获取初始数据（作为降级方案）。
4. 渲染界面。

## 7. i18n 扩展（修改 `src/frontend/js/i18n.js`）
在 `TEXT_MAP` 中添加以下键值对：

```js
['技能萃取流程监控', 'Skill Extraction Pipeline'],
['操作日志', 'Operation Log'],
['阶段步骤', 'Stage Steps'],
['实时记录', 'Real-time Record'],
['回顾注释', 'Review Note'],
['保存注释', 'Save Note'],
['已保存', 'Saved'],
['正在连接', 'Connecting'],
['已断开', 'Disconnected'],
['已锁定', 'Locked'],
['待开始', 'Pending'],
['进行中', 'In Progress'],
['已完成', 'Completed'],
['失败', 'Failed'],
['步骤', 'Step'],
```

## 8. 后端接口规范（供后端开发参考）
- **WebSocket 端点** `/ws/skill-extract?task_id={task_id}`
  - 连接时，服务端应查询该任务的最新日志和步骤状态，发送 `init_snapshot`。
  - 后续每当技能萃取引擎产生新日志或步骤状态变化时，广播相应消息。
- **REST 接口**
  - `GET /api/v1/skill-extract/{task_id}/logs` → 返回 `{ logs: [...], steps: [...] }`
  - `POST /api/v1/skill-extract/{task_id}/notes/{node_id}`
    - 请求体：`{ "review_note": "string" }`
    - 响应：更新后的 Node 对象或仅 200 OK

## 9. 进度锁与状态流转
- 前端步骤面板根据后端推送的步骤状态更新，当某步骤为 `locked` 时，该步骤显示为灰色不可交互。
- 仅当前一步骤变为 `completed` 时，后续步骤由后端推送 `pending` 或 `active` 状态，前端随即解锁。
- 不提供前端“开始步骤”按钮，避免状态不一致风险，所有控制权归后端。

## 10. 兼容性与降级
- 若 WebSocket 连接失败，可退化为每 5 秒轮询 `/api/v1/skill-extract/{task_id}/logs`，类似 `monitoring.html` 的刷新机制。
- 降级模式下仍支持注释保存（REST 始终可用）。

## 11. 交叉关注点
- **暗色主题一致性**：复用 `monitoring.html` 中定义的 `:root` 变量，确保页面风格统一。
- **性能**：日志可能较多，只渲染可见区域，或使用虚拟滚动（初期可简单全量渲染，若节点 < 500 则无性能问题）。
- **安全性**：注释保存请求需要携带认证信息（如已有的 session），后续由后端中间件处理。

## 12. 开发顺序建议
1. 搭建 HTML 骨架与 CSS 布局，填入静态示例数据，确保样式与响应式正确。
2. 实现 JavaScript 静态模拟数据渲染时间轴和步骤面板。
3. 集成 WebSocket 管理器，替换静态数据为动态推送。
4. 实现补全卡片展开/折叠与注释保存。
5. 细化步骤锁交互动画。
6. 添加 i18n 支持。
7. 联调后端接口，处理异常与降级。

---  
此方案完整定义了前端架构与交互流程，开发工程师可按步骤实施，后端同事可同步实现所需 API。任何不确定之处，请以现有项目代码风格为准。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
