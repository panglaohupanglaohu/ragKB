/**
 * office-boot.js — 办公室场景接线 (P7-1)
 * 激活: URL 带 ?office3d=1（feature flag，默认关闭，旧场景零影响）。
 * 接管策略: 重载 window._dt3dBuildRoom；rest-area(枯山水·Owner 隐藏款) 仍委托旧实现，原样保留。
 * 数据源: OfficeState 单一 store；输入 = 位置轮询 + handleTrialEvent 钩子 + transitionTrialStatus 钩子。
 */
import { createStore, collabStats } from './office-state.js';
import { createOfficeScene } from './office-scene.js';

const FLAG_ON = new URLSearchParams(location.search).get('office3d') === '1';

function bootOffice() {
  const container = document.getElementById('env-3d-container');
  const legacyCanvas = document.getElementById('env-3d-canvas');
  if (!container || !legacyCanvas) return;

  // 自有画布，与旧场景画布互斥显示（切枯山水时还原旧画布）
  const canvas = document.createElement('canvas');
  canvas.id = 'office-3d-canvas';
  canvas.style.cssText = 'width:100%;height:100%;display:block';
  container.appendChild(canvas);

  const store = createStore();
  const sceneApi = createOfficeScene(canvas, container);
  store.subscribe((state) => { sceneApi.applyState(state); renderPanel(state); });

  // ── 覆盖层: SIMULATION 徽标 + 协作热度面板（协作能力考察的读数） ──
  const badge = document.createElement('div');
  badge.textContent = 'SIMULATION · 孪生镜像';
  badge.style.cssText = 'position:absolute;top:10px;right:12px;padding:4px 10px;border:1px solid #4d9de0;color:#2b6cb0;background:rgba(230,240,255,.85);font:600 11px/1.6 sans-serif;border-radius:4px;letter-spacing:1px;display:none;pointer-events:none;z-index:5';
  const panel = document.createElement('div');
  panel.style.cssText = 'position:absolute;top:10px;left:12px;min-width:150px;padding:8px 10px;background:rgba(255,255,255,.88);border:1px solid #e2e5e9;border-radius:6px;font:11px/1.7 sans-serif;color:#3b4048;z-index:5';
  if (getComputedStyle(container).position === 'static') container.style.position = 'relative';
  container.appendChild(badge);
  container.appendChild(panel);

  function renderPanel(state) {
    badge.style.display = state.mirror ? 'block' : 'none';
    const stats = collabStats(state, 5);
    panel.innerHTML = '<b style="font-size:11px">协作热度 TOP5</b>' + (stats.length
      ? stats.map((s) => '<div>' + esc(s.pair) + ' <b>×' + s.count + '</b></div>').join('')
      : '<div style="color:#9aa1ab">演练开始后显示 Agent 协作</div>');
  }
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  renderPanel(store.getState());

  // ── 接管 _dt3dBuildRoom：枯山水(rest-area) 委托旧实现，其余房间进办公室 ──
  const legacyBuildRoom = window._dt3dBuildRoom;
  window._dt3dBuildRoom = function (roomId) {
    if (roomId === 'rest-area' && typeof legacyBuildRoom === 'function') {
      canvas.style.display = 'none'; panel.style.display = 'none'; badge.style.display = 'none';
      legacyCanvas.style.display = 'block';
      return legacyBuildRoom(roomId);            // 枯山水原样
    }
    legacyCanvas.style.display = 'none';
    canvas.style.display = 'block'; panel.style.display = 'block';
    const info = document.getElementById('env-3d-info');
    if (info) info.textContent = '▣ 数字办公室 — 全部任务在此进行孪生';
    syncPositions();
  };

  // ── 输入 1: 位置/团队 轮询（window.S 由 secs-core 维护，只读） ──
  function syncPositions() {
    try {
      const S = window.S || {};
      const positions = S.positions || {};
      const teamAgents = [];
      (S.teams || []).forEach((t) => (t.agents || []).forEach((a) =>
        teamAgents.push({ id: a.agent_id || a.id, name: a.name, role: a.role })));
      if (teamAgents.length) store.dispatch({ type: 'team_sync', agents: teamAgents });
      for (const [agentId, room] of Object.entries(positions)) {
        store.dispatch({ type: 'position', agentId, room });
      }
    } catch (e) { /* 只读同步失败不致命 */ }
  }
  setInterval(syncPositions, 2000);
  setInterval(() => store.dispatch({ type: 'tick', dt: 1 }), 1000);

  // ── 输入 2: 孪生事件钩子（step / 讨论 / 状态机），不改旧函数行为 ──
  const legacyHandle = window.handleTrialEvent;
  window.handleTrialEvent = function (ev) {
    try {
      if (ev && ev.type === 'step') {
        store.dispatch({ type: 'step', agentActions: ev.agent_actions || (ev.data && ev.data.agent_actions) || {} });
      }
    } catch (e) { /* 观测层不阻塞业务 */ }
    if (typeof legacyHandle === 'function') return legacyHandle(ev);
  };
  const legacyTransition = window.transitionTrialStatus;
  if (typeof legacyTransition === 'function') {
    window.transitionTrialStatus = function (from, to) {
      const ok = legacyTransition(from, to);
      if (ok) store.dispatch({ type: 'trial_status', status: to });
      return ok;
    };
  }

  // ── 对外 API（后续 P7-3 Plaza 白板接线 / 面板联动使用） ──
  window.OfficeAPI = {
    dispatch: store.dispatch,
    getState: store.getState,
    collabStats: (n) => collabStats(store.getState(), n),
    meeting(active, speakerId, boardLine, participantIds) {
      window.OfficeAPI._speakerId = speakerId || null;
      store.dispatch({ type: 'discussion', active, speakerId, boardLine, participantIds });
    },
    _speakerId: null,
  };

  // 初次进入即渲染办公室
  window._dt3dBuildRoom(window._currentRoomId && window._currentRoomId !== 'rest-area'
    ? window._currentRoomId : 'workshop');
}

function addToggleButton() {
  // 页面内切换入口: 不用手改 URL 就能进办公室视图
  const host = document.getElementById('env-3d-container');
  if (!host) return;
  const btn = document.createElement('button');
  btn.textContent = FLAG_ON ? '↩ 旧版房间视图' : '▣ 办公室视图';
  btn.title = '切换数字办公室 3D（Marvis 风格）';
  btn.style.cssText = 'position:absolute;bottom:10px;right:12px;z-index:6;padding:5px 12px;'
    + 'border:1px solid #cfd4da;border-radius:6px;background:rgba(255,255,255,.9);'
    + 'color:#3b4048;font:600 11px sans-serif;cursor:pointer';
  btn.onclick = () => {
    const url = new URL(location.href);
    if (FLAG_ON) url.searchParams.delete('office3d');
    else url.searchParams.set('office3d', '1');
    location.href = url.toString();
  };
  if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
  host.appendChild(btn);
}

function start() {
  addToggleButton();
  if (FLAG_ON) bootOffice();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start);
} else {
  start();
}
