/**
 * AgentsGroup2026 — SECS Sandbox Twin Dashboard
 * 重设计: 四层 Pipeline + I/O 镜像 + 数据驱动 Agent 协作图
 * Agent = 演员, Skill = 道具, Sandbox = 舞台, 四层 = 导演流程
 */
(function () {
  'use strict';

  const API = '/api/v1/sandbox';

  // CSRF helper for state-changing requests
  var _csrfTk='',_csrfPr=null;
  function _csrf(){if(_csrfTk)return Promise.resolve(_csrfTk);if(_csrfPr)return _csrfPr;_csrfPr=fetch('/api/v1/auth/csrf-token').then(function(r){return r.json()}).then(function(d){_csrfTk=d.csrf_token||'';return _csrfTk}).catch(function(){_csrfPr=null;return''});return _csrfPr}
  _csrf();
  async function _af(url,opts){var m=(opts&&opts.method||'GET').toUpperCase();if(m==='POST'||m==='PUT'||m==='DELETE'||m==='PATCH'){await _csrf();if(_csrfTk){opts=opts||{};opts.headers=opts.headers||{};opts.headers['x-csrf-token']=_csrfTk}}return (window._agFetch||fetch)(url,opts)}

  let currentSessionId = null;
  let rewardHistory = [];
  let eventSource = null;
  let runtimeState = null;
  let simulationRunning = false;
  let sessionHistoryList = [];
  let refreshIntervalId = null;
  let currentLayer = 'L3'; // 流水线当前激活层

  // Agent 角色 + 固定位置 (3+2 分层: 决策层上, 执行层下, Coordinator 居中枢纽)
  const AGENT_ROLES = [
    { id: 'planner',     name: '规划',  en: 'Planner',     color: '#6BC47F',  gradId: 'node-grad-planner',     x: 200, y: 70,  r: 32, role: '决策' },
    { id: 'coordinator', name: '协调',  en: 'Coordinator', color: '#D4A44A', gradId: 'node-grad-coordinator', x: 400, y: 70,  r: 38, role: '枢纽', central: true },
    { id: 'critic',      name: '校验',  en: 'Critic',      color: '#E07070',  gradId: 'node-grad-critic',      x: 600, y: 70,  r: 32, role: '决策' },
    { id: 'retriever',   name: '检索',  en: 'Retriever',   color: '#6B9FD4',  gradId: 'node-grad-retriever',   x: 250, y: 280, r: 32, role: '执行' },
    { id: 'executor',    name: '执行',  en: 'Executor',    color: '#9B8EC4',  gradId: 'node-grad-executor',    x: 550, y: 280, r: 32, role: '执行' }
  ];
  // 协作图边集合 (a -> b) — 真实业务流: 上层决策 → 中央协调 → 下层执行 → Critic 反馈回环
  const COLLAB_EDGES = [
    ['planner', 'coordinator',     '指令'],
    ['coordinator', 'retriever',   '查询'],
    ['coordinator', 'executor',    '执行'],
    ['executor', 'coordinator',    '回报'],
    ['retriever', 'coordinator',   '素材'],
    ['coordinator', 'critic',      '审核'],
    ['critic', 'planner',          '修订'],
    ['executor', 'critic',         '产出']
  ];
  // 实时通信计数: edgeCounts['a->b'] = count
  let edgeCounts = {};
  let edgeConflicts = {}; // 'a->b' = true 表示冲突
  let collabBackendMessageTotal = 0;
  // 后端权威 role 映射: { agentId: 'planner' | 'coordinator' | ... }
  let currentRoleMap = {};
  // ── Helpers ──

  function esc(v) { return String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

  // ── Toast ──

  function showToast(msg, type) {
    type = type || 'info';
    var container = document.getElementById('toast-container');
    if (!container) return;
    var icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    var el = document.createElement('div');
    el.className = 'toast ' + type;
    el.innerHTML = '<span class="toast-icon">' + (icons[type] || '') + '</span><span class="toast-msg">' + esc(msg) + '</span>';
    container.appendChild(el);
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 3200);
  }

  // ── IO Tab 切换 ──

  function setupTabs(tabsId, contentPrefix) {
    var tabs = document.querySelectorAll('#' + tabsId + ' .io-tab');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var target = tab.getAttribute('data-tab');
        // 切换 tab 样式
        tabs.forEach(function (t) { t.classList.remove('io-tab--active'); });
        tab.classList.add('io-tab--active');
        // 切换内容
        tabs.forEach(function (t) {
          var t2 = t.getAttribute('data-tab');
          var c = document.getElementById(contentPrefix + '-' + t2);
          if (c) c.style.display = (t2 === target) ? '' : 'none';
        });
      });
    });
  }

  // ── Pipeline 联动 ──

  function setActiveLayer(layer) {
    currentLayer = layer;
    document.querySelectorAll('.pipeline-node').forEach(function (el) {
      var l = el.getAttribute('data-layer');
      el.classList.toggle('pipeline-node--active', l === layer);
    });
    // 标记运行状态指示器
    document.querySelectorAll('.pipeline-node__status').forEach(function (el) { el.classList.remove('active'); });
    var activeInd = document.getElementById('pipe-status-' + layer);
    if (activeInd) activeInd.classList.add('active');
  }

  function bindPipelineNodes() {
    document.querySelectorAll('.pipeline-node').forEach(function (el) {
      el.addEventListener('click', function () {
        var layer = el.getAttribute('data-layer');
        setActiveLayer(layer);
        // 联动：点击 L1 切到 Output tab 让 L1 详情; 点击 L2 切到 Output/sop; L3 切到 reward; L4 切到 critic
        if (layer === 'L1') {
          // 滚动到 L1 详情
          document.getElementById('agent-grid')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else if (layer === 'L2') {
          switchOutputTab('sop');
        } else if (layer === 'L3') {
          switchOutputTab('reward');
        } else if (layer === 'L4') {
          switchOutputTab('critic');
        }
        showToast('已聚焦: ' + (el.querySelector('.pipeline-node__name')?.textContent || layer), 'info');
      });
    });
  }

  function switchOutputTab(tab) {
    var tabEl = document.querySelector('#output-tabs .io-tab[data-tab="' + tab + '"]');
    if (tabEl) tabEl.click();
  }

// ── Agent 协作图 ──

function clearCollabLayers() {
  ['collab-edges', 'collab-edge-labels', 'collab-nodes', 'collab-labels', 'collab-particles'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = '';
  });
  // 清掉旧统计 (否则 reset 时 + 已有数据会叠加)
  edgeCounts = {};
  edgeConflicts = {};
}

function renderCollabGraph(roles) {
  // BUGFIX(协作图空白): 包防御层 — 渲染异常时不留空白，回退默认角色图并在 console 暴露根因
  try {
    _renderCollabGraphInner(roles);
  } catch (err) {
    console.error('[collab] 协作图渲染异常:', err, 'roles=', roles);
    if (roles !== AGENT_ROLES) {
      try { _renderCollabGraphInner(AGENT_ROLES); return; } catch (e2) {
        console.error('[collab] 默认角色回退也失败:', e2);
      }
    }
    var nodesEl = document.getElementById('collab-nodes');
    if (nodesEl && !nodesEl.childNodes.length) {
      nodesEl.innerHTML = '<text x="400" y="180" text-anchor="middle" fill="#E07070" font-size="13">协作图渲染失败: ' +
        String(err && err.message || err).replace(/</g, '&lt;').slice(0, 80) + ' (见 console)</text>';
    }
  }
}

function _renderCollabGraphInner(roles) {
  var svg = document.getElementById('collab-graph');
  if (!svg) return;
  clearCollabLayers();

  var ns = 'http://www.w3.org/2000/svg';
  var nodes = document.getElementById('collab-nodes');
  var labels = document.getElementById('collab-labels');
  var edges = document.getElementById('collab-edges');
  var edgeLabels = document.getElementById('collab-edge-labels');

  // 1) 画边
  COLLAB_EDGES.forEach(function (triple) {
    var fromId = triple[0], toId = triple[1], type = triple[2];
    var from = roles.find(function (a) { return a.id === fromId; });
    var to = roles.find(function (a) { return a.id === toId; });
    if (!from || !to) return;

    var line = document.createElementNS(ns, 'line');
    line.setAttribute('class', 'collab-edge');
    line.setAttribute('id', 'edge-' + fromId + '-' + toId);
    line.setAttribute('x1', from.x);
    line.setAttribute('y1', from.y);
    line.setAttribute('x2', to.x);
    line.setAttribute('y2', to.y);
    line.setAttribute('marker-end', 'url(#arrowhead-cyan)');
    edges.appendChild(line);

    var midX = (from.x + to.x) / 2;
    var midY = (from.y + to.y) / 2;
    var badgeId = 'badge-' + fromId + '-' + toId;

    var badge = document.createElementNS(ns, 'rect');
    badge.setAttribute('class', 'collab-edge-badge');
    badge.setAttribute('id', badgeId);
    badge.setAttribute('x', midX - 14);
    badge.setAttribute('y', midY - 9);
    badge.setAttribute('width', 28);
    badge.setAttribute('height', 18);
    badge.setAttribute('rx', 9);
    edgeLabels.appendChild(badge);

    var badgeText = document.createElementNS(ns, 'text');
    badgeText.setAttribute('class', 'collab-edge-label');
    badgeText.setAttribute('id', badgeId + '-num');
    badgeText.setAttribute('x', midX);
    badgeText.setAttribute('y', midY + 3);
    badgeText.textContent = '0';
    edgeLabels.appendChild(badgeText);

    var typeText = document.createElementNS(ns, 'text');
    typeText.setAttribute('class', 'collab-edge-type');
    typeText.setAttribute('x', midX);
    typeText.setAttribute('y', midY - 13);
    typeText.textContent = type;
    edgeLabels.appendChild(typeText);
  });

  // 2) 画节点
  roles.forEach(function (r) {
    var g = document.createElementNS(ns, 'g');
    g.setAttribute('class', 'collab-node-outer inactive');
    g.setAttribute('data-agent', r.id);
    g.setAttribute('transform', 'translate(' + r.x + ',' + r.y + ')');

    var halo = document.createElementNS(ns, 'circle');
    halo.setAttribute('class', 'node-halo');
    halo.setAttribute('r', r.r + 8);
    halo.setAttribute('fill', r.color);
    halo.setAttribute('opacity', 0);
    g.appendChild(halo);

    var bg = document.createElementNS(ns, 'circle');
    bg.setAttribute('r', r.r + 2);
    bg.setAttribute('fill', 'var(--bg)');
    g.appendChild(bg);

    var main = document.createElementNS(ns, 'circle');
    main.setAttribute('r', r.r);
    main.setAttribute('fill', 'url(#' + r.gradId + ')');
    main.setAttribute('class', 'node-main');
    g.appendChild(main);

    var gloss = document.createElementNS(ns, 'ellipse');
    gloss.setAttribute('cx', -r.r * 0.25);
    gloss.setAttribute('cy', -r.r * 0.35);
    gloss.setAttribute('rx', r.r * 0.45);
    gloss.setAttribute('ry', r.r * 0.22);
    gloss.setAttribute('fill', 'white');
    gloss.setAttribute('opacity', 0.35);
    g.appendChild(gloss);

    var ringR = r.r + 5;
    var circumference = 2 * Math.PI * ringR;
    var ring = document.createElementNS(ns, 'circle');
    ring.setAttribute('class', 'node-progress-ring');
    ring.setAttribute('id', 'ring-' + r.id);
    ring.setAttribute('r', ringR);
    ring.setAttribute('stroke', r.color);
    ring.setAttribute('stroke-dasharray', circumference);
    ring.setAttribute('stroke-dashoffset', circumference);
    ring.setAttribute('transform', 'rotate(-90)');
    ring.setAttribute('fill', 'none');
    g.appendChild(ring);

    nodes.appendChild(g);

    var t1 = document.createElementNS(ns, 'text');
    t1.setAttribute('class', 'collab-node-label');
    t1.setAttribute('x', r.x);
    t1.setAttribute('y', r.y + 4);
    t1.textContent = r.name;
    labels.appendChild(t1);

    var t2 = document.createElementNS(ns, 'text');
    t2.setAttribute('class', 'collab-node-role');
    t2.setAttribute('x', r.x);
    t2.setAttribute('y', r.y + 20);
    t2.textContent = r.en + ' · ' + r.role;
    labels.appendChild(t2);

    var tc = document.createElementNS(ns, 'text');
    tc.setAttribute('class', 'collab-node-count');
    tc.setAttribute('id', 'count-' + r.id);
    tc.setAttribute('x', r.x);
    tc.setAttribute('y', r.y + 34);
    tc.setAttribute('fill', r.color);
    tc.textContent = '0 msg';
    labels.appendChild(tc);
  });

  // 3) hover
  nodes.querySelectorAll('.collab-node-outer').forEach(function (g) {
    g.addEventListener('mouseenter', function () {
      var id = g.getAttribute('data-agent');
      document.querySelectorAll('.collab-edge').forEach(function (line) {
        var lid = line.id.replace('edge-', '');
        line.style.opacity = (lid.indexOf(id) >= 0) ? '1' : '0.08';
      });
      document.querySelectorAll('.collab-edge-badge').forEach(function (b) {
        var lid = b.id.replace('badge-', '');
        b.style.opacity = (lid.indexOf(id) >= 0) ? '1' : '0.2';
      });
      g.style.transform = 'translate(' + g.getAttribute('data-tx') + ',' + g.getAttribute('data-ty') + ') scale(1.08)';
    });
    g.addEventListener('mouseleave', function () {
      document.querySelectorAll('.collab-edge').forEach(function (line) { line.style.opacity = ''; });
      document.querySelectorAll('.collab-edge-badge').forEach(function (b) { b.style.opacity = ''; });
      g.style.transform = '';
    });
  });

  updateCollabMetrics();
  startParticleAnimation();
}

function initCollabGraph() {
  renderCollabGraph(AGENT_ROLES);
  // BUGFIX(协作图空白): 自愈钩子 — 每 5s 检查节点层是否被意外清空（演练中
  // rebuild 链路若中断会清空后未重画），为空则用当前角色映射重画
  if (!window._collabSelfHealTimer) {
    window._collabSelfHealTimer = setInterval(function () {
      var nodesEl = document.getElementById('collab-nodes');
      if (nodesEl && nodesEl.childNodes.length === 0) {
        console.warn('[collab] 检测到协作图为空，自愈重画');
        try {
          if (Object.keys(currentRoleMap).length) {
            rebuildCollabGraphFromRoles(currentRoleMap);
          } else {
            renderCollabGraph(AGENT_ROLES);
          }
        } catch (e) { console.error('[collab] 自愈失败:', e); }
      }
    }, 5000);
  }
}

window._collabGraphHealth = function () {
  return {
    nodes: document.querySelectorAll('#collab-nodes .collab-node-outer').length,
    edges: document.querySelectorAll('#collab-edges .collab-edge').length,
    total_messages: Number(document.getElementById('collab-msg-total')?.textContent || 0)
  };
};

function rebuildCollabGraphFromRoles(roleMap) {
  // roleMap: { agentId: 'planner' | 'coordinator' | ... }
  if (!roleMap || typeof roleMap !== 'object') return;
  var knownIds = AGENT_ROLES.map(function (r) { return r.id; });
  var used = new Set();
  // 把后端映射到默认坐标的 5 个槽位
  var rebuilt = AGENT_ROLES.map(function (r) {
    var foundAgent = null;
    Object.keys(roleMap).forEach(function (agentId) {
      if (used.has(agentId)) return;
      if (roleMap[agentId] === r.id) { foundAgent = agentId; }
    });
    if (foundAgent) used.add(foundAgent);
    return Object.assign({}, r, { boundAgent: foundAgent || null });
  });
  renderCollabGraph(rebuilt);
}

function ingestAgentRoles(roleMap) {
  if (!roleMap || typeof roleMap !== 'object') return;
  var changed = false;
  Object.keys(roleMap).forEach(function (agentId) {
    if (currentRoleMap[agentId] !== roleMap[agentId]) {
      currentRoleMap[agentId] = roleMap[agentId];
      changed = true;
    }
  });
  if (changed) {
    rebuildCollabGraphFromRoles(currentRoleMap);
  }
}

  // 沿激活边流动的粒子
  var particleAnimId = null;
  function startParticleAnimation() {
    if (particleAnimId) return;
    function tick() {
      animateParticles();
      particleAnimId = requestAnimationFrame(tick);
    }
    particleAnimId = requestAnimationFrame(tick);
  }

  function animateParticles() {
    var layer = document.getElementById('collab-particles');
    if (!layer) return;
    // 不重建粒子 — 用 transform 在已有粒子上平移
    var particles = layer.querySelectorAll('.collab-particle');
    particles.forEach(function (p) {
      var x = parseFloat(p.getAttribute('data-x') || '0');
      var y = parseFloat(p.getAttribute('data-y') || '0');
      var speed = parseFloat(p.getAttribute('data-speed') || '0.02');
      var t = parseFloat(p.getAttribute('data-t') || '0');
      t += speed;
      if (t > 1) t = 0;
      p.setAttribute('data-t', t);
      var fromId = p.getAttribute('data-from');
      var toId = p.getAttribute('data-to');
      var from = AGENT_ROLES.find(function (a) { return a.id === fromId; });
      var to = AGENT_ROLES.find(function (a) { return a.id === toId; });
      if (!from || !to) return;
      // 沿贝塞尔曲线插值 (轻微弧度)
      var cx = (from.x + to.x) / 2;
      var cy = (from.y + to.y) / 2 - 12;
      var oneMinusT = 1 - t;
      var px = oneMinusT * oneMinusT * from.x + 2 * oneMinusT * t * cx + t * t * to.x;
      var py = oneMinusT * oneMinusT * from.y + 2 * oneMinusT * t * cy + t * t * to.y;
      p.setAttribute('cx', px);
      p.setAttribute('cy', py);
      // 透明度淡入淡出
      p.setAttribute('opacity', Math.sin(t * Math.PI) * 0.9 + 0.1);
    });
  }

  // 根据仿真日志驱动协作图
  function recordCollabEvent(data) {
    if (!data || !data.from || !data.to) return;
    var key = data.from + '->' + data.to;
    edgeCounts[key] = (edgeCounts[key] || 0) + 1;
    if (data.conflict) edgeConflicts[key] = true;

    // 激活节点
    var fromG = document.querySelector('.collab-node-outer[data-agent="' + data.from + '"]');
    var toG = document.querySelector('.collab-node-outer[data-agent="' + data.to + '"]');
    if (fromG) fromG.classList.remove('inactive');
    if (toG) toG.classList.remove('inactive');
    if (fromG && !fromG.classList.contains('active')) fromG.classList.add('active');
    if (toG && !toG.classList.contains('active')) toG.classList.add('active');

    // 更新边样式 + msg 徽章
    var line = document.getElementById('edge-' + data.from + '-' + data.to);
    var badge = document.getElementById('badge-' + data.from + '-' + data.to);
    var badgeNum = document.getElementById('badge-' + data.from + '-' + data.to + '-num');
    var count = edgeCounts[key];

    if (line) {
      line.classList.add('active');
      if (data.conflict) {
        line.classList.add('conflict');
        line.setAttribute('marker-end', 'url(#arrowhead-red)');
      } else if (count >= 5) {
        line.classList.add('heat');
        line.setAttribute('marker-end', 'url(#arrowhead-amber)');
      }
      line.setAttribute('stroke-width', Math.min(4, 1 + count * 0.2));
    }
    if (badge) {
      badge.classList.toggle('heat', count >= 5 && !data.conflict);
      badge.classList.toggle('conflict', !!data.conflict);
    }
    if (badgeNum) {
      badgeNum.textContent = count;
      badgeNum.classList.toggle('heat', count >= 5 && !data.conflict);
      badgeNum.classList.toggle('conflict', !!data.conflict);
    }

    // 更新节点 msg 计数 + 进度环
    updateNodeCount(data.from);
    updateNodeCount(data.to);

    // 添加流动粒子 (每条活跃边最多 3 个粒子)
    if (count % 2 === 0) { // 隔次添加,避免过密
      addParticle(data.from, data.to);
    }

    updateCollabMetrics();
  }

  function consumeCollabStepMessages(data) {
    var stepMessages = Number(data && data.messages_count);
    if (!Number.isFinite(stepMessages) || stepMessages <= 0) return;
    collabBackendMessageTotal += stepMessages;
    updateCollabMetrics();
  }

  function updateNodeCount(agentId) {
    var total = 0;
    for (var k in edgeCounts) {
      var pair = k.split('->');
      if (pair[0] === agentId || pair[1] === agentId) total += edgeCounts[k];
    }
    var countEl = document.getElementById('count-' + agentId);
    if (countEl) countEl.textContent = total + ' msg';

    // 进度环 — 假设 20 msg 满
    var ring = document.getElementById('ring-' + agentId);
    if (ring) {
      var r = AGENT_ROLES.find(function (a) { return a.id === agentId; });
      var circumference = 2 * Math.PI * (r.r + 5);
      var ratio = Math.min(1, total / 20);
      ring.setAttribute('stroke-dashoffset', circumference * (1 - ratio));
    }
  }

  function addParticle(fromId, toId) {
    var layer = document.getElementById('collab-particles');
    if (!layer) return;
    var ns = 'http://www.w3.org/2000/svg';
    var p = document.createElementNS(ns, 'circle');
    p.setAttribute('class', 'collab-particle');
    p.setAttribute('r', 3);
    p.setAttribute('data-from', fromId);
    p.setAttribute('data-to', toId);
    p.setAttribute('data-t', Math.random()); // 错开起始位置
    p.setAttribute('data-speed', 0.012 + Math.random() * 0.012);
    layer.appendChild(p);
    // 限制粒子数
    var all = layer.querySelectorAll('.collab-particle');
    if (all.length > 30) {
      layer.removeChild(all[0]);
    }
  }

  function updateCollabMetrics() {
    var edgeTotal = 0; var conflicts = 0; var active = 0;
    for (var k in edgeCounts) edgeTotal += edgeCounts[k];
    var total = Math.max(edgeTotal, collabBackendMessageTotal);
    for (var k2 in edgeConflicts) conflicts++;
    for (var k3 in edgeCounts) {
      if (edgeCounts[k3] > 0) active++;
    }
    var totalEl = document.getElementById('collab-msg-total');
    var densityEl = document.getElementById('collab-density');
    var conflictEl = document.getElementById('collab-conflict');
    if (totalEl) totalEl.textContent = total;
    if (densityEl) densityEl.textContent = active + '/' + COLLAB_EDGES.length;
    if (conflictEl) conflictEl.textContent = conflicts;
  }

  function resetCollabGraph() {
    edgeCounts = {}; edgeConflicts = {};
    collabBackendMessageTotal = 0;
    document.querySelectorAll('.collab-edge').forEach(function (line) {
      line.classList.remove('active', 'conflict', 'heat');
      line.setAttribute('stroke-width', 1);
      line.setAttribute('marker-end', 'url(#arrowhead-cyan)');
    });
    document.querySelectorAll('.collab-edge-badge').forEach(function (b) {
      b.classList.remove('heat', 'conflict');
    });
    document.querySelectorAll('.collab-edge-label').forEach(function (t) {
      t.classList.remove('heat', 'conflict');
    });
    document.querySelectorAll('.collab-node-outer').forEach(function (g) {
      g.classList.add('inactive');
      g.classList.remove('active');
    });
    AGENT_ROLES.forEach(function (r) {
      var ring = document.getElementById('ring-' + r.id);
      if (ring) {
        var circumference = 2 * Math.PI * (r.r + 5);
        ring.setAttribute('stroke-dashoffset', circumference);
      }
      var cnt = document.getElementById('count-' + r.id);
      if (cnt) cnt.textContent = '0 msg';
      // 清 msg 徽章
      COLLAB_EDGES.forEach(function (triple) {
        if (triple[0] === r.id) {
          var num = document.getElementById('badge-' + triple[0] + '-' + triple[1] + '-num');
          if (num) num.textContent = '0';
        }
      });
    });
    var partLayer = document.getElementById('collab-particles');
    if (partLayer) partLayer.innerHTML = '';
    updateCollabMetrics();
    showToast('协作图已重置', 'info');
  }

  // ── API Helpers ──

  async function apiFetch(path, options = {}) {
    const resp = await _af(`${API}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(formatApiError(err, resp.statusText));
    }
    return resp.json();
  }

  function formatApiError(err, fallback) {
    if (!err) return fallback || '请求失败';
    if (typeof err === 'string') return err;
    if (Array.isArray(err.detail)) {
      return err.detail.map(function (item) {
        if (!item || typeof item !== 'object') return String(item);
        var loc = Array.isArray(item.loc) ? item.loc.join('.') : '';
        return (loc ? loc + ': ' : '') + (item.msg || item.reason || item.error || JSON.stringify(item));
      }).join('; ');
    }
    if (typeof err.detail === 'string') return err.detail;
    if (err.detail && typeof err.detail === 'object') return err.detail.reason || err.detail.error || JSON.stringify(err.detail);
    return err.reason || err.error || fallback || '请求失败';
  }

  // ── Load Stats ──

  async function loadStats() {
    if (document.hidden) return;
    var ind = document.getElementById('refresh-indicator');
    if (ind) { ind.classList.add('active'); setTimeout(function () { ind.classList.remove('active'); }, 600); }

    try {
      const stats = await apiFetch('/stats');
      // 顶栏 stat strip
      setText('kpi-sessions', stats.twin_loop?.total_sessions || 0);
      setText('kpi-steps', stats.twin_loop?.total_steps || 0);
      setText('kpi-sops', stats.zero_exp?.total_sops || 0);
      var sc = stats.critic?.max_score;
      setText('kpi-score', sc ? sc.toFixed(3) : '—');
    } catch (e) {
      console.warn('Stats load failed:', e);
    }

    try {
      const sopData = await apiFetch('/sops');
      renderSOPs(sopData.sops || []);
    } catch (e) {}
  }

  function setText(id, v) { var el = document.getElementById(id); if (el) el.textContent = v; }

  function runtimeBool(v, okText, badText) {
    return v ? okText : badText;
  }

  // ── Runtime (页脚状态条) ──

  function renderRuntimeStatus(payload) {
    payload = payload || {};
    runtimeState = payload;
    const runtime = payload.runtime || payload;
    const limits = runtime.resource_limits || {};
    const lastCheck = runtime.last_self_check || payload.last_self_check || {};
    const ready = !!runtime.ready;
    const blocked = !!payload.blocked || !!runtime.self_check_blocked;

    var rtReady = document.getElementById('rt-ready');
    var readyChip = rtReady ? rtReady.parentElement : null;
    if (rtReady) rtReady.textContent = ready ? '●' : (blocked ? '⏸' : '○');
    if (readyChip) {
      readyChip.className = 'runtime-bar__chip ' + (ready ? 'ready' : (blocked ? 'blocked' : 'error'));
    }

    setText('rt-mode', runtime.mode || '—');
    setText('rt-docker', runtime.docker_available ? '已就绪' : '未安装');
    setText('rt-image', runtime.image_available ? '已就绪' : '镜像缺失');
    setText('rt-mem', (limits.memory_limit_mb || '—') + ' MB');
    setText('rt-lastcheck', lastCheck.ok !== undefined ? (lastCheck.ok ? 'OK' : 'FAIL') : '—');

    // 详情展开 (点击 Runtime 标题)
    var detail = document.getElementById('runtime-drawer__inner');
    if (detail) {
      var checks = lastCheck.checks || payload.checks || {};
      var checkItems = '';
      for (var key in checks) {
        if (checks.hasOwnProperty(key)) {
          var result = checks[key];
          var label = result && result.ok ? 'OK' : (result && result.skipped ? 'SKIP' : 'FAIL');
          checkItems += '<div class="runtime-list-item"><strong>' + esc(key) + '</strong> · ' + label +
            (typeof result?.exit_code !== 'undefined' ? ' · exit ' + result.exit_code : '') + '</div>';
        }
      }
      detail.innerHTML = [
        '<div class="runtime-grid">',
        '<div class="runtime-card"><div class="runtime-k">Docker 镜像</div><div class="runtime-v">' + esc(runtime.docker_image || '—') + '</div></div>',
        '<div class="runtime-card"><div class="runtime-k">CPU</div><div class="runtime-v">' + esc(limits.cpu_limit ?? '—') + '</div></div>',
        '<div class="runtime-card"><div class="runtime-k">PIDs</div><div class="runtime-v">' + esc(limits.pids_limit ?? '—') + '</div></div>',
        '<div class="runtime-card"><div class="runtime-k">nofile</div><div class="runtime-v">' + esc(limits.nofile_limit ?? '—') + '</div></div>',
        '</div>',
        checkItems
      ].join('');
    }
  }

  async function loadRuntimeStatus() {
    if (document.hidden) return;
    try {
      const runtime = await apiFetch('/runtime-status');
      renderRuntimeStatus(runtime);
    } catch (e) {
      console.warn('Runtime load failed:', e);
    }
  }

  async function runRuntimeSelfCheck() {
    showToast('正在执行 runtime self-check...', 'info');
    try {
      const payload = await apiFetch('/runtime-self-check', { method: 'POST' });
      renderRuntimeStatus(payload);
      if (payload.ok) showToast('Runtime self-check 通过', 'success');
      else if (payload.blocked) showToast('Runtime self-check 被阻塞', 'warning');
      else showToast('Runtime self-check 失败', 'error');
    } catch (e) {
      showToast('Runtime self-check 失败: ' + e.message, 'error');
    }
  }

// Runtime 抽屉点击展开
function bindRuntimeBar() {
  var btn = document.getElementById('runtime-bar__toggle');
  var drawer = document.getElementById('runtime-drawer');
  if (!btn || !drawer) return;
  btn.addEventListener('click', function () {
    var open = drawer.style.display !== 'none';
    drawer.style.display = open ? 'none' : 'block';
    btn.classList.toggle('runtime-bar__toggle--open', !open);
    // 展开时若抽屉内容还是空，自动拉一次 runtime-status
    if (!open && drawer.querySelector('.io-empty')) loadRuntimeStatus();
  });
}

function toggleRuntimeDrawer() {
  var btn = document.getElementById('runtime-bar__toggle');
  if (btn) btn.click();
}

  // ── Simulation State ──

  function setSimulationRunning(running) {
    simulationRunning = running;
    var btnLaunch = document.getElementById('btn-launch');
    var btnStop = document.getElementById('btn-stop');
    var btnRun = document.getElementById('btn-run');
    if (btnLaunch) btnLaunch.style.display = running ? 'none' : '';
    if (btnStop) btnStop.style.display = running ? '' : 'none';
    if (btnRun) btnRun.disabled = running;
    // 流水线联动：仿真启动时高亮 L3
    if (running) setActiveLayer('L3');
  }

  // ── Create & Run ──

  async function resolveExerciseTeamId() {
    if (exerciseState.teamId) return exerciseState.teamId;
    try {
      var resp = await (window._agFetch || fetch)('/api/v1/agent-config/teams?limit=200&offset=0');
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      var data = await resp.json();
      var teams = Array.isArray(data) ? data : (data.teams || data.items || []);
      var chosen = teams.find(function (team) {
        return Number(team.agent_count || team.member_count || team.agents_count || 0) > 0;
      }) || teams[0];
      if (chosen) {
        exerciseState.teamId = chosen.team_id || chosen.id || '';
        exerciseState.teamName = chosen.name || chosen.team_name || exerciseState.teamId;
        updateGuideTags();
      }
    } catch (e) {
      console.warn('[sandbox] 自动选择团队失败:', e && e.message || e);
    }
    return exerciseState.teamId || 'build_system';
  }

  async function createAndRun() {
    const mode = document.getElementById('sim-mode').value;
    const maxSteps = parseInt(document.getElementById('sim-steps').value, 10);
    const speed = parseFloat(document.getElementById('sim-speed').value, 10);
    const branches = parseInt(document.getElementById('sim-branches').value, 10);
    const teamId = await resolveExerciseTeamId();

    setStatus('正在创建沙箱会话...');
    setSimulationRunning(true);
    resetCollabGraph();
    resetEvolveLoop();

    try {
      const session = await apiFetch('/sessions', {
        method: 'POST',
        body: JSON.stringify({
          team_id: teamId,
          mode: mode,
          max_steps: maxSteps,
          speed_factor: speed,
          parallel_branches: branches,
          trigger_description: '手动触发仿真',
        }),
      });

      currentSessionId = session.session_id;
      renderSessionBar(session);
      setStatus('会话创建成功: ' + (session.session_id?.slice(0, 8)||'') + '... 正在启动仿真...');
      rewardHistory = [];
      document.getElementById('timeline').innerHTML = '';
      connectStream(currentSessionId);
      showToast('仿真已启动', 'info');

      // 更新 Input 任务标签
      var taskContent = document.getElementById('input-content-task');
      if (taskContent) taskContent.innerHTML = '<div style="font-size:11px;color:var(--text2);line-height:1.6">'
        + '<div><strong style="color:var(--cyan)">session</strong> <code>' + esc(session.session_id) + '</code></div>'
        + '<div><strong style="color:var(--cyan)">team</strong> ' + esc(teamId) + '</div>'
        + '<div><strong style="color:var(--cyan)">mode</strong> ' + esc(mode) + '</div>'
        + '<div><strong style="color:var(--cyan)">max_steps</strong> ' + maxSteps + '</div>'
        + '<div><strong style="color:var(--cyan)">branches</strong> ' + branches + '</div>'
        + '<div><strong style="color:var(--cyan)">trigger</strong> ' + esc('手动触发仿真') + '</div>'
        + '</div>';

      const result = await apiFetch('/sessions/' + session.session_id + '/run', { method: 'POST' });

      if (result.alignment) {
        updateEvaluation(result.alignment.evaluation);
        if (result.alignment.best_sop) document.getElementById('btn-inject').disabled = false;
        updateEvolveLoop(result.alignment);
      }

      var scoreText = result.alignment?.evaluation?.global_score?.toFixed(3) || '—';
      setStatus('✅ 仿真完成: ' + result.total_steps + ' 步 | 评分: ' + scoreText);
      showToast('仿真完成 · ' + result.total_steps + ' 步 · 评分 ' + scoreText, 'success');
      addSessionToHistory({ id: session.session_id, steps: result.total_steps, score: scoreText, status: 'completed' });
    } catch (e) {
      setStatus('❌ 错误: ' + e.message);
      showToast('仿真失败: ' + e.message, 'error');
      if (currentSessionId) addSessionToHistory({ id: currentSessionId, steps: rewardHistory.length, score: '—', status: 'failed' });
    } finally {
      setSimulationRunning(false);
      loadStats();
      loadSessionHistoryFromBackend();
    }
  }

  // ── Stop ──

  async function stopSimulation() {
    if (!currentSessionId) return;
    try {
      showToast('正在停止仿真...', 'warning');
      if (eventSource) { eventSource.close(); eventSource = null; }
      await apiFetch('/sessions/' + currentSessionId + '/stop', { method: 'POST' });
      setSimulationRunning(false);
      setStatus('⏹ 仿真已停止');
      showToast('仿真已停止 · ' + rewardHistory.length + ' 步', 'info');
      if (currentSessionId) addSessionToHistory({ id: currentSessionId, steps: rewardHistory.length, score: '—', status: 'stopped' });
    } catch (e) {
      if (eventSource) { eventSource.close(); eventSource = null; }
      setSimulationRunning(false);
      setStatus('⏹ 仿真已本地停止');
    }
  }

  // ── Session History ──

  function addSessionToHistory(info) {
    sessionHistoryList.unshift({ id: info.id, steps: info.steps, score: info.score, status: info.status || 'completed', time: new Date().toISOString() });
    if (sessionHistoryList.length > 20) sessionHistoryList = sessionHistoryList.slice(0, 20);
    renderSessionHistory();
  }

function renderSessionHistory() {
  var list = document.getElementById('session-list');
  var count = document.getElementById('session-count');
  if (count) count.textContent = sessionHistoryList.length;
  if (!list) return;
  if (!sessionHistoryList.length) {
    list.innerHTML = '<div style="color:var(--dim);font-size:11px;padding:12px;text-align:center">暂无历史会话</div>';
    return;
  }
  var html = '';
  for (var i = 0; i < sessionHistoryList.length; i++) {
    var s = sessionHistoryList[i];
    var statusClass = s.status === 'running' ? 'running' : s.status === 'failed' ? 'failed' : (s.status === 'stopped' ? 'stopped' : 'completed');
    var statusText = { running: '运行中', completed: '已完成', failed: '失败', stopped: '已停止' }[s.status] || s.status;
    var time = s.time ? new Date(s.time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
    var isCurrent = currentSessionId && s.id === currentSessionId;
    html += '<div class="session-item' + (isCurrent ? ' session-item--current' : '') + '" data-session-id="' + esc(s.id || '') + '">' +
      '<span class="session-item-id" title="' + esc(s.id) + '">' + esc((s.id || '').slice(0, 10)) + '</span>' +
      '<div class="session-item-meta">' +
      '<span>' + (s.steps || 0) + ' 步</span>' +
      '<span>分 ' + (s.score || '—') + '</span>' +
      '<span>' + time + '</span>' +
      '</div>' +
      '<span class="session-item-status ' + statusClass + '">' + statusText + '</span>' +
      '</div>';
  }
  list.innerHTML = html;
  // 绑定点击 — 切到该 session 并打开详情
  list.querySelectorAll('.session-item').forEach(function (el) {
    el.addEventListener('click', function () {
      var sid = el.getAttribute('data-session-id');
      if (!sid) return;
      currentSessionId = sid;
      var idEl = document.getElementById('session-id-display');
      if (idEl) idEl.textContent = sid;
      renderSessionHistory(); // 重新高亮 current
      loadSessionDetail();
    });
  });
}

async function loadSessionHistoryFromBackend() {
  try {
    var resp = await apiFetch('/sessions');
    var list = (resp && resp.sessions) || [];
    if (!Array.isArray(list) || !list.length) return;
    // 映射到本地格式 — 保留最新 20 条
    sessionHistoryList = list.slice(0, 20).map(function (s) {
      return {
        id: s.session_id,
        steps: s.total_steps_executed || s.steps || 0,
        score: s.evaluation && s.evaluation.global_score != null ? s.evaluation.global_score.toFixed(3) : '—',
        status: s.status || 'completed',
        time: s.created_at || s.updated_at || new Date().toISOString()
      };
    });
    renderSessionHistory();
  } catch (e) {
    console.warn('Session history load failed:', e);
  }
}

  function toggleSessionHistory() {
    var list = document.getElementById('session-list');
    var toggle = document.getElementById('session-history-toggle');
    if (!list) return;
    // 这里 list 始终展开，toggle 只是刷新
    renderSessionHistory();
    if (toggle) toggle.classList.toggle('open');
  }

  // ── SSE Stream ──

  function connectStream(sessionId) {
    if (eventSource) eventSource.close();
    eventSource = new EventSource(API + '/sessions/' + sessionId + '/stream');

    eventSource.onmessage = function (event) {
      var data = JSON.parse(event.data);

      if (data.type === 'step') {
        addTimelineStep(data);
        rewardHistory.push(data.global_reward);
        drawChart();
        document.getElementById('step-counter').textContent = rewardHistory.length + ' 步';
        updateRewardMeta();
        updateAgentNodes(data);
        updateRuntimeProgress(data);
        updatePipelineFromStep(data);
        if (data.agent_roles) ingestAgentRoles(data.agent_roles);

        consumeCollabStepMessages(data);
        // 数据驱动协作图：从 agent_actions 推断通信
        driveCollabFromStep(data);
        // 3D 场景同步
        sw3dOnStep(data);
      } else if (data.type === 'complete') {
        eventSource.close();
        setStatus('仿真完成: ' + data.total_steps + ' 步');
        showToast('仿真完成 · ' + data.total_steps + ' 步', 'success');
        addSessionToHistory({ id: sessionId, steps: data.total_steps, score: '—', status: 'completed' });
        setSimulationRunning(false);
        setActiveLayer('L4'); // 完成后切到评价层
        // 进度条置 100，4 秒后归 0
        setRuntimeProgress(100, (data.total_steps || 0) + '/' + (data.total_steps_planned || data.total_steps || 0));
        setTimeout(function () { resetRuntimeProgress(); }, 4000);
        markAllPipelineDone();
        updateEvolveLoop(data);
        // 3D: 全部 agent 亮起庆祝
        if (sw3dEnsure()) {
          ['planner','retriever','coordinator','executor','critic'].forEach(function (r) {
            window._sw3d.activateAgent(r, 5000);
          });
        }
        loadSessionHistoryFromBackend();
      }
    };

    eventSource.onerror = function () {
      eventSource.close();
      setSimulationRunning(false);
    };
  }

  // 数据驱动协作图：根据 step 事件推断 Agent 之间的通信
  function driveCollabFromStep(data) {
    var actions = data.agent_actions || {};
    var keys = Object.keys(actions);
    if (!keys.length) return;
    // 简化策略：取前两个 action 的 agent 之间通信
    for (var i = 0; i < keys.length - 1; i++) {
      var a1 = mapAgentId(keys[i]);
      var a2 = mapAgentId(keys[i + 1]);
      if (a1 && a2 && a1 !== a2) {
        recordCollabEvent({ from: a1, to: a2 });
        // 3D 通信线脉冲
        sw3dPulseComm(a1, a2);
      }
    }
  }

  // ── 3D 场景桥接 ──

  function sw3dEnsure() {
    if (!window._sw3d) return false;
    if (!window._sw3d.isInitialized()) {
      window._sw3d.init();
    }
    return window._sw3d.isInitialized();
  }

  function sw3dOnStep(data) {
    if (!sw3dEnsure()) return;
    var step = data.step_id || data.current || rewardHistory.length;
    window._sw3d.updateStep(step);

    // 激活当前步骤中活跃的 agent
    var actions = data.agent_actions || {};
    Object.keys(actions).forEach(function (agentId) {
      var role = mapAgentId(agentId);
      if (role) window._sw3d.activateAgent(role, 2500);
    });
  }

  function sw3dPulseComm(fromRole, toRole) {
    if (!sw3dEnsure()) return;
    window._sw3d.pulseCommLine(fromRole, toRole, 0.8);
  }

  function sw3dSetRoom(roomId) {
    if (!sw3dEnsure()) return;
    window._sw3d.setRoom(roomId);
    var name = window._sw3d.getCurrentRoomName();
    var label = document.getElementById('scene-3d-label');
    if (label) label.textContent = name || roomId;
  }

// 把后端返回的 agent id 映射到 5 个协作图角色
function mapAgentId(agentId) {
  if (!agentId) return null;
  var id = String(agentId);
  // 1) 后端权威 (SSE agent_roles 注入)
  if (currentRoleMap[id]) return currentRoleMap[id];
  if (currentRoleMap[agentId]) return currentRoleMap[agentId];
  // 2) 名字硬匹配兜底
  var lid = id.toLowerCase();
  if (lid.includes('plan')) return 'planner';
  if (lid.includes('retriev') || lid.includes('search') || lid.includes('rag')) return 'retriever';
  if (lid.includes('coord') || lid.includes('orchestrat') || lid.includes('manage')) return 'coordinator';
  if (lid.includes('exec') || lid.includes('action') || lid.includes('tool')) return 'executor';
  if (lid.includes('critic') || lid.includes('review') || lid.includes('check') || lid.includes('eval')) return 'critic';
  // 3) hash 兜底
  var hash = 0; for (var i = 0; i < lid.length; i++) hash = (hash + lid.charCodeAt(i)) % 5;
  return ['planner', 'retriever', 'coordinator', 'executor', 'critic'][hash];
}

function updateAgentNodes(data) {
  // 根据 step 事件更新 L1 agent 状态
  var actions = data.agent_actions || {};
  var keys = Object.keys(actions);
  var grid = document.getElementById('agent-grid');
  if (!grid) return;
  // 优先用后端传来的 twins/agents 列表 (真数据)
  var twins = data.twins || data.agents || null;
  if (Array.isArray(twins) && twins.length) {
    renderL1AgentGrid(twins);
    return;
  }
  // 否则只把现有 cell 标 working
  var activeCount = 0;
  grid.querySelectorAll('.agent-node').forEach(function (el) {
    el.classList.remove('idle', 'working', 'thinking', 'error');
    el.classList.add('working');
    activeCount++;
  });
  var cnt = document.getElementById('agent-active-count');
  if (cnt) cnt.textContent = activeCount;
}

function renderL1AgentGrid(twins) {
  var grid = document.getElementById('agent-grid');
  if (!grid) return;
  grid.innerHTML = '';
  var max = Math.min(twins.length, 24);
  var active = 0;
  for (var i = 0; i < max; i++) {
    var t = twins[i] || {};
    var name = t.name || t.agent_id || t.id || ('agent_' + i);
    var role = t.role || t.type || 'agent';
    var state = t.status || t.state || 'idle';
    var cell = document.createElement('div');
    cell.className = 'agent-node l1-agent-cell ' + (state === 'active' || state === 'working' ? 'l1-agent-cell--active' : '');
    cell.innerHTML = '<div class="agent-name l1-agent-cell__name">' + esc(name) + '</div>' +
      '<div class="agent-role l1-agent-cell__role">' + esc(role) + ' · ' + esc(state) + '</div>';
    grid.appendChild(cell);
    if (state === 'active' || state === 'working') active++;
  }
  var cnt = document.getElementById('agent-active-count');
  if (cnt) cnt.textContent = active;
  // 暴露总数角标
  var totalEl = document.getElementById('agent-total-count');
  if (totalEl) totalEl.textContent = twins.length;
}

async function loadL1AgentGridFromStats() {
  try {
    var stats = await apiFetch('/stats');
    var ws = stats && (stats.world_state || stats.digital_twin || null);
    var twins = ws && (ws.twins || ws.agents || null);
    if (Array.isArray(twins) && twins.length) {
      renderL1AgentGrid(twins);
    }
  } catch (e) {
    console.warn('L1 agent grid load failed:', e);
  }
}

  // ── Inject Strategy ──

  async function injectStrategy() {
    if (!currentSessionId) return;
    try {
      var result = await apiFetch('/sessions/' + currentSessionId + '/inject', {
        method: 'POST',
        body: JSON.stringify({ confirm: true }),
      });
      setStatus('💉 策略注入成功: ' + esc(result.sop_name));
      showToast('策略注入成功: ' + (result.sop_name || ''), 'success');
      document.getElementById('btn-inject').disabled = true;
    } catch (e) {
      showToast('注入失败: ' + e.message, 'error');
    }
  }

  // ── Skill Catalog ──

  var skillCatalog = [];

  async function loadSkillCatalog() {
    var teamEl = document.getElementById('skill-inject-team');
    var sel = document.getElementById('skill-inject-select');
    var panel = document.getElementById('skill-inject-panel');
    var team = (teamEl && teamEl.value.trim()) || '';
    if (sel) sel.disabled = true;
    if (panel) panel.innerHTML = '<div class="io-empty">正在加载技能库…</div>';
    try {
      var url = '/api/v1/skill-router/browse';
      if (team) url += '?team_id=' + encodeURIComponent(team);
      var resp = await _af(url);
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      var data = await resp.json();
      skillCatalog = (data && data.skills) || [];
      if (sel) {
        if (!skillCatalog.length) {
          sel.innerHTML = '<option value="">-- 暂无技能 --</option>';
        } else {
          sel.innerHTML = '<option value="">-- 选择要注入的 skill --</option>' +
            skillCatalog.map(function (s) {
              return '<option value="' + esc(s.skill_id || s.id) + '">' + esc(s.name || s.skill_id || s.id) + '</option>';
            }).join('');
        }
        sel.disabled = false;
      }
      if (panel) renderSkillCards(skillCatalog);
      showToast('加载了 ' + skillCatalog.length + ' 个技能', 'info');
    } catch (e) {
      if (panel) panel.innerHTML = '<div class="io-empty">加载失败: ' + esc(e.message) + '</div>';
      showToast('技能库加载失败', 'error');
    }
  }

  function renderSkillCards(skills) {
    var panel = document.getElementById('skill-inject-panel');
    if (!panel) return;
    if (!skills || !skills.length) {
      panel.innerHTML = '<div class="sop-empty"><span class="sop-empty-icon">📦</span><span>请先在技能萃取页提取技能</span></div>';
      return;
    }
    panel.innerHTML = skills.slice(0, 8).map(function (s) {
      var id = s.skill_id || s.id || '';
      var name = s.name || id;
      var summary = s.summary || s.description || '';
      var tagsHtml = (s.tags || []).slice(0, 2).map(function (t) {
        return '<span class="skill-tag">' + esc(t) + '</span>';
      }).join('');
      return '<div class="skill-card" data-skill-id="' + esc(id) + '" onclick="selectSkillCard(\'' + esc(id) + '\')">' +
        '<div class="skill-card-header"><div class="skill-card-name">' + esc(name) + '</div><code class="skill-card-id">' + esc(id.slice(0, 10)) + '</code></div>' +
        '<div class="skill-card-summary">' + esc(summary) + '</div>' +
        '<div class="skill-card-tags">' + (tagsHtml || '') + '</div>' +
        '</div>';
    }).join('');
  }

  function selectSkillCard(skillId) {
    var sel = document.getElementById('skill-inject-select');
    if (sel) sel.value = skillId;
    document.querySelectorAll('.skill-card').forEach(function (el) {
      el.classList.toggle('selected', el.getAttribute('data-skill-id') === skillId);
    });
  }

  async function injectSkillIntoSandbox() {
    var sel = document.getElementById('skill-inject-select');
    var teamEl = document.getElementById('skill-inject-team');
    var modeEl = document.getElementById('sim-mode');
    var stepsEl = document.getElementById('sim-steps');
    var result = document.getElementById('skill-inject-result');
    var skillId = sel ? sel.value : '';
    if (!skillId) { showToast('请先选择要注入的 skill', 'warning'); return; }
    if (result) result.innerHTML = '<span style="color:var(--muted)">正在创建 session 并注入 skill…</span>';

    var team = (teamEl && teamEl.value.trim()) || '';
    var mode = (modeEl && modeEl.value) || 'evolutionary';
    var steps = parseInt((stepsEl && stepsEl.value) || '60', 10);

    try {
      var createResp = await _af(API + '/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          team_id: team || 'public',
          mode: mode,
          max_steps: steps,
          parallel_branches: 3,
          trigger_description: 'injected from skill: ' + skillId,
          use_llm: false,
          sync_dt: true,
          initial_skill_id: skillId,
        }),
      });
      if (!createResp.ok) {
        var errBody = await createResp.text();
        throw new Error('创建 session 失败: ' + createResp.status + ' ' + errBody.slice(0, 200));
      }
      var session = await createResp.json();
      currentSessionId = session.session_id;
      var skillInfo = session.initial_skill || {};
      var skillName = skillInfo.skill_name || skillId;
      var sopId = skillInfo.sop_id || ('ext_' + skillId);

      var runResp = await _af(API + '/sessions/' + session.session_id + '/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steps: steps }),
      });
      if (!runResp.ok) {
        var runErr = await runResp.text();
        throw new Error('启动仿真失败: ' + runResp.status + ' ' + runErr.slice(0, 200));
      }
      var runData = await runResp.json();
      if (runData && runData.session_id) currentSessionId = runData.session_id;

      if (eventSource) try { eventSource.close(); } catch (e) {}
      connectStream(currentSessionId);

      var injBtn = document.getElementById('btn-inject');
      if (injBtn) injBtn.disabled = false;

      if (result) {
        result.innerHTML = '<span style="color:var(--koke)">✓ 注入成功</span> · skill <code>' + esc(skillName) + '</code> → seed sop <code>' + esc(sopId) + '</code>';
      }
      showToast('Skill ' + skillName + ' 已注入并启动仿真', 'success');
      setTimeout(loadStats, 1500);
    } catch (e) {
      if (result) result.innerHTML = '<span style="color:var(--shu)">✗ 失败: ' + esc(e.message) + '</span>';
      showToast('Skill 注入失败: ' + e.message, 'error');
    }
  }

  // ── UI Renderers ──

  function addTimelineStep(data) {
    var timeline = document.getElementById('timeline');
    if (timeline.children.length === 1 && timeline.children[0].classList.contains('io-empty')) {
      timeline.innerHTML = '';
    }

    var rewardClass = data.global_reward > 0.15 ? 'positive' : data.global_reward < 0 ? 'negative' : 'neutral';
    var actions = '';
    var agentActions = data.agent_actions || {};
    var actionParts = [];
    for (var id in agentActions) {
      if (agentActions.hasOwnProperty(id)) {
        actionParts.push((id?.slice(0, 6) || '') + ': ' + agentActions[id]);
      }
    }
    actions = actionParts.join(' | ');

    var el = document.createElement('div');
    el.className = 'timeline-step';
    el.innerHTML = '<span class="step-num">#' + data.step_id + '</span><div class="step-actions">' + (actions || '—') + '</div><span class="step-reward ' + rewardClass + '">' + data.global_reward.toFixed(3) + '</span>';
    timeline.prepend(el);

    // 同步到 log tab
    var logTimeline = document.getElementById('timeline-log');
    if (logTimeline) {
      if (logTimeline.children.length === 1 && logTimeline.children[0].classList.contains('io-empty')) {
        logTimeline.innerHTML = '';
      }
      var logEl = el.cloneNode(true);
      logTimeline.prepend(logEl);
    }
  }

  function updateEvaluation(evalData) {
    if (!evalData) return;
    var dims = [
      ['task', evalData.task_completion],
      ['comm', evalData.communication_efficiency],
      ['resource', evalData.resource_utilization],
      ['conflict', evalData.conflict_avoidance],
      ['convergence', evalData.convergence_speed],
      ['global', evalData.global_score],
    ];

    for (var i = 0; i < dims.length; i++) {
      var key = dims[i][0];
      var value = dims[i][1];
      var bar = document.getElementById('bar-' + key);
      var valEl = document.getElementById('val-' + key);
      if (bar && valEl) {
        var pct = (value * 100).toFixed(0);
        bar.style.width = pct + '%';
        bar.className = 'score-bar-fill ' + (value > 0.6 ? 'high' : value > 0.3 ? 'mid' : 'low');
        valEl.textContent = pct + '%';
      }
    }

    var recList = document.getElementById('rec-list');
    var recs = evalData.recommendations || [];
    var recHtml = '';
    for (var j = 0; j < recs.length; j++) {
      recHtml += '<div class="rec-item">' + esc(recs[j]) + '</div>';
    }
    if (recList) recList.innerHTML = recHtml;
  }

  function renderSOPs(sops) {
    var container = document.getElementById('sop-list');
    if (!container) return;
    if (!sops || !sops.length) {
      container.innerHTML = '<div class="sop-empty"><span class="sop-empty-icon">📋</span><span>尚未提取 SOP</span></div>';
      return;
    }
    var html = '';
    for (var i = 0; i < sops.length; i++) {
      var sop = sops[i];
      var statusColor = sop.status === 'validated' ? 'var(--green)' : 'var(--amber)';
      html += '<div class="sop-card">' +
        '<div class="sop-card-name">' + esc(sop.name) + '</div>' +
        '<div class="sop-card-stats">奖励: ' + (sop.avg_reward || 0).toFixed(3) + ' · 成功率: ' + ((sop.success_rate || 0) * 100).toFixed(0) + '%</div>' +
        '<div class="sop-card-status">状态: <span style="color:' + statusColor + ';">' + esc(sop.status || 'unknown') + '</span></div>' +
        '</div>';
    }
    container.innerHTML = html;
  }

function setStatus(msg) {
  var el = document.getElementById('sim-status');
  if (el) el.textContent = msg;
}

// ── Session Bar (顶部沙箱 ID 条) ──

function renderSessionBar(session) {
  if (!session) return;
  var idEl = document.getElementById('session-id-display');
  var modeEl = document.getElementById('session-mode');
  var stepEl = document.getElementById('session-step');
  var scoreEl = document.getElementById('session-score');
  var statusEl = document.getElementById('session-status');
  if (idEl) idEl.textContent = session.session_id || '—';
  if (modeEl) modeEl.textContent = session.mode || '—';
  if (stepEl) stepEl.textContent = session.total_steps ?? session.step_count ?? 0;
  if (scoreEl) scoreEl.textContent = session.last_score ?? '—';
  if (statusEl) statusEl.textContent = session.status || '—';
}

function copySessionId() {
  var el = document.getElementById('session-id-display');
  if (!el) return;
  var text = el.textContent || '';
  if (!text || text.indexOf('—') === 0) { showToast('尚未启动 session', 'warning'); return; }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function () { showToast('已复制: ' + text.slice(0, 12) + '…', 'success'); }, function () { fallbackCopy(text); });
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); showToast('已复制: ' + text.slice(0, 12) + '…', 'success'); }
  catch (e) { showToast('复制失败', 'error'); }
  document.body.removeChild(ta);
}

// ── Session 概要详情 ──

function updateRuntimeProgress(stepData) {
  // stepData: SSE step payload — current | total_steps
  var cur = Number(stepData.current ?? stepData.step_id ?? stepData.index ?? 0);
  var total = Number(stepData.total_steps ?? 0);
  if (!total || !isFinite(total) || total <= 0) return;
  var pct = Math.min(100, Math.max(0, (cur / total) * 100));
  setRuntimeProgress(pct, cur + '/' + total);
}

function setRuntimeProgress(pct, text) {
  var bar = document.getElementById('runtime-bar__progress');
  if (bar) bar.value = pct;
  var tx = document.getElementById('runtime-bar__progress-text');
  if (tx) tx.textContent = text || (Math.round(pct) + '%');
}

// ── Pipeline 节点状态随 step 推进 ──

function updatePipelineFromStep(data) {
  var cur = Number(data.current ?? data.step_id ?? 0);
  var total = Number(data.total_steps ?? 0);
  if (!total || total <= 0) return;
  var ratio = Math.max(0, Math.min(1, cur / total));
  // 4 层平均分: 0~0.25 L1, 0.25~0.5 L2, 0.5~0.75 L3, 0.75~1 L4
  var layerIdx = Math.min(3, Math.floor(ratio * 4));
  var layers = ['L1', 'L2', 'L3', 'L4'];
  for (var i = 0; i < layers.length; i++) {
    var el = document.getElementById('pipe-' + layers[i]);
    if (!el) continue;
    el.classList.remove('pipeline-node--pending', 'pipeline-node--running', 'pipeline-node--done');
    if (i < layerIdx) el.classList.add('pipeline-node--done');
    else if (i === layerIdx) el.classList.add('pipeline-node--running');
    else el.classList.add('pipeline-node--pending');
  }
}

function markAllPipelineDone() {
  ['L1', 'L2', 'L3', 'L4'].forEach(function (l) {
    var el = document.getElementById('pipe-' + l);
    if (!el) return;
    el.classList.remove('pipeline-node--pending', 'pipeline-node--running');
    el.classList.add('pipeline-node--done');
  });
}

// ── SECS Loop 回流指示 ──

function updateEvolveLoop(data) {
  // 更新回流箭头 label
  var label = document.querySelector('.pipeline-arrow__label');
  var hasSop = data.best_sop || (data.alignment && data.alignment.best_sop);
  if (label) {
    label.textContent = hasSop ? 'SOP 已沉淀' : '评分已回流';
    label.style.color = hasSop ? 'var(--koke, #6BC47F)' : 'var(--kitsune, #D4A44A)';
  }
  // 回流箭头动画加速
  var returnArrow = document.querySelector('.pipeline-arrow--return');
  if (returnArrow) returnArrow.style.animationDuration = '1.2s';
  // EVOLVE 节点 done
  var evolve = document.getElementById('pipe-EVOLVE');
  if (evolve) {
    evolve.classList.add('pipeline-node--done');
  }
}

function resetEvolveLoop() {
  var label = document.querySelector('.pipeline-arrow__label');
  if (label) {
    label.textContent = '回流进化';
    label.style.color = '';
  }
  var returnArrow = document.querySelector('.pipeline-arrow--return');
  if (returnArrow) returnArrow.style.animationDuration = '';
  var evolve = document.getElementById('pipe-EVOLVE');
  if (evolve) evolve.classList.remove('pipeline-node--done');
}

function resetRuntimeProgress() {
  setRuntimeProgress(0, '0/—');
}

async function loadSessionDetail() {
  var sid = currentSessionId;
  if (!sid) {
    var idEl = document.getElementById('session-id-display');
    if (idEl) sid = idEl.textContent;
  }
  if (!sid || sid.indexOf('—') === 0 || sid === '— 尚未启动 —') {
    showToast('请先启动一个 session', 'warning');
    return;
  }
  var modal = document.getElementById('session-detail-modal');
  var body = document.getElementById('session-detail-modal__body');
  if (!modal || !body) return;
  modal.style.display = 'flex';
  body.innerHTML = '<div class="io-empty">正在加载 ' + esc(sid.slice(0, 12)) + '… 的详情</div>';
  try {
    var detail = await apiFetch('/sessions/' + encodeURIComponent(sid));
    body.innerHTML = renderSessionDetailHtml(detail);
    renderSessionBar(detail);
  } catch (e) {
    body.innerHTML = '<div class="io-empty" style="color:var(--shu)">加载失败: ' + esc(e.message) + '</div>';
    showToast('加载 session 失败: ' + e.message, 'error');
  }
}

function closeSessionDetail() {
  var modal = document.getElementById('session-detail-modal');
  if (modal) modal.style.display = 'none';
}

function renderSessionDetailHtml(d) {
  if (!d) return '<div class="io-empty">无数据</div>';
  var ev = d.evaluation || {};
  var sop = d.best_sop || null;
  var score = (ev.global_score != null) ? ev.global_score.toFixed(3) : '—';
  var dims = [
    ['任务完成', ev.task_completion],
    ['通信效率', ev.communication_efficiency],
    ['资源利用', ev.resource_utilization],
    ['冲突回避', ev.conflict_avoidance],
    ['收敛速度', ev.convergence_speed]
  ];
  var dimRows = dims.map(function (t) {
    var v = (t[1] != null) ? (t[1] * 100).toFixed(0) + '%' : '—';
    return '<div class="session-detail-row"><span>' + esc(t[0]) + '</span><strong>' + v + '</strong></div>';
  }).join('');
  var sopRow = sop
    ? '<div class="session-detail-row"><span>最佳 SOP</span><strong>' + esc(sop.name || sop.sop_id) + '</strong></div>'
    : '<div class="session-detail-row"><span>最佳 SOP</span><strong>—</strong></div>';
  var recs = (ev.recommendations || []).slice(0, 4).map(function (r) {
    return '<li>' + esc(r) + '</li>';
  }).join('') || '<li class="io-empty">暂无建议</li>';
  return [
    '<div class="session-detail-grid">',
      '<div class="session-detail-row"><span>Session ID</span><code>' + esc(d.session_id || '—') + '</code></div>',
      '<div class="session-detail-row"><span>状态</span><strong>' + esc(d.status || '—') + '</strong></div>',
      '<div class="session-detail-row"><span>模式</span><strong>' + esc(d.mode || '—') + '</strong></div>',
      '<div class="session-detail-row"><span>团队</span><strong>' + esc(d.team_id || '—') + '</strong></div>',
      '<div class="session-detail-row"><span>最大步数</span><strong>' + (d.max_steps || 0) + '</strong></div>',
      '<div class="session-detail-row"><span>已执行步</span><strong>' + (d.total_steps_executed || 0) + '</strong></div>',
      '<div class="session-detail-row"><span>数字孪生体</span><strong>' + (d.twins_count || 0) + '</strong></div>',
      '<div class="session-detail-row"><span>综合评分</span><strong style="color:var(--koke)">' + score + '</strong></div>',
      sopRow,
    '</div>',
    '<div class="session-detail-section"><h4>评分维度</h4>' + dimRows + '</div>',
    '<div class="session-detail-section"><h4>优化建议</h4><ul class="session-detail-recs">' + recs + '</ul></div>'
  ].join('');
}

  // ── Reward Chart (SVG) ──

  function drawChart() {
    var svg = document.getElementById('reward-chart');
    if (!svg) return;
    if (rewardHistory.length < 2) { svg.innerHTML = ''; return; }

    var W = 400, H = 160;
    var padLeft = 40, padRight = 12, padTop = 14, padBottom = 20;
    var pw = W - padLeft - padRight;
    var ph = H - padTop - padBottom;

    var maxVal = Math.max.apply(null, rewardHistory.concat([0.5]));
    var minVal = Math.min.apply(null, rewardHistory.concat([0]));
    var range = maxVal - minVal || 1;

    var parts = [];
    for (var i = 0; i <= 4; i++) {
      var gy = padTop + (ph / 4) * i;
      parts.push('<line class="chart-grid-line" x1="' + padLeft + '" y1="' + gy + '" x2="' + (padLeft + pw) + '" y2="' + gy + '"/>');
    }

    var pts = [];
    for (var j = 0; j < rewardHistory.length; j++) {
      var x = padLeft + (j / (rewardHistory.length - 1)) * pw;
      var y = padTop + ph - ((rewardHistory[j] - minVal) / range) * ph;
      pts.push(x.toFixed(1) + ',' + y.toFixed(1));
    }

    var fillPts = pts.join(' ') + ' ' + (padLeft + pw).toFixed(1) + ',' + (padTop + ph).toFixed(1) + ' ' + padLeft.toFixed(1) + ',' + (padTop + ph).toFixed(1);
    parts.push('<polygon class="chart-fill" points="' + fillPts + '"/>');
    parts.push('<polyline class="chart-line" points="' + pts.join(' ') + '"/>');
    parts.push('<text class="chart-label" x="' + padLeft + '" y="' + (padTop - 2) + '">max: ' + maxVal.toFixed(3) + '</text>');
    parts.push('<text class="chart-label" x="' + (padLeft + pw) + '" y="' + (H - 4) + '" text-anchor="end">steps: ' + rewardHistory.length + '</text>');

    svg.innerHTML = parts.join('');
  }

  function updateRewardMeta() {
    if (rewardHistory.length < 2) return;
    var maxVal = Math.max.apply(null, rewardHistory);
    setText('reward-max', maxVal.toFixed(3));
    // 趋势：最近 1/3 步数 vs 前 1/3
    var n = rewardHistory.length;
    var last3rd = rewardHistory.slice(Math.floor(n * 2 / 3));
    var first3rd = rewardHistory.slice(0, Math.floor(n / 3));
    var lastAvg = last3rd.reduce(function (a, b) { return a + b; }, 0) / last3rd.length;
    var firstAvg = first3rd.reduce(function (a, b) { return a + b; }, 0) / first3rd.length;
    var diff = lastAvg - firstAvg;
    var trendEl = document.getElementById('reward-trend');
    if (trendEl) {
      if (diff > 0.05) { trendEl.textContent = '↑ 上升'; trendEl.style.color = 'var(--green)'; }
      else if (diff < -0.05) { trendEl.textContent = '↓ 下降'; trendEl.style.color = 'var(--red)'; }
      else { trendEl.textContent = '→ 平稳'; trendEl.style.color = 'var(--muted)'; }
    }
  }

  // ── Auto-refresh ──

  function startAutoRefresh() {
    if (refreshIntervalId) return;
    refreshIntervalId = setInterval(function () {
      if (!document.hidden) {
        loadStats();
        loadRuntimeStatus();
      }
    }, 30000);
  }

  // ── Globals ──

  window.loadStats = loadStats;
  window.loadRuntimeStatus = loadRuntimeStatus;
  window.runRuntimeSelfCheck = runRuntimeSelfCheck;
  window.createAndRun = createAndRun;
  window.stopSimulation = stopSimulation;
  window.injectStrategy = injectStrategy;
  window.loadSkillCatalog = loadSkillCatalog;
  window.selectSkillCard = selectSkillCard;
  window.injectSkillIntoSandbox = injectSkillIntoSandbox;
  window.toggleSessionHistory = toggleSessionHistory;
  window.resetCollabGraph = resetCollabGraph;
  window.loadSessionDetail = loadSessionDetail;
  window.copySessionId = copySessionId;
  window.toggleRuntimeDrawer = toggleRuntimeDrawer;
  window.runQuickDemo = runQuickDemo;
  window.dismissGuideBanner = dismissGuideBanner;
  window.openTeamSelector = openTeamSelector;
  window.closeTeamSelector = closeTeamSelector;
  window.confirmTeamSelection = confirmTeamSelection;
  window.openSceneSelector = openSceneSelector;
  window.closeSceneSelector = closeSceneSelector;
  window.confirmSceneSelection = confirmSceneSelection;
  window.startExercise = startExercise;

  // ── 全局演练状态 ──
  var exerciseState = {
    teamId: null,
    teamName: '',
    memberIds: [],   // 选中的成员 agent id 列表
    sceneId: null,
    sceneName: ''
  };

  // ── 引导横幅 ──

  function showGuideBanner() {
    var dismissed = localStorage.getItem('secs-guide-dismissed');
    if (dismissed === '1') return;
    var banner = document.getElementById('guide-banner');
    if (banner) banner.style.display = '';
  }

  function dismissGuideBanner() {
    localStorage.setItem('secs-guide-dismissed', '1');
    var banner = document.getElementById('guide-banner');
    if (banner) banner.style.display = 'none';
  }

  function updateGuideTags() {
    var tags = document.getElementById('guide-tags');
    if (!tags) return;
    var hasSelection = exerciseState.teamId || exerciseState.sceneId;
    tags.style.display = hasSelection ? 'flex' : 'none';

    var tagTeam = document.getElementById('tag-team');
    var tagScene = document.getElementById('tag-scene');
    if (tagTeam) {
      tagTeam.textContent = exerciseState.teamName ? '👥 ' + exerciseState.teamName : '未选团队';
      tagTeam.className = 'guide-banner__tag' + (exerciseState.teamName ? ' guide-banner__tag--active' : '');
    }
    if (tagScene) {
      tagScene.textContent = exerciseState.sceneName ? '🏟️ ' + exerciseState.sceneName : '未选场景';
      tagScene.className = 'guide-banner__tag' + (exerciseState.sceneName ? ' guide-banner__tag--active' : '');
    }
  }

  async function startExercise() {
    dismissGuideBanner();
    // 预填参数
    var modeEl = document.getElementById('sim-mode');
    var stepsEl = document.getElementById('sim-steps');
    if (modeEl) modeEl.value = 'evolutionary';
    if (stepsEl) stepsEl.value = '30';

    // 同步 3D 场景
    if (exerciseState.sceneId) sw3dSetRoom(exerciseState.sceneId);

    var parts = [];
    if (exerciseState.teamName) parts.push('团队: ' + exerciseState.teamName);
    if (exerciseState.sceneName) parts.push('场景: ' + exerciseState.sceneName);
    var extra = parts.length ? ' (' + parts.join(', ') + ')' : '';
    showToast('正在以 Lite 模式启动演练仿真' + extra + '…', 'info');
    await createAndRun();
  }

  // 兼容旧名
  async function runQuickDemo() {
    await startExercise();
  }

  // ── 团队选择 ──

  async function openTeamSelector() {
    var overlay = document.getElementById('team-overlay');
    if (!overlay) return;
    overlay.style.display = 'flex';
    var list = document.getElementById('team-list');
    var loading = document.getElementById('team-loading');
    if (list) list.innerHTML = '';
    if (loading) loading.style.display = '';
    var membersSection = document.getElementById('team-members');
    if (membersSection) membersSection.style.display = 'none';
    document.getElementById('team-hint').textContent = '请先选择一个团队';

    try {
      var resp = await fetch('/api/v1/agent-config/teams');
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      var data = await resp.json();
      var teams = data.teams || data || [];
      if (loading) loading.style.display = 'none';
      if (!teams.length) {
        if (list) list.innerHTML = '<div class="modal-select__empty">暂无可用团队，请先在「智能体团队」页面创建团队</div>';
        return;
      }
      renderTeamList(teams, list);
    } catch (err) {
      if (loading) loading.style.display = 'none';
      if (list) list.innerHTML = '<div class="modal-select__empty">加载失败: ' + (err.message || '网络错误') + '</div>';
    }
  }

  function renderTeamList(teams, container) {
    if (!container) return;
    container.innerHTML = teams.map(function (t) {
      var tid = t.id || t.team_id || '';
      var name = t.name || t.team_name || '未命名团队';
      var desc = t.description || '';
      var count = t.agent_count || t.member_count || '?';
      var selected = exerciseState.teamId === tid ? ' modal-select__item--selected' : '';
      return '<div class="modal-select__item' + selected + '" data-team-id="' + tid + '" data-team-name="' + escHtml(name) + '" onclick="selectTeamItem(this, \'' + tid + '\', \'' + escJs(name) + '\')">'
        + '<span class="modal-select__item-icon">👥</span>'
        + '<span class="modal-select__item-name">' + escHtml(name) + '</span>'
        + '<span class="modal-select__item-meta">' + count + ' 成员</span>'
        + '</div>';
    }).join('');
  }

  window.selectTeamItem = async function (el, tid, tname) {
    // 高亮
    document.querySelectorAll('#team-list .modal-select__item').forEach(function (it) { it.classList.remove('modal-select__item--selected'); });
    el.classList.add('modal-select__item--selected');
    exerciseState.teamId = tid;
    exerciseState.teamName = tname;

    // 加载该团队成员
    var membersSection = document.getElementById('team-members');
    var grid = document.getElementById('team-members-grid');
    if (membersSection) membersSection.style.display = '';
    if (grid) grid.innerHTML = '<span style="font-size:11px;color:var(--dim)">加载成员…</span>';
    document.getElementById('team-hint').textContent = '已选: ' + tname + ' — 勾选参演成员';

    try {
      var resp = await fetch('/api/v1/agent-config/teams/' + tid + '/agents');
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      var data = await resp.json();
      var agents = data.agents || data || [];
      exerciseState.memberIds = agents.map(function (a) { return a.id || a.agent_id || ''; }).filter(Boolean);
      renderMemberChips(agents, grid);
    } catch (err) {
      if (grid) grid.innerHTML = '<span style="font-size:11px;color:var(--red)">加载失败</span>';
    }
    updateGuideTags();
  };

  function renderMemberChips(agents, container) {
    if (!container) return;
    if (!agents.length) {
      container.innerHTML = '<span style="font-size:11px;color:var(--dim)">该团队暂无成员</span>';
      return;
    }
    container.innerHTML = agents.map(function (a) {
      var aid = a.id || a.agent_id || '';
      var name = a.name || a.agent_name || 'Agent';
      var role = a.role || '';
      var checked = exerciseState.memberIds.indexOf(aid) >= 0;
      return '<label class="modal-select__member-chip' + (checked ? ' modal-select__member-chip--checked' : '') + '">'
        + '<input type="checkbox" value="' + aid + '" ' + (checked ? 'checked' : '') + ' onchange="toggleMemberChip(this)">'
        + escHtml(role || name)
        + '</label>';
    }).join('');
  }

  window.toggleMemberChip = function (cb) {
    var aid = cb.value;
    var label = cb.parentElement;
    if (cb.checked) {
      if (exerciseState.memberIds.indexOf(aid) < 0) exerciseState.memberIds.push(aid);
      label.classList.add('modal-select__member-chip--checked');
    } else {
      exerciseState.memberIds = exerciseState.memberIds.filter(function (id) { return id !== aid; });
      label.classList.remove('modal-select__member-chip--checked');
    }
  };

  function closeTeamSelector() {
    var overlay = document.getElementById('team-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  function confirmTeamSelection() {
    if (!exerciseState.teamId) {
      showToast('请先选择一个团队', 'warn');
      return;
    }
    showToast('已选择团队: ' + exerciseState.teamName + ' (' + exerciseState.memberIds.length + ' 名成员)', 'info');
    updateGuideTags();
    closeTeamSelector();
  }

  // ── 场景选择 ──

  var DEFAULT_SCENES = [
    { id: 'council-hall',   name: '议事厅', icon: '🏛️', desc: '团队决策与任务分配' },
    { id: 'extraction-lab', name: '萃取室', icon: '⚗️', desc: '知识萃取与技能沉淀' },
    { id: 'workshop',       name: '工作坊', icon: '🔧', desc: '工具开发与调试' },
    { id: 'knowledge-base', name: '知识库', icon: '📚', desc: '经验检索与知识管理' },
    { id: 'training-ground',name: '演练场', icon: '🎯', desc: '仿真推演与压力测试' },
    { id: 'rest-area',      name: '休息区', icon: '☕', desc: '自由交流与创意发散' }
  ];

  async function openSceneSelector() {
    var overlay = document.getElementById('scene-overlay');
    if (!overlay) return;
    overlay.style.display = 'flex';
    var list = document.getElementById('scene-list');
    var loading = document.getElementById('scene-loading');
    if (list) list.innerHTML = '';
    if (loading) loading.style.display = '';
    document.getElementById('scene-hint').textContent = '从数字孪生的 3D 环境空间中选择演练场地';

    // 尝试从后端拉取孪生场景数据
    var scenes = DEFAULT_SCENES;
    try {
      var resp = await fetch('/api/v1/agent-config/digital-twin/state');
      if (resp.ok) {
        var data = await resp.json();
        var rooms = data.rooms || data.state?.rooms || [];
        if (rooms.length) {
          scenes = rooms.map(function (r) {
            var name = r.name || r.room_name || '未知房间';
            var iconMap = { '议事厅': '🏛️', '萃取室': '⚗️', '工作坊': '🔧', '知识库': '📚', '演练场': '🎯', '休息区': '☕' };
            return {
              id: r.id || r.room_id || name,
              name: name,
              icon: iconMap[name] || '📍',
              desc: r.description || ''
            };
          });
        }
      }
    } catch (e) { /* fallback to defaults */ }

    if (loading) loading.style.display = 'none';
    renderSceneList(scenes, list);
  }

  function renderSceneList(scenes, container) {
    if (!container) return;
    container.innerHTML = scenes.map(function (s) {
      var selected = exerciseState.sceneId === s.id ? ' modal-select__item--selected' : '';
      return '<div class="modal-select__item' + selected + '" data-scene-id="' + s.id + '" data-scene-name="' + escHtml(s.name) + '" onclick="selectSceneItem(this, \'' + escJs(s.id) + '\', \'' + escJs(s.name) + '\')">'
        + '<span class="modal-select__item-icon">' + (s.icon || '📍') + '</span>'
        + '<span class="modal-select__item-name">' + escHtml(s.name) + '</span>'
        + (s.desc ? '<span class="modal-select__item-meta">' + escHtml(s.desc) + '</span>' : '')
        + '</div>';
    }).join('');
  }

  window.selectSceneItem = function (el, sid, sname) {
    document.querySelectorAll('#scene-list .modal-select__item').forEach(function (it) { it.classList.remove('modal-select__item--selected'); });
    el.classList.add('modal-select__item--selected');
    exerciseState.sceneId = sid;
    exerciseState.sceneName = sname;
    document.getElementById('scene-hint').textContent = '已选场景: ' + sname;
    updateGuideTags();
  };

  function closeSceneSelector() {
    var overlay = document.getElementById('scene-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  function confirmSceneSelection() {
    if (!exerciseState.sceneId) {
      showToast('请先选择一个场景', 'warn');
      return;
    }
    showToast('已选择场景: ' + exerciseState.sceneName, 'info');
    sw3dSetRoom(exerciseState.sceneId);
    updateGuideTags();
    closeSceneSelector();
  }

  // ── 辅助 ──
  function escHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function escJs(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
  }

  // ── Init ──
  function bootSandboxTwin() {
    if (window._sandboxTwinBooted) return;
    window._sandboxTwinBooted = true;
    setupTabs('input-tabs', 'input-content');
    setupTabs('output-tabs', 'output-content');
    bindPipelineNodes();
    initCollabGraph();
    bindRuntimeBar();
    loadStats();
    loadRuntimeStatus();
    renderSessionHistory();
    startAutoRefresh();
    setActiveLayer('L3'); // 默认 L3
    loadL1AgentGridFromStats();
    loadSessionHistoryFromBackend();
    showGuideBanner();
  }
  window._sandboxTwinBoot = bootSandboxTwin;
  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', bootSandboxTwin);
  } else {
    setTimeout(bootSandboxTwin, 0);
  }
  window.addEventListener('load', bootSandboxTwin);
})();
