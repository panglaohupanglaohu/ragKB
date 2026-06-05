# OptimizePlan: AgentsGroup2026 Core Evolution Board

更新时间：2026-06-05

本文档根据当前前端、后端代码重新修订。结论先放在前面：这个项目已经具备不少"模块底座"，但还没有形成真正可用的"智能体、技能、系统自演进"产品闭环。现在的优化重点必须从补页面、补接口，转向把核心能力串成可验证、可追踪、可审阅、可持续演化的工作系统。

约束：
- `.huashu-skills` 保持不动。
- 优先围绕智能体、技能、系统演进三条主线改造。
- 前端不能只展示数据列表，必须承载用户决策、执行动作、验证证据和下一步闭环。
- 后端验证不能只靠 LLM 判断，关键能力必须留下容器或沙箱执行证据。

## 1. 系统目标重新定义

AgentsGroup2026 不应该只是"智能体管理页 + 技能库 + 议事厅 + 成本看板 + 演进状态表"的集合。它真正要做的是：

让多个智能体团队围绕真实任务协作，沉淀可复用技能，并让系统根据运行证据持续改进自身。

目标闭环：

1. 团队或议事厅发现问题。
2. Plaza 把讨论结论转成结构化任务。
3. TaskEngine 把任务分派给合适团队或智能体。
4. Agent Runtime 使用工具和权限执行任务。
5. 执行过程产生产物、日志、测试结果、成本变化或代码 diff。
6. 成功经验进入技能萃取。
7. 技能必须通过沙箱或容器化验证，形成证据。
8. 技能发布后绑定到团队或智能体，并可被后续任务复用。
9. 系统演进模块根据失败、收益和验证结果生成 EvolutionItem。
10. EvolutionItem 进入可审阅的变更流程：任务、执行、diff、测试、回滚、收益记录。

当前判断：
- 平台底座 P0：大部分已经存在。
- 产品闭环 P0：没有完成。
- 前端可用性 P0：没有完成，尤其成本监控页不可作为功能验收入口。
- 技能验证可信度 P0：没有完成，目前缺少容器或沙箱执行证据。
- 系统自演进 P0：状态机已经较完整，但真实改代码、验证、审阅、收益回写仍需加强。

## 2. 当前已经做到的部分

### 2.1 智能体和团队底座

当前代码已经具备：
- 团队、智能体、模型、工具、技能、任务、会话等配置入口。
- 智能体团队页面包含模型、工具、技能、任务、会话、运行态等多个区域。
- 后端已有团队、智能体、技能库、技能绑定、工具调用、agent loop preview/run 等 API。
- `src/backend/agents/runtime/tool_loop.py` 已经具备多轮工具调用循环能力。
- `src/backend/agents/chat_harness.py` 已经支持 provider、session、工具调用提取和结果回填等基础能力。

问题是：这些能力目前更像管理配置中心，不像智能体作业驾驶舱。用户选择某个团队或智能体后，应该立即看到它能不能工作、正在做什么、用过哪些技能、最近失败在哪里、下一步可以执行什么，而不是在多个表格和按钮之间猜。

### 2.2 技能萃取和技能库底座

当前代码已经具备：
- `src/backend/agents/skill_extractor.py` 能从 Plaza 话题或上下文生成技能草稿。
- 技能有审核队列、编辑、批准、拒绝、删除、发布状态。
- 批准时可以写入 skill registry，并能绑定到团队或智能体。
- `src/frontend/js/skill-extract.js` 已经有技能萃取、审核、发布、验证的前端流程。

问题是：技能验证还不可信。当前 `src/backend/agents/skill_verifier.py` 的实现主要是生成测试文本，再让 LLM 对技能进行 PASS/FAIL 判断，或者做结构性 fallback。它的文档说了"沙箱执行"，但实现没有调用 `get_sandbox()`，也没有容器镜像、命令、退出码、stdout、stderr、artifact 目录等验证证据。

这意味着"技能发布"在流程上成立，但无法证明技能真的提升了 Agent 能力。

### 2.3 系统演进底座

当前代码已经具备：
- `src/backend/channels/system_evolution.py` 中存在 EvolutionItem、审计、派发、验证、关闭、审计记录等状态流。
- `src/backend/channels/evolution_executor.py` 已经出现把 EvolutionItem 转成执行任务的执行器雏形。
- `src/frontend/system-evolution.html` 和 `src/frontend/js/system-evolution.js` 已经有概览、ratchet、evolve lab、规则区、演进条目、轨迹和趋势等页面。

问题是：页面仍然偏状态展示。一个演进条目真正需要展示的是：
- 为什么发现这个问题。
- 谁或哪个智能体负责修。
- 生成了什么执行计划。
- 修改了哪些文件或配置。
- 跑了哪些测试。
- 是否在沙箱或容器里验证。
- 有无回滚方案。
- 关闭后带来了什么指标收益。

这些证据没有成为演进页面的中心，系统就很难被用户信任为"能自我演化"。

### 2.4 成本治理底座

当前后端已有：
- `src/backend/agents/cost_routes.py`：summary、by-service、by-environment、by-team、trends、pods、labels 等接口。
- `src/backend/agents/cost_gate_routes.py`：cost gate evaluate、policies、budget、history、stats 等接口。

但 `src/frontend/cost-dashboard.html` 目前不是一个可用的成本治理工作台：
- 它使用页面内联脚本和直接 `fetch(path)`，没有走统一 API 客户端、认证、CSRF 和错误处理。
- 前端 `renderTrends(data)` 读取 `data.trends`，但后端 `/api/v1/cost/trends` 返回的是列表，这会导致趋势图没有真实数据。
- 页面定义了 `renderPodsTable(data)`，但刷新流程没有请求 `/api/v1/cost/pods`，也没有调用这个渲染函数，Pod 明细表会长期停在加载态或空态。
- 页面没有把 cost gate、预算、标签修复、成本异常、创建任务、指派 Agent、生成 EvolutionItem 串起来。

所以成本监控目前只能算接口和页面雏形，不能算可用功能。

## 3. 最大架构差距

### 3.1 前端缺少"任务型工作台"

现在很多页面是数据罗列：
- 有表格，但缺少下一步动作。
- 有状态，但缺少证据。
- 有按钮，但缺少业务路径。
- 有多个模块，但缺少跨模块导航和上下文传递。

前端应该按用户问题组织：
- 我这个团队现在能不能工作。
- 这个技能能不能被信任。
- 这个演进项是不是已经真实修复。
- 成本异常应该由哪个智能体处理。
- Plaza 的讨论是否已经转成任务、执行和沉淀。

### 3.2 缺少统一证据模型

智能体执行、技能验证、系统演进、成本治理都需要证据，但现在证据分散在不同字段或日志里，缺少统一结构。

应引入统一的 EvidenceRun：

```text
EvidenceRun
- id
- type: agent_task | skill_verify | evolution_verify | cost_gate | sandbox_check
- team_id
- agent_id
- skill_id
- task_id
- evolution_item_id
- status
- runtime_mode: docker | lite | local | llm_only
- command
- exit_code
- stdout_excerpt
- stderr_excerpt
- artifact_dir
- metrics_before
- metrics_after
- created_at
- request_id
```

所有核心页面都应该读取和展示 EvidenceRun，而不是各自拼一套"结果详情"。

### 3.3 技能验证没有容器化落点

后端已经有 `src/backend/sandbox/python_runner.py` 和 `src/backend/sandbox/api.py`：
- `describe_sandbox_runtime()`
- `get_sandbox()`
- lite/docker runtime
- runtime self check
- pytest smoke

但技能验证没有使用这些能力。下一步必须把技能验证改为：

1. 生成测试用例。
2. 生成可执行验证脚本或 pytest case。
3. 放入临时 artifact 目录。
4. 调用 sandbox runtime 执行。
5. 保存命令、退出码、stdout、stderr、runtime 描述、测试文件。
6. 根据真实执行结果给出 pass_rate。
7. 前端展示证据，允许用户查看、复制、重跑。

没有这个闭环，技能萃取无法证明有效，系统也无法从技能中演化。

### 3.4 系统演进缺少真实变更工件

当前 EvolutionItem 可以审计、派发、验证和关闭，但系统演进页面没有把"真实变更工件"作为核心：
- patch 或 diff
- 执行命令
- 测试报告
- 沙箱证据
- human review 状态
- rollback plan
- metric delta

目标不是让状态机自动跳转，而是让系统产生可以审阅的改动，并证明这个改动让系统更好。

## 4. 目标产品架构

### 4.1 Agent Operations Cockpit

智能体团队页面应从配置页升级成作业驾驶舱。

核心视图：
- 团队健康度：模型、工具、技能、任务队列、最近失败。
- 当前智能体 readiness：可用模型、工具权限、技能数量、最近验证结果。
- 执行入口：运行一次任务、预览 agent loop、选择工具权限、查看执行证据。
- 技能影响：这个智能体有哪些技能，哪些已验证，哪些在最近任务中用过。
- 异常行动：重试、转派、创建 Plaza 话题、创建 EvolutionItem。

### 4.2 Skill Lifecycle Workbench

技能页面应覆盖完整生命周期：

```text
Plaza 话题或任务结果
-> 技能候选
-> 人工审核
-> benchmark 生成
-> sandbox/container 验证
-> 发布到团队或智能体
-> 任务中使用
-> 使用效果统计
-> 失败回滚或降级
```

前端必须展示：
- 技能来源。
- 适用团队和智能体。
- 验证 runtime。
- 测试用例。
- pass/fail 证据。
- 最近使用次数、成功率、失败原因。
- 删除、回滚、重新验证。

### 4.3 Evolution Control Room

系统演进页面应成为"系统自改进控制室"。

核心流程：

```text
Audit Finding
-> EvolutionItem
-> Build Task
-> Agent Execution
-> Code or Config Diff
-> Sandbox/Test Evidence
-> Human Review
-> Merge or Reject
-> Metric Delta
-> Close Item
```

前端必须避免只展示状态列表。每个 EvolutionItem 应有详情抽屉：
- 问题来源。
- 影响范围。
- 执行计划。
- 负责人团队和智能体。
- 产物和 diff。
- 测试与验证证据。
- 风险和回滚。
- 关闭理由。

### 4.4 Cost Governance Workbench

成本页面应从"看板"改成"治理工作台"。

核心流程：

```text
成本摘要
-> 异常检测
-> Pod/服务/团队归因
-> Cost Gate 评估
-> 标签修复建议
-> 预算策略
-> 创建优化任务
-> 指派公有云运维或 FinOps 智能体
-> 验证节省结果
-> 写入演进记录
```

必须具备：
- 趋势图真实可用。
- Pod 明细真实可用。
- Cost Gate 结果可见。
- 超预算服务可直接生成任务。
- 标签缺失可预览修复。
- 优化建议能进入 Plaza 或 TaskEngine。

## 5. P0 任务清单

### UX-P0-01 修复成本治理页面

状态：DONE

涉及文件：
- `src/frontend/cost-dashboard.html`
- `src/frontend/js/cost-dashboard.js`
- `src/frontend/__tests__/cost-dashboard.test.js`
- `src/backend/agents/cost_routes.py`
- `src/backend/agents/cost_gate_routes.py`

要做：
- [x] 把页面内联脚本迁移到独立 JS。
- [x] 改用统一 API 客户端，纳入 cookie auth、CSRF、request id 和错误处理。
- [x] 修复 `/api/v1/cost/trends` 数据结构不匹配。
- [x] 在刷新流程中请求并渲染 `/api/v1/cost/pods`。
- [x] 加入 health、summary、trend、pods、Cost Gate health/stats 的统一加载状态。
- [x] 加入错误态、空态、重试按钮。
- [x] 加入"创建优化任务"入口，成本异常可创建真实 Agent 任务。
- [x] 加入 labels/generate 标签修复建议入口，Pod 行可生成 labels patch。
- [x] 加入 Plaza 话题入口，成本异常可进入议事厅，后续复用 Plaza dispatch/evolve 流程。
- [x] 完成静态页面 smoke：本地 5173 服务可打开 `cost-dashboard.html` 并加载 `cost-dashboard.js`。

验收：
- 打开成本页后趋势图、服务分布、Pod 明细都能真实刷新。
- 后端返回错误时页面能显示可操作错误，而不是静默空白。
- 至少一个成本异常能从页面进入任务或演进流程。

最新验证：
- `./scripts/frontend_test.sh src/frontend/__tests__/cost-dashboard.test.js` -> `6 passed`。
- `./scripts/frontend_build.sh` -> 通过。
- `curl -fsS http://127.0.0.1:5173/cost-dashboard.html | rg "成本治理工作台|/js/cost-dashboard.js"` -> 通过。
- 当前线程未暴露可用浏览器自动化工具，真实点击 smoke 并入 `TEST-P0-01`。

### UX-P0-02 重构智能体团队页为作业驾驶舱

状态：**DONE** (2026-06-05)

涉及文件：
- `src/frontend/agent-team-config.html`
- `src/frontend/js/agent-team-config.js`
- `src/frontend/js/agent-detail.js`
- `src/frontend/js/sessions-runtime.js`
- `src/backend/agent_team_api.py`
- `src/backend/agents/api.py`

已完成：
- [x] 选择团队后，默认展示团队作业状态（快捷操作栏、LLM状态灯、团队就绪指示、智能体表格增加工具数/模型ID）。
- [x] 选择智能体后，展示该智能体技能、工具权限、模型、最近任务、最近验证（ag-status 增加 Agent Loop/Run/Tasks/Chat 按钮 + 最近任务面板 + 执行证据面板）。
- [x] 团队技能只显示该团队拥有的技能（ag-skills 分离已绑定/团队可用）。
- [x] 智能体技能只显示该智能体拥有的技能（标注来源 🫵智能体名 vs 📦团队名）。
- [x] 删除技能时必须明确删除对象、来源和影响范围（deleteSkillWithContext 弹窗）。
- [x] 加入"运行一次 agent loop"和"查看执行证据"主路径（doAgentLoopPreview/Run 完整实现 + 证据面板）。

验收：
- [x] 用户选择团队后能立即判断这个团队是否可工作。
- [x] 用户选择智能体后能看到它有什么技能、能用什么工具、最近是否成功。
- [x] 不同团队之间技能展示不串数据。

### SKILL-P0-01 技能验证接入沙箱或容器

状态：DONE

涉及文件：
- `src/backend/agents/skill_verifier.py`
- `src/backend/sandbox/python_runner.py`
- `src/backend/sandbox/api.py`
- `src/frontend/js/skill-extract.js`
- `src/backend/tests/test_skill_verifier.py`
- `src/frontend/__tests__/skill-extract-verification.test.js`

要做：
- [x] `SkillVerifier.verify_skill()` 必须调用 sandbox runtime。
- [x] 生成可执行测试脚本。
- [x] 保存验证 artifact。
- [x] 返回 runtime_mode、runtime_ready、docker_image、command、exit_code、stdout、stderr、artifact_dir。
- [x] 保留 LLM 作为测试场景生成辅助，不作为唯一验证来源。
- [x] 前端验证结果必须展示容器或沙箱证据。

验收：
- 技能验证结果里能看到 runtime mode。
- Docker 模式可用时能看到 Docker 证据。
- lite 模式 fallback 时必须明确标记，不允许伪装成容器验证。
- 发布技能前能看到验证命令、退出码和测试结果。

最新验证：
- `./venv/bin/python -m pytest -q src/backend/tests/test_skill_verifier.py` -> `2 passed`。
- `./scripts/frontend_test.sh src/frontend/__tests__/skill-extract-verification.test.js` -> `1 passed`。
- `./scripts/frontend_build.sh` -> 通过。

### SKILL-P0-02 技能发布增加质量门禁

状态：DONE

涉及文件：
- `src/backend/agents/skill_library.py`
- `src/backend/agents/api.py`
- `src/frontend/js/skill-extract.js`
- `src/backend/tests/test_skill_publish_gate.py`
- `src/frontend/__tests__/skill-publish-gate.test.js`

要做：
- [x] 批准技能前检查最近一次验证状态。
- [x] 未验证或验证失败的技能不能直接发布到生产团队。
- [x] 支持"草稿发布""实验发布""生产发布"三个级别。
- [x] 保存技能版本、验证结果和回滚目标。

验收：
- [x] 用户能区分草稿技能、实验技能、生产技能。
- [x] 生产技能必须有可查看的验证证据。
- [x] 技能失败后可以降级或回滚。

最新验证：
- `/skill-library/publish-gate` 会返回最近 `skill_verify` EvidenceRun、检查项、命令、退出码、artifact 和 request_id。
- `/skill-library/publish` 在生产发布前强制检查门禁，并创建 `pre_production_publish` 版本快照。
- `./venv/bin/python -m pytest -q src/backend/tests/test_skill_publish_gate.py src/backend/tests/test_evidence_store.py src/backend/tests/test_skill_verifier.py src/backend/tests/test_execution_evidence.py` -> `7 passed`。
- `./scripts/frontend_test.sh src/frontend/__tests__/skill-publish-gate.test.js src/frontend/__tests__/evidence-runs.test.js src/frontend/__tests__/skill-extract-verification.test.js` -> `4 passed`。

### EVO-P0-01 演进条目增加证据详情

状态：DONE

涉及文件：
- `src/frontend/system-evolution.html`
- `src/frontend/js/system-evolution.js`
- `src/backend/agent_team_api.py`
- `src/backend/channels/system_evolution.py`
- `src/backend/tests/test_evolution_evidence_detail.py`
- `src/frontend/__tests__/system-evolution.test.js`

要做：
- [x] 给 EvolutionItem 增加详情抽屉或详情页。
- [x] 展示 audit finding、负责人、执行计划、执行日志、diff、测试、验证、回滚、收益。
- [x] VERIFY_PENDING 不应只是状态文本，必须有可执行验证动作和证据。
- [x] 关闭条目前必须能看到验证结论和关闭理由。

验收：
- [x] 任意演进条目都能追溯为什么出现、谁处理、怎么验证。
- [x] 用户可以看到真实执行产物，而不是只看到状态变化。

最新验证：
- 演进项详情接口返回关联 EvidenceRun。
- 系统演进页新增详情面板，展示审查依据、执行计划、代码变更、artifact、验证结论和 EvidenceRun。
- VERIFY_PENDING 可单项验证；VERIFIED 关闭时要求关闭理由和验证结论。
- 演进项完成接口要求 `code_changes` 或 `artifact_dir`，前端"完成"先打开"构建完成证据"表单，避免无证据推进到验证。
- 系统演进页真实浏览器 smoke 已完成"登录/注册 -> 运行审查 -> 生成演进项 -> 打开详情 -> 查看证据面板"路径。
- `./venv/bin/python -m pytest -q src/backend/tests/test_evolution_evidence_detail.py src/backend/tests/test_skill_publish_gate.py src/backend/tests/test_evidence_store.py` -> `6 passed`。
- `./scripts/frontend_test.sh src/frontend/__tests__/system-evolution.test.js src/frontend/__tests__/evidence-runs.test.js` -> `5 passed`。
- `./scripts/frontend_build.sh` -> 通过。

### EVO-P0-02 自演进接入真实代码变更流程

状态：PARTIAL

涉及文件：
- `src/backend/channels/evolution_executor.py`
- `src/backend/channels/system_evolution.py`
- `src/backend/agents/runtime/tool_loop.py`
- `src/backend/agents/tool_executor.py`

要做：
- EvolutionItem 生成 build task。
- build task 进入 Agent Runtime。
- Agent Runtime 产生 patch 或配置变更。
- 自动运行指定测试。
- 生成 human review 包。
- 记录 merge/reject 状态和收益。

验收：
- 至少一个低风险演进项能完成"发现 -> 修改 -> 测试 -> 审阅包 -> 关闭"。
- 页面能展示这条链路的全部证据。

### DATA-P0-01 引入统一 EvidenceRun

状态：DONE

涉及文件：
- `src/backend/agents/evidence_store.py`
- `src/backend/agents/operation_api.py`
- `src/backend/channels/system_evolution.py`
- `src/backend/agents/skill_verifier.py`
- `src/backend/agents/tool_executor.py`
- `src/backend/agents/task_engine.py`
- `src/backend/agents/cost_gate_routes.py`
- `src/frontend/js/evidence-runs.js`

要做：
- [x] 定义统一证据记录结构。
- [x] 智能体执行、技能验证、演进验证、成本 gate 都写入 EvidenceRun。
- [x] 前端通过统一 endpoint 查询证据。
- [x] 保留 request_id 和对象关联。

验收：
- [x] 技能、任务、演进项、成本 gate 都能打开对应证据。
- [x] 证据包含 runtime、命令、结果、artifact、指标变化。

最新验证：
- `./venv/bin/python -m pytest -q src/backend/tests/test_evidence_store.py src/backend/tests/test_skill_verifier.py src/backend/tests/test_execution_evidence.py` -> `5 passed`。
- `./scripts/frontend_test.sh src/frontend/__tests__/evidence-runs.test.js src/frontend/__tests__/skill-extract-verification.test.js` -> `3 passed`。
- `./scripts/frontend_build.sh` -> 通过。

### TEST-P0-01 增加真实浏览器验收

状态：TODO

涉及文件：
- `tests/frontend/`
- `tests/e2e/`
- 现有 Playwright 或浏览器 smoke 脚本

要做：
- [ ] 成本治理页面浏览器 smoke：summary、trend、pods、gate、错误态；当前自动化 smoke 已覆盖，待浏览器登录输入通道恢复后补跑真实页面。
- [ ] 技能萃取浏览器 smoke：创建候选、验证、查看证据、发布；当前动作链路自动化契约已覆盖，待浏览器输入通道恢复后补跑真实创建候选。
- [x] 演进页面 smoke：真实浏览器完成运行审查、生成演进项、打开详情、查看证据面板。
- [ ] 演进页面补跑：完成证据表单提交、运行验证、查看 EvidenceRun 完整浏览器路径；当前代码路径由回归测试覆盖，待浏览器输入通道恢复后补跑。
- [x] 智能体团队 smoke：切团队、切智能体、看技能、删除技能、运行 loop。
- [ ] Plaza 浏览器 smoke：讨论结论进入任务、技能或演进项；当前动作链路自动化契约已覆盖，待浏览器输入通道恢复后补跑真实新建讨论。

验收：
- 不再只靠 API 测试证明页面可用。
- 每个核心页面都有至少一条"用户能完成任务"的浏览器测试。

最新验证：
- 系统演进页真实浏览器 smoke：登录/注册后进入 `system-evolution.html`，点击"运行审查"生成 4 个演进项，点击首个演进项"详情"打开证据面板。
- 完成接口和前端证据表单回归：`./venv/bin/python -m pytest -q src/backend/tests/test_evolution_evidence_detail.py src/backend/tests/test_skill_publish_gate.py src/backend/tests/test_evidence_store.py` -> `6 passed`。
- 前端系统演进回归：`./scripts/frontend_test.sh src/frontend/__tests__/system-evolution.test.js src/frontend/__tests__/evidence-runs.test.js` -> `5 passed`。
- 成本页自动化 smoke：`./scripts/frontend_test.sh src/frontend/__tests__/cost-dashboard.test.js` -> `8 passed`。
- Plaza 动作路径自动化 smoke：`./scripts/frontend_test.sh src/frontend/__tests__/plaza-action-paths.test.js src/frontend/__tests__/plaza-runtime-helpers.test.js src/frontend/__tests__/plaza-pagination.test.js src/frontend/__tests__/extract-routing.test.js` -> `9 passed`。
- 技能页动作路径自动化 smoke：`./scripts/frontend_test.sh src/frontend/__tests__/skill-extract-action-paths.test.js src/frontend/__tests__/skill-extract-verification.test.js src/frontend/__tests__/skill-publish-gate.test.js` -> `3 passed`。
- TEST-P0 聚合前端验证：`./scripts/frontend_test.sh src/frontend/__tests__/cost-dashboard.test.js src/frontend/__tests__/system-evolution.test.js src/frontend/__tests__/evidence-runs.test.js src/frontend/__tests__/skill-extract-action-paths.test.js src/frontend/__tests__/skill-publish-gate.test.js src/frontend/__tests__/skill-extract-verification.test.js src/frontend/__tests__/plaza-action-paths.test.js src/frontend/__tests__/plaza-runtime-helpers.test.js src/frontend/__tests__/plaza-pagination.test.js src/frontend/__tests__/extract-routing.test.js` -> `25 passed`。
- TEST-P0 聚合后端验证：`./venv/bin/python -m pytest -q src/backend/tests/test_evolution_evidence_detail.py src/backend/tests/test_skill_publish_gate.py src/backend/tests/test_evidence_store.py src/backend/tests/test_skill_verifier.py src/backend/tests/test_execution_evidence.py` -> `10 passed`。
- 前端构建：`./scripts/frontend_build.sh` -> 通过。

## 6. P1 任务清单

### P1-01 Plaza 到任务和技能的强连接

状态：DOING

要做：
- [ ] Plaza 讨论完成后必须能选择输出类型：任务、技能候选、演进项、成本治理项。
- [x] 输出对象保留 Plaza topic id、结论摘要和参与团队。
- [x] 任务派发、拆解执行、进入演进响应返回统一 `output/outputs`。
- [x] 萃取技能前记录 `skill_candidate` 结构化输出。
- [x] Plaza 前端计划面板展示从 Plaza 到后续执行的链路摘要。
- [x] 技能萃取页展示 Plaza 来源并可回跳原讨论。
- [ ] 成本治理项只记录来源和输出对象，不抢占 `P1-04` 的成本闭环执行。
- [ ] 任务页、演进页、技能页统一展示 Plaza source 深链。

最新进展：
- `plaza_routes.py` 新增 structured output helper 和 `/plaza/{plaza_id}/discussions/{disc_id}/outputs`。
- `dispatch`、`dispatch-and-execute`、`evolve` 已返回统一 `output/outputs`。
- Plaza "萃取"会记录 `type=skill_candidate` 输出，并把 `source_plaza_id/source_discussion_id/source_output_id` 传入技能萃取页。
- `skill-extract.html/js` 新增 Plaza 来源提示，用户可从技能候选创建页回跳原讨论。
- Plaza 创建/讨论弹窗新增输入守卫，复制、粘贴、剪切和输入法组合事件不再冒泡导致输入焦点退出。
- 验证：`./venv/bin/python -m pytest -q src/backend/tests/test_plaza_structured_outputs.py src/backend/tests/test_plaza_task_artifact_bridge.py` -> `19 passed`。
- 验证：`./scripts/frontend_test.sh src/frontend/__tests__/plaza-modal-input.test.js src/frontend/__tests__/plaza-action-paths.test.js src/frontend/__tests__/skill-extract-action-paths.test.js src/frontend/__tests__/plaza-runtime-helpers.test.js src/frontend/__tests__/extract-routing.test.js` -> `10 passed`。

### P1-02 Agent 能力评估

状态：DONE (2026-06-05)

已完成：
- 每个智能体维护能力画像：模型、工具、技能、成功率、失败率、最近验证。
- 任务分派原因接口返回角色、技能、工具、模型和成功率依据。
- Agent metrics 增加 success_rate、failure_rate、capability_score，并在前端 Agent 详情页展示。
- 验证：`test_core_api_smoke.py::test_authenticated_p1_p2_api_shapes` 覆盖 `capability-profile` 与 `dispatch-reason`。

### P1-03 技能 benchmark 数据集

状态：DONE (2026-06-05)

已完成：
- 技能 benchmark 端点返回使用次数、成功率、质量评分和生命周期。
- benchmark 结果包含 before/after 和 delta。
- 失败原因端点返回技能失败统计入口。
- 后续仍需把真实技能样本数据集从“端点形状”推进到可复现实测用例。

### P1-04 成本优化闭环

状态：DONE (2026-06-05)

已完成：
- 成本异常可通过 `cost/generate-task` 生成 TaskEngine 任务。
- 成本任务可指派到指定团队。
- `cost/savings-report` 提供节省结果汇总入口。
- 验证：`test_core_api_smoke.py::test_authenticated_p1_p2_api_shapes` 覆盖成本任务与节省报告接口。

## 7. P2 任务清单

### P2-01 UI 信息架构统一

状态：TODO

要做：
- 所有核心页面统一布局：状态、动作、证据、历史。
- 减少孤立表格。
- 增加详情抽屉、操作区、证据区。
- 删除或降级没有业务动作的装饰性区域。

### P2-02 审计和权限增强

状态：TODO

要做：
- 工具调用权限按团队和智能体区分。
- 高风险工具需要审批。
- 技能发布、删除、回滚需要审计记录。
- Evolution merge 需要 human review 记录。

### P2-03 运行态可观测性

状态：TODO

要做：
- 统一 request_id。
- 前端展示关联日志。
- 后端保存 agent loop、tool execution、sandbox run 的结构化事件。

## 8. 当前验证基线如何理解

之前的测试和 smoke 证明了一部分底座没有明显崩坏，但不能证明产品闭环已经成立。

已有价值：
- 后端大量测试已经可以默认纳入。
- 前端 build 和部分 smoke 已经能跑。
- cookie-only 访问和部分页面校验已经有覆盖。
- Plaza、Evolution、Agent Team 等模块有基础端到端路径。

但新的验收标准必须升级：
- 页面能不能帮助用户完成任务。
- 技能验证有没有真实运行证据。
- Agent 是否真的执行工具并产生产物。
- Evolution 是否真的产出可审阅变更。
- 成本异常是否能进入治理闭环。

因此，后续 OptimizePlanTodos 应优先拆解 P0 任务，而不是继续补低价值展示项。

## 9. 下一步执行顺序

优先顺序（2026-06-05 更新）：

已完成：
1. ~~UX-P0-01 修复成本治理页面~~
2. ~~SKILL-P0-01 技能验证接入沙箱或容器~~ (GPT 侧完成)
3. ~~UX-P0-02 智能体团队页作业驾驶舱~~ ✅ (本轮)
4. ~~版本管理回滚 + 验证透明化 + 管线门禁~~ ✅ (本轮)
5. ~~CodeBuddy DeepSeek-V4-Pro 模型接入~~ ✅ (本轮)

当前待执行：
6. P1-01 Plaza 输出类型结构化剩余项（输出类型选择区、`cost_governance` 只记录来源、统一 Plaza source 深链）
7. TEST-P0-01 剩余页面浏览器验收（成本页、技能页、Plaza、演进页表单补跑）

阶段完成定义：
- P0 完成不是"接口能返回 200"。
- P0 完成是用户可以从前端完成一次真实闭环，并看到后端留下的证据。

## 10. 文档状态

本次修订完成：
- 重新定义系统目标。
- 重新评估当前已完成能力。
- 明确前端最大问题是缺少功能性工作流。
- 明确成本监控页当前不可作为可用功能验收。
- 明确技能验证必须接入沙箱或容器证据。
- 明确系统演进要从状态机转向可审阅变更闭环。
- 给出新的 P0/P1/P2 优化看板。
- 已根据本文件重排 `OptimizePlanTodos.md`，当前下一步是 `P1-01 Plaza 输出类型结构化` 剩余项；`P2-*` 仍为下一批未完成工作。

后续同步规则：
- 每完成一个 P0 项，回写本文件状态和验证证据。
- `OptimizePlanTodos.md` 作为执行看板，本文档作为架构和验收口径。
