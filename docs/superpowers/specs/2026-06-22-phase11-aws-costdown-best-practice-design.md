# Phase 11 · AWS 运维降本增效最佳实践 Case — 设计文档

> 日期：2026-06-22
> 状态：设计已与用户逐节确认（§1~§4）；**已对照真实代码库核查并修正（见 §7），可写入 todos 实施计划**
> 北极星：用一条可复现链路证明「角色对齐 → 迭代萃取特有技能 → 孪生协作 → 真实降本锁棘轮」能拿到「脚本可断言」的降本增效最佳实践。

---

## 0. 背景与定位

### 0.1 要解决的问题

用户要求重新给出一个示例，展示运维过程中的**最佳降本增效 case**，4 步闭环：

1. 在 Agent 团队中找到 AWS 运维团队，给每个 Agent 赋予合适的 skill+工具。
2. 在 Plaza 让该团队讨论 ElasticSearch 实例缩放运维脚本的实现，不停修正执行计划，萃取一项**特有技能**给运维系统开发同事，并让此技能演进、验证，得到该技能确实能产出正确脚本。
3. 在数字孪生工作坊演练该脚本（自动运行或单步），得到团队的协作数据。
4. 在成本优化上，采用棘轮页得到的 skill+协作数据的优化方案，最终把团队 token 数量降到设定目标。

每一步都要通过脚本验证，最终把该案例的最佳实践详细步骤写入 todos 形成新 Phase。

### 0.2 与现有 `scripts/aws_ops_e2e_test.py` 的关系

仓库已有 `aws_ops_e2e_test.py`（T0~T8，2026-06-16 复测 `PASS=14/FAIL=0`），但它与「降本增效最佳 case」有 4 处本质差距：

| 用户要求 | 现有 e2e 现状 | 差距 |
|---|---|---|
| ① 给每个 Agent 赋予**合适的** skill+工具 | `pick_by_keywords` 按 aws/terraform/shell 关键词匹配默认池 | **工具层** `run_shell`/`run_python` 已有（够用）；但默认池**无 aws/es/cost 等领域专用 skill**，按关键词匹配 skill 为空 → 角色能力错配。修正：本 Phase 新建领域 skill + 用真实工具绑定（§7.2）|
| ② 计划**不停修正**，萃取**特有技能**并演进/验证得到正确脚本 | 讨论跑一次出 6 项计划就派发；萃取是讨论结束自动触发一次性 | 无「计划→执行→修正→再计划」迭代环；萃取技能未与「能否产出正确脚本」挂钩 |
| ③ 数字孪生演练得到**协作数据** | step 产出 `agent_actions`/`messages` | 协作数据**未回流**到「脚本对不对」「哪个 agent 是瓶颈」 |
| ④ 棘轮页 skill+协作数据 → 团队 token 降到目标 | 9.1~9.6 已打通 target_id 绑定+复测+棘轮 | **未跑过**一次「真实降 token→达标→锁棘轮」完整实证 case（Phase 7 C4/C5 标⚠️需 LLM） |

**定位**：Phase 11 把现有 e2e 从「功能能跑通」升级为「降本增效可验证的最佳实践 case」，每一步都有脚本断言。两者职责分离，互不污染。

### 0.3 关键决策（已与用户确认锁定）

| 决策点 | 选定 |
|---|---|
| 脚本关系 | 新建独立脚本 `scripts/aws_ops_costdown_e2e.py` + 复用 e2e 的 `ApiClient`/`Runner`/`step` 封装 |
| LLM 依赖 | **必须真实 LLM**，不降级（P0b 找不到可用模型即 FAIL） |
| 第②步迭代形态 | **脚本 criteria 驱动多轮修订**（萃取的「特有技能」=能产出达标脚本的讨论模式） |
| 第①步能力补全 | **新建 `src/backend/agents/teams/aws_ops_team.py` 静态模板** |
| 第④步降本目标 | **百分比降幅，默认 20%**（metric=tokens_per_goal） |
| 脚本实现形态 | **Shell + aws-cli**（不用 terraform/boto3；与默认池已有 `run_shell` 对齐） |

---

## 1. §1 4 步闭环断言契约（G1~G4 主干）

核心：把用户 4 步要求变成 4 组可脚本断言的验收契约。

### G1 · 角色能力对齐（对应第①步）

> 「找到 AWS 运维团队 → 每个 Agent 赋予合适 skill+工具」

- 新建 `src/backend/agents/teams/aws_ops_team.py`，定义 6 角色 × 绑定的 skill/tool：

> **⚠️ 已对照 `tool_registry.py` 修正**（2026-06-22）：原表里的 `communication` / `auto_monitor` / `compliance_region_guard` **都不是已注册工具**，会让 G1「tools[].tool_id 与模板一致」断言失败。下表只用**真实存在的 tool name**（核实清单见 §7）。技能（skill）是本 Phase 新建的领域技能（可与模板自洽），与工具区分开——`compliance_region_guard` 只作技能、不作工具。

| 角色 | 工具（均为已注册 tool） | 技能（本 Phase 新建领域 skill） |
|---|---|---|
| 运维 Leader | `run_shell`、`delegate_task` | `aws_es_scaling_orchestration` |
| 上云架构师 | `run_shell`、`read_file` | `aws_es_capacity_planning` |
| 运维操作员 | `run_shell`、`run_python` | `aws_cli_script_authoring` |
| 巡检监控员 | `run_shell`、`set_alarm`、`watch_file` | `monitor_alarms_setup` |
| 成本优化成员 | `run_shell`、`run_python` | `cost_ri_advisor` |
| 北美 AI 项目运维员 | `run_shell`、`search_files` | `compliance_region_guard` |

> 可选告警/通信类工具（按需替换/增补，均已注册）：`set_alarm`、`watch_file`、`schedule_task`、`cron_trigger`、`send_message`、`broadcast`、`publish_event`。

- **G1 断言**：脚本调 `create_aws_ops_team()` 后，`GET /teams/{tid}/agents` 每个 agent 的 `tools[].tool_id` 与 `skills[].skill_id` **非空且与模板一致**；且每个 `tools[].tool_id` 必须能在 `GET /tools`（已注册工具）里查到（防止再绑不存在的工具）。

### G2 · 迭代式计划修订 + 特有技能萃取（对应第②步）

> 「讨论 ES 缩放脚本 → 不停修正 → 萃取一项特有技能 → 演进/验证 → 得到正确脚本」

**评分函数** `score_script(plan_content) → {score: 0~5, missing[]}`，5 项 criteria（全部针对 shell + aws-cli 实现）：

1. **实例规格识别**：含 `describe-elasticsearch-domain` 或 `describe-domain-config`（读取当前配置）
2. **变更执行**：含 `update-elasticsearch-domain-config`（含 `--instance-type` / `--instance-count` / `--cluster-config` 等变更参数）
3. **状态校验**：含轮询逻辑（`describe-domain` 查 `Processing`/`Active` 状态，shell 里体现为 `while`/`sleep`/轮询）
4. **监控告警**：含 CloudWatch 告警（`put-metric-alarm` 或 `cloudwatch put-metric-alarm`）
5. **回滚 + 成本预估**：含回滚分支（`if/else` + 备份配置）+ 成本估算注释或 `aws pricing`

- Plaza 跑计划 v1 → 评分 → 若 `score<5`，把 `missing[]` 作为修订意见回灌 discussion → 跑 v2 → … 最多 3 轮。
- 达标轮的 transcript → 萃取 1 项**特质技能** `aws_es_scaling_script_authoring`（trait，绑定运维 Leader）。
- **G2 断言**：
  1. 最终轮 `score==5`
  2. trait skill 过 `verify_skill`（沙箱 pass_rate≥0.7）+ `evolve_skill`（version+1）+ `publish` 三道门禁
  3. 验证产出的脚本 fragments **包含 5 项 criteria 对应的 aws-cli 子命令/shell 结构**

### G3 · 数字孪生协作数据（对应第③步）

> 「工作坊演练脚本 → 自动/单步都得到协作数据」

- Plaza 最终计划派发为任务 → 建 sandbox session（team=aws_ops, mode=what_if, use_llm=true）→ 分别跑**自动运行**和**单步运行**两条路径。
- **G3 断言**：两条路径都满足
  1. `total_steps_executed ≥ 5`
  2. 每步 `agent_actions` 非空
  3. `messages_count` 随步数递增
  4. `agent_actions` 里**至少 3 个不同 agent** 有动作（证明真协作而非单 agent 独走）
  5. `global_reward` 曲线非空

### G4 · 真实降本 + 棘轮锁定（对应第④步）

> 「棘轮页 skill+协作数据 → 团队 token 降到目标」

- **Run A（基线）**：用一组**未绑定** G2 特质技能的 agent 跑同一 ES 缩放任务，记 `baseline_tokens_per_call`。
- 创建目标：`metric=tokens_per_goal`，`baseline=Run A 每调用 token`，`target=baseline×0.8`（降 20%）。
- **Run B（优化后）**：把 G2 特质技能**注入**团队 → 重跑同一任务 → 记 `current_tokens_per_call`。
- **G4 断言**：
  1. `current < target`（即降幅 ≥20%）
  2. `status=achieved`
  3. `cost_efficiency:{team}` 棘轮被自动锁定
  4. 再跑一次更差的 run，棘轮值**不下降**（复用 Phase 7 C5 单调口径）
  5. 成本页 KPI/报告可见该团队降幅

---

## 2. §2 脚本分层结构

### 2.1 文件清单（5 个新文件 + 1 个文档章节）

| 文件 | 类型 | 职责 |
|---|---|---|
| `src/backend/agents/teams/aws_ops_team.py` | 后端 | 静态团队模板：6 角色 × skill/tool + `create_aws_ops_team()` 工厂 |
| `scripts/aws_ops_costdown_e2e.py` | 脚本 | **主 case 脚本**，跑 G1~G4 四组断言，复用 e2e 的 `ApiClient`/`Runner`/`step` |
| `scripts/_aws_costdown_assertions.py` | 脚本 | G1~G4 的**纯断言函数**（与 HTTP 客户端解耦，可单测） |
| `scripts/_aws_costdown_script_criteria.py` | 脚本 | G2 的 `score_script()` + 5 项 criteria 检查器（纯函数，可单测） |
| `src/backend/tests/test_aws_ops_costdown.py` | 测试 | 离线单测：模板结构、评分函数、断言函数（不依赖 LLM） |
| `docs/全局重构todos.md` § Phase 11 | 文档 | 新 Phase 章节（§3 详述结构） |

> 拆出 `_assertions.py` 和 `_script_criteria.py` 是为了让 **G2 评分逻辑和 G1~G4 断言逻辑可在无 LLM 环境单测**（参考 Phase 10「离线可验证部分」做法）。主脚本只负责编排，断言全委派给这俩模块。

### 2.2 主脚本 `aws_ops_costdown_e2e.py` 阶段划分

复用 e2e 的 `Runner.step(name, fn, critical=True)` 模式，18 个 step：

```
P0  bootstrap_auth()                    # 复用 e2e：鉴权 + CSRF
P0b find_real_llm_model()               # 关键：必须找到可用 LLM，找不到直接 FAIL（不降级）
P0c cleanup_legacy()                    # 清理历史 aws_ops_costdown_* 遗留

─── G1 角色能力对齐 ───
P1  create_aws_ops_team()               # 调 create_aws_ops_team() 工厂
P1b assert_g1_capabilities()            # 断言 6 agent × skill/tool 与模板一致

─── G2 迭代式计划修订 + 特有技能萃取 ───
P2  plaza_run_plan_v1()                 # Plaza 讨论 ES 缩放 → 计划 v1
P2b score_and_revise_loop()             # 评分 → 回灌修订 → v2/v3，最多 3 轮，断言 score==5
P2c extract_trait_skill()               # 萃取特质技能 aws_es_scaling_script_authoring
P2d verify_evolve_publish_skill()       # verify + evolve + publish 三道门禁
P2e assert_g2_correct_script()          # 断言验证产出的脚本 fragments 含 5 项 criteria

─── G3 数字孪生协作数据 ───
P3  dispatch_and_sandbox_run()          # 派发 + sandbox 自动运行
P3b sandbox_step_path()                 # sandbox 单步运行路径
P3c assert_g3_collab_data()             # 断言协作数据（步数/actions/messages/≥3 agent/reward）

─── G4 真实降本 + 棘轮锁定 ───
P4  run_a_baseline()                    # 未注入特质技能跑同一任务 → baseline_tokens_per_call
P4b create_target_and_inject_skill()    # 建 tokens_per_goal 目标（baseline×0.8）+ 注入特质技能
P4c run_b_optimized()                   # 注入后重跑 → current_tokens_per_call
P4d assert_g4_costdown_and_ratchet()    # 断言 current<target、achieved、棘轮锁定+单调

─── 收尾 ───
P5  build_report()                      # 写 docs/reports/aws-ops-costdown-report.{md,json}
```

### 2.3 与现有 `aws_ops_e2e_test.py` 的复用边界

**复用**（import，不复制）：
- `ApiClient` 类（HTTP 客户端 + CSRF + session）
- `Runner` 类 + `step()` 包裹器（统一 PASS/FAIL/SKIP 计数 + 报告）
- `bootstrap_auth`、`cleanup_legacy_aws_e2e_teams`、`find_codebuddy_model` 的实现思路（但 P0b 改为「找不到就 FAIL」而非降级）

**不复用**（独立实现）：
- 角色定义（新模板 `aws_ops_team.py` 是真源，e2e 的 `role_specs` 仍是它自己的）
- 评分函数（e2e 没有）
- G4 的 Run A/Run B 对比（e2e 没有）

### 2.4 失败语义

- **P0b 找不到可用 LLM → 整个 case 直接 FAIL**（不降级，对应决策「必须真实 LLM」）。这是与旧 e2e 最大的行为差异。
- 其余 step 失败 → 记 FAIL 但继续跑后续 step（收集完整失败信息），最终报告汇总。
- 报告末行打印 `COSTDOWN PASS: G1..G4 all green` 或 `COSTDOWN FAIL: <失败的 G>`。

---

## 3. §3 Phase 11 在 todos 文档的章节结构

插入位置：`docs/全局重构todos.md` 的 Phase 10 之后、「离线可验证部分的执行结果」之前。

```
## Phase 11 · AWS 运维降本增效最佳实践 Case（4 步闭环实证）

> 北极星：用一条可复现链路证明「角色对齐 → 迭代萃取特有技能 → 孪生协作 → 真实降本锁棘轮」
> 能拿到「脚本可断言」的降本增效最佳实践。与 aws_ops_e2e_test.py（功能验收）职责分离。
> LLM 依赖：必须真实 LLM，不降级（P0b 找不到可用模型即 FAIL）。

### 11.0 前置与定位
- 与 aws_ops_e2e_test.py 的职责分工（功能 vs 降本实证）
- 5 个新文件清单 + 复用边界

### 11.1 G1 · AWS 运维团队静态模板与角色能力对齐
- 新建 src/backend/agents/teams/aws_ops_team.py（6 角色 × skill/tool）
- create_aws_ops_team() 工厂 + 在 team_store 注册
- 验收：6 agent 的 tools/skills 非空且与模板一致；pick_by_keywords 不再空匹配

### 11.2 G2 · 脚本 criteria 评分函数（纯函数，可离线单测）
- score_script() 5 项 criteria（aws-cli/shell 语义）
- 单测覆盖：满分样本/各缺一项样本/空样本
- 验收：单测全绿（不依赖 LLM）

### 11.3 G2 · Plaza 迭代式计划修订环
- 计划 v1 → score → missing[] 回灌 discussion → v2/v3（最多 3 轮）
- 「修订意见回灌」的 API 路径（复用 plaza discussion 的 message 注入）
- 验收：最终轮 score==5；迭代轨迹可查（每轮 score 单调不退或收敛）

### 11.4 G2 · 特有技能萃取 + 三道门禁
- 萃取特质技能 aws_es_scaling_script_authoring（绑定运维 Leader）
- verify（沙箱 pass_rate≥0.7）+ evolve（version+1）+ publish
- 验收：三道门禁全过；验证产出脚本 fragments 含 5 项 criteria

### 11.5 G3 · 数字孪生双路径协作数据
- 派发最终计划 → sandbox session（自动运行 + 单步运行两条路径）
- 验收：两条路径都满足步数≥5 / agent_actions 非空 / messages 递增 / ≥3 agent / reward 曲线

### 11.6 G4 · Run A vs Run B 真实降本对比
- Run A（未注入特质技能）→ baseline_tokens_per_call
- 建 tokens_per_goal 目标（baseline×0.8，降 20%）
- 注入特质技能 → Run B → current_tokens_per_call
- 验收：current<target、status=achieved、cost_efficiency:{team} 棘轮锁定

### 11.7 G4 · 棘轮单调性复检
- 再跑一次更差 run（注入劣化技能或重跑 Run A）
- 验收：棘轮值不下降（复用 Phase 7 C5 口径）

### 11.8 主脚本编排与报告
- scripts/aws_ops_costdown_e2e.py 的 18 个 step
- 复用 e2e ApiClient/Runner；P0b 找不到 LLM 即 FAIL
- 报告：docs/reports/aws-ops-costdown-report.{md,json}，末行 COSTDOWN PASS/FAIL

### 11.9 离线单测（不依赖 LLM）
- test_aws_ops_costdown.py：模板结构、score_script、assertions
- 验收：pytest 全绿（CI 可跑）

### ✅ Phase 11 自检（汇总）
- 5 条断言链路（G1 结构 / G2 评分+门禁 / G3 协作 / G4 降本+棘轮）
- node scripts/check-docs-signoff.cjs --strict  # 0 FAIL
```

---

## 4. §4 与既有 Phase 的衔接关系

Phase 11 不重复造轮子，**复用** Phase 7/9/10 已打通的能力，只补「实证 case」这一层。

| 既有能力（已打通） | Phase 11 复用方式 | Phase 11 新增 |
|---|---|---|
| **Phase 7 C1~C6** 对账恒等式 | G4 的 token 对账沿用 C2（run 级一致）、C5（棘轮单调）口径 | Run A/Run B 对比框架 |
| **Phase 9.1** target_id 双向绑定 + CostTargetTracker 复测 | G4 创建目标时带 `metadata.target_id`，任务完成自动复测 | — |
| **Phase 9.2** tokens_per_goal 改「每调用 token」 | G4 目标 metric 直接用 `tokens_per_goal` | — |
| **Phase 9.6** 重复技能 merge | 若萃取的特质技能与现有重复，走 merge | — |
| **Phase 10.1** team_id 筛选透传 | G3/G4 的 token 查询带 `team_id=aws_ops` | — |
| **Phase 10.3** 存量目标 baseline 迁移 | G4 目标创建即用新口径，无需迁移 | — |
| **Phase 4** 沙箱 + token_scope 跨线程 | G3 sandbox session、G4 run 的 token 归因 | — |
| **aws_ops_e2e_test.py** ApiClient/Runner | import 复用 | 独立角色定义/评分/G4 |

**关键边界**：
- Phase 11 **不改** Phase 7/9/10 的任何已有代码（surgical changes）。
- Phase 11 **不依赖** Phase 10 的联机验收项（10.6/10.7/10.8）完成——它自己就是一条独立的实证链路。
- 若 G4 发现 token 对账或棘轮有 bug，**新开 buglog 条目**而不是改 Phase 11 设计（与 Phase 10 发现 bug-050 的处理方式一致）。

**⚠️ 已对照代码库修正的边界（2026-06-22）**：
- **既有云运维团队不可忽视**：`src/backend/agents/teams/` 下已存在 `cloud_ops_team.py`（`team_id=cloud-ops-team`，含 CloudFinOps/PlatformSRE/CCOE，frameworks 含 AWS Well-Architected/FinOps）与 `xops_team.py`（`create_xops_team`）。Phase 11 新建 `aws_ops_team.py` 前必须**先核查这两个团队**，二选一：
  - (A) **扩展既有**：若 `cloud-ops-team` 角色/技能已够用，直接给它补本 Phase 的 ES 缩放领域技能，不新建团队；
  - (B) **新建独立**：确需独立场景才建 `aws_ops_team`，且用一个**明确不冲突的 team_id**（如 `aws-ops`），与 `cloud-ops-team`/`xops-team` 区分。
  - 默认倾向 (B) 但 team_id 取 `aws-ops`；G1 断言里加一条「team_id 不与既有团队冲突」。
- **复用 `resolve_team_id` 防幻影团队**（bug-049）：脚本所有 `team_id` 入参先过 `trial_api.resolve_team_id`（已实现：连字符/下划线归一 + 必须匹配已存在团队，否则 400）。避免再次产生 `aws-ops` vs `aws_ops` 这类幻影团队。
- **工具必须是已注册 tool**：见 G1 修正——绑定前用 `GET /tools` 校验，杜绝绑 `auto_monitor`/`communication` 这类不存在的工具。

---

## 5. 验收总表（一张表看全 Phase 11）

| 契约 | 步骤 | 断言 | 依赖 LLM | 对应 todos 节 |
|---|---|---|---|---|
| G1 | ①角色对齐 | 6 agent × tools/skills 与模板一致 | 否（结构断言） | 11.1 |
| G2 | ②迭代修订 | 最终轮 score==5；三道门禁过；脚本 fragments 含 5 criteria | **是**（Plaza 讨论用 LLM） | 11.2~11.4 |
| G3 | ③孪生协作 | 双路径步数≥5/actions/messages/≥3 agent/reward | **是**（sandbox use_llm=true） | 11.5 |
| G4 | ④真实降本 | current<target（≥20%）、achieved、棘轮锁定+单调 | **是**（Run A/Run B 真实 token） | 11.6~11.7 |
| 离线 | 单测 | 模板结构/score_script/assertions 全绿 | 否 | 11.9 |

---

## 6. 未决事项（实施时再定，不阻塞 spec）

1. **Plaza「修订意见回灌」的具体 API**：是用 discussion 的 message 注入，还是新增一个 `revise-plan` 端点？倾向前者（surgical），实施时验证 `plaza_routes.py` 现有 message 端点是否够用。
2. **G2 verify 产出的「脚本 fragments」从哪取**：`skill_verifier` 沙箱跑校验脚本时的 stdout？还是 verify 时 LLM 生成的样本脚本？倾向前者（确定性），实施时读 `skill_verifier._run_sandbox_verification` 的返回结构。
3. **G4 Run A 的「未注入特质技能的 agent 组」**：是临时建一个影子团队，还是临时解绑 aws_ops 团队的特质技能？倾向后者（避免污染 team_store），实施时验证 `update_agent_skills` 的临时解绑+恢复能力。

以上 3 点均不影响 Phase 11 的整体形态，实施阶段在对应 todos 节里用伪代码落实即可。

---

## 7. 核查结论与修正记录（对照真实代码库，2026-06-22）

> 本节为「核查该 case 并修正」的结果：逐条把 spec 的代码假设对到真实仓库，✅ = 与代码一致可直接落地，⚠️ = 已修正。

### 7.1 ✅ 核实一致（可直接落地）
| spec 假设 | 核实结果 | 锚点 |
|---|---|---|
| `run_shell` 在默认工具池（§0.3/G1 绑定） | ✅ 存在，且是 core 工具 | `tool_registry.py:38`、core_names 集合 `:246` |
| `run_python` 存在 | ✅ | `tool_registry.py:36` |
| `src/backend/agents/teams/` 目录 + `create_*_team()` 工厂模式 | ✅ 已有 `ai_coding_team/build_team/cloud_ops_team/xops_team/energy_team` 均有工厂函数 | `teams/*.py` |
| `aws_ops_e2e_test.py` 提供 `ApiClient`/`Runner`/`step`/`bootstrap_auth`/`find_codebuddy_model`/`cleanup_legacy_aws_e2e_teams`/`pick_by_keywords` | ✅ 全部存在，§2.3 复用边界成立 | `scripts/aws_ops_e2e_test.py:66/122/137/168/185/254/358` |
| Phase 9.1/9.2/9.6/10.1、Phase 7 C2/C5 能力 | ✅ 已打通（本仓库 Phase 9/10 + 离线对账脚本可验证） | `cost_targets.py`/`cost_target_tracker.py`/`token_ledger.py`/`scripts/offline_reconcile_check.py` |

### 7.2 ⚠️ 已修正
1. **G1 工具绑定**：`communication` / `auto_monitor` / `compliance_region_guard`（作工具）**均未注册** → 已替换为真实工具（`delegate_task`/`read_file`/`set_alarm`/`watch_file`/`search_files`/`run_python`）；`compliance_region_guard` 仅作技能。G1 断言增「tool_id 必须在 `GET /tools` 中可查」。
   - 已注册工具实清单（节选）：`run_shell, run_python, read_file, write_file, search_files, list_directory, delegate_task, send_message, broadcast, publish_event, watch_file, set_alarm, schedule_task, cron_trigger, skill_list/view/manage, memory_read/save, web_search, …`（见 `tool_registry.py`）。
2. **既有云运维团队**：`cloud_ops_team.py`(`cloud-ops-team`) 与 `xops_team.py` 已存在且覆盖 AWS/FinOps 域 → §4 增「先核查、二选一(扩展/独立)、team_id 取 `aws-ops` 防冲突」。
3. **防幻影团队**：所有 team_id 入参须过 `resolve_team_id`（bug-049 已实现）→ 写入 §4 边界。

### 7.3 已补核（本次一并核实）
| §6 未决/依赖 | 核实结果 | 锚点 |
|---|---|---|
| skill verify/evolve/publish 三道门禁路由（G2/§6.2） | ✅ 全部存在：`/skill-library/verify`、`/evolve`、`/apply-evolution`、`/publish` | `api.py:8184/8164/8174/8194` |
| 临时解绑/恢复 agent 技能做 Run A 对照组（G4/§6.3） | ✅ 存在 `PUT /teams/{team_id}/agents/{agent_id}/skills`（`update_agent_skills`），可临时改技能后恢复 | `api.py:830/833` |
| 「脚本 fragments」取数口径（§6.2） | ⚠️ 仍需读 `skill_verifier._run_sandbox_verification` 返回结构确认 stdout 字段 | `skill_verifier.py` |

### 7.4 唯一仍需现场确认的开放项
- **Plaza「修订意见回灌」机制**（§6.1）：`plaza_routes.py` 未见明确的「向已有 discussion 追加修订 message/再起一轮」端点（讨论创建带 `max_rounds`，消息在 `disc.messages`）。落地前需确认：是**复用现有 discussion 的多轮机制**（在同一 discussion 内继续轮次），还是**每轮新建 discussion 把 missing[] 作为新输入**。倾向后者（每轮独立、轨迹清晰、不依赖未确认端点）。

> **核查结论**：spec 主体设计**与代码库一致、可落地**。实锤错误两处（G1 工具绑定、既有团队复用/防冲突）已就地改正；§6 三个未决项中两个（skill 三门禁、agent 技能临时改）已确认有真实路由可用，只剩「Plaza 修订回灌机制」一个开放项需在写 todos 时定方案。可据此把 Phase 11 写进 `docs/全局重构todos.md`。
