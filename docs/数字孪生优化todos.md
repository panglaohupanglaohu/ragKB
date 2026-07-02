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

## 落地顺序
```
T1(cli 三轮询) → T2(director 两轮询) → T3(可见即补刷) → T4 目检 + node --check
```
> 延后：P4 空 catch（按需补日志，不批量翻新）、P5 冷启动重复渲染（收益 < 回归风险）。见 plan。
