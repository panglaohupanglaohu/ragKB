# -*- coding: utf-8 -*-
"""Stage 1: Utterance encoder.

Production path: feature-hashed character n-gram embeddings (no torch).
Optional Longformer path is stubbed when transformers/torch available
and prefer_torch=True (weights not loaded unless checkpoint configured).
"""

from __future__ import annotations

import hashlib
import math
import struct
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .config import TSEConfig
from .transcript import PlazaTranscript, Utterance


# Fixed small vocabs for aux embeddings (extendable; unknown → 0)
DEFAULT_ROLES = [
    "unknown", "participant", "architect", "devops", "pm", "security",
    "data", "research", "developer", "document", "moderator", "analyst",
]
DEFAULT_SIGNALS = [
    "unknown", "supplement", "challenge", "support", "propose", "summarize",
    "question", "answer", "objection", "consensus",
]
DEFAULT_NICHES = [
    "unknown", "analyst", "moderator", "executor", "reviewer", "scout",
]


def _stable_hash_u32(text: str, seed: int) -> int:
    h = hashlib.blake2b(f"{seed}:{text}".encode("utf-8"), digest_size=8)
    return struct.unpack("<Q", h.digest())[0] & 0xFFFFFFFF


def hash_embed_text(text: str, dim: int, seed: int) -> np.ndarray:
    """Character 2/3-gram feature hashing into fixed dim (signed)."""
    vec = np.zeros(dim, dtype=np.float32)
    t = (text or "").lower()
    if not t:
        return vec
    # unigrams of CJK / words + char ngrams
    grams: List[str] = []
    for n in (1, 2, 3):
        if len(t) < n:
            continue
        for i in range(len(t) - n + 1):
            grams.append(t[i : i + n])
    # also split on whitespace tokens
    for tok in t.replace("，", " ").replace("。", " ").split():
        if tok:
            grams.append(f"W:{tok[:24]}")
    for g in grams:
        hv = _stable_hash_u32(g, seed)
        idx = hv % dim
        sign = 1.0 if (hv >> 16) & 1 else -1.0
        vec[idx] += sign
    # L2 normalize
    nrm = float(np.linalg.norm(vec))
    if nrm > 1e-8:
        vec /= nrm
    return vec


def _vocab_index(value: str, vocab: Sequence[str]) -> int:
    v = (value or "").strip().lower()
    if not v:
        return 0
    for i, name in enumerate(vocab):
        if name == v:
            return i
    # soft match substring
    for i, name in enumerate(vocab):
        if name != "unknown" and (name in v or v in name):
            return i
    return 0


def _make_table(n_rows: int, dim: int, seed: int, tag: str) -> np.ndarray:
    rng = np.random.RandomState(_stable_hash_u32(tag, seed) % (2**31 - 1))
    table = rng.normal(0.0, 0.02, size=(n_rows, dim)).astype(np.float32)
    # row-normalize lightly
    norms = np.linalg.norm(table, axis=1, keepdims=True) + 1e-8
    return table / norms * 0.1


class UtteranceEncoder:
    """Encode N utterances → (N, embed_dim) with aux speaker/role embeddings."""

    def __init__(self, config: TSEConfig | None = None):
        self.config = config or TSEConfig()
        d = self.config.embed_dim
        seed = self.config.hash_seed
        self.role_table = _make_table(len(DEFAULT_ROLES), d, seed, "role")
        self.signal_table = _make_table(len(DEFAULT_SIGNALS), d, seed, "signal")
        self.niche_table = _make_table(len(DEFAULT_NICHES), d, seed, "niche")
        self.round_table = _make_table(16, d, seed, "round")

    def encode_utterance(self, utt: Utterance) -> np.ndarray:
        cfg = self.config
        text = (utt.content or "")[: cfg.max_chars_per_utterance]
        h = hash_embed_text(text, cfg.embed_dim, cfg.hash_seed)
        role_i = _vocab_index(utt.role, DEFAULT_ROLES)
        sig_i = _vocab_index(utt.ritual_signal, DEFAULT_SIGNALS)
        niche_i = _vocab_index(utt.niche_role, DEFAULT_NICHES)
        rnd_i = max(0, min(15, int(utt.round_number)))
        emb = (
            h
            + 0.1 * self.role_table[role_i]
            + 0.1 * self.signal_table[sig_i]
            + 0.1 * self.niche_table[niche_i]
            + 0.05 * self.round_table[rnd_i]
        )
        nrm = float(np.linalg.norm(emb))
        if nrm > 1e-8:
            emb = emb / nrm
        return emb.astype(np.float32)

    def encode_transcript(self, transcript: PlazaTranscript) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns:
          embeddings: (N, dim)
          mask: (N,) float 1=real
        """
        msgs = transcript.messages[: self.config.max_utterances]
        if not msgs:
            d = self.config.embed_dim
            return np.zeros((0, d), dtype=np.float32), np.zeros((0,), dtype=np.float32)
        embs = np.stack([self.encode_utterance(m) for m in msgs], axis=0)
        mask = np.ones((len(msgs),), dtype=np.float32)
        return embs, mask


def torch_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except Exception:
        return False
