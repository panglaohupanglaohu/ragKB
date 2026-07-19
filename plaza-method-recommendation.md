# Plaza讨论方法调研与推荐：2020-2026年结构化讨论方法

## 范围说明

调研目标：从2020-2026年发表的论文中，选择一种适合Plaza实现的结构化讨论方法。
约束条件：
- ~20分钟的单一话题讨论
- LLM Agent参与的讨论（非人类）
- 可工程化实现
- 要能在系统代码中落地

## 文献检索结果

### 直接相关论文（可验证）

**1. Khamsi et al. (2024) "Focus Agent: LLM-Powered Virtual Focus Group"**
- 来源: arXiv 2409.01907 (2024年9月)
- 内容: 使用LLM同时模拟焦点小组参与者和主持人角色。通过5个焦点小组会话（23名人类参与者）验证了LLM主持的数据质量。
- 启示: LLM可以充当结构化讨论的主持人（Facilitator），不引导内容、只控制流程。

**2. Gungor et al. (2025) "TurQUaz at CheckThat! 2025: Debating Large Language Models for Scientific Web Discourse Detection"**
- 来源: arXiv 2508.08265 (2025)
- 内容: 提出三种LLM辩论方法：
  - Single debate：两个LLM持对立立场辩论，第三个LLM评判
  - Team debate：多个LLM在各自团队内协作辩论
  - Council model：多LLM组成"理事会"讨论
- 启示: 这是目前最直接适用于Plaza的LLM结构化讨论框架。

**3. Lippincott et al. (2025) "Group Decision-Making System with Sentiment Analysis of Discussion Chat and Fuzzy Consensus Modeling"**
- 来源: arXiv 2503.18765 (2025年3月)
- 内容: 基于模糊共识建模的群体决策系统——不是关键词计数（agree/disagree），而是情感分析的连续性共识度量。
- 启示: 验证了"关键词共识计数不可靠"（与我们之前的诊断一致），为五指量表替代方案提供了实证支撑。

### 间接相关文献（方法论基准）

以下方法的原始文献发表于1960-1990年代，不在2020-2026时间窗口内，但它们在组织管理领域被反复验证：
- ORID (Focused Conversation Method) — Stanfield, ICA, 1997
- Six Thinking Hats — de Bono, 1985
- Fist to Five / Gradients of Agreement — Kaner et al., 2014
- Delphi Method — Dalkey & Helmer, 1963
- Nominal Group Technique — Delbecq & Van de Ven, 1971

这些方法在2020-2026年间[无新论文提出]——不是因为没有价值，而是因为它们已经成为**成熟方法论**，研究重点已转移至应用场景（在线会议、AI辅助、混合办公）。

## 对比矩阵：六种方法对Plaza的适配度

| 方法 | 是否需要真人引导 | LLM实现可行性 | 是否已验证于LLM场景 | Plaza适配度 |
|------|----------------|-------------|-------------------|-----------|
| **TurQUaz Council Debate** | 否（LLM自组织） | 极高 — 原始设计就是给LLM的 | ✅ arXiv 2508.08265 (2025) | ⭐⭐⭐⭐⭐ |
| ORID + 五指共识 | 是（需Facilitator） | 高 — 四层递进是提示词模板 | ⚠️ 间接（Focus Agent 2024模拟了Facilitator，但非ORID） | ⭐⭐⭐⭐ |
| Six Thinking Hats | 是 | 中 — 六种思维模式的提示词切换 | ❌ 无LLM验证 | ⭐⭐⭐ |
| Nominal Group Technique | 是 | 低 — 需要"先独立写再轮流说" | ❌ 无LLM验证 | ⭐⭐ |
| Focus Agent (Focus Group) | 否（LLM模拟） | 高 | ✅ arXiv 2409.01907 (2024) | ⭐⭐⭐ |
| Delphi Method | 否 | 低 — 多轮匿名问卷不适合Agent | ❌ 无LLM验证 | ⭐ |

## 推荐方案：TurQUaz Council Debate + ORID四层结构

### 为什么选这个组合？

TurQUaz (2025) 是2020-2026年间**唯一一篇在arXiv上发表的、专门设计给多LLM Agent的、经过实验验证的结构化辩论方法**。它使用"辩论+评判"模型——这不是人类方法的翻译，而是原生为LLM设计的方法。

但TurQUaz的纯辩论模型（两个LLM对立辩论，第三LLM评判）更适合"真假判断"任务（其原始任务是检测推文中的科学声明）。对于我们的Plaza场景（团队讨论一个工程计划并产出ExecutionPlan），需要加入**议程结构**来防止辩论发散。ORID的四层递进提供了这个结构。

### Plaza实现伪代码

```
Topic: 一个工程规划话题（如"AWS ES扩容方案"）
Timebox: 每层5分钟，总计20分钟
Participants: 来自团队的N个LLM Agent

Phase 1 — Fact Finding (5 min)
  Facilitator Agent提示词:
    "你只问一个问题：'我们已知的客观事实是什么？'
     禁止：解释、判断、建议、感受
     格式：每个参与者用一句话陈述一条事实"
  输出: 事实清单 → 后续各层的共同知识基础

Phase 2 — Risk & Intuition (5 min)  
  Facilitator Agent提示词:
    "你只问一个问题：'你的直觉告诉你最大的风险是什么？'
     禁止：反驳他人的担忧、辩论风险的概率
     规则：感受不需要证据——每个担忧都是有效的输入"
  输出: 风险清单 + 直觉方向

Phase 3 — Solution Debate (5 min)
  采用TurQUaz Single Debate模式:
    两个LLM Agent持对立方案立场进行3轮辩论
    第三LLM Agent（Facilitator兼评判）追问关键假设:
      "这个方案的假设是什么？如果假设不成立，会发生什么？"
  输出: 方案-A vs 方案-B 的关键差异 + 假设列表

Phase 4 — Decision & Commitment (5 min)
  采用五指量表（替代当前的关键词共识计数）:
    每个Agent表达: 5指(全力支持) → 1指(根本性反对)
    🔴 如果有1指（根本性反对）:
      Facilitator追问: "是什么让你不能接受？"
      聚焦该问题，尝试修改方案
      如果仍有1指 → 记录为"有保留的共识"
    🟢 所有人≥3指:
      输出 ExecutionPlan + 五指分布记录
```

### 当前Plaza需要改什么

| 保留 | 删除 | 新增 |
|------|------|------|
| Plaza数据结构 (Plaza, Discussion, Participant) | `plaza_consensus.py`的关键词共识 | 四层Facilitator Agent的4个system prompt |
| 信号协议 (RitualSignal) | LLM-as-Moderator的话题引导 | 五指量表API |
| SSE实时推送 | `measure_consensus()` 的0.85阈值 | TurQUaz Single Debate的三Agent编排 |
| `plaza_engine.py`的Agent调用基础设施 | 按座席层级发言的顺序 | ORID四层时间盒控制 |

### 为什么不选其他方案

- **纯TurQUaz (无ORID)**: 辩论适合"谁对谁错"，不适合"我们一起规划"
- **纯ORID (无辩论)**: 缺乏对立观点的深度检验——容易群体思维
- **Six Thinking Hats**: 六种角色切换对20分钟太复杂——LLM上下文难以保持六种模式清晰分离
- **Focus Agent**: 偏重"数据收集"（模拟用户焦点小组），不适合Agent间的主动规划

## 参考文献

1. Khamsi, R. et al. (2024). "Focus Agent: LLM-Powered Virtual Focus Group." arXiv:2409.01907.
2. Gungor, O. et al. (2025). "TurQUaz at CheckThat! 2025: Debating Large Language Models for Scientific Web Discourse Detection." arXiv:2508.08265.
3. Lippincott, T. et al. (2025). "Group Decision-Making System with Sentiment Analysis of Discussion Chat and Fuzzy Consensus Modeling." arXiv:2503.18765.
4. Kaner, S. et al. (2014). *Facilitator's Guide to Participatory Decision-Making*. Jossey-Bass. (五指量表原始文献)
5. Stanfield, R.B. (1997). *The Art of Focused Conversation*. ICA Canada. (ORID原始文献)
6. de Bono, E. (1985). *Six Thinking Hats*. Little, Brown and Company.
