/**
 * office-state.js — 统一办公室场景的单一数据源 (P7-1)
 * 纯函数 reducer，无 three.js 依赖，可单测。
 * 设计: docs/unified-office-3d-design.md §4
 */

export const ACTIVITIES = ['working', 'meeting', 'treadmill', 'coffee', 'toilet', 'idle', 'zen'];

// 共享设施: 容量均为 1，后到者 FIFO 排队。停留时长(ms): 咖啡 1min、跑步机 5min、马桶 5min。
export const FACILITIES = ['coffee', 'treadmill', 'toilet'];
export const DWELL_MS = { coffee: 60e3, treadmill: 300e3, toilet: 300e3 };

/** 调试用时间加速（?breakspeed=60）: 停留时长同比例缩短，便于观察排队行为。 */
export function setBreakTimeScale(factor) {
  const f = Math.max(1, Number(factor) || 1);
  DWELL_MS.coffee = 60e3 / f;
  DWELL_MS.treadmill = 300e3 / f;
  DWELL_MS.toilet = 300e3 / f;
}

// 房间语义 → 办公室活动映射（兼容旧 ROOM_MAP 的 6 房间）
const ROOM_ACTIVITY = {
  'council-hall': 'meeting',
  'council': 'meeting',
  'extraction-lab': 'treadmill',
  'workshop': 'working',
  'knowledge-base': 'working',
  'training-ground': 'working',
  'rest-area': 'coffee',
};

const EDGE_TTL = 6;          // 协作光线存活秒数
const EDGE_MAX = 40;         // 同屏最多光线数

export function initialState() {
  return {
    agents: {},        // id -> {id,name,role,collar,activity,deskIndex,layer}
    edges: [],         // {from,to,kind,ttl}
    collab: {},        // "from→to" -> count（协作热度，考察协作能力的核心数据）
    meeting: { active: false, speakerId: null, boardLines: [] },
    mirror: false,     // 孪生镜像层
    catNote: '',       // 猫头顶气泡: 演练任务 / 仿真参数 / 种子技能注入
    workflow: [],      // M2-4: 工作流边 [{from,to,content,type,weight,order}]（结构化交接顺序+内容）
    workflowProgress: 0, // M2-4: 当前已推进到第几条边（顺序约束：前序交接未完成不得触发后序）
    workflowGraph: { nodes: [], edges: [], highlightedEdge: null }, // M3-1: 显式工作流图（节点=角色·技能·模型档，边=依赖·内容）
    biddingView: { active: false, candidates: [], winnerId: null, ranking: [] }, // M4-4: 竞标画中画
    stages: {},        // M2-5: 房间业务阶段 {room_id: stage}
    facilities: {      // facility -> {occupant, until, queue[]}
      coffee: { occupant: null, until: 0, queue: [] },
      treadmill: { occupant: null, until: 0, queue: [] },
      toilet: { occupant: null, until: 0, queue: [] },
    },
    seq: 0,
  };
}

const COLLARS = [0xE04040, 0x7C4DFF, 0x2BB8A8, 0xE8A020, 0x4D9DE0, 0xD05CB0];

function ensureAgent(state, id, extra) {
  if (!state.agents[id]) {
    // 取最小空闲座位号（与 team_reset 的粘性座位语义一致，避免编号碰撞）
    const usedDesks = new Set(Object.values(state.agents).map((a) => a.deskIndex));
    let deskIndex = 0;
    while (usedDesks.has(deskIndex)) deskIndex += 1;
    state.agents[id] = {
      id,
      name: id,
      role: '',
      team: '',
      collar: COLLARS[deskIndex % COLLARS.length],
      activity: 'working',   // 默认在工位落座干活
      deskIndex,
      layer: 'prod',
      lastAction: '',        // 最近一次 twin 动作（claim_task/execute_skill/delegate/...）
      skillUsed: '',         // execute_skill 的 skill_used
      task: '',              // 当前认领/执行的任务
      // ND-5.2: eco 模式生境字段
      health: 100,           // 血量（0~health_max）
      survivalTicks: 0,      // 生存时长
      ecoAlive: true,        // 是否存活
    };
  }
  if (extra) Object.assign(state.agents[id], extra);
  return state.agents[id];
}

function addEdge(state, from, to, kind) {
  if (!from || !to || from === to) return;
  state.edges.push({ from, to, kind: kind || 'help', ttl: EDGE_TTL });
  if (state.edges.length > EDGE_MAX) state.edges.splice(0, state.edges.length - EDGE_MAX);
  const key = from + '→' + to;
  state.collab[key] = (state.collab[key] || 0) + 1;
}

/** 纯 reducer: (state, event) → newState（浅拷贝顶层，内层原位修改副本） */
export function reduce(prev, event) {
  const state = {
    ...prev,
    agents: { ...prev.agents },
    edges: prev.edges.slice(),
    collab: { ...prev.collab },
    meeting: { ...prev.meeting, boardLines: prev.meeting.boardLines.slice() },
    facilities: Object.fromEntries(
      Object.entries(prev.facilities).map(([k, f]) => [k, { ...f, queue: f.queue.slice() }])
    ),
    seq: prev.seq + 1,
  };
  // agents 深一层拷贝，保证 reducer 纯度
  for (const k of Object.keys(state.agents)) state.agents[k] = { ...state.agents[k] };

  switch (event.type) {
    case 'team_sync': {
      (event.agents || []).forEach((a, i) => {
        ensureAgent(state, a.id, {
          name: a.name || a.id,
          role: a.role || '',
          team: a.team || '',
          collar: a.collar != null ? a.collar : COLLARS[i % COLLARS.length],
        });
      });
      break;
    }
    case 'team_reset': {
      // 花名册整体替换（团队/成员筛选）：只保留 roster 内的 Agent。
      // 座位语义 = 保序前移压缩:
      //   - 同一批人顺序抖动 → 映射恒等，无人移动（不玩抢椅子）；
      //   - 有人离编 → 保留者按原座位相对次序整体前移补位（只向前、不互换），
      //     避免幽灵成员清除后 7 个人孤零零坐在第 20+ 号后排桌。
      const retained = (event.agents || [])
        .filter((a) => state.agents[a.id])
        .sort((x, y) => state.agents[x.id].deskIndex - state.agents[y.id].deskIndex);
      const deskMap = {};
      retained.forEach((a, i) => { deskMap[a.id] = i; });
      let nextFree = retained.length;
      const roster = {};
      (event.agents || []).forEach((a, i) => {
        const prev = state.agents[a.id];
        roster[a.id] = prev
          ? {
              ...prev, name: a.name || prev.name, role: a.role || prev.role,
              team: a.team || prev.team, deskIndex: deskMap[a.id],
              // v2.4 修复: noBreaks 此前只对新建 agent 生效，重跑 eco 演练时 roster 已存在，
              // noBreaks:true 被 ...prev 的旧值(false)覆盖 → 演练结束作息欠账放行 → 全员涌向设施排成一列跑出镜头。
              // 事件显式携带 noBreaks 时对留任 agent 也应用之。
              noBreaks: event.noBreaks != null ? !!event.noBreaks : prev.noBreaks,
            }
          : {
              id: a.id, name: a.name || a.id, role: a.role || '', team: a.team || '',
              collar: COLLARS[i % COLLARS.length], activity: 'working',
              deskIndex: nextFree++, layer: state.mirror ? 'mirror' : 'prod',
              // v2.4: 默认允许作息调度；eco 种群由 _seedSceneRoster 显式置 true 跳过设施排队
              noBreaks: !!event.noBreaks,
            };
      });
      state.agents = roster;
      state.edges = state.edges.filter((e) => roster[e.from] && roster[e.to]);
      for (const f of Object.values(state.facilities)) {   // 清理离编成员的占位与排队
        if (f.occupant && !roster[f.occupant]) f.occupant = null;
        f.queue = f.queue.filter((id) => roster[id]);
      }
      break;
    }
    case 'position': {
      const agent = ensureAgent(state, event.agentId);
      agent.activity = ROOM_ACTIVITY[event.room] || 'working';
      break;
    }
    case 'activity': {
      if (ACTIVITIES.includes(event.activity)) {
        ensureAgent(state, event.agentId).activity = event.activity;
      }
      break;
    }
    case 'step': {
      // 孪生仿真步: agent_actions → 状态/协作光线（协作能力的观测点）
      // 对齐 twin 动作词表 (llm_decision.py):
      //   claim_task | work_on_task | execute_skill | offer_help | delegate | communicate | idle
      const actions = event.agentActions || {};
      for (const [id, act] of Object.entries(actions)) {
        const agent = ensureAgent(state, id);
        const a = typeof act === 'string' ? { action: act } : (act || {});
        const action = a.action || '';
        const target = a.target || a.to || '';
        agent.lastAction = action;

        // M2-4: 工作流顺序约束 — delegate/communicate 须按 workflow 边顺序推进
        // 前序交接未完成（workflowProgress < edge.order）时，不渲染协作边但仍记录动作
        const _isWorkflowOrdered = () => {
          if (!state.workflow.length) return false;
          return state.workflow.some((w) => w.from === id && (w.to === target || w.to === '*'));
        };
        const _workflowAllows = () => {
          // 无工作流边 → 不约束（自由模式）
          if (!state.workflow.length) return true;
          // 有工作流边但当前 agent/target 不在任何边上 → 不约束
          const relevant = state.workflow.filter((w) => w.from === id);
          if (!relevant.length) return true;
          // 当前 agent 有工作流边 → 检查顺序
          const nextEdge = relevant.find((w) => w.order === state.workflowProgress);
          return !!nextEdge;
        };
        const _advanceWorkflow = () => {
          // 推进到下一条边
          if (state.workflowProgress < state.workflow.length) {
            state.workflowProgress += 1;
          }
        };

        switch (action) {
          case 'offer_help':
            addEdge(state, id, target, 'help');
            agent.activity = 'working';
            break;
          case 'delegate':                                   // 委派：有向，与沟通区分
            if (_workflowAllows()) {
              addEdge(state, id, target, 'delegate');
              _advanceWorkflow();
            }
            agent.activity = 'working';
            break;
          case 'communicate':
            if (target === 'broadcast' || a.broadcast) {       // 广播：无定向目标
              state.edges.push({ from: id, to: '*', kind: 'broadcast', ttl: EDGE_TTL });
              if (state.edges.length > EDGE_MAX) state.edges.splice(0, state.edges.length - EDGE_MAX);
            } else {
              if (_workflowAllows()) {
                addEdge(state, id, target, 'comm');
                _advanceWorkflow();
              }
            }
            agent.activity = 'working';
            break;
          case 'claim_task':
            agent.task = a.task || a.task_id || agent.task || '';
            agent.activity = 'working';
            break;
          case 'execute_skill':
            agent.skillUsed = a.skill_used || a.skill || '';
            agent.activity = 'working';
            break;
          case 'work_on_task':
            if (a.task || a.task_id) agent.task = a.task || a.task_id;
            agent.activity = 'working';
            break;
          case 'disabled':
          case 'rest':
            agent.activity = 'coffee';
            break;
          case 'idle':
            agent.activity = 'idle';
            break;
          default:
            if (action) agent.activity = 'working';
        }
      }
      break;
    }
    case 'discussion': {
      state.meeting.active = !!event.active;
      state.meeting.speakerId = event.speakerId || null;
      if (event.boardLine) {
        state.meeting.boardLines.push(String(event.boardLine).slice(0, 48));
        if (state.meeting.boardLines.length > 8) state.meeting.boardLines.shift();
      }
      if (!event.active) state.meeting.boardLines = [];
      const ids = event.participantIds || Object.keys(state.agents);
      for (const id of ids) {
        const agent = state.agents[id];
        if (agent) agent.activity = event.active ? 'meeting' : 'working';
      }
      break;
    }
    case 'trial_status': {
      // running/evaluating → 镜像层（孪生进行中）；其余回生产层
      state.mirror = event.status === 'running' || event.status === 'evaluating';
      for (const k of Object.keys(state.agents)) {
        state.agents[k].layer = state.mirror ? 'mirror' : 'prod';
      }
      break;
    }
    case 'break_request': {
      // Agent 申请去设施: 空闲即占用（带释放时间戳），有人则 FIFO 排队。
      const f = state.facilities[event.facility];
      const agent = state.agents[event.agentId];
      if (!f || !agent || agent.activity !== 'working') break;
      const now = event.now != null ? event.now : Date.now();
      if (!f.occupant) {
        f.occupant = event.agentId;
        f.until = now + DWELL_MS[event.facility];
      } else if (f.occupant !== event.agentId && !f.queue.includes(event.agentId)) {
        f.queue.push(event.agentId);
      }
      agent.activity = event.facility;
      break;
    }
    case 'break_tick': {
      // 设施推进: 占用者到时释放回工位，队首补位并重新计时。
      const now = event.now != null ? event.now : Date.now();
      for (const [name, f] of Object.entries(state.facilities)) {
        if (f.occupant && now >= f.until) {
          const done = state.agents[f.occupant];
          if (done && done.activity === name) done.activity = 'working';
          f.occupant = null;
          while (f.queue.length) {
            const next = f.queue.shift();
            const na = state.agents[next];
            if (na && na.activity === name) {
              f.occupant = next;
              f.until = now + DWELL_MS[name];
              break;
            }
          }
        }
      }
      break;
    }
    case 'cat_say': {
      state.catNote = String(event.text || '').slice(0, 120);
      break;
    }
    case 'tick': {
      const dt = event.dt || 1;
      state.edges = state.edges
        .map((e) => ({ ...e, ttl: e.ttl - dt }))
        .filter((e) => e.ttl > 0);
      break;
    }
    case 'workflow_sync': {
      // M2-4: 同步工作流拓扑（源→目标 + 传递内容/类型），按给定顺序编号
      state.workflow = (event.edges || []).map((e, i) => ({
        from: e.from || e.source || '',
        to: e.to || e.target || '',
        content: e.content || e.channel || '',
        type: e.type || e.message_type || 'request',
        weight: e.weight != null ? e.weight : 1,
        order: e.order != null ? e.order : i,
      })).filter((e) => e.from && e.to);
      // 重置顺序进度
      state.workflowProgress = 0;
      break;
    }
    case 'stages_sync': {
      // M2-5: 同步房间业务阶段映射 {room_id: stage}
      state.stages = { ...(event.stages || {}) };
      break;
    }
    case 'workflow_graph_sync': {
      // M3-1: 同步显式工作流图（节点=角色·技能·模型档，边=依赖·内容）
      state.workflowGraph = {
        nodes: (event.nodes || []).map((n) => ({
          id: n.id || '',
          role: n.role || '',
          skills: Array.isArray(n.skills) ? n.skills : [],
          modelTier: n.model_tier || n.modelTier || '',
        })),
        edges: (event.edges || state.workflow || []).map((e, i) => ({
          from: e.from || e.source || '',
          to: e.to || e.target || '',
          content: e.content || e.channel || '',
          type: e.type || e.message_type || 'request',
          order: e.order != null ? e.order : i,
        })),
        highlightedEdge: null,
      };
      break;
    }
    case 'highlight_workflow_edge': {
      // M3-2: 协作热度面板点击 → 高亮工作流图对应边
      state.workflowGraph = { ...state.workflowGraph, highlightedEdge: event.edgeKey || null };
      break;
    }
    case 'bidding_sync': {
      // M4-4: 竞标画中画 — 同步候选排名与胜者
      state.biddingView = {
        active: !!event.active,
        candidates: (event.candidates || []).map((c) => ({
          id: c.id || c.candidate_id || '',
          operator: c.operator || '',
          desc: c.desc || c.operator_desc || '',
          score: c.score || c.quality_score || 0,
          token: c.token || c.token_consumed || 0,
          rank: c.rank || 0,
        })),
        winnerId: event.winnerId || event.winner_id || null,
        ranking: event.ranking || [],
      };
      break;
    }
    case 'eco_health': {
      // ND-5.2: eco 演练健康数据 → 更新 agent 血量/生存时长/存活状态
      const updates = event.updates || {};
      for (const [id, data] of Object.entries(updates)) {
        const agent = ensureAgent(state, id);
        if (data.health != null) agent.health = data.health;
        if (data.survivalTicks != null) agent.survivalTicks = data.survivalTicks;
        if (data.alive != null) agent.ecoAlive = data.alive;
      }
      break;
    }
    case 'eco_intent': {
      // 物竞天择 v2 XT-5.2: 回放帧的意图 → 头顶意图符号（🍖觅食/🛡避险/💕求偶/💤静息）
      const updates = event.updates || {};
      for (const [id, intent] of Object.entries(updates)) {
        ensureAgent(state, id).ecoIntent = String(intent || '');
      }
      break;
    }
    case 'eco_signal': {
      // 物竞天择 v2 XT-5.2: 信号协议可视化 — FOOD(淡金弧线)/HELP(红色脉冲)/COURT(粉色)
      // 复用 edges 渲染管线，kind = signal_food | signal_help | signal_court
      const kind = 'signal_' + (event.signal || 'food');
      const from = event.from;
      const to = event.to || '*';
      if (from) {
        state.edges.push({ from, to, kind, ttl: event.ttl != null ? event.ttl : 2 });
        if (state.edges.length > EDGE_MAX) state.edges.splice(0, state.edges.length - EDGE_MAX);
      }
      break;
    }
    case 'eco_mate': {
      // 物竞天择 v2 XT-5.2: 求偶配对成功 → 双亲间粉色光弧 + 新生个体落位
      const { p1, p2, childId, childName } = event;
      if (p1 && p2) {
        state.edges.push({ from: p1, to: p2, kind: 'mate', ttl: 4 });
        if (state.edges.length > EDGE_MAX) state.edges.splice(0, state.edges.length - EDGE_MAX);
      }
      if (childId) {
        ensureAgent(state, childId, {
          name: childName || childId,
          role: 'offspring',
          ecoNewborn: true,
          health: 100,
          survivalTicks: 0,
          ecoAlive: true,
        });
      }
      break;
    }
    case 'eco_reset': {
      // 物竞天择 v2: 回放重播前重置生境字段（血量/意图/存活），移除演练期新生个体
      for (const k of Object.keys(state.agents)) {
        const a = state.agents[k];
        if (a.ecoNewborn) { delete state.agents[k]; continue; }
        a.health = 100; a.survivalTicks = 0; a.ecoAlive = true; a.ecoIntent = '';
        a.activity = 'working';   // 强制回到工位（打断咖啡/厕所/跑步机）
      }
      // 清空所有设施占用和排队——防止 agent 继续往设施跑
      for (const f of Object.values(state.facilities)) {
        f.occupant = null; f.queue = []; f.until = 0;
      }
      state.edges = state.edges.filter((e) => state.agents[e.from] && (e.to === '*' || state.agents[e.to]));
      break;
    }
    case 'eco_predator': {
      // ND-5.2: 捕食压力 → 在目标 agent 上方显示红色警告（3D 连线/光环）
      // 存到 edges 里，kind='predator'，复用现有 edge 渲染管线
      const target = event.target;
      const source = event.source || '__predator__';
      if (target) {
        state.edges.push({ from: source, to: target, kind: 'predator', ttl: 3 });
        if (state.edges.length > EDGE_MAX) state.edges.splice(0, state.edges.length - EDGE_MAX);
      }
      break;
    }
    default:
      break;
  }
  return state;
}

/** 协作热度排行 —— 考察「哪些 Agent 之间的协作是可取的」的数据基础 */
export function collabStats(state, limit) {
  return Object.entries(state.collab)
    .map(([pair, count]) => ({ pair, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit || 5);
}

/** 简易 store */
export function createStore() {
  let state = initialState();
  const listeners = new Set();
  return {
    getState: () => state,
    dispatch(event) {
      state = reduce(state, event);
      listeners.forEach((fn) => { try { fn(state, event); } catch (e) { /* listener 隔离 */ } });
      return state;
    },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}
