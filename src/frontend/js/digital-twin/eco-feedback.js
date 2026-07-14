/**
 * eco-feedback.js — ③ 适者反馈台
 * Skill 写回 agent.skills + 协作写回 metadata.eco_collab → 再进成本优化
 */
(function () {
  'use strict';

  var _fbState = {
    result: null,
    integration: null,
    collabReport: null,
    channelReport: null,
    relationReport: null,
    skillApplied: false,
    collabApplied: false,
    channelApplied: false,
    relationApplied: false,
    skipped: false,
    skipReason: '',
    fingerprint: '',
  };
  // skill_id → 可读名 / 描述缓存（打开反馈台时加载）
  var _nameMap = {};
  var _metaMap = {}; // skill_id → { name, description, instructions? }

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function _isOpaqueId(s) {
    s = String(s || '');
    // 8 位 hex / uuid 短 id —— 单独看无法理解能力
    return /^[0-9a-f]{6,12}$/i.test(s) || /^[0-9a-f-]{16,}$/i.test(s);
  }
  function _sk(s) {
    var id = String(s == null ? '' : s);
    if (!id) return '';
    var meta = _metaMap[id] || {};
    var nm = _nameMap[id] || meta.name || '';
    if (nm && nm !== id && !_isOpaqueId(nm)) {
      return _isOpaqueId(id) ? (nm + ' · ' + id.slice(0, 8)) : nm;
    }
    if (window._ecoSkillLabel) {
      var lab = window._ecoSkillLabel(id);
      if (lab && lab !== id && !_isOpaqueId(lab)) return lab + (_isOpaqueId(id) ? ' · ' + id.slice(0, 8) : '');
    }
    if (_isOpaqueId(id)) return '（未命名技能）' + id.slice(0, 8);
    return id.replace(/_/g, ' ');
  }
  function _ingestMeta(sid, fields) {
    if (!sid) return;
    sid = String(sid);
    fields = fields || {};
    var prev = _metaMap[sid] || {};
    var nm = (fields.name || fields.slug || fields.title || prev.name || '').trim();
    var desc = (fields.description || fields.desc || prev.description || '').trim();
    var inst = (fields.instructions || prev.instructions || '').trim();
    if (nm && nm !== sid) _nameMap[sid] = nm;
    _metaMap[sid] = {
      name: nm || prev.name || '',
      description: desc,
      instructions: inst,
      category: fields.category || prev.category || '',
      source: fields.source || prev.source || '',
    };
  }
  function _ingestName(sid, name) {
    _ingestMeta(sid, { name: name });
  }
  /** 加载团队技能库 + 分类三池 + 全局目录（含 description） */
  function _loadSkillNames(teamId) {
    if (!teamId) return Promise.resolve();
    var pTeam = _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(teamId))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d) return;
        if (d.skills && typeof d.skills === 'object') {
          Object.keys(d.skills).forEach(function (sid) {
            _ingestMeta(sid, d.skills[sid] || {});
          });
        }
      }).catch(function () {});
    var pTeamList = _fetch('/api/v1/agent-config/teams/' + encodeURIComponent(teamId) + '/skills')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (list) {
        var arr = Array.isArray(list) ? list : [];
        arr.forEach(function (s) {
          if (!s) return;
          _ingestMeta(s.skill_id || s.id, s);
        });
      }).catch(function () {});
    var pCls = _fetch('/api/v1/skill-classification/teams/' + encodeURIComponent(teamId))
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (view) {
        if (!view) return;
        var pools = view.pools || {};
        Object.keys(pools).forEach(function (pk) {
          (pools[pk] || []).forEach(function (item) {
            if (!item) return;
            _ingestMeta(item.skill_id || item.id, {
              name: item.name || item.skill_name,
              description: (item.reasons && item.reasons.join) ? item.reasons.join('；') : '',
            });
          });
        });
      }).catch(function () {});
    var pAll = _fetch('/api/v1/agent-config/skills')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (list) {
        var arr = Array.isArray(list) ? list : (list && list.skills) || [];
        arr.forEach(function (s) {
          if (!s) return;
          _ingestMeta(s.skill_id || s.id, s);
        });
      }).catch(function () {});
    return Promise.all([pTeam, pTeamList, pCls, pAll]);
  }

  /** 与团队技能列表 📖 同语义：点开看 name / 描述 / 指令 */
  window.ecoFeedbackViewSkill = function (skillId, ev) {
    if (ev) { ev.preventDefault(); ev.stopPropagation(); }
    skillId = String(skillId || '');
    if (!skillId) return;
    var meta = _metaMap[skillId] || {};
    var title = meta.name || _nameMap[skillId] || skillId;
    var show = function (extra) {
      var desc = (extra && extra.description) || meta.description || '（暂无 description）';
      var inst = (extra && extra.instructions) || meta.instructions || '';
      var tools = (extra && extra.required_tools) || meta.required_tools || [];
      var toolsLine = Array.isArray(tools) ? tools.join(', ') : String(tools || '');
      var body =
        '名称: ' + title + '\n'
        + 'ID: ' + skillId + '\n'
        + (meta.category ? '类别: ' + meta.category + '\n' : '')
        + (meta.source ? '来源: ' + meta.source + '\n' : '')
        + (toolsLine ? '所需工具: ' + toolsLine + '\n' : '')
        + '\n--- 描述 ---\n' + desc
        + (inst ? '\n\n--- 指令 ---\n' + String(inst).slice(0, 4000) : '\n\n（暂无 instructions，可到「智能体团队 → 技能」点 📖 查看完整内容）');
      window.alert(body);
    };
    // 优先缓存；再拉 instructions API（与 tools-skills viewSkillInstructions 同源）
    _fetch('/api/v1/agent-config/skills/' + encodeURIComponent(skillId) + '/instructions')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (r) {
        if (r) {
          _ingestMeta(skillId, {
            name: r.name,
            description: r.description,
            instructions: r.instructions,
          });
          show({
            description: r.description || meta.description,
            instructions: r.instructions,
            required_tools: r.required_tools,
          });
        } else {
          show();
        }
      }).catch(function () { show(); });
  };
  function _fetch(url, opts) {
    opts = opts || {};
    opts.credentials = opts.credentials || 'same-origin';
    return fetch(url, opts);
  }
  /** 反馈台解析当前团队（多源，避免 team 空导致通道 before 空白） */
  function _resolveTeamId(result) {
    var tid = window._selectedTeamId || '';
    if (tid) return String(tid);
    try {
      if (window.AGCtx && typeof window.AGCtx.get === 'function') {
        tid = window.AGCtx.get('team') || window.AGCtx.get('team_id') || '';
        if (tid) return String(tid);
      }
    } catch (e) { /* ignore */ }
    result = result || _fbState.result || {};
    if (result.team_id) return String(result.team_id);
    var c = result.contract || {};
    if (c.team_id) return String(c.team_id);
    var p = c.provenance || {};
    if (p.team_id) return String(p.team_id);
    try {
      tid = localStorage.getItem('ag_current_team')
        || localStorage.getItem('ag_ctx_team')
        || '';
      if (tid) return String(tid);
    } catch (e2) { /* ignore */ }
    // ranking.population 常= team_id（aws-ops）
    var rank = result.final_ranking || [];
    if (rank[0] && rank[0].population) return String(rank[0].population);
    return '';
  }
  /** API 无 before 时，用 ranking 做同队编制 mesh（本地兜底，保证图不空白） */
  function _localTeamBeforeFromResult(result) {
    var rank = (result && result.final_ranking) || [];
    var ids = [];
    var seen = {};
    rank.forEach(function (r) {
      var id = String((r && r.agent_id) || '');
      if (!id || seen[id]) return;
      seen[id] = true;
      ids.push(id);
    });
    ids.sort();
    var edges = [];
    for (var i = 0; i < ids.length; i++) {
      for (var j = i + 1; j < ids.length; j++) {
        edges.push({
          source_agent_id: ids[i],
          target_id: ids[j],
          kind: 'agent_agent',
          rel_type: 'peer',
          note: 'team_collab_local',
          status: 'peer',
          layer: 'peer',
          undirected: true,
        });
      }
    }
    return edges;
  }
  function setStatus(msg) {
    var el = $('eco-fb-status');
    if (el) el.textContent = msg || '';
  }
  function setStep(n) {
    var root = $('eco2-steps');
    if (!root) return;
    root.querySelectorAll('.eco2-step').forEach(function (el) {
      var sn = parseInt(el.getAttribute('data-step') || '0', 10);
      el.classList.remove('eco2-step-active', 'eco2-step-done');
      if (sn < n) el.classList.add('eco2-step-done');
      if (sn === n) el.classList.add('eco2-step-active');
    });
  }
  function _fpFromResult(result) {
    var c = (result && result.contract) || {};
    var p = c.provenance || {};
    return p.fingerprint || c.plan_id || c.topic || '';
  }
  function _strategy() {
    var sel = $('eco-fb-collab-strategy');
    return (sel && sel.value) || 'blend';
  }
  function _persistFeedback(extra) {
    try {
      var teamId = window._selectedTeamId || '';
      var payload = Object.assign({
        team_id: teamId,
        fingerprint: _fbState.fingerprint,
        skill_applied: _fbState.skillApplied,
        collab_applied: _fbState.collabApplied,
        channel_applied: _fbState.channelApplied,
        relation_applied: _fbState.relationApplied,
        ts: Date.now(),
      }, extra || {});
      sessionStorage.setItem('eco_feedback_status', JSON.stringify(payload));
    } catch (e) { /* ignore */ }
  }

  function _buildBindingsFromChecks() {
    var box = $('eco-fb-skill-table');
    if (!box) return [];
    var byAgent = {};
    box.querySelectorAll('input[type=checkbox][data-aid][data-skill]:checked').forEach(function (cb) {
      var aid = cb.getAttribute('data-aid');
      var sk = cb.getAttribute('data-skill');
      if (!aid || !sk) return;
      if (!byAgent[aid]) byAgent[aid] = { agent_id: aid, add_skills: [], reason: 'eco_feedback_ui' };
      byAgent[aid].add_skills.push(sk);
    });
    return Object.keys(byAgent).map(function (k) { return byAgent[k]; });
  }

  function _buildCollabFromChecks() {
    var box = $('eco-fb-collab-table');
    if (!box) return [];
    var out = [];
    box.querySelectorAll('.eco-fb-collab-row').forEach(function (row) {
      var cb = row.querySelector('input[type=checkbox][data-collab-aid]');
      if (!cb || !cb.checked) return;
      var aid = cb.getAttribute('data-collab-aid');
      var collab = {};
      ['share_tendency', 'signal_tendency', 'follow_tendency', 'mate_choosiness'].forEach(function (d) {
        var inp = row.querySelector('input[data-dim="' + d + '"]');
        collab[d] = inp ? Number(inp.value) : 0.5;
      });
      out.push({
        agent_id: aid,
        collab: collab,
        survival_ticks: parseInt(row.getAttribute('data-t') || '0', 10),
        strategy: _strategy(),
        reason: 'eco_feedback_ui',
      });
    });
    return out;
  }

  function _renderSkillTable(result, integration) {
    var box = $('eco-fb-skill-table');
    if (!box) return;
    var ranking = (result && result.final_ranking) || [];
    var att = (result && result.survival_attribution) || {};
    var recs = (integration && integration.recommended_bindings) || [];
    var recMap = {};
    var srcMap = {};
    var boundMap = {};
    recs.forEach(function (b) {
      if (!b || !b.agent_id) return;
      recMap[b.agent_id] = Array.isArray(b.add_skills) ? b.add_skills : [];
      srcMap[b.agent_id] = b.skill_sources && typeof b.skill_sources === 'object' ? b.skill_sources : {};
      boundMap[b.agent_id] = Array.isArray(b.already_bound) ? b.already_bound : [];
    });
    var top = ranking.slice().sort(function (a, b) {
      return (b.survival_ticks || 0) - (a.survival_ticks || 0);
    }).slice(0, 12);
    if (!top.length) {
      box.innerHTML = '<div class="eco2-empty">无排行数据</div>';
      return;
    }
    // 仅未绑定候选；禁止回退到 skill_genome（那是已绑定）
    var html = '<div class="meta" style="margin-bottom:6px">只勾选<strong>未绑定</strong>候选'
      + '（来源: plan_demand / dominant / <b>reserve</b> / team_library）。已绑定不会出现。</div>';
    var anyAdd = false;
    top.forEach(function (r) {
      if (!r) return;
      var aid = r.agent_id || '';
      var add = Array.isArray(recMap[aid]) ? recMap[aid] : [];
      var sources = srcMap[aid] || {};
      // 修复: boundMap[aid] 可能 undefined（该 agent 无 recommend 行）
      var boundFromRec = Array.isArray(boundMap[aid]) ? boundMap[aid] : [];
      var genome = Array.isArray(r.skill_genome) ? r.skill_genome : [];
      var bound = boundFromRec.length ? boundFromRec : genome;
      var a = att[aid] || {};
      var skp = r.attr_skill_share != null ? r.attr_skill_share : a.skill_share;
      var cop = r.attr_collab_share != null ? r.attr_collab_share : a.collab_share;
      if (add.length) anyAdd = true;
      var checks = add.map(function (s) {
        var src = sources[s] || 'unbound';
        var sidAttr = String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        return '<span style="display:inline-flex;align-items:center;gap:2px;margin:2px 6px 2px 0;flex-wrap:wrap">'
          + '<label title="来源: ' + esc(src) + '"><input type="checkbox" data-aid="' + esc(aid) + '" data-skill="' + esc(s) + '" checked> '
          + esc(_sk(s))
          + ' <span class="meta">[' + esc(src) + ']</span></label>'
          + '<button type="button" class="btn" title="查看 skill 描述与指令（同团队技能列表 📖）" '
          + 'onclick="ecoFeedbackViewSkill(\'' + sidAttr + '\',event)" '
          + 'style="font-size:11px;padding:0 5px;line-height:1.4;min-width:22px;color:var(--cyan)">📖</button>'
          + '</span>';
      }).join(' ');
      var boundBits = bound.length
        ? bound.slice(0, 6).map(function (s) {
          var sidAttr = String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
          return esc(_sk(s))
            + ' <button type="button" class="btn" title="查看描述" onclick="ecoFeedbackViewSkill(\'' + sidAttr + '\',event)" '
            + 'style="font-size:10px;padding:0 3px;color:var(--cyan)">📖</button>';
        }).join(', ')
        : '无';
      html += '<div class="eco-fb-row">'
        + '<div><div class="aid">' + esc(aid) + '</div>'
        + '<div class="meta">' + esc(r.population || '') + ' · T=' + (r.survival_ticks || 0)
        + (skp != null ? ' · s' + Math.round(Number(skp) * 100) + '%' : '')
        + (cop != null ? ' · c' + Math.round(Number(cop) * 100) + '%' : '')
        + '</div>'
        + '<div class="meta">已绑定: ' + boundBits
        + (bound.length > 6 ? '…' : '') + '</div></div>'
        + '<div class="meta">未绑定</div>'
        + '<div>' + (checks || '<span class="meta">无未绑定候选</span>') + '</div>'
        + '</div>';
    });
    if (!anyAdd) {
      html += '<div class="meta" style="margin-top:6px;color:var(--amber)">'
        + '没有可写回的未绑定 skill（已全绑定，或储备/契约库为空）。</div>';
    }
    box.innerHTML = html;
  }

  function _relEdgeKey(e) {
    return String((e && e.source_agent_id) || '') + '\0' + String((e && e.target_id) || '')
      + '\0' + String((e && e.kind) || 'agent_agent');
  }

  function _relShortId(id) {
    id = String(id || '');
    if (!id) return '?';
    // 去掉常见前缀，取可读尾段
    var s = id.replace(/^agent[_-]?/i, '').replace(/_/g, '');
    if (s.length <= 6) return s;
    return s.slice(0, 3) + '…' + s.slice(-2);
  }

  /** 收集 Before/After/建议涉及的全部节点，保证两图坐标一致 */
  function _collectRelationNodeIds(before, suggestions, after) {
    var set = {};
    function add(id) {
      id = String(id || '');
      if (id) set[id] = true;
    }
    (before || []).forEach(function (e) { add(e.source_agent_id); add(e.target_id); });
    (after || []).forEach(function (e) { add(e.source_agent_id); add(e.target_id); });
    (suggestions || []).forEach(function (e) { add(e.source_agent_id); add(e.target_id); });
    return Object.keys(set).sort();
  }

  function _layoutRelationNodes(nodeIds, W, H) {
    var n = nodeIds.length;
    var cx = W / 2;
    var cy = H / 2;
    var rx = Math.min(W * 0.38, 88);
    var ry = Math.min(H * 0.34, 48);
    var pos = {};
    if (n === 0) return pos;
    if (n === 1) {
      pos[nodeIds[0]] = { x: cx, y: cy };
      return pos;
    }
    if (n === 2) {
      pos[nodeIds[0]] = { x: cx - rx * 0.7, y: cy };
      pos[nodeIds[1]] = { x: cx + rx * 0.7, y: cy };
      return pos;
    }
    for (var i = 0; i < n; i++) {
      var angle = (2 * Math.PI * i / n) - Math.PI / 2;
      pos[nodeIds[i]] = {
        x: cx + rx * Math.cos(angle),
        y: cy + ry * Math.sin(angle),
      };
    }
    return pos;
  }

  /**
   * 关系拓扑 SVG 图
   * @param {Array} edges {source, target, status: existing|keep|add}
   * @param {Object} opts {nodeIds, width, height, markerId, emptyText, mode: 'before'|'after'}
   */
  function _renderRelationGraphSvg(edges, opts) {
    opts = opts || {};
    var W = opts.width || 200;
    var H = opts.height || 130;
    var markerId = opts.markerId || ('relm_' + Math.random().toString(36).slice(2, 8));
    var nodeIds = opts.nodeIds || _collectRelationNodeIds(edges, [], []);
    var emptyText = opts.emptyText || '（无边）';
    var mode = opts.mode || 'after';

    if (!nodeIds.length) {
      return '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" '
        + 'style="display:block;background:rgba(0,0,0,.2);border-radius:4px">'
        + '<text x="' + (W / 2) + '" y="' + (H / 2) + '" text-anchor="middle" fill="#576375" font-size="9">'
        + esc(emptyText) + '</text></svg>';
    }

    var pos = _layoutRelationNodes(nodeIds, W, H);
    var edgeList = edges || [];
    // 无边但仍有节点：展示孤立点
    var hasEdges = edgeList.length > 0;

    // 颜色：store/keep 灰实线 · channel 紫点线 · peer 更淡 · add 青虚线
    var colKeep = '#64748b';
    var colAdd = '#22d3ee';
    var colChannel = '#a78bfa';
    var colPeer = '#475569';
    var colNode = '#94a3b8';
    var colNodeGlow = '#22d3ee';

    // 参与新增边的节点高亮
    var touchedAdd = {};
    edgeList.forEach(function (e) {
      if (e.status === 'add') {
        touchedAdd[e.source_agent_id] = true;
        touchedAdd[e.target_id] = true;
      }
    });

    var defs = '<defs>'
      + '<marker id="' + markerId + '_k" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto">'
      + '<path d="M0,0 L7,3 L0,6 Z" fill="' + colKeep + '"/></marker>'
      + '<marker id="' + markerId + '_a" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto">'
      + '<path d="M0,0 L7,3 L0,6 Z" fill="' + colAdd + '"/></marker>'
      + '<marker id="' + markerId + '_c" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto">'
      + '<path d="M0,0 L7,3 L0,6 Z" fill="' + colChannel + '"/></marker>'
      + '</defs>';

    function _edgeStyle(e) {
      var st = e.status || e.layer || 'existing';
      if (st === 'add') {
        return { stroke: colAdd, sw: 1.9, dash: '4 2', opacity: 1, mk: markerId + '_a', arrow: true };
      }
      if (st === 'channel') {
        return { stroke: colChannel, sw: 1.3, dash: '2 3', opacity: 0.85, mk: markerId + '_c', arrow: false };
      }
      if (st === 'peer') {
        return { stroke: colPeer, sw: 1.0, dash: '1 3', opacity: 0.55, mk: markerId + '_k', arrow: false };
      }
      // keep / existing / store
      return { stroke: colKeep, sw: 1.4, dash: '', opacity: 0.85, mk: markerId + '_k', arrow: true };
    }

    var edgesSvg = '';
    var rNode = 11;
    edgeList.forEach(function (e, ei) {
      var a = pos[e.source_agent_id];
      var b = pos[e.target_id];
      if (!a || !b) return;
      var dx = b.x - a.x;
      var dy = b.y - a.y;
      var len = Math.sqrt(dx * dx + dy * dy) || 1;
      var ux = dx / len;
      var uy = dy / len;
      var sty = _edgeStyle(e);
      var padEnd = sty.arrow ? (rNode + 2) : rNode;
      var x1 = a.x + ux * rNode;
      var y1 = a.y + uy * rNode;
      var x2 = b.x - ux * padEnd;
      var y2 = b.y - uy * padEnd;
      // 双向门禁边时弧偏移；通道/同伴无向不偏移
      var reverse = !e.undirected && edgeList.some(function (o, oi) {
        return oi !== ei && o.source_agent_id === e.target_id && o.target_id === e.source_agent_id
          && (o.status === 'add' || o.status === 'keep' || o.status === 'existing');
      });
      var dashAttr = sty.dash ? (' stroke-dasharray="' + sty.dash + '"') : '';
      var mkAttr = sty.arrow ? (' marker-end="url(#' + sty.mk + ')"') : '';
      if (reverse) {
        var nx = -uy * 10;
        var ny = ux * 10;
        var mx = (x1 + x2) / 2 + nx;
        var my = (y1 + y2) / 2 + ny;
        edgesSvg += '<path d="M' + x1.toFixed(1) + ',' + y1.toFixed(1)
          + ' Q' + mx.toFixed(1) + ',' + my.toFixed(1)
          + ' ' + x2.toFixed(1) + ',' + y2.toFixed(1) + '"'
          + ' fill="none" stroke="' + sty.stroke + '" stroke-width="' + sty.sw + '"' + dashAttr
          + ' opacity="' + sty.opacity + '"' + mkAttr + '/>';
      } else {
        edgesSvg += '<line x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1)
          + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1)
          + '" stroke="' + sty.stroke + '" stroke-width="' + sty.sw + '"' + dashAttr
          + ' opacity="' + sty.opacity + '"' + mkAttr + '/>';
      }
    });

    var nodesSvg = '';
    nodeIds.forEach(function (id) {
      var p = pos[id];
      if (!p) return;
      var glow = mode === 'after' && touchedAdd[id];
      var stroke = glow ? colNodeGlow : colNode;
      var sw = glow ? 2.2 : 1.5;
      var lab = _relShortId(id);
      // 不用 <title> 子节点：HTML innerHTML 解析对 SVG<title> 不稳定
      nodesSvg += '<circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1)
        + '" r="' + rNode + '" fill="rgba(15,23,42,.9)" stroke="' + stroke
        + '" stroke-width="' + sw + '"><desc>' + esc(id) + '</desc></circle>';
      nodesSvg += '<text x="' + p.x.toFixed(1) + '" y="' + (p.y + 3).toFixed(1)
        + '" text-anchor="middle" font-size="7" fill="#e2e8f0">'
        + esc(lab) + '</text>';
    });

    var hint = '';
    if (!hasEdges) {
      hint = '<text x="' + (W / 2) + '" y="' + (H - 8) + '" text-anchor="middle" fill="#576375" font-size="8">'
        + esc(emptyText) + '</text>';
    }

    // 固定 min-height，避免窄栏把图压没
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H
      + '" width="100%" height="' + H + 'px" preserveAspectRatio="xMidYMid meet"'
      + ' style="display:block;min-height:' + H + 'px;background:rgba(0,0,0,.22);border-radius:4px">'
      + defs + edgesSvg + nodesSvg + hint + '</svg>';
  }

  function _computeRelationAfter(before, selectedAdds) {
    var map = {};
    (before || []).forEach(function (e) {
      var k = _relEdgeKey(e);
      var layer = e.layer || e.status || 'existing';
      // 通道/同队协作在 After 保留作底图；门禁边标 keep
      var st = (layer === 'channel' || layer === 'peer' || e.status === 'channel' || e.status === 'peer')
        ? (e.status || layer)
        : 'keep';
      if (e.status === 'existing' || layer === 'store') st = 'keep';
      map[k] = {
        source_agent_id: e.source_agent_id,
        target_id: e.target_id,
        kind: e.kind || 'agent_agent',
        rel_type: e.rel_type || 'collaborator',
        note: e.note || '',
        status: st,
        layer: layer,
        undirected: !!e.undirected,
      };
    });
    (selectedAdds || []).forEach(function (e) {
      var k = _relEdgeKey(e);
      // 在通道/编制之上叠加将写入的门禁边
      map[k] = {
        source_agent_id: e.source_agent_id,
        target_id: e.target_id,
        kind: e.kind || 'agent_agent',
        rel_type: e.rel_type || 'collaborator',
        note: e.note || e.reason || '',
        status: 'add',
        layer: 'eco',
        undirected: false,
      };
    });
    return Object.keys(map).map(function (k) { return map[k]; })
      .sort(function (a, b) {
        var order = { add: 0, keep: 1, existing: 1, channel: 2, peer: 3 };
        var oa = order[a.status] != null ? order[a.status] : 9;
        var ob = order[b.status] != null ? order[b.status] : 9;
        if (oa !== ob) return oa - ob;
        return (a.source_agent_id + a.target_id).localeCompare(b.source_agent_id + b.target_id);
      });
  }

  function _selectedRelationAdds() {
    var box = $('eco-fb-relation-table');
    var report = _fbState.relationReport || {};
    var list = report.suggestions || [];
    if (!box) {
      return list.filter(function (s) {
        return s && !s.already_exists && s.default_checked;
      }).map(function (s) {
        return {
          source_agent_id: s.source_agent_id,
          target_id: s.target_id,
          kind: s.kind || 'agent_agent',
          rel_type: s.rel_type || 'collaborator',
          note: s.note || s.reason || '',
        };
      });
    }
    var out = [];
    box.querySelectorAll('input[type=checkbox][data-rel-idx]:checked').forEach(function (cb) {
      if (cb.disabled) return;
      var idx = parseInt(cb.getAttribute('data-rel-idx'), 10);
      var s = list[idx];
      if (!s || s.already_exists) return;
      out.push({
        source_agent_id: s.source_agent_id,
        target_id: s.target_id,
        kind: s.kind || 'agent_agent',
        rel_type: s.rel_type || 'collaborator',
        note: s.note || s.reason || '',
      });
    });
    return out;
  }

  function _relationGraphNodeIds() {
    var report = _fbState.relationReport || {};
    var before = report.before || [];
    var suggestions = report.suggestions || [];
    var after = _computeRelationAfter(before, _selectedRelationAdds());
    // 也包含未勾选建议节点，两图节点集稳定
    return _collectRelationNodeIds(before, suggestions, after);
  }

  function _refreshRelationAfterPreview() {
    var afterEl = $('eco-fb-rel-after');
    var beforeEl = $('eco-fb-rel-before');
    var deltaEl = $('eco-fb-rel-delta');
    var noteEl = $('eco-fb-rel-before-note');
    if (!afterEl) return;
    var report = _fbState.relationReport || {};
    var before = report.before || [];
    var adds = _selectedRelationAdds();
    var after = _computeRelationAfter(before, adds);
    var nodeIds = _relationGraphNodeIds();
    // 保留 layer/status（channel/peer/existing），不要全抹成 existing
    var beforeEdges = before.map(function (e) {
      return Object.assign({}, e, {
        status: e.status || e.layer || 'existing',
      });
    });
    if (beforeEl) {
      beforeEl.innerHTML = _renderRelationGraphSvg(beforeEdges, {
        nodeIds: nodeIds,
        width: 200,
        height: 132,
        markerId: 'eco_rel_before',
        emptyText: '无关系/通道拓扑',
        mode: 'before',
      });
    }
    afterEl.innerHTML = _renderRelationGraphSvg(after, {
      nodeIds: nodeIds,
      width: 200,
      height: 132,
      markerId: 'eco_rel_after',
      emptyText: '勾选建议边后预览',
      mode: 'after',
    });
    if (noteEl) {
      var src = report.before_source || '';
      var nStore = report.before_store_count != null ? report.before_store_count : 0;
      var nCh = report.before_channel_count != null ? report.before_channel_count : 0;
      var nPeer = report.before_peer_count != null ? report.before_peer_count : 0;
      var msg = '';
      if (src === 'channel') {
        msg = '协作=通道共总线（' + nCh + '）· 点对点门禁边 0 — 同总线即协作关系';
      } else if (src === 'peer') {
        msg = '协作=同队编制（' + nPeer + '）· 点对点门禁边 0 — 同队即协作单元';
      } else if (src === 'store') {
        msg = '协作=门禁边 ' + nStore + (nCh ? ' + 通道 ' + nCh : '');
      } else {
        msg = report.before_note || '无协作拓扑';
      }
      noteEl.textContent = msg;
    }
    if (deltaEl) {
      var nAdd = after.filter(function (e) { return e.status === 'add'; }).length;
      var nKeep = after.filter(function (e) { return e.status === 'keep'; }).length;
      var nChg = after.filter(function (e) { return e.status === 'channel'; }).length;
      var nPeer2 = after.filter(function (e) { return e.status === 'peer'; }).length;
      deltaEl.innerHTML = '<span style="color:#64748b">━ 门禁 ' + nKeep + '</span>'
        + (nChg ? ' · <span style="color:#a78bfa">·· 通道协作 ' + nChg + '</span>' : '')
        + (nPeer2 ? ' · <span style="color:#64748b">·· 同队 ' + nPeer2 + '</span>' : '')
        + ' · <span style="color:#22d3ee">┄ +门禁建议 ' + nAdd + '</span>';
    }
  }

  function _renderRelationTable(result, relationReport) {
    var box = $('eco-fb-relation-table');
    if (!box) return;
    var report = relationReport || {};
    var suggestions = report.suggestions || [];
    var before = report.before || [];
    // API 未带回 before 时本地兜底（ranking 同队 mesh），保证图始终可见
    if (!before.length) {
      before = _localTeamBeforeFromResult(result);
      if (before.length) {
        report = Object.assign({}, report, {
          before: before,
          before_count: before.length,
          before_peer: before,
          before_peer_count: before.length,
          before_source: report.before_source || 'peer',
          before_note: (report.before_note || '') + ' · 本地同队兜底',
        });
        // 写回 state，勾选 After 可复用
        if (_fbState.relationReport) {
          _fbState.relationReport.before = before;
          _fbState.relationReport.before_count = before.length;
          if (!_fbState.relationReport.before_source) {
            _fbState.relationReport.before_source = 'peer';
          }
        } else {
          _fbState.relationReport = report;
        }
      }
    }
    var teamId = _resolveTeamId(result);
    var link = teamId
      ? (' <a href="/agent-team-config.html?team_id=' + encodeURIComponent(teamId)
        + '&view=agent&atab=ag-relations&highlight=eco_fp" target="_blank" rel="noopener" '
        + 'style="color:var(--cyan);font-size:9px">打开团队配置·关系</a>')
      : '';

    // 始终画 Before/After 壳，不再整块变成一行 empty
    var html = '';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:6px;min-height:168px">';
    html += '<div style="border:1px solid var(--border);border-radius:6px;padding:6px;background:rgba(0,0,0,.12);min-height:160px">'
      + '<div style="font-size:9px;font-weight:700;margin-bottom:4px;color:var(--dim);display:flex;justify-content:space-between">'
      + '<span>BEFORE · 写回前</span><span class="meta" style="font-weight:400">' + before.length + ' 边</span></div>'
      + '<div id="eco-fb-rel-before" style="min-height:132px"></div>'
      + '<div id="eco-fb-rel-before-note" class="meta" style="margin-top:4px;font-size:8px;line-height:1.35;color:var(--amber)"></div>'
      + '</div>';
    html += '<div style="border:1px solid rgba(34,211,238,.4);border-radius:6px;padding:6px;background:rgba(34,211,238,.05);min-height:160px">'
      + '<div style="font-size:9px;font-weight:700;margin-bottom:4px;color:var(--cyan);display:flex;justify-content:space-between">'
      + '<span>AFTER · 勾选预览</span><span class="meta" style="font-weight:400;color:var(--cyan)">实时</span></div>'
      + '<div id="eco-fb-rel-after" style="min-height:132px"></div>'
      + '<div id="eco-fb-rel-delta" class="meta" style="margin-top:4px;font-size:8px;line-height:1.4"></div>'
      + '</div>';
    html += '</div>';
    html += '<div class="meta" style="margin-bottom:6px;font-size:8px;line-height:1.4;display:flex;flex-wrap:wrap;gap:8px;align-items:center">'
      + '<span style="font-weight:600;color:var(--text)">协作三层</span>'
      + '<span><span style="display:inline-block;width:14px;height:0;border-top:2px solid #64748b;vertical-align:middle;margin-right:3px"></span>门禁边 A2A</span>'
      + '<span><span style="display:inline-block;width:14px;height:0;border-top:2px dotted #a78bfa;vertical-align:middle;margin-right:3px"></span>通道协作</span>'
      + '<span><span style="display:inline-block;width:14px;height:0;border-top:2px dashed #475569;vertical-align:middle;margin-right:3px"></span>同队编制</span>'
      + '<span><span style="display:inline-block;width:14px;height:0;border-top:2px dashed #22d3ee;vertical-align:middle;margin-right:3px"></span>物竞建议门禁</span>'
      + link
      + '</div>';

    html += '<div class="meta" style="margin-bottom:4px">同队/共总线=已有协作；勾选建议是在其上叠加点对点门禁边（确认后落盘）'
      + (teamId ? '' : ' · <span style="color:var(--amber)">⚠ 未解析到 team_id，通道 before 可能不全</span>')
      + '</div>';
    if (!suggestions.length) {
      html += '<div class="eco2-empty">无新增门禁边建议（无 share/follow 证据时仅显示现有协作拓扑）</div>';
    }
    suggestions.forEach(function (s, idx) {
      var src = s.source_agent_id || '';
      var tgt = s.target_id || '';
      var exists = s.already_exists ? ' · 已存在' : '';
      var checked = s.default_checked && !s.already_exists ? ' checked' : '';
      var dim = s.already_exists ? 'opacity:.55;' : '';
      html += '<div class="eco-fb-rel-row" data-idx="' + idx + '" style="padding:4px 0;border-bottom:1px dashed var(--border);' + dim + '">'
        + '<label style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
        + '<input type="checkbox" data-rel-idx="' + idx + '"' + checked + (s.already_exists ? ' disabled' : '') + '>'
        + '<span class="aid">' + esc(src) + '</span>'
        + '<span class="meta">→</span>'
        + '<span class="aid">' + esc(tgt) + '</span>'
        + '<span class="meta">' + esc(s.rel_type || 'collaborator')
        + ' · w=' + (s.weight != null ? s.weight : '?') + exists + '</span>'
        + '<span class="meta">[' + esc(s.note || s.reason || '') + ']</span>'
        + '</label></div>';
    });
    box.innerHTML = html;
    box.querySelectorAll('input[type=checkbox][data-rel-idx]').forEach(function (cb) {
      cb.addEventListener('change', function () { _refreshRelationAfterPreview(); });
    });
    try {
      _refreshRelationAfterPreview();
    } catch (err) {
      var be = $('eco-fb-rel-before');
      var ae = $('eco-fb-rel-after');
      var msg = '拓扑图渲染失败: ' + (err && err.message ? err.message : err);
      if (be) be.innerHTML = '<div class="meta" style="color:var(--amber)">' + esc(msg) + '</div>';
      if (ae) ae.innerHTML = '<div class="meta" style="color:var(--amber)">' + esc(msg) + '</div>';
      setStatus('⚠ ' + msg);
    }
  }

  function _buildRelationFromChecks() {
    var box = $('eco-fb-relation-table');
    if (!box) return [];
    var report = _fbState.relationReport || {};
    var list = report.suggestions || [];
    var out = [];
    box.querySelectorAll('input[type=checkbox][data-rel-idx]:checked').forEach(function (cb) {
      if (cb.disabled) return;
      var idx = parseInt(cb.getAttribute('data-rel-idx'), 10);
      var s = list[idx];
      if (!s || s.already_exists) return;
      out.push({
        source_agent_id: s.source_agent_id,
        target_id: s.target_id,
        kind: s.kind || 'agent_agent',
        rel_type: s.rel_type || 'collaborator',
        note: s.note || s.reason || 'eco_feedback_ui',
        created_by: s.created_by || 'human_via_eco_feedback',
      });
    });
    return out;
  }

  function _renderChannelTable(result, channelReport) {
    var box = $('eco-fb-channel-table');
    if (!box) return;
    var suggestions = (channelReport && channelReport.suggestions) || [];
    var bus = (channelReport && channelReport.bus_name) || '';
    if (!suggestions.length) {
      box.innerHTML = '<div class="eco2-empty">无通道建议（可稍后再拉 suggest）</div>';
      return;
    }
    var html = '<div class="meta" style="margin-bottom:4px">总线 <b>' + esc(bus) + '</b> · 勾选后写回团队页「通道绑定」</div>';
    suggestions.forEach(function (s, idx) {
      var aid = s.agent_id || '';
      var diffs = s.channel_diffs || [];
      var d0 = diffs[0] || {};
      var sat = s.already_satisfied ? ' · 已满足' : '';
      html += '<div class="eco-fb-channel-row" data-aid="' + esc(aid) + '" style="padding:4px 0;border-bottom:1px dashed var(--border)">'
        + '<label style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
        + '<input type="checkbox" data-ch-aid="' + esc(aid) + '"' + (s.already_satisfied ? '' : ' checked') + (idx < 10 ? '' : '') + '>'
        + '<span class="aid">' + esc(aid) + '</span>'
        + '<span class="meta">T=' + (s.survival_ticks || 0) + sat + '</span>'
        + '<span class="meta">' + esc(d0.channel_name || bus)
        + ' sub=' + (d0.subscribe ? '✓' : '×')
        + ' pub=' + (d0.publish ? '✓' : '×')
        + ' P' + (d0.priority || 0) + '</span>'
        + '<span class="meta">[' + esc(s.reason || '') + ']</span>'
        + '</label></div>';
    });
    box.innerHTML = html;
  }

  function _buildChannelFromChecks() {
    var box = $('eco-fb-channel-table');
    if (!box) return [];
    var report = _fbState.channelReport || {};
    var byAid = {};
    (report.suggestions || []).forEach(function (s) {
      byAid[s.agent_id] = s;
    });
    var out = [];
    box.querySelectorAll('input[type=checkbox][data-ch-aid]:checked').forEach(function (cb) {
      var aid = cb.getAttribute('data-ch-aid');
      var s = byAid[aid];
      if (!s) return;
      out.push({
        agent_id: aid,
        channel_diffs: s.channel_diffs || [],
        reason: s.reason || 'eco_feedback_ui',
      });
    });
    return out;
  }

  function _renderCollabTable(result, collabReport) {
    var box = $('eco-fb-collab-table');
    if (!box) return;
    var suggestions = (collabReport && collabReport.suggestions) || [];
    if (!suggestions.length) {
      // 本地从 ranking 拼
      var ranking = ((result && result.final_ranking) || []).slice().sort(function (a, b) {
        return (b.survival_ticks || 0) - (a.survival_ticks || 0);
      }).slice(0, 10);
      suggestions = ranking.map(function (r) {
        var cg = r.collab_genome || {};
        return {
          agent_id: r.agent_id,
          survival_ticks: r.survival_ticks || 0,
          collab: {
            share_tendency: cg.share_tendency != null ? cg.share_tendency : 0.5,
            signal_tendency: cg.signal_tendency != null ? cg.signal_tendency : 0.5,
            follow_tendency: cg.follow_tendency != null ? cg.follow_tendency : 0.5,
            mate_choosiness: cg.mate_choosiness != null ? cg.mate_choosiness : 0.5,
          },
        };
      });
    }
    if (!suggestions.length) {
      box.innerHTML = '<div class="eco2-empty">无协作基因数据</div>';
      return;
    }
    var dims = [
      { k: 'share_tendency', lab: 'share' },
      { k: 'signal_tendency', lab: 'signal' },
      { k: 'follow_tendency', lab: 'follow' },
      { k: 'mate_choosiness', lab: 'mate' },
    ];
    var html = '';
    suggestions.forEach(function (s, idx) {
      var aid = s.agent_id || '';
      var cg = s.collab || {};
      var sliders = dims.map(function (d) {
        var v = cg[d.k] != null ? Number(cg[d.k]) : 0.5;
        return '<label class="meta" style="display:flex;flex-direction:column;gap:1px;min-width:52px">'
          + d.lab
          + '<input type="range" min="0" max="1" step="0.05" value="' + v + '" data-dim="' + d.k + '" style="width:56px">'
          + '</label>';
      }).join('');
      html += '<div class="eco-fb-collab-row" data-t="' + (s.survival_ticks || 0) + '" style="padding:6px 4px;border-bottom:1px dashed var(--border)">'
        + '<label style="display:flex;align-items:center;gap:6px;margin-bottom:4px">'
        + '<input type="checkbox" data-collab-aid="' + esc(aid) + '"' + (idx < 6 ? ' checked' : '') + '>'
        + '<span class="aid">' + esc(aid) + '</span>'
        + '<span class="meta">T=' + (s.survival_ticks || 0) + '</span>'
        + '</label>'
        + '<div style="display:flex;flex-wrap:wrap;gap:8px;padding-left:18px">' + sliders + '</div>'
        + '</div>';
    });
    box.innerHTML = html;
  }

  function _renderSummary(result, integration) {
    var el = $('eco-fb-summary');
    if (!el || !result) return;
    var c = result.contract || {};
    var dom = (integration && integration.dominant_skills) || [];
    if (!dom.length && result.gene_pool && result.gene_pool.dominant) {
      dom = (result.gene_pool.dominant || []).map(function (d) {
        return typeof d === 'string' ? d : d.skill;
      }).filter(Boolean);
    }
    var ranking = result.final_ranking || [];
    var best = ranking.slice().sort(function (a, b) {
      return (b.survival_ticks || 0) - (a.survival_ticks || 0);
    })[0];
    el.innerHTML =
      '<div>考卷: <b style="color:var(--text)">' + esc(c.topic || c.plan_id || '（无契约）') + '</b>'
      + (_fbState.fingerprint ? ' · fp <code style="font-size:9px">' + esc(String(_fbState.fingerprint).slice(0, 12)) + '</code>' : '')
      + '</div>'
      + '<div>适者: <b>' + esc(best && best.agent_id || '—') + '</b> T=' + (best && best.survival_ticks || 0)
      + ' · dominant: ' + (dom.length ? dom.map(function (s) { return esc(_sk(s)); }).join(', ') : '无')
      + '</div>'
      + '<div style="margin-top:2px">写回 Skill 与/或协作后，再进成本优化；或显式跳过并记原因。</div>';
  }

  window.ecoFeedbackSetStep = setStep;

  window.ecoFeedbackOpen = function (result) {
    result = result || window.__LAST_ECO_RESULT__;
    var panel = $('rp-eco-feedback');
    if (!panel) return;
    if (!result) {
      setStatus('⚠ 尚无演练结果');
      panel.style.display = 'block';
      return;
    }
    _fbState.result = result;
    _fbState.integration = result.integration || window.__LAST_INTEGRATION__ || null;
    _fbState.collabReport = null;
    _fbState.channelReport = null;
    _fbState.relationReport = null;
    _fbState.fingerprint = _fpFromResult(result);
    _fbState.skillApplied = false;
    _fbState.collabApplied = false;
    _fbState.channelApplied = false;
    _fbState.relationApplied = false;
    _fbState.skipped = false;
    window.__LAST_ECO_RESULT__ = result;
    if (result.integration) window.__LAST_INTEGRATION__ = result.integration;

    var openUi = function () {
      panel.style.display = 'block';
      setStep(3);
      try {
        _renderSummary(_fbState.result, _fbState.integration);
      } catch (e1) { /* ignore */ }
      try {
        _renderSkillTable(_fbState.result, _fbState.integration);
      } catch (e2) { /* ignore */ }
      try {
        _renderCollabTable(_fbState.result, _fbState.collabReport);
      } catch (e3) { /* ignore */ }
      try {
        _renderRelationTable(_fbState.result, _fbState.relationReport);
      } catch (e4) {
        var box = $('eco-fb-relation-table');
        if (box) {
          box.innerHTML = '<div class="meta" style="color:var(--amber)">关系拓扑渲染失败: '
            + esc(e4 && e4.message ? e4.message : e4) + '</div>';
        }
        setStatus('⚠ 关系拓扑渲染失败');
      }
      try {
        _renderChannelTable(_fbState.result, _fbState.channelReport);
      } catch (e5) { /* ignore */ }
      if (!_fbState.relationReport) {
        setStatus('⚠ 关系 suggest 未返回 — 已用本地同队拓扑兜底（若有 ranking）');
      } else {
        setStatus('');
      }
      try { panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (e) { /* ignore */ }
      // 滚到关系图区域
      try {
        var relBox = $('eco-fb-relation-table');
        if (relBox) relBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } catch (e6) { /* ignore */ }
    };

    var teamId = _resolveTeamId(result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    // 始终带 team_id 重算建议：过滤已绑定 + 注入储备池
    var pSkill = _fetch('/api/v1/eco-runtime/skill-integration/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        result: result,
        contract: result.contract || {},
        team_id: teamId || '',
      }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.ok && d.report) {
        _fbState.integration = d.report;
        window.__LAST_INTEGRATION__ = d.report;
      }
    }).catch(function () {});
    var pCollab = _fetch('/api/v1/eco-runtime/collab-integration/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ result: result, top_k: 12, default_strategy: 'blend' }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.ok && d.report) _fbState.collabReport = d.report;
    }).catch(function () {});
    var timeline = result.timeline || window.__LAST_ECO_TIMELINE__ || null;
    var pRel = _fetch('/api/v1/eco-runtime/relation-integration/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        result: result,
        timeline: timeline,
        team_id: teamId || '',
        top_k: 24,
      }),
    }).then(function (r) {
      if (!r.ok) throw new Error('relation-integration HTTP ' + r.status);
      return r.json();
    }).then(function (d) {
      if (d && d.ok && d.report) _fbState.relationReport = d.report;
    }).catch(function (err) {
      console.warn('[eco-feedback] relation suggest failed', err);
      _fbState._relationSuggestError = String(err && err.message ? err.message : err);
    });
    var pChan = _fetch('/api/v1/eco-runtime/channel-integration/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        result: result,
        timeline: timeline,
        team_id: teamId || '',
        top_k: 12,
      }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.ok && d.report) _fbState.channelReport = d.report;
    }).catch(function () {});
    // 先加载名称映射，再渲染（避免勾选区只见 hex）
    var pNames = _loadSkillNames(teamId);

    Promise.all([pSkill, pCollab, pRel, pChan, pNames]).then(openUi).catch(openUi);
  };

  window.ecoFeedbackClose = function () {
    var panel = $('rp-eco-feedback');
    if (panel) panel.style.display = 'none';
    setStep(2);
  };

  function _formatSkillAudit(d) {
    var audit = (d && d.audit) || [];
    if (!audit.length) return (d && d.hint) || '';
    var parts = audit.map(function (a) {
      var st = a.status || '?';
      if (st === 'applied') {
        return (a.agent_id || '') + ' +' + ((a.added || []).length) + ' skill';
      }
      if (st === 'already_present') {
        return (a.agent_id || '') + ' 已有(跳过)';
      }
      if (st === 'agent_not_found') {
        return (a.agent_id || '') + ' 未匹配真身';
      }
      return (a.agent_id || '') + ' ' + st;
    });
    return parts.join('；');
  }

  window.ecoFeedbackPreviewSkills = function () {
    var bindings = _buildBindingsFromChecks();
    var teamId = _resolveTeamId(_fbState.result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!bindings.length) { setStatus('⚠ 未勾选任何 skill'); return; }
    var nSk = bindings.reduce(function (n, b) { return n + (b.add_skills || []).length; }, 0);
    var report = Object.assign({}, _fbState.integration || {}, { recommended_bindings: bindings });
    _fetch('/api/v1/eco-runtime/skill-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id: teamId, confirm: false, report: report }),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          setStatus('Skill 预览: ' + (d.would_apply || bindings.length) + ' 个 agent / '
            + (d.would_add_skills != null ? d.would_add_skills : nSk) + ' 条 skill（确认后写入）');
        } else setStatus('⚠ ' + ((d && d.error) || 'preview failed'));
      }).catch(function (e) { setStatus('⚠ ' + (e.message || e)); });
  };

  window.ecoFeedbackApplySkills = function () {
    var bindings = _buildBindingsFromChecks();
    var teamId = _resolveTeamId(_fbState.result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!bindings.length) { setStatus('⚠ 未勾选任何 skill'); return; }
    var report = Object.assign({}, _fbState.integration || {}, { recommended_bindings: bindings });
    _fetch('/api/v1/eco-runtime/skill-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id: teamId, confirm: true, report: report, feedback_router: false }),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          var nAgent = d.applied || 0;
          var nSk = d.skills_added || 0;
          var detail = _formatSkillAudit(d);
          if (nAgent > 0 || nSk > 0) {
            _fbState.skillApplied = true;
            _fbState.skipped = false;
            setStatus('✅ Skill 写回: ' + nAgent + ' 个 agent / +' + nSk + ' 条'
              + (detail ? ' — ' + detail : ''));
            _persistFeedback({ feedback: 'done', applied: nAgent, skills_added: nSk });
          } else {
            // applied=0：已有 or 未匹配 — 说明原因，不算成功写回
            setStatus('⚠ 未写入新 skill（applied=0）'
              + (d.hint ? ' — ' + d.hint : '')
              + (detail ? ' | ' + detail : ''));
          }
        } else {
          setStatus('⚠ ' + ((d && d.error) || 'apply failed') + (d && d.hint ? ' — ' + d.hint : ''));
        }
      }).catch(function (e) { setStatus('⚠ ' + (e.message || e)); });
  };

  window.ecoFeedbackPreviewCollab = function () {
    var suggestions = _buildCollabFromChecks();
    var teamId = _resolveTeamId(_fbState.result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!suggestions.length) { setStatus('⚠ 未勾选协作行'); return; }
    _fetch('/api/v1/eco-runtime/collab-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        confirm: false,
        suggestions: suggestions,
        fingerprint: _fbState.fingerprint,
        strategy: _strategy(),
      }),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) setStatus('协作预览: 将写回 ' + (d.would_apply || 0) + ' 处 eco_collab');
        else setStatus('⚠ ' + ((d && d.error) || 'preview failed'));
      }).catch(function (e) { setStatus('⚠ ' + (e.message || e)); });
  };

  window.ecoFeedbackApplyCollab = function () {
    var suggestions = _buildCollabFromChecks();
    var teamId = _resolveTeamId(_fbState.result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!suggestions.length) { setStatus('⚠ 未勾选协作行'); return; }
    _fetch('/api/v1/eco-runtime/collab-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        confirm: true,
        suggestions: suggestions,
        fingerprint: _fbState.fingerprint,
        strategy: _strategy(),
      }),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          _fbState.collabApplied = true;
          _fbState.skipped = false;
          var miss = (d.audit || []).filter(function (a) { return a.error; }).length;
          setStatus('✅ 协作基因已写回 ' + (d.applied || 0) + ' 处'
            + (miss ? '（' + miss + ' 个 id 未匹配真身，可能为孪生后代 id）' : '')
            + ' · 提示：通道拓扑请用「写回通道」落地到团队页');
          _persistFeedback({ feedback: 'done', collab_applied: d.applied || 0 });
        } else {
          setStatus('⚠ ' + ((d && d.error) || 'apply failed'));
        }
      }).catch(function (e) { setStatus('⚠ ' + (e.message || e)); });
  };

  window.ecoFeedbackPreviewRelations = function () {
    var suggestions = _buildRelationFromChecks();
    var teamId = _resolveTeamId(_fbState.result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!suggestions.length) { setStatus('⚠ 未勾选关系边'); return; }
    _fetch('/api/v1/eco-runtime/relation-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        confirm: false,
        suggestions: suggestions,
        fingerprint: _fbState.fingerprint,
      }),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          setStatus('关系预览: 将写入 ' + (d.would_apply || 0) + ' 条边（确认后落盘）');
        } else setStatus('⚠ ' + ((d && d.error) || 'preview failed'));
      }).catch(function (e) { setStatus('⚠ ' + (e.message || e)); });
  };

  window.ecoFeedbackApplyRelations = function () {
    var suggestions = _buildRelationFromChecks();
    var teamId = _resolveTeamId(_fbState.result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!suggestions.length) { setStatus('⚠ 未勾选关系边'); return; }
    _fetch('/api/v1/eco-runtime/relation-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        confirm: true,
        suggestions: suggestions,
        fingerprint: _fbState.fingerprint,
      }),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          var n = d.applied || 0;
          var dup = d.skipped_dup || 0;
          if (n > 0) {
            _fbState.relationApplied = true;
            _fbState.skipped = false;
            setStatus('✅ 关系边已写回 ' + n + ' 条'
              + (dup ? '（跳过重复 ' + dup + '）' : '')
              + ' — 团队配置「关系」页可见 · created_by=human_via_eco_feedback');
            _persistFeedback({ feedback: 'done', relation_applied: n });
          } else {
            setStatus('⚠ 未写入新边（applied=0）'
              + (dup ? ' · 全部已存在 ' + dup : ''));
          }
        } else {
          setStatus('⚠ ' + ((d && d.error) || 'apply failed'));
        }
      }).catch(function (e) { setStatus('⚠ ' + (e.message || e)); });
  };

  window.ecoFeedbackPreviewChannels = function () {
    var suggestions = _buildChannelFromChecks();
    var teamId = _resolveTeamId(_fbState.result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!suggestions.length) { setStatus('⚠ 未勾选通道行'); return; }
    _fetch('/api/v1/eco-runtime/channel-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        confirm: false,
        suggestions: suggestions,
        fingerprint: _fbState.fingerprint,
      }),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          setStatus('通道预览: 将合并写回 ' + (d.would_apply || 0) + ' 个 agent / '
            + (d.would_diff || 0) + ' 条 diff（确认后持久化）');
        } else setStatus('⚠ ' + ((d && d.error) || 'preview failed'));
      }).catch(function (e) { setStatus('⚠ ' + (e.message || e)); });
  };

  window.ecoFeedbackApplyChannels = function () {
    var suggestions = _buildChannelFromChecks();
    var teamId = _resolveTeamId(_fbState.result);
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!suggestions.length) { setStatus('⚠ 未勾选通道行'); return; }
    _fetch('/api/v1/eco-runtime/channel-integration/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        confirm: true,
        suggestions: suggestions,
        fingerprint: _fbState.fingerprint,
      }),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          var n = d.applied || 0;
          var miss = (d.audit || []).filter(function (a) { return a.error; }).length;
          if (n > 0) {
            _fbState.channelApplied = true;
            _fbState.skipped = false;
            setStatus('✅ 通道已写回 ' + n + ' 个 agent'
              + (miss ? '（' + miss + ' 未匹配）' : '')
              + ' — 团队配置「关系→通道绑定」可见，publish/subscribe 已生效');
            _persistFeedback({ feedback: 'done', channel_applied: n });
          } else {
            setStatus('⚠ 未写入通道（applied=0）'
              + (miss ? ' · ' + miss + ' 个 id 未匹配' : ''));
          }
        } else {
          setStatus('⚠ ' + ((d && d.error) || 'apply failed'));
        }
      }).catch(function (e) { setStatus('⚠ ' + (e.message || e)); });
  };

  function _feedbackPayload() {
    return {
      feedback: _fbState.skipped ? 'skipped' : (
        (_fbState.skillApplied || _fbState.collabApplied
          || _fbState.channelApplied || _fbState.relationApplied) ? 'done' : ''
      ),
      skill_applied: !!_fbState.skillApplied,
      collab_applied: !!_fbState.collabApplied,
      channel_applied: !!_fbState.channelApplied,
      relation_applied: !!_fbState.relationApplied,
      reason: _fbState.skipReason || '',
      fingerprint: _fbState.fingerprint || '',
    };
  }

  function _boundTaskId() {
    try {
      if (window.eco2GetBoundTask) {
        var t = window.eco2GetBoundTask();
        if (t) return String(t.task_id || t.id || '');
      }
    } catch (e) { /* ignore */ }
    try {
      var ct = JSON.parse(sessionStorage.getItem('eco_bound_task') || 'null');
      if (ct) return String(ct.task_id || ct.id || '');
    } catch (e2) { /* ignore */ }
    var c = (_fbState.result && _fbState.result.contract) || {};
    return String(c.task_id || '');
  }

  /** XC-2.4：创建 BidCandidate 并跳转成本竞标 */
  window.ecoFeedbackPushBid = function () {
    var teamId = _resolveTeamId(_fbState.result) || window._selectedTeamId || '';
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (!teamId) { setStatus('⚠ 未选团队'); return; }
    if (!_fbState.result) { setStatus('⚠ 尚无演练结果'); return; }

    var taskId = _boundTaskId();
    if (!taskId) {
      setStatus('⚠ 未挂接任务（Q1）— 空跑不可推送成本竞标。请先在 ① 挂载业务任务再演练');
      return;
    }

    var hasWrite = _fbState.skillApplied || _fbState.collabApplied
      || _fbState.channelApplied || _fbState.relationApplied;
    if (!hasWrite && !_fbState.skipped) {
      setStatus('⚠ 请先写回 Skill/协作/关系/通道，或点「跳过写回」并填原因（Q2）');
      return;
    }
    if (_fbState.skipped && !(_fbState.skipReason || '').trim()) {
      setStatus('⚠ 跳过写回须填写原因');
      return;
    }

    var planId = '';
    try {
      if (window.eco2GetBoundContract) {
        var bc = window.eco2GetBoundContract();
        if (bc) planId = String(bc.plan_id || '');
      }
      if (!planId && _fbState.result.contract) {
        planId = String(_fbState.result.contract.plan_id || '');
      }
    } catch (e) { /* ignore */ }

    setStatus('⏳ 创建成本竞标候选（先适者后省钱）…');
    var body = {
      team_id: teamId,
      task_id: taskId,
      plan_id: planId,
      result: _fbState.result,
      feedback: _feedbackPayload(),
    };
    _fetch('/api/v1/eco-runtime/bid-candidates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.ok) {
          setStatus('⚠ 推送失败: ' + ((d && d.error) || 'unknown')
            + (d && d.hint ? ' — ' + d.hint : ''));
          return;
        }
        var c = d.candidate || {};
        var cid = c.candidate_id || '';
        _persistFeedback({
          feedback: body.feedback.feedback || 'done',
          candidate_id: cid,
          quality_status: c.quality_status,
        });
        setStep(4);
        var q = new URLSearchParams();
        q.set('team_id', teamId);
        q.set('candidate_id', cid);
        if (taskId) q.set('task_id', taskId);
        if (_fbState.fingerprint) q.set('eco_fp', String(_fbState.fingerprint).slice(0, 64));
        q.set('feedback', body.feedback.feedback || 'done');
        if (c.champion_agent_id) q.set('champ', String(c.champion_agent_id).slice(0, 48));
        if ((c.dominant_skills || []).length) {
          q.set('dominant', (c.dominant_skills || []).slice(0, 4).join(',').slice(0, 120));
        }
        q.set('best_T', String(c.best_T || 0));
        q.set('quality', c.quality_status || '');
        setStatus('✅ 已创建候选 ' + cid + ' · ' + (c.quality_status || '') + ' → 成本页');
        window.location.href = '/cost-dashboard.html?' + q.toString();
      }).catch(function (e) {
        setStatus('⚠ 推送失败: ' + (e.message || e));
      });
  };

  /** 步骤条 ④ / 顶栏：直接打开 cost 主轴（带当前 team/task） */
  window.ecoGoCostStep = function () {
    var teamId = _resolveTeamId(_fbState.result) || window._selectedTeamId || '';
    var taskId = _boundTaskId();
    var q = new URLSearchParams();
    if (teamId) q.set('team_id', teamId);
    if (taskId) q.set('task_id', taskId);
    if (_fbState.fingerprint) q.set('eco_fp', String(_fbState.fingerprint).slice(0, 64));
    if (_fbState.skillApplied || _fbState.collabApplied
        || _fbState.channelApplied || _fbState.relationApplied) {
      q.set('feedback', 'done');
    } else if (_fbState.skipped) {
      q.set('feedback', 'skipped');
    }
    window.location.href = '/cost-dashboard.html?' + q.toString();
  };

  function _syncCostNavLink() {
    var a = document.getElementById('nav-cost-eco');
    if (!a) return;
    var teamId = window._selectedTeamId || '';
    try {
      var qs = new URLSearchParams(location.search || '');
      teamId = teamId || qs.get('team_id') || '';
    } catch (e) { /* ignore */ }
    var href = '/cost-dashboard.html';
    if (teamId) href += '?team_id=' + encodeURIComponent(teamId);
    a.href = href;
  }
  try { _syncCostNavLink(); } catch (e) { /* ignore */ }
  // 种群切换后刷新顶栏深链
  var _prevTeam = window._selectedTeamId;
  setInterval(function () {
    if (window._selectedTeamId !== _prevTeam) {
      _prevTeam = window._selectedTeamId;
      _syncCostNavLink();
    }
  }, 1500);

  window.ecoFeedbackGoCost = function (skip) {
    var teamId = _resolveTeamId(_fbState.result) || window._selectedTeamId || '';
    if (teamId && !window._selectedTeamId) window._selectedTeamId = teamId;
    if (skip) {
      var reason = window.prompt('跳过 Skill/协作/关系/通道写回的原因（将记入审计）:', _fbState.skipReason || '');
      if (reason == null) return;
      reason = String(reason).trim();
      if (!reason) {
        setStatus('⚠ 跳过须填写原因');
        return;
      }
      _fbState.skipped = true;
      _fbState.skipReason = reason;
      _persistFeedback({ feedback: 'skipped', reason: reason });
    } else if (!_fbState.skillApplied && !_fbState.collabApplied
        && !_fbState.channelApplied && !_fbState.relationApplied && !_fbState.skipped) {
      setStatus('⚠ 请先写回 Skill / 协作基因 / 关系边 / 通道，或点「跳过写回」并填原因');
      return;
    } else if (_fbState.collabApplied && !_fbState.channelApplied && !_fbState.relationApplied && !_fbState.skipped) {
      // 仅基因未写拓扑：amber 警告仍可进成本
      setStatus('⚠ 已写协作基因但未写关系/通道 — 团队页协作拓扑未变；仍可进成本或先写回拓扑');
    }
    setStep(4);
    var q = new URLSearchParams();
    if (teamId) q.set('team_id', teamId);
    if (_fbState.fingerprint) q.set('eco_fp', String(_fbState.fingerprint).slice(0, 64));
    var fb = (skip || _fbState.skipped) ? 'skipped' : 'done';
    q.set('feedback', fb);
    if (_fbState.skillApplied) q.set('skill', '1');
    if (_fbState.collabApplied) q.set('collab', '1');
    if (_fbState.relationApplied) q.set('relation', '1');
    if (_fbState.channelApplied || _fbState.relationApplied) q.set('topology', 'done');
    else if (_fbState.collabApplied) q.set('topology', 'gene_only');
    if (_fbState.skipReason) q.set('skip_reason', _fbState.skipReason.slice(0, 120));
    var taskId = _boundTaskId();
    if (taskId) q.set('task_id', taskId);
    // 摘要供成本页展示
    try {
      var best = ((_fbState.result && _fbState.result.final_ranking) || [])[0];
      if (best) q.set('champ', String(best.agent_id || '').slice(0, 48));
      var dom = (_fbState.integration && _fbState.integration.dominant_skills) || [];
      if (dom.length) q.set('dominant', dom.slice(0, 4).join(',').slice(0, 120));
    } catch (e) { /* ignore */ }
    window.location.href = '/cost-dashboard.html?' + q.toString();
  };

  window.ecoFeedbackOnResult = function (result) {
    try {
      window.__LAST_ECO_RESULT__ = result;
      if (result && result.integration) window.__LAST_INTEGRATION__ = result.integration;
      setTimeout(function () { window.ecoFeedbackOpen(result); }, 400);
    } catch (e) { /* ignore */ }
  };
})();
