# -*- coding: utf-8 -*-
"""Stage 2: TCN temporal module (Bai 2018 dilated conv stack).

Pure numpy implementation of depthwise-separable dilated 1D convolutions
with residual + LayerNorm. Receptive field with k=3, d={1,2,4} ≈ 29 steps.
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

from .config import TSEConfig


def layer_norm(x: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """LayerNorm over last dim. x: (..., C)."""
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return (x - mean) / np.sqrt(var + eps)


def _same_pad_1d(x: np.ndarray, kernel_size: int, dilation: int) -> np.ndarray:
    """Pad time axis for 'same' length. x: (C, T)."""
    pad = dilation * (kernel_size - 1) // 2
    if pad <= 0:
        return x
    return np.pad(x, ((0, 0), (pad, pad)), mode="constant")


def dilated_depthwise_conv1d(
    x: np.ndarray,
    depthwise_w: np.ndarray,
    pointwise_w: np.ndarray,
    dilation: int,
) -> np.ndarray:
    """
    x: (C_in, T)
    depthwise_w: (C_in, K)
    pointwise_w: (C_out, C_in)
    returns: (C_out, T)
    """
    c_in, t = x.shape
    k = depthwise_w.shape[1]
    xp = _same_pad_1d(x, k, dilation)
    # depthwise
    dw_out = np.zeros((c_in, t), dtype=np.float32)
    for c in range(c_in):
        for i in range(t):
            acc = 0.0
            for j in range(k):
                acc += float(xp[c, i + j * dilation] * depthwise_w[c, j])
            dw_out[c, i] = acc
    # pointwise 1x1
    return pointwise_w @ dw_out


class DilatedConvBlock:
    def __init__(
        self,
        channels: int,
        kernel_size: int = 3,
        dilation: int = 1,
        seed: int = 0,
    ):
        rng = np.random.RandomState(seed + dilation * 17)
        # He-ish scale
        scale_dw = (2.0 / (kernel_size)) ** 0.5 * 0.5
        scale_pw = (2.0 / channels) ** 0.5 * 0.5
        self.depthwise_w = rng.normal(0, scale_dw, size=(channels, kernel_size)).astype(np.float32)
        self.pointwise_w = rng.normal(0, scale_pw, size=(channels, channels)).astype(np.float32)
        self.dilation = dilation
        self.kernel_size = kernel_size
        # residual is identity when dims match

    def forward(self, x: np.ndarray) -> np.ndarray:
        """x: (C, T) → (C, T)"""
        residual = x
        out = dilated_depthwise_conv1d(x, self.depthwise_w, self.pointwise_w, self.dilation)
        # LayerNorm over channels per time step: treat as (T, C)
        out_t = out.T  # (T, C)
        out_t = layer_norm(out_t)
        out = out_t.T
        out = np.maximum(out, 0)  # ReLU
        return out + residual


class TCNTemporalModule:
    """
    Multi-layer dilated TCN over utterance sequence.

    Input:  (N, input_dim)
    Output: (N, hidden_dim)
    """

    def __init__(self, config: TSEConfig | None = None):
        self.config = config or TSEConfig()
        cfg = self.config
        self.hidden = cfg.tcn_hidden_dim
        rng = np.random.RandomState(cfg.hash_seed + 99)
        # input projection
        self.W_in = rng.normal(0, 0.05, size=(cfg.embed_dim, self.hidden)).astype(np.float32)
        self.b_in = np.zeros(self.hidden, dtype=np.float32)
        dilations: Sequence[int] = cfg.dilations or [1, 2, 4]
        self.blocks: List[DilatedConvBlock] = [
            DilatedConvBlock(
                channels=self.hidden,
                kernel_size=cfg.tcn_kernel_size,
                dilation=int(d),
                seed=cfg.hash_seed + 1000 + i * 31,
            )
            for i, d in enumerate(dilations)
        ]
        self.W_out = rng.normal(0, 0.05, size=(self.hidden, self.hidden)).astype(np.float32)
        self.b_out = np.zeros(self.hidden, dtype=np.float32)

    def forward(self, utterance_embeddings: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        utterance_embeddings: (N, D)
        mask: (N,) 1=real 0=pad
        returns: (N, H)
        """
        if utterance_embeddings.size == 0:
            return np.zeros((0, self.hidden), dtype=np.float32)

        # project: (N, H)
        x = utterance_embeddings @ self.W_in + self.b_in
        # TCN expects (C, T)
        h = x.T.astype(np.float32)  # (H, N)
        m = mask.astype(np.float32).reshape(1, -1)  # (1, N)
        for block in self.blocks:
            h = block.forward(h)
            h = h * m
        # back to (N, H)
        y = h.T
        y = y @ self.W_out + self.b_out
        y = layer_norm(y)
        y = y * mask.reshape(-1, 1)
        return y.astype(np.float32)

    @staticmethod
    def receptive_field(num_layers: int = 3, kernel_size: int = 3) -> int:
        """1 + 2 * sum_{i=0}^{L-1} 2^i * (k-1)/?  for k=3: RF = 1 + 2*sum(d_i)."""
        dilations = [2 ** i for i in range(num_layers)]
        return 1 + 2 * sum(dilations)  # 1+2*(1+2+4)=15 one side; full window 29 if bilateral
