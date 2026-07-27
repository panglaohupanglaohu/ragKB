# -*- coding: utf-8 -*-
"""Tests for field evidence localization metrics and labeled fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from agents.tse.config import FIELD_NAMES
from agents.tse.experiments import (
    evidence_localization_metrics,
    load_experiment_samples,
    validate_field_evidence_indices,
)
from agents.tse.transcript import PlazaTranscript, Utterance


ROOT = Path(__file__).resolve().parents[3]
ATTENTION_FIXTURE = ROOT / "src" / "backend" / "agents" / "tse" / "fixtures" / "attention_9_4.jsonl"


def _utt(i: int) -> Utterance:
    return Utterance(
        msg_id=str(i),
        speaker_id=f"s{i}",
        speaker_name=f"S{i}",
        role="dev",
        niche_role="",
        ritual_signal="supplement",
        round_number=i,
        content=f"content {i}",
    )


def _sample(n: int, gold: dict) -> PlazaTranscript:
    tr = PlazaTranscript(
        discussion_id="t1",
        topic="t",
        messages=[_utt(i) for i in range(n)],
        meta={"field_evidence_indices": gold},
    )
    return tr


def test_attention_fixture_is_12_by_53_with_evidence_labels() -> None:
    samples = load_experiment_samples(ATTENTION_FIXTURE)
    assert len(samples) == 12
    assert sum(len(s.messages) for s in samples) == 53
    for s in samples:
        gold = s.meta.get("field_evidence_indices") or {}
        assert set(gold) == set(FIELD_NAMES)
        for field, idxs in gold.items():
            for i in idxs:
                assert 0 <= int(i) < len(s.messages)


def test_evidence_perfect_hit() -> None:
    gold = {f: [0] for f in FIELD_NAMES}
    sample = _sample(3, gold)
    # perfect: each field peaks at gold index 0
    attn = np.zeros((len(FIELD_NAMES), 3), dtype=np.float32)
    attn[:, 0] = 1.0
    m = evidence_localization_metrics([sample], [attn])
    assert m["hit_at_1"] == pytest.approx(1.0)
    assert m["micro"]["f1"] == pytest.approx(1.0)
    assert m["macro"]["f1"] == pytest.approx(1.0)


def test_evidence_total_miss() -> None:
    gold = {f: [0] for f in FIELD_NAMES}
    sample = _sample(3, gold)
    attn = np.zeros((len(FIELD_NAMES), 3), dtype=np.float32)
    attn[:, 2] = 1.0
    m = evidence_localization_metrics([sample], [attn])
    assert m["hit_at_1"] == pytest.approx(0.0)
    assert m["micro"]["f1"] == pytest.approx(0.0)


def test_evidence_multilabel_adaptive_k() -> None:
    gold = {f: [0, 2] for f in FIELD_NAMES}
    sample = _sample(4, gold)
    attn = np.zeros((len(FIELD_NAMES), 4), dtype=np.float32)
    # top-2 = gold
    attn[:, 0] = 0.5
    attn[:, 2] = 0.4
    attn[:, 1] = 0.1
    m = evidence_localization_metrics([sample], [attn])
    assert m["micro"]["recall"] == pytest.approx(1.0)
    assert m["fixed_k"]["recall_at_1"] == pytest.approx(0.5)  # only one of two golds in top1
    assert m["fixed_k"]["recall_at_3"] == pytest.approx(1.0)


def test_empty_labels_rejected() -> None:
    sample = _sample(2, {})
    attn = np.ones((len(FIELD_NAMES), 2), dtype=np.float32)
    with pytest.raises(ValueError, match="missing field_evidence_indices"):
        evidence_localization_metrics([sample], [attn])


def test_oob_indices_rejected_in_loader(tmp_path: Path) -> None:
    row = {
        "sample_id": "bad",
        "topic": "t",
        "messages": [{"content": "a"}, {"content": "b"}],
        "field_evidence_indices": {
            **{f: [0] for f in FIELD_NAMES},
            "name": [5],
        },
    }
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="out of range"):
        load_experiment_samples(path)


def test_validate_field_evidence_requires_all_fields_when_partial() -> None:
    with pytest.raises(ValueError, match="missing fields"):
        validate_field_evidence_indices(
            {"name": [0]}, n_messages=2, sample_id="x"
        )
