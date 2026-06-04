// Shared globals — var for cross-script access (tools-skills.js, tasks-view.js, etc.)
var A='/api/v1/agent-config',AT='/api/v1/agent-teams',TF='/api/v1/token-factory';
const csrfFetch = window._agFetch || fetch;

// ── Namespaced state (window.AG.state is the source of truth) ──
window.AG = window.AG || {};
window.AG.state = window.AG.state || {
  tid: '', aid: '', atab: 'ag-status', wzD: {}, wzS: 1,
  _teamsListCache: null, _teamsListCacheAt: 0,
  _offline: false, _currentOverviewTeam: null, _currentTraceSummaries: [],
  _lastRequestId: '',
};

// Legacy aliases — proxy bare names through AG.state via window property descriptors.
// Any read/write to tid/aid/atab/wzD/wzS etc. goes to AG.state directly.
// This keeps onclick/cross-script compat without needing to touch other files.
(function(){
  var PROXY_MAP = [
    'tid', 'aid', 'atab', 'wzD', 'wzS',
    '_offline', '_teamsListCache', '_teamsListCacheAt',
    '_currentOverviewTeam', '_currentTraceSummaries', '_lastRequestId',
  ];
  PROXY_MAP.forEach(function(k){
    Object.defineProperty(window, k, {
      get: function(){ return window.AG.state[k]; },
      set: function(v){ window.AG.state[k] = v; },
      configurable: true,
    });
  });
})();

// Cache TTL constants (not mutable state, kept as module-level bindings)
var TEAMS_LIST_CACHE_MS = 60000;

window.AG.getTeamId = function() { return window.AG.state.tid; };
window.AG.setTeamId = function(v) { window.AG.state.tid = v; };
window.AG.getAgentId = function() { return window.AG.state.aid; };
window.AG.setAgentId = function(v) { window.AG.state.aid = v; };

function toast(m,type){
  const e=document.getElementById('toast');
  e.className='toast'+(type?' toast-'+type:'');
  var text=String(m??'');
  var requestId=_lastRequestId||api._lastError?.request_id||'';
  var shouldDecorate=type==='error'||/失败|错误|异常|不可用|未找到|无法|无效|请求失败/.test(text);
  e.textContent=shouldDecorate&&requestId&&text.indexOf('请求ID:')===-1?`${text} · 请求ID: ${requestId}`:text;
  e.classList.add('show');
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

// Simple GET request cache (TTL 5s) to reduce waterfall requests
var _reqCache = {};
var _REQ_CACHE_TTL = 5000;

// CSRF token for state-changing requests — fetched once at startup
var _csrfToken = '';
var _csrfPromise = null;
function _ensureCsrf() {
  if (_csrfToken) return Promise.resolve(_csrfToken);
  if (_csrfPromise) return _csrfPromise;
  _csrfPromise = fetch('/api/v1/auth/csrf-token')
    .then(function(r) { return r.json(); })
    .then(function(d) { _csrfToken = d.csrf_token || ''; return _csrfToken; })
    .catch(function() { _csrfPromise = null; return ''; });
  return _csrfPromise;
}
// Pre-fetch CSRF token at load time (fire-and-forget)
_ensureCsrf();

function _apiMakeOpts(o) {
  var opts = {};
  if (o) {
    for (var k in o) {
      if (k === 'headers') {
        opts.headers = {};
        for (var h in o.headers) { opts.headers[h] = o.headers[h]; }
      } else {
        opts[k] = o[k];
      }
    }
  }
  // Attach CSRF token for state-changing methods
  var method = (opts.method || 'GET').toUpperCase();
  opts.headers = opts.headers || {};
  if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
    if (_csrfToken) opts.headers['x-csrf-token'] = _csrfToken;
  }
  if (!opts.headers['x-request-id']) {
    opts.headers['x-request-id'] = `ag-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,10)}`;
  }
  return opts;
}

function _sharedApiClient() {
  return (window.api && typeof window.api.request === 'function') ? window.api : null;
}

function _redirectToLoginPage() {
  const next = window.location.pathname + window.location.search + window.location.hash;
  window.location.href = '/login.html?next=' + encodeURIComponent(next);
}

async function ensureAuthenticatedPage() {
  try {
    const authResp = await fetch('/api/v1/auth/me', { credentials: 'same-origin' });
    if (authResp.status === 401) {
      _redirectToLoginPage();
      return false;
    }
    if (!authResp.ok) return true;
    const authData = await authResp.json().catch(function(){ return null; });
    if (authData && authData.authenticated === false) {
      _redirectToLoginPage();
      return false;
    }
  } catch (e) {
    // Let the existing offline banner flow handle true connectivity failures.
  }
  return true;
}

async function api(p, o) {
  var method = (o && o.method) ? o.method.toUpperCase() : 'GET';
  if (method === 'GET') {
    var key = 'GET:' + p;
    var cached = _reqCache[key];
    if (cached && Date.now() - cached.at < _REQ_CACHE_TTL) {
      return cached.data;
    }
    try {
      var getOpts = _apiMakeOpts(o);
      var sharedGet = _sharedApiClient();
      var data = null;
      if (sharedGet) {
        data = await sharedGet.request(p, getOpts);
        _lastRequestId = sharedGet.getLastRequestId ? sharedGet.getLastRequestId() : (sharedGet._lastRequestId || '');
        api._lastError = sharedGet._lastError || null;
      } else {
        var getReqId = getOpts.headers && getOpts.headers['x-request-id'] || '';
        var r = await fetch(p, getOpts);
        _lastRequestId = r.headers && typeof r.headers.get === 'function' ? (r.headers.get('X-Request-ID') || getReqId) : getReqId;
        if (!r.ok) {
          var msg = '';
          try { var d = await r.json(); msg = d.detail || d.message || ''; } catch(e) {}
          api._lastError = {status: r.status, message: msg, url: p, request_id: _lastRequestId || getReqId};
          return null;
        }
        data = await r.json();
        api._lastError = null;
      }
      if (_offline) { hideOfflineBanner(); }
      if (data !== null && data !== undefined) {
        _reqCache[key] = { data: data, at: Date.now() };
      }
      return data;
    } catch(e) {
      _lastRequestId = _lastRequestId || '';
      if (e.name === 'TypeError' || (e.message && e.message.indexOf('fetch') !== -1)) {
        _offline = true;
        showOfflineBanner();
      }
      api._lastError = {status: 0, message: e.message, url: p, network: true, request_id: _lastRequestId || ''};
      return null;
    }
  }
  // Mutations: ensure CSRF, clear cache, send
  await _ensureCsrf();
  var pathBase = p.split('?')[0];
  Object.keys(_reqCache).forEach(function(k) { if (k.indexOf(pathBase) !== -1) delete _reqCache[k]; });
  var opts = _apiMakeOpts(o);
  try {
    var sharedMutation = _sharedApiClient();
    if (sharedMutation) {
      var sharedData = await sharedMutation.request(p, opts);
      _lastRequestId = sharedMutation.getLastRequestId ? sharedMutation.getLastRequestId() : (sharedMutation._lastRequestId || '');
      api._lastError = sharedMutation._lastError || null;
      return sharedData;
    }
    var r2 = await fetch(p, opts);
    var reqId = opts.headers && opts.headers['x-request-id'] || '';
    _lastRequestId = r2.headers && typeof r2.headers.get === 'function' ? (r2.headers.get('X-Request-ID') || reqId) : reqId;
    if (!r2.ok) {
      var msg2 = '';
      try { var d2 = await r2.json(); msg2 = d2.detail || d2.message || ''; } catch(e3) {}
      api._lastError = {status: r2.status, message: msg2, url: p, request_id: _lastRequestId || reqId};
      return null;
    }
    api._lastError = null;
    return await r2.json();
  } catch(e2) {
    api._lastError = {status: 0, message: e2.message, url: p, network: true, request_id: _lastRequestId || ''};
    return null;
  }
}
api._lastError = null;
async function getTeamsList(force=false){
  const now=Date.now();
  if(!force&&_teamsListCache&&(now-_teamsListCacheAt)<TEAMS_LIST_CACHE_MS){
    return _teamsListCache;
  }
  const teams=await api(`${A}/teams`);
  if(Array.isArray(teams)&&teams.length){
    _teamsListCache=teams;
    _teamsListCacheAt=now;
    return teams;
  }
  return _teamsListCache||teams||[];
}

async function bootAgentTeamConfigPage(){
  const ok = await ensureAuthenticatedPage();
  if (!ok) return;
  return loadTeams();
}

function stL(s){return{idle:'待命中',working:'工作中',reporting:'汇报中',blocked:'阻塞',error:'异常'}[s]||s||'未知'}
function el(id){return document.getElementById(id)}
function escapeHtml(v){return String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}

function showViewLoading(viewId) {
  const el = document.getElementById(viewId);
  if (!el) return;
  hideViewLoading(viewId);
  const scroll = el.querySelector('.main-scroll') || el;
  const div = document.createElement('div');
  div.className = 'view-loading-el';
  div.style.cssText = 'display:flex;justify-content:center;align-items:center;padding:80px 0;color:var(--muted);font-size:13px';
  div.innerHTML = '<span style="display:inline-block;width:16px;height:16px;border:2px solid var(--groove);border-top-color:var(--koke);border-radius:50%;animation:spin .6s linear infinite;margin-right:10px"></span>加载中...';
  scroll.prepend(div);
}
function hideViewLoading(viewId) {
  const el = document.getElementById(viewId);
  if (!el) return;
  el.querySelectorAll('.view-loading-el').forEach(function(e) { e.remove(); });
}
function showInfoModal(title, body) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay open';
  overlay.onclick = function(e) { if (e.target === this) overlay.remove(); };
  overlay.innerHTML = '<div class="modal"><h3>' + escapeHtml(title) + '</h3><div style="font-size:13px;line-height:1.7;white-space:pre-wrap;word-break:break-word">' + body + '</div><div class="modal-actions"><button class="btn">关闭</button></div></div>';
  overlay.querySelector('.modal .btn').onclick = function() { overlay.remove(); };
  document.body.appendChild(overlay);
}

// ── Teams ──
async function loadTeams(){
  const d=await getTeamsList(true);const s=el('team-select');
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
  // Safe loader: catches sync/async errors and hides the loading spinner
  function _safe(fn,viewId){try{var p=fn();if(p&&typeof p.catch==='function')p.catch(function(e){console.error('Load error '+viewId,e);hideViewLoading(viewId)})}catch(e){console.error('Load error '+viewId,e);hideViewLoading(viewId)}}
  if(v==='overview'){el('view-overview').classList.remove('hidden');t.textContent='团队概览';b.textContent=tid;_safe(loadOverview,'view-overview')}
  else if(v==='models'){el('view-models').classList.remove('hidden');showViewLoading('view-models');t.textContent='模型池';b.textContent='';_safe(loadModels,'view-models')}
  else if(v==='tools'){el('view-tools').classList.remove('hidden');showViewLoading('view-tools');t.textContent='工具管理';b.textContent='';_safe(loadTools,'view-tools')}
  else if(v==='skills'){el('view-skills').classList.remove('hidden');showViewLoading('view-skills');t.textContent='技能管理';b.textContent='';_safe(loadSkills,'view-skills')}
  else if(v==='tasks'){el('view-tasks').classList.remove('hidden');showViewLoading('view-tasks');t.textContent='并发任务';b.textContent='';_safe(loadTasks,'view-tasks')}
  else if(v==='llm'){el('view-llm').classList.remove('hidden');showViewLoading('view-llm');t.textContent='LLM 配置';b.textContent='';_safe(loadLLMStatus,'view-llm');_safe(loadTTSConfig,'view-llm')}
  else if(v==='sessions'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-sessions').classList.remove('hidden');showViewLoading('view-sessions');t.textContent='会话存档';b.textContent='';_safe(loadPersistedSessions,'view-sessions')}
  else if(v==='runtime'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-runtime').classList.remove('hidden');hideViewLoading('view-runtime');t.textContent='PortRuntime';b.textContent='claw-code-parity';el('rt-results').classList.add('hidden')}
  else if(v==='registry'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-registry').classList.remove('hidden');showViewLoading('view-registry');t.textContent='自主 Token 工厂';b.textContent='Token Factory';_safe(loadTokenFactory,'view-registry');_startTfPoll()}
  else if(v==='agent'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='';el('agent-content').style.display='';_safe(function(){return loadAgent(extra)},'view-agent')}
  else if(v==='wizard'){el('view-wizard').classList.remove('hidden');t.textContent='新建智能体';b.textContent=''}
}
function loadView(){
  // ── Darwin rule: bridge-task-dispatch deep-link support ──
  const params = new URLSearchParams(window.location.search);
  const view = params.get('view');
  const nextView=view && document.querySelector(`[data-view="${view}"]`) ? view : 'overview';
  if(nextView!=='overview')loadSbAgents();
  switchView(nextView);
}

// ── Sidebar agents ──
function renderSbAgents(team){
  const c=el('sb-agents');
  if(!team||!team.agents){c.innerHTML='<div style="padding:12px;color:var(--dim);font-size:12px">暂无成员</div>';return}
  const aa=Array.isArray(team.agents)?team.agents:Object.values(team.agents);
  c.innerHTML=aa.map(a=>`<div class="sb-agent${a.agent_id===aid?' active':''}" onclick="selectAgent('${a.agent_id}')"><span class="dot ${a.state||'idle'}"></span><span style="overflow:hidden;text-overflow:ellipsis">${escapeHtml(a.name||a.agent_id)}</span></div>`).join('');
}

async function loadSbAgents(){
  const d=await api(`${A}/teams/${tid}`);
  renderSbAgents(d);
}
function selectAgent(id){aid=id;switchView('agent',id)}

// ── Overview ──
let _ovTimer=null;
let _traceDetailTaskId='';
let _traceRequestIds={summaries:'',events:'',detail:''};
async function loadOverview(){
  if(_ovTimer)clearInterval(_ovTimer);
  const [teamsList,ov]=await Promise.all([
    getTeamsList(),
    api(`${AT}/overview?team_id=${encodeURIComponent(tid)}`)
  ]);
  const curTm=ov?.current_team||null;
  const sc=el('ov-stats');
  const _teamIcons={'build_system':'🏗️','energy_first_principle':'⚡','ai_coding':'💻','d083a568':'☁️'};
  const allTeams=teamsList||[];
  if(ov){
    const sh=ov.scheduler||{};
    const ev=ov.evolution||{};
    const evs=ev.stats||{};
    const taskSummary=curTm?.tasks||{};
    const totalModels=allTeams.reduce((n,t)=>n+(Number(t?.model_count)||0),0);
    const totalAgents=allTeams.reduce((n,t)=>n+(Number(t?.agent_count)||0),0);
    const teamCards=allTeams.filter(Boolean).map(t=>{const ic=_teamIcons[t.team_id]||'🤖';return`<div class="stat-card" style="cursor:pointer" onclick="el('team-select').value='${t.team_id}';tid='${t.team_id}';loadView()"><div class="label">${ic} ${escapeHtml(t.name||t.team_id)}</div><div class="value">${t.agent_count??0}</div><div class="sub">${escapeHtml(t.description||'').slice(0,30)}</div></div>`}).join('');
    sc.innerHTML=`<div class="stat-card"><div class="label">📊 调度器</div><div class="value" style="font-size:16px;color:${sh.running?'var(--lime)':'var(--red)'}">${sh.running?'运行中':'已停止'}</div><div class="sub">Tick ${sh.tick_count??0} · 运行 ${Math.round((sh.uptime_seconds||0)/60)}m</div></div>${teamCards}<div class="stat-card"><div class="label">🔄 自我演进</div><div class="value">${ev?.evolution_items_count??'-'}</div><div class="sub">规则 ${ev?.audit_rules_count??0} · 已验证 ${evs?.total_verified??0}</div></div><div class="stat-card"><div class="label">📦 模型</div><div class="value">${totalModels}</div></div><div class="stat-card"><div class="label">🤖 智能体</div><div class="value">${totalAgents}</div></div><div class="stat-card"><div class="label">📋 任务</div><div class="value">${taskSummary.total||0}</div><div class="sub">${Object.entries(taskSummary.by_status||{}).map(([k,v])=>`${k}: ${v}`).join(' · ')||'无任务'}</div></div>`;
    const curTmMeta=allTeams.find(t=>t&&t.team_id===tid);
    const teamTitle=(curTm&&curTm.name)||(curTmMeta&&curTmMeta.name)||tid;
    const teamIcon=_teamIcons[tid]||'🤖';
    renderSbAgents(curTm);
    el('ov-team-title').textContent=`${teamIcon} ${teamTitle}`;
    const tbody=el('ov-team-agents');tbody.innerHTML='';
    if(curTm&&curTm.agents){
      const aa=Array.isArray(curTm.agents)?curTm.agents:Object.values(curTm.agents);
      aa.forEach(a=>{tbody.innerHTML+=`<tr><td><b>${escapeHtml(a.name||a.agent_id)}</b></td><td style="color:var(--muted)">${escapeHtml(a.role||'-')}</td><td><span class="st st-${a.state||'idle'}">${stL(a.state)}</span></td><td>${(a.skills||[]).slice(0,3).map(s=>'<span class="chip">'+s+'</span>').join('')}</td><td><button class="btn btn-sm btn-ghost" onclick="selectAgent('${a.agent_id}')">查看</button></td></tr>`});
    }
    if(!tbody.innerHTML)tbody.innerHTML='<tr><td colspan="5" style="color:var(--dim)">暂无</td></tr>';
    refreshTracePanel();
    _ovTimer=setInterval(()=>{
      if(document.hidden||!document.querySelector('#view-overview:not(.hidden)')){
        clearInterval(_ovTimer);
        _ovTimer=null;
        return;
      }
      // Incremental refresh
      if (typeof refreshBudgetPanel === 'function') refreshBudgetPanel();
      if (typeof refreshTracePanel === 'function') refreshTracePanel();
    },10000);
    loadEvolution(ov?.evolution?.compliance_rating||null);
  }
}

function _traceReqText(id){
  return id?`请求ID: ${escapeHtml(id)}`:'';
}

function _formatTraceTime(ts){
  if(!ts)return '-';
  const ms=Number(ts)*1000;
  if(Number.isNaN(ms))return '-';
  return new Date(ms).toLocaleString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

function _traceStatusColor(status){
  return {
    completed:'var(--lime)',
    failed:'var(--red)',
    running:'var(--cyan)',
    queued:'var(--amber)',
    pending:'var(--amber)',
  }[status]||'var(--muted)';
}

function _renderTraceSummaries(payload, requestId){
  const wrap=el('trace-summaries');
  if(!wrap)return;
  const traces=payload?.traces||[];
  if(!traces.length){
    wrap.innerHTML=`<div style="color:var(--dim);font-size:12px;padding:8px 0">暂无运行痕迹${requestId?` · ${_traceReqText(requestId)}`:''}</div>`;
    return;
  }
  wrap.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin:8px 0 6px"><div style="font-size:12px;color:var(--muted)">任务概览 (${traces.length})</div><div style="font-size:11px;color:var(--dim);font-family:var(--font-mono)">${_traceReqText(requestId)}</div></div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px">${traces.map(t=>{const ctx=t.trace_context||{};const wf=t.workflow_summary||{};const test=t.test_result||{};const verify=t.linked_evolution_items||[];return `<div style="padding:10px 12px;background:var(--panel2);border:1px solid var(--line)"><div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start"><div><div style="font-size:12px;font-weight:600">${escapeHtml(t.task_id?.slice(0,8)||'')}</div><div style="font-size:11px;color:var(--dim);margin-top:3px">${escapeHtml(ctx.source||t.source||'task')} · ${escapeHtml(ctx.discussion_topic||ctx.discussion_id||t.agent_id||'-')}</div></div><div style="font-size:11px;color:${_traceStatusColor(t.status)};font-weight:600">${escapeHtml(t.status||'-')}</div></div><div style="font-size:11px;color:var(--text);line-height:1.7;margin-top:8px">事件 ${t.trace_event_count||0} · 变更 ${(t.changed_files||[]).length} · 测试 ${escapeHtml(test.verdict||t.build_outcome||wf.verdict||'-')}</div><div style="font-size:11px;color:var(--dim);line-height:1.6;margin-top:4px">${verify.length?`关联演进 ${verify.length} 项 · `:''}${(t.recent_trace_events||[]).length?_formatTraceTime(t.recent_trace_events[t.recent_trace_events.length-1].ts):'无最近事件'}</div><div style="display:flex;gap:6px;margin-top:8px"><button class="btn btn-sm" onclick="showTraceDetail('${t.task_id}')">查看明细</button>${ctx.discussion_id?`<a class="btn btn-sm" href="/plaza.html?plaza_id=${encodeURIComponent(ctx.plaza_id||'')}&discussion_id=${encodeURIComponent(ctx.discussion_id)}">讨论</a>`:''}</div></div>`;}).join('')}</div>`;
}

function _renderTraceEvents(payload, requestId){
  const wrap=el('trace-events');
  if(!wrap)return;
  const events=payload?.events||[];
  wrap.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin:14px 0 6px"><div style="font-size:12px;color:var(--muted)">最近事件 (${events.length})</div><div style="font-size:11px;color:var(--dim);font-family:var(--font-mono)">${_traceReqText(requestId)}</div></div>${events.length?`<div style="display:flex;flex-direction:column;gap:6px">${events.slice(0,12).map(ev=>`<div style="padding:8px 10px;background:var(--panel2);border:1px solid var(--line)"><div style="display:flex;justify-content:space-between;gap:8px"><div style="font-size:12px"><b>${escapeHtml(ev.type||'-')}</b> · <span style="color:var(--dim)">${escapeHtml(ev.task_id?.slice(0,8)||'')}</span></div><div style="font-size:11px;color:var(--dim)">${_formatTraceTime(ev.ts)}</div></div><div style="font-size:11px;color:var(--text);margin-top:4px;line-height:1.6">${escapeHtml(ev.trace_context?.discussion_topic||ev.trace_context?.discussion_id||ev.trace_context?.source||'-')}</div></div>`).join('')}</div>`:`<div style="color:var(--dim);font-size:12px;padding:4px 0">暂无匹配事件</div>`}`;
}

function _renderTraceDetail(taskId, payload, requestId){
  const wrap=el('trace-detail');
  if(!wrap)return;
  const events=payload?.events||[];
  wrap.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin:14px 0 6px"><div style="font-size:12px;color:var(--muted)">任务明细 ${escapeHtml(taskId?.slice(0,8)||'')}</div><div style="font-size:11px;color:var(--dim);font-family:var(--font-mono)">${_traceReqText(requestId)}</div></div>${events.length?`<div style="display:flex;flex-direction:column;gap:8px">${events.map(ev=>`<div style="padding:10px 12px;background:var(--panel2);border:1px solid var(--line)"><div style="display:flex;justify-content:space-between;gap:8px"><div style="font-size:12px;font-weight:600">${escapeHtml(ev.type||'-')}</div><div style="font-size:11px;color:var(--dim)">${_formatTraceTime(ev.ts)}</div></div><div style="font-size:11px;color:var(--dim);margin-top:4px">${escapeHtml(ev.trace_context?.discussion_topic||ev.trace_context?.discussion_id||ev.trace_context?.source||'-')}</div><pre style="margin-top:8px;white-space:pre-wrap;word-break:break-word;font-size:11px;line-height:1.6;color:var(--text);background:rgba(0,0,0,0.12);padding:8px;border:1px solid var(--line)">${escapeHtml(JSON.stringify(ev.payload||{},null,2))}</pre></div>`).join('')}</div>`:`<div style="color:var(--dim);font-size:12px;padding:4px 0">没有可展示的事件明细</div>`}`;
}

async function refreshTracePanel(){
  if(!tid)return;
  const source=el('trace-source-filter')?.value||'';
  const eventType=el('trace-event-filter')?.value||'';
  const exportLink=el('trace-export-link');
  if(exportLink){
    const params=new URLSearchParams({team_id:tid,limit:'500'});
    if(source)params.set('source',source);
    if(eventType)params.set('event_type',eventType);
    exportLink.href=`${A}/traces/export?${params.toString()}`;
  }
  const summaryUrl=`${A}/traces/recent?team_id=${encodeURIComponent(tid)}${source?`&source=${encodeURIComponent(source)}`:''}`;
  const summaries=await api(summaryUrl);
  const summariesReqId=_lastRequestId||'';
  _traceRequestIds.summaries=summariesReqId;
  _renderTraceSummaries(summaries,summariesReqId);

  const eventsUrl=`${A}/traces/recent-events?team_id=${encodeURIComponent(tid)}${source?`&source=${encodeURIComponent(source)}`:''}${eventType?`&event_type=${encodeURIComponent(eventType)}`:''}`;
  const events=await api(eventsUrl);
  const eventsReqId=_lastRequestId||'';
  _traceRequestIds.events=eventsReqId;
  _renderTraceEvents(events,eventsReqId);

  if(_traceDetailTaskId){
    showTraceDetail(_traceDetailTaskId,true);
  }
}

async function showTraceDetail(taskId, silent){
  if(!tid||!taskId)return;
  _traceDetailTaskId=taskId;
  const payload=await api(`${A}/teams/${tid}/tasks/${taskId}/trace-events`);
  const detailReqId=_lastRequestId||'';
  _traceRequestIds.detail=detailReqId;
  _renderTraceDetail(taskId,payload,detailReqId);
  if(!silent&&payload){toast(`已加载任务明细 ${taskId.slice(0,8)}`)}
}

// ── System Evolution (自我演进) ──
const EVP='/api/v1/agent-teams/evolution';
const EVO_ITEMS_PAGE_SIZE=50;
let evoVisibleCount=EVO_ITEMS_PAGE_SIZE;
let evoCachedItems=[];

async function loadEvolution(prefetchedCompliance=null){
  const statusFilter=el('evo-filter')?.value||'';
  const itemsUrl=statusFilter?`${EVP}/items?status=${statusFilter}`:`${EVP}/items`;
  const rs=el('evo-rules'),is=el('evo-items'),sc=el('evo-stats'),cc=el('evo-compliance');
  const needsDetailedData=Boolean(rs||is||sc);
  const complianceReq=prefetchedCompliance?Promise.resolve(prefetchedCompliance):api(`${EVP}/compliance-rating`);
  const [rules,items,summary,compliance]=needsDetailedData
    ? await Promise.all([
        api(`${EVP}/rules`),
        api(itemsUrl),
        api(`${EVP}/summary`),
        complianceReq
      ])
    : [null,null,null,await complianceReq];

  // Compliance Rating Card
  if(compliance&&cc){
    const grade=compliance.grade||'?';
    const score=compliance.score??0;
    const gradeColor={A:'var(--lime)',B:'var(--koke)',C:'var(--amber)',D:'var(--kitsune)',E:'var(--red)'}[grade]||'var(--muted)';
    cc.innerHTML=`<div class="stat-card" style="grid-column:span 2"><div style="display:flex;align-items:center;gap:20px"><div style="position:relative;width:64px;height:64px"><svg viewBox="0 0 36 36" style="width:64px;height:64px;transform:rotate(-90deg)"><circle cx="18" cy="18" r="16" fill="none" stroke="var(--groove)" stroke-width="3"/><circle cx="18" cy="18" r="16" fill="none" stroke="${gradeColor}" stroke-width="3" stroke-dasharray="${score} ${100-score}" stroke-linecap="round"/></svg><div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:900;color:${gradeColor};font-family:var(--font-mono)">${grade}</div></div><div><div class="label">合规评级</div><div class="value" style="font-size:18px;color:${gradeColor}">${score}/100</div><div class="sub">${compliance.description||'系统合规状态'}</div></div></div></div>`;
  }

  // Stats
  if(summary&&sc){
    const bs=summary.by_status||{};const bd=summary.by_domain||{};
    sc.innerHTML=`<div class="stat-card"><div class="label">📋 规则</div><div class="value">${summary.audit_rules_count||0}</div><div class="sub">验证函数 ${summary.verify_tests_registered||0}</div></div><div class="stat-card"><div class="label">🔍 演进项</div><div class="value">${summary.total_items||0}</div><div class="sub">${Object.entries(bs).map(([k,v])=>evoStL(k)+': '+v).join(' · ')||'无'}</div></div><div class="stat-card"><div class="label">📚 域分布</div><div class="value" style="font-size:13px">${Object.entries(bd).map(([k,v])=>k+' '+v).join(' · ')||'-'}</div></div>`;
  }

  if(!needsDetailedData){
    return;
  }

  // Active Zones
  loadEvoZones();

  // Rules — filter by selected team
  const isEnergy=(tid==='energy_first_principle');
  const filteredRules=(rules||[]).filter(r=>isEnergy?r.domain==='Datacenter':r.domain!=='Datacenter');
  if(rs&&filteredRules.length){
    rs.innerHTML=`<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--muted)">审查规则 (${filteredRules.length})</div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px">${filteredRules.map(r=>`<div style="padding:10px 14px;background:var(--panel2);border:1px solid var(--line);border-radius:0"><div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:12px">${escapeHtml(r.id)}</b><span class="chip" style="font-size:10px">${escapeHtml(r.domain)}</span></div><div style="font-size:12px;margin-top:4px;color:var(--text)">${escapeHtml(r.title)}</div><div style="font-size:11px;color:var(--dim);margin-top:2px">${escapeHtml(r.reference||'')}</div><div style="font-size:11px;margin-top:2px"><span style="color:${r.severity==='critical'?'var(--red)':r.severity==='high'?'var(--amber)':'var(--muted)'}">${escapeHtml(r.severity)}</span> · ${escapeHtml(r.target_channel)}</div></div>`).join('')}</div>`;
  } else if(rs) { rs.innerHTML='<div style="color:var(--dim);font-size:12px">暂无审查规则</div>'; }

  // Items with action buttons
  evoCachedItems=items||[];
  evoVisibleCount=EVO_ITEMS_PAGE_SIZE;
  renderEvolutionItems();
}

function renderEvolutionItems(){
  const is=el('evo-items');
  if(!is)return;
  if(!evoCachedItems.length){
    is.innerHTML='<div style="color:var(--dim);font-size:12px;padding:8px">暂无演进条目 — 点击「审查」或「运行演进周期」开始</div>';
    return;
  }
  const shown=evoCachedItems.slice(0,evoVisibleCount);
  const remaining=Math.max(0,evoCachedItems.length-shown.length);
  is.innerHTML=`<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--muted)">演进条目 (${evoCachedItems.length}${remaining>0?' · 显示前'+shown.length+'条':''})</div><table class="tbl"><thead><tr><th>ID</th><th>标题</th><th>域</th><th>严重度</th><th>状态</th><th>目标</th><th>操作</th></tr></thead><tbody>${shown.map(i=>`<tr><td style="font-family:var(--font-mono);font-size:11px">${escapeHtml(i.id?.slice(0,8)||'')}</td><td><b>${escapeHtml(i.title)}</b></td><td><span class="chip" style="font-size:10px">${escapeHtml(i.audit_domain||'')}</span></td><td style="color:${i.severity==='critical'?'var(--red)':i.severity==='high'?'var(--amber)':'var(--muted)'}">${escapeHtml(i.severity||'')}</td><td>${evoStBadge(i.status)}</td><td style="font-size:12px">${escapeHtml(i.target_channel||'')}</td><td style="white-space:nowrap">${evoItemActions(i)}</td></tr>`).join('')}</tbody></table>${remaining>0?`<button class="btn btn-sm" style="margin-top:8px" onclick="evoLoadMore()">加载更多 (${remaining} 剩余)</button>`:''}`;
}

function evoLoadMore(){
  evoVisibleCount+=EVO_ITEMS_PAGE_SIZE;
  renderEvolutionItems();
}

function evoItemActions(item){
  const s=item.status;
  if(s==='discovered')return `<button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="evoMarkProgress('${item.id}')">开始</button>`;
  if(s==='in_progress')return `<button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="evoMarkComplete('${item.id}')">完成</button>`;
  if(s==='verify_pending')return `<span style="font-size:11px;color:var(--amber)">待验证</span>`;
  if(s==='verified')return `<span style="font-size:11px;color:var(--lime)">✓</span>`;
  if(s==='failed')return `<span style="font-size:11px;color:var(--red)">✗</span>`;
  return '—';
}

async function evoMarkProgress(itemId){
  const r=await api(`${EVP}/items/${itemId}/progress`,{method:'POST'});
  if(r){toast('已标记为进行中');loadEvolution()}else toast('操作失败')
}
async function evoMarkComplete(itemId){
  const r=await api(`${EVP}/items/${itemId}/complete`,{method:'POST'});
  if(r){toast('已标记完成，等待验证');loadEvolution()}else toast('操作失败')
}

async function loadEvoZones(){
  const zc=el('evo-zones');if(!zc)return;
  const zones=await api(`${EVP}/zones/active`);
  if(!zones||!zones.length){zc.innerHTML='';return}
  zc.innerHTML=`<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--muted)">活跃合规区域</div><div style="display:flex;gap:8px;flex-wrap:wrap">${zones.map(z=>`<div class="chip" style="padding:6px 12px"><b>${escapeHtml(z.name||z.zone_id||'')}</b>${z.standards?` · ${z.standards.length} 标准`:''}</div>`).join('')}</div>`;
}

function evoStL(s){return{discovered:'发现',dispatched:'已派发',in_progress:'进行中',verify_pending:'待验证',verified:'已验证',failed:'失败',closed:'已关闭'}[s]||s}
function evoStBadge(s){const c={discovered:'var(--cyan)',dispatched:'var(--amber)',in_progress:'var(--cyan-s)',verify_pending:'var(--pink)',verified:'var(--lime)',failed:'var(--red)',closed:'var(--dim)'}[s]||'var(--muted)';return `<span style="color:${c};font-weight:600;font-size:12px">${evoStL(s)}</span>`}

async function runEvoAudit(){
  toast('正在运行审查...');
  const r=await api(`${EVP}/audit`,{method:'POST'});
  if(r){toast(`审查完成: ${r.passed||0} 通过, ${r.failed||0} 未通过`);loadEvolution()}else toast('审查失败')
}

// Evolution Cycle Stepper — visual 4-step progress
async function runEvoCycleStepper(){
  const stepper=el('evo-stepper');const log=el('evo-stepper-log');
  stepper.classList.remove('hidden');
  const steps=['audit','dispatch','verify','close'];
  const stepNames=['审查','派发','验证','关闭'];
  // Reset all dots
  steps.forEach(s=>{const d=el('es-'+s);d.className='wf-dot'});
  ['es-c1','es-c2','es-c3'].forEach(id=>{const c=el(id);if(c)c.className='wf-connector'});
  log.innerHTML='';

  for(let i=0;i<steps.length;i++){
    const dotEl=el('es-'+steps[i]);
    dotEl.classList.add('wf-active');
    log.innerHTML+=`<div>⏳ ${stepNames[i]}...</div>`;
    const r=await api(`${EVP}/${steps[i]}`,{method:'POST'});
    dotEl.classList.remove('wf-active');
    if(r){
      dotEl.classList.add('wf-completed');
      const count=r.count||r.passed||r.dispatched||(r.closed||[]).length||0;
      log.innerHTML+=`<div style="color:var(--lime)">✓ ${stepNames[i]}完成 (${count})</div>`;
    }else{
      dotEl.classList.add('wf-failed');
      log.innerHTML+=`<div style="color:var(--red)">✗ ${stepNames[i]}失败</div>`;
      break;
    }
    // Mark connector as done
    if(i<3){const c=el('es-c'+(i+1));if(c)c.classList.add('wf-done')}
  }
  toast('演进周期完成');
  loadEvolution();
}

// Keep backward compat
async function runEvoCycle(){runEvoCycleStepper()}

// ── LLM Config ──
async function loadLLMStatus(){hideViewLoading('view-llm');
  const st=await api(`${A}/llm/status`);
  const prov=await api(`${A}/llm/provider`);
  const card=el('llm-status-card');
  if(!st||!prov){card.innerHTML='<p style="color:var(--pink)">⚠️ 无法获取 LLM 状态，请确认后端已启动</p>';return}
  const keyStatus=prov.has_api_key?'<span style="color:var(--lime)">✅ 已配置</span>':'<span style="color:var(--pink)">❌ 未配置</span>';
  card.innerHTML=`
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px">
      <div class="stat-card"><div class="label">提供商</div><div class="value">${escapeHtml(prov.provider)}</div></div>
      <div class="stat-card"><div class="label">模型</div><div class="value" style="font-size:14px">${escapeHtml(prov.model)}</div></div>
      <div class="stat-card"><div class="label">API Key</div><div class="value" style="font-size:14px">${keyStatus}</div><div class="sub">${prov.api_key_preview||''}</div></div>
      <div class="stat-card"><div class="label">Base URL</div><div class="value" style="font-size:11px;word-break:break-all">${escapeHtml(prov.base_url)}</div></div>
      <div class="stat-card"><div class="label">总调用</div><div class="value">${st.total_calls??0}</div></div>
      <div class="stat-card"><div class="label">总 Tokens</div><div class="value">${(st.total_tokens||0).toLocaleString()}</div></div>
      <div class="stat-card"><div class="label">活跃会话</div><div class="value">${st.active_sessions??0}</div></div>
      <div class="stat-card"><div class="label">错误数</div><div class="value" style="color:${(st.errors||0)>0?'var(--pink)':'var(--lime)'}">${st.errors??0}</div></div>
    </div>`;
  // Fill form with current values
  el('llm-provider').value=prov.provider||'deepseek';
  el('llm-model').value=prov.model||'';
  el('llm-url').value=prov.base_url||'';
  el('llm-tokens').value=prov.max_tokens||4096;
  el('llm-temp').value=prov.temperature||0.7;
  // Load sessions
  const sessions=await api(`${A}/llm/sessions`);
  const sc=el('llm-sessions');
  if(!sessions||!sessions.length){sc.innerHTML='<p style="color:var(--dim)">暂无活跃会话</p>';return}
  sc.innerHTML='<table class="tbl"><thead><tr><th>会话 ID</th><th>Agent</th><th>轮次</th><th>消息数</th><th>Tokens</th><th>创建时间</th></tr></thead><tbody>'+sessions.map(s=>`<tr><td>${escapeHtml(s.session_id)}</td><td>${escapeHtml(s.agent_id||'-')}</td><td>${s.turn_count}</td><td>${s.message_count}</td><td>${(s.usage?.total_tokens||0).toLocaleString()}</td><td>${s.created_at?.split('T')[0]||'-'}</td></tr>`).join('')+'</tbody></table>';
}
async function saveLLMConfig(){
  const body={provider:el('llm-provider').value,model:el('llm-model').value,api_key:el('llm-key').value,api_base_url:el('llm-url').value,max_tokens:parseInt(el('llm-tokens').value)||4096,temperature:parseFloat(el('llm-temp').value)||0.7};
  const r=await api(`${A}/llm/provider`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r){toast('LLM 配置已保存');el('llm-key').value='';loadLLMStatus()}else toast('保存失败')
}
async function testLLM(){
  const rc=el('llm-test-result');rc.classList.remove('hidden');
  el('llm-test-content').innerHTML='<p style="color:var(--dim)">正在测试连接...</p>';
  const r=await api(`${A}/llm/test`,{method:'POST'});
  if(!r){el('llm-test-content').innerHTML='<p style="color:var(--pink)">请求失败，请检查后端</p>';return}
  if(r.success){
    el('llm-test-content').innerHTML=`<div style="color:var(--lime);margin-bottom:8px">✅ 连接成功！</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><div><b>模型:</b> ${escapeHtml(r.model)}</div><div><b>提供商:</b> ${escapeHtml(r.provider)}</div><div><b>延迟:</b> ${r.latency_ms?.toFixed(0)||'?'}ms</div></div><div style="margin-top:12px;padding:12px;background:rgba(232,240,250,0.7);border-radius:0;font-size:13px;color:var(--text)">${escapeHtml(r.response)}</div>`;
  } else {
    el('llm-test-content').innerHTML=`<div style="color:var(--pink);margin-bottom:8px">❌ 连接失败</div><div style="padding:12px;background:rgba(224,27,36,0.06);border-radius:0;font-size:12px;color:var(--red);word-break:break-all">${escapeHtml(r.error||'未知错误')}</div><div style="margin-top:12px;padding:12px;background:rgba(232,240,250,0.7);border-radius:0;font-size:13px;color:var(--text)">${escapeHtml(r.response)}</div><div style="margin-top:12px;color:var(--muted);font-size:12px">💡 提示: 请确认 API Key 已正确填入，或检查本地模型服务是否运行中</div>`;
  }
}

// ── Models ──
let _editModelId='';
async function loadModels(){const d=await api(`${A}/teams/${tid}/models`);hideViewLoading('view-models');const tb=el('models-tb');if(!d||!d.length){tb.innerHTML='<tr><td colspan="7" style="color:var(--dim)">暂无模型 — 点击右上角「+ 添加模型」</td></tr>';return}tb.innerHTML=d.map(m=>{const mid=m.model_id;return `<tr><td><b>${escapeHtml(mid)}</b></td><td>${escapeHtml(m.name)}</td><td>${escapeHtml(m.provider)}</td><td>${(m.max_tokens||0).toLocaleString()}</td><td>${m.temperature??0.7}</td><td>${m.is_default?'<span style="color:var(--lime)">✓ 默认</span>':`<button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="setModelDefault('${mid}')">设为默认</button>`}</td><td style="display:flex;gap:6px"><button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="openEditModel('${mid}')">编辑</button><button class="btn btn-danger btn-sm" onclick="delModel('${mid}')">删除</button></td></tr>`}).join('')}
async function delModel(mid){if(!confirm('删除此模型？'))return;await csrfFetch(`${A}/teams/${tid}/models/${mid}`,{method:'DELETE'});toast('已删除');loadModels()}
async function setModelDefault(mid){
  const r=await api(`${A}/teams/${tid}/models/${mid}/default`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});
  if(r){toast(`模型 ${mid} 已设为默认，所有智能体已同步`);loadModels();loadSbAgents();if(aid)loadAgent()}else toast('设置失败')
}
async function openEditModel(mid){
  _editModelId=mid;
  const models=await api(`${A}/teams/${tid}/models`);
  const m=(models||[]).find(x=>x.model_id===mid);if(!m){toast('模型未找到');return}
  el('em-prov').value=m.provider||'deepseek';
  el('em-name').value=m.name||'';
  el('em-tok').value=m.max_tokens||8192;
  el('em-temp').value=m.temperature??0.7;
  // Show placeholder if key is stored, clear field otherwise
  el('em-key').value='';
  el('em-key').placeholder=m.has_api_key?'已配置 (留空则沿用已保存的密钥)':'输入 API Key';
  el('em-url').value=m.api_base_url||'';
  el('em-def').value=m.is_default?'true':'false';
  el('em-title').textContent=`✏️ 编辑模型 — ${mid}`;
  el('em-test-result').classList.add('hidden');
  updateEmUrlHint();
  openModal('modal-edit-model');
}
const _providerDefaultUrls={deepseek:'https://api.deepseek.com',openai:'https://api.openai.com/v1',anthropic:'https://api.anthropic.com/v1',github:'https://models.inference.ai.azure.com',qwen:'https://dashscope.aliyuncs.com/compatible-mode/v1',openrouter:'https://openrouter.ai/api/v1',local:'http://127.0.0.1:11434/v1'};
function updateEmUrlHint(){
  const prov=el('em-prov').value;
  const defaultUrl=_providerDefaultUrls[prov]||'';
  const urlInput=el('em-url');
  urlInput.placeholder=defaultUrl||'输入自定义 Base URL';
  const hint=el('em-url-hint');
  if(hint){
    if(urlInput.value){hint.textContent=`自定义 URL（默认: ${defaultUrl}）`}
    else{hint.textContent=`当前使用默认: ${defaultUrl}`}
  }
}
async function submitEditModel(){
  if(!_editModelId)return;
  const body={provider:el('em-prov').value,name:el('em-name').value.trim(),max_tokens:parseInt(el('em-tok').value)||8192,temperature:parseFloat(el('em-temp').value)||0.7,is_default:el('em-def').value==='true',api_key:el('em-key').value,api_base_url:el('em-url').value};
  if(!body.name){toast('模型名称不能为空');return}
  const r=await api(`${A}/teams/${tid}/models/${_editModelId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r){toast('模型已更新');closeModal('modal-edit-model');loadModels();if(body.is_default){loadSbAgents();if(aid)loadAgent()}}else toast('更新失败')
}
async function testModelInEdit(){
  const rb=el('em-test-result');rb.classList.remove('hidden');
  rb.style.background='rgba(232,240,250,0.7)';rb.style.color='var(--muted)';
  rb.innerHTML='⏳ 正在测试连接...';
  const btn=el('em-test-btn');btn.disabled=true;
  const body={provider:el('em-prov').value,name:el('em-name').value.trim(),api_key:el('em-key').value,api_base_url:el('em-url').value,max_tokens:parseInt(el('em-tok').value)||8192,temperature:parseFloat(el('em-temp').value)||0.7,model_id:_editModelId};
  const r=await api(`${A}/llm/test-model`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  btn.disabled=false;
  if(!r){rb.style.background='rgba(224,27,36,0.06)';rb.style.color='var(--red)';rb.innerHTML='❌ 请求失败，请检查后端是否运行';return}
  if(r.success){
    rb.style.background='rgba(38,162,105,0.08)';rb.style.color='var(--lime)';
    rb.innerHTML=`✅ 连接成功 — 模型: ${escapeHtml(r.model)} · 延迟: ${r.latency_ms?.toFixed(0)||'?'}ms<div style="margin-top:8px;padding:10px;background:rgba(232,240,250,0.6);border-radius:6px;color:var(--text);font-size:12px">${escapeHtml(r.response)}</div>`;
    // Auto-save after successful test
    if(_editModelId){
      const sb={provider:el('em-prov').value,name:el('em-name').value.trim(),max_tokens:parseInt(el('em-tok').value)||8192,temperature:parseFloat(el('em-temp').value)||0.7,is_default:el('em-def').value==='true',api_key:body.api_key,api_base_url:el('em-url').value};
      const sr=await api(`${A}/teams/${tid}/models/${_editModelId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(sb)});
      if(sr){rb.innerHTML+='<div style="margin-top:8px;color:var(--lime);font-size:12px">💾 配置已自动保存</div>';loadModels();if(sb.is_default){loadSbAgents();if(aid)loadAgent()}}
    }
  } else {
    rb.style.background='rgba(224,27,36,0.06)';rb.style.color='var(--red)';
    rb.innerHTML=`❌ 连接失败<div style="margin-top:6px;font-size:12px;word-break:break-all">${escapeHtml(r.error||'未知错误')}</div><div style="margin-top:8px;color:var(--muted);font-size:11px">💡 请确认 API Key 正确，或检查本地模型服务是否运行</div>`;
  }
}

// ── Tools (Clawith-style) ──
let _ctEventSource=null;
let _ctSessionId='';
let _ctElapsedTimer=null;

function openClaudeTerm(sessionId){
  _ctSessionId=sessionId;
  const overlay=el('claude-term-overlay');
  const body=el('ct-body');
  const statusEl=el('ct-status');
  const linesEl=el('ct-lines');
  const sessionEl=el('ct-session-id');
  const stopBtn=el('ct-stop');
  body.innerHTML='';
  sessionEl.textContent=sessionId;
  statusEl.textContent='● running';
  statusEl.style.color='oklch(0.52 0.04 160)';
  stopBtn.style.display='';
  linesEl.textContent='0 lines';
  overlay.classList.add('open');
  let lineCount=0;
  const startTime=Date.now();

  // Elapsed timer
  clearInterval(_ctElapsedTimer);
  _ctElapsedTimer=setInterval(()=>{
    const s=Math.floor((Date.now()-startTime)/1000);
    el('ct-elapsed').textContent=`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
  },1000);

  // Connect SSE
  if(_ctEventSource){_ctEventSource.close();_ctEventSource=null}
  const es=new EventSource(`${A}/claude-sessions/${sessionId}/stream`);
  _ctEventSource=es;

  es.onmessage=(e)=>{
    lineCount++;
    const line=document.createElement('div');
    line.className='ct-line';
    const text=e.data;
    if(text.startsWith('❌'))line.classList.add('ct-err');
    else if(text.startsWith('✅')||text.includes('passed'))line.classList.add('ct-success');
    line.textContent=text;
    body.appendChild(line);
    body.scrollTop=body.scrollHeight;
    linesEl.textContent=`${lineCount} lines`;
  };

  es.addEventListener('done',(e)=>{
    try{
      const d=JSON.parse(e.data);
      statusEl.textContent=d.status==='completed'?'✓ completed':'✗ '+d.status;
      statusEl.style.color=d.status==='completed'?'oklch(0.52 0.04 160)':'oklch(0.48 0.07 22)';
      stopBtn.style.display='none';
      clearInterval(_ctElapsedTimer);
      const endLine=document.createElement('div');
      endLine.className='ct-line '+(d.status==='completed'?'ct-success':'ct-err');
      endLine.textContent=`\n[${d.status}] exit code: ${d.exit_code}`;
      body.appendChild(endLine);
      body.scrollTop=body.scrollHeight;
    }catch(ex){}
    es.close();
    _ctEventSource=null;
  });

  es.onerror=()=>{
    statusEl.textContent='⚠ connection lost';
    statusEl.style.color='oklch(0.56 0.05 70)';
    clearInterval(_ctElapsedTimer);
    es.close();
    _ctEventSource=null;
  };
}

function closeClaudeTerm(){
  el('claude-term-overlay').classList.remove('open');
  if(_ctEventSource){_ctEventSource.close();_ctEventSource=null}
  clearInterval(_ctElapsedTimer);
}

async function stopClaudeSession(){
  if(!_ctSessionId)return;
  await csrfFetch(`${A}/claude-sessions/${_ctSessionId}/stop`,{method:'POST'});
  toast('已停止');
}

// ══════════════════════════════════
//  AGENT DETAIL (Clawith tabs)
// ══════════════════════════════════

// ═══ Phase 3: Performance Optimization ═══

// Debounced visibility change handler to prevent rapid re-fetches
let _visibilityDebounceTimer = null;
document.addEventListener('visibilitychange',()=>{
  if(document.hidden)return;
  clearTimeout(_visibilityDebounceTimer);
  _visibilityDebounceTimer=setTimeout(()=>{
    const v=document.querySelector('.main-inner:not(.hidden)');
    if(v&&v.id==='view-overview')loadOverview();
  },300);
});

// Debounce utility
function debounce(fn,ms=300){let t;return(...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms)}}

// SSE cleanup on page unload
window.addEventListener('beforeunload',()=>{
  if(_ovTimer){clearInterval(_ovTimer);_ovTimer=null}
});

// ═══ Phase 4: Interaction Experience ═══



// Keyboard navigation
document.addEventListener('keydown',e=>{
  // Escape closes modals
  if(e.key==='Escape'){
    document.querySelectorAll('.modal-overlay.open').forEach(m=>m.classList.remove('open'));
    document.querySelectorAll('.claude-term-overlay.open').forEach(m=>m.classList.remove('open'));
  }
  // Ctrl+K: focus search (if exists)
  if((e.ctrlKey||e.metaKey)&&e.key==='k'){
    const s=document.querySelector('.main-inner:not(.hidden) input[type="search"],input.fi[placeholder*="搜索"]');
    if(s){e.preventDefault();s.focus()}
  }
});

// Mobile sidebar toggle
(function(){
  const sidebar=document.querySelector('.sidebar');
  if(!sidebar)return;
  // ARIA roles
  sidebar.setAttribute('role','navigation');
  sidebar.setAttribute('aria-label','Agent 导航侧栏');
  sidebar.querySelectorAll('.sb-nav').forEach(n=>n.setAttribute('role','list'));
  sidebar.querySelectorAll('.sb-nav a').forEach(a=>a.setAttribute('role','listitem'));
  // Collapse memory
  const collapsed=localStorage.getItem('atc-sidebar-collapsed')==='1';
  if(collapsed)sidebar.classList.add('collapsed');
  // Add hamburger button for mobile
  const topbar=document.querySelector('.topbar-left');
  if(topbar){
    const btn=document.createElement('button');
    btn.className='btn btn-ghost sidebar-toggle';
    btn.innerHTML='☰';
    btn.setAttribute('aria-label','打开导航');
    btn.style.cssText='display:none;font-size:18px;padding:4px 8px';
    btn.onclick=()=>sidebar.classList.toggle('open');
    topbar.insertBefore(btn,topbar.firstChild);
    // Show on mobile
    const mq=window.matchMedia('(max-width:768px)');
    function check(e){btn.style.display=e.matches?'inline-flex':'none';if(!e.matches)sidebar.classList.remove('open')}
    mq.addEventListener('change',check);
    check(mq);
    // Desktop collapse toggle
    const colBtn=document.createElement('button');
    colBtn.className='btn btn-ghost';
    colBtn.style.cssText='position:absolute;bottom:8px;right:8px;font-size:14px;padding:4px 8px;opacity:0.5';
    colBtn.innerHTML='«';colBtn.title='折叠侧栏';
    colBtn.setAttribute('aria-label','折叠侧栏');
    colBtn.onclick=()=>{
      sidebar.classList.toggle('collapsed');
      const c=sidebar.classList.contains('collapsed');
      localStorage.setItem('atc-sidebar-collapsed',c?'1':'0');
      colBtn.innerHTML=c?'»':'«';
      colBtn.title=c?'展开侧栏':'折叠侧栏';
    };
    if(collapsed)colBtn.innerHTML='»';
    sidebar.style.position='relative';
    sidebar.appendChild(colBtn);
  }
  // Close sidebar on nav click (mobile)
  sidebar.querySelectorAll('.sb-nav a,.sb-agent').forEach(a=>{
    a.addEventListener('click',()=>{if(window.innerWidth<=768)sidebar.classList.remove('open')});
  });
})();

// ═══ Phase 5: Feature Enhancements ═══

// 5a. Search/filter for tools
(function(){
  const box=document.getElementById('tools-cards');
  if(!box)return;
  const parent=box.parentElement;
  const search=document.createElement('input');
  search.type='search';
  search.className='fi';
  search.placeholder='搜索工具名称或描述...';
  search.style.cssText='margin-bottom:12px;max-width:320px';
  parent.insertBefore(search,box);
  search.addEventListener('input',debounce(e=>{
    const q=e.target.value.toLowerCase();
    box.querySelectorAll('[data-tool-name]').forEach(card=>{
      const name=(card.dataset.toolName||'').toLowerCase();
      const desc=(card.textContent||'').toLowerCase();
      card.style.display=(name.includes(q)||desc.includes(q))?'':'none';
    });
  },200));
})();

// 5b. Team config export/import
async function exportTeamConfig(){
  if(!tid){toast('请先选择团队');return}
  const[info,models,tools,skills]=await Promise.all([
    api(`${A}/teams/${tid}`),
    api(`${A}/teams/${tid}/models`),
    api(`${A}/teams/${tid}/tools`),
    api(`${A}/teams/${tid}/skills`)
  ]);
  const cfg={team:info,models,tools,skills,exported_at:new Date().toISOString()};
  const blob=new Blob([JSON.stringify(cfg,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download=`team-${tid}-config.json`;
  document.body.appendChild(a);a.click();
  document.body.removeChild(a);URL.revokeObjectURL(url);
  toast('配置已导出');
}

async function importTeamConfig(){
  const input=document.createElement('input');
  input.type='file';input.accept='.json';
  input.onchange=async e=>{
    const file=e.target.files[0];if(!file)return;
    try{
      const text=await file.text();
      const cfg=JSON.parse(text);
      if(!cfg.team){toast('无效的配置文件');return}
      // Import models
      if(cfg.models&&Array.isArray(cfg.models)){
        for(const m of cfg.models){
          await api(`${A}/teams/${tid}/models`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m)});
        }
      }
      toast(`已导入配置 (${cfg.models?.length||0} 模型)`);
      loadView();
    }catch(err){toast('导入失败: '+err.message)}
  };
  input.click();
}

// 5c. Batch operations for tools
async function batchEnableTools(enable){
  const box=document.getElementById('tools-cards');
  const checks=box.querySelectorAll('input[type="checkbox"]');
  let count=0;
  for(const chk of checks){
    if(chk.checked!==enable){
      const card=chk.closest('[data-tool-name]');
      if(card&&card.style.display!=='none'){
        chk.checked=enable;
        chk.dispatchEvent(new Event('change'));
        count++;
      }
    }
  }
  if(count===0)toast('无需变更');
}

// 5d. Real-time status polling for agent detail
let _agentPollTimer=null;
function startAgentPoll(agentId){
  stopAgentPoll();
  if(!agentId)return;
  _agentPollTimer=setInterval(async()=>{
    if(document.hidden)return;
    const st=await api(`${A}/teams/${tid}/agents/${agentId}/status`);
    if(st){
      const dotEl=document.querySelector(`.sb-agent[data-aid="${agentId}"] .dot`);
      if(dotEl)dotEl.className='dot '+(st.status||'idle');
    }
  },10000);
}
function stopAgentPoll(){if(_agentPollTimer){clearInterval(_agentPollTimer);_agentPollTimer=null}}

// Add export/import buttons to topbar
(function(){
  const topRight=document.querySelector('.topbar-right');
  if(!topRight)return;
  const expBtn=document.createElement('button');
  expBtn.className='btn btn-sm';
  expBtn.innerHTML='📤 导出';
  expBtn.onclick=exportTeamConfig;
  const impBtn=document.createElement('button');
  impBtn.className='btn btn-sm';
  impBtn.innerHTML='📥 导入';
  impBtn.onclick=importTeamConfig;
  const createBtn = topRight.querySelector('button[onclick*="create-team"]');
  topRight.insertBefore(expBtn, createBtn);
  topRight.insertBefore(impBtn, createBtn);
})();

// ── TTS Configuration ──
const TTSAPI='/api/v1';
async function loadTTSConfig(){
  const cfg=await api(`${TTSAPI}/tts/config`);
  if(!cfg)return;
  el('tts-engine').value=cfg.engine||'gpt-sovits';
  el('tts-api-url').value=cfg.api_url||'http://127.0.0.1:9880';
  el('tts-ref-audio').value=cfg.ref_audio_path||'';
  el('tts-prompt-text').value=cfg.prompt_text||'';
  el('tts-lang').value=cfg.text_lang||'zh';
  el('tts-speed').value=cfg.speed_factor||1.0;
  // Check service status
  checkTTSStatus();
}
async function checkTTSStatus(){
  const badge=el('tts-status-badge');
  try{
    const r=await fetch(`${TTSAPI}/tts/status`);
    const d=await r.json();
    if(d.online){badge.textContent='🟢 在线';badge.style.background='rgba(152,245,167,0.15)';badge.style.color='var(--lime)'}
    else{badge.textContent='🔴 离线';badge.style.background='rgba(224,27,36,0.1)';badge.style.color='var(--pink)'}
  }catch(e){badge.textContent='🔴 离线';badge.style.background='rgba(224,27,36,0.1)';badge.style.color='var(--pink)'}
}
async function saveTTSConfig(){
  const body={engine:el('tts-engine').value,api_url:el('tts-api-url').value,ref_audio_path:el('tts-ref-audio').value,prompt_text:el('tts-prompt-text').value,text_lang:el('tts-lang').value,speed_factor:parseFloat(el('tts-speed').value)||1.0};
  const r=await api(`${TTSAPI}/tts/config`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r){toast('TTS 配置已保存');checkTTSStatus()}else toast('保存失败','error')
}
async function testTTSConnection(){
  const res=el('tts-test-result');
  res.textContent='正在测试 TTS 服务...';res.style.color='var(--dim)';
  try{
    const r=await fetch(`${TTSAPI}/tts/status`);
    const d=await r.json();
    if(d.online){res.innerHTML='<span style="color:var(--lime)">✅ GPT-SoVITS 服务在线，可正常使用</span>';checkTTSStatus()}
    else{res.innerHTML='<span style="color:var(--pink)">❌ 服务离线 — 请点击「▶ 启动服务」</span>';checkTTSStatus()}
  }catch(e){res.innerHTML='<span style="color:var(--pink)">❌ 无法连接: '+escapeHtml(e.message)+'</span>'}
}
async function startTTSService(){
  const res=el('tts-test-result');
  res.textContent='正在启动 GPT-SoVITS 服务...';res.style.color='var(--dim)';
  try{
    const r=await api(`${TTSAPI}/tts/start`,{method:'POST'});
    if(r&&r.status==='started'){res.innerHTML='<span style="color:var(--lime)">✅ GPT-SoVITS 服务已启动 (PID: '+r.pid+')</span>';setTimeout(checkTTSStatus,3000)}
    else if(r&&r.status==='already_running'){res.innerHTML='<span style="color:var(--lime)">ℹ️ 服务已在运行中 (PID: '+r.pid+')</span>';checkTTSStatus()}
    else{res.innerHTML='<span style="color:var(--pink)">❌ 启动失败: '+(r?.error||'未知错误')+'</span>'}
  }catch(e){res.innerHTML='<span style="color:var(--pink)">❌ 启动请求失败: '+escapeHtml(e.message)+'</span>'}
}


// ── Initialize on page load ──
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootAgentTeamConfigPage);
} else {
  bootAgentTeamConfigPage();
}
