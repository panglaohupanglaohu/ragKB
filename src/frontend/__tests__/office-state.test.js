/**
 * P7-1: OfficeState reducer 单测 — 单一数据源的纯函数契约
 */
import { describe, expect, it } from 'vitest';
import { initialState, reduce, collabStats, createStore } from '../js/office/office-state.js';

describe('office-state reducer', () => {
  it('team_sync 建档并分配工位与项圈', () => {
    const s = reduce(initialState(), {
      type: 'team_sync',
      agents: [{ id: 'pm', name: '经理', role: 'pm' }, { id: 'dev', name: '开发' }],
    });
    expect(Object.keys(s.agents)).toEqual(['pm', 'dev']);
    expect(s.agents.pm.deskIndex).toBe(0);
    expect(s.agents.dev.deskIndex).toBe(1);
    expect(s.agents.pm.collar).not.toBe(s.agents.dev.collar);
  });

  it('position 事件按房间语义映射活动', () => {
    let s = reduce(initialState(), { type: 'position', agentId: 'a1', room: 'council-hall' });
    expect(s.agents.a1.activity).toBe('meeting');
    s = reduce(s, { type: 'position', agentId: 'a1', room: 'rest-area' });
    expect(s.agents.a1.activity).toBe('coffee');
    s = reduce(s, { type: 'position', agentId: 'a1', room: 'unknown-room' });
    expect(s.agents.a1.activity).toBe('working');
  });

  it('step 的 offer_help 产生协作光线并累计协作热度', () => {
    let s = initialState();
    s = reduce(s, { type: 'step', agentActions: { dev: { action: 'offer_help', target: 'qa' } } });
    s = reduce(s, { type: 'step', agentActions: { dev: { action: 'offer_help', target: 'qa' } } });
    expect(s.edges.length).toBe(2);
    expect(s.collab['dev→qa']).toBe(2);
    expect(collabStats(s, 5)[0]).toEqual({ pair: 'dev→qa', count: 2 });
  });

  it('disabled 动作让 Agent 去茶水吧（混沌可视化）', () => {
    const s = reduce(initialState(), { type: 'step', agentActions: { ops: { action: 'disabled' } } });
    expect(s.agents.ops.activity).toBe('coffee');
  });

  it('discussion 聚拢参与者到白板并记录要点，结束清板归位', () => {
    let s = reduce(initialState(), { type: 'team_sync', agents: [{ id: 'a' }, { id: 'b' }] });
    s = reduce(s, { type: 'discussion', active: true, speakerId: 'a', boardLine: '步骤1: 调研现状' });
    expect(s.meeting.active).toBe(true);
    expect(s.agents.a.activity).toBe('meeting');
    expect(s.meeting.boardLines).toEqual(['步骤1: 调研现状']);
    s = reduce(s, { type: 'discussion', active: false });
    expect(s.meeting.boardLines).toEqual([]);
    expect(s.agents.a.activity).toBe('working');
  });

  it('trial_status running/evaluating 切镜像层，completed 回生产层', () => {
    let s = reduce(initialState(), { type: 'team_sync', agents: [{ id: 'a' }] });
    s = reduce(s, { type: 'trial_status', status: 'running' });
    expect(s.mirror).toBe(true);
    expect(s.agents.a.layer).toBe('mirror');
    s = reduce(s, { type: 'trial_status', status: 'completed' });
    expect(s.mirror).toBe(false);
    expect(s.agents.a.layer).toBe('prod');
  });

  it('tick 衰减并清理过期协作光线', () => {
    let s = reduce(initialState(), { type: 'step', agentActions: { a: { action: 'communicate', target: 'b' } } });
    for (let i = 0; i < 7; i++) s = reduce(s, { type: 'tick', dt: 1 });
    expect(s.edges.length).toBe(0);
    expect(s.collab['a→b']).toBe(1); // 热度保留，光线消失
  });

  it('reducer 纯度: 不修改前一状态', () => {
    const s0 = reduce(initialState(), { type: 'team_sync', agents: [{ id: 'a' }] });
    const frozen = JSON.stringify(s0);
    reduce(s0, { type: 'position', agentId: 'a', room: 'council-hall' });
    reduce(s0, { type: 'step', agentActions: { a: { action: 'offer_help', target: 'b' } } });
    expect(JSON.stringify(s0)).toBe(frozen);
  });

  it('team_reset 整体替换花名册: 移除未选成员并清理其协作边', () => {
    let s = reduce(initialState(), {
      type: 'team_sync',
      agents: [{ id: 'a' }, { id: 'b' }, { id: 'c' }],
    });
    s = reduce(s, { type: 'step', agentActions: { a: { action: 'offer_help', target: 'c' } } });
    s = reduce(s, { type: 'team_reset', agents: [{ id: 'a' }, { id: 'b' }] });
    expect(Object.keys(s.agents)).toEqual(['a', 'b']);
    expect(s.edges.length).toBe(0);            // 指向被移除成员的边一并清理
    expect(s.agents.a.deskIndex).toBe(0);
    expect(s.agents.a.activity).toBe('working');
  });

  it('座位保序前移: 顺序抖动不动座, 减员时保留者前移压缩不互换', () => {
    let s = reduce(initialState(), {
      type: 'team_sync', agents: [{ id: 'a' }, { id: 'b' }, { id: 'c' }],
    });
    // 同一批人换个顺序 reset → 座位恒等映射，无人移动（不玩抢椅子）
    s = reduce(s, { type: 'team_reset', agents: [{ id: 'c' }, { id: 'a' }, { id: 'b' }] });
    expect(s.agents.a.deskIndex).toBe(0);
    expect(s.agents.b.deskIndex).toBe(1);
    expect(s.agents.c.deskIndex).toBe(2);
    // 模拟幽灵成员场景: a/c 曾被挤到后排(10/12号桌), 幽灵清除后应前移压缩且保持相对次序
    s.agents.a.deskIndex = 10;
    s.agents.c.deskIndex = 12;
    s = reduce(s, { type: 'team_reset', agents: [{ id: 'c' }, { id: 'a' }] });
    expect(s.agents.a.deskIndex).toBe(0);      // 前移到前排
    expect(s.agents.c.deskIndex).toBe(1);      // 相对次序保持 a<c
    // 新人排在保留者之后
    s = reduce(s, { type: 'team_reset', agents: [{ id: 'a' }, { id: 'c' }, { id: 'd' }] });
    expect(s.agents.d.deskIndex).toBe(2);
  });

  it('设施排队: 容量1, FIFO, 到时释放队首补位并重新计时', () => {
    let s = reduce(initialState(), {
      type: 'team_sync', agents: [{ id: 'a' }, { id: 'b' }, { id: 'c' }],
    });
    const t0 = 1000000;
    s = reduce(s, { type: 'break_request', agentId: 'a', facility: 'toilet', now: t0 });
    s = reduce(s, { type: 'break_request', agentId: 'b', facility: 'toilet', now: t0 + 1000 });
    s = reduce(s, { type: 'break_request', agentId: 'c', facility: 'toilet', now: t0 + 2000 });
    expect(s.facilities.toilet.occupant).toBe('a');
    expect(s.facilities.toilet.queue).toEqual(['b', 'c']);       // FIFO 排队
    expect(s.facilities.toilet.until).toBe(t0 + 300e3);          // 马桶停留 5 分钟
    expect(s.agents.b.activity).toBe('toilet');
    // 未到时: 不释放
    s = reduce(s, { type: 'break_tick', now: t0 + 200e3 });
    expect(s.facilities.toilet.occupant).toBe('a');
    // 到时: a 回工位, b 补位并重新计时 5 分钟
    s = reduce(s, { type: 'break_tick', now: t0 + 300e3 });
    expect(s.agents.a.activity).toBe('working');
    expect(s.facilities.toilet.occupant).toBe('b');
    expect(s.facilities.toilet.queue).toEqual(['c']);
    expect(s.facilities.toilet.until).toBe(t0 + 300e3 + 300e3);
  });

  it('咖啡机停留 1 分钟; 排队中被 team_reset 移除的成员出队', () => {
    let s = reduce(initialState(), {
      type: 'team_sync', agents: [{ id: 'a' }, { id: 'b' }],
    });
    s = reduce(s, { type: 'break_request', agentId: 'a', facility: 'coffee', now: 0 });
    s = reduce(s, { type: 'break_request', agentId: 'b', facility: 'coffee', now: 1 });
    expect(s.facilities.coffee.until).toBe(60e3);                // 咖啡 1min
    s = reduce(s, { type: 'team_reset', agents: [{ id: 'a' }] });
    expect(s.facilities.coffee.queue).toEqual([]);               // b 离编即出队
  });

  it('store dispatch/subscribe 工作正常', () => {
    const store = createStore();
    let called = 0;
    store.subscribe(() => { called += 1; });
    store.dispatch({ type: 'team_sync', agents: [{ id: 'x' }] });
    expect(called).toBe(1);
    expect(store.getState().agents.x).toBeTruthy();
  });
});
