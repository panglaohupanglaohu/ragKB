/**
 * Skill-extract: B/C series smoke — confirm modal, request_id, DEBUG flag
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('Skill-extract confirm→modal (B)', () => {
  const src = read('src/frontend/js/skill-extract.js');

  it('showConfirm helper exists', () => {
    expect(src).toContain('function showConfirm(');
  });

  it('openInputModal helper exists', () => {
    expect(src).toContain('function openInputModal(');
  });

  it('no raw confirm() calls remain', () => {
    expect(src).not.toContain("if (!confirm('确认删除此萃取项？'))");
    expect(src).not.toContain("if (!confirm(`确认回滚技能到版本");
    expect(src).not.toContain("if (confirm('当前已有内容，是否用示例替换？'))");
    expect(src).not.toContain("if (confirm(`确认删除技能「${s.name}」？))");
  });

  it('no raw prompt() calls remain', () => {
    expect(src).not.toContain("prompt('拒绝原因（可选）：')");
    expect(src).not.toContain("prompt('待办标题:')");
  });
});

describe('Skill-extract robustness (C)', () => {
  const src = read('src/frontend/js/skill-extract.js');
  const html = read('src/frontend/skill-extract.html');

  it('DEBUG_SK flag exists', () => {
    expect(src).toContain('const DEBUG_SK = false');
    expect(src).toContain('const sklog = ');
    expect(src).toContain('const skwarn = ');
  });

  it('X-Request-ID header in api()', () => {
    expect(src).toContain("'X-Request-ID'");
    expect(src).toContain('_nextSkReqId');
  });

  it('canvas has aria-label', () => {
    expect(html).toContain('aria-label="技能萃取 3D 场景"');
  });

  it('modal has role=dialog', () => {
    expect(html).toContain('role="dialog"');
    expect(html).toContain('aria-modal="true"');
  });
});
