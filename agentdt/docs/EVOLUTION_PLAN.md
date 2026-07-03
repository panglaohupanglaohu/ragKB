# AgentsGroup 系统演进 — 自我进化优化管线

> 直接移植自: [NousResearch/hermes-agent-self-evolution PLAN.md](https://github.com/NousResearch/hermes-agent-self-evolution/blob/main/PLAN.md)  
> 引擎替换: DSPy+GEPA → **Qwen3 反思式演化** (零外部依赖，纯 API 调用)  
> 宿主系统: AgentsGroup2026 现有达尔文棘轮 + SkillClaw 管线

---

## Vision

一个独立的优化管线，系统性提升 Agent 团队的技能(skills)、系统提示词(system prompts)、
审查规则(audit rules) 的质量。使用自动化优化循环，运行在现有系统之上。

**三个互补引擎，统一在同一个工作流下：**

| 引擎 | 优化目标 | 许可 | 集成方式 |
|------|---------|------|---------|
| Qwen3 反思式演化 (类GEPA) | 技能指令、系统提示词、审查规则描述 | 免费API | 原生 Python，主引擎 |
| 达尔文棘轮 (已有) | 不可逆锁定所有改进 | 自有 | 已集成 |
| LLM-as-Judge 评估 | 质量评分、回归检测 | Qwen API | 原生 Python，评估引擎 |

**重要：无GPU训练。** 所有优化通过 Qwen API 调用完成。反思式演化变异和评估的是文本字符串
（指令、描述），不是模型权重。

---

## What Can Be Improved

### Tier 1: 技能指令 (Highest Value, Lowest Risk)

- **What**: `SkillDefinition.instructions` — Agent 执行任务时遵循的操作指令
- **How**: 将技能文本包装为可优化模块，在测试任务上评估，用 Qwen 反思式演化
- **Why it works**: 技能是纯文本，容易变异，效果直接可测（Agent 遵循此技能完成任务了吗？）
- **Example**: 演化「代码审查」技能，使其在已知好/坏代码案例上产生更准确的审查结果

### Tier 2: 审查规则描述 (Medium Value, Low Risk)

- **What**: 44 条审查规则的 `title` + `description` + `check_fn` 逻辑描述
- **How**: 反思式演化规则描述，评估规则是否能更准确识别问题
- **Why it works**: 规则检测是分类问题 — 非常适合优化
- **Example**: 演化 `GEN-CHAT-005` 规则描述，使其更精准检测 bridge_chat 注册状态

### Tier 3: Agent 系统提示词 (High Value, Higher Risk)

- **What**: Team 级别的 system_prompt 各段落
- **How**: 将可演化段落参数化，用 Qwen 反思式演化优化
- **Why it works**: 系统提示词质量直接决定 Agent 行为质量
- **Risk**: 必须小心不破坏整体行为 — 只离线优化，部署为新版本
- **Example**: 演化任务分配相关的提示词段落，减少不必要的工具调用

### Tier 4: 审查规则代码 (High Value, Highest Risk)

- **What**: `check_fn` 的实际 Python 逻辑
- **How**: LLM 改进规则实现代码，pytest 门禁验证
- **Why it works**: 某些规则实现有微妙 bug 或效率问题
- **Risk**: 代码更改可能破坏系统 — 需要强测试套件作为护栏
- **Example**: 演化 `DC-PUE-032` 的检查逻辑，覆盖更多边界情况

---

## Architecture

### The Optimization Loop (直接照搬 Hermes)

```
┌─────────────────────────────────────────────────────┐
│  1. SELECT TARGET                                   │
│     - 选择一个技能/规则/提示词段落                      │
│     - 加载当前版本作为 baseline                        │
│                                                     │
│  2. BUILD EVALUATION DATASET                        │
│     - 从 knowledge_base/ 挖掘真实使用案例              │
│     - 或用 Qwen 合成测试用例                          │
│     - 划分: train / validation / holdout             │
│                                                     │
│  3. WRAP AS OPTIMIZABLE MODULE                      │
│     - 技能文本 → SkillModule (可评估包装)              │
│     - 规则逻辑 → RuleModule                          │
│     - 提示词段落 → PromptModule                       │
│                                                     │
│  4. RUN OPTIMIZER (Qwen 反思式演化)                   │
│     - 主引擎: 反思式变异 (分析失败→定向改进)             │
│     - 回退: 随机变异 + 择优                           │
│     - 每轮生成 2-3 候选 → 评估 → 保留最优              │
│                                                     │
│  5. EVALUATE & COMPARE                              │
│     - 在 holdout 测试集上运行优化版本                   │
│     - 对比: 质量分、token 成本、指令遵循度               │
│     - 统计显著性检查                                   │
│                                                     │
│  6. DEPLOY (with approval)                          │
│     - 通过棘轮验证阶段 + Heritage Ledger 锁定          │
│     - 前端展示 diff + 分数对比供人工审核                 │
│     - 回滚机制: version 回退                          │
└─────────────────────────────────────────────────────┘
```

### Integration Points with Existing Infrastructure

| 现有组件 | 在优化管线中的角色 |
|---------|-----------------|
| `EvolutionExecutor` | 评估执行器 — 并行运行 Agent 在测试任务上 |
| `SkillEvolver.evolve_skill()` | 变异执行 — 调用 Qwen 生成候选变体 |
| `SystemEvolutionChannel` | 棘轮门禁 — 验证→锁定 |
| `knowledge_base/*.json` | 挖掘真实使用数据构建评估数据集 |
| `SkillLibrary` | 技能读写 — 加载当前版本、持久化演化版本 |
| `model_pool.json → qwen3` | 反思式演化 + 评估的 LLM 引擎 |
| `Heritage Ledger` | 追踪所有演化血统，锁定改进 |
| `system-evolution.html` | 前端展示优化过程、对比、审核 |

### Data Flow (照搬 Hermes，映射到我们的组件)

```
knowledge_base/ (真实会话记录)
    │
    ▼
Evaluation Dataset Builder (eval_dataset.py)
    │
    ├──► Skill Module Wrapper (将 skill.instructions 包装为可优化模块)
    │        │
    │        ▼
    │    Qwen 反思式演化 ◄── 执行轨迹 (从 EvolutionExecutor)
    │        │                    ▲
    │        │                    │
    │        ▼                    │
    │    Candidate Variants ──► EvolutionExecutor (并行评估)
    │        │
    │        ├──► Constraint Validation (长度、语义、格式约束)
    │        │
    │        ▼
    │    Best Valid Variant
    │        │
    ▼        ▼
Darwin Ratchet (棘轮验证 + Heritage Ledger 锁定)
    │
    ▼
Human Review (前端 diff 审核 + 批准)
```

---

## Implementation Structure

### Where It Lives

**不新建 repo，直接增强现有模块：**

```
src/backend/agents/
  evolution/                          # 新增演化优化包
    __init__.py
    dataset_builder.py               # 评估数据集生成 (合成 + knowledge_base 挖掘)
    fitness.py                       # Fitness 函数 (LLM-as-Judge 评分)
    constraints.py                   # 约束验证器 (长度、语义、格式、回归)
    optimizer.py                     # 主优化循环 (照搬 Hermes 的 GEPA runner)
    mutator.py                       # 反思式变异器 (Qwen 驱动)
    skill_module.py                  # 将 SkillDefinition 包装为可优化模块
    rule_module.py                   # 将 AuditRule 包装为可优化模块
    prompt_module.py                 # 将 system_prompt 段落包装为可优化模块
    comparator.py                    # baseline vs evolved 对比 + 统计检验
    auto_triage.py                   # 自动诊断 — 找最弱目标

src/backend/channels/
  system_evolution.py                # 已有 — 增加优化相关方法

src/backend/agent_team_api.py        # 已有 — 增加优化 API 端点

src/frontend/
  system-evolution.html              # 已有 — 增加「演化实验室」面板

storage/
  evolution_datasets/                # 生成的评估数据集 (JSON)
    skills/
    rules/
    prompts/
  evolution_runs/                    # 每次优化运行的快照 (可恢复)
```

### How It's Invoked

**后端 API (前端 system-evolution.html 调用):**

```python
# 1. 对技能运行 fitness 评估
POST /api/v1/agent-teams/evolution/fitness/skill/{skill_id}
# Returns: {"score": 0.72, "breakdown": {...}, "eval_examples": 15}

# 2. 启动技能优化
POST /api/v1/agent-teams/evolution/optimize
Body: {"target_type": "skill", "target_id": "xxx", "iterations": 5}
# Returns: SSE stream of optimization progress

# 3. 查看优化结果
GET /api/v1/agent-teams/evolution/optimize/{run_id}/result
# Returns: {"baseline_score": 0.72, "evolved_score": 0.85, "diff": "...", ...}

# 4. 批准演化 (走棘轮)
POST /api/v1/agent-teams/evolution/optimize/{run_id}/approve
# Triggers: apply_evolution → ratchet verify → heritage lock

# 5. 自动诊断
POST /api/v1/agent-teams/evolution/auto-triage
# Returns: [{"skill_id": "xxx", "impact_score": 3.2, "reason": "..."}]
```

**CLI (可选，调试用):**

```bash
# 评估某技能的 fitness
python -m src.backend.agents.evolution.optimizer --skill build_system/xxx --evaluate-only

# 运行优化循环
python -m src.backend.agents.evolution.optimizer --skill build_system/xxx --iterations 5

# 自动诊断
python -m src.backend.agents.evolution.auto_triage --team build_system --top 3
```

---

## Execution Plan

### How Phases Work (照搬 Hermes)

阶段是顺序的 — 每个阶段基于前一个阶段的基础设施，必须证明自己有效才继续。

```
Phase 1 ──► Validation Gate ──► Phase 2 ──► Validation Gate ──► Phase 3 ──► ...
  Build       "确实让事情           Build       "没有破坏           Build
  & test       变好了？"            & test       其他东西？"          & test
```

每个阶段之间:
1. 运行完整棘轮审查周期确认无回归
2. 审核所有演化产出 — 改动对人来说合理吗？
3. 通过棘轮锁定已验证的改进
4. 回顾: 什么有效、什么无效、调整下阶段方法

每阶段三个子阶段:
- **Build**: 编写该层级的优化基础设施
- **Run**: 在真实目标上执行优化，迭代评估数据集
- **Validate**: 棘轮验证、人工审核、锁定

---

### Phase 1: 技能演化 (Skill Evolution via Qwen Reflective)

**Goal:** 系统能优化任意 `SkillDefinition.instructions`，通过反思式演化循环。

**Build:**

- 安装无额外依赖（Qwen API 已在 model_pool.json 中配置）
- 构建 skill-as-module 包装器 (`skill_module.py`)
- 构建评估数据集生成器 (`dataset_builder.py`)
- 构建 Qwen 反思式优化运行器 (`optimizer.py` + `mutator.py`)
- 构建 LLM-as-Judge fitness 函数 (`fitness.py`)

**Run:**

- 选 2-3 个目标技能（从现有 build_system 团队中选 usage_count 最高的）
- 为每个技能生成评估数据集（15-20 examples）
- 运行反思式演化（5-10 iterations）
- 对比 baseline vs evolved on holdout set
- 根据噪声情况迭代评估数据集质量

**Validate:**

- 运行完整棘轮审查周期，确认无回归
- 人工审核所有演化 diff — 改动合理吗？
- 锁定通过审核的改进到 Heritage Ledger
- 记录什么有效什么无效

**Done when:**

- ≥1 技能在评估数据集上有可测量改进（≥10% score 提升）
- 无棘轮回归（CII 评级保持或提升）
- 演化 diff 对人工审核者来说读起来合理
- 优化管线可复用（指向任意技能即可运行）

**What to build (照搬 Hermes，1:1 映射):**

1. **Skill-as-Module wrapper** (`skill_module.py`) — 将 SkillDefinition 包装为可评估模块:
   - 注入 skill.instructions 作为系统提示词
   - 在测试任务上运行 Agent
   - 返回结果供评分

2. **Evaluation dataset builder** (`dataset_builder.py`) — 多来源创建 train/val/holdout:

   **来源 A: Qwen 合成 (主要, 冷启动)**
   - 读取技能 → 理解其功能
   - 生成 15-20 个 `(task_input, expected_behavior_rubric)` 对
   - expected_behavior 是评分标准，不是精确文本
   - 划分: 10 train / 5 val / 5 holdout

   **来源 B: knowledge_base 挖掘 (真实使用)**
   - 查询 `storage/knowledge_base/*.json` 中技能被使用的记录
   - 提取用户任务 + Agent 完整响应
   - LLM-as-Judge 评分 (task, response) 对
   - 高分对成为正例；低分对成为失败案例供反思分析

   **来源 C: 人工标注 (可选，高价值技能)**
   - 手动编写测试用例 + 预期输出
   - 存储为 `storage/evolution_datasets/skills/<skill-name>/golden.json`

   **来源 D: 自动评估 (如适用)**
   - 某些技能有天然的自动评估: 如代码审查→植入 bug 看是否能发现
   - 不是所有技能都有 — 这是加分项

   **评分: LLM-as-Judge + rubrics**
   - 大多数技能没有二值对错 — 质量是主观的
   - Fitness 函数用 LLM Judge 按 rubric 评分:
     - 指令遵循度 (0-1)
     - 输出正确性/有用性 (0-1)
     - 简洁度 (0-1)
   - Rubrics 是技能特定的，与评估数据集一起存储

3. **Qwen 反思式优化运行器** (`optimizer.py` + `mutator.py`) — 核心演化循环:
   - 使用 EvolutionExecutor 并行评估
   - 捕获执行轨迹供反思分析
   - 保存快照支持暂停/恢复

4. **Comparison & deployment** (`comparator.py`) — 并排评估:
   - baseline vs optimized on holdout
   - 展示 diff
   - 提交到棘轮验证流程

**前端增强 (system-evolution.html 新面板 "🧬 技能演化"):**

```
侧栏新增:
  <a onclick="switchPanel('skill-evolve')"><span class="seal seal-koke">🧬</span> 技能演化</a>

面板内容:
  ┌─────────────────────────────────────────────────────────┐
  │ 🧬 技能演化实验室                                        │
  ├─────────────────────────────────────────────────────────┤
  │ [选择团队 ▼] [选择技能 ▼]  [⚡ 评估 Fitness]  [🚀 启动优化] │
  ├─────────────────────────────────────────────────────────┤
  │ 当前 Fitness: 0.72  │  版本: V3  │  使用次数: 47         │
  ├─────────────────────────────────────────────────────────┤
  │ 📊 优化进度 (迭代 3/5)                                   │
  │ ┌───────────────────────────────┐                       │
  │ │ Round 1: 0.72 → 0.75 (+3%)   │ ← 反思: 缺少边界处理    │
  │ │ Round 2: 0.75 → 0.78 (+3%)   │ ← 反思: 步骤顺序不优    │
  │ │ Round 3: 0.78 → 0.85 (+7%)   │ ← 反思: 增加示例         │
  │ │ Round 4: running...           │                       │
  │ └───────────────────────────────┘                       │
  ├─────────────────────────────────────────────────────────┤
  │ 📝 Diff Preview (baseline → evolved)                    │
  │ ┌───────────────────────────────────────────────────┐   │
  │ │ - 第一步：检查输入格式                               │   │
  │ │ + 第一步：检查输入格式，如无效则返回明确错误提示        │   │
  │ │   第二步：分析上下文...                              │   │
  │ │ + 第二步半：验证上下文完整性（新增）                   │   │
  │ └───────────────────────────────────────────────────┘   │
  ├─────────────────────────────────────────────────────────┤
  │ [✅ 批准并锁定] [❌ 拒绝] [🔄 再跑一轮]                   │
  └─────────────────────────────────────────────────────────┘
```

---

### Phase 2: 审查规则描述优化 (Audit Rule Description Optimization)

**Goal:** 优化 44 条审查规则的自然语言描述，使其更准确地传达检测意图。

**Prerequisite:** Phase 1 gate passed — 反思式演化循环已证明可用于技能。

**Build:** 复用 Phase 1 的 Qwen runner，适配审查规则。构建规则效果评估器 +
合成检测数据集。难点是交叉评估 — 确保改进一条规则不会影响其他规则。

**Run:** 生成规则检测数据集（每条规则 10-15 个正负案例）。对所有规则描述同时优化。
从 audit trail 中挖掘误检/漏检模式。

**Validate:** 棘轮验证。人工审核演化后的描述 — 是否仍然准确描述规则意图？

**Done when:**
- 规则检测准确率提升（≥5% improvement on holdout）
- 无单条规则的检测率回归
- 棘轮评级保持（CII 分数 within 2%）
- 演化后的描述对人来说仍然准确 ≤200 chars

**What gets evolved:** 审查规则的 `title` 和 `description` 字段。这些描述决定了:
- 规则在前端的展示
- Agent 理解规则意图时的上下文
- 自动化检测逻辑的注释

**Constraints specific to rule descriptions:**
- Max 100 chars per title
- Max 500 chars per description
- 必须保持事实准确（不能声称规则做了它不做的事）
- 规则结构（id、severity、domain）FROZEN — 只有文本演化

**前端增强 (Rules 面板新增):**
- 每条规则卡片增加 "🧬 优化" 按钮
- 点击后展示当前 fitness + 启动优化

---

### Phase 3: Agent 系统提示词演化 (System Prompt Evolution)

**Goal:** 优化 Agent Team 的系统提示词中可演化的段落。

**Prerequisite:** Phase 2 gate passed — 棘轮门禁验证有效，Qwen 产生合理文本变异。

**Build:** 构建 prompt-section-as-parameter 包装器。构建行为测试套件生成器。
这是迄今风险最高的层级 — 系统提示词变更影响所有行为。

**Run:** 生成行为测试场景（每段落 10-15 个场景）。先独立优化每段落，再联合优化。
每轮优化后运行棘轮审查。

**Validate:** 完整棘轮验证周期。格外严格 — 系统提示词变更有最大爆炸半径。

**Done when:**
- 行为测试分数提升（≥10% on targeted sections）
- 棘轮评级保持或提升（zero tolerance for regression）
- Agent 的语调/风格没有明显偏移
- 提示词保持在合理长度内

**What gets evolved:**
| 段落 | 位置 | 是否可演化 |
|------|------|-----------|
| Team system_prompt 主体 | AgentTeam config | ✅ 是 — 语调、优先级、方法 |
| 任务分配指导 | EvolutionExecutor prompt builder | ✅ 是 — 触发条件 |
| 工具使用指引 | system prompt sections | ✅ 是 — 工具选择引导 |
| 用户实际数据 | knowledge_base | ❌ 否 — 用户数据 |
| 自动生成内容 | 技能列表等 | ❌ 否 — 自动生成 |

**Constraints specific to system prompt:**
- 每段落不超过当前长度的 120%（防止膨胀）
- 必须保持核心行为特征
- 平台相关提示必须保持平台准确性

---

### Phase 4: 审查规则代码演化 (Audit Rule Code Evolution)

**Goal:** 演化 `check_fn` 的实际 Python 逻辑，修复 bug 和覆盖边界情况。

**Prerequisite:** Phase 1-3 完成 — 强评估管线、验证过的棘轮门禁。

**Build:** 构建 code-as-organism 包装器，将规则 check_fn 映射为可变异单元。
构建复合 fitness 函数 (pytest + 棘轮审查 + bug 复现)。

**Run:** 从已知的审查失败开始 — 创建复现脚本，运行演化寻找修复。
然后对 1-2 条规则做边界情况强化。

**Validate:** 完整 pytest 套件 + 完整棘轮验证周期。最严格的人工审核 —
每行演化代码都要 review。

**Done when:**
- ≥1 已知 bug 被演化修复（通过复现脚本验证）
- 完整测试套件通过
- 棘轮评级保持
- 函数签名未改变
- 人工审核者批准所有代码变更

**Safety guardrails (最严格):**
- 测试套件必须 100% 通过
- 函数签名 frozen（不能破坏调用者）
- 不能删除错误处理或安全检查
- 人工审核 required on every change

---

### Phase 5: 持续自我优化循环 (Continuous Self-Improvement Loop)

**Goal:** 系统自动识别最弱领域并定期改进。

**Prerequisite:** Phase 1-4 证明有效 — 手动优化对技能、规则、提示词、代码都可靠工作。

**Build:** 构建性能监控器（跟踪 skill 成功率、规则准确率、棘轮趋势）。
构建自动诊断逻辑（按 影响力×频率 排序优化目标）。接入定时触发器。

**Deploy & Monitor:** 设置定期棘轮审查运行。设置阈值触发优化
（当技能 effectiveness < 0.7 时自动触发）。所有自动生成的改进仍需人工批准。

**Done when:**
- 定期棘轮审查无人值守运行并上报分数
- 自动诊断正确识别出低效技能
- 至少一次优化循环完整运行（检测问题→优化→锁定）无需人工介入
- 人工仍然审核和批准每次改进 — 此阶段自动化的是检测和优化，不是部署

**What to build:**

1. **Performance Monitor** — 从真实使用中追踪指标:
   - 每技能成功率（from knowledge_base — 技能是否被加载？任务是否成功？）
   - 规则检测准确率（from audit trail — 是否有误报/漏报？）
   - 棘轮分数趋势（periodic CII rating）
   - 用户修正（用户否决/修改了 Agent 的输出 — 这是信号）

2. **Auto-Triage** — 识别下一个优化目标:
   - effectiveness 持续下降的技能
   - 频繁被跳过的审查规则
   - CII 分数贡献最低的类别
   - 排序: `(potential_improvement × usage_frequency)`

3. **Scheduled optimization** — 定时管线:
   - 每周: 运行棘轮审查，记录分数
   - 当分数下降或技能 effectiveness 低于阈值: 触发反思式优化
   - 生成改进候选 + 对比结果
   - 通知人工审核

4. **Feedback loop** — 真实使用改进评估数据集:
   - 用户修正被记录并加入评估数据集
   - 高质量会话成为正例
   - 失败会话成为反思分析的失败案例
   - 评估数据集有机增长

**前端增强 (Overview 面板增加):**
- "自动诊断"按钮 → 展示 top-3 最弱技能 + 原因
- "定时优化"开关 → 启用/禁用自动循环
- "优化历史"时间线 → 每次自动运行的结果摘要

---

## Fitness Evaluation as Gate Signal (照搬 Hermes Benchmark 机制)

现有棘轮的三层门禁在优化管线中的角色:

| 门禁 | 检测内容 | 执行时间 | 成本 | 角色 |
|------|---------|---------|------|------|
| pytest (如有) | 功能正确性 | 秒级 | ¥0 | GATE 1: 硬性通过 |
| Fitness on holdout | 技能/规则质量分 | ~2-5 min | ~¥0.5 | GATE 2: 质量提升 |
| 棘轮审查周期 | 系统全局一致性 | ~1 min | ~¥0.1 | GATE 3: 无回归 |
| CII Rating recalc | 合规评级 | 即时 | ¥0 | GATE 4: 评级保持 |

```
Candidate Variant
    │
    ├──► Constraint Check (长度/格式/语义) ── GATE 1: 基本约束
    │
    ├──► Fitness on eval dataset ──────────── GATE 2: 质量分 > baseline
    │
    ├──► 棘轮审查 (run_full_audit) ────────── GATE 3: 无规则回归
    │
    ▼
Top Candidates Only (top 1-2)
    │
    ├──► CII Rating recalc ────────────────── GATE 4: 评级保持
    │
    ▼
Best Candidate → 前端展示 diff + 分数 → 人工审核 → Heritage Lock
```

**关键原则:** Fitness 是 FITNESS（质量变好了吗？），棘轮是 GATE（没破坏别的吧？）。
一个候选如果 fitness +20% 但让 CII 掉了 5%，则被 REJECTED。

---

## Constraints & Guardrails (照搬 Hermes)

所有候选变体必须通过以下全部约束才被视为有效:

### 1. Constraint Validation

```python
def passes_constraints(original, evolved):
    # 长度: 不超过原始的 150%
    if len(evolved) > len(original) * 1.5: return False
    # 语言一致: 中文保持中文
    if detect_lang(original) != detect_lang(evolved): return False
    # 格式保持: 有编号步骤则保留编号
    if has_numbered_steps(original) and not has_numbered_steps(evolved): return False
    return True
```

### 2. Character/Token Limits

| 目标类型 | 限制 | 原因 |
|---------|------|------|
| 技能 instructions | 不超过原始 150% | 防膨胀，保持简洁 |
| 审查规则 description | ≤500 chars | 前端展示空间有限 |
| 系统提示词段落 | 不超过当前 120% | 防上下文窗口浪费 |

Fitness 函数对接近限制的变体施加长度惩罚 — 即使其他方面更好，
也会被降分。防止演化向冗余漂移。

### 3. Semantic Preservation

优化器必须保持核心行为/意图:
- 「代码审查」技能演化后仍然执行代码审查
- 规则描述仍然准确描述规则实际检测的内容
- 系统提示词保持其功能角色

通过在 fitness 函数中包含语义相似度检查来强制执行。

### 4. Deploy via Ratchet (Never Direct Overwrite)

所有演化变更走棘轮流程:
```
optimized_variant
    → EvolutionItem (status: verify_pending)
    → 棘轮验证 (check_fn 全部通过)
    → 人工审核 (前端 diff view)
    → apply_evolution() (version += 1)
    → Heritage Ledger 锁定 (不可逆)
```

---

## 与 Hermes 的 1:1 映射表

| Hermes 概念 | 我们的实现 | 文件位置 |
|------------|-----------|---------|
| DSPy Module Wrapper | `skill_module.py` / `rule_module.py` | `agents/evolution/` |
| GEPA Optimizer | `optimizer.py` + `mutator.py` (Qwen反思式) | `agents/evolution/` |
| dspy.GEPA reflective analysis | `mutator.py` 失败分析→定向改进 | `agents/evolution/` |
| batch_runner | `EvolutionExecutor` 并行评估 | `channels/evolution_executor.py` |
| SessionDB Mining | `dataset_builder.py` ← knowledge_base/ | `agents/evolution/` |
| Fitness function (LLM-as-judge) | `fitness.py` (Qwen 评分) | `agents/evolution/` |
| Constraint validators | `constraints.py` | `agents/evolution/` |
| Benchmark gate (TBLite) | 棘轮审查周期 (`run_full_audit`) | `channels/system_evolution.py` |
| PR + Human Review | 前端 diff 审核 + 批准按钮 | `system-evolution.html` |
| Git branch + commit | `skill.version += 1` + Heritage Ledger | `agents/skill_library.py` |
| MIPROv2 (fallback) | 随机变异 + 择优 (optimizer fallback) | `agents/evolution/optimizer.py` |
| Darwinian Evolver | Phase 4: check_fn 代码演化 | `agents/evolution/` |
| Continuous loop | Phase 5: auto_triage + 定时触发 | `agents/evolution/auto_triage.py` |
| evolve CLI | API endpoints + 可选 CLI | `agent_team_api.py` |

---

## Practical Considerations

### Cost (照搬 Hermes)
- Qwen 反思式优化: ~¥1-5 per run (取决于评估数据集大小)
- LLM-as-Judge 评估: ~¥0.5-2 per skill (15 examples × 3 criteria)
- 建议: 小评估集起步（10-15 examples），重要技能再扩大

### Safety (照搬 Hermes)
- **人工审批 required** — 所有变更走棘轮，永不直接覆写
- **约束门禁** — 长度/语义/格式约束，zero tolerance
- **棘轮 gate** — CII 评级回归则拒绝
- **Heritage Ledger 追踪** — 每次演化都是一条不可变记录，回滚 trivial
- **Holdout 测试集** — 与训练数据分开，捕获过拟合

### 零外部依赖
- 不安装 DSPy、GEPA 或任何新 pip 包
- 全部用 Qwen3 API (已在 model_pool.json 中配置)
- 复用现有 `httpx` / `aiohttp` 做 API 调用
- 评估数据集存为 JSON 文件

---

## 新增审查规则 (Phase 5 生效)

| ID | 标题 | 严重度 | 检测条件 |
|----|------|--------|---------|
| GEN-EVOL-014 | 月度演化活跃 | medium | 过去 30 天至少 1 次技能演化完成 |
| GEN-FIT-015 | 团队 Fitness 基线 | high | 团队所有技能平均 fitness ≥ 0.6 |
| GEN-DRIFT-016 | 无持续退化 | critical | 无技能连续 3 个月 effectiveness 下降 |
| GEN-TRIAGE-017 | 自动诊断运行 | low | 过去 7 天运行过 auto_triage |

---

## Timeline (照搬 Hermes 结构)

| Phase | 内容 | 前置 | 完成标志 |
|-------|------|------|---------|
| Phase 1 | 技能演化 (核心能力) | 无 — 从这里开始 | ≥1 技能可测量改进，无棘轮回归 |
| Phase 2 | 审查规则描述优化 | Phase 1 基础设施 | 规则检测准确率提升，无回归 |
| Phase 3 | 系统提示词演化 | Phase 1-2 基础设施 + 验证过的棘轮门禁 | 行为测试通过，评级保持 |
| Phase 4 | 规则代码演化 | Phase 1-3 + 强评估管线 | Bug 修复，测试通过 |
| Phase 5 | 持续循环 | 以上全部工作 | 无人值守运行一次完整循环 |

如果某阶段未产生有意义的改进（演化版本不比 baseline 好），停下来重新评估。
不是非得做完五个阶段。

---

## Open Questions (照搬 Hermes)

1. **评估数据集冷启动**: 技能使用历史不多时怎么办？
   - 方案: Qwen 合成为主，真实使用积累为辅

2. **Fitness 评分一致性**: LLM-as-Judge 每次评分可能略有不同
   - 方案: 每个案例评 3 次取平均，设置最低置信度

3. **演化版本管理**: 演化后的技能是否需要单独版本号？
   - 方案: 复用 skill.version += 1，Heritage Ledger 记录每次演化详情

4. **最小可行首要目标**: 第一个优化的技能选谁？
   - 方案: 从 build_system 团队中选 usage_count 最高 + effectiveness 最低的

---

## Next Step

确认后立即开始 **Phase 1 Build**:
1. `src/backend/agents/evolution/__init__.py`
2. `src/backend/agents/evolution/dataset_builder.py`
3. `src/backend/agents/evolution/fitness.py`
4. `src/backend/agents/evolution/skill_module.py`
5. `src/backend/agents/evolution/mutator.py`
6. `src/backend/agents/evolution/optimizer.py`
7. `src/backend/agents/evolution/constraints.py`
8. `src/backend/agents/evolution/comparator.py`
9. API endpoints in `agent_team_api.py`
10. 前端 "🧬 技能演化" 面板 in `system-evolution.html`
