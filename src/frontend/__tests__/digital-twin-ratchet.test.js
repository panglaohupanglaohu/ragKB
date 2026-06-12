import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('Agent digital twin ratchet record UI', () => {
  it('shows scenario ratchet generation and the record to beat', () => {
    const html = read('src/frontend/Agent-digital-twin.html');
    expect(html).toContain('GP2-5');
    expect(html).toContain('/api/v1/ratchet/metrics?prefix=');
    expect(html).toContain('scenario_best:');
    expect(html).toContain('本次要打破的纪录');
    expect(html).toContain('rec.generation');
  });
});
