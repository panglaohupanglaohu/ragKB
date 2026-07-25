/**
 * eco-console.js — 物竞天择生境控制台逻辑层 (v2 XT-4.2)
 *
 * 办公室视图（?office3d=1）= 自然选择试验田：右侧演练菜单整体替换为本控制台。
 * 八区块：①总览KPI ②环境压力台 ③演练控制+回放 ④种群 ⑤世代曲线 ⑥基因池 ⑦谱系 ⑧棘轮
 *
 * 数据流：
 *   eco2RunDrill → POST /api/v1/twin-trials（drill_kind=natural_selection，任意团队可入生境）
 *               → POST .../branches/{id}/run → 结果{timeline, final_ranking, gene_pool, ...}
 *               → 渲染八区块 + createEcoReplay(timeline) 驱动左侧 3D 剧场回放
 *
 * 覆盖 secs-core.js 的旧版 ecoRunDrill/ecoLoadConfig（本文件后加载，window 赋值后者生效）。
 */
(function () {
  'use strict';

  var INTENT_ICON = { forage: '🍖', avoid: '🛡', mate: '💕', rest_explore: '💤' };
  var COLLAB_DIMS = [
    ['share_tendency', '分享'], ['signal_tendency', '信号'],
    ['follow_tendency', '跟随'], ['mate_choosiness', '择偶'],
  ];
  var _replay = null;
  var _lastResult = null;
  var _inited = false;
  var _reportShown = false;   // v2.3：每场演练自动弹一次生境报告
  var _boundContract = null;  // v4 TaskHabitatContract
  var _boundTask = null;      // XG-11 已挂接任务 {task_id, title, ...}
  var _budgetOverridden = false;

  function _renderBoundTaskUi(task) {
    _boundTask = task || null;
    var wrap = $('eco2-run-task-wrap');
    var elTitle = $('eco2-run-task');
    var elMeta = $('eco2-run-task-meta');
    var clearBtn = $('eco2-task-clear');
    var hint = $('eco2-task-mount-hint');
    if (!wrap) return;
    if (!_boundTask) {
      wrap.style.display = 'none';
      if (elTitle) elTitle.textContent = '—';
      if (elMeta) elMeta.textContent = '';
      if (clearBtn) clearBtn.style.display = 'none';
      if (hint) {
        hint.style.color = 'var(--amber)';
        hint.textContent = '尚未挂载任务 — 无业务考卷；请从下拉选择任务后再开跑。';
      }
      return;
    }
    wrap.style.display = 'block';
    if (clearBtn) clearBtn.style.display = '';
    if (hint) {
      hint.style.color = 'var(--dim)';
      hint.textContent = '已挂任务 · 考卷来自任务契约 demand（业务场景实例）。';
    }
    var title = _boundTask.title || _boundTask.name || _boundTask.task_id || '（无标题）';
    var tid = _boundTask.task_id || _boundTask.id || '';
    if (elTitle) elTitle.textContent = title;
    var bits = [];
    if (tid) bits.push('id=' + String(tid).slice(0, 12));
    if (_boundTask.status) bits.push('状态=' + _boundTask.status);
    var meta = _boundTask.metadata || {};
    if (meta.plan_id) bits.push('plan=' + meta.plan_id);
    if (meta.source) bits.push('来源=' + meta.source);
    var skills = meta.required_skills || meta.skills_used || [];
    if (skills.length) bits.push('技能=' + skills.slice(0, 6).join(','));
    if (elMeta) elMeta.textContent = bits.join(' · ');
    // 同步下拉选中
    var sel = $('eco2-primary-task-select');
    if (sel && tid) {
      var found = false;
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === tid) { sel.selectedIndex = i; found = true; break; }
      }
      if (!found && tid) {
        var opt = document.createElement('option');
        opt.value = tid;
        opt.textContent = (title || tid) + ' [已挂]';
        sel.appendChild(opt);
        sel.value = tid;
      }
    }
  }

  // XF-6: 主种群任务列表缓存
  var _primaryTasks = [];
  var _lastTaskMountTeam = '';

  function _showTaskMount(show) {
    var mount = $('eco2-task-mount');
    if (mount) mount.style.display = show ? 'block' : 'none';
  }

  function _fillPrimaryTaskSelect(tasks, selectedId) {
    var sel = $('eco2-primary-task-select');
    if (!sel) return;
    _primaryTasks = tasks || [];
    var opts = '<option value="">— 选择要挂载的任务（业务场景实例）—</option>';
    if (!_primaryTasks.length) {
      opts += '<option value="" disabled>该队暂无任务 · 请先到任务页/Plaza 派发</option>';
    } else {
      _primaryTasks.forEach(function (tk) {
        var label = tk.title + (tk.plan_id ? ' · plan:' + String(tk.plan_id).slice(0, 8) : '');
        if (tk.status) label += ' [' + tk.status + ']';
        opts += '<option value="' + esc(tk.task_id) + '"'
          + (selectedId && tk.task_id === selectedId ? ' selected' : '') + '>'
          + esc(label) + '</option>';
      });
    }
    sel.innerHTML = opts;
    if (selectedId) sel.value = selectedId;
  }

  function _loadPrimaryTasks(teamId) {
    if (!teamId) {
      _fillPrimaryTaskSelect([]);
      return Promise.resolve([]);
    }
    return _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(teamId) + '/tasks')
      .then(function (r) { return r.json ? r.json() : r; })
      .then(function (list) {
        var arr = Array.isArray(list) ? list : (list && (list.tasks || list.items || list.data)) || [];
        var tasks = arr.map(function (t) {
          return {
            task_id: t.task_id || t.id,
            title: t.title || t.name || (t.task_id || t.id),
            plan_id: _taskPlanId(t),
            status: t.status || '',
            raw: t,
          };
        }).filter(function (t) { return t.task_id; });
        var cur = (_boundTask && (_boundTask.task_id || _boundTask.id)) || '';
        _fillPrimaryTaskSelect(tasks, cur);
        return tasks;
      })
      .catch(function () {
        _fillPrimaryTaskSelect([]);
        return [];
      });
  }

  /** 选种群后刷新任务挂载区（XF-6） */
  function _syncPrimaryTaskMount(forceReload) {
    var tid = window._selectedTeamId || '';
    if (!tid) {
      _showTaskMount(false);
      _lastTaskMountTeam = '';
      return;
    }
    _showTaskMount(true);
    if (forceReload || _lastTaskMountTeam !== tid) {
      _lastTaskMountTeam = tid;
      // 换队：若当前绑定任务不属于新队，清空绑定
      if (_boundTask && forceReload !== 'keep-task') {
        // 仍可先加载列表；绑定是否保留由 deep link 路径决定
      }
      _loadPrimaryTasks(tid);
    }
  }

  window.eco2OnPrimaryTaskSelect = function (taskId) {
    var teamId = window._selectedTeamId;
    if (!teamId) {
      setText('eco2-run-status', '⚠ 请先选择投放种群');
      return;
    }
    if (!taskId) {
      window.eco2ClearPrimaryTask();
      return;
    }
    setText('eco2-run-status', '⏳ 正在挂载任务并编译考卷…');
    window.eco2BindTaskById(teamId, taskId).then(function () {
      _syncComparisonBanner();
    });
  };

  window.eco2ClearPrimaryTask = function () {
    _boundTask = null;
    _boundContract = null;
    try {
      sessionStorage.removeItem('eco_bound_task');
      sessionStorage.removeItem('eco_bound_contract');
    } catch (e) { /* ignore */ }
    try { if (window.ecoTaskHudClear) window.ecoTaskHudClear(); } catch (eH) { /* ignore */ }
    _renderBoundTaskUi(null);
    var sel = $('eco2-primary-task-select');
    if (sel) sel.value = '';
    _clearEnvDemandChips('未挂任务 — 无 demand');
    setText('eco2-run-status', '已解除任务挂载（无业务考卷）');
    _syncComparisonBanner();
  };

  function _fetch(url, opts) {
    var f = (typeof window._af === 'function') ? window._af : (window._agFetch || fetch);
    return f(url, opts);
  }
  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function setText(id, v) { var el = $(id); if (el) el.textContent = v; }

  /** 压力台只渲染 demand skills，禁止任务名/步骤长标题（无信息量、与挂载区重复） */
  function _renderEnvDemandChips(source) {
    var box = $('eco2-env-niches');
    if (!box) return;
    var names = [];
    var seen = {};
    function pushSk(s) {
      var n = _sk(s);
      if (!n || seen[n]) return;
      seen[n] = 1;
      names.push(n);
    }
    if (Array.isArray(source)) {
      // niches[] 或 skill id 字符串数组
      source.forEach(function (item) {
        if (item == null) return;
        if (typeof item === 'string') {
          pushSk(item);
        } else if (typeof item === 'object') {
          (item.demanded_skills || item.skills || []).forEach(pushSk);
        }
      });
    } else if (source && typeof source === 'object') {
      (source.demanded_skills || source.skills || []).forEach(pushSk);
    }
    if (!names.length) {
      box.innerHTML = '<span style="color:var(--dim);font-size:10px">无 demand skill</span>';
      return;
    }
    box.innerHTML = names.slice(0, 24).map(function (n) {
      return '<span class="eco2-chip" title="demand">' + esc(n) + '</span>';
    }).join(' ');
  }
  function _clearEnvDemandChips(msg) {
    var box = $('eco2-env-niches');
    if (box) box.innerHTML = '<span style="color:var(--dim);font-size:10px">'
      + esc(msg || '挂任务后显示 demand skills…') + '</span>';
  }

  // ═══ v2.3 R5: skill 名称解析（hex ID → 可读名，覆盖控制台+报告全部展示点） ═══
  var _skillNames = {};   // skillId -> 可读名（主队 + 对比种群的技能目录合并）
  function _sk(id) {
    var s = String(id == null ? '' : id);
    if (_skillNames[s]) return _skillNames[s];
    // 纯 hex 短 ID 未解析时保持原样（截短），snake_case 转空格增强可读
    if (/^[0-9a-f]{8}$/i.test(s)) return s.slice(0, 8);
    return s.replace(/_/g, ' ');
  }
  function _loadTeamSkills(teamId) {
    if (!teamId) return Promise.resolve();
    return _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(teamId))
      .then(function (r) { return r.json ? r.json() : r; })
      .then(function (d) {
        if (d && d.skills && typeof d.skills === 'object') {
          Object.keys(d.skills).forEach(function (sid) {
            var sd = d.skills[sid];
            var nm = (sd && (sd.name || sd.slug)) || '';
            if (nm) _skillNames[sid] = nm;
          });
        }
        return d;
      }).catch(function () { return null; });
  }

  function _setTeamUi(teamId, teamName) {
    var prev = window._selectedTeamId;
    window._selectedTeamId = teamId;
    window._selectedTeamName = teamName || teamId;
    var btn = $('eco2-run-team');
    if (btn) {
      btn.textContent = '👥 ① 种群：' + (teamName || teamId);
      btn.style.color = 'var(--cyan)';
    }
    var secsBtn = document.getElementById('secs-team-btn');
    if (secsBtn && teamName) {
      secsBtn.textContent = '👥 ' + teamName;
      secsBtn.style.color = 'var(--cyan)';
    }
    try {
      sessionStorage.setItem('eco_bound_team', JSON.stringify({ id: teamId, name: teamName || teamId }));
    } catch (e) { /* ignore */ }
    // XF-6: 换队则刷新任务挂载菜单；换队清空旧任务绑定（深链随后会再绑）
    if (prev && prev !== teamId) {
      _boundTask = null;
      _boundContract = null;
      _renderBoundTaskUi(null);
    }
    _syncPrimaryTaskMount(true);
  }

  /** XG-11: 从 URL/session 自动选中投放种群；支持 team_ids / extra_team_ids 多队对抗 */
  window.eco2ApplyTeamFromUrl = function () {
    var qs = new URLSearchParams(window.location.search || '');
    var teamId = qs.get('team_id') || '';
    var teamName = qs.get('team_name') || '';
    // 多队：team_ids=a,b,c 或 extra_team_ids=b,c
    var multiRaw = qs.get('team_ids') || '';
    var extraRaw = qs.get('extra_team_ids') || '';
    var multiIds = multiRaw
      ? multiRaw.split(',').map(function (s) { return s.trim(); }).filter(Boolean)
      : [];
    var extraIds = extraRaw
      ? extraRaw.split(',').map(function (s) { return s.trim(); }).filter(Boolean)
      : [];
    if (!teamId && multiIds.length) teamId = multiIds[0];
    if (multiIds.length > 1) {
      extraIds = multiIds.slice(1).concat(extraIds.filter(function (id) {
        return multiIds.indexOf(id) < 0;
      }));
    }
    try {
      if (!extraIds.length) {
        var ex = sessionStorage.getItem('eco_extra_team_ids');
        if (ex) extraIds = JSON.parse(ex) || [];
      }
      if (extraIds.length) {
        sessionStorage.setItem('eco_extra_team_ids', JSON.stringify(extraIds));
        window.__ECO_EXTRA_TEAM_IDS__ = extraIds;
      }
    } catch (e) { /* ignore */ }
    if (!teamId) {
      try {
        var raw = sessionStorage.getItem('eco_bound_team');
        if (raw) {
          var t = JSON.parse(raw);
          teamId = t.id || '';
          teamName = t.name || '';
        }
      } catch (e) { /* ignore */ }
    }
    if (!teamId) return Promise.resolve(null);
    // 暴露给 drill 创建：优先用 __ECO_EXTRA_TEAM_IDS__
    if (typeof window.eco2GetExtraTeamIds !== 'function') {
      window.eco2GetExtraTeamIds = function () {
        try {
          return window.__ECO_EXTRA_TEAM_IDS__ ||
            JSON.parse(sessionStorage.getItem('eco_extra_team_ids') || '[]') ||
            [];
        } catch (e2) {
          return [];
        }
      };
    }
    if (typeof window.sexySelectTeam === 'function') {
      window.sexySelectTeam(teamId, teamName || teamId);
      _setTeamUi(teamId, teamName || teamId);
      return Promise.resolve({ id: teamId, name: teamName || teamId, extra_team_ids: extraIds });
    }
    return _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(teamId))
      .then(function (r) { return r.json ? r.json() : r; })
      .then(function (d) {
        var nm = (d && (d.name || d.team_name)) || teamName || teamId;
        if (typeof window.sexySelectTeam === 'function') {
          window.sexySelectTeam(teamId, nm);
        }
        _setTeamUi(teamId, nm);
        _loadTeamSkills(teamId);
        return { id: teamId, name: nm };
      })
      .catch(function () {
        _setTeamUi(teamId, teamName || teamId);
        return { id: teamId, name: teamName || teamId };
      });
  };

  /** XG-11: 从任务编译/绑定生境契约（同时刷新「已挂接任务」UI） */
  window.eco2BindTask = function (taskObj, teamId) {
    if (!taskObj) return Promise.resolve(null);
    var task = Array.isArray(taskObj) ? taskObj[0] : taskObj;
    var tasks = Array.isArray(taskObj) ? taskObj : [taskObj];
    // 先立刻显示挂接任务（即使契约编译慢/失败，用户也能看到）
    _renderBoundTaskUi(task);
    try { sessionStorage.setItem('eco_bound_task', JSON.stringify(task)); } catch (e) { /* ignore */ }
    return _fetch('/api/v1/eco-runtime/habitat-contract/from-tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tasks: tasks }),
    }).then(function (r) { return r.json ? r.json() : r; })
      .then(function (d) {
        if (!d || !d.ok || !d.contract) {
          setText('eco2-run-status',
            '📋 任务已挂接「' + esc(task.title || task.task_id || '') + '」但契约编译失败: ' +
            ((d && d.error) || 'unknown') + ' — 仍可用团队技能做生境演练');
          return { contract: null, task: task };
        }
        _boundContract = d.contract;
        _budgetOverridden = false;
        var sb = _boundContract.step_budget || {};
        var stepsEl = $('eco2-run-steps');
        var gensEl = $('eco2-run-gens');
        if (stepsEl && sb.max_steps_per_generation) stepsEl.value = sb.max_steps_per_generation;
        if (gensEl && sb.max_generations) gensEl.value = sb.max_generations;
        _renderEnvDemandChips(_boundContract.niches || []);
        // XF-5：任务型 HUD（仅契约挂接时；步骤标题在 HUD，不进压力台）
        try {
          if (window.ecoTaskHudBind) window.ecoTaskHudBind(_boundContract, task);
        } catch (eHud) { /* ignore */ }
        var tid = teamId || window._selectedTeamId || '';
        setText('eco2-run-status',
          '🧬 团队 ' + esc(window._selectedTeamName || tid) +
          ' · 任务「' + esc(task.title || task.task_id || '') + '」' +
          ' · 契约 ' + (_boundContract.niches || []).length + ' 步 · 预算 ' +
          (sb.max_steps_per_generation || '?') + '步×' + (sb.max_generations || '?') + '代 — 可直接开始');
        // 主任务变化后，尝试给对比队预选同 plan 任务
        try {
          var pPlan = _taskPlanId(task) || (_boundContract && _boundContract.plan_id) || '';
          if (pPlan && _rivalTeams.length) {
            _rivalTeams.forEach(function (r) {
              if (r.task_id) return;
              var same = (r.tasks || []).find(function (x) { return x.plan_id === pPlan; });
              if (same) {
                r.task_id = same.task_id;
                r.task_title = same.title;
                r.plan_id = same.plan_id;
              }
            });
            _renderRivalChips();
          }
          _syncComparisonBanner();
        } catch (eSync) { /* ignore */ }
        return { contract: _boundContract, task: task };
      }).catch(function (err) {
        setText('eco2-run-status',
          '📋 任务已挂接「' + esc((task && (task.title || task.task_id)) || '') +
          '」· 契约请求失败: ' + (err.message || err));
        return { contract: null, task: task };
      });
  };

  window.eco2BindTaskById = function (teamId, taskId) {
    if (!teamId || !taskId) return Promise.resolve(null);
    // 优先 session 缓存（从任务菜单深链时已写入）
    try {
      var cached = sessionStorage.getItem('eco_bound_task');
      if (cached) {
        var ct = JSON.parse(cached);
        if (ct && (ct.task_id === taskId || ct.id === taskId)) {
          return window.eco2BindTask(ct, teamId);
        }
      }
    } catch (e) { /* ignore */ }
    // 先用 URL 中的 id 占位显示，避免「没挂上」的空白感
    _renderBoundTaskUi({ task_id: taskId, title: '加载中… ' + taskId, status: '…' });
    return _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(teamId) + '/tasks/' + encodeURIComponent(taskId))
      .then(function (r) {
        if (r && typeof r.ok === 'boolean' && !r.ok) {
          return _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(teamId) + '/tasks')
            .then(function (r2) { return r2.json ? r2.json() : r2; })
            .then(function (list) {
              var arr = Array.isArray(list) ? list : (list && (list.tasks || list.items || list.data)) || [];
              var found = arr.find(function (t) { return (t.task_id || t.id) === taskId; });
              if (!found) throw new Error('task not found in list');
              return found;
            });
        }
        return r.json ? r.json() : r;
      })
      .then(function (task) {
        if (!task || !(task.task_id || task.id || task.title)) {
          throw new Error('empty task payload');
        }
        // 规范化 id 字段
        if (!task.task_id && task.id) task.task_id = task.id;
        try { sessionStorage.setItem('eco_bound_task', JSON.stringify(task)); } catch (e) { /* ignore */ }
        return window.eco2BindTask(task, teamId);
      })
      .catch(function (err) {
        _renderBoundTaskUi({
          task_id: taskId,
          title: '（未能拉取详情）' + taskId,
          status: 'error',
          metadata: {},
        });
        setText('eco2-run-status', '⚠ 拉取任务失败: ' + (err.message || err) + ' — 任务 id 已显示，请检查任务是否仍存在');
        return null;
      });
  };

  // ═══ 初始化：读生境配置 → 滑杆/生态位/左侧旋钮 ═══
  window.eco2Init = function () {
    if (_inited) return;
    _inited = true;
    _bindSliders();
    window.ecoLoadConfig();
    _renderLeftKnobs();
    _loadNichesFromTeam();
    // XG-11: 先团队，再 plan/task 契约
    try {
      var qs = new URLSearchParams(window.location.search || '');
      var planId = qs.get('plan_id') || '';
      var taskId = qs.get('task_id') || '';
      var teamId = qs.get('team_id') || '';
      window.eco2ApplyTeamFromUrl().then(function (team) {
        var tid = (team && team.id) || teamId || window._selectedTeamId || '';
        // URL 无 task_id 时尝试 session 任务缓存
        if (!taskId) {
          try {
            var ct = JSON.parse(sessionStorage.getItem('eco_bound_task') || 'null');
            if (ct && (ct.task_id || ct.id)) taskId = ct.task_id || ct.id;
          } catch (e3) { /* ignore */ }
        }
        if (taskId && tid) {
          return window.eco2BindTaskById(tid, taskId).then(function (res) {
            // res 可能是 {contract, task} 或 null；有 task UI 即算挂接成功
            if (res && (res.task || res.contract || res.niches)) return res;
            if (_boundTask) return { task: _boundTask };
            return null;
          });
        }
        return null;
      }).then(function (bound) {
        if (bound) return;
        var planObj = null;
        if (window.__ECO_PLAN__ && window.__ECO_PLAN__.steps) {
          planObj = window.__ECO_PLAN__;
        } else {
          try {
            var raw = sessionStorage.getItem('eco_bound_plan');
            if (raw) planObj = JSON.parse(raw);
          } catch (e2) { planObj = null; }
        }
        if (planObj && planObj.steps && planObj.steps.length) {
          return window.eco2BindPlan(planObj).then(function () {
            if (window._selectedTeamId) {
              setText('eco2-run-status',
                '🧬 团队 ' + esc(window._selectedTeamName || window._selectedTeamId) +
                ' · 计划已绑定 — 可直接开始物竞天择');
            }
          });
        }
        if (planId && !window._selectedTeamId) {
          setText('eco2-run-status', '📋 有 plan_id 但未选团队：请从团队任务菜单「🧬 物竞试验田」进入，或点「选择投放种群」');
        } else if (!window._selectedTeamId) {
          setText('eco2-run-status', '投放种群后，点「开始物竞天择」。推荐路径：Plaza 拆解 → 团队任务 → 🧬 物竞试验田');
        }
      }).catch(function () { /* ignore */ });
    } catch (e) { /* ignore */ }
  };

  /** v4: 绑定 ExecutionPlan → 编译 TaskHabitatContract 并填步数/世代 */
  window.eco2BindPlan = function (plan) {
    if (!plan || !plan.steps || !plan.steps.length) {
      setText('eco2-run-status', '⚠ 计划无步骤，无法绑定');
      return Promise.resolve(null);
    }
    return _fetch('/api/v1/eco-runtime/habitat-contract/from-plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan: plan }),
    }).then(function (r) { return r.json ? r.json() : r; })
      .then(function (d) {
        if (!d || !d.ok || !d.contract) {
          setText('eco2-run-status', '⚠ 契约编译失败: ' + ((d && d.error) || 'unknown'));
          return null;
        }
        _boundContract = d.contract;
        _budgetOverridden = false;
        var sb = _boundContract.step_budget || {};
        var stepsEl = $('eco2-run-steps');
        var gensEl = $('eco2-run-gens');
        if (stepsEl && sb.max_steps_per_generation) stepsEl.value = sb.max_steps_per_generation;
        if (gensEl && sb.max_generations) gensEl.value = sb.max_generations;
        // 压力台只显示 demand skills；步骤标题在 HUD
        _renderEnvDemandChips(_boundContract.niches || []);
        try {
          if (window.ecoTaskHudBind) {
            window.ecoTaskHudBind(_boundContract, {
              title: _boundContract.topic || _boundContract.plan_id || '计划考卷',
              task_id: _boundContract.plan_id || '',
            });
          }
        } catch (eHud2) { /* ignore */ }
        setText('eco2-run-status',
          '📋 已绑定计划 ' + esc(_boundContract.plan_id || '') +
          ' · ' + (_boundContract.niches || []).length + ' 步骤 · 预算 ' +
          (sb.max_steps_per_generation || '?') + '步×' + (sb.max_generations || '?') + '代');
        try { _syncComparisonBanner(); } catch (eB) { /* ignore */ }
        return _boundContract;
      }).catch(function (err) {
        setText('eco2-run-status', '⚠ 绑定计划失败: ' + (err.message || err));
        return null;
      });
  };
  window.eco2ClearPlan = function () {
    _boundContract = null;
    _renderBoundTaskUi(null);
    try {
      sessionStorage.removeItem('eco_bound_task');
      sessionStorage.removeItem('eco_bound_contract');
    } catch (e) { /* ignore */ }
    try { if (window.ecoTaskHudClear) window.ecoTaskHudClear(); } catch (eH) { /* ignore */ }
    _clearEnvDemandChips('未挂任务 — 无 demand');
    setText('eco2-run-status', '已解除计划/任务绑定（回退 v3 手填预算）');
  };

  window.eco2CopyIntegration = function () {
    var integ = window.__LAST_INTEGRATION__;
    if (!integ) return;
    var text = JSON.stringify(integ.recommended_bindings || integ, null, 2);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        setText('eco2-run-status', '📋 已复制集成建议 JSON');
      }).catch(function () { window.prompt('复制：', text); });
    } else {
      window.prompt('复制：', text);
    }
  };

  window.eco2ApplyIntegration = function (confirm) {
    var integ = window.__LAST_INTEGRATION__;
    var teamId = window._selectedTeamId;
    if (!integ || !teamId) {
      setText('eco2-run-status', '⚠ 无集成建议或未选团队');
      return;
    }
    _fetch('/api/v1/eco-runtime/skill-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        confirm: !!confirm,
        report: integ,
        feedback_router: false,
      }),
    }).then(function (r) { return r.json ? r.json() : r; })
      .then(function (d) {
        if (!d || !d.ok) {
          setText('eco2-run-status', '⚠ apply: ' + ((d && d.error) || 'failed') + (d && d.hint ? ' — ' + d.hint : ''));
          return;
        }
        if (!confirm) {
          setText('eco2-run-status', '预览: 将写回 ' + (d.would_apply || 0) + ' 处绑定（需 confirm=true）');
        } else {
          setText('eco2-run-status', '✅ 已写回 ' + (d.applied || 0) + ' 处技能绑定');
        }
      }).catch(function (e) {
        setText('eco2-run-status', '⚠ apply 失败: ' + (e.message || e));
      });
  };

  /** XG-10: 按黄金适者技能集合创建一条溯源任务（可选，默认仅创建元数据草稿） */
  window.eco2DispatchWinner = function () {
    var result = window.__LAST_ECO_RESULT__;
    var teamId = window._selectedTeamId;
    if (!result || !teamId) {
      setText('eco2-run-status', '⚠ 无演练结果或未选团队');
      return;
    }
    var ranking = result.final_ranking || [];
    var champ = ranking.slice().sort(function (a, b) {
      return (b.survival_ticks || 0) - (a.survival_ticks || 0);
    })[0];
    if (!champ) {
      setText('eco2-run-status', '⚠ 无适者');
      return;
    }
    var contract = result.contract || _boundContract || {};
    var title = '物竞适者执行: ' + (contract.topic || contract.plan_id || teamId).slice(0, 40);
    _fetch('/api/v1/eco-runtime/skill-integration/dispatch-winner', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        agent_id: champ.agent_id,
        skill_genome: champ.skill_genome || [],
        plan_id: contract.plan_id || '',
        topic: contract.topic || '',
        fingerprint: (contract.provenance || {}).fingerprint || '',
        survival_ticks: champ.survival_ticks || 0,
        create_task: true,
      }),
    }).then(function (r) { return r.json ? r.json() : r; })
      .then(function (d) {
        if (d && d.ok) {
          setText('eco2-run-status', '🏷 已创建适者任务 ' + (d.task_id || '') + '（溯源 plan/eco）');
        } else {
          setText('eco2-run-status', '⚠ 派发失败: ' + ((d && d.error) || 'unknown'));
        }
      }).catch(function (e) {
        setText('eco2-run-status', '⚠ 派发失败: ' + (e.message || e));
      });
  };

  // ── 左侧音量式旋钮台 ───────────────────────────────────────────
  // 三组，与配置 JSON 字段严格对应：
  //   A habitat(4)  → abundance / predator_pressure / drift_prob / niche_capacity
  //   B evolution_pressure(11) → 环境选择压（含性选择/频依/上位；不含衰老）
  //   C metabolism  → senescence_rate（Agent 生命史，非环境）
  var _knobState = {
    // A habitat
    abundance: 0.7,
    predator_pressure: 0.12,
    drift_prob: 0.2,
    niche_capacity: 3,
    // B evolution_pressure（环境侧）
    skill_idle_penalty: 1.2,
    genome_carry_cost: 0.08,
    min_steps_when_contract: 64,
    min_gens_when_contract: 4,
    prefer_forage_when_can_serve: 1,
    predator_bias_unskilled: 2.0,
    scarce_share_boost: 1.2,
    same_pop_share_bias: 0.7,
    sexual_selection_strength: 1.0,
    freq_dep_strength: 0.5,
    epistasis_strength: 0.2,
    // C metabolism · Agent 侧
    senescence_rate: 0.003,
  };
  var _habitatDefs = [
    { key: 'abundance', label: '丰饶度', hint: '≈ token 松紧', min: 0.3, max: 2.0, step: 0.05, fmt: function (v) { return v.toFixed(2); } },
    { key: 'predator_pressure', label: '事故压', hint: '突发故障概率', min: 0, max: 0.4, step: 0.01, fmt: function (v) { return v.toFixed(2); } },
    { key: 'drift_prob', label: '需求漂移', hint: '换技能需求', min: 0, max: 1, step: 0.02, fmt: function (v) { return v.toFixed(2); } },
    { key: 'niche_capacity', label: '竞争名额', hint: '0=不限', min: 0, max: 6, step: 1, fmt: function (v) { return v <= 0 ? '∞' : String(Math.round(v)); } },
  ];
  var _pressureDefs = [
    { key: 'skill_idle_penalty', label: '闲置税', hint: '能 serve 却 REST', min: 0, max: 5, step: 0.1, fmt: function (v) { return v.toFixed(1); } },
    { key: 'genome_carry_cost', label: '囤积税', hint: '每 skill 每 tick 代谢', min: 0, max: 0.5, step: 0.01, fmt: function (v) { return v.toFixed(2); } },
    { key: 'min_steps_when_contract', label: '契约最少步', hint: '绑定任务时步数底', min: 0, max: 500, step: 8, fmt: function (v) { return String(Math.round(v)); } },
    { key: 'min_gens_when_contract', label: '契约最少代', hint: '绑定任务时世代底', min: 0, max: 20, step: 1, fmt: function (v) { return String(Math.round(v)); } },
    { key: 'prefer_forage_when_can_serve', label: '偏觅食', hint: '0/1 能做则 FORAGE', min: 0, max: 1, step: 1, fmt: function (v) { return Math.round(v) ? '1' : '0'; } },
    { key: 'predator_bias_unskilled', label: '无技偏压', hint: '事故盯无 skill', min: 0, max: 8, step: 0.1, fmt: function (v) { return v.toFixed(1); } },
    { key: 'scarce_share_boost', label: '稀缺分享', hint: '丰饶<1 分享放大', min: 0, max: 4, step: 0.1, fmt: function (v) { return v.toFixed(1); } },
    { key: 'same_pop_share_bias', label: '同队分享', hint: '0~1 优先同队', min: 0, max: 1, step: 0.05, fmt: function (v) { return v.toFixed(2); } },
    { key: 'sexual_selection_strength', label: '性选择', hint: '择偶×choosiness', min: 0, max: 3, step: 0.1, fmt: function (v) { return v.toFixed(1); } },
    { key: 'freq_dep_strength', label: '稀有利', hint: '负频率依赖 skill', min: 0, max: 2, step: 0.05, fmt: function (v) { return v.toFixed(2); } },
    { key: 'epistasis_strength', label: '技能协同', hint: '上位/组合加成', min: 0, max: 1, step: 0.05, fmt: function (v) { return v.toFixed(2); } },
  ];
  var _agentDefs = [
    { key: 'senescence_rate', label: '衰老率', hint: 'Agent 侧 μ×age', min: 0, max: 0.02, step: 0.001, fmt: function (v) { return v.toFixed(3); } },
  ];
  var _knobDefs = _habitatDefs.concat(_pressureDefs).concat(_agentDefs);
  var _knobSyncing = false;
  var _knobsBound = false;

  function _findDef(key) {
    for (var i = 0; i < _knobDefs.length; i++) if (_knobDefs[i].key === key) return _knobDefs[i];
    return null;
  }
  function _valueToAngle(v, min, max) {
    var t = (Number(v) - min) / (max - min || 1);
    t = Math.max(0, Math.min(1, t));
    return -135 + t * 270;
  }
  function _angleToValue(angle, min, max, step) {
    var t = (angle + 135) / 270;
    t = Math.max(0, Math.min(1, t));
    var raw = min + t * (max - min);
    if (step > 0) raw = Math.round(raw / step) * step;
    // 0/1 开关取整
    if (step === 1 && max === 1 && min === 0) raw = raw >= 0.5 ? 1 : 0;
    return Math.max(min, Math.min(max, raw));
  }
  function _pointerEventAngle(el, clientX, clientY) {
    var r = el.getBoundingClientRect();
    var cx = r.left + r.width / 2;
    var cy = r.top + r.height / 2;
    var deg = Math.atan2(clientY - cy, clientX - cx) * 180 / Math.PI + 90;
    if (deg > 180) deg -= 360;
    if (deg < -180) deg += 360;
    return Math.max(-135, Math.min(135, deg));
  }
  function _dialHtml(d) {
    return '<div class="eco-dial-wrap" data-key="' + d.key + '" title="' + d.key + ' · ' + (d.hint || '') + '">'
      + '<div class="eco-dial" role="slider" tabindex="0" aria-label="' + d.label + ' (' + d.key + ')"'
      + ' aria-valuemin="' + d.min + '" aria-valuemax="' + d.max + '">'
      + '<div class="eco-dial-ticks"></div>'
      + '<div class="eco-dial-pointer"></div>'
      + '<div class="eco-dial-cap"></div>'
      + '</div>'
      + '<div class="eco-dial-label">' + d.label + '</div>'
      + '<div class="eco-dial-val">—</div>'
      + '<div class="eco-dial-key">' + d.key + '</div>'
      + '</div>';
  }
  function _paintKnob(wrap) {
    if (!wrap) return;
    var key = wrap.getAttribute('data-key');
    var def = _findDef(key);
    if (!def) return;
    var v = _knobState[key];
    var angle = _valueToAngle(v, def.min, def.max);
    var fill = (angle + 135) / 270;
    var dial = wrap.querySelector('.eco-dial');
    var valEl = wrap.querySelector('.eco-dial-val');
    if (dial) {
      dial.style.setProperty('--angle', angle + 'deg');
      dial.style.setProperty('--fill', String(fill));
    }
    if (valEl) valEl.textContent = def.fmt(v);
  }
  function _paintAllKnobs() {
    var panel = $('lp-eco-knobs');
    if (!panel) return;
    panel.querySelectorAll('.eco-dial-wrap').forEach(function (w) { _paintKnob(w); });
  }
  function _renderLeftKnobs() {
    var panel = $('lp-eco-knobs');
    var gHab = $('lp-knobs-habitat');
    var gPr = $('lp-knobs-pressure');
    var gAg = $('lp-knobs-agent');
    if (!panel) return;
    var show = !!(window.__ECO_FIELD__ || document.body.classList.contains('office-mode')
      || (document.getElementById('rp-eco') && document.getElementById('rp-eco').style.display !== 'none'));
    panel.style.display = show ? 'block' : 'none';
    if (!show) return;
    if (gHab && !gHab.dataset.built) {
      gHab.innerHTML = _habitatDefs.map(_dialHtml).join('');
      gHab.dataset.built = '1';
    }
    if (gPr && !gPr.dataset.built) {
      gPr.innerHTML = _pressureDefs.map(_dialHtml).join('');
      gPr.dataset.built = '1';
    }
    if (gAg && !gAg.dataset.built) {
      gAg.innerHTML = _agentDefs.map(_dialHtml).join('');
      gAg.dataset.built = '1';
    }
    if (!_knobsBound) {
      _bindLeftKnobs(panel);
      _knobsBound = true;
    }
    // 兼容旧标记
    var legacy = $('lp-knobs-grid');
    if (legacy) legacy.dataset.built = '1';
    _paintAllKnobs();
  }
  function _bindLeftKnobs(root) {
    root.querySelectorAll('.eco-dial').forEach(function (dial) {
      var wrap = dial.parentElement;
      var key = wrap.getAttribute('data-key');
      var def = _findDef(key);
      if (!def) return;
      var dragging = false;
      function applyFromEvent(e) {
        var cx = e.touches ? e.touches[0].clientX : e.clientX;
        var cy = e.touches ? e.touches[0].clientY : e.clientY;
        var angle = _pointerEventAngle(dial, cx, cy);
        _knobState[key] = _angleToValue(angle, def.min, def.max, def.step);
        _paintKnob(wrap);
        _syncKnobsToRightSliders();
      }
      dial.addEventListener('pointerdown', function (e) {
        dragging = true;
        dial.setPointerCapture(e.pointerId);
        applyFromEvent(e);
        e.preventDefault();
      });
      dial.addEventListener('pointermove', function (e) {
        if (!dragging) return;
        applyFromEvent(e);
      });
      dial.addEventListener('pointerup', function () {
        if (!dragging) return;
        dragging = false;
        window.eco2SaveEnv();
      });
      dial.addEventListener('keydown', function (e) {
        var delta = 0;
        if (e.key === 'ArrowRight' || e.key === 'ArrowUp') delta = def.step;
        if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') delta = -def.step;
        if (!delta) return;
        e.preventDefault();
        _knobState[key] = Math.max(def.min, Math.min(def.max, Number(_knobState[key]) + delta));
        if (def.step === 1 && def.max === 1) _knobState[key] = Math.round(_knobState[key]);
        _paintKnob(wrap);
        _syncKnobsToRightSliders();
        window.eco2SaveEnv();
      });
    });
    var bp = $('lp-knob-pressure');
    if (bp) bp.onclick = function () { window.eco2ApplyPressureKnobs(); };
    var bl = $('lp-knob-loose');
    if (bl) bl.onclick = function () { window.eco2ApplyLooseKnobs(); };
    var bs = $('lp-knob-save');
    if (bs) bs.onclick = function () { window.eco2SaveEnv(); };
  }
  // 右侧 Darwin 扩展滑杆：raw → 真实值（与 HTML min/max 对齐）
  // sexual 0~30 → /10；freqdep 0~40 → /20；epistasis 0~20 → /20；senescence 0~20 → /1000
  function _setDarwinSlidersFromState() {
    _setSlider('eco2-env-sexual', Math.round(Number(_knobState.sexual_selection_strength || 0) * 10), 10);
    _setSlider('eco2-env-freqdep', Math.round(Number(_knobState.freq_dep_strength || 0) * 20), 20);
    _setSlider('eco2-env-epistasis', Math.round(Number(_knobState.epistasis_strength || 0) * 20), 20);
    _setSlider('eco2-env-senescence', Math.round(Number(_knobState.senescence_rate || 0) * 1000), 1000);
  }
  function _readDarwinSlidersToState() {
    var sx = $('eco2-env-sexual'), fd = $('eco2-env-freqdep'), ep = $('eco2-env-epistasis'), se = $('eco2-env-senescence');
    if (sx) _knobState.sexual_selection_strength = Number(sx.value) / 10;
    if (fd) _knobState.freq_dep_strength = Number(fd.value) / 20;
    if (ep) _knobState.epistasis_strength = Number(ep.value) / 20;
    if (se) _knobState.senescence_rate = Number(se.value) / 1000;
  }
  function _syncKnobsToRightSliders() {
    if (_knobSyncing) return;
    _knobSyncing = true;
    try {
      _setSlider('eco2-env-predator', Math.round(_knobState.predator_pressure * 100), 100);
      _setSlider('eco2-env-abundance', Math.round(_knobState.abundance * 100), 100);
      _setSlider('eco2-env-drift', Math.round(_knobState.drift_prob * 100), 100);
      _setSlider('eco2-env-capacity', Math.round(_knobState.niche_capacity), 1);
      _setDarwinSlidersFromState();
    } finally {
      _knobSyncing = false;
    }
  }
  function _syncRightSlidersToKnobs() {
    if (_knobSyncing) return;
    var p = $('eco2-env-predator'), a = $('eco2-env-abundance'), d = $('eco2-env-drift'), c = $('eco2-env-capacity');
    if (p) _knobState.predator_pressure = Number(p.value) / 100;
    if (a) _knobState.abundance = Number(a.value) / 100;
    if (d) _knobState.drift_prob = Number(d.value) / 100;
    if (c) _knobState.niche_capacity = Number(c.value);
    _readDarwinSlidersToState();
    _paintAllKnobs();
  }
  window.eco2ApplyPressureKnobs = function () {
    // 与 pet-config applyEvolutionPressurePreset 同口径
    Object.assign(_knobState, {
      abundance: 0.6,
      predator_pressure: 0.15,
      drift_prob: 0.18,
      niche_capacity: 3,
      skill_idle_penalty: 1.5,
      genome_carry_cost: 0.1,
      min_steps_when_contract: 72,
      min_gens_when_contract: 5,
      prefer_forage_when_can_serve: 1,
      predator_bias_unskilled: 2.5,
      scarce_share_boost: 1.5,
      same_pop_share_bias: 0.75,
      sexual_selection_strength: 1.2,
      freq_dep_strength: 0.6,
      epistasis_strength: 0.25,
      senescence_rate: 0.004,
    });
    _syncKnobsToRightSliders();
    _paintAllKnobs();
    window.eco2SaveEnv();
    setText('lp-knobs-status', '· 已加压(A+B+C)');
    setText('eco2-env-status', '· 加压预设已写回');
  };
  window.eco2ApplyLooseKnobs = function () {
    Object.assign(_knobState, {
      abundance: 1.2,
      predator_pressure: 0.04,
      drift_prob: 0.1,
      niche_capacity: 0,
      skill_idle_penalty: 0,
      genome_carry_cost: 0.05,
      min_steps_when_contract: 40,
      min_gens_when_contract: 2,
      prefer_forage_when_can_serve: 0,
      predator_bias_unskilled: 0,
      scarce_share_boost: 0,
      same_pop_share_bias: 0,
      sexual_selection_strength: 0,
      freq_dep_strength: 0,
      epistasis_strength: 0,
      senescence_rate: 0,
    });
    _syncKnobsToRightSliders();
    _paintAllKnobs();
    window.eco2SaveEnv();
    setText('lp-knobs-status', '· 宽松');
  };

  // 读配置 → 右侧滑杆 + 左 A/B 旋钮（字段一一回填）
  window.ecoLoadConfig = function () {
    _fetch('/api/v1/eco-runtime/config').then(function (r) { return r.json ? r.json() : r; })
      .then(function (cfg) {
        if (!cfg) return;
        var hab = cfg.habitat || {};
        var evo = cfg.evolution_pressure || {};
        var econ = cfg.drill_economics || {};
        var learn = cfg.learning || {};
        // A
        _knobState.predator_pressure = hab.predator_pressure != null ? Number(hab.predator_pressure) : 0.12;
        _knobState.abundance = hab.abundance != null ? Number(hab.abundance) : 0.7;
        _knobState.drift_prob = hab.drift_prob != null ? Number(hab.drift_prob) : 0.2;
        _knobState.niche_capacity = hab.niche_capacity != null ? Number(hab.niche_capacity) : 3;
        // B — 环境选择压；C — Agent 衰老（metabolism，兼容旧 evo 键）
        var metaSec = cfg.metabolism || {};
        _knobState.skill_idle_penalty = evo.skill_idle_penalty != null ? Number(evo.skill_idle_penalty)
          : (econ.skill_idle_penalty != null ? Number(econ.skill_idle_penalty) : 1.2);
        _knobState.genome_carry_cost = evo.genome_carry_cost != null ? Number(evo.genome_carry_cost)
          : (learn.genome_carry_cost != null ? Number(learn.genome_carry_cost) : 0.08);
        _knobState.min_steps_when_contract = evo.min_steps_when_contract != null ? Number(evo.min_steps_when_contract) : 64;
        _knobState.min_gens_when_contract = evo.min_gens_when_contract != null ? Number(evo.min_gens_when_contract) : 4;
        _knobState.prefer_forage_when_can_serve = evo.prefer_forage_when_can_serve != null ? Number(evo.prefer_forage_when_can_serve) : 1;
        _knobState.predator_bias_unskilled = evo.predator_bias_unskilled != null ? Number(evo.predator_bias_unskilled) : 2.0;
        _knobState.scarce_share_boost = evo.scarce_share_boost != null ? Number(evo.scarce_share_boost) : 1.2;
        _knobState.same_pop_share_bias = evo.same_pop_share_bias != null ? Number(evo.same_pop_share_bias) : 0.7;
        _knobState.sexual_selection_strength = evo.sexual_selection_strength != null ? Number(evo.sexual_selection_strength) : 1.0;
        _knobState.freq_dep_strength = evo.freq_dep_strength != null ? Number(evo.freq_dep_strength) : 0.5;
        _knobState.epistasis_strength = evo.epistasis_strength != null ? Number(evo.epistasis_strength) : 0.2;
        _knobState.senescence_rate = metaSec.senescence_rate != null ? Number(metaSec.senescence_rate)
          : (evo.senescence_rate != null ? Number(evo.senescence_rate) : 0.003);
        _setSlider('eco2-env-predator', Math.round(_knobState.predator_pressure * 100), 100);
        _setSlider('eco2-env-abundance', Math.round(_knobState.abundance * 100), 100);
        _setSlider('eco2-env-drift', Math.round(_knobState.drift_prob * 100), 100);
        _setSlider('eco2-env-capacity', _knobState.niche_capacity, 1);
        _setDarwinSlidersFromState();
        _renderLeftKnobs();
        setText('eco2-env-status', '· 环境+Agent 已加载');
        setText('lp-knobs-status', '· A4+B11+C1 已加载');
      }).catch(function () {
        setText('eco2-env-status', '· 使用默认值');
        _renderLeftKnobs();
      });
  };

  function _setSlider(id, raw, denom) {
    var el = $(id);
    if (!el) return;
    el.value = raw;
    _syncSliderVal(id, denom);
  }
  function _syncSliderVal(id, denom) {
    var el = $(id), out = $(id + '-val');
    if (!el || !out) return;
    if (denom === 1) {
      var v = Number(el.value);
      out.textContent = v === 0 ? '∞' : String(v);
    } else if (denom === 1000) {
      // 衰老率三位小数
      out.textContent = (Number(el.value) / denom).toFixed(3);
    } else if (denom === 10 || denom === 20) {
      out.textContent = (Number(el.value) / denom).toFixed(denom === 10 ? 1 : 2);
    } else {
      out.textContent = (Number(el.value) / denom).toFixed(2).replace(/0$/, '');
    }
  }
  function _bindSliders() {
    ['eco2-env-predator', 'eco2-env-abundance', 'eco2-env-drift'].forEach(function (id) {
      var el = $(id);
      if (el) el.addEventListener('input', function () {
        _syncSliderVal(id, 100);
        _syncRightSlidersToKnobs();
      });
    });
    var cap = $('eco2-env-capacity');
    if (cap) cap.addEventListener('input', function () {
      _syncSliderVal('eco2-env-capacity', 1);
      _syncRightSlidersToKnobs();
    });
    // Darwin 扩展四滑杆（右侧压力台可见）
    var darwinBind = [
      ['eco2-env-sexual', 10],
      ['eco2-env-freqdep', 20],
      ['eco2-env-epistasis', 20],
      ['eco2-env-senescence', 1000],
    ];
    darwinBind.forEach(function (pair) {
      var id = pair[0], den = pair[1];
      var el = $(id);
      if (el) el.addEventListener('input', function () {
        _syncSliderVal(id, den);
        _syncRightSlidersToKnobs();
      });
    });
  }

  // 环境剧本预设：一键组合「物竞（名额/丰饶）× 天择（捕食/漂移）」强度
  var ECO_SCENARIOS = {
    mild:     { predator: 2,  abundance: 150, drift: 10, capacity: 0 },
    harsh:    { predator: 15, abundance: 70,  drift: 30, capacity: 2 },
    upheaval: { predator: 10, abundance: 100, drift: 80, capacity: 3 },
    armsrace: { predator: 25, abundance: 90,  drift: 50, capacity: 1 },
  };
  window.eco2ApplyScenario = function (name, btn) {
    var s = ECO_SCENARIOS[name];
    if (!s) return;
    _setSlider('eco2-env-predator', s.predator, 100);
    _setSlider('eco2-env-abundance', s.abundance, 100);
    _setSlider('eco2-env-drift', s.drift, 100);
    _setSlider('eco2-env-capacity', s.capacity, 1);
    _syncRightSlidersToKnobs();
    window.eco2SaveEnv();
    setText('eco2-env-status', '· 剧本已应用并写回');
    // 选中态持久化（不受 :focus 丢失影响）
    if (btn) {
      var prev = btn.parentElement.querySelectorAll('.eco2-scenario-active');
      prev.forEach(function (el) { el.classList.remove('eco2-scenario-active'); });
      btn.classList.add('eco2-scenario-active');
    }
  };

  // 环境压力台 / 左侧旋钮 → 写回 habitat(A4) + evolution_pressure(B12 全量)
  window.eco2SaveEnv = function () {
    // 始终从右侧滑杆回填 A + Darwin（右侧是用户最常改的入口）
    if ($('eco2-env-predator')) {
      _knobState.predator_pressure = Number($('eco2-env-predator').value) / 100;
      _knobState.abundance = Number($('eco2-env-abundance').value) / 100;
      _knobState.drift_prob = Number($('eco2-env-drift').value) / 100;
      _knobState.niche_capacity = Number(($('eco2-env-capacity') || { value: 2 }).value);
      _readDarwinSlidersToState();
    }
    var body = {
      habitat: {
        predator_pressure: Number(_knobState.predator_pressure),
        abundance: Number(_knobState.abundance),
        drift_prob: Number(_knobState.drift_prob),
        niche_capacity: Number(_knobState.niche_capacity),
      },
      evolution_pressure: {
        skill_idle_penalty: Number(_knobState.skill_idle_penalty),
        genome_carry_cost: Number(_knobState.genome_carry_cost),
        min_steps_when_contract: Math.round(Number(_knobState.min_steps_when_contract)),
        min_gens_when_contract: Math.round(Number(_knobState.min_gens_when_contract)),
        prefer_forage_when_can_serve: Math.round(Number(_knobState.prefer_forage_when_can_serve)) ? 1 : 0,
        predator_bias_unskilled: Number(_knobState.predator_bias_unskilled),
        scarce_share_boost: Number(_knobState.scarce_share_boost),
        same_pop_share_bias: Number(_knobState.same_pop_share_bias),
        sexual_selection_strength: Number(_knobState.sexual_selection_strength),
        freq_dep_strength: Number(_knobState.freq_dep_strength),
        epistasis_strength: Number(_knobState.epistasis_strength),
      },
      // Agent 侧生命史（与环境加压分离）
      metabolism: {
        senescence_rate: Number(_knobState.senescence_rate),
      },
      // 生产路径会读 drill_economics.skill_idle 与 learning.genome_carry — 与 B 同步
      drill_economics: {
        skill_idle_penalty: Number(_knobState.skill_idle_penalty),
      },
      learning: {
        genome_carry_cost: Number(_knobState.genome_carry_cost),
      },
    };
    _fetch('/api/v1/eco-runtime/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(function (r) {
      var ok = r && r.ok !== false;
      setText('eco2-env-status', ok ? '· ✓ A+B+C 已写回' : '· 写回失败');
      setText('lp-knobs-status', ok ? '· ✓ A+B+C 已写回' : '· 失败');
    }).catch(function () {
      setText('eco2-env-status', '· 写回失败');
      setText('lp-knobs-status', '· 失败');
    });
  };

  // 无任务时：压力台不展示团队技能清单（那不是「环境 demand」）；提示去挂任务
  function _loadNichesFromTeam() {
    if (_boundContract && (_boundContract.niches || []).length) {
      _renderEnvDemandChips(_boundContract.niches);
      return;
    }
    var teamId = window._selectedTeamId;
    if (!teamId) {
      _clearEnvDemandChips('挂任务后显示 demand skills…');
      return;
    }
    _clearEnvDemandChips('已选种群 · 挂任务后显示 demand skills…');
  }

  // 团队选中联动（secs-core 的 sexyPickTeam 会更新 window._selectedTeamName）
  setInterval(function () {
    var btn = $('eco2-run-team');
    if (btn && window._selectedTeamName && btn.textContent.indexOf(window._selectedTeamName) === -1) {
      btn.textContent = '👥 ① 种群：' + window._selectedTeamName;
      _loadNichesFromTeam();
      _syncPrimaryTaskMount(true);
      // 换了种群 → 释放回放保护，恢复 office-boot 团队轮询（3D 显示新团队成员）
      window.__ECO_REPLAY_ACTIVE__ = false;
      if (_replay) { _replay.pause(); }
    }
    // 已有种群但挂载区未显示时补一次
    if (window._selectedTeamId) _syncPrimaryTaskMount(false);
    // v3: 主队策略选择器渲染（多队对抗模式可见）
    var psRow = $('eco2-primary-strategy-row');
    var psBox = $('eco2-primary-strategy');
    if (psRow && psBox && window._selectedTeamId) {
      psRow.style.display = (_raceMode === 'confrontation') ? 'flex' : 'none';
      if (psBox.getAttribute('data-tid') !== window._selectedTeamId) {
        psBox.setAttribute('data-tid', window._selectedTeamId);
        psBox.innerHTML = _strategySelectHtml(window._selectedTeamId);
      }
    } else if (psRow) {
      psRow.style.display = 'none';
    }
  }, 1500);

  // ═══ v2.3/XG-12 多种群：对比种群 + 可选挂接任务（同计划=apple-to-apple） ═══
  // [{id,name,task_id,task_title,plan_id,tasks:[{task_id,title,plan_id}]}]
  var _rivalTeams = [];
  var _pickingRival = false;
  var _prevPrimary = null;
  // v3: 每队排兵策略选择（team_id -> strategy_id，默认 head_on）
  var _teamStrategies = {};    // {team_id: 'head_on'}
  function _getTeamStrategy(tid) {
    return _teamStrategies[tid] || 'head_on';
  }
  function _setTeamStrategy(tid, sid) {
    _teamStrategies[tid] = sid;
  }
  // 生成策略下拉 HTML
  function _strategySelectHtml(tid) {
    var current = _getTeamStrategy(tid);
    var strategies = window.listMatchupStrategies ? window.listMatchupStrategies() : [];
    var opts = strategies.map(function (s) {
      return '<option value="' + esc(s.id) + '"' + (s.id === current ? ' selected' : '') + '>'
        + esc(s.icon || '') + ' ' + esc(s.name) + '</option>';
    }).join('');
    return '<select onchange="eco2SetTeamStrategy(\'' + esc(tid) + '\', this.value)" '
      + 'style="font-size:9px;padding:1px 3px;border:1px solid var(--border);border-radius:3px;background:var(--bg);color:var(--text)">' + opts + '</select>';
  }
  window.eco2SetTeamStrategy = function (tid, sid) {
    _setTeamStrategy(tid, sid);
  };

  function _taskPlanId(t) {
    if (!t) return '';
    var m = t.metadata || {};
    return m.plan_id || t.plan_id || '';
  }

  function _loadRivalTasks(teamId) {
    return _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(teamId) + '/tasks')
      .then(function (r) { return r.json ? r.json() : r; })
      .then(function (list) {
        var arr = Array.isArray(list) ? list : (list && (list.tasks || list.items || list.data)) || [];
        return arr.map(function (t) {
          return {
            task_id: t.task_id || t.id,
            title: t.title || t.name || (t.task_id || t.id),
            plan_id: _taskPlanId(t),
            status: t.status || '',
            raw: t,
          };
        }).filter(function (t) { return t.task_id; });
      })
      .catch(function () { return []; });
  }

  /** 用户为对比种群选任务：不选=随机比较；选相同/相似 plan=apple-to-apple */
  window.eco2SetRivalTask = function (teamId, taskId) {
    var rival = _rivalTeams.find(function (t) { return t.id === teamId; });
    if (!rival) return;
    if (!taskId) {
      rival.task_id = '';
      rival.task_title = '';
      rival.plan_id = '';
      _syncComparisonBanner();
      _renderRivalChips();
      return;
    }
    var hit = (rival.tasks || []).find(function (x) { return x.task_id === taskId; });
    rival.task_id = taskId;
    rival.task_title = hit ? hit.title : taskId;
    rival.plan_id = hit ? (hit.plan_id || '') : '';
    // 若主队尚未挂任务，且对比队选了任务 → 可提示 apple-to-apple
    _syncComparisonBanner();
    _renderRivalChips();
    // 尝试自动对齐主任务：对比任务与主任务同 plan 时刷新状态
    if (hit && hit.plan_id && _boundTask && _taskPlanId(_boundTask) === hit.plan_id) {
      setText('eco2-run-status',
        '🍎 Apple-to-apple：主队与「' + esc(rival.name) + '」挂接同一执行计划 ' + esc(hit.plan_id) +
        ' — 共用考卷，比 skill/协作');
    } else if (hit && !_boundTask) {
      setText('eco2-run-status',
        '对比队「' + esc(rival.name) + '」已选任务「' + esc(rival.task_title) +
        '」。建议主种群也挂接相同/相似任务以便公平比较');
    }
  };

  function _primaryPlanId() {
    if (_boundContract && _boundContract.plan_id) return _boundContract.plan_id;
    if (_boundTask) return _taskPlanId(_boundTask);
    return '';
  }

  function _syncComparisonBanner() {
    var el = $('eco2-compare-banner');
    if (!el) return;
    if (!_rivalTeams.length) {
      el.style.display = 'none';
      el.textContent = '';
      return;
    }
    var pPlan = _primaryPlanId();
    var withTask = _rivalTeams.filter(function (r) { return r.task_id; });
    var samePlan = pPlan && withTask.filter(function (r) { return r.plan_id && r.plan_id === pPlan; });
    var parts = [];
    parts.push('对比 ' + _rivalTeams.length + ' 队');
    if (!_boundTask && !withTask.length) {
      parts.push('未挂任务 → 随机生境比较（仅比队内基因，无统一考卷）');
    } else if (samePlan && samePlan.length === withTask.length && withTask.length) {
      parts.push('🍎 同计划 ' + pPlan + ' → Apple-to-apple（共用步数/生态位，比 skill+协作）');
    } else if (withTask.length) {
      parts.push('已选任务 ' + withTask.length + '/' + _rivalTeams.length +
        '（同 plan 才算严格公平；否则用主任务考卷或技能并集）');
    } else {
      parts.push('对比队未选任务 → 共用主任务考卷' + (pPlan ? ' plan=' + pPlan : ''));
    }
    el.style.display = 'block';
    el.textContent = parts.join(' · ');
  }

  // 包装 sexySelectTeam：处于"选对比种群"模式时截获选择，不改主种群
  var _wrapTimer = setInterval(function () {
    if (typeof window.sexySelectTeam !== 'function' || window.sexySelectTeam.__ecoWrapped) return;
    var orig = window.sexySelectTeam;
    window.sexySelectTeam = function (teamId, teamName) {
      if (_pickingRival) {
        _pickingRival = false;
        if (teamId && teamId !== window._selectedTeamId
            && !_rivalTeams.some(function (t) { return t.id === teamId; })) {
          var entry = {
            id: teamId,
            name: teamName || teamId,
            task_id: '',
            task_title: '',
            plan_id: '',
            tasks: [],
          };
          _rivalTeams.push(entry);
          _loadTeamSkills(teamId);
          // 不自动改赛制：分场也可多队比 skill；多队对抗比协作策略——由用户自选
          // 拉取该队任务列表，供下拉选择（同计划任务 → 同一客观环境）
          _loadRivalTasks(teamId).then(function (tasks) {
            entry.tasks = tasks || [];
            // 若主任务有 plan_id，自动预选同 plan 的首个任务
            var pPlan = _primaryPlanId();
            if (pPlan) {
              var same = entry.tasks.find(function (x) { return x.plan_id === pPlan; });
              if (same) {
                entry.task_id = same.task_id;
                entry.task_title = same.title;
                entry.plan_id = same.plan_id;
              }
            }
            _renderRivalChips();
            _syncComparisonBanner();
            _previewMultiPopRoster();
          });
        }
        _renderRivalChips();
        _syncComparisonBanner();
        _previewMultiPopRoster();
        if (_prevPrimary) {
          window._selectedTeamId = _prevPrimary.id;
          window._selectedTeamName = _prevPrimary.name;
        }
        var ov = document.getElementById('o-team');
        if (ov) ov.style.display = 'none';
        window._teamModalOpen = false;
        return;
      }
      var ret = orig(teamId, teamName);
      // 主种群选定后：打开任务挂载菜单（XF-6）
      try {
        if (teamId && typeof _setTeamUi === 'function') {
          // orig 可能已设 _selectedTeamId；确保挂载区刷新
          _syncPrimaryTaskMount(true);
          _loadNichesFromTeam();
        }
      } catch (eMount) { /* ignore */ }
      return ret;
    };
    window.sexySelectTeam.__ecoWrapped = true;
    clearInterval(_wrapTimer);
  }, 800);

  window.eco2AddRivalTeam = function () {
    _prevPrimary = window._selectedTeamId
      ? { id: window._selectedTeamId, name: window._selectedTeamName } : null;
    _pickingRival = true;
    if (window.sexyPickTeam) window.sexyPickTeam();
  };
  window.eco2RemoveRival = function (tid) {
    _rivalTeams = _rivalTeams.filter(function (t) { return t.id !== tid; });
    _renderRivalChips();
    _syncComparisonBanner();
    if (_rivalTeams.length) _previewMultiPopRoster();
    else {
      var box = $('eco2-pop-list');
      if (box) box.innerHTML = '<div class="eco2-empty">投放种群后，这里将显示每个生物的血量、意图与双基因（技能 + 协作倾向）。</div>';
      setText('eco2-pop-status', '');
    }
  };

  function _rivalTaskSelectHtml(t) {
    var opts = '<option value="">（不选=随机比较）</option>';
    (t.tasks || []).forEach(function (tk) {
      var label = tk.title + (tk.plan_id ? ' · plan:' + String(tk.plan_id).slice(0, 8) : '');
      if (tk.status) label += ' [' + tk.status + ']';
      opts += '<option value="' + esc(tk.task_id) + '"' +
        (tk.task_id === t.task_id ? ' selected' : '') + '>' + esc(label) + '</option>';
    });
    if (!(t.tasks || []).length) {
      opts += '<option value="" disabled>该队暂无任务</option>';
    }
    return '<select onchange="eco2SetRivalTask(\'' + esc(t.id) + '\', this.value)" '
      + 'title="选相同/相似执行计划任务 → 公平比 skill/协作；不选 → 随机生境"'
      + ' style="max-width:200px;font-size:9px;padding:2px 4px;border:1px solid var(--border);border-radius:3px;background:var(--bg);color:var(--text)">'
      + opts + '</select>';
  }

  function _renderRivalChips() {
    var box = $('eco2-rival-chips');
    if (!box) return;
    if (!_rivalTeams.length) {
      box.innerHTML = '<span style="color:var(--dim);font-size:9px">（单种群——加入对比种群后可为每队选择相同/相似任务做 Apple-to-apple）</span>';
      return;
    }
    box.innerHTML = _rivalTeams.map(function (t) {
      var taskHint = t.task_id
        ? '<span style="color:var(--purple);font-size:9px">📋 ' + esc((t.task_title || t.task_id).slice(0, 28)) + '</span>'
        : '<span style="color:var(--dim);font-size:9px">🎲 未选任务</span>';
      var apple = '';
      var pPlan = _primaryPlanId();
      if (t.task_id && pPlan && t.plan_id === pPlan) {
        apple = ' <span style="color:var(--amber);font-size:9px" title="与主任务同执行计划">🍎</span>';
      }
      return '<div class="eco2-chip" style="display:flex;flex-direction:column;align-items:flex-start;gap:3px;padding:6px 8px;min-width:180px">'
        + '<div style="display:flex;align-items:center;gap:6px;width:100%">'
        + '<b style="font-size:11px">' + esc(t.name) + '</b>' + apple
        + ' ' + _strategySelectHtml(t.id)
        + ' <a href="javascript:void(0)" onclick="eco2RemoveRival(\'' + esc(t.id) + '\')" style="color:#f87171;text-decoration:none;margin-left:auto">✕</a>'
        + '</div>'
        + '<div style="display:flex;align-items:center;gap:4px;width:100%">'
        + '<span style="font-size:9px;color:var(--dim);flex-shrink:0">任务</span>'
        + _rivalTaskSelectHtml(t)
        + '</div>'
        + taskHint
        + '</div>';
    }).join('');
  }

  // ═══ 开始物竞天择（覆盖旧版 ecoRunDrill） ═══
  // 赛制（用户校准）：①分场=多队Agent比个体skill；②多队对抗=协作+策略；③混合=个体+团队
  // 加对比种群不自动改赛制。旧别名 tournament→division, melee→confrontation
  var _raceMode = 'division';
  var _tournament = null;   // {entries:[{id,name,result}], done:bool}
  var _genView = 'qoq';     // XV-5: 世代曲线视图 qoq|yoy|composite
  // 世界杯隐喻：①球星评比 ②球队协作对决 ③世界杯（球星+协作，奖杯只有一座=客观环境）
  var _RACE_HINTS = {
    division: '① 分场·球星评比——各队 Agent 比个体 skill（同一任务环境过滤谁更合适）',
    confrontation: '② 多队·球队对决——比团队协作与排兵策略（需对比种群）',
    mixed: '③ 混合·世界杯——球星 skill + 球队协作一起经受客观环境（奖杯只有一座）',
  };
  window.eco2SetRaceMode = function (m) {
    // 旧别名映射（防外部调用断裂）
    if (m === 'tournament') m = 'division';
    else if (m === 'melee') m = 'confrontation';
    _raceMode = (m === 'confrontation' || m === 'mixed') ? m : 'division';
    // 释义已收到 radio title；不再占底部长文案
    var hintEl = $('eco2-race-hint');
    if (hintEl) {
      hintEl.textContent = '';
      hintEl.setAttribute('data-hint', _RACE_HINTS[_raceMode] || '');
    }
    // 同步 radio UI
    try {
      var radios = document.querySelectorAll('input[name="eco2-race-mode"]');
      radios.forEach(function (r) { r.checked = (r.value === _raceMode); });
    } catch (e) { /* ignore */ }
    // v3: 多队对抗模式才显示策略选择器
    var psRow = $('eco2-primary-strategy-row');
    if (psRow) psRow.style.display = (_raceMode === 'confrontation') ? 'flex' : 'none';
    _previewMultiPopRoster();
  };

  /** 分场/多队/混合：有对比队时预览各方 Agent（分场也是多队比 skill） */
  function _previewMultiPopRoster() {
    if (!window._selectedTeamId) return;
    var ids = [window._selectedTeamId];
    var names = [window._selectedTeamName || window._selectedTeamId];
    _rivalTeams.forEach(function (r) {
      ids.push(r.id);
      names.push(r.name);
    });
    _loadTeamAgentsPreview(ids, names);
  }

  function _loadTeamAgentsPreview(teamIds, teamNames) {
    var box = $('eco2-pop-list');
    if (!box) return;
    var status = $('eco2-pop-status');
    if (status) status.textContent = '· 预览入场名单（开跑后按生存刷新）';
    box.innerHTML = '<div class="eco2-empty">加载两队 Agent…</div>';
    var fetches = teamIds.map(function (tid) {
      return _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(tid))
        .then(function (r) { return r.json ? r.json() : r; })
        .then(function (d) {
          var agents = [];
          if (d && d.agents) {
            agents = Array.isArray(d.agents) ? d.agents : Object.values(d.agents);
          }
          return { teamId: tid, agents: agents };
        })
        .catch(function () { return { teamId: tid, agents: [] }; });
    });
    Promise.all(fetches).then(function (groups) {
      var html = '';
      var total = 0;
      groups.forEach(function (g, i) {
        var label = teamNames[i] || g.teamId;
        var agents = g.agents || [];
        total += agents.length;
        html += '<div style="padding:4px 2px;margin-top:4px;font-size:10px;font-weight:700;color:var(--cyan);border-bottom:1px solid var(--border)">'
          + '🏳️ ' + esc(label) + ' <span style="font-weight:400;color:var(--dim)">(' + esc(g.teamId) + ') · ' + agents.length + ' 人</span></div>';
        if (!agents.length) {
          html += '<div class="eco2-empty" style="padding:4px">（该队无 Agent）</div>';
          return;
        }
        agents.forEach(function (a) {
          var aid = a.agent_id || a.id || '';
          var nm = a.name || aid;
          var skills = (a.skills || []).slice(0, 4).map(function (s) {
            return '<span class="eco2-chip">' + esc(_sk(String(s)).slice(0, 12)) + '</span>';
          }).join(' ');
          html += '<div class="eco2-pop-row">'
            + '<span style="width:14px;text-align:center">·</span>'
            + '<span class="eco2-pop-name" title="' + esc(aid) + '">' + esc(nm) + '</span>'
            + '<span style="flex:1;overflow:hidden;font-size:9px;color:var(--dim)">' + (skills || '—') + '</span>'
            + '</div>';
        });
      });
      box.innerHTML = html || '<div class="eco2-empty">（无 Agent）</div>';
      if (status) {
        var modeHint = _raceMode === 'division' ? '分场：比个体 skill'
          : _raceMode === 'confrontation' ? '多队对抗：比协作/策略'
          : '混合：个体+团队';
        status.textContent = '· 预览 ' + groups.length + ' 队 / ' + total + ' 人 · ' + modeHint
          + (groups.length > 1 ? '（开跑后各方 Agent 均入场）' : '');
      }
    });
  }

  // XV-5: 世代曲线三比切换
  window.eco2SetGenView = function (v) {
    _genView = (v === 'yoy' || v === 'composite') ? v : 'qoq';
    // 更新 tab 高亮
    ['qoq', 'yoy', 'composite'].forEach(function (t) {
      var btn = $('eco2-gen-tab-' + t);
      if (btn) {
        if (t === _genView) {
          btn.style.background = 'var(--cyan)'; btn.style.color = '#fff';
        } else {
          btn.style.background = ''; btn.style.color = '';
        }
      }
    });
    if (_lastResult) _renderGenerations(_lastResult.generations || []);
  };

  /**
   * 解析多队任务对齐：
   * - 有主任务/同 plan 对比任务 → 共用一份考卷（步数/生态位），比 skill+协作
   * - 全不选任务 → 无 contract，随机生境
   */
  function _resolveSharedExam() {
    var pPlan = _primaryPlanId();
    var rivalsWithTask = _rivalTeams.filter(function (r) { return r.task_id; });
    var apple = [];
    if (pPlan) {
      apple = rivalsWithTask.filter(function (r) { return r.plan_id === pPlan; });
    }
    return {
      mode: (!_boundTask && !rivalsWithTask.length) ? 'random'
        : (pPlan && apple.length === rivalsWithTask.length && (_boundTask || apple.length)) ? 'apple'
        : (_boundContract || _boundTask) ? 'primary_exam'
        : 'random',
      plan_id: pPlan,
      apple_rivals: apple,
      rival_bindings: _rivalTeams.map(function (r) {
        return {
          team_id: r.id,
          team_name: r.name,
          task_id: r.task_id || '',
          task_title: r.task_title || '',
          plan_id: r.plan_id || '',
        };
      }),
    };
  }

  function _createAndRunDrill(teamId, extraIds, maxSteps, maxGens, opts) {
    opts = opts || {};
    var exam = _resolveSharedExam();
    var goalName = '物竞天择-' + Date.now().toString(36);
    if (_boundContract && _boundContract.plan_id) {
      goalName = '物竞-' + (_boundContract.topic || _boundContract.plan_id).slice(0, 40);
    } else if (_boundTask) {
      goalName = '物竞·' + (_boundTask.title || _boundTask.task_id || '').slice(0, 40);
    }
    // 步数/世代：有统一考卷时优先契约预算（用户未手改时）
    if (!_budgetOverridden && _boundContract && _boundContract.step_budget) {
      var sb = _boundContract.step_budget;
      if (sb.max_steps_per_generation) maxSteps = sb.max_steps_per_generation;
      if (sb.max_generations) maxGens = sb.max_generations;
    }
    // 多队对抗：参数 > URL/session 缓存
    var resolvedExtra = extraIds || [];
    if ((!resolvedExtra || !resolvedExtra.length) && typeof window.eco2GetExtraTeamIds === 'function') {
      resolvedExtra = window.eco2GetExtraTeamIds() || [];
    }
    if ((!resolvedExtra || !resolvedExtra.length) && window.__ECO_EXTRA_TEAM_IDS__) {
      resolvedExtra = window.__ECO_EXTRA_TEAM_IDS__;
    }
    var body = {
        team_id: teamId,
        mode: 'evolutionary',
        max_steps: maxSteps,
        max_generations: maxGens || 3,
        drill_kind: 'natural_selection',
        task_goal: {
          name: goalName,
          extra_team_ids: resolvedExtra || [],
          comparison_mode: exam.mode,
          rival_task_bindings: exam.rival_bindings,
        },
    };
    // 有考卷（主任务或 apple）→ 带 contract；纯随机不带
    if (exam.mode !== 'random' && _boundContract) {
      body.task_goal.contract = _boundContract;
      body.task_goal.plan_id = _boundContract.plan_id || exam.plan_id || '';
    } else if (exam.mode === 'random') {
      // 明确不带 contract，后端走团队技能并集随机生境
      body.task_goal.random_habitat = true;
    }
    // XG-11: 溯源已挂接任务
    if (_boundTask) {
      body.task_goal.task_id = _boundTask.task_id || _boundTask.id || '';
      body.task_goal.task_title = _boundTask.title || '';
    }
    // v3/v4 混合竞争：带 era 参数（后端 run_eras 识别）
    if (opts.mode === 'mixed') {
      body.task_goal.era = true;
      body.task_goal.race_mode = 'mixed';
    }
    return _fetch('/api/v1/twin-trials', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(function (r) {
      if (r && r.ok === false) {
        return r.json().catch(function () { return {}; }).then(function (d) {
          throw new Error('创建试炼失败 HTTP' + r.status + (d.detail ? ': ' + JSON.stringify(d.detail).slice(0, 120) : ''));
        });
      }
      return r.json ? r.json() : r;
    }).then(function (trial) {
      var trialId = trial && (trial.trial_id || trial.id);
      var branchId = trial && (trial.branch_id || (trial.branches && trial.branches[0]));
      if (!trialId) throw new Error((trial && trial.detail) ? JSON.stringify(trial.detail).slice(0, 120) : '创建试炼失败（无 trial_id）');
      if (!branchId) throw new Error('创建试炼成功但无分支');
      return _fetch('/api/v1/twin-trials/' + trialId + '/branches/' + branchId + '/run', { method: 'POST' })
        .then(function (r) {
          if (r && r.ok === false) {
            return r.json().catch(function () { return {}; }).then(function (d) {
              throw new Error('演练执行失败 HTTP' + r.status + (d.detail ? ': ' + String(d.detail).slice(0, 160) : ''));
            });
          }
          return r.json ? r.json() : r;
        });
    }).then(function (result) {
      if (result && result.detail) throw new Error(result.detail);
      return result;
    });
  }

  // 播放一场结果并等回放结束（锦标赛逐队上场的时序基础）
  function _playResultAndWait(result, suppressReport) {
    _lastResult = result;
    _reportShown = !!suppressReport;
    eco2RenderResult(result);
    // 终局（非锦标赛中间场）打开 ③ 适者反馈台
    if (!suppressReport && result && typeof window.ecoFeedbackOnResult === 'function') {
      try { window.ecoFeedbackOnResult(result); } catch (eFb) { /* ignore */ }
    }
    return new Promise(function (resolve) {
      _initReplay(result, resolve);
      // 兜底：无 timeline 时直接结束
      if (!result.timeline || !result.timeline.steps || !result.timeline.steps.length) resolve();
    });
  }

  window.eco2RunDrill = function () {
    if (!window._selectedTeamId) {
      setText('eco2-run-status', '⚠ 请先选择投放种群（团队）');
      if (window.sexyPickTeam) window.sexyPickTeam();
      return;
    }
    // XF-6: 任务主闭环 — 未挂任务须显式确认随机生境
    if (!_boundTask && !_boundContract) {
      _showTaskMount(true);
      var ok = window.confirm(
        '尚未挂载任务（业务场景实例）。\n\n'
        + '无任务 = 无统一业务考卷，结果难以归因到场景。\n'
        + '建议：在「② 挂载任务」下拉中选择任务后再开跑。\n\n'
        + '仍要用随机生境空跑吗？'
      );
      if (!ok) {
        setText('eco2-run-status', '请先挂载任务（业务场景实例）');
        var mount = $('eco2-task-mount');
        if (mount) try { mount.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (e) {}
        return;
      }
      setText('eco2-run-status', '⚠ 空跑：随机生境（无任务考卷）');
    }
    // 重跑修复：先停掉上一场回放，否则新演练在后端计算的数秒内旧回放仍在播放，
    // 用户看到的是旧动画 → 误以为"只是 replay，没有重新演练"。
    // 计算期间保持作息冻结（__ECO_REPLAY_ACTIVE__=true），防止旧生物涌向设施抢镜；
    // 失败/超时路径会在 finish 里释放。
    if (_replay) { try { _replay.destroy(); } catch (e) {} _replay = null; }
    var rbar = $('eco2-replay-bar'); if (rbar) rbar.style.display = 'none';
    window.__ECO_REPLAY_ACTIVE__ = true;
    var maxSteps = parseInt(($('eco2-run-steps') || {}).value || '150', 10);
    var maxGens = parseInt(($('eco2-run-gens') || {}).value || '3', 10);
    var btn = $('eco2-run-launch');
    if (btn) { btn.disabled = true; btn.textContent = '🧬 环境正在选择…'; }
    _tournament = null;

    var finish = function () {
      if (_safetyTimer) { clearTimeout(_safetyTimer); _safetyTimer = null; }
      if (btn) { btn.disabled = false; btn.textContent = '🧬 开始物竞天择'; }
    };
    var fail = function (err) {
      console.error('[eco2] drill failed:', err);
      setText('eco2-run-status', '❌ 演练失败: ' + (err.message || err));
      window.__ECO_REPLAY_ACTIVE__ = false;   // 释放作息冻结，否则失败后场景永久停滞
      finish();
    };
    // 安全超时：120 秒后强制恢复按钮（防止后端卡死时前端永久等待）
    var _safetyTimer = setTimeout(function () {
      setText('eco2-run-status', '❌ 演练超时（120s）— 请检查后端服务');
      window.__ECO_REPLAY_ACTIVE__ = false;
      finish();
    }, 120000);

    // ── ③ 混合竞争：全部种群混合 + 跨队交配 + 纪元嵌套（需后端 run_eras） ──
    if (_raceMode === 'mixed') {
      setText('eco2-run-status', '🌍 混合竞争：纪元嵌套 · 跨队交配 · 环境阶跃加压 · 螺旋上升');
      var _drillStart = Date.now();
      var allTeams = [{ id: window._selectedTeamId, name: window._selectedTeamName || window._selectedTeamId }]
        .concat(_rivalTeams.map(function (t) { return t.id; }));
      _createAndRunDrill(window._selectedTeamId,
        _rivalTeams.map(function (t) { return t.id; }),
        maxSteps, maxGens, { mode: 'mixed' }
      ).then(function (result) {
        var _elapsed = Date.now() - _drillStart;
        var _delay = _elapsed < 600 ? 600 - _elapsed : 0;
        setTimeout(function () {
          var tid = (result.trial_id || '').slice(0, 8);
          if (!result.eras || !result.eras.length) {
            setText('eco2-run-status', '⚠ 混合竞争未返回纪元数据——请重启后端（./start.sh）加载 run_eras 代码后重试');
          } else {
            setText('eco2-run-status', '✅ 混合竞争完成 (#' + tid + ') — ' + result.eras.length + ' 个纪元 · 回放中');
          }
          finish();
          _playResultAndWait(result, false);
        }, _delay);
      }).catch(fail);
      return;
    }

    // ── ② 多队对抗：强调团队协作 + 排兵策略（需对比种群） ──
    if (_raceMode === 'confrontation') {
      if (!_rivalTeams.length) {
        setText('eco2-run-status', '⚠ 多队对抗需要至少 1 个对比种群——请点「＋添加对比种群」');
        window.__ECO_REPLAY_ACTIVE__ = false;
        finish();
        return;
      }
      var examC = _resolveSharedExam();
      var examLabel = examC.mode === 'apple' ? '同一任务环境'
        : examC.mode === 'primary_exam' ? '主任务环境'
        : '随机生境';
      setText('eco2-run-status', '⚔️ 多队对抗 · ' + examLabel + ' · 比团队协作与排兵策略');
      var _drillStartC = Date.now();
      _createAndRunDrill(window._selectedTeamId,
        _rivalTeams.map(function (t) { return t.id; }),
        maxSteps, maxGens
      ).then(function (result) {
        var _elapsed = Date.now() - _drillStartC;
        var _delay = _elapsed < 600 ? 600 - _elapsed : 0;
        setTimeout(function () {
          var tid = (result.trial_id || '').slice(0, 8);
          if (!result.populations || result.populations.length < 2) {
            setText('eco2-run-status', '⚠ 对比种群未进入生境——请重启后端（./start.sh）后重试');
          } else {
            setText('eco2-run-status', '✅ 多队对抗完成 (#' + tid + ') — 回放中，拖动进度条可回顾');
          }
          finish();
          _playResultAndWait(result, false);
        }, _delay);
      }).catch(fail);
      return;
    }

    // ── ① 分场锦标赛：比个体 skill（可单队，也可多队同场——各方 Agent 都入场）──
    {
      var examD = _resolveSharedExam();
      var extraDiv = _rivalTeams.map(function (t) { return t.id; });
      var examHint = examD.mode === 'apple' ? ' · 同一任务环境'
        : examD.mode === 'primary_exam' ? ' · 主任务环境'
        : ' · 随机生境';
      if (extraDiv.length) {
        setText('eco2-run-status', '🏟 分场锦标赛：多队 Agent 同场 · 比个体 skill' + examHint + ' · 客观过滤');
      } else {
        setText('eco2-run-status', '🏟 分场锦标赛：队内个体 skill · 家族精英' + examHint);
      }
      var _drillStart = Date.now();
      _createAndRunDrill(window._selectedTeamId, extraDiv, maxSteps, maxGens)
      .then(function (result) {
        var _elapsed = Date.now() - _drillStart;
        var _delay = _elapsed < 600 ? 600 - _elapsed : 0;
        setTimeout(function () {
          var tid = (result.trial_id || '').slice(0, 8);
          var pops = result.populations || [];
          var msg = '✅ 分场锦标赛完成 (#' + tid + ')';
          if (pops.length > 1) msg += ' · ' + pops.length + ' 队 Agent 已入场 · ' + pops.join(' + ');
          msg += ' — 回放中';
          if (extraDiv.length && pops.length < 2) {
            msg = '⚠ 对比队未进入生境——请重启后端确认多种群路径';
          }
          setText('eco2-run-status', msg);
          finish();
          _playResultAndWait(result, false);
        }, _delay);
      }).catch(fail);
      return;
    }
  };
  // 旧入口兼容（rp-eco 旧按钮/外部调用）
  window.ecoRunDrill = window.eco2RunDrill;
  window._ecoSkillLabel = _sk;

  // ═══ 结果渲染：八区块 ═══
  window.eco2RenderResult = eco2RenderResult;
  function eco2RenderResult(result) {
    if (!result) return;
    var ranking = result.final_ranking || [];
    var gens = result.generations || [];
    var genePool = result.gene_pool || {};

    // ① KPI
    var aliveN = ranking.filter(function (r) { return r.alive; }).length;
    var skillSet = {};
    ranking.forEach(function (r) { (r.skill_genome || []).forEach(function (s) { if (r.alive) skillSet[s] = 1; }); });
    setText('eco2-kpi-gen', String(result.total_generations != null ? result.total_generations : gens.length));
    setText('eco2-kpi-alive', aliveN + ' / ' + ranking.length);
    setText('eco2-kpi-best', String(result.best_survival_ticks || (ranking[0] && ranking[0].survival_ticks) || 0));
    setText('eco2-kpi-diversity', String(Object.keys(skillSet).length));

    // v4 ⑧+ Skill 集成建议
    try {
      var integ = result.integration;
      var integBox = $('eco2-integration');
      if (integBox) {
        if (integ && (integ.recommended_bindings || integ.dominant_skills)) {
          var lines = [];
          lines.push('<div style="font-size:10px;margin-bottom:4px">🧩 Skill 集成 <span style="color:var(--dim)">(' + esc(integ.write_policy || 'suggest_only') + ')</span></div>');
          if (integ.dominant_skills && integ.dominant_skills.length) {
            lines.push('<div>dominant: ' + integ.dominant_skills.map(function (s) { return esc(_sk(s)); }).join(', ') + '</div>');
          }
          if (integ.missing_plan_skills && integ.missing_plan_skills.length) {
            lines.push('<div style="color:#f87171">missing: ' + integ.missing_plan_skills.map(function (s) { return esc(_sk(s)); }).join(', ') + '</div>');
          }
          (integ.recommended_bindings || []).slice(0, 5).forEach(function (b) {
            lines.push('<div>+ ' + esc(b.agent_id) + ' ← ' + (b.add_skills || []).map(function (s) { return esc(_sk(s)); }).join(', ') + '</div>');
          });
          lines.push('<div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">'
            + '<button type="button" class="btn" style="font-size:10px;padding:2px 8px" onclick="eco2CopyIntegration()">📋 复制建议 JSON</button>'
            + '<button type="button" class="btn" style="font-size:10px;padding:2px 8px" onclick="eco2ApplyIntegration(false)">建议预览 apply</button>'
            + '<button type="button" class="btn btn-primary" style="font-size:10px;padding:2px 8px" onclick="eco2ApplyIntegration(true)">✅ 确认写回绑定</button>'
            + '<button type="button" class="btn" style="font-size:10px;padding:2px 8px" onclick="eco2DispatchWinner()">🏷 按适者派发（可选）</button>'
            + '</div>');
          // 详细写回改走 ③ 适者反馈台；此处仅保留摘要入口
          lines.push('<div style="margin-top:6px"><button type="button" class="btn btn-primary" style="font-size:10px;padding:3px 10px" onclick="ecoFeedbackOpen()">③ 打开适者反馈台</button></div>');
          integBox.innerHTML = lines.join('');
          integBox.style.display = 'block';
          window.__LAST_INTEGRATION__ = integ;
          window.__LAST_ECO_RESULT__ = result;
        } else {
          integBox.style.display = 'none';
          window.__LAST_ECO_RESULT__ = result;
        }
      }
    } catch (e) { /* ignore */ }

    // ② 生态位 demand skills（演练后环境可能已漂移 → 用 result.env 刷新；无标题）
    if (result.env && result.env.demanded_skills) {
      _renderEnvDemandChips(result.env.demanded_skills);
    }

    _renderPopulation(ranking, null);
    _renderGenerations(gens);
    _renderGenePool(genePool, result.collab_profile);
    _renderLineage(result);

    // ⑧ 棘轮
    setText('eco2-ratchet-best', String(result.best_survival_ticks || '—'));
    var advanced = gens.some(function (g) { return g.ratchet_advanced; });
    setText('eco2-ratchet-note', advanced ? '↑ 本次演练推进了棘轮' : '= 未超越历史最优');
  }

  // ④ 种群面板（frame 传入时按回放帧实时刷新意图/血量；多种群时按种群分组）
  function _renderPopulation(ranking, frame) {
    var box = $('eco2-pop-list');
    if (!box) return;
    var actions = (frame && frame.actions) || {};
    var pops = {};
    ranking.forEach(function (r) { pops[r.population || ''] = 1; });
    var multiPop = Object.keys(pops).length > 1;
    var stats = (_lastResult && _lastResult.population_stats) || {};
    var lastPop = null;
    box.innerHTML = ranking.slice().sort(function (a, b) {
      var pa = a.population || '', pb = b.population || '';
      if (multiPop && pa !== pb) return pa < pb ? -1 : 1;
      return b.survival_ticks - a.survival_ticks;
    }).map(function (r) {
      var head = '';
      if (multiPop && (r.population || '') !== lastPop) {
        lastPop = r.population || '';
        var st = stats[lastPop] || {};
        head = '<div style="padding:4px 2px;margin-top:4px;font-size:10px;font-weight:700;color:var(--cyan);border-bottom:1px solid var(--border)">'
          + '🏳️ 种群 ' + esc(lastPop)
          + (st.total ? ' · 存活 ' + st.alive + '/' + st.total + ' · 平均 ' + st.avg_survival_ticks + 't · 最长 ' + st.best + 't' : '')
          + '</div>';
      }
      // v2.3: 回放中尚未出生的后代不显示（动画与淘汰/繁衍时序吻合）
      if (frame && frame.generation != null && (r.generation || 0) > frame.generation) return head;
      return head + _popRow(r, actions, frame);
    }).join('') || '<div class="eco2-empty">（无种群数据）</div>';
    var status = $('eco2-pop-status');
    if (status) {
      var aliveN = ranking.filter(function (r) { return r.alive; }).length;
      status.textContent = '· 存活 ' + aliveN + ' / ' + ranking.length
        + (multiPop ? '（多种群同场竞争）' : '（按生存时长排序）');
    }
  }

  function _popRow(r, actions, frame) {
    var act = actions[r.agent_id] || {};
    var health = act.health != null ? act.health : r.health;
    var ticks = act.survival_ticks != null ? act.survival_ticks : r.survival_ticks;
    var intent = act.intention || '';
    var alive = frame ? ((frame.deaths || []).indexOf(r.agent_id) === -1 && health > 0) : r.alive;
    var ratio = Math.max(0, Math.min(1, health / 100));
    var hpColor = ratio > 0.6 ? 'var(--green)' : ratio > 0.3 ? 'var(--amber)' : '#f43f5e';
    var cg = r.collab_genome || {};
    var collabBars = COLLAB_DIMS.map(function (d) {
      var v = cg[d[0]] != null ? cg[d[0]] : 0.5;
      return '<i title="' + d[1] + ' ' + v + '" style="height:' + Math.max(2, Math.round(v * 14)) + 'px"></i>';
    }).join('');
    var genome = (r.skill_genome || []).slice(0, 4).map(function (s) {
      return '<span class="eco2-chip' + (alive ? '' : ' dead') + '" title="' + esc(s) + '">'
        + esc(_sk(s).slice(0, 14)) + '</span>';
    }).join(' ') + ((r.skill_genome || []).length > 4 ? ' <span style="color:var(--dim)">+' + (r.skill_genome.length - 4) + '</span>' : '');
    var icon = !alive ? '💀' : (act.outcome === 'outcompeted' ? '🥊' : (INTENT_ICON[intent] || '·'));
    // 显示短名，title 带全 id + 种群
    var shortNm = (r.name || r.agent_id || '').replace(/^(build|aws|pet|ai|energy)_/, '');
    var nameTitle = esc(r.agent_id) + (r.population ? ' @ ' + r.population : '');
    // T_i 分解条（skill/协作/残差）
    var attrBar = '';
    if (r.attr_skill_share != null) {
      attrBar = '<span title="' + esc(r.attr_explain || '') + ' | skill '
        + Math.round(r.attr_skill_share * 100) + '% 协作 ' + Math.round(r.attr_collab_share * 100)
        + '% 残差 ' + Math.round(r.attr_residual_share * 100) + '%" '
        + 'style="display:inline-flex;width:40px;height:6px;border-radius:2px;overflow:hidden;flex-shrink:0">'
        + '<i style="width:' + Math.round(r.attr_skill_share * 100) + '%;background:#22d3ee"></i>'
        + '<i style="width:' + Math.round(r.attr_collab_share * 100) + '%;background:#a78bfa"></i>'
        + '<i style="width:' + Math.round(r.attr_residual_share * 100) + '%;background:#64748b"></i></span>';
    }
    return '<div class="eco2-pop-row' + (alive ? '' : ' dead') + '">'
      + '<span style="width:14px;text-align:center" title="' + (act.outcome === 'outcompeted' ? '竞争失败：有能力但没抢到生态位名额' : '') + '">' + icon + '</span>'
      + '<span class="eco2-pop-name" title="' + nameTitle + '">' + esc(shortNm) + '</span>'
      + '<span class="eco2-hpbar"><i style="width:' + Math.round(ratio * 100) + '%;background:' + hpColor + '"></i></span>'
      + '<span style="min-width:38px;color:var(--amber);font-weight:600">' + ticks + 't</span>'
      + attrBar
      + '<span class="eco2-collab-mini" style="height:14px" title="协作基因 分享/信号/跟随/择偶">' + collabBars + '</span>'
      + '<span style="flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">' + genome + '</span>'
      + '</div>';
  }

  // ⑤ 世代曲线 + 记录（v3 三比：环比/同比/综合比）
  function _renderGenerations(gens) {
    var chart = $('eco2-gen-chart'), list = $('eco2-gen-list');
    if (chart) {
      // XV-5: 三比切换器
      var tabsHtml = '<div style="display:flex;gap:4px;margin-bottom:6px;font-size:9px">'
        + '<button class="eco2-gen-tab" onclick="eco2SetGenView(\'qoq\')" id="eco2-gen-tab-qoq" style="padding:2px 6px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--cyan);color:#fff">环比</button>'
        + '<button class="eco2-gen-tab" onclick="eco2SetGenView(\'yoy\')" id="eco2-gen-tab-yoy" style="padding:2px 6px;border:1px solid var(--border);border-radius:4px;cursor:pointer">同比</button>'
        + '<button class="eco2-gen-tab" onclick="eco2SetGenView(\'composite\')" id="eco2-gen-tab-composite" style="padding:2px 6px;border:1px solid var(--border);border-radius:4px;cursor:pointer">综合比</button>'
        + '</div>';

      var view = _genView || 'qoq';
      var chartHtml = '';

      if (view === 'yoy' && window.computeYoY) {
        // 同比：分组折线（混合竞争按 era 分组，多队按 population 分组）
        var groupBy = (_raceMode === 'mixed') ? 'era' : 'population';
        var yoy = window.computeYoY(gens, groupBy);
        if (yoy.groups && yoy.groups.length > 1) {
          var maxVal = Math.max.apply(null, yoy.groups.flatMap(function (g) {
            return g.data.map(function (d) { return d.best || 0; });
          }).concat([1]));
          var colors = ['#f59e0b', '#22d3ee', '#a78bfa', '#22c55e', '#ec4899'];
          chartHtml = '<div style="font-size:9px;color:var(--dim);margin-bottom:4px">同相位对齐（' + (groupBy === 'era' ? '纪元' : '种群') + '分组）</div>'
            + '<div style="display:flex;gap:2px;align-items:flex-end;height:60px">';
          // 简易折线：每代一个点，组内连线用 flex 排列
          for (var gi = 0; gi < (yoy.aligned.length); gi++) {
            var row = yoy.aligned[gi];
            chartHtml += '<div style="flex:1;min-width:16px;text-align:center;border-right:1px dashed var(--border)">';
            yoy.groups.forEach(function (grp, idx) {
              var d = row[grp.key];
              if (d) {
                var h = Math.round((d.best / maxVal) * 50);
                chartHtml += '<div style="height:' + h + 'px;width:4px;display:inline-block;background:' + colors[idx % colors.length] + ';margin:0 1px" title="' + grp.key + ' G' + d.gen + ': ' + d.best + 't"></div>';
              }
            });
            chartHtml += '<div style="font-size:7px;color:var(--dim)">' + gi + '</div></div>';
          }
          chartHtml += '</div>';
          // 图例
          chartHtml += '<div style="font-size:8px;color:var(--dim);margin-top:2px">'
            + yoy.groups.map(function (grp, idx) {
              return '<span style="color:' + colors[idx % colors.length] + '">●</span> ' + esc(grp.key);
            }).join('　') + '</div>';
        } else {
          chartHtml = '<div class="eco2-empty">同比需≥2个' + (groupBy === 'era' ? '纪元' : '种群') + '——混合竞争或多队对抗模式才有意义</div>';
        }
      } else if (view === 'composite' && window.computeComposite) {
        // 综合比：归一化上升指数
        var comp = window.computeComposite(gens, (_lastResult && _lastResult.env) || {});
        var maxIdx = Math.max.apply(null, comp.map(function (c) { return c.index; }).concat([0.01]));
        chartHtml = '<div style="font-size:9px;color:var(--dim);margin-bottom:4px">综合上升指数（权重随环境压力自适应）</div>'
          + '<div style="display:flex;gap:2px;align-items:flex-end;height:60px">';
        comp.forEach(function (c) {
          var h = Math.round((c.index / maxIdx) * 56);
          var color = c.era > 0 ? '#a78bfa' : '#22d3ee';
          chartHtml += '<div style="flex:1;min-width:16px;text-align:center">'
            + '<div style="height:' + h + 'px;background:' + color + ';border-radius:2px 2px 0 0;min-height:2px" title="G' + c.gen + ' 指数 ' + c.index + ' (压力' + c.stress + ')"></div>'
            + '<div style="font-size:7px;color:var(--dim)">G' + c.gen + '</div></div>';
        });
        chartHtml += '</div>'
          + '<div style="font-size:8px;color:var(--dim);margin-top:2px">指数=适应率×w1+均值率×w2+多样性×w3+棘轮×w4（越严酷适应率权重越高）</div>';
      } else {
        // 环比（QoQ，默认）：柱状 + Δ 箭头
        var maxBest = Math.max.apply(null, gens.map(function (g) { return g.best_survival_ticks || 1; }).concat([1]));
        var qoq = window.computeQoQ ? window.computeQoQ(gens) : null;
        chartHtml = gens.map(function (g, i) {
          var h = Math.max(8, Math.round((g.best_survival_ticks || 0) / maxBest * 56));
          var ha = Math.max(4, Math.round((g.avg_survival_ticks || 0) / maxBest * 56));
          var deltaInfo = '';
          if (qoq && qoq[i] && i > 0) {
            var q = qoq[i];
            deltaInfo = '<div style="font-size:7px;color:' + q.arrowColor + '" title="Δ最长' + q.deltaBest + ' Δ平均' + q.deltaAvg + ' Δ多样性' + q.deltaDiv.toFixed(2) + '">'
              + q.arrow + (q.deltaBestPct > 0 ? '+' : '') + q.deltaBestPct + '%</div>';
          }
          return '<div class="eco2-genbar" style="height:' + h + 'px" title="G' + g.generation + ' 最长 ' + g.best_survival_ticks + 't / 平均 ' + g.avg_survival_ticks + 't / 多样性 ' + (g.diversity || '—') + '">'
            + '<div style="position:absolute;bottom:0;left:0;right:0;height:' + ha + 'px;background:rgba(255,255,255,.25);border-radius:2px"></div>'
            + '<span class="lbl">G' + g.generation + (g.drift ? '⚡' : '') + '</span>'
            + deltaInfo
            + '</div>';
        }).join('');
      }
      chart.innerHTML = tabsHtml + chartHtml;
    }
    if (list) {
      list.innerHTML = gens.map(function (g) {
        // v2.3: 多种群时每代附各种群对比行
        var popLine = '';
        var ps = g.population_stats || {};
        if (Object.keys(ps).length > 1) {
          popLine = '<br><span style="color:var(--dim);font-size:9px">'
            + Object.keys(ps).map(function (pop) {
                var s = ps[pop];
                return '🏳️' + esc(pop) + ' ' + s.alive + '/' + s.total + '·avg' + s.avg_survival_ticks + 't';
              }).join('　')
            + '</span>';
        }
        return '<div style="padding:3px 2px;border-bottom:1px dashed var(--border)">'
          + '<b style="color:var(--purple)">G' + g.generation + '</b>'
          + ' 存活 <b style="color:var(--green)">' + g.living + '</b>'
          + ' · 最长 <b style="color:var(--amber)">' + g.best_survival_ticks + 't</b>'
          + ' · 平均 ' + g.avg_survival_ticks + 't'
          + ' · 新生 ' + (g.births || 0)
          + (g.drift ? ' · <span style="color:var(--cyan)">⚡漂移 ' + esc(g.drift.removed) + '→' + esc(g.drift.added) + '</span>' : '')
          + (g.ratchet_advanced ? ' · <span style="color:var(--amber)">🔒棘轮↑</span>' : '')
          + (g.extinct ? ' · <span style="color:#f43f5e">💀全灭</span>' : '')
          + (g.cat_commentary ? '<br><span style="color:var(--text2);font-size:10px">🐈 ' + esc(g.cat_commentary) + '</span>' : '')
          + popLine
          + '</div>';
      }).join('') || '<div class="eco2-empty">（无世代记录）</div>';
    }
  }

  // ⑥ 基因池 + 协作画像
  function _renderGenePool(pool, collabProfile) {
    var box = $('eco2-gene-skills');
    if (box) {
      var html = '';
      var dom = pool.dominant || [];
      var dep = pool.deprecated || [];
      var neu = pool.neutral || [];
      if (dom.length) {
        html += '<div style="margin-bottom:4px"><b style="color:var(--amber)">👑 dominant（被环境选中）</b><br>'
          + dom.map(function (g) { return '<span class="eco2-chip dominant" title="' + esc(g.skill) + '">' + esc(_sk(g.skill)) + ' ×' + g.carriers + '</span>'; }).join(' ') + '</div>';
      }
      if (neu.length) {
        html += '<div style="margin-bottom:4px"><b style="color:var(--text2)">🌱 neutral（观察中）</b><br>'
          + neu.slice(0, 10).map(function (g) { return '<span class="eco2-chip" title="' + esc(g.skill) + '">' + esc(_sk(g.skill)) + ' ×' + g.carriers + '</span>'; }).join(' ') + '</div>';
      }
      if (dep.length) {
        html += '<div><b style="color:#f87171">🪦 deprecated（随死者消亡）</b><br>'
          + dep.slice(0, 10).map(function (g) { return '<span class="eco2-chip dead" title="' + esc(g.skill) + '">' + esc(_sk(g.skill)) + '</span>'; }).join(' ') + '</div>';
      }
      box.innerHTML = html || '<div class="eco2-empty">（基因池为空）</div>';
    }
    var cb = $('eco2-gene-collab');
    if (cb) {
      var means = (collabProfile && collabProfile.means) || (pool.collab_profile && pool.collab_profile.means) || null;
      cb.innerHTML = means
        ? COLLAB_DIMS.map(function (d) {
            var v = means[d[0]] != null ? means[d[0]] : 0.5;
            return '<div style="display:flex;align-items:center;gap:6px;font-size:10px;margin-bottom:3px">'
              + '<span style="min-width:34px;color:var(--text2)">' + d[1] + '</span>'
              + '<span class="eco2-hpbar" style="flex:1"><i style="width:' + Math.round(v * 100) + '%;background:var(--cyan)"></i></span>'
              + '<span style="min-width:30px;text-align:right;color:var(--cyan)">' + v + '</span></div>';
          }).join('')
        : '<div class="eco2-empty">（演练后显示协作基因被选择的方向）</div>';
    }
  }

  // ⑦ 繁衍谱系（v3 遗传学化七图 + 冷静判词）
  function _renderLineage(result) {
    var box = $('eco2-lineage');
    if (!box) return;
    var lineage = result.lineage || [];
    var ranking = result.final_ranking || [];
    var epochs = result.timeline && result.timeline.epochs || [];

    if (!lineage.length && !epochs.length) {
      box.innerHTML = '<div class="eco2-empty">（本场无繁衍——可能环境过于严酷或世代数不足）</div>';
      return;
    }

    var html = '';
    var genetics = window.heritability ? {
      h2_survival: window.heritability(lineage, ranking, 'survival_ticks'),
      h2_share: window.heritability(lineage, ranking, 'share_tendency'),
      assortative: window.assortativeMating(lineage, ranking),
      relationship: window.coefficientOfRelationship(lineage, ranking),
      regression: window.regressionToMean(lineage, ranking),
      founder: window.founderContribution(lineage, ranking),
      collabFlow: window.collabLineageFlow(lineage, ranking),
      schools: window.schoolClusters(ranking)
    } : {};
    var contract = result.contract || _boundContract || null;
    var heat = (window.planCoverageHeatmap && contract)
      ? window.planCoverageHeatmap(ranking, contract) : null;
    var xfer = window.verticalVsHorizontalTransfer
      ? window.verticalVsHorizontalTransfer(result.timeline || {}) : null;

    // ⓪ v4 计划技能覆盖热力
    if (heat && heat.skills && heat.skills.length) {
      html += '<div style="margin-bottom:8px"><b style="color:#a78bfa;font-size:11px">🗺 计划技能覆盖热力</b>'
        + ' <span style="color:var(--dim);font-size:9px">coverage=' + heat.coverage + '</span>';
      html += '<div style="overflow-x:auto;margin-top:4px"><table style="border-collapse:collapse;font-size:9px"><tr><th></th>';
      heat.skills.forEach(function (sk) {
        html += '<th style="padding:1px 3px;color:var(--dim)">' + esc(_sk(sk)).slice(0, 8) + '</th>';
      });
      html += '</tr>';
      (heat.matrix || []).slice(0, 12).forEach(function (row, ri) {
        html += '<tr><td style="padding:1px 3px;color:var(--dim)">' + esc(String(heat.agents[ri] || '').slice(0, 8)) + '</td>';
        row.forEach(function (v) {
          html += '<td style="width:14px;height:12px;background:' + (v ? 'rgba(34,197,94,.7)' : 'rgba(148,163,184,.15)') + '"></td>';
        });
        html += '</tr>';
      });
      html += '</table></div>';
      html += '<div style="font-size:9px;color:var(--dim);margin-top:2px">判词：覆盖率 ' + Math.round((heat.coverage || 0) * 100)
        + '%——绿格=持有计划技能；低覆盖意味着该队基因组与任务需求错配</div></div>';
    }
    if (xfer && xfer.total > 0) {
      html += '<div style="margin-bottom:8px"><b style="color:#22d3ee;font-size:11px">↕ 垂直 vs 水平传递</b>'
        + '<div style="font-size:10px">垂直(遗传) ' + xfer.inherit + ' · 水平(学习) ' + xfer.learn
        + ' · 变异 ' + xfer.mutate + '</div>'
        + '<div style="font-size:9px;color:var(--dim)">判词：水平比 '
        + Math.round((xfer.horizontal_ratio || 0) * 100) + '%——盲目学习贡献了多少新 skill</div></div>';
    }
    // 分 skill h²（取计划技能前 4）
    if (window.perSkillHeritability && heat && heat.skills) {
      var h2rows = [];
      heat.skills.slice(0, 4).forEach(function (sk) {
        var h = window.perSkillHeritability(lineage, ranking, sk);
        if (h) h2rows.push(h);
      });
      if (h2rows.length) {
        html += '<div style="margin-bottom:8px"><b style="color:#22d3ee;font-size:11px">🧬 分 skill 遗传力</b>';
        h2rows.forEach(function (h) {
          html += '<div style="font-size:10px">' + esc(_sk(h.skill)) + ' h²=<b>' + h.h2 + '</b> <span style="color:var(--dim)">(' + h.pairs + '对)</span></div>';
        });
        html += '</div>';
      }
    }

    // ① 血系树（保留原有缩进树 + 系谱系数着色）
    html += '<div style="margin-bottom:8px"><b style="color:#a78bfa;font-size:11px">🌳 血系树</b>';
    var treeRows = [];
    lineage.forEach(function (rec) {
      treeRows.push('<div style="padding:2px 2px;border-bottom:1px dashed var(--border);font-size:10px">'
        + '<b style="color:var(--purple)">G' + rec.generation + '</b> '
        + '<b style="color:var(--green)">' + esc(rec.child.replace(/^(build|aws|pet|ai|energy)_/, '')) + '</b>'
        + ' <span style="color:var(--dim)">↳ ' + (rec.parents || []).slice(0, 2).map(function (p) { return esc(p.replace(/^(build|aws|pet|ai|energy)_/, '')); }).join(' × ') + '</span>'
        + '</div>');
    });
    if (!treeRows.length) {
      epochs.forEach(function (ep) {
        (ep.offspring || []).forEach(function (child) {
          treeRows.push('<div style="padding:2px 2px;border-bottom:1px dashed var(--border);font-size:10px">'
            + '<b style="color:var(--purple)">G' + ep.generation + '</b> '
            + '<b style="color:var(--green)">' + esc(child.replace(/^(build|aws|pet|ai|energy)_/, '')) + '</b>'
            + ' <span style="color:var(--dim)">↳ ' + (ep.parents || []).slice(0, 2).map(function (p) { return esc(p.replace(/^(build|aws|pet|ai|energy)_/, '')); }).join(' × ') + '</span>'
            + '</div>');
        });
      });
    }
    html += treeRows.slice(0, 20).join('') || '<div class="eco2-empty">（无后代记录）</div>';
    if (treeRows.length > 20) html += '<div style="font-size:9px;color:var(--dim)">…共 ' + treeRows.length + ' 条</div>';
    html += '</div>';

    // ② 遗传力条（D1）
    if (genetics.h2_survival || genetics.h2_share) {
      html += '<div style="margin-bottom:8px"><b style="color:#22d3ee;font-size:11px">🧬 遗传力 h²（亲子回归斜率）</b>';
      var h2Items = [];
      if (genetics.h2_survival) h2Items.push({ trait: '生存时长', h2: genetics.h2_survival.h2, pairs: genetics.h2_survival.pairs });
      if (genetics.h2_share) h2Items.push({ trait: '分享倾向', h2: genetics.h2_share.h2, pairs: genetics.h2_share.pairs });
      h2Items.forEach(function (item) {
        var color = item.h2 > 0.5 ? '#22c55e' : item.h2 > 0.2 ? '#f59e0b' : '#f87171';
        var barW = Math.min(100, Math.abs(item.h2) * 100);
        html += '<div style="font-size:10px;margin:3px 0">'
          + '<span style="min-width:60px;display:inline-block">' + esc(item.trait) + '</span>'
          + '<span class="eco2-hpbar" style="display:inline-block;width:60px;vertical-align:middle"><i style="width:' + barW + '%;background:' + color + '"></i></span>'
          + ' <b style="color:' + color + '">' + item.h2 + '</b>'
          + ' <span style="color:var(--dim);font-size:9px">(' + item.pairs + ' 对亲子)</span></div>';
      });
      var judge = genetics.h2_survival && genetics.h2_survival.h2 > 0.5
        ? '生存时长遗传力强——适应度可遗传，选择有效'
        : genetics.h2_survival && genetics.h2_survival.h2 > 0.2
        ? '中等遗传力——部分可遗传，选择缓慢见效'
        : '遗传力低——环境噪声大或性状非加性遗传';
      html += '<div style="font-size:9px;color:var(--dim);margin-top:2px">判词：' + esc(judge) + '</div></div>';
    }

    // ③ 联姻散点（D2）
    if (genetics.assortative) {
      var ar = genetics.assortative.r;
      var aColor = ar > 0.3 ? '#22c55e' : ar > 0 ? '#f59e0b' : '#f87171';
      html += '<div style="margin-bottom:8px"><b style="color:#22d3ee;font-size:11px">💕 同类选配（配偶 survival 相关）</b>'
        + '<div style="font-size:10px;margin:3px 0">Pearson r = <b style="color:' + aColor + '">' + ar + '</b>'
        + ' <span style="color:var(--dim);font-size:9px">(' + genetics.assortative.pairs + ' 对配对)</span></div>'
        + '<div style="font-size:9px;color:var(--dim)">判词：' + (ar > 0.3 ? '强同类选配——精英联姻放大优势基因集中' : ar > 0 ? '弱同类选配——适者倾向与适者配对' : '随机选配——无门当户对效应') + '</div></div>';
    }

    // ④ 近交/杂优曲线（D3）
    if (genetics.relationship) {
      var rel = genetics.relationship;
      var hetColor = rel.heterosis_delta > 0 ? '#22c55e' : rel.heterosis_delta < 0 ? '#f87171' : '#8b9ab5';
      html += '<div style="margin-bottom:8px"><b style="color:#22d3ee;font-size:11px">🔬 近交 vs 杂种优势</b>'
        + '<div style="font-size:10px;margin:3px 0">跨队后代 ' + rel.hybrid_count + ' 个（avg ' + rel.hybrid_avg + 't）vs 队内后代 ' + rel.inbred_count + ' 个（avg ' + rel.inbred_avg + 't）</div>'
        + '<div style="font-size:10px">杂优 Δ = <b style="color:' + hetColor + '">' + (rel.heterosis_delta >= 0 ? '+' : '') + rel.heterosis_delta + 't</b></div>'
        + '<div style="font-size:9px;color:var(--dim)">判词：' + (rel.heterosis_delta > 2 ? '杂种优势显著——远缘血系后代更适应，混合竞争应鼓励跨队交配' : rel.heterosis_delta < -2 ? '近交衰退——队内后代优于跨队，当前环境不奖励基因流' : '无明显差异——杂优与近交生存相当') + '</div></div>';
    }

    // ⑤ 均值回归轨迹（D4）
    if (genetics.regression) {
      var reg = genetics.regression;
      html += '<div style="margin-bottom:8px"><b style="color:#22d3ee;font-size:11px">📉 均值回归轨迹</b>'
        + '<div style="font-size:10px;margin:3px 0">初代领先优势: ' + reg.initial_advantage + 't · 半衰期: ' + (reg.half_life != null ? reg.half_life + ' 代' : '未观测到') + '</div>';
      if (reg.trajectory && reg.trajectory.length > 1) {
        html += '<div style="display:flex;gap:2px;align-items:flex-end;height:30px;margin:4px 0">';
        var maxVal = Math.max.apply(null, reg.trajectory.map(function (t) { return t.descAvg; }));
        reg.trajectory.forEach(function (t) {
          var h1 = Math.round((t.descAvg / maxVal) * 28);
          var h2 = Math.round((t.popMean / maxVal) * 28);
          html += '<div style="flex:1;min-width:20px;text-align:center">'
            + '<div style="height:' + h1 + 'px;background:#f59e0b;border-radius:2px 2px 0 0" title="领先血系 G' + t.gen + ': ' + t.descAvg + 't"></div>'
            + '<div style="height:' + h2 + 'px;background:rgba(34,211,238,.4)" title="种群均值 G' + t.gen + ': ' + t.popMean + 't"></div>'
            + '<div style="font-size:7px;color:var(--dim)">G' + t.gen + '</div></div>';
        });
        html += '</div><div style="font-size:8px;color:var(--dim)">🟠 领先血系 · 🔵 种群均值</div>';
      }
      html += '<div style="font-size:9px;color:var(--dim)">判词：' + (reg.halfLife && reg.halfLife !== 0 ? '领先优势约 ' + reg.halfLife + ' 代衰减一半——持续的是可传承的底层能力而非单次运气' : '样本不足或优势未衰减') + '</div></div>';
    }

    // ⑥ 奠基者溯源（D5）
    if (genetics.founder) {
      var fc = genetics.founder;
      html += '<div style="margin-bottom:8px"><b style="color:#22d3ee;font-size:11px">🏛 奠基者贡献</b>'
        + '<div style="font-size:10px;margin:3px 0">末代（G' + fc.max_gen + '）各奠基者后裔占比：</div>';
      fc.contributions.slice(0, 5).forEach(function (c) {
        var name = c.founder.replace(/^(build|aws|pet|ai|energy)_/, '');
        html += '<div style="font-size:10px">' + esc(name) + ': ' + c.pct + '% (' + c.descendants_in_last_gen + ' 个后裔)</div>';
      });
      if (fc.bottleneck) {
        html += '<div style="font-size:9px;color:#f87171;margin-top:3px">⚠ 瓶颈世代 G' + fc.bottleneck.gen + ': 存活 ' + fc.bottleneck.count + '（上代 ' + fc.bottleneck.prev_count + '）</div>';
      }
      html += '<div style="font-size:9px;color:var(--dim);margin-top:2px">判词：奠基者效应' + (fc.contributions[0] && fc.contributions[0].pct > 50 ? '显著——少数初代个体主导末代基因池' : '分散——多奠基者均衡贡献') + '</div></div>';
    }

    // ⑦ 学派/政治/地理血系热力图（D6）
    if (genetics.collabFlow || (genetics.schools && genetics.schools.length)) {
      html += '<div style="margin-bottom:8px"><b style="color:#22d3ee;font-size:11px">🎓 学派/协作血系传递</b>';
      if (genetics.schools && genetics.schools.length) {
        html += '<div style="font-size:10px;margin:3px 0">学派（skill 共现簇）：</div>';
        genetics.schools.slice(0, 3).forEach(function (cluster, idx) {
          html += '<div style="font-size:9px;color:var(--dim)">学派' + (idx + 1) + '(' + cluster.size + '技能): '
            + cluster.skills.slice(0, 5).map(function (s) { return esc(_sk(s)); }).join('、') + '</div>';
        });
      }
      if (genetics.collabFlow) {
        var cf = genetics.collabFlow;
        html += '<div style="font-size:10px;margin:4px 0">协作基因亲子传递：</div>';
        Object.keys(cf).forEach(function (dim) {
          var d = cf[dim];
          var dimName = { share_tendency: '分享', signal_tendency: '信号', follow_tendency: '跟随', mate_choosiness: '择偶' }[dim] || dim;
          var deltaColor = d.delta > 0.02 ? '#22c55e' : d.delta < -0.02 ? '#f87171' : '#8b9ab5';
          html += '<div style="font-size:9px">' + dimName + ': 父' + d.parent_avg + '→子' + d.child_avg
            + ' <span style="color:' + deltaColor + '">Δ' + (d.delta >= 0 ? '+' : '') + d.delta + '</span></div>';
        });
      }
      html += '<div style="font-size:9px;color:var(--dim);margin-top:2px">判词：协作基因沿血系传递——Δ 正向=被环境正选择，负向=被淘汰</div></div>';
    }

    // 落盘状态
    if (result.lineage_written !== undefined) {
      html += '<div style="font-size:10px;color:var(--dim);margin-top:4px">'
        + (result.lineage_written ? '✅ 谱系已落盘到 AgentProfile' : '📝 谱系仅存于本次演练')
        + '</div>';
    }

    box.innerHTML = html;
  }

  // ═══ 3D 种群投放：演练结果直接注入办公室场景（3D 窗口永不空置） ═══
  // 不依赖左栏团队筛选/轮询——初代生物立即落位，后代经 eco_mate 在回放中出生。
  function _seedSceneRoster(result) {
    if (!window.OfficeAPI || !window.OfficeAPI.dispatch) return;
    var ranking = (result && result.final_ranking) || [];
    if (!ranking.length) return;
    // 重跑前先复位：清上一场的新生个体、恢复血量/存活/意图（死者透明度由场景侧按 ecoAlive 恢复）
    try { window.OfficeAPI.dispatch({ type: 'eco_reset' }); } catch (e) {}
    var gen0 = ranking.filter(function (r) { return !r.generation; });
    var roster = (gen0.length ? gen0 : ranking).map(function (r) {
      // 用 agent_id 的可读部分作名称（build_architect → architect）
      var shortName = r.agent_id.replace(/^(build|aws|pet|ai|energy)_/, '');
      return { id: r.agent_id, name: shortName, role: r.role || 'creature',
               team: r.population || 'eco_habitat',
               skills: r.skill_genome || [] };   // v2.3 按种群分组 + 技能标签
    });
    try {
      window.__ECO_REPLAY_ACTIVE__ = true;   // 暂停 office-boot 团队轮询（保护后代/死亡状态）
      window.OfficeAPI.dispatch({ type: 'team_reset', agents: roster, noBreaks: true });
      window.OfficeAPI.dispatch({ type: 'trial_status', status: 'running' });   // 镜像层 + 不摸鱼
      // 开始演练 → 所有生物立即归位（打断咖啡/跑步机/马桶，回到各自工位）
      roster.forEach(function (a) {
        window.OfficeAPI.dispatch({ type: 'activity', agentId: a.id, activity: 'working' });
      });
      // 初始生境状态：满血活体，等回放逐帧驱动
      var updates = {};
      roster.forEach(function (a) { updates[a.id] = { health: 100, survivalTicks: 0, alive: true }; });
      window.OfficeAPI.dispatch({ type: 'eco_health', updates: updates });
      window.OfficeAPI.dispatch({ type: 'cat_say', text: '🐈 生境开张：' + roster.length + ' 个生物入场，环境开始选择…' });
    } catch (e) { /* 观测层不阻塞 */ }
  }

  // ═══ v2.4 🏟 锦标赛裁决（各队黄金适者对决 → 冠军团队） ═══
  function _tournamentReportHtml() {
    var entries = _tournament.entries.filter(function (e) { return !e.error; }).map(function (e) {
      var ranking = (e.result && e.result.final_ranking) || [];
      var champ = ranking[0] || null;
      var alive = ranking.filter(function (x) { return x.alive; }).length;
      var avg = ranking.length
        ? Math.round(ranking.reduce(function (s, x) { return s + x.survival_ticks; }, 0) / ranking.length * 10) / 10 : 0;
      return { name: e.name, id: e.id, champ: champ, alive: alive, total: ranking.length,
               avg: avg, best: (e.result && e.result.best_survival_ticks) || (champ && champ.survival_ticks) || 0,
               gens: (e.result && e.result.total_generations) || 0 };
    }).sort(function (a, b) { return b.avg - a.avg; });
    var failedEntries = _tournament.entries.filter(function (e) { return e.error; });

    var html = '<div style="font-size:12px;color:#8b9ab5;margin-bottom:12px;line-height:1.8">'
      + '🏟 分场锦标赛：' + entries.length + ' 个种群在<b>同一环境配置</b>下各自独立演练——'
      + '同样的生态位规则、代谢红线与选择压力，唯一的差别是各队自己的技能结构与协作基因。'
      + '<b style="color:#f59e0b">平均生存时长 = 团队协作竞争力</b>。</div>';
    if (failedEntries.length) {
      html += '<div style="font-size:11px;color:#f87171;margin-bottom:10px">⚠ ' + failedEntries.length + ' 场失败已跳过：'
        + failedEntries.map(function (e) { return esc(e.name); }).join('、') + '</div>';
    }

    html += '<div style="margin-bottom:14px"><b style="color:#22d3ee;font-size:13px">👑 冠军团队裁决</b>'
      + '<table style="width:100%;font-size:11px;margin-top:6px;border-collapse:collapse">'
      + '<tr style="color:#8b9ab5;text-align:left"><th style="padding:3px">名次</th><th>种群</th><th>平均生存</th><th>存活</th><th>世代</th><th>黄金适者</th><th></th></tr>'
      + entries.map(function (e, i) {
        return '<tr style="border-top:1px solid rgba(255,255,255,.08)' + (i === 0 ? ';color:#f59e0b;font-weight:700' : '') + '">'
          + '<td style="padding:4px 3px">' + (i + 1) + '</td>'
          + '<td>' + esc(e.name) + '</td>'
          + '<td>' + e.avg + 't</td>'
          + '<td>' + e.alive + '/' + e.total + '</td>'
          + '<td>' + e.gens + '</td>'
          + '<td>' + (e.champ ? '🏅 ' + esc(e.champ.agent_id) + ' (' + e.champ.survival_ticks + 't'
              + (e.champ.alive ? '·存活' : '·已淘汰') + ')' : '—') + '</td>'
          + '<td>' + (i === 0 ? '👑 冠军团队' : (e.alive === 0 ? '💀 全灭' : '')) + '</td></tr>';
      }).join('')
      + '</table></div>';

    // 各队黄金适者的基因对比（为什么冠军是冠军）
    html += '<div style="margin-bottom:12px"><b style="color:#22d3ee;font-size:13px">🧬 黄金适者基因对比</b>'
      + entries.map(function (e) {
        if (!e.champ) return '';
        var cg = e.champ.collab_genome || {};
        return '<div style="font-size:11px;padding:4px 0;border-top:1px solid rgba(255,255,255,.06);line-height:1.7">'
          + '<b>' + esc(e.name) + '</b> 的适者 <b style="color:#f59e0b">' + esc(e.champ.agent_id) + '</b>'
          + '<br>技能基因：' + (e.champ.skill_genome || []).slice(0, 5).map(function (s) { return esc(_sk(s)); }).join('、')
          + '<br>协作基因：' + COLLAB_DIMS.map(function (d) {
              return d[1] + ' ' + (cg[d[0]] != null ? cg[d[0]] : '—');
            }).join(' · ')
          + '</div>';
      }).join('') + '</div>';

    // 世代演化曲线对比（各队并排）
    var allGens = entries.map(function (e) {
      return { name: e.name, gens: (e.result && e.result.generations) || [] };
    });
    var maxGenLen = Math.max.apply(null, allGens.map(function (t) { return t.gens.length; }).concat([1]));
    var maxBest = Math.max.apply(null, allGens.flatMap(function (t) { return t.gens.map(function (g) { return g.best_survival_ticks || 0; }); }).concat([1]));
    var teamColors = ['#f59e0b', '#22d3ee', '#a78bfa', '#22c55e'];
    html += '<div style="margin-bottom:14px"><b style="color:#22d3ee;font-size:13px">📊 世代演化对比</b>'
      + '<div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap">';
    allGens.forEach(function (t, ti) {
      var color = teamColors[ti % teamColors.length];
      html += '<div style="flex:1;min-width:200px">'
        + '<div style="font-size:10px;color:' + color + ';margin-bottom:4px;font-weight:600">🏳 ' + esc(t.name) + '</div>'
        + '<div style="display:flex;align-items:flex-end;gap:3px;height:70px">';
      for (var gi = 0; gi < maxGenLen; gi++) {
        var g = t.gens[gi];
        if (!g) { html += '<div style="width:20px"></div>'; continue; }
        var h = Math.max(8, Math.round((g.best_survival_ticks || 0) / maxBest * 60));
        var ha = Math.max(4, Math.round((g.avg_survival_ticks || 0) / maxBest * 60));
        html += '<div style="width:24px;height:' + h + 'px;background:' + color + ';border-radius:3px 3px 0 0;position:relative" title="G' + g.generation + ' 最长' + g.best_survival_ticks + 't / 平均' + g.avg_survival_ticks + 't">'
          + '<div style="position:absolute;bottom:0;left:0;right:0;height:' + ha + 'px;background:rgba(255,255,255,.3);border-radius:3px"></div>'
          + '<span style="position:absolute;top:-14px;left:0;right:0;text-align:center;font-size:8px;color:#8b9ab5">' + (g.best_survival_ticks || 0) + '</span>'
          + '</div>';
      }
      html += '</div><div style="display:flex;gap:3px;margin-top:2px">';
      for (var gi2 = 0; gi2 < maxGenLen; gi2++) { html += '<div style="width:24px;text-align:center;font-size:8px;color:#8b9ab5">G' + gi2 + '</div>'; }
      html += '</div></div>';
    });
    html += '</div>'
      + '<div style="font-size:9px;color:#8b9ab5;margin-top:4px">柱高=最长生存，内层浅色=平均生存。对比各队在同一环境下的世代走势。</div>'
      + '</div>';

    html += '<div style="font-size:10px;color:#8b9ab5">读法：冠军团队不是被打分打出来的——同一个环境，谁的种群整体活得久，谁就是适者。'
      + '想看单场细节：先切到该队再点回放条 📜。</div>';
    return html;
  }

  // ═══ XV-2: ① 分场锦标赛——家族精英阶梯 + 多样性/近交告警 ═══
  function _divisionEliteLadderHtml(ranking, gens) {
    if (!ranking || !ranking.length) return '';
    var html = '<div style="margin-bottom:14px"><b style="color:#f59e0b;font-size:13px">🏅 家族精英阶梯（Elite Ladder）</b>'
      + '<div style="font-size:10px;color:#8b9ab5;margin:4px 0">队内个体按生存时长降序——家族内部的精英识别。'
      + '近交+漂移+同类选配是单团队演化的遗传学特征。</div>';

    // 精英阶梯 top-k（最多 10）
    var ladder = ranking.slice().sort(function (a, b) { return b.survival_ticks - a.survival_ticks; }).slice(0, 10);
    html += '<table style="width:100%;font-size:11px;border-collapse:collapse">'
      + '<tr style="color:#8b9ab5;text-align:left"><th style="padding:3px">名次</th><th>精英</th><th>Tᵢ</th><th>skill|协作|残差</th><th>技能基因</th><th>判读</th></tr>'
      + ladder.map(function (x, i) {
        var sk = x.attr_skill_share != null ? x.attr_skill_share : null;
        var co = x.attr_collab_share != null ? x.attr_collab_share : null;
        var re = x.attr_residual_share != null ? x.attr_residual_share : null;
        var bar = '';
        if (sk != null) {
          bar = '<span title="skill ' + Math.round(sk * 100) + '% / 协作 ' + Math.round(co * 100)
            + '% / 残差 ' + Math.round(re * 100) + '%" style="display:inline-flex;width:72px;height:8px;border-radius:2px;overflow:hidden;vertical-align:middle">'
            + '<i style="width:' + Math.round(sk * 100) + '%;background:#22d3ee"></i>'
            + '<i style="width:' + Math.round(co * 100) + '%;background:#a78bfa"></i>'
            + '<i style="width:' + Math.round(re * 100) + '%;background:#64748b"></i></span>'
            + ' <span style="font-size:9px;color:#8b9ab5">' + Math.round(sk * 100) + '/' + Math.round(co * 100) + '/' + Math.round(re * 100) + '</span>';
        } else {
          bar = '<span style="color:#8b9ab5;font-size:9px">—</span>';
        }
        return '<tr style="border-top:1px solid rgba(255,255,255,.08)' + (i === 0 ? ';color:#f59e0b;font-weight:700' : '') + '">'
          + '<td style="padding:4px 3px">' + (i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : (i + 1)) + '</td>'
          + '<td>' + esc(x.agent_id.replace(/^(build|aws|pet|ai|energy)_/, '')) + '</td>'
          + '<td style="color:#f59e0b;font-weight:600">' + x.survival_ticks + 't</td>'
          + '<td style="font-size:9px">' + bar + '</td>'
          + '<td style="color:#8b9ab5">' + (x.skill_genome || []).slice(0, 4).map(function (s) { return esc(_sk(s)); }).join('、')
          + ((x.skill_genome || []).length > 4 ? '…' : '') + '</td>'
          + '<td style="font-size:9px;color:#8b9ab5;max-width:160px">' + esc(x.attr_explain || '') + '</td></tr>';
      }).join('')
      + '</table>'
      + '<div style="font-size:9px;color:#8b9ab5;margin-top:4px">青=skill 主因 · 紫=协作主因 · 灰=残差；三者对 Tᵢ 归一（skill+协作+残差=100%）</div>';

    // 家族多样性指数（随世代变化）
    if (gens && gens.length) {
      var diversitySeries = _computeDiversitySeries(gens, ranking);
      html += '<div style="margin-top:10px"><b style="color:#22d3ee;font-size:12px">🧬 家族多样性指数</b>'
        + '<div style="font-size:10px;color:#8b9ab5;margin:2px 0">存活个体不同 skill 数 / 初代不同 skill 数——'
        + '近交会让多样性单调下降，跌破 0.5 触发近交衰退告警。</div>';
      // 迷你趋势线
      var maxD = Math.max.apply(null, diversitySeries.map(function (d) { return d.value; }).concat([1]));
      html += '<div style="display:flex;align-items:flex-end;gap:3px;height:50px;margin:6px 0">';
      diversitySeries.forEach(function (d) {
        var h = Math.round((d.value / maxD) * 100);
        var color = d.value < 0.5 ? '#f87171' : d.value < 0.7 ? '#f59e0b' : '#22c55e';
        html += '<div style="flex:1;min-width:20px;text-align:center">'
          + '<div style="height:' + h + '%;background:' + color + ';border-radius:2px 2px 0 0;min-height:2px" title="G' + d.gen + ': ' + d.value.toFixed(2) + '"></div>'
          + '<div style="font-size:8px;color:#8b9ab5;margin-top:2px">G' + d.gen + '</div>'
          + '</div>';
      });
      html += '</div>';
      // 近交衰退告警
      var lastDiv = diversitySeries.length ? diversitySeries[diversitySeries.length - 1].value : 1;
      var firstDiv = diversitySeries.length ? diversitySeries[0].value : 1;
      if (lastDiv < 0.5) {
        html += '<div style="font-size:11px;color:#f87171;padding:6px 8px;background:rgba(248,113,113,.08);border-radius:6px;margin-top:4px">'
          + '⚠ 近交衰退：家族基因多样性降至 ' + lastDiv.toFixed(2) + '（阈值 0.50）——'
          + '建议引入外队血系（多队对抗 / 混合竞争）打破近交叉锁。</div>';
      } else if (diversitySeries.length >= 2 && lastDiv < firstDiv * 0.7) {
        html += '<div style="font-size:11px;color:#f59e0b;padding:6px 8px;background:rgba(245,158,11,.06);border-radius:6px;margin-top:4px">'
          + '📉 多样性下降：从 ' + firstDiv.toFixed(2) + ' 降至 ' + lastDiv.toFixed(2)
          + '——奠基者效应主导，技能池在收窄。持续近交将加速衰退。</div>';
      } else {
        html += '<div style="font-size:10px;color:#22c55e;margin-top:4px">✓ 多样性健康（' + lastDiv.toFixed(2) + '）——'
          + '盲目学习或漂移引入了新 skill，近交压力尚可控。</div>';
      }
      html += '</div>';
    }
    html += '</div>';
    return html;
  }

  // ═══ XV-3: ② 多队对抗——coordination_lift + 排兵策略对比 ═══
  function _confrontationMatchupHtml(r, ranking, stats, pops) {
    var html = '<div style="margin-bottom:14px"><b style="color:#22d3ee;font-size:13px">⚔️ 多队对抗 · 排兵布阵策略对比</b>'
      + '<div style="font-size:10px;color:#8b9ab5;margin:4px 0">田忌赛马只是一个例子——以下 7 种策略对同一批 survival_ticks 做不同排布，'
      + '局分差异揭示团队的能力性格（厚/尖/稳/专/脆/纯运气）。策略只管「怎么排」，胜负永远由已产出的生存时长决定。</div>';

    // coordination_lift（配合净收益 = 团队实际平均 survival − 单飞基线）
    // 单飞基线用全部个体的平均 survival 近似（无对照微跑时）
    var allAvg = ranking.length
      ? ranking.reduce(function (s, x) { return s + x.survival_ticks; }, 0) / ranking.length
      : 0;
    html += '<div style="margin-bottom:10px"><b style="color:#f59e0b;font-size:12px">🤝 coordination_lift（队内配合净收益）</b>'
      + '<table style="width:100%;font-size:11px;border-collapse:collapse;margin-top:4px">'
      + '<tr style="color:#8b9ab5;text-align:left"><th style="padding:3px">种群</th><th>实际均值</th><th>单飞基线</th><th>lift</th><th>判读</th></tr>';
    pops.forEach(function (pop) {
      var s = stats[pop] || {};
      var actual = s.avg_survival_ticks || 0;
      // 单飞基线: 该队个体 survival 的均值 vs 全局均值（近似）
      var teamMembers = ranking.filter(function (x) { return x.population === pop; });
      var teamAvg = teamMembers.length
        ? teamMembers.reduce(function (s2, x) { return s2 + x.survival_ticks; }, 0) / teamMembers.length
        : 0;
      var lift = actual - allAvg;
      var liftColor = lift > 0 ? '#22c55e' : lift < 0 ? '#f87171' : '#8b9ab5';
      var judge = lift > 2 ? '配合增益（协作被环境正选择）'
        : lift < -2 ? '利他负担（协作在该环境净亏）'
        : '中性（协作无明显收支）';
      html += '<tr style="border-top:1px solid rgba(255,255,255,.08)">'
        + '<td style="padding:3px">' + esc(pop) + '</td>'
        + '<td>' + actual.toFixed(1) + 't</td>'
        + '<td style="color:#8b9ab5">' + allAvg.toFixed(1) + 't</td>'
        + '<td style="color:' + liftColor + ';font-weight:600">' + (lift >= 0 ? '+' : '') + lift.toFixed(1) + 't</td>'
        + '<td style="font-size:10px;color:' + liftColor + '">' + judge + '</td></tr>';
    });
    html += '</table>'
      + '<div style="font-size:9px;color:#8b9ab5;margin-top:2px">注：单飞基线用全局均值近似（无对照微跑）。lift>0 = 配合被环境正选择。</div>'
      + '</div>';

    // 排兵策略对比（取前两个种群做 1v1）
    if (pops.length >= 2 && window.runAllMatchupStrategies) {
      var popA = pops[0], popB = pops[1];
      var teamA = ranking.filter(function (x) { return x.population === popA; })
        .sort(function (a, b) { return b.survival_ticks - a.survival_ticks; });
      var teamB = ranking.filter(function (x) { return x.population === popB; })
        .sort(function (a, b) { return b.survival_ticks - a.survival_ticks; });
      if (teamA.length && teamB.length) {
        var ctx = {
          laneDemands: (r.env && r.env.demanded_skills) || null,
          nicheCapacity: (r.env && r.env.niche_capacity) || 0,
          env: r.env || {}
        };

        // v3: A策略 vs B策略（各队选定的策略对位）
        var stratA = _getTeamStrategy(window._selectedTeamId) || 'head_on';
        var stratB = _getTeamStrategy(_rivalTeams.length ? _rivalTeams[0].id : '') || 'head_on';
        var sA = window.getMatchupStrategy ? window.getMatchupStrategy(stratA) : null;
        var sB = window.getMatchupStrategy ? window.getMatchupStrategy(stratB) : null;
        if (sA && sB) {
          // A 用自己的策略排列（看到 B 的 ranking 但不是 B 的排列）
          var lanesA = sA.arrange(teamA, teamB, ctx);
          // B 用自己的策略排列（看到 A 的 ranking 但不是 A 的排列）
          var lanesB = sB.arrange(teamB, teamA, ctx);
          // 合并：按 lane 对位（A 的第 i lane 的 mine vs B 的第 i lane 的 mine）
          var n = Math.min(lanesA.length, lanesB.length);
          var abLanes = [];
          for (var li = 0; li < n; li++) {
            abLanes.push({
              lane: li + 1,
              a: lanesA[li].mine,
              b: lanesB[li].mine
            });
          }
          // 局分裁定
          var abW = 0, abL = 0, abD = 0;
          var laneDetail = '';
          for (var li2 = 0; li2 < abLanes.length; li2++) {
            var ln = abLanes[li2];
            var aT = ln.a ? ln.a.survival_ticks : 0;
            var bT = ln.b ? ln.b.survival_ticks : 0;
            var win = aT > bT ? 'A' : aT < bT ? 'B' : 'D';
            if (win === 'A') abW++; else if (win === 'B') abL++; else abD++;
            laneDetail += '<div style="font-size:10px;padding:2px 0;border-top:1px solid rgba(255,255,255,.04)">'
              + '<b>L' + ln.lane + '</b> '
              + (ln.a ? esc(ln.a.agent_id.replace(/^(build|aws|pet|ai|energy)_/, '')) : '—') + '(' + aT + 't)'
              + ' vs '
              + (ln.b ? esc(ln.b.agent_id.replace(/^(build|aws|pet|ai|energy)_/, '')) : '—') + '(' + bT + 't)'
              + ' → <b style="color:' + (win === 'A' ? '#22c55e' : win === 'B' ? '#f87171' : '#8b9ab5') + '">'
              + (win === 'A' ? esc(popA) + ' 胜' : win === 'B' ? esc(popB) + ' 胜' : '平') + '</b></div>';
          }
          var abColor = abW > abL ? '#22c55e' : abW < abL ? '#f87171' : '#8b9ab5';
          html += '<div style="margin-bottom:10px;padding:10px;background:rgba(245,158,11,.06);border:1px solid rgba(245,158,11,.2);border-radius:8px">'
            + '<b style="color:#f59e0b;font-size:12px">⚔️ 策略对位（' + esc(sA.icon) + ' ' + esc(sA.name) + ' vs ' + esc(sB.icon) + ' ' + esc(sB.name) + '）</b>'
            + '<div style="font-size:11px;margin:6px 0">' + esc(popA) + ' <b style="color:' + abColor + '">' + abW + '</b> - '
            + abL + ' - ' + abD + ' ' + esc(popB)
            + ' <span style="color:' + abColor + ';font-weight:600">'
            + (abW > abL ? '← ' + esc(popA) + ' 胜' : abW < abL ? '← ' + esc(popB) + ' 胜' : '← 平局') + '</span></div>'
            + laneDetail
            + '<div style="font-size:9px;color:#8b9ab5;margin-top:4px">每队用自己选定的排兵策略排列，逐 lane 对位比 survival_ticks。'
            + '改策略重跑可看不同对位效果。</div></div>';
        }

        // 全策略对比矩阵（what-if 参考）
        var results = window.runAllMatchupStrategies(teamA, teamB, ctx);
        html += '<div style="margin-bottom:10px"><b style="color:#f59e0b;font-size:12px">🔀 全策略对比（' + esc(popA) + ' vs ' + esc(popB) + '）</b>'
          + '<table style="width:100%;font-size:11px;border-collapse:collapse;margin-top:4px">'
          + '<tr style="color:#8b9ab5;text-align:left"><th style="padding:3px">策略</th><th>局分 W-L-D</th><th>vs head_on</th><th>vs random</th></tr>';
        var headOnW = 0, randomW = 0;
        results.forEach(function (r2) {
          if (r2.id === 'head_on') headOnW = r2.w;
          if (r2.id === 'random') randomW = r2.w;
        });
        results.forEach(function (r2) {
          var delta = (r2.w - headOnW);
          var deltaR = (r2.w - randomW);
          var dColor = delta > 0 ? '#22c55e' : delta < 0 ? '#f87171' : '#8b9ab5';
          var dRColor = deltaR > 0.5 ? '#22c55e' : deltaR < -0.5 ? '#f87171' : '#8b9ab5';
          html += '<tr style="border-top:1px solid rgba(255,255,255,.08)">'
            + '<td style="padding:3px">' + (r2.icon || '') + ' ' + esc(r2.name) + (r2.isExpected ? ' <span style="color:#8b9ab5;font-size:9px">(期望)</span>' : '') + '</td>'
            + '<td><b>' + r2.w.toFixed(r2.isExpected ? 2 : 0) + '</b>-' + r2.l.toFixed(r2.isExpected ? 2 : 0) + '-' + r2.d.toFixed(r2.isExpected ? 2 : 0) + '</td>'
            + '<td style="color:' + dColor + '">' + (delta >= 0 ? '+' : '') + delta.toFixed(2) + '</td>'
            + '<td style="color:' + dRColor + '">' + (deltaR >= 0 ? '+' : '') + deltaR.toFixed(2) + '</td></tr>';
        });
        html += '</table>';

        // 能力性格诊断
        if (window.diagnoseMatchupPersonality) {
          var diag = window.diagnoseMatchupPersonality(results);
          html += '<div style="margin-top:8px;padding:8px;background:rgba(167,139,250,.06);border-radius:6px">'
            + '<b style="color:#a78bfa;font-size:11px">🔮 能力性格诊断</b>';
          diag.forEach(function (d) {
            html += '<div style="font-size:11px;margin-top:4px;color:' + d.color + '"><b>' + esc(d.tag) + '</b> — '
              + esc(d.desc) + '</div>';
          });
          html += '</div>';
        }
        html += '</div>';
      }
    }
    html += '</div>';
    return html;
  }

  // XV-3: 计算每代多样性指数 = 该代存活个体不同 skill 数 / 初代不同 skill 数
  function _computeDiversitySeries(gens, ranking) {
    if (!gens || !gens.length) return [];
    // 初代 skill 集合（从 ranking 中 generation=0 的个体）
    var gen0Skills = {};
    (ranking || []).forEach(function (r) {
      if (!r.generation) (r.skill_genome || []).forEach(function (s) { gen0Skills[s] = 1; });
    });
    var gen0Count = Object.keys(gen0Skills).length || 1;

    // 逐代：用 generations 里的 living + 该代存活个体的 skill（从 ranking 近似）
    // generations 可能不携带 per-gen skill 快照，用 ranking 的 generation 字段分组
    var byGen = {};
    (ranking || []).forEach(function (r) {
      var g = r.generation || 0;
      if (!byGen[g]) byGen[g] = {};
      (r.skill_genome || []).forEach(function (s) { byGen[g][s] = 1; });
    });
    var series = [];
    for (var g = 0; g <= (gens.length - 1); g++) {
      var skills = byGen[g] || {};
      var count = Object.keys(skills).length;
      series.push({ gen: g, value: count / gen0Count });
    }
    return series;
  }

  // ═══ LLM 深度分析（异步加载，不阻塞报告显示） ═══
  function _loadLlmAnalysis() {
    var box = document.getElementById('eco2-llm-analysis');
    if (!box) return;
    var body;
    if (_tournament && _tournament.done && _tournament.entries.length) {
      var entries = _tournament.entries.map(function (e) {
        var ranking = (e.result && e.result.final_ranking) || [];
        var champ = ranking[0] || {};
        return {
          name: e.name, avg: e.avg, best: e.best, alive: e.alive, total: e.total, gens: e.gens,
          champ: { agent_id: champ.agent_id, survival_ticks: champ.survival_ticks, alive: champ.alive,
                   skill_genome: champ.skill_genome, collab_genome: champ.collab_genome },
        };
      });
      body = { entries: entries, env: (_tournament.entries[0].result || {}).env || {} };
    } else if (_lastResult) {
      body = { entries: [], single_result: _lastResult, env: _lastResult.env || {} };
    } else { return; }

    _fetch('/api/v1/eco-runtime/analyze', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(function (r) { return r.json ? r.json() : r; }).then(function (d) {
      var text = (d && d.analysis) || '（分析失败）';
      var ok = d && d.ok;
      box.innerHTML = '<b style="color:#22d3ee;font-size:13px">🔍 LLM 深度分析</b>'
        + (ok ? '' : '<span style="color:#8b9ab5;font-size:9px;margin-left:6px">（降级）</span>')
        + '<div style="font-size:12px;line-height:1.8;margin-top:8px;white-space:pre-wrap;color:#d1d5db">' + esc(text) + '</div>';
    }).catch(function (e) {
      box.innerHTML = '<b style="color:#22d3ee;font-size:13px">🔍 LLM 深度分析</b>'
        + '<div style="color:#f87171;font-size:11px;margin-top:6px">分析请求失败：' + esc(e.message || e) + '</div>';
    });
  }

  // ═══ 📜 生境报告（v2.3：演练结束的裁决书） ═══
  window.eco2ShowReport = function () {
    var modal = document.getElementById('secs-report-modal');
    var content = document.getElementById('secs-report-content');
    var title = document.getElementById('secs-report-title');
    if (!modal || !content) return;
    // v2.4：锦标赛结束 → 冠军裁决报告
    if (_tournament && _tournament.done && _tournament.entries.length) {
      if (title) title.textContent = '🏟 物竞天择 · 锦标赛冠军裁决';
      content.innerHTML = _tournamentReportHtml() + '<div id="eco2-llm-analysis" style="margin-top:14px;padding:12px;background:rgba(34,211,238,.06);border:1px solid rgba(34,211,238,.2);border-radius:8px"><b style="color:#22d3ee;font-size:13px">🔍 LLM 深度分析</b><div style="color:#8b9ab5;font-size:11px;margin-top:6px">分析中…</div></div>';
      modal.style.display = 'flex';
      _loadLlmAnalysis();
      return;
    }
    var r = _lastResult;
    if (!r) { setText('eco2-run-status', '暂无演练结果——先开始一场物竞天择'); return; }
    if (title) title.textContent = '📜 物竞天择 · 生境报告';

    var env = r.env || {};
    var gens = r.generations || [];
    var ranking = r.final_ranking || [];
    var stats = r.population_stats || {};
    var pops = Object.keys(stats);
    var html = '';

    // 环境判词
    html += '<div style="font-size:12px;color:#8b9ab5;margin-bottom:14px;line-height:1.8">'
      + '本场生境：生态位 <b style="color:#22d3ee">' + (env.demanded_skills || []).slice(0, 6).map(function(x){return esc(_sk(x));}).join(' / ') + '</b>'
      + ' · 丰饶度 <b>' + (env.abundance != null ? env.abundance : '—') + '</b>'
      + ' · 捕食压力 <b>' + (env.predator_pressure != null ? env.predator_pressure : '—') + '</b>'
      + ' · 漂移 <b>' + (env.drift_prob != null ? env.drift_prob : '—') + '</b>'
      + ' · 竞争名额 <b>' + (env.niche_capacity ? env.niche_capacity : '∞') + '</b>'
      + '<br>共演化 <b style="color:#a78bfa">' + gens.length + '</b> 代 · '
      + '最长生存 <b style="color:#f59e0b">' + (r.best_survival_ticks || 0) + ' ticks</b> · '
      + '存活 <b style="color:#22c55e">' + ranking.filter(function (x) { return x.alive; }).length + '</b> / ' + ranking.length
      + '</div>';

    // 多种群竞争裁决（团队协作竞争力对比）
    if (pops.length > 1) {
      var ordered = pops.slice().sort(function (a, b) {
        return (stats[b].avg_survival_ticks || 0) - (stats[a].avg_survival_ticks || 0);
      });
      html += '<div style="margin-bottom:14px"><b style="color:#22d3ee;font-size:13px">🏆 种群竞争裁决（平均生存时长 = 协作竞争力）</b>'
        + '<table style="width:100%;font-size:11px;margin-top:6px;border-collapse:collapse">'
        + '<tr style="color:#8b9ab5;text-align:left"><th style="padding:3px">种群</th><th>存活</th><th>平均生存</th><th>最长</th><th></th></tr>'
        + ordered.map(function (pop, i) {
          var s = stats[pop];
          return '<tr style="border-top:1px solid rgba(255,255,255,.08)' + (i === 0 ? ';color:#f59e0b;font-weight:700' : '') + '">'
            + '<td style="padding:4px 3px">' + esc(pop) + '</td>'
            + '<td>' + s.alive + '/' + s.total + '</td>'
            + '<td>' + s.avg_survival_ticks + 't</td>'
            + '<td>' + s.best + 't</td>'
            + '<td>' + (i === 0 ? '👑 适者' : (s.alive === 0 ? '💀 灭绝' : '')) + '</td></tr>';
        }).join('')
        + '</table></div>';
    }

    // 🏅 个体生存排行榜（谁活得最长——全灭时也点名"最长存活者"）
    var top = ranking.slice(0, 5);
    if (top.length) {
      var champ = top[0];
      html += '<div style="margin-bottom:14px"><b style="color:#22d3ee;font-size:13px">🏅 个体生存排行</b>'
        + '<div style="font-size:11px;color:#f59e0b;margin:4px 0">'
        + (champ.alive ? '👑 最适者（仍存活）：' : '🕯 最长存活者（已淘汰）：')
        + '<b>' + esc(champ.agent_id) + '</b>'
        + (champ.population ? '（种群 ' + esc(champ.population) + '）' : '')
        + ' — ' + champ.survival_ticks + ' ticks</div>'
        + '<table style="width:100%;font-size:11px;border-collapse:collapse">'
        + '<tr style="color:#8b9ab5;text-align:left"><th style="padding:3px">#</th><th>个体</th><th>种群</th><th>生存</th><th>状态</th><th>携带基因</th></tr>'
        + top.map(function (x, i) {
          return '<tr style="border-top:1px solid rgba(255,255,255,.08)">'
            + '<td style="padding:3px">' + (i + 1) + '</td>'
            + '<td>' + esc(x.agent_id) + '</td>'
            + '<td style="color:#8b9ab5">' + esc(x.population || '—') + '</td>'
            + '<td style="color:#f59e0b;font-weight:600">' + x.survival_ticks + 't</td>'
            + '<td>' + (x.alive ? '<span style="color:#22c55e">✓ 存活</span>' : '<span style="color:#f87171">💀 淘汰</span>') + '</td>'
            + '<td style="color:#8b9ab5">' + (x.skill_genome || []).slice(0, 3).map(function(g2){return esc(_sk(g2));}).join('、')
            + ((x.skill_genome || []).length > 3 ? '…' : '') + '</td></tr>';
        }).join('')
        + '</table></div>';
    }

    // XV-2: ① 分场锦标赛专属——家族精英阶梯 + 多样性/近交告警
    if (_raceMode === 'division') {
      html += _divisionEliteLadderHtml(ranking, gens);
    }

    // XV-3: ② 多队对抗专属——coordination_lift + 排兵策略对比
    if (_raceMode === 'confrontation' && pops.length > 1) {
      html += _confrontationMatchupHtml(r, ranking, stats, pops);
    }

    // 世代纪事（含猫解说）
    html += '<div style="margin-bottom:14px"><b style="color:#22d3ee;font-size:13px">🧬 世代纪事</b>'
      + gens.map(function (g) {
        return '<div style="font-size:11px;padding:4px 0;border-top:1px solid rgba(255,255,255,.06)">'
          + '<b style="color:#a78bfa">G' + g.generation + '</b>'
          + ' 存活 ' + g.living + ' · 最长 ' + g.best_survival_ticks + 't · 平均 ' + g.avg_survival_ticks + 't'
          + ' · 新生 ' + (g.births || 0)
          + (g.drift ? ' · <span style="color:#22d3ee">⚡' + esc(g.drift.removed) + '→' + esc(g.drift.added) + '</span>' : '')
          + (g.ratchet_advanced ? ' · <span style="color:#f59e0b">🔒棘轮↑</span>' : '')
          + (g.extinct ? ' · <span style="color:#f43f5e">💀全灭</span>' : '')
          + (g.cat_commentary ? '<br><span style="color:#8b9ab5">🐈 ' + esc(g.cat_commentary) + '</span>' : '')
          + '</div>';
      }).join('') + '</div>';

    // 基因池裁决
    var gp = r.gene_pool || {};
    var dom = (gp.dominant || []).map(function (g) { return esc(_sk(g.skill)) + '×' + g.carriers; }).join('、');
    var dep = (gp.deprecated || []).map(function (g) { return esc(_sk(g.skill)); }).join('、');
    html += '<div style="margin-bottom:14px;font-size:11px;line-height:1.8"><b style="color:#22d3ee;font-size:13px">🧬 基因池裁决</b><br>'
      + '👑 被环境选中（dominant）：<span style="color:#f59e0b">' + (dom || '（无）') + '</span><br>'
      + '🪦 随死者消亡（deprecated）：<span style="color:#f87171">' + (dep || '（无）') + '</span></div>';

    // 协作画像
    var means = (r.collab_profile && r.collab_profile.means) || null;
    if (means) {
      html += '<div style="font-size:11px;line-height:1.8"><b style="color:#22d3ee;font-size:13px">🤝 幸存者协作画像</b><br>'
        + COLLAB_DIMS.map(function (d) {
          return d[1] + ' <b style="color:#22d3ee">' + (means[d[0]] != null ? means[d[0]] : '—') + '</b>';
        }).join(' · ')
        + '<br><span style="color:#8b9ab5">读法：数值是被环境选择后的种群均值——它们不是设计出来的，是活下来的。</span></div>';
    }

    // T_i 分解：skill / 协作 / 残差（以 survival_ticks 为根）
    var attMap = r.survival_attribution || {};
    var attRows = ranking.filter(function (x) { return x.attr_skill_share != null || attMap[x.agent_id]; }).slice(0, 12);
    if (attRows.length) {
      html += '<div style="margin-top:14px"><b style="color:#22d3ee;font-size:13px">🔬 存活归因（Tᵢ 分解）</b>'
        + '<div style="font-size:10px;color:#8b9ab5;margin:4px 0">唯一根 Tᵢ=生存 ticks；青=skill 主因 · 紫=协作主因 · 灰=残差；三份额之和=100%</div>'
        + '<table style="width:100%;font-size:11px;border-collapse:collapse">'
        + '<tr style="color:#8b9ab5;text-align:left"><th>Agent</th><th>Tᵢ</th><th>skill</th><th>协作</th><th>残差</th><th>判读</th></tr>';
      attRows.forEach(function (x) {
        var a = attMap[x.agent_id] || {};
        var sk = x.attr_skill_share != null ? x.attr_skill_share : a.skill_share;
        var co = x.attr_collab_share != null ? x.attr_collab_share : a.collab_share;
        var re = x.attr_residual_share != null ? x.attr_residual_share : a.residual_share;
        var ex = x.attr_explain || a.explain || '';
        html += '<tr style="border-top:1px solid rgba(255,255,255,.08)">'
          + '<td style="padding:3px">' + esc((x.agent_id || '').replace(/^(build|aws|pet|ai|energy)_/, '')) + '</td>'
          + '<td style="color:#f59e0b;font-weight:600">' + (x.survival_ticks || a.T_i || 0) + 't</td>'
          + '<td style="color:#22d3ee">' + (sk != null ? Math.round(sk * 100) + '%' : '—') + '</td>'
          + '<td style="color:#a78bfa">' + (co != null ? Math.round(co * 100) + '%' : '—') + '</td>'
          + '<td style="color:#94a3b8">' + (re != null ? Math.round(re * 100) + '%' : '—') + '</td>'
          + '<td style="font-size:9px;color:#8b9ab5">' + esc(ex) + '</td></tr>';
      });
      html += '</table></div>';
    }

    content.innerHTML = html + '<div id="eco2-llm-analysis" style="margin-top:14px;padding:12px;background:rgba(34,211,238,.06);border:1px solid rgba(34,211,238,.2);border-radius:8px"><b style="color:#22d3ee;font-size:13px">🔍 LLM 深度分析</b><div style="color:#8b9ab5;font-size:11px;margin-top:6px">分析中…</div></div>';
    modal.style.display = 'flex';
    _loadLlmAnalysis();
  };

  // ═══ 剧场回放（XT-5 接线；onDone=回放结束回调，锦标赛逐队上场用） ═══
  function _initReplay(result, onDone) {
    var timeline = result && result.timeline;
    var bar = $('eco2-replay-bar');
    _seedSceneRoster(result);
    if (!timeline || !timeline.steps || !timeline.steps.length) {
      if (bar) bar.style.display = 'none';
      if (typeof onDone === 'function') onDone();
      return;
    }
    if (_replay) _replay.destroy();
    var _doneFired = false;
    function _fireDone() {
      if (_doneFired) return;
      _doneFired = true;
      if (typeof onDone === 'function') onDone();
    }
    _replay = window.createEcoReplay(timeline, {
      onFrame: function (step, index, total) {
        var seek = $('eco2-replay-seek');
        if (seek) { seek.max = total - 1; seek.value = Math.min(index, total - 1); }
        setText('eco2-replay-label', step
          ? '第 ' + (step.generation != null ? step.generation : '?') + ' 代 · step ' + step.step
            + ' · 生态位 ' + _sk(step.demand || '—') + ' · 存活 ' + step.living
            + (step.deaths && step.deaths.length ? ' · 💀 ' + step.deaths.join(',') : '')
          : '回放结束 — 适者已被环境选出');
        // v2.3: 回放时 KPI 逐帧刷新 + 3D 左下角生态位提示
        if (step) {
          setText('eco2-kpi-gen', String(step.generation != null ? step.generation : 0));
          var total_n = (_lastResult && _lastResult.final_ranking || []).length || '—';
          setText('eco2-kpi-alive', step.living + ' / ' + total_n);
          var info = document.getElementById('env-3d-info');
          if (info) info.textContent = '🧬 生境演练 — 第 ' + (step.generation != null ? step.generation : 0)
            + ' 代 · 生态位: ' + _sk(step.demand || '—') + ' · 存活 ' + step.living;
          var legend = document.getElementById('env-3d-legend');
          if (legend) legend.style.display = 'block';
        } else if (_lastResult) {
          // 回放结束恢复终局 KPI
          eco2RenderResult(_lastResult);
          var info2 = document.getElementById('env-3d-info');
          if (info2) info2.textContent = '▣ 数字办公室 — 物竞天择演练已完成（📜 报告可回看）';
        }
        if (!step) {
          var pb = $('eco2-replay-play'); if (pb) pb.textContent = '↻';
          // 回放结束：退出镜像层 + 释放回放保护（恢复 office-boot 团队轮询，清理后代/死者残影）
          try { window.OfficeAPI && window.OfficeAPI.dispatch({ type: 'trial_status', status: 'completed' }); } catch (e) {}
          window.__ECO_REPLAY_ACTIVE__ = false;
          // v2.3：自动弹出生境报告（每场演练只弹一次；回放条 📜 可随时再看）
          if (!_reportShown) { _reportShown = true; try { window.eco2ShowReport(); } catch (e) {} }
          _fireDone();   // v2.4 锦标赛：本场回放结束 → 下一支队伍入场
        }
        if (step && _lastResult) _renderPopulation(_lastResult.final_ranking || [], step);
      },
      onEpoch: function () { /* 世代面板已按最终结果渲染 */ },
    });
    if (bar) bar.style.display = 'block';
    var seek = $('eco2-replay-seek');
    if (seek) { seek.max = timeline.steps.length - 1; seek.value = 0; }
    setText('eco2-replay-label', '回放就绪 — ' + timeline.steps.length + ' 帧');
    // 自动开始回放
    eco2ReplayToggle(true);
  }

  window.eco2ReplayToggle = function (forcePlay) {
    if (!_replay) return;
    var btn = $('eco2-replay-play');
    if (_replay.isPlaying() && forcePlay !== true) {
      _replay.pause();
      if (btn) btn.textContent = '▶';
    } else {
      _replay.play();
      if (btn) btn.textContent = '⏸';
    }
  };
  window.eco2ReplaySeek = function (v) {
    if (_replay) _replay.seek(Number(v));
  };
  window.eco2ReplaySpeed = function () {
    if (!_replay) return;
    var s = _replay.cycleSpeed();
    setText('eco2-replay-speed', s + 'x');
  };

  /** XC：供反馈台推送成本竞标读取挂接任务/契约 */
  window.eco2GetBoundTask = function () { return _boundTask; };
  window.eco2GetBoundContract = function () { return _boundContract; };

  // 办公室视图（__ECO_FIELD__）下页面加载即初始化。
  // office-boot.js（module，延迟执行）也会设该旗标；此处直接按 URL 自算，不依赖脚本时序。
  function _boot() {
    if (window.__ECO_FIELD__ == null) {
      try {
        window.__ECO_FIELD__ = new URLSearchParams(location.search).get('office3d') === '1';
      } catch (e) { window.__ECO_FIELD__ = false; }
    }
    if (window.__ECO_FIELD__ && window.applyEcoDrillMode) window.applyEcoDrillMode('eco');
    // eco2Init 可能已由 applyEcoDrillMode 触发；否则此处兜底
    try { if (window.eco2Init) window.eco2Init(); } catch (e1) { /* ignore */ }
    _renderLeftKnobs();
    try {
      var rp = document.getElementById('rp-eco');
      if (rp && typeof MutationObserver !== 'undefined') {
        new MutationObserver(function () { _renderLeftKnobs(); })
          .observe(rp, { attributes: true, attributeFilter: ['style', 'class'] });
      }
    } catch (e) { /* ignore */ }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', _boot);
  else _boot();
})();
