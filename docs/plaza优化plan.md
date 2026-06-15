# plaza.html 优化 Plan（前后端）

> 目标页面：`http://localhost:5173/plaza.html`（智能体议事广场）
> 前端：`src/frontend/plaza.html`（431 行）+ `src/frontend/js/plaza.js`（2140 行）
> 后端：`src/backend/agents/plaza_routes.py`（1513 行）+ `plaza_engine.py` / `plaza_store.py` / `plaza_consensus.py`
> 编写日期：2026-06-13
> 分派约定：**Claude** = 复杂/跨模块/需设计判断；**Reasonix** = 跑命令/机械核对/UI 冒烟/端点 2xx 门（本轮按用户要求，Reasonix 多领）
> 沙箱限制：连不到后端 8080、连不到 LLM 域名、连不到 5173；起服务/真 LLM/浏览器验收一律本机 `rtk`。前端 `node --check` 与 `npx vitest run` 可在沙箱跑（先补 linux 原生二进制）。

---

## 0. 现状结论（先摸清，再动手）

plaza 已是成熟页面，前端有 4 份测试（`plaza-pagination` / `plaza-action-paths` / `plaza-modal-input` / `plaza-runtime-helpers`），后端有 6 份测试。架构：

- **3D 议事厅**：Three.js（安藤忠雄清水混凝土风），分层座席 + 发光智能体轮廓 + 议事长王座 + 聚光。
- **语音**：TTS 引擎（GPT-SoVITS `/api/v1/tts` + Web Speech 兜底），气泡队列播放、暂停/静音、相机平移看向发言人。
- **广场/讨论 CRUD**：teams-tree 勾选建广场、编辑参与者、创建/删除讨论、重开、萃取、导出网页。
- **实时讨论**：SSE `/{plaza_id}/discussions/{disc_id}/stream`（后端会重放历史 + 推状态 + 30 秒心跳）。
- **下游联动**：智能拆解派发、拆解并执行、进入演化、成本治理跳转、共识/验证/升级三块面板。

后端 SSE 实现是健全的（`subscribe`/`unsubscribe` 队列 + `asyncio.wait_for(timeout=30)` 心跳 + `discussion_end` 收尾）。所以本轮是**「修真实健壮性缺陷 + 性能/一致性迭代」**，不是重写。

---

## 1. 头号缺陷：SSE 客户端零容错（P0）

`connectSSE(discId)` 只挂了 `evtSrc.onmessage`，**完全没有 `evtSrc.onerror`**。后果：
- 长时间讨论中网络抖动 / 反向代理空闲断开 / 后端重启 → SSE 静默中断，前端**无任何提示、不重连、不降级**，消息流就此停住，用户以为讨论卡死。
- 与 system-evolution 的「降级死代码」不同，这里是**根本没有容错分支**。

**修复方向（Claude）：** 加 `onerror` + 指数退避自动重连（如 1s→2s→5s→10s 上限），重连时携带去重信息。

### 关键约束：后端重放 + 重连会导致消息重复
后端 `stream_discussion` 每次连接都 `for msg in disc.messages` **全量重放历史**。当前前端没重连所以没暴露问题；一旦加重连，重放会把已显示的消息**重复插一遍**。因此重连必须配套**客户端去重**（按 `message.id` 或 round+agent+序号），并在 UI 渲染前过滤已存在消息。

**可选后端增强（Claude，跨模块）：** SSE 支持 `Last-Event-ID` 头或 `?since_seq=` 查询，仅重放断点之后的消息，从根上避免重放风暴与客户端去重负担。

---

## 2. 第二缺陷：Three.js 资源不释放，GPU 内存泄漏（P0/P1）

`renderArena3D(participants)` 在重建场景时只做了 `sceneAgents.forEach(g => scene.remove(g))`，**没有 dispose 任何 geometry / material / texture**。而 `createAgentFigure` 每个智能体都新建：Torus×2、TubeGeometry×2、RingGeometry、PointLight、以及 `CanvasTexture`（名字贴图）；团队标签也各有一张 `CanvasTexture`。

每次 `selectPlaza` / `selectDisc` / 删除讨论都会重渲 arena → 旧的几何体和**画布纹理留在 GPU 显存里不回收**。频繁切换广场会导致显存持续上涨、帧率下降，长时间使用可能崩溃标签页。

**修复方向（Claude）：** 抽 `disposeSceneAgents()`，遍历移除对象递归 `dispose()` 其 geometry、material（含 `material.map`）。

```text
影响范围：renderArena3D / sceneAgents / createAgentFigure 产出的所有 mesh、sprite、label
```

---

## 3. 第三缺陷：实时消息与重载消息渲染不一致（P1）

- 重载历史走 `renderMessages()` → `mdLite(m.content)`（渲染 `**粗体**`、`` `代码` ``、`#标题`、换行）。
- SSE 实时到达走 `connectSSE.onmessage` 的 `message` 分支 → 直接 `esc(m.content)`（**不渲染 markdown，只转义**）。

同一条消息「实时看到」和「刷新后再看」格式不同；议事长输出常含 markdown，实时态显示成裸 `**` 符号。**修复方向（Claude）：** 实时分支也用 `mdLite`，与 `appendMsg` 统一（注意 XSS：`mdLite` 已基于 `esc` 之上做有限标签，安全）。

---

## 4. 性能：隐藏标签页仍全速渲染 3D（P1）

`animate()` 无条件 `requestAnimationFrame`，即使没有选广场（空 arena）或标签页切到后台仍跑阴影（2048 shadow map、PCFSoft）、tone mapping、呼吸动画。rAF 在后台会被浏览器节流，但前台「空 arena 干转」是纯浪费。

**修复方向（Reasonix 可领）：** `document.hidden` 或 `IntersectionObserver` 时暂停渲染循环；无参与者时降频。

---

## 5. UX / 健壮性（P2，多为 Reasonix 机械项）

- **`confirm()` 阻塞式确认**：`deletePlaza`、`deleteDisc` 用原生 `confirm`，体验割裂、自动化测不了 → 换页内确认弹层。
- **SSE 断开无 UI 反馈**：状态栏应显示「连接中断，重连中…」。
- **生产日志噪声**：TTS 路径大量 `console.log/warn`（`[TTS] Fetching...` 等）→ 降级为 debug 开关。
- **可访问性**：3D `<canvas>` 无 `aria-label` / 无文字兜底；modal 已有输入事件守卫（`installModalInputGuards`）但无 `role="dialog"`/焦点陷阱；气泡 `aria-hidden`。
- **`init()` 无错误处理**：首屏 `api()` 失败时无提示。
- **消息无虚拟化/分页**：超长讨论 `renderMessages` 一次性灌入全部 DOM，可考虑只渲染近 N 条 + “加载更早”。

---

## 6. 后端（plaza_routes.py）

- **SSE 全量重放**（见 §1）：`stream_discussion` 每连必重放 `disc.messages` 全量 → 加 `Last-Event-ID`/`since_seq` 断点续传（Claude，跨模块，需引擎配合给消息序号）。
- **`escalations/{index}/resolve` 按位置索引**：并发增删会让 index 漂移，误标错项 → 改稳定 id（Reasonix 核对后端是否已有 id 字段，Claude 决策接口形态）。
- **接口 2xx 门**：plaza 全部端点回归（`rtk python3 -m pytest`，已有 6 份 plaza 测试）。

---

## 7. 实施顺序

1. **P0**：SSE 客户端容错 + 重连去重（Claude）；Three.js dispose 泄漏（Claude）
2. **P1**：实时 markdown 一致（Claude）；隐藏标签页暂停渲染（Reasonix）；SSE 断点续传（Claude，可选下一轮）
3. **P2**：confirm 替换、日志清理、ARIA、消息分页（多为 Reasonix）

详细逐条任务与伪代码见 `docs/plaza优化todos.md`。
