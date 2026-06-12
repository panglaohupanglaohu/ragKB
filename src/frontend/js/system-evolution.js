/**
 * AgentsGroup2026 — System Evolution Dashboard
 * Darwin Ratchet mechanism, compliance rating, audit rules,
 * evolution items, heritage ledger, and Qwen reflection lab.
 * Includes interactive 5-step evolution stepper.
 *
 * v2 — Optimized: cache layer, SSE real-time, skeletons, unified error handling
 */
'use strict';

// ═══ State & Cache ═══
let _allRules = [];
let _allItems = [];
let _panelLoaded = {};  // Track which panels have been loaded

const _panelCache = new Map();  // { key → { data, ts, ttl } }
const CACHE_TTL = {
  overview: 30000,        // 30s
  'compliance-rating': 60000,  // 60s (expensive)
  items: 15000,           // 15s
  rules: 30000,
  zones: 30000,
  trail: 15000,
  trend: 30000,
  heritage: 30000,
  ratchetMetrics: 30000,
  'evolve-skills': 15000,
  default: 30000,
};

const _evolutionState = {
  rules: null,
  items: null,
  zones: null,
  zonesActive: null,
  summary: null,
  compliance: null,
  trail: null,
  trend: null,
  history: null,
  monitoring: null,
  heritage: null,
};

// SSE state
let _sseSource = null;
let _ssePollTimer = null;
let _ssePollActive = false;

const Q = new URLSearchParams(window.location.search);
const deepLinkPanel = Q.get('panel') || '';
const deepLinkItemId = Q.get('item_id') || '';
const EVP = '/api/v1/agent-teams/evolution';

// ── Utilities ──
function el(id) { return document.getElementById(id); }
function escapeHtml(v) { return String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

// ── Unified Error-Handling Fetch ──
var _requestIdCounter = 0;
function _nextRequestId() { _requestIdCounter++; return 'se-' + Date.now().toString(36) + '-' + _requestIdCounter; }

async function safeFetch(url, options) {
  const rid = _nextRequestId();
  const opts = options || {};
  const headers = { 'X-Request-ID': rid, ...(opts.headers || {}) };
  try {
    const resp = await fetch(url, { ...opts, headers });
    if (!resp.ok) {
      let detail = '';
      try { const j = await resp.clone().json(); detail = j.detail || j.message || ''; } catch (_) {}
      const err = new Error(detail || `HTTP ${resp.status}`);
      err._requestId = rid;
      err._status = resp.status;
      throw err;
    }
    if (resp.status === 204) return null;
    return await resp.json();
  } catch (e) {
    if (e._requestId) throw e;
    const netErr = new Error('网络请求失败');
    netErr._requestId = rid;
    netErr._status = 0;
    netErr._cause = e;
    throw netErr;
  }
}

function formatError(e, context) {
  const rid = e?._requestId || 'unknown';
  const status = e?._status || 0;
  const msg = e?.message || '未知错误';
  if (status === 401 || status === 403) return `权限不足 — 请重新登录 [${rid}]`;
  if (status === 404) return `${context || '资源'}未找到 [${rid}]`;
  if (status === 0) return `网络连接失败 — 请检查后端服务是否运行 [${rid}]`;
  return `${msg} [${rid}]`;
}

function renderError(containerId, error, context, retryFn) {
  const c = typeof containerId === 'string' ? el(containerId) : containerId;
  if (!c) return;
  const msg = formatError(error, context);
  const retryBtn = retryFn ? `<button class="btn btn-sm" style="margin-top:8px" onclick="(${retryFn.toString()})()">🔄 重试</button>` : '';
  c.innerHTML = `<div style="text-align:center;padding:24px;color:var(--red)">
    <div style="font-size:13px;font-weight:600;margin-bottom:6px">${escapeHtml(msg)}</div>
    <div style="font-size:11px;color:var(--dim)">${context || ''}</div>
    ${retryBtn}
  </div>`;
}

function renderEmpty(containerId, message) {
  const c = typeof containerId === 'string' ? el(containerId) : containerId;
  if (!c) return;
  c.innerHTML = `<div style="text-align:center;padding:32px 16px;color:var(--dim);font-size:13px">
    <div style="font-size:28px;margin-bottom:8px;opacity:0.4">📭</div>
    <div>${escapeHtml(message || '暂无数据')}</div>
  </div>`;
}

// ── Cache Helpers ──
function cacheGet(key) {
  const entry = _panelCache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.ts > entry.ttl) { _panelCache.delete(key); return null; }
  return entry.data;
}

function cacheSet(key, data, ttl) {
  _panelCache.set(key, { data, ts: Date.now(), ttl: ttl || CACHE_TTL.default });
}

function cacheClear(prefix) {
  if (!prefix) { _panelCache.clear(); return; }
  for (const k of _panelCache.keys()) { if (k.startsWith(prefix)) _panelCache.delete(k); }
}

function toast(m) {
  const text = String(m ?? '');
  const shouldDecorate = /失败|错误|异常|不可用|未找到|无法|无效|请求失败/.test(text);
  const finalText = shouldDecorate && window.api?.decorateErrorMessage ? window.api.decorateErrorMessage(text) : text;
  const e = el('toast'); e.textContent = finalText; e.classList.add('show');
  setTimeout(() => e.classList.remove('show'), 2500);
}
// Button loading state helper
function btnLoading(btn, loading, originalText) {
  if (typeof btn === 'string') btn = document.querySelector(btn);
  if (!btn) return;
  if (loading) {
    btn._origText = btn.textContent;
    btn.disabled = true;
    btn.style.opacity = '0.6';
    btn.textContent = '⏳ ' + (originalText || '处理中...');
  } else {
    btn.disabled = false;
    btn.style.opacity = '';
    btn.textContent = btn._origText || originalText || btn.textContent;
  }
}
var _apiClient_se = window.api || null;
async function apiRequest(p, o) {
  const client = (window.api && typeof window.api.request === 'function') ? window.api : _apiClient_se;
  if (!client || typeof client.request !== 'function') {
    // Fallback to native fetch via safeFetch
    const method = (o?.method || 'GET').toUpperCase();
    const fetchOpts = { method };
    if (o?.headers) fetchOpts.headers = o.headers;
    if (o?.body) fetchOpts.body = o.body;
    try { return await safeFetch(p, fetchOpts); } catch (e) { toast(formatError(e, 'API请求')); return null; }
  }
  _apiClient_se = client;
  try { return await client.request(p, o); } catch (e) { return null; }
}
async function apiList(base, limit, offset) {
  const client = (window.api && typeof window.api.request === 'function') ? window.api : _apiClient_se;
  if (!client) {
    const pageLimit = limit || 50;
    const pageOffset = offset || 0;
    const sep = base.includes('?') ? '&' : '?';
    try { return await safeFetch(`${base}${sep}limit=${pageLimit}&offset=${pageOffset}`); } catch (e) { toast(formatError(e, '列表请求')); return null; }
  }
  _apiClient_se = client;
  if (typeof client.list === 'function') {
    return client.list(base, limit, offset);
  }
  const pageLimit = limit || 50;
  const pageOffset = offset || 0;
  const sep = base.includes('?') ? '&' : '?';
  return client.request(`${base}${sep}limit=${pageLimit}&offset=${pageOffset}`);
}
function collectionItems(payload) {
  if (Array.isArray(payload)) return payload;
  return Array.isArray(payload?.items) ? payload.items : [];
}
function stL(s) { return { discovered: '发现', dispatched: '已派发', in_progress: '进行中', verify_pending: '待验证', verified: '已验证', failed: '失败', closed: '已关闭' }[s] || s; }
function stColor(s) { return { discovered: 'var(--koke)', dispatched: 'var(--amber)', in_progress: 'var(--koke)', verify_pending: 'var(--shu)', verified: 'var(--lime)', failed: 'var(--red)', closed: 'var(--dim)' }[s] || 'var(--muted)'; }
function sevColor(s) { return s === 'critical' ? 'var(--red)' : s === 'high' ? 'var(--amber)' : 'var(--muted)'; }
function timeAgo(ts) { if (!ts) return '-'; const d = new Date(ts); return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
function escalationLabel(t) { return { normal: '正常', corrective: '纠正计划', review: '管理复核', hold: '冻结处理' }[t] || t || ''; }
function renderItemVerifyMeta(item) {
  const parts = [];
  if (item.verify_test_name) parts.push(`verify: ${escapeHtml(item.verify_test_name)}`);
  if (item.retry_count) parts.push(`retry ${item.retry_count}/${item.max_retries || 0}`);
  if (item.consecutive_failures) parts.push(`fail ${item.consecutive_failures}`);
  if (item.escalation_tier && item.escalation_tier !== 'normal') parts.push(`升级: ${escapeHtml(escalationLabel(item.escalation_tier))}`);
  if (item.verify_detail) parts.push(escapeHtml(item.verify_detail));
  if (!parts.length) return '';
  return `<div style="font-size:11px;color:var(--dim);margin-top:4px;line-height:1.6">${parts.join(' · ')}</div>`;
}
function evidenceSummary(run) {
  if (window.evidenceRuns && typeof window.evidenceRuns.summarize === 'function') {
    return window.evidenceRuns.summarize(run);
  }
  const runtime = run?.runtime || {};
  return {
    id: run?.evidence_id || '',
    type: run?.evidence_type || '',
    status: run?.status || '',
    runtimeLabel: [runtime.mode, runtime.component || runtime.tool_name].filter(Boolean).join(' / '),
    command: run?.command || '',
    exitCode: run?.exit_code,
    artifact: run?.artifact_dir || '',
    requestId: run?.request_id || '',
  };
}
function renderEvidenceRuns(runs) {
  runs = Array.isArray(runs) ? runs : [];
  if (!runs.length) {
    return '<div style="font-size:12px;color:var(--dim);padding:8px 0">暂无关联 EvidenceRun</div>';
  }
  return runs.map(run => {
    const s = evidenceSummary(run);
    const statusColor = s.status === 'passed' || s.status === 'verified' ? 'var(--lime)' : s.status === 'failed' || s.status === 'blocked' ? 'var(--red)' : 'var(--amber)';
    return `<div style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.06)">
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <span style="font-family:var(--font-mono);font-size:11px;color:var(--koke)">${escapeHtml(s.id)}</span>
        <span class="chip" style="font-size:10px">${escapeHtml(s.type)}</span>
        <span style="font-size:11px;color:${statusColor};font-weight:700">${escapeHtml(s.status)}</span>
        ${s.requestId ? `<span style="font-size:10px;color:var(--dim);font-family:var(--font-mono)">req ${escapeHtml(s.requestId)}</span>` : ''}
      </div>
      <div style="font-size:11px;color:var(--sumi-2);line-height:1.7;margin-top:4px">
        ${s.runtimeLabel ? `runtime: ${escapeHtml(s.runtimeLabel)} · ` : ''}exit: ${s.exitCode ?? '—'}${s.command ? ` · cmd: <code>${escapeHtml(s.command)}</code>` : ''}
      </div>
      ${s.artifact ? `<div style="font-size:10px;color:var(--dim);font-family:var(--font-mono);margin-top:3px">artifact: ${escapeHtml(s.artifact)}</div>` : ''}
    </div>`;
  }).join('');
}
function kv(label, value) {
  return `<div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04)"><div style="font-size:10px;color:var(--dim);text-transform:uppercase">${label}</div><div style="font-size:12px;color:var(--sumi-2);line-height:1.7;white-space:pre-wrap">${escapeHtml(value || '—')}</div></div>`;
}

// ── Panel Switch ──
function showSkeleton(name) {
  const panel = el('panel-' + name);
  if (!panel) return;
  // Find skeleton container or the first major content area
  const skelId = 'skel-' + name;
  let skel = el(skelId);
  if (!skel) {
    skel = document.createElement('div');
    skel.id = skelId;
    skel.className = 'skeleton-panel';
    skel.innerHTML = '<div class="skel-row"><div class="skel-block" style="width:60%;height:20px"></div></div><div class="skel-row"><div class="skel-block" style="width:100%;height:60px"></div></div><div class="skel-row"><div class="skel-block" style="width:45%;height:16px"></div><div class="skel-block" style="width:45%;height:16px"></div></div>';
    panel.insertBefore(skel, panel.firstChild);
  }
  skel.style.display = 'block';
  // Hide content containers while loading
  panel.querySelectorAll('.card-grid, .section, #ratchet-flow, #items-table, #rules-grid, #trail-list, #trend-data, #heritage-list, #zones-all, #zones-active, #history-list, #monitoring-data').forEach(el => { el._wasVisible = el.style.display !== 'none'; });
}

function hideSkeleton(name) {
  const skel = el('skel-' + name);
  if (skel) skel.style.display = 'none';
}

function switchPanel(name) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.sb-nav a').forEach(a => { a.classList.remove('active'); a.setAttribute('aria-selected', 'false'); });
  const panel = el('panel-' + name);
  if (panel) panel.classList.add('active');

  const links = document.querySelectorAll('.sb-nav a');
  const map = { overview: 0, ratchet: 1, 'evolve-lab': 2, 'rules-zones': 3, items: 4, trail: 5, trend: 6 };
  if (map[name] !== undefined && links[map[name]]) {
    links[map[name]].classList.add('active');
    links[map[name]].setAttribute('aria-selected', 'true');
  }
  const titles = { overview: '演进概览', ratchet: '达尔文棘轮', 'evolve-lab': '🧬 技能演化', 'rules-zones': '规则与区域', items: '演进条目', trail: '审计轨迹', trend: '趋势分析' };
  el('panel-title').textContent = titles[name] || name;

  // Check cache first
  const cacheKey = 'panel-' + name;
  const cached = cacheGet(cacheKey);
  if (cached && _panelLoaded[name]) {
    // Panel already loaded with fresh data — skip re-fetch
    return;
  }

  // Show skeleton for panels that load data
  const needsSkeleton = ['overview', 'ratchet', 'rules-zones', 'items', 'trail', 'trend'];
  if (needsSkeleton.includes(name)) showSkeleton(name);

  const alwaysRefresh = ['overview'];
  if (!_panelLoaded[name] || alwaysRefresh.includes(name)) {
    _panelLoaded[name] = true;
    if (name === 'overview') loadOverview();
    else if (name === 'ratchet') loadHeritage();
    else if (name === 'evolve-lab') loadEvolveLab();
    else if (name === 'rules-zones') { loadRules(); loadZones(); }
    else if (name === 'items') loadItems();
    else if (name === 'trail') loadTrail();
    else if (name === 'trend') loadTrend();
  }
}

// ── Overview ──
async function loadOverview() {
  try {
    const [summary, compliance, itemsPayload, zones] = await Promise.all([
      apiRequest(`${EVP}/summary`), apiRequest(`${EVP}/compliance-rating`), apiList(`${EVP}/items`, 50, 0), apiRequest(`${EVP}/zones/active`)
    ]);
    const items = collectionItems(itemsPayload);

    // Update state
    _evolutionState.summary = summary;
    _evolutionState.compliance = compliance;
    _evolutionState.zonesActive = zones;

    // Compliance Rating
    const rc = el('ov-rating');
    if (compliance) {
      const g = compliance.grade || '?', s = compliance.score ?? 0;
      const gc = { A: 'var(--lime)', B: 'var(--koke)', C: 'var(--amber)', D: 'var(--kitsune)', E: 'var(--red)' }[g] || 'var(--muted)';
      rc.innerHTML = `<div class="stat-card" style="grid-column:span 2"><div class="gauge-wrap">
        <div class="gauge-ring"><svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="none" stroke="var(--groove)" stroke-width="3"/><circle cx="18" cy="18" r="16" fill="none" stroke="${gc}" stroke-width="3" stroke-dasharray="${s} ${100 - s}" stroke-linecap="round" style="transform:rotate(-90deg);transform-origin:center"/></svg><div class="gauge-grade" style="color:${gc}">${g}</div></div>
        <div><div class="label">DNV 合规评级</div><div class="value" style="font-size:20px;color:${gc}">${s}/100</div><div class="sub">${escapeHtml(compliance.description || '')}</div></div>
      </div></div>
      <div class="stat-card"><div class="label">升级层级</div><div class="value" style="font-size:16px">${escapeHtml(compliance.escalation_tier || 'normal')}</div><div class="sub">DNV SEEMP Part III</div></div>`;
    } else {
      renderEmpty(rc, '暂无合规评级数据');
    }

    // Stats
    if (summary) {
      const bs = summary.by_status || {}, bd = summary.by_domain || {};
      const bsv = summary.by_severity || {}, bop = summary.by_operational_domain || {};
      el('ov-stats').innerHTML = `
        <div class="stat-card"><div class="label"><span class="seal">规</span> 审查规则</div><div class="value">${summary.audit_rules_count || 0}</div><div class="sub">验证函数 ${summary.verify_tests_registered || 0}</div></div>
        <div class="stat-card"><div class="label"><span class="seal seal-shu">项</span> 演进项</div><div class="value">${summary.total_items || 0}</div><div class="sub">${Object.entries(bs).map(([k, v]) => stL(k) + ': ' + v).join(' · ') || '无'}</div></div>
        <div class="stat-card"><div class="label">📚 域分布</div><div class="value" style="font-size:13px">${Object.entries(bd).map(([k, v]) => k + ' ' + v).join(' · ') || '-'}</div></div>
        <div class="stat-card"><div class="label">⚠ 严重度</div><div class="value" style="font-size:13px">${Object.entries(bsv).map(([k, v]) => `<span style="color:${sevColor(k)}">${k}: ${v}</span>`).join(' · ') || '-'}</div></div>
        <div class="stat-card"><div class="label">🏢 运营域</div><div class="value" style="font-size:11px;line-height:1.6">${Object.entries(bop).map(([k, v]) => k.replace(/_/g, ' ') + ': ' + v).join('<br>') || '-'}</div></div>`;
      el('panel-badge').textContent = `${summary.total_items || 0} 项`;
    }

    // Mini ratchet
    buildMiniRatchet();

    // Recent items (top 10)
    if (items && items.length) {
      const recent = items.slice(0, 10);
      el('ov-items').innerHTML = `<div class="tbl-wrapper"><table class="tbl"><thead><tr><th>ID</th><th>标题</th><th>域</th><th>严重度</th><th>状态</th><th>操作</th></tr></thead><tbody>${recent.map(i => `<tr>
        <td style="font-family:var(--font-mono);font-size:11px">${escapeHtml(i.id?.slice(0, 8) || '')}</td>
        <td><b>${escapeHtml(i.title)}</b></td>
        <td><span class="chip" style="font-size:10px">${escapeHtml(i.audit_domain || '')}</span></td>
        <td style="color:${sevColor(i.severity)}">${escapeHtml(i.severity || '')}</td>
        <td><span style="color:${stColor(i.status)};font-weight:600;font-size:12px">${stL(i.status)}</span></td>
        <td style="white-space:nowrap">${itemActions(i)}</td>
      </tr>`).join('')}</tbody></table></div>
      ${items.length > 10 ? `<button class="btn btn-sm" style="margin-top:8px" onclick="switchPanel('items')">查看全部 (${items.length})</button>` : ''}`;
    } else {
      renderEmpty('ov-items', '暂无演进条目 — 点击「运行审查」开始');
    }

    cacheSet('panel-overview', true, CACHE_TTL.overview);
  } catch (e) {
    renderError('ov-rating', e, '概览面板加载失败', loadOverview);
  }
  hideSkeleton('overview');
}

function buildMiniRatchet() {
  const steps = [
    { id: 'ov-r-audit', label: '审查', sub: 'AUDIT' },
    { id: 'ov-r-dispatch', label: '派发', sub: 'DISPATCH' },
    { id: 'ov-r-verify', label: '验证', sub: 'VERIFY' },
    { id: 'ov-r-close', label: '关闭', sub: 'CLOSE' }
  ];
  el('ov-ratchet').innerHTML = steps.map((s, i) =>
    `<div class="ratchet-node"><div class="ratchet-dot" id="${s.id}">${s.label[0]}</div><div class="ratchet-label">${s.label}</div><div class="ratchet-sublabel">${s.sub}</div></div>${i < 3 ? '<div class="ratchet-connector" id="ov-rc-' + (i + 1) + '"></div>' : ''}`
  ).join('');
}

// ── Items ──
let _itemSortKey = '';
let _itemSortDir = 1;  // 1=asc, -1=desc

function sortItems(items, key, dir) {
  if (!key) return items;
  return [...items].sort((a, b) => {
    let va = a[key] ?? '', vb = b[key] ?? '';
    if (key === 'severity') {
      const order = { critical: 4, high: 3, medium: 2, low: 1 };
      va = order[va] || 0; vb = order[vb] || 0;
    }
    if (va < vb) return -1 * dir;
    if (va > vb) return 1 * dir;
    return 0;
  });
}

function renderSortIndicator(key) {
  if (_itemSortKey !== key) return ' ↕';
  return _itemSortDir === 1 ? ' ↑' : ' ↓';
}

async function loadItems() {
  try {
    const sf = el('item-status-filter')?.value || '';
    const df = el('item-domain-filter')?.value || '';
    let url = `${EVP}/items`;
    if (sf) url += `?status=${encodeURIComponent(sf)}`;
    const itemsPayload = await apiList(url, 50, 0);
    _allItems = collectionItems(itemsPayload);
    // Populate domain filter
    const domains = [...new Set(_allItems.map(i => i.audit_domain).filter(Boolean))];
    const dSel = el('item-domain-filter');
    const curDom = dSel.value;
    if (dSel.options.length <= 1) {
      domains.forEach(d => { const o = document.createElement('option'); o.value = d; o.textContent = d; dSel.appendChild(o); });
    }
    let filtered = _allItems;
    if (df) filtered = filtered.filter(i => i.audit_domain === df);
    // Apply sort
    if (_itemSortKey) filtered = sortItems(filtered, _itemSortKey, _itemSortDir);
    el('item-count').textContent = `${filtered.length} 条`;

    if (filtered.length) {
      const thClick = (key, label) => `<th style="cursor:pointer" onclick="event.stopPropagation();_itemSortKey='${key}';_itemSortDir=_itemSortKey==='${key}'&&_itemSortDir===1?-1:1;loadItems()" title="点击排序">${label}${renderSortIndicator(key)}</th>`;
      el('items-table').innerHTML = `<div class="tbl-wrapper"><table class="tbl"><thead><tr>${thClick('id','ID')}${thClick('title','标题')}<th>域</th>${thClick('severity','严重度')}<th>状态 / 验证</th><th>目标通道</th><th>参考标准</th><th>操作</th></tr></thead><tbody>${filtered.map(i => `<tr id="evo-item-${escapeHtml(i.id || '')}"${i.id === deepLinkItemId ? ' style="outline:1px solid var(--koke);background:rgba(107,196,127,0.06)"' : ''}>
        <td style="font-family:var(--font-mono);font-size:11px" title="${escapeHtml(i.id || '')}">${escapeHtml(i.id?.slice(0, 8) || '')}</td>
        <td><b>${escapeHtml(i.title)}</b><br><span style="font-size:11px;color:var(--dim)">${escapeHtml(i.description?.slice(0, 60) || '')}</span></td>
        <td><span class="chip" style="font-size:10px">${escapeHtml(i.audit_domain || '')}</span></td>
        <td style="color:${sevColor(i.severity)}">${escapeHtml(i.severity || '')}</td>
        <td><span style="color:${stColor(i.status)};font-weight:600;font-size:12px">${stL(i.status)}</span>${renderItemVerifyMeta(i)}</td>
        <td style="font-size:12px">${escapeHtml(i.target_channel || '')}</td>
        <td style="font-size:11px;color:var(--dim)">${escapeHtml(i.reference_standard || '')}</td>
        <td style="white-space:nowrap">${itemActions(i)}</td>
      </tr>`).join('')}</tbody></table></div>`;
      if (deepLinkItemId) {
        requestAnimationFrame(() => {
          const row = document.getElementById(`evo-item-${deepLinkItemId}`);
          if (row) row.scrollIntoView({ block: 'center', behavior: 'smooth' });
          openItemDetail(deepLinkItemId);
        });
      }
    } else {
      renderEmpty('items-table', '暂无演进条目');
    }
    cacheSet('panel-items', true, CACHE_TTL.items);
  } catch (e) {
    renderError('items-table', e, '条目列表加载失败', loadItems);
  }
  hideSkeleton('items');
}

function itemActions(item) {
  const s = item.status;
  const detail = `<button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="openItemDetail('${item.id}')">详情</button>`;
  if (s === 'discovered') return `${detail} <button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="markProgress('${item.id}')">开始</button>`;
  if (s === 'dispatched') return `${detail} <button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="markProgress('${item.id}')">开始</button>`;
  if (s === 'in_progress') return `${detail} <button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="openItemDetail('${item.id}', 'complete')">完成</button>`;
  if (s === 'verify_pending') return `${detail} <button class="btn btn-sm btn-primary" style="padding:2px 8px;font-size:11px" onclick="verifyItem('${item.id}')">验证</button>`;
  if (s === 'verified') return `${detail} <button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="closeItem('${item.id}')">关闭</button>`;
  if (s === 'failed') return `${detail} <span style="font-size:11px;color:var(--shu)">✗ 失败</span>`;
  if (s === 'closed') return `${detail} <span style="font-size:11px;color:var(--dim)">已关闭</span>`;
  return detail;
}

function renderBuildCompleteForm(item) {
  if (item.status !== 'in_progress') return '';
  return `<div style="margin-top:12px;padding:12px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.03)">
    <div class="section-title" style="margin-bottom:8px">构建完成证据</div>
    <div style="font-size:11px;color:var(--dim);line-height:1.6;margin-bottom:8px">进入验证前必须记录本次构建产生的代码/配置变更或 artifact 目录。</div>
    <label style="display:block;font-size:10px;color:var(--dim);margin-bottom:4px">代码或配置变更（一行一个）</label>
    <textarea id="build-complete-code-changes" class="fi" rows="3" style="width:100%;resize:vertical" placeholder="例如：src/backend/agents/router.py 调整路由反馈记录"></textarea>
    <label style="display:block;font-size:10px;color:var(--dim);margin:8px 0 4px">Artifact 目录</label>
    <input id="build-complete-artifact-dir" class="fi" style="width:100%" placeholder="例如：storage/evolution_runs/${escapeHtml(item.id)}">
    <div style="display:flex;gap:8px;align-items:center;margin-top:10px">
      <button class="btn btn-sm btn-primary" onclick="submitBuildComplete('${item.id}')">提交完成证据</button>
      <span id="build-complete-status" style="font-size:11px;color:var(--dim)"></span>
    </div>
  </div>`;
}

async function openItemDetail(itemId, mode) {
  const panel = el('item-detail-panel');
  if (!panel) return;
  panel.style.display = 'block';
  panel.innerHTML = '<div style="font-size:12px;color:var(--muted)">加载演进证据...</div>';
  let item = await apiRequest(`${EVP}/items/${encodeURIComponent(itemId)}`);
  if (!item) {
    panel.innerHTML = '<div style="font-size:12px;color:var(--shu)">详情加载失败</div>';
    return;
  }
  let evidenceRuns = item.evidence_runs || [];
  if (!evidenceRuns.length && window.evidenceRuns?.byObject) {
    evidenceRuns = await window.evidenceRuns.byObject('evolution', itemId, { limit: 20 });
  }
  const buildArtifacts = item.build_artifacts || {};
  panel.innerHTML = `
    <div class="section-title" style="justify-content:space-between">
      <span>演进项证据详情</span>
      <button class="btn btn-sm" onclick="el('item-detail-panel').style.display='none'">收起</button>
    </div>
    <div style="display:grid;grid-template-columns:minmax(0,1.1fr) minmax(280px,.9fr);gap:16px">
      <div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px">
          <span style="font-family:var(--font-mono);color:var(--koke);font-size:12px">${escapeHtml(item.id)}</span>
          <span style="color:${stColor(item.status)};font-weight:700;font-size:12px">${stL(item.status)}</span>
          <span class="chip" style="font-size:10px">${escapeHtml(item.audit_domain || '')}</span>
          <span style="font-size:11px;color:${sevColor(item.severity)}">${escapeHtml(item.severity || '')}</span>
        </div>
        <h3 style="margin:0 0 8px 0;font-size:16px;color:var(--sumi)">${escapeHtml(item.title || '')}</h3>
        ${(item.metadata?.source_plaza_id || item.source_plaza_id) ? `<div style="margin-bottom:8px"><a href="/plaza.html?plaza_id=${encodeURIComponent(item.metadata?.source_plaza_id || item.source_plaza_id)}&discussion_id=${encodeURIComponent(item.metadata?.source_discussion_id || item.source_discussion_id || '')}" style="font-size:11px;color:var(--lime);text-decoration:none">🏛️ 来源: 议事厅讨论 ← 返回</a></div>` : ''}
        ${kv('发现问题', item.current_behavior || item.description)}
        ${kv('期望行为', item.expected_behavior)}
        ${kv('参考标准', item.reference_standard)}
        ${kv('执行计划 / Build Task', item.build_task_id || (item.source_task_ids || []).join(', '))}
        ${kv('代码变更', (item.code_changes || []).join('\\n'))}
        ${kv('Artifact', item.artifact_dir || buildArtifacts.artifact_dir || '')}
        ${kv('验证结论', item.verify_detail || item.verify_result || '')}
        ${item.close_reason || item.close_verify_conclusion ? `${kv('关闭理由', item.close_reason)}${kv('关闭验证结论', item.close_verify_conclusion)}` : ''}
        ${renderBuildCompleteForm(item)}
      </div>
      <div>
        <div class="section-title">EvidenceRun</div>
        ${renderEvidenceRuns(evidenceRuns)}
      </div>
    </div>`;
  if (mode === 'complete') {
    const input = el('build-complete-code-changes') || el('build-complete-artifact-dir');
    if (input) input.focus();
  }
}

async function verifyItem(itemId) {
  const r = await apiRequest(`${EVP}/items/${encodeURIComponent(itemId)}/verify`, { method: 'POST' });
  if (r) {
    toast(`验证完成: ${r.count || 0} 项`);
    await openItemDetail(itemId);
    refreshCurrent();
  } else {
    toast('验证失败');
  }
}

async function closeItem(itemId) {
  const reason = prompt('关闭理由（必填，用于审计）') || '';
  if (!reason.trim()) { toast('关闭失败：需要关闭理由'); return; }
  const verifyConclusion = prompt('验证结论（必填，会写入演进记录）') || '';
  if (!verifyConclusion.trim()) { toast('关闭失败：需要验证结论'); return; }
  const r = await apiRequest(`${EVP}/items/${encodeURIComponent(itemId)}/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason, verify_conclusion: verifyConclusion }),
  });
  if (r) {
    toast('已关闭并记录理由');
    await openItemDetail(itemId);
    refreshCurrent();
  } else {
    toast('关闭失败');
  }
}

async function markProgress(itemId) {
  const r = await apiRequest(`${EVP}/items/${itemId}/progress`, { method: 'POST' });
  if (r) { toast('已标记为进行中'); refreshCurrent(); } else toast('操作失败');
}
async function submitBuildComplete(itemId) {
  const changesText = (el('build-complete-code-changes')?.value || '').trim();
  const artifactDir = (el('build-complete-artifact-dir')?.value || '').trim();
  const codeChanges = changesText.split('\n').map(v => v.trim()).filter(Boolean);
  const statusEl = el('build-complete-status');
  if (!codeChanges.length && !artifactDir) {
    if (statusEl) statusEl.textContent = '请先填写代码变更或 artifact 目录';
    toast('完成失败：缺少构建证据');
    return;
  }
  if (statusEl) statusEl.textContent = '提交中...';
  await markComplete(itemId, { code_changes: codeChanges, artifact_dir: artifactDir });
}

async function markComplete(itemId, evidence) {
  if (!evidence) {
    await openItemDetail(itemId, 'complete');
    return;
  }
  const r = await apiRequest(`${EVP}/items/${itemId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(evidence),
  });
  if (r) {
    toast('已记录构建证据，等待验证');
    await openItemDetail(itemId);
    refreshCurrent();
  } else {
    const statusEl = el('build-complete-status');
    if (statusEl) statusEl.textContent = '提交失败，请查看错误提示';
    toast('操作失败');
  }
}

// ── Rules ──
async function loadRules() {
  try {
    if (!_allRules.length) _allRules = collectionItems(await apiList(`${EVP}/rules`, 50, 0));
    // Populate domain filter
    const domains = [...new Set(_allRules.map(r => r.domain).filter(Boolean))];
    const dSel = el('rule-domain-filter');
    if (dSel.options.length <= 1) {
      domains.forEach(d => { const o = document.createElement('option'); o.value = d; o.textContent = d; dSel.appendChild(o); });
    }
    renderRules();
    cacheSet('panel-rules-zones', true, CACHE_TTL.rules);
  } catch (e) {
    renderError('rules-grid', e, '规则列表加载失败', loadRules);
  }
  hideSkeleton('rules-zones');
}

let _ruleSearchTerm = '';

function renderRules() {
  const df = el('rule-domain-filter')?.value || '';
  const sf = el('rule-severity-filter')?.value || '';
  const searchTerm = (_ruleSearchTerm || '').toLowerCase();
  let filtered = _allRules;
  if (df) filtered = filtered.filter(r => r.domain === df);
  if (sf) filtered = filtered.filter(r => r.severity === sf);
  if (searchTerm) {
    filtered = filtered.filter(r =>
      (r.title || '').toLowerCase().includes(searchTerm) ||
      (r.id || '').toLowerCase().includes(searchTerm) ||
      (r.reference || '').toLowerCase().includes(searchTerm) ||
      (r.domain || '').toLowerCase().includes(searchTerm)
    );
  }
  el('rule-count').textContent = `${filtered.length} 条规则`;
  if (filtered.length) {
    el('rules-grid').innerHTML = filtered.map(r => `<div class="rule-card" role="listitem" aria-label="${escapeHtml(r.title)}">
      <div class="r-head"><span class="r-id">${escapeHtml(r.id)}</span><span class="chip" style="font-size:10px">${escapeHtml(r.domain)}</span></div>
      <div class="r-title">${escapeHtml(r.title)}</div>
      <div class="r-ref">${escapeHtml(r.reference || '')}</div>
      <div class="r-meta"><span style="color:${sevColor(r.severity)}">${escapeHtml(r.severity)}</span> · ${escapeHtml(r.target_channel || '')}${r.operational_domain ? ' · ' + r.operational_domain.replace(/_/g, ' ') : ''}${r.rating_weight ? ' · 权重 ' + r.rating_weight : ''}</div>
    </div>`).join('');
  } else {
    renderEmpty('rules-grid', searchTerm ? `未找到匹配 "${escapeHtml(_ruleSearchTerm)}" 的规则` : '暂无审查规则');
  }
}

// ── Zones ──
async function loadZones() {
  try {
    const cachedZ = cacheGet('zones-data');
    const cachedZA = cacheGet('zones-active-data');
    if (cachedZ && cachedZA) {
      renderZonesUI(cachedZ, cachedZA);
      return;
    }
    const [allZones, activeZones] = await Promise.all([
      apiRequest(`${EVP}/zones`), apiRequest(`${EVP}/zones/active`)
    ]);
    cacheSet('zones-data', allZones, CACHE_TTL.zones);
    cacheSet('zones-active-data', activeZones, CACHE_TTL.zones);
    renderZonesUI(allZones, activeZones);
  } catch (e) {
    renderError('zones-all', e, '合规区域加载失败', loadZones);
  }
}

function renderZonesUI(allZones, activeZones) {
  if (allZones && allZones.length) {
    el('zones-all').innerHTML = allZones.map(z => `<div class="stat-card">
      <div class="label" style="font-weight:600">${escapeHtml(z.name || z.zone_id || z.id || '')}</div>
      <div style="font-size:12px;color:var(--sumi-2);margin-top:4px">${escapeHtml(z.zone_type || '')}</div>
      ${z.extra_requirements ? `<div style="font-size:11px;color:var(--dim);margin-top:4px">${escapeHtml(z.extra_requirements)}</div>` : ''}
      ${z.activated_rule_ids ? `<div style="font-size:10px;color:var(--koke);margin-top:6px;font-family:var(--font-mono)">${z.activated_rule_ids.length} 规则</div>` : ''}
    </div>`).join('');
  } else {
    renderEmpty('zones-all', '暂无合规区域');
  }
  if (activeZones && activeZones.length) {
    el('zones-active').innerHTML = activeZones.map(z => `<div class="zone-badge"><b>${escapeHtml(z.name || z.zone_id || '')}</b>${z.standards ? ` · ${z.standards.length} 标准` : ''}</div>`).join('');
  } else {
    renderEmpty('zones-active', '无活跃区域');
  }
}

// ── Audit Trail ──
let _trailOffset = 0;
const _trailPageSize = 50;

async function loadTrail(reset) {
  try {
    if (reset) { _trailOffset = 0; el('trail-list').innerHTML = ''; }
    const tf = el('trail-type-filter')?.value || '';
    let url = `${EVP}/audit-trail`;
    if (tf) url += `?event_type=${encodeURIComponent(tf)}`;
    const trail = collectionItems(await apiList(url, _trailPageSize, _trailOffset));
    if (reset) el('trail-list').innerHTML = '';
    if (trail && trail.length) {
      const html = trail.map(e => `<div class="audit-entry">
        <span class="ae-time">${timeAgo(e.timestamp)}</span>
        <span class="ae-type" style="color:${stColor(e.event_type)}">${escapeHtml(e.event_type || '')}</span>
        <span class="ae-detail">${escapeHtml(e.detail || '')}${e.rule_id ? ' · ' + e.rule_id : ''}${e.item_id ? ' · ' + e.item_id.slice(0, 8) : ''}</span>
      </div>`).join('');
      el('trail-list').insertAdjacentHTML('beforeend', html);
      _trailOffset += trail.length;
      // Show load more button
      const moreBtn = el('trail-more');
      if (trail.length >= _trailPageSize) {
        if (moreBtn) moreBtn.style.display = 'block';
        else {
          const btn = document.createElement('button');
          btn.id = 'trail-more';
          btn.className = 'btn btn-sm';
          btn.style.cssText = 'margin-top:12px;width:100%';
          btn.textContent = '加载更多...';
          btn.onclick = () => loadTrail(false);
          el('trail-list').insertAdjacentElement('afterend', btn);
        }
      } else {
        if (moreBtn) moreBtn.style.display = 'none';
        if (reset && !trail.length) renderEmpty('trail-list', '暂无审计记录');
      }
    } else if (reset) {
      renderEmpty('trail-list', '暂无审计记录');
    }
    cacheSet('panel-trail', true, CACHE_TTL.trail);
  } catch (e) {
    renderError('trail-list', e, '审计轨迹加载失败', () => loadTrail(true));
  }
  hideSkeleton('trail');
}

// ── Trend ──
function renderTrendChart(scores) {
  if (!scores || !scores.length) return '<div class="trend-chart">暂无趋势数据</div>';

  const W = 600, H = 200, pad = { top: 20, right: 20, bottom: 30, left: 50 };
  const pw = W - pad.left - pad.right, ph = H - pad.top - pad.bottom;

  const vals = scores.map(s => typeof s === 'object' ? (s.score ?? s.value ?? 0) : Number(s));
  const labels = scores.map((s, i) => typeof s === 'object' ? (s.label || s.date || i) : i);
  const minVal = Math.min(...vals, 0); const maxVal = Math.max(...vals, 100);
  const range = maxVal - minVal || 1;

  const xScale = (i) => pad.left + (i / Math.max(vals.length - 1, 1)) * pw;
  const yScale = (v) => pad.top + ph - ((v - minVal) / range) * ph;

  // Build path
  const points = vals.map((v, i) => `${xScale(i).toFixed(1)},${yScale(v).toFixed(1)}`).join(' ');

  // Grid lines
  const gridLines = [];
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (ph / 4) * i;
    gridLines.push(`<line x1="${pad.left}" y1="${y}" x2="${W - pad.right}" y2="${y}" stroke="var(--groove)" stroke-width="0.5"/>`);
  }

  // X-axis labels (show max 6)
  const xLabels = [];
  const step = Math.max(1, Math.floor(labels.length / 6));
  for (let i = 0; i < labels.length; i += step) {
    xLabels.push(`<text x="${xScale(i).toFixed(1)}" y="${H - 6}" text-anchor="middle" font-size="9" fill="var(--dim)">${escapeHtml(String(labels[i]).slice(0, 8))}</text>`);
  }
  // Always show last label
  if (labels.length > 1 && (labels.length - 1) % step !== 0) {
    xLabels.push(`<text x="${xScale(labels.length - 1).toFixed(1)}" y="${H - 6}" text-anchor="middle" font-size="9" fill="var(--dim)">${escapeHtml(String(labels[labels.length - 1]).slice(0, 8))}</text>`);
  }

  // Y-axis labels
  const yLabels = [];
  for (let i = 0; i <= 4; i++) {
    const v = minVal + (range / 4) * i;
    yLabels.push(`<text x="${pad.left - 6}" y="${yScale(v).toFixed(1) + 3}" text-anchor="end" font-size="9" fill="var(--dim)">${Math.round(v)}</text>`);
  }

  // Fill area
  const areaPoints = `${xScale(0)},${pad.top + ph} ${points} ${xScale(vals.length - 1)},${pad.top + ph}`;

  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;max-width:${W}px;height:auto" role="img" aria-label="合规分数趋势图">
    <rect width="${W}" height="${H}" fill="var(--ishi)" rx="2"/>
    ${gridLines.join('')}
    ${yLabels.join('')}
    ${xLabels.join('')}
    <polygon points="${areaPoints}" fill="rgba(107,196,127,0.08)"/>
    <polyline points="${points}" fill="none" stroke="var(--koke)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    ${vals.map((v, i) => `<circle cx="${xScale(i).toFixed(1)}" cy="${yScale(v).toFixed(1)}" r="3" fill="var(--koke)" stroke="var(--shironeri)" stroke-width="1"><title>${escapeHtml(String(labels[i]))}: ${Math.round(v)}</title></circle>`).join('')}
  </svg>`;
}

async function loadTrend() {
  try {
    const [trend, historyPayload, monitoring] = await Promise.all([
      apiRequest(`${EVP}/trend`), apiList(`${EVP}/history`, 50, 0), apiRequest(`${EVP}/monitoring`)
    ]);
    const history = collectionItems(historyPayload);

    // Trend + SVG chart
    if (trend) {
      const scores = trend.scores || trend.data || [];
      let chartHtml = '';
      if (scores.length) {
        chartHtml = renderTrendChart(scores);
        el('trend-data').innerHTML = `<div class="card-grid">
          ${trend.current_score !== undefined ? `<div class="stat-card"><div class="label">当前分数</div><div class="value">${trend.current_score}</div></div>` : ''}
          ${trend.trend_direction ? `<div class="stat-card"><div class="label">趋势方向</div><div class="value" style="font-size:16px">${escapeHtml(trend.trend_direction)}</div></div>` : ''}
          ${trend.improvement_rate !== undefined ? `<div class="stat-card"><div class="label">改善率</div><div class="value" style="font-size:16px">${trend.improvement_rate}%</div></div>` : ''}
        </div>
        <div style="margin-top:12px">${chartHtml}</div>`;
      } else if (typeof trend === 'object') {
        el('trend-data').innerHTML = `<div class="trend-chart"><pre style="font-size:11px;text-align:left;white-space:pre-wrap">${escapeHtml(JSON.stringify(trend, null, 2))}</pre></div>`;
      }
    } else {
      renderEmpty(el('trend-data'), '暂无趋势数据');
    }

    // History
    if (history && history.length) {
      el('history-list').innerHTML = `<div class="tbl-wrapper"><table class="tbl"><thead><tr><th>时间</th><th>通过</th><th>失败</th><th>总计</th></tr></thead><tbody>${history.slice(0, 20).map(h => `<tr>
        <td style="font-family:var(--font-mono);font-size:11px">${timeAgo(h.timestamp || h.run_at)}</td>
        <td style="color:var(--koke)">${h.passed || 0}</td>
        <td style="color:var(--shu)">${h.failed || 0}</td>
        <td>${h.total || (h.passed || 0) + (h.failed || 0)}</td>
      </tr>`).join('')}</tbody></table></div>`;
    } else {
      renderEmpty('history-list', '暂无审查历史');
    }

    // Monitoring
    if (monitoring) {
      el('monitoring-data').innerHTML = `
        <div class="stat-card"><div class="label">监控状态</div><div class="value" style="font-size:16px">${monitoring.active ? '✓ 运行中' : '⏸ 停止'}</div></div>
        ${monitoring.last_check ? `<div class="stat-card"><div class="label">上次检查</div><div class="value" style="font-size:14px">${timeAgo(monitoring.last_check)}</div></div>` : ''}
        ${monitoring.interval_seconds ? `<div class="stat-card"><div class="label">检查间隔</div><div class="value" style="font-size:14px">${monitoring.interval_seconds}s</div></div>` : ''}`;
    }
    cacheSet('panel-trend', true, CACHE_TTL.trend);
  } catch (e) {
    renderError(el('trend-data'), e, '趋势数据加载失败', loadTrend);
  }
  hideSkeleton('trend');
}

// ── Heritage (Ratchet Lock ledger) ──
async function loadHeritage() {
  try {
    // Heritage = verified + closed items (ratchet-locked improvements)
    const [verifiedPayload, closedPayload] = await Promise.all([
      apiRequest(`${EVP}/items?status=verified`), apiRequest(`${EVP}/items?status=closed`)
    ]);
    const verified = collectionItems(verifiedPayload);
    const closed = collectionItems(closedPayload);
    const heritage = [...(verified || []), ...(closed || [])].sort((a, b) => (b.closed_at || b.completed_at || '').localeCompare(a.closed_at || a.completed_at || ''));
    el('heritage-count').textContent = `${heritage.length} 条锁定记录`;

    if (heritage.length) {
      el('heritage-list').innerHTML = heritage.map(h => `<div class="heritage-item">
        <div>
          <div class="h-title">🔒 ${escapeHtml(h.title)}</div>
          <div class="h-meta">${escapeHtml(h.audit_domain || '')} · ${escapeHtml(h.reference_standard || '')} · ${timeAgo(h.closed_at || h.completed_at)}</div>
        </div>
        <div class="h-delta">${h.status === 'closed' ? '✓ LOCKED' : '⏳ VERIFIED'}</div>
      </div>`).join('');
    } else {
      renderEmpty('heritage-list', '暂无遗产记录 — 运行演进周期后，通过验证的改进将被锁定于此');
    }
    // Build ratchet flow diagram too
    buildRatchetFlow();
    await loadRatchetMetrics();
    cacheSet('panel-ratchet', true, CACHE_TTL.heritage);
  } catch (e) {
    renderError('heritage-list', e, '遗产账本加载失败', loadHeritage);
  }
  hideSkeleton('ratchet');
}

async function loadRatchetMetrics() {
  const host = el('ratchet-ledger-metrics');
  if (!host) return;
  try {
    const payload = await apiRequest('/api/v1/ratchet/metrics');
    const metrics = collectionItems(payload?.metrics || payload);
    const count = el('ratchet-ledger-count');
    if (count) count.textContent = `${metrics.length} 项`;
    if (!metrics.length) {
      renderEmpty('ratchet-ledger-metrics', '暂无全局棘轮指标');
      return;
    }
    host.innerHTML = renderRatchetLedgerCurve(metrics) +
      '<div class="ratchet-ledger-grid">' +
      metrics.slice(0, 8).map(renderRatchetMetricCard).join('') +
      '</div>';
    cacheSet('ratchet-metrics', metrics, CACHE_TTL.ratchetMetrics);
  } catch (e) {
    renderError('ratchet-ledger-metrics', e, '全局棘轮指标加载失败', loadRatchetMetrics);
  }
}

function renderRatchetMetricCard(metric) {
  const key = metric.metric_key || '';
  const value = Number(metric.value || 0);
  const kind = key.split(':')[0] || 'metric';
  return `<div class="ratchet-metric">
    <div class="ratchet-metric__key">${escapeHtml(key)}</div>
    <div class="ratchet-metric__value">${formatMetricValue(value)}</div>
    <div class="ratchet-metric__meta">${escapeHtml(kind)} · gen ${metric.generation || 0} · ${timeAgo(metric.updated_at)}</div>
  </div>`;
}

function formatMetricValue(value) {
  if (!isFinite(value)) return '0';
  if (Math.abs(value) >= 1000) return value.toLocaleString('zh-CN', { maximumFractionDigits: 0 });
  return value.toLocaleString('zh-CN', { maximumFractionDigits: 4 });
}

function renderRatchetLedgerCurve(metrics) {
  const sorted = metrics.slice().sort((a, b) => String(a.updated_at || '').localeCompare(String(b.updated_at || '')));
  const values = sorted.map(m => Number(m.value || 0));
  const W = 720, H = 150, padL = 44, padR = 18, padT = 18, padB = 30;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = max - min || 1;
  const xAt = i => padL + (sorted.length <= 1 ? innerW / 2 : (i / (sorted.length - 1)) * innerW);
  const yAt = v => padT + innerH - ((v - min) / range) * innerH;
  const d = sorted.map((m, i) => `${i === 0 ? 'M' : 'L'}${xAt(i).toFixed(1)},${yAt(values[i]).toFixed(1)}`).join(' ');
  const dots = sorted.map((m, i) => `<circle cx="${xAt(i).toFixed(1)}" cy="${yAt(values[i]).toFixed(1)}" r="3"><title>${escapeHtml(m.metric_key || '')}: ${formatMetricValue(values[i])}</title></circle>`).join('');
  const first = sorted[0]?.metric_key || '';
  const last = sorted[sorted.length - 1]?.metric_key || '';
  return `<div class="ratchet-ledger-curve">
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="全局棘轮指标曲线">
      <line x1="${padL}" y1="${padT + innerH}" x2="${padL + innerW}" y2="${padT + innerH}" stroke="var(--groove)" stroke-width="1"/>
      <line x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT + innerH}" stroke="var(--groove)" stroke-width="1"/>
      <text x="${padL}" y="${H - 8}" text-anchor="start">${escapeHtml(first.slice(0, 22))}</text>
      <text x="${padL + innerW}" y="${H - 8}" text-anchor="end">${escapeHtml(last.slice(0, 22))}</text>
      <path d="${d}"/>
      ${dots}
    </svg>
  </div>`;
}

// ── Actions ──
async function runAudit() {
  toast('正在运行审查...');
  const r = await apiRequest(`${EVP}/audit`, { method: 'POST' });
  if (r) { toast(`审查完成: ${r.passed || 0} 通过, ${r.failed || 0} 未通过`); refreshCurrent(); }
  else toast('审查失败');
}

async function recalcRating() {
  toast('正在重算评级...');
  const r = await apiRequest(`${EVP}/compliance-rating/calculate`, { method: 'POST' });
  if (r) { toast(`评级: ${r.grade} (${r.score}/100)`); refreshCurrent(); }
  else toast('重算失败');
}

// ═══ RatchetAnimator — Shared animation logic ═══
const RatchetAnimator = {
  stepLabels: ['审查', '派发', '验证', '关闭'],
  stepKeys: ['audit', 'dispatch', 'verify', 'close'],

  resetFlow(dotPrefix, connPrefix, dotCount, hasLock) {
    for (let i = 0; i < dotCount; i++) {
      const d = el(dotPrefix + (i + 1));
      if (d) d.className = 'ratchet-dot';
    }
    for (let i = 1; i <= dotCount - 1; i++) {
      const c = el(connPrefix + i);
      if (c) c.className = 'ratchet-connector';
    }
    if (hasLock) {
      const lock = el(dotPrefix + 'lock'); if (lock) lock.className = 'ratchet-dot';
    }
  },

  activateDot(id) { const d = el(id); if (d) d.classList.add('active'); },
  doneDot(id) { const d = el(id); if (d) { d.classList.remove('active'); d.classList.add('done'); } },
  failedDot(id) { const d = el(id); if (d) { d.classList.remove('active'); d.classList.add('failed'); } },
  doneConnector(id) { const c = el(id); if (c) c.classList.add('done'); },

  async runCycle({ dotIds, connIds, lockId, logEl, onComplete, stepNames }) {
    const log = typeof logEl === 'string' ? el(logEl) : logEl;
    if (log) { log.style.display = 'block'; log.innerHTML = ''; }

    const labels = stepNames || this.stepLabels;
    const keys = this.stepKeys;

    for (let i = 0; i < keys.length; i++) {
      this.activateDot(dotIds[i]);
      if (log) log.innerHTML += `<div class="run">⏳ ${labels[i]}...</div>`;
      const r = await apiRequest(`${EVP}/${keys[i]}`, { method: 'POST' });
      if (r) {
        this.doneDot(dotIds[i]);
        const count = r.count || r.passed || r.dispatched || (r.closed || []).length || 0;
        if (log) log.innerHTML += `<div class="ok">✓ ${labels[i]}完成 (${count})</div>`;
      } else {
        this.failedDot(dotIds[i]);
        if (log) log.innerHTML += `<div class="err">✗ ${labels[i]}失败</div>`;
        return false;
      }
      if (connIds[i]) this.doneConnector(connIds[i]);
    }

    // Ratchet lock animation
    if (lockId) {
      const lock = el(lockId); if (lock) lock.classList.add('done');
    }
    if (log) log.innerHTML += `<div class="ok" style="font-weight:700">🔒 棘轮锁定 — 改进已不可逆记录</div>`;
    if (onComplete) await onComplete();
    return true;
  }
};

// Shared ratchet flow builder
function buildRatchetFlow() {
  // The Ratchet panel flow is in HTML, just returns
}

// Ratchet Cycle Stepper (on ratchet page)
async function runCycleOnRatchet() {
  RatchetAnimator.resetFlow('r-', 'rc-', 4, true);
  await RatchetAnimator.runCycle({
    dotIds: ['r-audit', 'r-dispatch', 'r-verify', 'r-close'],
    connIds: ['rc-1', 'rc-2', 'rc-3', 'rc-4'],
    lockId: 'r-lock',
    logEl: 'ratchet-log',
    onComplete: () => loadHeritage(),
  });
  toast('演进周期完成');
}

async function runAuditOnly() {
  toast('正在审查...');
  const r = await apiRequest(`${EVP}/audit`, { method: 'POST' });
  if (r) {
    RatchetAnimator.doneDot('r-audit');
    toast(`审查完成: ${r.passed || 0} 通过, ${r.failed || 0} 未通过`);
  } else toast('审查失败');
}

// Cycle stepper on overview
async function runCycleStepper() {
  RatchetAnimator.resetFlow(
    (i) => `ov-r-${['audit','dispatch','verify','close'][i]}`,
    (i) => `ov-rc-${i}`,
    4, false
  );
  // Manual reset for overview dots (using prefix pattern)
  ['ov-r-audit','ov-r-dispatch','ov-r-verify','ov-r-close'].forEach(id => { const d = el(id); if (d) d.className = 'ratchet-dot'; });
  ['ov-rc-1','ov-rc-2','ov-rc-3'].forEach(id => { const c = el(id); if (c) c.className = 'ratchet-connector'; });

  const log = el('ov-cycle-log');
  log.style.display = 'block';
  log.innerHTML = '';

  const steps = ['audit', 'dispatch', 'verify', 'close'];
  const labels = ['审查', '派发', '验证', '关闭'];
  const dotIds = ['ov-r-audit', 'ov-r-dispatch', 'ov-r-verify', 'ov-r-close'];

  for (let i = 0; i < steps.length; i++) {
    const d = el(dotIds[i]); if (d) d.classList.add('active');
    log.innerHTML += `<div class="run">⏳ ${labels[i]}...</div>`;
    const r = await apiRequest(`${EVP}/${steps[i]}`, { method: 'POST' });
    if (d) d.classList.remove('active');
    if (r) {
      if (d) d.classList.add('done');
      const count = r.count || r.passed || r.dispatched || (r.closed || []).length || 0;
      log.innerHTML += `<div class="ok">✓ ${labels[i]}完成 (${count})</div>`;
    } else {
      if (d) d.classList.add('failed');
      log.innerHTML += `<div class="err">✗ ${labels[i]}失败</div>`;
      break;
    }
    const c = el('ov-rc-' + (i + 1)); if (c) c.classList.add('done');
  }
  toast('演进周期完成');
  loadOverview();
}

function refreshCurrent() {
  const active = document.querySelector('.tab-panel.active');
  if (!active) return;
  const id = active.id.replace('panel-', '');
  cacheClear('panel-' + id);  // Clear cache for this panel
  _panelLoaded[id] = false;
  switchPanel(id);
}

function refreshAll() {
  _allRules = []; _allItems = [];
  _panelLoaded = {};  // Clear panel cache on manual refresh
  _panelCache.clear();
  refreshCurrent();
  toast('已刷新');
}

// ═══════════════════════════════════════════════════════════════════
// 🧬 技能演化实验室 (Interactive Stepper)
// ═══════════════════════════════════════════════════════════════════

let _evolveSkills = [];
let _evCurrentStep = 1;

// Per-skill stepper state: Map<skillId, { dataset, baseline, reflection, candidates, selectedCandidate, step }>
const _evolveStepperState = new Map();

function _getEvolveState(skillId) {
  if (!skillId) return null;
  if (!_evolveStepperState.has(skillId)) {
    _evolveStepperState.set(skillId, {
      dataset: null,
      baseline: null,
      reflection: null,
      candidates: [],
      selectedCandidate: -1,
      step: 1,
    });
  }
  return _evolveStepperState.get(skillId);
}

// Convenience getters/setters for current skill's state
function _evState() { return _getEvolveState(el('ev-skill-select')?.value); }

async function loadEvolveLab() {
  await loadEvolveTeams();
  await loadEvolveSkills();
  loadEvolveHistory();
}

async function loadEvolveTeams() {
  const teams = await apiRequest('/api/v1/agent-config/teams');
  const sel = el('ev-team-select');
  sel.innerHTML = '';
  (teams || []).forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.team_id;
    opt.textContent = `${t.name || t.team_id}`;
    sel.appendChild(opt);
  });
  if (!sel.value && sel.options.length) sel.selectedIndex = 0;
}

async function loadEvolveSkills() {
  const teamId = el('ev-team-select').value || 'build_system';
  // Get skills from skill library browse endpoint
  const r = await apiRequest(`/api/v1/skill-router/browse?team_id=${teamId}`);
  const skills = r?.skills || [];
  // Also try agent-config as fallback
  if (!skills.length) {
    const cfgSkills = await apiRequest(`/api/v1/agent-config/teams/${teamId}/skills`);
    if (cfgSkills && cfgSkills.length) skills.push(...cfgSkills);
  }
  _evolveSkills = skills;
  const sel = el('ev-skill-select');
  sel.innerHTML = '<option value="">— 选择技能 —</option>';
  // Deduplicate by skill_id
  const seen = new Set();
  _evolveSkills.forEach(s => {
    if (seen.has(s.skill_id)) return;
    seen.add(s.skill_id);
    const opt = document.createElement('option');
    opt.value = s.skill_id;
    opt.textContent = `${s.name} (${s.category || s.skill_id?.slice(0,8)})`;
    sel.appendChild(opt);
  });
}

function onSkillSelected() {
  const skillId = el('ev-skill-select').value;
  const state = _getEvolveState(skillId);

  // Restore persisted state if exists, otherwise reset
  if (state && state.dataset) {
    // Restore previous state
    goToStep(state.step || 1);
    renderDatasetTable();
    if (state.baseline) renderBaselineState();
    if (state.reflection) renderReflectionState();
    if (state.candidates.length) renderCandidates();
  } else {
    // New skill — reset
    if (state) {
      state.dataset = null;
      state.baseline = null;
      state.reflection = null;
      state.candidates = [];
      state.selectedCandidate = -1;
      state.step = 1;
    }
    goToStep(1);
    renderDatasetTable();
  }

  // Show skill info card
  const infoCard = el('ev-skill-info');
  if (!skillId) {
    infoCard.style.display = 'none';
    return;
  }
  const skill = _evolveSkills.find(s => s.skill_id === skillId);
  if (!skill) {
    infoCard.style.display = 'none';
    return;
  }
  infoCard.style.display = 'block';
  el('ev-skill-name').textContent = `${skill.icon || '⚡'} ${skill.name}`;
  el('ev-skill-desc').textContent = skill.description || '无描述';
  const instructions = skill.instructions || skill.snapshot?.instructions || '';
  el('ev-skill-meta').innerHTML = `
    ${skill.category || 'general'}<br>
    ${instructions.length} 字指令<br>
    v${skill.version || 1}`;
  el('ev-skill-instructions').textContent = instructions || '(无指令)';
}

// Helpers to restore complex state UI
function renderBaselineState() {
  const r = _evState()?.baseline;
  if (!r) return;
  const gc = r.mean_composite >= 0.8 ? 'var(--koke)' : r.mean_composite >= 0.6 ? 'var(--amber)' : 'var(--shu)';
  el('ev-baseline-cards').innerHTML = `
    <div class="stat-card"><div class="label">复合 Fitness</div><div class="value" style="color:${gc}">${(r.mean_composite * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">指令遵循</div><div class="value">${(r.mean_instruction_following * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">输出质量</div><div class="value">${(r.mean_output_quality * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">简洁度</div><div class="value">${(r.mean_conciseness * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">评估数</div><div class="value">${r.eval_count || r.total_examples}</div></div>
    <div class="stat-card"><div class="label">失败案例</div><div class="value" style="color:${r.failure_count ? 'var(--shu)' : 'var(--koke)'}">${r.failure_count || 0}</div></div>`;
  el('ev-step2-next').style.display = 'inline-block';
}

function renderReflectionState() {
  const r = _evState()?.reflection;
  if (!r) return;
  el('ev-reflect-result').style.display = 'block';
  el('ev-reflect-causes').value = (r.root_causes || []).join('\n');
  el('ev-reflect-defects').value = (r.specific_defects || []).join('\n');
  el('ev-reflect-directions').value = (r.improvement_directions || []).join('\n');
  el('ev-step3-next').style.display = 'inline-block';
}

// ── Stepper Navigation ──

function goToStep(step) {
  _evCurrentStep = step;
  const state = _evState();
  if (state) state.step = step;
  document.querySelectorAll('.ev-step').forEach(s => s.style.display = 'none');
  const target = el(`ev-step-${step}`);
  if (target) target.style.display = 'block';
  // Update stepper dots
  document.querySelectorAll('.step-dot').forEach(dot => {
    const s = parseInt(dot.dataset.step);
    dot.classList.remove('active', 'done');
    if (s === step) dot.classList.add('active');
    else if (s < step) dot.classList.add('done');
  });
}

// ── Step 1: Dataset Builder ──

async function evGenerateDataset() {
  const skillId = el('ev-skill-select').value;
  const teamId = el('ev-team-select').value;
  if (!skillId) { toast('请先选择技能'); return; }

  const btn = event?.target;
  btnLoading(btn, true, 'AI 生成中...');
  el('ev-ds-status').textContent = '⏳ AI 生成中...';
  el('ev-ds-status').style.color = 'var(--amber)';
  toast('正在生成评估数据集...');

  const r = await apiRequest(`${EVP}/dataset/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skill_id: skillId, team_id: teamId, count: 12 }),
  });

  if (r && r.examples) {
    _evDataset = r;
    el('ev-ds-status').textContent = `✓ 已生成 ${r.total_examples} 条`;
    renderDatasetTable();
    btnLoading(btn, false);
    toast(`数据集就绪: ${r.total_examples} 条`);
  } else {
    el('ev-ds-status').textContent = '✗ 生成失败';
    btnLoading(btn, false);
    toast('数据集生成失败');
  }
}

async function evImportKB() {
  const skillId = el('ev-skill-select').value;
  const teamId = el('ev-team-select').value;
  if (!skillId) { toast('请先选择技能'); return; }

  const skill = _evolveSkills.find(s => s.skill_id === skillId);
  toast('从知识库抽取...');

  const r = await apiRequest(`${EVP}/dataset/import-kb`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      skill_id: skillId,
      skill_name: skill?.name || skillId,
      dataset_id: _evDataset?.id || '',
      max_examples: 20,
    }),
  });

  if (r && r.dataset) {
    _evDataset = r.dataset;
    renderDatasetTable();
    toast(`导入了 ${r.imported_count} 条知识库用例`);
  } else {
    toast('知识库导入失败或无相关数据');
  }
}

function evShowManualInput() {
  el('ev-manual-form').style.display = el('ev-manual-form').style.display === 'none' ? 'block' : 'none';
}

async function evAddManualExample() {
  const task = el('ev-manual-task').value.trim();
  const rubric = el('ev-manual-rubric').value.trim();
  if (!task || !rubric) { toast('请填写任务和评分标准'); return; }

  const skillId = el('ev-skill-select').value;
  if (!skillId) { toast('请先选择技能'); return; }

  const skill = _evolveSkills.find(s => s.skill_id === skillId);

  const r = await apiRequest(`${EVP}/dataset/manual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      skill_id: skillId,
      skill_name: skill?.name || skillId,
      dataset_id: _evDataset?.id || '',
      examples: [{ task_input: task, rubric }],
    }),
  });

  if (r && r.examples) {
    _evDataset = r;
    renderDatasetTable();
    el('ev-manual-task').value = '';
    el('ev-manual-rubric').value = '';
    toast('已添加用例');
  } else {
    toast('添加失败');
  }
}

async function evDeleteExample(idx) {
  if (!_evDataset) return;
  const r = await apiRequest(`${EVP}/dataset/${_evDataset.id}/examples`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'delete', indices: [idx] }),
  });
  if (r && r.examples) {
    _evDataset = r;
    renderDatasetTable();
  }
}

function renderDatasetTable() {
  const container = el('ev-dataset-table');
  const countEl = el('ev-ds-count');
  const nextBtn = el('ev-step1-next');

  if (!_evDataset || !_evDataset.examples || !_evDataset.examples.length) {
    container.innerHTML = '<div style="color:var(--dim);font-size:12px;padding:12px">暂无数据。请生成、导入或手动录入评估用例。</div>';
    countEl.textContent = '';
    nextBtn.style.display = 'none';
    return;
  }

  const exs = _evDataset.examples;
  countEl.textContent = `共 ${exs.length} 条 (train:${_evDataset.split?.train || '?'} / val:${_evDataset.split?.val || '?'} / holdout:${_evDataset.split?.holdout || '?'})`;
  nextBtn.style.display = 'inline-block';

  container.innerHTML = `<div style="display:flex;gap:8px;padding:6px 10px;border-bottom:1px solid var(--groove);font-size:10px;color:var(--muted);font-weight:600">
    <span style="min-width:24px">#</span><span style="flex:1">任务</span><span style="flex:1">评分标准</span><span style="min-width:50px">操作</span>
  </div>` + exs.map((ex, i) => `<div class="ds-row">
    <span class="ds-idx">${i + 1}</span>
    <span class="ds-task">${escapeHtml(ex.task_input?.slice(0, 80))}${ex.task_input?.length > 80 ? '...' : ''}</span>
    <span class="ds-rubric">${escapeHtml(ex.rubric?.slice(0, 80))}${ex.rubric?.length > 80 ? '...' : ''}</span>
    <span class="ds-actions"><button class="btn btn-sm" style="padding:1px 6px;font-size:10px;color:var(--shu)" onclick="evDeleteExample(${i})">✕</button></span>
  </div>`).join('');
}

// ── Step 2: Baseline Evaluation ──

async function evRunBaseline() {
  const skillId = el('ev-skill-select').value;
  const teamId = el('ev-team-select').value;
  if (!skillId) { toast('请先选择技能'); return; }
  if (!_evDataset) { toast('请先构建数据集 (步骤1)'); return; }

  const btn = event?.target;
  btnLoading(btn, true, '评估中...');
  toast('正在评估 Baseline...');
  el('ev-baseline-cards').innerHTML = '<div class="stat-card"><div class="value" style="font-size:14px;color:var(--amber)">⏳ 评估中...</div></div>';

  const r = await apiRequest(`${EVP}/step/baseline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skill_id: skillId, team_id: teamId, dataset_id: _evDataset.id }),
  });

  if (!r) { el('ev-baseline-cards').innerHTML = '<div class="stat-card"><div class="value" style="color:var(--shu)">评估失败</div></div>'; btnLoading(btn, false); return; }

  _evBaseline = r;
  const gc = r.mean_composite >= 0.8 ? 'var(--koke)' : r.mean_composite >= 0.6 ? 'var(--amber)' : 'var(--shu)';
  el('ev-baseline-cards').innerHTML = `
    <div class="stat-card"><div class="label">复合 Fitness</div><div class="value" style="color:${gc}">${(r.mean_composite * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">指令遵循</div><div class="value">${(r.mean_instruction_following * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">输出质量</div><div class="value">${(r.mean_output_quality * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">简洁度</div><div class="value">${(r.mean_conciseness * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">评估数</div><div class="value">${r.eval_count || r.total_examples}</div></div>
    <div class="stat-card"><div class="label">失败案例</div><div class="value" style="color:${r.failure_count ? 'var(--shu)' : 'var(--koke)'}">${r.failure_count || 0}</div></div>`;

  // Show failures
  if (r.failures && r.failures.length) {
    el('ev-baseline-failures').innerHTML = `<details open><summary style="cursor:pointer;font-size:12px;color:var(--muted)">失败案例 (${r.failures.length}) — 将作为反思输入</summary>
      <div style="margin-top:8px">${r.failures.map(f => `<div style="padding:6px 10px;margin:4px 0;background:var(--ishi);border:1px solid var(--groove);font-size:11px">
        <div style="color:var(--shu);font-weight:600">得分: ${(f.composite * 100).toFixed(0)}%</div>
        <div style="color:var(--sumi-2);margin-top:2px">任务: ${escapeHtml(f.task_input)}</div>
        <div style="color:var(--dim);margin-top:2px">原因: ${escapeHtml(f.reasoning)}</div>
      </div>`).join('')}</div></details>`;
  } else {
    el('ev-baseline-failures').innerHTML = '<div style="color:var(--koke);font-size:12px;padding:8px">✓ 全部通过，无失败案例</div>';
  }

  el('ev-step2-next').style.display = 'inline-block';
  btnLoading(btn, false);
  toast(`Baseline: ${(r.mean_composite * 100).toFixed(1)}%`);
}

// ── Step 3: Reflection ──

async function evRunReflect() {
  const skillId = el('ev-skill-select').value;
  const teamId = el('ev-team-select').value;
  if (!skillId) { toast('请先选择技能'); return; }

  const failures = _evBaseline?.failures || [];
  const userHints = el('ev-user-hints').value.trim();

  if (!failures.length && !userHints) {
    toast('没有失败案例且未填写分析方向');
    return;
  }

  const btn = event?.target;
  btnLoading(btn, true, 'AI 反思中...');
  toast('🤖 AI 反思中...');

  const r = await apiRequest(`${EVP}/step/reflect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skill_id: skillId, team_id: teamId, failures, user_hints: userHints }),
  });

  if (!r) { toast('反思分析失败'); btnLoading(btn, false); return; }

  _evReflection = r;
  el('ev-reflect-result').style.display = 'block';
  el('ev-reflect-causes').value = (r.root_causes || []).join('\n');
  el('ev-reflect-defects').value = (r.specific_defects || []).join('\n');
  el('ev-reflect-directions').value = (r.improvement_directions || []).join('\n');
  el('ev-step3-next').style.display = 'inline-block';
  btnLoading(btn, false);
  toast('反思分析完成 — 可编辑后继续');
}

function getEditedReflection() {
  return {
    root_causes: el('ev-reflect-causes').value.split('\n').filter(Boolean),
    specific_defects: el('ev-reflect-defects').value.split('\n').filter(Boolean),
    improvement_directions: el('ev-reflect-directions').value.split('\n').filter(Boolean),
  };
}

// ── Step 4: Mutation Lab ──

async function evRunMutate() {
  const skillId = el('ev-skill-select').value;
  const teamId = el('ev-team-select').value;
  if (!skillId) { toast('请先选择技能'); return; }

  const reflection = getEditedReflection();
  if (!reflection.root_causes.length && !reflection.improvement_directions.length) {
    toast('请先完成反思分析 (步骤3)'); return;
  }

  const btn = event?.target;
  btnLoading(btn, true, '生成变异中...');
  toast('🤖 生成变异候选...');

  const r = await apiRequest(`${EVP}/step/mutate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skill_id: skillId, team_id: teamId, reflection }),
  });

  if (!r || !r.candidates || !r.candidates.length) {
    toast('未生成有效候选'); btnLoading(btn, false); return;
  }

  _evCandidates = r.candidates.map(c => ({ ...c, score: null, evaluated: false }));
  renderCandidates();
  btnLoading(btn, false);
  toast(`生成了 ${_evCandidates.length} 个候选`);
}

function evShowManualCandidate() {
  el('ev-manual-candidate').style.display = el('ev-manual-candidate').style.display === 'none' ? 'block' : 'none';
}

function evAddManualCandidate() {
  const text = el('ev-candidate-text').value.trim();
  if (!text) { toast('请填写候选指令'); return; }
  const state = _evState();
  if (state) state.candidates.push({ strategy: '手动', instructions: text, score: null, evaluated: false });
  el('ev-candidate-text').value = '';
  el('ev-manual-candidate').style.display = 'none';
  renderCandidates();
  toast('已添加手动候选');
}

async function evEvalCandidate(idx) {
  const skillId = el('ev-skill-select').value;
  const teamId = el('ev-team-select').value;
  if (!_evDataset) { toast('需要数据集'); return; }

  const cand = _evCandidates[idx];
  toast(`评估候选 #${idx + 1}...`);

  const r = await apiRequest(`${EVP}/step/evaluate-candidate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      skill_id: skillId,
      team_id: teamId,
      dataset_id: _evDataset.id,
      instructions: cand.instructions,
    }),
  });

  if (r) {
    _evCandidates[idx].score = r.score;
    _evCandidates[idx].evaluated = true;
    _evCandidates[idx].passed = r.passed_constraints;
    _evCandidates[idx].details = r;
    renderCandidates();
    toast(`候选 #${idx + 1}: ${(r.score * 100).toFixed(1)}%`);
  } else {
    toast('评估失败');
  }
}

async function evEvalAllCandidates() {
  for (let i = 0; i < _evCandidates.length; i++) {
    if (!_evCandidates[i].evaluated) {
      await evEvalCandidate(i);
    }
  }
}

function evSelectCandidate(idx) {
  _evSelectedCandidate = idx;
  renderCandidates();
  el('ev-step4-next').style.display = 'inline-block';
}

function renderCandidates() {
  const container = el('ev-candidates-list');
  if (!_evCandidates.length) {
    container.innerHTML = '<div style="color:var(--dim);font-size:12px;padding:12px">暂无候选。点击"生成候选"或手动添加。</div>';
    return;
  }

  const baseline = _evBaseline?.mean_composite || 0;
  container.innerHTML = _evCandidates.map((c, i) => {
    const selected = i === _evSelectedCandidate;
    const scoreColor = c.score > baseline ? 'var(--koke)' : c.score !== null ? 'var(--shu)' : 'var(--muted)';
    const delta = c.score !== null ? ((c.score - baseline) * 100).toFixed(1) : '—';
    return `<div class="cand-card ${selected ? 'selected' : ''}">
      <div class="cand-header">
        <span class="cand-strategy">${escapeHtml(c.strategy)} ${c.passed === false ? '⚠️ 约束违规' : ''}</span>
        <span>
          ${c.evaluated ? `<span class="cand-score" style="color:${scoreColor}">${(c.score * 100).toFixed(1)}% (${delta > 0 ? '+' : ''}${delta}%)</span>` : '<span style="font-size:11px;color:var(--muted)">未评估</span>'}
          <button class="btn btn-sm" style="padding:2px 6px;font-size:10px;margin-left:6px" onclick="evEvalCandidate(${i})">⚡ 评估</button>
          <button class="btn btn-sm ${selected ? 'btn-primary' : ''}" style="padding:2px 6px;font-size:10px;margin-left:4px" onclick="evSelectCandidate(${i})">✓ 选用</button>
        </span>
      </div>
      <div class="cand-body">${escapeHtml(c.instructions?.slice(0, 500))}${c.instructions?.length > 500 ? '\n...' : ''}</div>
    </div>`;
  }).join('');
}

// ── Step 5: Compare & Lock ──

function renderFinalCompare() {
  if (_evSelectedCandidate < 0 || !_evCandidates[_evSelectedCandidate]) return;
  const cand = _evCandidates[_evSelectedCandidate];
  const baseline = _evBaseline?.mean_composite || 0;
  const delta = cand.score !== null ? ((cand.score - baseline) * 100).toFixed(1) : '?';

  el('ev-final-compare').innerHTML = `<div class="card-grid">
    <div class="stat-card"><div class="label">Baseline</div><div class="value">${(baseline * 100).toFixed(1)}%</div></div>
    <div class="stat-card"><div class="label">候选 (${escapeHtml(cand.strategy)})</div><div class="value" style="color:var(--koke)">${cand.score !== null ? (cand.score * 100).toFixed(1) + '%' : '未评估'}</div></div>
    <div class="stat-card"><div class="label">提升</div><div class="value" style="color:${delta > 0 ? 'var(--koke)' : 'var(--shu)'}">+${delta}%</div></div>
    <div class="stat-card"><div class="label">长度</div><div class="value" style="font-size:14px">${cand.details?.length_candidate || cand.instructions?.length || '?'} 字</div></div>
  </div>`;

  // Simple text diff
  const skill = _evolveSkills.find(s => s.skill_id === el('ev-skill-select').value);
  // Side-by-side diff: original vs candidate
  const origInstructions = skill?.instructions || skill?.snapshot?.instructions || '(原始指令不可用)';
  el('ev-final-diff').innerHTML = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
    <div>
      <div style="margin-bottom:6px;color:var(--shu);font-weight:600;font-size:12px">📄 原始指令 (${origInstructions.length} 字)</div>
      <div style="white-space:pre-wrap;color:var(--sumi-2);font-size:11px;padding:8px;background:var(--ishi);border:1px solid var(--groove);max-height:250px;overflow-y:auto;line-height:1.7">${escapeHtml(origInstructions)}</div>
    </div>
    <div>
      <div style="margin-bottom:6px;color:var(--koke);font-weight:600;font-size:12px">✨ 变异后指令 (${cand.instructions?.length || 0} 字)</div>
      <div style="white-space:pre-wrap;color:var(--sumi);font-size:11px;padding:8px;background:var(--ishi);border:1px solid var(--groove);max-height:250px;overflow-y:auto;line-height:1.7">${escapeHtml(cand.instructions)}</div>
    </div>
  </div>`;
}

async function evApplyEvolution() {
  if (_evSelectedCandidate < 0) { toast('请先选择一个候选'); return; }
  const cand = _evCandidates[_evSelectedCandidate];
  const baseline = _evBaseline?.mean_composite || 0;

  if (!cand.score || cand.score <= baseline) {
    toast('候选分数未超过 Baseline，无法应用'); return;
  }

  const skillId = el('ev-skill-select').value;
  const teamId = el('ev-team-select').value;

  const btn = event?.target;
  btnLoading(btn, true, '应用中...');
  toast('正在应用演化...');
  const r = await apiRequest(`${EVP}/step/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      skill_id: skillId,
      team_id: teamId,
      instructions: cand.instructions,
      baseline_score: baseline,
      new_score: cand.score,
    }),
  });

  if (r && !r.error) {
    btnLoading(btn, false);
    toast(`✓ 已锁定! ${r.skill_id} → v${r.new_version} (${r.score_improvement})`);
    el('ev-final-compare').innerHTML += `<div style="margin-top:12px;color:var(--koke);font-weight:700;font-size:14px">🔒 已锁定到 Heritage Ledger — v${r.new_version}</div>`;
    loadEvolveSkills();
    loadEvolveHistory();
  } else {
    btnLoading(btn, false);
    toast('应用失败: ' + (r?.detail || r?.error || '未知错误'));
  }
}

// ── Auto-Triage ──

async function runAutoTriage() {
  const teamId = el('ev-team-select').value;
  toast('正在自动诊断...');
  el('ev-triage-section').style.display = 'block';

  const r = await apiRequest(`${EVP}/auto-triage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ team_id: teamId, top_n: 5 }),
  });

  if (!r) { el('ev-triage-summary').innerHTML = '<div class="stat-card"><div class="value" style="color:var(--shu)">诊断失败</div></div>'; return; }

  const s = r.summary || {};
  el('ev-triage-summary').innerHTML = `
    <div class="stat-card"><div class="label">总技能数</div><div class="value">${s.total_skills || 0}</div></div>
    <div class="stat-card"><div class="label">平均效率</div><div class="value">${((s.mean_effectiveness || 0) * 100).toFixed(0)}%</div></div>
    <div class="stat-card"><div class="label">⚠ 风险技能</div><div class="value" style="color:${s.at_risk ? 'var(--shu)' : 'var(--koke)'}">${s.at_risk || 0}</div><div class="sub">${s.at_risk_pct || 0}%</div></div>
    <div class="stat-card"><div class="label">✓ 健康技能</div><div class="value" style="color:var(--koke)">${s.healthy || 0}</div></div>`;

  const candidates = r.candidates || [];
  if (candidates.length) {
    el('ev-triage-candidates').innerHTML = `
      <div style="font-size:12px;color:var(--kitsune);margin-bottom:8px;font-weight:600">💡 ${escapeHtml(r.recommendation || '')}</div>
      <div class="tbl-wrapper"><table class="tbl"><thead><tr><th>技能</th><th>效率</th><th>使用</th><th>影响力</th><th>原因</th><th>操作</th></tr></thead><tbody>
      ${candidates.map(c => `<tr>
        <td><b>${escapeHtml(c.skill_name)}</b></td>
        <td style="color:${c.effectiveness < 0.7 ? 'var(--shu)' : 'var(--amber)'}">${(c.effectiveness * 100).toFixed(0)}%</td>
        <td>${c.usage_count}</td>
        <td style="font-family:var(--font-mono);font-weight:700">${c.impact_score.toFixed(1)}</td>
        <td style="font-size:11px;color:var(--dim)">${escapeHtml(c.reasons.join('; '))}</td>
        <td><button class="btn btn-sm" style="padding:2px 8px;font-size:10px" onclick="selectAndOptimize('${c.skill_id}')">🚀 选择</button></td>
      </tr>`).join('')}</tbody></table></div>`;
  } else {
    el('ev-triage-candidates').innerHTML = '<div style="color:var(--koke);font-size:12px;padding:8px">所有技能表现良好 ✓</div>';
  }
  toast('诊断完成');
}

function selectAndOptimize(skillId) {
  el('ev-skill-select').value = skillId;
  onSkillSelected();
}

// ── Step 5 auto-render on enter ──
const _origGoToStep = goToStep;
goToStep = function(step) {
  _origGoToStep(step);
  if (step === 5) renderFinalCompare();
};

// ── History ──

async function loadEvolveHistory() {
  const runs = collectionItems(await apiList(`${EVP}/optimize/runs`, 15, 0));
  if (!runs || !runs.length) {
    el('ev-history-table').innerHTML = '<div style="color:var(--dim);font-size:12px;padding:8px">暂无优化记录</div>';
    return;
  }
  el('ev-history-table').innerHTML = `<div class="tbl-wrapper"><table class="tbl"><thead><tr><th>ID</th><th>类型</th><th>目标</th><th>状态</th><th>Baseline</th><th>Best</th><th>Δ</th><th>时间</th></tr></thead><tbody>
    ${runs.map(r => {
      const sc = r.improved ? 'var(--koke)' : r.status === 'failed' ? 'var(--shu)' : 'var(--muted)';
      return `<tr>
        <td style="font-family:var(--font-mono);font-size:11px">${escapeHtml(r.run_id)}</td>
        <td><span class="chip" style="font-size:10px">${escapeHtml(r.target_type)}</span></td>
        <td style="font-size:12px">${escapeHtml(r.target_id?.slice(0, 12) || '')}</td>
        <td style="color:${sc};font-weight:600;font-size:12px">${escapeHtml(r.status)}</td>
        <td style="font-family:var(--font-mono)">${(r.baseline_score * 100).toFixed(0)}%</td>
        <td style="font-family:var(--font-mono)">${(r.best_score * 100).toFixed(0)}%</td>
        <td style="font-family:var(--font-mono);color:${r.score_delta > 0 ? 'var(--koke)' : 'var(--muted)'}">${r.score_delta > 0 ? '+' : ''}${(r.score_delta * 100).toFixed(1)}%</td>
        <td style="font-size:11px;color:var(--dim)">${timeAgo(r.started_at)}</td>
      </tr>`;
    }).join('')}</tbody></table></div>`;
}

function exposeEvolutionActions() {
  Object.assign(window, {
    el,
    switchPanel,
    loadOverview,
    loadItems,
    loadRules,
    loadZones,
    loadTrail,
    loadTrend,
    loadHeritage,
    openItemDetail,
    verifyItem,
    closeItem,
    markProgress,
    markComplete,
    submitBuildComplete,
    runAudit,
    runAuditOnly,
    recalcRating,
    runCycleOnRatchet,
    runCycleStepper,
    refreshCurrent,
    refreshAll,
    loadEvolveLab,
    loadEvolveTeams,
    loadEvolveSkills,
    onSkillSelected,
    goToStep,
    evGenerateDataset,
    evImportKB,
    evShowManualInput,
    evAddManualExample,
    evDeleteExample,
    evRunBaseline,
    evRunReflect,
    evRunMutate,
    evShowManualCandidate,
    evAddManualCandidate,
    evEvalCandidate,
    evEvalAllCandidates,
    evSelectCandidate,
    evApplyEvolution,
    runAutoTriage,
    selectAndOptimize,
    loadEvolveHistory,
  });
}

// ═══ SSE Real-time Updates ═══
function _startSSE() {
  if (_sseSource) return;
  try {
    _sseSource = new EventSource(`${EVP}/stream`);
    _sseSource.onmessage = function(e) {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'stats_update' || data.type === 'item_update') {
          // Incrementally refresh overview KPIs
          const active = document.querySelector('.tab-panel.active');
          if (active && active.id === 'panel-overview') {
            loadOverview();
          }
        }
        if (data.type === 'trail_update') {
          cacheClear('panel-trail');
        }
      } catch (_) {}
    };
    _sseSource.onerror = function() {
      _closeSSE();
      // Fallback to polling
      if (!_ssePollTimer && _ssePollActive && typeof setInterval === 'function') {
        _ssePollTimer = setInterval(() => {
          const active = document.querySelector('.tab-panel.active');
          if (active && active.id === 'panel-overview') loadOverview();
        }, 30000);
      }
    };
  } catch (_) {
    _fallbackPoll();
  }
}

function _closeSSE() {
  if (_sseSource) { _sseSource.close(); _sseSource = null; }
}

function _fallbackPoll() {
  if (!_ssePollTimer && typeof setInterval === 'function') {
    _ssePollActive = true;
    _ssePollTimer = setInterval(() => {
      const active = document.querySelector('.tab-panel.active');
      if (active && active.id === 'panel-overview') loadOverview();
    }, 30000);
  }
}

function _stopPolling() {
  if (_ssePollTimer && typeof clearInterval === 'function') { clearInterval(_ssePollTimer); _ssePollTimer = null; }
  _ssePollActive = false;
}

// ── Init ──
exposeEvolutionActions();

// Route evolve stepper global vars through per-skill state
Object.defineProperty(window, '_evDataset', {
  get() { const s = _evState(); return s ? s.dataset : null; },
  set(v) { const s = _evState(); if (s) s.dataset = v; },
  configurable: true, enumerable: true
});
Object.defineProperty(window, '_evBaseline', {
  get() { const s = _evState(); return s ? s.baseline : null; },
  set(v) { const s = _evState(); if (s) s.baseline = v; },
  configurable: true, enumerable: true
});
Object.defineProperty(window, '_evReflection', {
  get() { const s = _evState(); return s ? s.reflection : null; },
  set(v) { const s = _evState(); if (s) s.reflection = v; },
  configurable: true, enumerable: true
});
Object.defineProperty(window, '_evCandidates', {
  get() { const s = _evState(); return s ? s.candidates : []; },
  set(v) { const s = _evState(); if (s) s.candidates = v; },
  configurable: true, enumerable: true
});
Object.defineProperty(window, '_evSelectedCandidate', {
  get() { const s = _evState(); return s ? (s.selectedCandidate ?? -1) : -1; },
  set(v) { const s = _evState(); if (s) s.selectedCandidate = v; },
  configurable: true, enumerable: true
});

if (deepLinkPanel) switchPanel(deepLinkPanel);
else if (deepLinkItemId) switchPanel('items');
else loadOverview();

// Start SSE connection for real-time updates
_startSSE();

// Cleanup on page unload
if (window.addEventListener) {
  window.addEventListener('beforeunload', () => { _closeSSE(); _stopPolling(); });
}
