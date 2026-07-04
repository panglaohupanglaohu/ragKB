<!-- docs-signoff: author="Claude Fable 5" kind="llm" doc="plan" ts="2026-07-04T05:20:00Z" -->
# 测试失败分诊报告 2026H2（P0-2 交付物）

> 状态：current。基线环境：Linux（沙箱）、Python 3.10、Node 22。对照 Windows 基线（2026-06-26，96 py + 12 vitest 失败）。
> 分诊三分法：**真 bug（修实现）** / **契约漂移（以演进方向为准）** / **环境可移植性**。

## 结果总览

| 阶段 | 后端+根目录 pytest | 前端 vitest | build |
| --- | --- | --- | --- |
| Windows 基线 2026-06-26 | 96 失败 | 12 失败 | 失败 |
| Linux 初测 2026-07-04 | 46 失败 | 12 失败 | 失败 |
| **本轮修复后** | **0 失败（1388 通过）** | **7 失败（164 通过）** | **✓ 通过** |

Windows(96) 与 Linux(46) 的差值 ≈50 个为**环境可移植性**（`Path.rename` 覆盖写、GBK 编码、Windows 路径），对应 Todos P0-5，仍需在 Windows 上验证。

## 已修复清单（本轮，全部定性为「真 bug / 实现缺口」，修实现不改测试）

1. **build：three.js vendor 路径**。`sandbox-twin-3d.js` 用 `/vendor/three/...` 绝对路径（目录不存在），其余 3D 文件均为裸导入 `'three'`。→ 统一为裸导入。
2. **分页信封缺口（12+ 用例）**。`agent_team_api._paginate_optional`（可选分页信封，前端已兼容两种形状）从未接入 `agents/api.py` 的 9 个列表端点（teams/models/tools/agents/sessions/tasks/delegations/templates/skill-library×2）。→ 移植同一契约。
3. **鉴权豁免过宽（安全缺口，8 用例）**。`/api/v1/agent-config/teams` 前缀全方法豁免 → 未登录可创建/改/删团队；`digital-twin/state`、`agent-teams/overview` 等亦被豁免。→ 豁免改为方法感知（只读豁免仅限 GET/HEAD/OPTIONS），移除 overview/evolution/bridge-chat 豁免（startup_validator 本就把 401+health 在线视为可达）。
4. **技能绑定未物化（5 用例）**。`update_agent_skills` 只写引用不物化团队副本、不持久化；`disable_skill`/`delete_skill` 不解绑 Agent、不跨团队清理；`list_team_skills` 不含内置有效技能。→ 实现 物化/解绑/跨团队删除/有效技能视图（含 `bound_agent_count`）。
5. **P1/P2 运维端点从未实现（7 用例）**。capability-profile、dispatch-reason、cost/generate-task、cost/savings-report、audit/recent、runtime/events。→ 首版实现（能力评分=成功率60%+技能覆盖25%+工具覆盖15%，事件环形缓冲）。
6. **运行时模型绑定缺口（4 用例）**。`_get_deepseek_credentials` 不认团队模型；LLM 401 时任务卡死；缩写消歧（成本域 RI）缺失；能力画像不解析 team-local trait 技能。→ 实现 `_harness_provider_credentials` 分层凭据、降级草稿收尾、`_build_agent_loop_prompt_and_system` 消歧、容错技能解析。
7. **权限与密钥（4 用例）**。`update_permissions` 丢 `allowed_tools` 且不持久化；`update_llm_provider` 把密钥明文写 settings.json 而非加密 secret store；`run_agent_loop` 不传 permission_context/on_event；`run_agent_loop_stream` 不存在。→ 全部补齐。
8. **孪生管线中断误判（2 用例，核心真 bug）**。`orchestrator.run_full_pipeline` 用 `status != RUNNING` 判断中断，而 `run_simulation` 正常结束状态是 `EVALUATING` → 正常演练被跳过对齐、会话永久卡 evaluating。→ 改为仅 `PAUSED/FAILED` 视为中断。
9. **房间状态机未接线（1 用例）**。`world_state.validate_move` 存在但 `dt_move_agent` 不调用 → 业务阶段跳跃不被拒。→ 接线，违规返回 409 stage_violation。
10. **幻影团队校验误杀孪生团队（7 用例，顺序污染根因）**。`trial_api.resolve_team_id` 只认 agents 侧 TeamManager；孪生 `sync_world` 注册的团队被拒。→ orchestrator 记录 `known_teams`，校验放行。
11. **lite 沙箱误杀 stdlib 传递依赖（1 用例）**。`__import__` 钩子按名拦截 `subprocess`，Python 3.10 中 `uuid→platform→subprocess` 被误杀（危险函数本已被中和）。→ 已在 sys.modules 的模块放行，显式危险导入仍由 AST 静态检查拦截。
12. **startup_validator 被环境代理劫持（1 用例）**。httpx 默认 trust_env 读 ALL_PROXY。→ 本机自检 `trust_env=False`。
13. **前端 CSRF 契约（2 用例 + 22 处调用点）**。8 个文件存在裸状态变更 fetch()。→ 统一 `(window._agFetch || fetch)`。
14. **前端拆分回归（4 用例）**。`dp-scenario-cards` 场景卡片容器、故障注入面板 DOM、手动 createTrial 入口在文件拆分时从 HTML 丢失（JS/CSS 均在）；login 回退页指向未打包的 `-new.html`；试炼状态机转移表与会话 ID 别名（`window._currentSessionId`）与 D-4.3 契约不一致。→ 全部补齐。

## 遗留（7 个 vitest + 1 个 flaky）

- **cost-dashboard.test.js（7）— 定性：测试过期**。测试编码旧「美元/OpenCost」口径（`$10.00`、pod 表、美元趋势）；实现已按 P8.x 演进为 **token 北极星**口径（tokens、run_id、phase）。方向正确，**应重写测试**为 token 契约（新增 Todos P0-10 [GLM]，口径：normalizeTrends 点位字段 `total`、明细行 `run_id/phase/team_id/skill_id/calls/total`）。
- **tests/test_openclaw_sync.py::test_process_sync_request_deep_dependency — flaky**（全量偶发 1 次，单独/复跑均过）。新增 Todos P0-11 [GLM]：定位共享状态并隔离。

## 环境说明

- Linux 基线用系统 Python 3.10（仓库 venv 为宿主机版本）；Windows 复验请按 [VALIDATION.md](../VALIDATION.md)。
- 本轮所有修复均有对应测试守护，`npm run lint`（compileall）+ `vite build` 通过。
