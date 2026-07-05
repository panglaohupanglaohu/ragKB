/**
 * office-boot.js — 办公室场景接线 (P7-1)
 * 激活: URL 带 ?office3d=1（feature flag，默认关闭，旧场景零影响）。
 * 接管策略: 重载 window._dt3dBuildRoom；rest-area(枯山水·Owner 隐藏款) 仍委托旧实现，原样保留。
 * 数据源: OfficeState 单一 store；输入 = 位置轮询 + handleTrialEvent 钩子 + transitionTrialStatus 钩子。
 */
import { createStore, collabStats, setBreakTimeScale } from './office-state.js';
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
  // 尊重左栏团队选择: 只显示选中团队的成员；成员级筛选经 OfficeAPI.setRoster 覆盖。
  let memberFilter = null;   // Set<agentId> | null（null = 不做成员级过滤）
  let lastRosterKey = '';
  function syncPositions() {
    try {
      const S = window.S || {};
      const positions = S.positions || {};
      const selected = Array.isArray(S.selectedTeams) ? S.selectedTeams.filter(Boolean) : [];
      const teams = (S.teams || []).filter(
        (t) => !selected.length || selected.includes(t.team_id || t.id)
      );
      let roster = [];
      teams.forEach((t) => (t.agents || []).forEach((a) => {
        const entry = { id: a.agent_id || a.id, name: a.name, role: a.role, team: t.team_id || t.id || '' };
        // 宠物团队特殊标记
        const tid = t.team_id || t.id || '';
        if (tid === 'pet_squad') {
          entry._isCat = a.agent_id === 'xiaohu_cat' || a.id === 'xiaohu_cat';
          entry._isMouse = a.agent_id === 'squeak_mouse' || a.id === 'squeak_mouse';
          entry.skills = a.skills || [];
        }
        roster.push(entry);
      }));
      if (memberFilter) roster = roster.filter((a) => memberFilter.has(a.id));
      // 演练时只显示所选团队的正式成员——不并入「增援」等临时注入的 agent。
      if (roster.length) {
        const key = roster.map((a) => a.id).sort().join(',');   // 顺序无关: 成员集不变不触发重置
        if (key !== lastRosterKey) {          // 花名册变化才整体重置（含移除未选团队成员）
          lastRosterKey = key;
          store.dispatch({ type: 'team_reset', agents: roster });
        }
        const ids = new Set(roster.map((a) => a.id));
        for (const [agentId, room] of Object.entries(positions)) {
          if (ids.has(agentId)) store.dispatch({ type: 'position', agentId, room });
        }
      }
      syncScenarioStages();       // M2-5: 选中场景 → 阶段分区带
    } catch (e) { /* 只读同步失败不致命 */ }
  }
  // M2-5: 从当前选中场景 spec 的 world.rooms[].stage 派发业务阶段映射（幂等，变化才派发）
  let lastStageKey = '';
  function syncScenarioStages() {
    const rooms = (window._sx && _sx.scenarioSpec && _sx.scenarioSpec.world && _sx.scenarioSpec.world.rooms) || [];
    const stages = {};
    rooms.forEach((r) => { if (r && r.room_id != null) stages[r.name || r.room_id] = Number(r.stage || 0); });
    const key = Object.entries(stages).map(([k, v]) => k + ':' + v).sort().join(',');
    if (key === lastStageKey) return;
    lastStageKey = key;
    store.dispatch({ type: 'stages_sync', stages });
  }
  setInterval(syncPositions, 2000);

  // ── 猫气泡 = 演练解说员（优先级: 种子技能注入 > 运行中的仿真参数 > 当前演练任务） ──
  const MODE_LABEL = { what_if: 'What-if', multi_branch: '并行', parallel: '并行', evolutionary: '演化' };
  let seedNote = null;          // {text, until} 种子技能注入的置顶提示（45s）
  function catContextNote() {
    if (seedNote && Date.now() < seedNote.until) return seedNote.text;
    const sx = window._sx || {};
    if (sx.simRunning) {
      const modeEl = document.querySelector('input[name="secs-mode"]:checked');
      const mode = MODE_LABEL[(modeEl && modeEl.value) || (window._DTS && window._DTS.selectedMode)] || 'What-if';
      const steps = (document.getElementById('secs-steps') || {}).value || sx.maxSteps || 150;
      const speed = (document.getElementById('secs-speed-slider') || {}).value || 10;
      return `🐈 仿真参数\n模式 ${mode} · 步数 ${steps} · 加速 ${speed}x`;
    }
    // 任务来源链: SECS 任务选择(_selectedTaskGoal) > 场景名 > 任务下拉 > 导演台输入框 > 场景id
    const selOpt = (el) => (el && el.selectedIndex > 0
      ? el.options[el.selectedIndex].textContent.trim() : '');
    const task = (window._selectedTaskGoal && window._selectedTaskGoal.name)
      || (sx.scenarioSpec && sx.scenarioSpec.name)
      || selOpt(document.getElementById('secs-task-select'))
      || ((document.getElementById('dp-task-name') || {}).value || '').trim()
      || (sx.scenarioId ? String(sx.scenarioId) : '');
    return task ? `🐈 演练任务\n${task}` : '';
  }
  setInterval(() => {
    store.dispatch({ type: 'cat_say', text: catContextNote() });
  }, 2000);
  // 种子技能注入 → 气泡置顶显示注入的技能名（沙箱进料 · 💉 注入按钮）
  document.addEventListener('click', (e) => {
    const btn = e.target && e.target.closest && e.target.closest('#btn-inject-skill');
    if (!btn) return;
    const sel = document.getElementById('skill-inject-select');
    const name = sel && sel.selectedIndex > 0
      ? sel.options[sel.selectedIndex].textContent.trim() : '';
    if (name) {
      seedNote = { text: `🐈 种子技能已注入\n💉 ${name}`, until: Date.now() + 45e3 };
      store.dispatch({ type: 'cat_say', text: seedNote.text });
    }
  }, true);

  // 混沌加入/离开即时反映到办公室（不等 2s 轮询）
  for (const fn of ['_dt2dChaosJoin', '_dt2dChaosLeave', '_dt2dChaosReset']) {
    const orig = window[fn];
    if (typeof orig === 'function') {
      window[fn] = function (...args) {
        const r = orig.apply(this, args);
        try { syncPositions(); } catch (e) { /* 非致命 */ }
        return r;
      };
    }
  }
  setInterval(() => store.dispatch({ type: 'tick', dt: 1 }), 1000);

  // ── 作息调度（错峰 + 排队） ──
  // 频率: 咖啡≈1h / 马桶≈2h / 跑步机≈6h。停留与排队由 store 的设施占位模型管理
  //（咖啡 1min、跑步机 5min、马桶 5min，容量 1，FIFO）。
  // 错峰算法: 团队内相位均匀分布——同队第 i 个成员(共 N 人)的首次到点
  //   due = now + mean × (i+0.5)/N × jitter(0.9~1.1)
  // 之后 due += mean × (0.8~1.2)。再加团队并发闸: 同队已有人在该设施(占用或排队)则顺延，
  // 保证「一个团队不会集体去咖啡机」。
  // ?breakspeed=60 → 时间加速 60 倍（演示/调试排队行为）: 频率与停留时长同比缩短
  const SPEED = Math.max(1, Number(new URLSearchParams(location.search).get('breakspeed')) || 1);
  setBreakTimeScale(SPEED);
  const BREAK_MEAN = {
    coffee: 3600e3 / SPEED, toilet: 7200e3 / SPEED, treadmill: 21600e3 / SPEED,
  };
  const nextBreakAt = {};   // agentId -> {facility: dueTs}
  let staggerKey = '';
  function initStagger(state) {
    const byTeam = {};
    for (const a of Object.values(state.agents)) {
      (byTeam[a.team || '_'] = byTeam[a.team || '_'] || []).push(a.id);
    }
    const now = Date.now();
    for (const members of Object.values(byTeam)) {
      members.sort();
      members.forEach((id, i) => {
        nextBreakAt[id] = {};
        for (const [fac, mean] of Object.entries(BREAK_MEAN)) {
          nextBreakAt[id][fac] = now + mean * ((i + 0.5) / members.length) * (0.9 + Math.random() * 0.2);
        }
      });
    }
  }
  function teammateBusyAt(state, agent, facility) {
    const f = state.facilities[facility];
    if (!f) return false;
    const ids = [f.occupant, ...f.queue].filter(Boolean);
    return ids.some((id) => id !== agent.id && (state.agents[id] || {}).team === agent.team);
  }
  setInterval(() => store.dispatch({ type: 'break_tick', now: Date.now() }),
    Math.max(1000, 5e3 / SPEED));
  setInterval(() => {
    const state = store.getState();
    const rosterKey = Object.keys(state.agents).sort().join(',');
    if (rosterKey !== staggerKey) { staggerKey = rosterKey; initStagger(state); }
    if (state.mirror || state.meeting.active) return;   // 孪生演练/开会时不摸鱼
    const now = Date.now();
    for (const agent of Object.values(state.agents)) {
      if (!nextBreakAt[agent.id] || agent.activity !== 'working') continue;
      for (const fac of Object.keys(BREAK_MEAN)) {
        if (now < nextBreakAt[agent.id][fac]) continue;
        if (teammateBusyAt(state, agent, fac)) {
          // 团队并发闸: 同队有人在此设施 → 顺延一个错峰间隔
          nextBreakAt[agent.id][fac] = now + BREAK_MEAN[fac] * 0.15 * (0.8 + Math.random() * 0.4);
          continue;
        }
        nextBreakAt[agent.id][fac] = now + BREAK_MEAN[fac] * (0.8 + Math.random() * 0.4);
        store.dispatch({ type: 'break_request', agentId: agent.id, facility: fac, now });
        break;   // 一次只去一个地方
      }
    }
  }, Math.max(1000, 20e3 / SPEED));

  // ── 输入 2: 孪生事件钩子（step / 讨论 / 状态机），不改旧函数行为 ──
  // 孪生副本 → 真身对齐: SSE 的 agent_actions 以 twin_id 为键，
  // 用事件携带的 twin_agents 映射回真身 agent_id，办公室里的人才对得上号。
  // 两条演练通道共用: 试炼导演台(handleTrialEvent) + SECS 面板 SSE(secs-core 调 ingestStep)。
  function ingestStep(ev) {
    try {
      const raw = ev.agent_actions || (ev.data && ev.data.agent_actions) || {};
      const twinMap = ev.twin_agents || (ev.data && ev.data.twin_agents) || {};
      // 只驱动当前花名册内的 agent：仿真自带的外部/临时 agent（不在所选团队）忽略，
      // 否则 step reducer 会为其新建 figure → 自动运行时「弹出一堆 agent」。
      const known = store.getState().agents;
      const mapped = {};
      for (const [k, v] of Object.entries(raw)) {
        const realId = twinMap[k] || k;
        if (!known[realId]) continue;
        const act = typeof v === 'string' ? { action: v } : { ...(v || {}) };
        if (act.target) act.target = twinMap[act.target] || act.target;
        if (act.to) act.to = twinMap[act.to] || act.to;
        mapped[realId] = act;
      }
      store.dispatch({ type: 'step', agentActions: mapped });
      // 评分波动追踪 → 猫评价
      if (typeof ev.global_reward === 'number') trackReward(ev.global_reward);
    } catch (e) { /* 观测层不阻塞业务 */ }
  }
  const legacyHandle = window.handleTrialEvent;
  window.handleTrialEvent = function (ev) {
    if (ev && ev.type === 'step') ingestStep(ev);
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
  // 猫 TTS: 14 岁女声（高 pitch）
  let _catTtsBusy = false;
  function catSpeak(text) {
    if (_catTtsBusy) return;
    _catTtsBusy = true;
    if (window.speechSynthesis) speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = 'zh-CN';
    utt.rate = 1.1;
    utt.pitch = 1.8;   // 高音调 = 少女声
    utt.volume = 0.9;
    // 优先选择女声
    const voices = speechSynthesis.getVoices().filter(v => v.lang && v.lang.startsWith('zh'));
    const femaleKw = ['female', 'xiaoxiao', 'xiaoyi', 'wanlong', 'tingting', 'mei', 'hui', 'ting'];
    const fv = voices.find(v => femaleKw.some(k => v.name.toLowerCase().includes(k)));
    if (fv) utt.voice = fv;
    utt.onend = () => { _catTtsBusy = false; };
    utt.onerror = () => { _catTtsBusy = false; };
    speechSynthesis.speak(utt);
  }

  // 猫对话框
  let catDialogEl = null;
  function showCatDialog() {
    if (catDialogEl) { catDialogEl.remove(); catDialogEl = null; return; }
    catDialogEl = document.createElement('div');
    catDialogEl.style.cssText = 'position:absolute;bottom:60px;left:50%;transform:translateX(-50%);width:380px;background:rgba(255,255,255,0.97);border:2px solid #e8a020;border-radius:16px;padding:16px;z-index:10;box-shadow:0 8px 32px rgba(0,0,0,0.15);font-family:sans-serif';
    catDialogEl.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:24px">🐱</span>
        <span style="font-size:14px;font-weight:700;color:#e8a020">小虎</span>
        <span style="font-size:10px;color:#9aa1ab">叛逆高中生·办公室巡检猫</span>
        <button id="cat-dialog-close" style="margin-left:auto;border:none;background:none;font-size:18px;cursor:pointer;color:#9aa1ab">✕</button>
      </div>
      <div id="cat-dialog-reply" style="font-size:13px;color:#3b4048;line-height:1.6;min-height:40px;margin-bottom:10px">喵~ 你叫我？有什么事尽管问吧！</div>
      <div style="display:flex;gap:8px">
        <input id="cat-dialog-input" type="text" placeholder="问小虎一个问题…" style="flex:1;padding:8px 12px;border:1px solid #e2e5e9;border-radius:8px;font-size:13px;outline:none">
        <button id="cat-dialog-send" style="padding:8px 16px;background:#e8a020;color:white;border:none;border-radius:8px;font-size:13px;cursor:pointer;font-weight:600">问</button>
      </div>`;
    container.appendChild(catDialogEl);
    const closeBtn = catDialogEl.querySelector('#cat-dialog-close');
    closeBtn.onclick = () => { catDialogEl.remove(); catDialogEl = null; };
    const input = catDialogEl.querySelector('#cat-dialog-input');
    const sendBtn = catDialogEl.querySelector('#cat-dialog-send');
    const replyEl = catDialogEl.querySelector('#cat-dialog-reply');
    function askCat() {
      const q = input.value.trim();
      if (!q) return;
      input.value = '';
      // 猫的叛逆高中生人设回答（非硬编码，基于关键词生成）
      const ql = q.toLowerCase();
      let reply = '';
      if (/评分|分数|score/.test(ql)) {
        reply = '喵~ 你问我评分？哼，那些数字嘛…反正我觉得还可以做得更好。不过具体多少分你自己看面板啦，我又不是计算器！';
      } else if (/协作|合作|collab/.test(ql)) {
        reply = '喵~ 协作？我看他们整天传文件传得挺欢的。不过谁偷懒了我可一清二楚——我巡逻的时候什么都看在眼里！';
      } else if (/你是谁|介绍|who/.test(ql)) {
        reply = '我是小虎！办公室巡检猫，兼职抓老鼠。别看我只是一只猫，我的技能可多了——PM的活儿我都会！当然，我本质是个叛逆高中生，别想命令我~';
      } else if (/老鼠|mouse/.test(ql)) {
        reply = '喵！老鼠？在哪在哪？！那家伙整天在办公室窜来窜去，迟早被我逮到！';
      } else if (/你好|hi|hello/.test(ql)) {
        reply = '喵~ 你好呀。来找小虎聊天？难得有人不盯着屏幕看…说吧，什么事？';
      } else {
        reply = '喵？你说' + q.slice(0, 20) + '…？这个嘛，让我想想…哼，本猫觉得这事儿得看情况。你先把演练跑完再说吧！';
      }
      replyEl.textContent = reply;
      catSpeak(reply);
      sceneApi.showCatBubble('🐱 ' + reply.slice(0, 40) + '…');
    }
    sendBtn.onclick = askCat;
    input.onkeydown = (e) => { if (e.key === 'Enter') askCat(); };
    input.focus();
  }

  // 评分波动追踪
  let _lastReward = null;
  function trackReward(reward) {
    if (typeof reward !== 'number') return;
    if (_lastReward !== null) {
      sceneApi.onRewardUpdate(reward, _lastReward);
    }
    _lastReward = reward;
  }

  window.OfficeAPI = {
    dispatch: store.dispatch,
    getState: store.getState,
    ingestStep,
    collabStats: (n) => collabStats(store.getState(), n),
    setRoster(agentIds) {
      memberFilter = agentIds && agentIds.length ? new Set(agentIds) : null;
      lastRosterKey = '';
      syncPositions();
    },
    syncWorkflow(edges) { store.dispatch({ type: 'workflow_sync', edges: edges || [] }); },
    syncStages(map) { store.dispatch({ type: 'stages_sync', stages: map || {} }); },
    meeting(active, speakerId, boardLine, participantIds) {
      window.OfficeAPI._speakerId = speakerId || null;
      store.dispatch({ type: 'discussion', active, speakerId, boardLine, participantIds });
    },
    onCatClick: showCatDialog,
    onCatComment: (comment) => { catSpeak(comment); },
    trackReward,
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
