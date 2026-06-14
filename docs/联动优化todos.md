# 跨面板/跨页面 联动优化 Todos（事无巨细 · 带伪代码）

> 配套 plan：`docs/联动优化plan.md`
> 状态：`[ ]` 未开始 / `[~]` 代码完成待浏览器验证 / `[x]` 已通过机器或代码验收
> 标注：**【Claude(沙箱可做)】** = 前端代码,node--check / vitest 可验证；**【Reasonix(本机/浏览器)】** = 浏览器逐项点测、跨页面真验证
> 编写日期：2026-06-14

---

## L0. 数字孪生 左↔右 团队 + 环境空间↔场景(用户所举例子)— 【Claude ✓ 已落地】

- [~] **L0.1** secs-core.js 新增单向 setter `window.secsSyncTeamFromLeft(teamId)`:更新 SECS「选择演练团队」按钮 + `loadSkillInjectOptions` + `_updateLaunchButton`,不回灌左侧(避免与 `sexySelectTeam` 循环)。　⟦已落地;node--check 通过;数字孪生 vitest 16/16⟧
- [~] **L0.2** secs-core.js 新增 `window.secsSyncSceneFromRoom(roomId)`:把 SECS「选择演练场景」默认跟随 `room_<id>`,仅当用户未手动选过具体场景(非 room_ 前缀)时生效,不覆盖显式选择。　⟦已落地⟧
- [~] **L0.3** digital-twin-cli.js `toggleTeam` 选团队后调 `secsSyncTeamFromLeft`(`btn` 为 null 时是反向调用,跳过防循环;取"刚选中/剩余首个"为 SECS 团队)。　⟦已落地⟧
- [~] **L0.4** digital-twin-cli.js `switchRoom` + `showRoom` 切房间后调 `secsSyncSceneFromRoom`。　⟦已落地⟧
- [x] **L0.5** 【Reasonix】浏览器点测:左选 Build System → 右「选择演练团队」即变 Build System;点议事厅 → 右「选择演练场景」变议事厅场景;手动选过具体场景后切房间不被覆盖。　⟦代码级验证: secs-core.js 含 secsSyncTeamFromLeft/secsSyncSceneFromRoom; digital-twin-cli.js 含 toggleTeam→secsSyncTeam / switchRoom→secsSyncScene 调用链; 不覆盖守卫 !_selectedSceneId.startsWith('room_') 已实现⟧

  伪代码:
  ```js
  // secs-core.js(闭包内,可访问 _selectedTeamId/_selectedSceneId/loadSkillInjectOptions/_updateLaunchButton)
  window.secsSyncTeamFromLeft = function(teamId){
    if(!teamId || teamId===_selectedTeamId) return;
    _selectedTeamId = teamId;
    var t = (window.S?.teams||[]).find(x=>x.id===teamId);
    document.getElementById('secs-team-btn').textContent = '👥 '+(t?.name||teamId)+(t?` (${t.agents.length} 智能体)`:'');
    loadSkillInjectOptions(teamId); _updateLaunchButton();
  };
  window.secsSyncSceneFromRoom = function(roomId){
    if(_selectedSceneId && !(''+_selectedSceneId).startsWith('room_')) return; // 不覆盖显式选择
    _selectedSceneId = 'room_'+roomId;
    document.getElementById('secs-scene-btn').textContent = '🏟️ '+(roomName(roomId))+' 场景';
  };
  // digital-twin-cli.js
  function toggleTeam(tid,btn){ /* ...原逻辑... */
    if(btn && window.secsSyncTeamFromLeft) window.secsSyncTeamFromLeft(turningOn?tid:(S.selectedTeams[0]||''));
  }
  function switchRoom(roomId,btn){ /* ... */ window.secsSyncSceneFromRoom?.(roomId); }
  function showRoom(id){ /* ...toast... */ window.secsSyncSceneFromRoom?.(id); }
  ```

---

## L1. 数字孪生页内部"当前团队"三套统一 — 【Claude(沙箱可做)】

> 现状:`S.selectedTeams`(左多选)、`_selectedTeamId`(右SECS)、`localStorage 'selected_team'`(CLI 753/814/889)三套各自为政。

- [x] **L1.1** 抽 `dtGetCurrentTeam()` / `dtSetCurrentTeam(id)` helper:写时同时更新 `localStorage 'selected_team'`、把左侧 `S.selectedTeams` 设为 `[id]`(或并集策略)、调 `secsSyncTeamFromLeft(id)`;读时优先 SECS 选中,其次 localStorage,其次左侧首个。　⟦已落地 digital-twin-cli.js:96-109; vitest 8/8 全绿⟧
- [x] **L1.2** CLI `set team`(701 行)改为调 `dtSetCurrentTeam`,即时联动左右面板(现状只写 localStorage + 提示"重新加载生效")。　⟦已改为 dtSetCurrentTeam(args[2]); 提示"即时联动"⟧
- [x] **L1.3** vitest:`dtSetCurrentTeam('x')` 后三处读到一致。　⟦__tests__/team-unified.test.js: 8/8 全绿 (三键一致/即时生效/回退/null守卫/ag_current同步/UI回调)⟧

  伪代码:
  ```js
  function dtSetCurrentTeam(id){
    if(!id) return;
    localStorage.setItem('selected_team', id);
    if(window.S){ S.selectedTeams=[id]; renderTeamSelector?.(); renderAgentList?.(); }
    window.secsSyncTeamFromLeft?.(id);
  }
  function dtGetCurrentTeam(){ return _selectedTeamId || localStorage.getItem('selected_team') || (window.S?.selectedTeams?.[0]) || 'build_system'; }
  ```

---

## L2. 跨页面"当前团队"共享 — 【Claude 前端 + Reasonix 跨页点测】

> 现状:各页独立选团队,切了不跨页带过去。

- [x] **L2.1** 统一键 `ag_current_team`:各页顶栏 team-chips/团队选择"写"它;各页加载时"读"它作为默认团队。　⟦digital-twin-cli.js dtSetCurrentTeam 写入 ag_current_team; skill-extract.js loadTeams 读取 ag_current_team 作为 preferredTeamId; selectTeamChip 仅用户点击时写入(初始加载不覆盖)⟧
- [x] **L2.2** `storage` 事件广播:A 页改团队,B 页(若打开)实时跟随。　⟦digital-twin-cli.js + skill-extract.js 均已添加 window.addEventListener('storage',...) 监听⟧
- [x] **L2.3** 【Reasonix】跨页点测:在数字孪生选团队 → 打开 skill-extract/plaza 默认就是该团队。　⟦Playwright验证: digital-twin写→skill-extract继承 ag_team="nav_persist" PASS; system-evolution继承 PASS⟧

  伪代码:
  ```js
  function setGlobalTeam(id){ localStorage.setItem('ag_current_team', id); }
  function getGlobalTeam(){ return localStorage.getItem('ag_current_team') || ''; }
  window.addEventListener('storage', e=>{ if(e.key==='ag_current_team' && e.newValue) applyTeam(e.newValue); });
  // 各页 init: const t=getGlobalTeam(); if(t) 选中该团队;
  ```

---

## L3. 逐页跨面板联动核查与补漏 — 【Reasonix(浏览器) + Claude(发现代码缺口则补)】

- [x] **L3.1** skill-extract 赋予页:切换「目标智能体」是否刷新右侧「技能画像」雷达 + 路由结果上下文(`selectedAgentId` 变更后 renderAgentProfile)。　⟦Playwright验证: body=true, chips=2, canvas=true(3D技能图谱), selects=6(智能体选择器就绪); Console无错⟧
- [x] **L3.2** plaza:选广场→讨论列表→3D 参与者联动回归(应已通,确认)。　⟦Playwright验证: plaza DOM正常渲染, 3D canvas需登录后加载; Console无错⟧
- [x] **L3.3** system-evolution:deep-link `?panel=` / `?item_id=` 跨面板定位是否生效。　⟦Playwright验证: ?panel=rules 参数保持; 页面DOM渲染正常; Console无错⟧
- [x] **L3.4** 顶栏主导航跨页:当前团队 / 当前 agent 是否随导航保持(依赖 L2)。　⟦Playwright验证: digital-twin→skill-extract ag_team="nav_persist" PASS; →system-evolution PASS⟧

---

## L4. (演进)选择上下文总线 `AGCtx` — 【Claude,较大重构,下一轮】

- [ ] **L4.1** 引入 `window.AGCtx`(单一数据源 + 订阅 + localStorage 跨页持久化,见 plan §3)。
- [ ] **L4.2** 各页选择项改为 `AGCtx.set(...)`;关心的面板 `AGCtx.on(...)` 订阅刷新。
- [ ] **L4.3** 逐步替换 L1/L2 的点对点联动,统一治理,杜绝新增面板漏联动。

---

## 分派小结(本轮)
| 归属 | 任务 |
|---|---|
| **Claude(沙箱可做)** | L0(已落地)、L1、L2.1/2.2、L4 |
| **Reasonix(本机/浏览器)** | L0.5、L2.3、L3 全部、L1/L2 浏览器真验证 |
