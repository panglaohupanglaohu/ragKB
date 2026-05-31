/**
 * AgentsGroup2026 — Shared Navigation Sidebar
 * Injects OpenBridge-compliant sidebar navigation into any page.
 * Usage: <script src="/js/nav-sidebar.js" data-active="captain"></script>
 */
(function () {
  'use strict';

  const NAV_ITEMS = [
    { id: 'captain',    icon: '⚓', label: 'nav.captain',    href: '/captain-cockpit-new.html' },
    { id: 'navigation', icon: '航', label: 'nav.navigation', href: '/navigation.html' },
    { id: 'dp',         icon: '定', label: 'nav.dp',         href: '/dp-control.html' },
    { id: 'thruster',   icon: '推', label: 'nav.thruster',   href: '/thruster-control.html' },
    { id: 'monitor',    icon: '监', label: 'nav.monitor',    href: '/worldmonitor-map.html' },
    { id: 'cms',        icon: '健', label: 'nav.cms',        href: '/cms-health.html' },
    { id: 'hmi',        icon: '台', label: 'nav.hmi',        href: '/hmi-console.html' },
    { id: 'offshore',   icon: '工', label: 'nav.offshore',   href: '/offshore-ops.html' },
    { id: 'weather',    icon: '海', label: 'nav.weather',    href: '/weather-ocean.html' },
    { id: 'crew',       icon: '员', label: 'nav.crew',       href: '/crew-management.html' },
    { sep: true },
    { id: 'sim',        icon: '练', label: 'nav.sim',        href: '/sim-training.html' },
    { id: 'energy',     icon: '能', label: 'nav.energy',     href: '/energy-compliance.html' },
    { id: 'datacenter', icon: '数', label: 'nav.datacenter', href: '/marine-datacenter.html' },
    { id: 'safety',     icon: '安', label: 'nav.safety',     href: '/safety-emergency.html' },
    { id: 'shore',      icon: '岸', label: 'nav.shore',      href: '/ship-shore.html' },
    { sep: true },
    { id: 'twin',       icon: '孪', label: 'nav.twin',       href: '/digital-twin.html' },
    { id: 'agents',     icon: '智', label: 'nav.agents',     href: '/agent-team-config.html' },
    { id: 'plaza',      icon: '⊙', label: 'nav.plaza',      href: '/plaza.html' },
    { id: 'tasks',      icon: '任', label: 'nav.tasks',      href: '/tasks.html' },
    { id: 'evolution',  icon: '演', label: 'nav.evolution',  href: '/system-evolution.html' },
    { id: 'kb',         icon: '知', label: 'nav.kb',         href: '/knowledge-base.html' },
    { id: 'llm-config', icon: '配', label: 'nav.llm-config', href: '/poseidon-config.html' },
  ];

  const THEMES = ['day', 'dusk', 'night', 'bright'];

  function getActiveId() {
    const script = document.querySelector('script[data-active]');
    return script ? script.getAttribute('data-active') : '';
  }

  function getCurrentTheme() {
    return document.documentElement.getAttribute('data-obc-theme') || 'dusk';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-obc-theme', theme);
    localStorage.setItem('ob-theme', theme);
  }

  function initTheme() {
    const saved = localStorage.getItem('ob-theme');
    if (saved && THEMES.includes(saved)) {
      setTheme(saved);
    } else {
      setTheme('dusk');
    }
  }

  function _t(key) {
    return (window.PX_I18N && window.PX_I18N.t) ? window.PX_I18N.t(key) : key;
  }

  function buildSidebar() {
    const activeId = getActiveId();
    const sidebar = document.createElement('nav');
    sidebar.className = 'ob-sidebar';
    sidebar.setAttribute('role', 'navigation');
    sidebar.setAttribute('aria-label', 'Main Navigation');

    // Brand
    const brand = document.createElement('div');
    brand.className = 'ob-nav-brand';
    brand.textContent = 'PX';
    brand.title = 'AgentsGroup2026';
    sidebar.appendChild(brand);

    // Nav items container
    const items = document.createElement('div');
    items.className = 'ob-nav-items';

    NAV_ITEMS.forEach(item => {
      if (item.sep) {
        const sep = document.createElement('div');
        sep.className = 'ob-nav-sep';
        items.appendChild(sep);
        return;
      }

      const a = document.createElement('a');
      a.className = 'ob-nav-item' + (item.id === activeId ? ' active' : '');
      a.href = item.href;
      a.setAttribute('data-nav-i18n', item.label);
      a.setAttribute('data-tooltip', _t(item.label));

      const icon = document.createElement('span');
      icon.className = 'ob-nav-icon';
      icon.textContent = item.icon;
      icon.setAttribute('aria-hidden', 'true');

      const label = document.createElement('span');
      label.className = 'ob-nav-label';
      label.textContent = _t(item.label);

      a.appendChild(icon);
      a.appendChild(label);
      items.appendChild(a);
    });

    sidebar.appendChild(items);

    // Footer with language toggle + theme switcher
    const footer = document.createElement('div');
    footer.className = 'ob-nav-footer';

    // Language toggle button
    const langWrap = document.createElement('div');
    langWrap.style.cssText = 'padding: 4px 6px;';
    const langBtn = document.createElement('button');
    langBtn.className = 'ob-theme-btn';
    langBtn.id = 'px-lang-btn';
    langBtn.style.cssText = 'width:100%;font-size:11px;letter-spacing:1px;';
    const curLang = (window.PX_I18N && window.PX_I18N.getLang) ? window.PX_I18N.getLang() : 'zh';
    langBtn.textContent = curLang === 'zh' ? '中/EN' : 'EN/中';
    langBtn.title = 'Switch Language';
    langBtn.addEventListener('click', () => {
      if (window.PX_I18N && window.PX_I18N.toggleLang) {
        window.PX_I18N.toggleLang();
        // Update sidebar labels
        sidebar.querySelectorAll('[data-nav-i18n]').forEach(a => {
          const key = a.getAttribute('data-nav-i18n');
          const translated = _t(key);
          a.setAttribute('data-tooltip', translated);
          const lbl = a.querySelector('.ob-nav-label');
          if (lbl) lbl.textContent = translated;
        });
      }
    });
    langWrap.appendChild(langBtn);
    footer.appendChild(langWrap);

    // Theme switcher
    const themeWrap = document.createElement('div');
    themeWrap.style.cssText = 'padding: 4px 6px;';

    const themeSwitch = document.createElement('div');
    themeSwitch.className = 'ob-theme-switch';
    themeSwitch.style.cssText = 'flex-direction: column;';

    const currentTheme = getCurrentTheme();
    const themeLabels = { day: '日', dusk: '暮', night: '夜', bright: '明' };

    THEMES.forEach(t => {
      const btn = document.createElement('button');
      btn.className = 'ob-theme-btn' + (t === currentTheme ? ' active' : '');
      btn.textContent = themeLabels[t];
      btn.title = t.charAt(0).toUpperCase() + t.slice(1);
      btn.addEventListener('click', () => {
        setTheme(t);
        themeSwitch.querySelectorAll('.ob-theme-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
      themeSwitch.appendChild(btn);
    });

    themeWrap.appendChild(themeSwitch);
    footer.appendChild(themeWrap);
    sidebar.appendChild(footer);

    return sidebar;
  }

  function buildTopbar(title, subtitle) {
    const topbar = document.createElement('header');
    topbar.className = 'ob-topbar';

    const titleWrap = document.createElement('div');
    titleWrap.style.cssText = 'display:flex;align-items:baseline;gap:4px;min-width:0;';

    const h1 = document.createElement('span');
    h1.className = 'ob-topbar-title';
    h1.textContent = title || document.title;
    titleWrap.appendChild(h1);

    if (subtitle) {
      const sub = document.createElement('span');
      sub.className = 'ob-topbar-subtitle';
      sub.textContent = subtitle;
      titleWrap.appendChild(sub);
    }

    topbar.appendChild(titleWrap);

    // Right: clock + connection status
    const actions = document.createElement('div');
    actions.className = 'ob-topbar-actions';

    const connDot = document.createElement('span');
    connDot.className = 'ob-dot';
    connDot.id = 'ob-conn-dot';
    connDot.title = 'Backend connection';
    actions.appendChild(connDot);

    const clock = document.createElement('span');
    clock.className = 'ob-clock';
    clock.id = 'ob-clock';
    actions.appendChild(clock);

    topbar.appendChild(actions);

    return topbar;
  }

  function updateClock() {
    const el = document.getElementById('ob-clock');
    if (!el) return;
    const now = new Date();
    const utc = now.toISOString().slice(11, 19);
    el.textContent = utc + ' UTC';
  }

  function checkBackend() {
    const dot = document.getElementById('ob-conn-dot');
    if (!dot) return;
    fetch('/api/v1/health', { signal: AbortSignal.timeout(3000) })
      .then(r => {
        dot.className = r.ok ? 'ob-dot ob-dot-ok' : 'ob-dot ob-dot-warning';
        dot.title = r.ok ? 'Backend connected' : 'Backend error';
      })
      .catch(() => {
        dot.className = 'ob-dot ob-dot-alarm';
        dot.title = 'Backend offline';
      });
  }

  /**
   * Initialize navigation shell.
   * Wraps existing <body> content in the OpenBridge layout.
   */
  function init() {
    initTheme();

    const pageTitle = document.querySelector('meta[name="ob-title"]');
    const pageSubtitle = document.querySelector('meta[name="ob-subtitle"]');
    const title = pageTitle ? pageTitle.content : document.title;
    const subtitle = pageSubtitle ? pageSubtitle.content : '';

    // Check if already wrapped
    if (document.querySelector('.ob-app')) return;

    // Create shell
    const app = document.createElement('div');
    app.className = 'ob-app';

    const sidebar = buildSidebar();
    const main = document.createElement('div');
    main.className = 'ob-main';

    const topbar = buildTopbar(title, subtitle);

    const content = document.createElement('div');
    content.className = 'ob-content';

    // Move existing body children into content
    while (document.body.firstChild) {
      // Skip our own script tag
      if (document.body.firstChild === document.currentScript) {
        document.body.removeChild(document.body.firstChild);
        continue;
      }
      content.appendChild(document.body.firstChild);
    }

    main.appendChild(topbar);
    main.appendChild(content);
    app.appendChild(sidebar);
    app.appendChild(main);
    document.body.appendChild(app);

    // Start clock + health check (pause when tab hidden)
    updateClock();
    setInterval(function(){ if (!document.hidden) updateClock(); }, 1000);
    checkBackend();
    setInterval(function(){ if (!document.hidden) checkBackend(); }, 10000);
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
