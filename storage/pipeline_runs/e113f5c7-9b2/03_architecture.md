# 架构设计 — architect

任务: 实现 Skill 沉淀交互页面：包含半自动提炼向导（异步 LLM 预填、对比视图编辑）、待审核队列红绿灯可视化与 SSE 实时推送，用户确认后触发 SkillApproved 事件写入主表。
步骤: architecture
Agent: build_architect

---

📋 任务: e113f5c7-9b2
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
  实现 Skill 沉淀交互页面：包含半自动提炼向导（异步 LLM 预填、对比视图编辑）、待审核队列红绿灯可视化与 SSE 实时推送，用户确认后触发 SkillApproved 事件写入主表。
  Developer, Researcher
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
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
  src/backend/tests/__init__.py
  src/backend/tests/conftest.py
  src/backend/tests/conftest.py.bak
  src/backend/tests/test_ab_testing.py
  src/backend/tests/test_agent_toolbox.py
  src/backend/tests/test_models.py
  src/backend/tests/test_models.py.bak
  src/backend/tests/test_task_engine.py
  src/backend/tests/test_task_engine.py.bak
  src/backend/tests/test_team_manager.py
  src/backend/tests/test_team_manager.py.bak
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
  src/backend/channels/evolution_executor.py
  src/backend/channels/marine_base.py
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
  src/docs/agent_handoffs/11e9b4b9-283_executor_started_20260509T074916.md
  src/docs/agent_handoffs/11e9b4b9-283_pm_decompose_20260509T075116.md
  src/docs/agent_handoffs/1356f045-d02_executor_started_20260509T073232.md
  src/docs/agent_handoffs/15554439-6aa_executor_started_20260509T073231.md
  src/docs/agent_handoffs/15a7e2eb-cd1_executor_started_20260509T073232.md
  src/docs/agent_handoffs/18d4b20f-c33_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1aed56ed-eda_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1cc2c0fb-90b_executor_started_20260509T073232.md
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
  src/docs/agent_handoffs/1d2d7607-8a3_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1e04fc38-6e9_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1f835c25-c0f_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1fd87e2e-962_executor_started_20260509T073232.md
  src/docs/agent_handoffs/21750a9a-2ff_executor_started_20260509T073231.md
  src/docs/agent_handoffs/21ef94ba-2b6_executor_started_20260509T074916.md
  src/docs/agent_handoffs/21ef94ba-2b6_pm_decompose_20260509T075106.md
  src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/2da416d2-cdf_executor_started_20260509T074916.md
  src/docs/agent_handoffs/2da416d2-cdf_pm_decompose_20260509T075121.md
  src/docs/agent_handoffs/32a3b057-166_executor_started_20260509T073232.md
  src/docs/agent_handoffs/34efc37e-3a1_executor_started_20260509T073231.md
  src/docs/agent_handoffs/35b91517-bfb_executor_started_20260509T073231.md
  src/docs/agent_handoffs/35f5eb68-2b7_executor_started_20260509T073232.md
  src/docs/agent_handoffs/38c98cf4-15b_executor_started_20260509T073231.md
  src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
  src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
  src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
  src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
  src/docs/agent_handoffs/39c0911d-173_executor_started_20260509T073232.md
  src/docs/agent_handoffs/3bde709e-2fe_architecture_20260507T031839.md
  src/docs/agent_handoffs/3bde709e-2fe_deploy_FAILED_20260507T033021.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T031910.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032452.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032630.md
  src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
  src/docs/agent_handoffs/3bde709e-2fe_pm_decompose_20260507T031529.md
  src/docs/agent_handoffs/3bde709e-2fe_research_20260507T031614.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T031936.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032523.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032706.md
  src/docs/agent_handoffs/3f9494e1-96d_executor_started_20260509T074916.md
  src/docs/agent_handoffs/3f9494e1-96d_pm_decompose_20260509T075056.md
  src/docs/agent_handoffs/3f9494e1-96d_research_20260509T075256.md
  src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
  src/docs/agent_handoffs/4601c322-51d_executor_started_20260509T075153.md
  src/docs/agent_handoffs/4601c322-51d_pipeline_complete_20260509T075233.md
  ... (共 529 个 src/ 文件)
  
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
            <div class="form-group"><label class="form-label">提供商</label><select class="fi" id="llm-provider" onchange="syncLLMModelTierAvailability();syncLLMModelTierFromInput()"><option value="deepseek">DeepSeek</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="local">本地 (Ollama/vLLM)</option><option value="openrouter">OpenRouter</option><option value="github">GitHub Models</option><option value="qwen">通义千问</option></select></div>
            <div class="form-group"><label class="form-label">模型</label><input class="fi" id="llm-model" placeholder="deepseek-v4-flash" oninput="syncLLMModelTierFromInput()"></div>
            <div class="form-group" id="llm-model-tier-wrap">
              <label class="form-label">DeepSeek 档位</label>
              <div style="display:inline-flex;align-items:center;gap:0;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:rgba(0,0,0,0.08)">
                <input type="checkbox" id="llm-model-tier" onchange="onLLMModelTierToggle(this.checked)" style="display:none">
                <button type="button" id="llm-tier-flash" onclick="setLLMModelTier(false)" style="padding:6px 14px;border:none;background:transparent;color:var(--dim);font-size:12px;cursor:pointer;min-width:72px">Flash</button>
                <button type="button" id="llm-tier-pro" onclick="setLLMModelTier(true)" style="padding:6px 14px;border:none;background:transparent;color:var(--dim);font-size:12px;cursor:pointer;min-width:72px;border-left:1px solid var(--line)">Pro</button>
              </div>
              <div style="font-size:11px;color:var(--dim);margin-top:6px">点击按钮切换：Flash 或 Pro</div>
            </div>
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
        <div style="display:flex;justify-content:space-between;align-items:c
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
      for m in team.models.values():
          if m.is_default:
              default_model = m
              break
      if default_model is None:
          return
      harness.update_default_provider(
          provider=default_model.provider,
          api_key=default_model.api_key,
          api_base_url=default_model.api_base_url,
          model=default_model.name,
      )
      cfg = harness.get_provider_config()
      cfg.max_tokens = default_model.max_tokens
      cfg.temperature = default_model.temperature
  
  
  @router.delete(
      "/teams/{team_id}/models/{model_id}",
      summary="Remove model from team",
  )
  def remove_model(team_id: str, model_id: str) -> Dict[str, str]:
      removed = _tm().remove_model_from_team(team_id, model_id)
      if removed is None:
          raise HTTPException(status.HTTP_404_NOT_FOUND, d
  ```
  
  ### 文件: `src/backend/agents/models.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Agent Team Framework — Core Data Models.
  
  Inspired by Clawith platform architecture:
  - AgentTeam = Company (team-level resource sharing)
  - AgentProfile = Employee (individual agent with personality/skills/permissions)
  - ModelConfig = Model Pool entry
  - ToolDefinition = Tool catalog entry
  - SkillDefinition = Skill catalog entry
  """
  
  from __future__ import annotations
  
  import uuid
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from enum import Enum
  from typing import Any, Dict, List, Optional
  
  
  # ── Enums ──────────────────────────────────────────────────────────────────
  
  
  class AgentState(Enum):
      """Agent lifecycle states."""
  
      IDLE = "idle"
      WORKING = "working"
      PAUSED = "paused"
      ERROR = "error"
      STOPPED = "stopped"
  
  
  class ToolCategory(Enum):
      """Tool classification categories."""
  
      GENERAL = "general"
      BROWSER = "browser"
      CODE_EXECUTION = "code_execution"
      COMMUNICATION = "communication"
      FILE_OPERATION = "file_operation"
      TRIGGERS = "triggers"
      DISCOVERY = "discovery"
      DIGITAL_TWIN = "digital_twin"
      # Hermes-style tool categories
      WEB = "web"
      VISION = "vision"
      MEMORY = "memory"
      SKILLS = "skills"
      DELEGATION = "delegation"
  
  
  class SkillCategory(Enum):
      """Skill classification categories."""
  
      GENERAL = "general"
      DIGITAL_TWIN = "digital_twin"
      AUTOMATION = "automation"
      # Hermes-style skill categories
      RESEARCH = "research"
      DOMAIN_KNOWLEDGE = "domain_knowledge"
  
  
  class Visibility(Enum):
      """Visibility level for teams/agents."""
  
      PUBLIC = "public"
      PRIVATE = "private"
      INTERNAL = "internal"
  
  
  class AccessLevel(Enum):
      """Permission access levels."""
  
      READ = "read"
      WRITE = "write"
      ADMIN = "admin"
  
  
  class AgentTemplateType(Enum):
      """Predefined agent template types."""
  
      RESEARCHER = "researcher"
      DEVELOPER = "developer"
      ANALYST = "analyst"
      ENGINEER = "engineer"
      COORDINATOR = "coordinator"
      CUSTOM = "custom"
      # Hermes-style agent types
      HERMES_RESEARCHER = "hermes_researcher"
      HERMES_DEVELOPER = "hermes_developer"
      HERMES_CREATIVE = "hermes_creative"
  
  
  # ── Dataclasses ────────────────────────────────────────────────────────────
  
  
  @dataclass
  class ModelConfig:
      """LLM model configuration entry."""
  
      model_id: str = ""
      provider: str = "anthropic"
      name: str = "claude-sonnet-4-20250514"
      max_tokens: int = 65536
      temperature: float = 0.7
      is_default: bool = False
      enabled: bool = True
      api_key: str = ""
      api_base_url: str = ""
  
      def __post_init__(self) -> None:
          if not self.model_id:
              self.model_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "model_id": self.model_id,
              "provider": self.provider,
              "name": self.name,
              "max_tokens": self.max_tokens,
              "temperature": self.temperature,
              "is_default": self.is_default,
              "enabled": self.enabled,
              "api_key": ("****" + self.api_key[-4:]) if len(self.api_key) >= 4 else ("****" if self.api_key else ""),
              "api_base_url": self.api_base_url,
              "has_api_key": bool(self.api_key),
          }
  
  
  @dataclass
  class ToolDefinition:
      """Tool catalog entry."""
  
      tool_id: str = ""
      name: str = ""
      description: str = ""
      category: ToolCategory = ToolCategory.BROWSER
      enabled: bool = True
      requires_approval: bool = False
      parameters: Dict[str, Any] = field(default_factory=dict)
      icon: str = "🔧"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
  
      def __post_init__(self) -> None:
          if not self.tool_id:
              self.tool_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tool_id": self.tool_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "enabled": self.enabled,
              "requires_approval": self.requires_approval,
              "parameters": self.parameters,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
          }
  
  
  @dataclass
  class SkillDefinition:
      """Skill catalog entry."""
  
      skill_id: str = ""
      name: str = ""
      description: str = ""
      category: SkillCategory = SkillCategory.GENERAL
      required: bool = False
      enabled: bool = True
      icon: str = "⚡"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
      slug: str = ""
      required_tools: List[str] = field(default_factory=list)
      instructions: str = ""
  
      def __post_init__(self) -> None:
          if not self.skill_id:
              self.skill_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "skill_id": self.skill_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "required": self.required,
              "enabled": self.enabled,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
              "slug": self.slug,
              "required_tools": self.required_tools,
              "has_instructions": bool(self.instructions),
          }
  
  
  @dataclass
  class AgentPersonality:
      """Agent personality and behavior configuration."""
  
      tone: str = "professional"
      language: str = "zh-CN"
      expertise_areas: List[str] = field(default_factory=list)
      response_style: str = "concise"
      creativity: float = 0.5
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tone": self.tone,
              "language": self.language,
              "expertise_areas": self.expertise_areas,
              "response_style": self.response_style,
              "creativity": self.creativity,
          }
  
  
  @dataclass
  class ToolsetDistribution:
      """Hermes-style probabilistic toolset distribution.
  
      Each toolset has a % probability of being available per turn.
      Inspired by NousResearch/hermes-agent toolset_distributions.py.
      """
  
      name: str = "default"
      description: str = ""
      toolsets: Dict[str, int] = field(default_factory=dict)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "name": self.name,
              "description": self.description,
              "toolsets": self.toolsets,
          }
  
  
  @dataclass
  class HermesAgentConfig:
      """Hermes-style agent configuration — extends AgentProfile with
      learning loop, memory, skills, toolsets, and context management.
  
      Inspired by NousResearch/hermes-agent architecture:
      - Closed learning loop (skills from experience)
      - Persistent memory across sessions
      - Toolset distributions for probabilistic tool access
      - SOUL.md persona
      - Context files (AGENTS.md, HERMES.md)
      - Session search (cross-session recall)
      - Delegate/subagent parallelization
      """
  
      # Agent loop parameters
      max_iterations: int = 90
      iteration_budget: int = 90
  
      # Toolset distribution (Hermes-style probabilistic tool selection)
      toolset_distribution: ToolsetDistribution = field(
          default_factory=lambda: ToolsetDistribution(name="default")
      )
      enabled_toolsets: List[str] = field(default_factory=list)
      disabled_toolsets: List[str] = field(default_factory=list)
  
      # Memory & learning
      memory_enabled: bool = True
      session_search_enabled: bool = True
      skill_auto_create: bool = True
      soul_md: str = ""
      context_files: List[str] = field(default_factory=list)
  
      # Delegation
      can_delegate: bool = False
      max_subagents: int = 3
  
      # Platform
      platform: str = "cli"
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "max_iterations": self.max_iterations,
              "iteration_budget": self.iteration_budget,
              "toolset_distribution": self.toolset_distribution.to_dict(),
              "enabled_toolsets": self.enabled_toolsets,
              "disabled_toolsets": self.disabled_toolsets,
              "memory_enabled": self.memory_enabled,
              "session_search_enabled": self.session_search_enabled,
              "skill_auto_create": self.skill_auto_create,
              "soul_md": self.soul_md,
              "context_files": self.context_files,
              "can_delegate": self.can_delegate,
              "max_subagents": self.max_subagents,
              "platform": self.platform,
          }
  
  
  @dataclass
  class AgentPermission:
      """Agent access permission."""
  
      resource: str = ""
      access_level: AccessLevel = AccessLevel.READ
      channels: List[str] = field(default_factory=list)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "resource": self.resource,
              "access_level": self.access_level.value,
              "channels": self.channels,
          }
  
  
  @dataclass
  class AgentChannelConfig:
      """Channel subscription configuration for an agent."""
  
      channel_name: str = ""
      subscribe: bool = True
      publish: bool = False
      priority: int = 0
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "channel_name": self.channel_name,
              "subscribe": self.subscribe,
              "publish": self.publish,
              "priority": self.priority,
          }
  
  
  @dataclass
  class AgentProfile:
      """Individual agent profile — the Employee equivalent."""
  
      agent_id: str = ""
      name: str = ""
      role: str = ""
      description: str = ""
      template_type: AgentTemplateType = AgentTemplateType.CUSTOM
      state: AgentState = AgentState.IDLE
      model_id: str = ""
      system_prompt: str = ""
      personality: AgentPersonality = field(default_factory=AgentPersonality)
      permissions: List[AgentPermission] = field(default_factory=list)
      channels: List[AgentChannelConfig] = field(default_factory=list)
      tools: List[str] = field(default_factory=list)
      skills: List[str] = field(default_factory=list)
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
      # Hermes-style agent config (optional — non-None means Hermes mode)
      hermes_config: Optional[HermesAgentConfig] = None
  
      def __post_init__(self) -> None:
          if not self.agent_id:
              self.agent_id = str(uuid.uuid4())[:8]
  
      @property
      def is_hermes_agent(self) -> bool:
          return self.hermes_config is not None
  
      def to_dict(self) -> Dict[str, Any]:
          d = {
              "agent_id": self.agent_id,
              "name": self.name,
              "role": self.role,
              "description": self.description,
              "template_type": self.template_type.value,
              "state": self.state.value,
              "model_id": self.model_id,
              "system_prompt": self.system_prompt,
              "personality": self.personality.to_dict(),
              "permissions": [p.to_dict() for p in self.permissions],
              "channels": [c.to_dict() for c in self.channels],
              "tools": self.tools,
              "skills": self.skills,
              "metadata": self.metadata,
              "created_at": self.created_at,
              "is_hermes_agent": self.is_hermes_agent,
          }
          if self.hermes_config is not None:
              d["hermes_config"] = self.hermes_config.to_dict()
          return d
  
  
  @dataclass
  class AgentTeam:
      """Agent team — the Company equivalent. Holds shared resources."""
  
      team_id: str = ""
      name: str = ""
      description: str = ""
      visibility: Visibility = Visibility.PRIVATE
      agents: Dict[str, AgentProfile] = field(default_factory=dict)
      models: Dict[str, ModelConfig] = field(default_factory=dict)
      tools: Dict[str, ToolDefinition] = field(default_factory=dict)
      skills: Dict[str, SkillDefinition] = field(default_factory=dict)
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
  
      def __post_init__(self) -> None:
          if not self.team_id:
              self.team_id = str(uuid.uuid4())[:8]
  
      def add_agent(self, agent: AgentProfile) -> None:
          self.agents[agent.agent_id] = agent
  
      def remove_agent(self, agent_id: str) -> Optional[AgentProfile]:
          return self.agents.pop(agent_id, None)
  
      def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
          return self.agents.get(agent_id)
  
      def add_model(self, model: ModelConfig) -> None:
          self.models[model.model_id] = model
  
      def remove_model(self, model_id: str) -> Optional[ModelConfig]:
          return self.models.pop(model_id, None)
  
      def get_model(self, model_id: str) -> Optional[ModelConfig]:
          return self.models.get(model_id)
  
      def add_tool(self, tool: ToolDefinition) -> None:
          self.tools[tool.tool_id] = tool
  
      def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
          return self.tools.get(tool_id)
  
      def add_skill(self, skill: SkillDefinition) -> None:
          self.skills[skill.skill_id] = skill
  
      def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
          return self.skills.get(skill_id)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "team_id": self.team_id,
              "name": self.name,
              "description": self.description,
              "visibility": self.visibility.value,
              "agents": {k: v.to_dict() for k, v in self.agents.items()},
              "models": {k: v.to_dict() for k, v in self.models.items()},
              "tools": {k: v.to_dict() for k, v in self.tools.items()},
              "skills": {k: v.to_dict() for k, v in self.skills.items()},
              "metadata": self.metadata,
              "created_at": self.created_at,
          }
  
  ```
  
  ### 文件: `src/backend/agents/plaza_engine.py`
  ```py
  # -*- coding: utf-8 -*-
  """智能体广场引擎 — 讨论编排与多 Agent 协同.
  
  核心编排逻辑:
  1. Moderator（主持人壁龛）提出子话题，引导讨论方向
  2. 每轮: 各参与者按座席层级依次发言（内圈→中圈→外圈）
  3. Moderator 总结本轮关键观点
  4. 最终轮: Moderator 生成全局总结 + 关键结论
  
  消息通过 asyncio.Queue 实时推送给 SSE 订阅者。
  """
  
  from __future__ import annotations
  
  import asyncio
  import json
  import logging
  import re
  from datetime import datetime, timezone
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional
  from uuid import uuid4
  
  from .plaza import (
      Discussion, DiscussionStatus, NicheRole, Participant,
      Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
  )
  from .plaza_store import PlazaStore
  
  logger = logging.getLogger(__name__)
  
  _ROUND_SPEAKER_LIMIT = 5
  _EXCHANGES_PER_ROUND = 2  # 每轮内交锋次数
  _SPEAKERS_PER_EXCHANGE = 3  # 每次交锋参与人数
  _CORE_ROLE_PRIORITY = {
      "architect": 0,
      "researcher": 1,
      "developer": 2,
      "qa_engineer": 3,
      "qa": 3,
      "tester": 3,
      "devops": 4,
      "project_manager": 5,
      "documentation": 6,
  }
  
  
  class PlazaEngine:
      """广场引擎 — 管理广场、参与者和讨论编排."""
  
      def __init__(self):
          self._store = PlazaStore()
          self._plazas: Dict[str, Plaza] = self._store.load_all()
          self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
          self._discussion_locks: Dict[str, asyncio.Lock] = {}
          self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference
  
      def set_chat_fn(self, fn: Callable):
          """注入 ChatHarness.chat 异步函数."""
          self._chat_fn = fn
  
      def _get_agent_profile(self, agent_id: str):
          """从 TeamManager 获取完整 AgentProfile，用于注入个性."""
          try:
              from agents.api import _team_manager
              if _team_manager:
                  for team in _team_manager.list_teams():
                      agent = team.get_agent(agent_id)
                      if agent:
                          return agent
          except Exception:
              pass
          return None
  
      def _build_agent_system_prompt(self, participant: Participant) -> str:
          """根据 AgentProfile 构建有个性的 system prompt."""
          profile = self._get_agent_profile(participant.agent_id)
          if profile:
              expertise = "、".join(profile.personality.expertise_areas) if profile.personality.expertise_areas else ""
              traits = "、".join(profile.metadata.get("traits", [])) if profile.metadata else ""
              parts = [
                  f"你是 {profile.name}，职责: {profile.role}。",
                  f"专长: {expertise}。" if expertise else "",
                  f"性格特质: {traits}。" if traits else "",
                  f"你的工作方式: {profile.system_prompt}" if profile.system_prompt else "",
                  f"\n你正在一个智能体广场的讨论中发言。",
                  f"请用自然的方式说话，像一个真实的专业人士在开会讨论。",
                  f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。",
                  f"不需要客套寒暄，但要说人话，不要像电报一样压缩。",
              ]
              return "".join(p for p in parts if p)
          # 回退到基础信息
          return (
              f"你是 {participant.agent_name}，职责: {participant.role}。"
              f"你正在一个智能体广场的讨论中发言。"
              f"请用自然的方式说话，像一个真实的专业人士在开会讨论。"
              f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。"
          )
  
      # ── 广场 CRUD ──────────────────────────────────────────
  
      def create_plaza(self, name: str, description: str = "") -> Plaza:
          plaza = Plaza(name=name, description=description)
          self._plazas[plaza.id] = plaza
          self._store.save_plaza(plaza)
          logger.info(f"🏛️ 广场创建: {name} ({plaza.id})")
          return plaza
  
      def get_plaza(self, plaza_id: str) -> Optional[Plaza]:
          return self._plazas.get(plaza_id)
  
      def list_plazas(self) -> List[Plaza]:
          return list(self._plazas.values())
  
      def delete_plaza(self, plaza_id: str) -> bool:
          if plaza_id in self._plazas:
              del self._plazas[plaza_id]
              self._store.delete_plaza(plaza_id)
              return True
          return False
  
      # ── 参与者管理 ──────────────────────────────────────────
  
      def add_participant(
          self, plaza_id: str, agent_id: str, agent_name: str = "",
          role: str = "", team_id: str = "",
          seat_tier: SeatTier = SeatTier.MIDDLE,
          niche_role: NicheRole = NicheRole.OBSERVER,
      ) -> Optional[Participant]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          # 分配壁龛编号 (动态扩展)
          used_niches = {p.niche_index for p in plaza.participants.values() if p.niche_index >= 0}
          niche_index = len(used_niches)
          # 自动扩展壁龛数
          if niche_index >= plaza.niche_count:
              plaza.niche_count = niche_index + 1
          p = Participant(
              agent_id=agent_id, agent_name=agent_name, role=role,
              team_id=team_id, seat_tier=seat_tier, niche_role=niche_role,
              niche_index=niche_index,
          )
          plaza.participants[agent_id] = p
          self._store.save_plaza(plaza)
          logger.info(f"🪑 参与者加入广场 {plaza_id}: {agent_name} (壁龛 #{niche_index})")
          return p
  
      def remove_participant(self, plaza_id: str, agent_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if plaza and agent_id in plaza.participants:
              del plaza.participants[agent_id]
              self._store.save_plaza(plaza)
              return True
          return False
  
      # ── 讨论管理 ──────────────────────────────────────────
  
      def create_discussion(
          self, plaza_id: str, topic: str, description: str = "",
          moderator_agent_id: str = "", max_rounds: int = 5,
      ) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          disc = Discussion(
              plaza_id=plaza_id, topic=topic, description=description,
              moderator_agent_id=moderator_agent_id, max_rounds=max_rounds,
          )
          plaza.discussions[disc.id] = disc
          self._store.save_plaza(plaza)
          logger.info(f"💬 讨论创建: {topic[:40]} ({disc.id})")
          return disc
  
      def get_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          return plaza.discussions.get(discussion_id)
  
      def list_discussions(self, plaza_id: str) -> List[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return []
          return list(plaza.discussions.values())
  
      def delete_discussion(self, plaza_id: str, discussion_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if not plaza or discussion_id not in plaza.discussions:
              return False
          del plaza.discussions[discussion_id]
          self._sse_queues.pop(discussion_id, None)
          self._store.save_plaza(plaza)
          return True
  
      def reset_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          """重置已结束讨论，保留话题本身以便重新讨论。"""
          disc = self.get_discussion(plaza_id, discussion_id)
          if not disc:
              return None
          disc.status = DiscussionStatus.OPEN
          disc.current_round = 0
          disc.messages.clear()
          disc.summary = ""
          disc.key_conclusions.clear()
          disc.plan.clear()
          disc.assigned_team_id = ""
          disc.started_at = None
          disc.ended_at = None
          plaza = self._plazas.get(plaza_id)
          if plaza:
              self._store.save_plaza(plaza)
          return disc
  
      # ── SSE 订阅管理 ──────────────────────────────────────
  
      def subscribe(self, discussion_id: str) -> asyncio.Queue:
          q: asyncio.Queue = asyncio.Queue()
          self._sse_queues.setdefault(discussion_id, []).append(q)
          return q
  
      def unsubscribe(self, discussion_id: str, q: asyncio.Queue):
          qs = self._sse_queues.get(discussion_id, [])
          if q 
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 实现 Skill 沉淀交互页面：包含半自动提炼向导（异步 LLM 预填、对比视图编辑）、待审核队列红绿灯可视化与 SSE 实时推送，用户确认后触发 SkillApproved 事件写入主表。
  步骤: pm_decompose
  📋 任务: e113f5c7-9b2
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  实现 Skill 沉淀交互页面：包含半自动提炼向导（异步 LLM 预填、对比视图编辑）、待审核队列红绿灯可视化与 SSE 实时推送，用户确认后触发 SkillApproved 事件写入主表。
  Developer, Researcher
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/frontend/agent-team-config.html`
  ### 文件: `src/backend/agents/api.py`
  **关键决策:**
    - - **Researcher**：主要负责 LLM Prompt 设计和输出格式规范（2天），协助任务 2 联调。
  - **Developer**：先完成后端核心（任务 1,3,4）约 3-5 天；前端开发（任务 5,6,7）约 3-4 天；联调与测试 1-2 天。总计约 2 周。
  **子任务拆解:**
    - *任务名称**：Skill 沉淀交互页面  
    - *负责角色**：Developer, Researcher  
    - *目标**：提供一个技能沉淀的完整交互界面，支持从对话/文档中半自动提炼技能，经过审核队列的红绿灯可视化与实时推送，最终确认写入技能主表并触发 `SkillApproved` 事件。
    - 技能定义模型 `SkillDefinition`（`src/backend/agents/models.py`）
    - 技能注册中心 `SkillRegistry`（`src/backend/agents/skill_registry.py`，`src/backend/agents/api.py` 中通过 `_skill_registry` 使用）
    - 前端技能展示页（`src/frontend/agent-team-config.html` 中的 `view-skills`）
    - 异步 LLM 调用基础（`ChatHarness`，SSE 推送模式见于 `plaza_engine.py`）
    - 技能审批与事件写入机制
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 实现 Skill 沉淀交互页面：包含半自动提炼向导（异步 LLM 预填、对比视图编辑）、待审核队列红绿灯可视化与 SSE 实时推送，用户确认后触发 SkillApproved 事件写入主表。
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: e113f5c7-9b2
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
    实现 Skill 沉淀交互页面：包含半自动提炼向导（异步 LLM 预填、对比视图编辑）、待审核队列红绿灯可视化与 SSE 实时推送，用户确认后触发 SkillApproved 事件写入主表。
    Developer, Researcher
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
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
    src/backend/tests/__init__.py
    src/backend/tests/conftest.py
    src/backend/tests/conftest.py.bak
    src/backend/tests/test_ab_testing.py
    src/backend/tests/test_agent_toolbox.py
    src/backend/tests/test_models.py
    src/backend/tests/test_models.py.bak
    src/backend/tests/test_task_engine.py
    src/backend/tests/test_task_engine.py.bak
    src/backend/tests/test_team_manager.py
    src/backend/tests/test_team_manager.py.bak
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
    src/backend/channels/evolution_executor.py
    src/backend/channels/marine_base.py
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
    src/docs/agent_handoffs/11e9b4b9-283_executor_started_20260509T074916.md
    src/docs/agent_handoffs/11e9b4b9-283_pm_decompose_20260509T075116.md
    src/docs/agent_handoffs/1356f045-d02_executor_started_20260509T073232.md
    src/docs/agent_handoffs/15554439-6aa_executor_started_20260509T073231.md
    src/docs/agent_handoffs/15a7e2eb-cd1_executor_started_20260509T073232.md
    src/docs/agent_handoffs/18d4b20f-c33_executor_started_20260509T073231.md
    src/docs/agent_handoffs/1aed56ed-eda_executor_started_20260509T073232.md
    src/docs/agent_handoffs/1cc2c0fb-90b_executor_started_20260509T073232.md
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
    src/docs/agent_handoffs/1d2d7607-8a3_executor_started_20260509T073231.md
    src/docs/agent_handoffs/1e04fc38-6e9_executor_started_20260509T073231.md
    src/docs/agent_handoffs/1f835c25-c0f_executor_started_20260509T073232.md
    src/docs/agent_handoffs/1fd87e2e-962_executor_started_20260509T073232.md
    src/docs/agent_handoffs/21750a9a-2ff_executor_started_20260509T073231.md
    src/docs/agent_handoffs/21ef94ba-2b6_executor_started_20260509T074916.md
    src/docs/agent_handoffs/21ef94ba-2b6_pm_decompose_20260509T075106.md
    src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
    src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
    src/docs/agent_handoffs/2da416d2-cdf_executor_started_20260509T074916.md
    src/docs/agent_handoffs/2da416d2-cdf_pm_decompose_20260509T075121.md
    src/docs/agent_handoffs/32a3b057-166_executor_started_20260509T073232.md
    src/docs/agent_handoffs/34efc37e-3a1_executor_started_20260509T073231.md
    src/docs/agent_handoffs/35b91517-bfb_executor_started_20260509T073231.md
    src/docs/agent_handoffs/35f5eb68-2b7_executor_started_20260509T073232.md
    src/docs/agent_handoffs/38c98cf4-15b_executor_started_20260509T073231.md
    src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
    src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
    src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
    src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
    src/docs/agent_handoffs/39c0911d-173_executor_started_20260509T073232.md
    src/docs/agent_handoffs/3bde709e-2fe_architecture_20260507T031839.md
    src/docs/agent_handoffs/3bde709e-2fe_deploy_FAILED_20260507T033021.md
    src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T031910.md
    src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032452.md
    src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032630.md
    src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
    src/docs/agent_handoffs/3bde709e-2fe_pm_decompose_20260507T031529.md
    src/docs/agent_handoffs/3bde709e-2fe_research_20260507T031614.md
    src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T031936.md
    src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032523.md
    src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032706.md
    src/docs/agent_handoffs/3f9494e1-96d_executor_started_20260509T074916.md
    src/docs/agent_handoffs/3f9494e1-96d_pm_decompose_20260509T075056.md
    src/docs/agent_handoffs/3f9494e1-96d_research_20260509T075256.md
    src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
    src/docs/agent_handoffs/4601c322-51d_executor_started_20260509T075153.md
    src/docs/agent_handoffs/4601c322-51d_pipeline_complete_20260509T075233.md
    ... (共 529 个 src/ 文件)
    
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
              <div class="form-group"><label class="form-label">提供商</label><select class="fi" id="llm-provider" onchange="syncLLMModelTierAvailability();syncLLMModelTierFromInput()"><option value="deepseek">DeepSeek</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="local">本地 (Ollama/vLLM)</option><option value="openrouter">OpenRouter</option><option value="github">GitHub Models</option><option value="qwen">通义千问</option></select></div>
              <div class="form-group"><label class="form-label">模型</label><input class="fi" id="llm-model" placeholder="deepseek-v4-flash" oninput="syncLLMModelTierFromInput()"></div>
              <div class="form-group" id="llm-model-tier-wrap">
                <label class="form-label">DeepSeek 档位</label>
                <div style="display:inline-flex;align-items:center;gap:0;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:rgba(0,0,0,0.08)">
                  <input type="checkbox" id="llm-model-tier" onchange="onLLMModelTierToggle(this.checked)" style="display:none">
                  <button type="button" id="llm-tier-flash" onclick="setLLMModelTier(false)" style="padding:6px 14px;border:none;background:transparent;color:var(--dim);font-size:12px;cursor:pointer;min-width:72px">Flash</button>
                  <button type="button" id="llm-tier-pro" onclick="setLLMModelTier(true)" style="padding:6px 14px;border:none;background:transparent;color:var(--dim);font-size:12px;cursor:pointer;min-width:72px;border-left:1px solid var(--line)">Pro</button>
                </div>
                <div style="font-size:11px;color:var(--dim);margin-top:6px">点击按钮切换：Flash 或 Pro</div>
              </div>
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
          <div style="display:flex;justify-content:space-between;align-items:c
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
        for m in team.models.values():
            if m.is_default:
                default_model = m
                break
        if default_model is None:
            return
        harness.update_default_provider(
            provider=default_model.provider,
            api_key=default_model.api_key,
            api_base_url=default_model.api_base_url,
            model=default_model.name,
        )
        cfg = harness.get_provider_config()
        cfg.max_tokens = default_model.max_tokens
        cfg.temperature = default_model.temperature
    
    
    @router.delete(
        "/teams/{team_id}/models/{model_id}",
        summary="Remove model from team",
    )
    def remove_model(team_id: str, model_id: str) -> Dict[str, str]:
        removed = _tm().remove_model_from_team(team_id, model_id)
        if removed is None:
  
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

# 🏗️ 技术方案：Skill 沉淀交互页面

**角色：系统架构师 (architect)**  
**关联任务：** e113f5c7-9b2  
**依赖前序产出：** PM分解、研究分析  

---

## 一、总体架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (agent-team-config)              │
│  ┌──────────────────────┐  ┌─────────────────────────┐ │
│  │ 提炼输入 + 进度展示  │  │ 待审核队列 (红绿灯表格) │ │
│  └──────┬───────────────┘  └────────────┬────────────┘ │
│         │   POST /start                 │  SSE stream    │
└─────────┼───────────────────────────────┼────────────────┘
          │                               │
┌─────────▼───────────────────────────────▼────────────────┐
│                    后端 FastAPI                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SkillRefineRouter  (新增)                       │   │
│  │  ├─ POST /api/v1/skill-refine/start    → 后台任务│   │
│  │  ├─ GET  /api/v1/skill-refine/drafts   → 草稿列表│   │
│  │  ├─ GET  /api/v1/skill-refine/drafts/{id}→ 详情  │   │
│  │  ├─ PUT  /api/v1/skill-refine/drafts/{id}→ 更新  │   │
│  │  ├─ POST /api/v1/skill-refine/drafts/{id}/approve│   │
│  │  ├─ POST /api/v1/skill-refine/drafts/{id}/reject │   │
│  │  └─ GET  /api/v1/skill-refine/stream   → SSE推送 │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │ SkillDraftStore       │  │ SkillRegistry (已存在)   │ │
│  │ (内存+持久化JSON)     │  │ + SkillApproved 事件    │ │
│  └──────────────────────┘  └──────────────────────────┘ │
│  ┌──────────────────────┐                               │
│  │ ChatHarness (LLM调用) │                               │
│  └──────────────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

**核心流程：**
1. 用户输入源文本 → 触发异步LLM生成预填草稿 (`POST /start`)
2. 后台任务调用 LLM 生成 `SkillDraft`，并通过 SSE 推送状态变化
3. 前端在队列视图中展示草稿的红绿灯（完整性、置信度等）
4. 用户可进入“对比视图”编辑草稿，保存更新
5. 用户点击“批准” → 调用 `POST .../approve`，草稿转为 `SkillDefinition` 写入主表，触发 `SkillApproved` 事件，SSE 推送

---

## 二、数据模型设计

### 1. 新增 `SkillDraft` 及状态枚举

**文件：** `src/backend/agents/models.py`

```python
class DraftStatus(Enum):
    GENERATING = "generating"       # LLM 预填中
    DRAFT = "draft"                 # 待审核
    APPROVED = "approved"          # 已批准转为技能
    REJECTED = "rejected"          # 已驳回


@dataclass
class SkillDraft:
    draft_id: str = ""
    team_id: str = ""
    source_text: str = ""          # 原始输入文本
    # 预填 / 编辑字段
    name: str = ""
    description: str = ""
    category: str = ""             # 对应 SkillCategory.value
    instructions: str = ""
    required_tools: list = field(default_factory=list)
    icon: str = "⚡"
    
    # 元数据
    status: DraftStatus = DraftStatus.GENERATING
    llm_confidence: float = 0.0    # 0~1
    traffic_light: str = "yellow"  # green / yellow / red
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.draft_id:
            self.draft_id = str(uuid.uuid4())[:8]
        if not self.updated_at:
            self.updated_at = self.created_at
```

### 2. 红绿灯判定逻辑

| 条件 | 颜色 |
|------|------|
| `llm_confidence >= 0.7` 且 `name` 非空 且 `description` 非空 且 `instructions` 非空 | 🟢 green |
| `llm_confidence < 0.4` 或关键字段缺失 (`name` 或 `description` 为空) | 🔴 red |
| 其他情况 | 🟡 yellow |

该逻辑在后台任务生成草稿时自动计算，并在每次 `PUT` 更新时重新评估。

---

## 三、后端实现

### 1. 新增 `SkillDraftStore`

**新建文件：** `src/backend/agents/skill_draft_store.py`

```python
from typing import Dict, List, Optional
import json, os
from .models import SkillDraft, DraftStatus

class SkillDraftStore:
    def __init__(self, persist_path: str = "data/skill_drafts.json"):
        self._drafts: Dict[str, SkillDraft] = {}
        self._path = persist_path
        self._load()

    def _load(self): ...
    def _save(self): ...

    def add(self, draft: SkillDraft) -> SkillDraft: ...
    def get(self, draft_id: str) -> Optional[SkillDraft]: ...
    def list_drafts(self, team_id: str = "", status: str = "") -> List[SkillDraft]: ...
    def update(self, draft: SkillDraft) -> SkillDraft: ...
    def delete(self, draft_id: str) -> bool: ...
```

- 使用内存字典 + JSON 文件持久化（与现有 `PlazaStore` 风格一致）
- 启动时从文件加载，每次变更保存

### 2. SSE 广播管理器

**新建文件：** `src/backend/agents/skill_refine_sse.py`

```python
import asyncio
from typing import Dict, List

class SkillRefineSSE:
    def __init__(self):
        self._queues: Dict[str, List[asyncio.Queue]] = {}  # team_id -> list of queues

    def subscribe(self, team_id: str) -> asyncio.Queue: ...
    def unsubscribe(self, team_id: str, queue: asyncio.Queue): ...
    async def broadcast(self, team_id: str, event: dict): ...
```

**事件格式：**
```json
{
  "event": "draft_updated" | "draft_created" | "draft_approved" | "draft_rejected",
  "data": { ... draft_summary ... }
}
```

### 3. 添加 REST API 路由

**新建文件：** `src/backend/agents/skill_refine_routes.py`  
**或在 `api.py` 中追加**（建议新建独立文件以保持清晰）。

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from .chat_harness import get_chat_harness
from .skill_draft_store import SkillDraftStore
from .skill_refine_sse import SkillRefineSSE
from .models import SkillDraft, DraftStatus
from .skill_registry import SkillDefinition
```

**新增端点：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/skill-refine/start` | 启动异步提炼 |
| `GET` | `/api/v1/skill-refine/drafts` | 获取草稿列表（支持 `?team_id=&status=`） |
| `GET` | `/api/v1/skill-refine/drafts/{draft_id}` | 获取草稿详情 |
| `PUT` | `/api/v1/skill-refine/drafts/{draft_id}` | 更新草稿（用户编辑） |
| `POST` | `/api/v1/skill-refine/drafts/{draft_id}/approve` | 批准草稿 |
| `POST` | `/api/v1/skill-refine/drafts/{draft_id}/reject` | 驳回草稿 |
| `GET` | `/api/v1/skill-refine/stream` | SSE 流（`?team_id=`） |

**关键实现细节：**

- **`POST /start`**  
  接收 `{source_text, team_id}`，创建 `SkillDraft(status=GENERATING)`，放入 `BackgroundTasks` 调用 `_generate_skill_draft(draft_id)`。立即返回 `{draft_id}`。

- **后台任务 `_generate_skill_draft`**  
  1. 用 ChatHarness 调用 LLM，Prompt 要求提取技能名、描述、指令、分类、所需工具等，返回 JSON。
  2. 解析 JSON，填充 `SkillDraft` 字段，计算 `traffic_light`。
  3. 将状态改为 `DRAFT`，保存 store。
  4. 通过 SSE 广播 `draft_created` 事件。

- **`POST .../approve`**  
  1. 验证草稿状态为 `DRAFT`。
  2. 创建 `SkillDefinition` 对象。
  3. 调用 `SkillRegistry.add_skill(skill)` 写入主表（若 team 级别需要，则通过 `_tm().get_team(team_id).add_skill(...)`）。
  4. 更新草稿状态为 `APPROVED`，保存 store。
  5. **触发 `SkillApproved` 事件**：记录日志，广播 `draft_approved` SSE 事件（可选：调用事件总线，当前可先实现简单日志 + SSE）。
  6. 返回成功，包含新技能的 `skill_id`。

- **SSE 端点**  
  使用 `sse-starlette. EventSourceResponse` 配合 `SkillRefineSSE.subscribe(team_id)`，持续推送事件。

### 4. 注册路由

**修改文件：** `src/backend/main.py`

在现有的 `app.include_router(plaza_routes.router)` 附近添加：
```python
from .agents.skill_refine_routes import router as skill_refine_router
app.include_router(skill_refine_router)
```

初始化时对 `SkillDraftStore` 和 `SkillRefineSSE` 进行实例化，可能通过依赖注入或全局变量（参考 `_team_manager` 方式）。

---

## 四、前端实现

### 1. 新增侧边栏导航

**修改文件：** `src/frontend/agent-team-config.html`

在 `.sb-nav` 中增加一项（可放在“技能”之后）：
```html
<a data-view="skill-refine" onclick="switchView('skill-refine')">
  <span class="seal">炼</span> 技能沉淀
</a>
```

### 2. 新视图 `view-skill-refine`

在同一 HTML 文件中添加新的 `<div id="view-skill-refine" class="main-inner hidden">`，结构如下：

```html
<div id="view-skill-refine" class="main-inner hidden">
  <div class="main-scroll">
    <!-- 提炼输入区 -->
    <div class="card" style="padding:20px;margin-bottom:20px">
      <div class="section-title" style="margin-top:0;margin-bottom:12px">📝 半自动提炼向导</div>
      <textarea id="sr-source-text" class="fi" rows="4" placeholder="粘贴对话或文档片段，让 AI 提取技能..."></textarea>
      <button class="btn btn-pink btn-sm" onclick="startSkillRefine()" id="sr-start-btn">🚀 开始提炼</button>
      <span id="sr-progress" style="margin-left:12px;font-size:12px;color:var(--dim)"></span>
    </div>
    
    <!-- 红绿灯队列 -->
    <div class="section-title" style="margin-top:0;margin-bottom:12px">🚥 待审核队列
      <span id="sr-queue-count" style="font-size:12px;color:var(--dim)"></span>
    </div>
    <table class="tbl" id="sr-queue-table">
      <thead><tr>
        <th>草稿名称</th><th>状态</th><th>信号</th><th>置信度</th><th>创建时间</th><th>操作</th>
      </tr></thead>
      <tbody id="sr-queue-tb"></tbody>
    </table>
    
    <!-- 对比视图模态框 (默认隐藏) -->
    <div id="sr-compare-modal" class="modal hidden">
      <div class="modal-backdrop" onclick="closeCompareModal()"></div>
      <div class="modal-content" style="max-width:900px">
        <div class="modal-header">
          <h3>对比编辑</h3>
          <button onclick="closeCompareModal()">✕</button>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
          <div>
            <h4>🤖 LLM 预填</h4>
            <div id="sr-compare-llm" style="background:var(--card-bg);padding:12px;border-radius:8px"></div>
          </div>
          <div>
            <h4>✏️ 用户编辑</h4>
            <div class="form-group"><label>名称</label><input class="fi" id="sr-edit-name"></div>
            <div class="form-group"><label>描述</label><textarea class="fi" id="sr-edit-desc" rows="3"></textarea></div>
            <div class="form-group"><label>分类</label><select class="fi" id="sr-edit-category"></select></div>
            <div class="form-group"><label>指令</label><textarea class="fi" id="sr-edit-instructions" rows="3"></textarea></div>
            <div class="form-group"><label>所需工具 ID (逗号分隔)</label><input class="fi" id="sr-edit-tools"></div>
            <button class="btn btn-pink btn-sm" onclick="saveDraftEdit()">💾 保存修改</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 3. 前端 JavaScript 逻辑

**修改文件：** `src/frontend/js/agent-team-config.js`

新增以下函数（使用现有 `apiGet`, `apiPost`, `apiPut` 等工具函数）：

- `switchView('skill-refine')` 初始化时连接 SSE，加载队列。
- `startSkillRefine()`：获取 `#sr-source-text`，调用 `POST /api/v1/skill-refine/start`，显示进度。
- `connectSkillRefineSSE(teamId)`：建立 `EventSource` 连接 `/api/v1/skill-refine/stream?team_id=xxx`，监听事件更新队列。
- `loadDraftQueue()`：`GET /api/v1/skill-refine/drafts`，渲染表格。
- `renderDraftRow(draft)`：生成表格行，包含操作按钮（📝编辑, ✅批准, ❌驳回）。
- `openCompareModal(draftId)`：`GET details`，填充左侧 LLM 内容（只读），右侧表单回填草稿字段。
- `saveDraftEdit()`：`PUT /api/v1/skill-refine/drafts/{id}`，然后关闭模态框。
- `approveDraft(draftId)`：确认后调用 `POST .../approve`，成功后提示并刷新列表。
- `rejectDraft(draftId)`：调用 `POST .../reject`。

**红绿灯可视化：** 在 `renderDraftRow` 中根据 `traffic_light` 渲染不同颜色的圆点：
```javascript
const light = draft.traffic_light;
const dot = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${light==='green'?'var(--lime)':light==='red'?'var(--pink)':'var(--amber)'}"></span>`;
```

### 4. 新增或调整 CSS（可选）

如需弹窗样式，在 `agent-team-config.css` 中添加 `.modal` 相关规则（若已存在则复用）。

---

## 五、LLM 预填 Prompt 设计

由 Researcher 协作提供，核心要求：

**System Prompt:**
```
你是一个技能提炼专家。根据给定的文本，提取其中描述的技能，输出严格的 JSON 格式，不要包含任何额外说明。

输出格式：
{
  "name": "技能名称（简练）",
  "description": "一句话描述技能的功能",
  "category": "general | digital_twin | automation | research | domain_knowledge",
  "instructions": "详细的使用指令（如何激活该技能的行为）",
  "required_tools": ["tool_id1", "tool_id2"],
  "confidence": 0.85
}
```

后台任务解析 JSON 时需做容错处理（如截取代码块、修复格式）。

---

## 六、SkillApproved 事件规范

当前事件可简化为：
- **日志记录**：在 `skill_refine_routes.py` 中 `approve` 函数内执行 `logger.info(f"SkillApproved: {skill.skill_id} {skill.name}")`。
- **SSE 广播**：推送 `draft_approved` 事件给所属团队的所有订阅者。
- 若未来需要扩展事件总线（如通知 Agent 重新加载技能），可在 `SkillRegistry` 内部增加回调注册，当前不强制实现。

---

## 七、逐步实施指南

| 阶段 | 任务 | 负责角色 | 预计工时 |
|------|------|----------|----------|
| **1. 后端数据与存储** | 1. 在 `models.py` 中添加 `DraftStatus`, `SkillDraft`。<br>2. 创建 `skill_draft_store.py`（内存+JSON持久化）。<br>3. 编写单元测试验证存储功能。 | Developer | 0.5天 |
| **2. SSE 广播基础** | 1. 创建 `skill_refine_sse.py`。<br>2. 实现 subscribe / unsubscribe / broadcast。<br>3. 集成到 `main.py` 初始化。 | Developer | 0.5天 |
| **3. REST API 实现** | 1. 创建 `skill_refine_routes.py`，实现上述 7 个端点。<br>2. 后台任务调用 ChatHarness，LLM Prompt 由 Researcher 提供。<br>3. 在 `main.py` 注册路由。<br>4. 编写接口测试。 | Developer + Researcher | 2天 |
| **4. 前端视图与基础交互** | 1. 在 `agent-team-config.html` 中添加导航和 `view-skill-refine` 结构。<br>2. 实现 JS 函数：开始提炼、队列加载、红绿灯渲染。 | Developer | 1天 |
| **5. 对比视图与编辑** | 1. 实现模态框对比编辑。<br>2. 保存草稿更新。<br>3. 批准/驳回操作。 | Developer | 1天 |
| **6. SSE 前端集成** | 1. 在 `switchView('skill-refine')` 中连接 SSE 流。<br>2. 根据事件动态更新队列，实现实时刷新。 | Developer | 0.5天 |
| **7. 联调与测试** | 1. 端到端流程测试：输入文本 → LLM生成 → 队列更新 → 编辑 → 批准 → 写入技能表。<br>2. 异常处理（LLM调用失败、空文本等）。<br>3. 红绿灯逻辑验证。 | Developer + Researcher | 1天 |

总计约 6.5 天，与 PM 估算一致（Developer + Researcher 协同）。

---

## 八、关键注意事项

1. **安全性**：提炼 API 需要验证 `team_id` 属于当前用户（可复用 `_get_team_or_404`），但前端目前无登录状态检查，后续需补全。
2. **并发与锁**：`SkillDraftStore` 为单线程内存操作，FastAPI async 下需考虑加 `asyncio.Lock` 保护写操作（尤其 JSON 文件保存）。
3. **LLM 容错**：JSON 解析失败应回退为 `DRAFT` 状态但内容留空，将 `traffic_light` 置为 `red`，并附带错误信息供用户手动编辑。
4. **扩展性**：`SkillApproved` 事件可预留钩子，例如调用 `SkillRegistry.on_skill_approved(skill)` 允许其他模块监听。

设计完成，可交由开发工程师按指南实施。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
