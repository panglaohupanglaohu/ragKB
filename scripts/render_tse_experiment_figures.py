#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render paper figures 5 (latency) and 6 (attention) from experiment JSON only.

Does not re-run models or recompute metrics. All plotted numbers come from the
input report. Outputs PNG and SVG.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Keep renderer free of trainer/pipeline imports.
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


FIELD_ORDER = ("name", "description", "category", "tools", "instructions")
SUPPORTED_SCHEMAS = {
    "tse-paper-experiments/v1",
    "tse-paper-experiments/v2",
}


def _load_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"report not found: {path}")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid JSON report {path}: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError("report root must be an object")
    schema = str(report.get("schema_version") or "")
    if schema not in SUPPORTED_SCHEMAS:
        raise ValueError(f"unsupported schema_version: {schema!r}")
    return report


def _extract_latency(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("command") == "latency" and "result" in report:
        return report["result"]
    if report.get("command") == "all" and "experiments" in report:
        return report["experiments"]["latency"]
    if "latency" in report and isinstance(report["latency"], dict):
        return report["latency"]
    raise ValueError("report does not contain a 9.3 latency result block")


def _extract_attention(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("command") == "attention" and "result" in report:
        return report["result"]
    if report.get("command") == "all" and "experiments" in report:
        return report["experiments"]["attention"]
    if "attention" in report and isinstance(report["attention"], dict):
        return report["attention"]
    raise ValueError("report does not contain a 9.4 attention result block")


def render_latency(result: dict[str, Any], env: dict[str, Any], out_base: Path) -> None:
    samples = result.get("samples") or []
    if not samples:
        raise ValueError("latency result has no samples")
    labels = []
    means = []
    stds = []
    for s in samples:
        labels.append(str(s.get("topic") or s.get("sample_id") or "?"))
        lat = s.get("latency_ms") or {}
        means.append(float(lat.get("mean_ms") or 0.0))
        stds.append(float(lat.get("std_ms") or 0.0))

    runs = result.get("runs_per_sample")
    warmups = result.get("warmups_per_sample")
    py = env.get("python", "?")
    plat = env.get("platform", env.get("machine", "?"))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(labels))
    ax.bar(x, means, yerr=stds, capsize=4, color="#3B6D11", ecolor="#222", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Figure 5 — Local TSE extraction latency by topic")
    note = (
        f"runs={runs}, warmups={warmups}; Python {py}; {plat}. "
        "Local stages only (no online LLM/network/human review)."
    )
    fig.text(0.01, 0.01, note, fontsize=8, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out_base.with_suffix(".png"), dpi=160)
    fig.savefig(out_base.with_suffix(".svg"))
    plt.close(fig)


def render_attention(result: dict[str, Any], out_base: Path) -> None:
    samples = result.get("samples") or []
    if not samples:
        raise ValueError("attention result has no samples")
    n_samples = int(result.get("sample_count") or len(samples))
    n_utt = int(result.get("utterance_count") or 0)
    if n_utt <= 0:
        n_utt = sum(int(s.get("utterance_count") or 0) for s in samples)

    trained_blocks = []
    keyword_blocks = []
    boundaries = [0]
    for s in samples:
        t = np.asarray(s.get("trained_attention"), dtype=np.float64)
        k = np.asarray(s.get("keyword_attention"), dtype=np.float64)
        if t.ndim != 2 or k.ndim != 2:
            raise ValueError(f"bad attention matrix rank for {s.get('sample_id')}")
        if t.shape != k.shape:
            raise ValueError(f"trained/keyword shape mismatch for {s.get('sample_id')}")
        trained_blocks.append(t)
        keyword_blocks.append(k)
        boundaries.append(boundaries[-1] + t.shape[1])

    trained = np.concatenate(trained_blocks, axis=1)
    keyword = np.concatenate(keyword_blocks, axis=1)
    if trained.shape[0] != len(FIELD_ORDER):
        raise ValueError(
            f"attention field dimension must be {len(FIELD_ORDER)}; "
            f"got {trained.shape[0]}"
        )
    if trained.shape[1] != n_utt:
        raise ValueError(
            f"attention utterance count must be {n_utt}; got {trained.shape[1]}"
        )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, mat, title in (
        (axes[0], trained, "Trained query attention"),
        (axes[1], keyword, "Keyword baseline attention"),
    ):
        im = ax.imshow(mat, aspect="auto", cmap="viridis", interpolation="nearest")
        ax.set_yticks(range(len(FIELD_ORDER)))
        ax.set_yticklabels(list(FIELD_ORDER))
        ax.set_xlabel("Utterance index (concatenated samples)")
        ax.set_title(title)
        for b in boundaries[1:-1]:
            ax.axvline(b - 0.5, color="white", linewidth=0.6, alpha=0.7)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle(
        f"Figure 6 — Attention diagnostic ({n_samples} samples / {n_utt} utterances)"
    )
    algo = result.get("algorithm_version") or ""
    note = (
        f"algorithm={algo}; keyword baseline is diagnostic, not ground truth. "
        "Sample boundaries shown as white lines."
    )
    fig.text(0.01, 0.01, note, fontsize=8, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.savefig(out_base.with_suffix(".png"), dpi=160)
    fig.savefig(out_base.with_suffix(".svg"))
    plt.close(fig)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True, help="experiment JSON report")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--latency-input", type=Path, default=None, help="optional separate 9.3 JSON")
    p.add_argument("--attention-input", type=Path, default=None, help="optional separate 9.4 JSON")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        primary = _load_report(args.input)
        latency_report = primary
        attention_report = primary
        if args.latency_input:
            latency_report = _load_report(args.latency_input)
        if args.attention_input:
            attention_report = _load_report(args.attention_input)

        args.output_dir.mkdir(parents=True, exist_ok=True)
        lat = _extract_latency(latency_report)
        att = _extract_attention(attention_report)
        env = latency_report.get("environment") or primary.get("environment") or {}

        fig5 = args.output_dir / "fig5_latency"
        fig6 = args.output_dir / "fig6_attention"
        render_latency(lat, env, fig5)
        render_attention(att, fig6)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Figure 5: {fig5.with_suffix('.png')} / {fig5.with_suffix('.svg')}")
    print(f"Figure 6: {fig6.with_suffix('.png')} / {fig6.with_suffix('.svg')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
