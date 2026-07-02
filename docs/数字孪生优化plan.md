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
| P4 | 30 处空 `catch{}` 吞异常，排障困难 | 三文件 | ★ | 延后：全量改动面大、易误伤；仅在后续定位具体 bug 时按需补日志 |
| P5 | `init()` 一次性全量 render + 各 tab 进入再 render，存在少量重复渲染 | cli.js:18 | ★ | 延后：dtRefresh 已收口大部分；收益小于回归风险 |

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

## 3. 延后项（记录理由，不本次做）
- **P4 空 catch**：一次性全量替换风险高、易误伤（很多是"存不到就算了"的合理静默）。约定改为：**定位到具体 bug 时**再在该处补 `console.warn`/日志，而非批量翻新。
- **P5 重复渲染**：`dtRefresh` 调度器已把"上下文变→刷新当前 Tab"收口；剩余重复主要在 `init()` 冷启动一次，收益极小、回归风险大于收益，暂不动。

> 详细任务 + 伪代码 + [VSCode]/[人工核] 见 `docs/数字孪生优化todos.md`。
