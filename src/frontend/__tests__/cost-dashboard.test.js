import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { describe, expect, it, vi } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

function makeElement(initial = {}) {
  return {
    innerHTML: '',
    textContent: '',
    value: '',
    disabled: false,
    style: {},
    className: '',
    classList: {
      values: new Set(),
      add(name) { this.values.add(name); },
      remove(name) { this.values.delete(name); },
      contains(name) { return this.values.has(name); },
    },
    addEventListener() {},
    setAttribute() {},
    removeAttribute() {},
    ...initial,
  };
}

function buildContext(requestImpl) {
  const elements = Object.create(null);
  const defaults = {
    'filter-aggregation': { value: 'service' },
    'filter-window': { value: '24h' },
    'filter-environment': { value: '' },
    'filter-service': { value: '' },
    'cost-action-team': { value: 'cloud_ops' },
  };
  const document = {
    hidden: false,
    readyState: 'complete',
    getElementById(id) {
      if (!elements[id]) elements[id] = makeElement(defaults[id] || {});
      return elements[id];
    },
    createElement() {
      return makeElement();
    },
    addEventListener() {},
  };

  const window = {
    __AG_COST_DASHBOARD_NO_INIT__: true,
    AG: {
      escapeHtml(value) {
        return String(value ?? '')
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;');
      },
    },
    api: {
      request: requestImpl,
      getLastRequestId: () => 'req-cost-1',
    },
  };

  const context = vm.createContext({
    window,
    document,
    URLSearchParams,
    encodeURIComponent,
    setInterval: vi.fn(),
    fetch: vi.fn(),
    console,
  });
  vm.runInContext(read('src/frontend/js/cost-dashboard.js'), context);
  return { context, elements };
}

function sampleSummary() {
  return {
    summary: {
      total_cost: 42.5,
      pod_count: 2,
      container_count: 2,
      service_count: 1,
      environment_count: 1,
      team_count: 1,
      by_team: [{ value: 'cloud', total_cost: 42.5 }],
    },
  };
}

describe('cost governance dashboard', () => {
  it('normalizes backend trend lists and renders total_cost points', () => {
    const { context, elements } = buildContext(vi.fn());
    const trends = context.window.CostDashboard.normalizeTrends([{
      dimension: 'service',
      value: 'checkout',
      total: 22.5,
      points: [
        { timestamp: '2026-06-05T08:00:00Z', total_cost: 10 },
        { timestamp: '2026-06-05T09:00:00Z', total_cost: 12.5 },
      ],
    }]);

    context.window.CostDashboard.renderTrends(trends);

    expect(elements['trends-chart'].innerHTML).toContain('$10.00');
    expect(elements['trends-chart'].innerHTML).toContain('$12.50');
    expect(elements['trends-chart'].innerHTML).toContain('checkout');
  });

  it('normalizes pod labels from /cost/pods and renders the pod table', () => {
    const { context, elements } = buildContext(vi.fn());
    const pods = context.window.CostDashboard.normalizePods([{
      pod: 'checkout-7d9',
      namespace: 'prod',
      cpu_cost: 3,
      ram_cost: 2,
      network_cost: 1,
      total_cost: 6,
      labels: { service: 'checkout', environment: 'production', team: 'cloud-ops' },
    }]);

    context.window.CostDashboard.renderPodsTable(pods);

    expect(elements['pods-tbody'].innerHTML).toContain('checkout-7d9');
    expect(elements['pods-tbody'].innerHTML).toContain('checkout');
    expect(elements['pods-tbody'].innerHTML).toContain('cloud-ops');
    expect(elements['pods-tbody'].innerHTML).toContain('创建任务');
    expect(elements['pods-tbody'].innerHTML).toContain('标签补丁');
  });

  it('refreshes summary, trends, pods, teams, and governance state through the shared API client', async () => {
    const request = vi.fn(async (url) => {
      if (url === '/api/v1/cost/health') return { status: 'ok', data_age_seconds: 12 };
      if (url === '/api/v1/cost-gate/health') return { status: 'healthy' };
      if (url === '/api/v1/cost-gate/stats') return { passed: 1, warned: 2, blocked: 3 };
      if (url.startsWith('/api/v1/cost/summary?')) return sampleSummary();
      if (url.startsWith('/api/v1/cost/by-service?')) return [{ dimension: 'service', value: 'checkout', total_cost: 42.5 }];
      if (url.startsWith('/api/v1/cost/trends?')) {
        return [{
          dimension: 'service',
          value: 'checkout',
          total: 42.5,
          points: [{ timestamp: '2026-06-05T08:00:00Z', total_cost: 42.5 }],
        }];
      }
      if (url.startsWith('/api/v1/cost/pods?')) {
        return [{
          pod: 'checkout-7d9',
          namespace: 'prod',
          total_cost: 42.5,
          labels: { service: 'checkout', environment: 'production', team: 'cloud-ops' },
        }];
      }
      if (url === '/api/v1/sustainability/group') {
        return { teams: [{ team_id: 'cloud_ops', token_efficiency: 0.42, grade: 'B', tokens_consumed: 5000, data_quality: 'measured', recommendations: [] }], reallocations: [] };
      }
      if (url === '/api/v1/agent-config/teams?limit=200&offset=0') {
        return { items: [{ team_id: 'cloud_ops', name: '公有云运维团队' }] };
      }
      return null;
    });
    const { context, elements } = buildContext(request);

    await context.window.CostDashboard.refreshDashboard();

    expect(request.mock.calls.some(([url]) => url.startsWith('/api/v1/cost/pods?'))).toBe(true);
    expect(elements['summary-grid'].innerHTML).toContain('$42.50');
    expect(elements['trends-chart'].innerHTML).toContain('$42.50');
    expect(elements['pods-tbody'].innerHTML).toContain('checkout-7d9');
    expect(elements['efficiency-panel'].innerHTML).toContain('cloud_ops');
    expect(elements['efficiency-panel'].innerHTML).toContain('0.4200');
    expect(elements['governance-panel'].innerHTML).toContain('创建优化任务');
    expect(elements['governance-panel'].innerHTML).toContain('创建 Plaza 话题');
  });

  it('renders the token efficiency perspective from sustainability results', () => {
    const { context, elements } = buildContext(vi.fn());

    context.window.CostDashboard.renderEfficiencyView({
      teams: [
        { team_id: 'alpha', token_efficiency: 0.8, grade: 'A', tokens_consumed: 1000, data_quality: 'measured', recommendations: [] },
        { team_id: 'omega', token_efficiency: 0.02, grade: 'D', tokens_consumed: 90000, data_quality: 'estimated', recommendations: [{ detail: '降低演练频率' }] },
      ],
      reallocations: [{ from_team: 'omega', to_team: 'alpha', tokens: 18000 }],
    });

    expect(elements['efficiency-panel'].innerHTML).toContain('alpha');
    expect(elements['efficiency-panel'].innerHTML).toContain('omega');
    expect(elements['efficiency-panel'].innerHTML).toContain('18,000');
    expect(elements['efficiency-panel'].innerHTML).toContain('降低演练频率');
  });

  it('creates a real agent task from a cost anomaly target', async () => {
    const request = vi.fn(async (url, opts) => {
      if (url === '/api/v1/agent-config/teams/cloud_ops/tasks') {
        expect(opts.method).toBe('POST');
        const body = JSON.parse(opts.body);
        expect(body.title).toContain('成本优化');
        expect(body.metadata.source).toBe('cost-dashboard');
        expect(body.metadata.cost_target.value).toBe('checkout');
        return { task_id: 'task-cost-1' };
      }
      return null;
    });
    const { context, elements } = buildContext(request);
    context.window.CostDashboard.state.breakdown = [{ dimension: 'service', value: 'checkout', total_cost: 42.5 }];

    const created = await context.window.CostDashboard.createOptimizationTask('breakdown', 0);

    expect(created.task_id).toBe('task-cost-1');
    expect(elements['cost-action-result'].textContent).toContain('task-cost-1');
  });

  it('generates a label injection patch for a selected pod', async () => {
    const request = vi.fn(async (url, opts) => {
      if (url.startsWith('/api/v1/cost/labels/generate?')) {
        expect(opts.method).toBe('POST');
        expect(url).toContain('pod_name=checkout-7d9');
        expect(url).toContain('service=checkout');
        return { patch: [{ op: 'add', path: '/metadata/labels/service', value: 'checkout' }] };
      }
      return null;
    });
    const { context, elements } = buildContext(request);
    context.window.CostDashboard.state.pods = [{
      pod: 'checkout-7d9',
      namespace: 'prod',
      service: 'checkout',
      environment: 'production',
      team: 'cloud-ops',
      total_cost: 42.5,
      labels: {},
    }];

    const patch = await context.window.CostDashboard.generateLabelPatch('pod', 0);

    expect(patch.patch[0].value).toBe('checkout');
    expect(elements['cost-action-result'].innerHTML).toContain('service');
  });

  it('creates a Plaza discussion from the selected cost target', async () => {
    const request = vi.fn(async (url, opts) => {
      if (url === '/api/v1/agent-config/plaza?limit=50&offset=0') {
        return { items: [{ id: 'plaza-cost', name: '成本治理议事厅' }] };
      }
      if (url === '/api/v1/agent-config/plaza/plaza-cost/discussions') {
        expect(opts.method).toBe('POST');
        const body = JSON.parse(opts.body);
        expect(body.topic).toContain('成本治理');
        expect(body.description).toContain('cost-dashboard');
        expect(body.goal).toContain('成本优化任务');
        return { id: 'disc-cost-1', topic: body.topic };
      }
      return null;
    });
    const { context, elements } = buildContext(request);
    context.window.CostDashboard.state.breakdown = [{ dimension: 'service', value: 'checkout', total_cost: 42.5 }];

    const created = await context.window.CostDashboard.createPlazaTopic('breakdown', 0);

    expect(created.discussion.id).toBe('disc-cost-1');
    expect(elements['cost-action-result'].innerHTML).toContain('打开议事厅');
  });

  it('shows an actionable request_id error state when cost data is unavailable', async () => {
    const request = vi.fn(async () => null);
    const { context, elements } = buildContext(request);

    await context.window.CostDashboard.refreshDashboard();

    expect(elements['dashboard-alert'].textContent).toContain('成本接口暂时没有返回可用数据');
    expect(elements['dashboard-alert'].textContent).toContain('请求ID: req-cost-1');
    expect(elements['dashboard-alert'].classList.contains('show')).toBe(true);
    expect(elements['summary-grid'].innerHTML).toContain('暂无成本摘要');
    expect(elements['pods-tbody'].innerHTML).toContain('暂无 Pod 成本明细');
  });

  it('runs a Cost Gate self-check and refreshes gate stats', async () => {
    const request = vi.fn(async (url, opts) => {
      if (url === '/api/v1/cost-gate/evaluate') {
        expect(opts.method).toBe('POST');
        const body = JSON.parse(opts.body);
        expect(body.project_id).toBe('cost-dashboard-self-check');
        expect(body.metadata.source).toBe('cost-dashboard');
        return { decision: 'blocked', violations: [{ id: 'gpu-budget' }] };
      }
      if (url === '/api/v1/cost-gate/stats') {
        return { passed: 1, warned: 0, blocked: 1 };
      }
      return null;
    });
    const { context, elements } = buildContext(request);

    const report = await context.window.CostDashboard.runCostGateSelfCheck();

    expect(report.decision).toBe('blocked');
    expect(elements['cost-action-result'].innerHTML).toContain('Gate 决策');
    expect(elements['cost-action-result'].innerHTML).toContain('blocked');
    expect(elements['governance-panel'].innerHTML).toContain('Gate 统计');
    expect(elements['governance-panel'].innerHTML).toContain('阻断 1');
  });
});
