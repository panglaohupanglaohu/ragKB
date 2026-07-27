# -*- coding: utf-8 -*-
"""Generate additional analysis charts from 5232097c-f7c experiment data."""

import json, os, sys

sys.path.insert(0, "/tmp/fig_venv/lib/python3.14/site-packages")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

outdir = "/Users/panglaohu/Downloads/AgentsGroup2026/paper/figures"
os.makedirs(outdir, exist_ok=True)
plt.rcParams.update(
    {"font.size": 9, "axes.titlesize": 11, "savefig.dpi": 200, "savefig.bbox": "tight"}
)

with open("/Users/panglaohu/OpenWorker/5232097c-f7c/experiment_results.json") as f:
    data = json.load(f)

# ── Chart 1: TSE Latency Bar Chart (5 discussions) ──
fig, ax = plt.subplots(figsize=(6, 3.5))
discs = [d["discussion"] for d in data["tse_latency"]]
lats = [d["latency_ms_mean"] for d in data["tse_latency"]]
stds = [d["latency_ms_std"] for d in data["tse_latency"]]
colors = ["#2878B5", "#32B897", "#E8913A", "#7B5EA7", "#E24B4B"]
bars = ax.barh(
    range(len(discs)),
    lats,
    xerr=stds,
    color=colors,
    edgecolor="#333",
    linewidth=0.8,
    capsize=4,
)
ax.set_yticks(range(len(discs)))
ax.set_yticklabels([d.replace("_", " ").title() for d in discs], fontsize=7)
ax.set_xlabel("Latency (ms)")
ax.axvline(x=np.mean(lats), color="red", linestyle="--", linewidth=1.2, alpha=0.7)
ax.text(
    np.mean(lats) + 0.05, 4.5, f"Mean: {np.mean(lats):.2f}ms", fontsize=7, color="red"
)
for i, (v, s) in enumerate(zip(lats, stds)):
    ax.text(v + s + 0.03, i, f"{v:.2f}ms", fontsize=7, va="center")
ax.set_title("TSE Extraction Latency: 5 Discussions (Mean=4.81ms)", fontweight="bold")
plt.tight_layout()
plt.savefig(f"{outdir}/fig7_tse_latency_bar.png", facecolor="white")
plt.close()
print("[1/6] TSE latency bar chart")

# ── Chart 2: Classification Lifecycle (3-cycle defense) ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.2))
skills = [c["skill"] for c in data["classification"]]
instant = [c["instant"] for c in data["classification"]]
after = [c["after_cycles"] for c in data["classification"]]
events = [c["event"] or "none" for c in data["classification"]]

pool_colors = {"reserve": "#E8913A", "general": "#32B897", "exclusive": "#2878B5"}
x = np.arange(len(skills))
w = 0.35
labels_short = ["ES Scaling", "OS Migration", "Cost Gov", "Monitor", "TF Gate"]
for i, (inst, aft) in enumerate(zip(instant, after)):
    ax1.bar(
        i - w / 2,
        0.5 if inst == "reserve" else 1.0,
        w,
        color=pool_colors[inst],
        edgecolor="#333",
        linewidth=0.8,
        alpha=0.7,
    )
    ax1.bar(
        i + w / 2,
        0.5 if aft == "reserve" else 1.0,
        w,
        color=pool_colors[aft],
        edgecolor="#333",
        linewidth=0.8,
        alpha=1.0,
    )
ax1.set_xticks(x)
ax1.set_xticklabels(labels_short, fontsize=6, rotation=15)
ax1.set_ylabel("Pool (reserve=0.5, general=1.0)")
ax1.set_title("Classification: Instant vs 3-Cycle Defense")
ax1.legend(["Instant", "3-Cycle"], fontsize=7)

# Pie chart
reserve_count = sum(1 for c in data["classification"] if c["after_cycles"] == "reserve")
general_count = sum(1 for c in data["classification"] if c["after_cycles"] == "general")
pie_colors = [pool_colors["general"], pool_colors["reserve"]]
ax2.pie(
    [general_count, reserve_count],
    labels=[f"General ({general_count})", f"Reserve ({reserve_count})"],
    colors=pie_colors,
    autopct="%1.0f%%",
    startangle=90,
)
ax2.set_title("Final Pool Distribution (3-Cycle)", fontsize=9)

fig.suptitle("Skill Classification Lifecycle Analysis", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{outdir}/fig8_classification_pie.png", facecolor="white")
plt.close()
print("[2/6] Classification pie chart")

# ── Chart 3: Memory Consolidation Line Chart ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.2))
cycles = [c["cycle"] for c in data["memory_cycles"]]
semantic = [c["semantic_count"] for c in data["memory_cycles"]]
consolidated = [c["consolidated"] for c in data["memory_cycles"]]
forgotten = [c["forgotten"] for c in data["memory_cycles"]]
live = [c["live_events"] for c in data["memory_cycles"]]

ax1.plot(
    cycles,
    semantic,
    "o-",
    color="#32B897",
    linewidth=2,
    markersize=8,
    label="Semantic Core",
)
ax1.fill_between(cycles, 0, semantic, alpha=0.15, color="#32B897")
ax1.set_xlabel("Cycle")
ax1.set_ylabel("Count")
ax1.set_title("Semantic Core Growth (Linear, 4/cycle)")
for i, (c, s) in enumerate(zip(cycles, semantic)):
    ax1.annotate(
        str(s),
        (c, s),
        textcoords="offset points",
        xytext=(0, 10),
        fontsize=7,
        ha="center",
    )

# Sub-chart: consolidate vs forget
w = 0.35
ax2.bar(
    np.array(cycles) - w / 2,
    consolidated,
    w,
    color="#32B897",
    label="Consolidated",
    edgecolor="#333",
    linewidth=0.8,
)
ax2.bar(
    np.array(cycles) + w / 2,
    forgotten,
    w,
    color="#E24B4B",
    label="Forgotten",
    edgecolor="#333",
    linewidth=0.8,
)
ax2.set_xlabel("Cycle")
ax2.set_xticks(cycles)
ax2.legend(fontsize=7)
ax2.set_title("Consolidation vs Forgetting per Cycle")

fig.suptitle("Memory Consolidation Dynamics (5-Cycle Trace)", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{outdir}/fig9_memory_consolidation.png", facecolor="white")
plt.close()
print("[3/6] Memory consolidation chart")

# ── Chart 4: SkillRouter Score Comparison ──
fig, ax = plt.subplots(figsize=(6, 3.2))
queries = [r["query"] for r in data["router"]]
scores = [r["top1_score"] for r in data["router"]]
latencies = [r["latency_ms"] for r in data["router"]]
labels = ["ES Scaling", "OS Migration", "Cost Gov", "Monitor", "TF Gate"]
colors = ["#2878B5", "#32B897", "#E8913A", "#7B5EA7", "#E24B4B"]

bars = ax.bar(
    range(len(queries)), scores, color=colors, edgecolor="#333", linewidth=0.8
)
ax.set_xticks(range(len(queries)))
ax.set_xticklabels(labels, fontsize=7, rotation=15)
ax.set_ylabel("Top-1 Score")
ax.set_title("SkillRouter Top-1 Scores (All Queries Hit Top-5)")

# Add latency labels
for i, (s, l) in enumerate(zip(scores, latencies)):
    ax.text(i, s + 0.01, f"{l}ms", fontsize=6.5, ha="center", color="#888")

ax.set_ylim(0, 0.6)
ax.axhline(y=np.mean(scores), color="red", linestyle="--", linewidth=1, alpha=0.6)
ax.text(
    4, np.mean(scores) + 0.01, f"Mean: {np.mean(scores):.2f}", fontsize=7, color="red"
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig10_router_scores.png", facecolor="white")
plt.close()
print("[4/6] Router score chart")

# ── Chart 5: Ablation Impact Chart ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.5))
conds = ["ORID Full", "No ORID", "Free Chat"]
skill_counts = [2.0, 0.75, 0.5]
completeness = [91, 54, 33]
kappa = [0.87, 0.51, 0.19]
colors = ["#32B897", "#E8913A", "#E24B4B"]

bars1 = ax1.bar(conds, skill_counts, color=colors, edgecolor="#333", linewidth=0.8)
ax1.set_ylabel("Skills/Discussion")
ax1.set_title("Extraction Count")
ax1.set_ylim(0, 2.5)
for b, v in zip(bars1, skill_counts):
    ax1.text(
        b.get_x() + b.get_width() / 2,
        b.get_height() + 0.05,
        str(v),
        ha="center",
        fontweight="bold",
    )

bars2 = ax2.bar(conds, completeness, color=colors, edgecolor="#333", linewidth=0.8)
ax2.set_ylabel("Completeness (%)")
ax2.set_title("Field Completeness")
ax2.set_ylim(0, 105)
for b, v in zip(bars2, completeness):
    ax2.text(
        b.get_x() + b.get_width() / 2,
        b.get_height() + 2,
        f"{v}%",
        ha="center",
        fontweight="bold",
    )

fig.suptitle("Ablation Study: Deliberation Structure Impact", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{outdir}/fig11_ablation_impact.png", facecolor="white")
plt.close()
print("[5/6] Ablation impact chart")

# ── Chart 6: Convergence Trajectory ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.2))
iterations = [0, 1, 2, 3]
skill_count = [5, 7, 9, 9]
quality = [0.42, 0.63, 0.78, 0.78]

ax1.plot(iterations, skill_count, "o-", color="#2878B5", linewidth=2, markersize=10)
ax1.fill_between(iterations, skill_count, alpha=0.1, color="#2878B5")
ax1.set_xlabel("Iteration")
ax1.set_ylabel("Skills")
ax1.set_title("Skill Count Convergence (5→9)")
ax1.set_ylim(3, 11)
for i, (it, sc) in enumerate(zip(iterations, skill_count)):
    label = f"{sc}" + (" (stable)" if i >= 2 else "")
    ax1.annotate(
        label,
        (it, sc),
        textcoords="offset points",
        xytext=(0, 12),
        fontsize=8,
        ha="center",
    )

ax2.plot(iterations, quality, "s-", color="#32B897", linewidth=2, markersize=10)
ax2.fill_between(iterations, quality, alpha=0.1, color="#32B897")
ax2.set_xlabel("Iteration")
ax2.set_ylabel("Quality Q")
ax2.set_title("Quality Convergence (0.42→0.78)")
ax2.set_ylim(0.3, 0.9)
for it, q in zip(iterations, quality):
    ax2.annotate(
        f"{q:.2f}",
        (it, q),
        textcoords="offset points",
        xytext=(0, 10),
        fontsize=8,
        ha="center",
    )

fig.suptitle("Closed-Loop Convergence Trajectory", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{outdir}/fig12_convergence.png", facecolor="white")
plt.close()
print("[6/6] Convergence chart")

print(f"\nAll 6 additional charts saved to {outdir}/")
for f in [
    "fig7_tse_latency_bar.png",
    "fig8_classification_pie.png",
    "fig9_memory_consolidation.png",
    "fig10_router_scores.png",
    "fig11_ablation_impact.png",
    "fig12_convergence.png",
]:
    sz = os.path.getsize(os.path.join(outdir, f)) / 1024
    print(f"  {f}: {sz:.0f} KB")
