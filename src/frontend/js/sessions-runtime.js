/**
 * AgentsGroup2026 — Sessions & Runtime Views
 * Manages persisted session listing, cross-session search,
 * PortRuntime route matching, and Tool Pool assembly.
 * Extracted from agent-team-config.js for modularity.
 * Depends on: utils.js, api.js, agent-team-config.js (parent scope)
 */
(function(){
'use strict';
function setOcMode(m){_ocMode=m;el('oc-mode-platform').classList.toggle('selected',m==='platform');el('oc-mode-openclaw').classList.toggle('selected',m==='openclaw');el('oc-form').style.display=m==='openclaw'?'block':'none';if(m==='platform'){closeModal('modal-import-openclaw');openWizard()}}
function setOcVis(v){_ocVis=v;el('oc-vis-public').classList.toggle('selected',v==='public');el('oc-vis-private').classList.toggle('selected',v==='private')}

el('btn-oc').onclick=async()=>{const n=el('oc-name').value.trim();if(!n){toast('智能体名称不能为空');return}const gw=el('oc-url').value.trim();if(!gw){toast('请输入 OpenClaw Gateway URL');return}const tk=el('oc-token').value.trim();if(!tk){toast('请输入 API Token');return}const t=el('oc-team').value||tid;const r=await api(`${A}/teams/${t}/agents/import-openclaw`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n,role:el('oc-role').value.trim(),openclaw_url:gw,openclaw_token:tk,visibility:_ocVis})});if(r){toast(`${n} 已连接！`);closeModal('modal-import-openclaw');el('oc-name').value='';el('oc-role').value='';el('oc-url').value='';el('oc-token').value='';tid=t;aid=r.agent_id;loadTeams()}else toast('连接失败')};

// populate OC team select when modal opens
const _origOpen=openModal;
openModal=function(id){_origOpen(id);if(id==='modal-import-openclaw'){api(`${A}/teams`).then(ts=>{const s=el('oc-team');s.innerHTML='';(ts||[]).forEach(t=>{const o=document.createElement('option');o.value=t.team_id;o.textContent=t.name;if(t.team_id===tid)o.selected=true;s.appendChild(o)})})}};

// ══════════════════════════════════
//  SESSION PERSISTENCE (claw-code-parity)
// ══════════════════════════════════
function showToolSearch(){el('tools-search-bar').classList.remove('hidden');el('tools-search-input').focus()}
function filterToolCards(q){
  const cards=el('tools-cards').querySelectorAll('[data-tool-name]');
  cards.forEach(c=>{const n=c.dataset.toolName||'';c.style.display=(!q||n.toLowerCase().includes(q.toLowerCase()))?'':'none'});
}
async function loadPersistedSessions(){hideViewLoading("view-sessions");
  const d=await api(`${A}/sessions/persisted`);
  const ls=el('ss-list'),ct=el('ss-count');
  if(!d||!d.sessions||!d.sessions.length){
    ls.innerHTML='<div style="padding:20px;text-align:center;color:var(--dim)"><div style="font-size:32px;margin-bottom:8px">📂</div><div style="font-size:14px;margin-bottom:6px">暂无已保存的会话</div><div style="font-size:12px">在 Agent 聊天中与智能体对话后，会话将自动出现在此处。<br>您也可以通过 API 调用 <code>POST /sessions/{id}/persist</code> 手动保存。</div></div>';
    ct.textContent='0 个会话';return;
  }
  ct.textContent=`${d.count} 个会话`;
  ls.innerHTML=d.sessions.map(sid=>`<div class="ws-item" style="cursor:pointer" data-sid="${escapeHtml(sid)}"><span class="fname"><span style="font-size:16px">💬</span> ${escapeHtml(sid)}</span><span style="display:flex;gap:8px"><button class="btn btn-sm" data-action="load" title="加载到活跃会话">📂 加载</button><button class="btn btn-sm btn-ghost" data-action="preview" title="预览">👁</button></span></div>`).join('');
  // Event delegation for session actions (XSS-safe)
  ls.onclick=function(e){
    const item=e.target.closest('[data-sid]');if(!item)return;
    const sid=item.dataset.sid;
    const btn=e.target.closest('[data-action]');
    if(btn){
      if(btn.dataset.action==='load')persistSessionToActive(sid);
      else if(btn.dataset.action==='preview')previewPersistedSession(sid);
    }else{loadPersistedSession(sid)}
  };
}
async function loadPersistedSession(sid){
  const d=await api(`${A}/sessions/persisted/${sid}/load`,{method:'POST'});
  if(d){toast(`会话 ${sid.slice(0,8)} 已加载到内存`)}else{toast('加载失败')}
}
function persistSessionToActive(sid){loadPersistedSession(sid)}
async function previewPersistedSession(sid){
  const d=await api(`${A}/sessions/persisted/${sid}/load`,{method:'POST'});
  if(!d){toast('无法加载会话');return}
  const msgs=(d.messages||[]).slice(-20);
  let html=`<div class="modal-overlay open" id="modal-preview-session" onclick="if(event.target===this)this.remove()"><div class="modal" style="width:640px;max-height:85vh"><h3>💬 会话预览</h3><div style="margin-bottom:12px;font-size:12px;color:var(--muted)"><b>会话 ID</b>: ${escapeHtml(sid)}<br><b>消息数</b>: ${d.message_count||msgs.length} · <b>创建</b>: ${d.created_at||'?'}</div><div style="max-height:50vh;overflow-y:auto;border:1px solid var(--line);border-radius:0;padding:12px">`;
  if(msgs.length){msgs.forEach(m=>{const isUser=m.role==='user';html+=`<div style="margin-bottom:10px;padding:10px 14px;background:${isUser?'var(--chat-user)':'var(--chat-agent)'};border:1px solid ${isUser?'var(--chat-user-border)':'var(--chat-agent-border)'};border-radius:0"><div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:4px">${escapeHtml(m.role||'?')}</div><div style="font-size:13px;white-space:pre-wrap;word-break:break-word">${escapeHtml((m.content||'').slice(0,500))}</div></div>`})}
  else{html+='<p style="color:var(--dim)">无消息记录</p>'}
  html+=`</div><div class="modal-actions"><button class="btn" onclick="document.getElementById('modal-preview-session').remove()">关闭</button><button class="btn btn-pink" onclick="loadPersistedSession('${escapeHtml(sid)}');document.getElementById('modal-preview-session').remove()">📂 加载到活跃会话</button></div></div></div>`;
  document.body.insertAdjacentHTML('beforeend',html);
}
async function searchPersistedSessions(){
  const q=el('ss-query').value.trim();
  if(!q){toast('请输入搜索关键词');return}
  const d=await api(`${A}/sessions/search`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,max_results:20})});
  const rc=el('ss-search-results');
  if(!d||!d.results||!d.results.length){
    rc.innerHTML='<p style="color:var(--dim)">未找到匹配结果</p>';return;
  }
  rc.innerHTML=`<p style="color:var(--muted);font-size:12px;margin-bottom:8px">找到 ${d.count} 个结果</p>`+
    d.results.map(r=>`<div class="focus-item" style="padding:10px 14px;cursor:pointer" onclick="loadPersistedSession('${escapeHtml(r.session_id||r.id||'')}')"><div class="title"><span class="chip" style="font-size:10px">${escapeHtml(r.session_id||r.id||'').slice(0,8)}</span> ${escapeHtml((r.snippet||r.content||'').slice(0,120))}</div><div class="meta">${r.score?`相关度: ${(r.score*100).toFixed(0)}%`:''}</div></div>`).join('');
}

// ══════════════════════════════════
//  PORT RUNTIME (claw-code-parity)
// ══════════════════════════════════
function _rtParams(){
  return{
    prompt:el('rt-prompt').value.trim(),
    limit:parseInt(el('rt-limit').value)||5,
    deny_tools:(el('rt-deny').value||'').split(',').map(s=>s.trim()).filter(Boolean),
    deny_prefixes:(el('rt-deny-pfx').value||'').split(',').map(s=>s.trim()).filter(Boolean)
  };
}
async function doRoutePrompt(){
  const p=_rtParams();if(!p.prompt){toast('请输入 Prompt');return}
  toast('正在路由匹配...');
  const d=await api(`${A}/runtime/route`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
  const rc=el('rt-results'),rcc=el('rt-results-content');rc.classList.remove('hidden');
  if(!d){rcc.innerHTML='<p style="color:var(--pink)">路由失败 — 后端 PortRuntime 服务可能未就绪，请检查后端日志</p>';return}
  if(!d.matches||!d.matches.length){rcc.innerHTML='<p style="color:var(--dim)">未匹配到工具/命令 — 尝试更具体的 Prompt</p>';return}
  rcc.innerHTML=`<p style="color:var(--muted);font-size:12px;margin-bottom:12px">匹配到 ${d.count||d.matches.length} 个工具/命令</p><table class="tbl"><thead><tr><th>类型</th><th>名称</th><th>来源</th><th>得分</th></tr></thead><tbody>${d.matches.map(m=>`<tr><td><span class="chip" style="font-size:10px;background:${m.kind==='tool'?'rgba(38,162,105,0.1);color:var(--lime)':'rgba(26,95,180,0.1);color:var(--cyan)'}">${m.kind}</span></td><td><b>${escapeHtml(m.name)}</b></td><td style="color:var(--muted)">${escapeHtml(m.source_hint||'-')}</td><td style="font-family:'IBM Plex Mono',monospace">${(m.score||0).toFixed(2)}</td></tr>`).join('')}</tbody></table>`;
}
async function doBootstrapSession(){
  const p=_rtParams();if(!p.prompt){toast('请输入 Prompt');return}
  toast('正在引导会话...');
  const d=await api(`${A}/runtime/bootstrap`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
  const rc=el('rt-results'),rcc=el('rt-results-content');rc.classList.remove('hidden');
  if(!d){rcc.innerHTML='<p style="color:var(--pink)">引导失败 — 后端 PortRuntime 服务可能未就绪，请检查后端日志</p>';return}
  let html=`<div class="card-grid">
    <div class="stat-card"><div class="label">🎯 匹配数</div><div class="value">${(d.matches||[]).length}</div></div>
    <div class="stat-card"><div class="label">🔧 工具结果</div><div class="value">${(d.tool_results||[]).length}</div></div>
    <div class="stat-card"><div class="label">⚙️ 命令结果</div><div class="value">${(d.command_results||[]).length}</div></div>
    <div class="stat-card"><div class="label">🚫 权限拒绝</div><div class="value" style="color:${(d.denials||[]).length?'var(--red)':'var(--lime)'}">${(d.denials||[]).length}</div></div>
  </div>`;
  if(d.matches&&d.matches.length){html+=`<div class="section" style="margin-top:16px"><div class="section-title">路由匹配</div>${d.matches.map(m=>`<div class="ws-item"><span class="fname"><span class="chip" style="font-size:10px">${m.kind}</span> ${m.name}</span><span style="font-family:'IBM Plex Mono',monospace;color:var(--dim)">${(m.score||0).toFixed(2)}</span></div>`).join('')}</div>`;}
  if(d.tool_results&&d.tool_results.length){html+=`<div class="section" style="margin-top:16px"><div class="section-title">🔧 工具执行结果</div>${d.tool_results.map(r=>`<div class="focus-item"><div class="title"><span class="chip">${r.name}</span> ${r.handled?'✅':'❌'}</div><div style="margin-top:8px;padding:10px;background:rgba(232,240,250,0.7);border-radius:6px;font-size:12px;font-family:'IBM Plex Mono',monospace;max-height:120px;overflow-y:auto;white-space:pre-wrap">${escapeHtml(r.output||'(无输出)')}</div></div>`).join('')}</div>`;}
  if(d.denials&&d.denials.length){html+=`<div class="section" style="margin-top:16px"><div class="section-title" style="color:var(--red)">🚫 权限拒绝</div>${d.denials.map(dn=>`<div class="ws-item" style="border-color:rgba(224,27,36,0.2)"><span class="fname" style="color:var(--red)">${dn.tool_name}</span><span style="color:var(--muted)">${dn.reason}</span></div>`).join('')}</div>`;}
  if(d.history&&d.history.length){html+=`<div class="section" style="margin-top:16px"><div class="section-title">📜 执行历史</div>${d.history.slice(-8).map(h=>`<div class="focus-item" style="padding:8px 14px"><div class="title" style="font-size:12px"><span class="chip" style="font-size:10px">${h.kind||h.type||'event'}</span> ${escapeHtml(h.summary||h.detail||'')}</div><div class="meta">${h.ts||h.timestamp||''}</div></div>`).join('')}</div>`;}
  rcc.innerHTML=html;
}
async function doRouteAndChat(){
  const p=_rtParams();if(!p.prompt){toast('请输入 Prompt');return}
  toast('路由+对话...');
  const d=await api(`${A}/runtime/route-and-chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
  const rc=el('rt-results'),rcc=el('rt-results-content');rc.classList.remove('hidden');
  if(!d){rcc.innerHTML='<p style="color:var(--pink)">请求失败 — 请先在「LLM 配置」中配置提供商和 API Key</p>';return}
  rcc.innerHTML=`<div class="card-grid">
    <div class="stat-card"><div class="label">🎯 路由匹配</div><div class="value">${d.matched_count||d.matches?.length||0}</div></div>
    <div class="stat-card"><div class="label">📊 Tokens</div><div class="value">${(d.usage?.total_tokens||0).toLocaleString()}</div></div>
  </div>
  <div class="section" style="margin-top:16px"><div class="section-title">💬 LLM 回复</div><div style="padding:16px;background:rgba(232,240,250,0.7);border-radius:0;font-size:13px;line-height:1.7;white-space:pre-wrap">${escapeHtml(d.response||d.content||d.answer||'(无回复)')}</div></div>`;
}
async function doAssemblePool(){
  const body={
    simple_mode:el('tp-simple').checked,
    include_mcp:el('tp-mcp').checked,
    deny_tools:(el('tp-deny').value||'').split(',').map(s=>s.trim()).filter(Boolean),
    deny_prefixes:(el('tp-deny-pfx').value||'').split(',').map(s=>s.trim()).filter(Boolean)
  };
  const d=await api(`${A}/tool-pool`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const rc=el('tp-results');
  if(!d){rc.innerHTML='<p style="color:var(--pink)">装配失败 — 后端 Tool Pool 服务未就绪</p>';return}
  rc.innerHTML=`<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px"><span class="chip" style="background:rgba(38,162,105,0.1);color:var(--lime)">共 ${d.count} 个工具</span>${d.simple_mode?'<span class="chip" style="background:rgba(255,207,112,0.15);color:var(--amber)">简单模式</span>':''}${d.include_mcp?'<span class="chip">含 MCP</span>':''}</div>
  <div style="display:flex;gap:6px;flex-wrap:wrap">${(d.tools||[]).map(t=>`<span class="chip" style="font-size:11px">${escapeHtml(t)}</span>`).join('')}</div>`;
}

// ══════════════════════════════════
//  TOKEN FACTORY — 自主 Token 工厂
// ══════════════════════════════════



// Export to global scope for HTML onclick access
window.loadPersistedSessions = loadPersistedSessions;
window.searchPersistedSessions = searchPersistedSessions;
window.showToolSearch = showToolSearch;
window.filterToolCards = filterToolCards;
window.setOcMode = setOcMode;
window.setOcVis = setOcVis;
window.doRoutePrompt = doRoutePrompt;
window.doBootstrapSession = doBootstrapSession;
window.doRouteAndChat = doRouteAndChat;
window.doAgentLoopPreview = doAgentLoopPreview;
window.doAgentLoopRun = doAgentLoopRun;
window.doAssemblePool = doAssemblePool;
})();
