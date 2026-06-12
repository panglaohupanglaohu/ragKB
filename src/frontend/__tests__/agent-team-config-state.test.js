import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('agent-team-config state namespace', () => {
  it('stores page runtime state under window.AG.runtime', () => {
    const source = read('src/frontend/js/agent-team-config.js');
    expect(source).toContain('window.AG.runtime = window.AG.runtime || {');
    expect(source).toContain('const agRuntime = window.AG.runtime;');
    expect(source).toContain('agRuntime.traceDetailTaskId');
    expect(source).toContain('agRuntime.evoCachedItems');
    expect(source).toContain('agRuntime.editModelId');
    expect(source).toContain('agRuntime.claudeEventSource');
    expect(source).toContain('agRuntime.agentPollTimer');
  });

  it('wires the skill classification three-pool view', () => {
    const source = read('src/frontend/js/tools-skills.js');
    const html = read('src/frontend/agent-team-config.html');
    expect(html).toContain('id="skills-cards"');
    expect(source).toContain('/api/v1/skill-classification/teams/');
    expect(source).toContain('function renderSkillClassificationPanel(view)');
    expect(source).toContain('window.reclassifySkillPools = reclassifySkillPools');
    expect(source).toContain('特有 / 通用 / 储备');
  });
});
