# Frontend Big Change Plan（v1.0）— 前端大工程统一规划

> 日期：2026-06-12 · 配套执行清单：`docs/frontendBigChangeTodos.md`
> 范围：所有 todos 文件中遗留的前端大工程 + 用户报障
> 前置事实：AgentsGroupConfig E-F 已完结；GP2-1/2/3 可视化已完结；v4 前端 D-1/D-2/D-3 主体已完结

---

## 一、遗留盘点（来源 → 工程）

| # | 工程 | 来源 | 规模 | 风险 |
|---|---|---|---|---|
| F1 | **协作图"演练时空白" bug** | 用户报障（sandbox-twin.html [5v7]） | 小 | 低 |
| F2 | **Agent-digital-twin.html 拆文件** | v4 todos D-4.1/4.2/4.3 | **大**（~3700 行单文件 → 结构+样式 <1500 行 + js/digital-twin/ 模块） | **高** |
| F3 | 房间状态机前后端闭环 | v4 todos C-4.2 + D-1.3 后半（拖拽 409 toast） | 中 | 中 |
| F4 | roomAgentMap 单一数据源 | v4 todos D-0.2（S.positions 引用合一，替代定时复制） | 小 | 中 |
| F5 | 全量按钮手测回归 | v4 todos D-0.3 / E-4 | 手测 | — |

## 二、F1 协作图修复方案（已先行实施）

静态排查结论：CSS（sandbox-twin.css 34 处 collab 规则）、SVG 渐变 defs（5 个齐全）、初始化链（load→initCollabGraph）、变量声明均完好。"演练时空白"的机理推断：SSE step 事件携带 `agent_roles` → `ingestAgentRoles` → `rebuildCollabGraphFromRoles` → `renderCollabGraph` 先 `clearCollabLayers()` **清空后**若任一步抛异常 → 图层被清未重画 → 空白。

修复（防御三层，已落地）：
1. `renderCollabGraph` 拆为外壳+`_renderCollabGraphInner`，异常时 console.error 根因 + 回退渲染默认 `AGENT_ROLES` + 最终兜底在 SVG 内显示错误文字（不再静默空白）。
2. 自愈钩子：每 5s 检查 `#collab-nodes` 子节点数，为 0 自动按 `currentRoleMap` 或默认角色重画并 console.warn。
3. 根因留痕：用户下次演练若再触发，console 将给出确切异常栈（验收时收集）。

## 三、F2 拆文件方案（本计划核心）

### 3.1 现状

`Agent-digital-twin.html` ≈3700 行：`<style>` ≈1100 行 + 结构 ≈300 行 + 两个内联 `<script>` ≈2300 行：
- **SECS IIFE**（~1750 行）：`(function(){...})()` 闭包，内部 `var _sx` 经 `window._sx` 暴露；包含场景列表/团队树/仿真控制/房间渲染/CLI/SSE。
- **导演台块**（~350 行）：`window._DTS`、状态机 `transitionTrialStatus`、`createTrial` 等全局函数、`_BG` 按钮组。
- **v4 块**（~450 行）：场景选择/技能进化面板/代际曲线/AI生成场景（全部 `window.*` 或顶层 function，对外部引用全部 `typeof` 守卫——自包含度最高）。

### 3.2 拆分目标结构

```
src/frontend/js/digital-twin/
  secs-core.js        ← SECS IIFE 原样搬移（闭包结构不动）
  director.js         ← _DTS + 状态机 + trial 按钮函数 + 时间轴/雷达/柱状渲染
  v4-scenario-evolution.js ← v4 全部（场景/进化/代际/AI生成/状态收敛）
Agent-digital-twin.html ← 结构 + <style> + 3 个 <script src>（顺序同原内联顺序）
```

### 3.3 小步策略（每步可回退）

1. **先抽 v4 块**（依赖最少、最后加载）→ node --check + grep 校验无悬挂引用 → 提交。
2. **再抽导演台块**（依赖 `_sx`(window)、`_logConsole` 等 SECS 全局——均经 window 访问，搬移安全）→ 校验 → 提交。
3. **最后抽 SECS IIFE**（最大块；IIFE 自闭包，对外仅靠 window.* 交互，整体剪切即可）→ 校验 → 提交。
4. 每步后跑：`node --check` 全部新文件 + `grep` 确认 html 中无残留 `function` 定义 + 行数统计（验收 <1500 行）。
5. vite：script 用相对 `./js/digital-twin/x.js`（vite 对 html 引用的 js 自动作为模块图资产处理，与既有 `js/*.js` 同模式）；CSP `script-src 'self'` 已允许。

### 3.4 风险与对策

- **加载顺序**：三文件按原内联顺序 `<script src>` 串行加载（非 module、非 defer），与原语义一致。
- **DOMContentLoaded 监听**：v4 块在脚本执行时注册监听——外链脚本同步执行于 DOM 解析中段，监听时机不变。
- **闭包变量**：SECS IIFE 整体搬移不改一行内部代码；导演台/v4 块全部经 window 桥接。
- **回归**：每步后核对关键全局符号清单（createTrial/_DTS/_sx/loadScenarioList/startEvolution…）`grep -c` 在 html=0 且新 js=1。

## 四、F3/F4 闭环小项

- **F3 后端**（C-4.2）：`agents/api.py` 的 `POST /digital-twin/move` 接 `sandbox.world_state.validate_move`（lazy，scenario 有房间阶段映射时才校验），非法迁移返回 409+原因；**前端**：digital-twin 拖拽失败 toast 显示 409 reason（既有拖拽 onDrop 处理加分支）。
- **F4**（D-0.2）：`_syncRoomAgentMap` 由"每 2s 复制"改为**引用合一**（`window._sx.roomAgentMap = window.S.positions` 同对象），保留函数名与兜底逻辑，删除定时器拷贝语义。

## 五、验收

- 三个新 js `node --check` 全绿；html 行数 <1500；关键全局符号迁移核对表全过
- 协作图：演练 20 步无空白（自愈钩子 0 触发为佳；触发则 console 有根因）
- F3：拖拽违规迁移弹 409 原因 toast；F4：拖拽后 `_sx.roomAgentMap === S.positions` 为 true
- 手测回归清单（D-0.3）：创建试炼→单步→自动→注入→评分→SOP→反哺→进化 全按钮过一遍
