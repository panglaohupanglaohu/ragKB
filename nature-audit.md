# Nature Components Audit: Darwinian Natural Selection × LLM Agent Evolution

## Darwin's Four Necessary Conditions for Natural Selection

Darwin (1859) identified four conditions that, when met, make natural selection inevitable:

| # | Condition | Our Nature Implementation | Status |
|---|-----------|--------------------------|--------|
| 1 | **Variation** — individuals differ in traits | Skill genomes (S), CollabGenome (share/signal/follow) vary per agent | ✅ |
| 2 | **Heritability** — traits pass parent→offspring | Vertical inheritance (crossover+mutation), horizontal (blind learning, adoption) | ✅ |
| 3 | **Struggle for existence** — limited resources → competition | Resource abundance A, niche capacity K, metabolic decay μ | ✅ |
| 4 | **Differential fitness** — some reproduce more than others | Survival ticks τ as native fitness; mate intention L triggered by sustained health | ✅ |

Darwin's four conditions are **all met**. The framework is logically complete as a natural selection system.

## Beyond Darwin: Components Added to Nature (with justification)

| Component | Biological Analog | In Our Nature |
|-----------|------------------|---------------|
| **Predator pressure (P)** | Stochastic mortality from predation, accidents | Random failure probability independent of skill |
| **Requirement drift (D)** | Environmental change, shifting niches | Task demand changes over time |
| **Niche capacity (K)** | Carrying capacity per ecological niche | Max concurrent successful foragers per tick |
| **Scarce share boost** | By-product mutualism under scarcity economics | share_fraction amplified when A < 1.0 |
| **Signal protocol** | Animal communication (alarm calls, food calls, courtship displays) | FOOD/HELP/COURT signals with metabolic cost |

These go BEYOND Darwin's necessary conditions — they represent the Modern Synthesis and Extended Evolutionary Synthesis additions.

## Gaps Identified — What Nature Currently Lacks

### 1. Darwin's SECOND mechanism: Sexual Selection — ✅ IMPLEMENTED (2026-07-16)
Darwin identified **two** mechanisms of evolution: Natural Selection AND Sexual Selection.

**Now**: `mate_choosiness` × `evolution_pressure.sexual_selection_strength` drives quality-weighted mate choice (survival + COURT honest signal + skill complementarity). Baseline path (ss=0) keeps choosiness→pool-top for zero-regression tests.

### 2. Spatial Population Structure
Wright's shifting balance theory (1931) and modern spatial population genetics demonstrate that **spatial segregation + migration** drives speciation. Our agents exist in a well-mixed panmictic population — every agent can interact with every other.

**Missing**: Geographic isolation, demes, migration rates between subpopulations.

### 3. Frequency-Dependent Selection — ✅ IMPLEMENTED (2026-07-16)
**Now**: negative frequency dependence via `freq_dep_strength` — rare skills get forage p_ok + reward boost proportional to `(1 - f_s)`.

### 4. Environmental Periodicity (Seasonal Cycles)
Real ecosystems have cyclical fluctuations (seasons, day/night, El Niño). The extended evolutionary synthesis emphasizes that **temporal environmental structure** shapes adaptation differently from constant pressure.

**Missing**: Scheduled oscillation of A, P, D on predictable cycles (currently only monotonic or random).

### 5. Coevolution Between Teams (Red Queen)
Van Valen's Red Queen hypothesis: species must constantly evolve to survive against ever-evolving opponents. In our system, predator pressure P is a static parameter, not an evolving agent. The confrontation mode is competition, not coevolution.

**Missing**: Co-adapting adversarial populations where improvement in one team drives counter-adaptation in another.

### 6. Epistasis & Gene Interaction Networks — ✅ IMPLEMENTED (2026-07-16)
**Now**: `epistasis_strength` awards non-additive forage bonus when genome holds adjacent demand skill pairs.

### 7. Senescence — ✅ IMPLEMENTED (2026-07-16)
Engineering safeguard: `senescence_rate × survival_ticks` extra metabolic cost prevents immortal monopolists collapsing genetic diversity.

## Recommendations for System Enhancement

| # | Gap | 是否为物竞天择的主要驱动因素？ | 系统实现必要性 | 理由 |
|---|-----|-------------------------------|--------------|------|
| 1 | **Sexual Selection** | 是 — Darwin 命名了 **两种** 演化机制 | ✅ **已实现** | `sexual_selection_strength` × mate_choosiness；COURT/生存/互补加权择偶 |
| 2 | **Frequency-Dependent Selection** | 是 — 罕见性状常享有选择优势 | ✅ **已实现** | `freq_dep_strength` 负频率依赖，防 skill 池垄断 |
| 3 | **Epistatic Skill Synergy** | 是 — 基因交互效应是定量遗传学标准组件 | ✅ **已实现** | `epistasis_strength` demand 相邻对非加性加成 |
| 7 | **Senescence** | 否（工程防垄断） | ✅ **已实现** | `metabolism.senescence_rate` μ×age（**Agent 侧**，非环境压） |
| 4 | **Environmental Periodicity** | 否 — 环境周期是背景属性，不是选择机制的组成部分 | ❌ 不需要 | 增加了测试复杂度但不对选择机制本身产生质变 |
| 5 | **Spatial Deme Structure** | 否 — 空间结构影响演化速度，不影响演化逻辑 | ❌ 不需要 | 生态位隔离（分场/对抗赛制）已功能等价 |
| 6 | **Co-evolutionary Teams** | 否 — Red Queen是演化结果而非选择机制本身 | ❌ 不需要 | 对抗赛制已产生类似共同适应效应 |

## Papers Supporting These Recommendations

- **Frank, S.A. (2012)** "Natural selection. IV. The Price equation" — fundamental partition of evolutionary change into selection + transmission components
- **Frank, S.A. (2012)** "Natural selection. V. How to read the fundamental equations of evolutionary change in terms of information theory" — selection as information accumulation
- **Lenski et al. (2003)** "The evolutionary origin of complex features" — Avida digital evolution with resource constraints
- **Boyd & Richerson (1985)** "Culture and the Evolutionary Process" — dual inheritance, gene-culture coevolution
- **Odling-Smee et al. (2003)** "Niche Construction" — organisms modify their selective environments
- **Nowak, M.A. (2006)** "Five Rules for the Evolution of Cooperation" — conditions under which cooperation emerges
- **West-Eberhard, M.J. (2003)** "Developmental Plasticity and Evolution" — phenotypic plasticity in evolution
- **Pigliucci & Müller (2010)** "Evolution: The Extended Synthesis" — framework beyond the Modern Synthesis
---

## 2020-2026年间理论根基检验：Darwin自然选择是否被颠覆？

### 直接回答：没有。Darwin自然选择作为演化逻辑主干未被推翻，也未显著削弱。

### 详细分析

**1. Extended Evolutionary Synthesis (EES) — 补充而非替代**

Pigliucci & Muller (2010) 和 Laland et al. (2015) 提出的Extended Synthesis主张四个额外演化维度：
- 表型可塑性 (phenotypic plasticity)
- 生态位构建 (niche construction)  
- 发育偏向 (developmental bias)
- 包容性遗传 (inclusive inheritance)

EES的论证是：Modern Synthesis 不充分（insufficient），而非不正确（incorrect）。Laland本人最明确的表态是："We are not replacing the Modern Synthesis — we are extending it."

**2. 构建性中性演化 (Constructive Neutral Evolution, CNE) — 边缘挑战**

Stoltzfus (1999, 2012) 主张复杂特征可以通过中性过程积累，无需选择压力。CNE解释的是复杂性的起源，而非适应性的起源。适应性状仍然需要自然选择来解释。

**3. Third Way of Evolution — 未达成学界共识**

Koonin, Shapiro, Noble 等人批评基因中心主义，但核心论点已被EES和现代系统生物学吸收，未构成对自然选择的独立挑战。

**4. 数字进化/ALife的反复验证**

从Avida (Lenski 2003) 到 ASAL++ (2025) 到 Flow-Lenia (2025) 到本研究的45个Agent：在计算系统中，自然选择有效。代谢约束+生存适应度产生了可复现的适应性行为。

**5. 2025年的学界共识**

自然选择是适应性演化的主要（但不唯一）机制。中性过程（遗传漂变）、发育约束和生态位构建发挥补充作用。Modern Synthesis已被"延伸"而非"替代"。

### 需要警觉而非恐慌的学术前沿

| 前沿方向 | 对Darwin框架的影响 | 是否需要修正Nature？ |
|----------|-------------------|---------------------|
| Extended Synthesis | 补充，不替代 | 可添加Niche Construction环节 |
| 中性演化 | 解释复杂性来源 | 不需要 |
| 表型可塑性 | 基因型-表型映射更具动力学 | 可在表型层面添加环境交互 |
| 生态位构建 | 生物主动改造选择环境 | 允许dominant技能回写contract |

### 结论

Darwin自然选择框架对LLM Agent团队优化的工程应用是充分且可靠的理论基础。
