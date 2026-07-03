import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { describe, it, expect } from 'vitest';

function loadAGCtx() {
  const code = readFileSync(path.join(process.cwd(), 'src/frontend/js/ag-context.js'), 'utf8');
  const store = {};
  const localStorage = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
  };
  const listeners = {};
  const win = {
    localStorage,
    addEventListener: (t, fn) => { (listeners[t] = listeners[t] || []).push(fn); },
  };
  win.window = win;
  const ctx = vm.createContext(win);
  vm.runInContext(code, ctx);
  return {
    AGCtx: win.AGCtx,
    store,
    fireStorage: (key, newValue) => { (listeners.storage || []).forEach((fn) => fn({ key, newValue })); },
  };
}

describe('AGCtx 选择上下文总线', () => {
  it('set/get + 持久化(team 兼容旧键 ag_current_team)', () => {
    const { AGCtx, store } = loadAGCtx();
    expect(AGCtx.set('team', 'build_system')).toBe(true);
    expect(AGCtx.get('team')).toBe('build_system');
    expect(store['ag_ctx_team']).toBe('build_system');
    expect(store['ag_current_team']).toBe('build_system');
  });

  it('去重:同值再 set 返回 false 且不广播', () => {
    const { AGCtx } = loadAGCtx();
    AGCtx.set('room', 'council');
    let calls = 0; AGCtx.on(() => calls++);
    expect(AGCtx.set('room', 'council')).toBe(false);
    expect(calls).toBe(0);
    expect(AGCtx.set('room', 'dev')).toBe(true);
    expect(calls).toBe(1);
  });

  it('on 订阅收到 key/value;取消订阅生效', () => {
    const { AGCtx } = loadAGCtx();
    const got = []; const off = AGCtx.on((k, v) => got.push([k, v]));
    AGCtx.set('agent', 'pm');
    off(); AGCtx.set('agent', 'dev');
    expect(got).toEqual([['agent', 'pm']]);
  });

  it('storage 事件跨页静默入站(不回写、标记 fromStorage)', () => {
    const { AGCtx, fireStorage } = loadAGCtx();
    const got = []; AGCtx.on((k, v, opts) => got.push([k, v, opts.fromStorage]));
    fireStorage('ag_ctx_scenario', 'room_council');
    expect(AGCtx.get('scenario')).toBe('room_council');
    expect(got[0]).toEqual(['scenario', 'room_council', true]);
  });
});
