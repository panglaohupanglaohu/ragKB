# Methodology: Plaza-to-Evolution Closed-Loop Agent Team Optimization

## Research Question
Does a closed loop (Plaza discussion → Skill extraction → Evolution → Validation → Skill re-assignment) converge to measurably better agent team compositions?

## Hypotheses
H1: ORID-structured Plaza → higher contract niche-skill specificity → better evolution.
H2: Dominant skills from evolution → higher survival when re-assigned.
H3: 3+ closed-loop iterations → stable dominant skill set.

## Data Sources
1. Existing 9-run data (物竞闭环评估报告-aws-build.md): 45 agents across 9 evolutionary configurations
2. Plaza discussion contracts: AWS-ops and Build-system task domains
3. Code analysis: eco_drill.py (step, mate, era), plaza_engine.py (run_discussion)

## Closed-Loop Architecture
```
Phase 1 — Plaza讨论:
  Agents in Plaza → ORID-structured discussion → ExecutionPlan → TaskHabitatContract
  Metrics: contract niche count, demanded_skills specificity

Phase 2 — Skill萃取:
  From Contract demanded_skills + agent skill profiles → initial skill_genome assignment
  From discussion content (NLP extraction) → supplementary skills

Phase 3 — 演化选择:
  Contract → EcoDrill (metabolic constraint + ecological pressure)
  Four tournament modes tested: solo, division, confrontation, mixed
  Multi-generation mixed mode → dominant skill emergence
  
Phase 4 — 验证评估:
  Metrics: survival ticks (τ), skill%, collab%, dominant skill list
  Statistical test: quadratic regression of collab% on resource abundance (A)
  
Phase 5 — Skill赋予:
  Dominant skills identified from mixed-mode evolution
  Re-assigned to agent profiles for next Plaza discussion
  Re-evolution with updated skill genomes → measure τ improvement
```

## Experiment Design

### Experiment 1: Plaza Structure Effect (H1)
- Condition A: Baseline Plaza (current Moderator-led, seat-tier)
- Condition B: ORID Plaza (4-layer structured Facilitator, Fist-to-Five consensus)
- Same task topic in both conditions
- Compare: Contract niche specificity (number of demanded_skills per niche, skill coverage)
- N=3 discussion runs per condition

### Experiment 2: Evolution as Skill Filter (H2)
- Contraction from Phase 1 enters EcoDrill
- Mixed-mode, 9 generations (A=0.55, P=0.16, D=0.18, K=3)
- Identify dominant skills from survival
- Re-assign dominant skills to new agents → re-evolve → compare τ

### Experiment 3: Closed-Loop Iteration (H3)
- 3+ cycles of: Discuss→Extract→Evolve→Validate→Re-equip→Discuss
- Track: dominant skill set stability (Jaccard similarity between iterations)
- Track: mean τ improvement per iteration

## Statistical Plan
- Primary: Quadratic regression of collab% on A (existing analysis, R²=0.43, p<0.01)
- Secondary: Paired t-test of τ between dominant-skill and random-skill teams
- Convergence: Jaccard similarity between iteration i and i+1 dominant skill sets

## Limitations
- Single run per evolutionary configuration (no replication)
- Plaza contract generation by LLM introduces variability
- 9-run data from previous report — no new cloud GPU compute needed
