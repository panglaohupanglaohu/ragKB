<!-- docs-signoff: author="Kiro" kind="llm" doc="todos" ts="2026-07-10T00:00:00Z" -->
# Agent 仿生生态运行时 Todos v2 — 物竞天择驱动的非人演化生态

> 配套 [`Agent仿生生态运行时plan.md`](Agent仿生生态运行时plan.md)。
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> 本清单是 v1 todos 的全面重写：任务收窄为"扩展现有文件 + 一个核心新数据结构"，去掉了 v1 里被证实已存在或过度设计的部分（`FitnessRecord`、`selection.py`、`collaboration_genome.py`、生态可观测看板）。
> **执行原则**：每完成一项，跑对应 pytest 验收，通过后打勾，不再逐项等待人工 approve。

---

## Phase 1: 生态运行时基座（感知 · H/F/L 意图仲裁 · 局部感知约束）

- [x] **P1-1** 新建 `eco_loop.py`：`IntentionAgent` 基类 ✅ 已完成 2026-07-10
  文件：`src/backend/agents/runtime/eco_loop.py`（新增）
  落点：
  - `perceive(ctx) -> WorldView`：只读同 Team 近期事件窗口 + 自己可见任务队列，**不传入全局最优解**（硬约束，见 plan §7）。
  - `mental_state = {hunger, fear, libido}`，三个纯函数 `compute_hunger/compute_fear/compute_libido`（公式见 plan §2）。
  - `generate_intention(state, view) -> Intention`：`avoid > forage > mate > rest_explore` 优先级仲裁，含滞回防抖 + 单项记忆恢复。
  - `tick(ctx)`：perceive → update mental_state → generate_intention → 返回 Intention（本阶段不执行，只决策）。
  验收：`pytest src/backend/tests/test_eco_loop.py -q` — **23 passed**。覆盖三个纯函数边界值、仲裁优先级、滞回防抖、记忆恢复、`WorldView` 字段静态扫描（无 global/all_agents/optimal/assignment 标记）。

- [x] **P1-2** `PetEcosystem` 接入 `eco_loop` 验证（不改前端） ✅ 已完成 2026-07-10
  文件：`src/backend/agents/pet_ecosystem.py`（扩展，新增 `PetIntentionAgent`/`compute_pet_hunger`/`compute_pet_fear`，未改动现有 `PetEcosystem` 类）
  落点：新增一个基于 `IntentionAgent` 的 `PetIntentionAgent` 子类，复刻猫鼠的 hunger（原 `hunger_full_sec`）/fear（原 `fear_scale_D0`）公式，验证 eco_loop 抽象能等价表达现有宠物行为参数。
  验收：`pytest src/backend/tests/test_pet_ecosystem_eco.py -q` — **15 passed**。固定测试向量与 `pet-behavior.js` 的 `computeHunger`/`computeFear` 公式逐一比对数值一致；`_PET_DEFAULTS` 参数复用无漂移；fear 压制 forage 的仲裁行为验证通过。

---

## Phase 2: 代谢与生存（Health 账本 — 唯一核心新增数据结构）

- [x] **P2-1** `HealthLedger` 数据结构与代谢规则 ✅ 已完成 2026-07-10
  文件：`src/backend/agents/runtime/health_ledger.py`（新增）
  落点：
  - `HealthState` dataclass（字段见 plan §3）。
  - `HealthLedger.tick(agent_id, action_cost, reward=0.0)`：扣代谢 + 加行为成本 + 加任务回血，`survival_ticks += 1`。
  - `health <= 0` → `status="dormant"`，返回一个事件供上层映射到 `AgentState.STOPPED`（不在本文件内直接改 AgentProfile，保持职责单一）。
  - 持久化：JSON 文件落盘（`storage/health_ledger/{team_id}.json`），原子写模式参照 `ratchet_ledger.py` 的 `.tmp` + `.replace` 写法。
  验收：`pytest src/backend/tests/test_health_ledger.py -q` — **12 passed**。覆盖纯代谢致死、回血抵消代谢、dormant 后 survival_ticks 定格、revive、持久化重载一致性、sustained_ratio。

- [x] **P2-2** dormant → `AgentState.STOPPED` 映射 + revive 路径打通 ✅ 已完成 2026-07-10
  文件：`src/backend/agents/team_manager.py`（扩展，新增 `apply_health_event`/`revive_agent`）
  落点：新增 `apply_health_event(team_id, agent_id, event)`：把 `HealthLedger` 产出的 dormant 事件映射为 `agent.state = AgentState.STOPPED`；新增 `revive_agent(team_id, agent_id, health_ledger=None, revive_ratio=0.5)` 把 `STOPPED` 改回 `IDLE`，并（可选依赖注入）联动 `HealthLedger.revive` 恢复部分 Health；Health 联动异常不阻断状态复活本身。
  验收：`pytest src/backend/tests/test_team_manager_health.py -q` — **9 passed**。覆盖 dormant/revived 事件映射、未知事件不改状态、未知 team/agent 返回 None、HealthLedger 联动成功与异常降级。

---

## Phase 3: 盲目学习与特征抽象

- [x] **P3-1** 探索期 `exploration_rate` 衰减曲线 ✅ 已完成 2026-07-10
  文件：`src/backend/sandbox/twin_loop.py`（扩展，新增 `compute_exploration_rate`）
  落点：新增纯函数 `compute_exploration_rate(survival_ticks, base_rate=0.7, half_life=50) -> float`：`base_rate * 0.5 ** (survival_ticks / half_life)`，随存活时长衰减，补充现有 `strategy_params.exploration_rate` 的静态配置值——新 Agent（`survival_ticks` 低）默认更"盲目"。不改动现有 `_default_decision` 的调用方式，只新增这个函数供未来调用方选用（保持向后兼容，不破坏现有测试）。
  验收：`pytest src/backend/tests/test_exploration_decay.py -q` — **8 passed**。覆盖 ticks=0 返回 base_rate、半衰期数值验证、单调递减、异常输入防御性 clamp/兜底。既有 twin_loop 相关测试无回归。

- [x] **P3-2** 特征抽象触发条件（Health 净收益驱动 skill 提炼） ✅ 已完成 2026-07-10
  文件：`src/backend/agents/runtime/health_ledger.py`（扩展，新增 `net_gain_by_skill`/`should_solidify`）
  落点：新增 `HealthLedger.net_gain_by_skill(agent_id, skill_id, usage_records) -> dict`：接受调用方传入的 usage 记录列表（结构对齐 `proficiency_store.load_usages` 返回值，依赖注入而非硬编码 import，便于测试），按 skill 聚合净收益（复用 `reward_delta` 字段语义）。新增判定函数 `should_solidify(net_gain, usage_count, min_uses=5, min_gain=0.0) -> bool`：只返回布尔建议，不在函数内触发 `skill_evolver.evolve_skill` 调用，是否真正提炼由上层决定（避免意外烧 token）。
  验收：`pytest src/backend/tests/test_feature_abstraction.py -q` — **11 passed**。覆盖净收益正确聚合（含跨 agent/跨 skill 隔离）、should_solidify 边界条件、端到端整合场景。

---

## Phase 4: 繁殖与淘汰（交配门禁 · skill 状态机）

- [x] **P4-1** 交配门禁（duplicate_agent 前置检查） ✅ 已完成 2026-07-10
  文件：`src/backend/agents/team_manager.py`（扩展，新增 `can_mate`/`mate`）
  落点：新增 `can_mate(health_state, saturation_threshold=0.7) -> (bool, str)`（鸭子类型接受 `HealthState` 或 dict）：只有 `health/health_max >= saturation_threshold` 且非 dormant 才允许交配。新增 `mate(team_id, agent_id, health_state, saturation_threshold=0.7) -> Optional[AgentProfile]`：门禁通过后调用现有 `duplicate_agent`，并在新 agent 的 `metadata["lineage"]` 里记 `parent_agent_id` + `generation+1`（复用 `AgentProfile.metadata` 字段，不新增 dataclass 字段）。
  验收：`pytest src/backend/tests/test_mating.py -q` — **12 passed**。覆盖 health 不足拒绝、health 达标成功复制、lineage 血统链多代验证、边界阈值、真实 HealthLedger 整合。

- [x] **P4-2** skill dominant/deprecated 状态机（代谢驱动，不新增打分公式） ✅ 已完成 2026-07-10
  文件：`src/backend/agents/skill_library.py`（扩展，新增 `evaluate_selection_state`/`apply_selection_state`）
  落点：新增 `evaluate_selection_state(skill_id, team_id, net_gain_history, min_streak=3, dominant_usage_threshold=10) -> str`：接受调用方传入的净收益历史序列（依赖注入，衔接 Phase 3 的 `net_gain_by_skill`，不硬编码 import）——最近 `min_streak` 次连续为正且总次数达标 → `"dominant"`；连续为负 → `"deprecated"`；否则 `"neutral"`（防止单次波动误判）。新增 `apply_selection_state(team_id, skill_id, selection_state)`：`"dominant"` 复用现有 `solidify()`（映射 `SOLIDIFIED`）；`"deprecated"` 映射到既有 `DEGRADED`（软淘汰，不删除，可通过既有 `skill_evolver` 演化路径恢复）。
  验收：`pytest src/backend/tests/test_skill_selection_state.py -q` — **11 passed**。覆盖 dominant/deprecated/neutral 三态判定、连续性防误杀（混合信号不误判）、状态真正落到 `lifecycle_stage`、软淘汰可逆性（skill 未被删除）。既有 skill_library 相关测试无回归（发现一处与本次改动无关的预先存在的鉴权测试失败，已用 `git stash` 对比确认非本次改动引入）。

---

## Phase 5: 信号仪式化与自组织分工

- [x] **P5-1** `RitualSignal` 枚举 + Plaza 发言前信号声明 ✅ 已完成 2026-07-10
  文件：`src/backend/agents/plaza_engine.py`（扩展，新增 `RitualSignal` 枚举 + `PlazaEngine.declare_signal`）
  落点：新增 `RitualSignal` 枚举（值见 plan §6：supplement/challenge/agree/court/digress）。新增 `PlazaEngine.declare_signal(participant, perception_text) -> RitualSignal`：用**轻量关键词规则**（不调用 LLM，避免额外成本）从文本粗判信号（问号/疑问词→challenge，同意/赞同词→agree，跑题词→digress，默认→supplement），优先级 digress > challenge > agree > supplement。这是最小可行实现，不追求语义精确，只要结构化信号管道能跑通。`court` 信号留给上层调用方结合 IntentionAgent 的 libido 变量覆盖判定（本方法不感知生理状态，只提供文本基线信号）。
  验收：`pytest src/backend/tests/test_ritual_signal.py -q` — **9 passed**。覆盖各关键词映射、优先级冲突判定、枚举值固定集合校验、与既有 `_role_priority` 排序管道兼容性。既有 122 个 plaza 相关测试无回归。

- [x] **P5-2** 局部感知约束的代码 review checklist（文档任务，非代码） ✅ 已完成 2026-07-10
  文件：`docs/Agent仿生生态运行时plan.md`（已在 §7 写明）+ 本文件末尾"自组织分工检查清单"小节
  落点：不新增代码，在本 todos 文件末尾新增"自组织分工检查清单"小节，供后续 PR review 时人工核对——`IntentionAgent.perceive` 的任何子类实现，禁止读取跨 Team 的全局状态或"最优分配结果"。
  验收：checklist 已写入本文件末尾（见下方"自组织分工检查清单"小节），无需 pytest。

---

## 执行顺序

```
Phase 1（基座）→ Phase 2（代谢）→ Phase 3（盲目学习）→ Phase 4（繁殖淘汰）
                                                      ↘ Phase 5（信号仪式化，可与 Phase 3/4 并行）
```

每阶段完成后运行该阶段新增的 pytest 文件，全绿才打勾。全部 Phase 完成后跑一次仓库现有 `pytest tests/ -q` 全量回归，确认没有破坏既有测试。

---

## 自组织分工检查清单（P5-2 落地）

后续任何对 `IntentionAgent`/`eco_loop` 的修改，PR review 时必须确认：

- [ ] `perceive(ctx)` 的返回值里不包含其他 Agent 的完整状态快照，只包含"感知窗口内可见"的摘要信息。
- [ ] 没有引入任何形式的"全局最优任务分配"函数被 `generate_intention` 直接调用。
- [ ] 分工模式（如谁去做侦察/谁去觅食）必须能从"每个 Agent 独立 tick 的结果"里回溯解释，不能依赖一个外部裁决者。

---

## 与 v1 todos 的差异说明

- 删除：`FitnessRecord`、`runtime/selection.py`、`collaboration_genome.py`、Eco-6 生态可观测看板——v1 中这些属于"重新发明打分体系"，v2 改为"Health 代谢是唯一选择压力"后不再需要。
- 删除：`evolution_bridge.py`"新建"相关任务——该文件已存在且完整实现（v1 审核已核实），本轮不重复处理，如需扩展留待后续单独立项。
- 新增：`HealthLedger`（唯一核心新数据结构）、交配门禁、`RitualSignal` 结构化信号、探索期衰减曲线。
- 收窄：skill 状态机不再新造独立枚举值，复用已有 `SkillLifecycleStage`。

---

## 全量回归结果（2026-07-10）

**本次新增测试**（9 个文件，108 个测试用例，全部通过）：

| 测试文件 | 用例数 | 结果 |
|---|---|---|
| `test_eco_loop.py` | 23 | ✅ |
| `test_pet_ecosystem_eco.py` | 15 | ✅ |
| `test_health_ledger.py` | 12 | ✅ |
| `test_team_manager_health.py` | 9 | ✅ |
| `test_exploration_decay.py` | 8 | ✅ |
| `test_feature_abstraction.py` | 11 | ✅ |
| `test_mating.py` | 12 | ✅ |
| `test_skill_selection_state.py` | 11 | ✅ |
| `test_ritual_signal.py` | 9 | ✅ |
| **合计** | **108** | **全部通过** |

**新增/修改的源码文件**：
- 新增 `src/backend/agents/runtime/eco_loop.py`
- 新增 `src/backend/agents/runtime/health_ledger.py`
- 扩展 `src/backend/agents/pet_ecosystem.py`（新增 `PetIntentionAgent` 等，未改动现有 `PetEcosystem` 类）
- 扩展 `src/backend/agents/team_manager.py`（新增 `apply_health_event`/`revive_agent`/`can_mate`/`mate`）
- 扩展 `src/backend/agents/skill_library.py`（新增 `evaluate_selection_state`/`apply_selection_state`）
- 扩展 `src/backend/sandbox/twin_loop.py`（新增 `compute_exploration_rate`）
- 扩展 `src/backend/agents/plaza_engine.py`（新增 `RitualSignal`/`declare_signal`）

**全仓库回归**（`pytest src/backend/tests/ -q --ignore=test_evolution_evidence_detail.py`）：1271 passed, 5 skipped, 11 failed。
**11 个失败用 `git stash` 逐一核实为本次改动之前已存在的预先失败**（`test_api_handler_integration.py`/`test_api_integration_extended.py`/`test_frontend_auth_contract.py`/`test_request_models.py` 里的既有问题，均与 Agent 仿生生态运行时改动无关，本次会话未触碰这些文件）。另有 `test_evolution_evidence_detail.py` 一个测试收集期 `ImportError`（`agent_team_api.py` 缺少 `EvolutionCloseRequest`/`EvolutionCompleteRequest`），同样确认是预先存在、与本次改动无关的问题。

**本次会话未做的部分**（按 plan.md §11"不做什么"明确排除，非遗留债务）：
- 生态全景可视化看板（v1 Eco-6）——已在设计阶段决定不做。
- 真实强化学习训练循环——`exploration_rate` 衰减 + 现有 LLM 改写流程已经足以体现语义。
- `evolution_bridge.py` 的扩展性改造——该文件本身已存在且完整，本轮不重复处理。
- 各新增函数目前均为"胶水层 + 判定逻辑"，尚未接入生产调用链路（如 `apply_selection_state` 目前无自动化调度器定期调用，`declare_signal` 尚未接入 `run_discussion` 的实际发言流程）——这是刻意的：plan.md 强调"只返回建议，不自动触发"，真正接入调用链路需要产品侧决定触发时机与频率，留给后续迭代。

---

## Phase 6: 可配置参数中心（仿生生态运行时参数 Tab）✅ 已完成 2026-07-10

> 把散落在各模块的硬编码阈值收敛为单一可配置数据源，并在仿生生态页面新增独立 Tab 供人工调参（与小虎/吱吱生物个体区分）。

- [x] **P6-1** 后端配置单一数据源 + REST ✅
  文件：`src/backend/agents/runtime/eco_runtime_config.py`（新增）、`src/backend/agents/eco_runtime_routes.py`（新增）、`src/backend/main.py`（挂载）
  落点：`EcoRuntimeConfig` 单例 + `_DEFAULTS`（mental_state/metabolism/learning/selection/mating 五段），JSON 落盘 `storage/eco_runtime_config.json`。API：`GET /api/v1/eco-runtime/config`、`GET /defaults`、`PUT /config`（只接受已知键）、`POST /reset`。
  验收：`pytest src/backend/tests/test_eco_runtime_config.py -q` — **10 passed**。

- [x] **P6-2** 各模块从配置读取（硬编码退为兜底）✅
  文件：`eco_loop.py`（`IntentionThresholds.from_config()`）、`health_ledger.py`（`should_solidify_from_config`/`config_health_defaults`）、`twin_loop.py`（`compute_exploration_rate_from_config`）、`skill_library.py`（`evaluate_selection_state` 的 `min_streak`/`dominant_usage_threshold` 留 None 时读 config）。
  验收：配置不可用时回退内置默认，既有 108 个 eco 测试无回归；新增 3 个 from_config 读取测试通过。

- [x] **P6-3** 前端仿生生态页面新增 Tab ✅
  文件：`src/frontend/pet-config.html`（`switchTab`/`loadRuntime`/`renderRuntime`/`saveRuntime`/`resetRuntime`/`RUNTIME_META`）
  落点：Tab1「🐾 生物个体」= 原小虎/吱吱卡片 + 关系矩阵；Tab2「🧬 仿生生态运行时参数」= 5 段带中文标签的数字表单 + 保存/重载/恢复默认，接 `/api/v1/eco-runtime/*`。
  验收：node 语法检查通过；切 Tab 懒加载参数，保存/恢复默认经后端 API 往返。

- [x] **P6-4** 同步 plan 文档 ✅
  文件：`docs/Agent仿生生态运行时plan.md` §12（本次新增章节）。
