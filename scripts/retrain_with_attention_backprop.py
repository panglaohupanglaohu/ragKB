#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thin CLI for full-attention TSE training.

Training logic lives in ``agents.tse.full_attention_trainer``.
Legacy SAMPLE_DEFS generation is replaced by versioned synthetic corpora
from ``agents.tse.synthetic_corpus``.

Recommended paper-section reproduction still goes through:
  scripts/run_tse_paper_experiments.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agents.tse.config import TSEConfig  # noqa: E402
from agents.tse.full_attention_trainer import (  # noqa: E402
    FullAttentionTrainConfig,
    train_full_attention,
)
from agents.tse.heads import MultiTaskHeads  # noqa: E402
from agents.tse.pipeline import TSEPipeline  # noqa: E402
from agents.tse.synthetic_corpus import build_synthetic_dataset  # noqa: E402

logger = logging.getLogger("retrain_attn")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n-samples", type=int, default=20, help="synthetic corpus size")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ckpt-dir", type=Path, default=ROOT / "storage" / "tse" / "checkpoints")
    p.add_argument("--run-name", type=str, default="dart_net_full_backprop")
    p.add_argument("--history-out", type=Path, default=ROOT / "storage" / "tse" / "runs" / "retrain_history.json")
    p.add_argument("--val-ratio", type=float, default=0.15)
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = TSEConfig()
    pipeline = TSEPipeline(config)
    heads = MultiTaskHeads(hidden_dim=config.tcn_hidden_dim, seed=config.hash_seed + 3)
    full = build_synthetic_dataset(args.n_samples, config=config, seed=args.seed)
    train_ds, val_ds = full.split(val_ratio=args.val_ratio, seed=args.seed)
    if len(val_ds) == 0:
        val_ds = train_ds

    tc = FullAttentionTrainConfig(
        epochs=args.epochs,
        seed=args.seed,
        ckpt_dir=str(args.ckpt_dir),
        run_name=args.run_name,
        save_every_epoch=True,
    )
    pipe, heads, hist = train_full_attention(
        train_ds,
        val_ds,
        pipeline=pipeline,
        heads=heads,
        train_config=tc,
        tse_config=config,
    )
    args.history_out.parent.mkdir(parents=True, exist_ok=True)
    args.history_out.write_text(
        json.dumps(hist.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"trained n={args.n_samples} epochs={args.epochs} seed={args.seed}")
    print(f"checkpoint: {hist.ckpt_path}")
    print(f"history: {args.history_out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
