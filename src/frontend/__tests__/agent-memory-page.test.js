import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(rel) {
  return readFileSync(path.join(process.cwd(), rel), 'utf8');
}

describe('agent-memory hub page', () => {
  const page = read('src/frontend/js/agent-memory-page.js');
  const html = read('src/frontend/agent-memory.html');
  const nav = read('src/frontend/js/nav.js');

  it('registers Agent记忆 in site nav', () => {
    expect(nav).toContain("id: 'memory'");
    expect(nav).toContain('Agent记忆');
    expect(nav).toContain('/agent-memory.html');
  });

  it('has hub segments for overview share transfer persona lifecycle', () => {
    expect(html).toContain('data-seg="overview"');
    expect(html).toContain('data-seg="share"');
    expect(html).toContain('data-seg="transfer"');
    expect(html).toContain('data-seg="persona"');
    expect(html).toContain('data-seg="lifecycle"');
  });

  it('supports URL deep link team_id agent_id seg', () => {
    expect(page).toContain('team_id');
    expect(page).toContain('agent_id');
    expect(page).toContain('qSeg');
  });

  it('wires share grant and transfer execute APIs', () => {
    expect(page).toContain('/share');
    expect(page).toContain('/transfer');
    expect(page).toContain('share-matrix');
    expect(page).toContain('xiaoman');
    expect(page).toContain('shenmian');
  });

  it('supports shared log preview and co_writer path', () => {
    expect(page).toContain('data-preview-owner');
    expect(page).toContain('/shared/');
    expect(page).toContain('data-cowrite-owner');
    expect(page).toContain('health_avg');
  });
});
