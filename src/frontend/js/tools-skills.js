/**
 * AgentsGroup2026 — Tools & Skills Views
 * Manages tool listing, enable/disable, execution, editing,
 * and skill listing, configuration, and editing.
 * Extracted from agent-team-config.js for modularity.
 * Depends on: utils.js, api.js, agent-team-config.js (parent scope)
 */
(function(){
'use strict';
let _tcToolId='';
function asItems(payload){return Array.isArray(payload)?payload:Array.isArray(payload&&payload.items)?payload.items:[]}
async function loadTools(){hideViewLoading('view-tools');
  const[all,team]=await Promise.all([api(`${A}/tools`),api(`${A}/teams/${tid}/tools`)]);
  const en=new Set((team||[]).filter(t=>t.enabled!==false).map(t=>t.tool_id||t.id));const box=el('tools-cards');
  if(!all||!all.length){box.innerHTML='<p style="color:var(--dim)">暂无工具</p>';return}
  const cats={};all.forEach(t=>{const c=(t.category||'general').toUpperCase();if(!cats[c])cats[c]=[];cats[c].push(t)});
  let html='';Object.keys(cats).sort().forEach(cat=>{
    html+=`<div class="sb-section" style="margin-top:16px;margin-bottom:10px">${cat}</div>`;
    cats[cat].forEach(t=>{const on=en.has(t.tool_id);const hasCfg=t.config_schema&&Object.keys(t.config_schema).length;
      html+=`<div data-tool-name="${t.name}" style="display:flex;align-items:center;padding:14px 18px;background:var(--panel2,#21272D);border:1px solid var(--line);border-radius:0;margin-bottom:6px;gap:12px"><span style="font-size:22px;width:36px;text-align:center">${t.icon||'🔧'}</span><div style="flex:1;min-width:0"><div style="display:flex;align-items:center;gap:8px;margin-bottom:2px"><b style="font-size:13px;color:var(--text)">${t.name}</b><span class="chip" style="font-size:10px;padding:1px 6px">${t.source||'Built-in'}</span>${t.is_default?'<span class="chip" style="background:rgba(38,162,105,0.1);color:var(--lime);font-size:10px;padding:1px 6px">Default</span>':''}</div><div style="color:var(--muted);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(t.description||'')}</div></div><div style="display:flex;align-items:center;gap:8px"><button class="btn btn-sm btn-ghost" onclick="testToolExec('${t.name}')" title="测试执行">▶</button>${hasCfg?`<button class="btn btn-sm btn-ghost" onclick="openToolConfig('${t.tool_id}')">配置</button>`:''}<button class="btn btn-sm btn-ghost" onclick="openEditTool('${escapeHtml(t.tool_id)}')" title="编辑">✏️</button><button class="btn btn-sm btn-ghost" onclick="deleteTool('${escapeHtml(t.tool_id)}','${t.name}')" title="删除" style="color:var(--pink)">🗑️</button><label style="position:relative;display:inline-block;width:44px;height:24px;cursor:pointer"><input type="checkbox" role="switch" ${on?'checked':''} onchange="togTool('${escapeHtml(t.tool_id)}',this.checked)" style="opacity:0;width:0;height:0"><span style="position:absolute;inset:0;background:${on?'var(--pink)':'var(--dim)'};border-radius:0;transition:.3s"></span><span style="position:absolute;top:2px;left:${on?'22px':'2px'};width:20px;height:20px;background:oklch(0.96 0.003 110);border-radius:50%;transition:.3s"></span></label></div></div>`})});
  box.innerHTML=html;
}
async function togTool(id,en){
  const r=await api(`${A}/teams/${tid}/tools/${id}/${en?'enable':'disable'}`,{method:'POST'});
  if(r){toast(en?'已启用':'已禁用')}else{toast(en?'启用失败':'禁用失败 — 请刷新重试')}
  loadTools()
}
async function testToolExec(toolName){
  toast(`正在执行 ${toolName}...`);
  const args={};
  if(toolName==='web_search')args.query='AgentsGroup2026 maritime system';
  else if(toolName==='engine_status')args.engine_id='main';
  else if(toolName==='ais_query')args.mmsi='';
  else if(toolName==='weather_fetch'){args.lat=31.2;args.lon=121.5}
  else if(toolName==='cargo_status')args.hold_id='all';
  else if(toolName==='list_directory')args.path='.';
  else if(toolName==='run_python')args.code='print("Hello from AgentsGroup2026!")';
  else if(toolName==='colregs_check'){args.own_vessel={};args.target_vessel={}}
  else if(toolName==='route_calculate'){args.origin={lat:31.2,lon:121.5};args.destination={lat:22.3,lon:114.2}}
  const r=await api(`${A}/tools/${toolName}/execute`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({arguments:args})}).catch(()=>null);
  if(r&&r.success){toast(`✅ ${toolName} 执行成功`);alert(`工具: ${toolName}\n\n${r.output||'(无输出)'}`)}
  else if(r){toast(`❌ ${toolName} 执行失败`);alert(`工具: ${toolName}\n\n错误: ${r.error||'未知错误'}`)}
  else toast('执行请求失败')
}
function openToolConfig(toolId){_tcToolId=toolId;api(`${A}/tools`).then(all=>{const t=(all||[]).find(x=>x.tool_id===toolId);if(!t){toast('工具未找到');return}el('tc-title').textContent=`${t.icon||'🔧'} ${t.name} 配置`;const sch=t.config_schema||{};const cfg=t.config||{};let html='';Object.keys(sch).forEach(k=>{const s=sch[k];const v=cfg[k]??s.default??'';html+=`<div class="form-group"><label class="form-label">${k} <span style="color:var(--dim);font-size:11px">${escapeHtml(s.description||"")}</span></label>${s.type==='boolean'?`<select class="fi" id="tc-${k}"><option value="true"${v?'selected':''}>是</option><option value="false"${!v?' selected':''}>否</option></select>`:`<input class="fi" id="tc-${k}" value="${Array.isArray(v)?v.join(', '):v}" placeholder="${s.default||''}">`}</div>`});if(!html)html='<p style="color:var(--dim)">此工具暂无可配置项</p>';el('tc-form').innerHTML=html;openModal('modal-tool-config')})}
async function saveToolConfig(){
  if(!_tcToolId){toast('无工具选中');return}
  const inputs=el('tc-form').querySelectorAll('[id^="tc-"]');
  const config={};inputs.forEach(inp=>{const k=inp.id.replace('tc-','');config[k]=inp.tagName==='SELECT'?inp.value==='true':inp.value});
  const r=await api(`${A}/tools/${_tcToolId}/config`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({config})});
  if(r){toast('配置已保存');closeModal('modal-tool-config')}else toast('保存失败')
}

// ── Tool Edit / Delete ──
async function openEditTool(toolId){
  const all=await api(`${A}/tools`);const t=(all||[]).find(x=>x.tool_id===toolId);
  if(!t){toast('工具未找到');return}
  const html=`<div class="modal-overlay open" id="modal-edit-tool" onclick="if(event.target===this)this.remove()"><div class="modal"><h3>✏️ 编辑工具: ${escapeHtml(t.name)}</h3><div class="form-group"><label class="form-label">名称</label><input class="fi" id="et-name" value="${escapeHtml(t.name)}"></div><div class="form-group"><label class="form-label">描述</label><textarea class="fi" id="et-desc" rows="3">${escapeHtml(t.description||'')}</textarea></div><div class="form-group"><label class="form-label">图标</label><input class="fi" id="et-icon" value="${t.icon||'🔧'}" style="width:60px"></div><div class="form-group"><label class="form-label">需要审批</label><select class="fi" id="et-approval"><option value="false"${!t.requires_approval?' selected':''}>否</option><option value="true"${t.requires_approval?' selected':''}>是</option></select></div><div class="modal-actions"><button class="btn" onclick="document.getElementById('modal-edit-tool').remove()">取消</button><button class="btn btn-pink" onclick="submitEditTool('${toolId}')">保存</button></div></div></div>`;
  document.body.insertAdjacentHTML('beforeend',html);
}
async function submitEditTool(toolId){
  const data={name:el('et-name').value.trim(),description:el('et-desc').value.trim(),icon:el('et-icon').value.trim(),requires_approval:el('et-approval').value==='true'};
  const r=await api(`${A}/teams/${tid}/tools/${toolId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  if(r){toast('✅ 工具已更新');const m=document.getElementById('modal-edit-tool');if(m)m.remove();loadTools()}else toast('更新失败')
}
async function deleteTool(toolId,toolName){
  if(!confirm(`确认删除工具「${toolName}」？此操作不可撤销。`))return;
  const r=await api(`${A}/teams/${tid}/tools/${toolId}`,{method:'DELETE'});
  if(r){toast('✅ 工具已删除');loadTools()}else toast('删除失败')
}

// ── Skill Edit / Delete ──
async function openEditSkill(skillId){
  const teamSkills=asItems(await api(`${A}/teams/${tid}/skills`));const s=teamSkills.find(x=>x.skill_id===skillId);
  if(!s){toast('技能未找到');return}
  // Fetch full instructions
  let instructions='';
  if(s.has_instructions){const r=await api(`${A}/skills/${skillId}/instructions`);if(r)instructions=r.instructions||''}
  const html=`<div class="modal-overlay open" id="modal-edit-skill" onclick="if(event.target===this)this.remove()"><div class="modal"><h3>✏️ 编辑技能: ${escapeHtml(s.name)}</h3><div class="form-group"><label class="form-label">名称</label><input class="fi" id="es-name" value="${escapeHtml(s.name)}"></div><div class="form-group"><label class="form-label">描述</label><textarea class="fi" id="es-desc" rows="3">${escapeHtml(s.description||'')}</textarea></div><div class="form-group"><label class="form-label">图标</label><input class="fi" id="es-icon" value="${s.icon||'⚡'}" style="width:60px"></div><div class="form-group"><label class="form-label">类别</label><select class="fi" id="es-cat"><option value="general"${s.category==='general'?' selected':''}>通用</option><option value="maritime"${s.category==='maritime'?' selected':''}>海事</option><option value="coding"${s.category==='coding'?' selected':''}>编程</option><option value="analysis"${s.category==='analysis'?' selected':''}>分析</option><option value="research"${s.category==='research'?' selected':''}>研究</option><option value="communication"${s.category==='communication'?' selected':''}>沟通</option></select></div><div class="form-group"><label class="form-label">Slug</label><input class="fi" id="es-slug" value="${escapeHtml(s.slug||'')}"></div><div class="form-group"><label class="form-label">指令 (Instructions)</label><textarea class="fi" id="es-instructions" rows="6" style="font-family:monospace;font-size:12px">${escapeHtml(instructions)}</textarea></div><div class="modal-actions"><button class="btn" onclick="document.getElementById('modal-edit-skill').remove()">取消</button><button class="btn btn-pink" onclick="submitEditSkill('${skillId}')">保存</button></div></div></div>`;
  document.body.insertAdjacentHTML('beforeend',html);
}
async function submitEditSkill(skillId){
  const data={name:el('es-name').value.trim(),description:el('es-desc').value.trim(),icon:el('es-icon').value.trim(),category:el('es-cat').value,slug:el('es-slug').value.trim(),instructions:el('es-instructions').value};
  const r=await api(`${A}/teams/${tid}/skills/${skillId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  if(r){toast('✅ 技能已更新');const m=document.getElementById('modal-edit-skill');if(m)m.remove();loadSkills()}else toast('更新失败')
}
async function deleteSkill(skillId,skillName){
  if(!confirm(`确认删除技能「${skillName}」？此操作不可撤销。`))return;
  const r=await api(`${A}/teams/${tid}/skills/${skillId}`,{method:'DELETE'});
  if(r){toast('✅ 技能已删除');if(typeof loadAgent==='function'&&window.aid)loadAgent();loadSkills()}else toast('删除失败')
}

// ── Skills (Clawith-style) ──
async function loadSkills(){hideViewLoading('view-skills');
  const teamSkills=asItems(await api(`${A}/teams/${tid}/skills`));const box=el('skills-cards');
  let html='<div style="display:flex;gap:8px;margin-bottom:16px"><button class="btn btn-sm btn-pink" onclick="openGenerateSkillModal()">⚡ 生成技能</button><button class="btn btn-sm" onclick="importSkillFromFile()">📥 导入技能</button><button class="btn btn-sm" onclick="exportSkillsMD()">📤 导出全部</button></div>';
  if(!teamSkills.length){box.innerHTML=html+'<p style="color:var(--dim)">当前团队暂无技能</p>';return}
  const cats={};teamSkills.forEach(s=>{const c=(s.category||'general').toUpperCase();if(!cats[c])cats[c]=[];cats[c].push(s)});
  Object.keys(cats).sort().forEach(cat=>{
    html+=`<div class="sb-section" style="margin-top:16px;margin-bottom:10px">${cat}</div>`;
    cats[cat].forEach(s=>{const on=s.enabled!==false;const hasCfg=s.config_schema&&Object.keys(s.config_schema).length;
      html+=`<div style="display:flex;align-items:center;padding:14px 18px;background:var(--panel2,#21272D);border:1px solid var(--line);border-radius:0;margin-bottom:6px;gap:12px"><span style="font-size:22px;width:36px;text-align:center">${s.icon||'⚡'}</span><div style="flex:1;min-width:0"><div style="display:flex;align-items:center;gap:8px;margin-bottom:2px"><b style="font-size:13px;color:var(--text)">${s.name}</b><span class="chip" style="font-size:10px;padding:1px 6px">${s.source||'Built-in'}</span>${s.is_default?'<span class="chip" style="background:rgba(38,162,105,0.1);color:var(--lime);font-size:10px;padding:1px 6px">Default</span>':''}${s.slug?`<span class="chip" style="font-size:10px;padding:1px 6px">${s.slug}</span>`:''}</div><div style="color:var(--muted);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(s.description||'')}</div></div><div style="display:flex;align-items:center;gap:8px">${hasCfg?`<button class="btn btn-sm btn-ghost" onclick="openSkillConfig('${s.name}')" title="配置" style="color:var(--pink)">⚙️</button>`:''}<button class="btn btn-sm btn-ghost" onclick="testSkillExec('${s.name}')" title="测试执行">▶</button>${s.has_instructions?`<button class="btn btn-sm btn-ghost" onclick="viewSkillInstructions('${escapeHtml(s.skill_id)}')" title="查看指令">📖</button>`:''}<button class="btn btn-sm btn-ghost" onclick="openEditSkill('${s.skill_id}')" title="编辑">✏️</button><button class="btn btn-sm btn-ghost" onclick="deleteSkill('${s.skill_id}','${s.name}')" title="删除" style="color:var(--pink)">🗑️</button><button class="btn btn-sm btn-ghost" onclick="viewSkillPortability('${s.skill_id}')" title="可移植性">🏷</button><button class="btn btn-sm btn-ghost" onclick="viewSkillFolder('${s.skill_id}')" title="文件结构">📁</button><label style="position:relative;display:inline-block;width:44px;height:24px;cursor:pointer"><input type="checkbox" role="switch" ${on?'checked':''} onchange="togSkill('${s.skill_id}',this.checked)" style="opacity:0;width:0;height:0"><span style="position:absolute;inset:0;background:${on?'var(--pink)':'var(--dim)'};border-radius:0;transition:.3s"></span><span style="position:absolute;top:2px;left:${on?'22px':'2px'};width:20px;height:20px;background:oklch(0.96 0.003 110);border-radius:50%;transition:.3s"></span></label></div></div>`})});
  box.innerHTML=html;
}
async function togSkill(id,en){await api(`${A}/teams/${tid}/skills/${id}/${en?'enable':'disable'}`,{method:'POST'});toast(en?'已启用':'已禁用');loadSkills()}
function openGenerateSkillModal(){
  const html=`<div class="modal-overlay open" id="modal-gen-skill" onclick="if(event.target===this)this.remove()"><div class="modal"><h3>⚡ 生成新技能</h3><div class="form-group"><label class="form-label">技能名称 <span class="req">*</span></label><input class="fi" id="gs-name" placeholder="例: maritime_weather_analysis"></div><div class="form-group"><label class="form-label">描述</label><textarea class="fi" id="gs-desc" placeholder="技能用途描述"></textarea></div><div class="form-group"><label class="form-label">类别</label><select class="fi" id="gs-cat"><option value="general">通用</option><option value="maritime">海事</option><option value="coding">编程</option><option value="analysis">分析</option></select></div><div class="form-group"><label class="form-label">触发词 (逗号分隔)</label><input class="fi" id="gs-triggers" placeholder="天气分析, 气象, weather"></div><div class="modal-actions"><button class="btn" onclick="document.getElementById('modal-gen-skill').remove()">取消</button><button class="btn btn-pink" onclick="submitGenerateSkill()">生成</button></div></div></div>`;
  document.body.insertAdjacentHTML('beforeend',html);
}
async function submitGenerateSkill(){
  const name=el('gs-name').value.trim();if(!name){toast('请输入技能名称');return}
  const r=await api(`${A}/skills`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,description:el('gs-desc').value.trim(),category:el('gs-cat').value,triggers:(el('gs-triggers').value||'').split(',').map(s=>s.trim()).filter(Boolean)})});
  if(r){toast('✅ 技能已生成');const m=document.getElementById('modal-gen-skill');if(m)m.remove();loadSkills()}else{toast('❌ 生成失败，请检查后端')}
}
function importSkillFromFile(){
  const inp=document.createElement('input');inp.type='file';inp.accept='.json,.md';
  inp.onchange=async(e)=>{const f=e.target.files[0];if(!f)return;const text=await f.text();
    try{
      let data;
      if(f.name.endsWith('.json')){data=JSON.parse(text)}
      else{data={name:f.name.replace(/\.(md|json)$/,''),instructions:text,category:'general'}}
      const r=await api(`${A}/skills`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
      if(r){toast('✅ 技能导入成功');loadSkills()}else{toast('❌ 导入失败')}
    }catch(err){toast('文件解析失败: '+err.message)}
  };inp.click();
}
async function viewSkillInstructions(skillId){
  const r=await api(`${A}/skills/${skillId}/instructions`);
  if(!r){toast('获取失败');return}
  const inst=r.instructions||'暂无指令内容';
  const tools=(r.required_tools||[]).join(', ')||'无';
  alert(`技能: ${r.name}\n\n所需工具: ${tools}\n\n--- 指令内容 ---\n\n${inst}`);
}
async function viewSkillPortability(skillId){
  const r=await api(`${A}/skills/${skillId}/portability`);
  if(!r){toast('获取失败');return}
  const tcolors={1:'var(--lime)',2:'var(--amber)',3:'var(--pink)'};
  const tdesc={1:'纯 Prompt — 可在任何 LLM 平台使用',2:'CLI/API 依赖 — 需要对应运行环境',3:'平台原生 — 仅在 AgentsGroup2026 上运行'};
  toast(`${skillId}: Tier ${r.tier} (${r.label})`);
  alert(`技能: ${skillId}\n\n可移植性等级: Tier ${r.tier}\n标签: ${r.label}\n\n${tdesc[r.tier]||'未知等级'}`);
}
async function viewSkillFolder(skillId){
  const r=await api(`${A}/skills/${skillId}/folder`);
  if(!r){toast('获取失败');return}
  const files=(r.files||[]).map(f=>`  📄 ${f.name||f} (${f.size||'?'} B)`).join('\n')||'  (无文件)';
  alert(`技能文件结构: ${skillId}\n\n📁 ${r.folder_name||skillId}/\n${files}`);
}

// ── Skill Config Modal ──
async function openSkillConfig(skillName){
  const r=await api(`${A}/skills/${skillName}/config-schema`);
  if(!r||!r.config_schema){toast('该技能无可配置项');return}
  const schema=r.config_schema;const cfg=r.config||{};
  let html=`<div class="card" style="max-width:560px;margin:0 auto"><div class="section-title">⚙️ ${skillName} 配置</div>`;
  Object.entries(schema).forEach(([key,def])=>{
    const val=cfg[key]!==undefined?cfg[key]:def.default;
    const desc=def.description||key;
    html+=`<div class="form-group"><label class="form-label">${desc}</label>`;
    if(def.enum){
      html+=`<select class="fi" id="sc-${key}">`;
      def.enum.forEach(opt=>{html+=`<option value="${opt}"${val===opt?' selected':''}>${opt}</option>`});
      html+='</select>';
    } else if(def.type==='boolean'){
      html+=`<select class="fi" id="sc-${key}"><option value="true"${val?'selected':''}>是</option><option value="false"${!val?'selected':''}>否</option></select>`;
    } else if(def.type==='integer'||def.type==='number'){
      html+=`<input class="fi" type="number" id="sc-${key}" value="${val||0}">`;
    } else {
      html+=`<input class="fi" type="text" id="sc-${key}" value="${escapeHtml(String(val||''))}" placeholder="${def.default||''}">`;
    }
    html+='</div>';
  });
  html+=`<div style="display:flex;gap:10px;margin-top:16px"><button class="btn btn-pink" onclick="saveSkillConfig('${skillName}')">保存配置</button><button class="btn" onclick="switchView('skills')">取消</button></div></div>`;
  // Show in main area
  const main=el('view-skills');
  main.querySelector('.main-scroll').innerHTML=html;
  window._skillConfigSchema=schema;window._skillConfigName=skillName;
}
async function saveSkillConfig(skillName){
  const schema=window._skillConfigSchema||{};const cfg={};
  Object.entries(schema).forEach(([key,def])=>{
    const e=el('sc-'+key);if(!e)return;
    if(def.type==='boolean')cfg[key]=e.value==='true';
    else if(def.type==='integer')cfg[key]=parseInt(e.value)||0;
    else if(def.type==='number')cfg[key]=parseFloat(e.value)||0;
    else cfg[key]=e.value;
  });
  const r=await api(`${A}/skills/${skillName}/config`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});
  if(r){toast(`${skillName} 配置已保存`);loadSkills()}else toast('保存失败');
}
async function testSkillExec(skillName){
  const prompt=window.prompt(`输入测试提示词 (${skillName}):`);
  if(!prompt)return;
  toast('正在执行...');
  const agentId=aid||'build_developer';const teamId=tid||'build_system';
  const r=await api(`${A}/teams/${teamId}/agents/${agentId}/skills/${skillName}/execute`,{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({prompt,task_id:'',config_overrides:{}})
  });
  if(r){
    if(r.session_id && r.status==='streaming'){
      // Open terminal panel and stream output
      openClaudeTerm(r.session_id);
    } else {
      const status=r.status||'unknown';
      let msg=`技能: ${skillName}\n状态: ${status}`;
      if(r.output)msg+=`\n\n输出:\n${r.output?.slice(0,500)||''}`;
      if(r.error)msg+=`\n\n错误: ${r.error}`;
      if(r.subtasks)msg+=`\n\n子任务: ${r.count} 个`;
      showInfoModal('技能执行结果', msg);
      toast(`${skillName} 执行: ${status}`);
    }
  } else toast('执行失败');
}

// ── Export Skills ──
function exportSkillsMD(){
  api(`${A}/skills`).then(function(all){
    if(!all||!all.length){toast('暂无技能可导出');return}
    var md='# Skills Export\n\n';
    all.forEach(function(s){md+='## '+s.name+'\n\n'+s.description+'\n\n'});
    var blob=new Blob([md],{type:'text/markdown'});
    var url=URL.createObjectURL(blob);
    var a=document.createElement('a');a.href=url;a.download='skills-export.md';
    document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);
    toast('已导出 '+all.length+' 个技能');
  });
}

// ── Claude Code Terminal ──

// Export to global scope for HTML onclick access (all functions referenced from generated HTML)
window.loadTools = loadTools;
window.loadSkills = loadSkills;
window.togTool = togTool;
window.testToolExec = testToolExec;
window.openToolConfig = openToolConfig;
window.openEditTool = openEditTool;
window.deleteTool = deleteTool;
window.submitEditTool = submitEditTool;
window.saveToolConfig = saveToolConfig;
window.togSkill = togSkill;
window.openSkillConfig = openSkillConfig;
window.viewSkillInstructions = viewSkillInstructions;
window.openEditSkill = openEditSkill;
window.deleteSkill = deleteSkill;
window.viewSkillPortability = viewSkillPortability;
window.viewSkillFolder = viewSkillFolder;
window.openGenerateSkillModal = openGenerateSkillModal;
window.importSkillFromFile = importSkillFromFile;
window.exportSkillsMD = exportSkillsMD;
window.submitGenerateSkill = submitGenerateSkill;
window.saveSkillConfig = saveSkillConfig;
window.submitEditSkill = submitEditSkill;
window.testSkillExec = testSkillExec;

})();
