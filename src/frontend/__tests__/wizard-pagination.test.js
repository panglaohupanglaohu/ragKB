import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('wizard pagination consumers', () => {
  it('uses shared listApi helper for paginated bootstrap reads', () => {
    const source = read('src/frontend/js/wizard.js');
    expect(source).toContain('async function listApi(path, limit = 200, offset = 0)');
    expect(source).toContain("listApi(`${A}/teams`,200,0)");
    expect(source).toContain("listApi(`${A}/teams/${w.team_id||tid}/models`,200,0)");
    expect(source).toContain("listApi(`${A}/skills`,200,0)");
    expect(source).toContain("listApi(`${A}/tools`,200,0)");
  });
});
