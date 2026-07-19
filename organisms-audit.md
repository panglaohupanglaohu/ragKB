# Organisms Components Audit: Darwinian Individual × LLM Agent Evolution

**2026-07-16修正**：原始推荐#1 "技能衰减/用进废退"存在范畴错误。见下文§修正说明。

## Darwin's View of Organisms

Darwin recognized individuals as the unit of selection. Four organism-level properties enable natural selection:

| # | Property | Our Organisms Implementation | Status |
|---|----------|------------------------------|--------|
| 1 | **Individual variation** | Skill Genome + CollabGenome vary per agent | ✅ |
| 2 | **Overproduction** | mate intention triggers reproduction; niche capacity K limits survivors | ✅ |
| 3 | **Struggle for existence** | niche capacity competition, metabolic decay, outcompeted penalty | ✅ |
| 4 | **Differential survival & reproduction** | survival ticks τ determines mate eligibility | ✅ |

---

## ⚠️ 修正说明：为什么"用进废退"是错误的范畴

原始推荐#1 "技能衰减 —— 不用的技能逐渐衰退避免囤积无用基因" 存在问题：

**Darwin的"适者生存"机制**：Nature不关心个体技能的熟练度是否衰减。Nature只做一件事——代谢约束。拥有不匹配生态位需求的技能的个体，在觅食中持续失败→饥饿→恐惧→休眠。技能的有用性或无用性是由Nature的客观选择压力判定的，不需要额外的"衰减规则"来辅助。

**这是一个宏观过程**：不需要个体层面的主动"用进废退"。囤积了无用基因的个体，代谢惩罚（genome_carry_cost）已经让它在竞争中处于劣势 → 饿死 → 基因自然从基因池中消失。这是Nature宏观选择的结果，不是个体主动"废退"的结果。

**正确框架**：
- 让Nature通过代谢约束+生态位需求，自然地淘汰携带无用技能的个体 —— **这是物竞天择**
- 不应该在系统里加一个额外的"衰减规则"替Nature做判断 —— 这是越俎代庖

---

## Current Organisms Components (from code)

| Layer | Component | Location | Status |
|-------|-----------|----------|--------|
| Gene | Skill Genome (S) | Creature.skill_genome | ✅ |
| Gene | CollabGenome (share/signal/follow/choosiness) | CollabGenome | ✅ |
| Gene | Skill proficiency (表型表达水平) | Creature.skill_proficiency | ✅ |
| Physiology | Health Ledger | health_ledger | ✅ |
| Mental | Hunger (H), Fear (F), Libido (L) | eco_loop.py | ✅ |
| Behavior | Intention (avoid/forage/mate/rest) | eco_loop.py | ✅ |
| Behavior | Signal emission (FOOD/HELP/COURT) | step() | ✅ |
| Learning | Blind learning (随机技能获取) | step() REST_EXPLORE | ✅ |
| Memory | Fear window (recent_outcomes) | Creature | ✅ |
| Memory | WorldView (peer/signal visibility) | WorldView | ✅ |
| Role | Agent role (aws-ops/build_system) | Creature.role | ✅ |
| Reproduction | Mate (crossover+mutation) | _mate_pair() | ✅ |

---

## 修正后的Gap分析

### 1. ~~技能衰减~~ → 已删除，Nature通过代谢约束+生态位选择自然淘汰无用技能

---

## 关于2020-2026年间理论根基的检验

参见 `nature-audit.md` 中的详细分析。核心结论：
- **Darwin自然选择作为演化逻辑主干未被推翻，也未被显著削弱**
- Extended Evolutionary Synthesis (EES) 做的是**补充**而非**替代**
- 2020-2026年间没有颠覆性论文挑战自然选择的核心有效性
- 数字演化/ALife领域的大量实证（包括本文的45个Agent）反复验证了自然选择在计算系统中的功能

对于LLM Agent团队优化的工程应用而言，Darwin框架是充分且可靠的理论基础。
