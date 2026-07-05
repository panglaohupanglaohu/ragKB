<!-- docs-signoff: author="Claude Fable 5" kind="llm" doc="plan" ts="2026-07-05T01:14:09Z" -->
# 数字办公室协作演练闭环 Plan（讨论→计划→审查→编译→竞标演练→回流）

> 文档状态：current。配套 todos：[数字办公室协作演练todos.md](数字办公室协作演练todos.md)。
> 一句话目标：让**数字办公室**成为「Plaza 讨论产出的执行计划」被多智能体团队**真实演练与竞标**的地方，并在 3D 场景中把 Agent 之间的交互与协作**如实模拟**出来，供人肉眼考察协作能力。

## 0. 铁律与定位（不可违背）

- **两阶段经济学**：Plaza 讨论阶段不做任何 token 优化/预算约束/效能计量（智慧无价，只求不跑题+计划可落地）。成本纪律**从执行计划产生之后**才开始（编译→孪生试验→竞标→上生产）。
- **数字孪生 = 协作的观测仪器**，不是装饰。3D 里的协作光线/热度/工作流图/镜像层是「考察智能体协作能力」的读数面板。
- **演练对象是「任务」，不是抽象计划（Owner 拍板 2026-07-05）**：进入孪生演练的单位是**执行计划对应的任务**——即计划经人批准、派发到智能体团队后产生的任务；更一般地，**凡在智能体团队里运行过的任务都有资格进入演练**（含非 Plaza 来源的任务）。理由：任务带着真实执行上下文（团队/技能绑定/派发元数据/运行记录），演练结论才可迁移；抽象计划没有。由此推论：**批准门天然满足**——「运行过」必经「批准+派发」，孪生入口无需再查 plan.status，但须把任务的 plan/step 溯源元数据带进场景。内置 5 个种子场景仅作引擎自检/demo 数据，**已从演练菜单彻底移除**（数据保留供测试与闭环 demo）。

## 1. 目标闭环（端到端）

```
Plaza 讨论（集体智慧，无成本约束）
  → ExecutionPlan（结构化计划：步骤/角色/依赖/验收/预算上限）
    → 落地性审查（P6-2：每步须有 负责角色·验收·依赖·所需技能，缺项打回）
      → 编译 compile（ExecutionPlan → ScenarioSpec，source=plan，带 origin.plaza/discussion）
        → 竞标演练（同一计划 × 多候选组合[团队×技能×协作结构] → twin-trials）
          → 评分与排名（质量达标者中选 token 效益最优 → ratchet 锁定为该任务类型基线）
            → 数字办公室 3D 投影（协作交互全程可视：谁认领/执行/帮谁/交接什么/在哪一阶段）
              → 回流（竞标结论 + 协作热度 + 保真度回写讨论时间线与成本账）
```

## 2. 现状盘点（已具备 vs 缺口）

已具备（可复用，别重造）：
- **计划契约**：[execution_plan.py](../src/backend/agents/execution_plan.py) 已有 `ExecutionPlan/PlanStep/validate_plan/parse_plan_table`。
- **计划派发**：[plaza_routes.py](../src/backend/agents/plaza_routes.py) `assign_plan_to_team` 已把计划派发为任务。
- **场景编译**：[scenario_compiler.py](../src/backend/sandbox/scenario_compiler.py) `compile_scenario/match_team/generate_from_description`；[scenario_store.py](../src/backend/sandbox/scenario_store.py) 有 `source=builtin|custom|llm_generated`。
- **孪生引擎**：[twin_loop.py](../src/backend/sandbox/twin_loop.py) 真跑试炼；[llm_decision.py](../src/backend/sandbox/llm_decision.py) 定义 Agent 动作词表。
- **协作结构载体**：[world_state.py](../src/backend/sandbox/world_state.py) 有 `workflow_edges`（源→目标+传递内容）、`room_stages`、`validate_move`（阶段顺序）。
- **办公室 3D**：[office-state.js](../src/frontend/js/office/office-state.js) reducer（activities/edges/collab/meeting/facilities/mirror）+ [office-scene.js](../src/frontend/js/office/office-scene.js)（工位/白板/协作光线/递文件/镜像层/猫）+ [office-boot.js](../src/frontend/js/office/office-boot.js)（位置轮询 + step/discussion/trial_status 钩子）。

关键缺口：
- **G1 计划→场景断桥**：`ExecutionPlan` 从未编译成 `ScenarioSpec`；孪生菜单只有 builtin 种子，讨论计划进不了孪生。
- **G2 场景无来源区分**：菜单把测试样例当真实演练目标（用户已指出）。
- **G3 交互词表未全映射**：孪生 `llm_decision` 会发 `claim_task/execute_skill/delegate/communicate(broadcast)`，但办公室只渲染 help/comm 两类边，`skill_used`、委派方向、广播、`workflow_edges` 顺序与传递内容、`room_stages` 阶段迁移都没画。
- **G4 无竞标编排**：没有「同一计划跑多候选组合并排竞标」的编排与排名，ratchet 未锁定任务类型最优执行者。
- **G5 落地性审查未设卡**：编译前没有强制「每步有角色/验收/依赖/技能」的关卡。

## 3. 数字办公室交互与协作清单（要在 3D 模拟的东西）

> 数据来源均可接真实信号：动作来自 `llm_decision` 的 `agent_actions`，结构来自 `world_state.workflow_edges/room_stages`，讨论来自 plaza。下表是「交互 → 3D 表达 → 现状」。

### 3.1 个体任务动作（工位层）
| 交互 | 语义 | 3D 表达 | 现状 |
| --- | --- | --- | --- |
| `claim_task` | 认领任务 | Agent 走到任务看板取任务卡→回工位，头顶任务标签亮起 | ❌ 现只当 working |
| `work_on_task` | 执行任务 | 落座工位、屏幕点亮、轻微敲击 | ✅ 屏幕亮 |
| `execute_skill(skill_used)` | 使用某技能 | 工位上方对应技能图标脉冲 / 从墙边技能架取道具 | ❌ 未体现 skill_used |
| `idle` | 空闲 | 桌旁站立 / 去茶水吧 | ✅ |

### 3.2 协作动作（Agent↔Agent，考察协作能力的核心）
| 交互 | 语义 | 3D 表达 | 现状 |
| --- | --- | --- | --- |
| `offer_help` | 主动帮助 | 青色协作光线 A→B + 走到 B 工位旁 | ✅ help 边 |
| `delegate` | 委派下游 | 有向箭头 + 递任务卡（区别于沟通），下游头顶接任务 | ⚠️ 现归为 comm，未区分方向/语义 |
| `communicate(target=agent)` | 点对点沟通 | 蓝色光线 A→B + 气泡 | ✅ comm 边（无气泡） |
| `communicate(target=broadcast)` | 广播 | 以发言者为圆心的环形波纹，覆盖全场 | ❌ 未特殊处理 |
| `workflow_edges`(源→目标,传递内容) | 结构化交接（顺序+内容） | 工作流图连线（含内容标签），递文件动画按边的顺序推进 | ⚠️ 递文件动画有，但不读 workflow_edges 顺序/内容 |

### 3.3 讨论与计划（白板层）
| 交互 | 语义 | 3D 表达 | 现状 |
| --- | --- | --- | --- |
| 讨论进行 | 站立会议 | Agent 聚拢白板前，发言者高亮 | ✅ discussion→白板 |
| 计划步骤 | 计划要素可视 | 白板逐条写 ExecutionPlan 步骤，步骤↔负责 Agent 连线 | ⚠️ boardLines 有，但不绑定 ExecutionPlan steps |
| 落地性审查 | 缺项打回 | 缺角色/验收/依赖的步骤在白板标红，审查不过不进演练 | ❌ |

### 3.4 业务阶段与工作流拓扑（空间层）
| 交互 | 语义 | 3D 表达 | 现状 |
| --- | --- | --- | --- |
| `room_stages`/阶段迁移 | 业务阶段顺序 | 办公室按阶段分区（如 调研→开发→评审→交付 走廊分段），越阶迁移被挡 | ❌ 无阶段分区 |
| 协作拓扑 | 团队构型 | 显式工作流图（节点=角色·技能·模型档，边=依赖/传递） | ❌ 仅标量协作热度 |

### 3.5 竞标与孪生层（观测层）
| 交互 | 语义 | 3D 表达 | 现状 |
| --- | --- | --- | --- |
| 镜像层 | 生产 vs 仿真 | 家具线框化 + SIMULATION 徽标 | ✅ |
| 协作热度 | 协作强度读数 | TOP5 面板 | ✅ |
| 竞标画中画 | 多候选组合并排 | 同一计划的 N 个候选组合各占一个小视口，实时比分 | ❌（依赖竞标编排 G4） |

## 4. 架构与数据流

```
ExecutionPlan(JSON) ──compile──▶ ScenarioSpec(source=plan, origin={plaza,discussion})
        │                              │
        │ 落地性审查(P6-2)              ▼ 存 storage/scenarios/
        └─缺项打回                 GET /api/v1/scenarios?source=plan  ← 菜单「计划演练」区
                                       │
候选组合生成(团队×技能×协作结构) ──▶ twin-trials(TwinLoopEngine) ──▶ (质量, token) 评分
                                       │                                   │
                                 竞标排名(质量达标∧token最省)         ratchet 锁定基线
                                       │
                       office 3D 投影：agent_actions(step) + workflow_edges + room_stages
                                       │
                              回流：竞标结论/协作热度/保真度 → 讨论时间线 + 成本账(tag=simulation)
```

关键接口/落点：
- 后端新增 `compile_plan_to_scenario(plan) -> ScenarioSpec`（复用 scenario_compiler），`ScenarioSpec.source='plan'` + `origin`。✅已实现 `sandbox/plan_scenario_bridge.py`。
- `GET /api/v1/scenarios?source=plan|builtin` 分区；plaza「派发到孪生」触发编译落 custom store。✅已实现 `POST /api/v1/scenarios/from-plan`（审查→编译→落库）。
- 竞标编排 `bidding_orchestrator`：输入一个 scenario + 候选组合列表，输出排名，写 ratchet（`scenario_best:<plan>:<candidate>`）。
- 前端 office：`office-state` 扩交互词表；`office-scene` 加 skill 脉冲/委派箭头/广播波纹/工作流图/阶段分区/竞标画中画。

## 4.5 M4 候选生成规格（F5 亲定，GLM 按此执行不得自由发挥）

竞标候选 = 对**基线组合 C0** 施加**恰好一个变异算子**得到的组合（单步变异，效益差可归因到算子）。

- **C0（基线）**：该任务在团队中真实运行时的组合——实际团队构型 + 实际技能绑定 + 计划依赖给出的执行顺序 + 当时的模型档。C0 必须参与竞标（它是 ratchet 的现任基线）。
- **变异算子（对齐 P5-6）**：
  - R1 换角色：某步骤的负责 Agent 换成技能覆盖该步骤 required_skills 的另一 Agent（同队或增援池）。
  - R2 换技能绑定：某步骤所用技能换成 skill_router top-K 中的替代技能。
  - R3 并行化：无依赖关系的兄弟步骤从串行改并行（依赖图允许时才合法）。
  - R4 增删 Review：关键步骤（失败惩罚最高者）之后 增/删 一个评审回边。
  - R5 模型档升降：某步骤执行模型 economy⇄standard⇄frontier 相邻档变动。
- **v1 枚举策略**：C0 + 至少 3 个单算子候选，优先级 R5降档 > R3并行化 > R4加Review > R1 > R2（降本假设优先验证）；非法候选（依赖成环、技能不覆盖）在生成期过滤。
- **评分与裁决**：质量达标（成功率 ≥90% 且 rubric 验收通过）者中选 token 最省；平票取质量高者。每个候选记录 (算子, Δtoken, Δ质量, Δ协作热度) —— 这是 P5-6 搜索升级（MCTS/进化）的训练数据。
- **ratchet**：胜者写 `scenario_best:<task_type>:<candidate_hash>`，后来者须同时满足 质量不降 ∧ token 更省 才能取代。

## 5. 里程碑（先接正道，再补观测，最后竞标）

> 进度（2026-07-05 Review 校准）：**M1 数据正道后端闭环已打通**（from-plan 端点 + source 分区 + 菜单只留计划演练）。**M2 部分完成**：M2-1/M2-5 完成，M2-4 完成内容标签但「按边顺序推进」未实现（标 [~]），M2-2/M2-3 未做。M5-2 一致性关卡后端完成。剩 M1-6(任务→场景入口，语义校准新增)、M2 收尾、M3-1、M4(竞标，前置 P3-2)。
> **Review 修复（2026-07-05）**：落地性审查已统一为唯一实现 `execution_plan.validate_plan(profile='dispatch'|'twin')`，`plan_scenario_bridge.validate_plan_feasibility` 降级为适配层——两套规则分叉的风险已消除。

- **M1 数据正道（G1+G2+G5）** ✅后端：落地性审查关卡 → `ExecutionPlan` 编译成 `source=plan` 场景 → 菜单只列讨论产出计划（内置样例已从菜单移除，仍保留数据供测试/闭环 demo）。孪生第一次能演练讨论产出的计划。
- **M2 交互词表全映射（G3）** ✅状态层+3D 接入：office-state/office-scene 渲染 claim_task/execute_skill/delegate/broadcast/workflow_edges/room_stages。协作在 3D 里「看得全」。
- **M3 协作结构显式化**：标量协作热度 → 显式工作流图（复用 world_state.workflow_edges + CollaborationSOP）。
- **M4 竞标演练（G4）**：同一计划多候选组合并排 twin-trials → 排名 → ratchet 锁定 → office 竞标画中画多视口。（前置 P3-2 真实决策）
- **M5 回流与保真度**：竞标结论/协作热度/一致性回流讨论与成本账；孪生副本与真身一致性关卡（PICon 式，✅ 后端 twin_consistency）。

## 6. 验收总纲（每项 todos 各带命令级验收）

- M1：一场 Plaza 讨论 → 审查通过 → 在孪生菜单「计划演练」区出现该计划场景并可跑试炼；builtin 移到「样例自检」区且闭环 demo/测试不受影响。
- M2：注入一段含 claim_task/execute_skill/delegate/broadcast 的 step，办公室能逐一区分渲染；含 workflow_edges 的计划按边顺序递交并显示传递内容。
- M4：一份计划 → ≥3 候选组合竞标 → 选出 (质量达标∧token 最省) 者 → ratchet 记录 → 画中画可查看排名。

## 7. 风险与回滚

- 内置场景被测试/闭环 demo 依赖（test_scenario_system 断言 5 个 builtin、skill_closed_loop 依赖 code_review_delivery）：**只做来源分区，不删数据**，`?source=` 缺省仍返回全部，保证向后兼容。
- office 交互扩展全部走 feature flag `?office3d=1`，旧场景零影响；每步 vitest 守 office-state 契约。
- 竞标编排前置依赖「真实 LLM 决策模式（P3-2）」——启发式概率下竞标排名不可信，M4 须在 P3-2 之后或与之并进。
