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
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
}

function buildContext(listImpl) {
  const elements = Object.create(null);
  const document = {
    getElementById(id) {
      if (!elements[id]) elements[id] = makeElement();
      return elements[id];
    },
    createElement() { return makeElement(); },
    body: { insertAdjacentHTML() {} },
  };

  const window = {
    api: {
      list: listImpl,
    },
  };

  const context = vm.createContext({
    window,
    document,
    console,
    A: '/api/v1/agent-config',
    tid: 'build_system',
    aid: '',
    api: vi.fn(async () => null),
    el(id) { return document.getElementById(id); },
    escapeHtml(v) { return String(v ?? ''); },
    toast() {},
    hideViewLoading() {},
    openModal() {},
    closeModal() {},
    confirm() { return true; },
    alert() {},
    Blob,
    URL,
  });

  return { context, elements };
}

describe('tools-skills pagination consumers', () => {
  it('loadSkills uses window.api.list and renders team skills', async () => {
    const list = vi.fn(async (url, limit, offset) => {
      expect(limit).toBe(200);
      expect(offset).toBe(0);
      if (url === '/api/v1/agent-config/teams/build_system/skills') {
        return {
          items: [
            { skill_id: 'skill-1', name: 'Code Implementation', category: 'coding', enabled: true, description: 'desc' },
          ],
          total: 1,
          limit,
          offset,
          has_more: false,
        };
      }
      return { items: [], total: 0, limit, offset, has_more: false };
    });

    const { context, elements } = buildContext(list);
    vm.runInContext(read('src/frontend/js/tools-skills.js'), context);

    await context.window.loadSkills();

    expect(list).toHaveBeenCalledWith('/api/v1/agent-config/teams/build_system/skills', 200, 0);
    expect(elements['skills-cards'].innerHTML).toContain('Code Implementation');
  });
});
