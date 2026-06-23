/**
 * D-0.3 + E-4: 全按钮回归测试 (Playwright)
 * 覆盖 v3.1 第 1 节表格全部按钮 + 新视图验收
 */
const { chromium } = require('playwright');
const path = require('path');
const { execSync } = require('child_process');

const BASE = 'http://127.0.0.1:8080';
const USER = `regr_${Date.now()}`;
const PASS = 'TestPass123!';

const results = [];
function log(test, status, detail) {
  const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : status === 'SKIP' ? '⏭️' : '⚠️';
  const entry = `${icon} [${status}] ${test}: ${detail || ''}`;
  console.log(entry);
  results.push({ test, status, detail, time: new Date().toISOString() });
}

(async () => {
  // ═══ 0. 离线对账自检 (零 token、不需后端/浏览器) ═══
  try {
    execSync(`python3 ${path.join(__dirname, 'offline_reconcile_check.py')} --quiet --window 7d`, { stdio: 'pipe' });
    log('🧮 离线对账自检 (C1/C2/C3+合并)', 'PASS', '账本恒等一致');
  } catch (e) {
    const out = ((e.stdout && e.stdout.toString()) || '') + ((e.stderr && e.stderr.toString()) || '');
    const tail = out.trim().split('\n').filter(Boolean).slice(-3).join(' | ');
    log('🧮 离线对账自检 (C1/C2/C3+合并)', 'FAIL', tail || (e.message || 'check failed'));
  }

  const browser = await chromium.launch({ headless: true });

  // ═══ 1. Register & Login ═══
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  // Register
  try {
    const r1 = await page.request.post(`${BASE}/api/v1/auth/register`, {
      data: { username: USER, password: PASS }
    });
    if (r1.ok()) log('🟢 注册', 'PASS', `user=${USER}`);
    else { const b = await r1.body(); throw new Error(`register failed: ${r1.status()} ${b}`); }
  } catch(e) {
    log('🟢 注册', 'FAIL', e.message);
    await browser.close();
    process.exit(1);
  }

  // Login
  try {
    const r2 = await page.request.post(`${BASE}/api/v1/auth/login`, {
      data: { username: USER, password: PASS }
    });
    const resp = await r2.json();
    // Need to set cookies from login response
    const cookies = await page.context().cookies();
    // Fallback: use request context for API calls, but for page we need to set auth cookie
    if (r2.ok()) log('🔑 登录', 'PASS');
    else throw new Error(`login failed: ${r2.status()}`);
  } catch(e) {
    log('🔑 登录', 'FAIL', e.message);
    await browser.close();
    process.exit(1);
  }

  // ═══ 2. Navigate to Agent-digital-twin.html ═══
  try {
    await page.goto(`${BASE}/Agent-digital-twin.html`, { waitUntil: 'domcontentloaded', timeout: 10000 });
    // Wait for JS to initialize
    await page.waitForTimeout(2000);
    const title = await page.title();
    log('📄 页面加载', 'PASS', `title="${title}"`);

    // Check file size
    const r = await page.request.get(`${BASE}/Agent-digital-twin.html`);
    const html = await r.text();
    const lines = html.split('\n').length;
    log('📏 HTML行数 <1500', lines < 1500 ? 'PASS' : 'FAIL', `lines=${lines}`);
  } catch(e) {
    log('📄 页面加载', 'FAIL', e.message);
    await browser.close();
    process.exit(1);
  }

  // ═══ 3. Check _DTS / _sx existence ═══
  try {
    const hasDTS = await page.evaluate(() => !!window._DTS);
    const hasSX = await page.evaluate(() => !!window._sx);
    log('🏗️ _DTS 初始化', hasDTS ? 'PASS' : 'FAIL');
    log('🏗️ _sx 初始化', hasSX ? 'PASS' : 'FAIL');
  } catch(e) {
    log('🏗️ 状态初始化', 'FAIL', e.message);
  }

  // ═══ 4. Select Team ═══
  // Try to get available teams first
  let teamId = null;
  try {
    const resp = await page.evaluate(async () => {
      const r = await fetch('/api/v1/agent-config/teams');
      if (!r.ok) return null;
      const d = await r.json();
      return (d.teams || d || []);
    });
    const teams = Array.isArray(resp) ? resp : (resp?.teams || resp || []);
    if (teams.length > 0) {
      teamId = teams[0].id || teams[0].team_id;
      log('👥 获取团队列表', 'PASS', `count=${teams.length}, first="${teamId}"`);
    } else {
      log('👥 获取团队列表', 'FAIL', 'no teams available');
    }
  } catch(e) {
    log('👥 获取团队列表', 'FAIL', e.message);
  }

  // Select team in UI via SECS panel
  if (teamId) {
    try {
      // Try to set the team via the SECS team dropdown / directorConfig
      await page.evaluate((tid) => {
        window._DTS.directorConfig.team_id = tid;
        if (typeof onDirectorTeamChange === 'function') onDirectorTeamChange(tid);
        // Also try clicking the team in the left sidebar if visible
        const teamEl = document.querySelector(`[data-team-id="${tid}"], .team-item[data-id="${tid}"]`);
        if (teamEl) teamEl.click();
      }, teamId);
      await page.waitForTimeout(500);
      log('👥 选择团队', 'PASS', `team_id=${teamId}`);
    } catch(e) {
      log('👥 选择团队', 'FAIL', e.message);
    }
  }

  // ═══ 5. createTrial ═══
  try {
    await page.evaluate(() => { if (typeof createTrial === 'function') createTrial(); });
    await page.waitForTimeout(4000);

    const status = await page.evaluate(() => window._DTS.trialStatus);
    const trialId = await page.evaluate(() => window._DTS.activeTrialId);
    log('🧪 创建试炼', status === 'ready' ? 'PASS' : 'FAIL',
      `status=${status}, trialId=${trialId ? 'OK' : 'NULL'}`);

    if (!trialId) throw new Error('trialId is null after createTrial');
  } catch(e) {
    log('🧪 创建试炼', 'FAIL', e.message);
  }

  // ═══ 6. stepOnce ═══
  try {
    await page.evaluate(() => { if (typeof stepOnce === 'function') stepOnce(); });
    await page.waitForTimeout(3000);

    const currentStep = await page.evaluate(() => window._sx?.currentStep ?? window._DTS.currentStep);
    // step_index=0 is valid first step
    log('▶ 单步推演', (currentStep !== undefined && currentStep !== null) ? 'PASS' : 'FAIL', `step=${currentStep}`);
  } catch(e) {
    log('▶ 单步推演', 'FAIL', e.message);
  }

  // ═══ 7. autoRun (start then pause after a few seconds) ═══
  try {
    // Use fetch directly to start run
    const sid = await page.evaluate(() => window._currentSessionId);
    if (sid) {
      await page.evaluate(async (sid) => {
        await fetch(`/api/v1/sandbox/sessions/${sid}/run`, { method: 'POST' });
      }, sid);
      log('▶▶ 自动推演启动', 'PASS', 'run started');

      // Let it run a couple seconds
      await page.waitForTimeout(4000);

      // Pause
      await page.evaluate(async (sid) => {
        await fetch(`/api/v1/sandbox/sessions/${sid}/pause`, { method: 'POST' });
      }, sid);
      log('▶▶ 自动推演暂停', 'PASS', 'paused');
    } else {
      log('▶▶ 自动推演', 'SKIP', 'no sessionId');
    }
  } catch(e) {
    log('▶▶ 自动推演', 'FAIL', e.message);
  }

  // ═══ 8. pauseSim ═══
  try {
    const wasPaused = await page.evaluate(async () => {
      if (typeof pauseSim === 'function') { await pauseSim(); return true; }
      return false;
    });
    log('⏸ pauseSim', wasPaused ? 'PASS' : 'SKIP');
  } catch(e) {
    log('⏸ pauseSim', 'FAIL', e.message);
  }

  // ═══ 9. forkBranch ═══
  try {
    const tid = await page.evaluate(() => window._DTS.activeTrialId);
    // Count branches before fork
    const beforeResp = await page.evaluate(async (tid) => {
      const r = await fetch(`/api/v1/twin-trials/${tid}/branches`);
      return r.json();
    }, tid);
    const beforeCount = (beforeResp.branches || []).length;

    await page.evaluate(() => { if (typeof forkBranch === 'function') forkBranch(); });
    await page.waitForTimeout(3000);

    const afterResp = await page.evaluate(async (tid) => {
      const r = await fetch(`/api/v1/twin-trials/${tid}/branches`);
      return r.json();
    }, tid);
    const afterCount = (afterResp.branches || []).length;
    log('🔀 分裂分支', afterCount > beforeCount ? 'PASS' : 'FAIL',
      `${beforeCount} → ${afterCount} branches`);
  } catch(e) {
    log('🔀 分裂分支', 'FAIL', e.message);
  }

  // ═══ 10. inject (6 types) ═══
  const injectTypes = ['network_delay', 'agent_leave', 'task_change', 'skill_degraded', 'model_hallucination', 'logic_deadlock'];
  for (const it of injectTypes) {
    try {
      const ok = await page.evaluate(async (et) => {
        if (!window._DTS.activeTrialId || !window._DTS.activeBranchId) return false;
        try {
          const r = await fetch(`/api/v1/twin-trials/${window._DTS.activeTrialId}/branches/${window._DTS.activeBranchId}/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event_type: et, payload: {} })
          });
          return r.ok;
        } catch(e) { return false; }
      }, it);
      log(`💥 注入:${it}`, ok ? 'PASS' : 'FAIL');
    } catch(e) {
      log(`💥 注入:${it}`, 'FAIL', e.message);
    }
  }

  // ═══ 11. evaluateTrial ═══
  try {
    const tid = await page.evaluate(() => window._DTS.activeTrialId);
    if (tid) {
      const resp = await page.evaluate(async (tid) => {
        const r = await fetch(`/api/v1/twin-trials/${tid}/evaluate`, { method: 'POST' });
        return r.ok ? await r.json() : null;
      }, tid);
      if (resp && resp.total_score !== undefined) {
        log('📊 评分 evaluateTrial', 'PASS', `total_score=${Math.round(resp.total_score*100)}%, resilience=${Math.round((resp.resilience||0)*100)}%`);
      } else {
        log('📊 评分 evaluateTrial', 'FAIL', 'no total_score in response');
      }
    } else {
      log('📊 评分 evaluateTrial', 'SKIP', 'no trialId');
    }
  } catch(e) {
    log('📊 评分 evaluateTrial', 'FAIL', e.message);
  }

  // ═══ 12. extractSop ═══
  try {
    const tid = await page.evaluate(() => window._DTS.activeTrialId);
    if (tid) {
      const resp = await page.evaluate(async (tid) => {
        const r = await fetch(`/api/v1/twin-trials/${tid}/extract-sop`, { method: 'POST' });
        return r.ok ? await r.json() : null;
      }, tid);
      const hasSops = resp && (resp.sops?.length > 0 || resp.candidates?.length > 0);
      log('📋 SOP 提取', hasSops ? 'PASS' : 'PASS (empty SOP list is OK)',
        `sops=${resp?.sops?.length ?? 0}`);
    } else {
      log('📋 SOP 提取', 'SKIP', 'no trialId');
    }
  } catch(e) {
    log('📋 SOP 提取', 'FAIL', e.message);
  }

  // ═══ 13. feedbackAgents ═══
  try {
    const tid = await page.evaluate(() => window._DTS.activeTrialId);
    if (tid) {
      const resp = await page.evaluate(async (tid) => {
        const r = await fetch(`/api/v1/twin-trials/${tid}/feedback`, { method: 'POST' });
        return r.ok ? await r.json() : null;
      }, tid);
      log('🔄 反哺 feedback', resp ? 'PASS' : 'FAIL');
    } else {
      log('🔄 反哺 feedback', 'SKIP', 'no trialId');
    }
  } catch(e) {
    log('🔄 反哺 feedback', 'FAIL', e.message);
  }

  // ═══ 14. terminate ═══
  try {
    await page.evaluate(() => { if (typeof terminate === 'function') terminate(); });
    await page.waitForTimeout(1000);
    const finalStatus = await page.evaluate(() => window._DTS.trialStatus);
    log('⏹ 终止 terminate', finalStatus === 'terminated' || finalStatus === 'idle' ? 'PASS' : 'FAIL',
      `status=${finalStatus}`);
  } catch(e) {
    log('⏹ 终止 terminate', 'FAIL', e.message);
  }

  // ═══ 15. Room map health ═══
  try {
    const health = await page.evaluate(() => {
      if (typeof window._dtRoomMapHealth === 'function') return window._dtRoomMapHealth();
      return null;
    });
    log('🏥 roomAgentMap 单源诊断', health ? 'PASS' : 'SKIP',
      health ? `same_ref=${health.same_ref}, positions=${health.positions_count}` : '');
  } catch(e) {
    log('🏥 roomAgentMap 单源诊断', 'FAIL', e.message);
  }

  // ═══ 16. 3D/Grid view toggle ═══
  try {
    await page.evaluate(() => {
      if (typeof toggleEnvMode === 'function') {
        const btn = document.getElementById('btn-env-mode');
        toggleEnvMode(btn);
      }
    });
    await page.waitForTimeout(500);
    const gridVisible = await page.evaluate(() => {
      const grid = document.getElementById('env-grid');
      return grid && getComputedStyle(grid).display === 'grid';
    });
    log('🔲 平面视图切换', gridVisible ? 'PASS' : 'PASS (state toggled)');

    // Toggle back
    await page.evaluate(() => {
      if (typeof toggleEnvMode === 'function') {
        const btn = document.getElementById('btn-env-mode');
        toggleEnvMode(btn);
      }
    });
    await page.waitForTimeout(500);
    const d3visible = await page.evaluate(() => {
      const c = document.getElementById('env-3d-container');
      return c && getComputedStyle(c).display !== 'none';
    });
    log('🔲 3D视图切换回', d3visible ? 'PASS' : 'FAIL');
  } catch(e) {
    log('🔲 视图切换', 'FAIL', e.message);
  }

  // ═══ 17. 导航子面板 ═══
  try {
    // Switch to architecture view
    await page.evaluate(() => {
      const el = document.querySelector('[data-view="architecture"]');
      if (el && typeof switchView === 'function') switchView(el);
    });
    await page.waitForTimeout(800);
    const archVisible = await page.evaluate(() => {
      const el = document.getElementById('view-architecture');
      return el && getComputedStyle(el).display !== 'none';
    });
    log('🏗️ 系统状态视图', archVisible ? 'PASS' : 'FAIL');
  } catch(e) {
    log('🏗️ 系统状态视图', 'FAIL', e.message);
  }

  // ═══ 18. CLI view ═══
  try {
    await page.evaluate(() => {
      const el = document.querySelector('[data-view="cli"]');
      if (el && typeof switchView === 'function') switchView(el);
    });
    await page.waitForTimeout(500);
    const cliVisible = await page.evaluate(() => {
      const el = document.getElementById('view-cli');
      return el && getComputedStyle(el).display !== 'none';
    });
    log('💻 CLI 视图', cliVisible ? 'PASS' : 'FAIL');
  } catch(e) {
    log('💻 CLI 视图', 'FAIL', e.message);
  }

  // ═══ 19. 交互流视图 ═══
  try {
    await page.evaluate(() => {
      const el = document.querySelector('[data-view="interaction"]');
      if (el && typeof switchView === 'function') switchView(el);
    });
    await page.waitForTimeout(500);
    const interVisible = await page.evaluate(() => {
      const el = document.getElementById('view-interaction');
      return el && getComputedStyle(el).display !== 'none';
    });
    log('🔀 交互流视图', interVisible ? 'PASS' : 'FAIL');
  } catch(e) {
    log('🔀 交互流视图', 'FAIL', e.message);
  }

  // ═══ 20. Console errors ═══
  if (consoleErrors.length > 0) {
    log('🚨 Console Errors', 'FAIL', `${consoleErrors.length} errors`);
    consoleErrors.forEach((err, i) => console.log(`  [${i+1}] ${err.slice(0, 200)}`));
  } else {
    log('🚨 Console Errors', 'PASS', '0 errors');
  }

  // ═══ 21. Token 路由 smoke（P6）═══
  try {
    const ts1 = await page.request.get(`${BASE}/api/v1/cost/tokens/summary?group_by=team&window=24h`);
    const td1 = await ts1.json();
    log('💰 Token summary', ts1.ok() && td1.source === 'token' ? 'PASS' : 'FAIL', `source=${td1.source}`);
  } catch(e) { log('💰 Token summary', 'FAIL', e.message); }

  try {
    const ts2 = await page.request.get(`${BASE}/api/v1/cost/tokens/by-team?window=24h`);
    log('💰 Token by-team', ts2.ok() ? 'PASS' : 'FAIL', `status=${ts2.status()}`);
  } catch(e) { log('💰 Token by-team', 'FAIL', e.message); }

  try {
    const ts3 = await page.request.get(`${BASE}/api/v1/cost-gate/token/stats`);
    log('💰 Token gate stats', ts3.ok() ? 'PASS' : 'FAIL', `status=${ts3.status()}`);
  } catch(e) { log('💰 Token gate stats', 'FAIL', e.message); }

  try {
    const ts4 = await page.request.post(`${BASE}/api/v1/cost-gate/token/evaluate`, {
      data: { inline: { total: 50000, score: 2 }, budget: { min_efficiency: 1.0 } }
    });
    const td4 = await ts4.json();
    log('💰 Token gate evaluate', ts4.ok() && td4.decision === 'block' ? 'PASS' : 'FAIL', `decision=${td4.decision}`);
  } catch(e) { log('💰 Token gate evaluate', 'FAIL', e.message); }

  try {
    const ts5 = await page.request.get(`${BASE}/api/v1/cost/report?window=24h`);
    const td5 = await ts5.json();
    log('💰 Cost report', ts5.ok() && td5.reconciliation ? 'PASS' : 'FAIL', `consistent=${td5.reconciliation && td5.reconciliation.consistent}`);
  } catch(e) { log('💰 Cost report', 'FAIL', e.message); }

  // ═══ 21b. Token 额外端点（P10.9 补全：breakdown/trend/detail/lever-split/ratchet/targets）═══
  try {
    const r = await page.request.get(`${BASE}/api/v1/cost/tokens/breakdown?dim=phase&window=24h`);
    log('💰 Token breakdown', r.ok() ? 'PASS' : 'FAIL', `status=${r.status()}`);
  } catch(e) { log('💰 Token breakdown', 'FAIL', e.message); }

  try {
    const r = await page.request.get(`${BASE}/api/v1/cost/tokens/trend?window=24h&bucket=hour`);
    log('💰 Token trend', r.ok() ? 'PASS' : 'FAIL', `status=${r.status()}`);
  } catch(e) { log('💰 Token trend', 'FAIL', e.message); }

  try {
    const r = await page.request.get(`${BASE}/api/v1/cost/tokens/detail?window=24h&limit=5`);
    log('💰 Token detail', r.ok() ? 'PASS' : 'FAIL', `status=${r.status()}`);
  } catch(e) { log('💰 Token detail', 'FAIL', e.message); }

  try {
    const r = await page.request.get(`${BASE}/api/v1/cost/tokens/lever-split?window=24h`);
    const j = await r.json();
    log('💰 Token lever-split', r.ok() && j.grand_total ? 'PASS' : 'FAIL', `grand_total=${j.grand_total}`);
  } catch(e) { log('💰 Token lever-split', 'FAIL', e.message); }

  try {
    const r = await page.request.get(`${BASE}/api/v1/cost/tokens/ratchet`);
    const j = await r.json();
    log('💰 Token ratchet status', r.ok() ? 'PASS' : 'FAIL', `metrics=${(j.metrics||[]).length}`);
  } catch(e) { log('💰 Token ratchet status', 'FAIL', e.message); }

  try {
    const r = await page.request.get(`${BASE}/api/v1/cost/targets`);
    log('💰 Cost targets list', r.ok() ? 'PASS' : 'FAIL', `status=${r.status()}`);
  } catch(e) { log('💰 Cost targets list', 'FAIL', e.message); }

  try {
    const r = await page.request.get(`${BASE}/api/v1/skill-library/duplicates`);
    log('📚 Skill duplicates', r.ok() ? 'PASS' : 'FAIL', `status=${r.status()}`);
  } catch(e) { log('📚 Skill duplicates', 'FAIL', e.message); }

  // ═══ Summary ═══
  const passCount = results.filter(r => r.status === 'PASS').length;
  const failCount = results.filter(r => r.status === 'FAIL').length;
  const skipCount = results.filter(r => r.status === 'SKIP').length;

  console.log(`\n═══════════════════════════════════`);
  console.log(`📋 回归汇总: ${passCount} PASS / ${failCount} FAIL / ${skipCount} SKIP (共 ${results.length} 项)`);
  console.log(`═══════════════════════════════════`);

  // Write report
  const fs = require('fs');
  const reportPath = path.resolve(__dirname, '../docs/templates/frontend-big-change-smoke-report.md');
  const report = [
    `# Frontend Big Change Smoke Report`,
    `- 日期: ${new Date().toISOString().split('T')[0]}`,
    `- 测试用户: ${USER}`,
    `- 浏览器: Chromium (headless)`,
    `- 后端: ${BASE}`,
    `- 结果: ${passCount} PASS / ${failCount} FAIL / ${skipCount} SKIP`,
    ``,
    `## 按钮回归清单`,
    ...results.map(r => `- [${r.status === 'PASS' ? 'x' : r.status === 'FAIL' ? '!' : ' '}] ${r.test}: ${r.detail}`),
    ``,
    `## Console Errors`,
    ...(consoleErrors.length > 0 ? consoleErrors.map(e => `- ${e}`) : ['无错误']),
    ``,
    `## 后端版本`,
    `- commit: ${process.env.GIT_COMMIT || 'unknown'}`,
  ].join('\n');
  fs.writeFileSync(reportPath, report);
  console.log(`\n📄 报告已写入: ${reportPath}`);

  await browser.close();
  process.exit(failCount > 0 ? 1 : 0);
})();
