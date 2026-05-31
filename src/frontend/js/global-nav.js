/**
 * AgentsGroup2026 — Shared Global Navigation
 * Replaces hardcoded nav bars across all pages with a single
 * data-driven component. Use <script src="/js/global-nav.js" data-page="xxx">
 * where data-page matches one of the PAGE_IDS.
 */
(function () {
  'use strict';

  var PAGES = [
    { id: 'agents',       label: '智能体团队', href: '/agent-team-config.html' },
    { id: 'plaza',        label: '议事广场',   href: '/plaza.html' },
    { id: 'skill-extract', label: '技能萃取/赋予', href: '/skill-extract.html' },
    { id: 'digital-twin',  label: '数字孪生',   href: '/digital-twin-cli.html' },
    { id: 'sandbox',       label: 'SECS沙箱',   href: '/sandbox-twin.html' },
    { id: 'evolution',     label: '系统演进',   href: '/system-evolution.html' },
    { id: 'cost',          label: '💰 成本监控', href: '/cost-dashboard.html' },
  ];

  var script = document.querySelector('script[data-page]');
  var currentId = script ? script.getAttribute('data-page') : '';

  function buildNavHTML() {
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

  // Find all global-nav elements and replace content
  function injectNav() {
    var navs = document.querySelectorAll('.global-nav');
    var navHTML = buildNavHTML();
    for (var i = 0; i < navs.length; i++) {
      navs[i].innerHTML = navHTML;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectNav);
  } else {
    injectNav();
  }
})();
