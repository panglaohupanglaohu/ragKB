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
    querySelector() { return null; },
    createElement() {
      return makeElement();
    },
    addEventListener() {},
  };

  const window = {
    __AG_COST_DASHBOARD_NO_INIT__: true,
    location: { search: '', pathname: '/cost-dashboard.html' },
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
    setTimeout: vi.fn(),
    fetch: vi.fn(() => Promise.resolve({ ok: false, json: async () => null })),
    console,
  });
  vm.runInContext(read('src/frontend/js/cost-dashboard.js'), context);
  return { context, elements };
}

// Token 北极星口径样本
function tokenTeams() {
  return {
    teams: [
      { team_id: 'alpha', token_efficiency: 0.8, grade: 'A', tokens_consumed: 1000, trial_count: 4, total_score: 2, data_quality: 'measured', recommendations: [] },
      { team_id: 'omega', token_efficiency: 0.02, grade: 'D', tokens_consumed: 90000, trial_count: 1, total_score: 1, data_quality: 'estimated', recommendations: [{ detail: '降低演练频率' }] },
    ],
    reallocations: [{ from_team: 'omega', to_team: 'alpha', tokens: 18000 }],
  };
}

describe('cost governance dashboard (token 口径)', () => {
  it('renders a token trend series using point.total (not dollar cost)', () => {
    const { context, elements } = buildContext(vi.fn());

    context.window.CostDashboard.renderTrends({
      dimension: 'team',
      value: 'cloud_ops',
      total: 22500,
      points: [
        { timestamp: '2026-06-05T08:00:00Z', total: 10000 },
        { timestamp: '2026-06-05T09:00:00Z', total: 12500 },
      ],
    });

    // 副标题按 token 汇总，不再是美元
    expect(elements['trends-sub'].innerHTML).toContain('cloud_ops');
    expect(elements['trends-sub'].innerHTML).toContain('22,500');
    expect(elements['trends-sub'].innerHTML).toContain('tokens');
    expect(elements['trends-sub'].innerHTML).not.toContain('$');
    // 图表区渲染 svg 折线
    expect(elements['trends-chart'].innerHTML).toContain('line-chart');
  });

  it('renders token detail rows with run_id/phase/team_id/skill_id/calls/total', () => {
    const { context, elements } = buildContext(vi.fn());

    context.window.CostDashboard.renderPodsTable([
      { run_id: 'run-abcdef1234567890', phase: 'evaluating', team_id: 'cloud_ops', skill_id: 'cost-opt', calls: 3, total: 6000 },
    ]);

    const html = elements['pods-tbody'].innerHTML;
    expect(html).toContain('run-abcdef123456');   // run_id 前 16 字符
    expect(html).toContain('evaluating');          // phase
    expect(html).toContain('cloud_ops');           // team_id
    expect(html).toContain('cost-opt');            // skill_id
    expect(html).toContain('>3<');                 // calls
    expect(html).toContain('6,000 tokens');        // total
  });

  it('refreshes summary, trends, token detail, and efficiency through the token endpoints', async () => {
    const request = vi.fn(async (url) => {
      if (url === '/api/v1/cost/health') return { status: 'ok', data_age_seconds: 12 };
      if (url === '/api/v1/cost-gate/health') return { status: 'healthy' };
      if (url === '/api/v1/cost-gate/stats') return { passed: 1, warned: 2, blocked: 3 };
      if (url.startsWith('/api/v1/cost/summary?')) return { summary: { by_team: [], by_service: [], service_count: 1, pod_count: 0 } };
      if (url.startsWith('/api/v1/cost/tokens/breakdown?')) return [{ key: 'cloud_ops', total: 5000, calls: 10 }];
      if (url.startsWith('/api/v1/cost/tokens/trend?')) {
        return { dimension: 'team', value: 'cloud_ops', total: 5000, points: [{ timestamp: '2026-06-05T08:00:00Z', total: 5000 }] };
      }
      if (url.startsWith('/api/v1/cost/tokens/detail?')) {
        return [{ run_id: 'run-cloud-0001', phase: 'task', team_id: 'cloud_ops', skill_id: 'cost-opt', calls: 4, total: 5000 }];
      }
      if (url.startsWith('/api/v1/cost/tokens/overview?')) {
        return { summary: { total: 5000, calls: 10 }, by_team: [{ team_id: 'cloud_ops', total: 5000, calls: 10 }], by_phase: { task: { total: 5000 } } };
      }
      if (url === '/api/v1/cost/tokens/ratchet') return null;
      if (url === '/api/v1/sustainability/group') return tokenTeams();
      if (url === '/api/v1/agent-config/teams?limit=200&offset=0') return { items: [{ team_id: 'cloud_ops', name: '公有云运维团队' }] };
      return null;
    });
    const { context, elements } = buildContext(request);

    await context.window.CostDashboard.refreshDashboard();

    // 明细主源切到 token detail / overview
    expect(request.mock.calls.some(([url]) => url.startsWith('/api/v1/cost/tokens/detail?'))).toBe(true);
    expect(request.mock.calls.some(([url]) => url.startsWith('/api/v1/cost/tokens/overview?'))).toBe(true);
    expect(elements['pods-tbody'].innerHTML).toContain('run-cloud-0001');
    expect(elements['pods-tbody'].innerHTML).toContain('tokens');
    expect(elements['efficiency-panel'].innerHTML).toContain('omega');
    expect(elements['summary-grid'].innerHTML).toContain('5,000'); // 窗口总 Token
  });

  it('renders the token efficiency perspective from sustainability results', () => {
    const { context, elements } = buildContext(vi.fn());

    context.window.CostDashboard.renderEfficiencyView(tokenTeams());

    expect(elements['efficiency-panel'].innerHTML).toContain('alpha');
    expect(elements['efficiency-panel'].innerHTML).toContain('omega');
    expect(elements['efficiency-panel'].innerHTML).toContain('18,000'); // 再分配 tokens
    expect(elements['efficiency-panel'].innerHTML).toContain('降低演练频率');
    expect(elements['efficiency-panel'].innerHTML).toContain('0.8000'); // token_efficiency
  });

  it('creates a real agent task from a token cost breakdown target', async () => {
    const request = vi.fn(async (url, opts) => {
      if (url === '/api/v1/cost/targets?status=active') return [];
      if (url === '/api/v1/cost/targets') return { id: 'tgt-1' };
      if (url === '/api/v1/agent-config/teams/cloud_ops/tasks') {
        expect(opts.method).toBe('POST');
        const body = JSON.parse(opts.body);
        expect(body.title).toContain('Token 成本优化');
        expect(body.metadata.source).toBe('cost-dashboard');
        expect(body.metadata.cost_target.key).toBe('cloud_ops');
        expect(body.metadata.cost_target.total).toBe(42500);
        return { task_id: 'task-cost-1' };
      }
      return null;
    });
    const { context, elements } = buildContext(request);
    context.window.CostDashboard.state.breakdown = [{ key: 'cloud_ops', total: 42500, calls: 10 }];

    const created = await context.window.CostDashboard.createOptimizationTask('breakdown', 0);

    expect(created.task_id).toBe('task-cost-1');
    expect(elements['cost-action-result'].innerHTML).toContain('task-cost-1');
  });

  it('creates a Plaza discussion from the selected token cost target', async () => {
    const request = vi.fn(async (url, opts) => {
      if (url === '/api/v1/agent-config/plaza?limit=50&offset=0') {
        return { items: [{ id: 'plaza-cost', name: '成本治理议事厅' }] };
      }
      if (url === '/api/v1/agent-config/plaza/plaza-cost/discussions') {
        expect(opts.method).toBe('POST');
        const body = JSON.parse(opts.body);
        expect(body.topic).toContain('Token 成本治理');
        expect(body.description).toContain('cost-dashboard');
        expect(body.goal).toContain('成本优化任务');
        return { id: 'disc-cost-1', topic: body.topic };
      }
      return null;
    });
    const { context, elements } = buildContext(request);
    context.window.CostDashboard.state.breakdown = [{ key: 'cloud_ops', total: 42500, calls: 10 }];

    const created = await context.window.CostDashboard.createPlazaTopic('breakdown', 0);

    expect(created.discussion.id).toBe('disc-cost-1');
    expect(elements['cost-action-result'].innerHTML).toContain('打开该话题');
  });

  it('runs a Token Gate self-check and refreshes gate stats', async () => {
    const request = vi.fn(async (url, opts) => {
      if (url === '/api/v1/cost-gate/token/evaluate') {
        expect(opts.method).toBe('POST');
        const body = JSON.parse(opts.body);
        expect(body.inline.total).toBe(90000); // 取 token 消耗最高团队为样本
        expect(body.budget.max_tokens).toBe(1000000);
        return { decision: 'block', violations: [{ id: 'token-budget' }], efficiency: 0.02 };
      }
      if (url === '/api/v1/cost-gate/token/stats') {
        return { passed: 1, warned: 0, blocked: 1 };
      }
      return null;
    });
    const { context, elements } = buildContext(request);
    context.window.CostDashboard.state.sustainability = tokenTeams();

    const report = await context.window.CostDashboard.runCostGateSelfCheck();

    expect(report.decision).toBe('block');
    expect(elements['cost-action-result'].innerHTML).toContain('Token Gate');
    expect(elements['cost-action-result'].innerHTML).toContain('block');
    expect(elements['governance-panel'].innerHTML).toContain('Gate 统计');
    expect(elements['governance-panel'].innerHTML).toContain('1 阻');
  });
});
