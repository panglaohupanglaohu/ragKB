# -*- coding: utf-8 -*-
"""Generate Figure 6: Actual attention heatmap from epoch-5 checkpoint.

Shows 12-sample diagnostic dataset with:
1. LEFT: Pure trained attention (near-uniform — negative diagnostic, N < Nc)
2. RIGHT: Cold-start attention (keyword seeding — demonstrates potential)
3. Metrics: entropy, std, min-max per field
4. 6 decimal place values in cells
"""

import json, sys, os
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src" / "backend"
sys.path.insert(0, str(BACKEND))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.ticker as ticker

from agents.tse.config import TSEConfig, FIELD_NAMES, FIELD_KEYWORD_SEEDS
from agents.tse.pipeline import TSEPipeline, PlazaTranscript, parse_transcript
from agents.tse.checkpoint import load_checkpoint, latest_checkpoint
from agents.tse.heads import MultiTaskHeads
from agents.tse.encoder import hash_embed_text

# ── Load trained model ──
config = TSEConfig()
pipe = TSEPipeline(config)
heads = MultiTaskHeads(hidden_dim=config.tcn_hidden_dim, seed=config.hash_seed + 3)
ckpt_dir = Path("storage/tse/checkpoints")
ckpt = ckpt_dir / "dart_net_full_backprop_e30.npz"
load_checkpoint(ckpt, pipe, heads)

# ── Diagnostic samples: 12 diverse transcripts ──
sys.path.insert(0, str(ROOT / "scripts"))
from retrain_with_attention_backprop import SAMPLE_DEFS, _gen_transcript

samples = []
for i, (topic, skill_name, category, tools, key_utts) in enumerate(SAMPLE_DEFS[:12]):
    text = _gen_transcript(topic, skill_name, category, tools, key_utts)
    tr = parse_transcript(text, source_title=topic)
    stages = pipe.encode_stages(tr)
    attn = stages["attn_weights"]
    samples.append(
        {
            "idx": i,
            "skill": skill_name,
            "n_utt": attn.shape[1],
            "attn": attn,
            "transcript": tr,
        }
    )

# ── Build cold-start attention (no training, keyword-seeded queries) ──
from agents.tse.skill_attention import SkillQueryAttention, softmax
from agents.tse.encoder import UtteranceEncoder
from agents.tse.tcn import TCNTemporalModule

cold_encoder = UtteranceEncoder(config)
cold_tcn = TCNTemporalModule(config)
cold_att = SkillQueryAttention(config)  # uses FIELD_KEYWORD_SEEDS

cold_samples = []
for i, s in enumerate(samples[:12]):
    tr = s["transcript"]
    emb, mask = cold_encoder.encode_transcript(tr)
    temporal = cold_tcn.forward(emb, mask)
    _, attn = cold_att.forward(temporal, mask)
    cold_samples.append(
        {"idx": i, "skill": s["skill"], "n_utt": attn.shape[1], "attn": attn}
    )

# ── Aggregate: concat all 12 samples' attention into one grid ──
# Each sample has 4-5 utterances → total ~54 utterances
# Show as 12 horizontal blocks, each with its own utterances

# For the heatmap: 5 rows (fields) × total_utterances columns
trained_data = np.concatenate([s["attn"] for s in samples], axis=1)  # (5, total_N)
cold_data = np.concatenate([cs["attn"] for cs in cold_samples], axis=1)

total_N = trained_data.shape[1]
field_labels = ["name", "desc", "category", "tools", "instructions"]

# Build sample boundary markers
sample_boundaries = []
sample_names = []
offset = 0
for s in samples:
    sample_boundaries.append(offset + s["n_utt"] / 2 - 0.5)
    sample_names.append(s["skill"][:14])
    offset += s["n_utt"]


# ── Compute metrics ──
def compute_field_metrics(attn, fields):
    metrics = {}
    for i, f in enumerate(fields):
        w = attn[i]
        metrics[f"{f}_std"] = float(np.std(w))
        metrics[f"{f}_range"] = (float(np.min(w)), float(np.max(w)))
        w_norm = w / w.sum()
        ent = float(-np.sum(w_norm * np.log(w_norm + 1e-12)))
        max_ent = np.log(len(w))
        metrics[f"{f}_entropy"] = ent
        metrics[f"{f}_norm_ent"] = ent / max_ent
    return metrics


trained_metrics = compute_field_metrics(trained_data, field_labels)
cold_metrics = compute_field_metrics(cold_data, field_labels)

# ── Create the figure ──
fig, axes = plt.subplots(1, 2, figsize=(16, 4.5), gridspec_kw={"width_ratios": [1, 1]})
fig.patch.set_facecolor("white")

# Shared colorbar range
vmin = min(trained_data.min(), cold_data.min())
vmax = max(trained_data.max(), cold_data.max())

for ax_idx, (data, title_prefix, metrics) in enumerate(
    [
        (trained_data, "Trained (epoch 30)", trained_metrics),
        (cold_data, "Cold-start (keyword seeded)", cold_metrics),
    ]
):
    ax = axes[ax_idx]

    # Custom discrete colormap from white to deep red
    im = ax.imshow(data, cmap="YlOrRd", aspect="auto", vmin=vmin, vmax=vmax)

    N = data.shape[1]
    ax.set_xticks(np.arange(N))
    ax.set_xticklabels([""] * N)

    ax.set_yticks(range(5))
    ax.set_yticklabels(field_labels, fontsize=9)
    ax.set_ylabel("Skill field probe", fontsize=10, labelpad=4)

    # Add values in cells with 5 decimal places
    for i in range(5):
        for j in range(N):
            val = data[i, j]
            # Color threshold: white text on dark, dark text on light
            norm_val = (val - vmin) / (vmax - vmin + 1e-9)
            color = "white" if norm_val > 0.55 else "#222"
            ax.text(
                j,
                i,
                f"{val:.5f}",
                ha="center",
                va="center",
                fontsize=4.2,
                color=color,
                fontfamily="monospace",
            )

    # Sample boundary markers
    offset = 0
    for si, s in enumerate(samples):
        n = s["n_utt"]
        mid = offset + n / 2 - 0.5
        ax.axvline(x=offset - 0.5, color="#888", linewidth=0.5, linestyle=":")
        label = s["skill"][:12]
        ax.text(
            mid,
            -0.9,
            label,
            fontsize=5.5,
            ha="center",
            va="top",
            rotation=35,
            color="#555",
        )
        offset += n
    ax.axvline(x=offset - 0.5, color="#888", linewidth=0.5, linestyle=":")

    ax.set_xlabel("Utterances (12 samples, grouped)", fontsize=9, labelpad=18)

    # Add entropy stats text
    ent_text = ", ".join(f"{f}={metrics[f'{f}_norm_ent']:.4f}" for f in field_labels)
    std_text = ", ".join(f"{f}={metrics[f'{f}_std']:.6f}" for f in field_labels)
    ax.set_title(
        f"{title_prefix}\nNorm. entropy: {ent_text}\nStd: {std_text}",
        fontsize=8,
        weight="bold",
        pad=10,
        linespacing=1.2,
    )

    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Attention weight", fontsize=8)

# Global title
fig.suptitle(
    "Figure 6: Query attention heatmap — trained (near-uniform, N < Nc) vs cold-start (keyword-seeded, shows potential)",
    fontsize=11,
    weight="bold",
    y=1.02,
)

outdir = Path("paper/figures")
outdir.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(
    str(outdir / "fig6_attn_heatmap_real.png"),
    dpi=250,
    facecolor="white",
    edgecolor="none",
    bbox_inches="tight",
)
plt.close()
print(f"Saved: {outdir / 'fig6_attn_heatmap_real.png'}")

# ── Print detailed diagnostics ──
print("\n=== TRAINED ATTENTION METRICS (epoch 30) ===")
for f in field_labels:
    print(
        f"  {f:>12}: range=[{trained_metrics[f'{f}_range'][0]:.6f}, {trained_metrics[f'{f}_range'][1]:.6f}], "
        f"std={trained_metrics[f'{f}_std']:.6f}, norm_entropy={trained_metrics[f'{f}_norm_ent']:.6f}"
    )

print("\n=== COLD-START ATTENTION METRICS ===")
for f in field_labels:
    print(
        f"  {f:>12}: range=[{cold_metrics[f'{f}_range'][0]:.6f}, {cold_metrics[f'{f}_range'][1]:.6f}], "
        f"std={cold_metrics[f'{f}_std']:.6f}, norm_entropy={cold_metrics[f'{f}_norm_ent']:.6f}"
    )

# ── Save diagnostics JSON ──
diag = {
    "trained": {
        k: (list(v) if isinstance(v, tuple) else v) for k, v in trained_metrics.items()
    },
    "cold_start": {
        k: (list(v) if isinstance(v, tuple) else v) for k, v in cold_metrics.items()
    },
    "total_utterances": int(total_N),
    "num_samples": len(samples),
    "note": "Trained attention is near-uniform (norm_entropy ~ 1.0) — data below critical threshold Nc. "
    "Cold-start attention uses FIELD_KEYWORD_SEEDS to produce differentiated attention patterns.",
}
out_json = Path("storage/tse/runs/fig6_diagnostics.json")
out_json.parent.mkdir(parents=True, exist_ok=True)
with open(out_json, "w") as f:
    json.dump(diag, f, indent=2, ensure_ascii=False)
print(f"\nDiagnostics saved to: {out_json}")

# ── Simplified single-panel figure: PER-SAMPLE VIEW ──
# Show 12 sample blocks clearly with utterance labels
fig, ax = plt.subplots(figsize=(16, 3.8))
fig.patch.set_facecolor("white")

data_for_viz = np.concatenate([s["attn"] for s in samples], axis=1)
N = data_for_viz.shape[1]

im = ax.imshow(
    data_for_viz,
    cmap="RdYlBu_r",
    aspect="auto",
    vmin=data_for_viz.min(),
    vmax=data_for_viz.max(),
)

# Per-cell values
for i in range(5):
    for j in range(N):
        val = data_for_viz[i, j]
        nv = (val - data_for_viz.min()) / (
            data_for_viz.max() - data_for_viz.min() + 1e-9
        )
        color = "white" if nv > 0.6 else "#111"
        ax.text(
            j,
            i,
            f"{val:.5f}",
            ha="center",
            va="center",
            fontsize=4.0,
            color=color,
            fontfamily="monospace",
        )

ax.set_yticks(range(5))
ax.set_yticklabels(field_labels, fontsize=9)
ax.set_ylabel("Skill field probe", fontsize=10)
ax.set_xticks([])

# Sample separators and labels
offset = 0
for si, s in enumerate(samples):
    n = s["n_utt"]
    ax.axvline(x=offset - 0.5, color="#333", linewidth=0.8)
    mid = offset + n / 2 - 0.5
    ax.text(
        mid,
        -0.7,
        f"{s['skill'][:16]}",
        fontsize=5.5,
        ha="center",
        rotation=40,
        color="#333",
    )
    offset += n
ax.axvline(x=offset - 0.5, color="#333", linewidth=0.8)

ax.set_xlabel(
    "Utterances across 12 diagnostic samples (consecutive)", fontsize=9, labelpad=14
)
ax.set_title(
    "Attention heatmap — epoch 30 checkpoint (norm entropies ≈ 1.0, N < Nc)",
    fontsize=10,
    weight="bold",
)

cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Attention weight", fontsize=8)

plt.tight_layout()
plt.savefig(
    str(outdir / "fig6_attn_trained_only.png"),
    dpi=250,
    facecolor="white",
    edgecolor="none",
    bbox_inches="tight",
)
plt.close()
print(f"Saved: {outdir / 'fig6_attn_trained_only.png'}")

# ── Cold-start-only figure ──
fig, ax = plt.subplots(figsize=(16, 3.8))
fig.patch.set_facecolor("white")

data_cold = np.concatenate([cs["attn"] for cs in cold_samples], axis=1)
N_cold = data_cold.shape[1]

im = ax.imshow(
    data_cold, cmap="YlOrRd", aspect="auto", vmin=data_cold.min(), vmax=data_cold.max()
)

for i in range(5):
    for j in range(N_cold):
        val = data_cold[i, j]
        nv = (val - data_cold.min()) / (data_cold.max() - data_cold.min() + 1e-9)
        color = "white" if nv > 0.55 else "#111"
        ax.text(
            j,
            i,
            f"{val:.5f}",
            ha="center",
            va="center",
            fontsize=4.0,
            color=color,
            fontfamily="monospace",
        )

ax.set_yticks(range(5))
ax.set_yticklabels(field_labels, fontsize=9)
ax.set_ylabel("Skill field probe", fontsize=10)
ax.set_xticks([])

offset = 0
for si, cs in enumerate(cold_samples):
    n = cs["n_utt"]
    ax.axvline(x=offset - 0.5, color="#333", linewidth=0.8)
    mid = offset + n / 2 - 0.5
    ax.text(
        mid,
        -0.7,
        f"{cs['skill'][:16]}",
        fontsize=5.5,
        ha="center",
        rotation=40,
        color="#333",
    )
    offset += n
ax.axvline(x=offset - 0.5, color="#333", linewidth=0.8)

ax.set_xlabel("Utterances across 12 diagnostic samples", fontsize=9, labelpad=14)
ax.set_title(
    "Attention heatmap — cold-start (keyword-seeded, field-differentiated)",
    fontsize=10,
    weight="bold",
)

cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Attention weight", fontsize=8)

plt.tight_layout()
plt.savefig(
    str(outdir / "fig6_attn_coldstart_only.png"),
    dpi=250,
    facecolor="white",
    edgecolor="none",
    bbox_inches="tight",
)
plt.close()
print(f"Saved: {outdir / 'fig6_attn_coldstart_only.png'}")
