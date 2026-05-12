# 研究分析 — researcher

任务: 设计操作事件表和情境切片关联表数据模型，完成建表与存储逻辑，确保操作序列不可变、情境切片可追溯
步骤: research
Agent: build_researcher

---

📋 任务: 1f0da2f7-522
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
  设计操作事件表和情境切片关联表数据模型，完成建表与存储逻辑，确保操作序列不可变、情境切片可追溯
  Architect + 全栈开发
  
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
  ... (共 727 个 src/ 文件)
  
  ```
  
  ### 文件: `src/frontend/system-evolution.html`
  ```html
  <!DOCTYPE html>
  <html lang="zh-CN" data-obc-theme="dusk">
  <head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>系统演进 — AgentsGroup2026</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Noto+Serif+SC:wght@200;300;400;600;900&family=JetBrains+Mono:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
  :root{
    --shironeri:oklch(0.96 0.003 110);--ishi:oklch(0.91 0.004 110);--kabe:oklch(0.85 0.005 110);
    --hai:oklch(0.78 0.005 110);--nezumi:oklch(0.68 0.006 110);--sumi:oklch(0.18 0.008 110);
    --sumi-2:oklch(0.38 0.006 110);--sumi-3:oklch(0.55 0.005 110);
    --koke:oklch(0.52 0.04 160);--shu:oklch(0.48 0.07 22);--kitsune:oklch(0.56 0.05 70);
    --groove:oklch(0.82 0.004 110);
    --font-serif:'Noto Serif SC',serif;--font-sans:'Noto Sans SC',sans-serif;--font-mono:'JetBrains Mono',monospace;
    --lime:oklch(0.52 0.04 160);--cyan:oklch(0.52 0.04 160);--amber:oklch(0.56 0.05 70);--red:oklch(0.48 0.07 22);
    --muted:oklch(0.55 0.005 110);--dim:oklch(0.55 0.005 110);
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  body{font-family:var(--font-sans);min-height:100vh;background:var(--shironeri);color:var(--sumi);position:relative}
  body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
    background-image:radial-gradient(oklch(0 0 0/.012) 1px,transparent 1px),radial-gradient(oklch(0 0 0/.008) 1px,transparent 1px);
    background-size:5px 5px,7px 7px;background-position:0 0,3px 3px}
  a{color:var(--koke);text-decoration:none}
  .seal{display:inline-block;font-size:10px;font-weight:900;color:var(--shironeri);background:var(--sumi);padding:1px 5px;line-height:1.3;font-family:var(--font-serif);vertical-align:middle;margin-right:4px}
  .seal-koke{background:var(--koke)}.seal-shu{background:var(--shu)}.seal-kitsune{background:var(--kitsune)}
  
  /* Layout */
  .app{display:flex;height:100vh;overflow:hidden;position:relative;z-index:1}
  .sidebar{width:260px;min-width:260px;background:var(--ishi);border-right:1px solid var(--groove);display:flex;flex-direction:column;overflow:hidden}
  .main{flex:1;display:flex;flex-direction:column;overflow:hidden}
  .topbar{display:flex;justify-content:space-between;align-items:center;padding:12px 28px;border-bottom:1px solid var(--groove);background:var(--shironeri);min-height:56px}
  .topbar-left{display:flex;align-items:center;gap:12px}
  .topbar-left h1{font-size:18px;font-weight:600}
  .topbar-right{display:flex;gap:8px;align-items:center}
  .main-scroll{flex:1;overflow-y:auto;padding:24px 28px;min-height:0}
  
  /* Sidebar */
  .sb-header{padding:16px;border-bottom:1px solid var(--groove)}
  .sb-header h2{font-size:15px;color:var(--koke);display:flex;align-items:center;gap:6px}
  .sb-nav{display:flex;flex-direction:column;gap:2px;padding:8px}
  .sb-nav a{padding:8px 12px;font-size:13px;color:var(--muted);cursor:pointer;display:flex;align-items:center;gap:8px;transition:.15s}
  .sb-nav a:hover{background:oklch(0 0 0/.03);color:var(--sumi)}
  .sb-nav a.active{background:oklch(0.48 0.07 22/.06);color:var(--shu);font-weight:600}
  .sb-section{padding:8px 12px;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin-top:8px;font-weight:600}
  .sb-footer{padding:12px;border-top:1px solid var(--groove);margin-top:auto}
  
  /* Buttons */
  .btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;border:1px solid var(--groove);font-family:inherit;transition:.15s;background:transparent;color:var(--koke)}.btn:hover{background:oklch(0 0 0/.03)}
  .btn-primary{background:var(--sumi);color:var(--shironeri);border-color:transparent}.btn-primary:hover{background:oklch(0.28 0.008 110)}
  .btn-danger{color:var(--shu);border-color:oklch(0.48 0.07 22/.3)}.btn-danger:hover{background:oklch(0.48 0.07 22/.06)}
  .btn-sm{padding:5px 12px;font-size:12px}
  .btn-ghost{border:none;padding:6px 10px}
  
  /* Cards */
  .card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px;margin-bottom:20px}
  .stat-card{background:var(--ishi);border:1px solid var(--groove);padding:16px}
  .stat-card .label{font-size:12px;color:var(--muted);margin-bottom:6px;display:flex;align-items:center;gap:6px}
  .stat-card .value{font-size:24px;font-weight:700;font-family:var(--font-mono);color:var(--sumi)}
  .stat-card .sub{font-size:11px;color:var(--dim);margin-top:4px}
  
  /* Table */
  .tbl{width:100%;border-collapse:collapse;font-size:13px}
  .tbl th{text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;color:var(--dim);border-bottom:1px solid var(--groove);letter-spacing:.5px;font-weight:500}
  .tbl td{padding:10px;border-bottom:1px solid oklch(0 0 0/.04);color:var(--sumi)}
  .tbl tr:hover td{background:oklch(0 0 0/.02)}
  .chip{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;font-size:11px;background:oklch(0 0 0/.03);color:var(--koke);border:1px solid var(--groove);margin:2px}
  .section{margin-bottom:24px}
  .section-title{font-size:16px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;gap:8px}
  .toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;background:var(--ishi);border:1px solid var(--groove);font-size:13px;opacity:0;transition:.3s;pointer-events:none;z-index:999;color:var(--sumi)}.toast.show{opacity:1}
  
  /* Ratchet Flow Diagram */
  .ratchet-flow{display:flex;align-items:center;gap:0;padding:20px 0;overflow-x:auto}
  .ratchet-node{display:flex;flex-direction:column;align-items:center;min-width:130px}
  .ratchet-dot{width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:900;border:2px solid var(--groove);background:var(--shironeri);font-family:var(--font-serif);transition:.35s;position:relative}
  .ratchet-dot.active{border-color:var(--koke);box-shadow:0 0 0 3px oklch(0.52 0.04 160/.15),0 0 20px oklch(0.52 0.04 160/.25);animation:r-pulse 2s ease-in-out infinite}
  .ratchet-dot.done{border-color:var(--koke);background:oklch(0.52 0.04 160/.08);color:var(--koke)}
  .ratchet-dot.failed{border-color:var(--shu);background:oklch(0.48 0.07 22/.08);color:var(--shu)}
  @keyframes r-pulse{0%,100%{box-shadow:0 0 0 3px oklch(0.52 0.04 160/.15)}50%{box-shadow:0 0 0 3px oklch(0.52 0.04 160/.3),0 0 24px oklch(0.52 0.04 160/.2)}}
  .ratchet-label{font-size:11px;color:var(--muted);margin-top:6px;text-align:center;font-weight:500}
  .ratchet-sublabel{font-size:10px;color:var(--dim);margin-top:2px;font-family:var(--font-mono)}
  .ratchet-connector{width:40px;height:2px;background:var(--groove);flex-shrink:0}
  .ratchet-connector.done{background:var(--koke)}
  .ratchet-lock{border-color:var(--kitsune) !important}
  .ratchet-lock .ratchet-dot{border-color:var(--kitsune);color:var(--kitsune)}
  
  /* Compliance Gauge */
  .gauge-wrap{display:flex;align-items:center;gap:20px}
  .gauge-ring{position:relative;width:80px;height:80px;flex-shrink:0}
  .gauge-ring svg{width:80px;height:80px;transform:rotate(-90deg)}
  .gauge-grade{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;font-family:var(--font-mono)}
  
  /* Cycle log */
  .cycle-log{background:var(--ishi);border:1px solid var(--groove);padding:12px 16px;font-family:var(--font-mono);font-size:12px;line-height:1.8;max-height:200px;overflow-y:auto;margin-top:12px}
  .cycle-log .ok{color:var(--koke)}.cycle-log .err{color:var(--shu)}.cycle-log .run{color:var(--kitsune)}
  
  /* Heritage ledger */
  .heritage-item{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:var(--ishi);border:1px solid var(--groove);margin-bottom:6px;font-size:13px}
  .heritage-item .h-title{font-weight:600;font-size:13px}
  .heritage-item .h-meta{font-size:11px;color:var(--muted);font-family:var(--font-mono)}
  .heritage-item .h-delta{font-family:var(--font-mono);font-size:13px;font-weight:700;color:var(--koke);white-space:nowrap}
  
  /* Zone badge */
  .zone-badge{padding:8px 14px;background:oklch(0.52 0.04 160/.06);border:1px solid oklch(0.52 0.04 160/.15);display:inline-flex;align-items:center;gap:8px;font-size:12px;margin:4px}
  .zone-badge b{color:var(--sumi)}
  
  /* Rule card */
  .rule-card{padding:10px 14px;background:var(--ishi);border:1px solid var(--groove)}
  .rule-card .r-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
  .rule-card .r-id{font-size:12px;font-weight:700;font-family:var(--font-mono)}
  .rule-card .r-title{font-size:12px;margin-top:2px}
  .rule-card .r-ref{font-size:11px;color:var(--dim);margin-top:2px}
  .rule-card .r-meta{font-size:11px;margin-top:4px}
  .rule-card .r-actions{display:flex;gap:6px;margin-top:6px;justify-content:flex-end}
  .rule-card .r-actions button{padding:2px 8px;font-size:11px;cursor:pointer;border:1px solid var(--groove);background:transparent;color:var(--ink);border-radius:3px}
  .rule-card .r-actions button:hover{background:var(--groove)}
  .rule-card .r-actions .btn-del{color:var(--shu);border-color:oklch(0.48 0.07 22/.3)}
  .rule-card .r-actions .btn-del:hover{background:oklch(0.48 0.07 22/.08)}
  /* Edit Rule Modal */
  .rule-modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:1000;display:flex;align-items:center;justify-content:center}
  .rule-modal{background:var(--bg);border:1px solid var(--groove);padding:20px 24px;min-width:380px;max-width:500px;border-radius:6px}
  .rule-modal h3{margin:0 0 14px;font-size:14px;font-weight:600}
  .rule-modal label{display:block;font-size:12px;color:var(--dim);margin:8px 0 3px}
  .rule-modal input,.rule-modal select,.rule-modal textarea{width:100%;padding:6px 8px;font-size:12px;border:1px solid var(--groove);background:var(--ishi);color:var(--ink);border-radius:3px;box-sizing:border-box}
  .rule-modal textarea{min-height:60px;resize:vertical}
  .rule-modal .modal-btns{display:flex;gap:8px;justify-content:flex-end;margin-top:16px}
  
  /* Tabs */
  .tab-bar{display:flex;gap:0;border-bottom:1px solid var(--groove);margin-bottom:20px}
  .tab-btn{padding:10px 18px;font-size:13px;cursor:pointer;color:var(--muted);border:none;border-bottom:2px solid transparent;background:none;font-family:inherit;font-weight:500;transition:.15s}
  .tab-btn:hover{color:var(--sumi)}
  .tab-btn.active{color:var(--shu);border-bottom-color:var(--shu);font-weight:600}
  .tab-panel{display:none}.tab-panel.active{display:block}
  
  /* Filter bar */
  .filter-bar{display:flex;gap:8px;align-items:center;margin-bottom:16px;flex-wrap:wrap}
  .filter-bar select,.filter-bar input{padding:6px 10px;font-size:12px;border:1px solid var(--groove);background:var(--shironeri);color:var(--sumi);font-family:inherit}
  .filter-bar select:focus,.filter-bar input:focus{outline:none;border-color:var(--koke)}
  
  /* Trend placeholder */
  .trend-chart{background:var(--ishi);border:1px solid var(--groove);padding:20px;min-height:120px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px}
  .audit-entry{padding:8px 12px;border-bottom:1px solid oklch(0 0 0/.04);font-size:12px;display:flex;gap:12px;align-items:center}
  .audit-entry .ae-time{font-family:var(--font-mono);color:var(--dim);font-size:11px;min-width:140px}
  .audit-entry .ae-type{font-weight:600;min-width:80px}
  .audit-entry .ae-detail{color:var(--sumi-2);flex:1}
  </style>
  </head>
  <body>
  <div class="app">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="sb-header">
        <h2><span class="seal seal-koke">演</span> 系统演进</h2>
      </div>
      <div class="sb-nav">
        <a class="active" onclick="switchPanel('overview')"><span class="seal">览</span> 演进概览</a>
        <a onclick="switchPanel('rules')"><span class="seal">规</span> 审查规则</a>
        <a onclick="switchPanel('items')"><span class="seal seal-shu">项</span> 演进条目</a>
        <a onclick="switchPanel('zones')"><span class="seal seal-koke">域</span> 合规区域</a>
        <a onclick="switchPanel('trail')"><span class="seal">迹</span> 审计轨迹</a>
      </div>
      <div class="sb-section">操作</div>
      <div style="padding:8px 12px;display:flex;flex-direction:column;gap:6px">
        <button class="btn btn-sm" onclick="runAudit()">🔍 运行审查</button>
        <button class="btn btn-sm btn-primary" onclick="runCycleOnRatchet()">▶ 演进周期</button>
        <button class="btn btn-sm" onclick="recalcRating()">📊 重算评级</button>
      </div>
      <div class="sb-footer">
        <a href="/skill-extract.html" class="btn btn-ghost btn-sm" style="width:100%;justify-content:center;margin-bottom:6px"><span class="seal seal-shu">萃</span> 技能萃取</a>
        <a href="/agent-team-config.html" class="btn btn-ghost btn-sm" style="width:100%;justify-content:center">← 返回团队管理</a>
      </div>
    </div>
  
    <!-- Main Content -->
    <div class="main">
      <div class="topbar">
        <div class="topbar-left">
          <h1 id="panel-title">演进概览</h1>
          <span id="panel-badge" style="font-size:11px;padding:2px 8px;background:oklch(0.52 0.04 160/.1);color:var(--koke);font-family:var(--font-mono)"></span>
        </div>
        <div class="topbar-right">
          <span id="executor-status" style="font-size:11px;color:var(--muted);cursor:pointer" onclick="showExecutorStatus()" title="执行器状态"></span>
          <span id="last-audit" style="font-size:11px;color:var(--muted)"></span>
          <a href="/skill-extract.html" class="btn btn-sm"><span class="seal seal-shu">萃</span> 萃取</a>
          <button class="btn btn-sm" onclick="refreshAll()">↻ 刷新</button>
        </div>
      </div>
      <div class="main-scroll" id="content">
  
        <!-- ═══ Overview Panel ═══ -->
        <div id="panel-overview" class="tab-panel active">
          <!-- Compliance Rating -->
          <div class="section">
            <div class="section-title">合规评级</div>
            <div id="ov-rating" class="card-grid"></div>
          </div>
          <!-- Stats -->
          <div class="section">
            <div class="section-title">演进统计</div>
            <div id="ov-stats" class="card-grid"></div>
          </div>
          <!-- 达尔文棘轮 — 五步闭环 -->
          <div class="section">
            <div class="section-title">🔄 达尔文棘轮 — 不可逆演进机制</div>
            <p style="font-size:12px;color:var(--sumi-2);margin-bottom:12px;line-height:1.6">
              棘轮机制确保系统只能向前演进，永不回退。通过验证的改进被锁定为「遗产」— <b>append-only</b> 不可变记录。
            </p>
            <div class="ratchet-flow" id="ratchet-flow">
              <div class="ratchet-node">
                <div class="ratchet-dot" id="r-audit">审</div>
                <div class="ratchet-label">① 审查</div>
                <div class="ratchet-sublabel">AUDIT</div>
              </div>
              <div class="ratchet-connector" id="rc-1"></div>
              <div class="ratchet-node">
                <div class="ratchet-dot" id="r-dispatch">派</div>
                <div class="ratchet-label">② 派发</div>
                <div class="ratchet-sublabel">DISPATCH</div>
              </div>
              <div class="ratchet-connector" id="rc-2"></div>
              <div class="ratchet-node">
                <div class="ratchet-dot" id="r-verify">验</div>
                <div class="ratchet-label">③ 验证</div>
                <div class="ratchet-sublabel">VERIF
  ```
  
  ### 文件: `src/backend/tests/test_agent_toolbox.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentToolbox 单元测试 — 工具函数 (read_file, grep, list_files, dispatch)."""
  
  from __future__ import annotations
  
  import json
  import os
  import tempfile
  from pathlib import Path
  
  import pytest
  
  from agents.agent_toolbox import (
      TOOL_SCHEMA,
      dispatch_tool_call,
      get_tools_for_role,
      tool_grep,
      tool_list_files,
      tool_patch_file,
      tool_read_file,
      tool_run_python,
      tool_run_pytest,
      tool_write_file,
  )
  
  
  # ═══════════════════════════════════════════════════
  # read_file 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolReadFile:
      """tool_read_file 单元测试."""
  
      def test_read_existing_file(self):
          result = tool_read_file("src/backend/tests/__init__.py")
          assert result["ok"] is True
          assert "Test Pipeline" in result["content"]
  
      def test_read_with_line_range(self):
          result = tool_read_file(
              "src/backend/tests/__init__.py",
              start_line=1,
              end_line=3,
          )
          assert result["ok"] is True
          assert result["total_lines"] > 0
  
      def test_read_nonexistent_file(self):
          result = tool_read_file("nonexistent/file.txt")
          assert result["ok"] is False
  
      def test_read_empty_path_raises(self):
          result = tool_read_file("")
          assert result["ok"] is False
  
  
  # ═══════════════════════════════════════════════════
  # grep 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolGrep:
      """tool_grep 单元测试."""
  
      def test_grep_finds_matches(self):
          result = tool_grep(r"class.*Test", include="src/backend/tests/*.py")
          assert result["ok"] is True
          assert len(result["hits"]) > 0
          for hit in result["hits"]:
              assert "path" in hit
              assert "line" in hit
              assert "text" in hit
  
      def test_grep_no_matches(self):
          result = tool_grep(r"XYZZY_NOT_FOUND_12345", include="src/backend/tests/*.py")
          assert result["ok"] is True
          assert len(result["hits"]) == 0
  
      def test_grep_bad_regex(self):
          result = tool_grep(r"[invalid")
          assert result["ok"] is False
          assert "bad regex" in result["error"]
  
      def test_grep_max_hits(self):
          result = tool_grep(r"def ", include="src/backend/agents/*.py", max_hits=3)
          assert result["ok"] is True
          assert len(result["hits"]) <= 3
  
  
  # ═══════════════════════════════════════════════════
  # list_files 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolListFiles:
      """tool_list_files 单元测试."""
  
      def test_list_tests_directory(self):
          result = tool_list_files("src/backend/tests")
          assert result["ok"] is True
          files = result["files"]
          assert any("__init__.py" in f for f in files)
          assert any("conftest.py" in f for f in files)
  
      def test_list_nonexistent_directory(self):
          result = tool_list_files("nonexistent/dir")
          assert result["ok"] is False
  
      def test_list_with_depth(self):
          result = tool_list_files("src/backend", max_depth=1)
          assert result["ok"] is True
          # 不应深入到 agents/ 子目录
          for f in result["files"]:
              assert "/agents/" not in f or f.count("/") <= 2
  
  
  # ═══════════════════════════════════════════════════
  # write_file / patch_file 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolWriteFile:
      """tool_write_file 单元测试."""
  
      def test_write_new_file(self):
          result = tool_write_file(
              "tests/_test_write_temp.txt",
              "hello world",
          )
          assert result["ok"] is True
          assert result["path"] == "tests/_test_write_temp.txt"
          # 清理
          Path("src/backend/tests/_test_write_temp.txt").unlink(missing_ok=True)
  
      def test_write_outside_allowed_fails(self):
          result = tool_write_file(
              "../outside.txt",
              "should fail",
          )
          assert result["ok"] is False
  
      def test_create_only_existing(self):
          # conftest.py 已存在
          result = tool_write_file(
              "tests/conftest.py",
              "new content",
              create_only=True,
          )
          assert result["ok"] is False
          assert "create_only" in result["error"]
  
  
  class TestToolPatchFile:
      """tool_patch_file 单元测试."""
  
      def test_patch_unique_match(self):
          # 先创建临时文件
          tmp_path = "tests/_test_patch_temp.py"
          tool_write_file(tmp_path, "original line\nother line\n")
  
          result = tool_patch_file(
              tmp_path,
              search="original line",
              replace="patched line",
          )
          assert result["ok"] is True
  
          # 验证修改
          read_back = tool_read_file(tmp_path)
          assert "patched line" in read_back["content"]
  
          # 清理
          Path("src/backend/tests/_test_patch_temp.py").unlink(missing_ok=True)
  
      def test_patch_not_found(self):
          result = tool_patch_file(
              "tests/conftest.py",
              search="NOT_IN_THIS_FILE_XYZ",
              replace="whatever",
          )
          assert result["ok"] is False
  
      def test_patch_outside_allowed(self):
          result = tool_patch_file(
              "../outside.txt",
              search="x",
              replace="y",
          )
          assert result["ok"] is False
  
  
  # ═══════════════════════════════════════════════════
  # run_python 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolRunPython:
      """tool_run_python 单元测试."""
  
      def test_simple_expression(self):
          result = tool_run_python("print(1+1)")
          assert result["ok"] is True
          assert result["exit_code"] == 0
          assert "2" in result["stdout"]
  
      def test_import_check(self):
          result = tool_run_python("from agents.models import AgentProfile; print('OK')")
          assert result["ok"] is True
          assert "OK" in result["stdout"]
  
      def test_syntax_error(self):
          result = tool_run_python("def broken(")
          assert result["ok"] is True  # subprocess 成功执行
          assert result["exit_code"] != 0
  
  
  # ═══════════════════════════════════════════════════
  # run_pytest 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolRunPytest:
      """tool_run_pytest 单元测试."""
  
      def test_run_pytest_collect_only(self):
          result = tool_run_pytest("tests/test_models.py --co")
          assert result["ok"] is True
  
  
  # ═══════════════════════════════════════════════════
  # dispatch_tool_call 测试
  # ═══════════════════════════════════════════════════
  
  class TestDispatchToolCall:
      """dispatch_tool_call 单元测试."""
  
      def test_dispatch_read_file(self):
          result = dispatch_tool_call(
              "read_file",
              json.dumps({"path": "src/backend/tests/__init__.py"}),
          )
          assert result["ok"] is True
  
      def test_dispatch_finish(self):
          result = dispatch_tool_call("finish", "{}")
          assert result["ok"] is True
          assert result["_finished"] is True
  
      def test_dispatch_unknown_tool(self):
          result = dispatch_tool_call("unknown_tool", "{}")
          assert result["ok"] is False
  
      def test_dispatch_bad_json_args(self):
          result = dispatch_tool_call("read_file", "not json")
          assert result["ok"] is False
  
      def test_dispatch_bad_kwargs(self):
          result = dispatch_tool_call(
              "read_file",
              json.dumps({"path": "tests/__init__.py", "extra_bad_kwarg": True}),
          )
          # Either ok=False due to TypeError, or ok=True (if extra kwarg ignored)
          assert "ok" in result  # 至少返回了有效结构
  
  
  # ═══════════════════════════════════════════════════
  # get_tools_for_role 测试
  # ═══════════════════════════════════════════════════
  
  class TestGetToolsForRole:
      """get_tools_for_role 单元测试."""
  
      def test_developer_has_write_tools(self):
          tools = get_tools_for_role("developer")
          names = {t["function"]["name"] for t in tools}
          assert "write_file" in names
          assert "patch_file" in names
          assert "run_python" in names
  
      def test_qa_has_pytest(self):
          tools = get_tools_for_role("qa")
          names = {t["function"]["name"] for t in tools}
          assert "run_pytest" in names
  
      def test_architect_has_readonly(self):
          tools = get_tools_for_role("architect")
          names = {t["function"]["name"] for t in tools}
          assert "write_file" not in names
          assert "run_python" in names
  
      def test_all_roles_have_read_grep_list(self):
          for role in ("developer", "qa", "architect", "researcher", "unknown"):
              tools = get_tools_for_role(role)
              names = {t["function"]["name"] for t in tools}
              assert "read_file" in names
              assert "grep" in names
              assert "list_files" in names
              assert "finish" in names
  
  
  # ═══════════════════════════════════════════════════
  # TOOL_SCHEMA 结构测试
  # ═══════════════════════════════════════════════════
  
  class TestToolSchema:
      """TOOL_SCHEMA 常量测试."""
  
      def test_all_tools_have_function_name(self):
          for tool in TOOL_SCHEMA:
              assert "function" in tool
              assert "name" in tool["function"]
  
      def test_known_tools_present(self):
          names = {t["function"]["name"] for t in TOOL_SCHEMA}
          expected = {"read_file", "grep", "list_files", "write_file",
                      "patch_file", "run_python", "run_pytest", "finish"}
          assert expected.issubset(names)
  
  ```
  
  ### 文件: `src/backend/tests/test_team_manager.py`
  ```py
  # -*- coding: utf-8 -*-
  """团队管理器单元测试 — TeamManager CRUD 操作."""
  
  from __future__ import annotations
  
  import pytest
  
  from agents.models import (
      AgentProfile,
      AgentTeam,
      ModelConfig,
  )
  
  
  class TestTeamManagerCreate:
      """TeamManager 创建操作测试."""
  
      def test_create_team(self, team_manager):
          team = team_manager.create_team(
              name="测试团队",
              team_id="team-001",
              description="自动化测试",
          )
          assert team is not None
          assert team.team_id == "team-001"
          assert team.name == "测试团队"
          assert team.description == "自动化测试"
  
      def test_create_duplicate_team_raises(self, team_manager):
          team_manager.create_team(name="A", team_id="team-001")
          with pytest.raises(ValueError):
              team_manager.create_team(name="B", team_id="team-001")
  
  
  class TestTeamManagerRead:
      """TeamManager 读取操作测试."""
  
      def test_get_team(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          team = team_manager.get_team("t1")
          assert team is not None
          assert team.name == "T1"
  
      def test_get_nonexistent_team(self, team_manager):
          team = team_manager.get_team("nonexistent")
          assert team is None
  
      def test_list_teams(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          team_manager.create_team(name="T2", team_id="t2")
          teams = team_manager.list_teams()
          assert len(teams) == 2
          names = {t.name for t in teams}
          assert names == {"T1", "T2"}
  
  
  class TestTeamManagerUpdate:
      """TeamManager 更新操作测试."""
  
      def test_update_team(self, team_manager):
          team_manager.create_team(name="Old", team_id="t1")
          updated = team_manager.update_team("t1", name="New", description="Updated")
          assert updated is not None
          assert updated.name == "New"
          assert updated.description == "Updated"
  
      def test_update_team_ignores_immutable(self, team_manager):
          team_manager.create_team(name="OK", team_id="t1")
          # team_id 不在 AgentTeam dataclass 中当作可变字段
          updated = team_manager.update_team("t1", name="StillOK")
          assert updated is not None
          assert updated.team_id == "t1"  # team_id 不可变
  
      def test_update_nonexistent_team(self, team_manager):
          result = team_manager.update_team("noop", name="X")
          assert result is None
  
  
  class TestTeamManagerDelete:
      """TeamManager 删除操作测试."""
  
      def test_delete_team(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          deleted = team_manager.delete_team("t1")
          assert deleted is not None
          assert team_manager.get_team("t1") is None
  
      def test_delete_nonexistent_team(self, team_manager):
          result = team_manager.delete_team("noop")
          assert result is None
  
  
  class TestAgentManagement:
      """Agent 管理操作测试."""
  
      def test_add_agent(self, team_manager, sample_agent_dict):
          team_manager.create_team(name="T1", team_id="t1")
          agent = AgentProfile(
              agent_id="agent-001",
              name="TestAgent",
              role="developer",
              state="idle",
          )
          result = team_manager.add_agent_to_team("t1", agent)
          assert result is True
  
      def test_get_agent(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          agent = AgentProfile(agent_id="a1", name="A1", role="developer")
          team_manager.add_agent_to_team("t1", agent)
  
          found = team_manager.get_agent("t1", "a1")
          assert found is not None
          assert found.name == "A1"
  
      def test_get_agent_nonexistent_team(self, team_manager):
          result = team_manager.get_agent("no-team", "any-agent")
          assert result is None
  
      def test_list_agents(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a1", name="A1", role="dev"))
          team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a2", name="A2", role="qa"))
  
          agents = team_manager.list_agents("t1")
          assert len(agents) == 2
  
      def test_list_agents_empty_team(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          agents = team_manager.list_agents("t1")
          assert agents == []
  
      def test_list_agents_nonexistent_team(self, team_manager):
          agents = team_manager.list_agents("no-team")
          assert agents == []
  
      def test_remove_agent(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          agent = AgentProfile(agent_id="a1", name="A1", role="developer")
          team_manager.add_agent_to_team("t1", agent)
  
          removed = team_manager.remove_agent_from_team("t1", "a1")
          assert removed is not None
          assert removed.name == "A1"
          assert team_manager.get_agent("t1", "a1") is None
  
  
  class TestModelManagement:
      """Model 管理操作测试."""
  
      def test_add_model(self, team_manager, sample_model_dict):
          team_manager.create_team(name="T1", team_id="t1")
          model = ModelConfig(
              model_id="model-001",
              name="deepseek-v4",
              provider="deepseek",
          )
          result = team_manager.add_model_to_team("t1", model)
          assert result is True
  
      def test_add_model_to_nonexistent_team(self, team_manager):
          model = ModelConfig(model_id="m1", name="M1", provider="openai")
          result = team_manager.add_model_to_team("no-team", model)
          assert result is False
  
      def test_remove_model(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          model = ModelConfig(model_id="m1", name="M1", provider="deepseek")
          team_manager.add_model_to_team("t1", model)
  
          removed = team_manager.remove_model_from_team("t1", "m1")
          assert removed is not None
          assert removed.name == "M1"
  
  
  class TestTeamOverview:
      """Team overview 操作测试."""
  
      def test_get_team_overview(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a1", name="A1", role="developer"))
  
          overview = team_manager.get_team_overview("t1")
          assert overview is not None
          assert overview["team_id"] == "t1"
          assert overview["name"] == "T1"
          assert overview["agent_count"] == 1
  
      def test_get_team_overview_nonexistent(self, team_manager):
          overview = team_manager.get_team_overview("no-team")
          assert overview is None
  
  
  class TestDuplicateAgent:
      """Agent 复制功能测试."""
  
      def test_duplicate_agent(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          original = AgentProfile(agent_id="a1", name="Original", role="developer")
          team_manager.add_agent_to_team("t1", original)
  
          clone = team_manager.duplicate_agent("t1", "a1")
          assert clone is not None
          assert "副本" in clone.name
          assert clone.agent_id != original.agent_id
          # 验证克隆已在 team 中
          agents = team_manager.list_agents("t1")
          assert len(agents) == 2
  
      def test_duplicate_nonexistent_agent(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          result = team_manager.duplicate_agent("t1", "nonexistent")
          assert result is None
  
  
  class TestSerialization:
      """序列化操作测试."""
  
      def test_to_dict(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          d = team_manager.to_dict()
          assert "t1" in d
          assert d["t1"]["name"] == "T1"
  
  ```
  
  ### 文件: `src/backend/agents/chat_harness.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Chat Harness — Unified LLM Chat Module.
  
  Inspired by claw-code's QueryEngine + Runtime architecture:
  - Single chat module used by ALL agents, bridge commands, and sessions
  - Provider abstraction: OpenAI-compatible, Anthropic, DeepSeek, local Ollama
  - Session/turn management, token budgeting, transcript compaction
  - Tool invocation pipeline with permission checks
  - Streaming support via SSE-compatible generator
  
  Usage:
      harness = ChatHarness.from_config(config_path="config/settings.json")
      result = await harness.chat(agent_id, prompt, tools=[...])
  
      # Or streaming:
      async for chunk in harness.stream_chat(agent_id, prompt):
          ...
  """
  
  from __future__ import annotations
  
  import json
  import logging
  import os
  import time
  from collections import deque
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from enum import Enum
  from pathlib import Path
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple
  from uuid import uuid4
  
  from .session_store import (
      StoredSession, TranscriptStore,
      save_session, load_session as _load_stored_session,
      list_sessions as _list_stored_sessions,
      search_sessions,
  )
  from .execution_registry import (
      HistoryLog, ToolPermissionContext, PermissionDenial,
      RoutedMatch, ToolPool, assemble_tool_pool,
      PortRuntime, build_execution_registry,
  )
  
  logger = logging.getLogger(__name__)
  
  
  # ═══════════════════════════════════════════════════════════════
  # UltraPlan — Agentic Planning + Execution Pipeline
  # Inspired by Clawith's plan→act→observe→reflect loop
  # ═══════════════════════════════════════════════════════════════
  
  
  class PlanStepStatus(Enum):
      """Status of a single plan step."""
      PENDING = "pending"
      RUNNING = "running"
      COMPLETED = "completed"
      FAILED = "failed"
      SKIPPED = "skipped"
  
  
  @dataclass
  class PlanStep:
      """A single step in an execution plan."""
      step_id: int = 0
      action: str = ""            # e.g. "tool_call", "think", "respond", "delegate"
      tool_name: str = ""         # Tool to invoke (if action == "tool_call")
      tool_args: Dict[str, Any] = field(default_factory=dict)
      description: str = ""       # Human-readable description
      status: PlanStepStatus = PlanStepStatus.PENDING
      result: str = ""
      error: str = ""
      duration_ms: float = 0.0
      depends_on: List[int] = field(default_factory=list)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "step_id": self.step_id,
              "action": self.action,
              "tool_name": self.tool_name,
              "description": self.description,
              "status": self.status.value,
              "result": self.result[:500] if self.result else "",
              "error": self.error,
              "duration_ms": self.duration_ms,
              "depends_on": self.depends_on,
          }
  
  
  @dataclass
  class ExecutionPlan:
      """An ordered plan of steps to fulfill a user request."""
      plan_id: str = field(default_factory=lambda: uuid4().hex[:8])
      goal: str = ""
      steps: List[PlanStep] = field(default_factory=list)
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      status: str = "pending"  # pending / running / completed / failed
      final_response: str = ""
  
      def add_step(self, action: str, description: str = "",
                   tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None,
                   depends_on: Optional[List[int]] = None) -> PlanStep:
          step = PlanStep(
              step_id=len(self.steps) + 1,
              action=action,
              tool_name=tool_name,
              tool_args=tool_args or {},
              description=description,
              depends_on=depends_on or [],
          )
          self.steps.append(step)
          return step
  
      @property
      def completed_steps(self) -> int:
          return sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)
  
      @property
      def progress(self) -> float:
          if not self.steps:
              return 1.0
          return self.completed_steps / len(self.steps)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "plan_id": self.plan_id,
              "goal": self.goal,
              "status": self.status,
              "steps": [s.to_dict() for s in self.steps],
              "progress": round(self.progress, 2),
              "created_at": self.created_at,
          }
  
  
  # Plan builder: analyzes prompt keywords to auto-generate execution steps
  def build_plan_from_prompt(prompt: str, available_tools: List[str] = None) -> ExecutionPlan:
      """Build an execution plan by analyzing the prompt intent.
  
      This is a rule-based planner that maps keywords to tool invocations.
      When an LLM is available, the plan can be refined by the model.
      """
      plan = ExecutionPlan(goal=prompt[:200])
      lower = prompt.lower()
      tools = set(available_tools or [])
  
      # Multi-domain research
      if any(kw in lower for kw in ["研究", "分析", "调研", "research", "investigate"]):
          plan.add_step("tool_call", "网络搜索相关资料", tool_name="web_search",
                         tool_args={"query": prompt[:100]})
          plan.add_step("think", "整理搜索结果")
          plan.add_step("tool_call", "保存研究发现", tool_name="memory_save",
                         tool_args={"key": f"research_{uuid4().hex[:6]}", "content": ""})
          plan.add_step("respond", "生成研究报告")
  
      # General — single-step
      else:
          plan.add_step("think", "理解用户意图")
          plan.add_step("respond", "生成回复")
  
      return plan
  
  
  # Middleware hook type for plan interception
  PlanMiddleware = Callable[[ExecutionPlan], ExecutionPlan]
  
  
  # ═══════════════════════════════════════════════════════════════
  # Provider Abstraction
  # ═══════════════════════════════════════════════════════════════
  
  
  class LLMProvider(Enum):
      """Supported LLM providers."""
      OPENAI = "openai"
      ANTHROPIC = "anthropic"
      DEEPSEEK = "deepseek"
      OPENROUTER = "openrouter"
      LOCAL = "local"         # Ollama / vLLM / local OpenAI-compatible
      GITHUB = "github"       # GitHub Copilot models
      QWEN = "qwen"
  
  
  @dataclass
  class ProviderConfig:
      """LLM provider connection configuration."""
      provider: LLMProvider = LLMProvider.DEEPSEEK
      api_key: str = ""
      api_base_url: str = ""
      model: str = "deepseek-v4-flash"
      max_tokens: int = 65536  # DeepSeek V4: 64K output
      temperature: float = 0.2
      timeout: float = 1200.0  # Long timeout for big code generations
      thinking: Optional[Dict[str, str]] = None  # e.g. {"type": "enabled"}
      reasoning_effort: str = ""  # "low" | "medium" | "high"
  
      # Default endpoints per provider
      _DEFAULT_URLS: dict = field(default_factory=lambda: {
          LLMProvider.OPENAI: "https://api.openai.com/v1",
          LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
          LLMProvider.DEEPSEEK: "https://api.deepseek.com",
          LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
          LLMProvider.LOCAL: "http://127.0.0.1:11434/v1",
          LLMProvider.GITHUB: "https://models.inference.ai.azure.com",
          LLMProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
      }, repr=False)
  
      def resolve_base_url(self) -> str:
          if self.api_base_url:
              return self.api_base_url.rstrip("/")
          return self._DEFAULT_URLS.get(self.provider, "http://127.0.0.1:11434/v1")
  
      @classmethod
      def from_env(cls) -> "ProviderConfig":
          """Build config from environment variables."""
          provider_str = os.getenv("AG_LLM_PROVIDER", "deepseek")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.DEEPSEEK
  
          return cls(
              provider=provider,
              api_key=os.getenv("AG_LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
              api_base_url=os.getenv("AG_LLM_BASE_URL", ""),
              model=os.getenv("AG_LLM_MODEL", "deepseek-v4-flash"),
              max_tokens=int(os.getenv("AG_LLM_MAX_TOKENS", "65536")),
              temperature=float(os.getenv("AG_LLM_TEMPERATURE", "0.2")),
              thinking={"type": "enabled"},
              reasoning_effort="high",
          )
  
      @classmethod
      def from_settings(cls, settings: Dict[str, Any]) -> "ProviderConfig":
          """Build from config/settings.json llm section."""
          llm = settings.get("llm", {})
          provider_str = llm.get("provider", "local")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.LOCAL
  
          return cls(
              provider=provider,
              api_key=llm.get("api_key", os.getenv("DEEPSEEK_API_KEY", "")),
              api_base_url=llm.get("local", llm.get("api_base_url", "")),
              model=llm.get("model", "deepseek-v4-flash"),
              max_tokens=llm.get("max_tokens", 65536),
              temperature=llm.get("temperature", 0.2),
              thinking=llm.get("thinking"),
              reasoning_effort=llm.get("reasoning_effort", ""),
          )
  
      @classmethod
      def from_model_config(cls, model_config: Any) -> "ProviderConfig":
          """Build from agents.models.ModelConfig."""
          provider_str = getattr(model_config, "provider", "deepseek")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.DEEPSEEK
  
          return cls(
              provider=provider,
              api_key=getattr(model_config, "api_key", ""),
              api_base_url=getattr(model_config, "api_base_url", ""),
              model=getattr(model_config, "name", "deepseek-v4-flash"),
              max_tokens=getattr(model_config, "max_tokens", 65536),
              temperature=getattr(model_config, "temperature", 0.2),
              thinking={"type": "enabled"},
              reasoning_effort="high",
          )
  
  
  # ═══════════════════════════════════════════════════════════════
  # Turn / Session Data Models
  # ═══════════════════════════════════════════════════════════════
  
  
  @dataclass
  class UsageSummary:
      """Token usage tracking (mirrors claw-code UsageSummary)."""
      input_tokens: int = 0
      output_tokens: int = 0
      total_tokens: int = 0
  
      def add(self, inp: int, out: int) -> "UsageSummary":
          return UsageSummary(
              input_tokens=self.input_tokens + inp,
              output_tokens=self.output_tokens + out,
              total_tokens=self.total_tokens + inp + out,
          )
  
      def to_dict(self) -> Dict[str, int]:
          return {
              "input_tokens": self.input_tokens,
              "output_tokens": self.output_tokens,
              "total_tokens": self.total_tokens,
          }
  
  
  @dataclass
  class ToolInvocation:
      """A tool call extracted from the LLM response."""
      tool_name: str = ""
      arguments: Dict[str, Any] = field(default_factory=dict)
      result: str = ""
      permitted: bool = True
      denial_reason: str = ""
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tool_name": self.tool_name,
              "arguments": self.arguments,
              "result": self.result,
              "permitted": self.permitted,
              "denial_reason": self.denial_reason,
          }
  
  
  @dataclass
  class TurnResult:
      """Result of a single chat turn (mirrors claw-code TurnResult)."""
      prompt: str = ""
      response: str = ""
      usage: UsageSummary = field(default_factory=UsageSummary)
      tool_invocations: List[ToolInvocation] = field(default_factory=list)
      stop_reason: str = "completed"
      model: str = ""
      provider: str = ""
      latency_ms: float = 0.0
      error: str = ""
      timestamp: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "prompt": self.prompt,
              "response": self.response,
              "usage": self.usage.to_dict(),
              "tool_invocations": [t.to_dict() for t in self.tool_invocations],
              "stop_reason": self.stop_reason,
              "model": self.model,
              "provider": self.provider,
              "latency_ms": self.latency_ms,
              "error": self.error,
              "timestamp": self.timestamp,
          }
  
  
  @dataclass
  class ChatMessage:
      """A single message in a conversation."""
      role: str = "user"  # user | assistant | system | tool
      content: str = ""
      name: str = ""
      tool_calls: List[Dict[str, Any]] = field(default_factory=list)
      timestamp: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
  
      def to_openai_dict(self) -> Dict[str, Any]:
          d: Dict[str, Any] = {"role": self.role, "content": self.content}
          if self.name:
              d["name"] = self.name
          return d
  
  
  @dataclass
  class ChatSession:
      """Stateful conversation session with compaction, history & transcript.
  
      Integrates claw-code-parity patterns:
      - HistoryLog for event tracking
      - TranscriptStore for persistence & replay
      - Permission tracking
      """
      session_id: str = field(default_factory=lambda: uuid4().hex[:12])
      agent_id: str = ""
      system_prompt: str = ""
      messages: List[ChatMessage] = field(default_factory=list)
      total_usage: UsageSummary = field(default_factory=UsageSummary)
      turn_count: int = 0
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      max_turns: int = 100
      compact_after: int = 40
      # claw-code-parity extensions
      history: HistoryLog = field(default_factory=HistoryLog)
      transcript: TranscriptStore = field(default_factory=TranscriptStore)
      permission_denials: List[PermissionDenial] = field(default_factory=list)
  
      def add_user_message(self, content: str) -> None:
          self.messages.append(ChatMessage(role="user", content=content))
          self.transcript.append(content)
          self.history.add("user_message", content[:100])
  
      def add_assistant_message(self, content: str) -> None:
          self.messages.append(ChatMessage(role="assistant", content=content))
          self.turn_count += 1
          self.transcript.append(content)
          self.history.add("assistant_message", f"turn={self.turn_count}")
  
      def compact_if_needed(self) -> None:
          """Keep conversation manageable by dropping old turns."""
          if len(self.messages) > self.compact_after:
              # Keep system prompt context (first msg if system) + last N messages
              keep = self.compact_after // 2
              sys_msgs = [m for m in self.messages[:1] if m.role == "system"]
              self.messages = sys_msgs + self.messages[-keep:]
  
      def build_openai_messages(self) -> List[Dict[str, Any]]:
          """Build the messages array for OpenAI-compatible API calls."""
          msgs = []
          if self.system_prompt:
              msgs.append({"role": "system", "content": self.system_prompt})
          msgs.extend(m.to_openai_dict() for m in self.messages)
          return msgs
  
      def persist(self) -> str
  ```
  
  ### 文件: `src/backend/agents/hermes_research.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 — Hermes-style Research Agent Module.
  
  Transforms the Research Agent from a read-only advisory role into a
  self-improving research agent inspired by NousResearch/hermes-agent:
  
  Architecture mapping (Hermes → AgentsGroup2026):
    - AIAgent class         → HermesResearchAgent
    - run_conversation()    → agent_loop()
    - toolsets.py           → RESEARCH_TOOLSET_DISTRIBUTIONS
    - prompt_builder.py     → build_research_system_prompt()
    - SOUL.md               → agent.hermes_config.soul_md
    - Memory/Skills nudge   → MEMORY_GUIDANCE / SKILLS_GUIDANCE
    - Delegate subagents    → delegate_task()
    - Session search        → session_search()
  
  Key Hermes characteristics adopted:
    1. Closed learning loop — auto-create skills from complex research
    2. Persistent memory — save research findings across sessions
    3. Probabilistic toolset distribution — web 90%, browser 70%, vision 50%
    4. SOUL.md — research persona
    5. Context files — AGENTS.md project context
    6. Tool-use enforcement — tools must be used, not just described
    7. Session search — cross-session recall of past research
  """
  
  from __future__ import annotations
  
  import random
  from dataclasses import dataclass, field
  from typing import Any, Dict, List, Optional
  
  from .models import (
      AgentProfile,
      AgentTemplateType,
      AgentPersonality,
      HermesAgentConfig,
      ToolsetDistribution,
  )
  
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style Toolset Distributions
  # Inspired by NousResearch/hermes-agent/toolset_distributions.py
  # ══════════════════════════════════════════════════════════════
  
  RESEARCH_TOOLSET_DISTRIBUTIONS: Dict[str, Dict[str, Any]] = {
      "general_research": {
          "description": "General domain research — literature review, data analysis, technical investigation",
          "toolsets": {
              "web": 90,
              "browser": 70,
              "vision": 50,
              "file": 80,
              "research": 95,
              "memory": 100,
              "skills": 100,
              "delegation": 30,
          },
      },
      "deep_analysis": {
          "description": "Deep analysis — systematic review, data verification, cross-referencing",
          "toolsets": {
              "web": 60,
              "file": 95,
              "research": 100,
              "code_execution": 80,
              "memory": 100,
              "vision": 40,
          },
      },
      "compliance_audit": {
          "description": "Standards and compliance verification",
          "toolsets": {
              "web": 85,
              "browser": 65,
              "file": 90,
              "research": 100,
              "code_execution": 70,
              "memory": 100,
          },
      },
      "technical_review": {
          "description": "Technical design review, architecture analysis, code review",
          "toolsets": {
              "web": 50,
              "file": 95,
              "code_execution": 90,
              "research": 100,
              "vision": 70,
              "memory": 100,
          },
      },
      "general_research": {
          "description": "General web research with all tools available",
          "toolsets": {
              "web": 90,
              "browser": 70,
              "vision": 50,
              "memory": 100,
              "skills": 100,
              "file": 60,
              "code_execution": 30,
          },
      },
  }
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style Toolset Definitions
  # Inspired by NousResearch/hermes-agent/toolsets.py
  # ══════════════════════════════════════════════════════════════
  
  HERMES_TOOLSETS: Dict[str, Dict[str, Any]] = {
      "web": {
          "description": "Web research and content extraction",
          "tools": ["web_search", "extract_content"],
      },
      "browser": {
          "description": "Browser automation for deep research",
          "tools": ["navigate_url", "screenshot", "click_element", "fill_form", "extract_content", "web_search"],
      },
      "file": {
          "description": "File read/write/search operations",
          "tools": ["read_file", "write_file", "list_directory", "search_files"],
      },
      "code_execution": {
          "description": "Run Python/shell for analysis and calculation",
          "tools": ["run_python", "run_shell"],
      },
      "vision": {
          "description": "Image/chart analysis for technical documents",
          "tools": ["screenshot"],
      },
      "research": {
          "description": "Research-specific tools — search, analysis, data retrieval",
          "tools": ["search_query", "data_lookup", "info_fetch", "analysis_engine"],
      },
      "memory": {
          "description": "Persistent memory and session search",
          "tools": ["memory_save", "memory_read", "session_search"],
      },
      "skills": {
          "description": "Skill management — list, view, create, patch",
          "tools": ["skill_list", "skill_view", "skill_manage"],
      },
      "delegation": {
          "description": "Spawn subagents for parallel research tasks",
          "tools": ["delegate_task"],
      },
  }
  
  
  def sample_toolsets(distribution_name: str) -> List[str]:
      """Sample toolsets based on distribution probabilities.
  
      Each toolset rolls independently — multiple can be active.
      Mirrors NousResearch/hermes-agent/toolset_distributions.py logic.
      """
      dist = RESEARCH_TOOLSET_DISTRIBUTIONS.get(distribution_name)
      if not dist:
          dist = RESEARCH_TOOLSET_DISTRIBUTIONS["general_research"]
  
      selected = []
      for toolset_name, probability in dist["toolsets"].items():
          if random.random() * 100 < probability:
              selected.append(toolset_name)
  
      # Ensure at least one toolset
      if not selected and dist["toolsets"]:
          highest = max(dist["toolsets"].items(), key=lambda x: x[1])
          selected.append(highest[0])
  
      return selected
  
  
  def resolve_tools(toolset_names: List[str]) -> List[str]:
      """Resolve toolset names to individual tool IDs."""
      tools: set[str] = set()
      for name in toolset_names:
          ts = HERMES_TOOLSETS.get(name)
          if ts:
              tools.update(ts["tools"])
      return sorted(tools)
  
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style System Prompt Builder
  # Inspired by NousResearch/hermes-agent/agent/prompt_builder.py
  # ══════════════════════════════════════════════════════════════
  
  MARINE_RESEARCHER_IDENTITY = (
      "You are AgentsGroup2026 Research Agent, an intelligent research agent "
      "built on the Herme
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose (完整产出)
  
  # PM分解 — project_manager
  
  任务: 设计操作事件表和情境切片关联表数据模型，完成建表与存储逻辑，确保操作序列不可变、情境切片可追溯
  步骤: pm_decompose
  Agent: build_pm
  
  ---
  
  📋 任务: 1f0da2f7-522
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 PM (project_manager)。
    请执行以下开发任务:
    
    你是项目经理 (PM)。请对以下任务进行分解和规划:
    
    ## 任务
    设计操作事件表和情境切片关联表数据模型，完成建表与存储逻辑，确保操作序列不可变、情境切片可追溯
    Architect + 全栈开发
    
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
    ... (共 727 个 src/ 文件)
    
    ```
    
    ### 文件: `src/frontend/system-evolution.html`
    ```html
    <!DOCTYPE html>
    <html lang="zh-CN" data-obc-theme="dusk">
    <head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
    <title>系统演进 — AgentsGroup2026</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Noto+Serif+SC:wght@200;300;400;600;900&family=JetBrains+Mono:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
    :root{
      --shironeri:oklch(0.96 0.003 110);--ishi:oklch(0.91 0.004 110);--kabe:oklch(0.85 0.005 110);
      --hai:oklch(0.78 0.005 110);--nezumi:oklch(0.68 0.006 110);--sumi:oklch(0.18 0.008 110);
      --sumi-2:oklch(0.38 0.006 110);--sumi-3:oklch(0.55 0.005 110);
      --koke:oklch(0.52 0.04 160);--shu:oklch(0.48 0.07 22);--kitsune:oklch(0.56 0.05 70);
      --groove:oklch(0.82 0.004 110);
      --font-serif:'Noto Serif SC',serif;--font-sans:'Noto Sans SC',sans-serif;--font-mono:'JetBrains Mono',monospace;
      --lime:oklch(0.52 0.04 160);--cyan:oklch(0.52 0.04 160);--amber:oklch(0.56 0.05 70);--red:oklch(0.48 0.07 22);
      --muted:oklch(0.55 0.005 110);--dim:oklch(0.55 0.005 110);
    }
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    body{font-family:var(--font-sans);min-height:100vh;background:var(--shironeri);color:var(--sumi);position:relative}
    body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
      background-image:radial-gradient(oklch(0 0 0/.012) 1px,transparent 1px),radial-gradient(oklch(0 0 0/.008) 1px,transparent 1px);
      background-size:5px 5px,7px 7px;background-position:0 0,3px 3px}
    a{color:var(--koke);text-decoration:none}
    .seal{display:inline-block;font-size:10px;font-weight:900;color:var(--shironeri);background:var(--sumi);padding:1px 5px;line-height:1.3;font-family:var(--font-serif);vertical-align:middle;margin-right:4px}
    .seal-koke{background:var(--koke)}.seal-shu{background:var(--shu)}.seal-kitsune{background:var(--kitsune)}
    
    /* Layout */
    .app{display:flex;height:100vh;overflow:hidden;position:relative;z-index:1}
    .sidebar{width:260px;min-width:260px;background:var(--ishi);border-right:1px solid var(--groove);display:flex;flex-direction:column;overflow:hidden}
    .main{flex:1;display:flex;flex-direction:column;overflow:hidden}
    .topbar{display:flex;justify-content:space-between;align-items:center;padding:12px 28px;border-bottom:1px solid var(--groove);background:var(--shironeri);min-height:56px}
    .topbar-left{display:flex;align-items:center;gap:12px}
    .topbar-left h1{font-size:18px;font-weight:600}
    .topbar-right{display:flex;gap:8px;align-items:center}
    .main-scroll{flex:1;overflow-y:auto;padding:24px 28px;min-height:0}
    
    /* Sidebar */
    .sb-header{padding:16px;border-bottom:1px solid var(--groove)}
    .sb-header h2{font-size:15px;color:var(--koke);display:flex;align-items:center;gap:6px}
    .sb-nav{display:flex;flex-direction:column;gap:2px;padding:8px}
    .sb-nav a{padding:8px 12px;font-size:13px;color:var(--muted);cursor:pointer;display:flex;align-items:center;gap:8px;transition:.15s}
    .sb-nav a:hover{background:oklch(0 0 0/.03);color:var(--sumi)}
    .sb-nav a.active{background:oklch(0.48 0.07 22/.06);color:var(--shu);font-weight:600}
    .sb-section{padding:8px 12px;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin-top:8px;font-weight:600}
    .sb-footer{padding:12px;border-top:1px solid var(--groove);margin-top:auto}
    
    /* Buttons */
    .btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;border:1px solid var(--groove);font-family:inherit;transition:.15s;background:transparent;color:var(--koke)}.btn:hover{background:oklch(0 0 0/.03)}
    .btn-primary{background:var(--sumi);color:var(--shironeri);border-color:transparent}.btn-primary:hover{background:oklch(0.28 0.008 110)}
    .btn-danger{color:var(--shu);border-color:oklch(0.48 0.07 22/.3)}.btn-danger:hover{background:oklch(0.48 0.07 22/.06)}
    .btn-sm{padding:5px 12px;font-size:12px}
    .btn-ghost{border:none;padding:6px 10px}
    
    /* Cards */
    .card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px;margin-bottom:20px}
    .stat-card{background:var(--ishi);border:1px solid var(--groove);padding:16px}
    .stat-card .label{font-size:12px;color:var(--muted);margin-bottom:6px;display:flex;align-items:center;gap:6px}
    .stat-card .value{font-size:24px;font-weight:700;font-family:var(--font-mono);color:var(--sumi)}
    .stat-card .sub{font-size:11px;color:var(--dim);margin-top:4px}
    
    /* Table */
    .tbl{width:100%;border-collapse:collapse;font-size:13px}
    .tbl th{text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;color:var(--dim);border-bottom:1px solid var(--groove);letter-spacing:.5px;font-weight:500}
    .tbl td{padding:10px;border-bottom:1px solid oklch(0 0 0/.04);color:var(--sumi)}
    .tbl tr:hover td{background:oklch(0 0 0/.02)}
    .chip{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;font-size:11px;background:oklch(0 0 0/.03);color:var(--koke);border:1px solid var(--groove);margin:2px}
    .section{margin-bottom:24px}
    .section-title{font-size:16px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;gap:8px}
    .toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;background:var(--ishi);border:1px solid var(--groove);font-size:13px;opacity:0;transition:.3s;pointer-events:none;z-index:999;color:var(--sumi)}.toast.show{opacity:1}
    
    /* Ratchet Flow Diagram */
    .ratchet-flow{display:flex;align-items:center;gap:0;padding:20px 0;overflow-x:auto}
    .ratchet-node{display:flex;flex-direction:column;align-items:center;min-width:130px}
    .ratchet-dot{width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:900;border:2px solid var(--groove);background:var(--shironeri);font-family:var(--font-serif);transition:.35s;position:relative}
    .ratchet-dot.active{border-color:var(--koke);box-shadow:0 0 0 3px oklch(0.52 0.04 160/.15),0 0 20px oklch(0.52 0.04 160/.25);animation:r-pulse 2s ease-in-out infinite}
    .ratchet-dot.done{border-color:var(--koke);background:oklch(0.52 0.04 160/.08);color:var(--koke)}
    .ratchet-dot.failed{border-color:var(--shu);background:oklch(0.48 0.07 22/.08);color:var(--shu)}
    @keyframes r-pulse{0%,100%{box-shadow:0 0 0 3px oklch(0.52 0.04 160/.15)}50%{box-shadow:0 0 0 3px oklch(0.52 0.04 160/.3),0 0 24px oklch(0.52 0.04 160/.2)}}
    .ratchet-label{font-size:11px;color:var(--muted);margin-top:6px;text-align:center;font-weight:500}
    .ratchet-sublabel{font-size:10px;color:var(--dim);margin-top:2px;font-family:var(--font-mono)}
    .ratchet-connector{width:40px;height:2px;background:var(--groove);flex-shrink:0}
    .ratchet-connector.done{background:var(--koke)}
    .ratchet-lock{border-color:var(--kitsune) !important}
    .ratchet-lock .ratchet-dot{border-color:var(--kitsune);color:var(--kitsune)}
    
    /* Compliance Gauge */
    .gauge-wrap{display:flex;align-items:center;gap:20px}
    .gauge-ring{position:relative;width:80px;height:80px;flex-shrink:0}
    .gauge-ring svg{width:80px;height:80px;transform:rotate(-90deg)}
    .gauge-grade{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;font-family:var(--font-mono)}
    
    /* Cycle log */
    .cycle-log{background:var(--ishi);border:1px solid var(--groove);padding:12px 16px;font-family:var(--font-mono);font-size:12px;line-height:1.8;max-height:200px;overflow-y:auto;margin-top:12px}
    .cycle-log .ok{color:var(--koke)}.cycle-log .err{color:var(--shu)}.cycle-log .run{color:var(--kitsune)}
    
    /* Heritage ledger */
    .heritage-item{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:var(--ishi);border:1px solid var(--groove);margin-bottom:6px;font-size:13px}
    .heritage-item .h-title{font-weight:600;font-size:13px}
    .heritage-item .h-meta{font-size:11px;color:var(--muted);font-family:var(--font-mono)}
    .heritage-item .h-delta{font-family:var(--font-mono);font-size:13px;font-weight:700;color:var(--koke);white-space:nowrap}
    
    /* Zone badge */
    .zone-badge{padding:8px 14px;background:oklch(0.52 0.04 160/.06);border:1px solid oklch(0.52 0.04 160/.15);display:inline-flex;align-items:center;gap:8px;font-size:12px;margin:4px}
    .zone-badge b{color:var(--sumi)}
    
    /* Rule card */
    .rule-card{padding:10px 14px;background:var(--ishi);border:1px solid var(--groove)}
    .rule-card .r-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
    .rule-card .r-id{font-size:12px;font-weight:700;font-family:var(--font-mono)}
    .rule-card .r-title{font-size:12px;margin-top:2px}
    .rule-card .r-ref{font-size:11px;color:var(--dim);margin-top:2px}
    .rule-card .r-meta{font-size:11px;margin-top:4px}
    .rule-card .r-actions{display:flex;gap:6px;margin-top:6px;justify-content:flex-end}
    .rule-card .r-actions button{padding:2px 8px;font-size:11px;cursor:pointer;border:1px solid var(--groove);background:transparent;color:var(--ink);border-radius:3px}
    .rule-card .r-actions button:hover{background:var(--groove)}
    .rule-card .r-actions .btn-del{color:var(--shu);border-color:oklch(0.48 0.07 22/.3)}
    .rule-card .r-actions .btn-del:hover{background:oklch(0.48 0.07 22/.08)}
    /* Edit Rule Modal */
    .rule-modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:1000;display:flex;align-items:center;justify-content:center}
    .rule-modal{background:var(--bg);border:1px solid var(--groove);padding:20px 24px;min-width:380px;max-width:500px;border-radius:6px}
    .rule-modal h3{margin:0 0 14px;font-size:14px;font-weight:600}
    .rule-modal label{display:block;font-size:12px;color:var(--dim);margin:8px 0 3px}
    .rule-modal input,.rule-modal select,.rule-modal textarea{width:100%;padding:6px 8px;font-size:12px;border:1px solid var(--groove);background:var(--ishi);color:var(--ink);border-radius:3px;box-sizing:border-box}
    .rule-modal textarea{min-height:60px;resize:vertical}
    .rule-modal .modal-btns{display:flex;gap:8px;justify-content:flex-end;margin-top:16px}
    
    /* Tabs */
    .tab-bar{display:flex;gap:0;border-bottom:1px solid var(--groove);margin-bottom:20px}
    .tab-btn{padding:10px 18px;font-size:13px;cursor:pointer;color:var(--muted);border:none;border-bottom:2px solid transparent;background:none;font-family:inherit;font-weight:500;transition:.15s}
    .tab-btn:hover{color:var(--sumi)}
    .tab-btn.active{color:var(--shu);border-bottom-color:var(--shu);font-weight:600}
    .tab-panel{display:none}.tab-panel.active{display:block}
    
    /* Filter bar */
    .filter-bar{display:flex;gap:8px;align-items:center;margin-bottom:16px;flex-wrap:wrap}
    .filter-bar select,.filter-bar input{padding:6px 10px;font-size:12px;border:1px solid var(--groove);background:var(--shironeri);color:var(--sumi);font-family:inherit}
    .filter-bar select:focus,.filter-bar input:focus{outline:none;border-color:var(--koke)}
    
    /* Trend placeholder */
    .trend-chart{background:var(--ishi);border:1px solid var(--groove);padding:20px;min-height:120px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px}
    .audit-entry{padding:8px 12px;border-bottom:1px solid oklch(0 0 0/.04);font-size:12px;display:flex;gap:12px;align-items:center}
    .audit-entry .ae-time{font-family:var(--font-mono);color:var(--dim);font-size:11px;min-width:140px}
    .audit-entry .ae-type{font-weight:600;min-width:80px}
    .audit-entry .ae-detail{color:var(--sumi-2);flex:1}
    </style>
    </head>
    <body>
    <div class="app">
      <!-- Sidebar -->
      <div class="sidebar">
        <div class="sb-header">
          <h2><span class="seal seal-koke">演</span> 系统演进</h2>
        </div>
        <div class="sb-nav">
          <a class="active" onclick="switchPanel('overview')"><span class="seal">览</span> 演进概览</a>
          <a onclick="switchPanel('rules')"><span class="seal">规</span> 审查规则</a>
          <a onclick="switchPanel('items')"><span class="seal seal-shu">项</span> 演进条目</a>
          <a onclick="switchPanel('zones')"><span class="seal seal-koke">域</span> 合规区域</a>
          <a onclick="switchPanel('trail')"><span class="seal">迹</span> 审计轨迹</a>
        </div>
        <div class="sb-section">操作</div>
        <div style="padding:8px 12px;display:flex;flex-direction:column;gap:6px">
          <button class="btn btn-sm" onclick="runAudit()">🔍 运行审查</button>
          <button class="btn btn-sm btn-primary" onclick="runCycleOnRatchet()">▶ 演进周期</button>
          <button class="btn btn-sm" onclick="recalcRating()">📊 重算评级</button>
        </div>
        <div class="sb-footer">
          <a href="/skill-extract.html" class="btn btn-ghost btn-sm" style="width:100%;justify-content:center;margin-bottom:6px"><span class="seal seal-shu">萃</span> 技能萃取</a>
          <a href="/agent-team-config.html" class="btn btn-ghost btn-sm" style="width:100%;justify-content:center">← 返回团队管理</a>
        </div>
      </div>
    
      <!-- Main Content -->
      <div class="main">
        <div class="topbar">
          <div class="topbar-left">
            <h1 id="panel-title">演进概览</h1>
            <span id="panel-badge" style="font-size:11px;padding:2px 8px;background:oklch(0.52 0.04 160/.1);color:var(--koke);font-family:var(--font-mono)"></span>
          </div>
          <div class="topbar-right">
            <span id="executor-status" style="font-size:11px;color:var(--muted);cursor:pointer" onclick="showExecutorStatus()" title="执行器状态"></span>
            <span id="last-audit" style="font-size:11px;color:var(--muted)"></span>
            <a href="/skill-extract.html" class="btn btn-sm"><span class="seal seal-shu">萃</span> 萃取</a>
            <button class="btn btn-sm" onclick="refreshAll()">↻ 刷新</button>
          </div>
        </div>
        <div class="main-scroll" id="content">
    
          <!-- ═══ Overview Panel ═══ -->
          <div id="panel-overview" class="tab-panel active">
            <!-- Compliance Rating -->
            <div class="section">
              <div class="section-title">合规评级</div>
              <div id="ov-rating" class="card-grid"></div>
            </div>
            <!-- Stats -->
            <div class="section">
              <div class="section-title">演进统计</div>
              <div id="ov-stats" class="card-grid"></div>
            </div>
            <!-- 达尔文棘轮 — 五步闭环 -->
            <div class="section">
              <div class="section-title">🔄 达尔文棘轮 — 不可逆演进机制</div>
              <p style="font-size:12px;color:var(--sumi-2);margin-bottom:12px;line-height:1.6">
                棘轮机制确保系统只能向前演进，永不回退。通过验证的改进被锁定为「遗产」— <b>append-only</b> 不可变记录。
              </p>
              <div class="ratchet-flow" id="ratchet-flow">
                <div class="ratchet-node">
                  <div class="ratchet-dot" id="r-audit">审</div>
                  <div class="ratchet-label">① 审查</div>
                  <div class="ratchet-sublabel">AUDIT</div>
                </div>
                <div class="ratchet-connector" id="rc-1"></div>
                <div class="ratchet-node">
                  <div class="ratchet-dot" id="r-dispatch">派</div>
                  <div class="ratchet-label">② 派发</div>
                  <div class="ratchet-sublabel">DISPATCH</div>
                </div>
                <div class="ratchet-connector" id="rc-2"></div>
                <div class="ratchet-node">
                  <div class="ratchet-dot" id="r-verify">验</div>
                  <div class="ratchet-label">③ 验证</div>
                  <div class="ratchet-sublabel">VERIF
    ```
    
    ### 文件: `src/backend/tests/test_agent_toolbox.py`
    ```py
    # -*- coding: utf-8 -*-
    """AgentToolbox 单元测试 — 工具函数 (read_file, grep, list_files, dispatch)."""
    
    from __future__ import annotations
    
    import json
    import os
    import tempfile
    from pathlib import Path
    
    import pytest
    
    from agents.agent_toolbox import (
        TOOL_SCHEMA,
        dispatch_tool_call,
        get_tools_for_role,
        tool_grep,
        tool_list_files,
        tool_patch_file,
        tool_read_file,
        tool_run_python,
        tool_run_pytest,
        tool_write_file,
    )
    
    
    # ═══════════════════════════════════════════════════
    # read_file 测试
    # ═══════════════════════════════════════════════════
    
    class TestToolReadFile:
        """tool_read_file 单元测试."""
    
        def test_read_existing_file(self):
            result = tool_read_file("src/backend/tests/__init__.py")
            assert result["ok"] is True
            assert "Test Pipeline" in result["content"]
    
        def test_read_with_line_range(self):
            result = tool_read_file(
                "src/backend/tests/__init__.py",
                start_line=1,
                end_line=3,
            )
            assert result["ok"] is True
            assert result["total_lines"] > 0
    
        def test_read_nonexistent_file(self):
            result = tool_read_file("nonexistent/file.txt")
            assert result["ok"] is False
    
        def test_read_empty_path_raises(self):
            result = tool_read_file("")
            assert result["ok"] is False
    
    
    # ═══════════════════════════════════════════════════
    # grep 测试
    # ═══════════════════════════════════════════════════
    
    class TestToolGrep:
        """tool_grep 单元测试."""
    
        def test_grep_finds_matches(self):
            result = tool_grep(r"class.*Test", include="src/backend/tests/*.py")
            assert result["ok"] is True
            assert len(result["hits"]) > 0
            for hit in result["hits"]:
                assert "path" in hit
                assert "line" in hit
                assert "text" in hit
    
        def test_grep_no_matches(self):
            result = tool_grep(r"XYZZY_NOT_FOUND_12345", include="src/backend/tests/*.py")
            assert result["ok"] is True
            assert len(result["hits"]) == 0
    
        def test_grep_bad_regex(self):
            result = tool_grep(r"[invalid")
            assert result["ok"] is False
            assert "bad regex" in result["error"]
    
        def test_grep_max_hits(self):
            result = tool_grep(r"def ", include="src/backend/agents/*.py", max_hits=3)
            assert result["ok"] is True
            assert len(result["hits"]) <= 3
    
    
    # ═══════════════════════════════════════════════════
    # list_files 测试
    # ═══════════════════════════════════════════════════
    
    class TestToolListFiles:
        """tool_list_files 单元测试."""
    
        def test_list_tests_directory(self):
            result = tool_list_files("src/backend/tests")
            assert result["ok"] is True
            files = result["files"]
            assert any("__init__.py" in f for f in files)
            assert any("conftest.py" in f for f in files)
    
        def test_list_nonexistent_directory(self):
            result = tool_list_files("nonexistent/dir")
            assert result["ok"] is False
    
        def test_list_with_depth(self):
            result = tool_list_files("src/backend", max_depth=1)
            assert result["ok"] is True
            # 不应深入到 agents/ 子目录
            for f in result["files"]:
                assert "/agents/" not in f or f.count("/") <= 2
    
    
    # ═══════════════════════════════════════════════════
    # write_file / patch_file 测试
    # ═══════════════════════════════════════════════════
    
    class TestToolWriteFile:
        """tool_write_file 单元测试."""
    
        def test_write_new_file(self):
            result = tool_write_file(
                "tests/_test_write_temp.txt",
                "hello world",
            )
            assert result["ok"] is True
            assert result["path"] == "tests/_test_write_temp.txt"
            # 清理
            Path("src/backend/tests/_test_write_temp.txt").unlink(missing_ok=True)
    
        def test_write_outside_allowed_fails(self):
            result = tool_write_file(
                "../outside.txt",
                "should fail",
            )
            assert result["ok"] is False
    
        def test_create_only_existing(self):
            # conftest.py 已存在
            result = tool_write_file(
                "tests/conftest.py",
                "new content",
                create_only=True,
            )
            assert result["ok"] is False
            assert "create_only" in result["error"]
    
    
    class TestToolPatchFile:
        """tool_patch_file 单元测试."""
    
        def test_patch_unique_match(self):
            # 先创建临时文件
            tmp_path = "tests/_test_patch_temp.py"
            tool_write_file(tmp_path, "original line\nother line\n")
    
            result = tool_patch_file(
                tmp_path,
                search="original line",
                replace="patched line",
            )
            assert result["ok"] is True
    
            # 验证修改
            read_back = tool_read_file(tmp_path)
            assert "patched line" in read_back["content"]
    
            # 清理
            Path("src/backend/tests/_test_patch_temp.py").unlink(missing_ok=True)
    
        def test_patch_not_found(self):
            result = tool_patch_file(
                "tests/conftest.py",
                search="NOT_IN_THIS_FILE_XYZ",
                replace="whatever",
            )
            assert result["ok"] is False
    
        def test_patch_outside_allowed(self):
            result = tool_patch_file(
                "../outside.txt",
                search="x",
                replace="y",
            )
            assert result["ok"] is False
    
    
    # ═══════════════════════════════════════════════════
    # run_python 测试
    # ═══════════════════════════════════════════════════
    
    class TestToolRunPython:
        """tool_run_python 单元测试."""
    
        def test_simple_expression(self):
            result = tool_run_python("print(1+1)")
            assert result["ok"] is True
            assert result["exit_code"] == 0
            assert "2" in result["stdout"]
    
        def test_import_check(self):
            result = tool_run_python("from agents.models import AgentProfile; print('OK')")
            assert result["ok"] is True
            assert "OK" in result["stdout"]
    
        def test_syntax_error(self):
            result = tool_run_python("def broken(")
            assert result["ok"] is True  # subprocess 成功执行
            assert result["exit_code"] != 0
    
    
    # ═══════════════════════════════════════════════════
    # run_pytest 测试
    # ═══════════════════════════════════════════════════
    
    class TestToolRunPytest:
        """tool_run_pytest 单元测试."""
    
        def test_run_pytest_collect_only(self):
            result = tool_run_pytest("tests/test_models.py --co")
            assert result["ok"] is True
    
    
    # ═══════════════════════════════════════════════════
    # dispatch_tool_call 测试
    # ═══════════════════════════════════════════════════
    
    class TestDispatchToolCall:
        """dispatch_tool_call 单元测试."""
    
        def test_dispatch_read_file(self):
            result = dispatch_tool_call(
                "read_file",
                json.dumps({"path": "src/backend/tests/__init__.py"}),
            )
            assert result["ok"] is True
    
        def test_dispatch_finish(self):
            result = dispatch_tool_call("finish", "{}")
            assert result["ok"] is True
            assert result["_finished"] is True
    
        def test_dispatch_unknown_tool(self):
            result = dispatch_tool_call("unknown_tool", "{}")
            assert result["ok"] is False
    
        def test_dispatch_bad_json_args(self):
            result = dispatch_tool_call("read_file", "not json")
            assert result["ok"] is False
    
        def test_dispatch_bad_kwargs(self):
            result = dispatch_tool_call(
                "read_file",
                json.dumps({"path": "tests/__init__.py", "extra_bad_kwarg": True}),
            )
            # Either ok=False due to TypeError, or ok=True (if extra kwarg ignored)
            assert "ok" in result  # 至少返回了有效结构
    
    
    # ═══════════════════════════════════════════════════
    # get_tools_for_role 测试
    # ═══════════════════════════════════════════════════
    
    class TestGetToolsForRole:
        """get_tools_for_role 单元测试."""
    
        def test_developer_has_write_tools(self):
            tools = get_tools_for_role("developer")
            names = {t["function"]["name"] for t in tools}
            assert "write_file" in names
            assert "patch_file" in names
            assert "run_python" in names
    
        def test_qa_has_pytest(self):
            tools = get_tools_for_role("qa")
            names = {t["function"]["name"] for t in tools}
            assert "run_pytest" in names
    
        def test_architect_has_readonly(self):
            tools = get_tools_for_role("architect")
            names = {t["function"]["name"] for t in tools}
            assert "write_file" not in names
            assert "run_python" in names
    
        def test_all_roles_have_read_grep_list(self):
            for role in ("developer", "qa", "architect", "researcher", "unknown"):
                tools = get_tools_for_role(role)
                names = {t["function"]["name"] for t in tools}
                assert "read_file" in names
                assert "grep" in names
                assert "list_files" in names
                assert "finish" in names
    
    
    # ═══════════════════════════════════════════════════
    # TOOL_SCHEMA 结构测试
    # ═══════════════════════════════════════════════════
    
    class TestToolSchema:
        """TOOL_SCHEMA 常量测试."""
    
        def test_all_tools_have_function_name(self):
            for tool in TOOL_SCHEMA:
                assert "function" in tool
                assert "name" in tool["function"]
    
        def test_known_tools_present(self):
            names = {t["function"]["name"] for t in TOOL_SCHEMA}
            expected = {"read_file", "grep", "list_files", "write_file",
                        "patch_file", "run_python", "run_pytest", "finish"}
            assert expected.issubset(names)
    
    ```
    
    ### 文件: `src/backend/tests/test_team_manager.py`
    ```py
    # -*- coding: utf-8 -*-
    """团队管理器单元测试 — TeamManager CRUD 操作."""
    
    from __future__ import annotations
    
    import pytest
    
    from agents.models import (
        AgentProfile,
        AgentTeam,
        ModelConfig,
    )
    
    
    class TestTeamManagerCreate:
        """TeamManager 创建操作测试."""
    
        def test_create_team(self, team_manager):
            team = team_manager.create_team(
                name="测试团队",
                team_id="team-001",
                description="自动化测试",
            )
            assert team is not None
            assert team.team_id == "team-001"
            assert team.name == "测试团队"
            assert team.description == "自动化测试"
    
        def test_create_duplicate_team_raises(self, team_manager):
            team_manager.create_team(name="A", team_id="team-001")
            with pytest.raises(ValueError):
                team_manager.create_team(name="B", team_id="team-001")
    
    
    class TestTeamManagerRead:
        """TeamManager 读取操作测试."""
    
        def test_get_team(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            team = team_manager.get_team("t1")
            assert team is not None
            assert team.name == "T1"
    
        def test_get_nonexistent_team(self, team_manager):
            team = team_manager.get_team("nonexistent")
            assert team is None
    
        def test_list_teams(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            team_manager.create_team(name="T2", team_id="t2")
            teams = team_manager.list_teams()
            assert len(teams) == 2
            names = {t.name for t in teams}
            assert names == {"T1", "T2"}
    
    
    class TestTeamManagerUpdate:
        """TeamManager 更新操作测试."""
    
        def test_update_team(self, team_manager):
            team_manager.create_team(name="Old", team_id="t1")
            updated = team_manager.update_team("t1", name="New", description="Updated")
            assert updated is not None
            assert updated.name == "New"
            assert updated.description == "Updated"
    
        def test_update_team_ignores_immutable(self, team_manager):
            team_manager.create_team(name="OK", team_id="t1")
            # team_id 不在 AgentTeam dataclass 中当作可变字段
            updated = team_manager.update_team("t1", name="StillOK")
            assert updated is not None
            assert updated.team_id == "t1"  # team_id 不可变
    
        def test_update_nonexistent_team(self, team_manager):
            result = team_manager.update_team("noop", name="X")
            assert result is None
    
    
    class TestTeamManagerDelete:
        """TeamManager 删除操作测试."""
    
        def test_delete_team(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            deleted = team_manager.delete_team("t1")
            assert deleted is not None
            assert team_manager.get_team("t1") is None
    
        def test_delete_nonexistent_team(self, team_manager):
            result = team_manager.delete_team("noop")
            assert result is None
    
    
    class TestAgentManagement:
        """Agent 管理操作测试."""
    
        def test_add_agent(self, team_manager, sample_agent_dict):
            team_manager.create_team(name="T1", team_id="t1")
            agent = AgentProfile(
                agent_id="agent-001",
                name="TestAgent",
                role="developer",
                state="idle",
            )
            result = team_manager.add_agent_to_team("t1", agent)
            assert result is True
    
        def test_get_agent(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            agent = AgentProfile(agent_id="a1", name="A1", role="developer")
            team_manager.add_agent_to_team("t1", agent)
    
            found = team_manager.get_agent("t1", "a1")
            assert found is not None
            assert found.name == "A1"
    
        def test_get_agent_nonexistent_team(self, team_manager):
            result = team_manager.get_agent("no-team", "any-agent")
            assert result is None
    
        def test_list_agents(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a1", name="A1", role="dev"))
            team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a2", name="A2", role="qa"))
    
            agents = team_manager.list_agents("t1")
            assert len(agents) == 2
    
        def test_list_agents_empty_team(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            agents = team_manager.list_agents("t1")
            assert agents == []
    
        def test_list_agents_nonexistent_team(self, team_manager):
            agents = team_manager.list_agents("no-team")
            assert agents == []
    
        def test_remove_agent(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            agent = AgentProfile(agent_id="a1", name="A1", role="developer")
            team_manager.add_agent_to_team("t1", agent)
    
            removed = team_manager.remove_agent_from_team("t1", "a1")
            assert removed is not None
            assert removed.name == "A1"
            assert team_manager.get_agent("t1", "a1") is None
    
    
    class TestModelManagement:
        """Model 管理操作测试."""
    
        def test_add_model(self, team_manager, sample_model_dict):
            team_manager.create_team(name="T1", team_id="t1")
            model = ModelConfig(
                model_id="model-001",
                name="deepseek-v4",
                provider="deepseek",
            )
            result = team_manager.add_model_to_team("t1", model)
            assert result is True
    
        def test_add_model_to_nonexistent_team(self, team_manager):
            model = ModelConfig(model_id="m1", name="M1", provider="openai")
            result = team_manager.add_model_to_team("no-team", model)
            assert result is False
    
        def test_remove_model(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            model = ModelConfig(model_id="m1", name="M1", provider="deepseek")
            team_manager.add_model_to_team("t1", model)
    
            removed = team_manager.remove_model_from_team("t1", "m1")
            assert removed is not None
            assert removed.name == "M1"
    
    
    class TestTeamOverview:
        """Team overview 操作测试."""
    
        def test_get_team_overview(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a1", name="A1", role="developer"))
    
            overview = team_manager.get_team_overview("t1")
            assert overview is not None
            assert overview["team_id"] == "t1"
            assert overview["name"] == "T1"
            assert overview["agent_count"] == 1
    
        def test_get_team_overview_nonexistent(self, team_manager):
            overview = team_manager.get_team_overview("no-team")
            assert overview is None
    
    
    class TestDuplicateAgent:
        """Agent 复制功能测试."""
    
        def test_duplicate_agent(self, team_manager):
            team_manager.create_team(name="T1", team_id="t1")
            original = AgentProfile(agent_id="a1", name="Original", role="developer")
            team_manager.add_agent_to_team("t1", original)
    
            clone = team_manager.duplicate_agent("t1", "a1")
            assert clone is not None
            assert "副本" in clone.name
          
  ...(截断)
  
  ## ⚠️ 最重要的规则
  系统已自动预加载项目文件结构和相关源文件（见上方 📂 项目上下文）。
  **你必须只引用上方提供的实际文件**，严禁凭想象编造文件名或路径。
  如果上下文中没有某个文件，说明该文件不存在。
  
  ## 要求
  1. 仔细阅读上方提供的项目文件结构和源文件内容
  2. 根据**实际存在的文件**分析哪些需要修改
  3. 列出需要修改的文件的**完整路径** (必须是项目上下文中出现的路径)
  4. 分析实现方案的可行性
  5. 引用具体代码行号说明修改点
  
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

# 技术调研报告：操作事件表与情境切片关联表

**任务编号**: 1f0da2f7-522  
**研究员**: Researcher (researcher)  
**日期**: 2026-05-17  
**项目**: AgentsGroup2026  
**目标**: 设计操作事件表（operation_events）和情境切片关���表（context_snapshots）数据模型，完成建表与存储逻辑，确保操作序列不可变、情境切片可追溯。

---

## 1. 现有系统分析

### 1.1 审计与事件相关模块
项目已存在多个与事件、审计相关的模块，为本次设计提供了基础：

| 文件 | 关键内容 |
|------|----------|
| `src/backend/agents/audit_store.py` | 审计存储结构，可能已有持久化事件记录功能（文件列表中可找到，具体实现未在上下文中展开） |
| `src/backend/agents/domain_events.py` | 领域事件定义，包含事件类型与数据结构 |
| `src/backend/agents/event_bus.py` | 事件总线，负责事件的发布与订阅 |
| `src/backend/agents/execution_registry.py` | 包含 `HistoryLog`、`ToolPermissionContext`、`RoutedMatch` 等，`HistoryLog` 记录 agent 操作历史 |
| `src/backend/agents/session_store.py` | 会话持久化，存有 `TranscriptStore`（对话转录），可用于追溯交互上下文 |
| `src/backend/agents/models.py` | 数据模型基类，如 `AgentProfile`, `AgentTeam`, `ModelConfig` |
| `src/backend/monitoring/models.py` | 监控事件模型，可能包含指标事件 |
| `src/backend/scripts/migrate.py` | 数据库迁移脚本，可用于建表 |

**亮点**：
- `HistoryLog`（execution_registry.py）已提供不可变日志的基础：`history.add("user_message", content[:100])` 等，但它是内存结构，需持久化。
- `TranscriptStore`（session_store.py）以追加方式存储对话，与操作事件类似。
- 前端 `system-evolution.html` 已有“审计轨迹”面板（`audit-entry` 样式），可用于展示操作事件。

### 1.2 前端相关页面
- `src/frontend/system-evolution.html`：包含“审计轨迹”标签页，展示 `audit-entry` 列表。
- `src/frontend/monitoring.html`：监控仪表板，可能展示实时事件流。
- 这些页面可直接绑定新设计的 API，展示操作事件与情境切片。

### 1.3 存储机制推断
根据 `src/backend/agents/session_store.py` 中使用的文件持久化（如 `.json` 或 `.db`），以及 `src/backend/agents/team_store.py`、`src/backend/agents/task_store.py` 等命名推测，系统采用 **JSON 文件或内置 DB** 存储，没有使用传统关系型数据库。但 `migrate.py` 的存在暗示可能已有 SQLite 或类似迁移能力。 需要确认，但设计方案应兼容简单文件持久化与轻量级数据库（SQLite）两种模式。

---

## 2. 数据模型设计

### 2.1 表：`operation_events`（操作事件）

**设计原则**：
- **不可变性**：记录一旦创建，不允许修改或删除（append-only）。
- **完整性**：包含事件类型、操作主体、参数、结果、关联的情境切片 ID。
- **可验证性**：通过哈希链或内容哈希确保记录未被篡改。

**字段定义**：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `id` | string (UUID) | 主键，全局唯一 |
| `event_type` | string | 事件类型，如 `tool_invocation`, `agent_action`, `gate_evaluation`, `merge_decision` 等 |
| `agent_id` | string | 执行操作的 Agent ID |
| `team_id` | string | 所属团队 ID |
| `operation` | string | 操作名称，如 `read_file`, `run_pytest` |
| `params` | JSON | 操作参数（输入） |
| `result_summary` | string | 操作结果摘要（缩短的文本） |
| `result_full` | JSON/text | 完整结果数据（可存外部文件引用） |
| `context_snapshot_id` | string (FK) | 关联的情境切片 ID，允许为空 |
| `parent_event_id` | string (FK) | 父事件 ID，构建事件链 |
| `timestamp` | ISO8601 string | 事件发生时间（毫秒精度） |
| `immutable_hash` | string | 内容哈希（SHA256），确保完整性 |
| `previous_hash` | string | 前一事件哈希，形成链式结构（可选） |

**索引建议**：
- 按 `team_id` + `timestamp` 复合索引，便于按团队时间线查询。
- 按 `agent_id` 索引。
- 按 `event_type` 索引用于分类统计。

### 2.2 表：`context_snapshots`（情境切片）

**用途**：记录事件发生时的系统上下文，例如当前团队配置、Agent 状态、模型配置、系统版本等，便于事后追溯“为什么会这样操作”。

**字段定义**：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `id` | string (UUID) | 主键 |
| `event_id` | string (FK) | 关联的操作事件 ID（一个事件可有多个切片版本） |
| `snapshot_type` | string | 切片类型：`team_config`, `agent_pool`, `system_state`, `environment` |
| `snapshot_data` | JSON | 上下文数据快照 |
| `created_at` | ISO8601 string | 快照创建时间 |
| `immutable_hash` | string | 内容哈希，不可变标记 |

**关联关系**：
- `operation_events.context_snapshot_id` → `context_snapshots.id`（多对一）
- `context_snapshots.event_id` → `operation_events.id`（外键反向引用）

---

## 3. 存储逻辑与不可变策略

### 3.1 追加写入保证
- 写入操作只执行 `INSERT`，不暴露 `UPDATE` 或 `DELETE` 接口。
- 在数据类或 DAO 层强制检查：任何“修改”操作视为无效，需抛出异常。
- 如果使用 JSON 文件存储，每条记录独立文件（如 `events/<event_id>.json`），文件名不可���改。
- 如果使用 SQLite，不使用 `UPDATE` 语句，只用 `INSERT`，并提供只读接口。

### 3.2 哈希链机制（可选增强）
不可变性可通过以下方式加强：
- 生成 `immutable_hash = SHA256(event_data_json + previous_hash)`，形成一个不可变链。任何记录变动都会破坏后续哈希。
- 在前端或审计 API 中提供验证端点，检查哈希链完整性。

### 3.3 与现有组件集成方案

#### 3.3.1 利用 `event_bus` 拦截
修改 `src/backend/agents/event_bus.py`，增加一个持久化订阅者：
```python
# 在 EventBus 初始化时
self.subscribe("operation.*", operation_event_store.handle_event)
```
这样所有通过总线发布的操作事件会自动入库。

#### 3.3.2 `HistoryLog` 持久化
`execution_registry.py` 中的 `HistoryLog` 目前是内存列表，可以添加 `flush_to_db()` 方法，将累积的日志批量写入 `operation_events` 表。在 agent 循环结束时调用即可。

#### 3.3.3 `TranscriptStore` 关联
会话转录（session_store.py 中的 `TranscriptStore`）可作为情境切片的一种来源，当用户与系统交互时，将对话片段作为 `context_snapshot` 记录。

### 3.4 API 设计
在 `src/backend/agents/api.py` 或新增 `src/backend/agents/operation_api.py` 中增加：
- `GET /api/operations` – 分页查询操作事件（支持团队 ID、agent ID、时间范围过滤）
- `GET /api/operations/{id}` – 获取单个事件详情，附带关联的情境切片
- `GET /api/context-snapshots/{id}` – 获取情境切片数据
- `POST /api/context-snapshots/validate` – 验证哈希链完整性

前端 `system-evolution.html` 的审计轨迹面板可直接调用这些 API。

---

## 4. 需要修改与新建的文件清单

基于项目现有文件结构，具体变更如下：

### 4.1 新建文件
- **`src/backend/agents/operation_models.py`**  
  定义 `OperationEvent`、`ContextSnapshot` 数据类（dataclass / Pydantic）。
- **`src/backend/agents/operation_store.py`**  
  实现存取逻辑：追加写入、查询、哈希链生成、与现有存储模块的兼容（如 JSON 文件或 SQLite）。
- **`src/backend/agents/operation_api.py`**  
  提供 REST API 接口。
- **`src/backend/tests/test_operation_store.py`**  
  单元测试，验证不可变写入、关联查询、哈希链正确性。

### 4.2 修改现有文件
| 文件 | 修改内容 |
|------|----------|
| `src/backend/agents/event_bus.py` | 增加持久化订阅者，将操作相关事件路由到 `operation_store` |
| `src/backend/agents/execution_registry.py` | `HistoryLog` 增加 `flush_to_db` 方法，调用 `operation_store` 批量保存 |
| `src/backend/agents/session_store.py` | `TranscriptStore` 或 `ChatSession` 增加保存上下文快照的方法，关联 `operation_events` |
| `src/backend/agents/models.py` | 如果需要，可在此文件添加 `OperationEvent` 等模型（但更推荐独立文件） |
| `src/backend/scripts/migrate.py` | 添加建表迁移逻辑（若使用 SQLite） |
| `src/backend/main.py` | 注册新路由 `from agents.operation_api import router` 并挂载 |
| `src/frontend/system-evolution.html` | 修改审计轨迹面板，调用 `/api/operations` 展示操作事件列表；增加查看详情和情境切片的功能 |
| `src/frontend/monitoring.html` | 可选：添加实时事件流展示 |

### 4.3 无需修改但需参考的文件
- `src/backend/agents/audit_store.py` – 其结构可能类似，可对比或直接扩展使用。
- `src/backend/agents/domain_events.py` – 事件类型定义，需要确保新事件类型与之兼容。
- `src/backend/agents/team_store.py` – 存储模式参考，特别是文件路径管理。

---

## 5. 实现方案与关键代码示例

### 5.1 数据类定义（`operation_models.py`）
```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
import hashlib
import json

@dataclass
class OperationEvent:
    id: str = field(default_factory=lambda: uuid4().hex)
    event_type: str = ""
    agent_id: str = ""
    team_id: str = ""
    operation: str = ""
    params: dict = field(default_factory=dict)
    result_summary: str = ""
    result_full: str = ""
    context_snapshot_id: str = ""
    parent_event_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    immutable_hash: str = ""
    previous_hash: str = ""

    def compute_hash(self, previous: str = "") -> str:
        payload = json.dumps({
            "id": self.id, "event_type": self.event_type, "agent_id": self.agent_id,
            "operation": self.operation, "timestamp": self.timestamp, "params": self.params,
            "result_summary": self.result_summary, "previous_hash": previous
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def seal(self, previous_hash: str = ""):
        self.previous_hash = previous_hash
        self.immutable_hash = self.compute_hash(previous_hash)
```

### 5.2 存储实现（`operation_store.py`）– 伪代码
```python
class OperationStore:
    def __init__(self, storage_dir: str = "data/operations"):
        self.storage_dir = storage_dir
        self.ensure_dir()
        # 可选：加载索引

    def save_event(self, event: OperationEvent, previous_hash: str = ""):
        event.seal(previous_hash)
        filepath = Path(self.storage_dir) / f"{event.id}.json"
        with open(filepath, "w") as f:
            json.dump(event.to_dict(), f, ensure_ascii=False, indent=2)
        self.update_index(event)

    def query_events(self, team_id: str = "", limit: int = 50, offset: int = 0) -> List[dict]:
        # 基于索引或遍历文件
        pass

    # 不可变性检测
    def verify_chain(self, start_id: str) -> bool:
        pass
```

### 5.3 EventBus 集成（修改 `event_bus.py`）
```python
from .operation_store import OperationStore
op_store = OperationStore()

def handle_operation_event(event: dict):
    event_obj = OperationEvent(**event)
    op_store.save_event(event_obj)

event_bus.subscribe("operation.*", handle_operation_event)
```

### 5.4 前端集成（`system-evolution.html` 审计轨迹）
利用现有 HTML 模板，添加 JS：
```javascript
fetch('/api/operations?team_id=currentTeam')
  .then(res => res.json())
  .then(events => {
      const container = document.querySelector('#audit-list');
      events.forEach(ev => {
          const entry = `<div class="audit-entry">
            <span class="ae-time">${ev.timestamp}</span>
            <span class="ae-type">${ev.event_type}</span>
            <span class="ae-detail">${ev.operation} by ${ev.agent_id}</span>
          </div>`;
          container.innerHTML += entry;
      });
  });
```

---

## 6. 不可变性与追溯性保证

- **数据库层面**：只允许 INSERT，拒绝 UPDATE/DELETE。在 ORM 或数据访问层中通过函数限制实现。
- **应用层**：数据类 `seal()` 方法计算哈希并写入字段，此后字段不可变（通过属性保护或代码约定）。
- **审计验证**：提供 API `GET /api/operations/verify?from_id=xxx`，遍历事件链，重新计算哈希并对比，返回验证报告。
- **情境切片**：每次操作前，系统调用 `context_snapshot.create(event_id)` 记录当前上下文，关联 ID 存入事件表，查询时自动 JOIN。

---

## 7. 测试策略

### 7.1 单元测试（新建 `test_operation_store.py`）
- 测试追加写入并读取。
- 测试多次调用不产生修改。
- 测试哈希链正确性。
- 测试关联查询（事件带切片）。

### 7.2 集成测试
- 通过 EventBus 发布操作事件，验证持久化触发。
- 模拟 agent 执行完整流程，检查日志中出现相应事件记录。
- 前端 e2e 测试：审计页面加载并展示事件列表。

---

## 8. 风险与依赖

- 现有 `audit_store.py` 可能已有类似实现，需先审查其代码（未在上下文中展示），避免重复建设。
- 若系统改用数据库迁移（如 SQLite），需修改 `migrate.py`，并确保与现有文件存储模式兼容。
- 大量事件存储可能影响性能，需考虑定期归档或索引优化（如按日分文件夹）。

---

## 9. 总结

本调研基于项目现有代码，提出了 **操作事件表** 与 **情境切片表** 的完整设计方案，明确了需要新建 4 个文件和修改 8 个现有文件，并给出了数据模型、存储逻辑、API 设计、前端展示以及不可变链保证的具体实现路径。方案复用事件总线、历史日志等现有组件，改动最小化，且完全满足“操作序列不可变、情境切片可追溯”的需求。

下一步应由 Architect 进行详细架构设计，并由 Developer 和 QA 依次推进实现。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
