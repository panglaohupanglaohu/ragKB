/**
 * Agent 记忆中枢页 — 总览 / 生命周期 / Persona（小满·沈弥安·混合）
 * API: /api/v1/agent-memory + 兼容 /api/v1/agent-config/.../memory-core
 */
(function () {
  'use strict';

  const HUB = '/api/v1/agent-memory';
  const CFG = '/api/v1/agent-config';

  let teamId = '';
  let agentId = '';
  let agents = [];
  let seg = 'overview';
  let overview = null;

  function toast(msg) {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 2200);
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  async function api(path, opts) {
    if (window.api && typeof window.api === 'function') {
      try {
        return await window.api(path, opts);
      } catch (e) {
        // 统一错误文案
        const msg = (e && (e.message || e.detail)) || String(e);
        if (/401|认证|登录/.test(msg)) {
          throw new Error('未登录或会话过期，请先登录后再打开 Agent记忆');
        }
        if (/404|Not Found/.test(msg)) {
          throw new Error('接口 404：后端可能未加载记忆路由，请重启 ./start.sh 后硬刷新');
        }
        throw e;
      }
    }
    const r = await fetch(path, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(opts && opts.headers) },
      ...opts,
    });
    if (!r.ok) {
      const t = await r.text();
      if (r.status === 401) {
        throw new Error('未登录或会话过期，请先登录后再打开 Agent记忆');
      }
      if (r.status === 404) {
        throw new Error('接口 404：后端可能未加载记忆路由，请重启 ./start.sh 后硬刷新');
      }
      throw new Error(t || r.statusText);
    }
    return r.json();
  }

  function stateChip(state) {
    const map = {
      active: ['ok', '活体'],
      shared: ['ok', '共享中'],
      sealed: ['warn', '已封存'],
      unbound: ['', '未绑定'],
      destroyed: ['bad', '已销毁'],
      transferring: ['warn', '传递中'],
      archived: ['warn', '凭吊'],
    };
    const [cls, lab] = map[state] || ['', state || '?'];
    return `<span class="chip ${cls}">${esc(lab)}</span>`;
  }

  function memoryStyleName(a) {
    const s = (a && a.memory_style) || {};
    return s.name || `${(a && (a.name || a.agent_id)) || 'Agent'}的记忆方式`;
  }

  function pct(v) {
    const n = Number(v);
    return Number.isFinite(n) ? `${Math.round(n * 100)}%` : '—';
  }

  async function loadTeams() {
    const sel = document.getElementById('team-select');
    let teams = [];
    try {
      const data = await api(`${CFG}/teams`);
      teams = Array.isArray(data) ? data : data.items || data.teams || [];
    } catch (e) {
      toast('加载团队失败');
    }
    if (!teams.length) {
      sel.innerHTML = '<option value="">无团队</option>';
      return;
    }
    sel.innerHTML = teams
      .map((t) => {
        const id = t.team_id || t.id;
        const name = t.name || id;
        return `<option value="${esc(id)}">${esc(name)}</option>`;
      })
      .join('');
    teamId = teams[0].team_id || teams[0].id;
    sel.value = teamId;
    sel.onchange = () => {
      teamId = sel.value;
      agentId = '';
      refresh();
    };
  }

  async function loadOverview() {
    if (!teamId) return;
    let hubErr = null;
    try {
      overview = await api(`${HUB}/overview?team_id=${encodeURIComponent(teamId)}`);
    } catch (e) {
      hubErr = e;
      overview = null;
    }
    // hub 失败时回退：读团队 agents + 逐个 lifecycle（兼容旧后端）
    if (!overview || !Array.isArray(overview.agents)) {
      try {
        const team = await api(`${CFG}/teams/${encodeURIComponent(teamId)}`);
        const agMap = (team && team.agents) || {};
        const rows = [];
        for (const id of Object.keys(agMap)) {
          let st = { state: 'unbound', persona: 'hybrid' };
          try {
            st = (await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(id)}/lifecycle`)) || st;
          } catch (_) {
            try {
              st =
                (await api(
                  `${CFG}/teams/${encodeURIComponent(teamId)}/agents/${encodeURIComponent(id)}/memory-core/lifecycle`
                )) || st;
            } catch (__) {}
          }
          rows.push({
            agent_id: id,
            name: (agMap[id] && agMap[id].name) || id,
            role: (agMap[id] && agMap[id].role) || '',
            state: st.state || 'unbound',
            persona: st.persona || 'hybrid',
            counts: {},
            health: st.bound ? 20 : 0,
          });
        }
        const by_state = {};
        const by_persona = {};
        rows.forEach((r) => {
          by_state[r.state] = (by_state[r.state] || 0) + 1;
          by_persona[r.persona] = (by_persona[r.persona] || 0) + 1;
        });
        overview = {
          team_id: teamId,
          agents: rows,
          by_state,
          by_persona,
          health_avg: 0,
          _fallback: true,
        };
        if (hubErr) {
          toast((hubErr && hubErr.message) || '记忆总览降级加载（请确认后端已挂载 /api/v1/agent-memory）');
        }
      } catch (e2) {
        overview = { agents: [], by_state: {}, by_persona: {} };
        toast((hubErr && hubErr.message) || (e2 && e2.message) || '加载失败');
      }
    }
    agents = overview.agents || [];
    renderAgentList();
    renderMain();
  }

  function renderAgentList() {
    const box = document.getElementById('agent-list');
    if (!agents.length) {
      box.innerHTML = '<div class="empty">该团队暂无智能体</div>';
      return;
    }
    box.innerHTML = agents
      .map((a) => {
        const id = a.agent_id;
        const active = id === agentId ? 'active' : '';
        return `<button type="button" class="mem-agent ${active}" data-id="${esc(id)}">
          <div class="name">${esc(a.name || id)}</div>
          <div class="meta">${stateChip(a.state)} ${esc(memoryStyleName(a))}
            · 情节 ${(a.counts && a.counts.log) || 0}
            · 健康 ${esc(String(a.health != null ? a.health : '—'))}
          </div>
        </button>`;
      })
      .join('');
    box.querySelectorAll('.mem-agent').forEach((btn) => {
      btn.onclick = () => {
        agentId = btn.getAttribute('data-id');
        if (seg === 'overview') seg = 'agents';
        setSegActive();
        renderAgentList();
        renderMain();
      };
    });
  }

  function setSegActive() {
    document.querySelectorAll('.mem-seg').forEach((b) => {
      b.classList.toggle('active', b.getAttribute('data-seg') === seg);
    });
  }

  async function renderMain() {
    const main = document.getElementById('main-panel');
    if (seg === 'overview') {
      const byS = (overview && overview.by_state) || {};
      const health = overview && overview.health_avg != null ? overview.health_avg : '—';
      const activeN = overview && overview.active_memory_agents != null
        ? overview.active_memory_agents
        : (byS.active || 0) + (byS.shared || 0);
      const top = agents
        .slice()
        .sort((a, b) => (b.health || 0) - (a.health || 0))
        .slice(0, 5);
      main.innerHTML = `
        <h2 style="margin:0 0 12px;font-size:16px">团队记忆总览</h2>
        <div class="stat-row">
          <div class="stat"><b>${agents.length}</b><span>智能体</span></div>
          <div class="stat"><b>${health}</b><span>平均健康分</span></div>
          <div class="stat"><b>${activeN}</b><span>活体+共享</span></div>
          <div class="stat"><b>${byS.sealed || 0}</b><span>封存/凭吊</span></div>
          <div class="stat"><b>${byS.destroyed || 0}</b><span>已销毁</span></div>
        </div>
        <div class="audit-line" style="margin-bottom:12px">
          团队中的记忆方式不再按模板分组；每个 Agent 拥有自己的连续性、克制性、可塑性与情绪通透度。
        </div>
        <h3 style="font-size:13px;margin:8px 0">记忆健康 Top</h3>
        <div>${
          top.length
            ? top
                .map(
                  (a) =>
                    `<div class="audit-line" style="cursor:pointer" data-pick="${esc(a.agent_id)}">
                      <b>${esc(a.name || a.agent_id)}</b> ${stateChip(a.state)}
                      · 健康 ${esc(String(a.health ?? 0))}
                      · 日志 ${esc(String((a.counts && a.counts.log) || 0))}
                    </div>`
                )
                .join('')
            : '<div class="empty">暂无</div>'
        }</div>
        <p style="font-size:12px;color:#6B7280;line-height:1.55;margin-top:12px">
          共享矩阵只共享有来源的痕迹；传递台复制自传连续性。程序性记忆由技能与熟练度承载，不伪装成文本记忆层。
        </p>
        <div class="panel-actions">
          <a class="btn" href="/agent-team-config.html">打开智能体配置</a>
          <button type="button" class="btn btn-primary" onclick="window.__memRefresh()">刷新总览</button>
        </div>`;
      main.querySelectorAll('[data-pick]').forEach((row) => {
        row.onclick = () => {
          agentId = row.getAttribute('data-pick');
          seg = 'agents';
          setSegActive();
          renderAgentList();
          renderMain();
        };
      });
      return;
    }

    if (seg === 'share') {
      await renderShare(main);
      return;
    }
    if (seg === 'transfer') {
      await renderTransfer(main);
      return;
    }

    if (!agentId) {
      main.innerHTML = '<div class="empty">请先在左侧选择智能体</div>';
      return;
    }

    if (seg === 'persona') {
      await renderPersona(main);
      return;
    }
    if (seg === 'lifecycle') {
      await renderLifecycle(main);
      return;
    }
    // agents — 拟生摘要 + 快捷
    await renderAgentDetail(main);
  }

  async function fetchStatus() {
    return api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/lifecycle`);
  }

  async function fetchOverviewAgent() {
    try {
      return await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}`);
    } catch (e) {
      return api(
        `${CFG}/teams/${encodeURIComponent(teamId)}/agents/${encodeURIComponent(agentId)}/memory-core`
      );
    }
  }

  async function renderAgentDetail(main) {
    main.innerHTML = '<div class="empty">加载记忆…</div>';
    let data, st;
    try {
      st = await fetchStatus();
      data = await fetchOverviewAgent();
    } catch (e) {
      main.innerHTML = `<div class="empty">加载失败：${esc(e.message || e)}
        <div class="panel-actions"><button class="btn btn-primary" data-act="bind">绑定记忆</button></div></div>`;
      wireActions(main);
      return;
    }
    const c = data.counts || {};
    main.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap">
        <div>
          <h2 style="margin:0;font-size:16px">${esc(data.agent_id || agentId)}</h2>
          <div style="margin-top:6px">${stateChip(st.state)}
            <span class="chip">${esc(memoryStyleName(data))}</span>
          </div>
        </div>
        <div class="panel-actions" style="margin:0">
          <a class="btn" href="/agent-team-config.html?team_id=${encodeURIComponent(teamId)}&agent_id=${encodeURIComponent(agentId)}&atab=ag-memory">打开记忆详情</a>
          <a class="btn" href="/agent-memory.html?team_id=${encodeURIComponent(teamId)}&agent_id=${encodeURIComponent(agentId)}&seg=share">共享</a>
          <a class="btn" href="/agent-memory.html?team_id=${encodeURIComponent(teamId)}&agent_id=${encodeURIComponent(agentId)}&seg=transfer">传递</a>
        </div>
      </div>
      <div class="stat-row" style="margin-top:14px">
        <div class="stat"><b>${c.log || 0}</b><span>情节</span></div>
        <div class="stat"><b>${c.perception || 0}</b><span>感觉痕迹</span></div>
        <div class="stat"><b>${c.semantic || 0}</b><span>语义核</span></div>
        <div class="stat"><b>${c.intentions_pending || 0}</b><span>前瞻意图·过程</span></div>
        <div class="stat"><b>${c.affect_labels || 0}</b><span>情绪选择场</span></div>
        <div class="stat"><b>${c.forgotten || 0}</b><span>已遗忘</span></div>
      </div>
      <p style="font-size:12px;color:#6B7280">💬 ${esc(data.tone_hint || '—')}</p>
      ${renderDynamicState(data)}
      ${renderSystemsBlocks(data)}
      <div class="panel-actions">
        <button class="btn btn-primary" data-act="bind">绑定/激活</button>
        <button class="btn" data-act="save">保存固化</button>
        <button class="btn" data-act="consolidate">巩固→语义</button>
        <button class="btn" data-act="forget">遗忘 tick</button>
        <button class="btn" data-act="drift">拓扑漂移</button>
        <button class="btn" data-act="seal">封存</button>
        <button class="btn" data-act="unseal">启封</button>
        <button class="btn btn-danger" data-act="destroy">销毁</button>
      </div>
      <h3 style="font-size:13px;margin:16px 0 8px">工作台</h3>
      <div>${(data.working || [])
        .map((w) => `<div class="audit-line">${esc(w.text || '')} <span style="color:#9CA3AF">${esc(w.source || '')}</span></div>`)
        .join('') || '<div class="empty">空</div>'}
      </div>
      <h3 style="font-size:13px;margin:16px 0 8px">最近情节</h3>
      <div>${(data.log || [])
        .slice(-8)
        .reverse()
        .map(
          (e) =>
            `<div class="audit-line"><b>${esc(e.action || '')}</b> ${esc((e.detail || '').slice(0, 80))}</div>`
        )
        .join('') || '<div class="empty">暂无</div>'}
      </div>
      <h3 style="font-size:13px;margin:16px 0 8px">遗忘审计（soft）</h3>
      <div>${(data.forgotten_recent || [])
        .slice(0, 8)
        .map(
          (e) =>
            `<div class="audit-line" style="opacity:.75">✕ ${esc(e.action || '')} · ${esc((e.detail || '').slice(0, 60))}</div>`
        )
        .join('') || '<div class="empty">尚无 soft-forget</div>'}
      </div>`;
    wireActions(main);
  }

  function renderDynamicState(data) {
    const s = data.memory_style || {};
    const d = data.dynamic_state || {};
    return `<div style="border:1px solid #D8DEE8;border-radius:10px;padding:12px;margin:10px 0;background:linear-gradient(135deg,#F8FAFC,#F2F7F4)">
      <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap">
        <div><b>${esc(s.name || memoryStyleName(data))}</b><div style="font-size:10px;color:#9CA3AF">version ${esc(String(s.version || 1))}</div></div>
        <button type="button" class="btn" data-act="edit-style">调整我的记忆方式</button>
      </div>
      <div class="stat-row" style="margin:10px 0 0">
        <div class="stat"><b>${pct(s.continuity)}</b><span>连续性</span></div>
        <div class="stat"><b>${pct(s.restraint)}</b><span>克制性</span></div>
        <div class="stat"><b>${pct(s.plasticity)}</b><span>可塑性</span></div>
        <div class="stat"><b>${pct(s.affective_permeability)}</b><span>情绪通透度</span></div>
        <div class="stat"><b>${pct(d.continuity_index)}</b><span>当前连续指数</span></div>
      </div>
      <div style="font-size:11px;color:#6B7280">活跃记忆质量 ${esc(String(d.active_memory_mass ?? '—'))} · 遗忘比 ${pct(d.forgetting_ratio)} · 情绪能量 ${pct(d.charge_energy)}</div>
    </div>`;
  }

  function renderSystemsBlocks(data) {
    const sys = (data.systems && data.systems.systems) || {};
    const topo = data.topology || (data.systems && data.systems.topology) || {};
    const order = [
      ['layer', '保存的痕迹'],
      ['field', '选择场 · 不存事实'],
      ['process', '过程 · 不作为记忆层'],
    ];
    const byKind = { layer: [], field: [], process: [] };
    Object.keys(sys).forEach((k) => {
      const s = sys[k] || {};
      const kind = s.kind || 'layer';
      if (!byKind[kind]) byKind[kind] = [];
      byKind[kind].push({ id: k, ...s });
    });
    const cols = order
      .map(([kind, title]) => {
        const items = byKind[kind] || [];
        return `<div style="flex:1;min-width:140px;border:1px solid #E5E7EB;border-radius:8px;padding:10px;background:#FAFAFA">
          <div style="font-size:11px;font-weight:700;color:#6B7280;margin-bottom:8px">${esc(title)}</div>
          ${items
            .map(
              (it) =>
                `<div style="font-size:12px;margin-bottom:6px"><b>${esc(it.label || it.id)}</b>
                  <span style="color:#9CA3AF">${it.count != null ? it.count : (it.slots ? it.slots.length : '—')}</span>
                  ${it.note ? `<div style="font-size:10px;color:#9CA3AF;line-height:1.3">${esc(it.note)}</div>` : ''}
                </div>`
            )
            .join('') || '<div class="empty">—</div>'}
        </div>`;
      })
      .join('');
    const topoLine = `cap情节 ${esc(String(topo.episodic_soft_cap ?? '—'))} · 巩固≥${esc(
      String(topo.consolidate_min_importance ?? '—')
    )} · 遗忘 ${esc(String(topo.forget_aggressiveness ?? '—'))} · 电荷传 ${esc(
      String(topo.charge_transfer ?? '—')
    )}`;
    return `
      <h3 style="font-size:13px;margin:14px 0 8px">动态记忆系统：痕迹 / 过程 / 选择场</h3>
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">${cols}</div>
      <div class="audit-line" style="font-size:11px;color:#6B7280">拓扑 ${topoLine}</div>
    `;
  }

  async function renderLifecycle(main) {
    main.innerHTML = '<div class="empty">加载生命周期…</div>';
    let st, audit;
    try {
      st = await fetchStatus();
      audit = await api(
        `${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/audit?limit=30`
      );
    } catch (e) {
      main.innerHTML = `<div class="empty">${esc(e.message || e)}</div>`;
      return;
    }
    main.innerHTML = `
      <h2 style="margin:0 0 8px;font-size:16px">生命周期</h2>
      <p>当前状态 ${stateChip(st.state)} · 记忆方式会随时间和适应度缓慢变化</p>
      <div class="panel-actions">
        <button class="btn btn-primary" data-act="bind">bind 激活</button>
        <button class="btn" data-act="save">save 固化(+反思)</button>
        <button class="btn" data-act="share">share 标记</button>
        <button class="btn" data-act="unshare">unshare</button>
        <button class="btn" data-act="seal">seal 封存</button>
        <button class="btn" data-act="unseal">unseal 启封</button>
        <button class="btn btn-danger" data-act="destroy">destroy 销毁</button>
      </div>
      <h3 style="font-size:13px;margin:16px 0 8px">审计</h3>
      <div>${(audit.audit || [])
        .slice()
        .reverse()
        .map(
          (a) =>
            `<div class="audit-line">${esc(a.t)} · ${esc(a.action)} ${a.from ? esc(a.from) + '→' + esc(a.to) : ''}</div>`
        )
        .join('') || '<div class="empty">暂无审计</div>'}
      </div>`;
    wireActions(main);
  }

  async function renderPersona(main) {
    main.innerHTML = '<div class="empty">加载记忆方式…</div>';
    try {
      const data = await fetchOverviewAgent();
      const style = data.memory_style || {};
      const dyn = data.dynamic_state || {};
      main.innerHTML = `
        <h2 style="margin:0 0 8px;font-size:16px">${esc(style.name || memoryStyleName(data))}</h2>
        <p style="font-size:12px;color:#6B7280;line-height:1.6">
          这不是预设人格。它是该 Agent 经历任务、失败、物竞存活、巩固和遗忘后形成的独有记忆方式。
          调整的是倾向，不直接改写记忆内容；后续经历仍会让它漂移。
        </p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px">
          <label>名称<input class="fi" id="style-name" value="${esc(style.name || memoryStyleName(data))}" style="width:100%;box-sizing:border-box"></label>
          <label>连续性 <span id="v-continuity">${pct(style.continuity)}</span><input id="style-continuity" type="range" min="0" max="1" step="0.05" value="${esc(String(style.continuity ?? .5))}" style="width:100%"></label>
          <label>克制性 <span id="v-restraint">${pct(style.restraint)}</span><input id="style-restraint" type="range" min="0" max="1" step="0.05" value="${esc(String(style.restraint ?? .5))}" style="width:100%"></label>
          <label>可塑性 <span id="v-plasticity">${pct(style.plasticity)}</span><input id="style-plasticity" type="range" min="0" max="1" step="0.05" value="${esc(String(style.plasticity ?? .5))}" style="width:100%"></label>
          <label>情绪通透度 <span id="v-affective">${pct(style.affective_permeability)}</span><input id="style-affective" type="range" min="0" max="1" step="0.05" value="${esc(String(style.affective_permeability ?? .4))}" style="width:100%"></label>
        </div>
        <div class="audit-line" style="margin-top:14px">当前连续指数 ${pct(dyn.continuity_index)} · 遗忘比 ${pct(dyn.forgetting_ratio)} · 活跃质量 ${esc(String(dyn.active_memory_mass ?? '—'))}</div>
        <div class="panel-actions"><button type="button" class="btn btn-primary" id="save-memory-style">保存倾向</button></div>
        <h3 style="font-size:13px;margin:16px 0 8px">演化史</h3>
        <div>${(style.history || []).slice(-12).reverse().map((h) => `<div class="audit-line">${esc(String(h.t || ''))} · ${esc(h.reason || '')}${h.fitness_delta != null ? ` · Δ${esc(String(h.fitness_delta))}` : ''}</div>`).join('') || '<div class="empty">尚无</div>'}</div>`;
      [['continuity','continuity'],['restraint','restraint'],['plasticity','plasticity'],['affective','affective']].forEach(([id,vid]) => {
        const input = document.getElementById(`style-${id}`);
        const value = document.getElementById(`v-${vid}`);
        if (input && value) input.oninput = () => { value.textContent = pct(input.value); };
      });
      document.getElementById('save-memory-style').onclick = async () => {
        const body = {
          name: document.getElementById('style-name').value,
          continuity: Number(document.getElementById('style-continuity').value),
          restraint: Number(document.getElementById('style-restraint').value),
          plasticity: Number(document.getElementById('style-plasticity').value),
          affective_permeability: Number(document.getElementById('style-affective').value),
          reason: 'owner_tuning',
        };
        await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/memory-style`, { method: 'PUT', body: JSON.stringify(body) });
        toast('已保存；后续经历仍会继续改变它');
        await loadOverview();
        await renderPersona(main);
      };
    } catch (e) {
      main.innerHTML = `<div class="empty">${esc(e.message || e)}</div>`;
    }
  }

  async function renderShare(main) {
    main.innerHTML = '<div class="empty">加载共享矩阵…</div>';
    let matrix;
    try {
      matrix = await api(`${HUB}/${encodeURIComponent(teamId)}/share-matrix`);
    } catch (e) {
      main.innerHTML = `<div class="empty">加载失败：${esc(e.message || e)}</div>`;
      return;
    }
    const cells = matrix.cells || [];
    const options = agents
      .map((a) => `<option value="${esc(a.agent_id)}">${esc(a.name || a.agent_id)}</option>`)
      .join('');
    main.innerHTML = `
      <h2 style="margin:0 0 8px;font-size:16px">共享矩阵</h2>
      <p style="font-size:12px;color:#6B7280;margin:0 0 12px;line-height:1.5">
        默认共享 <b>情节 / 感觉 / 前瞻 / 语义</b>，不含 <b>情绪电荷</b>。
        沈弥安 Persona 强制剥离电荷场。前瞻意图是过程，不是记忆层。
      </p>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:8px;align-items:end;margin-bottom:14px">
        <div>
          <label style="font-size:11px;color:#6B7280">拥有者 owner</label><br>
          <select class="fi" id="share-owner" style="width:100%">${options}</select>
        </div>
        <div>
          <label style="font-size:11px;color:#6B7280">被授权 grantee</label><br>
          <select class="fi" id="share-grantee" style="width:100%">${options}</select>
        </div>
        <div>
          <label style="font-size:11px;color:#6B7280">角色</label><br>
          <select class="fi" id="share-role" style="width:100%">
            <option value="reader">reader 只读</option>
            <option value="co_writer">co_writer 协作写</option>
          </select>
        </div>
        <button type="button" class="btn btn-primary" id="share-grant-btn">授权</button>
      </div>
      <div style="font-size:11px;color:#6B7280;margin-bottom:8px">层（默认不含 affect）
        <label style="margin-left:8px"><input type="checkbox" class="share-layer" value="log" checked> log</label>
        <label style="margin-left:6px"><input type="checkbox" class="share-layer" value="perception" checked> perception</label>
        <label style="margin-left:6px"><input type="checkbox" class="share-layer" value="intentions" checked> 前瞻意图</label>
        <label style="margin-left:6px"><input type="checkbox" class="share-layer" value="semantic" checked> 语义核</label>
        <label style="margin-left:6px"><input type="checkbox" class="share-layer" value="affect"> affect</label>
      </div>
      <h3 style="font-size:13px;margin:12px 0 8px">当前授权 ${cells.length} 条</h3>
      <div id="share-cells">
        ${
          cells.length
            ? cells
                .map(
                  (c) => `<div class="audit-line" style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap">
            <span><b>${esc(c.owner)}</b> → <b>${esc(c.grantee)}</b>
              <span class="chip">${esc(c.role)}</span>
              ${(c.layers || []).map((L) => `<span class="chip ok">${esc(L)}</span>`).join('')}
            </span>
            <span style="display:flex;gap:4px;flex-wrap:wrap">
              <button type="button" class="btn" data-preview-owner="${esc(c.owner)}" data-preview-reader="${esc(c.grantee)}" data-preview-layer="log">预览log</button>
              ${
                c.role === 'co_writer'
                  ? `<button type="button" class="btn" data-cowrite-owner="${esc(c.owner)}" data-cowrite-writer="${esc(c.grantee)}">协作写</button>`
                  : ''
              }
              <button type="button" class="btn" data-revoke-owner="${esc(c.owner)}" data-revoke-grantee="${esc(c.grantee)}">撤销</button>
            </span>
          </div>`
                )
                .join('')
            : '<div class="empty">暂无授权</div>'
        }
      </div>
      <div id="share-preview" style="margin-top:12px;padding:10px;border:1px dashed #D8DEE8;border-radius:8px;font-size:12px;color:#4B5568;min-height:40px">
        选择「预览log」查看被授权可读内容
      </div>`;

    const grantBtn = document.getElementById('share-grant-btn');
    if (grantBtn) {
      grantBtn.onclick = async () => {
        const owner = document.getElementById('share-owner').value;
        const grantee = document.getElementById('share-grantee').value;
        const role = document.getElementById('share-role').value;
        const layers = [...document.querySelectorAll('.share-layer:checked')].map((x) => x.value);
        if (!owner || !grantee || owner === grantee) {
          toast('请选择不同的 owner / grantee');
          return;
        }
        try {
          await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(owner)}/share`, {
            method: 'POST',
            body: JSON.stringify({ grantee, role, layers }),
          });
          toast('已授权');
          await renderShare(main);
          await loadOverview();
        } catch (e) {
          toast('失败: ' + (e.message || e));
        }
      };
    }
    main.querySelectorAll('[data-revoke-owner]').forEach((btn) => {
      btn.onclick = async () => {
        const owner = btn.getAttribute('data-revoke-owner');
        const grantee = btn.getAttribute('data-revoke-grantee');
        try {
          await api(
            `${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(owner)}/share/${encodeURIComponent(grantee)}`,
            { method: 'DELETE' }
          );
          toast('已撤销');
          await renderShare(main);
        } catch (e) {
          toast('失败: ' + (e.message || e));
        }
      };
    });
    main.querySelectorAll('[data-preview-owner]').forEach((btn) => {
      btn.onclick = async () => {
        const owner = btn.getAttribute('data-preview-owner');
        const reader = btn.getAttribute('data-preview-reader');
        const layer = btn.getAttribute('data-preview-layer') || 'log';
        const box = document.getElementById('share-preview');
        try {
          const r = await api(
            `${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(owner)}/shared/${encodeURIComponent(reader)}/${encodeURIComponent(layer)}?limit=8`
          );
          const rows = Array.isArray(r.data) ? r.data : [];
          box.innerHTML = rows.length
            ? `<b>预览 ${esc(owner)}.${esc(layer)}</b> (reader=${esc(reader)})<br>` +
              rows
                .slice()
                .reverse()
                .map(
                  (e) =>
                    `· <b>${esc(e.action || '')}</b> ${esc((e.detail || '').slice(0, 100))}`
                )
                .join('<br>')
            : `无数据（${esc(owner)}.${esc(layer)}）`;
        } catch (e) {
          box.textContent = '预览失败: ' + (e.message || e);
        }
      };
    });
    main.querySelectorAll('[data-cowrite-owner]').forEach((btn) => {
      btn.onclick = async () => {
        const owner = btn.getAttribute('data-cowrite-owner');
        const writer = btn.getAttribute('data-cowrite-writer');
        const detail = prompt('协作写入日志内容（将记入 owner 的 log）：');
        if (!detail) return;
        try {
          await api(
            `${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(owner)}/shared/${encodeURIComponent(writer)}/log`,
            {
              method: 'POST',
              body: JSON.stringify({
                action: '协作写入',
                detail,
                importance: 6,
              }),
            }
          );
          toast('协作写入成功');
        } catch (e) {
          toast('失败: ' + (e.message || e));
        }
      };
    });
  }

  async function renderTransfer(main) {
    main.innerHTML = '<div class="empty">加载 Will 传递台…</div>';
    let history = [];
    let wills = [];
    let migrations = [];
    let inherited = null;
    try {
      const r = await api(`${HUB}/transfers?team_id=${encodeURIComponent(teamId)}&limit=20`);
      history = r.transfers || [];
    } catch (_) {
      history = [];
    }
    try {
      const wr = await api(
        `${HUB}/wills?team_id=${encodeURIComponent(teamId)}&limit=20`
      );
      wills = wr.wills || [];
    } catch (_) {
      wills = [];
    }
    try {
      const mr = await api(`${HUB}/migrations?limit=15`);
      migrations = mr.transactions || [];
    } catch (_) {
      migrations = [];
    }
    if (agentId) {
      try {
        const ir = await api(
          `${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/inherited`
        );
        inherited = ir.inherited || null;
      } catch (_) {
        inherited = null;
      }
    }
    const options = agents
      .map((a) => `<option value="${esc(a.agent_id)}">${esc(a.name || a.agent_id)}</option>`)
      .join('');
    const layerChecks = ['log', 'perception', 'intentions', 'semantic', 'affect']
      .map(
        (l) =>
          `<label style="margin-right:10px;font-size:12px"><input type="checkbox" class="will-layer" value="${l}" ${
            l === 'affect' ? '' : 'checked'
          }> ${l}</label>`
      )
      .join('');
    main.innerHTML = `
      <h2 style="margin:0 0 8px;font-size:16px">Will 传递台</h2>
      <p style="font-size:12px;color:#6B7280;line-height:1.5;margin:0 0 12px">
        流程：创建 Will → 预检（计数/哈希/冲突）→ 执行事务。默认 <b>merge</b> 写入继承分区，不覆盖受益方本地记忆。
        失败会回滚并显示原因；凭吊源显示「这是回放，不是本人」。
      </p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">
        <div>
          <label style="font-size:11px;color:#6B7280">源 Agent（立遗嘱者）</label><br>
          <select class="fi" id="xfer-from" style="width:100%">${options}</select>
        </div>
        <div>
          <label style="font-size:11px;color:#6B7280">受益 Agent</label><br>
          <select class="fi" id="xfer-to" style="width:100%">${options}</select>
        </div>
        <div>
          <label style="font-size:11px;color:#6B7280">冲突策略</label><br>
          <select class="fi" id="xfer-strategy" style="width:100%">
            <option value="merge" selected>merge 继承分区（默认）</option>
            <option value="selective">selective 仅所选层</option>
            <option value="replace_all">replace_all 覆盖活动层</option>
          </select>
        </div>
        <div>
          <label style="font-size:11px;color:#6B7280">意图交接</label><br>
          <select class="fi" id="xfer-ho" style="width:100%">
            <option value="ask_new_owner">ask_new_owner 待新主人确认</option>
            <option value="auto">auto 自动承接</option>
            <option value="drop">drop 全部放弃</option>
          </select>
        </div>
        <div style="grid-column:1/-1">
          <label style="font-size:11px;color:#6B7280">迁移层 scope</label><br>
          ${layerChecks}
        </div>
        <div style="grid-column:1/-1">
          <label style="font-size:11px;color:#6B7280">备注</label><br>
          <input class="fi" id="xfer-note" style="width:100%;box-sizing:border-box" placeholder="交接说明"/>
        </div>
      </div>
      <label style="font-size:12px;color:#4B5568;display:flex;align-items:center;gap:6px;margin-bottom:12px">
        <input type="checkbox" id="xfer-keep" checked> 保留原件凭吊 keep_memorial
      </label>
      <div class="panel-actions" style="display:flex;gap:8px;flex-wrap:wrap">
        <button type="button" class="btn" id="will-create">① 创建 Will</button>
        <button type="button" class="btn" id="will-preflight" disabled>② 预检</button>
        <button type="button" class="btn btn-primary" id="will-execute" disabled>③ 执行</button>
      </div>
      <div id="will-report" style="margin-top:12px"></div>
      <h3 style="font-size:13px;margin:18px 0 8px">遗嘱列表</h3>
      <div id="will-list">
        ${
          wills.length
            ? wills
                .map(
                  (w) => `<div class="audit-line">
            <b>${esc((w.testator && w.testator.agent_id) || '')}</b> →
            <b>${esc((w.beneficiary && w.beneficiary.agent_id) || '')}</b>
            · ${esc(w.conflict_strategy || '')} · <span class="chip">${esc(w.status || '')}</span>
            <span style="color:#9AA3AF">${esc(w.will_id || '')}</span>
          </div>`
                )
                .join('')
            : '<div class="empty">暂无遗嘱</div>'
        }
      </div>
      <h3 style="font-size:13px;margin:18px 0 8px">迁移事务</h3>
      <div>
        ${
          migrations.length
            ? migrations
                .map((tx) => {
                  const st = tx.state || '';
                  const color =
                    st === 'committed' ? '#059669' : st === 'rolled_back' ? '#DC2626' : '#6B7280';
                  return `<div class="audit-line">
              <span style="color:${color};font-weight:600">${esc(st)}</span>
              · ${esc(tx.strategy || '')}
              · tx ${esc(tx.tx_id || '')}
              ${tx.error ? `· <span style="color:#DC2626">${esc(tx.error)}</span>` : ''}
              ${
                tx.validation
                  ? `· strength=${esc((tx.validation && tx.validation.validation_strength) || '')}`
                  : ''
              }
            </div>`;
                })
                .join('')
            : '<div class="empty">暂无迁移事务</div>'
        }
      </div>
      <h3 style="font-size:13px;margin:18px 0 8px">当前 Agent 继承分区</h3>
      <div>
        ${
          inherited && (inherited.partitions || []).length
            ? (inherited.partitions || [])
                .map((p) => {
                  const src = (p.source_agent && p.source_agent.agent_id) || '?';
                  const counts = p.record_counts || {};
                  return `<div class="audit-line">
              <span class="chip warn">继承自 ${esc(src)}</span>
              · log ${counts.log || 0} · semantic ${counts.semantic || 0}
              · transfer ${esc(p.transfer_id || '')}
            </div>`;
                })
                .join('')
            : '<div class="empty">无继承分区（或未选中 Agent）</div>'
        }
      </div>
      <h3 style="font-size:13px;margin:18px 0 8px">历史传递</h3>
      <div>
        ${
          history.length
            ? history
                .map(
                  (t) => `<div class="audit-line">
            <b>${esc(t.from)}</b> → <b>${esc(t.to)}</b>
            · ${esc(t.strategy || t.handover_intentions || '')}
            · 日志${(t.copied && t.copied.log) || 0}
            ${t.keep_memorial ? '<span class="chip warn">凭吊</span>' : ''}
            <span style="color:#9AA3AF">${esc(t.transfer_id || t.will_id || '')}</span>
          </div>`
                )
                .join('')
            : '<div class="empty">暂无传递记录</div>'
        }
      </div>`;

    let currentWillId = '';
    const reportEl = document.getElementById('will-report');
    const btnPre = document.getElementById('will-preflight');
    const btnEx = document.getElementById('will-execute');

    function selectedLayers() {
      return Array.from(main.querySelectorAll('.will-layer:checked')).map((el) => el.value);
    }

    function renderReport(report, title) {
      if (!reportEl) return;
      const counts = report.record_counts || (report.validation && report.validation.counts) || {};
      const hashes = report.layer_hashes || (report.validation && report.validation.layer_hashes) || {};
      const conflicts = report.conflicts || [];
      const ok = report.ok !== false && !(report.validation && report.validation.ok === false);
      reportEl.innerHTML = `
        <div style="border:1px solid ${ok ? '#86EFAC' : '#FECACA'};background:${
          ok ? '#F0FDF4' : '#FEF2F2'
        };border-radius:8px;padding:12px">
          <div style="font-weight:600;margin-bottom:6px">${esc(title || '预检报告')} · ${
            ok ? '通过' : '未通过'
          }</div>
          <div style="font-size:12px;color:#374151">策略 ${esc(
            report.strategy || ''
          )} · strength ${esc(
            (report.validation && report.validation.validation_strength) || report.validation_strength || ''
          )}</div>
          <div style="font-size:12px;margin-top:6px">计数：${esc(JSON.stringify(counts))}</div>
          <div style="font-size:11px;margin-top:4px;color:#6B7280;word-break:break-all">哈希：${esc(
            JSON.stringify(hashes)
          )}</div>
          ${
            conflicts.length
              ? `<div style="font-size:12px;color:#B45309;margin-top:6px">冲突：${esc(
                  conflicts.join('; ')
                )}</div>`
              : ''
          }
          ${
            report.error
              ? `<div style="font-size:12px;color:#DC2626;margin-top:6px">错误：${esc(
                  report.error
                )}</div>`
              : ''
          }
        </div>`;
    }

    const createBtn = document.getElementById('will-create');
    if (createBtn) {
      createBtn.onclick = async () => {
        const from = document.getElementById('xfer-from').value;
        const to = document.getElementById('xfer-to').value;
        if (!from || !to || from === to) {
          toast('请选择不同的源与受益者');
          return;
        }
        try {
          const r = await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(from)}/wills`, {
            method: 'POST',
            body: JSON.stringify({
              beneficiary: to,
              strategy: document.getElementById('xfer-strategy').value,
              layers: selectedLayers(),
              handover_intentions: document.getElementById('xfer-ho').value,
              keep_memorial: document.getElementById('xfer-keep').checked,
              note: document.getElementById('xfer-note').value || '',
            }),
          });
          currentWillId = (r.will && r.will.will_id) || '';
          toast('Will 已创建 ' + currentWillId);
          if (btnPre) btnPre.disabled = !currentWillId;
          if (btnEx) btnEx.disabled = true;
          if (reportEl) {
            reportEl.innerHTML = `<div class="audit-line">will_id=${esc(currentWillId)} status=${esc(
              (r.will && r.will.status) || 'draft'
            )}</div>`;
          }
        } catch (e) {
          toast('创建失败: ' + (e.message || e));
        }
      };
    }

    if (btnPre) {
      btnPre.onclick = async () => {
        if (!currentWillId) {
          toast('请先创建 Will');
          return;
        }
        try {
          const r = await api(`${HUB}/wills/${encodeURIComponent(currentWillId)}/preflight`, {
            method: 'POST',
            body: '{}',
          });
          renderReport(r.report || r, '预检报告');
          const ok = r.report && r.report.ok;
          if (btnEx) btnEx.disabled = !ok;
          toast(ok ? '预检通过，可执行' : '预检未通过');
        } catch (e) {
          toast('预检失败: ' + (e.message || e));
          if (btnEx) btnEx.disabled = true;
        }
      };
    }

    if (btnEx) {
      btnEx.onclick = async () => {
        if (!currentWillId) {
          toast('请先创建并预检 Will');
          return;
        }
        if (!confirm('确认执行遗嘱迁移？失败将回滚受益方文件。')) return;
        try {
          const r = await api(`${HUB}/wills/${encodeURIComponent(currentWillId)}/execute`, {
            method: 'POST',
            body: JSON.stringify({ idempotency_key: currentWillId }),
          });
          const exec = r.execution || r;
          const state = r.state || exec.state || '';
          if (reportEl) {
            reportEl.innerHTML += `
              <div style="margin-top:10px;border:1px solid #BFDBFE;background:#EFF6FF;border-radius:8px;padding:12px">
                <div style="font-weight:600">执行结果 · ${esc(state)}</div>
                <div style="font-size:12px;margin-top:4px">tx ${esc(exec.tx_id || '')}</div>
                <div style="font-size:12px">partition ${esc(
                  (exec.partition && exec.partition.partition_id) ||
                    (exec.report && exec.report.partition_id) ||
                    ''
                )}</div>
                <div style="font-size:12px">计数 ${esc(
                  JSON.stringify((exec.report && exec.report.record_counts) || {})
                )}</div>
                ${
                  state === 'rolled_back' || exec.error
                    ? `<div style="color:#DC2626">回滚原因：${esc(exec.error || '')}</div>`
                    : ''
                }
              </div>`;
          }
          toast(state === 'executed' || r.ok ? '迁移已提交' : '执行结束: ' + state);
          await loadOverview();
          await renderTransfer(main);
        } catch (e) {
          const msg = e.message || String(e);
          toast('执行失败(已回滚): ' + msg);
          if (reportEl) {
            reportEl.innerHTML += `<div style="margin-top:8px;color:#DC2626">回滚：${esc(msg)}</div>`;
          }
        }
      };
    }
  }

  function wireActions(root) {
    root.querySelectorAll('[data-act]').forEach((btn) => {
      btn.onclick = async () => {
        const act = btn.getAttribute('data-act');
        if (act === 'edit-style') {
          seg = 'persona'; setSegActive(); await renderPersona(root); return;
        }
        if (act === 'open-detail') {
          location.href = `/agent-team-config.html?team_id=${encodeURIComponent(teamId)}&agent_id=${encodeURIComponent(agentId)}&atab=ag-memory`;
          return;
        }
        if (act === 'destroy') {
          if (!confirm('销毁将删除记忆并写入墓碑，不可静默恢复。确认？')) return;
        }
        try {
          const base = `${CFG}/teams/${encodeURIComponent(teamId)}/agents/${encodeURIComponent(agentId)}/memory-core`;
          if (act === 'bind') {
            await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/lifecycle`, {
              method: 'POST',
              body: JSON.stringify({ action: 'bind' }),
            });
          } else if (act === 'consolidate') {
            const r = await api(`${base}/consolidate`, { method: 'POST', body: JSON.stringify({ max_new: 5 }) });
            toast(`巩固 ${(r && r.consolidated) || 0} 条→语义`);
          } else if (act === 'forget') {
            const r = await api(`${base}/forget`, { method: 'POST', body: JSON.stringify({}) });
            toast(`遗忘 ${(r && r.forgotten) || 0} 条`);
          } else if (act === 'drift') {
            const r = await api(`${base}/drift`, {
              method: 'POST',
              body: JSON.stringify({ fitness_delta: 0.2, force: true }),
            });
            toast('拓扑已漂移');
            console.info('topology', r && r.topology);
          } else {
            await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/lifecycle`, {
              method: 'POST',
              body: JSON.stringify({ action: act }),
            });
            toast('已执行 ' + act);
          }
          await loadOverview();
          await renderMain();
        } catch (e) {
          toast('失败: ' + (e.message || e));
        }
      };
    });
  }

  async function refresh() {
    await loadOverview();
  }

  window.__memRefresh = refresh;

  document.querySelectorAll('.mem-seg').forEach((b) => {
    b.onclick = () => {
      seg = b.getAttribute('data-seg');
      setSegActive();
      renderMain();
    };
  });

  async function checkAuthHint() {
    const hint = document.getElementById('auth-hint');
    if (!hint) return;
    try {
      const me = await api('/api/v1/auth/me');
      if (me && me.authenticated) {
        hint.style.display = 'none';
        return;
      }
    } catch (_) {}
    // 未登录：只读仍可用；写操作会提示登录
    hint.style.display = 'block';
    hint.innerHTML =
      '当前为访客只读。绑定/封存/共享/传递等写操作需 <a href="/login.html" style="color:#1F6B4A;font-weight:600">登录</a>。';
  }

  (async function init() {
    // URL 深链：?team_id=&agent_id=&seg=lifecycle|share|transfer|persona|agents
    let qTeam = '', qAgent = '', qSeg = '';
    try {
      const qp = new URLSearchParams(window.location.search || '');
      qTeam = qp.get('team_id') || qp.get('team') || '';
      qAgent = qp.get('agent_id') || qp.get('aid') || '';
      qSeg = qp.get('seg') || qp.get('tab') || '';
    } catch (_) {}

    await checkAuthHint();
    await loadTeams();
    if (qTeam) {
      const sel = document.getElementById('team-select');
      if (sel) {
        const opts = [...sel.options].map((o) => o.value);
        if (opts.includes(qTeam)) {
          teamId = qTeam;
          sel.value = qTeam;
        }
      }
    }
    await refresh();
    if (qAgent) {
      agentId = qAgent;
      renderAgentList();
    }
    if (qSeg && ['overview', 'agents', 'lifecycle', 'persona', 'share', 'transfer'].includes(qSeg)) {
      seg = qSeg;
      if (qAgent && qSeg === 'overview') seg = 'agents';
      setSegActive();
    }
    await renderMain();
  })();
})();
