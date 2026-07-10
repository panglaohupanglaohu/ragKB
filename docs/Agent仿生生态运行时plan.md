<!-- docs-signoff: author="Kiro" kind="llm" doc="plan" ts="2026-07-10T00:00:00Z" -->
# Agent 仿生生态运行时 Plan v2 — 物竞天择驱动的非人演化生态

> 版本：v2.0（重写）· 日期：2026-07-10
> 前置文档：
> - [`宠物团队生态仿真plan.md`](宠物团队生态仿真plan.md) §10 Phase I — "感知-意图-行为"范式泛化（PI-1~PI-6）
> - [`Agent数字孪生场景演练与技能进化plan.md`](Agent数字孪生场景演练与技能进化plan.md) — EvolutionRun 技能进化闭环
> - v1 版本（本文件历史版本）— 保留了准确的代码现状核实，本次重写在其基础上叠加"非人演化"设计
>
> **一句话目标**：Agent 不是为了执行任务而存在，而是为了维持自身内部生理平衡（Health/代谢）而存在；任务执行只是它在环境中觅食/避险/协作的副产品。**环境不给 Skill 打分，环境只放行或饿死** —— 物竞天择的客观性，来自于选择压力是代谢约束的自然结果，不是人工评分。

---

## 0. 核心立场：从"打分驱动"到"生存驱动"

v1 版本的设计是"感知→意图→行为→fitness 打分→选择"，fitness 是一个显式的复合评分函数（`composite = w1*success + w2*(1/cost) + ...`）。这仍然是**人工评分**，只是打分维度更细。

v2 的设计原则不同：

> **不设计"评分函数"，设计"死亡规则"。**

具体来说：
- Agent 有一个真实的资源账本——**Health（健康值）**，每个 tick 按代谢速率衰减，行为（调用 LLM/执行工具/等待）都消耗它，唯有"任务完成获得资源"能补充它。
- Agent 不会被"打低分"，只会在 Health 归零时进入**休眠/退役**（不删除，可复活——呼应 v1 的"可逆"设计原则）。
- **生存时长本身就是适应度**：活得久 = 这套 skill 组合/协作模式在代谢约束下是可持续的。不需要再单独设计 `composite` 公式去衡量"好不好"，"活了多久"就是答案。
- 这与本仓库 `sandbox/twin_loop.py` 已有的 `skill_proficiency` 驱动成功率机制是同构的——只是把"熟练度"的意义从"用得准不准"上升为"用得起不起"（是否消耗得起代谢成本）。

这个立场变化直接决定了 v2 与 v1 在实现上的分野：v1 需要新造一套 `FitnessRecord` 打分体系；v2 只需要给已有的 `token_budget`/`skill_proficiency`/`generation` 三个字段接上一条真实的代谢流水线，**复用更多，新造更少**。

---

## 1. PIB 认知闭环 × 代码落点（哪些是直译，哪些是工程化改写）

用户设计中的每个生物学机制，在这个平台上都有一个对应物。下表标注 **【直译】**（生物学概念可以几乎原样映射为数据结构/状态机）和 **【改写】**（生物学机制本身不可移植，需要找一个"同构但不同质"的工程等价物）。

| 生物学设计 | 平台落点 | 性质 |
|---|---|---|
| 感知层：300° 有限视野，只见同类姿态/速度/位置 | `WorldView`：Agent 只能感知同 Team 的近期事件（EventBus 窗口）+ 任务队列 + 消息流，**不能看到全局状态** | 【直译】视野限制 = 数据可见性限制 |
| 意图生成器：H/F/L 三个生理变量仲裁意图 | `mental_state = {hunger, fear, libido}`：hunger=任务/资源压力，fear=失败/阻塞应激，libido=繁殖倾向（仅在 hunger 低时才升高） | 【直译】三变量优先级仲裁直接可搬 |
| 行为层：冗余肌肉 Skill 池，电机控制器 | Agent 的 `skills: list[str]`（已有字段）就是"肌肉池"；执行动作时选择哪个 skill = 选择哪组"肌肉激活模式" | 【改写】没有物理电机，用"选 skill_id + 调用参数"代替"选肌肉+力度" |
| 盲目学习：RL 随机探索肌肉激活函数 | `twin_loop.py` 已有的 `exploration_rate` 策略参数（`_default_decision` 中 `explore > 0.5` 触发随机认领）就是"随机探索"的现有实现 | 【直译】twin_loop 已经在做这件事，只是没有显式称为"盲目学习期" |
| 从混沌到特征抽象（傅里叶基函数压缩） | skill instructions 的"提炼/固化"（`skill_evolver.evolve_skill` → `skill_library.solidify`）就是把杂乱试错压缩成稳定策略的对应物 | 【改写】没有信号处理意义上的傅里叶变换，但"多次试错→提炼成一条稳定 instructions"是同构过程 |
| 能量代谢红线：Health 损耗，能效低的行为致死 | **新增**：`HealthLedger`——每 tick 按代谢速率扣 Health，任务完成按产出回血；Health=0 → Agent 进入 `STOPPED`（复用已有 `AgentState.STOPPED`） | 【直译】这是本次最核心的新增机制 |
| 生存时长作为隐式适应度 | **新增**：`survival_time`（Agent 从 ACTIVE 到 STOPPED 的存续 tick 数），不需要额外打分，直接就是排序键 | 【直译】 |
| 军备竞赛：捕食者/猎物协作协议的对抗性升级 | 复用 `pet_ecosystem.py` 的 `chase_pairs`/`flee_pairs` 语义，泛化到"竞争同一任务的多个 Agent/skill" | 【改写】没有真实捕食者，用"资源竞争关系表"代替 |
| 信号仪式化：非语言沟通（求偶舞/循环舞） | **新增**：`plaza_engine.py` 发言前的 `declare_intention()`——不是自由文本，而是从有限的仪式化信号集合（补充/质疑/赞同/求偶/示警）中选一个，供其他 Agent"视觉焦点"式响应 | 【改写】没有物理动作，用"结构化信号枚举"代替肢体语言 |
| 自组织分工：局部规则涌现全局有序（Schooling） | eco_loop 的 tick 本身就是局部规则（每个 Agent 只看自己的感知窗口做决策），分工是多个 Agent tick 的涌现结果，**不需要额外设计"分工模块"** | 【直译】只要 tick 逻辑是纯局部的，分工自然涌现，这是架构约束不是功能开发 |
| 交配机制：跨过饱暖门槛才能繁殖，传递成功基因 | 复用已有 `team_manager.duplicate_agent`，加一道门禁：只有 Health 持续高于阈值（"饱暖"）的 Agent 才能被复制，复制时继承其当前 skill 组合（"基因"） | 【直译】duplicate_agent 已存在，新增的是门禁条件，不是复制本身 |

**关键结论**：这份表格里真正需要新写代码的只有三块——① Health 代谢账本、② 意图仲裁的三变量优先级逻辑、③ 交配门禁和信号仪式化的结构化信号集合。其余都是给现有机制换一个语义外壳、或者约束现有代码"只用局部信息"。这比 v1 提出的"新造 FitnessRecord + selection.py + collaboration_genome.py"要小得多、也更贴近现有代码的实际形态。

---

## 2. 生理状态变量（替代 v1 的 mental_state 四驱动）

v1 定义了 `task_pressure/blocked_stress/idle_drive/budget_pressure` 四个驱动。v2 收敛为三个，直接对应用户设计的 H/F/L，且明确谁压制谁：

| 变量 | 生物学原型 | 计算方式 | 上升来源 | 下降来源 |
|---|---|---|---|---|
| `hunger` (H) | 饥饿 | `1 - health / health_max` | Health 代谢消耗 | 任务完成获得资源回血 |
| `fear` (F) | 恐惧 | `min(1, recent_fail_rate + blocked_ratio)` | 近期失败、被阻塞、资源竞争中处于劣势 | 任务连续成功、脱离阻塞 |
| `libido` (L) | 繁殖倾向 | `max(0, saturation - hunger) * health_sustained_ratio` | Health 长期处于高位（"饱暖"） | hunger 或 fear 升高时被压制（`libido *= (1 - hunger)`） |

**仲裁优先级**（比 v1 的 avoid>collaborate>work>forage>rest 五级更贴近用户设计的两级压制关系）：

```
if fear > fear_escape_threshold:      intention = avoid          # 恐惧压倒一切
elif hunger > hunger_threshold:       intention = forage         # 饥饿驱动觅食(认领任务/求助)
elif libido > libido_threshold:       intention = mate           # 仅在温饱后才会触发交配意图
else:                                 intention = rest_or_idle_explore  # 空闲时进入"盲目学习"探索
```

这与 v1 的区别：v1 的 `work`（执行任务）是独立的最高优先级意图之一；v2 里"觅食"（forage，即认领/执行任务）本身就是 hunger 驱动的觅食行为，任务执行不再是"应该做的事"，而是"为了不饿死而做的事"——这是用户设计里"Agent 不为了任务而存在"的核心体现，需要在实现里保持这个语义：**意图生成器判断 hunger 时，不区分"当前已分配任务"和"待认领任务"，两者都是可觅食的资源，选哪个只看代价函数**（沿用 v1 §3 的 `task_cost` 代价函数思路，不重新发明）。

---

## 3. Health 代谢账本（核心新增）

新建 `HealthLedger`，是本计划唯一的核心新数据结构：

```python
@dataclass
class HealthState:
    agent_id: str
    health: float = 100.0          # 当前健康值，0~health_max
    health_max: float = 100.0
    metabolic_rate: float = 1.0    # 每 tick 基础代谢消耗
    survival_ticks: int = 0        # 存活 tick 数（隐式适应度）
    generation: int = 0            # 继承自父代时 +1
    parent_agent_id: str = ""      # 交配溯源
    status: str = "active"         # active | dormant（Health=0，复用 AgentState.STOPPED）
```

代谢规则（每 tick）：
1. `health -= metabolic_rate * action_cost_multiplier`（行为消耗，调用 LLM/执行工具的动作比 idle 消耗更多，复用 `budget.py` 里已有的 token 用量估算做 `action_cost_multiplier` 的来源，**不重新发明成本模型**）。
2. 任务完成 → `health = min(health_max, health + reward)`（`reward` 来自任务优先级/价值，复用 `task_engine` 已有的任务字段）。
3. `health <= 0` → `status = "dormant"`，映射到已有 `AgentState.STOPPED`（复用，不新增状态值），**不删除**，可通过 `team_manager` 现有的 revive 路径唤醒。
4. `survival_ticks` 每 tick +1，直到 dormant 为止定格——这就是隐式适应度，不需要额外的 `composite` 公式。

**这是唯一的选择压力来源**：一个 skill 组合是否"好"，不再由 LLM-as-judge 打分决定，而是由"用了这套组合的 Agent 能活多久"决定。`evolution/fitness.py`（LLM-as-judge）仍然保留用于**技能文本改写时的质量校验**（v1 §4.4 的 evolution_bridge 场景），但不再是"生态选择"的裁判，只是"变异后的质检"。

---

## 4. 盲目学习：探索期与特征抽象（复用 twin_loop，收窄改写范围）

v1 计划里没有"盲目学习"这个阶段，v2 补上，但**完全基于 twin_loop.py 已有的 `exploration_rate` 机制**改写，不新建独立的强化学习模块（这在当前架构下成本过高且偏离"胶水层"设计原则）：

- **探索期**：新 Agent（`generation=0` 或 `survival_ticks` 很低）默认 `exploration_rate` 高，倾向"盲目"尝试非最优匹配的 skill/任务组合（复用 `_default_decision` 里已有的随机认领逻辑）。
- **特征抽象**：当某个 skill 在探索期内被反复使用且 Health 净收益为正（说明"这套动作在数字物理法则下是划算的"），触发 `skill_evolver.evolve_skill` 对该 skill 的 instructions 做一次"提炼"（把试错过程中积累的 `SkillUsageRecord` 证据喂给已有的 `evolve_skill` LLM 改写流程），对应用户设计里"从混沌到高度压缩表达"。
- **随经验衰减**：`exploration_rate` 随 `survival_ticks` 增长而下降（活得越久，越倾向用已验证有效的 skill，即 v1 §4.2 提到的"fitness 驱动决策"，但这里驱动信号是 Health 净收益，不是抽象 fitness 分数）。

---

## 5. 军备竞赛：竞争性选择压力（复用 pet_ecosystem 语义，不新建对抗引擎）

用户设计中的捕食者/猎物军备竞赛，在没有真实捕食者的 Agent 生态里对应**资源竞争关系**：多个 Agent 竞争同一个任务/技能位时，一方 Health 收益的提升必然伴随另一方的相对损失。

实现方式：复用 `pet_ecosystem.py` 已有的 `chase_pairs`/`flee_pairs` 数据结构语义（而不是新写一套关系模型），把"predator/prey"泛化为"competitor 关系"：
- 当两个 Agent 的 `skill_genome` 高度重叠且竞争同一批任务时，系统标记为竞争对（`ecosystem.competitor_pairs`）。
- 竞争对中，任务分配给代价函数更优的一方（复用 v1 §3 的 `task_cost`），另一方本轮觅食失败、hunger 上升。
- **这天然形成军备竞赛**：连续觅食失败的一方 fear 上升触发 `avoid`（可能是切换技能方向/求助协作），如果长期无法适应，Health 持续走低直至 dormant——不需要额外设计"升级"机制，代谢压力本身就会驱动技能分化（同一生态位下不能有两个低效竞争者同时存活）。

---

## 6. 信号仪式化：结构化非语言信号（扩展 plaza_engine）

用户设计的求偶舞/循环舞，在 Plaza 议事场景里对应"发言前的意图信号"。v1 §4.5 已经提出了类似的 `declare_intention`，v2 把它收窄为一个**有限枚举信号集**（而不是自由文本意图），更贴近"仪式化"的本意——仪式化信号的关键特征是**形式固定、语义靠上下文推断，不是自由表达**：

```python
class RitualSignal(str, Enum):
    SUPPLEMENT = "supplement"   # 补充论据（对应"跟随游动"）
    CHALLENGE = "challenge"     # 质疑（对应"示警姿态"）
    AGREE = "agree"             # 赞同（对应"同步游动"）
    COURT = "court"             # 求偶信号 —— 仅在 libido 高时可能出现，表达"想与某个高 fitness 协作对象建立协作模式"
    DIGRESS = "digress"         # 跑题（主持人可强制拉回）
```

发言前先产出 `RitualSignal`，主持人（复用已有 `PlazaEngine` 的 moderator 角色和 `_role_priority` 排序逻辑）据此决定发言顺序和是否拉回——不新建"意图仲裁引擎"，直接扩展现有 `run_discussion` 的轮次编排。`COURT` 信号是本设计特有的一环：**当一个 Agent 的 libido 变量升高时，它在议事中会倾向发出 COURT 信号，尝试与近期协作收益高的伙伴建立更紧密的协作模式**（对应"协作模式繁殖"），这个信号被主持人观察到后可以触发"协作模式模板化"的建议（而不是自动执行，保留人工确认这道安全阀，呼应 v1 的可逆性原则）。

---

## 7. 自组织分工：架构约束而非功能模块

用户设计强调 Schooling 式分工是局部规则涌现的，**不是中心化分配的结果**。这一条在 v2 里不是一个"要新建的功能"，而是对 eco_loop 实现方式的一条**硬约束**：

> `IntentionAgent.perceive(ctx)` 只能读取该 Agent 自己的感知窗口（同 Team 近期事件 + 自己可见的任务队列），**不能传入全局最优分配结果**。

如果不遵守这条约束，随便加一个"全局调度器"来分配任务，分工看起来会更"高效"，但就不再是自组织涌现，而是回到了人类预设脚本——这违背了用户设计的核心动机（"非人类式智慧"）。这条约束需要写进代码 review checklist，而不是写成一个 todo 任务。

---

## 8. 与现有代码的接口点（复用清单，不再重复 v1 的详细代码审计）

以下机制在代码库中已经存在并可直接复用，v1 版本的现状审计部分（对 `twin_loop.py`/`evolution_bridge.py`/`trial_api.py` 的核实）依然有效，此处不重复贴代码，只列复用点：

- `sandbox/twin_loop.py`：`_settle_skill_action` 的熟练度驱动成功率公式 → 复用为 Health 净收益的计算基础。
- `sandbox/proficiency_store.py`：`aggregate_usages`/`aggregate_trial` → 复用为"特征抽象"触发条件的统计来源。
- `agents/team_manager.py`：`duplicate_agent` → 复用为交配机制的执行动作，新增门禁条件。
- `agents/models.py`：`AgentState.STOPPED` → 复用为 dormant 状态，不新增枚举值。
- `agents/skill_evolver.py`：`evolve_skill`/`apply_evolution` → 复用为特征抽象/技能提炼的执行路径。
- `agents/plaza_engine.py`：`PlazaEngine.run_discussion`/`_sort_speakers`/`_role_priority` → 复用为信号仪式化的发言顺序编排底座。
- `agents/pet_ecosystem.py`：`chase_pairs`/`flee_pairs` 语义 → 复用为竞争关系表的建模范式。
- `agents/budget/guard.py`：`BudgetGuard`/token 用量估算 → 复用为代谢消耗的成本来源。

---

## 9. 分阶段路线（对应 todos.md 的 Phase 编号）

| 阶段 | 主题 | 关键交付 | 依赖 |
|---|---|---|---|
| **Phase 1** | 生态运行时基座 | `eco_loop.py`：`IntentionAgent` 基类 + H/F/L 三变量意图仲裁 + 局部感知约束 | 无 |
| **Phase 2** | 代谢与生存 | `HealthLedger`：Health 代谢/回血/dormant 转换 + `survival_ticks` 隐式适应度 | Phase 1 |
| **Phase 3** | 盲目学习与选择 | 探索期 `exploration_rate` 衰减曲线 + 特征抽象触发（接 `skill_evolver`） | Phase 2 |
| **Phase 4** | 繁殖与淘汰 | 交配门禁（Health 阈值 + `duplicate_agent`）+ skill dominant/deprecated 状态机（沿用代谢驱动，不新增打分） | Phase 2、3 |
| **Phase 5** | 信号仪式化与自组织 | `RitualSignal` 枚举 + Plaza 发言顺序扩展 + 局部感知约束落地到 code review checklist | Phase 1（可并行） |

**不做 v1 的 Eco-6（生态全景可观测看板）**：本次重写认为可视化面板属于锦上添花，不影响核心机制是否成立，留到后续如有需要再补，本 todos 不列入。

---

## 10. 设计原则（更新）

1. **死亡规则优先于评分函数**：任何"这个 skill/Agent 好不好"的判断，优先用"Health 是否可持续"回答，只有变异质检环节才用 LLM-as-judge。
2. **局部感知是硬约束**：`perceive()` 不能访问全局最优解，分工必须是涌现的。
3. **可逆性不变**：dormant 不是删除，复用已有 `STOPPED` 状态和 revive 路径。
4. **交配不是随意复制**：`duplicate_agent` 必须挂 Health 阈值门禁，否则退化为人工选择。
5. **仪式化信号是枚举，不是自由文本**：这样才能被主持人/系统结构化处理，不依赖 LLM 去猜测意图。
6. **不新造重型子系统**：本次没有新的 `FitnessRecord`/`selection.py`/`collaboration_genome.py`，能扩展现有文件的都扩展现有文件。

---

## 11. 不做什么

- 不做真实物理仿真（流体力学/肌肉质点弹簧模型）——那是被开发平台的领域，不是 Agent 平台的领域，这里只取"代谢驱动选择"的抽象。
- 不做生态全景可视化看板（v1 Eco-6）——非核心机制，本轮不做。
- 不引入独立的强化学习训练循环——`exploration_rate` 衰减 + 现有 LLM 改写流程已经足以体现"盲目学习→特征抽象"的语义，不需要真的训练神经网络。
- 不允许任何"全局最优分配"式的调度器混入 eco_loop——这会破坏自组织涌现的设计前提。

---

*配套执行清单见：[`Agent仿生生态运行时todos.md`](Agent仿生生态运行时todos.md)*

---

## 12. 可配置参数中心（仿生生态运行时参数 Tab — 2026-07-10 新增）

之前 plan/todos 里散落的阈值常量（H/F/L 仲裁阈值、Health 代谢、探索期衰减、选择状态机、交配门禁）此前硬编码在各模块里。本次把它们收敛为**单一可配置数据源**，并在仿生生态页面新增一个独立 Tab 供人工调参，与「小虎/吱吱」生物个体配置区分开。

### 12.1 后端：单一数据源 + REST

- `src/backend/agents/runtime/eco_runtime_config.py`：`EcoRuntimeConfig` 单例 + `_DEFAULTS`（5 段），JSON 落盘 `storage/eco_runtime_config.json`（原子写）。`get_config()` 深度补全默认，`update()` 只接受已知 section/键（防脏写），`reset()` 恢复默认。
- `src/backend/agents/eco_runtime_routes.py`：`GET /api/v1/eco-runtime/config`、`GET /defaults`、`PUT /config`、`POST /reset`，`main.py` 挂载。
- **各模块从配置读取而非硬编码**（硬编码常量退为最终兜底，配置不可用时不破坏运行）：
  - `eco_loop.IntentionThresholds.from_config()` ← `mental_state` 段
  - `health_ledger.should_solidify_from_config()` / `config_health_defaults()` ← `learning`/`metabolism` 段
  - `twin_loop.compute_exploration_rate_from_config()` ← `learning` 段
  - `skill_library.evaluate_selection_state()`（`min_streak`/`dominant_usage_threshold` 留 None 时读 `selection` 段）
  - 交配门禁 `saturation_threshold` ← `mating` 段

### 12.2 可配置参数清单（5 段）

| 段 | 参数 | 含义 |
|---|---|---|
| `mental_state` | fear_escape / fear_calm / hunger_threshold / libido_threshold | H/F/L 意图仲裁阈值（§2） |
| `metabolism` | health_max / metabolic_rate / revive_ratio / saturation_threshold | Health 代谢账本（§3） |
| `learning` | exploration_base_rate / exploration_half_life / solidify_min_uses / solidify_min_gain | 盲目学习 + 特征抽象（§4） |
| `selection` | dominant_min_streak / dominant_usage_threshold | 物竞天择选择状态机 |
| `mating` | saturation_threshold | 交配门禁 |

### 12.3 前端：仿生生态页面新增 Tab

`src/frontend/pet-config.html` 用 `switchTab()` 分成两个 Tab：
- **Tab1「🐾 生物个体」**：原有小虎/吱吱卡片 + 互动关系矩阵（不变）。
- **Tab2「🧬 仿生生态运行时参数」**：按 5 段渲染带中文标签+说明的数字输入表单，`保存参数`（PUT）/`重新加载`（GET）/`恢复默认`（POST reset）。首次切到该 Tab 才懒加载。

### 12.4 验收

`pytest src/backend/tests/test_eco_runtime_config.py -q` — 10 passed（默认补全、部分更新过滤未知键、持久化重载、reset、以及 3 个模块 from_config 读取验证）。既有 108 个 eco 测试无回归。
