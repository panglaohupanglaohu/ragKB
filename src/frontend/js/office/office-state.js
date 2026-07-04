/**
 * office-state.js — 统一办公室场景的单一数据源 (P7-1)
 * 纯函数 reducer，无 three.js 依赖，可单测。
 * 设计: docs/unified-office-3d-design.md §4
 */

export const ACTIVITIES = ['working', 'meeting', 'treadmill', 'coffee', 'idle', 'zen'];

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
    seq: 0,
  };
}

const COLLARS = [0xE04040, 0x7C4DFF, 0x2BB8A8, 0xE8A020, 0x4D9DE0, 0xD05CB0];

function ensureAgent(state, id, extra) {
  if (!state.agents[id]) {
    const deskIndex = Object.keys(state.agents).length;
    state.agents[id] = {
      id,
      name: id,
      role: '',
      collar: COLLARS[deskIndex % COLLARS.length],
      activity: 'idle',
      deskIndex,
      layer: 'prod',
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
          collar: a.collar != null ? a.collar : COLLARS[i % COLLARS.length],
        });
      });
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
      const actions = event.agentActions || {};
      for (const [id, act] of Object.entries(actions)) {
        const agent = ensureAgent(state, id);
        const a = typeof act === 'string' ? { action: act } : (act || {});
        if (a.action === 'offer_help' || a.action === 'communicate' || a.action === 'delegate') {
          addEdge(state, id, a.target || a.to, a.action === 'offer_help' ? 'help' : 'comm');
          agent.activity = 'working';
        } else if (a.action === 'disabled' || a.action === 'rest') {
          agent.activity = 'coffee';
        } else if (a.action) {
          agent.activity = 'working';
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
    case 'tick': {
      const dt = event.dt || 1;
      state.edges = state.edges
        .map((e) => ({ ...e, ttl: e.ttl - dt }))
        .filter((e) => e.ttl > 0);
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
