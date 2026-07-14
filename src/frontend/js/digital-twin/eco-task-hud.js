/**
 * eco-task-hud.js — XF-5 任务型考卷 HUD（办公室语言，非生物图腾）
 *
 * 决策（2026-07-14 推进）：
 *  - 载体 = 2D HUD（3D 窗口角）+ 右侧生态位 chips 高亮（非 3D 蓝柱）
 *  - 仅当已挂接 TaskHabitatContract / 任务时显示
 *  - 文案：本步所需技能 / 考卷进度；禁止裸 skill_id（走 _ecoSkillLabel）
 *  - 旧 __ECO_HABITAT_3D__ 实验图腾路径保留但不在此打开
 */
(function () {
  'use strict';

  var _contract = null;
  var _task = null;
  var _lastEnv = null;
  var _nameCache = {};

  function $(id) { return document.getElementById(id); }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function _sk(id) {
    id = String(id || '');
    if (!id) return '—';
    if (window._ecoSkillLabel) {
      try {
        var lab = window._ecoSkillLabel(id);
        if (lab && lab !== id) return lab;
      } catch (e) { /* ignore */ }
    }
    if (_nameCache[id]) return _nameCache[id];
    // 非 hex 可读 id：下划线转空格
    if (!/^[0-9a-f]{6,}$/i.test(id) && id.indexOf('-') < 0) {
      return id.replace(/_/g, ' ');
    }
    return '技能·' + id.slice(0, 8);
  }

  function _niches() {
    return (_contract && _contract.niches) || [];
  }

  function _isTaskExamActive() {
    return !!(
      _contract &&
      Array.isArray(_contract.niches) &&
      _contract.niches.length
    );
  }

  function _hudEl() {
    return $('env-3d-task-hud');
  }

  function _currentNicheIndex(env) {
    env = env || _lastEnv || {};
    if (env.niche_index != null && env.niche_index !== '') {
      var ni = parseInt(env.niche_index, 10);
      if (!isNaN(ni)) return ni;
    }
    // 按 title 匹配
    var title = env.niche_title || '';
    if (title) {
      var niches = _niches();
      for (var i = 0; i < niches.length; i++) {
        if ((niches[i].title || niches[i].step_id || '') === title) {
          return niches[i].index != null ? niches[i].index : i;
        }
      }
    }
    return 0;
  }

  function _findNiche(idx) {
    var niches = _niches();
    for (var i = 0; i < niches.length; i++) {
      var n = niches[i];
      if (n.index === idx || i === idx) return n;
    }
    return niches[0] || null;
  }

  function _renderRightChips(activeIdx) {
    var nb = $('eco2-env-niches');
    if (!nb || !_isTaskExamActive()) return;
    var niches = _niches();
    nb.innerHTML = niches.map(function (n, i) {
      var idx = n.index != null ? n.index : i;
      var sk = (n.demanded_skills || []).map(function (s) { return _sk(s); }).join(' · ');
      var active = idx === activeIdx;
      var done = idx < activeIdx;
      var bg = active
        ? 'background:rgba(34,211,238,.18);border-color:var(--cyan);color:var(--cyan)'
        : done
          ? 'background:rgba(52,211,153,.12);border-color:rgba(52,211,153,.4);color:var(--green)'
          : '';
      return '<span class="eco2-chip eco2-niche-chip" data-niche-idx="' + idx + '" title="'
        + esc(sk || '（无技能）') + '" style="' + bg + '">'
        + (done ? '✓ ' : active ? '▶ ' : '')
        + esc((idx) + '. ' + (n.title || n.step_id || '步骤'))
        + '</span>';
    }).join(' ') || '<span style="color:var(--dim)">（无考卷步骤）</span>';
  }

  function _renderHud() {
    var el = _hudEl();
    if (!el) return;
    if (!_isTaskExamActive()) {
      el.style.display = 'none';
      el.innerHTML = '';
      window.__ECO_TASK_EXAM__ = false;
      return;
    }
    window.__ECO_TASK_EXAM__ = true;
    el.style.display = 'block';

    var niches = _niches();
    var total = niches.length || 1;
    var activeIdx = _currentNicheIndex(_lastEnv);
    var niche = _findNiche(activeIdx) || {};
    var skills = niche.demanded_skills || [];
    var progress = Math.min(100, Math.round(((activeIdx + (_lastEnv && _lastEnv.demand ? 0.35 : 0)) / total) * 100));
    if (activeIdx >= total - 1 && _lastEnv && _lastEnv.step != null) {
      // 末步略抬进度
      progress = Math.max(progress, Math.min(99, progress));
    }
    var taskTitle = (_task && (_task.title || _task.name || _task.task_id)) ||
      (_contract && (_contract.topic || _contract.plan_id)) || '已挂接任务';
    var skillHtml = skills.length
      ? skills.map(function (s) {
        var sid = String(s);
        var lab = _sk(sid);
        var sidAttr = sid.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        return '<span class="eco-task-hud-skill" title="' + esc(sid) + '">'
          + esc(lab)
          + (window.ecoFeedbackViewSkill
            ? ' <button type="button" class="eco-task-hud-book" data-skill="' + esc(sid)
              + '" onclick="event.stopPropagation();if(window.ecoFeedbackViewSkill)ecoFeedbackViewSkill(\''
              + sidAttr + '\',event)">📖</button>'
            : '')
          + '</span>';
      }).join(' ')
      : '<span class="meta">（本步无显式技能需求）</span>';

    var living = _lastEnv && _lastEnv.living != null ? _lastEnv.living : '—';
    var tick = _lastEnv && _lastEnv.step != null ? _lastEnv.step : '—';
    var nicheTitle = niche.title || niche.step_id || (_lastEnv && _lastEnv.niche_title) || '—';

    el.innerHTML =
      '<div class="eco-task-hud-title">📋 任务考卷</div>'
      + '<div class="eco-task-hud-task" title="' + esc(taskTitle) + '">' + esc(String(taskTitle).slice(0, 42)) + '</div>'
      + '<div class="eco-task-hud-row"><span class="meta">进度</span> '
      + '<b style="color:var(--cyan)">' + (activeIdx + 1) + '</b><span class="meta">/' + total + '</span>'
      + ' · tick ' + esc(String(tick))
      + ' · 存活 ' + esc(String(living))
      + '</div>'
      + '<div class="eco-task-hud-bar"><i style="width:' + progress + '%"></i></div>'
      + '<div class="eco-task-hud-step">本步：' + esc(String(nicheTitle).slice(0, 36)) + '</div>'
      + '<div class="eco-task-hud-skills"><span class="meta">所需技能</span> ' + skillHtml + '</div>'
      + '<div class="eco-task-hud-foot meta">办公室语言 · 非觅食图腾 · 仅任务型演练</div>';

    _renderRightChips(activeIdx);
  }

  window.ecoTaskHudBind = function (contract, task) {
    _contract = contract || null;
    _task = task || null;
    _lastEnv = null;
    _renderHud();
  };

  window.ecoTaskHudClear = function () {
    _contract = null;
    _task = null;
    _lastEnv = null;
    window.__ECO_TASK_EXAM__ = false;
    var el = _hudEl();
    if (el) {
      el.style.display = 'none';
      el.innerHTML = '';
    }
    // 右侧 chips 保留契约列表但不强行清空（由 eco-console 负责）
  };

  window.ecoTaskHudOnEnv = function (env) {
    if (!env) return;
    _lastEnv = env;
    if (_isTaskExamActive()) _renderHud();
  };

  window.ecoTaskHudIsActive = function () {
    return _isTaskExamActive();
  };

  // 缓存技能名：若全局加载过 name map 则可用
  window.ecoTaskHudIngestNames = function (map) {
    if (!map || typeof map !== 'object') return;
    Object.keys(map).forEach(function (k) {
      if (map[k]) _nameCache[k] = String(map[k]);
    });
    if (_isTaskExamActive()) _renderHud();
  };
})();
