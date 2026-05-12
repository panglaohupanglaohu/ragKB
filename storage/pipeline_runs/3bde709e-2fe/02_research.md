# 研究分析 — researcher

任务: 硬编码基线到 CI 门禁，实现模型更新自动重算并投射为业务方可读的实时契约仪表
步骤: research
Agent: build_researcher

---

📋 任务: 3bde709e-2fe
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
  硬编码基线到 CI 门禁，实现模型更新自动重算并投射为业务方可读的实时契约仪表
  全栈开发 + Architect
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/datacenter-ratchet-evolution.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/plaza-dark.html
  src/frontend/plaza-old.html
  src/frontend/plaza-wabisabi-v2.html
  src/frontend/plaza-wabisabi.html
  src/frontend/plaza.html
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
  src/backend/agents/__init__.py
  src/backend/agents/ab_testing.py
  src/backend/agents/agent_loop.py
  src/backend/agents/agent_toolbox.py
  src/backend/agents/api.py
  src/backend/agents/chat_harness.py
  src/backend/agents/execution_registry.py
  src/backend/agents/hermes_research.py
  src/backend/agents/knowledge_base.py
  src/backend/agents/models.py
  src/backend/agents/plaza.py
  src/backend/agents/plaza_engine.py
  src/backend/agents/plaza_routes.py
  src/backend/agents/plaza_routes.py.bak
  src/backend/agents/plaza_store.py
  src/backend/agents/session_store.py
  src/backend/agents/skill_registry.py
  src/backend/agents/task_engine.py
  src/backend/agents/task_store.py
  src/backend/agents/team_manager.py
  src/backend/agents/team_store.py
  src/backend/agents/tool_executor.py
  src/backend/agents/tool_registry.py
  src/backend/agents/tts_routes.py
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/greeting.py
  src/backend/agents/skills/hello.py
  src/backend/scripts/__init__.py
  src/backend/scripts/validate_startup.py
  src/backend/scripts/validate_telemetry.py
  src/backend/monitoring/__init__.py
  src/backend/monitoring/collector.py
  src/backend/monitoring/models.py
  src/backend/monitoring/plaza_monitor.py
  src/backend/monitoring/plaza_monitor.py.bak
  src/backend/monitoring/sampler.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/marine_base.py
  src/backend/channels/openclaw_sync.py
  src/backend/channels/openclaw_sync.py.bak
  src/backend/channels/system_evolution.py
  src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
  src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
  src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
  src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
  src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
  src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
  src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
  src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
  src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
  src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
  src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
  src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T004102.md
  src/docs/agent_handoffs/6f911ba3-822_architecture_20260507T003740.md
  src/docs/agent_handoffs/6f911ba3-822_deploy_FAILED_20260507T004337.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T003806.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004113.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004235.md
  src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
  src/docs/agent_handoffs/6f911ba3-822_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/6f911ba3-822_research_20260507T003550.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T003827.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004134.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004311.md
  src/docs/agent_handoffs/7c934759-39e_architecture_20260505T010014.md
  src/docs/agent_handoffs/7c934759-39e_develop_20260505T010359.md
  src/docs/agent_handoffs/7c934759-39e_develop_20260505T012357.md
  src/docs/agent_handoffs/7c934759-39e_develop_FAILED_20260505T011447.md
  src/docs/agent_handoffs/7c934759-39e_executor_started_20260505T005814.md
  src/docs/agent_handoffs/7c934759-39e_pm_decompose_20260505T005849.md
  src/docs/agent_handoffs/7c934759-39e_research_20260505T005919.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011016.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011949.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T012853.md
  src/docs/agent_handoffs/8a5071c5-834_architecture_20260507T003655.md
  src/docs/agent_handoffs/8a5071c5-834_deploy_FAILED_20260507T004051.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003716.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003903.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T004005.md
  src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
  src/docs/agent_handoffs/8a5071c5-834_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/8a5071c5-834_research_20260507T003540.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003737.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003929.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T004031.md
  src/docs/agent_handoffs/a77bd3b9-2db_architecture_20260507T003625.md
  src/docs/agent_handoffs/a77bd3b9-2db_deploy_FAILED_20260507T004102.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003646.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003838.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T004005.md
  src/docs/agent_handoffs/a77bd3b9-2db_executor_started_20260507T003435.md
  src/docs/agent_handoffs/a77bd3b9-2db_pm_decompose_20260507T003515.md
  src/docs/agent_handoffs/a77bd3b9-2db_research_20260507T003545.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003712.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003904.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T004042.md
  src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
  src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
  src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
  src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
  src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154631.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154838.md
  ... (共 255 个 src/ 文件)
  
  ```
  
  ### 文件: `src/frontend/agent-team-config.html`
  ```html
  <!DOCTYPE html>
  <html lang="zh-CN">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentsGroup2026 — 智能体团队管理</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@300;400;500;700&family=Noto+Serif:wght@200;300;400;600;900&family=Noto+Serif+SC:wght@200;300;400;600;900&family=Noto+Sans+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/css/agent-team-config.css">
    <link rel="stylesheet" href="/css/openbridge-theme.css">
    <link rel="stylesheet" href="/css/ws-theme-bridge.css">
  </head>
  <body>
  <div class="app">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="sb-header"><h2><span class="seal">智</span> AgentsGroup</h2><select class="fi" id="team-select" style="font-size:12px;padding:6px 8px"></select></div>
      <div class="sb-nav">
        <a class="active" data-view="overview" onclick="switchView('overview')"><span class="seal">览</span> 仪表盘</a>
        <a data-view="models" onclick="switchView('models')"><span class="seal">腦</span> 模型池</a>
        <a data-view="llm" onclick="switchView('llm')"><span class="seal">接</span> LLM 配置</a>
        <a data-view="tools" onclick="switchView('tools')"><span class="seal seal-koke">具</span> 工具</a>
        <a data-view="skills" onclick="switchView('skills')"><span class="seal seal-kitsune">能</span> 技能</a>
        <a data-view="tasks" onclick="switchView('tasks')"><span class="seal">务</span> 任务</a>
        <a data-view="sessions" onclick="switchView('sessions')"><span class="seal">存</span> 会话存档</a>
        <a data-view="runtime" onclick="switchView('runtime')"><span class="seal seal-shu">行</span> Runtime</a>
        <a data-view="registry" onclick="switchView('registry')"><span class="seal">厂</span> Token 工厂</a>
      </div>
      <div class="sb-section">团队成员</div>
      <div class="sb-agents" id="sb-agents"></div>
      <div class="sb-footer"><button class="btn btn-pink btn-sm" onclick="openWizard()" style="width:100%;justify-content:center">＋ 新建智能体</button></div>
    </div>
    <!-- Main -->
    <div class="main">
      <div class="topbar"><div class="topbar-left"><h1 id="main-title">团队概览</h1><span class="badge" id="main-badge" style="background:rgba(152,245,167,0.15);color:var(--lime)"></span></div><div class="topbar-right"><a href="/plaza.html" class="btn btn-sm btn-ghost"><span class="seal">⊙</span> 智能体广场</a><a href="/system-evolution.html" class="btn btn-sm btn-ghost"><span class="seal seal-koke">进</span> 演进视图</a><button class="btn btn-sm" onclick="openModal('modal-create-team')">＋ 创建团队</button></div></div>
      <!-- Views -->
      <div id="view-overview" class="main-inner"><div class="main-scroll"><div class="card-grid" id="ov-stats"></div><div class="section" id="ov-team-section"><div class="section-title" id="ov-team-title"></div><table class="tbl"><thead><tr><th>Agent</th><th>角色</th><th>状态</th><th>技能</th><th>操作</th></tr></thead><tbody id="ov-team-agents"></tbody></table></div>
  <!-- 系统自我演进 -->
  <div class="section" id="evo-section"><div class="section-title" style="display:flex;justify-content:space-between;align-items:center">
  <span>🔄 系统自我演进</span>
  <div style="display:flex;gap:8px">
    <select class="fi" id="evo-filter" style="width:auto;padding:4px 8px;font-size:11px" onchange="loadEvolution()"><option value="">全部状态</option><option value="discovered">发现</option><option value="dispatched">已派发</option><option value="in_progress">进行中</option><option value="verify_pending">待验证</option><option value="verified">已验证</option><option value="failed">失败</option></select>
    <button class="btn btn-sm" onclick="runEvoAudit()">🔍 审查</button>
    <button class="btn btn-sm btn-pink" onclick="runEvoCycleStepper()">▶ 运行演进周期</button>
  </div>
  </div>
  <!-- Compliance Rating -->
  <div id="evo-compliance" class="card-grid" style="margin-bottom:16px"></div>
  <!-- Evolution Cycle Stepper (hidden by default) -->
  <div id="evo-stepper" class="card hidden" style="margin-bottom:16px;padding:16px">
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px">
      <div class="evo-step-item" data-step="audit"><span class="wf-dot" id="es-audit">1</span><span style="font-size:12px;margin-left:4px">审查</span></div>
      <div class="wf-connector" id="es-c1"></div>
      <div class="evo-step-item" data-step="dispatch"><span class="wf-dot" id="es-dispatch">2</span><span style="font-size:12px;margin-left:4px">派发</span></div>
      <div class="wf-connector" id="es-c2"></div>
      <div class="evo-step-item" data-step="verify"><span class="wf-dot" id="es-verify">3</span><span style="font-size:12px;margin-left:4px">验证</span></div>
      <div class="wf-connector" id="es-c3"></div>
      <div class="evo-step-item" data-step="close"><span class="wf-dot" id="es-close">4</span><span style="font-size:12px;margin-left:4px">关闭</span></div>
    </div>
    <div id="evo-stepper-log" style="font-size:12px;color:var(--muted)"></div>
  </div>
  <!-- Stats -->
  <div class="card-grid" id="evo-stats" style="margin-bottom:16px"></div>
  <!-- Zones -->
  <div id="evo-zones" style="margin-bottom:16px"></div>
  <!-- Rules -->
  <div id="evo-rules" style="margin-bottom:16px"></div>
  <!-- Items -->
  <div id="evo-items"></div>
  </div>
  </div></div>
      <div id="view-models" class="main-inner hidden"><div class="main-scroll"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">🧠 模型池</div><button class="btn btn-pink btn-sm" onclick="openModal('modal-add-model')">＋ 添加模型</button></div><table class="tbl"><thead><tr><th>ID</th><th>名称</th><th>提供商</th><th>Max Tokens</th><th>温度</th><th>默认</th><th>操作</th></tr></thead><tbody id="models-tb"></tbody></table></div></div>
      <div id="view-tools" class="main-inner hidden"><div class="main-scroll"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">🔧 可用工具</div><div style="display:flex;gap:8px"><button class="btn btn-sm" onclick="switchView('registry')">🏭 Token 工厂</button><button class="btn btn-sm" onclick="showToolSearch()">🔍 搜索</button></div></div><div id="tools-search-bar" class="hidden" style="margin-bottom:12px"><div style="display:flex;gap:10px"><input class="fi" id="tools-search-input" placeholder="搜索工具..." oninput="filterToolCards(this.value)" style="flex:1"><button class="btn btn-sm" onclick="el('tools-search-bar').classList.add('hidden')">✕</button></div></div><div id="tools-cards"></div></div></div>
      <div id="view-skills" class="main-inner hidden"><div class="main-scroll"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">⚡ 可用技能</div><div style="display:flex;gap:8px"><button class="btn btn-sm" onclick="switchView('registry')">📥 导入</button><button class="btn btn-sm" onclick="exportSkillsMD()">📤 导出</button></div></div><div id="skills-cards"></div></div></div>
      <div id="view-tasks" class="main-inner hidden"><div class="main-scroll"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">📋 并发任务</div><div style="display:flex;gap:8px"><span id="task-stats" style="font-size:12px;color:var(--muted);display:flex;align-items:center"></span><button class="btn btn-pink btn-sm" onclick="openModal('modal-add-task')">＋ 提交任务</button><button class="btn btn-sm" onclick="openModal('modal-batch-task')">📦 批量提交</button></div></div><table class="tbl"><thead><tr><th>ID</th><th>标题</th><th>Agent</th><th>优先级</th><th>依赖</th><th>状态</th><th>操作</th></tr></thead><tbody id="tasks-tb"></tbody></table></div></div>
      <div id="view-llm" class="main-inner hidden"><div class="main-scroll">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">🔌 LLM 提供商配置</div><button class="btn btn-pink btn-sm" onclick="testLLM()">🧪 测试连接</button></div>
        <div id="llm-status-card" class="card" style="margin-bottom:20px;padding:20px"><p style="color:var(--dim)">加载中...</p></div>
        <div class="card" style="padding:20px;margin-bottom:20px">
          <div class="section-title" style="margin-top:0;margin-bottom:12px">⚙️ 配置 LLM 提供商</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div class="form-group"><label class="form-label">提供商</label><select class="fi" id="llm-provider"><option value="deepseek">DeepSeek</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="local">本地 (Ollama/vLLM)</option><option value="openrouter">OpenRouter</option><option value="github">GitHub Models</option><option value="qwen">通义千问</option></select></div>
            <div class="form-group"><label class="form-label">模型</label><input class="fi" id="llm-model" placeholder="deepseek-v4-pro"></div>
            <div class="form-group"><label class="form-label">API Key</label><input class="fi" id="llm-key" type="password" placeholder="sk-..."></div>
            <div class="form-group"><label class="form-label">API Base URL (可选)</label><input class="fi" id="llm-url" placeholder="https://api.deepseek.com"></div>
            <div class="form-group"><label class="form-label">Max Tokens</label><input class="fi" id="llm-tokens" type="number" value="4096" min="100" max="128000"></div>
            <div class="form-group"><label class="form-label">温度</label><input class="fi" id="llm-temp" type="number" value="0.7" min="0" max="2" step="0.1"></div>
          </div>
          <div style="margin-top:16px;display:flex;gap:10px"><button class="btn btn-pink" onclick="saveLLMConfig()">💾 保存配置</button><button class="btn" onclick="loadLLMStatus()">🔄 刷新状态</button></div>
        </div>
        <div id="llm-test-result" class="card hidden" style="padding:20px"><div class="section-title" style="margin-top:0;margin-bottom:8px">🧪 测试结果</div><div id="llm-test-content"></div></div>
        <!-- TTS Config Section -->
        <div class="card" style="padding:20px;margin-bottom:20px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><div class="section-title" style="margin-top:0;margin-bottom:0">🔊 TTS 语音合成配置</div><div style="display:flex;gap:8px"><span id="tts-status-badge" class="badge" style="font-size:11px">检测中...</span><button class="btn btn-sm" onclick="testTTSConnection()">🧪 测试</button><button class="btn btn-pink btn-sm" onclick="startTTSService()">▶ 启动服务</button></div></div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div class="form-group"><label class="form-label">TTS 引擎</label><select class="fi" id="tts-engine"><option value="gpt-sovits">GPT-SoVITS</option><option value="edge-tts">Edge TTS (在线)</option><option value="web-speech">浏览器内置</option></select></div>
            <div class="form-group"><label class="form-label">API 地址</label><input class="fi" id="tts-api-url" placeholder="http://127.0.0.1:9880"></div>
            <div class="form-group"><label class="form-label">参考音频路径</label><input class="fi" id="tts-ref-audio" placeholder="ref_audio/male_sample.wav"></div>
            <div class="form-group"><label class="form-label">参考音频文本</label><input class="fi" id="tts-prompt-text" placeholder="参考音频对应的文字内容"></div>
            <div class="form-group"><label class="form-label">语言</label><select class="fi" id="tts-lang"><option value="zh">中文</option><option value="en">English</option><option value="ja">日本語</option><option value="auto">自动</option></select></div>
            <div class="form-group"><label class="form-label">语速</label><input class="fi" id="tts-speed" type="number" value="1.0" min="0.5" max="2.0" step="0.1"></div>
          </div>
          <div style="margin-top:16px;display:flex;gap:10px"><button class="btn btn-pink" onclick="saveTTSConfig()">💾 保存 TTS 配置</button><button class="btn" onclick="loadTTSConfig()">🔄 刷新</button></div>
          <div id="tts-test-result" style="margin-top:12px;font-size:12px;color:var(--dim)"></div>
        </div>
        <div class="card" style="padding:20px"><div class="section-title" style="margin-top:0;margin-bottom:8px">📊 会话列表</div><div id="llm-sessions"></div></div>
      </div></div>
      <div id="view-agent" class="main-inner hidden">
      <!-- Session Persistence View -->
      <div id="view-sessions" class="main-inner hidden"><div class="main-scroll">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">💾 会话存档管理</div><div style="display:flex;gap:8px"><button class="btn btn-sm" onclick="loadPersistedSessions()">🔄 刷新</button></div></div>
        <div class="card" style="margin-bottom:20px;padding:20px">
          <div class="section-title" style="margin-top:0;margin-bottom:12px">🔍 跨会话搜索</div>
          <div style="display:flex;gap:10px"><input class="fi" id="ss-query" placeholder="搜索所有持久化会话的内容..." style="flex:1" onkeydown="if(event.key==='Enter')searchPersistedSessions()"><button class="btn btn-pink btn-sm" onclick="searchPersistedSessions()">搜索</button></div>
          <div id="ss-search-results" style="margin-top:12px"></div>
        </div>
        <div class="card" style="padding:20px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><div class="section-title" style="margin:0">📁 已保存的会话</div><span id="ss-count" style="color:var(--dim);font-size:12px"></span></div>
          <div id="ss-list"></div>
        </div>
      </div></div>
      <!-- PortRuntime View -->
      <div id="view-runtime" class="main-inner hidden"><div class="main-scroll">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">🚀 PortRuntime 路由引擎</div></div>
        <div class="card" style="margin-bottom:20px;padding:20px">
          <div class="section-title" style="margin-top:0;margin-bottom:12px">🎯 Prompt 路由</div>
          <p style="color:var(--muted);font-size:12px;margin-bottom:14px">输入自然语言指令，系统将自动匹配最佳工具和命令 (claw-code-parity PortRuntime)</p>
          <div style="display:grid;gap:12px">
            <div class="form-group" style="margin:0"><label class="form-label">Prompt</label><textarea class="fi" id="rt-prompt" rows="3" placeholder="例: 检查主机状态并分析油温趋势"></textarea></div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
              <div class="form-group" style="margin:0"><label class="form-label">最大匹配数</label><input class="fi" id="rt-limit" type="number" value="5" min="1" max="20"></div>
              <div class="form-group" style="margin:0"><label class="form-label">禁用工具 (逗号分隔)</label><input class="fi" id="rt-deny" placeholder="web_search, run_python"></div>
              <div class="form-group" style="margin:0"><label class="form-label">禁用前缀</
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
      model: str = "deepseek-v4-pro"
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
              model=os.getenv("AG_LLM_MODEL", "deepseek-v4-pro"),
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
              model=llm.get("model", "deepseek-v4-pro"),
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
              model=getattr(model_config, "name", "deepseek-v4-pro"),
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
  
      def persist(self) -> str:
        
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
      "built on the Hermes Agent architecture from Nous Research. "
      "You are a self-improving researcher with a closed learning loop — "
      "you create skills from experience, improve them during use, persist knowledge, "
     
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose (完整产出)
  
  # PM分解 — project_manager
  
  任务: 硬编码基线到 CI 门禁，实现模型更新自动重算并投射为业务方可读的实时契约仪表
  步骤: pm_decompose
  Agent: build_pm
  
  ---
  
  📋 任务: 3bde709e-2fe
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
    硬编码基线到 CI 门禁，实现模型更新自动重算并投射为业务方可读的实时契约仪表
    全栈开发 + Architect
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
    src/frontend/datacenter-ratchet-evolution.html
    src/frontend/index.html
    src/frontend/login.html
    src/frontend/plaza-dark.html
    src/frontend/plaza-old.html
    src/frontend/plaza-wabisabi-v2.html
    src/frontend/plaza-wabisabi.html
    src/frontend/plaza.html
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
    src/backend/agents/__init__.py
    src/backend/agents/ab_testing.py
    src/backend/agents/agent_loop.py
    src/backend/agents/agent_toolbox.py
    src/backend/agents/api.py
    src/backend/agents/chat_harness.py
    src/backend/agents/execution_registry.py
    src/backend/agents/hermes_research.py
    src/backend/agents/knowledge_base.py
    src/backend/agents/models.py
    src/backend/agents/plaza.py
    src/backend/agents/plaza_engine.py
    src/backend/agents/plaza_routes.py
    src/backend/agents/plaza_routes.py.bak
    src/backend/agents/plaza_store.py
    src/backend/agents/session_store.py
    src/backend/agents/skill_registry.py
    src/backend/agents/task_engine.py
    src/backend/agents/task_store.py
    src/backend/agents/team_manager.py
    src/backend/agents/team_store.py
    src/backend/agents/tool_executor.py
    src/backend/agents/tool_registry.py
    src/backend/agents/tts_routes.py
    src/backend/agents/teams/__init__.py
    src/backend/agents/teams/ai_coding_team.py
    src/backend/agents/teams/build_team.py
    src/backend/agents/teams/energy_team.py
    src/backend/agents/skills/__init__.py
    src/backend/agents/skills/greeting.py
    src/backend/agents/skills/hello.py
    src/backend/scripts/__init__.py
    src/backend/scripts/validate_startup.py
    src/backend/scripts/validate_telemetry.py
    src/backend/monitoring/__init__.py
    src/backend/monitoring/collector.py
    src/backend/monitoring/models.py
    src/backend/monitoring/plaza_monitor.py
    src/backend/monitoring/plaza_monitor.py.bak
    src/backend/monitoring/sampler.py
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/marine_base.py
    src/backend/channels/openclaw_sync.py
    src/backend/channels/openclaw_sync.py.bak
    src/backend/channels/system_evolution.py
    src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
    src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
    src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
    src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
    src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
    src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
    src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
    src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
    src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
    src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
    src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
    src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
    src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
    src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T004102.md
    src/docs/agent_handoffs/6f911ba3-822_architecture_20260507T003740.md
    src/docs/agent_handoffs/6f911ba3-822_deploy_FAILED_20260507T004337.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T003806.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004113.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004235.md
    src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
    src/docs/agent_handoffs/6f911ba3-822_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/6f911ba3-822_research_20260507T003550.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T003827.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004134.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004311.md
    src/docs/agent_handoffs/7c934759-39e_architecture_20260505T010014.md
    src/docs/agent_handoffs/7c934759-39e_develop_20260505T010359.md
    src/docs/agent_handoffs/7c934759-39e_develop_20260505T012357.md
    src/docs/agent_handoffs/7c934759-39e_develop_FAILED_20260505T011447.md
    src/docs/agent_handoffs/7c934759-39e_executor_started_20260505T005814.md
    src/docs/agent_handoffs/7c934759-39e_pm_decompose_20260505T005849.md
    src/docs/agent_handoffs/7c934759-39e_research_20260505T005919.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011016.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011949.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T012853.md
    src/docs/agent_handoffs/8a5071c5-834_architecture_20260507T003655.md
    src/docs/agent_handoffs/8a5071c5-834_deploy_FAILED_20260507T004051.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003716.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003903.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T004005.md
    src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
    src/docs/agent_handoffs/8a5071c5-834_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/8a5071c5-834_research_20260507T003540.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003737.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003929.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T004031.md
    src/docs/agent_handoffs/a77bd3b9-2db_architecture_20260507T003625.md
    src/docs/agent_handoffs/a77bd3b9-2db_deploy_FAILED_20260507T004102.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003646.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003838.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T004005.md
    src/docs/agent_handoffs/a77bd3b9-2db_executor_started_20260507T003435.md
    src/docs/agent_handoffs/a77bd3b9-2db_pm_decompose_20260507T003515.md
    src/docs/agent_handoffs/a77bd3b9-2db_research_20260507T003545.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003712.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003904.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T004042.md
    src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
    src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
    src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
    src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
    src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154631.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154838.md
    ... (共 255 个 src/ 文件)
    
    ```
    
    ### 文件: `src/frontend/agent-team-config.html`
    ```html
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>AgentsGroup2026 — 智能体团队管理</title>
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@300;400;500;700&family=Noto+Serif:wght@200;300;400;600;900&family=Noto+Serif+SC:wght@200;300;400;600;900&family=Noto+Sans+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap" rel="stylesheet">
      <link rel="stylesheet" href="/css/agent-team-config.css">
      <link rel="stylesheet" href="/css/openbridge-theme.css">
      <link rel="stylesheet" href="/css/ws-theme-bridge.css">
    </head>
    <body>
    <div class="app">
      <!-- Sidebar -->
      <div class="sidebar">
        <div class="sb-header"><h2><span class="seal">智</span> AgentsGroup</h2><select class="fi" id="team-select" style="font-size:12px;padding:6px 8px"></select></div>
        <div class="sb-nav">
          <a class="active" data-view="overview" onclick="switchView('overview')"><span class="seal">览</span> 仪表盘</a>
          <a data-view="models" onclick="switchView('models')"><span class="seal">腦</span> 模型池</a>
          <a data-view="llm" onclick="switchView('llm')"><span class="seal">接</span> LLM 配置</a>
          <a data-view="tools" onclick="switchView('tools')"><span class="seal seal-koke">具</span> 工具</a>
          <a data-view="skills" onclick="switchView('skills')"><span class="seal seal-kitsune">能</span> 技能</a>
          <a data-view="tasks" onclick="switchView('tasks')"><span class="seal">务</span> 任务</a>
          <a data-view="sessions" onclick="switchView('sessions')"><span class="seal">存</span> 会话存档</a>
          <a data-view="runtime" onclick="switchView('runtime')"><span class="seal seal-shu">行</span> Runtime</a>
          <a data-view="registry" onclick="switchView('registry')"><span class="seal">厂</span> Token 工厂</a>
        </div>
        <div class="sb-section">团队成员</div>
        <div class="sb-agents" id="sb-agents"></div>
        <div class="sb-footer"><button class="btn btn-pink btn-sm" onclick="openWizard()" style="width:100%;justify-content:center">＋ 新建智能体</button></div>
      </div>
      <!-- Main -->
      <div class="main">
        <div class="topbar"><div class="topbar-left"><h1 id="main-title">团队概览</h1><span class="badge" id="main-badge" style="background:rgba(152,245,167,0.15);color:var(--lime)"></span></div><div class="topbar-right"><a href="/plaza.html" class="btn btn-sm btn-ghost"><span class="seal">⊙</span> 智能体广场</a><a href="/system-evolution.html" class="btn btn-sm btn-ghost"><span class="seal seal-koke">进</span> 演进视图</a><button class="btn btn-sm" onclick="openModal('modal-create-team')">＋ 创建团队</button></div></div>
        <!-- Views -->
        <div id="view-overview" class="main-inner"><div class="main-scroll"><div class="card-grid" id="ov-stats"></div><div class="section" id="ov-team-section"><div class="section-title" id="ov-team-title"></div><table class="tbl"><thead><tr><th>Agent</th><th>角色</th><th>状态</th><th>技能</th><th>操作</th></tr></thead><tbody id="ov-team-agents"></tbody></table></div>
    <!-- 系统自我演进 -->
    <div class="section" id="evo-section"><div class="section-title" style="display:flex;justify-content:space-between;align-items:center">
    <span>🔄 系统自我演进</span>
    <div style="display:flex;gap:8px">
      <select class="fi" id="evo-filter" style="width:auto;padding:4px 8px;font-size:11px" onchange="loadEvolution()"><option value="">全部状态</option><option value="discovered">发现</option><option value="dispatched">已派发</option><option value="in_progress">进行中</option><option value="verify_pending">待验证</option><option value="verified">已验证</option><option value="failed">失败</option></select>
      <button class="btn btn-sm" onclick="runEvoAudit()">🔍 审查</button>
      <button class="btn btn-sm btn-pink" onclick="runEvoCycleStepper()">▶ 运行演进周期</button>
    </div>
    </div>
    <!-- Compliance Rating -->
    <div id="evo-compliance" class="card-grid" style="margin-bottom:16px"></div>
    <!-- Evolution Cycle Stepper (hidden by default) -->
    <div id="evo-stepper" class="card hidden" style="margin-bottom:16px;padding:16px">
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px">
        <div class="evo-step-item" data-step="audit"><span class="wf-dot" id="es-audit">1</span><span style="font-size:12px;margin-left:4px">审查</span></div>
        <div class="wf-connector" id="es-c1"></div>
        <div class="evo-step-item" data-step="dispatch"><span class="wf-dot" id="es-dispatch">2</span><span style="font-size:12px;margin-left:4px">派发</span></div>
        <div class="wf-connector" id="es-c2"></div>
        <div class="evo-step-item" data-step="verify"><span class="wf-dot" id="es-verify">3</span><span style="font-size:12px;margin-left:4px">验证</span></div>
        <div class="wf-connector" id="es-c3"></div>
        <div class="evo-step-item" data-step="close"><span class="wf-dot" id="es-close">4</span><span style="font-size:12px;margin-left:4px">关闭</span></div>
      </div>
      <div id="evo-stepper-log" style="font-size:12px;color:var(--muted)"></div>
    </div>
    <!-- Stats -->
    <div class="card-grid" id="evo-stats" style="margin-bottom:16px"></div>
    <!-- Zones -->
    <div id="evo-zones" style="margin-bottom:16px"></div>
    <!-- Rules -->
    <div id="evo-rules" style="margin-bottom:16px"></div>
    <!-- Items -->
    <div id="evo-items"></div>
    </div>
    </div></div>
        <div id="view-models" class="main-inner hidden"><div class="main-scroll"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">🧠 模型池</div><button class="btn btn-pink btn-sm" onclick="openModal('modal-add-model')">＋ 添加模型</button></div><table class="tbl"><thead><tr><th>ID</th><th>名称</th><th>提供商</th><th>Max Tokens</th><th>温度</th><th>默认</th><th>操作</th></tr></thead><tbody id="models-tb"></tbody></table></div></div>
        <div id="view-tools" class="main-inner hidden"><div class="main-scroll"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">🔧 可用工具</div><div style="display:flex;gap:8px"><button class="btn btn-sm" onclick="switchView('registry')">🏭 Token 工厂</button><button class="btn btn-sm" onclick="showToolSearch()">🔍 搜索</button></div></div><div id="tools-search-bar" class="hidden" style="margin-bottom:12px"><div style="display:flex;gap:10px"><input class="fi" id="tools-search-input" placeholder="搜索工具..." oninput="filterToolCards(this.value)" style="flex:1"><button class="btn btn-sm" onclick="el('tools-search-bar').classList.add('hidden')">✕</button></div></div><div id="tools-cards"></div></div></div>
        <div id="view-skills" class="main-inner hidden"><div class="main-scroll"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">⚡ 可用技能</div><div style="display:flex;gap:8px"><button class="btn btn-sm" onclick="switchView('registry')">📥 导入</button><button class="btn btn-sm" onclick="exportSkillsMD()">📤 导出</button></div></div><div id="skills-cards"></div></div></div>
        <div id="view-tasks" class="main-inner hidden"><div class="main-scroll"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">📋 并发任务</div><div style="display:flex;gap:8px"><span id="task-stats" style="font-size:12px;color:var(--muted);display:flex;align-items:center"></span><button class="btn btn-pink btn-sm" onclick="openModal('modal-add-task')">＋ 提交任务</button><button class="btn btn-sm" onclick="openModal('modal-batch-task')">📦 批量提交</button></div></div><table class="tbl"><thead><tr><th>ID</th><th>标题</th><th>Agent</th><th>优先级</th><th>依赖</th><th>状态</th><th>操作</th></tr></thead><tbody id="tasks-tb"></tbody></table></div></div>
        <div id="view-llm" class="main-inner hidden"><div class="main-scroll">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">🔌 LLM 提供商配置</div><button class="btn btn-pink btn-sm" onclick="testLLM()">🧪 测试连接</button></div>
          <div id="llm-status-card" class="card" style="margin-bottom:20px;padding:20px"><p style="color:var(--dim)">加载中...</p></div>
          <div class="card" style="padding:20px;margin-bottom:20px">
            <div class="section-title" style="margin-top:0;margin-bottom:12px">⚙️ 配置 LLM 提供商</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
              <div class="form-group"><label class="form-label">提供商</label><select class="fi" id="llm-provider"><option value="deepseek">DeepSeek</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="local">本地 (Ollama/vLLM)</option><option value="openrouter">OpenRouter</option><option value="github">GitHub Models</option><option value="qwen">通义千问</option></select></div>
              <div class="form-group"><label class="form-label">模型</label><input class="fi" id="llm-model" placeholder="deepseek-v4-pro"></div>
              <div class="form-group"><label class="form-label">API Key</label><input class="fi" id="llm-key" type="password" placeholder="sk-..."></div>
              <div class="form-group"><label class="form-label">API Base URL (可选)</label><input class="fi" id="llm-url" placeholder="https://api.deepseek.com"></div>
              <div class="form-group"><label class="form-label">Max Tokens</label><input class="fi" id="llm-tokens" type="number" value="4096" min="100" max="128000"></div>
              <div class="form-group"><label class="form-label">温度</label><input class="fi" id="llm-temp" type="number" value="0.7" min="0" max="2" step="0.1"></div>
            </div>
            <div style="margin-top:16px;display:flex;gap:10px"><button class="btn btn-pink" onclick="saveLLMConfig()">💾 保存配置</button><button class="btn" onclick="loadLLMStatus()">🔄 刷新状态</button></div>
          </div>
          <div id="llm-test-result" class="card hidden" style="padding:20px"><div class="section-title" style="margin-top:0;margin-bottom:8px">🧪 测试结果</div><div id="llm-test-content"></div></div>
          <!-- TTS Config Section -->
          <div class="card" style="padding:20px;margin-bottom:20px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><div class="section-title" style="margin-top:0;margin-bottom:0">🔊 TTS 语音合成配置</div><div style="display:flex;gap:8px"><span id="tts-status-badge" class="badge" style="font-size:11px">检测中...</span><button class="btn btn-sm" onclick="testTTSConnection()">🧪 测试</button><button class="btn btn-pink btn-sm" onclick="startTTSService()">▶ 启动服务</button></div></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
              <div class="form-group"><label class="form-label">TTS 引擎</label><select class="fi" id="tts-engine"><option value="gpt-sovits">GPT-SoVITS</option><option value="edge-tts">Edge TTS (在线)</option><option value="web-speech">浏览器内置</option></select></div>
              <div class="form-group"><label class="form-label">API 地址</label><input class="fi" id="tts-api-url" placeholder="http://127.0.0.1:9880"></div>
              <div class="form-group"><label class="form-label">参考音频路径</label><input class="fi" id="tts-ref-audio" placeholder="ref_audio/male_sample.wav"></div>
              <div class="form-group"><label class="form-label">参考音频文本</label><input class="fi" id="tts-prompt-text" placeholder="参考音频对应的文字内容"></div>
              <div class="form-group"><label class="form-label">语言</label><select class="fi" id="tts-lang"><option value="zh">中文</option><option value="en">English</option><option value="ja">日本語</option><option value="auto">自动</option></select></div>
              <div class="form-group"><label class="form-label">语速</label><input class="fi" id="tts-speed" type="number" value="1.0" min="0.5" max="2.0" step="0.1"></div>
            </div>
            <div style="margin-top:16px;display:flex;gap:10px"><button class="btn btn-pink" onclick="saveTTSConfig()">💾 保存 TTS 配置</button><button class="btn" onclick="loadTTSConfig()">🔄 刷新</button></div>
            <div id="tts-test-result" style="margin-top:12px;font-size:12px;color:var(--dim)"></div>
          </div>
          <div class="card" style="padding:20px"><div class="section-title" style="margin-top:0;margin-bottom:8px">📊 会话列表</div><div id="llm-sessions"></div></div>
        </div></div>
        <div id="view-agent" class="main-inner hidden">
        <!-- Session Persistence View -->
        <div id="view-sessions" class="main-inner hidden"><div class="main-scroll">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">💾 会话存档管理</div><div style="display:flex;gap:8px"><button class="btn btn-sm" onclick="loadPersistedSessions()">🔄 刷新</button></div></div>
          <div class="card" style="margin-bottom:20px;padding:20px">
            <div class="section-title" style="margin-top:0;margin-bottom:12px">🔍 跨会话搜索</div>
            <div style="display:flex;gap:10px"><input class="fi" id="ss-query" placeholder="搜索所有持久化会话的内容..." style="flex:1" onkeydown="if(event.key==='Enter')searchPersistedSessions()"><button class="btn btn-pink btn-sm" onclick="searchPersistedSessions()">搜索</button></div>
            <div id="ss-search-results" style="margin-top:12px"></div>
          </div>
          <div class="card" style="padding:20px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><div class="section-title" style="margin:0">📁 已保存的会话</div><span id="ss-count" style="color:var(--dim);font-size:12px"></span></div>
            <div id="ss-list"></div>
          </div>
        </div></div>
        <!-- PortRuntime View -->
        <div id="view-runtime" class="main-inner hidden"><div class="main-scroll">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">🚀 PortRuntime 路由引擎</div></div>
          <div class="card" style="margin-bottom:20px;padding:20px">
            <div class="section-title" style="margin-top:0;margin-bottom:12px">🎯 Prompt 路由</div>
            <p style="color:var(--muted);font-size:12px;margin-bottom:14px">输入自然语言指令，系统将自动匹配最佳工具和命令 (claw-code-parity PortRuntime)</p>
            <div style="display:grid;gap:12px">
              <div class="form-group" style="margin:0"><label class="form-label">Prompt</label><textarea class="fi" id="rt-prompt" rows="3" placeholder="例: 检查主机状态并分析油温趋势"></textarea></div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
                <div class="form-group" style="margin:0"><label class="form-label">最大匹配数</label><input class="fi" id="rt-limit" type="number" value="5" min="1" max="20"></div>
                <div class="form-group" style="margin:0"><label class="form-label">禁用工具 (逗号分隔)</label><input class="fi" id="rt-deny" placeholder="web_search, run_python"></div>
                <div class="form-group" style="margin:0"><label class="form-label">禁用前缀</
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

🔗 API: api.deepseek.com | 模型: deepseek-chat
────────────────────────────────────────────────────────────

# 技术调研报告 — 硬编码基线到 CI 门禁，实现模型更新自动重算并投射为业务方可读的实时契约仪表

## 1. 任务理解与范围界定

### 核心需求分解
1. **硬编码基线到 CI 门禁** — 将模型版本/配置作为不可变基线，集成到 CI/CD 流水线中作为门禁检查
2. **模型更新自动重算** — 当模型更新时，自动触发契约/指标的重新计算
3. **实时契约仪表** — 将计算结果投射为业务方可读的实时仪表板

### 技术栈映射
- 后端: Python FastAPI (`src/backend/`)
- 前端: HTML + JS (`src/frontend/`)
- 现有演进系统: `system_evolution.py`, `plaza_monitor.py`
- 现有模型管理: `models.py`, `chat_harness.py`

## 2. 现有系统分析

### 2.1 模型管理相关文件

| 文件 | 路径 | 关键功能 |
|------|------|----------|
| 模型定义 | `src/backend/agents/models.py` | `AgentProfile`, `ModelConfig`, `HermesAgentConfig` |
| 模型池 | `src/frontend/agent-team-config.html` | 前端模型池视图 (view-models) |
| LLM配置 | `src/backend/agents/chat_harness.py` | `ProviderConfig`, `LLMProvider` 枚举 |
| 执行注册表 | `src/backend/agents/execution_registry.py` | `ToolPool`, `PortRuntime` |

### 2.2 演进/监控相关文件

| 文件 | 路径 | 关键功能 |
|------|------|----------|
| 系统演进 | `src/backend/channels/system_evolution.py` | 演进引擎核心逻辑 |
| 监控收集 | `src/backend/monitoring/collector.py` | 指标收集 |
| 监控模型 | `src/backend/monitoring/models.py` | 监控数据模型 |
| 广场监控 | `src/backend/monitoring/plaza_monitor.py` | 广场监控逻辑 |
| 采样器 | `src/backend/monitoring/sampler.py` | 数据采样 |

### 2.3 前端仪表相关文件

| 文件 | 路径 | 关键功能 |
|------|------|----------|
| 团队配置 | `src/frontend/agent-team-config.html` | 主管理界面，含演进视图 |
| 演进视图 | `src/frontend/system-evolution.html` | 系统演进专用页面 |
| 数据中心棘轮 | `src/frontend/datacenter-ratchet-evolution.html` | 棘轮演进视图 |
| JS逻辑 | `src/frontend/js/agent-team-config.js` | 前端核心逻辑 |

## 3. 技术方案设计

### 3.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Code     │→ │ Build    │→ │ Test     │→ │ Deploy   │   │
│  │ Commit   │  │          │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                      │              │                       │
│                      ▼              ▼                       │
│              ┌──────────────┐ ┌──────────────┐             │
│              │ Model        │ │ Contract     │             │
│              │ Baseline     │ │ Compliance   │             │
│              │ Gate         │ │ Gate         │             │
│              └──────────────┘ └──────────────┘             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AgentsGroup2026 Backend                   │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Contract Engine  │  │ Recalculation    │                │
│  │ (新模块)         │  │ Scheduler (新)   │                │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Model Registry   │  │ Evolution Engine │                │
│  │ (扩展 models.py) │  │ (system_evolution)│               │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Contract Dashboard (新页面/扩展现有视图)              │   │
│  │  - 模型基线状态                                       │   │
│  │  - 契约合规评分                                       │   │
│  │  - 自动重算历史                                       │   │
│  │  - 实时指标卡片                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心模块设计

#### 模块1: 模型基线引擎 (`src/backend/agents/model_baseline.py` — 新文件)

```python
# 核心数据结构
@dataclass
class ModelBaseline:
    """模型基线定义"""
    baseline_id: str
    model_name: str
    model_version: str
    provider: str
    config_hash: str  # 配置的SHA256哈希
    created_at: str
    frozen: bool = True  # 基线不可变
    contracts: List[ContractDefinition] = field(default_factory=list)

@dataclass
class ContractDefinition:
    """契约定义"""
    contract_id: str
    name: str
    description: str
    metric: str  # 指标名称
    threshold: float  # 阈值
    operator: str  # >=, <=, ==, between
    severity: str  # critical, warning, info
    auto_recalculate: bool = True

@dataclass
class ContractResult:
    """契约计算结果"""
    contract_id: str
    baseline_id: str
    actual_value: float
    passed: bool
    calculated_at: str
    model_version: str
    details: Dict[str, Any]
```

#### 模块2: CI门禁集成 (`src/backend/agents/ci_gate.py` — 新文件)

```python
class CIGate:
    """CI门禁检查器"""
    
    def check_model_baseline(self, model_config: Dict) -> GateResult:
        """检查模型配置是否与基线一致"""
        
    def check_contract_compliance(self, baseline_id: str) -> GateResult:
        """检查契约合规性"""
        
    def generate_gate_report(self) -> Dict:
        """生成门禁报告"""
```

#### 模块3: 自动重算调度器 (`src/backend/agents/recalculation_scheduler.py` — 新文件)

```python
class RecalculationScheduler:
    """模型更新自动重算调度器"""
    
    async def on_model_update(self, model_id: str):
        """模型更新时触发重算"""
        
    async def recalculate_contracts(self, baseline_id: str):
        """重新计算所有关联契约"""
        
    def get_recalculation_history(self) -> List[RecalculationRecord]:
        """获取重算历史"""
```

### 3.3 需要修改的现有文件

#### 文件1: `src/backend/agents/models.py`
**修改��:**
- 添加 `ModelBaseline` 相关数据类
- 添加 `ContractDefinition` 和 `ContractResult` 数据类
- 扩展 `AgentProfile` 以支持基线关联

#### 文件2: `src/backend/agents/chat_harness.py`
**修改点:**
- 在 `ProviderConfig` 中添加基线版本追踪
- 添加模型更新事件钩子

#### 文件3: `src/backend/channels/system_evolution.py`
**修改点:**
- 集成基线检查到演进流程
- 添加契约合规作为演进指标

#### 文件4: `src/backend/monitoring/collector.py`
**修改点:**
- 添加契约指标收集
- 添加基线状态监控

#### 文件5: `src/frontend/agent-team-config.html`
**修改点:**
- 在现有视图结构中添加"契约仪表"视���
- 添加基线管理UI组件
- 添加实时指标卡片

#### 文件6: `src/frontend/js/agent-team-config.js`
**修改点:**
- 添加契约仪表相关API调用
- 添加基线管理逻辑
- 添加实时数据刷新机制

#### 文件7: `src/frontend/system-evolution.html`
**修改点:**
- 集成契约合规视图
- 添加基线演进时间线

### 3.4 需要创建的新文件

| 文件路径 | 用途 |
|----------|------|
| `src/backend/agents/model_baseline.py` | 模型基线引擎核心逻辑 |
| `src/backend/agents/ci_gate.py` | CI门禁检查器 |
| `src/backend/agents/recalculation_scheduler.py` | 自动重算调度器 |
| `src/backend/agents/contract_routes.py` | 契约相关API路由 |
| `src/frontend/contract-dashboard.html` | 契约仪表专用页面 |
| `src/frontend/css/contract-dashboard.css` | 契约仪表样式 |
| `src/frontend/js/contract-dashboard.js` | 契约仪表逻辑 |
| `src/backend/scripts/ci_gate_check.py` | CI门禁检查脚本 |

## 4. 实现可行性分析

### 4.1 技术可行性 ✅

| 方面 | 评估 | 说明 |
|------|------|------|
| 后端架构 | ✅ 可行 | FastAPI支持异步事件驱动，适合重算调度 |
| 前端框架 | ✅ 可行 | 现有HTML+JS架构可扩展，无需引入新框架 |
| 数据持久化 | ✅ 可行 | 现有session_store/task_store模式可复用 |
| CI集成 | ✅ 可行 | 可通过CLI脚本或API调用实现门禁检查 |
| 实时更新 | ✅ 可行 | 可通过SSE或WebSocket实现实时推送 |

### 4.2 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 模型更新频繁导致重算风暴 | 实现去重和节流机制，设置最小重算间隔 |
| 基线版本管理复杂 | 使用语义化版本号 + 配置哈希双重校验 |
| 前端实时性能 | 使用虚拟滚动和增量更新 |
| 与现有演进系统冲突 | 设计清晰的接口边界，通过事件总线解耦 |

## 5. 实施路线图

### Phase 1: 核心引擎 (2-3天)
1. 创建 `model_baseline.py` — 基线定义与存储
2. 创建 `contract_routes.py` — 契约CRUD API
3. 修改 `models.py` — 添加数据模型

### Phase 2: CI门禁 (1-2天)
1. 创建 `ci_gate.py` — 门禁检查逻辑
2. 创建 `ci_gate_check.py` — CLI检查脚本
3. 编写CI配置文件示例 (`.github/workflows/` 或 `Jenkinsfile`)

### Phase 3: 自动重算 (1-2天)
1. 创建 `recalculation_scheduler.py` — 调度器
2. 集成到现有模型更新流程
3. 添加事件监听机制

### Phase 4: 前端仪表 (2-3天)
1. 创建 `contract-dashboard.html` — 仪表页面
2. 创建 `contract-dashboard.js` — 前端逻辑
3. 修改 `agent-team-config.html` — 集成到主界面
4. 添加实时数据刷新

### Phase 5: 测试与集成 (1-2天)
1. 单元测试
2. 集成测试
3. 端到端测试
4. 文档编写

## 6. 关键设计决策

### 6.1 基线不可变性
- 基线一旦创建即为不可变（frozen）
- 模型更新必须创建新基线
- 旧基线保留用于审计和回滚

### 6.2 契约定义
- 支持多种指标类型（数值、布尔、百分比）
- 支持复合条件（AND/OR）
- 支持自定义严重级别

### 6.3 重算触发机制
- 事件驱动：模型更新事件 → 自动重算
- 定时触发：可配置���定期重算
- 手动触发：管理员手动触发

### 6.4 前端实时性
- 使用Server-Sent Events (SSE) 推送实时更新
- 支持WebSocket作为备选
- 降级到轮询机制

## 7. 总结

本方案充分利用了AgentsGroup2026现有架构：
- **复用** `system_evolution.py` 的演进引擎模式
- **扩展** `models.py` 的数据模型
- **集成** 现有前端框架和样式系统
- **兼容** 现有的监控和收集体系

核心创新点：
1. 将模型配置作为不可变基线引入CI门禁
2. 事件驱动的自动重算机制
3. 业务方可读的实时契约仪表

建议优先实现Phase 1和Phase 2，快速验证核心流程，再逐步完善前端和自动化功能。

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
