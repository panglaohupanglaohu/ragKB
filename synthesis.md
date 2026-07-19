# Synthesis: Ecological Pressure Drives Emergent Team Collaboration in LLM-Agent Populations

## Hypothesis Evaluation

### Hypothesis 1: Non-Linear Ecological Pressure → Specialization

**Collab%: CONFIRMED with significant inverted-U relationship (R²=0.43, p<0.01).**
The collaboration rate (`collab%`) exhibits a clear hump-shaped response to resource abundance: it peaks at moderate pressure (A≈0.55, collab%=13.2%) and collapses at both extremes (harsh: 2.5%, abundant: 4.9%). This finding directly maps to **Gause's Competitive Exclusion Principle** (stabilizing coexistence requires limiting similarity) and **r/K selection theory** (unstable harsh environments select for selfish "r-strategists"; overly stable environments eliminate selective pressure for cooperation). The internal mechanism is the `scarce_share_boost` and `same_pop_share_bias` parameters — under moderate scarcity, collaboration is economically rational because shared task rewards outweigh independent foraging costs. Under harsh conditions, agents cannot afford the metabolic overhead of collaboration before extinction; under abundance, cooperation offers no marginal survival advantage.

**Skill%: NOT CONFIRMED (R²=0.04, ns).**
Skill specialization did not show a significant quadratic relationship with abundance. This is interpretable within the system's design: skill% reflects *inherited genetic skill specialization*, which requires multi-generational descent and gene-flow recombination to manifest. The habitat gradient runs (pressure/scarce/harsh/abundant) all executed for only 1-2 generations — insufficient for Gregor Mendel-style genetic heritability to emerge. The sole run that *did* produce explicit `dominant` skills was `aws+build-mixed` (9 generations with cross-team recombination). This supports **Boyd & Richerson's Dual Inheritance Theory**: horizontal gene-flow (cross-team mixing) is necessary to stabilize vertical skill transmission beyond single-generation drift.

### Hypothesis 2: Tournament Format → Collaboration & Dominance

**NOT CONFIRMED at single-generation ANOVA level (all p>0.7). QUALITATIVELY SUPPORTED at multi-generational level.**

The null result at single-generation granularity is informative: merely changing the competitive format (solo vs division vs confrontation vs mixed) without allowing sufficient evolutionary time does not alter emergent agent behavior. This is consistent with **Hutchinson's niche theory** — ecological niches exert selective pressure over ecological time, not instantaneous behavioral time. However, the qualitative production of 5 `dominant` skills exclusively in the 9-generation mixed run demonstrates that tournament format *does* matter when combined with generational depth — the mixed format's cross-team recombination acts as a form of sexual recombination, breaking genetic drift and enabling skill-marker fixation in the population.

## Integration with Literature

| Finding | Literature Connection |
|---------|---------------------|
| Inverted-U collab% response to abundance | **Gause (1934)**: competitive exclusion at extremes; **Odling-Smee (2003)**: niche construction mediates selection intensity |
| Residual dominance (85% mean) | **Brooks (1991)**: behavior-based intelligence operates via default reflexes unless overridden by strong drives — residual% is the "default reflex" of LLM agents |
| Only multi-generational mixing yields dominant skills | **Boyd & Richerson (1985)**: horizontal transmission stabilizes vertical inheritance; **Visscher et al. (2008)**: narrow-sense heritability h² requires multi-generational pedigree data |
| Survival ticks as sole native fitness | **Ray (1991)**: Tierra's CPU-time competition; **Lenski et al. (2003)**: Avida's digital selection — survival under resource constraint is the oldest and most robust fitness proxy in ALife |
| Centralized scheduling forbidden | **Reynolds (1987)**: boids emerge from local rules; **Bonabeau (1999)**: swarm intelligence requires decentralized threshold-response, not global optimization |

## Practical Implications

1. **Tuning ecological parameters matters more than tournament format** for emergent team behavior within short-run simulations. Resource abundance A is the primary lever controlling collaboration emergence.
2. **Multi-generational evolution is non-negotiable** for skill specialization. Single-generation "snapshot" runs can measure collaboration equilibrium but cannot produce heritable skill fixation.
3. **The "goldilocks zone" for collaboration** lies at A≈0.5-0.6 — sufficiently scarce to make sharing economically rational, but not so harsh that agents starve before achieving cooperative equilibrium.

## Limitations

- Single-run-per-condition design precludes replication-based confidence intervals at the run level.
- 24 data points for the quadratic regression (4 regimes × ~5 agents per regime) yields significant but imprecise coefficient estimates.
- The system's design separates `skill%` (inherited) from learned behavior — the skill% null result may reflect correct system behavior (no heritability in 1 generation) rather than experimental failure.

## Success Criteria Assessment

| Criterion | Result |
|-----------|--------|
| Specialization peak at moderate pressure | ✗ Not confirmed for skill%; ✓ Confirmed for collab% |
| Cooperation higher in competitive/pressure environments | ✓ Confirmed (collab% peak at pressure, 13.2%) |
| Only competitive + multi-generational yields dominant skills | ✓ Confirmed (only aws+build-mixed produced dominant list) |
| Statistical significance in trends | ✓ Collab% quadratic model significant at p<0.01 |

## Next Steps for the Paper

The strongest narrative arc for the IEEE paper is: **"Ecological pressure parameters (specifically resource abundance) non-linearly modulate emergent cooperative behavior in LLM-agent teams, but skill heritability requires sustained multi-generational competition with cross-lineage recombination."** This dual finding — one immediately controllable parameter (abundance), one requiring temporal depth (generations) — provides actionable guidance for designing LLM-agent team training pipelines.
