# -*- coding: utf-8 -*-
"""Generate 6 publication-quality figures for Plaza/DART-Net/memory paper.
Style: clean, scientific, proper fonts, no unicode subscripts."""

import os, sys

sys.path.insert(0, "/tmp/fig_venv/lib/python3.14/site-packages")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.ticker as ticker
import numpy as np

outdir = "/Users/panglaohu/Downloads/AgentsGroup2026/paper/figures"
os.makedirs(outdir, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 9,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
    }
)

PALETTE = {
    "blue": "#2878B5",
    "blue_light": "#9ECAE1",
    "green": "#32B897",
    "green_light": "#A8E6CF",
    "orange": "#E8913A",
    "orange_light": "#FDD0A2",
    "red": "#E24B4B",
    "red_light": "#F9B5B5",
    "purple": "#7B5EA7",
    "purple_light": "#C5B4E3",
    "gray": "#888888",
    "gray_light": "#DDDDDD",
    "white": "#FFFFFF",
    "bg": "#FAFAFA",
}

# ═══════════════════════════════════════════════════════════
# Figure 1: Plaza 12-Niche ring layout
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(5, 5))
ax.set_xlim(-5.2, 5.2)
ax.set_ylim(-5.2, 5.2)
ax.set_aspect("equal")
ax.axis("off")

for r, lc, label, pos in [
    (1.6, PALETTE["green"], "Inner ring\n(core)", (2.0, -0.3)),
    (3.0, PALETTE["orange"], "Middle ring\n(extended)", (3.5, -0.3)),
    (4.2, PALETTE["gray"], "Outer ring\n(observer)", (4.7, -0.3)),
]:
    circ = plt.Circle(
        (0, 0), r, fill=False, color=lc, linewidth=1.5, linestyle="--", alpha=0.6
    )
    ax.add_patch(circ)
    ax.text(pos[0], pos[1], label, fontsize=6, color=lc, ha="center", va="top")

niches = [
    ("Architect", 0, 1.6, PALETTE["blue_light"], PALETTE["blue"]),
    ("DevOps", 90, 1.6, PALETTE["blue_light"], PALETTE["blue"]),
    ("Monitor", 180, 1.6, PALETTE["blue_light"], PALETTE["blue"]),
    ("Cost-Opt", 270, 1.6, PALETTE["blue_light"], PALETTE["blue"]),
    ("Security", 45, 3.0, PALETTE["orange_light"], PALETTE["orange"]),
    ("Container", 135, 3.0, PALETTE["orange_light"], PALETTE["orange"]),
    ("CI/CD", 225, 3.0, PALETTE["orange_light"], PALETTE["orange"]),
    ("Data-Eng", 315, 3.0, PALETTE["orange_light"], PALETTE["orange"]),
    ("Auditor", 0, 4.2, PALETTE["gray_light"], PALETTE["gray"]),
    ("Reviewer", 90, 4.2, PALETTE["gray_light"], PALETTE["gray"]),
    ("Scribe", 180, 4.2, PALETTE["gray_light"], PALETTE["gray"]),
    ("Observer", 270, 4.2, PALETTE["gray_light"], PALETTE["gray"]),
]
for name, angle, r, fc, ec in niches:
    x, y = r * np.cos(np.radians(angle)), r * np.sin(np.radians(angle))
    c = plt.Circle((x, y), 0.48, fc=fc, ec=ec, linewidth=1.2)
    ax.add_patch(c)
    ax.text(
        x, y, name, fontsize=5.5, ha="center", va="center", weight="bold", color="#222"
    )

fac = plt.Circle(
    (0, 0), 0.55, fc=PALETTE["red_light"], ec=PALETTE["red"], linewidth=1.8
)
ax.add_patch(fac)
ax.text(0, 0, "Facilitator", fontsize=7, ha="center", va="center", weight="bold")

ax.set_title("Plaza 12-Niche ring layout", fontsize=11, weight="bold", pad=8)
plt.tight_layout()
plt.savefig(f"{outdir}/fig1_plaza_niche.png", facecolor="white", edgecolor="none")
plt.close()
print("[1/6] Plaza ring")

# ═══════════════════════════════════════════════════════════
# Figure 2: DART-Net architecture pipeline
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 5))
ax.set_xlim(0, 12)
ax.set_ylim(0, 12)
ax.axis("off")

stages_data = [
    (
        6,
        10.2,
        5,
        1.0,
        "Plaza deliberation transcript\n(m1, m2, ..., mn)",
        PALETTE["blue_light"],
        PALETTE["blue"],
    ),
    (
        6,
        8.2,
        5,
        1.0,
        "Stage 1: Utterance hash encoder\nembed_dim = 256",
        PALETTE["green_light"],
        PALETTE["green"],
    ),
    (
        6,
        6.2,
        5,
        1.0,
        "Stage 2: TCN dilated conv\nk = 3, dilations = [1, 2, 4]",
        "#FFF5CC",
        PALETTE["orange"],
    ),
    (
        6,
        4.2,
        5,
        1.0,
        "Stage 3: Skill Query Cross-Attention\n5 learnable field probes",
        PALETTE["orange_light"],
        PALETTE["orange"],
    ),
    (
        6,
        2.2,
        5,
        1.0,
        "Stage 4: Constrained JSON decoder\nCodeLLaMA / local template",
        PALETTE["red_light"],
        PALETTE["red"],
    ),
]
for cx, cy, w, h, txt, fc, ec in stages_data:
    rect = FancyBboxPatch(
        (cx - w / 2, cy - h / 2),
        w,
        h,
        boxstyle="round,pad=0.12",
        fc=fc,
        ec=ec,
        linewidth=1.5,
    )
    ax.add_patch(rect)
    ax.text(cx, cy, txt, fontsize=6.5, ha="center", va="center", linespacing=1.3)

for i in range(len(stages_data) - 1):
    y1 = stages_data[i][1] - stages_data[i][3] / 2
    y2 = stages_data[i + 1][1] + stages_data[i + 1][3] / 2
    ax.annotate(
        "",
        xy=(6, y2),
        xytext=(6, y1),
        arrowprops=dict(arrowstyle="->", lw=1.8, color="#555"),
    )

# Multi-task heads
aux = FancyBboxPatch(
    (9.0, 3.5),
    2.6,
    1.4,
    boxstyle="round,pad=0.1",
    fc="#F8F8F8",
    ec=PALETTE["gray"],
    linewidth=1.2,
    linestyle=":",
)
ax.add_patch(aux)
ax.text(
    10.3,
    4.2,
    "Multi-task heads\ncategory (cls)\ntools (multi-label)",
    fontsize=6,
    ha="center",
    va="center",
)
ax.annotate(
    "",
    xy=(9.0, 4.2),
    xytext=(8.5, 4.2),
    arrowprops=dict(arrowstyle="->", lw=1, color=PALETTE["gray"], linestyle="dashed"),
)

ax.set_title(
    "DART-Net hierarchical encoding pipeline", fontsize=11, weight="bold", pad=8
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig2_dart_arch.png", facecolor="white", edgecolor="none")
plt.close()
print("[2/6] DART-Net arch")

# ═══════════════════════════════════════════════════════════
# Figure 3: Memory genetics flow
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4))
ax.set_xlim(0, 14)
ax.set_ylim(0, 7)
ax.axis("off")

nodes = [
    (
        1.5,
        5.0,
        "Agent Alpha\n(4-layer memory online)",
        PALETTE["green_light"],
        PALETTE["green"],
    ),
    (4.5, 5.8, "Seal\n(legacy snapshot)", PALETTE["orange_light"], PALETTE["orange"]),
    (4.5, 4.2, "Will\n(beneficiary intent)", "#EEEEEE", PALETTE["gray"]),
    (8.0, 5.8, "Export\n(JSON normalize)", PALETTE["blue_light"], PALETTE["blue"]),
    (
        11.5,
        5.0,
        "Agent Beta\n(inherits all memory)",
        PALETTE["green_light"],
        PALETTE["green"],
    ),
    (8.0, 3.0, "Import\n(overlay 4 layers)", PALETTE["red_light"], PALETTE["red"]),
]
for cx, cy, txt, fc, ec in nodes:
    rect = FancyBboxPatch(
        (cx - 1.3, cy - 0.6),
        2.6,
        1.2,
        boxstyle="round,pad=0.1",
        fc=fc,
        ec=ec,
        linewidth=1.5,
    )
    ax.add_patch(rect)
    ax.text(cx, cy, txt, fontsize=7, ha="center", va="center", linespacing=1.2)

arrows = [
    (2.8, 5.0, 3.2, 5.8),
    (2.8, 5.0, 3.2, 4.2),
    (5.8, 5.8, 6.7, 5.8),
    (5.8, 4.2, 6.7, 3.0),
    (9.3, 5.8, 10.2, 5.0),
    (9.3, 3.0, 10.2, 5.0),
]
for x1, y1, x2, y2 in arrows:
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", lw=1.3, color="#555"),
    )

ax.set_title(
    "Memory genetics: Seal -> Export -> Import -> Inheritance",
    fontsize=11,
    weight="bold",
    pad=8,
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig3_memory_genetics.png", facecolor="white", edgecolor="none")
plt.close()
print("[3/6] Memory genetics")

# ═══════════════════════════════════════════════════════════
# Figure 4: System closed-loop architecture
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
ax.set_xlim(0, 14)
ax.set_ylim(0, 12)
ax.axis("off")

loop_nodes = [
    (
        2.0,
        9.5,
        "1. Plaza deliberation\nORID + 12-niche\n+ RitualSignal",
        PALETTE["blue_light"],
        PALETTE["blue"],
    ),
    (
        7.0,
        9.5,
        "2. DART-Net extraction\nTCN + Cross-Attn\n+ JSON decoder",
        PALETTE["green_light"],
        PALETTE["green"],
    ),
    (
        12.0,
        9.5,
        "3. Skill indexing\nTF-IDF vector\n+ decay + boost",
        "#FFF5CC",
        PALETTE["orange"],
    ),
    (
        12.0,
        6.0,
        "4. Skill assignment\nSkillRouter\n3-pool classification",
        PALETTE["orange_light"],
        PALETTE["orange"],
    ),
    (
        12.0,
        3.0,
        "5. Task execution\nAgent + skill\n-> usage data",
        PALETTE["red_light"],
        PALETTE["red"],
    ),
    (
        7.0,
        3.0,
        "6. Skill evolution\nEffectiveness tracking\n+ LLM improvement",
        PALETTE["purple_light"],
        PALETTE["purple"],
    ),
]
for cx, cy, txt, fc, ec in loop_nodes:
    rect = FancyBboxPatch(
        (cx - 1.7, cy - 0.9),
        3.4,
        1.8,
        boxstyle="round,pad=0.12",
        fc=fc,
        ec=ec,
        linewidth=1.5,
    )
    ax.add_patch(rect)
    ax.text(cx, cy, txt, fontsize=6.5, ha="center", va="center", linespacing=1.3)

# Main loop
loop_arrows = [
    (3.7, 9.5, 5.3, 9.5),
    (10.4, 9.5, 10.3, 9.5),
    (12, 8.6, 12, 6.9),
    (12, 5.1, 12, 3.9),
    (10.3, 3, 5.3, 3),
]
for x1, y1, x2, y2 in loop_arrows:
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", lw=2, color="#444"),
    )

# Return arrow
ax.annotate(
    "",
    xy=(3.7, 9.5),
    xytext=(5.3, 3.0),
    arrowprops=dict(
        arrowstyle="->",
        lw=1.5,
        color=PALETTE["red"],
        connectionstyle="arc3,rad=-0.35",
        linestyle="dashed",
    ),
)

# Memory bridge
mem = FancyBboxPatch(
    (1.5, 5.3),
    2.8,
    1.2,
    boxstyle="round,pad=0.08",
    fc="#FDFDFD",
    ec=PALETTE["gray"],
    linewidth=1.2,
    linestyle="--",
)
ax.add_patch(mem)
ax.text(
    2.9,
    5.9,
    "Memory genetics\n(Seal/Will/Import)",
    fontsize=6.5,
    ha="center",
    va="center",
    color=PALETTE["gray"],
)

ax.annotate(
    "",
    xy=(2.9, 6.5),
    xytext=(2.9, 7.0),
    arrowprops=dict(arrowstyle="->", lw=1, color=PALETTE["gray"], linestyle="dotted"),
)
ax.annotate(
    "",
    xy=(2.9, 4.1),
    xytext=(2.9, 5.3),
    arrowprops=dict(arrowstyle="->", lw=1, color=PALETTE["gray"], linestyle="dotted"),
)

# Feedback label
ax.text(
    4.5,
    6.3,
    "feedback",
    fontsize=7,
    color=PALETTE["red"],
    ha="center",
    style="italic",
    rotation=-15,
)

ax.set_title(
    "System closed-loop architecture (6-node cycle)", fontsize=11, weight="bold", pad=8
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig4_sys_arch.png", facecolor="white", edgecolor="none")
plt.close()
print("[4/6] System architecture")

# ═══════════════════════════════════════════════════════════
# Figure 5: Ablation experiment — dual bar chart
# ═══════════════════════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.8))
fig.patch.set_facecolor("white")

conds = ["A. ORID full", "B. No ORID", "C. Free chat"]
cat_colors = [PALETTE["blue"], PALETTE["orange"], PALETTE["red"]]
x = np.arange(len(conds))
w = 0.55

# Left: skill count
vals1 = [2.0, 0.75, 0.5]
bars1 = ax1.bar(x, vals1, w, color=cat_colors, edgecolor="#333", linewidth=0.8)
ax1.set_xticks(x)
ax1.set_xticklabels(conds, fontsize=7)
ax1.set_ylabel("Skills / discussion", fontsize=9)
ax1.set_title("Extraction count", fontsize=10, weight="bold")
ax1.set_ylim(0, 2.6)
ax1.axhline(y=2.0, color=PALETTE["blue"], linestyle="--", linewidth=1.2, alpha=0.6)
ax1.text(-0.3, 2.05, "ORID baseline = 2.0", fontsize=6.5, color=PALETTE["blue"])
for bar, v in zip(bars1, vals1):
    ax1.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.05,
        str(v),
        ha="center",
        fontsize=9,
        weight="bold",
    )
# Add delta annotation
ax1.annotate(
    "-62%",
    xy=(1, 0.75),
    xytext=(1, 1.5),
    arrowprops=dict(arrowstyle="->", color=PALETTE["red"], lw=1.5),
    fontsize=8,
    color=PALETTE["red"],
    weight="bold",
    ha="center",
)
ax1.annotate(
    "-75%",
    xy=(2, 0.5),
    xytext=(2, 1.3),
    arrowprops=dict(arrowstyle="->", color=PALETTE["red"], lw=1.5),
    fontsize=8,
    color=PALETTE["red"],
    weight="bold",
    ha="center",
)

# Right: field completeness
vals2 = [91, 54, 33]
bars2 = ax2.bar(x, vals2, w, color=cat_colors, edgecolor="#333", linewidth=0.8)
ax2.set_xticks(x)
ax2.set_xticklabels(conds, fontsize=7)
ax2.set_ylabel("Field completeness (%)", fontsize=9)
ax2.set_title("Output quality", fontsize=10, weight="bold")
ax2.set_ylim(0, 105)
for bar, v in zip(bars2, vals2):
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 2,
        f"{v}%",
        ha="center",
        fontsize=9,
        weight="bold",
    )
ax2.annotate(
    "-41%",
    xy=(1, 54),
    xytext=(1, 75),
    arrowprops=dict(arrowstyle="->", color=PALETTE["red"], lw=1.5),
    fontsize=8,
    color=PALETTE["red"],
    weight="bold",
    ha="center",
)

fig.suptitle(
    "Ablation study: Impact of deliberation structure on skill extraction quality",
    fontsize=11,
    weight="bold",
    y=1.02,
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig5_ablation.png", facecolor="white", edgecolor="none")
plt.close()
print("[5/6] Ablation")

# ═══════════════════════════════════════════════════════════
# Figure 6: Attention weight heatmap
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7.5, 3.0))
fig.patch.set_facecolor("white")

data = np.ones((5, 12)) * (1.0 / 12)
fields = ["name", "desc", "category", "tools", "instructions"]
utt_labels = [f"{i}" for i in range(12)]

im = ax.imshow(data, cmap="YlOrRd", aspect="auto", vmin=0.04, vmax=0.12)
ax.set_xticks(range(12))
ax.set_xticklabels(utt_labels, fontsize=7)
ax.set_yticks(range(5))
ax.set_yticklabels(fields, fontsize=8)
ax.set_xlabel("Utterance index", fontsize=9, labelpad=4)
ax.set_ylabel("Skill field probe", fontsize=9, labelpad=4)

for i in range(5):
    for j in range(12):
        c = "white" if data[i, j] > 0.10 else "#333"
        ax.text(
            j, i, f"{data[i, j]:.3f}", ha="center", va="center", fontsize=6, color=c
        )

# Highlight expected focus regions
ax.add_patch(
    plt.Rectangle(
        (-0.5, 3.5),
        2,
        2,
        fill=False,
        edgecolor=PALETTE["green"],
        linewidth=2,
        linestyle="--",
    )
)
ax.text(
    0.5,
    3.15,
    "name -> u0-1\n(expected)",
    fontsize=6,
    color=PALETTE["green"],
    ha="center",
)
ax.add_patch(
    plt.Rectangle(
        (5.5, 0.5),
        3,
        2,
        fill=False,
        edgecolor=PALETTE["green"],
        linewidth=2,
        linestyle="--",
    )
)
ax.text(
    7.0,
    0.15,
    "tools -> u6-8\n(expected)",
    fontsize=6,
    color=PALETTE["green"],
    ha="center",
)

cbar = plt.colorbar(im, ax=ax, shrink=0.82, pad=0.02)
cbar.set_label("Attention weight", fontsize=8)

ax.set_title(
    "Attention heatmap (epoch-5 checkpoint): uniform weight distribution",
    fontsize=10,
    weight="bold",
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig6_attn_heatmap.png", facecolor="white", edgecolor="none")
plt.close()
print("[6/6] Attention heatmap")
print("\nAll figures regenerated with improved quality.")
print(f"Output: {outdir}/")
for f in sorted(os.listdir(outdir)):
    sz = os.path.getsize(os.path.join(outdir, f)) / 1024
    print(f"  {f}: {sz:.0f} KB")
