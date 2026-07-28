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
    expect(page).toContain('memory-style');
    expect(page).toContain('memoryStyleName');
  });

  it('supports Will create preflight execute and migration audit UI', () => {
    expect(page).toContain('/wills');
    expect(page).toContain('will-create');
    expect(page).toContain('will-preflight');
    expect(page).toContain('will-execute');
    expect(page).toContain('/migrations');
    expect(page).toContain('/inherited');
    expect(page).toContain('conflict_strategy');
    expect(page).toContain('merge 继承分区');
    expect(page).toContain('继承自');
    expect(page).toContain('rolled_back');
  });

  it('hides prototype names and exposes an agent-owned memory style', () => {
    expect(html).not.toContain('<b>小满</b>');
    expect(html).not.toContain('<b>沈弥安</b>');
    expect(html).toContain('每个 Agent 都会形成自己的记忆方式');
    expect(page).toContain('连续性');
    expect(page).toContain('克制性');
    expect(page).toContain('前瞻意图·过程');
  });

  it('supports shared log preview and co_writer path', () => {
    expect(page).toContain('data-preview-owner');
    expect(page).toContain('/shared/');
    expect(page).toContain('data-cowrite-owner');
    expect(page).toContain('health_avg');
  });
});
