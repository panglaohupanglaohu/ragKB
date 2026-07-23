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

  function personaLabel(p) {
    return { xiaoman: '小满', shenmian: '沈弥安', hybrid: '混合' }[p] || p || '混合';
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
          <div class="meta">${stateChip(a.state)} ${esc(personaLabel(a.persona))}
            · 日志 ${(a.counts && a.counts.log) || 0}
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
      const byP = (overview && overview.by_persona) || {};
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
        <div class="stat-row">
          <div class="stat"><b>${byP.xiaoman || 0}</b><span>小满</span></div>
          <div class="stat"><b>${byP.shenmian || 0}</b><span>沈弥安</span></div>
          <div class="stat"><b>${byP.hybrid || 0}</b><span>混合</span></div>
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
          共享矩阵可预览授权层；传递台执行复制交接。配置页「记忆绑定」可写四层细节。
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
    // agents — 四层摘要 + 快捷
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
            <span class="chip">${esc(personaLabel(st.persona))}</span>
          </div>
        </div>
        <div class="panel-actions" style="margin:0">
          <a class="btn" href="/agent-team-config.html?team_id=${encodeURIComponent(teamId)}&agent_id=${encodeURIComponent(agentId)}&atab=ag-memory">打开四层详情</a>
          <a class="btn" href="/agent-memory.html?team_id=${encodeURIComponent(teamId)}&agent_id=${encodeURIComponent(agentId)}&seg=share">共享</a>
          <a class="btn" href="/agent-memory.html?team_id=${encodeURIComponent(teamId)}&agent_id=${encodeURIComponent(agentId)}&seg=transfer">传递</a>
        </div>
      </div>
      <div class="stat-row" style="margin-top:14px">
        <div class="stat"><b>${c.log || 0}</b><span>运行日志</span></div>
        <div class="stat"><b>${c.perception || 0}</b><span>感知缓冲</span></div>
        <div class="stat"><b>${c.intentions_pending || 0}</b><span>待办意图</span></div>
        <div class="stat"><b>${c.affect_labels || 0}</b><span>情绪标签</span></div>
      </div>
      <p style="font-size:12px;color:#6B7280">💬 ${esc(data.tone_hint || '—')}</p>
      <div class="panel-actions">
        <button class="btn btn-primary" data-act="bind">绑定/激活</button>
        <button class="btn" data-act="save">保存固化</button>
        <button class="btn" data-act="seal">封存</button>
        <button class="btn" data-act="unseal">启封</button>
        <button class="btn btn-danger" data-act="destroy">销毁</button>
      </div>
      <h3 style="font-size:13px;margin:16px 0 8px">最近日志</h3>
      <div>${(data.log || [])
        .slice(-8)
        .reverse()
        .map(
          (e) =>
            `<div class="audit-line"><b>${esc(e.action || '')}</b> ${esc((e.detail || '').slice(0, 80))}</div>`
        )
        .join('') || '<div class="empty">暂无</div>'}
      </div>`;
    wireActions(main);
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
      <p>当前状态 ${stateChip(st.state)} · Persona ${esc(personaLabel(st.persona))}</p>
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
    let st;
    try {
      st = await fetchStatus();
    } catch (e) {
      main.innerHTML = `<div class="empty">${esc(e.message || e)}</div>`;
      return;
    }
    const cur = st.persona || 'hybrid';
    const cards = [
      {
        id: 'xiaoman',
        title: '小满 · 活体连续',
        desc: '边做边记、感知易逝、情绪余温、意图常挂；对话注入语气与宽检索。适合日常自主。',
      },
      {
        id: 'shenmian',
        title: '沈弥安 · 深层沉静',
        desc: '择要长存、定时反思、克制共享情绪、封存与交接优先；检索要求更高重要度。',
      },
      {
        id: 'hybrid',
        title: '混合（默认）',
        desc: '小满写路径 + 沈弥安共享边界与 promote 门槛。',
      },
    ];
    main.innerHTML = `
      <h2 style="margin:0 0 12px;font-size:16px">自主策略 Persona</h2>
      ${cards
        .map(
          (c) => `
        <div class="persona-card ${c.id === cur ? 'active' : ''}" data-persona="${c.id}">
          <h4>${esc(c.title)} ${c.id === cur ? '<span class="chip ok">当前</span>' : ''}</h4>
          <p>${esc(c.desc)}</p>
        </div>`
        )
        .join('')}
      <div class="panel-actions">
        <button class="btn" data-act="open-detail">打开四层详情页</button>
      </div>`;
    main.querySelectorAll('.persona-card').forEach((card) => {
      card.onclick = async () => {
        const p = card.getAttribute('data-persona');
        try {
          await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/persona`, {
            method: 'PUT',
            body: JSON.stringify({ persona: p }),
          });
          toast('已切换 ' + personaLabel(p));
          await loadOverview();
          await renderPersona(main);
        } catch (e) {
          toast('失败: ' + (e.message || e));
        }
      };
    });
    wireActions(main);
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
        默认共享 <b>log / perception / intentions</b>，不含 <b>affect</b>。
        沈弥安 Persona 强制剥离情绪层。
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
        <label style="margin-left:6px"><input type="checkbox" class="share-layer" value="intentions" checked> intentions</label>
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
    main.innerHTML = '<div class="empty">加载传递台…</div>';
    let history = [];
    try {
      const r = await api(`${HUB}/transfers?team_id=${encodeURIComponent(teamId)}&limit=20`);
      history = r.transfers || [];
    } catch (_) {
      history = [];
    }
    const options = agents
      .map((a) => `<option value="${esc(a.agent_id)}">${esc(a.name || a.agent_id)}</option>`)
      .join('');
    main.innerHTML = `
      <h2 style="margin:0 0 8px;font-size:16px">传递台</h2>
      <p style="font-size:12px;color:#6B7280;line-height:1.5;margin:0 0 12px">
        传递 = <b>复制</b>到受益者；原件默认封存凭吊（「这是回放，不是本人」）。
        意图交接：auto 直接挂载 / ask_new_owner 待确认 / drop 放弃。
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
          <label style="font-size:11px;color:#6B7280">意图交接</label><br>
          <select class="fi" id="xfer-ho" style="width:100%">
            <option value="ask_new_owner">ask_new_owner 待新主人确认</option>
            <option value="auto">auto 自动承接</option>
            <option value="drop">drop 全部放弃</option>
          </select>
        </div>
        <div>
          <label style="font-size:11px;color:#6B7280">备注</label><br>
          <input class="fi" id="xfer-note" style="width:100%;box-sizing:border-box" placeholder="交接说明"/>
        </div>
      </div>
      <label style="font-size:12px;color:#4B5568;display:flex;align-items:center;gap:6px;margin-bottom:12px">
        <input type="checkbox" id="xfer-keep" checked> 保留原件凭吊 keep_memorial
      </label>
      <div class="panel-actions">
        <button type="button" class="btn btn-primary" id="xfer-run">执行传递</button>
      </div>
      <h3 style="font-size:13px;margin:18px 0 8px">历史记录</h3>
      <div>
        ${
          history.length
            ? history
                .map(
                  (t) => `<div class="audit-line">
            <b>${esc(t.from)}</b> → <b>${esc(t.to)}</b>
            · ${esc(t.handover_intentions)} · 日志${(t.copied && t.copied.log) || 0}
            ${t.keep_memorial ? '<span class="chip warn">凭吊</span>' : ''}
            <span style="color:#9AA3AF">${esc(t.transfer_id || '')}</span>
          </div>`
                )
                .join('')
            : '<div class="empty">暂无传递记录</div>'
        }
      </div>`;

    const run = document.getElementById('xfer-run');
    if (run) {
      run.onclick = async () => {
        const from = document.getElementById('xfer-from').value;
        const to = document.getElementById('xfer-to').value;
        if (!from || !to || from === to) {
          toast('请选择不同的源与受益者');
          return;
        }
        if (!confirm(`确认将 ${from} 的记忆传递给 ${to}？`)) return;
        try {
          const r = await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(from)}/transfer`, {
            method: 'POST',
            body: JSON.stringify({
              to,
              handover_intentions: document.getElementById('xfer-ho').value,
              keep_memorial: document.getElementById('xfer-keep').checked,
              note: document.getElementById('xfer-note').value || '',
            }),
          });
          toast('传递完成 ' + (r.transfer && r.transfer.transfer_id));
          await loadOverview();
          await renderTransfer(main);
        } catch (e) {
          toast('失败: ' + (e.message || e));
        }
      };
    }
  }

  function wireActions(root) {
    root.querySelectorAll('[data-act]').forEach((btn) => {
      btn.onclick = async () => {
        const act = btn.getAttribute('data-act');
        if (act === 'open-detail') {
          location.href = `/agent-team-config.html?team_id=${encodeURIComponent(teamId)}&agent_id=${encodeURIComponent(agentId)}&atab=ag-memory`;
          return;
        }
        if (act === 'destroy') {
          if (!confirm('销毁将删除四层记忆并写入墓碑，不可静默恢复。确认？')) return;
        }
        try {
          if (act === 'bind') {
            await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/lifecycle`, {
              method: 'POST',
              body: JSON.stringify({ action: 'bind' }),
            });
          } else {
            await api(`${HUB}/${encodeURIComponent(teamId)}/${encodeURIComponent(agentId)}/lifecycle`, {
              method: 'POST',
              body: JSON.stringify({ action: act }),
            });
          }
          toast('已执行 ' + act);
          await loadOverview();
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
