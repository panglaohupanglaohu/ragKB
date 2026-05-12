# PM分解 — project_manager

任务: 实现 SDK 配置管理核心模块：原子文件写入（临时文件+rename）、内存缓存、预编译决策树、health endpoint 暴露版本/来源状态/刷新时间戳、last known good config 回退
步骤: pm_decompose
Agent: build_pm

---

📋 任务: 8a5071c5-834
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
  实现 SDK 配置管理核心模块：原子文件写入（临时文件+rename）、内存缓存、预编译决策树、health endpoint 暴露版本/来源状态/刷新时间戳、last known good config 回退
  Developer
  
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
  src/docs/agent_handoffs/ba472f30-1a6_executor_started_20260507T003435.md
  src/docs/agent_handoffs/d553cde7-ee1_executor_started_20260506T101306.md
  src/docs/agent_handoffs/d87c964b-c06_architecture_20260503T045321.md
  src/docs/agent_handoffs/d87c964b-c06_pm_decompose_20260503T045236.md
  src/docs/agent_handoffs/d87c964b-c06_research_20260503T045251.md
  src/docs/agent_handoffs/d87c964b-c06_task_init_20260503T045211.md
  src/docs/agent_handoffs/dbf24d0c-5cc_architecture_20260503T235205.md
  src/docs/agent_handoffs/dbf24d0c-5cc_deploy_FAILED_20260504T012356.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_20260503T235646.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_20260504T004702.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_FAILED_20260504T001109.md
  src/docs/agent_handoffs/dbf24d0c-5cc_executor_started_20260503T234950.md
  src/docs/agent_handoffs/dbf24d0c-5cc_pm_decompose_20260503T235020.md
  src/docs/agent_handoffs/dbf24d0c-5cc_research_20260503T235105.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T000157.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T002112.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T012326.md
  src/docs/agent_handoffs/dd0e3569-eb0_architecture_20260503T114837.md
  src/docs/agent_handoffs/dd0e3569-eb0_deploy_FAILED_20260503T121257.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_20260503T115309.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_FAILED_20260503T120023.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_FAILED_20260503T120906.md
  src/docs/agent_handoffs/dd0e3569-eb0_executor_started_20260503T114547.md
  src/docs/agent_handoffs/dd0e3569-eb0_pm_decompose_20260503T114622.md
  src/docs/agent_handoffs/dd0e3569-eb0_research_20260503T114712.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_20260503T115557.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_FAILED_20260503T120434.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_FAILED_20260503T121242.md
  src/docs/workflow_artifacts/1ce78c0e-062_architecture.md
  src/docs/workflow_artifacts/1ce78c0e-062_deploy.md
  src/docs/workflow_artifacts/1ce78c0e-062_develop.md
  src/docs/workflow_artifacts/1ce78c0e-062_pm_decompose.md
  src/docs/workflow_artifacts/1ce78c0e-062_research.md
  src/docs/workflow_artifacts/1ce78c0e-062_test.md
  src/docs/workflow_artifacts/38e22004-b64_architecture.md
  src/docs/workflow_artifacts/38e22004-b64_pm_decompose.md
  src/docs/workflow_artifacts/38e22004-b64_research.md
  src/docs/workflow_artifacts/7c934759-39e_architecture.md
  src/docs/workflow_artifacts/7c934759-39e_deploy.md
  src/docs/workflow_artifacts/7c934759-39e_develop.md
  src/docs/workflow_artifacts/7c934759-39e_pm_decompose.md
  src/docs/workflow_artifacts/7c934759-39e_research.md
  src/docs/workflow_artifacts/7c934759-39e_test.md
  src/docs/workflow_artifacts/ba3b66b1-a77_architecture.md
  ... (共 170 个 src/ 文件)
  
  ```
  
  ### 文件: `src/frontend/js/agent-team-config.js`
  ```js
  const A='/api/v1/agent-config',AT='/api/v1/agent-teams';
  let tid='',aid='',atab='ag-status',wzD={},wzS=1;
  let _offline=false;
  
  function toast(m,type){
    const e=document.getElementById('toast');
    e.className='toast'+(type?' toast-'+type:'');
    e.textContent=m;e.classList.add('show');
    const dur=type==='error'?5000:2500;
    setTimeout(()=>e.classList.remove('show'),dur);
  }
  function openModal(id){
    const m=document.getElementById(id);m.classList.add('open');
    m.setAttribute('role','dialog');m.setAttribute('aria-modal','true');
    // Focus trap
    const focusable=m.querySelectorAll('button,input,select,textarea,[tabindex]:not([tabindex="-1"])');
    if(focusable.length)focusable[0].focus();
    m._focusTrap=e=>{
      if(e.key==='Escape'){closeModal(id);return}
      if(e.key!=='Tab')return;
      const first=focusable[0],last=focusable[focusable.length-1];
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
    };
    m.addEventListener('keydown',m._focusTrap);
  }
  function closeModal(id){
    const m=document.getElementById(id);m.classList.remove('open');
    m.removeAttribute('aria-modal');
    if(m._focusTrap){m.removeEventListener('keydown',m._focusTrap);delete m._focusTrap}
  }
  
  // Connection status banner
  function showOfflineBanner(){
    if(document.getElementById('offline-banner'))return;
    const b=document.createElement('div');
    b.id='offline-banner';
    b.style.cssText='position:fixed;top:0;left:0;right:0;z-index:1000;background:var(--shu);color:var(--shironeri);padding:8px 16px;font-size:13px;text-align:center;display:flex;justify-content:center;align-items:center;gap:12px';
    b.innerHTML='⚠ 后端连接失败 <button style="background:var(--shironeri);color:var(--shu);border:none;padding:4px 12px;cursor:pointer;font-size:12px;font-weight:600" onclick="retryConnection()">重试</button>';
    document.body.prepend(b);
  }
  function hideOfflineBanner(){
    const b=document.getElementById('offline-banner');if(b)b.remove();
    _offline=false;
  }
  async function retryConnection(){
    const r=await fetch(`${A}/teams`).catch(()=>null);
    if(r&&r.ok){hideOfflineBanner();loadTeams();toast('连接已恢复','success')}
    else toast('仍然无法连接','error')
  }
  
  async function api(p,o){
    try{
      const r=await fetch(p,o);
      if(_offline){hideOfflineBanner()}
      if(!r.ok){
        let msg='';
        try{const d=await r.json();msg=d.detail||d.message||''}catch{}
        console.warn(`API ${r.status}: ${p}`,msg);
        // Attach error info for callers that want it
        const result=null;
        api._lastError={status:r.status,message:msg,url:p};
        return result;
      }
      api._lastError=null;
      return await r.json();
    }catch(e){
      console.error(`API error: ${p}`,e);
      // Network error — show offline banner
      if(e.name==='TypeError'||e.message?.includes('fetch')){
        _offline=true;
        showOfflineBanner();
      }
      api._lastError={status:0,message:e.message,url:p,network:true};
      return null;
    }
  }
  api._lastError=null;
  
  function stL(s){return{idle:'待命中',working:'工作中',reporting:'汇报中',blocked:'阻塞',error:'异常'}[s]||s||'未知'}
  function el(id){return document.getElementById(id)}
  function escapeHtml(v){return String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
  
  // ── Teams ──
  async function loadTeams(){
    const d=await api(`${A}/teams`);const s=el('team-select');
    if(!d||!d.length){s.innerHTML='<option>无团队</option>';return}
    s.innerHTML=d.map(t=>`<option value="${escapeHtml(t.team_id)}">${escapeHtml(t.name)}</option>`).join('');
    if(!tid)tid=d[0].team_id;s.value=tid;loadView();
  }
  el('team-select').onchange=e=>{tid=e.target.value;loadView()};
  
  // ── View switch ──
  function switchView(v,extra){
    document.querySelectorAll('.main-inner').forEach(e=>e.classList.add('hidden'));
    document.querySelectorAll('.sb-nav a').forEach(a=>a.classList.toggle('active',a.dataset.view===v));
    document.querySelectorAll('.sb-agent').forEach(a=>a.classList.remove('active'));
    const t=el('main-title'),b=el('main-badge');
    if(v==='overview'){el('view-overview').classList.remove('hidden');t.textContent='团队概览';b.textContent=tid;loadOverview()}
    else if(v==='models'){el('view-models').classList.remove('hidden');t.textContent='模型池';b.textContent='';loadModels()}
    else if(v==='tools'){el('view-tools').classList.remove('hidden');t.textContent='工具管理';b.textContent='';loadTools()}
    else if(v==='skills'){el('view-skills').classList.remove('hidden');t.textContent='技能管理';b.textContent='';loadSkills()}
    else if(v==='tasks'){el('view-tasks').classList.remove('hidden');t.textContent='并发任务';b.textContent='';loadTasks()}
    else if(v==='llm'){
      el('view-llm').classList.remove('hidden');
      t.textContent='LLM 配置';
      b.textContent='';
      // Avoid a transient UI mismatch before async status response arrives.
      syncLLMModelTierFromInput();
      syncLLMModelTierAvailability();
      loadLLMStatus();
      loadTTSConfig();
    }
    else if(v==='sessions'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-sessions').classList.remove('hidden');t.textContent='会话存档';b.textContent='';loadPersistedSessions()}
    else if(v==='runtime'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-runtime').classList.remove('hidden');t.textContent='PortRuntime';b.textContent='claw-code-parity';el('rt-results').classList.add('hidden')}
    else if(v==='registry'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-registry').classList.remove('hidden');t.textContent='自主 Token 工厂';b.textContent='Token Factory';loadTokenFactory();_startTfPoll()}
    else if(v==='agent'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='';el('agent-content').style.display='';loadAgent(extra)}
    else if(v==='wizard'){el('view-wizard').classList.remove('hidden');t.textContent='新建智能体';b.textContent=''}
  }
  function loadView(){loadSbAgents();
    // ── Darwin rule: bridge-task-dispatch deep-link support ──
    const params = new URLSearchParams(window.location.search);
    const view = params.get('view');
    switchView(view && document.querySelector(`[data-view="${view}"]`) ? view : 'overview');
  }
  
  // ── Sidebar agents ──
  async function loadSbAgents(){
    const d=await api(`${A}/teams/${tid}`);const c=el('sb-agents');
    if(!d||!d.agents){c.innerHTML='<div style="padding:12px;color:var(--dim);font-size:12px">暂无成员</div>';return}
    const aa=Array.isArray(d.agents)?d.agents:Object.values(d.agents);
    c.innerHTML=aa.map(a=>`<div class="sb-agent${a.agent_id===aid?' active':''}" onclick="selectAgent('${a.agent_id}')"><span class="dot ${a.state||'idle'}"></span><span style="overflow:hidden;text-overflow:ellipsis">${escapeHtml(a.name||a.agent_id)}</span></div>`).join('');
  }
  function selectAgent(id){aid=id;switchView('agent',id)}
  
  // ── Overview ──
  let _ovTimer=null;
  async function loadOverview(){
    if(_ovTimer)clearInterval(_ovTimer);
    const teamsList=await api(`${A}/teams`);
    const teamIds=(teamsList||[]).map(t=>t.team_id);
    const[ov,dash,...allTeams]=await Promise.all([
      api(`${AT}/overview`),
      api(`${A}/teams/${tid}/dashboard`),
      ...teamIds.map(id=>api(`${A}/teams/${id}`))
    ]);
    const sc=el('ov-stats');
    const _teamIcons={'build_system':'🏗️','energy_first_principle':'⚡','ai_coding':'💻'};
    if(ov){const sh=ov.scheduler||{};const dt=dash||{};const ev=ov.evolution||{};const evs=ev.stats||{};
    const totalModels=allTeams.reduce((n,t)=>n+(t&&t.models?Object.keys(t.models).length:0),0);
    const totalAgents=allTeams.reduce((n,t)=>n+(t&&t.agents?(Array.isArray(t.agents)?t.agents.length:Object.keys(t.agents).length):0),0);
    const teamCards=allTeams.filter(Boolean).map(t=>{const ac=t.agents?(Array.isArray(t.agents)?t.agents.length:Object.keys(t.agents).length):0;const ic=_teamIcons[t.team_id]||'🤖';return`<div class="stat-card" style="cursor:pointer" onclick="el('team-select').value='${t.team_id}';tid='${t.team_id}';loadView()"><div class="label">${ic} ${escapeHtml(t.name||t.team_id)}</div><div class="value">${ac}</div><div class="sub">${escapeHtml(t.description||'').slice(0,30)}</div></div>`}).join('');
    sc.innerHTML=`<div class="stat-card"><div class="label">📊 调度器</div><div class="value" style="font-size:16px;color:${sh.running?'var(--lime)':'var(--red)'}">${sh.running?'运行中':'已停止'}</div><div class="sub">Tick ${sh.tick_count??0} · 运行 ${Math.round((sh.uptime_seconds||0)/60)}m</div></div>${teamCards}<div class="stat-card"><div class="label">🔄 自我演进</div><div class="value">${ev?.evolution_items_count??'-'}</div><div class="sub">规则 ${ev?.audit_rules_count??0} · 已验证 ${evs?.total_verified??0}</div></div><div class="stat-card"><div class="label">📦 模型</div><div class="value">${totalModels}</div></div><div class="stat-card"><div class="label">🤖 智能体</div><div class="value">${totalAgents}</div></div><div class="stat-card"><div class="label">📋 任务</div><div class="value">${dt.tasks?.total||0}</div><div class="sub">${Object.entries(dt.tasks?.by_status||{}).map(([k,v])=>`${k}: ${v}`).join(' · ')||'无任务'}</div></div>`}
    const curTm=allTeams.find(t=>t&&t.team_id===tid);
    const teamTitle=curTm?curTm.name:tid;
    const teamIcon=_teamIcons[tid]||'🤖';
    el('ov-team-title').textContent=`${teamIcon} ${teamTitle}`;
    const tbody=el('ov-team-agents');tbody.innerHTML='';
    if(curTm&&curTm.agents){
      const aa=Array.isArray(curTm.agents)?curTm.agents:Object.values(curTm.agents);
      aa.forEach(a=>{tbody.innerHTML+=`<tr><td><b>${escapeHtml(a.name||a.agent_id)}</b></td><td style="color:var(--muted)">${escapeHtml(a.role||'-')}</td><td><span class="st st-${a.state||'idle'}">${stL(a.state)}</span></td><td>${(a.skills||[]).slice(0,3).map(s=>'<span class="chip">'+s+'</span>').join('')}</td><td><button class="btn btn-sm btn-ghost" onclick="selectAgent('${a.agent_id}')">查看</button></td></tr>`});
    }
    if(!tbody.innerHTML)tbody.innerHTML='<tr><td colspan="5" style="color:var(--dim)">暂无</td></tr>';
    _ovTimer=setInterval(()=>{if(document.querySelector('#view-overview:not(.hidden)'))loadOverview();else clearInterval(_ovTimer)},10000);
    loadEvolution();
  }
  
  // ── System Evolution (自我演进) ──
  const EVP='/api/v1/agent-teams/evolution';
  async function loadEvolution(){
    const statusFilter=el('evo-filter')?.value||'';
    const itemsUrl=statusFilter?`${EVP}/items?status=${statusFilter}`:`${EVP}/items`;
    const[rules,items,summary,compliance]=await Promise.all([
      api(`${EVP}/rules`),api(itemsUrl),api(`${EVP}/summary`),api(`${EVP}/compliance-rating`)
    ]);
    const rs=el('evo-rules'),is=el('evo-items'),sc=el('evo-stats'),cc=el('evo-compliance');
  
    // Compliance Rating Card
    if(compliance&&cc){
      const grade=compliance.grade||'?';
      const score=compliance.score??0;
      const gradeColor={A:'var(--lime)',B:'var(--koke)',C:'var(--amber)',D:'var(--kitsune)',E:'var(--red)'}[grade]||'var(--muted)';
      cc.innerHTML=`<div class="stat-card" style="grid-column:span 2"><div style="display:flex;align-items:center;gap:20px"><div style="position:relative;width:64px;height:64px"><svg viewBox="0 0 36 36" style="width:64px;height:64px;transform:rotate(-90deg)"><circle cx="18" cy="18" r="16" fill="none" stroke="var(--groove)" stroke-width="3"/><circle cx="18" cy="18" r="16" fill="none" stroke="${gradeColor}" stroke-width="3" stroke-dasharray="${score} ${100-score}" stroke-linecap="round"/></svg><div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:900;color:${gradeColor};font-family:var(--font-mono)">${grade}</div></div><div><div class="label">合规评级</div><div class="value" style="font-size:18px;color:${gradeColor}">${score}/100</div><div class="sub">${compliance.description||'系统合规状态'}</div></div></div></div>`;
    }
  
    // Stats
    if(summary){
      const bs=summary.by_status||{};const bd=summary.by_domain||{};
      sc.innerHTML=`<div class="stat-card"><div class="label">📋 规则</div><div class="value">${summary.audit_rules_count||0}</div><div class="sub">验证函数 ${summary.verify_tests_registered||0}</div></div><div class="stat-card"><div class="label">🔍 演进项</div><div class="value">${summary.total_items||0}</div><div class="sub">${Object.entries(bs).map(([k,v])=>evoStL(k)+': '+v).join(' · ')||'无'}</div></div><div class="stat-card"><div class="label">📚 域分布</div><div class="value" style="font-size:13px">${Object.entries(bd).map(([k,v])=>k+' '+v).join(' · ')||'-'}</div></div>`;
    }
  
    // Active Zones
    loadEvoZones();
  
    // Rules — filter by selected team
    const isEnergy=(tid==='energy_first_principle');
    const filteredRules=(rules||[]).filter(r=>isEnergy?r.domain==='Datacenter':r.domain!=='Datacenter');
    if(filteredRules.length){
      rs.innerHTML=`<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--muted)">审查规则 (${filteredRules.length})</div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px">${filteredRules.map(r=>`<div style="padding:10px 14px;background:var(--panel2);border:1px solid var(--line);border-radius:0"><div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:12px">${escapeHtml(r.id)}</b><span class="chip" style="font-size:10px">${escapeHtml(r.domain)}</span></div><div style="font-size:12px;margin-top:4px;color:var(--text)">${escapeHtml(r.title)}</div><div style="font-size:11px;color:var(--dim);margin-top:2px">${escapeHtml(r.reference||'')}</div><div style="font-size:11px;margin-top:2px"><span style="color:${r.severity==='critical'?'var(--red)':r.severity==='high'?'var(--amber)':'var(--muted)'}">${escapeHtml(r.severity)}</span> · ${escapeHtml(r.target_channel)}</div></div>`).join('')}</div>`;
    } else { rs.innerHTML='<div style="color:var(--dim);font-size:12px">暂无审查规则</div>'; }
  
    // Items with action buttons
    if(items&&items.length){
      const maxItems=50;const shown=items.slice(0,maxItems);
      is.innerHTML=`<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--muted)">演进条目 (${items.length}${items.length>maxItems?' · 显示前'+maxItems+'条':''})</div><table class="tbl"><thead><tr><th>ID</th><th>标题</th><th>域</th><th>严重度</th><th>状态</th><th>目标</th><th>操作</th></tr></thead><tbody>${shown.map(i=>`<tr><td style="font-family:var(--font-mono);font-size:11px">${escapeHtml(i.id?.slice(0,8)||'')}</td><td><b>${escapeHtml(i.title)}</b></td><td><span class="chip" style="font-size:10px">${escapeHtml(i.audit_domain||'')}</span></td><td style="color:${i.severity==='critical'?'var(--red)':i.severity==='high'?'var(--amber)':'var(--muted)'}">${escapeHtml(i.severity||'')}</td><td>${evoStBadge(i.status)}</td><td style="font-size:12px">${escapeHtml(i.target_channel||'')}</td><td style="white-space:nowrap">${evoItemActions(i)}</td></tr>`).join('')}</tbody></table>${items.length>maxItems?`<button class="btn btn-sm" style
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
  
  ### 文件: `src/backend/startup_validator.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  Startup Validator - 系统启动完整性验证器
  
  提供:
  1. 后端服务启动检查
  2. API 端点可用性验证
  3. 核心模块初始化状态确认
  4. 结构化验证报告生成
  """
  
  from __future__ import annotations
  
  import asyncio
  import logging
  import time
  from dataclasses import dataclass, field
  from enum import Enum
  from typing import Any, Callable, Dict, List, Optional, Tuple
  
  import httpx
  
  logger = logging.getLogger("startup_validator")
  
  
  class CheckStatus(Enum):
      PASS = "pass"
      FAIL = "fail"
      WARN = "warn"
      SKIP = "skip"
  
  
  @dataclass
  class CheckResult:
      """单个检查项结果"""
      name: str
      status: CheckStatus
      detail: str = ""
      duration_ms: float = 0.0
      error: Optional[str] = None
      metadata: Dict[str, Any] = field(default_factory=dict)
  
  
  @dataclass
  class ValidationReport:
      """完整验证报告"""
      timestamp: float = field(default_factory=time.time)
      total_checks: int = 0
      passed: int = 0
      failed: int = 0
      warnings: int = 0
      skipped: int = 0
      checks: List[CheckResult] = field(default_factory=list)
      summary: str = ""
  
      def add(self, result: CheckResult):
          self.checks.append(result)
          self.total_checks += 1
          if result.status == CheckStatus.PASS:
              self.passed += 1
          elif result.status == CheckStatus.FAIL:
              self.failed += 1
          elif result.status == CheckStatus.WARN:
              self.warnings += 1
          elif result.status == CheckStatus.SKIP:
              self.skipped += 1
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "timestamp": self.timestamp,
              "total_checks": self.total_checks,
              "passed": self.passed,
              "failed": self.failed,
              "warnings": self.warnings,
              "skipped": self.skipped,
              "checks": [
                  {
                      "name": c.name,
                      "status": c.status.value,
                      "detail": c.detail,
                      "duration_ms": round(c.duration_ms, 1),
                      "error": c.error,
                      "metadata": c.metadata,
                  }
                  for c in self.checks
              ],
              "summary": self.summary or self._generate_summary(),
          }
  
      def _generate_summary(self) -> str:
          if self.failed > 0:
              return f"❌ {self.failed}/{self.total_checks} checks FAILED"
          if self.warnings > 0:
              return f"⚠️ {self.warnings}/{self.total_checks} checks have warnings"
          return f"✅ All {self.total_checks} checks passed"
  
  
  class StartupValidator:
      """系统启动验证器"""
  
      def __init__(self, base_url: str = "http://localhost:8080"):
          self.base_url = base_url.rstrip("/")
          self.client = httpx.AsyncClient(timeout=10.0)
          self._results: List[CheckResult] = []
  
      async def close(self):
          await self.client.aclose()
  
      async def _check(
          self,
          name: str,
          check_fn: Callable,
          timeout: float = 10.0,
      ) -> CheckResult:
          """执行单个检查项"""
          start = time.time()
          try:
              result = await asyncio.wait_for(check_fn(), timeout=timeout)
              if isinstance(result, CheckResult):
                  result.duration_ms = (time.time() - start) * 1000
                  return result
              return CheckResult(
                  name=name,
                  status=CheckStatus.PASS if result else CheckStatus.FAIL,
                  detail=str(result) if isinstance(result, str) else "",
                  duration_ms=(time.time() - start) * 1000,
              )
          except asyncio.TimeoutError:
              return CheckResult(
                  name=name,
                  status=CheckStatus.FAIL,
                  error=f"Timeout after {timeout}s",
                  duration_ms=(time.time() - start) * 1000,
              )
          except Exception as e:
              return CheckResult(
                  name=name,
                  status=CheckStatus.FAIL,
                  error=str(e),
                  duration_ms=(time.time() - start) * 1000,
              )
  
      async def run_all(self) -> ValidationReport:
          """运行所有验证检查"""
          report = ValidationReport()
  
          # 1. 基础服务检查
          report.add(await self._check_health())
          report.add(await self._check_info())
  
          # 2. API 端点可用性
          report.add(await self._check_api_endpoints())
  
          # 3. 核心模块状态
          report.add(await self._check_evolution_engine())
          report.add(await self._check_agent_config())
          report.add(await self._check_bridge_chat())
  
          # 4. 认证系统
          report.add(await self._check_auth())
  
          # 5. 前端页面
          report.add(await self._check_frontend_pages())
  
          return report
  
      async def _check_health(self) -> CheckResult:
          """检查健康端点"""
          async def check():
              resp = await self.client.get(f"{self.base_url}/api/v1/health")
              data = resp.json()
              if resp.status_code != 200:
                  return CheckResult(
                      name="health_endpoint",
                      status=CheckStatus.FAIL,
                      error=f"HTTP {resp.status_code}",
                  )
              services = data.get("services", {})
              offline = [k for k, v in services.items() if not v]
              if offline:
                  return CheckResult(
                      name="health_endpoint",
                      status=CheckStatus.WARN,
                      detail=f"Services offline: {', '.join(offline)}",
                      metadata={"services": services},
                  )
              return CheckResult(
                  name="health_endpoint",
                  status=CheckStatus.PASS,
                  detail=f"All services online: {list(services.keys())}",
                  metadata={"services": services},
              )
          return await self._check("health_endpoint", check)
  
      async def _check_info(self) -> CheckResult:
          """检查系统信息端点"""
          async def check():
              resp = await self.client.get(f"{self.base_url}/api/v1/info")
              data = resp.json()
              required_keys = ["name", "version", "capabilities", "endpoints"]
              missing = [k for k in required_keys if k not in data]
              if missing:
                  return CheckResult(
                      name="info_endpoint",
                      status=CheckStatus.FAIL,
                      error=f"Missing keys: {missing}",
                  )
              return CheckResult(
                  name="info_endpoint",
                  status=CheckStatus.PASS,
                  detail=f"System: {data.get('name')} v{data.get('version')}",
                  metadata=data,
              )
          return await self._check("info_endpoint", check)
  
      async def _check_api_endpoints(self) -> CheckResult:
          """检查关键 API 端点"""
          endpoints = [
              ("agent_teams_overview", "/api/v1/agent-teams/overview"),
              ("evolution_status", "/api/v1/agent-teams/evolution/status"),
              ("evolution_summary", "/api/v1/agent-teams/evolution/summary"),
              ("agent_config_teams", "/api/v1/agent-config/teams"),
              ("agent_config_agents", "/api/v1/agent-config/agents"),
          ]
  
          async def check():
              results = []
              for name, path in endpoints:
                  try:
                      resp = await self.client.get(f"{self.base_url}{path}")
                      if resp.status_code in (200, 404):
                          results.append(f"{name}: HTTP {resp.status_code}")
                      else:
                          results.append(f"{name}: HTTP {resp.status_code} (unexpected)")
                  except Exception as e:
                      results.append(f"{name}: ERROR - {str(e)[:50]}")
  
              failed = [r for r in results if "ERROR" in r or "unexpected" in r]
              if failed:
                  return CheckResult(
                      name="api_endpoints",
                      status=CheckStatus.WARN if len(failed) < len(endpoints) else CheckStatus.FAIL,
                      detail="; ".join(results),
                      metadata={"endpoints_checked": len(endpoints), "failed": len(failed)},
                  )
              return CheckResult(
                  name="api_endpoints",
                  status=CheckStatus.PASS,
                  detail=f"All {len(endpoints)} endpoints reachable",
                  metadata={"endpoints": [e[0] for e in endpoints]},
              )
          return await self._check("api_endpoints", check)
  
      async def _check_evolution_engine(self) -> CheckResult:
          """检查演进引擎状态"""
          async def check():
              resp = await self.client.get(
                  f"{self.base_url}/api/v1/agent-teams/evolution/status"
              )
              if resp.status_code == 404:
                  return CheckResult(
                      name="evolution_engine",
                      status=CheckStatus.FAIL,
                      error="Evolution engine not registered (HTTP 404)",
                  )
              data = resp.json()
              if data.get("status") == "initialized":
                  return CheckResult(
                      name="evolution_engine",
                      status=CheckStatus.PASS,
                      detail=f"Engine initialized with {data.get('audit_rules_count', 0)} rules",
                      metadata=data,
                  )
              return CheckResult(
                  name="evolution_engine",
                  status=CheckStatus.WARN,
                  detail=f"Engine status: {data.get('status', 'unknown')}",
                  metadata=data,
              )
          return await self._check("evolution_engine", check)
  
      async def _check_agent_config(self) -> CheckResult:
          """检查 Agent 配置 API"""
          async def check():
              resp = await self.client.get(f"{self.base_url}/api/v1/agent-config/teams")
              if resp.status_code != 200:
                  return CheckResult(
                      name="agent_config",
                      status=CheckStatus.FAIL,
                      error=f"HTTP {resp.status_code}",
                  )
              data = resp.json()
              teams = data if isinstance(data, list) else data.get("teams", [])
              return CheckResult(
                  name="agent_config",
                  status=CheckStatus.PASS,
                  detail=f"{len(teams)} teams configured",
                  metadata={"teams_count": len(teams)},
              )
          return await self._check("agent_config", check)
  
      async def _check_bridge_chat(self) -> CheckResult:
          """检查聊天通道"""
          async def check():
              resp = await self.client.post(
                  f"{self.base_url}/api/v1/bridge-chat/send",
                  json={
                      "message": "ping",
                      "session_id": "startup_validation",
                      "agent_id": "default_agent",
                  },
              )
              if resp.status_code != 200:
                  return CheckResult(
                      name="bridge_chat",
                      status=CheckStatus.FAIL,
                      error=f"HTTP {resp.status_code}",
                  )
              data = resp.json()
              if "reply" in data:
                  return CheckResult(
                      name="bridge_chat",
                      status=CheckStatus.PASS,
                      detail=f"Chat channel responsive (source: {data.get('source', 'unknown')})",
                      metadata={"source": data.get("source")},
                  )
              return CheckResult(
                  name="bridge_chat",
                  status=CheckStatus.WARN,
                  detail="Chat channel responded but no reply content",
                  metadata=data,
              )
          return await self._check("bridge_chat", check)
  
      async def _check_auth(self) -> CheckResult:
          """检查认证系统"""
          async def check():
              # 检查未认证状态
              resp = await self.client.get(
                  f"{self.base_url}/api/v1/auth/me",
                  headers={"Authorization": ""},
              )
              if resp.status_code != 200:
                  return CheckResult(
                      name="auth_system",
                      status=CheckStatus.FAIL,
                      error=f"Auth me endpoint: HTTP {resp.status_code}",
                  )
              data = resp.json()
              if data.get("authenticated") is False:
                  return CheckResult(
                      name="auth_system",
                      status=CheckStatus.PASS,
                      detail="Auth system working (guest mode)",
                      metadata=data,
                  )
              return CheckResult(
                  name="auth_system",
                  status=CheckStatus.WARN,
                  detail=f"Unexpected auth state: {data}",
                  metadata=data,
              )
          return await self._check("auth_system", check)
  
      async def _check_frontend_pages(self) -> CheckResult:
          """检查前端页面可访问性"""
          pages = [
              ("index", "/"),
              ("login", "/login.html"),
              ("plaza", "/plaza.html"),
              ("system_evolution", "/system-evolution.html"),
              ("agent_team_config", "/agent-team-config.html"),
          ]
  
          async def check():
              results = []
              for name, path in pages:
                  try:
                      resp = await self.client.get(f"{self.base_url}{path}")
                      if resp.status_code == 200:
                          content_type = resp.headers.get("content-type", "")
                          if "text/html" in content_type or "text/plain" in content_type:
                              results.append(f"{name}: OK")
                          else:
                              results.append(f"{name}: HTTP 200 but content-type={content_type}")
                      else:
                          results.append(f"{name}: HTTP {resp.status_code}")
                  except Exception as e:
                      results.append(f"{name}: ERROR - {str(e)[:50]}")
  
              failed = [r for r in results if "ERROR" in r or "HTTP 4" in r or "HTTP 5" in r]
              if failed:
                  return CheckResult(
                      name="frontend_pages",
                      status=CheckStatus.WARN if len(failed) < len(pages) else CheckStatus.FAIL,
                      detail="; ".join(results),
                      metadata={"pages_checked": len(pages), "failed": len(failed)},
                  )
              return CheckResult(
                  name="frontend_pages",
                  status=CheckStatus.PASS,
                  detail=f"All {len(pages)} frontend pages accessible",
                  metadata={"pages": [p[0] for p in pages]},
              )
          return await self._check("frontend_pages", check)
  
  
  # ── 便捷函数 ──
  
  async def validate_startup(
      base_url: str = "http://localhost:8080",
      verbose: bool = True,
  ) -> ValidationReport:
      """执行完整的启动验证"""
      validator = StartupValidator(base_url)
      try:
          report = await validator.run_all()
          if verbose:
              _print_report(report)
          return report
      finally:
    
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
          return len(sel
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  ## 要求
  1. 分析任务需求，拆解为可执行的子步骤
  2. 识别技术风险和依赖关系
  3. 为后续研究人员、架构师、开发者提供清晰的指导
  4. 输出一份结构化的任务分解文档 (Markdown 格式)
  
  ## ⚠️ 重要提示
  系统已自动预加载项目文件结构和相关源文件（见下方 📂 项目上下文）。
  请基于**实际存在的文件**进行分析，不要猜测文件名。
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
⚡ 使用 DeepSeek V4 直连 (64K 输出, 流式)...

🔗 API: 127.0.0.1 | 模型: deepseek-chat
────────────────────────────────────────────────────────────

⚠️ 连接错误: [Errno 61] Connection refused

🔄 连接重试 (1/2)...

⚠️ 连接错误: [Errno 61] Connection refused

🔄 连接重试 (2/2)...

⚠️ 连接错误: [Errno 61] Connection refused

❌ 所有重试已耗尽: [Errno 61] Connection refused
