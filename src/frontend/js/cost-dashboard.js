/**
 * AgentsGroup2026 — Cost Governance Workbench
 * Repairs the OpenCost dashboard path and connects cost anomalies to task work.
 */
(function () {
  'use strict';

  var COST_API = '/api/v1/cost';
  var GATE_API = '/api/v1/cost-gate';
  var AGENT_API = '/api/v1/agent-config';
  var state = {
    teams: [],
    summary: null,
    breakdown: [],
    trends: [],
    pods: [],
    health: null,
    gateHealth: null,
    gateStats: null,
    filters: {},
  };

  function $(id) {
    return document.getElementById(id);
  }

  function esc(value) {
    if (window.AG && typeof window.AG.escapeHtml === 'function') {
      return window.AG.escapeHtml(value);
    }
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function money(value) {
    return '$' + Number(value || 0).toFixed(2);
  }

  function compactNumber(value) {
    return Number(value || 0).toLocaleString();
  }

  function setText(id, value) {
    var node = $(id);
    if (node) node.textContent = value;
  }

  function setHtml(id, value) {
    var node = $(id);
    if (node) node.innerHTML = value;
  }

  function showAlert(message) {
    var alert = $('dashboard-alert');
    if (!alert) return;
    if (!message) {
      alert.classList.remove('show');
      alert.textContent = '';
      return;
    }
    var requestId = window.api && typeof window.api.getLastRequestId === 'function'
      ? window.api.getLastRequestId()
      : '';
    alert.textContent = requestId ? message + ' · 请求ID: ' + requestId : message;
    alert.classList.add('show');
  }

  async function requestJson(url, opts) {
    if (window.api && typeof window.api.request === 'function') {
      return await window.api.request(url, opts);
    }
    var response = await fetch(url, opts || { credentials: 'same-origin' });
    if (!response.ok) return null;
    return await response.json();
  }

  function getFilters() {
    return {
      aggregation: ($('filter-aggregation') && $('filter-aggregation').value) || 'service',
      window: ($('filter-window') && $('filter-window').value) || '24h',
      environment: ($('filter-environment') && $('filter-environment').value) || '',
      service: (($('filter-service') && $('filter-service').value) || '').trim(),
    };
  }

  function queryString(params) {
    var query = new URLSearchParams();
    Object.keys(params || {}).forEach(function (key) {
      if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
        query.set(key, params[key]);
      }
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
      var points = Array.isArray(series.points)
        ? series.points
        : Array.isArray(series.data_points)
          ? series.data_points
          : [];
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

  function renderSummary(payload) {
    var grid = $('summary-grid');
    if (!grid) return;
    var summary = payload && payload.summary ? payload.summary : null;
    if (!summary) {
      grid.innerHTML = '<div class="empty-state"><div class="icon">--</div><div>暂无成本摘要</div><div style="font-size:12px;color:var(--dim);margin-top:4px">请检查 OpenCost 或后端接口状态</div></div>';
      return;
    }

    grid.innerHTML = [
      '<div class="summary-card accent">',
      '<div class="card-label">总成本</div>',
      '<div class="card-value">' + money(summary.total_cost) + '</div>',
      '<div class="card-sub">' + esc(state.filters.window || '24h') + ' 窗口</div>',
      '</div>',
      '<div class="summary-card">',
      '<div class="card-label">活跃 Pod</div>',
      '<div class="card-value">' + compactNumber(summary.pod_count || summary.total_pods || 0) + '</div>',
      '<div class="card-sub">容器 ' + compactNumber(summary.container_count || 0) + '</div>',
      '</div>',
      '<div class="summary-card">',
      '<div class="card-label">服务 / 环境</div>',
      '<div class="card-value">' + compactNumber(summary.service_count || (summary.by_service || []).length) + '</div>',
      '<div class="card-sub">环境 ' + compactNumber(summary.environment_count || (summary.by_environment || []).length) + '</div>',
      '</div>',
      '<div class="summary-card success">',
      '<div class="card-label">团队归因</div>',
      '<div class="card-value">' + compactNumber(summary.team_count || (summary.by_team || []).length) + '</div>',
      '<div class="card-sub">最大团队成本 ' + money(maxCost(summary.by_team)) + '</div>',
      '</div>',
    ].join('');
  }

  function maxCost(items) {
    items = Array.isArray(items) ? items : [];
    return items.reduce(function (max, item) {
      return Math.max(max, Number(item.total_cost || 0));
    }, 0);
  }

  function renderBreakdown(items) {
    var container = $('breakdown-chart');
    if (!container) return;
    if (!items || !items.length) {
      container.innerHTML = '<div class="empty-state"><div class="icon">--</div><div>该维度下暂无数据</div></div>';
      return;
    }

    var sorted = items.slice().sort(function (a, b) {
      return Number(b.total_cost || 0) - Number(a.total_cost || 0);
    }).slice(0, 10);
    var max = Math.max.apply(null, sorted.map(function (item) { return Number(item.total_cost || 0); }).concat([0.01]));

    container.innerHTML = [
      '<div class="bar-chart">',
      sorted.map(function (item) {
        var height = Math.max((Number(item.total_cost || 0) / max) * 180, 4);
        return [
          '<div class="bar-item">',
          '<div class="bar-value">' + money(item.total_cost) + '</div>',
          '<div class="bar" style="height:' + height + 'px" title="' + esc(item.value || '?') + ': ' + money(item.total_cost) + '"></div>',
          '<div class="bar-label">' + esc(item.value || '?') + '</div>',
          '</div>',
        ].join('');
      }).join(''),
      '</div>',
    ].join('');
  }

  function renderTrends(seriesList) {
    var container = $('trends-chart');
    if (!container) return;
    var series = Array.isArray(seriesList) && seriesList.length ? seriesList[0] : null;
    if (!series || !series.points || series.points.length < 1) {
      container.innerHTML = '<div class="empty-state"><div class="icon">--</div><div>趋势数据不足</div><div style="font-size:12px;color:var(--dim)">需要 OpenCost 返回至少一个时间点</div></div>';
      return;
    }

    var values = series.points.map(function (point) { return Number(point.cost || 0); });
    var max = Math.max.apply(null, values.concat([0.01]));
    var min = Math.min.apply(null, values.concat([0]));
    container.innerHTML = [
      '<div style="display:flex;flex-direction:column;gap:12px">',
      '<div style="display:flex;align-items:flex-end;gap:4px;height:190px;padding:0 10px">',
      series.points.map(function (point) {
        var value = Number(point.cost || 0);
        var height = Math.max(((value - min) / (max - min || 1)) * 160, 4);
        var label = point.timestamp ? point.timestamp.slice(11, 16) || point.timestamp.slice(5, 10) : '?';
        return [
          '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px" title="' + esc(label) + ': ' + money(value) + '">',
          '<div style="font-size:9px;color:var(--dim)">' + money(value) + '</div>',
          '<div class="trend-bar" style="height:' + height + 'px"></div>',
          '<div style="font-size:8px;color:var(--dim);transform:rotate(-45deg);white-space:nowrap">' + esc(label) + '</div>',
          '</div>',
        ].join('');
      }).join(''),
      '</div>',
      '<div style="text-align:center;font-size:12px;color:var(--muted)">' + esc(series.dimension || 'series') + ': ' + esc(series.value || '-') + ' · 总计 ' + money(series.total) + '</div>',
      '</div>',
    ].join('');
  }

  function renderPodsTable(pods) {
    var tbody = $('pods-tbody');
    if (!tbody) return;
    if (!pods || !pods.length) {
      tbody.innerHTML = '<tr><td colspan="10"><div class="empty-state"><div class="icon">--</div><div>暂无 Pod 成本明细</div><div style="font-size:12px;color:var(--dim)">等待 OpenCost 数据采集或调整筛选条件</div></div></td></tr>';
      setText('pod-count', '');
      return;
    }

    setText('pod-count', '(共 ' + pods.length + ' 个 Pod，显示前 50 个)');
    tbody.innerHTML = pods.slice(0, 50).map(function (pod, index) {
      var envClass = (pod.environment || 'unknown').toLowerCase();
      return [
        '<tr>',
        '<td style="font-family:monospace;font-size:12px">' + esc(pod.pod || '?') + '</td>',
        '<td>' + esc(pod.namespace || 'default') + '</td>',
        '<td><strong>' + esc(pod.service || '-') + '</strong></td>',
        '<td><span class="pill ' + esc(envClass || 'unknown') + '">' + esc(pod.environment || '-') + '</span></td>',
        '<td>' + esc(pod.team || '-') + '</td>',
        '<td>' + money(pod.cpu_cost) + '</td>',
        '<td>' + money(pod.ram_cost) + '</td>',
        '<td>' + money(pod.network_cost) + '</td>',
        '<td class="cost-positive">' + money(pod.total_cost) + '</td>',
        '<td><div style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn btn-sm" onclick="createOptimizationTask(\'pod\',' + index + ')">创建任务</button><button class="btn btn-sm" onclick="generateLabelPatch(\'pod\',' + index + ')">标签补丁</button></div></td>',
        '</tr>',
      ].join('');
    }).join('');
  }

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
    var gateStatText = [
      '通过 ' + compactNumber(stats.passed || stats.pass || 0),
      '警告 ' + compactNumber(stats.warned || stats.warn || 0),
      '阻断 ' + compactNumber(stats.blocked || stats.block || 0),
    ].join(' · ');

    panel.innerHTML = [
      '<div class="governance-row"><span>OpenCost 数据</span><strong>' + esc(health.status || 'unknown') + '</strong></div>',
      '<div class="governance-row"><span>数据年龄</span><strong>' + compactNumber(health.data_age_seconds || health.data_freshness_seconds || 0) + ' 秒</strong></div>',
      '<div class="governance-row"><span>Cost Gate</span><strong>' + esc(gateStatus) + '</strong></div>',
      '<div class="governance-row"><span>Gate 统计</span><strong>' + esc(gateStatText) + '</strong></div>',
      '<div class="action-box">',
      '<div><strong>当前治理目标</strong><div style="font-size:12px;color:var(--muted);margin-top:4px">' + esc(topLabel) + ' · ' + esc(topCost) + '</div></div>',
      '<label>指派团队<select id="cost-action-team">' + teamOptionsHtml() + '</select></label>',
      '<div class="action-buttons">',
      '<button class="btn btn-pink btn-sm" onclick="createOptimizationTask(\'breakdown\',0)">创建优化任务</button>',
      '<button class="btn btn-sm" onclick="createPlazaTopic(\'breakdown\',0)">创建 Plaza 话题</button>',
      '<button class="btn btn-sm" onclick="generateLabelPatch(\'pod\',0)">生成标签补丁</button>',
      '<button class="btn btn-sm" onclick="runCostGateSelfCheck()">运行 Cost Gate 自检</button>',
      '</div>',
      '<div class="action-result" id="cost-action-result"></div>',
      '</div>',
    ].join('');
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
    dot.className = 'status-dot';
    if (summaryPayload && summaryPayload.summary) {
      dot.classList.add('healthy');
      text.textContent = '已连接';
      text.style.color = 'var(--lime)';
      var summary = summaryPayload.summary;
      cache.textContent = '服务 ' + compactNumber(summary.service_count || 0) + ' · Pod ' + compactNumber(summary.pod_count || 0);
    } else if (state.health && state.health.status) {
      dot.classList.add(state.health.status === 'ok' ? 'healthy' : 'unhealthy');
      text.textContent = state.health.status;
      text.style.color = state.health.status === 'ok' ? 'var(--lime)' : 'var(--pink)';
      cache.textContent = state.health.last_error ? state.health.last_error : '';
    } else {
      dot.classList.add('unknown');
      text.textContent = '无数据';
      text.style.color = 'var(--dim)';
      cache.textContent = '';
    }
  }

  function setLoading() {
    setHtml('summary-grid', '<div class="loading-state"><div class="spinner"></div><div>加载中...</div></div>');
    setHtml('breakdown-chart', '<div class="loading-state"><div class="spinner"></div></div>');
    setHtml('trends-chart', '<div class="loading-state"><div class="spinner"></div></div>');
    setHtml('governance-panel', '<div class="loading-state"><div class="spinner"></div></div>');
    var tbody = $('pods-tbody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="10" class="loading-state"><div class="spinner" style="margin:20px auto"></div></td></tr>';
  }

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

    var responses = await Promise.all([
      requestJson(COST_API + '/health'),
      requestJson(GATE_API + '/health'),
      requestJson(GATE_API + '/stats'),
      requestJson(COST_API + '/summary?' + summaryQuery),
      requestJson(COST_API + '/by-' + state.filters.aggregation + '?' + breakdownQuery),
      requestJson(COST_API + '/trends?' + trendQuery),
      requestJson(COST_API + '/pods?' + podQuery),
      state.teams.length ? Promise.resolve(null) : loadTeams(),
    ]);

    state.health = responses[0];
    state.gateHealth = responses[1];
    state.gateStats = responses[2];
    state.summary = responses[3];
    state.breakdown = asItems(responses[4], 'items');
    state.trends = normalizeTrends(responses[5]);
    state.pods = normalizePods(responses[6]);

    if (!state.summary && !state.breakdown.length && !state.trends.length && !state.pods.length) {
      showAlert('成本接口暂时没有返回可用数据，请检查 OpenCost、登录状态或后端日志');
    }

    updateStatus(state.summary);
    renderSummary(state.summary);
    renderBreakdown(state.breakdown);
    renderTrends(state.trends);
    renderPodsTable(state.pods);
    renderGovernance();
    setText('last-refresh', '最后更新: ' + new Date().toLocaleTimeString('zh-CN'));

    if (refreshBtn) refreshBtn.disabled = false;
  }

  function resetFilters() {
    if ($('filter-aggregation')) $('filter-aggregation').value = 'service';
    if ($('filter-window')) $('filter-window').value = '24h';
    if ($('filter-environment')) $('filter-environment').value = '';
    if ($('filter-service')) $('filter-service').value = '';
    refreshDashboard();
  }

  function targetFromSource(source, index) {
    if (source === 'pod') {
      return state.pods[index || 0] || null;
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
      return null;
    }
    var target = targetFromSource(source, index);
    if (!target) {
      if (result) result.textContent = '没有可用成本目标';
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

    var created = await requestJson(AGENT_API + '/teams/' + encodeURIComponent(teamId) + '/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (created && created.task_id) {
      if (result) result.textContent = '已创建任务 ' + created.task_id;
      return created;
    }
    if (result) result.textContent = '创建任务失败，请查看后端日志或 request_id';
    return null;
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
      return null;
    }
    if (result) result.textContent = '正在创建 Plaza 话题...';

    var plaza = await ensureCostPlaza();
    if (!plaza || !plaza.id) {
      if (result) result.textContent = '没有可用 Plaza，创建话题失败';
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
        result.innerHTML = '已创建 Plaza 话题 <a href="/plaza.html" style="color:var(--pink)">打开议事厅</a> · ' + esc(discussion.id);
      }
      return { plaza: plaza, discussion: discussion };
    }
    if (result) result.textContent = '创建 Plaza 话题失败，请查看后端日志或 request_id';
    return null;
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
        values: {
          instance_type: 'p4d.24xlarge',
          count: 2,
          tags: {},
        },
      }],
    };
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
      return report;
    }
    if (result) result.textContent = 'Cost Gate 自检失败，请查看后端日志或 request_id';
    return null;
  }

  async function generateLabelPatch(source, index) {
    var result = $('cost-action-result');
    var target = targetFromSource(source, index);
    if (!target || !target.pod) {
      if (result) result.textContent = '请选择一条 Pod 成本明细后再生成标签补丁';
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
    var patch = await requestJson(COST_API + '/labels/generate?' + params, { method: 'POST' });
    if (patch) {
      if (result) {
        result.innerHTML = '已生成标签补丁: <code style="word-break:break-all">' + esc(JSON.stringify(patch.patch || patch)) + '</code>';
      }
      return patch;
    }
    if (result) result.textContent = '标签补丁生成失败，请查看后端日志或 request_id';
    return null;
  }

  function init() {
    window.refreshDashboard = refreshDashboard;
    window.resetFilters = resetFilters;
    window.createOptimizationTask = createOptimizationTask;
    window.createPlazaTopic = createPlazaTopic;
    window.runCostGateSelfCheck = runCostGateSelfCheck;
    window.generateLabelPatch = generateLabelPatch;
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
    renderSummary: renderSummary,
    renderBreakdown: renderBreakdown,
    renderGovernance: renderGovernance,
    refreshDashboard: refreshDashboard,
    resetFilters: resetFilters,
    createOptimizationTask: createOptimizationTask,
    createPlazaTopic: createPlazaTopic,
    runCostGateSelfCheck: runCostGateSelfCheck,
    generateLabelPatch: generateLabelPatch,
  };

  if (!window.__AG_COST_DASHBOARD_NO_INIT__) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }
})();
