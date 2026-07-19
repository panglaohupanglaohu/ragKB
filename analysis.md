# Analysis: Ecological Pressure and Emergent Skill Specialisation

## Executive Summary
9 evolutionary simulation runs (45 agents, 5 per run) were parsed from the `物竞闭环评估报告-aws-build.md` evaluation report. The runs span two task domains (AWS Ops and Build System), three tournament formats (solo/division, confrontation, mixed-competitive), and four controlled ecological-pressure regimes (harsh, scarce, pressure, abundant) parameterized by resource abundance A ∈ {0.35, 0.45, 0.55, 1.40}.

## Hypothesis 1: Non-Linear Ecological Pressure → Specialization

**Test**: Quadratic regression of resource abundance A on agent-level `skill%` and `collab%`.

| Metric | Intercept | A (linear) | A² (quadratic) | R² | Significance |
|--------|-----------|------------|-----------------|-----|--------------|
| skill% | −0.045 | 0.305 (p=0.54) | −0.181 (p=0.51) | 0.042 | ✗ Not supported |
| collab% | −0.275 | 1.126 (p=0.004) | −0.639 (p=0.004) | 0.430 | ✓ **Supported** |

**Interpretation**: The inverted-U hypothesis is **supported for collaboration emergence (collab%)** but **not supported for skill specialization (skill%)**. Among sampled regimes, collab% peaks in the moderate-scarcity band (scarce A=0.45 → 13.6%; pressure A=0.55 → 13.2%) and collapses at extremes (harsh 2.5%, abundant 4.9%). The fitted quadratic vertex is near A≈0.88 (between pressure and abundant sample points). This aligns with ecological r/K selection theory: intermediate resource levels foster cooperative strategies, while extremes select for either selfish survival (harsh) or indifferent solipsism (abundant).

For skill%, the null finding suggests that skill specialization may require additional mechanisms beyond raw metabolic pressure — specifically, multi-generational temporal depth (cf. the `aws+build-mixed` run, which ran for 9 generations and produced the only `dominant` skill list). A single generation per environmental regime may be insufficient for skill-level selective pressures to manifest.

## Hypothesis 2: Tournament Format → Collaboration & Dominance

**Test**: One-way ANOVA across tournament formats (solo, division, confrontation, mixed).

| Metric | F-statistic | p-value | Significance |
|--------|------------|---------|--------------|
| skill% | 0.237 | 0.870 | ✗ ns |
| collab% | 0.198 | 0.897 | ✗ ns |
| residual% | 0.468 | 0.707 | ✗ ns |

**Interpretation**: No significant effect of tournament format on agent-level skill% or collab% within single-generation runs. However, a **qualitative emergent signal** appeared exclusively in the `mixed` format: only this run (at 9 generations) produced a non-empty `dominant` skill list containing 5 skills (`coverage_analysis`, `aws_es_scaling_orchestration`, `interface_definition`, `monitor_alarms_setup`, `e21d7092`). This suggests that multi-generational competitive mixing, rather than single-generation format alone, is the necessary condition for skill dominance to crystallize.

## Survival Dynamics

| Regime | Abundance | Best T | Mean residual% | Interpretation |
|--------|-----------|--------|----------------|----------------|
| abundant | 1.40 | 86 | 92.3% | Lowest pressure, longest lifespan, maximal residual behavior |
| pressure | 0.55 | 67 | 78.9% | Peak collab% (13.2%), moderate survival decline |
| scarce | 0.45 | 61 | 82.7% | Enhanced collab% (13.6%), declining survival |
| harsh | 0.35 | 60 | 92.6% | Collab collapses (2.5%), survival near-minimum |

The survival gradient: abundant (86) > pressure (67) > scarce (61) > harsh (60), confirms that metabolic pressure directly translates to reduced lifespan — validating the `HealthLedger` mechanism.

## Residual Dominance Problem

A consistent finding: residual behavior dominates across all conditions (mean=85.0%). Even in the most specialized agent (`build_architect`, skill%=28.77%), residual% remained at 71.23%. This reflects a system-level property: the LLM-agent ecological simulator's native behavioral economy is dominated by non-specialized "background" activity, and skill specialization must be actively carved out through sustained multi-generational selective pressure.

## Key Visualizations

1. `figures/fig1_hump_shaped_abundance.png` — Inverted-U relationship of collab% (significant) vs abundance, with skill% overlaid (ns). Error bars show ±1σ.
2. `figures/fig2_tournament_comparison.png` — Boxplots of skill% and collab% across 4 tournament formats. No significant main effect.
3. `figures/fig3_survival_comparison.png` — Boxplots of survival ticks (T) across all 9 runs, showing the abundance → survival gradient.
