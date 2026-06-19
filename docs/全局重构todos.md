<!-- docs-signoff: author="GitHub Copilot" kind="llm" doc="todos" ts="2026-06-19T00:07:00Z" -->

# 全局重构 TODOS — 以「Token 最少」为北极星（交接级 · 事无巨细 + 真实代码锚点）

> 配套 [全局重构plan.md](全局重构plan.md)。
> **北极星**：让 Agent 团队在达成业务场景目标的前提下，消耗的 Token 最少。
> **成本 = LLM Token**（技能形成 / 技能验证 / 数字孪生演练 / 议事辩论 / 任务执行），**不是** Terraform/EC2 基础设施账单。
>
> **给接手者（codebuddy）的三条铁律**：
> 1. **进程内归因，不是 Pod sidecar**。已代码核实：技能验证 / 孪生演练的 LLM 调用都发生在**后端编排进程**（`chat_harness.chat`），沙箱 Pod 里只跑**确定性校验脚本（零 LLM 调用）**。所以 Token 探针 = 进程内 `contextvars` 归因层，绝不要去拦截 Pod 出站流量（拦不到）。
> 2. **K8s 解耦可选**。本机常态无 K8s，所有沙箱必须能自动降级 docker/lite，进程内探针始终工作。K8s 不是北极星前置依赖。
> 3. **每个 Phase 独立可交付、可回退**，末尾留一个最小可运行自检（`✅自检`）。先 P1 止血，再按 `P1 →（P2 ∥ P4）→ P5 → P6`，P3 随时可插。

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
- [ ] **0.4** 后续每完成一个 Phase，回写本文件勾选状态并把 sign-off `ts` 更新为完成时刻（`date -u +%Y-%m-%dT%H:%M:%SZ`），跑 `node scripts/check-docs-signoff.cjs` 确认 0 FAIL。

---

## Phase 1 · TokenLedger 打通（最高 ROI · 零新基建 · 本机无 OpenCost 也能看真实 Token）

### 1.1 `UsageRecord` 增加归因字段
- [ ] `src/backend/agents/budget/models.py`：给 `UsageRecord` dataclass 加 4 个**带默认值**的字段（放在 `cost_usd` 之后、`timestamp` 之前，避免无默认值字段排序报错）：
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
- [ ] `src/backend/agents/budget/store.py::UsageStore._ensure_schema()`：在 `executescript` 之后追加幂等迁移（旧库已存在 `usage_log` 时补列）：
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
- [ ] `store.py::record_usage()`：INSERT 补 4 列：
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
- [ ] 新增 `src/backend/agents/token_context.py`：
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
- [ ] `src/backend/agents/chat_harness.py` 记账漏斗处（约 L1015，`budget_guard.record_usage(UsageRecord(...))`）合并上下文（**显式入参优先，contextvar 兜底**）：
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
- [ ] 新增 `src/backend/agents/token_ledger.py`（直接读 `storage/usage.db`，复用 `UsageStore.path`）：
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
- [ ] `src/backend/agents/cost_routes.py` 增加（沿用现有 router 前缀 `/api/v1/cost`）：
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
- [ ] `/cost/summary` 增 `source` 参数：`source=token`（默认，走 Ledger）/`source=infra`（走 OpenCost `cost_aggregator`）。OpenCost 无数据时返回空列表 + `"degraded": true`，**不**抛错、不返回非 200。

### 1.6 前端：成本页主数据源切 Token
- [ ] `src/frontend/js/cost-dashboard.js::refreshDashboard()`（或等价主刷新函数）主源切到 token：
  ```js
  const win = state.window || '24h';
  const tok = await requestJson(`${COST_API}/tokens/summary?group_by=team&window=${win}`);
  state.tokenByTeam = tok.items || [];
  renderKpiHero();          // 改为 token 维度
  renderTeamTable();        // team_id / total_tokens / calls / efficiency(score/1k)
  // OpenCost health/pods 仅在 source=infra 或显式切换时拉，无数据不渲染红条
  ```
- [ ] KPI Hero 四块改 Token 维度：① 窗口总 Token ② 最贵团队（Top team_id + token）③ 平均 score/1k ④ 棘轮已锁定的累计节省（来自 ratchet `cost_efficiency:*`）。
- [ ] 「效率视角」用 `/tokens/by-team` 的 `efficiency` 倒序排名；缺 score 的行显示「—」不参与排名。
- [ ] 删除/降级 OpenCost「无成本数据」红条：无数据时显示中性「基础设施成本未接入（可选）」。

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
- [ ] 新增 `src/backend/agents/token_policy.py`：
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
- [ ] 新增 `src/backend/agents/token_gate_routes.py`：
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
- [ ] `src/backend/agents/cost_gate_routes.py`：把现有 Terraform `evaluate` 迁到 `POST /cost-gate/terraform/evaluate`；保留 `/cost-gate/stats`、`/cost-gate/health` 转发到 token 版（默认 token 语义）。

### 2.3 前端治理语义改 token
- [ ] `js/cost-dashboard.js::runCostGateSelfCheck()` 改调 `/cost-gate/token/evaluate`，用当前 Top 团队最近一次 run（无 run_id 时用 `inline` 拼 `{total, score}`）。
- [ ] 「当前治理目标」从 OpenCost breakdown 改为 **token 最贵团队/技能**：
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

## Phase 3 · K8s Pod 沙箱（可选隔离升级；解耦、不阻塞北极星）
> **前提**：Pod 只跑**确定性校验脚本，无 LLM 调用，不产生也不采集 token**；token 归因已在 P1 进程内完成。本 Phase 仅升级执行隔离/可复现，仅在已有 kind 集群时启用，否则可延后。**不要在这里写任何 token 采集逻辑。**

### 3.1 KubernetesSandbox
- [ ] 新增 `src/backend/sandbox/k8s_runner.py`（继承 `LiteSandbox`，复用 `SandboxResult`；**不涉 token**）：
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
- [ ] `src/backend/sandbox/python_runner.py::get_sandbox()` 支持 `mode=k8s` + 自动降级（现有 `get_sandbox()` **无参**，加可选 `mode` 形参，默认 `None` 走 `CONFIG.mode`，保持旧调用兼容）：
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
- [ ] `config/settings.json` 的 `sandbox` 段增 `k8s` 子段：`{namespace, image, job_ttl, cpu, mem}`。`load_sandbox_config()` 读取并填入 `SandboxConfig.k8s`。

### 3.2 统一沙箱入口（run_id 编排；探针本体在 P1）
> 本节只补「统一 run 入口」，把 `token_scope` 包到验证/演练执行外层。**读出仍用 `LEDGER.run(run_id)`，不新建 token_probe 模块。**
- [ ] 新增统一入口路由 `POST /api/v1/sandbox/runs`：
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
- [ ] `src/backend/agents/skill_verifier.py::verify_skill(team_id, skill_id, provider_config)`：用 `token_scope` 包裹整段（`_generate_tests` 的 LLM 调用就此归因）：
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
- [ ] verified→granted 流程加 Gate 闸门：`block` 拦截不授予；`warn` 允许但标记需人工复核；`pass` 正常授予。

### 4.2 数字孪生演练接 Ledger + Gate + **跨线程 contextvar 修复（关键）**
- [ ] **修复 `src/backend/sandbox/orchestrator.py::_llm_decision_wrapper()`**：`ThreadPoolExecutor` 不会传播 contextvar，必须显式 `copy_context()`，否则孪生 token 归因为 0：
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
- [ ] `src/backend/sandbox/orchestrator.py::run_full_pipeline(session_id)`（或 `create_session`/`twin_loop.run_simulation` 外层）包 run_id：
  ```python
  run_id = new_run_id("drill")
  with token_scope(run_id=run_id, phase="drill",
                   scenario_id=scenario_id, team_id=team_id):
      self.twin_loop.run_simulation(...)
      self.aligner.align_session(...)
  run = LEDGER.run(run_id)
  gate = ENGINE.evaluate(run, budget=_drill_budget(scenario_id))  # DRILL_TOKEN_BURST 检测
  ```
- [ ] passed→ratchet-lock 前调 Gate：`block` 不锁定；分支结构（`parallel_branches`）与故障场景（`chaos_engine`）产生的 LLM 决策 token 全部归因到该 run_id。

### 4.3 sustainability / ratchet 切真实源
- [ ] `src/backend/agents/sustainability.py`：`tokens_consumed` 改取 `LEDGER.by_team(window)`（替代 proficiency 估算 / 800-token 兜底）；token_efficiency = score / (tokens/1k) 用真实 token。
- [ ] 达标的 token 节省 push `cost_efficiency:{team_id}` 进 `src/backend/agents/ratchet_ledger.py`（只进不退）。

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
- [ ] 新增 `src/backend/agents/cost_targets.py`：
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
- [ ] 成本页新增「设定 Token 优化目标」表单：选团队/技能 → 选指标 → 填目标值 → 选杠杆 → 提交。
  ```js
  async function createTokenTarget() {
    const body = { scope, ref_id, metric, target: Number(val), lever };
    await requestJson(`${COST_API}/targets`, { method:'POST', body: JSON.stringify(body) });
    renderTargets();   // 目标卡片：进度条 + 当前/目标 + 杠杆
  }
  ```
- [ ] 「创建优化任务 / 创建 Plaza 话题」携带该目标与杠杆建议，正向推动 token 下降。

### ✅ Phase 5 自检
```bash
TID=$(curl -s -XPOST localhost:8000/api/v1/cost/targets \
  -d '{"scope":"team","ref_id":"default","metric":"score_per_1k","target":3.0,"lever":"skill_extraction"}' | jq -r .id)
curl -s "localhost:8000/api/v1/cost/targets/$TID/progress" | jq '{baseline,current,progress}'
```

---

## Phase 6 · 清理与收口
- [ ] `src/backend/agents/cost_policy.py`、`src/backend/ci_cost_gate.py` 顶部加注释：`# LEGACY: Terraform 资源成本，与 Token 北极星无关，仅 CI 兼容保留`（**不删**，避免破坏既有 CI）。
- [ ] 主页面 / 导航统一「成本 = Token」表述；复核 OpenCost 无数据时不再喧宾夺主（P1 已降级）。
- [ ] 更新 README「API 参考」「项目结构」，加入 `token_ledger.py` / `token_context.py` / `token_policy.py` / `token_gate_routes.py` / `cost_targets.py` / `k8s_runner.py`（标可选）。
- [ ] 回归脚本增 token 链路用例：`scripts/regression-smoke.cjs`、`scripts/linkage-smoke.cjs` 覆盖 `/cost/tokens/*` 与 `/cost-gate/token/*`。

### ✅ Phase 6 自检
```bash
node scripts/check-docs-signoff.cjs          # 0 FAIL
node scripts/regression-smoke.cjs            # 含 token 路由用例
node scripts/linkage-smoke.cjs
```

---

## 全局验收（与 plan §7 对齐）
- [ ] **A1** 本机无 OpenCost 也显示真实 Token 成本，无红条。
- [ ] **A2** `/cost/tokens/by-team` 与 `usage.db` 聚合一致（脚本核对）。
- [ ] **A3** 验证 token 可按 run 查并归因 skill→agent→team（`/cost/tokens/run/{run_id}`）。
- [ ] **A4** 高 token 低 score 的 run 被 Gate WARN/BLOCK。
- [ ] **A5** `mode=k8s` 有/无 K8s 都能完成 skill_verify 且记账（有则起 Pod，无则降级）。
- [ ] **A6** 孪生演练 token 在子线程正确归因（`by_phase.drill > 0`，验证 contextvar 跨线程修复生效）。
- [ ] **A7** 设定目标 → 派发任务 → 进度可见 → 棘轮锁定 `cost_efficiency:{team_id}`。

---

## 接手顺序建议（给 codebuddy）
1. **先 P1**（1.1→1.2→1.3→1.4→1.5→1.6），跑 ✅Phase1 自检，确认本机能看到 token——这一步独立止血。
2. **P4 的 4.2 跨线程修复优先于其余 P4**：先写「子线程能读到 token_scope」的断言自检，再接验证/演练。
3. P2 与 P4 可并行；P5 依赖 P1 的 Ledger；P3（K8s）随时可插，不阻塞。
4. P6 收口 + 全局验收。
5. 每个 Phase 完成回写本文件勾选 + 更新 sign-off `ts`，跑 `node scripts/check-docs-signoff.cjs`。
