/**
 * AgentsGroup2026 — v4 技能进化面板 (技能统计/失败样本/SSE进化/回滚/A-B对比/代际)
 * 从 v4-scenario-evolution.js 拆出 (D-4.1)。
 * 加载顺序: secs-core.js → director.js → v4-scenarios.js → v4-evolution.js
 */

// C-1: 进化拒绝/失败原因 → 中文可操作提示(不再甩英文 code)
function _evoErrCN(code, detail) {
  if (!code) return '未知原因';
  var c = String(code);
  var MAP = {
    no_weak_skills_identified: '未发现弱技能:本团队最近无带技能使用的试炼数据。请先①选「演练场景」②创建并运行试炼(产生 skill usage)→ 再发起进化。',
    no_candidates_generated: '未生成有效变体候选,可调整反思方向或稍后重试。',
    apply_failed: '写回技能库失败,请检查技能库状态后重试。',
  };
  var base;
  if (MAP[c]) base = MAP[c];
  else if (c.indexOf('budget') === 0 || c.indexOf('budget_exceeded') >= 0) base = '预算已耗尽:请调高小预算或下一周期再试(' + c + ')。';
  else if (c.indexOf('ratchet_blocked') === 0) base = '达尔文棘轮拦截:新版本未超过已锁定基线,不允许回退(' + c + ')。';
  else if (c.indexOf('gate_error') === 0) base = '门禁评估出错(' + c + ')。';
  else base = c;
  // C-1.2: 附加后端结构化原因(扫描试炼数 / usage 条数 / 是无数据还是都达标)
  if (c === 'no_weak_skills_identified' && detail) {
    var why = detail.reason === 'all_meet' ? '有数据但都达标' : '无 usage 数据';
    base += '(扫描 ' + (detail.scanned_trials || 0) + ' 个试炼、usage ' + (detail.usages || 0) + ' 条 · ' + why + ')';
  }
  return base;
}

// ═══ D-2.1: 技能统计 + 失败样本展开 ═══
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
      var clickable = !ok ? ' onclick="showSkillFailures(\'' + s.skill_name.replace(/'/g,"\\'") + '\')" style="cursor:pointer"' : '';
      h += '<div' + clickable + ' title="' + (ok?'':'点击查看失败样本') + '" style="display:flex;align-items:center;gap:6px;margin-bottom:3px">' +
        '<span style="width:90px;font-size:9px;color:' + (ok?'var(--dim)':'var(--red)') + ';text-align:right;overflow:hidden;text-overflow:ellipsis">' + (ok?'':'⚠ ') + s.skill_name + '</span>' +
        '<div style="flex:1;height:12px;background:rgba(255,255,255,.05);border-radius:2px"><div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:2px"></div></div>' +
        '<span style="font-size:9px;color:var(--dim);width:60px">' + pct + '%/' + Math.round(s.expected_success_rate*100) + '% ×' + s.total_uses + '</span></div>';
      if (!ok && s.failure_samples && s.failure_samples.length) {
        h += '<div id="skill-fail-' + s.skill_name.replace(/[^a-z0-9]/gi,'_') + '" style="display:none;margin:2px 0 6px 96px;padding:4px 8px;background:rgba(239,68,68,.06);border-left:2px solid var(--red);border-radius:2px;font-size:8px;color:var(--dim)">';
        s.failure_samples.slice(0,5).forEach(function(f){
          h += '<div>@step' + (f.step_index||'?') + ': ' + (f.failure_reason||'执行未达标') + '</div>';
        });
        if (s.failure_samples.length > 5) h += '<div>… 还有 ' + (s.failure_samples.length-5) + ' 条</div>';
        h += '</div>';
      }
    });
    if (d.weak_skills && d.weak_skills.length) {
      h += '<div style="color:var(--amber);margin-top:4px">⚠ 低于期望: ' + d.weak_skills.join(', ') + ' — 可发起进化</div>';
    }
    area.innerHTML = h;
  } catch(e) { area.innerHTML = '<span style="color:var(--red)">技能统计加载失败: ' + (e.message||'') + '</span>'; }
}
function showSkillFailures(skillName){
  var el = document.getElementById('skill-fail-' + skillName.replace(/[^a-z0-9]/gi,'_'));
  if (el) { el.style.display = el.style.display === 'none' ? '' : 'none'; }
}

// ═══ D-2.2: SSE 进化进度 + 轮询降级 ═══
var _evoPollTimer = null;
var _evoEventSource = null;
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
    var r = await (window._agFetch || fetch)('/api/v1/twin-evolution/runs', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
    var d = await r.json();
    if (!r.ok) throw new Error(d.detail || ('HTTP ' + r.status));
    if (window._sx) window._sx.evolutionRunId = d.run_id;
    document.getElementById('evo-pipeline').style.display = '';
    document.getElementById('evo-result-area').innerHTML = '运行中: ' + d.run_id;
    if (typeof _dtLogConsole === 'function') _dtLogConsole('🧬 进化运行启动: ' + d.run_id, 'info');
    if (_evoPollTimer) { clearInterval(_evoPollTimer); _evoPollTimer = null; }
    if (_evoEventSource) { _evoEventSource.close(); _evoEventSource = null; }
    if (typeof EventSource !== 'undefined') {
      connectEvolutionSSE(d.run_id);
    } else {
      _evoPollTimer = setInterval(pollEvolutionRun, 1500);
    }
  } catch(e) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('进化启动失败: ' + (e.message||'')); }
}

function connectEvolutionSSE(rid){
  if (_evoEventSource) _evoEventSource.close();
  var es = new EventSource('/api/v1/twin-evolution/runs/' + encodeURIComponent(rid) + '/events/stream');
  _evoEventSource = es;
  var lastEvent = Date.now();
  var watchdog = setInterval(function(){
    if (Date.now() - lastEvent > 30000) {
      clearInterval(watchdog);
      if (_evoEventSource) { _evoEventSource.close(); _evoEventSource = null; }
      console.warn('[DT] SSE 超时，降级为轮询');
      _evoPollTimer = setInterval(pollEvolutionRun, 1500);
    }
  }, 5000);
  es.onmessage = function(e){
    lastEvent = Date.now();
    try {
      var ev = JSON.parse(e.data);
      _renderEvoPipeline(ev.status || ev.phase);
      if (ev.status === 'applied' || ev.status === 'rejected' || ev.status === 'failed' || ev.phase === 'terminal') {
        clearInterval(watchdog);
        es.close();
        _evoEventSource = null;
        _finalizeEvolutionResult(ev);
      } else {
        document.getElementById('evo-result-area').innerHTML = '阶段: ' + (ev.status || ev.phase);
      }
    } catch(ex) {}
  };
  es.onerror = function(){
    clearInterval(watchdog);
    if (_evoEventSource) { _evoEventSource.close(); _evoEventSource = null; }
    console.warn('[DT] SSE 连接失败，降级为轮询');
    _evoPollTimer = setInterval(pollEvolutionRun, 1500);
  };
}

function _finalizeEvolutionResult(ev){
  var rid = window._sx && window._sx.evolutionRunId;
  if (!rid) return;
  fetch('/api/v1/twin-evolution/runs/' + encodeURIComponent(rid))
    .then(function(r){ return r.json(); })
    .then(function(run){
      _renderEvoPipeline(run.status);
      var area = document.getElementById('evo-result-area');
      var gate = document.getElementById('evo-gate-actions');
      if (run.status === 'gating' && run.winner) {
        gate.style.display = 'flex';
        area.innerHTML = '<span style="color:var(--green)">胜出: ' + run.winner.strategy +
          ' · fitness ' + (run.winner.fitness||0).toFixed(3) + ' (基线 ' + (run.winner.baseline_fitness||0).toFixed(3) + ', +' +
          Math.round((run.winner.improvement||0)*100) + 'pp)</span><br><span style="color:var(--dim)">技能: ' + run.winner.skill_name + ' — 等待人工裁决</span>';
        _renderAbCompare(run);
      } else if (run.status === 'applied') {
        gate.style.display = 'none';
        area.innerHTML = '<span style="color:var(--green)">✓ 已写回 ' + (run.winner ? run.winner.skill_name + ' v' + (run.winner.new_version||'?') : '') +
          '</span> <button class="btn btn-accent" style="font-size:9px;padding:3px 8px" onclick="nextGeneration()">⏭ 再战一代</button>' +
          ' <button class="btn btn-outline" style="font-size:9px;padding:3px 8px;color:var(--amber);border-color:var(--amber)" onclick="rollbackEvolution()">⏪ 回滚</button>';
        if (typeof _dtLogConsole === 'function') _dtLogConsole('🧬 进化完成并写回技能库', 'success');
      } else if (run.status === 'rejected' || run.status === 'failed') {
        gate.style.display = 'none';
        area.innerHTML = '<span style="color:var(--red)">✗ ' + run.status + ': ' + _evoErrCN(run.error, run.error_detail) + '</span>';
        if (typeof _dtLogConsole === 'function') _dtLogConsole('进化未推进: ' + _evoErrCN(run.error, run.error_detail), 'warn');
      }
    })
    .catch(function(){});
}

async function pollEvolutionRun(){
  var rid = window._sx && window._sx.evolutionRunId;
  if (!rid) { clearInterval(_evoPollTimer); return; }
  if (_evoEventSource) return;
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
      _renderAbCompare(run);
    } else if (run.status === 'applied') {
      clearInterval(_evoPollTimer);
      gate.style.display = 'none';
      area.innerHTML = '<span style="color:var(--green)">✓ 已写回 ' + (run.winner ? run.winner.skill_name + ' v' + (run.winner.new_version||'?') : '') +
        '</span> <button class="btn btn-accent" style="font-size:9px;padding:3px 8px" onclick="nextGeneration()">⏭ 再战一代</button>' +
        ' <button class="btn btn-outline" style="font-size:9px;padding:3px 8px;color:var(--amber);border-color:var(--amber)" onclick="rollbackEvolution()">⏪ 回滚</button>';
      if (typeof _dtLogConsole === 'function') _dtLogConsole('🧬 进化完成并写回技能库', 'success');
    } else if (run.status === 'rejected' || run.status === 'failed') {
      clearInterval(_evoPollTimer);
      gate.style.display = 'none';
      area.innerHTML = '<span style="color:var(--red)">✗ ' + run.status + ': ' + _evoErrCN(run.error, run.error_detail) + '</span>';
      if (typeof _dtLogConsole === 'function') _dtLogConsole('进化未推进: ' + _evoErrCN(run.error, run.error_detail), 'warn');
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
    if (!_evoEventSource) _evoPollTimer = setInterval(pollEvolutionRun, 800);
  } catch(e) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('批准失败: ' + (e.message||'')); }
}

async function rejectEvolution(){
  var rid = window._sx && window._sx.evolutionRunId;
  if (!rid) return;
  try {
    await fetch('/api/v1/twin-evolution/runs/' + encodeURIComponent(rid) + '/reject', { method:'POST' });
    if (!_evoEventSource) _evoPollTimer = setInterval(pollEvolutionRun, 800);
  } catch(e) {}
}

// ── D-2.4: 回滚进化 → 恢复技能到进化前版本 ──
async function rollbackEvolution(){
  var rid = window._sx && window._sx.evolutionRunId;
  if (!rid) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('无进化运行可回滚'); return; }
  try {
    var r = await fetch('/api/v1/twin-evolution/runs/' + encodeURIComponent(rid));
    var run = await r.json();
    if (!run.winner) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('无胜出技能可回滚'); return; }
    var skillId = run.winner.skill_id || run.winner.skill_name;
    var targetVer = Math.max(1, (run.winner.new_version || 2) - 1);
    var teamId = (typeof _selectedTeamId !== 'undefined' && _selectedTeamId) || (window._DTS && window._DTS.directorConfig.team_id) || run.team_id || '';
    if (!window.confirm('回滚技能 "' + run.winner.skill_name + '" 到版本 v' + targetVer + '？ 此操作会创建快照后再回滚。')) return;
    var rr = await (window._agFetch || fetch)('/api/v1/agent-config/skill-library/version/rollback', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ team_id: teamId, skill_id: skillId, target_version: targetVer })
    });
    var rd = await rr.json();
    if (rr.ok && rd.ok) {
      if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('已回滚 ' + skillId + ' → v' + rd.new_version);
      if (typeof _dtLogConsole === 'function') _dtLogConsole('⏪ 技能回滚: ' + skillId + ' → v' + rd.new_version, 'info');
    } else {
      throw new Error(rd.detail || ('HTTP ' + rr.status));
    }
  } catch(e) { if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('回滚失败: ' + (e.message||'')); }
}

// ── D-3: 代际续跑 ──
function nextGeneration(){
  if (window._sx) {
    window._sx.parentTrialId = (window._DTS && window._DTS.activeTrialId) || '';
    window._sx.generation = (window._sx.generation || 0) + 1;
  }
  if (typeof resetForNew === 'function') resetForNew();
  if (typeof _dtLogConsole === 'function') _dtLogConsole('⏭ 进入第 ' + window._sx.generation + ' 代试炼（继承进化后技能），点击"创建试炼"开始', 'info');
  if (typeof _dtWarnOrLog === 'function') _dtWarnOrLog('第 ' + window._sx.generation + ' 代就绪，点击创建试炼');
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

// ═══ D-2.3: A/B 对比卡 + LCS 行级 diff ═══
function _lcsTable(a, b){
  var m = a.length, n = b.length;
  var dp = []; for (var i=0;i<=m;i++){ dp[i]=[]; for(var j=0;j<=n;j++)dp[i][j]=0; }
  for (var i=1;i<=m;i++){
    for (var j=1;j<=n;j++){
      dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1]+1 : Math.max(dp[i-1][j], dp[i][j-1]);
    }
  }
  return dp;
}
function _diffLines(orig, evolved){
  var a = (orig||'').split('\n'), b = (evolved||'').split('\n');
  var dp = _lcsTable(a, b);
  var h = '', i = a.length, j = b.length;
  var hunks = [];
  while (i>0 || j>0){
    if (i>0 && j>0 && a[i-1] === b[j-1]){ hunks.unshift({t:'=',v:a[i-1]}); i--; j--; }
    else if (j>0 && (i===0 || dp[i][j-1] >= dp[i-1][j])){ hunks.unshift({t:'+',v:b[j-1]}); j--; }
    else { hunks.unshift({t:'-',v:a[i-1]}); i--; }
  }
  var hasChange = false;
  hunks.forEach(function(hk){
    if (hk.t === '=') { if (hk.v.trim()) h += '<div style="color:#666">  ' + _escDiff(hk.v) + '</div>'; }
    else { hasChange = true; h += '<div style="color:' + (hk.t==='+'?'var(--green)':'var(--red)') + '">' + hk.t + ' ' + _escDiff(hk.v) + '</div>'; }
  });
  return hasChange ? h : '<div style="color:var(--dim)">（无行级差异）</div>';
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
  if (run.winner && run.winner.baseline_dims) {
    var winDims = null;
    run.candidates.forEach(function(cd){ if (cd.strategy === run.winner.strategy) winDims = cd.dims; });
    if (winDims) { var er = document.getElementById('eval-results'); if (er) er.style.display=''; renderRadarChart(winDims, run.winner.baseline_dims); }
  }
  var orig = (run.target_skills && run.target_skills[0] && run.target_skills[0].instructions_snapshot) || '';
  if (run.winner && run.winner.instructions && orig) {
    h += '<details style="margin-top:4px"><summary style="font-size:9px;color:var(--cyan);cursor:pointer">📝 指令变更 diff</summary>' +
         '<div style="font-family:monospace;font-size:8.5px;max-height:120px;overflow-y:auto;background:rgba(0,0,0,.3);padding:6px;border-radius:4px;margin-top:4px">' +
         _diffLines(orig, run.winner.instructions) + '</div></details>';
  }
  c.innerHTML = h;
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
