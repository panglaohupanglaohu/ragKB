# -*- coding: utf-8 -*-
"""Generate charts from ablation decomposition results."""

import json, os, sys

sys.path.insert(0, "/tmp/fig_venv/lib/python3.14/site-packages")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

with open(
    "/Users/panglaohu/Downloads/AgentsGroup2026/5232097c-f7c/ablation_metrics_results.json"
) as f:
    data = json.load(f)

outdir = "/Users/panglaohu/Downloads/AgentsGroup2026/paper/figures"
os.makedirs(outdir, exist_ok=True)
plt.rcParams.update(
    {"font.size": 9, "axes.titlesize": 11, "savefig.dpi": 200, "savefig.bbox": "tight"}
)

metrics_data = data["metrics"]
disc_names = list(metrics_data.keys())
short_names = ["ES Scaling", "CentOS Mig", "RI Gov", "Monitor", "TF Gate"]

# ═══ Chart 16: Plaza Structural Metrics Radar ═══
metric_keys = [
    "role_coverage",
    "challenge_ratio",
    "risk_coverage",
    "source_entropy",
    "c_role",
]
metric_labels = [
    "Role\nCoverage",
    "Cross-Role\nCHALLENGE",
    "Risk\nCoverage",
    "Source\nEntropy",
    "C_role",
]
colors = ["#2878B5", "#32B897", "#E8913A", "#7B5EA7", "#E24B4B"]

fig, axes = plt.subplots(1, 3, figsize=(9, 4))

# Radar-style: bar chart of metrics per discussion
x = np.arange(len(metric_labels))
w = 0.15
for di, (disc_name, sn) in enumerate(zip(disc_names, short_names)):
    m = metrics_data[disc_name]
    values = [m[k] for k in metric_keys]
    ax = axes[min(di, 2)]
    bars = ax.bar(
        x + di * w - 2 * w,
        values,
        w,
        color=colors[di],
        edgecolor="#333",
        linewidth=0.8 if di < 3 else 0,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, fontsize=7, rotation=20)
    ax.set_ylim(0, 1.15)
    ax.set_title(sn, fontsize=9)

axes[0].set_ylabel("Score")
plt.suptitle("Plaza Structural Metrics by Discussion", fontweight="bold", y=1.03)
plt.tight_layout()
plt.savefig(f"{outdir}/fig16_plaza_metrics.png", facecolor="white")
plt.close()
print("[1/3] Plaza metrics chart")

# ═══ Chart 17: Risk Coverage & Tool Omission ═══
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.2))

risk_vals = [metrics_data[d]["risk_coverage"] for d in disc_names]
tool_vals = [1 - metrics_data[d]["tool_omission"] for d in disc_names]  # tool_coverage

ax1.bar(
    short_names,
    risk_vals,
    color=[
        "#E24B4B" if v < 0.3 else "#E8913A" if v < 0.5 else "#32B897" for v in risk_vals
    ],
    edgecolor="#333",
    linewidth=0.8,
)
ax1.set_ylabel("Risk Coverage")
ax1.set_title("Risk Boundary Coverage")
ax1.set_ylim(0, 1)
for i, v in enumerate(risk_vals):
    ax1.text(i, v + 0.03, f"{v:.0%}", ha="center", fontsize=7)
ax1.axhline(y=0.3, color="red", linestyle="--", alpha=0.5, label="Critical threshold")
ax1.legend(fontsize=7)

ax2.bar(
    short_names,
    tool_vals,
    color=[
        "#E24B4B" if v < 0.2 else "#E8913A" if v < 0.3 else "#32B897" for v in tool_vals
    ],
    edgecolor="#333",
    linewidth=0.8,
)
ax2.set_ylabel("Tool Coverage")
ax2.set_title("Tool/Pipeline Mention Rate")
ax2.set_ylim(0, 0.5)
for i, v in enumerate(tool_vals):
    ax2.text(i, v + 0.01, f"{v:.0%}", ha="center", fontsize=7)

fig.suptitle("Safety Coverage Metrics Across Discussions", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{outdir}/fig17_risk_tool_coverage.png", facecolor="white")
plt.close()
print("[2/3] Risk & tool coverage chart")

# ═══ Chart 18: Role Dominance & Entropy ═══
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.2))

dom_vals = [metrics_data[d]["dominance"] for d in disc_names]
ent_vals = [metrics_data[d]["source_entropy"] for d in disc_names]

colors_dom = ["#E24B4B" if v > 0.5 else "#32B897" for v in dom_vals]
ax1.bar(short_names, dom_vals, color=colors_dom, edgecolor="#333", linewidth=0.8)
ax1.set_ylabel("Dominance Score")
ax1.set_title("Single-Role Dominance")
ax1.set_ylim(0, 1)
ax1.axhline(y=0.4, color="blue", linestyle="--", alpha=0.5, label="Balanced")
ax1.legend(fontsize=7)
for i, v in enumerate(dom_vals):
    ax1.text(i, v + 0.02, f"{v:.1%}", ha="center", fontsize=7)

colors_ent = ["#32B897" if v > 0.9 else "#E8913A" for v in ent_vals]
ax2.bar(short_names, ent_vals, color=colors_ent, edgecolor="#333", linewidth=0.8)
ax2.set_ylabel("Normalized Entropy")
ax2.set_title("Source Role Entropy")
ax2.set_ylim(0, 1.2)
for i, v in enumerate(ent_vals):
    ax2.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=7)

fig.suptitle("Role Distribution Analysis", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{outdir}/fig18_role_distribution.png", facecolor="white")
plt.close()
print("[3/3] Role distribution chart")

# Summary statistics
print("\n=== Metric Summary (mean across 5 discussions) ===")
for mk in metric_keys:
    vals = [metrics_data[d][mk] for d in disc_names]
    print(f"  {mk}: mean={np.mean(vals):.3f}, std={np.std(vals):.3f}")

# Metric delta analysis
md = data.get("metric_deltas", {})
if md:
    print("\n=== Component Contribution Analysis ===")
    for cond_name, deltas in md.items():
        print(f"  {cond_name}:")
        for metric_name, delta in deltas.items():
            impact = (
                "critical"
                if abs(delta) > 0.5
                else "moderate"
                if abs(delta) > 0.2
                else "minor"
            )
            print(f"    {metric_name}: Δ{delta:+.3f} [{impact}]")
