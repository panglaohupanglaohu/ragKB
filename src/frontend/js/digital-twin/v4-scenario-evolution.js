/**
 * AgentsGroup2026 — Agent Digital Twin: v4 场景化演练 × 技能进化 (场景选择/进化面板/代际)
 * 从 Agent-digital-twin.html 内联脚本拆出 (frontendBigChange F2)。
 * 加载顺序: secs-core.js → director.js → v4-scenario-evolution.js
 */
// ═══════════════════════════════════════════════════════════
// v4: 场景化演练 × 技能进化 (D-0 状态收敛 / D-1 场景选择 / D-2 进化面板)
// ═══════════════════════════════════════════════════════════

// ── D-0.1: _sx 扩展为唯一真源 + _currentSessionId 降级为别名 ──
(function(){
  if (!window._sx) return;
  var sx = window._sx;
  sx.scenarioId = sx.scenarioId || '';
  sx.scenarioSpec = sx.scenarioSpec || null;
  sx.generation = sx.generation || 0;
  sx.parentTrialId = sx.parentTrialId || '';
  sx.skillStats = sx.skillStats || null;
  sx.evolutionRunId = sx.evolutionRunId || null;
  try {
    var legacy = window._currentSessionId;
    if (legacy !== undefined && legacy !== null) sx.sessionId = sx.sessionId || legacy;
    delete window._currentSessionId;
    var warned = false;
    Object.defineProperty(window, '_currentSessionId', {
      get: function(){
        if (!warned) { console.warn('[DT][deprecated] _currentSessionId 已是 _sx.sessionId 的别名'); warned = true; }
        return sx.sessionId;
      },
      set: function(v){ sx.sessionId = v; },
      configurable: true
    });
  } catch(e) { console.warn('[DT] _currentSessionId 别名化失败(不影响功能):', e); }
})();

// ── D-1.1: 场景列表加载 ──
async function loadScenarioList(){
  var sel = document.getElementById('dp-scenario-select');
  if (!sel) return;
  try {
    var r = await fetch('/api/v1/scenarios');
    var d = await r.json();
    (d.scenarios || []).forEach(function(s){
      var opt = document.createElement('option');
      opt.value = s.scenario_id;
      var stars = '★'.repeat(s.difficulty || 1);
      opt.textContent = s.name + ' ' + stars + (s.best_score != null ? (' · 最佳' + Math.round(s.best_score*100) + '%') : '');
      sel.appendChild(opt);
    });
    window._scenarioIndex = {};
    (d.scenarios || []).forEach(function(s){ window._scenarioIndex[s.scenario_id] = s; });
  } catch(e) { console.warn('[DT] 场景列表加载失败:', e); }
}

// ── D-1.1/D-1.2: 场景选择 ──
async function onScenarioChange(sid){
  if (window._sx) window._sx.scenarioId = sid;
  var info = document.getElementById('dp-scenario-info');
  if (!sid) { if (info) info.innerHTML = ''; if (window._sx) window._sx.scenarioSpec = null; return; }
  var meta = (window._scenarioIndex || {})[sid];
  try {
    var r = await fetch('/api/v1/scenarios/' + encodeURIComponent(sid));
    var spec = await r.json();
    if (window._sx) window._sx.scenarioSpec = spec;
    // 推荐步数回填
    var ms = document.getElementById('dp-max-steps');
    if (ms && spec.recommended_max_steps) ms.value = spec.recommended_max_steps;
    var html = (spec.description || '') +
      '<br>🏠 ' + (spec.world.rooms||[]).length + ' 房间 · 📋 ' + (spec.taskflow||[]).length + ' 任务 · 🌀 ' + (spec.chaos_script||[]).length + ' 个混沌阶段';
    // 角色匹配度
    var tid = (typeof _selectedTeamId !== 'undefined' && _selectedTeamId) || (window._DTS && window._DTS.directorConfig.team_id) || '';
    if (tid) {
      try {
        var mr = await fetch('/api/v1/scenarios/' + encodeURIComponent(sid) + '/match?team_id=' + encodeURIComponent(tid));
        var m = await mr.json();
        var pct = Math.round((m.match_rate||0)*100);
        var color = pct >= 70 ? 'var(--green)' : (pct >= 40 ? 'var(--amber)' : 'var(--red)');
        html += '<br><span style="color:'+color+'">匹配度 ' + pct + '%</span>';
        if (m.missing_skills && m.missing_skills.length) html += ' · 缺: ' + m.missing_skills.slice(0,3).join(', ');
      } catch(e2) {}
    }
    // GP2-5: 显示该场景的棘轮纪录（要打破的历史最佳）
    try {
      var rr = await fetch('/api/v1/ratchet/metrics?prefix=' + encodeURIComponent('scenario_best:' + sid));
      var rd2 = await rr.json();
      if (rd2.metrics && rd2.metrics.length) {
        var rec = rd2.metrics[0];
        html += '<br><span style="color:var(--amber)">🏆 棘轮纪录 gen' + rec.generation + ' · 最佳 ' + Math.round(rec.value*100) + '%（本次要打破的纪录）</span>';
      }
    } catch(e3) {}
    if (info) info.innerHTML = html;
    if (typeof _dtLogConsole === 'function') _dtLogConsole('已选择业务场景: ' + (spec.name||sid), 'info');
  } catch(e) { if (info) info.innerHTML = '<span style="color:var(--red)">场景详情加载失败</span>'; }
}

// ── D-1.3: 场景房间渲染（env-grid 2D 视图 + S.rooms 同步） ──
function applyScenarioRooms(rooms){
  if (!rooms || !rooms.length) return;
  // 同步给既有 S.rooms（3D/其他视图消费）
  try {
    if (window.S) {
      window.S.rooms = rooms.map(function(r){
        return { id: r.room_id, name: r.name, icon: r.icon, capacity: r.capacity, stage: r.stage };
      });
    }
  } catch(e) {}
  var grid = document.getElementById('env-grid');
  if (!grid) return;
  grid.style.display = '';
  grid.innerHTML = rooms.map(function(r){
    return '<div class="env-room" data-room-id="' + r.room_id + '">' +
      '<div class="room-icon">' + (r.icon||'🏠') + '</div>' +
      '<div class="room-name">' + r.name + ' <span style="font-size:9px;color:var(--cyan)">阶段' + (r.stage!=null?r.stage:'-') + '</span></div>' +
      '<div class="room-desc">业务阶段 ' + (r.stage!=null?r.stage:'-') + ' · 容量 ' + (r.capacity||6) + '</div>' +
      '<div class="room-agents"></div>' +
      '<div class="room-footer"><span>scenario room</span><span>0/' + (r.capacity||6) + '</span></div>' +
      '<div class="drop-hint">放置 Agent 到此业务阶段</div></div>';
  }).join('');
  if (typeof _dtLogConsole === 'function') _dtLogConsole('环境空间已切换为场景房间 (' + rooms.length + ' 间)', 'success');
}

// ── D-2.1: 技能统计 ──
async function loadSkillStats(){
  var area = document.getElementById('skill-stats-area');
  var tid = window._DTS && window._DTS.activeTrialId;
  if (!tid) { if (area) area.innerHTML = '<span style="color:var(--amber)">请先创建并运行试炼</span>'; return; }
  try {
    var r = await fetch('/api/v1/twin-trials/' + encodeURIComponent(tid) + '/skill-stats');
    var d = await r.json();
    if (window._sx) window._sx.skillStats = d;
    if (!d.skills || !d.skills.length) { area.innerHTML = '暂无技能使用记录（先步进/自动运行）'; return; }
    var h = '';
    d.skills.forEach(function(s){
      var pct = Math.round(s.success_rate * 100);
      var ok = s.meets_expectation;
      var color = ok ? 'var(--green)' : 'var(--red)';
      h += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">' +
        '<span style="width:90px;font-size:9px;color:' + (ok?'var(--dim)':'var(--red)') + ';text-align:right;overflow:hidden;text-overflow:ellipsis">' + (ok?'':'⚠ ') + s.skill_name + '</span>' +
        '<div style="flex:1;height:12px;background:rgba(255,255,255,.05);border-radius:2px"><div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:2px"></div></div>' +
        '<span style="font-size:9px;color:var(--dim);width:60px">' + pct + '%/' + Math.round(s.expected_success_rate*100) + '% ×' + s.total_uses + '</span></div>';
    });
    if (d.weak_skills && d.weak_skills.length) {
      h += '<div style="color:var(--amber);margin-top:4px">⚠ 低于期望: ' + d.weak_skills.join(', ') + ' — 可发起进化</div>';
    }
    area.innerHTML = h;
  } catch(e) { area.innerHTML = '<span style="color:var(--red)">技能统计加载失败: ' + (e.message||'') + '</span>'; }
}

// ── D-2.2: 发起进化 + 轮询进度 ──
var _evoPollTimer = null;
async function startEvolution(){
  var teamId = (typeof _selectedTeamId !== 'undefined' && _selectedTeamId) || (window._DTS && window._DTS.directorConfig.team_id) || '';
  if (!teamId) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('请先选择团队'); return; }
  var body = {
    team_id: teamId,
    scenario_id: (window._sx && window._sx.scenarioId) || '',
    skill_ids: (window._sx && window._sx.skillStats && window._sx.skillStats.weak_skills) || [],
    baseline_trial_id: (window._DTS && window._DTS.activeTrialId) || '',
    auto_apply: false
  };
  try {
    var r = await fetch('/api/v1/twin-evolution/runs', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
    var d = await r.json();
    if (!r.ok) throw new Error(d.detail || ('HTTP ' + r.status));
    if (window._sx) window._sx.evolutionRunId = d.run_id;
    document.getElementById('evo-pipeline').style.display = '';
    document.getElementById('evo-result-area').innerHTML = '运行中: ' + d.run_id;
    if (typeof _dtLogConsole === 'function') _dtLogConsole('🧬 进化运行启动: ' + d.run_id, 'info');
    if (_evoPollTimer) clearInterval(_evoPollTimer);
    _evoPollTimer = setInterval(pollEvolutionRun, 1500);
  } catch(e) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('进化启动失败: ' + (e.message||'')); }
}

async function pollEvolutionRun(){
  var rid = window._sx && window._sx.evolutionRunId;
  if (!rid) { clearInterval(_evoPollTimer); return; }
  try {
    var r = await fetch('/api/v1/twin-evolution/runs/' + encodeURIComponent(rid));
    var run = await r.json();
    _renderEvoPipeline(run.status);
    var area = document.getElementById('evo-result-area');
    var gate = document.getElementById('evo-gate-actions');
    if (run.status === 'gating' && run.winner) {
      clearInterval(_evoPollTimer);
      gate.style.display = 'flex';
      area.innerHTML = '<span style="color:var(--green)">胜出: ' + run.winner.strategy +
        ' · fitness ' + (run.winner.fitness||0).toFixed(3) + ' (基线 ' + (run.winner.baseline_fitness||0).toFixed(3) + ', +' +
        Math.round((run.winner.improvement||0)*100) + 'pp)</span><br><span style="color:var(--dim)">技能: ' + run.winner.skill_name + ' — 等待人工裁决</span>';
      _renderAbCompare(run);  // D-2.3: A/B 对比卡 + diff
    } else if (run.status === 'applied') {
      clearInterval(_evoPollTimer);
      gate.style.display = 'none';
      area.innerHTML = '<span style="color:var(--green)">✓ 已写回 ' + (run.winner ? run.winner.skill_name + ' v' + (run.winner.new_version||'?') : '') +
        '</span> <button class="btn btn-accent" style="font-size:9px;padding:3px 8px" onclick="nextGeneration()">⏭ 再战一代</button>';
      if (typeof _dtLogConsole === 'function') _dtLogConsole('🧬 进化完成并写回技能库', 'success');
    } else if (run.status === 'rejected' || run.status === 'failed') {
      clearInterval(_evoPollTimer);
      gate.style.display = 'none';
      area.innerHTML = '<span style="color:var(--red)">✗ ' + run.status + ': ' + (run.error||'') + '</span>';
    } else {
      area.innerHTML = '阶段: ' + run.status + (run.candidates && run.candidates.length ? ' · ' + run.candidates.length + ' 个变体' : '');
    }
  } catch(e) { console.warn('[DT] 进化轮询失败:', e); }
}

function _renderEvoPipeline(status){
  var order = ['identifying','reflecting','mutating','ab_testing','gating'];
  var idx = order.indexOf(status);
  document.querySelectorAll('#evo-pipeline .secs-node').forEach(function(n){
    var p = n.getAttribute('data-phase');
    var pi = order.indexOf(p);
    n.classList.remove('secs-active','secs-done');
    if (status === 'applied' || pi < idx) n.classList.add('secs-done');
    else if (pi === idx) n.classList.add('secs-active');
  });
}

async function approveEvolution(){
  var rid = window._sx && window._sx.evolutionRunId;
  if (!rid) return;
  try {
    var r = await fetch('/api/v1/twin-evolution/runs/' + encodeURIComponent(rid) + '/approve', { method:'POST' });
    var d = await r.json();
    if (!r.ok) throw new Error(d.detail || ('HTTP ' + r.status));
    _evoPollTimer = setInterval(pollEvolutionRun, 800);
  } catch(e) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('批准失败: ' + (e.message||'')); }
}

async function rejectEvolution(){
  var rid = window._sx && window._sx.evolutionRunId;
  if (!rid) return;
  try {
    await fetch('/api/v1/twin-evolution/runs/' + encodeURIComponent(rid) + '/reject', { method:'POST' });
    _evoPollTimer = setInterval(pollEvolutionRun, 800);
  } catch(e) {}
}

// ── D-3: 代际续跑 — 带着进化后的技能再战一代 ──
function nextGeneration(){
  if (window._sx) {
    window._sx.parentTrialId = (window._DTS && window._DTS.activeTrialId) || '';
    window._sx.generation = (window._sx.generation || 0) + 1;
  }
  if (typeof resetForNew === 'function') resetForNew();
  if (typeof _dtLogConsole === 'function') _dtLogConsole('⏭ 进入第 ' + window._sx.generation + ' 代试炼（继承进化后技能），点击"创建试炼"开始', 'info');
  if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('第 ' + window._sx.generation + ' 代就绪，点击创建试炼');
}

// ── D-1.4: AI 生成场景入口 ──
async function generateScenarioFromDesc(){
  var desc = prompt('描述你的业务场景（如：电商大促期间的库存补货协同流程）：');
  if (!desc || !desc.trim()) return;
  var tid = (typeof _selectedTeamId !== 'undefined' && _selectedTeamId) || '';
  if (typeof _dtLogConsole === 'function') _dtLogConsole('✨ LLM 生成场景中（最多重试 3 次）...', 'info');
  try {
    var r = await fetch('/api/v1/scenarios/generate', { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ description: desc, team_id: tid }) });
    var d = await r.json();
    if (!r.ok) throw new Error((d.detail && (d.detail.message||d.detail)) || ('HTTP '+r.status));
    var spec = d.draft;
    var summary = '场景草稿: ' + spec.name + '\n房间: ' + (spec.world.rooms||[]).map(function(x){return x.name}).join('/') +
      '\n任务: ' + (spec.taskflow||[]).length + ' 个 · 混沌阶段: ' + (spec.chaos_script||[]).length + ' 个\n\n保存到场景库？';
    if (!confirm(summary)) { if (typeof _dtLogConsole === 'function') _dtLogConsole('场景草稿已丢弃', 'info'); return; }
    var sr = await fetch('/api/v1/scenarios', { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ spec: spec }) });
    var sd = await sr.json();
    if (!sr.ok) throw new Error(JSON.stringify(sd.detail||sd));
    if (typeof _dtLogConsole === 'function') _dtLogConsole('✅ 场景已保存: ' + sd.scenario_id, 'success');
    // 重载场景列表并选中
    var sel = document.getElementById('dp-scenario-select');
    if (sel) { while (sel.options.length > 1) sel.remove(1); await loadScenarioList(); sel.value = sd.scenario_id; onScenarioChange(sd.scenario_id); }
  } catch(e) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('场景生成失败: ' + (e.message||'')); }
}

// ── D-2.5: 进化建议提示条（评分后检查弱 skill） ──
function _checkEvolutionSuggestion(ev){
  var area = document.getElementById('evo-result-area');
  if (!area || !ev) return;
  var weak = [];
  (ev.skill_breakdown || []).forEach(function(s){
    if ((s.success_rate||0) < 0.6) weak.push(s.skill_name);
  });
  if (weak.length) {
    area.innerHTML = '<div style="padding:6px 8px;background:rgba(251,191,36,.08);border-left:2px solid var(--amber);border-radius:4px;color:var(--amber)">' +
      '⚠ 本次试炼 ' + weak.length + ' 项技能低于预期（' + weak.slice(0,3).join(', ') + (weak.length>3?'…':'') + '）' +
      ' <a href="javascript:startEvolution()" style="color:var(--cyan)">去进化 →</a></div>';
    if (window._sx) window._sx.skillStats = { weak_skills: weak };
  }
}

// ── D-2.3: A/B 对比卡 + instructions 行级 diff ──
function _diffLines(orig, evolved){
  var a = (orig||'').split('\n'), b = (evolved||'').split('\n');
  var setA = {}; a.forEach(function(l){ setA[l] = true; });
  var setB = {}; b.forEach(function(l){ setB[l] = true; });
  var h = '';
  a.forEach(function(l){ if (!setB[l] && l.trim()) h += '<div style="color:var(--red)">- ' + _escDiff(l) + '</div>'; });
  b.forEach(function(l){ if (!setA[l] && l.trim()) h += '<div style="color:var(--green)">+ ' + _escDiff(l) + '</div>'; });
  return h || '<div style="color:var(--dim)">（无行级差异）</div>';
}
function _escDiff(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').slice(0,120); }

function _renderAbCompare(run){
  var c = document.getElementById('ab-compare-area');
  if (!c || !run || !run.candidates) return;
  var baseF = (run.winner && run.winner.baseline_fitness) || 0;
  var h = '<label class="dp-label" style="margin-top:4px">⚖️ A/B 对照</label>';
  h += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:2px"><span style="width:80px;font-size:9px;color:var(--dim);text-align:right">baseline</span>' +
       '<div style="flex:1;height:10px;background:rgba(255,255,255,.05);border-radius:2px"><div style="height:100%;width:' + Math.round(baseF*100) + '%;background:var(--dim);border-radius:2px"></div></div>' +
       '<span style="font-size:9px;color:var(--dim);width:34px">' + baseF.toFixed(3) + '</span></div>';
  run.candidates.forEach(function(cd){
    var f = cd.fitness || 0;
    var isWin = run.winner && cd.strategy === run.winner.strategy;
    h += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:2px"><span style="width:80px;font-size:9px;color:' + (isWin?'var(--green)':'var(--dim)') + ';text-align:right">' + (isWin?'🏆 ':'') + cd.strategy + '</span>' +
         '<div style="flex:1;height:10px;background:rgba(255,255,255,.05);border-radius:2px"><div style="height:100%;width:' + Math.round(f*100) + '%;background:' + (isWin?'var(--green)':'var(--purple)') + ';border-radius:2px"></div></div>' +
         '<span style="font-size:9px;color:var(--dim);width:34px">' + f.toFixed(3) + '</span></div>';
  });
  // 雷达叠加: 胜者维度 vs 基线维度
  if (run.winner && run.winner.baseline_dims) {
    var winDims = null;
    run.candidates.forEach(function(cd){ if (cd.strategy === run.winner.strategy) winDims = cd.dims; });
    if (winDims) { var er = document.getElementById('eval-results'); if (er) er.style.display=''; renderRadarChart(winDims, run.winner.baseline_dims); }
  }
  // instructions diff
  var orig = (run.target_skills && run.target_skills[0] && run.target_skills[0].instructions_snapshot) || '';
  if (run.winner && run.winner.instructions && orig) {
    h += '<details style="margin-top:4px"><summary style="font-size:9px;color:var(--cyan);cursor:pointer">📝 指令变更 diff</summary>' +
         '<div style="font-family:monospace;font-size:8.5px;max-height:120px;overflow-y:auto;background:rgba(0,0,0,.3);padding:6px;border-radius:4px;margin-top:4px">' +
         _diffLines(orig, run.winner.instructions) + '</div></details>';
  }
  c.innerHTML = h;
}

// ── D-3.2: 代际成长曲线（同场景各 generation 最佳分折线） ──
async function loadGenerationCurve(){
  var c = document.getElementById('gen-curve-area');
  var sid = window._sx && window._sx.scenarioId;
  if (!c || !sid) return;
  try {
    var r = await fetch('/api/v1/twin-trials?scenario_id=' + encodeURIComponent(sid) + '&page_size=100');
    var d = await r.json();
    var byGen = {};
    (d.trials || []).forEach(function(t){
      if (t.max_reward == null) return;
      var g = t.generation || 0;
      byGen[g] = Math.max(byGen[g] || 0, t.max_reward);
    });
    var gens = Object.keys(byGen).map(Number).sort(function(a,b){return a-b});
    if (gens.length < 1) { c.innerHTML = ''; return; }
    var W = 240, H = 50, pad = 6;
    var maxV = Math.max.apply(null, gens.map(function(g){return byGen[g]})) || 1;
    var pts = gens.map(function(g, i){
      var x = pad + (gens.length === 1 ? 0 : i * (W - 2*pad) / (gens.length - 1));
      var y = H - pad - (byGen[g] / maxV) * (H - 2*pad);
      return x.toFixed(1) + ',' + y.toFixed(1);
    });
    var svg = '<label class="dp-label">📈 代际成长（' + sid + '）</label><svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:' + H + 'px;background:rgba(0,0,0,.25);border-radius:6px">';
    svg += '<polyline points="' + pts.join(' ') + '" fill="none" stroke="var(--green)" stroke-width="1.5"/>';
    gens.forEach(function(g, i){
      var xy = pts[i].split(',');
      svg += '<circle cx="' + xy[0] + '" cy="' + xy[1] + '" r="2.5" fill="var(--cyan)"><title>gen' + g + ': ' + Math.round(byGen[g]*100) + '%</title></circle>';
      svg += '<text x="' + xy[0] + '" y="' + (H-1) + '" fill="#666" font-size="6" text-anchor="middle">g' + g + '</text>';
    });
    c.innerHTML = svg + '</svg>';
  } catch(e) { console.warn('[DT] 代际曲线加载失败:', e); }
}

// ── D-3.1: 时间轴点附带代际信息 ──
(function(){
  var _origAdd = window._addToTimeline;
  if (typeof _origAdd === 'function') {
    window._addToTimeline = function(e){
      _origAdd(e);
      var tl = document.querySelector('.trial-timeline');
      if (tl && tl.lastChild && tl.lastChild.classList && tl.lastChild.classList.contains('tl-dot')) {
        tl.lastChild.title = 'gen' + ((window._sx && window._sx.generation) || 0) + ' · ' + (e && e.type || '');
        tl.lastChild.setAttribute('data-gen', (window._sx && window._sx.generation) || 0);
      }
    };
  }
})();

window.addEventListener('DOMContentLoaded', loadScenarioList);

