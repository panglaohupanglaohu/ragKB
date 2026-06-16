/**
 * AgentsGroup2026 — Unified Navigation (single source of truth)
 * Renders the shared page set into:
 *   - .topbar-ws__nav   (primary horizontal topbar — recommended shell)
 *   - .global-nav       (legacy flat nav — kept for back-compat / tests)
 * Usage: <script src="/js/nav.js" data-page="plaza"></script>
 * data-page must match a PAGE id below.
 *
 * Also wires the user chip (.topbar-ws__user-name / -avatar / logout btn)
 * and exposes window._agLogout (back-compat with global-nav.js).
 */
(function () {
  'use strict';

  // Single shared page set (matches global-nav.js)
  var PAGES = [
    { id: 'agents',        label: '智能体团队',     href: '/agent-team-config.html' },
    { id: 'plaza',         label: '议事广场',       href: '/plaza.html' },
    { id: 'skill-extract', label: '技能萃取/赋予',  href: '/skill-extract.html' },
    { id: 'digital-twin',  label: '数字孪生',       href: '/Agent-digital-twin.html' },
    { id: 'evolution',     label: '系统演进',       href: '/system-evolution.html' },
    { id: 'cost',          label: '💰 成本监控',    href: '/cost-dashboard.html' }
  ];

  function currentPageId() {
    var s = document.querySelector('script[data-page]');
    return s ? s.getAttribute('data-page') : '';
  }

  // Build link set HTML; current page is non-clickable <span class="cur">.
  function buildNavHTML(currentId) {
    var html = '';
    for (var i = 0; i < PAGES.length; i++) {
      var p = PAGES[i];
      if (p.id === currentId) {
        html += '<span class="cur">' + p.label + '</span>';
      } else {
        html += '<a href="' + p.href + '">' + p.label + '</a>';
      }
    }
    return html;
  }

  // Inject into every nav container on the page.
  function injectNav() {
    var currentId = currentPageId();
    var html = buildNavHTML(currentId);
    var targets = document.querySelectorAll('.topbar-ws__nav, .global-nav');
    for (var i = 0; i < targets.length; i++) {
      // Only overwrite if empty OR explicitly marked data-nav-auto
      var el = targets[i];
      if (el.hasAttribute('data-nav-auto') || el.children.length === 0) {
        el.innerHTML = html;
      }
    }
    syncUserChip();
  }

  // Sync user chip from localStorage('ag-user')
  function syncUserChip() {
    var user = localStorage.getItem('ag-user');
    var name = (user && user !== 'guest') ? user : 'guest';
    var initial = name ? name.charAt(0).toUpperCase() : 'U';
    var nameEls = document.querySelectorAll('.topbar-ws__user-name');
    var avatarEls = document.querySelectorAll('.topbar-ws__user-avatar');
    for (var i = 0; i < nameEls.length; i++) nameEls[i].textContent = name;
    for (var j = 0; j < avatarEls.length; j++) avatarEls[j].textContent = initial;
  }

  // Logout — back-compat with global-nav.js (window._agLogout)
  window._agLogout = function () {
    if (window.api && window.api.logout) {
      window.api.logout().then(function () {
        localStorage.removeItem('ag-user');
        window.location.href = '/login.html';
      });
    } else {
      localStorage.removeItem('ag-user');
      window.location.href = '/login.html';
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectNav);
  } else {
    injectNav();
  }

  // Expose for reuse / tests
  window.AG_NAV = { PAGES: PAGES, buildNavHTML: buildNavHTML, injectNav: injectNav };
})();
