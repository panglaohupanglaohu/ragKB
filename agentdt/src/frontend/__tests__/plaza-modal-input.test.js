import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('plaza modal input guards', () => {
  it('keeps clipboard and IME events inside modal text inputs', () => {
    const source = read('src/frontend/js/plaza.js');

    expect(source).toContain('function installModalInputGuards(modal)');
    expect(source).toContain('function isModalTextInput(target)');
    expect(source).toContain("'copy', 'cut', 'paste'");
    expect(source).toContain("'compositionstart', 'compositionupdate', 'compositionend'");
    expect(source).toContain('event.stopPropagation()');
    expect(source).toContain('installModalInputGuards(modal)');
    expect(source).not.toContain('event.preventDefault()');
  });
});
