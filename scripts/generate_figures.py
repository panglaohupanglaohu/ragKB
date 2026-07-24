# -*- coding: utf-8 -*-
"""Generate all 6 figures for v3 paper using matplotlib (pandoc-compatible)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Arc
import numpy as np
import os

outdir = "/Users/panglaohu/Downloads/AgentsGroup2026/paper/figures"
os.makedirs(outdir, exist_ok=True)

# Chinese font
plt.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "Heiti SC",
    "SimHei",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

# ── Figure 1: Plaza 12-niche ring ──
fig, ax = plt.subplots(1, 1, figsize=(5.5, 5.5))
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_aspect("equal")
ax.axis("off")

for r, color, label in [
    (1.5, "#4A90D9", "内环"),
    (2.8, "#50B86C", "中环"),
    (4.0, "#E8913A", "外环"),
]:
    circle = plt.Circle((0, 0), r, fill=False, color=color, linewidth=2, linestyle="--")
    ax.add_patch(circle)
    ax.text(r + 0.15, 0.15, label, fontsize=8, color=color, ha="left")

# Inner ring (4 niches)
inner = [("架构师", 0), ("运维员", 90), ("监控员", 180), ("成本员", 270)]
for name, angle in inner:
    x, y = 1.5 * np.cos(np.radians(angle)), 1.5 * np.sin(np.radians(angle))
    circle = plt.Circle(
        (x, y), 0.45, fill=True, color="#B3D4FC", ec="#4A90D9", linewidth=1
    )
    ax.add_patch(circle)
    ax.text(x, y, name, fontsize=6, ha="center", va="center")

# Middle ring (4 niches)
mid = [("安全审计", 45), ("容器编排", 135), ("CI/CD", 225), ("数据引擎", 315)]
for name, angle in mid:
    x, y = 2.8 * np.cos(np.radians(angle)), 2.8 * np.sin(np.radians(angle))
    circle = plt.Circle(
        (x, y), 0.45, fill=True, color="#C8E6C9", ec="#50B86C", linewidth=1
    )
    ax.add_patch(circle)
    ax.text(x, y, name, fontsize=6, ha="center", va="center")

# Outer ring (4 niches)
outer = [("版本审计", 0), ("技术审查", 90), ("记录归档", 180), ("驻场观察", 270)]
for name, angle in outer:
    x, y = 4.0 * np.cos(np.radians(angle)), 4.0 * np.sin(np.radians(angle))
    circle = plt.Circle(
        (x, y), 0.45, fill=True, color="#FDE0C2", ec="#E8913A", linewidth=1
    )
    ax.add_patch(circle)
    ax.text(x, y, name, fontsize=6, ha="center", va="center")

# Center facilitator
center = plt.Circle(
    (0, 0), 0.55, fill=True, color="#F5A0A0", ec="#CC4444", linewidth=1.5
)
ax.add_patch(center)
ax.text(0, 0, "议事长", fontsize=8, ha="center", va="center", fontweight="bold")

ax.set_title("Plaza环状12-Niche座位布局", fontsize=12, fontweight="bold", pad=10)
plt.tight_layout()
plt.savefig(f"{outdir}/fig1_plaza_niche.png", dpi=200, bbox_inches="tight")
plt.close()
print("fig1 done")

# ── Figure 2: DART-Net architecture ──
fig, ax = plt.subplots(1, 1, figsize=(6, 4.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")

stages = [
    (5, 8.5, 4, 0.8, "Plaza审议转录文本\n(m₁, m₂, ..., mₙ)", "#B3D4FC"),
    (5, 6.5, 4, 0.8, "Stage 1: 话语级哈希编码\nembed_dim=256", "#C8E6C9"),
    (5, 4.8, 4, 0.8, "Stage 2: TCN膨胀卷积\nk=3, d=[1,2,4]", "#FFF9C4"),
    (5, 3.1, 4, 0.8, "Stage 3: 技能查询Cross-Attn\n5个可学习探针 qₖ", "#FFE0B2"),
    (5, 1.4, 4, 0.8, "Stage 4: 约束JSON解码\nCodeLLaMA / 离线模板", "#F8BBD0"),
]
for cx, cy, w, h, text, color in stages:
    rect = FancyBboxPatch(
        (cx - w / 2, cy - h / 2),
        w,
        h,
        boxstyle="round,pad=0.1",
        facecolor=color,
        edgecolor="#333",
        linewidth=1.2,
    )
    ax.add_patch(rect)
    ax.text(cx, cy, text, fontsize=6.5, ha="center", va="center")

# Arrows between stages
for i in range(len(stages) - 1):
    y1 = stages[i][1] - stages[i][3] / 2
    y2 = stages[i + 1][1] + stages[i + 1][3] / 2
    ax.annotate(
        "",
        xy=(5, y2),
        xytext=(5, y1),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#555"),
    )

# Auxiliary heads
rect = FancyBboxPatch(
    (7.5 - 1.2, 2.8 - 0.35),
    2.4,
    0.7,
    boxstyle="round,pad=0.05",
    facecolor="#E8E8E8",
    edgecolor="#999",
    linewidth=1,
)
ax.add_patch(rect)
ax.text(7.5, 3.15, "辅助训练头\ncategory + tools", fontsize=6, ha="center", va="center")
ax.annotate(
    "",
    xy=(7.5, 3.0),
    xytext=(7, 3.1),
    arrowprops=dict(arrowstyle="->", lw=1, color="#999", linestyle="dashed"),
)

ax.set_title("DART-Net三级层次化编码架构", fontsize=12, fontweight="bold", pad=8)
plt.tight_layout()
plt.savefig(f"{outdir}/fig2_dart_arch.png", dpi=200, bbox_inches="tight")
plt.close()
print("fig2 done")

# ── Figure 3: Memory genetics flow ──
fig, ax = plt.subplots(1, 1, figsize=(6, 3.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis("off")

nodes = [
    (1.5, 4.5, "Agent Alpha\n四层记忆在线", "#C8E6C9"),
    (3.8, 5.2, "Seal 封存\nLegacy快照", "#FFE0B2"),
    (3.8, 3.8, "Will 遗嘱\n指定继承人", "#E8E8E8"),
    (6.5, 5.2, "Export 导出\nJSON规范化", "#B3D4FC"),
    (8.5, 4.5, "Agent Beta\n继承Alpha全脑", "#C8E6C9"),
    (6.5, 2.8, "Import 导入\n逐层覆盖四层", "#F8BBD0"),
]
for cx, cy, text, color in nodes:
    rect = FancyBboxPatch(
        (cx - 1.1, cy - 0.55),
        2.2,
        1.1,
        boxstyle="round,pad=0.1",
        facecolor=color,
        edgecolor="#333",
        linewidth=1.2,
    )
    ax.add_patch(rect)
    ax.text(cx, cy, text, fontsize=6.5, ha="center", va="center")

# Arrows
arrows = [
    (2.6, 4.5, 2.7, 5.2),
    (2.6, 4.5, 2.7, 3.8),
    (4.9, 5.2, 5.4, 5.2),
    (4.9, 3.8, 5.4, 2.8),
    (7.6, 5.2, 7.4, 4.5),
    (7.6, 2.8, 7.4, 4.5),
]
for x1, y1, x2, y2 in arrows:
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", lw=1.2, color="#555"),
    )

ax.set_title(
    "记忆遗传流程：Seal→Export→Import→继承", fontsize=12, fontweight="bold", pad=8
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig3_memory_genetics.png", dpi=200, bbox_inches="tight")
plt.close()
print("fig3 done")

# ── Figure 4: System architecture diagram ──
fig, ax = plt.subplots(1, 1, figsize=(6, 4.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")

places = [
    (1.5, 8, "1.Plaza审议\nORID+12-niche\n+仪式信号", "#B3D4FC"),
    (5, 8, "2.DART-Net萃取\nTCN+CrossAttn\n+JSON解码", "#C8E6C9"),
    (8.5, 8, "3.技能索引\nTF-IDF向量\n+衰减增强", "#FFF9C4"),
    (8.5, 5, "4.技能赋予\nSkillRouter\n三池分类", "#FFE0B2"),
    (8.5, 2.5, "5.任务执行\nAgent+技能\n→usage数据", "#FFCDD2"),
    (5, 2.5, "6.技能演化\n效果追踪\n+LLM改进", "#E1BEE7"),
]
for cx, cy, text, color in places:
    rect = FancyBboxPatch(
        (cx - 1.4, cy - 0.7),
        2.8,
        1.4,
        boxstyle="round,pad=0.1",
        facecolor=color,
        edgecolor="#333",
        linewidth=1.2,
    )
    ax.add_patch(rect)
    ax.text(cx, cy, text, fontsize=6.5, ha="center", va="center")

# Main loop arrows
main_arrows = [
    (2.9, 8, 3.6, 8),
    (7.8, 8, 7.1, 8),
    (8.5, 7.3, 8.5, 5.7),
    (8.5, 4.3, 8.5, 3.2),
    (7.1, 2.5, 3.6, 2.5),
]
for x1, y1, x2, y2 in main_arrows:
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", lw=1.8, color="#333"),
    )

# Return arrow from evolution to Plaza
ax.annotate(
    "",
    xy=(1.5, 7.3),
    xytext=(3.6, 2.5),
    arrowprops=dict(
        arrowstyle="->", lw=1.5, color="#CC4444", connectionstyle="arc3,rad=-0.4"
    ),
)

# Memory bridge
rect = FancyBboxPatch(
    (1.5 - 1.2, 4.5 - 0.5),
    2.4,
    1.0,
    boxstyle="round,pad=0.05",
    facecolor="#F5F5F5",
    edgecolor="#999",
    linewidth=1,
    linestyle="--",
)
ax.add_patch(rect)
ax.text(1.5, 5, "记忆遗传\n(Seal/Will/Import)", fontsize=6, ha="center", va="center")
ax.annotate(
    "",
    xy=(1.5, 5.5),
    xytext=(1.5, 5.5),
    arrowprops=dict(arrowstyle="->", lw=1, color="#999", linestyle="dashed"),
)

ax.set_title("系统六环闭环架构", fontsize=12, fontweight="bold", pad=8)
plt.tight_layout()
plt.savefig(f"{outdir}/fig4_sys_arch.png", dpi=200, bbox_inches="tight")
plt.close()
print("fig4 done")

# ── Figure 5: Ablation bar chart ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.5))

# Subplot 1: skills extracted
conditions = ["A.ORID完整", "B.无ORID议程", "C.自由聊天"]
skills = [2.0, 0.75, 0.5]
colors = ["#4A90D9", "#E8913A", "#CC4444"]
bars = ax1.bar(conditions, skills, color=colors, edgecolor="#333", linewidth=0.8)
ax1.set_ylabel("萃取技能数 / 讨论", fontsize=9)
ax1.set_title("萃取数量对比", fontsize=10, fontweight="bold")
ax1.set_ylim(0, 2.5)
ax1.axhline(y=2.0, color="#4A90D9", linestyle="--", linewidth=1, alpha=0.7)
ax1.text(0, 2.05, "ORID基线=2.0", fontsize=7, color="#4A90D9")
for bar, val in zip(bars, skills):
    ax1.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.05,
        f"{val}",
        ha="center",
        fontsize=9,
        fontweight="bold",
    )

# Subplot 2: field completeness
completeness = [91, 54, 33]
bars2 = ax2.bar(conditions, completeness, color=colors, edgecolor="#333", linewidth=0.8)
ax2.set_ylabel("字段完整性 (%)", fontsize=9)
ax2.set_title("字段完整性对比", fontsize=10, fontweight="bold")
ax2.set_ylim(0, 105)
for bar, val in zip(bars2, completeness):
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 2,
        f"{val}%",
        ha="center",
        fontsize=9,
        fontweight="bold",
    )

fig.suptitle("消融实验：审议结构对技能萃取质量的影响", fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{outdir}/fig5_ablation.png", dpi=200, bbox_inches="tight")
plt.close()
print("fig5 done")

# ── Figure 6: Attention heatmap ──
fig, ax = plt.subplots(1, 1, figsize=(7, 3.2))

data = np.ones((5, 12)) * 0.083  # uniform
fields = ["name", "desc", "category", "tools", "instructions"]
utts = [f"u{i}" for i in range(12)]

im = ax.imshow(data, cmap="YlOrRd", aspect="auto", vmin=0, vmax=0.15)
ax.set_xticks(range(12))
ax.set_xticklabels(utts, fontsize=7)
ax.set_yticks(range(5))
ax.set_yticklabels(fields, fontsize=8)
ax.set_xlabel("utterance →", fontsize=9)
ax.set_ylabel("field →", fontsize=9)

# Add text annotations
for i in range(5):
    for j in range(12):
        ax.text(j, i, ".083", ha="center", va="center", fontsize=6, color="#333")

# Highlight expected focus regions
ax.add_patch(
    plt.Rectangle(
        (-0.5, 3.5),
        1.5,
        1.5,
        fill=False,
        edgecolor="green",
        linewidth=1.5,
        linestyle="--",
    )
)
ax.add_patch(
    plt.Rectangle(
        (5.5, 0.5),
        2.5,
        1.5,
        fill=False,
        edgecolor="green",
        linewidth=1.5,
        linestyle="--",
    )
)
ax.text(0.25, 3.2, "name→u0\n(expected)", fontsize=6, color="green", ha="center")
ax.text(6.75, 0.2, "tools→u6\n(expected)", fontsize=6, color="green", ha="center")

plt.colorbar(im, ax=ax, label="attention weight", shrink=0.8)
ax.set_title(
    "注意力权重热图（epoch-5: 均匀分布, 0.083/utterance）",
    fontsize=11,
    fontweight="bold",
)
plt.tight_layout()
plt.savefig(f"{outdir}/fig6_attn_heatmap.png", dpi=200, bbox_inches="tight")
plt.close()
print("fig6 done")

print(f"\nAll 6 figures saved to {outdir}/")
