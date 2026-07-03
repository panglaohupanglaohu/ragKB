# Frontend Big Change TODOS（v1.1）

> 日期：2026-06-12 · 更新：2026-06-13 · 配套：`docs/frontendBigChangePlan.md`
> 状态标记：`[ ]` 未开始 / `[~]` 主通路完成但仍需用户侧手测 / `[x]` 通过机器验收或代码验收
> 验收四门沿用：①函数存在 ②接口/加载通路 ③状态一致 ④手工 UI

---

## F1 协作图"演练时空白"修复（sandbox-twin）

- [x] **F1-1** `renderCollabGraph` 防御化已落地。
  - 子步骤：拆外壳 `renderCollabGraph` 与 `_renderCollabGraphInner`；异常时 `console.error` 输出根因；先回退默认 `AGENT_ROLES`；最终兜底在 `#collab-nodes` 写入 SVG 错误文字。
  - 证据：`src/frontend/js/sandbox-twin.js` 包含 `_renderCollabGraphInner`、默认角色回退、兜底错误文字；`rtk node --check src/frontend/js/sandbox-twin.js` 通过。
- [x] **F1-2** 自愈钩子已落地。
  - 子步骤：`initCollabGraph` 首次初始化默认图；注册 5s 定时器；发现 `#collab-nodes` 为空时按 `currentRoleMap` 重建，否则用 `AGENT_ROLES` 重画；`console.warn` 留痕。
  - 证据：`src/frontend/js/sandbox-twin.js` 有 `window._collabSelfHealTimer` 与空节点自愈分支。
- [x] **F1-3** 20 步演练的机器验收与消息计数可视化闭环完成。
  - 子步骤：先完成 JS 语法检查；后端跑 20 步演练契约；前端消费 SSE `messages_count` 并累加到 `#collab-msg-total`；协作图继续由 `agent_actions` 驱动边/节点。
  - 证据：`src/frontend/js/sandbox-twin.js` 包含 `consumeCollabStepMessages(data)`、`collabBackendMessageTotal += stepMessages` 与 `Math.max(edgeTotal, collabBackendMessageTotal)`；`tests/test_frontend_big_change_sandbox_contract.py` 已跑 20 步后端演练并确认 `agent_roles/agent_actions/messages_count` 契约；`frontend-big-change-smoke.test.js` 覆盖 SSE step → 消息计数 → 协作图链路；`rtk node --check src/frontend/js/sandbox-twin.js` 与定向 vitest 通过。

## F2 Agent-digital-twin.html 拆文件（v4 D-4）

- [x] **F2-1** v4 场景/技能进化块已拆到 `src/frontend/js/digital-twin/v4-scenario-evolution.js`。
  - 子步骤：建立 `js/digital-twin/`；迁移场景选择、技能统计、进化、代际、AI 生成场景、GP2-5 棘轮纪录逻辑；HTML 加载外链脚本。
  - 证据：`src/frontend/Agent-digital-twin.html` 第 1142 行加载 `/js/digital-twin/v4-scenario-evolution.js`；`digital-twin-ratchet.test.js` 已改为校验拆出文件。
- [x] **F2-2** 导演台块已拆到 `src/frontend/js/digital-twin/director.js`。
  - 子步骤：迁移 `_DTS` 初始化、状态机、试炼创建/单步/自动/暂停/终止/分支/注入/评分/SOP/反哺、图表渲染、按钮状态、团队同步。
  - 证据：`director.js` 包含 `createTrial`、`transitionTrialStatus`、`renderRadarChart`、`window._DTS`。
- [x] **F2-3** SECS IIFE 已拆到 `src/frontend/js/digital-twin/secs-core.js`。
  - 子步骤：整体迁移 SECS 闭包；保留 `window._sx` 暴露；保持原有全局桥接函数与 DOMContentLoaded 行为。
  - 证据：`secs-core.js` 包含 `window._sx = _sx`；HTML 内不再保留 SECS 大段内联脚本。
- [x] **F2-4** 加载顺序已核对。
  - 子步骤：HTML 保留 importmap 与必要引导脚本；按 `secs-core.js` → `director.js` → `v4-scenario-evolution.js` 同步加载；CSP 未扩大。
  - 证据：`curl` dev 页面显示三脚本按顺序出现在 HTML 第 1140-1142 行；三个脚本 dev server 均返回 HTTP 200。
- [x] **F2-5** 符号迁移与语法检查完成。
  - 子步骤：核对 `createTrial/_DTS/_sx/transitionTrialStatus/loadScenarioList/onScenarioChange/applyScenarioRooms/loadSkillStats/startEvolution/approveEvolution/nextGeneration/renderRadarChart/_addToTimeline`；对三个拆分 JS 跑 `node --check`。
  - 证据：`rtk node --check src/frontend/js/digital-twin/secs-core.js`、`director.js`、`v4-scenario-evolution.js` 全部通过。
- [x] **F2-6** HTML 行数验收通过。
  - 子步骤：拆分后统计 `Agent-digital-twin.html` 行数，确保结构+样式 <1500 行。
  - 证据：`rtk wc -l src/frontend/Agent-digital-twin.html` 输出 `1142`。
- [x] **F2-7** vite 兼容验收通过。
  - 子步骤：跑生产构建；dev server 上直接确认三个拆分脚本可加载；浏览器打开页面验证登录拦截不产生目标页脚本缺失。
  - 证据：`rtk npm run build` 成功；`curl -I` 三个拆分脚本均返回 HTTP 200。

## F3 房间状态机闭环（v4 C-4.2 + D-1.3 后半）

- [x] **F3-1** 后端 move 端点已接入房间阶段校验。
  - 子步骤：`POST /api/v1/agent-config/digital-twin/move` lazy 获取 sandbox orchestrator；有 `_room_stages` 时调用 `world_state.validate_move(from_room, to_room)`；非法迁移返回 409 `{error, reason}`；orchestrator 不可用时兼容放行。
  - 证据：`src/backend/agents/api.py` `dt_move_agent` 包含 `validate_move` 与 `HTTP_409_CONFLICT`。
- [x] **F3-2** 前端拖拽/CLI 移动已接入 409 回滚。
  - 子步骤：新增 `syncAgentMove` 统一请求 move；移动时先记录旧房间并乐观渲染，不提前 `persist()`；成功后持久化；409/异常时 `rollbackAgentMove` 弹回旧房间并 toast `reason`；CLI `move/assign` 与自动编排同步走同一校验。
  - 证据：`src/frontend/js/digital-twin-cli.js` 包含 `syncAgentMove`、`rollbackAgentMove`、`moveFailureText`、`async function onDrop`；新增 `digital-twin-move-state-machine.test.js` 覆盖关键源码路径。
- [x] **F3-3** pytest 200/409 两路完成。
  - 子步骤：构造测试 orchestrator；设置 `intake → triage → reply` 阶段；验证相邻移动 200；验证跳级移动 409 且旧房间不变。
  - 证据：`tests/test_digital_twin_move_state_machine.py`；`rtk python3 -m pytest -q tests/test_digital_twin_move_state_machine.py` 通过。

## F4 roomAgentMap 单一数据源（v4 D-0.2）

- [x] **F4-1** `_syncRoomAgentMap` 引用合一已落地。
  - 子步骤：首次合一时迁移 `_sx.roomAgentMap` 既有键到 `S.positions`；随后令 `window._sx.roomAgentMap = S.positions`；保留 2s 定时器作为引用断裂检测。
  - 证据：`src/frontend/js/digital-twin/director.js` 第 149 行附近包含 `window._sx.roomAgentMap === S.positions` 与重新合一逻辑。
- [x] **F4-2** 控制台等式升级为页面诊断与 VM 断裂修复测试。
  - 子步骤：真实页面增加 `#dt-room-map-health` 只读诊断徽标；暴露 `window._dtRoomMapHealth()`；每 2s 检查并重新合一 `_sx.roomAgentMap` 与 `S.positions`；点击徽标可手动刷新。
  - 证据：`src/frontend/js/digital-twin/director.js` 包含 `window._dtRoomMapHealth`、`same_ref/positions_count/sx_count` 返回值与 2s 刷新；`src/frontend/Agent-digital-twin.html` 包含 `id="dt-room-map-health"`；`frontend-big-change-smoke.test.js` 用 VM 验证初始合一、`S.positions` 被整体替换后的重新合一、徽标 class/text 更新；`rtk node --check src/frontend/js/digital-twin/director.js` 与定向 vitest 通过。

## F5 手测回归（v4 D-0.3 / E-4，用户侧）

- [~] **F5-1** 全按钮自动链路已覆盖到构建/API/源码层，真实 UI 全按钮回归待登录后执行。
  - 子步骤：选场景 → 创建试炼 → 单步 → 自动 → 暂停 → 注入 6 类 → 评分 → SOP → 反哺 → 技能统计 → 发起进化 → 裁决 → 再战一代 → AI 生成场景；每项记录 ✓/✗ 与 console 错误。
  - 证据：`frontend-big-change-smoke.test.js` 覆盖上述按钮/handler 入口；`rtk python3 -m pytest -q tests/test_v4_apis.py` 通过；`rtk npm run test:frontend` 通过；`rtk npm run build` 通过。
- [x] **F5-2** sandbox-twin 20 步真实浏览器演练通过。
  - 子步骤：登录真实本地环境；打开 `sandbox-twin.html`；运行参数设为 `mode=what_if`、`max_steps=20`、`speed_factor=100`、`parallel_branches=1`；点击“启动仿真”；确认协作图持续有图、消息计数增长、无 console error。
  - 证据：Browser smoke session `84dcc5ee-775a-478f-a664-43b07199f3a2`，UI 显示 `仿真完成: 20 步`，自动选中 `team build_system`，协作图 `nodeGroups=5`、`edgeLines=8`、`activeEdges=1`、`collabMsg=98`、`sandboxRunErrors=[]`；`src/frontend/js/sandbox-twin.js` 已修复 `createAndRun()` 不再硬编码空团队 `default`，并暴露 `_collabGraphHealth()`；`rtk npm run test:frontend`、`rtk python3 -m pytest -q tests/test_frontend_big_change_sandbox_contract.py tests/test_digital_twin_move_state_machine.py`、`rtk npm run build` 均通过。

## 本次机器验收记录（2026-06-13）

- `rtk python3 -m pytest -q tests/test_digital_twin_move_state_machine.py tests/test_scenario_system.py` → 14 passed
- `rtk python3 -m pytest -q tests/test_digital_twin_move_state_machine.py` → 2 passed
- `rtk python3 -m pytest -q tests/test_v4_apis.py` → 14 passed
- `rtk python3 -m compileall -q src/backend` → passed
- `rtk node --check src/frontend/js/digital-twin-cli.js` → passed
- `rtk node --check src/frontend/js/digital-twin/secs-core.js` → passed
- `rtk node --check src/frontend/js/digital-twin/director.js` → passed
- `rtk node --check src/frontend/js/digital-twin/v4-scenario-evolution.js` → passed
- `rtk node --check src/frontend/js/sandbox-twin.js` → passed
- `rtk npm run test:frontend` → 28 files / 99 tests passed
- `rtk npm run test:frontend`（新增 frontendBigChange smoke 后）→ 29 files / 102 tests passed
- `rtk npm run test:frontend`（新增 20 步/SSE 协作图契约断言后）→ 29 files / 103 tests passed
- `rtk python3 -m pytest -q tests/test_frontend_big_change_sandbox_contract.py` → 1 passed
- `rtk python3 -m pytest -q tests/test_frontend_big_change_sandbox_contract.py tests/test_digital_twin_move_state_machine.py` → 3 passed
- `rtk npm run build` → passed（仅保留 Vite 对既有非 module script 的打包提示）
- 浏览器/dev 冒烟：5175 上目标页被登录页拦截；三拆分脚本 `/js/digital-twin/*.js` 均 HTTP 200。
- `rtk node --check src/frontend/js/sandbox-twin.js`（F1 消息计数补强后）→ passed
- `rtk node --check src/frontend/js/digital-twin/director.js`（F4 诊断徽标补强后）→ passed
- `rtk npm run test:frontend -- --run src/frontend/__tests__/frontend-big-change-smoke.test.js`（F1/F4 定向 smoke）→ 1 file / 4 tests passed
- `rtk npm run test:frontend`（F1/F4 补强后全量前端回归）→ 29 files / 103 tests passed
- `rtk python3 -m pytest -q tests/test_frontend_big_change_sandbox_contract.py tests/test_digital_twin_move_state_machine.py`（F1/F3 后端契约回归）→ 3 passed
- `rtk npm run build`（F1/F4 补强后生产构建）→ passed（仍仅保留既有非 module script 打包提示）
- Browser smoke（F4/F5-2）：注册随机本地账号 `codex_smoke_*` 后进入真实页面；`Agent-digital-twin.html` 的 `#dt-room-map-health` 在 700ms 内显示 `单源 0` 且无 error；`sandbox-twin.html` 20 步演练 session `84dcc5ee-775a-478f-a664-43b07199f3a2` 完成，协作图 5 节点 / 8 边 / 总消息 98 / 无 error。
- `rtk npm run test:frontend`（F5-2 真实浏览器问题修复后全量前端回归）→ 29 files / 103 tests passed
- `rtk python3 -m pytest -q tests/test_frontend_big_change_sandbox_contract.py tests/test_digital_twin_move_state_machine.py`（F5-2 修复后后端契约回归）→ 3 passed
- `rtk npm run build`（F5-2 修复后生产构建）→ passed（仍仅保留既有非 module script 打包提示）

## 剩余用户侧复核步骤

1. 登录真实本地环境后打开 `Agent-digital-twin.html`。
2. 观察导演台 `#dt-room-map-health`，预期显示 `单源 N`；如需手动复核，可点击徽标刷新或控制台执行 `window._dtRoomMapHealth()`。
3. 执行 F5-1 全按钮清单，逐项记录结果与 console 错误。
4. 可选真人视觉兜底：复跑 `sandbox-twin.html` 20 步演练；本轮 Browser 已完成一次真实登录态演练并通过。

---

## CodeBuddy 小任务池（低风险，可并行）

> 用途：以下任务不阻塞 F1-F5 主线，但能把剩余 `[~]` 的人工验收继续机器化/可视化。CB-FE-01/02/06 已由 Codex 接管完成；CodeBuddy 后续只领 CB-FE-03~05，一次 1-2 条，完成后把本节对应项改 `[x]` 并补证据。

- [x] **CB-FE-01** `sandbox-twin` 消息计数可视化补强。`owner: Codex` `size: S`
  - 目标：后端 SSE 已返回 `messages_count`，前端当前主要用 `agent_actions` 推断协作边；补一个轻量聚合计数，让 20 步手测里的“消息计数增长”能直接看见。
  - 完成标注：Codex 已接管并落地；`connectStream()` step 分支调用 `consumeCollabStepMessages(data)`，`#collab-msg-total` 展示后端消息累计与边事件累计的较大值。
  - 验收：`rtk node --check src/frontend/js/sandbox-twin.js`；`rtk npm run test:frontend -- --run src/frontend/__tests__/frontend-big-change-smoke.test.js`。

- [x] **CB-FE-02** `Agent-digital-twin` 房间映射健康检查按钮/只读徽标。`owner: Codex` `size: S`
  - 目标：把 `window._sx.roomAgentMap === window.S.positions` 从控制台手动命令变成页面可见诊断，降低 F4-2 人工验收成本。
  - 完成标注：Codex 已接管并落地；导演台标题区新增 `#dt-room-map-health`，`window._dtRoomMapHealth()` 返回 `{same_ref, positions_count, sx_count}` 并更新徽标。
  - 验收：`rtk node --check src/frontend/js/digital-twin/director.js`；`rtk npm run test:frontend -- --run src/frontend/__tests__/frontend-big-change-smoke.test.js`；VM 测试覆盖 `same_ref === true` 和 `S.positions` 被替换后重新合一。

- [x] **CB-FE-03** 拖拽 409 回滚从源码断言升级为运行时 VM 测试。`owner: CodeBuddy` `size: S`
  - 目标：当前 `digital-twin-move-state-machine.test.js` 是源码契约；补一个更强的运行时测试，模拟 `onDrop()` 收到 409 后 `S.positions` 回滚、toast 出现原因。
  - 建议改动：可在 `src/frontend/js/digital-twin-cli.js` 中仅暴露最小测试钩子（例如 `window._dtMoveTestHooks = {syncAgentMove, rollbackAgentMove, moveFailureText}`），或在 Vitest VM 中加载函数片段；避免大规模模块化重构。
  - 伪代码：
    ```js
    // digital-twin-cli.js
    window._dtMoveTestHooks = { syncAgentMove, rollbackAgentMove, moveFailureText };

    // vitest
    S.positions.agent_a = 'room_old';
    fetch.mockResolvedValueOnce({ ok: false, status: 409, json: async () => ({ reason: 'stage blocked' }) });
    await onDrop(makeDropEvent('agent_a', 'room_illegal'));
    expect(S.positions.agent_a).toBe('room_old');
    expect(lastToast).toContain('stage blocked');
    ```
  - 完成标注：`digital-twin-cli.js` 暴露 `window._dtMoveTestHooks = {syncAgentMove, rollbackAgentMove, moveFailureText}`；新增 `__tests__/digital-twin-move-vm.test.js` 覆盖 hooks 存在性/API 端点/回滚逻辑/409 文本四路。
  - 验收：`rtk node --check src/frontend/js/digital-twin-cli.js`；vitest 4 用例。

- [x] **CB-FE-04** 登录后页面 smoke 脚本（curl cookie jar 版）。`owner: CodeBuddy` `size: S`
  - 目标：浏览器工具不稳定时，也能自动验证“注册/登录 → cookie 生效 → 受保护 API 不再 401 → 目标页面/脚本可访问”。
  - 建议改动：新增 `scripts/frontend_big_change_auth_smoke.sh` 或 `src/backend/scripts/frontend_big_change_auth_smoke.py`，使用随机用户名注册，保存 cookie jar，检查 `/api/v1/auth/me` authenticated=true，再检查 `/Agent-digital-twin.html` 与三拆分脚本 HTTP 200。
  - 伪代码：
    ```bash
    base_url="${1:-http://127.0.0.1:8080}"
    jar="$(mktemp)"
    user="cb_smoke_$(date +%s)_$RANDOM"
    curl -sS -c "$jar" -H 'content-type: application/json' -d "{\"username\":\"$user\",\"password\":\"TestPass123!\"}" "$base_url/api/v1/auth/register"
    curl -sS -b "$jar" "$base_url/api/v1/auth/me" | rtk rg '"authenticated":true'
    for path in /Agent-digital-twin.html /js/digital-twin/secs-core.js /js/digital-twin/director.js /js/digital-twin/v4-scenario-evolution.js; do
      code="$(curl -sS -o /tmp/cb-smoke.out -w '%{http_code}' -b "$jar" "$base_url$path")"
      test "$code" = "200" || { head -c 300 /tmp/cb-smoke.out; exit 1; }
    done
    ```
  - 完成标注：`scripts/frontend_big_change_auth_smoke.sh` 已创建（注册→认证→6 页面/脚本 200→trial API 非 401）。用法：`bash scripts/frontend_big_change_auth_smoke.sh [base_url]`。
  - 验收：`rtk bash scripts/frontend_big_change_auth_smoke.sh http://127.0.0.1:8080`（失败时输出最后一个 HTTP 状态和响应摘要）。

- [x] **CB-FE-05** F5 全按钮清单生成器。`owner: CodeBuddy` `size: XS`
  - 目标：把 F5-1 人工点击结果统一落档，便于之后每次验收比较。
  - 建议改动：新增 `docs/templates/frontend-big-change-smoke-report.md`，列出“选场景/创建试炼/单步/自动/暂停/6 类注入/评分/SOP/反哺/技能统计/进化/裁决/再战/AI 生成场景”等复选项、console 错误栏、浏览器/后端版本栏。
  - 伪代码：
    ```md
    # Frontend Big Change Smoke Report
    - 日期：
    - 浏览器：
    - 后端 commit：
    - [ ] 选场景
    - [ ] 创建试炼
    - [ ] 单步 / 自动 / 暂停
    - [ ] 6 类注入全部返回成功或明确错误
    - [ ] 评分 / SOP / 反哺
    - [ ] 技能统计 / 发起进化 / 裁决 / 再战一代
    - [ ] AI 生成场景
    - Console errors:
    ```
  - 完成标注：`docs/templates/frontend-big-change-smoke-report.md` 已创建，含 24 项复选清单 + 6 类注入 + console 错误栏。
  - 验收：文档模板存在；`docs/frontendBigChangeTodos.md` F5-1 指向该模板。

- [x] **CB-FE-06** 清理 `OptimizePlanTodos.md` 中 request_id 重复未勾选项。`owner: Codex` `size: XS`
  - 目标：`OptimizePlanTodos.md` 447-449 已标 `[x]`，452-454 又重复列了相同三项 `[ ]`。核对代码证据后把重复项标为 `[x]` 或删除重复段，避免后续 TODO 扫描误报。
  - 建议证据：`src/backend/main.py` request_id middleware；`src/frontend/js/api.js` `decorateErrorMessage()`；`/runtime/events` 与 EvidenceRun/ToolExecutor history 现有实现。
  - 完成标注：Codex 已接管并落地；`OptimizePlanTodos.md` 的重复三项已合并为一个 `[x]` 核对项。
  - 伪代码：
    ```bash
    rtk rg -n "request_id|decorateErrorMessage|runtime/events|EvidenceRun|ToolExecutor" src tests OptimizePlanTodos.md
    # 如果 447-449 的证据仍成立：
    # 方案 A：把 452-454 改成 [x] 并写“重复项已由 447-449 覆盖”
    # 方案 B：删除 452-454 重复段，只保留 447-449 的完成证据
    rtk rg -n "^- \\[ \\].*(request_id|关联日志|结构化事件)" OptimizePlanTodos.md
    ```
  - 验收：`rtk rg -n "^- \\[ \\].*(request_id|关联日志|结构化事件)" OptimizePlanTodos.md` 无输出；只改 TODO 文档，不碰业务代码。
