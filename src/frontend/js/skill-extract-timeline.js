/**
 * AgentsGroup2026 — Skill Extraction Timeline + WebSocket Module
 *
 * Features:
 *  - Vertical timeline with operation log nodes
 *  - Completion cards (realtime record + review annotation) attached to each node
 *  - WebSocket real-time card status updates
 *  - Phase step cards with progress lock mechanism
 *
 * Usage:
 *   <script src="/js/skill-extract-timeline.js"></script>
 *   Then call: SkillExtractTimeline.init({ containerId: 'timeline-panel', teamId: 'default' });
 */
(function () {
  'use strict';

  const WS_PATH = '/api/v1/skill-extract/ws';
  const RECONNECT_DELAY_MS = 3000;
  const MAX_RECONNECT_ATTEMPTS = 10;
  const PING_INTERVAL_MS = 25000;

  /* ─── Phase Definitions ────────────────────────────────────── */
  const PHASES = [
    { key: 'extract',       label: '📥 原始数据提取',   icon: '📥', order: 0 },
    { key: 'llm_prefill',   label: '🤖 LLM 预填草稿',   icon: '🤖', order: 1 },
    { key: 'review',        label: '🔍 人工审核',       icon: '🔍', order: 2 },
    { key: 'approve',       label: '✅ 质量审批',       icon: '✅', order: 3 },
    { key: 'index',         label: '📇 技能入库索引',   icon: '📇', order: 4 },
    { key: 'verify',        label: '🧪 验证校验',       icon: '🧪', order: 5 },
    { key: 'complete',      label: '🏁 萃取完成',       icon: '🏁', order: 6 },
  ];

  const PHASE_MAP = {};
  PHASES.forEach(p => { PHASE_MAP[p.key] = p; });

  /* ─── Status Badge Styles ──────────────────────────────────── */
  const STATUS_STYLES = {
    pending:   { bg: 'rgba(255,255,255,0.04)', border: '#1e2a3a', text: '#8b949e', dot: '#8b949e', label: '待处理' },
    recording: { bg: 'rgba(88,166,255,0.08)',  border: '#58a6ff', text: '#58a6ff', dot: '#58a6ff', label: '记录中', pulse: true },
    recorded:  { bg: 'rgba(63,185,80,0.08)',   border: '#3fb950', text: '#3fb950', dot: '#3fb950', label: '已记录' },
    reviewing: { bg: 'rgba(210,153,34,0.08)',  border: '#d29922', text: '#d29922', dot: '#d29922', label: '审核中', pulse: true },
    reviewed:  { bg: 'rgba(163,113,247,0.08)', border: '#a371f7', text: '#a371f7', dot: '#a371f7', label: '已审核' },
    approved:  { bg: 'rgba(63,185,80,0.12)',   border: '#3fb950', text: '#3fb950', dot: '#3fb950', label: '已批准' },
    rejected:  { bg: 'rgba(248,81,73,0.08)',   border: '#f85149', text: '#f85149', dot: '#f85149', label: '已驳回' },
    error:     { bg: 'rgba(248,81,73,0.12)',   border: '#f85149', text: '#f85149', dot: '#f85149', label: '错误' },
  };

  /* ─── Lock Reason Labels ───────────────────────────────────── */
  const LOCK_LABELS = {
    not_started:         '⏸ 尚未开始',
    in_progress:         '🔄 进行中',
    waiting_review:      '👁 等待审核',
    waiting_approval:    '🔐 等待批准',
    dependency_blocked:  '🚫 前置步骤未完成',
    completed:           '✅ 已完成',
  };

  /* ─── State ────────────────────────────────────────────────── */
  let _config = null;
  let _ws = null;
  let _reconnectAttempts = 0;
  let _reconnectTimer = null;
  let _pingTimer = null;
  let _nodes = {};          // node_id -> node data
  let _nodeOrder = [];      // ordered node ids
  let _extractionId = null;
  let _isConnected = false;

  /* ─── DOM References (set on init) ──────────────────────────── */
  let _$container = null;
  let _$phaseBar = null;
  let _$timeline = null;
  let _$cardPanel = null;
  let _$statusDot = null;
  let _$connLabel = null;

  /* ══════════════════════════════════════════════════════════════
     Public API
     ══════════════════════════════════════════════════════════════ */

  window.SkillExtractTimeline = {
    /**
     * Initialize the timeline component.
     * @param {Object} opts
     * @param {string} opts.containerId - DOM element ID to mount into
     * @param {string} [opts.teamId='default'] - Team ID for WebSocket
     * @param {string} [opts.wsPath] - Custom WebSocket path
     */
    init(opts = {}) {
      _config = Object.assign({
        containerId: 'timeline-panel',
        teamId: 'default',
        wsPath: WS_PATH,
      }, opts);

      const el = document.getElementById(_config.containerId);
      if (!el) {
        console.warn('[SkillExtractTimeline] Container #' + _config.containerId + ' not found, creating');
        _createContainer(_config.containerId);
      }
      _render();
      _connectWS();
    },

    /** Subscribe to a specific extraction process. */
    subscribe(extractionId) {
      _extractionId = extractionId;
      if (_ws && _ws.readyState === WebSocket.OPEN) {
        _ws.send(JSON.stringify({ type: 'subscribe', extraction_id: extractionId }));
      }
    },

    /** Manually add a log node (e.g., from SSE fallback). */
    addNode(nodeData) {
      _upsertNode(nodeData);
      _renderTimeline();
    },

    /** Manually update a card. */
    updateCard(cardData) {
      const nodeId = cardData.node_id;
      if (!nodeId || !_nodes[nodeId]) return;
      const node = _nodes[nodeId];

      if (!node.cards) node.cards = {};
      node.cards[cardData.card_type || 'default'] = Object.assign(
        node.cards[cardData.card_type || 'default'] || {},
        cardData
      );
      // Also update node status if card status is terminal
      if (['approved', 'rejected', 'error'].includes(cardData.status)) {
        node.status = cardData.status;
      }
      _renderTimeline();
    },

    /** Update phase progress (with lock state). */
    updatePhase(phaseData) {
      _renderPhaseBar(phaseData);
    },

    /** Toggle timeline panel visibility. */
    toggle() {
      if (_$container) {
        _$container.classList.toggle('sk-timeline--hidden');
      }
    },

    /** Show the timeline panel. */
    show() {
      if (_$container) _$container.classList.remove('sk-timeline--hidden');
    },

    /** Hide the timeline panel. */
    hide() {
      if (_$container) _$container.classList.add('sk-timeline--hidden');
    },

    /** Disconnect WebSocket. */
    disconnect() {
      _cleanupWS();
    },

    /** Get connection status. */
    get isConnected() { return _isConnected; },

    /** Get all nodes. */
    get nodes() { return _nodes; },

    /** Get extraction ID. */
    get extractionId() { return _extractionId; },
  };

  /* ══════════════════════════════════════════════════════════════
     Container & Initial Render
     ══════════════════════════════════════════════════════════════ */

  function _createContainer(id) {
    const div = document.createElement('div');
    div.id = id;
    div.className = 'sk-timeline-panel';
    document.body.appendChild(div);
  }

  function _render() {
    const container = document.getElementById(_config.containerId);
    if (!container) return;
    _$container = container;

    container.innerHTML = `
      <div class="sk-timeline-header">
        <div class="sk-timeline-header-left">
          <span class="sk-timeline-dot" id="sk-ws-dot"></span>
          <span class="sk-timeline-title">⏱ 技能萃取时间轴</span>
        </div>
        <div class="sk-timeline-header-right">
          <span class="sk-timeline-conn-label" id="sk-conn-label">连接中...</span>
          <button class="sk-timeline-close-btn" onclick="SkillExtractTimeline.hide()">✕</button>
        </div>
      </div>
      <div class="sk-phase-bar" id="sk-phase-bar"></div>
      <div class="sk-timeline-body">
        <div class="sk-timeline-track" id="sk-timeline-track">
          <div class="sk-timeline-empty">等待萃取数据...</div>
        </div>
      </div>
      <div class="sk-card-detail" id="sk-card-detail" style="display:none"></div>
    `;

    _$phaseBar = document.getElementById('sk-phase-bar');
    _$timeline = document.getElementById('sk-timeline-track');
    _$cardPanel = document.getElementById('sk-card-detail');
    _$statusDot = document.getElementById('sk-ws-dot');
    _$connLabel = document.getElementById('sk-conn-label');

    _renderPhaseBar();
  }

  /* ══════════════════════════════════════════════════════════════
     Phase Bar (Step Cards with Progress Lock)
     ══════════════════════════════════════════════════════════════ */

  function _renderPhaseBar(currentData) {
    if (!_$phaseBar) return;
    const currentPhase = (currentData && currentData.phase) || 'extract';
    const currentOrder = PHASE_MAP[currentPhase] ? PHASE_MAP[currentPhase].order : 0;

    let html = '';
    PHASES.forEach((p, idx) => {
      const isPast = idx < currentOrder;
      const isCurrent = idx === currentOrder;
      const isFuture = idx > currentOrder;

      let phaseState = 'future';
      let lockReason = '';
      let progressPct = 0;
      let statusLabel = '';

      if (isPast) {
        phaseState = 'completed';
        progressPct = 100;
        statusLabel = '✅';
      } else if (isCurrent) {
        phaseState = 'active';
        progressPct = (currentData && currentData.progress_pct) || 0;
        if (currentData && currentData.is_locked) {
          lockReason = currentData.lock_reason || 'dependency_blocked';
          statusLabel = '🔒';
        } else {
          statusLabel = '🔄';
        }
      } else {
        phaseState = 'locked';
        progressPct = 0;
        lockReason = 'not_started';
        statusLabel = '🔒';
      }

      html += `
        <div class="sk-phase-step sk-phase--${phaseState}" title="${p.label}">
          <div class="sk-phase-icon">${p.icon}</div>
          <div class="sk-phase-label">${p.label}</div>
          <div class="sk-phase-progress">
            <div class="sk-phase-fill" style="width:${progressPct}%"></div>
          </div>
          <div class="sk-phase-status">${statusLabel}</div>
          ${lockReason ? `<div class="sk-phase-lock-hint">${LOCK_LABELS[lockReason] || lockReason}</div>` : ''}
        </div>
      `;
    });

    _$phaseBar.innerHTML = html;
  }

  /* ══════════════════════════════════════════════════════════════
     Timeline Rendering
     ══════════════════════════════════════════════════════════════ */

  function _renderTimeline() {
    if (!_$timeline) return;

    if (_nodeOrder.length === 0) {
      _$timeline.innerHTML = '<div class="sk-timeline-empty">等待萃取数据...</div>';
      return;
    }

    let html = '<div class="sk-timeline-line"></div>';
    _nodeOrder.forEach((nodeId, idx) => {
      const node = _nodes[nodeId];
      if (!node) return;
      const st = STATUS_STYLES[node.status] || STATUS_STYLES.pending;
      const timeStr = node.timestamp ? _formatTime(node.timestamp) : '';

      html += `
        <div class="sk-tl-node" data-node-id="${nodeId}" onclick="SkillExtractTimeline._onNodeClick('${nodeId}')">
          <div class="sk-tl-node-dot" style="background:${st.dot};${st.pulse ? 'animation:sk-pulse 1.5s infinite;' : ''}"></div>
          <div class="sk-tl-node-card" style="background:${st.bg};border-color:${st.border}">
            <div class="sk-tl-node-header">
              <span class="sk-tl-node-phase">${PHASE_MAP[node.phase] ? PHASE_MAP[node.phase].icon : '📌'} ${node.title || node.phase}</span>
              <span class="sk-tl-node-badge" style="background:${st.border};color:${st.text}">${st.label}</span>
              ${node.agent_id ? `<span class="sk-tl-node-agent">🤖 ${node.agent_id}</span>` : ''}
            </div>
            ${node.description ? `<div class="sk-tl-node-desc">${node.description}</div>` : ''}
            <div class="sk-tl-node-footer">
              <span class="sk-tl-node-time">${timeStr}</span>
              ${node.cards ? `<span class="sk-tl-node-card-count">📋 ${Object.keys(node.cards).length} 卡片</span>` : ''}
            </div>
            <!-- Completion Cards (inline preview) -->
            ${_renderInlineCards(node)}
          </div>
        </div>
      `;
    });

    _$timeline.innerHTML = html;
  }

  function _renderInlineCards(node) {
    if (!node.cards || Object.keys(node.cards).length === 0) return '';
    let html = '<div class="sk-inline-cards">';
    Object.entries(node.cards).forEach(([cardType, card]) => {
      const st = STATUS_STYLES[card.status] || STATUS_STYLES.pending;
      html += `
        <div class="sk-inline-card" style="border-left-color:${st.border}" onclick="event.stopPropagation();SkillExtractTimeline._onCardClick('${node.node_id || node.id}','${cardType}')">
          <div class="sk-inline-card-header">
            <span>📝 ${cardType === 'realtime_record' ? '实时记录' : cardType === 'review_annotation' ? '回顾注释' : cardType}</span>
            <span style="color:${st.text};font-size:10px">${st.label}</span>
          </div>
          ${card.realtime_record ? `<div class="sk-inline-card-preview">${_truncate(card.realtime_record, 60)}</div>` : ''}
          ${card.review_annotation ? `<div class="sk-inline-card-preview sk-inline-card-review">💬 ${_truncate(card.review_annotation, 60)}</div>` : ''}
        </div>
      `;
    });
    html += '</div>';
    return html;
  }

  /* ══════════════════════════════════════════════════════════════
     Card Detail Panel (expanded view)
     ══════════════════════════════════════════════════════════════ */

  function _showCardDetail(nodeId, cardType) {
    const node = _nodes[nodeId];
    if (!node) return;
    const card = node.cards ? node.cards[cardType] : null;
    if (!card) return;

    const st = STATUS_STYLES[card.status] || STATUS_STYLES.pending;
    let html = `
      <div class="sk-card-detail-header">
        <span>📋 补全卡片详情</span>
        <button class="sk-timeline-close-btn" onclick="document.getElementById('sk-card-detail').style.display='none'">✕</button>
      </div>
      <div class="sk-card-detail-body">
        <div class="sk-card-detail-meta">
          <span>节点: ${node.title || node.phase}</span>
          <span class="sk-tl-node-badge" style="background:${st.border};color:${st.text}">${st.label}</span>
        </div>
        <div class="sk-card-detail-field">
          <label>📝 实时记录 (Realtime Record)</label>
          <div class="sk-card-detail-content">${card.realtime_record || '<em style="color:#8b949e">暂无实时记录...</em>'}</div>
        </div>
        <div class="sk-card-detail-field">
          <label>💬 回顾注释 (Review Annotation)</label>
          <div class="sk-card-detail-content sk-card-detail-review">${card.review_annotation || '<em style="color:#8b949e">等待审核人员添加注释...</em>'}</div>
        </div>
        ${card.reviewer ? `<div class="sk-card-detail-field"><label>👤 审核人</label><span>${card.reviewer}</span></div>` : ''}
        ${card.timestamp ? `<div class="sk-card-detail-field"><label>🕐 更新时间</label><span>${_formatTime(card.timestamp)}</span></div>` : ''}
        ${card.metadata ? `<div class="sk-card-detail-field"><label>📎 元数据</label><pre class="sk-card-detail-meta-json">${JSON.stringify(card.metadata, null, 2)}</pre></div>` : ''}
      </div>
    `;
    _$cardPanel.innerHTML = html;
    _$cardPanel.style.display = 'block';
  }

  /* ══════════════════════════════════════════════════════════════
     WebSocket
     ══════════════════════════════════════════════════════════════ */

  function _connectWS() {
    _cleanupWS();

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = location.host;
    const url = `${proto}//${host}${_config.wsPath}?team_id=${encodeURIComponent(_config.teamId)}`;

    try {
      _ws = new WebSocket(url);
    } catch (e) {
      console.error('[SkillExtractTimeline] WebSocket construction failed:', e);
      _scheduleReconnect();
      return;
    }

    _ws.onopen = () => {
      _isConnected = true;
      _reconnectAttempts = 0;
      _updateConnectionUI(true);
      console.log('[SkillExtractTimeline] WebSocket connected');

      if (_extractionId) {
        _ws.send(JSON.stringify({ type: 'subscribe', extraction_id: _extractionId }));
      }
      _startPing();
    };

    _ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        _handleMessage(msg);
      } catch (e) {
        console.warn('[SkillExtractTimeline] Bad message:', e);
      }
    };

    _ws.onclose = (event) => {
      _isConnected = false;
      _stopPing();
      _updateConnectionUI(false);
      console.log('[SkillExtractTimeline] WebSocket closed:', event.code, event.reason);
      if (event.code !== 1000) {
        _scheduleReconnect();
      }
    };

    _ws.onerror = (err) => {
      console.error('[SkillExtractTimeline] WebSocket error:', err);
    };
  }

  function _handleMessage(msg) {
    switch (msg.type) {
      case 'connected':
        console.log('[SkillExtractTimeline] Connected ack:', msg.message);
        break;

      case 'subscribed':
        _extractionId = msg.extraction_id;
        console.log('[SkillExtractTimeline] Subscribed to extraction:', msg.extraction_id);
        break;

      case 'log_node':
        _upsertNode(msg);
        _renderTimeline();
        break;

      case 'card_update':
        SkillExtractTimeline.updateCard(msg);
        break;

      case 'phase_progress':
        _renderPhaseBar(msg);
        break;

      case 'extraction_completed':
        _renderPhaseBar({ phase: 'complete', progress_pct: 100 });
        console.log('[SkillExtractTimeline] Extraction completed:', msg.summary);
        break;

      case 'error':
        console.error('[SkillExtractTimeline] Server error:', msg.message);
        break;

      case 'pong':
        // heartbeat response, no action needed
        break;

      default:
        console.debug('[SkillExtractTimeline] Unknown message type:', msg.type);
    }
  }

  function _upsertNode(nodeData) {
    const nodeId = nodeData.node_id || nodeData.id || _generateId();
    if (!_nodes[nodeId]) {
      _nodeOrder.push(nodeId);
    }
    _nodes[nodeId] = Object.assign(_nodes[nodeId] || {}, nodeData, {
      node_id: nodeId,
    });
  }

  function _startPing() {
    _stopPing();
    _pingTimer = setInterval(() => {
      if (_ws && _ws.readyState === WebSocket.OPEN) {
        _ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, PING_INTERVAL_MS);
  }

  function _stopPing() {
    if (_pingTimer) { clearInterval(_pingTimer); _pingTimer = null; }
  }

  function _scheduleReconnect() {
    if (_reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.warn('[SkillExtractTimeline] Max reconnect attempts reached');
      _updateConnectionUI(false, '连接失败');
      return;
    }
    _reconnectAttempts++;
    const delay = RECONNECT_DELAY_MS * Math.min(_reconnectAttempts, 5);
    console.log(`[SkillExtractTimeline] Reconnecting in ${delay}ms (attempt ${_reconnectAttempts})`);
    _reconnectTimer = setTimeout(() => _connectWS(), delay);
  }

  function _cleanupWS() {
    _stopPing();
    if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null; }
    if (_ws) {
      _ws.onopen = null;
      _ws.onmessage = null;
      _ws.onclose = null;
      _ws.onerror = null;
      if (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING) {
        _ws.close(1000, 'client reinit');
      }
      _ws = null;
    }
    _isConnected = false;
  }

  function _updateConnectionUI(connected, label) {
    if (_$statusDot) {
      _$statusDot.className = 'sk-timeline-dot' + (connected ? ' sk-timeline-dot--ok' : ' sk-timeline-dot--err');
    }
    if (_$connLabel) {
      _$connLabel.textContent = label || (connected ? '已连接' : '断开');
      _$connLabel.style.color = connected ? 'var(--accent2, #3fb950)' : 'var(--error, #f85149)';
    }
  }

  /* ══════════════════════════════════════════════════════════════
     Event Handlers (exposed on public API for onclick usage)
     ══════════════════════════════════════════════════════════════ */

  window.SkillExtractTimeline._onNodeClick = function (nodeId) {
    // Toggle card detail for the first card of this node
    const node = _nodes[nodeId];
    if (!node || !node.cards) return;
    const firstCardType = Object.keys(node.cards)[0];
    if (firstCardType) {
      _showCardDetail(nodeId, firstCardType);
    }
  };

  window.SkillExtractTimeline._onCardClick = function (nodeId, cardType) {
    _showCardDetail(nodeId, cardType);
  };

  /* ══════════════════════════════════════════════════════════════
     Helpers
     ══════════════════════════════════════════════════════════════ */

  function _generateId() {
    return 'node_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
  }

  function _formatTime(isoStr) {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) { return isoStr; }
  }

  function _truncate(str, maxLen) {
    if (!str) return '';
    return str.length > maxLen ? str.slice(0, maxLen) + '...' : str;
  }

})();
