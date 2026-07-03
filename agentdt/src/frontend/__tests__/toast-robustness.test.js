/**
 * B-4.1: toast decorateErrorMessage 健壮性 — 源码级断言
 * 验证 system-evolution.js 中 toast() 的 shouldDecorate 逻辑不会因 api 缺失而崩溃
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('toast robustness (B-4.1)', () => {
  it('toast 使用可选链 api?.decorateErrorMessage 防崩溃', () => {
    const src = read('src/frontend/js/system-evolution.js');
    // 验证 toast 函数存在
    expect(src).toContain('function toast(');
    // 验证可选链保护
    expect(src).toContain('window.api?.decorateErrorMessage');
    // 验证 shouldDecorate 标志控制装饰逻辑
    expect(src).toContain('shouldDecorate');
  });

  it('renderError 使用 data-retry 事件委托替代 toString() 内联', () => {
    const src = read('src/frontend/js/system-evolution.js');
    expect(src).toContain('data-retry');
    expect(src).toContain('_retryMap');
    // 不应再有旧模式 onclick="(${retryFn.toString()})()"
    expect(src).not.toContain('onclick="(${retryFn.toString()})()"');
  });

  it('closeItem 不再使用 prompt()', () => {
    const src = read('src/frontend/js/system-evolution.js');
    expect(src).toContain('showCloseForm');
    expect(src).toContain('submitCloseForm');
    // 不应再有 prompt 调用
    expect(src).not.toContain("prompt('关闭理由");
    expect(src).not.toContain("prompt('验证结论");
  });
});
