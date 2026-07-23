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

**技能体系（Skills）** — 把「演练中学到的东西」变成可复用资产，这是省 token 的根本手段：好技能让便宜模型也能干对事。**从 Plaza 讨论萃取技能**走 **TSE 管线**（TCN 时序神经 + Skill Query Attention + 约束 JSON 解码，见 [技能萃取（TSE 管线）](#技能萃取tse-管线)）；入库后 `skill_verifier` 验证，`skill_router` 用 BM25/TF-IDF 两阶段检索重排把 top-K 技能注入 Agent 提示词，`skill_tracker` 跟踪命中率反哺路由。模块：`agents/tse/`、`skill_extractor.py`、`skill_library.py`、`skill_router.py`、`skill_evolver.py`；API：`/api/v1/teams/{team_id}/skill-extract/*`、`/api/v1/skill-router`、`/api/v1/extraction`、`/api/v1/skill-classification`。页面：`skill-extract`。

**成本与 Token 门禁（Cost）** — 北极星指标的度量与执法。所有 LLM 调用 token 经 `token_context` 归因到 团队/阶段/run_id；**任务 Token 治理**在 `prepare_request` 管线做简化/压缩/缓存/路由/预算（详见 [任务 Token 治理](#任务-token-治理)）。budget guard 扣减预算，cost-gate 在预算超限时阻断。Plaza 讨论阶段**不做** token 优化。旧的 Terraform 资源成本体系（`cost_policy.py`）为 LEGACY。API：`/api/v1/cost`、`/api/v1/cost/token-governance/*`、`/api/v1/cost-gate`。

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
| [docs/物竞天择任务闭环与Skill遗传plan.md](docs/物竞天择任务闭环与Skill遗传plan.md) | 物竞 v4：任务契约 → 生境 → Skill 遗传 |
| [docs/物竞闭环评估报告-aws-build.md](docs/物竞闭环评估报告-aws-build.md) | AWS×Build 闭环 LOOP 评估样例 |
| [docs/全仓库分阶段重构路线.md](docs/全仓库分阶段重构路线.md) | 工程收口重构路线 |
| [docs/archive/root-legacy](docs/archive/root-legacy) | 历史 README 与旧计划（仅参考） |
| 下文 [技能萃取（TSE 管线）](#技能萃取tse-管线) | Plaza→技能：TSE 架构、与 LLM 关系、可用性与训练 |

根 README 内嵌公式摘要见上文 **「物竞天择：适应度、加压 12 钮与公式」**。

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

## 物竞天择：适应度、加压 12 钮与公式

办公室视图试验田（[`Agent-digital-twin.html?office3d=1`](src/frontend/Agent-digital-twin.html)）把团队放入**自然选择生境**：任务契约是客观考卷（同一 demand 过滤），**不是天选任务**。环境不打分；只通过健康账本与生存时长筛选「匹配且干活的 skill」与「稀缺时能救命的协作」。内核：`sandbox/eco_drill.py`；配置：`storage/eco_runtime_config.json`（`GET/PUT /api/v1/eco-runtime/config`）；左侧音量旋钮与 [`pet-config.html`](src/frontend/pet-config.html) 深参同键。

赛制语义：①分场＝多队比个体 skill；②多队对抗＝比协作/策略；③混合＝个体+团队（世界杯）。加对比种群**不**自动改赛制。

### 唯一适应度

\[
T_i \;=\; \sum_{t=1}^{t_{\mathrm{death}}} \mathbf{1}\{\text{agent } i \text{ alive at tick } t\}
\]

选择只看 \(T_i\)（活得久）。不另设 skill 分、协作分。

### 每 tick 健康（示意）

\[
H_{i,t+1}
=
H_{i,t}
- m
- c\cdot |G_i|
- \lambda\cdot \mathbf{1}\{\mathrm{can\_serve}\land \mathrm{REST}\}
- \mu_{\mathrm{sen}}\cdot T_i^{\mathrm{so\,far}}
- C(\mathrm{act}_{i,t})
+ R_{i,t}
- P_{i,t}
\]

| 符号 | 含义 | 配置键 |
| --- | --- | --- |
| \(m\) | 基础代谢 | `metabolism.metabolic_rate` |
| \(G_i\) | skill 基因组 | agent 携带 skills |
| \(c\) | 每 skill 每 tick 囤积税 | `evolution_pressure.genome_carry_cost` |
| \(\lambda\) | 能 serve 却 REST 的闲置税 | `evolution_pressure.skill_idle_penalty` |
| \(\mu_{\mathrm{sen}}\) | 衰老：每已存活 tick 额外代谢（**Agent 侧**） | `metabolism.senescence_rate` |
| \(C\) | 动作成本（觅食 miss / 信号 / 避险等） | `drill_economics.*` |
| \(R\) | 觅食命中（含频依/上位放大）、收分享等收益 | 见下 |
| \(P\) | 事故/捕食伤害 | 生境 `predator_pressure` + 偏压 \(\beta\) |

\(H\le 0\Rightarrow\) 死亡，\(T_i\) 封顶。

### 能否 serve 与觅食

\[
\mathrm{can\_serve}_{i,t}
=
\mathbf{1}\{ G_i \cap D_t \neq \emptyset \}
\]

\(D_t\)：当前生态位 demand（任务契约 niches / `TaskHabitatContract`）。

\[
R^{\mathrm{forage}}_{i,t}
=
\begin{cases}
a\cdot g & \text{FORAGE 且 can\_serve 且命中}\\
0 & \text{否则}
\end{cases}
\]

- \(a=\) `habitat.abundance`（丰饶度 ≈ token 松紧）  
- \(g=\) `drill_economics.forage_gain`  
- 命中率随熟练度与跟随 `follow_bonus` 上升  

意图加压（0/1）：

\[
\mathrm{REST}
\;\xrightarrow{\pi=1}\;
\mathrm{FORAGE}
\quad\text{当 can\_serve 且略饿},\quad
\pi=\texttt{prefer\_forage\_when\_can\_serve}
\]

### 事故偏压（无 skill 更易中）

\[
\mathbb{P}(\text{事故打中 } i)
\propto
1 + \beta\cdot \mathbf{1}\{\neg\mathrm{can\_serve}_{i,t}\}
\]

\(\beta=\) `predator_bias_unskilled`；事故是否发生由 `habitat.predator_pressure` 控制。

### 协作分享

\[
R^{\mathrm{share}}_{j\leftarrow i}
=
r_i\cdot f\cdot
\bigl(1 + s\cdot \mathbf{1}\{a<1\}\cdot(1-a)\bigr)
\]

- \(f=\) `share_fraction`  
- \(s=\) `scarce_share_boost`（稀缺时分享更值钱）  
- 同队偏好 \(\gamma=\) `same_pop_share_bias`  

协作基因 \((share, signal, follow)\) 决定是否 HELP/FOOD、是否分享、是否跟随（可遗传）。

### 契约最少长度

绑定任务契约时：

\[
\mathrm{steps}\ge S_{\min},\quad
\mathrm{gens}\ge G_{\min}
\]

\(S_{\min}=\) `min_steps_when_contract`，\(G_{\min}=\) `min_gens_when_contract`（避免过短跑次被残差噪声主导）。

### 事后分解（只解释，不另评分）

\[
T_i = T_i^{\mathrm{skill}} + T_i^{\mathrm{collab}} + T_i^{\mathrm{residual}}
\]

\[
\mathrm{skill\%}_i=\frac{T_i^{\mathrm{skill}}}{T_i},\quad
\mathrm{collab\%}_i=\frac{T_i^{\mathrm{collab}}}{T_i},\quad
\mathrm{residual\%}_i=\frac{T_i^{\mathrm{residual}}}{T_i}
\]

实现：`sandbox/survival_decompose.py`。skill tick ≈ can_serve 且觅食成功；collab tick ≈ 收分享/跟随等；其余为 residual。

### 旋钮对照：A 生境 4 + B 加压 12

左侧试验田旋钮与配置 JSON **同键**（盘下灰字为字段名）。

**A · `habitat`（客观环境松紧）**

| 中文 | 键 | 作用 |
| --- | --- | --- |
| 丰饶度 | `abundance` | 觅食收益倍率（≈ token 松紧） |
| 事故压 | `predator_pressure` | 每 tick 事故概率 |
| 需求漂移 | `drift_prob` | 世代替换 demand skill |
| 竞争名额 | `niche_capacity` | 每 tick 成功觅食名额（0=不限） |

**B · `evolution_pressure`（让 skill/协作在 \(T_i\) 上拉开差距）**

| 中文 | 键 | 作用 |
| --- | --- | --- |
| 闲置税 | `skill_idle_penalty` | 能 serve 却 REST → 额外代谢 |
| 囤积税 | `genome_carry_cost` | 每 skill 每 tick 代谢（覆盖 learning） |
| 契约最少步 | `min_steps_when_contract` | 绑定契约时步数底 |
| 契约最少代 | `min_gens_when_contract` | 绑定契约时世代底 |
| 偏觅食 | `prefer_forage_when_can_serve` | 0/1，能做则 REST→FORAGE |
| 无技偏压 | `predator_bias_unskilled` | 事故加权打 \(\neg\)can_serve |
| 稀缺分享 | `scarce_share_boost` | abundance&lt;1 时分享放大 |
| 同队分享 | `same_pop_share_bias` | 0~1 优先同 population 分享 |
| 性选择 | `sexual_selection_strength` | Darwin 第二机制：×`mate_choosiness`，按 COURT/生存/互补 skill 加权择偶 |
| 稀有利 | `freq_dep_strength` | 负频率依赖：稀有 skill 觅食优势（防垄断） |
| 技能协同 | `epistasis_strength` | 上位：持有 demand 相邻 skill 对时非加性加成 |

**C · `metabolism`（Agent 生命史，非环境选择压）**

| 中文 | 键 | 作用 |
| --- | --- | --- |
| 衰老率 | `senescence_rate` | \(\mu\times\mathrm{age}\) 个体代谢递增（防不死垄断基因池） |

### 性选择 / 频依 / 上位 / 衰老

\[
\mathrm{eff\_choose}
=
\min\bigl(1,\; \mathrm{mate\_choosiness}\cdot \alpha_{\mathrm{ss}}\bigr)
\]

\(\alpha_{\mathrm{ss}}=\) `sexual_selection_strength`。挑剔时按展示质量 \(Q\)（生存 + COURT 诚实信号 + skill 互补）加权抽样伴侣。

\[
R^{\mathrm{forage}}
\;\times\;
\bigl(1 + \phi\cdot(1-f_s)\bigr)
\;\times\;
\bigl(1 + E(G)\bigr)
\]

- \(\phi=\) `freq_dep_strength`，\(f_s=\) 存活种群中 skill \(s\) 的频率  
- \(E(G)=\min(0.5,\; \varepsilon\cdot \#\{\text{synergy pairs}\subseteq G\})\)，\(\varepsilon=\) `epistasis_strength`

\[
C^{\mathrm{sen}}_{i,t}
=
\mu_{\mathrm{sen}}\cdot T_i^{\mathrm{so\,far}}
\]

\(\mu_{\mathrm{sen}}=\) `metabolism.senescence_rate`（Agent 侧，与环境加压分离）。

### 加压链（一句）

\[
\underbrace{\lambda,\pi,\beta,c}_{\text{逼用对 skill、罚躺/囤/无技}}
+
\underbrace{s,\gamma}_{\text{稀缺协作值钱、偏同队}}
+
\underbrace{\alpha_{\mathrm{ss}},\phi,\varepsilon,\mu_{\mathrm{sen}}}_{\text{性选择·频依·上位·衰老}}
+
\underbrace{S_{\min},G_{\min}}_{\text{够长才选得出来}}
\;\Longrightarrow\;
\Delta T_i\text{ 放大}
\;\Longrightarrow\;
\text{高 }T\text{ 的 }(G,\text{collab 基因})\text{ 入繁衍}
\;\Longrightarrow\;
\text{合适 skill + 协作方式被环境保留}
\]

**一句话**：环境不打分；只通过 \(H\) 与 \(T_i\) 让「匹配且干活的 skill」和「稀缺时能救命的协作」活得更久。

相关文档：[docs/物竞天择任务闭环与Skill遗传plan.md](docs/物竞天择任务闭环与Skill遗传plan.md)、[docs/物竞天择数字孪生演练plan.md](docs/物竞天择数字孪生演练plan.md)、[docs/物竞闭环评估报告-aws-build.md](docs/物竞闭环评估报告-aws-build.md)。闭环脚本：`scripts/eco_closed_loop_eval.py`（`ECO_LOOP_SKIP_LLM=1` 可跳过 LLM 分析加速）。

**与演进式成本优化结合（先适者，后省钱）**：任务挂载 → 物竞 \(T_i\) 过线 → ③ 适者反馈写回 Skill/协作 → 成本页在过线构型内比 token 并棘轮锁定。设计见 [docs/物竞与成本优化结合plan.md](docs/物竞与成本优化结合plan.md)，执行清单 [docs/物竞与成本优化结合todos.md](docs/物竞与成本优化结合todos.md)。

## 任务 Token 治理

> 页面：`cost-dashboard.html` 工作台杠杆区（**一行管线 + 旋钮**）。长文与出处在此；UI 不堆调研海报。  
> 设计：`docs/任务Token治理plan.md` · 清单：`docs/任务Token治理todos.md`

### 北极星

- **对象** = 任务执行路径的 LLM token（`chat_harness` / `tool_loop`）。  
- **Plaza 集体讨论阶段不优化**（智慧无价；成本纪律从执行计划之后开始）。  
- **真省**：算法进 `TokenGovernanceService.prepare_request`；计量认净 `before→after`；`cache_mode=observe` 的 HIT **不计入**已省（仅 `serve` 短路计）。

### prepare 管线与接线

```
simplify → ponytail/caveman → rtk_tool → compress → progressive_mem →
codegraph → cache → skill → cost_tier+model → budget
```

| 接线点 | 说明 |
|--------|------|
| `chat_harness.chat` | 每轮对话 prepare 后调 LLM |
| `tool_loop` 每轮 | 工具环同样 prepare |
| `POST /api/v1/cost/token-governance/simulate` | 与生产同一 prepare（试跑） |

配置：`config/settings.json` → `token_governance`（开关 + `params`）与 `budget`（限额/告警）。

### 杠杆对照（算法 · 模块 · 可调参数）

| 杠杆 | 借鉴（摘要） | 本仓模块 | 可调参数（旋钮） |
|------|--------------|----------|------------------|
| 提示词简化 | BCG 去冗 / 稳定 prefix | `prompt_simplify.simplify_messages` | 开关 |
| Ponytail+Caveman | ponytail YAGNI · flowork caveman | `behavior_inject` | `ponytail_level` / `caveman_level` |
| RTK tool 压缩 | rtk-ai/rtk 滤噪去重截断 | `rtk_tool_compress` | `max_tool_chars`（默认 2200） |
| 内容压缩 | tool compaction · 无 LLM 摘要 | `prompt_cache.compress_messages` | `system_max_chars` 6000 · `msg_max_chars` 4000 |
| 渐进历史 | claude-mem index | `progressive_history` | `keep_recent` · `min_total_for_collapse` · `index_max_chars` |
| CodeGraph | MIT codegraph + 本地符号 | `codegraph_bridge` | `min_blob_chars` |
| 缓存 | Portkey exact+semantic-lite | `PromptCache` | `cache_mode` observe/serve/off · `cache_max_size` |
| Skill 路由 | SkillRouter + 缩短 system | `service._apply_skill_shorten` | `skill_system_max_chars` |
| 模型路由 | LiteLLM 档 · flowork cost_tier | `ModelRouter` + `cost_tier` | `cost_tier_route` |
| 预算门禁 | Portkey budgets · FinOps | `BudgetGuard` | **`alert_threshold` 默认 0.8** · `on_exceed` · session/agent/team 日限 |

权威目录代码：`src/backend/agents/token_governance/lever_catalog.py` + `lever_params.py`。

### API

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/v1/cost/token-governance/levers` | catalog + 开关 + **params 当前值** + budget |
| POST | `/api/v1/cost/token-governance/levers` | 写开关 + `params`（budget 键双写 `settings.budget`） |
| POST | `/api/v1/cost/token-governance/simulate` | 同 prepare 试跑（选 task 或 fixture） |
| POST | `/api/v1/cost/token-governance/budget` | 预算限额（与杠杆旋钮同源） |
| GET | `/api/v1/cost/token-governance/dashboard` | KPI / by_task / savings |
| GET | `/api/v1/cost/token-governance/savings` | prepare 节省 JSONL 按 task |

### 计量规则（诚实）

| 量 | 规则 |
|----|------|
| `saved_tokens_est` | `max(0, before − after)` 净减 |
| 各 lever `saved` | 分步真实 before/after |
| observe cache HIT | 只记统计，**不计省** |
| serve cache HIT | 短路才计省 |

### 前端约定

- 杠杆区：**一行** = 顺序 · 名称 · 接线 · 启用 · 试跑槽 · **参数旋钮**。  
- 业界出处 / 算法步骤 / 模块路径 **不在页面展开**（本 README + plan）。  
- 保存 → `POST /levers` → 下一轮 `prepare_request` 立即使用新参数。

## 技能萃取（TSE 管线）

**状态（2026-07）：可用。** 入口页面 `skill-extract`；后端 `skill_extractor._llm_prefill` 主路径调用 TSE。验收特征：`llm_model_used` 以 `tse+` 开头（如 `tse+qwen-36`），`source_meta.tse` 含 `focus_indices` / `stage_timings`。

### 它解决什么

Plaza 讨论是 **时间序列**（`utterance_1 … utterance_N`），技能定义往往 **跨多轮、嵌在寒暄与争论之间**。TSE（TCN-Skill-Extractor）用时序卷积 + 可学习 skill query 找到「技能时刻」，再 **约束解码** 成结构化 skill JSON，进入人审队列后入库。

设计文档见仓库 `methodology.md` / `reasoning.md`；实现包：`src/backend/agents/tse/`。

### 架构（神经编码 + LLM 解码，串联而非二选一）

```
Plaza transcript D = {m_1, …, m_N}
  m_i = {speaker, role, niche, ritual_signal, round, content}

[Stage 1] Utterance Encoder（token/句编码）
  每句 → 向量 h_i（生产：hash n-gram；训练设计可接 Longformer CLS）
  + speaker/role/signal/niche/round 辅助 embedding

[Stage 2] TCN Temporal Module（Bai 2018 膨胀卷积）
  d ∈ {1,2,4}，receptive field 覆盖约 3–5 轮讨论
  depthwise-separable + residual + LayerNorm
  {h_i} → Z ∈ R^{N×H}

[Stage 3] Skill Query Cross-Attention
  5 个可学习 query：name / description / category / tools / instructions
  各自对 Z 做 multi-head cross-attention → 字段表征 + 聚焦 utterance 下标

[Stage 4] Constrained JSON Decoder
  skill 时刻片段 + 字段 hints → 合法 skill JSON
  生产：ChatHarness 系统 LLM（如 qwen-36）+ schema 校验 / 一次重试
  方法论中的 CodeLLaMA-7B+QLoRA 为训练向目标；无权重时由系统 LLM 顶同一角色
  LLM 不可用时：tse+local 本地合成（仍基于 Stage 1–3 聚焦，非泛化模板）
```

| 阶段 | 谁在算 | 负责什么 | 不负责什么 |
| --- | --- | --- | --- |
| 1–3 神经 | pure-numpy（可加载 `storage/tse/checkpoints/*.npz`） | **何时/何处**在定义技能；字段先验；压缩讨论 | 不写长篇 instructions 散文 |
| 4 解码 | 系统配置 LLM（`ChatHarness`） | **写成** name/desc/instructions/tools 的合法 JSON | 不单独做跨轮时序建模 |
| 人审 | `skill-extract` 队列 | 通过才写入 skill 库 / 团队技能表 | — |

**和「纯 LLM 萃取」的差别：** 旧路径把大段原文塞进 prompt；TSE 先用 TCN+Attention 筛 **skill-moments** 再解码，时序结构与字段对齐由神经侧承担。

### `llm_model_used` 标签含义

| 值 | 含义 | 是否可当正式候选 |
| --- | --- | --- |
| `tse+<model>`（如 `tse+qwen-36`） | Stage 1–3 已跑 + Stage 4 用配置模型解码成功 | ✅ 是 |
| `tse+local(...)` | Stage 1–3 已跑，LLM 失败，本地按聚焦句合成 skill | ⚠️ 可审，质量弱于真解码 |
| `deterministic-fallback` | 智能链路未产出可用 skill 时的 **占位回退草稿**（常带「【回退草稿】」） | ❌ 勿当正式技能 |

萃取调用 **跳过 Token 治理的 `model_route`**（`agent_id` ∈ `skill_extractor` / `tse_skill_extractor`，或 `phase=extract`），并 `model_override` 为用户配置的默认模型名，避免被改写成上游不存在的 `deepseek-v4-flash/pro` 导致假离线。

### 产品链路与 API

```
Plaza 共识 / 手工粘贴讨论
  → POST /api/v1/teams/{team_id}/skill-extract/start
  → TSE.extract_skills → 审核队列（SSE: .../skill-extract/stream）
  → 人 approve → skill_registry + 团队 skills
```

| 动作 | 方法 |
| --- | --- |
| 开始萃取 | `POST .../skill-extract/start` body: `source_text`, `source_title`, `source_type`, `source_meta` |
| 队列 | `GET .../skill-extract/queue` |
| 详情 / 编辑 / 通过 / 拒绝 / 删除 | `GET|POST|DELETE .../skill-extract/{item_id}/...` |

前端：`src/frontend/skill-extract.html`（及配套 JS）。遥测：`source_meta.tse`（`focus_indices`、`category_hint`、`tools_hint`、`latency_ms`、`stage_timings`）。

### 入库后：演化 · 验证 · 路由（速查）

```
人审 approve → skill 库
  ├─ 演化 POST /skill-library/evolve → JSON 草稿 + 语言守卫 → 人确认 apply-evolution
  ├─ 验证 POST /skill-library/verify → 沙箱结构检查 → lifecycle=verified（非业务实跑）
  └─ 路由 POST /skill-router/route → BM25/IDF 两段检索 + lifecycle 加权 → assign 赋予
```

| 能力 | 实现要点 | 边界 |
| --- | --- | --- |
| **演化** `skill_evolver` | 证据包 → 强制 JSON（instructions/changelog/intent）→ 中文原文禁整段英文化 → 人审可编辑后 apply；`__skill_evolver__` 跳过 TG model_route | 不自动写库；不做孪生 A/B 反哺 |
| **验证** `skill_verifier` | 语义层 + 沙箱 mock + **孪生 A/B 全量**（`skill_twin_ab`：baseline 低熟练度 vs treatment 高熟练度+instructions 覆盖，默认 5 种子）→ pass_rate≥0.7 且 twin 达增益阈值 → VERIFIED | Twin 需可绑定 scenario（metadata.scenario + target_skill，或 code_delivery→`code_review_delivery`）；非匹配场景会 skip 而不挡语义通过 |
| **路由** `skill_router` | Stage1 词法检索 + Stage2 字段重排 + **lifecycle 加权**（verified↑ draft/degraded↓）+ 反馈 affinity（落盘 `storage/skill_router_state.json`）；UI 展示 lifecycle 徽章与 match_reasons | 名 Bi/Cross-Encoder，实为本地 BM25/IDF，无 GPU embedding |

API：`/api/v1/skill-library/evolve|apply-evolution|verify` · `/api/v1/skill-router/route|assign`。页面：`skill-extract` 详情 tab「演化 / 验证」与路由模式。

### 训练（银标 → 多任务 → checkpoint）

多任务 loss（与 methodology 一致）：

`L = 1.0 · field_AE + 0.1 · CE(category) + 0.1 · BCE(tools)`

```bash
# 离线 demo：内置讨论 + 银标 + 训练，写出 latest.npz
PYTHONPATH=src/backend python3 scripts/train_tse.py --demo --epochs 8

# 用系统 LLM 打银标
PYTHONPATH=src/backend python3 scripts/train_tse.py --demo --use-llm --epochs 5

# 自有 JSONL
PYTHONPATH=src/backend python3 scripts/train_tse.py --data storage/tse/silver/train.jsonl
```

| 路径 | 内容 |
| --- | --- |
| `storage/tse/silver/train.jsonl` | `(transcript, skills)` 银标/金标 |
| `storage/tse/checkpoints/latest.npz` | 推理自动加载（`get_tse_pipeline(load_checkpoint=True)`） |
| `storage/tse/active/review_queue.json` | active learning 不确定样本（可选） |

单测：`tests/test_tse_pipeline.py`、`tests/test_tse_train.py`。

### 使用注意

1. 后端需已配置 **可用的默认 LLM**（模型与连接页 / `ChatHarness` provider；模型名须被上游接受）。  
2. 浏览器打开技能萃取页，硬刷新后再跑；队列里历史「【回退草稿】」可删。  
3. Plaza 讨论阶段 **不做 token 优化**（两阶段经济学）；萃取本身在讨论结束后发生，走 `phase=extract`。

## Agent 记忆（四层 + 生命周期 + 自主）

> 设计：`docs/Agent记忆生命周期plan.md` · 清单：`docs/Agent记忆生命周期todos.md`  
> 站级入口：**顶栏「Agent记忆」** → `/agent-memory.html`  
> 配置页深链：智能体 → **记忆绑定** tab（`atab=ag-memory`）

### 它解决什么

智能体需要**可拥有、可共享、可传递、可销毁**的记忆，而不是散落的 md 文件或仅沙箱内的经验池。记忆与 Agent 生命周期绑定，并按 Persona 自主读写。

### 四层模型（记忆遗体）

| 层 | 含义 | 要点 |
|----|------|------|
| **运行日志 log** | 做过的事 | append-only；三因子 recall（时新×重要度×词面） |
| **感知流 perception** | 易逝刺激 | 环形缓冲 500；达阈值 **compress** 固化进日志 |
| **未发送队列 intentions** | 打算做还没做 | 创建者/触发/超时策略；传递时可 auto/ask/drop |
| **情绪残留 affect** | 语气余烬 | 只影响 `tone_hint`，默认**不共享** |

### 生命周期

`unbound → active → shared | sealed → (transfer) archived → destroy(tombstone)`

| 操作 | 含义 |
|------|------|
| **bind / save** | 拥有记忆；感知压缩固化 |
| **share** | ACL：reader/co_writer + layer_mask |
| **seal** | 仪式只读；凭吊披露「这是回放，不是本人」 |
| **transfer** | **复制**到受益者；原件可凭吊 |
| **destroy** | 删盘 + 墓碑，禁止静默复活 |

### Persona（小满 / 沈弥安 / 混合）

| Persona | 自主倾向 |
|---------|----------|
| **小满 xiaoman** | 边做边记、tool→感知、任务→日志、聊天宽检索 |
| **沈弥安 shenmian** | 择要、克制共享 affect、更高 recall 重要度门槛 |
| **hybrid** | 默认：小满写路径 + 沈弥安边界 |

### 运行时挂钩（自主）

- **聊天**（`chat_harness`）：注入 `[AG_MEMORY]`（tone + recall + 意图）；`phase=plaza` 跳过  
- **任务**（EventBus `TASK_COMPLETED/FAILED`）：写成功/失败日志 + 情绪  
- **Tool loop**：tool 结果进感知流，达阈值自动 compress  
- **AAS 孪生经验**（可选）：`AG_MEMORY_AAS_BRIDGE=1` 时，沙箱 `record_experience` 同步一条 episodic log（需 `team_id` 在 experience.metadata 或环境变量 `AG_TEAM_ID`）

### API 速查

| 前缀 | 用途 |
|------|------|
| `/api/v1/agent-memory/overview?team_id=` | 团队总览 |
| `/api/v1/agent-memory/{team}/{agent}/lifecycle` | 状态机动作 |
| `.../persona` | 切换小满/沈弥安/混合 |
| `.../share` · `.../share-matrix` | 共享 ACL |
| `.../transfer` · `/transfers` | 传递 |
| `.../runtime/recall` · `.../runtime/record` | 运行时读写 |
| `/api/v1/agent-config/.../memory-core/*` | 兼容旧四层 CRUD |

存储：`storage/agent_memory/<team>/<agent>/`（四层 JSON + meta + shares + audit + legacy）。

### 与其它记忆的关系

| 体系 | 角色 |
|------|------|
| 四层 MemoryCore | **主记忆**（生命周期/共享/自主） |
| 人格页 `memory_files` / 数字员工 `memory.md` | 文档式补充，不替代四层 |
| 沙箱 AAS `memory_system` | 孪生试错经验；可选桥接进四层 log |

## 核心概念速查

- **TwinLoop**（`sandbox/twin_loop.py`）：snapshot_world → spawn_twins → run_simulation → evaluate_outcomes → inject_best_strategy 的仿真在环闭环；支持混沌注入与熟练度结算。
- **物竞天择 / EcoDrill**（`sandbox/eco_drill.py`）：生存时长 \(T_i\) 唯一适应度；任务契约 demand 过滤；加压 12 钮见上文公式节（含性选择/频依/上位/衰老）；办公室视图 `?office3d=1` 左侧 A 生境 4 + B 加压 12 音量旋钮。
- **SECS 演练**：团队 + 场景驱动的 演练→评估→进化 循环，SSE 实时推流到 3D 前端。
- **SkillRouter**：BM25/TF-IDF 双阶段检索重排，把 top-K 技能注入 agent system prompt（无 GPU 依赖）。
- **SkillClaw 流水线**：Filter → Improve → Verify → Solidify，从演练轨迹提取技能并验证后入库。
- **Token 北极星**：新成本体系以 token 为唯一口径（`token_policy.py` + cost-gate）；`cost_policy.py` 的 Terraform 成本规则为 LEGACY。
- **Ratchet（棘轮）**：演进只进不退——新策略必须在孪生环境中证明优于基线才允许发布。

## 部署

Docker：`Dockerfile` + `docker/`；K8s：`k8s/`（含成本标签 mutating webhook）。可观测性：可选 OpenTelemetry（`pip install -e ".[otel]"`）。
