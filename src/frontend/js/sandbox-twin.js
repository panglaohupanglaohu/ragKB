/**
 * AgentsGroup2026 — SECS Sandbox Twin Dashboard
 * Self-Evolving Collaborative Sandbox with MADTwin environment
 * mapping, TwinLoop simulation, DT-MADDPG critic, and SOP library.
 * Includes runtime self-check and reward chart visualization.
 */
(function () {
  'use strict';

  const API = '/api/v1/sandbox';

  // CSRF helper for state-changing requests
  var _csrfTk='',_csrfPr=null;
  function _csrf(){if(_csrfTk)return Promise.resolve(_csrfTk);if(_csrfPr)return _csrfPr;_csrfPr=fetch('/api/v1/auth/csrf-token').then(function(r){return r.json()}).then(function(d){_csrfTk=d.csrf_token||'';return _csrfTk}).catch(function(){_csrfPr=null;return''});return _csrfPr}
  _csrf();
  async function _af(url,opts){var m=(opts&&opts.method||'GET').toUpperCase();if(m==='POST'||m==='PUT'||m==='DELETE'||m==='PATCH'){await _csrf();if(_csrfTk){opts=opts||{};opts.headers=opts.headers||{};opts.headers['x-csrf-token']=_csrfTk}}return (window._agFetch||fetch)(url,opts)}
  let currentSessionId = null;
  let rewardHistory = [];
  let eventSource = null;
  let runtimeState = null;

  // ── Helpers ──

  function esc(v) { return String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

  // ── API Helpers ──

  async function apiFetch(path, options = {}) {
    const resp = await _af(`${API}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || resp.statusText);
    }
    return resp.json();
  }

  // ── Load Stats ──

  async function loadStats() {
    if (document.hidden) return;
    try {
      const stats = await apiFetch('/stats');
      document.getElementById('stat-sessions').textContent = stats.twin_loop?.total_sessions || 0;
      document.getElementById('stat-steps').textContent = stats.twin_loop?.total_steps || 0;
      document.getElementById('stat-sops').textContent = stats.zero_exp?.total_sops || 0;
      document.getElementById('stat-experiences').textContent = stats.zero_exp?.total_experiences || 0;
      document.getElementById('stat-drifts').textContent = stats.drift_detector?.total_drifts || 0;
      const maxScore = stats.critic?.max_score;
      document.getElementById('stat-score').textContent = maxScore ? maxScore.toFixed(3) : '—';
    } catch (e) {
      console.warn('Stats load failed:', e);
    }

    try {
      const sopData = await apiFetch('/sops');
      renderSOPs(sopData.sops || []);
    } catch (e) {}
  }

  function runtimeBool(v, okText, badText) {
    return v ? okText : badText;
  }

  function renderRuntimeStatus(payload) {
    payload = payload || {};
    runtimeState = payload;
    const panel = document.getElementById('runtime-panel');
    const badge = document.getElementById('runtime-ready-badge');
    const runtime = payload.runtime || payload;
    const limits = runtime.resource_limits || {};
    const lastCheck = runtime.last_self_check || payload.last_self_check || {};
    const checks = lastCheck.checks || payload.checks || {};
    const ready = !!runtime.ready;
    badge.textContent = ready ? 'Ready' : 'Attention';
    badge.style.color = ready ? 'var(--green)' : 'var(--amber)';

    const esc = function (v) { return String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };

    const chips = [
      '<span class="runtime-chip"><span class="status-dot ' + (ready ? 'active' : 'error') + '"></span>' + esc(runtimeBool(ready, '就绪', '未就绪')) + '</span>',
      '<span class="runtime-chip">mode · ' + esc(runtime.mode || 'unknown') + '</span>',
      '<span class="runtime-chip">docker · ' + esc(runtimeBool(runtime.docker_available, 'available', 'n/a')) + '</span>',
      '<span class="runtime-chip">image · ' + esc(runtimeBool(runtime.image_available, 'present', 'missing')) + '</span>',
    ].join('');

    const selfCheckSummary = lastCheck && Object.keys(lastCheck).length
      ? '<div class="runtime-list-item">最近自检: <strong style="color:' + (lastCheck.ok ? 'var(--green)' : 'var(--amber)') + '">' + esc(lastCheck.ok ? '通过' : '失败') + '</strong>' + (lastCheck.runtime?.mode ? ' · mode ' + esc(lastCheck.runtime.mode) : '') + '</div>'
      : '<div class="runtime-list-item">尚未执行 runtime self-check。</div>';

    var checkItems = '';
    for (var key in checks) {
      if (checks.hasOwnProperty(key)) {
        var result = checks[key];
        checkItems += '<div class="runtime-list-item"><strong style="color:' + (result && result.ok ? 'var(--green)' : 'var(--amber)') + '">' + esc(key) + '</strong> · ' + (result && result.ok ? 'OK' : 'FAIL') + (typeof result?.exit_code !== 'undefined' ? ' · exit ' + result.exit_code : '') + (result && result.error ? '<div style="margin-top:4px;color:var(--text)">' + esc(result.error) + '</div>' : '') + '</div>';
      }
    }

    panel.innerHTML = [
      '<div class="runtime-chip-row">' + chips + '</div>',
      '<div class="runtime-grid">',
      '<div class="runtime-card"><div class="runtime-k">Docker 镜像</div><div class="runtime-v">' + esc(runtime.docker_image || '—') + '</div></div>',
      '<div class="runtime-card"><div class="runtime-k">Memory / CPU</div><div class="runtime-v">' + esc(limits.memory_limit_mb || runtime.memory_limit_mb || '—') + ' MB · ' + esc(limits.cpu_limit ?? '—') + ' CPU</div></div>',
      '<div class="runtime-card"><div class="runtime-k">PIDs / nproc</div><div class="runtime-v">' + esc(limits.pids_limit ?? '—') + ' / ' + esc(limits.nproc_limit ?? '—') + '</div></div>',
      '<div class="runtime-card"><div class="runtime-k">tmpfs / nofile</div><div class="runtime-v">' + esc(limits.tmpfs_tmp_mb ?? '—') + 'M · ' + esc(limits.nofile_limit ?? '—') + '</div></div>',
      '</div>',
      '<div class="runtime-list">',
      selfCheckSummary,
      runtime.build_command ? '<div class="runtime-list-item">镜像构建命令: <code>' + esc(runtime.build_command) + '</code></div>' : '',
      checkItems,
      '</div>',
    ].join('');
  }

  async function loadRuntimeStatus() {
    if (document.hidden) return;
    try {
      const runtime = await apiFetch('/runtime-status');
      renderRuntimeStatus(runtime);
    } catch (e) {
      document.getElementById('runtime-panel').innerHTML = '<div style="color: var(--red); font-size: 12px;">加载失败: ' + esc(e.message) + '</div>';
      document.getElementById('runtime-ready-badge').textContent = 'Error';
    }
  }

  async function runRuntimeSelfCheck() {
    setStatus('正在执行 sandbox runtime self-check...');
    try {
      const payload = await apiFetch('/runtime-self-check', { method: 'POST' });
      renderRuntimeStatus(payload);
      setStatus(payload.ok ? '✅ runtime self-check 通过' : '⚠️ runtime self-check 失败');
    } catch (e) {
      setStatus('❌ runtime self-check 失败: ' + e.message);
    }
  }

  // ── Create & Run Simulation ──

  async function createAndRun() {
    const mode = document.getElementById('sim-mode').value;
    const maxSteps = parseInt(document.getElementById('sim-steps').value, 10);
    const speed = parseFloat(document.getElementById('sim-speed').value);
    const branches = parseInt(document.getElementById('sim-branches').value, 10);

    setStatus('正在创建沙箱会话...');
    document.getElementById('btn-run').disabled = true;

    try {
      const session = await apiFetch('/sessions', {
        method: 'POST',
        body: JSON.stringify({
          team_id: 'default',
          mode: mode,
          max_steps: maxSteps,
          speed_factor: speed,
          parallel_branches: branches,
          trigger_description: '手动触发仿真',
        }),
      });

      currentSessionId = session.session_id;
      setStatus('会话创建成功: ' + session.session_id?.slice(0, 8)||'' + '... 正在启动仿真...');
      rewardHistory = [];
      document.getElementById('timeline').innerHTML = '';
      connectStream(currentSessionId);

      const result = await apiFetch('/sessions/' + session.session_id + '/run', { method: 'POST' });

      if (result.alignment) {
        updateEvaluation(result.alignment.evaluation);
        if (result.alignment.best_sop) {
          document.getElementById('btn-inject').disabled = false;
        }
      }

      setStatus('✅ 仿真完成: ' + result.total_steps + ' 步 | 评分: ' + (result.alignment?.evaluation?.global_score?.toFixed(3) || '—'));
    } catch (e) {
      setStatus('❌ 错误: ' + e.message);
    } finally {
      document.getElementById('btn-run').disabled = false;
      loadStats();
    }
  }

  // ── SSE Stream ──

  function connectStream(sessionId) {
    if (eventSource) eventSource.close();

    eventSource = new EventSource(API + '/sessions/' + sessionId + '/stream');

    eventSource.onmessage = function (event) {
      var data = JSON.parse(event.data);

      if (data.type === 'step') {
        addTimelineStep(data);
        rewardHistory.push(data.global_reward);
        drawChart();
        document.getElementById('step-counter').textContent = rewardHistory.length + ' 步';
      } else if (data.type === 'complete') {
        eventSource.close();
        setStatus('仿真完成: ' + data.total_steps + ' 步');
      }
    };

    eventSource.onerror = function () {
      eventSource.close();
    };
  }

  // ── Inject Strategy ──

  async function injectStrategy() {
    if (!currentSessionId) return;
    try {
      var result = await apiFetch('/sessions/' + currentSessionId + '/inject', {
        method: 'POST',
        body: JSON.stringify({ confirm: true }),
      });
      setStatus('💉 策略注入成功: ' + esc(result.sop_name));
      document.getElementById('btn-inject').disabled = true;
    } catch (e) {
      setStatus('❌ 注入失败: ' + e.message);
    }
  }

  // ── UI Renderers ──

  function addTimelineStep(data) {
    var timeline = document.getElementById('timeline');
    if (timeline.children.length === 1 && timeline.children[0].style.textAlign === 'center') {
      timeline.innerHTML = '';
    }

    var rewardClass = data.global_reward > 0.15 ? 'positive' : data.global_reward < 0 ? 'negative' : 'neutral';
    var actions = '';
    var agentActions = data.agent_actions || {};
    var actionParts = [];
    for (var id in agentActions) {
      if (agentActions.hasOwnProperty(id)) {
        actionParts.push(id?.slice(0, 6)||'' + ': ' + agentActions[id]);
      }
    }
    actions = actionParts.join(' | ');

    var el = document.createElement('div');
    el.className = 'timeline-step';
    el.innerHTML = '<span class="step-num">#' + data.step_id + '</span><div class="step-content"><div class="step-actions">' + (actions || '—') + '</div></div><span class="step-reward ' + rewardClass + '">' + data.global_reward.toFixed(3) + '</span>';
    timeline.prepend(el);
  }

  function updateEvaluation(evalData) {
    if (!evalData) return;

    var dims = [
      ['task', evalData.task_completion],
      ['comm', evalData.communication_efficiency],
      ['resource', evalData.resource_utilization],
      ['conflict', evalData.conflict_avoidance],
      ['convergence', evalData.convergence_speed],
      ['global', evalData.global_score],
    ];

    for (var i = 0; i < dims.length; i++) {
      var key = dims[i][0];
      var value = dims[i][1];
      var bar = document.getElementById('bar-' + key);
      var valEl = document.getElementById('val-' + key);
      if (bar && valEl) {
        var pct = (value * 100).toFixed(0);
        bar.style.width = pct + '%';
        bar.className = 'score-bar-fill ' + (value > 0.6 ? 'high' : value > 0.3 ? 'mid' : 'low');
        valEl.textContent = pct + '%';
      }
    }

    var recList = document.getElementById('rec-list');
    var recs = evalData.recommendations || [];
    var recHtml = '';
    for (var j = 0; j < recs.length; j++) {
      recHtml += '<div class="rec-item">' + recs[j] + '</div>';
    }
    recList.innerHTML = recHtml;
  }

  function renderSOPs(sops) {
    var container = document.getElementById('sop-list');
    if (!sops || !sops.length) {
      container.innerHTML = '<div style="color: var(--dim); font-size: 12px;">尚未提取任何 SOP...</div>';
      return;
    }
    var html = '';
    for (var i = 0; i < sops.length; i++) {
      var sop = sops[i];
      html += '<div style="background: var(--panel2); border: 1px solid var(--border); border-radius: 6px; padding: 12px; min-width: 200px;">';
      html += '<div style="font-size: 13px; font-weight: 500; color: var(--cyan);">' + esc(sop.name) + '</div>';
      html += '<div style="font-size: 11px; color: var(--muted); margin-top: 4px;">奖励: ' + sop.avg_reward.toFixed(3) + ' | 成功率: ' + (sop.success_rate * 100).toFixed(0) + '%</div>';
      html += '<div style="font-size: 11px; color: var(--dim); margin-top: 2px;">状态: <span style="color: ' + (sop.status === 'validated' ? 'var(--green)' : 'var(--amber)') + ';">' + esc(sop.status) + '</span></div>';
      html += '</div>';
    }
    container.innerHTML = html;
  }

  function setStatus(msg) {
    var el = document.getElementById('sim-status');
    if (el) el.textContent = msg;
  }

  // ── Reward Chart ──

  function drawChart() {
    var canvas = document.getElementById('reward-chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var rect = canvas.parentElement.getBoundingClientRect();
    // Only resize if container size changed
    if (canvas._lastW !== rect.width || canvas._lastH !== rect.height) {
        canvas.width = rect.width * 2;
        canvas.height = rect.height * 2;
        canvas._lastW = rect.width;
        canvas._lastH = rect.height;
    }
    ctx.scale(2, 2);
    var w = rect.width;
    var h = rect.height;

    ctx.clearRect(0, 0, w, h);
    if (rewardHistory.length < 2) return;

    // Grid
    ctx.strokeStyle = '#2d3a4d';
    ctx.lineWidth = 0.5;
    for (var i = 0; i <= 4; i++) {
      var y = (h / 4) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Data line
    var maxVal = Math.max.apply(null, rewardHistory.concat([0.5]));
    var minVal = Math.min.apply(null, rewardHistory.concat([0]));
    var range = maxVal - minVal || 1;

    ctx.beginPath();
    ctx.strokeStyle = '#22d3ee';
    ctx.lineWidth = 1.5;

    for (var j = 0; j < rewardHistory.length; j++) {
      var x = (j / (rewardHistory.length - 1)) * w;
      var y = h - ((rewardHistory[j] - minVal) / range) * (h - 20) - 10;
      if (j === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Fill
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = 'rgba(34, 211, 238, 0.08)';
    ctx.fill();

    ctx.fillStyle = '#8b9ab5';
    ctx.font = '10px JetBrains Mono';
    ctx.fillText('max: ' + maxVal.toFixed(3), 4, 12);
    ctx.fillText('steps: ' + rewardHistory.length, w - 60, h - 4);
  }

  // ── Expose globals for inline onclick handlers ──

  window.loadStats = loadStats;
  window.loadRuntimeStatus = loadRuntimeStatus;
  window.runRuntimeSelfCheck = runRuntimeSelfCheck;
  window.createAndRun = createAndRun;
  window.injectStrategy = injectStrategy;

  // ── Init ──
  window.addEventListener('load', function () {
    loadStats();
    loadRuntimeStatus();
    setInterval(loadStats, 30000);
    setInterval(loadRuntimeStatus, 30000);
  });
})();
