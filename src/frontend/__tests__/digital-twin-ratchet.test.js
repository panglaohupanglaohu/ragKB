import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('Agent digital twin ratchet record UI', () => {
  it('shows scenario ratchet generation and the record to beat', () => {
    const html = read('src/frontend/Agent-digital-twin.html');
    const v4s = read('src/frontend/js/digital-twin/v4-scenarios.js');
    expect(html).toContain('/js/digital-twin/v4-scenarios.js');
    expect(v4s).toContain('GP2-5');
    expect(v4s).toContain('/api/v1/ratchet/metrics?prefix=');
    expect(v4s).toContain('scenario_best:');
    expect(v4s).toContain('本次要打破的纪录');
    expect(v4s).toContain('rec.generation');
  });
});
