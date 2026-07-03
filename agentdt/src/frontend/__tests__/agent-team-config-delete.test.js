import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('deleteSelectedTeams', () => {
  const src = read('src/frontend/js/agent-team-config.js');

  it('冻结快照 snapshot 数组 [{id, name}]', () => {
    expect(src).toContain('var snapshot = []');
    expect(src).toContain('id: tid');
    expect(src).toContain('name: name');
  });

  it('从 cb.dataset.name 或 parentElement.label 取名称', () => {
    expect(src).toContain('cb.dataset.name');
    expect(src).toContain('parentElement.querySelector');
  });

  it('每条显示 • 名称 [id]', () => {
    expect(src).toContain("• ' + x.name + '  [");
    expect(src).toContain("x.id + ']'");
  });

  it('删除走 snapshot 而非 DOM', () => {
    expect(src).toContain('snapshot[i].id');
    expect(src).not.toContain('for (const teamId of ids)');
  });

  it('checkbox 模板有 data-name', () => {
    expect(src).toContain('data-name=');
  });
});
