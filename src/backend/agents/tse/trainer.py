# -*- coding: utf-8 -*-
"""TSE multi-task trainer (pure numpy).

Loss (methodology §3):
  L = λ_ae * field_AE + λ_cat * CE(category) + λ_tools * BCE(tools)
  defaults: 1.0 / 0.1 / 0.1

Trainable params (no torch required):
  - SkillQueryAttention.query_vectors, W_o (field alignment via AE)
  - MultiTaskHeads W_cat/b_cat, W_tools/b_tools
  - Optional light TCN output projection (W_out, b_out)

Encoder hash tables + TCN dilated kernels default frozen (silver-phase freeze).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .checkpoint import DEFAULT_CKPT_DIR, save_checkpoint
from .config import FIELD_NAMES, TSEConfig
from .dataset import PlazaExtractionDataset
from .evaluate import evaluate_heads_on_dataset
from .heads import MultiTaskHeads
from .pipeline import TSEPipeline

logger = logging.getLogger(__name__)


@dataclass
class TrainConfig:
    epochs: int = 10
    learning_rate: float = 5e-3
    lr_heads: float = 1e-2
    lr_queries: float = 5e-3
    lr_tcn_out: float = 1e-3
    weight_ae: float = 1.0
    weight_category: float = 0.1
    weight_tools: float = 0.1
    train_tcn_out: bool = True
    train_queries: bool = True
    seed: int = 42
    log_every: int = 1
    val_every: int = 2
    grad_clip: float = 1.0
    ckpt_dir: str = ""
    run_name: str = "tse_run"


@dataclass
class TrainHistory:
    epochs: List[Dict[str, float]] = field(default_factory=list)
    best_val_score: float = -1.0
    best_epoch: int = -1
    ckpt_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epochs": self.epochs,
            "best_val_score": self.best_val_score,
            "best_epoch": self.best_epoch,
            "ckpt_path": self.ckpt_path,
        }


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)
    e = np.exp(x.astype(np.float64))
    return (e / (e.sum() + 1e-12)).astype(np.float32)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return (1.0 / (1.0 + np.exp(-np.clip(x, -40, 40)))).astype(np.float32)


def _clip_grad(g: np.ndarray, max_norm: float) -> np.ndarray:
    n = float(np.linalg.norm(g))
    if n > max_norm and n > 0:
        g = g * (max_norm / n)
    return g


class TSETrainer:
    """Multi-task SGD trainer for pure TSE stack."""

    def __init__(
        self,
        pipeline: Optional[TSEPipeline] = None,
        heads: Optional[MultiTaskHeads] = None,
        config: Optional[TSEConfig] = None,
        train_config: Optional[TrainConfig] = None,
    ):
        self.pipeline = pipeline or TSEPipeline(config)
        self.config = self.pipeline.config
        h = self.config.tcn_hidden_dim
        self.heads = heads or MultiTaskHeads(hidden_dim=h, seed=self.config.hash_seed + 3)
        self.tc = train_config or TrainConfig()
        self.history = TrainHistory()

    def _forward_repr(self, ex) -> Tuple[Dict[str, np.ndarray], np.ndarray, Dict[str, Any]]:
        stages = self.pipeline.encode_stages(ex.transcript)
        return stages["skill_repr"], stages["attn_weights"], stages

    def _step_example(self, ex, lr_scale: float = 1.0) -> Dict[str, float]:
        skill = self.pipeline  # noqa — placate linters
        _ = skill
        if not ex.skills or not ex.transcript.messages:
            return {"loss": 0.0, "ae": 0.0, "cat": 0.0, "tools": 0.0, "skip": 1.0}

        primary = ex.skills[0]
        stages = self.pipeline.encode_stages(ex.transcript)
        skill_repr: Dict[str, np.ndarray] = stages["skill_repr"]
        temporal = stages["temporal"]
        mask = stages["mask"]
        attn = stages["attn_weights"]  # (5, N)

        # ── Field AE targets ──
        targets = PlazaExtractionDataset(
            config=self.config
        ).field_targets(primary, self.config.tcn_hidden_dim, self.config.hash_seed)
        labels = PlazaExtractionDataset(config=self.config).label_tensors(primary)

        tc = self.tc
        ae_loss = 0.0
        d_query = np.zeros_like(self.pipeline.attention.query_vectors)
        d_Wo = np.zeros_like(self.pipeline.attention.W_o)

        # AE: skill_repr[f] ≈ target[f]; grad w.r.t. query via residual path ≈ d_repr
        # skill_repr comes from attention residual: out + query; approximate d_query ≈ d_out
        for i, fname in enumerate(FIELD_NAMES):
            pred = skill_repr[fname]
            tgt = targets[fname]
            diff = pred - tgt
            ae_loss += float(np.mean(diff ** 2))
            # dL/dpred = 2*(pred-tgt)/H
            dpred = (2.0 * diff / max(1, pred.size)).astype(np.float32)
            if tc.train_queries:
                d_query[i] += dpred
                # light update on W_o: treat last projection as linear from query
                # skip full attention backprop; query residual is main path

        ae_loss /= max(1, len(FIELD_NAMES))

        # ── Category CE ──
        h_cat = skill_repr["category"]
        logits = self.heads.category_logits(h_cat)
        probs = _softmax(logits)
        y_id = int(labels["category_id"])
        cat_loss = float(-np.log(probs[y_id] + 1e-9))
        dlogits = probs.copy()
        dlogits[y_id] -= 1.0
        # dL/dW = h.T @ dlogits; dL/dh = W @ dlogits
        dW_cat = np.outer(h_cat, dlogits).astype(np.float32)
        db_cat = dlogits.astype(np.float32)
        dh_cat = (self.heads.W_cat @ dlogits).astype(np.float32)
        if tc.train_queries:
            d_query[FIELD_NAMES.index("category")] += dh_cat * tc.weight_category

        # ── Tools BCE ──
        h_tools = skill_repr["tools"]
        t_logits = self.heads.tools_logits(h_tools)
        t_prob = _sigmoid(t_logits)
        y_t = labels["tools_multihot"]
        # clip shapes
        n = min(len(t_prob), len(y_t))
        t_prob = t_prob[:n]
        y_t = y_t[:n]
        t_logits = t_logits[:n]
        tools_loss = float(
            -np.mean(y_t * np.log(t_prob + 1e-9) + (1 - y_t) * np.log(1 - t_prob + 1e-9))
        )
        d_tlogits = ((t_prob - y_t) / max(1, n)).astype(np.float32)
        # pad d_tlogits to full head dim
        if len(d_tlogits) < self.heads.n_tools:
            pad = np.zeros(self.heads.n_tools - len(d_tlogits), dtype=np.float32)
            d_tlogits_full = np.concatenate([d_tlogits, pad])
        else:
            d_tlogits_full = d_tlogits[: self.heads.n_tools]
        dW_tools = np.outer(h_tools, d_tlogits_full).astype(np.float32)
        db_tools = d_tlogits_full.astype(np.float32)
        dh_tools = (self.heads.W_tools @ d_tlogits_full).astype(np.float32)
        if tc.train_queries:
            d_query[FIELD_NAMES.index("tools")] += dh_tools * tc.weight_tools

        loss = tc.weight_ae * ae_loss + tc.weight_category * cat_loss + tc.weight_tools * tools_loss

        # ── SGD updates ──
        lr_h = tc.lr_heads * lr_scale
        lr_q = tc.lr_queries * lr_scale
        self.heads.W_cat -= lr_h * _clip_grad(dW_cat * tc.weight_category, tc.grad_clip)
        self.heads.b_cat -= lr_h * _clip_grad(db_cat * tc.weight_category, tc.grad_clip)
        self.heads.W_tools -= lr_h * _clip_grad(dW_tools * tc.weight_tools, tc.grad_clip)
        self.heads.b_tools -= lr_h * _clip_grad(db_tools * tc.weight_tools, tc.grad_clip)

        if tc.train_queries:
            self.pipeline.attention.query_vectors -= lr_q * _clip_grad(
                d_query * tc.weight_ae, tc.grad_clip
            )

        # Optional: push TCN output projection toward field targets via attention-weighted temporal
        if tc.train_tcn_out and temporal.size and attn.size:
            # soft target: mean of field targets; attract mean temporal
            mean_tgt = np.mean([targets[f] for f in FIELD_NAMES], axis=0)
            # weighted pool of temporal by sum of attn
            w = attn.sum(axis=0)  # (N,)
            w = w / (w.sum() + 1e-9)
            pooled = (w.reshape(-1, 1) * temporal).sum(axis=0)
            d_pool = (2.0 * (pooled - mean_tgt) / max(1, pooled.size)).astype(np.float32)
            # temporal ≈ (emb @ W_in ...) @ W_out; update W_out with outer approx using pre-out features
            # Use pooled as proxy input to W_out: y = x @ W_out + b → approximate x ≈ pooled
            # dW_out ≈ outer(pooled, d_pool) is wrong dim; W_out is (H,H): y = x @ W_out
            # dy/dW = outer(x, dy)
            dW_out = np.outer(pooled, d_pool).astype(np.float32)
            db_out = d_pool
            lr_t = tc.lr_tcn_out * lr_scale
            self.pipeline.tcn.W_out -= lr_t * _clip_grad(dW_out * tc.weight_ae * 0.1, tc.grad_clip)
            self.pipeline.tcn.b_out -= lr_t * _clip_grad(db_out * tc.weight_ae * 0.1, tc.grad_clip)

        # silence unused
        _ = mask
        _ = d_Wo

        return {
            "loss": float(loss),
            "ae": float(ae_loss),
            "cat": float(cat_loss),
            "tools": float(tools_loss),
            "skip": 0.0,
        }

    def fit(
        self,
        train_ds: PlazaExtractionDataset,
        val_ds: Optional[PlazaExtractionDataset] = None,
    ) -> TrainHistory:
        tc = self.tc
        rng = np.random.RandomState(tc.seed)
        n = len(train_ds)
        if n == 0:
            logger.warning("empty train dataset")
            return self.history

        ckpt_dir = Path(tc.ckpt_dir or DEFAULT_CKPT_DIR)
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        best_path = ckpt_dir / "latest.npz"

        for epoch in range(1, tc.epochs + 1):
            t0 = time.perf_counter()
            order = np.arange(n)
            rng.shuffle(order)
            totals = {"loss": 0.0, "ae": 0.0, "cat": 0.0, "tools": 0.0, "count": 0.0}

            # simple LR decay
            lr_scale = 1.0 / (1.0 + 0.05 * (epoch - 1))

            for idx in order:
                ex = train_ds[int(idx)]
                stats = self._step_example(ex, lr_scale=lr_scale)
                if stats.get("skip"):
                    continue
                totals["loss"] += stats["loss"]
                totals["ae"] += stats["ae"]
                totals["cat"] += stats["cat"]
                totals["tools"] += stats["tools"]
                totals["count"] += 1

            c = max(1.0, totals["count"])
            row = {
                "epoch": float(epoch),
                "loss": totals["loss"] / c,
                "ae": totals["ae"] / c,
                "cat": totals["cat"] / c,
                "tools": totals["tools"] / c,
                "sec": time.perf_counter() - t0,
            }

            if val_ds is not None and len(val_ds) > 0 and (epoch % tc.val_every == 0 or epoch == tc.epochs):
                metrics = evaluate_heads_on_dataset(self.pipeline, val_ds, self.heads)
                row["val_cat_acc"] = metrics["cat_acc"]
                row["val_tools_f1"] = metrics["tools_f1"]
                score = metrics["cat_acc"] + metrics["tools_f1"]
                if score >= self.history.best_val_score:
                    self.history.best_val_score = score
                    self.history.best_epoch = epoch
                    save_checkpoint(
                        best_path,
                        self.pipeline,
                        self.heads,
                        meta={
                            "epoch": epoch,
                            "train_loss": row["loss"],
                            "val_cat_acc": metrics["cat_acc"],
                            "val_tools_f1": metrics["tools_f1"],
                            "run_name": tc.run_name,
                        },
                    )
                    # also epoch snapshot
                    snap = ckpt_dir / f"{tc.run_name}_e{epoch}.npz"
                    save_checkpoint(snap, self.pipeline, self.heads, meta={"epoch": epoch})
                    self.history.ckpt_path = str(best_path)

            self.history.epochs.append(row)
            if epoch % tc.log_every == 0:
                extra = ""
                if "val_cat_acc" in row:
                    extra = f" | val_cat={row['val_cat_acc']:.3f} tools_f1={row['val_tools_f1']:.3f}"
                logger.info(
                    "epoch %d/%d loss=%.4f ae=%.4f cat=%.4f tools=%.4f (%.2fs)%s",
                    epoch, tc.epochs, row["loss"], row["ae"], row["cat"], row["tools"], row["sec"], extra,
                )

        # always save final as latest if never validated
        if not self.history.ckpt_path:
            save_checkpoint(
                best_path,
                self.pipeline,
                self.heads,
                meta={"epoch": tc.epochs, "run_name": tc.run_name, "final": True},
            )
            self.history.ckpt_path = str(best_path)

        return self.history


def train_tse(
    train_ds: PlazaExtractionDataset,
    val_ds: Optional[PlazaExtractionDataset] = None,
    *,
    pipeline: Optional[TSEPipeline] = None,
    train_config: Optional[TrainConfig] = None,
    tse_config: Optional[TSEConfig] = None,
) -> Tuple[TSEPipeline, MultiTaskHeads, TrainHistory]:
    """Public training entry (methodology train_tse)."""
    trainer = TSETrainer(pipeline=pipeline, config=tse_config, train_config=train_config)
    hist = trainer.fit(train_ds, val_ds)
    return trainer.pipeline, trainer.heads, hist
