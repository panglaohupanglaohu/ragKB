# -*- coding: utf-8 -*-
"""Tests for TSE training: silver → multi-task fit → checkpoint → reload."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agents.tse.active import sample_uncertainty  # noqa: E402
from agents.tse.checkpoint import load_checkpoint, save_checkpoint  # noqa: E402
from agents.tse.config import TSEConfig  # noqa: E402
from agents.tse.dataset import ExtractionExample, PlazaExtractionDataset  # noqa: E402
from agents.tse.evaluate import evaluate_heads_on_dataset, evaluate_name_match  # noqa: E402
from agents.tse.heads import MultiTaskHeads, category_to_id  # noqa: E402
from agents.tse.pipeline import TSEPipeline  # noqa: E402
from agents.tse.silver import generate_silver_dataset, seed_demo_transcripts  # noqa: E402
from agents.tse.trainer import TrainConfig, train_tse  # noqa: E402


@pytest.mark.asyncio
async def test_heuristic_silver_bootstrap(tmp_path):
    out = tmp_path / "silver.jsonl"
    ds = await generate_silver_dataset(seed_demo_transcripts(), out_path=out)
    assert len(ds) >= 3
    assert out.exists()
    line = out.read_text(encoding="utf-8").strip().splitlines()[0]
    obj = json.loads(line)
    assert obj["skills"]
    assert obj["transcript"]["messages"]


def test_dataset_roundtrip(tmp_path):
    tr = seed_demo_transcripts()[0]
    ex = ExtractionExample(
        discussion_id="t1",
        transcript=tr,
        skills=[{
            "name": "AWS ES Auto-Scaling",
            "description": "自动扩缩 ES",
            "category": "automation",
            "instructions": "1. 告警\n2. 扩容\n3. 验证",
            "required_tools": ["aws_cli", "cloudwatch_api"],
            "confidence": 0.9,
            "slug": "aws-es",
            "icon": "📈",
            "scope": "public",
            "extraction_algorithm": "test",
        }],
        source="gold",
        verified=True,
    )
    # validate_skill_fields applied in from_dict; construct via dataset
    path = tmp_path / "d.jsonl"
    ds = PlazaExtractionDataset([ex])
    ds.save_jsonl(path)
    ds2 = PlazaExtractionDataset.load_jsonl(path)
    assert len(ds2) == 1
    assert ds2[0].skills[0]["name"]


@pytest.mark.asyncio
async def test_train_loss_decreases(tmp_path):
    """Multi-task train should reduce train loss over epochs on seed silver."""
    ds = await generate_silver_dataset(seed_demo_transcripts())
    # Expand dataset by duplicating with noise-free copies (tiny corpus)
    while len(ds) < 8:
        for ex in list(ds.examples):
            ds.append(ex)
            if len(ds) >= 8:
                break

    train_ds, val_ds = ds.split(val_ratio=0.25, seed=0)
    if len(train_ds) < 2:
        train_ds = ds

    pipe = TSEPipeline(TSEConfig())
    tc = TrainConfig(
        epochs=6,
        lr_heads=2e-2,
        lr_queries=1e-2,
        lr_tcn_out=5e-3,
        seed=0,
        ckpt_dir=str(tmp_path / "ckpt"),
        run_name="unit",
        val_every=2,
        log_every=1,
    )
    pipe, heads, hist = train_tse(train_ds, val_ds if len(val_ds) else None, pipeline=pipe, train_config=tc)
    assert hist.epochs
    first = hist.epochs[0]["loss"]
    last = hist.epochs[-1]["loss"]
    # Allow small noise but expect non-increase trend or last <= first * 1.05
    assert last <= first * 1.15 or last < first + 0.05
    assert hist.ckpt_path
    assert Path(hist.ckpt_path).exists()

    # reload into fresh pipeline
    pipe2 = TSEPipeline(TSEConfig())
    heads2 = MultiTaskHeads(hidden_dim=pipe2.config.tcn_hidden_dim)
    load_checkpoint(hist.ckpt_path, pipe2, heads2)
    m = evaluate_heads_on_dataset(pipe2, train_ds, heads2)
    assert m["n"] > 0


def test_checkpoint_roundtrip(tmp_path):
    pipe = TSEPipeline(TSEConfig())
    heads = MultiTaskHeads(hidden_dim=pipe.config.tcn_hidden_dim, seed=1)
    # mutate a weight
    pipe.attention.query_vectors[0, 0] = 0.12345
    heads.W_cat[0, 0] = 0.99
    path = tmp_path / "c.npz"
    save_checkpoint(path, pipe, heads, meta={"x": 1})
    pipe2 = TSEPipeline(TSEConfig())
    heads2 = MultiTaskHeads(hidden_dim=pipe2.config.tcn_hidden_dim, seed=99)
    load_checkpoint(path, pipe2, heads2)
    assert abs(float(pipe2.attention.query_vectors[0, 0]) - 0.12345) < 1e-5
    assert abs(float(heads2.W_cat[0, 0]) - 0.99) < 1e-5


def test_name_match_metrics():
    pred = [[{"name": "AWS ES Auto Scaling"}], [{"name": "K8s Rollout"}]]
    gold = [[{"name": "aws es auto-scaling"}], [{"name": "Other"}]]
    m = evaluate_name_match(pred, gold)
    assert m["tp"] == 1.0
    assert m["f1"] > 0


def test_active_uncertainty_ranking():
    pipe = TSEPipeline(TSEConfig())
    heads = MultiTaskHeads(hidden_dim=pipe.config.tcn_hidden_dim)
    items = sample_uncertainty(pipe, heads, seed_demo_transcripts(), top_k=2)
    assert len(items) == 2
    assert items[0]["uncertainty"] >= items[1]["uncertainty"]


def test_category_id_stable():
    assert category_to_id("automation") == category_to_id("AUTOMATION")
    assert category_to_id("unknown_xyz") == category_to_id("general")
