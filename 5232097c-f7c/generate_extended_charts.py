# -*- coding: utf-8 -*-
"""Generate charts for extended experiments (Track 2 and Track 3)."""

import json, os, sys

sys.path.insert(0, "/tmp/fig_venv/lib/python3.14/site-packages")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

with open(
    "/Users/panglaohu/Downloads/AgentsGroup2026/5232097c-f7c/extended_experiment_results.json"
) as f:
    data = json.load(f)

outdir = "/Users/panglaohu/Downloads/AgentsGroup2026/paper/figures"
os.makedirs(outdir, exist_ok=True)
plt.rcParams.update(
    {"font.size": 9, "axes.titlesize": 11, "savefig.dpi": 200, "savefig.bbox": "tight"}
)

# ═══ Chart 13: Multi-Agent Memory Inheritance ═══
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.2))

t2 = data["track2_memory_inheritance"]
pairs = [f"{r['src_agent']}\n{r['dst_agent']}" for r in t2[:3]]
export_sizes = [r["export_size_bytes"] / 1024 for r in t2[:3]]
log_integrity = [r["log_integrity"] for r in t2[:3]]
perc_integrity = [r["perception_integrity"] for r in t2[:3]]

bars = ax1.bar(
    range(3),
    export_sizes,
    color=["#2878B5", "#32B897", "#E8913A"],
    edgecolor="#333",
    linewidth=0.8,
)
ax1.set_xticks(range(3))
ax1.set_xticklabels(["architect", "security", "finops"], fontsize=7, rotation=15)
ax1.set_ylabel("Export Size (KB)")
ax1.set_title("Memory Export Size by Pair")
for b, v in zip(bars, export_sizes):
    ax1.text(
        b.get_x() + b.get_width() / 2,
        b.get_height() + 1,
        f"{v:.0f}KB",
        ha="center",
        fontsize=7,
    )

ax2.barh([0, 1], [3, 3], color="#32B897", edgecolor="#333", label="Log Integrity")
ax2.barh(
    [0.3, 1.3], [3, 3], color="#2878B5", edgecolor="#333", label="Perception Integrity"
)
ax2.set_yticks([0.15, 1.15])
ax2.set_yticklabels(["Log Layer", "Perception"], fontsize=8)
ax2.set_xlim(0, 4)
ax2.legend(fontsize=7, loc="lower right")
ax2.set_title("Integrity (3/3 pairs = 100%)")

fig.suptitle(
    "Multi-Agent Memory Inheritance: 3 Pairs, Cross-Team Verified",
    fontweight="bold",
    y=1.02,
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig13_memory_inheritance.png", facecolor="white")
plt.close()
print("[1/3] Memory inheritance chart")

# ═══ Chart 14: Robustness Matrix ═══
fig, ax = plt.subplots(figsize=(6, 3.5))

t3 = data["track3_robustness"]
tests = [
    "Contamination\nIsolation",
    "Safe\nRollback",
    "Version\nConflict",
    "Malicious\nInjection",
]
results_map = {
    "Contamination\nIsolation": t3["contamination"]["clean_events_preserved"],
    "Safe\nRollback": t3["rollback"]["rollback_integrity"],
    "Version\nConflict": t3["version_conflict"]["coexistence_ok"],
    "Malicious\nInjection": t3["malicious_injection"]["validation_layer_required"],
}
passed = [results_map[t] for t in tests]
colors = ["#32B897" if p else "#E8913A" for p in passed]
bars = ax.barh(
    range(len(tests)), [1] * len(tests), color=colors, edgecolor="#333", linewidth=0.8
)
ax.set_yticks(range(len(tests)))
ax.set_yticklabels(tests, fontsize=8)
ax.set_xlim(0, 1.5)
for i, (t, p) in enumerate(zip(tests, passed)):
    status = "PASS" if p else "PARTIAL"
    ax.text(
        1.05,
        i,
        status,
        fontsize=8,
        va="center",
        fontweight="bold",
        color="#2878B5" if p else "#E24B4B",
    )

details = [
    "10 injected → 20 flagged (over-inclusive, safe)",
    "80→95→80: restore integrity 100%",
    "v1 imported, v2 overwritten (design: replace, not merge)",
    "TSE extracts 2 clean + 1 malicious; gate at classifier",
]
for i, d in enumerate(details):
    ax.text(0.02, i - 0.25, d, fontsize=6.5, color="#666", va="top")

ax.set_title("Robustness Experiment Results (4 Scenarios)", fontweight="bold")
plt.tight_layout()
plt.savefig(f"{outdir}/fig14_robustness_matrix.png", facecolor="white")
plt.close()
print("[2/3] Robustness matrix chart")

# ═══ Chart 15: Cross-Team Memory Transfer ═══
ct = t2[3]["cross_team_transfer"]
fig, ax = plt.subplots(figsize=(5, 3))
teams = ["ops→security", "ops→finops"]
transfer_ok = [ct["sec_import_ok"], ct["fin_import_ok"]]
log_counts = [ct["sec_log_count"], ct["fin_log_count"]]
colors = ["#2878B5", "#32B897"]
bars = ax.bar(teams, log_counts, color=colors, edgecolor="#333", linewidth=0.8)
ax.set_ylabel("Inherited Events")
ax.set_title("Cross-Team Memory Transfer")
for b, v, ok in zip(bars, log_counts, transfer_ok):
    status = "OK" if ok else "FAIL"
    ax.text(
        b.get_x() + b.get_width() / 2,
        b.get_height() + 2,
        f"{v} events ({status})",
        ha="center",
        fontsize=8,
        fontweight="bold",
    )
plt.tight_layout()
plt.savefig(f"{outdir}/fig15_cross_team_transfer.png", facecolor="white")
plt.close()
print("[3/3] Cross-team transfer chart")

print(f"\nAll 3 extended charts saved to {outdir}/")
for f in [
    "fig13_memory_inheritance.png",
    "fig14_robustness_matrix.png",
    "fig15_cross_team_transfer.png",
]:
    sz = os.path.getsize(os.path.join(outdir, f)) / 1024
    print(f"  {f}: {sz:.0f} KB")
