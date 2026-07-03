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
    expect(source).toContain("listApi(`${A}/tools`,200,0)");
    expect(source).toContain("listApi(`${A}/teams/${tid}/skills`,200,0)");
    expect(source).toContain("listApi(`${A}/teams/${tid}/agents/${aid}/sessions`,200,0)");
  });
});
