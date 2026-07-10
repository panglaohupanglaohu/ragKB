<!-- docs-signoff: author="Kiro" kind="llm" doc="plan" ts="2026-07-09T00:00:00Z" -->
# Agent 生态仿生进化模块 — Perception / Intention / Behavior + 物竞天择 Plan

> 目标：把宠物生态（`pet-behavior.js`）已验证的**整体式智能体模型**上升到真正的 **Agent** 身上——
> 让每个 `AgentProfile` 作为一个"生物"以 **感知(Perception) → 心理状态(Mental State) → 意图(Intention) → 行为(Behavior)** 的方式
> 存在于一个**生态环境（Team）**中；再用**物竞天择（Natural Selection）**的客观规律，驱动 Agent 的 **skill（基因）** 与 **协作（可遗传性状）** 的进化。
>
> 参照 Tu & Terzopoulos《Artificial Fishes》(SIGGRAPH '94) 的四层整体式模型 +（可选）达尔文种群选择。
> **核心原则：最大化复用现有地基，新代码只写"生物本体的 tick 内核 + 个体适应度聚合 + 世代选择循环"。**

---

## 0. 现状盘点（已有地基，本次不重写）

| 仿生/进化要素 | 现有落点 | 复用方式 |
|---|---|---|
| 环境事件流（感知输入） | `agents/event_bus.py` + `domain_events.py`（skill.*/agent.*/task.*，携带完整快照） | 感知层订阅 |
| 任务队列 / DAG 调度 | `agents/task_engine.py`（`AgentTask`、依赖、TASK_* 事件、evidence） | `work` 行为 + 感知任务压力 |
| 协作 / 议事 | `agents/plaza_engine.py`（多轮讨论、共识检测、自动技能抽取）、`agent_relationships.py` | `collaborate` 行为 + 协作性状 |
| 团队 / 个体模型 | `agents/models.py`（`AgentProfile`/`AgentTeam`/`SkillDefinition`）、`team_manager.py`（含 `duplicate_agent`） | 生物本体 + 繁殖 |
| 适应度评分（LLM-as-Judge） | `agents/evolution/fitness.py`（instruction_following/quality/conciseness → 复合分） | 个体/技能适应度 |
| 变异（反思式演化） | `agents/evolution/optimizer.py` + `mutator.py`、`agents/skill_evolver.py` | 基因变异 |
| 效果反馈（选择压力信号） | `agents/skill_tracker.py`（订阅 TASK_*，更新 effectiveness，自动标 DEGRADED） | 选择压力度量 |
| 不可逆锁定（抗退化棘轮） | `agents/ratchet_ledger.py` + `ratchet_routes.py`、`channels/system_evolution.py` | 世代进步锁定 |
| 前端可视化 | `system-evolution.html`、`Agent-digital-twin.html`、办公室 3D 场景 | 生态可视化面板 |

> 结论：**"物竞天择"的评分/变异/锁定三件套已存在**，缺的是①把 Agent 变成有内在驱动的"生物"，②在种群层面跑选择循环。

---

## 1. 理论映射（论文四层 + 种群选择 → 本模块）

| 层 | 论文（Artificial Fishes / 达尔文） | 本模块落点 | 状态 |
|---|---|---|---|
| 环境 | 水域 + 食物/捕食者 | **Team**（资源=任务/token 预算/技能） | 复用 team_manager |
| 感知 Perception | 视觉/温度感知 | 订阅 EventBus + 查询 task_engine/relationships → `WorldView` 快照 | 待做 |
| 心理状态 Mental State | 饥饿 H / 恐惧 F / 力竭 | 任务压力 / 阻塞应激 / 空闲驱动 / 预算压力（∈[0,1]） | 待做 |
| 意图 Intention | 带优先级的意图生成器 + 单项记忆防抖 | 后端意图内核（本次核心） | 待做 |
| 行为 Behavior | 游动/逃逸/觅食 | 映射到 task_engine / plaza / skill_evolver（**不新造执行器**） | 复用 |
| 种群选择 | 适者生存 + 遗传变异 | 个体适应度 → 繁殖(duplicate+变异)/休眠/基因流/协作强化 → 棘轮锁定 | 待做 |

> **简化原则（照抄宠物 plan 的克制）**：不做地形/流体/交配等复杂子系统。只移植对"Agent 团队协作进化"真正有用的东西：
> ① 4 个内在驱动（心理状态）；② 带优先级+单项记忆的意图生成器；③ 世代选择循环（复用已有评分/变异/棘轮）。

---

## 2. 心理状态（Mental State，论文 §4.2 泛化）

每个 Agent 每个 tick 更新 4 个驱动，均 ∈ [0,1]，单调可解释，带滞回防抖：

| 驱动 | 类比 | 上升来源（感知） | 影响的意图 |
|---|---|---|---|
| `task_pressure` | 饥饿 H | 已分配未完成任务数 + 临近 deadline：`min(1, backlog/full + deadline_urgency)` | ↑ `work` 优先级、执行速度（并发） |
| `blocked_stress` | 恐惧 F | 近期失败率 + 阻塞任务 + 缺失所需技能：`min(1, fails/window + missing_skill_ratio)` | ↑ `collaborate` / `avoid` |
| `idle_drive` | 觅食冲动 | 空闲时长 / 无任务：`min(1, idle_sec/idle_full_sec)` | ↑ `forage`（认领任务 / 自我进化） |
| `budget_pressure` | 力竭 | token 预算消耗比：`used/token_budget`（budget=0 则恒 0） | ↑ `avoid`（降级模型/延后） |

- 参数（`*_full_sec`、窗口大小、滞回阈值）落在 Agent 的 `bio.mental_state` 配置块（Phase A）。
- 纯函数实现（`compute_pressure` 等），无副作用，便于自检——对齐 `pet-behavior.js` 导出纯函数的做法。

---

## 3. 意图生成器（Intention Generator，论文 §5）

每 tick 按优先级从高到低判定，命中即生成意图并退出。**带单项短期记忆 `I_s` 防抖 + 目标切换持久化阈值**（照搬宠物内核）：

优先级（最高 → 最低）：

1. **`avoid`（最高，安全优先）**：`budget_pressure` 超阈 或 处于 `error` 状态 或 权限/审批阻断 → 降级模型 / 延后任务 / 上报。对应论文避碰。
2. **`collaborate`**：`blocked_stress` 超阈 或 当前任务需要自己不具备的技能 → 开 Plaza 讨论 / 委派(delegate) / 请求技能。
3. **`work`**：`task_pressure` 超阈 → 执行**价值最高**的可执行任务（价值=优先级×紧迫度，用代价函数选目标，类比捕猎 §6.1）。
4. **`forage`**：`idle_drive` 超阈 → 认领未分配任务；若无任务则触发**自我进化**（对自己 effectiveness 最低的技能跑 optimizer）。
5. **`rest`（默认）**：空闲，仅维护心跳。

**防抖机制**（论文 §5 单项记忆）：
- 高优先级意图（`avoid`）打断进行中的意图（如 `work`）时，把被打断意图压栈 `I_s`；打断解除后弹栈恢复，避免反复横跳。
- 任务目标切换加**持久化阈值** `persistence_threshold`：新任务代价须比当前任务低超过阈值才切换（论文 fickle/devoted）。

**目标选择代价函数**（work，类比 §6.1，去集群项）：
$$C_k = \text{cost}_k \cdot (1 + \beta \cdot \text{switch\_penalty}_k)$$
其中 `cost_k` 由任务优先级/紧迫度/依赖就绪度构成，`switch_penalty` 表示从当前任务切换到任务 k 的上下文代价（鼓励"追正在做的任务"，减少上下文抖动）。

---

## 4. 行为例程（Behavior，映射到现有能力，不新造执行器）

| 意图 | 行为例程 | 复用的现有组件 |
|---|---|---|
| `work` | 执行选定任务 | `task_engine`（executor / chat_harness），完成→发 TASK_COMPLETED（触发 skill_tracker） |
| `collaborate` | 发起/加入议事、委派子任务 | `plaza_engine`（讨论+共识+自动抽技能）、`task_engine` 子任务、`agent_relationships` |
| `forage` | 认领未分配任务 或 自我进化 | `task_engine.get_team_tasks`（PENDING 未分配）；`skill_evolver`/`optimizer.optimize_skill` |
| `avoid` | 降级/延后/上报 | `AgentProfile.fallback_model_id`、任务重排、事件上报 |
| `rest` | 心跳维护 | — |

> 行为层**只做编排/分派**，真正的 LLM 调用、任务执行、议事全部走既有通路。这保证回归面最小、与现有系统天然联动。

---

## 5. 物竞天择（Natural Selection，世代循环）

生态的"客观规律"层。**不在每帧跑**，而在**世代 tick（epoch）**跑——可手动触发或定时（复用 Phase 5 定时思路）。种群 = 一个 Team 内的 Agents。

### 5.1 基因与遗传
- **基因 = Skill**：已有 `version` / `lineage`（血统）/ `adopted_by`（横向基因流）/ `effectiveness`（表现型）。
- **表现型 = Agent 行为产出**：任务成功、协作贡献、成本效率。

### 5.2 个体适应度（Agent Fitness）
聚合已有信号，加权得单一 fitness ∈ [0,1]：
- 任务成功率（from `task_engine` evidence / EvidenceRun）
- 所拥有技能的平均 effectiveness（from `skill_tracker`）
- 协作成功度（from `plaza` 共识贡献 + `agent_relationships` 边权）
- 成本效率（token 预算利用率，越省越高）
> 复用 `evolution/fitness.py` 的 LLM-as-Judge 作为可选的"质量维度"补充。

### 5.3 选择算子（全部**可逆 + 人工门禁**）
1. **排序**：按 fitness 对种群排名。
2. **繁殖（遗传+变异）**：Top-K Agent → `team_manager.duplicate_agent`（已有）→ 继承最优技能（记 `lineage`）→ 对其中 1 个技能跑 `optimizer.optimize_skill` **变异**（version+1）。产出为**草稿**，需过棘轮+审批。
3. **休眠（可逆"死亡"）**：Bottom-K Agent → `state = STOPPED`（休眠，**不删除**）；其最优技能通过 `adopted_by` 被更适者采纳（**基因流**，不随个体消失）。
4. **协作性状进化**：成功的协作边（`agent_relationships`）加权强化，失败的衰减 → 团队组合朝高产配对演化。**让"协作"本身成为被选择的可遗传性状**。
5. **棘轮锁定（抗退化）**：通过 fitness + 棘轮双门禁的改进 → `ratchet_ledger` 不可逆锁定，防止世代回退。

### 5.4 选择门禁（照搬 EVOLUTION_PLAN 的四门）
```
候选（繁殖/变异产物）
  → GATE1 约束校验（长度/格式/语义，constraints.py）
  → GATE2 fitness > baseline（holdout 集）
  → GATE3 棘轮审查无回归（run_full_audit）
  → GATE4 CII 评级保持
  → 人工审核 diff → 采纳（version+1）→ Heritage Ledger 锁定
```
> **关键原则**：fitness 是"变好了吗"，棘轮是"没破坏别的吧"。fitness +20% 但 CII −5% → REJECTED。

---

## 6. 配置 Schema 扩展（AgentProfile，向后兼容）

在 `AgentProfile` 新增**可选** `bio` 块（放 `metadata["bio"]` 或新增 optional dataclass 字段，缺省=不启用仿生，退回现有行为）：

```jsonc
{
  "bio": {
    "enabled": false,                 // 默认关闭，显式开启才进入生态 tick
    "archetype": "worker",            // worker | coordinator | researcher …（影响默认阈值）
    "perception": {
      "event_window_sec": 60,         // 感知事件回看窗口
      "peer_scope": "team"            // team | related | all
    },
    "mental_state": {
      "task_backlog_full": 5,         // task_pressure 满值背压
      "idle_full_sec": 300,           // idle_drive 满值空闲秒数
      "fail_window": 10,              // blocked_stress 失败统计窗口
      "stress_escape": 0.55,          // 触发 collaborate 阈值
      "stress_calm": 0.35             // 恢复阈值（滞回）
    },
    "intention": {
      "beta_switch_cost": 0.2,        // 任务切换代价 β
      "persistence_threshold": 1.5    // 目标切换持久化阈值
    },
    "selection": {
      "reproduce_top_k": 1,           // 每世代繁殖数
      "dormant_bottom_k": 0,          // 每世代休眠数（默认 0=不休眠，需显式开启）
      "auto_mutate": false            // 变异是否自动（默认否，人工触发）
    }
  }
}
```

> 后端 `_AGENT_BIO_DEFAULTS` 深度合并（同 `pet_ecosystem.py` 的 `_PET_DEFAULTS` 做法），用户值覆盖默认。

---

## 7. 实施步骤（Phase A–E，每阶段独立可验证）

### Phase A — 配置 Schema（生物档案）
- `agents/models.py`：`AgentProfile` 增可选 `bio` 支持（读写 `metadata["bio"]`，`to_dict` 透出），默认不启用。
- 新增 `_AGENT_BIO_DEFAULTS` 深度合并 + 校验（向后兼容）。
- **验收**：无 `bio` 的既有 agent 序列化/加载无变化；显式 `bio.enabled=true` 时默认字段补全正确。

### Phase B — 生物行为内核（意图生成器）
- 新增 `agents/bionic/agent_behavior.py`：`perceive → update_mental_state → generate_intention → dispatch_behavior` 单 Agent tick。
- 纯函数（`compute_task_pressure`/`compute_stress`/`task_cost` …）独立可测，对齐 `pet-behavior.js` 的自检风格。
- 意图内核含单项记忆防抖 + 持久化阈值。
- **验收**：`pytest` 单元测试覆盖公式与"avoid 打断 work 后恢复"防抖；无副作用（不真正执行任务）。

### Phase C — 生态运行时（环境 tick）
- 新增 `agents/bionic/ecosystem.py`：`AgentEcosystem` 管理器——为启用 `bio` 的 agents 建感知（订阅 EventBus / 查 task_engine）、驱动 tick、把意图分派到 `task_engine`/`plaza`/`skill_evolver`。类比 `pet-ecosystem.js`。
- 单例 + 生命周期（start/stop），tick 由定时器或手动 API 驱动（**默认手动**，避免自动消耗 token）。
- **验收**：一个启用 bio 的测试 agent，注入 PENDING 任务 → tick 后进入 `work` 并提交给 task_engine（可 mock executor）。

### Phase D — 物竞天择（世代选择循环）
- 新增 `agents/bionic/selection.py`：`aggregate_agent_fitness` + `run_epoch`（排序→繁殖(duplicate+optimizer 变异草稿)→休眠→基因流→协作边强化→棘轮锁定）。
- 复用 `fitness.py` / `optimizer.py` / `skill_evolver.py` / `ratchet_ledger.py` / `agent_relationships.py`。
- **全部产物为草稿 + 人工门禁**；休眠=STOPPED 可逆；不删除任何 agent/skill。
- **验收**：对一个小种群（3–4 agents）跑 `run_epoch`，产出 fitness 排名 + 1 个繁殖草稿（过 4 门），不触碰生产状态。

### Phase E — API + 前端可视化
- `agent_team_api.py`（或新 `bionic_routes.py`）：`GET 生态快照` / `POST tick` / `POST epoch` / `GET fitness 排名` / `POST 采纳繁殖草稿`。**高危操作（休眠/采纳）需审批**。
- 前端：`system-evolution.html` 增"🧬 生态进化"面板 或 办公室 3D 用生物姿态可视化 Agent 心理状态/意图（复用宠物场景思路）。
- **验收**：面板展示各 agent 的驱动值/当前意图/fitness；手动跑一次 epoch 看到排名与草稿 diff。

---

## 8. 与既有 plan 的关系（避免重复造）

- **`EVOLUTION_PLAN.md`（技能/规则/提示词优化管线）**：本模块的 **Phase D 变异/评分/锁定直接调用它**——它是"基因变异引擎"，本模块是"种群选择框架"。二者互补，不重叠。
- **`宠物团队生态仿真plan.md`**：本模块是它的**泛化上升版**——把 2 只宠物的 P/I/B 内核推广到 N 个真实 Agent，并加种群选择。宠物场景可作为本模块的"可视化演示皮肤"。
- **`Agent数字孪生场景演练与技能进化plan.md`**：数字孪生提供"演练环境"，可作为本模块 fitness 评估的沙盒来源之一。

---

## 9. 假设与开放问题（Think-Before-Coding）

**假设**（已写入设计，如需调整请指出）：
1. 生态 = 单个 Team；跨 Team 的"物种迁移"暂不做。
2. 选择循环**默认手动触发**、产物为草稿、休眠可逆——不做无人值守的生产 agent 自动增删。
3. 心理状态用**可解释的确定性公式**（非学习得到），先跑通闭环再谈参数自适应。

**开放问题**（建议先答再进 Phase B）：
1. tick 频率：实时（秒级，贴近仿生）还是事件驱动（省 token）？默认建议**事件驱动 + 手动 epoch**。
2. "繁殖"是否真的新增 agent（种群膨胀），还是只产出"技能变异草稿"给现有 agent 采纳？默认**后者更安全**（种群规模稳定，避免 token 爆炸）。
3. 是否需要"资源约束"作为硬选择压力（如团队总 token 预算封顶，agent 竞争预算）？这会让"物竞天择"更真实但增加复杂度——建议 Phase D+ 再评估。

> 建议：Phase A→B→C 先把"单个 Agent 作为生物活起来"跑通（低风险、可观测），再进 Phase D 的种群选择（涉及适应度/繁殖，风险更高，需门禁）。

---

## 附：可配置参数中心（2026-07-10）

本 plan 中提到的可调阈值（心理状态阈值、繁殖/淘汰门槛、代谢/选择参数等）已在实现侧统一收敛为可配置数据源，并在仿生生态页面新增独立 Tab 供人工调参（与生物个体配置区分）。详见 [`Agent仿生生态运行时plan.md`](Agent仿生生态运行时plan.md) §12「可配置参数中心」。

- 后端：`src/backend/agents/runtime/eco_runtime_config.py` + `agents/eco_runtime_routes.py`（`/api/v1/eco-runtime/*`）
- 前端：`src/frontend/pet-config.html` → Tab「🧬 仿生生态运行时参数」
- 参数分 5 段：mental_state / metabolism / learning / selection / mating
