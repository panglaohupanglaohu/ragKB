#!/usr/bin/env python3
"""Parse 物竞闭环评估报告-aws-build.md, run statistics, generate IEEE-quality figures."""

import re, os, sys, json, ast
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from statsmodels.formula.api import ols
from scipy import stats

# ── Paths ──────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "docs", "物竞闭环评估报告-aws-build.md")
OUT_CSV = os.path.join(ROOT, "experiments_raw.tsv")
FIGDIR = os.path.join(ROOT, "figures")
os.makedirs(FIGDIR, exist_ok=True)

# ── Style ───────────────────────────────────────────────────────────
plt.rcParams.update(
    {
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 13,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
    }
)

# ── Parse ───────────────────────────────────────────────────────────
text = open(REPORT).read()
# Split into runs by "### " headers
sections = re.split(r"\n### ", text)[1:]  # skip frontmatter

records = []
run_meta = {}

for sec in sections:
    lines = sec.strip().split("\n")
    run_name = lines[0].strip()
    # --- metadata line: - bestT=... gens=... skill%=... collab%=...
    meta_line = ""
    habitat_raw = {}
    dominant_list = []
    for li in lines[1:]:
        if li.startswith("- bestT="):
            meta_line = li
        elif li.startswith("- dominant="):
            dom = li.split("=", 1)[1].strip()
            if dom == "[]":
                dominant_list = []
            else:
                dom = dom.strip("[]")
                dominant_list = [
                    s.strip().strip("'\"") for s in dom.split(",") if s.strip()
                ]
        elif li.startswith("- habitat="):
            hab_str = li.split("=", 1)[1].strip()
            if hab_str == "None":
                habitat_raw = {}
            else:
                try:
                    habitat_raw = ast.literal_eval(hab_str)
                except:
                    habitat_raw = {}

    # parse meta_line
    m = re.search(
        r"bestT=(\d+).*?gens=(\d+).*?skill%=([\d.]+).*?collab%=([\d.]+)", meta_line
    )
    if m:
        bestT = int(m.group(1))
        gens = int(m.group(2))
        run_skill_mean = float(m.group(3))
        run_collab_mean = float(m.group(4))
    else:
        bestT = gens = run_skill_mean = run_collab_mean = None

    A = habitat_raw.get("abundance", None)
    P = habitat_raw.get("predator_pressure", None)
    D = habitat_raw.get("drift_prob", None)
    C = habitat_raw.get("niche_capacity", None)

    # Determine tournament type
    if "solo" in run_name:
        tourney = "solo"
    elif "mixed" in run_name:
        tourney = "mixed"
    elif "confrontation" in run_name:
        tourney = "confrontation"
    else:
        tourney = "division"

    # Determine habitat regime
    if "habitat-pressure" in run_name:
        regime = "pressure"
    elif "habitat-scarce" in run_name:
        regime = "scarce"
    elif "habitat-harsh" in run_name:
        regime = "harsh"
    elif "habitat-abundant" in run_name:
        regime = "abundant"
    else:
        regime = "base"  # default / non-modulated

    # --- table rows ---
    in_table = False
    for li in lines:
        if li.startswith("| Agent | Pop | T |"):
            in_table = True
            continue
        if in_table and (li.startswith("|---") or li.startswith("| ---")):
            continue
        # Also skip rows that are clear separator artifacts
        cols_check = [c.strip() for c in li.split("|")[1:-1]]
        if in_table and all(
            c.strip() in ("---", "—", "") or c.strip() == "" for c in cols_check if c
        ):
            continue
        if in_table and li.startswith("|") and "|" in li[1:]:
            cols = [c.strip() for c in li.split("|")[1:-1]]
            if len(cols) >= 7:
                agent = cols[0]
                pop = cols[1]
                try:
                    T_val = int(cols[2])
                except:
                    T_val = None
                try:
                    sk = float(cols[3]) if cols[3] != "" else 0.0
                except:
                    sk = None
                try:
                    cl = float(cols[4]) if cols[4] != "" else 0.0
                except:
                    cl = None
                try:
                    rs = float(cols[5]) if cols[5] != "" else 0.0
                except:
                    rs = None
                skill_list_raw = cols[6] if len(cols) > 6 else ""
                skill_list = [
                    s.strip().strip("'\"")
                    for s in skill_list_raw.split(",")
                    if s.strip()
                ]

                records.append(
                    {
                        "run": run_name,
                        "agent": agent,
                        "pop": pop,
                        "T": T_val,
                        "skill_pct": sk,
                        "collab_pct": cl,
                        "residual_pct": rs,
                        "skill_list": skill_list,
                        "bestT": bestT,
                        "gens": gens,
                        "run_skill_mean": run_skill_mean,
                        "run_collab_mean": run_collab_mean,
                        "tournament": tourney,
                        "regime": regime,
                        "abundance": A,
                        "predator_pressure": P,
                        "drift_prob": D,
                        "niche_capacity": C,
                        "dominant": dominant_list,
                        "n_dominant": len(dominant_list),
                    }
                )

df = pd.DataFrame(records)
df.to_csv(OUT_CSV, sep="\t", index=False)
print(f"Parsed {len(df)} agents across {df['run'].nunique()} runs → {OUT_CSV}")

# ── Statistical Summary ────────────────────────────────────────────
print("\n=== Per-Run Summary ===")
run_summary = (
    df.groupby("run")
    .agg(
        agents=("agent", "count"),
        bestT=("bestT", "first"),
        gens=("gens", "first"),
        mean_skill_pct=("skill_pct", "mean"),
        max_skill_pct=("skill_pct", "max"),
        mean_collab_pct=("collab_pct", "mean"),
        max_collab_pct=("collab_pct", "max"),
        mean_residual_pct=("residual_pct", "mean"),
        n_dominant=("n_dominant", "first"),
        tournament=("tournament", "first"),
        regime=("regime", "first"),
        abundance=("abundance", "first"),
    )
    .round(4)
)
print(run_summary.to_string())

# ── H1 Test: Quadratic regression of abundance on skill_pct ─────────
print("\n=== H1: Abundance × skill_pct (quadratic) ===")
h1_df = df[df["abundance"].notna()].copy()
h1_df["A2"] = h1_df["abundance"] ** 2
model = ols("skill_pct ~ abundance + A2", data=h1_df).fit()
print(model.summary().tables[1])
print(f"R² = {model.rsquared:.4f}, AIC = {model.aic:.2f}")

# collab
model_col = ols("collab_pct ~ abundance + A2", data=h1_df).fit()
print("\nH1: Abundance × collab_pct (quadratic):")
print(model_col.summary().tables[1])
print(f"R² = {model_col.rsquared:.4f}, AIC = {model_col.aic:.2f}")

# ── H2 Test: Tournament format ANOVA ────────────────────────────────
print("\n=== H2: Tournament format ANOVA ===")
for var in ["skill_pct", "collab_pct", "residual_pct"]:
    groups = [
        df[df["tournament"] == t][var].dropna().values
        for t in ["solo", "division", "confrontation", "mixed"]
    ]
    f_stat, p_val = stats.f_oneway(*groups)
    print(f"{var}: F={f_stat:.4f}, p={p_val:.4f}")

# ── FIGURE 1: Hump-shaped abundance × skill/collab ──────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left: skill_pct vs abundance
ax = axes[0]
hab_regimes = (
    df[df["abundance"].notna()]
    .groupby("regime")
    .agg(
        A=("abundance", "first"),
        skill_mean=("skill_pct", "mean"),
        skill_std=("skill_pct", "std"),
        label=("regime", "first"),
    )
)
colors_regime = {
    "harsh": "#d62728",
    "scarce": "#ff7f0e",
    "pressure": "#2ca02c",
    "abundant": "#1f77b4",
}

for _, r in hab_regimes.iterrows():
    ax.errorbar(
        r["A"],
        r["skill_mean"],
        yerr=r["skill_std"],
        fmt="o",
        capsize=5,
        color=colors_regime.get(r["label"], "gray"),
        label=r["label"],
        markersize=10,
    )

# Quad fit curve
A_vals = np.linspace(0.30, 1.45, 100)
A2_vals = A_vals**2
coef = model.params
fit_vals = coef["Intercept"] + coef["abundance"] * A_vals + coef["A2"] * A2_vals
ax.plot(
    A_vals,
    fit_vals,
    "k--",
    linewidth=1.5,
    label=f"Quadratic fit (R²={model.rsquared:.3f})",
)

ax.set_xlabel("Resource Abundance (A)")
ax.set_ylabel("Mean Agent skill%")
ax.set_title("(a) Skill Specialization vs Abundance")
ax.legend(fontsize=9, framealpha=0.8)
ax.grid(alpha=0.3)

# Right: collab_pct vs abundance
ax = axes[1]
hab_regimes_c = (
    df[df["abundance"].notna()]
    .groupby("regime")
    .agg(
        A=("abundance", "first"),
        collab_mean=("collab_pct", "mean"),
        collab_std=("collab_pct", "std"),
        label=("regime", "first"),
    )
)
for _, r in hab_regimes_c.iterrows():
    ax.errorbar(
        r["A"],
        r["collab_mean"],
        yerr=r["collab_std"],
        fmt="s",
        capsize=5,
        color=colors_regime.get(r["label"], "gray"),
        label=r["label"],
        markersize=10,
    )

coef_c = model_col.params
fit_c = coef_c["Intercept"] + coef_c["abundance"] * A_vals + coef_c["A2"] * A2_vals
ax.plot(
    A_vals,
    fit_c,
    "k--",
    linewidth=1.5,
    label=f"Quadratic fit (R²={model_col.rsquared:.3f})",
)
ax.set_xlabel("Resource Abundance (A)")
ax.set_ylabel("Mean Agent collab%")
ax.set_title("(b) Collaboration vs Abundance")
ax.legend(fontsize=9, framealpha=0.8)
ax.grid(alpha=0.3)

plt.tight_layout()
fig.savefig(f"{FIGDIR}/fig1_hump_shaped_abundance.png")
print(f"Saved {FIGDIR}/fig1_hump_shaped_abundance.png")

# ── FIGURE 2: Tournament format comparison ──────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
tourney_order = ["solo", "division", "confrontation", "mixed"]
tourney_labels = ["Solo", "Division", "Confrontation", "Mixed"]
palette = {
    "solo": "#999999",
    "division": "#2ca02c",
    "confrontation": "#ff7f0e",
    "mixed": "#d62728",
}

sns.boxplot(
    data=df,
    x="tournament",
    y="skill_pct",
    order=tourney_order,
    palette=palette,
    ax=axes[0],
)
axes[0].set_xticklabels(tourney_labels)
axes[0].set_xlabel("Tournament Format")
axes[0].set_ylabel("Agent skill%")
axes[0].set_title("(a) Skill Specialization by Tournament")
axes[0].grid(alpha=0.3, axis="y")

sns.boxplot(
    data=df,
    x="tournament",
    y="collab_pct",
    order=tourney_order,
    palette=palette,
    ax=axes[1],
)
axes[1].set_xticklabels(tourney_labels)
axes[1].set_xlabel("Tournament Format")
axes[1].set_ylabel("Agent collab%")
axes[1].set_title("(b) Collaboration by Tournament")
axes[1].grid(alpha=0.3, axis="y")

plt.tight_layout()
fig.savefig(f"{FIGDIR}/fig2_tournament_comparison.png")
print(f"Saved {FIGDIR}/fig2_tournament_comparison.png")

# ── FIGURE 3: Survival T across runs ────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 6))
run_order = (
    df.groupby("run")["bestT"].first().sort_values(ascending=False).index.tolist()
)
sns.boxplot(data=df, x="run", y="T", order=run_order, ax=ax, palette="Set2")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
ax.set_xlabel("Experimental Run")
ax.set_ylabel("Agent Survival Ticks (T)")
ax.set_title("Agent Survival Duration across 9 Evolutionary Runs")
ax.grid(alpha=0.3, axis="y")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/fig3_survival_comparison.png")
print(f"Saved {FIGDIR}/fig3_survival_comparison.png")

# ── Summary table ───────────────────────────────────────────────────
print("\n=== Key Metrics Summary ===")
print(f"Total agents: {len(df)}")
print(f"Total runs: {df['run'].nunique()}")
print(f"Overall mean skill%: {df['skill_pct'].mean():.4f}")
print(f"Overall mean collab%: {df['collab_pct'].mean():.4f}")
print(f"Overall mean residual%: {df['residual_pct'].mean():.4f}")
top_skill = df.loc[df["skill_pct"].idxmax()]
print(
    f"Top skill% agent: {top_skill['agent']} in {top_skill['run']} (T={top_skill['T']}, skill%={top_skill['skill_pct']:.4f})"
)
runs_w_dominant = df[df["n_dominant"] > 0]["run"].unique()
print(f"Runs with dominant skills: {list(runs_w_dominant)}")
print("\nDone.")
