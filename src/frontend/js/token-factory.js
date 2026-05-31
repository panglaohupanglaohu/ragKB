/**
 * AgentsGroup2026 — Token Factory Dashboard
 * Manages SSH tunnel, Ollama probing, Claude Code connectivity
 * testing, and overall inference service health monitoring.
 * Extracted from agent-team-config.js for modularity.
 * Depends on: utils.js, api.js, agent-team-config.js (parent scope)
 */
(function(){
'use strict';
let _tfPollTimer=null;
function _startTfPoll(){if(_tfPollTimer)clearInterval(_tfPollTimer);_tfPollTimer=setInterval(()=>{if(document.querySelector('#view-registry:not(.hidden)'))loadTokenFactory();else{clearInterval(_tfPollTimer);_tfPollTimer=null}},5000)}
async function loadTokenFactory(){hideViewLoading("view-registry");
  try{
    const r=await fetch(`${TF}/health`);
    if(!r.ok){el('tf-health').innerHTML=`<p style="color:oklch(0.48 0.07 22)">API 错误: HTTP ${r.status}</p>`;return}
    const d=await r.json();
    if(!d){el('tf-health').innerHTML='<p style="color:var(--dim)">Token Factory 返回空数据</p>';return}
  // Health overview
  const ready=d.ready;
  const providers=d.providers||{};
  const ollama=providers.ollama_local||{};
  const deepseek=providers.deepseek||{};
  const cc=providers.claude_code||{};
  const tunnel=d.tunnel||{};
  let html='<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">';
  html+=`<div style="text-align:center;padding:14px;background:rgba(0,0,0,.1);border-radius:0"><div style="font-size:24px;margin-bottom:4px">${ready?'🟢':'🔴'}</div><div style="font-size:11px;color:var(--muted)">整体状态</div><div style="font-weight:600;font-size:13px">${ready?'就绪':'不可用'}</div></div>`;
  html+=`<div style="text-align:center;padding:14px;background:rgba(0,0,0,.1);border-radius:0"><div style="font-size:24px;margin-bottom:4px">${ollama.reachable?'🦙':'⬛'}</div><div style="font-size:11px;color:var(--muted)">Ollama</div><div style="font-weight:600;font-size:13px;color:${ollama.reachable?'var(--lime)':'var(--dim)'}">${ollama.reachable?ollama.latency_ms+'ms':'离线'}</div></div>`;
  html+=`<div style="text-align:center;padding:14px;background:rgba(0,0,0,.1);border-radius:0"><div style="font-size:24px;margin-bottom:4px">${cc.ok?'☁️':'⬛'}</div><div style="font-size:11px;color:var(--muted)">Claude via DeepSeek</div><div style="font-weight:600;font-size:13px;color:${cc.ok?'var(--lime)':'var(--dim)'}">${cc.ok?'就绪':(deepseek.reachable?deepseek.latency_ms+'ms':(deepseek.error||'离线'))}</div></div>`;
  html+=`<div style="text-align:center;padding:14px;background:rgba(0,0,0,.1);border-radius:0"><div style="font-size:24px;margin-bottom:4px">${tunnel.state==='running'?'🔗':'🔌'}</div><div style="font-size:11px;color:var(--muted)">SSH 隧道</div><div style="font-weight:600;font-size:13px;color:${tunnel.state==='running'?'var(--lime)':'var(--dim)'}">${tunnel.state==='running'?'PID '+tunnel.pid:'停止'}</div></div>`;
  html+='</div>';
  if(d.ollama_models&&d.ollama_models.length){
    html+=`<div style="margin-top:14px;font-size:12px;color:var(--muted)">可用模型: <span style="color:var(--lime);font-family:'IBM Plex Mono',monospace">${d.ollama_models.join(', ')}</span></div>`;
  }
  el('tf-health').innerHTML=html;
  // Tunnel
  el('tf-tunnel-state').innerHTML=`<span style="color:${tunnel.state==='running'?'oklch(0.52 0.04 160)':'oklch(0.48 0.07 22)'}">${tunnel.state==='running'?'● 运行中':'○ 停止'}</span>${tunnel.pid?' — PID '+tunnel.pid:''}`;
  el('tf-tunnel-port').textContent=tunnel.config?.local_port||'11434';
  el('tf-tunnel-host').textContent=tunnel.config?.remote_host||'—';
  // Ollama models
  if(ollama.reachable&&ollama.models&&ollama.models.length){
    el('tf-ollama-models').innerHTML=ollama.models.map(m=>`<span style="display:inline-block;padding:3px 10px;margin:2px 4px;background:rgba(110,231,183,.12);border:1px solid rgba(110,231,183,.3);border-radius:4px;color:oklch(0.52 0.04 160)">${escapeHtml(m)}</span>`).join('');
  }else{
    el('tf-ollama-models').innerHTML='<span style="color:var(--dim)">未检测到模型</span>';
  }
  // DeepSeek — show Claude Code via DeepSeek result
  if(cc.ok){
    let h='<span style="color:oklch(0.52 0.04 160);font-weight:600">● 就绪</span> <span style="color:var(--muted);font-size:11px">— Claude Code 已通过 DeepSeek 返回响应 ('+cc.latency_ms+'ms)</span>';
    if(cc.reply){h+='<div style="margin-top:8px;padding:8px 12px;background:rgba(110,231,183,.08);border:1px solid rgba(110,231,183,.2);border-radius:6px;white-space:pre-wrap;color:oklch(0.18 0.008 110);font-size:12px;max-height:120px;overflow-y:auto">'+escapeHtml(cc.reply||'').slice(0,500)+'</div>'}
    el('tf-deepseek-status').innerHTML=h;
  }else if(deepseek.reachable){
    el('tf-deepseek-status').innerHTML='<span style="color:oklch(0.52 0.04 160)">● 在线</span> <span style="color:var(--muted);font-size:11px">— 点击 ⚡确保就绪 测试 Claude Code 链路</span>';
  }else{
    el('tf-deepseek-status').innerHTML='<span style="color:oklch(0.48 0.07 22)">○ '+(cc.error||deepseek.error||'离线')+'</span>';
  }
  }catch(e){el('tf-health').innerHTML=`<p style="color:oklch(0.48 0.07 22)">加载失败: ${e.message}</p>`;console.error('TokenFactory load error:',e)}
}
async function tfEnsureReady(){
  toast('正在确保推理服务就绪...');
  const d=await api(`${TF}/ensure-ready`,{method:'POST'});
  if(d&&d.ready){toast('✅ Token Factory 就绪')}else{toast('⚠️ 部分服务不可用')}
  loadTokenFactory();
}
async function tfTunnelStart(){
  toast('正在启动 SSH 隧道...');
  el('tf-tunnel-state').innerHTML='<span style="color:oklch(0.56 0.05 70)">⏳ 启动中...</span>';
  try{
    const ctrl=new AbortController();
    const tmr=setTimeout(()=>ctrl.abort(),15000);
    const r=await fetch(`${TF}/tunnel/start`,{method:'POST',signal:ctrl.signal});
    clearTimeout(tmr);
    const d=await r.json();
    if(d&&d.ok){
      toast('✅ 隧道已启动');
      el('tf-tunnel-state').innerHTML=`<span style="color:oklch(0.52 0.04 160)">● 运行中</span> — PID ${d.pid||'?'} — ${d.state}`;
    }else{
      toast('⚠️ 隧道启动失败');
      el('tf-tunnel-state').innerHTML=`<span style="color:oklch(0.48 0.07 22)">✕ 启动失败</span> — ${d.state||d.error||'未知错误'}`;
    }
  }catch(e){
    const msg=e.name==='AbortError'?'请求超时(15s)':e.message;
    toast('❌ 请求失败: '+msg);
    el('tf-tunnel-state').innerHTML=`<span style="color:oklch(0.48 0.07 22)">✕ ${msg}</span>`;
  }
  loadTokenFactory();
  setTimeout(loadTokenFactory,3000);
}
async function tfTunnelStop(){
  el('tf-tunnel-state').innerHTML='<span style="color:oklch(0.56 0.05 70)">⏳ 停止中...</span>';
  try{
    const ctrl=new AbortController();
    const tmr=setTimeout(()=>ctrl.abort(),10000);
    const r=await fetch(`${TF}/tunnel/stop`,{method:'POST',signal:ctrl.signal});
    clearTimeout(tmr);
    const d=await r.json();
    toast('隧道已停止');
    el('tf-tunnel-state').innerHTML=`<span style="color:oklch(0.55 0.005 110)">○ 已停止</span> — ${d.state||'stopped'}`;
  }catch(e){
    const msg=e.name==='AbortError'?'请求超时(10s)':e.message;
    toast('❌ 请求失败: '+msg);
    el('tf-tunnel-state').innerHTML=`<span style="color:oklch(0.48 0.07 22)">✕ ${msg}</span>`;
  }
  loadTokenFactory();
  setTimeout(loadTokenFactory,2000);
}
async function tfTestClaude(){
  const statusEl=el('tf-claude-test-status');
  const resultEl=el('tf-claude-test-result');
  statusEl.innerHTML='<span style="color:oklch(0.56 0.05 70)">⏳ 运行 claude -p "hi" ...</span>';
  resultEl.style.display='block';
  resultEl.innerHTML='<span style="color:oklch(0.56 0.05 70)">⏳ 正在通过 CLI 调用 Claude Code... (提示词: "hi")</span>';
  toast('正在测试 Claude Code CLI...');
  const ctrl=new AbortController();const tmr=setTimeout(()=>ctrl.abort(),15000);
  try{
    const r=await fetch(`${TF}/probe/claude`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:'hi'}),signal:ctrl.signal});
    clearTimeout(tmr);
    const d=await r.json();
    let html='';
    if(d.ok){
      statusEl.innerHTML='<span style="color:oklch(0.52 0.04 160)">✅ 测试通过</span>';
      html+=`<div style="color:oklch(0.52 0.04 160);font-weight:600;margin-bottom:8px">✅ Claude Code CLI 正常</div>`;
      html+=`<div><b>模型</b>: ${escapeHtml(d.model)}</div>`;
      html+=`<div><b>延迟</b>: ${d.latency_ms} ms</div>`;
      html+=`<div style="margin-top:8px;padding:10px 12px;background:rgba(110,231,183,.08);border:1px solid rgba(110,231,183,.2);border-radius:6px"><b>模型回复</b>:<div style="margin-top:4px;white-space:pre-wrap;color:oklch(0.18 0.008 110)">${escapeHtml(d.reply||'(空)')}</div></div>`;
      toast(`✅ Claude Code 测试通过 — ${d.latency_ms}ms`);
    }else{
      statusEl.innerHTML='<span style="color:oklch(0.48 0.07 22)">❌ 测试失败</span>';
      html+=`<div style="color:oklch(0.48 0.07 22);font-weight:600;margin-bottom:8px">❌ Claude Code CLI 异常</div>`;
      html+=`<div><b>模型</b>: ${escapeHtml(d.model)}</div>`;
      if(d.latency_ms) html+=`<div><b>延迟</b>: ${d.latency_ms} ms</div>`;
      if(d.error) html+=`<div style="margin-top:8px;padding:10px 12px;background:oklch(0.48 0.07 22 / .08);border:1px solid oklch(0.48 0.07 22 / .2);border-radius:6px;color:oklch(0.48 0.07 22)"><b>错误</b>: ${escapeHtml(d.error)}</div>`;
      toast('⚠️ Claude Code 测试失败');
    }
    resultEl.innerHTML=html;
  }catch(e){
    clearTimeout(tmr);
    const msg=e.name==='AbortError'?'请求超时(15s)，请检查服务状态':e.message;
    statusEl.innerHTML='<span style="color:oklch(0.48 0.07 22)">❌ 请求异常</span>';
    resultEl.innerHTML=`<div style="color:oklch(0.48 0.07 22)">❌ 请求失败: ${escapeHtml(msg)}</div>`;
    toast('❌ 测试请求失败: '+msg);
  }
}
async function tfTestClaudeReady(){
  const stEl=el('tf-claude-ready-status');
  const dsEl=el('tf-deepseek-status');
  stEl.innerHTML='<span style="color:oklch(0.56 0.05 70)">⏳ 正在测试 Claude Code → DeepSeek 链路...</span>';
  dsEl.innerHTML='<span style="color:oklch(0.56 0.05 70)">⏳ 运行 claude -p "hi" ，请稍候...</span>';
  toast('正在测试 Claude → DeepSeek 就绪...');
  const ctrl=new AbortController();const tmr=setTimeout(()=>ctrl.abort(),15000);
  try{
    const r=await fetch(`${TF}/probe/claude`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:'hi'}),signal:ctrl.signal});
    clearTimeout(tmr);
    const d=await r.json();
    if(d.ok){
      stEl.innerHTML='<span style="color:oklch(0.52 0.04 160)">✅ Claude 就绪</span>';
      let h='<span style="color:oklch(0.52 0.04 160);font-weight:600">● 就绪</span> <span style="color:var(--muted);font-size:11px">— Claude Code 已通过 DeepSeek 返回响应 ('+d.latency_ms+'ms)</span>';
      if(d.reply){h+='<div style="margin-top:8px;padding:8px 12px;background:rgba(110,231,183,.08);border:1px solid rgba(110,231,183,.2);border-radius:6px;white-space:pre-wrap;color:oklch(0.18 0.008 110);font-size:12px;max-height:120px;overflow-y:auto">'+escapeHtml(d.reply||'').slice(0,500)+'</div>'}
      dsEl.innerHTML=h;
      toast('✅ Claude via DeepSeek 就绪 — '+d.latency_ms+'ms');
    }else{
      stEl.innerHTML='<span style="color:oklch(0.48 0.07 22)">❌ 未就绪</span>';
      dsEl.innerHTML='<span style="color:oklch(0.48 0.07 22)">○ '+(d.error||'连接失败')+'</span>';
      toast('⚠️ Claude 未就绪: '+(d.error||''));
    }
  }catch(e){
    clearTimeout(tmr);
    const msg=e.name==='AbortError'?'请求超时(15s)，请检查服务状态':e.message;
    stEl.innerHTML='<span style="color:oklch(0.48 0.07 22)">❌ 请求异常</span>';
    dsEl.innerHTML='<span style="color:oklch(0.48 0.07 22)">○ '+escapeHtml(msg)+'</span>';
    toast('❌ 测试失败: '+msg);
  }finally{
    loadTokenFactory();
  }
}
async function tfProbeOllama(){
  toast('正在探测 Ollama...');
  const modelsEl=el('tf-ollama-models');
  modelsEl.innerHTML='<span style="color:oklch(0.56 0.05 70)">⏳ 探测中 http://127.0.0.1:11434 ...</span>';
  const ctrl=new AbortController();const tmr=setTimeout(()=>ctrl.abort(),15000);
  try{
    const r=await fetch(`${TF}/probe/ollama`,{signal:ctrl.signal});
    clearTimeout(tmr);
    const d=await r.json();
    let html='';
    if(d.reachable){
      const root=d.root||{};
      const tags=d.api_tags||{};
      html+=`<div style="margin-bottom:8px"><span style="color:oklch(0.52 0.04 160);font-weight:600">✅ Ollama 可达</span> — <code>${d.url}</code></div>`;
      html+=`<div style="font-size:12px;padding:8px 12px;background:rgba(0,0,0,.2);border-radius:6px;margin-bottom:6px">`;
      html+=`<div><b>GET /</b> → HTTP ${root.status} (${root.latency_ms}ms)</div>`;
      html+=`<div style="color:var(--muted);font-family:'IBM Plex Mono',monospace;font-size:11px;margin:4px 0">${escapeHtml((root.body||'').trim())}</div>`;
      html+=`<div style="margin-top:6px"><b>GET /api/tags</b> → HTTP ${tags.status} (${tags.latency_ms}ms) — ${tags.model_count} 个模型</div>`;
      if(tags.models&&tags.models.length){
        html+=`<div style="margin-top:4px">`+tags.models.map(m=>`<span style="display:inline-block;padding:2px 8px;margin:2px 3px;background:rgba(110,231,183,.12);border:1px solid rgba(110,231,183,.3);border-radius:4px;color:oklch(0.52 0.04 160);font-size:11px">${escapeHtml(m)}</span>`).join('')+'</div>';
      }
      html+=`</div>`;
      toast(`✅ Ollama 在线 — ${tags.model_count} 个模型, ${root.latency_ms}ms`);
    }else{
      html+=`<div style="color:oklch(0.48 0.07 22)">❌ Ollama 不可达 — <code>${d.url}</code></div>`;
      if(d.error) html+=`<div style="font-size:12px;color:oklch(0.48 0.07 22);margin-top:4px;padding:8px 12px;background:oklch(0.48 0.07 22 / .08);border-radius:6px;font-family:'IBM Plex Mono',monospace">${escapeHtml(d.error)}</div>`;
      toast('⚠️ Ollama 不可达: '+(d.error||''));
    }
    modelsEl.innerHTML=html;
  }catch(e){
    clearTimeout(tmr);
    const msg=e.name==='AbortError'?'请求超时(15s)，请检查 Ollama 服务':e.message;
    modelsEl.innerHTML=`<span style="color:oklch(0.48 0.07 22)">❌ 探测请求失败: ${escapeHtml(msg)}</span>`;
    toast('❌ 探测失败: '+msg);
  }
  setTimeout(loadTokenFactory,3000);
}




// Export to global scope
window.loadTokenFactory = loadTokenFactory;
window._startTfPoll = _startTfPoll;
window.tfEnsureReady = tfEnsureReady;
window.tfTunnelStart = tfTunnelStart;
window.tfTunnelStop = tfTunnelStop;
window.tfTestClaude = tfTestClaude;
window.tfTestClaudeReady = tfTestClaudeReady;
window.tfProbeOllama = tfProbeOllama;
})();
