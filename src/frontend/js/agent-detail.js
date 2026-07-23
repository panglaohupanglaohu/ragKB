/**
 * AgentsGroup2026 — Agent Detail Views
 * Renders agent status, personality/soul, tools, skills,
 * relationships, workspace, chat, logs, and settings tabs.
 * Extracted from agent-team-config.js for modularity.
 * Depends on: utils.js, api.js, agent-team-config.js (parent scope)
 */
(function(){
'use strict';
const csrfFetch = window._agFetch || fetch;
const EMPLOYEE_API = '/api/v1/agent-employee';
async function listApi(path, limit = 200, offset = 0){
  if(window.api&&typeof window.api.list==='function'){
    const payload=await window.api.list(path,limit,offset);
    return Array.isArray(payload?.items)?payload.items:[];
  }
  const payload=await api(path);
  return Array.isArray(payload)?payload:Array.isArray(payload?.items)?payload.items:[];
}
function _isLikelyOpaqueId(v){
  return /^[a-f0-9]{8,}$/i.test(String(v||''));
}

async function _resolveSkillLabels(teamId, skills){
  const list = Array.isArray(skills) ? skills : [];
  if (!list.length) return [];
  const payload = await api(`${A}/teams/${teamId}/skills`).catch(function(){ return null; });
  const items = Array.isArray(payload) ? payload : (Array.isArray(payload?.items) ? payload.items : []);
  const map = {};
  items.forEach(function(s){
    const name = s && s.name ? String(s.name) : '';
    if (!name) return;
    if (s.skill_id) map[String(s.skill_id)] = name;
    if (s.slug) map[String(s.slug)] = name;
    map[name] = name;
  });
  return list.map(function(raw){
    const key = String(raw||'');
    return { raw: key, label: map[key] || key };
  });
}
async function loadAgent(id){
  if(id){aid=id;_chatSid=''}const d=await api(`${A}/teams/${tid}/agents/${aid}`);
  if(!d){el('agent-content').innerHTML='<p style="color:var(--dim);padding:40px">加载失败</p>';return}
  el('main-title').textContent=d.name||d.agent_id;el('main-badge').textContent=d.role||d.template_type||'';
  document.querySelectorAll('.sb-agent').forEach(e=>e.classList.toggle('active',e.onclick&&e.onclick.toString().includes(aid)));
  renderATab(d);
}
document.querySelectorAll('#agent-tabs .tab').forEach(t=>t.addEventListener('click',()=>{document.querySelectorAll('#agent-tabs .tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');atab=t.dataset.at;loadAgent()}));

function renderATab(d){
  const c=el('agent-content'),p=d.personality||{},m=d.metadata||{},cr=d.created_at?d.created_at.split('T')[0]:'?';
  if(atab==='ag-status'){
    // Fetch real metrics + tasks for evidence
    Promise.all([
      api(`${A}/teams/${tid}/agents/${aid}/metrics`),
      api(`${A}/teams/${tid}/agents/${aid}/activity`),
      api(`${A}/teams/${tid}/tasks?limit=5&offset=0`),
      api(`${A}/teams/${tid}/agents/${aid}/logs?limit=5`),
    ]).then(([mt,act,tasks,lg])=>{
      mt=mt||{};act=act||{};
      const taskItems = tasks?.items || tasks || [];
      const logs = (lg?.logs || []).slice(-3).reverse();
      const recentTasksHtml = taskItems.length
        ? taskItems.slice(0,5).map(t => `<div class="focus-item" style="padding:8px 12px"><div class="title" style="font-size:12px"><span class="chip" style="font-size:9px;background:${t.status==='completed'?'rgba(38,162,105,0.1)':t.status==='failed'?'rgba(224,27,36,0.1)':'rgba(128,128,128,0.1)'};color:${t.status==='completed'?'var(--lime)':t.status==='failed'?'var(--red)':'var(--muted)'}">${escapeHtml(t.status||'pending')}</span> ${escapeHtml((t.title||t.task_id||'').slice(0,60))}</div><div class="meta">${t.created_at?t.created_at.slice(0,16):''}</div></div>`).join('')
        : '<p style="color:var(--dim);font-size:12px">暂无任务</p>';
      const evidenceHtml = logs.length
        ? logs.map(l => `<div class="focus-item" style="padding:6px 12px"><span class="chip" style="font-size:9px">${escapeHtml(l.action||'log')}</span> <span style="font-size:11px;color:var(--muted)">${escapeHtml((l.detail||'').slice(0,80))}</span></div>`).join('')
        : '<p style="color:var(--dim);font-size:12px">暂无执行记录 — 运行 Agent Loop 后显示</p>';

      // XF-2.4 物竞协作基因（metadata.eco_collab）只读
      const eco=m.eco_collab&&typeof m.eco_collab==='object'?m.eco_collab:null;
      const dimBar=(lab,v)=>{
        const n=Math.max(0,Math.min(1,Number(v!=null?v:0.5)));
        const pct=Math.round(n*100);
        return `<div class="detail-row" style="align-items:center"><span class="lbl">${lab}</span>`
          +`<span class="val" style="display:flex;align-items:center;gap:8px;flex:1;min-width:0">`
          +`<span style="flex:1;height:6px;background:var(--panel2);border-radius:3px;overflow:hidden;max-width:120px">`
          +`<span style="display:block;height:100%;width:${pct}%;background:var(--cyan)"></span></span>`
          +`<span style="font-size:12px;min-width:36px">${pct}%</span></span></div>`;
      };
      const ecoCard=eco
        ?`<div class="card" style="margin-top:16px;border-color:rgba(34,211,238,.35)"><div class="section-title">🧬 物竞协作基因 <span class="chip" style="font-size:10px;background:rgba(34,211,238,.12);color:var(--cyan)">eco_collab · 只读</span></div>`
          +`<p style="color:var(--dim);font-size:12px;margin:0 0 10px">仿真表型参数（非团队页关系/通道拓扑）。来源 ${escapeHtml(eco.source||'—')} · 策略 ${escapeHtml(eco.strategy||'—')}${eco.eco_fp?` · fp <code style="font-size:10px">${escapeHtml(String(eco.eco_fp).slice(0,12))}</code>`:''}</p>`
          +dimBar('share',eco.share_tendency)+dimBar('signal',eco.signal_tendency)
          +dimBar('follow',eco.follow_tendency)+dimBar('mate',eco.mate_choosiness)
          +(eco.survival_ticks!=null?`<div class="detail-row"><span class="lbl">存活 T</span><span class="val">${eco.survival_ticks}</span></div>`:'')
          +`<p style="color:var(--dim);font-size:11px;margin:10px 0 0">改拓扑请回 <a href="/Agent-digital-twin.html?office3d=1&team_id=${encodeURIComponent(tid||'')}" style="color:var(--cyan)">物竞 ③ 反馈台</a> 写回关系/通道</p></div>`
        :`<div class="card" style="margin-top:16px"><div class="section-title">🧬 物竞协作基因</div><p style="color:var(--dim);font-size:13px;margin:0">尚未写回 metadata.eco_collab — 在物竞试验田 ③ 勾选「写回协作基因」后此处可见四维倾向</p></div>`;

      c.innerHTML=`<div style="display:flex;gap:8px;margin-bottom:12px"><button class="btn btn-pink btn-sm" onclick="switchView('runtime')">▶ 运行 Agent Loop</button><button class="btn btn-sm" onclick="switchView('tasks')">📋 任务队列</button><button class="btn btn-sm" onclick="atab='ag-chat';loadAgent()">💬 对话</button></div>
<div class="card-grid"><div class="stat-card"><div class="label">📋 状态</div><div class="value" style="font-size:16px"><span class="st st-${d.state||'idle'}">● ${stL(d.state)}</span></div><div class="sub"><button class="btn btn-sm" style="margin-top:6px;padding:3px 10px;font-size:11px" onclick="startStop('${escapeHtml(d.state)}')">${d.state==='working'?'⏹ 停止':'▶ 启动'}</button></div></div><div class="stat-card"><div class="label">📊 今日 Token</div><div class="value">${(mt.today_tokens||0).toLocaleString()}</div></div><div class="stat-card"><div class="label">📈 本月 Token</div><div class="value">${((mt.month_tokens||0)/1000).toFixed(1)}K</div></div><div class="stat-card"><div class="label">🤖 今日 LLM 调用</div><div class="value">${mt.today_llm_calls||0}</div><div class="sub">消息: ${mt.messages_sent||0}</div></div><div class="stat-card"><div class="label">✅ 任务完成</div><div class="value">${mt.tasks_completed||0}</div><div class="sub" style="color:${(mt.tasks_failed||0)>0?'var(--pink)':'var(--muted)'}">成功率: ${mt.success_rate?Math.round(mt.success_rate*100)+'%':'N/A'}</div></div><div class="stat-card"><div class="label">🎯 能力评分</div><div class="value" style="color:${(mt.capability_score||0)>=60?'var(--lime)':(mt.capability_score||0)>=30?'var(--amber)':'var(--red)'}">${mt.capability_score||'?'}</div><div class="sub">/100</div></div><div class="stat-card"><div class="label">🔧 工具调用</div><div class="value">${mt.tools_invoked||0}</div></div><div class="stat-card"><div class="label">⚡ 技能数</div><div class="value">${(d.skills||[]).length}</div></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div class="card"><div class="section-title">📁 Agent 档案</div><div class="detail-row"><span class="lbl">👤 角色</span><span class="val">${escapeHtml(d.role||d.description||'-')}</span></div><div class="detail-row"><span class="lbl">📅 创建时间</span><span class="val">${cr}</span></div><div class="detail-row"><span class="lbl">🔴 最后活跃</span><span class="val">${mt.last_active?mt.last_active.split('T')[0]:'从未'}</span></div><div class="detail-row"><span class="lbl">💬 会话数</span><span class="val">${mt.sessions_created||0}</span></div></div><div class="card"><div class="section-title">🧠 模型配置</div><div class="detail-row"><span class="lbl">🟠 模型</span><span class="val">${escapeHtml(d.model_id||'未配置')}</span></div><div class="detail-row"><span class="lbl">📁 模板</span><span class="val">${escapeHtml(d.template_type||'-')}</span></div><div class="detail-row"><span class="lbl">🔧 工具数</span><span class="val">${(d.tools||[]).length}</span></div><div class="detail-row"><span class="lbl">📡 通道数</span><span class="val">${(d.channels||[]).length}</span></div></div></div>
${ecoCard}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px"><div class="card"><div class="section-title">📋 最近任务</div>${recentTasksHtml}</div><div class="card"><div class="section-title">📡 执行证据</div>${evidenceHtml}</div></div>
<div class="section" style="margin-top:20px"><div class="section-title">📊 近期活动</div>${act.recent_logs&&act.recent_logs.length?act.recent_logs.slice(-8).reverse().map(l=>`<div class="focus-item" style="padding:10px 14px"><div class="title" style="font-size:13px"><span class="chip" style="font-size:10px">${escapeHtml(l.action)}</span> ${escapeHtml(l.detail||'')}</div><div class="meta">${l.timestamp?l.timestamp.replace('T',' ').slice(0,19):''}</div></div>`).join(''):'<p style="color:var(--dim);font-size:13px">暂无活动记录 — 发送消息或启动 Agent 后将显示</p>'}</div>`;
    });
  } else if(atab==='ag-employee'){
    renderEmployeeView(d);
  } else if(atab==='ag-aware'){
    const tr=m.traits||[],bd=m.behavior_boundaries||[];
    c.innerHTML='<div class="section"><div class="section-title">关注点</div><p style="color:var(--dim);font-size:12px">加载中...</p></div>';
    _resolveSkillLabels(tid, d.skills||[]).then(function(resolved){
      c.innerHTML=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">关注点</div><span style="color:var(--dim);font-size:12px">${resolved.length+tr.length} active</span></div><p style="color:var(--muted);font-size:12px;margin-bottom:14px">技能、性格特质与行为边界</p>${resolved.map(s=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--pink)"></span>${escapeHtml(s.label)}${_isLikelyOpaqueId(s.raw)&&s.label===s.raw?` <span style="font-size:11px;color:var(--dim)">(${escapeHtml(s.raw.slice(0,8))})</span>`:''}</div><div class="meta">skill · active</div></div>`).join('')}${tr.map(t=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--amber)"></span>${escapeHtml(t)}</div><div class="meta">trait · personality</div></div>`).join('')}${bd.map(b=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--dim)"></span>${escapeHtml(b)}</div><div class="meta">boundary · constraint</div></div>`).join('')}${!resolved.length&&!tr.length&&!bd.length?'<p style="color:var(--dim)">暂无关注项</p>':''}</div>`;
    }).catch(function(){
      c.innerHTML=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">关注点</div><span style="color:var(--dim);font-size:12px">${(d.skills||[]).length+tr.length} active</span></div><p style="color:var(--muted);font-size:12px;margin-bottom:14px">技能、性格特质与行为边界</p>${(d.skills||[]).map(s=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--pink)"></span>${escapeHtml(s)}</div><div class="meta">skill · active</div></div>`).join('')}${tr.map(t=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--amber)"></span>${escapeHtml(t)}</div><div class="meta">trait · personality</div></div>`).join('')}${bd.map(b=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--dim)"></span>${escapeHtml(b)}</div><div class="meta">boundary · constraint</div></div>`).join('')}${!(d.skills||[]).length&&!tr.length&&!bd.length?'<p style="color:var(--dim)">暂无关注项</p>':''}</div>`;
    });
  } else if(atab==='ag-soul'){
    const soul=`# Soul — ${d.name||d.agent_id}\n\n## Identity\n- **名称**: ${d.name||d.agent_id}\n- **角色**: ${escapeHtml(d.role||d.description||'-')}\n- **创建时间**: ${cr}\n\n## Personality\n- ${p.tone||'professional'}\n- ${p.response_style||'concise'}\n- 创造力: ${p.creativity??0.5}\n- 语言: ${p.language||'zh-CN'}\n- 专长: ${(p.expertise_areas||[]).join(', ')||'无'}\n\n## Boundaries\n${(m.behavior_boundaries||[]).map(b=>'- '+b).join('\n')||'- 无限制'}`;
    // Load saved soul or generate default
    api(`${A}/teams/${tid}/agents/${aid}/soul`).then(sd=>{
      const savedSoul=(sd&&sd.content)?sd.content:soul;
      // Load memory files
      api(`${A}/teams/${tid}/agents/${aid}/memory`).then(mf=>{
        const files=mf||[];
        c.innerHTML=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div><div class="section-title" style="margin:0">🧬 Soul.md — 人格定义</div><p style="color:var(--muted);font-size:12px;margin-top:2px">核心身份、人格和行为边界</p></div><div><button class="btn btn-sm" id="soul-edit-btn" onclick="toggleSoulEdit()">编辑</button><button class="btn btn-pink btn-sm hidden" id="soul-save-btn" onclick="saveSoul()">保存</button></div></div><div class="soul-block" id="soul-view">${escapeHtml(savedSoul)}</div><textarea class="fi hidden" id="soul-editor" rows="16" style="font-family:'IBM Plex Mono',monospace;font-size:13px;line-height:1.7;min-height:300px">${savedSoul}</textarea></div><div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">🧠 记忆文件</div><button class="btn btn-sm" onclick="addMemoryFile()">＋ 新建</button></div><p style="color:var(--muted);font-size:12px;margin-bottom:12px">通过对话和经验积累的持久记忆</p><div id="memory-list">${files.length?files.map(f=>`<div class="memory-item" style="cursor:pointer" onclick="openMemoryFile('${escapeHtml(f.filename)}')"><span>📄 ${escapeHtml(f.filename)}</span><span style="display:flex;align-items:center;gap:8px"><span style="color:var(--dim);font-size:12px">${escapeHtml(f.size_display||f.size+' B')}</span><span style="cursor:pointer;color:var(--dim);font-size:14px" onclick="event.stopPropagation();delMemoryFile('${escapeHtml(f.filename)}')" title="删除">×</span></span></div>`).join(''):'<p style="color:var(--dim);font-size:13px">暂无记忆文件，点击「新建」开始积累</p>'}</div></div><div class="section hidden" id="mem-editor-section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><div class="section-title" style="margin:0" id="mem-editor-title">📝 编辑文件</div><div style="display:flex;gap:8px"><button class="btn btn-pink btn-sm" onclick="saveMemoryFile()">保存</button><button class="btn btn-sm" onclick="closeMemEditor()">关闭</button></div></div><textarea class="fi" id="mem-editor" rows="12" style="font-family:'IBM Plex Mono',monospace;font-size:13px;line-height:1.7"></textarea></div><div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">关注点</div><span style="color:var(--dim);font-size:12px">${(d.skills||[]).length+(m.traits||[]).length} active</span></div><p style="color:var(--muted);font-size:12px;margin-bottom:14px">技能、性格特质与行为边界</p>${(d.skills||[]).map(s=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--pink)"></span>${escapeHtml(s)}</div><div class="meta">skill · active</div></div>`).join('')}${(m.traits||[]).map(t=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--amber)"></span>${escapeHtml(t)}</div><div class="meta">trait · personality</div></div>`).join('')}${(m.behavior_boundaries||[]).map(b=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--dim)"></span>${escapeHtml(b)}</div><div class="meta">boundary · constraint</div></div>`).join('')}${!(d.skills||[]).length&&!(m.traits||[]).length&&!(m.behavior_boundaries||[]).length?'<p style="color:var(--dim)">暂无关注项</p>':''}</div>`;
      });
    });
  } else if(atab==='ag-memory'){
    c.innerHTML='<div class="section"><div class="section-title">🧠 记忆绑定</div><p style="color:var(--dim);font-size:12px">加载中…</p></div>';
    renderAgentMemoryBind(d);
  } else if(atab==='ag-tools'){
    listApi(`${A}/tools`,200,0).then(all=>{
      const bound=new Set(d.tools||[]);
      const cats={};(all||[]).forEach(t=>{const c=(t.category||'general').toUpperCase();if(!cats[c])cats[c]=[];cats[c].push(t)});
      let html=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">🔧 已绑定工具</div><span style="color:var(--dim);font-size:12px">${bound.size} / ${(all||[]).length} 已启用</span></div>`;
      Object.keys(cats).sort().forEach(cat=>{
        html+=`<div class="sb-section" style="margin-top:12px;margin-bottom:8px;font-size:11px;color:var(--dim);letter-spacing:1px">${cat}</div>`;
        cats[cat].forEach(t=>{const on=bound.has(t.tool_id)||bound.has(t.name);
          html+=`<div class="ws-item" style="padding:10px 14px"><span class="fname" style="gap:10px"><span style="font-size:18px">${t.icon||'🔧'}</span> <b>${t.name}</b> <span style="color:var(--dim);font-size:11px">${t.category||''}</span></span><span style="display:flex;align-items:center;gap:8px"><span style="color:var(--dim);font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(t.description||"")}</span><button class="btn btn-sm btn-ghost" onclick="testToolExec('${t.name}')" title="测试执行">▶</button><button class="btn btn-sm btn-ghost" onclick="openEditTool('${escapeHtml(t.tool_id)}')" title="编辑">✏️</button><button class="btn btn-sm btn-ghost" onclick="deleteTool('${escapeHtml(t.tool_id)}','${t.name}')" title="删除" style="color:var(--pink)">🗑️</button><button class="btn btn-sm${on?' btn-danger':''}" onclick="togAgentTool('${escapeHtml(t.tool_id)}',${!on})">${on?'解绑':'绑定'}</button></span></div>`})});
      html+=`</div>`;
      c.innerHTML=html;
    });
  } else if(atab==='ag-skills'){
    // 只显示当前智能体的技能，数据隔离
    const agentSkillIds = new Set(d.skills||[]);
    const isBoundSkill = (s) => agentSkillIds.has(s.skill_id) || agentSkillIds.has(s.name) || agentSkillIds.has(s.slug);
    Promise.all([
      listApi(`${A}/teams/${tid}/skills`,200,0),
      api(`${A}/skills`).catch(() => []),   // 全局内置技能库（可供绑定）
    ]).then(([all, registry]) => {
      const mySkills = all.filter(isBoundSkill);
      const teamAvail = all.filter(s => !isBoundSkill(s));
      // 智能体绑定了、但团队技能注册表里没有记录的技能（如内置核心技能），仍需展示，
      // 否则会出现「智能体明明有技能却显示为空」。用 id 兜底构造一个最小技能行。
      const coveredIds = new Set();
      mySkills.forEach(s => { [s.skill_id, s.name, s.slug].forEach(v => v && coveredIds.add(v)); });
      const orphanSkills = [...agentSkillIds].filter(id => !coveredIds.has(id)).map(id => ({
        skill_id: id,
        name: id,
        category: '内置',
        description: '该技能未登记在团队技能库（可能为内置/核心技能）',
      }));
      mySkills.push(...orphanSkills);
      // 全局内置技能库里、尚未绑定且团队列表中没有的技能，作为「可绑定」补充进来。
      // 内置技能在 agent.skills 中按 name 存储，故绑定标识用 name，保证解绑/识别一致。
      const teamCovered = new Set();
      all.forEach(s => { [s.skill_id, s.name, s.slug].forEach(v => v && teamCovered.add(v)); });
      const registryAvail = (Array.isArray(registry) ? registry : [])
        .filter(s => !isBoundSkill(s) && !teamCovered.has(s.skill_id) && !teamCovered.has(s.name))
        .map(s => ({ ...s, bind_id: s.name || s.skill_id, _from_registry: true }));
      const teamSkills = [...teamAvail, ...registryAvail];
      const renderSkillRow = (s, isBound, source) => {
        const bindId = s.bind_id || s.skill_id;
        const sid = String(s.skill_id || s.slug || s.name || '');
        const versionInfo = s.version ? ` v${s.version}` : '';
        const lifecycle = s.lifecycle_stage ? `<span class="chip" style="font-size:9px">${escapeHtml(s.lifecycle_stage)}</span>` : '';
        // type=button 防止误触 form submit 整页刷新；data-skill-id 供删除后就地移除
        return `<div class="ws-item" data-skill-row data-skill-id="${escapeHtml(sid)}" style="padding:10px 14px"><span class="fname" style="gap:10px"><span style="font-size:18px">${s.icon||'⚡'}</span> <b>${escapeHtml(s.name||'')}</b>${versionInfo} ${lifecycle}<span style="color:var(--dim);font-size:11px">${escapeHtml(s.category||'')}</span></span><span style="display:flex;align-items:center;gap:8px"><span style="color:var(--dim);font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(s.description||"")}</span><span style="font-size:9px;color:var(--muted)">${source}</span>${s.has_instructions?`<button type="button" class="btn btn-sm btn-ghost" onclick="viewSkillInstructions('${escapeHtml(s.skill_id)}')" title="查看指令">📖</button>`:''}<button type="button" class="btn btn-sm btn-ghost" onclick="openEditSkill('${escapeHtml(sid)}')" title="编辑">✏️</button><button type="button" class="btn btn-sm btn-ghost" data-skill-del="${escapeHtml(sid)}" onclick="event.preventDefault();event.stopPropagation();deleteSkillWithContext('${encodeURIComponent(sid)}','${encodeURIComponent(s.name||'')}','agent','${encodeURIComponent(aid||'')}')" title="删除" style="color:var(--pink)">🗑️</button>${isBound?`<button type="button" class="btn btn-sm btn-danger" onclick="event.preventDefault();togAgentSkill('${escapeHtml(bindId)}',false)">解绑</button>`:`<button type="button" class="btn btn-sm" onclick="event.preventDefault();togAgentSkill('${escapeHtml(bindId)}',true)">绑定</button>`}</span></div>`;
      };
      let html = `<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">⚡ 智能体技能</div><span style="color:var(--dim);font-size:12px">${mySkills.length} 个已绑定 · 可绑定 ${teamSkills.length} 个</span></div>`;
      html += `<div style="display:flex;gap:8px;margin-bottom:12px"><button class="btn btn-pink btn-sm" onclick="switchView('runtime')">▶ 运行 Agent Loop 测试</button><button class="btn btn-sm" onclick="switchView('tasks')">📋 查看任务</button></div>`;
      html += mySkills.length ? mySkills.map(s => renderSkillRow(s, true, `🫵 ${escapeHtml(d.name||d.agent_id)}`)).join('') : '<p style="color:var(--dim);padding:0 14px 12px">该智能体当前没有已绑定技能</p>';
      html += `<div class="sb-section" style="margin-top:16px;margin-bottom:8px;font-size:11px;color:var(--dim);letter-spacing:1px">可绑定技能 (${teamSkills.length})</div>`;
      html += teamSkills.length ? teamSkills.map(s => renderSkillRow(s, false, s._from_registry ? '🌐 技能库' : `📦 ${escapeHtml(tid)}`)).join('') : '<p style="color:var(--dim);padding:0 14px 4px">当前没有更多可绑定技能</p>';
      html += `</div>`;
      c.innerHTML = html;
    });
  } else if(atab==='ag-relations'){
    // 协作三层：门禁边(store) + 通讯录(api) + 通道 + eco_collab 摘要
    const AE='/api/v1/agent-employee';
    const eco=m.eco_collab&&typeof m.eco_collab==='object'?m.eco_collab:null;
    Promise.all([
      api(`${A}/teams/${tid}/agents/${aid}/relationships`).catch(()=>null),
      api(`${AE}/teams/${tid}/relationships?agent_id=${encodeURIComponent(aid)}`).catch(()=>null),
    ]).then(([rel,storeRel])=>{
      const edges=(storeRel&&storeRel.relationships)||[];
      const twinUrl=`/Agent-digital-twin.html?office3d=1&team_id=${encodeURIComponent(tid||'')}`;
      const edgeHtml=edges.length?edges.map(r=>{
        const other=r.source_agent_id===aid?r.target_id:r.source_agent_id;
        const dir=r.source_agent_id===aid?'→':'←';
        const ecoChip=(r.note&&String(r.note).includes('eco'))||(r.created_by&&String(r.created_by).includes('eco'));
        return `<div class="ws-item"><span class="fname">🔗 ${escapeHtml(dir)} ${escapeHtml(other||'?')}</span>`
          +`<span class="chip">${escapeHtml(r.rel_type||'collaborator')}</span>`
          +(ecoChip?'<span class="chip" style="background:rgba(34,211,238,.12);color:var(--cyan)">物竞</span>':'')
          +`</div>`;
      }).join(''):(
        `<div style="padding:12px;border:1px dashed var(--line);border-radius:0;margin-bottom:8px">`
        +`<p style="color:var(--dim);margin:0 0 8px;font-size:13px">暂无门禁关系边（RelationshipStore）</p>`
        +`<p style="color:var(--muted);font-size:12px;margin:0 0 10px">同队/共总线已是协作；点对点门禁需在物竞 ③ 确认写回或在此人工添加。</p>`
        +`<a class="btn btn-sm btn-pink" href="${twinUrl}" style="text-decoration:none">🧬 打开物竞 ③ 生成关系建议</a>`
        +`</div>`
      );
      const topoHtml=rel&&rel.relationships&&rel.relationships.length
        ?rel.relationships.map(r=>`<div class="ws-item"><span class="fname">👤 ${escapeHtml(r.name||r.target||'?')}</span>`
          +`<span class="chip">${escapeHtml(r.type||r.relationship||'peer')}</span>`
          +((r.layers||[]).length?`<span style="color:var(--dim);font-size:11px">${escapeHtml((r.layers||[]).join(', '))}</span>`:'')
          +`</div>`).join('')
        :'<p style="color:var(--dim)">暂无协作通讯录</p>';
      const ecoHtml=eco
        ?`<div class="section"><div class="section-title">🧬 协作基因 eco_collab（只读表型）</div>`
          +`<div class="ws-item">share ${Math.round((eco.share_tendency??0.5)*100)}% · signal ${Math.round((eco.signal_tendency??0.5)*100)}% · follow ${Math.round((eco.follow_tendency??0.5)*100)}% · mate ${Math.round((eco.mate_choosiness??0.5)*100)}%</div>`
          +`<p style="color:var(--dim);font-size:11px;margin:6px 0 0">基因≠拓扑；关系/通道才是真协作拓扑</p></div>`
        :'';
      c.innerHTML=`<div class="section"><div class="section-title">🔗 门禁关系边</div>${edgeHtml}</div>`
        +`<div class="section"><div class="section-title">🤝 协作通讯录（同队/通道/门禁）</div>${topoHtml}</div>`
        +`<div class="section"><div class="section-title">📡 通道绑定</div>${(d.channels||[]).length?(d.channels||[]).map(ch=>`<div class="ws-item"><span class="fname">📡 ${escapeHtml(ch.channel_name||ch.channel||'')}</span><span>${ch.subscribe?'<span class="chip">订阅</span>':''}${ch.publish?'<span class="chip">发布</span>':''}<span class="chip" style="background:rgba(255,207,112,0.1);color:var(--amber)">P${ch.priority??0}</span>${ch.source==='eco_drill'?'<span class="chip" style="background:rgba(34,211,238,.12);color:var(--cyan)">物竞</span>':''}</span></div>`).join(''):'<p style="color:var(--dim)">暂无通道</p>'}</div>`
        +ecoHtml;
    });
  } else if(atab==='ag-workspace'){
    var wsPath='';
    function renderWs(p){
      wsPath=p||'';
      api(`${A}/teams/${tid}/agents/${aid}/workspace?path=${encodeURIComponent(wsPath)}`).then(ws=>{
        if(ws.type==='file'){
          c.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">📄 ${escapeHtml(ws.name)}</div><div style="display:flex;gap:8px"><button class="btn btn-sm" onclick="renderWs('${wsPath.split('/').slice(0,-1).join('/')}')">← 返回</button><button class="btn btn-danger btn-sm" onclick="wsDelete('${wsPath}')">🗑 删除</button></div></div><textarea id="ws-edit" style="width:100%;min-height:300px;background:var(--card);color:var(--fg);border:1px solid var(--border);border-radius:0;padding:12px;font-family:monospace;font-size:13px;resize:vertical">${escapeHtml(ws.content||'')}</textarea><div style="margin-top:12px;display:flex;gap:8px"><button class="btn btn-pink" onclick="wsSave('${wsPath}')">💾 保存</button><button class="btn" onclick="wsIngestFile('${wsPath}')">📥 送入知识库</button></div>`;
          return;
        }
        var items=(ws.items||[]).map(it=>{
          var icon=it.type==='folder'?'📁':'📄';
          var newPath=wsPath?wsPath+'/'+it.name:it.name;
          return `<div class="ws-item" style="cursor:pointer" onclick="renderWs('${newPath}')"><span class="fname">${icon} ${escapeHtml(it.name)}</span><span style="color:var(--dim);font-size:12px">${it.size_display||''}</span></div>`;
        }).join('')||'<p style="color:var(--dim)">空文件夹</p>';
        var breadcrumb=wsPath?`<span style="cursor:pointer;color:var(--pink)" onclick="renderWs('')">workspace</span> / ${wsPath.split('/').map((p,i,a)=>`<span style="cursor:pointer;color:var(--pink)" onclick="renderWs('${a.slice(0,i+1).join('/')}')">${p}</span>`).join(' / ')}`:'workspace';
        c.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><div class="section-title" style="margin:0">📁 ${breadcrumb}</div><div style="display:flex;gap:8px"><button class="btn btn-sm" onclick="wsCreateFolder()">📁 新建文件夹</button><button class="btn btn-pink btn-sm" onclick="wsCreateFile()">＋ 新建文件</button><button class="btn btn-sm" onclick="wsIngestAll()">📥 全部送入知识库</button></div></div>${items}`;
      }).catch(()=>{
        c.innerHTML=`<p style="color:var(--dim)">加载工作区失败</p>`;
      });
    }
    window.wsSave=function(fp){
      var content=document.getElementById('ws-edit').value;
      csrfFetch(`${A}/teams/${tid}/agents/${aid}/workspace/${fp}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({content})}).then(r=>r.json()).then(()=>{toast('已保存');renderWs(fp)});
    };
    window.wsDelete=function(fp){
      if(!confirm('确认删除 '+fp+'?'))return;
      csrfFetch(`${A}/teams/${tid}/agents/${aid}/workspace/${fp}`,{method:'DELETE'}).then(r=>r.json()).then(()=>{toast('已删除');renderWs(fp.split('/').slice(0,-1).join('/'))});
    };
    window.wsCreateFolder=function(){
      var name=prompt('文件夹名称');if(!name)return;
      csrfFetch(`${A}/teams/${tid}/agents/${aid}/workspace?path=${encodeURIComponent(wsPath)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,type:'folder'})}).then(r=>r.json()).then(()=>{toast('已创建');renderWs(wsPath)});
    };
    window.wsCreateFile=function(){
      var name=prompt('文件名称 (例如 report.md)');if(!name)return;
      csrfFetch(`${A}/teams/${tid}/agents/${aid}/workspace?path=${encodeURIComponent(wsPath)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,type:'file',content:''})}).then(r=>r.json()).then(()=>{toast('已创建');renderWs(wsPath)});
    };
    window.wsIngestAll=function(){
      csrfFetch(`${A}/teams/${tid}/agents/${aid}/workspace/ingest-to-kb?path=${encodeURIComponent(wsPath)}`,{method:'POST'}).then(r=>r.json()).then(r=>{toast('已送入知识库: '+r.files+' 个文件')});
    };
    window.wsIngestFile=function(fp){
      csrfFetch(`${A}/teams/${tid}/agents/${aid}/workspace/ingest-to-kb?path=${encodeURIComponent(fp)}`,{method:'POST'}).then(r=>r.json()).then(r=>{toast('已送入知识库')});
    };
    renderWs('');
  } else if(atab==='ag-chat'){
    if(_chatSid){loadChatView(c);return}
    listApi(`${A}/teams/${tid}/agents/${aid}/sessions`,200,0).then(ss=>{c.innerHTML=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">💬 对话</div><button class="btn btn-pink btn-sm" onclick="newSession()">＋ 新建会话</button></div>${ss&&ss.length?ss.map(s=>`<div class="ws-item" style="cursor:pointer" onclick="openChatSession('${s.session_id||s.id}')"><span class="fname">💬 ${s.session_id||s.id}</span><span style="color:var(--dim);font-size:12px">${s.created_at||''}</span></div>`).join(''):'<p style="color:var(--dim)">暂无会话，点击上方按钮开始对话</p>'}</div>`});
  } else if(atab==='ag-logs'){
    api(`${A}/teams/${tid}/agents/${aid}/logs?limit=100`).then(lg=>{
      const logs=(lg&&lg.logs)||[];
      c.innerHTML=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">📋 工作日志</div><span style="color:var(--dim);font-size:12px">${logs.length} 条记录</span></div>${logs.length?logs.slice().reverse().map(l=>`<div class="focus-item" style="padding:10px 14px"><div class="title" style="font-size:13px"><span class="chip" style="font-size:10px">${l.action||'log'}</span> ${escapeHtml(l.detail||'')}</div><div class="meta">${l.timestamp?l.timestamp.replace('T',' ').slice(0,19):''}</div></div>`).join(''):'<p style="color:var(--dim)">暂无日志 — 与 Agent 交互后日志将自动生成</p>'}</div>`});
  } else if(atab==='ag-settings'){
    c.innerHTML=`<div class="card" style="max-width:600px"><div class="section-title">⚙️ 设置</div><div class="form-group"><label class="form-label">名称</label><input class="fi" value="${d.name||''}" id="set-name"></div><div class="form-group"><label class="form-label">角色</label><input class="fi" value="${d.role||''}" id="set-role"></div><div class="form-group"><label class="form-label">描述</label><textarea class="fi" id="set-desc">${d.description||''}</textarea></div><div class="form-group"><label class="form-label">系统提示词</label><textarea class="fi" id="set-prompt" rows="4">${d.system_prompt||''}</textarea></div><div class="form-group"><label class="form-label">模型 ID</label><input class="fi" value="${escapeHtml(d.model_id||'')}" id="set-model"></div><div id="agent-test-result" class="hidden" style="margin-top:12px;padding:14px;border-radius:0;border:1px solid var(--line);font-size:13px"></div><div style="display:flex;gap:10px;margin-top:20px"><button class="btn btn-pink" onclick="saveAgent()">保存</button><button class="btn" onclick="testAgentLLM()">🧪 测试连接</button><button class="btn btn-danger" onclick="delAgent()">删除</button></div></div>`;
  }
}
async function newSession(){const r=await api(`${A}/teams/${tid}/agents/${aid}/sessions`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:`${aid||'agent'}-${new Date().toISOString().slice(0,16)}`})});if(r){toast('会话已创建');_chatSid=r.session_id||r.id;loadAgent()}else{toast('会话创建失败','error')}}
let _chatSid='';
function openChatSession(sid){_chatSid=sid;loadAgent()}
function closeChatSession(){_chatSid='';loadAgent()}
function loadChatView(c){
  const sid=_chatSid;
  api(`${A}/teams/${tid}/agents/${aid}/sessions/${sid}/messages`).then(resp=>{
    const msgs=resp&&resp.messages?resp.messages:resp||[];
    let html=`<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px"><button class="btn btn-sm" onclick="closeChatSession()">← 返回</button><div class="section-title" style="margin:0">💬 会话 ${sid.slice(0,8)}</div></div>`;
    html+=`<div id="chat-msgs" style="display:flex;flex-direction:column;gap:10px;margin-bottom:20px;min-height:200px">`;
    if(msgs&&msgs.length){msgs.forEach(m=>{const isU=m.role==='user';html+=`<div style="display:flex;${isU?'justify-content:flex-end':''}"><div style="max-width:80%;padding:12px 16px;border-radius:${isU?'12px 12px 4px 12px':'12px 12px 12px 4px'};background:${isU?'var(--chat-user)':'var(--chat-agent)'};border:1px solid ${isU?'var(--chat-user-border)':'var(--chat-agent-border)'};font-size:13px;line-height:1.7;color:var(--chat-text)"><div style="font-size:11px;color:${isU?'var(--pink)':'var(--cyan)'};margin-bottom:4px">${isU?'👤 你':'🤖 Agent'} · ${(m.timestamp||m.created_at||'').slice(11,19)}</div><div style="white-space:pre-wrap;color:var(--text)">${(m.content||'').replace(/</g,'&lt;')}</div></div></div>`})}else{html+=`<p style="color:var(--dim);text-align:center;padding:40px 0">开始对话吧 👋</p>`}
    html+=`</div>`;
    html+=`<div style="display:flex;gap:10px;position:sticky;bottom:0;background:linear-gradient(to top,var(--bg) 80%,transparent);padding:12px 0"><input class="fi" id="chat-input" placeholder="输入消息..." style="flex:1" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChatMsg()}"><button class="btn btn-pink" onclick="sendChatMsg()">发送</button></div>`;
    c.innerHTML=html;
    const ci=el('chat-input');if(ci)ci.focus();
    const cm=el('chat-msgs');if(cm)cm.scrollTop=cm.scrollHeight;
  }).catch(()=>{
    c.innerHTML=`<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px"><button class="btn btn-sm" onclick="closeChatSession()">← 返回</button><div class="section-title" style="margin:0">💬 会话 ${sid.slice(0,8)}</div></div><div style="display:flex;flex-direction:column;gap:10px;margin-bottom:20px;min-height:200px"><p style="color:var(--dim);text-align:center;padding:40px 0">开始对话吧 👋</p></div><div style="display:flex;gap:10px;position:sticky;bottom:0;background:linear-gradient(to top,var(--bg) 80%,transparent);padding:12px 0"><input class="fi" id="chat-input" placeholder="输入消息..." style="flex:1" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChatMsg()}"><button class="btn btn-pink" onclick="sendChatMsg()">发送</button></div>`;
    const ci=el('chat-input');if(ci)ci.focus();
  });
}
async function sendChatMsg(){const inp=el('chat-input');if(!inp)return;const msg=inp.value.trim();if(!msg)return;inp.value='';inp.disabled=true;
  // 乐观渲染:立即把用户消息 + "正在思考…"占位插入对话区,避免应答前"像没发出去"
  const cm=el('chat-msgs');
  if(cm){
    const ph=cm.querySelector('p');if(ph)ph.remove();
    const now=new Date().toTimeString().slice(0,8);
    cm.insertAdjacentHTML('beforeend',`<div style="display:flex;justify-content:flex-end"><div style="max-width:80%;padding:12px 16px;border-radius:12px 12px 4px 12px;background:var(--chat-user);border:1px solid var(--chat-user-border);font-size:13px;line-height:1.7;color:var(--chat-text)"><div style="font-size:11px;color:var(--pink);margin-bottom:4px">👤 你 · ${now}</div><div style="white-space:pre-wrap;color:var(--text)">${msg.replace(/</g,'&lt;')}</div></div></div>`);
    cm.insertAdjacentHTML('beforeend',`<div id="chat-thinking" style="display:flex"><div style="max-width:80%;padding:12px 16px;border-radius:12px 12px 12px 4px;background:var(--chat-agent);border:1px solid var(--chat-agent-border);font-size:13px;color:var(--dim)"><div style="font-size:11px;color:var(--cyan);margin-bottom:4px">🤖 Agent</div><span class="dim">正在思考…</span></div></div>`);
    cm.scrollTop=cm.scrollHeight;
  }
  const r=await api(`${A}/teams/${tid}/agents/${aid}/sessions/${_chatSid}/messages`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:'user',content:msg})}).catch(()=>null);
  inp.disabled=false;if(r){loadAgent();if(r.task_id){toast(`📋 任务已创建: ${r.task_id}`)}}else{const t=el('chat-thinking');if(t)t.remove();toast('发送失败');inp.value=msg}}
async function saveAgent(){const b={name:el('set-name').value.trim(),role:el('set-role').value.trim(),description:el('set-desc').value.trim(),system_prompt:el('set-prompt').value.trim(),model_id:el('set-model').value.trim()};const r=await api(`${A}/teams/${tid}/agents/${aid}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});if(r){toast('已保存');loadSbAgents();loadAgent()}else toast('失败')}
async function testAgentLLM(){
  const rc=document.getElementById('agent-test-result');
  if(!rc)return;
  rc.classList.remove('hidden');
  rc.innerHTML='<p style="color:var(--dim)">正在测试 Agent LLM 连接...</p>';
  try{
    const r=await api(`${A}/llm/test`,{method:'POST'});
    if(!r){rc.innerHTML='<p style="color:var(--pink)">请求失败，请检查后端</p>';return}
    if(r.success){
      rc.style.borderColor='var(--lime,oklch(0.52 0.04 160))';
      rc.innerHTML=`<div style="color:var(--lime,oklch(0.52 0.04 160));margin-bottom:6px">✅ 连接成功</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12px"><div><b>模型:</b> ${escapeHtml(r.model)}</div><div><b>提供商:</b> ${escapeHtml(r.provider)}</div><div><b>延迟:</b> ${r.latency_ms?r.latency_ms.toFixed(0):'?'}ms</div></div><div style="margin-top:8px;padding:10px;background:rgba(232,240,250,0.7);border-radius:6px;font-size:12px;color:var(--text)">${escapeHtml(r.response||'')}</div>`;
      // Auto-update model_id to the actual connected model
      const mi=document.getElementById('set-model');
      if(mi && r.model && mi.value!==r.model){
        mi.value=r.model;
        const b={name:el('set-name').value.trim(),role:el('set-role').value.trim(),description:el('set-desc').value.trim(),system_prompt:el('set-prompt').value.trim(),model_id:r.model};
        api(`${A}/teams/${tid}/agents/${aid}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(()=>{toast('模型已自动更新为 '+r.model);loadSbAgents()});
      }
    } else {
      rc.style.borderColor='var(--pink,oklch(0.48 0.07 22))';
      rc.innerHTML=`<div style="color:var(--pink,oklch(0.48 0.07 22));margin-bottom:6px">❌ 连接失败</div><div style="padding:10px;background:rgba(224,27,36,0.06);border-radius:6px;font-size:12px;word-break:break-all">${escapeHtml(r.error||'未知错误')}</div><div style="margin-top:8px;font-size:11px;color:var(--muted)">💡 请在「模型池」或「LLM 配置」中填入正确的 API Key</div>`;
    }
  }catch(e){rc.innerHTML=`<p style="color:var(--pink)">请求异常: ${escapeHtml(e.message)}</p>`}
}
async function delAgent(){
  if(!aid){toast('未选中智能体');return}
  // 复用列表删除（CSRF + 确认文案）
  if(typeof deleteAgentFromList==='function'){
    const nameEl=document.getElementById('set-name');
    await deleteAgentFromList(aid, nameEl?nameEl.value:aid);
    return;
  }
  if(!confirm('确定删除？'))return;
  await csrfFetch(`${A}/teams/${tid}/agents/${encodeURIComponent(aid)}`,{method:'DELETE'});
  toast('已删除');aid='';loadSbAgents();switchView('overview');
}
// 列表按钮若在 agent-detail 之后加载，仍挂到 window
if(typeof editAgentFromList==='function')window.editAgentFromList=editAgentFromList;
if(typeof deleteAgentFromList==='function')window.deleteAgentFromList=deleteAgentFromList;
async function startStop(cur){const act=cur==='working'?'stop':'start';const r=await api(`${A}/teams/${tid}/agents/${aid}/${act}`,{method:'POST'});if(r){toast(act==='start'?'Agent 已启动':'Agent 已停止');loadSbAgents();loadAgent()}else toast('操作失败')}

// ══════════════════════════════════
//  SOUL.MD & MEMORY FILES
// ══════════════════════════════════
let _memFn='';
function toggleSoulEdit(){const v=el('soul-view'),e=el('soul-editor'),eb=el('soul-edit-btn'),sb=el('soul-save-btn');if(e.classList.contains('hidden')){e.classList.remove('hidden');v.classList.add('hidden');eb.classList.add('hidden');sb.classList.remove('hidden');e.focus()}else{e.classList.add('hidden');v.classList.remove('hidden');eb.classList.remove('hidden');sb.classList.add('hidden')}}
async function saveSoul(){const c=el('soul-editor').value;const r=await api(`${A}/teams/${tid}/agents/${aid}/soul`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:c})});if(r){toast('Soul.md 已保存');el('soul-view').textContent=c;toggleSoulEdit()}else toast('保存失败')}
async function addMemoryFile(){const n=prompt('输入文件名 (例: learning_log.md):');if(!n||!n.trim())return;const fn=n.trim();const r=await api(`${A}/teams/${tid}/agents/${aid}/memory/${encodeURIComponent(fn)}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:`# ${fn}\n\n创建于 ${new Date().toISOString().split('T')[0]}\n`})});if(r){toast(`${fn} 已创建`);loadAgent()}else toast('创建失败')}
async function openMemoryFile(fn){_memFn=fn;const r=await api(`${A}/teams/${tid}/agents/${aid}/memory/${encodeURIComponent(fn)}`);if(!r){toast('无法打开');return}const sec=el('mem-editor-section');sec.classList.remove('hidden');el('mem-editor-title').textContent=`📝 ${fn}`;el('mem-editor').value=r.content||'';el('mem-editor').focus()}
async function saveMemoryFile(){if(!_memFn)return;const c=el('mem-editor').value;const r=await api(`${A}/teams/${tid}/agents/${aid}/memory/${encodeURIComponent(_memFn)}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:c})});if(r){toast(`${_memFn} 已保存`);loadAgent()}else toast('保存失败')}
function closeMemEditor(){el('mem-editor-section').classList.add('hidden');_memFn=''}
// Ensure overlay click also resets memory editor state
document.addEventListener('click',e=>{if(e.target.classList.contains('modal-overlay')&&_memFn){closeMemEditor()}})
async function delMemoryFile(fn){if(!confirm(`删除记忆文件 "${fn}"？`))return;await csrfFetch(`${A}/teams/${tid}/agents/${aid}/memory/${encodeURIComponent(fn)}`,{method:'DELETE'});toast(`${fn} 已删除`);loadAgent()}

// ══════════════════════════════════
//  DIGITAL EMPLOYEE PROFILE
// ══════════════════════════════════
let _employeeFileTab = 'soul';

function employeeFileLabel(kind){
  return {soul:'灵魂',focus:'聚焦',memory:'记忆',heartbeat:'心跳'}[kind] || kind;
}

function normalizeTeamAgents(team){
  if(!team || !team.agents)return [];
  return Array.isArray(team.agents) ? team.agents : Object.values(team.agents);
}

function normalizeTeamModels(team, current){
  const raw = team && team.models ? (Array.isArray(team.models) ? team.models : Object.values(team.models)) : [];
  const models = raw.map(m => m.model_id || m.id || m.name).filter(Boolean);
  if(current && !models.includes(current))models.unshift(current);
  return models;
}

function triggerSummary(t){
  const c=t.config||{};
  if(t.trigger_type==='cron')return c.expr || 'cron';
  if(t.trigger_type==='once')return c.fire_at || 'once';
  if(t.trigger_type==='interval')return `${c.every_minutes||'?'} 分钟`;
  if(t.trigger_type==='poll')return `${c.url||'poll'} · ${c.every_minutes||'?'} 分钟`;
  if(t.trigger_type==='on_message')return c.from_agent ? `from agent ${c.from_agent}` : `from user ${c.from_user||'*'}`;
  if(t.trigger_type==='webhook')return `${c.rate_limit_per_min||5}/min`;
  return '';
}

function renderEmployeeView(d){
  const c=el('agent-content');
  c.innerHTML='<div class="section"><div class="section-title">数字员工</div><p style="color:var(--dim);font-size:13px">加载数字员工档案...</p></div>';
  Promise.all([
    api(`${EMPLOYEE_API}/agents/${aid}/files/soul`),
    api(`${EMPLOYEE_API}/agents/${aid}/files/focus`),
    api(`${EMPLOYEE_API}/agents/${aid}/files/memory`),
    api(`${EMPLOYEE_API}/agents/${aid}/files/heartbeat`),
    api(`${EMPLOYEE_API}/agents/${aid}/focus-items`),
    api(`${EMPLOYEE_API}/teams/${tid}/agents/${aid}/triggers`),
    api(`${EMPLOYEE_API}/teams/${tid}/relationships?agent_id=${encodeURIComponent(aid)}`),
    api(`${EMPLOYEE_API}/teams/${tid}/agents/${aid}/governance`),
    api(`${A}/teams/${tid}`),
  ]).then(([soul,focus,memory,heartbeat,focusData,triggers,relationships,governance,team])=>{
    const files={soul:soul||{},focus:focus||{},memory:memory||{},heartbeat:heartbeat||{}};
    const focusItems=(focusData&&focusData.items)||[];
    const triggerItems=(triggers&&triggers.triggers)||[];
    const relItems=(relationships&&relationships.relationships)||[];
    const gateMode=(relationships&&relationships.gate_mode)||'soft';
    const teamAgents=normalizeTeamAgents(team).filter(a => (a.agent_id||a.id)!==aid);
    const models=normalizeTeamModels(team, governance&&governance.fallback_model_id);
    const currentLevel=(governance&&governance.autonomy_level)||2;
    const focusOptions=focusItems.length
      ? focusItems.map(i=>`<option value="${escapeHtml(i.text)}">${i.done?'✓':'□'} ${escapeHtml(i.text)}</option>`).join('')
      : '<option value="">先在聚焦文件中添加 checklist</option>';
    const triggerList=triggerItems.length?triggerItems.map(t=>`
      <div class="employee-row">
        <div>
          <div class="employee-row-title"><span class="chip">${escapeHtml(t.trigger_type)}</span> ${escapeHtml(t.focus_item||'事件触发')}</div>
          <div class="employee-row-meta">${escapeHtml(triggerSummary(t))} · 下次 ${escapeHtml(t.next_fire_at||'—')} · 已触发 ${t.fire_count||0}</div>
        </div>
        <div class="employee-row-actions">
          <button class="btn btn-sm" onclick="toggleEmployeeTrigger('${escapeHtml(t.trigger_id)}')">${t.enabled?'停用':'启用'}</button>
          <button class="btn btn-sm btn-ghost" style="color:var(--pink)" onclick="deleteEmployeeTrigger('${escapeHtml(t.trigger_id)}')">删除</button>
        </div>
      </div>`).join(''):'<p class="employee-empty">暂无 Trigger</p>';
    const relList=relItems.length?relItems.map(r=>`
      <div class="employee-row">
        <div>
          <div class="employee-row-title"><span class="chip">${r.kind==='agent_human'?'人类':'Agent'}</span> ${escapeHtml(r.source_agent_id)} → ${escapeHtml(r.target_id)}</div>
          <div class="employee-row-meta">${escapeHtml(r.rel_type)}${r.note?' · '+escapeHtml(r.note):''}</div>
        </div>
        <button class="btn btn-sm btn-ghost" style="color:var(--pink)" onclick="deleteEmployeeRelationship('${escapeHtml(r.rel_id)}')">删除</button>
      </div>`).join(''):'<p class="employee-empty">暂无显式关系</p>';
    const agentOptions=teamAgents.length
      ? teamAgents.map(a=>`<option value="${escapeHtml(a.agent_id||a.id)}">${escapeHtml(a.name||a.agent_id||a.id)}</option>`).join('')
      : '<option value="">无其他 Agent</option>';
    const modelOptions=['<option value="">不设置降级模型</option>'].concat(
      models.map(m=>`<option value="${escapeHtml(m)}" ${governance&&governance.fallback_model_id===m?'selected':''}>${escapeHtml(m)}</option>`)
    ).join('');
    c.innerHTML=`
      <div class="employee-header">
        <div>
          <div class="section-title" style="margin:0">数字员工档案</div>
          <p>四件套档案、Aware 唤醒、关系网络和治理参数集中管理</p>
        </div>
        <button class="btn btn-sm" onclick="previewEmployeeContext()">预览组织上下文</button>
      </div>

      <div class="section employee-section">
        <div class="employee-section-head"><div class="section-title">四件套</div></div>
        <div class="employee-file-tabs">
          ${['soul','focus','memory','heartbeat'].map(k=>`<button class="employee-file-tab ${_employeeFileTab===k?'active':''}" data-kind="${k}" onclick="switchEmployeeFileTab('${k}')">${employeeFileLabel(k)}</button>`).join('')}
        </div>
        ${['soul','focus','heartbeat'].map(k=>`
          <div class="employee-file-pane ${_employeeFileTab===k?'active':''}" id="employee-pane-${k}">
            <textarea class="fi employee-textarea" id="employee-${k}-editor">${escapeHtml(files[k].content||'')}</textarea>
            <div class="employee-actions">
              <span>${files[k].updated_at?`更新于 ${escapeHtml(files[k].updated_at.slice(0,19))}`:'默认模板'}</span>
              <button class="btn btn-pink btn-sm" onclick="saveEmployeeFile('${k}')">保存${employeeFileLabel(k)}</button>
              ${k==='heartbeat'?'<button class="btn btn-sm" onclick="resetEmployeeHeartbeat()">重置心跳模板</button>':''}
            </div>
          </div>`).join('')}
        <div class="employee-file-pane ${_employeeFileTab==='memory'?'active':''}" id="employee-pane-memory">
          <div class="employee-memory">${escapeHtml(files.memory.content||'')}</div>
          <textarea class="fi" id="employee-memory-entry" placeholder="追加一条经验、教训或发现"></textarea>
          <div class="employee-actions">
            <span>memory.md append-only</span>
            <button class="btn btn-pink btn-sm" onclick="appendEmployeeMemory()">追加记忆</button>
          </div>
        </div>
      </div>

      <div class="employee-two-col">
        <div class="section employee-section">
          <div class="employee-section-head"><div class="section-title">Aware Trigger</div><span>${triggerItems.length} 个</span></div>
          <div class="employee-form-grid">
            <label><span>类型</span><select class="fi" id="employee-trigger-type" onchange="updateEmployeeTriggerFields()"><option value="cron">cron</option><option value="once">once</option><option value="interval">interval</option><option value="poll">poll</option><option value="on_message">on_message</option><option value="webhook">webhook</option></select></label>
            <label><span>绑定聚焦项</span><select class="fi" id="employee-trigger-focus">${focusOptions}</select></label>
          </div>
          <div id="employee-trigger-fields"></div>
          <button class="btn btn-pink btn-sm" onclick="createEmployeeTrigger()">创建 Trigger</button>
          <div class="employee-list">${triggerList}</div>
        </div>

        <div class="section employee-section">
          <div class="employee-section-head"><div class="section-title">关系网络</div><span>${gateMode==='hard'?'硬门禁':'软门禁'}</span></div>
          <div class="employee-form-grid">
            <label><span>对象类型</span><select class="fi" id="employee-rel-kind" onchange="updateEmployeeRelationTarget()"><option value="agent_agent">Agent</option><option value="agent_human">Human</option></select></label>
            <label id="employee-rel-agent-wrap"><span>目标 Agent</span><select class="fi" id="employee-rel-target-agent">${agentOptions}</select></label>
            <label id="employee-rel-human-wrap" class="hidden"><span>Human ID</span><input class="fi" id="employee-rel-target-human" placeholder="user_xxx"></label>
            <label><span>关系</span><select class="fi" id="employee-rel-type"><option value="collaborator">collaborator</option><option value="supervisor">supervisor</option><option value="subordinate">subordinate</option><option value="reviewer">reviewer</option></select></label>
            <label><span>备注</span><input class="fi" id="employee-rel-note" placeholder="关系说明"></label>
          </div>
          <button class="btn btn-pink btn-sm" onclick="createEmployeeRelationship()">添加关系</button>
          <div class="employee-list">${relList}</div>
        </div>
      </div>

      <div class="section employee-section">
        <div class="employee-section-head"><div class="section-title">治理参数</div><span>${(governance&&governance.budget_status&&governance.budget_status.used_today)||0} / ${(governance&&governance.token_budget)||0} tokens</span></div>
        <input type="hidden" id="employee-autonomy-level" value="${currentLevel}">
        <div class="employee-levels">
          ${[1,2,3,4].map(l=>`<button class="employee-level ${currentLevel===l?'active':''}" onclick="setEmployeeAutonomy(${l})" title="${['只读建议','低危执行','高危需审批','全自主'][l-1]}">L${l}<span>${['建议','低危','审批','自主'][l-1]}</span></button>`).join('')}
        </div>
        <div class="employee-form-grid">
          <label><span>日 token 预算</span><input class="fi" id="employee-token-budget" type="number" min="0" value="${(governance&&governance.token_budget)||0}"></label>
          <label><span>降级模型</span><select class="fi" id="employee-fallback-model">${modelOptions}</select></label>
        </div>
        <button class="btn btn-pink btn-sm" onclick="saveEmployeeGovernance()">保存治理参数</button>
      </div>`;
    updateEmployeeTriggerFields();
    updateEmployeeRelationTarget();
  }).catch(e=>{
    c.innerHTML=`<div class="section"><div class="section-title">数字员工</div><p style="color:var(--pink)">加载失败: ${escapeHtml(e.message||e)}</p></div>`;
  });
}

function switchEmployeeFileTab(kind){
  _employeeFileTab=kind;
  document.querySelectorAll('.employee-file-tab').forEach(b=>b.classList.toggle('active',b.dataset.kind===kind));
  document.querySelectorAll('.employee-file-pane').forEach(p=>p.classList.toggle('active',p.id===`employee-pane-${kind}`));
}

async function saveEmployeeFile(kind){
  const editor=el(`employee-${kind}-editor`);
  if(!editor)return;
  const r=await api(`${EMPLOYEE_API}/agents/${aid}/files/${kind}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:editor.value})});
  if(r){toast(`${employeeFileLabel(kind)}已保存`,'success');loadAgent()}else toast('保存失败','error');
}

async function appendEmployeeMemory(){
  const input=el('employee-memory-entry');
  const entry=input&&input.value.trim();
  if(!entry){toast('请输入要追加的记忆','error');return}
  const r=await api(`${EMPLOYEE_API}/agents/${aid}/files/memory/append`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entry,source:'agent-team-config'})});
  if(r){toast('记忆已追加','success');_employeeFileTab='memory';loadAgent()}else toast('追加失败','error');
}

async function resetEmployeeHeartbeat(){
  const r=await api(`${EMPLOYEE_API}/agents/${aid}/files/heartbeat/reset`,{method:'POST'});
  if(r){toast('心跳模板已重置','success');_employeeFileTab='heartbeat';loadAgent()}else toast('重置失败','error');
}

function updateEmployeeTriggerFields(){
  const type=el('employee-trigger-type')?.value||'cron';
  const target=el('employee-trigger-fields');
  if(!target)return;
  const fields={
    cron:'<div class="employee-form-grid"><label><span>cron 表达式</span><input class="fi" id="employee-trigger-expr" value="0 9 * * 1-5"></label><label><span>时区偏移(分钟)</span><input class="fi" id="employee-trigger-tz" type="number" value="480"></label></div>',
    once:'<div class="employee-form-grid"><label><span>触发时间</span><input class="fi" id="employee-trigger-fire-at" type="datetime-local"></label></div>',
    interval:'<div class="employee-form-grid"><label><span>间隔(分钟)</span><input class="fi" id="employee-trigger-every" type="number" min="1" value="240"></label></div>',
    poll:'<div class="employee-form-grid"><label><span>URL</span><input class="fi" id="employee-trigger-url" placeholder="https://api.example.com/status"></label><label><span>间隔(分钟)</span><input class="fi" id="employee-trigger-every" type="number" min="1" value="30"></label><label><span>JSONPath</span><input class="fi" id="employee-trigger-jsonpath" placeholder="$.status"></label><label><span>期望值</span><input class="fi" id="employee-trigger-expect" placeholder="changed"></label></div>',
    on_message:'<div class="employee-form-grid"><label><span>from_agent</span><input class="fi" id="employee-trigger-from-agent" placeholder="agent_id"></label><label><span>from_user</span><input class="fi" id="employee-trigger-from-user" placeholder="user_id"></label></div>',
    webhook:'<div class="employee-form-grid"><label><span>secret_token</span><input class="fi" id="employee-trigger-secret" placeholder="留空由后端外部注入"></label><label><span>rate_limit/min</span><input class="fi" id="employee-trigger-rate" type="number" min="1" value="5"></label></div>',
  };
  target.innerHTML=fields[type]||'';
}

function employeeTriggerConfig(){
  const type=el('employee-trigger-type')?.value||'cron';
  if(type==='cron')return {expr:el('employee-trigger-expr')?.value||'',tz_offset_min:parseInt(el('employee-trigger-tz')?.value||'0',10)};
  if(type==='once')return {fire_at:el('employee-trigger-fire-at')?.value||''};
  if(type==='interval')return {every_minutes:parseInt(el('employee-trigger-every')?.value||'0',10)};
  if(type==='poll')return {url:el('employee-trigger-url')?.value||'',jsonpath:el('employee-trigger-jsonpath')?.value||'',expect:el('employee-trigger-expect')?.value||'',every_minutes:parseInt(el('employee-trigger-every')?.value||'0',10)};
  if(type==='on_message')return {from_agent:el('employee-trigger-from-agent')?.value||'',from_user:el('employee-trigger-from-user')?.value||''};
  if(type==='webhook')return {secret_token:el('employee-trigger-secret')?.value||'',rate_limit_per_min:parseInt(el('employee-trigger-rate')?.value||'5',10)};
  return {};
}

async function createEmployeeTrigger(){
  const payload={trigger_type:el('employee-trigger-type').value,enabled:true,focus_item:el('employee-trigger-focus')?.value||'',config:employeeTriggerConfig()};
  const r=await api(`${EMPLOYEE_API}/teams/${tid}/agents/${aid}/triggers`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(r){toast('Trigger 已创建','success');loadAgent()}else toast('Trigger 创建失败','error');
}

async function toggleEmployeeTrigger(triggerId){
  const r=await api(`${EMPLOYEE_API}/teams/${tid}/triggers/${triggerId}/toggle`,{method:'POST'});
  if(r){toast(r.enabled?'Trigger 已启用':'Trigger 已停用','success');loadAgent()}else toast('操作失败','error');
}

async function deleteEmployeeTrigger(triggerId){
  if(!confirm('删除这个 Trigger？'))return;
  const r=await api(`${EMPLOYEE_API}/teams/${tid}/triggers/${triggerId}`,{method:'DELETE'});
  if(r){toast('Trigger 已删除','success');loadAgent()}else toast('删除失败','error');
}

function updateEmployeeRelationTarget(){
  const isHuman=el('employee-rel-kind')?.value==='agent_human';
  el('employee-rel-agent-wrap')?.classList.toggle('hidden',isHuman);
  el('employee-rel-human-wrap')?.classList.toggle('hidden',!isHuman);
}

async function createEmployeeRelationship(){
  const kind=el('employee-rel-kind').value;
  const targetId=kind==='agent_human' ? el('employee-rel-target-human').value.trim() : el('employee-rel-target-agent').value;
  if(!targetId){toast('请选择或输入关系对象','error');return}
  const payload={kind,source_agent_id:aid,target_id:targetId,rel_type:el('employee-rel-type').value,note:el('employee-rel-note').value.trim(),created_by:'human'};
  const r=await api(`${EMPLOYEE_API}/teams/${tid}/relationships`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(r){toast('关系已添加','success');loadAgent()}else toast('关系添加失败','error');
}

async function deleteEmployeeRelationship(relId){
  if(!confirm('删除这条关系？'))return;
  const r=await api(`${EMPLOYEE_API}/teams/${tid}/relationships/${relId}`,{method:'DELETE'});
  if(r){toast('关系已删除','success');loadAgent()}else toast('删除失败','error');
}

function setEmployeeAutonomy(level){
  const input=el('employee-autonomy-level');
  if(input)input.value=String(level);
  document.querySelectorAll('.employee-level').forEach((b,i)=>b.classList.toggle('active',i+1===level));
}

async function saveEmployeeGovernance(){
  const payload={
    autonomy_level:parseInt(el('employee-autonomy-level')?.value||'2',10),
    token_budget:parseInt(el('employee-token-budget')?.value||'0',10),
    fallback_model_id:el('employee-fallback-model')?.value||'',
  };
  const r=await api(`${EMPLOYEE_API}/teams/${tid}/agents/${aid}/governance`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(r){toast('治理参数已保存','success');loadAgent()}else toast('治理参数保存失败','error');
}

async function previewEmployeeContext(){
  const r=await api(`${EMPLOYEE_API}/teams/${tid}/agents/${aid}/context`);
  if(!r){toast('组织上下文加载失败','error');return}
  const body=`<pre style="white-space:pre-wrap;word-break:break-word;font-size:12px;line-height:1.7;max-height:60vh;overflow:auto">${escapeHtml(r.system_prefix||'')}</pre>`;
  if(typeof showInfoModal==='function')showInfoModal('组织上下文预览',body);
  else alert(r.system_prefix||'');
}

// ══════════════════════════════════
//  AGENT TOOL / SKILL BIND
// ══════════════════════════════════
async function togAgentTool(toolId,bind){
  const d=await api(`${A}/teams/${tid}/agents/${aid}`);if(!d)return;
  let cur=new Set(d.tools||[]);if(bind)cur.add(toolId);else cur.delete(toolId);
  await api(`${A}/teams/${tid}/agents/${aid}/tools`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({tool_ids:[...cur]})});
  toast(bind?`已绑定 ${toolId}`:`已解绑 ${toolId}`);loadAgent();
}
async function togAgentSkill(skillId,bind){
  const d=await api(`${A}/teams/${tid}/agents/${aid}`);if(!d)return;
  let cur=new Set(d.skills||[]);if(bind)cur.add(skillId);else cur.delete(skillId);
  const action=bind?'绑定':'解绑';
  try {
    const resp = await csrfFetch(`${A}/teams/${tid}/agents/${encodeURIComponent(aid)}/skills`,{
      method:'PUT',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({skill_ids:[...cur]})
    });
    if (resp.ok) {
      // csrfFetch 绕过了 api() 的缓存清理，需手动清掉该 agent 的 GET 缓存，
      // 否则 loadAgent() 会命中 5s TTL 缓存返回旧的 skills 列表。
      var agentGetKey = 'GET:' + A + '/teams/' + tid + '/agents/' + aid;
      if (_reqCache[agentGetKey]) delete _reqCache[agentGetKey];
      toast(bind?`已绑定 ${skillId}`:`已解绑 ${skillId}`);
      loadAgent();
    } else {
      const body = await resp.json().catch(()=>({}));
      const detail = body.detail || body.message || '';
      toast(`${action}失败 HTTP ${resp.status}${detail ? ': ' + detail : ''}`, 'error');
    }
  } catch(e) {
    toast(`${action}失败: ` + e.message, 'error');
  }
}

// ── Enhanced Skill Delete (with context) ──
// 防连点 + 幂等：删后立刻从 DOM 去掉，不整页跳转/刷新
const _skillCtxDeleteInFlight = new Set();
function _removeSkillRowsFromDom(skillId) {
  const id = String(skillId || '');
  if (!id) return;
  document.querySelectorAll('[data-skill-row]').forEach(function (row) {
    if (row.getAttribute('data-skill-id') === id) row.remove();
  });
  document.querySelectorAll('[data-skill-del]').forEach(function (btn) {
    if (btn.getAttribute('data-skill-del') === id) {
      const row = btn.closest('.ws-item, [data-skill-row]');
      if (row) row.remove();
    }
  });
}
async function deleteSkillWithContext(skillId, skillName, sourceType, sourceId) {
  const rawSkillId = decodeURIComponent(String(skillId || ''));
  const rawSkillName = decodeURIComponent(String(skillName || ''));
  const rawSourceId = decodeURIComponent(String(sourceId || ''));
  if (!rawSkillId) { toast('缺少 skill_id'); return; }
  if (_skillCtxDeleteInFlight.has(rawSkillId)) { toast('正在删除，请稍候…'); return; }

  // 查找技能详情确定影响范围（失败也不挡删除）
  let skill = null;
  let boundAgents = [];
  try {
    const teamSkills = await listApi(`${A}/teams/${tid}/skills`, 200, 0);
    skill = teamSkills.find(s => s.skill_id === rawSkillId || s.name === rawSkillName || s.slug === rawSkillId) || null;
    if (skill) {
      const teamDetail = await api(`${A}/teams/${tid}`);
      if (teamDetail && teamDetail.agents) {
        const agents = Array.isArray(teamDetail.agents) ? teamDetail.agents : Object.values(teamDetail.agents);
        agents.forEach(a => {
          const aSkills = a.skills || [];
          if (aSkills.includes(rawSkillId) || aSkills.includes(skill.name) || aSkills.includes(skill.slug)) {
            boundAgents.push(a.name || a.agent_id);
          }
        });
      }
    }
  } catch (_) { /* ignore */ }

  const confirmed = confirm(
    `确认删除技能「${rawSkillName || rawSkillId}」？\n\n` +
    (skill ? `来源: ${sourceType}${rawSourceId ? ' ' + rawSourceId : ''} · 影响智能体: ${boundAgents.length} 个\n\n` : '') +
    '此操作不可撤销。'
  );
  if (!confirmed) return;

  _skillCtxDeleteInFlight.add(rawSkillId);
  // 先就地移除行，避免「删了还在 → 再点 404 / 以为要刷整页」
  _removeSkillRowsFromDom(rawSkillId);

  try {
    let body = null;
    let status = 0;
    if (window.api && typeof window.api.del === 'function') {
      body = await window.api.del(`${A}/teams/${tid}/skills/${encodeURIComponent(rawSkillId)}`);
      const err = window.api._lastError || {};
      status = body ? 200 : (err.status || 0);
      if (!body && status === 404) {
        body = { status: 'already_deleted', skill_id: rawSkillId };
        status = 200;
      }
    } else {
      const resp = await csrfFetch(`${A}/teams/${tid}/skills/${encodeURIComponent(rawSkillId)}`, { method: 'DELETE' });
      status = resp.status;
      body = await resp.json().catch(() => ({}));
      if (status === 404) {
        body = { status: 'already_deleted', skill_id: rawSkillId };
        status = 200;
      }
    }

    const ok = status >= 200 && status < 300 && (
      !body || body.status === 'deleted' || body.status === 'already_deleted' || body.skill_id || body.deleted
    );
    if (ok) {
      toast(body && body.status === 'already_deleted'
        ? `「${rawSkillName || rawSkillId}」已不存在`
        : `✅ 已删除「${rawSkillName || rawSkillId}」`);
      // 只软刷技能 Tab 内容，不 location.reload / 不跳转
      if (typeof atab !== 'undefined') atab = 'ag-skills';
      if (typeof loadAgent === 'function' && (window.aid || aid)) {
        try { await loadAgent(window.aid || aid); } catch (_) {}
      }
      if (typeof loadSkills === 'function') {
        try { await loadSkills(); } catch (_) {}
      }
      return;
    }

    // 409 强制删
    if (status === 409) {
      const detail = (body && (body.detail || body.message)) || '技能已通过验证/发布，不允许直接删除';
      if (confirm(String(detail) + '\n\n是否强制删除？')) {
        const resp2 = await csrfFetch(
          `${A}/teams/${tid}/skills/${encodeURIComponent(rawSkillId)}?force=true`,
          { method: 'DELETE' }
        );
        if (resp2.ok || resp2.status === 404) {
          toast(`✅ 已强制删除「${rawSkillName || rawSkillId}」`);
          _removeSkillRowsFromDom(rawSkillId);
          if (typeof loadAgent === 'function' && (window.aid || aid)) await loadAgent(window.aid || aid);
          if (typeof loadSkills === 'function') try { await loadSkills(); } catch (_) {}
          return;
        }
        toast('强制删除失败 HTTP ' + resp2.status);
      }
      // 用户取消强制删 → 刷回列表
      if (typeof loadAgent === 'function' && (window.aid || aid)) await loadAgent(window.aid || aid);
      return;
    }

    const errMsg = (window.api && window.api._lastError && window.api._lastError.message)
      || (body && (body.detail || body.message))
      || ('HTTP ' + status);
    toast('删除失败：' + errMsg);
    // 失败时刷回真实列表，恢复被乐观移除的行
    if (typeof loadAgent === 'function' && (window.aid || aid)) await loadAgent(window.aid || aid);
  } catch (e) {
    toast('删除失败: ' + (e && e.message ? e.message : e));
    if (typeof loadAgent === 'function' && (window.aid || aid)) {
      try { await loadAgent(window.aid || aid); } catch (_) {}
    }
  } finally {
    _skillCtxDeleteInFlight.delete(rawSkillId);
  }
}

// Export
window.deleteSkillWithContext = deleteSkillWithContext;

// ══════════════════════════════════
//  记忆绑定（四层记忆核心 · TigerInBamboo 移植）
//  运行日志 / 感知流 / 未发送队列 / 情绪残留
// ══════════════════════════════════
const _MEM = () => `${A}/teams/${tid}/agents/${aid}/memory-core`;
const _MEM_HUB = () => `/api/v1/agent-memory/${encodeURIComponent(tid)}/${encodeURIComponent(aid)}`;
let _memPane = 'log';

function _memFmtTime(t){
  if(t==null||t==='') return '—';
  try{
    const d=new Date(Number(t));
    if(Number.isNaN(d.getTime())) return String(t);
    return d.toLocaleString();
  }catch(_){ return String(t); }
}

function _memPersonaLabel(p){
  return {xiaoman:'小满',shenmian:'沈弥安',hybrid:'混合'}[p]||p||'混合';
}

function _memStateLabel(s){
  return ({
    active:'活体',shared:'共享中',sealed:'已封存',unbound:'未绑定',
    destroyed:'已销毁',archived:'凭吊',transferring:'传递中'
  })[s]||s||'—';
}

async function renderAgentMemoryBind(agent){
  const c=el('agent-content');
  try{
    const data=await api(_MEM());
    if(!data){ c.innerHTML='<div class="section"><p style="color:var(--red)">加载记忆失败</p></div>'; return; }
    let life={};
    try{ life=await api(_MEM_HUB()+'/lifecycle')||{}; }catch(_){ life={}; }
    const state=life.state||data.state||(data.sealed?'sealed':(data.bound===false?'unbound':'active'));
    const persona=life.persona||data.persona||'hybrid';
    const sealed=!!data.sealed||state==='sealed'||state==='archived';
    const bound=data.bound!==false&&state!=='unbound'&&state!=='destroyed';
    const counts=data.counts||{};
    const ro=sealed?' disabled':'';
    const memorialBanner=sealed
      ? `<div style="padding:12px 14px;margin-bottom:12px;border:1px solid rgba(196,75,75,.35);border-radius:10px;background:rgba(196,75,75,.06)">
          <div style="font-weight:700;color:#8B1E1E">这是回放，不是本人</div>
          <div style="font-size:12px;color:var(--muted);margin-top:4px">你在凭吊一段封存的记忆 —— 一切只读，时间轴可拖动回放</div>
        </div>` : '';
    const tone=data.tone_hint||'语气平静，没有明显的情绪残留。';
    const logRows=(data.log||[]).slice().reverse().map(e=>`
      <div class="focus-item" style="padding:8px 12px">
        <div class="title" style="font-size:12px"><b>${escapeHtml(e.action||'事件')}</b>
          <span style="color:var(--dim);font-size:11px;margin-left:6px">${escapeHtml(_memFmtTime(e.t))}</span>
          <span class="chip" style="font-size:9px;margin-left:6px">重要度 ${e.importance??5}</span>
        </div>
        <div class="meta">${escapeHtml(e.detail||'')}${e.place?` · 📍 ${escapeHtml(e.place)}`:''}
          ${(e.tags||[]).map(t=>`<span class="chip" style="font-size:9px">${escapeHtml(t)}</span>`).join(' ')}
        </div>
      </div>`).join('') || '<p style="color:var(--dim);font-size:12px">暂无运行日志</p>';
    const perc=(data.perception||[]).slice().reverse().map(p=>`
      <div class="focus-item" style="padding:6px 12px">
        <span class="chip" style="font-size:9px">${escapeHtml(p.modality||'?')}</span>
        <span style="font-size:11px;color:var(--muted)">${escapeHtml(typeof p.payload==='object'?JSON.stringify(p.payload):(p.payload||''))}</span>
        <span style="color:var(--dim);font-size:10px;margin-left:6px">${escapeHtml(_memFmtTime(p.t))}</span>
      </div>`).join('') || '<p style="color:var(--dim);font-size:12px">感知缓冲为空</p>';
    const intents=(data.intentions||[]).map(i=>`
      <div class="focus-item" style="padding:10px 12px">
        <div class="title" style="font-size:12px">${escapeHtml(i.instruction||'')}
          <span class="chip" style="font-size:9px">${escapeHtml(i.dueLabel||i.status||'')}</span>
        </div>
        <div class="meta">创建          创建者 ${escapeHtml(i.creator||'—')} · 触发 ${escapeHtml(i.trigger||'—')} · 策略 ${escapeHtml(i.timeoutPolicy||'drop')}
          ${!sealed?`<button class="btn btn-sm" style="margin-left:8px" onclick="memConfirmIntention('${escapeHtml(i.id)}')">确认</button>
          <button class="btn btn-sm btn-ghost" onclick="memDropIntention('${escapeHtml(i.id)}')">放弃</button>`:''}
        </div>
      </div>`).join('') || '<p style="color:var(--dim);font-size:12px">无待办意图</p>';
    const aff=data.affect||{};
    const labels=Object.entries(aff.labels||{}).map(([k,v])=>
      `<span class="chip" style="font-size:10px">${escapeHtml(k)} ${(Number(v)*100).toFixed(0)}%</span>`
    ).join(' ') || '<span style="color:var(--dim);font-size:12px">无标签</span>';

    c.innerHTML=`
      ${memorialBanner}
      <div class="section">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:12px">
          <div>
            <div class="section-title" style="margin:0">🧠 记忆绑定 · ${escapeHtml(agent.name||agent.agent_id||aid)}</div>
            <p style="color:var(--muted);font-size:12px;margin:4px 0 0">
              四层记忆共享时间轴：运行日志 · 感知流 · 未发送队列 · 情绪残留。
              封存是仪式不是删除。与站级「Agent记忆」中枢共用同一存储。
            </p>
          </div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <a class="btn btn-sm btn-pink" href="/agent-memory.html?team_id=${encodeURIComponent(tid||'')}&agent_id=${encodeURIComponent(aid||'')}&seg=agents">打开记忆中枢</a>
            <button class="btn btn-sm ${bound?'btn-pink':''}" onclick="memToggleBind(${bound? 'false':'true'})">${bound?'已绑定 · 点此解绑':'绑定记忆'}</button>
            ${!sealed?`<button class="btn btn-sm" onclick="memSeal()">封 存</button>`:''}
            <button class="btn btn-sm btn-ghost" onclick="memLifeAct('save')">保存固化</button>
            <button class="btn btn-sm btn-ghost" onclick="memExport()">导出</button>
            ${!sealed?`<button class="btn btn-sm btn-ghost" onclick="memImportPrompt()">导入</button>`:''}
            <button class="btn btn-sm btn-ghost" onclick="memWillDraft()">遗嘱草稿</button>
            <button class="btn btn-sm btn-ghost" style="color:var(--red,#B33A3A)" onclick="memLifeAct('destroy')">销毁</button>
            <button class="btn btn-sm btn-ghost" onclick="renderAgentMemoryBind()">刷新</button>
          </div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:11px;font-family:var(--font-mono);color:var(--muted);margin-bottom:10px;align-items:center">
          <span class="chip">状态 ${_memStateLabel(state)}</span>
          <span class="chip">Persona ${_memPersonaLabel(persona)}</span>
          <span>日志 ${counts.log||0}</span>
          <span>感知 ${counts.perception||0}</span>
          <span>意图待办 ${counts.intentions_pending||0}/${counts.intentions||0}</span>
          <span>情绪标签 ${counts.affect_labels||0}</span>
          <span>${sealed?'🔒 已封存':'🟢 活体'}</span>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;align-items:center;font-size:12px">
          <span style="color:var(--muted)">切换 Persona：</span>
          ${[['xiaoman','小满'],['shenmian','沈弥安'],['hybrid','混合']].map(([id,lab])=>
            `<button class="btn btn-sm ${persona===id?'btn-pink':''}" onclick="memSetPersona('${id}')">${lab}</button>`
          ).join('')}
        </div>
        <div style="padding:10px 12px;border-radius:8px;background:var(--panel2,rgba(0,0,0,.03));font-size:12px;color:var(--muted);margin-bottom:14px">
          💬 语气提示：<b style="color:var(--text)">${escapeHtml(tone)}</b>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px" id="mem-tabs">
          ${[['log','运行日志'],['perception','感知流'],['intentions','未发送队列'],['affect','情绪残留'],['timeline','时间轴']].map(([k,lab])=>
            `<button class="btn btn-sm ${_memPane===k?'btn-pink':''}" data-pane="${k}" onclick="memSwitchPane('${k}')">${lab}</button>`
          ).join('')}
        </div>
      </div>

      <div class="section mem-pane" id="mem-pane-log" style="${_memPane==='log'?'':'display:none'}">
        <div class="section-title">运行日志（append-only）</div>
        <p style="color:var(--dim);font-size:12px;margin-bottom:8px">检索 score = 时新(0.995/小时) + 重要度/10 + 词面匹配</p>
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
          <input class="fi" id="mem-log-q" placeholder="检索：词 / 标签 / 地点…" style="flex:1;min-width:160px" ${ro}/>
          <button class="btn btn-sm" onclick="memRecallLog()" ${ro}>检索</button>
          <button class="btn btn-sm btn-ghost" onclick="renderAgentMemoryBind()">全部</button>
        </div>
        <div id="mem-log-list">${logRows}</div>
        ${!sealed?`
        <details style="margin-top:12px">
          <summary style="cursor:pointer;font-size:12px;color:var(--muted)">＋ 追加一条记忆</summary>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px">
            <input class="fi" id="mem-log-subject" placeholder="主体" value="${escapeHtml(agent.name||aid)}"/>
            <input class="fi" id="mem-log-action" placeholder="动作，如：扩容 / 对话"/>
            <input class="fi" id="mem-log-place" placeholder="地点"/>
            <label style="font-size:11px;color:var(--muted)">重要度 <span id="mem-log-imp-v">5</span>
              <input type="range" id="mem-log-imp" min="1" max="10" value="5" oninput="el('mem-log-imp-v').textContent=this.value"/>
            </label>
            <textarea class="fi" id="mem-log-detail" rows="2" placeholder="详情" style="grid-column:1/-1"></textarea>
            <input class="fi" id="mem-log-tags" placeholder="标签，逗号分隔" style="grid-column:1/-1"/>
          </div>
          <button class="btn btn-pink btn-sm" style="margin-top:8px" onclick="memAppendLog()">记入日志</button>
        </details>`:''}
      </div>

      <div class="section mem-pane" id="mem-pane-perception" style="${_memPane==='perception'?'':'display:none'}">
        <div class="section-title">感知流（环形缓冲 500）</div>
        <p style="color:var(--dim);font-size:12px;margin-bottom:8px">易逝刺激；「压缩固化」聚合写入运行日志</p>
        ${!sealed?`
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
          <select class="fi" id="mem-perc-mod" style="width:auto">
            <option value="vision">视觉</option><option value="audition">听觉</option>
            <option value="touch">触觉</option><option value="weather">气象</option><option value="smell">嗅觉</option>
            <option value="alert">告警</option><option value="metric">指标</option>
          </select>
          <input class="fi" id="mem-perc-payload" placeholder='载荷文本或 JSON {"fear":0.6}' style="flex:1;min-width:160px"/>
          <button class="btn btn-sm" onclick="memPerceive()">注入感知</button>
          <button class="btn btn-sm btn-pink" onclick="memCompress()">压缩固化</button>
        </div>`:''}
        <div style="font-size:11px;color:var(--muted);margin-bottom:8px">缓冲 ${(data.perception_summary&&data.perception_summary.count)||0} 条
          ${data.perception_summary&&data.perception_summary.byModality? ' · '+Object.entries(data.perception_summary.byModality).map(([k,v])=>k+':'+v).join(', '):''}
        </div>
        <div id="mem-perc-list">${perc}</div>
      </div>

      <div class="section mem-pane" id="mem-pane-intentions" style="${_memPane==='intentions'?'':'display:none'}">
        <div class="section-title">未发送队列（prospective）</div>
        <p style="color:var(--dim);font-size:12px;margin-bottom:8px">打算做但还没做 —— 创建者 / 触发 / 超时策略 / 交接预留</p>
        ${!sealed?`
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">
          <input class="fi" id="mem-in-instruction" placeholder="指令（打算做什么）" style="grid-column:1/-1"/>
          <input class="fi" id="mem-in-creator" placeholder="创建者"/>
          <input class="fi" id="mem-in-trigger" placeholder="触发条件"/>
          <select class="fi" id="mem-in-timeout"><option value="drop">到期放弃 drop</option><option value="escalate">到期提醒 escalate</option><option value="keep">持续保留 keep</option></select>
          <select class="fi" id="mem-in-conf"><option value="normal">置信 normal</option><option value="unclear">置信 unclear</option></select>
          <button class="btn btn-pink btn-sm" onclick="memAddIntention()" style="grid-column:1/-1;justify-self:start">存入队列</button>
        </div>`:''}
        <div id="mem-intent-list">${intents}</div>
      </div>

      <div class="section mem-pane" id="mem-pane-affect" style="${_memPane==='affect'?'':'display:none'}">
        <div class="section-title">情绪残留</div>
        <p style="color:var(--dim);font-size:12px;margin-bottom:8px">只影响语气，不参与事实检索 · 衰减 η=72h</p>
        <div style="font-size:12px;margin-bottom:8px">valence ${Number(aff.valence||0).toFixed(2)} · arousal ${Number(aff.arousal||0).toFixed(2)}</div>
        <div style="margin-bottom:10px">${labels}</div>
        ${!sealed?`
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <input class="fi" id="mem-aff-label" placeholder="标签，如：谨慎 / 牵挂" style="width:140px"/>
          <input class="fi" id="mem-aff-intensity" type="number" min="0" max="1" step="0.1" value="0.5" style="width:80px" title="强度"/>
          <input class="fi" id="mem-aff-valence" type="number" min="-1" max="1" step="0.1" value="0" style="width:80px" title="效价"/>
          <button class="btn btn-sm btn-pink" onclick="memFeel()">注入感受</button>
        </div>`:''}
      </div>

      <div class="section mem-pane" id="mem-pane-timeline" style="${_memPane==='timeline'?'':'display:none'}">
        <div class="section-title">共享时间轴</div>
        <p style="color:var(--dim);font-size:12px;margin-bottom:8px">给定时刻 t，四层切片并集（回放任一层可拉到另外三层）</p>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px">
          <input type="range" id="mem-timeline" min="0" max="100" value="100" style="flex:1;min-width:180px" oninput="memTimelinePreview()"/>
          <span id="mem-timeline-label" style="font-size:11px;color:var(--muted);font-family:var(--font-mono)">现在</span>
          <button class="btn btn-sm" onclick="memTimelineLoad()">查看切片</button>
        </div>
        <div id="mem-timeline-slice" style="font-size:12px;color:var(--muted)">拖动滑块后点「查看切片」</div>
      </div>
    `;
    window._memCache = data;
  }catch(e){
    c.innerHTML=`<div class="section"><p style="color:var(--red)">记忆加载异常: ${escapeHtml(e.message||e)}</p>
      <button class="btn btn-sm" onclick="memToggleBind(true)">尝试绑定并重试</button></div>`;
  }
}

function memSwitchPane(pane){
  _memPane=pane||'log';
  if(typeof renderAgentMemoryBind==='function') renderAgentMemoryBind();
}

async function memToggleBind(enabled){
  const r=await api(_MEM()+'/bind',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:!!enabled})});
  if(r){ toast(enabled?'记忆已绑定':'记忆已解绑'); renderAgentMemoryBind(); }
  else toast('绑定失败','error');
}

async function memLifeAct(action){
  if(action==='destroy'&&!confirm('销毁将删除四层记忆并写墓碑，不可静默恢复。确认？')) return;
  try{
    const r=await api(_MEM_HUB()+'/lifecycle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});
    if(r&&(r.ok||r.state||r.status)){ toast('已执行 '+action); renderAgentMemoryBind(); }
    else toast((r&&r.detail)||'操作失败','error');
  }catch(e){ toast('失败: '+(e.message||e),'error'); }
}

async function memSetPersona(persona){
  try{
    const r=await api(_MEM_HUB()+'/persona',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({persona})});
    if(r&&r.ok!==false){ toast('Persona → '+_memPersonaLabel(persona)); renderAgentMemoryBind(); }
    else toast('切换失败','error');
  }catch(e){ toast('失败: '+(e.message||e),'error'); }
}

async function memAppendLog(){
  const body={
    subject:(el('mem-log-subject')||{}).value||aid,
    action:(el('mem-log-action')||{}).value||'',
    detail:(el('mem-log-detail')||{}).value||'',
    place:(el('mem-log-place')||{}).value||'',
    importance:Number((el('mem-log-imp')||{}).value||5),
    tags:String((el('mem-log-tags')||{}).value||'').split(/[,，]/).map(s=>s.trim()).filter(Boolean),
  };
  if(!body.action&&!body.detail){ toast('请填写动作或详情','error'); return; }
  const r=await api(_MEM()+'/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r&&r.ok){ toast('已记入日志'); renderAgentMemoryBind(); } else toast('写入失败','error');
}

async function memRecallLog(){
  const q=(el('mem-log-q')||{}).value||'';
  const r=await api(_MEM()+`/log?recall=1&query=${encodeURIComponent(q)}&k=20`);
  const list=el('mem-log-list');
  if(!list) return;
  const hits=(r&&r.hits)||[];
  if(!hits.length){ list.innerHTML='<p style="color:var(--dim);font-size:12px">无匹配</p>'; return; }
  list.innerHTML=hits.map(h=>{
    const e=h.event||{};
    return `<div class="focus-item" style="padding:8px 12px">
      <div class="title" style="font-size:12px"><b>${escapeHtml(e.action||'')}</b>
        <span class="chip" style="font-size:9px">score ${Number(h.score||0).toFixed(2)}</span>
      </div>
      <div class="meta">${escapeHtml(e.detail||'')} · R${(h.parts&&h.parts.recency||0).toFixed(2)} I${(h.parts&&h.parts.importance||0).toFixed(2)} V${(h.parts&&h.parts.relevance||0).toFixed(2)}</div>
    </div>`;
  }).join('');
}

async function memPerceive(){
  let payload=(el('mem-perc-payload')||{}).value||'';
  try{ if(payload.trim().startsWith('{')) payload=JSON.parse(payload); }catch(_){}
  const body={ modality:(el('mem-perc-mod')||{}).value||'vision', payload };
  const r=await api(_MEM()+'/perception',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r&&r.ok){ toast('已注入感知'); renderAgentMemoryBind(); } else toast('失败','error');
}

async function memCompress(){
  const r=await api(_MEM()+'/perception/compress',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  if(r&&r.ok){ toast(r.compressed?'已压缩固化到日志':'缓冲为空'); renderAgentMemoryBind(); }
  else toast('压缩失败','error');
}

async function memAddIntention(){
  const instruction=(el('mem-in-instruction')||{}).value||'';
  if(!instruction.trim()){ toast('请填写指令','error'); return; }
  const body={
    instruction,
    creator:(el('mem-in-creator')||{}).value||'',
    trigger:(el('mem-in-trigger')||{}).value||'',
    timeoutPolicy:(el('mem-in-timeout')||{}).value||'drop',
    provenance:{ confidence:(el('mem-in-conf')||{}).value||'normal' },
  };
  const r=await api(_MEM()+'/intentions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r&&r.ok){ toast('意图已入队'); renderAgentMemoryBind(); } else toast('失败','error');
}

async function memConfirmIntention(id){
  const r=await api(_MEM()+`/intentions/${encodeURIComponent(id)}/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  if(r&&r.ok){ toast('已确认'); renderAgentMemoryBind(); } else toast('失败','error');
}

async function memDropIntention(id){
  const r=await api(_MEM()+`/intentions/${encodeURIComponent(id)}/drop`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  if(r&&r.ok){ toast('已放弃'); renderAgentMemoryBind(); } else toast('失败','error');
}

async function memFeel(){
  const label=(el('mem-aff-label')||{}).value||'';
  if(!label.trim()){ toast('请填写情绪标签','error'); return; }
  const body={
    label,
    intensity:Number((el('mem-aff-intensity')||{}).value||0.5),
    valence:Number((el('mem-aff-valence')||{}).value||0),
    arousal:0.5,
  };
  const r=await api(_MEM()+'/affect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r&&r.ok){ toast('已注入 · '+ (r.tone_hint||'')); renderAgentMemoryBind(); } else toast('失败','error');
}

async function memSeal(){
  if(!confirm('封存是仪式不是删除：将生成只读快照，活体写入关闭。确认封存？')) return;
  const r=await api(_MEM()+'/seal',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  if(r&&r.ok){ toast('已封存 · 这是回放，不是本人'); renderAgentMemoryBind(); } else toast('封存失败','error');
}

async function memExport(){
  const r=await api(_MEM()+'/export');
  if(!r){ toast('导出失败','error'); return; }
  const blob=new Blob([JSON.stringify(r,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=`memory-${tid}-${aid}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  toast('已导出记忆 JSON');
}

async function memImportPrompt(){
  const raw=prompt('粘贴记忆 JSON（schema=ag.memory/v1）：');
  if(!raw) return;
  let data;
  try{ data=JSON.parse(raw); }catch(_){ toast('JSON 无效','error'); return; }
  const r=await api(_MEM()+'/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  if(r&&r.ok){ toast('导入成功'); renderAgentMemoryBind(); } else toast('导入失败','error');
}

async function memWillDraft(){
  const r=await api(_MEM()+'/will');
  if(!r){ toast('失败','error'); return; }
  const blob=new Blob([JSON.stringify(r,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=`will-draft-${aid}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  toast('遗嘱草稿已下载（协议 define-only）');
}

function memTimelinePreview(){
  const s=el('mem-timeline');
  const lab=el('mem-timeline-label');
  if(!s||!lab) return;
  const pct=Number(s.value||100);
  lab.textContent=pct>=100?'现在':`回放位置 ${pct}%`;
}

async function memTimelineLoad(){
  const cache=window._memCache||{};
  const logs=cache.log||[];
  const times=logs.map(e=>Number(e.t)).filter(Number.isFinite);
  let t=Date.now();
  if(times.length){
    const min=Math.min(...times), max=Math.max(...times, Date.now());
    const pct=Number((el('mem-timeline')||{}).value||100)/100;
    t=Math.round(min+(max-min)*pct);
  }
  const r=await api(_MEM()+`/at?t=${t}&window_ms=3600000`);
  const box=el('mem-timeline-slice');
  if(!box) return;
  if(!r||!r.slice){ box.textContent='无切片'; return; }
  const sl=r.slice;
  box.innerHTML=`
    <div style="margin-bottom:6px;font-family:var(--font-mono);font-size:11px">t = ${_memFmtTime(sl.t)}</div>
    <div><b>日志</b> ${(sl.log||[]).length} · <b>感知</b> ${(sl.perception||[]).length} · <b>意图</b> ${(sl.intentions||[]).length}</div>
    <div style="margin-top:6px">情绪 valence ${Number((sl.affect||{}).valence||0).toFixed(2)} · labels ${Object.keys((sl.affect||{}).labels||{}).join(', ')||'—'}</div>
    <ul style="margin:8px 0 0;padding-left:18px;font-size:11px;color:var(--muted)">
      ${(sl.log||[]).slice(0,8).map(e=>`<li>${escapeHtml(e.action||'')} — ${escapeHtml((e.detail||'').slice(0,80))}</li>`).join('')}
    </ul>`;
}

// ══════════════════════════════════
//  5-STEP WIZARD
// ══════════════════════════════════

// Export functions referenced from HTML onclick handlers and other scripts
window.loadAgent = loadAgent;
window.renderAgentMemoryBind = renderAgentMemoryBind;
window.memSwitchPane = memSwitchPane;
window.memToggleBind = memToggleBind;
window.memAppendLog = memAppendLog;
window.memRecallLog = memRecallLog;
window.memPerceive = memPerceive;
window.memCompress = memCompress;
window.memAddIntention = memAddIntention;
window.memConfirmIntention = memConfirmIntention;
window.memDropIntention = memDropIntention;
window.memFeel = memFeel;
window.memSeal = memSeal;
window.memExport = memExport;
window.memImportPrompt = memImportPrompt;
window.memWillDraft = memWillDraft;
window.memTimelinePreview = memTimelinePreview;
window.memTimelineLoad = memTimelineLoad;
window.memLifeAct = memLifeAct;
window.memSetPersona = memSetPersona;
window.sendChatMsg = sendChatMsg;
window.newSession = newSession;
window.saveAgent = saveAgent;
window.testAgentLLM = testAgentLLM;
window.delAgent = delAgent;
window.startStop = startStop;
window.togAgentTool = togAgentTool;
window.togAgentSkill = togAgentSkill;
window.openChatSession = openChatSession;
window.closeChatSession = closeChatSession;
window.toggleSoulEdit = toggleSoulEdit;
window.saveSoul = saveSoul;
window.addMemoryFile = addMemoryFile;
window.openMemoryFile = openMemoryFile;
window.saveMemoryFile = saveMemoryFile;
window.closeMemEditor = closeMemEditor;
window.delMemoryFile = delMemoryFile;
window.renderEmployeeView = renderEmployeeView;
window.switchEmployeeFileTab = switchEmployeeFileTab;
window.saveEmployeeFile = saveEmployeeFile;
window.appendEmployeeMemory = appendEmployeeMemory;
window.resetEmployeeHeartbeat = resetEmployeeHeartbeat;
window.updateEmployeeTriggerFields = updateEmployeeTriggerFields;
window.createEmployeeTrigger = createEmployeeTrigger;
window.toggleEmployeeTrigger = toggleEmployeeTrigger;
window.deleteEmployeeTrigger = deleteEmployeeTrigger;
window.updateEmployeeRelationTarget = updateEmployeeRelationTarget;
window.createEmployeeRelationship = createEmployeeRelationship;
window.deleteEmployeeRelationship = deleteEmployeeRelationship;
window.setEmployeeAutonomy = setEmployeeAutonomy;
window.saveEmployeeGovernance = saveEmployeeGovernance;
window.previewEmployeeContext = previewEmployeeContext;

})();
