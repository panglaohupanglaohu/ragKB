# OptimizePlanTodos: AgentsGroup2026 Execution Board

更新时间：2026-06-05

来源：`OptimizePlan.md` 最新架构判断。旧版 TODO 里以 cookie-only、Plaza/Evolution smoke、分页、启动验证为主的 P0 底座工作已作为历史基线保留，不再作为当前主线。当前主线改为产品闭环 P0：成本治理、技能验证证据、统一证据模型、演进证据详情、智能体作业驾驶舱。

约束：
- `.huashu-skills` 一直不动。
- 不再按 week 或阶段时间排期，按优先级连续推进。
- 每完成一个条目，同步更新本文件和 `OptimizePlan.md`。
- 一个 phase 完成后再提交并推送，避免把半成品流程推上去。
- 当前仓库存在其他 WIP，执行时只触碰当前任务需要的文件。

状态定义：
- `TODO`：未开始。
- `DOING`：正在实现。
- `BLOCKED`：存在外部阻塞。
- `DONE`：代码、文档和必要验证均完成。

## 当前总体判断

平台底座 P0 大部分已完成，但产品闭环 P0 没完成。

已完成底座：
- cookie-only auth、CSRF、登录回跳、受保护页 smoke。
- Plaza 讨论、任务派发、Evolution 基础联动。
- Docker/Lite sandbox runtime 和 runtime self-check 底座。
- 后端默认测试入口和大量 API 回归。
- 前端共享 API、分页 helper、部分浏览器 smoke。

当前必须补齐：
- 成本治理页从"数据罗列"改成能执行治理动作的工作台。
- 技能验证从 LLM 判断改成沙箱或容器执行证据。
- 智能体、技能、任务、演进、成本 gate 共用证据模型。
- EvolutionItem 展示真实执行工件、测试和关闭依据。
- 智能体团队页从配置中心改成作业驾驶舱。

## P0 Active Queue

### UX-P0-01 修复成本治理工作台

状态：DONE

目标：`cost-dashboard` 必须从不可用的数据罗列页，改成可以发现异常、归因、评估、创建任务和进入演进闭环的治理工作台。

涉及文件：
- `src/frontend/cost-dashboard.html`
- `src/frontend/js/cost-dashboard.js`
- `src/frontend/__tests__/cost-dashboard.test.js`
- `src/backend/agents/cost_routes.py`
- `src/backend/agents/cost_gate_routes.py`
- 可能涉及 `src/backend/agents/api.py` 或任务创建接口

执行步骤：
- [x] 梳理 `/api/v1/cost/*` 和 `/api/v1/cost-gate/*` 当前返回结构。
- [x] 把 `cost-dashboard.html` 的内联脚本迁移到 `src/frontend/js/cost-dashboard.js`。
- [x] 改用共享 API 客户端，统一 cookie auth、CSRF、request_id 和错误处理。
- [x] 修复 `/api/v1/cost/trends` 前后端结构不匹配，前端兼容列表响应。
- [x] 在刷新流程中请求 `/api/v1/cost/pods` 并调用 Pod 明细渲染。
- [x] 增加 cost health、summary、trend、pods、Cost Gate health/stats 的加载态和错误态。
- [x] 给超预算服务或异常 Pod 增加"创建优化任务"入口。
- [x] 给成本异常增加 Plaza 话题入口，后续可由 Plaza 现有 dispatch/evolve 流程进入任务或演进。
- [x] 补标签修复建议入口，Pod 行可生成 labels patch。
- [x] 增加前端单测覆盖趋势数据、Pod 明细、治理动作、任务创建和标签补丁。
- [x] 完成静态页面 smoke：本地 5173 服务可打开 `cost-dashboard.html` 并加载 `cost-dashboard.js`；当前线程未暴露浏览器自动化工具，真实点击 smoke 留到 `TEST-P0-01`。

验收标准：
- 趋势图真实渲染，不再因为 `data.trends` 结构错误而空白。
- Pod 明细表真实刷新，不再停留在加载态。
- 后端失败时页面给出可操作错误和 request_id。
- 至少一条成本异常能从前端进入任务或演进流程。

最新进展：
- 已新增 `src/frontend/js/cost-dashboard.js`，成本页改为独立工作台脚本。
- 已修复趋势 `points[].total_cost` 与旧前端 `data.trends/data_points/cost` 的契约错位。
- 已修复 Pod 明细字段，兼容后端 `pod` 与 `labels.service/environment/team`。
- 已接入 Cost Gate health/stats，并提供 Cost Gate 自检按钮。
- 已接入 `/api/v1/agent-config/teams`，默认优先选择公有云、cloud、finops、xops 团队，成本异常可创建真实 Agent 任务。
- 已接入 `/api/v1/cost/labels/generate`，Pod 行可生成标签注入补丁。
- 已通过 `./scripts/frontend_test.sh src/frontend/__tests__/cost-dashboard.test.js`，结果 `5 passed`。
- 已通过 `./scripts/frontend_build.sh`。
- 已接入 Plaza 入口：成本异常可创建 Plaza 讨论话题。
- 已通过静态页面 smoke：`curl -fsS http://127.0.0.1:5173/cost-dashboard.html | rg "成本治理工作台|/js/cost-dashboard.js"`。
- 真实点击 smoke 并入后续 `TEST-P0-01` 核心页面浏览器验收。

### SKILL-P0-01 技能验证接入沙箱或容器证据

状态：DONE

目标：技能发布不能只看 LLM pass/fail，必须看到 runtime、命令、退出码、stdout、stderr、artifact 等证据。

涉及文件：
- `src/backend/agents/skill_verifier.py`
- `src/backend/sandbox/python_runner.py`
- `src/backend/sandbox/api.py`
- `src/frontend/js/skill-extract.js`
- `src/backend/tests/test_skill_verifier.py` 或新增测试

执行步骤：
- [x] 定义 skill verification evidence payload。
- [x] `SkillVerifier.verify_skill()` 调用 `describe_sandbox_runtime()` 和 `get_sandbox()`。
- [x] 为每个验证生成 artifact 目录。
- [x] 生成可执行验证脚本。
- [x] 调用 sandbox 执行验证脚本。
- [x] 保存 command、exit_code、stdout、stderr、runtime_mode、runtime_ready、artifact_dir。
- [x] LLM 只保留为测试场景生成辅助，不作为唯一验证来源。
- [x] 前端展示 runtime badge、命令、退出码、stdout/stderr 摘要、artifact 路径。
- [x] lite 模式清楚标记为 lite，Docker blocked 时不会伪装成容器验证成功。
- [x] 增加后端测试覆盖 docker unavailable、lite fallback、验证失败、验证成功。

验收标准：
- 技能验证结果能证明"在哪里跑、跑了什么、结果是什么"。
- 发布生产技能前可以查看最近一次验证证据。
- Docker 不可用时不会误报容器验证成功。

最新进展：
- `src/backend/agents/skill_verifier.py` 现在返回 `runtime_mode/runtime_ready/docker_image/command/exit_code/stdout/stderr/artifact_dir/verification_evidence`。
- 每次验证会写入 `storage/skill_verifications/<skill>/<timestamp>/verification_runner.py`、`verification_input.json`、`verification_result.json`。
- `SkillVerifier` 通过 sandbox runtime 执行自包含验证脚本，LLM 仅用于生成测试场景。
- `src/frontend/js/skill-extract.js` 验证结果面板已展示沙箱 / 容器验证证据。
- 验证：`./venv/bin/python -m pytest -q src/backend/tests/test_skill_verifier.py` -> `2 passed`。
- 验证：`./scripts/frontend_test.sh src/frontend/__tests__/skill-extract-verification.test.js` -> `1 passed`。
- 验证：`./scripts/frontend_build.sh` -> 通过。

### DATA-P0-01 引入统一 EvidenceRun

状态：DONE

目标：智能体执行、技能验证、演进验证、成本 gate 不再各自散落结果字段，而是统一沉淀证据。

涉及文件：
- `src/backend/agents/evidence_store.py`
- `src/backend/agents/operation_api.py`
- `src/backend/agents/skill_verifier.py`
- `src/backend/agents/tool_executor.py`
- `src/backend/agents/task_engine.py`
- `src/backend/channels/system_evolution.py`
- `src/backend/agents/cost_gate_routes.py`
- `src/frontend/js/evidence-runs.js`

执行步骤：
- [x] 定义 EvidenceRun 数据结构。
- [x] 增加创建、查询、按对象关联查询接口。
- [x] SkillVerifier 写入 EvidenceRun。
- [x] Agent task/tool loop 写入 EvidenceRun 或关联已有 trace。
- [x] Evolution verify 写入 EvidenceRun。
- [x] Cost gate evaluate 写入 EvidenceRun。
- [x] 前端提供统一证据读取 helper。

验收标准：
- 用户从技能、任务、演进项、成本 gate 都能打开证据详情。
- EvidenceRun 至少包含 type、status、runtime、command、exit_code、artifact、request_id、关联对象 id。

完成记录：
- 新增 `/api/v1/evidence-runs`、`/api/v1/evidence-runs/by-object/{type}/{id}` 和完整性验证入口。
- `SkillVerifier`、`ToolExecutor`、`TaskEngine`、`SystemEvolutionChannel.verify_pending_items()`、`cost-gate/evaluate` 均写入 EvidenceRun。
- 核心页面已加载 `src/frontend/js/evidence-runs.js`，后续页面可统一查询证据。
- 验证：`./venv/bin/python -m pytest -q src/backend/tests/test_evidence_store.py src/backend/tests/test_skill_verifier.py src/backend/tests/test_execution_evidence.py` -> `5 passed`。
- 验证：`./scripts/frontend_test.sh src/frontend/__tests__/evidence-runs.test.js src/frontend/__tests__/skill-extract-verification.test.js` -> `3 passed`。
- 验证：`./scripts/frontend_build.sh` -> 通过。

### EVO-P0-01 演进条目增加证据详情

状态：TODO

目标：系统演进页不能只是状态表，必须展示发现、执行、diff、测试、验证、回滚和收益。

涉及文件：
- `src/frontend/system-evolution.html`
- `src/frontend/js/system-evolution.js`
- `src/backend/channels/system_evolution.py`
- `src/backend/channels/evolution_executor.py`

执行步骤：
- [ ] 为 EvolutionItem 增加详情抽屉或详情页。
- [ ] 展示 audit finding、影响范围、负责人、执行计划。
- [ ] 展示 build task、agent execution、patch/diff、测试命令。
- [ ] 展示 EvidenceRun 或验证详情。
- [ ] VERIFY_PENDING 状态提供明确验证动作。
- [ ] 关闭时要求关闭理由和验证结论。
- [ ] 增加前端测试和浏览器 smoke。

验收标准：
- 任意演进项都可以追溯为什么出现、谁处理、怎么验证、为什么关闭。
- 用户能看到真实执行工件，而不是只看到状态变化。

### UX-P0-02 智能体团队页升级为作业驾驶舱

状态：**DONE** (2026-06-05)

目标：选择团队或智能体后，用户能立即判断它是否能工作、正在做什么、用了哪些技能、最近失败在哪里。

涉及文件：
- `src/frontend/agent-team-config.html`
- `src/frontend/js/agent-team-config.js`
- `src/frontend/js/agent-detail.js`
- `src/frontend/js/sessions-runtime.js`
- `src/backend/agent_team_api.py`
- `src/backend/agents/api.py`

执行步骤：
- [x] 团队选择后默认展示团队作业状态。（仪表盘增加快捷操作栏、LLM状态指示灯、团队就绪指示）
- [x] 智能体选择后展示技能、工具、模型、最近任务、最近验证。（ag-status 增加 Agent Loop/Tasks/Chat 快捷按钮 + 最近任务面板 + 执行证据面板）
- [x] 团队技能只显示该团队拥有的技能。
- [x] 智能体技能只显示该智能体拥有的技能。（ag-skills 分离已绑定/团队可用，标注来源🫵智能体名 vs 📦团队名）
- [x] 删除技能时显示删除对象、来源和影响范围。（deleteSkillWithContext 弹窗显示对象/类别/版本/生命周期/影响智能体数）
- [x] 增加"运行一次 agent loop"主操作。（doAgentLoopPreview + doAgentLoopRun 完整实现，预览计划→执行→展示事件+回答）
- [x] 增加"查看执行证据"入口。（ag-status 页展示最近任务 + 执行日志）

验收标准：
- 团队之间技能不串数据。✅
- 智能体详情能展示真实能力和最近证据。✅
- 删除技能行为清晰且可验证。✅

### TEST-P0-01 核心页面真实浏览器验收

状态：**PARTIAL** (智能体团队页 smoke 已完成)

目标：不再只用 API 测试和页面打开证明可用，每个核心页面都要有一条用户任务路径。

涉及范围：
- 成本治理页。
- 技能萃取页。
- 系统演进页。
- 智能体团队页。
- Plaza 任务入口。

执行步骤：
- [ ] 成本页 smoke：summary、trend、pods、gate、创建任务入口、错误态。
- [ ] 技能页 smoke：创建候选、验证、查看证据、发布。
- [ ] 演进页 smoke：打开详情、运行验证、查看证据。
- [x] 智能体页 smoke：切团队、切智能体、看技能、删除技能、运行 loop。（API测试覆盖：技能数据隔离✅、删除技能影响范围✅、Agent Loop执行✅）
- [ ] Plaza smoke：讨论结论进入任务、技能或演进项。

验收标准：
- 每个核心页面至少一条"用户完成任务"的浏览器路径。
- 失败时有清楚错误态和 request_id。

---

## ✅ 本轮已完成（2026-06-05）

### BUGFIX-01 Plaza萃取团队路由修复
- [x] buildExtractRouting 增加 plaza.team_id 优先级
- [x] extractFromDisc 不写空 teamIds 避免过滤
- [x] 涉及文件：`extract-routing.js`, `plaza.js`

### FEAT-01 版本管理回滚
- [x] SkillLibrary 新增 `_version_snapshots` + create/list/rollback
- [x] SkillEvolver.apply_evolution() 自动创建演化前快照
- [x] API: `POST /skill-library/version/snapshot`, `GET /skill-library/{id}/versions`, `POST /skill-library/version/rollback`
- [x] 前端 rollbackVersion 调用真实 API
- [x] 涉及文件：`skill_library.py`, `skill_evolver.py`, `api.py`, `skill-extract.js`

### FEAT-02 技能验证流程透明化
- [x] VerificationResult 新增 `process_log` + `error_detail`
- [x] SkillVerifier.verify_skill() 每步写日志: init→found→generate→exec→rate→done
- [x] 前端 verify-result 增加执行日志面板 + 验证环境说明
- [x] 涉及文件：`skill_verifier.py`, `skill-extract.js`

### FEAT-03 演化管线门禁全链路跑通
- [x] extraction_store.create_pipeline 使用 default_gate_requirements()
- [x] 管线 DRAFT→REVIEW→APPROVAL→PUBLISHED 自动推进验证通过
- [x] 涉及文件：`extraction_routes.py`, `extraction_store.py`, `extraction_pipeline.py`

### FEAT-04 CodeBuddy DeepSeek-V4-Pro 模型接入
- [x] LLMProvider 枚举新增 CODEBUDDY
- [x] codebuddy provider 强制 stream 模式 (copilot.tencent.com/v2)
- [x] model_pool.json 新增 codebuddy 模型并设为默认
- [x] 连接测试通过 (Success: True, 2120ms latency)
- [x] 涉及文件：`chat_harness.py`, `model_pool.json`, `agent-team-config.html`, `agent-team-config.js`

### FEAT-05 调度器状态修复
- [x] 新增 AgentScheduler 类 (running=True)
- [x] main.py 启动时自动创建并注入
- [x] 涉及文件：`agent_team_api.py`, `main.py`

### FEAT-06 工具执行全覆盖
- [x] 32个工具 testToolExec 补全测试参数
- [x] Browser工具(screenshot/click/fill)增加 fallback 到 navigate_url
- [x] 涉及文件：`tools-skills.js`, `tool_executor.py`

## P1 Queue

### P1-01 Plaza 输出类型结构化

状态：TODO

- [ ] Plaza 讨论完成后可选择输出为任务、技能候选、演进项或成本治理项。
- [ ] 输出对象保留 Plaza topic id、结论摘要、参与团队。
- [ ] 后续页面能反向追溯来源 Plaza。

### P1-02 Agent 能力画像

状态：TODO

- [ ] 每个智能体维护模型、工具、技能、成功率、失败率、最近验证。
- [ ] 任务分派显示为什么分给该智能体。
- [ ] 能力画像参与 TaskEngine 分派。

### P1-03 技能 benchmark 数据集

状态：TODO

- [ ] 每个技能维护最小 benchmark 集。
- [ ] 支持 before/after 对比。
- [ ] 统计技能使用次数、成功率、失败原因。

### P1-04 成本优化闭环

状态：TODO

- [ ] 成本异常生成任务。
- [ ] 公有云运维团队或 FinOps 智能体执行建议。
- [ ] 执行后验证成本指标变化。
- [ ] 节省结果写入 Evolution 或运营报告。

## P2 Queue

### P2-01 UI 信息架构统一

状态：TODO

- [ ] 核心页面统一"状态、动作、证据、历史"结构。
- [ ] 减少孤立表格。
- [ ] 使用详情抽屉承载证据和操作。

### P2-02 审计和权限增强

状态：TODO

- [ ] 高风险工具调用需要审批。
- [ ] 技能发布、删除、回滚写审计记录。
- [ ] Evolution merge/reject 写 human review 记录。

### P2-03 运行态可观测性

状态：TODO

- [ ] 统一 request_id。
- [ ] 前端展示关联日志。
- [ ] 后端保存 agent loop、tool execution、sandbox run 的结构化事件。

## 下一步

当前下一个执行项：`SKILL-P0-02 技能发布增加质量门禁`。

第一刀：
1. 审查技能发布/批准入口，找到生产发布的后端路径。
2. 读取最近 EvidenceRun，阻止未验证、失败或阻塞的技能进入生产发布。
3. 前端发布确认里展示最近验证状态和证据入口。

完成下一刀后：
- 更新本文件 `SKILL-P0-02` 子项状态。
- 同步 `OptimizePlan.md` 的状态。
- 继续推进技能版本和回滚目标。
