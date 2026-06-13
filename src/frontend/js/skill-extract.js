import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { prioritizeExtractTeams } from './extract-routing.js';

// ── Globals ─────────────────────────────────────────────────────
let scene, camera, renderer, controls, clock;
let humanFigure, extractionGroup;
let myceliumGroup;
let skillNodes = [];
let extractionActive = false;
let animTime = 0, animFrame = 0;
let extractParticleGeo, extractParticleData = [];
const EXTRACT_PARTICLE_COUNT = 80;
const myceliumColor = new THREE.Color(0xD4A574);

// ── Team/Agent data ─────────────────────────────────────────────
let allTeams = [];
let teamAgents = {}; // { team_id: [{agent_id, name, role}, ...] }

// ── API ─────────────────────────────────────────────────────────
const API_BASE = '/api/v1/agent-config';
// C-2: 日志开关
const DEBUG_SK = false;
const sklog = (...a) => { if (DEBUG_SK) console.log(...a); };
const skwarn = (...a) => { if (DEBUG_SK) console.warn(...a); };
// C-1: request_id 计数器
let _skReqIdCounter = 0;
function _nextSkReqId() { _skReqIdCounter++; return 'sk-' + Date.now().toString(36) + '-' + _skReqIdCounter; }

let currentTeamId = '';
let queueItems = [];
let currentFilter = '';
let selectedItemId = null;
let allSkills = [];
let sseSource = null;

// CSRF token cache — fetched once, reused for all state-changing requests
var _csrfToken_sk = '';
var _csrfPromise_sk = null;
function _ensureCsrf_sk() {
  if (_csrfToken_sk) return Promise.resolve(_csrfToken_sk);
  if (_csrfPromise_sk) return _csrfPromise_sk;
  _csrfPromise_sk = fetch('/api/v1/auth/csrf-token')
    .then(function(r) { return r.json(); })
    .then(function(d) { _csrfToken_sk = d.csrf_token || ''; return _csrfToken_sk; })
    .catch(function() { _csrfPromise_sk = null; return ''; });
  return _csrfPromise_sk;
}
_ensureCsrf_sk();

// Local CSRF-aware fetch wrapper — use instead of raw fetch() for POST/PUT/DELETE
var _af_sk = async function(url, opts) {
  var method = (opts && opts.method) ? opts.method.toUpperCase() : 'GET';
  if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
    await _ensureCsrf_sk();
    if (_csrfToken_sk) {
      opts = opts || {};
      opts.headers = opts.headers || {};
      opts.headers['x-csrf-token'] = _csrfToken_sk;
    }
  }
  return (window._agFetch || fetch)(url, opts);
};

async function api(path, opts = {}) {
  try {
    var method = (opts.method || 'GET').toUpperCase();
    var rid = _nextSkReqId();
    var headers = { 'Content-Type': 'application/json', 'X-Request-ID': rid, ...opts.headers };
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
      await _ensureCsrf_sk();
      if (_csrfToken_sk) headers['x-csrf-token'] = _csrfToken_sk;
    }
    const r = await (window._agFetch || fetch)(API_BASE + path, {
      headers: headers,
      ...opts,
    });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return await r.json();
  } catch (e) {
    skwarn('[API]', path, e);
    showToast(`请求失败 [${e._requestId || '?'}]: ${e.message}`);
    return null;
  }
}

function collectionItems(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.items)) return payload.items;
  return [];
}

function renderPlazaSourceMeta(src) {
  const el = document.getElementById('plaza-source-meta');
  if (!el) return;
  const plazaId = src?.source_plaza_id || '';
  const discussionId = src?.source_discussion_id || '';
  if (!plazaId || !discussionId) {
    el.style.display = 'none';
    el.innerHTML = '';
    return;
  }
  const href = `/plaza.html?plaza_id=${encodeURIComponent(plazaId)}&discussion_id=${encodeURIComponent(discussionId)}`;
  const outputId = src?.source_output_id || '';
  el.innerHTML = `来源 Plaza：<a href="${href}" style="color:oklch(0.72 0.12 250);text-decoration:none">${escapeHtml(src.source_title || discussionId)}</a>${outputId ? ` · output <code>${escapeHtml(outputId)}</code>` : ''}`;
  el.style.display = 'block';
}

async function listApi(path, limit = 200, offset = 0) {
  if (window.api && typeof window.api.list === 'function') {
    const payload = await window.api.list(API_BASE + path, limit, offset);
    return collectionItems(payload);
  }
  return collectionItems(await api(path));
}

// Skill-router API uses a different base path
async function routerApi(path, opts = {}) {
  try {
    var method = (opts.method || 'GET').toUpperCase();
    var headers = { 'Content-Type': 'application/json', ...opts.headers };
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
      await _ensureCsrf_sk();
      if (_csrfToken_sk) headers['x-csrf-token'] = _csrfToken_sk;
    }
    const r = await (window._agFetch || fetch)('/api/v1/skill-router' + path, {
      headers: headers,
      ...opts,
    });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return await r.json();
  } catch (e) {
    console.error('[RouterAPI]', path, e);
    return null;
  }
}

// ── Team Loading ────────────────────────────────────────────────
async function loadTeams() {
  const teams = await listApi('/teams');
  if (!teams.length) return;
  allTeams = teams;

  // Check for participant teams from plaza (via sessionStorage)
  let participantTeamIds = null;
  let preferredTeamId = '';
  const storedTeams = sessionStorage.getItem('extract_teams');
  if (storedTeams) {
    try { participantTeamIds = JSON.parse(storedTeams); } catch(e) {}
    sessionStorage.removeItem('extract_teams');
  }
  const storedPreferredTeam = sessionStorage.getItem('extract_team_id');
  if (storedPreferredTeam) {
    preferredTeamId = storedPreferredTeam;
    sessionStorage.removeItem('extract_team_id');
  }

  // Render team chips — dynamic add/remove
  const container = document.getElementById('team-chips');
  const params = new URLSearchParams(location.search);
  const urlTeam = params.get('team_id');
  if (urlTeam) preferredTeamId = urlTeam;
  let displayTeams = prioritizeExtractTeams(teams, participantTeamIds, preferredTeamId);
  if (!displayTeams.length && teams.length) displayTeams.push(...teams);

  // Store active team IDs for add/remove
  window._activeTeamIds = displayTeams.map(t => t.team_id);
  renderTeamChips();

  if (preferredTeamId && displayTeams.find(t => t.team_id === preferredTeamId)) {
    selectTeamChip(container.querySelector(`[data-tid="${preferredTeamId}"]`), preferredTeamId);
  } else if (displayTeams.length) {
    const first = displayTeams[0];
    selectTeamChip(container.querySelector(`[data-tid="${first.team_id}"]`), first.team_id);
  }

  // Pre-fill source text from URL params or sessionStorage (for plaza jump)
  const storedSource = sessionStorage.getItem('extract_source');
  if (storedSource) {
    sessionStorage.removeItem('extract_source');
    try {
      const src = JSON.parse(storedSource);
      document.getElementById('source-text').value = src.source_text || '';
      document.getElementById('source-title').value = src.source_title || '';
      document.getElementById('source-type').value = src.source_type || 'chat';
      renderPlazaSourceMeta(src);
      document.getElementById('knowledge-input-section').classList.remove('collapsed');
      setTimeout(() => startExtraction(), 500);
    } catch(e) { console.error('Failed to parse extract_source', e); }
  } else if (params.get('source_text')) {
    document.getElementById('source-text').value = decodeURIComponent(params.get('source_text'));
    document.getElementById('source-title').value = decodeURIComponent(params.get('source_title') || '');
    document.getElementById('source-type').value = params.get('source_type') || 'chat';
    document.getElementById('knowledge-input-section').classList.remove('collapsed');
    setTimeout(() => startExtraction(), 500);
  }
}

window.selectTeamChip = function(el, teamId) {
  if (!el) return;
  document.querySelectorAll('.team-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  currentTeamId = teamId;
  loadTeamAgents(teamId);
  connectSSE();
  loadQueue();
  loadSkills();
};

// ── Dynamic team chip rendering ─────────────────────────────────
function renderTeamChips() {
  const container = document.getElementById('team-chips');
  const activeIds = window._activeTeamIds || [];
  // 折叠策略: 最多展示 2 个 chip + "+N" 按钮
  const MAX_VISIBLE = 2;
  const visible = activeIds.slice(0, MAX_VISIBLE);
  const hidden = activeIds.length - visible.length;
  const chips = visible.map(tid => {
    const t = allTeams.find(x => x.team_id === tid);
    if (!t) return '';
    return `<span class="team-chip" data-tid="${t.team_id}"><span onclick="selectTeamChip(this.parentElement,'${t.team_id}')">${t.name}</span><span class="chip-close" onclick="event.stopPropagation();window._removeTeamChip('${t.team_id}')">✕</span></span>`;
  }).join('');
  const more = hidden > 0 ? `<span class="team-chips__more" onclick="window._toggleChipDropdown()">+${hidden}</span>` : '';
  // Add button + dropdown
  const addBtn = `<span class="chip-add" onclick="window._toggleChipDropdown()">＋</span>`;
  const dropdown = `<div class="chip-dropdown" id="chip-dropdown"></div>`;
  container.innerHTML = chips + more + addBtn + dropdown;
  // Re-activate current
  if (currentTeamId) {
    const el = container.querySelector(`[data-tid="${currentTeamId}"]`);
    if (el) el.classList.add('active');
  }
}

window._removeTeamChip = function(teamId) {
  window._activeTeamIds = (window._activeTeamIds || []).filter(id => id !== teamId);
  renderTeamChips();
  // If removed the active team, switch to first remaining
  if (currentTeamId === teamId && window._activeTeamIds.length) {
    const container = document.getElementById('team-chips');
    const first = window._activeTeamIds[0];
    selectTeamChip(container.querySelector(`[data-tid="${first}"]`), first);
  }
};

window._toggleChipDropdown = function() {
  const dd = document.getElementById('chip-dropdown');
  dd.classList.toggle('open');
  if (dd.classList.contains('open')) {
    // Show teams not already active
    const activeIds = new Set(window._activeTeamIds || []);
    const available = allTeams.filter(t => !activeIds.has(t.team_id));
    if (!available.length) {
      dd.innerHTML = '<div class="chip-dropdown-item" style="color:oklch(0.4 0.005 110)">所有团队已添加</div>';
    } else {
      dd.innerHTML = available.map(t =>
        `<div class="chip-dropdown-item" onclick="window._addTeamChip('${t.team_id}')">${t.name}</div>`
      ).join('');
    }
    // Close on outside click
    setTimeout(() => document.addEventListener('click', _closeChipDropdown, { once: true }), 0);
  }
};

function _closeChipDropdown() {
  const dd = document.getElementById('chip-dropdown');
  if (dd) dd.classList.remove('open');
}

window._addTeamChip = function(teamId) {
  if (!window._activeTeamIds.includes(teamId)) {
    window._activeTeamIds.push(teamId);
  }
  renderTeamChips();
  // Select the newly added team
  const container = document.getElementById('team-chips');
  selectTeamChip(container.querySelector(`[data-tid="${teamId}"]`), teamId);
  _closeChipDropdown();
};

async function loadTeamAgents(teamId) {
  const agents = await listApi(`/teams/${teamId}/agents`);
  teamAgents[teamId] = agents;
  updateAgentSelect();
}

function updateAgentSelect() {
  const sel = document.getElementById('approve-agent-select');
  if (!sel) return;
  const agents = teamAgents[currentTeamId] || [];
  sel.innerHTML = agents.map(a =>
    `<option value="${a.agent_id}">${a.name || a.agent_id}${a.role ? ' (' + a.role + ')' : ''}</option>`
  ).join('');
}

// ── SSE Connection ──────────────────────────────────────────────
let _sseReconnectAttempts = 0;
const _SSE_MAX_RECONNECT = 20;
const _SSE_BASE_DELAY = 3000;

function connectSSE() {
  if (sseSource) { sseSource.close(); sseSource = null; }
  if (!currentTeamId) return;
  sseSource = new EventSource(`${API_BASE}/teams/${currentTeamId}/skill-extract/stream`);
  sseSource.onopen = () => { _sseReconnectAttempts = 0; };
  sseSource.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data);
      handleSSE(d);
    } catch(err) { console.warn('[SSE] parse error:', err.message); }
  };
  sseSource.onerror = () => {
    if (sseSource) { sseSource.close(); sseSource = null; }
    _sseReconnectAttempts++;
    if (_sseReconnectAttempts > _SSE_MAX_RECONNECT) {
      console.error('[SSE] Max reconnection attempts reached, stopping');
      return;
    }
    // Exponential backoff: 3s, 6s, 12s, 24s... capped at 60s
    const delay = Math.min(_SSE_BASE_DELAY * Math.pow(2, _sseReconnectAttempts - 1), 60000);
    console.warn(`[SSE] connection error, reconnecting in ${delay/1000}s (attempt ${_sseReconnectAttempts}/${_SSE_MAX_RECONNECT})`);
    clearTimeout(window._sseReconnectTimer);
    window._sseReconnectTimer = setTimeout(() => { if (!document.hidden) connectSSE(); }, delay);
  };
}

function handleSSE(data) {
  switch (data.type) {
    case 'connected':
      queueItems = data.queue || [];
      renderQueue();
      rebuildSkillNodes();
      // Sync extraction progress with actual queue state on reconnect
      if (extractionActive) {
        const hasInProgress = queueItems.some(q => q.status === 'pending' || q.status === 'llm_prefilling');
        if (!hasInProgress) stopExtractionVFX();
      }
      break;
    case 'item_created':
      queueItems.unshift(data.item);
      renderQueue();
      // Additional extracted skills arrive as item_created with ready_for_review status
      if (data.item?.status === 'ready_for_review') {
        const extraName = data.item.draft_name || '未命名';
        addMessage('system', `⚗️ 发现额外技能「${escHtml(extraName)}」`);
        rebuildSkillNodes();
      } else {
        triggerExtractionVFX();
        onExtractionItemCreated();
        updatePipelineStepper('draft');
        addMessage('system', `📥 收到知识原料 (${(data.item?.source_text?.length || 0) > 1000 ? ((data.item.source_text.length / 1024).toFixed(1) + 'KB') : (data.item?.source_text?.length || 0) + '字'})，<b>[①日志采集]</b> 开始分解…`);
      }
      break;
    case 'item_status_changed':
      updateQueueItemStatus(data);
      // SSE-driven progress: step 2/3
      if (data.status === 'llm_prefilling') {
        document.getElementById('ep-fill').style.width = '60%';
        document.getElementById('ep-text').textContent = '🔬 LLM 分析中…';
        updatePipelineStepper('draft');
        addMessage('system', '🔬 <b>[①日志采集]</b> LLM 正在分析知识结构…识别知识簇中');
      } else if (data.status === 'ready_for_review') {
        document.getElementById('ep-fill').style.width = '90%';
        document.getElementById('ep-text').textContent = '⚗️ 结晶化完成';
        updatePipelineStepper('review');
        const name = data.draft_name || '未命名技能';
        const conf = data.llm_confidence ? (data.llm_confidence * 100).toFixed(0) + '%' : '—';
        const scopeHint = data.draft_scope === 'public' ? ' 🌐公共' : ' 🔒私有';
        addMessage('system', `⚗️ <b>[②上下文补全]</b> 正在结晶化…置信度 ${conf}`);
        addMessage('skill-card', `✨ 发现技能「${escHtml(name)}」${scopeHint}，请补全上下文后进行交叉复核`, data.item_id);
        // rebuildSkillNodes (called by updateQueueItemStatus above) will spawn with animation
        // Highlight the latest crystal
        setTimeout(() => highlightLatestCrystal(), 300);
      } else if (data.status === 'error') {
        addMessage('system', '⚠️ 萃取出错，请重试');
      }
      break;
    case 'skill_approved':
      updateQueueItemStatus({ item_id: data.item_id, status: 'approved', status_icon: '◎', status_label: '已通过' });
      loadSkills();
      updatePipelineStepper('published');
      spawnSkillNodeAnimated(data.skill);  // Use animated version
      showToast(`✅ 技能「${escHtml(data.skill_name)}」已入库`);
      addMessage('system', `🔮 <b>[④技能发布]</b> 技能「${escHtml(data.skill_name)}」已结晶发布！菌丝网络已延伸至新节点`);
      if (viewMode === 'panorama') buildPanoramaView();
      break;
    case 'skill_rejected':
      updateQueueItemStatus({ item_id: data.item_id, status: 'rejected', status_icon: '✕', status_label: '已拒绝' });
      addMessage('system', `❌ 已拒绝「${escHtml(data.draft_name || '')}」${data.reason ? '，原因：' + escHtml(data.reason) : ''}`);
      break;
    case 'item_edited':
      // Refresh the item in queue
      loadQueue();
      break;
    case 'item_deleted':
      {
        const delItem = queueItems.find(i => i.item_id === data.item_id);
        if (delItem) shatterSkillNode(delItem.draft_name || delItem.item_id || data.item_id);
      }
      queueItems = queueItems.filter(i => i.item_id !== data.item_id);
      renderQueue();
      if (viewMode === 'panorama') buildPanoramaView();
      break;
    case 'ping':
      break;
    case 'dedup_skipped':
      stopExtractionVFX();
      addMessage('system', `⏭️ ${data.message || '该文本已萃取过'} (状态: ${data.existing_status || '—'})`);
      showToast(`⏭️ 已存在: ${data.existing_name || '已有技能'}`);
      // Highlight existing crystal
      highlightExistingCrystal(data.existing_item_id);
      break;
    case 'dedup_slug_skipped':
      addMessage('system', `⏭️ ${data.message || '同名技能已存在，跳过'}`);
      break;
    case 'dedup_all_skipped':
      stopExtractionVFX();
      addMessage('system', `⏭️ ${data.message || '所有技能均已存在'}`);
      showToast(`⏭️ 全部重复: ${(data.skipped_names || []).join(', ')}`);
      break;
    // Cross-team events
    case 'skill_published':
      addMessage('system', `🌐 团队「${escHtml(data.origin_team_id)}」发布了技能「${escHtml(data.skill_icon || '⚡')} ${escHtml(data.skill_name)}」 — <a href="#" onclick="event.preventDefault();window._importSkill('${escHtml(data.skill_id)}')">引入</a>`);
      if (viewMode === 'panorama') buildPanoramaView();
      break;
  }
}

function updateQueueItemStatus(data) {
  const item = queueItems.find(i => i.item_id === data.item_id);
  if (item) {
    if (data.status) item.status = data.status;
    if (data.status_icon) item.status_icon = data.status_icon;
    if (data.status_label) item.status_label = data.status_label;
    if (data.traffic_light) item.traffic_light = data.traffic_light;
    if (data.llm_confidence !== undefined) item.llm_confidence = data.llm_confidence;
    if (data.draft_name) item.draft_name = data.draft_name;
    if (data.draft_scope) item.draft_scope = data.draft_scope;
  }
  renderQueue();
  // Update extraction VFX based on status
  if (data.status === 'ready_for_review' || data.status === 'error') {
    stopExtractionVFX();
    rebuildSkillNodes();
  }
}

// ── Queue ───────────────────────────────────────────────────────
async function loadQueue() {
  if (!currentTeamId) return;
  const items = await api(`/teams/${currentTeamId}/skill-extract/queue`);
  if (items) { queueItems = items; renderQueue(); }
}

function renderQueue() {
  const el = document.getElementById('queue-list');
  let filtered = queueItems;
  if (currentFilter) filtered = filtered.filter(i => i.status === currentFilter);

  if (!filtered.length) {
    el.innerHTML = `<div style="text-align:center;padding:40px 20px;color:oklch(0.4 0.005 110);font-size:12px">
      暂无${currentFilter ? '此状态的' : ''}萃取项目</div>`;
    return;
  }

  el.innerHTML = filtered.map(item => {
    const scopeIs = item.skill_type || item.draft_scope || 'pending';
    const scopeBadges = {
      trait: '<span style="font-size:9px;padding:1px 5px;background:oklch(0.62 0.10 70/.15);color:oklch(0.78 0.08 70);border-radius:3px;margin-left:6px">🎯 特质</span>',
      public: '<span style="font-size:9px;padding:1px 5px;background:oklch(0.55 0.10 250/.15);color:oklch(0.78 0.08 250);border-radius:3px;margin-left:6px">🌍 公共</span>',
      reserve: '<span style="font-size:9px;padding:1px 5px;background:oklch(0.52 0.04 160/.15);color:oklch(0.72 0.06 160);border-radius:3px;margin-left:6px">📦 储备</span>',
    };
    const scopeBadge = scopeBadges[scopeIs] || '';
    const stageMap = { pending:'①采集', llm_prefilling:'①采集', ready_for_review:'②补全', approved:'④发布', rejected:'①采集' };
    const stageTag = stageMap[item.status] || '①采集';
    return `
    <div class="queue-item${selectedItemId === item.item_id ? ' selected' : ''}"
         onclick="window._openDetail('${item.item_id}')" data-id="${item.item_id}">
      <span class="status-dot ${item.status === 'approved' ? 'st-approved' : item.status === 'rejected' ? 'st-rejected' : item.status === 'ready_for_review' ? 'st-review' : 'st-pending'}">${item.status === 'approved' ? '◎' : item.status === 'rejected' ? '✕' : item.status === 'ready_for_review' ? '◈' : '○'}</span>
      <div class="qi-body">
        <div class="qi-name">${item.draft_name || item.source_title || '未命名'}${scopeBadge}</div>
        <div class="qi-meta">
          <span>${item.status_label || item.status}</span>
          <span style="font-size:9px;padding:1px 4px;background:oklch(0.62 0.1 70/.1);color:oklch(0.7 0.06 70);border-radius:2px">${stageTag}</span>
          <span class="qi-conf">${item.llm_confidence ? (item.llm_confidence * 100).toFixed(0) + '%' : '—'}</span>
        </div>
      </div>
      <div class="qi-actions">
        ${item.status === 'ready_for_review' ? `
          <button class="btn btn-sm" onclick="event.stopPropagation();window._quickApprove('${item.item_id}','reserve')" title="储备技能" style="font-size:11px">📦</button>
          <button class="btn btn-sm" onclick="event.stopPropagation();window._quickApprove('${item.item_id}','public')" title="公共技能" style="font-size:11px">🌍</button>
        ` : ''}
        <button class="btn btn-sm" onclick="event.stopPropagation();window._deleteItem('${item.item_id}')" title="删除" style="color:var(--shu);opacity:0.5">🗑️</button>
      </div>
    </div>
  `}).join('');
}

window.setQueueFilter = function(btn, filter) {
  currentFilter = filter;
  document.querySelectorAll('.queue-tabs button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderQueue();
};

// ── Submission ──────────────────────────────────────────────────
window.startExtraction = async function() {
  const text = document.getElementById('source-text').value.trim();
  if (!text || text.length < 10) { showToast('请输入至少 10 个字符的文本'); return; }
  if (!currentTeamId) { showToast('请先选择一个团队'); return; }

  const title = document.getElementById('source-title').value.trim();
  const type = document.getElementById('source-type').value;

  document.getElementById('btn-extract').disabled = true;
  document.getElementById('btn-extract').textContent = '萃取中…';

  const result = await api(`/teams/${currentTeamId}/skill-extract/start`, {
    method: 'POST',
    body: JSON.stringify({ source_text: text, source_title: title, source_type: type }),
  });

  document.getElementById('btn-extract').disabled = false;
  document.getElementById('btn-extract').textContent = '🩸 开始萃取';

  if (result) {
    // Check if this was a dedup return (existing item with status beyond 'pending')
    if (result.status && result.status !== 'pending') {
      showToast(`⏭️ 已有相同萃取: ${result.draft_name || result.source_title || result.item_id}`);
      addMessage('system', `⏭️ 该文本已萃取过技能「${result.draft_name || '—'}」(${result.status})，无需重复萃取`);
    } else {
      showToast(`萃取已启动: ${result.item_id}`);
      triggerExtractionVFX();
    }
    document.getElementById('source-text').value = '';
    document.getElementById('source-title').value = '';
  }
};

// ── Detail Modal ────────────────────────────────────────────────
window._openDetail = async function(itemId) {
  selectedItemId = itemId;
  renderQueue();
  // Update pipeline stepper for this item
  const qi = queueItems.find(q => q.item_id === itemId);
  updateStepperForItem(qi);
  const detail = await api(`/teams/${currentTeamId}/skill-extract/${itemId}`);
  if (!detail) return;

  document.getElementById('modal-icon').textContent = detail.draft_icon || '⚡';
  document.getElementById('modal-title').textContent = detail.draft_name || '技能详情';
  // Format source text with page breaks
  const srcEl = document.getElementById('modal-source');
  const srcText = detail.source_text || '';
  srcEl.innerHTML = srcText
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^(--- 第 \d+ 页 ---)$/gm, '<div style="text-align:center;color:oklch(0.45 0.06 250);font-size:10px;margin:12px 0;padding:4px 0;border-top:1px dashed oklch(0.3 0.02 250);border-bottom:1px dashed oklch(0.3 0.02 250)">$1</div>')
    .replace(/^(ROUND \d+)$/gm, '<div style="font-weight:700;color:oklch(0.7 0.08 200);margin:10px 0 4px">$1</div>')
    .replace(/^(PM|ARCHITECT|RESEARCHER|DEVELOPER|TESTER|DEPLOYER|技术研究员|测试工程师|全栈开发)(.*)$/gm, '<span style="font-weight:700;color:oklch(0.65 0.06 140)">$1</span>$2');
  document.getElementById('edit-name').value = detail.draft_name || '';
  document.getElementById('edit-desc').value = detail.draft_description || '';
  document.getElementById('edit-category').value = detail.draft_category || 'general';
  document.getElementById('edit-icon').value = detail.draft_icon || '';
  document.getElementById('edit-slug').value = detail.draft_slug || '';
  document.getElementById('edit-instructions').value = detail.draft_instructions || '';
  // Default to preview mode for readability
  const instrPreview = document.getElementById('edit-instructions-preview');
  const instrTextarea = document.getElementById('edit-instructions');
  const instrBtn = document.getElementById('btn-preview-toggle');
  instrPreview.innerHTML = formatInstructions(detail.draft_instructions || '');
  instrPreview.style.display = 'block';
  instrTextarea.style.display = 'none';
  instrBtn.textContent = '✏️ 编辑';
  document.getElementById('edit-tools').value = (detail.draft_required_tools || []).join(', ');

  const conf = detail.llm_confidence || 0;
  const confColor = conf >= 0.7 ? 'var(--atomic-green)' : conf >= 0.4 ? 'var(--trait-amber)' : 'var(--shu)';
  document.getElementById('edit-confidence-bar').style.width = (conf * 100) + '%';
  document.getElementById('edit-confidence-bar').style.background = confColor;
  document.getElementById('edit-confidence-val').textContent = (conf * 100).toFixed(0) + '% 置信度';

  // Show scope recommendation
  const scopeEl = document.getElementById('edit-scope-badge');
  if (scopeEl) {
    const sc = detail.draft_scope || 'personal';
    const scopeLabels = {
      public: '<span style="display:inline-block;font-size:10px;padding:2px 8px;background:oklch(0.55 0.10 250/.15);color:oklch(0.78 0.08 250);border-radius:3px">🌍 建议公共技能</span>',
      personal: '<span style="display:inline-block;font-size:10px;padding:2px 8px;background:oklch(0.62 0.10 70/.15);color:oklch(0.78 0.08 70);border-radius:3px">🎯 建议特质技能</span>',
    };
    scopeEl.innerHTML = scopeLabels[sc] || scopeLabels.personal;
  }

  // Show agent select for trait skill
  const agentSel = document.getElementById('approve-agent-select');
  if (agentSel) {
    updateAgentSelect();
    agentSel.style.display = '';
  }

  document.getElementById('modal-detail').classList.add('open');
  // Reset to edit tab with footer visible
  switchModalTab('edit');
  // Load pipeline data for this item
  loadItemPipeline(itemId);
};

window.closeDetail = function() {
  document.getElementById('modal-detail').classList.remove('open');
  selectedItemId = null;
  _evolveCache = null;
  renderQueue();
};

// ── Modal Tab Switching ────────────────────────────────────────
// ── Source Column Collapse / Resize ─────────────────────────────
window.toggleSourceCol = function() {
  const col = document.getElementById('modal-col-source');
  const handle = document.getElementById('modal-resize-handle');
  const btn = document.getElementById('btn-collapse-source');
  if (col.style.display === 'none') {
    col.style.display = '';
    handle.style.display = '';
    btn.textContent = '◀ 收起';
  } else {
    col.style.display = 'none';
    handle.style.display = 'none';
    btn.textContent = '▶ 展开';
  }
};

// Drag-to-resize the source column
(function initModalResize() {
  let dragging = false, startX = 0, startW = 0;
  document.addEventListener('mousedown', e => {
    if (e.target.id !== 'modal-resize-handle') return;
    dragging = true;
    startX = e.clientX;
    startW = document.getElementById('modal-col-source').offsetWidth;
    e.target.classList.add('dragging');
    e.preventDefault();
  });
  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const col = document.getElementById('modal-col-source');
    const newW = Math.max(120, Math.min(startW + e.clientX - startX, col.parentElement.offsetWidth * 0.6));
    col.style.width = newW + 'px';
  });
  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    const h = document.getElementById('modal-resize-handle');
    if (h) h.classList.remove('dragging');
  });
})();

// ── Instruction Preview Toggle ──────────────────────────────────
window.toggleInstructionPreview = function() {
  const textarea = document.getElementById('edit-instructions');
  const preview = document.getElementById('edit-instructions-preview');
  const btn = document.getElementById('btn-preview-toggle');
  if (preview.style.display === 'none') {
    // Render formatted preview
    preview.innerHTML = formatInstructions(textarea.value);
    preview.style.display = 'block';
    textarea.style.display = 'none';
    btn.textContent = '✏️ 编辑';
  } else {
    preview.style.display = 'none';
    textarea.style.display = 'block';
    btn.textContent = '👁 预览';
  }
};

function formatInstructions(text) {
  if (!text) return '<span style="color:oklch(0.4 0.005 110)">暂无指令内容</span>';
  // Simple markdown-like rendering
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // Headers: ## or ### or #
    .replace(/^### (.+)$/gm, '<div style="font-size:12px;font-weight:700;color:oklch(0.75 0.06 200);margin:12px 0 4px;border-bottom:1px solid oklch(0.25 0.02 200);padding-bottom:3px">$1</div>')
    .replace(/^## (.+)$/gm, '<div style="font-size:13px;font-weight:700;color:oklch(0.8 0.08 250);margin:14px 0 6px;border-bottom:1px solid oklch(0.25 0.02 250);padding-bottom:4px">$1</div>')
    .replace(/^# (.+)$/gm, '<div style="font-size:14px;font-weight:700;color:oklch(0.85 0.08 250);margin:16px 0 8px;border-bottom:2px solid oklch(0.25 0.02 250);padding-bottom:4px">$1</div>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<b style="color:oklch(0.85 0.02 60)">$1</b>')
    // Bullet lists
    .replace(/^[-•] (.+)$/gm, '<div style="padding-left:16px;margin:2px 0"><span style="color:oklch(0.5 0.08 200)">●</span> $1</div>')
    // Numbered lists
    .replace(/^(\d+)\. (.+)$/gm, '<div style="padding-left:16px;margin:2px 0"><span style="color:oklch(0.6 0.08 250);font-weight:600">$1.</span> $2</div>')
    // Empty lines → spacing
    .replace(/\n\n/g, '<div style="height:8px"></div>')
    .replace(/\n/g, '<br>');
}

window.switchModalTab = function(tab) {
  document.querySelectorAll('.modal-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  document.querySelectorAll('.modal-tab-content').forEach(c => {
    c.classList.toggle('active', c.id === 'tab-' + tab);
    c.style.display = c.id === 'tab-' + tab ? 'flex' : 'none';
  });
  // Show footer (save/approve/reject) only on edit tab
  const footer = document.getElementById('modal-footer-actions');
  if (footer) footer.style.display = (tab === 'edit') ? 'flex' : 'none';
  if (tab === 'evolve') loadEvolveTab();
  if (tab === 'verify') loadVerifyTab();
  if (tab === 'usage') loadUsageTab();
  if (tab === 'version') loadVersionTab();
  if (tab === 'pipeline') loadPipelineTab();
};

// ── Evolve Tab ─────────────────────────────────────────────────
let _evolveCache = null;

// Helper: resolve skill_id from queue item (checks skill_draft, then looks up by slug in skills array)
function resolveSkillId(item) {
  if (!item) return '';
  if (item.skill_draft?.skill_id) return item.skill_draft.skill_id;
  // After approval, find by slug in loaded skills
  const slug = item.draft_slug;
  if (slug && allSkills?.length) {
    const found = allSkills.find(s => s.slug === slug);
    if (found) return found.skill_id || found.slug;
  }
  // Approved items can use draft_slug as fallback
  if (item.status === 'approved' && slug) return slug;
  return '';
}

function loadEvolveTab() {
  if (!selectedItemId) return;
  const item = queueItems.find(q => q.item_id === selectedItemId);
  if (!item) return;
  const registeredSkill = allSkills?.find(s => s.slug === item.draft_slug) || {};
  const statsEl = document.getElementById('evolve-stats');
  statsEl.innerHTML = `
    <span>📊 使用: ${registeredSkill.usage_count || 0}次</span>
    <span>✅ 成功率: ${((registeredSkill.effectiveness || 0) * 100).toFixed(0)}%</span>
    <span>📈 版本: v${registeredSkill.version || 1}</span>
    <span>🏷️ 阶段: ${registeredSkill.lifecycle_stage || item.status || 'draft'}</span>
  `;
  // Load suggestions
  loadEvolveSuggestions();
}

async function loadEvolveSuggestions() {
  const data = await listApi(`/skill-library/suggestions?team_id=${encodeURIComponent(currentTeamId)}`);
  const el = document.getElementById('evolve-suggestions');
  if (data.length === 0) {
    el.innerHTML = '<div style="color:oklch(0.4 0.005 110);padding:8px 0">暂无演化建议</div>';
    return;
  }
  el.innerHTML = '<h5 style="margin:8px 0 4px;color:oklch(0.6 0.005 110)">💡 演化建议</h5>' +
    data.map(s => `<div style="padding:4px 0;border-bottom:1px solid oklch(0.15 0.005 110)">${s.reason} — <b>${s.name || ''}</b> <span style="color:oklch(0.4 0.005 110)">[${s.action}]</span></div>`).join('');
}

window.triggerEvolve = async function() {
  if (!selectedItemId) return;
  const item = queueItems.find(q => q.item_id === selectedItemId);
  if (!item) return;
  if (item.status !== 'approved') { showToast('需要先批准入库才能演化'); return; }
  const skillId = resolveSkillId(item);
  if (!skillId) { showToast('找不到已注册的技能ID'); return; }
  document.getElementById('btn-evolve').textContent = '⏳ 演化中...';
  document.getElementById('btn-evolve').disabled = true;
  const result = await api('/skill-library/evolve', {
    method: 'POST',
    body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId }),
  });
  document.getElementById('btn-evolve').textContent = '⚡ 触发演化';
  document.getElementById('btn-evolve').disabled = false;
  if (!result || result.error) { showToast('演化失败: ' + (result?.error || 'unknown')); return; }
  _evolveCache = result;
  const diffEl = document.getElementById('evolve-diff');
  diffEl.style.display = 'block';
  document.getElementById('evolve-old').textContent = result.original_instructions || '';
  document.getElementById('evolve-new').textContent = result.improved_instructions || '';
  showToast('🧬 演化完成，请审阅');
};

window.acceptEvolution = async function() {
  if (!_evolveCache) return;
  const item = queueItems.find(q => q.item_id === selectedItemId);
  const skillId = resolveSkillId(item);
  if (!skillId) return;

  // Find the crystal node for this skill before applying
  const skillName = item?.draft_name || '';
  const targetNode = skillNodes.find(n => n.userData.skill?.skill_id === skillId || n.userData.skill?.name === skillName);

  const result = await api('/skill-library/apply-evolution', {
    method: 'POST',
    body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId, new_instructions: _evolveCache.improved_instructions }),
  });
  if (result && !result.error) {
    showToast('✅ 演化已应用 v' + result.version);
    document.getElementById('evolve-diff').style.display = 'none';
    _evolveCache = null;

    // Evolution VFX: light beam → shrink → expand
    if (targetNode) triggerEvolutionVFX(targetNode);

    loadQueue(); loadSkills();
  }
};

window.discardEvolution = function() {
  document.getElementById('evolve-diff').style.display = 'none';
  _evolveCache = null;
  showToast('已丢弃演化草稿');
};

// ── Evolution VFX: light beam → shrink → expand ────────────────
function triggerEvolutionVFX(node) {
  const pos = node.position.clone();
  // Light beam from above
  const beamGeo = new THREE.CylinderGeometry(0.02, 0.15, 4, 8, 1, true);
  const beamMat = new THREE.MeshBasicMaterial({
    color: 0xD4A574, transparent: true, opacity: 0.5,
    blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
  });
  const beam = new THREE.Mesh(beamGeo, beamMat);
  beam.position.set(pos.x, pos.y + 2.5, pos.z);
  beam.userData._evolveBeam = { start: clock.getElapsedTime() };
  extractionGroup.add(beam);

  // Flash point light
  const flash = new THREE.PointLight(0xD4A574, 3, 5);
  flash.position.set(pos.x, pos.y + 1, pos.z);
  extractionGroup.add(flash);

  // Animate: shrink → expand via userData flag
  node.userData._evolving = { start: clock.getElapsedTime(), origScale: node.scale.x };
  // Cleanup after 2.5s
  setTimeout(() => {
    extractionGroup.remove(beam); beam.geometry.dispose(); beam.material.dispose();
    extractionGroup.remove(flash);
    delete node.userData._evolving;
    node.scale.set(1, 1, 1);
  }, 2500);
}

// ── Verify Tab ─────────────────────────────────────────────────
// ── Usage / Before-After Tab ───────────────────────────────────
function loadUsageTab() {
  if (!selectedItemId) return;
  const item = queueItems.find(q => q.item_id === selectedItemId);
  if (!item) return;
  const skillId = resolveSkillId(item) || item.draft_slug || '';

  // Fetch current skill state from team skills
  const fetchCurrent = async () => {
    if (!skillId) {
      renderUsageEmpty('尚未批准入库，无法查看效果');
      return;
    }
    const skills = await listApi(`/teams/${currentTeamId}/skills`);
    const current = skills.find(s => s.skill_id === skillId || s.slug === skillId || s.slug === item.draft_slug);

    // Metrics cards
    const usage = current?.usage_count || 0;
    const eff = current?.effectiveness || 0;
    const successCount = usage > 0 ? Math.round(usage * eff) : 0;
    const failCount = usage - successCount;
    const quality = current?.quality_score || 0;

    document.getElementById('usage-metrics').innerHTML = [
      metricCard('📊', '使用次数', usage, ''),
      metricCard('✅', '成功率', usage > 0 ? (eff * 100).toFixed(0) + '%' : '—', eff >= 0.7 ? 'var(--atomic-green)' : eff >= 0.4 ? 'var(--trait-amber)' : 'var(--shu)'),
      metricCard('⚡', '质量分', (quality * 100).toFixed(0) + '%', quality >= 0.7 ? 'var(--atomic-green)' : quality >= 0.4 ? 'var(--trait-amber)' : 'var(--shu)'),
      metricCard('🕐', '最近使用', current?.last_used_at ? new Date(current.last_used_at).toLocaleDateString('zh-CN') : '—', ''),
    ].join('');

    // Before state (from extraction draft)
    const beforeLines = [
      `<b>名称:</b> ${item.draft_name || '—'}`,
      `<b>类别:</b> ${item.draft_category || '—'}`,
      `<b>置信度:</b> ${((item.llm_confidence || 0) * 100).toFixed(0)}%`,
      `<b>质量分:</b> 0%`,
      `<b>使用次数:</b> 0`,
      `<b>成功率:</b> —`,
      `<b>生命周期:</b> draft`,
      `<b>可见性:</b> ${item.draft_scope || 'personal'}`,
      `<b>版本:</b> v1`,
      `<b style="color:oklch(0.5 0.02 20)">指令 (${(item.draft_instructions || '').length}字):</b>`,
      `<pre style="margin:4px 0 0;font-size:10px;white-space:pre-wrap;color:oklch(0.55 0.005 110);max-height:120px;overflow-y:auto">${escHtml((item.draft_instructions || '').slice(0, 300))}${(item.draft_instructions || '').length > 300 ? '…' : ''}</pre>`,
    ];
    document.getElementById('usage-before').innerHTML = beforeLines.join('<br>');

    // After state (current from team skills)
    if (!current) {
      document.getElementById('usage-after').innerHTML = '<div style="text-align:center;padding:20px;color:oklch(0.45 0.005 110)">⏳ 技能已批准但尚未被使用<br><span style="font-size:10px">使用后数据将在此处更新</span></div>';
      document.getElementById('usage-diff-summary').textContent = '初始状态';
    } else {
      const afterLines = [
        `<b>名称:</b> ${current.name || '—'}`,
        `<b>类别:</b> ${current.category || '—'}`,
        `<b>置信度:</b> —`,
        `<b>质量分:</b> <span style="color:${quality > 0 ? 'var(--atomic-green)' : 'inherit'}">${(quality * 100).toFixed(0)}%</span>`,
        `<b>使用次数:</b> <span style="color:${usage > 0 ? 'var(--atomic-green)' : 'inherit'}">${usage}</span>`,
        `<b>成功率:</b> <span style="color:${eff >= 0.7 ? 'var(--atomic-green)' : eff >= 0.4 ? 'var(--trait-amber)' : 'inherit'}">${usage > 0 ? (eff * 100).toFixed(0) + '%' : '—'}</span>`,
        `<b>生命周期:</b> <span style="color:var(--koke)">${current.lifecycle_stage || '—'}</span>`,
        `<b>可见性:</b> ${current.visibility || 'private'}`,
        `<b>版本:</b> v${current.version || 1}`,
        `<b style="color:oklch(0.55 0.04 140)">指令变化:</b>`,
        current.has_instructions
          ? `<span style="font-size:10px;color:oklch(0.6 0.04 140)">✓ 指令已写入技能库</span>`
          : `<span style="font-size:10px;color:oklch(0.5 0.02 20)">— 无指令</span>`,
      ];
      document.getElementById('usage-after').innerHTML = afterLines.join('<br>');

      // Diff summary
      const changes = [];
      if (usage > 0) changes.push(`使用 ${usage} 次`);
      if (current.version > 1) changes.push(`演化 v${current.version}`);
      if (current.visibility !== (item.draft_scope || 'personal')) changes.push('可见性变更');
      document.getElementById('usage-diff-summary').textContent = changes.length ? changes.join(' · ') : '无变化';
    }

    // Timeline
    if (usage > 0) {
      const barWidth = Math.min(usage * 10, 100);
      document.getElementById('usage-timeline').innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
          <span style="width:60px;font-size:10px;color:oklch(0.5 0.005 110)">成功</span>
          <div style="flex:1;height:8px;background:oklch(0.15 0.005 60);border-radius:4px;overflow:hidden">
            <div style="width:${eff * 100}%;height:100%;background:oklch(0.52 0.1 140);transition:width .5s"></div>
          </div>
          <span style="font-size:10px;font-family:var(--font-mono);color:oklch(0.6 0.005 110)">${successCount}</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <span style="width:60px;font-size:10px;color:oklch(0.5 0.005 110)">失败</span>
          <div style="flex:1;height:8px;background:oklch(0.15 0.005 60);border-radius:4px;overflow:hidden">
            <div style="width:${usage > 0 ? ((1 - eff) * 100) : 0}%;height:100%;background:oklch(0.55 0.12 22);transition:width .5s"></div>
          </div>
          <span style="font-size:10px;font-family:var(--font-mono);color:oklch(0.6 0.005 110)">${failCount}</span>
        </div>
      `;
    } else {
      document.getElementById('usage-timeline').innerHTML = '<div style="text-align:center;padding:16px;color:oklch(0.4 0.005 110);font-size:11px">📈 使用数据将在技能被调用后显示</div>';
    }
  };
  fetchCurrent();
}

function metricCard(icon, label, value, color) {
  const valStyle = color ? `color:${color}` : 'color:oklch(0.85 0.003 110)';
  return `<div style="text-align:center;padding:12px;background:oklch(0.1 0.005 60);border:1px solid oklch(1 0 0/.06);border-radius:6px">
    <div style="font-size:18px;margin-bottom:4px">${icon}</div>
    <div style="font-size:18px;font-weight:700;font-family:var(--font-mono);${valStyle}">${value}</div>
    <div style="font-size:9px;color:oklch(0.45 0.005 110);margin-top:2px">${label}</div>
  </div>`;
}

function renderUsageEmpty(msg) {
  document.getElementById('usage-metrics').innerHTML = '';
  document.getElementById('usage-before').innerHTML = `<div style="text-align:center;padding:20px;color:oklch(0.4 0.005 110)">${msg}</div>`;
  document.getElementById('usage-after').innerHTML = '';
  document.getElementById('usage-timeline').innerHTML = '';
  document.getElementById('usage-diff-summary').textContent = '';
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

window.refreshUsageTab = function() { loadUsageTab(); showToast('🔄 已刷新'); };

// ── Usage Chat: Interactive Skill Optimization ─────────────────
let _usageChatHistory = [];

function _addUsageChatMsg(role, text) {
  const log = document.getElementById('usage-chat-log');
  const div = document.createElement('div');
  div.style.cssText = role === 'user'
    ? 'padding:6px 10px;margin:4px 0;background:oklch(0.18 0.01 60);border:1px solid oklch(1 0 0/.08);color:oklch(0.85 0.003 110);max-width:85%;margin-left:auto;font-size:11px;line-height:1.5'
    : 'padding:6px 10px;margin:4px 0;background:oklch(0.14 0.008 250/.3);border:1px solid oklch(0.55 0.1 250/.15);color:oklch(0.78 0.005 110);max-width:90%;font-size:11px;line-height:1.5;white-space:pre-wrap';
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

window.usageChatSend = async function() {
  const input = document.getElementById('usage-chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  const item = queueItems.find(q => q.item_id === selectedItemId);
  if (!item) { showToast('请先选择一个技能'); return; }
  const skillId = resolveSkillId(item);
  const skillName = item.draft_name || '';
  const instructions = item.draft_instructions || '';

  _addUsageChatMsg('user', text);
  _addUsageChatMsg('system', '⏳ 思考中...');

  const result = await api('/skill-library/evolve', {
    method: 'POST',
    body: JSON.stringify({
      team_id: currentTeamId,
      skill_id: skillId || item.draft_slug,
      user_feedback: text,
    }),
  });

  // Remove "thinking" message
  const log = document.getElementById('usage-chat-log');
  log.lastChild?.remove();

  if (result && !result.error && result.improved_instructions) {
    _addUsageChatMsg('assistant', `💡 改进建议:\n\n${result.improved_instructions.slice(0, 500)}${result.improved_instructions.length > 500 ? '…' : ''}`);
    // Offer apply button
    const applyDiv = document.createElement('div');
    applyDiv.style.cssText = 'display:flex;gap:6px;padding:4px 0;justify-content:flex-end';
    applyDiv.innerHTML = `<button class="btn btn-sm" onclick="applyUsageChatEvolution()" style="font-size:9px;padding:2px 8px;background:oklch(0.52 0.04 160/.15);border-color:oklch(0.52 0.04 160/.3);color:oklch(0.65 0.06 155)">✅ 应用改进</button>
      <button class="btn btn-sm" onclick="this.parentElement.remove()" style="font-size:9px;padding:2px 8px">忽略</button>`;
    log.appendChild(applyDiv);
    log.scrollTop = log.scrollHeight;
    window._lastChatEvolution = result;
  } else {
    _addUsageChatMsg('assistant', `⚠️ ${result?.error || '无法生成改进建议，请重试'}`);
  }
};

window.applyUsageChatEvolution = async function() {
  const result = window._lastChatEvolution;
  if (!result) return;
  const item = queueItems.find(q => q.item_id === selectedItemId);
  const skillId = resolveSkillId(item);
  if (!skillId) return;

  const applyResult = await api('/skill-library/apply-evolution', {
    method: 'POST',
    body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId, new_instructions: result.improved_instructions }),
  });
  if (applyResult && !applyResult.error) {
    _addUsageChatMsg('system', `✅ 已应用改进，版本更新为 v${applyResult.version}`);
    showToast(`✅ 技能已优化到 v${applyResult.version}`);
    window._lastChatEvolution = null;
    loadSkills();
    loadUsageTab();
  } else {
    _addUsageChatMsg('system', `❌ 应用失败: ${applyResult?.error || 'unknown'}`);
  }
};

window.usageChatSuggest = function(type) {
  const prompts = {
    improve: '请分析这个技能的薄弱环节，给出具体的改进建议',
    simplify: '请精简这个技能的指令，去掉冗余步骤，保留核心逻辑',
    edge: '请为这个技能补充边界场景和异常处理的指导',
  };
  document.getElementById('usage-chat-input').value = prompts[type] || '';
  usageChatSend();
};

function loadVerifyTab() {
  // Reset to initial state
  document.getElementById('verify-results').style.display = 'none';
  document.getElementById('verify-status').textContent = '尚未执行验证';
}

window.triggerVerify = async function() {
  if (!selectedItemId) return;
  const item = queueItems.find(q => q.item_id === selectedItemId);
  if (item && item.status !== 'approved') { showToast('需要先批准入库才能验证'); return; }
  const skillId = resolveSkillId(item);
  if (!skillId) { showToast('找不到已注册的技能ID'); return; }
  document.getElementById('btn-verify').textContent = '⏳ 验证中...';
  document.getElementById('btn-verify').disabled = true;
  document.getElementById('verify-status').textContent = '🔬 正在生成测试场景并执行...';

  // Add scanning ring to the skill's crystal in Three.js
  const skillName = item?.draft_name || '';
  const targetNode = skillNodes.find(n => n.userData.skill?.name === skillName || n.userData.skill?.skill_id === skillId);
  let scanRing = null;
  if (targetNode) {
    const pos = targetNode.position;
    const r = targetNode.geometry?.parameters?.radius || 0.3;
    scanRing = new THREE.Mesh(
      new THREE.TorusGeometry(r * 1.5, 0.015, 8, 32),
      new THREE.MeshBasicMaterial({ color: 0xFFD700, transparent: true, opacity: 0.6, side: THREE.DoubleSide })
    );
    scanRing.position.copy(pos);
    scanRing.userData._scanRing = true;
    scanRing.userData._scanStart = clock.getElapsedTime();
    extractionGroup.add(scanRing);
  }

  const result = await api('/skill-library/verify', {
    method: 'POST',
    body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId }),
  });
  document.getElementById('btn-verify').textContent = '🧪 开始验证';
  document.getElementById('btn-verify').disabled = false;

  // Remove/transform scan ring based on result
  if (scanRing) {
    if (result && result.status === 'verified') {
      // Solidify to green verify ring
      scanRing.material.color.set(0x4CAF50);
      scanRing.material.opacity = 0.35;
      scanRing.userData._scanRing = false;
      scanRing.userData.isVerifyRing = true;
    } else {
      // Shatter the scan ring into particles
      scanRing.material.color.set(0xFF4444);
      const ringPos = scanRing.position.clone();
      const shatterCount = 20;
      const shatterGeo = new THREE.BufferGeometry();
      const shatterPos = new Float32Array(shatterCount * 3);
      const shatterVels = [];
      for (let i = 0; i < shatterCount; i++) {
        const a = (i / shatterCount) * Math.PI * 2;
        const r = scanRing.geometry.parameters?.radius || 0.5;
        shatterPos[i * 3] = ringPos.x + Math.cos(a) * r;
        shatterPos[i * 3 + 1] = ringPos.y + Math.sin(a) * r * 0.3;
        shatterPos[i * 3 + 2] = ringPos.z + Math.sin(a) * r;
        shatterVels.push(new THREE.Vector3(
          Math.cos(a) * 0.06 + (Math.random() - 0.5) * 0.03,
          Math.random() * 0.04,
          Math.sin(a) * 0.06 + (Math.random() - 0.5) * 0.03
        ));
      }
      shatterGeo.setAttribute('position', new THREE.BufferAttribute(shatterPos, 3));
      const shatterMat = new THREE.PointsMaterial({
        color: 0xFF4444, size: 0.04, transparent: true, opacity: 0.8,
        blending: THREE.AdditiveBlending, depthWrite: false
      });
      const shatterPts = new THREE.Points(shatterGeo, shatterMat);
      shatterPts.userData._shatter = { velocities: shatterVels, startTime: clock.getElapsedTime(), duration: 1.2 };
      scene.add(shatterPts);
      // Remove original scan ring
      extractionGroup.remove(scanRing);
      scanRing.geometry.dispose();
      scanRing.material.dispose();
    }
  }

  if (!result) { document.getElementById('verify-status').textContent = '验证失败'; return; }
  // Show results
  document.getElementById('verify-status').style.display = 'none';
  document.getElementById('verify-results').style.display = 'block';
  const pr = (result.pass_rate * 100).toFixed(0);
  document.getElementById('verify-pass-rate').textContent = pr + '%';
  document.getElementById('verify-pass-rate').style.color = result.pass_rate >= 0.7 ? 'oklch(0.7 0.1 140)' : 'oklch(0.7 0.1 25)';
  document.getElementById('verify-passed').textContent = result.passed;
  document.getElementById('verify-failed').textContent = result.failed;
  const detailsEl = document.getElementById('verify-details');

  // Build detailed results including process log
  let html = '<div style="margin-top:8px"><b>测试场景:</b></div><div style="max-height:200px;overflow-y:auto;margin:4px 0">';
  html += (result.test_details || []).map((t, i) =>
    `<div style="padding:4px 0;border-bottom:1px solid oklch(0.15 0.005 110)">${t.passed ? '✅' : '❌'} 测试${(t.test_index || i + 1)}: ${t.scenario}</div>`
  ).join('');
  html += '</div>';

  // Show process log for transparency
  if (result.process_log && result.process_log.length) {
    html += '<div style="margin-top:12px"><b>📋 执行日志:</b></div><div style="max-height:250px;overflow-y:auto;font-family:monospace;font-size:11px;background:oklch(0.1 0.005 110);padding:8px;border-radius:4px;margin:4px 0">';
    html += result.process_log.map(l =>
      `<div style="padding:1px 0;color:${l.passed === false ? 'oklch(0.7 0.1 25)' : 'oklch(0.5 0.01 110)'}">  ${escapeHtml(l.msg || '')}</div>`
    ).join('');
    html += '</div>';
  }
  if (result.error_detail) {
    html += `<div style="margin-top:6px;color:oklch(0.7 0.1 25);font-size:12px">⚠️ ${escapeHtml(result.error_detail)}</div>`;
  }
  const evidence = result.verification_evidence || {};
  const runtime = evidence.runtime || {};
  const runtimeMode = result.runtime_mode || evidence.runtime_mode || runtime.mode || 'unknown';
  const runtimeReady = result.runtime_ready ?? evidence.runtime_ready ?? runtime.ready;
  const exitCode = result.exit_code ?? evidence.exit_code;
  html += '<div style="margin-top:12px;border:1px solid oklch(0.18 0.01 110);border-radius:6px;padding:10px;background:oklch(0.105 0.006 110)">';
  html += '<div style="font-weight:700;margin-bottom:6px">沙箱 / 容器验证证据</div>';
  html += `<div style="font-size:12px;color:oklch(0.55 0.01 110)">runtime: <b>${escapeHtml(runtimeMode)}</b> · ready: <b>${runtimeReady ? 'yes' : 'no'}</b> · exit: <b>${escapeHtml(String(exitCode ?? '-'))}</b></div>`;
  if (result.docker_image || evidence.docker_image || runtime.docker_image) {
    html += `<div style="font-size:12px;color:oklch(0.55 0.01 110)">docker image: ${escapeHtml(result.docker_image || evidence.docker_image || runtime.docker_image || '')}</div>`;
  }
  if (result.command || evidence.command) {
    html += `<div style="font-size:12px;color:oklch(0.55 0.01 110)">command: <code>${escapeHtml(result.command || evidence.command || '')}</code></div>`;
  }
  if (result.artifact_dir || evidence.artifact_dir) {
    html += `<div style="font-size:12px;color:oklch(0.55 0.01 110)">artifact: <code>${escapeHtml(result.artifact_dir || evidence.artifact_dir || '')}</code></div>`;
  }
  if (result.stdout || evidence.stdout || result.stderr || evidence.stderr) {
    html += '<details style="margin-top:8px"><summary style="cursor:pointer;font-size:12px">stdout / stderr</summary>';
    html += `<pre style="white-space:pre-wrap;max-height:180px;overflow:auto;font-size:11px;background:oklch(0.08 0.005 110);padding:8px;border-radius:4px">${escapeHtml((result.stdout || evidence.stdout || '') + (result.stderr || evidence.stderr ? '\n--- stderr ---\n' + (result.stderr || evidence.stderr || '') : ''))}</pre>`;
    html += '</details>';
  }
  if (runtime.self_check_blocked) {
    html += `<div style="font-size:12px;color:oklch(0.7 0.1 25);margin-top:6px">runtime blocked: ${escapeHtml(runtime.ready_reason || 'self check blocked')}</div>`;
  }
  html += '</div>';
  detailsEl.innerHTML = html;

  showToast(result.status === 'verified' ? '✅ 验证通过' : '❌ 验证未通过');
  // Rebuild to reflect lifecycle changes
  if (result.status === 'verified') { loadSkills(); }
};

// ── Version Tab ────────────────────────────────────────────────
async function loadVersionTab() {
  if (!selectedItemId) return;
  const item = queueItems.find(q => q.item_id === selectedItemId);
  const skillId = resolveSkillId(item);
  const el = document.getElementById('version-timeline');
  const diffEl = document.getElementById('version-diff');
  const curEl = document.getElementById('version-current');
  diffEl.style.display = 'none';
  
  // Get actual version from team skill (not queue item which has no version)
  const teamSkill = allSkills?.find(s => s.skill_id === skillId || s.slug === (item?.draft_slug || ''));
  const curVer = teamSkill?.version || item?.draft_version || 1;
  document.getElementById('ver-current-num').textContent = `v${curVer}`;
  document.getElementById('ver-next-num').textContent = curVer + 1;
  document.getElementById('ver-lifecycle').textContent = teamSkill?.lifecycle_stage || item?.status || 'draft';

  if (!skillId) { el.innerHTML = '暂无版本历史'; curEl.textContent = ''; return; }
  curEl.textContent = `v${curVer}`;
  const data = await api(`/skill-library/${skillId}/evolution-history?team_id=${currentTeamId}`);

  // Parse lineage response: { skill_id, lineage: { ancestors: [], current: {}, children: [] } }
  const lineage = data?.lineage || {};
  const ancestors = lineage.ancestors || [];
  const current = lineage.current;
  const evolveCount = ancestors.length + (current ? 1 : 0);
  document.getElementById('ver-evolve-count').textContent = Math.max(0, evolveCount - 1);

  if (!current && ancestors.length === 0) {
    el.innerHTML = `<div style="padding:12px 0;text-align:center;color:oklch(0.4 0.005 110)">📌 当前版本 v${curVer} · 暂无演化历史</div>`;
    return;
  }

  // Build timeline: ancestors (oldest first) + current
  const timelineItems = [...ancestors];
  if (current) timelineItems.push(current);
  // If only current exists (no ancestors), show single version
  if (timelineItems.length <= 1 && curVer <= 1) {
    el.innerHTML = `<div style="padding:12px 0;text-align:center;color:oklch(0.4 0.005 110)">📌 当前版本 v${curVer} · 暂无演化历史</div>`;
    return;
  }

  el.innerHTML = timelineItems.map((vData, idx) => {
    const isCurrent = idx === timelineItems.length - 1;
    const verNum = vData.version || (idx + 1);
    const dotColor = isCurrent ? 'oklch(0.7 0.1 140)' : 'oklch(0.5 0.03 80)';
    const lineColor = idx < timelineItems.length - 1 ? 'oklch(0.25 0.02 80)' : 'transparent';
    const ts = vData.last_used_at ? new Date(vData.last_used_at).toLocaleString('zh-CN', {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';
    const stage = vData.lifecycle_stage || '';
    return `<div style="display:flex;gap:10px;position:relative">
      <div style="display:flex;flex-direction:column;align-items:center;min-width:12px">
        <div style="width:8px;height:8px;border-radius:50%;background:${dotColor};flex-shrink:0;margin-top:4px"></div>
        <div style="width:1px;flex:1;background:${lineColor}"></div>
      </div>
      <div style="padding-bottom:12px;flex:1">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-weight:600;color:${isCurrent ? 'oklch(0.82 0.003 110)' : 'oklch(0.6 0.005 110)'}">v${verNum}${isCurrent ? ' ← 当前' : ''}</span>
          <span style="font-size:9px;color:oklch(0.4 0.005 110)">${ts} ${stage}</span>
        </div>
        ${vData.name ? `<div style="font-size:10px;color:oklch(0.5 0.005 110);margin-top:2px">${escHtml(vData.name)}</div>` : ''}
        <div style="margin-top:4px;display:flex;gap:6px">
          ${idx > 0 ? `<button class="btn" style="font-size:9px;padding:2px 8px" onclick="showVersionDiff(${idx}, ${idx - 1})">diff</button>` : ''}
          ${!isCurrent ? `<button class="btn" style="font-size:9px;padding:2px 8px" onclick="rollbackVersion('v${verNum}')">rollback</button>` : ''}
        </div>
      </div>
    </div>`;
  }).join('');
  // Store entries for diff
  window._versionEntries = timelineItems.map((v, i) => [`v${v.version || i + 1}`, v]);
}
window.showVersionDiff = function(idxA, idxB) {
  const entries = window._versionEntries;
  if (!entries) return;
  const [, a] = entries[idxA] || [];
  const [, b] = entries[idxB] || [];
  if (!a || !b) return;
  const diffEl = document.getElementById('version-diff');
  // Simple field-level diff
  const allKeys = new Set([...Object.keys(a), ...Object.keys(b)]);
  let html = '<div style="margin-bottom:4px;color:oklch(0.6 0.005 110)">变更对比:</div>';
  for (const k of allKeys) {
    if (k === 'timestamp') continue;
    const va = JSON.stringify(a[k]) || '';
    const vb = JSON.stringify(b[k]) || '';
    if (va !== vb) {
      html += `<div style="color:oklch(0.7 0.1 25)">- ${k}: ${vb}</div>`;
      html += `<div style="color:oklch(0.7 0.1 140)">+ ${k}: ${va}</div>`;
    }
  }
  diffEl.innerHTML = html;
  diffEl.style.display = 'block';
};
window.rollbackVersion = async function(versionKey) {
  const targetVer = parseInt(versionKey.replace('v', ''));
  if (!targetVer || !currentTeamId || !skillId) {
    showToast('缺少必要信息: team_id/skill_id/version'); return;
  }
  showConfirm(`确认回滚技能到版本 v${targetVer}？\n当前版本将自动保存为快照。`, async () => {
    showToast('正在回滚...');
    const r = await api('/skill-library/version/rollback', {
      method: 'POST',
      body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId, target_version: targetVer }),
    });
    if (r && r.ok) {
      showToast(`✅ 已回滚到 v${targetVer}（新版本号: v${r.new_version}）`);
      loadVersionTab();
    } else {
      showToast(`回滚失败: ${r?.error || '未知错误'}`, true);
    }
  });
};

// ── Version Creation Functions ─────────────────────────────────
window.createNewVersion = function() {
  document.getElementById('version-create-form').style.display = 'block';
  document.getElementById('version-changelog').focus();
};
window.cancelNewVersion = function() {
  document.getElementById('version-create-form').style.display = 'none';
  document.getElementById('version-changelog').value = '';
};
window.confirmNewVersion = async function() {
  const item = queueItems.find(q => q.item_id === selectedItemId);
  if (!item) return;
  const skillId = resolveSkillId(item);
  if (!skillId) { showToast('技能尚未入库'); return; }
  const changelog = document.getElementById('version-changelog').value.trim();
  
  // Apply current instructions as a new version via evolve + apply
  const result = await api('/skill-library/evolve', {
    method: 'POST',
    body: JSON.stringify({
      team_id: currentTeamId,
      skill_id: skillId,
      user_feedback: changelog || '创建新版本快照',
    }),
  });
  if (result && result.improved_instructions) {
    const applyResult = await api('/skill-library/apply-evolution', {
      method: 'POST',
      body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId, new_instructions: result.improved_instructions }),
    });
    if (applyResult && !applyResult.error) {
      showToast(`✅ 版本已更新到 v${applyResult.version}`);
      cancelNewVersion();
      loadVersionTab();
      loadSkills();
      return;
    }
  }
  showToast('❌ 版本创建失败', 'error');
};

window.saveEdits = async function() {
  if (!selectedItemId) return;
  const updates = {
    name: document.getElementById('edit-name').value,
    description: document.getElementById('edit-desc').value,
    category: document.getElementById('edit-category').value,
    icon: document.getElementById('edit-icon').value,
    slug: document.getElementById('edit-slug').value,
    instructions: document.getElementById('edit-instructions').value,
    required_tools: document.getElementById('edit-tools').value.split(',').map(s => s.trim()).filter(Boolean),
  };
  const r = await api(`/teams/${currentTeamId}/skill-extract/${selectedItemId}/edit`, {
    method: 'POST',
    body: JSON.stringify({ field_updates: updates }),
  });
  if (r) { showToast('已保存'); loadQueue(); }
};

async function publishSkillWithGate(skillId, skillName) {
  if (!skillId) return { error: 'missing_skill_id' };
  const gate = await api('/skill-library/publish-gate', {
    method: 'POST',
    body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId }),
  });
  if (gate && gate.ok === false) {
    const latest = gate.latest_evidence || {};
    const checks = (gate.checks || []).map(c => `${c.passed ? '✓' : '✕'} ${c.name}: ${c.detail}`).join('<br>');
    addMessage('system', `🚧 技能「${skillName || skillId}」未通过发布门禁。<br>${checks || gate.reason || '缺少验证证据'}${latest.evidence_id ? `<br>证据: <code>${latest.evidence_id}</code> · ${latest.command || ''}` : ''}`);
    showToast('发布门禁未通过，请先完成技能验证', 'error');
    return { error: 'publish_gate_blocked', gate };
  }
  const pr = await api('/skill-library/publish', {
    method: 'POST',
    body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId }),
  });
  if (pr && pr.error === 'publish_gate_blocked') {
    addMessage('system', `🚧 技能「${skillName || skillId}」发布被质量门禁阻断，请查看最近验证证据。`);
    showToast('发布门禁未通过', 'error');
  }
  return pr;
}

window.approveAs = async function(skillType) {
  if (!selectedItemId) return;
  const edits = {
    name: document.getElementById('edit-name').value,
    description: document.getElementById('edit-desc').value,
    category: document.getElementById('edit-category').value,
    icon: document.getElementById('edit-icon').value,
    slug: document.getElementById('edit-slug').value,
    instructions: document.getElementById('edit-instructions').value,
    required_tools: document.getElementById('edit-tools').value.split(',').map(s => s.trim()).filter(Boolean),
  };
  const body = { reviewer: 'human', edited_fields: edits, skill_type: skillType };
  if (skillType === 'trait') {
    const agentSel = document.getElementById('approve-agent-select');
    if (!agentSel || !agentSel.value) { showToast('请先选择目标智能体'); agentSel.style.display = ''; return; }
    body.target_agent_id = agentSel.value;
  }
  const r = await api(`/teams/${currentTeamId}/skill-extract/${selectedItemId}/approve`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  if (!r) return;
  const typeLabels = { trait: '特质技能', public: '公共技能', reserve: '储备技能' };
  const typeIcons = { trait: '🎯', public: '🌍', reserve: '📦' };
  if (skillType === 'public') {
    const skillId = r.draft_slug;
    if (skillId) {
      const pr = await publishSkillWithGate(skillId, r.draft_name);
      if (pr && !pr.error) {
        addMessage('system', `🌍 技能「${r.draft_name}」已发布为公共技能，所有智能体已获得此技能`);
      }
    }
  }
  showToast(`${typeIcons[skillType]} 已批准为${typeLabels[skillType]}`);
  if (skillType === 'trait') {
    const agents = teamAgents[currentTeamId] || [];
    const agent = agents.find(a => a.agent_id === body.target_agent_id);
    addMessage('system', `🎯 技能「${r.draft_name}」已赋予智能体「${agent?.name || body.target_agent_id}」`);
  } else if (skillType === 'reserve') {
    addMessage('system', `📦 技能「${r.draft_name}」已入库储备，未赋予任何智能体`);
  }
  const idx = queueItems.findIndex(q => q.item_id === selectedItemId);
  if (idx >= 0) Object.assign(queueItems[idx], r);
  await loadSkills();
  renderQueue();

  // ── Closed-loop: suggest best agent for auto-injection ──
  const skillId = r.draft_slug || r.skill_id;
  if (skillId && skillType !== 'trait') {
    // trait already assigned to specific agent; for public/reserve, suggest
    _showInjectionSuggestion(skillId, r.draft_name || edits.name);
  }
};

window.rejectItem = async function() {
  if (!selectedItemId) return;
  const reason = ''; /* B-1: prompt() removed — reason now optional */
  const r = await api(`/teams/${currentTeamId}/skill-extract/${selectedItemId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reviewer: 'human', reason }),
  });
  if (r) { showToast('❌ 已拒绝'); closeDetail(); loadQueue(); }
};

window._quickApprove = async function(itemId, skillType = 'reserve') {
  const body = { reviewer: 'human', skill_type: skillType };
  const r = await api(`/teams/${currentTeamId}/skill-extract/${itemId}/approve`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  const labels = { trait: '特质技能', public: '公共技能', reserve: '储备技能' };
  const icons = { trait: '🎯', public: '🌍', reserve: '📦' };
  if (r) {
    if (skillType === 'public') {
      const skillId = r.draft_slug;
      if (skillId) {
        await publishSkillWithGate(skillId, r.draft_name);
      }
    }
    showToast(`${icons[skillType]} 已批准为${labels[skillType]}`);
    loadQueue(); loadSkills();
  }
};

window._deleteItem = async function(itemId) {
  showConfirm('确认删除此萃取项？', async () => {
    const item = queueItems.find(q => q.item_id === itemId);
    if (item) { shatterSkillNode(item.draft_name || item.skill_id || itemId); }
    const r = await api(`/teams/${currentTeamId}/skill-extract/${itemId}`, { method: 'DELETE' });
    if (r !== null) { showToast('🗑️ 已删除'); loadQueue(); addMessage('system', '🗑️ 萃取项已删除，结晶已碎裂'); }
  });
};

// ── Skills (Taxonomy) ───────────────────────────────────────────
async function loadSkills() {
  if (!currentTeamId) return;
  // Fetch real registered skills from backend
  let registeredSkills = [];
  try {
    registeredSkills = await listApi(`/teams/${currentTeamId}/skills`);
  } catch(e) { /* ignore */ }

  // Build from queue items (both review & approved)
  const seen = new Set();
  const merged = [];
  queueItems.forEach(q => {
    if (q.status !== 'ready_for_review' && q.status !== 'approved') return;
    const slug = q.draft_slug || q.item_id;
    if (seen.has(slug)) return;
    seen.add(slug);
    // If approved, try to enrich with real backend data
    const reg = registeredSkills.find(s => s.slug === slug);
    merged.push({
      skill_id: reg?.skill_id || slug,
      name: q.draft_name || q.source_title || '未命名',
      icon: q.draft_icon || '⚡',
      category: q.draft_category || 'general',
      slug: slug,
      description: q.draft_description || '',
      instructions: q.draft_instructions || '',
      required_tools: q.draft_required_tools || [],
      source: 'distilled',
      lifecycle_stage: q.status === 'approved' ? 'team_local' : 'draft',
      usage_count: reg?.usage_count || 0,
      effectiveness: reg?.effectiveness || 0,
      version: reg?.version || 1,
      _from_queue: true,
      _queue_status: q.status,
      _draft_scope: q.draft_scope || 'personal',
    });
  });
  allSkills = merged;
  renderTaxonomy(); updateSkillCounts(); rebuildSkillNodes();
}

function classifySkill(skill) {
  // Heuristic: classify into atomic / trait / composite
  const tools = skill.required_tools || [];
  const isDefault = skill.is_default;
  const source = skill.source || '';

  if (source === 'distilled') return 'trait';        // Extracted = trait (个人特质)
  if (tools.length >= 3) return 'composite';          // Multi-tool = composite
  if (isDefault && tools.length <= 1) return 'atomic'; // Simple default = atomic
  if (skill.category === 'domain_knowledge') return 'trait';
  if (tools.length >= 2) return 'composite';
  return 'atomic';
}

function renderTaxonomy() {
  const body = document.getElementById('taxonomy-body');
  if (!allSkills.length) {
    body.innerHTML = '<div style="padding:10px;font-size:11px;color:oklch(0.4 0.005 110)">暂无萃取出的技能。请在上方输入知识文本并点击「开始萃取」。</div>';
    return;
  }

  const atomics = [], traits = [], composites = [];
  allSkills.forEach(s => {
    const type = classifySkill(s);
    if (type === 'atomic') atomics.push(s);
    else if (type === 'trait') traits.push(s);
    else composites.push(s);
  });

  const renderCards = (skills, type) => skills.map(s => {
    const statusBadge = s._from_queue
      ? (s._queue_status === 'approved'
        ? '<span style="font-size:9px;padding:1px 4px;background:oklch(0.45 0.12 145/.2);color:oklch(0.65 0.1 145);border-radius:3px;margin-left:4px">✅ 已批准</span>'
        : '<span style="font-size:9px;padding:1px 4px;background:oklch(0.56 0.08 60/.15);color:oklch(0.65 0.06 60);border-radius:3px;margin-left:4px">⏳ 待审核</span>')
      : '';
    const scopeBadge = s._draft_scope === 'public'
      ? '<span style="font-size:9px;padding:1px 4px;background:oklch(0.55 0.12 250/.2);color:oklch(0.7 0.1 250);border-radius:3px;margin-left:4px">🌐</span>'
      : '';
    return `
    <div class="skill-card ${type}" data-skill-id="${s.skill_id}">
      <span class="sc-type">${type === 'atomic' ? '原子' : type === 'trait' ? '特质' : '组合'}</span>
      <div class="sc-icon">${s.icon || '⚡'}</div>
      <div class="sc-name">${s.name}${scopeBadge}${statusBadge}</div>
      <div class="sc-desc">${s.description || ''}</div>
      <div class="sc-source">${s.source || 'distilled'} · ${(s.required_tools || []).length} tools</div>
    </div>
  `}).join('');

  body.innerHTML = renderCards(atomics, 'atomic') + renderCards(traits, 'trait') + renderCards(composites, 'composite');
}

function updateSkillCounts() {
  let a = 0, t = 0, c = 0;
  allSkills.forEach(s => {
    const type = classifySkill(s);
    if (type === 'atomic') a++;
    else if (type === 'trait') t++;
    else c++;
  });
  document.getElementById('count-atomic').textContent = a;
  document.getElementById('count-trait').textContent = t;
  document.getElementById('count-composite').textContent = c;
}

window.toggleTaxonomy = function() {
  const bar = document.getElementById('taxonomy-bar');
  bar.classList.toggle('collapsed');
  document.getElementById('taxonomy-toggle').textContent = bar.classList.contains('collapsed') ? '▲' : '▼';
};

// ── Taxonomy dual-tab: 特质技能 / 公共技能 ────────────────────
let currentTaxonomyTab = 'my';
let publicSkills = [];

window.switchTaxonomyTab = function(btn, tab) {
  currentTaxonomyTab = tab;
  document.querySelectorAll('.taxonomy-tab').forEach(b => {
    b.style.borderBottomColor = 'transparent';
    b.style.color = 'oklch(0.5 0.005 110)';
  });
  btn.style.borderBottomColor = 'var(--koke)';
  btn.style.color = 'var(--shironeri)';

  if (tab === 'my') {
    document.getElementById('taxonomy-body').style.display = '';
    document.getElementById('taxonomy-body-public').style.display = 'none';
  } else {
    document.getElementById('taxonomy-body').style.display = 'none';
    document.getElementById('taxonomy-body-public').style.display = '';
    loadPublicLibrary();
  }
};

async function loadPublicLibrary() {
  // Only show current session queue items marked as public scope
  publicSkills = [];
  const seen = new Set();
  queueItems.forEach(q => {
    if (q.status !== 'ready_for_review' && q.status !== 'approved') return;
    if ((q.draft_scope || 'personal') !== 'public') return;
    const slug = q.draft_slug || q.item_id;
    if (seen.has(slug)) return;
    seen.add(slug);
    publicSkills.push({
      skill_id: slug,
      name: q.draft_name || q.source_title || '未命名',
      icon: q.draft_icon || '⚡',
      category: q.draft_category || 'general',
      description: q.draft_description || '',
      lifecycle_stage: q.status === 'approved' ? 'team_local' : 'draft',
      origin_team_id: currentTeamId,
      _is_own: true,
      _from_queue: true,
      _queue_status: q.status,
    });
  });
  renderPublicLibrary();
}

function renderPublicLibrary() {
  const body = document.getElementById('taxonomy-body-public');
  if (!publicSkills.length) {
    body.innerHTML = '<div style="padding:10px;font-size:11px;color:oklch(0.4 0.005 110)">暂无萃取出的公共技能。萃取时 LLM 会自动推荐公共/私有分类。</div>';
    return;
  }
  body.innerHTML = publicSkills.map(s => {
    const isOwn = s._is_own || s.origin_team_id === currentTeamId;
    const adopted = (s.adopted_by || []).includes(currentTeamId);
    const stageLabels = { draft:'胚胎', team_local:'新生', published:'发布', verified:'已验证', solidified:'固化', degraded:'退化' };
    const stage = stageLabels[s.lifecycle_stage] || s.lifecycle_stage || '';
    return `
      <div class="skill-card" style="border-color:${isOwn ? 'oklch(0.56 0.05 70/.3)' : adopted ? 'oklch(0.55 0.10 250/.3)' : 'oklch(1 0 0/.06)'}">
        <span class="sc-type" style="color:oklch(0.6 0.005 110)">${stage}</span>
        <div class="sc-icon">${s.icon || '⚡'}</div>
        <div class="sc-name">${s.name}</div>
        <div class="sc-desc">${s.description || ''}</div>
        <div class="sc-source" style="display:flex;justify-content:space-between;align-items:center">
          <span>${s.origin_team_id ? '团队 ' + s.origin_team_id.slice(0, 6) : 'builtin'} · 使用 ${s.usage_count || 0}</span>
          ${!isOwn && !adopted ? `<button class="btn btn-sm" onclick="importSkill('${s.skill_id}')" style="font-size:9px;padding:2px 8px">引入</button>` : ''}
          ${adopted ? '<span style="color:var(--koke);font-size:9px">✓ 已引入</span>' : ''}
        </div>
      </div>
    `;
  }).join('');
}

window.importSkill = async function(skillId) {
  const r = await api('/skill-library/import', {
    method: 'POST',
    body: JSON.stringify({ target_team_id: currentTeamId, skill_id: skillId }),
  });
  if (r && !r.error) {
    showToast('✅ 技能已引入');
    addMessage('system', `📦 已引入技能到团队`);
    loadSkills();
    loadPublicLibrary();
  }
};
window._importSkill = window.importSkill;

// ── View Mode Toggle: 🔬萃取 ↔ 🌐全景 ─────────────────────────
let viewMode = 'extract'; // 'extract' | 'panorama'
let panoramaGroup = null;  // Three.js group for panorama elements

window.toggleViewMode = function() {
  viewMode = viewMode === 'extract' ? 'panorama' : 'extract';
  document.getElementById('btn-view-mode').textContent = viewMode === 'extract' ? '🔬' : '🌐';

  if (viewMode === 'panorama') {
    buildPanoramaView();
    // Zoom out to bird's eye
    camera.position.set(0, 45, 8);
    controls.target.set(0, 0, 0);
    controls.maxDistance = 80;
    // Hide main scene elements (fade)
    if (humanFigure) humanFigure.visible = false;
    if (myceliumGroup) myceliumGroup.visible = false;
    extractionGroup.visible = false;
    addMessage('system', '🌐 切换到全景视角 — 鸟瞰所有团队培养皿');
  } else {
    // Cleanup panorama
    if (panoramaGroup) {
      scene.remove(panoramaGroup);
      panoramaGroup.traverse(child => {
        if (child.geometry) child.geometry.dispose();
        if (child.material) {
          if (child.material.map) child.material.map.dispose();
          child.material.dispose();
        }
      });
      panoramaGroup = null;
    }
    // Restore main scene
    if (humanFigure) humanFigure.visible = document.body.classList.contains('mode-router');
    if (myceliumGroup) myceliumGroup.visible = true;
    extractionGroup.visible = true;
    camera.position.set(0, 10, 22);
    controls.target.set(0, 2, 0);
    controls.maxDistance = 40;
    addMessage('system', '🔬 切换到萃取视角 — 聚焦当前团队');
  }
};

async function buildPanoramaView() {
  // Fetch all teams + public library overview
  const teams = await listApi('/teams');
  const overview = await api('/skill-library/overview');
  if (!teams.length) return;

  if (panoramaGroup) {
    scene.remove(panoramaGroup);
    panoramaGroup.traverse(child => {
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
    });
  }
  panoramaGroup = new THREE.Group();

  // Center: public library pool (golden glow)
  const poolGeo = new THREE.CircleGeometry(5, 64);
  const poolMat = new THREE.MeshPhysicalMaterial({
    color: 0xC8B468, roughness: 0.3, metalness: 0.1,
    transmission: 0.6, thickness: 0.5, ior: 1.3,
    emissive: new THREE.Color(0xC8B468), emissiveIntensity: 0.15,
    transparent: true, opacity: 0.4,
  });
  const pool = new THREE.Mesh(poolGeo, poolMat);
  pool.rotation.x = -Math.PI / 2;
  pool.position.y = 0.01;
  panoramaGroup.add(pool);

  // Pool glow light
  const poolLight = new THREE.PointLight(0xC8B468, 0.6, 30);
  poolLight.position.set(0, 2, 0);
  panoramaGroup.add(poolLight);

  // Pool label
  const poolTex = new THREE.CanvasTexture(makeSkillLabel('🌐', '公共技能'));
  poolTex.minFilter = THREE.LinearFilter;
  const poolLabel = new THREE.Sprite(new THREE.SpriteMaterial({ map: poolTex, transparent: true, depthTest: false }));
  poolLabel.position.set(0, 3, 0);
  poolLabel.scale.set(3, 0.75, 1);
  panoramaGroup.add(poolLabel);

  // Public skills in center pool
  const publicSkills = await listApi('/skill-library?visibility=public');
  if (publicSkills.length > 0) {
    publicSkills.forEach((s, i) => {
      const a = (i / publicSkills.length) * Math.PI * 2;
      const r = 1.5 + Math.min(i * 0.3, 3.5);
      const size = 0.15 + Math.min((s.adopted_by?.length || 0) / 5, 0.3);
      const pTorusR = size * 0.85, pTorusTube = size * 0.12;
      const skillMesh = new THREE.Mesh(
        new THREE.TorusGeometry(pTorusR, pTorusTube, 12, 32),
        new THREE.MeshBasicMaterial({
          color: 0xC8B468, transparent: true, opacity: 0.7, side: THREE.DoubleSide,
        })
      );
      skillMesh.position.set(Math.cos(a) * r, size + 0.1, Math.sin(a) * r);
      // Panorama skill glow
      const pGlow = new THREE.Mesh(
        new THREE.TorusGeometry(pTorusR, pTorusTube * 3.5, 12, 32),
        new THREE.MeshBasicMaterial({ color: 0xC8B468, transparent: true, opacity: 0.15, side: THREE.DoubleSide })
      );
      pGlow.position.copy(skillMesh.position);
      panoramaGroup.add(pGlow);
      panoramaGroup.add(skillMesh);
    });
  }

  // Team petri dishes arranged in a circle around center
  const teamRadius = 20;
  teams.forEach((team, idx) => {
    const angle = (idx / teams.length) * Math.PI * 2 - Math.PI / 2;
    const tx = Math.cos(angle) * teamRadius;
    const tz = Math.sin(angle) * teamRadius;
    const isCurrentTeam = team.team_id === currentTeamId;

    // Mini petri dish
    const dishColor = isCurrentTeam ? 0xD4A574 : 0x88AABA;
    const dish = new THREE.Mesh(
      new THREE.CircleGeometry(4, 48),
      new THREE.MeshStandardMaterial({
        color: 0x1A2026, roughness: 0.9, metalness: 0,
        transparent: true, opacity: 0.7,
      })
    );
    dish.rotation.x = -Math.PI / 2;
    dish.position.set(tx, 0.005, tz);
    panoramaGroup.add(dish);

    // Dish rim
    const rim = new THREE.Mesh(
      new THREE.RingGeometry(3.8, 4.2, 48),
      new THREE.MeshBasicMaterial({
        color: dishColor, transparent: true, opacity: isCurrentTeam ? 0.5 : 0.2,
        side: THREE.DoubleSide,
      })
    );
    rim.rotation.x = -Math.PI / 2;
    rim.position.set(tx, 0.01, tz);
    panoramaGroup.add(rim);

    // Team label
    const teamTex = new THREE.CanvasTexture(makeSkillLabel(isCurrentTeam ? '🔬' : '🧫', team.name || team.team_id));
    teamTex.minFilter = THREE.LinearFilter;
    const teamLabel = new THREE.Sprite(new THREE.SpriteMaterial({ map: teamTex, transparent: true, depthTest: false }));
    teamLabel.position.set(tx, 5, tz);
    teamLabel.scale.set(3, 0.75, 1);
    panoramaGroup.add(teamLabel);

    // Team light
    const tLight = new THREE.PointLight(dishColor, isCurrentTeam ? 0.4 : 0.15, 12);
    tLight.position.set(tx, 1.5, tz);
    panoramaGroup.add(tLight);

    // Team's skills as small spheres on their dish
    const teamSkillCount = team.skill_count || team.agent_count || 0;
    const teamOverview = overview?.teams?.find(t => t.team_id === team.team_id);
    const skillCount = teamOverview?.skill_count || teamSkillCount;
    const publicCount = teamOverview?.public_count || 0;
    for (let si = 0; si < Math.min(skillCount, 12); si++) {
      const sa = (si / Math.max(skillCount, 1)) * Math.PI * 2;
      const sr = 1.2 + Math.random() * 2;
      const isPublic = si < publicCount;
      const sColor = isPublic ? 0xC8B468 : (isCurrentTeam ? 0xD4A574 : 0x88AABA);
      const sNode = new THREE.Mesh(
        new THREE.TorusGeometry(0.10, 0.015, 8, 24),
        new THREE.MeshBasicMaterial({
          color: sColor, transparent: true, opacity: isPublic ? 0.8 : 0.5, side: THREE.DoubleSide,
        })
      );
      sNode.position.set(tx + Math.cos(sa) * sr, 0.2, tz + Math.sin(sa) * sr);
      panoramaGroup.add(sNode);
    }

    // Arc lines from team to center pool (for published skills)
    if (publicCount > 0) {
      const arcPts = [];
      const arcSteps = 20;
      for (let i = 0; i <= arcSteps; i++) {
        const t = i / arcSteps;
        arcPts.push(new THREE.Vector3(
          tx * (1 - t),
          2 + Math.sin(t * Math.PI) * 6,
          tz * (1 - t),
        ));
      }
      const arcCurve = new THREE.CatmullRomCurve3(arcPts);
      const arcGeo = new THREE.TubeGeometry(arcCurve, 20, 0.03, 4, false);
      const arcMat = new THREE.MeshBasicMaterial({
        color: 0xC8B468, transparent: true, opacity: 0.08 + publicCount * 0.04,
      });
      panoramaGroup.add(new THREE.Mesh(arcGeo, arcMat));
    }
  });

  scene.add(panoramaGroup);
}

// ── File Drop ───────────────────────────────────────────────────
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error('Failed to load: ' + src));
    document.head.appendChild(s);
  });
}

const fileDrop = document.getElementById('file-drop');
const fileInput = document.getElementById('file-input');
fileDrop.addEventListener('click', () => fileInput.click());
fileDrop.addEventListener('dragover', e => { e.preventDefault(); fileDrop.classList.add('dragover'); });
fileDrop.addEventListener('dragleave', () => fileDrop.classList.remove('dragover'));
fileDrop.addEventListener('drop', e => {
  e.preventDefault(); fileDrop.classList.remove('dragover');
  handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });

async function handleFile(file) {
  if (!file) return;
  const title = file.name.replace(/\.[^.]+$/, '');

  if (file.name.toLowerCase().endsWith('.pdf')) {
    showToast('正在解析 PDF…');
    try {
      if (!window.pdfjsLib) {
        const pdfjsMod = await import('https://cdn.jsdelivr.net/npm/pdfjs-dist@4.4.168/build/pdf.min.mjs');
        window.pdfjsLib = pdfjsMod;
        pdfjsMod.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.4.168/build/pdf.worker.min.mjs';
      }
      const buf = await file.arrayBuffer();
      const pdf = await window.pdfjsLib.getDocument({ data: buf }).promise;
      const pages = [];
      const ocrPages = []; // pages that need OCR
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const tc = await page.getTextContent();
        const text = tc.items.map(it => it.str).join('');
        if (text.trim()) {
          pages.push({ idx: i, text: `--- 第 ${i} 页 ---\n${text}` });
        } else {
          ocrPages.push({ idx: i, page });
        }
      }

      // If some pages have no embedded text, use OCR
      if (ocrPages.length > 0) {
        showToast(`${ocrPages.length} 页为扫描件，正在启动 OCR…`);
        try {
          if (!window.Tesseract) {
            await loadScript('https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js');
          }
          const worker = await window.Tesseract.createWorker('chi_sim+eng', 1, {
            logger: m => {
              if (m.status === 'recognizing text') {
                const pct = Math.round(m.progress * 100);
                showToast(`OCR 识别中… ${pct}%`);
              }
            }
          });

          for (const op of ocrPages) {
            const viewport = op.page.getViewport({ scale: 2.0 });
            const canvas = document.createElement('canvas');
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            const ctx = canvas.getContext('2d');
            await op.page.render({ canvasContext: ctx, viewport }).promise;
            const dataUrl = canvas.toDataURL('image/png');
            const { data } = await worker.recognize(dataUrl);
            if (data.text.trim()) {
              pages.push({ idx: op.idx, text: `--- 第 ${op.idx} 页 (OCR) ---\n${data.text}` });
            }
          }
          await worker.terminate();
        } catch (ocrErr) {
          console.error('OCR error:', ocrErr);
          showToast('OCR 识别失败: ' + ocrErr.message, 'error');
        }
      }

      // Sort by page index and join
      pages.sort((a, b) => a.idx - b.idx);
      const fullText = pages.map(p => p.text).join('\n\n');
      if (!fullText.trim()) { showToast('PDF 未提取到任何文本', 'error'); return; }
      document.getElementById('source-text').value = fullText;
      document.getElementById('source-title').value = title;
      document.getElementById('source-type').value = 'document';
      // Auto-expand knowledge input section
      document.getElementById('knowledge-input-section').classList.remove('collapsed');
      const ocrNote = ocrPages.length > 0 ? `（含 ${ocrPages.length} 页 OCR）` : '';
      showToast(`已解析 PDF: ${pdf.numPages} 页${ocrNote}`);
    } catch (e) {
      console.error('PDF parse error:', e);
      showToast('PDF 解析失败: ' + e.message, 'error');
    }
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    document.getElementById('source-text').value = reader.result;
    document.getElementById('source-title').value = title;
    document.getElementById('knowledge-input-section').classList.remove('collapsed');
    showToast(`已加载: ${file.name}`);
  };
  reader.readAsText(file);
}

// ── Toast ───────────────────────────────────────────────────────
function showToast(msg, severity) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('toast-error', 'toast-info');
  if (severity === 'error') t.classList.add('toast-error');
  else if (severity === 'info') t.classList.add('toast-info');
  t.classList.add('show');
  clearTimeout(t._tm);
  t._tm = setTimeout(() => t.classList.remove('show'), 3000);
}

// B-1: 通用确认弹层（替代 confirm）— 复用 toast 容器
function showConfirm(msg, onOk) {
  var existing = document.getElementById('confirm-overlay');
  if (existing) existing.remove();
  var overlay = document.createElement('div');
  overlay.id = 'confirm-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:10000;display:flex;align-items:center;justify-content:center';
  overlay.onclick = function(e) { if (e.target === overlay) overlay.remove(); };
  overlay.innerHTML = '<div style="background:var(--bg,oklch(0.16 0.005 110));border:1px solid oklch(0.25 0.005 110);border-radius:8px;padding:16px;max-width:360px;width:90%;color:oklch(0.75 0.005 110);font-size:13px;text-align:center">' +
    '<div style="margin-bottom:12px">' + msg + '</div>' +
    '<div style="display:flex;gap:8px;justify-content:center">' +
    '<button id="confirm-cancel" style="padding:6px 16px;background:oklch(0.25 0.005 110);border:none;border-radius:4px;color:oklch(0.6 0.005 110);cursor:pointer">取消</button>' +
    '<button id="confirm-ok" style="padding:6px 16px;background:oklch(0.5 0.1 250);border:none;border-radius:4px;color:#fff;cursor:pointer;font-weight:600">确认</button></div></div>';
  document.body.appendChild(overlay);
  document.getElementById('confirm-cancel').onclick = function() { overlay.remove(); };
  document.getElementById('confirm-ok').onclick = function() { overlay.remove(); onOk(); };
  document.getElementById('confirm-ok').focus();
}

// B-2: 页内输入弹层（替代 prompt）
function openInputModal(label, onOk, placeholder) {
  var existing = document.getElementById('confirm-overlay');
  if (existing) existing.remove();
  var overlay = document.createElement('div');
  overlay.id = 'confirm-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:10000;display:flex;align-items:center;justify-content:center';
  overlay.onclick = function(e) { if (e.target === overlay) overlay.remove(); };
  overlay.innerHTML = '<div style="background:var(--bg,oklch(0.16 0.005 110));border:1px solid oklch(0.25 0.005 110);border-radius:8px;padding:16px;max-width:360px;width:90%;color:oklch(0.75 0.005 110);font-size:13px">' +
    '<div style="margin-bottom:8px">' + label + '</div>' +
    '<textarea id="input-modal-text" rows="3" placeholder="' + (placeholder || '') + '" style="width:100%;padding:6px 8px;font-size:12px;background:oklch(0.12 0.005 110);border:1px solid oklch(0.3 0.005 110);border-radius:4px;color:oklch(0.75 0.005 110);box-sizing:border-box;margin-bottom:10px"></textarea>' +
    '<div id="input-modal-hint" style="font-size:11px;color:#ef4444;margin-bottom:8px;display:none"></div>' +
    '<div style="display:flex;gap:8px;justify-content:flex-end">' +
    '<button id="confirm-cancel" style="padding:6px 16px;background:oklch(0.25 0.005 110);border:none;border-radius:4px;color:oklch(0.6 0.005 110);cursor:pointer">取消</button>' +
    '<button id="confirm-ok" style="padding:6px 16px;background:oklch(0.5 0.1 250);border:none;border-radius:4px;color:#fff;cursor:pointer;font-weight:600">确认</button></div></div>';
  document.body.appendChild(overlay);
  document.getElementById('confirm-cancel').onclick = function() { overlay.remove(); };
  document.getElementById('confirm-ok').onclick = function() {
    var val = document.getElementById('input-modal-text').value.trim();
    overlay.remove();
    onOk(val);
  };
  setTimeout(function() { document.getElementById('input-modal-text').focus(); }, 100);
}

// ── Message Flow ────────────────────────────────────────────────
function addMessage(type, content, itemId) {
  const log = document.getElementById('msg-log');
  const div = document.createElement('div');
  div.className = `msg ${type}`;
  const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

  if (type === 'skill-card' && itemId) {
    div.innerHTML = `
      <div class="sc-inline-name">${content}</div>
      <div class="sc-inline-actions">
        <button class="btn-inline-approve" onclick="window._quickApprove('${itemId}','reserve');this.closest('.msg').style.opacity='0.5'">📦 储备</button>
        <button class="btn-inline-approve" onclick="window._quickApprove('${itemId}','public');this.closest('.msg').style.opacity='0.5'" style="border-color:oklch(0.55 0.10 250/.3);color:oklch(0.7 0.08 250)">🌍 公共</button>
        <button onclick="window._openDetail('${itemId}')">✏️ 编辑</button>
        <button class="btn-inline-reject" onclick="window._inlineReject('${itemId}');this.closest('.msg').style.opacity='0.5'">❌ 拒绝</button>
      </div>
      <div class="msg-time">${now}</div>`;
  } else {
    div.innerHTML = `<div>${content}</div><div class="msg-time">${now}</div>`;
  }
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

window._inlineReject = async function(itemId) {
  const reason = ''; /* B-1: prompt() removed — reason now optional */
  const r = await api(`/teams/${currentTeamId}/skill-extract/${itemId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reviewer: 'human', reason }),
  });
  if (r) { showToast('❌ 已拒绝'); loadQueue(); }
};

// ── Knowledge Input Toggle ──────────────────────────────────────
window.toggleKnowledgeInput = function() {
  document.getElementById('knowledge-input-section').classList.toggle('collapsed');
};

// ── STAR 引导萃取 ──────────────────────────────────────────────
const STAR_STEPS = [
  { key: 'S', label: '场景', prompt: '请描述当时的<b>场景/背景</b>：你在什么环境下？面对什么情况？', placeholder: '例：在季度复盘会上，团队发现客户流失率突然上升了15%…' },
  { key: 'T', label: '任务', prompt: '你当时的<b>任务/目标</b>是什么？需要达成什么结果？', placeholder: '例：需要在一周内找出流失原因并提出改进方案…' },
  { key: 'A', label: '行动', prompt: '你具体采取了哪些<b>行动/步骤</b>？用了什么方法或工具？', placeholder: '例：我先分析了近3个月的用户行为数据，然后设计了一份…' },
  { key: 'R', label: '结果', prompt: '最终取得了什么<b>结果/成效</b>？有什么经验教训？', placeholder: '例：流失率在两个月内降低了8%，团队沉淀了一套…' },
];

// STAR modal step definitions (richer than chat prompts)
const STAR_MODAL_STEPS = [
  {
    key: 'S', label: '场景 Situation',
    question: '请描述一个与上述文档相关的真实场景',
    hint: '回忆你亲历过的一次具体事件 — 当时是什么环境？团队处于什么阶段？面临什么压力或约束条件？越具体越好，时间、地点、角色都可以写。',
    placeholder: '例：2025年Q3末，我们的生产环境在凌晨3点发生了一次配置变更导致的P0事故。当时值班的运维工程师在AWS控制台手动修改了安全组规则…',
    context_prefix: '基于你在 Six-Pager 中描述的背景，',
  },
  {
    key: 'T', label: '任务 Task',
    question: '在那个场景中，你的具体任务是什么？',
    hint: '明确你需要达成的目标或解决的问题。这个任务是谁交给你的？有什么时间限制？成功的标准是什么？',
    placeholder: '例：事故复盘后，CTO要求我在两周内建立一套配置变更标准流程，确保同类事故不再发生。目标是将配置变更事故率降低80%…',
    context_prefix: '结合你刚才描述的场景，',
  },
  {
    key: 'A', label: '行动 Action',
    question: '你具体采取了哪些行动？',
    hint: '详细描述你的操作步骤、使用的工具和方法。这是萃取技能的核心 — 你做了什么"别人可以复用"的事情？分步骤写最佳。',
    placeholder: '例：\n1. 首先梳理了过去6个月所有配置变更记录，识别出高风险操作类型\n2. 引入了 Terraform 作为 IaC 工具，将所有配置代码化\n3. 设计了灰度发布流程：10%→25%→50%→100%\n4. 为每个变更编写自动回滚脚本…',
    context_prefix: '针对上述任务，',
  },
  {
    key: 'R', label: '结果 Result',
    question: '最终取得了什么结果？',
    hint: '用数据说话 — 量化成效。同时总结经验教训：哪些做法值得推广？哪些踩坑需要避免？这些会成为技能的"验证依据"。',
    placeholder: '例：实施3个月后，配置变更引发的事故从每月2.3次降至0.1次，降幅96%。MTTR从45分钟缩短至3分钟。团队沉淀了一套标准操作手册，新成员入职即可使用…',
    context_prefix: '经过上述行动，',
  },
];

let starActive = false;
let starStep = 0;
let starData = {};
let _starModalStep = 0;
let _starModalAnswers = {};

window.startStarGuide = function() {
  if (starActive) { cancelStarGuide(); return; }
  // Open Six-Pager modal
  document.getElementById('sixpager-overlay').classList.add('open');
};

window.closeSixPager = function() {
  document.getElementById('sixpager-overlay').classList.remove('open');
};

window.submitSixPager = function() {
  const purpose = document.getElementById('sp-purpose').value.trim();
  const pain    = document.getElementById('sp-pain').value.trim();
  const tenets  = document.getElementById('sp-tenets').value.trim();
  const sop     = document.getElementById('sp-sop').value.trim();
  const faq     = document.getElementById('sp-faq').value.trim();
  const risk    = document.getElementById('sp-risk').value.trim();

  if (!purpose && !pain && !sop) {
    showToast('请至少填写目的、痛点和SOP流程', 'warn');
    return;
  }

  // Compose Six-Pager narrative
  let composed = `【Six-Pager 叙述文档】\n\n`;
  if (purpose) composed += `## 1. 目的 Purpose\n${purpose}\n\n`;
  if (pain)    composed += `## 2. 业务现状与痛点\n${pain}\n\n`;
  if (tenets)  composed += `## 3. 核心原则 Tenets\n${tenets}\n\n`;
  if (sop)     composed += `## 4. 提议的 SOP 标准流程\n${sop}\n\n`;
  if (faq)     composed += `## 5. 内部 FAQ\n${faq}\n\n`;
  if (risk)    composed += `## 6. 风险预判\n${risk}\n\n`;

  // Close Six-Pager modal
  closeSixPager();

  // Open STAR step modal
  starActive = true;
  starData = { _sixPager: composed, _sixPagerTitle: purpose.slice(0, 40) };
  _starModalStep = 0;
  _starModalAnswers = {};
  _renderStarModal();
  document.getElementById('star-modal-overlay').classList.add('open');
  addMessage('system', '📄 <b>Six-Pager 叙述文档</b>已收集 — 现在通过 STAR 四步引导补充真实经验案例。');
};

// ── STAR Modal Navigation ───────────────────────────────────────
function _renderStarModal() {
  const step = STAR_MODAL_STEPS[_starModalStep];
  const total = STAR_MODAL_STEPS.length;

  // Progress
  document.querySelectorAll('.smp-step').forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i < _starModalStep) el.classList.add('done');
    else if (i === _starModalStep) el.classList.add('active');
  });

  // Context from Six-Pager
  const ctxEl = document.getElementById('star-modal-context');
  if (starData._sixPagerTitle) {
    ctxEl.innerHTML = `${step.context_prefix}请回忆一个与「<b>${escHtml(starData._sixPagerTitle)}</b>」相关的真实经验案例。`;
    ctxEl.style.display = '';
  } else {
    ctxEl.style.display = 'none';
  }

  // Question & hint
  document.getElementById('star-modal-question').textContent = `${step.key}. ${step.question}`;
  document.getElementById('star-modal-hint').textContent = step.hint;
  document.getElementById('star-modal-example').innerHTML = `<span style="color:oklch(0.5 0.04 70);cursor:pointer;text-decoration:underline" onclick="fillStarExample()">💡 点击使用示例填充</span> ${step.placeholder}`;

  // Input — pre-fill with saved answer if user navigated back
  const input = document.getElementById('star-modal-input');
  input.value = _starModalAnswers[step.key] || '';
  input.placeholder = '请在此输入您的经验描述…';
  setTimeout(() => input.focus(), 100);

  // Buttons
  document.getElementById('star-modal-prev').style.display = _starModalStep === 0 ? 'none' : '';
  const nextBtn = document.getElementById('star-modal-next');
  if (_starModalStep === total - 1) {
    nextBtn.textContent = '⚗️ 完成并萃取';
  } else {
    nextBtn.textContent = '下一步 →';
  }

  // Step hint
  document.getElementById('star-modal-step-hint').textContent = `第 ${_starModalStep + 1} 步 / 共 ${total} 步`;
}

// Fill example text into STAR textarea
window.fillStarExample = function() {
  const step = STAR_MODAL_STEPS[_starModalStep];
  const input = document.getElementById('star-modal-input');
  if (!input.value.trim()) {
    input.value = step.placeholder.replace(/^例[：:]?\s*/, '');
    showToast('💡 示例已填入，请根据实际情况修改');
  } else {
    showConfirm('当前已有内容，是否用示例替换？', () => {
      input.value = step.placeholder.replace(/^例[：:]?\s*/, '');
    });
  }
  input.focus();
};

window.starModalNext = function() {
  const step = STAR_MODAL_STEPS[_starModalStep];
  const val = document.getElementById('star-modal-input').value.trim();
  if (!val) {
    showToast(`请填写「${step.label}」`, 'warn');
    return;
  }
  _starModalAnswers[step.key] = val;

  if (_starModalStep >= STAR_MODAL_STEPS.length - 1) {
    // All done — extract
    document.getElementById('star-modal-overlay').classList.remove('open');
    _finishStarModal();
  } else {
    _starModalStep++;
    _renderStarModal();
  }
};

window.starModalPrev = function() {
  if (_starModalStep <= 0) return;
  // Save current input
  const step = STAR_MODAL_STEPS[_starModalStep];
  _starModalAnswers[step.key] = document.getElementById('star-modal-input').value.trim();
  _starModalStep--;
  _renderStarModal();
};

window.closeStarModal = function() {
  document.getElementById('star-modal-overlay').classList.remove('open');
  starActive = false;
  starData = {};
  _starModalStep = 0;
  _starModalAnswers = {};
  addMessage('system', '⭐ STAR 引导已退出');
};

function _finishStarModal() {
  let composed = '';

  // Include Six-Pager
  if (starData._sixPager) {
    composed += starData._sixPager + '\n---\n\n【STAR 经验案例】\n\n';
  }

  composed += `【场景 Situation】\n${_starModalAnswers.S}\n\n【任务 Task】\n${_starModalAnswers.T}\n\n【行动 Action】\n${_starModalAnswers.A}\n\n【结果 Result】\n${_starModalAnswers.R}`;

  addMessage('system', '⭐ STAR 四步收集完成，正在组合知识文本并启动萃取…');

  // Fill source text and trigger extraction
  document.getElementById('source-text').value = composed;
  document.getElementById('source-title').value = starData._sixPager ? 'Six-Pager + STAR萃取' : 'STAR引导萃取';
  startExtraction();

  // Reset
  starActive = false;
  starStep = 0;
  starData = {};
  _starModalStep = 0;
  _starModalAnswers = {};
}

// ── Legacy chat-based STAR (kept for /star command without Six-Pager) ──
window.cancelStarGuide = function() {
  starActive = false;
  starStep = 0;
  starData = {};
  document.getElementById('panel-left').classList.remove('star-guide-active');
  document.getElementById('star-guide-bar').classList.remove('visible');
  const chatInput = document.getElementById('chat-input');
  chatInput.placeholder = '输入知识文本或指令（/extract, /evolve, /share）…\nEnter 发送 · Shift+Enter 换行 · >200字自动萃取';
  addMessage('system', '⭐ STAR 引导已退出');
};

function updateStarUI() {
  const steps = document.querySelectorAll('.star-step');
  steps.forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i < starStep) el.classList.add('done');
    else if (i === starStep) el.classList.add('active');
  });
  if (starActive && starStep < STAR_STEPS.length) {
    const s = STAR_STEPS[starStep];
    document.getElementById('chat-input').placeholder = s.placeholder;
  }
}

function showStarPrompt() {
  const s = STAR_STEPS[starStep];
  addMessage('system', `<b>[${s.key}] ${s.label}</b> — ${s.prompt}`);
}

function handleStarInput(text) {
  const s = STAR_STEPS[starStep];
  starData[s.key] = text;
  addMessage('user', text);
  starStep++;
  updateStarUI();

  if (starStep >= STAR_STEPS.length) {
    // All steps done — compose and extract
    finishStarGuide();
  } else {
    showStarPrompt();
  }
}

function finishStarGuide() {
  let composed = '';

  // Include Six-Pager if present
  if (starData._sixPager) {
    composed += starData._sixPager + '\n---\n\n【STAR 经验案例】\n\n';
  }

  composed += `【场景 Situation】\n${starData.S}\n\n【任务 Task】\n${starData.T}\n\n【行动 Action】\n${starData.A}\n\n【结果 Result】\n${starData.R}`;

  addMessage('system', '⭐ STAR 四步收集完成，正在组合知识文本并启动萃取…');

  // Reset STAR state
  starActive = false;
  document.getElementById('panel-left').classList.remove('star-guide-active');
  document.getElementById('star-guide-bar').classList.remove('visible');
  document.getElementById('chat-input').placeholder = '输入知识文本或指令（/extract, /evolve, /share）…\nEnter 发送 · Shift+Enter 换行 · >200字自动萃取';

  // Fill source text and trigger extraction
  document.getElementById('source-text').value = composed;
  document.getElementById('source-title').value = starData._sixPager ? 'Six-Pager + STAR萃取' : 'STAR引导萃取';
  startExtraction();

  // Reset data
  starStep = 0;
  starData = {};
}

// ── Chat Input — Enter发送, Shift+Enter换行, >200字自动萃取 ────
const chatInput = document.getElementById('chat-input');
const cmdMenu = document.getElementById('cmd-menu');
const SLASH_COMMANDS = [
  { cmd: '/extract',  icon: '🩸', desc: '萃取知识文本中的技能',           usage: '/extract <知识文本>' },
  { cmd: '/star',     icon: '⭐', desc: 'STAR引导式萃取（场景→任务→行动→结果）', usage: '/star' },
  { cmd: '/evolve',   icon: '🧬', desc: '进化已有技能（即将上线）',        usage: '/evolve <技能名>' },
  { cmd: '/share',    icon: '🌐', desc: '分享技能到公共库（即将上线）',     usage: '/share <技能名>' },
  { cmd: '/merge',    icon: '🔀', desc: '合并相似技能（即将上线）',        usage: '/merge <技能A> <技能B>' },
  { cmd: '/list',     icon: '📋', desc: '列出当前团队所有技能',           usage: '/list' },
  { cmd: '/help',     icon: '❓', desc: '显示帮助信息',                  usage: '/help' },
];
let cmdActiveIdx = -1;

function renderCmdMenu(filter) {
  const items = SLASH_COMMANDS.filter(c => c.cmd.startsWith(filter));
  if (!items.length) { cmdMenu.classList.remove('open'); return; }
  cmdMenu.innerHTML = items.map((c, i) =>
    `<div class="cmd-item${i === cmdActiveIdx ? ' active' : ''}" data-cmd="${c.cmd}" onclick="selectCmd('${c.cmd}')">
      <div class="cmd-icon">${c.icon}</div>
      <div class="cmd-body">
        <div class="cmd-name"><span>${c.cmd}</span> — ${c.desc}</div>
        <div class="cmd-desc">${c.usage}</div>
      </div>
    </div>`
  ).join('');
  cmdMenu.classList.add('open');
}

window.selectCmd = function(cmd) {
  chatInput.value = cmd + ' ';
  chatInput.focus();
  cmdMenu.classList.remove('open');
  cmdActiveIdx = -1;
};

chatInput.addEventListener('keydown', (e) => {
  // Command menu navigation
  if (cmdMenu.classList.contains('open')) {
    const items = cmdMenu.querySelectorAll('.cmd-item');
    if (e.key === 'ArrowDown') { e.preventDefault(); cmdActiveIdx = Math.min(cmdActiveIdx + 1, items.length - 1); items.forEach((el, i) => el.classList.toggle('active', i === cmdActiveIdx)); return; }
    if (e.key === 'ArrowUp')   { e.preventDefault(); cmdActiveIdx = Math.max(cmdActiveIdx - 1, 0); items.forEach((el, i) => el.classList.toggle('active', i === cmdActiveIdx)); return; }
    if (e.key === 'Tab' || (e.key === 'Enter' && cmdActiveIdx >= 0)) {
      e.preventDefault();
      const sel = items[Math.max(cmdActiveIdx, 0)];
      if (sel) selectCmd(sel.dataset.cmd);
      return;
    }
    if (e.key === 'Escape') { cmdMenu.classList.remove('open'); cmdActiveIdx = -1; return; }
  }
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleChatSend();
  }
});
// Auto-resize + slash command menu
chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 80) + 'px';
  // Slash command detection
  const val = chatInput.value;
  if (val.startsWith('/') && !val.includes('\n') && val.indexOf(' ') === -1) {
    cmdActiveIdx = 0;
    renderCmdMenu(val.toLowerCase());
  } else {
    cmdMenu.classList.remove('open');
    cmdActiveIdx = -1;
  }
});

window.handleChatSend = async function() {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = '';
  chatInput.style.height = 'auto';
  cmdMenu.classList.remove('open');
  cmdActiveIdx = -1;

  // STAR guide mode — intercept input
  if (starActive) {
    handleStarInput(text);
    return;
  }

  // Commands
  if (text.startsWith('/')) {
    const cmd = text.split(' ')[0].toLowerCase();
    if (cmd === '/extract') {
      addMessage('user', text);
      const body = text.slice('/extract'.length).trim();
      if (body) {
        document.getElementById('source-text').value = body;
        startExtraction();
      } else {
        addMessage('system', '请在 /extract 后输入知识文本，或展开「知识投入」区粘贴');
      }
      return;
    }
    if (cmd === '/star') {
      addMessage('user', text);
      startStarGuide();
      return;
    }
    if (cmd === '/evolve' || cmd === '/share' || cmd === '/merge') {
      addMessage('user', text);
      addMessage('system', `⏳ ${cmd} 功能即将上线（Phase 4/5）`);
      return;
    }
    if (cmd === '/list') {
      addMessage('user', text);
      if (!currentTeamId) { addMessage('system', '请先选择一个团队'); return; }
      const skills = allSkills || [];
      if (!skills.length) { addMessage('system', '当前团队暂无技能'); return; }
      const lines = skills.map((s, i) => `${i + 1}. <b>${escHtml(s.draft_name || s.name || s.slug)}</b> — ${(s._draft_scope || s.visibility || s.draft_scope) === 'public' ? '🌐公共' : '🔒私有'} · ${s.status || s.lifecycle_stage || '—'}`);
      addMessage('system', `📋 当前团队 ${currentTeamId} 共 ${skills.length} 个技能:<br>${lines.join('<br>')}`);
      return;
    }
    if (cmd === '/help') {
      addMessage('user', text);
      const helpLines = SLASH_COMMANDS.map(c => `${c.icon} <b>${c.cmd}</b> — ${c.desc}`);
      addMessage('system', `📖 可用指令:\n${helpLines.join('\n')}\n\n💡 输入 / 显示指令菜单，↑↓ 导航，Tab 选择`);
      return;
    }
  }

  addMessage('user', text);

  // >200字 → 自动萃取
  if (text.length > 200) {
    if (!currentTeamId) { addMessage('system', '请先选择一个团队'); return; }
    addMessage('system', `📥 收到知识文本 (${(text.length / 1024).toFixed(1)}KB)，自动触发萃取…`);
    document.getElementById('source-text').value = text;
    startExtraction();
  } else {
    addMessage('system', '💡 输入>200字的知识文本可自动触发萃取，或使用 /extract 命令');
  }
};

// ── Keyboard shortcuts ──────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  // Don't capture when typing in inputs
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
  if (e.key === 'a' || e.key === 'A') {
    // Quick approve focused/selected item
    if (selectedItemId) { window._quickApprove(selectedItemId, 'reserve'); }
  }
  if (e.key === 'r' || e.key === 'R') {
    if (selectedItemId) { window.rejectItem(); }
  }
  if (e.key === 'Escape') {
    if (document.getElementById('modal-detail').classList.contains('open')) { closeDetail(); }
  }
});

// ═══════════════════════════════════════════════════════════════════
// PIPELINE STATE MACHINE — 四阶段萃取管线
// ═══════════════════════════════════════════════════════════════════

const PIPELINE_API = '/api/v1/extraction';
const STAGE_LABELS = { draft: '日志采集', review: '上下文补全', approval: '情境验证', published: '技能发布' };
const STAGE_ORDER = ['draft', 'review', 'approval', 'published'];

// Per-item pipeline mapping (item_id → pipeline_id)
let itemPipelineMap = {};
// Current pipeline data cache
let currentPipeline = null;
// Context supplement local cache per item
let ctxSupplementCache = {};
// Context mode: 'realtime' or 'retro'
let ctxMode = 'realtime';

// ── Pipeline Stepper (right panel) update ───────────────────────
function updatePipelineStepper(stage) {
  const steps = document.querySelectorAll('#pipeline-stepper .pipe-step');
  const stageIdx = STAGE_ORDER.indexOf(stage || 'draft');
  steps.forEach((el, i) => {
    el.classList.remove('active', 'done', 'locked');
    if (i < stageIdx) el.classList.add('done');
    else if (i === stageIdx) el.classList.add('active');
    else el.classList.add('locked');
    const gate = el.querySelector('.pipe-gate');
    if (gate) gate.textContent = i <= stageIdx ? '' : '🔒';
  });
}

// ── Create or get pipeline for an item ──────────────────────────
async function ensurePipeline(itemId) {
  if (itemPipelineMap[itemId]) {
    return itemPipelineMap[itemId];
  }
  // Try to find existing pipeline by tag
  const list = await api2(`${PIPELINE_API}/pipelines?team_id=${currentTeamId}`);
  const pipelines = list && list.pipelines ? list.pipelines : (Array.isArray(list) ? list : []);
  if (pipelines.length) {
    const found = pipelines.find(p => (p.tags || []).includes(`item:${itemId}`));
    if (found) {
      itemPipelineMap[itemId] = found.pipeline_id;
      return found.pipeline_id;
    }
  }
  // Create new pipeline
  const item = queueItems.find(q => q.item_id === itemId);
  const result = await api2(`${PIPELINE_API}/pipelines`, {
    method: 'POST',
    body: JSON.stringify({
      name: item ? (item.draft_name || item.source_title || itemId) : itemId,
      description: `萃取管线 — ${itemId}`,
      team_id: currentTeamId,
      created_by: 'human',
      tags: [`item:${itemId}`],
    }),
  });
  if (result && result.pipeline_id) {
    itemPipelineMap[itemId] = result.pipeline_id;
    return result.pipeline_id;
  }
  return null;
}

// helper for extraction pipeline API (different base)
async function api2(url, options = {}) {
  try {
    var method = (options.method || 'GET').toUpperCase();
    var headers = { 'Content-Type': 'application/json', ...options.headers };
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
      await _ensureCsrf_sk();
      if (_csrfToken_sk) headers['x-csrf-token'] = _csrfToken_sk;
    }
    const resp = await fetch(url, {
      headers: headers,
      ...options,
    });
    const data = await resp.json();
    if (!resp.ok) {
      // Return error detail so callers can handle it
      return { _error: true, status: resp.status, ...(data.detail || data) };
    }
    return data;
  } catch (e) {
    console.warn('api2 error:', e);
    return null;
  }
}

// ── Load pipeline data for an item ──────────────────────────────
async function loadItemPipeline(itemId) {
  const pipelineId = await ensurePipeline(itemId);
  if (!pipelineId) {
    currentPipeline = null;
    updatePipelineStepper('draft');
    return;
  }
  const data = await api2(`${PIPELINE_API}/pipelines/${pipelineId}`);
  if (data) {
    currentPipeline = data;
    updatePipelineStepper(data.current_stage);
    updateModalPipelineStepper(data.current_stage);
    updateReviewGateUI(data);
    // Load context supplement from payload
    const ctx = data.payload?.context_supplement || {};
    document.getElementById('ctx-pressure-type').value = ctx.pressure_type || '';
    document.getElementById('ctx-business-goal').value = ctx.business_goal || '';
    document.getElementById('ctx-branch-reason').value = ctx.branch_reason || '';
    document.getElementById('ctx-scene-tags').value = (ctx.scene_tags || []).join(', ');
    document.getElementById('ctx-decision-notes').value = ctx.decision_notes || '';
    setCtxMode(ctx.record_mode || 'realtime');
  } else {
    currentPipeline = null;
    updatePipelineStepper('draft');
  }
}

// ── Pipeline Tab ────────────────────────────────────────────────
async function loadPipelineTab() {
  if (!selectedItemId || !currentPipeline) {
    // Try loading
    if (selectedItemId) await loadItemPipeline(selectedItemId);
    if (!currentPipeline) return;
  }
  const p = currentPipeline;
  updateModalPipelineStepper(p.current_stage);

  // Gate requirements
  const gate = p.gate_requirements || {};
  const currentGate = gate[p.current_stage] || gate.review || {};
  document.getElementById('pipe-min-reviewers').textContent = currentGate.min_reviewers ?? 1;
  document.getElementById('pipe-min-approvals').textContent = currentGate.min_approvals ?? 1;
  document.getElementById('pipe-forbid-self').textContent = currentGate.forbid_self_review ? '❌' : '✅';
  document.getElementById('pipe-cross-team').textContent = currentGate.require_cross_team ? '✅' : '—';
  document.getElementById('pipe-current-stage').textContent = STAGE_LABELS[p.current_stage] || p.current_stage;

  // Enable advance button (always enabled except published)
  const advBtn = document.getElementById('btn-advance-pipe');
  advBtn.disabled = p.current_stage === 'published';

  // Update reviewer/approval counts
  const reviews = p.reviews?.[p.current_stage] || [];
  const approvals = reviews.filter(r => r.decision === 'approve');
  const reqReviewers = currentGate.min_reviewers ?? 1;
  const reqApprovals = currentGate.min_approvals ?? 1;
  const progress = Math.min(100, Math.round((approvals.length / reqApprovals) * 100));
  _eachGateEl('gate-reviewer-count', el => el.textContent = `${reviews.length}/${reqReviewers} 复核`);
  _eachGateEl('gate-approval-count', el => el.textContent = `${approvals.length}/${reqApprovals} 同意`);
  _eachGateEl('gate-progress-fill', el => el.style.width = progress + '%');
  _eachGateEl('gate-status-badge', el => el.textContent = approvals.length >= reqApprovals ? '🔓 可推进' : '🔒 未确认');

  // Render reviewer list (两套门禁 UI 都写)
  if (reviews.length > 0) {
    const reviewsHtml = reviews.map(r => `<div style="display:flex;align-items:center;gap:6px;padding:3px 0;font-size:10px;border-bottom:1px solid oklch(1 0 0/.04)">
      <span>${r.decision === 'approve' ? '✅' : '❌'}</span>
      <span style="color:oklch(0.7 0.005 110)">${escHtml(r.reviewer_name || 'anonymous')}</span>
      <span style="color:oklch(0.4 0.005 110);font-family:var(--font-mono)">${r.identity || 'peer'}</span>
      ${r.comment ? `<span style="color:oklch(0.5 0.005 110);margin-left:auto;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(r.comment)}</span>` : ''}
    </div>`).join('');
    _eachGateEl('reviewer-list', el => el.innerHTML = reviewsHtml);
  }

  // Update SkillClaw phase indicators
  const clawMap = { draft: 'evidence', review: 'attribution', approval: 'evolution', published: 'distribution' };
  const activeClawPhase = clawMap[p.current_stage] || 'evidence';
  const clawOrder = ['evidence', 'attribution', 'evolution', 'distribution'];
  const clawIdx = clawOrder.indexOf(activeClawPhase);
  document.querySelectorAll('.skillclaw-phase').forEach(el => {
    const phase = el.dataset.clawPhase;
    const idx = clawOrder.indexOf(phase);
    el.classList.remove('active-claw', 'done-claw');
    if (idx < clawIdx) el.classList.add('done-claw');
    else if (idx === clawIdx) el.classList.add('active-claw');
  });

  // Todos
  renderPipelineTodos(p.todos || []);

  // Events
  const evtData = await api2(`${PIPELINE_API}/pipelines/${p.pipeline_id}/events`);
  renderPipelineEvents(evtData?.events || []);
}

function updateModalPipelineStepper(stage) {
  const steps = document.querySelectorAll('[data-modal-stage]');
  const stageIdx = STAGE_ORDER.indexOf(stage || 'draft');
  steps.forEach(el => {
    const idx = STAGE_ORDER.indexOf(el.dataset.modalStage);
    el.classList.remove('active', 'done', 'locked');
    if (idx < stageIdx) el.classList.add('done');
    else if (idx === stageIdx) el.classList.add('active');
    else el.classList.add('locked');
  });
}

function renderPipelineTodos(todos) {
  const el = document.getElementById('pipe-todos');
  if (!todos.length) { el.innerHTML = '<div style="text-align:center;padding:8px;font-size:10px;color:oklch(0.4 0.005 110)">暂无待办</div>'; return; }
  el.innerHTML = todos.map(t => {
    const statusIcon = t.status === 'completed' ? '<span style="color:#8CBEB2">◉</span>' : t.status === 'in_progress' ? '<span style="color:#6BB5D9">◎</span>' : '<span style="color:#4A535C">○</span>';
    const stageLabel = STAGE_LABELS[t.stage] || t.stage;
    return `<div style="display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid oklch(1 0 0/.04)">
      <span style="cursor:pointer" onclick="togglePipelineTodo('${t.todo_id}')">${statusIcon}</span>
      <span style="flex:1;color:oklch(0.75 0.005 110);font-size:11px;${t.status === 'completed' ? 'text-decoration:line-through;opacity:0.5' : ''}">${escHtml(t.title)}</span>
      <span style="font-size:9px;color:oklch(0.4 0.005 110);font-family:var(--font-mono)">${stageLabel}</span>
    </div>`;
  }).join('');
}

function renderPipelineEvents(events) {
  const el = document.getElementById('pipe-event-list');
  if (!events.length) { el.innerHTML = '<div style="font-size:10px;color:oklch(0.4 0.005 110);text-align:center">暂无事件记录</div>'; return; }
  el.innerHTML = events.map(evt => {
    const type = evt.transition_type || evt.type || 'create';
    const dotClass = type === 'advance' ? 'advance' : type === 'reject' ? 'reject' : type === 'review' ? 'review' : 'create';
    const icon = type === 'advance' ? '⏭' : type === 'reject' ? '↩️' : type === 'review' ? '👁️' : '📝';
    const fromLabel = STAGE_LABELS[evt.from_stage] || evt.from_stage || '—';
    const toLabel = STAGE_LABELS[evt.to_stage] || evt.to_stage || '—';
    const time = evt.occurred_at ? new Date(evt.occurred_at).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '';
    return `<div class="evt-item">
      <div class="evt-dot ${dotClass}">${icon}</div>
      <div class="evt-body">
        <div class="evt-title">${fromLabel} → ${toLabel}</div>
        <div class="evt-meta">${time} · ${evt.triggered_by || 'system'}</div>
        ${evt.metadata?.comment ? `<div class="evt-comment">${escHtml(evt.metadata.comment)}</div>` : ''}
      </div>
    </div>`;
  }).join('');
}

// ── Context Supplement ──────────────────────────────────────────
window.toggleCtxSupplement = function() {
  document.getElementById('ctx-supplement').classList.toggle('collapsed');
  const arrow = document.getElementById('ctx-collapse-arrow');
  arrow.textContent = document.getElementById('ctx-supplement').classList.contains('collapsed') ? '▶' : '▼';
};

window.setCtxMode = function(mode) {
  ctxMode = mode;
  document.getElementById('ctx-btn-realtime').style.opacity = mode === 'realtime' ? '1' : '0.5';
  document.getElementById('ctx-btn-retro').style.opacity = mode === 'retro' ? '1' : '0.5';
  document.getElementById('ctx-mode-label').className = `ctx-record-label ${mode === 'realtime' ? 'realtime' : 'retro'}`;
  document.getElementById('ctx-mode-label').textContent = mode === 'realtime' ? '实时记录' : '回顾注释';
  document.getElementById('ctx-decision-notes').placeholder = mode === 'realtime'
    ? '记录当时的决策上下文：为什么这样做？考虑了哪些替代方案？'
    : '事后回顾注释：回头看这个决策，有什么需要补充的？';
};

window.saveCtxSupplement = async function() {
  if (!selectedItemId || !currentPipeline) { showToast('请先打开一个萃取项目'); return; }
  const ctx = {
    pressure_type: document.getElementById('ctx-pressure-type').value,
    business_goal: document.getElementById('ctx-business-goal').value,
    branch_reason: document.getElementById('ctx-branch-reason').value,
    scene_tags: document.getElementById('ctx-scene-tags').value.split(',').map(s => s.trim()).filter(Boolean),
    decision_notes: document.getElementById('ctx-decision-notes').value,
    record_mode: ctxMode,
    updated_at: new Date().toISOString(),
  };
  const result = await api2(`${PIPELINE_API}/pipelines/${currentPipeline.pipeline_id}`, {
    method: 'PATCH',
    body: JSON.stringify({ payload: { ...currentPipeline.payload, context_supplement: ctx } }),
  });
  if (result) {
    currentPipeline.payload = { ...currentPipeline.payload, context_supplement: ctx };
    showToast('💾 上下文已保存');
  } else {
    showToast('保存失败', 'error');
  }
};

// ── Cross-Review Gate ───────────────────────────────────────────
function updateReviewGateUI(pipeline) {
  if (!pipeline) return;
  const reviewers = pipeline.reviewers || [];
  const gate = pipeline.gate_requirements || {};
  const currentGate = gate[pipeline.current_stage] || gate.review || {};
  const minReviewers = currentGate.min_reviewers ?? 2;
  const minApprovals = currentGate.min_approvals ?? 1;

  const approvals = reviewers.filter(r => r.action === 'approve').length;
  const rejections = reviewers.filter(r => r.action === 'reject').length;
  const totalReviewers = reviewers.length;

  // Gate badge (两套门禁 UI 都写)
  const passed = totalReviewers >= minReviewers && approvals >= minApprovals;
  _eachGateEl('gate-status-badge', badge => {
    badge.className = `gate-badge ${passed ? 'unlocked' : 'locked'}`;
    badge.textContent = passed ? '🔓 已解锁' : '🔒 未解锁';
  });

  // Progress
  _eachGateEl('gate-reviewer-count', el => el.textContent = `${totalReviewers}/${minReviewers} 复核`);
  _eachGateEl('gate-approval-count', el => el.textContent = `${approvals}/${minApprovals} 同意`);
  const progressPct = Math.min(100, (totalReviewers / minReviewers) * 100);
  _eachGateEl('gate-progress-fill', fillEl => {
    fillEl.style.width = progressPct + '%';
    fillEl.style.background = passed ? 'oklch(0.52 0.04 160)' : 'oklch(0.55 0.1 250)';
  });

  // Reviewer list (两套都写)
  let listHtml;
  if (!reviewers.length) {
    listHtml = '<div style="font-size:10px;color:oklch(0.4 0.005 110);text-align:center;padding:8px">尚无复核记录</div>';
  } else {
    listHtml = reviewers.map(r => {
      const actionClass = r.action === 'approve' ? 'approved' : r.action === 'reject' ? 'rejected' : '';
      const actionIcon = r.action === 'approve' ? '✅' : r.action === 'reject' ? '❌' : '💬';
      return `<div class="reviewer-row">
        <div class="rv-avatar">${r.reviewer_name ? r.reviewer_name[0] : '👤'}</div>
        <span class="rv-name">${escHtml(r.reviewer_name || r.reviewer_id)}</span>
        <span class="rv-role">${r.identity || 'peer'}</span>
        <span class="rv-action ${actionClass}">${actionIcon} ${r.action}</span>
      </div>`;
    }).join('');
  }
  _eachGateEl('reviewer-list', el => el.innerHTML = listHtml);
}

// 门禁有两套同义 UI(编辑页 id 无后缀 / 管线"快速确认"页 id 带 '-pipe'),
// 显示类更新两套都写;表单按 scope('' | 'pipe') 读写各自元素,避免重复 id 串扰。
function _eachGateEl(idBase, fn) {
  ['', '-pipe'].forEach(function(sfx) {
    const el = document.getElementById(idBase + sfx);
    if (el) fn(el);
  });
}
function _reviewSuffix(scope) { return scope === 'pipe' ? '-pipe' : ''; }

window.toggleReviewForm = function(scope) {
  const sfx = _reviewSuffix(scope);
  const form = document.getElementById('review-inline-form' + sfx);
  const btn = document.getElementById('btn-show-review-form' + sfx);
  if (!form || !btn) return;
  if (form.style.display === 'none') {
    form.style.display = 'block';
    btn.style.display = 'none';
    document.getElementById('review-name' + sfx)?.focus();
  } else {
    form.style.display = 'none';
    btn.style.display = '';
  }
};

window.submitReviewAction = async function(action, scope) {
  if (!selectedItemId || !currentPipeline) { showToast('请先打开萃取项目'); return; }
  const sfx = _reviewSuffix(scope);
  const nameEl = document.getElementById('review-name' + sfx);
  const reviewerName = (nameEl?.value || '').trim();
  if (!reviewerName) { showToast('请填写你的名字'); nameEl?.focus(); return; }
  const identity = document.getElementById('review-identity' + sfx)?.value || 'peer';
  const comment = (document.getElementById('review-comment' + sfx)?.value || '').trim();

  const result = await api2(`${PIPELINE_API}/pipelines/${currentPipeline.pipeline_id}/reviewers`, {
    method: 'POST',
    body: JSON.stringify({
      reviewer_id: reviewerName.toLowerCase().replace(/\s+/g, '_'),
      reviewer_name: reviewerName,
      identity,
      team_id: currentTeamId,
      action,
      comment,
    }),
  });
  if (result && !result._error) {
    showToast(`👁️ 复核已提交: ${action === 'approve' ? '同意' : '拒绝'}`);
    // Reset form (当前 scope)
    if (nameEl) nameEl.value = '';
    const cEl = document.getElementById('review-comment' + sfx); if (cEl) cEl.value = '';
    const fEl = document.getElementById('review-inline-form' + sfx); if (fEl) fEl.style.display = 'none';
    const bEl = document.getElementById('btn-show-review-form' + sfx); if (bEl) bEl.style.display = '';
    await loadItemPipeline(selectedItemId);
  } else if (result && result._error) {
    showToast(`❌ 复核失败: ${result.detail || result.reason || '未知错误'}`, 'error');
  }
};

// ── Pipeline Advance ────────────────────────────────────────────
window.advancePipeline = async function() {
  if (!currentPipeline) return;
  const result = await api2(`${PIPELINE_API}/pipelines/${currentPipeline.pipeline_id}/advance`, {
    method: 'POST',
    body: JSON.stringify({ triggered_by: 'human' }),
  });
  if (result && result._error) {
    const gr = result.gate_result || result;
    showToast(`🔒 门禁未通过: ${result.reason || gr.reason || result.error}`, 'error');
    // Show gate check result
    const gateEl = document.getElementById('pipe-gate-result');
    gateEl.style.display = 'block';
    gateEl.style.borderColor = 'oklch(0.5 0.08 18/.3)';
    gateEl.style.color = 'oklch(0.65 0.08 18)';
    gateEl.innerHTML = `🔒 <b>门禁未通过</b><br>${gr.reason || ''}<br>
      ${gr.missing_identities?.length ? '缺少身份: ' + gr.missing_identities.join(', ') : ''}
      <br>当前复核: ${gr.current_reviewers ?? 0}/${gr.required_reviewers ?? 2}
      · 同意: ${gr.current_approvals ?? 0}/${gr.required_approvals ?? 1}`;
  } else if (result) {
    const newStage = result.transition?.to_stage || result.current_stage;
    showToast(`⏭ 已推进到: ${STAGE_LABELS[newStage] || newStage}`);
    await loadItemPipeline(selectedItemId);
    loadPipelineTab();
    addMessage('system', `🔄 管线已推进到「${STAGE_LABELS[newStage] || newStage}」阶段`);
  }
};

// ── Check Gate ──────────────────────────────────────────────────
window.checkGate = async function() {
  if (!currentPipeline) return;
  const result = await api2(`${PIPELINE_API}/pipelines/${currentPipeline.pipeline_id}/check-gate`, { method: 'POST' });
  const gateEl = document.getElementById('pipe-gate-result');
  gateEl.style.display = 'block';
  if (result && result.passed) {
    gateEl.style.borderColor = 'oklch(0.52 0.04 160/.3)';
    gateEl.style.color = 'oklch(0.65 0.06 155)';
    gateEl.innerHTML = `🔓 <b>门禁已通过</b> — 可以推进到下一阶段`;
  } else {
    gateEl.style.borderColor = 'oklch(0.5 0.08 18/.3)';
    gateEl.style.color = 'oklch(0.65 0.08 18)';
    gateEl.innerHTML = `🔒 <b>门禁未通过</b><br>${result?.reason || '条件不满足'}`;
  }
};

// ── Pipeline Todos ──────────────────────────────────────────────
window.addPipelineTodo = async function() {
  if (!currentPipeline) return;
  const title = await new Promise(resolve => openInputModal('待办标题', resolve, '输入标题...')); if (!title) return;
  const result = await api2(`${PIPELINE_API}/pipelines/${currentPipeline.pipeline_id}/todos`, {
    method: 'POST',
    body: JSON.stringify({
      title,
      stage: currentPipeline.current_stage,
      assignee_name: 'human',
    }),
  });
  if (result) {
    showToast('📋 待办已添加');
    loadPipelineTab();
  }
};

window.togglePipelineTodo = async function(todoId) {
  if (!currentPipeline) return;
  const todo = (currentPipeline.todos || []).find(t => t.todo_id === todoId);
  if (!todo) return;
  const newStatus = todo.status === 'completed' ? 'pending' : 'completed';
  if (newStatus === 'completed') {
    await api2(`${PIPELINE_API}/pipelines/${currentPipeline.pipeline_id}/todos/${todoId}/resolve`, { method: 'POST' });
  } else {
    await api2(`${PIPELINE_API}/pipelines/${currentPipeline.pipeline_id}/todos/${todoId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus }),
    });
  }
  await loadItemPipeline(selectedItemId);
  loadPipelineTab();
};

// ── Update pipeline stepper when queue item selected ────────────
function updateStepperForItem(item) {
  if (!item) { updatePipelineStepper('draft'); return; }
  // Map item status to pipeline stage
  const statusStageMap = {
    'pending': 'draft',
    'llm_prefilling': 'draft',
    'ready_for_review': 'review',
    'approved': 'published',
    'rejected': 'draft',
    'error': 'draft',
  };
  const stage = statusStageMap[item.status] || 'draft';
  updatePipelineStepper(stage);
}

// ═══════════════════════════════════════════════════════════════════
// THREE.JS SCENE — 萃取数字孪生
// ═══════════════════════════════════════════════════════════════════

function initScene() {
  const canvas = document.getElementById('three-canvas');
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
  renderer.setClearColor(0x1A2026);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = false;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.85;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1A2026);
  scene.fog = new THREE.FogExp2(0x1A2026, 0.016);

  camera = new THREE.PerspectiveCamera(45, 1, 0.1, 200);
  camera.position.set(0, 10, 22);

  controls = new OrbitControls(camera, document.getElementById('viewport'));
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.minDistance = 8;
  controls.maxDistance = 40;
  controls.maxPolarAngle = Math.PI / 2.1;
  controls.target.set(0, 2, 0);

  clock = new THREE.Clock();

  // Lighting
  scene.add(new THREE.AmbientLight(0x2A2828, 0.18));
  const mainLight = new THREE.DirectionalLight(0x554840, 0.45);
  mainLight.position.set(5, 25, 8);
  scene.add(mainLight);
  scene.add(new THREE.HemisphereLight(0x2A2828, 0x181614, 0.08));

  // Ground — hexagonal platform
  buildPlatform();

  // Human figure (center) — used in router/赋予 mode as selected agent
  humanFigure = createAgentFigure('智能体', 0xD4A574);
  humanFigure.visible = false; // Hidden in extraction mode by default
  scene.add(humanFigure);

  // Extraction group (vessels + nerves + skill nodes)
  extractionGroup = new THREE.Group();
  scene.add(extractionGroup);

  // Ambient particles (dust motes)
  buildAmbientDust();

  // Build initial vessel/nerve scaffold (dormant)
  buildVesselNerveScaffold();

  onResize();
  animate();
}

// ── Platform — 培养皿基质 ────────────────────────────────────────
function buildPlatform() {
  // 基质层
  const substrate = new THREE.Mesh(
    new THREE.CircleGeometry(25, 48),
    new THREE.MeshStandardMaterial({ color: 0x1A2026, roughness: 0.96, metalness: 0, transparent: true, opacity: 0.85 })
  );
  substrate.rotation.x = -Math.PI / 2;
  scene.add(substrate);

  // 培养皿边缘
  const rim = new THREE.Mesh(
    new THREE.TorusGeometry(25, 0.15, 6, 48),
    new THREE.MeshBasicMaterial({ color: 0x1E1A16, transparent: true, opacity: 0.6 })
  );
  rim.rotation.x = -Math.PI / 2; rim.position.y = 0.08;
  scene.add(rim);

  // 同心纹理
  [5, 10, 15, 20].forEach(r => {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(r - 0.02, r + 0.02, 48),
      new THREE.MeshBasicMaterial({ color: 0x221E18, transparent: true, opacity: 0.08 })
    );
    ring.rotation.x = -Math.PI / 2; ring.position.y = 0.002;
    scene.add(ring);
  });
}

// ── 智能体形象 (Digital Twin) ────────────────────────────────────
function createAgentFigure(name, hexColor, isChairman = false) {
  const group = new THREE.Group();
  const col = new THREE.Color(hexColor);
  const scale = isChairman ? 1.3 : 1.0;
  group.userData.labelColor = `#${col.getHexString()}`;
  group.userData.bubbleOffsetY = (isChairman ? 3.15 : 2.9) * scale;

  const outlineMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.7, side: THREE.DoubleSide });
  const glowMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.28, side: THREE.DoubleSide });

  // Head ring
  const headR = 0.34 * scale, headTube = 0.035 * scale;
  const head = new THREE.Mesh(new THREE.TorusGeometry(headR, headTube, 12, 32), outlineMat);
  head.position.y = 2.0 * scale;
  group.add(head);
  group.userData.head = head;

  // Head glow
  const headGlow = new THREE.Mesh(new THREE.TorusGeometry(headR, headTube * 4, 12, 32), glowMat);
  headGlow.position.copy(head.position);
  group.add(headGlow);

  // Body U-arc
  const pts = [];
  for (let i = 0; i <= 32; i++) {
    const t = i / 32, a = Math.PI * t;
    pts.push(new THREE.Vector3(-Math.cos(a) * 0.48 * scale, (1.25 - Math.sin(a) * 0.65) * scale, 0));
  }
  const curve = new THREE.CatmullRomCurve3(pts);
  group.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 32, 0.035 * scale, 8, false), outlineMat));
  group.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 32, 0.12 * scale, 8, false), glowMat));

  // Light
  const pLight = new THREE.PointLight(col, isChairman ? 0.95 : 0.55, isChairman ? 8 : 5.5);
  pLight.position.y = 1.4 * scale;
  group.add(pLight);

  // Ground ring
  const glowRing = new THREE.Mesh(
    new THREE.RingGeometry(0.35 * scale, 0.55 * scale, 32),
    new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.22, side: THREE.DoubleSide })
  );
  glowRing.rotation.x = -Math.PI / 2; glowRing.position.y = 0.01;
  group.add(glowRing);
  group.userData.glowRing = glowRing;

  // Name
  const tex = new THREE.CanvasTexture(makeLabel(name));
  tex.minFilter = THREE.LinearFilter;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  sprite.position.y = (isChairman ? 3.12 : 2.84) * scale;
  sprite.scale.set(2.7, 0.72, 1);
  group.add(sprite);

  group.position.set(0, 0, 0);
  return group;
}

function makeLabel(text) {
  const c = document.createElement('canvas');
  c.width = 384; c.height = 96;
  const ctx = c.getContext('2d');
  ctx.clearRect(0, 0, 384, 96);
  ctx.font = '700 30px "Noto Sans SC", sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#D4A574';
  ctx.fillText(text, 192, 48);
  return c;
}

// ── 菌丝网络 — 递归分枝，半透明玻璃质感 ────────────────────────
function buildVesselNerveScaffold() {
  myceliumGroup = new THREE.Group();
  scene.add(myceliumGroup);

  function growHypha(origin, direction, length, thickness, depth, maxDepth) {
    if (depth > maxDepth || length < 0.25) return;
    const pts = [origin.clone()];
    const steps = Math.max(Math.floor(length * 5), 3);
    const current = origin.clone();
    const dir = direction.clone().normalize();
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      const wobble = Math.sin(t * 7 + depth * 2.5) * 0.08 * (1 + depth * 0.3);
      const perpX = -dir.z, perpZ = dir.x;
      current.add(dir.clone().multiplyScalar(length / steps));
      current.x += perpX * wobble;
      current.z += perpZ * wobble;
      current.y = origin.y + Math.sin(t * Math.PI) * 0.06 * length;
      pts.push(current.clone());
    }
    const curve = new THREE.CatmullRomCurve3(pts);
    const depthRatio = 1 - depth / maxDepth;
    const mat = new THREE.MeshBasicMaterial({
      color: myceliumColor,
      transparent: true, opacity: 0.06 + depthRatio * 0.18,
      side: THREE.DoubleSide
    });
    myceliumGroup.add(new THREE.Mesh(
      new THREE.TubeGeometry(curve, Math.max(steps * 2, 4), thickness, 3, false), mat
    ));
    const endPt = pts[pts.length - 1];
    const branches = depth < 2 ? 2 : 1;
    for (let b = 0; b < branches; b++) {
      const spread = (b / branches) * Math.PI * 1.4 - Math.PI * 0.7;
      const newDir = new THREE.Vector3(
        dir.x * Math.cos(spread) - dir.z * Math.sin(spread), 0,
        dir.x * Math.sin(spread) + dir.z * Math.cos(spread)
      ).normalize();
      newDir.x += (Math.random() - 0.5) * 0.35;
      newDir.z += (Math.random() - 0.5) * 0.35;
      newDir.normalize();
      growHypha(endPt, newDir, length * (0.5 + Math.random() * 0.28), thickness * 0.6, depth + 1, maxDepth);
    }
  }

  [0, 1.57, 3.14, 4.71].forEach(angle => {
    growHypha(new THREE.Vector3(0, 0.06, 0), new THREE.Vector3(Math.cos(angle), 0, Math.sin(angle)),
      3.0 + Math.random() * 1.2, 0.035 + Math.random() * 0.012, 0, 4);
  });

  // 萃取粒子系统 — 螺旋吸收 → 再分配
  buildExtractionParticles();
}

// ── 萃取粒子 — 螺旋向内吸收、再分配到技能节点 ──────────────────
function buildExtractionParticles() {
  const positions = new Float32Array(EXTRACT_PARTICLE_COUNT * 3);
  const colors = new Float32Array(EXTRACT_PARTICLE_COUNT * 3);
  extractParticleData = [];

  const typeColors = [
    new THREE.Color(0xB898C8), // atomic
    new THREE.Color(0xC8B468), // trait
    new THREE.Color(0x88AABA), // composite
  ];

  for (let i = 0; i < EXTRACT_PARTICLE_COUNT; i++) {
    const angle = Math.random() * Math.PI * 2;
    const r = 2 + Math.random() * 14;
    positions[i * 3] = Math.cos(angle) * r;
    positions[i * 3 + 1] = 0.05 + Math.random() * 0.3;
    positions[i * 3 + 2] = Math.sin(angle) * r;

    const colorIdx = i % 3;
    const c = typeColors[colorIdx].clone().lerp(myceliumColor, 0.3);
    colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;

    extractParticleData.push({
      phase: Math.random(),
      speed: 0.001 + Math.random() * 0.002,
      angle,
      startR: r,
      targetAngle: [0, 1.05, 2.1, 3.14, 4.19, 5.24][Math.floor(Math.random() * 6)],
      targetR: 6 + Math.random() * 6
    });
  }

  extractParticleGeo = new THREE.BufferGeometry();
  extractParticleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  extractParticleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const mat = new THREE.PointsMaterial({
    size: 0.14, vertexColors: true, transparent: true, opacity: 0.0,
    blending: THREE.AdditiveBlending, depthWrite: false
  });
  const points = new THREE.Points(extractParticleGeo, mat);
  points.userData.mat = mat;
  scene.add(points);
}

// ── Extraction VFX triggers ─────────────────────────────────────
// Incremental mycelium: store endpoint positions for branching
let myceliumEndpoints = [];
let extractionStage = 0; // 0=idle, 1=inject, 2=grow, 3=cluster, 4=crystallize, 5=review
let extractionTimer = null;
let pendingCrystalSkill = null; // skill to crystallize after animation

function collectMyceliumEndpoints() {
  // Walk mycelium tubes to find tip positions for future branching
  if (!myceliumGroup) return;
  myceliumEndpoints = [];
  myceliumGroup.children.forEach(mesh => {
    if (mesh.geometry && mesh.geometry.parameters?.path) {
      const pts = mesh.geometry.parameters.path.getPoints(4);
      if (pts.length > 0) {
        myceliumEndpoints.push(pts[pts.length - 1].clone());
      }
    }
  });
  // Fallback: sample from existing children positions
  if (myceliumEndpoints.length === 0) {
    myceliumGroup.children.forEach((mesh, i) => {
      if (i % 8 === 0 && mesh.geometry) {
        const pos = mesh.geometry.boundingSphere?.center;
        if (pos) myceliumEndpoints.push(pos.clone());
      }
    });
  }
  // Ensure at least 6 fallback points
  if (myceliumEndpoints.length < 6) {
    for (let a = 0; a < 6; a++) {
      const angle = a * Math.PI / 3;
      myceliumEndpoints.push(new THREE.Vector3(Math.cos(angle) * 6, 0.06, Math.sin(angle) * 6));
    }
  }
}

// Grow new mycelium branches from random existing endpoint
function growIncrementalMycelium(targetPos) {
  if (myceliumEndpoints.length === 0) collectMyceliumEndpoints();
  // Pick closest endpoint to target (or random if no target)
  let origin;
  if (targetPos) {
    origin = myceliumEndpoints.reduce((closest, ep) =>
      ep.distanceTo(targetPos) < closest.distanceTo(targetPos) ? ep : closest
    , myceliumEndpoints[0]);
  } else {
    origin = myceliumEndpoints[Math.floor(Math.random() * myceliumEndpoints.length)];
  }

  const direction = targetPos
    ? new THREE.Vector3().subVectors(targetPos, origin).normalize()
    : new THREE.Vector3(Math.random() - 0.5, 0, Math.random() - 0.5).normalize();
  const length = 1.5 + Math.random() * 2;

  // Grow a short branch with 2-3 sub-branches
  const pts = [origin.clone()];
  const steps = Math.max(Math.floor(length * 5), 4);
  const current = origin.clone();
  const dir = direction.clone();
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const wobble = Math.sin(t * 7) * 0.06;
    current.add(dir.clone().multiplyScalar(length / steps));
    current.x += (-dir.z) * wobble;
    current.z += dir.x * wobble;
    current.y = origin.y + Math.sin(t * Math.PI) * 0.04;
    pts.push(current.clone());
  }
  const curve = new THREE.CatmullRomCurve3(pts);
  const mat = new THREE.MeshBasicMaterial({
    color: myceliumColor,
    transparent: true, opacity: 0.0, // Start invisible, animate in
    side: THREE.DoubleSide
  });
  const tube = new THREE.Mesh(
    new THREE.TubeGeometry(curve, Math.max(steps * 2, 4), 0.015 + Math.random() * 0.01, 3, false), mat
  );
  tube.userData._targetOpacity = 0.18;
  tube.userData._growing = true;
  tube.userData._growStart = clock.getElapsedTime();
  myceliumGroup.add(tube);

  // Record new endpoint
  const newEnd = pts[pts.length - 1].clone();
  myceliumEndpoints.push(newEnd);

  // Sub-branches
  for (let b = 0; b < 2; b++) {
    const subDir = new THREE.Vector3(
      dir.x + (Math.random() - 0.5) * 0.8,
      0,
      dir.z + (Math.random() - 0.5) * 0.8
    ).normalize();
    const subLen = length * 0.4;
    const subPts = [newEnd.clone()];
    const subCur = newEnd.clone();
    const subSteps = 4;
    for (let i = 1; i <= subSteps; i++) {
      subCur.add(subDir.clone().multiplyScalar(subLen / subSteps));
      subCur.y = newEnd.y + Math.sin(i / subSteps * Math.PI) * 0.02;
      subPts.push(subCur.clone());
    }
    const subCurve = new THREE.CatmullRomCurve3(subPts);
    const subMat = mat.clone();
    subMat.opacity = 0.0;
    const subTube = new THREE.Mesh(
      new THREE.TubeGeometry(subCurve, 8, 0.008, 4, false), subMat
    );
    subTube.userData._targetOpacity = 0.12;
    subTube.userData._growing = true;
    subTube.userData._growStart = clock.getElapsedTime() + 0.5; // Delayed
    myceliumGroup.add(subTube);
    myceliumEndpoints.push(subPts[subPts.length - 1].clone());
  }
}

// ── Multi-step extraction animation sequence ────────────────────
function triggerExtractionVFX() {
  if (extractionActive) return;
  extractionActive = true;
  extractionStage = 1;

  // Show progress indicator
  document.getElementById('extract-progress').classList.add('visible');
  document.getElementById('ep-fill').style.width = '10%';
  document.getElementById('ep-text').textContent = '📥 培养基注入中…';

  // Stage 1: 培养基注入（0-2s）— particles spiral inward, mycelium brightens
  if (myceliumGroup) {
    myceliumGroup.children.forEach(mesh => {
      if (mesh.material) {
        mesh.userData._origOpacity = mesh.material.opacity;
        mesh.material.opacity = Math.min(mesh.material.opacity * 2, 0.35);
      }
    });
  }
  scene.children.forEach(child => {
    if (child.isPoints && child.userData.mat) child.userData.mat.opacity = 0.85;
  });
  if (humanFigure?.userData?.glowRing) {
    humanFigure.userData.glowRing.material.opacity = 0.4;
  }

  // Stage 2: 菌丝生长（2s delay）— grow new incremental branches
  extractionTimer = setTimeout(() => {
    if (!extractionActive) return;
    extractionStage = 2;
    document.getElementById('ep-fill').style.width = '25%';
    document.getElementById('ep-text').textContent = '🧬 菌丝正在生长…';

    // Grow 2-3 new branches from existing endpoints
    collectMyceliumEndpoints();
    for (let i = 0; i < 2 + Math.floor(Math.random() * 2); i++) {
      growIncrementalMycelium(null);
    }

    // Brighten mycelium more
    if (myceliumGroup) {
      myceliumGroup.children.forEach(mesh => {
        if (mesh.material) mesh.material.opacity = Math.min(mesh.material.opacity * 1.5, 0.5);
      });
    }
  }, 2000);

  // Stage 3: 知识簇聚集（4s delay）— particles cluster at tips
  setTimeout(() => {
    if (!extractionActive) return;
    extractionStage = 3;
    document.getElementById('ep-fill').style.width = '45%';
    document.getElementById('ep-text').textContent = '⚗️ 知识簇正在聚集…';
  }, 4000);

  // Safety timeout: auto-stop if stuck for 60s
  setTimeout(() => {
    if (extractionActive) {
      console.warn('[VFX] Extraction VFX safety timeout — forcing stop');
      stopExtractionVFX();
    }
  }, 60000);
}

function onExtractionItemCreated() {
  // Called when SSE item_created arrives — enter stage 3→4
  if (extractionActive) {
    extractionStage = 4;
    document.getElementById('ep-fill').style.width = '60%';
    document.getElementById('ep-text').textContent = '🔬 正在结晶化…';
  }
}

function stopExtractionVFX() {
  extractionActive = false;
  extractionStage = 0;
  if (extractionTimer) { clearTimeout(extractionTimer); extractionTimer = null; }

  document.getElementById('ep-fill').style.width = '100%';
  document.getElementById('ep-text').textContent = '萃取完成';
  setTimeout(() => {
    document.getElementById('extract-progress').classList.remove('visible');
    document.getElementById('ep-fill').style.width = '0%';
    document.getElementById('ep-text').textContent = '正在萃取…';
  }, 2000);

  // Restore mycelium opacity
  if (myceliumGroup) {
    myceliumGroup.children.forEach(mesh => {
      if (mesh.material) mesh.material.opacity = mesh.userData._origOpacity || mesh.material.opacity * 0.33;
    });
  }

  // Fade extraction particles
  scene.children.forEach(child => {
    if (child.isPoints && child.userData.mat) child.userData.mat.opacity = 0.25;
  });

  if (humanFigure?.userData?.glowRing) humanFigure.userData.glowRing.material.opacity = 0.15;
}

// ── Crystal spawn with growth animation ─────────────────────────
function spawnSkillNodeAnimated(skill) {
  // Grow new mycelium branch toward the skill's position first
  const type = classifySkill(skill);
  const angle = Math.random() * Math.PI * 2;
  const v = getLifecycleVisuals(skill);
  const x = Math.cos(angle) * v.orbR;
  const z = Math.sin(angle) * v.orbR;
  const targetPos = new THREE.Vector3(x, v.sphereR, z);

  // Grow mycelium toward the crystal position
  growIncrementalMycelium(targetPos);

  // Spawn torus ring (agent-head style) with scale-up animation
  const col = new THREE.Color(v.color);
  const torusR = v.sphereR * 0.85;
  const torusTube = v.sphereR * 0.12;
  const outlineMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0, side: THREE.DoubleSide });
  const glowMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(new THREE.TorusGeometry(torusR, torusTube, 12, 32), outlineMat);
  mesh.position.set(x, v.sphereR, z);
  mesh.scale.set(0.01, 0.01, 0.01); // Start tiny
  mesh.rotation.x = -Math.PI / 2; // Start flat (lying down)
  // Glow halo ring
  const glowRing = new THREE.Mesh(new THREE.TorusGeometry(torusR, torusTube * 3.5, 12, 32), glowMat);
  glowRing.position.copy(mesh.position);
  glowRing.rotation.x = -Math.PI / 2; // Start flat too
  extractionGroup.add(glowRing);
  mesh.userData = {
    skill, type,
    spawnTime: clock.getElapsedTime(),
    lifecycle: v,
    blink: v.blink,
    degraded: v.degraded || false,
    _animating: true,  // Growth animation flag
    _targetOpacity: v.opacity,
    _glowTargetOpacity: v.opacity * 0.25,
    _targetScale: 1,
    _glowBrighten: true, // Glow brightens gradually after growth
    _glowRing: glowRing,
  };
  extractionGroup.add(mesh);
  skillNodes.push(mesh);

  // Ground glow
  const glow = new THREE.Mesh(
    new THREE.CircleGeometry(0.8, 32),
    new THREE.MeshBasicMaterial({ color: v.color, transparent: true, opacity: 0.04, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  glow.rotation.x = -Math.PI / 2;
  glow.position.set(x, 0.003, z);
  extractionGroup.add(glow);

  // Point light
  const cLight = new THREE.PointLight(v.color, v.lightIntensity, 4);
  cLight.position.set(x, 0.5, z);
  extractionGroup.add(cLight);

  // Halo ring for published
  if (v.halo) {
    const haloMat = new THREE.MeshBasicMaterial({ color: v.color, transparent: true, opacity: 0.12, side: THREE.DoubleSide });
    const haloMesh = new THREE.Mesh(new THREE.RingGeometry(v.sphereR * 1.3, v.sphereR * 1.8, 32), haloMat);
    haloMesh.rotation.x = -Math.PI / 2;
    haloMesh.position.set(x, v.sphereR * 0.5, z);
    extractionGroup.add(haloMesh);
  }

  // Public scope ring — cyan orbital ring
  if (v.isPublic) {
    const scopeMat = new THREE.MeshBasicMaterial({ color: 0x48C9B0, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    const scopeRing = new THREE.Mesh(new THREE.TorusGeometry(v.sphereR * 1.6, 0.018, 8, 48), scopeMat);
    scopeRing.position.set(x, v.sphereR, z);
    scopeRing.rotation.x = Math.PI / 5;
    scopeRing.userData._scopeRing = true;
    extractionGroup.add(scopeRing);
  }

  // Verify ring
  if (v.verifyRing) {
    const vRingMat = new THREE.MeshBasicMaterial({ color: 0x4CAF50, transparent: true, opacity: 0.35, side: THREE.DoubleSide });
    const vRing = new THREE.Mesh(new THREE.TorusGeometry(v.sphereR * 1.2, 0.02, 8, 32), vRingMat);
    vRing.position.set(x, v.sphereR, z);
    vRing.rotation.x = Math.PI / 3;
    vRing.userData.isVerifyRing = true;
    extractionGroup.add(vRing);
  }

  // Degraded: red warning ring (flickers in animate loop)
  if (v.degraded) {
    const warnMat = new THREE.MeshBasicMaterial({ color: 0xFF4444, transparent: true, opacity: 0.25, side: THREE.DoubleSide });
    const warnRing = new THREE.Mesh(new THREE.TorusGeometry(v.sphereR * 1.4, 0.012, 8, 32), warnMat);
    warnRing.position.set(x, v.sphereR, z);
    warnRing.rotation.x = Math.PI / 4;
    warnRing.userData._degradedRing = true;
    warnRing.userData._parentNode = mesh;
    extractionGroup.add(warnRing);
  }

  // Label sprite
  const labelCanvas = makeSkillLabel(skill.icon || '⚡', skill.name || '');
  const tex = new THREE.CanvasTexture(labelCanvas);
  tex.minFilter = THREE.LinearFilter;
  const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  label.position.set(x, v.sphereR * 2 + 0.6, z);
  const scaleX = 2 * (labelCanvas.width / 256);
  label.scale.set(scaleX, 0.5, 1);
  extractionGroup.add(label);
  mesh.userData._label = label;
}

// ── Delete shatter animation ────────────────────────────────────
function shatterSkillNode(skillId) {
  const nodeIdx = skillNodes.findIndex(n => n.userData.skill?.skill_id === skillId || n.userData.skill?.name === skillId);
  if (nodeIdx === -1) return;

  const node = skillNodes[nodeIdx];
  const pos = node.position.clone();
  const col = new THREE.Color(node.material.color);

  // Create shatter particles
  const particleCount = 30;
  const shatterGeo = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const velocities = [];
  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = pos.x;
    positions[i * 3 + 1] = pos.y;
    positions[i * 3 + 2] = pos.z;
    velocities.push(new THREE.Vector3(
      (Math.random() - 0.5) * 0.08,
      Math.random() * 0.06,
      (Math.random() - 0.5) * 0.08
    ));
  }
  shatterGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const shatterMat = new THREE.PointsMaterial({
    color: col, size: 0.06, transparent: true, opacity: 0.9,
    blending: THREE.AdditiveBlending, depthWrite: false
  });
  const shatterPts = new THREE.Points(shatterGeo, shatterMat);
  shatterPts.userData._shatter = { velocities, startTime: clock.getElapsedTime(), duration: 1.5 };
  scene.add(shatterPts);

  // Remove original node and associated elements near its position
  skillNodes.splice(nodeIdx, 1);
  const toRemove = [];
  extractionGroup.children.forEach(child => {
    if (child === node) { toRemove.push(child); return; }
    // Remove nearby elements (glow, light, label, halo, ring)
    if (child.position.distanceTo(pos) < 1.2 && child !== node) {
      toRemove.push(child);
    }
  });
  toRemove.forEach(child => {
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      if (child.material.map) child.material.map.dispose();
      child.material.dispose();
    }
    extractionGroup.remove(child);
  });
}

// ── Skill Node 3D — 生命周期6阶段视觉差异 ───────────────────────
function getLifecycleVisuals(skill) {
  const stage = skill.lifecycle_stage || 'team_local';
  const type = classifySkill(skill);
  const scope = skill.visibility || skill.draft_scope || 'private';
  const isPublic = scope === 'public' || scope === 'shared';
  let baseColor, sphereR, orbR;

  if (isPublic) {
    // Public skills: cool blue-cyan palette
    if (type === 'atomic') { baseColor = 0x6AB0E8; sphereR = 0.25; orbR = 3 + Math.random() * 1.5; }
    else if (type === 'trait') { baseColor = 0x48C9B0; sphereR = 0.32; orbR = 5 + Math.random() * 2; }
    else { baseColor = 0x5DADE2; sphereR = 0.4; orbR = 7 + Math.random() * 2; }
  } else {
    // Personal skills: warm palette (original)
    if (type === 'atomic') { baseColor = 0xB898C8; sphereR = 0.25; orbR = 3 + Math.random() * 1.5; }
    else if (type === 'trait') { baseColor = 0xC8B468; sphereR = 0.32; orbR = 5 + Math.random() * 2; }
    else { baseColor = 0x88AABA; sphereR = 0.4; orbR = 7 + Math.random() * 2; }
  }

  // Scale by usage_count (Phase 4 mapping)
  const usageScale = 1 + Math.min((skill.usage_count || 0) / 20, 0.6);
  sphereR *= usageScale;

  // Lifecycle-specific material params
  const params = { color: baseColor, sphereR, orbR, geo: 'sphere', isPublic };
  switch (stage) {
    case 'draft':       // 胚胎: 半透明闪烁虚影
      Object.assign(params, { opacity: 0.25, emissive: 0.03, transmission: 0.85, blink: true, lightIntensity: 0.08 });
      break;
    case 'team_local':  // 新生: 微弱发光实体
      Object.assign(params, { opacity: 0.7, emissive: 0.10, transmission: 0.6, blink: false, lightIntensity: 0.2 });
      break;
    case 'published':   // 发布: 明亮脉动+光环
      Object.assign(params, { opacity: 1.0, emissive: 0.20, transmission: 0.5, blink: false, lightIntensity: 0.4, halo: true });
      break;
    case 'verified':    // 验证: 稳定明亮+绿色验证环
      Object.assign(params, { opacity: 1.0, emissive: 0.25, transmission: 0.4, blink: false, lightIntensity: 0.5, verifyRing: true });
      break;
    case 'solidified':  // 固化: 晶莹剔透+几何切面
      Object.assign(params, { opacity: 1.0, emissive: 0.30, transmission: 0.8, blink: false, lightIntensity: 0.6, geo: 'icosa' });
      break;
    case 'degraded':    // 退化: 暗淡+微颤
      Object.assign(params, { opacity: 0.4, emissive: 0.02, transmission: 0.3, blink: false, lightIntensity: 0.05, degraded: true });
      break;
    default:
      Object.assign(params, { opacity: 0.7, emissive: 0.10, transmission: 0.6, blink: false, lightIntensity: 0.2 });
  }
  return params;
}

function spawnSkillNode(skill) {
  const type = classifySkill(skill);
  const angle = Math.random() * Math.PI * 2;
  const v = getLifecycleVisuals(skill);
  const col = new THREE.Color(v.color);

  // Torus ring geometry (agent-head style)
  const torusR = v.sphereR * 0.85;
  const torusTube = v.sphereR * 0.12;
  const outlineMat2 = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: v.opacity, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(new THREE.TorusGeometry(torusR, torusTube, 12, 32), outlineMat2);
  const x = Math.cos(angle) * v.orbR;
  const z = Math.sin(angle) * v.orbR;
  mesh.position.set(x, v.sphereR, z);
  // Glow halo ring
  const glowRing2 = new THREE.Mesh(
    new THREE.TorusGeometry(torusR, torusTube * 3.5, 12, 32),
    new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: v.opacity * 0.25, side: THREE.DoubleSide })
  );
  glowRing2.position.copy(mesh.position);
  extractionGroup.add(glowRing2);
  mesh.userData._glowRing = glowRing2;
  mesh.userData = { skill, type, spawnTime: clock.getElapsedTime(), lifecycle: v, blink: v.blink, degraded: v.degraded || false };
  extractionGroup.add(mesh);
  skillNodes.push(mesh);

  // 地面光斑
  const glow = new THREE.Mesh(
    new THREE.CircleGeometry(0.6, 12),
    new THREE.MeshBasicMaterial({ color: v.color, transparent: true, opacity: 0.04, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  glow.rotation.x = -Math.PI / 2;
  glow.position.set(x, 0.003, z);
  extractionGroup.add(glow);

  // Halo ring for published stage
  if (v.halo) {
    const haloMat = new THREE.MeshBasicMaterial({ color: v.color, transparent: true, opacity: 0.12, side: THREE.DoubleSide });
    const haloMesh = new THREE.Mesh(new THREE.RingGeometry(v.sphereR * 1.3, v.sphereR * 1.8, 16), haloMat);
    haloMesh.rotation.x = -Math.PI / 2;
    haloMesh.position.set(x, v.sphereR * 0.5, z);
    extractionGroup.add(haloMesh);
  }

  // Public scope ring — cyan orbital ring
  if (v.isPublic) {
    const scopeMat = new THREE.MeshBasicMaterial({ color: 0x48C9B0, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    const scopeRing = new THREE.Mesh(new THREE.TorusGeometry(v.sphereR * 1.6, 0.018, 4, 16), scopeMat);
    scopeRing.position.set(x, v.sphereR, z);
    scopeRing.rotation.x = Math.PI / 5;
    scopeRing.userData._scopeRing = true;
    extractionGroup.add(scopeRing);
  }

  // Verify ring for verified stage — green ring
  if (v.verifyRing) {
    const vRingMat = new THREE.MeshBasicMaterial({ color: 0x4CAF50, transparent: true, opacity: 0.35, side: THREE.DoubleSide });
    const vRing = new THREE.Mesh(new THREE.TorusGeometry(v.sphereR * 1.2, 0.02, 4, 16), vRingMat);
    vRing.position.set(x, v.sphereR, z);
    vRing.rotation.x = Math.PI / 3;
    vRing.userData.isVerifyRing = true;
    extractionGroup.add(vRing);
  }

  // Label sprite
  const labelCanvas = makeSkillLabel(skill.icon || '⚡', skill.name || '');
  const tex = new THREE.CanvasTexture(labelCanvas);
  tex.minFilter = THREE.LinearFilter;
  const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  label.position.set(x, v.sphereR * 2 + 0.6, z);
  const scaleX = 2 * (labelCanvas.width / 256);
  label.scale.set(scaleX, 0.5, 1);
  extractionGroup.add(label);
  mesh.userData._label = label;
}

function makeSkillLabel(icon, name) {
  const c = document.createElement('canvas');
  const ctx = c.getContext('2d');
  const font = '500 22px "Noto Sans SC", sans-serif';
  ctx.font = font;
  const text = `${icon} ${name}`;
  const measured = ctx.measureText(text).width;
  const pad = 32;
  c.width = Math.max(256, Math.ceil(measured + pad));
  c.height = 64;
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.font = font;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#B0A898';
  ctx.fillText(text, c.width / 2, 32);
  return c;
}

function rebuildSkillNodes() {
  // Clear ALL children from extractionGroup (meshes, lights, sprites, glow circles)
  while (extractionGroup.children.length > 0) {
    const child = extractionGroup.children[0];
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      if (child.material.map) child.material.map.dispose();
      child.material.dispose();
    }
    extractionGroup.remove(child);
  }
  skillNodes = [];
  const seenSlugs = new Set();
  // Show queue items as crystals (draft / approved)
  queueItems.forEach(q => {
    if (q.status !== 'ready_for_review' && q.status !== 'approved') return;
    const slug = q.draft_slug || q.item_id;
    if (seenSlugs.has(slug)) return;
    seenSlugs.add(slug);
    spawnSkillNodeAnimated({
      skill_id: slug,
      name: q.draft_name || q.source_title || '未命名',
      icon: q.draft_icon || '⚡',
      category: q.draft_category || 'general',
      slug: slug,
      lifecycle_stage: q.status === 'approved' ? 'team_local' : 'draft',
      required_tools: q.draft_required_tools || [],
      description: q.draft_description || '',
      visibility: q.draft_scope || 'private',
      draft_scope: q.draft_scope || 'private',
      _from_queue: true,
    });
  });
  // Also show registered team skills not from queue
  if (allSkills && allSkills.length) {
    allSkills.forEach(s => {
      const slug = s.slug || s.skill_id;
      if (seenSlugs.has(slug)) return;
      seenSlugs.add(slug);
      spawnSkillNodeAnimated({
        skill_id: s.skill_id || slug,
        name: s.name || '未命名',
        icon: s.icon || '⚡',
        category: s.category || 'general',
        slug: slug,
        lifecycle_stage: s.lifecycle_stage || 'team_local',
        required_tools: s.required_tools || [],
        description: s.description || '',
        visibility: s.visibility || 'team',
      });
    });
  }
  // Draw lineage lines
  buildLineageLines();
}

// ── Highlight Latest Crystal ────────────────────────────────────
function highlightLatestCrystal() {
  if (!skillNodes.length) return;
  // Find newest crystal (latest spawnTime)
  let latest = skillNodes[0];
  for (const node of skillNodes) {
    if ((node.userData.spawnTime || 0) >= (latest.userData.spawnTime || 0)) latest = node;
  }
  if (!latest) return;
  _doHighlight(latest);
}

function highlightExistingCrystal(itemId) {
  if (!skillNodes.length || !itemId) return;
  const target = skillNodes.find(n => {
    const s = n.userData.skill;
    return s && (s.skill_id === itemId || s.slug === itemId);
  });
  if (target) _doHighlight(target);
}

function _doHighlight(latest) {
  // Cancel any previous highlight animation
  if (window._highlightFocusInterval) clearInterval(window._highlightFocusInterval);
  if (window._highlightRestoreTimer) clearTimeout(window._highlightRestoreTimer);

  // Dim all others
  skillNodes.forEach(n => {
    if (n !== latest && n.material) {
      n.userData._preHighlightEmissive = n.material.emissiveIntensity;
      n.material.emissiveIntensity *= 0.3;
      n.material.opacity *= 0.5;
    }
  });

  // Bright pulse ring on latest
  const pos = latest.position;
  const r = latest.geometry?.parameters?.radius || 0.3;
  const pulseGeo = new THREE.RingGeometry(r * 1.2, r * 2.5, 48);
  const pulseMat = new THREE.MeshBasicMaterial({
    color: 0xFFD700, transparent: true, opacity: 0.5,
    side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const pulseRing = new THREE.Mesh(pulseGeo, pulseMat);
  pulseRing.position.copy(pos);
  pulseRing.rotation.x = -Math.PI / 2;
  pulseRing.userData._highlightPulse = { start: clock.getElapsedTime(), duration: 3.0 };
  extractionGroup.add(pulseRing);

  // Boost latest crystal glow
  if (latest.material) {
    latest.material.emissiveIntensity = 0.6;
    latest.material.opacity = 1.0;
  }

  // Smooth camera focus on latest crystal
  const targetPos = new THREE.Vector3().copy(pos).add(new THREE.Vector3(0, 2, 4));
  const startPos = camera.position.clone();
  const startTarget = controls.target.clone();
  const endTarget = pos.clone();
  let focusT = 0;
  window._highlightFocusInterval = setInterval(() => {
    focusT += 0.02;
    if (focusT >= 1) {
      clearInterval(window._highlightFocusInterval);
      // Restore other crystals after 3s
      window._highlightRestoreTimer = setTimeout(() => {
        skillNodes.forEach(n => {
          if (n !== latest && n.material && n.userData._preHighlightEmissive !== undefined) {
            n.material.emissiveIntensity = n.userData._preHighlightEmissive;
            n.material.opacity = n.userData.lifecycle?.opacity || 0.7;
            delete n.userData._preHighlightEmissive;
          }
        });
      }, 2500);
      return;
    }
    const ease = focusT * (2 - focusT); // easeOut
    camera.position.lerpVectors(startPos, targetPos, ease);
    controls.target.lerpVectors(startTarget, endTarget, ease);
    controls.update();
  }, 16);
}

// ── Lineage Lines (parent → child) ─────────────────────────────
function buildLineageLines() {
  // Remove old lineage lines
  const toRemove = [];
  extractionGroup.children.forEach(c => { if (c.userData?._lineageLine) toRemove.push(c); });
  toRemove.forEach(c => { c.geometry?.dispose(); c.material?.dispose(); extractionGroup.remove(c); });

  skillNodes.forEach(childNode => {
    const parentId = childNode.userData.skill?.lineage;
    if (!parentId) return;
    const parentNode = skillNodes.find(n => n.userData.skill?.skill_id === parentId);
    if (!parentNode) return;
    // Curved line from parent to child
    const p1 = parentNode.position.clone();
    const p2 = childNode.position.clone();
    const mid = p1.clone().add(p2).multiplyScalar(0.5);
    mid.y += 0.8; // arc upward
    const curve = new THREE.QuadraticBezierCurve3(p1, mid, p2);
    const pts = curve.getPoints(20);
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const mat = new THREE.LineBasicMaterial({
      color: 0xD4A574, transparent: true, opacity: 0.2,
      blending: THREE.AdditiveBlending, depthWrite: false
    });
    const line = new THREE.Line(geo, mat);
    line.userData._lineageLine = true;
    extractionGroup.add(line);
  });
}

// ── Ambient Dust ────────────────────────────────────────────────
function buildAmbientDust() {
  const count = 120;
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 50;
    positions[i * 3 + 1] = Math.random() * 10 + 0.5;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 50;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const mat = new THREE.PointsMaterial({
    color: 0x584838, size: 0.1, transparent: true, opacity: 0.3
  });
  scene.add(new THREE.Points(geo, mat));
}

// ── Animation Loop ──────────────────────────────────────────────
function animate() {
  requestAnimationFrame(animate);
  animTime = clock.getElapsedTime();
  animFrame++;
  controls.update();

  const metabolic = Math.sin(animTime * 0.4) * 0.5 + 0.5;

  // Human breathing + glow
  if (humanFigure) {
    humanFigure.position.y = Math.sin(animTime * 0.5) * 0.03;
    const head = humanFigure.userData.head;
    if (head) head.material.opacity = 0.5 + metabolic * 0.2;
    humanFigure.children.forEach(child => {
      if (child.type === 'PointLight') {
        child.intensity = 0.4 + metabolic * 0.3;
      }
    });
  }

  // Mycelium pulsation (throttled to every 6th frame)
  if (myceliumGroup && (animFrame & 5) === 0) {
    const wave = Math.sin(animTime * 0.6) * 0.5 + 0.5;
    const baseOp = 0.05 + wave * 0.12 + metabolic * 0.04;
    myceliumGroup.children.forEach((mesh) => {
      if (mesh.material && !mesh.userData._growing) {
        if (!extractionActive) mesh.material.opacity = baseOp;
      }
    });
  }

  // Extraction particles — spiral inward, then redistribute outward
  if (extractParticleGeo && extractParticleData.length > 0) {
    const eArr = extractParticleGeo.attributes.position.array;
    const activeSpeed = extractionActive ? 2.5 : 1.0;
    for (let i = 0; i < EXTRACT_PARTICLE_COUNT; i++) {
      const ed = extractParticleData[i];
      ed.phase = (ed.phase + ed.speed * activeSpeed) % 1;
      if (ed.phase < 0.5) {
        // Spiral inward (absorption)
        const p = ed.phase / 0.5;
        const r = ed.startR * (1 - p);
        const spiral = ed.angle + p * 1.5;
        eArr[i * 3] = Math.cos(spiral) * r;
        eArr[i * 3 + 1] = 0.05 + Math.sin(p * Math.PI) * 0.4;
        eArr[i * 3 + 2] = Math.sin(spiral) * r;
      } else {
        // Redistribute outward to skill node positions
        const p = (ed.phase - 0.5) / 0.5;
        const tx = Math.cos(ed.targetAngle) * ed.targetR;
        const tz = Math.sin(ed.targetAngle) * ed.targetR;
        eArr[i * 3] = p * tx;
        eArr[i * 3 + 1] = 0.05 + Math.sin(p * Math.PI) * 0.3;
        eArr[i * 3 + 2] = p * tz;
      }
    }
    extractParticleGeo.attributes.position.needsUpdate = true;
  }

  // Skill node lifecycle animation
  skillNodes.forEach(node => {
    // Router mode: orbit animation
    if (node.userData._orbit) {
      const orb = node.userData._orbit;
      orb.angle += orb.speed * 0.016; // ~60fps
      node.position.x = Math.cos(orb.angle) * orb.radius;
      node.position.z = Math.sin(orb.angle) * orb.radius;
      node.position.y = orb.baseY + Math.sin(animTime * 0.8 + orb.angle) * 0.15;
      if (node.userData._glowRing) node.userData._glowRing.position.copy(node.position);
      if (node.userData._label) {
        node.userData._label.position.set(node.position.x, node.position.y + 0.8, node.position.z);
      }
      return; // skip lifecycle animation for routed nodes
    }

    // Skip lifecycle for nodes currently in fly animation
    if (node.userData._flying) return;

    const age = animTime - (node.userData.spawnTime || 0);
    const g = Math.sin(age * 0.5) * 0.5 + 0.5;
    const baseY = node.userData.lifecycle?.sphereR || node.geometry?.parameters?.radius || 0.3;

    // Growth animation for newly spawned torus rings
    // Flat-to-upright: like a life form learning to stand
    if (node.userData._animating) {
      const growAge = Math.min(age / 2.5, 1); // 2.5s growth (slower, more dramatic)
      const eased = 1 - Math.pow(1 - growAge, 3); // ease-out cubic
      node.scale.set(eased, eased, eased);
      node.material.opacity = node.userData._targetOpacity * eased;
      // Rotate from flat (-PI/2) to upright (0)
      const tiltEased = 1 - Math.pow(1 - Math.min(growAge * 1.2, 1), 4); // ease-out quartic, slightly ahead
      node.rotation.x = -Math.PI / 2 * (1 - tiltEased);
      // Glow ring stays dim during growth, brightens after
      if (node.userData._glowRing) {
        node.userData._glowRing.scale.set(eased, eased, eased);
        node.userData._glowRing.rotation.x = node.rotation.x;
        node.userData._glowRing.material.opacity = 0; // keep dark during growth
      }
      if (growAge >= 1) {
        node.userData._animating = false;
        node.material.opacity = node.userData._targetOpacity;
        node.scale.set(1, 1, 1);
        node.rotation.x = 0;
        if (node.userData._glowBrighten) {
          node.userData._glowBrightenStart = animTime; // start brightening now
        }
        if (node.userData._glowRing) {
          node.userData._glowRing.scale.set(1, 1, 1);
          node.userData._glowRing.rotation.x = 0;
        }
      }
    }

    // Glow gradually brightens after growth completes (2s ease-in)
    if (node.userData._glowBrighten && node.userData._glowRing && node.userData._glowBrightenStart) {
      const glowAge = Math.min((animTime - node.userData._glowBrightenStart) / 2.0, 1);
      const glowEased = glowAge * glowAge; // ease-in quadratic
      const targetOp = node.userData._glowTargetOpacity || 0.15;
      node.userData._glowRing.material.opacity = targetOp * glowEased;
      if (glowAge >= 1) {
        node.userData._glowBrighten = false; // done brightening
        node.userData._glowRing.material.opacity = targetOp;
      }
    }

    if (node.userData.blink) {
      // Draft: blink (opacity oscillates 0.1–0.35)
      node.material.opacity = 0.1 + Math.abs(Math.sin(age * 2.5)) * 0.25;
      if (node.userData._glowRing) node.userData._glowRing.material.opacity = node.material.opacity * 0.3;
    } else if (node.userData.degraded) {
      // Degraded: micro-shake
      node.position.x += (Math.random() - 0.5) * 0.003;
      node.position.z += (Math.random() - 0.5) * 0.003;
    }
    node.position.y = baseY + Math.sin(animTime * 0.8 + node.position.x) * 0.04;
    // Sync glow ring position
    if (node.userData._glowRing) node.userData._glowRing.position.copy(node.position);

    // Evolution VFX: shrink → expand
    if (node.userData._evolving) {
      const ev = node.userData._evolving;
      const evAge = animTime - ev.start;
      if (evAge < 0.6) {
        // Phase 1: shrink down
        const s = ev.origScale * (1 - evAge / 0.6 * 0.7);
        node.scale.set(s, s, s);
        node.material.emissiveIntensity = 0.3 + evAge * 0.5;
      } else if (evAge < 1.2) {
        // Phase 2: hold small + glow
        const s = ev.origScale * 0.3;
        node.scale.set(s, s, s);
        node.material.emissiveIntensity = 0.8;
      } else if (evAge < 2.2) {
        // Phase 3: expand to new size
        const t = (evAge - 1.2) / 1.0;
        const eased = 1 - Math.pow(1 - t, 3);
        const s = ev.origScale * (0.3 + eased * 0.85);
        node.scale.set(s, s, s);
        node.material.emissiveIntensity = 0.8 - eased * 0.6;
      }
    }
  });

  // Growing mycelium fade-in animation
  if (myceliumGroup) {
    myceliumGroup.children.forEach(mesh => {
      if (mesh.userData._growing) {
        const growStart = mesh.userData._growStart || 0;
        if (animTime < growStart) return; // Delayed start
        const growAge = Math.min((animTime - growStart) / 1.0, 1);
        mesh.material.opacity = (mesh.userData._targetOpacity || 0.18) * growAge;
        if (growAge >= 1) mesh.userData._growing = false;
      }
    });
  }

  // Shatter particle animation
  scene.children.forEach(child => {
    if (child.isPoints && child.userData._shatter) {
      const sh = child.userData._shatter;
      const elapsed = animTime - sh.startTime;
      const progress = elapsed / sh.duration;
      if (progress >= 1) {
        child.geometry.dispose();
        child.material.dispose();
        scene.remove(child);
        return;
      }
      const arr = child.geometry.attributes.position.array;
      for (let i = 0; i < sh.velocities.length; i++) {
        arr[i * 3] += sh.velocities[i].x;
        arr[i * 3 + 1] += sh.velocities[i].y;
        arr[i * 3 + 2] += sh.velocities[i].z;
        sh.velocities[i].y -= 0.001; // gravity
      }
      child.geometry.attributes.position.needsUpdate = true;
      child.material.opacity = 0.9 * (1 - progress);
    }
  });

  // Rotate verify rings + animate scan rings
  extractionGroup.children.forEach(child => {
    if (child.userData?.isVerifyRing) {
      child.rotation.z = animTime * 0.3;
    }
    if (child.userData?._scanRing) {
      // Fast spinning + wobble during verification
      const scanAge = animTime - (child.userData._scanStart || 0);
      child.rotation.x = Math.PI / 3 + Math.sin(scanAge * 3) * 0.4;
      child.rotation.z = scanAge * 4;
      child.material.opacity = 0.3 + Math.abs(Math.sin(scanAge * 5)) * 0.4;
    }
    if (child.userData?._degradedRing) {
      // Red warning ring: flicker + slow rotation
      child.rotation.z = animTime * 0.5;
      child.material.opacity = 0.08 + Math.abs(Math.sin(animTime * 3)) * 0.25;
    }
    if (child.userData?._scopeRing) {
      // Public scope ring: gentle orbital rotation
      child.rotation.z = animTime * 0.2;
      child.rotation.x = Math.PI / 5 + Math.sin(animTime * 0.5) * 0.1;
    }
    if (child.userData?._evolveBeam) {
      // Beam fade out over 2s
      const beamAge = animTime - child.userData._evolveBeam.start;
      child.material.opacity = Math.max(0, 0.5 - beamAge * 0.25);
      child.rotation.y = beamAge * 2;
    }
    if (child.userData?._highlightPulse) {
      const hp = child.userData._highlightPulse;
      const hpAge = animTime - hp.start;
      if (hpAge > hp.duration) {
        child.geometry?.dispose();
        child.material?.dispose();
        extractionGroup.remove(child);
      } else {
        const t = hpAge / hp.duration;
        child.scale.set(1 + t * 1.5, 1 + t * 1.5, 1);
        child.material.opacity = 0.5 * (1 - t);
        child.rotation.z = hpAge * 0.8;
      }
    }
  });

  // Animate injected skill rings orbiting agent head
  if (humanFigure?.userData?._injectedRings) {
    humanFigure.userData._injectedRings.forEach(ring => {
      const d = ring.userData._injectedRing;
      if (!d) return;
      if (d.axis === 'y') ring.rotation.y += d.speed * 0.016;
      else ring.rotation.z += d.speed * 0.016;
    });
  }

  renderer.render(scene, camera);
}

function onResize() {
  const w = window.innerWidth, h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

window.addEventListener('resize', onResize);

// ── Raycasting — hover tooltip + click to detail ────────────────
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let hoveredNode = null;

// Tooltip element
const tooltip = document.createElement('div');
tooltip.style.cssText = 'position:fixed;z-index:50;background:oklch(0.14 0.005 60/.92);border:1px solid oklch(1 0 0/.1);backdrop-filter:blur(8px);padding:8px 12px;font-size:11px;color:oklch(0.82 0.003 110);pointer-events:none;display:none;font-family:var(--font-sans);max-width:220px;line-height:1.5';
document.body.appendChild(tooltip);

// Context menu element
const ctxMenu = document.createElement('div');
ctxMenu.style.cssText = 'position:fixed;z-index:60;background:oklch(0.12 0.005 60/.95);border:1px solid oklch(1 0 0/.12);backdrop-filter:blur(12px);padding:4px 0;font-size:12px;color:oklch(0.82 0.003 110);display:none;font-family:var(--font-sans);min-width:160px;box-shadow:0 8px 24px oklch(0 0 0/.5)';
document.body.appendChild(ctxMenu);
let ctxSkill = null;
function showCtxMenu(e, skill) {
  ctxSkill = skill;
  const stage = skill.lifecycle_stage || 'team_local';
  const items = [
    { icon: '📝', label: '查看详情', action: 'detail' },
    { icon: '✏️', label: '编辑', action: 'edit' },
    stage === 'team_local' ? { icon: '🌐', label: '发布到公共库', action: 'publish' } : null,
    { icon: '⚡', label: '触发演化', action: 'evolve' },
    { icon: '🧪', label: '验证', action: 'verify' },
    { icon: '🔗', label: '查看谱系', action: 'lineage' },
    null, // separator
    { icon: '🗑️', label: '删除', action: 'delete', danger: true },
  ].filter(Boolean);
  ctxMenu.innerHTML = items.map(it => {
    if (it === null) return '<div style="height:1px;background:oklch(1 0 0/.08);margin:4px 0"></div>';
    const color = it.danger ? 'oklch(0.7 0.15 25)' : 'oklch(0.82 0.003 110)';
    return `<div data-action="${it.action}" style="padding:6px 14px;cursor:pointer;color:${color};display:flex;align-items:center;gap:8px;transition:background .15s" onmouseenter="this.style.background='oklch(1 0 0/.06)'" onmouseleave="this.style.background=''">${it.icon} ${it.label}</div>`;
  }).join('');
  ctxMenu.style.display = 'block';
  ctxMenu.style.left = Math.min(e.clientX, window.innerWidth - 180) + 'px';
  ctxMenu.style.top = Math.min(e.clientY, window.innerHeight - ctxMenu.offsetHeight - 10) + 'px';
}
ctxMenu.addEventListener('click', async (e) => {
  const action = e.target.closest('[data-action]')?.dataset.action;
  if (!action || !ctxSkill) return;
  ctxMenu.style.display = 'none';
  const s = ctxSkill;
  const qItem = queueItems.find(q => q.draft_name === s.name || q.item_id === s.skill_id);
  switch (action) {
    case 'detail': case 'edit':
      if (qItem) window._openDetail(qItem.item_id);
      else addMessage('system', `${s.icon || '⚡'} <b>${s.name}</b> — ${s.description || ''}`);
      break;
    case 'publish':
      const pr = await publishSkillWithGate(s.skill_id, s.name);
      if (pr && !pr.error) { showToast('🌐 已发布'); loadSkills(); addMessage('system', `🌐 技能「${s.name}」已发布为公共技能`); }
      else showToast(pr?.error || '发布失败', 'error');
      break;
    case 'evolve':
      if (qItem) { window._openDetail(qItem.item_id); setTimeout(() => switchModalTab('evolve'), 200); }
      else addMessage('system', `/evolve ${s.skill_id}`);
      break;
    case 'verify':
      if (qItem) { window._openDetail(qItem.item_id); setTimeout(() => switchModalTab('verify'), 200); }
      else addMessage('system', `/verify ${s.skill_id}`);
      break;
    case 'lineage':
      const lin = await api(`/skill-library/${s.skill_id}/lineage?team_id=${currentTeamId}`);
      if (lin) addMessage('system', `🔗 谱系: ${JSON.stringify(lin.lineage || [], null, 1)}`);
      break;
    case 'delete':
      if (qItem) window._deleteItem(qItem.item_id);
      else { showConfirm(`确认删除技能「${s.name}」？`, () => { shatterSkillNode(s.skill_id || s.name); showToast('🗑️ 已删除'); }); }
      break;
  }
});
document.addEventListener('click', () => ctxMenu.style.display = 'none');
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') ctxMenu.style.display = 'none'; });

document.getElementById('viewport').addEventListener('mousemove', (e) => {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(skillNodes, false);

  if (hits.length > 0) {
    const node = hits[0].object;
    if (hoveredNode !== node) {
      // Restore previous
      if (hoveredNode && hoveredNode.material) {
        hoveredNode.material.emissiveIntensity = hoveredNode.userData.lifecycle?.emissive || 0.1;
      }
      hoveredNode = node;
      node.material.emissiveIntensity = 0.5; // highlight
    }
    const s = node.userData.skill;
    const stage = s.lifecycle_stage || 'team_local';
    const stageLabels = { draft:'胚胎', team_local:'新生', published:'发布', verified:'已验证', solidified:'固化', degraded:'退化' };
    tooltip.innerHTML = `<b>${s.icon || '⚡'} ${s.name}</b><br>${s.category || ''} · ${stageLabels[stage] || stage}<br>效果: ${((s.effectiveness || 0) * 100).toFixed(0)}% · 使用: ${s.usage_count || 0}次`;
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX + 12) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
    renderer.domElement.style.cursor = 'pointer';
  } else {
    if (hoveredNode && hoveredNode.material) {
      hoveredNode.material.emissiveIntensity = hoveredNode.userData.lifecycle?.emissive || 0.1;
    }
    hoveredNode = null;
    tooltip.style.display = 'none';
    renderer.domElement.style.cursor = '';
  }
});

document.getElementById('viewport').addEventListener('click', (e) => {
  if (!hoveredNode) return;
  const s = hoveredNode.userData.skill;
  // Find matching queue item to open detail
  const qItem = queueItems.find(q => q.draft_name === s.name || q.item_id === s.skill_id);
  if (qItem) {
    window._openDetail(qItem.item_id);
  } else {
    // Show skill info in message flow
    addMessage('system', `${s.icon || '⚡'} <b>${s.name}</b> — ${s.description || ''}<br>阶段: ${s.lifecycle_stage || 'team_local'} · 效果: ${((s.effectiveness || 0) * 100).toFixed(0)}%`);
  }
});

document.getElementById('viewport').addEventListener('contextmenu', (e) => {
  if (!hoveredNode) return;
  e.preventDefault();
  e.stopPropagation();
  showCtxMenu(e, hoveredNode.userData.skill);
});

// ═══ SKILL ROUTER MODE ═══════════════════════════════════════════════════
(function initRouterMode() {
  let currentPageMode = 'extract';
  let routerSelectedSkills = new Set();
  let routerResults = [];
  let selectedAgentId = 'default';

  // Mode switching
  window._switchPageMode = function(mode) {
    currentPageMode = mode;
    document.body.classList.toggle('mode-router', mode === 'router');
    // Update toggle buttons
    document.querySelectorAll('.mode-toggle button').forEach(b => {
      b.classList.toggle('active', b.dataset.mode === mode);
    });
    // Update seal + title
    const seal = document.getElementById('mode-seal');
    const title = document.getElementById('mode-title');
    if (mode === 'router') {
      seal.textContent = '赋';
      title.textContent = '技能萃取/赋予';
      // Show agent figure in router mode
      if (humanFigure) humanFigure.visible = true;
      // Show assign bar immediately
      updateAssignBar();
    } else {
      seal.textContent = '萃';
      title.textContent = '技能萃取/赋予';
      // Hide agent figure in extraction mode — skill nodes stay visible
      if (humanFigure) humanFigure.visible = false;
      // Hide assign bar
      const bar = document.getElementById('rassign-bar');
      if (bar) bar.classList.remove('always-show', 'visible');
      // Rebuild extraction 3D view
      rebuildSkillNodes();
    }
    // Load agents list when entering router mode
    if (mode === 'router') { loadRouterAgents(); _loadDashboard(); }
  };

  // Load agents
  async function loadRouterAgents() {
    try {
      const agents = await listApi(`/teams/${currentTeamId || 'default'}/agents`);
      if (agents.length === 0) return;
      const list = document.getElementById('ragent-list');
      list.innerHTML = agents.map((a, i) => `
        <div class="ragent-item${i === 0 ? ' selected' : ''}" data-agent-id="${a.agent_id || a.id || a.name}" data-agent-name="${a.name}" data-agent-color="${a.color || ''}" onclick="window._selectRouterAgent(this)">
          <span class="ra-icon">${a.avatar || '🤖'}</span>
          <span class="ra-name">${a.name}</span>
          <span class="ra-badge">${a.role || '通用'}</span>
        </div>
      `).join('');
      selectedAgentId = agents[0]?.agent_id || agents[0]?.id || agents[0]?.name || 'default';
      // Update 3D figure to match first agent
      updateAgentFigure3D(agents[0]?.name || '智能体', agents[0]?.color || '#D4A574');
    } catch(e) { /* keep default */ }
  }

  window._selectRouterAgent = function(el) {
    document.querySelectorAll('.ragent-item').forEach(x => x.classList.remove('selected'));
    el.classList.add('selected');
    selectedAgentId = el.dataset.agentId;
    // Update 3D figure to represent selected agent
    const name = el.dataset.agentName || el.querySelector('.ra-name')?.textContent || '智能体';
    const color = el.dataset.agentColor || '#D4A574';
    updateAgentFigure3D(name, color);
    // Load agent skill profile
    _loadAgentProfile(selectedAgentId);
  };

  async function _loadAgentProfile(agentId) {
    const panel = document.getElementById('agent-profile-panel');
    if (!agentId || agentId === 'default') { panel.style.display = 'none'; return; }
    try {
      const data = await routerApi(`/agent-profile/${currentTeamId}/${agentId}`);
      if (!data || data.error) { panel.style.display = 'none'; return; }
      panel.style.display = 'block';
      // Draw radar chart
      _drawRadarChart(data.radar || []);
      // Show skill list
      const skillsDiv = document.getElementById('agent-profile-skills');
      if (data.skills && data.skills.length > 0) {
        skillsDiv.innerHTML = data.skills.map(s =>
          `<span style="display:inline-block;padding:2px 6px;margin:2px;background:oklch(0.22 0.02 110);border:1px solid oklch(0.35 0.02 110);border-radius:3px">${s.icon} ${s.name}${s.avg_rating ? ` ⭐${s.avg_rating}` : ''}</span>`
        ).join('');
      } else {
        skillsDiv.innerHTML = '<span style="opacity:0.5">暂无注入技能</span>';
      }
    } catch(e) { panel.style.display = 'none'; }
  }

  function _drawRadarChart(radarData) {
    const canvas = document.getElementById('agent-radar-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const cx = W / 2, cy = H / 2, R = 70;
    ctx.clearRect(0, 0, W, H);

    if (!radarData || radarData.length < 3) {
      ctx.fillStyle = 'oklch(0.4 0.01 110)';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('需要3+类别才能生成雷达图', cx, cy);
      return;
    }

    const n = radarData.length;
    const maxVal = Math.max(...radarData.map(d => d.value), 1);
    const angleStep = (2 * Math.PI) / n;

    // Draw grid circles
    for (let ring = 1; ring <= 3; ring++) {
      const r = R * ring / 3;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const a = i * angleStep - Math.PI / 2;
        const x = cx + r * Math.cos(a);
        const y = cy + r * Math.sin(a);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'oklch(0.3 0.01 110)';
      ctx.lineWidth = 0.5;
      ctx.stroke();
    }

    // Draw axes and labels
    radarData.forEach((d, i) => {
      const a = i * angleStep - Math.PI / 2;
      const x = cx + R * Math.cos(a);
      const y = cy + R * Math.sin(a);
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.strokeStyle = 'oklch(0.35 0.01 110)';
      ctx.lineWidth = 0.5;
      ctx.stroke();
      // Label
      const lx = cx + (R + 14) * Math.cos(a);
      const ly = cy + (R + 14) * Math.sin(a);
      ctx.fillStyle = 'oklch(0.6 0.02 110)';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(d.axis, lx, ly);
    });

    // Draw data polygon
    ctx.beginPath();
    radarData.forEach((d, i) => {
      const a = i * angleStep - Math.PI / 2;
      const r = R * (d.value / maxVal);
      const x = cx + r * Math.cos(a);
      const y = cy + r * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.fillStyle = 'oklch(0.55 0.12 145 / 0.25)';
    ctx.fill();
    ctx.strokeStyle = 'oklch(0.65 0.12 145)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Draw data points
    radarData.forEach((d, i) => {
      const a = i * angleStep - Math.PI / 2;
      const r = R * (d.value / maxVal);
      const x = cx + r * Math.cos(a);
      const y = cy + r * Math.sin(a);
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = 'oklch(0.75 0.12 145)';
      ctx.fill();
    });
  }

  // ── Skill Pool Dashboard ──
  async function _loadDashboard() {
    if (!currentTeamId) return;
    const panel = document.getElementById('skill-dashboard');
    try {
      const data = await routerApi(`/dashboard/${currentTeamId}`);
      if (!data || data.error) { panel.style.display = 'none'; return; }
      panel.style.display = 'block';

      document.getElementById('dash-pool-size').textContent = data.pool_size || 0;
      document.getElementById('dash-categories').textContent = data.category_count || 0;
      const rm = data.router_metrics || {};
      document.getElementById('dash-routes').textContent = rm.total_routes || 0;
      document.getElementById('dash-assigns').textContent = rm.total_assigns || 0;
      document.getElementById('dash-top1').textContent = rm.avg_top1_score ? (rm.avg_top1_score * 100).toFixed(1) + '%' : '—';
      document.getElementById('dash-latency').textContent = rm.avg_latency_ms ? rm.avg_latency_ms.toFixed(0) + 'ms' : '—';
      document.getElementById('dash-success').textContent = rm.success_rate ? (rm.success_rate * 100).toFixed(0) + '%' : '—';
      const fb = data.feedback || {};
      document.getElementById('dash-avg-rating').textContent = fb.avg_rating ? fb.avg_rating.toFixed(1) + '⭐' : '—';

      // Category bar chart
      const catDist = data.category_distribution || {};
      const maxCat = Math.max(...Object.values(catDist), 1);
      const barsEl = document.getElementById('dash-category-bars');
      barsEl.innerHTML = Object.entries(catDist).slice(0, 6).map(([cat, count]) => `
        <div style="display:flex;align-items:center;gap:6px;margin:2px 0">
          <span style="font-size:9px;color:oklch(0.55 0.02 110);width:50px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${cat}</span>
          <div style="flex:1;height:8px;background:oklch(0.2 0.01 110);border-radius:4px;overflow:hidden">
            <div style="height:100%;width:${(count/maxCat*100).toFixed(0)}%;background:oklch(0.55 0.10 145);border-radius:4px;transition:width .3s"></div>
          </div>
          <span style="font-size:9px;color:oklch(0.5 0.02 110);width:16px">${count}</span>
        </div>
      `).join('');
    } catch(e) { panel.style.display = 'none'; }
  }

  // Update the 3D humanFigure to represent the selected agent
  function updateAgentFigure3D(name, hexColor) {
    if (!humanFigure) return;
    // Remove old figure, create new one
    const pos = humanFigure.position.clone();
    const visible = humanFigure.visible;
    scene.remove(humanFigure);
    // Dispose old geometry/materials
    humanFigure.traverse(child => {
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (child.material.map) child.material.map.dispose();
        child.material.dispose();
      }
    });
    // Parse color
    let colorHex = 0xD4A574;
    if (hexColor) {
      if (hexColor.startsWith('#')) colorHex = parseInt(hexColor.slice(1), 16);
      else if (typeof hexColor === 'number') colorHex = hexColor;
    }
    humanFigure = createAgentFigure(name, colorHex);
    humanFigure.position.copy(pos);
    humanFigure.visible = visible;
    scene.add(humanFigure);
  }

  // Pipeline step animation
  function setPipelineStep(step, timingMs) {
    const steps = document.querySelectorAll('#router-pipeline .rp-step');
    const connectors = document.querySelectorAll('#router-pipeline .rp-connector');
    const order = ['retrieve','rerank','assign'];
    const idx = order.indexOf(step);
    steps.forEach((s, i) => {
      s.classList.remove('active','done');
      if (i < idx) s.classList.add('done');
      else if (i === idx) {
        s.classList.add('active');
        if (timingMs !== undefined) {
          const t = s.querySelector('.rp-timing');
          if (t) t.textContent = timingMs < 1 ? `${(timingMs*1000).toFixed(0)}μs` : `${timingMs.toFixed(1)}ms`;
        }
      }
    });
    connectors.forEach((c, i) => {
      c.classList.remove('flowing','done');
      if (i < idx) c.classList.add('done');
      else if (i === idx - 1 || i === idx) c.classList.add('flowing');
    });
  }

  function setPipelineStepTiming(step, ms) {
    const el = document.querySelector(`#router-pipeline .rp-step[data-rp="${step}"] .rp-timing`);
    if (el) el.textContent = ms < 1 ? `${(ms*1000).toFixed(0)}μs` : `${ms.toFixed(1)}ms`;
  }

  function clearPipelineTimings() {
    document.querySelectorAll('#router-pipeline .rp-timing').forEach(t => t.textContent = '');
    document.querySelectorAll('#router-pipeline .rp-connector').forEach(c => c.classList.remove('flowing','done'));
  }

  // Add log entry
  function addRouterLog(type, text) {
    const log = document.getElementById('router-log');
    const now = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    const div = document.createElement('div');
    div.className = `rlog ${type}`;
    div.innerHTML = `${text}<div class="rlog-time">${now}</div>`;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }

  // Route
  window._executeRoute = async function() {
    const query = document.getElementById('router-query-input').value.trim();
    if (!query) return;
    const topK = parseInt(document.getElementById('router-topk').value) || 5;

    addRouterLog('sys', `🔍 路由查询: "${query}" (top-${topK})`);
    clearPipelineTimings();
    setPipelineStep('retrieve');

    try {
      const resp = await _af_sk('/api/v1/skill-router/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, team_id: currentTeamId || 'default', agent_id: selectedAgentId, top_k: topK, mode: 'assign' })
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      setPipelineStep('rerank', data.stage1_ms);
      if (data.stage1_ms) setPipelineStepTiming('retrieve', data.stage1_ms);
      await new Promise(r => setTimeout(r, 300));

      routerResults = data.results || [];
      routerSelectedSkills.clear();
      renderRouterResults(routerResults);
      visualizeRoutedSkills(routerResults);

      if (data.stage2_ms) setPipelineStepTiming('rerank', data.stage2_ms);
      setPipelineStep('assign', data.stage2_ms);
      const s1 = data.stage1_ms ? `S1:${data.stage1_ms}ms` : '';
      const s2 = data.stage2_ms ? `S2:${data.stage2_ms}ms` : '';
      const pool = data.pool_size ? `pool:${data.pool_size}` : '';
      addRouterLog('route', `✅ 检索到 ${routerResults.length} 项匹配技能 (${data.duration_ms || '?'}ms ${s1} ${s2} ${pool})`);
      if (routerResults.length > 0) {
        const top = routerResults[0];
        addRouterLog('route', `🏆 最佳匹配: <b>${top.name}</b> (分数: ${(top.score * 100).toFixed(1)}%)`);
      }
    } catch(e) {
      addRouterLog('sys', `❌ 路由失败: ${e.message}`);
      setPipelineStep('retrieve');
    }
  };

  // Runtime simulation — FULL end-to-end demo (route → select all → assign → animate)
  window._executeRuntimeSim = async function() {
    const queries = [
      '需要快速分析数据异常并生成报告',
      '客户沟通与情绪管理',
      '代码审查和质量把控',
      '跨团队项目协调'
    ];
    const q = queries[Math.floor(Math.random() * queries.length)];
    document.getElementById('router-query-input').value = q;
    addRouterLog('sys', `⚡ 运行时模拟: ${q}`);
    await window._executeRoute();

    // Auto-select top 3 results after a short delay for visual effect
    await new Promise(r => setTimeout(r, 800));
    const items = document.querySelectorAll('#rresults .rr-item');
    const autoSelectCount = Math.min(3, items.length);
    for (let i = 0; i < autoSelectCount; i++) {
      items[i].click(); // triggers _toggleRouterResult
    }
    addRouterLog('sys', `🎯 自动选择 ${autoSelectCount} 项最佳匹配`);

    // Auto-assign after another delay
    await new Promise(r => setTimeout(r, 600));
    window._executeAssign();
  };

  // Render results
  function renderRouterResults(results) {
    const container = document.getElementById('rresults');
    const header = document.getElementById('rresults-header');
    const stats = document.getElementById('rr-stats');

    header.style.display = 'flex';
    stats.textContent = `${results.length} results`;

    container.innerHTML = results.map((r, i) => {
      const rs = r.retrieval_score != null ? r.retrieval_score : r.score;
      const rk = r.rerank_score != null ? r.rerank_score : r.score;
      const reasonTag = (t) => {
        const lo = t.toLowerCase();
        let reason = 'semantic';
        if (lo.includes('name') || lo.includes('名称')) reason = 'name';
        else if (lo.includes('desc') || lo.includes('描述')) reason = 'desc';
        else if (lo.includes('categ') || lo.includes('类别')) reason = 'category';
        return `<span class="rr-tag" data-reason="${reason}">${t}</span>`;
      };
      return `
      <div class="rr-item" data-idx="${i}" onclick="window._toggleRouterResult(this, ${i})">
        <span class="rr-check">✓</span>
        <span class="rr-icon">${r.icon || '⚡'}</span>
        <div class="rr-body">
          <div class="rr-name">${r.name}</div>
          <div class="rr-desc">${r.description || r.match_reasons?.join(', ') || ''}</div>
          <div class="rr-tags">${(r.match_reasons || []).slice(0, 3).map(t => reasonTag(t)).join('')}</div>
        </div>
        <div class="rr-scores">
          <div class="rr-score-row"><span class="rr-score-label">R1</span><div class="rr-score-bar"><div class="rr-score-fill retrieve" style="width:${(rs*100).toFixed(0)}%"></div></div><span class="rr-score-val">${(rs*100).toFixed(0)}</span></div>
          <div class="rr-score-row"><span class="rr-score-label">R2</span><div class="rr-score-bar"><div class="rr-score-fill rerank" style="width:${(rk*100).toFixed(0)}%"></div></div><span class="rr-score-val">${(rk*100).toFixed(0)}</span></div>
        </div>
      </div>`;
    }).join('');
    updateAssignBar();
  }

  // Visualize routed skills in 3D scene — orbit around humanFigure
  function visualizeRoutedSkills(results) {
    // Clear existing skill nodes and rebuild with routed skills
    while (extractionGroup.children.length > 0) {
      const child = extractionGroup.children[0];
      if (child.geometry) child.geometry.dispose();
      if (child.material) { if (child.material.map) child.material.map.dispose(); child.material.dispose(); }
      extractionGroup.remove(child);
    }
    skillNodes.length = 0;

    if (!results.length) return;

    // Spawn routed skills as orbit nodes around the figure
    const radius = 3.5;
    results.forEach((r, i) => {
      const angle = (i / results.length) * Math.PI * 2;
      const skill = {
        skill_id: r.skill_id || r.name,
        name: r.name,
        icon: r.icon || '⚡',
        category: r.category || 'general',
        description: r.description || '',
        lifecycle_stage: 'published',
        score: r.score,
        _routed: true,
      };
      spawnSkillNodeAnimated(skill);
      // Position the last spawned node in orbit
      const node = skillNodes[skillNodes.length - 1];
      if (node) {
        const y = 1.5 + Math.sin(i * 0.7) * 0.5;
        node.position.set(
          Math.cos(angle) * radius,
          y,
          Math.sin(angle) * radius
        );
        // IMPORTANT: Cancel old flat lifecycle animation — orbit nodes appear upright immediately
        node.userData._animating = false;
        node.rotation.x = 0;
        node.scale.set(1, 1, 1);
        node.material.opacity = node.userData._targetOpacity || 0.8;
        // Glow ring also upright and visible immediately
        if (node.userData._glowRing) {
          node.userData._glowRing.position.copy(node.position);
          node.userData._glowRing.rotation.x = 0;
          node.userData._glowRing.scale.set(1, 1, 1);
          node.userData._glowRing.material.opacity = node.userData._glowTargetOpacity || 0.25;
        }
        // Color by score (higher = more cyan, lower = more gray)
        if (node.material) {
          const hue = 0.48 + r.score * 0.12; // cyan range
          node.material.color.setHSL(hue, 0.6, 0.4 + r.score * 0.2);
          node.material.opacity = 0.5 + r.score * 0.5;
        }
        // Store orbit data for animation
        node.userData._orbit = { angle, radius, speed: 0.15 + i * 0.02, baseY: y };
        // Sync label position to orbit start
        if (node.userData._label) {
          node.userData._label.position.set(node.position.x, node.position.y + 0.8, node.position.z);
        }
      }
    });
  }

  window._toggleRouterResult = function(el, idx) {
    const skillId = routerResults[idx]?.skill_id || routerResults[idx]?.name;
    if (routerSelectedSkills.has(skillId)) {
      routerSelectedSkills.delete(skillId);
      el.classList.remove('sel');
    } else {
      routerSelectedSkills.add(skillId);
      el.classList.add('sel');
    }
    updateAssignBar();
  };

  function updateAssignBar() {
    const bar = document.getElementById('rassign-bar');
    const count = document.getElementById('rassign-count');
    const btn = bar.querySelector('.btn-assign-go');
    // Always visible in router mode
    bar.classList.add('always-show');
    if (routerSelectedSkills.size > 0) {
      count.textContent = `已选 ${routerSelectedSkills.size} 项`;
      btn.disabled = false;
    } else {
      count.textContent = '点击上方结果选择技能';
      btn.disabled = true;
    }
  }

  // ── Closed-loop: Post-approval injection suggestion ──
  async function _showInjectionSuggestion(skillId, skillName) {
    try {
      const result = await routerApi('/suggest', {
        method: 'POST',
        body: JSON.stringify({ team_id: currentTeamId, skill_id: skillId, top_k: 3 }),
      });
      if (!result || result.error || !result.suggestions || result.suggestions.length === 0) return;

      const suggestions = result.suggestions.filter(s => !s.already_has && s.affinity > 0.1);
      if (suggestions.length === 0) return;

      // Build suggestion toast with inject buttons
      const top = suggestions[0];
      const othersHtml = suggestions.slice(1).map(s =>
        `<span class="suggest-alt" data-agent="${s.agent_id}" data-skill="${skillId}" onclick="_quickInject('${s.agent_id}','${skillId}')" title="${s.match_reasons.join(', ')}">${s.agent_name} (${Math.round(s.affinity * 100)}%)</span>`
      ).join(' ');

      const html = `
        <div class="injection-suggest" id="injection-suggest-${skillId}">
          <div style="font-size:11px;color:oklch(0.65 0.02 110);margin-bottom:6px">
            ◎ 智能赋予建议 — 「${skillName}」
          </div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
            <button class="btn btn-approve" onclick="_quickInject('${top.agent_id}','${skillId}')" style="font-size:11px;padding:4px 12px;background:oklch(0.55 0.12 145/.2);border-color:oklch(0.55 0.12 145/.4);color:oklch(0.8 0.08 145)">
              ▷ 注入 → ${top.agent_name} <span style="opacity:.6">(${Math.round(top.affinity * 100)}% 匹配)</span>
            </button>
            <span style="font-size:10px;color:oklch(0.45 0.01 110)">${top.match_reasons[0] || ''}</span>
          </div>
          ${othersHtml ? `<div style="font-size:10px;color:oklch(0.5 0.01 110)">其他: ${othersHtml}</div>` : ''}
          <button onclick="this.parentElement.remove()" style="position:absolute;top:4px;right:6px;background:none;border:none;color:oklch(0.5 0.01 110);cursor:pointer;font-size:12px">✕</button>
        </div>
      `;
      // Insert into message log
      addMessage('system', html, true);
    } catch (e) {
      console.warn('Injection suggestion failed:', e);
    }
  }

  window._quickInject = async function(agentId, skillId) {
    const result = await routerApi('/assign', {
      method: 'POST',
      body: JSON.stringify({ team_id: currentTeamId, agent_id: agentId, skill_ids: [skillId] }),
    });
    if (result && result.status === 'ok') {
      showToast(`▷ 已注入`);
      addMessage('system', `▷ 技能已自动注入到「${agentId}」`);
      // Remove suggestion card
      const card = document.getElementById(`injection-suggest-${skillId}`);
      if (card) card.remove();
      // Trigger animation if in router mode
      if (typeof animateSkillsToHead === 'function' && currentPageMode === 'router') {
        const targets = skillNodes.filter(n => n.userData?.skill_id === skillId);
        if (targets.length > 0) animateSkillsToHead(targets);
      }
    }
  };

  // ── Feedback: Rate + Revoke ──
  window._rateStar = async function(skillId, rating) {
    const agentId = document.querySelector('#rassign-bar')?.closest('.rrightpanel')?.querySelector('[data-agent-id].active')?.dataset?.agentId
      || routerSelectedAgent || '';
    const result = await routerApi('/feedback', {
      method: 'POST',
      body: JSON.stringify({ team_id: currentTeamId, agent_id: agentId, skill_id: skillId, action: 'rate', rating }),
    });
    if (result && result.status === 'ok') {
      // Update star display
      const stars = document.querySelectorAll(`.tag-stars[data-skill="${skillId}"] .star`);
      stars.forEach((s, i) => { s.textContent = i < rating ? '★' : '☆'; s.classList.toggle('filled', i < rating); });
      showToast(`⭐ 评分 ${rating}/5`);
    }
  };

  window._revokeSkill = async function(skillId) {
    const agentId = routerSelectedAgent || '';
    const result = await routerApi('/feedback', {
      method: 'POST',
      body: JSON.stringify({ team_id: currentTeamId, agent_id: agentId, skill_id: skillId, action: 'revoke' }),
    });
    if (result && result.status === 'ok') {
      // Remove tag from UI
      const tag = document.querySelector(`.rassigned-tag[data-skill-id="${skillId}"]`);
      if (tag) { tag.style.opacity = '0'; setTimeout(() => tag.remove(), 300); }
      showToast('🗑️ 已撤销注入');
      addRouterLog('feedback', `🗑️ 技能 ${skillId} 已从智能体撤销`);
    }
  };

  // Assign
  window._executeAssign = async function() {
    if (routerSelectedSkills.size === 0) return;
    const skillIds = [...routerSelectedSkills];

    addRouterLog('assign', `⚡ 注入 ${skillIds.length} 项技能 → ${selectedAgentId}`);

    try {
      const resp = await _af_sk('/api/v1/skill-router/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: selectedAgentId, team_id: currentTeamId || 'default', skill_ids: skillIds })
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      // Mark assigned (injected) in UI
      document.querySelectorAll('#rresults .rr-item.sel').forEach(el => {
        el.classList.remove('sel');
        el.classList.add('assigned');
        el.querySelector('.rr-check').textContent = '▷';
      });

      // Show injected tags with feedback controls
      const tagsEl = document.getElementById('rassigned-tags');
      const section = document.getElementById('rassigned-section');
      const assigned = routerResults.filter(r => skillIds.includes(r.skill_id || r.name));
      tagsEl.innerHTML += assigned.map(r => `
        <span class="rassigned-tag" data-skill-id="${r.skill_id}">
          ${r.icon || '⚡'} ${r.name}
          <span class="tag-feedback">
            <span class="tag-stars" data-skill="${r.skill_id}">${[1,2,3,4,5].map(n => `<span class="star" data-n="${n}" onclick="_rateStar('${r.skill_id}',${n})">☆</span>`).join('')}</span>
            <span class="tag-revoke" onclick="_revokeSkill('${r.skill_id}')" title="撤销注入">✕</span>
          </span>
        </span>
      `).join('');
      section.classList.add('visible');

      routerSelectedSkills.clear();
      updateAssignBar();

      addRouterLog('assign', `✅ 注入完成！${data.assigned_count || skillIds.length} 项技能已融入智能体`);

      // Show inject_prompt in log
      if (data.inject_prompt) {
        addRouterLog('inject', `📋 Inject Prompt 已生成 (${data.inject_prompt.length} chars)`);
        addRouterLog('inject', `<pre style="font-size:9px;max-height:80px;overflow:auto;background:#1a1f25;padding:6px;border-radius:4px;margin-top:4px;white-space:pre-wrap">${data.inject_prompt.slice(0, 300)}${data.inject_prompt.length > 300 ? '...' : ''}</pre>`);
      }

      // 3D animation — skill nodes fly to agent head and merge (injection)
      animateSkillsToHead(skillIds, assigned.length);
    } catch(e) {
      addRouterLog('sys', `❌ 注入失败: ${e.message}`);
    }
  };

  function animateSkillsToHead(skillIds, count) {
    if (!humanFigure) { console.warn('animateSkillsToHead: no humanFigure'); return; }

    // Force world matrix update to get accurate head position
    humanFigure.updateMatrixWorld(true);
    
    // Get head world position — with explicit fallback
    const headWorldPos = new THREE.Vector3();
    const headObj = humanFigure.userData.head;
    if (headObj) {
      headObj.getWorldPosition(headWorldPos);
    } else {
      // Fallback: humanFigure center + head offset (y=2.0)
      humanFigure.getWorldPosition(headWorldPos);
      headWorldPos.y += 2.0;
    }
    console.log('animateSkillsToHead: headWorldPos =', headWorldPos.x.toFixed(2), headWorldPos.y.toFixed(2), headWorldPos.z.toFixed(2));

    // Find matching skill nodes — try by skill_id first, fallback to ALL orbit nodes
    let targets = skillNodes.filter(n => {
      const sid = n.userData.skill?.skill_id || n.userData.skill?.name || '';
      return skillIds.includes(sid);
    });
    // Fallback: if no ID match, grab nodes that are currently in orbit
    if (!targets.length) {
      targets = skillNodes.filter(n => n.userData._orbit);
      console.warn('animateSkillsToHead: ID match failed, using', targets.length, 'orbit nodes');
    }
    if (!targets.length) { console.warn('animateSkillsToHead: no targets found'); return; }
    console.log('animateSkillsToHead: animating', targets.length, 'nodes to head');

    // Disable orbit animation for flying nodes
    targets.forEach(node => { node.userData._orbit = null; node.userData._flying = true; });

    const duration = 2200; // ms total — slower for drama
    const startTime = performance.now();

    // Store start state — use CURRENT node world position (orbit position is accurate)
    const ringData = targets.map(node => {
      const glow = node.userData._glowRing;
      // Use node.position (local to extractionGroup) as the true orbit position
      const pos = node.position.clone();
      // Sync glow to current orbit position if not already
      if (glow) glow.position.copy(pos);
      return {
        node,
        glow,
        startPos: pos,
        startRotX: 0, // orbit nodes are already upright (rotation.x=0)
        startRotY: glow ? glow.rotation.y : 0,
        startRotZ: glow ? glow.rotation.z : 0,
      };
    });

    function flyFrame(now) {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / duration, 1);

      ringData.forEach(({ node, glow, startPos, startRotX, startRotY, startRotZ }, i) => {
        if (!glow) return;

        // ═══ Phase 1 (0~20%): STAND UP — ring rotates from flat to vertical facing camera ═══
        if (t < 0.20) {
          const p = t / 0.20;
          const ease = p * p * (3 - 2 * p); // smoothstep
          
          // Rotate from flat (XZ plane, rotation.x=-PI/2) to vertical (XY plane, rotation.x=0)
          // Plus rotate Y to face the agent head
          const faceAngle = Math.atan2(headWorldPos.x - startPos.x, headWorldPos.z - startPos.z);
          glow.rotation.x = startRotX + (0 - startRotX) * ease;
          glow.rotation.y = startRotY + (faceAngle - startRotY) * ease;
          glow.rotation.z = ease * 0.4; // dramatic tilt
          
          // Scale pulse — grows bigger as it stands
          glow.scale.setScalar(1.0 + ease * 0.5);
          
          // Brighten significantly
          if (glow.material) {
            glow.material.opacity = 0.3 + ease * 0.7;
            glow.material.color.setHSL(0.5, 0.8, 0.4 + ease * 0.3); // cyan glow
          }
          
          // Position stays at startPos
          glow.position.copy(startPos);

        // ═══ Phase 2 (20~40%): RISE + SPIN — ring floats up while spinning ═══
        } else if (t < 0.40) {
          const p = (t - 0.20) / 0.20;
          const ease = p * p * (3 - 2 * p);
          
          // Vertical ring, spinning on Y axis
          glow.rotation.x = Math.sin(p * Math.PI * 2) * 0.2; // wobble
          glow.rotation.y += 0.12; // continuous spin
          glow.rotation.z = 0.4 * (1 - p); // settle tilt
          
          // Rise up 5 units
          glow.position.set(
            startPos.x,
            startPos.y + ease * 5.0,
            startPos.z
          );
          
          // Scale settles
          glow.scale.setScalar(1.5 - ease * 0.3);
          if (glow.material) glow.material.opacity = 1.0;

        // ═══ Phase 3 (40~100%): FLY TO HEAD — arc trajectory with spin ═══
        } else {
          const p = (t - 0.40) / 0.60;
          const ease = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; // easeInOutQuad
          
          // Start position = risen position
          const riseEnd = new THREE.Vector3(startPos.x, startPos.y + 5.0, startPos.z);
          
          // Lerp toward head with arc
          const pos = riseEnd.clone().lerp(headWorldPos, ease);
          // Add arc height in the middle
          const arcHeight = Math.sin(p * Math.PI) * 2.5;
          pos.y += arcHeight * (1 - ease * 0.5);
          glow.position.copy(pos);
          
          // Continuous spin during flight
          glow.rotation.x = Math.sin(p * Math.PI * 3) * 0.3;
          glow.rotation.y += 0.1;
          glow.rotation.z += 0.07;
          
          // Shrink as approaching head
          const scale = 1.2 * (1 - ease * 0.7);
          glow.scale.setScalar(Math.max(scale, 0.2));
          
          // Fade slightly near end
          if (glow.material) {
            glow.material.opacity = 1.0 - ease * 0.6;
            // Color shifts to white near head
            const hue = 0.5 * (1 - ease);
            glow.material.color.setHSL(hue, 0.8 * (1 - ease), 0.5 + ease * 0.4);
          }
        }

        // Fade out the main crystal mesh
        if (node.material) {
          const fadeT = Math.min(t / 0.4, 1);
          node.material.opacity = (1 - fadeT) * (node.userData._targetOpacity || 0.8);
          node.scale.setScalar(1 - fadeT * 0.7);
        }
        // Fade out and move label with glow ring
        if (node.userData._label) {
          const lbl = node.userData._label;
          lbl.position.set(glow.position.x, glow.position.y + 0.6, glow.position.z);
          lbl.material.opacity = Math.max(0, 1 - t * 2); // fade out in first half
        }
      });

      if (t < 1) {
        requestAnimationFrame(flyFrame);
      } else {
        // Merge flash
        flashAgentHead();
        // Cleanup
        targets.forEach(node => {
          const glow = node.userData._glowRing;
          if (glow) { extractionGroup.remove(glow); if (glow.geometry) glow.geometry.dispose(); if (glow.material) glow.material.dispose(); }
          const lbl = node.userData._label;
          if (lbl) { extractionGroup.remove(lbl); if (lbl.material) { if (lbl.material.map) lbl.material.map.dispose(); lbl.material.dispose(); } }
          extractionGroup.remove(node);
          if (node.geometry) node.geometry.dispose();
          if (node.material) node.material.dispose();
        });
        // Remove from skillNodes array
        skillIds.forEach(sid => {
          const idx = skillNodes.findIndex(n => (n.userData.skill?.skill_id || n.userData.skill?.name) === sid);
          if (idx >= 0) skillNodes.splice(idx, 1);
        });
        // Add persistent injected rings
        addInjectedRings(skillIds);
      }
    }
    requestAnimationFrame(flyFrame);
  }

  // Persistent mini-rings around agent head representing injected skills
  function addInjectedRings(skillIds) {
    if (!humanFigure) return;
    if (!humanFigure.userData._injectedRings) humanFigure.userData._injectedRings = [];
    const existing = humanFigure.userData._injectedRings.length;
    const headY = humanFigure.userData.head ? humanFigure.userData.head.position.y : 2.0;

    skillIds.forEach((sid, i) => {
      const idx = existing + i;
      const ringR = 0.38 + idx * 0.08;
      const color = new THREE.Color().setHSL(0.48 + idx * 0.07, 0.7, 0.55);
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(ringR, 0.012, 8, 32),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.6 })
      );
      ring.position.y = headY;
      ring.rotation.x = Math.PI / 2 + idx * 0.25;
      ring.rotation.z = idx * 0.4;
      ring.userData._injectedRing = { speed: 0.3 + idx * 0.1, axis: idx % 2 === 0 ? 'y' : 'z' };
      humanFigure.add(ring);
      humanFigure.userData._injectedRings.push(ring);
    });
  }

  function flashAgentHead() {
    if (!humanFigure) return;
    const head = humanFigure.userData.head;
    if (!head || !head.material) return;
    // Bright flash
    const origColor = head.material.color.clone();
    const origEmissive = head.material.emissive ? head.material.emissive.clone() : null;
    head.material.color.setHex(0xffffff);
    if (head.material.emissive) head.material.emissive.setHex(0x88ffcc);

    // Expand ring briefly
    const origScale = head.scale.clone();
    head.scale.setScalar(1.6);

    // Glow ring flash
    const glowRing = humanFigure.userData.glowRing;
    if (glowRing && glowRing.material) glowRing.material.opacity = 0.8;

    // Fade back
    let frame = 0;
    const fadeBack = () => {
      frame++;
      const t = frame / 30;
      if (t >= 1) {
        head.material.color.copy(origColor);
        if (origEmissive && head.material.emissive) head.material.emissive.copy(origEmissive);
        head.scale.copy(origScale);
        if (glowRing && glowRing.material) glowRing.material.opacity = 0.22;
        return;
      }
      head.scale.setScalar(1.6 - t * 0.6);
      if (glowRing && glowRing.material) glowRing.material.opacity = 0.8 - t * 0.58;
      requestAnimationFrame(fadeBack);
    };
    requestAnimationFrame(fadeBack);
  }
})();

// ── Init ────────────────────────────────────────────────────────
initScene();
loadTeams();
