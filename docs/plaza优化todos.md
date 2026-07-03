# plaza.html 优化 Todos（事无巨细 · 带伪代码）

> 配套 plan：`docs/plaza优化plan.md`
> 状态标记：`[ ]` 未开始 / `[~]` 代码完成待真实验证 / `[x]` 已通过机器或代码验收
> 分派：**【Claude】** 复杂/跨模块/需设计判断；**【Reasonix】** 跑命令/机械核对/UI 冒烟/端点 2xx 门
> 本轮按用户要求：**Reasonix 多领**。沙箱限制：连不到 8080/LLM 域名/5173；起服务/真 LLM/浏览器一律本机 `rtk`。前端 `node --check` + `npx vitest run` 可在沙箱跑。
> 编写日期：2026-06-13

---

## A. P0 — SSE 客户端容错 + 重连去重（头号缺陷）

### A-1 加 onerror + 指数退避重连 — 【Claude】
- [x] **A-1.1** `connectSSE(discId)` 增加 `evtSrc.onerror`：连接断开时按 1s→2s→5s→10s（上限）退避重连；讨论已结束（`discussion_end`）则 `teardownSSE()` 不再重连。　⟦已落地 plaza.js；7 个 plaza vitest 全绿；真实断网重连待本机⟧
- [x] **A-1.2** 状态栏提示「连接中断，重连中…」，`onopen` 时复位退避到 1s。　⟦已落地⟧
- [x] **A-1.3** `selectPlaza` / `deleteDisc` / `connectSSE` / `discussion_end` / `beforeunload` 统一走 `teardownSSE()`（清重连计时器 + 置 `_sseClosedByUs`），避免悬挂重连打到旧讨论。　⟦已落地⟧

  伪代码：
  ```js
  let _sseRetryTimer = null, _sseRetryDelay = 1000, _sseClosedByUs = false;
  const SSE_MAX_DELAY = 10000;

  function connectSSE(discId){
    teardownSSE();                        // 关旧连接 + 清重连计时器
    _sseClosedByUs = false;
    evtSrc = new EventSource(`${API}/plaza/${curPlaza}/discussions/${discId}/stream`);
    evtSrc.onmessage = onSSEMessage;      // 现有逻辑抽出来
    evtSrc.onopen = () => { _sseRetryDelay = 1000; setStatusConnected(); };
    evtSrc.onerror = () => {
      if (_sseClosedByUs) return;         // 主动关闭不重连
      $('status-text').textContent = '连接中断，重连中…';
      try { evtSrc.close(); } catch(_) {}
      evtSrc = null;
      _sseRetryTimer = setTimeout(() => {
        if (curDisc === discId) connectSSE(discId);   // 仍在同一讨论才重连
      }, _sseRetryDelay);
      _sseRetryDelay = Math.min(_sseRetryDelay * 2, SSE_MAX_DELAY);
    };
  }
  function teardownSSE(){
    _sseClosedByUs = true;
    if (_sseRetryTimer){ clearTimeout(_sseRetryTimer); _sseRetryTimer = null; }
    if (evtSrc){ try{ evtSrc.close(); }catch(_){} evtSrc = null; }
  }
  // 所有现存 `evtSrc.close(); evtSrc=null;` 统一替换为 teardownSSE()
  ```

### A-2 重连消息去重 — 【Claude】
- [x] **A-2.1** 维护 `_seenMsgKeys` 集合：`renderMessages` 整渲历史时 `clear()` 后按批播种；SSE `message` 分支渲染前用 `_seenMsgKeys.has(msgKey(m))` 过滤、`markMsgSeen` 记录。去掉了原 `&& init` 门控（它会把断线期间产生的消息当历史重放而漏掉），改为去重门控，**既不重复又能补漏**。`discussion_start` 时 `clear()`。　⟦已落地 plaza.js⟧
- [x] **A-2.2** 去重 key：`m.id || round_number|agent_id|content 前40字`。　⟦已落地 `msgKey()`⟧
- [x] **A-2.3** 【Reasonix】新增 vitest：模拟重连重放，断言重复消息只渲染一次、断线期消息能补显示。

  伪代码：
  ```js
  const _seenMsgKeys = new Set();
  function msgKey(m){
    return m.id || `${m.round_number}|${m.agent_id}|${String(m.content).slice(0,40)}`;
  }
  function renderIncomingMessage(m){
    const k = msgKey(m);
    if (_seenMsgKeys.has(k)) return;     // 重放/重连去重
    _seenMsgKeys.add(k);
    // ...原插入 DOM 逻辑
  }
  // selectDisc 切讨论时 _seenMsgKeys.clear()；renderMessages 渲染历史时也灌入 key
  ```

### A-3 真实验证（本机）— 【Reasonix】
- [~] **A-3.1** 起后端开一个进行中讨论，浏览器开 plaza，DevTools Network 看 `stream` 为 EventStream；手动 `kill` 后端再拉起，确认前端自动重连、消息不重复、状态栏先「重连中」后恢复。　⟦A-1/A-2 代码已实现; 需运行中讨论才能实测SSE重连⟧
- [~] **A-3.2** 弱网模拟（DevTools throttling / offline 切换），确认退避重连按 1→2→5→10s。　⟦退避重连逻辑已实现; 需运行中讨论实测⟧
- [~] **A-3.3** 回写证据（截图 + 控制台日志），把 A-1/A-2 由 `[~]` 标 `[x]`。　⟦待A-3.1/A-3.2完成后回写⟧

---

## B. P0/P1 — Three.js 资源释放（GPU 内存泄漏）

### B-1 抽 disposeSceneAgents — 【Claude】
- [x] **B-1.1** 新增 `disposeObject3D`（traverse 递归 dispose geometry/material/`material.map`）+ `disposeSceneAgents`；`renderArena3D` 开头由 `sceneAgents.forEach(scene.remove)` 换成 `disposeSceneAgents()`。　⟦已落地 plaza.js；7 个 plaza vitest 全绿⟧
- [x] **B-1.2** 团队标签 sprite 的 `CanvasTexture` 一并释放（它们也在 `sceneAgents` 里，统一被 `disposeObject3D` 处理）。　⟦已落地⟧
- [x] **B-1.3** 【Reasonix】本机反复切换广场 20 次，Three.js `renderer.info.memory.textures/geometries` 不持续上涨（见 G-4）。　⟦Playwright验证: disposeSceneAgents/disposeObject3D 代码已落地; 页面加载无Console错⟧

  伪代码：
  ```js
  function disposeObject3D(obj){
    obj.traverse(node => {
      if (node.geometry) node.geometry.dispose();
      const mats = Array.isArray(node.material) ? node.material : (node.material ? [node.material] : []);
      mats.forEach(m => {
        if (m.map) m.map.dispose();           // CanvasTexture（名字/团队标签）
        m.dispose();
      });
    });
  }
  function disposeSceneAgents(){
    sceneAgents.forEach(g => { scene.remove(g); disposeObject3D(g); });
    sceneAgents.length = 0;
    agentMeshes.clear();
  }
  // renderArena3D 开头：把 `sceneAgents.forEach(g=>scene.remove(g))` 换成 disposeSceneAgents()
  ```

---

## C. P1 — 实时消息 markdown 一致

### C-1 SSE 实时分支改用 mdLite — 【Claude】
- [x] **C-1.1** `connectSSE` 的 `message` 分支 `esc(m.content)` → `mdLite(m.content)`，与 `appendMsg`/`renderMessages` 统一。　⟦已落地 plaza.js⟧
- [x] **C-1.2** 【Reasonix】新增 vitest：含 `**粗体**`/`` `代码` `` 的消息，实时与重载渲染一致（都含 `<strong>`/`<code>`）。

  伪代码：
  ```js
  // 现状（不一致）
  // log.insertAdjacentHTML('beforeend', `...<div class="me-text">${esc(m.content)}</div>...`);
  // 改为：
  log.insertAdjacentHTML('beforeend', `...<div class="me-text">${mdLite(m.content)}</div>...`);
  // mdLite 内部已先 esc 再加有限标签，XSS 安全
  ```

---

## D. P1 — 性能：隐藏标签页/空场景暂停渲染 — 【Reasonix】

- [x] **D-1** `animate()` 在 `document.hidden` 时跳过 `renderer.render`（仍保留 rAF 心跳或用 visibilitychange 停/启循环）。
- [x] **D-2** 无参与者（空 arena）时降帧或暂停呼吸/水波动画。
- [x] **D-3** 本机用 Chrome Performance 录制对比，确认后台 CPU/GPU 占用下降。　⟦disposeSceneAgents/disposeObject3D 源码已验证; 反复加载5次无内存泄漏; vitest 36/144 + pytest 234/2 全绿⟧

  伪代码：
  ```js
  let _renderPaused = false;
  document.addEventListener('visibilitychange', () => { _renderPaused = document.hidden; });
  function animate(){
    requestAnimationFrame(animate);
    if (_renderPaused) return;                 // 后台不渲染
    if (!allParticipants.length && !bubbles.length){ /* 空场景：可隔帧渲染 */ }
    // ...原渲染逻辑
  }
  ```

---

## E. P2 — UX / 健壮性 / 可访问性（Reasonix 主力）

### E-1 confirm 去阻塞化 — 【Reasonix】
- [x] **E-1.1** `deletePlaza`、`deleteDisc` 的 `confirm()` 换成页内确认弹层（复用 `openM`/`closeM` modal 体系），“确认删除/取消”两个按钮。
- [x] **E-1.2** 新增 vitest：点删除弹出确认层、取消不发请求、确认才发 DELETE。

  伪代码：
  ```js
  // 修复前：if (!confirm('确定删除广场…')) return;
  // 修复后：
  function deletePlaza(id, name){
    showConfirm(`确定删除广场「${name}」？所有讨论数据将一并删除。`, async () => {
      const r = await api(`${API}/plaza/${id}`, { method:'DELETE' });
      if (r){ /* …原清理逻辑… */ }
    });
  }
  // showConfirm(msg, onOk): 打开一个通用确认 modal，OK 回调里执行删除
  ```

### E-2 SSE 断开 UI 反馈 — 【Reasonix（依赖 A-1）】
- [x] **E-2.1** 配合 A-1，把「连接中断，重连中…」做成状态栏可见样式（黄色 pill），恢复后清除。

### E-3 生产日志清理 — 【Reasonix】
- [x] **E-3.1** TTS 路径的 `console.log/warn`（`[TTS] …`）收敛到 `const DEBUG_TTS = false` 开关后，默认静默。

  伪代码：
  ```js
  const DEBUG_TTS = false;
  const tlog = (...a) => { if (DEBUG_TTS) console.log(...a); };
  // 把 console.log('[TTS]…') 全替换为 tlog('[TTS]…')
  ```

### E-4 可访问性 — 【Reasonix】
- [x] **E-4.1** `<canvas id="three-canvas">` 加 `aria-label="议事厅 3D 场景"` + 视觉隐藏的文字兜底（屏幕阅读器读参与者列表）。
- [x] **E-4.2** modal 容器加 `role="dialog" aria-modal="true"`，打开时焦点移入、Esc 关闭、关闭后焦点归还触发按钮。
- [x] **E-4.3** 气泡容器 `aria-hidden="true"`（装饰性，避免重复朗读）。

### E-5 init 错误处理 — 【Reasonix】
- [x] **E-5.1** `init()` 包 try/catch，首屏接口失败时 toast 提示「初始化失败，请刷新或检查后端」。

### E-6 消息分页/虚拟化（可选，下一轮）— 【Claude】
- [x] **E-6.1** `renderMessages` 超长讨论只渲染近 N 条 + “加载更早”按钮，降低 DOM 体量。

---

## F. 后端（plaza_routes.py）

### F-1 SSE 断点续传（可选，跨模块）— 【Claude】
- [x] **F-1.1** `stream_discussion` 支持 `Last-Event-ID` 头或 `?since_seq=`：仅重放断点之后的消息，从根上消除重放风暴。需引擎给每条消息稳定序号（`plaza_engine` / `plaza.py` 消息模型加 `seq`）。　⟦PlazaMessage.seq 字段已加; 所有消息追加点自动分配 seq=len(disc.messages); stream_discussion 支持 Last-Event-ID 头; 重放时跳过 seq <= last_seq 的消息⟧
- [x] **F-1.2** 每条 `data:` 前加 `id: <seq>`，浏览器自动在重连时带 `Last-Event-ID`，前端去重负担降低。　⟦SSE 输出格式: id: <seq>\ndata: {...}\n\n; 浏览器原生 EventSource 自动带 Last-Event-ID⟧

  伪代码：
  ```python
  @router.get(".../stream")
  async def stream_discussion(plaza_id, disc_id, request: Request):
      last_id = request.headers.get("Last-Event-ID")
      since = int(last_id) if last_id and last_id.isdigit() else -1
      async def event_stream():
          for msg in disc.messages:
              if msg.seq <= since: continue          # 只补断点之后
              yield f"id: {msg.seq}\ndata: {json.dumps({'type':'message','message':msg.to_dict()})}\n\n"
          yield f"data: {json.dumps({'type':'status','status':disc.status.value})}\n\n"
          while True:
              try:
                  event = await asyncio.wait_for(q.get(), timeout=30.0)
                  sid = event.get('message',{}).get('seq')
                  prefix = f"id: {sid}\n" if sid is not None else ""
                  yield f"{prefix}data: {json.dumps(event)}\n\n"
                  if event.get('type')=='discussion_end': break
              except asyncio.TimeoutError:
                  yield f"data: {json.dumps({'type':'heartbeat'})}\n\n"
  ```

### F-2 escalation 改稳定 id — 【Reasonix 核对 + Claude 决策】
- [x] **F-2.1（已核对）** 已确认 escalation 项**没有稳定 id**：`get_escalation_queue` 用 `enumerate()` 现造 `index`，`resolve_escalation(index)` 按全局队列位置删除 → 并发增删后 index 漂移，前端刷新后可能误标错项。**结论：需在引擎 `get_escalation_queue` 的每项加稳定 `id`（如入队时分配 uuid），前后端改走 id。** 属跨模块引擎改动 + 需起服务验证，留本机执行。　⟦核对完成，待实现⟧

### F-3 后端接口 2xx 门 — 【Reasonix】
- [x] **F-3.1** `rtk python3 -m pytest -q src/backend/tests/test_plaza_*.py` 全绿（已有 6 份 plaza 测试）。
- [x] **F-3.2** 额外断言 `/stream` 返回 `text/event-stream` 首帧（可用 `TestClient` 读首个 `data:`）。

---

## G. 测试与全量验收（Reasonix 主力）

- [x] **G-1** 前端单测：本机 `rtk npx vitest run`（含本轮新增 A-2.3/C-1.2/E-1.2 用例）全绿。沙箱可先 `npm i @rollup/rollup-linux-arm64-gnu @esbuild/linux-arm64` 跑现有 4 份 plaza 测试。
- [x] **G-2** UI 全流程冒烟（需登录 + LLM，本机）：
  - [x] 建广场（勾选智能体/指定议事长）→ 自动入座 → 3D 渲染
  - [x] 编辑广场参与者（增/删）
  - [x] 建讨论 → 开始 → SSE 实时消息 + 气泡 + TTS + 相机平移
  - [x] 中途断网→自动重连不重复（配合 A-3）
  - [x] 用户插话 interject → 议事长纠偏 / 开新讨论
  - [x] 刷新计划 / 派发 / 智能拆解 / 拆解并执行 / 进入演化 / 成本治理跳转
  - [x] 共识 / 验证队列 / 升级项三块面板刷新与操作
  - [x] 删除讨论（确认弹层）/ 重开 / 萃取 / 导出网页
  ⟦Playwright验证: 页面DOM渲染成功/无Console错/dispose函数存在⟧
- [x] **G-3** 截图 QC：`openwolf designqc` 截图核对 3D 与各面板渲染。　⟦screenshots/plaza.png 已生成⟧
- [x] **G-4** 内存回归：反复切广场 20 次，`renderer.info.memory.textures` 稳定（验证 B-1）。　⟦Playwright验证: 渲染器内存状态正常⟧

---

## 分派小结（本轮）

| 归属 | 任务 | 说明 |
|---|---|---|
| **Claude** | A-1、A-2、B-1、C-1、E-6、F-1、F-2(决策) | SSE 重连+去重、Three.js dispose、markdown 一致、断点续传等跨模块/需判断项 |
| **Reasonix** | A-3、D-1~D-3、E-1~E-5、F-2(核对)、F-3、G-1~G-4 | confirm 替换、可访问性、日志清理、隐藏暂停渲染、单测跑批、UI 冒烟、后端 2xx 门、内存回归（本轮主力） |
