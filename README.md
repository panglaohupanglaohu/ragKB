# AgentsGroup2026 — Agent 数字孪生平台

**系统目标：找出最有效能的智能体团队。** 效能 = 在给定任务上「完成质量 × 成功率」相对「token 成本」的性价比。围绕这个目标，平台提供两条互相咬合的路径：

1. **孪生演练路径**（对团队做实验）：团队先在数字孪生沙箱里演练、被混沌事件考验、评分对比、棘轮择优——用仿真代价筛出最能打的团队构型与策略，再进入生产。
2. **集体智慧路径**（对任务做规划）：Plaza 议事厅里多智能体讨论「如何完成这个任务」，形成结构化**执行计划**；计划经人确认与修改后，通过 人↔智能体、智能体↔智能体 的交互协作执行，执行结果再回流评估。

**两阶段经济学原则**：Plaza 集体智慧阶段**不做 token 优化**（智慧无价，讨论只求不跑题、计划能落地）；成本纪律从执行计划产生后开始——同一份计划在孪生沙箱对 团队×技能×协作 的多个候选组合反复试验（竞标），质量达标者中 token 效益最优的获得执行权。找到最好的团队、最优的技能与协作，正是数字孪生存在的意义。

```
                    ┌── Plaza 议事：怎么干？ ──→ 执行计划 ──→ 人确认/交互 ─┐
真实任务 ──┤                                                              ├──→ 协作执行 ──→ 效能评分
                    └── 孪生演练：谁来干？ ──→ 最优团队/策略 (Ratchet 锁定) ─┘         │
   ▲                                                                                  │
   └────────── 技能提取(SkillClaw)→验证→入库→路由复用 · token 归因/门禁 ←─────────────┘
```

## 系统组成：七个域与它们存在的理由

后端为单一 FastAPI 应用（`src/backend/main.py`，端口 8080），前端为多页面原生 JS + Three.js（Vite 构建，开发端口 5173）。约 96k 行 Python，98 个测试文件。每个域在「演练→进化→省钱执行」闭环中承担一个不可缺的角色：

**智能体团队（Team）** — 一切的载体。定义谁在干活：团队 → 成员 Agent（角色/系统提示词/绑定的模型、工具、技能、权限）→ 会话与任务。五步向导创建 Agent，运行时经 `chat_harness` + `runtime/tool_loop`（plan→act→observe→reflect）执行，权限上下文约束每个 Agent 能碰哪些工具。模块：`agents/api.py`、`agent_team_api.py`、`chat_harness.py`；API：`/api/v1/agent-teams`、`/api/v1/agent-config`。

**广场（Plaza）** — **集体智慧的场所：在这里讨论「如何完成任务」，并形成可执行的计划。** 主持人（Moderator）围绕任务话题带多轮结构化讨论：参与 Agent 按座席层级（内圈→中圈→外圈）依次发言、每轮多次交锋、主持人逐轮总结并收敛共识（`plaza_consensus`），全程 SSE 实时推流到 3D 圆桌页面。讨论的落点不是结论文本，而是**执行计划**：计划可由人审阅、修改、追问（人↔智能体交互），经桥接派发为真实任务后由多个 Agent 协作完成（智能体↔智能体交互，task bridge / evolution bridge），执行进度与结果回流讨论与演进。模块：`plaza_engine.py`、`plaza_routes.py`、`plaza_consensus.py`；API：`/api/v1/agent-config/plaza`。

**数字孪生沙箱（Twin Sandbox）** — 核心差异化能力：让团队先在仿真世界里犯错。`world_state` 把真实团队/任务/资源二次映射成世界快照，`twin_loop` spawn 出 Agent 孪生副本做并行 What-if 推演（支持混沌注入：断网、成员离场、技能退化、模型幻觉…），`orchestrator` 串起 快照→仿真→评估→对齐 全管线，试炼（trial）支持分支对比与代际演进，场景（scenario）把房间建模为业务阶段（状态机约束迁移）。产出是被验证过的策略/SOP，而不是猜测。模块：`sandbox/`；API：`/api/v1/sandbox`、`/api/v1/twin-trials`、`/api/v1/scenarios`。

**技能体系（Skills）** — 把「演练中学到的东西」变成可复用资产，这是省 token 的根本手段：好技能让便宜模型也能干对事。SkillClaw 流水线（Filter→Improve→Verify→Solidify）从演练/执行轨迹提取技能，`skill_verifier` 验证后入库，`skill_router` 用 BM25/TF-IDF 两阶段检索重排把 top-K 技能注入 Agent 提示词，`skill_tracker` 跟踪命中率反哺路由。模块：`skill_library.py`、`skill_router.py`、`skill_extractor.py`、`skill_evolver.py`；API：`/api/v1/skill-router`、`/api/v1/extraction`、`/api/v1/skill-classification`。

**成本与 Token 门禁（Cost）** — 北极星指标的度量与执法。所有 LLM 调用 token 经 `token_context` 归因到 团队/阶段/run_id，`cost_aggregator` 汇总，budget guard 扣减预算，cost-gate 在预算超限时阻断。演练消耗与生产消耗分列。旧的 Terraform 资源成本体系（`cost_policy.py`）为 LEGACY。API：`/api/v1/cost`、`/api/v1/cost-gate`、`/api/v1/token-factory`。

**系统演进（Evolution）** — 闭环的马达。`evolution/`（fitness/mutator/optimizer）对策略与技能做变异-评估-择优，**Ratchet 棘轮**保证只进不退：新策略必须在孪生对比中胜过基线才能锁定为新的代际（generation），成本效率棘轮同理。API：`/api/v1/twin-evolution`、`/api/v1/ratchet`、`/api/v1/sustainability`。

**运行时（Runtime）** — 各域共用的执行地基：`tool_loop`（多轮工具循环 + 上下文预算 + token 计量）、`plan_loop`、`state_machine`、runtime events。模块：`agents/runtime/`。

前端页面与域一一对应：`agent-team-config`（团队配置）、`plaza`（3D 圆桌议事）、`Agent-digital-twin`（试炼导演台：场景卡片/故障注入/分支/评分/反哺）、`sandbox-twin`（SECS 演练总台）、`digital-twin-cli`（命令行式孪生操作）、`skill-extract`（技能萃取）、`system-evolution`（演进看板）、`cost-dashboard`（token 成本治理）、`tasks`、`datacenter-ratchet-evolution`、`index`。

## 快速开始

要求：Node.js ≥ 22、Python ≥ 3.11。

macOS / Linux：

```bash
npm install
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
npm start          # 同时起后端(8080) + 前端 dev(5173)
```

Windows PowerShell：

```powershell
npm install
python -m venv venv; venv\Scripts\python.exe -m pip install -e ".[dev]"
npm start
```

`scripts/run-python.cjs` 会自动选择 `.venv` → `venv` → 系统 Python。也可用 `./start.sh` / `start.ps1`（含鉴权引导）。

## 验证命令

```bash
npm run lint        # python -m compileall（当前通过）
npm run typecheck   # 同上（无真正静态类型检查，见优化规划）
npm run build       # vite build
npm test            # 后端 + 根目录 pytest
npm run test:frontend   # vitest
```

当前基线状态以 [docs/VALIDATION.md](docs/VALIDATION.md) 为准；已知遗留失败（测试契约漂移等）记录在同一文件，修复计划见 [docs/OPTIMIZATION_TODOS_2026H2.md](docs/OPTIMIZATION_TODOS_2026H2.md)。**不要把历史计划文档中的能力描述当成已验证事实。**

## 文档导航

| 文档 | 用途 |
| --- | --- |
| [docs/README.md](docs/README.md) | 文档入口与可信度规则 |
| [docs/VALIDATION.md](docs/VALIDATION.md) | 验证基线与已知失败 |
| [docs/OPTIMIZATION_PLAN_2026H2.md](docs/OPTIMIZATION_PLAN_2026H2.md) | **当前优化规划**（孪生验证 + 最低 token 成本目标） |
| [docs/OPTIMIZATION_TODOS_2026H2.md](docs/OPTIMIZATION_TODOS_2026H2.md) | **当前 Todos**（按执行模型分层标注） |
| [docs/全仓库分阶段重构路线.md](docs/全仓库分阶段重构路线.md) | 工程收口重构路线 |
| [docs/archive/root-legacy](docs/archive/root-legacy) | 历史 README 与旧计划（仅参考） |

`docs/` 下 plan/todos 文件需签名头，规则见 [docs/SIGNING_RULE.md](docs/SIGNING_RULE.md)，校验：`node scripts/check-docs-signoff.cjs --strict`。

## 生态仿真范式（Perception → Intention → Behavior）

**本平台的根本设计哲学**：把「感知-意图-行为」闭环作为**所有 Agent 的通用运行时范式**，而不是某个 demo 模块。猫小虎 + 鼠吱吱的 Predator/Prey 演示只是这个范式的**第一个具体实例**，用来验证可行性——真正的目标是让 Plaza 议事、孪生演练、skill 调用、任务协作全都从生态仿真视角来看。

### 范式定义

每个 Agent 在每个 tick 走统一闭环：

```
感知 (Perception)   →  从环境/上下文/他者提取信号（视野、消息、状态、token 预算…）
意图生成 (Intention) →  基于内部心理状态 + 感知信号，按优先级生成当前意图（avoid > hunt/escape > wander 的泛化）
行为 (Behavior)     →  执行意图对应的例程（工具调用、发言、移动、技能触发…），产出可观测动作
```

心理状态（Hunger/Fear 的泛化：紧迫度、信心、预算压力…）让 Agent 有**内部驱动**而非纯反应式；单项短期记忆 + 持久化阈值防抖动，让意图稳定不横跳。

### 与现有子系统的对齐路线

| 子系统 | 现状 | 生态仿真范式下的目标 |
| --- | --- | --- |
| **Agent 运行时** | `chat_harness` + `tool_loop` 走 plan→act→observe→reflect | 改造为 perception→intention→behavior 闭环，plan/act 是"行为例程"的展开 |
| **skill 体系** | SkillRouter 用 BM25/TF-IDF 检索关键词注入 prompt | skill = "可复用行为例程库"，按**意图**路由而非关键词匹配 |
| **Plaza 协作** | 主持人 + 座席层级 + 结构化发言 | 多 Agent **意图协调**：感知他人意图 → 调整自己意图 → 协调行为 |
| **孪生沙箱** | twin_loop spawn 副本做 What-if 推演 | What-if = "多 Agent 意图-行为"仿真，混沌注入 = 扰动感知/心理状态 |

### 第一个实例：3D 办公室 Predator/Prey

[`Agent-digital-twin.html?office3d=1`](src/frontend/Agent-digital-twin.html) 的猫鼠场景是这个范式的参考实现：小虎（predator）饥饿到阈值进入 hunt，吱吱（prey）恐惧超阈值进入 escape，碰撞敏感区临时 avoid 并单项记忆防抖，捕获后吱吱瞬移远角、小虎念得意台词 + TTS 播报。所有参数（role/perception/mental_state/intention/voice）由 [`storage/pet_config.json`](storage/pet_config.json) 配置驱动，[`pet-config.html`](src/frontend/pet-config.html) 页面编辑，[`PetEcosystem`](src/backend/agents/pet_ecosystem.py) 单例管理，文件缺失自动落盘 `_DEFAULT_SEED`。

### 工程支撑

- **TTS 语音**：edge-tts / gpt-sovits / browser 三 provider，全由页面配置驱动，前端无兜底默认值，缺字段由 [`validateVoiceConfig`](src/frontend/js/office/voice-config-validator.js) 抛错暴露；CSP 已放行 `media-src 'self' data: blob:`。
- **模型凭据**：`api_key` 支持 `env:VAR_NAME` 前缀引用环境变量（落盘原样保留，真实 key 脱敏不入库），[`setup_keys.sh`](scripts/setup_keys.sh) / [`setup_keys.ps1`](scripts/setup_keys.ps1) 提供交互式创建，[`env_loader.py`](src/backend/agents/env_loader.py) 启动时加载 `.env`。

详细设计与路线图见 [docs/宠物团队生态仿真plan.md](docs/宠物团队生态仿真plan.md)（§10 Phase I 是泛化路线），任务追踪见 [docs/宠物团队生态仿真todos.md](docs/宠物团队生态仿真todos.md)。

## 核心概念速查

- **TwinLoop**（`sandbox/twin_loop.py`）：snapshot_world → spawn_twins → run_simulation → evaluate_outcomes → inject_best_strategy 的仿真在环闭环；支持混沌注入与熟练度结算。
- **SECS 演练**：团队 + 场景驱动的 演练→评估→进化 循环，SSE 实时推流到 3D 前端。
- **SkillRouter**：BM25/TF-IDF 双阶段检索重排，把 top-K 技能注入 agent system prompt（无 GPU 依赖）。
- **SkillClaw 流水线**：Filter → Improve → Verify → Solidify，从演练轨迹提取技能并验证后入库。
- **Token 北极星**：新成本体系以 token 为唯一口径（`token_policy.py` + cost-gate）；`cost_policy.py` 的 Terraform 成本规则为 LEGACY。
- **Ratchet（棘轮）**：演进只进不退——新策略必须在孪生环境中证明优于基线才允许发布。

## 部署

Docker：`Dockerfile` + `docker/`；K8s：`k8s/`（含成本标签 mutating webhook）。可观测性：可选 OpenTelemetry（`pip install -e ".[otel]"`）。
