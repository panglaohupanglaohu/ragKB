# -*- coding: utf-8 -*-
from pathlib import Path
R=Path('/Users/panglaohu/Downloads/AgentsGroup2026')
html=R/'src/frontend/agent-memory.html';js=R/'src/frontend/js/agent-memory-page.js'
def rep(p,a,b):
 t=p.read_text(encoding='utf-8')
 if a not in t: raise RuntimeError(f'missing {p}: {a[:70]}')
 p.write_text(t.replace(a,b,1),encoding='utf-8')

rep(html,
'''        每个智能体拥有四层记忆（运行日志 · 感知流 · 未发送队列 · 情绪残留）。
        生命周期：绑定 → 活体 → 共享/封存 → 传递 → 销毁。
        <b>小满</b>偏日常自主连续记忆；<b>沈弥安</b>偏深层固化与克制检索。''',
'''        记忆不是静态仓库，而是随时间变化的有机体：感觉痕迹被注意选择，情节被重构，
        自传语义从经历中巩固；工作台和前瞻意图负责现在与未来，但不是保存层；情绪选择场调制巩固、检索和遗忘。
        每个 Agent 都会形成自己的记忆方式，并在任务成败、物竞存活与传递中继续变化。''')
rep(html,'data-seg="persona">自主策略','data-seg="persona">记忆方式')

# Introduce style helpers and remove visible persona labels.
rep(js,
'''  function personaLabel(p) {
    return { xiaoman: '小满', shenmian: '沈弥安', hybrid: '混合' }[p] || p || '混合';
  }''',
'''  function memoryStyleName(a) {
    const s = (a && a.memory_style) || {};
    return s.name || `${(a && (a.name || a.agent_id)) || 'Agent'}的记忆方式`;
  }

  function pct(v) {
    const n = Number(v);
    return Number.isFinite(n) ? `${Math.round(n * 100)}%` : '—';
  }''')
rep(js,
'''          <div class="meta">${stateChip(a.state)} ${esc(personaLabel(a.persona))}
            · 日志 ${(a.counts && a.counts.log) || 0}''',
'''          <div class="meta">${stateChip(a.state)} ${esc(memoryStyleName(a))}
            · 情节 ${(a.counts && a.counts.log) || 0}''')
# Overview removes xiaoman/shenmian counts.
rep(js,
'''      const byP = (overview && overview.by_persona) || {};
      const health = overview && overview.health_avg != null ? overview.health_avg : '—';''',
'''      const health = overview && overview.health_avg != null ? overview.health_avg : '—';''')
rep(js,
'''        <div class="stat-row">
          <div class="stat"><b>${byP.xiaoman || 0}</b><span>小满</span></div>
          <div class="stat"><b>${byP.shenmian || 0}</b><span>沈弥安</span></div>
          <div class="stat"><b>${byP.hybrid || 0}</b><span>混合</span></div>
        </div>''','''        <div class="audit-line" style="margin-bottom:12px">
          团队中的记忆方式不再按模板分组；每个 Agent 拥有自己的连续性、克制性、可塑性与情绪通透度。
        </div>''')
rep(js,
'''          共享矩阵可预览授权；传递台执行复制交接。配置页「记忆绑定」写拟生痕迹/电荷/前瞻过程。''',
'''          共享矩阵只共享有来源的痕迹；传递台复制自传连续性。程序性记忆由技能与熟练度承载，不伪装成文本记忆层。''')
# Detail title uses memory style.
rep(js,
'''          <div style="margin-top:6px">${stateChip(st.state)} 
            <span class="chip">${esc(personaLabel(st.persona))}</span>
          </div>''',
'''          <div style="margin-top:6px">${stateChip(st.state)}
            <span class="chip">${esc(memoryStyleName(data))}</span>
          </div>''')
rep(js,'<div class="stat"><b>${c.intentions_pending || 0}</b><span>前瞻意图</span></div>',
'''<div class="stat"><b>${c.intentions_pending || 0}</b><span>前瞻意图·过程</span></div>''')
rep(js,'<div class="stat"><b>${c.affect_labels || 0}</b><span>情绪电荷</span></div>',
'''<div class="stat"><b>${c.affect_labels || 0}</b><span>情绪选择场</span></div>''')
# Add dynamic state card before system blocks.
rep(js,
'''      <p style="font-size:12px;color:#6B7280">💬 ${esc(data.tone_hint || '—')}</p>
      ${renderSystemsBlocks(data)}''',
'''      <p style="font-size:12px;color:#6B7280">💬 ${esc(data.tone_hint || '—')}</p>
      ${renderDynamicState(data)}
      ${renderSystemsBlocks(data)}''')
# Insert renderDynamicState before renderSystemsBlocks.
rep(js,
'''  function renderSystemsBlocks(data) {''',
'''  function renderDynamicState(data) {
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

  function renderSystemsBlocks(data) {''')
# Rename system section and labels.
rep(js,"<h3 style=\"font-size:13px;margin:14px 0 8px\">拟生分区</h3>",
'''<h3 style="font-size:13px;margin:14px 0 8px">动态记忆系统：痕迹 / 过程 / 选择场</h3>''')
rep(js,"['layer', '层 · 痕迹'],", "['layer', '保存的痕迹'],")
rep(js,"['field', '场 · 电荷'],", "['field', '选择场 · 不存事实'],")
rep(js,"['process', '过程 · 非层'],", "['process', '过程 · 不作为记忆层'],")
# lifecycle no persona.
rep(js,
'''      <p>当前状态 ${stateChip(st.state)} · Persona ${esc(personaLabel(st.persona))}</p>''',
'''      <p>当前状态 ${stateChip(st.state)} · 记忆方式会随时间和适应度缓慢变化</p>''')
# Replace entire renderPersona function up to renderShare.
start=js.read_text(encoding='utf-8')
a=start.index('  async function renderPersona(main) {')
b=start.index('  async function renderShare(main) {',a)
new_fn='''  async function renderPersona(main) {
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

'''
js.write_text(start[:a]+new_fn+start[b:],encoding='utf-8')
# edit style action redirects segment.
t=js.read_text(encoding='utf-8')
t=t.replace("        if (act === 'open-detail') {", "        if (act === 'edit-style') {\n          seg = 'persona'; setSegActive(); await renderPersona(root); return;\n        }\n        if (act === 'open-detail') {")
# user-facing transfer narrative shouldn't name prototype style.
t=t.replace("<h3 style=\"font-size:13px;margin:12px 0 6px\">交接叙事 · ${esc(\n              lastNav.style || ''\n            )}</h3>", "<h3 style=\"font-size:13px;margin:12px 0 6px\">交接叙事</h3>")
js.write_text(t,encoding='utf-8')
print('patched ui')
