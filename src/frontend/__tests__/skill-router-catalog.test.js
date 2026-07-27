import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('skill assignment catalog', () => {
  const source = read('src/frontend/js/skill-extract.js');
  const html = read('src/frontend/skill-extract.html');

  it('loads the visible skill catalog when router mode opens or team changes', () => {
    expect(source).toContain('async function loadRouterSkillCatalog()');
    expect(source).toContain('routerApi(`/browse?team_id=${encodeURIComponent(teamId)}`)');
    expect(source).toContain("if (mode === 'router') window._refreshRouterContext()");
    expect(source).toContain("document.body.classList.contains('mode-router')");
  });

  it('renders catalog items as directly selectable skills without fake scores', () => {
    expect(html).toContain('id="rresults-title">📚 可赋予技能');
    expect(html).toContain('/js/skill-extract.js?v=20260727-skill-binding');
    expect(source).toContain('_catalog: true');
    expect(source).toContain("score == null ?");
    expect(source).toContain("value !== null && value !== undefined && value !== ''");
    expect(source).toContain('routerResults = results.filter');
    expect(source).toContain('正在加载技能目录');
    expect(source).toContain('当前团队没有可见技能');
  });

  it('keeps selected catalog skills when switching to routed results', () => {
    expect(source).toContain("if (routerDisplayMode === 'catalog')");
    expect(source).toContain('routerSelectedSkills.has(r.skill_id || r.slug || r.name)');
    expect(source).toContain('routerResults[existingByKey.get(k)] = r');
  });

  it('refreshes the agent profile and links to bound skills after assignment', () => {
    expect(source).toContain('await _loadAgentProfile(selectedAgentId);');
    expect(source).toContain('&atab=ag-skills`');
    expect(source).toContain('data.assigned_count ?? skillIds.length');
  });
});
