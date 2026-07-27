import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('agent detail pagination consumers', () => {
  it('uses shared listApi helper for paginated reads', () => {
    const source = read('src/frontend/js/agent-detail.js');
    expect(source).toContain('async function listApi(path, limit = 200, offset = 0)');
    expect(source).toContain('return Array.isArray(payload)?payload:Array.isArray(payload?.items)?payload.items:[];');
    expect(source).toContain("listApi(`${A}/tools`,200,0)");
    expect(source).toContain("listApi(`${A}/teams/${tid}/skills`,200,0)");
    expect(source).toContain("listApi(`${A}/teams/${tid}/agents/${aid}/sessions`,200,0)");
  });

  it('shows resolved bound skills on the agent status page', () => {
    const source = read('src/frontend/js/agent-detail.js');
    const html = read('src/frontend/agent-team-config.html');
    expect(source).toContain('_resolveSkillLabels(tid,d.skills||[])');
    expect(source).toContain('⚡ 已绑定技能');
    expect(source).toContain("atab='ag-skills'");
    expect(html).toContain('/js/agent-detail.js?v=20260727-skill-binding');
  });
});
