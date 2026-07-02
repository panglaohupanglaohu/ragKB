# 数字孪生优化 TODOS（事无巨细 + 伪代码）

> 配套 `docs/数字孪生优化plan.md`。本轮主线 = **后台轮询可见性门控**（对齐仓库既有 `document.hidden` 约定）。
> 标注：**[VSCode]** 机械低风险；**[人工核]** 需联机目检。

## T1 · cli.js 三个轮询加 hidden 守卫 ★★★ [VSCode]（digital-twin-cli.js）✅已落地(feat-021)
- [x] `:20` `setInterval(loadLiveMetrics,10000)` → 回调首行 `if(document.hidden)return;`
- [x] `:1236` 频率图采样 → `if(document.hidden)return;`（隐藏时不采样、不重绘）
- [x] `:1238` `loadTeamsAndAgents+render`(30s) → `if(document.hidden)return;`
```js
setInterval(()=>{ if(document.hidden)return; loadLiveMetrics(); }, 10000);
setInterval(()=>{ if(document.hidden)return; S.freqData.push(_freqBucket);_freqBucket=0;S.freqData.shift();renderFreqChart(); }, 2000);
setInterval(async()=>{ if(document.hidden)return; await loadTeamsAndAgents();renderAgentList();renderStats();renderDashboard(); }, 30000);
```

## T2 · director.js 两个轮询加 hidden 守卫 + syncTeam 降频 ★★ [VSCode]✅已落地(feat-021)
- [x] `:226` `_dtRoomMapHealth` 2s → `if(document.hidden)return;`
- [x] `:256` `syncTeam` 1000ms → 2000ms + `if(document.hidden)return;`
```js
setInterval(()=>{ if(document.hidden)return; window._dtRoomMapHealth(); }, 2000);
setInterval(()=>{ if(document.hidden)return; syncTeam(); }, 2000);
```

## T3 · 重新可见时补刷一次 ★★ [VSCode]（cli.js）✅已落地(feat-021)
```js
document.addEventListener('visibilitychange', function(){
  if(document.hidden) return;
  loadLiveMetrics();                 // 指标立即回补
  if(window.dtRefresh) window.dtRefresh('tab');  // 当前 Tab 回刷
});
```
- **验收**：切走→切回，指标/当前 Tab 立即更新，不停在过期态。

## T4 · 验收 ★★
- [x] **[VSCode] 代码级**：`node --check` cli.js / -3d.js / director.js / secs-core.js 四文件全绿。
- [ ] **[人工核] 联机目检**（需在浏览器打开运行中的页面，我这边未跑）：
```
切到其它标签页 → DevTools Network：/tasks/stats、/extraction/stats、/teams 轮询停止。
切回本页 → 立即恢复且刷新一次；频率图/智能体/团队标签照常。
```

## T5 · P4 定向补日志 ★ [VSCode] ✅已落地(feat-022)
- [x] cli.js 6 处网络/状态加载 catch → `console.warn('[dt]',e)`：loadDtState / syncDtState / 加载团队 agent / loadSkills / loadTools / loadLiveMetrics。
- [x] secs-core 混沌同步 catch → warn。
- 纯 UI 防御性 catch（render 守卫等）保持静默，避免控制台噪音。

## T6 · P5 冷启动惰性渲染 ★ [VSCode] ✅已落地(feat-022)
- [x] `init()` 只渲染常驻区 + 默认「环境空间」；architecture/interaction/pipeline 进入时经 `dtRefresh('tab')` 惰性渲染。
- **验收**：冷启动少 3 次无谓渲染；点各 Tab 首次进入正常显示（switchView→dtRefresh 已覆盖）。

## T7 · P6 右侧「协作图」反映增/减 agent ★★ [VSCode] ✅已落地(bug-088)
- [x] `_renderCollabGraph` 接 `_chaosTopoState`（剔离开/并增援，增援虚线描边）+ 数据回退 + 动态标题计数 + 空态提示 + 椭圆布局。
- [x] 混沌注入末尾 `_renderCollabGraph()` 实时重渲染；`init` 占位。
- **验收**：演练中注入「智能体离开/加入」→ 右侧协作图节点随之增减，标题 `[n]` 同步。

## 落地顺序
```
T1(cli 三轮询) → T2(director 两轮询) → T3(可见即补刷) → T4 目检 + node --check
→ T5(P4 定向日志) → T6(P5 惰性渲染) → T7(P6 协作图增/减)
```
