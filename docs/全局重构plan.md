<!-- docs-signoff: author="GitHub Copilot" kind="llm" doc="plan" ts="2026-06-18T23:45:39Z" -->

# 全局重构 PLAN — 以「Token 最少」为北极星的 Agent 团队效率系统

> 一句话目标：**让 Agent 团队在达成业务场景目标的前提下，消耗的 Token 最少。**
> 「成本」= LLM Token（技能形成 / 技能验证 / 数字孪生演练 / 议事辩论 / 任务执行），**不是** Terraform/EC2 基础设施账单。
> 度量与验证发生在 **K8s Pod 沙箱** 里，由 **Token 探针（Cost Gate Probe）** 采集；技能属于 Agent、Agent 属于团队，Token 成本一路归因到团队。

配套：[全局重构todos.md](全局重构todos.md)（事无巨细 + 伪代码勾选项）。

---

## 0. 为什么这样设计（把四个模块串成一条 Token 因果链）

```
议事广场(讨论) → 萃取 Skill → 【K8s Pod 沙箱 + Token 探针】验证技能是否真有效、路由是否合适
                                   │
                                   ▼ 技能归属 Agent、Agent 归属 Team
数字孪生(演练) → 【K8s Pod 沙箱 + Token 探针】在分支结构 / 故障场景下检验团队协作鲁棒性
                                   │
                                   ▼ 所有 Token 进入统一 TokenLedger（按 phase/skill/agent/team 归因）
演进式成本优化页 → 设定 Token 节流目标（在 Skill 省 or 在协作省）→ 创建任务/话题正向推动 → 棘轮锁定
```

- **智能体团队的效率必须用 Token 衡量**：没有 Token 归因，就无法判断一个团队/技能是不是「高效」。
- **技能必须被验证**：萃取出的 Skill 要保证有效、可被正确路由；验证需要一个**隔离、可计量 Token** 的环境 = K8s Pod 沙箱；探针看的是「验证这个技能花了多少 Token」。
- **数字孪生是模拟尝试空间**：用不同分支结构 + 故障场景压测团队协作鲁棒性；同样跑在 K8s Pod 沙箱里，用探针采集演练 Token。
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
| 技能验证 | 在 **Docker/Lite 本地沙箱** 跑结构性校验；**不计 Token**；无 K8s Pod | `src/backend/agents/skill_verifier.py`、`src/backend/sandbox/python_runner*.py` | ⚠️ 非 K8s、无 Token 探针 |
| 数字孪生演练 | 纯 Python in-memory asyncio 模拟；chaos 是状态突变；**不计 Token**；无 Pod | `src/backend/sandbox/twin_loop.py`、`scenario_*.py`、`agents/chaos_engine.py` | ⚠️ 非 K8s、无 Token 探针 |
| K8s | 只有 **MutatingAdmissionWebhook 注入成本标签**，不创建/运行 Pod | `src/backend/agents/k8s_webhook_handler.py`、`k8s/*.yaml` | ⚠️ 无 Pod 沙箱调度 |
| ratchet | `cost_efficiency:{team_id}` 等指标只进不退 | `src/backend/agents/ratchet_ledger.py` | ✅ 可复用 |

**核心结论**：Token 数据**已经在 `usage.db` 里产生**，但①成本页读的是 OpenCost 基础设施成本而非 Token；②Cost Gate 在评估 Terraform 而非 Token；③技能验证 / 演练既没跑在 K8s Pod 沙箱，也没有 Token 探针把「这次验证/演练花了多少 token」记账并归因。重构就是把这三条断链接上。

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

### L2 · Token 探针（进程内 run_id 归因）+ Pod 沙箱（可选隔离底座）
**关键认知（已代码核实）**：技能验证/演练的 LLM 调用发生在**后端编排层**（`chat_harness.chat`，如 `skill_verifier._generate_tests`/场景评估/演练决策），**不在沙箱 Pod 内**——Pod 里只跑确定性校验脚本（零 LLM 调用）。因此：

- **Token 探针 = 进程内 run_id 归因层**：用 `contextvars` 包裹编排层的 `chat_harness.chat` → token 照常落 `usage.db`，但带上 `run_id`/`phase`/`skill_id` → 按 run_id 聚合即得本次验证/演练的真实 Token。**不是拦截 Pod 出站流量的 sidecar**（Pod 内无 LLM 流量可拦）。
- **Pod 沙箱 = 确定性校验脚本的隔离升级**（与 `DockerSandbox`/`LiteSandbox` 平行的 `KubernetesSandbox`，`batch/v1.Job` 短生命周期 Pod）。它给隔离/可复现，**不参与 Token 采集**。可选打 OpenCost 标签做基础设施成本归因，但北极星的 Token 成本与 Pod 是否存在无关。

降级策略：`mode=k8s|docker|lite`，K8s 不可用回退 docker/lite；**进程内探针始终工作**，保证本机零基建即可计量 Token。

### L3 · Cost Gate 重构为 TokenBudgetGate（K8s 探针语义，而非 Terraform）
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

# K8s 沙箱（验证/演练统一入口，内部可降级）
POST /api/v1/sandbox/runs                 # {kind: skill_verify|drill, payload} -> run_id
GET  /api/v1/sandbox/runs/{run_id}        # 状态 + token 探针结果
```

---

## 4. 分阶段路线图（每阶段独立可交付、可回退）

- **Phase 0 · README & 文档**（本次）：北极星写入 README；产出本 plan + todos。
- **Phase 1 · TokenLedger + 进程内 Token 探针（最高 ROI、零新基建）**：给 `record_usage` 增加归因上下文（contextvar run_id/phase/skill_id）；新增 `token_probe.py` 进程内归因 + `/api/v1/cost/tokens/*`；成本页改读 token 数据。**做完这步，本机无 OpenCost、无 K8s 也能看到按 run/skill/team 归因的真实 Token 成本。**
- **Phase 2 · TokenBudgetGate**：新增 `token_policy.py` + `/api/v1/cost-gate/token/*`；页面「Cost Gate 自检」「治理目标」改用 token 语义；Terraform gate 降级为 legacy。
- **Phase 3 · K8s Pod 沙箱（可选隔离升级）**：新增 `KubernetesSandbox` 作为 docker/lite 之外的确定性校验执行底座；**token 归因已在 P1 由进程内探针完成**，K8s 仅提升隔离/可复现、不采 token；K8s 不可用自动降级。**非北极星前置依赖，可延后或仅在已有 kind 集群时启用。**
- **Phase 4 · 验证/演练 Token 归因闭环**：技能验证、孪生演练全程记 token 并归因到 skill→agent→team；sustainability/ratchet 接入真实数据。
- **Phase 5 · 优化目标驱动**：成本页设定 token 目标 + 杠杆，派发任务/话题，进度追踪 + 棘轮锁定。
- **Phase 6 · 清理与收口**：移除/隔离与 token 无关的 Terraform 成本逻辑在主路径上的暴露；统一命名（成本=Token）。

> 依赖顺序：P1 →（P2 ∥ P4）→ P5 → P6；**P3（K8s）解耦可选**，不阻塞 token 归因闭环。P1 单独就能止血当前页面「无数据/告警喧宾夺主」并打通 run→skill→team 的 Token 归因。

---

## 5. 代码评审：需补充 / 修改清单（按文件）

**新增**
- `src/backend/agents/token_ledger.py`：TokenLedger 归因聚合（封装 usage.db + proficiency_store + scenario tokens）。
- `src/backend/agents/token_policy.py`：TokenViolationType / TokenBudgetEngine（替代 cost_policy 的 token 版）。
- `src/backend/agents/token_gate_routes.py`：`/api/v1/cost-gate/token/*`。
- `src/backend/sandbox/k8s_runner.py`：`KubernetesSandbox`（batch/v1.Job，确定性校验脚本的隔离底座；**不采 token**）。可选/后置。
- `src/backend/agents/token_context.py`：`contextvars` 实现 `token_scope(run_id, phase, skill_id, ...)`——这就是「进程内 Token 探针」的插桩端；读出端复用 `TokenLedger.run(run_id)`，**不单独建 token_probe.py**（避免与 ledger 重复）。属 P1。
- `src/backend/agents/cost_targets.py` + 路由：Token 优化目标存储与进度。

**修改**
- `src/backend/agents/chat_harness.py`：`record_usage` 调用处补 `phase/skill_id/scenario_id/run_id`（从 contextvar 透传）。
- `src/backend/agents/budget/store.py`：usage_log 增列（phase, skill_id, scenario_id, run_id），加聚合查询。
- `src/backend/agents/cost_routes.py`：新增 `/cost/tokens/*`；`/cost/summary` 增加 `source=token|infra` 切换。
- `src/backend/agents/skill_verifier.py`：用 `get_sandbox(mode)`（含 k8s）；包一层 run_id；把验证 LLM token 计入 Ledger；verified→granted 前调 TokenBudgetGate。
- `src/backend/sandbox/orchestrator.py` / `twin_loop.py`：演练包 run_id；接探针；passed→lock 前调 TokenBudgetGate。
- `src/backend/sandbox/python_runner.py`：`get_sandbox()` 支持 `mode=k8s`。
- `src/backend/agents/sustainability.py`：tokens_consumed 数据源切到 TokenLedger（真实）。
- `src/backend/agents/cost_gate_routes.py`：Terraform 路由迁到 `/terraform/*`，根路径转 token。
- 前端 `src/frontend/cost-dashboard.html` + `js/cost-dashboard.js`：默认渲染 token 数据；治理目标/自检改 token 语义；新增「设定 Token 优化目标」表单。

**保留/兼容**：`ci_cost_gate.py`、`cost_policy.py` 标注 legacy；不删，避免破坏既有 CI 引用。

---

## 6. 风险与回退
- **K8s 不可用（本机常态）**：所有沙箱 `mode=k8s` 必须能自动降级 docker/lite，探针进程内计量，保证本机闭环可跑。
- **usage.db schema 变更**：新增列用 `ALTER TABLE ... ADD COLUMN`（SQLite 兼容旧库），旧行字段置空不报错。
- **行为兼容**：Terraform gate 不删，迁到 `/terraform/*`；旧 CI 调用保持可用。
- **每阶段可回退**：P1~P5 各自独立分支/提交，前端通过 `source` 开关灰度。

## 7. 验收标准（可验证）
- A1：本机无 OpenCost 时，成本页仍显示真实 **Token** 成本（来自 usage.db），不再弹「无成本数据」红条。
- A2：`/api/v1/cost/tokens/by-team` 返回非空且与 usage.db 一致（脚本核对）。
- A3：技能验证产生的 token 能在 `/cost/tokens/run/{run_id}` 查到，并归因到 skill→agent→team。
- A4：TokenBudgetGate 对一个「高 token 低 score」run 给出 WARN/BLOCK。
- A5：`mode=k8s` 在有/无 K8s 两种环境都能完成一次 skill_verify（有 K8s 起 Pod，无则降级），且都记录到 Ledger。
- A6：在成本页设定一个团队的 token 目标 → 创建任务 → 进度可见；达成后棘轮新增一条 `cost_efficiency:{team_id}` 记录。
