<!-- docs-signoff: author="CodeBuddy" kind="llm" doc="todos" ts="2026-07-10T14:55:00Z" -->
# 物竞天择数字孪生演练 Todos — 自然选择生境

> 配套 [`物竞天择数字孪生演练plan.md`](物竞天择数字孪生演练plan.md)。
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> **作者标注**：【CodeBuddy】既有 · 【Claude】本轮已做 · 【待做】本清单待实现（默认由 Claude 续做）。

---

## 依赖盘点：已就绪的零件（不重造，直接接）

| 零件 | 归属 | 用途 |
|---|---|---|
| `eco_loop.py`（WorldView/MentalState/H·F·L/generate_intention） | 【Claude】 | 生境每步的感知→意图仲裁 |
| `health_ledger.py`（HealthLedger.tick/revive/survival_ticks/net_gain_by_skill） | 【Claude】 | 代谢红线 + 生存时长适应度 |
| `team_manager.can_mate/mate`（Health 门禁 + 复制+lineage） | 【Claude】 | 繁衍门禁（待升级为 skill 交叉） |
| `skill_library.evaluate_selection_state/apply_selection_state` | 【Claude】 | dominant/deprecated 基因池迁移 |
| `eco_runtime_config.py` + `/api/v1/eco-runtime/*` | 【Claude】 | 生境参数（代谢/学习/选择/交配）单一数据源 |
| `twin_loop.py::_run_evolutionary`（多代 top50%+变异+棘轮） | 【CodeBuddy】 | 演化循环骨架 |
| `twin_loop.py::_settle_skill_action`（熟练度→成功率） | 【CodeBuddy】 | 动作代谢成本来源 |
| `twin_loop.py::inject_chaos_event`（捕食压力/扰动） | 【CodeBuddy】 | 动态博弈/军备竞赛压力 |
| `trial_api.py`（Trial/Branch/Session + SSE） | 【CodeBuddy】 | 演练会话管理 + 前端事件流 |
| `ratchet_ledger.py`（只进不退） | 【CodeBuddy】 | 世代最优锁定 |

---

## ND-1: 演练模式判定 + AgentProfile.runtime 落地  【CodeBuddy ✅ 完成】

- [x] **ND-1.1** `AgentProfile`/`AgentTeam` 增 `runtime: "eco" | "legacy"` 字段（默认 legacy）
  文件：`src/backend/agents/models.py`【CodeBuddy 既有文件 → Claude 扩展】、`team_store.py`（序列化，向后兼容缺字段）
  验收：旧数据反序列化默认 legacy；`pytest` 快照测试无回归。

- [x] **ND-1.2** 演练创建时读取团队 runtime，路由到对应引擎
  文件：`src/backend/sandbox/trial_api.py`【CodeBuddy → Claude 加分支】
  落点：`create_trial` 判定 team.runtime；eco → 走 ND-2 的 eco_drill，legacy → 现有 SECS（不动）。
  验收：eco 团队创建 trial 标记 `drill_kind="natural_selection"`；legacy 标记 `secs`。

---

## ND-2: eco_drill 生境内核  【CodeBuddy ✅ 完成】

- [x] **ND-2.1** 新建 `sandbox/eco_drill.py`：Health 代谢在环的 step 循环
  落点：每 step 对存活种群 `perceive(eco_loop) → generate_intention → 分派动作(复用 twin_loop 决策) → 结算 cost/reward → HealthLedger.tick`。死亡（health≤0）退出种群。
  依赖：【Claude】eco_loop/health_ledger + 【CodeBuddy】twin_loop 动作分派/`_settle_skill_action`。
  验收：`pytest tests/test_eco_drill.py`：低能效组合的 twin 先饿死；survival_ticks 有差异。

- [x] **ND-2.2** epoch（世代）循环：生存时长排序 → 繁衍 → 变异 → 棘轮锁定
  落点：复用【CodeBuddy】`_run_evolutionary` 的多代骨架，但选择键换成【Claude】`survival_ticks`（不是 reward）。
  验收：多代演化后种群平均生存时长单调不降（棘轮），可观测代际曲线数据。

- [x] **ND-2.3** 捕食压力/军备竞赛接线
  落点：复用【CodeBuddy】`inject_chaos_event` + `pet_ecosystem` chase/flee 语义，作为生境的动态选择压力。
  验收：注入捕食压力后，未适应的 skill 组合生存时长显著下降。

---

## ND-3: Skill 交叉遗传（复合型 Skill）  【CodeBuddy ✅ 完成】

- [x] **ND-3.1** `team_manager.mate` 升级：双亲 skill_genome 选择与交叉
  文件：`src/backend/agents/team_manager.py`【Claude 本轮已建 mate → 本任务升级】
  落点：当前 mate 只复制单亲；改为取双亲 skill 并集/交叉子集，`metadata.lineage` 记双亲 + generation。
  验收：`pytest tests/test_mating.py` 扩展：后代 genome = 双亲交叉；谱系可追双亲。

- [x] **ND-3.2** （可选）交叉后调 skill_evolver 提炼复合 Skill
  文件：复用【CodeBuddy】`skill_evolver.evolve_skill`（只在 apply 时，避免烧 token）
  验收：产出为草稿，经门禁+人工确认才入库（沿用可逆原则）。

---

## ND-4: 生存时长适应度 + 基因抹除  【CodeBuddy ✅ 完成】

- [x] **ND-4.1** survival_ticks 作为唯一选择键接入 epoch 排序
  验收：不引入新的人工评分；排序/繁衍/淘汰全部由 survival_ticks 驱动。

- [x] **ND-4.2** 基因抹除：死亡个体 skill 不进入下一代基因池
  落点：eco_drill 内种群级淘汰用"移除出本场种群"（演练内），全局仍走【Claude】dormant（可逆，不删 AgentProfile）。
  验收：死亡个体的 skill_genome 不参与 ND-3 交叉；可观测基因池收敛。

---

## ND-5: 前端双形态页面（3D + 右侧菜单随模式切换）  【CodeBuddy ✅ 完成】

- [x] **ND-5.1** 演练页按 team.runtime 切换右侧面板
  文件：`src/frontend/Agent-digital-twin.html`【CodeBuddy 既有 → Claude 加 eco 分支】
  落点：eco 模式隐藏 SECS Pipeline 面板，显示「生境控制台」：代谢参数（读 `/api/v1/eco-runtime/config`）+ 世代循环按钮 + 种群面板（存活数/世代/生存时长分布）+ 基因池（dominant/deprecated）+ 繁衍谱系。
  验收：eco 团队进页面 → 右侧为生境控制台；legacy → 原 SECS 面板（零回归）。

- [x] **ND-5.2** 左侧 3D 生境视图：血条/饥饿/生存时长 + 捕食连线 + 死亡淡出
  文件：`src/frontend/js/office/*`【CodeBuddy 既有 → Claude 加 eco 渲染】
  落点：eco 模式下 Agent 头顶显示 Health 血条与生存时长；捕食/竞争关系连线；health=0 变灰淡出。
  验收：一场 eco 演练可视化看到个体饿死/繁衍。

---

## ND-6: 接线与回归  【CodeBuddy ✅ 完成】

- [x] **ND-6.1** eco_drill 接 ratchet_ledger 锁世代最优
  验收：世代最优生存时长写入棘轮，只进不退。

- [x] **ND-6.2** 全量回归：legacy SECS 演练零改变
  验收：`pytest src/backend/tests/ -q` 既有 sandbox/twin/trial 测试全过；新增 eco_drill 测试全绿。

---

## 执行顺序

```
ND-1（模式判定）→ ND-2（生境内核）→ [ND-3（交叉遗传）∥ ND-4（生存适应度/抹除）] → ND-5（前端双形态）→ ND-6（接线回归）
```

---

## 归属总览（一览表）

| 模块/文件 | 归属 |
|---|---|
| eco_loop.py / health_ledger.py / eco_runtime_config.py / eco_runtime_routes.py | 【Claude】本轮已做 |
| team_manager.can_mate/mate / skill_library 选择状态机 / pet-config Tab2 | 【Claude】本轮已做 |
| start.sh .env 加载 / agent-team-config.js 记住密钥接线 | 【Claude】本轮已做 |
| twin_loop.py（含 _run_evolutionary/_settle_skill_action/chaos） | 【CodeBuddy】既有 |
| trial_api.py / sandbox/models.py / ratchet_ledger.py / skill_evolver.py | 【CodeBuddy】既有 |
| Agent-digital-twin.html SECS 面板 / office 3D | 【CodeBuddy】既有 |
| eco_drill.py / mate 交叉遗传 / 前端双形态 / runtime 字段 | 【CodeBuddy ✅ 完成】 |
