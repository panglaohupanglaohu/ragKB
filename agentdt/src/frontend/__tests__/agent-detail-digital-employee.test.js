import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { describe, expect, it, vi } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

function makeElement() {
  return {
    innerHTML: '',
    textContent: '',
    value: '',
    style: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    addEventListener() {},
    removeEventListener() {},
    focus() {},
  };
}

describe('agent detail digital employee panel', () => {
  it('renders the four profile files, triggers, relationships, and governance', async () => {
    const elements = Object.create(null);
    const document = {
      getElementById(id) {
        if (!elements[id]) elements[id] = makeElement();
        return elements[id];
      },
      querySelectorAll() { return []; },
      querySelector() { return null; },
      addEventListener() {},
    };
    document.getElementById('agent-content');

    const api = vi.fn(async (url) => {
      if (url.includes('/files/soul')) return { content: '# Soul', exists: true, updated_at: '2026-06-13T00:00:00Z' };
      if (url.includes('/files/focus')) return { content: '- [ ] 每日复盘', exists: true, updated_at: '2026-06-13T00:00:00Z' };
      if (url.includes('/files/memory')) return { content: '# Memory', exists: true };
      if (url.includes('/files/heartbeat')) return { content: '# Heartbeat', exists: true };
      if (url.includes('/focus-items')) return { items: [{ text: '每日复盘', done: false }] };
      if (url.includes('/triggers')) return { triggers: [{ trigger_id: 'trg1', trigger_type: 'interval', focus_item: '每日复盘', config: { every_minutes: 10 }, enabled: true, fire_count: 1 }] };
      if (url.includes('/relationships')) return { gate_mode: 'soft', relationships: [{ rel_id: 'rel1', kind: 'agent_agent', source_agent_id: 'a1', target_id: 'a2', rel_type: 'reviewer', note: 'review' }] };
      if (url.includes('/governance')) return { autonomy_level: 3, token_budget: 2048, fallback_model_id: 'cheap', budget_status: { used_today: 512 } };
      if (url.includes('/api/v1/agent-config/teams/teamA')) return { agents: [{ agent_id: 'a2', name: 'Reviewer' }], models: [{ model_id: 'cheap' }] };
      return null;
    });

    const context = vm.createContext({
      window: {},
      document,
      console,
      fetch: vi.fn(),
      api,
      A: '/api/v1/agent-config',
      tid: 'teamA',
      aid: 'a1',
      atab: 'ag-employee',
      el: (id) => document.getElementById(id),
      escapeHtml: (v) => String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;'),
      toast: vi.fn(),
      confirm: vi.fn(() => true),
      setTimeout,
      clearTimeout,
    });
    context.window = context.window || {};

    vm.runInContext(read('src/frontend/js/agent-detail.js'), context);
    context.window.renderEmployeeView({ name: 'Agent A', agent_id: 'a1' });
    await new Promise((resolve) => setTimeout(resolve, 0));

    const html = elements['agent-content'].innerHTML;
    expect(html).toContain('数字员工档案');
    expect(html).toContain('四件套');
    expect(html).toContain('Aware Trigger');
    expect(html).toContain('关系网络');
    expect(html).toContain('治理参数');
    expect(html).toContain('预览组织上下文');
    expect(html).toContain('每日复盘');
  });
});
