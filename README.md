<p align="center">
  <strong>🏛️ AgentsGroup2026</strong>
</p>

<p align="center">
  <em>自演进多智能体协作平台 — 让 AI 团队自己开会、萃取技能、驱动系统进化</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vite-6.x-purple" alt="Vite" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License" />
</p>

---

## 目录

- [项目愿景](#项目愿景)
- [四大核心模块](#四大核心模块)
  - [1. 多智能体协作框架](#1-多智能体协作框架-agents)
  - [2. 议事广场](#2-议事广场-plaza)
  - [3. 技能萃取管线](#3-技能萃取管线-extraction-pipeline)
  - [4. 系统演进引擎](#4-系统演进引擎-system-evolution)
- [四大模块如何协同运转](#四大模块如何协同运转)
- [数字孪生与语音化身](#数字孪生与语音化身)
  - [智能体数字孪生可视化系统](#智能体数字孪生可视化系统-digital-twin-cli)
  - [核心算法](#核心算法)
  - [使用方法](#使用方法)
- [系统架构总览](#系统架构总览)
- [核心算法与设计模式](#核心算法与设计模式)
- [智能体团队一览](#智能体团队一览)
- [快速开始](#快速开始)
- [API 参考](#api-参考)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [未来计划](#未来计划)

---

## 项目愿景

AgentsGroup2026 的核心信念是：**AI 不应该只是回答问题的工具，它应该像一个真正的团队一样工作——开会讨论、形成共识、提炼经验、驱动系统自我进化。**

我们构建了一个闭环平台，让多个 AI 智能体组成团队，围绕真实业务问题在「议事广场」中展开多轮辩论，将讨论中产生的洞察萃取为可复用的技能，最终通过系统演进引擎将这些技能落地为实际的代码变更和系统改善。

**这不是又一个 AI 聊天工具。** 这是一套让 AI 产出真正落地的闭环系统。

### 自演进闭环

整个系统是一条不可逆的演进链——每转一圈，系统能力只增不减（达尔文棘轮）：

```
构建团队 → 议事广场讨论 → 萃取 Skill → 赋予 Agent → 数字孪生试跑 → 真实落地 → (产生新问题) → 回到讨论
```

| 环节 | 页面 | 作用 |
|------|------|------|
| 构建 | agent-team-config | 组建团队、配置角色与技能 |
| 讨论 | plaza | 多智能体多轮辩论、协作决策 |
| 萃取/赋予 | skill-extract | 讨论中涌现的知识结晶为 Skill，回注给 Agent |
| 试跑 | digital-twin-cli | 在镜像世界验证新技能，推演 what-if 场景 |
| 落地+度量 | system-evolution | Darwin Ratchet 锁定改善，不可逆进化 |

自演进的关键：**通过人机交互驱动系统持续进化**——人类提出问题和方向，系统自动完成讨论→学习→验证→部署→锁定的闭环，每一轮交互都让系统变得更好。

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  🤖 智能体   │────▶│  🏛️ 议事广场  │────▶│  ⚗️ 技能萃取  │────▶│  🔄 系统演进  │
│  Multi-Agent │     │    Plaza    │     │  Extraction │     │  Evolution  │
│  协作框架     │◀────│  多轮辩论    │◀────│  落地验证    │◀────│  闭环审查    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │                    │
       └────────── 🔊 TTS 语音化身 ─ 数字孪生 ─ 事件溯源 ──────────┘
```

---

## 四大核心模块

### 1. 多智能体协作框架 (Agents)

> **"不是一个 Agent 在战斗，而是一个有分工、有层级、有记忆的团队。"**

#### 架构设计

多智能体框架采用 **团队→智能体→技能→工具** 的四层抽象：

```
AgentTeam (团队)
├── ModelPool          # LLM 模型池（多供应商热切换）
├── AgentProfile[]     # 智能体列表
│   ├── role           # 角色定位（architect / developer / qa / ...）
│   ├── system_prompt  # 人格注入（SOUL.md 风格）
│   ├── skills[]       # 绑定技能
│   ├── tools[]        # 可用工具
│   ├── channels[]     # 通信频道（发布/订阅）
│   └── traits[]       # 性格标签（decisive / analytical / ...）
└── Workflow           # 团队协作流程
```

#### 对话引擎 (ChatHarness)

对话引擎是智能体与外部世界交互的核心。它不是简单的 prompt→response，而是一个包含 **规划-执行-观察** 循环的完整推理系统：

1. **UltraPlan 规划器**：根据用户意图自动生成工具调用计划（关键词→工具序列映射）
2. **AgentLoop 执行引擎**：Function-calling 循环，支持最多 90 轮迭代，内置 80% 进度催促机制
3. **多供应商 LLM 路由**：统一 OpenAI-compatible 协议，支持 DeepSeek / Qwen / Anthropic / GitHub Copilot / Ollama
4. **上下文预算管理**：100K 字符窗口，超限自动压缩历史工具输出至 500 字符
5. **Token 跟踪**：每次会话记录 input/output/total token 消耗与平均延迟

```python
# 对话引擎工作流
Chat Request → Session Lookup/Creation
    ↓
Build OpenAI-compatible message array (system + history + user)
    ↓
LLMClient HTTP POST (重试策略: 3次, 退避 [2, 5, 10]s)
    ↓
Tool Call Extraction + Permission Check
    ↓
Tool Execution (sandboxed) → 结果回填
    ↓
TurnResult (usage, tool_invocations, stop_reason)
    ↓
Session Persist + Transcript Store
```

#### 智能体工具箱 (AgentToolbox)

每个智能体拥有 7 个基础工具能力：

| 工具 | 功能 | 安全边界 |
|------|------|---------|
| `read_file` | 读取文件内容 | 路径白名单 |
| `grep` | 正则搜索代码 | 只读操作 |
| `list_files` | 列举目录结构 | 递归深度限制 |
| `write_file` | 写入文件 | 需要权限 |
| `patch_file` | 精确补丁修改 | 需要权限 |
| `run_python` | 执行 Python 脚本 | 沙箱环境 |
| `run_pytest` | 运行测试套件 | 隔离执行 |

#### Hermes 风格扩展

借鉴 NousResearch/Hermes-Agent 的设计理念：

- **概率工具集分布**：不同任务场景下，工具按概率激活（如 deep_analysis 模式下 code_execution 80%，web 60%）
- **跨会话持久记忆**：智能体可在多次对话间保持记忆
- **自动技能创建**：复杂研究结果自动凝结为可复用技能
- **子智能体委派**：支持最多 3 个并发子智能体执行并行任务
- **SOUL.md 人格注入**：每个智能体拥有独立的身份认同和行为准则

---

### 2. 议事广场 (Plaza)

> **"不是空谈——每次讨论都必须产出可执行的行动计划。"**

#### 设计灵感

议事广场的空间设计融合了三大建筑学理念：

- **维特鲁威比例** (Vitruvius) — D:H = 2:1 的声学完美比例，确保每个参与者的「声音」都能被听见
- **威尔士议会** (Welsh Senedd) — 环形阶梯式座席，中心为数字奇点，三层同心圆分布参与者
- **12 壁龛** — 为主持人、分析师、挑战者、综合者、观察者等 12 种角色预留专属席位

#### 讨论编排算法

广场的核心是一个 **LLM 驱动的多轮辩论编排引擎**：

```
第 1 轮: 主持人开题 → 各角色按优先级发言 → 主持人轮次总结
第 2 轮: 主持人追问 → 深入讨论 → 主持人汇总分歧
...
第 N 轮 (终轮): 主持人加权总结 → 生成执行计划表
```

**发言排序算法**：
```
优先级: architect(0) → researcher(1) → developer(2) → qa(3) → devops(4) → pm(5)
层级:    内圈(core) → 中圈(advisory) → 外圈(observer)
```

每轮包含 2-3 个交换组，组内成员轮转发言，确保多元视角。主持人在非终轮生成阶段性总结，在终轮生成带权重的最终结论。

#### 执行计划输出

每次讨论的最终产出不是一段总结文字，而是一张结构化的执行计划表：

| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |
|------|------|---------|--------|------|---------|
| 1 | 架构评审 | architect | P0 | - | 架构决策文档 |
| 2 | 单元测试补充 | qa | P1 | #1 | 覆盖率报告 |
| 3 | 部署脚本优化 | devops | P2 | #1 | CI/CD 配置 |

#### 用户介入机制

讨论不是黑箱。用户可以在任何时刻介入：

1. **主持人暂停** → 重定向讨论焦点
2. **指名回复** → 指定某个智能体回应
3. **补充发言** → 1-2 个相关角色跟进
4. **执行计划刷新** → 根据新信息自动更新

#### 实时流式传输 (SSE)

广场使用 Server-Sent Events 实时推送讨论进展：

| 事件类型 | 说明 |
|---------|------|
| `discussion_start` | 讨论创建 |
| `round_start` | 新一轮开始 |
| `message` | 智能体发言（流式） |
| `interjection_state` | 用户介入状态变更 |
| `plan_updated` | 执行计划更新 |
| `discussion_end` | 讨论结束 |

---

### 3. 技能萃取管线 (Extraction Pipeline)

> **"讨论中的洞察不应该消散——它们应该被萃取、验证、锁定，成为组织的永久资产。"**

#### 四阶段门控状态机

技能萃取采用工业级的 **四阶段门控管线**，每个阶段都有严格的准入条件：

```
  ┌──────────┐    Gate 1    ┌──────────┐    Gate 2    ┌──────────┐    Gate 3    ┌──────────┐
  │  DRAFT   │────────────▶│  REVIEW  │────────────▶│ APPROVAL │────────────▶│PUBLISHED │
  │ 团队内实验 │             │  同行评审  │             │  高级审批  │             │  全局发布  │
  └──────────┘             └──────────┘             └──────────┘             └──────────┘
                                                                                   │
                                                                            quality > 0.4
                                                                                   ▼
                                                                            ┌──────────┐
                                                                            │SOLIDIFIED│
                                                                            │ 版本锁定  │
                                                                            └──────────┘
```

#### 门控要求 (Gate Requirements)

每道门都定义了必须满足的条件：

| 门控 | 最少评审人数 | 必须身份 | 最少赞成数 | 特殊要求 |
|------|------------|---------|----------|---------|
| Gate 1: DRAFT→REVIEW | 1 | AUTHOR | 1 | 禁止自审 |
| Gate 2: REVIEW→APPROVAL | 2 | PEER + SENIOR | 2 | 跨团队要求 |
| Gate 3: APPROVAL→PUBLISHED | 1 | LEAD/ARCHITECT | 1 | quality_score > 0.4 |

#### Todo 驱动的工作流

门控缺口会自动生成待办事项（TodoItem），解决待办会触发自动推进：

```
Gate 检查 → 发现缺口（缺少 PEER 评审） → 生成 Todo
    ↓
评审员提交评审 → Todo 标记完成 → 重新评估门控
    ↓
门控条件满足 → 自动推进到下一阶段
```

#### SkillClaw 萃取链

技能从讨论中萃取到落地，经过四步精炼：

```
Filter（过滤）→ Improve（改进）→ Verify（验证）→ Solidify（固化）
```

- **Filter**：Jaccard 相似度 ≥ 0.85 去重，避免重复技能
- **Improve**：SkillEvolver 基于使用反馈迭代改进技能描述和参数
- **Verify**：SkillVerifier 通过测试用例和实际执行验证技能有效性
- **Solidify**：版本锁定，推送到所有采纳团队

#### 三层存储架构

| 层级 | 存储位置 | 访问速度 | 说明 |
|------|---------|---------|------|
| L1 | `Team.skills` 字典 | 最快（内存） | 团队内活跃技能 |
| L2 | `SkillStore` JSON + Domain Events | 快（文件） | 持久化 + 事件溯源 |
| L3 | `SkillRegistry` 内置默认 | 快（内存） | 系统预装技能 |

#### 技能谱系追踪

每个技能都记录完整的演化谱系：

```
parent_skill (v1.0) → child_skill (v1.1, improved by Team B)
                    → adopted_copy (v1.0, used by Team C)
                    → solidified (v1.1, locked, pushed to all adopters)
```

---

### 4. 系统演进引擎 (System Evolution)

> **"审查不是为了找茬，是为了让系统永远在变好——而且不允许退步。"**

#### 七阶段生命周期状态机

演进引擎管理每个改进项的完整生命周期：

```
DISCOVERED ──▶ DISPATCHED ──▶ IN_PROGRESS ──▶ VERIFY_PENDING ──▶ VERIFIED ──▶ CLOSED
     │                                              │
     │                                              ▼
     │                                           FAILED
     └──────────────── 重新发现 ◀──────────────────┘
```

#### 审查规则体系

系统内置 **44+ 条审查规则**，参照工业级标准：

| 标准来源 | 规则数量 | 覆盖范围 |
|---------|---------|---------|
| DNV CII (碳排放强度指标) | 8 | 能效评级、合规趋势 |
| IMO SOLAS (海上生命安全) | 10 | 系统可靠性、冗余设计 |
| MARPOL (防止船舶污染) | 8 | 资源泄漏、废弃物管理 |
| ClassNK (日本船级社) | 6 | 结构完整性、维护周期 |
| 自定义业务规则 | 12+ | 代码质量、测试覆盖率、安全 |

#### 合规评级算法

采用 **DNV CII 五级评分体系**：

```
A级 (85+): 重大优秀 — 系统表现卓越，持续引领
B级 (70-84): 轻微优秀 — 超出基线，持续改善中
C级 (55-69): 中等      — 符合基本要求，有改善空间
D级 (40-54): 轻微不足 — 需要纠正行动
E级 (<40):  不合格    — 紧急干预，系统性风险
```

**评分维度权重**（满分 100）：

| 维度 | 权重 | 说明 |
|------|------|------|
| compliance_score | 25% | 合规审查通过率 |
| test_pass_rate | 20% | 测试通过率 |
| code_quality_score | 20% | 代码质量评分 |
| security_score | 15% | 安全漏洞数量（反向映射） |
| documentation_level | 10% | 文档完备度 |
| performance_score | 10% | 性能影响评估 |

**一票否决项**：
- 存在严重安全漏洞 → 强制 E 级
- 存在破坏性变更 → 强制 E 级
- 关键测试失败 > 0 → 强制 E 级

#### Darwin Ratchet（达尔文棘轮）

这是系统演进的核心算法，灵感来自进化论的「不可逆进步」：

```
             ┌──────────────────────────────┐
             │     Heritage Ledger          │
             │   (遗产账本 — 不可篡改)       │
             │                              │
             │  Round 1: PUE 1.8 → 1.7  🔒  │
             │  Round 2: PUE 1.7 → 1.65 🔒  │
             │  Round 3: PUE 1.65 → 1.6 🔒  │
             │  ⚡ 累计节省: 42 kWh/day     │
             │  📉 PUE 只能降，不能升        │
             └──────────────────────────────┘
```

**棘轮规则**：
- **每一次 PUE 下降都会被锁定**，禁止回退（"once PUE decreases, never revert"）
- 使用 EWMA（指数加权移动平均）追踪 PUE 趋势
- 闭环节拍：Sense → Decide → Execute → Verify
- 配合 Musk 五步第一性原理审计：质疑每一瓦特的必要性

#### 升级梯度 (Escalation Tiers)

参照 DNV SEEMP Part III 标准的四级响应：

| 级别 | 触发条件 | 响应动作 |
|------|---------|---------|
| Normal | 评级 A/B | 常规监控，维持现状 |
| Corrective | 评级 C | 生成纠正计划，30 天内完成 |
| Review | 评级 D | 专项审查，涉及架构变更 |
| Hold | 评级 E | 系统暂停变更，全面整改 |

#### 地理围栏合规区域

受 Wärtsilä 航海合规系统启发，支持按坐标自动激活规则集：

| 区域 | 自动激活规则 |
|------|-------------|
| ECA (排放控制区) | 严格排放监控 |
| MARPOL | 防污染检查 |
| PSSA (特别敏感海域) | 环境影响评估 |

#### 事件溯源

所有演进记录采用 **不可变 JSONL 事件流**，保证完整的审计追踪：

```jsonl
{"ts":"2026-05-14T10:00:00Z","type":"item_discovered","item_id":"EVO-001","rule":"pue_threshold"}
{"ts":"2026-05-14T10:05:00Z","type":"item_dispatched","item_id":"EVO-001","team":"energy"}
{"ts":"2026-05-14T11:30:00Z","type":"item_verified","item_id":"EVO-001","result":"passed"}
{"ts":"2026-05-14T11:31:00Z","type":"ratchet_locked","delta_pue":-0.05,"cumulative_kwh":42}
```

---

## 四大模块如何协同运转

四个模块不是孤立运行的——它们构成一个 **自增强的飞轮**：

```
                           ┌──────────────────────────────┐
                           │    1. 演进引擎触发审查         │
                           │    发现 PUE 超过阈值           │
                           └───────────┬──────────────────┘
                                       │
                                       ▼
                           ┌──────────────────────────────┐
                           │    2. 议事广场召开讨论         │
                           │    6 个能源团队智能体辩论       │
                           │    产出: 执行计划表            │
                           └───────────┬──────────────────┘
                                       │
                                       ▼
                           ┌──────────────────────────────┐
                           │    3. 技能萃取管线处理         │
                           │    从讨论中提取「冷却策略优化」  │
                           │    经过 DRAFT→REVIEW→PUBLISHED│
                           └───────────┬──────────────────┘
                                       │
                                       ▼
                           ┌──────────────────────────────┐
                           │    4. 构建团队执行变更         │
                           │    developer 编写代码          │
                           │    tester 运行验证             │
                           │    deployer 部署上线           │
                           └───────────┬──────────────────┘
                                       │
                                       ▼
                           ┌──────────────────────────────┐
                           │    5. 演进引擎验证关闭         │
                           │    达尔文棘轮锁定 PUE 改善     │
                           │    合规评级从 C → B            │
                           │    ── 新一轮审查开始 ──        │
                           └──────────────────────────────┘
```

**具体数据流**：

1. **演进引擎** 44 条审查规则定期扫描 → 发现 `EvolutionItem`（如"PUE 超阈值"）
2. 将问题项提交到 **议事广场** → 6 个能源智能体在 3 轮讨论中辩论解决方案
3. 讨论结束后，执行计划中的关键步骤被 **技能萃取管线** 捕获
4. 萃取出的技能经过 Gate 审核后 PUBLISHED → 同步推送到相关团队
5. **构建团队** (Build Team) 基于执行计划和新技能执行代码变更
6. 演进引擎的 **验证阶段** 自动运行测试 → 通过后 **棘轮锁定** 改善
7. 合规评级更新 → 触发下一轮审查 → **飞轮继续转动**

**关键连接点**：

| 从 | 到 | 连接方式 |
|----|---|---------|
| 演进引擎 → 议事广场 | 审查发现项作为讨论议题 | `EvolutionItem` → `Discussion.topic` |
| 议事广场 → 技能萃取 | 讨论中的关键洞察 | `ExecutionPlan` → `ExtractionPipeline.submit()` |
| 技能萃取 → 智能体 | 发布的技能绑定到角色 | `PUBLISHED Skill` → `AgentProfile.skills[]` |
| 智能体 → 演进引擎 | 构建团队执行变更 | `AgentLoop` → `EvolutionExecutor.run_task()` |
| 演进引擎 → 演进引擎 | 棘轮锁定 + 新轮审查 | `Heritage Ledger` → `AuditRules.scan()` |

---

## 数字孪生与语音化身

> **"每个智能体不只是文字——它有声音、有角色、有性格。"**

### TTS 语音合成系统

系统采用 **双引擎架构** 实现智能体语音化身：

#### 主引擎: Microsoft Edge-TTS (Neural)

免费、高质量的神经网络语音，支持情感表达：

| 声音 | 风格 | 适用角色 |
|------|------|---------|
| `zh-CN-YunxiNeural` | 活泼阳光 | 研究员、文档 |
| `zh-CN-YunjianNeural` | 热情成熟 | 架构师、开发者 |
| `zh-CN-YunyangNeural` | 专业新闻 | 项目经理、测试 |

#### 备选引擎: GPT-SoVITS (声音克隆)

当需要更高度定制化的声音身份时，切换到本地部署的 GPT-SoVITS：

- 基于参考音频 + 提示文本实现零样本声音克隆
- 支持 Few-shot 微调，复刻特定人物音色
- 本地推理，延迟 < 3 秒

#### 智能语速自适应

系统根据文本长度和角色特征动态调整语速：

```python
# 文本越短，语速越慢（给听众反应时间）
< 20 字  → +8% 语速
< 60 字  → +12%
< 150 字 → +18%
> 150 字 → +22%（长段加速，避免拖沓）
```

#### 角色语音匹配

每个智能体角色有独立的语音 Profile，确保声音与角色一致：

```python
项目经理 → YunyangNeural (专业), rate +3%, pitch -2Hz
架构师  → YunjianNeural (沉稳), rate +2%, pitch -4Hz
开发者  → YunjianNeural (干练), rate +8%, pitch +1Hz
研究员  → YunxiNeural  (活泼), rate +4%, pitch +0Hz
```

#### 文本口语化预处理

LLM 输出的 Markdown 格式文本在合成前会被智能口语化：

- 去除代码块标记 (`` ` ``)、加粗 (`**`)
- 技术术语替换：`SLA` → "服务等级目标"，`CI/CD` → "持续集成和持续部署"
- 标点语调映射：`:` → `，`（逗号停顿），`\n` → `。`（句号换气）

### 数字孪生的实现路径

通过 TTS + 多智能体议事广场，每个智能体成为一个 **有声音、有角色、有观点的数字化身**：

```
                    🎙️ 数字孪生体
            ┌───────────────────────┐
            │  角色人格 (SOUL.md)    │  ← 性格、价值观、行为准则
            │  专业技能 (Skills[])   │  ← 领域知识、方法论
            │  语音化身 (TTS)        │  ← 独特音色、语速、音调
            │  行为记忆 (Memory)     │  ← 跨会话经验积累
            │  社交网络 (Channels)   │  ← 团队沟通、信息订阅
            └───────────────────────┘
```

在议事广场中，这些数字孪生体像真实会议参与者一样：
- **有各自的观点和立场**（基于角色 system_prompt）
- **有独特的声音**（TTS 角色语音匹配）
- **会记住之前的讨论**（跨会话记忆）
- **会相互质疑和补充**（多轮辩论机制）
- **会产出可执行的结论**（执行计划表）

### 智能体数字孪生可视化系统 (Digital Twin CLI)

> **"观测即理解——将智能体运行状态、交互关系、编排管线全部可视化。"**

#### 核心定位

**数字孪生 ≠ 监控面板。** 监控是被动观察，数字孪生是在虚拟空间中建立一个与真实系统实时同步的"镜像体"。这个页面的终极功能是让人类像操作飞行模拟器一样操控整个智能体团队——既能实时观测飞行状态，也能切到模拟模式做安全实验。

四层能力模型：

| 层级 | 能力 | 说明 |
|------|------|------|
| L1 | **观测 (Observe)** | 实时系统指标、协作拓扑、消息流——给整个 agent 系统装了一面单向玻璃 |
| L2 | **干预 (Intervene)** | 通过 CLI 直接调整智能体参数、注入指令、热替换技能，实时生效 |
| L3 | **推演 (What-if)** | 在不影响生产的情况下，模拟"如果把智能体从 A 团队调到 B 团队"会发生什么 |
| L4 | **回放与预测 (Replay & Forecast)** | 把过去协作全过程像录像一样重放，定位瓶颈；基于历史交互模式预测团队在新任务上的表现 |

当前已实现 L1（五大视图 + 拓扑联动）和 L2 雏形（CLI 命令），L3/L4 为演进方向。

#### 设计哲学

数字孪生可视化系统采用 **NVIDIA Agent Orchestration** 参考架构（六层模型），将智能体系统从抽象概念转化为可交互的实时可视化：

```
┌─────────────────────────────────────────────────────────────────┐
│ L1  用户界面层 (UI Layer)                                        │
│     Web 对话接口 + CLI 结构化命令 + 拖拽交互                       │
├─────────────────────────────────────────────────────────────────┤
│ L2  智能体编排层 (Orchestrator)                                   │
│     意图解析 · 多智能体协调 · 任务分配 · Handoff 交接               │
├─────────────────────────────────────────────────────────────────┤
│ L3  LLM 推理层 (Reasoning)                                       │
│     Function Calling · 思维链推理 (CoT) · 意图分类                 │
├─────────────────────────────────────────────────────────────────┤
│ L4  记忆与上下文层 (Memory)                                       │
│     技能库 · 知识图谱 · 会话历史 · 跨会话持久化记忆                  │
├─────────────────────────────────────────────────────────────────┤
│ L5  工具执行层 (Execution)                                        │
│     Web 搜索 · 代码执行 · API 调用 · 文件操作                      │
├─────────────────────────────────────────────────────────────────┤
│ L6  环境模拟层 (Environment)                                      │
│     虚拟空间拓扑 · 智能体定位移动 · 多智能体交互模拟                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 系统架构

```
                     ┌─────────────────────┐
                     │   digital-twin-cli  │
                     │      (前端 SPA)      │
                     └──────────┬──────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
    ┌─────────▼──┐    ┌────────▼───┐    ┌───────▼────────┐
    │ Agent API  │    │  DT State  │    │  Plaza/Chat    │
    │ /teams/    │    │  /digital- │    │  /plaza/       │
    │ /agents/   │    │  twin/     │    │  /bridge-chat/ │
    │ /skills/   │    │  state     │    │                │
    │ /tools/    │    │  move      │    │                │
    └────────────┘    │  interact  │    └────────────────┘
                      └────────────┘
```

#### 五大视图模块

| 视图 | 功能 | 核心算法 |
|------|------|---------|
| **架构总览** | 六层模型 + SVG 拓扑图 | 圆形布局 + 边权重计算 |
| **交互流** | 实时消息时间线 + 类型过滤 + 统计条 | 滚动窗口 + 分类计数 |
| **编排管线** | 5步任务流 + 动画执行 + 执行日志 | 有限状态机步进 |
| **环境空间** | 房间网格 + 拖拽分配 + 创建空间 | 拖拽DOM + 后端同步 |
| **CLI** | 终端界面 + 20+ 命令 + 命令历史 | 命令解析器 + API桥接 |

#### 核心算法

##### 1. 拓扑图布局算法 (Circular Layout + Edge Weighting)

智能体拓扑图采用极坐标圆形布局，边权重反映交互频率：

```javascript
// 圆形布局：将 N 个智能体等分到圆周上
for (i = 0; i < agents.length; i++) {
    angle = (2π × i) / N - π/2          // 起始角偏移 -90°
    x = cx + radius × cos(angle)
    y = cy + radius × sin(angle)
    nodeRadius = 16 + skills.length × 3  // 节点大小 ∝ 技能数量
}

// 边权重：从交互历史中统计双向连接强度
edgeMap[sorted(a.id, b.id)] += 1        // 每次交互+1
strokeWidth = min(4, 1 + count × 0.5)   // 线宽映射
opacity = min(0.8, 0.1 + count × 0.1)   // 透明度映射
```

**复杂度：** O(N) 节点布局 + O(M) 边统计，N=智能体数，M=交互消息数

##### 2. 管线状态机 (Pipeline FSM)

任务编排管线采用5步有限状态机，每步 800ms 动画推进：

```
     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
     │ 输入解析  │────▶│ 意图识别  │────▶│ 任务路由  │────▶│ 工具调用  │────▶│ 结果聚合  │
     │ (parse)  │     │ (intent) │     │ (route)  │     │ (exec)   │     │ (aggr)   │
     └──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
         idle    ────▶   active   ────▶   done
```

状态转换规则：
- `idle → active`: 定时器触发 (800ms interval)
- `active → done`: 下一步激活时当前步标记完成
- 进度条: `width = (step + 1) / totalSteps × 100%`

##### 3. 交互流滚动窗口 (Sliding Window)

采用定长滚动窗口维护交互消息历史：

```
消息存储策略:
- 内存保留: 最近 200 条
- 渲染窗口: 最近 50 条 (DOM 性能)
- localStorage 持久化: 最近 100 条
- 后端同步: 全量 interactions[]

过滤算法:
- 分类计数: O(N) 遍历统计 {tool-call, llm-call, handoff, broadcast, response}
- 类型过滤: Array.filter(m => m.type === selectedType)
```

##### 4. 拖拽分配算法 (Drag-and-Drop Room Assignment)

```
onDragStart(agentId):
    设置 dataTransfer = agentId
    添加 .dragging 视觉反馈

onDragOver(roomElement):
    preventDefault()  // 允许放置
    添加 .drag-over 高亮

onDrop(roomId):
    positions[agentId] = roomId    // 更新前端状态
    persist() → localStorage       // 本地持久化
    syncDtState() → PUT /state     // 后端同步
    POST /digital-twin/move        // 记录移动事件
    renderAgentList()              // 重绘左侧面板
    renderEnvironment()            // 重绘环境网格
    addMsg(type='handoff')         // 记录交互流
```

##### 5. 频率监控 (Frequency Chart)

滑动窗口实时频率统计：

```
数据结构: freqData[30]  (30个时间槽, 每槽2秒)
更新规则: 每2秒 push(isActive ? 1 : 0), shift()
可视化:   barHeight = value / max(freqData) × 100%
```

##### 6. 模拟算法

| 模式 | 策略 | 复杂度 |
|------|------|--------|
| `random` | 随机选取两个不同智能体，随机消息类型 | O(1) |
| `chain` | 按智能体列表顺序，依次传递消息 | O(N) |
| `stress` | 随机 min(20, N×3) 次交互，测试系统容量 | O(min(20,3N)) |

#### 使用方法

##### 访问页面

```bash
# 启动项目后访问:
http://localhost:5173/digital-twin-cli.html

# 或从团队管理页顶部导航栏点击「孪 数字孪生」
```

##### 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `Cmd/Ctrl + K` | 聚焦 CLI 输入框 |
| `Cmd/Ctrl + 1~5` | 切换视图（架构/交互/管线/环境/CLI）|
| `Escape` | 清空 CLI 输入 |
| `↑ / ↓` | CLI 历史命令导航 |

##### CLI 命令一览

**查询类：**

| 命令 | 说明 | 示例 |
|------|------|------|
| `status` | 系统状态摘要 | `status` |
| `agents` | 列出所有智能体 | `agents` |
| `skills` | 列出已注册技能 | `skills` |
| `tools` | 列出已注册工具 | `tools` |
| `rooms` | 列出环境空间 | `rooms` |
| `arch` | 显示六层架构 | `arch` |
| `inspect <name>` | 查看智能体详情 | `inspect PM` |
| `trace <name>` | 追踪智能体交互历史 | `trace Researcher` |

**编排类：**

| 命令 | 说明 | 示例 |
|------|------|------|
| `move <agent> <room>` | 移动智能体到空间 | `move PM 议事厅` |
| `interact <a1> <a2>` | 触发两智能体交互 | `interact PM Developer` |
| `broadcast <msg>` | 全局广播消息 | `broadcast 开始技能萃取` |
| `pipeline show` | 查看管线状态 | `pipeline show` |
| `pipeline run <task>` | 运行管线任务 | `pipeline run 需求分析` |
| `simulate <mode>` | 模拟交互 (random/chain/stress) | `simulate stress` |
| `discuss <topic>` | 创建广场讨论 | `discuss API设计评审` |
| `delegate <a1> <a2> <task>` | 委派任务 | `delegate PM Dev 编写测试` |
| `chat <msg>` | 与 AI 对话 | `chat 分析系统瓶颈` |

**工具类：**

| 命令 | 说明 | 示例 |
|------|------|------|
| `flow last <n>` | 最近 N 条交互 | `flow last 20` |
| `export <type>` | 导出 (snapshot/agents/skills) | `export snapshot` |
| `config show` | 查看配置 | `config show` |
| `config set <k> <v>` | 设置配置 | `config set team build_system` |
| `clear` | 清屏 | `clear` |

##### 拖拽分配智能体

1. 在左侧智能体列表中，**长按并拖动**任意智能体卡片
2. 切换到「环境空间」视图
3. 将智能体**放置到目标房间**卡片上
4. 系统自动更新位置并同步到后端

##### 导入/导出快照

```bash
# 导出：点击顶部「📤 导出」按钮，或在 CLI 中执行：
export snapshot

# 导入：点击顶部「📥 导入」按钮，选择之前导出的 JSON 文件
# 导入会恢复：房间配置、智能体位置、交互消息历史
```

##### 压力测试

```bash
# 在 CLI 中执行：
simulate stress
# 生成 min(20, 智能体数×3) 次随机交互
# 可在「交互流」视图实时观察消息涌入

# 链式传递测试：
simulate chain
# 智能体 A→B→C→D... 依次传递消息
```

#### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/agent-config/digital-twin/state` | 获取全局状态 |
| `PUT` | `/api/v1/agent-config/digital-twin/state` | 更新房间/位置 |
| `POST` | `/api/v1/agent-config/digital-twin/move` | 移动智能体 |
| `POST` | `/api/v1/agent-config/digital-twin/interact` | 记录交互事件 |
| `GET` | `/api/v1/agent-config/digital-twin/interactions` | 获取交互历史 |

#### 状态持久化策略

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   localStorage   │────▶│   Backend API    │────▶│  Server Memory   │
│  (即时响应)       │     │  (PUT /state)    │     │  (运行时缓存)     │
│  rooms           │     │                  │     │  _dt_state{}     │
│  positions       │     │  自动同步         │     │                  │
│  messages[100]   │     │  每次 persist()   │     │                  │
│  interactions    │     │  调用时触发        │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### 模块交互全景图

数字孪生作为**统一观测面板 + 编排中枢 + 模块间工作流粘合剂**：

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        数字孪生 (Digital Twin CLI)                               │
│                     统一观测面板 · 编排中枢 · 工作流粘合剂                          │
├──────────┬───────────┬───────────────┬──────────────┬──────────────────────────┤
│ 架构总览  │  交互流    │   编排管线     │   环境空间    │        CLI              │
│ +拓扑图   │  +SSE实时  │   +任务DAG    │   +房间管理   │    +工作流引擎           │
└────┬─────┴─────┬─────┴──────┬────────┴──────┬───────┴──────────┬──────────────┘
     │           │            │               │                  │
     ▼           ▼            ▼               ▼                  ▼
┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────────────────────┐
│智能体团队│ │议事广场  │ │技能萃取   │ │系统演进    │ │     任务引擎           │
│Agents   │ │Plaza    │ │Extraction│ │Evolution  │ │     TaskEngine         │
└─────────┘ └─────────┘ └──────────┘ └───────────┘ └────────────────────────┘
```

##### 与智能体团队 (Agents) 的交互

| 方向 | 交互 | 实现 |
|------|------|------|
| 读取 | 实时加载智能体列表、状态、技能、工具 | `GET /teams/{tid}/agents` |
| 写入 | 拖拽分配智能体到虚拟空间 | `POST /digital-twin/move` |
| 观测 | 左侧面板显示活跃状态、详情抽屉展示完整信息 | 30s自动刷新 |
| 编排 | CLI `inspect`/`trace` 深度审查单个智能体 | 交互历史追踪 |
| 健康 | 智能体健康度仪表盘：调用频率、成功率、响应时间 | `health` 命令 |

##### 与议事广场 (Plaza) 的交互

| 方向 | 交互 | 实现 |
|------|------|------|
| 发起 | CLI `discuss <topic>` 直接创建讨论 | `POST /plaza/{id}/discussions` |
| 观测 | 交互流视图订阅 SSE 实时消息流 | `GET .../discussions/{id}/stream` |
| 注入 | CLI `interject <msg>` 人类介入讨论 | `POST .../interject` |
| 转化 | 讨论结论 → 任务分派到管线视图 | `POST .../dispatch-and-execute` |
| 空间 | 讨论参与者自动聚集到"议事厅"房间 | 自动移动 + 环境视图 |

##### 与技能萃取 (Extraction) 的交互

| 方向 | 交互 | 实现 |
|------|------|------|
| 触发 | CLI `extract <source>` 触发萃取 | `POST .../skill-extract/start` |
| 观测 | 管线视图映射4阶段: DRAFT→REVIEW→APPROVAL→PUBLISHED | WebSocket |
| 审查 | CLI `review <skill_id>` 快速审批/拒绝 | `POST /pipelines/{id}/advance` |
| 验证 | 进度条反映 gate 通过状况 | `POST /pipelines/{id}/check-gate` |
| 统计 | 萃取漏斗可视化 (pending/yellow/green/approved) | `extract status` |

##### 与系统演进 (Evolution) 的交互

| 方向 | 交互 | 实现 |
|------|------|------|
| 注入 | CLI `evolve <item>` 推入演进引擎 | `POST .../evolve` |
| 观测 | 架构视图显示合规评级(A-E) + 演进项状态 | `GET /evolution/stats` |
| 追踪 | 交互流显示演进事件链 | event sourcing |
| 优化 | CLI `optimize <skill>` 触发 Hermes 循环 | `optimize_skill()` |
| 可视 | 技能进化树：baseline→mutation→improved | fitness曲线 |

##### 与任务引擎 (TaskEngine) 的交互

| 方向 | 交互 | 实现 |
|------|------|------|
| 创建 | `delegate`/`discuss dispatch` 产生任务 | `POST /teams/{tid}/tasks` |
| 观测 | 管线视图展示 DAG 依赖图 + 并发槽位 | `GET /task-engine/stats` |
| 控制 | CLI `task start/cancel/complete <id>` | REST API |
| 可视 | 甘特图/DAG图 + 并发度(semaphore=4) | `task dag` 命令 |

#### 流程优化设计

##### 优化 1: 议事厅讨论自动化闭环

```
CLI discuss ──▶ 议事广场(SSE多轮辩论) ──▶ 交互流(实时监控) ──▶ 管线(自动派发) ──▶ 任务执行
                        ↑ interject (人类注入)
```

##### 优化 2: 技能萃取质量门控

```
CLI extract ──▶ 萃取管线(LLM预填充) ──▶ Gate可视化(通过/阻塞) ──▶ CLI review ──▶ 绑定智能体
                        ↓ 漏斗统计: 待审N / 通过N / 拒绝N
```

##### 优化 3: 系统演进闭环加速

```
架构视图(合规仪表盘) ──▶ 演进引擎(审计规则) ──▶ 交互流(状态追踪) ──▶ 自动验证 ──▶ 评级更新
                                                        ↓ optimize ──▶ Hermes优化 ──▶ 自动替换
```

##### 优化 4: 智能体工作空间编排

```
环境空间(6房间) ──▶ 空间规则(议事厅=讨论, 萃取室=萃取, 工作坊=编码, 演练场=测试)
                        ↓ 任务开始时自动移动智能体到对应空间 → 上下文隔离 → 效率提升
```

#### 预定义工作流

```bash
# 工作流 1: 完整闭环 — 从讨论到代码
workflow full-loop "优化登录性能"
  → discuss → dispatch → task-execute → evolve-audit

# 工作流 2: 技能进化 — 从萃取到优化
workflow skill-evolve "API设计模式"
  → extract → review → optimize → bind

# 工作流 3: 质量巡检 — 全系统健康检查
workflow health-check
  → health → evolve-audit → extract-status → task-list → report
```

#### 演进路线图

| 阶段 | 目标 | 关键变化 |
|------|------|---------|
| Phase 1 ✅ | 观测+CLI控制 | 5视图 + 拖拽 + 20命令 |
| Phase 2 | SSE实时联动 | 接入Plaza SSE、Extraction WS |
| Phase 3 | 任务DAG可视化 | 管线视图升级为DAG图 |
| Phase 4 | 预定义工作流 | `workflow` 命令 + 编排器 |
| Phase 5 | 智能编排 | 自动调度 + 瓶颈预测 + 推荐优化 |

---

## SECS 自进化协同沙箱系统 (Self-Evolving Collaborative Sandbox)

> **"数字世界的二次映射——智能体的思维预演场"**

SECS 是数字孪生功能的核心升级，将孪生从"被动观测"进化为"主动预演+自主进化"。它为智能体提供了一个安全的虚拟试错空间，经过沙箱验证的最优策略才会被注入真实环境。

### 四维一体架构

```
┌────────────────────────────────────────────────────────────────┐
│            Layer 4: 集体智慧对齐 (DT-MADDPG)                    │
│        全局评论家 · 协同悖论检测 · 策略对齐 · SOP 输出            │
├────────────────────────────────────────────────────────────────┤
│            Layer 3: 策略试错实验 (TwinLoop)                      │
│     环境偏移检测 · 触发式仿真 · 并行What-if · 闭环注入           │
├────────────────────────────────────────────────────────────────┤
│            Layer 2: 认知进化循环 (AAS Zero-Exp)                  │
│       零经验启动 · 经验-反思-优化循环 · 双记忆系统 · SOP提取      │
├────────────────────────────────────────────────────────────────┤
│            Layer 1: 环境语义映射 (MADTwin)                       │
│     智能体状态 · 工作流拓扑 · 资源建模 · 约束语义化 · 快照       │
└────────────────────────────────────────────────────────────────┘
```

### 系统运行流程

```
快照与预警 → 沙箱试错 → 全局对齐 → 闭环注入
    │              │            │           │
  MADTwin 检测   AAS 零经验   DT-MADDPG    TwinLoop
  环境偏移       并行实验     评估优化      策略回注
```

1. **快照与预警**: WorldStateManager 实时感知数字世界状态，DriftDetector 检测环境偏移（任务突变/资源冲突/智能体故障/性能衰退），自动触发仿真
2. **沙箱试错**: TwinLoopEngine 创建智能体孪生副本，在加速沙箱中执行大量 What-if 推演（支持单场景/并行/演化三种模式）
3. **全局对齐**: GlobalCritic 从5个维度（任务完成率/通信效率/资源利用率/冲突避免/收敛速度）评估群体表现，ZeroExpEngine 提取协作 SOP
4. **闭环注入**: 只有验证通过的最优策略才被注入真实环境，同时固化经验到长期记忆

### 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| 数据模型 | `sandbox/models.py` | 全部数据结构（快照/经验/SOP/评估等） |
| 环境映射 | `sandbox/world_state.py` | MADTwin 二次映射 + 快照管理 |
| 双记忆 | `sandbox/memory_system.py` | 短期/长期经验 + 反思 + 启发式规则 |
| 仿真引擎 | `sandbox/twin_loop.py` | 仿真在环控制 + 并行策略对比 |
| 演化引擎 | `sandbox/zero_exp_engine.py` | 零经验循环 + SOP 提取 |
| 偏移检测 | `sandbox/drift_detector.py` | 5 类偏移检测 + 自动触发 |
| 全局评论家 | `sandbox/global_critic.py` | 5 维评估 + 建议生成 |
| 策略对齐 | `sandbox/strategy_aligner.py` | 协同悖论检测 + 对齐协议 |
| 编排器 | `sandbox/orchestrator.py` | 四维统一编排入口 |
| API | `sandbox/api.py` | REST + SSE 实时流 |
| Channel | `sandbox/channel.py` | MarineChannel 集成 |

### API 端点

```
POST   /api/v1/sandbox/sessions              # 创建沙箱会话
GET    /api/v1/sandbox/sessions              # 列出所有会话
GET    /api/v1/sandbox/sessions/{id}         # 获取会话详情
POST   /api/v1/sandbox/sessions/{id}/run     # 启动仿真
GET    /api/v1/sandbox/sessions/{id}/stream  # SSE 实时流
POST   /api/v1/sandbox/sessions/{id}/inject  # 注入最优策略
POST   /api/v1/sandbox/world/sync            # 同步世界状态
GET    /api/v1/sandbox/stats                 # 全局统计
GET    /api/v1/sandbox/drift/history         # 偏移历史
GET    /api/v1/sandbox/sops                  # SOP 库
GET    /api/v1/sandbox/memory/{agent_id}     # 智能体记忆
```

### 前端页面

访问 `sandbox-twin.html` 可看到完整的 SECS 仪表盘：
- 🌐 环境语义映射面板 — 智能体拓扑实时可视化
- 🎮 仿真控制面板 — 配置模式/步数/速度并一键启动
- 📊 仿真时间线 — 奖励曲线 + 步骤回放
- 🎯 全局评论家面板 — 5 维评分条 + 改进建议
- 📋 SOP 库 — 已提取的协作标准操作程序

---

## 系统架构总览

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (Vite + Vanilla JS)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 团队管理  │ │ 议事广场  │ │ 技能萃取  │ │ 系统演进  │           │
│  │ Config   │ │ Plaza    │ │ Extract  │ │ Evolution│           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │ SSE        │             │                  │
└───────┼────────────┼────────────┼─────────────┼──────────────────┘
        │            │            │             │
  ──────┼────────────┼────────────┼─────────────┼────── Vite Proxy
        │            │            │             │
┌───────┼────────────┼────────────┼─────────────┼──────────────────┐
│       ▼            ▼            ▼             ▼   FastAPI 8080   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Agent    │ │ Plaza    │ │Extraction│ │Evolution │           │
│  │ Config   │ │ Routes   │ │ Routes   │ │ API      │           │
│  │ API      │ │ + SSE    │ │ + WS     │ │          │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │             │                  │
│       ▼            ▼            ▼             ▼                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │              Core Services Layer                  │           │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │           │
│  │  │ChatHarness │  │PlazaEngine │  │Extraction  │ │           │
│  │  │+ AgentLoop │  │+ SSE Stream│  │Pipeline    │ │           │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘ │           │
│  │        │               │               │        │           │
│  │        ▼               ▼               ▼        │           │
│  │  ┌──────────────────────────────────────────┐   │           │
│  │  │         TeamManager + SkillLibrary       │   │           │
│  │  └──────────────────────────────────────────┘   │           │
│  └──────────────────────────────────────────────────┘           │
│       │            │            │             │                  │
│       ▼            ▼            ▼             ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                Channel Layer (MarineBase)                 │   │
│  │  SystemEvolution │ BridgeChat │ MergeChannel │ OpenClaw  │   │
│  └──────────────────────────────────────────────────────────┘   │
│       │            │            │             │                  │
│       ▼            ▼            ▼             ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Monitoring & Observability                     │   │
│  │  TraceCollector │ PlazaMonitor │ AdaptiveSampler          │   │
│  └──────────────────────────────────────────────────────────┘   │
│       │            │            │             │                  │
│       ▼            ▼            ▼             ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Storage Layer (File-based)                  │   │
│  │  JSON snapshots │ JSONL event streams │ Knowledge Base    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
        │                                           │
        ▼                                           ▼
 ┌──────────────┐                          ┌──────────────┐
 │  LLM APIs    │                          │  TTS Engine  │
 │  DeepSeek    │                          │  Edge-TTS    │
 │  Qwen        │                          │  GPT-SoVITS  │
 │  Anthropic   │                          │  (optional)  │
 │  Ollama      │                          └──────────────┘
 └──────────────┘
```

---

## 核心算法与设计模式

### 算法一览

| 算法 | 模块 | 用途 |
|------|------|------|
| **Darwin Ratchet** | 系统演进 | 不可逆进步锁定，防止性能退化 |
| **EWMA** | 演进 + OpenClaw | 指数加权移动平均追踪趋势 |
| **DNV CII 五级评分** | 演进引擎 | A~E 合规评级体系 |
| **Jaccard 相似度** | 技能萃取 | 技能去重（阈值 ≥ 0.85） |
| **TF-IDF Cosine** | 知识库 + 合并 | 语义搜索和聚类 |
| **Levenshtein 距离** | 相似度引擎 | 文本编辑距离匹配 |
| **Z-score 异常检测** | 监控系统 | 实时异常识别 |
| **Lamport Clock** | OpenClaw 同步 | 因果一致性保证 |
| **自适应采样** | 遥测收集 | P0:20% P1:20% P2:5%（异常时 100%） |

### 设计模式

| 模式 | 应用位置 | 说明 |
|------|---------|------|
| **事件溯源** | 演进、萃取、领域事件 | 不可变 JSONL 追加日志，完整审计追踪 |
| **物化视图** | JSON 快照缓存 | 从事件流重建状态，读写分离 |
| **状态机** | 萃取管线(4阶段)、演进(7阶段) | 严格状态转移，防止非法跳转 |
| **门控工作流** | 技能审核 | Todo 驱动的条件推进 |
| **发布/订阅** | Channel + EventBus | 17 种领域事件类型解耦 |
| **供应商抽象** | LLM 路由 | 统一 OpenAI-compatible 协议 |
| **三层缓存** | 技能存储 | 内存→文件→注册表 |
| **自适应降级** | 监控系统 | 异常时全量采集，正常时采样 |

---

## 智能体团队一览

### 🏗️ Build System 团队（构建系统）

全栈软件工程团队，覆盖从需求到部署的完整流程。

| 智能体 | 角色 | 职责 |
|--------|------|------|
| PM | 项目经理 | 任务拆解、进度跟踪、阻塞疏通 |
| Researcher | 研究员 | 技术调研、竞品分析、需求分析 |
| Architect | 架构师 | 系统设计、接口定义、模式选择 |
| Developer | 开发者 | 编码实现、调试、重构、测试 |
| Tester | 测试工程师 | 测试设计、执行、覆盖率分析、回归测试 |
| Deployer | 运维工程师 | CI/CD、容器管理、部署编排 |
| Doc Writer | 文档专家 | 技术文档、API 文档、变更日志 |

### 💻 AI Coding 团队（AI 编程）

精简的软件开发团队，中文优先。

| 智能体 | 角色 | 职责 |
|--------|------|------|
| 项目经理 | 协调者 | 需求分析、任务拆解、代码评审组织 |
| 技术研究员 | 研究员 | 技术选型、方案对比、可行性分析 |
| 全栈开发 | 开发者 | 代码生成、调试、重构、API 开发 |
| 测试工程师 | QA | 测试用例设计、自动化测试、缺陷跟踪 |

### ⚡ Energy First Principle 团队（能耗第一性原理）

专注数据中心能效优化的自演进团队，实现 Darwin Ratchet 进化机制。

| 智能体 | 角色 | 职责 |
|--------|------|------|
| PUE Optimizer | 能效优化器 | PUE 趋势监控、棘轮锁定、制冷优化 |
| Thermal Sentinel | 热场哨兵 | IoT 传感网监控、热岛检测、CRAC 风扇自适应控制 |
| Policy Engine | 策略引擎 | 节能策略评估、适应度评分、What-If 模拟 |
| Darwin Ratchet | 达尔文棘轮 | 遗产账本管理、棘轮锁定、Musk 五步审计 |
| Anomaly Watchdog | 异常看门狗 | Z-score 异常检测、传感器漂移识别、告警路由 |
| Forecast Planner | 预测规划师 | 24h PUE 预测、CAPEX/ROI 评估、CO₂ 计算 |

### ☁️ xOPs 团队（公有云运维运营）

多云运维管理团队，Hub-and-Spoke 架构，覆盖主流云厂商。

| 智能体 | 角色 | 职责 |
|--------|------|------|
| 云平台运维运营负责人 | 总协调 | 多云编排、FinOps、SLA 管理 |
| 平台SRE架构师 | SRE | HA 架构、SLO/SLI、灾备 |
| 自动化与平台工程师 | 平台工程 | CI/CD、IaC、IDP 建设 |
| 安全与合规工程师 | 安全 | IAM、网络安全、合规审计 |
| 值班与事件指挥官 | 应急指挥 | 故障响应、轮转管理、事后复盘 |
| FinOps分析师 | 成本分析 | 费用优化、RI/SP、预算管理 |
| AWS/Azure/Aliyun/GCP/国内云负责人 | 云服务 | 各云厂商账号、服务、架构管理 |

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- (可选) GPT-SoVITS 用于自定义语音克隆

### 1. 安装依赖

```bash
# 克隆项目
git clone <repo-url> AgentsGroup2026
cd AgentsGroup2026

# Python 后端
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn[standard] pydantic httpx edge-tts

# 前端
npm install
```

### 2. 配置

编辑 `config/settings.json`，配置 LLM API 密钥：

```json
{
  "llm": {
    "provider": "deepseek",
    "model": "deepseek-v4-pro",
    "api_key": "sk-your-key-here"
  }
}
```

编辑 `config/model_pool.json`，配置各团队的模型池。

### 3. 启动服务

```bash
# 方式一：一键启动
bash start.sh

# 方式二：分别启动
# 后端 (端口 8080)
cd src/backend && python main.py --port 8080

# 前端 (端口 5173，自动代理 API 到 8080)
npm run dev
```

### 4. 访问

打开浏览器访问 http://localhost:5173

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页 | `/` | 系统仪表盘 |
| 登录 | `/login.html` | 用户认证 |
| 团队管理 | `/agent-team-config.html` | 团队/智能体/模型/工具/技能配置 |
| 议事广场 | `/plaza.html` | 多智能体讨论界面 |
| 技能萃取 | `/extraction-pipeline.html` | 门控审核工作流 |
| 系统演进 | `/system-evolution.html` | 审查规则/合规评级/演进项 |
| 任务队列 | `/tasks.html` | 任务执行跟踪 |
| 系统监控 | `/monitoring.html` | 健康指标/遥测/告警 |

---

## API 参考

### 核心 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/health` | 健康检查 |
| `GET` | `/api/v1/info` | 系统信息 |
| `POST` | `/api/v1/auth/login` | 用户登录 |
| `POST` | `/api/v1/auth/register` | 用户注册 |

### 智能体配置

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/agent-config/teams` | 获取所有团队 |
| `GET` | `/api/v1/agent-config/teams/{team_id}` | 团队详情 |
| `GET` | `/api/v1/agent-config/teams/{team_id}/dashboard` | 团队仪表盘 |

### 议事广场

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/agent-config/plaza/discussions` | 创建讨论 |
| `POST` | `/api/v1/agent-config/plaza/discussions/{id}/start` | 启动讨论 |
| `GET` | `/api/v1/agent-config/plaza/discussions/{id}/stream` | SSE 实时流 |
| `POST` | `/api/v1/agent-config/plaza/discussions/{id}/interject` | 用户介入 |

### 技能萃取

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/extraction/pipelines` | 创建萃取管线 |
| `GET` | `/api/v1/extraction/pipelines/{id}` | 管线状态 |
| `POST` | `/api/v1/extraction/pipelines/{id}/review` | 提交评审 |
| `GET` | `/api/v1/extraction/pipelines/{id}/todos` | 获取待办 |

### 系统演进

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/agent-teams/evolution/status` | 引擎状态 |
| `POST` | `/api/v1/agent-teams/evolution/audit` | 触发审查 |
| `POST` | `/api/v1/agent-teams/evolution/cycle` | 运行演进周期 |
| `GET` | `/api/v1/agent-teams/evolution/compliance-rating` | 合规评级 |
| `GET` | `/api/v1/agent-teams/evolution/items` | 演进项列表 |
| `GET` | `/api/v1/agent-teams/evolution/rules` | 审查规则集 |
| `GET` | `/api/v1/agent-teams/evolution/zones/active` | 活跃合规区域 |

### Bridge Chat

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/bridge-chat/send` | 发送消息 |

### TTS 语音合成

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/tts` | 文本转语音（返回 MP3/WAV） |

---

## 项目结构

```
AgentsGroup2026/
├── config/
│   ├── settings.json                # 全局配置（LLM、TTS、OpenClaw）
│   └── model_pool.json              # 各团队模型池配置
├── src/
│   ├── backend/
│   │   ├── main.py                  # FastAPI 入口 + 启动编排
│   │   ├── agent_team_api.py        # 演进 API 路由
│   │   ├── startup_check.py         # 启动健康验证
│   │   ├── agents/                  # 🤖 多智能体框架
│   │   │   ├── models.py            # 核心数据模型
│   │   │   ├── team_manager.py      # 团队生命周期管理
│   │   │   ├── chat_harness.py      # UltraPlan 对话引擎
│   │   │   ├── agent_loop.py        # Function-calling 执行循环
│   │   │   ├── agent_toolbox.py     # 7 个基础工具
│   │   │   ├── hermes_research.py   # Hermes 风格自改进研究
│   │   │   ├── plaza.py             # 广场数据模型
│   │   │   ├── plaza_engine.py      # 讨论编排引擎
│   │   │   ├── plaza_routes.py      # 广场 REST + SSE API
│   │   │   ├── plaza_store.py       # 广场持久化
│   │   │   ├── extraction_pipeline.py  # 四阶段门控管线
│   │   │   ├── extraction_models.py    # 萃取数据模型
│   │   │   ├── extraction_routes.py    # 萃取 REST API
│   │   │   ├── extraction_store.py     # 萃取事件溯源存储
│   │   │   ├── skill_library.py     # SkillClaw 萃取链
│   │   │   ├── skill_evolver.py     # 技能迭代改进器
│   │   │   ├── skill_verifier.py    # 技能验证器
│   │   │   ├── skill_tracker.py     # 技能使用追踪
│   │   │   ├── skill_registry.py    # 内置技能注册表
│   │   │   ├── skill_store.py       # 技能持久化
│   │   │   ├── skill_indexer.py     # 技能索引器
│   │   │   ├── skill_querier.py     # 技能查询器
│   │   │   ├── skill_extractor.py   # LLM 技能提取器
│   │   │   ├── similarity_engine.py # 多策略相似度引擎
│   │   │   ├── knowledge_base.py    # TF-IDF 知识库
│   │   │   ├── merge_engine.py      # 合并聚类引擎
│   │   │   ├── gate_evaluator.py    # DNV 风格门控评分
│   │   │   ├── trajectory_analyzer.py  # 会话轨迹分析
│   │   │   ├── review_service.py    # 审核队列管理
│   │   │   ├── domain_events.py     # 17 种领域事件
│   │   │   ├── event_bus.py         # 发布/订阅事件总线
│   │   │   ├── ab_testing.py        # A/B 测试框架
│   │   │   ├── tts_routes.py        # TTS 语音合成 API
│   │   │   └── teams/               # 团队定义
│   │   │       ├── build_team.py    # 构建系统团队 (7 agents)
│   │   │       ├── ai_coding_team.py # AI 编程团队 (4 agents)
│   │   │       ├── energy_team.py   # 能耗优化团队 (6 agents)
│   │   │       └── xops_team.py     # 多云运维团队 (11 agents)
│   │   ├── channels/                # 📡 Channel 通信层
│   │   │   ├── marine_base.py       # Channel 基类
│   │   │   ├── system_evolution.py  # 系统演进 Channel
│   │   │   ├── bridge_chat.py       # Bridge Chat Channel
│   │   │   ├── merge_channel.py     # 相似度合并 Channel
│   │   │   └── openclaw_sync.py     # OpenClaw 多云同步
│   │   └── monitoring/              # 📊 可观测性
│   │       ├── collector.py         # 遥测收集器
│   │       ├── sampler.py           # 自适应采样器
│   │       ├── aggregation_window.py # 聚合窗口
│   │       └── plaza_monitor.py     # 广场监控 Channel
│   └── frontend/                    # 🖥️ 前端页面
│       ├── index.html               # 系统仪表盘
│       ├── login.html               # 登录页
│       ├── agent-team-config.html   # 团队管理
│       ├── plaza.html               # 议事广场
│       ├── plaza-wabisabi.html      # 侘寂风格广场
│       ├── extraction-pipeline.html # 技能萃取管线
│       ├── system-evolution.html    # 系统演进面板
│       ├── skill-extract.html       # 技能提取工作流
│       ├── tasks.html               # 任务队列
│       ├── monitoring.html          # 监控仪表盘
│       ├── datacenter-ratchet-evolution.html  # 数据中心棘轮演进
│       ├── css/                     # 样式文件
│       └── js/                      # 交互逻辑
├── storage/                         # 💾 持久化存储
│   ├── knowledge_base/              # 知识库 JSON 文件
│   ├── discussions/                 # 广场讨论记录
│   ├── tasks/                       # 任务记录
│   └── teams/                       # 团队配置缓存
├── package.json
├── pyproject.toml
├── vite.config.mjs                  # Vite 配置（API 代理）
└── start.sh                         # 一键启动脚本
```

---

## 技术栈

### 后端

| 技术 | 用途 |
|------|------|
| **Python 3.11+** | 运行时 |
| **FastAPI** | Web 框架 + SSE + WebSocket |
| **Uvicorn** | ASGI 服务器 |
| **Pydantic** | 数据验证与序列化 |
| **httpx** | 异步 HTTP 客户端（LLM API 调用） |
| **edge-tts** | Microsoft 神经网络语音合成 |
| **asyncio** | 异步并发（广场讨论、任务执行、遥测） |

### 前端

| 技术 | 用途 |
|------|------|
| **Vite 6** | 开发服务器 + API 代理 |
| **Vanilla JS** | 无框架依赖，轻量直出 |
| **Three.js** | 3D 可视化（数据中心棘轮演进） |
| **SSE (EventSource)** | 实时流式更新 |

### LLM 供应商

| 供应商 | 模型 | 场景 |
|--------|------|------|
| **DeepSeek** | V4-Pro / V4-Flash | 主力推理 |
| **Qwen** | 3.6-27B-FP8 | 本地/边缘部署 |
| **Anthropic** | Claude | 复杂分析 |
| **GitHub Copilot** | copilot-chat | 代码生成 |
| **Ollama** | 各种开源模型 | 本地开发 |

### TTS 引擎

| 引擎 | 特点 | 用途 |
|------|------|------|
| **Edge-TTS** | 免费、高质量神经语音、3 种男声 | 主引擎，议事广场语音化身 |
| **GPT-SoVITS** | 零样本声音克隆、Few-shot 微调 | 备选，自定义声音身份 |

---

## 未来计划

### 🎯 近期 (2026 Q3-Q4)

- **多模态议事广场**：支持图表、白板、代码片段的实时协作讨论
- **技能市场 (Skill Marketplace)**：跨组织的技能发现、订阅和交易
- **实时 3D 数字孪生**：基于 Three.js 的数据中心能耗实时 3D 可视化，将 Darwin Ratchet 的每一步进化映射为可交互的空间变化
- **GPT-SoVITS 深度集成**：每个智能体拥有独立克隆声音，实现真正的「声音身份」
- **多语言支持**：英文/日文议事广场，跨语言团队协作

### 🚀 中期 (2027 H1)

- **自治演进 (Autonomous Evolution)**：演进引擎完全自主运行——发现问题→开会讨论→萃取技能→编写代码→测试部署→锁定改善，无需人类干预
- **联邦学习技能共享**：多个 AgentsGroup 实例间安全共享技能，保护敏感数据
- **Embodied Agent**：将数字孪生扩展到物理世界——连接 IoT 设备、机器人、数据中心传感器
- **智能体性格进化**：基于长期交互数据，智能体的 traits 和 SOUL.md 自适应演化
- **OpenClaw 生态**：开放协议对接第三方智能体平台，形成多平台协作网络

### 🌐 远期愿景

- **组织级 AI 操作系统**：AgentsGroup 成为企业的 "AI 团队操作系统"——所有 AI 工作通过团队协作完成，技能持续积累，系统永远在变好
- **群体智能涌现**：当足够多的智能体团队在足够多的领域积累了足够多的技能，群体智能将超越任何单一模型的能力
- **永续进化**：达尔文棘轮的终极形态——系统的每一次改善都是不可逆的，组织的 AI 能力只增不减

---

## 更新日志

### 2026-05-18

#### 导航体系统一

为所有主要页面补全了统一的跨页面导航，使各模块之间可以直接跳转：

| 页面 | 新增/调整内容 |
|------|------------|
| `plaza.html` | nav-links 新增「数字孪生」 |
| `plaza-dark.html` | nav-links 新增「孪生」（日式风格保持一致） |
| `plaza-wabisabi.html` | nav-links 新增「数字孪生」 |
| `plaza-wabisabi-v2.html` | nav-links 新增「数字孪生」 |
| `plaza-old.html` | nav-links 新增「数字孪生」 |
| `skill-extract.html` | topbar-nav 新增「数字孪生」；「智能体团队」调整至「议事广场」之前 |
| `system-evolution.html` | 侧边栏底部新增「数字孪生」快捷按钮 |
| `digital-twin-cli.html` | header-actions 新增「议事广场」「技能萃取/赋予」「系统演进」「智能体」导航；「← 主控台」改名为「智 智能体」 |

#### agent-team-config.html 导航栏重排

- 顶栏右侧按钮顺序调整为：**议事广场 → 技能萃取/赋予 → 数字孪生 → 系统演进 → 导出 → 导入 → 创建团队**
- 「技能萃取」按钮改名为「技能萃取/赋予」，反映该页面包含萃取与赋予两种模式
- 导出/导入按钮位置从顶部最左移至「系统演进」与「创建团队」之间（`agent-team-config.js` 由 `prepend` 改为 `insertBefore(createBtn)`）

#### skill-extract.html 页面名称统一

- `<title>` 及 `<h1 id="mode-title">` 统一改为「技能萃取/赋予」
- `_switchPageMode()` 函数两个分支（extract / router）均输出「技能萃取/赋予」，去除模式间标题切换差异

#### 数字孪生协作拓扑修复（digital-twin-cli.html）

- **过滤联动**：拓扑节点改为只显示左侧已选团队（`selectedTeams`）中的智能体，与左侧面板保持一致；原来显示全量 `S.agents`
- **颜色统一**：节点颜色从全局索引 `i%6` 改为按团队着色（`teamColorMap`），颜色与左侧团队标签完全匹配
- **实时刷新**：`toggleTeam()` 切换团队过滤时，若协作拓扑当前可见，立即同步重绘

---

<p align="center">
  <em>"不是让 AI 替代人，而是让 AI 像团队一样工作——开会、辩论、学习、进化。"</em>
</p>
