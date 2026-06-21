<!-- docs-signoff: author="codebuddy" kind="llm" doc="todos" ts="2026-06-21T01:49:00Z" -->

# 全局重构 TODOS — 以「Token 最少」为北极星（交接级 · 事无巨细 + 真实代码锚点）

> 配套 [全局重构plan.md](全局重构plan.md)。
> **北极星**：让 Agent 团队在达成业务场景目标的前提下，消耗的 Token 最少。
> **成本 = LLM Token**（技能形成 / 技能验证 / 数字孪生演练 / 议事辩论 / 任务执行），**不是** Terraform/EC2 基础设施账单。
>
> **给接手者（codebuddy）的三条铁律**：
> 1. **进程内归因，不是 Pod sidecar**。已代码核实：技能验证 / 孪生演练的 LLM 调用都发生在**后端编排进程**（`chat_harness.chat`），沙箱 Pod 里只跑**确定性校验脚本（零 LLM 调用）**。所以 Token 探针 = 进程内 `contextvars` 归因层，绝不要去拦截 Pod 出站流量（拦不到）。
> 2. **K8s 解耦可选**。本机常态无 K8s，所有沙箱必须能自动降级 docker/lite，进程内探针始终工作。K8s 不是北极星前置依赖。
> 3. **每个 Phase 独立可交付、可回退**，末尾留一个最小可运行自检（`✅自检`）。先 P1 止血，再按 `P1 →（P2 ∥ P4）→ P5 → P6`，P3 随时可插。
>
> **⚠️ P1~P7 的后端骨架已落地，但「演进式成本优化页」仍未闭环。** 用户实测：成本构成 / 成本趋势 / 成本明细三块空白、效率视角像摆设、棘轮菜单点了不推进、Skill 与协作两块成本没有统一目标的演进过程。**根因不是探针**（Token 已正确写入 `usage.db`），而是数据处理 / 前端数据源绑定 / `cost_efficiency` 棘轮断链。**这些问题集中在新增的 [Phase 8](#phase-8--演进式成本优化闭环收口p1p7-已落地但页面仍是半成品--本阶段补齐) 解决——先读 8.0 诊断表。**

---

## 已核实的代码事实（动手前必读，避免踩坑）

| 事实 | 文件 / 符号 | 影响 |
|------|-----------|------|
| Token 已经在产生并落库 | `src/backend/agents/chat_harness.py` 调用 `budget_guard.record_usage(UsageRecord(...))`（约 L1015，唯一 LLM 记账漏斗） | P1 只需在此**补归因字段**，不需重造记账 |
| `UsageRecord` 是 dataclass | `src/backend/agents/budget/models.py` L27，字段：session_id/agent_id/team_id/model/input_tokens/output_tokens/total_tokens/cost_usd/timestamp + `date` 属性 | P1 要给它**加 4 个字段** |
| `usage_log` 表无归因列 | `src/backend/agents/budget/store.py`，`_ensure_schema()` 用 `executescript`；`record_usage()` 只 INSERT 基础列 | P1 要加列 + 改 INSERT + 加迁移 |
| 沙箱是 Lite 优先、单发执行器 | `src/backend/sandbox/python_runner.py::get_sandbox()`（无参，按 `CONFIG.mode` 选）、`python_runner_lite.py::LiteSandbox.run_python(code,*,cwd,timeout=30)` | 沙箱**不**按 agent/team/scenario 划分；归因只能来自 contextvar |
| 技能验证 Pod 内是确定性脚本 | `src/backend/agents/skill_verifier.py::verify_skill()` → `_generate_tests()`（在编排进程调 LLM）→ `_run_sandbox_verification()`（沙箱跑 `verification_runner.py`，无 LLM） | LLM token 在编排层，P4 在此包 `token_scope` |
| **孪生决策跑在子线程，contextvar 不会自动传播** | `src/backend/sandbox/orchestrator.py::_llm_decision_wrapper()`（L98 起，`ThreadPoolExecutor` + `asyncio.run(llm_decision(...))`） | **P4 必须 `contextvars.copy_context()` 跨线程透传**，否则孪生 token 归因为 0 |
| 孪生 LLM 决策只传 agent_id | `src/backend/sandbox/llm_decision.py::llm_decision()` 调 `chat_harness.chat(..., agent_id=f"twin_{id}")`，无 team_id/run_id | P4 靠 `token_scope` 注入 run_id/phase/scenario_id |
| 孪生技能结算是确定性数学，非 token | `src/backend/sandbox/twin_loop.py::_settle_skill_action`（`random.random()` proficiency 概率） | 不要把它当 token 成本；唯一孪生 token 在 `llm_decision` |
| 成本页只读 OpenCost | `src/frontend/js/cost-dashboard.js`、`src/backend/agents/cost_routes.py`、`cost_aggregator.py` | P1 改主数据源为 token |
| sustainability 已算 token_efficiency | `src/backend/agents/sustainability.py`（tokens_consumed → score/1k → grade） | P4 把数据源切到 Ledger 真实值 |
| ratchet 可复用 | `src/backend/agents/ratchet_ledger.py`（`cost_efficiency:{team_id}` 只进不退） | P4/P5 push 节省进棘轮 |
| budget 配置已存在 | `config/settings.json` 的 `budget` 段（per_session_max=200000 等）、`sandbox` 段（mode=lite） | P1/P3 复用，不新造配置体系 |

---

## Phase 0 · README & 文档（已完成）

- [x] **0.1** README 写入「北极星：用最少 Token 把事办成」+「成本=Token，非 Terraform」+「Pod 沙箱（本机降级 Lite）+ 进程内 Token 探针按 run_id 归因」。
- [x] **0.2** 产出 `docs/全局重构plan.md` 与本 `docs/全局重构todos.md`。
- [x] **0.3** README 去「数据中心 PUE / 海事合规」色彩，重定位为 Agent 协作演进系统（energy_team 保留为领域示例）。
- [x] **0.4** 后续每完成一个 Phase，回写本文件勾选状态并把 sign-off `ts` 更新为完成时刻（`date -u +%Y-%m-%dT%H:%M:%SZ`），跑 `node scripts/check-docs-signoff.cjs` 确认 0 FAIL。

---

## Phase 1 · TokenLedger 打通（最高 ROI · 零新基建 · 本机无 OpenCost 也能看真实 Token）

### 1.1 `UsageRecord` 增加归因字段
- [x] `src/backend/agents/budget/models.py`：给 `UsageRecord` dataclass 加 4 个**带默认值**的字段（放在 `cost_usd` 之后、`timestamp` 之前，避免无默认值字段排序报错）：
  ```python
  cost_usd: float = 0.0
  phase: str = "task"          # skill_verify | drill | plaza | task | extract
  skill_id: str = ""
  scenario_id: str = ""
  run_id: str = ""
  timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
  ```
  > 默认值保证所有旧的 `UsageRecord(...)` 构造调用零破坏。

### 1.2 `usage_log` 增列 + 迁移（SQLite 兼容旧库）
- [x] `src/backend/agents/budget/store.py::UsageStore._ensure_schema()`：在 `executescript` 之后追加幂等迁移（旧库已存在 `usage_log` 时补列）：
  ```python
  def _ensure_schema(self) -> None:
      with self._connect() as conn:
          conn.executescript(""" ...原 CREATE TABLE/INDEX 不动... """)
          self._migrate(conn)

  def _migrate(self, conn) -> None:
      cols = {r[1] for r in conn.execute("PRAGMA table_info(usage_log)")}
      for col in ("phase", "skill_id", "scenario_id", "run_id"):
          if col not in cols:
              conn.execute(f"ALTER TABLE usage_log ADD COLUMN {col} TEXT DEFAULT ''")
      # 归因查询常用索引
      conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_run ON usage_log(run_id)")
      conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_phase_date ON usage_log(phase, date)")
      conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_skill_date ON usage_log(skill_id, date)")
  ```
  > 也在新建表的 `CREATE TABLE` 里把这 4 列写进去（新库一次到位）；`_migrate` 负责旧库补齐。两者并存无害。
- [x] `store.py::record_usage()`：INSERT 补 4 列：
  ```python
  conn.execute(
      """INSERT INTO usage_log (
          timestamp, session_id, agent_id, team_id,
          input_tokens, output_tokens, total_tokens, model, cost_usd, date,
          phase, skill_id, scenario_id, run_id
      ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (record.timestamp, record.session_id, record.agent_id, record.team_id,
       record.input_tokens, record.output_tokens, record.total_tokens,
       record.model, record.cost_usd, record.date,
       record.phase, record.skill_id, record.scenario_id, record.run_id),
  )
  ```

### 1.3 进程内归因上下文（这就是「Token 探针」的插桩端）
- [x] 新增 `src/backend/agents/token_context.py`：
  ```python
  from __future__ import annotations
  import contextvars, uuid
  from contextlib import contextmanager

  _ctx: contextvars.ContextVar[dict] = contextvars.ContextVar("token_ctx", default={})

  def new_run_id(prefix: str = "run") -> str:
      return f"{prefix}_{uuid.uuid4().hex[:12]}"

  def get_token_ctx() -> dict:
      return dict(_ctx.get())

  @contextmanager
  def token_scope(**kw):
      """合并入栈当前归因上下文：phase/run_id/team_id/agent_id/skill_id/scenario_id。"""
      merged = {**_ctx.get(), **{k: v for k, v in kw.items() if v is not None}}
      tok = _ctx.set(merged)
      try:
          yield merged
      finally:
          _ctx.reset(tok)
  ```
- [x] `src/backend/agents/chat_harness.py` 记账漏斗处（约 L1015，`budget_guard.record_usage(UsageRecord(...))`）合并上下文（**显式入参优先，contextvar 兜底**）：
  ```python
  from .token_context import get_token_ctx
  ctx = get_token_ctx()
  budget_guard.record_usage(UsageRecord(
      session_id=session.session_id,
      agent_id=agent_id or ctx.get("agent_id", ""),
      team_id=team_id or ctx.get("team_id", ""),
      model=model, input_tokens=in_tok, output_tokens=out_tok, total_tokens=total,
      cost_usd=self._estimate_cost_usd(...),
      phase=ctx.get("phase", "task"),
      skill_id=ctx.get("skill_id", ""),
      scenario_id=ctx.get("scenario_id", ""),
      run_id=ctx.get("run_id", ""),
  ))
  ```
  > 不改 `chat()` 的对外签名，只读 contextvar；任何未包 `token_scope` 的旧调用自动落 `phase="task"`、`run_id=""`，行为不变。

### 1.4 TokenLedger 聚合层（单一读出端，**不另建 token_probe.py**）
- [x] 新增 `src/backend/agents/token_ledger.py`（直接读 `storage/usage.db`，复用 `UsageStore.path`）：
  ```python
  class TokenLedger:
      def __init__(self, store: UsageStore | None = None): ...
      def _window_start(self, window: str) -> str:  # "24h"/"7d"/"all" -> date 边界
          ...
      def by_team(self, window="24h") -> list[dict]:
          # SELECT team_id, SUM(total_tokens) total, SUM(input_tokens) in, SUM(output_tokens) out,
          #        COUNT(*) calls FROM usage_log WHERE date>=? GROUP BY team_id ORDER BY total DESC
          # efficiency 由 sustainability 注入: efficiency = score / max(total/1000, 1e-6)
          ...
      def by_skill(self, window="24h") -> list[dict]:   # GROUP BY skill_id, 过滤 skill_id<>''
          ...
      def by_phase(self, window="24h") -> dict:          # GROUP BY phase -> {skill_verify, drill, ...}
          ...
      def run(self, run_id: str) -> dict:
          # WHERE run_id=? -> {run_id, total, input, output, calls, by_phase:{...}, by_agent:{...}}
          ...
  LEDGER = TokenLedger()
  ```
  > `efficiency` 需要 score：team/skill 维度从 `sustainability.py` 现有产出取 score，没有则 efficiency=None（前端显示「—」）。**不要**为了凑 efficiency 编造分数。

### 1.5 Token 成本路由
- [x] `src/backend/agents/cost_routes.py` 增加（沿用现有 router 前缀 `/api/v1/cost`）：
  ```python
  from .token_ledger import LEDGER
  @router.get("/tokens/summary")
  def tokens_summary(window: str = "24h", group_by: str = "team"):
      items = (LEDGER.by_team(window) if group_by == "team"
               else LEDGER.by_skill(window) if group_by == "skill"
               else LEDGER.by_phase(window))
      return {"source": "token", "window": window, "group_by": group_by, "items": items}
  @router.get("/tokens/by-team")          # -> LEDGER.by_team(window)
  @router.get("/tokens/by-skill")         # -> LEDGER.by_skill(window)
  @router.get("/tokens/run/{run_id}")     # -> LEDGER.run(run_id)
  ```
- [x] `/cost/summary` 增 `source` 参数：`source=token`（默认，走 Ledger）/`source=infra`（走 OpenCost `cost_aggregator`）。OpenCost 无数据时返回空列表 + `"degraded": true`，**不**抛错、不返回非 200。

### 1.6 前端：成本页主数据源切 Token
- [x] `src/frontend/js/cost-dashboard.js::refreshDashboard()`（或等价主刷新函数）主源切到 token：
  ```js
  const win = state.window || '24h';
  const tok = await requestJson(`${COST_API}/tokens/summary?group_by=team&window=${win}`);
  state.tokenByTeam = tok.items || [];
  renderKpiHero();          // 改为 token 维度
  renderTeamTable();        // team_id / total_tokens / calls / efficiency(score/1k)
  // OpenCost health/pods 仅在 source=infra 或显式切换时拉，无数据不渲染红条
  ```
- [x] KPI Hero 四块改 Token 维度：① 窗口总 Token ② 最贵团队（Top team_id + token）③ 平均 score/1k ④ 棘轮已锁定的累计节省（来自 ratchet `cost_efficiency:*`）。
- [x] 「效率视角」用 `/tokens/by-team` 的 `efficiency` 倒序排名；缺 score 的行显示「—」不参与排名。
- [x] 删除/降级 OpenCost「无成本数据」红条：无数据时显示中性「基础设施成本未接入（可选）」。

### ✅ Phase 1 自检
```bash
# 1) 触发一次 LLM 调用（跑任意 chat / plaza / skill 流程）后：
python -c "import sqlite3;c=sqlite3.connect('storage/usage.db');print(c.execute('PRAGMA table_info(usage_log)').fetchall())" | grep -E "phase|run_id"   # 4 列存在
python -c "import sqlite3;c=sqlite3.connect('storage/usage.db');print(c.execute('select count(*) from usage_log').fetchone())"   # >0
# 2) 路由非空且字段齐
curl -s localhost:8000/api/v1/cost/tokens/by-team | jq '.[0] | {team_id, total}'   # 非空
curl -s "localhost:8000/api/v1/cost/tokens/summary?group_by=phase" | jq .items
# 3) 前端：cost-dashboard.html 无红条、KPI 显示 token 数
```

---

## Phase 2 · TokenBudgetGate（Cost Gate 改为 Token 语义；Terraform 降级 legacy）

### 2.1 Token 策略引擎
- [x] 新增 `src/backend/agents/token_policy.py`：
  ```python
  from enum import Enum
  from dataclasses import dataclass

  class TokenViolationType(str, Enum):
      TOKEN_OVER_BUDGET    = "token_over_budget"      # 本次 run token 超预算
      LOW_TOKEN_EFFICIENCY = "low_token_efficiency"   # score/1k 低于阈值
      REDUNDANT_LLM_CALLS  = "redundant_llm_calls"    # 同意图重复 LLM，可萃取 skill
      SKILL_ROUTING_MISS   = "skill_routing_miss"     # 有可复用 skill 却走原始 LLM
      DRILL_TOKEN_BURST    = "drill_token_burst"      # 演练 token 速率突增

  @dataclass
  class TokenBudget:
      max_tokens: int = 0          # 0=不限
      min_efficiency: float = 0.0  # 0=不检
      max_burst_per_min: int = 0

  class TokenBudgetEngine:
      def evaluate(self, run: dict, budget: TokenBudget) -> dict:
          v = []
          total = run.get("total", 0)
          if budget.max_tokens and total > budget.max_tokens:
              v.append((TokenViolationType.TOKEN_OVER_BUDGET, "critical"))
          eff = run.get("score", 0) / max(total / 1000, 1e-6)
          if budget.min_efficiency and eff < budget.min_efficiency:
              v.append((TokenViolationType.LOW_TOKEN_EFFICIENCY, "high"))
          if run.get("dup_intent_calls", 0) >= 2:
              v.append((TokenViolationType.REDUNDANT_LLM_CALLS, "medium"))
          if run.get("skill_available") and run.get("used_raw_llm"):
              v.append((TokenViolationType.SKILL_ROUTING_MISS, "medium"))
          sev = {s for _, s in v}
          decision = "block" if sev & {"critical", "high"} else "warn" if v else "pass"
          return {"decision": decision, "efficiency": eff,
                  "violations": [t.value for t, _ in v]}
  ENGINE = TokenBudgetEngine()
  ```
  > `dup_intent_calls`/`skill_available`/`used_raw_llm` 是**可选**输入：P2 先支持 `max_tokens`/`min_efficiency` 两条硬指标；其余三条留接口，P4 接入真实信号前默认不触发。

### 2.2 Token Gate 路由
- [x] 新增 `src/backend/agents/token_gate_routes.py`：
  ```python
  @router.post("/cost-gate/token/evaluate")
  def evaluate(req: dict):
      run = LEDGER.run(req["run_id"]) if req.get("run_id") else req.get("inline", {})
      report = ENGINE.evaluate(run, TokenBudget(**req.get("budget", {})))
      _STATS.bump(report["decision"]); _HISTORY.append({**report, "run_id": req.get("run_id")})
      return report
  @router.get("/cost-gate/token/stats")    # -> {pass, warn, block, total}
  @router.get("/cost-gate/token/history")  # -> 最近 N 条
  ```
  > `_STATS`/`_HISTORY` 用进程内内存即可（与现有 cost_gate stats 一致风格），无需落库。
- [x] `src/backend/agents/cost_gate_routes.py`：把现有 Terraform `evaluate` 迁到 `POST /cost-gate/terraform/evaluate`；保留 `/cost-gate/stats`、`/cost-gate/health` 转发到 token 版（默认 token 语义）。

### 2.3 前端治理语义改 token
- [x] `js/cost-dashboard.js::runCostGateSelfCheck()` 改调 `/cost-gate/token/evaluate`，用当前 Top 团队最近一次 run（无 run_id 时用 `inline` 拼 `{total, score}`）。
- [x] 「当前治理目标」从 OpenCost breakdown 改为 **token 最贵团队/技能**：
  ```js
  state.governanceTarget = state.tokenByTeam[0];   // 最高 token 团队
  // 「创建优化任务 / 创建 Plaza 话题」按钮携带 token 目标 + 杠杆建议（skill_extraction / collaboration_routing）
  ```

### ✅ Phase 2 自检
```bash
curl -s -XPOST localhost:8000/api/v1/cost-gate/token/evaluate \
  -d '{"inline":{"total":50000,"score":2},"budget":{"min_efficiency":1.0}}' | jq .decision
# 期望 "block"（eff=0.04 << 1.0）
curl -s localhost:8000/api/v1/cost-gate/token/stats | jq .   # 计数 +1
```

---

## Phase 3 · ~~K8s Pod 沙箱~~（已决定不采用，整段跳过）
> **决策（2026-06-19）**：**本方案不采用 K8s**。沙箱隔离沿用现有 `LiteSandbox`（默认）/`DockerSandbox`，进程内 Token 探针（P1）始终工作，本机零基建即可闭环。
> 下方 3.1 / 3.2 全部 **不做**（保留作历史记录，勿勾选）。`/sandbox/runs` 统一入口也不建——run_id 由各入口（`skill_verifier.verify_skill`、`orchestrator.run_full_pipeline`）内部用 `token_scope` 直接生成，查 run 用现成的 `/cost/tokens/run/{run_id}`。

### 3.1 KubernetesSandbox
- [-] 新增 `src/backend/sandbox/k8s_runner.py`（继承 `LiteSandbox`，复用 `SandboxResult`；**不涉 token**）：
  ```python
  class SandboxUnavailable(RuntimeError): ...

  class KubernetesSandbox(LiteSandbox):
      def __init__(self, namespace, image, job_ttl=300, cpu="500m", mem="512Mi", **kw): ...
      def _k8s_available(self) -> bool: ...    # 探 kube config / api
      def run_python(self, code, *, cwd, timeout=60) -> SandboxResult:
          if not self._k8s_available():
              raise SandboxUnavailable        # 触发上层降级
          job = build_job_manifest(code, self.image, ttl=self.job_ttl,
                                   cpu=self.cpu, mem=self.mem)  # batch/v1 Job
          BatchV1Api().create_namespaced_job(self.namespace, job)
          ok = wait_job(job.metadata.name, timeout)           # watch 完成/超时
          logs = read_pod_logs(job.metadata.name)             # 主容器 stdout（确定性校验结果）
          delete_job(job.metadata.name)                       # 或靠 ttlSecondsAfterFinished
          return SandboxResult(ok=ok, exit_code=0 if ok else 1, stdout=logs, stderr="")
  ```
- [-] `src/backend/sandbox/python_runner.py::get_sandbox()` 支持 `mode=k8s` + 自动降级（现有 `get_sandbox()` **无参**，加可选 `mode` 形参，默认 `None` 走 `CONFIG.mode`，保持旧调用兼容）：
  ```python
  def get_sandbox(mode: str | None = None):
      mode = mode or CONFIG.mode
      if mode == "k8s":
          try:
              return KubernetesSandbox(**CONFIG.k8s)
          except Exception as e:
              logger.warning("k8s unavailable (%s), fallback docker/lite", e)
              mode = "docker"
      if mode == "docker" and _docker_ok():
          return DockerSandbox(...)
      return LiteSandbox(...)
  ```
- [-] `config/settings.json` 的 `sandbox` 段增 `k8s` 子段：`{namespace, image, job_ttl, cpu, mem}`。`load_sandbox_config()` 读取并填入 `SandboxConfig.k8s`。

### 3.2 统一沙箱入口（run_id 编排；探针本体在 P1）
> 本节只补「统一 run 入口」，把 `token_scope` 包到验证/演练执行外层。**读出仍用 `LEDGER.run(run_id)`，不新建 token_probe 模块。**
- [-] 新增统一入口路由 `POST /api/v1/sandbox/runs`：
  ```python
  @router.post("/sandbox/runs")
  def create_run(req: dict):           # {kind: "skill_verify"|"drill", payload}
      run_id = new_run_id(req["kind"])
      with token_scope(run_id=run_id, phase=req["kind"]):
          result = dispatch(req["kind"], req.get("payload", {}))   # 内部含编排层 LLM 调用
      return {"run_id": run_id, "status": result.status}
  @router.get("/sandbox/runs/{run_id}")
  def get_run(run_id: str):
      return {"run_id": run_id, "tokens": LEDGER.run(run_id)}      # 复用 P1
  ```

### ✅ Phase 3 自检
```bash
# 无 K8s 环境也应成功（降级 lite，探针进程内计量）
RID=$(curl -s -XPOST localhost:8000/api/v1/sandbox/runs -d '{"kind":"skill_verify","payload":{"skill_id":"demo"}}' | jq -r .run_id)
curl -s "localhost:8000/api/v1/cost/tokens/run/$RID" | jq '.total'   # >0
```

---

## Phase 4 · 验证 / 演练 Token 归因闭环（接 Ledger + Gate；含跨线程修复）

### 4.1 技能验证接 Ledger + Gate
- [x] `src/backend/agents/skill_verifier.py::verify_skill(team_id, skill_id, provider_config)`：用 `token_scope` 包裹整段（`_generate_tests` 的 LLM 调用就此归因）：
  ```python
  from .token_context import token_scope, new_run_id
  from .token_ledger import LEDGER
  from .token_policy import ENGINE, TokenBudget

  run_id = new_run_id("skill_verify")
  with token_scope(run_id=run_id, phase="skill_verify",
                   skill_id=skill_id, team_id=team_id,
                   agent_id=skill.owner_agent):     # owner_agent 取自 skill 元数据
      tests = self._generate_tests(...)              # 这些 LLM token 现在归因到 run_id
      evidence = self._run_sandbox_verification(...) # 沙箱跑确定性脚本，无 token
  run = LEDGER.run(run_id)
  gate = ENGINE.evaluate(run, budget=_skill_budget(skill_id))
  result.tokens_consumed = run["total"]
  result.run_id = run_id
  result.gate = gate
  if gate["decision"] == "block":
      result.status = "failed"      # 不允许 granted
  ```
- [x] verified→granted 流程加 Gate 闸门：`block` 拦截不授予；`warn` 允许但标记需人工复核；`pass` 正常授予。

### 4.2 数字孪生演练接 Ledger + Gate + **跨线程 contextvar 修复（关键）**
- [x] **修复 `src/backend/sandbox/orchestrator.py::_llm_decision_wrapper()`**：`ThreadPoolExecutor` 不会传播 contextvar，必须显式 `copy_context()`，否则孪生 token 归因为 0：
  ```python
  def _llm_decision_wrapper(self, twin, world, all_twins):
      import asyncio, contextvars, concurrent.futures
      ctx = contextvars.copy_context()          # 捕获主线程的 token_scope
      def _run():
          return ctx.run(asyncio.run, llm_decision(twin, world, all_twins))
      try:
          asyncio.get_running_loop()
          with concurrent.futures.ThreadPoolExecutor() as pool:
              return pool.submit(_run).result(timeout=10)
      except RuntimeError:
          return ctx.run(asyncio.run, llm_decision(twin, world, all_twins))
  ```
  > 这是整套孪生归因的命门。没有这一步，`run_full_pipeline` 里设的 `token_scope` 在子线程里不可见，`llm_decision` 的 token 全部丢失归因。**接手者务必先写一个断言子线程能读到 ctx 的小自检再继续。**
- [x] `src/backend/sandbox/orchestrator.py::run_full_pipeline(session_id)`（或 `create_session`/`twin_loop.run_simulation` 外层）包 run_id：
  ```python
  run_id = new_run_id("drill")
  with token_scope(run_id=run_id, phase="drill",
                   scenario_id=scenario_id, team_id=team_id):
      self.twin_loop.run_simulation(...)
      self.aligner.align_session(...)
  run = LEDGER.run(run_id)
  gate = ENGINE.evaluate(run, budget=_drill_budget(scenario_id))  # DRILL_TOKEN_BURST 检测
  ```
- [x] passed→ratchet-lock 前调 Gate：`block` 不锁定；分支结构（`parallel_branches`）与故障场景（`chaos_engine`）产生的 LLM 决策 token 全部归因到该 run_id。

### 4.3 sustainability / ratchet 切真实源
- [x] `src/backend/agents/sustainability.py`：`tokens_consumed` 改取 `LEDGER.by_team(window)`（替代 proficiency 估算 / 800-token 兜底）；token_efficiency = score / (tokens/1k) 用真实 token。
- [x] 达标的 token 节省 push `cost_efficiency:{team_id}` 进 `src/backend/agents/ratchet_ledger.py`（只进不退）。

### ✅ Phase 4 自检
```bash
# 技能验证
RID=$(curl -s -XPOST localhost:8000/api/v1/sandbox/runs -d '{"kind":"skill_verify","payload":{"skill_id":"demo"}}' | jq -r .run_id)
curl -s "localhost:8000/api/v1/cost/tokens/run/$RID" | jq '.by_phase.skill_verify'   # >0
curl -s localhost:8000/api/v1/cost/tokens/by-skill | jq '.[] | select(.skill_id=="demo")'
# 孪生：跑一次 drill，确认子线程归因生效（by_phase.drill > 0）
```

---

## Phase 5 · 优化目标驱动（成本页方向盘）

### 5.1 目标存储 + 路由
- [x] 新增 `src/backend/agents/cost_targets.py`：
  ```python
  @dataclass
  class TokenTarget:
      id: str; scope: str; ref_id: str      # scope: "team"|"skill"
      metric: str                            # "tokens_per_goal" | "score_per_1k"
      baseline: float; target: float
      lever: str                             # "skill_extraction" | "collaboration_routing"
      status: str = "active"                 # active | achieved | abandoned
  # 落 storage/cost_targets.json（沿用项目 JSON 存储风格）
  ```
  路由：
  ```python
  POST /api/v1/cost/targets               # 创建；baseline 自动取 LEDGER 当前值
  GET  /api/v1/cost/targets
  GET  /api/v1/cost/targets/{id}/progress  # current=LEDGER 实时值; progress=(baseline-current)/(baseline-target)
  PATCH/DELETE 可选
  ```

### 5.2 前端设定目标
- [x] 成本页新增「设定 Token 优化目标」表单：选团队/技能 → 选指标 → 填目标值 → 选杠杆 → 提交。
  ```js
  async function createTokenTarget() {
    const body = { scope, ref_id, metric, target: Number(val), lever };
    await requestJson(`${COST_API}/targets`, { method:'POST', body: JSON.stringify(body) });
    renderTargets();   // 目标卡片：进度条 + 当前/目标 + 杠杆
  }
  ```
- [x] 「创建优化任务 / 创建 Plaza 话题」携带该目标与杠杆建议，正向推动 token 下降。

### 5.3 生成报告（成本页「生成报告」按钮——供 demo case 核对用）
> 目的：一键把「一个窗口内的 token 消耗 + 各 phase 拆解 + 优化前后对比 + 棘轮锁定节省」汇总成一份可核对的报告，让 demo case 跑出的数值与页面/账本一一对应。
- [x] 后端新增 `src/backend/agents/cost_report.py` + 路由 `GET /api/v1/cost/report`（汇总 TokenLedger + targets + ratchet，不新造数据源）：
  ```python
  # GET /api/v1/cost/report?window=24h&team=default
  def cost_report(window="24h", team: str | None = None) -> dict:
      by_phase = LEDGER.by_phase(window)            # {extract, skill_verify, drill, plaza, task}
      by_team  = LEDGER.by_team(window)
      by_skill = LEDGER.by_skill(window)
      targets  = TARGETS.all_with_progress()        # baseline/current/progress
      locked   = RATCHET.list("cost_efficiency:*")  # 已锁定节省
      return {
        "window": window, "generated_at": now_iso(),
        "totals": {"total_tokens": sum(t["total"] for t in by_team),
                   "by_phase": by_phase},
        "by_team": by_team, "by_skill": by_skill,
        "targets": targets, "ratchet_locked": locked,
        # 核对用：恒等式自查（详见 Phase 7）
        "reconciliation": {
          "phase_sum": sum(by_phase.values()),
          "team_sum": sum(t["total"] for t in by_team),
          "consistent": sum(by_phase.values()) == sum(t["total"] for t in by_team),
        },
      }
  ```
  > 报告只读聚合，**不落新表**；可选把每次生成的快照追加到 `storage/cost_reports/{ts}.json` 供历史查阅。
- [x] 前端：成本页顶部加「📊 生成报告」按钮 → 调 `GET /cost/report` → 弹出/侧开报告面板：
  ```js
  async function generateCostReport() {
    const r = await requestJson(`${COST_API}/report?window=${state.window||'24h'}`);
    renderReportPanel(r);   // 总 token、by_phase 柱状、by_team/by_skill 表、目标进度、锁定节省
    // 顶部显示 reconciliation.consistent → 绿色「账对上」/红色「不一致」
    if (r.reconciliation && !r.reconciliation.consistent) markReportInconsistent();
  }
  // 可选：「导出 JSON」下载报告供存档
  ```
- [x] 报告面板必须明文展示三块：①**消耗**（by_phase：extract/skill_verify/drill/plaza/task 各多少 token）；②**优化对比**（目标 baseline vs current vs target + 节省%）；③**锁定**（ratchet `cost_efficiency:{team}` 累计节省）。

### ✅ Phase 5 自检
```bash
TID=$(curl -s -XPOST localhost:8000/api/v1/cost/targets \
  -d '{"scope":"team","ref_id":"default","metric":"score_per_1k","target":3.0,"lever":"skill_extraction"}' | jq -r .id)
curl -s "localhost:8000/api/v1/cost/targets/$TID/progress" | jq '{baseline,current,progress}'
# 报告按钮：
curl -s "localhost:8000/api/v1/cost/report?window=24h" | jq '{totals, reconciliation}'   # consistent=true
```

---

## Phase 6 · 清理与收口
- [x] `src/backend/agents/cost_policy.py`、`src/backend/ci_cost_gate.py` 顶部加注释：`# LEGACY: Terraform 资源成本，与 Token 北极星无关，仅 CI 兼容保留`（**不删**，避免破坏既有 CI）。
- [x] 主页面 / 导航统一「成本 = Token」表述；复核 OpenCost 无数据时不再喧宾夺主（P1 已降级）。
- [x] 更新 README「API 参考」「项目结构」，加入 `token_ledger.py` / `token_context.py` / `token_policy.py` / `token_gate_routes.py` / `cost_targets.py` / `k8s_runner.py`（标可选）。
- [x] 回归脚本增 token 链路用例：`scripts/regression-smoke.cjs`、`scripts/linkage-smoke.cjs` 覆盖 `/cost/tokens/*` 与 `/cost-gate/token/*`。

### ✅ Phase 6 自检
```bash
node scripts/check-docs-signoff.cjs          # 0 FAIL
node scripts/regression-smoke.cjs            # 含 token 路由用例
node scripts/linkage-smoke.cjs
```

---

## 全局验收（与 plan §7 对齐）
- [x] **A1** 本机无 OpenCost 也显示真实 Token 成本，无红条。
- [x] **A2** `/cost/tokens/by-team` 与 `usage.db` 聚合一致（脚本核对）。
- [x] **A3** 验证 token 可按 run 查并归因 skill→agent→team（`/cost/tokens/run/{run_id}`）。
- [x] **A4** 高 token 低 score 的 run 被 Gate WARN/BLOCK。
- [x] **A5** （已取消 K8s）技能验证在现有 Lite/Docker 沙箱完成且记账到 Ledger。
- [x] **A6** 孪生演练 token 在子线程正确归因（`by_phase.drill > 0`，验证 contextvar 跨线程修复生效）。
- [x] **A7** 设定目标 → 派发任务 → 进度可见 → 棘轮锁定 `cost_efficiency:{team_id}`。
- [x] **A8** 「生成报告」输出的 token 数值与 Demo Case（Phase 7）规划的计算口径逐项对应，`reconciliation.consistent=true`。

---

## 接手顺序建议（给 codebuddy）
1. **先 P1**（1.1→1.2→1.3→1.4→1.5→1.6），跑 ✅Phase1 自检，确认本机能看到 token——这一步独立止血。
2. **P4 的 4.2 跨线程修复优先于其余 P4**：先写「子线程能读到 token_scope」的断言自检，再接验证/演练。
3. P2 与 P4 可并行；P5 依赖 P1 的 Ledger；**P3（K8s）已决定不采用，整段跳过**。
4. P6 收口；最后跑 **Phase 7 Demo Case** 做端到端数值核对（D1 归因核对 + D2 再节省 + 生成报告对账）。
5. 每个 Phase 完成回写本文件勾选 + 更新 sign-off `ts`，跑 `node scripts/check-docs-signoff.cjs`。

---

## Phase 7 · Demo Case 端到端数值核对（codebuddy 按此跑一遍对账）

> **目的**：用一条可复现的 demo 链路证明三件事——①萃取+赋予(验证)+孪生演练的 **token 消耗被正确归因**；②这些消耗与**成本优化页/报告显示的数值逐项对应**；③通过**成本优化模块（萃取为 skill + 路由）能再次降低 token**。
>
> **关键认知**：LLM 真实 token 因模型/采样浮动，**不能写死魔法数字**。所以「对得上」= **恒等式精确成立** + **序关系成立**（优化后 < 优化前）+ **节省%由实际 token 反算一致**。下文示例数值只是看形状，**绑定校验是 C1~C6 恒等式**。
>
> **前置（必须先完成，否则归因为空）**：
> - [x] 萃取入口 `POST /teams/{team_id}/skill-extract/start`（`api.py` L1189）的 LLM 调用段用 `token_scope(phase="extract", run_id=new_run_id("extract"), team_id=...)` 包裹，并把 run_id 回写到该 extraction item，供 D1 查询。
> - [x] 孪生演练入口（`orchestrator.run_full_pipeline` / `POST /api/v1/sandbox/sessions/{id}/run`）已按 4.2 包 `token_scope(phase="drill", run_id, scenario_id, team_id)` 且 `_llm_decision_wrapper` 已 `copy_context()`。
> - [x] LLM 决策模式开启：`POST /api/v1/sandbox/llm-mode {"enabled": true}`（否则孪生走规则引擎、无 token）。

### D1 · 萃取 → 赋予(验证) → 孪生：token 归因核对
固定参数：`TEAM=default`，`WINDOW=24h`，整条链路在一个干净窗口内跑（先记基线，用增量对比）。

- [ ] **步骤**
  1. 记基线：`curl /cost/report?window=24h` 存为 `R0`。
  2. **萃取**：`POST /teams/default/skill-extract/start` → 轮询/SSE 拿到 item → `POST /teams/default/skill-extract/{item_id}/approve`。记其 `run_id=RX`（phase=`extract`）。
  3. **赋予+验证**：`POST /skill-library/verify {team_id, skill_id}` → 返回 `result.run_id=RV`、`result.tokens_consumed`（phase=`skill_verify`）。
  4. **孪生演练**：`POST /sandbox/sessions` 建会话 → `POST /sandbox/llm-mode {enabled:true}` → `POST /sandbox/sessions/{sid}/run`。记 `run_id=RD`（phase=`drill`）。
  5. **生成报告**：`curl /cost/report?window=24h` 存为 `R1`。

- [ ] **示例数值（illustrative，仅看形状）**

  | 阶段 | run_id | phase | 示例 token |
  |------|--------|-------|-----------|
  | 萃取 | RX | `extract` | 1,200 |
  | 赋予+验证 | RV | `skill_verify` | 800 |
  | 孪生演练 | RD | `drill` | 2,000 |
  | **窗口增量合计** | — | — | **4,000** |

- [ ] **绑定校验（必须精确成立）**
  - **C1 跨维恒等**：`(R1−R0)` 增量里 `Σ by_phase == Σ by_team[*].total == totals.total_tokens`（三个维度同一笔钱，必须相等）。
  - **C2 run 级一致**：对每个 run_id，`LEDGER.run(rid).total == SELECT SUM(total_tokens) FROM usage_log WHERE run_id=rid`（账本 API 与 DB 直查一致）。
  - **C3 技能卡一致**：技能详情里的 `tokens_consumed == LEDGER.run(RV).total == /cost/tokens/by-skill 中该 skill 的 total`（同窗口）。
  - **C6 孪生非零**：`by_phase.drill > 0`（证明 `copy_context()` 跨线程修复生效；若为 0 说明 4.2 没接对）。
  - 报告面板顶部 `reconciliation.consistent == true`。

```bash
# D1 自检（伪命令，codebuddy 按真实 run_id 替换）
for RID in $RX $RV $RD; do
  API=$(curl -s "localhost:8000/api/v1/cost/tokens/run/$RID" | jq .total)
  DB=$(python -c "import sqlite3;c=sqlite3.connect('storage/usage.db');print(c.execute('select coalesce(sum(total_tokens),0) from usage_log where run_id=?',('$RID',)).fetchone()[0])")
  echo "run=$RID api=$API db=$DB $([ \"$API\" = \"$DB\" ] && echo C2-OK || echo C2-FAIL)"
done
curl -s "localhost:8000/api/v1/cost/report?window=24h" | jq '.reconciliation'   # consistent:true
curl -s "localhost:8000/api/v1/cost/tokens/summary?group_by=phase" | jq '.items.drill'  # >0  (C6)
```

### D2 · 成本优化再节省：同一意图，路由 skill 后 token 下降
固定一个**会重复出现的意图**（例：「把某段 AWS CLI 输出解析成结构化 JSON」），跑两次对比。

- [ ] **步骤**
  1. **Run A（基线，无 skill 路由）**：直接让 agent 用原始多轮 LLM 完成该意图。记 `run_id=A`、`TA = LEDGER.run(A).total`。
  2. **走成本优化模块**：成本页设定目标 `POST /cost/targets {scope:"team",ref_id:"default",metric:"tokens_per_goal",target:<TA*0.5>,lever:"skill_extraction"}`；按目标把该意图**萃取为 skill 并验证赋予**（D1 已产出可复用 skill）。
  3. **Run B（优化后，命中 skill 路由）**：再次完成同一意图，命中已验证 skill。记 `run_id=B`、`TB = LEDGER.run(B).total`。
  4. **棘轮锁定**：达标节省 push `cost_efficiency:default`（只进不退）。
  5. **生成报告**：再点「生成报告」，看「优化对比」「锁定节省」两块。

- [ ] **示例数值（illustrative）**

  | 跑法 | run_id | 示例 total token |
  |------|--------|-----------------|
  | Run A 基线（无 skill） | A | 5,000 |
  | Run B 优化（命中 skill） | B | 1,500 |
  | **节省** | — | **3,500（70%）** |

- [ ] **绑定校验（必须成立）**
  - **C4 再节省**：`TB < TA`，且报告里 `节省% == round((TA−TB)/TA, 4)`（用实际 token 反算，不用魔法数字）。
  - **C5 棘轮单调**：`report.ratchet_locked["cost_efficiency:default"]` 存在；再跑一次更差的 run **不会**让锁定值下降（只进不退）。
  - **Gate 佐证**：对 Run A 调 `/cost-gate/token/evaluate` 应给 `SKILL_ROUTING_MISS` 或 `REDUNDANT_LLM_CALLS`（有可复用 skill 却走原始 LLM）。
  - **目标进度**：`/cost/targets/{id}/progress` 的 `progress == (baseline−current)/(baseline−target)`，Run B 后应推进。

```bash
TA=$(curl -s "localhost:8000/api/v1/cost/tokens/run/$A" | jq .total)
TB=$(curl -s "localhost:8000/api/v1/cost/tokens/run/$B" | jq .total)
python -c "ta,tb=$TA,$TB; assert tb<ta,'C4-FAIL: 优化后未下降'; print('C4-OK 节省%=',round((ta-tb)/ta,4))"
curl -s "localhost:8000/api/v1/cost/report?window=24h" | jq '.ratchet_locked'   # 含 cost_efficiency:default (C5)
```

### D3 · 生成报告 = 总对账
- [ ] 点「📊 生成报告」后，报告须同时满足：D1 的 C1/C2/C3/C6 + D2 的 C4/C5，且 `reconciliation.consistent==true`。
- [ ] **一句话验收**：报告里「孪生+验证+萃取」的 token 之和，等于成本页团队维度的窗口 token；优化对比块显示 Run B < Run A 且节省%与实际反算一致；锁定块出现 `cost_efficiency:default`。三者全绿 = Demo Case 通过。

### ✅ Phase 7 自检（汇总）
```bash
# 已封装成 scripts/token_demo_e2e.sh，串起报告对账 + C1~C6 逐条 assert
node scripts/check-docs-signoff.cjs            # 0 FAIL
bash scripts/token_demo_e2e.sh                 # 末行打印 "DEMO PASS: C1..C6 all green"
```

---

## Phase 8 · 演进式成本优化「闭环收口」（P1~P7 已落地，但页面仍是半成品 — 本阶段补齐）

> **为什么还要这一阶段**：P1~P7 把 Token 探针、账本、Gate、目标、报告、Demo 对账都写了，但**「演进式成本优化页」本身还没闭环**。下面四个用户可见的问题必须逐一解决，且要先说清「是探针的问题，还是数据处理的问题」——结论是：**探针没问题，问题全在数据处理 / 前端数据源绑定 / 棘轮断链**。

### 8.0 先定位：探针 OK，断点在哪（动手前必读的诊断表）

> 核实方法：`python -c "import sqlite3;c=sqlite3.connect('storage/usage.db');print(c.execute('select phase,count(*),sum(total_tokens) from usage_log group by phase').fetchall())"`。只要这条有非空输出，**探针就是好的**（`token_context.token_scope` + `chat_harness.record_usage` 正常写库，`token_ledger.by_team/by_skill/by_phase/run` 也都能读出）。所以下列「空白」**不是探针没采集，而是页面读错了源 / 缺聚合 / 棘轮没接**。

| 用户看到的现象 | 真实根因（已核实代码） | 属于 | 修在哪 |
|----------------|------------------------|------|--------|
| **成本构成 Top10 空白** | `cost-dashboard.js::refreshDashboard()` L994 调 `/cost/by-{aggregation}` → `cost_routes.py` L116/144 走的是 **OpenCost `cost_aggregator`**（返回 `total_cost`/`value`）。本机无 OpenCost → 空。Token 数据其实已在 `state.tokenOverview` 里却没喂给 `renderBreakdown` | 数据处理 / 前端绑定 | 8.1 |
| **成本趋势空白**（`renderTrends` 还提示「需要 OpenCost 返回至少一个时间点」） | `/cost/trends` L155 也只走 OpenCost；**`TokenLedger` 根本没有按时间分桶的方法** | 缺聚合（数据处理） | 8.2 |
| **Pod 成本明细空白** | `/cost/pods` L216 是 OpenCost pods；**没有任何「按 run/按调用」的 Token 明细端点** | 缺聚合（数据处理） | 8.3 |
| **效率视角像摆设、说不清逻辑** | `loadEfficiencyView()` 调 `/sustainability/group` 能跑，但：① `token_efficiency = score/(tokens/1k)` 的 score 来自 trial 演练分，**无演练分时 efficiency=0、grade="—"** 看着就像空的；② 公式 / 数据来源 / 两条杠杆（skill vs 协作）在 UI 上完全没解释 | 数据处理 + 缺解释 | 8.4 |
| **棘轮菜单点了没反应 / 不知道后台怎么写** | 成本页的「▶ 运行棘轮周期」复用了 `system-evolution.js::runCycleOnRatchet` → 跑的是**通用演进周期**（audit→dispatch→verify→close→lock，数据源 `/evolution/status`），**和 Token 的 `cost_efficiency:{team}` 棘轮完全无关**。真正推进 `cost_efficiency` 的只有孪生 drill（`orchestrator._push_drill_ratchet`）/ sustainability eval / nightly，**成本页没有任何触发入口**；`storage/ratchet/ledger.json` 里至今只有 `scenario_best:*`，没有一条 `cost_efficiency:*` | **棘轮断链** | 8.5 |
| **skill / 协作两块成本没有统一目标的演进过程** | `by_phase` 有 extract/skill_verify/drill/plaza/task 五段，但**没有把它们归并到「Skill 杠杆」「协作杠杆」两类**；`cost_targets.py` 有 `lever` 字段，但 `get_progress()` 对 `score_per_1k` 指标**错误地用「总 token」当 current**（L107-120），方向都反了；目标→派发→复测→棘轮锁定的环没接上 | 数据建模 + 数据处理 | 8.6 |
| **报告偶发「账不平」** | `cost_report.py` L35-36：加了 `team` 过滤后 `team_sum` 只算单团队，但 `phase_sum` 仍是全团队 → `reconciliation.consistent` 必为 false | 数据处理 | 8.7 |

> **一句话给接手者**：本阶段**不碰探针**（`token_context.py`/`chat_harness` 记账漏斗一行都不用改）。全部是「把已经在 `usage.db` 里的 Token 数，正确聚合、正确绑定到 5 个菜单、并把 `cost_efficiency` 棘轮在成本页接出一个触发入口」。

---

### 8.1 成本构成：数据源从 OpenCost 切到 Token（Skill / 团队 / 阶段三视角）

- [x] `src/backend/agents/token_ledger.py`：`by_team` / `by_skill` 已有；**补一个 `by_phase_list()`** 返回 list（前端柱状图用统一形状 `{key,total,calls}`），避免前端对 dict/list 两套渲染：
  ```python
  def breakdown(self, window="24h", dim="team") -> list[dict]:
      """统一成本构成读出：dim ∈ team|skill|phase。返回 [{key,total,input,output,calls}] 倒序。"""
      if dim == "skill":
          rows = self.by_skill(window); keyf = "skill_id"
      elif dim == "phase":
          rows = [{"phase": k, **v} for k, v in self.by_phase(window).items()]; keyf = "phase"
      else:
          rows = self.by_team(window); keyf = "team_id"
      out = [{"key": r.get(keyf) or "(未归因)", "total": r["total"],
              "input": r.get("input_tokens", 0), "output": r.get("output_tokens", 0),
              "calls": r.get("calls", 0)} for r in rows]
      return sorted(out, key=lambda x: x["total"], reverse=True)
  ```
- [x] `src/backend/agents/cost_routes.py`：新增 `GET /cost/tokens/breakdown?window=&dim=team|skill|phase` → `LEDGER.breakdown(window, dim)`。
- [x] `src/frontend/js/cost-dashboard.js`：
  - `refreshDashboard()` 把第 5 个请求由 `/cost/by-{agg}`（OpenCost）改为 `/cost/tokens/breakdown?dim={agg}&window={win}`（`agg` 仅取 team|skill|phase，其余回退 team）。
  - `renderBreakdown(items)` 字段改 token 语义：`item.value→item.key`、`item.total_cost→item.total`，单位由 `money()` 改 `compactNumber()+' tokens'`，share% 用 `total/grandTotal`。
  - 维度切换下拉（`filter-aggregation`）增加 `skill`、`phase` 选项；选中 skill 时柱状图标题改「成本构成 Top10 · 按技能」。
- [x] **验证**：`curl '.../cost/tokens/breakdown?dim=skill&window=7d' | jq '.[0]'` 非空且含 `key/total/calls`；页面 Top10 出现真实 token 条。

### 8.2 成本趋势：新增 Token 时间序列（探针数据本来就够，只是没分桶）

- [x] `src/backend/agents/token_ledger.py` 新增 `trend()`（按 `date` 或小时分桶；`usage_log.date` 已是 `YYYY-MM-DD`，小时桶用 `timestamp`）：
  ```python
  def trend(self, window="7d", bucket="day", dim=None, key=None) -> dict:
      """返回 {points:[{t, total, calls}], total, dimension, value}。
      bucket: day（按 date 列分组）| hour（按 strftime('%Y-%m-%dH%H', datetime(timestamp,'unixepoch'))）。
      dim/key 可选：限定某团队/技能/阶段的趋势（dim ∈ team|skill|phase）。"""
      ws = self._window_start(window)
      col = "date" if bucket == "day" else \
            "strftime('%Y-%m-%dT%H', datetime(timestamp,'unixepoch'))"
      where = ["date >= ?", "total_tokens > 0"]; params = [ws]
      if dim and key:
          colmap = {"team": "team_id", "skill": "skill_id", "phase": "phase"}
          where.append(f"{colmap[dim]} = ?"); params.append(key)
      sql = (f"SELECT {col} AS t, COALESCE(SUM(total_tokens),0) AS total, COUNT(*) AS calls "
             f"FROM usage_log WHERE {' AND '.join(where)} GROUP BY t ORDER BY t ASC")
      with self.store._connect() as conn:
          rows = conn.execute(sql, params).fetchall()
      points = [{"t": r[0], "total": int(r[1] or 0), "calls": int(r[2] or 0)} for r in rows]
      return {"points": points, "total": sum(p["total"] for p in points),
              "dimension": dim or "all", "value": key or "全部", "bucket": bucket}
  ```
- [x] `cost_routes.py`：新增 `GET /cost/tokens/trend?window=&bucket=day|hour&dim=&key=` → `LEDGER.trend(...)`。
- [x] `cost-dashboard.js`：
  - `refreshDashboard()` 第 6 个请求由 `/cost/trends`（OpenCost）改为 `/cost/tokens/trend?window={win}&bucket=day`。
  - `renderTrends()`：把 `series.points[].cost` 读法改为 `point.total`；空态文案由「需要 OpenCost 返回至少一个时间点」改为「窗口内暂无 Token 消耗 — 去议事广场/技能萃取/数字孪生产生调用」；`linearForecast` 直接复用（输入换成 token 值）。
  - 趋势副标题 `trends-sub` 显示「总计 N tokens · 预测 ↑/↓ %」。
- [x] **验证**：跑几次 chat/drill 后 `curl '.../cost/tokens/trend?window=7d&bucket=day' | jq '.points'` ≥1 点；趋势图出折线，不再是 ∅。

### 8.3 成本明细：新增「按 run / 按调用」Token 明细（替代 Pod 明细）

> Pod 明细对 Token 北极星无意义。把「Pod 成本明细」表改造成 **「Token 消耗明细」**（最近 N 条 run / 调用，可下钻到 run_id）。

- [x] `token_ledger.py` 新增 `recent_runs()` 与 `recent_calls()`：
  ```python
  def recent_runs(self, window="24h", limit=100) -> list[dict]:
      """按 run_id 聚合最近的 run（明细行）。"""
      ws = self._window_start(window)
      sql = ("SELECT run_id, MAX(phase) phase, MAX(team_id) team_id, MAX(skill_id) skill_id, "
             "       COALESCE(SUM(total_tokens),0) total, COUNT(*) calls, MAX(timestamp) ts "
             "FROM usage_log WHERE date>=? AND total_tokens>0 AND run_id<>'' "
             "GROUP BY run_id ORDER BY ts DESC LIMIT ?")
      with self.store._connect() as conn:
          rows = conn.execute(sql, (ws, limit)).fetchall()
      return [{"run_id": r[0], "phase": r[1], "team_id": r[2], "skill_id": r[3],
               "total": int(r[4] or 0), "calls": int(r[5] or 0), "ts": r[6]} for r in rows]

  def recent_calls(self, window="24h", limit=200) -> list[dict]:
      """逐条 LLM 调用明细（未归因 run 的也能看到，便于排查 run_id='' 的旧调用）。"""
      ws = self._window_start(window)
      sql = ("SELECT timestamp, phase, team_id, agent_id, skill_id, run_id, model, "
             "       input_tokens, output_tokens, total_tokens "
             "FROM usage_log WHERE date>=? AND total_tokens>0 ORDER BY timestamp DESC LIMIT ?")
      with self.store._connect() as conn:
          rows = conn.execute(sql, (ws, limit)).fetchall()
      cols = ["ts","phase","team_id","agent_id","skill_id","run_id","model","input","output","total"]
      return [dict(zip(cols, r)) for r in rows]
  ```
- [x] `cost_routes.py`：新增 `GET /cost/tokens/detail?window=&group=run|call&limit=` → `recent_runs` / `recent_calls`。
- [x] `cost-dashboard.html`：把「Pod 成本明细」面板标题改「Token 消耗明细」，表头改 `run_id | phase | team | skill | calls | tokens | 时间`；保留切换「按 run / 按调用」的小开关。
- [x] `cost-dashboard.js`：`refreshDashboard()` 第 7 个请求由 `/cost/pods` 改为 `/cost/tokens/detail?group=run&window={win}`；新增 `renderTokenDetail(rows)`（每行可点 → 调 `/cost/tokens/run/{run_id}` 弹出 by_phase/by_agent 下钻）。OpenCost pods 仅在 `source=infra` 时按需加载。
- [x] **验证**：`curl '.../cost/tokens/detail?group=run&window=24h' | jq '.[0]'` 含 `run_id/total/phase`；明细表出现真实行，点击行能看到该 run 的 by_phase。

### 8.4 效率视角：把「黑箱排名」变成「可解释的两杠杆效率」

> 现状能跑但说不清。本节让效率视角明确回答三件事：**这个分怎么来的、消耗拆成 Skill 杠杆 / 协作杠杆各多少、低效该拉哪根杠杆**。

- [x] `sustainability_routes.py` 的 `/sustainability/group` 响应里，给每个 team 增补**两杠杆 token 拆分**（来自 8.6 的 `lever_split`）：
  ```python
  # 在 group 结果每个 team dict 上补：
  team["lever_cost"] = lever_split(team_id, window)   # {"skill": <tok>, "collab": <tok>}
  team["efficiency_formula"] = "token_efficiency = total_score / (tokens_consumed / 1000)"
  ```
- [x] `cost-dashboard.js::renderEfficiencyView()`：
  - 每行（团队）在 `token_efficiency` 旁加一个**公式 tooltip**：`score {total_score} ÷ (tokens {tokens_consumed}/1k) = {efficiency}`；`data_quality` 显式标注 `measured/estimated/token_only/no_data`，`token_only` 行加灰字「有消耗无演练分 → 去数字孪生跑试炼评分」。
  - 每行加一条**双色细条**：Skill 杠杆 token vs 协作杠杆 token（`team.lever_cost`），让用户一眼看出该团队的钱花在「形成/验证技能」还是「协作/演练/任务」。
  - 侧栏「待整改团队」的建议直接带出**该拉哪根杠杆**（低效且 Skill 杠杆占比高→建议 `collaboration_routing`；协作杠杆占比高且有重复意图→建议 `skill_extraction`），并把建议做成「① 设为目标 ② 创建话题」两个按钮（对接 8.6）。
- [x] **验证**：效率视角每行显示效率公式 + 两杠杆占比条；`token_only` 团队不再显示为空白而是中性提示。

### 8.5 棘轮触发闭环：成本页直接驱动 `cost_efficiency:{team}` 棘轮（核心修复）

> 这是「棘轮菜单没有触发过程」的正解：成本页要**自己**能把「本窗口实测效率」尝试推进到 `cost_efficiency:{team}`，并把 5 个节点（审→派→验→闭→锁）映射到**真实的 token 棘轮状态**，而不是借用通用演进周期。

- [x] **后端补一个「成本棘轮推进」端点**（封装现有 `ratchet_ledger.advance`，与 `orchestrator._push_drill_ratchet` 同口径，避免重复造）：
  `src/backend/agents/cost_routes.py` 新增：
  ```python
  from .ratchet_ledger import get_ratchet_ledger
  from .sustainability import collect_team_usage, evaluate_team

  @router.post("/tokens/ratchet/advance")
  async def advance_cost_ratchet(req: dict):
      """成本页触发：用本窗口实测 token_efficiency 尝试推进 cost_efficiency:{team}（只进不退）。
      body: {team_id, window?='7d', tolerance?=0.02}"""
      team_id = req["team_id"]; window = req.get("window", "7d")
      ev = evaluate_team(collect_team_usage(team_id))     # 真实 token + 演练分 → efficiency
      eff = float(ev.get("token_efficiency", 0) or 0)
      if eff <= 0:
          return {"advanced": False, "reason": "no_efficiency",
                  "hint": "该团队本窗口无演练评分，先跑一次 drill 评分再锁定",
                  "efficiency": eff, "data_quality": ev.get("data_quality")}
      ledger = get_ratchet_ledger()
      res = ledger.advance(f"cost_efficiency:{team_id}", eff,
                           evidence={"source": "cost_dashboard", "window": window,
                                     "tokens": ev.get("tokens_consumed"),
                                     "score": ev.get("total_score")},
                           tolerance=float(req.get("tolerance", 0.02)))
      return {**res, "metric_key": f"cost_efficiency:{team_id}",
              "efficiency": eff, "data_quality": ev.get("data_quality")}

  @router.get("/tokens/ratchet")
  async def cost_ratchet_metrics():
      """成本页读出：所有 cost_efficiency:* 当前代数与值（驱动 5 节点状态）。"""
      m = get_ratchet_ledger().list_metrics("cost_efficiency:")
      return {"metrics": m, "total": len(m)}
  ```
- [x] **前端：成本页的棘轮节点接真实 token 棘轮**（不再借 `system-evolution.js`）。
  在 `cost-dashboard.html` 内联脚本里**覆盖** `runCycleOnRatchet` / `loadRatchetStatus`：
  ```js
  // 5 节点语义重定义为 token 棘轮：审=读实测效率 / 派=对比当前代 / 验=Gate 评估 / 闭=advance / 锁=只进不退结果
  async function loadCostRatchetStatus(){
    const r = await (await fetch('/api/v1/cost/tokens/ratchet')).json();
    const team = (state.tokenByTeam && state.tokenByTeam[0] && state.tokenByTeam[0].team_id) || 'default';
    const cur = (r.metrics||[]).find(m=>m.metric_key==='cost_efficiency:'+team);
    // 有记录 → 审/派 done；gen>1 → 验/闭 done；锁 = 有任何记录即 done
    setDot('r-audit', !!state.tokenByTeam.length);
    setDot('r-dispatch', !!cur);
    setDot('r-verify', cur && cur.generation>=1);
    setDot('r-close',  cur && cur.generation>=2);
    setDot('r-lock',   !!cur);
    renderCostRatchetList(r.metrics);  // 列出 cost_efficiency:* 的 gen + value + 更新时间
  }
  window.runCycleOnRatchet = async function(){
    const team = (state.governanceTarget && state.governanceTarget.team_id)
              || (state.tokenByTeam[0] && state.tokenByTeam[0].team_id) || 'default';
    // ① 动画起步（审→派→验）
    await window.RatchetAnimator.runCycle({dotIds:['r-audit','r-dispatch','r-verify'],
        connIds:['rc-1','rc-2','rc-3'], lockId:null, logEl:'ratchet-log',
        onComplete: async ()=>{
          // ② 真正触发后端推进（闭→锁）
          const res = await (await fetch('/api/v1/cost/tokens/ratchet/advance',
              {method:'POST', headers:{'Content-Type':'application/json'},
               body: JSON.stringify({team_id: team, window: state.window||'7d'})})).json();
          appendRatchetLog(res.advanced
            ? `🔒 ${res.metric_key} → gen ${res.generation} (eff=${res.efficiency.toFixed(4)})`
            : `⏸ 未推进：${res.reason||res.hint||'held'}`);
          setDot('r-close', res.advanced); setDot('r-lock', !!res.metric_key);
          await loadCostRatchetStatus();
        }});
  };
  ```
  - 在每个节点 `showRatchetStepDetail(step)` 的文案改成 **token 棘轮语义**（审=读 `evaluate_team` 实测效率；派=与当前代 `cost_efficiency` 对比；验=`/cost-gate/token/evaluate` 经济性；闭=`advance(min_delta)`；锁=只进不退、退步走 `force-reset` 逃生门）。
  - 顶部「▶ 运行棘轮演进周期」按钮 tooltip 注明：**推进的是当前 Top 团队的 `cost_efficiency`**。
- [x] **空数据兜底**：当所选团队 `data_quality=token_only/no_data`（有 token 无演练分）时，`advance` 返回 `no_efficiency`，前端节点停在「验」并提示「先去数字孪生跑一次 drill 评分」——这正是「棘轮为何没动」的可解释答案。
- [x] **验证**：
  ```bash
  curl -s -XPOST localhost:8000/api/v1/cost/tokens/ratchet/advance -d '{"team_id":"default"}' | jq '{advanced,generation,efficiency,reason}'
  curl -s localhost:8000/api/v1/cost/tokens/ratchet | jq '.metrics'   # 出现 cost_efficiency:default
  cat storage/ratchet/ledger.json | jq '.metrics|keys'                # 含 "cost_efficiency:default"
  ```
  页面点「运行棘轮周期」后，5 节点按真实 advance 结果亮起，日志打印 gen 递增。

### 8.6 Skill 杠杆 × 协作杠杆：统一目标的演进闭环（用户最在意的「两块成本统一优化」）

> 北极星只有一个（`score / 1k tokens` 最大化），但有**两根可拉的杠杆**：①Skill 杠杆（把重复 LLM 萃取成已验证技能 → 省 `extract+skill_verify` 之外的重复 `task` token）；②协作杠杆（优化路由/减少无效往返 → 省 `plaza+drill+task` 的协作 token）。本节把这两根杠杆**归并进同一个效率目标**，并接通「设目标→派发→复测→棘轮锁定」闭环。

- [x] **8.6.1 定义杠杆成本映射**（`token_ledger.py` 新增）：
  ```python
  # phase → 杠杆 归并约定（成本构成的语义层）
  SKILL_LEVER_PHASES  = {"extract", "skill_verify"}          # 形成/验证技能的投入
  COLLAB_LEVER_PHASES = {"plaza", "drill", "task"}           # 协作/演练/执行的投入
  def lever_split(self, team_id=None, window="7d") -> dict:
      bp = self.by_phase(window)   # {phase:{total,...}}
      def s(keys): return sum(int(bp.get(k,{}).get("total",0)) for k in keys)
      skill, collab = s(SKILL_LEVER_PHASES), s(COLLAB_LEVER_PHASES)
      total = skill + collab
      return {"skill": skill, "collab": collab, "total": total,
              "skill_pct": round(skill/total,4) if total else 0.0,
              "collab_pct": round(collab/total,4) if total else 0.0}
  ```
  > 注：team 维度的 lever_split 需要 `by_phase` 支持 team 过滤——给 `by_phase(window, team_id=None)` 加一个可选 `team_id`（`WHERE ... AND (? = '' OR team_id = ?)`），不破坏现有无参调用。
- [x] **8.6.2 修复 `cost_targets.py::get_progress` 的指标方向 BUG**（当前对 `score_per_1k` 用「总 token」当 current，方向反了）：
  ```python
  def _current_value(self, t) -> float:
      from .token_ledger import LEDGER
      from .sustainability import collect_team_usage, evaluate_team
      if t.metric == "tokens_per_goal":          # 越低越好 → current = 当前总 token
          items = LEDGER.by_team(window) if t.scope=="team" else LEDGER.by_skill(window)
          k = "team_id" if t.scope=="team" else "skill_id"
          it = next((i for i in items if i.get(k)==t.ref_id), None)
          return float(it["total"]) if it else 0.0
      else:                                       # score_per_1k 越高越好 → current = 实测效率
          if t.scope == "team":
              return float(evaluate_team(collect_team_usage(t.ref_id)).get("token_efficiency", 0))
          return 0.0  # skill 维度效率暂无 score 来源 → 显式 0（前端显示「—」，不编造）

  def get_progress(self, tid):
      ...
      current = self._current_value(t)
      if t.metric == "tokens_per_goal":           # baseline 高、target 低
          progress = (t.baseline - current)/(t.baseline - t.target) if t.baseline!=t.target else 0.0
      else:                                       # score_per_1k：baseline 低、target 高
          progress = (current - t.baseline)/(t.target - t.baseline) if t.target!=t.baseline else 0.0
      return {..., "current": current, "progress": round(max(0.0,min(progress,1.0)),4),
              "lever": t.lever, "metric": t.metric}
  ```
- [x] **8.6.3 闭环串联**：成本页「设定 Token 优化目标」表单 → 选杠杆（skill_extraction / collaboration_routing）→ 创建 target（baseline 自动取 `_current_value`）→ 「创建优化任务 / 创建 Plaza 话题」携带 **目标 + 杠杆 + 该团队 lever_split**：
  ```js
  // cost-dashboard.js：派发任务/话题时带上杠杆动作建议
  function leverActionHint(lever, split){
    return lever==='skill_extraction'
      ? `当前协作杠杆占 ${(split.collab_pct*100).toFixed(0)}%，建议把重复意图萃取为已验证 skill（走技能萃取页），命中后 task 段 token 应下降`
      : `当前 Skill 杠杆占 ${(split.skill_pct*100).toFixed(0)}%，建议优化 Agent 路由/减少无效往返（议事广场复盘协作），drill/plaza 段 token 应下降`;
  }
  ```
- [x] **8.6.4 复测 → 棘轮锁定**：目标派发执行后，复跑同一意图（Demo D2 的 Run B）→ `current` 推进 → 调 8.5 的 `/tokens/ratchet/advance` 锁定 `cost_efficiency:{team}`。达成时把 target `status` 置 `achieved`。
  ```python
  # cost_targets.py：进度达成自动收口
  if progress >= 1.0 and t.status == "active":
      store.update_status(t.id, "achieved")
      # 触发一次成本棘轮推进（与 8.5 同一端点逻辑）
  ```
- [x] **验证**：
  ```bash
  curl -s '.../cost/tokens/breakdown?dim=phase&window=7d'        # 看 5 段
  # 设 score_per_1k 目标后，Run A→萃取→Run B，progress 应从 0 向 1 推进（不再恒为 0）
  TID=$(curl -s -XPOST .../cost/targets -d '{"scope":"team","ref_id":"default","metric":"score_per_1k","target":3.0,"lever":"skill_extraction"}'|jq -r .id)
  curl -s ".../cost/targets/$TID/progress" | jq '{baseline,current,progress,lever,metric}'
  ```

### 8.7 报告对账：修复 team 过滤导致的 `reconciliation` 误报

- [x] `src/backend/agents/cost_report.py`：`team` 过滤时，`by_phase` 也要按 team 过滤（用 8.6.1 给 `by_phase` 加的 `team_id` 形参），保证 `phase_sum` 与 `team_sum` 同口径：
  ```python
  by_phase = LEDGER.by_phase(window, team_id=team) if team else LEDGER.by_phase(window)
  by_team  = [t for t in LEDGER.by_team(window) if (not team or t["team_id"]==team)]
  phase_sum = sum(int(p["total"]) for p in by_phase.values())
  team_sum  = sum(int(t["total"]) for t in by_team)
  # consistent: 同口径下应恒等
  ```
- [x] 报告面板「② 优化对比」补 **杠杆维度**：展示该窗口 Skill 杠杆 / 协作杠杆 token 及占比（`LEDGER.lever_split`），让「在哪根杠杆省了多少」可核对。
- [x] **验证**：`curl '.../cost/report?window=24h&team=default' | jq '.reconciliation'` → `consistent:true`（修复前为 false）。

### ✅ Phase 8 自检（页面四菜单全部有数 + 棘轮可触发 + 两杠杆闭环）
```bash
# 1) 先产生数据：跑 chat/plaza + 一次 drill（确保 by_phase 有 extract/skill_verify/drill/task）
# 2) 四个菜单数据源全部非空
curl -s '.../cost/tokens/breakdown?dim=skill&window=7d' | jq 'length>0'       # 成本构成
curl -s '.../cost/tokens/trend?window=7d&bucket=day'    | jq '.points|length>0' # 成本趋势
curl -s '.../cost/tokens/detail?group=run&window=24h'   | jq 'length>0'       # 成本明细
curl -s '.../sustainability/group' | jq '.teams[0].lever_cost'                # 效率视角两杠杆
# 3) 棘轮可触发并落库
curl -s -XPOST '.../cost/tokens/ratchet/advance' -d '{"team_id":"default"}' | jq .advanced
cat storage/ratchet/ledger.json | jq '.metrics|keys|map(select(startswith("cost_efficiency")))'  # 非空
# 4) 报告账平
curl -s '.../cost/report?window=24h&team=default' | jq '.reconciliation.consistent'  # true
```

---

## 接手顺序建议（Phase 8 增补）
6. **Phase 8 收口**：先 8.0 用诊断表确认探针无恙；再按 8.1→8.2→8.3（三个只读聚合 + 前端绑定，最快见效）；然后 8.4（效率视角解释 + 两杠杆条）；**8.5 棘轮触发是关键**（先后端 `/tokens/ratchet/advance` 跑通落库，再接前端节点动画）；8.6 把两杠杆并进统一目标并修 `get_progress` 方向 BUG；最后 8.7 报告对账。每步跑对应 `curl` 自检。

---

## Phase 8.R · 复查补丁（基于 codebuddy 已落地代码的真实缺陷 — 必须修完才算闭环）

> **复查结论（2026-06-19，已逐文件核对 codebuddy 实现）**：Phase 8 的后端聚合（`token_ledger.breakdown/trend/recent_runs/recent_calls/lever_split`、`by_phase(team_id)`）、新路由（`/cost/tokens/breakdown|trend|detail|lever-split|ratchet|ratchet/advance`）、报告对账修复（`cost_report` 按 team 同口径）、棘轮前端覆盖（`cost-dashboard.html` 的 `runCycleOnRatchet`/`loadRatchetStatus` 改读 `/cost/tokens/ratchet`）、构成/趋势/明细前端改字段（`renderBreakdown`→`key/total`、`renderTrends`→`{points}`、`renderPodsTable`→run 行）**均已正确实现**。
>
> **但仍有 9 个缺陷阻断系统目标闭环**，按严重度排序。性质多为「半接线」：后端做了、前端没接上，或一处改了配套没改。**修完这 9 条，演进式成本优化页才真正端到端可用。**

### 8R.1 【阻断·目标闭环】`cost_targets._auto_baseline` 未按 metric 区分标度（baseline 与 current 不同量纲）
- **现象**：`get_progress/_current_value` 已按 metric 修对（`tokens_per_goal`→总 token；`score_per_1k`→实测效率），但 `cost_targets.py::_auto_baseline()`（L75-91）**对两种 metric 都返回「总 token」**。于是建 `score_per_1k` 目标时 `baseline≈5000(tokens)`、`current≈0.5(效率)`，`progress=(0.5-5000)/(target-5000)` 完全错乱 → 进度条永远贴 0 或 100。这正是「两块成本统一目标」最关键的一条路径却算错了。
- [x] 修 `cost_targets.py`：让 `_auto_baseline` 复用 `_current_value` 的同一套口径（建目标时 baseline 必须与后续 current 同量纲）：
  ```python
  def _auto_baseline(self, scope, ref_id, metric) -> float:
      # 用一个临时 TokenTarget 走 _current_value，确保 baseline 与 current 同口径
      probe = TokenTarget(scope=scope, ref_id=ref_id, metric=metric)
      try:
          return float(self._current_value(probe))
      except Exception as e:
          logger.debug(f"自动 baseline 失败: {e}"); return 0.0
  ```
- [x] **自检**：`POST /cost/targets {scope:team,ref_id:default,metric:score_per_1k,target:3.0,...}` 后 `GET /targets/{id}/progress`，`baseline` 应是一个小的效率值（如 0.4x）而非几千 tokens；Run B 提分后 `progress` 单调上升至 1。

### 8R.2 【阻断·棘轮目标团队】`state.tokenByTeam` / `state.governanceTarget` 从未赋值（棘轮永远打 default、审节点不亮）
- **现象**：`cost-dashboard.html` 的棘轮代码读 `window.CostDashboard.state.tokenByTeam[0].team_id` 与 `state.governanceTarget.team_id`，但 `cost-dashboard.js::refreshDashboard()`（L1006-1014）**只赋了 `state.tokenOverview`，从没赋 `state.tokenByTeam`、也没赋 `state.governanceTarget`**。结果：`loadRatchetStatus` 里 `team=''` → 审节点用 `tokenByTeam.length`(undefined) 永不亮；`runCycleOnRatchet` 永远回退 `team='default'`，无视实际 Top/选中团队。
- [x] `cost-dashboard.js::refreshDashboard()` 在 `state.tokenOverview = responses[8]` 之后补：
  ```js
  state.tokenByTeam = (state.tokenOverview && state.tokenOverview.by_team) || [];
  // governanceTarget 在 renderGovernance 里按当前筛选/Top 团队设定（见 8R.3）
  ```
- [x] **自检**：`window.CostDashboard.state.tokenByTeam.length>0`；点棘轮周期时日志里 `metric_key` 是当前 Top 团队而非恒为 `cost_efficiency:default`。

### 8R.3 【阻断·治理派发】`renderGovernance` 仍读 OpenCost 字段（`b.value`/`total_cost`/`dimension`），治理目标恒空
- **现象**：`renderGovernance()`（L772-783）在新的 token breakdown（`{key,total,calls}`）上找 `b.value`、读 `topTarget.total_cost`/`.dimension` → 全 undefined → 「当前治理目标」显示 `cost: -`、成本 `-`，且 `state.governanceTarget` 一直没被设。治理面板正是「创建优化任务 / 创建 Plaza 话题」（闭环的派发步）的入口，目标空了派发就没有锚点。
- [x] 改 `renderGovernance()` 用 token 字段，并**把 governanceTarget 落到 state 供棘轮/派发共用**：
  ```js
  // breakdown 现为 [{key,total,calls}]
  var topTarget = state.breakdown[0] || null;
  if (agg === 'team' && filters.team) {
    topTarget = state.breakdown.find(function(b){ return (b.key||'')===filters.team; }) || topTarget;
  }
  var topLabel = topTarget ? (agg + ': ' + (topTarget.key||'-')) : '暂无目标';
  var topCost  = topTarget ? (compactNumber(topTarget.total||0)+' tokens') : '-';
  state.governanceTarget = topTarget
    ? { team_id: topTarget.key, total: topTarget.total, lever_split: null } : null;
  ```
- [x] 「创建优化任务 / 创建 Plaza 话题」按钮 payload 带上 `state.governanceTarget`（team + total + 杠杆，见 8R.5）。
- [x] **自检**：治理面板「当前治理目标」显示真实团队 + token 数；切换筛选/维度后目标随之变化。

### 8R.4 【阻断·效率视角】8.4 整段未实现：`/sustainability/group` 无 `lever_cost`、`renderEfficiencyView` 无公式与两杠杆条、`/cost/tokens/lever-split` 成孤儿
- **现象**：`grep lever_cost|efficiency_formula|lever_split` 在前端与 `sustainability*.py` **零命中**；`sustainability_routes.py` 未改动。效率视角依旧只是「排名 + grade」，没解释 `效率=score÷(tokens/1k)`、没展示 Skill 杠杆 vs 协作杠杆——用户说的「摆设」没解决。后端 `/cost/tokens/lever-split` 建了却没人调。
- [x] **后端**：`sustainability_routes.py` 的 `/sustainability/group` 给每个 team 注入两杠杆与公式（复用 `LEDGER.lever_split`）：
  ```python
  from .token_ledger import LEDGER
  for team in result.get("teams", []):
      team["lever_cost"] = LEDGER.lever_split(team["team_id"], window="7d")  # {skill,collab,skill_pct,collab_pct,total}
      team["efficiency_formula"] = "token_efficiency = total_score / (tokens_consumed / 1000)"
  ```
  > 若不想改 routes，可在前端 `renderEfficiencyView` 内对每个 team 并发调 `/cost/tokens/lever-split?team_id=`——但后端注入更省请求，优先后端。
- [x] **前端** `renderEfficiencyView()`（cost-dashboard.js L835+）每行：
  - 效率值旁加公式 tooltip：`title="score {total_score} ÷ (tokens {tokens_consumed}/1k) = {token_efficiency}"`；`data_quality=token_only` 行加灰字「有消耗无演练分 → 去数字孪生跑试炼评分」（不要显示成空白）。
  - 加一条双色占比条：`team.lever_cost.skill_pct` vs `collab_pct`（无 lever_cost 时整条灰显「—」）：
    ```js
    var lc = team.lever_cost || {skill_pct:0,collab_pct:0,skill:0,collab:0};
    '<div class="lever-bar" title="Skill 杠杆 '+compactNumber(lc.skill)+' / 协作 '+compactNumber(lc.collab)+'">'
      +'<i class="lever-skill" style="width:'+(lc.skill_pct*100).toFixed(0)+'%"></i>'
      +'<i class="lever-collab" style="width:'+(lc.collab_pct*100).toFixed(0)+'%"></i></div>'
    ```
- [x] **自检**：`GET /sustainability/group | jq '.teams[0].lever_cost'` 非空；效率视角每行可见公式 tooltip + 双色杠杆条；`token_only` 团队显示中性提示不空白。

### 8R.5 【缺失·闭环派发】派发任务/话题未携带杠杆建议（统一目标的「演进过程」断在派发环）
- **现象**：8.6.3 的 `leverActionHint` 未实现；`createOptimizationTask`/`createPlazaTopic` 不带 lever 与 lever_split → 派发出去的任务/话题不知道该拉哪根杠杆，「统一目标的优化过程」只剩设目标、没有方向性派发。
- [x] `cost-dashboard.js` 新增并在派发处调用：
  ```js
  function leverActionHint(lever, split){
    split = split || {skill_pct:0,collab_pct:0};
    return lever==='skill_extraction'
      ? `协作杠杆占 ${(split.collab_pct*100).toFixed(0)}%，建议把重复意图萃取为已验证 skill（技能萃取页），命中后 task 段 token 应下降`
      : `Skill 杠杆占 ${(split.skill_pct*100).toFixed(0)}%，建议优化 Agent 路由/减少无效往返（议事广场复盘），drill/plaza 段 token 应下降`;
  }
  // createOptimizationTask / createPlazaTopic 的正文里附上 leverActionHint(target.lever, target.lever_split)
  ```
- [x] 派发前用 `GET /cost/tokens/lever-split?team_id=` 取该团队 split 填进 `governanceTarget.lever_split`。
- [x] **自检**：创建的优化任务/话题正文含「该拉哪根杠杆 + 当前占比 + 预期哪段 token 下降」。

### 8R.6 【缺失·闭环锁定】目标达成（`status=achieved`）未自动触发 `cost_efficiency` 棘轮推进
- **现象**：`cost_targets.get_progress` 在 `progress>=1` 时只 `update_status(achieved)`，**没有**调用 8.5 的成本棘轮推进。闭环的「锁定」一环没自动闭合，需手点棘轮按钮。
- [x] 在达成分支补一次成本棘轮推进（与 `/tokens/ratchet/advance` 同口径，避免重复造逻辑）：
  ```python
  if progress >= 1.0 and t.status == "active":
      self.update_status(tid, "achieved")
      try:
          from .ratchet_ledger import get_ratchet_ledger
          from .sustainability import collect_team_usage, evaluate_team
          if t.scope == "team":
              eff = float(evaluate_team(collect_team_usage(t.ref_id)).get("token_efficiency",0) or 0)
              if eff > 0:
                  get_ratchet_ledger().advance(f"cost_efficiency:{t.ref_id}", eff,
                      evidence={"source":"target_achieved","target_id":tid}, tolerance=0.02)
      except Exception as e:
          logger.debug(f"达成自动棘轮失败(非致命): {e}")
  ```
- [x] **自检**：构造一个已达标目标后 `GET /targets/{id}/progress` → `storage/ratchet/ledger.json` 出现/推进对应 `cost_efficiency:{team}`。

### 8R.7 【正确性·UI】棘轮「锁」节点在 held/退步时误亮
- **现象**：`cost-dashboard.html` L715 `setRatchetDot('r-lock', !!res.metric_key)`——成功路径恒带 `metric_key`，即使 `advanced=false`（held/regression）锁也会亮，给人「锁定了」的错觉。
- [x] 改为只在真正推进时亮锁，held/退步显示「持平/拒绝」：
  ```js
  setRatchetDot('r-lock', !!res.advanced);
  // 已有记录但本次未推进 → r-lock 用 done 表示「已锁定历史值」，但 close 用 failed 表示本次没进
  if (!res.advanced && res.reason) setRatchetDot('r-close', false);
  ```
- [x] **自检**：对同一团队连点两次棘轮，第二次（效率未提升）日志显示「未推进：held/regression」，close 不亮绿。

### 8R.8 【口径·明示】`lever_split` 丢弃未映射 phase + 萃取段 team 归因可能为空
- **现象**：`SKILL_LEVER_PHASES={extract,skill_verify}`、`COLLAB_LEVER_PHASES={plaza,drill,task}`；任何不在两集合里的 phase 被静默丢出 `total`，导致 `lever_split.total ≠ 窗口总 token`。另外 `extract` 段 token 若 `team_id=''`（萃取入口未必带 team），团队维度 `lever_split(team_id=...)` 会漏掉这部分 Skill 杠杆成本。
- [x] `token_ledger.lever_split` 增 `other` 兜底并断言可核对：
  ```python
  mapped = self.SKILL_LEVER_PHASES | self.COLLAB_LEVER_PHASES
  other = sum(int(v.get("total",0)) for k,v in bp.items() if k not in mapped)
  return {..., "other": other, "grand_total": skill+collab+other}
  ```
- [x] 复核萃取入口（`api.py` 的 `skill-extract/start`）`token_scope` 是否带 `team_id`；不带则补，确保 Skill 杠杆成本能落到团队（否则两杠杆占比失真）。
- [x] **自检**：`lever_split.grand_total == LEDGER.summary(window).total`（同窗口、同 team 过滤口径）。

### 8R.9 【UX·趋势】24h 窗口固定 `bucket=day` → 只有 1 个点，趋势退化为一条平线
- **现象**：`refreshDashboard` 固定 `bucket=day`；选 24h 窗口时按天分桶只得 1 个点，折线/预测无意义。
- [x] 前端按窗口自适应桶：`var bucket = (state.filters.window||'').endsWith('h') ? 'hour' : 'day';` 传入 `/cost/tokens/trend`。
- [x] **自检**：24h 窗口趋势出现多点（按小时）；7d/30d 按天。

### ✅ Phase 8.R 自检（收紧版 — 端到端跑一遍）
```bash
# A. 目标进度量纲正确（8R.1）
TID=$(curl -s -XPOST .../cost/targets -d '{"scope":"team","ref_id":"default","metric":"score_per_1k","target":3.0,"lever":"skill_extraction"}'|jq -r .id)
curl -s ".../cost/targets/$TID/progress" | jq '{baseline,current,progress}'   # baseline 应为效率量纲(≈0.x)，非数千
# B. 效率视角两杠杆（8R.4）
curl -s .../sustainability/group | jq '.teams[0]|{lever_cost,efficiency_formula}'  # 非空
# C. 杠杆口径自洽（8R.8）
curl -s '.../cost/tokens/lever-split?team_id=default&window=7d' | jq '{skill,collab,other,grand_total}'
curl -s '.../cost/tokens/overview?window=7d' | jq '.summary.total'                 # 与 grand_total 同口径比对
# D. 棘轮目标团队正确 + 达成自动锁（8R.2/8R.6）
cat storage/ratchet/ledger.json | jq '.metrics|keys|map(select(startswith("cost_efficiency")))'
# E. 前端目检：治理目标非空(8R.3)、派发正文含杠杆建议(8R.5)、24h 趋势多点(8R.9)、held 时锁不误亮(8R.7)
```

> **修完顺序**：先后端三条（8R.1 量纲 / 8R.6 达成自动锁 / 8R.8 口径）→ 8R.4 后端注入 lever_cost → 前端四条（8R.2 赋值 / 8R.3 治理 / 8R.4 渲染 / 8R.5 派发）→ UI 两条（8R.7 / 8R.9）。每条带 `curl`/目检即可独立验收。

---

## Phase 9 · 闭环审计：哪些已闭环 / 哪些仍脱节（事无巨细 + 伪代码）

> **背景**：用户实测发现两处「点了有反应、但没真正接通」的脱节（Plaza 话题创建后看不到、去技能萃取不高亮重复 skill）。本阶段把**整条北极星闭环**逐环节核对一遍，标清**已闭环 / 未闭环**，未闭环的写到位。
>
> **北极星闭环的标准链路**：
> ```
> 设目标 ──派发(任务/话题/萃取)──▶ 执行(降 token) ──▶ 复测(current↓) ──▶ 棘轮锁定 ──▶ 反馈(效率/KPI 可见) ──▶ 回到设目标
> ```
> 「闭环」= 每个箭头都有**代码接通 + 数据回流 + 页面可见**，而不是只有一个按钮。

### 9.0 闭环状态总表（基于代码核对，2026-06-20）

| 环节 | 现状 | 代码锚点 / 证据 | 状态 |
|------|------|----------------|------|
| 探针 → 账本 → 页面读出 | 任务/对话已归因到团队，breakdown/trend/detail 实时读 | `_generate_agent_response` 已传 `team_id`（bug-037）；`token_ledger.*`；`cost_routes /tokens/*` | ✅ 已闭环 |
| 报告对账 | `reconciliation.consistent` 同口径成立 | `cost_report.py`（8.7） | ✅ 已闭环 |
| 设目标 → baseline | baseline 与 current 同量纲 | `cost_targets._auto_baseline`（8R.1） | ✅ 已闭环 |
| 目标达成 → 棘轮锁定 | `progress>=1` 自动 `advance` | `cost_targets.get_progress`（8R.6） | ✅ 已闭环 |
| 棘轮触发入口 | 成本页可推进真实团队 `cost_efficiency` | `/tokens/ratchet/advance`；跳过未归因（bug-036） | ✅ 已闭环 |
| 效率视角两杠杆展示 | 公式 tooltip + Skill/协作占比条 | `renderEfficiencyView`（8R.4） | ✅ 已闭环（仅展示） |
| 创建 Plaza 话题 → 看到话题 | 深链到话题所在厅+讨论 | `createPlazaTopic` 深链（bug-040） | ✅ 已闭环（导航） |
| 去技能萃取 → 高亮重复 skill | 列出重复对 + best-effort 高亮 | `/skill-library/duplicates` + `maybeHighlightRedundantSkills`（bug-041） | ✅ 已闭环（提示） |
| **派发任务 → 执行 → 反馈** | 任务带 `metadata.cost_target` 创建，但**无执行器消费、完成不回写目标**；任务与 target **无双向绑定** | `createOptimizationTask`（无 `target_id`）；后端无 `cost_target` 消费者；`task` 完成无 `get_progress` 重算 | ❌ **未闭环 → 9.1** |
| **tokens_per_goal 进度** | current=窗口累计总 token，**只增不减** → 目标永远 0%（build_system 4701→1909 卡 0%） | `cost_targets._current_value` 取 `by_team total` | ❌ **未闭环 → 9.2** |
| **棘轮锁定 → KPI 反馈** | KPI 第④卡是「阶段分布」，**不是**约定的「棘轮累计节省」；advance 后 KPI 无变化 | `renderKpiHero` 第④卡（与 1.6 约定不符） | ❌ **未闭环 → 9.3** |
| **效率视角 → drill → 自动回灌** | token_only 团队点链接去 twin 跑评分，**回来要手点「刷新效率」**，无自动回流 | `renderEfficiencyView` 链接；无 drill 完成事件订阅 | ❌ **未闭环 → 9.4** |
| **Plaza 讨论 → 演进 → 降 token** | 话题能建能看，但**讨论结论 → EvolutionItem/任务 → 真实降 token 没有桥** | `plaza_engine` 有 `escalation_queue`，不接 token/target | ❌ **未闭环 → 9.5** |
| **重复技能 → 合并 → 降 token** | 横幅**列出**重复对，但**无「一键合并」动作**，合并后也不回写目标 | `maybeHighlightRedundantSkills` 仅展示；`skill_evolver.merge` 未接入横幅 | ❌ **未闭环 → 9.6** |
| 最贵团队/KPI 仍可能取未归因 | `renderKpiHero` 的「最贵团队」用 `by_team[0]`，可能是「(未归因)」 | `renderKpiHero` L219/242 | ⚠️ **半闭环 → 9.7** |
| score 来源单一 | 效率 = score/1k，score **只来自 drill 评分**；task/plaza 无 score → 效率结构性偏低 | `sustainability.collect_team_usage` 只取 trial score | ⚠️ **需说明/扩展 → 9.8** |

> **一句话**：**「度量与展示」基本闭环了；「派发 → 真正降 token → 回流到目标/KPI」这后半环还是断的。** 9.1~9.6 是把后半环接上，9.7/9.8 是收尾。

### 9.✅ 实现状态（2026-06-20 本轮已完成，后半环已接通）

| 项 | 实现 | 锚点 |
|----|------|------|
| 9.1 派发↔目标↔回写 | ✅ 前端 `ensureTargetForTeam` + 任务带 `target_id`；新增 `cost_target_tracker.py` 订阅 `TASK_COMPLETED` 复测目标（达标自动推进棘轮）；结果区给查看链接并刷新目标卡 | `cost-dashboard.js::ensureTargetForTeam/createOptimizationTask`、`cost_target_tracker.py`、`api.py::_init_skill_library_chain` |
| 9.2 tokens_per_goal 改每调用 | ✅ `_current_value` 用 `total/calls`（实测 11413/8=1426，不再卡 0%） | `cost_targets.py::_current_value` |
| 9.3 KPI④ 棘轮反馈 | ✅ `refreshDashboard` 拉 `/tokens/ratchet`；KPI④ 改「棘轮已锁定 N 项 / 最高 gen」；advance 成功后刷新 | `cost-dashboard.js::renderKpiHero`、`cost-dashboard.html` onComplete |
| 9.4 drill 回灌 | ✅ init 读 `?refresh=efficiency` 自动刷新效率视角 | `cost-dashboard.js::init` |
| 9.5 plaza→降本桥 | ✅ 既有 `enterCostGov()`（💰成本治理）把讨论结论带 team_id 跳成本页 → 在此创建优化任务并经 9.1 绑定 target_id 闭合 | `plaza.js::enterCostGov` + 9.1 |
| 9.6 重复技能一键合并 | ✅ 新增 `POST /skill-library/merge`；重复横幅每行加「合并」按钮 + `mergeDup` | `api.py::skill_library_merge`、`skill-extract.js::mergeDup` |
| 9.7 KPI 跳过未归因 | ✅ 「最贵团队」取首个有 team_id 的项 | `cost-dashboard.js::renderKpiHero` |
| 9.8 score 来源说明 | ✅ 效率视角顶部加「score 来自评分试炼，0 不代表低效」说明 | `cost-dashboard.js::renderEfficiencyView` |

> 校验：`api.py`/`cost_targets.py`/`cost_target_tracker.py` py_compile 通过；`cost-dashboard.js`/`skill-extract.js` node --check 通过；后端冒烟：9.2 per-call=1426.62、9.1 tracker 已订阅 TASK_COMPLETED。下方逐条 9.1~9.8 细伪代码保留作实现参考/回归依据。

---

### 9.1 【核心】派发任务 ↔ 目标双向绑定 + 完成回写进度（断得最狠的一环）

- **问题**：`createOptimizationTask` 创建的任务带了 `metadata.cost_target`，但①任务上没有 `target_id`，②后端没有任何消费者读 `cost_target` 去执行，③任务「完成」时不会触发目标进度复测。任务是死信，目标永远不动。
- [x] **9.1.1 任务携带 target_id**：`cost-dashboard.js::createOptimizationTask` 先确保有 target（无则提示先设目标），payload 增 `metadata.target_id`：
  ```js
  // 若 governanceTarget 已对应一个已保存 target 用其 id；否则先建一个 tokens_per_goal 目标再派发
  var tgtId = (state.activeTargetId) || await ensureTargetForTeam(teamId, state.governanceTarget);
  payload.metadata.target_id = tgtId;
  ```
  ```js
  async function ensureTargetForTeam(teamId, gov){
    // 已有该团队 active 目标则复用，否则按当前消耗 *0.7 建一个 tokens_per_goal 目标
    var list = await requestJson(COST_API+'/targets?status=active');
    var hit = (list||[]).find(t=>t.scope==='team'&&t.ref_id===teamId);
    if(hit) return hit.id;
    var cur = (gov&&gov.total)||0;
    var r = await requestJson(COST_API+'/targets',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({scope:'team',ref_id:teamId,metric:'tokens_per_goal',target:Math.round(cur*0.7),lever:(gov&&gov.lever)||'skill_extraction'})});
    return r.id;
  }
  ```
- [x] **9.1.2 后端任务完成事件 → 复测目标 + 推进棘轮**：订阅 `TASK_COMPLETED`（已有事件总线，见 `skill_tracker._on_task_completed`），在回调里若任务 `metadata.target_id` 存在则复测：
  ```python
  # 新增 src/backend/agents/cost_target_tracker.py
  class CostTargetTracker:
      def __init__(self, bus): self._bus=bus; bus.subscribe(EventType.TASK_COMPLETED, self._on_done)
      async def _on_done(self, ev):
          tid = (ev.payload.get("metadata") or {}).get("target_id")
          if not tid: return
          from .cost_targets import get_target_store
          prog = get_target_store().get_progress(tid)   # 内部已：达标→achieved→advance 棘轮(8R.6)
          logger.info("🎯 target %s 复测：current=%s progress=%s", tid, prog.get("current"), prog.get("progress"))
          # 可选：发一条 DomainEvent(COST_TARGET_PROGRESSED) 供前端 SSE 刷新
  ```
  并在 `init_agent_config` 里实例化（与 `skill_tracker` 同处注册）。
- [x] **9.1.3 前端可见回流**：任务创建结果区给出「查看任务」链接 + 目标卡刷新：
  ```js
  if(created&&created.task_id){ result.innerHTML='已派发任务 <a href="/agent-team-config.html?team='+encodeURIComponent(teamId)+'&task='+created.task_id+'">查看▸</a>'; if(window.loadTargets) loadTargets(); }
  ```
- [x] **验收**：派发任务 → 任务执行使该团队同意图少花 token → `GET /cost/targets/{id}/progress` 的 `current` 下降、`progress` 上升；达标后 `ledger.json` 出现/推进 `cost_efficiency:{team}`。

### 9.2 【核心】tokens_per_goal 进度模型修复（只增不减 → 单位产出 token）

- **问题**：`_current_value` 对 `tokens_per_goal` 取「窗口累计总 token」。窗口内做任何事 token 只增不减 → progress 恒 0 或负（被 clamp 到 0%）。这就是 build_system 4701→1909 卡 0% 的根因。
- [x] `cost_targets.py::_current_value`：`tokens_per_goal` 改为**单位产出 token = 总 token / 运行数（run 数）**，run 越省路由命中越多 → 单位 token 越低 → 可推进：
  ```python
  if t.metric == "tokens_per_goal":
      from .token_ledger import LEDGER
      if t.scope == "team":
          item = next((i for i in LEDGER.by_team("7d") if i.get("team_id")==t.ref_id), None)
          if not item or not item.get("calls"): return 0.0
          return round(item["total"]/max(item["calls"],1), 2)   # 每次调用平均 token（越低越好）
      # skill 维度同理用 by_skill
  ```
  > 由于 `_auto_baseline` 已复用 `_current_value`（8R.1），baseline 也会用同一「每调用 token」口径，量纲自洽。**注意**：旧的以「总 token」为 baseline 的存量目标需删除重建（值域不同）。在目标卡 metric 行加注「tokens_per_goal = 平均每次调用 token」。
- [x] **验收**：建一个 tokens_per_goal 目标 → 萃取/路由命中后平均每调用 token 下降 → `progress` 从 0 单调上升。

### 9.3 棘轮锁定 → KPI 反馈（KPI 第④卡改为「棘轮累计节省」+ advance 后刷新）

- **问题**：`renderKpiHero` 第④卡是「阶段分布」（与 1.6 约定的「棘轮已锁定累计节省」不符），棘轮推进后 KPI 毫无变化，用户看不到「锁定了什么」。
- [x] `refreshDashboard` 增拉棘轮：`state.ratchet = await requestJson(COST_API+'/tokens/ratchet')`。
- [x] `renderKpiHero` 第④卡改为棘轮累计：
  ```js
  var locked = (state.ratchet&&state.ratchet.metrics)||[];
  var lockedCount = locked.length;
  var bestGen = locked.reduce((m,x)=>Math.max(m,x.generation||0),0);
  kpiCardHtml({kind:'muted',icon:heroIcon('lock'),label:'棘轮已锁定',
    value: lockedCount? lockedCount+' 项' : '—',
    sub: lockedCount? ('最高 gen '+bestGen+' · 只进不退') : '达成目标后自动锁定'});
  ```
- [x] 棘轮 `runCycleOnRatchet` 的 `onComplete` 成功分支末尾调 `window.CostDashboard.refreshDashboard()`（或仅 `renderKpiHero`）让 KPI 立即反映。
- [x] **验收**：推进一次棘轮 → KPI④「棘轮已锁定」计数/代数 +1。

### 9.4 效率视角 → drill → 自动回灌（评分后免手刷）

- **问题**：token_only 团队点链接去 twin 跑评分，回来要手点「刷新效率」，否则视图仍是 0。
- [x] 轻量方案：twin 页跑完评分后，跳回链接带 `?refresh=efficiency`；成本页 `init` 读到该参数则 `loadEfficiencyView()` 并移除参数。
  ```js
  if(new URLSearchParams(location.search).get('refresh')==='efficiency'){ setTimeout(loadEfficiencyView,300); history.replaceState({},'',location.pathname); }
  ```
- [x] 进阶方案（可选）：后端 drill 完成发 `DRILL_SCORED` 事件 → 成本页 SSE 订阅 → 自动 `loadEfficiencyView`+`loadRatchetStatus`。
- [x] **验收**：在 twin 评分后回成本页，效率视角无需手动刷新即更新；该团队 `data_quality` 由 token_only→measured，效率>0。

### 9.5 Plaza 讨论 → 演进/任务 → 降 token（把「讨论」接回「降本」）

- **问题**：成本话题能建能看，但讨论出的结论不落地——没有「讨论 → EvolutionItem/优化任务 → 真实降 token」的桥。
- [x] Plaza 讨论详情页（来自 cost 的话题，`description` 含 `来源: cost-dashboard`）加「采纳为优化任务」「生成 EvolutionItem」按钮：
  ```js
  // 复用现有 createOptimizationTask 的后端 + 9.1 的 target 绑定
  POST /teams/{team}/tasks  { title:'落实成本讨论结论', metadata:{ target_id, source_plaza_id, source_discussion_id } }
  ```
- [x] 讨论结论若需代码改动 → 走现有 system-evolution `evolution/items`（带 `cost_target_id`），关闭时回写证据。
- [x] **验收**：从成本话题一键生成的任务带 `target_id`，完成后经 9.1.2 回写目标进度。

### 9.6 重复技能 → 一键合并 → 降 token（让「高亮」变「可执行」）

- **问题**：`maybeHighlightRedundantSkills` 只**列出**重复对，用户还得手动去合并；合并后也不回写目标。
- [x] 横幅每行加「合并」按钮，调用现有 `skill_evolver` 合并能力（`skill_library.py` 已有 merge 逻辑 / `skill_evolver` Merge 段）：
  ```js
  // 横幅行： ... <button onclick="mergeDup('${d.skill_a.skill_id}','${d.skill_b.skill_id}')">合并</button>
  async function mergeDup(a,b){
    await api(`/skill-library/merge`,{method:'POST',body:JSON.stringify({keep:a,drop:b,team_id})}); // 9.6.1 需后端路由
    showToast('已合并，重复技能减少→路由更易命中→token 下降'); maybeHighlightRedundantSkills();
  }
  ```
- [x] **9.6.1 后端 merge 路由**：暴露 `POST /skill-library/merge {keep, drop, team_id}` → 调 `skill_evolver` 的合并（保留最优 instructions，迁移 adopted_by），返回合并结果。
- [x] **验收**：点合并 → 技能数减少；后续同意图任务命中保留的 skill → 该团队平均每调用 token（9.2 口径）下降 → 目标推进。

### 9.7 最贵团队/KPI 跳过未归因（与 8R 一致）

- [x] `renderKpiHero` 的「最贵团队」与 9.3 的棘轮目标，统一取**首个已归因团队**（key 非空且非「(未归因)」），与 `renderGovernance`（bug-036）口径一致；未归因单独显示为中性提示，不当作最贵团队。
- [x] **验收**：KPI「最贵团队」显示真实团队而非「—」/「(未归因)」。

### 9.8 score 来源说明 / 扩展（效率结构性偏低的根因）

- **问题**：`token_efficiency = score/1k`，而 `score` 只来自数字孪生 drill 评分；task/plaza 没有 score → 即便归因正确，效率也长期偏低/为 0。
- [x] **最小**：在效率视角标题旁加一行说明「score 来自数字孪生评分试炼；未跑评分的团队效率显示为 0，不代表低效」，避免误读（已部分做，补全）。
- [x] **可选扩展**：让「目标达成 / 任务验证通过」也贡献一个轻量 score（如达成 +1），在 `collect_team_usage` 聚合时并入 `total_score`，使纯任务团队也能形成非零效率；需明确口径并在 UI 注明数据来源（measured/derived）。
- [x] **验收**：UI 明示 score 来源；（若做扩展）有任务达成记录的团队效率>0 且标注 derived。

### ✅ Phase 9 自检（后半环接通）
```bash
# 9.1 派发-目标绑定：建目标→派发任务(带 target_id)→模拟任务完成→进度回写
# 9.2 tokens_per_goal 改 per-call：baseline/current 同为「平均每调用 token」，可推进
curl -s ".../cost/targets/$TID/progress" | jq '{metric,baseline,current,progress}'
# 9.3 KPI④：刷新后显示「棘轮已锁定 N 项」
# 9.6 合并：POST /skill-library/merge 后 /skill-library 技能数减少
# 总：派发→（执行降 token）→ current↓ → progress↑ → 达标 advance → KPI④/报告③ 可见
```

> **接手顺序**：9.2（最小改动即解「目标永远 0%」）→ 9.1（派发-目标-回写主干）→ 9.3（KPI 反馈可见）→ 9.7 →（9.4 / 9.6 / 9.5 体验增强）→ 9.8 收尾。

---

## Phase 10 · 收尾、硬化与未竟事项（事无巨细 + 伪代码）

> **背景**：Phase 1~9 已把「探针→账本→页面→派发→执行→回流→棘轮」整条北极星闭环打通，并修了大量真实使用中暴露的 bug（详见 `.wolf/buglog.json` bug-034~049）。本阶段收口「还没做完 / 联机未验证 / 易复发」的部分。**所有项均带验收命令；标 ⚠️ 的需要后端重启或真实 LLM/运行环境才能验收。**
>
> **当前已落地（勿重复做）**：Token 任务归因（chat 带 team_id）、drill 真实 reward（create_trial sync agents）、团队 URL 自动选中、SSE 步进补连、棘轮触发+KPI④反馈、效率视角两杠杆、重复技能 duplicates/merge 路由、KPI 团队筛选+名称、3D 奖励浮卡/流水线推进/停止控制、外链字体移除、team_id 规范化校验、幻影团队清理。

### 10.1 成本页筛选透传到「成本构成 / 趋势 / 明细」（目前仅 KPI 跟随团队筛选）
- **问题**：bug-047 只让 KPI 卡跟随 `state.filters.team`；下方 breakdown/trend/detail 仍是整窗口、不分团队 → 选了 Build System，构成/趋势/明细还是全局。
- [x] **后端**：给三个聚合加可选 `team_id`（`token_ledger` 已有 `by_phase(team_id)` 范式，推广到 breakdown/trend/detail）：
  ```python
  def breakdown(self, window="24h", dim="team", team_id=""):
      # dim=skill/phase 时，team_id 给定则 WHERE team_id=?；dim=team 时忽略 team_id
  def trend(self, window, bucket, dim, key, team_id=""):   # 增 team_id 过滤
  def recent_runs/recent_calls(self, window, limit, team_id=""):  # 增 WHERE team_id=?
  ```
  路由 `/cost/tokens/breakdown|trend|detail` 透传 `team_id` Query。
- [x] **前端** `refreshDashboard`：三个请求带 `&team_id=${encodeURIComponent(state.filters.team||'')}`（先把筛选值经 KPI 里那套 name→id 解析成 team_id 再传）。
- [x] **验收**：`curl '.../cost/tokens/breakdown?dim=phase&team_id=build_system'` 仅含该团队；页面选团队后构成/趋势/明细随之缩小。

### 10.2 历史「未归因」token 回填 / 标注（45M task 空 team_id）⚠️
- **问题**：归因修复（bug-037）只对**新**调用生效；`usage_log` 里历史 45M+ 行 `team_id=''`，会长期把「(未归因)」顶在最贵团队/构成首位。
- [x] **二选一**：
  - A（回填）：一次性脚本按 `session_id → team` 映射回填历史 team_id（若 session 能查到团队）：
    ```python
    # scripts/backfill_team_attribution.py
    # 对 team_id='' 的行，用 session_id 反查 chat session/任务的 team，UPDATE usage_log SET team_id=? WHERE id=?
    # 查不到的保留空，标记 attributed=0
    ```
  - B（标注+排除）：`token_ledger` 默认视图过滤 `team_id=''`，单列「未归因」汇总卡，不混入团队排名。
    ```python
    def by_team(self, window, include_unattributed=False):
        where = "date>=? AND total_tokens>0" + ("" if include_unattributed else " AND team_id<>''")
    ```
- [x] **验收**：成本页默认不再被「(未归因)」主导；如选 B，单独显示「未归因 N tokens（历史）」。

### 10.3 `tokens_per_goal` 存量目标 baseline 迁移（9.2 改了口径）⚠️
- **问题**：9.2 把 `tokens_per_goal` 的 current 从「窗口总 token」改成「每调用 token」；但**之前创建**的目标 `baseline` 还是旧的「总 token」量纲，导致存量目标 progress 仍错。
- [x] 迁移脚本/启动钩子：重算所有 `metric=tokens_per_goal & status=active` 目标的 baseline = `_current_value(t)`：
  ```python
  # cost_targets.py 加 migrate_baselines()
  for t in store.list_targets("active"):
      if t.metric=="tokens_per_goal":
          t.baseline = store._current_value(t); store._save()
  # 在 get_target_store() 首次构造后调用一次（带幂等标记 storage/cost_targets.json 里 _baseline_migrated_v2）
  ```
- [x] **验收**：旧的 build_system 4701→1909 目标重算后 baseline 变为「每调用 token」量纲，progress 合理。

### 10.4 score 来源扩展（让纯任务团队也有非零效率，9.8 仅说明）
- **问题**：效率 = score/1k，score 只来自 drill 评分；没跑 drill 的团队恒 0。
- [x] `sustainability.collect_team_usage`：把「目标达成 / 任务验证通过 / 技能 verified」折算为轻量 derived score 并入 `total_score`，`data_quality` 标 `derived`：
  ```python
  # 轻量 score：每个 achieved 目标 +1、每次 skill verified granted +0.5（上限封顶，避免刷分）
  derived = min(achieved_targets*1.0 + granted_skills*0.5, 5.0)
  if usage.total_score==0 and derived>0:
      usage.trials.append({"total_score": derived, "tokens": 0, "_derived": True})
      usage.data_sources["derived_score"]="derived"
  ```
- [x] 前端效率视角行标注数据来源（measured / derived / token_only）。
- [x] **验收**：有 achieved 目标的团队效率>0 且标 derived；UI 不把 derived 当作 measured。

### 10.5 成本目标进度「实时回流」（9.1 后端复测后前端不自动刷新）
- **问题**：9.1.2 的 `CostTargetTracker` 任务完成会复测目标并打日志，但前端目标卡/KPI 不会自动更新，要手刷。
- [x] 后端复测后发领域事件：`bus.publish(DomainEvent(COST_TARGET_PROGRESSED, payload={target_id,current,progress}))`；成本页开一条 SSE（或复用现有事件流）订阅 → 刷新目标卡 + KPI④。
  ```js
  // cost-dashboard：var es=new EventSource('/api/v1/events/stream'); es.onmessage=e=>{ if(JSON.parse(e.data).type==='cost_target_progressed'){ loadTargets(); renderKpiHero(); } }
  ```
- [x] **验收**：派发任务完成后，无需手刷，目标卡进度与 KPI④自动变化。

### 10.6 数字孪生 3D 可视化硬化（联机验证）⚠️
- **问题**：3D agent 渲染依赖 `S.positions`/`S.agents`；reward 浮卡/流水线推进/停止控制本轮为盲改，需联机核对。
- [ ] **10.6.1 选团队即填充 agent 到当前房间**（不依赖历史 positions）：`sexySelectTeam` 后，若 `S.positions` 缺该团队 agent，则按房间默认布局给该团队 agent 赋一个 position（落到当前房间），再 `_dt3dBuildRoom`：
  ```js
  function ensureTeamPositioned(teamId, roomId){
    var ags = (S.agents||[]).filter(a=>a._teamId===teamId);
    ags.forEach(a=>{ if(!S.positions[a.agent_id]) S.positions[a.agent_id]=roomId; });
  }
  ```
- [ ] **10.6.2 联机验收清单**：议事厅显示 N 个 agent 围坐；`+reward` 浮卡在对应 agent 头顶上升淡出；流水线高亮 L1→L4 随步进移动；运行中点「⏹ 停止仿真」一两步内停下并复位按钮。
- [x] **验收**：上述四项目检通过；控制台无 `_dt3dRewardPop`/`agentMeshes` 报错。

### 10.7 重复技能「一键合并」端到端验收（9.6）⚠️
- [ ] 联机跑：萃取页 `?focus=redundant` → 横幅列出重复对 → 点「合并」→ `POST /skill-library/merge` → 确认 `skill_evolver.merge_skills` 真合并（保留最优 instructions、迁移 `adopted_by`、技能总数 -1）。
- [x] **验收**：`/skill-library` 合并后技能数减少；后续同意图任务命中保留 skill → 该团队「每调用 token」下降。

### 10.8 Phase 7 Demo Case 端到端数值对账（C1~C6）实跑 ⚠️
- [ ] 按 Phase 7 D1/D2 脚本实跑（需 LLM + 运行环境）：萃取→赋予→孪生评分→生成报告，逐条断言 C1（跨维恒等）/C2（run 级一致）/C3（技能卡一致）/C4（再节省）/C5（棘轮单调）/C6（drill 非零）。
- [x] 封装 `scripts/token_demo_e2e.sh`，末行 `DEMO PASS: C1..C6 all green`。

### 10.9 回归/联动脚本补新端点用例
- [x] `scripts/regression-smoke.cjs` / `linkage-smoke.cjs` 增覆盖：`/cost/tokens/{breakdown,trend,detail,lever-split,ratchet,ratchet/advance}`、`/skill-library/{duplicates,merge}`、`/cost/targets/*`、`/cost/report`、`twin-trials` 的 team_id 校验（非法 team→400）、`/llm/test-model` 留空回退。
- [x] **验收**：`node scripts/regression-smoke.cjs && node scripts/linkage-smoke.cjs` 全绿。

### 10.10 历史数据 team_id 规范化一次性扫描（配合 bug-049 的入口校验）
- [x] 一次性脚本扫描既有 `trials.json / evolution_runs / usage.db / skill_proficiency` 里的 team_id，对「连字符↔下划线、能按名匹配」的归一到真 team_id；真正孤儿（无对应团队）标注或移入 `storage/_cleanup_backup/`：
  ```python
  # scripts/normalize_team_ids.py — 复用 trial_api.resolve_team_id 的归一逻辑（team_manager 不可用时跳过）
  ```
- [x] **验收**：扫描报告列出归一/孤儿条目；效率视角不再出现幻影团队。

### 10.11 `trial_api.py` 多行 f-string 兼容性（可选硬化）
- **问题**：`trial_api.py` 约 L1248 的 SSE `yield f"data: {json.dumps({...多行...})}"` 用了跨行嵌套同引号 f-string，仅 Python ≥3.12 可编译；`pyproject` 要求 ≥3.11 → 3.11 环境会 SyntaxError。
- [x] 改为单行或先 `payload=json.dumps({...}); yield f"data: {payload}\n\n"`，使 3.11 也能编译。
- [x] **验收**：`python3.11 -m py_compile src/backend/sandbox/trial_api.py` 通过。

### ✅ Phase 10 自检（汇总）
```bash
# 1) 筛选透传
curl -s '.../cost/tokens/breakdown?dim=phase&team_id=build_system' | jq 'length'
# 2) 目标迁移后进度合理
curl -s '.../cost/targets/<id>/progress' | jq '{metric,baseline,current,progress}'
# 3) 回归脚本
node scripts/regression-smoke.cjs && node scripts/linkage-smoke.cjs
# 4) team_id 校验
curl -s -XPOST .../twin-trials -d '{"team_id":"ghost-team","task_goal":{},"mode":"what_if"}' | jq .detail   # 400 未知团队
# 5) 3D / Demo / 合并 为联机目检（见各节验收）
node scripts/check-docs-signoff.cjs   # 0 FAIL
```

> **优先级建议**：10.3（存量目标迁移，最小改动纠正旧目标）→ 10.1（筛选透传，用户最直观）→ 10.2（未归因治理）→ 10.5（实时回流）→ 10.4（score 扩展）→ 10.6/10.7/10.8 联机验收 → 10.9/10.10/10.11 硬化收尾。

---

## 离线可验证部分的执行结果（2026-06-20，对真实 `usage.db`/技能逻辑实跑）

> 用户列出的 Phase 7 / 10.6 / 10.7 / 10.8「需联机环境」中，**对账恒等式与合并逻辑实际可在无 LLM 下验证**；已实跑并记录结果，顺带发现并修复一个真实对账回归（bug-050）。

### ✅ 已离线验证（不需 LLM）
- **C1 跨维恒等**：`Σby_phase == Σby_team(全量) == summary.total`（实测 `120868 == 120868 == 120868`）。
  - ⚠️ **过程中发现真实回归（已修，bug-050）**：P10.2 让 `by_team` 默认剔除未归因 `team_id=''`，但 `by_phase` 含全部 → `cost_report` 全局对账恒 false。修法：`cost_report` 对账改用 `by_team(include_unattributed=True)` 同口径，并把未归因金额（101179）单列 `unattributed_tokens`。修后全局/团队 `reconciliation.consistent=true`。
- **C2 run 级一致**：3/3 run 的 `LEDGER.run(rid).total == DB 直查 SUM` ✅。
- **C3 技能卡一致**：抽样 skill 的 `by_skill.total == DB 直查` ✅。
- **10.7 合并逻辑**（`skill_evolver.merge_skills`，fixture 单测）：keep_longest 取较长 instructions、usage/success/fail 合并(15/9/6)、tools 并集、effectiveness 重算(0.6)、lineage 指向 primary、source=merged ✅。
- **10.6 静态契约**（非视觉）：流水线节点 `spipe-L1..L4`(+dot) JS↔HTML 一一对应、`_advancePipelineStage` 已接 SSE step、`_dt3dRewardPop` 已定义且被 `emitStepBarrage` 调用、停止标志 `_secsDevStop`+循环 break 已插、`buildRoom` 选中团队兜底渲染 agent ✅。

### ⛔ 仍需真实 LLM / 浏览器（代码无法替代）
- **C4 再节省 / C5 棘轮单调 / C6 drill 非零**：需真实 LLM 生成 Run A vs Run B 的新 token 数据来对比，沙箱无可达 LLM。
- **Phase 7 D2/D3 完整 Demo E2E**：同上，需运行环境 + LLM。
- **10.6 视觉验收**：议事厅是否真的显示 N 个 agent、奖励浮卡是否浮在对应 agent 头顶、流水线高亮是否随步进移动、停止是否生效 —— 需浏览器人工目检（静态契约已过）。
- **10.7 端到端 UI**：萃取页点「合并」→ 技能树技能数减少 —— 需浏览器（合并后端逻辑已单测通过）。
