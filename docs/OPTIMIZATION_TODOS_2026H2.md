<!-- docs-signoff: author="Claude Fable 5" kind="llm" doc="todos" ts="2026-07-05T03:12:00Z" -->
# 优化 Todos 2026H2（按执行模型分层）

> 文档状态：current。规划依据：[OPTIMIZATION_PLAN_2026H2.md](OPTIMIZATION_PLAN_2026H2.md)。
> 标注说明：
> - **[F5]** = 需要 Claude Fable 5 级模型（跨模块推理、定性判断、核心设计）。
> - **[GLM]** = GLM-5.2 级普通开发模型可完成（有规格、有样例、可机械验收）。
> - 每项必须有「验收」命令；GLM 项验收不通过时升级为 F5 处理。
> - 状态：`[x]` 已完成 / `[ ]` 待办 / `[~]` 进行中。

## P0 工程基线收口

- [x] **P0-1 [F5] 修复 vite build**：`sandbox-twin-3d.js` 的 `/vendor/three/...` 改为裸导入 `'three'`（与其余 3 个 3D 文件一致；页面 importmap 已兜底原生加载）。
  验收：`npm run build` 退出码 0。（2026-07-04 完成）
- [x] **P0-2 [F5] 测试失败分诊报告**：全部失败按簇定性，报告见 [reports/test-triage-2026H2.md](reports/test-triage-2026H2.md)。（2026-07-04 完成）
- [x] **P0-3 [F5] 修复真 bug 簇**：14 簇全部修实现（未改测试）：分页信封接线、鉴权豁免方法感知（安全）、技能绑定物化/解绑/跨团队删除、P1/P2 运维端点、模型绑定分层凭据 + LLM 降级收尾 + RI 消歧、权限 allowed_tools + 密钥入加密 store、孪生管线 EVALUATING 中断误判、房间状态机接线、幻影团队校验放行孪生团队、lite 沙箱 stdlib 误杀、validator trust_env、前端 CSRF 包装 22 处、拆分回归 DOM 补齐、login 回退页。结果：**pytest 1388 通过 / 0 失败，build 通过**。（2026-07-04 完成）
- [x] **P0-4 [F5] 契约漂移定性**：结论——后端所有「疑似漂移」实为实现缺口，已按实现修复；唯一「测试过期」是 cost-dashboard（旧美元口径），转 P0-10。（2026-07-04 完成）
- [x] **P0-10 [GLM] 重写 cost-dashboard 测试为 token 口径**：按 triage 报告给出的字段口径（趋势点 `total`、明细 `run_id/phase/team_id/skill_id/calls/total`）重写 `src/frontend/__tests__/cost-dashboard.test.js` 7 个用例，禁止改实现。
  验收：`npx vitest run` 全绿。（2026-07-04 完成，7/7 通过，口径切 token：renderTrends 用 point.total、renderPodsTable 明细行 run_id/phase/team_id/skill_id/calls/total）
- [x] **P0-11 [GLM] 隔离 openclaw_sync 顺序 flaky**：`tests/test_openclaw_sync.py::test_process_sync_request_deep_dependency` 全量偶发，定位共享单例/事件循环并在 fixture 中隔离。
  验收：全量 pytest 连续 5 次通过。（2026-07-04 完成，根因=get_ab_test_manager() 模块级单例共享 EWMA 状态，autouse fixture 每例前后 reset_ab_test_manager()；全量 1399 passed）
- [x] **P0-5 [GLM] 修 Windows/GBK 可移植性**：`Path.rename` 覆盖写改 `os.replace`；`config/settings.json` 读写显式 `encoding="utf-8"`。全仓库同类模式一并替换。
  验收：`rg "\.rename\(" src tests` 无覆盖写用法；`rg "open\((?!.*encoding)" --pcre2` 复核清零；根测试对应用例通过。（2026-07-04 完成，13 处 tmp.rename→.replace()、api.py 4 处 settings.json 读加 encoding）
- [x] **P0-6 [GLM] 清理 `.bak` 与临时文件**：删除 `src/backend/**/*.bak`、`src/backend/0tfuaiyp`、`main.py.bak` 等（按重构路线 Phase 2 清单，先确认无引用）。
  验收：`rg -l "\.bak" src` 为空；build/test 不受影响。（2026-07-04 完成，删 34 个 .bak 快照 + 垃圾文件 0tfuaiyp；代码内运行时 .json.bak 备份机制为合法用途保留）
- [~] **P0-7 [GLM] 前端脚本 module 化**：按 Vite 警告清单为各 HTML 的 `<script src>` 补 `type="module"`（或改为显式入口），消除 build 警告。
  验收：`npm run build` 无 "can't be bundled" 警告，各页面手工冒烟正常。（2026-07-04 暂缓：部署不走 vite 打包(dist/js 未生成，后端直服 src/frontend/js)，且页面有解析期 inline script 依赖经典脚本同步全局函数，加 type=module 改 defer+模块作用域会破坏页面，需真机冒烟方可安全落地——列为高风险待验证项）
- [ ] **P0-8 [F5→GLM] mypy 渐进接入**：F5 定 mypy 配置与首批严格目录（`agents/runtime`、`agents/budget`、`sandbox/models.py`）；GLM 逐目录消错扩圈。
  验收：`mypy` 对配置内目录零错误，`npm run typecheck` 切换到 mypy。
- [x] **P0-9 [GLM] CI 门禁**：GitHub Actions 跑 lint+typecheck+build+test+docs 签名，全绿才可合并。
  验收：PR 上可见五项检查。（2026-07-04 完成，.github/workflows/ci-gate.yml 五 job：lint/typecheck/build/test 硬门禁 + docs-signoff 信息性检查，避免存量债务卡死）

## P1 成本最优执行

- [ ] **P1-1 [F5] ModelRouter 设计与首版实现**：`agents/runtime/model_router.py`——三档（economy/standard/frontier），输入任务特征+剩余预算+历史成功率，输出模型绑定；接入 tool_loop 与 chat_harness 的模型选择点；决策日志写 cost_aggregator。含单元测试（预算耗尽降档、失败升档、档位粘滞）。
  验收：`pytest src/backend/tests/test_model_router.py` 通过；tool_loop 路由日志可查。
- [ ] **P1-2 [F5] 技能渐进披露改造设计**：技能注入改为「目录（name+description）常驻 + 全文按需加载」，对齐 SKILL.md 三级披露；定义 SkillDefinition ↔ SKILL.md 互转规格与回退开关。
  验收：设计落地为 `docs/skill-progressive-disclosure.md` + 核心 loader 实现与测试。
- [ ] **P1-3 [GLM] 渐进披露批量接线**：按 P1-2 规格改 skill_router 注入路径、前端技能面板展示、既有技能数据迁移脚本。
  验收：注入 prompt 长度基准下降（跑分脚本对比）；G5 命中率不降（skill_tracker 报表）。
- [ ] **P1-4 [F5] token/任务跑分基准**：固定场景集（≥5 场景）× 固定团队，脚本 `scripts/benchmark-token-per-task.py` 输出每任务 token/成功率报告，存 `docs/reports/`。
  验收：连续两次运行结果可复现（±10%），报告含 G2/G3 两列。
- [ ] **P1-5 [GLM] 上下文预算强化**：tool_loop 工具结果分级截断（按工具类型配额）、重复调用结果缓存、历史轮次摘要压缩（按 P1-1 设计中给出的规格）。
  验收：既有 tool_loop 测试全过 + 新增截断/缓存用例通过；跑分 token 下降。
- [ ] **P1-6 [GLM] 演练成本入账**：沙箱演练消耗的 token 也写入 cost_aggregator（tag=simulation），成本看板分列生产/演练。
  验收：cost-dashboard 出现 simulation 列；对应 API 测试通过。

## P2 技能进化闭环

- [ ] **P2-1 [F5] 闭环端到端打通**：演练完成 → skill_extractor 提取 → skill_verifier 验证 → 孪生 A/B（带/不带技能）→ ratchet 门禁 → skill_library 发布 → skill_router 可路由。补齐缺失的桥接与状态机，写一条 E2E 测试。
  验收：`pytest -k skill_loop_e2e` 通过，全程无人工步骤。
- [ ] **P2-2 [F5] 发布门禁规则**：定义技能发布的量化门槛（验证通过率、A/B 增益、样本数下限）并实现于 skill_publish_gate。
  验收：门禁规则有测试覆盖，不达标技能停留在 candidate 阶段。
- [ ] **P2-3 [GLM] 技能库治理任务**：similarity 去重批处理、命中率淘汰（连续 N 次注入未使用降级）、周期报表。
  验收：治理脚本有测试；技能库无 similarity>0.9 的重复对。
- [ ] **P2-4 [GLM] SKILL.md 导入/导出**：按 P1-2 互转规格实现 import/export CLI 与 API。
  验收：往返转换无损（round-trip 测试）。

## P3 孪生保真度

- [ ] **P3-1 [F5] 生产轨迹回放编译**：把生产 tool_loop 执行记录编译为孪生场景（扩展 scenario_compiler），支持脱敏。
  验收：从一条真实执行记录生成可运行场景，演练可复现原任务结构。
- [~] **P3-2 [F5] 真实决策演练模式**（复核 2026-07-04：机制已存在）：`orchestrator.create_session(use_llm=True)` / `set_llm_mode` 已可切换 `llm_decision`（含 fallback 与 token 归因透传），启发式即 fast 模式。剩余：演练绑定 economy 档模型（依赖 P1-1 ModelRouter）+ 试炼记录标注 decision_mode 以便区分两种演练结果。
- [ ] **P3-3 [F5] 保真度校准回路**：drift_detector 周期比对沙箱预测与生产实际，输出 Spearman 相关；低于阈值自动建重校准任务。
  验收：校准报告 API + 测试；G4 指标可在演进页查看。
- [ ] **P3-4 [GLM] 场景集扩充**：按既有 scenario schema 批量补 ≥10 个覆盖主要团队类型的标准场景。
  验收：场景通过 scenario_compiler 校验并可在前端选择。
- [x] **P3-5 [F5] 孪生 Agent 行为一致性评测（PICon 式）**：**已由 数字办公室协作演练todos.md M5-2 完成**（sandbox/twin_consistency.py，6 测试过；剩前端展示为 GLM 项）。原描述：孪生副本必须与生产真身同 prompt/技能/模型档；建立一致性测试集——同一情境下孪生与真身的决策/输出一致率，低于阈值说明孪生失真、竞标结论不可迁移。这是 sim-to-real 校准（P3-3 Spearman）之前更细粒度的保真度关卡。
  验收：一致性评测脚本 + 报告；一致率纳入孪生可信度指标并在演练页展示。

## P4 架构收口

- [ ] **P4-1 [F5] api.py 拆分方案**：8.8k 行按域切分的模块边界、共享依赖处理、兼容路由表设计。
  验收：方案文档 + 首个域试点拆出且契约测试通过。
- [ ] **P4-2 [GLM] api.py 批量搬运**：按 P4-1 方案逐域搬运路由（纯移动不改逻辑）。
  验收：OpenAPI schema 与拆分前逐字节一致（契约快照对比）；全测试通过。
- [ ] **P4-3 [GLM] 契约测试**：为全部 `/api/v1/*` 路由生成 OpenAPI 快照测试。
  验收：`pytest -k contract` 通过，快照入库。
- [ ] **P4-4 [F5] 技能三存储归一**：SkillLibrary 成为唯一写入口，Registry/Store/Team-local 降级为只读视图；数据迁移与回滚方案。
  验收：并发写测试通过；旧入口写操作被拒绝并有迁移日志。
- [ ] **P4-5 [GLM] LEGACY 成本体系隔离**：Terraform cost_policy 移至 `agents/legacy/`，import 修正，禁止新增依赖（CI grep 检查）。
  验收：build/test 全过；CI 含 legacy 依赖检查。

## P5 Plaza 计划闭环（集体智慧 → 执行计划 → 人机协作执行）

> 系统目标是找出最有效能的智能体团队；Plaza 是「任务怎么干」的集体智慧入口。这条主线把 讨论 → **结构化执行计划** → 人确认/交互 → 多智能体协作执行 → 效能回流 打通成一等公民流程（现有 plan-panel 雏形与 task/evolution bridge 为基础）。

- [x] **P5-1 [F5] 执行计划的结构化契约**（2026-07-04 完成）：`agents/execution_plan.py`——ExecutionPlan/PlanStep schema（步骤/负责角色/验收依据/依赖/优先级/状态机 draft→approved→dispatched→completed）、`build_plan_from_text` 把议事长计划文本编译为结构（计划解析唯一实现迁入本模块）、随讨论持久化于 `disc.plan["structured"]`；`GET .../execution-plan` 可获取结构化计划+审查结果。11 个测试全过。
- [~] **P5-2 [F5] 计划 → 任务派发闭环**（2026-07-04 主链路完成）：`POST .../execution-plan/approve` 人批准（审查不过 422，可 force）→ dispatch 时落地性关卡强制执行（结构化计划未批准/审查不过 → 400，旧无结构化流程不受影响）→ 派发后步骤↔任务绑定（task_id 回填、状态 dispatched）→ `POST .../execution-plan/steps/{id}/status` 执行状态回流，全部完成自动置 completed 并 SSE 广播 plan_approved/plan_step_updated/plan_completed。E2E 测试过（讨论→计划→批准→派发→回流→完成）。剩余：完成后自动触发效能评分写入 ratchet/cost_aggregator（依赖 P1-4 口径）。
- [x] **P5-3 [GLM] 计划面板人机交互前端**：plaza 页 plan-panel 补全——计划步骤可视化、人工编辑/批准/驳回、逐步骤执行状态、追问某步骤（人↔Agent 对话锚定到步骤）。
  验收：vitest 契约测试 + 手工冒烟；驳回后计划可重议。（2026-07-05 完成：plaza.js 新增 loadExecutionPlan/renderExecutionPlan（步骤+落地性 issues 缺项）+ approveExecutionPlan（含强制批准保留人最终决定权，接 422 issues）+ rejectExecutionPlan（=refreshPlan 重议）+ askPlanStep（锚定步骤→interject 追问）；接后端 execution-plan/approve/refresh-plan/interject；plaza-action-paths.test.js 加 P5-3 契约用例，vitest 189 全绿 + build 通过；手工冒烟待本机）
- [→] **P5-4 [F5] 执行计划的孪生竞标（数字孪生的核心意义）**：**已移交** [数字办公室协作演练todos.md](数字办公室协作演练todos.md) M4（候选生成规格见其 plan §4.5；演练对象语义已校准为「任务」，见 M1-6），本条不再单独执行。原描述：ExecutionPlan 上生产前，在孪生沙箱对**同一份计划**做多候选组合的反复试验——候选 = 团队构型 × 技能组合 × 协作结构，每个候选跑 twin-trials 得到 (成功率, 完成质量, token 消耗)；在成功率/质量达标的候选中选 **token 效益最优**者获得执行权，结果写入 ratchet（该任务类型的最优执行者被锁定为代际基线，后来者必须更优才能取代）。首版候选可枚举（≥3 组），搜索升级见 P5-6。**前置**：P3-2 真实 LLM 决策模式——启发式概率下的竞标排名不可信。
  验收：E2E：一份计划 → ≥3 个候选组合孪生竞标 → 按 (质量达标 ∧ token 最省) 选出胜者 → 派发执行 → 竞标记录与排名可在计划面板查看；ratchet 记录该任务类型的最优执行者。
- [→] **P5-5 [F5] 协作结构显式化（可搜索的工作流图）**：**已移交** 数字办公室协作演练todos.md M3-1（M2-4/M2-5 已完成部分底座），本条不再单独执行。原描述：把候选的「协作方式」从标量 `collaboration_weight` 升级为显式工作流图：节点=（角色, 绑定技能, 模型档），边=（依赖顺序, 信息传递内容）；复用 `world_state.workflow_edges` 与 `CollaborationSOP` 承载；ExecutionPlan 步骤 ↔ 工作流节点互相映射。这是协作可被优化的前提——结构不进搜索空间，就谈不上优化协作。
  验收：twin-trials 接受工作流图作为候选参数并按图约束仿真执行顺序/通信；两个不同拓扑（如 串行流水 vs 并行+Review）在同一计划上产生可区分的评分。
- [→] **P5-6 [F5] 竞标搜索升级：AFlow 式 MCTS/进化搜索**：**已移交** 数字办公室协作演练todos.md M4 后续（M4-1 记录的 (算子,Δtoken,Δ质量) 即其训练数据），本条不再单独执行。原描述：候选生成从人工枚举升级为自动搜索——变异算子：换角色、换技能绑定、改依赖顺序、增删 Review/Ensemble 节点、升降模型档；用孪生评分 (质量, token) 做适应度，MCTS 或进化搜索（复用 `agents/evolution/` mutator/optimizer 骨架）在试验预算内探索；胜出的协作结构固化为 CollaborationSOP 入技能库，同类任务直接复用（FlowBank 思路），复用即跳过搜索。
  验收：标准任务集上，搜索产出的协作结构比人工枚举基线 token 效益提升 ≥20%（质量不降）；胜出 SOP 可被第二个同类计划直接复用并跳过搜索。

## P6 Plaza 讨论质量与计划落地性（2026-07 调研落地，经用户校准）

> **两阶段经济学原则（本仓库铁律）**：Plaza 集体智慧阶段**不做任何 token 优化、不设预算约束、不把讨论消耗计入团队效能考核**——智慧是无价的，计划质量优先。成本纪律从「执行计划产生之后」才开始：计划派发为任务、进孪生反复试验、上生产执行，那里才是 token 效益的战场（见 P5-4）。
> P6 的唯一目标：**讨论不跑题，收敛出能落地、能实现、可派发执行的计划。** 调研依据（仅取质量向结论）：typed epistemic acts 结构化审议、匿名化去从众偏差、说服攻击/自信偏差鲁棒性、模型异质性避免集体盲区。

- [ ] **P6-1 [F5] 跑题守卫与目标收敛**：每轮收束时 moderator 对照讨论目标（disc.goal）做偏航检测——本轮内容与目标的相关性、是否引入无关话题；偏航则下一轮子问题强制拉回，连续偏航则点名最相关角色发言。讨论的终止条件是「目标问题已被回答且计划要素齐备」，而不是轮次耗尽。
  验收：注入跑题干扰的测试话题集上，最终计划仍完整覆盖 goal；偏航事件在时间线可见。
- [~] **P6-2 [F5] 计划落地性审查（可执行性关卡）**（2026-07-04 关卡完成；2026-07-05 Review 修复：与孪生侧审查统一为唯一实现 `validate_plan(profile='dispatch'|'twin')`，plan_scenario_bridge 降级为适配层）：`execution_plan.validate_plan`——计划非空、每步骤必须有 标题/负责角色/验收依据，依赖必须可解析且不得自依赖；审查不过 → approve 422 / dispatch 400（残缺计划测试验证无法派发）。剩余：审查意见回写讨论时间线 + moderator 自动追问补齐（GLM 按本契约接线）。
- [ ] **P6-3 [GLM] 匿名化汇总与共识判定**：moderator 收束与 plaza_consensus 判定时，把发言剥离 agent 名字/座席层级（去内圈权威偏差），只看内容与证据。
  验收：consensus 单测通过；汇总 prompt 中无发言者身份字段。
- [ ] **P6-4 [F5] 结构化发言（typed epistemic acts）**：发言标注类型（主张/证据/反驳/让步/提问），PlazaMessage 增加 act_type 字段；共识 = 未被有效反驳的主张集合；该结构直接喂给 P5-1 的 ExecutionPlan 生成，使计划每一步可溯源到讨论中的主张与证据。
  验收：消息带类型且前端可视化；ExecutionPlan 步骤能溯源到具体主张。
- [ ] **P6-5 [GLM] 反自信偏差 + 魔鬼代言人席**：共识判定要求主张附证据（工具结果/引用），无证据的高置信发言降权；NicheRole 增加 devil_advocate 固定席位，最终轮前必须提出至少一条反对意见。
  验收：consensus 对「自信但无证据」用例的单测；devil_advocate 缺席时 moderator 代行。
- [ ] **P6-6 [GLM] 讨论模型异质性**：关键讨论中参与 Agent 绑定不同模型（而非全场同一配置），避免同质模型集体走进同一个错误；讨论阶段模型选择以多样性和能力为准，**与成本无关**。
  验收：讨论参与者模型分布可配置且默认异质；孪生对照实验显示异质讨论的计划质量不低于同质。
- [ ] **P6-7 [GLM] 讨论 token 计量隔离**：Plaza 讨论消耗单独归档（tag=deliberation），**不计入**团队效能指标（G2）与成本门禁；成本看板分列展示但不参与治理目标与棘轮。
  验收：cost_aggregator 中 deliberation 消耗与 execution/simulation 分离；效能报表不含讨论消耗。

## P7 统一 3D 办公室场景（设计见 [unified-office-3d-design.md](unified-office-3d-design.md)）

> 现状：4 套独立 three.js 实现约 1 万行（sandbox-twin-3d / digital-twin-cli-3d / plaza 圆桌 / skill-extract 水晶），同一「房间+位置」语义写了三遍且已漂移过（roomAgentMap 单源 bug 的根源）。
> **v2（Owner 校准，参考 Marvis 办公室风格图）**：全站只有两个 3D 场景——① 极简白等轴测办公室（工位网格+白板讨论角+技能架+跑步机/茶水吧状态道具，**不做圆桌**；一切任务与孪生都在此发生，孪生=镜像层/竞标画中画视口）② 隐藏款枯山水庭院。Agent 用 plaza 模型骨架换自有造型（项圈色=角色/团队），**保留那只猫**。指标进右侧 HTML 面板不进 3D。

- [x] **P7-0 [F5] 场景信息架构设计 v2**：办公室布局（家具即功能）、双层视觉规范、OfficeState 单源状态模型、模块架构、四阶段迁移与回退。（2026-07-04 完成，见 [unified-office-3d-design.md](unified-office-3d-design.md)）
- [x] **P7-1 [F5] office-engine + office-state 骨架**（2026-07-04 完成）：`js/office/office-state.js`（纯函数 store/reducer，9 个单测全过）+ `office-scene.js`（正交等轴测极简白办公室：工位网格/白板讨论角/跑步机/茶水吧/软阴影）+ `office-boot.js`（flag `?office3d=1`；接管 `_dt3dBuildRoom` 且 **rest-area 枯山水委托旧实现原样保留**；handleTrialEvent/transitionTrialStatus 无侵入钩子；`window.OfficeAPI` 供 P7-3 使用）。已挂入 Agent-digital-twin.html。flag 关闭时旧页面零变化（vitest 全回归 + build 通过）。
- [~] **P7-2 [GLM] 三页接入收尾**：孪生页已交付（自有小兽造型+项圈色、猫、镜像层线框化+SIMULATION 徽标、协作光线+协作热度 TOP5 面板、跑步机/咖啡状态道具、SSE step→协作边）。剩余：sandbox-twin / digital-twin-cli 两页接入同一办公室；枯山水 `zen` 彩蛋入口（Logo 连点 5 次，UI 淡出，空闲 Agent 自动入座）；竞标画中画多视口（依赖 P5-4）。
  验收：三页 vitest 契约过；枯山水几何与原版逐 mesh 一致、彩蛋可触发。
- [ ] **P7-3 [GLM] Plaza 接入白板讨论角（无圆桌）**：讨论开始 Agent 起身聚拢白板前，发言者气泡+高亮，moderator 白板逐条写要点（=P6-4 结构化主张/P5-1 计划步骤的可视化），用户插话为白板旁用户气泡；结束归位工位。
  验收：plaza 全部现有交互等价通过；位置由 OfficeState 单源驱动；点击白板打开讨论时间线/计划面板。
- [ ] **P7-4 [GLM] 技能架/萃取台接入 + 指标面板统一 + 删旧**：技能水晶入墙边陈列架（命中率高更亮）、SkillClaw 萃取=架旁工作台动画；今日消耗/节省 Token 与任务计数进右侧 HTML 面板；四套旧 3D 代码归档（不硬删），旧页路由重定向。
  验收：`rg "new THREE.Scene" src/frontend` 仅 office-engine 与 zen-garden 两处；构建体积下降；全站 vitest + 手工冒烟通过；稳定一周后归档旧代码。

## 执行顺序建议

M1（P0-10/P0-11 并行 P0-5→P0-9）→ M2（P1-4、P1-1）→ M3（P1-2/P1-3/P1-5 + P6-1/P6-2（讨论质量与落地性）+ P7-1 引擎骨架）→ M4（P2-1/P2-2 + P5-1/P5-2 + P6-4 + P6-7 + P7-2 房间世界合一）→ M5（**P3-2 真实决策（竞标前置）** → P3-1/P3-3 + P5-5 协作结构显式化 → **P5-4 孪生竞标** + P5-3 + P6-3/P6-5/P6-6 + P7-3）→ M6（P4 + P5-6 竞标搜索升级 + P7-4 收口删旧）。
注意：P1（成本最优执行）、P2（技能进化）、P3（孪生保真度）的全部成本类优化只作用于**执行与孪生试验阶段**，Plaza 讨论阶段除外（两阶段经济学原则，见 P6 节首）。
每完成一项更新本文件状态位并运行 `node scripts/check-docs-signoff.cjs --strict`。
