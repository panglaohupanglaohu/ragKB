# -*- coding: utf-8 -*-
"""Save/load TSE pure-numpy weights (TCN + attention + multi-task heads)."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from .config import TSEConfig
from .heads import MultiTaskHeads
from .pipeline import TSEPipeline
from .skill_attention import SkillQueryAttention
from .tcn import TCNTemporalModule

logger = logging.getLogger(__name__)

DEFAULT_CKPT_DIR = Path(__file__).resolve().parents[4] / "storage" / "tse" / "checkpoints"


def _module_arrays(prefix: str, obj: Any, keys: list[str]) -> Dict[str, np.ndarray]:
    out = {}
    for k in keys:
        if hasattr(obj, k):
            out[f"{prefix}.{k}"] = np.asarray(getattr(obj, k), dtype=np.float32)
    return out


def collect_state(pipeline: TSEPipeline, heads: Optional[MultiTaskHeads] = None) -> Dict[str, np.ndarray]:
    """Flatten trainable arrays from pipeline (+ optional heads)."""
    state: Dict[str, np.ndarray] = {}
    # TCN
    tcn = pipeline.tcn
    state.update(_module_arrays("tcn", tcn, ["W_in", "b_in", "W_out", "b_out"]))
    for i, block in enumerate(tcn.blocks):
        state.update(_module_arrays(f"tcn.block{i}", block, ["depthwise_w", "pointwise_w"]))
    # Attention
    att = pipeline.attention
    state.update(_module_arrays("att", att, ["query_vectors", "W_q", "W_k", "W_v", "W_o"]))
    # Encoder tables (aux)
    enc = pipeline.encoder
    state.update(_module_arrays("enc", enc, ["role_table", "signal_table", "niche_table", "round_table"]))
    if heads is not None:
        for k, v in heads.state_dict().items():
            state[f"heads.{k}"] = np.asarray(v, dtype=np.float32)
    return state


def apply_state(pipeline: TSEPipeline, state: Dict[str, np.ndarray], heads: Optional[MultiTaskHeads] = None) -> None:
    """Load arrays into pipeline modules (best-effort shape match)."""
    tcn = pipeline.tcn
    for key, arr in state.items():
        arr = np.asarray(arr, dtype=np.float32)
        if key.startswith("tcn.block"):
            # tcn.block0.depthwise_w
            parts = key.split(".")
            if len(parts) != 3:
                continue
            bi = int(parts[1].replace("block", ""))
            attr = parts[2]
            if bi < len(tcn.blocks) and hasattr(tcn.blocks[bi], attr):
                cur = getattr(tcn.blocks[bi], attr)
                if cur.shape == arr.shape:
                    setattr(tcn.blocks[bi], attr, arr)
        elif key.startswith("tcn."):
            attr = key.split(".", 1)[1]
            if hasattr(tcn, attr) and getattr(tcn, attr).shape == arr.shape:
                setattr(tcn, attr, arr)
        elif key.startswith("att."):
            attr = key.split(".", 1)[1]
            if hasattr(pipeline.attention, attr):
                cur = getattr(pipeline.attention, attr)
                if cur.shape == arr.shape:
                    setattr(pipeline.attention, attr, arr)
        elif key.startswith("enc."):
            attr = key.split(".", 1)[1]
            if hasattr(pipeline.encoder, attr):
                cur = getattr(pipeline.encoder, attr)
                if cur.shape == arr.shape:
                    setattr(pipeline.encoder, attr, arr)
        elif key.startswith("heads.") and heads is not None:
            attr = key.split(".", 1)[1]
            if hasattr(heads, attr):
                cur = getattr(heads, attr)
                if cur.shape == arr.shape:
                    setattr(heads, attr, arr)


def save_checkpoint(
    path: str | Path,
    pipeline: TSEPipeline,
    heads: Optional[MultiTaskHeads] = None,
    *,
    meta: Optional[Dict[str, Any]] = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = collect_state(pipeline, heads)
    meta_obj = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "embed_dim": pipeline.config.embed_dim,
        "tcn_hidden_dim": pipeline.config.tcn_hidden_dim,
        "hash_seed": pipeline.config.hash_seed,
        "keys": list(state.keys()),
        **(meta or {}),
    }
    # npz cannot store nested dict easily — store meta JSON sidecar
    np.savez_compressed(path, **state)
    meta_path = path.with_suffix(path.suffix + ".meta.json") if path.suffix else Path(str(path) + ".meta.json")
    if path.suffix == ".npz":
        meta_path = path.with_name(path.stem + ".meta.json")
    else:
        meta_path = Path(str(path) + ".meta.json")
    meta_path.write_text(json.dumps(meta_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("saved TSE checkpoint %s (%d tensors)", path, len(state))
    return path


def load_checkpoint(
    path: str | Path,
    pipeline: TSEPipeline,
    heads: Optional[MultiTaskHeads] = None,
) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    data = np.load(path, allow_pickle=False)
    state = {k: data[k] for k in data.files}
    apply_state(pipeline, state, heads)
    meta: Dict[str, Any] = {}
    meta_path = path.with_name(path.stem + ".meta.json")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    logger.info("loaded TSE checkpoint %s (%d tensors)", path, len(state))
    return meta


def latest_checkpoint(ckpt_dir: str | Path | None = None) -> Optional[Path]:
    d = Path(ckpt_dir or DEFAULT_CKPT_DIR)
    if not d.exists():
        return None
    cands = sorted(d.glob("*.npz"), key=lambda p: p.stat().st_mtime, reverse=True)
    # prefer latest.npz if present
    preferred = d / "latest.npz"
    if preferred.exists():
        return preferred
    return cands[0] if cands else None
