<!-- docs-signoff: author="GitHub Copilot" kind="llm" doc="plan" ts="2026-06-22T02:46:05Z" -->

# 全局重构 PLAN — 以「Token 最少」为北极星的 Agent 团队效率系统

> 一句话目标：**让 Agent 团队在达成业务场景目标的前提下，消耗的 Token 最少。**
> 「成本」= LLM Token（技能形成 / 技能验证 / 数字孪生演练 / 议事辩论 / 任务执行），**不是** Terraform/EC2 基础设施账单。
> Token 由 **进程内 Token 探针（Cost Gate Probe）** 按 `run_id` 归因采集（编排层 `chat_harness.chat` 处插桩）；技能验证 / 演练在**本地 Lite/Docker 沙箱**跑确定性校验脚本。技能属于 Agent、Agent 属于团队，Token 成本一路归因到团队。
> **本方案不采用 K8s**：本机零基建即可闭环；沙箱隔离用现成的 Lite（默认）/Docker，不引入 Pod 调度。

配套：[全局重构todos.md](全局重构todos.md)（事无巨细 + 伪代码勾选项）。

---

## 0. 为什么这样设计（把四个模块串成一条 Token 因果链）

```
议事广场(讨论) → 萃取 Skill → 【本地沙箱跑校验脚本 + 进程内 Token 探针】验证技能是否真有效、路由是否合适
                                   │
                                   ▼ 技能归属 Agent、Agent 归属 Team
数字孪生(演练) → 【进程内 Token 探针 + 本地模拟】在分支结构 / 故障场景下检验团队协作鲁棒性
                                   │
                                   ▼ 所有 Token 进入统一 TokenLedger（按 phase/skill/agent/team 归因）
演进式成本优化页 → 设定 Token 节流目标（在 Skill 省 or 在协作省）→ 创建任务/话题正向推动 → 棘轮锁定
```

- **智能体团队的效率必须用 Token 衡量**：没有 Token 归因，就无法判断一个团队/技能是不是「高效」。
- **技能必须被验证**：萃取出的 Skill 要保证有效、可被正确路由；验证在**本地 Lite/Docker 沙箱**跑确定性校验脚本，验证用的 LLM 调用发生在编排层、由进程内探针按 `run_id` 计量；探针看的是「验证这个技能花了多少 Token」。
- **数字孪生是模拟尝试空间**：用不同分支结构 + 故障场景压测团队协作鲁棒性；演练决策的 LLM 调用同样由进程内探针采集 Token。
- **成本页是方向盘**：设定 Token 优化目标，正向推动整体 Token 下降，并锁定成果。

---

## 1. 现状诊断（基于代码事实，非推测）

| 子系统 | 现状 | 文件 | 与北极星是否一致 |
|--------|------|------|------------------|
| Cost Gate | **评估 Terraform plan 资源**（实例族/存储层/AWS 区域/RI/孤儿资源），与 Token 完全无关 | `src/backend/agents/cost_policy.py`、`src/backend/channels/cost_gate.py`、`src/backend/agents/cost_gate_routes.py`、`src/backend/ci_cost_gate.py` | ❌ 背道而驰 |
| 成本看板数据 | 只读 **OpenCost K8s 基础设施成本**；本机无 OpenCost → 全空 | `src/backend/agents/cost_aggregator.py`、`cost_routes.py` | ❌ 展示的不是 Token |
| Token 账本（已存在但断链） | 每次 LLM 调用后 `budget_guard.record_usage()` 写入 `storage/usage.db`（input/output/total tokens + cost_usd，按 session/agent/team/model） | `src/backend/agents/chat_harness.py`、`src/backend/agents/budget/store.py` | ✅ 数据在，但**页面没用它** |
| 演练 Token | 孪生 trial 的 skill 用量写入 `storage/twin_trials/*_skill_usage.jsonl` | `src/backend/sandbox/proficiency_store.py` | ✅ 局部有，未统一 |
| 可持续性 | 已把 tokens_consumed → token_efficiency(score/1k) → grade | `src/backend/agents/sustainability.py` | ✅ 最接近目标，应上位为核心 |
| 技能验证 | 在 **Docker/Lite 本地沙箱** 跑结构性校验；**不计 Token** | `src/backend/agents/skill_verifier.py`、`src/backend/sandbox/python_runner*.py` | ⚠️ 无 Token 探针（沙箱本身够用，复用即可） |
| 数字孪生演练 | 纯 Python in-memory asyncio 模拟；chaos 是状态突变；**不计 Token** | `src/backend/sandbox/twin_loop.py`、`scenario_*.py`、`agents/chaos_engine.py` | ⚠️ 无 Token 探针 |
| ratchet | `cost_efficiency:{team_id}` 等指标只进不退 | `src/backend/agents/ratchet_ledger.py` | ✅ 可复用 |

**核心结论**：Token 数据**已经在 `usage.db` 里产生**，但①成本页读的是 OpenCost 基础设施成本而非 Token；②Cost Gate 在评估 Terraform 而非 Token；③技能验证 / 演练没有 Token 探针把「这次验证/演练花了多少 token」记账并归因。重构就是把这三条断链接上——**沙箱沿用现成的 Lite/Docker，不引入 K8s**。

### 1.1 二次诊断（P1~P7 落地后，页面仍未闭环 — 探针无恙，断点在数据处理 / 前端绑定 / 棘轮断链）

P1~P7 已把探针、TokenLedger、Gate、目标、报告、Demo 对账写完（`token_context.py`/`token_ledger.py`/`token_policy.py`/`cost_targets.py`/`cost_report.py` 均在）。但「演进式成本优化页」仍是半成品，用户可见五处问题，**根因均非探针**（`select phase,count(*),sum(total_tokens) from usage_log group by phase` 有非空输出即证明探针正常）：

| 页面现象 | 根因 | 性质 |
|---------|------|------|
| 成本构成 Top10 空白 | `refreshDashboard()` 仍调 OpenCost 的 `/cost/by-{agg}`，token 数据躺在 `state.tokenOverview` 没绑定 | 前端数据源绑定 |
| 成本趋势空白 | `/cost/trends` 只走 OpenCost；`TokenLedger` 无时间分桶方法 | 缺聚合 |
| 成本明细空白 | `/cost/pods` 是 OpenCost pods；无「按 run/调用」的 Token 明细端点 | 缺聚合 |
| 效率视角像摆设 | `/sustainability/group` 能跑，但效率公式 / 数据来源 / 两杠杆拆分在 UI 上无解释；无演练分时 efficiency=0 看着像空 | 数据处理 + 缺解释 |
| 棘轮菜单点了不推进 | 成本页复用 `system-evolution.js::runCycleOnRatchet`（通用演进周期），与 `cost_efficiency:{team}` token 棘轮**完全无关**；`ledger.json` 至今无 `cost_efficiency:*` | **棘轮断链** |
| Skill / 协作两块成本无统一目标演进 | `by_phase` 五段未归并为「Skill 杠杆 / 协作杠杆」；`get_progress` 对 `score_per_1k` 用「总 token」当 current（方向反）；目标→派发→复测→锁定环未接 | 数据建模 + 数据处理 |

→ 这些在新增的 **Phase 8** 收口（详见 todos）。原则：**不碰探针**，只做正确聚合、正确绑定、并在成本页接出 `cost_efficiency` 棘轮触发入口。

---

## 2. 目标架构（四层）

### L1 · 统一 Token 账本 TokenLedger（单一事实源）
在现有 `budget/store.py`（usage.db）之上，增加**归因上下文**，让任意一次 LLM 调用都能落到 (phase, skill_id, agent_id, team_id, scenario_id, run_id)。

```
TokenEvent {
  run_id, ts,
  phase: "skill_verify" | "drill" | "plaza" | "task" | "extract",
  team_id, agent_id, skill_id?, scenario_id?,
  input_tokens, output_tokens, total_tokens, model,
  goal_achieved: bool?, score: float?      # 用于 efficiency = score / (tokens/1k)
}
```

聚合查询（供成本页 / Gate / sustainability 共用）：
```
tokens_by_team(window) -> [{team_id, total_tokens, score, efficiency}]
tokens_by_skill(window) -> [{skill_id, team_id, total_tokens, calls, efficiency}]
tokens_by_phase(window) -> {skill_verify, drill, plaza, task, extract}
run_tokens(run_id) -> {input,output,total, by_phase}
```

### L2 · Token 探针（进程内 run_id 归因）+ 本地沙箱（现成 Lite/Docker）
**关键认知（已代码核实）**：技能验证/演练的 LLM 调用发生在**后端编排层**（`chat_harness.chat`，如 `skill_verifier._generate_tests`/场景评估/演练决策），**不在沙箱子进程内**——沙箱里只跑确定性校验脚本（零 LLM 调用）。因此：

- **Token 探针 = 进程内 run_id 归因层**：用 `contextvars` 包裹编排层的 `chat_harness.chat` → token 照常落 `usage.db`，但带上 `run_id`/`phase`/`skill_id` → 按 run_id 聚合即得本次验证/演练的真实 Token。**不是拦截沙箱出站流量的 sidecar**（沙箱内无 LLM 流量可拦）。
- **本地沙箱 = 确定性校验脚本的执行底座**：直接复用现有 `LiteSandbox`（默认）/`DockerSandbox`，提供隔离/可复现，**不参与 Token 采集**，**不新增 K8s**。

**进程内探针与沙箱形态完全解耦**：换不换沙箱、有没有容器，Token 计量都照常工作，本机零基建即可闭环。

### L3 · Cost Gate 重构为 TokenBudgetGate（评估 run 的 Token 经济性，而非 Terraform）
把「评估 Terraform 资源」替换为「评估一次 run 的 Token 经济性」：

```
TokenViolationType:
  TOKEN_OVER_BUDGET        # 本次 run token 超预算
  LOW_TOKEN_EFFICIENCY     # score/1k 低于阈值（产出太贵）
  REDUNDANT_LLM_CALLS      # 同一意图重复 LLM 调用，可萃取为 skill
  SKILL_ROUTING_MISS       # 已有可复用 skill 却走了原始 LLM（路由没命中）
  DRILL_TOKEN_BURST        # 演练 token 速率突增（鲁棒性差/抖动）

Gate 决策: PASS | WARN | BLOCK
作为「探针」用途：
  - 技能 verified → granted 之前，Gate 评估验证 token 经济性，不达标则 WARN/BLOCK
  - 演练 passed → ratchet-lock 之前，Gate 评估演练 token 经济性
```

保留旧 Terraform gate 为 **legacy 兼容**（`/api/v1/cost-gate/terraform/*`），但默认页面与闭环改用 TokenBudgetGate（`/api/v1/cost-gate/token/*`）。

### L4 · 演进式成本优化页（方向盘）
- **数据源切换/叠加**：默认展示 **TokenLedger**（团队/技能/阶段的 token 与 efficiency），OpenCost 基础设施成本降为可选附属。本机无 OpenCost 也有数据。
- **设定 Token 优化目标**：选择 (团队/技能) + 指标(`tokens_per_goal` 或 `score_per_1k`) + 目标值 + 杠杆(`skill_extraction` | `collaboration_routing`)。
- **正向推动**：用现有「创建优化任务 / 创建 Plaza 话题」把目标派发出去；TokenBudgetGate 自检；棘轮锁定达成的节省。
- **页面五菜单的数据源必须全部是 TokenLedger**（Phase 8）：成本构成 = `breakdown(dim)`、成本趋势 = `trend(bucket)`、成本明细 = `recent_runs/recent_calls`、效率视角 = `sustainability + lever_split`、棘轮 = `cost_efficiency:*`。任何一个还连着 OpenCost 都算未闭环。

### L5 · 两根节流杠杆，一个统一目标（Skill 杠杆 × 协作杠杆）

北极星只有一个标量目标：**最大化 `score / 1k tokens`**。但可拉的杠杆有两根，二者在「成本构成」里按 `phase` 归并、在「效率视角」里并排展示、在「优化目标」里收敛到同一个效率指标：

```
统一目标:  maximize  token_efficiency = Σscore / (Σtokens / 1000)
                                   ▲
        ┌──────────────────────────┴──────────────────────────┐
   ① Skill 杠杆 (skill_extraction)              ② 协作杠杆 (collaboration_routing)
   成本 = phase ∈ {extract, skill_verify}        成本 = phase ∈ {plaza, drill, task}
   省法 = 把重复 LLM 萃取为已验证可路由 skill      省法 = 优化 Agent 路由 / 减少无效往返
   信号 = REDUNDANT_LLM_CALLS / SKILL_ROUTING_MISS  信号 = DRILL_TOKEN_BURST / 低效协作
```

闭环：成本页选杠杆 → 设目标（baseline 自动取实测）→ 创建任务/话题派发并附带「该拉哪根杠杆」建议 → 执行后复测 `current` → 达标则 **`cost_efficiency:{team}` 棘轮只进不退锁定**。两根杠杆任何一根把单位 token 产出做高，都推进同一条棘轮——这就是「统一目标的演进过程」。

---

## 3. 关键 API（重构后）

```
# Token 账本
GET  /api/v1/cost/tokens/summary?window=&group_by=team|skill|phase
GET  /api/v1/cost/tokens/by-team
GET  /api/v1/cost/tokens/by-skill
GET  /api/v1/cost/tokens/run/{run_id}

# Token 预算门（探针）
POST /api/v1/cost-gate/token/evaluate     # body: {run_id|inline tokens, budget, context}
GET  /api/v1/cost-gate/token/stats
# legacy 保留
POST /api/v1/cost-gate/terraform/evaluate

# 优化目标
POST /api/v1/cost/targets                 # 设定 token 优化目标
GET  /api/v1/cost/targets
GET  /api/v1/cost/targets/{id}/progress
```

> 注：验证/演练的 run_id 由各自入口（`skill_verifier.verify_skill`、`orchestrator.run_full_pipeline`）内部用 `token_scope` 直接生成并归因，**不单建** `/sandbox/runs` 统一入口（去 K8s 后无需额外编排层；查 run 用现成的 `/cost/tokens/run/{run_id}`）。

---

## 4. 分阶段路线图（每阶段独立可交付、可回退）

- **Phase 0 · README & 文档**（本次）：北极星写入 README；产出本 plan + todos。
- **Phase 1 · TokenLedger + 进程内 Token 探针（最高 ROI、零新基建）**：给 `record_usage` 增加归因上下文（contextvar run_id/phase/skill_id）；新增 `token_context.py` 进程内归因 + `token_ledger.py` 聚合 + `/api/v1/cost/tokens/*`；成本页改读 token 数据。**做完这步，本机无 OpenCost 也能看到按 run/skill/team 归因的真实 Token 成本。**
- **Phase 2 · TokenBudgetGate**：新增 `token_policy.py` + `/api/v1/cost-gate/token/*`；页面「Cost Gate 自检」「治理目标」改用 token 语义；Terraform gate 降级为 legacy。
- **Phase 4 · 验证/演练 Token 归因闭环**：技能验证、孪生演练全程记 token 并归因到 skill→agent→team（在现有 Lite/Docker 沙箱上跑确定性校验）；sustainability/ratchet 接入真实数据。**含关键修复**：`orchestrator._llm_decision_wrapper` 用 `contextvars.copy_context()` 跨 ThreadPoolExecutor 线程透传 token_scope。
- **Phase 5 · 优化目标驱动**：成本页设定 token 目标 + 杠杆，派发任务/话题，进度追踪 + 棘轮锁定。
- **Phase 6 · 清理与收口**：移除/隔离与 token 无关的 Terraform 成本逻辑在主路径上的暴露；统一命名（成本=Token）。
- **Phase 7 · Demo Case 端到端数值核对**：用一条可复现链路证明归因正确、与页面/报告逐项对应、能再节省（C1~C6 恒等式 assert）。
- **Phase 8 · 演进式成本优化闭环收口（本轮重点）**：在 P1~P7 骨架之上，把页面五菜单全部切到 TokenLedger（成本构成 / 趋势 / 明细 / 效率视角），并**接通 `cost_efficiency` 棘轮触发入口**与**两杠杆统一目标闭环**（含 `get_progress` 方向修复、报告对账 team 口径修复）。详见 todos Phase 8。
- **Phase 8.R · 复查补丁**：对 codebuddy 已落地的 Phase 8 代码逐文件复查，修掉 9 处「半接线」缺陷（baseline 量纲、`tokenByTeam`/`governanceTarget` 未赋值、`renderGovernance` 残留 OpenCost 字段、8.4 两杠杆、派发杠杆、达成自动锁棘轮、锁节点 held 误亮、`lever_split` 口径、趋势分桶）。详见 todos Phase 8.R。
- **Phase 9 · 闭环审计与「后半环」接通（已完成）**：把「派发 → 真正降 token → 回流到目标/KPI」接上：9.1 派发任务↔目标双向绑定 + `CostTargetTracker` 任务完成复测；9.2 `tokens_per_goal` 改「每调用 token」(解「目标永远 0%」)；9.3 KPI④改棘轮累计 + advance 后刷新；9.4 drill 回灌；9.6 重复技能 `duplicates`/`merge` 路由 + 一键合并；9.7 KPI 跳过未归因；9.8 score 来源说明；9.5 复用 `enterCostGov` 桥。详见 todos Phase 9。
- **Phase 9.x · 真实使用 bug 修复（已完成，见 `.wolf/buglog.json` bug-034~049）**：测试连接留空回退已存密钥 + 浏览器「记住密钥」；`RatchetAnimator` window 导出（棘轮按钮静默无反应）；任务/对话 Token 归因到团队（`chat(team_id=...)`）；**孪生 drill reward 恒 0 根因 = `create_trial` 未 `sync_agents_from_team` → 0 twin**（已修）；团队 `?team=` 自动选中；SSE 步进补连；流水线阶段推进；3D 奖励浮卡（投射到对应 agent）；房间仿真停止控制；KPI 团队筛选 + 名称；外链 Google Fonts 移除（离线超时）；**`team_id` 规范化校验（防幻影团队，如 build-system）** + 幻影团队数据清理。
- **Phase 10 · 收尾、硬化与未竟事项（待办）**：筛选透传到构成/趋势/明细、历史未归因回填/标注、`tokens_per_goal` 存量目标 baseline 迁移、score 来源扩展、目标进度实时回流、3D 可视化与合并/Demo 联机验收、回归脚本补新端点、历史 team_id 归一、`trial_api` 多行 f-string 3.11 兼容。详见 todos Phase 10。
- **Phase 11 · AWS 运维降本增效最佳实践 Case（待实施）**：用一条可复现链路实证「角色对齐(G1) → 迭代萃取特有技能(G2) → 孪生协作(G3) → 真实降本锁棘轮(G4)」，每步脚本可断言；AWS 为业务域、度量仍是 Token。设计与代码核查见 `docs/superpowers/specs/2026-06-22-phase11-aws-costdown-best-practice-design.md`（§7 已对照代码修正：工具绑定用真实 tool、与既有 cloud-ops/xops 团队防冲突、过 `resolve_team_id`）。详见 todos Phase 11。
- **全局模型 override（已实现）**：模型池每行「设为全局」→ `ChatHarness._global_override` 压过 per-agent/per-team/default；plaza 讨论 / 技能演进 / 棘轮 / 数字孪生 等所有走 harness 的 LLM 调用统一使用该模型。路由 `GET/POST/DELETE /api/v1/agent-config/llm/global-model`，持久化到 `settings.json.global_model`，启动自动加载。

> 依赖顺序：P1 →（P2 ∥ P4）→ P5 → P6 → P7 → **P8 → P8.R → P9** →（P9.x bug 修复贯穿）→ **P10 收尾**。**本方案不采用 K8s**（原 Phase 3 已移除）；沙箱隔离沿用现有 Lite（默认）/Docker。
>
> **当前状态（2026-06-20）**：北极星闭环主干**已端到端打通并经真实使用验证**（设目标→派发带 target_id→任务完成复测→达标自动锁棘轮→KPI/报告可见；孪生 drill 产出真实 reward/评分喂效率与棘轮）。剩余为 P10 的硬化与联机验收项。

---

## 5. 代码评审：需补充 / 修改清单（按文件）

**新增**
- `src/backend/agents/token_ledger.py`：TokenLedger 归因聚合（封装 usage.db + proficiency_store + scenario tokens）。
- `src/backend/agents/token_policy.py`：TokenViolationType / TokenBudgetEngine（替代 cost_policy 的 token 版）。
- `src/backend/agents/token_gate_routes.py`：`/api/v1/cost-gate/token/*`。
- `src/backend/agents/token_context.py`：`contextvars` 实现 `token_scope(run_id, phase, skill_id, ...)`——这就是「进程内 Token 探针」的插桩端；读出端复用 `TokenLedger.run(run_id)`，**不单独建 token_probe.py**（避免与 ledger 重复）。属 P1。
- `src/backend/agents/cost_targets.py` + 路由：Token 优化目标存储与进度。

> **不新增** `k8s_runner.py`（本方案不采用 K8s）；沙箱沿用现有 `python_runner_lite.py`/`python_runner_docker.py`。

**修改**
- `src/backend/agents/chat_harness.py`：`record_usage` 调用处补 `phase/skill_id/scenario_id/run_id`（从 contextvar 透传）。
- `src/backend/agents/budget/store.py`：usage_log 增列（phase, skill_id, scenario_id, run_id），加聚合查询。
- `src/backend/agents/cost_routes.py`：新增 `/cost/tokens/*`；`/cost/summary` 增加 `source=token|infra` 切换。
- `src/backend/agents/skill_verifier.py`：用 `get_sandbox()`（现有 Lite/Docker）；包一层 run_id；把验证 LLM token 计入 Ledger；verified→granted 前调 TokenBudgetGate。
- `src/backend/sandbox/orchestrator.py` / `twin_loop.py`：演练包 run_id；接探针；passed→lock 前调 TokenBudgetGate；**`_llm_decision_wrapper` 用 `contextvars.copy_context()` 跨线程透传 token_scope**。
- `src/backend/agents/sustainability.py`：tokens_consumed 数据源切到 TokenLedger（真实）。
- `src/backend/agents/cost_gate_routes.py`：Terraform 路由迁到 `/terraform/*`，根路径转 token。
- 前端 `src/frontend/cost-dashboard.html` + `js/cost-dashboard.js`：默认渲染 token 数据；治理目标/自检改 token 语义；新增「设定 Token 优化目标」表单。

**保留/兼容**：`ci_cost_gate.py`、`cost_policy.py` 标注 legacy；不删，避免破坏既有 CI 引用。

**Phase 8 增补（页面闭环，不碰探针）**
- `token_ledger.py`：新增 `breakdown(window,dim)`、`trend(window,bucket,dim,key)`、`recent_runs/recent_calls`、`lever_split(team_id,window)`、`SKILL_LEVER_PHASES/COLLAB_LEVER_PHASES` 常量；给 `by_phase` 加可选 `team_id` 形参。
- `cost_routes.py`：新增 `/cost/tokens/breakdown`、`/cost/tokens/trend`、`/cost/tokens/detail`、`/cost/tokens/ratchet`、`POST /cost/tokens/ratchet/advance`（封装 `ratchet_ledger.advance`，与 `orchestrator._push_drill_ratchet` 同口径）。
- `cost_targets.py`：修复 `get_progress` 按 `metric` 区分方向（`tokens_per_goal` 越低越好 / `score_per_1k` 越高越好，current 取实测效率），达标自动 `status=achieved`。
- `cost_report.py`：`team` 过滤时 `by_phase` 同口径过滤，修 `reconciliation.consistent` 误报；报告补杠杆维度。
- `sustainability_routes.py`：`/sustainability/group` 每个 team 补 `lever_cost` 与 `efficiency_formula`。
- 前端 `cost-dashboard.html` + `js/cost-dashboard.js`：五菜单数据源切 Token；`renderBreakdown/renderTrends` 改 token 字段；Pod 明细改 Token 消耗明细；效率视角加公式 tooltip + 两杠杆条；**覆盖 `runCycleOnRatchet`/`loadRatchetStatus` 为 token 棘轮语义**（调 `/cost/tokens/ratchet*`），不再借用 `system-evolution.js`。

---

## 6. 风险与回退
- **不采用 K8s**：沙箱隔离用现有 Lite（默认）/Docker；进程内探针始终工作，本机零基建闭环可跑。若未来需要更强隔离，`get_sandbox` 预留 docker 分支，不影响 Token 归因。
- **usage.db schema 变更**：新增列用 `ALTER TABLE ... ADD COLUMN`（SQLite 兼容旧库），旧行字段置空不报错。
- **行为兼容**：Terraform gate 不删，迁到 `/terraform/*`；旧 CI 调用保持可用。
- **每阶段可回退**：P1~P5 各自独立分支/提交，前端通过 `source` 开关灰度。

## 7. 验收标准（可验证）
- A1：本机无 OpenCost 时，成本页仍显示真实 **Token** 成本（来自 usage.db），不再弹「无成本数据」红条。
- A2：`/api/v1/cost/tokens/by-team` 返回非空且与 usage.db 一致（脚本核对）。
- A3：技能验证产生的 token 能在 `/cost/tokens/run/{run_id}` 查到，并归因到 skill→agent→team。
- A4：TokenBudgetGate 对一个「高 token 低 score」run 给出 WARN/BLOCK。
- A5：孪生演练 token 在子线程正确归因（`by_phase.drill > 0`，验证 `contextvars.copy_context()` 跨线程修复生效）。
- A6：在成本页设定一个团队的 token 目标 → 创建任务 → 进度可见；达成后棘轮新增一条 `cost_efficiency:{team_id}` 记录。

### 7.1 Phase 8 验收（页面闭环可用，与 todos Phase 8 自检对齐）
- A9：成本构成 / 成本趋势 / 成本明细三菜单数据源均为 TokenLedger，本机无 OpenCost 也非空（`/cost/tokens/breakdown|trend|detail` 均返回非空）。
- A10：效率视角每行显示效率公式（`score ÷ tokens/1k`）+ Skill/协作两杠杆 token 占比；`token_only` 团队显示中性提示而非空白。
- A11：成本页点「运行棘轮周期」→ `POST /cost/tokens/ratchet/advance` 真实推进 → `storage/ratchet/ledger.json` 出现 `cost_efficiency:{team}`；无演练分时返回 `no_efficiency` 并给出可解释提示。
- A12：`score_per_1k` 目标的 `progress` 随实测效率上升而从 0 推进至 1（修复方向 BUG）；达标自动 `status=achieved`。
- A13：`/cost/report?window=&team=` 加 team 过滤后 `reconciliation.consistent=true`（同口径）。

### 7.2 Phase 8.R 复查补丁验收（修完 9 缺陷才算闭环，与 todos Phase 8.R 自检对齐）
- A14：`score_per_1k` 目标的 `baseline` 为效率量纲（≈0.x）而非数千 token，Run B 提分后 `progress` 单调升至 1（8R.1）。
- A15：`window.CostDashboard.state.tokenByTeam` 非空；棘轮推进 `metric_key` 为当前 Top/选中团队而非恒为 `cost_efficiency:default`（8R.2）。
- A16：治理面板「当前治理目标」显示真实团队 + token 数；派发任务/话题正文含「该拉哪根杠杆 + 当前占比 + 预期哪段 token 下降」（8R.3 / 8R.5）。
- A17：`/sustainability/group` 每 team 含 `lever_cost`，效率视角每行显示效率公式 tooltip + Skill/协作双色杠杆条；`token_only` 团队中性提示不空白（8R.4）。
- A18：`lever_split.grand_total == LEDGER.summary(window).total`（同口径），萃取段 token 能归因到团队（8R.8）；目标达成自动推进 `cost_efficiency:{team}` 棘轮（8R.6）。

### 7.3 Phase 9 验收（后半环接通，已完成）
- A19：派发优化任务携带 `target_id`；任务 `TASK_COMPLETED` 由 `CostTargetTracker` 自动复测目标进度（达标自动推棘轮）。
- A20：`tokens_per_goal` 的 current = 平均每调用 token（`total/calls`），目标不再恒 0%（实测 build_system 1426/调用）。
- A21：KPI 第④卡显示「棘轮已锁定 N 项 / 最高 gen」，advance 成功后自动刷新。
- A22：萃取页 `?focus=redundant` 列出重复技能对并可「合并」（`POST /skill-library/merge`），技能数减少。

### 7.4 Phase 9.x 真实使用验收（已完成）
- A23：编辑模型留空 + 测试连接 → 回退已存/浏览器记住的密钥成功；棘轮按钮可点（`window.RatchetAnimator` 已导出）。
- A24：孪生 drill 产出**非零 reward / 综合评分**（`create_trial` 已 `sync_agents_from_team`，team 经 `?team=` 自动选中）；房间仿真可「⏹ 停止」。
- A25：成本页 KPI 随团队筛选缩放并显示团队名；离线无 Google Fonts 超时。
- A26：`POST /twin-trials`（及 `/twin-evolution/runs`）对未知 team_id 返回 400；`build-system`→`build_system` 自动归一（防幻影团队）。

### 7.5 Phase 10 验收（待办，见 todos Phase 10）
- A27：构成/趋势/明细随团队筛选缩放（`team_id` 透传）。
- A28：`tokens_per_goal` 存量目标 baseline 迁移后 progress 合理；历史「未归因」token 不再主导排名。
- A29：3D 议事厅显示 agent、奖励浮卡投射到对应 agent、流水线随步进推进、停止可用（联机目检）；Phase 7 Demo C1~C6 实跑全绿；回归脚本覆盖新端点全绿。
