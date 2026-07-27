import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const source = readFileSync(
  path.join(process.cwd(), 'src/frontend/Agent-digital-twin.html'),
  'utf8',
);

describe('digital twin office layout', () => {
  it('hides legacy room tabs only in office mode', () => {
    expect(source).toContain('body.office-mode #room-tabs { display: none !important; }');
    expect(source).toContain('<div id="room-tabs"');
  });
});
