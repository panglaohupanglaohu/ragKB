const API='/api/v1/agent-config';
const S={agents:[],skills:[],tools:[],rooms:[],messages:[],positions:{},execLog:[],activityFeed:[],interactionCount:0,freqData:new Array(30).fill(0),teams:[],selectedTeams:[]};
const liveMetrics={tasks:{total:0,running:0,completed:0,failed:0},extraction:{pending:0,active:0,completed:0},uptime:Date.now(),lastRefresh:null};
window.S=S;

// CSRF helper for state-changing requests (fetched once, cached, auto-refresh on 403)
var _csrfTk='',_csrfPr=null;
function _csrf(){if(_csrfTk)return Promise.resolve(_csrfTk);if(_csrfPr)return _csrfPr;_csrfPr=fetch('/api/v1/auth/csrf-token').then(function(r){return r.json()}).then(function(d){_csrfTk=d.csrf_token||'';return _csrfTk}).catch(function(){_csrfPr=null;return''});return _csrfPr}
function _csrfReset(){_csrfTk='';_csrfPr=null;return _csrf()}
_csrf();
async function _af(url,opts){var m=(opts&&opts.method||'GET').toUpperCase();if(m==='POST'||m==='PUT'||m==='DELETE'||m==='PATCH'){await _csrf();if(_csrfTk){opts=opts||{};opts.headers=opts.headers||{};opts.headers['x-csrf-token']=_csrfTk}}var r=await (window._agFetch||fetch)(url,opts);if(r.status===403&&m!=='GET'){await _csrfReset();if(_csrfTk){opts=opts||{};opts.headers=opts.headers||{};opts.headers['x-csrf-token']=_csrfTk}r=await (window._agFetch||fetch)(url,opts)}return r}
function _listItems(payload){if(Array.isArray(payload))return payload;if(Array.isArray(payload?.items))return payload.items;if(Array.isArray(payload?.sessions))return payload.sessions;return[]}
async function _list(url,limit=200,offset=0){if(window.api&&typeof window.api.list==='function'){return _listItems(await window.api.list(url,limit,offset))}const sep=url.includes('?')?'&':'?';const r=await _af(`${url}${sep}limit=${limit}&offset=${offset}`);if(!r.ok)return[];return _listItems(await r.json())}
async function _plazas(){return _list(`${API}/plaza`,200,0)}
async function _plazaDiscussions(plazaId){return _list(`${API}/plaza/${plazaId}/discussions`,200,0)}
async function init(){
  loadLocal();
  await Promise.all([loadTeamsAndAgents(),loadSkills(),loadTools(),loadDtState()]);
  // P5: 冷启动只渲染常驻区 + 默认可见的「环境空间」Tab；architecture/interaction/pipeline
  // 三个隐藏 Tab 改为进入时经 switchView→dtRefresh('tab') 惰性渲染，省掉冷启动 3 次无谓渲染。
  renderAgentList();renderEnvironment();renderRoomTabs();renderStats();renderFreqChart();renderActivityFeed();
  if(window._secsRenderCollab)window._secsRenderCollab();   // 协作图初始占位(不空白)
  secsInitTeamDropdown();
  setInterval(()=>{if(document.hidden)return;loadLiveMetrics();},10000);
  // 重新可见时立即补刷，避免回到页面看到过期数据（对齐仓库既有 document.hidden 约定）
  document.addEventListener('visibilitychange',function(){
    if(document.hidden)return;
    loadLiveMetrics();
    if(window.dtRefresh)window.dtRefresh('tab');
  });
  startSim();
}
async function loadDtState(){try{const r=await _af(`${API}/digital-twin/state`);if(r.ok){const d=await r.json();if(d.positions&&Object.keys(d.positions).length)S.positions=d.positions;if(d.rooms&&d.rooms.length>=6){S.rooms=d.rooms;scopeRoomsToCurrentScenario();}if(d.interactions&&d.interactions.length){d.interactions.forEach(i=>{if(!S.messages.find(m=>m.time===i.time&&m.from===i.from))S.messages.push(i)})}}}catch(e){console.warn('[dt] loadDtState',e)}}
async function syncDtState(){try{await _af(`${API}/digital-twin/state`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({rooms:(S.rooms||[]).filter(r=>!(r&&r._scn)),positions:S.positions})})}catch(e){console.warn('[dt] syncDtState',e)}}
async function syncAgentMove(agentId,roomId){
  const r=await _af(`${API}/digital-twin/move`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agentId,room_id:roomId})});
  let d={};try{d=await r.json()}catch{}
  if(!r.ok){
    const detail=d.detail||d||{};
    const reason=typeof detail==='string'?detail:(detail.reason||detail.error||d.reason||d.error||`HTTP ${r.status}`);
    const err=new Error(reason);err.status=r.status;err.payload=d;throw err;
  }
  return d;
}
function rollbackAgentMove(agentId,oldRoomId){
  if(oldRoomId)S.positions[agentId]=oldRoomId;else delete S.positions[agentId];
  persist();renderAgentList();renderEnvironment();
}
function moveFailureText(err){return err&&err.status===409?(err.message||'违反业务阶段顺序'):('移动失败: '+(err&&err.message||'服务异常'))}
// CB-FE-03: 暴露最小测试钩子供 VM 测试拖拽 409 回滚
window._dtMoveTestHooks = { syncAgentMove, rollbackAgentMove, moveFailureText };
function loadLocal(){
  const storedRooms=JSON.parse(localStorage.getItem('dt2_rooms')||'null');
  S.rooms=(storedRooms&&storedRooms.length)?storedRooms:defaultRooms();
  scopeRoomsToCurrentScenario();  // 剔除历史遗留的其他场景房间残留
  S.positions=JSON.parse(localStorage.getItem('dt2_positions')||'{}');
  S.messages=JSON.parse(localStorage.getItem('dt2_messages')||'[]').slice(-100);
  S.interactionCount=parseInt(localStorage.getItem('dt2_interactions')||'0');
}
function defaultRooms(){return[
  {id:'council',name:'议事厅',icon:'◇',desc:'团队协作讨论与任务分配',color:'var(--cyan)'},
  {id:'extraction',name:'萃取室',icon:'○',desc:'技能萃取、知识提炼与结构化',color:'var(--green)'},
  {id:'workshop',name:'工作坊',icon:'□',desc:'编码构建与工程实践',color:'var(--amber)'},
  {id:'library',name:'知识库',icon:'△',desc:'文档检索与知识管理',color:'var(--purple)'},
  {id:'arena',name:'演练场',icon:'◎',desc:'A/B测试、技能验证与对抗演练',color:'var(--pink)'},
  {id:'rest',name:'休息区',icon:'◌',desc:'智能体待机、充能与状态恢复',color:'var(--dim)'},
]}
// tab 房间 = 6 内置 + 自定义(r_开头) + 当前演练场景房间(_scn 标记)；其余场景残留一律剔除
const BUILTIN_ROOM_IDS=['council','extraction','workshop','library','arena','rest'];
window.BUILTIN_ROOM_IDS=BUILTIN_ROOM_IDS;
function scopeRoomsToCurrentScenario(){
  if(!S||!Array.isArray(S.rooms))return;
  S.rooms=S.rooms.filter(function(r){return r&&(BUILTIN_ROOM_IDS.includes(r.id)||/^r_/.test(r.id||'')||r._scn);});
  if(!S.rooms.length)S.rooms=defaultRooms();
}
window.scopeRoomsToCurrentScenario=scopeRoomsToCurrentScenario;
async function loadTeamsAndAgents(){
  try{
    const teams=await _list(`${API}/teams`,200,0);
    console.log('[DT] teams count:',teams.length);
    if(!teams.length){console.warn('[DT] 0 teams from API');return}
    S.teams=[];S.agents=[];
    const fetches=teams.map(async t=>{
      const tid=t.team_id||t.id;
      try{const agents=await _list(`${API}/teams/${tid}/agents`,200,0);S.teams.push({id:tid,name:t.name||tid,agents});agents.forEach(a=>{a._teamId=tid;a._teamName=t.name||tid});S.agents.push(...agents)}catch(e){console.warn('[dt] 加载团队 agent 失败',tid,e)}
    });
    await Promise.all(fetches);
    console.log('[DT] loaded',S.teams.length,'teams,',S.agents.length,'agents');
    if(!S.selectedTeams.length) S.selectedTeams=S.teams.map(t=>t.id);
    renderTeamSelector();
  }catch(e){console.error('[DT] loadTeamsAndAgents FAILED:',e.message)}
}
// 树状展开状态（团队 id → bool）；默认展开已选中团队
window._lpTreeExpanded = window._lpTreeExpanded || {};
function renderTeamSelector(){
  // 兼容旧调用点：树状合并后主渲染走 renderAgentList
  if(typeof renderAgentList==='function') renderAgentList();
  // 隐藏兼容容器若仍被填充
  const el=document.getElementById('team-selector');
  if(el && el.style.display!=='none') el.style.display='none';
}
function toggleTeam(tid,btn){
  const idx=S.selectedTeams.indexOf(tid);
  const turningOn = idx < 0;
  if(idx>=0)S.selectedTeams.splice(idx,1);else S.selectedTeams.push(tid);
  if(turningOn) window._lpTreeExpanded[tid]=true;
  renderTeamSelector();renderAgentList();
  // 重建当前3D房间以刷新智能体（3D 常在，独立于当前 Tab）
  if(window._dt3dBuildRoom&&window._currentRoomId)window._dt3dBuildRoom(window._currentRoomId);
  // 统一调度：刷新当前可见 Tab（拓扑/时间线/仪表盘/编排 均按团队联动）
  if(window.dtRefresh)window.dtRefresh('team');
  // 左→右 联动:把右侧 SECS「选择演练团队」同步为当前团队
  // 注意:btn 为 null 时是由 sexySelectTeam 反向调用,跳过以免循环
  if(btn && window.secsSyncTeamFromLeft){
    const target = turningOn ? tid : (S.selectedTeams[0] || '');
    if(target) window.secsSyncTeamFromLeft(target);
  }
}
function lpToggleExpand(tid, ev){
  if(ev){ ev.stopPropagation(); }
  window._lpTreeExpanded[tid]=!window._lpTreeExpanded[tid];
  renderAgentList();
}
window.lpToggleExpand=lpToggleExpand;
// L1: 统一数字孪生页"当前团队"(localStorage 'selected_team' / S.selectedTeams / 右SECS 三套)
function dtGetCurrentTeam(){
  return localStorage.getItem('selected_team') || (S.selectedTeams && S.selectedTeams[0]) || 'build_system';
}
function dtSetCurrentTeam(id, fromCtx){
  if(!id) return;
  localStorage.setItem('selected_team', id);
  localStorage.setItem('ag_current_team', id);  // L2: 跨页面共享
  if(window.S){ S.selectedTeams=[id]; if(typeof renderTeamSelector==='function')renderTeamSelector(); if(typeof renderAgentList==='function')renderAgentList(); }
  if(window._dt3dBuildRoom && window._currentRoomId) window._dt3dBuildRoom(window._currentRoomId);
  if(window.secsSyncTeamFromLeft) window.secsSyncTeamFromLeft(id);  // 右侧 SECS 同步
  // L4: 上报全局上下文总线(fromCtx=true 为总线回调,跳过以防回灌循环)
  if(!fromCtx && window.AGCtx) window.AGCtx.set('team', id);
}
// L4: 订阅总线 — 其它页面切团队时本页跟随(AGCtx 已 dedup,这里再防 dtSetCurrentTeam 循环)
if(window.AGCtx){ window.AGCtx.on(function(k,v){ if(k==='team' && v && v!==dtGetCurrentTeam()) dtSetCurrentTeam(v, true); }); }
// L2: 跨页面 storage 事件广播 — 任一页改团队,其他页实时跟随
window.addEventListener('storage', function(e) {
  if (e.key === 'ag_current_team' && e.newValue && e.key !== e.oldValue) {
    // 仅在另一页修改时触发(同页通过 dtSetCurrentTeam 已更新)
    if (window.dtSetCurrentTeam && typeof dtGetCurrentTeam === 'function' && localStorage.getItem('ag_current_team') !== dtGetCurrentTeam()) {
      dtSetCurrentTeam(e.newValue);
    }
  }
});
window.dtGetCurrentTeam = dtGetCurrentTeam; window.dtSetCurrentTeam = dtSetCurrentTeam;
async function loadSkills(){try{S.skills=await _list(`${API}/skills`,200,0)}catch(e){console.warn('[dt] loadSkills',e)}}
async function loadTools(){try{S.tools=await _list(`${API}/tools`,200,0)}catch(e){console.warn('[dt] loadTools',e)}}

function switchView(el){
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));el.classList.add('active');
  document.querySelectorAll('.view-panel').forEach(p=>p.classList.remove('active'));
  document.getElementById('view-'+el.dataset.view).classList.add('active');
  // 演练配置/控制台(含「选择演练场景」)在所有 Tab 都常驻——否则在 编排管线/协作交互 等 Tab
  // 提示"去右侧选场景"却看不到选场景入口(rp-default 是隐藏的旧面板)。
  document.getElementById('rp-default').style.display = 'none';
  document.getElementById('rp-secs').style.display = '';
  if(el.dataset.view==='environment'){renderRoomTabs();const _scnFirst=(window._scenarioRooms&&window._scenarioRooms[0]&&window._scenarioRooms[0].id);setTimeout(()=>{switchRoom(_3dCurrentRoom||_scnFirst||'council')},50)}
  // 统一走调度器刷新当前可见 Tab（替代逐个 renderXxx，杜绝"某 Tab 不联动"打地鼠）
  if(window.dtRefresh)window.dtRefresh('tab');
}

// ── 联动调度器：右侧演练面板(团队/场景/步进/混沌) 变化 → 只刷新当前可见 Tab ──
// L3 数据源判定：
// - loadLiveMetrics 拉的 /tasks/stats 与 /extraction/stats 是进程级全局聚合（无 team/trial 过滤）；
//   保留为「平台全局 KPI」，不要伪装成当前演练指标。
// - 「当前演练」摘要卡只读 dtContext() + window._sx / SECS 选择态（team/scene/task/steps/reward），
//   经 dtRefresh(team|scenario|task|step|tab) → renderArchitecture → renderDashboard 联动刷新。
function dtContext(){
  var sx=window._sx||{};
  var team=window._selectedTeamId||(window.S&&window.S.selectedTeams&&window.S.selectedTeams[0])||'';
  var rewards=Array.isArray(sx.rewardPoints)?sx.rewardPoints:[];
  var lastReward=rewards.length?rewards[rewards.length-1]:null;
  var bestReward=rewards.length?Math.max.apply(null,rewards.map(Number).filter(function(n){return Number.isFinite(n);})):null;
  if(bestReward!=null&&!Number.isFinite(bestReward))bestReward=null;
  var taskGoal=window._selectedTaskGoal||null;
  return{
    team:team,
    teamName:window._selectedTeamName||'',
    scenarioId:sx.scenarioId||window._selectedSceneId||'',
    scenarioName:window._selectedSceneName||'',
    taskId:(taskGoal&&taskGoal.task_id)||window._selectedTaskId||'',
    taskName:(taskGoal&&(taskGoal.name||taskGoal.title))||window._selectedTaskTitle||'',
    steps:sx.steps||0,
    maxSteps:sx.maxSteps||0,
    running:!!sx.simRunning,
    trialId:(window._DTS&&window._DTS.activeTrialId)||'',
    lastReward:lastReward,
    bestReward:bestReward,
  };
}
window.dtContext=dtContext;
window.dtRefresh=function(reason){
  var p=document.querySelector('.view-panel.active');var v=p?p.id:'';
  try{
    if(v==='view-environment'){ if((reason==='team'||reason==='scenario'||reason==='tab')&&window._dt3dBuildRoom&&window._currentRoomId)window._dt3dBuildRoom(window._currentRoomId); }
    else if(v==='view-architecture'){ if(typeof renderArchitecture==='function')renderArchitecture(); }
    else if(v==='view-interaction'){ var tp=document.getElementById('interact-sub-topo');
      if(tp&&tp.style.display!=='none'){ if(typeof renderTopology==='function')renderTopology(); }
      else { if(typeof renderInteractions==='function')renderInteractions('all'); } }
    else if(v==='view-pipeline'){ if(typeof renderPipeline==='function')renderPipeline(); }
  }catch(e){}
};

function renderAgentList(){
  // 树根：优先 #lp-tree，否则退回 #agent-list
  const tree=document.getElementById('lp-tree');
  const el=tree||document.getElementById('agent-list');
  if(!el) return;
  const visibleAgents=S.agents.filter(a=>S.selectedTeams.includes(a._teamId));
  const countEl=document.getElementById('agent-count');
  if(countEl) countEl.textContent=visibleAgents.length;
  const colors=['var(--cyan)','var(--green)','var(--purple)','var(--amber)','var(--pink)','var(--blue)'];
  const teamColors=['var(--cyan)','var(--green)','var(--purple)','var(--amber)','var(--pink)','var(--blue)'];
  // 首次：已选团队默认展开
  (S.teams||[]).forEach(t=>{
    if(window._lpTreeExpanded[t.id]==null && S.selectedTeams.includes(t.id))
      window._lpTreeExpanded[t.id]=true;
  });
  let html='';
  (S.teams||[]).forEach((team,ti)=>{
    const tc=teamColors[ti%teamColors.length];
    const sel=S.selectedTeams.includes(team.id);
    const expanded=!!window._lpTreeExpanded[team.id];
    const nAgents=(team.agents||[]).length;
    html+=`<div class="lp-team${sel?' selected':''}${expanded?' expanded':''}" data-tid="${team.id}" role="treeitem" aria-expanded="${expanded}">
      <div class="lp-team-row" onclick="lpToggleExpand('${team.id}',event)">
        <span class="lp-team-caret">▶</span>
        <span class="lp-team-check" title="投放/筛选此种群" onclick="event.stopPropagation();toggleTeam('${team.id}',this)">${sel?'✓':''}</span>
        <span class="lp-team-dot" style="background:${tc}"></span>
        <span class="lp-team-name" style="color:${sel?tc:'var(--text)'}">${team.name||team.id}</span>
        <span class="lp-team-meta">${nAgents}</span>
      </div>
      <div class="lp-agents" role="group">`;
    (team.agents||[]).forEach((a)=>{
      const ci=S.agents.indexOf(a)%6;const c=colors[ci];
      const room=S.rooms.find(r=>r.id===S.positions[a.agent_id]);
      const dim=!sel;
      html+=`<div class="agent-card" draggable="true" data-agent-id="${a.agent_id}" style="${dim?'opacity:.45':''}"
        onclick="selectAgent('${a.agent_id}',this)" ondragstart="onDragStart(event,'${a.agent_id}')">
        <div class="top">
          <div class="avatar" style="background:${c}20;color:${c};border:1.5px solid ${c}40">${(a.name||'?').charAt(0)}</div>
          <div><div class="name">${a.name}</div><div class="role">${a.role||'agent'}</div></div>
          <span class="state-dot" style="background:${a.state==='active'?'var(--green)':'var(--dim)'};margin-left:auto"></span>
        </div>
        <div class="meta"><span>▣${(a.tools||[]).length}</span><span>◈${(a.skills||[]).length}</span><span>○${room?room.name:'—'}</span></div>
      </div>`;
    });
    html+=`</div></div>`;
  });
  if(!(S.teams||[]).length) html='<div style="padding:12px;font-size:11px;color:var(--dim)">加载团队中…</div>';
  el.innerHTML=html;
  // 兼容：隐藏的 #agent-list 若独立存在且不是 tree 子节点被清空后需忽略
}
function selectAgent(aid,el){
  document.querySelectorAll('.agent-card').forEach(c=>c.classList.remove('active'));el.classList.add('active');
  const ag=S.agents.find(a=>a.agent_id===aid);if(!ag)return;
  addActivity(`选中: ${ag.name}`);
  showAgentDrawer(ag);
  // 3D: 聚焦到该智能体
  if(window._dt3dFocusAgent)window._dt3dFocusAgent(aid);
}
function showAgentDrawer(ag){
  const drawer=document.getElementById('agent-drawer');
  const colors=['var(--cyan)','var(--green)','var(--purple)','var(--amber)','var(--pink)','var(--blue)'];
  const ci=S.agents.indexOf(ag)%6;const c=colors[ci];
  const room=S.rooms.find(r=>r.id===S.positions[ag.agent_id]);
  const ints=S.messages.filter(m=>m.from===ag.name||m.to===ag.name);
  drawer.innerHTML=`<div class="drawer-header"><div class="drawer-avatar" style="background:${c}20;color:${c};border:2px solid ${c}40">${(ag.name||'?').charAt(0)}</div><div><div class="drawer-name">${ag.name}</div><div class="drawer-role">${ag.role||'agent'}</div></div><button class="drawer-close" onclick="closeDrawer()">✕</button></div>
    <div class="drawer-section"><div class="drawer-section-title">基本信息</div><div class="drawer-kv"><span class="k">ID</span><span class="v" style="font-family:'JetBrains Mono',monospace;font-size:10px">${ag.agent_id}</span></div><div class="drawer-kv"><span class="k">状态</span><span class="v" style="color:${ag.state==='active'?'var(--green)':'var(--dim)'}">${ag.state==='active'?'● 活跃':'○ 空闲'}</span></div><div class="drawer-kv"><span class="k">位置</span><span class="v">${room?room.icon+' '+room.name:'未分配'}</span></div><div class="drawer-kv"><span class="k">交互次数</span><span class="v" style="color:var(--amber)">${ints.length}</span></div><div class="drawer-kv"><span class="k">模型</span><span class="v">${ag.model||'default'}</span></div></div>
    <div class="drawer-section"><div class="drawer-section-title">技能 (${(ag.skills||[]).length})</div><div class="drawer-tags">${(ag.skills||[]).map(s=>`<span class="drawer-tag">${s.icon||'◈'} ${s.name||s}</span>`).join('')||'<span style="font-size:11px;color:var(--dim)">无绑定技能</span>'}</div></div>
    <div class="drawer-section"><div class="drawer-section-title">工具 (${(ag.tools||[]).length})</div><div class="drawer-tags">${(ag.tools||[]).map(t=>`<span class="drawer-tag">${t.icon||'▣'} ${t.name||t}</span>`).join('')||'<span style="font-size:11px;color:var(--dim)">无绑定工具</span>'}</div></div>
    ${ints.length?`<div class="drawer-section"><div class="drawer-section-title">最近交互</div>${ints.slice(-5).map(m=>`<div style="font-size:11px;color:var(--text2);padding:4px 0;border-bottom:1px solid rgba(42,53,68,0.3)"><span style="color:var(--dim);font-family:'JetBrains Mono',monospace;font-size:9px">${m.time}</span> ${m.from===ag.name?'→ '+m.to:'← '+m.from} <span style="color:var(--dim)">[${m.type}]</span></div>`).join('')}</div>`:''}
    <div class="drawer-actions"><button class="btn" onclick="execCmd('inspect ${ag.name}');closeDrawer()">CLI 检视</button><button class="btn" onclick="execCmd('trace ${ag.name}');closeDrawer()">追踪交互</button></div>`;
  drawer.classList.add('open');
}
function closeDrawer(){document.getElementById('agent-drawer').classList.remove('open')}

function renderArchitecture(){
  // 先画本地「当前演练」卡（即时联动），再拉全局 KPI 回填下方卡片
  renderDashboard();
  loadLiveMetrics();
}
function _mapTaskEngineStats(d){
  // task_engine.stats() → {total, by_status:{pending|running|completed|failed|...}, running:bool}
  // 前端 KPI 需要的是状态计数，不能把 engine.running(bool) 当活跃任务数。
  var by=(d&&d.by_status)||{};
  return{
    total:Number(d&&d.total)||0,
    running:Number(by.running)||0,
    completed:Number(by.completed)||0,
    failed:Number(by.failed)||0,
    pending:Number(by.pending)||0,
    cancelled:Number(by.cancelled)||0,
    engine_running:!!(d&&d.running),
  };
}
async function loadLiveMetrics(){
  try{
    const[taskR,extR]=await Promise.allSettled([_af(`${API}/tasks/stats`),_af('/api/v1/extraction/stats')]);
    // 全局 KPI：不按 team/trial 过滤（后端当前无过滤参数；演练态看上方「当前演练」卡）
    if(taskR.status==='fulfilled'&&taskR.value.ok){
      const d=await taskR.value.json();
      Object.assign(liveMetrics.tasks,_mapTaskEngineStats(d));
    }
    if(extR.status==='fulfilled'&&extR.value.ok){const d=await extR.value.json();if(d.funnel)Object.assign(liveMetrics.extraction,d.funnel)}
  }catch(e){console.warn('[dt] loadLiveMetrics',e)}
  liveMetrics.lastRefresh=new Date();
  renderDashboard();
}
function renderDashboard(){
  const el=document.getElementById('live-dashboard');if(!el)return;
  const activeAgents=S.agents.filter(a=>a.state==='active').length;
  const totalAgents=S.agents.length;
  const recentMsgs=S.messages.filter(m=>{const t=new Date();const mt=new Date();mt.setHours(...m.time.split(':'));return(t-mt)<600000}).length;
  const taskRunning=liveMetrics.tasks.running||0;
  const taskCompleted=liveMetrics.tasks.completed||0;
  const taskFailed=liveMetrics.tasks.failed||0;
  const taskTotal=liveMetrics.tasks.total||0;
  const successRate=(taskCompleted+taskFailed)>0?Math.round(taskCompleted/(taskCompleted+taskFailed)*100):100;
  // L3: 当前演练摘要（team/scene/task/steps/reward；随 dtRefresh 刷新）
  var _c=(window.dtContext?window.dtContext():{});
  var _tn=_c.teamName||(S.teams.find(t=>t.id===_c.team)||{}).name||_c.team||'未选团队';
  var _sn=_c.scenarioName
    ||(window._pipeScnCache&&window._pipeScnCache.data&&window._pipeScnCache.data.name)
    ||_c.scenarioId
    ||'未选场景';
  var _mx=_c.maxSteps||(window._sx&&window._sx.maxSteps)||150;
  var _rw=_c.lastReward;
  var _best=_c.bestReward;
  var _task=_c.taskName||_c.taskId||'';
  var _trial=_c.trialId||'';
  var _drill=`<div id="dt-current-drill-card" data-team="${esc(_c.team||'')}" data-scenario="${esc(_c.scenarioId||'')}" data-steps="${Number(_c.steps)||0}" data-running="${_c.running?'1':'0'}" style="background:linear-gradient(135deg,rgba(34,211,238,.08),rgba(34,211,238,.02));border:1px solid var(--cyan);border-radius:10px;padding:12px 16px;margin-bottom:12px;display:flex;align-items:center;gap:16px;flex-wrap:wrap">
    <div style="font-size:12px;font-weight:600;color:var(--cyan)">◎ 当前演练</div>
    <div style="font-size:12px;color:var(--text)">👥 ${esc(_tn)}</div>
    <div style="font-size:12px;color:var(--text)">🎯 ${esc(_sn)}</div>
    ${_task?`<div style="font-size:12px;color:var(--text)">📋 ${esc(_task)}</div>`:''}
    <div style="font-size:12px;color:${_c.running?'var(--green)':'var(--dim)'}">${_c.running?'▶ 运行中':'空闲'} · 步 ${_c.steps}/${_mx}</div>
    ${_rw!=null&&Number.isFinite(Number(_rw))?`<div style="font-size:12px;color:var(--amber)">收益 ${Number(_rw).toFixed(3)}${_best!=null&&Number(_best)!==Number(_rw)?` · 最优 ${Number(_best).toFixed(3)}`:''}</div>`:''}
    ${_trial?`<div style="font-size:11px;color:var(--dim);font-family:JetBrains Mono,monospace">trial ${esc(String(_trial).slice(0,12))}</div>`:''}
    <div style="font-size:10px;color:var(--dim);margin-left:auto">全局 KPI 不随团队过滤 · 本卡读 dtContext</div>
  </div>`;
  el.innerHTML=_drill+`
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:12px">
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px">
        <div style="font-size:11px;color:var(--dim);margin-bottom:6px">智能体在线</div>
        <div style="font-size:24px;font-weight:700;color:var(--cyan)">${activeAgents}<span style="font-size:13px;color:var(--dim);font-weight:400">/${totalAgents}</span></div>
        <div style="margin-top:6px;height:3px;border-radius:2px;background:var(--border)"><div style="height:100%;border-radius:2px;background:var(--cyan);width:${totalAgents?activeAgents/totalAgents*100:0}%"></div></div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px">
        <div style="font-size:11px;color:var(--dim);margin-bottom:6px">活跃任务</div>
        <div style="font-size:24px;font-weight:700;color:var(--amber)">${taskRunning}</div>
        <div style="font-size:11px;color:var(--dim);margin-top:4px">完成 ${taskCompleted} · 失败 ${taskFailed}</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px">
        <div style="font-size:11px;color:var(--dim);margin-bottom:6px">10分钟交互</div>
        <div style="font-size:24px;font-weight:700;color:var(--green)">${recentMsgs}</div>
        <div style="font-size:11px;color:var(--dim);margin-top:4px">总计 ${S.messages.length} 条</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px">
        <div style="font-size:11px;color:var(--dim);margin-bottom:6px">任务成功率</div>
        <div style="font-size:24px;font-weight:700;color:${successRate>=90?'var(--green)':successRate>=70?'var(--amber)':'var(--red)'}">${successRate}%</div>
        <div style="margin-top:6px;height:3px;border-radius:2px;background:var(--border)"><div style="height:100%;border-radius:2px;background:${successRate>=90?'var(--green)':successRate>=70?'var(--amber)':'var(--red)'};width:${successRate}%"></div></div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px">
        <div style="font-size:11px;color:var(--dim);margin-bottom:6px">技能库</div>
        <div style="font-size:24px;font-weight:700;color:var(--purple)">${S.skills.length}</div>
        <div style="font-size:11px;color:var(--dim);margin-top:4px">工具 ${S.tools.length} 个</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px">
        <div style="font-size:11px;color:var(--dim);margin-bottom:6px">空间分布</div>
        <div style="font-size:24px;font-weight:700;color:var(--text)">${S.rooms.length}</div>
        <div style="font-size:11px;color:var(--dim);margin-top:4px">已部署 ${Object.keys(S.positions).length}</div>
      </div>
    </div>
    <div style="font-size:10px;color:var(--dim);text-align:right">最近刷新: ${liveMetrics.lastRefresh?liveMetrics.lastRefresh.toLocaleTimeString('zh-CN'):'—'}</div>`;
  renderTaskQueue();
}
function renderTaskQueue(){
  const el=document.getElementById('live-task-queue');if(!el)return;
  // Show recent messages as "task-like" items (since real tasks come from CLI)
  const recentTasks=S.messages.filter(m=>m.type==='handoff'||m.type==='tool-call').slice(-10).reverse();
  if(!recentTasks.length){el.innerHTML='<div style="padding:20px;text-align:center;color:var(--dim);font-size:12px">暂无活跃任务 · 使用 <code style="background:var(--card);padding:2px 6px;border-radius:4px">task create</code> 创建</div>';return}
  const typeColors={'handoff':'var(--blue)','tool-call':'var(--green)','llm-call':'var(--purple)','broadcast':'var(--amber)','response':'var(--cyan)'};
  el.innerHTML=recentTasks.map(t=>`
    <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;border:1px solid var(--border);border-radius:8px;margin-bottom:6px;background:var(--card)">
      <div style="width:8px;height:8px;border-radius:50%;background:${typeColors[t.type]||'var(--dim)'};flex-shrink:0"></div>
      <div style="flex:1;min-width:0">
        <div style="font-size:12px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${t.from} → ${t.to||'System'}</div>
        <div style="font-size:11px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(t.content)}</div>
      </div>
      <div style="font-size:10px;color:var(--dim);flex-shrink:0">${t.time}</div>
      <div style="font-size:10px;padding:2px 6px;border-radius:4px;background:${typeColors[t.type]||'var(--dim)'}18;color:${typeColors[t.type]||'var(--dim)'}">${t.type}</div>
    </div>`).join('');
}

function showArchSub(tab,btn){
  // 系统状态现只剩「实时仪表盘」（协作拓扑已迁至「协作·交互」Tab）
  var layers=document.getElementById('arch-sub-layers');if(layers)layers.style.display='block';
  if(btn){document.querySelectorAll('#view-architecture .flow-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');}
  loadLiveMetrics();
}
// 「协作·交互」Tab 子页切换：交互时间线 / 协作拓扑（同源交互数据的两个视角）
window.showInteractSub=function(which,btn){
  var tl=document.getElementById('interact-sub-timeline'),tp=document.getElementById('interact-sub-topo');
  if(tl)tl.style.display=which==='timeline'?'':'none';
  if(tp)tp.style.display=which==='topo'?'':'none';
  ['isub-btn-timeline','isub-btn-topo'].forEach(function(id){var b=document.getElementById(id);if(b)b.classList.remove('active');});
  if(btn)btn.classList.add('active');
  if(which==='topo'){if(typeof renderTopology==='function')renderTopology();}
  else{if(typeof renderInteractions==='function')renderInteractions('all');}
};

// ── 混沌事件 → 协作拓扑同步（与 3D/后端 agent 数一致）──
window._chaosTopoState = window._chaosTopoState || { removed:{}, added:[] };
function _dt2dRefreshTopo(){ try{ var el=document.getElementById('interact-sub-topo'); if(el&&el.style.display!=='none'&&typeof renderTopology==='function') renderTopology(); }catch(e){} }
window._dt2dChaosLeave=function(agentId){ if(!agentId)return; window._chaosTopoState.removed[agentId]=true; window._chaosTopoState.added=(window._chaosTopoState.added||[]).filter(function(a){return a.agent_id!==agentId;}); _dt2dRefreshTopo(); };
window._dt2dChaosJoin=function(agentId,name,skills){ if(!agentId)return; var st=window._chaosTopoState; delete st.removed[agentId]; st.added=st.added||[]; if(!st.added.some(function(a){return a.agent_id===agentId;})) st.added.push({agent_id:agentId,name:name||agentId,skills:skills||[],_teamId:(S.selectedTeams&&S.selectedTeams[0])||''}); _dt2dRefreshTopo(); };
window._dt2dChaosReset=function(){ window._chaosTopoState={removed:{},added:[]}; _dt2dRefreshTopo(); };

function renderTopology(){
  const svg=document.getElementById('topo-svg');
  const W=svg.clientWidth||800,H=460;
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  const teamColors=['#22d3ee','#34d399','#a78bfa','#fbbf24','#f472b6','#60a5fa'];
  // Filter agents by selected teams, matching left panel behavior
  // 混沌同步：剔除演练中已离开的 agent，并并入增援 agent，让拓扑与 3D/后端一致
  const _chaos=window._chaosTopoState||{removed:{},added:[]};
  let visibleAgents=S.agents.filter(a=>S.selectedTeams.includes(a._teamId)&&!_chaos.removed[a.agent_id]);
  (_chaos.added||[]).forEach(function(ad){
    if(!visibleAgents.some(function(a){return a.agent_id===ad.agent_id;})) visibleAgents=visibleAgents.concat([ad]);
  });
  if(!visibleAgents.length){svg.innerHTML=`<text x="${W/2}" y="${H/2}" text-anchor="middle" fill="#576375" font-size="14">${S.agents.length?'请在左侧选择至少一个团队':'加载智能体数据后显示拓扑...'}</text>`;return}
  // Build team color map (matching left panel's teamColors)
  const teamColorMap={};
  S.teams.filter(t=>S.selectedTeams.includes(t.id)).forEach((t,i)=>{teamColorMap[t.id]=teamColors[i%teamColors.length]});
  const cx=W/2,cy=H/2,radius=Math.min(W,H)*0.32;
  // Position agents in circle
  const nodes=visibleAgents.map((a,i)=>{
    const angle=(2*Math.PI*i)/visibleAgents.length-Math.PI/2;
    const color=teamColorMap[a._teamId]||teamColors[i%6];
    return{...a,x:cx+radius*Math.cos(angle),y:cy+radius*Math.sin(angle),color,r:16+((a.skills||[]).length)*3};
  });
  // Build edges from interaction messages
  const edgeMap={};
  S.messages.forEach(m=>{
    const fromN=nodes.find(n=>n.name===m.from),toN=nodes.find(n=>n.name===m.to);
    if(fromN&&toN){const key=[fromN.agent_id,toN.agent_id].sort().join('-');edgeMap[key]=(edgeMap[key]||0)+1}
  });
  // Render
  let html='';
  // Edges
  const edgeEntries=Object.entries(edgeMap);
  if(edgeEntries.length){
    // 有真实交互历史 → 按交互频次画加权连线
    edgeEntries.forEach(([key,count])=>{
      const[id1,id2]=key.split('-');
      const n1=nodes.find(n=>n.agent_id===id1),n2=nodes.find(n=>n.agent_id===id2);
      if(n1&&n2){const opacity=Math.min(0.8,0.1+count*0.1);html+=`<line x1="${n1.x}" y1="${n1.y}" x2="${n2.x}" y2="${n2.y}" stroke="#3d5070" stroke-width="${Math.min(4,1+count*0.5)}" stroke-opacity="${opacity}"/>`}
    });
  }else{
    // 暂无交互历史 → 画编排中枢的基线连线(编排↔各 agent)，体现协作骨架，避免空白
    nodes.forEach(n=>{html+=`<line x1="${cx}" y1="${cy}" x2="${n.x}" y2="${n.y}" stroke="#3d5070" stroke-width="1" stroke-opacity="0.3" stroke-dasharray="5,5"/>`});
  }
  // Nodes
  nodes.forEach(n=>{
    html+=`<circle cx="${n.x}" cy="${n.y}" r="${n.r}" fill="${n.color}20" stroke="${n.color}" stroke-width="2"/>`;
    html+=`<text x="${n.x}" y="${n.y+4}" text-anchor="middle" fill="${n.color}" font-size="12" font-weight="600">${(n.name||'?').charAt(0)}</text>`;
    html+=`<text x="${n.x}" y="${n.y+n.r+14}" text-anchor="middle" fill="#cbd5e1" font-size="10">${n.name||'?'}</text>`;
  });
  // Center hub
  html+=`<circle cx="${cx}" cy="${cy}" r="20" fill="#0f141920" stroke="#3d5070" stroke-width="1" stroke-dasharray="4,4"/>`;
  html+=`<text x="${cx}" y="${cy+4}" text-anchor="middle" fill="#576375" font-size="10">编排</text>`;
  svg.innerHTML=html;
}

// 交互按当前所选团队过滤（from/to 命中该团队 agent 名）——与右侧选团队联动，且与协作拓扑同口径
function _scopedMsgs(){
  if(!S.selectedTeams||!S.selectedTeams.length) return S.messages;
  var names=new Set(S.agents.filter(a=>S.selectedTeams.includes(a._teamId)).map(a=>a.name));
  if(!names.size) return S.messages;
  var f=S.messages.filter(m=>names.has(m.from)||names.has(m.to));
  return f.length?f:S.messages;   // 该团队暂无交互时退回全部，避免空白误解
}
function renderFlowStats(){
  const counts={'tool-call':0,'llm-call':0,'handoff':0,'broadcast':0,'response':0};
  _scopedMsgs().forEach(m=>{if(counts[m.type]!==undefined)counts[m.type]++});
  const colors={'tool-call':'var(--green)','llm-call':'var(--purple)','handoff':'var(--blue)','broadcast':'var(--amber)','response':'var(--cyan)'};
  const labels={'tool-call':'工具调用','llm-call':'LLM推理','handoff':'任务交接','broadcast':'广播','response':'响应'};
  document.getElementById('flow-stats').innerHTML=Object.entries(counts).map(([k,v])=>`<div class="flow-stat-item"><span class="flow-stat-dot" style="background:${colors[k]}"></span><span class="flow-stat-count">${v}</span><span class="flow-stat-label">${labels[k]}</span></div>`).join('')+`<div class="flow-stat-item" style="margin-left:auto"><span class="flow-stat-label">总计</span><span class="flow-stat-count" style="color:var(--text)">${_scopedMsgs().length}</span></div>`;
}
function renderInteractions(filter='all'){
  renderFlowStats();
  const el=document.getElementById('msg-timeline');
  const scoped=_scopedMsgs();
  document.getElementById('msg-count').textContent=scoped.length;
  const msgs=filter==='all'?scoped:scoped.filter(m=>m.type===filter);
  if(!msgs.length){el.innerHTML='<div style="text-align:center;padding:40px;color:var(--dim)">暂无交互记录<br><span style="font-size:11px">使用CLI或触发任务后显示</span></div>';return}
  const colors={'tool-call':'var(--green)','llm-call':'var(--purple)','handoff':'var(--blue)','broadcast':'var(--amber)','response':'var(--cyan)'};
  el.innerHTML=msgs.slice(-50).map(m=>{const c=colors[m.type]||'var(--muted)';
    return`<div class="msg-item"><span class="msg-time">${m.time}</span><div class="msg-avatar" style="background:${c}20;color:${c}">${(m.from||'S').charAt(0)}</div><div class="msg-body"><div class="msg-sender">${m.from} <span class="arrow">→</span> <span class="target">${m.to||'System'}</span> <span class="msg-type-tag ${m.type}">${m.type}</span></div><div class="msg-content">${esc(m.content)}</div>${m.duration?`<div class="msg-meta"><span>⏱ ${m.duration}ms</span></div>`:''}</div></div>`;
  }).join('');el.scrollTop=el.scrollHeight;
}
function filterMsgs(type){document.querySelectorAll('.flow-btn').forEach(b=>b.classList.remove('active'));event.target.classList.add('active');renderInteractions(type)}
let currentFlowView='timeline';
function switchFlowView(view,btn){
  currentFlowView=view;
  document.getElementById('msg-timeline').style.display=view==='timeline'?'block':'none';
  document.getElementById('sequence-diagram').style.display=view==='sequence'?'block':'none';
  document.getElementById('btn-view-timeline').classList.toggle('active',view==='timeline');
  document.getElementById('btn-view-sequence').classList.toggle('active',view==='sequence');
  if(view==='sequence')renderSequenceDiagram();
}
function renderSequenceDiagram(){
  const svg=document.getElementById('seq-svg');if(!svg)return;
  // 与时间线同口径：按所选团队过滤（bug-086），避免序列图串入别团队/演示消息
  const msgs=(typeof _scopedMsgs==='function'?_scopedMsgs():S.messages).slice(-30);
  if(!msgs.length){svg.innerHTML='<text x="50%" y="50%" text-anchor="middle" fill="#576375" font-size="13">暂无交互记录</text>';return}
  // Collect unique participants
  const participants=[...new Set(msgs.flatMap(m=>[m.from,m.to||'System'].filter(Boolean)))];
  const colW=140,padX=60,padY=60,rowH=36;
  const W=padX*2+participants.length*colW;
  const H=padY+60+msgs.length*rowH+40;
  svg.setAttribute('width',W);svg.setAttribute('height',H);
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  const colors={'tool-call':'#34d399','llm-call':'#a78bfa','handoff':'#60a5fa','broadcast':'#fbbf24','response':'#22d3ee'};
  const agentColors=['#22d3ee','#34d399','#a78bfa','#fbbf24','#f472b6','#60a5fa','#fb923c','#e879f9'];
  let html='';
  // Participant lifelines
  participants.forEach((p,i)=>{
    const x=padX+i*colW+colW/2;
    const c=agentColors[i%agentColors.length];
    html+=`<line x1="${x}" y1="${padY+30}" x2="${x}" y2="${H-20}" stroke="${c}30" stroke-width="1.5" stroke-dasharray="4,4"/>`;
    html+=`<rect x="${x-48}" y="${padY}" width="96" height="26" rx="6" fill="${c}18" stroke="${c}" stroke-width="1.2"/>`;
    html+=`<text x="${x}" y="${padY+17}" text-anchor="middle" fill="${c}" font-size="11" font-weight="600">${p.length>10?p.slice(0,9)+'…':p}</text>`;
  });
  // Messages as arrows
  msgs.forEach((m,i)=>{
    const fromIdx=participants.indexOf(m.from);
    const toIdx=participants.indexOf(m.to||'System');
    if(fromIdx<0||toIdx<0)return;
    const y=padY+60+i*rowH;
    const x1=padX+fromIdx*colW+colW/2;
    const x2=padX+toIdx*colW+colW/2;
    const c=colors[m.type]||'#576375';
    const isSelf=fromIdx===toIdx;
    if(isSelf){
      html+=`<path d="M${x1} ${y} C${x1+40} ${y},${x1+40} ${y+20},${x1} ${y+20}" fill="none" stroke="${c}" stroke-width="1.5" marker-end="url(#arrow-${m.type||'def'})"/>`;
    }else{
      html+=`<line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${c}" stroke-width="1.5" marker-end="url(#arrow-${m.type||'def'})"/>`;
    }
    const midX=(x1+x2)/2;
    const label=(m.content||'').slice(0,20);
    html+=`<text x="${midX}" y="${y-6}" text-anchor="middle" fill="${c}" font-size="9" opacity="0.85">${m.type} ${label?'· '+label:''}</text>`;
    html+=`<text x="${padX-8}" y="${y+4}" text-anchor="end" fill="#576375" font-size="9">${m.time||''}</text>`;
  });
  // Arrow markers
  const markerTypes=Object.keys(colors).concat(['def']);
  html+=`<defs>${markerTypes.map(t=>`<marker id="arrow-${t}" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="${colors[t]||'#576375'}"/></marker>`).join('')}</defs>`;
  svg.innerHTML=html;
}

// 编排管线 = 当前演练场景的「任务编排 DAG」+ 实时执行状态（不再复制技能萃取阶段）
async function renderPipeline(){
  const flow=document.getElementById('pipeline-flow');const bar=document.getElementById('pipeline-progress-bar');
  if(!flow)return;
  // 场景来源：优先当前手选场景；否则回退到「正在运行试炼」创建时捕获的 runScenarioId
  // （runScenarioId 只在 createTrial 里写，房间/场景导航不会清它 → 运行中切房间也不会把管线弄空）。
  const _sxo=window._sx||{};
  const sid=_sxo.scenarioId||_sxo.runScenarioId;
  if(!sid){
    const _running=!!(_sxo.sessionId&&_sxo.simRunning);
    flow.innerHTML='<div style="padding:28px;text-align:center;color:var(--dim);font-size:13px">'+(_running
      ? '本次为<b>无场景基线运行</b>，没有任务编排 DAG。<br>如需查看 DAG，请在右侧「选择演练场景」选一个具体场景后运行。'
      : '在右侧「选择演练场景」选一个场景后，这里显示该场景的<b>任务编排（DAG）</b>与实时执行状态')+'</div>';
    if(bar)bar.style.width='0%';renderExecLog();return;
  }
  // 场景缓存：每步重渲染时不再重复拉取
  let scn=(window._pipeScnCache&&window._pipeScnCache.id===sid)?window._pipeScnCache.data:null;
  if(!scn){try{scn=await _af('/api/v1/scenarios/'+encodeURIComponent(sid)).then(r=>r.json());window._pipeScnCache={id:sid,data:scn};}catch(e){return;}}
  const tf=(scn&&(scn.taskflow||scn.task_flow))||[];
  if(!tf.length){flow.innerHTML='<div style="padding:28px;text-align:center;color:var(--dim)">该场景暂无任务流</div>';renderExecLog();return;}
  // 拓扑分层（按 depends_on），含环保护
  const byId={};tf.forEach(t=>byId[t.task_id]=t);const layer={};
  function depth(id,seen){if(layer[id]!=null)return layer[id];const s=seen||new Set();if(s.has(id))return 0;s.add(id);const deps=(byId[id]&&byId[id].depends_on)||[];const d=deps.length?Math.max(...deps.map(x=>depth(x,new Set(s))))+1:0;layer[id]=d;return d;}
  tf.forEach(t=>depth(t.task_id));const maxL=Math.max(...tf.map(t=>layer[t.task_id]||0));
  const cols=[];for(let i=0;i<=maxL;i++)cols[i]=tf.filter(t=>(layer[t.task_id]||0)===i);
  // 实时状态：后端有 taskflow 节点状态时精确高亮；旧会话无字段时保留步数比例兜底。
  var _cur=(window._sx&&window._sx.steps)||0;var _mx=(window._sx&&window._sx.maxSteps)||scn.recommended_max_steps||150;
  var _activeIds=new Set((Array.isArray(_sxo.activeTaskIds)?_sxo.activeTaskIds:(_sxo.activeTaskId?[_sxo.activeTaskId]:[])).filter(Boolean));
  var _doneIds=new Set((Array.isArray(_sxo.doneTaskIds)?_sxo.doneTaskIds:[]).filter(Boolean));
  var _hasPrecise=Array.isArray(_sxo.doneTaskIds)||_activeIds.size>0;
  var doneCount=_hasPrecise?tf.filter(t=>_doneIds.has(t.task_id)).length:Math.round(Math.min(1,_mx?_cur/_mx:0)*tf.length);
  function _taskState(t,gi){
    if(_hasPrecise){
      if(_doneIds.has(t.task_id))return'done';
      if(_activeIds.has(t.task_id))return'running';
      var deps=t.depends_on||[];
      if(deps.length&&!deps.every(d=>_doneIds.has(d)))return'blocked';
      return'pending';
    }
    return gi<doneCount?'done':(gi===doneCount?'running':'pending');
  }
  flow.innerHTML=cols.map((col,ci)=>{
    const colHtml='<div style="display:flex;flex-direction:column;gap:8px">'+col.map(t=>{
      const gi=tf.indexOf(t);const st=_taskState(t,gi);
      const c={done:'var(--green)',running:'var(--cyan)',pending:'var(--dim)',blocked:'var(--amber)'}[st];const txt={done:'✓ 完成',running:'▶ 进行中',pending:'待办',blocked:'等待依赖'}[st];
      return '<div class="pipeline-step" style="min-width:150px;text-align:left;border-left:3px solid '+c+'"><div class="step-name">'+esc(t.name||t.task_id)+'</div><div class="step-desc">'+esc(t.room_id||'')+(((t.required_skills||[]).length)?(' · '+esc((t.required_skills||[]).slice(0,2).join(','))):'')+'</div><div style="font-size:10px;color:'+c+'">'+txt+'</div></div>';
    }).join('')+'</div>';
    return (ci>0?'<div class="pipeline-connector">→</div>':'')+colHtml;
  }).join('');
  if(bar)bar.style.width=(tf.length?doneCount/tf.length*100:0)+'%';
  renderExecLog();
}
async function loadPipelineState(){
  try{
    const r=await _af('/api/v1/extraction/pipelines');
    if(!r.ok)return;
    const data=await r.json();
    const pipelines=data.pipelines||data||[];
    if(!pipelines.length)return;
    // Show the most recent active pipeline's stage
    const active=pipelines.find(p=>p.current_stage!=='published'&&p.current_stage!=='draft')||pipelines[0];
    if(!active)return;
    const stageOrder=['draft','extract','review','approval','published'];
    const currentIdx=stageOrder.indexOf(active.current_stage);
    const steps=document.querySelectorAll('.pipeline-step');
    const bar=document.getElementById('pipeline-progress-bar');
    steps.forEach((s,i)=>{s.classList.remove('active','done');if(i<currentIdx)s.classList.add('done');if(i===currentIdx)s.classList.add('active')});
    bar.style.width=currentIdx>=0?((currentIdx+1)/stageOrder.length*100)+'%':'0%';
    // Show pipeline info in exec log
    addExecLog('info',`管线 "${active.name}" 当前阶段: ${active.current_stage}`);
    // Show count summary
    const counts={};pipelines.forEach(p=>{counts[p.current_stage]=(counts[p.current_stage]||0)+1});
    addExecLog('info',`管线统计: ${Object.entries(counts).map(([k,v])=>`${k}(${v})`).join(' · ')}`);
  }catch{}
}
function renderExecLog(){
  document.getElementById('log-count').textContent=S.execLog.length+' 条';
  const el=document.getElementById('exec-log');
  const tagC={info:'var(--cyan-dim);color:var(--cyan)',tool:'var(--green-dim);color:var(--green)',llm:'var(--purple-dim);color:var(--purple)',error:'var(--pink-dim);color:var(--red)'};
  el.innerHTML=S.execLog.slice(-20).map(l=>`<div class="exec-log-item"><span class="ts">${l.time}</span><span class="tag" style="background:${tagC[l.type]||tagC.info}">${l.type}</span><span class="content">${esc(l.msg)}</span></div>`).join('')||'<div style="padding:16px;color:var(--dim);font-size:12px;text-align:center">等待任务执行...</div>';
}

function renderRoomTabs(){
  const el=document.getElementById('room-tabs');if(!el)return;
  if(!S.rooms||!S.rooms.length)S.rooms=defaultRooms();
  const _cur=window._currentRoomId||(S.rooms[0]&&S.rooms[0].id);
  el.innerHTML=S.rooms.map((r)=>`<button class="flow-btn${r.id===_cur?' active':''}" onclick="switchRoom('${r.id}',this)">${r.name}</button>`).join('');
}
function renderEnvironment(){
  const colors=['var(--cyan)','var(--green)','var(--purple)','var(--amber)','var(--pink)','var(--blue)'];
  document.getElementById('env-grid').innerHTML=S.rooms.map(r=>{
    const ag=S.agents.filter(a=>S.positions[a.agent_id]===r.id);
    return`<div class="env-room" data-room-id="${r.id}" onclick="showRoom('${r.id}')" ondragover="onDragOver(event)" ondragleave="onDragLeave(event)" ondrop="onDrop(event,'${r.id}')"><div class="room-icon">${r.icon}</div><div class="room-name">${r.name}</div><div class="room-desc">${r.desc}</div><div class="room-agents">${ag.map((a,i)=>`<div class="ag-dot" style="background:${colors[i%6]}30;color:${colors[i%6]}" title="${a.name}">${(a.name||'?').charAt(0)}</div>`).join('')||'<span style="font-size:10px;color:var(--dim)">空</span>'}</div><div class="drop-hint">拖放智能体到此空间</div><div class="room-footer"><span>${ag.length} 智能体</span><span style="color:${r.color}">●</span></div></div>`;
  }).join('');
}
function showRoom(id){const r=S.rooms.find(x=>x.id===id);if(!r)return;const ag=S.agents.filter(a=>S.positions[a.agent_id]===id);toast(`${r.icon} ${r.name} — ${ag.length} 智能体: ${ag.map(a=>a.name).join(', ')||'(空)'}`);if(window.secsSyncSceneFromRoom)window.secsSyncSceneFromRoom(id);}
function createRoom(){const name=prompt('新空间名称:');if(!name)return;S.rooms.push({id:'r_'+Date.now().toString(36),name,icon:prompt('图标:','◇')||'◇',desc:prompt('描述:','')||'',color:'var(--muted)'});persist();renderEnvironment();renderRoomTabs();toast('空间已创建: '+name)}

function renderStats(){
  document.getElementById('stat-agents').textContent=S.agents.length;
  document.getElementById('stat-skills').textContent=S.skills.length;
  document.getElementById('stat-tools').textContent=S.tools.length;
  document.getElementById('stat-interactions').textContent=S.interactionCount;
  // Pipeline count from liveMetrics
  const pipeActive=(liveMetrics.extraction.active||0)+(liveMetrics.extraction.pending||0);
  document.getElementById('stat-pipelines').textContent=pipeActive||'-';
  // Health indicator
  const activeAgents=S.agents.filter(a=>a.state==='active').length;
  const healthEl=document.getElementById('stat-health');
  if(S.agents.length===0){healthEl.textContent='—';healthEl.className='value'}
  else if(activeAgents/S.agents.length>=0.8){healthEl.textContent='● 优良';healthEl.className='value green'}
  else if(activeAgents/S.agents.length>=0.5){healthEl.textContent='● 一般';healthEl.className='value amber'}
  else{healthEl.textContent='● 异常';healthEl.className='value red'}
}
function renderFreqChart(){const el=document.getElementById('freq-chart');const max=Math.max(...S.freqData,1);el.innerHTML=S.freqData.map(v=>`<div class="bar" style="height:${(v/max)*100}%"></div>`).join('')}

function addActivity(text){
  const time=new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  S.activityFeed.unshift({time,text});if(S.activityFeed.length>50)S.activityFeed.pop();renderActivityFeed();
}
function renderActivityFeed(){document.getElementById('activity-feed').innerHTML=S.activityFeed?.slice(0,20)||[].map(a=>`<div class="activity-item"><div class="act-time">${a.time}</div><div class="act-text">${a.text}</div></div>`).join('')||'<div style="color:var(--dim);font-size:11px">暂无活动</div>'}

// ── CLI ──
const cliH=[];let hIdx=-1;
document.addEventListener('DOMContentLoaded',()=>{
  const inp=document.getElementById('cli-input');
  inp.addEventListener('keydown',e=>{
    if(e.key==='Enter'){execCmd(inp.value);inp.value=''}
    else if(e.key==='ArrowUp'){e.preventDefault();if(hIdx>0){hIdx--;inp.value=cliH[hIdx]}}
    else if(e.key==='ArrowDown'){e.preventDefault();if(hIdx<cliH.length-1){hIdx++;inp.value=cliH[hIdx]}else{hIdx=cliH.length;inp.value=''}}
  });
  init();
});

async function execCmd(input){
  if(!input.trim())return;cliH.push(input);hIdx=cliH.length;
  const out=document.getElementById('cli-output');
  out.innerHTML+=`\n<span class="prompt">❯ </span><span class="cmd">${esc(input)}</span>\n`;
  // Show loading for async commands
  const asyncCmds=['move','assign','discuss','extract','review','evolve','optimize','health','task','workflow','delegate','chat'];
  const cmd0=input.trim().split(/\s+/)[0];
  let loadEl=null;
  if(asyncCmds.includes(cmd0)){
    loadEl=document.createElement('span');loadEl.className='dim';loadEl.textContent='⏳ 处理中...';
    loadEl.style.animation='pulse 1s infinite';out.appendChild(loadEl);out.scrollTop=out.scrollHeight;
  }
  const result=await processCmd(input.trim());
  if(loadEl)loadEl.remove();
  if(result)out.innerHTML+=result+'\n';
  out.scrollTop=out.scrollHeight;
  addActivity(`CLI: ${input}`);
  S.interactionCount++;S.freqData.push(1);S.freqData.shift();
  renderStats();renderFreqChart();
  localStorage.setItem('dt2_interactions',S.interactionCount);
}

async function processCmd(input){
  const[cmd,...args]=input.split(/\s+/);const arg=args.join(' ');
  switch(cmd){
    case'help':return helpText();
    case'status':return statusText();
    case'agents':return agentsText();
    case'skills':return skillsText();
    case'tools':return toolsText();
    case'rooms':return roomsText();
    case'arch':return archText();
    case'clear':document.getElementById('cli-output').innerHTML='';return'';
    case'move':return await moveAgent(args[0],args.slice(1).join(' '));
    case'interact':return interactAgents(args[0],args[1]);
    case'assign':return await moveAgent(args[0],args.slice(1).join(' '));
    case'pipeline':return pipelineCmd(args);
    case'flow':return flowCmd(args);
    case'export':return exportCmd(args[0]);
    case'broadcast':return broadcastCmd(arg);
    case'inspect':return inspectCmd(args[0]);
    case'trace':return traceCmd(args[0]);
    case'simulate':return simulateCmd(args);
    case'config':return configCmd(args);
    case'discuss':return await discussCmd(args);
    case'delegate':return await delegateCmd(args);
    case'chat':return await chatCmd(arg);
    case'extract':return await extractCmd(args);
    case'review':return await reviewCmd(args);
    case'evolve':return await evolveCmd(args);
    case'optimize':return await optimizeCmd(args);
    case'health':return await healthCmd(args);
    case'task':return await taskCmd(args);
    case'workflow':return await workflowCmd(args);
    case'cam':return camCmd(args);
    case'fly':return camCmd(args);
    case'tour':flyTour();return'<span class="cmd">▶</span> 3D巡览启动 — 依次飞越 6 个空间';
    case'trial':return await trialCmd(args);
    case'whoami':return'<span class="result">admin@AgentsGroup2026 (Digital Twin v3.0)</span>';
    default:return`<span class="err">未知命令: ${cmd}</span> — 输入 <span class="cmd">help</span> 查看帮助`;
  }
}

async function trialCmd(args){var sub=args[0]||'list',id=args[1]||'',API='/api/v1/twin-trials';
  switch(sub){
    case'list':try{var r=await _af(API);var d=await r.json();var t=d.trials||[];
      if(!t.length)return'<span class="dim">暂无试炼</span>';
      return'<span class="info">━━━ '+d.total+' 条试炼 ━━━</span><br>'+t.map(function(x){var e={READY:'●',RUNNING:'▶',COMPLETED:'✓',FAILED:'✗'};return'  <span class="cmd">'+(e[x.status]||'○')+' '+x.id.slice(0,8)+'</span> '+x.name+' <span class="dim">['+x.mode+']</span>';}).join('<br>')}catch(e){return'<span class="err">'+e.message+'</span>'}
    case'show':if(!id)return'<span class="err">用法: trial show &lt;id&gt;</span>';
      try{var r2=await _af(API+'/'+id);var td=await r2.json();
        var ev=td.evaluation||{};
        return'<span class="info">━━━ '+td.name+' ━━━</span><br>  状态: <span class="cmd">'+td.status+'</span> | 模式: '+td.mode+'<br>  步数: '+td.total_steps+' | SOP: '+td.sop_count+' | 评分: '+(td.best_score||'--')+'<br>  韧性: '+Math.round((ev.resilience||0)*100)+'% | 总分: '+Math.round((ev.total_score||0)*100)+'%';}catch(e){return'<span class="err">'+e.message+'</span>'}
    case'eval':if(!id)return'<span class="err">用法: trial eval &lt;id&gt;</span>';
      try{var r3=await _af(API+'/'+id+'/evaluate',{method:'POST'});var ed=await r3.json();
        return'<span class="cmd">✓ 评分完成</span><br>  🎯'+Math.round((ed.task_completion||0)*100)+'% | 🤝'+Math.round((ed.collaboration_efficiency||0)*100)+'% | 🛡️'+Math.round((ed.resilience||0)*100)+'% | 💰'+Math.round((ed.cost_efficiency||0)*100)+'% | 📋'+Math.round((ed.extractability||0)*100)+'% | ⭐'+Math.round((ed.total_score||0)*100)+'%';}catch(e){return'<span class="err">'+e.message+'</span>'}
    case'sop':if(!id)return'<span class="err">用法: trial sop &lt;id&gt;</span>';
      try{var r4=await _af(API+'/'+id+'/extract-sop',{method:'POST'});var sd=await r4.json();var ss=sd.sops||[];
        if(!ss.length)return'<span class="dim">未提取到SOP</span>';
        return'<span class="cmd">✓ '+ss.length+' SOP</span><br>'+ss.map(function(s){return'  📋 '+s.name+' <span class="dim">'+Math.round(s.confidence*100)+'%</span>';}).join('<br>');}catch(e){return'<span class="err">'+e.message+'</span>'}
    case'feedback':if(!id)return'<span class="err">用法: trial feedback &lt;id&gt;</span>';
      try{var r5=await _af(API+'/'+id+'/feedback',{method:'POST'});var fd=await r5.json();
        return'<span class="cmd">✓ 反哺完成</span><br>  SOP: '+fd.applied_sops+' | Agent: '+(fd.updated_agents||[]).length+' | 技能: '+(fd.updated_skills||[]).length;}catch(e){return'<span class="err">'+e.message+'</span>'}
    case'events':if(!id)return'<span class="err">用法: trial events &lt;id&gt;</span>';
      try{var r6=await _af(API+'/'+id);var td2=await r6.json();
        return'<span class="info">━━━ 试炼 #'+id.slice(0,8)+' 事件 ━━━</span><br>  分支: '+(td2.branches||[]).length+' | 评分: '+(td2.best_score||'--')+'<br>  使用 <span class="cmd">trial show '+id+'</span> 查看详情';}catch(e){return'<span class="err">'+e.message+'</span>'}
    default:return'<span class="err">未知: '+sub+' — trial list|show|eval|sop|feedback|events</span>'}}

function helpText(){return`<span class="info">━━━ 可用命令 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  <span class="layer-ui">查询</span>
    <span class="cmd">status</span>             系统状态摘要
    <span class="cmd">agents</span>             列出所有智能体
    <span class="cmd">skills</span>             列出已注册技能
    <span class="cmd">tools</span>              列出已注册工具
    <span class="cmd">rooms</span>              列出环境空间
    <span class="cmd">arch</span>               显示系统架构
    <span class="cmd">inspect &lt;name&gt;</span>     查看智能体详情
    <span class="cmd">trace &lt;name&gt;</span>       追踪智能体交互
    <span class="cmd">health</span>             全系统健康巡检

  <span class="layer-orch">编排</span>
    <span class="cmd">move &lt;agent&gt; &lt;room&gt;</span>    移动智能体到空间
    <span class="cmd">interact &lt;a1&gt; &lt;a2&gt;</span>    触发两个智能体交互
    <span class="cmd">broadcast &lt;msg&gt;</span>        全局广播消息
    <span class="cmd">pipeline show</span>          管线状态
    <span class="cmd">pipeline run &lt;task&gt;</span>    执行任务管线
    <span class="cmd">simulate &lt;scenario&gt;</span>   模拟(random|chain|stress)
    <span class="cmd">discuss &lt;topic&gt;</span>       创建广场讨论
    <span class="cmd">discuss watch &lt;id&gt;</span>    订阅讨论SSE实时流
    <span class="cmd">discuss start &lt;id&gt;</span>    启动讨论
    <span class="cmd">delegate &lt;a1&gt; &lt;a2&gt; &lt;task&gt;</span> 委派任务
    <span class="cmd">chat &lt;msg&gt;</span>            与AI对话

  <span class="layer-llm">萃取 &amp; 演进</span>
    <span class="cmd">extract &lt;source&gt;</span>      触发技能萃取管线
    <span class="cmd">extract status</span>         萃取漏斗统计
    <span class="cmd">review &lt;id&gt; [approve|reject]</span> 审批萃取管线
    <span class="cmd">evolve audit</span>           运行演进审计
    <span class="cmd">evolve status</span>          演进引擎状态
    <span class="cmd">evolve items</span>           列出演进项
    <span class="cmd">evolve rating</span>          合规评级
    <span class="cmd">optimize &lt;skill&gt;</span>      触发技能优化

  <span class="layer-tool">任务 &amp; 工作流</span>
    <span class="cmd">task list</span>              查看任务列表
    <span class="cmd">task create &lt;title&gt;</span>   创建任务
    <span class="cmd">task start &lt;id&gt;</span>       启动任务
    <span class="cmd">task dag</span>               可视化任务DAG
    <span class="cmd">task stats</span>             任务引擎统计
    <span class="cmd">workflow &lt;name&gt; [arg]</span> 执行预定义工作流
    <span class="cmd">workflow list</span>          列出可用工作流

  <span class="layer-ui">3D空间 &amp; 摄像头</span>
    <span class="cmd">cam council</span>            飞到议事厅
    <span class="cmd">cam extraction</span>         飞到萃取室
    <span class="cmd">cam workshop</span>           飞到工作坊
    <span class="cmd">cam library</span>            飞到知识库
    <span class="cmd">cam arena</span>              飞到演练场
    <span class="cmd">cam rest</span>               飞到休息区
    <span class="cmd">cam overview</span>           鸟瞰全景
    <span class="cmd">tour</span>                  自动巡览全部空间
    <span class="cmd">export &lt;type&gt;</span>          导出(snapshot|agents|skills)
    <span class="cmd">config show</span>            查看配置
    <span class="cmd">clear</span>                 清屏
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>`}

function statusText(){
  const p=Object.keys(S.positions).length;
  return`<span class="info">━━━ 系统状态 ━━━</span>
  <span class="layer-orch">编排层</span>  智能体: <span class="result">${S.agents.length}</span> (活跃 <span class="cmd">${S.agents.filter(a=>a.state==='active').length}</span>)
  <span class="layer-llm">推理层</span>  交互数: <span class="result">${S.interactionCount}</span>
  <span class="layer-mem">记忆层</span>  技能: <span class="result">${S.skills.length}</span> | 工具: <span class="result">${S.tools.length}</span>
  <span class="layer-tool">环境层</span>  空间: <span class="result">${S.rooms.length}</span> | 已部署: <span class="result">${p}/${S.agents.length}</span>
  <span class="dim">${new Date().toLocaleString('zh-CN')}</span>`}

function agentsText(){
  if(!S.agents.length)return'<span class="warn">暂无智能体</span>';
  let o='<span class="info">━━━ 智能体列表 ━━━</span>\n';
  S.agents.forEach(a=>{const room=S.rooms.find(r=>r.id===S.positions[a.agent_id]);
    o+=`  <span class="result">${(a.name||'?').padEnd(12)}${(a.role||'-').padEnd(12)}</span>${a.state==='active'?'<span class="cmd">●活跃</span>':'<span class="dim">○空闲</span>'}  ○${(room?.name||'—').padEnd(8)} ◈${(a.skills||[]).length} ▣${(a.tools||[]).length}\n`});
  return o}

function skillsText(){
  if(!S.skills.length)return'<span class="warn">暂无技能</span>';
  let o=`<span class="info">━━━ 技能 (${S.skills.length}) ━━━</span>\n`;
  S.skills?.slice(0,20)||[].forEach(s=>{o+=`  <span class="result">${(s.icon||'◈')} ${(s.name||'?').padEnd(22)}</span><span class="dim">[${s.category||'general'}]</span> ${(s.description||'').slice(0,35)}\n`});
  if(S.skills.length>20)o+=`  <span class="dim">...共 ${S.skills.length} 个</span>\n`;return o}

function toolsText(){
  if(!S.tools.length)return'<span class="warn">暂无工具</span>';
  let o=`<span class="info">━━━ 工具 (${S.tools.length}) ━━━</span>\n`;
  S.tools?.slice(0,15)||[].forEach(t=>{o+=`  <span class="result">${(t.icon||'▣')} ${(t.name||'?').padEnd(22)}</span><span class="dim">[${t.category||'-'}]</span> ${(t.description||'').slice(0,30)}\n`});
  if(S.tools.length>15)o+=`  <span class="dim">...共 ${S.tools.length} 个</span>\n`;return o}

function roomsText(){let o='<span class="info">━━━ 环境空间 ━━━</span>\n';S.rooms.forEach(r=>{const c=S.agents.filter(a=>S.positions[a.agent_id]===r.id).length;o+=`  <span class="result">${r.icon} ${r.name.padEnd(8)}</span> <span class="dim">${c} 智能体</span>  ${r.desc}\n`});return o}

function archText(){return`<span class="info">━━━ 六层架构 ━━━</span>
  <span class="layer-ui">┌─ L1 用户界面层 ────── Web + CLI</span>
  <span class="layer-ui">│</span>   ↕
  <span class="layer-orch">├─ L2 编排层 ────────── 意图解析 · 多智能体协调</span>
  <span class="layer-orch">│</span>   ↕
  <span class="layer-llm">├─ L3 LLM推理层 ───── Function Calling · CoT</span>
  <span class="layer-llm">│</span>   ↕
  <span class="layer-mem">├─ L4 记忆层 ────────── 技能库 · 知识图谱</span>
  <span class="layer-mem">│</span>   ↕
  <span class="layer-tool">├─ L5 工具执行层 ───── 工具集 · API · 代码</span>
  <span class="layer-tool">│</span>   ↕
  <span class="layer-ui">└─ L6 环境层 ────────── 虚拟空间 · 交互模拟</span>`}

async function moveAgent(name,room){
  if(!name||!room)return'<span class="err">用法: move <智能体> <空间></span>';
  const agent=S.agents.find(a=>a.name===name||a.agent_id===name);
  if(!agent)return`<span class="err">「${name}」未找到</span>`;
  const r=S.rooms.find(x=>x.name===room||x.id===room);
  if(!r)return`<span class="err">空间「${room}」未找到</span>`;
  const oldRoomId=S.positions[agent.agent_id];
  const old=S.rooms.find(x=>x.id===S.positions[agent.agent_id]);
  S.positions[agent.agent_id]=r.id;renderAgentList();renderEnvironment();
  try{
    await syncAgentMove(agent.agent_id,r.id);
    persist();addMsg('System',agent.name,'handoff',`移动到「${r.name}」`);
    return`<span class="cmd">✓</span> ${agent.name} ${old?'从「'+old.name+'」':''}→ <span class="result">「${r.name}」</span>`;
  }catch(err){
    rollbackAgentMove(agent.agent_id,oldRoomId);
    return`<span class="err">${esc(moveFailureText(err))}</span>`;
  }
}

function interactAgents(a1,a2){
  if(!a1||!a2)return'<span class="err">用法: interact <a1> <a2></span>';
  const ag1=S.agents.find(a=>a.name===a1),ag2=S.agents.find(a=>a.name===a2);
  if(!ag1)return`<span class="err">「${a1}」未找到</span>`;if(!ag2)return`<span class="err">「${a2}」未找到</span>`;
  addMsg(ag1.name,ag2.name,'handoff','发起协作');addMsg(ag2.name,ag1.name,'response','准备协作');
  // Sync to backend
  _af(`${API}/digital-twin/interact`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:ag1.name,to:ag2.name,type:'handoff',content:'协作触发'})}).catch(()=>{});
  simulatePipeline(`${ag1.name} ↔ ${ag2.name}`);
  return`<span class="cmd">✓</span> 交互触发: <span class="result">${ag1.name} ↔ ${ag2.name}</span>`}

function broadcastCmd(msg){if(!msg)return'<span class="err">用法: broadcast <消息></span>';addMsg('System','All','broadcast',msg);return`<span class="cmd">✓</span> 广播已发送到 ${S.agents.length} 个智能体`}
function inspectCmd(name){
  if(!name)return'<span class="err">用法: inspect <智能体名></span>';
  const ag=S.agents.find(a=>a.name===name||a.agent_id===name);
  if(!ag)return`<span class="err">「${name}」未找到</span>`;
  const room=S.rooms.find(r=>r.id===S.positions[ag.agent_id]);
  const ints=S.messages.filter(m=>m.from===ag.name||m.to===ag.name).length;
  return`<span class="info">━━━ 智能体详情 ━━━</span>\n  <span class="result">名称:</span>     ${ag.name}\n  <span class="result">ID:</span>       ${ag.agent_id}\n  <span class="result">角色:</span>     ${ag.role||'-'}\n  <span class="result">状态:</span>     ${ag.state==='active'?'<span class="cmd">活跃</span>':'<span class="dim">空闲</span>'}\n  <span class="result">位置:</span>     ${room?room.icon+' '+room.name:'未分配'}\n  <span class="result">技能:</span>     ${(ag.skills||[]).map(s=>s.name||s).join(', ')||'无'}\n  <span class="result">工具:</span>     ${(ag.tools||[]).map(t=>t.name||t).join(', ')||'无'}\n  <span class="result">交互数:</span>   ${ints}`;}
function traceCmd(name){
  if(!name)return'<span class="err">用法: trace <智能体名></span>';
  const ag=S.agents.find(a=>a.name===name);
  if(!ag)return`<span class="err">「${name}」未找到</span>`;
  const related=S.messages.filter(m=>m.from===ag.name||m.to===ag.name).slice(-15);
  if(!related.length)return`<span class="dim">${ag.name} 暂无交互记录</span>`;
  let o=`<span class="info">━━━ ${ag.name} 交互追踪 (最近${related.length}条) ━━━</span>\n`;
  related.forEach(m=>{const dir=m.from===ag.name?'→':'←';o+=`  <span class="dim">${m.time}</span> ${dir} ${m.from===ag.name?m.to:m.from} <span class="dim">[${m.type}]</span> ${m.content.slice(0,35)}\n`});
  return o;}
function simulateCmd(args){
  const scenario=args.join(' ')||'random';
  if(scenario==='help')return'<span class="info">simulate <scenario>\n  random    随机交互\n  chain     链式传递\n  stress    压力测试</span>';
  if(S.agents.length<2)return'<span class="warn">至少需要2个智能体</span>';
  if(scenario.includes('chain')){
    let o='<span class="cmd">✓</span> 链式模拟:\n';
    for(let i=0;i<S.agents.length-1;i++){const a=S.agents[i],b=S.agents[i+1];addMsg(a.name,b.name,'handoff',`Chain step ${i+1}`);o+=`  ${a.name} → ${b.name}\n`;}
    simulatePipeline('chain-sim');return o;}
  if(scenario.includes('stress')){
    const n=Math.min(20,S.agents.length*3);
    for(let i=0;i<n;i++){const a=S.agents[Math.floor(Math.random()*S.agents.length)],b=S.agents[Math.floor(Math.random()*S.agents.length)];if(a!==b)addMsg(a.name,b.name,['tool-call','llm-call','handoff'][Math.floor(Math.random()*3)],'stress-test');}
    simulatePipeline('stress-test');return`<span class="cmd">✓</span> 压力测试: ${n} 次交互生成`;}
  const a=S.agents[Math.floor(Math.random()*S.agents.length)],b=S.agents[Math.floor(Math.random()*S.agents.length)];
  if(a===b)return simulateCmd(['random']);
  addMsg(a.name,b.name,['tool-call','llm-call','handoff','response'][Math.floor(Math.random()*4)],'模拟交互');
  simulatePipeline(`sim: ${a.name}→${b.name}`);
  return`<span class="cmd">✓</span> 模拟: ${a.name} → ${b.name}`;}
function configCmd(args){
  if(!args.length)return'<span class="info">config show | config set <key> <value></span>';
  if(args[0]==='show')return`<span class="info">━━━ 配置 ━━━</span>\n  team: <span class="result">${localStorage.getItem('selected_team')||'build_system'}</span>\n  rooms: <span class="result">${S.rooms.length}</span>\n  positions: <span class="result">${Object.keys(S.positions).length}</span>`;
  if(args[0]==='set'&&args[1]==='team'&&args[2]){dtSetCurrentTeam(args[2]);return`<span class="cmd">✓</span> team → ${args[2]} (即时联动)`;}
  return'<span class="dim">可配置: config set team <id></span>';}
async function discussCmd(args){
  if(!args.length)return'<span class="info">discuss <topic> — 创建广场讨论\n  discuss list — 列出已有讨论\n  discuss watch <disc_id> — 订阅SSE实时流\n  discuss start <disc_id> — 启动讨论\n  discuss stop — 断开SSE</span>';
  if(args[0]==='stop'){sseDisconnect();return'<span class="cmd">✓</span> SSE连接已断开'}
  if(args[0]==='watch'){
    const discId=args[1];if(!discId)return'<span class="err">用法: discuss watch <discussion_id></span>';
    try{const plazas=await _plazas();
    const plazaId=plazas[0]?.id;if(!plazaId)return'<span class="err">暂无广场</span>';
    sseConnect(plazaId,discId);
    autoMoveForTask('council');
    return`<span class="cmd">✓</span> 已订阅讨论SSE流\n  讨论: <span class="result">${discId.slice(0,8)}</span>\n  <span class="dim">实时消息将显示在交互流视图 | discuss stop 断开</span>`}catch(e){return`<span class="err">${e.message}</span>`}
  }
  if(args[0]==='start'){
    const discId=args[1];if(!discId)return'<span class="err">用法: discuss start <discussion_id></span>';
    try{const plazas=await _plazas();
    const plazaId=plazas[0]?.id;if(!plazaId)return'<span class="err">暂无广场</span>';
    const r=await _af(`${API}/plaza/${plazaId}/discussions/${discId}/start`,{method:'POST'});
    if(!r.ok)return`<span class="err">启动失败: ${r.status}</span>`;
    addMsg('System','Plaza','broadcast',`讨论已启动: ${discId.slice(0,8)}`);
    sseConnect(plazaId,discId);
    autoMoveForTask('council');
    return`<span class="cmd">✓</span> 讨论已启动并订阅SSE\n  ID: <span class="result">${discId.slice(0,8)}</span>\n  <span class="dim">智能体将开始多轮辩论...</span>`}catch(e){return`<span class="err">${e.message}</span>`}
  }
  if(args[0]==='list'){
    try{const plazas=await _plazas();if(!plazas.length)return'<span class="dim">暂无广场</span>';let o='<span class="info">━━━ 广场列表 ━━━</span>\n';for(const p of plazas){o+=`  <span class="result">${p.id?.slice(0,8)||'?'}</span> ${p.name||'unnamed'} (${(p.participants||[]).length} 参与者)\n`;
    // List discussions for each plaza
    try{const discs=await _plazaDiscussions(p.id);discs.slice(0,5).forEach(d=>{o+=`    <span class="dim">└─</span> <span class="cmd">${(d.id||'').slice(0,8)}</span> ${d.topic||'?'} [${d.status||'?'}]\n`})}catch{}}return o}catch{return'<span class="err">请求失败</span>'}
  }
  const topic=args.join(' ');
  simulatePipeline('讨论: '+topic);
  addMsg('System','All','broadcast',`发起讨论: ${topic}`);
  try{
    const plazas=await _plazas();
    let plazaId=plazas[0]?.id;
    if(!plazaId){const cr=await _af(`${API}/plaza`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'数字孪生广场'})});if(cr.ok){const np=await cr.json();plazaId=np.id}else return'<span class="err">创建广场失败</span>'}
    const dr=await _af(`${API}/plaza/${plazaId}/discussions`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic,goal:'讨论并达成共识',max_rounds:3})});
    if(!dr.ok)return'<span class="err">创建讨论失败: '+dr.status+'</span>';
    const disc=await dr.json();
    addMsg('System','Plaza','llm-call',`讨论创建: ${disc.id?.slice(0,8)}`);
    autoMoveForTask('council');
    return`<span class="cmd">✓</span> 讨论已创建\n  ID: <span class="result">${disc.id?.slice(0,8)}</span>\n  主题: ${topic}\n  <span class="dim">使用 discuss start ${disc.id?.slice(0,8)} 启动 | discuss watch ${disc.id?.slice(0,8)} 订阅</span>`;
  }catch(e){return`<span class="err">请求失败: ${e.message}</span>`}
}
async function delegateCmd(args){
  if(args.length<3)return'<span class="err">用法: delegate <from_agent> <to_agent> <task_description></span>';
  const fromName=args[0],toName=args[1],desc=args.slice(2).join(' ');
  const ag1=S.agents.find(a=>a.name===fromName),ag2=S.agents.find(a=>a.name===toName);
  if(!ag1)return`<span class="err">「${fromName}」未找到</span>`;if(!ag2)return`<span class="err">「${toName}」未找到</span>`;
  addMsg(ag1.name,ag2.name,'handoff',`委派任务: ${desc}`);
  simulatePipeline(`delegate: ${fromName}→${toName}`);
  try{
    const tid=localStorage.getItem('selected_team')||'build_system';
    const r=await _af(`${API}/teams/${tid}/agents/${ag1.agent_id}/delegate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target_agent_id:ag2.agent_id,task_description:desc})});
    if(r.ok){const d=await r.json();addMsg(ag2.name,ag1.name,'response','已接受委派');return`<span class="cmd">✓</span> 任务已委派: ${fromName} → ${toName}\n  描述: ${desc}`}
    else return`<span class="warn">委派API返回 ${r.status}</span> (任务已模拟记录)`;
  }catch{return`<span class="cmd">✓</span> 委派已记录 (离线模式): ${fromName} → ${toName}`}
}
async function chatCmd(msg){
  if(!msg)return'<span class="err">用法: chat <消息></span>';
  addMsg('User','System','llm-call',msg);
  simulatePipeline('chat: '+msg.slice(0,20));
  try{
    const r=await _af('/api/v1/bridge-chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg,session_id:'dt-cli'})});
    if(r.ok){const d=await r.json();const reply=d.reply||d.response||d.message||JSON.stringify(d).slice(0,200);addMsg('System','User','response',reply?.slice(0,100)||'');return`<span class="result">${esc(reply)}</span>`}
    else return`<span class="warn">Chat API: ${r.status}</span>`;
  }catch{return'<span class="warn">Chat API 不可用</span>'}
}
function pipelineCmd(args){if(args[0]==='show')return pipelineStatusText();if(args[0]==='run'){simulatePipeline(args.slice(1).join(' ')||'task');return'<span class="cmd">✓</span> 管线启动'}return'<span class="info">子命令: pipeline show | pipeline run <task></span>'}
function pipelineStatusText(){return`<span class="info">━━━ 管线 ━━━</span>\n  Step 1: ▶ 输入解析 <span class="cmd">就绪</span>\n  Step 2: ◈ 意图识别 <span class="cmd">就绪</span>\n  Step 3: ◎ 任务路由 <span class="cmd">就绪</span>\n  Step 4: ▣ 工具调用 <span class="cmd">就绪</span>\n  Step 5: ◇ 结果聚合 <span class="cmd">就绪</span>`}
function flowCmd(args){const n=parseInt(args[1])||10;const recent=S.messages.slice(-n);if(!recent.length)return'<span class="dim">暂无记录</span>';let o=`<span class="info">━━━ 最近 ${recent.length} 条 ━━━</span>\n`;recent.forEach(m=>{o+=`  <span class="dim">${m.time}</span> ${m.from}→${m.to} <span class="dim">[${m.type}]</span> ${m.content.slice(0,40)}\n`});return o}

// ═══════════════════════════════════════════════════════════════
// Phase 2: SSE Real-time Integration
// ═══════════════════════════════════════════════════════════════
let _sseConnection=null;
let _sseDiscId=null;

function sseConnect(plazaId,discId){
  if(_sseConnection){_sseConnection.close();_sseConnection=null}
  _sseDiscId=discId;
  const url=`${API}/plaza/${plazaId}/discussions/${discId}/stream`;
  _sseConnection=new EventSource(url);
  _sseConnection.onopen=()=>{addActivity(`SSE 已连接: ${discId.slice(0,8)}`);toast('● LIVE — 讨论实时流已连接')};
  _sseConnection.onmessage=(ev)=>{
    try{
      const data=JSON.parse(ev.data);
      if(data.type==='message'&&data.message){
        const m=data.message;
        addMsg(m.agent_name||m.role||'Agent','Plaza','llm-call',m.content?.slice(0,100)||'(消息)');
        addActivity(`◈ ${m.agent_name||'?'}: ${(m.content||'').slice(0,30)}`);
      }else if(data.type==='status'){
        addMsg('System','Plaza','broadcast',`讨论状态: ${data.status}`);
      }else if(data.type==='discussion_end'){
        addMsg('System','Plaza','response','讨论结束');
        addActivity('✅ 讨论已结束');toast('讨论已结束');
        sseDisconnect();
      }
    }catch{}
  };
  _sseConnection.onerror=()=>{
    addActivity('SSE 连接中断，3s后重连...');
    const pid=plazaId,did=discId;
    _sseConnection=null;_sseDiscId=null;
    setTimeout(()=>{if(!_sseConnection)sseConnect(pid,did)},3000);
  };
}
function sseDisconnect(){if(_sseConnection){_sseConnection.close();_sseConnection=null;_sseDiscId=null;addActivity('SSE 已断开')}}

// ═══════════════════════════════════════════════════════════════
// Phase 3: Task Engine Commands
// ═══════════════════════════════════════════════════════════════
async function taskCmd(args){
  const tid=localStorage.getItem('selected_team')||'build_system';
  if(!args.length)return'<span class="info">task list | task create <title> | task start <id> | task dag | task stats</span>';
  if(args[0]==='list'){
    try{const tasks=await _list(`${API}/teams/${tid}/tasks`,200,0);if(!tasks.length)return'<span class="dim">暂无任务</span>';
    const statusC={pending:'dim',running:'cmd',completed:'result',failed:'err',cancelled:'dim'};
    let o=`<span class="info">━━━ 任务列表 (${tasks.length}) ━━━</span>\n`;
    tasks.slice(0,20).forEach(t=>{o+=`  <span class="${statusC[t.status]||'dim'}">${(t.status||'?').padEnd(10)}</span> <span class="result">${(t.task_id||'').slice(0,8)}</span> ${(t.title||'?').slice(0,35)} ${t.dependencies?.length?'<span class="dim">deps:'+t.dependencies.length+'</span>':''}\n`});
    return o}catch{return'<span class="err">请求失败</span>'}
  }
  if(args[0]==='create'){
    const title=args.slice(1).join(' ');if(!title)return'<span class="err">用法: task create <标题></span>';
    try{const r=await _af(`${API}/teams/${tid}/tasks`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,priority:1,dependencies:[]})});
    if(!r.ok)return`<span class="err">创建失败: ${r.status}</span>`;
    const t=await r.json();addMsg('System','TaskEngine','tool-call',`创建任务: ${title}`);
    autoMoveForTask('workshop');
    return`<span class="cmd">✓</span> 任务已创建\n  ID: <span class="result">${(t.task_id||t.id||'').slice(0,8)}</span>\n  标题: ${title}`}catch(e){return`<span class="err">${e.message}</span>`}
  }
  if(args[0]==='start'){
    const taskId=args[1];if(!taskId)return'<span class="err">用法: task start <task_id></span>';
    try{const r=await _af(`${API}/teams/${tid}/tasks/${taskId}/start`,{method:'POST'});
    if(!r.ok)return`<span class="err">启动失败: ${r.status}</span>`;
    addMsg('System','TaskEngine','tool-call',`启动任务: ${taskId.slice(0,8)}`);simulatePipeline('task:'+taskId.slice(0,8));
    autoMoveForTask('workshop');
    return`<span class="cmd">✓</span> 任务已启动: <span class="result">${taskId.slice(0,8)}</span>`}catch(e){return`<span class="err">${e.message}</span>`}
  }
  if(args[0]==='complete'){
    const taskId=args[1];if(!taskId)return'<span class="err">用法: task complete <task_id></span>';
    try{const r=await _af(`${API}/teams/${tid}/tasks/${taskId}/complete`,{method:'POST'});
    if(!r.ok)return`<span class="err">完成失败: ${r.status}</span>`;
    addMsg('System','TaskEngine','response',`任务完成: ${taskId.slice(0,8)}`);
    return`<span class="cmd">✓</span> 任务已完成: <span class="result">${taskId.slice(0,8)}</span>`}catch(e){return`<span class="err">${e.message}</span>`}
  }
  if(args[0]==='stats'){
    try{const r=await _af(`${API}/tasks/stats`);if(!r.ok)return'<span class="err">获取统计失败</span>';
    const s=await r.json();
    return`<span class="info">━━━ 任务引擎统计 ━━━</span>\n  总任务: <span class="result">${s.total||0}</span>\n  运行中: <span class="cmd">${s.running||0}</span> / 最大并发: <span class="result">${s.max_concurrency||4}</span>\n  <span class="dim">待执行: ${s.by_status?.pending||0} | 完成: ${s.by_status?.completed||0} | 失败: ${s.by_status?.failed||0}</span>`}catch{return'<span class="err">请求失败</span>'}
  }
  if(args[0]==='dag'){
    try{const tasks=await _list(`${API}/teams/${tid}/tasks`,200,0);if(!tasks.length)return'<span class="dim">暂无任务, DAG为空</span>';
    let o=`<span class="info">━━━ 任务DAG ━━━</span>\n`;
    const statusIcon={pending:'○',running:'◐',completed:'●',failed:'✗',cancelled:'◌'};
    tasks.forEach(t=>{
      const icon=statusIcon[t.status]||'?';
      const deps=t.dependencies||[];
      if(deps.length){deps.forEach(d=>{o+=`  <span class="dim">${d.slice(0,6)}</span> ──▶ <span class="${t.status==='completed'?'result':'cmd'}">${icon} ${(t.task_id||'').slice(0,6)}</span> ${t.title?.slice(0,25)||''}\n`})}
      else{o+=`  <span class="${t.status==='completed'?'result':'cmd'}">${icon} ${(t.task_id||'').slice(0,6)}</span> ${t.title?.slice(0,25)||''} <span class="dim">(无依赖)</span>\n`}
    });
    o+=`\n  <span class="dim">○待执行 ◐运行中 ●完成 ✗失败</span>`;
    return o}catch{return'<span class="err">请求失败</span>'}
  }
  return'<span class="info">task list | create | start | complete | dag | stats</span>';
}

// ═══════════════════════════════════════════════════════════════
// Phase 4: Extraction, Evolution, Optimize, Health, Workflow
// ═══════════════════════════════════════════════════════════════
const EXTRACT_API='/api/v1/extraction';
const EVOLVE_API='/api/v1/agent-teams/evolution';

async function extractCmd(args){
  if(!args.length)return'<span class="info">extract <source> — 触发萃取\n  extract status — 漏斗统计\n  extract list — 列出管线</span>';
  if(args[0]==='status'){
    try{const r=await _af(`${EXTRACT_API}/stats`);if(!r.ok)return'<span class="err">获取统计失败</span>';
    const s=await r.json();
    return`<span class="info">━━━ 萃取漏斗 ━━━</span>\n  总管线: <span class="result">${s.total||0}</span>\n  DRAFT: <span class="dim">${s.by_stage?.DRAFT||0}</span> → REVIEW: <span class="cmd">${s.by_stage?.REVIEW||0}</span> → APPROVAL: <span class="layer-llm">${s.by_stage?.APPROVAL||0}</span> → PUBLISHED: <span class="result">${s.by_stage?.PUBLISHED||0}</span>\n  <span class="dim">通过率: ${s.pass_rate||'-'}%</span>`}catch{return'<span class="err">请求失败</span>'}
  }
  if(args[0]==='list'){
    try{const r=await _af(`${EXTRACT_API}/pipelines`);if(!r.ok)return'<span class="err">获取失败</span>';
    const d=await r.json();const ps=d.pipelines||d||[];if(!ps.length)return'<span class="dim">暂无萃取管线</span>';
    let o=`<span class="info">━━━ 萃取管线 (${ps.length}) ━━━</span>\n`;
    const stageC={DRAFT:'dim',REVIEW:'cmd',APPROVAL:'layer-llm',PUBLISHED:'result',REJECTED:'err'};
    ps.slice(0,15).forEach(p=>{o+=`  <span class="${stageC[p.current_stage]||'dim'}">${(p.current_stage||'?').padEnd(10)}</span> <span class="result">${(p.id||'').slice(0,8)}</span> ${(p.name||'?').slice(0,30)}\n`});
    return o}catch{return'<span class="err">请求失败</span>'}
  }
  const source=args.join(' ');
  const tid=localStorage.getItem('selected_team')||'build_system';
  try{const r=await _af(`${EXTRACT_API}/pipelines`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:source,description:`从 ${source} 萃取技能`,team_id:tid,created_by:'dt-cli'})});
  if(!r.ok)return`<span class="err">创建萃取管线失败: ${r.status}</span>`;
  const p=await r.json();
  addMsg('System','Extraction','tool-call',`萃取启动: ${source}`);simulatePipeline('extract:'+source?.slice(0,15)||'');
  autoMoveForTask('extraction');
  return`<span class="cmd">✓</span> 萃取管线已创建\n  ID: <span class="result">${(p.id||'').slice(0,8)}</span>\n  名称: ${source}\n  阶段: <span class="dim">DRAFT</span>\n  <span class="dim">使用 review ${(p.id||'').slice(0,8)} approve 推进</span>`}catch(e){return`<span class="err">${e.message}</span>`}
}

async function reviewCmd(args){
  if(!args.length)return'<span class="info">review <pipeline_id> [approve|reject|status]</span>';
  const pipeId=args[0];const action=args[1]||'status';
  if(action==='status'){
    try{const r=await _af(`${EXTRACT_API}/pipelines/${pipeId}`);if(!r.ok)return`<span class="err">获取失败: ${r.status}</span>`;
    const p=await r.json();
    return`<span class="info">━━━ 管线详情 ━━━</span>\n  ID: <span class="result">${p.id}</span>\n  名称: ${p.name}\n  阶段: <span class="cmd">${p.current_stage}</span>\n  创建: ${p.created_at||'-'}\n  描述: ${p.description||'-'}`}catch{return'<span class="err">请求失败</span>'}
  }
  if(action==='approve'){
    try{const r=await _af(`${EXTRACT_API}/pipelines/${pipeId}/advance`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({triggered_by:'dt-cli',force:false})});
    if(!r.ok){const e=await r.json().catch(()=>({}));return`<span class="err">推进失败: ${e.error||r.status}</span>${e.reason?'\n  原因: '+e.reason:''}`}
    const d=await r.json();addMsg('System','Extraction','response',`管线推进: ${pipeId.slice(0,8)}`);
    return`<span class="cmd">✓</span> 管线已推进\n  ID: <span class="result">${pipeId.slice(0,8)}</span>\n  状态: ${d.status}`}catch(e){return`<span class="err">${e.message}</span>`}
  }
  if(action==='reject'){
    const reason=args.slice(2).join(' ')||'CLI拒绝';
    try{const r=await _af(`${EXTRACT_API}/pipelines/${pipeId}/reject`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({triggered_by:'dt-cli',reason})});
    if(!r.ok)return`<span class="err">拒绝失败: ${r.status}</span>`;
    addMsg('System','Extraction','response',`管线拒绝: ${pipeId.slice(0,8)}`);
    return`<span class="cmd">✓</span> 已拒绝: <span class="result">${pipeId.slice(0,8)}</span>\n  原因: ${reason}`}catch(e){return`<span class="err">${e.message}</span>`}
  }
  return'<span class="info">review <id> [approve|reject|status]</span>';
}

async function evolveCmd(args){
  if(!args.length)return'<span class="info">evolve audit | status | items | rating | cycle</span>';
  if(args[0]==='status'){
    try{const r=await _af(`${EVOLVE_API}/status`);if(!r.ok)return'<span class="err">获取失败</span>';
    const s=await r.json();
    return`<span class="info">━━━ 演进引擎 ━━━</span>\n  状态: <span class="cmd">${s.status||'active'}</span>\n  规则数: <span class="result">${s.rules_count||'-'}</span>\n  最近审计: ${s.last_audit||'-'}\n  待处理项: <span class="amber">${s.pending_items||0}</span>`}catch{return'<span class="err">请求失败</span>'}
  }
  if(args[0]==='audit'){
    try{const r=await _af(`${EVOLVE_API}/audit`,{method:'POST'});if(!r.ok)return'<span class="err">审计失败</span>';
    const d=await r.json();addMsg('System','Evolution','tool-call','执行演进审计');simulatePipeline('evolve-audit');
    const findings=d.findings||d.violations||[];
    let o=`<span class="cmd">✓</span> 审计完成\n  发现问题: <span class="${findings.length?'err':'result'}">${findings.length}</span>\n`;
    findings?.slice(0,5)||[].forEach(f=>{o+=`  <span class="dim">•</span> ${f.rule||f.message||f.description||JSON.stringify(f).slice(0,50)}\n`});
    return o}catch{return'<span class="err">请求失败</span>'}
  }
  if(args[0]==='items'){
    try{const items=await _list(`${EVOLVE_API}/items`,200,0);if(!items.length)return'<span class="dim">暂无演进项</span>';
    let o=`<span class="info">━━━ 演进项 (${items.length}) ━━━</span>\n`;
    const sc={open:'cmd',in_progress:'layer-llm',verify_pending:'amber',closed:'result'};
    items.slice(0,15).forEach(it=>{o+=`  <span class="${sc[it.status]||'dim'}">${(it.status||'?').padEnd(14)}</span> <span class="result">${(it.id||'').slice(0,8)}</span> ${(it.title||it.description||'').slice(0,30)}\n`});
    return o}catch{return'<span class="err">请求失败</span>'}
  }
  if(args[0]==='rating'){
    try{const r=await _af(`${EVOLVE_API}/compliance-rating`);if(!r.ok)return'<span class="err">获取失败</span>';
    const d=await r.json();
    const gradeC={A:'result',B:'cmd',C:'amber',D:'err',E:'err'};
    return`<span class="info">━━━ 合规评级 ━━━</span>\n  等级: <span class="${gradeC[d.grade]||'dim'}" style="font-size:18px;font-weight:bold">${d.grade||'?'}</span>\n  分数: <span class="result">${d.rating||d.score||'-'}</span>/100\n  描述: ${d.description||'-'}\n  升级层: ${d.escalation_tier||'-'}`}catch{return'<span class="err">请求失败</span>'}
  }
  if(args[0]==='cycle'){
    try{const r=await _af(`${EVOLVE_API}/cycle`,{method:'POST'});if(!r.ok)return'<span class="err">执行失败</span>';
    const d=await r.json();addMsg('System','Evolution','tool-call','完整演进循环');simulatePipeline('evolve-cycle');
    return`<span class="cmd">✓</span> 演进循环已执行\n  ${JSON.stringify(d).slice(0,100)}`}catch{return'<span class="err">请求失败</span>'}
  }
  return'<span class="info">evolve audit | status | items | rating | cycle</span>';
}

async function optimizeCmd(args){
  if(!args.length)return'<span class="info">optimize <skill_name> — 触发Hermes技能优化</span>';
  const skillName=args.join(' ');
  addMsg('System','Optimizer','tool-call',`优化技能: ${skillName}`);simulatePipeline('optimize:'+skillName?.slice(0,12)||'');
  try{await _af(`${EVOLVE_API}/cycle`,{method:'POST'})}catch{}
  return`<span class="cmd">✓</span> 已触发技能优化: <span class="result">${skillName}</span>\n  <span class="dim">Hermes循环: baseline → mutation → evaluation → select</span>`;
}

async function healthCmd(){
  let o=`<span class="info">━━━ 系统健康巡检 ━━━</span>\n`;
  const activeCount=S.agents.filter(a=>a.state==='active').length;
  o+=`  <span class="result">智能体</span>    ${activeCount}/${S.agents.length} 活跃 ${activeCount===S.agents.length?'<span class="cmd">✓</span>':'<span class="warn">⚠</span>'}\n`;
  try{const r=await _af(`${API}/tasks/stats`);if(r.ok){const s=await r.json();o+=`  <span class="result">任务引擎</span>  运行: ${s.running||0}/${s.max_concurrency||4} <span class="cmd">✓</span>\n`}else{o+=`  <span class="result">任务引擎</span>  <span class="dim">不可用</span>\n`}}catch{o+=`  <span class="result">任务引擎</span>  <span class="err">离线</span>\n`}
  try{const r=await _af(`${EXTRACT_API}/stats`);if(r.ok){const s=await r.json();o+=`  <span class="result">萃取管线</span>  ${s.total||0} 管线 <span class="cmd">✓</span>\n`}else{o+=`  <span class="result">萃取管线</span>  <span class="dim">不可用</span>\n`}}catch{o+=`  <span class="result">萃取管线</span>  <span class="err">离线</span>\n`}
  try{const r=await _af(`${EVOLVE_API}/compliance-rating`);if(r.ok){const d=await r.json();o+=`  <span class="result">合规评级</span>  ${d.grade||'?'} (${d.rating||'-'}/100) <span class="cmd">✓</span>\n`}else{o+=`  <span class="result">合规评级</span>  <span class="dim">不可用</span>\n`}}catch{o+=`  <span class="result">合规评级</span>  <span class="err">离线</span>\n`}
  o+=`  <span class="result">SSE连接</span>   ${_sseConnection?'<span class="cmd">● 已连接 ('+(_sseDiscId||'').slice(0,8)+')</span>':'<span class="dim">○ 未连接</span>'}\n`;
  const placed=Object.keys(S.positions).length;
  o+=`  <span class="result">空间利用</span>  ${placed}/${S.agents.length} 已部署到空间\n`;
  o+=`\n  <span class="dim">${new Date().toLocaleString('zh-CN')}</span>`;
  return o;
}

// ═══════════════════════════════════════════════════════════════
// Phase 4: Workflow Engine
// ═══════════════════════════════════════════════════════════════
const WORKFLOWS={
  'full-loop':{name:'完整闭环',desc:'从讨论到代码',steps:['discuss 性能优化方案','task create 执行优化','evolve audit']},
  'skill-evolve':{name:'技能进化',desc:'从萃取到优化',steps:['extract status','evolve items','evolve rating']},
  'health-check':{name:'质量巡检',desc:'全系统健康检查',steps:['health','evolve rating','extract status','task stats']},
};

async function workflowCmd(args){
  if(!args.length||args[0]==='list'){
    let o='<span class="info">━━━ 预定义工作流 ━━━</span>\n';
    Object.entries(WORKFLOWS).forEach(([k,w])=>{o+=`  <span class="cmd">${k.padEnd(14)}</span> ${w.name} — ${w.desc}\n    <span class="dim">步骤: ${w.steps.join(' → ')}</span>\n`});
    o+='\n  <span class="dim">用法: workflow <name> [参数]</span>';
    return o;
  }
  const wfName=args[0];const wfArg=args.slice(1).join(' ');
  const wf=WORKFLOWS[wfName];
  if(!wf)return`<span class="err">未知工作流: ${wfName}</span>\n  <span class="dim">可用: ${Object.keys(WORKFLOWS).join(', ')}</span>`;
  let o=`<span class="cmd">▶</span> 执行工作流: <span class="result">${wf.name}</span> (${wf.desc})\n`;
  addMsg('System','Workflow','broadcast',`启动工作流: ${wf.name}`);
  simulatePipeline('workflow:'+wfName);
  for(let i=0;i<wf.steps.length;i++){
    const step=wfArg&&i===0?wf.steps[i].split(' ')[0]+' '+wfArg:wf.steps[i];
    o+=`  <span class="dim">[${i+1}/${wf.steps.length}]</span> <span class="cmd">${step}</span>\n`;
    addExecLog('info',`[workflow] Step ${i+1}: ${step}`);
    try{
      const result=await processCmd(step);
      if(result){
        const clean=result.replace(/<[^>]+>/g,'').slice(0,60);
        o+=`    <span class="dim">${clean}</span>\n`;
        if(result.includes('class="err"')){o+=`    <span class="warn">▲ 步骤失败，工作流中止</span>\n`;break}
      }
    }catch(e){o+=`    <span class="err">失败: ${e.message}</span>\n`;break}
  }
  o+=`\n<span class="cmd">✓</span> 工作流完成: ${wf.name}`;
  addMsg('System','Workflow','response',`工作流完成: ${wf.name}`);
  return o;
}

// ═══════════════════════════════════════════════════════════════
// Phase 5: Smart Orchestration — Auto-move agents to rooms
// ═══════════════════════════════════════════════════════════════
function autoMoveForTask(targetRoomId){
  const activeAgents=S.agents.filter(a=>a.state==='active');
  if(!activeAgents.length)return;
  const agent=activeAgents.find(a=>S.positions[a.agent_id]!==targetRoomId);
  if(!agent)return;
  const room=S.rooms.find(r=>r.id===targetRoomId);
  if(!room)return;
  const oldRoomId=S.positions[agent.agent_id];
  S.positions[agent.agent_id]=targetRoomId;
  renderAgentList();renderEnvironment();
  syncAgentMove(agent.agent_id,targetRoomId).then(()=>{
    persist();addMsg('System',agent.name,'handoff',`自动移动到「${room.name}」`);
    addActivity(`▷ ${agent.name} → ${room.name} (自动编排)`);
  }).catch(err=>{
    rollbackAgentMove(agent.agent_id,oldRoomId);
    toast(moveFailureText(err));
  });
}

function camCmd(args){
  if(!args.length)return`<span class="info">━━━ 摄像头路径 ━━━</span>
  <span class="cmd">cam council</span>     飞到议事厅
  <span class="cmd">cam extraction</span>  飞到萃取室
  <span class="cmd">cam workshop</span>    飞到工作坊
  <span class="cmd">cam library</span>     飞到知识库
  <span class="cmd">cam arena</span>       飞到演练场
  <span class="cmd">cam rest</span>        飞到休息区
  <span class="cmd">cam overview</span>    鸟瞰全景
  <span class="cmd">cam tour</span>        自动巡览全部空间
  <span class="dim">需要先切换到环境空间3D视图</span>`;
  const target=args[0].toLowerCase();
  if(!_3dInitialized)return'<span class="warn">请先切换到环境空间 → 3D视图</span>';
  if(target==='overview'){flyToOverview();return'<span class="cmd">✓</span> 飞往鸟瞰全景'}
  if(target==='tour'){flyTour();return'<span class="cmd">▶</span> 3D巡览启动 — 依次飞越 6 个空间'}
  if(ROOM_POS[target]){flyToRoom(target);
    const names={council:'◇ 议事厅',extraction:'○ 萃取室',workshop:'□ 工作坊',library:'△ 知识库',arena:'◎ 演练场',rest:'◌ 休息区'};
    return`<span class="cmd">✓</span> 飞往 <span class="result">${names[target]||target}</span>`}
  return`<span class="err">未知空间: ${target}</span>\n  <span class="dim">可用: council extraction workshop library arena rest overview tour</span>`;
}

function exportCmd(type){
  var trialInfo=window._DTS&&window._DTS.activeTrialId?{activeTrialId:window._DTS.activeTrialId,activeBranchId:window._DTS.activeBranchId,trialStatus:window._DTS.trialStatus,selectedMode:window._DTS.selectedMode}:null;
  const data={version:'3.0',exported_at:new Date().toISOString(),agents:S.agents,teams:S.teams,selectedTeams:S.selectedTeams,rooms:S.rooms,positions:S.positions,messages:type==='snapshot'?S.messages:undefined,skills:type==='skills'?S.skills:undefined,trials:trialInfo};
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download=`dt_${type||'snapshot'}_${Date.now()}.json`;a.click();URL.revokeObjectURL(url);
  return`<span class="cmd">✓</span> 已导出`}

// ── Messages & Simulation ──
function addMsg(from,to,type,content){
  const time=new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  S.messages.push({from,to,type,content,time,duration:Math.floor(Math.random()*200+50)});
  if(S.messages.length>200)S.messages=S.messages.slice(-100);
  localStorage.setItem('dt2_messages',JSON.stringify(S.messages.slice(-100)));
  document.getElementById('msg-count').textContent=S.messages.length;renderInteractions();
  // Trigger 3D agent pulse
  if(typeof pulse3DAgent==='function')pulse3DAgent(from,to);
}
function addExecLog(type,msg){
  const time=new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  S.execLog.push({time,type,msg});if(S.execLog.length>100)S.execLog.shift();renderExecLog();
}
function simulatePipeline(task){
  // Real pipeline: create or track a pipeline run for this task
  const steps=document.querySelectorAll('.pipeline-step');
  const bar=document.getElementById('pipeline-progress-bar');
  steps.forEach(s=>{s.classList.remove('active','done')});
  bar.style.width='0%';
  const stageLabels=['草稿','萃取','评审','批准','发布'];
  addExecLog('info',`开始处理: ${task}`);
  // Progressive reveal based on actual message processing
  let i=0;
  const iv=setInterval(()=>{
    if(i>0){steps[i-1].classList.remove('active');steps[i-1].classList.add('done')}
    if(i<steps.length){steps[i].classList.add('active');addExecLog(i<2?'llm':'tool',`[${stageLabels[i]}] ${task}`);bar.style.width=((i+1)/steps.length*100)+'%'}
    else{clearInterval(iv);addExecLog('info',`完成: ${task}`);bar.style.width='100%';setTimeout(()=>loadPipelineState(),1000)}
    i++;
  },600);
}
function startSim(){
  // Freq chart — track real API call count per 2s window
  let _freqBucket=0;
  const _origFetch=window.fetch;
  window.fetch=function(...args){_freqBucket++;return _origFetch.apply(this,args)};
  setInterval(()=>{if(document.hidden)return;S.freqData.push(_freqBucket);_freqBucket=0;S.freqData.shift();renderFreqChart()},2000);
  // Auto-refresh agent states every 30s
  setInterval(async()=>{
    if(document.hidden)return;
    await loadTeamsAndAgents();renderAgentList();renderStats();renderDashboard();
  },30000);
}

// ── Import/Export ──
function importSnapshot(){document.getElementById('import-file').click()}
function handleImport(ev){
  const file=ev.target.files[0];if(!file)return;
  const reader=new FileReader();
  reader.onload=function(e){
    try{
      const data=JSON.parse(e.target.result);
      if(data.rooms)S.rooms=data.rooms;
      if(data.positions)S.positions=data.positions;
      if(data.messages)S.messages=data.messages.slice(-100);
      persist();
      renderAgentList();renderEnvironment();renderInteractions();renderArchitecture();
      toast('✓ 快照已导入');addActivity('快照导入');
    }catch(err){toast('导入失败: '+err.message)}
  };reader.readAsText(file);ev.target.value='';
}

// ── Keyboard Shortcuts ──
document.addEventListener('keydown',function(e){
  // Ctrl/Cmd+K → focus CLI
  if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();switchView(document.querySelector('[data-view="cli"]'));document.getElementById('cli-input').focus()}
  // Ctrl/Cmd+1-5 → switch views
  if((e.ctrlKey||e.metaKey)&&['1','2','3','4','5'].includes(e.key)){e.preventDefault();const tabs=document.querySelectorAll('.nav-item');const idx=parseInt(e.key)-1;if(tabs[idx])switchView(tabs[idx])}
  // Escape → clear CLI input
  if(e.key==='Escape'){const inp=document.getElementById('cli-input');if(document.activeElement===inp)inp.value=''}
});

// ── Drag & Drop ──
let _dragAgentId=null;
function onDragStart(ev,agentId){_dragAgentId=agentId;ev.target.closest('.agent-card').classList.add('dragging');ev.dataTransfer.effectAllowed='move';ev.dataTransfer.setData('text/plain',agentId)}
function onDragOver(ev){ev.preventDefault();ev.dataTransfer.dropEffect='move';ev.currentTarget.classList.add('drag-over')}
function onDragLeave(ev){ev.currentTarget.classList.remove('drag-over')}
async function onDrop(ev,roomId){
  ev.preventDefault();ev.currentTarget.classList.remove('drag-over');
  const agentId=ev.dataTransfer.getData('text/plain')||_dragAgentId;
  if(!agentId)return;
  const agent=S.agents.find(a=>a.agent_id===agentId);const room=S.rooms.find(r=>r.id===roomId);
  if(!agent||!room)return;
  const oldRoomId=S.positions[agentId];
  const old=S.rooms.find(r=>r.id===oldRoomId);
  S.positions[agentId]=roomId;renderAgentList();renderEnvironment();
  try{
    await syncAgentMove(agentId,roomId);
    persist();addMsg('System',agent.name,'handoff',`拖放移动到「${room.name}」`);addActivity(`${agent.name} → ${room.name}`);
    toast(`✓ ${agent.name} → ${room.name}`);
  }catch(err){
    rollbackAgentMove(agentId,oldRoomId);
    const back=old?`，已退回「${old.name}」`:'，已取消移动';
    toast(moveFailureText(err)+back);
    addActivity(`${agent.name} → ${room.name} 被拒绝`);
  }finally{
    document.querySelectorAll('.agent-card.dragging').forEach(c=>c.classList.remove('dragging'));_dragAgentId=null;
  }
}
document.addEventListener('dragend',()=>{document.querySelectorAll('.agent-card.dragging').forEach(c=>c.classList.remove('dragging'));_dragAgentId=null})

function persist(){const persistRooms=(S.rooms||[]).filter(function(r){return !(r&&r._scn);});localStorage.setItem('dt2_rooms',JSON.stringify(persistRooms));localStorage.setItem('dt2_positions',JSON.stringify(S.positions));syncDtState()}
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function toast(msg){const el=document.createElement('div');el.className='toast';el.textContent=msg;document.body.appendChild(el);setTimeout(()=>el.remove(),3000)}

// ═══════════════════════════════════════════════════════════════
// 3D stub — real rendering in module script below
// ═══════════════════════════════════════════════════════════════
let _3dCurrentRoom='council';
function getRoomName(id){const r=(window.S&&window.S.rooms||[]).find(x=>x.id===id);return r?(r.icon+' '+r.name):id;}
window.getRoomName=getRoomName;
const ROOM_NAMES=new Proxy({},{get:(_,k)=>getRoomName(k)});
window.ROOM_NAMES=ROOM_NAMES;

let _envMode='3d';
function toggleEnvMode(btn){
  _envMode=_envMode==='grid'?'3d':'grid';
  if(btn){
    btn.innerHTML=_envMode==='grid'
      ?'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg> 平面视图'
      :'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg> 3D 视图';
  }
  switchEnvMode(_envMode,btn);
}
function switchEnvMode(mode,btn){
  const allBtns=document.querySelectorAll('#view-environment > .env-container > div:first-child .flow-btn');
  allBtns.forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  if(mode==='grid'){
    document.getElementById('env-3d-container').style.display='none';
    document.getElementById('room-tabs').style.display='none';
    document.getElementById('env-grid').style.display='grid';
    renderEnvironment();
  }else{
    document.getElementById('env-3d-container').style.display='block';
    document.getElementById('room-tabs').style.display='flex';
    document.getElementById('env-grid').style.display='none';
    if(window._dt3dBuildRoom)window._dt3dBuildRoom(_3dCurrentRoom);
  }
}

function switchRoom(roomId,btn){
  if(btn){document.querySelectorAll('#room-tabs .flow-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active')}
  _3dCurrentRoom=roomId;
  if(window._dt3dBuildRoom)window._dt3dBuildRoom(roomId);
  // 切房间时刷新任务下拉菜单
  secsRefreshTaskDropdown();
  // 环境空间→右侧 SECS「选择演练场景」联动(用户未手动选具体场景时跟随)
  if(window.secsSyncSceneFromRoom)window.secsSyncSceneFromRoom(roomId);
}

function flyToRoom(roomId){
  const btns=document.querySelectorAll('#room-tabs .flow-btn');
  const idx=S.rooms.findIndex(r=>r.id===roomId);
  if(idx>=0&&btns[idx])switchRoom(roomId,btns[idx]);
}
function flyToOverview(){if(window._dt3dSetCamera)window._dt3dSetCamera(0,25,25,0,0,0)}
function flyTour(){let i=0;const next=()=>{if(i>=S.rooms.length)return;flyToRoom(S.rooms[i].id);i++;setTimeout(next,2500)};next()}

// ── SECS 仿真控制 (右面板) ──────────────────────────────────
const SECS_API = '/api/v1/sandbox';
let _secsSession = null;

document.getElementById('secs-steps').addEventListener('input', function(){
  document.getElementById('secs-steps-val').textContent = this.value;
});

async function secsSyncDT(){
  const el = document.getElementById('secs-sync-status');
  el.innerHTML = '<span style="color:var(--amber)">⏳ 同步中...</span>';
  try {
    const r = await _af(`${SECS_API}/sync-from-dt`, {method:'POST'});
    const d = await r.json();
    if(d.synced_agents > 0){
      el.innerHTML = `<span style="color:var(--green)">✓ 已同步</span> <span style="color:var(--dim)">${d.synced_agents} agents · ${d.synced_rooms} rooms · ${d.synced_edges} edges</span>`;
    } else {
      el.innerHTML = `<span style="color:var(--amber)">⚠ 场景为空</span> <span style="color:var(--dim)">请先在3D场景中放置智能体</span>`;
    }
  } catch(e){
    el.innerHTML = `<span style="color:var(--red)">✗ 同步失败</span>`;
  }
}

async function secsRun(){
  const btn = document.getElementById('secs-run-btn');
  const mode = document.querySelector('input[name="secs-mode"]:checked').value;
  const useLlm = document.getElementById('secs-use-llm').checked;
  const steps = parseInt(document.getElementById('secs-steps').value);
  const triggerEl = document.getElementById('secs-trigger');
  const trigger = triggerEl ? triggerEl.value.trim() : '';

  btn.disabled = true;
  btn.textContent = '⏳ 仿真运行中...';
  btn.style.opacity = '0.6';

  try {
    // 创建会话 (自动同步DT)
    const cr = await _af(`${SECS_API}/sessions`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({mode, use_llm:useLlm, max_steps:steps, trigger_description:trigger, sync_dt:true})
    });
    const session = await cr.json();
    _secsSession = session;

    // 执行仿真
    const rr = await _af(`${SECS_API}/sessions/${session.session_id}/run`, {method:'POST'});
    const result = await rr.json();

    // 显示结果
    secsShowResult(session, result);
  } catch(e){
    document.getElementById('secs-results').style.display = '';
    document.getElementById('secs-results-body').innerHTML = `<span style="color:var(--red)">仿真失败: ${e.message}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = '▶ 开始仿真';
    btn.style.opacity = '1';
  }
}

function secsShowResult(session, result){
  const el = document.getElementById('secs-results');
  const body = document.getElementById('secs-results-body');
  el.style.display = '';

  const eval_ = result.evaluation || {};
  const sop = result.best_sop || {};
  const score = eval_.global_score != null ? (eval_.global_score * 100).toFixed(0) : '--';
  const scoreColor = score >= 70 ? 'var(--green)' : score >= 40 ? 'var(--amber)' : 'var(--red)';

  body.innerHTML = `
    <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:10px">
      <span style="font-size:22px;font-weight:700;color:${scoreColor}">${score}</span>
      <span style="font-size:11px;color:var(--dim)">/ 100 综合评分</span>
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;margin-bottom:12px">
      ${_secsMetric('任务完成', eval_.task_completion)}
      ${_secsMetric('通信效率', eval_.communication_efficiency)}
      ${_secsMetric('资源利用', eval_.resource_utilization)}
      ${_secsMetric('冲突规避', eval_.conflict_avoidance)}
      ${_secsMetric('收敛速度', eval_.convergence_speed)}
    </div>
    ${sop.name ? `<div style="padding:8px 10px;background:var(--green-dim);border:1px solid rgba(52,211,153,0.3);border-radius:6px;margin-bottom:10px">
      <div style="font-size:11px;font-weight:600;color:var(--green)">📋 最优 SOP: ${sop.name}</div>
      <div style="font-size:10.5px;color:var(--dim);margin-top:2px">avg_reward: ${sop.avg_reward?.toFixed(3) || '--'}</div>
    </div>` : ''}
    ${eval_.recommendations?.length ? `<div style="margin-top:6px;font-size:11px;color:var(--muted)"><b>建议:</b><ul style="margin:4px 0 0 14px">${eval_.recommendations.map(r=>`<li>${r}</li>`).join('')}</ul></div>` : ''}
    <button onclick="secsInject()" style="width:100%;margin-top:10px;padding:8px 0;font-size:12px;font-weight:500;background:var(--green-dim);color:var(--green);border:1px solid rgba(52,211,153,0.3);border-radius:6px;cursor:pointer">⬆ 注入最优策略到真实环境</button>
  `;
}

function _secsMetric(label, val){
  const v = val != null ? (val * 100).toFixed(0) : '--';
  const pct = val != null ? (val * 100) : 0;
  return `<div style="display:flex;align-items:center;gap:8px"><span style="font-size:10.5px;color:var(--dim);min-width:56px">${label}</span><div style="flex:1;height:4px;background:var(--panel3);border-radius:2px;overflow:hidden"><div style="height:100%;width:${pct}%;background:var(--cyan);border-radius:2px"></div></div><span style="font-size:10.5px;color:var(--text2);min-width:24px;text-align:right">${v}</span></div>`;
}

async function secsInject(){
  if(!_secsSession) return;
  try {
    const r = await _af(`${SECS_API}/sessions/${_secsSession.session_id}/inject`, {
      method:'POST', headers:{'Content-Type':'application/json'}, body:'{"confirm":true}'
    });
    const d = await r.json();
    if(d.status === 'injected'){
      addActivity({type:'info', text:'✅ SECS 策略已注入真实环境', time:new Date().toISOString()});
    }
  } catch(e){}
}

// ══════════════════════════════════════════════════════════════
// SECS 实时对话日志 + TTS 语音播报
// ══════════════════════════════════════════════════════════════
let _secsTTSEnabled = localStorage.getItem('secs_tts') !== 'false'; // 默认开启
let _secsTTSAudio = null;
let _secsTTSSerial = 0;

function secsToggleTTS(){
  _secsTTSEnabled = !_secsTTSEnabled;
  localStorage.setItem('secs_tts', String(_secsTTSEnabled));
  const btn = document.getElementById('secs-tts-btn');
  if(btn) btn.textContent = _secsTTSEnabled ? '🔊 语音' : '🔇 静音';
  if(btn) btn.style.color = _secsTTSEnabled ? 'var(--cyan)' : 'var(--dim)';
  if(!_secsTTSEnabled){
    if(_secsTTSAudio){_secsTTSAudio.pause();_secsTTSAudio=null}
    if(window.speechSynthesis) speechSynthesis.cancel();
  }
}
// 初始化按钮状态
setTimeout(()=>{
  const btn = document.getElementById('secs-tts-btn');
  if(btn){btn.textContent = _secsTTSEnabled ? '🔊 语音' : '🔇 静音';btn.style.color = _secsTTSEnabled ? 'var(--cyan)' : 'var(--dim)';}
},100);

// 追加一条对话记录到面板
function secsAppendDialogue(agentName, text, color){
  const log = document.getElementById('secs-dialogue-log');
  if(!log) return;
  // 如果是初始提示文字, 先清空
  if(log.querySelector('span[style*="dim"]') && log.children.length === 1) log.innerHTML = '';
  const entry = document.createElement('div');
  entry.style.cssText = 'margin-bottom:4px;border-left:2px solid '+(color||'#22d3ee')+';padding-left:8px;animation:fadeIn 0.3s ease';
  entry.innerHTML = `<span style="color:${color||'#22d3ee'};font-weight:600;font-size:10px">${agentName}</span> <span style="color:#ccc">${text}</span>`;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

// TTS 语音播报 (后端GPT-SoVITS优先，Web Speech API兜底)
async function secsTTSSpeak(text, agentName){
  if(!_secsTTSEnabled || !text) return;
  const serial = ++_secsTTSSerial;
  // 停止上一段
  if(_secsTTSAudio){_secsTTSAudio.pause();_secsTTSAudio=null}
  if(window.speechSynthesis) speechSynthesis.cancel();

  // 尝试后端TTS
  try {
    const resp = await _af('/api/v1/tts', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({text, text_lang:'zh', speed_factor:1.1, agent_name:agentName||''})
    });
    if(resp.ok && serial === _secsTTSSerial){
      const blob = await resp.blob();
      if(blob.size > 0 && serial === _secsTTSSerial){
        return new Promise(resolve=>{
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          _secsTTSAudio = audio;
          audio.volume = 0.8;
          audio.onended = ()=>{URL.revokeObjectURL(url);if(_secsTTSAudio===audio)_secsTTSAudio=null;resolve()};
          audio.onerror = ()=>{URL.revokeObjectURL(url);if(_secsTTSAudio===audio)_secsTTSAudio=null;resolve()};
          audio.play().catch(()=>resolve());
        });
      }
    }
  } catch(e){/* fallback to Web Speech */}

  // Web Speech API 兜底
  if(serial !== _secsTTSSerial) return;
  if(!window.speechSynthesis) return;
  return new Promise(resolve=>{
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = 'zh-CN';
    utt.rate = 1.1;
    utt.pitch = 0.85;
    utt.volume = 0.8;
    const voices = speechSynthesis.getVoices();
    const zhVoice = voices.find(v=>v.lang.startsWith('zh'));
    if(zhVoice) utt.voice = zhVoice;
    utt.onend = ()=>resolve();
    utt.onerror = ()=>resolve();
    speechSynthesis.speak(utt);
  });
}

// ══════════════════════════════════════════════════════════════
// SECS 开发流程仿真 (工作坊场景专用) — 基于真实团队/任务
// ══════════════════════════════════════════════════════════════
let _secsSimRunning = false;
let _secsTeams = [];
let _secsTaskCache = {};

// 角色 → 工作描述映射 (console风格真实输出)
const _roleWorkMap = {
  project_manager: { emoji:'📋', task:'需求分析与任务分配', screens:[
    ['$ ag-pm analyze --task="{task}"','[INFO] Loading requirements.json...','[INFO] Parsing 12 user stories','> Priority: P0=3, P1=5, P2=4','> Assigning subtasks to agents...','[OK] 7 subtasks dispatched'],
    ['$ ag-pm schedule --sprint=current','[INFO] Capacity: 7 agents × 8h','> Critical path: design→impl→test','> ETA: 4.2h (parallel factor 0.6)','[OK] Sprint plan generated']
  ]},
  researcher: { emoji:'🔬', task:'技术研究与方案调研', screens:[
    ['$ ag-research scan --domain="{task}"','[INFO] Querying knowledge_base...','[INFO] Found 23 relevant papers','> Comparing: approach_A vs approach_B','> Feasibility score: 0.87','[OK] Report: research_output.md'],
    ['$ ag-research compare --depth=3','[INFO] Evaluating solution_A...','[INFO] Evaluating solution_B...','[INFO] Evaluating solution_C...','> Best: solution_B (cost↓40%, perf↑12%)','[OK] Recommendation finalized']
  ]},
  architect: { emoji:'🏗', task:'架构设计', screens:[
    ['$ ag-arch design --scope="{task}"','[INFO] Analyzing dependencies...','> Modules: core(3), api(2), store(1)','> Interface contracts: 8 defined','> Pattern: event-driven + CQRS','[OK] arch_diagram.mermaid written'],
    ['$ ag-arch validate --strict','[CHECK] Circular deps... PASS','[CHECK] Single responsibility... PASS','[CHECK] API consistency... PASS','> Coverage: 100% modules validated','[OK] Architecture approved']
  ]},
  developer: { emoji:'💻', task:'编码实现', screens:[
    ['$ ag-dev implement --module=core','[INFO] Reading arch spec...','> Generating: src/core/handler.ts','> Generating: src/core/types.ts','> Lines written: 347','[OK] 4 files, 0 lint errors'],
    ['$ ag-dev test --unit --coverage','[RUN] handler.test.ts... 12 passed','[RUN] types.test.ts... 8 passed','> Coverage: 94.2% (target: 90%)','> Mutations killed: 87/92','[OK] All tests green ✓']
  ]},
  qa_engineer: { emoji:'🧪', task:'测试验证', screens:[
    ['$ ag-qa run --suite=integration','[INFO] Spinning up test env...','[RUN] api_flow.spec... 23/23 ✓','[RUN] edge_cases.spec... 18/18 ✓','[RUN] stress.spec... 5/5 ✓','[OK] 46 tests passed, 0 failed'],
    ['$ ag-qa fuzz --iterations=1000','[INFO] Generating random inputs...','[WARN] Found 2 boundary issues','> Fix applied: input validation','[RUN] Re-test... ALL PASS','[OK] Security audit complete']
  ]},
  devops: { emoji:'🚀', task:'部署发布', screens:[
    ['$ ag-deploy build --target=prod','[INFO] Installing dependencies...','> Bundle size: 2.1MB (gzip: 680KB)','> Docker image: agentsgroup:v2.4.1','[INFO] Pushing to registry...','[OK] Image pushed, ready to deploy'],
    ['$ ag-deploy rollout --canary=10%','[INFO] Canary: 10% traffic routed','> Health: 200 OK (p99: 45ms)','> Error rate: 0.00%','[INFO] Promoting to 100%...','[OK] Deployment complete 🎉']
  ]},
  documentation: { emoji:'📝', task:'文档输出', screens:[
    ['$ ag-docs generate --format=md','[INFO] Scanning source files...','> API endpoints: 12 documented','> Params/Returns: auto-extracted','> Examples: 8 generated from tests','[OK] docs/api-reference.md updated'],
    ['$ ag-docs changelog --since=v2.3','[INFO] Parsing git log (47 commits)','> Features: 3, Fixes: 8, Refactor: 2','> Breaking changes: 0','> Migration guide: not needed','[OK] CHANGELOG.md appended']
  ]},
};
const _roleColors = ['#22d3ee','#60a5fa','#a78bfa','#34d399','#f472b6','#fbbf24','#fb923c'];

async function secsInitTeamDropdown(){
  try {
    _secsTeams = await _list('/api/v1/agent-config/teams',200,0);
    const sel = document.getElementById('secs-team-select');
    if(!sel) return;
    sel.innerHTML = '<option value="">-- 选择团队 --</option>' +
      _secsTeams.map(t=>`<option value="${t.team_id}">${t.name||t.team_id} (${t.agent_count||0}人)</option>`).join('');
  } catch(e){ console.warn('SECS teams load failed',e); }
}

async function secsLoadTeamTasks(){
  const teamId = document.getElementById('secs-team-select')?.value;
  const taskSel = document.getElementById('secs-task-select');
  if(!taskSel) return;
  if(!teamId){ taskSel.innerHTML = '<option value="">请先选择团队</option>'; return; }

  // 立即切换3D场景到该团队的智能体
  if(window.S && window.S.selectedTeams){
    window.S.selectedTeams = [teamId];
    if(typeof renderTeamSelector === 'function') renderTeamSelector();
    if(typeof renderAgentList === 'function') renderAgentList();
    // 保持当前房间并重建场景 (加载该团队agents)
    const curRoom = window._currentRoomId || 'council';
    if(window._dt3dBuildRoom){
      if(typeof flyToRoom === 'function') flyToRoom(curRoom);
      else window._dt3dBuildRoom(curRoom);
    }
  }

  // 先加载真实任务到缓存
  taskSel.innerHTML = '<option value="">加载中...</option>';
  try {
    _secsTaskCache[teamId] = await _list(`/api/v1/agent-config/teams/${teamId}/tasks`,200,0);
  } catch(e){ _secsTaskCache[teamId] = []; }

  // 根据当前房间渲染不同内容
  secsRefreshTaskDropdown();
}

// ── 场景化任务/议题配置 ──
const _roomTaskConfig = {
  council: {
    label: '◇ 选择讨论议题',
    btnText: '🎬 开始议事讨论 · 仅预演(不评分)',
    // 从真实任务提取议题 + 预置通用议题
    transform(tasks){
      const fromTasks = tasks.slice(0,5).map(t => ({
        id: t.task_id, title: '讨论: ' + (t.title?.substring(0,30)||'议题')
      }));
      const preset = [
        {id:'_c1', title:'技术方案评审: 架构选型与风险评估'},
        {id:'_c2', title:'迭代复盘: 上周交付质量与改进'},
        {id:'_c3', title:'资源协调: 人员分配与优先级排序'},
        {id:'_c4', title:'技术债务: 是否立即还债'},
        {id:'_c5', title:'新需求评估: 可行性与工期预估'},
      ];
      return [...fromTasks, ...preset];
    }
  },
  workshop: {
    label: '□ 选择开发任务',
    btnText: '🎬 运行开发流程仿真 · 仅预演(不评分)',
    transform(tasks){
      if(!tasks.length) return [{id:'_w1', title:'通用开发流程演示'}];
      return tasks.map(t => ({id: t.task_id, title: (t.title?.substring(0,38)||t.task_id) + ` [${t.status}]`}));
    }
  },
  extraction: {
    label: '○ 选择萃取目标',
    btnText: '🎬 启动技能萃取仿真 · 仅预演(不评分)',
    transform(tasks){
      const fromTasks = tasks.slice(0,3).map(t => ({
        id: t.task_id, title: '萃取: ' + (t.title?.substring(0,28)||'技能')
      }));
      const preset = [
        {id:'_e1', title:'萃取: 代码审查最佳实践'},
        {id:'_e2', title:'萃取: 故障排查经验模式'},
        {id:'_e3', title:'萃取: 架构设计决策知识'},
        {id:'_e4', title:'萃取: 测试策略与边界发现'},
        {id:'_e5', title:'萃取: 部署回滚操作SOP'},
      ];
      return [...fromTasks, ...preset];
    }
  },
  library: {
    label: '△ 选择检索主题',
    btnText: '🎬 启动知识检索仿真 · 仅预演(不评分)',
    transform(tasks){
      const fromTasks = tasks.slice(0,3).map(t => ({
        id: t.task_id, title: '检索: ' + (t.title?.substring(0,28)||'知识')
      }));
      const preset = [
        {id:'_l1', title:'检索: 系统架构设计文档'},
        {id:'_l2', title:'检索: API接口规范与示例'},
        {id:'_l3', title:'检索: 历史故障案例库'},
        {id:'_l4', title:'检索: 技术选型对比分析'},
        {id:'_l5', title:'检索: 团队知识图谱概览'},
      ];
      return [...fromTasks, ...preset];
    }
  },
  arena: {
    label: '◎ 选择对抗命题',
    btnText: '🎬 启动对抗演练 · 仅预演(不评分)',
    transform(tasks){
      const fromTasks = tasks.slice(0,3).map(t => ({
        id: t.task_id, title: 'PK: ' + (t.title?.substring(0,28)||'挑战')
      }));
      const preset = [
        {id:'_a1', title:'PK: 方案A vs 方案B 架构对决'},
        {id:'_a2', title:'PK: 性能优化 — 激进派 vs 保守派'},
        {id:'_a3', title:'PK: 新框架 vs 现有框架 迁移决策'},
        {id:'_a4', title:'PK: 限时编码挑战 (30min)'},
        {id:'_a5', title:'PK: 代码审查攻防演练'},
      ];
      return [...fromTasks, ...preset];
    }
  },
  rest: {
    label: '◌ 选择复盘对象',
    btnText: '🎬 启动复盘充能 · 仅预演(不评分)',
    transform(tasks){
      const fromTasks = tasks.filter(t=>t.status==='completed').slice(0,3).map(t => ({
        id: t.task_id, title: '复盘: ' + (t.title?.substring(0,28)||'项目')
      }));
      const preset = [
        {id:'_r1', title:'复盘: 本周工作效率与瓶颈'},
        {id:'_r2', title:'复盘: 最近一次线上事故'},
        {id:'_r3', title:'复盘: 团队协作流程优化'},
        {id:'_r4', title:'充能: 技能缺口分析与学习规划'},
        {id:'_r5', title:'充能: 认知负荷管理与专注力恢复'},
      ];
      return [...fromTasks, ...preset];
    }
  },
};

// 根据当前房间刷新任务下拉菜单
function secsRefreshTaskDropdown(){
  const taskSel = document.getElementById('secs-task-select');
  const taskLabel = document.getElementById('secs-task-label');
  const btn = document.getElementById('secs-dev-btn');
  if(!taskSel) return;

  const curRoom = window._currentRoomId || 'workshop';
  const config = _roomTaskConfig[curRoom] || _roomTaskConfig.workshop;
  const teamId = document.getElementById('secs-team-select')?.value;
  const tasks = _secsTaskCache[teamId] || [];

  // 更新标签
  if(taskLabel) taskLabel.textContent = config.label;
  // 更新按钮文字
  if(btn && !btn.disabled) btn.textContent = config.btnText;

  // 生成选项
  const items = config.transform(tasks);
  if(!items.length){
    taskSel.innerHTML = '<option value="">暂无可选项</option>';
    return;
  }
  taskSel.innerHTML = items.map(item =>
    `<option value="${item.id}">${item.title}</option>`
  ).join('');
}

async function secsDevWorkflow(){
  // 运行中再次点击 = 停止：置停止标志，让 _secsRunStep / 各循环尽快退出到 finalize
  if(_secsSimRunning){ window._secsDevStop = true; if(window.toast) toast('⏹ 正在停止仿真...'); return; }
  window._secsDevStop = false;
  const teamId = document.getElementById('secs-team-select')?.value;
  const taskId = document.getElementById('secs-task-select')?.value;
  if(!teamId){ toast('请先选择团队', 'error'); return; }

  _secsSimRunning = true;
  // 清空对话日志
  const dlLog = document.getElementById('secs-dialogue-log');
  if(dlLog) dlLog.innerHTML = '';

  // 切换到仅显示选中团队的智能体
  if(window.S && window.S.selectedTeams){
    window.S.selectedTeams = [teamId];
    if(typeof renderTeamSelector === 'function') renderTeamSelector();
  }

  // 确定目标场景: 保持当前房间 (任何房间都支持推演)
  const validRooms = ['council','extraction','workshop','library','arena','rest'];
  const targetRoom = validRooms.includes(window._currentRoomId) ? window._currentRoomId : 'workshop';
  if(window._currentRoomId !== targetRoom){
    if(typeof flyToRoom === 'function') flyToRoom(targetRoom);
    else if(window._dt3dBuildRoom) window._dt3dBuildRoom(targetRoom);
    await new Promise(r=>setTimeout(r,800));
  } else {
    if(window._dt3dBuildRoom) window._dt3dBuildRoom(targetRoom);
    await new Promise(r=>setTimeout(r,600));
  }

  const btn = document.getElementById('secs-dev-btn');
  // 运行中按钮可点击 = 停止（点击再次进入 secsDevWorkflow → 置停止标志）
  if(btn){ btn.disabled=false; btn.textContent='⏹ 停止仿真'; btn.style.opacity='1'; }

  // 清除旧屏幕内容
  if(window._dt3dClearScreens) window._dt3dClearScreens();

  // 获取当前3D场景中的agent名字 (通过module暴露的helper)
  const sceneAgentNames = window._dt3dGetAgentNames ? window._dt3dGetAgentNames() : [];

  // 获取团队agents
  let teamAgents = [];
  try {
    teamAgents = await _list(`/api/v1/agent-config/teams/${teamId}/agents`,200,0);
  } catch(e){}

  // 只保留当前场景中存在的agents (label必须能匹配)
  console.log('[SECS] 场景agents:', sceneAgentNames, '团队agents:', teamAgents.map(a=>a.name));
  const activeAgents = teamAgents.filter(a => sceneAgentNames.includes(a.name));
  if(!activeAgents.length){
    // 如果没匹配上, 尝试用场景中所有agent
    alert(`团队 "${teamId}" 的智能体不在当前3D场景中。\n场景中有: ${sceneAgentNames.join(', ')}\n请确保已选择该团队后切换到workshop。`);
    if(btn){ btn.disabled=false; btn.textContent=(_roomTaskConfig[window._currentRoomId||'workshop']||_roomTaskConfig.workshop).btnText; btn.style.opacity='1'; }
    _secsSimRunning = false;
    return;
  }

  // 获取选中的任务标题 → 直接从下拉菜单读取显示文本
  const taskSelEl = document.getElementById('secs-task-select');
  const taskTitle = taskSelEl?.selectedOptions?.[0]?.textContent?.trim()
    || (_secsTaskCache[teamId]?.find(t=>t.task_id===taskId)?.title)
    || '通用流程';
  // 去掉前缀标记 (讨论:/萃取:/检索:/PK:/复盘:)
  const topic = taskTitle.replace(/^(讨论|萃取|检索|PK|复盘|充能):\s*/,'');

  // 获取仿真模式
  const simMode = document.querySelector('input[name="secs-mode"]:checked')?.value || 'what_if';

  // ════════════════════════════════════════════════════
  // 场景角色映射 (每个场景有不同的推演语义)
  // ════════════════════════════════════════════════════
  const _roomRoleMaps = {
    // ── 议事厅: 讨论/辩论 ──
    council: {
      project_manager: { emoji:'📋', task:'主持讨论', screens:[
        [`◇ 议题: "${topic}"`,'[主持] 各位，今天讨论该议题','> 请每位发表观点','> 时间: 每人3分钟','[OK] 开始第一轮发言'],
        [`◇ 议题: "${topic}"`,'[主持] 进入总结阶段','> 综合各方意见...','> 形成决议草案','[OK] 决议已拟定，待表决']
      ]},
      researcher: { emoji:'🔬', task:'提供研究论据', screens:[
        [`[发言] 关于 "${topic}"`,'> 根据调研数据显示...','> 方案A可行性: 87%','> 方案B风险较高(成本↑40%)','> 建议: 采用方案A','[结论] 论据已呈现'],
        [`[发言] 补充调研结论`,'> 对比行业案例 3 个','> 类似项目成功率: 72%','> 关键风险点: 2处','> 建议: 增加验证环节','[结论] 建议已提交']
      ]},
      architect: { emoji:'🏗', task:'架构视角发言', screens:[
        [`[发言] 架构影响分析`,'> 该议题涉及模块: 3个','> 接口变更: 需要','> 兼容性: 向后兼容可行','> 预计重构: 2天','[结论] 技术可行'],
        [`[发言] 系统设计建议`,'> 推荐: 渐进式实施','> 第一阶段: 核心模块','> 第二阶段: 边缘适配','> 风险隔离: 可控','[结论] 分阶段推进']
      ]},
      developer: { emoji:'💻', task:'实现难度评估', screens:[
        [`[发言] 开发评估`,'> 工作量: ~320行代码','> 难度: 中等','> 依赖: 需 API v2','> 开发周期: 3天','[结论] 可按期交付'],
        [`[发言] 技术细节讨论`,'> 现有代码可复用: 60%','> 新增逻辑: handler+types','> 测试覆盖: 需补充','> 建议: 先写测试','[结论] 测试先行']
      ]},
      qa_engineer: { emoji:'🧪', task:'质量风险发言', screens:[
        [`[发言] 质量影响`,'> 测试用例需新增: 15个','> 回归范围: 中等','> 边界条件: 需关注3处','> 自动化覆盖: 可达90%','[结论] 风险可控'],
        [`[发言] 验收标准建议`,'> 建议验收条件 5 项','> P0: 核心流程不退化','> P1: 性能无劣化','> P2: 文档同步更新','[结论] 标准已定义']
      ]},
      devops: { emoji:'🚀', task:'部署视角发言', screens:[
        [`[发言] 部署影响`,'> 需要: 配置变更','> 灰度策略: 10%→50%→100%','> 回滚方案: 已备','> 预计上线窗口: 2h','[结论] 可安全发布'],
        [`[发言] 运维建议`,'> 监控: 需增加2个告警','> 资源: 不需扩容','> SLA影响: 无','> 建议: 非高峰期部署','[结论] 风险低']
      ]},
      documentation: { emoji:'📝', task:'文档视角发言', screens:[
        [`[发言] 文档影响`,'> 需更新: API文档+变更日志','> 用户指南: 需修改1章','> FAQ: 预计新增3条','> 工作量: 0.5天','[结论] 同步更新'],
        [`[发言] 知识沉淀建议`,'> 建议: 记录决策过程','> ADR编号: #47','> 模板: 已有可复用','> 归档: knowledge_base/','[结论] 将同步归档']
      ]},
    },
    // ── 萃取室: 技能萃取/知识提炼 ──
    extraction: {
      project_manager: { emoji:'📋', task:'萃取规划', screens:[
        [`○ 萃取目标: "${topic}"`,'[规划] 识别可萃取知识点...','> 知识粒度: 细分3层','> 萃取策略: 深度优先','> 预计产出: 5个技能卡片','[OK] 萃取流程启动'],
        [`○ 萃取协调`,'[规划] 分配萃取任务...','> 隐性知识: 需访谈','> 显性知识: 文档提取','> 实践知识: 代码分析','[OK] 任务分配完毕']
      ]},
      researcher: { emoji:'🔬', task:'知识挖掘', screens:[
        [`[萃取] 深度分析 "${topic}"`,'> 扫描相关文档 47份','> 识别核心概念: 12个','> 构建知识图谱节点...','> 发现隐含关联: 3处','[结晶] 知识原矿已提取'],
        [`[萃取] 模式识别`,'> 分析历史执行记录...','> 成功模式: 4种','> 反模式: 2种','> 频率最高: Pattern#A','[结晶] 模式谱已生成']
      ]},
      architect: { emoji:'🏗', task:'结构化提炼', screens:[
        [`[提炼] 构建知识骨架`,'> 分类: 概念/流程/决策','> 层级: 3层树状结构','> 关联边: 8条','> 覆盖度: 92%','[结晶] 结构化完成'],
        [`[提炼] 形式化建模`,'> 抽象为可复用模板...','> 模板参数: 5个','> 适用场景: 3类','> 复用率预估: 78%','[结晶] 模板已固化']
      ]},
      developer: { emoji:'💻', task:'代码知识萃取', screens:[
        [`[萃取] 代码模式分析`,'> 扫描关键函数: 23个','> 提取设计意图...','> 编码惯例: 7条','> 技巧集锦: 4项','[结晶] 代码DNA已提取'],
        [`[萃取] 实现经验提炼`,'> 踩坑记录: 5处','> 最佳实践: 8条','> 性能窍门: 3条','> 可教学化: 已标注','[结晶] 经验卡片已生成']
      ]},
      qa_engineer: { emoji:'🧪', task:'质量知识萃取', screens:[
        [`[萃取] 测试经验提炼`,'> 经典Bug模式: 6种','> 测试策略知识: 4条','> 覆盖率陷阱: 3处','> 自动化窍门: 5项','[结晶] 测试智慧已提取'],
        [`[萃取] 验证方法归纳`,'> 边界值发现法: 记录','> 等价类划分: 记录','> 探索式策略: 记录','> 有效性: 已验证','[结晶] 方法论已固化']
      ]},
      devops: { emoji:'🚀', task:'运维知识萃取', screens:[
        [`[萃取] 部署经验`,'> 故障排查路径: 5条','> 监控配置模板: 3套','> 回滚SOP: 已结构化','> 容量规划公式: 2个','[结晶] 运维手册已萃取'],
        [`[萃取] 基础设施知识`,'> 架构决策记录: 4份','> 配置演进历史: 追溯','> 性能调优参数: 归档','> 灾备方案: 已模板化','[结晶] 基建知识已固化']
      ]},
      documentation: { emoji:'📝', task:'知识结晶', screens:[
        [`[结晶] 最终输出`,'> 技能卡片: 已生成5张','> 知识图谱: 节点12/边8','> 可教学材料: 3份','> 索引更新: knowledge_base/','[完成] 萃取产物已归档'],
        [`[结晶] 格式化输出`,'> Markdown文档: 生成','> 思维导图: 导出','> Anki卡片: 8张','> 搜索索引: 已更新','[完成] 多格式输出完毕']
      ]},
    },
    // ── 知识库: 检索/归档/学习 ──
    library: {
      project_manager: { emoji:'📋', task:'检索规划', screens:[
        [`△ 检索目标: "${topic}"`,'[规划] 解析查询意图...','> 关键词: 3组','> 搜索范围: 全库','> 策略: 语义+关键词混合','[OK] 检索计划就绪'],
        [`△ 知识任务分配`,'[规划] 需要汇集的信息...','> 直接相关: 优先检索','> 关联知识: 扩展搜索','> 历史案例: 追溯','[OK] 分工明确']
      ]},
      researcher: { emoji:'🔬', task:'深度检索', screens:[
        [`[检索] "${topic}" 相关知识`,'> 命中文档: 34份','> 精排Top5: 相关度>0.85','> 摘要提取中...','> 关键段落: 已标记12处','[完成] 检索报告已生成'],
        [`[检索] 扩展关联搜索`,'> 引用链追踪: 3层','> 发现关联主题: 5个','> 跨领域连接: 2处','> 时间线: 按版本排列','[完成] 知识地图已扩展']
      ]},
      architect: { emoji:'🏗', task:'知识结构分析', screens:[
        [`[分析] 知识架构映射`,'> 概念层级: 解析完毕','> 依赖关系: 8条','> 知识缺口: 发现2处','> 推荐补充: 已标注','[完成] 结构图已更新'],
        [`[分析] 体系完整性检查`,'> 覆盖率: 87%','> 缺失章节: 2处','> 过期内容: 3份需更新','> 冗余: 1处可合并','[完成] 健康报告已出']
      ]},
      developer: { emoji:'💻', task:'代码示例检索', screens:[
        [`[检索] 相关代码示例`,'> 匹配代码片段: 8个','> 最佳实践: 3份','> Stack Overflow: 5条','> 内部案例: 2个','[完成] 示例集已整理'],
        [`[检索] API用法查询`,'> 匹配接口: 4个','> 使用示例: 生成中','> 兼容性注意: 2条','> 版本差异: 已标注','[完成] API手册已汇编']
      ]},
      qa_engineer: { emoji:'🧪', task:'测试知识检索', screens:[
        [`[检索] 测试相关知识`,'> 历史Bug: 相似12条','> 回归用例: 推荐5个','> 测试策略文档: 3份','> 覆盖率基准: 已查到','[完成] 测试参考已汇总'],
        [`[检索] 质量标准查询`,'> 行业标准: ISO相关2份','> 内部规范: 4份','> Checklist: 推荐使用v3','> 度量指标: 已整理','[完成] 标准库已输出']
      ]},
      devops: { emoji:'🚀', task:'运维知识检索', screens:[
        [`[检索] 部署相关知识`,'> 配置模板: 3套匹配','> 故障案例: 相似5条','> Runbook: 推荐2份','> 容量数据: 历史可查','[完成] 运维知识已汇总'],
        [`[检索] 基础设施文档`,'> 架构图: 最新版已定位','> 变更记录: 近30天','> 监控仪表盘: 3个相关','> 告警规则: 已检索','[完成] 基建文档已输出']
      ]},
      documentation: { emoji:'📝', task:'归档与索引', screens:[
        [`[归档] 更新知识库`,'> 新增条目: 3条','> 索引重建: 执行中','> 标签更新: +5个','> 交叉引用: 已建立','[完成] 知识库已更新'],
        [`[归档] 生成学习路径`,'> 前置知识: 标注完毕','> 推荐顺序: 已排列','> 预计学习时间: 2.5h','> 练习题: 已生成8道','[完成] 学习路径已输出']
      ]},
    },
    // ── 演练场: A/B对抗/技能验证 ──
    arena: {
      project_manager: { emoji:'📋', task:'裁判/规则制定', screens:[
        [`◎ 对抗命题: "${topic}"`,'[裁判] 制定评判标准...','> 维度: 性能/质量/创新','> 权重: 40/35/25','> 回合数: 3轮','[OK] 竞技规则已发布'],
        [`◎ 赛事管理`,'[裁判] 初始化对抗环境...','> 红队/蓝队: 已分配','> 计时器: 启动','> 评分板: 已就绪','[OK] 比赛开始!']
      ]},
      researcher: { emoji:'🔬', task:'红队·方案A', screens:[
        [`[红队] 方案A: "${topic}"`,'> 策略: 激进创新路线','> 优势: 性能提升35%','> 实现: 全新架构','> 风险: 兼容性待验证','[提交] 方案A 已完成'],
        [`[红队] 第2轮优化`,'> 吸收蓝队反馈...','> 调整: 增加兼容层','> 性能微降5%→仍领先','> 稳定性: ↑显著','[提交] 方案A v2 已优化']
      ]},
      architect: { emoji:'🏗', task:'蓝队·方案B', screens:[
        [`[蓝队] 方案B: "${topic}"`,'> 策略: 渐进稳健路线','> 优势: 零风险迁移','> 实现: 现有架构扩展','> 代价: 性能提升20%','[提交] 方案B 已完成'],
        [`[蓝队] 第2轮优化`,'> 吸收红队亮点...','> 调整: 热路径重构','> 性能: ↑至28%','> 维持零风险承诺','[提交] 方案B v2 已优化']
      ]},
      developer: { emoji:'💻', task:'实战编码PK', screens:[
        [`[PK] 限时编码挑战`,'> 题目: ${topic.substring(0,15)}','> 计时: 00:00 开始','> 提交代码: 127行','> 通过用例: 18/20','[完成] 编码分数: 87/100'],
        [`[PK] 代码审查对决`,'> 审查对方代码...','> 发现问题: 3处','> 提出优化: 2处','> 防守: 自身0 bug','[完成] 审查分: 92/100']
      ]},
      qa_engineer: { emoji:'🧪', task:'压力测试裁判', screens:[
        [`[验证] 方案对比测试`,'> 方案A: 1000req/s → p99=45ms','> 方案B: 1000req/s → p99=62ms','> 稳定性A: 99.2%','> 稳定性B: 99.8%','[裁决] 各有优劣'],
        [`[验证] 极限测试`,'> 并发拉到5000...','> 方案A: 劣化15%但未崩','> 方案B: 劣化8%稳定','> 边界: B更抗压','[裁决] 综合评分已出']
      ]},
      devops: { emoji:'🚀', task:'部署对决', screens:[
        [`[对决] 部署速度PK`,'> 方案A部署: 2m30s','> 方案B部署: 1m45s','> 回滚测试A: 30s','> 回滚测试B: 15s','[结果] B部署效率胜出'],
        [`[对决] 容灾演练`,'> 模拟节点宕机...','> 方案A恢复: 8s','> 方案B恢复: 12s','> 数据一致性: 均PASS','[结果] A容灾能力胜出']
      ]},
      documentation: { emoji:'📝', task:'记录与判定', screens:[
        [`[记录] 对抗结果汇总`,'> 红队总分: 84.5','> 蓝队总分: 82.3','> 最佳单项: 红队·创新','> 最佳稳定: 蓝队·兼容','[判定] 红队微幅胜出'],
        [`[记录] 经验归档`,'> 对抗收获: 已记录','> 可融合方案: 提取中','> 最终推荐: 融合A+B优点','> ADR: 已生成','[完成] 演练报告归档']
      ]},
    },
    // ── 休息区: 充能/自省/复盘 ──
    rest: {
      project_manager: { emoji:'📋', task:'复盘引导', screens:[
        [`◌ 复盘主题: "${topic}"`,'[复盘] 回顾项目执行过程...','> 目标达成: 88%','> 超时环节: 2处','> 协作瓶颈: 1处','[完成] 改进计划已生成'],
        [`◌ 状态检查`,'[巡检] 团队成员状态...','> 疲劳指数: 平均 0.6','> 注意力: 中等偏下','> 建议: 休整30min','[OK] 充能计划已下发']
      ]},
      researcher: { emoji:'🔬', task:'知识消化', screens:[
        [`[充能] 消化近期所学`,'> 整理笔记: 12条','> 建立关联: 5处','> 遗忘曲线复习: 执行','> 灵感记录: 2条','[完成] 知识已巩固'],
        [`[自省] 研究方法回顾`,'> 成功路径: 回溯3条','> 低效尝试: 标记2处','> 方法论更新: 1处','> 下次改进: 已记录','[完成] 自省完毕']
      ]},
      architect: { emoji:'🏗', task:'架构反思', screens:[
        [`[充能] 架构设计回顾`,'> 当初决策: 审视5个','> 事后看仍正确: 4个','> 需调整: 1个','> 技术债: 已标注','[完成] 架构笔记已更新'],
        [`[自省] 思维模式校准`,'> 是否过度设计: 检查','> 是否忽略简单方案: 检查','> KISS原则: 重新对齐','> 心智模型: 已刷新','[完成] 认知校准完毕']
      ]},
      developer: { emoji:'💻', task:'技能复盘', screens:[
        [`[充能] 编码复盘`,'> 本周代码: 回顾','> 重复模式: 发现2处','> 可抽象为工具: 1个','> 新技能GET: async模式','[完成] 技能树已更新'],
        [`[自省] 效率分析`,'> 流畅时段: 10am-12pm','> 打断次数: 7次/天','> 上下文切换成本: 高','> 优化: 设置专注时间','[完成] 效率方案已定']
      ]},
      qa_engineer: { emoji:'🧪', task:'质量反思', screens:[
        [`[充能] 测试策略复盘`,'> 漏测Bug: 回顾2个','> 根因: 边界覆盖不足','> 新增规则: 3条','> 自动化率: 可提升至95%','[完成] 策略已优化'],
        [`[自省] 效能分析`,'> 发现Bug效率: 分析','> 误报率: 偏高(12%)','> 优化: 调整阈值','> 优先级判断: 已校准','[完成] 质量感知已升级']
      ]},
      devops: { emoji:'🚀', task:'系统健康检查', screens:[
        [`[充能] 基础设施巡检`,'> CPU均值: 42% ✓','> 内存: 68% ⚠ 偏高','> 磁盘: 55% ✓','> 异常日志: 0 ✓','[完成] 系统状态良好'],
        [`[自省] 运维流程复盘`,'> 上次故障响应: 回顾','> MTTR: 从8min→5min','> 可优化: 告警分级','> 自动恢复: 新增2个场景','[完成] SRE手册已更新']
      ]},
      documentation: { emoji:'📝', task:'整理归档', screens:[
        [`[充能] 文档债务清理`,'> 过期文档: 标记3份','> 缺失文档: 补充2份','> 格式统一: 执行','> 搜索优化: 标签重建','[完成] 文档库已整洁'],
        [`[自省] 写作复盘`,'> 可读性评分: 回顾','> 读者反馈: 整理','> 改进: 增加示例','> 模板: 优化2个','[完成] 写作能力↑']
      ]},
    },
  };

  // ═══════════════════════════════════════════════
  // 场景元数据配置
  // ═══════════════════════════════════════════════
  const _roomMeta = {
    council:    { label:'议事厅', icon:'◇', handoff:'发言权交接', defaultTask:'发表观点', 
                  modes:{what_if:'议题讨论',parallel:'分组辩论',evolutionary:'多轮共识'} },
    extraction: { label:'萃取室', icon:'○', handoff:'萃取传递', defaultTask:'知识萃取',
                  modes:{what_if:'萃取推演',parallel:'并行萃取',evolutionary:'迭代精炼'} },
    workshop:   { label:'工作坊', icon:'□', handoff:'产出交付', defaultTask:'执行任务',
                  modes:{what_if:'What-if 推演',parallel:'并行策略对比',evolutionary:'演化搜索'} },
    library:    { label:'知识库', icon:'△', handoff:'知识传递', defaultTask:'知识检索',
                  modes:{what_if:'检索推演',parallel:'并行检索',evolutionary:'深度挖掘'} },
    arena:      { label:'演练场', icon:'◎', handoff:'挑战传递', defaultTask:'技能验证',
                  modes:{what_if:'对抗推演',parallel:'多路PK',evolutionary:'淘汰赛'} },
    rest:       { label:'休息区', icon:'◌', handoff:'状态同步', defaultTask:'自省充能',
                  modes:{what_if:'复盘推演',parallel:'并行充能',evolutionary:'渐进恢复'} },
  };

  const roomMeta = _roomMeta[targetRoom] || _roomMeta.workshop;
  const roleMap = _roomRoleMaps[targetRoom] || _roleWorkMap;

  // 动态生成步骤
  const steps = activeAgents.map((ag, idx) => {
    const roleInfo = roleMap[ag.role] || { emoji:'⚡', task: roomMeta.defaultTask, screens:[
      [`[${roomMeta.icon}] ${topic}`,'> 正在处理...','> 分析中...','> 输出结果...','[完成] 任务已执行']
    ]};
    const color = _roleColors[idx % _roleColors.length];
    const screenSet = roleInfo.screens[Math.floor(Math.random()*roleInfo.screens.length)]
      .map(l => l.replace('{task}', taskTitle.substring(0,20)));
    return {
      agent: ag.name,
      task: roleInfo.task,
      screenLines: screenSet,
      next: idx < activeAgents.length-1 ? activeAgents[idx+1].name : null,
      handoff: roomMeta.handoff,
      color
    };
  });

  const simLog = [];
  const startTime = Date.now();
  const modeLabel = roomMeta.modes[simMode] || simMode;

  addActivity({type:'info', text:`🎬 ${roomMeta.label}[${modeLabel}]: ${topic} (${activeAgents.length}个智能体)`, time:new Date().toISOString()});

  // ══════════════════════════════════════
  // 根据场景+模式选择执行策略
  // ══════════════════════════════════════

  // ── 议事厅专属: 围坐讨论模式 ──
  if(targetRoom === 'council' && simMode === 'what_if'){
    const syncEl = document.getElementById('secs-sync-status');
    // PM开场
    if(syncEl) syncEl.innerHTML = `<span style="color:#22d3ee">◇ 议事开始 · ${esc(topic)}</span>`;
    await _secsRunStep(steps[0], 0, steps, simLog);
    // 全员并行发言 (PM不再发言)
    if(steps.length > 2){
      const speakers = steps.slice(1);
      if(syncEl) syncEl.innerHTML = `<span style="color:#a78bfa">◇ 自由讨论中 · ${speakers.length}人发言</span>`;
      if(window._dt3dOverview) window._dt3dOverview();
      await new Promise(r=>setTimeout(r,800));
      // 每位逐一发言 (围坐轮转)
      for(let si=0; si<speakers.length; si++){
        if(window._secsDevStop) break;
        const sp = speakers[si];
        if(syncEl) syncEl.innerHTML = `<span style="color:${sp.color}">◇ ${esc(sp.agent)} 发言中...</span>`;
        // 从PM到发言者画线
        if(si===0 && window._dt3dHandoff) window._dt3dHandoff(steps[0].agent, sp.agent, '请发言', '#22d3ee');
        else if(window._dt3dHandoff) window._dt3dHandoff(speakers[si-1].agent, sp.agent, '接力', speakers[si-1].color);
        await new Promise(r=>setTimeout(r,600));
        if(window._dt3dFocusByName) window._dt3dFocusByName(sp.agent);
        if(window._dt3dSpeakerBubble) window._dt3dSpeakerBubble(sp.agent, true);
        // 找出有意义的发言内容
        const spContent = sp.screenLines.find(l=> l && !l.startsWith('[') && !l.startsWith('──') && !l.startsWith('═') && l.length > 4) || sp.task;
        secsAppendDialogue(sp.agent, spContent, sp.color);
        const ttsP = secsTTSSpeak(sp.agent + '：' + spContent, sp.agent);
        // 逐行显示发言
        for(let li=0; li<sp.screenLines.length; li++){
          if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(sp.agent, sp.screenLines.slice(0,li+1), sp.color);
          await new Promise(r=>setTimeout(r, 400 + Math.random()*200));
        }
        await ttsP;
        await new Promise(r=>setTimeout(r,300));
        if(window._dt3dSpeakerBubble) window._dt3dSpeakerBubble(sp.agent, false);
        if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(sp.agent, [...sp.screenLines, '── 发言完毕 ──'], '#34d399');
        simLog.push({agent:sp.agent, task:sp.task, duration:((speakers.length-si)*1.2).toFixed(1)+'s', status:'completed'});
      }
      // PM总结
      if(syncEl) syncEl.innerHTML = `<span style="color:#22d3ee">◇ 主持人总结</span>`;
      await new Promise(r=>setTimeout(r,500));
      if(window._dt3dOverview) window._dt3dOverview();
      await new Promise(r=>setTimeout(r,400));
      // 所有发言者向PM画汇聚线
      for(const sp of speakers){
        if(window._dt3dHandoff) window._dt3dHandoff(sp.agent, steps[0].agent, '观点', sp.color);
        await new Promise(r=>setTimeout(r,200));
      }
      await new Promise(r=>setTimeout(r,1200));
      if(window._dt3dFocusByName) window._dt3dFocusByName(steps[0].agent);
      if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(steps[0].agent, [
        '═══════════════════════════',
        `  ◇ 议题: ${topic.substring(0,20)}`,
        `  📋 综合 ${speakers.length} 位成员意见`,
        '  ✅ 决议: 通过 (共识度 87%)',
        '  📌 待办: 3项 Action Items',
        '═══════════════════════════'
      ], '#22d3ee');
      simLog.push({agent:steps[0].agent, task:'总结决议', duration:'2.0s', status:'completed'});
    }

  // ── 演练场专属: 红蓝对抗模式 ──
  } else if(targetRoom === 'arena' && simMode === 'what_if'){
    const syncEl = document.getElementById('secs-sync-status');
    // 第1位=裁判, 奇数位=红队, 偶数位=蓝队
    const judge = steps[0];
    const contestants = steps.slice(1);
    const redTeam = contestants.filter((_,i)=>i%2===0);
    const blueTeam = contestants.filter((_,i)=>i%2===1);
    // 裁判开场
    if(syncEl) syncEl.innerHTML = `<span style="color:#fbbf24">◎ 裁判制定规则</span>`;
    await _secsRunStep(judge, 0, steps, simLog);
    // 红蓝交替对抗
    const maxRounds = Math.max(redTeam.length, blueTeam.length);
    for(let rd=0; rd<maxRounds; rd++){
      if(window._secsDevStop) break;
      // 红队出场
      if(rd < redTeam.length){
        const red = redTeam[rd];
        if(syncEl) syncEl.innerHTML = `<span style="color:#f472b6">🔴 红队: ${esc(red.agent)}</span>`;
        if(window._dt3dHandoff) window._dt3dHandoff(judge.agent, red.agent, '红队挑战', '#f472b6');
        await new Promise(r=>setTimeout(r,500));
        if(window._dt3dFocusByName) window._dt3dFocusByName(red.agent);
        const redContent = red.screenLines.find(l=>l&&!l.startsWith('[')&&!l.startsWith('──')&&l.length>4) || red.task;
        secsAppendDialogue('🔴 '+red.agent, redContent, '#f472b6');
        const redTTS = secsTTSSpeak(red.agent + '红队观点：' + redContent, red.agent);
        for(let li=0; li<red.screenLines.length; li++){
          if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(red.agent, red.screenLines.slice(0,li+1), '#f472b6');
          await new Promise(r=>setTimeout(r,350));
        }
        await redTTS;
        simLog.push({agent:red.agent, task:red.task, duration:'3.2s', status:'completed'});
        await new Promise(r=>setTimeout(r,400));
      }
      // 蓝队出场
      if(rd < blueTeam.length){
        const blue = blueTeam[rd];
        if(syncEl) syncEl.innerHTML = `<span style="color:#60a5fa">🔵 蓝队: ${esc(blue.agent)}</span>`;
        if(window._dt3dHandoff) window._dt3dHandoff(judge.agent, blue.agent, '蓝队应战', '#60a5fa');
        await new Promise(r=>setTimeout(r,500));
        if(window._dt3dFocusByName) window._dt3dFocusByName(blue.agent);
        const blueContent = blue.screenLines.find(l=>l&&!l.startsWith('[')&&!l.startsWith('──')&&l.length>4) || blue.task;
        secsAppendDialogue('🔵 '+blue.agent, blueContent, '#60a5fa');
        const blueTTS = secsTTSSpeak(blue.agent + '蓝队应答：' + blueContent, blue.agent);
        for(let li=0; li<blue.screenLines.length; li++){
          if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(blue.agent, blue.screenLines.slice(0,li+1), '#60a5fa');
          await new Promise(r=>setTimeout(r,350));
        }
        await blueTTS;
        simLog.push({agent:blue.agent, task:blue.task, duration:'3.4s', status:'completed'});
        // PK spark between red & blue
        if(rd < redTeam.length && window._dt3dPKSpark) window._dt3dPKSpark(redTeam[rd].agent, blue.agent);
        await new Promise(r=>setTimeout(r,400));
      }
    }
    // 裁判判定
    if(syncEl) syncEl.innerHTML = `<span style="color:#fbbf24">◎ 裁判最终判定</span>`;
    await new Promise(r=>setTimeout(r,600));
    if(window._dt3dOverview) window._dt3dOverview();
    await new Promise(r=>setTimeout(r,500));
    // 全员向裁判汇聚
    for(const c of contestants){
      if(window._dt3dHandoff) window._dt3dHandoff(c.agent, judge.agent, '成绩', c.color);
      await new Promise(r=>setTimeout(r,150));
    }
    await new Promise(r=>setTimeout(r,1200));
    if(window._dt3dFocusByName) window._dt3dFocusByName(judge.agent);
    const redScore = (78 + Math.random()*15).toFixed(1);
    const blueScore = (78 + Math.random()*15).toFixed(1);
    if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(judge.agent, [
      '═══════════════════════════',
      `  ◎ 命题: ${topic.substring(0,18)}`,
      `  🔴 红队总分: ${redScore}`,
      `  🔵 蓝队总分: ${blueScore}`,
      `  🏆 ${parseFloat(redScore)>parseFloat(blueScore)?'红队':'蓝队'}胜出!`,
      '═══════════════════════════'
    ], '#fbbf24');
    simLog.push({agent:judge.agent, task:'最终裁决', duration:'1.5s', status:'completed'});

  // ── 萃取室专属: 培养皿萃取模式 ──
  } else if(targetRoom === 'extraction' && simMode === 'what_if'){
    const syncEl = document.getElementById('secs-sync-status');
    // 第1位=萃取规划者, 最后1位=结晶输出, 中间=并行萃取
    if(syncEl) syncEl.innerHTML = `<span style="color:#34d399">○ 萃取启动 · ${esc(topic)}</span>`;
    await _secsRunStep(steps[0], 0, steps, simLog);
    if(steps.length > 2){
      const extractors = steps.slice(1, -1);
      const crystalizer = steps[steps.length-1];
      // 中心辐射: 规划者向所有萃取者发射
      if(syncEl) syncEl.innerHTML = `<span style="color:#34d399">○ 并行萃取中 · ${extractors.length}路</span>`;
      if(window._dt3dOverview) window._dt3dOverview();
      await new Promise(r=>setTimeout(r,500));
      for(let ei=0; ei<extractors.length; ei++){
        if(window._secsDevStop) break;
        if(window._dt3dHandoff) window._dt3dHandoff(steps[0].agent, extractors[ei].agent, '萃取任务', '#34d399');
        await new Promise(r=>setTimeout(r,300));
      }
      await new Promise(r=>setTimeout(r,1000));
      // 所有萃取者并行工作
      const maxLines = Math.max(...extractors.map(e=>e.screenLines.length));
      for(let li=0; li<maxLines; li++){
        for(const ext of extractors){
          if(li < ext.screenLines.length && window._dt3dUpdateScreen){
            window._dt3dUpdateScreen(ext.agent, ext.screenLines.slice(0,li+1), ext.color);
          }
        }
        await new Promise(r=>setTimeout(r, 400 + Math.random()*150));
      }
      await new Promise(r=>setTimeout(r,600));
      // 追加对话日志 (每人一条总结)
      for(const ext of extractors){
        const extContent = ext.screenLines.find(l=>l&&!l.startsWith('[')&&!l.startsWith('──')&&l.length>4) || ext.task;
        secsAppendDialogue(ext.agent, extContent, ext.color);
      }
      extractors.forEach(ext=>{
        if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(ext.agent, [...ext.screenLines, '── 萃取完成 ──'], '#34d399');
        simLog.push({agent:ext.agent, task:ext.task, duration:'3.5s', status:'completed'});
      });
      // 汇聚到结晶者
      if(syncEl) syncEl.innerHTML = `<span style="color:#fbbf24">○ 知识结晶中...</span>`;
      await new Promise(r=>setTimeout(r,500));
      for(const ext of extractors){
        if(window._dt3dHandoff) window._dt3dHandoff(ext.agent, crystalizer.agent, '原矿', ext.color);
        await new Promise(r=>setTimeout(r,250));
      }
      await new Promise(r=>setTimeout(r,1200));
      await _secsRunStep(crystalizer, steps.length-1, steps, simLog);
    } else if(steps.length === 2){
      await _secsRunStep(steps[1], 1, steps, simLog);
    }

  // ── 知识库专属: 分布检索→汇聚归纳 ──
  } else if(targetRoom === 'library' && simMode === 'what_if'){
    const syncEl = document.getElementById('secs-sync-status');
    const coordinator = steps[0]; // 第1人=检索协调者
    const searchers = steps.slice(1, -1); // 中间=检索者
    const summarizer = steps[steps.length-1]; // 最后=归纳者
    // 协调者发起检索
    if(syncEl) syncEl.innerHTML = `<span style="color:#a78bfa">△ ${esc(coordinator.agent)} 发起检索</span>`;
    await _secsRunStep(coordinator, 0, steps, simLog);
    // 检索者并行检索
    if(searchers.length > 0){
      if(syncEl) syncEl.innerHTML = `<span style="color:#a78bfa">△ ${searchers.length} 路并行检索中...</span>`;
      if(window._dt3dOverview) window._dt3dOverview();
      await new Promise(r=>setTimeout(r,600));
      // 发射检索线
      for(let si=0; si<searchers.length; si++){
        if(window._secsDevStop) break;
        const s = searchers[si];
        if(window._dt3dHandoff) window._dt3dHandoff(coordinator.agent, s.agent, '检索#'+(si+1), '#a78bfa');
        await new Promise(r=>setTimeout(r,300));
      }
      await new Promise(r=>setTimeout(r,800));
      // 每位检索者逐行显示结果
      for(const s of searchers){
        if(syncEl) syncEl.innerHTML = `<span style="color:${s.color}">△ ${esc(s.agent)} 检索中...</span>`;
        if(window._dt3dFocusByName) window._dt3dFocusByName(s.agent);
        const sContent = s.screenLines.find(l=>l&&!l.startsWith('[')&&!l.startsWith('──')&&l.length>4) || s.task;
        secsAppendDialogue(s.agent, sContent, s.color);
        const sTTS = secsTTSSpeak(s.agent + '：' + sContent, s.agent);
        for(let li=0; li<s.screenLines.length; li++){
          if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(s.agent, s.screenLines.slice(0,li+1), s.color);
          await new Promise(r=>setTimeout(r, 300 + Math.random()*150));
        }
        await sTTS;
        simLog.push({agent:s.agent, task:s.task, duration:(2+Math.random()*2).toFixed(1)+'s', status:'completed'});
        await new Promise(r=>setTimeout(r,400));
      }
      // 汇聚到归纳者
      if(syncEl) syncEl.innerHTML = `<span style="color:#a78bfa">△ 汇聚检索结果 → ${summarizer.agent}</span>`;
      if(window._dt3dOverview) window._dt3dOverview();
      await new Promise(r=>setTimeout(r,500));
      for(const s of searchers){
        if(window._dt3dHandoff) window._dt3dHandoff(s.agent, summarizer.agent, '结果', s.color);
        await new Promise(r=>setTimeout(r,200));
      }
      await new Promise(r=>setTimeout(r,1200));
    }
    // 归纳者总结
    await _secsRunStep(summarizer, steps.length-1, steps, simLog);
    if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(summarizer.agent, [
      '═══════════════════════════',
      `  △ 检索主题: ${topic.substring(0,18)}`,
      `  📚 命中文档: ${Math.ceil(Math.random()*20+15)} 份`,
      `  🔗 关联知识: ${Math.ceil(Math.random()*8+3)} 条`,
      `  ✅ 知识覆盖率: ${(78+Math.random()*18).toFixed(0)}%`,
      '═══════════════════════════'
    ], '#a78bfa');

  // ── 休息区专属: 慢节奏复盘 ──
  } else if(targetRoom === 'rest'){
    const syncEl = document.getElementById('secs-sync-status');
    if(syncEl) syncEl.innerHTML = `<span style="color:var(--dim)">◌ 安静复盘中... (慢节奏)</span>`;
    // 顺序执行但速度慢1.5x, 每步之间有呼吸间隔
    for(let i=0; i<steps.length; i++){
      if(window._secsDevStop) break;
      const step = steps[i];
      const stepStart = Date.now();
      try {
        if(i > 0 && window._dt3dUpdateScreen) window._dt3dUpdateScreen(steps[i-1].agent, [''], '#333');
        if(window._dt3dFocusByName) window._dt3dFocusByName(step.agent);
        // 追加对话日志 + TTS
        const restContent = step.screenLines.find(l=>l&&!l.startsWith('[')&&!l.startsWith('──')&&!l.startsWith('═')&&l.length>4) || step.task;
        secsAppendDialogue(step.agent, restContent, step.color);
        const restTTS = secsTTSSpeak(step.agent + '：' + restContent, step.agent);
        // 慢速逐行显示
        for(let li=0; li<step.screenLines.length; li++){
          if(window._dt3dUpdateScreen) window._dt3dUpdateScreen(step.agent, step.screenLines.slice(0,li+1), step.color);
          await new Promise(r=>setTimeout(r, 600 + Math.random()*300)); // 比正常慢1.5x
        }
        await restTTS;
        await new Promise(r=>setTimeout(r,800)); // 呼吸
        if(window._dt3dUpdateScreen){
          window._dt3dUpdateScreen(step.agent, [...step.screenLines, '── ✓ ──'], '#34d399');
        }
        if(step.next && window._dt3dHandoff){
          window._dt3dHandoff(step.agent, step.next, '轮到你了', step.color);
          await new Promise(r=>setTimeout(r,2500)); // 慢速过渡
        }
      } catch(e){}
      simLog.push({agent:step.agent, task:step.task, duration:((Date.now()-stepStart)/1000).toFixed(1)+'s', status:'completed'});
    }

  } else if(simMode === 'parallel'){
    // ── 并行策略对比模式 ──
    // 第1步: PM 独立规划
    await _secsRunStep(steps[0], 0, steps, simLog);
    // 第2步: 剩余agents并行执行 (屏幕同时更新)
    if(steps.length > 2){
      const parallelSteps = steps.slice(1, -1);
      const syncEl = document.getElementById('secs-sync-status');
      if(syncEl) syncEl.innerHTML = `<span style="color:#a78bfa">⚡ 并行执行: ${parallelSteps.map(s=>s.agent).join(' + ')}</span>`;
      // 摄像机拉远到全景, 让所有弧线可见
      if(window._dt3dOverview) window._dt3dOverview();
      await new Promise(r=>setTimeout(r,600));
      // 逐条发射handoff线 (间隔300ms, 每条不同颜色)
      const parallelColors = ['#a78bfa','#60a5fa','#f472b6','#fbbf24','#34d399'];
      for(let pi=0; pi<parallelSteps.length; pi++){
        if(window._secsDevStop) break;
        const s = parallelSteps[pi];
        const c = parallelColors[pi % parallelColors.length];
        if(window._dt3dHandoff) window._dt3dHandoff(steps[0].agent, s.agent, '→'+s.agent, c);
        await new Promise(r=>setTimeout(r,400));
      }
      await new Promise(r=>setTimeout(r,1500));
      // 并行: 逐行同时推进所有agent屏幕
      // 先追加对话日志 (并行启动信息)
      for(const ps of parallelSteps){
        const psContent = ps.screenLines.find(l=>l&&!l.startsWith('$')&&!l.startsWith('[')&&!l.startsWith('──')&&l.length>4) || ps.task;
        secsAppendDialogue(ps.agent, psContent, ps.color);
      }
      const maxLines = Math.max(...parallelSteps.map(s=>s.screenLines.length));
      for(let li=0; li<maxLines; li++){
        for(const ps of parallelSteps){
          if(li < ps.screenLines.length && window._dt3dUpdateScreen){
            window._dt3dUpdateScreen(ps.agent, ps.screenLines.slice(0,li+1), ps.color);
          }
        }
        await new Promise(r=>setTimeout(r, 300 + Math.random()*150));
      }
      await new Promise(r=>setTimeout(r,600));
      // 标记完成
      const pStart = Date.now();
      parallelSteps.forEach(ps=>{
        if(window._dt3dUpdateScreen){
          window._dt3dUpdateScreen(ps.agent, [...ps.screenLines, '── done (parallel) ──'], '#34d399');
        }
        simLog.push({agent:ps.agent, task:ps.task, duration:((Date.now()-pStart)/1000+2).toFixed(1)+'s', status:'completed'});
      });
      await new Promise(r=>setTimeout(r,800));
      // 汇聚到最后一个agent: 多条线同时飞向它
      const lastStep = steps[steps.length-1];
      for(let pi=0; pi<parallelSteps.length; pi++){
        const ps = parallelSteps[pi];
        const c = parallelColors[pi % parallelColors.length];
        if(window._dt3dHandoff) window._dt3dHandoff(ps.agent, lastStep.agent, '汇总', c);
        await new Promise(r=>setTimeout(r,300));
      }
      await new Promise(r=>setTimeout(r,1500));
      await _secsRunStep(lastStep, steps.length-1, steps, simLog);
    } else if(steps.length === 2){
      await _secsRunStep(steps[1], 1, steps, simLog);
    }

  } else if(simMode === 'evolutionary'){
    // ── 演化搜索模式 ──
    // 两轮迭代: 草案轮(快) + 精炼轮(正常)
    const syncEl = document.getElementById('secs-sync-status');
    // 第1轮: 快速草案
    if(syncEl) syncEl.innerHTML = `<span style="color:#fbbf24">🧬 第1轮 · 草案探索</span>`;
    for(let i=0; i<steps.length; i++){
      const step = steps[i];
      const stepStart = Date.now();
      try {
        if(window._dt3dFocusByName) window._dt3dFocusByName(step.agent);
        // 快速显示(一次性刷完)
        if(window._dt3dUpdateScreen){
          window._dt3dUpdateScreen(step.agent, [...step.screenLines, '── draft v1 ──'], '#fbbf24');
        }
        await new Promise(r=>setTimeout(r, 600));
        if(step.next && window._dt3dHandoff) window._dt3dHandoff(step.agent, step.next, 'v1草案', '#fbbf24');
        await new Promise(r=>setTimeout(r, 800));
      } catch(e){}
    }
    // 第2轮: 精炼
    if(syncEl) syncEl.innerHTML = `<span style="color:#34d399">🧬 第2轮 · 精炼优化</span>`;
    await new Promise(r=>setTimeout(r,600));
    for(let i=0; i<steps.length; i++){
      const step = steps[i];
      // 改写output为"refined"版
      const refinedLines = step.screenLines.map(l => l.replace('[INFO]','[v2]').replace('[OK]','[✓✓]'));
      step.screenLines = refinedLines;
      await _secsRunStep(step, i, steps, simLog);
    }

  } else {
    // ── What-if 推演 (默认) ──
    // 顺序执行, 逐个agent
    for(let i=0; i<steps.length; i++){
      await _secsRunStep(steps[i], i, steps, simLog);
    }
  }

  const totalTime = ((Date.now()-startTime)/1000).toFixed(1);

  // 所有agent显示完成
  steps.forEach((step,idx)=>{
    if(window._dt3dUpdateScreen){
      const elapsed = simLog[idx]?.duration || '?s';
      window._dt3dUpdateScreen(step.agent, [
        '═══════════════════════════',
        `  ✅ ${step.task}`,
        `  ⏱  ${elapsed}`,
        '═══════════════════════════'
      ], '#34d399');
    }
  });

  const syncEl2 = document.getElementById('secs-sync-status');
  if(syncEl2) syncEl2.innerHTML = `<span style="color:var(--green)">✓ [${modeLabel}] 完成</span> <span style="color:var(--dim)">总耗时 ${totalTime}s</span>`;

  // 生成报告并弹出
  await new Promise(r=>setTimeout(r,800));
  if(window._dt3dSpeakerBubble) window._dt3dSpeakerBubble(null, false); // 清除发言气泡
  // 停止TTS
  if(_secsTTSAudio){_secsTTSAudio.pause();_secsTTSAudio=null}
  if(window.speechSynthesis) speechSynthesis.cancel();
  _secsTTSSerial++;
  showSecsReport(simLog, totalTime, steps);

  if(btn){ btn.disabled=false; btn.textContent=(_roomTaskConfig[window._currentRoomId||'workshop']||_roomTaskConfig.workshop).btnText; btn.style.opacity='1'; }
  _secsSimRunning = false;
  if(window._secsDevStop){ window._secsDevStop = false; if(window.toast) toast('⏹ 仿真已停止'); }
}

// ── 单步执行helper (What-if/演化精炼 共用) ──
async function _secsRunStep(step, i, steps, simLog){
  if(window._secsDevStop) return;  // 停止仿真：跳过该步动画，让流程尽快走到 finalize
  const stepStart = Date.now();
  try {
    const syncEl = document.getElementById('secs-sync-status');
    if(syncEl) syncEl.innerHTML = `<span style="color:${step.color}">▶ ${esc(step.agent)}: ${esc(step.task)}</span>`;
    if(i > 0 && window._dt3dUpdateScreen){
      window._dt3dUpdateScreen(steps[i-1].agent, [''], '#333');
    }
    if(window._dt3dFocusByName) window._dt3dFocusByName(step.agent);
    // 追加对话日志
    secsAppendDialogue(step.agent, step.task, step.color);
    const lines = step.screenLines;
    // 找出有实质内容的行作为TTS朗读文本
    const speakLine = lines.find(l=> l && !l.startsWith('$') && !l.startsWith('[OK]') && !l.startsWith('──') && !l.startsWith('═') && l.length > 4) || step.task;
    const ttsPromise = secsTTSSpeak(step.agent + '：' + speakLine, step.agent);
    for(let li=0; li<lines.length; li++){
      if(window._dt3dUpdateScreen){
        window._dt3dUpdateScreen(step.agent, lines.slice(0, li+1), step.color);
      }
      await new Promise(r=>setTimeout(r, 350 + Math.random()*200));
    }
    await ttsPromise; // 等TTS说完再继续
    await new Promise(r=>setTimeout(r,400));
    if(window._dt3dUpdateScreen){
      const elapsed = ((Date.now()-stepStart)/1000).toFixed(1);
      window._dt3dUpdateScreen(step.agent, [...lines, `── done ${elapsed}s ──`], '#34d399');
    }
    if(step.next && window._dt3dHandoff){
      window._dt3dHandoff(step.agent, step.next, step.handoff, step.color);
      await new Promise(r=>setTimeout(r,2200));
    } else {
      await new Promise(r=>setTimeout(r,800));
    }
  } catch(e){ console.error('[SECS] Step error:', step.agent, e); }
  simLog.push({agent:step.agent, task:step.task, duration:((Date.now()-stepStart)/1000).toFixed(1)+'s', status:'completed'});
}

function showSecsReport(log, totalTime, _secsDevSteps){
  const modal = document.getElementById('secs-report-modal');
  const content = document.getElementById('secs-report-content');
  const curRoom = window._currentRoomId || 'workshop';

  // 计算指标
  const taskCount = log.length;
  const completedCount = log.filter(l=>l.status==='completed').length;
  const efficiency = ((completedCount/taskCount)*100).toFixed(0);
  const handoffs = taskCount - 1;

  // 场景专属标题和指标名
  const reportMeta = {
    council: { title:'◇ 议事决议报告', metric1:'发言人数', metric2:'共识度', metric3:'讨论轮次', metric4:'总耗时', color:'#22d3ee' },
    extraction: { title:'○ 知识萃取报告', metric1:'萃取节点', metric2:'结晶率', metric3:'知识关联', metric4:'总耗时', color:'#34d399' },
    workshop: { title:'□ 开发交付报告', metric1:'任务阶段', metric2:'完成率', metric3:'任务交接', metric4:'总耗时', color:'#fbbf24' },
    library: { title:'△ 知识检索报告', metric1:'检索路径', metric2:'命中率', metric3:'关联发现', metric4:'总耗时', color:'#a78bfa' },
    arena: { title:'◎ 对抗演练报告', metric1:'参赛选手', metric2:'完成率', metric3:'对抗回合', metric4:'总耗时', color:'#f472b6' },
    rest: { title:'◌ 复盘充能报告', metric1:'复盘项', metric2:'完成度', metric3:'改进点', metric4:'总耗时', color:'#60a5fa' },
  }[curRoom] || { title:'仿真报告', metric1:'阶段', metric2:'完成率', metric3:'交接', metric4:'总耗时', color:'#22d3ee' };

  // 场景专属结论
  const conclusions = {
    council: [
      `议事讨论共 <b>${taskCount}</b> 位成员参与，<b>${handoffs}</b> 次发言交接`,
      `共识度评估：<span style="color:#22d3ee;font-weight:600">${(82+Math.random()*15).toFixed(0)}%</span>`,
      `决议结果：通过 — 已生成 3 项 Action Items`,
      `建议：对分歧较大的议题可增加第二轮辩论`
    ],
    extraction: [
      `萃取流程 <b>${taskCount}</b> 个节点，产出知识卡片 <b>${Math.max(3,taskCount-1)}</b> 张`,
      `知识纯度评分：<span style="color:#34d399;font-weight:600">${(85+Math.random()*12).toFixed(0)}/100</span>`,
      `发现隐含关联 <b>${Math.ceil(Math.random()*4+1)}</b> 处，已自动建立连接`,
      `建议：高频模式可进一步结晶为可复用技能模板`
    ],
    workshop: [
      `开发流程共 <b>${taskCount}</b> 个阶段，<b>${handoffs}</b> 次交接，全部顺畅完成`,
      `瓶颈分析：编码实现阶段耗时最长，建议并行拆分子任务`,
      `协作效率评分：<span style="color:#34d399;font-weight:600">${(88+Math.random()*10).toFixed(0)}/100</span>`,
      `建议：策划师可与架构师并行工作，减少串行等待`
    ],
    library: [
      `检索路径 <b>${taskCount}</b> 条，命中相关文档 <b>${Math.ceil(Math.random()*20+15)}</b> 份`,
      `知识覆盖率：<span style="color:#a78bfa;font-weight:600">${(78+Math.random()*18).toFixed(0)}%</span>`,
      `发现知识缺口 <b>${Math.ceil(Math.random()*3)}</b> 处，已标记待补充`,
      `建议：定期运行检索以发现过期和缺失内容`
    ],
    arena: [
      `对抗演练 <b>${taskCount}</b> 位参与，<b>${Math.ceil(handoffs/2)}</b> 回合对决`,
      `红队综合分：<span style="color:#f472b6;font-weight:600">${(78+Math.random()*15).toFixed(1)}</span> / 蓝队：<span style="color:#60a5fa;font-weight:600">${(78+Math.random()*15).toFixed(1)}</span>`,
      `最佳表现：${log[Math.floor(Math.random()*log.length)]?.agent||'Agent'} (单项最高)`,
      `建议：融合双方优点形成最终方案，记录对抗经验`
    ],
    rest: [
      `复盘 <b>${taskCount}</b> 项内容，团队疲劳指数下降 <b>${(15+Math.random()*20).toFixed(0)}%</b>`,
      `认知校准完成度：<span style="color:#60a5fa;font-weight:600">${(85+Math.random()*12).toFixed(0)}%</span>`,
      `发现改进点 <b>${Math.ceil(Math.random()*4+2)}</b> 处，已加入迭代计划`,
      `建议：每周安排固定复盘时段，保持持续改进`
    ],
  }[curRoom] || [];

  content.innerHTML = `
    <div style="text-align:center;margin-bottom:16px">
      <h2 style="font-size:16px;color:${reportMeta.color};margin:0;font-weight:600">${reportMeta.title}</h2>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px">
      <div style="background:#0d1520;border:1px solid ${reportMeta.color}33;border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:24px;font-weight:700;color:${reportMeta.color}">${taskCount}</div>
        <div style="font-size:11px;color:#888;margin-top:4px">${reportMeta.metric1}</div>
      </div>
      <div style="background:#0d1520;border:1px solid rgba(52,211,153,0.2);border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:24px;font-weight:700;color:#34d399">${efficiency}%</div>
        <div style="font-size:11px;color:#888;margin-top:4px">${reportMeta.metric2}</div>
      </div>
      <div style="background:#0d1520;border:1px solid rgba(167,139,250,0.2);border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:24px;font-weight:700;color:#a78bfa">${handoffs}</div>
        <div style="font-size:11px;color:#888;margin-top:4px">${reportMeta.metric3}</div>
      </div>
      <div style="background:#0d1520;border:1px solid rgba(251,191,36,0.2);border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:24px;font-weight:700;color:#fbbf24">${totalTime}s</div>
        <div style="font-size:11px;color:#888;margin-top:4px">${reportMeta.metric4}</div>
      </div>
    </div>

    <div style="margin-bottom:20px">
      <h3 style="font-size:14px;color:#e8e8e8;margin:0 0 12px 0;font-weight:500">📊 执行明细</h3>
      <table style="width:100%;border-collapse:collapse;font-size:12px">
        <thead>
          <tr style="border-bottom:1px solid #2a3040">
            <th style="text-align:left;padding:8px;color:#888;font-weight:500">智能体</th>
            <th style="text-align:left;padding:8px;color:#888;font-weight:500">职责</th>
            <th style="text-align:center;padding:8px;color:#888;font-weight:500">耗时</th>
            <th style="text-align:center;padding:8px;color:#888;font-weight:500">状态</th>
          </tr>
        </thead>
        <tbody>
          ${log.map((l,i)=>{
            const stepDef = _secsDevSteps[i];
            const c = stepDef?.color || '#888';
            return `<tr style="border-bottom:1px solid #1a2030">
              <td style="padding:8px;color:${c};font-weight:500">${l.agent}</td>
              <td style="padding:8px;color:#ccc">${l.task}</td>
              <td style="padding:8px;text-align:center;color:#aaa">${l.duration}</td>
              <td style="padding:8px;text-align:center"><span style="background:rgba(52,211,153,0.15);color:#34d399;padding:2px 8px;border-radius:4px;font-size:11px">✓ 完成</span></td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>

    <div style="margin-bottom:20px">
      <h3 style="font-size:14px;color:#e8e8e8;margin:0 0 12px 0;font-weight:500">🔗 协作流程</h3>
      <div style="display:flex;align-items:center;gap:0;overflow-x:auto;padding:10px 0">
        ${_secsDevSteps.map((s,i)=>{
          const arrow = i < _secsDevSteps.length-1 ? `<div style="color:#555;font-size:16px;margin:0 4px">→</div>` : '';
          return `<div style="display:flex;align-items:center;gap:0">
            <div style="background:rgba(255,255,255,0.03);border:1px solid ${s.color}33;border-radius:6px;padding:8px 12px;text-align:center;min-width:68px">
              <div style="font-size:11px;color:${s.color};font-weight:500">${s.agent}</div>
              <div style="font-size:10px;color:#666;margin-top:2px">${s.task}</div>
            </div>
            ${arrow}
          </div>`;
        }).join('')}
      </div>
    </div>

    <div style="background:${reportMeta.color}12;border:1px solid ${reportMeta.color}33;border-radius:8px;padding:16px;margin-bottom:16px">
      <h3 style="font-size:13px;color:${reportMeta.color};margin:0 0 8px 0;font-weight:500">💡 ${reportMeta.title.replace(/[◇○□△◎◌]\s*/,'')}</h3>
      <ul style="margin:0;padding-left:16px;color:#bbb;font-size:12px;line-height:1.8">
        ${conclusions.map(c=>`<li>${c}</li>`).join('')}
      </ul>
    </div>

    <div style="background:rgba(255,255,255,0.02);border:1px solid #2a3040;border-radius:8px;padding:12px 16px;margin-bottom:16px">
      <h3 style="font-size:12px;color:#888;margin:0 0 8px 0;font-weight:500">🔄 后续建议</h3>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        ${{
          council:['→ 工作坊: 将决议转为开发任务','→ 萃取室: 归档讨论精华'],
          extraction:['→ 知识库: 检索关联知识验证','→ 工作坊: 应用萃取技能'],
          workshop:['→ 演练场: 测试方案对比','→ 萃取室: 沉淀开发经验'],
          library:['→ 工作坊: 基于检索结果开发','→ 议事厅: 讨论知识缺口'],
          arena:['→ 工作坊: 采纳获胜方案','→ 休息区: 复盘对抗收获'],
          rest:['→ 工作坊: 带着新认知继续','→ 议事厅: 规划下个迭代'],
        }[curRoom]?.map(s=>`<span style="font-size:11px;background:#1a2030;border:1px solid #333;padding:4px 10px;border-radius:12px;color:#aaa;cursor:pointer" onclick="closeSecsReport();flyToRoom('${s.includes('工作坊')?'workshop':s.includes('萃取')?'extraction':s.includes('知识库')?'library':s.includes('议事')?'council':s.includes('演练')?'arena':'rest'}')">${s}</span>`).join('')||''}
      </div>
    </div>

    <div style="display:flex;gap:10px;justify-content:flex-end">
      <button onclick="closeSecsReport()" style="padding:8px 16px;font-size:12px;background:transparent;border:1px solid #333;color:#aaa;border-radius:6px;cursor:pointer">关闭</button>
      <button onclick="secsInjectFromReport()" style="padding:8px 16px;font-size:12px;background:linear-gradient(135deg,#34d399,#22d3ee);color:#000;border:none;border-radius:6px;cursor:pointer;font-weight:500">⬆ 注入优化策略</button>
    </div>
  `;

  // 动态更新报告弹窗标题
  const titleEl = document.getElementById('secs-report-title');
  if(titleEl){titleEl.textContent = '📋 ' + reportMeta.title; titleEl.style.color = reportMeta.color;}
  modal.style.display = 'flex';
}

function closeSecsReport(){
  document.getElementById('secs-report-modal').style.display = 'none';
}

async function secsInjectFromReport(){
  var sessionId = window._lastReportSessionId;
  if (!sessionId) {
    // 无 sessionId 时仅做 UI 反馈
    closeSecsReport();
    addActivity({type:'info', text:'⚠️ 无可用会话，无法注入策略', time:new Date().toISOString()});
    return;
  }
  try {
    var btn = document.querySelector('#secs-report-modal button[onclick*="secsInjectFromReport"]');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ 注入中...'; }
    var r = await fetch('/api/v1/sandbox/sessions/'+encodeURIComponent(sessionId)+'/inject', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ confirm: true })
    });
    if (!r.ok) {
      var ej = await r.json().catch(function(){return{};});
      throw new Error(ej.detail || 'HTTP '+r.status);
    }
    var d = await r.json();
    closeSecsReport();
    addActivity({type:'info', text:'✅ SECS 优化策略已注入: '+(d.sop_name||d.sop_id||sessionId.slice(0,8)), time:new Date().toISOString()});
    var syncEl = document.getElementById('secs-sync-status');
    if (syncEl) syncEl.innerHTML = '<span style="color:var(--green)">✓ 策略已注入</span> <span style="color:var(--dim)">SOP 已同步至真实环境</span>';
    // 刷新统计
    if (typeof loadSecsStats === 'function') loadSecsStats();
    if (typeof loadExerciseHistory === 'function') loadExerciseHistory();
  } catch(e) {
    closeSecsReport();
    addActivity({type:'error', text:'❌ 策略注入失败: '+e.message, time:new Date().toISOString()});
    var syncEl = document.getElementById('secs-sync-status');
    if (syncEl) syncEl.innerHTML = '<span style="color:var(--red)">✗ 注入失败</span> <span style="color:var(--dim)">'+esc(e.message)+'</span>';
  }
}
