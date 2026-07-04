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

  it('store dispatch/subscribe 工作正常', () => {
    const store = createStore();
    let called = 0;
    store.subscribe(() => { called += 1; });
    store.dispatch({ type: 'team_sync', agents: [{ id: 'x' }] });
    expect(called).toBe(1);
    expect(store.getState().agents.x).toBeTruthy();
  });
});
