<!-- docs-signoff: author="grok-4.5" kind="llm" doc="todos" ts="2026-07-27T14:12:00Z" -->
# 数字孪生联动 TODOS（事无巨细 + 伪代码）

> 配套 `docs/数字孪生联动plan.md`。核心：**建一个 `dtRefresh(reason)` 调度器**，把"上下文变→刷新当前 Tab"收成一处，替代各处零散补渲染。
> 标注：**[VSCode]** 机械低风险；**[人工核]** 需判断/联机。

## L1 · 建调度器 `dtRefresh` + 快照 `dtContext` ★★★ [VSCode]（digital-twin-cli.js）
```js
function dtContext(){return{team:window._selectedTeamId||'',scenarioId:(window._sx&&window._sx.scenarioId)||'',
  steps:(window._sx&&window._sx.steps)||0,running:!!(window._sx&&window._sx.simRunning),
  trialId:(window._DTS&&window._DTS.activeTrialId)||''};}
window.dtRefresh=function(reason){
  var p=document.querySelector('.view-panel.active');var v=p?p.id:'';
  try{
    if(v==='view-environment'){ if(['team','scenario','tab'].includes(reason)&&window._dt3dBuildRoom&&window._currentRoomId)window._dt3dBuildRoom(window._currentRoomId); }
    else if(v==='view-architecture'){ if(typeof renderArchitecture==='function')renderArchitecture(); }
    else if(v==='view-interaction'){ var tp=document.getElementById('interact-sub-topo');
      if(tp&&tp.style.display!=='none'){ if(typeof renderTopology==='function')renderTopology(); }
      else { if(typeof renderInteractions==='function')renderInteractions('all'); } }
    else if(v==='view-pipeline'){ if(typeof renderPipeline==='function')renderPipeline(); }
  }catch(e){}
};
```
- **验收**：`dtRefresh('team')` 只刷新当前可见 Tab，无报错。

## L2 · 事实源变化处统一喊 `dtRefresh(reason)` ★★★（去掉零散补渲染）
- [VSCode] `switchView` 末尾：`if(window.dtRefresh)window.dtRefresh('tab');`（保留 environment 的房间初始化）。
- [VSCode] 选团队 `toggleTeam`：把手动 `renderTopology()` 换成 `window.dtRefresh&&dtRefresh('team')`（3D 重建保留）。
- [VSCode] `sexySelectScene`(secs-core)：已加的 `renderPipeline()` 换成 `window.dtRefresh&&window.dtRefresh('scenario')`。
- [VSCode] `sexySelectTask`(secs-core) 末尾：`window.dtRefresh&&window.dtRefresh('task')`。
- [VSCode] SECS 步进处(`_sx.steps=` 之后)：把只刷 pipeline 换成 `window.dtRefresh&&window.dtRefresh('step')`。
- [VSCode] `_doInjectEvent` 混沌分支末尾：3D/拓扑同步后 `window.dtRefresh&&window.dtRefresh('chaos')`。
- **验收**：grep 不到"选团队/切Tab 后手动逐个 renderXxx"；统一走 dtRefresh。

## L3 · 系统状态(仪表盘) 团队/运行联动 ★★ ✅已落地(当前演练摘要卡)
- [x] [人工核] `loadLiveMetrics` 现拉 `/tasks/stats` `/extraction/stats`——**是否需要按当前团队 / 当前 trial 过滤**？
  - **结论：全局 KPI 不按 team/trial 过滤**（后端无过滤参数；`running` 是 engine bool）。
  - 演练态单独用「当前演练」卡：读 `dtContext()` + `_sx`/SECS 选择态（team/scene/task/steps/reward/trial）。
  - 不做 `/tasks/stats?team_id=`，避免把全局任务引擎统计伪装成当前演练。
- [x] [VSCode] `renderArchitecture` → `renderDashboard` 顶部 `#dt-current-drill-card`（team/场景/任务/步数/running/收益/最优分/trial），随 dtRefresh 刷新；`_mapTaskEngineStats` 修正 by_status 计数。
- **验收**：切团队/跑演练时，系统状态顶部"当前演练"卡随之变。⟦vitest `digital-twin-current-drill-card.test.js` 3 passed⟧

## L4 · 协作·交互 时间线运行时实时追加 ★★ ✅已落地(step 的 agent_actions 喂入 S.messages)
- [x] 团队过滤已做(bug-086)。
- [VSCode] 步进时若在该 Tab：dtRefresh('step') 已会调 renderInteractions → 新消息自动追加（依赖 `S.messages` 被 SSE 追加）。**[人工核]** 确认演练 SSE 消息进了 `S.messages`（`loadDtState` 的 interactions 或 step 事件）；若没进，补一处 `S.messages.push(标准化消息)`。
- **验收**：运行中在协作·交互 Tab，时间线随步数增长；切"协作拓扑"子页节点随混沌增删。

## L5 · 编排管线 精确节点状态（可选，进阶）★ ⏸需后端(sim 需 emit active_task_id, 现为步进比例近似)
- 现为"整体步进比例"近似。要精确到"T3 此刻在跑"：后端 step 事件带 `active_task_id/done_task_ids`，前端按之标状态。
- **[需后端]** 标记为进阶项，不阻塞 L1~L4。

## L6 · 验收（联机目检）★★ [人工]
```
选团队A→跑演练→轮流点 4 个 Tab：都只反映 A + 当前运行，无串台/无停初始态。
改选团队B→当前 Tab 立即变 B。
注入 离开/增援→3D、协作拓扑、(仪表盘计数) 一致。
来回切 Tab→都是最新态。
node --check 前端无误；控制台无 renderXxx 报错。
```

## 落地顺序
```
L1 建 dtRefresh(地基) → L2 各触发点收口(替换零散补渲染) → L4 交互时间线实时(小补)
→ L3 仪表盘当前演练卡([人工核]数据源) → L5 精确节点状态(进阶,需后端)
```
> L1+L2 就能根治"打地鼠"；L3/L4 补齐剩余联动；L5 是进阶精度，需后端配合。
