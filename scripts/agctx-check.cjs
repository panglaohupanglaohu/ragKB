const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e));

  // Load a simple page first to establish origin
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded', timeout: 10000 });
  await page.waitForTimeout(1000);

  // Then load plaza which has ag-context
  await page.goto('http://127.0.0.1:5173/plaza.html', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(3000);

  // Try to get AGCtx with a direct eval
  let agType;
  try {
    agType = await page.evaluate('window.AGCtx ? typeof window.AGCtx : "undefined"');
  } catch(e) {
    agType = 'error: ' + e.message;
  }
  console.log('AGCtx:', agType);
  console.log('pageErrors:', errors.length, errors.slice(0, 3).join(' | '));

  // Check if script was requested
  const reqs = [];
  page.on('request', r => { if (r.url().includes('ag-context')) reqs.push(r.url()); });
  page.on('response', r => { if (r.url().includes('ag-context')) console.log('Response:', r.status(), r.url()); });
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(3000);
  console.log('ag-context requests:', reqs);

  await browser.close();
})();
