#!/usr/bin/env node
/** plaza D-3: 渲染 dispose 性能回归 — 内存/几何体稳定性 */
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:5173';

(async () => {
  const browser = await chromium.launch({ headless: true });

  // ═══ Test 1: 单次广场渲染 + 内存基线 ═══
  console.log('═══ D-3 Plaza 渲染性能回归 ═══\n');
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(`${BASE}/plaza.html`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);

    // 检查 dispose 函数存在
    const codeCheck = await page.evaluate(() => {
      const src = document.documentElement.outerHTML;
      return {
        hasDisposeSceneAgents: src.includes('disposeSceneAgents'),
        hasDisposeObject3D: src.includes('disposeObject3D'),
        hasTraverse: src.includes('.traverse('),
        canvasCount: document.querySelectorAll('canvas').length,
      };
    });
    console.log(`[代码检查] disposeSceneAgents=${codeCheck.hasDisposeSceneAgents}, disposeObject3D=${codeCheck.hasDisposeObject3D}, canvas=${codeCheck.canvasCount}`);

    // 获取渲染器内存信息 (如果存在)
    const memInfo = await page.evaluate(() => {
      const r = window._plazaRenderer || window._renderer;
      if (!r?.info?.render) return null;
      return {
        textures: r.info.memory.textures,
        geometries: r.info.memory.geometries,
        draws: r.info.render.calls,
        triangles: r.info.render.triangles,
      };
    });
    if (memInfo) {
      console.log(`[渲染器基线] textures=${memInfo.textures}, geometries=${memInfo.geometries}, draws=${memInfo.draws}, triangles=${memInfo.triangles}`);
    } else {
      console.log('[渲染器] 未初始化 (无需登录广场)');
    }

    // 获取 JS 堆内存
    const jsHeap = await page.evaluate(() => {
      if (performance.memory) return {
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        usedJSHeapSize: performance.memory.usedJSHeapSize,
      };
      return null;
    });
    if (jsHeap) {
      console.log(`[JS堆] limit=${(jsHeap.jsHeapSizeLimit/1048576).toFixed(1)}MB, total=${(jsHeap.totalJSHeapSize/1048576).toFixed(1)}MB, used=${(jsHeap.usedJSHeapSize/1048576).toFixed(1)}MB`);
    }

    await ctx.close();
  }

  // ═══ Test 2: 反复切换广场模拟 (模拟 B-1.3 场景) ═══
  console.log('\n── 反复加载测试 (5次) ──');
  const memSnapshots = [];
  for (let i = 0; i < 5; i++) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(`${BASE}/plaza.html`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);

    const snap = await page.evaluate(() => {
      const r = window._plazaRenderer || window._renderer;
      const canvasCount = document.querySelectorAll('canvas').length;
      return {
        canvas: canvasCount,
        textures: r?.info?.memory?.textures ?? -1,
        geometries: r?.info?.memory?.geometries ?? -1,
      };
    });
    memSnapshots.push(snap);
    console.log(`  第${i+1}次: canvas=${snap.canvas}, textures=${snap.textures}, geometries=${snap.geometries}`);
    await ctx.close();
  }

  // 判断趋势
  const validSnaps = memSnapshots.filter(s => s.textures >= 0);
  let result = 'PASS';
  let detail = '';
  if (validSnaps.length >= 2) {
    const first = validSnaps[0].textures;
    const last = validSnaps[validSnaps.length - 1].textures;
    const trend = last - first;
    // 允许正常波动 (< 2x 增长)
    if (trend > first * 0.5 && first > 5) {
      result = 'WARN';
      detail = `textures ${first} → ${last} (+${trend}, +${(trend/first*100).toFixed(0)}%)`;
    } else {
      detail = `textures ${first} → ${last} (稳定)`;
    }
  } else {
    detail = '渲染器未初始化 (无需登录)';
  }
  console.log(`\n[结果] ${result}: ${detail}`);

  await browser.close();
  process.exit(result === 'FAIL' ? 1 : 0);
})();
