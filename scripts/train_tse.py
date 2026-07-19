#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI: TSE silver bootstrap → multi-task train → checkpoint.

Examples:
  # Offline demo (heuristic silver + train)
  PYTHONPATH=src/backend python3 scripts/train_tse.py --demo --epochs 5

  # From existing JSONL
  PYTHONPATH=src/backend python3 scripts/train_tse.py --data storage/tse/silver/train.jsonl --epochs 10

  # Generate silver with system LLM (requires configured ChatHarness)
  PYTHONPATH=src/backend python3 scripts/train_tse.py --demo --use-llm --epochs 3

  # Active learning selection only
  PYTHONPATH=src/backend python3 scripts/train_tse.py --active-only --demo
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agents.tse.active import active_learning_step  # noqa: E402
from agents.tse.checkpoint import DEFAULT_CKPT_DIR, load_checkpoint  # noqa: E402
from agents.tse.config import TSEConfig  # noqa: E402
from agents.tse.dataset import PlazaExtractionDataset  # noqa: E402
from agents.tse.evaluate import evaluate_heads_on_dataset  # noqa: E402
from agents.tse.heads import MultiTaskHeads  # noqa: E402
from agents.tse.pipeline import TSEPipeline, get_tse_pipeline  # noqa: E402
from agents.tse.silver import generate_silver_dataset, seed_demo_transcripts  # noqa: E402
from agents.tse.trainer import TrainConfig, train_tse  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("train_tse")


def _default_paths() -> dict:
    base = ROOT / "storage" / "tse"
    return {
        "silver": base / "silver" / "train.jsonl",
        "ckpt": base / "checkpoints",
        "active": base / "active" / "review_queue.json",
        "history": base / "runs" / "last_history.json",
    }


async def _maybe_silver(args, paths) -> PlazaExtractionDataset:
    if args.data:
        ds = PlazaExtractionDataset.load_jsonl(args.data)
        logger.info("loaded dataset %s n=%d", args.data, len(ds))
        return ds

    if not args.demo and not args.seed_only:
        p = paths["silver"]
        if p.exists():
            ds = PlazaExtractionDataset.load_jsonl(p)
            logger.info("loaded existing silver %s n=%d", p, len(ds))
            return ds

    transcripts = seed_demo_transcripts()
    harness = None
    chat_fn = None
    if args.use_llm:
        try:
            from agents.chat_harness import get_chat_harness
            harness = get_chat_harness()
            logger.info("using ChatHarness for silver labels")
        except Exception as e:
            logger.warning("ChatHarness unavailable (%s); heuristic silver", e)

    out = paths["silver"]
    ds = await generate_silver_dataset(
        transcripts,
        harness=harness,
        chat_fn=chat_fn,
        out_path=out,
    )
    logger.info("silver dataset n=%d → %s", len(ds), out)
    return ds


async def main_async(args) -> int:
    paths = _default_paths()
    for k in ("silver", "ckpt", "active", "history"):
        paths[k].parent.mkdir(parents=True, exist_ok=True)

    ds = await _maybe_silver(args, paths)
    if len(ds) == 0:
        logger.error("no training examples")
        return 2

    train_ds, val_ds = ds.split(val_ratio=args.val_ratio, seed=args.seed)
    if len(train_ds) == 0:
        train_ds = ds
        val_ds = PlazaExtractionDataset([])

    pipe = TSEPipeline(TSEConfig())
    heads = MultiTaskHeads(hidden_dim=pipe.config.tcn_hidden_dim, seed=args.seed)

    # resume
    if args.resume:
        ckpt = Path(args.resume)
        if ckpt.exists():
            load_checkpoint(ckpt, pipe, heads)
            logger.info("resumed from %s", ckpt)

    if args.active_only:
        items = active_learning_step(
            pipe, heads, [ex.transcript for ex in ds],
            queue_path=paths["active"],
            top_k=args.active_k,
        )
        print(json.dumps({"active_queue": len(items), "path": str(paths["active"])}, indent=2))
        return 0

    tc = TrainConfig(
        epochs=args.epochs,
        learning_rate=args.lr,
        lr_heads=args.lr,
        lr_queries=args.lr * 0.5,
        lr_tcn_out=args.lr * 0.2,
        weight_ae=args.w_ae,
        weight_category=args.w_cat,
        weight_tools=args.w_tools,
        seed=args.seed,
        ckpt_dir=str(paths["ckpt"] if not args.ckpt_dir else args.ckpt_dir),
        run_name=args.run_name,
        val_every=max(1, args.val_every),
    )

    pipe, heads, hist = train_tse(train_ds, val_ds, pipeline=pipe, train_config=tc)

    metrics = evaluate_heads_on_dataset(pipe, val_ds if len(val_ds) else train_ds, heads)
    paths["history"].write_text(
        json.dumps({"history": hist.to_dict(), "metrics": metrics}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # refresh singleton so live server can pick up if same process
    try:
        live = get_tse_pipeline()
        from agents.tse.checkpoint import apply_state, collect_state
        apply_state(live, collect_state(pipe, heads))
        if hasattr(live, "heads"):
            live.heads = heads  # type: ignore
        else:
            setattr(live, "heads", heads)
    except Exception:
        pass

    if args.active_after:
        active_learning_step(
            pipe, heads, [ex.transcript for ex in ds],
            queue_path=paths["active"],
            top_k=args.active_k,
        )

    summary = {
        "train_n": len(train_ds),
        "val_n": len(val_ds),
        "epochs": args.epochs,
        "ckpt": hist.ckpt_path,
        "best_epoch": hist.best_epoch,
        "best_val_score": hist.best_val_score,
        "metrics": metrics,
        "history_path": str(paths["history"]),
        "last_loss": hist.epochs[-1]["loss"] if hist.epochs else None,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train TSE multi-task encoder (pure numpy)")
    p.add_argument("--data", type=str, default="", help="JSONL path of (transcript, skills)")
    p.add_argument("--demo", action="store_true", help="Use built-in seed transcripts + silver")
    p.add_argument("--seed-only", action="store_true", help="Alias of demo for silver bootstrap")
    p.add_argument("--use-llm", action="store_true", help="Silver labels via ChatHarness")
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-2)
    p.add_argument("--w-ae", type=float, default=1.0)
    p.add_argument("--w-cat", type=float, default=0.1)
    p.add_argument("--w-tools", type=float, default=0.1)
    p.add_argument("--val-ratio", type=float, default=0.25)
    p.add_argument("--val-every", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ckpt-dir", type=str, default="")
    p.add_argument("--resume", type=str, default="", help="Checkpoint npz to resume")
    p.add_argument("--run-name", type=str, default="tse_run")
    p.add_argument("--active-only", action="store_true", help="Only write active-learning queue")
    p.add_argument("--active-after", action="store_true", help="After train, write active queue")
    p.add_argument("--active-k", type=int, default=5)
    return p


def main() -> int:
    args = build_parser().parse_args()
    if not args.data and not args.demo and not args.seed_only:
        # default to demo for empty invocation
        args.demo = True
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
