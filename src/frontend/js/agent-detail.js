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
    // Fetch real metrics from the new endpoint
    Promise.all([
      api(`${A}/teams/${tid}/agents/${aid}/metrics`),
      api(`${A}/teams/${tid}/agents/${aid}/activity`)
    ]).then(([mt,act])=>{
      mt=mt||{};act=act||{};
      c.innerHTML=`<div class="card-grid"><div class="stat-card"><div class="label">📋 状态</div><div class="value" style="font-size:16px"><span class="st st-${d.state||'idle'}">● ${stL(d.state)}</span></div><div class="sub"><button class="btn btn-sm" style="margin-top:6px;padding:3px 10px;font-size:11px" onclick="startStop('${escapeHtml(d.state)}')">${d.state==='working'?'⏹ 停止':'▶ 启动'}</button></div></div><div class="stat-card"><div class="label">📊 今日 Token</div><div class="value">${(mt.today_tokens||0).toLocaleString()}</div></div><div class="stat-card"><div class="label">📈 本月 Token</div><div class="value">${((mt.month_tokens||0)/1000).toFixed(1)}K</div></div><div class="stat-card"><div class="label">🤖 今日 LLM 调用</div><div class="value">${mt.today_llm_calls||0}</div><div class="sub">消息: ${mt.messages_sent||0}</div></div><div class="stat-card"><div class="label">🔄 总 Token</div><div class="value">${((mt.total_tokens||0)/1000).toFixed(1)}K</div></div><div class="stat-card"><div class="label">✅ 任务完成</div><div class="value">${mt.tasks_completed||0}</div><div class="sub">失败: ${mt.tasks_failed||0}</div></div><div class="stat-card"><div class="label">🔧 工具调用</div><div class="value">${mt.tools_invoked||0}</div></div><div class="stat-card"><div class="label">🔴 24h 活动</div><div class="value">${act.total_actions||0}</div></div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div class="card"><div class="section-title">📁 Agent 档案</div><div class="detail-row"><span class="lbl">👤 角色</span><span class="val">${escapeHtml(d.role||d.description||'-')}</span></div><div class="detail-row"><span class="lbl">📅 创建时间</span><span class="val">${cr}</span></div><div class="detail-row"><span class="lbl">👤 创建者</span><span class="val">@system</span></div><div class="detail-row"><span class="lbl">🔴 最后活跃</span><span class="val">${mt.last_active?mt.last_active.split('T')[0]:'从未'}</span></div><div class="detail-row"><span class="lbl">💬 会话数</span><span class="val">${mt.sessions_created||0}</span></div><div class="detail-row"><span class="lbl">🧠 是否 Hermes</span><span class="val">${d.is_hermes_agent?'<span style="color:var(--lime)">✓</span>':'—'}</span></div></div><div class="card"><div class="section-title">🧠 模型配置</div><div class="detail-row"><span class="lbl">🟠 模型</span><span class="val">${escapeHtml(d.model_id||'未配置')}</span></div><div class="detail-row"><span class="lbl">📁 模板</span><span class="val">${escapeHtml(d.template_type||'-')}</span></div><div class="detail-row"><span class="lbl">🔧 工具数</span><span class="val">${(d.tools||[]).length}</span></div><div class="detail-row"><span class="lbl">⚡ 技能数</span><span class="val">${(d.skills||[]).length}</span></div><div class="detail-row"><span class="lbl">📡 通道数</span><span class="val">${(d.channels||[]).length}</span></div></div></div><div class="section" style="margin-top:20px"><div class="section-title">📊 近期活动</div>${act.recent_logs&&act.recent_logs.length?act.recent_logs.slice(-8).reverse().map(l=>`<div class="focus-item" style="padding:10px 14px"><div class="title" style="font-size:13px"><span class="chip" style="font-size:10px">${escapeHtml(l.action)}</span> ${escapeHtml(l.detail||'')}</div><div class="meta">${l.timestamp?l.timestamp.replace('T',' ').slice(0,19):''}</div></div>`).join(''):'<p style="color:var(--dim);font-size:13px">暂无活动记录 — 发送消息或启动 Agent 后将显示</p>'}</div>`;
    });
  } else if(atab==='ag-aware'){
    const tr=m.traits||[],bd=m.behavior_boundaries||[];
    c.innerHTML=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">关注点</div><span style="color:var(--dim);font-size:12px">${(d.skills||[]).length+tr.length} active</span></div><p style="color:var(--muted);font-size:12px;margin-bottom:14px">Agent 当前正在关注的任务</p>${(d.skills||[]).map(s=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--pink)"></span>${escapeHtml(s)}</div><div class="meta">skill · active</div></div>`).join('')}${tr.map(t=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--amber)"></span>${escapeHtml(t)}</div><div class="meta">trait · personality</div></div>`).join('')}${bd.map(b=>`<div class="focus-item"><div class="title"><span class="dot" style="width:8px;height:8px;background:var(--dim)"></span>${escapeHtml(b)}</div><div class="meta">boundary · constraint</div></div>`).join('')}${!(d.skills||[]).length&&!tr.length&&!bd.length?'<p style="color:var(--dim)">暂无关注项</p>':''}</div>`;
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
  } else if(atab==='ag-tools'){
    api(`${A}/tools`).then(all=>{
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
    api(`${A}/teams/${tid}/skills`).then(teamSkills=>{
      const all=Array.isArray(teamSkills)?teamSkills:(teamSkills&&teamSkills.items)||[];
      const boundRefs=new Set(d.skills||[]);
      const boundSkills=[];const availableSkills=[];
      all.forEach(s=>{
        const isBound=boundRefs.has(s.skill_id)||boundRefs.has(s.name)||boundRefs.has(s.slug);
        (isBound?boundSkills:availableSkills).push(s);
      });
      const renderSkillRow=(s,isBound)=>`<div class="ws-item" style="padding:10px 14px"><span class="fname" style="gap:10px"><span style="font-size:18px">${s.icon||'⚡'}</span> <b>${s.name}</b> <span style="color:var(--dim);font-size:11px">${s.category||''}</span></span><span style="display:flex;align-items:center;gap:8px"><span style="color:var(--dim);font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(s.description||"")}</span>${s.has_instructions?`<button class="btn btn-sm btn-ghost" onclick="viewSkillInstructions('${escapeHtml(s.skill_id)}')" title="查看指令">📖</button>`:''}<button class="btn btn-sm btn-ghost" onclick="openEditSkill('${s.skill_id}')" title="编辑">✏️</button>${isBound?`<button class="btn btn-sm btn-ghost" onclick="deleteSkill('${s.skill_id}','${s.name}')" title="删除" style="color:var(--pink)">🗑️</button><button class="btn btn-sm btn-danger" onclick="togAgentSkill('${s.skill_id}',false)">解绑</button>`:`<button class="btn btn-sm" onclick="togAgentSkill('${s.skill_id}',true)">绑定</button>`}</span></div>`;
      let html=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">⚡ 当前团队技能</div><span style="color:var(--dim);font-size:12px">${boundSkills.length} / ${all.length} 已绑定</span></div>`;
      html+=`<div class="sb-section" style="margin-top:12px;margin-bottom:8px;font-size:11px;color:var(--dim);letter-spacing:1px">已绑定技能</div>`;
      html+=boundSkills.length?boundSkills.map(s=>renderSkillRow(s,true)).join(''):'<p style="color:var(--dim);padding:0 14px 12px">该智能体当前没有已绑定技能</p>';
      html+=`<div class="sb-section" style="margin-top:16px;margin-bottom:8px;font-size:11px;color:var(--dim);letter-spacing:1px">团队可用技能</div>`;
      html+=availableSkills.length?availableSkills.map(s=>renderSkillRow(s,false)).join(''):'<p style="color:var(--dim);padding:0 14px 4px">当前团队没有更多可绑定技能</p>';
      html+=`</div>`;
      c.innerHTML=html;
    });
  } else if(atab==='ag-relations'){
    api(`${A}/teams/${tid}/agents/${aid}/relationships`).then(rel=>{
      c.innerHTML=`<div class="section"><div class="section-title">🔗 关系</div>${rel&&rel.relationships&&rel.relationships.length?rel.relationships.map(r=>`<div class="ws-item"><span class="fname">👤 ${escapeHtml(r.target||r.name||'?')}</span><span class="chip">${escapeHtml(r.type||'peer')}</span></div>`).join(''):'<p style="color:var(--dim)">暂无</p>'}</div><div class="section"><div class="section-title">📡 通道绑定</div>${(d.channels||[]).length?d.channels.map(ch=>`<div class="ws-item"><span class="fname">📡 ${escapeHtml(ch.channel_name)}</span><span>${ch.subscribe?'<span class="chip">订阅</span>':''}${ch.publish?'<span class="chip">发布</span>':''}<span class="chip" style="background:rgba(255,207,112,0.1);color:var(--amber)">P${ch.priority??0}</span></span></div>`).join(''):'<p style="color:var(--dim)">暂无</p>'}</div>`;
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
    api(`${A}/teams/${tid}/agents/${aid}/sessions`).then(ss=>{c.innerHTML=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">💬 对话</div><button class="btn btn-pink btn-sm" onclick="newSession()">＋ 新建会话</button></div>${ss&&ss.length?ss.map(s=>`<div class="ws-item" style="cursor:pointer" onclick="openChatSession('${s.session_id||s.id}')"><span class="fname">💬 ${s.session_id||s.id}</span><span style="color:var(--dim);font-size:12px">${s.created_at||''}</span></div>`).join(''):'<p style="color:var(--dim)">暂无会话，点击上方按钮开始对话</p>'}</div>`});
  } else if(atab==='ag-logs'){
    api(`${A}/teams/${tid}/agents/${aid}/logs?limit=100`).then(lg=>{
      const logs=(lg&&lg.logs)||[];
      c.innerHTML=`<div class="section"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div class="section-title" style="margin:0">📋 工作日志</div><span style="color:var(--dim);font-size:12px">${logs.length} 条记录</span></div>${logs.length?logs.slice().reverse().map(l=>`<div class="focus-item" style="padding:10px 14px"><div class="title" style="font-size:13px"><span class="chip" style="font-size:10px">${l.action||'log'}</span> ${escapeHtml(l.detail||'')}</div><div class="meta">${l.timestamp?l.timestamp.replace('T',' ').slice(0,19):''}</div></div>`).join(''):'<p style="color:var(--dim)">暂无日志 — 与 Agent 交互后日志将自动生成</p>'}</div>`});
  } else if(atab==='ag-settings'){
    c.innerHTML=`<div class="card" style="max-width:600px"><div class="section-title">⚙️ 设置</div><div class="form-group"><label class="form-label">名称</label><input class="fi" value="${d.name||''}" id="set-name"></div><div class="form-group"><label class="form-label">角色</label><input class="fi" value="${d.role||''}" id="set-role"></div><div class="form-group"><label class="form-label">描述</label><textarea class="fi" id="set-desc">${d.description||''}</textarea></div><div class="form-group"><label class="form-label">系统提示词</label><textarea class="fi" id="set-prompt" rows="4">${d.system_prompt||''}</textarea></div><div class="form-group"><label class="form-label">模型 ID</label><input class="fi" value="${escapeHtml(d.model_id||'')}" id="set-model"></div><div id="agent-test-result" class="hidden" style="margin-top:12px;padding:14px;border-radius:0;border:1px solid var(--line);font-size:13px"></div><div style="display:flex;gap:10px;margin-top:20px"><button class="btn btn-pink" onclick="saveAgent()">保存</button><button class="btn" onclick="testAgentLLM()">🧪 测试连接</button><button class="btn btn-danger" onclick="delAgent()">删除</button></div></div>`;
  }
}
async function newSession(){const r=await api(`${A}/teams/${tid}/agents/${aid}/sessions`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});if(r){toast('会话已创建');_chatSid=r.session_id||r.id;loadAgent()}else{toast('已创建');loadAgent()}}
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
  const r=await api(`${A}/teams/${tid}/agents/${aid}/sessions/${_chatSid}/messages`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:'user',content:msg})}).catch(()=>null);
  inp.disabled=false;if(r){loadAgent();if(r.task_id){toast(`📋 任务已创建: ${r.task_id}`)}}else{toast('发送失败');inp.value=msg}}
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
async function delAgent(){if(!confirm('确定删除？'))return;await csrfFetch(`${A}/teams/${tid}/agents/${aid}`,{method:'DELETE'});toast('已删除');aid='';loadSbAgents();switchView('overview')}
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
  await api(`${A}/teams/${tid}/agents/${aid}/skills`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill_ids:[...cur]})});
  toast(bind?`已绑定 ${skillId}`:`已解绑 ${skillId}`);loadAgent();
}

// ══════════════════════════════════
//  5-STEP WIZARD
// ══════════════════════════════════

// Export functions referenced from HTML onclick handlers and other scripts
window.loadAgent = loadAgent;
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

})();
