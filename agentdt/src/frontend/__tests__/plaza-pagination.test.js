import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('plaza pagination consumers', () => {
  it('uses shared listApi for plaza list, team tree, and discussion list reads', () => {
    const source = read('src/frontend/js/plaza.js');
    expect(source).toContain("listApi(`${API}/plaza`, 200, 0)");
    expect(source).toContain("listApi(`${API}/teams-tree`, 200, 0)");
    expect(source).toContain("listApi(`${API}/plaza/${id}/discussions`, 200, 0)");
    expect(source).toContain("listApi(`${API}/plaza/${curPlaza}/discussions`, 200, 0)");
  });
});
