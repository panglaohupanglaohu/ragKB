/**
 * AgentsGroup2026 — Agent Digital Twin: 试炼导演台 (_DTS 状态机/trial 控制/图表渲染)
 * 从 Agent-digital-twin.html 内联脚本拆出 (frontendBigChange F2)。
 * 加载顺序: secs-core.js → director.js → v4-scenario-evolution.js
 */

// ═══ 导演台全局 helper（作用域在 IIFE 外，需自行处理 showToast 不可见问题） ═══
function _dtWarnOrLog(msg){try{if(typeof showToast==='function'){showToast(msg,'warn');return}}catch(e){}console.warn('[DT]',msg);if(typeof _logConsole==='function')try{_logConsole(msg,'warn')}catch(e){}}
function _dtLogConsole(msg,level){console.log('[DT]',msg);if(typeof _logConsole==='function')try{_logConsole(msg,level||'info')}catch(e){}}

async function createTrial(){if(!transitionTrialStatus(window._DTS.trialStatus,'creating'))return;var tid = window._selectedTeamId || (window._DTS&&window._DTS.directorConfig&&window._DTS.directorConfig.team_id) || (window.S&&window.S.selectedTeams&&window.S.selectedTeams[0]) || '';if(!tid){_dtWarnOrLog('请先在 SECS 面板选择演练团队');transitionTrialStatus('creating','idle');return}document.getElementById('dp-status-badge').textContent='⏳ 创建中...';_dtLogConsole('🧪 创建试炼 · 团队 '+tid+' · 模式 '+window._DTS.selectedMode+' · 步数 '+(parseInt((document.getElementById('dp-max-steps')||{}).value)||150),'info');var ac=new AbortController();var to=setTimeout(function(){ac.abort()},15000);console.log('[DT] createTrial POST /api/v1/twin-trials team='+tid+' mode='+window._DTS.selectedMode);try{var resp=await fetch('/api/v1/twin-trials',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({team_id:tid,task_goal:{name:(document.getElementById('dp-task-name')||{}).value||'默认试炼'},mode:window._DTS.selectedMode,max_steps:parseInt((document.getElementById('dp-max-steps')||{}).value)||150,scenario_id:(window._sx&&window._sx.scenarioId)||'',generation:(window._sx&&window._sx.generation)||0,parent_trial_id:(window._sx&&window._sx.parentTrialId)||''}),signal:ac.signal});clearTimeout(to);console.log('[DT] createTrial resp status='+resp.status);var d=await resp.json();if(!resp.ok)throw new Error(d.detail||'HTTP '+resp.status);if(d.error)throw new Error(d.error);window._DTS.activeTrialId=d.trial_id;window._DTS.activeBranchId=d.branch_id;if(window._sx){window._sx.trialId=d.trial_id;window._sx.branchId=d.branch_id;window._sx.sessionId=d.session_id;window._sx.generation=d.generation||0;}if(d.rooms&&d.rooms.length&&typeof applyScenarioRooms==='function'){applyScenarioRooms(d.rooms);}console.log('[DT] createTrial success trial='+d.trial_id+' session='+d.session_id);_dtLogConsole('✅ 试炼已创建 · trial '+String(d.trial_id||'').slice(0,8)+' · session '+String(d.session_id||'').slice(0,8)+' · 就绪，可「运行/单步」','success');transitionTrialStatus('creating','ready');document.getElementById('dp-status-badge').textContent='● 就绪';showBranchManager(d.trial_id)}catch(e){clearTimeout(to);console.error('[DT] createTrial FAILED:', e.name, e.message);transitionTrialStatus('creating','failed');document.getElementById('dp-status-badge').textContent='✗ 失败';_dtWarnOrLog(e.name==='AbortError'?'创建超时(15s)，请检查后端服务':('创建失败: '+(e.message||'未知错误')));if(e.name==='AbortError'){_dtLogConsole('创建超时(15s) — 后端无响应或网络不通','warn')}else{_dtLogConsole('创建失败: '+(e.message||'未知错误'),'err')}}}
async function stepOnce(){if(!(window._sx&&window._sx.sessionId)){await createTrial()}if(!(window._sx&&window._sx.sessionId))return;_dtLogConsole('▶ 单步','step');try{var r=await fetch('/api/v1/sandbox/sessions/'+(window._sx&&window._sx.sessionId)+'/step',{method:'POST'});var d=await r.json();var sx=window._sx||{};sx.currentStep=d.step_index||d.step_id||sx.currentStep;handleTrialEvent({type:'step',step_index:d.step_index||d.step_id,global_reward:d.global_reward})}catch(e){console.error('[DT] Step:',e)}}
async function autoRun(){if(window._DTS.trialStatus!=='ready'&&window._DTS.trialStatus!=='paused')return;if(!(window._sx&&window._sx.sessionId)){await createTrial()}if(!(window._sx&&window._sx.sessionId))return;transitionTrialStatus(window._DTS.trialStatus,'running');_dtLogConsole('▶▶ 自动运行','step');await window.sexyAutoRun()}
async function pauseSim(){if(!(window._sx&&window._sx.sessionId))return;try{await fetch('/api/v1/sandbox/sessions/'+(window._sx&&window._sx.sessionId)+'/pause',{method:'POST'});transitionTrialStatus('running','paused')}catch(e){}}
async function terminate(){
  // Abort 导演台自身的 autoRun fetch
  if (window._DTS._abortCtrl) { window._DTS._abortCtrl.abort(); window._DTS._abortCtrl = null; }
  // 同步停止 SECS 面板（如果也在运行）
  if (typeof sexyStopSim === 'function') await sexyStopSim();
  // 停止试炼导演台的 session
  if (window._sx && window._sx.sessionId) {
    try { await fetch('/api/v1/sandbox/sessions/'+window._sx.sessionId+'/stop', { method:'POST' }); }
    catch(e) { console.warn('[DT] stop trial session:', e.message); }
  }
  transitionTrialStatus(window._DTS.trialStatus, 'terminated');
}
async function forkBranch(){if(!window._DTS.activeTrialId)return;try{var r=await fetch('/api/v1/twin-trials/'+window._DTS.activeTrialId+'/branches',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fork_from_branch_id:window._DTS.activeBranchId})});var d=await r.json();handleTrialEvent({type:'branch_forked',data:d});showBranchManager(window._DTS.activeTrialId)}catch(e){}}
function showInjectDropdown(){var p=document.getElementById('inject-event-panel');if(p)p.style.display=(p.style.display==='none'?'':'none')}
async function doInjectEvent(et){if(!window._DTS.activeTrialId||!window._DTS.activeBranchId){_dtWarnOrLog('请先创建试炼再进行故障注入');return}try{var r=await fetch('/api/v1/twin-trials/'+window._DTS.activeTrialId+'/branches/'+window._DTS.activeBranchId+'/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_type:et,payload:{}})});var d=await r.json();handleTrialEvent({type:'chaos_injected',data:d});var hist=document.getElementById('inject-history-list');if(hist){var now=new Date();var curStep=window._DTS.currentStep||(window._sx?window._sx.currentStep:0)||0;var item=document.createElement('div');item.className='inject-item';item.innerHTML='<span class="inj-type" style="color:var(--amber)">💥 '+et+'</span><span class="inj-step">@step '+curStep+'</span><span class="inj-time">'+now.toLocaleTimeString()+'</span>';hist.insertBefore(item,hist.firstChild);if(hist.children.length>20){hist.removeChild(hist.lastChild)}}_dtWarnOrLog('故障注入: '+et)}catch(e){_dtWarnOrLog('注入失败: '+(e.message||'服务异常'))}}
async function evaluateTrial(){var _tid=window._DTS.activeTrialId||(window._sx&&window._sx.trialId);if(!_tid){_dtWarnOrLog('请先创建并运行一次试炼再评分');return}_dtLogConsole('📊 评分中...','eval');try{var r=await fetch('/api/v1/twin-trials/'+_tid+'/evaluate',{method:'POST'});var d=await r.json();var er=document.getElementById('eval-results');if(er)er.style.display='';renderRadarChart(d,window._lastEvalForOverlay||null);renderBarChart(d);window._lastEvalForOverlay=d;if(typeof _checkEvolutionSuggestion==='function')_checkEvolutionSuggestion(d);if(typeof loadGenerationCurve==='function')loadGenerationCurve();if(d.ratchet){_dtLogConsole(d.ratchet.advanced?('🏆 棘轮推进 → gen'+d.ratchet.generation):('棘轮: '+(d.ratchet.reason||'未推进')),d.ratchet.advanced?'success':'info')}_dtLogConsole('评分完成: 韧性'+Math.round((d.resilience||0)*100)+'% 总分'+Math.round((d.total_score||0)*100)+'%','success');_dtAutoCostRatchet()}catch(e){_dtWarnOrLog('评分失败')}}
// 13.3: 评分/反哺成功后自动尝试推进 cost_efficiency 棘轮（只进不退，失败静默）
async function _dtAutoCostRatchet(){try{var tid=window._selectedTeamId||(window._DTS&&window._DTS.directorConfig&&window._DTS.directorConfig.team_id)||'';if(!tid)return;var r=await fetch('/api/v1/cost/tokens/ratchet/advance',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({team_id:tid})});var d=await r.json();if(d&&d.advanced){_dtLogConsole('🔒 成本棘轮推进 → gen'+(d.generation!=null?d.generation:'?')+' · 效率锁定 '+(d.efficiency!=null?Number(d.efficiency).toFixed(4):(d.value!=null?d.value:'')),'success')}else{_dtLogConsole('成本棘轮未推进: '+((d&&(d.reason||d.hint))||'效率未达标'),'info')}}catch(e){}}
async function extractSop(){if(!window._DTS.activeTrialId)return;try{var r=await fetch('/api/v1/twin-trials/'+window._DTS.activeTrialId+'/extract-sop',{method:'POST'});var d=await r.json();renderSopList(d.sops);var sr=document.getElementById('sop-results');if(sr)sr.style.display=''}catch(e){}}
async function feedbackAgents(){var _tid=window._DTS.activeTrialId||(window._sx&&window._sx.trialId);if(!_tid){_dtWarnOrLog('请先创建并运行一次试炼再反哺');return}_dtLogConsole('🔄 反哺中...','info');try{var r=await fetch('/api/v1/twin-trials/'+_tid+'/feedback',{method:'POST'});var d=await r.json();_dtWarnOrLog('反哺完成: '+d.applied_sops+' SOP');_dtLogConsole('反哺: '+d.applied_sops+' SOP','info');_dtAutoCostRatchet()}catch(e){_dtWarnOrLog('反哺失败: '+(e.message||'服务异常'))}}
function viewReport(){evaluateTrial()}
function resetForNew(){window._DTS.activeTrialId=null;window._DTS.activeTrial=null;window._DTS.activeBranchId=null;if(window._sx)window._sx.sessionId=null;window._DTS.currentStep=0;window._DTS.processedStepSet.clear();window._DTS.events=[];transitionTrialStatus(window._DTS.trialStatus,'idle')}
function selectMode(m){window._DTS.selectedMode=m;document.querySelectorAll('.mode-card').forEach(function(c){c.classList.remove('mode-active')});var s=document.querySelector('.mode-card[data-mode="'+m+'"]');if(s)s.classList.add('mode-active')}
function onDirectorTeamChange(tid){window._DTS.directorConfig.team_id=tid}
async function showBranchManager(tid){var p=document.getElementById('branch-manager'),l=document.getElementById('branch-list');if(!p)return;p.style.display='';try{var r=await fetch('/api/v1/twin-trials/'+tid+'/branches');var d=await r.json();l.innerHTML='';(d.branches||[]).forEach(function(b){var it=document.createElement('div');it.className='branch-item'+(b.id===window._DTS.activeBranchId?' branch-active':'');it.innerHTML='<span class="branch-dot" style="background:'+b.color+'"></span><span class="branch-name">'+b.label+'</span>';it.onclick=function(){switchBranch(b.id)};l.appendChild(it)})}catch(e){l.innerHTML='<div style="color:var(--dim)">fail</div>'}}
function switchBranch(bid){
  window._DTS.activeBranchId=bid;
  if(window._sx){window._sx.branchId=bid}
  // P4-02: 切换分支后刷新 UI
  // 1. 高亮当前分支条目
  var items=document.querySelectorAll('.branch-item');
  items.forEach(function(it){it.classList.toggle('branch-active',false)});
  // 2. 刷新注入历史
  if(typeof loadExerciseHistory==='function')loadExerciseHistory();
  // 3. 同步事件/时间线
  if(window._sx){window._sx.events=[]}
  _logConsole('[DT] 切换到分支: '+bid,'info');
}
window._addToTimeline=function(e){if(!e)return;var tl=document.querySelector('.trial-timeline');if(!tl)return;var c='tl-normal';if(e.type==='chaos_injected')c='tl-fault';else if(e.type.includes('branch'))c='tl-fork';else if(e.type==='sop_extracted')c='tl-sop';else if(e.global_reward!==undefined)c=(window._DTS.latestReward||0)<(e.global_reward||0)?'tl-reward-up':'tl-reward-down';else return;var dot=document.createElement('div');dot.className='tl-dot '+c;tl.appendChild(dot)}
function renderRadarChart(ed, overlay){if(!ed)return;var c=document.getElementById('radar-chart-area');if(!c)return;
  // v4 D-2.3/D-3.3: 修复数据多边形缺失 + 支持叠加层（基线/上一代 = 虚线）
  var DIM_KEYS=[['目标完成度','task_completion'],['协作效率','collaboration_efficiency'],['韧性评分','resilience'],['成本控制','cost_efficiency'],['可萃取性','extractability']];
  var cx=140,cy=120,r=90,n=DIM_KEYS.length,s='<svg viewBox="0 0 280 240">';
  function pt(val,i){var a=Math.PI*2*i/n-Math.PI/2;return (cx+r*val*Math.cos(a)).toFixed(1)+','+(cy+r*val*Math.sin(a)).toFixed(1);}
  for(var lv=5;lv>=1;lv--){var pts=[];DIM_KEYS.forEach(function(d,i){pts.push(pt(lv/5,i))});s+='<polygon points="'+pts.join(' ')+'" fill="none" stroke="rgba(255,255,255,.08)"/>';}
  DIM_KEYS.forEach(function(d,i){var a=Math.PI*2*i/n-Math.PI/2;s+='<text x="'+(cx+(r+20)*Math.cos(a)).toFixed(1)+'" y="'+(cy+(r+20)*Math.sin(a)).toFixed(1)+'" fill="#888" font-size="9" text-anchor="middle">'+d[0]+'</text>';});
  if(overlay){var op=[];DIM_KEYS.forEach(function(d,i){op.push(pt(Math.max(0,Math.min(1,overlay[d[1]]||0)),i))});s+='<polygon points="'+op.join(' ')+'" fill="rgba(167,139,250,.10)" stroke="#a78bfa" stroke-width="1.2" stroke-dasharray="4 3"/>';}
  var dp=[];DIM_KEYS.forEach(function(d,i){dp.push(pt(Math.max(0,Math.min(1,ed[d[1]]||0)),i))});s+='<polygon points="'+dp.join(' ')+'" class="radar-polygon"/>';
  if(overlay){s+='<text x="14" y="14" fill="#a78bfa" font-size="8">- - 对照(基线/上代)</text><text x="14" y="26" fill="#22d3ee" font-size="8">— 当前</text>';}
  c.innerHTML=s+'</svg>';
  var rd=document.getElementById('resilience-detail-area');if(rd){var resVal=Math.round((ed.resilience||0)*100);var insight='🛡️ '+resVal+'%';if(resVal>=90)insight+=' — 系统高度抗扰';else if(resVal>=70)insight+=' — 有一定抗扰能力';else insight+=' — 抗扰较弱';rd.innerHTML=insight}}
function renderBarChart(ed){if(!ed)return;var c=document.getElementById('bar-chart-area');if(!c)return;var rows=[['目标完成',ed.task_completion||0,'#22d3ee'],['协作效率',ed.collaboration_efficiency||0,'#34d399'],['韧性评分',ed.resilience||0,'#f59e0b'],['成本控制',ed.cost_efficiency||0,'#a78bfa'],['可萃取性',ed.extractability||0,'#f472b6']];var h='<div style="display:flex;flex-direction:column;gap:4px">';rows.forEach(function(r){h+='<div style="display:flex;align-items:center;gap:6px"><span style="width:60px;font-size:9px;color:#888;text-align:right">'+r[0]+'</span><div style="flex:1;height:14px;background:rgba(255,255,255,.05);border-radius:2px"><div style="height:100%;width:'+(r[1]*100)+'%;background:'+r[2]+';border-radius:2px;transition:width .6s ease-out"></div></div><span style="font-size:9px;color:var(--dim);width:35px;text-align:right">'+Math.round(r[1]*100)+'%</span></div>'});var insights=(ed.key_insights&&ed.key_insights.length)?ed.key_insights.join(' · '):'';h+='<div class="resilience-detail">🛡️ 韧性: '+Math.round((ed.resilience||0)*100)+'% | 总分: '+Math.round((ed.total_score||0)*100)+'%'+(insights?'<br>💡 '+insights:'')+'</div>';c.innerHTML=h+'</div>'}
function renderSopList(ss){var c=document.getElementById('sop-list-area');if(!c)return;c.innerHTML=!ss||!ss.length?'<div style="color:#888;padding:10px">暂无SOP</div>':ss.map(function(s){return '<div style="padding:10px;border:1px solid var(--border);border-radius:6px;margin-bottom:4px"><b style="color:#fbbf24">'+s.name+'</b> <span style="color:#4ade80">'+Math.round(s.confidence*100)+'%</span></div>'}).join('')}
// ═══ 试炼导演台状态对象初始化 ═══
// D-0.1: _DTS 代理到 _sx 单一数据源 — trialStatus/activeTrialId/activeBranchId/currentStep/events/processedStepSet 读写均走 _sx
(function() {
  'use strict';
  var _sx = window._sx || {};
  // 确保 _sx 字段就绪
  _sx.trialId = _sx.trialId || null;
  _sx.branchId = _sx.branchId || null;
  _sx.currentStep = _sx.currentStep || 0;
  _sx.status = _sx.status || 'idle';
  _sx.roomAgentMap = _sx.roomAgentMap || {};
  _sx.events = _sx.events || [];
  _sx.processedStepSet = _sx.processedStepSet || new Set();

  // 内部独立字段（不共享给 _sx，仅导演台使用）
  var _independent = {
    selectedMode: 'what_if',
    directorConfig: { team_id: '' },
    activeTrial: null,
    latestReward: 0,
    _abortCtrl: null
  };

  window._DTS = new Proxy({}, {
    get: function(target, prop) {
      if (prop === 'trialStatus') return _sx.status;
      if (prop === 'activeTrialId') return _sx.trialId;
      if (prop === 'activeBranchId') return _sx.branchId;
      if (prop === 'currentStep') return _sx.currentStep;
      if (prop === 'events') return _sx.events;
      if (prop === 'processedStepSet') return _sx.processedStepSet;
      if (prop in _independent) return _independent[prop];
      return undefined;
    },
    set: function(target, prop, value) {
      if (prop === 'trialStatus') { _sx.status = value; return true; }
      if (prop === 'activeTrialId') { _sx.trialId = value; return true; }
      if (prop === 'activeBranchId') { _sx.branchId = value; return true; }
      if (prop === 'currentStep') { _sx.currentStep = value; return true; }
      if (prop === 'events') { _sx.events = value; return true; }
      if (prop === 'processedStepSet') { _sx.processedStepSet = value; return true; }
      if (prop in _independent) { _independent[prop] = value; return true; }
      console.warn('[DT] _DTS ignore write:', prop);
      return true;
    },
    has: function(target, prop) {
      return prop === 'trialStatus' || prop === 'activeTrialId' || prop === 'activeBranchId' ||
             prop === 'currentStep' || prop === 'events' || prop === 'processedStepSet' ||
             prop in _independent;
    }
  });
})();

// ═══ 状态转换机 ═══
function transitionTrialStatus(from, to) {
  var valid = {
    idle:['creating'], creating:['ready','failed','idle'],
    ready:['running','evaluating','failed'], running:['paused','evaluating','completed','failed','terminated'],
    paused:['running','terminated','failed'], evaluating:['completed','failed','terminated'],
    completed:['idle','terminated'], failed:['idle','terminated'], terminated:['idle','creating']
  };
  if (from && window._DTS.trialStatus !== from) return false;
  if (!valid[from] || !valid[from].includes(to)) { console.warn('[DT] invalid transition:', from, '→', to); return false; }
  window._DTS.trialStatus = to;
  window._updateButtonStates(to);
  document.getElementById('dp-status-badge').textContent = {
    idle:'● 就绪', creating:'⏳ 创建中...', ready:'● 就绪', running:'▶ 运行中', paused:'⏸ 已暂停',
    evaluating:'⏳ 评分中', completed:'✓ 已完成', failed:'✗ 失败', terminated:'■ 已终止'
  }[to] || '● ' + to;
  return true;
}

// ═══ 事件处理（时间线 + 日志） ═══
function handleTrialEvent(e) {
  if (!e) return;
  _addToTimeline(e);
  // 控制台日志
  var msg = '';
  if (e.type === 'step') msg = '步进 #' + (e.step_index||'?') + (e.global_reward!==undefined ? ' | reward: '+e.global_reward : '');
  else if (e.type === 'chaos_injected') msg = '💥 混沌注入';
  else if (e.type === 'branch_forked') msg = '🔀 分支创建';
  else if (e.type === 'sop_extracted') msg = '📋 SOP提取';
  else msg = e.type;
  if (msg && typeof _logConsole === 'function') _logConsole('[DT] '+msg,'info');
  // 更新 reward 追踪
  if (e.global_reward !== undefined) {
    window._DTS.latestReward = e.global_reward;
    _updateRewardHeat(e.global_reward);
  }
}

// ── P3-04: Reward 热力反馈 ──
var _lastReward = 0;
function _updateRewardHeat(reward) {
  var rooms = document.querySelectorAll('.room-cell,.env-room');
  rooms.forEach(function(r){
    r.classList.remove('room-heat-up','room-heat-down','room-heat-peak');
  });
  if (reward > _lastReward * 1.15) {
    rooms.forEach(function(r){ r.classList.add('room-heat-up'); });
  } else if (reward < _lastReward * 0.85) {
    rooms.forEach(function(r){ r.classList.add('room-heat-down'); });
  }
  if (reward > 0.9) {
    rooms.forEach(function(r){ r.classList.add('room-heat-peak'); });
  }
  _lastReward = reward;
}

// ── F4-1 (v4 D-0.2): 单一数据源 — _sx.roomAgentMap 与 S.positions 引用合一 ──
// 同一对象，写任一侧即时一致；定时器仅做"引用断裂检测"（S.positions 被整体替换时重新合一）
// 规范读入口: window._roomPositions() 始终返回合一的 positions 对象
window._roomPositions = function(){ return window._sx && window._sx.roomAgentMap; };
function _syncRoomAgentMap() {
  if (typeof S === 'undefined' || !S.positions || !window._sx) return;
  if (window._sx.roomAgentMap === S.positions) return;  // 已合一
  // 首次合一或断裂修复: 把 _sx 侧既有键迁入 S.positions，然后共享引用
  var old = window._sx.roomAgentMap;
  if (old && typeof old === 'object') {
    for (var k in old) {
      if (old.hasOwnProperty(k) && !(k in S.positions)) S.positions[k] = old[k];
    }
  }
  window._sx.roomAgentMap = S.positions;
  console.log('[DT] roomAgentMap 已与 S.positions 引用合一 (单一数据源)');
}
function _dtOwnKeyCount(obj) {
  if (!obj || typeof obj !== 'object') return 0;
  return Object.keys(obj).length;
}
function _renderDtRoomMapHealth(health) {
  var el = document.getElementById('dt-room-map-health');
  if (!el) return;
  var ok = !!(health && health.same_ref);
  var pending = !!(health && (!health.has_sx || !health.has_positions));
  el.className = 'dt-health-badge ' + (ok ? 'dt-health-badge--ok' : (pending ? 'dt-health-badge--pending' : 'dt-health-badge--bad'));
  el.textContent = ok ? ('单源 ' + health.positions_count) : (pending ? '等待' : '断裂');
  el.title = 'roomAgentMap/S.positions same_ref=' + ok + ' positions=' + (health.positions_count || 0) + ' sx=' + (health.sx_count || 0);
}
window._dtRoomMapHealth = function(){
  _syncRoomAgentMap();
  var hasPositions = typeof S !== 'undefined' && !!S.positions;
  var hasSx = !!window._sx;
  var positions = hasPositions ? S.positions : {};
  var sxMap = hasSx && window._sx.roomAgentMap ? window._sx.roomAgentMap : {};
  var health = {
    has_sx: hasSx,
    has_positions: hasPositions,
    same_ref: !!(hasSx && hasPositions && window._sx.roomAgentMap === S.positions),
    positions_count: _dtOwnKeyCount(positions),
    sx_count: _dtOwnKeyCount(sxMap)
  };
  _renderDtRoomMapHealth(health);
  return health;
};
window._dtRoomMapHealth();
window.addEventListener('DOMContentLoaded', window._dtRoomMapHealth);
window.addEventListener('load', window._dtRoomMapHealth);
setInterval(window._dtRoomMapHealth, 2000);  // 引用断裂检测 + 页面诊断刷新

var _BG={idle:'<div style="width:100%;text-align:center;font-size:11px;color:var(--dim);padding:8px 0;line-height:1.5">👆 点上方绿色「▶ 沙箱推演」按钮创建并就绪试炼<br>（统一创建入口：读取仿真参数 + 场景守卫）</div>',
creating:'<button class="btn-disabled" disabled style="width:100%">⏳ 创建中...</button>',
ready:'<div style="display:flex;gap:4px;width:100%"><button class="btn btn-accent" onclick="stepOnce()" style="flex:1">▶ 单步</button><button class="btn btn-primary" onclick="autoRun()" style="flex:1">▶▶ 自动</button><button class="btn btn-warning" onclick="showInjectDropdown()" style="flex:1">💥 注入</button></div>',
running:'<button class="btn btn-warning" onclick="pauseSim()" style="width:100%">⏸ 暂停</button>',
paused:'<div style="display:flex;gap:4px;width:100%"><button class="btn btn-accent" onclick="stepOnce()" style="flex:1">▶ 继续</button><button class="btn btn-primary" onclick="autoRun()" style="flex:1">▶▶ 自动</button><button class="btn btn-danger" onclick="terminate()" style="flex:1">⏹ 终止</button></div>',
evaluating:'<button class="btn-disabled" disabled style="width:100%">⏳ 评分中...</button>',
completed:'<div style="display:flex;gap:4px;flex-wrap:wrap"><button class="btn btn-info" onclick="viewReport()">📊 评分</button><button class="btn btn-success" onclick="extractSop()">📋 SOP</button><button class="btn btn-primary" onclick="feedbackAgents()">🔄 反哺</button><button class="btn btn-secondary" onclick="resetForNew()">🔁 新试炼</button></div>',
failed:'<button class="btn btn-secondary" onclick="resetForNew()" style="width:100%">🔁 新试炼</button>',
terminated:'<button class="btn btn-secondary" onclick="resetForNew()" style="width:100%">🔁 新试炼</button>'};
window._updateButtonStates=function(s){var c=document.getElementById('dt-action-buttons');if(c)c.innerHTML=_BG[s]||_BG.idle};
// 导演台与SECS团队同步 + 初始化
window.addEventListener('DOMContentLoaded',function(){
  window._updateButtonStates(window._DTS.trialStatus);
  // 团队同步：从SECS的_selectedTeamId同步到导演台
  var syncTeam = function() {
    var el = document.getElementById('dp-team-display');
    if (!el) return;
    if (typeof _selectedTeamId !== 'undefined' && _selectedTeamId) {
      el.textContent = (_selectedTeamName||_selectedTeamId) + ' (' + (window._agentCountForTeam||'?') + ' 智能体)';
      el.style.color = 'var(--cyan)';
      window._DTS.directorConfig.team_id = _selectedTeamId;
    } else {
      el.textContent = '— 等待 SECS 选择团队 —';
      el.style.color = 'var(--dim)';
    }
  };
  syncTeam();
  // 定期同步（SECS选择团队后）
  setInterval(syncTeam, 1000);
});
