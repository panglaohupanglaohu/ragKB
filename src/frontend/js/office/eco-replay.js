/**
 * eco-replay.js — 物竞天择生境演练剧场回放引擎 (v2 XT-5.1)
 *
 * 输入: eco_drill 返回的 timeline {steps:[stepSummary], epochs:[epochRec]}
 * 输出: 按可调速度逐帧驱动
 *   - OfficeAPI.dispatch(eco_health / eco_intent / eco_signal / eco_predator / eco_mate / cat_say)
 *   - onFrame(step, index, total) 回调 → 生境控制台种群面板刷新
 *   - onEpoch(epochRec) 回调 → 世代曲线/谱系追加
 *
 * 纯逻辑（定时器可注入），可 vitest 单测。经典脚本（非 module）：挂 window.createEcoReplay。
 */
(function (root) {
  'use strict';

  var SPEEDS = [1, 4, 16];
  var BASE_FRAME_MS = 500;   // 1x 时每帧间隔

  function createEcoReplay(timeline, opts) {
    opts = opts || {};
    var steps = (timeline && timeline.steps) || [];
    var epochs = (timeline && timeline.epochs) || [];
    var dispatch = opts.dispatch
      || (root.OfficeAPI && root.OfficeAPI.dispatch)
      || function () {};
    var onFrame = opts.onFrame || function () {};
    var onEpoch = opts.onEpoch || function () {};
    var setTimer = opts.setTimer || function (fn, ms) { return setTimeout(fn, ms); };
    var clearTimer = opts.clearTimer || function (h) { clearTimeout(h); };

    // 世代边界：steps 里带 generation 字段（SSE 直播帧）或按 epochs 均分
    function genOfStep(i) {
      var s = steps[i];
      if (s && s.generation != null) return s.generation;
      if (!epochs.length) return 0;
      return Math.min(epochs.length, Math.floor(i / Math.max(1, steps.length / (epochs.length + 1))));
    }

    var state = {
      index: 0,
      playing: false,
      speed: 1,
      timer: null,
      lastGen: -1,
      done: false,
    };

    function frameDelay() { return BASE_FRAME_MS / state.speed; }

    /** 把一帧 step_summary 翻译成 office store 事件 */
    function emitFrame(step) {
      if (!step) return;
      var actions = step.actions || {};
      var healthUpdates = {};
      var intentUpdates = {};
      var ids = Object.keys(actions);
      for (var i = 0; i < ids.length; i++) {
        var id = ids[i];
        var a = actions[id] || {};
        healthUpdates[id] = {
          health: a.health != null ? a.health : 0,
          survivalTicks: a.survival_ticks || 0,
          alive: (step.deaths || []).indexOf(id) === -1 ? undefined : false,
        };
        if (healthUpdates[id].alive === undefined) delete healthUpdates[id].alive;
        intentUpdates[id] = a.intention || '';
        // 信号 → 弧线（挑一个存活同伴作视觉目标；协议本身是广播）
        var signals = a.signals || [];
        for (var k = 0; k < signals.length; k++) {
          var sig = String(signals[k]);
          var kind = sig.indexOf('FOOD') === 0 ? 'food'
            : sig === 'HELP' ? 'help'
            : sig === 'COURT' ? 'court' : '';
          if (!kind) continue;
          var peer = pickPeer(ids, id);
          if (peer) dispatch({ type: 'eco_signal', signal: kind, from: id, to: peer, ttl: 2 });
        }
        // 分享 → 用既有 help 协作边呈现（利他行为进入协作热度统计）
        // v2.4: 用专用 kind 'signal_help' 代替 'help'，避免触发递文件动画（courier 只跑 help/delegate/comm，不跑 signal_*）
        if (a.shared_to) dispatch({ type: 'eco_signal', signal: 'help', from: id, to: a.shared_to, ttl: 2 });
      }
      dispatch({ type: 'eco_health', updates: healthUpdates });
      dispatch({ type: 'eco_intent', updates: intentUpdates });
      // 死亡帧：标记不再存活
      var deaths = step.deaths || [];
      if (deaths.length) {
        var deadUpd = {};
        for (var d = 0; d < deaths.length; d++) deadUpd[deaths[d]] = { alive: false };
        dispatch({ type: 'eco_health', updates: deadUpd });
      }
      // 捕食事件
      var predated = step.predated || [];
      for (var p = 0; p < predated.length; p++) {
        dispatch({ type: 'eco_predator', target: predated[p] });
      }
    }

    function pickPeer(ids, self) {
      if (!ids || !ids.length) return null;
      // v2.4: 随机挑一个同伴（之前固定返回 ids[0]，导致所有信号线视觉上全部汇到同一个 agent，
      // 用户反馈"全员朝一个方向跑"的视觉错觉其实来自此处的视觉聚合）。
      // 协议本身是广播，挑不同 peer 仅作可视化目标，语义不变。
      const pool = [];
      for (let i = 0; i < ids.length; i++) if (ids[i] !== self) pool.push(ids[i]);
      if (!pool.length) return null;
      return pool[Math.floor(Math.random() * pool.length)];
    }

    /** 世代边界：eco_mate 派发 + 猫播报 */
    function emitEpoch(ep, step) {
      if (!ep) return;
      var offspring = ep.offspring || [];
      var parents = ep.parents || [];
      for (var i = 0; i < offspring.length; i++) {
        dispatch({
          type: 'eco_mate',
          p1: parents[0] || null,
          p2: parents[1] || null,
          childId: offspring[i],
          childName: offspring[i],
        });
      }
      var living = step ? step.living : '?';
      var note = '🐈 第 ' + ep.generation + ' 代 · 存活 ' + living
        + ' · 新生 ' + offspring.length
        + (ep.drift ? ' · ⚡生态位漂移 ' + ep.drift.removed + '→' + ep.drift.added : '');
      dispatch({ type: 'cat_say', text: note });
      onEpoch(ep);
    }

    function tick() {
      state.timer = null;
      if (!state.playing) return;
      if (state.index >= steps.length) {
        state.playing = false;
        state.done = true;
        onFrame(null, steps.length, steps.length);   // 结束帧通知
        return;
      }
      var step = steps[state.index];
      emitFrame(step);
      onFrame(step, state.index, steps.length);
      // 世代边界检测
      var gen = genOfStep(state.index);
      if (gen !== state.lastGen) {
        if (state.lastGen >= 0 && epochs[state.lastGen]) emitEpoch(epochs[state.lastGen], step);
        state.lastGen = gen;
      }
      state.index += 1;
      if (state.index >= steps.length) {
        // 收尾：补发最后一个 epoch
        var lastEp = epochs[epochs.length - 1];
        if (lastEp && (state.lastGen < 0 || epochs.indexOf(lastEp) >= state.lastGen)) {
          emitEpoch(lastEp, step);
        }
      }
      state.timer = setTimer(tick, frameDelay());
    }

    var api = {
      steps: steps,
      epochs: epochs,
      getIndex: function () { return state.index; },
      getTotal: function () { return steps.length; },
      isPlaying: function () { return state.playing; },
      getSpeed: function () { return state.speed; },
      play: function () {
        if (state.playing) return;
        if (state.done || state.index >= steps.length) api.reset();
        state.playing = true;
        state.timer = setTimer(tick, 0);
      },
      pause: function () {
        state.playing = false;
        if (state.timer) { clearTimer(state.timer); state.timer = null; }
      },
      seek: function (index) {
        state.index = Math.max(0, Math.min(steps.length - 1, index | 0));
        state.done = false;
        var step = steps[state.index];
        if (step) { emitFrame(step); onFrame(step, state.index, steps.length); }
      },
      cycleSpeed: function () {
        var i = SPEEDS.indexOf(state.speed);
        state.speed = SPEEDS[(i + 1) % SPEEDS.length];
        return state.speed;
      },
      reset: function () {
        api.pause();
        state.index = 0;
        state.lastGen = -1;
        state.done = false;
        dispatch({ type: 'eco_reset' });   // 重播幂等：清生境字段 + 移除演练期新生个体
      },
      destroy: function () { api.pause(); },
    };
    return api;
  }

  // 导出：浏览器挂 window；CommonJS(vitest) 挂 module.exports
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createEcoReplay: createEcoReplay };
  }
  root.createEcoReplay = createEcoReplay;
})(typeof window !== 'undefined' ? window : globalThis);
