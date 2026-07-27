# -*- coding: utf-8 -*-
"""Lightweight unit tests for FullAttentionTrainer (tiny dims / few epochs)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from agents.tse.config import FIELD_NAMES, TSEConfig
from agents.tse.full_attention_trainer import (
    TRAINER_ID,
    FullAttentionTrainConfig,
    FullAttentionTrainer,
    attention_backward,
    dataset_content_sha256,
    train_full_attention,
)
from agents.tse.pipeline import TSEPipeline
from agents.tse.skill_attention import SkillQueryAttention
from agents.tse.synthetic_corpus import build_synthetic_dataset


def _tiny() -> TSEConfig:
    return TSEConfig(embed_dim=16, tcn_hidden_dim=16, num_heads=4)


def test_attention_backward_shapes_and_finite() -> None:
    cfg = _tiny()
    pipe = TSEPipeline(cfg)
    ds = build_synthetic_dataset(2, config=cfg, seed=1)
    stages = pipe.encode_stages(ds[0].transcript)
    nq = len(FIELD_NAMES)
    h = cfg.tcn_hidden_dim
    d_repr = np.random.RandomState(0).randn(nq, h).astype(np.float32) * 0.01
    grads = attention_backward(
        stages["temporal"], stages["mask"], d_repr, pipe.attention
    )
    assert grads["d_query"].shape == pipe.attention.query_vectors.shape
    assert grads["d_Wq"].shape == pipe.attention.W_q.shape
    assert grads["d_Wk"].shape == pipe.attention.W_k.shape
    assert grads["d_Wv"].shape == pipe.attention.W_v.shape
    assert grads["d_Wo"].shape == pipe.attention.W_o.shape
    for v in grads.values():
        assert np.all(np.isfinite(v))


def test_attention_backward_matches_finite_differences() -> None:
    cfg = TSEConfig(embed_dim=4, tcn_hidden_dim=4, num_heads=2)
    att = SkillQueryAttention(cfg)
    rng = np.random.RandomState(11)
    temporal = rng.randn(3, 4).astype(np.float32) * 0.2
    mask = np.ones(3, dtype=np.float32)
    d_repr = rng.randn(len(FIELD_NAMES), 4).astype(np.float32) * 0.1
    grads = attention_backward(temporal, mask, d_repr, att)

    def objective() -> float:
        representations, _ = att.forward(temporal, mask)
        stacked = np.stack([representations[field] for field in FIELD_NAMES])
        return float(np.sum(stacked * d_repr))

    checks = (
        (att.query_vectors, grads["d_query"], (1, 2)),
        (att.W_q, grads["d_Wq"], (2, 1)),
        (att.W_k, grads["d_Wk"], (1, 3)),
        (att.W_v, grads["d_Wv"], (3, 0)),
        (att.W_o, grads["d_Wo"], (0, 2)),
    )
    eps = 1e-3
    for param, grad, index in checks:
        original = float(param[index])
        param[index] = original + eps
        plus = objective()
        param[index] = original - eps
        minus = objective()
        param[index] = original
        numerical = (plus - minus) / (2.0 * eps)
        assert grad[index] == pytest.approx(numerical, rel=3e-2, abs=2e-3)


def test_dataset_hash_covers_transcript_and_skill_content() -> None:
    ds = build_synthetic_dataset(2, config=_tiny(), seed=0)
    original = dataset_content_sha256(ds)
    ds[0].transcript.messages[0].content += " changed"
    assert dataset_content_sha256(ds) != original
    after_transcript = dataset_content_sha256(ds)
    ds[0].skills[0]["instructions"] += " changed"
    assert dataset_content_sha256(ds) != after_transcript


def test_full_attention_trainer_one_epoch_reduces_or_finite_loss(tmp_path: Path) -> None:
    cfg = _tiny()
    ds = build_synthetic_dataset(4, config=cfg, seed=7)
    train_cfg = FullAttentionTrainConfig(
        epochs=2,
        seed=7,
        ckpt_dir=str(tmp_path / "ckpt"),
        run_name="unit",
        save_every_epoch=False,
        log_every=1,
    )
    pipe, heads, hist = train_full_attention(
        ds, ds, tse_config=cfg, train_config=train_cfg
    )
    assert hist.trainer == TRAINER_ID
    assert hist.seed == 7
    assert len(hist.epochs) == 2
    assert hist.train_input_sha256 == dataset_content_sha256(ds)
    assert Path(hist.ckpt_path).is_file()
    meta = json.loads(Path(hist.ckpt_path).with_name("latest.meta.json").read_text())
    assert meta["trainer"] == TRAINER_ID
    assert meta["seed"] == 7
    assert "train_input_sha256" in meta
    assert all(np.isfinite(e["loss"]) for e in hist.epochs)


def test_trainer_module_does_not_import_scripts() -> None:
    import agents.tse.full_attention_trainer as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "scripts/" not in src
    assert "import scripts" not in src
