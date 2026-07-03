# sandbox-twin.html 前端剩余工作交接

> 接手人：M3
> 后端已就绪（`sandbox/api.py` + `sandbox/twin_loop.py` + `sandbox/orchestrator.py` 改造完成）
> 任务：把下面 10 项全部清掉，让前端真的能跑、真的能看、真的能停下来。

---

## 一、背景

后端上一轮已经升级过：

- `twin_loop.py` 内部维护 `_stop_events: Dict[str, asyncio.Event]`，每步检查并支持优雅中断
- `POST /api/v1/sandbox/sessions/{id}/stop` 新增停止端点
- SSE `step` 事件新增 `total_steps` 和 `agent_roles` 字段
- SSE `complete` 事件新增 `session_id` 和 `total_steps_planned`
- `POST /sessions/{id}/run` 状态校验放宽为 `CREATED | PAUSED | COMPLETED`

前端 (`src/frontend/sandbox-twin.html` + `css/sandbox-twin.css` + `js/sandbox-twin.js`) 拿到这些能力后**还没接上**。下面按 P0 → P1 → P2 排好，M3 按顺序打。

---

## 二、P0 Bug 修复（4 个，先打）

### Bug 1 — 孤儿代码：resetCollabGraph 重复闭合

**文件**：`src/frontend/js/sandbox-twin.js`
**行号**：480–485
**症状**：
```js
}     // 479 行，函数正常结束
    document.querySelectorAll('.collab-node-circle').forEach(function (c) {  // 480
      c.classList.add('inactive');
    });
    updateCollabMetrics();
    showToast('协作图已重置', 'info');
  }   // 485 — 第二个函数开括号都没有
```
**修法**：直接删掉 480–485 那 6 行，479 行的 `}` 之后紧接 `// ── API Helpers ──` 块。

---

### Bug 2 — bindRuntimeBar 选择器选不到元素

**文件**：`src/frontend/js/sandbox-twin.js`
**行号**：605（`bindRuntimeBar` 函数体）
**症状**：JS 里 `document.querySelector('.runtime-bar__title')` 找不到元素。HTML 上一轮把类名改成了 `id="runtime-bar__toggle"`。
**修法**：把选择器换成 `#runtime-bar__toggle`，并把函数里的 `titleEl` / `title` 逻辑都改用 toggle 按钮的事件：
```js
const btn = document.getElementById('runtime-bar__toggle');
if (!btn) return;
btn.addEventListener('click', toggleRuntimeDrawer);
```
（`toggleRuntimeDrawer` 已存在，复用。）

---

### Bug 3 — 沙箱 ID 条启动后未填充

**文件**：`src/frontend/sandbox-twin.html` 第 138 行附近，运行时条 (`runtime-bar`) 启动后没把当前 session id 写进条上。
**症状**：用户启动一次仿真，整个 `runtime-bar` 上的"沙箱会话 id"一直显示空白。
**修法**：
1. 在 `runtime-bar` 里加一个挂载点：
   ```html
   <span class="runtime-bar__sandbox-id" id="runtime-bar__sandbox-id">—</span>
   ```
2. 在 JS 的 `startSimulation` / `subscribeStream` 入口（拿到 `sessionId` 后）加：
   ```js
   const idEl = document.getElementById('runtime-bar__sandbox-id');
   if (idEl) idEl.textContent = sessionId;
   ```
3. 复制 sandbox id 加一个 `📋` 小按钮调用 `navigator.clipboard.writeText(sessionId)`。

---

### Bug 4 — `loadSessionDetail` 函数未定义

**文件**：`src/frontend/sandbox-twin.html` 第 138 行
**症状**：
```html
<button class="btn btn-sm" onclick="loadSessionDetail()" id="btn-refresh-session">↻ 概要详情</button>
```
**修法**：在 `src/frontend/js/sandbox-twin.js` 末尾、`window.xxx = xxx` 那一段（1165 行附近）注册一个新函数：
```js
async function loadSessionDetail() {
  const sid = getCurrentSessionId();   // 你需要这个 getter，自己维护一下
  if (!sid) { showToast('请先选择或启动一个 session', 'warn'); return; }
  try {
    const detail = await apiFetch(`/sessions/${sid}`);
    renderSessionDetail(detail);       // 你来定怎么画，最少把 id/status/total_steps/agent_roles 摆出来
  } catch (e) {
    showToast('加载 session 失败: ' + e.message, 'error');
  }
}
window.loadSessionDetail = loadSessionDetail;
```
（如果 `getCurrentSessionId` 没有，临时存一个全局 `window._currentSessionId` 也行。）

---

## 三、P1 缺失功能（6 个，后端已经发了字段，前端没消费）

### 5. 消费 SSE `total_steps` → 进度条

**后端发了**（SSE `step` 事件 payload）：
```json
{ "type": "step", "current": 3, "total_steps": 12, ... }
```
**前端要做的**：
1. 在 `runtime-bar` 区域加一个 `<progress>` 或自绘条：
   ```html
   <progress id="runtime-bar__progress" value="0" max="100"></progress>
   ```
2. SSE `step` 处理分支里（大致在 770 行附近）：
   ```js
   if (data.total_steps) {
     const pct = Math.min(100, Math.round((data.current / data.total_steps) * 100));
     document.getElementById('runtime-bar__progress').value = pct;
   }
   ```
3. `complete` 事件里把进度条置 100，4 秒后归 0。

---

### 6. 消费 SSE `agent_roles` → 协作图动态建模

**后端发了**（SSE `step` 事件 payload）：
```json
{ "agent_roles": { "planner": "planner", "executor": "executor-2", ... } }
```
**现状**：JS 里有 `function mapAgentId(agentId)`（809 行）做硬匹配（agent_0 → planner、agent_1 → coordinator…）。
**修法**：
1. 维护一个 `currentRoleMap: Record<string, string>` 变量。
2. SSE `step` 收到 `agent_roles` 时：
   ```js
   if (data.agent_roles) {
     currentRoleMap = data.agent_roles;     // 后端权威，覆盖前端默认
     rebuildCollabGraphFromRoles(currentRoleMap);
   }
   ```
3. 把 `mapAgentId` 改成查 `currentRoleMap`：
   ```js
   function mapAgentId(agentId) {
     if (currentRoleMap[agentId]) return currentRoleMap[agentId];
     // 后端没发就退回硬匹配（兜底）
     return legacyMapAgentId(agentId);
   }
   ```
4. `rebuildCollabGraphFromRoles` 复用 `initCollabGraph` 的渲染逻辑 + 新的 role list 重画节点和边。

---

### 7. Pipeline 状态点不更新

**现状**：`sandbox-twin.html` 里的 4 层流水线（L1 MADTwin / L2 SOP / L3 仿真 / L4 评价）静态。
**后端数据**：`/sessions/{id}` 详情里能拿到每层状态、SOP 数量、当前 step 进度。
**前端要做**：
1. 给 4 个流水线节点加 `id`：`pipeline-l1` `pipeline-l2` `pipeline-l3` `pipeline-l4`。
2. 每个节点上加一个状态徽章（`pending` / `running` / `done` / `error`）。
3. SSE `step` 时根据 `step_index` 推算当前层：
   ```js
   const layers = ['l1', 'l2', 'l3', 'l4'];
   const cur = layers[Math.min(3, Math.floor(data.current / (data.total_steps / 4)))];
   layers.forEach(l => {
     const el = document.getElementById('pipeline-' + l);
     el.classList.remove('running', 'done');
     if (l === cur) el.classList.add('running');
     if (layers.indexOf(l) < layers.indexOf(cur)) el.classList.add('done');
   });
   ```
4. `complete` 时把 4 个全置 `done`。

---

### 8. L1 Agent 网格静态

**现状**：`sandbox-twin.html` 里的 L1 区域（数字孪生 agent 网格）写死 5×5 占位。
**修法**：
1. 给网格容器加 `id="l1-agent-grid"`。
2. `loadStats()` 或新的 `loadDigitalTwinSnapshot()` 拉到 agent 列表后清空再渲染：
   ```js
   const grid = document.getElementById('l1-agent-grid');
   grid.innerHTML = '';
   agents.forEach(a => {
     const cell = document.createElement('div');
     cell.className = 'l1-agent-cell';
     cell.dataset.role = a.role;
     cell.innerHTML = `<span class="l1-agent-cell__name">${a.name}</span><span class="l1-agent-cell__role">${a.role}</span>`;
     grid.appendChild(cell);
   });
   ```
3. 加一个 `loadDigitalTwinSnapshot()`，从后端取（如果没有专门的端点，调 `GET /api/v1/agents` 或 `GET /stats` 然后从 `digital_twin` 字段拿）。

---

### 9. session 历史条目点击无响应

**现状**：`addSessionToHistory` 把 session 推进列表，但条目只是 `<div>`，点了没反应。
**修法**：
1. 渲染条目时挂 click handler：
   ```js
   item.addEventListener('click', () => {
     window._currentSessionId = item.dataset.sessionId;
     loadSessionDetail();   // 复用 Bug 4 新加的函数
   });
   item.style.cursor = 'pointer';
   ```
2. 加 hover 态 CSS（`css/sandbox-twin.css`）：
   ```css
   .session-history__item:hover { background: var(--bg-hover, rgba(0,0,0,0.04)); }
   ```

---

### 10. 演练历史改成走后端

**现状**：`sessionHistory` 数组是纯前端内存，关页面就丢。
**修法**：
1. 找后端的 `GET /api/v1/sandbox/sessions` 端点（详情见 `docs/SECSOptimize.md` 第 2 节），拉真实历史。
2. 新建 `async function loadSessionHistoryFromBackend()`：
   ```js
   const list = await apiFetch('/sessions');   // 不带 id 走列表
   sessionHistory = list.map(s => ({
     id: s.session_id, steps: s.total_steps, score: s.last_score, status: s.status
   }));
   renderSessionHistory();
   ```
3. `loadStats()` 里同时调一次。
4. 启动新 session 后别只 push 本地数组，先 `await apiFetch(...)` 然后再 reload。

---

## 四、验证清单

M3 改完，逐项验证：

- [ ] 浏览器 console 0 error 0 warning
- [ ] 点"启动仿真"后 `runtime-bar__sandbox-id` 立刻显示 id
- [ ] 仿真过程中 progress 条从 0 平滑涨到 100
- [ ] 协作图节点名字跟后端发的 `agent_roles` 一致（不是写死的 planner/coordinator/...）
- [ ] 4 层流水线有 running 态在动
- [ ] L1 agent 网格是真数据，不是 5×5 占位
- [ ] 点历史里任一条会跳到 `loadSessionDetail` 显示该 session
- [ ] 刷新页面历史还在（不是丢）
- [ ] 仿真进行中点停止（后端 /stop）能断

---

## 五、参考文档

- 后端改造细节 + API 完整列表：`docs/SECSOptimize.md`
- 样式 token & 现有协作图组件：`src/frontend/css/sandbox-twin.css`
- SSE payload 完整 schema：`src/backend/sandbox/api.py`（`step` / `complete` 事件附近）

---

**预计工作量**：6 ~ 8 个文件改动，~300 行 JS / ~50 行 HTML / ~30 行 CSS。
**风险点**：P1 第 6 项 `rebuildCollabGraphFromRoles` 需要复用 `initCollabGraph` 逻辑，别重写一份，提取公共函数 `renderCollabGraph(roles, edges)`。
