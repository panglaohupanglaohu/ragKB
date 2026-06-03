import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { afterEach, describe, expect, it, vi } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

function makeElement() {
  return {
    innerHTML: '',
    textContent: '',
    value: '',
    style: {},
    options: [],
    disabled: false,
    className: '',
    classList: {
      add() {},
      remove() {},
    },
    appendChild(child) {
      this.options.push(child);
      return child;
    },
    querySelector() {
      return null;
    },
    querySelectorAll() {
      return [];
    },
    scrollIntoView() {},
  };
}

function buildContext(requestImpl) {
  const elements = Object.create(null);
  const document = {
    getElementById(id) {
      if (!elements[id]) elements[id] = makeElement();
      return elements[id];
    },
    querySelectorAll() {
      return [];
    },
    querySelector() {
      return null;
    },
    createElement() {
      return makeElement();
    },
  };

  document.getElementById('panel-title');
  document.getElementById('panel-skip');

  const location = new URL('http://127.0.0.1:5173/system-evolution.html?panel=skip');
  const window = {
    location,
    api: {
      request: requestImpl,
    },
  };

  return {
    elements,
    context: vm.createContext({
      window,
      document,
      location,
      URL,
      URLSearchParams,
      requestAnimationFrame: (fn) => fn(),
      setTimeout,
      clearTimeout,
      console,
    }),
  };
}

describe('system-evolution dashboard', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('uses the agent-team evolution prefix and renders paginated overview items', async () => {
    const request = vi.fn(async (url) => {
      if (url === '/api/v1/agent-teams/evolution/summary') {
        return { audit_rules_count: 2, verify_tests_registered: 3, total_items: 1, by_status: { discovered: 1 }, by_domain: {}, by_severity: {}, by_operational_domain: {} };
      }
      if (url === '/api/v1/agent-teams/evolution/compliance-rating') {
        return { grade: 'A', score: 95, description: 'good', escalation_tier: 'normal' };
      }
      if (url === '/api/v1/agent-teams/evolution/items') {
        return { items: [{ id: 'item-1', title: 'Patch drift', status: 'discovered', severity: 'high', audit_domain: 'build', description: 'desc' }], total: 1, limit: 50, offset: 0, has_more: false };
      }
      if (url === '/api/v1/agent-teams/evolution/zones/active') {
        return [];
      }
      return null;
    });

    const { context, elements } = buildContext(request);
    vm.runInContext(read('src/frontend/js/system-evolution.js'), context);

    expect(typeof context.window.api.request).toBe('function');
    await context.loadOverview();

    expect(request).toHaveBeenCalledWith('/api/v1/agent-teams/evolution/summary', undefined);
    expect(elements['ov-items'].innerHTML).toContain('Patch drift');
    expect(elements['panel-badge'].textContent).toBe('1 项');
  });

  it('renders paginated optimize history envelopes', async () => {
    const request = vi.fn(async (url) => {
      if (url === '/api/v1/agent-teams/evolution/optimize/runs?limit=15') {
        return {
          items: [{
            run_id: 'run-1',
            target_type: 'skill',
            target_id: 'skill-1',
            status: 'completed',
            improved: true,
            baseline_score: 0.5,
            best_score: 0.75,
            score_delta: 0.25,
            started_at: '2026-06-03T01:00:00Z',
          }],
          total: 1,
          limit: 15,
          offset: 0,
          has_more: false,
        };
      }
      return [];
    });

    const { context, elements } = buildContext(request);
    vm.runInContext(read('src/frontend/js/system-evolution.js'), context);

    expect(typeof context.window.api.request).toBe('function');
    await context.loadEvolveHistory();

    expect(elements['ev-history-table'].innerHTML).toContain('run-1');
    expect(elements['ev-history-table'].innerHTML).toContain('75%');
  });
});
