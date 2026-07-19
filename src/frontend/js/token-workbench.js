/**
 * token-workbench.js — 任务 Token 治理统一工作台（v2）
 * 数据源：GET /api/v1/cost/token-governance/dashboard
 * 与 cost-dashboard.js 共存：本文件管主工作台，旧 JS 管深度分析。
 */
(function () {
  'use strict';

  var TG_API = '/api/v1/cost/token-governance';

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  }
  function num(n) { return Number(n || 0).toLocaleString('en-US'); }
  function pct(x) { return ((Number(x) || 0) * 100).toFixed(1) + '%'; }

  /** 安全 toast：cost 页常无 #toast（system-evolution 全局 toast 会炸） */
  function tgToast(msg, kind) {
    try {
      var host = $('cost-toast-host');
      if (host) {
        var el = document.createElement('div');
        el.className = 'cost-toast cost-toast--' + (kind === 'error' || kind === 'warn' ? kind : 'success');
        el.innerHTML = '<div class="cost-toast__body">' + esc(String(msg || '')) + '</div>';
        host.appendChild(el);
        setTimeout(function () {
          el.classList.add('cost-toast--leaving');
          setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 260);
        }, 3500);
        return;
      }
      var t = $('toast');
      if (t) {
        t.className = 'toast show' + (kind ? ' toast-' + kind : '');
        t.textContent = String(msg || '');
        setTimeout(function () { t.classList.remove('show'); }, 2500);
        return;
      }
    } catch (e) { /* never break sim path */ }
  }

  async function jget(url) {
    var r = await fetch(url, { credentials: 'same-origin' });
    if (!r.ok) {
      var errBody = '';
      try { errBody = await r.text(); } catch (e2) { /* ignore */ }
      throw new Error('HTTP ' + r.status + (errBody ? ': ' + errBody.slice(0, 180) : ''));
    }
    return r.json();
  }
  async function jpost(url, body) {
    var r = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    if (!r.ok) {
      var errBody = '';
      try { errBody = await r.text(); } catch (e2) { /* ignore */ }
      throw new Error('HTTP ' + r.status + (errBody ? ': ' + errBody.slice(0, 180) : ''));
    }
    return r.json();
  }

  function windowVal() {
    var el = $('filter-window');
    return (el && el.value) || '24h';
  }

  function renderKpis(d) {
    var host = $('tg-kpi-row');
    if (!host) return;
    var sum = d.summary || {};
    var attr = d.attribution || {};
    var stats = (d.stats && d.stats.counters) || {};
    var cache = (d.stats && d.stats.cache) || {};
    var cards = [
      { k: '窗口 Token', v: num(sum.total), s: '调用 ' + num(sum.calls) + ' · 全量(含未挂 team)' },
      {
        k: '任务已归因',
        v: num(attr.attributed_total),
        s: '占比 ' + pct(attr.attributed_share)
          + ' · 任务 ' + (attr.task_count || 0)
          + (Number(attr.unscoped_total) > 0 ? ' · 未挂 team ' + num(attr.unscoped_total) : ''),
      },
      { k: '治理已省', v: num(stats.tokens_saved_est), s: 'prepare ' + num(stats.prepare_calls) + ' · skill≈' + num(stats.skill_tokens_saved_est) },
      { k: '缓存命中', v: num(cache.hits || stats.cache_hits), s: 'miss ' + num(cache.misses || stats.cache_misses) + ' · rate ' + pct(cache.hit_rate) },
      { k: '路由', v: num(stats.model_routes), s: 'economy ' + num(stats.model_economy_routes) + ' · skill提示 ' + num(stats.skill_hints) },
      { k: '预算拦截', v: num(stats.budget_blocks), s: (d.budget && d.budget.on_exceed) || 'halt' },
    ];
    host.innerHTML = cards.map(function (c) {
      return '<div class="tg-kpi">'
        + '<div class="tg-kpi__k">' + esc(c.k) + '</div>'
        + '<div class="tg-kpi__v">' + esc(c.v) + '</div>'
        + '<div class="tg-kpi__s">' + esc(c.s) + '</div></div>';
    }).join('');
  }

  var KIND_CN = {
    simplify: '提示词简化',
    compress: '内容压缩',
    rtk_tool: 'RTK tool 压缩',
    progressive_mem: '渐进历史',
    codegraph: 'CodeGraph 切片',
    behavior: 'Ponytail/Caveman',
    cache: '上下文缓存',
    skill_route: 'Skill 路由',
    model_route: '模型路由',
    budget: '预算门禁',
  };

  function kindCn(kind, catalogId) {
    return KIND_CN[kind] || catalogId || kind || '—';
  }

  /** 试跑表「说明」列：中文可读，对齐账单 levers 可读性 */
  function humanLeverDetail(x) {
    if (!x) return '—';
    var bits = [];
    var kind = x.kind || '';
    if (x.before != null && x.after != null) {
      bits.push(num(x.before) + '→' + num(x.after) + ' tok');
    }
    var saved = x.saved != null ? x.saved : x.saved_est;
    if (saved != null && Number(saved) > 0) bits.push('约省 ' + num(saved));

    if (kind === 'simplify') bits.push('去空白/套话');
    if (kind === 'compress') {
      var ac = x.actions || {};
      var parts = [];
      if (ac.dedupe_adjacent) parts.push('相邻去重×' + ac.dedupe_adjacent);
      if (ac.fold_long_tool || ac.fold_long) parts.push('折叠长 tool');
      if (ac.truncate_system || ac.truncate) parts.push('硬截断');
      bits.push(parts.length ? parts.join('、') : '压缩上下文');
    }
    if (kind === 'rtk_tool') {
      bits.push('tool 滤噪/去重/截断' + (x.tool_msgs_touched != null ? '（' + x.tool_msgs_touched + ' 条）' : ''));
      if (x.actions) {
        var a2 = Array.isArray(x.actions) ? x.actions.slice(0, 4).join('·') : '';
        if (a2) bits.push(a2);
      }
    }
    if (kind === 'progressive_mem') {
      bits.push('旧轮次压成索引' + (x.collapsed != null ? '（折叠 ' + x.collapsed + '）' : ''));
    }
    if (kind === 'codegraph') {
      bits.push('源码→符号切片' + (x.replaced ? '×' + x.replaced : '') + (x.indexed ? ' · 已索引' : ''));
    }
    if (kind === 'behavior') {
      bits.push('注入 ' + ((x.injected || []).join('+') || '行为约束') + '（主降输出，输入可能略增）');
    }
    if (kind === 'cache') {
      bits.push(x.hit ? ('缓存命中 · 模式 ' + (x.mode || 'observe')) : ('未命中 · 模式 ' + (x.mode || 'observe')));
      if (x.mode === 'observe' && x.hit) bits.push('observe 只记统计、不短路、不计已省');
    }
    if (kind === 'skill_route') {
      var sk = (x.skills || []).slice(0, 3).map(function (s) { return String(s).slice(0, 10); });
      bits.push(sk.length ? '复用 skill ' + sk.join(',') : '无 skill 命中');
      if (x.system_truncated) bits.push('已裁 system');
      if (x.injected) bits.push('已注入精简指令');
    }
    if (kind === 'model_route') {
      bits.push((x.tier || '?') + ' 档 → ' + (x.model || '?'));
      if (x.cost_tier_hint) bits.push('复杂度 ' + x.cost_tier_hint);
    }
    if (kind === 'budget') {
      bits.push(x.blocked ? '⛔ 拦截' : '✓ 放行');
      if (x.level) bits.push(String(x.level));
    }
    return bits.join(' · ') || kindCn(kind, x.catalog_id);
  }

  function leverPills(byKind) {
    var keys = Object.keys(byKind || {});
    if (!keys.length) return '<span class="dim">—</span>';
    return keys.map(function (k) {
      return '<span class="tg-lever-pill" title="' + esc(k) + '">' + esc(kindCn(k, k)) + '</span>';
    }).join('');
  }

  function renderTasks(d) {
    /* 与试跑同面板：账单 + 节省 pills + prepare 流水 */
    var el = $('tg-task-table');
    if (!el) return;
    var rows = d.by_task || [];
    var uns = d.unscoped;
    var sav = d.savings_by_task || [];
    var recent = d.recent_savings || [];
    var html = '';

    if (uns && Number(uns.total) > 0) {
      html += '<div class="tg-warn">历史 unscoped <b>' + num(uns.total) + '</b> tokens · '
        + '新任务须带 task_id。可在试跑报告末尾看归因建议。</div>';
    }

    html += '<div class="tg-subhead">任务消耗 · usage_log（点行选中试跑）</div>';
    if (!rows.length) {
      html += '<div class="tg-empty">尚无按任务拆分账单。执行带 task_id 的任务后刷新。</div>';
    } else {
      html += '<table class="tg-table"><thead><tr>'
        + '<th>task_key</th><th>team</th><th>tokens</th><th>in</th><th>out</th><th>calls</th>'
        + '</tr></thead><tbody>';
      rows.forEach(function (r) {
        var tk = String(r.task_key || '');
        html += '<tr class="tg-bill-row" data-task-key="' + esc(tk) + '" data-team-id="' + esc(r.team_id || '') + '" style="cursor:pointer" title="点选后试跑">'
          + '<td class="mono">' + esc(tk.slice(0, 36)) + '</td>'
          + '<td>' + esc(r.team_id || '—') + '</td>'
          + '<td><b>' + num(r.total) + '</b></td>'
          + '<td>' + num(r.input_tokens) + '</td>'
          + '<td>' + num(r.output_tokens) + '</td>'
          + '<td>' + num(r.calls) + '</td></tr>';
      });
      html += '</tbody></table>';
    }

    if (sav.length) {
      html += '<div class="tg-subhead" style="margin-top:14px">治理节省 · 按 task（prepare 落盘）</div>';
      html += '<table class="tg-table"><thead><tr>'
        + '<th>task_id</th><th>events</th><th>saved≈</th><th>命中杠杆</th></tr></thead><tbody>';
      sav.slice(0, 10).forEach(function (r) {
        html += '<tr class="tg-bill-row" data-task-key="' + esc(String(r.task_id || '')) + '" data-team-id="" style="cursor:pointer">'
          + '<td class="mono">' + esc(String(r.task_id || '').slice(0, 28)) + '</td>'
          + '<td>' + num(r.events) + '</td>'
          + '<td><b>' + num(r.saved_tokens_est) + '</b></td>'
          + '<td>' + leverPills(r.by_kind) + '</td></tr>';
      });
      html += '</tbody></table>';
    }

    if (recent.length) {
      html += '<div class="tg-subhead" style="margin-top:14px">最近 prepare 流水</div><div class="tg-events">';
      recent.slice(0, 8).forEach(function (e) {
        var kinds = e.lever_kinds || [];
        var pills = kinds.map(function (k) {
          return '<span class="tg-lever-pill">' + esc(kindCn(k, k)) + '</span>';
        }).join('');
        html += '<div class="tg-ev">'
          + '<code class="mono">' + esc(String(e.task_id || '—').slice(0, 16)) + '</code>'
          + ' · 约省 <b>' + num(e.saved_tokens_est) + '</b> '
          + (pills || '<span class="dim">—</span>')
          + (e.model_tier ? ' · 档 ' + esc(e.model_tier) : '')
          + '</div>';
      });
      html += '</div>';
    }

    el.innerHTML = html;
    el.querySelectorAll('.tg-bill-row').forEach(function (tr) {
      tr.onclick = function () {
        var tk = tr.getAttribute('data-task-key') || '';
        var team = tr.getAttribute('data-team-id') || '';
        if (!tk || tk === '(unscoped)') return;
        if (window.tgSelectSimTask) window.tgSelectSimTask(tk, team, tk);
        tgToast('已选 ' + tk.slice(0, 16) + ' · 点「用所选 task 试跑」', 'success');
      };
    });
  }

  function _simFixture() {
    // 故意制造：重复套话、超长 tool、git/test 噪声、长源码 → 触发 rtk/compress/codegraph/progressive
    var sys = '';
    for (var i = 0; i < 25; i++) sys += '你是运维助手。\n\n';
    sys += '背景说明。';
    for (var j = 0; j < 400; j++) sys += '背景说明。';
    var tool = 'Enumerating objects: 5, done.\nCounting objects: 100% (5/5), done.\n';
    for (var g = 0; g < 40; g++) tool += 'M  src/pkg/file' + g + '.py\n';
    for (var t = 0; t < 30; t++) tool += 'test_ok_' + t + ' ... ok\n';
    tool += 'ERROR line repeated\nERROR line repeated\nERROR line repeated\n';
    for (var k = 0; k < 3000; k++) tool += 'x';
    var src = '#!/usr/bin/env python3\n';
    for (var fn = 0; fn < 20; fn++) {
      src += 'def handler_' + fn + '(x):\n';
      for (var body = 0; body < 40; body++) src += '    value = x + ' + body + '  # noise\n';
      src += '    return value\n\n';
    }
    var hist = [];
    for (var h = 0; h < 12; h++) {
      hist.push({ role: 'user', content: '中间轮次讨论细节 ' + h + ' ' + ('padding '.repeat(80)) });
      hist.push({ role: 'assistant', content: '中间回复 ' + h + ' ' + ('text '.repeat(80)) });
    }
    return [
      { role: 'system', content: sys },
      { role: 'user', content: 'ES 集群巡检 监控 告警' },
      { role: 'user', content: 'ES 集群巡检 监控 告警' },
    ].concat(hist).concat([
      { role: 'tool', content: tool },
      { role: 'tool', content: src },
      { role: 'user', content: 'How does prepare_request route models?' },
    ]);
  }

  function renderLevers(d, leversPayload) {
    var el = $('tg-lever-panel');
    if (!el) return;
    var catalog = (leversPayload && leversPayload.catalog) || [];
    var arch = (leversPayload && leversPayload.architecture) || {};
    var stats = ((leversPayload && leversPayload.stats) || d.stats || {}).counters || {};
    var cache = (leversPayload && leversPayload.cache) || (d.stats && d.stats.cache) || {};
    var pipeline = (leversPayload && leversPayload.pipeline) || [];
    var docsHref = (leversPayload && leversPayload.docs) || '/README.md#任务-token-治理';

    // settings_key → DOM id for enable/mode controls
    var idMap = {
      simplify_prompt: 'lv-simplify',
      compress: 'lv-compress',
      model_route: 'lv-model',
      skill_route_hint: 'lv-skill',
      cache_mode: 'lv-cache-mode',
      budget_enforce_turn: 'lv-budget',
      rtk_tool_compress: 'lv-rtk_tool_compress',
      progressive_memory: 'lv-progressive_memory',
      codegraph_context: 'lv-codegraph_context',
      ponytail_level: 'lv-ponytail_level',
      cost_tier_route: 'lv-cost_tier_route',
    };

    function renderKnob(spec) {
      if (!spec || !spec.key) return '';
      var key = spec.key;
      var val = spec.value != null ? spec.value : spec.default;
      var pid = 'lv-param-' + key;
      if (spec.type === 'enum') {
        var opts = (spec.enum_values || []).map(function (m) {
          return '<option value="' + esc(m) + '"' + (String(val) === String(m) ? ' selected' : '') + '>'
            + esc(m) + '</option>';
        }).join('');
        return '<label class="tg-knob tg-knob--enum" title="' + esc(spec.label || key) + '">'
          + '<span class="tg-knob__lab">' + esc(spec.label || key) + '</span>'
          + '<select class="tg-knob__sel" id="' + pid + '" data-param-key="' + esc(key) + '"'
          + ' data-param-type="enum">' + opts + '</select></label>';
      }
      if (spec.type === 'float') {
        var fmin = spec.min != null ? spec.min : 0;
        var fmax = spec.max != null ? spec.max : 1;
        var fstep = spec.step != null ? spec.step : 0.05;
        var fval = Number(val);
        if (isNaN(fval)) fval = Number(spec.default) || 0;
        // range uses scaled integers for smooth drag
        var scale = 100;
        var rmin = Math.round(fmin * scale);
        var rmax = Math.round(fmax * scale);
        var rstep = Math.max(1, Math.round(fstep * scale));
        var rval = Math.round(fval * scale);
        return '<label class="tg-knob" title="' + esc(spec.label || key) + '">'
          + '<span class="tg-knob__lab">' + esc(spec.label || key) + '</span>'
          + '<input type="range" class="tg-knob__range" id="' + pid + '" data-param-key="' + esc(key) + '"'
          + ' data-param-type="float" data-scale="' + scale + '"'
          + ' min="' + rmin + '" max="' + rmax + '" step="' + rstep + '" value="' + rval + '">'
          + '<span class="tg-knob__val mono" data-for="' + pid + '">' + fval.toFixed(2) + '</span>'
          + '</label>';
      }
      // int default
      var imin = spec.min != null ? spec.min : 0;
      var imax = spec.max != null ? spec.max : 100;
      var istep = spec.step != null ? spec.step : 1;
      var ival = parseInt(val, 10);
      if (isNaN(ival)) ival = parseInt(spec.default, 10) || 0;
      var unit = spec.unit ? '<span class="tg-knob__unit">' + esc(spec.unit) + '</span>' : '';
      return '<label class="tg-knob" title="' + esc(spec.label || key) + '">'
        + '<span class="tg-knob__lab">' + esc(spec.label || key) + '</span>'
        + '<input type="range" class="tg-knob__range" id="' + pid + '" data-param-key="' + esc(key) + '"'
        + ' data-param-type="int"'
        + ' min="' + imin + '" max="' + imax + '" step="' + istep + '" value="' + ival + '">'
        + '<span class="tg-knob__val mono" data-for="' + pid + '">' + ival + '</span>'
        + unit + '</label>';
    }

    function renderRow(c) {
      var on = !!c.enabled;
      var sk = c.settings_key || c.id;
      var cid = idMap[sk] || ('lv-' + sk);
      var toggle = c.kind === 'enum'
        ? '<select class="tg-pipe-enable" id="' + cid + '" data-settings-key="' + esc(sk) + '">'
          + (c.enum_values || ['observe', 'serve', 'off']).map(function (m) {
            return '<option value="' + m + '"' + (String(c.value) === m ? ' selected' : '') + '>' + m + '</option>';
          }).join('')
          + '</select>'
        : '<input type="checkbox" class="tg-pipe-enable" id="' + cid + '" data-settings-key="' + esc(sk) + '"'
          + (on ? ' checked' : '') + ' title="启用">';
      // companions
      var extraToggle = '';
      if (c.id === 'model_route') {
        extraToggle = '<label class="tg-knob tg-knob--tiny" title="cost_tier 启发">'
          + '<input type="checkbox" id="lv-cost_tier_route" data-settings-key="cost_tier_route"'
          + (c.cost_tier_route !== false ? ' checked' : '') + '>'
          + '<span class="tg-knob__lab">cost_tier</span></label>';
      }
      if (c.id === 'budget') {
        // submit 预检与 turn 门禁分开；turn 用主 checkbox（budget_enforce_turn）
        var subOn = true;
        try {
          var levRoot = (leversPayload && leversPayload.levers) || {};
          if (levRoot.budget_enforce_submit === false) subOn = false;
        } catch (eSub) { /* ignore */ }
        extraToggle = '<label class="tg-knob tg-knob--tiny" title="任务 submit 预算预检 402">'
          + '<input type="checkbox" id="lv-budget-submit" data-settings-key="budget_enforce_submit"'
          + (subOn ? ' checked' : '') + '>'
          + '<span class="tg-knob__lab">submit</span></label>';
      }
      var knobs = (c.params || []).map(renderKnob).join('');
      var wire = c.wired !== false
        ? '<span class="tg-wire tg-wire--on" title="chat_harness · tool_loop · simulate">✓ 接线</span>'
        : '<span class="tg-wire tg-wire--off">未接线</span>';
      return '<tr class="tg-pipe-row' + (on ? ' is-on' : '') + '" data-lever-id="' + esc(c.id) + '">'
        + '<td class="tg-pipe-ord mono">' + esc(String(c.order != null ? c.order : '')) + '</td>'
        + '<td class="tg-pipe-name"><b>' + esc(c.title || c.id) + '</b>'
        + '<div class="dim mono">' + esc(c.id) + '</div></td>'
        + '<td class="tg-pipe-wire">' + wire + '</td>'
        + '<td class="tg-pipe-en">' + toggle + extraToggle + '</td>'
        + '<td class="tg-pipe-sim"><div class="tg-lever-card__simhit dim" data-sim-slot="'
        + esc(c.id) + '">—</div></td>'
        + '<td class="tg-pipe-knobs">' + (knobs || '<span class="dim">—</span>') + '</td>'
        + '</tr>';
    }

    var pipeChips = (pipeline.length ? pipeline : catalog.map(function (c) { return c.id; })).map(function (id) {
      var c = catalog.find(function (x) { return x.id === id; });
      var on = c ? !!c.enabled : true;
      return '<span class="tg-pipe-chip' + (on ? ' is-on' : '') + '">' + esc(id) + '</span>';
    }).join('<span class="tg-pipe-arrow">→</span>');

    var rows = catalog.length
      ? catalog.map(renderRow).join('')
      : '<tr><td colspan="6"><div class="tg-warn">杠杆目录未加载（GET /levers 需返回 catalog）</div></td></tr>';

    el.innerHTML =
      '<div class="tg-arch tg-arch--slim">'
      + '<div class="tg-arch__t">prepare_request 管线'
      + ' <a class="tg-docs-link" href="' + esc(docsHref) + '" target="_blank" rel="noopener">完整说明 → README</a></div>'
      + '<div class="tg-pipe-flow">' + (pipeChips || '<span class="dim">—</span>') + '</div>'
      + '<div class="dim mono" style="margin-top:4px">' + esc(arch.entry || 'TokenGovernanceService.prepare_request')
      + ' · ' + esc((arch.wired_into || []).join(' · ')) + '</div>'
      + '</div>'
      + '<div class="tg-pipe-wrap"><table class="tg-table tg-pipe-table"><thead><tr>'
      + '<th>#</th><th>杠杆</th><th>接线</th><th>启用</th><th>试跑</th><th>可调参数</th>'
      + '</tr></thead><tbody>' + rows + '</tbody></table></div>'
      + '<div class="tg-lever-meta">'
      + '<div class="tg-lever-summary">'
      + 'prepare <b>' + num(stats.prepare_calls || 0) + '</b>'
      + ' · 已省≈ <b>' + num(stats.tokens_saved_est || 0) + '</b>'
      + ' · cache ' + num(cache.size || 0) + '/' + num(cache.max_size || 256)
      + '</div>'
      + '<div class="tg-lever-actions">'
      + '<button type="button" class="btn cost-btn cost-btn--primary cost-btn--sm" id="lv-save">保存开关与旋钮</button>'
      + '<span id="lv-dirty" class="dim" style="font-size:11px">已同步</span>'
      + '<span class="dim" style="font-size:11px">· 试跑前自动保存 · 旋钮写 settings → prepare 真生效</span>'
      + '</div></div>';

    function markDirty() {
      var d = $('lv-dirty');
      if (d) {
        d.textContent = '未保存';
        d.style.color = 'var(--tg-warn,#A67C1A)';
        d.style.fontWeight = '700';
      }
    }
    function markClean() {
      var d = $('lv-dirty');
      if (d) {
        d.textContent = '已同步';
        d.style.color = '';
        d.style.fontWeight = '';
      }
    }

    // live knob value labels + dirty
    el.querySelectorAll('.tg-knob__range').forEach(function (inp) {
      var sync = function () {
        var lab = el.querySelector('[data-for="' + inp.id + '"]');
        if (!lab) return;
        var typ = inp.getAttribute('data-param-type');
        if (typ === 'float') {
          var sc = parseInt(inp.getAttribute('data-scale') || '100', 10) || 100;
          lab.textContent = (parseInt(inp.value, 10) / sc).toFixed(2);
        } else {
          lab.textContent = inp.value;
        }
        markDirty();
      };
      inp.addEventListener('input', sync);
      // initial label only, no dirty
      var lab0 = el.querySelector('[data-for="' + inp.id + '"]');
      if (lab0) {
        var typ0 = inp.getAttribute('data-param-type');
        if (typ0 === 'float') {
          var sc0 = parseInt(inp.getAttribute('data-scale') || '100', 10) || 100;
          lab0.textContent = (parseInt(inp.value, 10) / sc0).toFixed(2);
        } else lab0.textContent = inp.value;
      }
    });
    el.querySelectorAll('[data-settings-key], [data-param-key]').forEach(function (node) {
      if (node.classList && node.classList.contains('tg-knob__range')) return;
      node.addEventListener('change', markDirty);
    });

    function collectBody() {
      var body = {};
      var params = {};
      // enable / mode controls
      el.querySelectorAll('[data-settings-key]').forEach(function (node) {
        var key = node.getAttribute('data-settings-key');
        if (!key) return;
        if (node.type === 'checkbox') body[key] = !!node.checked;
        else if (node.value != null && node.value !== '') body[key] = node.value;
      });
      // also legacy idMap checkboxes not marked data-settings-key
      Object.keys(idMap).forEach(function (sk) {
        var node = $(idMap[sk]);
        if (!node) return;
        if (body[sk] !== undefined) return;
        if (node.type === 'checkbox') body[sk] = !!node.checked;
        else if (node.value != null && node.value !== '') body[sk] = node.value;
      });
      if (body.ponytail_level) {
        body.caveman_level = body.ponytail_level === 'off' ? 'off' : body.ponytail_level;
      }
      // knobs
      el.querySelectorAll('[data-param-key]').forEach(function (node) {
        var key = node.getAttribute('data-param-key');
        var typ = node.getAttribute('data-param-type') || 'int';
        if (!key) return;
        if (typ === 'enum') {
          params[key] = node.value;
        } else if (typ === 'float') {
          var sc = parseInt(node.getAttribute('data-scale') || '100', 10) || 100;
          params[key] = parseInt(node.value, 10) / sc;
        } else {
          params[key] = parseInt(node.value, 10);
        }
      });
      body.params = params;
      return body;
    }

    async function saveLevers(silent) {
      var r = await jpost(TG_API + '/levers', collectBody());
      if (r && r.ok !== false) markClean();
      if (!silent) {
        tgToast(r.ok !== false ? '杠杆+参数已写入 settings（prepare 真生效）' : '保存失败', r.ok !== false ? 'success' : 'error');
      }
      return r;
    }

    // 供试跑路径调用：改旋钮后未点保存也能先落盘再 prepare
    window.tgSaveLevers = function (silent) { return saveLevers(!!silent); };
    window.tgCollectLevers = collectBody;

    function formatLeverDetail(x) {
      return humanLeverDetail(x);
    }

    function paintSimOnCards(levers) {
      var byCat = {};
      (levers || []).forEach(function (x) {
        if (!x) return;
        var id = x.catalog_id || ({
          simplify: 'simplify_prompt',
          compress: 'compress',
          rtk_tool: 'rtk_tool_compress',
          progressive_mem: 'progressive_memory',
          codegraph: 'codegraph_context',
          behavior: 'ponytail_caveman',
          cache: 'cache',
          skill_route: 'skill_route',
          model_route: 'model_route',
          budget: 'budget',
        })[x.kind] || x.kind;
        byCat[id] = x;
      });
      var nodes = document.querySelectorAll('[data-sim-slot]');
      for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];
        if (!node) continue;
        var slot = node.getAttribute('data-sim-slot');
        var x = byCat[slot];
        try {
          if (!x) {
            node.textContent = '未触发';
            if (node.classList) node.classList.remove('is-hit');
          } else {
            var short = formatLeverDetail(x);
            // 表内列窄：优先 before→after / saved
            var bits = [];
            if (x.before != null && x.after != null) bits.push(num(x.before) + '→' + num(x.after));
            if (x.saved != null || x.saved_est != null) bits.push('−' + num(x.saved != null ? x.saved : x.saved_est));
            node.textContent = bits.length ? bits.join(' · ') : (short.slice(0, 48) || x.kind);
            node.title = short;
            if (node.classList) node.classList.add('is-hit');
          }
        } catch (ePaint) { /* ignore single card */ }
      }
    }

    function renderSimResult(p, title) {
      _renderSimResultOuter(p, title, arguments.length > 2 ? arguments[2] : null);
      paintSimOnCards(p.levers || []);
    }

    var saveBtn = $('lv-save');
    if (saveBtn) {
      saveBtn.onclick = function () {
        saveLevers(false).then(function () { loadDashboard(); });
      };
    }
  }

  /* ── 试跑选 task（独立面板，用户点选） ── */
  var _simTasks = [];
  var _selectedTask = null; // {task_id, team_id, title, ...}

  function _persistSelectedTask(t) {
    _selectedTask = t || null;
    try {
      if (t && t.task_id) {
        localStorage.setItem('tg_sim_task_id', t.task_id);
        localStorage.setItem('tg_sim_team_id', t.team_id || '');
      }
    } catch (e) { /* ignore */ }
  }

  function _restoreSelectedId() {
    try { return localStorage.getItem('tg_sim_task_id') || ''; } catch (e) { return ''; }
  }

  function renderSelectedTask() {
    var el = $('tg-sim-selected');
    if (!el) return;
    if (!_selectedTask || !_selectedTask.task_id) {
      el.innerHTML = '<span class="dim">尚未选择任务 — 请在上方列表 <b>点击一行</b> 选中</span>';
      return;
    }
    var t = _selectedTask;
    el.innerHTML =
      '已选 · <strong>' + esc(t.title || '（无标题）') + '</strong>'
      + '<div class="mono" style="margin-top:4px;font-size:11px">'
      + 'task_id=<b>' + esc(t.task_id) + '</b>'
      + ' · team=<b>' + esc(t.team_id || '—') + '</b>'
      + ' · status=<b>' + esc(t.status || '—') + '</b>'
      + (t.has_snapshot ? ' · 📸 snapshot' : '')
      + (t.has_tool_trace ? ' · 🔧 tool_trace' : '')
      + (!t.has_snapshot && !t.has_tool_trace ? ' · 将尝试重构消息' : '')
      + '</div>';
  }

  function renderTaskList(tasks) {
    var host = $('tg-sim-task-list');
    if (!host) return;
    _simTasks = tasks || [];
    if (!_simTasks.length) {
      host.innerHTML = '<div class="tg-empty" style="padding:14px">当前筛选下暂无任务。可切换团队或先提交/执行任务。</div>';
      return;
    }
    var selId = (_selectedTask && _selectedTask.task_id) || _restoreSelectedId();
    host.innerHTML = _simTasks.map(function (t, idx) {
      var id = t.task_id || '';
      var selected = id && id === selId;
      if (selected) _selectedTask = t;
      var badges = '';
      if (t.has_snapshot) badges += '<span class="tg-sim-badge tg-sim-badge--ok">snapshot</span>';
      if (t.has_tool_trace) badges += '<span class="tg-sim-badge tg-sim-badge--ok">tool_trace</span>';
      if (t.has_pipeline && !t.has_snapshot && !t.has_tool_trace) {
        badges += '<span class="tg-sim-badge">pipeline</span>';
      }
      badges += '<span class="tg-sim-badge">' + esc(t.status || '?') + '</span>';
      return '<div class="tg-sim-task-row' + (selected ? ' is-selected' : '') + '"'
        + ' role="option" aria-selected="' + (selected ? 'true' : 'false') + '"'
        + ' data-task-idx="' + idx + '" tabindex="0">'
        + '<input type="radio" class="tg-sim-task-row__radio" name="tg-sim-task"'
        + (selected ? ' checked' : '') + ' tabindex="-1" aria-hidden="true">'
        + '<div>'
        + '<div class="tg-sim-task-row__title">' + esc(t.title || '（无标题）') + '</div>'
        + '<div class="tg-sim-task-row__meta">' + esc(id)
        + (t.team_id ? ' · ' + esc(t.team_id) : '')
        + '</div></div>'
        + '<div class="tg-sim-task-row__badges">' + badges + '</div>'
        + '</div>';
    }).join('');

    // bind row click
    host.querySelectorAll('.tg-sim-task-row').forEach(function (row) {
      function pick() {
        var idx = Number(row.getAttribute('data-task-idx'));
        var t = _simTasks[idx];
        if (!t) return;
        _persistSelectedTask(t);
        host.querySelectorAll('.tg-sim-task-row').forEach(function (r) {
          r.classList.remove('is-selected');
          r.setAttribute('aria-selected', 'false');
          var rad = r.querySelector('input[type=radio]');
          if (rad) rad.checked = false;
        });
        row.classList.add('is-selected');
        row.setAttribute('aria-selected', 'true');
        var radio = row.querySelector('input[type=radio]');
        if (radio) radio.checked = true;
        renderSelectedTask();
        var st = $('tg-sim-pick-status');
        if (st) st.textContent = '已选 ' + String(t.task_id).slice(0, 14);
      }
      row.onclick = pick;
      row.onkeydown = function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          pick();
        }
      };
    });
    renderSelectedTask();
  }

  async function loadSimTasks() {
    var st = $('tg-sim-pick-status');
    var teamSel = $('tg-sim-team');
    var teamId = (teamSel && teamSel.value) || '';
    if (st) st.textContent = '加载任务…';
    try {
      // 先拉全量填充团队下拉（不因筛选丢选项）
      var all = await jget(TG_API + '/recent-tasks?limit=40');
      var allTasks = (all && all.tasks) || [];
      if (teamSel) {
        var prev = teamSel.value || '';
        var teams = {};
        allTasks.forEach(function (t) {
          if (t.team_id) teams[t.team_id] = true;
        });
        var opts = '<option value="">全部团队</option>';
        Object.keys(teams).sort().forEach(function (tid) {
          opts += '<option value="' + esc(tid) + '"'
            + (prev === tid ? ' selected' : '') + '>' + esc(tid) + '</option>';
        });
        teamSel.innerHTML = opts;
        if (prev && teams[prev]) teamSel.value = prev;
        teamId = teamSel.value || '';
      }
      var tasks = teamId
        ? allTasks.filter(function (t) { return t.team_id === teamId; })
        : allTasks;
      var want = (_selectedTask && _selectedTask.task_id) || _restoreSelectedId();
      if (want) {
        var found = tasks.find(function (t) { return t.task_id === want; })
          || allTasks.find(function (t) { return t.task_id === want; });
        _selectedTask = found || null;
      } else {
        _selectedTask = null;
      }
      renderTaskList(tasks);
      if (st) {
        st.textContent = tasks.length + ' 个任务 · 点击一行选中，再点「用所选 task 试跑」';
      }
    } catch (e) {
      var host = $('tg-sim-task-list');
      if (host) {
        host.innerHTML = '<div class="tg-warn" style="padding:12px">任务列表加载失败: '
          + esc(e.message || e) + '</div>';
      }
      if (st) st.textContent = '加载失败';
    }
  }

  /**
   * @param {string} title
   * @param {{mode?:'task'|'fixture', taskId?:string}} opts
   */
  async function runSim(title, opts) {
    opts = opts || {};
    var mode = opts.mode || 'fixture';
    var box = $('tg-sim-out');
    if (box) box.innerHTML = '<div class="dim">试跑中…</div>';
    try {
      // 试跑前自动保存旋钮/开关 → prepare 所见即所得
      try {
        if (typeof window.tgSaveLevers === 'function') {
          await window.tgSaveLevers(true);
        }
      } catch (e0) { /* ignore save errors; still try simulate */ }

      var body;
      if (mode === 'task') {
        var tid = opts.taskId || (_selectedTask && _selectedTask.task_id) || '';
        if (!tid) throw new Error('请先在列表中点选一个 task');
        body = {
          source: 'task',
          task_id: tid,
          team_id: (_selectedTask && _selectedTask.team_id) || '',
          query_for_skill: '',
        };
      } else {
        body = {
          source: 'fixture',
          messages: _simFixture(),
          team_id: 'aws-ops',
          task_id: 'sim_fixture_' + Date.now().toString(36),
          query_for_skill: 'ES 集群巡检 监控 告警',
        };
      }
      var r = await jpost(TG_API + '/simulate', body);
      if (r && r.ok === false) {
        throw new Error((r.error || r.detail || 'simulate rejected')
          + (r.hint ? ' · ' + r.hint : ''));
      }
      var p = (r && r.prepare) || {};
      var meta = Object.assign({ task_id: r.task_id }, r.input || {});
      // renderSimResult lives inside renderLevers closure — call via paint path duplicated here
      _renderSimResultOuter(p, title, meta);
      tgToast('试跑完成 · 省≈' + (p.saved_tokens_est || 0)
        + (meta.source ? ' · ' + meta.source : ''), 'success');
      try {
        var d2 = await jget(TG_API + '/dashboard?window=' + encodeURIComponent(windowVal()));
        if (d2 && d2.ok !== false) {
          renderKpis(d2);
          renderTasks(d2);
          renderBudget(d2, null);
          // 高亮账单中当前 task
          var tid = meta.task_id || (opts && opts.taskId) || '';
          if (tid) {
            document.querySelectorAll('.tg-bill-row').forEach(function (tr) {
              var k = tr.getAttribute('data-task-key') || '';
              tr.style.outline = (k === tid || k.indexOf(String(tid).slice(0, 12)) === 0)
                ? '2px solid var(--tg-accent,#1F6B4A)' : '';
            });
          }
        }
      } catch (e2) { /* ignore */ }
    } catch (e) {
      var msg = (e && e.message) ? e.message : String(e);
      if (box) {
        box.innerHTML = '<div class="tg-warn">试跑失败: ' + esc(msg)
          + '<div class="dim" style="margin-top:4px">请确认已点选任务；无 snapshot 时需有 pipeline/tool_trace。也可用「样例 fixture」对照算法。</div></div>';
      }
      tgToast('试跑失败: ' + msg, 'error');
    }
  }

  function _renderSimResultOuter(p, title, inputMeta) {
    var box = $('tg-sim-out');
    if (!box) return;
    var levers = p.levers || [];
    // 回写杠杆行试跑槽
    try {
      var byCat = {};
      var map = {
        simplify: 'simplify_prompt', compress: 'compress', rtk_tool: 'rtk_tool_compress',
        progressive_mem: 'progressive_memory', codegraph: 'codegraph_context',
        behavior: 'ponytail_caveman', cache: 'cache', skill_route: 'skill_route',
        model_route: 'model_route', budget: 'budget',
      };
      (levers || []).forEach(function (x) {
        if (!x) return;
        byCat[x.catalog_id || map[x.kind] || x.kind] = x;
      });
      document.querySelectorAll('[data-sim-slot]').forEach(function (node) {
        if (!node) return;
        var x = byCat[node.getAttribute('data-sim-slot')];
        if (!x) {
          node.textContent = '未触发';
          if (node.classList) node.classList.remove('is-hit');
        } else {
          var bits = [];
          if (x.before != null && x.after != null) bits.push(num(x.before) + '→' + num(x.after));
          var sv = x.saved != null ? x.saved : x.saved_est;
          if (sv != null && Number(sv) > 0) bits.push('−' + num(sv));
          if (x.kind === 'cache') bits.push(x.hit ? 'HIT' : 'MISS');
          if (x.kind === 'budget') bits.push(x.blocked ? '拦截' : '放行');
          node.textContent = bits.join(' · ') || kindCn(x.kind, x.catalog_id);
          node.title = humanLeverDetail(x);
          if (node.classList) node.classList.add('is-hit');
        }
      });
    } catch (ePaint) { /* ignore */ }

    var rows = levers.map(function (x) {
      return '<tr>'
        + '<td class="tg-kind">' + esc(kindCn(x.kind, x.catalog_id))
        + '<div class="dim mono">' + esc(x.kind || '') + '</div></td>'
        + '<td class="mono">'
        + (x.before != null ? num(x.before) : '—')
        + (x.after != null ? ' → ' + num(x.after) : '')
        + '</td>'
        + '<td class="mono">' + num(x.saved != null ? x.saved : (x.saved_est || 0)) + '</td>'
        + '<td class="tg-detail">' + esc(humanLeverDetail(x)) + '</td>'
        + '</tr>';
    }).join('');

    var advice = buildSimAdvice(p, _lastBudgetSnap, _lastDashSnap);
    var adviceHtml = '<div class="tg-sim-advice">'
      + '<div class="tg-sim-advice__t">预算 / 归因告警与建议</div><ul>'
      + advice.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('')
      + '</ul></div>';

    box.innerHTML =
      '<div class="tg-sim-head">' + esc(title || '试跑结果') + ' · before / after</div>'
      + (inputMeta
        ? '<div class="dim" style="font-size:11px;margin-bottom:6px">输入源: <b>'
          + esc(inputMeta.source || '—') + '</b>'
          + (inputMeta.task_id ? ' · task=<code class="mono">' + esc(inputMeta.task_id) + '</code>' : '')
          + (inputMeta.message_count != null ? ' · msgs=' + num(inputMeta.message_count) : '')
          + (inputMeta.chars != null ? ' · chars≈' + num(inputMeta.chars) : '')
          + '</div>'
        : '')
      + '<div class="tg-sim-kpi">'
      + '<span>before <b>' + num(p.before_tokens) + '</b></span>'
      + '<span>→ after <b>' + num(p.after_tokens) + '</b></span>'
      + '<span>净省≈ <b class="ok">' + num(p.saved_tokens_est) + '</b></span>'
      + '<span>cache <b>' + (p.cache_hit ? 'HIT' : 'MISS') + '</b></span>'
      + '<span>杠杆 <b>' + levers.length + '</b></span>'
      + '</div>'
      + (rows
        ? '<table class="tg-table tg-sim-table"><thead><tr>'
          + '<th>杠杆</th><th>before→after</th><th>约省</th><th>说明</th>'
          + '</tr></thead><tbody>' + rows + '</tbody></table>'
        : '<div class="tg-empty">本轮无杠杆触发</div>')
      + adviceHtml;
  }

  function wireSimPicker() {
    var teamSel = $('tg-sim-team');
    if (teamSel) {
      teamSel.onchange = function () {
        loadSimTasks();
      };
    }
    var ref = $('tg-sim-refresh');
    if (ref) ref.onclick = function () { loadSimTasks(); };
    var runTask = $('tg-sim-run-task');
    if (runTask) {
      runTask.onclick = function () {
        runSim('真实 task · prepare', { mode: 'task' });
      };
    }
    var runFix = $('tg-sim-run-fixture');
    if (runFix) {
      runFix.onclick = function () {
        runSim('样例 fixture · 压力消息', { mode: 'fixture' });
      };
    }
    var run2 = $('tg-sim-run-cache2');
    if (run2) {
      run2.onclick = async function () {
        await runSim('第 1 次（建立缓存）', { mode: 'fixture' });
        await runSim('第 2 次（应出现 cache HIT）', { mode: 'fixture' });
      };
    }
    var runOff = $('tg-sim-run-offcmp');
    if (runOff) {
      runOff.onclick = async function () {
        // H2.4: 临时关 compress 试跑后恢复，并同步 UI checkbox + dirty
        var prev = true;
        try {
          var cur = await jget(TG_API + '/levers');
          if (cur && cur.levers && cur.levers.compress === false) prev = false;
        } catch (e0) { /* ignore */ }
        try {
          await jpost(TG_API + '/levers', { compress: false });
          var cb = $('lv-compress');
          if (cb && cb.type === 'checkbox') cb.checked = false;
          await runSim('关 compress 后试跑', { mode: 'fixture' });
          await jpost(TG_API + '/levers', { compress: prev });
          if (cb && cb.type === 'checkbox') cb.checked = !!prev;
          var dirty = $('lv-dirty');
          if (dirty) {
            dirty.textContent = '已同步';
            dirty.style.color = '';
            dirty.style.fontWeight = '';
          }
          // 刷新杠杆行不整页闪：只重拉 levers 状态条
          try {
            var lev = await jget(TG_API + '/levers');
            if (lev && lev.ok !== false) {
              var dash = await jget(TG_API + '/dashboard?window=' + encodeURIComponent(windowVal()));
              if (dash && dash.ok !== false) renderBudget(dash, lev);
            }
          } catch (e1) { /* ignore */ }
        } catch (e) {
          tgToast(String(e.message || e), 'error');
          try { await jpost(TG_API + '/levers', { compress: prev }); } catch (e2) { /* ignore */ }
        }
      };
    }
    loadSimTasks();
  }

  var _lastBudgetSnap = null;
  var _lastDashSnap = null;

  function renderBudget(d, leversPayload) {
    // 无独立预算菜单：只在杠杆区下条展示当前限额
    var el = $('tg-budget-strip');
    var b = d.budget || {};
    var levBudget = (leversPayload && leversPayload.budget) || {};
    var thr = levBudget.alert_threshold != null ? levBudget.alert_threshold : b.alert_threshold;
    if (thr == null) thr = 0.8;
    var onEx = levBudget.on_exceed || b.on_exceed || 'halt';
    var sess = levBudget.per_session_max != null ? levBudget.per_session_max : b.per_session_max;
    var agent = levBudget.per_agent_daily_max != null ? levBudget.per_agent_daily_max : b.per_agent_daily_max;
    var team = levBudget.per_team_daily_max != null ? levBudget.per_team_daily_max : b.per_team_daily_max;
    _lastBudgetSnap = {
      alert_threshold: thr, on_exceed: onEx,
      per_session_max: sess, per_agent_daily_max: agent, per_team_daily_max: team,
    };
    _lastDashSnap = d;
    if (!el) return;
    var ev = d.budget_events || [];
    var lastEv = ev.length ? (ev[0].level + ' · ' + (ev[0].message || ev[0].scope || '')) : '无近期预算事件';
    el.innerHTML =
      '预算门禁 · session≤<b>' + num(sess) + '</b>'
      + ' · agent日≤<b>' + num(agent) + '</b>'
      + ' · team日≤<b>' + num(team) + '</b>'
      + ' · 告警阈值 <b>' + esc(String(thr)) + '</b>'
      + ' · 超限 <b>' + esc(onEx) + '</b>'
      + ' · <span class="dim">' + esc(lastEv) + '</span>'
      + ' <span class="dim">（改旋钮在上表「预算门禁」行 · 试跑报告末尾给建议）</span>';
  }

  /** 试跑后预算/归因告警 + 调参建议 */
  function buildSimAdvice(p, budget, dash) {
    var tips = [];
    var levers = (p && p.levers) || [];
    var bud = budget || _lastBudgetSnap || {};
    var thr = Number(bud.alert_threshold != null ? bud.alert_threshold : 0.8);
    var budL = null;
    levers.forEach(function (x) { if (x && x.kind === 'budget') budL = x; });

    if (budL && budL.blocked) {
      tips.push('预算门禁拦截：提高「会话上限 / 日限」旋钮，或把超限策略改为 warn（仅告警不阻断）。');
    } else if (budL) {
      tips.push('本轮预算门禁放行（阈值 ' + thr + ' · 策略 ' + (bud.on_exceed || 'halt') + '）。');
    }

    var after = Number((p && p.after_tokens) || 0);
    var sessMax = Number(bud.per_session_max || 0);
    if (sessMax > 0 && after > 0 && after >= sessMax * thr) {
      tips.push('本轮 after≈' + num(after) + ' 已接近会话上限×告警阈值（' + num(sessMax) + '×' + thr + '）。可：① 提高 session 上限 ② 提高告警阈值 ③ 加强 rtk/compress 旋钮。');
    }

    var saved = Number((p && p.saved_tokens_est) || 0);
    if (saved <= 0) {
      tips.push('净省≈0：可能 skill/行为注入使 after≥before。看分步「约省」列；或加大 tool 噪声、开 rtk/progressive。');
    }

    var attr = dash && dash.attribution;
    if (attr && Number(attr.unscoped_total || 0) > 0 && Number(attr.attributed_share || 0) < 0.5) {
      tips.push('归因不足（unscoped 占比高）：生产任务必须带 task_id，否则账单与预算对不齐。');
    }

    var hasRtk = levers.some(function (x) { return x && x.kind === 'rtk_tool' && Number(x.saved || 0) > 0; });
    if (!hasRtk) {
      tips.push('未看到 RTK 明显省量：确认「RTK tool 压缩」开启，并降低 max_tool_chars 旋钮后再试跑。');
    }

    if (tips.length < 2) {
      tips.push('预算不准时：只调杠杆表「预算门禁」行（阈值/限额/halt|warn），保存后 submit 与 prepare 即生效。');
    }
    return tips.slice(0, 5);
  }

  var _loadDashInflight = null;
  async function loadDashboard() {
    // H4.1 去抖：并发合并
    if (_loadDashInflight) return _loadDashInflight;
    var st = $('tg-workbench-status');
    if (st) st.textContent = '加载中…';
    _loadDashInflight = (async function () {
      try {
        var results = await Promise.all([
          jget(TG_API + '/dashboard?window=' + encodeURIComponent(windowVal())),
          jget(TG_API + '/levers'),
        ]);
        var d = results[0];
        var lev = results[1];
        if (!d || d.ok === false) throw new Error((d && d.error) || 'dashboard failed');
        renderKpis(d);
        renderTasks(d);
        renderLevers(d, lev && lev.ok !== false ? lev : null);
        renderBudget(d, lev && lev.ok !== false ? lev : null);
        if (st) st.textContent = '窗口 ' + (d.window || windowVal())
          + ' · catalog ' + ((lev && lev.catalog && lev.catalog.length) || 0)
          + ' · ' + new Date().toLocaleTimeString();
      } catch (e) {
        // H4.2 可见错误
        var msg = e.message || String(e);
        if (st) st.textContent = '加载失败: ' + msg;
        var strip = $('tg-budget-strip');
        if (strip) strip.innerHTML = '<span style="color:var(--tg-warn,#A67C1A)">杠杆/看板加载失败：' + esc(msg) + ' — 确认后端 /api/v1/cost/token-governance/* 可达</span>';
        var kpi = $('tg-kpi-row');
        if (kpi && /加载|…|失败/.test(kpi.textContent || '')) {
          kpi.innerHTML = '<div class="tg-warn">Token 治理看板失败：' + esc(msg) + '</div>';
        }
        tgToast('工作台加载失败: ' + msg, 'error');
      } finally {
        _loadDashInflight = null;
      }
    })();
    return _loadDashInflight;
  }

  window.tgRefreshAll = loadDashboard;
  window.tgRunVerify = async function () {
    // 不再使用独立预算「效果验证」菜单：诊断写入试跑报告区 + toast
    var box = $('tg-sim-out');
    if (box) box.innerHTML = '<div class="dim">诊断中…</div>';
    try {
      var d = await jpost(TG_API + '/verify', {
        window: windowVal(),
        messages: [
          { role: 'system', content: 'x'.repeat(2500) },
          { role: 'user', content: 'ping' },
          { role: 'user', content: 'ping' },
        ],
      });
      var v = d.verdict || {};
      var a = d.attribution || {};
      var notes = v.notes || [];
      var tips = notes.slice();
      tips.push('预算不准时：只调杠杆表「预算门禁」行的阈值/限额/halt|warn，保存后 prepare/submit 生效。');
      tips.push('归因差：确保任务执行带 task_id（账单与门禁才对齐）。');
      if (box) {
        box.innerHTML =
          '<div class="tg-sim-head">诊断（原「效果验证」）</div>'
          + '<div class="tg-sim-kpi">'
          + '<span>分 <b>' + esc(String(v.score != null ? v.score : '—')) + '</b></span>'
          + '<span>归因 <b>' + pct(a.attributed_share) + '</b></span>'
          + '<span>unscoped <b>' + num(a.unscoped_total) + '</b></span>'
          + '</div>'
          + '<div class="tg-sim-advice"><div class="tg-sim-advice__t">告警与建议</div><ul>'
          + tips.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('')
          + '</ul></div>';
      }
      tgToast('诊断完成 · 见试跑报告区', 'success');
      loadDashboard();
    } catch (e) {
      if (box) box.innerHTML = '<div class="tg-warn">' + esc(String(e.message || e)) + '</div>';
    }
  };

  // 兼容旧四卡 id（若仍存在则轻量填充）
  window.tgLoadMeter = loadDashboard;
  window.tgLoadCache = loadDashboard;
  window.tgLoadRouter = loadDashboard;
  window.tgLoadBudget = loadDashboard;

  /** 分析台改窗口 → TG 主轴 KPI/账单同步 */
  window.onCostWindowChange = function () {
    try { loadDashboard(); } catch (e1) { /* ignore */ }
    try {
      if (window.CostDashboard && typeof window.CostDashboard.refreshDashboard === 'function') {
        window.CostDashboard.refreshDashboard();
      } else if (typeof window.refreshDashboard === 'function') {
        window.refreshDashboard();
      }
    } catch (e2) { /* ignore */ }
  };

  function boot() {
    loadDashboard();
    wireSimPicker();
    // 段锚点平滑滚动
    document.querySelectorAll('.tg-seg-nav a[href^="#"]').forEach(function (a) {
      a.addEventListener('click', function (ev) {
        var id = (a.getAttribute('href') || '').slice(1);
        var el = id && document.getElementById(id);
        if (!el) return;
        ev.preventDefault();
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
    var fw = $('filter-window');
    if (fw && !fw._tgBound) {
      fw._tgBound = true;
      fw.addEventListener('change', function () {
        if (window.onCostWindowChange) window.onCostWindowChange();
        else loadDashboard();
      });
    }
  }

  // 暴露给报表区：点账单行可同步选中
  window.tgSelectSimTask = function (taskId, teamId, title) {
    if (!taskId) return;
    _persistSelectedTask({
      task_id: taskId,
      team_id: teamId || '',
      title: title || taskId,
      status: '',
      has_snapshot: false,
      has_tool_trace: false,
      has_pipeline: true,
    });
    renderSelectedTask();
    // 尽量在列表中高亮
    loadSimTasks().then(function () {
      var panel = $('tg-sim-picker-panel');
      if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
