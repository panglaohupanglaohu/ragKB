/**
 * AgentsGroup2026 — Cost Governance Workbench
 * Repairs the OpenCost dashboard path and connects cost anomalies to task work.
 * Visual upgrade: KPI hero + horizontal bars + SVG line chart + count-up + toast.
 */
(function () {
  'use strict';

  var COST_API = '/api/v1/cost';
  var GATE_API = '/api/v1/cost-gate';
  var AGENT_API = '/api/v1/agent-config';
  var SUSTAINABILITY_API = '/api/v1/sustainability';
  var state = {
    teams: [],
    summary: null,
    breakdown: [],
    trends: [],
    pods: [],
    sustainability: null,
    health: null,
    gateHealth: null,
    gateStats: null,
    tokenOverview: null,
    filters: {},
    prevTotal: null,         // QoQ: previous refresh total (session)
    prevPeriodTotal: null,   // QoQ: previous comparable period (24h/7d/30d shifted back)
    budget: null,            // { monthly, currency, loadedAt }
  };

  /* ─────────────── DOM helpers ─────────────── */
  function $(id) { return document.getElementById(id); }

  function esc(value) {
    if (window.AG && typeof window.AG.escapeHtml === 'function') return window.AG.escapeHtml(value);
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function money(value) {
    var n = Number(value || 0);
    if (n > 0 && n < 0.01) return '$' + n.toFixed(4);
    return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function compactNumber(value) { return Number(value || 0).toLocaleString('en-US'); }

  function setText(id, value) { var n = $(id); if (n) n.textContent = value; }
  function setHtml(id, value) { var n = $(id); if (n) n.innerHTML = value; }

  /* ─────────────── count-up animation ─────────────── */
  function countUp(target, finalText, duration) {
    var node = typeof target === 'string' ? $(target) : target;
    if (!node) return;
    // Parse numeric value out of formatted string
    var numeric = parseFloat(String(finalText).replace(/[^0-9.\-]/g, ''));
    if (!isFinite(numeric)) { node.textContent = finalText; return; }

    // Preserve prefix/suffix (e.g. "$" or "%")
    var prefix = (String(finalText).match(/^[^0-9\-]*/) || [''])[0];
    var suffix = (String(finalText).match(/[^0-9]*$/) || [''])[0];

    var decimals = 0;
    var dotIdx = String(finalText).indexOf('.');
    if (dotIdx >= 0) {
      var tail = String(finalText).slice(dotIdx + 1).replace(/[^0-9]/g, '');
      decimals = tail.length;
    }

    var start = performance.now();
    var startVal = 0;
    function frame(now) {
      var t = Math.min(1, (now - start) / (duration || 600));
      // easeOutCubic
      var eased = 1 - Math.pow(1 - t, 3);
      var v = startVal + (numeric - startVal) * eased;
      var formatted = decimals > 0
        ? v.toFixed(decimals)
        : Math.round(v).toLocaleString('en-US');
      node.textContent = prefix + formatted + suffix;
      if (t < 1) requestAnimationFrame(frame);
      else node.textContent = finalText;
    }
    requestAnimationFrame(frame);
  }

  /* ─────────────── toast ─────────────── */
  function toast(message, opts) {
    var host = $('cost-toast-host');
    if (!host) return;
    if (typeof host.appendChild !== 'function') return;
    opts = opts || {};
    var kind = opts.kind || 'success';
    var title = opts.title || (kind === 'error' ? '操作失败' : kind === 'warn' ? '请稍候' : '完成');
    var duration = opts.duration == null ? 3500 : opts.duration;

    var el = document.createElement('div');
    el.className = 'cost-toast cost-toast--' + kind;
    el.innerHTML =
      '<div class="cost-toast__title">' + esc(title) + '</div>' +
      '<div class="cost-toast__body">' + esc(message) + '</div>';
    host.appendChild(el);

    setTimeout(function () {
      el.classList.add('cost-toast--leaving');
      setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 260);
    }, duration);
  }

  function showAlert(message) {
    var alert = $('dashboard-alert');
    if (!alert) return;
    if (!message) { alert.classList.remove('show'); alert.textContent = ''; return; }
    var requestId = window.api && typeof window.api.getLastRequestId === 'function'
      ? window.api.getLastRequestId() : '';
    alert.textContent = requestId ? message + ' · 请求ID: ' + requestId : message;
    alert.classList.add('show');
  }

  /* ─────────────── fetch helper ─────────────── */
  async function requestJson(url, opts) {
    if (window.api && typeof window.api.request === 'function') return await window.api.request(url, opts);
    var response = await fetch(url, opts || { credentials: 'same-origin' });
    if (!response.ok) return null;
    return await response.json();
  }

  /* ─────────────── filter & payload helpers ─────────────── */
  function getFilters() {
    var agg = ($('filter-aggregation') && $('filter-aggregation').value) || 'team';
    var lastVal = (($('filter-service') && $('filter-service').value) || '').trim();
    var env = ($('filter-environment') && $('filter-environment').value) || '';
    var filters = {
      aggregation: agg,
      window: ($('filter-window') && $('filter-window').value) || '24h',
      environment: env,
      service: '',
      team: '',
    };
    // Map the fourth filter value to the correct API parameter based on aggregation dimension
    if (agg === 'service') filters.service = lastVal;
    else if (agg === 'team') filters.team = lastVal;
    else if (agg === 'environment') {
      // When aggregation is environment, the fourth filter IS the environment filter;
      // the dedicated env dropdown becomes redundant/ignored
      filters.environment = lastVal;
    }
    return filters;
  }
  function queryString(params) {
    var query = new URLSearchParams();
    Object.keys(params || {}).forEach(function (key) {
      if (params[key] !== undefined && params[key] !== null && params[key] !== '') query.set(key, params[key]);
    });
    return query.toString();
  }
  function asItems(payload, key) {
    if (Array.isArray(payload)) return payload;
    if (!payload) return [];
    if (Array.isArray(payload[key])) return payload[key];
    if (Array.isArray(payload.items)) return payload.items;
    return [];
  }
  function normalizeTrends(payload) {
    return asItems(payload, 'trends').map(function (series) {
      var points = Array.isArray(series.points) ? series.points
        : Array.isArray(series.data_points) ? series.data_points : [];
      return {
        dimension: series.dimension || '',
        value: series.value || '',
        total: Number(series.total || 0),
        points: points.map(function (point) {
          return {
            timestamp: point.timestamp || '',
            cost: Number(point.total_cost != null ? point.total_cost : point.cost || 0),
          };
        }),
      };
    });
  }
  function normalizePods(payload) {
    return asItems(payload, 'pods').map(function (pod) {
      var labels = pod.labels || {};
      return {
        pod: pod.pod || pod.pod_name || pod.name || '',
        namespace: pod.namespace || 'default',
        service: pod.service || labels.service || labels.app || '',
        environment: pod.environment || labels.environment || '',
        team: pod.team || labels.team || '',
        cpu_cost: Number(pod.cpu_cost || 0),
        ram_cost: Number(pod.ram_cost || 0),
        network_cost: Number(pod.network_cost || 0),
        pv_cost: Number(pod.pv_cost || 0),
        total_cost: Number(pod.total_cost || 0),
        labels: labels,
      };
    });
  }

  /* ─────────────── KPI HERO ─────────────── */
  function renderKpiHero() {
    var host = $('kpi-hero');
    if (!host) return;

    // P1: 优先使用 Token 数据（北极星）
    var tok = state.tokenOverview;
    var tokSummary = tok && tok.summary;
    var tokByTeam = (tok && tok.by_team) || [];
    var tokByPhase = (tok && tok.by_phase) || {};

    if (tokSummary && tokSummary.total > 0) {
      // team_id ↔ 名称映射；并把筛选值（可能是名称或 id）解析为 team_id
      var nameById = {}, idByName = {};
      (state.teams || []).forEach(function (t) {
        nameById[t.team_id] = t.name || t.team_id;
        if (t.name) idByName[t.name.toLowerCase()] = t.team_id;
      });
      var teamLabel = function (id) { return nameById[id] || id || '—'; };
      var filterTeam = (state.filters && state.filters.team) || '';
      var filterTeamId = filterTeam ? (idByName[filterTeam.toLowerCase()] || filterTeam) : '';

      // 选中团队 → 把 KPI 限定到该团队；未选 → 全部
      var scoped = filterTeamId ? tokByTeam.filter(function (t) { return t.team_id === filterTeamId; }) : tokByTeam;
      var totalTokens = filterTeamId
        ? scoped.reduce(function (s, t) { return s + (t.total || 0); }, 0)
        : tokSummary.total;
      var totalCalls = filterTeamId
        ? scoped.reduce(function (s, t) { return s + (t.calls || 0); }, 0)
        : tokSummary.calls;
      var delta = (state.prevTotal != null && state.prevTotal > 0)
        ? (totalTokens - state.prevTotal) / state.prevTotal : null;
      state.prevTotal = totalTokens;

      // 第二卡：选中团队时显示「当前团队」，否则显示全局「最贵团队」（均用名称，不显示原始 id）
      var topTeam = filterTeamId
        ? (scoped[0] || { team_id: filterTeamId, total: 0, calls: 0 })
        : (tokByTeam.find(function (t) { return t && t.team_id; }) || null);
      var teamCard2Label = filterTeamId ? '当前团队' : '最贵团队';
      var teamCount = filterTeamId ? 1 : tokByTeam.length;

      // 第三卡 sub：阶段分布（说明这是 token 按阶段拆分，不是团队数的细分）
      var phaseText = '阶段 ' + (Object.keys(tokByPhase).map(function (k) {
        return k + ':' + compactNumber(tokByPhase[k].total || tokByPhase[k]);
      }).join(' · ') || '无');

      // 9.3: 棘轮累计锁定（KPI④ 反馈）
      var locked = (state.ratchet && state.ratchet.metrics) || [];
      var lockedCount = locked.length;
      var bestGen = locked.reduce(function (m, x) { return Math.max(m, x.generation || 0); }, 0);

      host.innerHTML =
        '<div class="kpi-hero__skeleton">' +
        kpiCardHtml({
          kind: 'hero',
          icon: heroIcon('wallet'),
          label: filterTeamId ? ('窗口 Token · ' + teamLabel(filterTeamId)) : '窗口总 Token',
          value: compactNumber(totalTokens),
          sub: windowLabel(state.filters.window) + ' · ' + compactNumber(totalCalls) + ' 次调用',
          delta: delta != null ? { value: delta, format: 'pct' } : null,
          deltaLabel: 'vs 上次刷新',
        }) +
        kpiCardHtml({
          kind: topTeam && topTeam.total > 10000 ? 'warning' : 'standard',
          icon: heroIcon('team'),
          label: teamCard2Label,
          value: topTeam ? teamLabel(topTeam.team_id) : '—',
          sub: topTeam ? compactNumber(topTeam.total) + ' tokens · ' + compactNumber(topTeam.calls) + ' 调用' : '等待数据',
        }) +
        kpiCardHtml({
          kind: 'standard',
          icon: heroIcon('grid'),
          label: filterTeamId ? '团队（已筛选）' : '团队数',
          value: compactNumber(teamCount),
          sub: phaseText,
        }) +
        kpiCardHtml({
          kind: lockedCount ? 'success' : 'muted',
          icon: heroIcon('lock'),
          label: '棘轮已锁定',
          value: lockedCount ? (lockedCount + ' 项') : '—',
          sub: lockedCount ? ('最高 gen ' + bestGen + ' · 只进不退') : '达成目标后自动锁定',
        }) +
        '</div>';
      setHtml('summary-grid', host.innerHTML);
      return;
    }

    // 回退：OpenCost 基础设施成本（无 Token 数据时）
    var summary = state.summary && state.summary.summary;
    if (!summary) {
      host.innerHTML = '<div class="empty-state"><div class="icon">∅</div><div>暂无 Token 消耗数据</div><div style="font-size:12px;color:var(--dim);margin-top:4px">Agent 调用 LLM 后将自动产生 Token 记录</div></div>';
      setHtml('summary-grid', host.innerHTML);
      return;
    }

    var totalCost = Number(summary.total_cost || 0);
    var delta = (state.prevTotal != null && state.prevTotal > 0)
      ? (totalCost - state.prevTotal) / state.prevTotal : null;
    state.prevTotal = totalCost;

    var podCount = Number(summary.pod_count || summary.total_pods || 0);
    var containerCount = Number(summary.container_count || 0);
    var serviceCount = Number(summary.service_count || (summary.by_service || []).length);
    var teamCount = Number(summary.team_count || (summary.by_team || []).length);

    host.innerHTML =
      '<div class="kpi-hero__skeleton">' +
      kpiCardHtml({
        kind: 'muted',
        icon: heroIcon('wallet'),
        label: '基础设施成本（OpenCost）',
        value: money(totalCost),
        sub: windowLabel(state.filters.window) + ' · ' + compactNumber(podCount) + ' 个 Pod',
        delta: delta != null ? { value: delta, format: 'pct' } : null,
        deltaLabel: 'vs 上次刷新',
      }) +
      kpiCardHtml({
        kind: 'muted',
        icon: heroIcon('pod'),
        label: '活跃 Pod',
        value: compactNumber(podCount),
        sub: '容器 ' + compactNumber(containerCount),
      }) +
      kpiCardHtml({
        kind: 'muted',
        icon: heroIcon('grid'),
        label: '服务 × 环境',
        value: compactNumber(serviceCount),
        sub: '团队 ' + compactNumber(teamCount),
      }) +
      kpiCardHtml({
        kind: 'muted',
        icon: heroIcon('team'),
        label: '提示',
        value: '等待 Token',
        sub: 'Agent 调用 LLM 后显示 Token 成本',
      }) +
      '</div>';
    setHtml('summary-grid', host.innerHTML);

    // Trigger count-up on each numeric value
    var raf = typeof requestAnimationFrame === 'function' ? requestAnimationFrame : function (fn) { fn(); };
    raf(function () {
      if (!host.querySelectorAll) return;
      host.querySelectorAll('[data-countup]').forEach(function (el) {
        countUp(el, el.getAttribute('data-countup'), 700);
      });
    });
  }

  function kpiCardHtml(opts) {
    var deltaHtml = '';
    if (opts.delta && isFinite(opts.delta.value)) {
      var v = opts.delta.value;
      var cls = 'flat', sign = '—', display = '0%';
      if (Math.abs(v) < 0.0005) {
        cls = 'flat'; sign = '·'; display = '0%';
      } else if (v > 0) {
        // Cost up is bad
        cls = 'up'; sign = '↑'; display = (v * 100).toFixed(1) + '%';
      } else {
        cls = 'down'; sign = '↓'; display = (Math.abs(v) * 100).toFixed(1) + '%';
      }
      var deltaLabel = opts.deltaLabel || 'vs 上次';
      deltaHtml =
        '<span class="kpi-card__delta kpi-card__delta--' + cls + '">' +
        sign + ' ' + display +
        '</span><span style="color:var(--sumi-3)">' + esc(deltaLabel) + '</span>';
    }

    return [
      '<div class="kpi-card kpi-card--' + (opts.kind || 'standard') + '">',
      '<div class="kpi-card__icon">' + opts.icon + '</div>',
      '<div>',
      '<div class="kpi-card__label">' + esc(opts.label) + '</div>',
      '<div class="kpi-card__value" data-countup="' + esc(opts.value) + '">' + esc(opts.value) + '</div>',
      '</div>',
      '<div class="kpi-card__sub">' + deltaHtml + esc(opts.sub || '') + (opts.subExtra || '') + '</div>',
      opts.spark || '',
      '</div>',
    ].join('');
  }

  function heroIcon(kind) {
    var icons = {
      wallet: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>',
      pod: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 9h6v6H9z"/></svg>',
      grid: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
      team: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    };
    return icons[kind] || icons.wallet;
  }

  function windowLabel(w) {
    if (w === '24h') return '最近 24 小时';
    if (w === '7d') return '最近 7 天';
    if (w === '30d') return '最近 30 天';
    return w || '24h';
  }

  /* ─────────────── Budget (localStorage) ─────────────── */
  function loadBudget() {
    try {
      var raw = localStorage.getItem('ag-cost-budget');
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (parsed && Number(parsed.monthly) > 0) return parsed;
    } catch (e) {}
    return null;
  }
  function saveBudget(monthly) {
    try {
      if (monthly && Number(monthly) > 0) {
        localStorage.setItem('ag-cost-budget', JSON.stringify({ monthly: Number(monthly), loadedAt: new Date().toISOString() }));
      } else {
        localStorage.removeItem('ag-cost-budget');
      }
    } catch (e) {}
  }

  function updateBudgetPill() {
    var pill = $('budget-pill');
    var pillValue = $('budget-pill-value');
    var inputWrap = $('budget-input-wrap');
    var input = $('budget-input');
    if (!pill) return;
    var b = loadBudget();
    if (b) {
      pill.style.display = 'inline-flex';
      if (inputWrap) inputWrap.style.display = 'none';
      if (pillValue) pillValue.textContent = money(b.monthly) + '/月';
    } else {
      pill.style.display = 'none';
      if (inputWrap) inputWrap.style.display = 'inline-flex';
      if (input) input.value = '';
    }
  }

  function initBudgetUI() {
    var setBtn = $('budget-set');
    var input = $('budget-input');
    var clearBtn = $('budget-clear');
    if (setBtn && input) {
      var commit = function () {
        var v = parseFloat(input.value);
        if (!isFinite(v) || v <= 0) {
          saveBudget(null);
          toast('预算已清除', { kind: 'info', title: '预算' });
        } else {
          saveBudget(v);
          toast('月度预算已设置: ' + money(v), { kind: 'success', title: '预算生效' });
        }
        updateBudgetPill();
        refreshDashboard();
      };
      setBtn.addEventListener('click', commit);
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') commit();
      });
    }
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        saveBudget(null);
        toast('预算已清除', { kind: 'info', title: '预算' });
        updateBudgetPill();
        refreshDashboard();
      });
    }
    updateBudgetPill();
  }

  function maxCost(items) {
    items = Array.isArray(items) ? items : [];
    return items.reduce(function (max, item) { return Math.max(max, Number(item.total_cost || 0)); }, 0);
  }

  function buildSparkFromSummary(summary) {
    // Build a fake-but-stable sparkline from the breakdown series
    var series = summary.by_team || summary.by_service || summary.by_environment || [];
    if (!Array.isArray(series) || series.length < 2) return '';
    var values = series.map(function (s) { return Number(s.total_cost || 0); });
    return sparkSvg(values);
  }

  function sparkSvg(values) {
    if (!values.length) return '';
    var max = Math.max.apply(null, values.concat([0.0001]));
    var min = Math.min.apply(null, values);
    var range = max - min || 1;
    var w = 200, h = 36, pad = 2;
    var stepX = (w - pad * 2) / Math.max(1, values.length - 1);
    var trend = values[values.length - 1] - values[0];
    var cls = trend > 0.0001 ? 'up' : (trend < -0.0001 ? 'down' : 'flat');
    var points = values.map(function (v, i) {
      var x = pad + i * stepX;
      var y = h - pad - ((v - min) / range) * (h - pad * 2);
      return x.toFixed(1) + ',' + y.toFixed(1);
    });
    return '<svg class="spark-svg" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none">' +
      '<polyline class="spark-line spark-line--' + cls + '" points="' + points.join(' ') + '"/>' +
      '</svg><div class="kpi-card__spark"></div>';
  }

  /* ─────────────── Top 10 horizontal bar chart ─────────────── */
  function renderBreakdown(items) {
    var container = $('breakdown-chart');
    if (!container) return;
    if (!items || !items.length) {
      container.innerHTML = '<div class="empty-state"><div class="icon">∅</div><div>该维度下暂无 Token 数据</div><div style="font-size:12px;color:var(--dim);margin-top:4px">去议事广场/技能萃取/数字孪生产生 LLM 调用</div></div>';
      return;
    }
    // P8.1: 字段从 OpenCost {value, total_cost} 改为 Token {key, total}
    var sorted = items.slice().sort(function (a, b) {
      return Number(b.total || 0) - Number(a.total || 0);
    }).slice(0, 10);
    var grand = sorted.reduce(function (s, x) { return s + Number(x.total || 0); }, 0);
    var max = Math.max.apply(null, sorted.map(function (item) { return Number(item.total || 0); }).concat([0.0001]));

    var rows = sorted.map(function (item, idx) {
      var v = Number(item.total || 0);
      var pct = (v / max) * 100;
      var share = grand > 0 ? (v / grand) * 100 : 0;
      var tier = idx === 0 ? 'accent' : (v / max > 0.6 ? 'warning' : '');
      return [
        '<li class="hbar-item ' + (tier ? 'hbar-item--' + tier : '') + (idx === 0 ? ' hbar-item--top' : '') + '">',
        '  <div class="hbar-rank">#' + (idx + 1).toString().padStart(2, '0') + '</div>',
        '  <div class="hbar-label" title="' + esc(item.key || '?') + '">' + esc(item.key || '?') + '</div>',
        '  <div class="hbar-track">',
        '    <div class="hbar-fill" style="width:' + pct.toFixed(1) + '%"></div>',
        '  </div>',
        '  <div class="hbar-value">' + compactNumber(v) + ' tokens<span class="hbar-pct">' + share.toFixed(1) + '%</span></div>',
        '</li>',
      ].join('');
    }).join('');

    container.innerHTML = '<ul class="hbar-list">' + rows + '</ul>';
  }

  /* ─────────────── SVG line chart (trend) ─────────────── */
  function renderTrends(seriesList) {
    var container = $('trends-chart');
    var sub = $('trends-sub');
    if (!container) return;
    // P8.2: Token trend 返回 {points, total, ...}，不是数组
    var series = null;
    if (seriesList && Array.isArray(seriesList) && seriesList.length) {
      series = seriesList[0];
    } else if (seriesList && seriesList.points) {
      series = seriesList;
    }
    if (!series || !series.points || series.points.length < 1) {
      container.innerHTML = '<div class="empty-state"><div class="icon">∅</div><div>窗口内暂无 Token 消耗</div><div style="font-size:12px;color:var(--dim);margin-top:4px">去议事广场/技能萃取/数字孪生产生调用</div></div>';
      if (sub) sub.textContent = '—';
      return;
    }
    var points = series.points;
    // P8.2: point.total 替代 point.cost
    var values = points.map(function (p) { return Number(p.total || 0); });
    var total = Number(series.total || values.reduce(function (s, v) { return s + v; }, 0));

    // Linear forecast for next 3 points (only when we have ≥3 real points)
    var forecast = linearForecast(values, 3);
    var fcEndValue = forecast.length ? forecast[forecast.length - 1] : null;
    var fcDelta = (forecast.length && values.length) ? (fcEndValue - values[values.length - 1]) / (values[values.length - 1] || 1) : null;

    // Adjust Y max so forecast fits inside viewbox
    var allValues = values.concat(forecast);
    var max = Math.max.apply(null, allValues.concat([0.0001]));
    var min = 0;

    if (sub) {
      var fcText = '';
      if (fcEndValue != null && fcDelta != null) {
        var dir = fcDelta > 0.001 ? '↑' : (fcDelta < -0.001 ? '↓' : '→');
        var cls = fcDelta > 0.05 ? 'fc-up' : (fcDelta < -0.05 ? 'fc-down' : 'fc-flat');
        fcText = ' · 预测 ' + dir + ' <span class="fc-pill fc-pill--' + cls + '">' +
                 compactNumber(fcEndValue) + ' tokens (' + (fcDelta * 100).toFixed(1) + '%)</span>';
      }
      sub.innerHTML = esc(series.dimension || 'series') + ' · ' +
        esc(series.value || '-') + ' · 总计 ' + compactNumber(total) + ' tokens' + fcText;
    }

    var html = lineChartSvg(points, values, max, min, forecast);
    container.innerHTML = '<div class="chart-meta" style="display:none">' + esc(series.value || series.dimension || '') + '</div>' + html;
    attachLineChartTooltip(container, points, values, forecast);
  }

  /* ─────────────── Forecast (linear extrapolation) ─────────────── */
  function linearForecast(values, steps) {
    // Simple least-squares fit on (index, value) for the last min(N, 7) points
    if (!Array.isArray(values) || values.length < 2 || steps < 1) return [];
    var useN = Math.min(7, values.length);
    var slice = values.slice(-useN);
    var n = slice.length;
    var sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    for (var i = 0; i < n; i++) {
      sumX += i; sumY += slice[i];
      sumXY += i * slice[i]; sumX2 += i * i;
    }
    var denom = (n * sumX2 - sumX * sumX) || 1;
    var slope = (n * sumXY - sumX * sumY) / denom;
    var intercept = (sumY - slope * sumX) / n;
    var lastIdx = values.length - 1;
    var out = [];
    for (var k = 1; k <= steps; k++) {
      var v = slope * (lastIdx + k) + intercept;
      if (v < 0) v = 0;
      out.push(Number(v.toFixed(6)));
    }
    return out;
  }

  function lineChartSvg(points, values, max, min, forecast) {
    var W = 560, H = 240;
    var padL = 56, padR = 16, padT = 16, padB = 32;
    var innerW = W - padL - padR;
    var innerH = H - padT - padB;
    var n = points.length;
    var fSteps = (forecast && forecast.length) || 0;
    var totalSlots = n + fSteps;
    // Use forecast-aware x scale so the predicted segment uses remaining space
    var xStep = totalSlots > 1 ? innerW / (totalSlots - 1) : 0;

    function xAt(i) { return padL + i * xStep; }
    function yAt(v) { return padT + innerH - ((v - min) / (max - min || 1)) * innerH; }

    // Y-axis ticks (4 levels)
    var ticks = 4;
    var yTicks = [];
    for (var i = 0; i <= ticks; i++) {
      var v = (max / ticks) * i;
      yTicks.push({ y: yAt(v), label: money(v) });
    }

    // X-axis labels: at most 6 evenly distributed across real points
    var xLabels = [];
    var labelCount = Math.min(6, n);
    var labelStep = n > labelCount ? Math.floor((n - 1) / (labelCount - 1)) : 1;
    for (var li = 0; li < n; li += labelStep) {
      var ts = points[li].timestamp || '';
      var lbl = ts.length >= 16 ? ts.slice(5, 16).replace('T', ' ') : ts;
      xLabels.push({ x: xAt(li), label: lbl });
    }
    if (xLabels.length && xLabels[xLabels.length - 1].x < xAt(n - 1) - 4) {
      xLabels.push({ x: xAt(n - 1), label: (points[n - 1].timestamp || '').slice(5, 16).replace('T', ' ') });
    }
    // Forecast zone tick
    if (fSteps > 0) {
      xLabels.push({ x: xAt(totalSlots - 1), label: '预测' });
    }

    var maxIdx = 0;
    for (var mi = 1; mi < values.length; mi++) if (values[mi] > values[maxIdx]) maxIdx = mi;

    var lineD = points.map(function (p, i) { return (i === 0 ? 'M' : 'L') + xAt(i).toFixed(1) + ',' + yAt(values[i]).toFixed(1); }).join(' ');
    var areaD = lineD + ' L' + xAt(n - 1).toFixed(1) + ',' + (padT + innerH).toFixed(1) + ' L' + padL + ',' + (padT + innerH).toFixed(1) + ' Z';

    var gridLines = yTicks.map(function (t) {
      return '<line x1="' + padL + '" y1="' + t.y + '" x2="' + (padL + innerW) + '" y2="' + t.y + '"/>';
    }).join('');

    var yLabels = yTicks.map(function (t) {
      return '<text x="' + (padL - 8) + '" y="' + (t.y + 3) + '" text-anchor="end">' + esc(t.label) + '</text>';
    }).join('');

    var xLabelsHtml = xLabels.map(function (l) {
      return '<text x="' + l.x + '" y="' + (padT + innerH + 18) + '" text-anchor="middle">' + esc(l.label) + '</text>';
    }).join('');

    var dots = points.map(function (p, i) {
      var cls = i === maxIdx ? ' lc-dot lc-dot--max' : ' lc-dot';
      return '<circle class="' + cls.trim() + '" cx="' + xAt(i) + '" cy="' + yAt(values[i]) + '" r="3" data-i="' + i + '"><title>' + esc(money(values[i])) + '</title></circle>';
    }).join('');

    // Forecast: dashed line + open ring dots
    var forecastMarkup = '';
    if (fSteps > 0) {
      var fStartX = xAt(n - 1);
      var fStartY = yAt(values[values.length - 1]);
      var fPoints = [fStartX.toFixed(1) + ',' + fStartY.toFixed(1)];
      for (var fi = 0; fi < fSteps; fi++) {
        fPoints.push(xAt(n + fi).toFixed(1) + ',' + yAt(forecast[fi]).toFixed(1));
      }
      var fLineD = fPoints.map(function (p, i) { return (i === 0 ? 'M' : 'L') + p; }).join(' ');
      // Vertical separator (now line)
      forecastMarkup +=
        '<line class="lc-fc-sep" x1="' + fStartX.toFixed(1) + '" y1="' + padT +
        '" x2="' + fStartX.toFixed(1) + '" y2="' + (padT + innerH) + '"/>' +
        '<path class="lc-fc-line" d="' + fLineD + '"/>';
      for (var fi2 = 0; fi2 < fSteps; fi2++) {
        forecastMarkup +=
          '<circle class="lc-fc-dot" cx="' + xAt(n + fi2).toFixed(1) +
          '" cy="' + yAt(forecast[fi2]).toFixed(1) + '" r="3" data-fc-i="' + fi2 + '"><title>' +
          esc(money(forecast[fi2])) + '</title></circle>';
      }
    }

    return [
      '<svg class="line-chart" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet">',
      '  <defs>',
      '    <linearGradient id="lc-area-grad" x1="0" y1="0" x2="0" y2="1">',
      '      <stop offset="0%" stop-color="var(--koke)" stop-opacity="0.35"/>',
      '      <stop offset="100%" stop-color="var(--koke)" stop-opacity="0"/>',
      '    </linearGradient>',
      '  </defs>',
      '  <g class="lc-grid">' + gridLines + '</g>',
      '  <g class="lc-axis">' + yLabels + xLabelsHtml + '</g>',
      '  <path class="lc-area" d="' + areaD + '"/>',
      '  <path class="lc-line" d="' + lineD + '"/>',
      '  ' + dots,
        forecastMarkup,
      '</svg>',
    ].join('');
  }

  function attachLineChartTooltip(container, points, values, forecast) {
    if (!container || typeof container.querySelector !== 'function') return;
    var svg = container.querySelector('svg.line-chart');
    if (!svg) return;
    var tip = document.createElement('div');
    tip.className = 'lc-tip';
    tip.style.display = 'none';
    container.style.position = 'relative';
    container.appendChild(tip);

    svg.addEventListener('mousemove', function (e) {
      var target = e.target;
      if (!target || target.tagName !== 'circle') { tip.style.display = 'none'; return; }
      var rect = svg.getBoundingClientRect();
      var ctm = svg.getScreenCTM();
      if (!ctm) return;
      var svgPt = svg.createSVGPoint();
      svgPt.x = e.clientX; svgPt.y = e.clientY;
      var local = svgPt.matrixTransform(ctm.inverse());

      if (target.classList && target.classList.contains('lc-fc-dot')) {
        var fi = parseInt(target.getAttribute('data-fc-i') || '0', 10);
        tip.innerHTML = '<strong>' + money(forecast[fi]) + '</strong> · <span style="color:var(--kitsune)">预测</span> +' + (fi + 1) + ' 步';
      } else {
        var idx = parseInt(target.getAttribute('data-i') || '0', 10);
        tip.innerHTML = '<strong>' + money(values[idx]) + '</strong> · ' + esc((points[idx].timestamp || '').slice(0, 16).replace('T', ' '));
      }
      tip.style.left = (rect.left - container.getBoundingClientRect().left + local.x) + 'px';
      tip.style.top = (rect.top - container.getBoundingClientRect().top + local.y) + 'px';
      tip.style.display = 'block';
    });
    svg.addEventListener('mouseleave', function () { tip.style.display = 'none'; });
  }

  /* ─────────────── Pod cost table ─────────────── */
  function renderPodsTable(pods) {
    var tbody = $('pods-tbody');
    if (!tbody) return;
    // P8.3: Token 消耗明细（替代 Pod 明细）
    if (!pods || !pods.length) {
      tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><div class="icon">∅</div><div>暂无 Token 消耗明细</div><div style="font-size:12px;color:var(--dim);margin-top:4px">去议事广场/技能萃取/数字孪生产生 LLM 调用</div></div></td></tr>';
      setText('pod-count', '');
      return;
    }
    var sorted = pods.slice().sort(function (a, b) { return Number(b.total || 0) - Number(a.total || 0); });
    var max = Math.max.apply(null, sorted.map(function (p) { return Number(p.total || 0); }).concat([0.0001]));

    setText('pod-count', '(共 ' + pods.length + ' 条)');

    tbody.innerHTML = sorted.slice(0, 50).map(function (row, index) {
      var v = Number(row.total || 0);
      var barW = (v / max) * 100;
      var tier = v / max > 0.6 ? 'row--accent' : v / max > 0.3 ? 'row--warning' : '';
      var rid = esc(row.run_id || '?');
      var ts = row.ts ? new Date(Number(row.ts)).toLocaleString('zh-CN') : '-';
      return [
        '<tr class="' + tier + '">',
        '  <td class="col-pod" title="' + rid + '">' + rid.slice(0, 16) + '</td>',
        '  <td><span class="pill">' + esc(row.phase || 'task') + '</span></td>',
        '  <td>' + esc(row.team_id || '-') + '</td>',
        '  <td>' + esc(row.skill_id || '-') + '</td>',
        '  <td class="num">' + (row.calls || 0) + '</td>',
        '  <td class="num col-total"><span class="col-total-bar"><i style="width:' + barW.toFixed(1) + '%"></i></span>' + compactNumber(v) + ' tokens</td>',
        '  <td style="font-size:11px;color:var(--dim)">' + ts + '</td>',
        '</tr>',
      ].join('');
    }).join('');
  }

  /* ─────────────── Governance panel ─────────────── */
  function renderGovernance() {
    var panel = $('governance-panel');
    if (!panel) return;
    var summaryResp = state.summary || {};
    var health = state.health || {};
    var stats = state.gateStats || {};
    var filters = state.filters || {};
    var agg = filters.aggregation || 'team';

    // 治理目标联动筛选条件：优先展示当前选中的维度值
    // P8R.3: 改用 token breakdown 字段 {key, total}
    // 治理/棘轮目标必须是「已归因」团队——空 team_id 会被渲染成「(未归因)」，
    // 它若被选为目标，运行棘轮周期会 POST team_id='' → 后端 400 → 静默无反应。
    var isAttributed = function (b) { return b && b.key && b.key !== '(未归因)'; };
    var attributed = (state.breakdown || []).filter(isAttributed);
    var topTarget = null;
    if (agg === 'team' && filters.team) {
      topTarget = state.breakdown.find(function (b) { return (b.key || '') === filters.team; }) || attributed[0] || null;
    } else if (agg === 'service' && filters.service) {
      topTarget = state.breakdown.find(function (b) { return (b.key || '') === filters.service; }) || attributed[0] || null;
    } else if (agg === 'environment' && filters.environment) {
      topTarget = state.breakdown.find(function (b) { return (b.key || '') === filters.environment; }) || attributed[0] || null;
    } else {
      topTarget = attributed[0] || null;
    }
    var topLabel = topTarget ? (agg + ': ' + (topTarget.key || '-'))
      : (state.breakdown && state.breakdown.length ? '仅有未归因消耗（先让调用带上 team_id）' : '暂无异常目标');
    var topCost = topTarget ? (compactNumber(topTarget.total || 0) + ' tokens') : '-';
    // P8R.3: 赋值 governanceTarget 供棘轮/派发共用（仅取已归因目标，避免空 team_id）
    state.governanceTarget = (topTarget && isAttributed(topTarget))
      ? { team_id: topTarget.key, total: topTarget.total, lever: '', lever_split: null }
      : null;

    // 指派团队联动
    var selectedTeam = filters.team || filters.service || '';
    var teamOptionsHtml = teamOptionsHtmlWithSelected(selectedTeam);

    var dataAge = Number(summaryResp.data_freshness_seconds || health.data_age_seconds || health.data_freshness_seconds || 0);
    var dataAgeClass = dataAge <= 120 ? 'ok' : dataAge <= 600 ? 'warn' : 'alert';
    var dataAgeText = dataAge <= 60 ? '刚刚' : dataAge <= 3600 ? Math.floor(dataAge / 60) + ' 分钟前' : dataAge <= 86400 ? Math.floor(dataAge / 3600) + ' 小时前' : Math.floor(dataAge / 86400) + ' 天前';

    var blocked = Number(stats.blocked || stats.block || 0);
    var passed = Number(stats.passed || stats.pass || 0);
    var warned = Number(stats.warned || stats.warn || 0);
    var total = blocked + passed + warned || 1;
    var blockRate = ((blocked / total) * 100);

    panel.innerHTML = [
      '<div class="governance-status">',
      // 数据新鲜度
      '  <div class="gov-stat">',
      '    <div class="gov-stat__label">数据新鲜度</div>',
      '    <div class="gov-stat__value gov-stat__value--' + dataAgeClass + '">' + esc(dataAgeText) + '</div>',
      '  </div>',
      // Gate 拦截率
      '  <div class="gov-stat">',
      '    <div class="gov-stat__label">Gate 拦截率</div>',
      '    <div class="gov-stat__value ' + (blockRate > 20 ? 'gov-stat__value--alert' : blockRate > 5 ? 'gov-stat__value--warn' : 'gov-stat__value--ok') + '">' + blockRate.toFixed(1) + '%</div>',
      '  </div>',
      // Gate 通行/阻断统计
      '  <div class="gov-stat">',
      '    <div class="gov-stat__label">Gate 统计</div>',
      '    <div class="gov-stat__value" style="font-size:12px;color:var(--sumi)"><span style="color:var(--koke)">' + compactNumber(passed) + ' 通</span> · <span style="color:var(--kitsune)">' + compactNumber(warned) + ' 警</span> · <span style="color:var(--shu)">' + compactNumber(blocked) + ' 阻</span></div>',
      '  </div>',
      '</div>',

      '<div class="action-box">',
      '  <div class="action-box__title">⚡ 当前治理目标</div>',
      '  <div class="action-box__target">' + esc(topLabel) + '<span class="action-box__target-cost">' + esc(topCost) + '</span></div>',
      '  <label>指派团队<select id="cost-action-team">' + teamOptionsHtml + '</select></label>',
      '  <div class="action-buttons">',
      '    <button class="btn cost-btn cost-btn--accent cost-btn--sm" onclick="createOptimizationTask(\'breakdown\',0)">创建优化任务</button>',
      '    <button class="btn cost-btn cost-btn--ghost cost-btn--sm" onclick="createPlazaTopic(\'breakdown\',0)">创建 Plaza 话题</button>',
      '  </div>',
      '  <div class="action-result" id="cost-action-result"></div>',
      '</div>',
    ].join('');
  }

  function renderEfficiencyView(payload) {
    var host = $('efficiency-panel');
    if (!host) return;
    state.effSort = state.effSort || 'worst';
    var _effRank = function (t) {
      var spend = Number(t.tokens_consumed || 0);
      var eff = Number(t.token_efficiency || 0);
      if (spend <= 0) return { g: 2, v: 0 };
      return { g: 0, v: state.effSort === 'worst' ? eff : -eff };
    };
    var teams = asItems(payload, 'teams').slice().sort(function (a, b) {
      var ra = _effRank(a), rb = _effRank(b);
      return ra.g - rb.g || ra.v - rb.v;
    });
    if (!teams.length) {
      host.innerHTML = '<div class="empty-state"><div class="icon">∅</div><div>暂无可持续性评估数据</div></div>';
      return;
    }
    // Build team_id → team_name map from state.teams for display consistency
    var teamNameMap = {};
    if (Array.isArray(state.teams)) {
      state.teams.forEach(function (t) { teamNameMap[t.team_id] = t.name || t.team_id; });
    }
    function teamLabel(tid) { return teamNameMap[tid] || tid; }

    var rows = teams.map(function (team, index) {
      var grade = team.grade || '-';
      // P8R.4: 效率公式 tooltip
      var formulaTitle = 'score ' + (team.total_score || 0) + ' ÷ (tokens ' + (team.tokens_consumed || 0) + '/1k) = ' + Number(team.token_efficiency || 0).toFixed(4);
      var dqText = esc(team.data_quality || '-');
      var twinLink = '/Agent-digital-twin.html?team=' + encodeURIComponent(team.team_id || '');
      if (team.data_quality === 'token_only') dqText += ' · 有消耗无评分 → <a href="' + twinLink + '" style="color:var(--koke);text-decoration:none">去数字孪生跑评分试炼▸</a>';
      if (team.data_quality === 'no_data') dqText += ' · 暂无数据 → <a href="' + twinLink + '" style="color:var(--koke);text-decoration:none">先跑一次试炼▸</a>';
      // P8R.4: 两杠杆占比条
      var lc = team.lever_cost || { skill_pct: 0, collab_pct: 0, skill: 0, collab: 0, other: 0 };
      var leverBar = '<div class="lever-bar" title="Skill杠杆 ' + compactNumber(lc.skill || 0) + ' / 协作 ' + compactNumber(lc.collab || 0) + '" style="display:flex;height:4px;border-radius:2px;overflow:hidden;margin-top:2px">'
        + '<i style="width:' + (lc.skill_pct * 100).toFixed(0) + '%;background:var(--koke);display:block"></i>'
        + '<i style="width:' + (lc.collab_pct * 100).toFixed(0) + '%;background:var(--kitsune);display:block"></i>'
        + '</div>';
      var _pct = function (x) { return Math.round((x || 0) * 100); };
      var hasSpend = Number(team.tokens_consumed || 0) > 0;
      var leverHint = '';
      if (hasSpend && ((lc.skill || 0) + (lc.collab || 0)) > 0) {
        var skillHeavy = (lc.skill_pct || 0) >= (lc.collab_pct || 0);
        leverHint = skillHeavy
          ? '<div class="lever-next" style="font-size:10px;color:var(--sumi-3);margin-top:3px">技能杠杆重(' + _pct(lc.skill_pct) + '%) → <a href="/skill-extract.html" style="color:var(--koke);text-decoration:none">去技能萃取固化重复 skill▸</a></div>'
          : '<div class="lever-next" style="font-size:10px;color:var(--sumi-3);margin-top:3px">协作杠杆重(' + _pct(lc.collab_pct) + '%) → <a href="/plaza.html" style="color:var(--koke);text-decoration:none">去议事广场复盘协作▸</a></div>';
      }
      return [
        '<div class="efficiency-row" title="' + esc(formulaTitle) + '">',
        '  <div class="efficiency-rank">#' + String(index + 1).padStart(2, '0') + '</div>',
        '  <div class="efficiency-team"><b>' + esc(teamLabel(team.team_id)) + '</b><span>' + dqText + ' · ' + compactNumber(team.tokens_consumed || 0) + ' tokens</span>' + leverBar + leverHint + '</div>',
        '  <div class="efficiency-score" title="' + esc(formulaTitle) + '">' + Number(team.token_efficiency || 0).toFixed(4) + '</div>',
        '  <div class="efficiency-grade efficiency-grade--' + esc(grade) + '">' + esc(grade) + '</div>',
        '</div>',
      ].join('');
    }).join('');
    var reallocations = asItems(payload, 'reallocations');
    var recs = teams.filter(function (t) { return t.grade === 'C' || t.grade === 'D'; });
    // 9.8: 说明 score 来源，避免把「未跑评分→效率0」误读为低效
    var allZeroEff = teams.every(function (t) { return !Number(t.token_efficiency || 0); });
    var scoreNote = '<div style="font-size:11px;color:var(--sumi-3);margin-bottom:8px;line-height:1.5">效率 = score ÷ (tokens/1k)，<b>score 来自数字孪生「评分试炼」</b>。'
      + (allZeroEff ? '当前所有团队尚无评分 → 效率显示 0（<b>不代表低效</b>）。去 <a href="/Agent-digital-twin.html" style="color:var(--koke)">数字孪生</a> 跑一次评分试炼即可解锁。' : '未跑评分的团队显示为 0。') + '</div>';
    // 13.1: 未归因 token 健康指标（>5% 红字提示，效率被低估）
    var ua = payload && payload._unattributed;
    var uaBanner = '';
    if (ua && ua.tokens > 0) {
      var uaPct = (ua.ratio * 100).toFixed(1);
      var uaWarn = ua.ratio > 0.05;
      uaBanner = '<div style="font-size:11px;margin-bottom:8px;line-height:1.5;' + (uaWarn ? 'color:var(--shu)' : 'color:var(--sumi-3)') + '">'
        + (uaWarn ? '⚠ ' : '') + '未归因 token：' + compactNumber(ua.tokens) + ' (' + uaPct + '%)'
        + (uaWarn ? ' — 有 LLM 调用未带 team_id，部分团队效率被低估；让议事/萃取/演练调用带上 token_scope(team_id)，归因占比应 <5%。' : ' · 归因健康')
        + '</div>';
    }
    var sortBar = '<div style="font-size:11px;color:var(--sumi-3);margin-bottom:8px">排序：'
      + '<b style="color:var(--sumi-1)">' + (state.effSort === 'worst' ? '最需优化优先（低效在前）' : '效率最高优先') + '</b>'
      + ' · <a href="javascript:void(0)" onclick="toggleEffSort()" style="color:var(--koke);text-decoration:none">切换为' + (state.effSort === 'worst' ? '效率最高优先' : '最需优化优先') + '▸</a></div>';
    host.innerHTML = [
      uaBanner,
      sortBar,
      scoreNote,
      '<div class="efficiency-grid">',
      '  <div class="efficiency-list">' + rows + '</div>',
      '  <aside class="efficiency-side">',
      '    <h4>资源再分配</h4>',
      reallocations.length
        ? reallocations.slice(0, 5).map(function (r) {
            return '<p><b>' + esc(teamLabel(r.from_team)) + '</b> → <b>' + esc(teamLabel(r.to_team)) + '</b> · ' + compactNumber(r.tokens) + ' tokens</p>';
          }).join('')
        : '<p>暂无再分配建议</p>',
      '    <h4 style="margin-top:14px">待整改团队</h4>',
      recs.length
        ? recs.map(function (t) {
            var first = (t.recommendations || [])[0] || {};
            return '<p><b>' + esc(teamLabel(t.team_id)) + '</b> · ' + esc(t.grade) + ' · ' + esc(first.detail || '等待建议') + '</p>';
          }).join('')
        : '<p>当前无 C/D 级团队</p>',
      '  </aside>',
      '</div>',
    ].join('');
  }

  async function loadEfficiencyView() {
    setHtml('efficiency-panel', '<div class="loading-state"><div class="spinner"></div></div>');
    try {
      state.sustainability = await requestJson(SUSTAINABILITY_API + '/group');
      // 13.1: 取未归因 token，算占比挂到 payload 供顶部健康指标显示
      try {
        var rep = await requestJson(COST_API + '/report?window=' + encodeURIComponent((state.filters && state.filters.window) || '24h'));
        var unattr = (rep && (rep.unattributed_tokens || (rep.reconciliation && rep.reconciliation.unattributed))) || 0;
        var attr = ((state.sustainability && state.sustainability.teams) || []).reduce(function (s, t) { return s + (t.tokens_consumed || 0); }, 0);
        var tot = attr + unattr;
        state.sustainability._unattributed = { tokens: unattr, ratio: tot > 0 ? unattr / tot : 0 };
      } catch (e) { /* 未归因指标可选，失败不影响主视图 */ }
      renderEfficiencyView(state.sustainability);
      return state.sustainability;
    } catch (e) {
      setHtml('efficiency-panel', '<div class="empty-state"><div class="icon">!</div><div>效率数据加载失败</div></div>');
      return null;
    }
  }

  function teamOptionsHtml() {
    if (!state.teams.length) return '<option value="">加载团队中...</option>';
    return state.teams.map(function (team) {
      return '<option value="' + esc(team.team_id) + '"' + (team.preferred ? ' selected' : '') + '>' + esc(team.name || team.team_id) + '</option>';
    }).join('');
  }

  function teamOptionsHtmlWithSelected(selectedTeamId) {
    if (!state.teams.length) return '<option value="">加载团队中...</option>';
    return state.teams.map(function (team) {
      var sel = (team.team_id === selectedTeamId || team.name === selectedTeamId) ? ' selected' : '';
      return '<option value="' + esc(team.team_id) + '"' + sel + '>' + esc(team.name || team.team_id) + '</option>';
    }).join('');
  }

  function updateStatus(summaryPayload) {
    var dot = $('status-dot');
    var text = $('status-text');
    var cache = $('cache-age');
    if (!dot || !text || !cache) return;
    dot.className = 'status-dot pulse';
    if (summaryPayload && summaryPayload.summary) {
      dot.classList.add('healthy');
      text.textContent = '已连接';
      text.style.color = 'var(--koke)';
      var summary = summaryPayload.summary;
      cache.textContent = '· 服务 ' + compactNumber(summary.service_count || 0) + ' · Pod ' + compactNumber(summary.pod_count || 0);
    } else if (state.health && state.health.status) {
      dot.classList.add(state.health.status === 'ok' ? 'healthy' : 'unhealthy');
      text.textContent = state.health.status;
      text.style.color = state.health.status === 'ok' ? 'var(--koke)' : 'var(--shu)';
      cache.textContent = state.health.last_error ? '· ' + state.health.last_error : '';
    } else {
      dot.classList.add('unknown');
      text.textContent = '无数据';
      text.style.color = 'var(--sumi-3)';
      cache.textContent = '';
    }
  }

  function setLoading() {
    setHtml('breakdown-chart', '<div class="loading-state"><div class="spinner"></div></div>');
    setHtml('trends-chart', '<div class="loading-state"><div class="spinner"></div></div>');
    setHtml('governance-panel', '<div class="loading-state"><div class="spinner"></div></div>');
    setHtml('efficiency-panel', '<div class="loading-state"><div class="spinner"></div></div>');
    var tbody = $('pods-tbody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="10" class="loading-state"><div class="spinner" style="margin:20px auto"></div></td></tr>';
    // KPI keeps previous values (don't blank)
  }

  /* ─────────────── Data loaders ─────────────── */
  async function loadTeams() {
    var payload = await requestJson(AGENT_API + '/teams?limit=200&offset=0');
    var teams = asItems(payload, 'items');
    var preferredIndex = teams.findIndex(function (team) {
      var text = ((team.name || '') + ' ' + (team.team_id || '')).toLowerCase();
      return text.indexOf('公有云') >= 0 || text.indexOf('cloud') >= 0 || text.indexOf('finops') >= 0 || text.indexOf('xops') >= 0;
    });
    if (preferredIndex < 0) {
      preferredIndex = teams.findIndex(function (team) { return team.team_id === 'build_system'; });
    }
    state.teams = teams.map(function (team, index) {
      return {
        team_id: team.team_id,
        name: team.name || team.team_id,
        preferred: index === (preferredIndex >= 0 ? preferredIndex : 0),
      };
    });
  }

  async function refreshDashboard() {
    state.filters = getFilters();
    state.budget = loadBudget();
    showAlert('');
    setLoading();
    var refreshBtn = $('refresh-btn');
    if (refreshBtn) refreshBtn.disabled = true;

    var common = {
      window: state.filters.window,
      environment: state.filters.environment,
      service: state.filters.service,
      team: state.filters.team,
    };
    var summaryQuery = queryString(Object.assign({ aggregation: state.filters.aggregation }, common));
    var breakdownQuery = queryString(common);
    var trendQuery = queryString({ aggregation: state.filters.aggregation, window: state.filters.window });
    var podQuery = queryString(Object.assign({}, common, { limit: 100 }));

    try {
      // P8.1-8.3: 成本构成/趋势/明细主源切 Token
      var tokenDim = (state.filters.aggregation === 'service') ? 'team' : state.filters.aggregation;
      if (tokenDim !== 'team' && tokenDim !== 'skill' && tokenDim !== 'phase') tokenDim = 'team';
      // P8R.9: 24h 窗口按小时分桶，否则按天
      var trendBucket = (state.filters.window || '').endsWith('h') ? 'hour' : 'day';
      // P10.1: 透传 team_id 筛选（必须在 Promise.all 数组之外声明）
      var teamFilter = state.filters.team ? '&team_id=' + encodeURIComponent(state.filters.team) : '';
      var responses = await Promise.all([
        requestJson(COST_API + '/health'),
        requestJson(GATE_API + '/health'),
        requestJson(GATE_API + '/stats'),
        requestJson(COST_API + '/summary?' + summaryQuery),
        // P8.1: 成本构成 → Token breakdown（透传 team_id 筛选）
        requestJson(COST_API + '/tokens/breakdown?dim=' + tokenDim + '&window=' + state.filters.window + teamFilter),
        // P8.2: 成本趋势 → Token trend
        requestJson(COST_API + '/tokens/trend?window=' + state.filters.window + '&bucket=' + trendBucket + teamFilter),
        // P8.3: 成本明细 → Token detail
        requestJson(COST_API + '/tokens/detail?group=run&window=' + state.filters.window + '&limit=50' + teamFilter),
        requestJson(SUSTAINABILITY_API + '/group'),
        // P1: Token 数据源（北极星）
        requestJson(COST_API + '/tokens/overview?window=' + state.filters.window),
        state.teams.length ? Promise.resolve(null) : loadTeams(),
      ]);

      state.health = responses[0];
      state.gateHealth = responses[1];
      state.gateStats = responses[2];
      state.summary = responses[3];
      state.breakdown = responses[4] || [];      // P8.1: [{key,total,calls}]
      state.trends = responses[5] || null;        // P8.2: {points,total,...}
      state.pods = responses[6] || [];            // P8.3: [{run_id,phase,total,...}]
      state.sustainability = responses[7];
      state.tokenOverview = responses[8] || null;
      // P8R.2: 赋值 tokenByTeam 供棘轮/治理面板使用
      state.tokenByTeam = (state.tokenOverview && state.tokenOverview.by_team) || [];
      // 9.3: 拉棘轮累计锁定，供 KPI④ 反馈
      try { state.ratchet = await requestJson(COST_API + '/tokens/ratchet'); } catch (e) { state.ratchet = state.ratchet || null; }
      // populateLastFilter after ALL state is assigned so fallbacks work
      // Note: state.summary is CostDashboardResponse; the inner .summary is CostSummary with by_team/by_service
      populateLastFilter(state.summary && state.summary.summary);

      // P1: OpenCost 无数据时降级为中性提示（不显示红条）
      if (!state.summary && !state.breakdown.length && !state.trends.length && !state.pods.length) {
        // 仅在 Token 也无数据时才提示
        if (!state.tokenOverview || !state.tokenOverview.summary || !state.tokenOverview.summary.total) {
          showAlert('基础设施成本（OpenCost）未接入（可选）— Token 成本为北极星指标');
        }
      }

      updateStatus(state.summary);
      renderKpiHero();
      renderBreakdown(state.breakdown);
      renderTrends(state.trends);
      renderPodsTable(state.pods);
      renderEfficiencyView(state.sustainability);
      renderGovernance();
      setText('last-refresh', '最后更新: ' + new Date().toLocaleTimeString('zh-CN'));
    } catch (err) {
      toast('刷新失败: ' + (err && err.message ? err.message : '网络异常'), { kind: 'error', title: '刷新失败' });
    } finally {
      if (refreshBtn) refreshBtn.disabled = false;
    }
  }

  function populateLastFilter(summary) {
    var sel = $('filter-service');
    if (!sel) return;
    var labelEl = $('filter-last-label');
    var agg = (state.filters && state.filters.aggregation) || ($('filter-aggregation') && $('filter-aggregation').value) || 'team';
    var currentVal = sel.value;

    // Determine label text and items source
    var labelText = '服务';
    var items = [];
    if (agg === 'service') {
      labelText = '服务';
      if (summary && Array.isArray(summary.by_service)) {
        items = summary.by_service.map(function (s) { return s.value; });
      }
    } else if (agg === 'team') {
      labelText = '团队';
      if (summary && Array.isArray(summary.by_team)) {
        items = summary.by_team.map(function (t) { return t.value; });
      }
      // Fallback: from pods
      if (!items.length && Array.isArray(state.pods)) {
        var seen = {};
        state.pods.forEach(function (p) {
          var t = (p.team || '').trim();
          if (t && !seen[t]) { seen[t] = true; items.push(t); }
        });
      }
      // Fallback: from state.teams
      if (!items.length && Array.isArray(state.teams)) {
        items = state.teams.map(function (t) { return t.name || t.team_id; });
      }
    } else if (agg === 'environment') {
      labelText = '环境';
      if (summary && Array.isArray(summary.by_environment)) {
        items = summary.by_environment.map(function (e) { return e.value; });
      }
      // Fallback: from pods
      if (!items.length && Array.isArray(state.pods)) {
        var seen2 = {};
        state.pods.forEach(function (p) {
          var env = (p.environment || '').trim();
          if (env && !seen2[env]) { seen2[env] = true; items.push(env); }
        });
      }
    }

    // Update fourth column label
    if (labelEl) labelEl.textContent = labelText;

    // Toggle third column (环境): hide when aggregation=environment (redundant)
    var envLabel = $('filter-env-label');
    if (envLabel) {
      if (agg === 'environment') {
        envLabel.style.display = 'none';
        if ($('filter-environment')) $('filter-environment').value = '';
      } else {
        envLabel.style.display = '';
      }
    }
    if (!items.length) return; // no data yet, keep default

    items.sort(function (a, b) { return a.localeCompare(b); });
    sel.innerHTML = '<option value="">全部</option>' +
      items.map(function (s) { return '<option value="' + esc(s) + '">' + esc(s) + '</option>'; }).join('');

    // Restore previous selection if still available
    if (currentVal) {
      var exists = items.indexOf(currentVal) >= 0;
      sel.value = exists ? currentVal : '';
    }
  }

  function resetFilters() {
    if ($('filter-aggregation')) $('filter-aggregation').value = 'team';
    if ($('filter-window')) $('filter-window').value = '24h';
    if ($('filter-environment')) $('filter-environment').value = '';
    if ($('filter-service')) $('filter-service').value = '';
    refreshDashboard();
  }

  function targetFromSource(source, index) {
    if (source === 'pod') {
      // P8.3: pods is now token detail rows [{run_id, total, ...}]
      var sorted = state.pods.slice().sort(function (a, b) { return Number(b.total || 0) - Number(a.total || 0); });
      return sorted[index || 0] || null;
    }
    return state.breakdown[index || 0] || null;
  }

  // P8R.5: 杠杆建议
  function leverActionHint(lever, split) {
    split = split || { skill_pct: 0, collab_pct: 0, skill: 0, collab: 0 };
    return lever === 'skill_extraction'
      ? '协作杠杆占 ' + (split.collab_pct * 100).toFixed(0) + '%，建议把重复意图萃取为已验证 skill（技能萃取页），命中后 task 段 token 应下降'
      : 'Skill 杠杆占 ' + (split.skill_pct * 100).toFixed(0) + '%，建议优化 Agent 路由/减少无效往返（议事广场复盘），drill/plaza 段 token 应下降';
  }

  function targetLabel(target) {
    if (!target) return '成本异常';
    if (target.run_id) return 'Run ' + (target.run_id || '').slice(0, 8);
    // P8R.3: token breakdown 字段 {key, total}
    return (state.filters.aggregation || 'cost') + ' ' + (target.key || '');
  }

  // 当顶部操作栏按钮所需的输入位于下方「治理动作」面板时，滚动过去并高亮提示。
  function revealGovernanceAction(message, focusTeam) {
    var panel = document.querySelector('.panel--governance');
    if (panel && typeof panel.scrollIntoView === 'function') {
      panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    if (message) setText('cost-action-result', message);
    if (focusTeam) {
      var teamSelect = $('cost-action-team');
      if (teamSelect) {
        setTimeout(function () {
          try { teamSelect.focus(); } catch (e) {}
          teamSelect.classList.add('cost-input-flash');
          setTimeout(function () { teamSelect.classList.remove('cost-input-flash'); }, 1600);
        }, 360);
      }
    }
  }

  // 9.1: 复用该团队已有 active 目标，否则按当前消耗自动建一个 tokens_per_goal 目标
  async function ensureTargetForTeam(teamId, gov) {
    try {
      var list = await requestJson(COST_API + '/targets?status=active');
      var hit = (list || []).find(function (t) { return t.scope === 'team' && t.ref_id === teamId; });
      if (hit) return hit.id;
      // 用「平均每调用 token」当前值的 0.7 作为目标（9.2 口径），baseline 由后端自动取
      var byTeam = (state.tokenByTeam || []).find(function (t) { return t.team_id === teamId; });
      var perCall = (byTeam && byTeam.calls) ? Math.round(byTeam.total / byTeam.calls) : 0;
      var r = await requestJson(COST_API + '/targets', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scope: 'team', ref_id: teamId, metric: 'tokens_per_goal',
          target: perCall ? Math.round(perCall * 0.7) : 0,
          lever: (gov && gov.lever) || 'skill_extraction',
        }),
      });
      return (r && r.id) || '';
    } catch (e) { return ''; }
  }

  async function createOptimizationTask(source, index) {
    var teamSelect = $('cost-action-team');
    var teamId = teamSelect ? teamSelect.value : '';
    if (!teamId) {
      revealGovernanceAction('请在下方「治理动作」面板选择指派团队后再创建任务', true);
      toast('请在下方治理动作面板选择团队', { kind: 'warn' });
      return null;
    }
    var target = targetFromSource(source, index);
    if (!target) {
      revealGovernanceAction('暂无可用 Token 成本目标 — 请先产生 LLM 调用', false);
      toast('暂无可用成本目标，请先刷新成本数据', { kind: 'warn' });
      return null;
    }
    var result = $('cost-action-result');
    if (result) result.textContent = '正在创建优化任务...';

    // P8R.5: 带杠杆建议
    var leverHint = leverActionHint(state.governanceTarget && state.governanceTarget.lever, state.governanceTarget && state.governanceTarget.lever_split);
    var title = 'Token 成本优化: ' + targetLabel(target);
    var description = [
      '来源: cost-dashboard',
      '治理目标: ' + targetLabel(target),
      '当前消耗: ' + compactNumber(target.total || 0) + ' tokens',
      '筛选窗口: ' + (state.filters.window || '24h'),
      leverHint ? '' : '',
      leverHint || '',
      '',
      '请分析该团队的 Token 消耗分布，按上述杠杆方向制定优化方案。完成后回写 token 变化、验证证据和后续演进建议。',
    ].join('\n');
    // 9.1: 确保有 target_id，任务完成时后端 CostTargetTracker 据此复测目标进度
    var targetId = await ensureTargetForTeam(teamId, state.governanceTarget);
    var payload = {
      title: title,
      description: description,
      priority: 1,
      metadata: {
        source: 'cost-dashboard',
        evidence_type: 'cost_anomaly',
        cost_filters: state.filters,
        cost_target: target,
        target_id: targetId || '',
        suggested_followups: ['cost_gate', 'plaza_discussion', 'evolution_item'],
      },
    };

    try {
      var created = await requestJson(AGENT_API + '/teams/' + encodeURIComponent(teamId) + '/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (created && created.task_id) {
        if (result) {
          result.innerHTML = '已派发任务 <a href="/agent-team-config.html?team=' + encodeURIComponent(teamId) + '" style="color:var(--koke)">查看团队任务▸</a> · ' + esc(created.task_id)
            + (targetId ? '<br><span style="font-size:11px;color:var(--sumi-3)">已绑定目标 ' + esc(targetId) + '，任务完成将自动复测进度</span>' : '');
        }
        toast('任务 ' + created.task_id + ' 已派发', { kind: 'success', title: '已派发' });
        if (window.loadTargets) loadTargets();
        return created;
      }
      if (result) result.textContent = '创建任务失败，请查看后端日志或 request_id';
      toast('创建任务失败', { kind: 'error' });
      return null;
    } catch (e) {
      if (result) result.textContent = '创建任务失败: ' + e.message;
      toast('创建任务失败: ' + e.message, { kind: 'error' });
      return null;
    }
  }

  async function ensureCostPlaza() {
    var payload = await requestJson(AGENT_API + '/plaza?limit=50&offset=0');
    var plazas = asItems(payload, 'items');
    var existing = plazas.find(function (plaza) {
      var text = ((plaza.name || '') + ' ' + (plaza.description || '')).toLowerCase();
      return text.indexOf('成本') >= 0 || text.indexOf('finops') >= 0 || text.indexOf('cost') >= 0;
    }) || plazas[0];
    if (existing && existing.id) return existing;

    return await requestJson(AGENT_API + '/plaza', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: '成本治理议事厅',
        description: '由成本治理工作台创建，用于讨论成本异常、预算风险、标签归因和优化演进。',
        selected_agents: [],
        chairperson_agent_id: '',
      }),
    });
  }

  async function createPlazaTopic(source, index) {
    var target = targetFromSource(source, index);
    if (!target) {
      revealGovernanceAction('暂无可用 Token 成本目标 — 无法创建 Plaza 话题', false);
      toast('暂无可用成本目标，请先刷新成本数据', { kind: 'warn' });
      return null;
    }
    var result = $('cost-action-result');
    if (result) result.textContent = '正在创建 Plaza 话题...';

    var plaza = await ensureCostPlaza();
    if (!plaza || !plaza.id) {
      if (result) result.textContent = '没有可用 Plaza，创建话题失败';
      toast('Plaza 不可用', { kind: 'error' });
      return null;
    }

    // P8R.5: 带杠杆建议
    var leverHint = leverActionHint(state.governanceTarget && state.governanceTarget.lever, state.governanceTarget && state.governanceTarget.lever_split);
    var topic = 'Token 成本治理: ' + targetLabel(target);
    var description = [
      '来源: cost-dashboard',
      '治理目标: ' + targetLabel(target),
      '当前消耗: ' + compactNumber(target.total || 0) + ' tokens',
      '筛选窗口: ' + (state.filters.window || '24h'),
      leverHint || '',
      '',
      '请从 Token 消耗归因、杠杆优化方向、可回滚优化方案和是否需要生成 EvolutionItem 角度讨论。',
    ].join('\n');

    try {
      var discussion = await requestJson(AGENT_API + '/plaza/' + encodeURIComponent(plaza.id) + '/discussions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic,
          description: description,
          goal: '形成可派发的成本优化任务，并判断是否需要进入系统演进。',
          moderator_agent_id: '',
          max_rounds: 3,
          // 关联当前选中/治理目标团队 → 话题归属该团队，可按团队过滤查看
          team_id: (target && target.ref_id) || (state.filters && state.filters.team) || '',
        }),
      });
      if (discussion && discussion.id) {
        if (result) {
          // 深链到话题所在的「成本治理议事厅」+ 具体讨论，否则 plaza.html 默认打开别的厅，看不到刚建的话题
          var deepLink = '/plaza.html?plaza_id=' + encodeURIComponent(plaza.id) + '&discussion_id=' + encodeURIComponent(discussion.id);
          result.innerHTML = '已在「' + esc(plaza.name || '成本治理议事厅') + '」创建话题 <a href="' + deepLink + '" style="color:var(--koke)">打开该话题▸</a> · ' + esc(discussion.id);
        }
        toast('Plaza 话题已创建', { kind: 'success', title: '已发起' });
        return { plaza: plaza, discussion: discussion };
      }
      if (result) result.textContent = '创建 Plaza 话题失败，请查看后端日志或 request_id';
      toast('创建话题失败', { kind: 'error' });
      return null;
    } catch (e) {
      if (result) result.textContent = '创建 Plaza 话题失败: ' + e.message;
      toast('创建话题失败: ' + e.message, { kind: 'error' });
      return null;
    }
  }

  async function runCostGateSelfCheck() {
    var result = $('cost-action-result');
    if (result) result.textContent = '正在运行 Token Gate 自检...';
    try {
      // 用「效率视角」的真实数据(含真实评分，bug-062 后从持久化 trials 补回)做自检。
      // 旧实现硬编码 score:0 + min_efficiency:1.0 → eff 恒为 0 → 永远 block → 自检总是失败。
      var sust = state.sustainability;
      if (!sust || !sust.teams) { sust = await requestJson(SUSTAINABILITY_API + '/group'); }
      var teams = (sust && sust.teams) || [];
      // 取 token 消耗最高的团队作为自检样本（最能体现"高 token"风险）
      var sample = teams.slice().sort(function (a, b) { return (b.tokens_consumed || 0) - (a.tokens_consumed || 0); })[0] || null;
      var inlineData = sample
        ? { total: sample.tokens_consumed || 0, calls: sample.trial_count || 0, score: sample.total_score || 0 }
        : { total: 0, calls: 0, score: 0 };
      var sampleName = sample ? (sample.team_id || '样本') : '样本';
      // 13.4 自适应阈值：底线效率 = 全员真实效率 P25 × 0.5（替代写死的 0.05），最低 0.02。
      var effs = teams.map(function (t) { return t.token_efficiency || 0; }).filter(function (e) { return e > 0; }).sort(function (a, b) { return a - b; });
      var p25 = effs.length ? effs[Math.floor(effs.length * 0.25)] : 0;
      var minEff = Math.max(p25 * 0.5, 0.02);
      var report = await requestJson(GATE_API + '/token/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inline: inlineData,
          // max_tokens 给足，避免样本团队 token 多被误判超预算。
          budget: { min_efficiency: minEff, max_tokens: 1000000 },
        }),
      });
      if (report) {
        var decision = report.decision || '-';
        var violations = (report.violations || []).length;
        var eff = report.efficiency != null ? report.efficiency.toFixed(4) : '—';
        if (result) {
          var icon = decision === 'pass' ? '✅' : decision === 'warn' ? '⚠️' : '🚫';
          result.innerHTML = icon + ' Token Gate【' + esc(sampleName) + '】: <strong>' + esc(decision) + '</strong> · 效率 ' + eff + ' · 底线 ' + minEff.toFixed(3) + '(全员P25×0.5) · 违规 ' + compactNumber(violations);
        }
        // 更新 Gate 统计
        var tokStats = await requestJson(GATE_API + '/token/stats');
        if (tokStats) { state.gateStats = tokStats; renderGovernance(); }
        var kind = decision === 'block' ? 'warn' : 'success';
        toast('Token Gate: ' + decision + ' · 效率 ' + eff, { kind: kind, title: '自检完成' });
        return report;
      }
      if (result) result.textContent = 'Token Gate 自检失败，API 无返回数据';
      toast('Token Gate 自检失败', { kind: 'error' });
      return null;
    } catch (e) {
      if (result) result.textContent = 'Token Gate 自检失败: ' + e.message;
      toast('Token Gate 自检失败: ' + e.message, { kind: 'error' });
      return null;
    }
  }

  async function generateLabelPatch(source, index) {
    var result = $('cost-action-result');
    var target = targetFromSource(source, index);
    if (!target || !target.pod) {
      if (result) result.textContent = '请选择一条 Pod 成本明细后再生成标签补丁';
      toast('请选择 Pod', { kind: 'warn' });
      return null;
    }
    if (result) result.textContent = '正在生成标签补丁...';

    var params = queryString({
      pod_name: target.pod,
      namespace: target.namespace || 'default',
      service: target.service || (target.labels && target.labels.app) || 'unknown',
      environment: target.environment || 'development',
      team: target.team || 'platform',
    });
    try {
      var patch = await requestJson(COST_API + '/labels/generate?' + params, { method: 'POST' });
      if (patch) {
        if (result) {
          result.innerHTML = '已生成标签补丁: <code>' + esc(JSON.stringify(patch.patch || patch)) + '</code>';
        }
        toast('标签补丁已生成', { kind: 'success', title: '已生成' });
        return patch;
      }
      if (result) result.textContent = '标签补丁生成失败，请查看后端日志或 request_id';
      toast('标签补丁生成失败', { kind: 'error' });
      return null;
    } catch (e) {
      if (result) result.textContent = '标签补丁生成失败: ' + e.message;
      toast('标签补丁生成失败: ' + e.message, { kind: 'error' });
      return null;
    }
  }

  function init() {
    window.refreshDashboard = refreshDashboard;
    window.resetFilters = resetFilters;
    window.createOptimizationTask = createOptimizationTask;
    window.createPlazaTopic = createPlazaTopic;
    window.runCostGateSelfCheck = runCostGateSelfCheck;
    window.generateLabelPatch = generateLabelPatch;
    window.loadEfficiencyView = loadEfficiencyView;
    window.toggleEffSort = function () {
      state.effSort = state.effSort === 'worst' ? 'best' : 'worst';
      if (state.sustainability) renderEfficiencyView(state.sustainability);
    };

    // Budget UI wiring
    initBudgetUI();

    // Plaza source back-link
    var params = new URLSearchParams(window.location.search);
    var plazaId = params.get('plaza_id');
    var discId = params.get('discussion_id');
    if (plazaId && params.get('source') === 'plaza') {
      var banner = document.createElement('div');
      banner.style.cssText = 'display:flex;align-items:center;gap:8px;padding:10px 16px;margin-bottom:16px;background:rgba(38,162,105,0.08);border:1px solid rgba(38,162,105,0.2);border-radius:8px;font-size:12px';
      banner.innerHTML = '<span>🏛️ 来自议事厅讨论</span><a href="/plaza.html?plaza_id=' + encodeURIComponent(plazaId) + '&discussion_id=' + encodeURIComponent(discId || '') + '" style="color:var(--koke);text-decoration:none;font-weight:600">← 返回讨论</a>';
      var main = document.querySelector('.cost-dashboard');
      if (main) main.insertBefore(banner, main.firstChild);
    }

    refreshDashboard();
    setInterval(function () {
      if (!document.hidden) refreshDashboard();
    }, 60000);

    // P10.5: 轮询目标进度变化（30s），有变化则刷新目标卡 + KPI
    setInterval(function () {
      if (document.hidden) return;
      fetch(COST_API + '/targets/changed', { credentials: 'same-origin' })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          if (!d || !d.items) return;
          var changed = d.items.some(function (it) {
            return it.status === 'achieved' || (it.progress !== undefined && it.progress >= 1.0);
          });
          if (changed) {
            if (window.loadTargets) loadTargets();
            renderKpiHero();
          }
        })
        .catch(function () {});
    }, 30000);

    // 9.4: 从数字孪生评分后跳回 ?refresh=efficiency → 自动刷新效率视角，免手点
    if (params.get('refresh') === 'efficiency') {
      setTimeout(function () { if (typeof loadEfficiencyView === 'function') loadEfficiencyView(); }, 800);
      history.replaceState({}, '', location.pathname);
    }
  }

  // 「如何推进」引导文案：按 metric/杠杆给出可点击的下一步
  function targetHowto(t) {
    var ref = encodeURIComponent(t.ref_id || '');
    if (t.metric === 'score_per_1k') {
      return '推进：去 <a href="/Agent-digital-twin.html?team=' + ref + '" style="color:var(--koke)">数字孪生</a> 为该团队跑「评分试炼」提高 score/1k → 回来点「刷新效率」→ 棘轮可锁定';
    }
    // tokens_per_goal — 13.5: 附「预计可省 token」量化（基于当前消耗 × 各杠杆经验降幅）
    var cur = Number(t.current || t.total || t.value || 0);
    var save = function (pct) { return cur > 0 ? '（预计可省 ~' + compactNumber(Math.round(cur * pct)) + ' token · ~' + Math.round(pct * 100) + '%）' : ''; };
    return t.lever === 'collaboration_routing'
      ? '推进：去 <a href="/plaza.html" style="color:var(--koke)">议事广场</a> 复盘协作/优化 Agent 路由，减少无效往返 → 同意图 token 下降 ' + save(0.15)
      : '推进：去 <a href="/skill-extract.html?team_id=' + ref + '&focus=redundant" style="color:var(--koke)">技能萃取</a> 把重复意图固化为已验证 skill，复跑同意图命中 skill → token 下降 ' + save(0.25);
  }

  // ═══ P5.2: Token 优化目标管理 ═══
  async function loadTargets() {
    var el = document.getElementById('target-list');
    if (!el) return;
    try {
      var resp = await fetch(COST_API + '/targets', { credentials: 'same-origin' });
      if (!resp.ok) { el.innerHTML = '<p style="color:var(--dim);font-size:12px">目标加载失败</p>'; return; }
      var targets = await resp.json();
      if (!targets || !targets.length) {
        el.innerHTML = '<p style="color:var(--sumi-3);font-size:12px;padding:8px 0">暂无目标 — 点击「+ 设定目标」创建第一个 token 优化目标</p>';
        return;
      }
      var esc = window.escapeHtml || function (s) { return String(s == null ? '' : s); };
      var html = targets.map(function (t) {
        var pct = Math.round((t.progress || 0) * 100);
        var barColor = pct >= 100 ? 'var(--koke)' : pct >= 50 ? 'var(--kitsune)' : 'var(--shu)';
        return '<div style="padding:10px 12px;background:var(--ob-bg-section);border:1px solid var(--ob-border);border-radius:8px;margin-bottom:8px">' +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">' +
          '<span style="font-weight:600;font-size:12px">' + esc(t.scope) + ': ' + esc(t.ref_id || '—') + '</span>' +
          '<span style="font-size:10px;color:var(--sumi-3)">杠杆: ' + esc(t.lever) + '</span>' +
          '</div>' +
          '<div style="display:flex;gap:6px;align-items:center;font-size:11px;color:var(--sumi-3);margin-bottom:4px">' +
          '<span>baseline ' + (t.baseline || 0).toFixed(1) + '</span>' +
          '<span>→ target ' + (t.target || 0).toFixed(1) + '</span>' +
          '<span style="margin-left:auto;color:' + barColor + ';font-weight:600">' + pct + '%</span>' +
          '</div>' +
          '<div style="height:6px;background:rgba(255,255,255,.05);border-radius:3px;overflow:hidden">' +
          '<div style="height:100%;width:' + Math.max(0, Math.min(100, pct)) + '%;background:' + barColor + ';transition:width .3s"></div>' +
          '</div>' +
          // 「如何推进」引导：按 metric/杠杆给出明确下一步动作 + 链接
          '<div style="font-size:10px;color:var(--kitsune);margin-top:6px;line-height:1.5">' + targetHowto(t) + '</div>' +
          '<div style="display:flex;justify-content:space-between;margin-top:6px">' +
          '<span style="font-size:10px;color:var(--sumi-3)">metric: ' + esc(t.metric) + ' · ' + esc(t.status) + '</span>' +
          '<button class="btn cost-btn cost-btn--ghost" style="font-size:9px;padding:2px 8px" onclick="deleteTarget(\'' + esc(t.id) + '\')">删除</button>' +
          '</div>' +
          '</div>';
      }).join('');
      el.innerHTML = html;
    } catch (e) {
      el.innerHTML = '<p style="color:var(--dim);font-size:12px">目标加载失败: ' + (e.message || '') + '</p>';
    }
  }

  async function createTokenTarget() {
    var body = {
      scope: document.getElementById('tgt-scope').value || 'team',
      ref_id: document.getElementById('tgt-ref').value || 'default',
      metric: document.getElementById('tgt-metric').value || 'score_per_1k',
      target: parseFloat(document.getElementById('tgt-value').value) || 0,
      lever: document.getElementById('tgt-lever').value || 'skill_extraction',
    };
    if (!body.ref_id || body.target <= 0) {
      toast('请填写目标 ID 和目标值');
      return;
    }
    try {
      var resp = await fetch(COST_API + '/targets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        credentials: 'same-origin',
      });
      if (!resp.ok) {
        var err = await resp.json().catch(function () { return {}; });
        toast('创建失败: ' + (err.detail || resp.status));
        return;
      }
      toast('✅ 目标已创建');
      toggleTargetForm();
      loadTargets();
    } catch (e) {
      toast('创建失败: ' + (e.message || ''));
    }
  }

  async function deleteTarget(tid) {
    if (!confirm('删除目标 ' + tid + '？')) return;
    try {
      await fetch(COST_API + '/targets/' + encodeURIComponent(tid), {
        method: 'DELETE', credentials: 'same-origin',
      });
      toast('已删除');
      loadTargets();
    } catch (e) { toast('删除失败: ' + (e.message || '')); }
  }

  function toggleTargetForm() {
    var el = document.getElementById('target-form');
    if (el) el.style.display = el.style.display === 'none' ? '' : 'none';
    // 展开时填充下拉选项
    if (el && el.style.display !== 'none') {
      populateTargetRefOptions();
    }
  }

  // 根据范围（团队/技能）动态填充目标 ID 下拉
  async function populateTargetRefOptions() {
    var sel = document.getElementById('tgt-ref');
    var scopeEl = document.getElementById('tgt-scope');
    if (!sel || !scopeEl) return;
    var scope = scopeEl.value || 'team';
    sel.innerHTML = '<option value="">加载中...</option>';
    try {
      if (scope === 'team') {
        // 从 state.teams 或 token by-team 获取团队列表
        var teams = [];
        if (Array.isArray(state.teams) && state.teams.length) {
          teams = state.teams.map(function (t) { return { id: t.team_id, name: t.name || t.team_id, tokens: 0 }; });
        }
        // 补充从 token overview 获取的团队
        try {
          var resp = await fetch(COST_API + '/tokens/by-team?window=7d', { credentials: 'same-origin' });
          if (resp.ok) {
            var tokTeams = await resp.json();
            (tokTeams || []).forEach(function (t) {
              if (t.team_id && !teams.some(function (x) { return x.id === t.team_id; })) {
                teams.push({ id: t.team_id, name: t.team_id, tokens: t.total || 0 });
              }
            });
          }
        } catch (e) { /* ignore */ }
        if (!teams.length) {
          sel.innerHTML = '<option value="">暂无团队数据</option>';
          return;
        }
        sel.innerHTML = teams.map(function (t) {
          return '<option value="' + esc(t.id) + '">' + esc(t.name) + (t.tokens ? ' (' + compactNumber(t.tokens) + ' tokens)' : '') + '</option>';
        }).join('');
      } else {
        // 从 token by-skill 获取技能列表
        var resp2 = await fetch(COST_API + '/tokens/by-skill?window=7d', { credentials: 'same-origin' });
        var skills = [];
        if (resp2.ok) {
          skills = await resp2.json();
        }
        if (!skills || !skills.length) {
          sel.innerHTML = '<option value="">暂无技能 token 数据</option>';
          return;
        }
        sel.innerHTML = skills.map(function (s) {
          return '<option value="' + esc(s.skill_id) + '">' + esc(s.skill_id) + ' (' + compactNumber(s.total || 0) + ' tokens)</option>';
        }).join('');
      }
    } catch (e) {
      sel.innerHTML = '<option value="">加载失败</option>';
    }
  }

  // ═══ P5.3: 生成成本报告 ═══
  async function generateCostReport() {
    var btn = document.getElementById('report-btn');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ 生成中...'; }
    try {
      var win = state.window || '24h';
      var resp = await fetch(COST_API + '/report?window=' + encodeURIComponent(win), { credentials: 'same-origin' });
      if (!resp.ok) { toast('报告生成失败: HTTP ' + resp.status); return; }
      var r = await resp.json();
      renderReportPanel(r);
    } catch (e) {
      toast('报告生成失败: ' + (e.message || ''));
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '📊 生成报告'; }
    }
  }

  function renderReportPanel(r) {
    var esc = window.escapeHtml || function (s) { return String(s == null ? '' : s); };
    var consistent = r.reconciliation && r.reconciliation.consistent;
    var bannerColor = consistent ? 'var(--koke)' : 'var(--shu)';
    var bannerText = consistent ? '✅ 账对上 (phase_sum == team_sum)' : '❌ 不一致 (phase_sum != team_sum)';

    var html = '<div style="position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:1000;display:flex;align-items:center;justify-content:center" onclick="if(event.target===this)this.remove()">' +
      '<div style="background:var(--ob-bg-section);border:1px solid var(--ob-border);border-radius:12px;max-width:900px;width:92%;max-height:85vh;overflow-y:auto;padding:20px 24px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">' +
      '<h3 style="margin:0">📊 Token 成本报告 <span style="font-size:12px;color:var(--sumi-3);font-weight:400">· ' + esc(r.window || '') + '</span></h3>' +
      '<button class="btn cost-btn cost-btn--ghost cost-btn--sm" onclick="this.closest(\'div[style*=fixed]\').remove()">关闭</button>' +
      '</div>' +
      '<div style="padding:8px 12px;background:' + bannerColor + '20;border:1px solid ' + bannerColor + '60;border-radius:6px;margin-bottom:14px;font-size:12px;color:' + bannerColor + '">' + bannerText + '</div>';

    // ① 消耗（by_phase）
    var byPhase = r.totals && r.totals.by_phase || r.by_phase || {};
    var phaseItems = Object.keys(byPhase).map(function (k) {
      var v = byPhase[k];
      var total = typeof v === 'object' ? (v.total || 0) : v;
      return '<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:12px;border-bottom:1px solid var(--ob-border)">' +
        '<span>' + esc(k) + '</span><span style="font-family:monospace">' + Number(total).toLocaleString() + ' tokens</span></div>';
    }).join('');
    html += '<h4 style="font-size:13px;margin:12px 0 6px">① 消耗（按阶段）</h4>' +
      (phaseItems || '<p style="color:var(--sumi-3);font-size:12px">暂无数据</p>');

    // ② 优化对比（targets）
    var targets = r.targets || [];
    html += '<h4 style="font-size:13px;margin:14px 0 6px">② 优化对比（目标进度）</h4>';
    if (targets.length) {
      html += targets.map(function (t) {
        var pct = Math.round((t.progress || 0) * 100);
        var saved = ((t.baseline || 0) - (t.current || 0)).toFixed(1);
        return '<div style="padding:6px 0;font-size:12px;border-bottom:1px solid var(--ob-border)">' +
          '<div style="display:flex;justify-content:space-between"><span>' + esc(t.scope) + ': ' + esc(t.ref_id) + '</span><span>' + pct + '%</span></div>' +
          '<span style="color:var(--sumi-3);font-size:11px">baseline ' + (t.baseline || 0).toFixed(1) + ' → current ' + (t.current || 0).toFixed(1) + ' (target ' + (t.target || 0).toFixed(1) + ') · 节省 ' + saved + '</span>' +
          '</div>';
      }).join('');
    } else {
      html += '<p style="color:var(--sumi-3);font-size:12px">暂无目标</p>';
    }

    // ③ 锁定（ratchet）
    var locked = r.ratchet_locked || [];
    html += '<h4 style="font-size:13px;margin:14px 0 6px">③ 锁定（棘轮累计节省）</h4>';
    if (locked.length) {
      html += locked.map(function (l) {
        return '<div style="padding:6px 0;font-size:12px;border-bottom:1px solid var(--ob-border);display:flex;justify-content:space-between">' +
          '<span>' + esc(l.metric_key) + '</span><span style="font-family:monospace;color:var(--koke)">gen ' + l.generation + ' · ' + Number(l.value).toFixed(4) + '</span></div>';
      }).join('');
    } else {
      html += '<p style="color:var(--sumi-3);font-size:12px">暂无锁定记录</p>';
    }

    html += '</div></div>';
    var div = document.createElement('div');
    div.innerHTML = html;
    document.body.appendChild(div.firstChild);
  }

  // 暴露给 inline HTML 调用
  window.toggleTargetForm = toggleTargetForm;
  window.createTokenTarget = createTokenTarget;
  window.deleteTarget = deleteTarget;
  window.loadTargets = loadTargets;
  window.generateCostReport = generateCostReport;
  window.populateTargetRefOptions = populateTargetRefOptions;

  window.CostDashboard = {
    state: state,
    normalizeTrends: normalizeTrends,
    normalizePods: normalizePods,
    renderTrends: renderTrends,
    renderPodsTable: renderPodsTable,
    renderSummary: renderKpiHero,
    renderBreakdown: renderBreakdown,
    renderEfficiencyView: renderEfficiencyView,
    loadEfficiencyView: loadEfficiencyView,
    renderGovernance: renderGovernance,
    refreshDashboard: refreshDashboard,
    resetFilters: resetFilters,
    createOptimizationTask: createOptimizationTask,
    createPlazaTopic: createPlazaTopic,
    runCostGateSelfCheck: runCostGateSelfCheck,
    generateLabelPatch: generateLabelPatch,
    loadTargets: loadTargets,
    createTokenTarget: createTokenTarget,
    toggleTargetForm: toggleTargetForm,
    generateCostReport: generateCostReport,
  };

  if (!window.__AG_COST_DASHBOARD_NO_INIT__) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
  }
})();
