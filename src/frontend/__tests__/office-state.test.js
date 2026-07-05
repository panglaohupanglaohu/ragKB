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

  it('step 动作词表: delegate 与 comm 边类型区分', () => {
    let s = reduce(initialState(), { type: 'step', agentActions: { pm: { action: 'delegate', target: 'dev' } } });
    s = reduce(s, { type: 'step', agentActions: { dev: { action: 'communicate', target: 'qa' } } });
    const kinds = s.edges.map((e) => e.kind).sort();
    expect(kinds).toEqual(['comm', 'delegate']);
    expect(s.agents.pm.lastAction).toBe('delegate');
  });

  it('step 动作词表: communicate broadcast 产生 broadcast 边（无定向目标）', () => {
    const s = reduce(initialState(), { type: 'step', agentActions: { pm: { action: 'communicate', target: 'broadcast' } } });
    const bc = s.edges.find((e) => e.kind === 'broadcast');
    expect(bc).toBeTruthy();
    expect(bc.from).toBe('pm');
    expect(bc.to).toBe('*');
  });

  it('step 动作词表: execute_skill 记录 skillUsed, claim_task 记录 task', () => {
    let s = reduce(initialState(), { type: 'step', agentActions: { dev: { action: 'execute_skill', skill_used: 'code_review' } } });
    expect(s.agents.dev.skillUsed).toBe('code_review');
    expect(s.agents.dev.activity).toBe('working');
    s = reduce(s, { type: 'step', agentActions: { dev: { action: 'claim_task', task: 'T-42' } } });
    expect(s.agents.dev.task).toBe('T-42');
    expect(s.agents.dev.lastAction).toBe('claim_task');
  });

  it('step 动作词表: idle → idle 活动', () => {
    const s = reduce(initialState(), { type: 'step', agentActions: { dev: { action: 'idle' } } });
    expect(s.agents.dev.activity).toBe('idle');
  });

  it('workflow_sync 归一工作流边（源→目标+内容/类型+顺序）', () => {
    const s = reduce(initialState(), {
      type: 'workflow_sync',
      edges: [
        { source: 'pm', target: 'dev', channel: '任务卡', message_type: 'delegate' },
        { source: 'dev', target: 'qa', channel: '构建产物', message_type: 'request' },
        { source: '', target: 'x' },   // 缺 from → 丢弃
      ],
    });
    expect(s.workflow.length).toBe(2);
    expect(s.workflow[0]).toMatchObject({ from: 'pm', to: 'dev', content: '任务卡', type: 'delegate', order: 0 });
    expect(s.workflow[1]).toMatchObject({ from: 'dev', to: 'qa', content: '构建产物', order: 1 });
  });

  it('stages_sync 存房间业务阶段映射', () => {
    const s = reduce(initialState(), { type: 'stages_sync', stages: { research: 0, build: 1, review: 2 } });
    expect(s.stages).toEqual({ research: 0, build: 1, review: 2 });
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

  // ── M2-4: 工作流顺序约束 ──────────────────────────────────

  it('M2-4: workflow 顺序约束 — 前序交接未完成时后序 delegate 不渲染边', () => {
    let s = reduce(initialState(), {
      type: 'workflow_sync',
      edges: [
        { source: 'pm', target: 'dev', channel: '需求文档' },   // order=0
        { source: 'dev', target: 'qa', channel: '构建产物' },    // order=1
      ],
    });
    // dev 尝试先 delegate 给 qa（跳过 pm→dev），应被顺序约束阻止
    s = reduce(s, { type: 'step', agentActions: { dev: { action: 'delegate', target: 'qa' } } });
    expect(s.edges.filter((e) => e.kind === 'delegate')).toHaveLength(0);
    expect(s.workflowProgress).toBe(0); // 未推进

    // pm delegate 给 dev（order=0，正确顺序），应渲染并推进
    s = reduce(s, { type: 'step', agentActions: { pm: { action: 'delegate', target: 'dev' } } });
    expect(s.edges.filter((e) => e.kind === 'delegate')).toHaveLength(1);
    expect(s.workflowProgress).toBe(1);

    // 现在 dev delegate 给 qa（order=1），应渲染并推进
    s = reduce(s, { type: 'step', agentActions: { dev: { action: 'delegate', target: 'qa' } } });
    expect(s.edges.filter((e) => e.kind === 'delegate')).toHaveLength(2);
    expect(s.workflowProgress).toBe(2);
  });

  it('M2-4: 无 workflow 边时不受顺序约束（自由模式）', () => {
    const s = reduce(initialState(), {
      type: 'step', agentActions: { dev: { action: 'delegate', target: 'qa' } },
    });
    expect(s.edges.filter((e) => e.kind === 'delegate')).toHaveLength(1);
  });

  it('M2-4: 串行 vs 并行拓扑产生可区分的递交序列', () => {
    // 串行: a→b→c
    const serial = reduce(initialState(), {
      type: 'workflow_sync',
      edges: [
        { source: 'a', target: 'b' },
        { source: 'b', target: 'c' },
      ],
    });
    let s1 = reduce(serial, { type: 'step', agentActions: { a: { action: 'delegate', target: 'b' } } });
    s1 = reduce(s1, { type: 'step', agentActions: { b: { action: 'delegate', target: 'c' } } });
    const serialEdges = s1.edges.filter((e) => e.kind === 'delegate');

    // 并行: a→b, a→c (a 同时 delegate 给 b 和 c)
    const parallel = reduce(initialState(), {
      type: 'workflow_sync',
      edges: [
        { source: 'a', target: 'b' },
        { source: 'a', target: 'c' },
      ],
    });
    let s2 = reduce(parallel, { type: 'step', agentActions: { a: { action: 'delegate', target: 'b' } } });
    s2 = reduce(s2, { type: 'step', agentActions: { a: { action: 'delegate', target: 'c' } } });
    const parallelEdges = s2.edges.filter((e) => e.kind === 'delegate');

    // 串行: 两条边按序推进，都被渲染
    expect(serialEdges.length).toBe(2);
    expect(serialEdges[0].from).toBe('a');
    expect(serialEdges[1].from).toBe('b');
    // 并行: 两条边都来自 a，第二条也应被渲染（同一 agent 的不同 target）
    expect(parallelEdges.length).toBe(2);
    expect(parallelEdges.every((e) => e.from === 'a')).toBe(true);
  });

  // ── M3-1: 显式工作流图 ────────────────────────────────────

  it('M3-1: workflow_graph_sync 构建节点(角色·技能·模型档)+边', () => {
    const s = reduce(initialState(), {
      type: 'workflow_graph_sync',
      nodes: [
        { id: 'pm', role: 'project_manager', skills: ['planning'], model_tier: 'standard' },
        { id: 'dev', role: 'developer', skills: ['python', 'terraform'], model_tier: 'economy' },
      ],
      edges: [
        { source: 'pm', target: 'dev', channel: '需求文档', message_type: 'delegate' },
      ],
    });
    expect(s.workflowGraph.nodes.length).toBe(2);
    expect(s.workflowGraph.nodes[0]).toMatchObject({ id: 'pm', role: 'project_manager', modelTier: 'standard' });
    expect(s.workflowGraph.nodes[0].skills).toEqual(['planning']);
    expect(s.workflowGraph.edges.length).toBe(1);
    expect(s.workflowGraph.edges[0]).toMatchObject({ from: 'pm', to: 'dev', content: '需求文档' });
  });

  it('M3-1: 两种拓扑(串行 vs 并行+Review)在工作流图上可区分', () => {
    // 串行拓扑
    const serial = reduce(initialState(), {
      type: 'workflow_graph_sync',
      nodes: [{ id: 'a' }, { id: 'b' }, { id: 'c' }],
      edges: [{ source: 'a', target: 'b' }, { source: 'b', target: 'c' }],
    });
    // 并行+Review 拓扑
    const parallel = reduce(initialState(), {
      type: 'workflow_graph_sync',
      nodes: [{ id: 'a' }, { id: 'b' }, { id: 'c' }, { id: 'r' }],
      edges: [
        { source: 'a', target: 'b' }, { source: 'a', target: 'c' },
        { source: 'b', target: 'r' }, { source: 'c', target: 'r' },
      ],
    });
    // 串行: 2 条边，a→b→c
    expect(serial.workflowGraph.edges.length).toBe(2);
    expect(serial.workflowGraph.edges[1].from).toBe('b');
    // 并行+Review: 4 条边，b 和 c 都指向 r
    expect(parallel.workflowGraph.edges.length).toBe(4);
    const reviewEdges = parallel.workflowGraph.edges.filter((e) => e.to === 'r');
    expect(reviewEdges.length).toBe(2);
  });

  // ── M3-2: 协作热度面板联动工作流图 ────────────────────────

  it('M3-2: highlight_workflow_edge 设置高亮边', () => {
    let s = reduce(initialState(), {
      type: 'workflow_graph_sync',
      nodes: [{ id: 'a' }, { id: 'b' }],
      edges: [{ source: 'a', target: 'b' }],
    });
    expect(s.workflowGraph.highlightedEdge).toBeNull();
    s = reduce(s, { type: 'highlight_workflow_edge', edgeKey: 'a→b' });
    expect(s.workflowGraph.highlightedEdge).toBe('a→b');
  });

  // ── M4-4: 竞标画中画 ──────────────────────────────────────

  it('M4-4: bidding_sync 同步候选排名与胜者', () => {
    const s = reduce(initialState(), {
      type: 'bidding_sync',
      active: true,
      candidates: [
        { candidate_id: 'c0', operator: 'C0', operator_desc: '基线', quality_score: 0.92, token_consumed: 1000, rank: 2 },
        { candidate_id: 'c1', operator: 'R5', operator_desc: '降档', quality_score: 0.91, token_consumed: 700, rank: 1 },
      ],
      winner_id: 'c1',
      ranking: [],
    });
    expect(s.biddingView.active).toBe(true);
    expect(s.biddingView.candidates.length).toBe(2);
    expect(s.biddingView.candidates[0]).toMatchObject({ id: 'c0', operator: 'C0', score: 0.92, token: 1000 });
    expect(s.biddingView.winnerId).toBe('c1');
  });
});
