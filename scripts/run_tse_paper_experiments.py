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

from agents.tse.config import TSEConfig  # noqa: E402
from agents.tse.experiments import (  # noqa: E402
    ATTENTION_DIAGNOSTIC_BOUNDARY,
    LOCAL_BENCHMARK_BOUNDARY,
    benchmark_local_extraction,
    compare_attention_baseline,
    load_experiment_samples,
    sha256_file,
)


FIXTURE_DIR = BACKEND / "agents" / "tse" / "fixtures"
DEFAULT_LATENCY_INPUT = FIXTURE_DIR / "latency_9_3.jsonl"
DEFAULT_ATTENTION_INPUT = FIXTURE_DIR / "attention_9_4.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "storage" / "tse" / "runs"
DEFAULT_CHECKPOINT = ROOT / "storage" / "tse" / "checkpoints" / "dart_net_full_backprop_e30.npz"


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
        "schema_version": "tse-paper-experiments/v1",
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
