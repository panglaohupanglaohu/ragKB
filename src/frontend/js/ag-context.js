/**
 * AGCtx — 全局"选择上下文"总线(L4)
 *
 * 解决系统中"同一选择被多处各自存一份、改一处不通知其他"的联动问题:
 *   - 单一数据源:team / room / scenario / agent / discussion
 *   - 订阅广播:面板用 AGCtx.on(fn) 订阅,选择项变更自动收到通知去刷新
 *   - 跨页持久化:localStorage `ag_ctx_<key>`;`storage` 事件让其它已打开页面实时跟随
 *
 * 纯浏览器脚本(无 import),可由各页面 <script src="/js/ag-context.js"> 直接引入。
 * 设计为渐进式:不要求一次性替换所有点对点联动,新面板订阅即可,不会再漏。
 */
(function (global) {
  'use strict';
  if (global.AGCtx) return; // 幂等,避免重复注入

  var KEYS = ['team', 'room', 'scenario', 'agent', 'discussion'];
  // 兼容历史键:team 仍镜像到 L2 已用的 ag_current_team
  var LEGACY = { team: 'ag_current_team' };

  function lsGet(k) {
    try { return localStorage.getItem('ag_ctx_' + k) || (LEGACY[k] ? localStorage.getItem(LEGACY[k]) : '') || ''; }
    catch (e) { return ''; }
  }
  function lsSet(k, v) {
    try {
      localStorage.setItem('ag_ctx_' + k, v);
      if (LEGACY[k]) localStorage.setItem(LEGACY[k], v); // 双写兼容旧代码
    } catch (e) {}
  }

  var AGCtx = {
    _s: {},
    _subs: [],

    /** 读当前值:内存优先,回退 localStorage */
    get: function (k) {
      if (this._s[k] != null && this._s[k] !== '') return this._s[k];
      return lsGet(k);
    },

    /** 设值:去重 → 持久化 → 广播订阅者。silent=true 时只更新不持久化(用于跨页同步入站) */
    set: function (k, v, opts) {
      v = v == null ? '' : String(v);
      if (this._s[k] === v) return false;       // 去重,杜绝循环
      this._s[k] = v;
      if (!(opts && opts.silent)) lsSet(k, v);
      this._emit(k, v, opts || {});
      return true;
    },

    /** 订阅:fn(key, value, opts);返回取消订阅函数 */
    on: function (fn) {
      if (typeof fn !== 'function') return function () {};
      this._subs.push(fn);
      var self = this;
      return function () { var i = self._subs.indexOf(fn); if (i >= 0) self._subs.splice(i, 1); };
    },

    _emit: function (k, v, opts) {
      for (var i = 0; i < this._subs.length; i++) {
        try { this._subs[i](k, v, opts); } catch (e) { /* 单个订阅异常不影响其他 */ }
      }
    },

    keys: function () { return KEYS.slice(); },
  };

  // 跨页同步:其它页面/标签页改了 ag_ctx_* 或兼容键 → 静默入站(不回写,避免循环)
  global.addEventListener && global.addEventListener('storage', function (e) {
    if (!e || !e.key) return;
    var key = null;
    if (e.key.indexOf('ag_ctx_') === 0) key = e.key.slice(7);
    else { for (var k in LEGACY) { if (LEGACY[k] === e.key) { key = k; break; } } }
    if (key && e.newValue != null) AGCtx.set(key, e.newValue, { silent: true, fromStorage: true });
  });

  global.AGCtx = AGCtx;
})(typeof window !== 'undefined' ? window : this);
