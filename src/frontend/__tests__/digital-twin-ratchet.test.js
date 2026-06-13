import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('Agent digital twin ratchet record UI', () => {
  it('shows scenario ratchet generation and the record to beat', () => {
    const html = read('src/frontend/Agent-digital-twin.html');
    const v4 = read('src/frontend/js/digital-twin/v4-scenario-evolution.js');
    expect(html).toContain('/js/digital-twin/v4-scenario-evolution.js');
    expect(v4).toContain('GP2-5');
    expect(v4).toContain('/api/v1/ratchet/metrics?prefix=');
    expect(v4).toContain('scenario_best:');
    expect(v4).toContain('本次要打破的纪录');
    expect(v4).toContain('rec.generation');
  });
});
