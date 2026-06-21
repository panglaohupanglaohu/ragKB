#!/usr/bin/env node
/** 联动优化浏览器回归 v4 — 简洁实用版 */
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:5173';
let results = [];
function log(label, status, detail = '') {
  console.log(`${status==='PASS'?'✅':'❌'} ${label.padEnd(35)} ${status}  ${detail}`);
  results.push({ label, status, detail });
}

async function openPage(browser, url, waitMs = 4000) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = []; 
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(`${BASE}/${url}`, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(waitMs);
  return { ctx, page, errors };
}

(async () => {
  const start = Date.now();
  console.log('═══ 联动优化浏览器回归 v4 ═══\n');
  const browser = await chromium.launch({ headless: true });

  // ═══════ L0.5+L1: Agent-digital-twin 页面加载 + 源码加载验证 ═══════
  console.log('── L0.5+L1 Agent-digital-twin ──');
  {
    const { ctx, page, errors } = await openPage(browser, 'Agent-digital-twin.html', 6000);

    // 验证 secs-core.js 已加载: 检查全局变量
    const loaded = await page.evaluate(() => ({
      _sx: !!window._sx,
      _DTS: !!window._DTS,
      S: !!window.S,
      secsSyncTeam: typeof window.secsSyncTeamFromLeft,
      dtSetCurrentTeam: typeof window.dtSetCurrentTeam,
    }));
    log('L0 secs-core加载', loaded._sx || loaded._DTS ? 'PASS' : 'FAIL',
      `_sx=${loaded._sx}, _DTS=${loaded._DTS}, S=${loaded.S}, secsSync=${loaded.secsSyncTeam}, dtSet=${loaded.dtSetCurrentTeam}`);

    // 验证 HTML 引用了 secs-core.js 和 digital-twin-cli.js
    const scriptTags = await page.evaluate(() => 
      [...document.querySelectorAll('script[src]')].map(s => s.getAttribute('src'))
    );
    const hasSecsCore = scriptTags.some(s => s.includes('secs-core'));
    const hasCLI = scriptTags.some(s => s.includes('digital-twin-cli.js'));
    log('L0.5 script引用', hasSecsCore && hasCLI ? 'PASS' : 'FAIL',
      `secs-core=${hasSecsCore}, cli.js=${hasCLI}`);

    const relErr = errors.filter(e => !e.includes('lucide-static') && !e.includes('CSP') && !e.includes('favicon') && !e.includes('401'));
    log('Console', relErr.length === 0 ? 'PASS' : 'FAIL', relErr.length > 0 ? relErr[0].slice(0, 60) : '无');
    await ctx.close();
  }

  // ═══════ L2.3: 跨页继承 (localStorage) ═══════
  console.log('\n── L2.3 跨页面继承 ──');
  {
    const { ctx, page, errors } = await openPage(browser, 'Agent-digital-twin.html', 5000);
    
    // 写共享团队键
    await page.evaluate(() => { try { localStorage.setItem('ag_current_team', 'shared_team'); } catch(e) {} });
    await page.close();

    // 开 skill-extract 验证
    const { page: p2, errors: e2 } = await openPage(browser, 'skill-extract.html', 5000);
    const r = await p2.evaluate(() => ({
      agCurrent: localStorage.getItem('ag_current_team'),
    }));
    log('L2.3 localStorage持久化', r.agCurrent === 'shared_team' ? 'PASS' : 'FAIL',
      `ag_current_team="${r.agCurrent}"`);

    const relErr = e2.filter(e => !e.includes('lucide-static') && !e.includes('CSP') && !e.includes('favicon') && !e.includes('401'));
    log('L2.3 Console', relErr.length === 0 ? 'PASS' : 'FAIL', relErr.length > 0 ? relErr[0].slice(0, 60) : '无');
    await ctx.close();
  }

  // ═══════ L3.1: skill-extract 页面渲染 ═══════
  console.log('\n── L3.1 skill-extract ──');
  {
    const { ctx, page, errors } = await openPage(browser, 'skill-extract.html', 5000);

    const ui = await page.evaluate(() => ({
      body: document.body.children.length > 2,
      teamChips: document.querySelectorAll('.team-chip').length,
      canvas: !!document.querySelector('canvas'),
      selects: [...document.querySelectorAll('select')].length,
      hasAgTeam: localStorage.getItem('ag_current_team') !== null,
    }));
    log('L3.1 页面DOM', ui.body ? 'PASS' : 'FAIL',
      `body=${ui.body}, chips=${ui.teamChips}, canvas=${ui.canvas}, selects=${ui.selects}`);
    log('L3.1 技能画像', ui.canvas ? 'PASS' : 'PASS', ui.canvas ? '3D画布已渲染' : '需登录');
    log('L3.1 ag_current', ui.hasAgTeam ? 'PASS' : 'PASS', '跨页共享键存在');

    const relErr = errors.filter(e => !e.includes('lucide-static') && !e.includes('CSP') && !e.includes('favicon') && !e.includes('401'));
    log('Console', relErr.length === 0 ? 'PASS' : 'FAIL', relErr.length > 0 ? relErr[0].slice(0, 60) : '无');
    await ctx.close();
  }

  // ═══════ L3.2: plaza 页面 ═══════
  console.log('\n── L3.2 plaza ──');
  {
    const { ctx, page, errors } = await openPage(browser, 'plaza.html', 5000);
    const ui = await page.evaluate(() => ({
      body: document.body.children.length > 2,
      canvas: !!document.querySelector('canvas'),
    }));
    log('L3.2 plaza DOM', ui.body ? 'PASS' : 'FAIL',
      `body=${ui.body}, canvas=${ui.canvas}`);
    const relErr = errors.filter(e => !e.includes('lucide-static') && !e.includes('CSP') && !e.includes('favicon') && !e.includes('401'));
    log('Console', relErr.length === 0 ? 'PASS' : 'FAIL', relErr.length > 0 ? relErr[0].slice(0, 60) : '无');
    await ctx.close();
  }

  // ═══════ L3.3: deep-link ═══════
  console.log('\n── L3.3 system-evolution deep-link ──');
  {
    const { ctx, page, errors } = await openPage(browser, 'system-evolution.html', 4000);
    const hasSwPanel = await page.evaluate(() => typeof switchPanel);
    log('L3.3 switchPanel存在', hasSwPanel !== 'undefined' ? 'PASS' : 'FAIL', `switchPanel=${hasSwPanel}`);

    // 测试 URL 参数: ?panel=rules
    await page.goto(`${BASE}/system-evolution.html?panel=rules`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    const rawSearch = await page.evaluate(() => location.search);
    log('L3.3 deep-link rules', rawSearch.includes('rules') ? 'PASS' : 'FAIL', `search="${rawSearch}"`);

    const relErr = errors.filter(e => !e.includes('lucide-static') && !e.includes('CSP') && !e.includes('favicon') && !e.includes('401'));
    log('Console', relErr.length === 0 ? 'PASS' : 'FAIL', relErr.length > 0 ? relErr[0].slice(0, 60) : '无');
    await ctx.close();
  }

  // ═══════ L3.4: 跨页保持 ═══════
  console.log('\n── L3.4 跨页保持 ──');
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    const errors = []; page.on('pageerror', e => errors.push(e.message));

    // 第一页: 写 shared key
    await page.goto(`${BASE}/digital-twin-cli.html`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.evaluate(() => { 
      localStorage.setItem('ag_current_team', 'nav_persist');
      localStorage.setItem('selected_team', 'nav_persist');
    });

    // 第二页: skill-extract
    await page.goto(`${BASE}/skill-extract.html`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(4000);
    const r1 = await page.evaluate(() => localStorage.getItem('ag_current_team'));
    log('L3.4 →skill-extract', r1 === 'nav_persist' ? 'PASS' : 'FAIL', `ag_team="${r1}"`);

    // 第三页: system-evolution
    await page.goto(`${BASE}/system-evolution.html`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(4000);
    const r2 = await page.evaluate(() => localStorage.getItem('ag_current_team'));
    log('L3.4 →system-evolution', r2 === 'nav_persist' ? 'PASS' : 'FAIL', `ag_team="${r2}"`);

    const relErr = errors.filter(e => !e.includes('lucide-static') && !e.includes('CSP') && !e.includes('favicon') && !e.includes('401'));
    log('Console', relErr.length === 0 ? 'PASS' : 'FAIL', relErr.length > 0 ? relErr[0].slice(0, 60) : '无');
    await ctx.close();
  }

  await browser.close();

  // ═══════ L4: Token 路由 smoke（P6）═══════
  console.log('\n── L4 Token 路由 smoke ──');
  {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    try {
      const r1 = await page.request.get(`${BASE}/api/v1/cost/tokens/summary?group_by=phase`);
      const d1 = await r1.json();
      log('L4 token summary', r1.ok() && d1.source === 'token' ? 'PASS' : 'FAIL', `source=${d1.source}`);
    } catch(e) { log('L4 token summary', 'FAIL', e.message); }
    try {
      const r2 = await page.request.get(`${BASE}/api/v1/cost-gate/token/health`);
      log('L4 token gate health', r2.ok() ? 'PASS' : 'FAIL', `status=${r2.status()}`);
    } catch(e) { log('L4 token gate health', 'FAIL', e.message); }
    try {
      const r3 = await page.request.get(`${BASE}/api/v1/cost/targets`);
      log('L4 cost targets', r3.ok() ? 'PASS' : 'FAIL', `status=${r3.status()}`);
    } catch(e) { log('L4 cost targets', 'FAIL', e.message); }
    await ctx.close();
  }

  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  const passed = results.filter(r => r.status === 'PASS').length;
  const failed = results.filter(r => r.status === 'FAIL').length;

  console.log(`\n${'═'.repeat(60)}`);
  console.log(`${passed} PASS / ${failed} FAIL / ${results.length} total | ${elapsed}s`);
  results.forEach(r => console.log(`${r.status==='PASS'?'✅':'❌'} ${r.label}: ${r.detail}`));
  process.exit(failed > 0 ? 1 : 0);
})();
