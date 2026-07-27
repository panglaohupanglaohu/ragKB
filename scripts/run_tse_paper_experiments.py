#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducible CLI for the paper's TSE experiments 9.3 and 9.4.

Recommended entrypoint for reproducing section 9.3 (local extraction latency)
and 9.4 (trained vs keyword attention diagnostic). Prefer this over legacy
one-off scripts under scripts/experiment_tse_full.py and
scripts/generate_fig6_keyword_attn.py.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agents.tse.config import FIELD_NAMES, TSEConfig  # noqa: E402
from agents.tse.experiments import (  # noqa: E402
    ATTENTION_DIAGNOSTIC_BOUNDARY,
    LOCAL_BENCHMARK_BOUNDARY,
    attention_distribution_metrics,
    benchmark_local_extraction,
    build_keyword_attention,
    compare_attention_baseline,
    evidence_localization_metrics,
    load_experiment_samples,
    sha256_file,
)
from agents.tse.full_attention_trainer import (  # noqa: E402
    FullAttentionTrainConfig,
    train_full_attention,
)
from agents.tse.heads import MultiTaskHeads  # noqa: E402
from agents.tse.pipeline import TSEPipeline  # noqa: E402
from agents.tse.synthetic_corpus import build_synthetic_dataset  # noqa: E402


FIXTURE_DIR = BACKEND / "agents" / "tse" / "fixtures"
DEFAULT_LATENCY_INPUT = FIXTURE_DIR / "latency_9_3.jsonl"
DEFAULT_ATTENTION_INPUT = FIXTURE_DIR / "attention_9_4.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "storage" / "tse" / "runs"
DEFAULT_CHECKPOINT = ROOT / "storage" / "tse" / "checkpoints" / "dart_net_full_backprop_e30.npz"
SCHEMA_VERSION = "tse-paper-experiments/v2"
TREND_BOUNDARY = (
    "Sweep summaries describe empirical trends only; they do not name a critical "
    "sample size or claim an attention phase transition."
)
TRAINING_CORPUS_SEED = 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _environment(
    config: TSEConfig,
    *,
    runs: int | None = None,
    warmups: int | None = None,
    temperature: float | None = None,
) -> dict[str, Any]:
    """Report metadata: Python / NumPy / platform / processor / TSE / run params."""
    env: dict[str, Any] = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "machine": platform.machine(),
        "tse_config": asdict(config),
    }
    if runs is not None:
        env["runs"] = int(runs)
    if warmups is not None:
        env["warmups"] = int(warmups)
    if temperature is not None:
        env["temperature"] = float(temperature)
    return env


def _input_metadata(path: Path, samples: Sequence[Any]) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "sample_count": len(samples),
        "utterance_count": sum(len(sample.messages) for sample in samples),
    }


def _require_shape(
    samples: Sequence[Any], *, sample_count: int, utterance_count: int, label: str
) -> None:
    actual_samples = len(samples)
    actual_utterances = sum(len(sample.messages) for sample in samples)
    if (actual_samples, actual_utterances) != (sample_count, utterance_count):
        raise ValueError(
            f"{label} input must contain {sample_count} samples/{utterance_count} utterances; "
            f"got {actual_samples}/{actual_utterances}"
        )


def _base_report(
    command: str,
    config: TSEConfig,
    *,
    runs: int | None = None,
    warmups: int | None = None,
    temperature: float | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "generated_at": _utc_now(),
        "environment": _environment(
            config, runs=runs, warmups=warmups, temperature=temperature
        ),
    }


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON atomically (temp file + os.replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _run_latency(args: argparse.Namespace, config: TSEConfig) -> dict[str, Any]:
    samples = load_experiment_samples(args.input)
    _require_shape(samples, sample_count=5, utterance_count=25, label="9.3")
    input_metadata = _input_metadata(args.input, samples)
    report = _base_report(
        "latency", config, runs=args.runs, warmups=args.warmups
    )
    report["input"] = input_metadata
    report["scope_boundary"] = LOCAL_BENCHMARK_BOUNDARY
    report["result"] = benchmark_local_extraction(
        samples,
        runs=args.runs,
        warmups=args.warmups,
        config=config,
        input_sha256=input_metadata["sha256"],
    )
    return report


def _run_attention(args: argparse.Namespace, config: TSEConfig) -> dict[str, Any]:
    samples = load_experiment_samples(args.input)
    _require_shape(samples, sample_count=12, utterance_count=53, label="9.4")
    input_metadata = _input_metadata(args.input, samples)
    report = _base_report("attention", config, temperature=args.temperature)
    report["input"] = input_metadata
    report["interpretation_boundary"] = ATTENTION_DIAGNOSTIC_BOUNDARY
    report["result"] = compare_attention_baseline(
        samples,
        checkpoint=args.checkpoint,
        temperature=args.temperature,
        config=config,
        expected_epoch=30,
        input_sha256=input_metadata["sha256"],
    )
    return report


def _run_all(args: argparse.Namespace, config: TSEConfig) -> dict[str, Any]:
    latency_samples = load_experiment_samples(args.latency_input)
    attention_samples = load_experiment_samples(args.attention_input)
    _require_shape(latency_samples, sample_count=5, utterance_count=25, label="9.3")
    _require_shape(attention_samples, sample_count=12, utterance_count=53, label="9.4")
    latency_input = _input_metadata(args.latency_input, latency_samples)
    attention_input = _input_metadata(args.attention_input, attention_samples)

    report = _base_report(
        "all",
        config,
        runs=args.runs,
        warmups=args.warmups,
        temperature=args.temperature,
    )
    report["inputs"] = {
        "latency": latency_input,
        "attention": attention_input,
    }
    report["scope_boundary"] = LOCAL_BENCHMARK_BOUNDARY
    report["interpretation_boundary"] = ATTENTION_DIAGNOSTIC_BOUNDARY
    report["experiments"] = {
        "latency": benchmark_local_extraction(
            latency_samples,
            runs=args.runs,
            warmups=args.warmups,
            config=config,
            input_sha256=latency_input["sha256"],
        ),
        "attention": compare_attention_baseline(
            attention_samples,
            checkpoint=args.checkpoint,
            temperature=args.temperature,
            config=config,
            expected_epoch=30,
            input_sha256=attention_input["sha256"],
        ),
    }
    return report


def _parse_int_list(raw: str, name: str) -> list[int]:
    parts = [p.strip() for p in str(raw).split(",") if p.strip()]
    if not parts:
        raise ValueError(f"{name} must contain at least one integer")
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError as exc:
            raise ValueError(f"invalid integer in {name}: {p!r}") from exc
    return out


def _mean_std(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {"mean": 0.0, "std": 0.0}
    return {"mean": float(np.mean(arr)), "std": float(np.std(arr))}


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 1.0
    u = a | b
    return float(len(a & b) / len(u)) if u else 0.0


def _evaluate_trained_on_gold(
    pipeline: TSEPipeline,
    gold_samples: Sequence[Any],
    *,
    temperature: float,
    config: TSEConfig,
) -> dict[str, Any]:
    trained = []
    keyword = []
    topk_by_field: dict[str, list[set[int]]] = {f: [] for f in FIELD_NAMES}
    for sample in gold_samples:
        stages = pipeline.encode_stages(sample)
        attn = stages["attn_weights"]
        trained.append(attn)
        keyword.append(build_keyword_attention(sample, temperature=temperature, config=config))
        for fi, field in enumerate(FIELD_NAMES):
            order = list(np.argsort(-attn[fi]))[:3]
            topk_by_field[field].append(set(int(i) for i in order))

    trained_all = np.concatenate(trained, axis=1)
    dist = attention_distribution_metrics(trained_all)
    # average concentration / entropy across fields
    ent = float(np.mean([dist[f]["normalized_entropy"] for f in FIELD_NAMES]))
    conc = float(np.mean([dist[f]["concentration"] for f in FIELD_NAMES]))
    evid = evidence_localization_metrics(gold_samples, trained)
    kw_evid = evidence_localization_metrics(gold_samples, keyword)
    return {
        "normalized_entropy_mean": ent,
        "concentration_mean": conc,
        "evidence_f1": float(evid["micro"]["f1"]),
        "evidence_hit_at_1": float(evid["hit_at_1"]),
        "evidence_f1_by_field": {
            field: float(evid["fields"][field]["f1"]) for field in FIELD_NAMES
        },
        "keyword_evidence_f1": float(kw_evid["micro"]["f1"]),
        "topk_sets": {f: [sorted(s) for s in sets] for f, sets in topk_by_field.items()},
        "distribution_fields": dist,
    }


def _run_sweep(args: argparse.Namespace, config: TSEConfig) -> dict[str, Any]:
    sample_sizes = _parse_int_list(args.sample_sizes, "sample-sizes")
    seeds = _parse_int_list(args.seeds, "seeds")
    if any(n <= 0 for n in sample_sizes):
        raise ValueError("sample sizes must be positive")
    if any(s < 0 for s in seeds):
        raise ValueError("seeds must be non-negative")
    max_runs = int(args.max_runs) if args.max_runs is not None else 10**9
    planned = len(sample_sizes) * len(seeds)
    if planned > max_runs:
        raise ValueError(
            f"planned runs {planned} exceed --max-runs {max_runs}; "
            "raise budget or reduce sizes/seeds"
        )

    gold = load_experiment_samples(args.diagnostic_input)
    _require_shape(gold, sample_count=12, utterance_count=53, label="9.4 diagnostic")
    gold_meta = _input_metadata(args.diagnostic_input, gold)

    # tiny-dim override for fast tests via env-like CLI flag
    if getattr(args, "tiny", False):
        config = TSEConfig(embed_dim=16, tcn_hidden_dim=16, num_heads=4)

    raw_runs: list[dict[str, Any]] = []
    failures = 0
    for n in sample_sizes:
        for seed in seeds:
            run: dict[str, Any] = {"n": int(n), "seed": int(seed), "ok": False}
            try:
                # Keep each n dataset fixed across optimizer seeds so the sweep
                # measures training variability instead of corpus variation.
                train_ds = build_synthetic_dataset(
                    int(n), config=config, seed=TRAINING_CORPUS_SEED
                )
                # no held-out split for small n; evaluate heads on train for tools F1
                pipeline = TSEPipeline(config)
                heads = MultiTaskHeads(
                    hidden_dim=config.tcn_hidden_dim, seed=config.hash_seed + 3 + int(seed)
                )
                tc = FullAttentionTrainConfig(
                    epochs=int(args.epochs),
                    seed=int(seed),
                    save_every_epoch=False,
                    log_every=max(1, int(args.epochs)),
                    run_name=f"sweep_n{n}_s{seed}",
                    ckpt_dir=str(Path(args.ckpt_dir) / f"n{n}_s{seed}"),
                )
                pipe, heads, hist = train_full_attention(
                    train_ds,
                    train_ds,
                    pipeline=pipeline,
                    heads=heads,
                    train_config=tc,
                    tse_config=config,
                )
                last = hist.epochs[-1] if hist.epochs else {}
                eval_out = _evaluate_trained_on_gold(
                    pipe, gold, temperature=float(args.temperature), config=config
                )
                run.update(
                    {
                        "ok": True,
                        "train_loss": float(last.get("loss") or 0.0),
                        "tools_f1": float(last.get("val_tools_f1", 0.0)),
                        "normalized_entropy": eval_out["normalized_entropy_mean"],
                        "concentration": eval_out["concentration_mean"],
                        "evidence_f1": eval_out["evidence_f1"],
                        "evidence_hit_at_1": eval_out["evidence_hit_at_1"],
                        "evidence_f1_by_field": eval_out["evidence_f1_by_field"],
                        "keyword_evidence_f1": eval_out["keyword_evidence_f1"],
                        "topk_sets": eval_out["topk_sets"],
                        "train_input_sha256": hist.train_input_sha256,
                        "ckpt_path": hist.ckpt_path,
                    }
                )
            except Exception as exc:
                failures += 1
                run["ok"] = False
                run["error"] = str(exc)
            raw_runs.append(run)

    # Aggregate by n
    by_n: dict[str, Any] = {}
    for n in sample_sizes:
        subset = [r for r in raw_runs if r["n"] == n and r.get("ok")]
        failed_n = [r for r in raw_runs if r["n"] == n and not r.get("ok")]
        metrics = {}
        for key in (
            "train_loss",
            "tools_f1",
            "normalized_entropy",
            "concentration",
            "evidence_f1",
            "evidence_hit_at_1",
        ):
            metrics[key] = _mean_std([float(r[key]) for r in subset])

        # Seed stability: mean pairwise Jaccard of top-3 indices over every
        # field and every diagnostic sample.
        jaccards: list[float] = []
        if len(subset) >= 2:
            for field in FIELD_NAMES:
                sample_count = min(
                    len(run["topk_sets"][field]) for run in subset
                )
                for sample_idx in range(sample_count):
                    for i in range(len(subset)):
                        for j in range(i + 1, len(subset)):
                            a = set(subset[i]["topk_sets"][field][sample_idx])
                            b = set(subset[j]["topk_sets"][field][sample_idx])
                            jaccards.append(_jaccard(a, b))
        stability = {
            "topk_jaccard_mean": float(np.mean(jaccards)) if jaccards else 1.0,
            "topk_jaccard_std": float(np.std(jaccards)) if jaccards else 0.0,
            "failed_runs": len(failed_n),
            "successful_runs": len(subset),
        }
        # coefficient of variation on evidence F1
        f1s = [float(r["evidence_f1"]) for r in subset]
        if f1s and abs(np.mean(f1s)) > 1e-9:
            stability["evidence_f1_cv"] = float(np.std(f1s) / np.mean(f1s))
        else:
            stability["evidence_f1_cv"] = 0.0
        field_cv: dict[str, float] = {}
        for field in FIELD_NAMES:
            values = [float(r["evidence_f1_by_field"][field]) for r in subset]
            mean = float(np.mean(values)) if values else 0.0
            field_cv[field] = (
                float(np.std(values) / mean) if abs(mean) > 1e-9 else 0.0
            )
        stability["field_evidence_f1_cv"] = field_cv

        by_n[str(n)] = {
            "n": int(n),
            "metrics": metrics,
            "stability": stability,
            "raw_run_ids": [
                {"seed": r["seed"], "ok": r.get("ok")} for r in raw_runs if r["n"] == n
            ],
        }

    # Trend description only — no critical-point naming
    trend_lines = []
    ordered = sorted(sample_sizes)
    if len(ordered) >= 2:
        e0 = by_n[str(ordered[0])]["metrics"]["evidence_f1"]["mean"]
        e1 = by_n[str(ordered[-1])]["metrics"]["evidence_f1"]["mean"]
        if e1 > e0 + 0.02:
            trend_lines.append(
                f"Mean evidence F1 increased from n={ordered[0]} ({e0:.3f}) "
                f"to n={ordered[-1]} ({e1:.3f})."
            )
        elif e0 > e1 + 0.02:
            trend_lines.append(
                f"Mean evidence F1 decreased from n={ordered[0]} ({e0:.3f}) "
                f"to n={ordered[-1]} ({e1:.3f})."
            )
        else:
            trend_lines.append(
                f"Mean evidence F1 remained similar from n={ordered[0]} to n={ordered[-1]}."
            )
    trend_lines.append(TREND_BOUNDARY)

    report = _base_report("sweep", config, temperature=args.temperature)
    report["diagnostic_input"] = gold_meta
    report["sweep"] = {
        "sample_sizes": sample_sizes,
        "seeds": seeds,
        "epochs": int(args.epochs),
        "training_corpus_seed": TRAINING_CORPUS_SEED,
        "max_runs": max_runs,
        "planned_runs": planned,
        "failed_runs": failures,
        "by_sample_size": by_n,
        "raw_runs": [
            {k: v for k, v in r.items() if k != "topk_sets"} for r in raw_runs
        ],
        "trend_notes": trend_lines,
        "interpretation_boundary": TREND_BOUNDARY,
    }
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    latency = subparsers.add_parser("latency", help="run experiment 9.3")
    latency.add_argument("--input", type=Path, default=DEFAULT_LATENCY_INPUT)
    latency.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR / "tse_9_3.json")
    latency.add_argument("--runs", type=int, default=10)
    latency.add_argument("--warmups", type=int, default=1)

    attention = subparsers.add_parser("attention", help="run experiment 9.4")
    attention.add_argument("--input", type=Path, default=DEFAULT_ATTENTION_INPUT)
    attention.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR / "tse_9_4.json")
    attention.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to epoch-30 npz checkpoint (required; no silent random fallback)",
    )
    attention.add_argument("--temperature", type=float, default=0.15)

    all_parser = subparsers.add_parser("all", help="run experiments 9.3 and 9.4")
    all_parser.add_argument("--latency-input", type=Path, default=DEFAULT_LATENCY_INPUT)
    all_parser.add_argument("--attention-input", type=Path, default=DEFAULT_ATTENTION_INPUT)
    all_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR / "tse_9_3_9_4.json")
    all_parser.add_argument("--runs", type=int, default=10)
    all_parser.add_argument("--warmups", type=int, default=1)
    all_parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to epoch-30 npz checkpoint (required; no silent random fallback)",
    )
    all_parser.add_argument("--temperature", type=float, default=0.15)

    sweep = subparsers.add_parser("sweep", help="multi-size multi-seed stability sweep")
    sweep.add_argument("--sample-sizes", type=str, default="12,24,48,96")
    sweep.add_argument("--seeds", type=str, default="7,42,2026")
    sweep.add_argument("--epochs", type=int, default=30)
    sweep.add_argument("--temperature", type=float, default=0.15)
    sweep.add_argument("--diagnostic-input", type=Path, default=DEFAULT_ATTENTION_INPUT)
    sweep.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR / "tse_attention_sweep.json")
    sweep.add_argument("--ckpt-dir", type=Path, default=DEFAULT_OUTPUT_DIR / "sweep_ckpts")
    sweep.add_argument("--max-runs", type=int, default=None, help="hard budget on n×seed runs")
    sweep.add_argument(
        "--tiny",
        action="store_true",
        help="use tiny TSE dims for smoke sweeps (not paper-scale)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = TSEConfig()
    try:
        if args.command == "latency":
            report = _run_latency(args, config)
        elif args.command == "attention":
            report = _run_attention(args, config)
        elif args.command == "sweep":
            report = _run_sweep(args, config)
        else:
            report = _run_all(args, config)

        _atomic_write_json(args.output, report)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # stdout: summary + report path only (stable machine parsing)
    if args.command == "latency":
        result = report["result"]
        print(
            f"9.3 complete: {result['sample_count']} samples, "
            f"{result['runs_per_sample']} runs each, "
            f"{result['warmups_per_sample']} warmups"
        )
    elif args.command == "attention":
        result = report["result"]
        print(
            f"9.4 complete: {result['sample_count']} samples, "
            f"{result['utterance_count']} utterances"
        )
    elif args.command == "sweep":
        sw = report["sweep"]
        print(
            f"sweep complete: sizes={sw['sample_sizes']} seeds={sw['seeds']} "
            f"failed={sw['failed_runs']}"
        )
    else:
        lat = report["experiments"]["latency"]
        att = report["experiments"]["attention"]
        print(
            f"9.3+9.4 complete: latency samples={lat['sample_count']} "
            f"attention samples={att['sample_count']} utterances={att['utterance_count']}"
        )
    print(f"Report: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
