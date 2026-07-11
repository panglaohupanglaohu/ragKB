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

  function _fetch(url, opts) {
    var f = (typeof window._af === 'function') ? window._af : (window._agFetch || fetch);
    return f(url, opts);
  }
  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function setText(id, v) { var el = $(id); if (el) el.textContent = v; }

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

  // ═══ 初始化：读生境配置 → 滑杆/生态位 ═══
  window.eco2Init = function () {
    if (_inited) return;
    _inited = true;
    _bindSliders();
    window.ecoLoadConfig();
    _loadNichesFromTeam();
  };

  // 覆盖旧版：读配置 → 滑杆与状态条
  window.ecoLoadConfig = function () {
    _fetch('/api/v1/eco-runtime/config').then(function (r) { return r.json ? r.json() : r; })
      .then(function (cfg) {
        if (!cfg) return;
        var hab = cfg.habitat || {};
        _setSlider('eco2-env-predator', Math.round((hab.predator_pressure != null ? hab.predator_pressure : 0.08) * 100), 100);
        _setSlider('eco2-env-abundance', Math.round((hab.abundance != null ? hab.abundance : 1.0) * 100), 100);
        _setSlider('eco2-env-drift', Math.round((hab.drift_prob != null ? hab.drift_prob : 0.3) * 100), 100);
        _setSlider('eco2-env-capacity', hab.niche_capacity != null ? hab.niche_capacity : 2, 1);
        setText('eco2-env-status', '· 已加载');
      }).catch(function () { setText('eco2-env-status', '· 使用默认值'); });
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
    } else {
      out.textContent = (Number(el.value) / denom).toFixed(2).replace(/0$/, '');
    }
  }
  function _bindSliders() {
    ['eco2-env-predator', 'eco2-env-abundance', 'eco2-env-drift'].forEach(function (id) {
      var el = $(id);
      if (el) el.addEventListener('input', function () { _syncSliderVal(id, 100); });
    });
    var cap = $('eco2-env-capacity');
    if (cap) cap.addEventListener('input', function () { _syncSliderVal('eco2-env-capacity', 1); });
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
    window.eco2SaveEnv();
    setText('eco2-env-status', '· 剧本已应用并写回');
    // 选中态持久化（不受 :focus 丢失影响）
    if (btn) {
      var prev = btn.parentElement.querySelectorAll('.eco2-scenario-active');
      prev.forEach(function (el) { el.classList.remove('eco2-scenario-active'); });
      btn.classList.add('eco2-scenario-active');
    }
  };

  // 环境压力台 → 写回 habitat 配置
  window.eco2SaveEnv = function () {
    var body = {
      habitat: {
        predator_pressure: Number($('eco2-env-predator').value) / 100,
        abundance: Number($('eco2-env-abundance').value) / 100,
        drift_prob: Number($('eco2-env-drift').value) / 100,
        niche_capacity: Number(($('eco2-env-capacity') || { value: 2 }).value),
      },
    };
    _fetch('/api/v1/eco-runtime/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(function (r) {
      setText('eco2-env-status', (r && r.ok !== false) ? '· ✓ 已写回' : '· 写回失败');
    }).catch(function () { setText('eco2-env-status', '· 写回失败'); });
  };

  // 生态位 chips：选中团队的 skill 汇总（与后端 run_drill_via_trial 的需求采集一致）
  function _loadNichesFromTeam() {
    var box = $('eco2-env-niches');
    if (!box) return;
    var teamId = window._selectedTeamId;
    if (!teamId) {
      box.innerHTML = '<span style="color:var(--dim);font-size:10px">选择团队后加载生态位…</span>';
      return;
    }
    _loadTeamSkills(teamId).then(function (d) {
      var names = [];
      if (d && d.skills && typeof d.skills === 'object') {
        Object.keys(d.skills).forEach(function (sid) { names.push(_sk(sid)); });
      }
      if (!names.length && d && Array.isArray(d.agents)) {
        var set = {};
        d.agents.forEach(function (a) { (a.skills || []).forEach(function (s) { set[s] = 1; }); });
        names = Object.keys(set).map(_sk);
      }
      // 按名称去重（不同 skill ID 可能同名——如旧技能迁移后的重复条目）
      var seen = {};
      names = names.filter(function (n) { if (seen[n]) return false; seen[n] = 1; return true; });
      box.innerHTML = names.length
        ? names.slice(0, 16).map(function (n) { return '<span class="eco2-chip">' + esc(n) + '</span>'; }).join(' ')
        : '<span style="color:var(--dim);font-size:10px">该团队暂无 skill——生境将以 generic 生态位运行</span>';
    });
  }

  // 团队选中联动（secs-core 的 sexyPickTeam 会更新 window._selectedTeamName）
  setInterval(function () {
    var btn = $('eco2-run-team');
    if (btn && window._selectedTeamName && btn.textContent.indexOf(window._selectedTeamName) === -1) {
      btn.textContent = '👥 种群：' + window._selectedTeamName;
      _loadNichesFromTeam();
      // 换了种群 → 释放回放保护，恢复 office-boot 团队轮询（3D 显示新团队成员）
      window.__ECO_REPLAY_ACTIVE__ = false;
      if (_replay) { _replay.pause(); }
    }
  }, 1500);

  // ═══ v2.3 多种群同场竞争：对比种群选择 ═══
  var _rivalTeams = [];        // [{id,name}]
  var _pickingRival = false;
  var _prevPrimary = null;

  // 包装 sexySelectTeam：处于"选对比种群"模式时截获选择，不改主种群
  var _wrapTimer = setInterval(function () {
    if (typeof window.sexySelectTeam !== 'function' || window.sexySelectTeam.__ecoWrapped) return;
    var orig = window.sexySelectTeam;
    window.sexySelectTeam = function (teamId, teamName) {
      if (_pickingRival) {
        _pickingRival = false;
        if (teamId && teamId !== window._selectedTeamId
            && !_rivalTeams.some(function (t) { return t.id === teamId; })) {
          _rivalTeams.push({ id: teamId, name: teamName || teamId });
          _loadTeamSkills(teamId);   // R5: 对比种群的技能目录也进名称解析缓存
        }
        _renderRivalChips();
        // 恢复主种群选择，关闭弹窗
        if (_prevPrimary) {
          window._selectedTeamId = _prevPrimary.id;
          window._selectedTeamName = _prevPrimary.name;
        }
        var ov = document.getElementById('o-team');
        if (ov) ov.style.display = 'none';
        window._teamModalOpen = false;
        return;
      }
      return orig(teamId, teamName);
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
  };
  function _renderRivalChips() {
    var box = $('eco2-rival-chips');
    if (!box) return;
    box.innerHTML = _rivalTeams.map(function (t) {
      return '<span class="eco2-chip">' + esc(t.name)
        + ' <a href="javascript:void(0)" onclick="eco2RemoveRival(\'' + esc(t.id) + '\')" style="color:#f87171;text-decoration:none">✕</a></span>';
    }).join(' ') || '<span style="color:var(--dim);font-size:9px">（单种群演练——加入对比种群才能比出协作竞争力）</span>';
  }

  // ═══ 开始物竞天择（覆盖旧版 ecoRunDrill） ═══
  // ═══ v2.4 赛制 ═══
  // tournament（默认）：各队独立进同一环境各自演练→各出黄金适者→冠军团队裁决（用户的"恐龙队 vs 人类队"语义）
  // melee：全部种群进同一生境直接竞争（依赖后端多种群代码）
  var _raceMode = 'tournament';
  var _tournament = null;   // {entries:[{id,name,result}], done:bool}
  window.eco2SetRaceMode = function (m) {
    _raceMode = m === 'melee' ? 'melee' : 'tournament';
    setText('eco2-race-hint', _raceMode === 'melee'
      ? '所有种群进同一生境直接竞争（同一生态位抢名额）'
      : '各队独立进同一环境演练，各出黄金适者，最后裁决冠军团队');
  };

  function _createAndRunDrill(teamId, extraIds, maxSteps, maxGens) {
    return _fetch('/api/v1/twin-trials', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        mode: 'evolutionary',
        max_steps: maxSteps,
        max_generations: maxGens || 3,
        drill_kind: 'natural_selection',
        task_goal: {
          name: '物竞天择-' + Date.now().toString(36),
          extra_team_ids: extraIds || [],
        },
      }),
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
      finish();
    };
    // 安全超时：120 秒后强制恢复按钮（防止后端卡死时前端永久等待）
    var _safetyTimer = setTimeout(function () {
      setText('eco2-run-status', '❌ 演练超时（120s）— 请检查后端服务');
      finish();
    }, 120000);

    // ── ⚔️ 同场混战 ──
    if (_raceMode === 'melee' || !_rivalTeams.length) {
      setText('eco2-run-status', '🧬 生境运行中：代谢红线 · 受限感知 · 信号协议 · 世代繁衍');
      var _drillStart = Date.now();
      _createAndRunDrill(window._selectedTeamId,
        _raceMode === 'melee' ? _rivalTeams.map(function (t) { return t.id; }) : [],
        maxSteps, maxGens
      ).then(function (result) {
        // 最小展示 600ms，让用户看到"运行中"状态（演练太快会误以为没跑）
        var _elapsed = Date.now() - _drillStart;
        var _delay = _elapsed < 600 ? 600 - _elapsed : 0;
        setTimeout(function () {
          var tid = (result.trial_id || '').slice(0, 8);
          if (_raceMode === 'melee' && _rivalTeams.length
              && (!result.populations || result.populations.length < 2)) {
            setText('eco2-run-status', '⚠ 对比种群未进入生境——请重启后端（./start.sh）加载多种群演练代码后重试');
          } else {
            setText('eco2-run-status', '✅ 新演练完成 (#' + tid + ') — 回放中，拖动进度条可回顾');
          }
          finish();
          _playResultAndWait(result, false);
        }, _delay);
      }).catch(fail);
      return;
    }

    // ── 🏟 分场锦标赛：各队独立进同一环境，依次上场演练 ──
    var teams = [{ id: window._selectedTeamId, name: window._selectedTeamName || window._selectedTeamId }]
      .concat(_rivalTeams.map(function (t) { return { id: t.id, name: t.name }; }));
    _tournament = { entries: [], done: false };
    var idx = 0;
    function nextTeam() {
      if (idx >= teams.length) {
        _tournament.done = true;
        setText('eco2-run-status', '🏟 锦标赛结束 — ' + teams.length + ' 个种群完成演练，查看冠军裁决');
        finish();
        _reportShown = true;
        try { window.eco2ShowReport(); } catch (e) {}
        return;
      }
      var t = teams[idx];
      setText('eco2-run-status', '🏟 锦标赛 第 ' + (idx + 1) + '/' + teams.length + ' 场 — 种群「' + t.name + '」入场演练…');
      _loadTeamSkills(t.id).then(function () {
        return _createAndRunDrill(t.id, [], maxSteps, maxGens);
      }).then(function (result) {
        _tournament.entries.push({ id: t.id, name: t.name, result: result });
        setText('eco2-run-status', '🏟 第 ' + (idx + 1) + '/' + teams.length + ' 场回放中 — 种群「' + t.name + '」');
        return _playResultAndWait(result, true);   // 逐场回放，压制单场报告
      }).then(function () {
        idx += 1;
        nextTeam();
      }).catch(function (err) {
        // 单场失败不中断整个锦标赛——记录错误，跳到下一队
        console.error('[eco2] 第' + (idx + 1) + '场失败:', err);
        _tournament.entries.push({ id: t.id, name: t.name, error: err.message || String(err) });
        idx += 1;
        if (idx < teams.length) {
          setText('eco2-run-status', '⚠ 第' + idx + '场失败已跳过—继续第' + (idx + 1) + '场');
          nextTeam();
        } else {
          // 全部跑完（含失败场次）
          _tournament.done = true;
          var okCount = _tournament.entries.filter(function (e) { return !e.error; }).length;
          setText('eco2-run-status', '🏟 锦标赛结束 — ' + okCount + '/' + teams.length + ' 场成功');
          finish();
          _reportShown = true;
          try { window.eco2ShowReport(); } catch (e) {}
        }
      });
    }
    nextTeam();
  };
  // 旧入口兼容（rp-eco 旧按钮/外部调用）
  window.ecoRunDrill = window.eco2RunDrill;

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

    // ② 生态位（演练后环境可能已漂移 → 用 result.env 刷新）
    if (result.env && result.env.demanded_skills) {
      var nb = $('eco2-env-niches');
      if (nb) {
        var _seen = {};
        var _names = result.env.demanded_skills.map(_sk).filter(function (n) {
          if (_seen[n]) return false; _seen[n] = 1; return true;
        });
        nb.innerHTML = _names.slice(0, 16).map(function (n) {
          return '<span class="eco2-chip">' + esc(n) + '</span>';
        }).join(' ');
      }
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
    return '<div class="eco2-pop-row' + (alive ? '' : ' dead') + '">'
      + '<span style="width:14px;text-align:center" title="' + (act.outcome === 'outcompeted' ? '竞争失败：有能力但没抢到生态位名额' : '') + '">' + icon + '</span>'
      + '<span class="eco2-pop-name" title="' + esc(r.agent_id) + '">' + esc(r.agent_id) + '</span>'
      + '<span class="eco2-hpbar"><i style="width:' + Math.round(ratio * 100) + '%;background:' + hpColor + '"></i></span>'
      + '<span style="min-width:38px;color:var(--amber);font-weight:600">' + ticks + 't</span>'
      + '<span class="eco2-collab-mini" style="height:14px" title="协作基因 分享/信号/跟随/择偶">' + collabBars + '</span>'
      + '<span style="flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">' + genome + '</span>'
      + '</div>';
  }

  // ⑤ 世代曲线 + 记录
  function _renderGenerations(gens) {
    var chart = $('eco2-gen-chart'), list = $('eco2-gen-list');
    if (chart) {
      var maxBest = Math.max.apply(null, gens.map(function (g) { return g.best_survival_ticks || 1; }).concat([1]));
      chart.innerHTML = gens.map(function (g) {
        var h = Math.max(8, Math.round((g.best_survival_ticks || 0) / maxBest * 56));
        var ha = Math.max(4, Math.round((g.avg_survival_ticks || 0) / maxBest * 56));
        return '<div class="eco2-genbar" style="height:' + h + 'px" title="G' + g.generation + ' 最长 ' + g.best_survival_ticks + 't / 平均 ' + g.avg_survival_ticks + 't">'
          + '<div style="position:absolute;bottom:0;left:0;right:0;height:' + ha + 'px;background:rgba(255,255,255,.25);border-radius:2px"></div>'
          + '<span class="lbl">G' + g.generation + (g.drift ? '⚡' : '') + '</span></div>';
      }).join('') || '';
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

  // ⑦ 繁衍谱系
  function _renderLineage(result) {
    var box = $('eco2-lineage');
    if (!box) return;
    var rows = [];
    
    // 优先显示 result.lineage（包含完整谱系信息）
    var lineage = result.lineage || [];
    var epochs = result.timeline && result.timeline.epochs || [];
    
    // 显示谱系记录
    lineage.forEach(function (rec) {
      rows.push('<div style="padding:3px 2px;border-bottom:1px dashed var(--border)">'
        + '<b style="color:var(--purple)">G' + rec.generation + '</b> '
        + '<b style="color:var(--green)">' + esc(rec.child) + '</b>'
        + '<br><span style="color:var(--dim)">↳ 双亲: ' + (rec.parents || []).slice(0, 2).map(esc).join(' × ') + '</span>'
        + '<br><span style="color:var(--dim)">↳ 基因: </span>' + (rec.skill_genome || []).slice(0, 5).map(function (s) {
          return '<span class="eco2-chip">' + esc(String(s).slice(0, 12)) + '</span>';
        }).join(' ')
        + '</div>');
    });
    
    // 如果没有谱系记录，显示 timeline.epochs 中的谱系
    if (!rows.length) {
      epochs.forEach(function (ep) {
        (ep.offspring || []).forEach(function (child) {
          var genome = (ep.offspring_genomes && ep.offspring_genomes[child]) || [];
          rows.push('<div style="padding:3px 2px;border-bottom:1px dashed var(--border)">'
            + '<b style="color:var(--purple)">G' + ep.generation + '</b> '
            + '<b style="color:var(--green)">' + esc(child) + '</b>'
            + '<br><span style="color:var(--dim)">↳ 双亲: ' + (ep.parents || []).slice(0, 2).map(esc).join(' × ') + '</span>'
            + '<br><span style="color:var(--dim)">↳ 基因: </span>' + genome.slice(0, 5).map(function (s) {
              return '<span class="eco2-chip">' + esc(String(s).slice(0, 12)) + '</span>';
            }).join(' ')
            + '</div>');
        });
      });
    }
    
    // 显示谱系落盘状态
    var lineageWritten = result.lineage_written;
    var statusText = '';
    if (lineageWritten !== undefined) {
      statusText = '<div style="font-size:10px;color:var(--dim);margin-top:4px">'
        + (lineageWritten ? '✅ 谱系已落盘到 AgentProfile' : '📝 谱系仅存于本次演练')
        + '</div>';
    }
    
    box.innerHTML = (rows.length ? rows.join('') + statusText : '<div class="eco2-empty">（本场无繁衍——可能环境过于严酷或世代数不足）</div>');
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
      window.OfficeAPI.dispatch({ type: 'team_reset', agents: roster });
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
        } else if (_lastResult) {
          // 回放结束恢复终局 KPI
          eco2RenderResult(_lastResult);
          var info2 = document.getElementById('env-3d-info');
          if (info2) info2.textContent = '▣ 数字办公室 — 物竞天择演练已完成（📜 报告可回看）';
        }
        if (!step) {
          var pb = $('eco2-replay-play'); if (pb) pb.textContent = '↻';
          // 回放结束：退出镜像层（种群保留在场景中，含存活后代与死者残影）
          try { window.OfficeAPI && window.OfficeAPI.dispatch({ type: 'trial_status', status: 'completed' }); } catch (e) {}
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

  // 办公室视图（__ECO_FIELD__）下页面加载即初始化。
  // office-boot.js（module，延迟执行）也会设该旗标；此处直接按 URL 自算，不依赖脚本时序。
  function _boot() {
    if (window.__ECO_FIELD__ == null) {
      try {
        window.__ECO_FIELD__ = new URLSearchParams(location.search).get('office3d') === '1';
      } catch (e) { window.__ECO_FIELD__ = false; }
    }
    if (window.__ECO_FIELD__ && window.applyEcoDrillMode) window.applyEcoDrillMode('eco');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', _boot);
  else _boot();
})();
