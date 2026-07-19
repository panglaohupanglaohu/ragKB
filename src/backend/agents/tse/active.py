# -*- coding: utf-8 -*-
"""Active learning loop for TSE.

Select high-uncertainty discussions for human verification, then merge
verified gold into the training JSONL and retrain.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from .dataset import ExtractionExample, PlazaExtractionDataset
from .heads import MultiTaskHeads
from .pipeline import TSEPipeline
from .transcript import PlazaTranscript

logger = logging.getLogger(__name__)


def sample_uncertainty(
    pipeline: TSEPipeline,
    heads: MultiTaskHeads,
    transcripts: Sequence[PlazaTranscript],
    *,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Rank transcripts by predictive uncertainty:
    - category entropy (higher = more uncertain)
    - tools prediction sparsity / low max prob
    """
    scored: List[Dict[str, Any]] = []
    for tr in transcripts:
        if not tr.messages:
            continue
        stages = pipeline.encode_stages(tr)
        pred = heads.predict(stages["skill_repr"])
        probs = pred.get("category_probs")
        if probs is None:
            ent = 1.0
        else:
            p = np.clip(np.asarray(probs, dtype=np.float64), 1e-9, 1.0)
            ent = float(-(p * np.log(p)).sum())
        tools_p = pred.get("tools_probs")
        tools_conf = float(np.max(tools_p)) if tools_p is not None and len(tools_p) else 0.0
        # high entropy, low tool confidence → query human
        score = ent + (1.0 - tools_conf) * 0.5
        scored.append({
            "discussion_id": tr.discussion_id,
            "topic": tr.topic,
            "uncertainty": score,
            "category_entropy": ent,
            "tools_max_prob": tools_conf,
            "pred_category": pred.get("category"),
            "pred_tools": pred.get("required_tools"),
            "focus_indices": stages["focus_indices"],
            "transcript": tr.to_dict(),
        })
    scored.sort(key=lambda x: -x["uncertainty"])
    return scored[:top_k]


def write_review_queue(items: Sequence[Dict[str, Any]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(items), ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("active learning queue → %s (%d)", path, len(items))
    return path


def merge_verified_into_dataset(
    dataset_path: str | Path,
    verified_examples: Sequence[ExtractionExample | Dict[str, Any]],
) -> PlazaExtractionDataset:
    """Append human-verified gold examples (source=gold, verified=True)."""
    path = Path(dataset_path)
    ds = PlazaExtractionDataset.load_jsonl(path) if path.exists() else PlazaExtractionDataset()
    for item in verified_examples:
        if isinstance(item, ExtractionExample):
            ex = item
        else:
            ex = ExtractionExample.from_dict(item)
        ex.verified = True
        ex.source = "gold"
        ds.append(ex)
    ds.save_jsonl(path)
    return ds


def active_learning_step(
    pipeline: TSEPipeline,
    heads: MultiTaskHeads,
    unlabeled: Sequence[PlazaTranscript],
    *,
    queue_path: str | Path,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """One active learning selection step."""
    items = sample_uncertainty(pipeline, heads, unlabeled, top_k=top_k)
    write_review_queue(items, queue_path)
    return items
