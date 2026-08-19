/**
 * Plaza E-1/E-3/E-4/E-5/D-1/D-2: vitest smoke for new features
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('Plaza confirm→modal (E-1)', () => {
  it('deletePlaza uses showConfirm not confirm()', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain('function showConfirm(');
    expect(src).toContain("showConfirm(plazaT('confirm.deletePlaza'");
    expect(src).toContain("showConfirm(plazaT('confirm.deleteDiscussion')");
    expect(src).not.toContain("confirm('删除这个讨论？')");
    expect(src).not.toContain("confirm(`确定删除广场");
  });

  it('showConfirm renders modal with role=dialog', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain("setAttribute('role', 'dialog')");
    expect(src).toContain("setAttribute('aria-modal', 'true')");
    expect(src).toContain("Escape");
  });
});

describe('Plaza TTS debug flag (E-3)', () => {
  it('DEBUG_TTS flag exists and defaults to false', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain('const DEBUG_TTS = false');
    expect(src).toContain('const tlog = ');
    expect(src).toContain('const twarn = ');
  });

  it('TTS console.log replaced with tlog/twarn', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain("tlog('[TTS] Fetching audio");
    expect(src).toContain("twarn('[TTS] Skipped");
    // Should NOT have raw console.log for TTS
    expect(src).not.toContain("console.log('[TTS] Fetching audio");
    expect(src).not.toContain("console.warn('[TTS] Skipped");
  });
});

describe('Plaza accessibility (E-4)', () => {
  it('canvas has aria-label', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain("aria-label', '议事厅 3D 场景");
  });

  it('speech bubbles have aria-hidden', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain("setAttribute('aria-hidden', 'true')");
  });
});

describe('Plaza performance (D-1/D-2)', () => {
  it('visibilitychange pauses render', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain('visibilitychange');
    expect(src).toContain('_renderPaused');
    expect(src).toContain('document.hidden');
  });

  it('empty arena reduces frame rate', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain('_emptyFrameSkip');
    expect(src).toContain('!allParticipants.length');
  });
});

describe('Plaza init error handling (E-5)', () => {
  it('init() wrapped in try/catch with toast', () => {
    const src = read('src/frontend/js/plaza.js');
    expect(src).toContain('async function init() {');
    expect(src).toContain('try {');
    expect(src).toContain('初始化失败，请刷新或检查后端服务');
  });
});
