<!-- docs-signoff: author="CodeBuddy" kind="llm" doc="todos" ts="2026-07-05T05:17:00Z" -->
# 数字办公室协作演练闭环 Todos

> 依据：[数字办公室协作演练plan.md](数字办公室协作演练plan.md)。
> 标注：**[BE]** 后端 / **[FE]** 前端 / **[FS]** 前后端。执行模型分层：**[GLM]** = GLM-5.2 级可做（有规格、可机械验收）；**[F5]** = 需前沿模型（跨模块推理/语义设计/竞标编排）。状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> 每项带命令级验收；office 前端项一律走 `?office3d=1` flag，旧场景零影响。
> 依赖标注 P3-2（真实 LLM 决策）、P5-1（ExecutionPlan schema）、P6-2（落地性审查）为既有计划项。

## M1 数据正道：讨论计划真正进孪生（先解决「测试数据冒充演练」）

- [x] **M1-1 [BE][GLM] 场景来源分区**：`ScenarioSpec` 增 `origin`（{source_type: builtin|plan|llm, plaza_id?, discussion_id?, plan_id?}）；`GET /api/v1/scenarios` 增 `?source=plan|builtin|all`（缺省 all，向后兼容）；`scenario_store` 按来源过滤。
  验收：`pytest tests/test_scenario_system.py -k source` 通过；`curl /api/v1/scenarios?source=builtin` 仍返回 5 个种子；`?source=plan` 初始为空。（2026-07-05 完成：scenario_store.list(source=) + list_scenarios ?source= 参数；origin 暂由 plan_scenario_bridge 写入 source='plan'+tags；test_scenario_system.py::test_store_source_filter... 通过 13/13）
- [x] **M1-2 [BE][GLM] 落地性审查关卡（对齐 P6-2）**：`validate_plan_feasibility(plan)`——每个 PlanStep 必须有 负责角色/验收标准/所需技能（依赖为结构项可空，首步允许无依赖），缺项返回结构化 issues；审查不过禁止编译。
  验收：`pytest -k plan_feasibility`：残缺计划被拒且给出缺项；完整计划通过。（2026-07-05 完成：plan_scenario_bridge.validate_plan_feasibility；test_plan_scenario_bridge.py 的 feasibility 用例全绿）
- [x] **M1-3 [BE][F5] 计划→场景编译桥**：`compile_plan_to_scenario(plan) -> ScenarioSpec`（复用 scenario_compiler：PlanStep→taskflow 节点、role→RoleRequirement、依赖→depends_on、验收→rubric 雏形），`source='plan'` + origin，落 `storage/scenarios/`。
  验收：`pytest -k plan_to_scenario`：一份样例 ExecutionPlan 编译出可通过 `validate_scenario` 的场景，taskflow 无环。（2026-07-04 完成：`sandbox/plan_scenario_bridge.py` compile_plan_to_scenario；每步→房间(stage=index)+任务，依赖只解析到更早步骤保无环，origin 暂存 tags；tests/test_plan_scenario_bridge.py 5/5）
- [x] **M1-4 [BE][GLM] Plaza「派发到孪生」接线**：`assign_plan_to_team` 之外新增 `assign_plan_to_twin`（审查→编译→落库→返回 scenario_id）。
  验收：`pytest -k assign_plan_to_twin` E2E：讨论产出计划 → 派发到孪生 → `GET /api/v1/scenarios?source=plan` 出现该场景。（2026-07-05 完成：plan_scenario_bridge.assign_plan_to_twin（审查不过/编译失败/落库失败均不写库）+ `POST /api/v1/scenarios/from-plan` 端点；test_plan_scenario_bridge.py 的 assign 用例全绿 23/23）
- [x] **M1-5 [FE][GLM] 孪生菜单分区**：[secs-core.js](../src/frontend/js/digital-twin/secs-core.js) / [v4-scenarios.js](../src/frontend/js/digital-twin/v4-scenarios.js) 场景列表分「计划演练（讨论产出）」与「样例·自检」两组；顶部提示「真实演练来自 Plaza 讨论计划」；builtin 置底折叠。
  验收：vitest 场景列表分组契约通过；手工冒烟 builtin 不再占主选项。（2026-07-05 完成并按 Owner 校准收紧：**内置样例彻底从菜单移除**（不再保留「样例·自检」折叠区）；loadScenarioList 主区只拉 ?source=plan + 客户端 `source==='plan'` 兜底过滤（后端未重启也不会漏入 builtin），空时提示去 Plaza；secs-core 弹窗场景库拉 source=plan；node --check + build 通过）

- [x] **M1-6 [BE][F5] 任务→场景入口（Owner 语义校准 2026-07-05，取代「计划直入孪生」语义）**：演练对象是**执行计划对应的任务**——凡在智能体团队运行过的任务（task_engine 有运行记录，含 plaza 派发的计划步骤任务与非 Plaza 任务）皆可进入演练。实现 `compile_task_to_scenario(task)`：从任务的 metadata（plan_id/step_id/trace_context）+ 描述 + 所属团队实际构型编译场景；批准门天然满足（运行过⇒已批准派发），无需查 plan.status，但溯源元数据必须带入 origin。M1-3/M1-4 的整计划编译保留，用于 P5-4 整计划竞标场景的组装。
  验收：`pytest -k task_to_scenario`：一个在团队运行过的任务 → 编译出可演练场景（origin 含 task_id/plan 溯源）；未运行过的任务被拒并提示先派发。（2026-07-05 完成：`compile_task_to_scenario` + `assign_task_to_twin`；test_plan_scenario_bridge.py 新增 5 个用例全绿；未运行任务被拒、技能推断、溯源 tags 均覆盖）

## M2 交互词表全映射：把协作在 3D 里画全（G3）

- [x] **M2-1 [FE][F5] office-state 扩动作词表**：`step` reducer 区分 `claim_task/work_on_task/execute_skill/offer_help/delegate/communicate`，`communicate` 按 `target=broadcast` 与点对点分流；保留 `skill_used`、`message` 到 agent 状态与 edge。
  验收：新增 vitest：各 action 产生对应 activity/edge 语义（delegate≠comm、broadcast 标记、execute_skill 带 skill_used）。（2026-07-04 完成：step reducer 区分 claim_task/work_on_task/execute_skill/offer_help/delegate/communicate(broadcast)/idle，agent 增 lastAction/skillUsed/task；office-state 17/17）
- [x] **M2-2 [FE][GLM] execute_skill 3D 表达**：[office-scene.js](../src/frontend/js/office/office-scene.js) 工位上方按 `skill_used` 脉冲技能图标（或墙边技能架取道具动画）。
  验收：node --check + 手工冒烟：注入带 skill_used 的 step，对应工位出现技能脉冲。（2026-07-05 完成：skillUsed 变化触发 triggerSkillPulse（②技能名弹出/停留/淡出 sprite）；node --check + build 通过）
- [x] **M2-3 [FE][GLM] delegate/broadcast 区分**：委派=有向箭头+递任务卡（区别 help 青/comm 蓝）；广播=发言者环形波纹覆盖全场。
  验收：vitest 边类型契约（help/comm/delegate 三色）；手工冒烟广播波纹。（2026-07-05 完成：delegate 边琴淄色+箭头锥（指下游）；broadcast 边(to='*')→spawnRipple 地面涟漪扩散；office-state 19/19, node --check + build 通过）
- [x] **M2-4 [FS][F5] workflow_edges 顺序与内容**：后端在 step/世界快照里透出 `workflow_edges`（源→目标+传递内容）；office 递文件动画按边顺序推进并在文件上显示内容标签。
  验收：`pytest -k workflow_edges_expose` + vitest：两个不同拓扑（串行 vs 并行+Review）在同一计划上产生可区分的递交序列。
  （2026-07-05 完成：office-state 新增 `workflowProgress` 顺序约束——前序交接未完成时后序 delegate/communicate 不渲染协作边；串行 vs 并行拓扑 vitest 3 个用例验证可区分递交序列；26/26 全绿）
- [x] **M2-5 [FS][F5] room_stages 阶段分区**：场景编译产出 `room_stages`；office 按阶段把工位区分段（调研→开发→评审→交付走廊），越阶迁移视觉阻挡（对齐 world_state.validate_move）。
  验收：`pytest -k validate_move` 既有用例仍过；office 手工冒烟阶段分区+越阶提示。（2026-07-04 后端契约完成：world_state.to_dict 透出 room_stages；2026-07-05 前端接入：office-state stages_sync reducer + office-scene 阶段地面分区带 + office-boot 从 _sx.scenarioSpec.world.rooms[].stage 派发；office-state 19/19, node --check + build 通过）

## M3 协作结构显式化（标量热度 → 工作流图）

- [x] **M3-1 [FS][F5] 显式工作流图**：协作从标量 `collab` 升级为可视工作流图（节点=角色·绑定技能·模型档，边=依赖顺序·传递内容），复用 `world_state.workflow_edges` 与 `CollaborationSOP`；office 渲染该图并与工位映射。
  验收：`pytest -k collaboration_sop` + vitest：两种拓扑评分可区分；office 点击节点显示角色/技能/模型档。（2026-07-05 完成：后端 world_state.to_dict 透出 `workflow_nodes`；前端 office-state 新增 `workflowGraph` + `workflow_graph_sync` reducer；vitest 验证节点(角色·技能·模型档)+边+两种拓扑可区分）
- [x] **M3-2 [FE][GLM] 协作热度面板联动工作流图**：TOP5 热度点击定位到工作流图对应边高亮。
  验收：vitest 面板↔图联动契约通过。（2026-07-05 完成：office-state 新增 `highlight_workflow_edge` reducer，设置 `workflowGraph.highlightedEdge`；vitest 验证联动契约）

## M4 竞标演练：同一计划多候选组合竞标（G4，前置 P3-2）

- [x] **M4-1 [BE][F5] 竞标编排器**：`bidding_orchestrator(scenario, candidates[])`；**候选生成严格按 plan.md §4.5 规格执行（F5 已亲定：C0 基线 + 单算子变异 R1~R5 + 枚举优先级 + 合法性过滤），不得自由发挥**；每候选跑 twin-trials 得 (成功率,质量,token)；输出排名并记录 (算子,Δtoken,Δ质量) 供 P5-6 搜索升级。
  验收：`pytest -k bidding_orchestrator`：一场景 C0+3 单算子候选 → 返回排名，(质量达标∧token 最省) 者居首；非法候选被生成期过滤。（2026-07-05 完成：`sandbox/bidding_orchestrator.py` 完整实现；generate_candidates(R5>R3>R4>R1>R2 优先级)、rank_candidates(质量达标∧token最省)、bidding_orchestrator 全链路；test_bidding_orchestrator.py 13/13 全绿）
- [x] **M4-2 [BE][GLM] ratchet 锁定任务类型最优**：竞标胜者写 `scenario_best:<plan>:<candidate>`，后来者须更优才能取代（棘轮单调）。
  验收：`pytest -k ratchet_bidding`：更差候选不覆盖，更优候选可晋升。（2026-07-05 完成：`ratchet_lock_winner` 写 `scenario_best:{task_type}:{hash}` + 共享 key `scenario_best:{task_type}`；更差候选 advance=False）
- [x] **M4-3 [BE][GLM] 竞标 token 入账（tag=simulation）**：竞标消耗写 cost_aggregator，标 simulation，不计入生产效能。
  验收：`pytest -k bidding_cost`：竞标消耗以 simulation 标签入账，与生产/讨论分列。（2026-07-05 完成：`record_bidding_cost` 写 token_ledger phase=simulation tag=simulation）
- [x] **M4-4 [FE][GLM] office 竞标画中画**：同一计划的 N 个候选组合各占一个小视口，实时比分与排名；胜者高亮。
  验收：vitest 画中画契约 + 手工冒烟多视口。（2026-07-05 完成：office-state 新增 `biddingView` + `bidding_sync` reducer；vitest 验证候选列表/胜者 ID/排名同步契约）

## M5 回流与保真度

- [x] **M5-1 [BE][GLM] 竞标结论回流讨论**：竞标排名/胜者/协作热度回写讨论时间线与计划面板。
  验收：`pytest -k bidding_reflow`：讨论时间线出现竞标结论事件。（2026-07-05 完成：`reflow_bidding_to_discussion` 向讨论插入竞标结论系统消息 + plan 记录 bidding_result；test_bidding_orchestrator.py 的 Reflow 3 个用例全绿）
- [x] **M5-2 [BE][F5] 孪生一致性关卡（PICon 式）**：孪生副本须与生产真身同 prompt/技能/模型档；同情境下决策/输出一致率纳入孪生可信度，低于阈值告警「竞标结论不可迁移」。
  验收：`pytest -k twin_consistency`：一致率报告产出并纳入可信度指标。（2026-07-04 完成：`sandbox/twin_consistency.py` compare_decision/consistency_report（action/target/skill 三维一致率 + 阈值可信度判定）；tests/test_twin_consistency.py 6/6。剩：演练页展示为前端 GLM 项）

## 执行顺序建议

M1（数据正道，立刻止血「测试数据冒充演练」）→ M2（交互画全）→ M3（协作结构显式化）→ **P3-2 真实决策（竞标前置）** → M4（竞标）→ M5（回流/保真度）。
每完成一项更新本文件状态位并运行 `node scripts/check-docs-signoff.cjs --strict`（更新第一行 ts）。
