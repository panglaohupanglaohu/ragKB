# -*- coding: utf-8 -*-
"""Stage 3: Skill Query Cross-Attention.

5 learnable query vectors (name/desc/category/tools/instr) attend over
TCN outputs via multi-head scaled dot-product attention.

Pure numpy path; field keyword seeds bias queries toward skill-relevant
utterances when weights are untrained (cold-start prior).
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

from .config import FIELD_KEYWORD_SEEDS, FIELD_NAMES, TSEConfig
from .encoder import hash_embed_text
from .transcript import PlazaTranscript


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / (np.sum(e, axis=axis, keepdims=True) + 1e-9)


class SkillQueryAttention:
    """Cross-attention: Q_skill × K/V_temporal → field representations."""

    def __init__(self, config: TSEConfig | None = None):
        self.config = config or TSEConfig()
        cfg = self.config
        h = cfg.tcn_hidden_dim
        self.hidden_dim = h
        self.num_heads = max(1, cfg.num_heads)
        self.head_dim = h // self.num_heads
        # ensure divisible
        self.proj_dim = self.head_dim * self.num_heads
        rng = np.random.RandomState(cfg.hash_seed + 777)

        self.query_vectors = rng.normal(0, 0.02, size=(len(FIELD_NAMES), h)).astype(np.float32)
        # Cold-start: mix field keyword embeddings into queries
        for i, field in enumerate(FIELD_NAMES):
            seeds = FIELD_KEYWORD_SEEDS.get(field, ())
            if not seeds:
                continue
            acc = np.zeros(h, dtype=np.float32)
            for s in seeds:
                e = hash_embed_text(s, h, cfg.hash_seed + i)
                # pad/truncate to h
                if e.shape[0] < h:
                    e = np.pad(e, (0, h - e.shape[0]))
                else:
                    e = e[:h]
                acc += e
            acc /= max(1, len(seeds))
            nrm = float(np.linalg.norm(acc)) + 1e-8
            self.query_vectors[i] = 0.7 * self.query_vectors[i] + 0.3 * (acc / nrm)

        scale = (2.0 / h) ** 0.5 * 0.5
        self.W_q = rng.normal(0, scale, size=(h, self.proj_dim)).astype(np.float32)
        self.W_k = rng.normal(0, scale, size=(h, self.proj_dim)).astype(np.float32)
        self.W_v = rng.normal(0, scale, size=(h, self.proj_dim)).astype(np.float32)
        self.W_o = rng.normal(0, scale, size=(self.proj_dim, h)).astype(np.float32)

    def forward(
        self,
        temporal_features: np.ndarray,
        mask: np.ndarray,
    ) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        """
        temporal_features: (N, H)
        mask: (N,)

        Returns:
          skill_repr: dict field → (H,)
          attn_weights: (num_queries, N) averaged over heads
        """
        n = temporal_features.shape[0]
        if n == 0:
            empty = {f: np.zeros(self.hidden_dim, dtype=np.float32) for f in FIELD_NAMES}
            return empty, np.zeros((len(FIELD_NAMES), 0), dtype=np.float32)

        nh = self.num_heads
        hd = self.head_dim
        nq = len(FIELD_NAMES)

        # Q: (nq, proj)  K/V: (N, proj)
        Q = self.query_vectors @ self.W_q  # (nq, proj)
        K = temporal_features @ self.W_k
        V = temporal_features @ self.W_v

        # reshape heads: Q (nq, nh, hd) K/V (N, nh, hd)
        Qh = Q.reshape(nq, nh, hd)
        Kh = K.reshape(n, nh, hd)
        Vh = V.reshape(n, nh, hd)

        # scores: (nh, nq, N)
        scale = hd ** -0.5
        scores = np.einsum("qhd,nhd->hqn", Qh, Kh) * scale
        # mask padded
        m = mask.astype(np.float32)
        scores = scores + (1.0 - m.reshape(1, 1, n)) * (-1e9)
        weights = softmax(scores, axis=-1)  # (nh, nq, N)

        # context: (nh, nq, hd)
        ctx = np.einsum("hqn,nhd->hqd", weights, Vh)
        # merge heads: (nq, nh*hd)
        ctx = np.transpose(ctx, (1, 0, 2)).reshape(nq, nh * hd)
        out = ctx @ self.W_o  # (nq, H)
        # residual + simple LN-ish
        out = out + self.query_vectors
        mean = out.mean(axis=-1, keepdims=True)
        var = out.var(axis=-1, keepdims=True)
        out = (out - mean) / np.sqrt(var + 1e-5)

        attn_avg = weights.mean(axis=0)  # (nq, N)
        skill_repr = {FIELD_NAMES[i]: out[i].astype(np.float32) for i in range(nq)}
        return skill_repr, attn_avg.astype(np.float32)


def select_skill_moments(
    attn_weights: np.ndarray,
    *,
    top_k: int = 8,
) -> List[int]:
    """Union of top-attended utterances across all 5 field queries."""
    if attn_weights.size == 0:
        return []
    nq, n = attn_weights.shape
    scores = attn_weights.sum(axis=0)  # (N,)
    k = max(1, min(top_k, n))
    # also take top-1 per field to guarantee field coverage
    selected = set()
    for q in range(nq):
        selected.add(int(np.argmax(attn_weights[q])))
    order = list(np.argsort(-scores))
    for i in order:
        if len(selected) >= k:
            break
        selected.add(int(i))
    return sorted(selected)


def field_focus_summary(
    transcript: PlazaTranscript,
    attn_weights: np.ndarray,
    top_per_field: int = 3,
) -> Dict[str, List[Dict]]:
    """Debug/telemetry: which utterances each field query focuses on."""
    out: Dict[str, List[Dict]] = {}
    if attn_weights.size == 0:
        return {f: [] for f in FIELD_NAMES}
    n = min(attn_weights.shape[1], len(transcript.messages))
    for qi, field in enumerate(FIELD_NAMES):
        w = attn_weights[qi, :n]
        idxs = list(np.argsort(-w))[:top_per_field]
        rows = []
        for i in idxs:
            msg = transcript.messages[int(i)]
            rows.append({
                "index": int(i),
                "weight": float(w[int(i)]),
                "speaker": msg.speaker_name,
                "round": msg.round_number,
                "preview": (msg.content or "")[:120],
            })
        out[field] = rows
    return out
