# 数字孪生联动 Plan — Tab 菜单 ↔ 右侧演练面板 单一事实源联动

> 承接 `docs/数字孪生收口plan.md`。目标：**根治"选了团队/场景，某个 Tab 不跟着变"的打地鼠问题**——让右侧「演练配置 + 运行状态」成为**单一事实源(SSOT)**，5 个 Tab 都从它读、并在上下文变化时**自动刷新当前可见 Tab**。

---

## 1. 现状诊断：谁是数据源、哪里断

**右侧面板 = 事实源（已在用，但没被统一消费）**：
- `window._selectedTeamId` / `S.selectedTeams` — 所选团队
- `window._sx.scenarioId` — 所选场景
- `window._sx.steps / maxSteps / simRunning` — 运行状态（步进/是否在跑）
- `window._DTS.activeTrialId / trialStatus` — 试炼状态
- `S.messages` / 混沌事件 — 交互与扰动

**5 个 Tab 对事实源的消费现状**：
| Tab | 团队 | 场景 | 运行/步进 | 混沌 | 现状 |
|---|---|---|---|---|---|
| 环境空间(3D) | ✅重建agent | ✅切房间 | ✅动画/奖励 | ✅增删/置灰 | 基本联动 |
| 系统状态(仪表盘) | ❔ | — | ❔ | — | 指标是否随团队/运行变？**待查** |
| 协作·交互 | ✅拓扑+时间线(刚修) | — | ❔时间线是否随步进追加 | ✅拓扑增删 | 团队联动已补 |
| 编排管线 | — | ✅DAG(刚修) | ✅步进推进(刚修) | — | 场景/步进已补 |
| CLI | — | — | — | — | 独立，可不联动 |

**病根（为什么打地鼠）**：每个 Tab 的渲染函数各自为政，**没有统一的"上下文变了→刷新当前 Tab"入口**。改团队时只手动补了个别刷新（如 `renderTopology`），漏的就不动。切 Tab 时也只在 init 渲染过一次。

---

## 2. 设计：一个调度器把所有联动收口

### 2.1 单一事实源 + 单一刷新入口
```js
// 事实源快照（只读聚合，不新增状态）
function dtContext(){
  return {
    team: window._selectedTeamId||'',
    scenarioId: (window._sx&&window._sx.scenarioId)||'',
    steps: (window._sx&&window._sx.steps)||0,
    running: !!(window._sx&&window._sx.simRunning),
    trialId: (window._DTS&&window._DTS.activeTrialId)||'',
  };
}
// 唯一刷新入口：只刷"当前可见 Tab"，按变更类型决定刷什么
function dtRefresh(reason){         // reason: 'team'|'scenario'|'task'|'step'|'chaos'|'tab'
  var v=document.querySelector('.view-panel.active')?.id||'';
  switch(v){
    case 'view-environment':  if(reason==='team'||reason==='scenario'||reason==='tab') rebuildRoom(); break;
    case 'view-architecture': renderArchitecture(); break;                 // 仪表盘随团队/运行
    case 'view-interaction':  if(interactSubIsTopo()) renderTopology(); else renderInteractions('all'); break;
    case 'view-pipeline':     renderPipeline(); break;                     // 场景 DAG + 步进
  }
}
```

### 2.2 在事实源变化处**统一触发** `dtRefresh(reason)`
| 触发点 | reason | 现状 |
|---|---|---|
| 选团队(`toggleTeam`/`sexySelectTeam`) | `'team'` | 现只手动刷了拓扑/3D，改为统一 `dtRefresh('team')` |
| 选场景(`sexySelectScene`) | `'scenario'` | 现补了 pipeline/3D，改为 `dtRefresh('scenario')` |
| 选任务(`sexySelectTask`) | `'task'` | 无 → 补 |
| 每步(`_sx.steps=`) | `'step'` | 现只补了 pipeline，改为 `dtRefresh('step')` |
| 混沌(`_doInjectEvent`) | `'chaos'` | 现补了 3D/拓扑，纳入 `dtRefresh('chaos')` |
| 切 Tab(`switchView`) | `'tab'` | 现按 view 分支，改为末尾统一 `dtRefresh('tab')` |

> **收口效果**：以后任何 Tab 的联动都只需在 `dtRefresh` 的 switch 里加一行；事实源变化处只管喊 `dtRefresh(reason)`，不再各自补渲染 → 不再打地鼠。

---

## 3. 各 Tab 的联动契约（"应该联动成什么样"）
- **环境空间**：team→只显示该团队 agent + 场景房间；running→动画/奖励/流水线；chaos→增删/置灰（已达成，纳入调度器）。
- **系统状态(仪表盘)**：指标应反映**当前团队 + 当前运行**（会话数/步数/吞吐/评分）。**[待查+补]** loadLiveMetrics 是否带 team_id / 当前 trial。
- **协作·交互**：team→时间线&拓扑只看该团队(已补)；running/step→时间线**实时追加**该团队新消息；chaos→拓扑增删(已补)。**[补]** 步进时若在该 Tab，追加渲染时间线。
- **编排管线**：scenario→DAG；step→节点按进度推进(已补)；**[可选]** 精确节点状态需后端 step 带 task_id。
- **CLI**：独立，不纳入。

---

## 4. 验收
```
选团队A→跑演练→依次点 环境空间/系统状态/协作·交互/编排管线：
  每个 Tab 都只反映团队A + 当前运行（无 B 团队串台、无停在初始态）。
改选团队B（运行中或空闲）→ 当前可见 Tab 立即刷新为 B。
注入 离开/增援 → 3D、协作拓扑、(仪表盘计数) 三处一致。
切 Tab 来回 → 每个 Tab 都是最新态，不需手动刷新。
```

> 详细任务 + 伪代码 + [VSCode]/[人工核] 见 `docs/数字孪生联动todos.md`。
