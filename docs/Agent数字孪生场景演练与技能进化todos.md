# Agent 数字孪生 v4 — 场景化演练 × 技能进化 TODOS（代码对齐版）

> 版本：v4.0 · 日期：2026-06-12
> 配套文档：`Agent数字孪生场景演练与技能进化plan.md`
> 状态标记：`[ ]` 未开始 / `[~]` 主通路完成但有缺陷 / `[x]` 通过四门验收
> **四门验收规则沿用 v3.1**：①函数存在门（grep 可查到定义） ②接口通路门（请求 2xx） ③状态一致门（关键字段按预期变化） ④手工 UI 门（界面可见正确结果）。后端纯逻辑项以 pytest 通过替代 ④。

---

## A. 数据结构（M1/M2 基础，全部新增于 `src/backend/sandbox/` 除特别注明）

### A-1 ScenarioSpec 场景模型 — 新文件 `sandbox/scenario_models.py`

- [x] **A-1.1** `@dataclass ScenarioSpec` 字段级定义：　⟦scenario_models.py:ScenarioSpec；test_scenario_system 全绿⟧
  ```python
  scenario_id: str            # "cs_ticket_surge" 等，slug 格式
  name: str                   # "客服工单高峰"
  category: str               # customer_service | data_pipeline | marketing | code_delivery | incident
  description: str
  version: int = 1
  # 五要素
  world: ScenarioWorld        # 见 A-1.2
  taskflow: List[ScenarioTask]  # 见 A-1.3
  roles: List[RoleRequirement]  # 见 A-1.4
  chaos_script: List[ChaosPhase]  # 见 A-1.5
  rubric: ScenarioRubric      # 见 A-1.6
  # 元数据
  tags: List[str]
  difficulty: int = 1         # 1-5
  recommended_max_steps: int = 150
  created_at: str / updated_at: str
  source: str = "builtin"     # builtin | custom | llm_generated
  ```
- [x] **A-1.2** `ScenarioWorld`：`rooms: List[RoomSpec]`（room_id/name/icon/capacity/stage 序号——房间即业务阶段状态机）、`resources: List[Dict]`（对齐 `world_state.sync_resources` 入参）、`constraints: List[Dict]`（对齐 `EnvironmentConstraint`）、`global_metrics_init: Dict[str, float]`。　⟦ScenarioWorld/RoomSpec⟧
- [x] **A-1.3** `ScenarioTask`：`task_id/name/room_id/required_skills: List[str]/depends_on: List[task_id]/base_duration_steps: int/reward: float/failure_penalty: float/optional: bool`。形成 DAG，由 compiler 校验无环。　⟦ScenarioTask + DAG 校验⟧
- [x] **A-1.4** `RoleRequirement`：`role/min_count/required_skills/preferred_skills`。用于真实团队匹配度计算（前端显示"角色匹配度 80%，缺 skill X"）。　⟦RoleRequirement + match_team⟧
- [x] **A-1.5** `ChaosPhase`：`from_step/to_step/events: List[{event_type, probability_per_step, payload}]`。event_type 复用 trial_api 既有枚举（network_delay/agent_leave/task_change/skill_degraded/model_hallucination/logic_deadlock）。　⟦ChaosPhase⟧
- [x] **A-1.6** `ScenarioRubric`：`kpi_targets: Dict[str, float]`（如 completion_rate≥0.9）、`dimension_weights: Dict[str, float]`（覆写五维评分权重）、`skill_expectations: Dict[skill_name, float]`（期望成功率，进化触发阈值的依据）。　⟦ScenarioRubric⟧
- [x] **A-1.7** 全部 dataclass 提供 `to_dict()/from_dict()`，风格对齐 `sandbox/models.py` 现有写法。　⟦to_dict/from_dict 往返测试通过⟧

### A-2 技能使用与熟练度模型 — 追加到 `sandbox/models.py`

- [x] **A-2.1** `@dataclass SkillUsageRecord`：　⟦models.py:SkillUsageRecord⟧
  ```python
  record_id / session_id / branch_id / trial_id
  step_index: int
  agent_id: str / agent_role: str
  skill_name: str / skill_id: Optional[str] / skill_version: Optional[int]
  task_id: str
  outcome: str          # success | failure | partial
  duration_steps: int
  reward_delta: float   # 该次使用对 global_reward 的贡献
  failure_reason: str   # 失败时由决策/judge 填写
  context: Dict         # 房间、当时混沌事件、协作者
  ```
- [x] **A-2.2** `@dataclass SkillProficiency`（聚合视图，可即时计算也可缓存）：`skill_name/agent_id/scenario_category/total_uses/success_count/success_rate/avg_reward_delta/trend: List[float]`（最近 10 个 trial 的成功率序列）`/last_updated`。　⟦models.py:SkillProficiency⟧
- [x] **A-2.3** `AgentTwin` 增加字段 `skill_proficiency: Dict[str, float]`（skill_name→成功率先验，spawn 时从存储载入，默认 0.5）。　⟦AgentTwin.skill_proficiency；spawn 载入测试通过⟧
- [x] **A-2.4** `SimulationStep` 增加 `skill_usages: List[str]`（record_id 引用，避免嵌套膨胀）。　⟦SimulationStep.skill_usages⟧
- [x] **A-2.5** `TrialEvaluation` 增加 `skill_breakdown: List[Dict]`（结构对齐 `evolution/fitness.SkillFitnessReport.to_dict()`）。　⟦TrialEvaluation.skill_breakdown⟧
- [x] **A-2.6** `Trial` 增加 `scenario_id: str = ""`、`generation: int = 0`、`parent_trial_id: str = ""`（保留旧 `scenario: str` 字段不删，兼容存量 JSON）。　⟦Trial.scenario_id/generation/parent_trial_id；旧 scenario 字段保留⟧

### A-3 进化运行模型 — 追加到 `sandbox/models.py`

- [x] **A-3.1** `@dataclass EvolutionRun`：　⟦models.py:EvolutionRun + EvolutionRunStatus⟧
  ```python
  run_id / team_id / scenario_id
  target_skills: List[{skill_id, skill_name, reason, baseline_success_rate}]
  status: str   # identifying|reflecting|mutating|ab_testing|gating|applied|rejected|failed
  reflection: Dict          # mutator.reflect_on_failures 输出
  candidates: List[Dict]    # 每个含 strategy/instructions/branch_id/fitness/five_dim_score
  winner: Optional[Dict]    # 胜出候选 + gate 结果 + new_version
  baseline_trial_id: str / ab_trial_ids: List[str]
  triggered_by: str         # manual | auto_low_score | nightly
  created_at / completed_at
  cost_tokens: int          # LLM 成本累计，供 cost_gate
  ```
- [x] **A-3.2** `TrialEventType` 枚举新增：`EVOLUTION_STARTED / EVOLUTION_PHASE / EVOLUTION_APPLIED / EVOLUTION_REJECTED / SKILL_USAGE`（SSE 推送用）。　⟦TrialEventType 新增 6 个事件⟧

### A-4 持久化

- [x] **A-4.1** 新文件 `sandbox/scenario_store.py`：仿照 `trial_store.py` 结构。内置场景从 `config/scenarios/*.json` 加载（只读），自定义场景写 `storage/scenarios/{scenario_id}.json`。提供 `list/get/save/delete(仅 custom)`，启动时校验 schema。　⟦scenario_store.py；builtin 只读/custom 可写测试通过⟧
- [x] **A-4.2** 5 个种子场景 JSON 落地 `config/scenarios/`：`cs_ticket_surge.json`（客服工单高峰）、`data_pipeline_recovery.json`（数据管道故障恢复）、`marketing_campaign.json`（营销活动投放）、`code_review_delivery.json`（代码评审交付）、`capacity_incident.json`（容量事故演练）。每个含 ≥4 房间、≥6 任务节点、≥2 个混沌阶段、完整 rubric。　⟦config/scenarios/ 5 个种子全部 compile 通过（≥4房间/≥6任务/≥2混沌阶段/完整rubric）⟧
- [x] **A-4.3** `trial_store.py` 扩展：SkillUsageRecord 按 trial 追加写 `storage/twin_trials/{trial_id}_skill_usage.jsonl`（对齐既有 `_events.jsonl` 模式）；EvolutionRun 写 `storage/evolution_runs/`（目录已存在，复用）。　⟦proficiency_store.append_usages → {trial}_skill_usage.jsonl；EvolutionRun → storage/evolution_runs/⟧
- [x] **A-4.4** SkillProficiency 缓存写 `storage/skill_proficiency/{team_id}.json`，trial 完成时增量更新；提供 rebuild 函数（全量扫 usage jsonl 重算），供数据修复。　⟦update_from_trial 增量更新 + rebuild 全量重建，测试通过⟧
- [x] **A-4.5** 存量兼容迁移：trial_store 加载旧 Trial JSON 时缺失新字段给默认值（generation=0, scenario_id="legacy"）；写一个幂等迁移脚本 `src/backend/scripts/migrate_trials_v4.py`，pytest 验证旧文件可读。　⟦scripts/migrate_trials_v4.py 实跑：10 条迁移成功且幂等（二次运行 migrated=0）⟧

---

## B. 后端 API（M1/M3）

### B-1 场景 API — 新文件 `sandbox/scenario_api.py`，router prefix `/api/v1/scenarios`

- [~] **B-1.1** `GET /api/v1/scenarios?category=&tag=` — 列表（含每场景历史最佳分：联查 trial_store 同 scenario_id 最高 total_score）。　⟦代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-1.2** `GET /api/v1/scenarios/{id}` — 详情（完整 spec）。　⟦代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-1.3** `POST /api/v1/scenarios` — 上传自定义场景 JSON，schema 校验失败返回 422 + 字段级错误。　⟦422+字段级错误已实现；代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-1.4** `POST /api/v1/scenarios/generate` — body `{description, team_id}`，调 compiler 的 LLM 生成（见 C-1.4），返回草稿 spec（source=llm_generated，需用户确认后 POST 保存）。　⟦接口完成；LLM 生成通路需真实 chat_harness 联测⟧
- [~] **B-1.5** `GET /api/v1/scenarios/{id}/match?team_id=` — 角色匹配度：拉 teams-tree 团队成员 skills 与 `roles` 要求比对，返回 `{match_rate, missing_skills, role_coverage}`。　⟦match_team 纯逻辑已测；接口层待本机验证⟧
- [x] **B-1.6** 在 `main.py` 注册 router（对齐既有 trial_api 注册方式）。　⟦main.py 5.6/5.7 注册 + 豁免前缀，grep 可验证⟧

### B-2 试炼 API 扩展 — 改 `sandbox/trial_api.py`

- [~] **B-2.1** `CreateTrialRequest` 增加 `scenario_id: str = ""`、`generation: int = 0`、`parent_trial_id: str = ""`；创建逻辑：有 scenario_id 时调 ScenarioCompiler 实例化世界（见 C-1），覆盖默认 world/任务。　⟦场景编译注入世界+混沌时间表+熟练度先验；代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-2.2** `GET /twin-trials/{id}/skill-stats` — 返回该 trial 聚合后的 per-skill 统计（usage 数、成功率、reward 贡献、对比 rubric.skill_expectations 的达标状态）。　⟦/skill-stats 实现；代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-2.3** `POST /twin-trials/{id}/evaluate` 扩展：计算并写入 `skill_breakdown`（A-2.5）；五维权重读 scenario rubric 的 `dimension_weights`（无场景时用现有默认）。　⟦rubric 权重覆写+skill_breakdown 实现；代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-2.4** `POST /twin-trials/{id}/feedback` **去模拟化**（核心）：　⟦去模拟化完成：create_version_snapshot+effectiveness+evidence_sessions 真实写回，含 reversible/rollback_hint；接口门待本机⟧
  - 删除"(模拟)"路径；改为：对 `updated_skills` 中每个 skill，调 `skill_library.create_version_snapshot`（变更原因="trial_feedback:{trial_id}"）+ 更新 skill metadata（`proficiency_hint`、`last_trial_score`）；
  - SOP 应用走 `skill_registry`/team 协作图真实写入（具体落点：`team_store` 协作边权重字段，如无则在 metadata 记录）；
  - 返回中增加 `skill_versions_created: List`、`reversible: true` 与回滚指引；
  - 失败任一步回滚已建快照，保证原子性。
- [~] **B-2.5** `GET /twin-trials?scenario_id=&generation=` — 列表过滤参数，供代际对比图取数。　⟦scenario_id/generation 过滤实现；代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧

### B-3 进化 API — 新文件 `sandbox/evolution_api.py`，prefix `/api/v1/twin-evolution`

- [~] **B-3.1** `POST /api/v1/twin-evolution/runs` — body `{team_id, scenario_id, skill_ids?: [], baseline_trial_id?: str, auto_apply: false}`。skill_ids 为空时自动识别弱 skill（C-3.1）。返回 run_id，后台 asyncio 任务执行（对齐 trial 的运行模式）。　⟦后台任务+弱skill自动识别实现；代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-3.2** `GET /runs/{run_id}` — 状态 + 各阶段产物。　⟦代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-3.3** `GET /runs?team_id=&scenario_id=` — 历史列表。　⟦代码+pytest 完成(test_v4_apis.py)；沙箱无 fastapi，接口通路门需本机 `pytest tests/test_v4_apis.py` 验证⟧
- [~] **B-3.4** `POST /runs/{run_id}/approve` / `POST /runs/{run_id}/reject` — `auto_apply=false` 时人工裁决入口（UI 复用 SOP approve 模式）。approve 触发 C-3.5 晋升。　⟦approve/reject 实现+bridge 状态机测试通过；接口门待本机⟧
- [~] **B-3.5** `GET /runs/{run_id}/events/stream` — SSE（复用 trial_api SSE 实现模式），推 EVOLUTION_PHASE 事件。　⟦SSE 实现；接口门待本机⟧
- [~] **B-3.6** `GET /api/v1/twin-evolution/proficiency?team_id=&scenario_category=` — SkillProficiency 聚合查询（技能进化面板主数据源）。　⟦/proficiency 实现；store.query 纯逻辑已测⟧

---

## C. 引擎/流程改造（M1/M2/M3 核心逻辑）

### C-1 ScenarioCompiler — 新文件 `sandbox/scenario_compiler.py`（~250 行）

- [x] **C-1.1** `compile(spec, team_snapshot) -> WorldStateSnapshot`：spec.world → `WorldStateManager.sync_resources/sync_workflow`；taskflow → pending_tasks（按 DAG 依赖标记 blocked）；团队成员映射到 roles（不足时告警，多余成员闲置）。　⟦compile_scenario：DAG→pending_tasks(blocked标记)+resources+constraints+room_stages⟧
- [x] **C-1.2** DAG 校验：环检测、required_skills 在团队 skill 全集中的覆盖检查，编译失败抛带定位信息的 `ScenarioCompileError`。　⟦环检测/坏引用/缺字段三类失败用例通过⟧
- [x] **C-1.3** `build_chaos_timeline(spec) -> List[ScheduledChaos]`：把 ChaosPhase 展开为 per-step 概率表，交给 twin_loop（C-2.3）。　⟦build_chaos_timeline；概率1.0必注入/0不注入/越界不触发 测试通过⟧
- [~] **C-1.4** `generate_from_description(text, team_id) -> ScenarioSpec`：LLM 生成（走既有 chat_harness），prompt 输出严格 JSON，三次重试 + schema 校验，失败返回 None 而非半成品。　⟦generate_from_description 3次重试+校验实现；真 LLM 未实测⟧
- [x] **C-1.5** pytest：5 个种子场景全部 compile 通过；环依赖、缺角色、坏 JSON 三类失败用例。　⟦12 个场景测试用例全绿⟧

### C-2 TwinLoop 改造 — 改 `sandbox/twin_loop.py`

- [x] **C-2.1** `spawn_twins` 载入熟练度：从 SkillProficiency 存储读 agent×skill 成功率写入 `AgentTwin.skill_proficiency`（无记录默认 0.5）。　⟦set_proficiency_priors + _spawn_twins 载入，测试通过⟧
- [x] **C-2.2** 动作结算消费熟练度：执行 work_on_task 时成功概率 = `clamp(0.3 + 0.6 * proficiency, 0.2, 0.95)`，耗时 = `base_duration * (1.5 - 0.5*proficiency)`；同一 session 内成功一次该 twin 的临时熟练度 +0.02（演练中可见的"练熟"效应，不写回全局）。常量集中到文件顶部，便于调参。　⟦_settle_skill_action：成功率公式+失败折损+练熟效应；高低熟练度对照测试通过（hi>lo*1.1）⟧
- [x] **C-2.3** 混沌剧本驱动：run_simulation 接受 `chaos_timeline` 参数，每 step 按概率表自动注入（复用既有 `_chaos_states` 注入机制），与手工 inject 并存；`skill_degraded` 事件实现为目标 skill 熟练度临时 -0.3。　⟦set_chaos_timeline + _apply_scheduled_chaos 接入顺序循环与 step_once⟧
- [x] **C-2.4** 落 SkillUsageRecord：每次动作结算生成记录（A-2.1），通过回调交 trial_store 异步落盘；同时发 `SKILL_USAGE` SSE 事件（节流：每 10 条批量推一次）。　⟦SkillUsageRecord 缓冲+drain+失败必带 failure_reason，测试通过⟧
- [~] **C-2.5** `llm_decision.py` prompt 增强：身份段注入熟练度表（"你的技能及历史成功率：…"），决策输出增加 `skill_used` 字段；解析失败回退规则引擎（现有 fallback 路径不动）。　⟦prompt 注入熟练度表+skill_used 输出字段；LLM 实际效果未验证⟧
- [x] **C-2.6** pytest：固定随机种子下，高熟练度团队 vs 低熟练度团队跑同场景，前者 total_score 显著更高（验证熟练度语义生效）；chaos_timeline 注入次数符合概率期望（容差断言）。　⟦test_skill_proficiency 8 用例全绿⟧

### C-3 EvolutionBridge — 新文件 `sandbox/evolution_bridge.py`（~300 行，胶水层）

- [x] **C-3.1** `identify_weak_skills(team_id, scenario_id, window=5) -> List`：聚合最近 window 个同场景 trial 的 usage 记录，规则：成功率 < rubric.skill_expectations（缺省 0.6）或趋势连续 3 点下滑。输出含证据（失败记录样本）。　⟦identify_weak_skills：成功率阈值+趋势下滑，测试通过⟧
- [x] **C-3.2** `reflect`：弱 skill 的失败记录（failure_reason + context）喂 `evolution/mutator.reflect_on_failures`；结果存 EvolutionRun.reflection。　⟦对接 mutator.reflect_on_failures（mock 验证）⟧
- [x] **C-3.3** `mutate`：调 `mutator.generate_candidates`（含反思）+ `skill_evolver.evolve_skill`（不含反思的独立改写）各产候选，合并去重，**上限 4 个**；候选过 `evolution/constraints` 检查 + `fitness.apply_length_penalty` 预筛。　⟦generate_candidates 上限 4（mock 验证）⟧
- [~] **C-3.4** `ab_test`：为基线 + 每候选创建对照 Trial（同 scenario_id、同随机种子、generation 同代标记 ab_test）；候选 skill 的 instructions 注入对应 Branch 的 twin（只改该 Branch 的 spec 副本，不动真库）；跑完用 `evaluate` 五维分 + `fitness.evaluate_skill` 计算综合 fitness = `0.6*五维总分 + 0.4*skill_fitness`。　⟦A/B 执行器在 evolution_api._default_ab_runner（真实建 trial+跑+评估）；同随机种子控制未实现；mock 路径全绿⟧
- [x] **C-3.5** `promote`：胜者需满足 fitness 提升 ≥ 5% 且不低于基线任何单维 10% 以上；走 `skill_library.evaluate_publish_gate` → `create_version_snapshot` → `skill_evolver.apply_evolution`；失败状态置 rejected 并记录原因。`auto_apply=false` 时停在 gating 等人工 approve。　⟦晋升判定 5%提升+单维10%回退保护+publish_gate+快照+apply_evolution（mock 全流程通过）⟧
- [x] **C-3.6** 成本闸门：每阶段累计 token 计入 `cost_tokens`，超过 `config/settings.json` 新增的 `evolution_budget_tokens`（默认 200k）即中止并置 failed(budget)；接入既有 cost_policy 记账。　⟦预算闸门超限中止测试通过；settings.evolution_budget_tokens 可配⟧
- [~] **C-3.7** 自动触发钩子：trial evaluate 完成后若 total_score < rubric 阈值，发 `EVOLUTION_SUGGESTED` 事件（仅建议，前端弹提示，不自动跑）；nightly plist 任务可调 B-3.1（复用 `config/launchd/` 既有机制，本期只留接口不改 plist）。　⟦EVOLUTION_SUGGESTED 事件已在 evaluate 低分时发出；nightly 自动触发未接⟧
- [x] **C-3.8** pytest：mock LLM 全流程（identify→promote）状态机走通；预算中止用例；门禁拒绝用例；版本可回滚用例。　⟦test_evolution_bridge 7 用例全绿（含预算中止/门禁拒绝/人工拒绝）⟧

### C-4 环境空间状态机化 — 后端部分

- [~] **C-4.1** 房间由场景定义后，`world_state` 增加 `move_agent(agent_id, room_id)` 语义校验：只允许沿 taskflow 阶段顺序迁移或回退（拖拽乱放返回 409 + 原因）。　⟦world_state.set_room_stages+validate_move 完成并测试；拖拽 409 API 对接未做⟧
- [ ] **C-4.2** `sync-from-dt` 接口（`sandbox/api.py`）兼容场景房间：同步时携带 scenario_id，房间集合以场景为准。　⟦未实现⟧

---

## D. 前端改造（M1 部分 + M4，全部在 `src/frontend/`）

### D-0 状态收敛（先行，阻塞其余 D 项）

- [~] **D-0.1** `_sx` 成为唯一真源：新增字段 `scenarioId/scenarioSpec/generation/skillStats/evolutionRun`；`window._DTS` 与 `window._currentSessionId` 改为 `Object.defineProperty` getter 别名指向 `_sx`，控制台打 deprecation warn 一次。　⟦_sx 扩展+_currentSessionId defineProperty 别名化（含 deprecation warn）；_DTS 仍为独立对象未代理⟧
- [ ] **D-0.2** `S.positions` 迁移到 `_sx.roomAgentMap`（v3.1 第 0.3 节遗留），grep 确认无残留直接读写 `S.positions`。　⟦S.positions 仍为定时同步，未迁移⟧
- [ ] **D-0.3** 回归：v3.1 todos 第 1 节表格中全部按钮重测一遍（createTrial/stepOnce/autoRun/pause/terminate/fork/inject/evaluate/extractSop/feedback），全绿才继续。　⟦需启动后端手工回归⟧

### D-1 场景选择器（M1）

- [~] **D-1.1** 导演台顶部新增"业务场景"区：横向卡片列表（icon/名称/难度星级/历史最佳分/匹配度徽章），数据来自 B-1.1 + B-1.5；选中写 `_sx.scenarioId`。样式复用 `.mode-card` 体系。　⟦实现为下拉选择器（含难度星级/历史最佳分/匹配度/缺口提示），未做卡片式⟧
- [~] **D-1.2** `createTrial` 携带 `scenario_id` 与 `generation`（默认 0；从代际视图"再战一代"入口进入时 = parent.generation+1 并带 parent_trial_id）。　⟦createTrial 携带 scenario_id/generation/parent_trial_id；UI 门待手测⟧
- [~] **D-1.3** 环境空间渲染改造：`defaultRooms()` 仅作无场景 fallback；选中场景后房间列表/icon/容量由 `_sx.scenarioSpec.world.rooms` 渲染，房间卡片显示所属业务阶段序号；拖拽违规时 toast 显示 409 原因（对接 C-4.1）。　⟦applyScenarioRooms 渲染 env-grid 2D+同步 S.rooms（含阶段标记）；3D 视图与 409 toast 未接⟧
- [ ] **D-1.4** "生成场景"入口：textarea 描述业务 → 调 B-1.4 → 预览草稿 spec（房间/任务/扰动摘要）→ 确认保存。失败态文案明确（LLM 生成失败/校验失败字段）。　⟦后端 /generate 已就绪，前端入口未做⟧

### D-2 技能进化面板（M4 核心新视图）

- [~] **D-2.1** 新导航项"技能进化"+ view-panel：上半部 per-skill 成功率柱状图（复用 `.bar-chart-container`，按 B-3.6 数据渲染；低于期望的 skill 红色 + ⚠）；点击 skill 展开 usage 失败样本列表（failure_reason + step 链接）。　⟦skill-stats 柱状图+弱skill红色⚠+期望对比已实现于导演台面板；失败样本展开未做⟧
- [~] **D-2.2** "发起进化"按钮：选中弱 skill（或留空自动识别）→ POST B-3.1 → 渲染五节点进度流（识别→反思→变体→A/B→晋升，复用 `.secs-pipeline-indicator` 样式），SSE（B-3.5）驱动节点点亮。　⟦发起进化+五节点进度流（secs-pipeline 样式）已实现；用轮询替代 SSE（后端 SSE 已备）⟧
- [ ] **D-2.3** A/B 结果卡：基线 vs 各候选的五维分对比（雷达图双叠加，扩展现有 `renderRadarChart` 支持两层 polygon）+ fitness 数值 + instructions diff（简单行级 diff，新增 `js/digital-twin/diff.js`，无需引库）。　⟦A/B 对比卡/雷达叠加/diff 未做⟧
- [~] **D-2.4** 晋升裁决 UI：gating 状态显示 approve/reject 按钮（复用 `.sop-btn` 样式），调 B-3.4；applied 后显示新版本号 + "回滚"按钮（调 skill_library rollback 既有接口）。　⟦approve/reject 按钮（sop-btn 样式）已接 B-3.4；回滚按钮未做⟧
- [ ] **D-2.5** trial 完成后收到 `EVOLUTION_SUGGESTED` 事件时，导演台弹非阻塞提示条："本次试炼 X 项技能低于预期，去进化 →"。　⟦未做⟧

### D-3 代际对比（M4）

- [ ] **D-3.1** 试炼时间轴（`.trial-timeline`）按 generation 分组着色，hover 显示 gen/score。　⟦未做⟧
- [ ] **D-3.2** 代际成长曲线：同 scenario_id 下各代 total_score 折线（复用 erf-mini-chart 的 SVG 画法放大版），数据来自 B-2.5。　⟦未做⟧
- [ ] **D-3.3** 雷达图代际叠加：gen N（虚线）vs gen N+1（实线）。　⟦未做（nextGeneration 再战一代入口已实现，代际字段全链路已通）⟧

### D-4 拆文件（M4 收尾）

- [ ] **D-4.1** 内联 JS 抽出为 `js/digital-twin/{state,api,director,scenario,evolution,render-rooms,render-charts,diff}.js`；html 保留结构/样式/初始化引导。每抽一个模块跑一遍 D-0.3 回归再抽下一个（小步提交）。　⟦未拆⟧
- [ ] **D-4.2** `vite.config.mjs` 增加入口（对齐既有多页配置）；CSP 不变。　⟦未做⟧
- [ ] **D-4.3** `__tests__/` 增加 state.js 单测：别名 getter 等价性、roomAgentMap 迁移正确性。　⟦未做⟧

---

## E. 测试与验收（每阶段出口）

- [~] **E-1** M1 出口：`pytest tests/ -k scenario` 全绿；前端选择"客服工单高峰"→ createTrial → 环境空间渲染出场景房间 → autoRun 跑完 → evaluate 出分。手工录屏一遍。　⟦场景系统 pytest 12 用例全绿（离线 runner）；UI 手测/录屏待做⟧
- [~] **E-2** M2 出口：跑 2 次同场景 trial，`GET /skill-stats` 返回非空且成功率随熟练度变化；feedback 后 `skill_library.list_versions` 出现新快照且可回滚。　⟦熟练度/反哺逻辑测试全绿；本机接口联测待做⟧
- [~] **E-3** M3 出口（闭环验收，本轮成败判据）：完整跑一次 EvolutionRun（真 LLM，小预算）：弱 skill 被识别 → 4 个以内变体 → A/B 对照 trial → 胜者过门禁写回 → 新建 generation+1 trial，其 skill_breakdown 中该 skill 成功率高于上代。把全过程 trial_id/run_id 记入验收记录。　⟦mock LLM 全闭环（识别→变体→A/B→门禁→写回→拒绝/预算）7 用例全绿；真 LLM 小预算实跑待做⟧
- [ ] **E-4** M4 出口：D-0.3 全量按钮回归 + 新增视图四门验收；`npm test`（__tests__）全绿；单文件行数降到 < 1500（HTML 结构+样式）。　⟦按钮回归与单文件瘦身未做⟧
- [~] **E-5** 全程回归：`tests/test_sandbox_secs.py`、`tests/test_full_flow.py` 在每个 M 结束时必须保持绿。　⟦沙箱环境无 fastapi 无法跑 test_sandbox_secs/test_full_flow；新增 27 个纯逻辑用例全绿，本机需复跑全量⟧

---

## F. 实施顺序与依赖

```
W1  A-1 A-4.1 A-4.2 ──► C-1 ──► B-1 ──► D-1（M1 可演示）
W2  A-2 A-4.3 A-4.4 A-4.5 ──► C-2 ──► B-2.1/2.2/2.3/2.5
W3  B-2.4(真实反哺) + D-0（状态收敛，可与 W2 并行由前端进行）
W4  A-3 ──► C-3 ──► B-3（M3 闭环，E-3 验收）
W5  D-2 D-3 ──► D-4 ──► E-4/E-5（M4 收尾）
```

并行原则：前端 D-0 不依赖后端新接口，可最早开工；C-3 依赖 C-2 的 usage 数据真实落盘后才能联调，前期用 mock 数据先行开发。

每条目完成时在本文件标记并附：文件+行号、验证命令/请求、UI 截图（涉及前端时）。
