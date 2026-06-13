/**
 * B-1: closeItem form validation smoke test
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('closeItem inline form (B-1)', () => {
  it('showCloseForm renders textareas, not prompt()', () => {
    const src = read('src/frontend/js/system-evolution.js');
    expect(src).toContain('function showCloseForm(');
    expect(src).toContain('id="close-reason"');
    expect(src).toContain('id="close-conclusion"');
    expect(src).toContain('id="close-submit-btn"');
    // No prompt calls
    expect(src).not.toContain("prompt('关闭理由");
    expect(src).not.toContain("prompt('验证结论");
  });

  it('updateCloseValidation disables button when empty', () => {
    const src = read('src/frontend/js/system-evolution.js');
    expect(src).toContain('function updateCloseValidation');
    expect(src).toContain('btn.disabled');
    expect(src).toContain('请填写关闭理由');
    expect(src).toContain('请填写验证结论');
  });

  it('submitCloseForm sends POST with reason and conclusion', () => {
    const src = read('src/frontend/js/system-evolution.js');
    expect(src).toContain('function submitCloseForm');
    expect(src).toContain('/close');
    expect(src).toContain('verify_conclusion');
    expect(src).toContain('refreshCurrent()');
  });
});
