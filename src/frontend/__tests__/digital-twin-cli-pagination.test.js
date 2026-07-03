import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('digital-twin-cli pagination consumers', () => {
  it('uses shared list helper for paginated platform reads', () => {
    const source = read('src/frontend/js/digital-twin-cli.js');
    expect(source).toContain('async function _list(url,limit=200,offset=0)');
    expect(source).toContain("const teams=await _list(`${API}/teams`,200,0);");
    expect(source).toContain("const agents=await _list(`${API}/teams/${tid}/agents`,200,0);");
    expect(source).toContain("S.skills=await _list(`${API}/skills`,200,0)");
    expect(source).toContain("S.tools=await _list(`${API}/tools`,200,0)");
    expect(source).toContain("async function _plazas(){return _list(`${API}/plaza`,200,0)}");
    expect(source).toContain("async function _plazaDiscussions(plazaId){return _list(`${API}/plaza/${plazaId}/discussions`,200,0)}");
    expect(source).toContain("const plazas=await _plazas();");
    expect(source).toContain("const discs=await _plazaDiscussions(p.id);");
    expect(source).toContain("const tasks=await _list(`${API}/teams/${tid}/tasks`,200,0);");
    expect(source).toContain("const items=await _list(`${EVOLVE_API}/items`,200,0);");
    expect(source).toContain("_secsTeams = await _list('/api/v1/agent-config/teams',200,0);");
    expect(source).toContain("_secsTaskCache[teamId] = await _list(`/api/v1/agent-config/teams/${teamId}/tasks`,200,0);");
    expect(source).toContain("teamAgents = await _list(`/api/v1/agent-config/teams/${teamId}/agents`,200,0);");
    expect(source).not.toContain("const pr=await _af(`${API}/plaza`);");
    expect(source).not.toContain("const dr=await _af(`${API}/plaza/${p.id}/discussions`);");
  });
});
