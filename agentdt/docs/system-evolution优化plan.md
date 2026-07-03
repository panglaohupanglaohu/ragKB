# system-evolution.html 优化 Plan

> 目标页面:`http://localhost:5173/system-evolution.html`
> 前端:`src/frontend/system-evolution.html` + `src/frontend/js/system-evolution.js`(1909 行)
> 后端:`src/backend/agent_team_api.py`(`/api/v1/agent-teams/evolution/*`)+ `src/backend/channels/system_evolution.py`(引擎)
> 编写日期:2026-06-13
> 分派约定:**Claude** = 复杂/跨模块/需设计判断;**Reasonix** = 跑命令/机械核对/UI 冒烟/端点 2xx 门(本轮按用户要求,Reasonix 多领)

---

## 0. 现状结论(先摸清,再动手)

`system-evolution.js` 头部已标注 **「v2 — Optimized」**,经逐函数核对,早前 codebuddy plan(`.codebuddy/plans/system-evolution-optimization_802df068(未完成).md`)列的大部分项**已经落地**:

| 优化项 | 状态 | 证据(函数/位置) |
|---|---|---|
| `_panelCache` 缓存层 + TTL | ✅ 已实现 | `_panelCache` / `cacheGet` / `cacheSet` / `cacheClear` |
| `safeFetch` 统一错误封装(request_id) | ✅ 已实现 | `safeFetch` / `formatError` / `_nextRequestId` |
| 三态渲染(加载/错误/空) | ✅ 已实现 | `showSkeleton` / `hideSkeleton` / `renderError` / `renderEmpty` |
| RatchetAnimator 统一动画 | ✅ 已实现 | `RatchetAnimator` 对象 |
| 条目表头排序 | ✅ 已实现 | `sortItems` / `renderSortIndicator` / `thClick` |
| 规则搜索过滤 | ✅ 已实现 | `_ruleSearchTerm` / `renderRules` |
| 审计轨迹分页加载 | ✅ 已实现 | `_trailOffset` / `loadTrail(reset)` / `trail-more` |
| 趋势 SVG 折线图 | ✅ 已实现 | `renderTrendChart` / `renderRatchetLedgerCurve` |
| 演化实验室步进器 per-skill 状态 | ✅ 已实现 | `_evolveStepperState`(Map) + `Object.defineProperty` 路由 |

所以本轮**不是从零优化**,而是**「修真实缺陷 + 下一轮迭代」**。

---

## 1. 头号缺陷:实时更新整条链路是死的(P0)

这是本次最重要的发现,影响「实时刷新关键指标」这个核心卖点。

**根因有两处,叠加导致实时更新完全不生效:**

1. **后端缺端点。** 前端 `_startSSE()` 连接 `${EVP}/stream`(即 `/api/v1/agent-teams/evolution/stream`),但 `agent_team_api.py` **从未注册该路由**(plaza、skill-extract 有 SSE,evolution 没有)。结果:`EventSource` 必然收到 404 → 触发 `onerror`。
   - 验证:`grep -rn '/stream' src/backend` 在 evolution 相关文件中无任何 SSE 端点。

2. **前端轮询降级逻辑是死代码。** `_sseSource.onerror` 里的降级条件是 `if (!_ssePollTimer && _ssePollActive && ...)`,而 `_ssePollActive` 初始为 `false`,只有 `_fallbackPoll()` 会置 `true`,但 `_fallbackPoll()` 仅在 `new EventSource(...)` **构造抛异常**的 `catch` 分支调用。404/断线走的是 `onerror`(构造不抛异常)→ 永远进不去降级分支 → **轮询永不启动**。

**净效果:SSE 404 + 轮询不启动 = 概览页 KPI 永远不会自动刷新,只能手动「刷新」。**

### 修复方案(已由 Claude 落地代码部分)

- **前端**(已改):`onerror` 内改为 `_closeSSE(); _fallbackPoll();`,`_fallbackPoll()` 自带 `!_ssePollTimer` 去重,首次失败即可正确降级为 30 秒轮询。
- **后端**(已新增):在 `agent_team_api.py` 增加 `GET /evolution/stream`,`StreamingResponse(media_type="text/event-stream")`,每 10 秒只读快照引擎 `get_evolution_summary()` 做变化检测,变了就推 `stats_update`;审计轨迹长度变化推 `trail_update`;附 `: ping` 心跳防代理超时。**不改演进引擎**,单次快照异常不打断长连接。事件格式与前端 `onmessage`(`data.type === 'stats_update' | 'item_update' | 'trail_update'`)对齐。

### 待真实验证(需本机 rtk,沙箱连不到后端/LLM 域名)
- 起后端 → 浏览器开概览页 → DevTools Network 看 `/evolution/stream` 是否 `200 text/event-stream` 且持续推送。
- 断开后端 → 确认前端自动转 30 秒轮询(`_ssePollTimer` 启动)。

---

## 2. 第二梯队:缓存语义偏弱(P1)

`_panelCache` 当前存的是**布尔标志**(`cacheSet('panel-overview', true, ...)`),只是「最近加载过」的去重闸,**不缓存真实响应数据**。后果:
- 面板切走再切回,TTL 内虽不重复请求,但数据并未真正复用——逻辑靠 `_panelLoaded[name]` 而非缓存内容。
- `zones` 是唯一真正缓存了数据的(`zones-data` / `zones-active-data`),证明缓存层有能力存数据,只是大部分面板没用上。

**迭代方向:** 把高频只读面板(overview summary、rules、items)的实际 payload 存入缓存,切回时直接渲染缓存数据再后台校验(stale-while-revalidate),减少可感知延迟。属中等复杂度、需设计判断 → 倾向 Claude,但非阻塞。

---

## 3. 第三梯队:UX / 可访问性 / 健壮性(P2,多为 Reasonix 可领的机械项)

- **`prompt()` 阻塞式输入**:`closeItem` 用两次 `prompt()` 收集关闭理由/验证结论,体验割裂且无法在自动化测试中走通 → 替换为页内弹层表单。
- **可访问性**:tab 导航已有 `aria-selected`,但骨架屏、错误重试按钮、SVG 图缺部分 ARIA;键盘导航未全覆盖。
- **重试按钮实现脆弱**:`renderError` 通过 `retryFn.toString()` 内联 `onclick`,依赖函数为全局可达;闭包重试在某些面板可用但耦合度高 → 改为事件委托。
- **错误信息装饰**:`toast` 依赖 `window.api.decorateErrorMessage` 存在性,缺失时降级正常,可补单测固化。

---

## 4. 测试与验收(Reasonix 主力)

- 前端单测:`src/frontend/__tests__/system-evolution.test.js`(现有 3 用例,沙箱内 `npx vitest run` 已全绿;本机用 `rtk npx vitest run`)。新增实时更新降级、缓存语义用例。
- 后端接口门:`/evolution/stream` 返回 `200 text/event-stream`;其余 evolution 端点 2xx 回归(`rtk python3 -m pytest`)。
- UI 全按钮冒烟:7 面板逐项手测(需登录,本机执行)。

---

## 5. 实施顺序

1. **P0 实时更新**(Claude 已落地代码 → Reasonix 本机验证)
2. **P2 机械健壮性项**(Reasonix 为主:prompt 替换、ARIA 补全、单测补充)
3. **P1 缓存真实数据**(Claude,非阻塞,可下一轮)

详细逐条任务见 `docs/system-evolution优化todos.md`。
