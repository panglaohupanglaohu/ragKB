import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('skill publish quality gate UI wiring', () => {
  it('routes public publish actions through publishSkillWithGate', () => {
    const source = read('src/frontend/js/skill-extract.js');
    expect(source).toContain("async function publishSkillWithGate(skillId, skillName)");
    expect(source).toContain("'/skill-library/publish-gate'");
    expect(source).toContain('发布门禁未通过');
    expect(source.match(/publishSkillWithGate\(/g)?.length || 0).toBeGreaterThanOrEqual(4);
  });
});
