import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

function bootGlobalNav(options = {}) {
  const source = read('src/frontend/js/global-nav.js');
  const navNode = { innerHTML: '' };
  const store = new Map();
  const user = options.user;
  if (user !== undefined) store.set('ag-user', user);
  const location = { href: '', pathname: '/plaza.html', search: '', hash: '' };
  const windowObj = {
    location,
    api: options.withLogoutApi === false ? null : { logout: () => Promise.resolve({ ok: true }) },
  };
  const localStorage = {
    getItem(key) { return store.has(key) ? store.get(key) : null; },
    setItem(key, value) { store.set(key, String(value)); },
    removeItem(key) { store.delete(key); },
  };
  const document = {
    readyState: 'complete',
    querySelector(selector) {
      if (selector === 'script[data-page]') {
        return { getAttribute(name) { return name === 'data-page' ? (options.pageId || 'plaza') : null; } };
      }
      return null;
    },
    querySelectorAll(selector) {
      return selector === '.global-nav' ? [navNode] : [];
    },
    addEventListener() {},
  };
  const context = {
    window: windowObj,
    document,
    localStorage,
    console,
    Promise,
    setTimeout,
    clearTimeout,
  };
  windowObj.window = windowObj;
  vm.runInNewContext(source, context);
  return { navNode, windowObj, location, localStorage };
}

describe('global-nav.js', () => {
  it('renders current page as plain text and shows logout for signed-in users', () => {
    const { navNode } = bootGlobalNav({ user: 'admin', pageId: 'plaza' });
    expect(navNode.innerHTML).toContain('<span class="cur">议事广场</span>');
    expect(navNode.innerHTML).toContain('window._agLogout()');
    expect(navNode.innerHTML).toContain('admin');
  });

  it('omits logout controls for guest users', () => {
    const { navNode } = bootGlobalNav({ user: 'guest', pageId: 'agents' });
    expect(navNode.innerHTML).toContain('<span class="cur">智能体团队</span>');
    expect(navNode.innerHTML).not.toContain('window._agLogout()');
  });

  it('logout clears cached user and redirects through api.logout when available', async () => {
    const { windowObj, location, localStorage } = bootGlobalNav({ user: 'operator' });
    windowObj._agLogout();
    await Promise.resolve();
    expect(localStorage.getItem('ag-user')).toBeNull();
    expect(location.href).toBe('/login.html');
  });

  it('logout still redirects when api.logout is unavailable', () => {
    const { windowObj, location, localStorage } = bootGlobalNav({ user: 'operator', withLogoutApi: false });
    windowObj._agLogout();
    expect(localStorage.getItem('ag-user')).toBeNull();
    expect(location.href).toBe('/login.html');
  });
});
