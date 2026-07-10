<!-- docs-signoff: author="Claude" kind="llm" doc="plan" ts="2026-07-10T00:00:00Z" -->
# 物竞天择数字孪生演练 Plan — 从「执行协作」到「被环境选择」

> 版本：v1.0 · 日期：2026-07-10 · 作者：Claude（本轮）
> 前置：
> - [`Agent仿生生态运行时plan.md`](Agent仿生生态运行时plan.md)（Claude）— PIB 认知闭环 + Health 代谢 + 交配/淘汰
> - [`Agent数字孪生场景演练与技能进化plan.md`](Agent数字孪生场景演练与技能进化plan.md)（CodeBuddy）— SECS 演练管线 + Trial/Branch/Session
> - [`宠物团队生态仿真plan.md`](宠物团队生态仿真plan.md)（CodeBuddy）— 猫鼠 PIB 原型
>
> **一句话目标**：当团队处于仿生（eco）模式时，数字孪生演练不再是"让 Agent 执行预设协作"，而是把 Agent 放进一个有**代谢红线 + 生存博弈 + 随机繁衍**的生境里，让 Skill 与协作协议**被环境选择出来**——生存时长是唯一隐式适应度，没有上帝视角人工评分。

---

## 0. 作者标注约定（贯穿本文档与配套 todos）

本项目由两个 AI 协作构建，为便于追溯，全文用以下标记区分归属：

- **【CodeBuddy】** — 既有代码/文档，本轮之前由 CodeBuddy 构建。
- **【Claude】** — 本轮（2026-07-09~10）由 Claude 新增/改写。
- **【待做】** — 本 plan 提出、尚未实现的设计。

> 归属依据：`docs-signoff` 的 `author` 字段 + git 历史 + 本轮会话记录。若某项跨两者，标注为 **【CodeBuddy→Claude】**（既有基座 + 本轮扩展）。

---

## 1. 现状：两套"演练"语义并存，尚未打通

| 能力 | 归属 | 现状 |
|---|---|---|
| SECS 演练管线（L1 MADTwin→L2 A3S→L3 TwinLoop→L4 MADCG） | 【CodeBuddy】 | `Agent-digital-twin.html` 右侧面板 + `sandbox/twin_loop.py` |
| Trial/Branch/Session 三层模型 + 五维评分 | 【CodeBuddy】 | `sandbox/trial_api.py`、`sandbox/models.py` |
| 达尔文棘轮演化模式 `_run_evolutionary`（多代进化、只进不退） | 【CodeBuddy】 | `twin_loop.py::_run_evolutionary`（已存在！保留 top50% + 变异） |
| 混沌注入（断网/离场/技能退化/幻觉/死锁…） | 【CodeBuddy】 | `twin_loop.py::inject_chaos_event` |
| 熟练度驱动动作成功率 `_settle_skill_action` | 【CodeBuddy】 | `skill_proficiency` → 成功概率 |
| **PIB 认知闭环（感知→H/F/L意图→行为）** | 【Claude】 | `agents/runtime/eco_loop.py` |
| **Health 代谢账本（代谢/回血/dormant/生存时长）** | 【Claude】 | `agents/runtime/health_ledger.py` |
| **交配门禁 + skill 选择状态机** | 【Claude】 | `team_manager.can_mate/mate`、`skill_library.evaluate_selection_state` |
| **可配置参数中心 + 前端 Tab** | 【Claude】 | `eco_runtime_config.py`、`pet-config.html` Tab2 |

**核心缺口（本 plan 要解决）**：上面两组能力是**平行的**——数字孪生演练（CodeBuddy 的 twin_loop）用的是「reward 打分 + 熟练度」模型，而仿生生态（Claude 的 eco_loop/health_ledger）用的是「Health 代谢 + 生存时长」模型。**演练时并没有真正跑物竞天择**：twin_loop 的 `_calculate_reward` 仍是人工设计的加权评分，不是"活得久=适者"。

---

## 2. 目标形态：仿生模式下的数字孪生 = 自然选择生境

当被演练团队 `runtime == "eco"`（仿生模式）时，数字孪生演练切换为**自然选择生境**：

### 2.1 环境作为「严酷审计师」（用户设计 §1 → 落点）

| 用户设计机制 | 落点（复用/新增） | 归属 |
|---|---|---|
| 能量代谢红线：动作耗 Health，能效低→饿死→参数抹除 | 复用【Claude】`HealthLedger.tick(action_cost, reward)`；演练每步按 twin 动作代价扣 Health | 【Claude→待做】接进 twin_loop 每步 |
| 饥饿度 H 强制仲裁：赤字时中断协作转进食 | 复用【Claude】`eco_loop.generate_intention`（H>阈值→forage） | 【待做】twin 决策改走 eco_loop |
| 性欲 L 能量门槛：只有"饱暖"个体繁衍 | 复用【Claude】`compute_libido`（被 hunger 压制）+ `can_mate` | 【待做】演练代际间触发 mate |
| 隐式适应度=生存时长 | 复用【Claude】`HealthState.survival_ticks` | 【待做】替代 `_calculate_reward` 作为选择键 |
| 基因抹除：Health=0→移除→参数不遗传 | 复用【Claude】dormant（STOPPED，可逆）；演练内可选"真移除出种群" | 【待做】演化模式内淘汰 |

### 2.2 求偶/繁衍 = Skill 混合遗传（用户澄清）

> 用户明确："求偶与繁衍是指将 Skill 混合后遗传给其他 Agent 的过程，或者说复合型 Skill 构建的过程。"

- 两个高生存时长 Agent「交配」→ 后代 `skill_genome` = 双亲 skill 的**选择与交叉**（复合型 Skill）。
- 落点：扩展【Claude】`team_manager.mate` —— 当前只复制单亲，需改为**双亲 skill 交叉** + 变异（可选调【CodeBuddy】`skill_evolver` 做一次提炼）。
- 归属：【Claude→待做】。

### 2.3 混合驱动：学习(RL) + 进化(EA)（用户设计 §4）

- 个体学习：复用【CodeBuddy】`_settle_skill_action` 的 session 内"练熟"效应 + 【Claude】`compute_exploration_rate`（探索期衰减）。
- 群体进化：复用【CodeBuddy】`_run_evolutionary`（多代 top50%+变异）+ 【Claude】`survival_ticks` 作为选择键。
- 决策震荡防抖：复用【Claude】`eco_loop` 的单项短期记忆（avoid 打断 forage 后恢复）。

---

## 3. 关键设计：演练模式判定与「双形态」页面

### 3.1 演练模式判定

```
被演练团队.runtime == "eco"  →  自然选择生境（Natural Selection Drill）
被演练团队.runtime == "legacy"（默认）  →  现有 SECS 演练（reward 模型，CodeBuddy 原样保留，不回归）
```

- 判定来源：team/agent 配置的 `runtime` 字段（【Claude】Agent仿生生态运行时 plan §4.1 已定义，待落地到 AgentProfile）。
- **向后兼容硬约束**：legacy 团队的演练行为**零变化**（CodeBuddy 的 twin_loop 现有路径不动），只有 eco 团队才走新生境。

### 3.2 数字办公室 → 双形态页面（用户观察："3D 窗口不同，右侧菜单也不同"）

用户点「数字办公室」进入演练页后，**左侧 3D + 右侧菜单都随模式切换**：

| 区域 | Legacy 模式（CodeBuddy 现状） | Eco 模式（本 plan 新增） | 归属 |
|---|---|---|---|
| 左 3D | 办公室工位 + Agent 头像 + 协作热度 | 生境视图：Agent 显示 **Health 血条 / 饥饿度 / 生存时长**，捕食-猎物/竞争连线，死亡个体变灰淡出 | 【待做】 |
| 右菜单 | SECS Pipeline + What-if/并行/演化 + 注入故障 + 五维评分 | **生境控制台**：代谢参数（读 eco-runtime config）+ 世代循环（run epoch）+ 种群面板（存活数/世代/fitness 分布=生存时长）+ 基因池（dominant/deprecated skill）+ 繁衍谱系 | 【待做】 |

- 右菜单参数**直接复用**【Claude】`/api/v1/eco-runtime/config`（已做），无需另造配置。
- 实现方式：`Agent-digital-twin.html` 加一个 `mode` 判定，eco 模式渲染新的右侧「生境控制台」面板（与现有 SECS 面板并存，按 mode 显隐）。

---

## 4. 后端演练内核：`eco_drill`（自然选择生境）

新增 `sandbox/eco_drill.py`（【待做】），作为 eco 模式的演练引擎，**编排既有零件而非重造**：

```
每一步 step（生境 tick）:
  for twin in 存活种群:
    view   = 感知(受限视野, 复用 eco_loop.WorldView)          【Claude 已有】
    intent = eco_loop.generate_intention(H/F/L, view)         【Claude 已有】
    action = 执行意图例程(work/collab/forage/mate/avoid)      【CodeBuddy twin_loop 分派】
    cost   = 动作代谢成本(复用 _settle_skill_action 的熟练度)  【CodeBuddy】
    reward = 觅食/任务产出                                     【CodeBuddy】
    HealthLedger.tick(twin, cost, reward)                     【Claude 已有】
    if health<=0: 标记死亡, 退出种群(基因不遗传)               【Claude dormant】
  每 epoch(世代):
    排序(生存时长) → top 存活者 mate(skill 交叉遗传) → 变异     【Claude mate + 待做交叉】
    dominant/deprecated skill 状态迁移                        【Claude 已有】
    棘轮锁定世代最优(只进不退)                                 【CodeBuddy ratchet_ledger】
```

**关键原则（用户设计 §"实现建议"）**：不写"Agent 应该如何协作"的规则，只构建代谢红线 + 受限感知 + 生存时长繁衍 + 动态捕食压力的闭环，让协作**被迫涌现**。

---

## 5. 分阶段路线

| 阶段 | 主题 | 关键交付 | 归属 |
|---|---|---|---|
| **ND-1** | 模式判定 + AgentProfile.runtime 落地 | team/agent 配置 `runtime` 字段 + 演练读取 | 【待做，Claude】 |
| **ND-2** | eco_drill 生境内核 | `sandbox/eco_drill.py`：Health 代谢在环的 step/epoch 循环 | 【待做，Claude】 |
| **ND-3** | Skill 交叉遗传（复合 Skill） | `team_manager.mate` 升级为双亲 skill 交叉+变异 | 【待做，Claude】 |
| **ND-4** | 生存时长适应度 + 基因抹除 | survival_ticks 作选择键；死亡个体基因不入池 | 【待做，Claude】 |
| **ND-5** | 前端双形态：eco 模式生境 3D + 右侧生境控制台 | `Agent-digital-twin.html` 按 mode 切换 | 【待做，Claude】 |
| **ND-6** | 复用既有零件接线（不回归 legacy） | 接 twin_loop 分派 / ratchet / skill_library / eco_runtime_config | 【CodeBuddy→Claude】 |

---

## 6. 验证标准

| 阶段 | 验收 |
|---|---|
| ND-1 | eco 团队进演练页走新生境；legacy 团队行为零回归（现有 twin 测试全过） |
| ND-2 | 一场生境演练里低能效 skill 组合的 Agent 先饿死（Health→0），可观测 survival_ticks 差异 |
| ND-3 | 两个高存活 Agent 交配产出的后代 skill_genome = 双亲交叉，可追谱系 |
| ND-4 | 死亡个体 skill 不进入下一代基因池；生存时长排序驱动繁衍 |
| ND-5 | eco 模式页面左 3D 显血条/生存时长、右菜单为生境控制台；legacy 模式保持原 SECS 面板 |
| ND-6 | `pytest` 新增 eco_drill 测试全绿；既有 sandbox/twin 测试无回归 |

---

## 7. 设计原则

1. **不回归 legacy**：CodeBuddy 的 SECS 演练是默认路径，eco 生境是并行新增，按 `runtime` 切换。
2. **复用优先**：Health/eco_loop/mate/选择状态机（Claude 已做）+ twin_loop/ratchet/skill_evolver（CodeBuddy 已做）都复用，eco_drill 只做编排。
3. **生存时长是唯一适应度**：不新增人工评分公式（这正是 v2 "死亡规则优先于评分函数"原则的延伸）。
4. **繁衍=Skill 交叉遗传**：mate 产出复合 Skill，不是简单复制。
5. **协作靠涌现**：只给约束（代谢/感知/捕食压力），不写协作规则。

---

*配套执行清单见：[`物竞天择数字孪生演练todos.md`](物竞天择数字孪生演练todos.md)*
