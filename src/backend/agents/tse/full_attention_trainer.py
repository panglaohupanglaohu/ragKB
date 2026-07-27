# -*- coding: utf-8 -*-
"""Full multi-head attention SGD trainer (pure NumPy).

Ports the complete W_q/W_k/W_v/W_o + query_vectors backprop from the legacy
one-off retrain script into the TSE package.

Import-safe: no training, file I/O, or global logging configuration at import time.
Does not import the legacy CLI layer.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .checkpoint import DEFAULT_CKPT_DIR, save_checkpoint
from .config import FIELD_NAMES, TSEConfig
from .dataset import ExtractionExample, PlazaExtractionDataset
from .evaluate import evaluate_heads_on_dataset
from .heads import MultiTaskHeads
from .pipeline import TSEPipeline
from .skill_attention import softmax as attention_softmax

logger = logging.getLogger(__name__)

TRAINER_ID = "full_attention_v1"


@dataclass
class FullAttentionTrainConfig:
    """Hyper-parameters for full attention backprop training."""

    epochs: int = 30
    lr: float = 1e-2
    lr_queries: float = 5e-3
    lr_attn_proj: float = 5e-3
    lr_heads: float = 1e-2
    lr_tcn_out: float = 1e-3
    weight_ae: float = 2.0
    weight_category: float = 0.3
    weight_tools: float = 0.3
    seed: int = 42
    grad_clip: float = 2.0
    val_every: int = 3
    train_tcn_out: bool = False
    log_every: int = 1
    ckpt_dir: str = ""
    run_name: str = "full_attention"
    save_every_epoch: bool = False


@dataclass
class FullAttentionTrainHistory:
    epochs: List[Dict[str, float]] = field(default_factory=list)
    best_val_score: float = -1.0
    best_epoch: int = -1
    ckpt_path: str = ""
    train_input_sha256: str = ""
    val_input_sha256: str = ""
    trainer: str = TRAINER_ID
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epochs": self.epochs,
            "best_val_score": self.best_val_score,
            "best_epoch": self.best_epoch,
            "ckpt_path": self.ckpt_path,
            "train_input_sha256": self.train_input_sha256,
            "val_input_sha256": self.val_input_sha256,
            "trainer": self.trainer,
            "seed": self.seed,
        }


def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x.astype(np.float64))
    return (e / (np.sum(e, axis=axis, keepdims=True) + 1e-12)).astype(np.float32)


def _ce_loss_and_grad(logits: np.ndarray, y_id: int) -> Tuple[float, np.ndarray]:
    probs = _softmax(logits, axis=0)
    loss = float(-np.log(probs[y_id] + 1e-12))
    dlogits = probs.copy()
    dlogits[y_id] -= 1.0
    return loss, dlogits


def _bce_loss_and_grad(logits: np.ndarray, y: np.ndarray) -> Tuple[float, np.ndarray]:
    n = min(len(logits), len(y))
    prob = 1.0 / (1.0 + np.exp(-np.clip(logits[:n], -40, 40)))
    loss = float(
        -np.mean(y[:n] * np.log(prob + 1e-12) + (1 - y[:n]) * np.log(1 - prob + 1e-12))
    )
    dlogits = np.zeros_like(logits, dtype=np.float32)
    dlogits[:n] = ((prob - y[:n]) / max(1, n)).astype(np.float32)
    return loss, dlogits


def _clip(g: np.ndarray, max_norm: float) -> np.ndarray:
    n = float(np.linalg.norm(g))
    if n > max_norm and n > 0:
        g = g * (max_norm / n)
    return g.astype(np.float32)


def dataset_content_sha256(dataset: PlazaExtractionDataset) -> str:
    """Stable hash of complete ordered examples for checkpoint metadata."""
    payload = [ex.to_dict() for ex in dataset.examples]
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def attention_backward(
    temporal: np.ndarray,
    mask: np.ndarray,
    d_repr: np.ndarray,
    params,
) -> Dict[str, np.ndarray]:
    """Backprop through multi-head cross-attention into Q/K/V/O and queries.

    Parameters
    ----------
    temporal : (N, H)
    mask : (N,)
    d_repr : (nq, H) gradient w.r.t. post-LayerNorm skill field representations
    params : SkillQueryAttention-like object with query_vectors, W_q, W_k, W_v, W_o

    Returns
    -------
    grads dict with d_query, d_Wq, d_Wk, d_Wv, d_Wo
    """
    att = params
    n = temporal.shape[0]
    h = att.hidden_dim
    nh = att.num_heads
    hd = att.head_dim
    nq = len(FIELD_NAMES)
    if n == 0:
        zq = np.zeros_like(att.query_vectors)
        return {
            "d_query": zq,
            "d_Wq": np.zeros_like(att.W_q),
            "d_Wk": np.zeros_like(att.W_k),
            "d_Wv": np.zeros_like(att.W_v),
            "d_Wo": np.zeros_like(att.W_o),
        }

    Q = att.query_vectors @ att.W_q
    K = temporal @ att.W_k
    V = temporal @ att.W_v
    Qh = Q.reshape(nq, nh, hd)
    Kh = K.reshape(n, nh, hd)
    Vh = V.reshape(n, nh, hd)
    scale = hd ** -0.5
    scores = np.einsum("qhd,nhd->hqn", Qh, Kh) * scale
    m = mask.astype(np.float32)
    scores = scores + (1.0 - m.reshape(1, 1, n)) * (-1e9)
    weights = attention_softmax(scores, axis=-1).astype(np.float32)
    ctx_v = np.einsum("hqn,nhd->hqd", weights, Vh)
    ctx_flat = np.transpose(ctx_v, (1, 0, 2)).reshape(nq, nh * hd)

    pre_norm = ctx_flat @ att.W_o + att.query_vectors
    mean = pre_norm.mean(axis=-1, keepdims=True)
    centered = pre_norm - mean
    inv_std = 1.0 / np.sqrt(pre_norm.var(axis=-1, keepdims=True) + 1e-5)
    normalized = centered * inv_std
    d_norm = d_repr.astype(np.float32)
    width = max(1, pre_norm.shape[-1])
    d_out = (
        inv_std
        / width
        * (
            width * d_norm
            - d_norm.sum(axis=-1, keepdims=True)
            - normalized * (d_norm * normalized).sum(axis=-1, keepdims=True)
        )
    ).astype(np.float32)
    d_query = d_out.copy()

    d_Wo = np.einsum("qp,qh->ph", ctx_flat, d_out).astype(np.float32)
    d_ctx = (d_out @ att.W_o.T).astype(np.float32)
    d_ctx_h = d_ctx.reshape(nq, nh, hd)

    d_Vh = np.einsum("hqn,qhd->nhd", weights, d_ctx_h)
    d_weights = np.einsum("nhd,qhd->hqn", Vh, d_ctx_h)

    d_scores = np.zeros_like(weights)
    for hi in range(nh):
        for qi in range(nq):
            w = weights[hi, qi, :]
            dw = d_weights[hi, qi, :]
            d_scores[hi, qi, :] = w * (dw - np.dot(dw, w))
    d_scores = d_scores * scale

    d_Qh = np.einsum("hqn,nhd->qhd", d_scores, Kh)
    d_Q = d_Qh.reshape(nq, nh * hd)
    d_Wq = (att.query_vectors.T @ d_Q).astype(np.float32)
    d_query = d_query + (d_Q @ att.W_q.T).astype(np.float32)

    d_Kh = np.einsum("hqn,qhd->nhd", d_scores, Qh)
    d_K = d_Kh.reshape(n, nh * hd)
    d_Wk = (temporal.T @ d_K).astype(np.float32)

    d_V = d_Vh.reshape(n, nh * hd)
    d_Wv = (temporal.T @ d_V).astype(np.float32)

    return {
        "d_query": d_query.astype(np.float32),
        "d_Wq": d_Wq,
        "d_Wk": d_Wk,
        "d_Wv": d_Wv,
        "d_Wo": d_Wo,
    }


class FullAttentionTrainer:
    """SGD trainer updating query_vectors, W_q/k/v/o, heads, optional tcn.W_out/b_out."""

    def __init__(
        self,
        pipeline: Optional[TSEPipeline] = None,
        heads: Optional[MultiTaskHeads] = None,
        config: Optional[TSEConfig] = None,
        train_config: Optional[FullAttentionTrainConfig] = None,
    ):
        self.pipeline = pipeline or TSEPipeline(config)
        self.config = self.pipeline.config
        h = self.config.tcn_hidden_dim
        self.heads = heads or MultiTaskHeads(
            hidden_dim=h, seed=self.config.hash_seed + 3
        )
        self.tc = train_config or FullAttentionTrainConfig()
        self.history = FullAttentionTrainHistory(seed=self.tc.seed)

    def train_epoch(
        self,
        dataset: PlazaExtractionDataset,
        *,
        epoch: int = 1,
        rng: Optional[np.random.RandomState] = None,
    ) -> Dict[str, float]:
        """One epoch of full-attention SGD. Returns mean loss metrics."""
        tc = self.tc
        rng = rng or np.random.RandomState(tc.seed + epoch)
        n = len(dataset)
        if n == 0:
            return {"loss": 0.0, "ae": 0.0, "cat": 0.0, "tools": 0.0, "count": 0.0}

        order = np.arange(n)
        rng.shuffle(order)
        totals = {"loss": 0.0, "ae": 0.0, "cat": 0.0, "tools": 0.0, "count": 0.0}
        lr_scale = 1.0 / (1.0 + 0.02 * max(0, epoch - 1))
        t0 = time.perf_counter()

        for idx in order:
            stats = self._step_example(dataset[int(idx)], lr_scale=lr_scale)
            if stats.get("skip"):
                continue
            for k in ("loss", "ae", "cat", "tools"):
                totals[k] += stats[k]
            totals["count"] += 1.0

        c = max(1.0, totals["count"])
        return {
            "epoch": float(epoch),
            "loss": totals["loss"] / c,
            "ae": totals["ae"] / c,
            "cat": totals["cat"] / c,
            "tools": totals["tools"] / c,
            "count": totals["count"],
            "sec": time.perf_counter() - t0,
        }

    def _step_example(self, ex: ExtractionExample, *, lr_scale: float) -> Dict[str, float]:
        if not ex.skills or not ex.transcript or not ex.transcript.messages:
            return {"loss": 0.0, "ae": 0.0, "cat": 0.0, "tools": 0.0, "skip": 1.0}

        tc = self.tc
        primary = ex.skills[0]
        stages = self.pipeline.encode_stages(ex.transcript)
        skill_repr = stages["skill_repr"]
        temporal = stages["temporal"]
        mask = stages["mask"]
        attn_w = stages["attn_weights"]
        h = self.config.tcn_hidden_dim
        nq = len(FIELD_NAMES)

        helper = PlazaExtractionDataset(config=self.config)
        targets = helper.field_targets(primary, h, self.config.hash_seed)
        labels = helper.label_tensors(primary)

        ae_loss = 0.0
        d_repr = np.zeros((nq, h), dtype=np.float32)
        for i, fname in enumerate(FIELD_NAMES):
            pred = skill_repr[fname]
            tgt = targets[fname]
            diff = pred - tgt
            ae_loss += float(np.mean(diff ** 2))
            d_repr[i] = (
                tc.weight_ae
                * 2.0
                * diff
                / (max(1, pred.size) * max(1, nq))
            ).astype(np.float32)
        ae_loss /= max(1, nq)

        h_cat = skill_repr["category"]
        cat_logits = self.heads.category_logits(h_cat)
        cat_loss, d_cat_logits = _ce_loss_and_grad(
            cat_logits, int(labels["category_id"])
        )
        d_repr[FIELD_NAMES.index("category")] += (
            self.heads.W_cat @ d_cat_logits
        ) * tc.weight_category

        h_tools = skill_repr["tools"]
        tools_logits = self.heads.tools_logits(h_tools)
        tools_loss, d_tools_logits = _bce_loss_and_grad(
            tools_logits, labels["tools_multihot"]
        )
        d_repr[FIELD_NAMES.index("tools")] += (
            self.heads.W_tools @ d_tools_logits
        ) * tc.weight_tools

        loss = (
            tc.weight_ae * ae_loss
            + tc.weight_category * cat_loss
            + tc.weight_tools * tools_loss
        )

        grads = attention_backward(temporal, mask, d_repr, self.pipeline.attention)

        lr_h = tc.lr_heads * lr_scale
        dW_cat = np.outer(h_cat, d_cat_logits).astype(np.float32)
        db_cat = d_cat_logits.astype(np.float32)
        self.heads.W_cat -= lr_h * _clip(dW_cat * tc.weight_category, tc.grad_clip)
        self.heads.b_cat -= lr_h * _clip(db_cat * tc.weight_category, tc.grad_clip)

        dW_tools = np.outer(h_tools, d_tools_logits).astype(np.float32)
        db_tools = d_tools_logits.astype(np.float32)
        self.heads.W_tools -= lr_h * _clip(dW_tools * tc.weight_tools, tc.grad_clip)
        self.heads.b_tools -= lr_h * _clip(db_tools * tc.weight_tools, tc.grad_clip)

        lr_q = tc.lr_queries * lr_scale
        lr_a = tc.lr_attn_proj * lr_scale
        att = self.pipeline.attention
        att.query_vectors -= lr_q * _clip(grads["d_query"], tc.grad_clip)
        att.W_q -= lr_a * _clip(grads["d_Wq"], tc.grad_clip)
        att.W_k -= lr_a * _clip(grads["d_Wk"], tc.grad_clip)
        att.W_v -= lr_a * _clip(grads["d_Wv"], tc.grad_clip)
        att.W_o -= lr_a * _clip(grads["d_Wo"], tc.grad_clip)

        # Optional legacy auxiliary update. This is not part of the exact
        # attention gradient verified by attention_backward, so it is opt-in.
        if tc.train_tcn_out and temporal.size and attn_w.size:
            mean_tgt = np.mean([targets[f] for f in FIELD_NAMES], axis=0)
            w_sum = attn_w.sum(axis=0)
            w_sum = w_sum / (w_sum.sum() + 1e-9)
            pooled = (w_sum.reshape(-1, 1) * temporal).sum(axis=0)
            d_pool = (2.0 * (pooled - mean_tgt) / max(1, pooled.size)).astype(np.float32)
            dW_out = np.outer(pooled, d_pool).astype(np.float32)
            lr_t = tc.lr_tcn_out * lr_scale
            tcn = self.pipeline.tcn
            tcn.W_out -= lr_t * _clip(dW_out * tc.weight_ae * 0.1, tc.grad_clip)
            tcn.b_out -= lr_t * _clip(d_pool * tc.weight_ae * 0.1, tc.grad_clip)

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
    ) -> FullAttentionTrainHistory:
        tc = self.tc
        self.history = FullAttentionTrainHistory(seed=tc.seed)
        self.history.train_input_sha256 = dataset_content_sha256(train_ds)
        if val_ds is not None and len(val_ds) > 0:
            self.history.val_input_sha256 = dataset_content_sha256(val_ds)

        ckpt_dir = Path(tc.ckpt_dir or DEFAULT_CKPT_DIR)
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        best_path = ckpt_dir / "latest.npz"
        rng = np.random.RandomState(tc.seed)

        for epoch in range(1, tc.epochs + 1):
            row = self.train_epoch(train_ds, epoch=epoch, rng=rng)

            tools_f1 = 0.0
            cat_acc = 0.0
            if val_ds is not None and len(val_ds) > 0 and (
                epoch % max(1, tc.val_every) == 0 or epoch == tc.epochs
            ):
                metrics = evaluate_heads_on_dataset(self.pipeline, val_ds, self.heads)
                cat_acc = float(metrics.get("cat_acc") or 0.0)
                tools_f1 = float(metrics.get("tools_f1") or 0.0)
                row["val_cat_acc"] = cat_acc
                row["val_tools_f1"] = tools_f1
                score = cat_acc + tools_f1
                if score >= self.history.best_val_score:
                    self.history.best_val_score = score
                    self.history.best_epoch = epoch
                    self._save_ckpt(
                        best_path,
                        epoch=epoch,
                        train_loss=row["loss"],
                        tools_f1=tools_f1,
                        cat_acc=cat_acc,
                        train_hash=self.history.train_input_sha256,
                        val_hash=self.history.val_input_sha256,
                    )
                    self.history.ckpt_path = str(best_path)

            if tc.save_every_epoch:
                snap = ckpt_dir / f"{tc.run_name}_e{epoch}.npz"
                self._save_ckpt(
                    snap,
                    epoch=epoch,
                    train_loss=row["loss"],
                    tools_f1=tools_f1,
                    cat_acc=cat_acc,
                    train_hash=self.history.train_input_sha256,
                    val_hash=self.history.val_input_sha256,
                )

            self.history.epochs.append(row)
            if epoch % max(1, tc.log_every) == 0:
                extra = ""
                if "val_tools_f1" in row:
                    extra = (
                        f" | val_cat={row['val_cat_acc']:.3f}"
                        f" tools_f1={row['val_tools_f1']:.3f}"
                    )
                logger.info(
                    "full_attn epoch %d/%d loss=%.4f ae=%.4f cat=%.4f tools=%.4f (%.2fs)%s",
                    epoch,
                    tc.epochs,
                    row["loss"],
                    row["ae"],
                    row["cat"],
                    row["tools"],
                    row["sec"],
                    extra,
                )

        if not self.history.ckpt_path:
            self._save_ckpt(
                best_path,
                epoch=tc.epochs,
                train_loss=self.history.epochs[-1]["loss"] if self.history.epochs else 0.0,
                tools_f1=0.0,
                cat_acc=0.0,
                train_hash=self.history.train_input_sha256,
                val_hash=self.history.val_input_sha256,
            )
            self.history.ckpt_path = str(best_path)
        return self.history

    def _save_ckpt(
        self,
        path: Path,
        *,
        epoch: int,
        train_loss: float,
        tools_f1: float,
        cat_acc: float,
        train_hash: str,
        val_hash: str,
    ) -> None:
        meta = {
            "trainer": TRAINER_ID,
            "epoch": int(epoch),
            "seed": int(self.tc.seed),
            "train_loss": float(train_loss),
            "tools_f1": float(tools_f1),
            "cat_acc": float(cat_acc),
            "train_input_sha256": train_hash,
            "val_input_sha256": val_hash,
            "run_name": self.tc.run_name,
            "train_config": asdict(self.tc),
        }
        save_checkpoint(path, self.pipeline, self.heads, meta=meta)


def train_full_attention(
    train_ds: PlazaExtractionDataset,
    val_ds: Optional[PlazaExtractionDataset] = None,
    *,
    pipeline: Optional[TSEPipeline] = None,
    heads: Optional[MultiTaskHeads] = None,
    train_config: Optional[FullAttentionTrainConfig] = None,
    tse_config: Optional[TSEConfig] = None,
) -> Tuple[TSEPipeline, MultiTaskHeads, FullAttentionTrainHistory]:
    """Public package entry for full-attention training."""
    trainer = FullAttentionTrainer(
        pipeline=pipeline,
        heads=heads,
        config=tse_config,
        train_config=train_config,
    )
    hist = trainer.fit(train_ds, val_ds)
    return trainer.pipeline, trainer.heads, hist
