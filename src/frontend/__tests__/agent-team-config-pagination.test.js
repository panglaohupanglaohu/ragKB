import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('agent-team-config pagination consumers', () => {
  it('uses shared apiList helper for paginated embedded views', () => {
    const source = read('src/frontend/js/agent-team-config.js');
    expect(source).toContain('async function apiList(p, limit=200, offset=0)');
    expect(source).toContain("const teams=await apiList(`${A}/teams`,200,0);");
    expect(source).toContain("apiList(`${EVP}/rules`,50,0)");
    expect(source).toContain("apiList(itemsUrl,50,0)");
    expect(source).toContain("const sessions=await apiList(`${A}/llm/sessions`,50,0);");
    expect(source).toContain("const d=await apiList(`${A}/teams/${tid}/models`,200,0);");
    expect(source).toContain("const models=await apiList(`${A}/teams/${tid}/models`,200,0);");
  });
});
