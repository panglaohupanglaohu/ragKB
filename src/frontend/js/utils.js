/**
 * AgentsGroup2026 — Shared Utility Library
 * Core helpers: escapeHtml, toast, modal management, loading states,
 * error display, debounce/throttle, time formatting, number formatting.
 * Exposes window.AG namespace and legacy global aliases.
 * Load before api.js and all page-specific scripts.
 */
(function () {
  'use strict';

  var utils = window.AG = {};

  /**
   * Escape HTML special characters for safe innerHTML insertion.
   */
  utils.escapeHtml = function (v) {
    return String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  };

  /**
   * Shortcut: document.getElementById
   */
  utils.$ = function (id) { return document.getElementById(id); };

  /**
   * Status label mapping (Chinese).
   */
  utils.statusLabel = function (s) {
    return { idle: '待命中', working: '工作中', reporting: '汇报中', blocked: '阻塞', error: '异常' }[s] || s || '未知';
  };

  /**
   * Format a number with locale separators.
   */
  utils.fmtNum = function (v) {
    return Number(v || 0).toLocaleString();
  };

  /**
   * Shorten an ID to n chars.
   */
  utils.shortId = function (v, n) {
    n = n || 8;
    var s = String(v || '');
    return s ? s.slice(0, n) : '-';
  };

  /**
   * Relative time in Chinese.
   */
  utils.relTime = function (v) {
    if (!v) return '-';
    var ms = typeof v === 'number' ? v * 1000 : Date.parse(v);
    if (!Number.isFinite(ms)) return '-';
    var diff = Math.max(0, Date.now() - ms);
    var mins = Math.floor(diff / 60000);
    if (mins < 1) return '刚刚';
    if (mins < 60) return mins + ' 分钟前';
    var hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + ' 小时前';
    return Math.floor(hrs / 24) + ' 天前';
  };

  /**
   * Debounce a function.
   */
  utils.debounce = function (fn, ms) {
    ms = ms || 300;
    var t;
    return function () {
      var args = arguments;
      var ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  };

  /**
   * Throttle a function.
   */
  utils.throttle = function (fn, ms) {
    ms = ms || 200;
    var last = 0;
    return function () {
      var now = Date.now();
      if (now - last >= ms) {
        last = now;
        fn.apply(this, arguments);
      }
    };
  };

  /**
   * Toast notification.
   */
  utils.toast = function (msg, type) {
    var e = document.getElementById('toast');
    if (!e) return;
    e.className = 'toast' + (type ? ' toast-' + type : '');
    e.textContent = msg;
    e.classList.add('show');
    var dur = type === 'error' ? 5000 : 2500;
    setTimeout(function () { e.classList.remove('show'); }, dur);
  };

  /**
   * Open a modal by id with focus trap.
   */
  utils.openModal = function (id) {
    var m = document.getElementById(id);
    if (!m) return;
    m.classList.add('open');
    m.setAttribute('role', 'dialog');
    m.setAttribute('aria-modal', 'true');
    var focusable = m.querySelectorAll('button,input,select,textarea,[tabindex]:not([tabindex="-1"])');
    if (focusable.length) focusable[0].focus();
    m._focusTrap = function (e) {
      if (e.key === 'Escape') { utils.closeModal(id); return; }
      if (e.key !== 'Tab') return;
      var first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    m.addEventListener('keydown', m._focusTrap);
  };

  /**
   * Close a modal by id.
   */
  utils.closeModal = function (id) {
    var m = document.getElementById(id);
    if (!m) return;
    m.classList.remove('open');
    m.removeAttribute('aria-modal');
    if (m._focusTrap) { m.removeEventListener('keydown', m._focusTrap); delete m._focusTrap; }
  };

  /**
   * Show an informational modal.
   */
  utils.showInfoModal = function (title, body) {
    var overlay = document.createElement('div');
    overlay.className = 'modal-overlay open';
    overlay.onclick = function (e) { if (e.target === this) overlay.remove(); };
    overlay.innerHTML = '<div class="modal"><h3>' + utils.escapeHtml(title) + '</h3><div style="font-size:13px;line-height:1.7;white-space:pre-wrap;word-break:break-word">' + body + '</div><div class="modal-actions"><button class="btn">关闭</button></div></div>';
    overlay.querySelector('.modal .btn').onclick = function () { overlay.remove(); };
    document.body.appendChild(overlay);
  };

  /**
   * Show loading state in a view.
   */
  utils.showViewLoading = function (viewId) {
    var el = document.getElementById(viewId);
    if (!el) return;
    var scroll = el.querySelector('.main-scroll') || el;
    scroll.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;padding:80px 0;color:var(--muted);font-size:13px"><span style="display:inline-block;width:16px;height:16px;border:2px solid var(--groove);border-top-color:var(--koke);border-radius:50%;animation:spin .6s linear infinite;margin-right:10px"></span>加载中...</div>';
  };

  // ── Legacy aliases for backward compatibility ──
  window.escapeHtml = utils.escapeHtml;
  window.el = utils.$;
  window.stL = utils.statusLabel;
  window.fmtNum = utils.fmtNum;
  window.shortId = utils.shortId;
  window.relTime = utils.relTime;
  window.debounce = utils.debounce;
  window.toast = utils.toast;
  window.openModal = utils.openModal;
  window.closeModal = utils.closeModal;
  window.showInfoModal = utils.showInfoModal;
  window.showViewLoading = utils.showViewLoading;

  /**
   * Show an inline error message in a view.
   * Creates or updates an error banner inside the given element.
   */
  utils.showError = function (containerId, message) {
    var container = document.getElementById(containerId);
    if (!container) return;
    // Check if existing error banner
    var existing = container.querySelector('.ag-error-banner');
    if (existing) {
      existing.textContent = '⚠ ' + message;
      existing.style.display = '';
      return;
    }
    var banner = document.createElement('div');
    banner.className = 'ag-error-banner';
    banner.textContent = '⚠ ' + message;
    banner.style.cssText = 'padding:12px 16px;margin-bottom:12px;background:rgba(224,27,36,0.08);border:1px solid rgba(224,27,36,0.25);color:var(--shu);font-size:13px;border-radius:0;';
    container.insertBefore(banner, container.firstChild);
  };

  /**
   * Clear error banner from a container.
   */
  utils.clearError = function (containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;
    var existing = container.querySelector('.ag-error-banner');
    if (existing) existing.style.display = 'none';
  };

})();
