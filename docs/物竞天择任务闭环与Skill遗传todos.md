<!-- docs-signoff: author="Grok" kind="llm" doc="todos" ts="2026-07-13T17:00:02Z" -->
# 物竞天择 v4 Todos — 任务闭环 · Skill 遗传与集成

> 配套 [`物竞天择任务闭环与Skill遗传plan.md`](物竞天择任务闭环与Skill遗传plan.md)（v4.0）。  
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。  
> 承接 v3：[`物竞天择数字孪生演练todos.md`](物竞天择数字孪生演练todos.md) 中 XV/XB 遗留项并入本清单标注。  
> 执行顺序：XG-0 → XG-1 → XG-2 → XG-3 → XG-4 → (XG-5 ∥ XG-6) → XG-7 → XG-8 → XG-9 → XG-10 → XG-11 → XG-12 → XG-13 → XR-1。

---

## 已知缺陷（并入对应阶段，勿另开大坑）

| ID | 现象 | 状态 |
| --- | --- | --- |
| **D1** | mixed 未接 `run_eras` | ✅ 已修（XG-5） |
| **D2** | 分场误强制 `extra_team_ids=[]` / 加对比自动切对抗 | ✅ 已修（XG-7.4 校准：分场也允许多队入场比 skill，**不**自动改赛制） |
| **D3** | PlanStep.required_skills 常空 | ✅ 已修（列/角色/启发式） |
| **D4** | 技能 ID 漂移误饿死 | ✅ 已修（skill_identity） |

---

## 依赖盘点（v3 已就绪，v4 直接接）

| 零件 | 文件 | v4 用途 |
| --- | --- | --- |
| EcoDrill / CollabGenome / timeline / gene_pool | `sandbox/eco_drill.py` | 任务生境 + 遗传内核 |
| `run_eras` 方法体 | `eco_drill.py` | mixed 纪元 |
| ExecutionPlan / validate_plan | `agents/execution_plan.py` | 上游计划 |
| 计划→SECS 场景 | `sandbox/plan_scenario_bridge.py` | 编译参考（不复用 SECS 输出） |
| trial 路由 drill_kind | `sandbox/trial_api.py` | contract 透传 |
| 三档赛制 UI | `eco-console.js` | 绑定计划 + 预算 + 世界杯语义 |
| 遗传学七图 | `eco-genetics.js` | Skill 中心增量 |
| 排兵策略表 | `eco-matchup.js` | 不变，事后镜头 |
| T_i 分解 | `survival_decompose.py` | skill / 协作 / 残差 |

---

## XG-0: 文档落盘

- [x] **XG-0.1** 写入 `docs/物竞天择任务闭环与Skill遗传plan.md`（sign-off）
- [x] **XG-0.2** 写入 `docs/物竞天择任务闭环与Skill遗传todos.md`（本文件，sign-off）
- [x] **XG-0.3** `docs/README.md` 增加导航条目（current）
- [x] **XG-0.4** 本两文件 sign-off 校验 OK（全仓 `--strict` 仍有历史缺签 36 FAIL，非本轮引入）
- [x] **XG-0.5** `.wolf/memory.md` 追加落盘记录；`.wolf/anatomy.md` Manual note 2026-07-13

---

## XG-1: 计划技能数据质量（闭环上游）【D3】

- [x] **XG-1.1** `parse_plan_table` / `build_plan_from_text` 支持「所需技能」列  
- [x] **XG-1.2** 角色→默认 `required_skills` 映射表  
- [x] **XG-1.3** title/description 关键词启发式补技能  
- [x] **XG-1.4** `validate_plan(profile='eco')`  
- [x] **XG-1.5** plaza 侧「送入物竞试验田」深链（`sendPlanToEcoField` + sessionStorage）

---

## XG-2: TaskHabitatContract 编译器 + API

- [x] **XG-2.1** `plan_eco_bridge.py` TaskHabitatContract  
- [x] **XG-2.2** `compile_plan_to_habitat_contract`  
- [x] **XG-2.3** `compile_tasks_to_habitat_contract`  
- [x] **XG-2.4** `validate_habitat_contract`  
- [x] **XG-2.5** API `POST /api/v1/eco-runtime/habitat-contract/from-plan`  
- [x] **XG-2.6** API `POST /api/v1/eco-runtime/habitat-contract/from-tasks`  
- [x] **XG-2.7** `tests/test_plan_eco_bridge.py`  
- [x] **XG-2.8** 挂在既有 `eco_runtime_routes`（无需新 mount）

---

## XG-3: Skill 身份归一【D4】

- [x] **XG-3.1** `skill_identity.py`  
- [x] **XG-3.2** `run_drill_via_trial` genome 归一  
- [x] **XG-3.3** contract niches 归一  
- [x] **XG-3.4** 覆盖于 `tests/test_plan_eco_bridge.py`

---

## XG-4: eco_drill 任务生境

- [x] **XG-4.1** niches 列表  
- [x] **XG-4.2** step 按 niche_index 取 demand  
- [x] **XG-4.3** 窗口推进 + timeline niche 字段  
- [x] **XG-4.4** 角色亲和  
- [x] **XG-4.5** skill_origin=learn 事件  
- [x] **XG-4.6** contract 入参  
- [x] **XG-4.7** 无 contract v3 零回归（eco_drill_v2 全绿）  
- [x] **XG-4.8** 技能选择优势单测  
- [x] **XG-4.9** 绑定计划降 drift + `task_coupling` 配置节  

---

## XG-5: run_eras 生产接线【D1】

- [x] **XG-5.1** `task_goal.era` / mixed → `run_eras`  
- [x] **XG-5.2** 透传 era config  
- [x] **XG-5.3** era_count=1 专项单测  
- [x] **XG-5.4** contract 路径 + 选择优势单测（覆盖组合场景）  
- [x] **XG-5.5** trial_api.branch_run 透传

---

## XG-6: trial_api 透传 contract

- [x] **XG-6.1** task_goal.contract 快照  
- [x] **XG-6.2** branch_run 传递  
- [x] **XG-6.3** integration 字段

---

## XG-7: 前端绑定计划 · 预算 · 赛制语义【D2】

- [x] **XG-7.1** `eco2BindPlan` + URL/__ECO_PLAN__  
- [x] **XG-7.2** 自动填 steps/gens  
- [x] **XG-7.3** 计划生态位 chips  
- [x] **XG-7.4** 分场允许多队 `extra_team_ids`（比个体 skill）；**加对比种群不自动改赛制**；对抗才比协作/策略；混合=个体+团队（世界杯）  
- [x] **XG-7.5** confrontation 无 rival 拦截  
- [x] **XG-7.6** mixed 带 era  
- [x] **XG-7.7** task_goal 带 contract  
- [x] **XG-7.8** Plaza 深链按钮 `sendPlanToEcoField` + sessionStorage  
- [x] **XG-7.9** `node --check` eco-console.js

---

## XG-8: Skill 集成报告

- [x] **XG-8.1** `skill_integration.py`  
- [x] **XG-8.2** 结果附 integration  
- [x] **XG-8.3** 控制台 `eco2-integration` 区块  
- [x] **XG-8.4** `POST /api/v1/eco-runtime/skill-integration/suggest`  
- [x] **XG-8.5** `POST .../apply`（confirm=false 预览；true 写回）  
- [x] **XG-8.6** apply 可选 `feedback_router`（默认关）  
- [x] **XG-8.7** suggest_only 纯函数单测

---

## XG-9: 遗传学 Skill UI 深化

- [x] **XG-9.1** `planCoverageHeatmap` + vitest  
- [x] **XG-9.2** `perSkillHeritability` + vitest  
- [x] **XG-9.3** `verticalVsHorizontalTransfer` + vitest  
- [x] **XG-9.4** lineage 区渲染热力 / 传递比 / 分 skill h² + 判词  
- [x] **XG-9.5** 复制 JSON / apply / 适者派发按钮

---

## XG-10: 棘轮与生产闭环

- [x] **XG-10.1** ratchet key `eco_plan:{fingerprint}`  
- [x] **XG-10.2** 演练/纪元结束 advance（team + plan）  
- [x] **XG-10.3** `dispatch-winner` API + 控制台按钮  
- [x] **XG-10.4** 验收命令见文末

---

## XG-11: 入口 UX — 先派发团队任务再进物竞（2026-07-13）

- [x] **XG-11.1** Plaza「派发并送入物竞」：强制选团队；无 task 时先 `dispatch`；深链带 `team_id`/`task_id`
- [x] **XG-11.2** 团队任务表 `🧬 物竞`（pending 起，含 running/completed）
- [x] **XG-11.3** `eco2ApplyTeamFromUrl` + `eco2BindTaskById` 自动投放种群与契约
- [x] **XG-11.4** vitest 源码断言 + node --check

---

## XG-12: 对比种群任务选择 · Apple-to-apple（2026-07-13）

- [x] **XG-12.1** 对比队可选挂接任务（同 plan → 共用考卷；不选 → 随机生境）
- [x] **XG-12.2** `_resolveSharedExam`：`apple` / `primary_exam` / `random` 三态
- [x] **XG-12.3** `task_goal.comparison_mode` + `rival_task_bindings` 透传
- [x] **XG-12.4** UI：`eco2-rival-chips` 任务下拉 + Apple 提示
- [x] **XG-12.5** 硬约束：加对比种群 **不** 自动改赛制（用户校准）

---

## XG-13: T_i 存活归因 — skill / 协作 / 残差（2026-07-13）

- [x] **XG-13.1** `sandbox/survival_decompose.py`：`T_i = skill + collab + residual`（份额和=1）
- [x] **XG-13.2** `eco_drill` 结果附 `survival_attribution` + ranking `attr_*` 字段
- [x] **XG-13.3** 控制台种群行 T_i 分解条 + 报告「存活归因」表 + 分场精英阶梯
- [x] **XG-13.4** `tests/test_survival_decompose.py` 全绿
- [x] **XG-13.5** 唯一适应度仍是 `survival_ticks`；分解仅可解释，不另设评分

---

## XR-1: 本机全量验收

- [x] **XR-1.1** 无 contract → v3 行为（eco_drill_v2 回归绿）
- [x] **XR-1.2** contract / division / mixed→run_eras / confrontation 拦截（单测+前端）
- [x] **XR-1.3** 谱系热力/传递/集成 UI 已接线  
- [x] **XR-1.4** pytest plan_eco_bridge + survival_decompose + eco_smoke_static + eco_drill_v2/engine/routing/runtime_config **73 passed**；vitest eco-genetics-v4 **4 passed**
- [x] **XR-1.5** 自动化静态冒烟：`tests/test_eco_smoke_static.py`（HTML/JS 入口、模块 import、config 节、滑杆/生境层源码契约）。浏览器 SECS 手感仍建议本机 `./start.sh` 点验一次  
- [x] **XR-1.6** 后端热更：start.sh reload / process_started_at

---

## 并入 v3 遗留（本轮一并收口）

| v3 项 | 本清单处理 | 状态 |
| --- | --- | --- |
| XV-8.2 谱系七图本机复验 | XR-1.3 + XG-9 | ✅ 代码接线；真数据手感建议本机点验 |
| XV-8.3 相关 pytest | XR-1.4（73 passed） | ✅ |
| mixed 纪元未接线 | XG-5 | ✅ |
| XT-9.7 / XT-10.4 双队浏览器 | XG-7.4 多队入场 + XG-12 | ✅ 代码；浏览器 E2E 建议本机 |
| XB-6.1 生境 3D 轻量层 | HUD + 生态位图腾 + 觅食光点 + 捕食竖线 | ✅ |
| XB-7.1 pet-config 滑杆 | range 联动 + 钳位 + 搜索 + 分节折叠 + dirty 高亮 | ✅ |

---

## 归属建议

| 工作面 | 建议 |
| --- | --- |
| plan/todos、bridge、eco_drill、identity、integration、归因、pytest | 本机编码 Agent（Grok）✅ 本轮完成 |
| 浏览器三档 E2E 手感、Plaza 深链点验、密钥相关 | 本机人工 / CodeBuddy 风格复验 |
| v2/v3 内核与赛制 UI | 已完成（Fable 5 / CodeBuddy） |

---

## 快速验收命令（实现期）

```bash
# 物竞 v4 核心回归（本机 venv）
venv/bin/python -m pytest \
  tests/test_plan_eco_bridge.py \
  tests/test_survival_decompose.py \
  tests/test_eco_smoke_static.py \
  src/backend/tests/test_eco_drill_v2.py \
  src/backend/tests/test_eco_drill_engine.py \
  src/backend/tests/test_eco_drill_routing.py \
  src/backend/tests/test_eco_runtime_config.py -q

node --check src/frontend/js/digital-twin/eco-console.js
node --check src/frontend/js/office/office-scene.js
npx vitest run src/frontend/__tests__/eco-genetics-v4.test.js

# 服务 + 浏览器（可选手感）
./start.sh
# http://localhost:5173/Agent-digital-twin.html?office3d=1
# http://localhost:5173/pet-config.html → 仿生生态运行时参数 Tab
```

---

## 本轮收口纪要（2026-07-13/14）

1. **赛制世界杯语义**：①分场=多队球星比 skill；②对抗=球队协作；③混合=世界杯。客观环境=同一任务过滤，非天选。  
2. **XG-12** 对比队可选同/相似任务 → Apple-to-apple。  
3. **XG-13** T_i 分解 skill/协作/残差，唯一适应度仍是生存 ticks。  
4. **XB-7.1** pet-config 滑杆+搜索+折叠。  
5. **XB-6.1** 生境 HUD + 3D 图腾 + 觅食光点。  
6. 回归：**73 pytest + 4 vitest** 全绿。
