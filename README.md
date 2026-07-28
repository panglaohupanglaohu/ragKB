# AgentsGroup2026 — Agent 数字孪生平台

> **一句话**：找出最有效能的智能体团队。效能 = 在给定任务上「完成质量 × 成功率」相对「token 成本」的性价比。

平台围绕这个目标提供两条互相咬合的路径：

1. **孪生演练路径（对团队做实验）** — 团队先在数字孪生沙箱里演练、被混沌事件考验、评分对比、棘轮择优，用仿真代价筛出最能打的团队构型与策略，再进入生产。
2. **集体智慧路径（对任务做规划）** — Plaza 议事厅里多智能体讨论「如何完成这个任务」，形成结构化**执行计划**；计划经人确认与修改后，通过人↔智能体、智能体↔智能体协作执行，结果回流评估。

**两阶段经济学**：Plaza 集体智慧阶段**不做 token 优化**（智慧无价，讨论只求不跑题、计划能落地）；成本纪律从执行计划产生后才开始——同一份计划在孪生沙箱对「团队 × 技能 × 协作」的多个候选组合反复竞标，质量达标者中 token 效益最优的获得执行权。

```
                ┌── Plaza 议事：怎么干？ ──→ 执行计划 ──→ 人确认/交互 ─┐
真实任务 ──┤                                                          ├──→ 协作执行 ──→ 效能评分
                └── 孪生演练：谁来干？ ──→ 最优团队/策略 (Ratchet 锁定) ─┘        │
   ▲                                                                             │
   └──── 技能提取(TSE)→验证→入库→路由复用 · token 归因/门禁 ←────────────────────┘
```

---

## 技术栈与规模

| 项 | 说明 |
| --- | --- |
| 后端 | 单一 FastAPI 应用（`src/backend/main.py`，端口 **8080**，30 个路由域），约 **133k 行 Python** |
| 前端 | 多页面原生 JS + Three.js，Vite 构建（开发端口 **5173**），16 个页面 |
| 测试 | 后端 102 + 根目录 47 + 前端 46 个测试文件 |
| 依赖 | Python ≥ 3.11（fastapi/uvicorn/pydantic/httpx/cryptography/edge-tts）· Node.js ≥ 22（vite/vitest/three/playwright） |
| 神经组件 | TSE 技能萃取管线为 pure-numpy 实现（TCN + Skill Query Attention），无 GPU 依赖 |

---

## 目录结构

```
src/
  backend/
    main.py              FastAPI 入口（鉴权 / CORS / 静态托管 / 30 路由注册）
    agents/              核心域（~180 个模块）
      teams/  api.py     团队与 Agent 配置、chat_harness 运行时
      plaza*.py          Plaza 议事引擎（engine/consensus/stream/store/routes）
      tse/               TSE 技能萃取管线（TCN + attention + 约束解码）
      skill_*.py         技能库/路由/验证/演化/分类/追踪
      runtime/           tool_loop / plan_loop / state_machine（各域共用执行地基）
      evolution/         fitness / mutator / optimizer + Ratchet 棘轮
      token_governance/  任务 token 治理（prepare 管线 + lever catalog）
      budget/            预算门禁
      agent_memory_*.py  拟生记忆（core/lifecycle/share/transfer/runtime）
      pet_ecosystem.py   生态仿真（Perception→Intention→Behavior 范式实例）
      cost_*.py          成本归因/报表/门禁（token 北极星 + LEGACY Terraform）
    sandbox/             数字孪生沙箱（twin_loop / orchestrator / eco_drill / scenario）
    tests/               后端测试（102 文件）
  frontend/
    *.html               16 个页面（见下表）
    js/  css/            页面逻辑与样式
    __tests__/           vitest 前端测试（46 文件）
docs/                    plan/todos 设计文档（需签名头，见 SIGNING_RULE.md）
config/                  settings.json / model_pool.json / users.json 等
storage/                 运行时状态落盘（技能库/记忆/棘轮/eco 配置…）
scripts/                 训练/评估/运维脚本 · run-python.cjs（解释器选择）
docker/  k8s/            部署（K8s 含成本标签 mutating webhook）
tests/                   根目录集成测试（47 文件）
```

---

## 七个域

后端按域组织，每个域在「演练 → 进化 → 省钱执行」闭环中承担一个不可缺的角色。

| 域 | 存在理由 | 关键模块 | API 前缀 |
| --- | --- | --- | --- |
| **团队 Team** | 一切的载体：定义谁在干活（团队 → 成员 Agent → 会话/任务）。运行时经 `chat_harness` + `runtime/tool_loop`（plan→act→observe→reflect）执行 | `agents/api.py`、`agent_team_api.py`、`chat_harness.py` | `/api/v1/agent-teams`、`/api/v1/agent-config` |
| **广场 Plaza** | 集体智慧的场所：讨论「如何完成任务」并形成可执行计划。主持人带多轮结构化讨论，SSE 实时推流到 3D 圆桌 | `plaza_engine.py`、`plaza_consensus.py`、`plaza_routes.py` | `/api/v1/agent-config/plaza` |
| **孪生沙箱 Twin** | 核心差异化：让团队先在仿真世界里犯错。`world_state` 映射快照，`twin_loop` spawn 副本做 What-if 推演（支持混沌注入），`orchestrator` 串起全管线 | `sandbox/twin_loop.py`、`orchestrator.py`、`eco_drill.py` | `/api/v1/sandbox`、`/api/v1/twin-trials`、`/api/v1/scenarios` |
| **技能 Skills** | 把演练所学变成可复用资产（省 token 的根本手段）。TSE 管线萃取 → 验证 → 入库 → BM25/TF-IDF 两阶段路由注入提示词 | `agents/tse/`、`skill_extractor.py`、`skill_router.py`、`skill_verifier.py`、`skill_evolver.py` | `/api/v1/teams/{id}/skill-extract/*`、`/api/v1/skill-router` |
| **成本 Cost** | 北极星指标的度量与执法。所有 LLM token 经 `token_context` 归因；任务 Token 治理在 `prepare_request` 管线做简化/压缩/缓存/路由/预算 | `token_governance/`、`cost_routes.py`、`token_context.py`、`budget/` | `/api/v1/cost`、`/api/v1/cost/token-governance/*`、`/api/v1/cost-gate` |
| **演进 Evolution** | 闭环的马达。对策略与技能做变异-评估-择优；**Ratchet 棘轮**保证只进不退（新策略须在孪生对比中胜出才锁定为新代际） | `evolution/`、`ratchet_ledger.py` | `/api/v1/twin-evolution`、`/api/v1/ratchet`、`/api/v1/sustainability` |
| **运行时 Runtime** | 各域共用的执行地基：多轮工具循环 + 上下文预算 + token 计量 + 状态机 | `agents/runtime/`（tool_loop / plan_loop / state_machine） | — |

### 前端页面（与域对应）

| 页面 | 职责 |
| --- | --- |
| `index` | 站点入口导航 |
| `agent-team-config` | 团队配置（五步向导创建 Agent） |
| `plaza` | 3D 圆桌议事 |
| `Agent-digital-twin` | 试炼导演台：场景卡片/故障注入/分支/评分/反哺（`?office3d=1` 为生态仿真视图） |
| `sandbox-twin` | SECS 演练总台 |
| `digital-twin-cli` | 命令行式孪生操作 |
| `skill-extract` | 技能萃取与审核队列 |
| `extraction-pipeline` | 萃取流水线视图 |
| `system-evolution` | 演进看板 |
| `cost-dashboard` | token 成本治理工作台 |
| `agent-memory` | 拟生记忆总览 |
| `pet-config` | 生态仿真参数编辑 |
| `datacenter-ratchet-evolution` | 数据中心棘轮演进 |
| `tasks` | 任务 |
| `login` | 鉴权 |

---

## 快速开始

要求：Node.js ≥ 22、Python ≥ 3.11。

**macOS / Linux**
```bash
npm install
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
npm start          # 同时起后端(8080) + 前端 dev(5173)
```

**Windows PowerShell**
```powershell
npm install
python -m venv venv; venv\Scripts\python.exe -m pip install -e ".[dev]"
npm start
```

`scripts/run-python.cjs` 自动选择 `.venv` → `venv` → 系统 Python。也可用 `./start.sh` / `start.ps1`（含鉴权引导）。

---

## 验证命令

```bash
npm run lint        # python -m compileall（当前通过）
npm run typecheck   # 同上（无真正静态类型检查，见优化规划）
npm run build       # vite build
npm test            # 后端 + 根目录 pytest
npm run test:frontend   # vitest
```

当前基线状态以 [docs/VALIDATION.md](docs/VALIDATION.md) 为准；已知遗留失败与修复计划见 [docs/OPTIMIZATION_TODOS_2026H2.md](docs/OPTIMIZATION_TODOS_2026H2.md)。**不要把历史计划文档中的能力描述当成已验证事实。**

---

## 核心机制速查

- **TwinLoop**（`sandbox/twin_loop.py`）：snapshot_world → spawn_twins → run_simulation → evaluate_outcomes → inject_best_strategy 的仿真在环闭环；支持混沌注入与熟练度结算。
- **物竞天择 / EcoDrill**（`sandbox/eco_drill.py`）：以「生存时长 $T_i$」为唯一适应度，任务契约 demand 过滤，加压旋钮（性选择/频依/上位/衰老等）让匹配的 skill 与稀缺时的协作活得更久。完整公式与旋钮见 [docs/物竞天择任务闭环与Skill遗传plan.md](docs/物竞天择任务闭环与Skill遗传plan.md)。
- **SkillRouter**：BM25/TF-IDF 双阶段检索重排 + lifecycle 加权，把 top-K 技能注入 Agent system prompt（无 GPU 依赖）。
- **TSE 技能萃取**：TCN 时序卷积 + Skill Query Attention 定位「技能时刻」→ 约束 JSON 解码成结构化 skill → 人审入库。`llm_model_used` 以 `tse+` 开头即走了神经路径。设计见 `methodology.md` / `reasoning.md`。
- **Token 北极星**：新成本体系以 token 为唯一口径（`token_governance` prepare 管线 + cost-gate）；`cost_policy.py` 的 Terraform 成本规则为 LEGACY。prepare 管线：`simplify → ponytail/caveman → rtk_tool → compress → progressive_mem → codegraph → cache → skill → cost_tier+model → budget`。
- **拟生记忆**：可拥有/共享/传递/销毁的动态记忆（感觉痕迹/情节/语义核/工作台层 + 情绪电荷场 + 前瞻意图过程），感情作为选择压驱动巩固与遗忘。设计见 [docs/拟生记忆架构plan.md](docs/拟生记忆架构plan.md)。
- **生态仿真范式**：把「感知-意图-行为」闭环作为所有 Agent 的通用运行时范式；`Agent-digital-twin.html?office3d=1` 的猫鼠 Predator/Prey 是第一个具体实例。设计见 [docs/宠物团队生态仿真plan.md](docs/宠物团队生态仿真plan.md)。
- **Ratchet 棘轮**：演进只进不退——新策略必须在孪生环境中证明优于基线才允许发布。

---

## 文档导航

| 文档 | 用途 |
| --- | --- |
| [docs/README.md](docs/README.md) | 文档入口与可信度规则 |
| [docs/VALIDATION.md](docs/VALIDATION.md) | 验证基线与已知失败 |
| [docs/OPTIMIZATION_PLAN_2026H2.md](docs/OPTIMIZATION_PLAN_2026H2.md) | 当前优化规划（孪生验证 + 最低 token 成本目标） |
| [docs/OPTIMIZATION_TODOS_2026H2.md](docs/OPTIMIZATION_TODOS_2026H2.md) | 当前 Todos（按执行模型分层标注） |
| [docs/任务Token治理plan.md](docs/任务Token治理plan.md) | 任务 Token 治理设计（prepare 管线 + 杠杆目录） |
| [docs/拟生记忆架构plan.md](docs/拟生记忆架构plan.md) | Agent 拟生记忆架构 |
| [docs/物竞天择任务闭环与Skill遗传plan.md](docs/物竞天择任务闭环与Skill遗传plan.md) | 物竞 v4：任务契约 → 生境 → Skill 遗传（含完整公式） |
| [docs/宠物团队生态仿真plan.md](docs/宠物团队生态仿真plan.md) | 生态仿真范式（Perception→Intention→Behavior） |
| [docs/全仓库分阶段重构路线.md](docs/全仓库分阶段重构路线.md) | 工程收口重构路线 |

`docs/` 下 plan/todos 文件需签名头，规则见 [docs/SIGNING_RULE.md](docs/SIGNING_RULE.md)，校验：`node scripts/check-docs-signoff.cjs --strict`。

---

## 部署

Docker：`Dockerfile` + `docker/`；K8s：`k8s/`（含成本标签 mutating webhook）。可观测性：可选 OpenTelemetry（`pip install -e ".[otel]"`）。

模型凭据：`api_key` 支持 `env:VAR_NAME` 前缀引用环境变量（真实 key 脱敏不入库），`scripts/setup_keys.sh` / `setup_keys.ps1` 提供交互式创建，`env_loader.py` 启动时加载 `.env`。
