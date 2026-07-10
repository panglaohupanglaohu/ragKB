<!-- docs-signoff: author="Kiro" kind="llm" doc="todos" ts="2026-07-09T00:00:00Z" -->
# Agent 生态仿生进化 Todos — Perception / Intention / Behavior + 物竞天择

> 配套 [Agent生态仿生进化plan.md](Agent生态仿生进化plan.md)。
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> **风险分级**：🟢 低危（本地新增/纯函数） · 🟡 中危（接线既有系统） · 🔴 高危（改选择/状态，需人工门禁）。
> **总原则**：最大化复用现有地基（见 plan §0），新代码集中在 `src/backend/agents/bionic/`；选择循环默认手动、产物为草稿、休眠可逆。

---

## Phase 0: 地基核对（已存在，本次不重写）

- [x] **BE-0a** 事件总线 `event_bus.py` + `domain_events.py`（感知输入）✅ 已有
- [x] **BE-0b** 任务引擎 `task_engine.py`（work 行为 + 任务压力信号）✅ 已有
- [x] **BE-0c** 议事/协作 `plaza_engine.py` + `agent_relationships.py`（collaborate 行为 + 协作性状）✅ 已有
- [x] **BE-0d** 适应度/变异/棘轮 `evolution/fitness.py`·`optimizer.py`·`skill_evolver.py`·`ratchet_ledger.py`（物竞天择三件套）✅ 已有
- [x] **BE-0e** 效果反馈 `skill_tracker.py`（选择压力度量）✅ 已有
- [x] **BE-0f** 个体/团队/繁殖 `models.py`·`team_manager.py`（含 `duplicate_agent`）✅ 已有

---

## Phase A: 配置 Schema（生物档案，向后兼容）  🟢

- [ ] **BA-1** `AgentProfile` 增可选 `bio` 支持
  文件：[src/backend/agents/models.py](../src/backend/agents/models.py)
  落点：不改动现有字段；在 `to_dict()` 中若 `metadata.get("bio")` 存在则透出。定义模块级 `_AGENT_BIO_DEFAULTS`（archetype/perception/mental_state/intention/selection，见 plan §6）。
  验收：`python -m py_compile src/backend/agents/models.py`；无 `bio` 的 agent `to_dict()` 输出与之前逐字段一致（快照测试）。

- [ ] **BA-2** 生物档案深度合并 + 校验工具
  文件：新增 [src/backend/agents/bionic/__init__.py](../src/backend/agents/bionic/__init__.py) + [src/backend/agents/bionic/bio_config.py](../src/backend/agents/bionic/bio_config.py)
  落点：`merge_bio_defaults(profile_dict)` —— 对 `bio` 各块 `{**default, **user}`（用户值覆盖，参照 `pet_ecosystem.py::get_config`）；`bio.enabled` 默认 `False`。
  验收：`pytest`：无 `bio` → 补全后 `enabled==False`；显式 `enabled=true` + 部分字段 → 缺省字段被正确补全。

---

## Phase B: 生物行为内核（意图生成器，纯逻辑）  🟢

> 文件：新增 [src/backend/agents/bionic/agent_behavior.py](../src/backend/agents/bionic/agent_behavior.py)
> 对齐 `pet-behavior.js`：把"感知→心理状态→意图→分派"拆成可单测的纯函数 + 一个 `AgentBehavior` 控制器。
> **本 Phase 不真正执行任务**，只产出「意图 + 目标」，执行留给 Phase C 分派。

- [ ] **BB-1** 心理状态纯函数（4 个驱动，plan §2）
  落点：`compute_task_pressure(backlog, full, deadline_urgency)`、`compute_stress(fail_rate, missing_skill_ratio, blocked)`、`compute_idle_drive(idle_sec, full_sec)`、`compute_budget_pressure(used, budget)`，均返回 [0,1]。
  验收：`pytest`：backlog=0→0、backlog=full→1；budget=0→恒 0；idle=full_sec→1。

- [ ] **BB-2** 感知快照 `WorldView`（数据结构，无 I/O）
  落点：`@dataclass WorldView`（自己的 pending/running 任务、近期成功/失败计数、peers 摘要、token 用量、未分配任务列表）。Phase C 负责填充，本 Phase 只定义 + 用假数据测。
  验收：`pytest`：从假 dict 构造 `WorldView` 字段正确。

- [ ] **BB-3** 意图生成器（优先级 + 单项记忆防抖 + 持久化阈值，plan §3）
  落点：`generate_intention(state, world, bio)`，优先级 `avoid > collaborate > work > forage > rest`；`avoid` 打断压栈 `state.memory`，解除弹栈恢复；`work` 目标用 `task_cost(task, current_target, beta)` 选最小代价 + 持久化阈值。
  验收：`pytest`：①各驱动超阈触发对应意图；②`avoid` 打断 `work`、解除后恢复 `work`（不掉回 `rest`）；③目标切换需超阈值（fickle/devoted）。

- [ ] **BB-4** `AgentBehavior` 控制器 + tick 骨架
  落点：`class AgentBehavior` 持 `state`（intention/memory/target/驱动值/last_*）；`tick(world) -> BehaviorDecision{intention, target_id, params}`（只决策不执行）。
  验收：`pytest`：喂一串 `WorldView` 序列，`tick` 产出的 decision 序列符合预期（含防抖）。

- [ ] **BB-5** 内核自检（对齐宠物 `__checks__` 风格）
  落点：单测集中在 [tests/](../tests/) 下 `test_bionic_behavior.py`（或就地 pytest），覆盖 BB-1/3/4 全部公式与状态机。
  验收：`pytest tests/test_bionic_behavior.py -q` 全绿。

---

## Phase C: 生态运行时（环境 tick，接线既有系统）  🟡

> 文件：新增 [src/backend/agents/bionic/ecosystem.py](../src/backend/agents/bionic/ecosystem.py)，类比 `pet-ecosystem.js`。

- [ ] **BC-1** `AgentEcosystem` 管理器骨架（单例 + 生命周期）
  落点：`class AgentEcosystem`：`register_team(team_id)` 收集 `bio.enabled` 的 agents；`start()/stop()`；`snapshot()` 返回各 agent 驱动/意图/fitness 摘要。单例 `get_agent_ecosystem()`。
  验收：`python -m py_compile`；注册一个含 1 个 bio agent 的 mock team，`snapshot()` 返回该 agent 条目。

- [ ] **BC-2** 感知装配：从 EventBus + task_engine 填充 `WorldView`  🟡
  落点：订阅 `EventType.TASK_*`/`AGENT_STATE_CHANGED`（`event_bus.subscribe`）维护近期成功/失败窗口；`_build_world_view(agent)` 查 `task_engine.get_agent_tasks` + 未分配 PENDING + peers（`team_manager`/`agent_relationships`）。
  验收：`pytest`（mock task_engine/bus）：注入 2 个 PENDING 任务 + 1 个近期 FAILED 事件 → `WorldView.backlog==2`、`fail count==1`。

- [ ] **BC-3** 意图分派到现有能力（行为层，plan §4）  🟡
  落点：`_dispatch(agent, decision)`：
  - `work` → 构造/挑选 `AgentTask` 提交 `task_engine`（可用 metadata 标 `_engine_auto_execute=False` 走人工/受控）；
  - `collaborate` → 调 `plaza_engine` 开讨论 或 `task_engine` 委派子任务；
  - `forage` → 认领未分配 PENDING 任务 或 调 `skill_evolver.suggest_evolution`（不自动 apply）；
  - `avoid` → 切 `fallback_model_id` / 延后任务 / 发上报事件；
  - `rest` → no-op。
  验收：`pytest`（mock 各引擎）：每种意图调用对应引擎一次、参数正确；`work` 提交的任务默认**不自动执行**。

- [ ] **BC-4** tick 驱动（默认手动/事件驱动，不自动烧 token）  🟡
  落点：`tick_once()` 遍历注册 agents：`_build_world_view → behavior.tick → _dispatch`；提供 `tick_agent(agent_id)`。**不加自动定时器**（留给 Phase E API/开关）。
  验收：`pytest`：一个 bio agent + 注入 PENDING → `tick_once()` 后进入 `work` 且调用了 task_engine 提交（mock）。

---

## Phase D: 物竞天择（世代选择循环）  🔴 需人工门禁

> 文件：新增 [src/backend/agents/bionic/selection.py](../src/backend/agents/bionic/selection.py)。
> **硬约束**：全部产物为草稿；休眠=`state=STOPPED`（可逆，**不删除**）；采纳/休眠需人工确认；变异走既有 4 门 + 棘轮。

- [ ] **BD-1** 个体适应度聚合 `aggregate_agent_fitness`（plan §5.2）  🟡
  落点：加权合并——任务成功率（task evidence）+ 所拥有技能平均 effectiveness（`skill_tracker`/`skill_library`）+ 协作边权（`agent_relationships`）+ 成本效率（token 利用率）。返回 `{agent_id, fitness, breakdown}`。
  验收：`pytest`（mock 各来源）：给定信号 → fitness 落 [0,1] 且 breakdown 各分量正确；缺失来源有安全默认。

- [ ] **BD-2** 种群排序 + 选择计划（只读，不改状态）  🟢
  落点：`plan_epoch(team_id)` → `{ranking, reproduce:[top_k], dormant:[bottom_k], gene_flow:[skill→adopter]}`。纯计算，产出**计划**不执行。
  验收：`pytest`：4 个 agent 不同 fitness → ranking/繁殖/休眠名单符合 `bio.selection` 配置（默认 dormant_bottom_k=0 → 空）。

- [ ] **BD-3** 繁殖（遗传+变异，产草稿）  🔴
  落点：`reproduce(team_id, agent_id)` → `team_manager.duplicate_agent`（已有）+ 继承最优技能（记 `lineage`）+ 对 1 个技能调 `optimizer.optimize_skill` 产**变异草稿**。**不直接落库到生产**，返回待审草稿包。
  验收：`pytest`（mock optimizer/team_manager）：产出草稿含新 agent 副本 + 1 个 version+1 的技能草稿；生产团队状态未变。

- [ ] **BD-4** 选择四门 + 棘轮锁定（复用既有）  🔴
  落点：`gate_candidate(draft)` 串 `constraints.validate_all` → fitness on holdout（`evolution/fitness`）→ 棘轮 `run_full_audit` → CII 保持；全过则可提交 `ratchet_ledger` 锁定（**仍需人工批准后**）。
  验收：`pytest`（mock 门禁）：任一门失败 → 草稿标 rejected + 原因；全过 → 标 `verify_pending` 待人工。

- [ ] **BD-5** 休眠（可逆）+ 基因流  🔴
  落点：`retire(agent_id)` → `state=STOPPED`（经 team_manager，可 `revive`）；`gene_flow` → 把休眠者最优技能 `adopted_by` 更适者（技能不随个体消失）。**不删除**。
  验收：`pytest`：`retire` 后 agent 仍存在且 `state==stopped`、可 `revive`；技能 `adopted_by` 追加了采纳者。

- [ ] **BD-6** `run_epoch` 编排（默认 dry-run）  🔴
  落点：`run_epoch(team_id, apply=False)`：`plan_epoch → reproduce(草稿) → gate → 汇总报告`；`apply=False` 时**只报告不改状态**（休眠/采纳/锁定均需显式 `apply=True` + 人工）。
  验收：`pytest`：`apply=False` 跑完输出完整报告、零状态变更；`apply=True`（mock 审批）才触发 retire/lock。

---

## Phase E: API + 前端可视化  🟡（含 🔴 审批端点）

- [ ] **BE-1** 生态 REST 端点
  文件：[src/backend/agent_team_api.py](../src/backend/agent_team_api.py) 或新增 [src/backend/agents/bionic_routes.py](../src/backend/agents/bionic_routes.py) + `main.py` 挂载
  落点：`GET /bionic/{team}/snapshot`（驱动/意图/fitness）、`POST /bionic/{team}/tick`、`POST /bionic/{team}/epoch?apply=false`、`GET /bionic/{team}/ranking`、`POST /bionic/{team}/candidate/{id}/approve` 🔴（走既有审批/CSRF）。
  验收：`pytest`（TestClient）：snapshot/ranking 200；`epoch?apply=false` 返回报告；approve 需鉴权。

- [ ] **BE-2** 前端"🧬 生态进化"面板
  文件：[src/frontend/system-evolution.html](../src/frontend/system-evolution.html)（新面板）
  落点：展示各 agent 的 4 个驱动条 + 当前意图 + fitness 排名；"手动 tick / dry-run epoch / 审核繁殖草稿 diff（复用 EVOLUTION_PLAN 的 diff 审核 UI）"。
  验收：`npm run build` 通过；面板加载 snapshot、跑 dry-run epoch 显示排名与草稿 diff。

- [ ] **BE-3**（可选）办公室 3D 生物姿态可视化
  文件：办公室场景（复用 `pet-*` 思路）
  落点：把启用 bio 的 Agent 以生物姿态在场景中表达心理状态/意图（如高压快走、阻塞求助光圈、觅食游走）。**纯可视化，不改逻辑。**
  验收：office3d 手动演练，姿态随 snapshot 变化，无回归。

---

## 执行顺序与门禁

**推荐路径**：先让"单个 Agent 作为生物活起来"（低风险、可观测），再上种群选择：
```
Phase A（Schema）→ Phase B（意图内核，纯逻辑）→ Phase C（生态 tick 接线）
   ↓ 验证：单 agent 能感知→生成意图→分派到既有引擎
Phase D（物竞天择，默认 dry-run + 人工门禁）→ Phase E（API/可视化）
```

**每阶段收口**：跑 `node scripts/check-docs-signoff.cjs --strict` + 相关 `pytest` / `py_compile` / `npm run build`。

**先决问题（进 Phase B 前请拍板，见 plan §9）**：
1. tick 频率：实时 vs 事件驱动？（默认事件驱动 + 手动 epoch）
2. "繁殖"= 新增 agent 还是只产技能变异草稿？（默认后者，种群规模稳定）
3. 是否引入"团队 token 预算封顶"作为硬选择压力？（建议 Phase D+ 再评估）

---

## 与其他 plan 的接线（不重复造轮子）

- **变异/评分/锁定** 全部调用 `docs/EVOLUTION_PLAN.md` 的现成管线（`evolution/*` + 棘轮）。
- **本模块是"种群选择框架"**，EVOLUTION_PLAN 是"基因变异引擎"，宠物 plan 是"P/I/B 内核原型 + 可视化皮肤"。三者互补。

---

## 附：可配置参数中心（2026-07-10 已落地）

本 todos 涉及的可调参数已统一为可配置数据源 + 仿生生态页面独立 Tab（与小虎/吱吱区分）。详见 [`Agent仿生生态运行时todos.md`](Agent仿生生态运行时todos.md) Phase 6「可配置参数中心」。

- [x] 后端配置单一数据源 + REST（`eco_runtime_config.py` / `eco_runtime_routes.py`，`/api/v1/eco-runtime/*`）
- [x] 各模块从配置读取（硬编码退为兜底）
- [x] 前端 Tab「🧬 仿生生态运行时参数」（`pet-config.html`）
- [x] 测试 `test_eco_runtime_config.py` 10 passed
