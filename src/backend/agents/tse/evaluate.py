# -*- coding: utf-8 -*-
"""TSE evaluation: name-level P/R/F1 + multi-task head accuracy."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Set

import numpy as np

from .dataset import PlazaExtractionDataset
from .heads import MultiTaskHeads, category_to_id
from .pipeline import TSEPipeline


def _norm_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[\s_\-]+", "", s)
    return s


def name_set(skills: Sequence[Dict[str, Any]]) -> Set[str]:
    return {_norm_name(str(s.get("name") or "")) for s in skills if s.get("name")}


def prf1(pred: Set[str], gold: Set[str]) -> Dict[str, float]:
    if not pred and not gold:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def evaluate_name_match(
    predictions: Sequence[Sequence[Dict[str, Any]]],
    ground_truth: Sequence[Sequence[Dict[str, Any]]],
) -> Dict[str, float]:
    """Micro-average name set P/R/F1 (methodology evaluate_tse)."""
    tp = fp = fn = 0
    for pred, gold in zip(predictions, ground_truth):
        p, g = name_set(pred), name_set(gold)
        tp += len(p & g)
        fp += len(p - g)
        fn += len(g - p)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": float(tp), "fp": float(fp), "fn": float(fn)}


def evaluate_heads_on_dataset(
    pipeline: TSEPipeline,
    dataset: PlazaExtractionDataset,
    heads: MultiTaskHeads,
) -> Dict[str, float]:
    """Category accuracy + tools micro-F1 from multi-task heads (no decoder LLM)."""
    if len(dataset) == 0:
        return {"cat_acc": 0.0, "tools_f1": 0.0, "n": 0.0}

    cat_ok = 0
    cat_n = 0
    tp = fp = fn = 0

    for ex in dataset:
        if not ex.skills or not ex.transcript.messages:
            continue
        stages = pipeline.encode_stages(ex.transcript)
        pred = heads.predict(stages["skill_repr"])
        gold = ex.skills[0]
        gold_cat = category_to_id(str(gold.get("category") or "general"))
        pred_cat = category_to_id(str(pred["category"]))
        cat_n += 1
        if pred_cat == gold_cat:
            cat_ok += 1
        gold_tools = set(str(t).lower() for t in (gold.get("required_tools") or []))
        pred_tools = set(str(t).lower() for t in (pred.get("required_tools") or []))
        tp += len(pred_tools & gold_tools)
        fp += len(pred_tools - gold_tools)
        fn += len(gold_tools - pred_tools)

    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    tools_f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {
        "cat_acc": cat_ok / cat_n if cat_n else 0.0,
        "tools_f1": tools_f1,
        "n": float(cat_n),
    }


async def evaluate_full_with_decoder(
    pipeline: TSEPipeline,
    dataset: PlazaExtractionDataset,
    *,
    chat_fn=None,
    harness=None,
    max_samples: int = 50,
) -> Dict[str, float]:
    """Optional end-to-end eval (calls decoder LLM if provided)."""
    preds: List[List[Dict[str, Any]]] = []
    golds: List[List[Dict[str, Any]]] = []
    for i, ex in enumerate(dataset):
        if i >= max_samples:
            break
        result = await pipeline.extract(
            "",
            source_title=ex.transcript.topic,
            transcript=ex.transcript,
            harness=harness,
            chat_fn=chat_fn,
        )
        preds.append(result.skills)
        golds.append(ex.skills)
    metrics = evaluate_name_match(preds, golds)
    metrics["n"] = float(len(preds))
    return metrics
