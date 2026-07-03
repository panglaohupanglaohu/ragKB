# 数字孪生模块 优化 Plan（复核 2026-07-02）

> 复核范围：`js/digital-twin-cli.js`(2690) / `js/digital-twin-cli-3d.js`(1309) / `js/digital-twin/secs-core.js`(2633) / `js/digital-twin/director.js`(257) / `Agent-digital-twin.html`。
> 原则（对齐 CLAUDE.md）：外科式、最小改动、不加投机功能；只治真问题，风险高的标为延后。

---

## 1. 发现清单（按严重度）

| # | 发现 | 位置 | 严重度 | 处置 |
|---|---|---|---|---|
| P1 | **后台轮询不随页面可见性暂停** — 5 个 `setInterval` 页面隐藏时仍空转，持续打后端 | cli.js:20/1236/1238、director.js:226/256 | ★★★ | **本次做** |
| P2 | `syncTeam` 每 **1s** 写 DOM（纯 UI 镜像），频率偏高 | director.js:256 | ★★ | 本次做（并入 P1 门控，降频到 2s） |
| P3 | `_dtRoomMapHealth` 每 2s 诊断轮询常开 | director.js:226 | ★★ | 本次做（并入 P1 门控） |
| P4 | 30 处空 `catch{}` 吞异常，排障困难 | 三文件 | ★ | **已做（定向）**：6 处网络/状态加载路径补 `console.warn('[dt]',e)`；纯 UI 防御性 catch 保持静默 |
| P5 | `init()` 冷启动全量 render，非可见 Tab 也渲染 | cli.js:18 | ★ | **已做**：冷启动只渲染常驻区 + 默认「环境空间」Tab；architecture/interaction/pipeline 惰性渲染（进入时经 dtRefresh('tab')） |
| P6 | **右侧「协作图」不反映增/减 agent，标题 `[5v7]` 硬编码，无 twins 时空白** | secs-core `_renderCollabGraph` + HTML:1071 | ★★ | **已做（bug-088）** |

**为什么 P1 是主线**：仓库其它模块（`nav-sidebar.js`、`cost-dashboard.js`、`agent-team-config.js`、`sandbox-twin.js`）**已统一用 `document.hidden` 门控轮询**，唯独数字孪生模块漏了。这既是性能/后端压力问题，也是**一致性缺口**——补齐即与既有约定对齐，低风险、有明确先例。

---

## 2. P1/P2/P3 方案：轮询可见性门控（本次落地）

### 病灶（5 个常开轮询）
```
digital-twin-cli.js
  :20    setInterval(loadLiveMetrics, 10000)              // 指标
  :1236  setInterval(freq 采样 + renderFreqChart, 2000)   // 频率图
  :1238  setInterval(loadTeamsAndAgents+render, 30000)    // 智能体状态
digital-twin/director.js
  :226   setInterval(_dtRoomMapHealth, 2000)              // 引用断裂诊断
  :256   setInterval(syncTeam, 1000)                      // 团队标签镜像
```
页面隐藏（切到别的标签页/最小化）时全部照跑 → 无谓后端请求 + 无谓重绘。

### 改法（对齐仓库既有写法 `if(!document.hidden)fn()`）
```js
// 每个后台轮询回调首行早退
setInterval(()=>{ if(document.hidden) return; /* …原逻辑… */ }, ms);
// 重新可见时立即补一次（避免回到页面看到过期数据）
document.addEventListener('visibilitychange', ()=>{
  if(document.hidden) return;
  loadLiveMetrics(); /* + 需要即时刷新的项 */
});
```
- `syncTeam` 顺带 1000ms → 2000ms（纯 UI 镜像，2s 足够）。
- 诊断/频率图隐藏时不采样即可，无需回补。

### 验收
- 切到其它标签页：Network 面板中数字孪生的 `/tasks/stats`、`/extraction/stats`、`/teams` 轮询停止；回到页面立即恢复且刷新一次。
- 功能与门控前一致：可见时指标/频率图/智能体状态/团队标签照常更新。
- `node --check` 全绿；控制台无报错。

---

## 3. P6：右侧「协作图」反映增/减 agent（bug-088，已落地）
**病灶**：`_renderCollabGraph(twins)` 仅在评分报告返回时调一次，`if(!twins.length)return` 无数据即空白；标题 `[5v7]` 是 HTML 硬编码；不接混沌状态，故增/减 agent 不反映。
**改法**：
- 数据源优先级：报告 twins > 缓存 `_sx.lastTwins` > 当前团队 agent（回退，避免空白）。
- 叠加 `_chaosTopoState`：剔除已离开、并入增援（增援节点虚线描边），与 3D/协作拓扑同口径。
- 标题 `#secs-collab-title` 动态显示 `[实际节点数]`；空集时显示提示文案而非空白。
- 椭圆布局 rx155/ry48 适配 400×140 视窗（原 r=110 上下裁切）。
- 混沌注入 `_doInjectEvent` 末尾调 `_renderCollabGraph()` → 增/减实时反映。
- 暴露 `window._secsRenderCollab`，`init()` 冷启动占位一次。

> 说明：另有 协作·交互 Tab →「协作拓扑」(`#topo-svg`/`renderTopology`) 早已反映增/减；本次是补齐**右侧那张**协作图。

> 详细任务 + 伪代码 + [VSCode]/[人工核] 见 `docs/数字孪生优化todos.md`。
