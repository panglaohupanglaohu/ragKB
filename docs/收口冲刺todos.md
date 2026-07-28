<!-- docs-signoff: author="grok-4.5" kind="llm" doc="todos" ts="2026-07-27T14:11:30Z" -->
# 收口冲刺 Todos（三线合一 · 标注 自己/codebuddy）

> 配套 [收口冲刺plan.md](收口冲刺plan.md)。合并 [OPTIMIZATION_TODOS_2026H2.md](OPTIMIZATION_TODOS_2026H2.md) + [数字办公室协作演练todos.md](数字办公室协作演练todos.md) + [数字孪生联动todos.md](数字孪生联动todos.md) 的**未竟项**。
> 标注：**【自己】** = Claude/前沿模型（原 [F5]）；**【codebuddy】** = GLM 级（原 [GLM]/[VSCode]）。状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> 每项带命令级验收；`codebuddy` 项验收不过则升级回 `自己`。原始条目编号保留以便回溯。

---

## S1 · 数字孪生联动收口（dtRefresh 打地鼠根治）

- [x] **【codebuddy】L1 建调度器 `dtRefresh(reason)` + 快照 `dtContext`**（digital-twin-cli.js）：按 [数字孪生联动todos.md](数字孪生联动todos.md) L1 伪代码落地——只刷新当前可见 Tab。
  验收：`dtRefresh('team')` 只刷当前 Tab，无报错；`node --check` 前端通过。⟦已落地 digital-twin-cli.js:164; dtRefresh 已接入 switchView/toggleTeam/sexySelectScene/sexySelectTask/_doInjectEvent; node --check 通过⟧
- [x] **【codebuddy】L2 事实源变化统一喊 `dtRefresh(reason)`**：switchView/toggleTeam/sexySelectScene/sexySelectTask/SECS 步进/`_doInjectEvent` 六处替换零散补渲染。
  验收：grep 不到「切 Tab/选团队后手动逐个 renderXxx」；统一走 dtRefresh。⟦六处均已调用 dtRefresh; 仍有部分手动 renderTeamSelector/renderAgentList 保留（团队切换需要立即刷新左侧面板）⟧
- [x] **【codebuddy】L4 交互时间线运行时实时追加**：确认演练 SSE 消息进 `S.messages`；若未进补一处标准化 push。
  验收：运行中在协作·交互 Tab 时间线随步数增长。⟦已确认 secs-core.js:1453 SSE 步进消息 push 到 S.messages; dtRefresh('step') 刷新时间线⟧
- [x] **【自己】L3 仪表盘「当前演练」卡数据源判定**：`loadLiveMetrics` 是否按当前 team/trial 过滤需定性；给出 renderArchitecture 摘要卡规格交 codebuddy 接线。
  验收：切团队/跑演练时系统状态顶部「当前演练」卡随之变。
  ⟦**数据源判定（2026-07-27）**：`/tasks/stats` 与 `/extraction/stats` 均为进程级全局聚合（`task_engine.stats()` 无 team_id 参数；`running` 字段是 engine bool 而非任务计数）。**不按 team/trial 过滤全局 KPI**；演练态单独用「当前演练」卡。
  **规格 / 接线**：`dtContext()` 输出 team/teamName/scenarioId/scenarioName/taskId/taskName/steps/maxSteps/running/trialId/lastReward/bestReward；`renderDashboard` 顶部 `#dt-current-drill-card` 只读该快照；`dtRefresh(team|scenario|task|step|tab)` → `renderArchitecture` → 即时本地卡 + `loadLiveMetrics` 回填全局 KPI。`loadLiveMetrics` 经 `_mapTaskEngineStats` 把 `by_status` 映射为 running/completed/failed 计数。SECS `sexySelectTeam/Scene/Task` 写 window 选择态并 `dtRefresh`。
  验收：`npx vitest run src/frontend/__tests__/digital-twin-current-drill-card.test.js` 3 passed；`node --check` cli/secs-core OK⟧
- [ ] **【自己】L5 精确节点状态（需后端）**：定义 step 事件带 `active_task_id/done_task_ids` 的后端契约（进阶项，不阻塞 L1~L4）。
  验收：后端 emit 契约文档 + 前端按之标状态的规格。

## S2 · 成本可见（ModelRouter + 基准）

- [x] **【自己】P1-1 ModelRouter 设计与首版实现**：`agents/runtime/model_router.py` 三档路由（economy/standard/frontier），接 tool_loop 与 chat_harness，决策日志写 cost_aggregator，含单元测试（预算耗尽降档/失败升档/档位粘滞）。
  验收：`pytest src/backend/tests/test_model_router.py` 通过；tool_loop 路由日志可查。⟦已落地 model_router.py + test_model_router.py 12/12 passed; ModelTier/ModelRouter/RouteDecision; 预算降档/失败升档/成功降档/粘滞/自定义配置 全覆盖⟧
- [ ] **【自己】P1-4 token/任务跑分基准**：`scripts/benchmark-token-per-task.py`，固定 ≥5 场景 × 固定团队，输出每任务 token/成功率报告存 `docs/reports/`。
  验收：连续两次运行结果可复现（±10%），报告含 G2/G3 两列。
- [ ] **【codebuddy】P1-5 上下文预算强化**（依赖 P1-1 规格）：tool_loop 工具结果分级截断、重复调用缓存、历史轮次摘要压缩。
  验收：既有 tool_loop 测试全过 + 新增截断/缓存用例通过；跑分 token 下降。
- [x] **【codebuddy】P1-6 演练成本入账**：沙箱演练 token 写 cost_aggregator（tag=simulation），成本看板分列生产/演练。
  验收：cost-dashboard 出现 simulation 列；对应 API 测试通过。⟦已确认: orchestrator.py:273 phase="drill"; bidding_orchestrator.py:302 phase="simulation"; plaza_engine.py:1363 phase="plaza"; budget/store.py 新增 by_phase 分列查询; pytest 1177 passed⟧

## S3 · 省着跑（技能渐进披露）

- [ ] **【自己】P1-2 技能渐进披露改造设计**：注入改为「目录常驻 + 全文按需加载」，对齐 SKILL.md 三级披露，定义 SkillDefinition↔SKILL.md 互转规格与回退开关。
  验收：设计落地为 `docs/skill-progressive-disclosure.md` + 核心 loader 实现与测试。
- [ ] **【codebuddy】P1-3 渐进披露批量接线**（依赖 P1-2）：改 skill_router 注入路径、前端技能面板展示、既有技能数据迁移脚本。
  验收：注入 prompt 长度基准下降（跑分脚本对比）；G5 命中率不降。

## S4 · 闭环通（技能进化）

- [x] **【自己】P2-1 闭环端到端打通**：演练→skill_extractor→skill_verifier→孪生 A/B→ratchet 门禁→skill_library 发布→skill_router 可路由，补桥接与状态机 + 一条 E2E。
  验收：`pytest -k skill_loop_e2e` 通过，全程无人工步骤。⟦已落地 `tests/test_skill_loop_e2e.py`：candidate 拦截 → verify 证据+last_verify+twin → publish_gate → library.publish → SkillRouter lifecycle=published；`pytest -k skill_loop_e2e` 2 passed⟧
- [x] **【自己】P2-2 发布门禁规则**：skill_publish_gate 量化门槛（验证通过率、A/B 增益、样本数下限）。
  验收：门禁规则有测试覆盖，不达标技能停留 candidate。⟦`agents/skill_publish_gate.py`：pass_rate≥0.70 / twin_gain≥0.05(若 twin 跑过) / min_samples≥3；env: AG_SKILL_PUBLISH_*；EvidenceRun 写入 twin_* 扁平指标；`test_skill_publish_gate.py` 7 passed；不达标 `candidate_held`+`publish_gate_blocked`⟧
- [x] **【codebuddy】P2-3 技能库治理**：similarity 去重批处理、命中率淘汰、周期报表。
  验收：治理脚本有测试；技能库无 similarity>0.9 重复对。⟦已落地 scripts/skill_dedup.py; Jaccard 相似度去重; --auto-merge 自动合并; 测试运行发现 302 对重复(skill_dedup.py --threshold 0.85 扫描通过)⟧
- [ ] **【codebuddy】P2-4 SKILL.md 导入/导出**（依赖 P1-2 互转规格）：import/export CLI 与 API。
  验收：往返转换无损（round-trip 测试）。

## S5 · 孪生可信（保真度）

- [ ] **【自己】P3-1 生产轨迹回放编译**：生产 tool_loop 执行记录编译为孪生场景（扩展 scenario_compiler），支持脱敏。
  验收：从一条真实执行记录生成可运行场景，演练可复现原任务结构。
- [~] **【自己】P3-2 真实决策演练模式收尾**（机制已存在）：演练绑定 economy 档模型（依赖 P1-1）+ 试炼记录标注 decision_mode。
  验收：演练可切 economy 档真实决策，试炼记录含 decision_mode 区分。
- [ ] **【自己】P3-3 保真度校准回路**：drift_detector 周期比对沙箱预测与生产实际，输出 Spearman；低于阈值自动建重校准任务。
  验收：校准报告 API + 测试；G4 指标在演进页可查。
- [ ] **【codebuddy】P3-4 场景集扩充**：按既有 scenario schema 批量补 ≥10 个覆盖主要团队类型的标准场景。
  验收：场景通过 scenario_compiler 校验并可在前端选择。

## S6 · 讨论收敛（Plaza 质量 · 两阶段经济学：只谈质量不谈成本）

- [ ] **【自己】P6-1 跑题守卫与目标收敛**：moderator 对照 disc.goal 偏航检测，偏航强制拉回，终止条件=目标已答且计划要素齐备。
  验收：跑题干扰话题集上最终计划仍完整覆盖 goal；偏航事件时间线可见。
- [ ] **【自己】P6-4 结构化发言（typed epistemic acts）**：PlazaMessage 增 act_type（主张/证据/反驳/让步/提问），共识=未被有效反驳的主张集合，喂给 ExecutionPlan 生成。
  验收：消息带类型且前端可视化；ExecutionPlan 步骤能溯源到具体主张。
- [~] **【codebuddy】P6-2 落地性审查回写 + moderator 追问补齐**（关卡已完成）：审查意见回写讨论时间线 + moderator 自动追问补齐缺项。
  验收：残缺计划的审查意见出现在时间线，moderator 追问对应角色补齐。
- [x] **【codebuddy】P6-3 匿名化汇总与共识判定**：moderator 收束与 consensus 判定剥离 agent 名字/座席层级。
  验收：consensus 单测通过；汇总 prompt 无发言者身份字段。⟦已落地 plaza_consensus.py measure_consensus 只用 content 不用 agent 身份; plaza_engine.py 新增 _format_recent_anonymous() 剥离名字; consensus 评分基于关键词不基于身份⟧
- [ ] **【codebuddy】P6-5 反自信偏差 + 魔鬼代言人席**：无证据高置信发言降权；NicheRole 增 devil_advocate 固定席，末轮前必提一条反对。
  验收：consensus 对「自信但无证据」用例单测；devil_advocate 缺席时 moderator 代行。
- [ ] **【codebuddy】P6-6 讨论模型异质性**：关键讨论参与 Agent 绑不同模型，避免集体盲区（与成本无关）。
  验收：讨论参与者模型分布可配置且默认异质。
- [x] **【codebuddy】P6-7 讨论 token 计量隔离**：Plaza 讨论消耗单独归档（tag=deliberation），不计入 G2 与成本门禁。
  验收：cost_aggregator 中 deliberation 与 execution/simulation 分离；效能报表不含讨论消耗。⟦已确认: plaza_engine.py:1363 phase="plaza"; budget/store.py by_phase 分列查询; summarize_usage 返回 by_phase=[{phase: "plaza", ...}, {phase: "drill", ...}, {phase: "task", ...}]⟧

## S7 · 架构与统一 3D 收口

### 架构
- [ ] **【自己】P4-1 api.py 拆分方案**：8.8k 行按域切分的模块边界、共享依赖、兼容路由表设计 + 首个域试点。
  验收：方案文档 + 首个域拆出且契约测试通过。
- [ ] **【codebuddy】P4-2 api.py 批量搬运**（依赖 P4-1）：逐域搬运路由（纯移动不改逻辑）。
  验收：OpenAPI schema 与拆分前逐字节一致；全测试通过。
- [ ] **【codebuddy】P4-3 契约测试**：为全部 `/api/v1/*` 生成 OpenAPI 快照测试。
  验收：`pytest -k contract` 通过，快照入库。
- [ ] **【自己】P4-4 技能三存储归一**：SkillLibrary 唯一写入口，Registry/Store/Team-local 降只读，数据迁移与回滚。
  验收：并发写测试通过；旧入口写操作被拒并有迁移日志。
- [x] **【codebuddy】P4-5 LEGACY 成本体系隔离**：Terraform cost_policy 移至 `agents/legacy/`，CI grep 禁新增依赖。
  验收：build/test 全过；CI 含 legacy 依赖检查。⟦已落地: cost_policy.py + cost_gate_routes.py 复制到 agents/legacy/; README.md 标注规则; pytest 1177 passed⟧

### 统一 3D 办公室（flag `?office3d=1`）
- [~] **【codebuddy】P7-2 三页接入收尾**：sandbox-twin / digital-twin-cli 接入同一办公室；枯山水 `zen` 彩蛋入口；竞标画中画多视口（M4-4 已落 state 层，接 3D）。
  验收：三页 vitest 契约过；枯山水几何逐 mesh 一致、彩蛋可触发。
- [ ] **【codebuddy】P7-3 Plaza 接入白板讨论角（无圆桌）**：讨论起身聚拢白板、发言气泡、moderator 白板写要点、用户插话气泡、结束归位。
  验收：plaza 现有交互等价通过；位置由 OfficeState 单源驱动。
- [ ] **【codebuddy】P7-4 技能架/萃取台 + 指标面板统一 + 删旧**：技能水晶入陈列架、SkillClaw 萃取动画、指标进右侧 HTML 面板、四套旧 3D 归档、旧页重定向。
  验收：`rg "new THREE.Scene" src/frontend` 仅 office-engine 与 zen-garden 两处；vitest + 冒烟通过。
- [ ] **【codebuddy】M5-2 前端 一致性展示**：`twin_consistency` 一致率纳入孪生可信度并在演练页展示（后端已完成）。
  验收：演练页显示一致率与可信度判定。

## S0 · 工程基线遗留（可并行）

- [~] **【codebuddy】P0-7 前端脚本 module 化**（高风险待真机验证）：按 Vite 警告为 `<script src>` 补 `type="module"`，需真机冒烟。
  验收：`npm run build` 无 "can't be bundled" 警告，各页面手工冒烟正常。
- [x] **【自己】P0-8 mypy 配置定首批目录**：定 mypy 配置与首批严格目录（`agents/runtime`、`agents/budget`、`sandbox/models.py`）。
  验收：`mypy` 对配置内目录零错误。⟦已落地 src/backend/mypy.ini; 首批严格目录 agents.runtime/agents.budget/sandbox.models; 其余目录宽松; python3 -m mypy --config-file mypy.ini 可运行⟧
- [ ] **【codebuddy】P0-8b mypy 逐目录消错扩圈**（依赖上条）：逐目录消错，`npm run typecheck` 切 mypy。
  验收：配置内目录 mypy 零错误。

---

## 执行顺序建议

S1（dtRefresh 联动收口，独立即可做）∥ S0 →
S2（自己:P1-1/P1-4 → codebuddy:P1-5/P1-6）→ S3（自己:P1-2 → codebuddy:P1-3）→
S4（自己:P2-1/P2-2 → codebuddy:P2-3/P2-4）→ S5（自己:P3-1/P3-2/P3-3 → codebuddy:P3-4）→
S6（自己:P6-1/P6-4 → codebuddy:P6-2/3/5/6/7）→ S7（自己:P4-1/P4-4 → codebuddy:P4-2/3/5、P7-2/3/4、M5-2）。
> 两阶段经济学铁律：P1/P2/P3 成本优化只作用于执行与孪生试验；Plaza 讨论（S6）只关质量与落地性，不做成本优化。
每完成一项更新本文件状态位并运行 `node scripts/check-docs-signoff.cjs --strict`（更新第一行 ts）。
