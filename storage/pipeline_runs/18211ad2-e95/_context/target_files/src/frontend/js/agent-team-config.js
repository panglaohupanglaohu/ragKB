const A='/api/v1/agent-config',AT='/api/v1/agent-teams';
let tid='',aid='',atab='ag-status',wzD={},wzS=1;
let _offline=false;

function toast(m,type){
  const e=document.getElementById('toast');
  e.className='toast'+(type?' toast-'+type:'');
  e.textContent=m;e.classList.add('show');
  const dur=type==='error'?5000:2500;
  setTimeout(()=>e.classList.remove('show'),dur);
}
function openModal(id){
  const m=document.getElementById(id);m.classList.add('open');
  m.setAttribute('role','dialog');m.setAttribute('aria-modal','true');
  // Focus trap
  const focusable=m.querySelectorAll('button,input,select,textarea,[tabindex]:not([tabindex="-1"])');
  if(focusable.length)focusable[0].focus();
  m._focusTrap=e=>{
    if(e.key==='Escape'){closeModal(id);return}
    if(e.key!=='Tab')return;
    const first=focusable[0],last=focusable[focusable.length-1];
    if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
    else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
  };
  m.addEventListener('keydown',m._focusTrap);
}
function closeModal(id){
  const m=document.getElementById(id);m.classList.remove('open');
  m.removeAttribute('aria-modal');
  if(m._focusTrap){m.removeEventListener('keydown',m._focusTrap);delete m._focusTrap}
}

// Connection status banner
function showOfflineBanner(){
  if(document.getElementById('offline-banner'))return;
  const b=document.createElement('div');
  b.id='offline-banner';
  b.style.cssText='position:fixed;top:0;left:0;right:0;z-index:1000;background:var(--shu);color:var(--shironeri);padding:8px 16px;font-size:13px;text-align:center;display:flex;justify-content:center;align-items:center;gap:12px';
  b.innerHTML='⚠ 后端连接失败 <button style="background:var(--shironeri);color:var(--shu);border:none;padding:4px 12px;cursor:pointer;font-size:12px;font-weight:600" onclick="retryConnection()">重试</button>';
  document.body.prepend(b);
}
function hideOfflineBanner(){
  const b=document.getElementById('offline-banner');if(b)b.remove();
  _offline=false;
}
async function retryConnection(){
  const r=await fetch(`${A}/teams`).catch(()=>null);
  if(r&&r.ok){hideOfflineBanner();loadTeams();toast('连接已恢复','success')}
  else toast('仍然无法连接','error')
}

async function api(p,o){
  try{
    const r=await fetch(p,o);
    if(_offline){hideOfflineBanner()}
    if(!r.ok){
      let msg='';
      try{const d=await r.json();msg=d.detail||d.message||''}catch{}
      console.warn(`API ${r.status}: ${p}`,msg);
      // Attach error info for callers that want it
      const result=null;
      api._lastError={status:r.status,message:msg,url:p};
      return result;
    }
    api._lastError=null;
    return await r.json();
  }catch(e){
    console.error(`API error: ${p}`,e);
    // Network error — show offline banner
    if(e.name==='TypeError'||e.message?.includes('fetch')){
      _offline=true;
      showOfflineBanner();
    }
    api._lastError={status:0,message:e.message,url:p,network:true};
    return null;
  }
}
api._lastError=null;

function stL(s){return{idle:'待命中',working:'工作中',reporting:'汇报中',blocked:'阻塞',error:'异常'}[s]||s||'未知'}
function el(id){return document.getElementById(id)}
function escapeHtml(v){return String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}

// ── Teams ──
async function loadTeams(){
  const d=await api(`${A}/teams`);const s=el('team-select');
  if(!d||!d.length){s.innerHTML='<option>无团队</option>';return}
  s.innerHTML=d.map(t=>`<option value="${escapeHtml(t.team_id)}">${escapeHtml(t.name)}</option>`).join('');
  if(!tid)tid=d[0].team_id;s.value=tid;loadView();
}
el('team-select').onchange=e=>{tid=e.target.value;loadView()};

// ── View switch ──
function switchView(v,extra){
  document.querySelectorAll('.main-inner').forEach(e=>e.classList.add('hidden'));
  document.querySelectorAll('.sb-nav a').forEach(a=>a.classList.toggle('active',a.dataset.view===v));
  document.querySelectorAll('.sb-agent').forEach(a=>a.classList.remove('active'));
  const t=el('main-title'),b=el('main-badge');
  if(v==='overview'){el('view-overview').classList.remove('hidden');t.textContent='团队概览';b.textContent=tid;loadOverview()}
  else if(v==='models'){el('view-models').classList.remove('hidden');t.textContent='模型池';b.textContent='';loadModels()}
  else if(v==='tools'){el('view-tools').classList.remove('hidden');t.textContent='工具管理';b.textContent='';loadTools()}
  else if(v==='skills'){el('view-skills').classList.remove('hidden');t.textContent='技能管理';b.textContent='';loadSkills()}
  else if(v==='tasks'){el('view-tasks').classList.remove('hidden');t.textContent='并发任务';b.textContent='';loadTasks()}
  else if(v==='llm'){
    el('view-llm').classList.remove('hidden');
    t.textContent='LLM 配置';
    b.textContent='';
    // Avoid a transient UI mismatch before async status response arrives.
    syncLLMModelTierFromInput();
    syncLLMModelTierAvailability();
    loadLLMStatus();
    loadTTSConfig();
  }
  else if(v==='sessions'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-sessions').classList.remove('hidden');t.textContent='会话存档';b.textContent='';loadPersistedSessions()}
  else if(v==='runtime'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-runtime').classList.remove('hidden');t.textContent='PortRuntime';b.textContent='claw-code-parity';el('rt-results').classList.add('hidden')}
  else if(v==='registry'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='none';el('agent-content').style.display='none';el('view-registry').classList.remove('hidden');t.textContent='自主 Token 工厂';b.textContent='Token Factory';loadTokenFactory();_startTfPoll()}
  else if(v==='agent'){el('view-agent').classList.remove('hidden');el('agent-tabs').style.display='';el('agent-content').style.display='';loadAgent(extra)}
  else if(v==='wizard'){el('view-wizard').classList.remove('hidden');t.textContent='新建智能体';b.textContent=''}
}
function loadView(){loadSbAgents();
  // ── Darwin rule: bridge-task-dispatch deep-link support ──
  const params = new URLSearchParams(window.location.search);
  const view = params.get('view');
  switchView(view && document.querySelector(`[data-view="${view}"]`) ? view : 'overview');
}

// ── Sidebar agents ──
async function loadSbAgents(){
  const d=await api(`${A}/teams/${tid}`);const c=el('sb-agents');
  if(!d||!d.agents){c.innerHTML='<div style="padding:12px;color:var(--dim);font-size:12px">暂无成员</div>';return}
  const aa=Array.isArray(d.agents)?d.agents:Object.values(d.agents);
  c.innerHTML=aa.map(a=>`<div class="sb-agent${a.agent_id===aid?' active':''}" onclick="selectAgent('${a.agent_id}')"><span class="dot ${a.state||'idle'}"></span><span style="overflow:hidden;text-overflow:ellipsis">${escapeHtml(a.name||a.agent_id)}</span></div>`).join('');
}
function selectAgent(id){aid=id;switchView('agent',id)}

// ── Overview ──
let _ovTimer=null;
async function loadOverview(){
  if(_ovTimer)clearInterval(_ovTimer);
  const teamsList=await api(`${A}/teams`);
  const teamIds=(teamsList||[]).map(t=>t.team_id);
  const[ov,dash,...allTeams]=await Promise.all([
    api(`${AT}/overview`),
    api(`${A}/teams/${tid}/dashboard`),
    ...teamIds.map(id=>api(`${A}/teams/${id}`))
  ]);
  const sc=el('ov-stats');
  const _teamIcons={'build_system':'🏗️','energy_first_principle':'⚡','ai_coding':'💻'};
  if(ov){const sh=ov.scheduler||{};const dt=dash||{};const ev=ov.evolution||{};const evs=ev.stats||{};
  const totalModels=allTeams.reduce((n,t)=>n+(t&&t.models?Object.keys(t.models).length:0),0);
  const totalAgents=allTeams.reduce((n,t)=>n+(t&&t.agents?(Array.isArray(t.agents)?t.agents.length:Object.keys(t.agents).length):0),0);
  const teamCards=allTeams.filter(Boolean).map(t=>{const ac=t.agents?(Array.isArray(t.agents)?t.agents.length:Object.keys(t.agents).length):0;const ic=_teamIcons[t.team_id]||'🤖';return`<div class="stat-card" style="cursor:pointer" onclick="el('team-select').value='${t.team_id}';tid='${t.team_id}';loadView()"><div class="label">${ic} ${escapeHtml(t.name||t.team_id)}</div><div class="value">${ac}</div><div class="sub">${escapeHtml(t.description||'').slice(0,30)}</div></div>`}).join('');
  sc.innerHTML=`<div class="stat-card"><div class="label">📊 调度器</div><div class="value" style="font-size:16px;color:${sh.running?'var(--lime)':'var(--red)'}">${sh.running?'运行中':'已停止'}</div><div class="sub">Tick ${sh.tick_count??0} · 运行 ${Math.round((sh.uptime_seconds||0)/60)}m</div></div>${teamCards}<div class="stat-card"><div class="label">🔄 自我演进</div><div class="value">${ev?.evolution_items_count??'-'}</div><div class="sub">规则 ${ev?.audit_rules_count??0} · 已验证 ${evs?.total_verified??0}</div></div><div class="stat-card"><div class="label">📦 模型</div><div class="value">${totalModels}</div></div><div class="stat-card"><div class="label">🤖 智能体</div><div class="value">${totalAgents}</div></div><div class="stat-card"><div class="label">📋 任务</div><div class="value">${dt.tasks?.total||0}</div><div class="sub">${Object.entries(dt.tasks?.by_status||{}).map(([k,v])=>`${k}: ${v}`).join(' · ')||'无任务'}</div></div>`}
  const curTm=allTeams.find(t=>t&&t.team_id===tid);
  const teamTitle=curTm?curTm.name:tid;
  const teamIcon=_teamIcons[tid]||'🤖';
  el('ov-team-title').textContent=`${teamIcon} ${teamTitle}`;
  const tbody=el('ov-team-agents');tbody.innerHTML='';
  if(curTm&&curTm.agents){
    const aa=Array.isArray(curTm.agents)?curTm.agents:Object.values(curTm.agents);
    aa.forEach(a=>{tbody.innerHTML+=`<tr><td><b>${escapeHtml(a.name||a.agent_id)}</b></td><td style="color:var(--muted)">${escapeHtml(a.role||'-')}</td><td><span class="st st-${a.state||'idle'}">${stL(a.state)}</span></td><td>${(a.skills||[]).slice(0,3).map(s=>'<span class="chip">'+s+'</span>').join('')}</td><td><button class="btn btn-sm btn-ghost" onclick="selectAgent('${a.agent_id}')">查看</button></td></tr>`});
  }
  if(!tbody.innerHTML)tbody.innerHTML='<tr><td colspan="5" style="color:var(--dim)">暂无</td></tr>';
  _ovTimer=setInterval(()=>{if(document.querySelector('#view-overview:not(.hidden)'))loadOverview();else clearInterval(_ovTimer)},10000);
  loadEvolution();
}

// ── System Evolution (自我演进) ──
const EVP='/api/v1/agent-teams/evolution';
async function loadEvolution(){
  const statusFilter=el('evo-filter')?.value||'';
  const itemsUrl=statusFilter?`${EVP}/items?status=${statusFilter}`:`${EVP}/items`;
  const[rules,items,summary,compliance]=await Promise.all([
    api(`${EVP}/rules`),api(itemsUrl),api(`${EVP}/summary`),api(`${EVP}/compliance-rating`)
  ]);
  const rs=el('evo-rules'),is=el('evo-items'),sc=el('evo-stats'),cc=el('evo-compliance');

  // Compliance Rating Card
  if(compliance&&cc){
    const grade=compliance.grade||'?';
    const score=compliance.score??0;
    const gradeColor={A:'var(--lime)',B:'var(--koke)',C:'var(--amber)',D:'var(--kitsune)',E:'var(--red)'}[grade]||'var(--muted)';
    cc.innerHTML=`<div class="stat-card" style="grid-column:span 2"><div style="display:flex;align-items:center;gap:20px"><div style="position:relative;width:64px;height:64px"><svg viewBox="0 0 36 36" style="width:64px;height:64px;transform:rotate(-90deg)"><circle cx="18" cy="18" r="16" fill="none" stroke="var(--groove)" stroke-width="3"/><circle cx="18" cy="18" r="16" fill="none" stroke="${gradeColor}" stroke-width="3" stroke-dasharray="${score} ${100-score}" stroke-linecap="round"/></svg><div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:900;color:${gradeColor};font-family:var(--font-mono)">${grade}</div></div><div><div class="label">合规评级</div><div class="value" style="font-size:18px;color:${gradeColor}">${score}/100</div><div class="sub">${compliance.description||'系统合规状态'}</div></div></div></div>`;
  }

  // Stats
  if(summary){
    const bs=summary.by_status||{};const bd=summary.by_domain||{};
    sc.innerHTML=`<div class="stat-card"><div class="label">📋 规则</div><div class="value">${summary.audit_rules_count||0}</div><div class="sub">验证函数 ${summary.verify_tests_registered||0}</div></div><div class="stat-card"><div class="label">🔍 演进项</div><div class="value">${summary.total_items||0}</div><div class="sub">${Object.entries(bs).map(([k,v])=>evoStL(k)+': '+v).join(' · ')||'无'}</div></div><div class="stat-card"><div class="label">📚 域分布</div><div class="value" style="font-size:13px">${Object.entries(bd).map(([k,v])=>k+' '+v).join(' · ')||'-'}</div></div>`;
  }

  // Active Zones
  loadEvoZones();

  // Rules — filter by selected team
  const isEnergy=(tid==='energy_first_principle');
  const filteredRules=(rules||[]).filter(r=>isEnergy?r.domain==='Datacenter':r.domain!=='Datacenter');
  if(filteredRules.length){
    rs.innerHTML=`<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--muted)">审查规则 (${filteredRules.length})</div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px">${filteredRules.map(r=>`<div style="padding:10px 14px;background:var(--panel2);border:1px solid var(--line);border-radius:0"><div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:12px">${escapeHtml(r.id)}</b><span class="chip" style="font-size:10px">${escapeHtml(r.domain)}</span></div><div style="font-size:12px;margin-top:4px;color:var(--text)">${escapeHtml(r.title)}</div><div style="font-size:11px;color:var(--dim);margin-top:2px">${escapeHtml(r.reference||'')}</div><div style="font-size:11px;margin-top:2px"><span style="color:${r.severity==='critical'?'var(--red)':r.severity==='high'?'var(--amber)':'var(--muted)'}">${escapeHtml(r.severity)}</span> · ${escapeHtml(r.target_channel)}</div></div>`).join('')}</div>`;
  } else { rs.innerHTML='<div style="color:var(--dim);font-size:12px">暂无审查规则</div>'; }

  // Items with action buttons
  if(items&&items.length){
    const maxItems=50;const shown=items.slice(0,maxItems);
    is.innerHTML=`<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--muted)">演进条目 (${items.length}${items.length>maxItems?' · 显示前'+maxItems+'条':''})</div><table class="tbl"><thead><tr><th>ID</th><th>标题</th><th>域</th><th>严重度</th><th>状态</th><th>目标</th><th>操作</th></tr></thead><tbody>${shown.map(i=>`<tr><td style="font-family:var(--font-mono);font-size:11px">${escapeHtml(i.id?.slice(0,8)||'')}</td><td><b>${escapeHtml(i.title)}</b></td><td><span class="chip" style="font-size:10px">${escapeHtml(i.audit_domain||'')}</span></td><td style="color:${i.severity==='critical'?'var(--red)':i.severity==='high'?'var(--amber)':'var(--muted)'}">${escapeHtml(i.severity||'')}</td><td>${evoStBadge(i.status)}</td><td style="font-size:12px">${escapeHtml(i.target_channel||'')}</td><td style="white-space:nowrap">${evoItemActions(i)}</td></tr>`).join('')}</tbody></table>${items.length>maxItems?`<button class="btn btn-sm" style="margin-top:8px" onclick="toast('TODO: 加载更多')">加载更多 (${items.length-maxItems} 剩余)</button>`:''}`;
  } else { is.innerHTML='<div style="color:var(--dim);font-size:12px;padding:8px">暂无演进条目 — 点击「审查」或「运行演进周期」开始</div>'; }
}

function evoItemActions(item){
  const s=item.status;
  if(s==='discovered')return `<button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="evoMarkProgress('${item.id}')">开始</button>`;
  if(s==='in_progress')return `<button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="evoMarkComplete('${item.id}')">完成</button>`;
  if(s==='verify_pending')return `<span style="font-size:11px;color:var(--amber)">待验证</span>`;
  if(s==='verified')return `<span style="font-size:11px;color:var(--lime)">✓</span>`;
  if(s==='failed')return `<span style="font-size:11px;color:var(--red)">✗</span>`;
  return '—';
}

async function evoMarkProgress(itemId){
  const r=await api(`${EVP}/items/${itemId}/progress`,{method:'POST'});
  if(r){toast('已标记为进行中');loadEvolution()}else toast('操作失败')
}
async function evoMarkComplete(itemId){
  const r=await api(`${EVP}/items/${itemId}/complete`,{method:'POST'});
  if(r){toast('已标记完成，等待验证');loadEvolution()}else toast('操作失败')
}

async function loadEvoZones(){
  const zc=el('evo-zones');if(!zc)return;
  const zones=await api(`${EVP}/zones/active`);
  if(!zones||!zones.length){zc.innerHTML='';return}
  zc.innerHTML=`<div style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--muted)">活跃合规区域</div><div style="display:flex;gap:8px;flex-wrap:wrap">${zones.map(z=>`<div class="chip" style="padding:6px 12px"><b>${escapeHtml(z.name||z.zone_id||'')}</b>${z.standards?` · ${z.standards.length} 标准`:''}</div>`).join('')}</div>`;
}

function evoStL(s){return{discovered:'发现',dispatched:'已派发',in_progress:'进行中',verify_pending:'待验证',verified:'已验证',failed:'失败',closed:'已关闭'}[s]||s}
function evoStBadge(s){const c={discovered:'var(--cyan)',dispatched:'var(--amber)',in_progress:'var(--cyan-s)',verify_pending:'var(--pink)',verified:'var(--lime)',failed:'var(--red)',closed:'var(--dim)'}[s]||'var(--muted)';return `<span style="color:${c};font-weight:600;font-size:12px">${evoStL(s)}</span>`}

async function runEvoAudit(){
  toast('正在运行审查...');
  const r=await api(`${EVP}/audit`,{method:'POST'});
  if(r){toast(`审查完成: ${r.passed||0} 通过, ${r.failed||0} 未通过`);loadEvolution()}else toast('审查失败')
}

// Evolution Cycle Stepper — visual 4-step progress
async function runEvoCycleStepper(){
  const stepper=el('evo-stepper');const log=el('evo-stepper-log');
  stepper.classList.remove('hidden');
  const steps=['audit','dispatch','verify','close'];
  const stepNames=['审查','派发','验证','关闭'];
  // Reset all dots
  steps.forEach(s=>{const d=el('es-'+s);d.className='wf-dot'});
  ['es-c1','es-c2','es-c3'].forEach(id=>{const c=el(id);if(c)c.className='wf-connector'});
  log.innerHTML='';

  for(let i=0;i<steps.length;i++){
    const dotEl=el('es-'+steps[i]);
    dotEl.classList.add('wf-active');
    log.innerHTML+=`<div>⏳ ${stepNames[i]}...</div>`;
    const r=await api(`${EVP}/${steps[i]}`,{method:'POST'});
    dotEl.classList.remove('wf-active');
    if(r){
      dotEl.classList.add('wf-completed');
      const count=r.count||r.passed||r.dispatched||(r.closed||[]).length||0;
      log.innerHTML+=`<div style="color:var(--lime)">✓ ${stepNames[i]}完成 (${count})</div>`;
    }else{
      dotEl.classList.add('wf-failed');
      log.innerHTML+=`<div style="color:var(--red)">✗ ${stepNames[i]}失败</div>`;
      break;
    }
    // Mark connector as done
    if(i<3){const c=el('es-c'+(i+1));if(c)c.classList.add('wf-done')}
  }
  toast('演进周期完成');
  loadEvolution();
}

// Keep backward compat
async function runEvoCycle(){runEvoCycleStepper()}

// ── LLM Config ──
function _isDeepseekTierModel(model){
  return model==='deepseek-v4-pro'||model==='deepseek-v4-flash';
}
function _deepseekTierModel(isPro){
  return isPro?'deepseek-v4-pro':'deepseek-v4-flash';
}
function _renderLLMModelTierToggle(){
  const tg=el('llm-model-tier');
  const flashBtn=el('llm-tier-flash');
  const proBtn=el('llm-tier-pro');
  if(!tg)return;

  const activeBg='rgba(152,245,167,0.18)';
  const activeColor='var(--text)';
  const inactiveBg='transparent';
  const inactiveColor='var(--dim)';

  if(flashBtn&&proBtn){
    if(tg.checked){
      proBtn.style.background=activeBg;
      proBtn.style.color=activeColor;
      flashBtn.style.background=inactiveBg;
      flashBtn.style.color=inactiveColor;
      flashBtn.style.fontWeight='400';
      proBtn.style.fontWeight='600';
    }else{
      flashBtn.style.background=activeBg;
      flashBtn.style.color=activeColor;
      proBtn.style.background=inactiveBg;
      proBtn.style.color=inactiveColor;
      proBtn.style.fontWeight='400';
      flashBtn.style.fontWeight='600';
    }
  }
}
function syncLLMModelTierAvailability(){
  const provider=el('llm-provider')?.value||'';
  const wrap=el('llm-model-tier-wrap');
  const tg=el('llm-model-tier');
  if(!wrap||!tg)return;
  const enabled=provider==='deepseek';
  tg.disabled=!enabled;
  wrap.style.opacity=enabled?'1':'0.45';
  wrap.style.pointerEvents=enabled?'auto':'none';
  _renderLLMModelTierToggle();
}
function syncLLMModelTierFromInput(){
  const model=(el('llm-model')?.value||'').trim();
  const tg=el('llm-model-tier');
  if(!tg)return;
  if(model==='deepseek-v4-pro')tg.checked=true;
  else if(model==='deepseek-v4-flash')tg.checked=false;
  _renderLLMModelTierToggle();
}
function onLLMModelTierToggle(isPro){
  const provider=el('llm-provider')?.value||'';
  _renderLLMModelTierToggle();
  if(provider!=='deepseek')return;
  const modelInput=el('llm-model');
  if(modelInput)modelInput.value=_deepseekTierModel(isPro);
}
function setLLMModelTier(isPro){
  const tg=el('llm-model-tier');
  if(!tg||tg.disabled)return;
  tg.checked=!!isPro;
  onLLMModelTierToggle(tg.checked);
}
function toggleLLMModelTier(){
  const tg=el('llm-model-tier');
  if(!tg||tg.disabled)return;
  tg.checked=!tg.checked;
  onLLMModelTierToggle(tg.checked);
}

async function loadLLMStatus(){
  const st=await api(`${A}/llm/status`);
  const prov=await api(`${A}/llm/provider`);
  const card=el('llm-status-card');
  if(!st||!prov){card.innerHTML='<p style="color:var(--pink)">⚠️ 无法获取 LLM 状态，请确认后端已启动</p>';return}
  const keyStatus=prov.has_api_key?'<span style="color:var(--lime)">✅ 已配置</span>':'<span style="color:var(--pink)">❌ 未配置</span>';
  card.innerHTML=`
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px">
      <div class="stat-card"><div class="label">提供商</div><div class="value">${escapeHtml(prov.provider)}</div></div>
      <div class="stat-card"><div class="label">模型</div><div class="value" style="font-size:14px">${escapeHtml(prov.model)}</div></div>
      <div class="stat-card"><div class="label">API Key</div><div class="value" style="font-size:14px">${keyStatus}</div><div class="sub">${prov.api_key_preview||''}</div></div>
      <div class="stat-card"><div class="label">Base URL</div><div class="value" style="font-size:11px;word-break:break-all">${escapeHtml(prov.base_url)}</div></div>
      <div class="stat-card"><div class="label">总调用</div><div class="value">${st.total_calls??0}</div></div>
      <div class="stat-card"><div class="label">总 Tokens</div><div class="value">${(st.total_tokens||0).toLocaleString()}</div></div>
      <div class="stat-card"><div class="label">活跃会话</div><div class="value">${st.active_sessions??0}</div></div>
      <div class="stat-card"><div class="label">错误数</div><div class="value" style="color:${(st.errors||0)>0?'var(--pink)':'var(--lime)'}">${st.errors??0}</div></div>
    </div>`;
  // Fill form with current values
  el('llm-provider').value=prov.provider||'deepseek';
  el('llm-model').value=prov.model||'';
  el('llm-url').value=prov.base_url||'';
  el('llm-tokens').value=prov.max_tokens||4096;
  el('llm-temp').value=prov.temperature||0.7;
  syncLLMModelTierFromInput();
  syncLLMModelTierAvailability();
  // Load sessions
  const sessions=await api(`${A}/llm/sessions`);
  const sc=el('llm-sessions');
  if(!sessions||!sessions.length){sc.innerHTML='<p style="color:var(--dim)">暂无活跃会话</p>';return}
  sc.innerHTML='<table class="tbl"><thead><tr><th>会话 ID</th><th>Agent</th><th>轮次</th><th>消息数</th><th>Tokens</th><th>创建时间</th></tr></thead><tbody>'+sessions.map(s=>`<tr><td>${escapeHtml(s.session_id)}</td><td>${escapeHtml(s.agent_id||'-')}</td><td>${s.turn_count}</td><td>${s.message_count}</td><td>${(s.usage?.total_tokens||0).toLocaleString()}</td><td>${s.created_at?.split('T')[0]||'-'}</td></tr>`).join('')+'</tbody></table>';
}
async function saveLLMConfig(){
  const provider=el('llm-provider').value;
  let model=(el('llm-model').value||'').trim();
  if(provider==='deepseek'&&(!model||_isDeepseekTierModel(model))){
    model=_deepseekTierModel(!!el('llm-model-tier')?.checked);
    el('llm-model').value=model;
  }
  const body={provider,model,api_key:el('llm-key').value,api_base_url:el('llm-url').value,max_tokens:parseInt(el('llm-tokens').value)||4096,temperature:parseFloat(el('llm-temp').value)||0.7};
  const r=await api(`${A}/llm/provider`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r){toast('LLM 配置已保存');el('llm-key').value='';loadLLMStatus()}else toast('保存失败')
}
async function testLLM(){
  const rc=el('llm-test-result');rc.classList.remove('hidden');
  el('llm-test-content').innerHTML='<p style="color:var(--dim)">正在测试连接...</p>';
  const r=await api(`${A}/llm/test`,{method:'POST'});
  if(!r){el('llm-test-content').innerHTML='<p style="color:var(--pink)">请求失败，请检查后端</p>';return}
  if(r.success){
    el('llm-test-content').innerHTML=`<div style="color:var(--lime);margin-bottom:8px">✅ 连接成功！</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><div><b>模型:</b> ${escapeHtml(r.model)}</div><div><b>提供商:</b> ${escapeHtml(r.provider)}</div><div><b>延迟:</b> ${r.latency_ms.toFixed(0)}ms</div></div><div style="margin-top:12px;padding:12px;background:rgba(232,240,250,0.7);border-radius:0;font-size:13px;color:var(--text)">${escapeHtml(r.response)}</div>`;
  } else {
    el('llm-test-content').innerHTML=`<div style="color:var(--pink);margin-bottom:8px">❌ 连接失败</div><div style="padding:12px;background:rgba(224,27,36,0.06);border-radius:0;font-size:12px;color:var(--red);word-break:break-all">${escapeHtml(r.error||'未知错误')}</div><div style="margin-top:12px;padding:12px;background:rgba(232,240,250,0.7);border-radius:0;font-size:13px;color:var(--text)">${escapeHtml(r.response)}</div><div style="margin-top:12px;color:var(--muted);font-size:12px">💡 提示: 请确认 API Key 已正确填入，或检查本地模型服务是否运行中</div>`;
  }
}

// ── Models ──
let _editModelId='';
async function loadModels(){const d=await api(`${A}/teams/${tid}/models`);const tb=el('models-tb');if(!d||!d.length){tb.innerHTML='<tr><td colspan="7" style="color:var(--dim)">暂无模型 — 点击右上角「+ 添加模型」</td></tr>';return}tb.innerHTML=d.map(m=>{const mid=m.model_id;return `<tr><td><b>${escapeHtml(mid)}</b></td><td>${escapeHtml(m.name)}</td><td>${escapeHtml(m.provider)}</td><td>${m.max_tokens.toLocaleString()}</td><td>${m.temperature}</td><td>${m.is_default?'<span style="color:var(--lime)">✓ 默认</span>':`<button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="setModelDefault('${mid}')">设为默认</button>`}</td><td style="display:flex;gap:6px"><button class="btn btn-sm" style="padding:2px 8px;font-size:11px" onclick="openEditModel('${mid}')">编辑</button><button class="btn btn-danger btn-sm" onclick="delModel('${mid}')">删除</button></td></tr>`}).join('')}
async function delModel(mid){if(!confirm('删除此模型？'))return;await fetch(`${A}/teams/${tid}/models/${mid}`,{method:'DELETE'});toast('已删除');loadModels()}
async function setModelDefault(mid){
  const r=await api(`${A}/teams/${tid}/models/${mid}/default`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});
  if(r){toast(`模型 ${mid} 已设为默认，所有智能体已同步`);loadModels();loadSbAgents();if(aid)loadAgent()}else toast('设置失败')
}
async function openEditModel(mid){
  _editModelId=mid;
  const models=await api(`${A}/teams/${tid}/models`);
  const m=(models||[]).find(x=>x.model_id===mid);if(!m){toast('模型未找到');return}
  el('em-prov').value=m.provider||'deepseek';
  el('em-name').value=m.name||'';
  el('em-tok').value=m.max_tokens||8192;
  el('em-temp').value=m.temperature??0.7;
  el('em-key').value='';
  el('em-url').value=m.api_base_url||'';
  el('em-def').value=m.is_default?'true':'false';
  el('em-title').textContent=`✏️ 编辑模型 — ${mid}`;
  el('em-test-result').classList.add('hidden');
  updateEmUrlHint();
  openModal('modal-edit-model');
}
const _providerDefaultUrls={deepseek:'https://api.deepseek.com',openai:'https://api.openai.com/v1',anthropic:'https://api.anthropic.com/v1',github:'https://models.inference.ai.azure.com',qwen:'https://dashscope.aliyuncs.com/compatible-mode/v1',openrouter:'https://openrouter.ai/api/v1',local:'http://127.0.0.1:11434/v1'};
function updateEmUrlHint(){
  const prov=el('em-prov').value;
  const defaultUrl=_providerDefaultUrls[prov]||'';
  const urlInput=el('em-url');
  urlInput.placeholder=defaultUrl||'输入自定义 Base URL';
  const hint=el('em-url-hint');
  if(hint){
    if(urlInput.value){hint.textContent=`自定义 URL（默认: ${defaultUrl}）`}
    else{hint.textContent=`当前使用默认: ${defaultUrl}`}
  }
}
async function submitEditModel(){
  if(!_editModelId)return;
  const body={provider:el('em-prov').value,name:el('em-name').value.trim(),max_tokens:parseInt(el('em-tok').value)||8192,temperature:parseFloat(el('em-temp').value)||0.7,is_default:el('em-def').value==='true',api_key:el('em-key').value,api_base_url:el('em-url').value};
  if(!body.name){toast('模型名称不能为空');return}
  const r=await api(`${A}/teams/${tid}/models/${_editModelId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r){toast('模型已更新');closeModal('modal-edit-model');loadModels();if(body.is_default){loadSbAgents();if(aid)loadAgent()}}else toast('更新失败')
}
async function testModelInEdit(){
  const rb=el('em-test-result');rb.classList.remove('hidden');
  rb.style.background='rgba(232,240,250,0.7)';rb.style.color='var(--muted)';
  rb.innerHTML='⏳ 正在测试连接...';
  const btn=el('em-test-btn');btn.disabled=true;
  const body={provider:el('em-prov').value,name:el('em-name').value.trim(),api_key:el('em-key').value,api_base_url:el('em-url').value,max_tokens:parseInt(el('em-tok').value)||8192,temperature:parseFloat(el('em-temp').value)||0.7};
  const r=await api(`${A}/llm/test-model`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  btn.disabled=false;
  if(!r){rb.style.background='rgba(224,27,36,0.06)';rb.style.color='var(--red)';rb.innerHTML='❌ 请求失败，请检查后端是否运行';return}
  if(r.success){
    rb.style.background='rgba(38,162,105,0.08)';rb.style.color='var(--lime)';
    rb.innerHTML=`✅ 连接成功 — 模型: ${escapeHtml(r.model)} · 延迟: ${r.latency_ms.toFixed(0)}ms<div style="margin-top:8px;padding:10px;background:rgba(232,240,250,0.6);border-radiu