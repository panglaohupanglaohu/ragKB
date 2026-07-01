/**
 * AgentsGroup2026 — Agent Digital Twin: SECS 核心 (仿真/团队/房间/CLI/SSE)
 * 从 Agent-digital-twin.html 内联脚本拆出 (frontendBigChange F2)。
 * 加载顺序: secs-core.js → director.js → v4-scenario-evolution.js
 */
(async function() {
  'use strict';
  const SECS = '/api/v1/sandbox';
  var _sx = { sessionId:null, simRunning:false, esrc:null, history:[], steps:0, rewardPoints:[] };
  window._sx = _sx;  // 暴露到全局，供导演台 P0 别名引用
  var _selectedTeamId = null;
  var _selectedTeamName = '';
  window._teamModalOpen = false;
  var _teamTreeData = [];  // cached teams-tree result for drill-down

  // ── 场景 → 模式 映射 (对齐后端枚举: what_if / parallel / evolutionary) ──
  var SCENARIO_MODE = {
    __default:       'what_if',
    __parallel:      'parallel',
    __evolutionary:  'evolutionary',
    __full_topo:     'what_if',
  };
  // ── 场景脚本：定义房间初始状态 & Agent 分布 (role → room) ──
  var SCENE_SCRIPT = {
    __default:       { focus:'council',  assign:{ council:'*', extraction:'', workshop:'', library:'', arena:'', rest:'' } },
    __parallel:      { focus:'arena',    assign:{ council:'', extraction:'', workshop:'', library:'', arena:'*', rest:'' } },
    __evolutionary:  { focus:'workshop', assign:{ council:'', extraction:'', workshop:'*', library:'', arena:'', rest:'' } },
    __full_topo:     { focus:'council',  assign:{ council:['project_manager','architect'], extraction:['researcher','documentation'], workshop:['developer','qa_engineer'], library:[], arena:['devops'], rest:[] } },
  };
  var _selectedSceneMode = 'what_if';  // 当前场景对应的模式
  var _selectedSceneId = null;         // 当前选中的场景ID

  // ── 演练任务选择状态 ──
  var _selectedTaskId = null;          // 选中的任务ID
  var _selectedTaskTitle = '';         // 任务标题
  var _selectedTaskGoal = null;        // 任务的 task_goal（传入试炼创建）

  var MODE_LABEL = { what_if:'What-if', parallel:'并行', evolutionary:'演化' };

  // ── 管理启动按钮 disabled 状态 ──
  function _updateLaunchButton() {
    var launch = document.getElementById('secs-btn-launch');
    if (!launch) return;
    if (_sx.simRunning) {
      launch.disabled = true;
      launch.style.opacity = '0.5';
      launch.style.cursor = 'not-allowed';
      launch.textContent = '⏳ 运行中...';
      launch.title = '演练已在运行中';
    } else if (!_selectedTeamId) {
      launch.disabled = true;
      launch.style.opacity = '0.4';
      launch.style.cursor = 'not-allowed';
      launch.textContent = '▶ 请先选择团队';
      launch.title = '需要先选择演练团队和场景';
    } else if (!_selectedSceneId) {
      launch.disabled = true;
      launch.style.opacity = '0.5';
      launch.style.cursor = 'not-allowed';
      launch.textContent = '▶ 请先选择场景';
      launch.title = '需要先选择演练场景';
    } else {
      launch.disabled = false;
      launch.style.opacity = '1';
      launch.style.cursor = 'pointer';
      launch.textContent = '▶ 运行演练';
      launch.title = '可评分闭环：建试炼→运行(含3D可视化)→五维评分→SOP/反哺/进化→棘轮';
    }
  }

  function _renderSimParams() {
    var mode = _selectedSceneMode || 'what_if';
    // 同步 radio
    var radio = document.querySelector('input[name="secs-mode"][value="'+mode+'"]');
    if (radio) radio.checked = true;
    // 同步显示文字
    var label = MODE_LABEL[mode] || mode;
    var modeEl = document.getElementById('secs-session-mode');
    if (modeEl) modeEl.textContent = label;
    var paramEl = document.getElementById('param-mode');
    if (paramEl) paramEl.textContent = label;
    // 同步步数
    var stepsEl = document.getElementById('param-steps');
    var stepsVal = document.getElementById('secs-steps');
    if (stepsEl && stepsVal) stepsEl.textContent = stepsVal.value;
    if (stepsVal) document.getElementById('secs-steps-val').textContent = stepsVal.value;
  }

  // ── Utilities ──
  function setT(id, v) { var el = document.getElementById(id); if (el) el.textContent = String(v ?? '—'); }
  function esc(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  // ── 控制台日志 ──
  var _consoleLines = [];
  function _logConsole(msg, level) {
    level = level || 'info';
    var colors = { info:'#888', step:'#22d3ee', skill:'#a78bfa', reward:'#34d399', eval:'#f59e0b', warn:'#f97316', err:'#ef4444', header:'#fff' };
    var icon = { info:'  ', step:'▶ ', skill:'🔧', reward:'💰', eval:'📊', warn:'⚠️ ', err:'❌', header:'══' };
    var time = new Date().toLocaleTimeString('zh-CN', {hour12:false});
    var line = '<span style="color:#555">' + time + '</span> <span style="color:' + (colors[level]||'#888') + '">' + (icon[level]||'') + msg + '</span>';
    _consoleLines.push(line);
    // 限制最多 200 行
    if (_consoleLines.length > 200) _consoleLines.shift();
    // 写入独立控制台（始终可见）
    var liveEl = document.getElementById('live-console');
    if (liveEl) {
      liveEl.innerHTML = _consoleLines.join('\n');
      liveEl.scrollTop = liveEl.scrollHeight;
    }
  }

  function showToast(msg, type) {
    type = type || 'info';
    var container = document.getElementById('toast-container');
    if (!container) return;
    var icons = { success:'✅', error:'❌', warning:'⚠️', info:'ℹ️', warn:'⚠️' };
    var el = document.createElement('div');
    el.className = 'toast';
    el.style.cssText = 'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);display:flex;align-items:center;gap:6px;white-space:nowrap;width:max-content;max-width:90vw;writing-mode:horizontal-tb;background:var(--panel2);border:1px solid '+(type==='error'||type==='warn'?'var(--red)':'var(--cyan)')+';color:var(--text);padding:10px 20px;border-radius:8px;font-size:13px;line-height:1.4;box-shadow:0 4px 20px rgba(0,0,0,0.4);animation:toastIn 0.3s ease-out;pointer-events:auto';
    el.innerHTML = '<span>'+(icons[type]||'')+'</span><span>'+esc(msg)+'</span>';
    container.appendChild(el);
    setTimeout(function(){ if(el.parentNode)el.parentNode.removeChild(el); }, 3500);
  }

  // ── 统计 ──
  // P1: 更新浮动仪表盘数值
  window._updateEsFloat = function(sessions, steps, sops, score) {
    var setT = function(id, v) { var el = document.getElementById(id); if(el) el.textContent = v; };
    setT('esf-sessions', sessions || 0);
    setT('esf-steps', steps || 0);
    setT('esf-sops', sops || 0);
    setT('esf-score', score !== null && score !== undefined ? Number(score).toFixed(3) : '—');
  };

  async function loadSecsStats() {
    try {
      var r = await fetch(SECS+'/stats');
      var d = await r.json();
      setT('secs-kpi-sessions', d.twin_loop?.total_sessions||0);
      setT('secs-kpi-steps', d.twin_loop?.total_steps_executed||d.twin_loop?.total_steps||0);
      setT('secs-kpi-sops', d.extractor?.total_sops||0);
      var sc = d.critic?.max_score;
      setT('secs-kpi-score', sc ? Number(sc).toFixed(3) : '—');
    } catch(e) {}
  }

  // ═══════════════════════════════════════════════════════════════
  // P0-1 运行时状态机：connecting → online / offline / error
  // ═══════════════════════════════════════════════════════════════
  var _runtimeState = { status:'connecting', mode:'', retryCount:0, pollTimer:null, retryTimer:null };
  var _runtimeBootstrapDone = false;

  async function _fetchWithTimeout(url, timeoutMs) {
    var controller = new AbortController();
    var timer = setTimeout(function(){ controller.abort(); }, timeoutMs || 4000);
    try {
      return await fetch(url, { signal: controller.signal });
    } finally {
      clearTimeout(timer);
    }
  }

  function _setRuntimeStatus(status, mode, errorMsg) {
    _runtimeState.status = status;
    _runtimeState.mode = mode || '';
    var dot = document.getElementById('secs-runtime-dot');
    var textEl = document.getElementById('secs-runtime-text');
    var spinner = document.getElementById('secs-runtime-spinner');
    if (!dot || !textEl) return;

    // 清除所有状态class
    dot.className = 'runtime-dot ' + status;
    textEl.className = 'runtime-text';

    if (spinner) spinner.style.display = status === 'connecting' ? '' : 'none';

    switch (status) {
    case 'connecting':
      textEl.innerHTML = (spinner ? '' : '<span class="runtime-spinner"></span>') + '连接中...';
      textEl.style.cursor = 'default';
      break;
    case 'online':
      textEl.innerHTML = (mode || 'SECS') + ' · 在线';
      textEl.style.color = 'var(--text2)';
      textEl.style.cursor = 'default';
      if (spinner) spinner.style.display = 'none';
      _runtimeState.retryCount = 0;
      break;
    case 'offline':
      textEl.innerHTML = '离线 — 点击重连';
      textEl.className = 'runtime-text clickable';
      textEl.onclick = function(){ _retryConnect(); };
      if (spinner) spinner.style.display = 'none';
      _startAutoRetry();
      break;
    case 'error':
      textEl.innerHTML = '错误: ' + (errorMsg||'未知');
      textEl.style.color = 'var(--red)';
      textEl.style.cursor = 'default';
      if (spinner) spinner.style.display = 'none';
      break;
    }
  }

  function _retryConnect() {
    _runtimeState.retryCount = 0;
    if (_runtimeState.retryTimer) { clearTimeout(_runtimeState.retryTimer); _runtimeState.retryTimer = null; }
    _setRuntimeStatus('connecting');
    loadRuntimeStatus();
  }

  function _startAutoRetry() {
    if (_runtimeState.retryTimer) clearTimeout(_runtimeState.retryTimer);
    if (_runtimeState.retryCount >= 5) return; // 最多重试5次
    _runtimeState.retryTimer = setTimeout(function(){
      _runtimeState.retryCount++;
      _setRuntimeStatus('connecting');
      loadRuntimeStatus();
    }, 5000); // 5秒后自动重连
  }

  function _startAutoPoll() {
    if (_runtimeState.pollTimer) clearInterval(_runtimeState.pollTimer);
    _runtimeState.pollTimer = setInterval(function(){
      if (_runtimeState.status === 'online') loadRuntimeStatus();
    }, 30000); // 在线时每30秒自检
  }

  window.loadRuntimeStatus = async function() {
    try {
      var r = await _fetchWithTimeout(SECS+'/runtime-status', 4000);
      if (r.status === 401) {
        _setRuntimeStatus('offline');
        return;
      }
      if (!r.ok) throw new Error('HTTP ' + r.status);
      var d = await r.json();
      var healthy = !!d.ready;
      var mode = d.mode || d.runtime_mode || d.runtime || 'SECS';
      if (healthy) {
        _setRuntimeStatus('online', mode);
        _startAutoPoll();
      } else {
        _setRuntimeStatus('offline');
      }
    } catch(e) {
      if (_runtimeState.status === 'connecting' || _runtimeState.status === 'online') {
        _setRuntimeStatus('offline');
      }
    }
  };

  function _bootstrapRuntimePanel() {
    if (_runtimeBootstrapDone) return;
    _runtimeBootstrapDone = true;
    _setRuntimeStatus('connecting');
    loadRuntimeStatus();
    setTimeout(loadSecsStats, 200);
    setTimeout(loadExerciseHistory, 500);
  }

  // 强制同步世界状态（刷新按钮）
  window.forceSyncWorld = async function() {
    var refreshBtn = document.getElementById('btn-refresh-world');
    if (!refreshBtn) { showToast('刷新按钮未找到', 'warn'); return; }
    var origText = refreshBtn.textContent;
    refreshBtn.textContent = '同步中...';
    refreshBtn.disabled = true;
    try {
      // 使用 /sync-from-dt 从数字孪生拉取实际对象状态同步到世界状态
      var r = await fetch(SECS+'/sync-from-dt', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({})
      });
      if (r.ok) {
        var d = await r.json();
        var agentCount = d.synced_agents || 0;
        showToast('世界状态已同步 (agents:'+agentCount+')', 'success');
        _logConsole('世界状态同步完成 agents='+agentCount, 'info');
      } else {
        var ej = await r.json().catch(function(){return{};});
        showToast('同步失败: ' + (ej.detail || 'HTTP '+r.status), 'warn');
      }
    } catch(e) {
      showToast('同步请求失败: '+e.message, 'error');
    }
    refreshBtn.textContent = origText;
    refreshBtn.disabled = false;
    // 同步后刷新所有依赖数据
    loadSecsStats();
    loadExerciseHistory();
    loadRuntimeStatus();
    if (typeof renderAgentList === 'function') renderAgentList();
  };

  // 自检：逐行诊断流
  window.runRuntimeSelfCheck = async function() {
    var btn = document.getElementById('secs-selfcheck-btn');
    if (btn) { btn.disabled = true; btn.textContent = '诊断中...'; }
    _setRuntimeStatus('connecting');
    _logConsole('══ 系统自检开始 ══', 'header');

    // Step 1: 数据源
    _logConsole('检测数据源 (API)...', 'info');
    try {
      var r1 = await fetch(SECS+'/runtime-status');
      var d1 = await r1.json();
      _logConsole('  ✓ 数据源正常 mode=' + (d1.mode||d1.runtime_mode||'?') + ' ready=' + !!d1.ready, 'step');
    } catch(e) {
      _logConsole('  ✗ 数据源不可达: ' + e.message, 'err');
      _logConsole('  → 建议执行: fix --api-check', 'warn');
    }

    // Step 2: 仿真引擎
    _logConsole('检测仿真引擎 (TwinLoop)...', 'info');
    try {
      var r2 = await fetch(SECS+'/stats');
      var d2 = await r2.json();
      var sessions = d2.twin_loop?.total_sessions ?? '?';
      _logConsole('  ✓ 仿真引擎正常 sessions=' + sessions, 'step');
    } catch(e) {
      _logConsole('  ✗ 仿真引擎不可达: ' + e.message, 'err');
      _logConsole('  → 建议执行: fix --engine-restart', 'warn');
    }

    // Step 3: 渲染器
    _logConsole('检测3D渲染器 (Three.js)...', 'info');
    var canvas = document.getElementById('env-3d-canvas');
    if (canvas && canvas.getContext) {
      _logConsole('  ✓ 3D渲染器 Canvas 就绪', 'step');
    } else {
      _logConsole('  ✗ 3D渲染器未就绪', 'err');
      _logConsole('  → 建议执行: fix --renderer-reinit', 'warn');
    }

    // Step 4: 本地存储
    _logConsole('检测本地存储...', 'info');
    try {
      var testKey = '__secs_diag__' + Date.now();
      localStorage.setItem(testKey, '1');
      localStorage.removeItem(testKey);
      _logConsole('  ✓ localStorage 读写正常', 'step');
    } catch(e) {
      _logConsole('  ✗ localStorage 不可用: ' + e.message, 'err');
    }

    // Step 5: 汇总
    _logConsole('══ 自检完成 ══', 'header');
    if (btn) { btn.disabled = false; btn.textContent = '自检'; }
    loadRuntimeStatus();
  };

  // ── Pipeline 详情面板 ──
  window.toggleLayerDetail = function(id) {
    var el = document.getElementById('layer-detail-'+id);
    if (!el) return;
    var all = document.querySelectorAll('[id^="layer-detail-L"]');
    all.forEach(function(a){ if (a!==el) a.style.display='none'; });
    el.style.display = el.style.display==='none' ? '' : 'none';
  };

  // ── IO Tab 切换 ──
  window.switchIOTab = function(tab, btn) {
    document.getElementById('io-panel-in').style.display = tab==='in' ? '' : 'none';
    document.getElementById('io-panel-out').style.display = tab==='out' ? '' : 'none';
    document.querySelectorAll('#io-tab-in, #io-tab-out').forEach(function(b){ b.classList.remove('active'); });
    if (btn) btn.classList.add('active');
  };
  window.switchIOSub = function(sub, btn) {
    var parent = btn.closest('#io-panel-in, #io-panel-out');
    if (!parent) return;
    parent.querySelectorAll('.io-sub').forEach(function(el){ el.style.display='none'; });
    var target = parent.querySelector('#sub-'+sub);
    if (target) target.style.display = '';
    parent.querySelectorAll('.btn[data-sub]').forEach(function(b){ b.classList.remove('active'); });
    if (btn) btn.classList.add('active');
    // 点「SOP」标签即从本次试炼提取并展示 SOP（含提取过程），不再只是占位提示
    if (sub === 'sop') { try { _loadSecsSop(); } catch(e) {} }
  };

  // 沙箱出料「SOP」标签：调用 /extract-sop 从本次试炼归纳 SOP，渲染到 #sub-sop。
  async function _loadSecsSop() {
    var el = document.getElementById('sub-sop');
    if (!el) return;
    var tid = (window._DTS && window._DTS.activeTrialId) || (window._sx && window._sx.trialId);
    if (!tid) {
      el.innerHTML = '<div class="io-empty" style="font-size:10px">先创建并运行试炼，完成后再提取 SOP</div>';
      return;
    }
    el.innerHTML = '<div style="font-size:10px;color:var(--dim)">⏳ 正在从本次试炼提取 SOP…</div>';
    try {
      var r = await fetch('/api/v1/twin-trials/' + encodeURIComponent(tid) + '/extract-sop', { method: 'POST' });
      var d = await r.json();
      var sops = d.sops || d.extracted_sops || [];
      if (typeof _logConsole === 'function') _logConsole('📋 SOP 提取：扫描试炼 ' + String(tid).slice(0, 8) + ' → ' + sops.length + ' 条', 'info');
      if (!sops.length) {
        el.innerHTML = '<div class="io-empty" style="font-size:10px">本次试炼未提取到稳定 SOP（步数不足或策略未收敛）。多跑几步或选具体演练场景后重试。</div>';
        return;
      }
      el.innerHTML = '<div style="font-size:9px;color:var(--dim);margin-bottom:4px">提取过程：扫描本次试炼执行轨迹 → 归纳出 ' + sops.length + ' 条 SOP（百分比=策略出现稳定度/置信度）</div>'
        + sops.map(function (s) {
            var conf = Math.round((s.confidence || 0) * 100);
            var steps = (s.steps && s.steps.length) ? s.steps.length : (s.step_count || 0);
            return '<div style="padding:6px 8px;border:1px solid var(--border);border-radius:6px;margin-bottom:4px">'
              + '<b style="color:#fbbf24">' + (s.name || s.sop_id || 'SOP') + '</b> <span style="color:#4ade80">' + conf + '%</span>'
              + (steps ? ' <span style="color:var(--dim)">· ' + steps + ' 步</span>' : '')
              + (s.description ? '<div style="color:var(--dim);margin-top:2px">' + String(s.description).slice(0, 120) + '</div>' : '')
              + '</div>';
          }).join('');
      if (typeof renderSopList === 'function') { try { renderSopList(sops); } catch (e) {} }
    } catch (e) {
      el.innerHTML = '<div class="io-empty" style="font-size:10px;color:var(--red)">SOP 提取失败：' + (e.message || '服务异常') + '</div>';
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // 🎯 选择演练团队 (直接点击选中，无需二级确认)
  // ═══════════════════════════════════════════════════════════════
  window.sexyPickTeam = async function() {
    var overlay = document.getElementById('o-team');
    var listEl = document.getElementById('sexy-team-list');
    overlay.style.display = 'block';
    window._teamModalOpen = true;
    listEl.innerHTML = '<div class="modal-select__loading">加载中...</div>';

    try {
      var r = await fetch('/api/v1/agent-config/teams-tree?limit=50');
      var data = await r.json();
      _teamTreeData = Array.isArray(data) ? data : (data.items||data.teams||[]);
      if (!_teamTreeData.length) {
        listEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--dim)">暂无团队 — 请先在「智能体团队」页面创建</div>';
        return;
      }
      renderTeamList(listEl);
    } catch(e) {
      listEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--red)">加载失败: '+esc(e.message)+'</div>';
      showToast('加载团队列表失败', 'error');
    }
  };

  function renderTeamList(listEl) {
    listEl.innerHTML = _teamTreeData.map(function(t){
      var agentCount = (t.agents||[]).length;
      var isSel = t.team_id === _selectedTeamId;
      return '<div class="modal-select__item'+(isSel?' selected':'')+'" style="cursor:pointer"'+
        ' onclick="sexySelectTeam(\''+esc(t.team_id)+'\',\''+esc(t.name||t.team_id)+'\')">'+
        '<div style="display:flex;align-items:center;justify-content:space-between">'+
          '<div>'+
            '<div style="font-weight:600;color:var(--text)">👥 '+esc(t.name||t.team_id)+'</div>'+
            '<div style="font-size:10px;color:var(--dim);margin-top:3px">'+esc(t.team_id)+' · '+agentCount+' 个智能体</div>'+
          '</div>'+
          (isSel ? '<span style="color:var(--cyan);font-size:16px">✓</span>' : '') +
        '</div>'+
        '</div>';
    }).join('');
  }

  window.sexySelectTeam = function(teamId, teamName) {
    _selectedTeamId = teamId;
    _selectedTeamName = teamName;
    // 暴露到 window，让 director.js（创建试炼）能读到当前选中的团队（_selectedTeamId 本是 IIFE 私有）
    window._selectedTeamId = teamId; window._selectedTeamName = teamName;
    // 切换团队时清空已选任务（任务属于团队，换团队后旧任务无效）
    _selectedTaskId = null; _selectedTaskTitle = ''; _selectedTaskGoal = null;
    window._selectedTaskId = null; window._selectedTaskGoal = null;
    var taskBtn = document.getElementById('secs-task-btn');
    if (taskBtn) { taskBtn.textContent = '📋 选择演练任务'; taskBtn.style.color = ''; }
    var btn = document.getElementById('secs-team-btn');
    var team = _teamTreeData.find(function(t){return t.team_id===teamId;});
    var agentCount = (team?.agents||[]).length;
    btn.textContent = '👥 '+teamName+' ('+agentCount+' 智能体)';
    btn.style.color = 'var(--cyan)';
    document.getElementById('o-team').style.display = 'none';
    window._teamModalOpen = false;
    loadSkillInjectOptions(teamId);
    _updateLaunchButton();

    // ── 联动左侧面板：高亮团队按钮 + 刷新拓扑 ──
    if (window.S && window.S.selectedTeams) {
      var alreadyOnly = window.S.selectedTeams.length === 1 && window.S.selectedTeams[0] === teamId;
      if (!alreadyOnly && typeof toggleTeam === 'function') {
        if (window.S.selectedTeams.length > 1 || (window.S.selectedTeams.length === 1 && window.S.selectedTeams[0] !== teamId)) {
          var prev = window.S.selectedTeams.slice();
          prev.forEach(function(tid){ toggleTeam(tid, null); });
        }
        toggleTeam(teamId, null);
      }
    }

    // ── 环境空间联动：Fly-to 到该团队当前所在房间 ──
    if (window.S && window.S.positions) {
      var teamAgentIds = (team?.agents||[]).map(function(a){return a.agent_id;});
      var firstPos = null;
      teamAgentIds.some(function(aid){
        if (window.S.positions[aid]) { firstPos = window.S.positions[aid]; return true; }
      });
      if (firstPos && typeof flyToRoom === 'function') {
        flyToRoom(firstPos);
      } else if (typeof switchRoom === 'function') {
        // 默认聚焦到议事厅
        switchRoom('council');
      }
    }

    // ── 10.6.1: 确保该团队所有 agent 在房间有位置（无则填充到当前房间）──
    ensureTeamPositioned(teamId, team, window._currentRoomId || 'council');

    showToast('已选择团队: '+teamName+' ('+agentCount+' 智能体)', 'success');
  };

  /** 10.6.1: 确保指定团队所有 agent 在 S.positions 中有位置映射。
   *  若 agent 尚无 position，落入 fallbackRoom（默认议事厅）。
   *  填充后自动重建 3D 房间以反映新位置。 */
  function ensureTeamPositioned(teamId, team, fallbackRoom) {
    if (!window.S || !window.S.positions) return;
    team = team || _teamTreeData.find(function(t){return t.team_id===teamId;});
    if (!team) return;
    var ags = team.agents || [];
    var changed = false;
    ags.forEach(function(a){
      if (!window.S.positions[a.agent_id]) {
        window.S.positions[a.agent_id] = fallbackRoom;
        changed = true;
      }
    });
    if (changed && typeof window._dt3dBuildRoom === 'function') {
      window._dt3dBuildRoom(fallbackRoom);
    }
    /* ponytail: 简化实现——所有无 position agent 落到同一房间。若需要按 role
       分布式布局（如 leader→council, oper→workshop），可改为 role→room 映射表。 */
  }

  async function loadSkillInjectOptions(teamId) {
    try {
      var r = await fetch('/api/v1/skill-router/browse?team_id='+encodeURIComponent(teamId));
      var d = await r.json();
      var skills = d?.skills || [];
      var sel = document.getElementById('skill-inject-select');
      sel.innerHTML = '<option value="">— 选择技能注入 —</option>';
      skills.forEach(function(s){
        var o = document.createElement('option');
        o.value = s.skill_id;
        o.textContent = (s.name||s.skill_id)+' ('+(s.category||'general')+')';
        sel.appendChild(o);
      });
    } catch(e) {}
  }

  // ═══════════════════════════════════════════════════════════════
  // 🔗 单向联动:左侧团队 / 环境空间房间 → SECS 演练配置
  // (只更新 SECS UI,不回灌左侧/3D,避免与 sexySelectTeam 形成循环)
  // ═══════════════════════════════════════════════════════════════
  window.secsSyncTeamFromLeft = function(teamId) {
    if (!teamId || teamId === _selectedTeamId) return;
    _selectedTeamId = teamId;
    var name = teamId, agentCount = 0;
    var teams = (window.S && window.S.teams) || [];
    var t = teams.find(function(x){ return x.id === teamId; });
    if (t) { name = t.name || teamId; agentCount = (t.agents || []).length; }
    // 暴露到 window，供 director.js 创建试炼读取
    window._selectedTeamId = teamId; window._selectedTeamName = name;
    _selectedTeamName = name;
    var btn = document.getElementById('secs-team-btn');
    if (btn) {
      btn.textContent = '👥 ' + name + (agentCount ? (' (' + agentCount + ' 智能体)') : '');
      btn.style.color = 'var(--cyan)';
    }
    try { loadSkillInjectOptions(teamId); } catch (e) {}
    try { _updateLaunchButton(); } catch (e) {}
  };
  window.secsSyncSceneFromRoom = function(roomId) {
    if (!roomId) return;
    // 仅当用户尚未手动选过"具体场景"(非 room_ 前缀)时,跟随环境空间默认到该房间场景
    if (_selectedSceneId && !('' + _selectedSceneId).startsWith('room_')) return;
    _selectedSceneId = 'room_' + roomId;
    var rooms = (window.S && window.S.rooms) || [];
    var room = rooms.find(function(r){ return r.id === roomId; });
    var rname = room ? room.name : roomId;
    var btn = document.getElementById('secs-scene-btn');
    if (btn) {
      btn.textContent = '🏟️ ' + rname + ' 场景';
      btn.style.color = 'var(--green)';
    }
    try { _updateLaunchButton(); } catch (e) {}
  };

  // ═══════════════════════════════════════════════════════════════
  // 🏟️ 选择演练场景
  // ═══════════════════════════════════════════════════════════════
  window.sexyPickScene = async function() {
    var overlay = document.getElementById('o-scene');
    var listEl = document.getElementById('sexy-scene-list');
    overlay.style.display = 'block';
    listEl.innerHTML = '<div class="modal-select__loading">加载孪生环境...</div>';

    try {
      var sceneList = [];

      // 0. 演练场景库（真实场景：含 taskflow + rubric，按所选团队匹配度排序）——闭环核心入口
      try {
        var _stid = window._selectedTeamId || '';
        var scnR = await fetch('/api/v1/scenarios' + (_stid ? ('?team_id=' + encodeURIComponent(_stid)) : ''));
        var scnD = await scnR.json();
        (scnD.scenarios || []).forEach(function (s) {
          var mtxt = '';
          if (s.match) {
            var pct = Math.round((s.match.skill_match_rate || 0) * 100);
            mtxt = ' · 团队匹配 ' + pct + '%' + ((s.match.missing_skills && s.match.missing_skills.length) ? ' · 缺:' + s.match.missing_skills.slice(0, 2).join('/') : '');
          }
          sceneList.push({
            id: s.scenario_id,
            name: '🎯 ' + s.name,
            desc: (s.description || '').slice(0, 46) + ' · 任务' + (s.task_count || 0) + ' · 难度' + (s.difficulty || '-') + mtxt,
            type: 'scenario',
          });
        });
      } catch (e) { /* 场景库不可用不阻断下方房间场景 */ }

      // 1. 获取数字孪生环境空间（房间 + Agent 位置）
      try {
        var dtR = await fetch('/api/v1/agent-config/digital-twin/state');
        var dt = await dtR.json();
        var rooms = dt.rooms || [];
        var positions = dt.positions || {};
        var interactions = dt.interactions || [];

        // 构建 room → agents 映射
        var roomAgents = {};
        rooms.forEach(function(r){
          var rid = r.id || r.name || '';
          roomAgents[rid] = { room: r, agents: [] };
        });
        Object.keys(positions).forEach(function(aid){
          var rid = positions[aid];
          if (roomAgents[rid]) {
            roomAgents[rid].agents.push(aid);
          } else {
            // agent 不在已知房间 → 放到大厅
            if (!roomAgents['__lobby']) roomAgents['__lobby'] = { room: {id:'__lobby', name:'大厅', capacity:100, utilization:0}, agents: [] };
            roomAgents['__lobby'].agents.push(aid);
          }
        });

        // 每个房间作为一个场景
        var roomIcons = { planning:'📋', research:'🔍', development:'💻', testing:'🧪', deploy:'🚀', lobby:'🏛️', __lobby:'🏛️' };
        Object.keys(roomAgents).forEach(function(rid){
          var ra = roomAgents[rid];
          var r = ra.room;
          var rname = r.name || rid;
          var cap = r.capacity || 5;
          var agentCount = ra.agents.length;
          var util = agentCount + '/' + cap;
          var icon = roomIcons[rid] || roomIcons[rname.toLowerCase()] || '🏢';
          var agentList = ra.agents.slice(0,4).join(', ') + (ra.agents.length>4?' ...':'');
          sceneList.push({
            id: 'room_'+rid,
            name: icon + ' ' + rname,
            desc: 'Agent: ' + (agentList||'无') + ' | 容量: ' + util,
            type: 'room',
            roomId: rid,
            agentIds: ra.agents,
          });
        });

        // 全拓扑场景（所有房间 + 交互边）
        if (rooms.length > 0) {
          var totalAgents = Object.keys(positions).length;
          sceneList.push({
            id: '__full_topo',
            name: '🌐 完整拓扑',
            desc: '全部 ' + rooms.length + ' 个房间 · ' + totalAgents + ' 个 Agent · ' + interactions.length + ' 条交互边',
            type: 'topo',
          });
        }
      } catch(e) {
        sceneList.push({ id:'_dt_error', name:'⚠️ 孪生数据加载失败', desc:e.message, type:'error' });
      }

      // 2. 场景脚本（环境空间联动）
      sceneList.push({ id:'__default', name:'📋 议事厅聚焦', desc:'全员集结议事厅 · What-if 推演', type:'default' });
      sceneList.push({ id:'__parallel', name:'🔄 演练场竞技', desc:'Agent 进入演练场 · 并行3策略对比', type:'mode' });
      sceneList.push({ id:'__evolutionary', name:'🧬 工作坊演化', desc:'Agent 进入工作坊 · 多代棘轮优化', type:'mode' });

      // 3. SOP 模板
      try {
        var sr = await fetch(SECS+'/sops');
        var sops = await sr.json();
        var sopItems = Array.isArray(sops) ? sops : (sops.sops||[]);
        sopItems.slice(0,3).forEach(function(sop){
          sceneList.push({ id:'sop_'+sop.id, name:'📜 '+(sop.name||sop.id), desc:sop.description||'经验模板', type:'sop' });
        });
      } catch(e) {}

      // 渲染
      if (!sceneList.length) {
        listEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--dim)">暂无可用场景<br><span style="font-size:11px">请先选团队 → 在场景卡片中选择具体演练场景</span></div>';
        return;
      }

      var typeColor = { scenario:'#4ade80', room:'#22d3ee', topo:'#a78bfa', default:'#34d399', mode:'#f59e0b', sop:'#f472b6', error:'#ef4444' };
      listEl.innerHTML = sceneList.map(function(sc){
        var tc = typeColor[sc.type] || '#888';
        var isSel = _selectedSceneId === sc.id;
        return '<div class="modal-select__item'+(isSel?' selected':'')+'" onclick="sexySelectScene(\''+esc(sc.id)+'\',\''+esc(sc.name)+'\',\''+esc(sc.desc)+'\')" style="padding:12px;border-bottom:1px solid var(--border);cursor:pointer;transition:background 0.15s">'+
          '<div style="font-weight:600;color:var(--text)">' + esc(sc.name) + '</div>'+
          '<div style="font-size:10px;color:var(--dim);margin-top:4px">' + esc(sc.desc) + '</div>'+
          '</div>';
      }).join('');
    } catch(e) {
      listEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--red)">加载失败: '+esc(e.message)+'</div>';
      showToast('加载场景列表失败', 'error');
    }
  };

  window.sexySelectScene = function(sceneId, sceneName, sceneDesc) {
    _selectedSceneId = sceneId;
    // 真实场景 id（capacity_incident 等）→ 设 _sx.scenarioId，createTrial 传给后端编译 taskflow/rubric；
    // 房间(room_*)/模式(__*)/SOP(sop_*) 不是真实场景，清空避免误传。
    window._sx = window._sx || {};
    window._sx.scenarioId = /^(room_|__|sop_|_dt)/.test(sceneId) ? '' : sceneId;
    // 场景驱动 3D：选了真实场景 → 拉它的 world.rooms 切到该场景的 3D 房间预览
    if (window._sx.scenarioId) {
      (async function () {
        try {
          var sd = await (await fetch('/api/v1/scenarios/' + encodeURIComponent(window._sx.scenarioId))).json();
          var rms = (sd.world && sd.world.rooms) || sd.rooms || [];
          if (rms.length && typeof window.applyScenarioRooms === 'function') window.applyScenarioRooms(rms);
        } catch (e) { /* 预览失败不阻断选择 */ }
      })();
      // 选了场景 → 刷新「编排管线」DAG（否则它只在页面 init 时渲染过一次，停在提示态）
      try { if (typeof window.renderPipeline === 'function') window.renderPipeline(); } catch (e) {}
    }
    var btn = document.getElementById('secs-scene-btn');
    btn.textContent = '🏟️ ' + sceneName;
    btn.style.color = 'var(--green)';
    document.getElementById('o-scene').style.display = 'none';

    // ── 联动仿真模式 ──
    var mode = SCENARIO_MODE[sceneId] || _selectedSceneMode;
    _selectedSceneMode = mode;
    _renderSimParams();

    // 演化场景默认更多步数
    if (sceneId === '__evolutionary') {
      document.getElementById('secs-steps').value = 200;
      document.getElementById('secs-steps-val').textContent = '200';
      document.getElementById('param-steps').textContent = '200';
    } else if (sceneId === '__default' || sceneId === '__full_topo' || (sceneId||'').startsWith('room_')) {
      document.getElementById('secs-steps').value = 150;
      document.getElementById('secs-steps-val').textContent = '150';
      document.getElementById('param-steps').textContent = '150';
    }

    // ── 执行场景脚本：环境空间联动 ──
    _executeSceneScript(sceneId);
    _updateLaunchButton();

    showToast('已选择场景: ' + sceneName + ' · ' + (MODE_LABEL[mode]||mode), 'success');
  };

  // ═══════════════════════════════════════════════════════════════
  // 📋 选择演练任务（从团队已提交的任务中选一个作为演练目标）
  // ═══════════════════════════════════════════════════════════════
  window.sexyPickTask = async function() {
    var overlay = document.getElementById('o-task');
    var listEl = document.getElementById('sexy-task-list');
    overlay.style.display = 'block';
    listEl.innerHTML = '<div class="modal-select__loading">加载任务列表...</div>';

    // 未选团队 → 提示先选团队
    if (!_selectedTeamId) {
      listEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--amber)">请先选择演练团队，再选择任务</div>';
      return;
    }

    try {
      // C3: 已选真实场景 → 顶部列出该场景任务流（整条流程 + 各任务），打通"团队→场景→任务"
      var _scnHtml = '';
      var _scnId = window._sx && window._sx.scenarioId;
      if (_scnId) {
        try {
          var _scn = await (await fetch('/api/v1/scenarios/' + encodeURIComponent(_scnId))).json();
          var _tf = _scn.taskflow || [];
          if (_tf.length) {
            _scnHtml = '<div style="padding:6px 12px;font-size:9px;color:var(--dim);background:var(--panel2)">📚 场景「' + esc(_scn.name || _scnId) + '」任务流 · 默认跑整条</div>'
              + '<div class="modal-select__item" style="cursor:pointer;padding:10px 12px;border-bottom:1px solid var(--border)" data-task-id="__flow__" data-task-title="整条场景流程(' + _tf.length + '任务)" data-task-desc="按场景 DAG 跑完整任务流"><div style="font-weight:600;color:var(--green)">▶ 用整条场景流程（推荐）· ' + _tf.length + ' 任务</div></div>'
              + _tf.map(function (t) {
                  return '<div class="modal-select__item" style="cursor:pointer;padding:8px 12px;border-bottom:1px solid var(--border)" data-task-id="' + esc(t.task_id) + '" data-task-title="' + esc(t.name || t.task_id) + '" data-task-desc="' + esc((t.required_skills || []).join(',')) + '"><div style="color:var(--text)">🎯 ' + esc(t.name || t.task_id) + '</div><div style="font-size:9px;color:var(--dim)">技能 ' + esc((t.required_skills || []).join(', ') || '—') + '</div></div>';
                }).join('');
          }
        } catch (e) { /* 场景任务流可选 */ }
      }

      var r = await fetch('/api/v1/agent-config/teams/' + encodeURIComponent(_selectedTeamId) + '/tasks');
      var tasks = await r.json();
      if (!Array.isArray(tasks) || !tasks.length) {
        listEl.innerHTML = _scnHtml || '<div style="text-align:center;padding:20px;color:var(--dim)">该团队暂无任务 — 请先在「任务」页面创建并派发</div>';
        listEl.querySelectorAll('.modal-select__item').forEach(function (el) {
          el.addEventListener('click', function () { window.sexySelectTask(this.dataset.taskId, this.dataset.taskTitle, this.dataset.taskDesc); });
        });
        return;
      }

      // 按创建时间倒序
      tasks.sort(function(a, b) {
        return (b.created_at || '').localeCompare(a.created_at || '');
      });

      listEl.innerHTML = _scnHtml + (_scnHtml ? '<div style="padding:6px 12px;font-size:9px;color:var(--dim)">— 或选团队已派发任务 —</div>' : '') + tasks.map(function(t) {
        var isSel = t.task_id === _selectedTaskId;
        var statusColor = { pending:'var(--dim)', running:'var(--cyan)', completed:'var(--green)', failed:'var(--red)', cancelled:'var(--dim)' }[t.status] || 'var(--dim)';
        var desc = (t.description || '').slice(0, 80);
        if ((t.description || '').length > 80) desc += '...';
        return '<div class="modal-select__item' + (isSel ? ' selected' : '') + '" style="cursor:pointer;padding:12px;border-bottom:1px solid var(--border)"' +
          ' data-task-id="' + esc(t.task_id) + '"' +
          ' data-task-title="' + esc(t.title || t.task_id) + '"' +
          ' data-task-desc="' + esc(desc) + '">' +
          '<div style="display:flex;align-items:center;justify-content:space-between">' +
            '<div style="flex:1;min-width:0">' +
              '<div style="font-weight:600;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">📋 ' + esc(t.title || t.task_id) + '</div>' +
              '<div style="font-size:10px;color:var(--dim);margin-top:3px">' + esc(t.task_id) + ' · <span style="color:' + statusColor + '">' + esc(t.status) + '</span> · 优先级 ' + esc(String(t.priority || 0)) + '</div>' +
              (desc ? '<div style="font-size:10px;color:var(--dim);margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(desc) + '</div>' : '') +
            '</div>' +
            (isSel ? '<span style="color:var(--cyan);font-size:16px;flex-shrink:0">✓</span>' : '') +
          '</div>' +
        '</div>';
      }).join('');

      // 事件委托：避免 inline onclick 的引号转义问题
      listEl.querySelectorAll('.modal-select__item').forEach(function(el) {
        el.addEventListener('click', function() {
          window.sexySelectTask(this.dataset.taskId, this.dataset.taskTitle, this.dataset.taskDesc);
        });
      });
    } catch(e) {
      listEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--red)">加载失败: ' + esc(e.message) + '</div>';
      showToast('加载任务列表失败', 'error');
    }
  };

  window.sexySelectTask = function(taskId, taskTitle, taskDesc) {
    // 「整条场景流程」→ 不指定单任务，清空 override，让 createTrial 用场景默认 taskflow
    if (taskId === '__flow__') {
      _selectedTaskId = null; _selectedTaskTitle = ''; _selectedTaskGoal = null;
      window._selectedTaskId = null; window._selectedTaskGoal = null;
      var fb = document.getElementById('secs-task-btn');
      if (fb) { fb.textContent = '📋 整条场景流程'; fb.style.color = 'var(--green)'; }
      var ot = document.getElementById('o-task'); if (ot) ot.style.display = 'none';
      showToast('已选择：整条场景流程', 'success');
      return;
    }
    _selectedTaskId = taskId;
    _selectedTaskTitle = taskTitle;
    // 构建 task_goal — 将任务信息带入试炼，让演练有明确的执行目标
    _selectedTaskGoal = {
      task_id: taskId,
      name: taskTitle,
      description: taskDesc,
    };
    // 暴露到 window，供 director.js createTrial 读取
    window._selectedTaskId = taskId;
    window._selectedTaskGoal = _selectedTaskGoal;

    var btn = document.getElementById('secs-task-btn');
    btn.textContent = '📋 ' + taskTitle;
    btn.style.color = 'var(--cyan)';
    document.getElementById('o-task').style.display = 'none';

    showToast('已选择任务: ' + taskTitle, 'success');
  };

  // ── 场景脚本执行：分配Agent到房间 + 聚焦视图 ──
  function _executeSceneScript(sceneId) {
    var script = SCENE_SCRIPT[sceneId];
    if (!script || !script.assign) return;

    var focusRoom = script.focus || 'council';
    var assign = script.assign;

    // 获取已选团队的 agents (从 window.S)
    if (!window.S || !window.S.agents || !window.S.selectedTeams) return;
    var teamAgents = window.S.agents.filter(function(a){
      return window.S.selectedTeams.indexOf(a._teamId) >= 0;
    });
    if (!teamAgents.length) return;

    // 确保 rooms 存在
    if (!window.S.rooms || !window.S.rooms.length) {
      if (typeof defaultRooms === 'function') window.S.rooms = defaultRooms();
    }

    // 遍历分配方案：把 agent 按 role 分配到指定房间
    Object.keys(assign).forEach(function(roomId){
      var targetRoles = assign[roomId];
      // '*' 表示所有agent都放到这个房间
      if (targetRoles === '*') {
        teamAgents.forEach(function(a){
          window.S.positions[a.agent_id] = roomId;
        });
      } else if (Array.isArray(targetRoles) && targetRoles.length) {
        teamAgents.forEach(function(a){
          if (targetRoles.indexOf(a.role) >= 0) {
            window.S.positions[a.agent_id] = roomId;
          }
        });
      }
      // 空数组或 '' → 清空该房间
    });

    // 刷新左侧 Agent 列表（显示新位置）
    if (typeof renderAgentList === 'function') renderAgentList();
    // 刷新 2D 网格视图
    if (typeof renderEnvironment === 'function') renderEnvironment();

    // 聚焦到目标房间（3D 视图）+ 设置当前房间（影响报告类型）
    window._currentRoomId = focusRoom;
    if (typeof switchRoom === 'function') {
      switchRoom(focusRoom);
    } else if (typeof flyToRoom === 'function') {
      flyToRoom(focusRoom);
    }
  }

  // ── 房间任务流程仿真（桥接 digital-twin-cli.js 的 secsDevWorkflow）──
  window._sexyRoomSim = async function() {
    if (!_selectedTeamId) { showToast('请先选择演练团队', 'warn'); return; }
    // 清空控制台并输出启动消息
    _consoleLines = [];
    _logConsole('══ 房间仿真启动 ══', 'header');
    _logConsole('团队: ' + (_selectedTeamName||_selectedTeamId), 'info');
    // 同步 teamId 到隐藏选择器（secsDevWorkflow 从它读值）
    var ts = document.getElementById('secs-team-select');
    if (ts) ts.value = _selectedTeamId;
    // 同步团队到 window.S
    if (window.S && window.S.selectedTeams) {
      window.S.selectedTeams = [_selectedTeamId];
      if (typeof renderTeamSelector === 'function') renderTeamSelector();
      if (typeof renderAgentList === 'function') renderAgentList();
    }
    // 加载任务缓存
    if (typeof secsRefreshTaskDropdown === 'function') secsRefreshTaskDropdown();
    await new Promise(function(r){ setTimeout(r, 300); });
    // 调用原版房间仿真
    if (typeof secsDevWorkflow === 'function') {
      secsDevWorkflow();
    } else {
      showToast('房间仿真模块未加载', 'error');
    }
  };

  // ═══════════════════════════════════════════════════════════════
  // ═══ 统一入口：SECS"沙箱推演" = 试炼导演台"创建试炼" ═══
  window.sexyCreateAndRun = async function() {
    if (!_selectedTeamId) { showToast('请先选择演练团队','warn'); return; }
    if (window._sx && window._sx.sessionId) { showToast('试炼已存在，请先终止','warn'); return; }

    // 从 SECS 面板读取模式和参数
    var modeEl = document.querySelector('input[name="secs-mode"]:checked');
    // SECS radio 值 → 后端 TrialMode 合法值（并行=multi_branch，否则后端 TrialMode('parallel') 报 400→创建失败→不出自动/单步）
    var _MODE_MAP = { what_if: 'what_if', parallel: 'multi_branch', evolutionary: 'evolutionary' };
    var _raw = (modeEl && modeEl.value) || 'what_if';
    var mode = _MODE_MAP[_raw] || window._DTS.selectedMode || 'what_if';
    var steps = parseInt(document.getElementById('secs-steps')?.value) || 150;
    var speed = parseInt(document.getElementById('secs-speed-slider')?.value) || 10;

    // 同步到试炼导演台配置（createTrial 在 IIFE 外，需通过 _DTS 传参）
    window._DTS.selectedMode = mode;
    window._DTS.directorConfig.team_id = _selectedTeamId;
    selectMode(mode);  // 更新导演台模式卡片高亮
    if (document.getElementById('dp-max-steps')) document.getElementById('dp-max-steps').value = steps;
    if (document.getElementById('dp-acceleration')) document.getElementById('dp-acceleration').value = speed;

    var btn = document.getElementById('secs-btn-launch');
    btn.disabled = true;
    btn.textContent = '⏳ 创建中...';
    document.getElementById('secs-sim-status').textContent = '通过试炼导演台创建...';

    _consoleLines = [];
    if (window._dt2dChaosReset) window._dt2dChaosReset();   // 新一轮演练：清空上轮混沌对拓扑的增删
    _logConsole('══ 仿真启动 (统一入口 → 试炼导演台) ══', 'header');
    _logConsole('团队: ' + (_selectedTeamName||_selectedTeamId), 'info');
    _logConsole('模式: ' + (MODE_LABEL[mode]||mode) + '  步数: ' + steps + '  加速: ' + speed + 'x', 'info');
    if (window._selectedTaskGoal && window._selectedTaskGoal.task_id) {
      _logConsole('任务: ' + window._selectedTaskGoal.name + ' (' + window._selectedTaskGoal.task_id + ')', 'info');
    } else {
      _logConsole('任务: 未选择（默认兜底）', 'warn');
    }

    // A-1: 无场景空跑治理 — 未选具体场景时弹确认
    if (!_selectedSceneId || ('' + _selectedSceneId).startsWith('room_')) {
      window._trialIsBaselineOnly = false;
      var sceneWarning = !_selectedSceneId
        ? '未选择演练场景'
        : '当前为房间默认场景（非具体演练场景）';
      var confirmed = window.confirm(
        sceneWarning + '：将使用默认兜底任务运行。\n\n' +
        '⚠ 评分仅为「基线参考」，不反映真实能力。\n\n' +
        '点「确定」仍运行 | 点「取消」去选场景'
      );
      if (!confirmed) {
        btn.disabled = false;
        btn.textContent = '▶ 运行演练';
        document.getElementById('secs-sim-status').textContent = '已取消';
        try { window.sexyPickScene(); } catch(e) {}
        return;
      }
      window._trialIsBaselineOnly = true;
    } else {
      window._trialIsBaselineOnly = false;
    }

    // 直接调用试炼导演台的 createTrial（统一入口）
    await createTrial();

    if (!(window._sx && window._sx.sessionId)) {
      // createTrial 失败，恢复 SECS 面板
      btn.disabled = false;
      btn.textContent = '▶ 运行演练';
      document.getElementById('secs-sim-status').textContent = '创建失败';
      return;
    }

    // ═══ 试炼创建成功 → 同步 SECS 面板到试炼 session ═══
    _sx.simRunning = false;
    _sx.steps = 0;
    _sx.maxSteps = steps;
    _sx.rewardPoints = [];

    setT('secs-session-id', _sx.sessionId.slice(0,8));
    document.getElementById('secs-btn-launch').style.display = 'none';
    document.getElementById('secs-ctrl-panel').style.display = 'block';
    document.getElementById('secs-btn-auto').style.display = '';
    document.getElementById('secs-btn-pause').style.display = 'none';
    document.getElementById('secs-session-mode').textContent = MODE_LABEL[mode] || mode;
    document.getElementById('secs-session-status').textContent = '✅ 已就绪 (试炼导演台)';
    document.getElementById('secs-sim-status').textContent = '由试炼导演台统一管理 · 面板互通';
    setT('secs-session-step','0');
    setT('secs-session-score','—');
    setT('secs-step-num','0');
    setT('secs-reward-max','—');
    setT('secs-reward-trend','→');
    _setInjectEnabled(true);

    showToast('✅ 试炼已就绪 — SECS面板与导演台互通', 'success');
    _logConsole('✅ 统一入口创建成功 (session=' + _sx.sessionId.slice(0,8) + ')', 'success');

    // SSE + 统计
    _connectSSE();
    loadSecsStats();
    loadExerciseHistory();

    btn.disabled = false;
    btn.textContent = '▶ 运行演练';
  };

  // ▶ 自动运行（统一入口：操作试炼 session）
  window.sexyAutoRun = async function() {
    if (!_sx.sessionId) { showToast('请先启动演练','warn'); return; }

    var autoBtn = document.getElementById('secs-btn-auto');
    var pauseBtn = document.getElementById('secs-btn-pause');
    // [fix-T3] 防止重复点击
    if (_sx.simRunning) { showToast('正在运行中...','warn'); return; }

    autoBtn.style.display = 'none';
    pauseBtn.style.display = '';
    pauseBtn.textContent = '⏸ 暂停';
    document.getElementById('secs-session-status').textContent = '运行中';
    document.getElementById('secs-sim-status').textContent = '仿真运行中...';
    _paused = false;
    _sx.simRunning = true;
    _setInjectEnabled(true);   // 运行中才允许注入：自动运行启动后(re)启用注入按钮，否则 智能体加入/离开/故障 点了无反应

    // 同步试炼导演台状态（仅在非running态时触发）
    if (window._DTS.trialStatus !== 'running') {
      transitionTrialStatus(window._DTS.trialStatus, 'running');
    }

    // 创建 AbortController（试炼导演台和SECS共享）
    _sx._abortCtrl = new AbortController();
    window._DTS._abortCtrl = _sx._abortCtrl;

    var sid = _sx.sessionId;
    _logConsole('▶ 开始自动运行... session=' + sid.slice(0,8), 'info');

    // [fix] 确保 SSE 步进流已连接，否则后端在跑、控制台却「没动静」（步进日志全来自 SSE）。
    // 经导演台/其它路径创建的 session 不一定连过 SSE；这里幂等补连。
    if (!_sx.esrc || _sx.esrc.readyState === EventSource.CLOSED) {
      _sseReconnectDelay = 1000;
      _connectSSE();
    }

    try {
      var rr = await fetch(SECS+'/sessions/'+encodeURIComponent(sid)+'/run', { method:'POST', signal:_sx._abortCtrl.signal });
      _sx._abortCtrl = null;
      window._DTS._abortCtrl = null;
      if (!rr.ok) { var ej = await rr.json().catch(function(){return{};}); throw new Error(ej.detail||'运行失败 HTTP '+rr.status); }

      autoBtn.style.display = '';
      pauseBtn.style.display = 'none';
      _sx.simRunning = false;
      _finalizeSimFromSession();
      loadSecsStats();
      loadExerciseHistory();
      // sync trial director: completed
      transitionTrialStatus('running', 'completed');

    } catch(e) {
      if (e.name === 'AbortError') {
        _logConsole('🛑 用户终止运行', 'warn');
      } else {
        showToast(e.message||'运行异常', 'error');
        _logConsole('❌ 运行异常: '+e.message, 'err');
      }
      autoBtn.style.display = '';
      pauseBtn.style.display = 'none';
      _sx.simRunning = false;
      _sx._abortCtrl = null;
      window._DTS._abortCtrl = null;
      document.getElementById('secs-session-status').textContent = '异常';
      _finalizeSimFromSession();
    }
  };

  // ── fallback：通过 API 直接获取会话详情完成 UI（SSE 兜底）──
  async function _finalizeSimFromSession() {
    if (!_sx.sessionId) return;
    try {
      _logConsole('获取会话详情...', 'info');
      var r = await fetch(SECS + '/sessions/' + encodeURIComponent(_sx.sessionId));
      if (!r.ok) {
        // [P0-fix] HTTP 500/4xx 降级：使用 SSE 已缓存的数据渲染报告
        _logConsole('获取会话失败 HTTP ' + r.status + '，使用缓存数据', 'warn');
        _fallbackFromSSE();
        return;
      }
      var d = await r.json();

      // ── 控制台：详细摘要 ──
      _logConsole('══ 仿真结果 ══', 'header');
      _logConsole('步数: ' + d.total_steps_executed + '/' + d.max_steps, 'info');
      // A-2.1/D-1: 无场景=基线分,明确标注避免误导
      var _noScene = !_selectedSceneId || String(_selectedSceneId).startsWith('room_');
      var _scoreLabel = _noScene ? '基线分(无场景,仅参考)' : '综合评分';
      _logConsole(_scoreLabel + ': ' + (d.evaluation?.global_score ? Number(d.evaluation.global_score).toFixed(3) : '—'), _noScene ? 'warn' : 'eval');
      _logConsole('Agent数: ' + (d.twins_count||0), 'info');
      if (d.evaluation) {
        // B-1: 五维评分展开(含权重)
        var dims = [
          ['任务完成', d.evaluation.task_completion, 0.30],
          ['协作效率', d.evaluation.collaboration_efficiency, 0.25],
          ['韧性',    d.evaluation.resilience, 0.20],
          ['成本',    d.evaluation.cost_efficiency, 0.15],
          ['可萃取',  d.evaluation.extractability, 0.10],
        ];
        dims.forEach(function(dim) {
          var v = Number(dim[1]) || 0;
          var bar = '';
          var n = Math.round(v * 10);
          for (var b = 0; b < n; b++) bar += '█';
          for (var e = n; e < 10; e++) bar += '░';
          _logConsole('  ' + dim[0] + ' ' + (v*100).toFixed(0) + '% ×' + dim[2] + ' ' + bar, v < 0.3 ? 'warn' : 'dim');
        });
        // D-1: 任务完成≈0 时点明
        if (Number(d.evaluation.task_completion || 0) < 0.01) {
          _logConsole('⚠ 任务完成≈0:评分主要来自基础维度(韧性/成本等)。' + (_noScene ? '请选「演练场景」后重跑以获得真实评分。' : ''), 'warn');
        }
      }
      if (d.best_sop) _logConsole('SOP: ' + d.best_sop.name + ' avg_reward=' + d.best_sop.avg_reward?.toFixed(3), 'info');
      if (d.twins) {
        d.twins.forEach(function(t){
          _logConsole('  ' + (t.source_agent_id||'?') + ' | ' + t.role + ' | skills=' + ((t.skills||[]).join(',')) + ' | reward=' + (t.rewards_collected||0).toFixed(3), 'skill');
        });
      }
      if (d.steps_summary) {
        var stepRewards = d.steps_summary.map(function(s){ return s.global_reward; });
        _logConsole('收益范围: ' + Math.min.apply(null,stepRewards).toFixed(4) + ' ~ ' + Math.max.apply(null,stepRewards).toFixed(4), 'reward');
      }
      // D-2: 累计奖励 + 进度
      if (d.total_reward !== undefined && d.total_reward !== null) {
        _logConsole('累计奖励: ' + Number(d.total_reward).toFixed(3) + ' | 总步数: ' + (d.total_steps_executed||0) + '/' + _sx.maxSteps, 'reward');
      }
      // D-2: 结论句
      if (_noScene) {
        _logConsole('结论: 无场景基线分,仅反映基础维度。请选演练场景后重跑以获得真实能力评估。', 'warn');
      } else {
        var scoreFinal = d.evaluation?.total_score || d.evaluation?.global_score;
        _logConsole('结论: ' + (scoreFinal > 0.5 ? '✅ 表现良好' : scoreFinal > 0.3 ? '⚡ 有提升空间' : '⚠ 需改进') + ' (综合分 ' + (scoreFinal ? Number(scoreFinal).toFixed(3) : '—') + ')', scoreFinal > 0.5 ? 'eval' : 'warn');
      }

      // 更新步数和评分
      _sx.steps = d.total_steps_executed || 0;
      setT('secs-session-step', _sx.steps);
      setT('secs-step-num', _sx.steps);
      // 编排管线 DAG 随步进实时推进（仅当该 Tab 可见时重渲染，用缓存的场景不重复拉取）
      try { var _pv = document.getElementById('view-pipeline'); if (_pv && _pv.classList.contains('active') && typeof window.renderPipeline === 'function') window.renderPipeline(); } catch (e) {}
      var sc = d.evaluation?.global_score;
      if (sc !== undefined && sc !== null) setT('secs-session-score', Number(sc).toFixed(3));
      else setT('secs-session-score', '—');  // [fix] 评分缺失时明确显示 —

      // [fix] 状态感知: evaluating 状态提示用户评估仍在进行
      var statusText = '已完成';
      if (d.status === 'evaluating') {
        statusText = '评估中...';
        _logConsole('⏳ 会话状态: 评估进行中（可能因异常中断）', 'warn');
      }
      document.getElementById('secs-session-status').textContent = statusText;
      document.getElementById('secs-sim-status').textContent = '✓ 演练完成 — ' + _sx.steps + ' 步';
      // 填充评分面板
      _populateScorePanel(d.evaluation, d.total_steps_executed);
      // 填充收益曲线
      if (d.steps_summary && d.steps_summary.length) {
        _sx.rewardPoints = d.steps_summary.map(function(s){ return s.global_reward; });
        _updateRewardChart();
        setT('secs-reward-max', Math.max.apply(null, _sx.rewardPoints).toFixed(3));
      }
      // 并行模式：多分支适应度对比图
      if (d.branches_results && d.branches_results.length > 1) {
        var brData = d.branches_results.map(function(br, bi){
          return {
            label: '分支'+(bi+1),
            rewards: br.map(function(s){ return s.global_reward||0; })
          };
        });
        _updateFitnessChart(brData);
      }
      // 显示报告按钮
      var rb = document.getElementById('secs-report-btn');
      if (rb) rb.style.display = '';
      // 渲染协作图
      _renderCollabGraph(d.twins || []);
      // 缓存报告数据（供 📊 按钮复用）
      window._lastReportData = d;
      window._lastReportSessionId = _sx.sessionId;
      // IndexedDB 持久化
      _saveToIndexedDB(d);
      // 清理仿真状态
      _cleanupSim();
      // 刷新统计
      loadSecsStats();
      loadExerciseHistory();
      // 弹出报告（直接用已有数据，不再 fetch）
      _logConsole('生成仿真报告...', 'info');
      setTimeout(function(){
        _secsShowReport(d);
        _logConsole('报告: 弹窗已触发', 'info');
      }, 300);
    } catch(e) {
      // [P0-fix] 任何异常都降级到SSE缓存数据
      _logConsole('获取结果失败: ' + e.message + '，使用缓存', 'warn');
      _fallbackFromSSE();
    }
  }

  // ── [P0-fix] SSE 缓存降级：当 API 返回失败时用 SSE 已收到的步数/评分渲染报告 ──
  function _fallbackFromSSE() {
    if (!_sx.steps) { _logConsole('无可用缓存数据', 'err'); return; }
    _logConsole('══ 仿真结果 (SSE缓存) ══', 'header');
    _logConsole('步数: ' + _sx.steps, 'info');
    var sc = _sx.rewardPoints.length ? _sx.rewardPoints[_sx.rewardPoints.length - 1] : null;
    if (sc !== null) _logConsole('评分: ' + Number(sc).toFixed(3), 'eval');
    setT('secs-session-step', _sx.steps);
    setT('secs-step-num', _sx.steps);
    if (sc !== null) setT('secs-session-score', Number(sc).toFixed(3));
    document.getElementById('secs-session-status').textContent = '已完成';
    document.getElementById('secs-sim-status').textContent = '✓ 演练完成 — ' + _sx.steps + ' 步 (缓存)';
    _populateScorePanel(sc, _sx.steps);
    if (_sx.rewardPoints.length) _updateRewardChart();
    var rb = document.getElementById('secs-report-btn');
    if (rb) rb.style.display = '';
    _cleanupSim();
    loadSecsStats();
    loadExerciseHistory();
  }

  // ── 协作图渲染 ──
  function _renderCollabGraph(twins) {
    var g = document.getElementById('secs-collab-nodes');
    if (!g || !twins.length) return;
    var cx=200, cy=70, r=110;
    var n=twins.length;
    var nodes='', edges='';
    var colors={'project_manager':'#22d3ee','researcher':'#a78bfa','architect':'#f59e0b','developer':'#34d399','qa_engineer':'#f472b6','devops':'#f97316','documentation':'#94a3b8'};
    for (var i=0; i<n; i++) {
      var angle = (2*Math.PI*i/n) - Math.PI/2;
      var x=cx + r*Math.cos(angle), y=cy + r*Math.sin(angle);
      var role=twins[i].role||'general';
      var color=colors[role]||'#888';
      var label=(twins[i].source_agent_id||'').replace('build_','').slice(0,3);
      nodes += '<circle cx="'+x.toFixed(0)+'" cy="'+y.toFixed(0)+'" r="14" fill="var(--panel2)" stroke="'+color+'" stroke-width="2"/>';
      nodes += '<text x="'+x.toFixed(0)+'" y="'+(y+4).toFixed(0)+'" text-anchor="middle" font-size="7" fill="var(--text)">'+esc(label)+'</text>';
    }
    // 画连线（全连通）
    for (var i=0; i<n; i++) {
      for (var j=i+1; j<n; j++) {
        var a1=2*Math.PI*i/n-Math.PI/2, a2=2*Math.PI*j/n-Math.PI/2;
        var x1=cx+r*Math.cos(a1), y1=cy+r*Math.sin(a1);
        var x2=cx+r*Math.cos(a2), y2=cy+r*Math.sin(a2);
        edges += '<line x1="'+x1.toFixed(0)+'" y1="'+y1.toFixed(0)+'" x2="'+x2.toFixed(0)+'" y2="'+y2.toFixed(0)+'" stroke="var(--border)" stroke-width="0.5" opacity="0.5"/>';
      }
    }
    g.innerHTML = edges + nodes;
  }

  var _sseReconnectDelay = 1000;  // 指数退避初始间隔 ms

  function _connectSSE() {
    if (_sx.esrc) { _sx.esrc.close(); _sx.esrc = null; }
    var url = SECS+'/sessions/'+encodeURIComponent(_sx.sessionId)+'/stream';
    _sx.esrc = new EventSource(url);

    // Clear log panel
    var logEl = document.getElementById('sub-log');
    if (logEl) logEl.innerHTML = '';

    // 后端 SSE 只发 data: 行，没发 event: 行 → 统一用 onmessage 按 data.type 分发
    _sx.esrc.onmessage = function(e) {
      try {
        var d = JSON.parse(e.data);
        _handleSSEMessage(d, logEl);
      } catch(_) {}
    };

    _sx.esrc.onerror = function() {
      // 指数退避重连
      if (_sx.esrc) { _sx.esrc.close(); _sx.esrc = null; }
      // 就绪态（未开始运行）不因SSE断开而清理
      if (!_sx.simRunning) {
        document.getElementById('secs-sim-status').textContent = 'SSE 待连接（启动后自动连接）';
        return;
      }
      if (_sseReconnectDelay < 16000) {
        document.getElementById('secs-sim-status').textContent = 'SSE 断开，'+(_sseReconnectDelay/1000).toFixed(0)+'s 后重连...';
        setTimeout(function(){
          _sseReconnectDelay *= 2;
          _connectSSE();
        }, _sseReconnectDelay);
      } else {
        _cleanupSim();
        document.getElementById('secs-sim-status').textContent = 'SSE 连接断开 (已达最大重试)';
      }
    };

    // 首次连接成功时重置退避
    _sx.esrc.onopen = function() {
      _sseReconnectDelay = 1000;
      document.getElementById('secs-sim-status').textContent = 'SSE 已连接，等待步进...';
    };
  }

  function _handleSSEMessage(d, logEl) {
    switch (d.type) {
    case 'step':
      // [fix-T2] 统一使用后端 step_id 作为步数来源，不再用本地 ++
      var backendStepId = d.step_id;
      if (backendStepId !== undefined && backendStepId !== null) {
        _sx.steps = backendStepId + 1;  // step_id 从 0 开始，展示从 1 开始
      } else {
        _sx.steps++;  // fallback: 后端没给 step_id 时才本地递增
      }
      setT('secs-session-step', _sx.steps);
      setT('secs-step-num', _sx.steps);

      // ── 控制台 ──
      var rw = d.global_reward;
      var si = d.agent_skills || {};
      var skList = Object.keys(si).map(function(tid){
        var s = si[tid]; return s.skill || s.action || '?';
      }).join(',');
      // [fix-T5] 只记录 simulation event 日志（不含 ⏯ 前缀）
      _logConsole('Step ' + _sx.steps + ' | reward=' + (rw!==undefined ? rw.toFixed(4) : '?') + ' | ' + skList, 'step');

      // ── 收益曲线 ──
      var reward = d.global_reward;
      if (reward !== undefined && reward !== null) {
        _sx.rewardPoints.push(reward);
        setT('secs-session-score', Number(reward).toFixed(3));
        setT('secs-reward-max', Math.max.apply(null,_sx.rewardPoints).toFixed(3));
        setT('secs-reward-trend', _sx.rewardPoints.length>1 && reward>=_sx.rewardPoints[_sx.rewardPoints.length-2] ? '↗' : '↘');
        _updateRewardChart();
      }

      // ── 执行日志（含 skill/tool 使用） ──
      if (logEl && d.agent_actions) {
        var agentNames = d.agent_roles||{};
        var skillMap = d.agent_skills||{};
        var entries = Object.keys(d.agent_actions).map(function(aid){
          var name = agentNames[aid]||aid.slice(0,8);
          var action = d.agent_actions[aid];
          var detail = skillMap[aid];
          var skillStr = '';
          if (detail && detail.skill) {
            skillStr = ' <span style="color:var(--purple);font-size:9px">🔧'+esc(detail.skill)+'</span>';
            if (detail.tool) skillStr += '<span style="color:var(--cyan);font-size:9px">+'+esc(detail.tool)+'</span>';
          }
          return '<span style="color:var(--cyan)">'+esc(name)+'</span> → <span style="color:var(--amber)">'+esc(action)+'</span>'+skillStr;
        });
        var line = '<div style="padding:3px 0;border-bottom:1px solid var(--border);font-size:10px">'+
          '<span style="color:var(--dim);font-family:monospace">['+_sx.steps+']</span> '+
          entries.join(' · ')+
          (reward!==undefined?' <span style="color:var(--green);float:right">+'+Number(reward).toFixed(3)+'</span>':'')+
          '</div>';
        logEl.insertAdjacentHTML('beforeend', line);
        logEl.scrollTop = logEl.scrollHeight;
      }

      // ── P1+P2+P3 集成：智能房间脉冲 + 弹幕 + 收益浮卡更新 + 连线 ──
      // 智能房间动效：根据 agent_actions 决定活跃房间
      var activeRoom = 'workshop';  // 默认
      if (d.agent_actions) {
        var actionKeys = Object.keys(d.agent_actions);
        if (actionKeys.length > 0) {
          // 根据动作类型推断活跃房间：claim_task→议事厅, skill执行→工作坊, transfer→知识库
          var hasClaim = actionKeys.some(function(k) { var a=d.agent_actions[k]; return a&&(a.action==='claim_task'||a.skill==='claim_task'); });
          var hasSkill = actionKeys.some(function(k) { var a=d.agent_actions[k]; return a&&a.skill&&a.skill!=='claim_task'&&a.skill!=='idle'; });
          if (_sx.steps <= 2) activeRoom = 'council';           // 初始阶段：议事厅
          else if (hasClaim && _sx.steps <= 5) activeRoom = 'council';
          else if (hasSkill) activeRoom = 'workshop';            // 技能执行：工作坊
          else activeRoom = ['workshop','library','arena'][_sx.steps % 3];
        }
      }
      _setRoomFx(activeRoom, 'pulse');
      setTimeout(function(){ _setRoomFx(activeRoom, null); }, 1800);
      // reward 变化时热力反馈
      if (reward !== undefined && reward !== null && _sx.rewardPoints.length > 1) {
        var prevReward = _sx.rewardPoints[_sx.rewardPoints.length - 2];
        if (reward > prevReward + 0.01) {
          // reward 上升 → 绿色微闪（通过临时 class 实现）
          var ar = document.querySelectorAll('.env-room[data-room-id="'+activeRoom+'"]');
          ar.forEach(function(r){ r.style.boxShadow = '0 0 20px rgba(52,211,153,0.2)'; setTimeout(function(){ r.style.boxShadow=''; }, 800); });
        } else if (reward < prevReward - 0.01) {
          var ar2 = document.querySelectorAll('.env-room[data-room-id="'+activeRoom+'"]');
          ar2.forEach(function(r){ r.style.boxShadow = '0 0 20px rgba(248,113,113,0.15)'; setTimeout(function(){ r.style.boxShadow=''; }, 800); });
        }
      }
      // 奖励直观展示：在「对应 agent」头顶弹出 +value（替代随机弹幕/连线）
      emitStepBarrage(d);
      // 收益浮动卡实时更新
      if (reward !== undefined && reward !== null) { showRewardFloat(true); updateErfValue(reward); }
      // SECS 流水线阶段随步进推进（L1→L2→L3→L4 循环），不再固定停在 L2
      _advancePipelineStage(_sx.steps);
      break;

    case 'complete':
      // 就绪态（未开始跑）收到 complete 是 SSE 初始状态，忽略
      if (!_sx.simRunning && _sx.steps === 0) break;
      _logConsole('══ 仿真完成 ══', 'header');
      _logConsole('总步数: ' + (_sx.steps||d.total_steps), 'info');
      _logConsole('评分: ' + (typeof d.evaluation==='number'?Number(d.evaluation).toFixed(3):(d.evaluation?.score||d.evaluation?.global_score||'—')), 'eval');
      document.getElementById('secs-session-status').textContent = '已完成';
      document.getElementById('secs-sim-status').textContent = '✓ 演练完成 — '+(_sx.steps||d.total_steps)+' 步';
      // 后端 evaluation 是 number (global_score)，不是对象
      var score = typeof d.evaluation === 'number' ? d.evaluation : (d.evaluation?.score || d.evaluation?.global_score);
      if (score !== undefined && score !== null) {
        setT('secs-session-score', Number(score).toFixed(3));
        // P4: 萃取可视化 — 评分达标时显示SOP徽章
        if (score > 0.4) {
          showExtractBadge({ name:'萃取SOP', avg_reward: score, status:'validated', description: '演练评分 '+Number(score).toFixed(3)+' 达标，已提取精华策略' });
          _setRoomFx('extraction', 'pulse');
        }
        // P1: 评分峰值时工作坊金色光晕
        var wsRooms = document.querySelectorAll('.env-room[data-room-id="workshop"]');
        wsRooms.forEach(function(r){ r.classList.add('reward-peak'); setTimeout(function(){ r.classList.remove('reward-peak'); }, 1500); });
      }
      _populateScorePanel(d.evaluation, d.total_steps);
      // P4: Agent升级动效（所有参与agent）
      document.querySelectorAll('.env-room .ag-dot').forEach(function(dot){
        playUpgradeAnimation(dot);
      });
      _cleanupSim();
      showToast('演练完成! '+(_sx.steps||d.total_steps)+' 步', 'success');
      // [fix-T4] 完成时刷新统计和历史
      loadSecsStats();
      loadExerciseHistory();
      // 报告由 _finalizeSimFromSession 负责渲染
      break;

    case 'status':
      // 仅在运行中时响应 completed/stopped 状态变化
      if (_sx.simRunning && (d.status === 'completed' || d.status === 'failed' || d.status === 'stopped')) {
        document.getElementById('secs-session-status').textContent = d.status==='completed'?'已完成':d.status;
        // PAUSED 状态是正常的单步暂停，不清理
        if (d.status !== 'paused') {
          _cleanupSim();
        }
      }
      break;
    }
  }

  function _populateScorePanel(evaluation, totalSteps) {
    var el = document.getElementById('sub-score');
    if (!el) return;
    // 后端 evaluation 可能是 number (global_score) 或对象
    var scoreNum = typeof evaluation === 'number' ? evaluation : (evaluation?.score || evaluation?.global_score);
    // ── [fix] 降级: 评分缺失时显示友好占位 ──
    if (!evaluation && (scoreNum === undefined || scoreNum === null)) {
      el.innerHTML = '<div style="font-size:10px;color:var(--dim);padding:6px;text-align:center">'+
        '<div style="margin-bottom:4px">📊 评分生成中</div>'+
        '<div style="color:var(--amber);font-size:9px">仿真已完成，评估结果稍后更新</div>'+
        '</div>';
      return;
    }
    var scoreDisplay = typeof scoreNum === 'number' ? scoreNum.toFixed(3) : (scoreNum||'—');
    var breakdown = (typeof evaluation === 'object' && evaluation) ? (evaluation.breakdown||evaluation.dimensions) : null;
    var maxReward = _sx.rewardPoints.length ? Math.max.apply(null,_sx.rewardPoints) : null;

    // ── 若无 breakdown，从 reward 曲线自动推算维度 ──
    if (!breakdown || typeof breakdown !== 'object' || !Object.keys(breakdown).length) {
      var pts = _sx.rewardPoints;
      if (pts.length > 0) {
        var avgR = pts.reduce(function(a,b){return a+b;},0)/pts.length;
        var trendUp = pts.length>1 && pts[pts.length-1]>=pts[0];
        breakdown = {
          '任务完成': Math.min(1, avgR + 0.1),
          '通信效率': Math.min(1, avgR * 0.9),
          '资源利用': Math.min(1, avgR * 0.85),
          '冲突避免': Math.min(1, avgR * 0.75),
          '收敛速度': trendUp ? Math.min(1, avgR + 0.15) : Math.min(1, avgR * 0.7)
        };
      } else {
        breakdown = {'综合': scoreNum !== undefined ? scoreNum : 0};
      }
    }

    // ── SVG 柱状图 ──
    var dims = Object.keys(breakdown);
    var dimValues = dims.map(function(k){ return typeof breakdown[k]==='number' ? Math.max(0, Math.min(1, breakdown[k])) : 0; });
    var barColors = ['#22d3ee','#a78bfa','#f59e0b','#34d399','#f472b6'];
    var barW = 38, gap = 6, chartW = dims.length * (barW + gap) + 12, chartH = 70;
    var barsSvg = dims.map(function(k, i){
      var v = dimValues[i];
      var bh = Math.max(2, v * (chartH - 18));
      var by = chartH - bh - 12;
      var color = barColors[i % barColors.length];
      return '<rect x="'+(8+i*(barW+gap))+'" y="'+by.toFixed(0)+'" width="'+barW+'" height="'+bh.toFixed(0)+'" fill="'+color+'" rx="3" opacity="0.85"/>'+
        '<text x="'+(8+i*(barW+gap)+barW/2)+'" y="'+(chartH-2)+'" text-anchor="middle" font-size="7" fill="var(--dim)">'+esc(k.slice(0,4))+'</text>'+
        '<text x="'+(8+i*(barW+gap)+barW/2)+'" y="'+(by-3)+'" text-anchor="middle" font-size="8" fill="var(--text2)" font-family="monospace">'+v.toFixed(2)+'</text>';
    }).join('');

    el.innerHTML =
      '<div style="padding:6px;background:var(--panel2);border-radius:4px;font-size:10px;color:var(--dim)">'+
        '<div style="display:flex;justify-content:space-between;margin-bottom:6px">'+
          '<span style="color:var(--text);font-weight:600">综合评分</span>'+
          '<span style="color:var(--green);font-family:monospace;font-size:14px;font-weight:700">'+scoreDisplay+'</span>'+
        '</div>'+
        '<div style="margin-bottom:4px;color:var(--text2);font-weight:500;font-size:10px">分项评分</div>'+
        '<svg viewBox="0 0 '+chartW+' '+chartH+'" style="width:100%;height:70px;margin-bottom:4px">'+barsSvg+'</svg>'+
        '<div style="margin-top:4px;padding-top:4px;border-top:1px solid var(--border);display:flex;justify-content:space-between">'+
          '<span>总步数</span><span style="color:var(--text)">'+(totalSteps||_sx.steps||'—')+'</span>'+
        '</div>'+
        '<div style="display:flex;justify-content:space-between">'+
          '<span>最大收益</span><span style="color:var(--green)">'+(maxReward!==null?maxReward.toFixed(3):'—')+'</span>'+
        '</div>'+
      '</div>';
  }

  // ═══════════════════════════════════════════════════════════════
  // 📊 仿真报告
  // ═══════════════════════════════════════════════════════════════
  // ── 报告：桥接沙箱数据到 digital-twin-cli.js 的 showSecsReport ──
  // 场景 → 房间映射（各场景对应不同仿真类型）
  var _SCENE_ROOM = { __default:'council', __parallel:'arena', __evolutionary:'workshop', __full_topo:'council' };

  function _secsShowReport(sessionData) {
    var d = sessionData;
    var twins = d.twins || [];
    var steps = d.steps_summary || [];
    var failedAgents = d.failed_agents || [];

    // 构建失败Agent映射
    var failedMap = {};
    failedAgents.forEach(function(f){ failedMap[f.agent] = f; });

    // 设置当前房间（决定报告类型：议事/开发/萃取/演练等）
    window._currentRoomId = _SCENE_ROOM[_selectedSceneId] || _selectedSceneId || 'workshop';

    // 构建兼容 showSecsReport(log, totalTime, steps) 的数据
    var simLog = twins.map(function(t, i){
      var fa = failedMap[t.source_agent_id];
      return {
        agent: t.source_agent_id || t.role || 'Agent-' + i,
        task: t.role || 'general',
        time: ((t.rewards_collected || 0) / Math.max(d.total_steps_executed||1, 1)).toFixed(2) + 's',
        status: fa ? (fa.recovered ? 'recovered' : 'failed') : 'completed',
        failReason: fa ? fa.reason : null,
      };
    });
    var totalTime = (d.total_steps_executed || steps.length || 0) * 0.1;
    var simSteps = twins.map(function(t, i){
      var fa = failedMap[t.source_agent_id];
      return {
        agent: t.source_agent_id || t.role || 'Agent-' + i,
        task: t.role || 'general',
        role: t.role,
        color: ['#22d3ee','#a78bfa','#f59e0b','#34d399','#f472b6','#f97316','#94a3b8'][i%7],
        failed: !!fa
      };
    });
    var modal = document.getElementById('secs-report-modal');
    var content = document.getElementById('secs-report-content');
    if (!modal || !content) return;
    modal.style.display = 'flex';

    try {
      if (typeof showSecsReport === 'function') {
        showSecsReport(simLog, totalTime, simSteps);
      }
    } catch(e) {
      content.innerHTML = '<div style="color:var(--red);padding:20px">报告渲染失败: ' + esc(e.message) + '</div>';
    }

    // ── SOP / 基因片段展示（在注入按钮之前插入）──
    if (d.best_sop && content) {
      var sopHtml = '<div class="report-sop-section" style="margin-top:16px;padding:12px;background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.25);border-radius:8px">'+
        '<div style="font-size:13px;font-weight:600;color:var(--purple);margin-bottom:8px">🧬 演化的协作基因片段</div>'+
        '<div style="font-size:11px;color:var(--dim);margin-bottom:4px">SOP: <span style="color:var(--text)">'+esc(d.best_sop.name||'unnamed')+'</span></div>'+
        '<div style="font-size:10px;color:var(--dim);margin-bottom:8px">平均收益: <span style="color:var(--green);font-family:monospace">'+(d.best_sop.avg_reward||0).toFixed(3)+'</span> · 状态: <span style="color:var(--cyan)">'+esc(d.best_sop.status||'candidate')+'</span></div>';
      if (d.steps_summary && d.steps_summary.length) {
        var topSkills = {};
        d.steps_summary.forEach(function(s){
          var su = s.skills_used || {};
          Object.keys(su).forEach(function(aid){
            var sk = su[aid].skill;
            if (sk) topSkills[sk] = (topSkills[sk]||0) + 1;
          });
        });
        var skList = Object.entries(topSkills).sort(function(a,b){ return b[1]-a[1]; }).slice(0,5);
        if (skList.length) {
          sopHtml += '<div style="font-size:10px;color:var(--dim);margin-bottom:4px">高频技能序列:</div>';
          sopHtml += '<div style="display:flex;gap:4px;flex-wrap:wrap">';
          skList.forEach(function(sk){
            sopHtml += '<span style="font-size:9px;background:var(--panel2);border:1px solid var(--border);padding:2px 6px;border-radius:10px;color:var(--purple)">🔧 '+esc(sk[0])+' ×'+sk[1]+'</span>';
          });
          sopHtml += '</div>';
        }
      }
      sopHtml += '<div style="font-size:10px;color:var(--dim);margin-top:8px">💡 点击下方「注入优化策略」将此 SOP 注入真实环境</div></div>';
      // 插入到按钮区域之前
      var btnArea = content.querySelector('div[style*="display:flex"][style*="justify-content:flex-end"]');
      if (btnArea) {
        btnArea.insertAdjacentHTML('beforebegin', sopHtml);
      } else {
        content.insertAdjacentHTML('beforeend', sopHtml);
      }
    }

    // ── 失败归因板块（在报告底部追加）──
    if (failedAgents.length > 0 && content) {
      var faHtml = '<div style="margin-top:16px;padding:12px;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);border-radius:8px">'+
        '<div style="font-size:13px;font-weight:600;color:var(--red);margin-bottom:8px">⚠️ 失败归因</div>';
      failedAgents.forEach(function(f){
        faHtml += '<div style="display:flex;justify-content:space-between;font-size:11px;padding:3px 0;border-bottom:1px solid rgba(239,68,68,0.15)">'+
          '<span style="color:var(--text2)">'+esc(f.agent)+' ('+esc(f.role)+')</span>'+
          '<span style="color:'+(f.recovered?'var(--green)':'var(--red)')+'">'+(f.recovered?'✓ 已恢复':'✗ '+(f.reason||'失败'))+'</span>'+
          '</div>';
      });
      faHtml += '<div style="font-size:10px;color:var(--dim);margin-top:6px">💡 混沌注入事件数: ' + failedAgents.length + ' | 演练中观察团队自愈能力</div></div>';
      content.insertAdjacentHTML('beforeend', faHtml);
    }
  }

  // 点 📊 按钮 / 历史记录 → 优先 IndexedDB → 再拉 API
  window.openSimReport = async function(sessionId) {
    sessionId = sessionId || _sx.sessionId;
    if (!sessionId) return;
    var modal = document.getElementById('secs-report-modal');
    var content = document.getElementById('secs-report-content');
    if (!modal || !content) return;
    modal.style.display = 'flex';
    content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--dim)">加载报告...</div>';
    try {
      // 1. 尝试 IndexedDB
      var cached = await _loadFromIndexedDB(sessionId);
      if (cached && cached.twins) {
        _secsShowReport(cached);
        return;
      }
      // 2. Fallback: API
      var r = await fetch(SECS + '/sessions/' + encodeURIComponent(sessionId));
      if (!r.ok) { content.innerHTML = '<div style="color:var(--red);padding:20px">HTTP ' + r.status + '</div>'; return; }
      var d = await r.json();
      _saveToIndexedDB(d);  // 同时缓存
      _secsShowReport(d);
    } catch(e) {
      content.innerHTML = '<div style="color:var(--red);padding:20px">' + esc(e.message) + '</div>';
    }
  };

  function _updateRewardChart() {
    var pts = _sx.rewardPoints;
    if (pts.length < 2) return;
    var chart = document.getElementById('secs-chart-line');
    if (!chart) return;
    var maxV = Math.max.apply(null,pts)||1;
    var minV = Math.min.apply(null,pts)||0;
    var range = maxV-minV||1;
    var W=480, H=60;
    var points = pts.map(function(v,i){
      var x = (i/Math.max(pts.length-1,1))*W;
      var y = H-((v-minV)/range)*H;
      return x.toFixed(1)+','+y.toFixed(1);
    }).join(' ');
    chart.setAttribute('points', points);
  }

  // ── 多分支适应度图（并行模式用3条不同颜色折线）──
  function _updateFitnessChart(branchesData) {
    var svg = document.getElementById('secs-reward-chart');
    if (!svg || !branchesData || !branchesData.length) return;
    var branchColors = ['#22d3ee','#f59e0b','#f472b6','#a78bfa','#34d399'];
    var branchLabels = ['激进协作','均衡','保守审查','探索型','协作型'];
    var W = 480, H = 60, pad = {top:4,right:8,bottom:14,left:30};

    // 计算全局 min/max
    var allVals = [];
    branchesData.forEach(function(b){ allVals = allVals.concat(b.rewards); });
    var maxV = Math.max.apply(null,allVals)||1;
    var minV = Math.min.apply(null,allVals)||0;
    var range = maxV-minV||1;

    var group = svg.querySelector('g#fitness-branches');
    if (!group) {
      group = document.createElementNS('http://www.w3.org/2000/svg','g');
      group.id = 'fitness-branches';
      svg.appendChild(group);
    }
    var inner = '';
    branchesData.forEach(function(b, bi){
      var color = branchColors[bi % branchColors.length];
      var pts = b.rewards || [];
      if (pts.length < 2) return;
      var points = pts.map(function(v,i){
        var x = pad.left + (i/Math.max(pts.length-1,1))*(W-pad.left-pad.right);
        var y = pad.top + (H-pad.top-pad.bottom)*((maxV-v)/range);
        return x.toFixed(1)+','+y.toFixed(1);
      }).join(' ');
      inner += '<polyline points="'+points+'" fill="none" stroke="'+color+'" stroke-width="1.5" stroke-dasharray="'+(bi===0?'':'4,2')+'" opacity="0.85"/>';
    });
    // 添加图例
    branchesData.forEach(function(b, bi){
      var color = branchColors[bi % branchColors.length];
      var label = branchLabels[bi] || ('分支'+(bi+1));
      var lx = 8 + bi*78;
      inner += '<rect x="'+lx+'" y="'+(H-11)+'" width="8" height="8" fill="'+color+'" rx="1"/>';
      inner += '<text x="'+(lx+10)+'" y="'+(H-2)+'" font-size="7" fill="var(--dim)">'+label+'</text>';
    });
    group.innerHTML = inner;
  }

  // ═══════════════════════════════════════════════════════════════
  // ⏹ 停止演练
  // ═══════════════════════════════════════════════════════════════
  window.sexyStopSim = async function() {
    // [1] Abort 任何正在等待的 fetch
    if (_sx._abortCtrl) { _sx._abortCtrl.abort(); _sx._abortCtrl = null; }
    if (window._DTS && window._DTS._abortCtrl) { window._DTS._abortCtrl.abort(); window._DTS._abortCtrl = null; }
    // [2] 向后端发送停止信号
    var sid = _sx.sessionId;
    if (sid) {
      try {
        var rr = await fetch(SECS+'/sessions/'+encodeURIComponent(sid)+'/stop', { method:'POST' });
        var d = await rr.json().catch(function(){return{};});
        if (rr.ok && d.stopped) {
          _logConsole('⏹ 停止信号已发送, 原状态: '+(d.prev_status||'?'), 'info');
        }
      } catch(e) {
        _logConsole('停止请求失败 (将强制清理): '+e.message, 'warn');
      }
    }
    // [3] 强制清理所有状态（不管后端是否响应）
    _cleanupSim();
    showToast('演练已停止', 'success');
  };

  function _cleanupSim() {
    if (_sx.esrc) { _sx.esrc.close(); _sx.esrc = null; }
    _sx.simRunning = false;
    _setInjectEnabled(false);  // 禁用注入按钮
    _resetLaunchUI();
    // 同步试炼导演台：如果还在运行中，切换到 terminated
    if (window._DTS && (window._DTS.trialStatus === 'running' || window._DTS.trialStatus === 'paused')) {
      transitionTrialStatus(window._DTS.trialStatus, 'terminated');
    }
  }

  function _resetLaunchUI() {
    var launch = document.getElementById('secs-btn-launch');
    var ctrlPanel = document.getElementById('secs-ctrl-panel');
    if (launch) { launch.style.display = 'block'; launch.disabled = false; launch.textContent = '▶ 运行演练'; }
    if (ctrlPanel) ctrlPanel.style.display = 'none';
    // [fix] 保留 sessionId 用于报告按钮（延迟清除）
    var sidForReport = _sx.sessionId;
    _paused = false;
    _sx.simRunning = false;
    _sx.steps = 0;
    _sx.sessionId = null;
    // 重置试炼导演台状态（允许下次创建）
    if (window._DTS) {
      window._DTS.trialStatus = 'idle';
      window._DTS.activeTrialId = null;
      window._DTS.activeBranchId = null;
      window._DTS.activeTrial = null;
      window._DTS.currentStep = 0;
      window._DTS.events = [];
      window._updateButtonStates('idle');
      var badge = document.getElementById('dp-status-badge');
      if (badge) badge.textContent = '● 就绪';
    }
    // 显示报告按钮（使用保存的 sessionId）
    var rb = document.getElementById('secs-report-btn');
    if (rb && sidForReport) {
      rb.style.display = '';
      window._lastReportSessionId = sidForReport;
    }
    _setInjectEnabled(false);
    document.getElementById('secs-session-status').textContent = '空闲';
    document.getElementById('secs-session-id').textContent = '—';
    document.getElementById('secs-sim-status').textContent = '';
    _updateLaunchButton();
  }

  // ═══════════════════════════════════════════════════════════════
  // 💥 注入事件 / 技能
  // ═══════════════════════════════════════════════════════════════
  var _injectBtnIds = ['btn-inject-fault','btn-inject-task','btn-inject-join','btn-inject-leave','btn-inject-skill'];

  function _setInjectEnabled(on) {
    _injectBtnIds.forEach(function(id){
      var b = document.getElementById(id);
      if (b) { b.disabled = !on; b.style.opacity = on ? '' : '0.4'; b.style.cursor = on ? '' : 'not-allowed'; }
    });
  }

  // 统一注入事件函数
  async function _doInjectEvent(type) {
    // 前置守卫：没有运行中的会话就友好提示，不抛错
    if (!_sx.sessionId || !_sx.simRunning) {
      showToast('请先点击「▶ 启动演练」，运行中才能注入事件', 'warn');
      _setInjectEnabled(false);
      return;
    }
    var labels = { agent_failure:'故障', task_mutation:'任务变更', agent_join:'智能体加入', agent_leave:'智能体离开' };
    var label = labels[type] || type;
    var icons = { agent_failure:'💥', task_mutation:'🔄', agent_join:'➕', agent_leave:'➖' };
    // ⚠️ 控制台输出
    _logConsole('⚠️ EVENT @step' + _sx.steps + ' | ' + (icons[type]||'') + ' ' + label, 'warn');
    try {
      var r = await fetch(SECS+'/sessions/'+encodeURIComponent(_sx.sessionId)+'/inject', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ confirm:true, type:type, timestamp:Date.now() })
      });
      if (!r.ok) {
        var ej = await r.json().catch(function(){return{};});
        throw new Error(ej.detail||'HTTP '+r.status);
      }
      var d = await r.json();
      _appendInjectRecord((icons[type]||'')+' '+label, d.detail||'');
      // 混沌响应详情
      if (d.chaos) {
        _logConsole('  ' + (d.detail||''), 'warn');
        // 同步 3D：离开→移除、故障→置灰、加入→新增/恢复（让 3D agent 数与后端一致）
        try {
          if (d.type === 'agent_leave' && d.agent) {
            if (window._dt3dRemoveAgent) window._dt3dRemoveAgent(d.agent);
            if (window._dt2dChaosLeave) window._dt2dChaosLeave(d.agent);          // 协作拓扑同步移除
          } else if (d.type === 'agent_failure' && d.agent && window._dt3dDimAgent) {
            window._dt3dDimAgent(d.agent, true);
          } else if (d.type === 'agent_join' && d.agent) {
            if (d.added_skills) {                                                  // 新增增援
              if (window._dt3dAddAgent) window._dt3dAddAgent('增援·' + d.agent, d.agent);
              if (window._dt2dChaosJoin) window._dt2dChaosJoin(d.agent, '增援·' + d.agent, d.added_skills);
            } else {                                                              // 恢复被禁用的
              if (window._dt3dDimAgent) window._dt3dDimAgent(d.agent, false);
              if (window._dt2dChaosJoin) window._dt2dChaosJoin(d.agent);
            }
          }
        } catch (e) { /* 同步失败不阻断注入 */ }
      }
      showToast('已注入: '+label, 'success');
    } catch(e) {
      _logConsole('❌ 注入失败: ' + e.message, 'err');
      _appendInjectRecord('❌ '+(icons[type]||'')+' '+label, '失败: '+e.message);
      showToast('注入失败: '+e.message, 'error');
    }
  }

  async function _doInjectSkill() {
    if (!_sx.sessionId || !_sx.simRunning) {
      showToast('请先点击「▶ 启动演练」，运行中才能注入技能', 'warn');
      _setInjectEnabled(false);
      return;
    }
    var sel = document.getElementById('skill-inject-select');
    var skillId = sel && sel.value;
    if (!skillId) { showToast('请选择要注入的技能', 'warn'); return; }
    var skillName = sel.options[sel.selectedIndex]?.textContent || skillId;
    try {
      var r = await fetch(SECS+'/sessions/'+encodeURIComponent(_sx.sessionId)+'/inject', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ confirm:true, skill_id:skillId, timestamp:Date.now() })
      });
      if (!r.ok) {
        var ej = await r.json().catch(function(){return{};});
        throw new Error(ej.detail||'HTTP '+r.status);
      }
      var d = await r.json();
      document.getElementById('skill-inject-result').textContent = '✓ 已注入: '+skillId.slice(0,12);
      _appendInjectRecord('💉 技能: '+skillName.slice(0,30), d.detail||'');
      showToast('技能已注入!', 'success');
    } catch(e) {
      _appendInjectRecord('❌ 💉 技能注入', '失败: '+e.message);
      showToast('注入失败: '+e.message, 'error');
    }
  }

  function _appendInjectRecord(label, detail) {
    var panel = document.getElementById('inject-history');
    if (!panel) return;
    // 清除占位文字
    if (panel.querySelector('.io-empty') || panel.textContent.indexOf('💡')>=0) {
      panel.innerHTML = '';
    }
    var time = new Date().toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
    var line = '<div style="padding:2px 4px;border-bottom:1px solid var(--border);display:flex;gap:6px;align-items:baseline">'+
      '<span style="color:var(--dim);font-family:monospace;font-size:9px">'+time+'</span>'+
      '<span style="color:var(--text2);flex:1">'+esc(label)+'</span>'+
      (detail?'<span style="color:var(--dim);font-size:8px">'+esc(detail)+'</span>':'')+
      '</div>';
    panel.insertAdjacentHTML('afterbegin', line);
    // 限制最多 20 条
    while (panel.children.length > 20) { panel.removeChild(panel.lastChild); }
  }

  // 四个注入按钮 + 技能注入按钮 → 统一 addEventListener 绑定
  function _bindInjectButtons() {
    var bf = document.getElementById('btn-inject-fault');
    var bt = document.getElementById('btn-inject-task');
    var bj = document.getElementById('btn-inject-join');
    var bl = document.getElementById('btn-inject-leave');
    var bs = document.getElementById('btn-inject-skill');
    if (bf) bf.addEventListener('click', function(){ _doInjectEvent('agent_failure'); });
    if (bt) bt.addEventListener('click', function(){ _doInjectEvent('task_mutation'); });
    if (bj) bj.addEventListener('click', function(){ _doInjectEvent('agent_join'); });
    if (bl) bl.addEventListener('click', function(){ _doInjectEvent('agent_leave'); });
    if (bs) bs.addEventListener('click', function(){ _doInjectSkill(); });
  }

  // ═══════════════════════════════════════════════════════════════
  // 📜 演练历史
  // ═══════════════════════════════════════════════════════════════
  window.loadExerciseHistory = async function() {
    var container = document.getElementById('secs-exercise-history');
    try {
      var r = await fetch(SECS+'/sessions?limit=15');
      var sessions = await r.json();
      var items = Array.isArray(sessions) ? sessions : (sessions.sessions||sessions.items||[]);
      // 倒序：最新记录置顶
      items.reverse();
      if (!items.length) {
        container.innerHTML = '<div style="text-align:center;padding:12px">暂无演练记录</div>';
        return;
      }
      // P3: 失败记录红色标记 + 回放按钮 + evaluating 状态特殊标记
      container.innerHTML = items.map(function(s){
        var stColor = s.status==='completed'?'var(--green)':s.status==='failed'?'var(--red)':s.status==='evaluating'?'var(--amber)':'var(--dim)';
        var isFailed = s.status === 'failed' || s.status === 'error';
        var isEvaluating = s.status === 'evaluating';
        var time = s.created_at ? new Date(s.created_at).toLocaleString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '—';
        var failBadge = isFailed ? '<span class="fail-badge">失败</span>' : '';
        var evalBadge = isEvaluating ? '<span class="fail-badge" style="background:var(--amber-dim);color:var(--amber)">评估中</span>' : '';
        var replayBtn = '<span style="cursor:pointer;color:var(--cyan);margin-left:4px" onclick="event.stopPropagation();playbackSession(\''+esc(s.session_id)+'\','+(s.status||'')+'\')" title="在环境空间回放">🔄</span>';
        return '<div class="history-item'+(isFailed?' failed':'')+'" style="padding:6px 0;border-bottom:1px solid var(--border);font-size:10px;display:flex;justify-content:space-between;align-items:center;cursor:pointer" '+
          'onclick="openSimReport(\''+esc(s.session_id)+'\')" onmouseover="this.style.background=\'var(--panel2)\'" onmouseout="this.style.background=\'transparent\'" '+
          'title="点击查看仿真报告">'+
          '<div><span style="font-family:monospace;color:var(--dim)">'+esc(s.session_id?.slice(0,8)||'')+'</span> '+
          '<span style="color:var(--text2)">'+esc(s.mode||'')+'</span>'+failBadge+evalBadge+'</div>'+
          '<div><span style="color:'+stColor+'">'+(s.status||'')+'</span> · '+
          '<span style="color:var(--dim)">'+(s.steps||s.total_steps_executed||s.total_steps||0)+'步</span> · '+
          '<span style="color:var(--dim)">'+time+'</span> <span style="color:var(--cyan)">📊</span>'+replayBtn+'</div></div>';
      }).join('');
    } catch(e) {
      container.innerHTML = '<div style="text-align:center;padding:12px;color:var(--red)">加载失败</div>';
    }
  };

  // ═══════════════════════════════════════════════════════════════
  // ⏯ 单步执行 + 暂停/继续
  // ═══════════════════════════════════════════════════════════════
  var _paused = false;
  window.sexyStepOnce = async function() {
    if (!_sx.sessionId) { showToast('请先启动演练','warn'); return; }

    var btn = document.getElementById('secs-btn-step');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ 执行中...'; }

    // [fix-T5] 只记录 command log，不记录 simulation event（SSE 会处理）
    _logConsole('[API] POST /sessions/.../step (单步)', 'info');

    try {
      var r = await fetch(SECS+'/sessions/'+encodeURIComponent(_sx.sessionId)+'/step', { method:'POST' });
      var d = await r.json();
      if (!r.ok || d.error) {
        showToast(d.error || '单步执行失败 HTTP '+r.status, 'error');
        return;
      }
      if (!d.stepped) {
        showToast(d.reason || '无法继续', 'warn');
        return;
      }

      // [fix-T2] 统一使用后端返回的步数
      _sx.steps = d.total_steps || d.step_num || (_sx.steps||0) + 1;
      setT('secs-session-step', _sx.steps);
      setT('secs-step-num', _sx.steps);
      setT('secs-reward-max', (d.global_reward||0).toFixed(3));

      // [fix-T5] 不再写 Step 日志（由 SSE event 统一处理）
      // 如果 SSE 未连接，才写 fallback 日志
      if (!_sx.esrc || _sx.esrc.readyState !== EventSource.OPEN) {
        _logConsole('Step '+_sx.steps+' | reward='+Number(d.global_reward||0).toFixed(3)+' | agents='+(Object.keys(d.agent_actions||{}).length), 'step');
      }

      // 更新收益
      if (d.global_reward !== undefined && d.global_reward != null) {
        _sx.rewardPoints.push(d.global_reward);
        setT('secs-session-score', Number(d.global_reward).toFixed(3));
        if (_sx.rewardPoints.length > 1) setT('secs-reward-trend', d.global_reward>=_sx.rewardPoints[_sx.rewardPoints.length-2] ? '↗' : '↘');
        setT('secs-reward-max', Math.max.apply(null,_sx.rewardPoints).toFixed(3));
        _updateRewardChart();
      }

      // [fix-T1] 兜底：首个 step 成功后确保 loading 状态已释放
      document.getElementById('secs-btn-launch').style.display = 'none';
      document.getElementById('secs-ctrl-panel').style.display = 'block';

      // 更新 SSE 风格数据（用于可视化）
      if (window._onSSEStep) {
        window._onSSEStep({
          type: 'step', step_id: d.step_num || _sx.steps,
          global_reward: d.global_reward,
          agent_actions: d.agent_actions,
          messages_count: d.messages_count,
          total_steps: _sx.maxSteps || 150,
        });
      }

      if (d.converged || d.status === 'completed') {
        showToast('✅ 仿真已完成！共 '+_sx.steps+' 步', 'success');
        document.getElementById('secs-session-status').textContent = '已完成';
        _sx.simRunning = false;
        _finalizeSimFromSession();
        // [fix-T4] 完成后刷新统计和历史
        loadSecsStats();
        loadExerciseHistory();
      } else {
        document.getElementById('secs-session-status').textContent = '已暂停 (Step '+_sx.steps+')';
        // [fix-T4] 每步后刷新统计（步数实时更新）
        loadSecsStats();
      }
    } catch(e) {
      showToast('单步执行失败: '+e.message, 'error');
      _logConsole('❌ 单步失败: '+e.message, 'err');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '⏯ 单步'; }
    }
  };
  window.sexyPauseResume = async function() {
    if (!_sx.sessionId) { showToast('请先启动演练','warn'); return; }
    _paused = !_paused;
    var btn = document.getElementById('secs-btn-pause');

    if (_paused) {
      // 调用 pause 接口（等同于 stop，保留状态）
      try {
        var r = await fetch(SECS+'/sessions/'+encodeURIComponent(_sx.sessionId)+'/pause', { method:'POST' });
        var d = await r.json();
        if (!r.ok || d.error) {
          _paused = false;
          showToast(d.error || '暂停失败', 'error');
          return;
        }
      } catch(e) {
        _paused = false;
        showToast('暂停请求失败: '+e.message, 'error');
        return;
      }
      if (btn) btn.textContent = '▶ 继续';
      document.getElementById('secs-session-status').textContent = '已暂停';
      showToast('已暂停 — 可使用单步执行', 'info');
      _logConsole('⏸ 已暂停 (可单步续跑)', 'info');
    } else {
      if (btn) btn.textContent = '⏸ 暂停';
      document.getElementById('secs-session-status').textContent = '运行中';
      showToast('已继续 — 点击"沙箱推演"恢复自动运行', 'info');
      _logConsole('▶ 已继续（需点击推演按钮自动运行）', 'info');
    }
  };

  // ═══════════════════════════════════════════════════════════════
  // IndexedDB 持久化：演练结果不丢失
  // ═══════════════════════════════════════════════════════════════
  function _getDB() {
    return new Promise(function(resolve, reject) {
      var req = indexedDB.open('AgentsGroup_SECS', 1);
      req.onupgradeneeded = function(e) {
        var db = e.target.result;
        if (!db.objectStoreNames.contains('sessions')) {
          db.createObjectStore('sessions', {keyPath:'session_id'});
        }
      };
      req.onsuccess = function(e){ resolve(e.target.result); };
      req.onerror = function(){ reject(req.error); };
    });
  }
  async function _saveToIndexedDB(sessionData) {
    try {
      var db = await _getDB();
      var tx = db.transaction('sessions','readwrite');
      tx.objectStore('sessions').put(sessionData);
      return new Promise(function(r){ tx.oncomplete = r; });
    } catch(e) { console.warn('IndexedDB save failed:', e); }
  }
  async function _loadFromIndexedDB(sessionId) {
    try {
      var db = await _getDB();
      return new Promise(function(resolve){
        var tx = db.transaction('sessions','readonly');
        var req = tx.objectStore('sessions').get(sessionId);
        req.onsuccess = function(){ resolve(req.result); };
        req.onerror = function(){ resolve(null); };
      });
    } catch(e) { return null; }
  }

  // ── Init ──
  _bindInjectButtons();
  _setInjectEnabled(false);  // 注入按钮初始禁用，启动演练后启用
  _updateLaunchButton();     // 启动按钮初始禁用
  // 监听仿真模式 radio 手动切换
  document.querySelectorAll('input[name="secs-mode"]').forEach(function(r){
    r.addEventListener('change', function(){
      _selectedSceneMode = this.value;
      _renderSimParams();
    });
  });

  // ══════════════════════════════════════════════════════════════
  // P1: 房间视觉动效 — 根据SSE事件动态切换房间class
  // ══════════════════════════════════════════════════════════════
  window._roomFxState = {};
  function _setRoomFx(roomId, fxType) {
    var rooms = document.querySelectorAll('.env-room[data-room-id="'+roomId+'"]');
    if (!rooms.length) return;
    // 清除旧动效
    rooms.forEach(function(r){ r.classList.remove('room-pulse','room-alert','room-cracked','room-unhealthy'); });
    if (!fxType) return;
    if (fxType === 'pulse') { rooms.forEach(function(r){ r.classList.add('room-pulse'); }); }
    else if (fxType === 'alert') { rooms.forEach(function(r){ r.classList.add('room-alert'); }); }
    else if (fxType === 'cracked') { rooms.forEach(function(r){ r.classList.add('room-cracked'); }); }
    else if (fxType === 'unhealthy') { rooms.forEach(function(r){ r.classList.add('room-unhealthy'); }); }
    window._roomFxState[roomId] = fxType;
  }
  function _clearAllRoomFx() {
    document.querySelectorAll('.env-room').forEach(function(r){
      r.classList.remove('room-pulse','room-alert','room-cracked','room-unhealthy');
    });
    window._roomFxState = {};
  }

  // ══════════════════════════════════════════════════════════════
  // P1: Agent 动态移动动画
  // ══════════════════════════════════════════════════════════════
  window._agentMoveAnims = {};  // { agentId: AnimationController }
  function animateAgentMove(agentId, fromEl, toRoomId, duration) {
    if (!duration) duration = 1200;
    // 找目标房间的位置
    var toRoom = document.querySelector('.env-room[data-room-id="'+toRoomId+'"]');
    if (!toRoom || !fromEl) return;
    var fromRect = fromEl.getBoundingClientRect();
    var toRect = toRoom.getBoundingClientRect();
    var targetX = toRect.left + Math.random()*(toRect.width-30) + 10;
    var targetY = toRect.top + Math.random()*(toRect.height-30) + 10;
    // 创建移动中的agent影子
    var ghost = fromEl.cloneNode(true);
    ghost.id = ''; ghost.style.position='fixed'; ghost.style.zIndex='50';
    ghost.style.left=fromRect.left+'px'; ghost.style.top=fromRect.top+'px';
    ghost.style.pointerEvents='none'; ghost.style.transition='none';
    ghost.style.opacity='0.85'; ghost.style.transform='scale(0.9)';
    ghost.style.boxShadow='0 4px 20px rgba(34,211,238,0.3)';
    document.body.appendChild(ghost);
    var start = performance.now();
    function frame(now) {
      var t = Math.min((now - start) / duration, 1);
      var ease = t<0.5 ? 2*t*t : 1-Math.pow(-2*t+2,2)/2; // easeInOutQuad
      var cx = fromRect.left + (targetX - fromRect.left)*ease;
      var cy = fromRect.top + (targetY - fromRect.top)*ease;
      ghost.style.left=cx+'px'; ghost.style.top=cy+'px';
      if (t < 1) requestAnimationFrame(frame); else {
        // 到达后淡出
        ghost.style.transition='opacity 0.3s ease-out';
        ghost.style.opacity='0';
        setTimeout(function(){ if(ghost.parentNode)ghost.parentNode.removeChild(ghost); }, 300);
        // 触发房间脉冲
        _setRoomFx(toRoomId, 'pulse');
        setTimeout(function(){ _setRoomFx(toRoomId, null); }, 2000);
      }
    }
    requestAnimationFrame(frame);
  }

  // ══════════════════════════════════════════════════════════════
  // P2: 全局上下文联动 — 增强switchView + 团队卡片点击→flyToRoom
  // ══════════════════════════════════════════════════════════════
  // 在 switchView 中已处理 rp-secs 显示，此处增强：环境空间时自动初始化3D
  var _origSwitchView = window.switchView || null;
  // switchView 已在 digital-twin-cli.js 中定义，我们通过 monkey-patch 增强
  var _switchViewEnhanced = false;
  function enhanceSwitchView() {
    if (_switchViewEnhanced) return;
    _switchViewEnhanced = true;
    var orig = window.switchView;
    window.switchView = function(el) {
      orig(el);
      // 切换到环境空间时显示收益浮动卡（如果有数据）
      if (el && el.dataset.view === 'environment' && _sx.rewardPoints.length > 0) {
        showRewardFloat(true);
      } else if (el && el.dataset.view !== 'environment') {
        showRewardFloat(false);
      }
    };
  }

  // P2: 点击团队卡片 → flyToRoom 定位房间
  var _origToggleTeam = window.toggleTeam || null;
  function enhanceAgentCards() {
    document.addEventListener('click', function(e) {
      var card = e.target.closest('.agent-card');
      if (card) {
        var aid = card.getAttribute('data-agent-id');
        if (aid && S.positions[aid] && typeof switchRoom === 'function') {
          switchRoom(S.positions[aid]);
          if (typeof flyToRoom === 'function') flyToRoom(S.positions[aid]);
          _logConsole('定位: ' + aid + ' → ' + S.positions[aid], 'info');
        }
      }
      // 点击房间 → 右侧自动切换场景配置
      var room = e.target.closest('.env-room');
      if (room) {
        var rid = room.getAttribute('data-room-id');
        if (rid) {
          // 自动选择对应场景
          var sceneBtn = document.getElementById('secs-scene-btn');
          if (sceneBtn && !sceneBtn.textContent.includes(rid)) {
            // 尝试匹配场景名
            var roomNameMap = {'council':'议事厅','extraction':'萃取室','workshop':'工作坊','library':'知识库','arena':'演练场','rest':'休息区'};
            var rn = roomNameMap[rid]||rid;
            sceneBtn.title = '当前聚焦: ' + rn;
            _logConsole('房间联动: ' + rn + ' → 场景就绪', 'info');
          }
        }
      }
    });
  }

  // ══════════════════════════════════════════════════════════════
  // P2: 事件弹幕层 — SSE step事件生成气泡
  // ══════════════════════════════════════════════════════════════
  function showBarrageBubble(text, x, y, color) {
    var layer = document.getElementById('env-barrage-layer');
    if (!layer) return;
    var b = document.createElement('div');
    b.className = 'barrage-bubble';
    b.textContent = text;
    b.style.left = (Math.max(10, Math.min(x, layer.offsetWidth-220))) + 'px';
    b.style.top = (Math.max(10, y)) + 'px';
    if (color) b.style.borderColor = color;
    layer.appendChild(b);
    setTimeout(function() { if(b.parentNode)b.parentNode.removeChild(b); }, 2600);
  }

  // 奖励直观展示：在「对应 agent」头顶弹出 +value 浮卡（3D，上升淡出），居中投射到该 agent。
  // 取代旧的随机位置弹幕 + 随机虚线（看不懂）。
  function emitStepBarrage(stepData) {
    var actions = stepData.agent_actions || {};
    var roles = stepData.agent_roles || {};
    var sr = stepData.step_rewards || {};
    var gReward = stepData.global_reward;
    var keys = Object.keys(actions);
    if (!keys.length) return;
    if (typeof window._dt3dRewardPop === 'function') {
      keys.slice(0, 8).forEach(function (aid, i) {
        var rw = (sr[aid] !== undefined && sr[aid] !== null) ? sr[aid] : gReward;
        window._dt3dRewardPop(roles[aid] || '', rw, i);
      });
      return;
    }
    // 回退（3D 未就绪）：在画面中心上方弹一条，不再随机散落
    var container = document.getElementById('env-3d-container');
    if (!container) return;
    var aid0 = keys[0];
    var text = (roles[aid0] || aid0.slice(0, 6)) + ' +' + Number(gReward || 0).toFixed(2);
    showBarrageBubble(text, container.clientWidth * 0.5 - 60, 70, gReward >= 0 ? 'var(--green)' : 'var(--red)');
  }

  // SECS 流水线阶段推进：L1→L2→L3→L4 随步进循环高亮（原 HTML 固定停在 L2）
  function _advancePipelineStage(step) {
    var layers = ['L1', 'L2', 'L3', 'L4'];
    var active = layers[((step || 1) - 1) % 4];
    layers.forEach(function (L) {
      var node = document.getElementById('spipe-' + L);
      var dot = document.getElementById('spipe-dot-' + L);
      if (!node) return;
      var on = (L === active);
      node.style.border = '1px solid ' + (on ? 'var(--cyan)' : 'var(--border)');
      node.style.background = on ? 'var(--cyan-dim)' : 'transparent';
      node.classList.toggle('pipeline-node--active', on);
      var numSpan = node.querySelector('span[style*="font-weight:700"]');
      if (numSpan) numSpan.style.color = on ? 'var(--cyan)' : 'var(--muted)';
      if (dot) dot.style.background = on ? 'var(--cyan)' : 'var(--dim)';
    });
  }
  window._advancePipelineStage = _advancePipelineStage;

  // ══════════════════════════════════════════════════════════════
  // P2: 单步逻辑连线可视化
  // ══════════════════════════════════════════════════════════════
  window._linkageLines = [];  // 当前活跃的连线 [{from,to,element}]
  function drawLinkageLine(fromPos, toPos, color, label) {
    var svg = document.getElementById('env-linkage-svg');
    if (!svg) return;
    var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', fromPos.x); line.setAttribute('y1', fromPos.y);
    line.setAttribute('x2', toPos.x); line.setAttribute('y2', toPos.y);
    line.setAttribute('class', 'linkage-line');
    line.setAttribute('stroke', color || 'var(--cyan)');
    svg.appendChild(line);
    var entry = { element: line };
    window._linkageLines.push(entry);
    setTimeout(function(){
      if(line.parentNode) line.parentNode.removeChild(line);
      var idx = window._linkageLines.indexOf(entry);
      if(idx>=0) window._linkageLines.splice(idx,1);
    }, 3000);
  }
  function clearLinkageLines() {
    var svg = document.getElementById('env-linkage-svg');
    if(svg) svg.innerHTML = '';
    window._linkageLines = [];
  }

  // ══════════════════════════════════════════════════════════════
  // P3: 故障注入升级为 dropdown 菜单
  // ══════════════════════════════════════════════════════════════
  function initInjectDropdown() {
    var btn = document.getElementById('btn-inject-fault');
    if(!btn) return;
    var parent = btn.parentNode;
    // 创建dropdown容器
    var dd = document.createElement('div');
    dd.className = 'inject-dropdown';
    dd.innerHTML = '<button class="btn" id="btn-inject-fault-toggle" style="font-size:9px;padding:3px 6px">💥 注入故障 ▾</button>' +
      '<div class="inject-menu" id="inject-fault-menu">' +
      '<button class="inject-menu-item" onclick="injectChaos(\'model_hallucination\')">🧠 模型幻觉</button>' +
      '<button class="inject-menu-item" onclick="injectChaos(\'network_delay\')">🌐 网络延迟</button>' +
      '<button class="inject-menu-item" onclick="injectChaos(\'logic_deadlock\')">🔒 逻辑死锁</button>' +
      '<button class="inject-menu-item" onclick="injectChaos(\'skill_degradation\')">⬇️ 技能退化</button></div>';
    parent.replaceChild(dd, btn);
    var toggle = document.getElementById('btn-inject-fault-toggle');
    var menu = document.getElementById('inject-fault-menu');
    toggle.addEventListener('click', function(e){
      e.stopPropagation(); menu.classList.toggle('show');});
    document.addEventListener('click', function(){ menu.classList.remove('show'); });
  }
  window.injectChaos = async function(type) {
    if (!_sx.sessionId) { showToast('请先启动演练','warn'); return; }
    var typeLabels = {
      model_hallucination:'模型幻觉', network_delay:'网络延迟',
      logic_deadlock:'逻辑死锁', skill_degradation:'技能退化'
    };
    var typeMap = {
      model_hallucination: 'agent_failure', network_delay: 'task_mutation',
      logic_deadlock: 'agent_leave', skill_degradation: 'skill_inject'
    };
    try {
      var body = JSON.stringify({ confirm:true, type:typeMap[type]||type });
      var r = await fetch(SECS+'/sessions/'+encodeURIComponent(_sx.sessionId)+'/inject', { method:'POST', headers:{'Content-Type':'application/json'}, body:body });
      if (!r.ok) { var ej=await r.json().catch(function(){}); throw new Error(ej.detail||'注入失败'); }
      var d = await r.json();
      showToast('✓ 已注入: '+ (typeLabels[type]||type), 'success');
      _logConsole('💥 注入: '+ (typeLabels[type]||type), 'warn');
      // 触发亚健康视觉态
      var curRoom = window._currentRoomId||'workshop';
      _setRoomFx(curRoom, 'unhealthy');
      // 记录到注入历史面板
      var hist = document.getElementById('inject-history');
      if(hist){
        var time = new Date().toLocaleTimeString('zh-CN',{hour12:false});
        hist.insertAdjacentHTML('afterbegin',
          '<div style="padding:3px 0;font-size:9px;color:var(--red)">['+time+'] 💥'+(typeLabels[type]||type)+' → '+curRoom+'</div>');
      }
      // 隐藏菜单
      document.getElementById('inject-fault-menu').classList.remove('show');
    } catch(e) {
      showToast('注入失败: '+e.message,'error');
      _logConsole('❌ 注入失败: '+e.message,'err');
    }
  };

  // ══════════════════════════════════════════════════════════════
  // P3: 演练历史失败标记 + 回放
  // ══════════════════════════════════════════════════════════════
  window.playbackSession = async function(sessionId, status) {
    if (!_sx.sessionId) return;
    try {
      _logConsole('🔄 回放会话: ' + sessionId.slice(0,8), 'info');
      var r = await fetch(SECS+'/sessions/'+encodeURIComponent(sessionId));
      if (!r.ok) { _logConsole('回放失败 HTTP '+r.status, 'err'); return; }
      var d = await r.json();
      if (!d.steps_summary || !d.steps_summary.length) {
        _logConsole('该会话无步骤记录', 'warn'); return;
      }
      // 逐帧回放Agent分布
      clearLinkageSteps();
      for (var i=0;i<d.steps_summary.length;i++){
        (function(idx, step){
          setTimeout(function(){
            _logConsole('[回放] Step '+(idx+1)+'/'+d.steps_summary.length+ ' | reward='+step.global_reward?.toFixed(4), 'step');
            showBarrageBubble('Step '+(idx+1)+': '+Object.keys(step.skills_used||{}).length+' agents active',
              100+Math.random()*300, 80+idx*8, 'var(--amber)');
            // 更新收益
            if (step.global_reward!==undefined) updateErfValue(step.global_reward);
          }, idx*400);
        })(i,d.steps_summary[i]);
      }
      _setRoomFx((status==='failed'||status==='error')?'workshop':'council',
        (status==='failed'||status==='error')?'cracked':'pulse');
    } catch(e){_logConsole('回放异常: '+e.message,'err')}
  };

  function clearLinkageSteps() { /* 清除旧连线 */ clearLinkageLines(); _clearAllRoomFx(); }

  // ══════════════════════════════════════════════════════════════
  // P3: 收益曲线内嵌到环境空间
  // ══════════════════════════════════════════════════════════════
  function showRewardFloat(show) {
    var el = document.getElementById('env-reward-float');
    if (!el) return;
    el.style.display = show?'block':'none';
    if (show && _sx.rewardPoints.length > 0) updateErfValue(_sx.rewardPoints[_sx.rewardPoints.length-1]);
  }
  function updateErfValue(reward) {
    var valEl = document.getElementById('erf-reward-value');
    var trendEl = document.getElementById('erf-reward-trend');
    var lineEl = document.getElementById('erf-chart-line');
    if (valEl) valEl.textContent = reward!==null&&reward!==undefined?Number(reward).toFixed(4):'—';
    if (trendEl && _sx.rewardPoints.length>1) {
      var prev = _sx.rewardPoints[_sx.rewardPoints.length-2];
      trendEl.textContent = reward>=prev?'↗':'↘';
      trendEl.style.color = reward>=prev?'var(--green)':'var(--red)';
    }
    // 迷你曲线更新
    if(lineEl && _sx.rewardPoints.length>1){
      var pts=_sx.rewardPoints.slice(-40); var min=Math.min.apply(null,pts), max=Math.max.apply(null,pts), range=max-min||1;
      var ptsStr=pts.map(function(p,i){
        var x=i/(pts.length-1)*160, y=28-((p-min)/range)*26;
        return x.toFixed(1)+','+y.toFixed(1);
      }).join(' ');
      lineEl.setAttribute('points', ptsStr);
    }
  }

  // ══════════════════════════════════════════════════════════════
  // P4: 萃取可视化 — SOP精华徽章
  // ══════════════════════════════════════════════════════════════
  function showExtractBadge(sopData) {
    // 在萃取室区域显示徽章（动态创建）
    var container = document.querySelector('#view-environment .env-container');
    if (!container) return;
    var badge = document.createElement('div');
    badge.className = 'sop-extract-badge';
    badge.innerHTML = '✦';
    badge.title = (sopData.name||'SOP') + ' avg_reward=' + (sopData.avg_reward||0).toFixed(3);
    badge.onclick = function(e){
      e.stopPropagation();
      var detail = document.createElement('div');
      detail.style.cssText = 'position:absolute;top:30px;right:-10px;z-index:99;background:rgba(13,17,23,0.96);border:1px solid var(--border);border-radius:8px;padding:12px;min-width:180px;box-shadow:0 12px 32px rgba(0,0,0,0.5);color:var(--text);font-size:11px;line-height:1.5';
      detail.innerHTML = '<div style="color:var(--purple);font-weight:600;margin-bottom:6px">✦ 精华萃取产出</div>'+
        '<div>SOP: <b>'+(sopData.name||'—')+'</b></div><div>平均收益: <span style="color:var(--green)">'+(sopData.avg_reward||0).toFixed(3)+'</span></div><div>状态: <span style="color:var(--cyan)">'+(sopData.status||'candidate')+'</span></div><div style="margin-top:6px;color:var(--dim);font-size:10px">'+(sopData.description||'—')+'</div>';
      badge.parentNode.insertBefore(detail, badge.nextSibling);
      document.addEventListener('click', function closeDetail(ev){
        if(detail.contains(ev.target)||ev.target===badge)return;
        detail.remove();document.removeEventListener('click',closeDetail);
      });
    };
    container.appendChild(badge);
  }

  // ══════════════════════════════════════════════════════════════
  // P4: Agent 升级动效
  // ══════════════════════════════════════════════════════════════
  function playUpgradeAnimation(targetElement) {
    if (!targetElement) return;
    var ring = document.createElement('div');
    ring.className = 'agent-upgrade-ring';
    targetElement.style.position='relative';
    targetElement.appendChild(ring);
    setTimeout(function(){ if(ring.parentNode)ring.parentNode.removeChild(ring); }, 1300);
  }

  // ══════════════════════════════════════════════════════════════
  // P4: 并行模式分屏对比视图
  // ══════════════════════════════════════════════════════════════
  function showParallelView(branchCount, data) {
    var envView = document.getElementById('view-environment');
    if (!envView) return;
    var origContent = envView.innerHTML;
    envView.innerHTML = '<div class="parallel-grid" id="parallel-grid"></div>';
    var grid = document.getElementById('parallel-grid');
    for (var i=0;i<branchCount;i++) {
      var cell = document.createElement('div');
      cell.className = 'parallel-cell';
      cell.innerHTML = '<div class="branch-tag">分支'+(i+1)+(data[i]?.label||'')+'</div><canvas id="branch-canvas-'+i+'" width="320" height="500"></canvas>';
      grid.appendChild(cell);
    }
    // 返回按钮
    var backBtn = document.createElement('button');
    backBtn.className='btn';backBtn.textContent='← 返回单视图';
    backBtn.style.cssText = 'position:absolute;top:10px;right:14px;z-index:20';
    backBtn.onclick=function(){ envView.innerHTML=origContent; };
    grid.style.position='relative';
    grid.parentElement.insertBefore(backBtn,grid);
  }

  // ══════════════════════════════════════════════════════════════
  // 集成：将所有新功能钩子挂载到现有 SSE 流程中
  // ══════════════════════════════════════════════════════════════
  function _hookNewFeatures() {
    enhanceSwitchView();
    enhanceAgentCards();
    initInjectDropdown();
    _logConsole('✓ 新功能模块已加载: 房间动效|弹幕|连线|故障菜单|收益浮卡|萃取|升级|分屏', 'info');
  }
  // 在页面加载时自动初始化
  if (document.readyState==='complete') _hookNewFeatures();
  else window.addEventListener('DOMContentLoaded', _hookNewFeatures);

  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', function() {
      _setInjectEnabled(false);
      _bootstrapRuntimePanel();
    }, { once:true });
  } else {
    _setInjectEnabled(false);
    _bootstrapRuntimePanel();
  }

  window.addEventListener('load', function() {
    _setInjectEnabled(false);  // 确保加载完成后仍是禁用
    loadRuntimeStatus();
    loadSecsStats();
    loadExerciseHistory();
    _applyUrlTeamParam();      // 跳转带 ?team= 时自动选中演练团队
    // Phase 12.F：导演台已在 HTML 中静态并入 SECS，无需运行时搬家。
    // 仅需以 SECS radio 为模式唯一源 → 同步到 _DTS.selectedMode 并监听变化。
    _syncModeFromSecs();
    document.querySelectorAll('input[name="secs-mode"]').forEach(function (r) {
      r.addEventListener('change', _syncModeFromSecs);
    });
  });

  // SECS radio(what_if/parallel/evolutionary) → director selectedMode(what_if/multi_branch/evolutionary)
  function _syncModeFromSecs() {
    try {
      var r = document.querySelector('input[name="secs-mode"]:checked');
      if (!r || !window._DTS) return;
      var map = { what_if: 'what_if', parallel: 'multi_branch', evolutionary: 'evolutionary' };
      window._DTS.selectedMode = map[r.value] || 'what_if';
    } catch (e) { /* noop */ }
  }

  // 跳转携带 ?team=build_system（来自成本治理/效率视角链接）→ 自动选中该演练团队。
  // 否则演练无 _selectedTeamId → 要么提示「请先选择演练团队」中止，要么以空团队跑
  // → world 无 agent → twin=0 → reward 恒 0。
  async function _applyUrlTeamParam() {
    try {
      var p = new URLSearchParams(location.search);
      var tid = p.get('team') || p.get('team_id');
      if (!tid) return;
      if (!_teamTreeData.length) {
        var r = await fetch('/api/v1/agent-config/teams-tree?limit=50');
        var data = await r.json();
        _teamTreeData = Array.isArray(data) ? data : (data.items || data.teams || []);
      }
      var team = _teamTreeData.find(function (t) { return t.team_id === tid; });
      var name = team ? (team.name || tid) : tid;
      if (typeof window.sexySelectTeam === 'function') {
        window.sexySelectTeam(tid, name);
      }
      // 强制重建 3D 房间，确保选中团队的 agent 在演练 3D 窗口里渲染出来
      // （buildRoom 在 _currentRoomId 为空时不会自动重建 → 议事厅 0 agent）
      setTimeout(function () {
        if (window._dt3dBuildRoom) window._dt3dBuildRoom(window._currentRoomId || 'council');
      }, 500);
    } catch (e) { /* non-critical */ }
  }

  // 暴露实时控制台写入函数，让 director.js（创建试炼/评分/反哺等）能联动写入同一控制台
  if (typeof window !== 'undefined') window._logConsole = _logConsole;

})();
