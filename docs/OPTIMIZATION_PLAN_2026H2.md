<!-- docs-signoff: author="Claude Fable 5" kind="llm" doc="plan" ts="2026-07-04T05:52:00Z" -->
# 优化规划 2026H2 — 孪生验证的最低成本智能体团队

> 文档状态：current。北极星目标（用户定义）：**找出最有效能的智能体团队——在数字孪生环境里验证过、能完成任务且消耗 token 最少。**
>
> **两阶段经济学（用户定义的铁律）**：
> 1. **智慧阶段（Plaza 集体智慧 → 执行计划）**：不做 token 优化、不设预算、消耗不计入效能考核。目标只有一个——讨论不跑题，形成能落地、能实现、可派发的执行计划。这些智慧是无价的。
> 2. **执行阶段（计划 → 孪生竞标 → 生产执行）**：成本纪律从这里开始。同一份计划在孪生沙箱反复试验 团队×技能×协作 的候选组合，在质量达标者中选 token 效益最优的执行者上生产——**这是数字孪生的真正意义**：找到最好的团队、最优的技能与协作（Todos P5-4）。
>
> 因此本规划中 P1/P2/P3 的一切成本优化仅作用于执行与孪生试验；Plaza 讨论阶段的优化（P6）只关乎质量与落地性。G2（token/任务）只度量执行阶段。
> 配套执行清单：[OPTIMIZATION_TODOS_2026H2.md](OPTIMIZATION_TODOS_2026H2.md)（按执行模型分层标注）。
> 验证基线以 [VALIDATION.md](VALIDATION.md) 为准；本规划兼容并细化《全仓库分阶段重构路线》，不与其冲突。

## 一、现状诊断（2026-07-04 复核）

代码面：后端约 96k 行 Python，`agents/api.py` 单文件 8.8k 行；孪生沙箱（TwinLoop/场景/试炼）、技能体系（Router/Library/Extractor/Evolver）、Token 成本门禁、演进引擎四大域均已成型。
质量面（Windows 基线 2026-06-26）：lint/typecheck 通过；build 失败（three.js vendor 路径，本轮已修复）；后端测试 66 失败/952 通过，根目录 30 失败/204 通过，前端 12 失败/159 通过——失败主体是**测试与实现的契约漂移**，不是功能损坏。
结构面：三套技能存储桥接（Registry/Store/Team-local）、两套成本体系并存（Terraform LEGACY vs Token 北极星）、`.bak` 文件与巨石文件并存，说明演进快于收口。

**结论：功能骨架已经对齐业界方向（沙箱先行、技能库、成本门禁、棘轮演进），短板在于三点——闭环没有端到端打通、成本路由没有落到每次 LLM 调用、质量基线不绿导致无法安全重构。**

## 二、业界对标（2026-07 调研）

1. **成本-性能悖论与分层路由**：全部用旗舰模型成本不可承受，全部用弱模型会因单点错误级联失败；业界共识是按任务难度路由（简单任务小模型、关键决策旗舰模型），可降本 5–10×；预算约束路由可建模为 contextual bandit，在推理时拨动成本/质量旋钮。本仓库的对应物是 `token_policy` + 每个 agent 的 model binding——缺一个统一的 **ModelRouter** 在调用点生效。
2. **Agent Skills 开放标准**：SKILL.md + progressive disclosure（发现→激活→执行三级加载，正文 ≤500 行，拆分互斥上下文）已成为跨厂商标准（Anthropic 2025-12 开放，OpenAI/Google/GitHub/Cursor 已跟进）。本仓库技能是自有 JSON 模型且**全量注入 system prompt**——迁移到渐进披露可直接省 token，并让技能可被外部生态复用。
3. **孪生沙箱的价值边界**：有效的 agentic sandbox 必须镜像生产环境的接口与数据形态，agent 在沙箱中的行为方式必须与生产一致，否则演练结论不可迁移。本仓库仿真步进含启发式成功概率（熟练度结算），**孪生保真度需要用生产轨迹回放来校准**。
4. **技能库规模效应**：研究显示技能库增长存在选择相变——库越大路由越难；需要去重、淘汰与命中率跟踪（本仓库已有 similarity_engine/skill_tracker 雏形）。

## 三、目标与可量化指标

| 指标 | 定义 | 基线 | 2026H2 目标 |
| --- | --- | --- | --- |
| G1 全绿基线 | lint+typecheck+build+test 全通过 | build 失败、108 个测试失败 | 全部通过并进 CI 门禁 |
| G2 token/任务 | 标准场景集单任务平均 token 消耗 | 未度量（先建基准） | 建立基准后 ≥40% 下降 |
| G3 任务成功率 | 孪生验证团队在场景集上的完成率 | 未度量 | ≥90%（成本下降不得牺牲此项） |
| G4 孪生保真度 | 沙箱评分与生产表现的秩相关 | 未校准 | Spearman ≥0.7 |
| G5 技能命中率 | 注入技能被实际使用的比例 | skill_tracker 有数据无口径 | ≥60%，未命中技能不注入 |
| G6 演进棘轮 | 新策略发布前必须通过孪生对比门禁 | 已有 ratchet 雏形 | 100% 强制，含回滚 |

G2 与 G3 构成一对约束：**在 G3 不低于 90% 的前提下最小化 G2**——这就是「性价比」的操作化定义。

## 四、五大工作流（Pillar）

### P0 工程基线收口（其余一切的前提）
build 修复（已完成）；108 个失败测试按簇分诊：真 bug → 修实现，契约漂移 → 以代码/OpenAPI 为准修测试，环境差异（Windows 路径/GBK 编码）→ 修可移植性；`typecheck` 从 compileall 升级为 mypy/pyright 渐进覆盖；`.bak` 清理与 CI 门禁（lint+typecheck+build+test 全绿才能合并）。

### P1 成本最优执行（G2/G5）
1. **ModelRouter**：统一入口 `agents/runtime/model_router.py`，输入（任务类型、复杂度估计、剩余预算、历史成功率），输出（模型档位）；三档：`economy`（GLM-5.2 级）/ `standard` / `frontier`（Fable 5 级）；预算由既有 budget guard 扣减；路由决策与结果写入 cost_aggregator，形成 bandit 反馈数据。
2. **技能渐进披露**：技能注入从「全文进 system prompt」改为「name+description 目录 + 按需加载 instructions」，对齐 SKILL.md 标准；SkillRouter top-K 只决定目录条目，命中才加载全文。
3. **上下文预算**：tool_loop 已有 100k 字符预算，补充：工具结果分级截断、历史轮次摘要压缩、重复工具调用缓存。
4. **token/任务基准**：固定场景集 + 固定团队，跑分脚本产出 token 消耗报告，作为一切优化的前后对照。

### P2 技能进化闭环（G5/G6）
打通 演练→提取(SkillClaw Filter/Improve/Verify/Solidify)→验证→发布→路由复用 的全自动链路；发布门禁 = skill_verifier 通过 + 孪生 A/B（带技能 vs 不带技能）胜出；技能库治理：similarity 去重、命中率淘汰（连续 N 次注入未使用即降级）；技能格式与 SKILL.md 标准互转，可导入/导出外部生态技能。

### P3 孪生保真度（G4）
生产轨迹回放：把生产 tool_loop 的真实执行记录编译为孪生场景（scenario_compiler 已有基础）；启发式成功概率改为「真实 LLM 决策 + 廉价模型代练」双模式，演练用 economy 档模型跑真实决策而非随机数；drift_detector 定期比对沙箱预测分与生产实际分，偏差超阈值自动触发场景重校准。

### P4 架构收口（可持续性）
拆 `agents/api.py`（8.8k 行）为域路由模块，以 OpenAPI schema 为契约、契约测试守护；技能三存储归一到 SkillLibrary 单写入口；LEGACY Terraform 成本体系隔离到 `legacy/` 并停止新增依赖。

## 五、执行模型分层（谁干什么）

| 层 | 模型 | 适合任务 | 判据 |
| --- | --- | --- | --- |
| L-F | **Claude Fable 5**（本模型） | 跨模块架构决策、失败簇分诊定性、核心算法（ModelRouter/保真度校准）设计与首版实现、规划与验收 | 需要全局推理、错误代价高、规格不明确 |
| L-D | GLM-5.2 级普通开发模型 | 按既定模式批量改造：修契约漂移测试、拆路由文件搬运、i18n、`.bak` 清理、按模板补测试 | 有明确样例可模仿、单文件局部、可被测试机械验收 |
| 门禁 | 任一 | 所有提交过 `npm run lint && npm test` + docs 签名检查 | — |

协作协议：Fable 5 先在 Todos 中把任务写成「有验收命令的规格」，GLM 级模型照规格执行，验收命令通过即完成；不通过则升级回 Fable 5 处理。这本身就是本项目「skill + 智能体协作达到最优性价比」理念在开发流程上的自举。

## 六、里程碑

| 里程碑 | 内容 | 出口标准 |
| --- | --- | --- |
| M1 基线绿 | P0 全部 | `npm run build` + `npm test` + vitest 全绿，CI 门禁生效 |
| M2 成本可见 | P1.4 + P1.1 骨架 | token/任务基准报告 + ModelRouter 上线并有路由日志 |
| M3 省着跑 | P1.2/P1.3 | 基准对照 token 下降 ≥25%，G3 不降 |
| M4 闭环通 | P2 | 一条技能从演练自动提取→验证→发布→被路由复用，全程无人工 |
| M5 孪生可信 | P3 | G4 ≥0.7，ratchet 门禁强制化 |
| M6 收口 | P4 | api.py ≤ 1k 行/模块，契约测试覆盖全部 v1 路由 |

## 七、风险

- 契约漂移修复可能掩盖真 bug → 分诊必须由 L-F 定性后才allow L-D 批量修。
- 渐进披露可能降低技能命中率 → 以 G5 指标做 A/B，回退开关保留全量注入。
- 孪生用真实 LLM 决策会增加演练成本 → 演练一律走 economy 档 + 严格步数预算，演练成本也计入 cost_aggregator。
- 单会话大重构风险 → 遵守《全仓库分阶段重构路线》的阶段边界与 commit 粒度。

## 参考

CASTER（成本-性能悖论，arXiv:2601.19793）、SkillOrchestra（技能路由迁移，arXiv:2602.19672）、预算约束路由（contextual bandit）、Anthropic Agent Skills 开放标准与 progressive disclosure 最佳实践、agentic sandbox 镜像生产原则（Jentic）、LLM-Augmented Digital Twin 政策评估（arXiv:2603.11333）。
