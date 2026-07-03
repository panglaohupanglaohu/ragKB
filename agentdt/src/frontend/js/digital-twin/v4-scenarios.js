/**
 * AgentsGroup2026 — v4 场景管理 (卡片选择器 / 房间渲染 / AI生成 / 代际曲线)
 * 从 v4-scenario-evolution.js 拆出 (D-4.1)。
 * 加载顺序: secs-core.js → director.js → v4-scenarios.js → v4-evolution.js
 */

// ── D-1.1: 场景卡片列表加载 ──
async function loadScenarioList(){
  var cards = document.getElementById('dp-scenario-cards');
  if (!cards) return;
  cards.innerHTML = '';
  // 自由模式卡片
  cards.innerHTML = '<div class="mode-card scenario-card sc-free sc-active" data-scenario="" onclick="onScenarioChange(\'\')">' +
    '<span class="mode-icon">🌍</span><span class="mode-name">自由模式</span><span class="mode-desc">无场景约束</span></div>';
  try {
    var r = await fetch('/api/v1/scenarios');
    var d = await r.json();
    window._scenarioIndex = {};
    (d.scenarios || []).forEach(function(s){
      window._scenarioIndex[s.scenario_id] = s;
      var stars = '★'.repeat(s.difficulty || 1);
      var bestHtml = s.best_score != null ? '<span class="sc-best">🏆 ' + Math.round(s.best_score*100) + '%</span>' : '';
      var card = document.createElement('div');
      card.className = 'mode-card scenario-card';
      card.setAttribute('data-scenario', s.scenario_id);
      card.onclick = function(){ onScenarioChange(s.scenario_id); };
      card.innerHTML = '<span class="mode-icon">' + (s.category==='incident'?'🚨':s.category==='data_pipeline'?'📡':s.category==='marketing'?'📢':s.category==='code_delivery'?'💻':'🎧') + '</span>' +
        '<span class="mode-name">' + s.name + '</span><span class="sc-stars">' + stars + '</span>' + bestHtml;
      cards.appendChild(card);
    });
  } catch(e) { console.warn('[DT] 场景列表加载失败:', e); }
}

// ── D-1.1/D-1.2: 场景选择（卡片点击 → 详情+匹配度+棘轮纪录） ──
async function onScenarioChange(sid){
  // 卡片高亮
  document.querySelectorAll('.scenario-card').forEach(function(c){
    c.classList.toggle('sc-active', c.getAttribute('data-scenario') === sid);
  });
  if (window._sx) window._sx.scenarioId = sid;
  var info = document.getElementById('dp-scenario-info');
  if (!sid) { if (info) info.innerHTML = ''; if (window._sx) window._sx.scenarioSpec = null; return; }
  try {
    var r = await fetch('/api/v1/scenarios/' + encodeURIComponent(sid));
    var spec = await r.json();
    if (window._sx) window._sx.scenarioSpec = spec;
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
        // 回填匹配度徽章到卡片
        var card = document.querySelector('.scenario-card[data-scenario="' + sid + '"]');
        if (card) {
          var badge = card.querySelector('.sc-match');
          if (!badge) { badge = document.createElement('span'); badge.className = 'sc-match'; card.appendChild(badge); }
          badge.textContent = pct + '%';
          badge.style.background = pct >= 70 ? '#22c55e' : (pct >= 40 ? '#f59e0b' : '#ef4444');
        }
      } catch(e2) {}
    }
    // GP2-5: 棘轮纪录
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
  try {
    if (window.S) {
      window.S.rooms = rooms.map(function(r){
        return { id: r.room_id, name: r.name, icon: r.icon||'🏠', desc: '业务阶段 '+(r.stage!=null?r.stage:'-')+' · 容量 '+(r.capacity||6), color: 'var(--cyan)', capacity: r.capacity, stage: r.stage };
      });
      // D-1.3: 刷新 2D 房间网格（走 renderEnvironment 统一渲染，含拖放事件）
      if (typeof renderEnvironment === 'function') renderEnvironment();
      // D-1.3: 切换到第一个场景房间的 3D 视图
      if (rooms[0] && typeof window._dt3dBuildRoom === 'function') {
        setTimeout(function(){ window._dt3dBuildRoom(rooms[0].room_id); }, 200);
      }
    }
  } catch(e) {}
  if (typeof _dtLogConsole === 'function') _dtLogConsole('环境空间已切换为场景房间 (' + rooms.length + ' 间)', 'success');
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
    await loadScenarioList();
    onScenarioChange(sd.scenario_id);
  } catch(e) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('场景生成失败: ' + (e.message||'')); }
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

window.addEventListener('DOMContentLoaded', loadScenarioList);
