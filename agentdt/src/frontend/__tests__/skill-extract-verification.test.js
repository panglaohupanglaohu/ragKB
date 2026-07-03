import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('skill extraction verification evidence UI', () => {
  it('surfaces sandbox/container evidence instead of claiming LLM-only verification', () => {
    const source = read('src/frontend/js/skill-extract.js');

    expect(source).toContain('沙箱 / 容器验证证据');
    expect(source).toContain('runtime:');
    expect(source).toContain('stdout / stderr');
    expect(source).toContain('artifact:');
    expect(source).not.toContain('不涉及容器/沙箱');
  });
});
