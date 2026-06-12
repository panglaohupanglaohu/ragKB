# Agent 数字孪生 v4 — 场景化演练 × 技能进化闭环 Plan

> 版本：v4.0 · 日期：2026-06-12
> 前置文档：`Agent数字孪生优化plan.md`（v3.0，已完成）、`Agent数字孪生优化todos.md`（v3.1，18 项全部 ✅）
> 主页面：`src/frontend/Agent-digital-twin.html`（3467 行）
> 核心后端：`src/backend/sandbox/`（twin_loop / trial_api / world_state / llm_decision …）、`src/backend/agents/`（skill_evolver / skill_library / evolution/）
> 本轮目标：**让 Agent 拥有与业务场景对应的数字孪生演练环境，并通过演练数据驱动 skill 持续进化。**

---

## 一、代码 Review 结论（本轮事实基线）

### 1.1 已具备的能力（不要重做）

| 能力 | 位置 | 状态 |
|---|---|---|
| Trial/Branch/Session 三层模型 + CRUD + SSE | `sandbox/trial_api.py`(880行) `sandbox/models.py` | ✅ 可用 |
| 仿真引擎（步进/暂停/混沌注入/并行分支） | `sandbox/twin_loop.py`(1241行) | ✅ 可用 |
| 世界状态二次映射 | `sandbox/world_state.py` | ✅ 可用 |
| LLM 决策（Qwen 接入） | `sandbox/llm_decision.py` | ✅ 可用但 skill 仅作 prompt 文本 |
| 五维评分 / SOP 萃取 / 反哺接口 | `trial_api.py` evaluate / extract-sop / feedback | ⚠️ feedback 为**模拟**实现 |
| 技能库（版本快照/lineage/回滚/发布门禁） | `agents/skill_library.py` | ✅ 可用但与试炼无关联 |
| 技能进化器（LLM 改写 instructions） | `agents/skill_evolver.py` | ✅ 可用但无调用方 |
| 进化流水线（fitness/mutator/optimizer） | `agents/evolution/` | ✅ 可用但独立运行，不连 trial |
| Trial 持久化 | `sandbox/trial_store.py` + `storage/` | ✅ 可用 |
| 前端导演台/分支管理/雷达图/弹幕/房间动效 | `Agent-digital-twin.html` | ✅ 可用 |

### 1.2 本轮要解决的四个结构性缺口

**缺口 1：环境 ≠ 业务场景。**
环境空间是写死的 6 个房间（workshop 等），`Trial.scenario` 只是一个空字符串字段。没有 Scenario 数据模型、没有场景库、没有"场景 → 初始世界状态 + 任务流 + 扰动剧本 + 验收标准"的生成机制。Agent 演练的不是业务，是抽象的任务认领游戏。

**缺口 2：skill 在仿真中没有语义。**
`twin_loop._default_decision` 只做 skill 名字匹配；`llm_decision` 把 skills 列表塞进 prompt。skill 没有熟练度、成功率、适用场景，演练结果无法归因到具体 skill，自然谈不上"调整 skill"。

**缺口 3：反哺是假的。**
`POST /twin-trials/{id}/feedback` 代码注释自认"R-02 技能分数提升（模拟）/ R-03 协作图（模拟）"——只改 trial 自身字段，不写 `skill_library`、不触发 `skill_evolver`。L3→L1 闭环断裂。

**缺口 4：三套进化设施孤岛。**
`skill_evolver`（LLM 改写）、`evolution/`（reflect→mutate→fitness→optimize）、`twin-trials`（演练数据）互不调用。演练失败数据没有进入 `mutator.reflect_on_failures`，进化候选没有回到沙箱做 A/B 验证。

**前端附加债务：** `_DTS` / `_sx` / `window._currentSessionId` 三套状态并存（v3.1 todos 第 0.3 节遗留）；3467 行单文件；无场景选择、无技能成长视图、无代际对比视图。

---

## 二、目标与设计原则

**一句话目标：** 选定一个业务场景 → 系统生成对应孪生环境 → Agent 团队在其中反复演练 → 每次演练产出 skill 级别的归因数据 → 进化引擎改写弱 skill → 新版本 skill 回沙箱验证 → 通过门禁后反哺真实团队 → 团队带着新 skill 进入下一代演练。

原则（在 v3 五原则之上新增）：

1. **场景即环境。** 每个孪生环境必须由一个 ScenarioSpec 实例化生成，禁止再硬编码房间/任务。
2. **skill 是进化的最小单元。** 评分、归因、改写、验证、反哺全部落到 skill_id + version 粒度。
3. **进化必须经过沙箱验证。** 任何 skill 变体在写回真实团队前，必须在同场景跑对照试炼且 fitness 提升。
4. **反哺走既有门禁。** 写回复用 `skill_library.evaluate_publish_gate` + `create_version_snapshot`，可回滚。
5. **不新造轮子。** 优先连通既有模块（evolution/、skill_evolver、trial_store），新增代码以"胶水层 + 数据模型"为主。

---

## 三、目标架构

```
┌──────────────────────────────── L0 场景层（本轮新增） ────────────────────────────────┐
│  ScenarioSpec 场景库（业务场景 = 客服工单/数据管道/营销投放/代码交付/容量事故…）        │
│  ScenarioCompiler: spec → 初始 WorldStateSnapshot + 任务流 + 扰动剧本 + 验收 Rubric    │
└──────────────┬───────────────────────────────────────────────────────────────────────┘
               ▼ instantiate
┌──────────────────────────────── L1 镜像层（已有，增强） ──────────────────────────────┐
│  WorldStateManager  ←  真实团队快照(teams-tree) × ScenarioSpec 合成                    │
└──────────────┬───────────────────────────────────────────────────────────────────────┘
               ▼ spawn twins (携带 SkillProficiency)
┌──────────────────────────────── L2 试炼层（已有，增强） ──────────────────────────────┐
│  Trial → Branch → Session   TwinLoop 决策消费 skill 熟练度   ChaosScript 按剧本注入    │
│  产出: SimulationStep + SkillUsageRecord(新增，skill 级归因)                           │
└──────────────┬───────────────────────────────────────────────────────────────────────┘
               ▼ evaluate (五维评分 + per-skill fitness)
┌──────────────────────────────── L3 进化层（连通既有模块） ────────────────────────────┐
│  EvolutionRun: 弱skill识别 → mutator.reflect/generate → 变体回沙箱A/B → fitness 对比   │
│  → skill_evolver.apply_evolution → skill_library 版本快照+发布门禁 → 反哺真实团队      │
└──────────────┬───────────────────────────────────────────────────────────────────────┘
               ▼ feedback (真实写回，可回滚)
            下一代 Trial（generation+1，环比对比）
```

数据闭环：`ScenarioSpec → Trial → SkillUsageRecord → SkillFitnessReport → MutationCandidate → 对照Trial → SkillVersion → AgentTwin(下一代)`

---

## 四、核心设计

### 4.1 业务场景模型（ScenarioSpec）

场景是"可实例化的环境模板"，五要素：

- **world**：房间/资源/约束（替代硬编码 6 房间，房间数量、类型由场景定义）
- **taskflow**：带依赖 DAG 的业务任务流（如 客服场景：接单→分类→查询→回复→回访）
- **roles**：场景要求的角色及最低 skill 要求（与真实团队成员做匹配/缺口提示）
- **chaos_script**：分阶段扰动剧本（step 区间 + 事件 + 概率），替代手工单发注入
- **rubric**：验收标准（KPI 目标、五维权重覆写、per-skill 期望成功率）

内置 5 个种子场景（客服工单高峰、数据管道故障恢复、营销活动投放、代码评审交付、容量事故演练），支持 JSON 自定义上传与 LLM 辅助生成（`scenario_compiler.generate_from_description`）。

### 4.2 技能熟练度模型（SkillProficiency + SkillUsageRecord）

- `SkillUsageRecord`：每个 step 中 twin 使用某 skill 的一条记录（成功/失败/耗时/上下文/失败原因），由 twin_loop 在执行动作时落盘。
- `SkillProficiency`：聚合视图 = skill_id × agent_id × scenario_type 的成功率、调用数、平均 reward 贡献、趋势。仿真决策时读取它：熟练度影响动作成功概率与耗时（让"演练多了真的变强"在仿真语义里成立）。
- 评分扩展：`TrialEvaluation` 增加 `skill_breakdown`，复用 `evolution/fitness.SkillFitnessReport` 结构。

### 4.3 演练→进化闭环（EvolutionRun）

新增编排器 `sandbox/evolution_bridge.py`（胶水层，~300 行）：

1. **识别**：从近 N 次同场景 Trial 聚合 SkillUsageRecord，找出成功率 < 阈值或 fitness 下滑的弱 skill。
2. **反思**：调 `evolution/mutator.reflect_on_failures(失败记录)` 产出失败模式。
3. **变体**：调 `mutator.generate_candidates` / `skill_evolver.evolve_skill` 生成 2–4 个 instructions 变体。
4. **验证**：为每个变体 fork 对照 Branch（同场景同种子），跑沙箱 A/B，用 `evolution/fitness.evaluate_skill` + trial 五维分对比。
5. **晋升**：胜出变体走 `skill_library.evaluate_publish_gate`，通过则 `create_version_snapshot` + `skill_evolver.apply_evolution` 写回；失败可 `rollback_version`。
6. **代际**：Trial 增加 `generation` 与 `parent_trial_id`，前端展示代际成长曲线。

支持手动触发（导演台"进化"按钮）与自动触发（trial 完成后评分低于 rubric 时建议进化，复用 nightly 机制可定时跑）。

### 4.4 前端改造方向（Agent-digital-twin.html）

1. **状态收敛（先做）**：落实 v3.1 遗留——`_sx` 唯一真源，`_DTS`/`_currentSessionId` 降级为 getter 别名；新增 `_sx.scenario`、`_sx.generation`、`_sx.skillStats`。
2. **场景选择器**：导演台顶部增加"业务场景"选区（卡片式，含场景简介/角色匹配度/历史最佳分），createTrial 携带 scenario_id；环境空间房间改为由场景 world 渲染。
3. **技能进化面板**（新视图或抽屉）：per-skill 成功率柱状图（复用 `.bar-chart-container`）、弱 skill 红色标记、"发起进化"按钮、EvolutionRun 进度流（识别→反思→变体→A/B→晋升五节点，复用 `.secs-pipeline-indicator` 样式）、版本 diff 与回滚入口。
4. **代际对比**：试炼时间轴上叠加 generation 标记；雷达图支持双代叠加（gen N vs gen N+1）。
5. **拆文件**：内联 JS 抽出为 `js/digital-twin/`（state.js / api.js / director.js / scenario.js / evolution.js / render-*.js），html 保留结构与样式（vite 已有，多入口可加）。

---

## 五、分阶段路线

| 阶段 | 主题 | 关键交付 | 依赖 |
|---|---|---|---|
| M1 | 场景化环境 | ScenarioSpec 模型 + 5 种子场景 + compiler + scenario API + 前端场景选择器 + 房间由场景渲染 | 无 |
| M2 | skill 语义化与真实反哺 | SkillUsageRecord/SkillProficiency + twin_loop 决策消费熟练度 + evaluate skill_breakdown + feedback 真实写回 skill_library | M1 |
| M3 | 进化闭环 | evolution_bridge + EvolutionRun API + 沙箱 A/B 验证 + 发布门禁晋升 + 代际字段 | M2 |
| M4 | 前端整合与拆分 | 状态收敛 + 技能进化面板 + 代际对比 + JS 拆文件 + SSE 推送进化事件 | M1–M3 可并行其 UI 部分 |

M1/M2 为基础（约 60% 工作量），M3 是价值闭环，M4 保证可用性。每阶段结束跑 `tests/` 回归 + 新增针对性 pytest。

---

## 六、风险与边界

- **LLM 成本**：EvolutionRun 每轮含多次 LLM 调用（反思+变体+judge）。限制：每轮最多 4 变体、A/B 每分支 ≤ 100 步、接入既有 cost_gate（`ci_cost_gate.py` / `cost_policy.py`）。
- **仿真失真**：熟练度影响成功率是启发式建模，不等于真实能力。缓解：反哺仅改 instructions 文本与元数据，不直接改真实执行权限；门禁中保留人工 approve 开关（沿用 SOP approve/reject UI 模式）。
- **存量兼容**：`Trial.scenario` 字符串字段保留并兼容旧数据；无 scenario_id 的旧 trial 归入 "legacy" 场景。
- **不做**：3D 可视化、多团队联合演练、真实生产流量回放——留给 v5。

---

*配套执行清单见：`Agent数字孪生场景演练与技能进化todos.md`*
