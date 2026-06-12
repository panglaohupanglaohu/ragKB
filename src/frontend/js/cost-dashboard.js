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
    return {
      aggregation: ($('filter-aggregation') && $('filter-aggregation').value) || 'team',
      window: ($('filter-window') && $('filter-window').value) || '24h',
      environment: ($('filter-environment') && $('filter-environment').value) || '',
      service: (($('filter-service') && $('filter-service').value) || '').trim(),
    };
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
    var summary = state.summary && state.summary.summary;
    if (!summary) {
      host.innerHTML = '<div class="empty-state"><div class="icon">∅</div><div>暂无成本摘要</div></div>';
      setHtml('summary-grid', host.innerHTML);
      return;
    }

    var totalCost = Number(summary.total_cost || 0);
    // Note: backend has no /previous-period endpoint, so the delta is "vs last refresh"
    // (which still detects sudden cost spikes between auto-refreshes).
    var delta = (state.prevTotal != null && state.prevTotal > 0)
      ? (totalCost - state.prevTotal) / state.prevTotal : null;
    state.prevTotal = totalCost;

    // Budget burn rate (per-team / per-month). If budget set and current cost exceeds prorated share → critical
    var budget = state.budget;
    var heroKind = totalCost > 5 ? 'critical' : totalCost > 1 ? 'warning' : 'success';
    var budgetWarn = null;
    if (budget && budget.monthly > 0) {
      // Crude prorate: assume window cost * 30d / windowDays is the monthly burn
      var windowDays = (state.filters.window === '24h' ? 1 : state.filters.window === '7d' ? 7 : 30);
      var monthlyBurn = totalCost * (30 / Math.max(1, windowDays));
      var ratio = monthlyBurn / budget.monthly;
      if (ratio >= 1) { heroKind = 'critical'; budgetWarn = { ratio: ratio, monthlyBurn: monthlyBurn }; }
      else if (ratio >= 0.8) { heroKind = heroKind === 'critical' ? 'critical' : 'warning'; budgetWarn = { ratio: ratio, monthlyBurn: monthlyBurn }; }
    }

    var podCount = Number(summary.pod_count || summary.total_pods || 0);
    var containerCount = Number(summary.container_count || 0);
    var serviceCount = Number(summary.service_count || (summary.by_service || []).length);
    var envCount = Number(summary.environment_count || (summary.by_environment || []).length);
    var teamCount = Number(summary.team_count || (summary.by_team || []).length);
    var topTeam = maxCost(summary.by_team);
    var topTeamValue = topTeam > 0 ? topTeam : null;

    // Per-pod avg cost
    var avgCost = podCount > 0 ? totalCost / podCount : 0;

    // Hero sub: delta label (vs last refresh) + budget pill if applicable
    var deltaLabel = 'vs 上次刷新';
    var heroSub = windowLabel(state.filters.window) + ' · ' + compactNumber(podCount) + ' 个 Pod';
    var heroBudgetPill = '';
    if (budgetWarn) {
      heroBudgetPill = ' · <span class="kpi-card__pill kpi-card__pill--' +
        (heroKind === 'critical' ? 'alert' : 'warn') + '">' +
        '预算燃烧 ' + (budgetWarn.ratio * 100).toFixed(0) + '%' +
        (budgetWarn.ratio >= 1 ? ' · 已超预算' : '') +
        '</span>';
    }

    host.innerHTML =
      '<div class="kpi-hero__skeleton">' +
      kpiCardHtml({
        kind: heroKind === 'success' ? 'hero' : (heroKind === 'critical' ? 'critical' : 'warning'),
        icon: heroIcon('wallet'),
        label: '总成本',
        value: money(totalCost),
        sub: heroSub,
        subExtra: heroBudgetPill,
        delta: delta != null ? { value: delta, format: 'pct' } : null,
        deltaLabel: deltaLabel,
        spark: buildSparkFromSummary(summary),
      }) +
      kpiCardHtml({
        kind: 'standard',
        icon: heroIcon('pod'),
        label: '活跃 Pod',
        value: compactNumber(podCount),
        sub: '容器 ' + compactNumber(containerCount) + ' · 均摊 ' + money(avgCost) + '/Pod',
      }) +
      kpiCardHtml({
        kind: 'standard',
        icon: heroIcon('grid'),
        label: '服务 × 环境',
        value: compactNumber(serviceCount),
        sub: '环境 ' + compactNumber(envCount) + ' · 团队 ' + compactNumber(teamCount),
      }) +
      kpiCardHtml({
        kind: topTeamValue != null && topTeamValue > 1 ? 'warning' : 'muted',
        icon: heroIcon('team'),
        label: 'Top 团队',
        value: money(topTeamValue || 0),
        sub: teamCount > 0 ? (teamCount + ' 个团队贡献成本') : '等待团队归因数据',
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
      container.innerHTML = '<div class="empty-state"><div class="icon">∅</div><div>该维度下暂无数据</div></div>';
      return;
    }
    var filtered = items.filter(function (item) {
      return item.value !== '(unknown)' && item.value !== 'unknown';
    });
    if (!filtered.length) filtered = items.slice();

    var sorted = filtered.slice().sort(function (a, b) {
      return Number(b.total_cost || 0) - Number(a.total_cost || 0);
    }).slice(0, 10);
    var grand = sorted.reduce(function (s, x) { return s + Number(x.total_cost || 0); }, 0);
    var max = Math.max.apply(null, sorted.map(function (item) { return Number(item.total_cost || 0); }).concat([0.0001]));

    var rows = sorted.map(function (item, idx) {
      var v = Number(item.total_cost || 0);
      var pct = (v / max) * 100;
      var share = grand > 0 ? (v / grand) * 100 : 0;
      var tier = idx === 0 ? 'accent' : (v / max > 0.6 ? 'warning' : '');
      return [
        '<li class="hbar-item ' + (tier ? 'hbar-item--' + tier : '') + (idx === 0 ? ' hbar-item--top' : '') + '">',
        '  <div class="hbar-rank">#' + (idx + 1).toString().padStart(2, '0') + '</div>',
        '  <div class="hbar-label" title="' + esc(item.value || '?') + '">' + esc(item.value || '?') + '</div>',
        '  <div class="hbar-track">',
        '    <div class="hbar-fill" style="width:' + pct.toFixed(1) + '%"></div>',
        '  </div>',
        '  <div class="hbar-value">' + money(v) + '<span class="hbar-pct">' + share.toFixed(1) + '%</span></div>',
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
    var series = Array.isArray(seriesList) && seriesList.length ? seriesList[0] : null;
    if (!series || !series.points || series.points.length < 1) {
      container.innerHTML = '<div class="empty-state"><div class="icon">∅</div><div>趋势数据不足</div><div style="font-size:12px;color:var(--dim);margin-top:4px">需要 OpenCost 返回至少一个时间点</div></div>';
      if (sub) sub.textContent = '—';
      return;
    }
    var points = series.points;
    var values = points.map(function (p) { return Number(p.cost || 0); });
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
                 money(fcEndValue) + ' (' + (fcDelta * 100).toFixed(1) + '%)</span>';
      }
      sub.innerHTML = esc(series.dimension || 'series') + ' · ' +
        esc(series.value || '-') + ' · 总计 ' + money(total) + fcText;
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
    if (!pods || !pods.length) {
      tbody.innerHTML = '<tr><td colspan="10"><div class="empty-state"><div class="icon">∅</div><div>暂无 Pod 成本明细</div><div style="font-size:12px;color:var(--dim);margin-top:4px">等待 OpenCost 数据采集或调整筛选条件</div></div></td></tr>';
      setText('pod-count', '');
      return;
    }
    var sorted = pods.slice().sort(function (a, b) { return Number(b.total_cost || 0) - Number(a.total_cost || 0); });
    var max = Math.max.apply(null, sorted.map(function (p) { return Number(p.total_cost || 0); }).concat([0.0001]));

    setText('pod-count', '(共 ' + pods.length + ' 个 · 显示前 50)');

    tbody.innerHTML = sorted.slice(0, 50).map(function (pod, index) {
      var v = Number(pod.total_cost || 0);
      var barW = (v / max) * 100;
      var tier = v / max > 0.6 ? 'row--accent' : v / max > 0.3 ? 'row--warning' : '';
      var envClass = (pod.environment || 'unknown').toLowerCase();
      var idx = sorted.indexOf(pod);
      return [
        '<tr class="' + tier + '">',
        '  <td class="col-pod" title="' + esc(pod.pod || '?') + '">' + esc(pod.pod || '?') + '</td>',
        '  <td>' + esc(pod.namespace || 'default') + '</td>',
        '  <td><strong>' + esc(pod.service || '-') + '</strong></td>',
        '  <td><span class="pill ' + esc(envClass || 'unknown') + '">' + esc(pod.environment || '-') + '</span></td>',
        '  <td>' + esc(pod.team || '-') + '</td>',
        '  <td class="num">' + money(pod.cpu_cost) + '</td>',
        '  <td class="num">' + money(pod.ram_cost) + '</td>',
        '  <td class="num">' + money(pod.network_cost) + '</td>',
        '  <td class="num col-total"><span class="col-total-bar"><i style="width:' + barW.toFixed(1) + '%"></i></span>' + money(pod.total_cost) + '</td>',
        '  <td><div class="row-actions">',
        '    <button class="icon-btn" title="创建任务" onclick="createOptimizationTask(\'pod\',' + idx + ')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg></button>',
        '    <button class="icon-btn" title="创建 Plaza 话题" onclick="createPlazaTopic(\'pod\',' + idx + ')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></button>',
        '    <button class="icon-btn icon-btn--accent" title="生成标签补丁" onclick="generateLabelPatch(\'pod\',' + idx + ')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41 13.42 20.58a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg></button>',
        '  </div></td>',
        '</tr>',
      ].join('');
    }).join('');
  }

  /* ─────────────── Governance panel ─────────────── */
  function renderGovernance() {
    var panel = $('governance-panel');
    if (!panel) return;
    var health = state.health || {};
    var gate = state.gateHealth || {};
    var stats = state.gateStats || {};
    var top = state.breakdown[0] || null;
    var topLabel = top ? (top.dimension || state.filters.aggregation || 'cost') + ': ' + (top.value || '-') : '暂无异常目标';
    var topCost = top ? money(top.total_cost) : '-';

    var gateStatus = gate.status || gate.decision || '未知';
    var gateStatusClass = gateStatus === 'ok' || gateStatus === 'allow' || gateStatus === 'pass' ? 'ok' : (gateStatus === 'block' || gateStatus === 'blocked' ? 'alert' : 'warn');
    var dataAge = Number(health.data_age_seconds || health.data_freshness_seconds || 0);
    var dataAgeClass = dataAge <= 120 ? 'ok' : dataAge <= 600 ? 'warn' : 'alert';
    var blocked = Number(stats.blocked || stats.block || 0);
    var passed = Number(stats.passed || stats.pass || 0);
    var warned = Number(stats.warned || stats.warn || 0);
    var total = blocked + passed + warned || 1;
    var blockRate = ((blocked / total) * 100);

    panel.innerHTML = [
      '<div class="governance-status">',
      '  <div class="gov-stat">',
      '    <div class="gov-stat__label"><span class="status-dot ' + (health.status === 'ok' ? 'healthy' : 'unhealthy') + ' pulse"></span>OpenCost</div>',
      '    <div class="gov-stat__value ' + (health.status === 'ok' ? 'gov-stat__value--ok' : 'gov-stat__value--alert') + '">' + esc(health.status || 'unknown') + '</div>',
      '  </div>',
      '  <div class="gov-stat">',
      '    <div class="gov-stat__label">数据新鲜度</div>',
      '    <div class="gov-stat__value gov-stat__value--' + dataAgeClass + '">' + dataAge + 's</div>',
      '  </div>',
      '  <div class="gov-stat">',
      '    <div class="gov-stat__label">Cost Gate</div>',
      '    <div class="gov-stat__value gov-stat__value--' + gateStatusClass + '">' + esc(gateStatus) + '</div>',
      '  </div>',
      '  <div class="gov-stat">',
      '    <div class="gov-stat__label">拦截率</div>',
      '    <div class="gov-stat__value ' + (blockRate > 20 ? 'gov-stat__value--alert' : blockRate > 5 ? 'gov-stat__value--warn' : 'gov-stat__value--ok') + '">' + blockRate.toFixed(1) + '%</div>',
      '  </div>',
      '</div>',

      '<div class="governance-row"><span>Gate 统计</span><strong>通 ' + compactNumber(passed) + ' · 警 ' + compactNumber(warned) + ' · 阻断 ' + compactNumber(blocked) + '</strong></div>',

      '<div class="action-box">',
      '  <div class="action-box__title">⚡ 当前治理目标</div>',
      '  <div class="action-box__target">' + esc(topLabel) + '<span class="action-box__target-cost">' + esc(topCost) + '</span></div>',
      '  <label>指派团队<select id="cost-action-team">' + teamOptionsHtml() + '</select></label>',
      '  <div class="action-buttons">',
      '    <button class="btn cost-btn cost-btn--accent cost-btn--sm" onclick="createOptimizationTask(\'breakdown\',0)">创建优化任务</button>',
      '    <button class="btn cost-btn cost-btn--ghost cost-btn--sm" onclick="createPlazaTopic(\'breakdown\',0)">创建 Plaza 话题</button>',
      '    <button class="btn cost-btn cost-btn--ghost cost-btn--sm" onclick="generateLabelPatch(\'pod\',0)">标签补丁</button>',
      '    <button class="btn cost-btn cost-btn--ghost cost-btn--sm" onclick="runCostGateSelfCheck()">Gate 自检</button>',
      '  </div>',
      '  <div class="action-result" id="cost-action-result"></div>',
      '</div>',
    ].join('');
  }

  function renderEfficiencyView(payload) {
    var host = $('efficiency-panel');
    if (!host) return;
    var teams = asItems(payload, 'teams').slice().sort(function (a, b) {
      return Number(b.token_efficiency || 0) - Number(a.token_efficiency || 0);
    });
    if (!teams.length) {
      host.innerHTML = '<div class="empty-state"><div class="icon">∅</div><div>暂无可持续性评估数据</div></div>';
      return;
    }
    var rows = teams.map(function (team, index) {
      var grade = team.grade || '-';
      return [
        '<div class="efficiency-row">',
        '  <div class="efficiency-rank">#' + String(index + 1).padStart(2, '0') + '</div>',
        '  <div class="efficiency-team"><b>' + esc(team.team_id || '-') + '</b><span>' + esc(team.data_quality || '-') + ' · ' + compactNumber(team.tokens_consumed || 0) + ' tokens</span></div>',
        '  <div class="efficiency-score">' + Number(team.token_efficiency || 0).toFixed(4) + '</div>',
        '  <div class="efficiency-grade efficiency-grade--' + esc(grade) + '">' + esc(grade) + '</div>',
        '</div>',
      ].join('');
    }).join('');
    var reallocations = asItems(payload, 'reallocations');
    var recs = teams.filter(function (t) { return t.grade === 'C' || t.grade === 'D'; }).slice(0, 3);
    host.innerHTML = [
      '<div class="efficiency-grid">',
      '  <div class="efficiency-list">' + rows + '</div>',
      '  <aside class="efficiency-side">',
      '    <h4>资源再分配</h4>',
      reallocations.length
        ? reallocations.slice(0, 3).map(function (r) {
            return '<p><b>' + esc(r.from_team) + '</b> → <b>' + esc(r.to_team) + '</b> · ' + compactNumber(r.tokens) + ' tokens</p>';
          }).join('')
        : '<p>暂无再分配建议</p>',
      '    <h4 style="margin-top:14px">待整改团队</h4>',
      recs.length
        ? recs.map(function (t) {
            var first = (t.recommendations || [])[0] || {};
            return '<p><b>' + esc(t.team_id) + '</b> · ' + esc(t.grade) + ' · ' + esc(first.detail || '等待建议') + '</p>';
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
    };
    var summaryQuery = queryString(Object.assign({ aggregation: state.filters.aggregation }, common));
    var breakdownQuery = queryString(common);
    var trendQuery = queryString({ aggregation: state.filters.aggregation, window: state.filters.window });
    var podQuery = queryString(Object.assign({}, common, { limit: 100 }));

    try {
      var responses = await Promise.all([
        requestJson(COST_API + '/health'),
        requestJson(GATE_API + '/health'),
        requestJson(GATE_API + '/stats'),
        requestJson(COST_API + '/summary?' + summaryQuery),
        requestJson(COST_API + '/by-' + state.filters.aggregation + '?' + breakdownQuery),
        requestJson(COST_API + '/trends?' + trendQuery),
        requestJson(COST_API + '/pods?' + podQuery),
        requestJson(SUSTAINABILITY_API + '/group'),
        state.teams.length ? Promise.resolve(null) : loadTeams(),
      ]);

      state.health = responses[0];
      state.gateHealth = responses[1];
      state.gateStats = responses[2];
      state.summary = responses[3];
      state.breakdown = asItems(responses[4], 'items');
      state.trends = normalizeTrends(responses[5]);
      state.pods = normalizePods(responses[6]);
      state.sustainability = responses[7];

      if (!state.summary && !state.breakdown.length && !state.trends.length && !state.pods.length) {
        showAlert('成本接口暂时没有返回可用数据，请检查 OpenCost、登录状态或后端日志');
        toast('暂无成本数据', { kind: 'warn', title: '数据缺失' });
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

  function resetFilters() {
    if ($('filter-aggregation')) $('filter-aggregation').value = 'team';
    if ($('filter-window')) $('filter-window').value = '24h';
    if ($('filter-environment')) $('filter-environment').value = '';
    if ($('filter-service')) $('filter-service').value = '';
    refreshDashboard();
  }

  function targetFromSource(source, index) {
    if (source === 'pod') {
      // Index refers to sorted order in renderPodsTable, so re-derive by total_cost
      var sorted = state.pods.slice().sort(function (a, b) { return Number(b.total_cost || 0) - Number(a.total_cost || 0); });
      return sorted[index || 0] || null;
    }
    return state.breakdown[index || 0] || null;
  }

  function targetLabel(target) {
    if (!target) return '成本异常';
    if (target.pod) return 'Pod ' + target.pod;
    return (target.dimension || state.filters.aggregation || 'cost') + ' ' + (target.value || '');
  }

  async function createOptimizationTask(source, index) {
    var result = $('cost-action-result');
    var teamSelect = $('cost-action-team');
    var teamId = teamSelect ? teamSelect.value : '';
    if (!teamId) {
      if (result) result.textContent = '没有可用团队，无法创建任务';
      toast('请先选择团队', { kind: 'warn' });
      return null;
    }
    var target = targetFromSource(source, index);
    if (!target) {
      if (result) result.textContent = '没有可用成本目标';
      toast('没有可用成本目标', { kind: 'warn' });
      return null;
    }
    if (result) result.textContent = '正在创建优化任务...';

    var title = '成本优化: ' + targetLabel(target);
    var description = [
      '来源: cost-dashboard',
      '治理目标: ' + targetLabel(target),
      '当前成本: ' + money(target.total_cost),
      '筛选窗口: ' + (state.filters.window || '24h'),
      '',
      '请分析资源利用率、标签归因、预算影响和可回滚优化方案。完成后回写成本变化、验证证据和后续演进建议。',
    ].join('\n');
    var payload = {
      title: title,
      description: description,
      priority: 1,
      metadata: {
        source: 'cost-dashboard',
        evidence_type: 'cost_anomaly',
        cost_filters: state.filters,
        cost_target: target,
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
        if (result) result.textContent = '已创建任务 ' + created.task_id;
        toast('任务 ' + created.task_id + ' 已创建', { kind: 'success', title: '已派发' });
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
    var result = $('cost-action-result');
    var target = targetFromSource(source, index);
    if (!target) {
      if (result) result.textContent = '没有可用成本目标，无法创建 Plaza 话题';
      toast('没有可用成本目标', { kind: 'warn' });
      return null;
    }
    if (result) result.textContent = '正在创建 Plaza 话题...';

    var plaza = await ensureCostPlaza();
    if (!plaza || !plaza.id) {
      if (result) result.textContent = '没有可用 Plaza，创建话题失败';
      toast('Plaza 不可用', { kind: 'error' });
      return null;
    }

    var topic = '成本治理: ' + targetLabel(target);
    var description = [
      '来源: cost-dashboard',
      '治理目标: ' + targetLabel(target),
      '当前成本: ' + money(target.total_cost),
      '筛选窗口: ' + (state.filters.window || '24h'),
      '筛选环境: ' + (state.filters.environment || '全部'),
      '筛选服务: ' + (state.filters.service || '全部'),
      '',
      '请从成本归因、资源规格、标签修复、预算风险、可回滚优化方案和是否需要生成 EvolutionItem 六个角度讨论。',
      '',
      '原始目标:',
      JSON.stringify(target, null, 2),
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
        }),
      });
      if (discussion && discussion.id) {
        if (result) {
          result.innerHTML = '已创建 Plaza 话题 <a href="/plaza.html" style="color:var(--koke)">打开议事厅</a> · ' + esc(discussion.id);
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
    if (result) result.textContent = '正在运行 Cost Gate 自检...';
    var plan = {
      resource_changes: [{
        address: 'aws_instance.cost_dashboard_sample',
        type: 'aws_instance',
        name: 'cost_dashboard_sample',
        provider_name: 'aws',
        change: { actions: ['create'] },
        values: { instance_type: 'p4d.24xlarge', count: 2, tags: {} },
      }],
    };
    try {
      var report = await requestJson(GATE_API + '/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: plan,
          project_id: 'cost-dashboard-self-check',
          metadata: { source: 'cost-dashboard', purpose: 'ui_self_check' },
        }),
      });
      if (report) {
        if (result) {
          result.innerHTML = 'Gate 决策: <strong>' + esc(report.decision || '-') + '</strong> · 违规 ' + compactNumber((report.violations || []).length || report.violations_count || 0);
        }
        state.gateStats = await requestJson(GATE_API + '/stats');
        renderGovernance();
        toast('Gate 决策: ' + (report.decision || '-'), { kind: report.decision === 'block' ? 'warn' : 'success', title: '自检完成' });
        return report;
      }
      if (result) result.textContent = 'Cost Gate 自检失败，请查看后端日志或 request_id';
      toast('Cost Gate 自检失败', { kind: 'error' });
      return null;
    } catch (e) {
      if (result) result.textContent = 'Cost Gate 自检失败: ' + e.message;
      toast('Cost Gate 自检失败: ' + e.message, { kind: 'error' });
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
  }

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
  };

  if (!window.__AG_COST_DASHBOARD_NO_INIT__) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
  }
})();
