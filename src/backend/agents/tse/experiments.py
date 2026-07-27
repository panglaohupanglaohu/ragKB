# -*- coding: utf-8 -*-
"""Reusable, side-effect-free computations for the paper's TSE experiments."""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np

from .config import FIELD_KEYWORD_SEEDS, FIELD_NAMES, TSEConfig
from .decoder import (
    heuristic_category_hint,
    heuristic_tools_hint,
    synthesize_skills_local,
)
from .encoder import hash_embed_text
from .pipeline import TSEPipeline
from .skill_attention import field_focus_summary, select_skill_moments
from .transcript import PlazaTranscript, parse_transcript


KEYWORD_ATTENTION_ALGORITHM_VERSION = "field-keyword-cosine-v2-shared-hash-space"
LOCAL_BENCHMARK_BOUNDARY = (
    "Measures deterministic local encoding, TCN, field attention/evidence aggregation, "
    "and local synthesis only; excludes online LLM calls, network latency, human review, "
    "tool grounding, safety gates, and regression gates."
)
ATTENTION_DIAGNOSTIC_BOUNDARY = (
    "The keyword baseline is an interpretable diagnostic, not ground truth; the comparison "
    "does not establish an attention phase transition or a validated sample threshold."
)
STAGE_KEYS = (
    "stage1_encoder_ms",
    "stage2_tcn_ms",
    "stage3_attention_evidence_ms",
    "stage4_local_synthesis_ms",
)


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 of the exact input bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_field_evidence_indices(
    field_evidence: Any,
    *,
    n_messages: int,
    sample_id: str = "",
    line_number: int | None = None,
) -> Dict[str, List[int]]:
    """Validate optional per-field gold utterance indices (no OOB, non-empty fields)."""
    loc = f"line {line_number} ({sample_id})" if line_number else sample_id or "sample"
    if field_evidence is None:
        return {}
    if not isinstance(field_evidence, dict):
        raise ValueError(f"{loc}: field_evidence_indices must be an object")
    out: Dict[str, List[int]] = {}
    for field in FIELD_NAMES:
        raw = field_evidence.get(field)
        if raw is None:
            # partial labels allowed only if key missing for all or present for all
            continue
        if not isinstance(raw, (list, tuple)):
            raise ValueError(f"{loc}: field_evidence_indices[{field!r}] must be a list")
        idxs: List[int] = []
        for item in raw:
            try:
                ii = int(item)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{loc}: field_evidence_indices[{field!r}] indices must be ints"
                ) from exc
            if ii < 0 or ii >= n_messages:
                raise ValueError(
                    f"{loc}: field_evidence_indices[{field!r}] index {ii} "
                    f"out of range for n_messages={n_messages}"
                )
            if ii not in idxs:
                idxs.append(ii)
        out[field] = idxs
    # If any field provided, require all five fields present (explicit empty list ok)
    if out and set(out) != set(FIELD_NAMES):
        missing = [f for f in FIELD_NAMES if f not in out]
        raise ValueError(
            f"{loc}: field_evidence_indices missing fields: {', '.join(missing)}"
        )
    return out


def load_experiment_samples(path: str | Path) -> list[PlazaTranscript]:
    """Load and validate the JSONL fixture format used by both experiments.

    Optional per-sample ``field_evidence_indices`` is validated when present and
    stored on ``transcript.meta['field_evidence_indices']`` (backward compatible).
    """
    fixture_path = Path(path)
    samples: list[PlazaTranscript] = []
    seen_ids: set[str] = set()

    for line_number, raw_line in enumerate(
        fixture_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            sample = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{fixture_path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(sample, dict):
            raise ValueError(f"{fixture_path}:{line_number}: sample must be an object")

        sample_id = str(sample.get("sample_id") or "").strip()
        if not sample_id:
            raise ValueError(f"{fixture_path}:{line_number}: sample_id is required")
        if sample_id in seen_ids:
            raise ValueError(f"{fixture_path}:{line_number}: duplicate sample_id {sample_id!r}")
        seen_ids.add(sample_id)

        topic = str(sample.get("topic") or "").strip()
        if not topic:
            raise ValueError(f"{fixture_path}:{line_number} ({sample_id}): topic is required")
        messages = sample.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError(
                f"{fixture_path}:{line_number} ({sample_id}): messages must be a non-empty list"
            )
        for message_index, message in enumerate(messages):
            if not isinstance(message, dict):
                raise ValueError(
                    f"{fixture_path}:{line_number} ({sample_id}): "
                    f"message {message_index} must be an object"
                )
            content = str(
                message.get("content") or message.get("text") or message.get("body") or ""
            ).strip()
            if not content:
                raise ValueError(
                    f"{fixture_path}:{line_number} ({sample_id}): "
                    f"message {message_index} content is required"
                )

        evidence = validate_field_evidence_indices(
            sample.get("field_evidence_indices"),
            n_messages=len(messages),
            sample_id=sample_id,
            line_number=line_number,
        )

        transcript = parse_transcript(
            "",
            source_title=topic,
            source_meta={
                "discussion_id": sample_id,
                "sample_id": sample_id,
                "topic": topic,
                "messages": messages,
                "field_evidence_indices": evidence,
            },
        )
        if len(transcript.messages) != len(messages):
            raise ValueError(
                f"{fixture_path}:{line_number} ({sample_id}): one or more messages were rejected"
            )
        if evidence:
            transcript.meta["field_evidence_indices"] = evidence
        samples.append(transcript)

    if not samples:
        raise ValueError(f"{fixture_path}: fixture contains no samples")
    return samples


def _top_indices(weights: np.ndarray, k: int) -> List[int]:
    if weights.size == 0 or k <= 0:
        return []
    k = min(int(k), int(weights.size))
    order = list(np.argsort(-weights.astype(np.float64)))
    return [int(i) for i in order[:k]]


def evidence_localization_metrics(
    samples: Sequence[PlazaTranscript],
    attention_matrices: Sequence[np.ndarray],
    *,
    field_names: Sequence[str] = FIELD_NAMES,
    k_mode: str = "adaptive",
    fixed_ks: Sequence[int] = (1, 3),
) -> Dict[str, Any]:
    """Hit@1, Recall@k, micro/macro P/R/F1 for field evidence localization.

    Parameters
    ----------
    samples : transcripts with meta['field_evidence_indices']
    attention_matrices : list of (n_fields, n_utterances) weight matrices
    k_mode : 'adaptive' uses k=max(1, |gold|) per field instance
    fixed_ks : also report fixed-k metrics (default 1 and 3)
    """
    if len(samples) != len(attention_matrices):
        raise ValueError("samples and attention_matrices length mismatch")
    if not samples:
        raise ValueError("samples must not be empty")

    names = tuple(field_names)
    # micro counters for adaptive k
    tp = fp = fn = 0
    hit1_hits = 0
    hit1_total = 0
    recall_at = {int(k): {"num": 0.0, "den": 0.0} for k in fixed_ks}
    per_field = {
        f: {"tp": 0, "fp": 0, "fn": 0, "hit1_hits": 0, "hit1_total": 0} for f in names
    }

    labeled = 0
    for sample, attn in zip(samples, attention_matrices):
        gold_map = (sample.meta or {}).get("field_evidence_indices") or {}
        if not gold_map:
            raise ValueError(
                f"sample {sample.discussion_id} missing field_evidence_indices "
                "(empty labels are rejected for localization metrics)"
            )
        weights = np.asarray(attn, dtype=np.float64)
        if weights.ndim != 2 or weights.shape[0] != len(names):
            raise ValueError(
                f"attention for {sample.discussion_id} must be "
                f"({len(names)}, N); got {weights.shape}"
            )
        n_utt = weights.shape[1]
        if n_utt != len(sample.messages):
            raise ValueError(
                f"attention width {n_utt} != message count {len(sample.messages)} "
                f"for {sample.discussion_id}"
            )
        labeled += 1
        for fi, field in enumerate(names):
            raw_gold = gold_map.get(field)
            if raw_gold is None:
                raise ValueError(
                    f"sample {sample.discussion_id} missing gold for field {field!r}"
                )
            gold = set(int(i) for i in raw_gold)
            if not gold:
                raise ValueError(
                    f"sample {sample.discussion_id} field {field!r} has empty gold set"
                )
            for g in gold:
                if g < 0 or g >= n_utt:
                    raise ValueError(
                        f"sample {sample.discussion_id} field {field!r} gold index {g} OOB"
                    )

            w = weights[fi]
            top1 = int(np.argmax(w))
            hit1_total += 1
            per_field[field]["hit1_total"] += 1
            if top1 in gold:
                hit1_hits += 1
                per_field[field]["hit1_hits"] += 1

            k_adapt = max(1, len(gold))
            pred = set(_top_indices(w, k_adapt))
            tp_i = len(pred & gold)
            fp_i = len(pred - gold)
            fn_i = len(gold - pred)
            tp += tp_i
            fp += fp_i
            fn += fn_i
            per_field[field]["tp"] += tp_i
            per_field[field]["fp"] += fp_i
            per_field[field]["fn"] += fn_i

            for k in fixed_ks:
                pred_k = set(_top_indices(w, int(k)))
                recall_at[int(k)]["num"] += len(pred_k & gold)
                recall_at[int(k)]["den"] += len(gold)

    def _prf(tp_: int, fp_: int, fn_: int) -> Dict[str, float]:
        precision = tp_ / (tp_ + fp_) if (tp_ + fp_) else 0.0
        recall = tp_ / (tp_ + fn_) if (tp_ + fn_) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        return {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "tp": int(tp_),
            "fp": int(fp_),
            "fn": int(fn_),
        }

    micro = _prf(tp, fp, fn)
    field_metrics = {}
    macro_p = macro_r = macro_f = 0.0
    for field in names:
        m = _prf(per_field[field]["tp"], per_field[field]["fp"], per_field[field]["fn"])
        ht = per_field[field]["hit1_total"]
        m["hit_at_1"] = (
            per_field[field]["hit1_hits"] / ht if ht else 0.0
        )
        field_metrics[field] = m
        macro_p += m["precision"]
        macro_r += m["recall"]
        macro_f += m["f1"]
    n_fields = max(1, len(names))
    macro = {
        "precision": float(macro_p / n_fields),
        "recall": float(macro_r / n_fields),
        "f1": float(macro_f / n_fields),
    }

    fixed = {}
    for k, bucket in recall_at.items():
        den = bucket["den"] or 1.0
        fixed[f"recall_at_{k}"] = float(bucket["num"] / den)

    return {
        "sample_count": labeled,
        "k_mode": k_mode,
        "hit_at_1": float(hit1_hits / hit1_total) if hit1_total else 0.0,
        "micro": micro,
        "macro": macro,
        "fields": field_metrics,
        "fixed_k": fixed,
        "adaptive_f1": micro["f1"],
    }


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonnegative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _latency_stats(values: Sequence[float]) -> Dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean_ms": float(np.mean(arr)),
        "std_ms": float(np.std(arr)),
        "p50_ms": float(np.percentile(arr, 50)),
        "p95_ms": float(np.percentile(arr, 95)),
    }


def _run_local_extraction(pipeline: TSEPipeline, transcript: PlazaTranscript) -> Dict[str, Any]:
    t0 = time.perf_counter()
    embeddings, mask = pipeline.encoder.encode_transcript(transcript)
    t1 = time.perf_counter()

    temporal = pipeline.tcn.forward(embeddings, mask)
    t2 = time.perf_counter()

    skill_repr, attention = pipeline.attention.forward(temporal, mask)
    focus_indices = select_skill_moments(
        attention, top_k=pipeline.config.top_k_utterances
    )
    if not focus_indices and transcript.messages:
        focus_indices = list(range(len(transcript.messages)))
    field_focus = field_focus_summary(transcript, attention)
    try:
        head_prediction = pipeline.heads.predict(skill_repr)
        category_hint = str(
            head_prediction.get("category") or heuristic_category_hint(transcript)
        )
        tools_hint = list(head_prediction.get("required_tools") or [])
        if not tools_hint:
            tools_hint = heuristic_tools_hint(transcript)
    except Exception:
        category_hint = heuristic_category_hint(transcript)
        tools_hint = heuristic_tools_hint(transcript)
    t3 = time.perf_counter()

    skills = synthesize_skills_local(
        transcript,
        focus_indices=focus_indices,
        category_hint=category_hint,
        tools_hint=tools_hint,
    )
    t4 = time.perf_counter()

    stages = {
        "stage1_encoder_ms": (t1 - t0) * 1000.0,
        "stage2_tcn_ms": (t2 - t1) * 1000.0,
        "stage3_attention_evidence_ms": (t3 - t2) * 1000.0,
        "stage4_local_synthesis_ms": (t4 - t3) * 1000.0,
    }
    return {
        "total_ms": float(sum(stages.values())),
        "stage_timings_ms": stages,
        "focus_utterance_count": len(focus_indices),
        "skill_count": len(skills),
    }


def benchmark_local_extraction(
    samples: Sequence[PlazaTranscript],
    *,
    runs: int = 10,
    warmups: int = 1,
    config: TSEConfig | None = None,
    pipeline: TSEPipeline | None = None,
    input_sha256: str = "",
) -> Dict[str, Any]:
    """Benchmark deterministic Stage 1-4 local extraction for each transcript."""
    _positive_int(runs, "runs")
    _nonnegative_int(warmups, "warmups")
    if pipeline is not None and config is not None:
        raise ValueError("pass either pipeline or config, not both")
    transcripts = list(samples)
    if not transcripts:
        raise ValueError("samples must not be empty")
    for index, transcript in enumerate(transcripts):
        if not isinstance(transcript, PlazaTranscript):
            raise TypeError(f"sample {index} must be a PlazaTranscript")
        if not transcript.messages:
            raise ValueError(f"sample {index} ({transcript.discussion_id}) is empty")

    active_pipeline = pipeline or TSEPipeline(config or TSEConfig())
    cfg = active_pipeline.config
    sample_reports: list[Dict[str, Any]] = []

    for transcript in transcripts:
        for _ in range(warmups):
            _run_local_extraction(active_pipeline, transcript)

        measurements = []
        for run_number in range(1, runs + 1):
            measurement = _run_local_extraction(active_pipeline, transcript)
            measurement["run"] = run_number
            measurements.append(measurement)

        total_stats = _latency_stats([m["total_ms"] for m in measurements])
        stage_stats: Dict[str, Dict[str, float]] = {}
        for stage in STAGE_KEYS:
            stats = _latency_stats(
                [m["stage_timings_ms"][stage] for m in measurements]
            )
            share = stats["mean_ms"] / total_stats["mean_ms"]
            stats["share"] = float(share)
            stats["share_pct"] = float(share * 100.0)
            stage_stats[stage] = stats

        sample_reports.append(
            {
                "sample_id": transcript.discussion_id,
                "topic": transcript.topic,
                "utterance_count": len(transcript.messages),
                "focus_utterance_count": measurements[-1]["focus_utterance_count"],
                "skill_count": measurements[-1]["skill_count"],
                "runs": runs,
                "warmups": warmups,
                "measurements": measurements,
                "latency_ms": total_stats,
                "stage_timings_ms": stage_stats,
            }
        )

    receptive_field = 1 + (cfg.tcn_kernel_size - 1) * sum(cfg.dilations)
    return {
        "experiment": "9.3_local_extraction_latency",
        "sample_count": len(transcripts),
        "utterance_count": sum(len(sample.messages) for sample in transcripts),
        "runs_per_sample": runs,
        "warmups_per_sample": warmups,
        "input_sha256": input_sha256,
        "tse_config": {
            "kernel_size": cfg.tcn_kernel_size,
            "dilations": list(cfg.dilations),
            "theoretical_receptive_field_utterances": receptive_field,
            "receptive_field_note": (
                "The theoretical span is capped by each sample's input length and boundary padding."
            ),
        },
        "scope_boundary": LOCAL_BENCHMARK_BOUNDARY,
        "samples": sample_reports,
    }


def build_keyword_attention(
    transcript: PlazaTranscript,
    *,
    temperature: float = 0.15,
    config: TSEConfig | None = None,
) -> np.ndarray:
    """Compute field-to-utterance cosine attention in one shared hash space."""
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be a finite positive number")
    if not isinstance(transcript, PlazaTranscript):
        raise TypeError("transcript must be a PlazaTranscript")

    cfg = config or TSEConfig()
    utterance_count = len(transcript.messages)
    if utterance_count == 0:
        return np.zeros((len(FIELD_NAMES), 0), dtype=np.float32)

    hidden_dim = cfg.tcn_hidden_dim
    field_vectors = np.zeros((len(FIELD_NAMES), hidden_dim), dtype=np.float32)
    for field_index, field in enumerate(FIELD_NAMES):
        seed_terms = FIELD_KEYWORD_SEEDS.get(field) or (field,)
        vectors = [
            hash_embed_text(term, hidden_dim, cfg.hash_seed) for term in seed_terms
        ]
        field_vector = np.mean(vectors, axis=0).astype(np.float32)
        norm = float(np.linalg.norm(field_vector))
        if norm > 1e-8:
            field_vector /= norm
        field_vectors[field_index] = field_vector

    utterance_vectors = np.stack(
        [
            hash_embed_text(
                (message.content or "")[: cfg.max_chars_per_utterance],
                hidden_dim,
                cfg.hash_seed,
            )
            for message in transcript.messages
        ],
        axis=0,
    )
    similarities = field_vectors @ utterance_vectors.T
    logits = similarities / temperature
    logits -= np.max(logits, axis=1, keepdims=True)
    exponentials = np.exp(logits)
    return (exponentials / exponentials.sum(axis=1, keepdims=True)).astype(np.float32)


def _single_distribution_metrics(weights: np.ndarray) -> Dict[str, Any]:
    if weights.ndim != 1:
        raise ValueError("attention weights must be one-dimensional")
    if weights.size == 0:
        return {
            "count": 0,
            "range": [None, None],
            "span": 0.0,
            "std": 0.0,
            "normalized_entropy": 0.0,
            "concentration": 0.0,
            "concentration_max_over_mean": 0.0,
        }
    if not np.all(np.isfinite(weights)):
        raise ValueError("attention weights must be finite")
    if np.any(weights < 0):
        raise ValueError("attention weights must be non-negative")
    total = float(np.sum(weights))
    if total <= 0:
        raise ValueError("attention weights must have a positive sum")

    probabilities = weights / total
    positive = probabilities > 0
    entropy = float(-np.sum(probabilities[positive] * np.log(probabilities[positive])))
    normalized_entropy = 1.0 if weights.size == 1 else entropy / math.log(weights.size)
    minimum = float(np.min(weights))
    maximum = float(np.max(weights))
    concentration = maximum / float(np.mean(weights))
    return {
        "count": int(weights.size),
        "range": [minimum, maximum],
        "span": maximum - minimum,
        "std": float(np.std(weights)),
        "normalized_entropy": float(normalized_entropy),
        "concentration": float(concentration),
        "concentration_max_over_mean": float(concentration),
    }


def attention_distribution_metrics(
    attention_weights: Sequence[float] | np.ndarray,
    *,
    field_names: Sequence[str] = FIELD_NAMES,
) -> Dict[str, Any]:
    """Compute range, standard deviation, normalized entropy, and concentration."""
    weights = np.asarray(attention_weights, dtype=np.float64)
    if weights.ndim == 1:
        return _single_distribution_metrics(weights)
    if weights.ndim != 2:
        raise ValueError("attention weights must be one- or two-dimensional")
    names = tuple(field_names)
    if weights.shape[0] != len(names):
        raise ValueError(
            f"field dimension mismatch: got {weights.shape[0]}, expected {len(names)}"
        )
    return {
        field: _single_distribution_metrics(weights[index])
        for index, field in enumerate(names)
    }


def _load_checkpoint_strict(
    checkpoint: str | Path,
    pipeline: TSEPipeline,
    *,
    expected_epoch: int,
) -> tuple[Dict[str, Any], str]:
    from .checkpoint import apply_state, collect_state

    checkpoint_path = Path(checkpoint)
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"checkpoint not found: {checkpoint_path}")
    expected_state = collect_state(pipeline, pipeline.heads)
    try:
        with np.load(checkpoint_path, allow_pickle=False) as archive:
            state = {key: archive[key] for key in archive.files}
    except Exception as exc:
        raise ValueError(f"invalid checkpoint {checkpoint_path}: {exc}") from exc

    missing = sorted(set(expected_state) - set(state))
    if missing:
        raise ValueError(
            f"checkpoint {checkpoint_path} is missing required tensors: {', '.join(missing[:5])}"
        )
    mismatched = [
        f"{key}: got {state[key].shape}, expected {expected.shape}"
        for key, expected in expected_state.items()
        if state[key].shape != expected.shape
    ]
    if mismatched:
        raise ValueError(
            f"checkpoint {checkpoint_path} has incompatible shapes: {'; '.join(mismatched[:5])}"
        )

    metadata_path = checkpoint_path.with_name(checkpoint_path.stem + ".meta.json")
    if not metadata_path.is_file():
        raise ValueError(f"checkpoint metadata not found: {metadata_path}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        epoch = int(metadata.get("epoch"))
    except Exception as exc:
        raise ValueError(f"checkpoint metadata must contain a valid epoch: {metadata_path}") from exc
    if epoch != expected_epoch:
        raise ValueError(
            f"checkpoint epoch must be {expected_epoch}, got {epoch}: {checkpoint_path}"
        )

    apply_state(pipeline, state, pipeline.heads)
    return metadata, sha256_file(checkpoint_path)


def compare_attention_baseline(
    samples: Sequence[PlazaTranscript],
    *,
    checkpoint: str | Path,
    temperature: float = 0.15,
    config: TSEConfig | None = None,
    expected_epoch: int = 30,
    input_sha256: str = "",
) -> Dict[str, Any]:
    """Compare strict-checkpoint query attention with the keyword diagnostic."""
    if not checkpoint:
        raise ValueError("checkpoint is required")
    transcripts = list(samples)
    if not transcripts:
        raise ValueError("samples must not be empty")
    cfg = config or TSEConfig()
    for index, transcript in enumerate(transcripts):
        if not isinstance(transcript, PlazaTranscript):
            raise TypeError(f"sample {index} must be a PlazaTranscript")
        if not transcript.messages:
            raise ValueError(f"sample {index} ({transcript.discussion_id}) is empty")
        if len(transcript.messages) > cfg.max_utterances:
            raise ValueError(
                f"sample {index} ({transcript.discussion_id}) exceeds max_utterances"
            )

    pipeline = TSEPipeline(cfg)
    checkpoint_metadata, checkpoint_sha256 = _load_checkpoint_strict(
        checkpoint, pipeline, expected_epoch=expected_epoch
    )

    trained_attention: list[np.ndarray] = []
    keyword_attention: list[np.ndarray] = []
    per_sample: list[Dict[str, Any]] = []
    for transcript in transcripts:
        trained = pipeline.encode_stages(transcript)["attn_weights"]
        keyword = build_keyword_attention(
            transcript, temperature=temperature, config=cfg
        )
        trained_attention.append(trained)
        keyword_attention.append(keyword)
        per_sample.append(
            {
                "sample_id": transcript.discussion_id,
                "topic": transcript.topic,
                "utterance_count": len(transcript.messages),
                "trained_attention": trained.tolist(),
                "keyword_attention": keyword.tolist(),
            }
        )

    trained_all = np.concatenate(trained_attention, axis=1)
    keyword_all = np.concatenate(keyword_attention, axis=1)
    trained_metrics = attention_distribution_metrics(trained_all)
    keyword_metrics = attention_distribution_metrics(keyword_all)
    fields: Dict[str, Any] = {}
    for field in FIELD_NAMES:
        trained = trained_metrics[field]
        keyword = keyword_metrics[field]
        fields[field] = {
            "trained": trained,
            "keyword": keyword,
            "trained_minus_keyword": {
                metric: float(trained[metric] - keyword[metric])
                for metric in ("span", "std", "normalized_entropy", "concentration")
            },
        }

    # Evidence localization (Hit@1 / Recall@k / F1) when gold labels present
    evidence_metrics: Dict[str, Any] = {"available": False}
    if all((t.meta or {}).get("field_evidence_indices") for t in transcripts):
        evidence_metrics = {
            "available": True,
            "trained": evidence_localization_metrics(transcripts, trained_attention),
            "keyword": evidence_localization_metrics(transcripts, keyword_attention),
            "note": (
                "Predictions use top-k per field with k=max(1, |gold|) plus fixed k=1/3; "
                "keyword baseline is diagnostic, not human ground truth."
            ),
        }

    checkpoint_path = Path(checkpoint)
    return {
        "experiment": "9.4_attention_keyword_diagnostic",
        "sample_count": len(transcripts),
        "utterance_count": sum(len(sample.messages) for sample in transcripts),
        "temperature": float(temperature),
        "input_sha256": input_sha256,
        "algorithm_version": KEYWORD_ATTENTION_ALGORITHM_VERSION,
        "algorithm_note": (
            "FIELD_KEYWORD_SEEDS and utterance text are embedded with the same hash_seed "
            "coordinate space; values are not expected to reproduce the legacy mismatched-seed range."
        ),
        "checkpoint": {
            "path": str(checkpoint_path.resolve()),
            "sha256": checkpoint_sha256,
            "epoch": expected_epoch,
            "metadata": checkpoint_metadata,
        },
        "interpretation_boundary": ATTENTION_DIAGNOSTIC_BOUNDARY,
        "fields": fields,
        "evidence_metrics": evidence_metrics,
        "samples": per_sample,
    }
