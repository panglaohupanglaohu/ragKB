# -*- coding: utf-8 -*-
"""Tests for the productized paper experiments 9.3 and 9.4."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from agents.tse.checkpoint import collect_state, save_checkpoint
from agents.tse.config import FIELD_KEYWORD_SEEDS, FIELD_NAMES, TSEConfig
from agents.tse.encoder import hash_embed_text
from agents.tse.experiments import (
    KEYWORD_ATTENTION_ALGORITHM_VERSION,
    STAGE_KEYS,
    attention_distribution_metrics,
    benchmark_local_extraction,
    build_keyword_attention,
    compare_attention_baseline,
    load_experiment_samples,
    sha256_file,
)
from agents.tse.pipeline import TSEPipeline
from agents.tse.transcript import PlazaTranscript


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = ROOT / "src" / "backend" / "agents" / "tse" / "fixtures"
LATENCY_FIXTURE = FIXTURE_DIR / "latency_9_3.jsonl"
ATTENTION_FIXTURE = FIXTURE_DIR / "attention_9_4.jsonl"
CLI = ROOT / "scripts" / "run_tse_paper_experiments.py"


def _tiny_config() -> TSEConfig:
    return TSEConfig(embed_dim=16, tcn_hidden_dim=16, num_heads=4)


def test_paper_fixtures_have_required_sample_and_utterance_counts() -> None:
    latency = load_experiment_samples(LATENCY_FIXTURE)
    attention = load_experiment_samples(ATTENTION_FIXTURE)

    assert len(latency) == 5
    assert [sample.topic for sample in latency] == [
        "ES Instances Scaling",
        "CentOS-Rocky Migration",
        "Resource Cost Governance",
        "Monitoring Rollback",
        "Terraform Change Gate",
    ]
    assert [len(sample.messages) for sample in latency] == [5] * 5
    assert len(attention) == 12
    assert [len(sample.messages) for sample in attention] == [5, 4, 5, 4, 5, 4, 5, 4, 4, 4, 4, 5]
    assert sum(len(sample.messages) for sample in attention) == 53
    assert sha256_file(ATTENTION_FIXTURE) == __import__("hashlib").sha256(
        ATTENTION_FIXTURE.read_bytes()
    ).hexdigest()


def test_fixture_loader_reports_duplicate_ids_and_empty_content(tmp_path: Path) -> None:
    duplicate = {
        "sample_id": "same",
        "topic": "topic",
        "messages": [{"content": "valid"}],
    }
    duplicate_path = tmp_path / "duplicate.jsonl"
    duplicate_path.write_text(
        json.dumps(duplicate) + "\n" + json.dumps(duplicate) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate sample_id"):
        load_experiment_samples(duplicate_path)

    empty_path = tmp_path / "empty-message.jsonl"
    empty_path.write_text(
        json.dumps(
            {"sample_id": "empty", "topic": "topic", "messages": [{"content": ""}]}
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="message 0 content is required"):
        load_experiment_samples(empty_path)


def test_keyword_attention_uses_shared_hash_space_and_normalizes() -> None:
    transcript = load_experiment_samples(ATTENTION_FIXTURE)[0]
    config = _tiny_config()
    attention = build_keyword_attention(transcript, temperature=0.15, config=config)

    assert attention.shape == (len(FIELD_NAMES), len(transcript.messages))
    assert np.all(np.isfinite(attention))
    assert np.all(attention >= 0)
    np.testing.assert_allclose(attention.sum(axis=1), np.ones(len(FIELD_NAMES)), atol=1e-6)

    field = "tools"
    field_vector = np.mean(
        [
            hash_embed_text(term, config.tcn_hidden_dim, config.hash_seed)
            for term in FIELD_KEYWORD_SEEDS[field]
        ],
        axis=0,
    )
    field_vector /= np.linalg.norm(field_vector)
    utterance_vectors = np.stack(
        [
            hash_embed_text(message.content, config.tcn_hidden_dim, config.hash_seed)
            for message in transcript.messages
        ]
    )
    logits = field_vector @ utterance_vectors.T / 0.15
    logits -= logits.max()
    expected = np.exp(logits) / np.exp(logits).sum()
    np.testing.assert_allclose(attention[FIELD_NAMES.index(field)], expected, atol=1e-6)


def test_keyword_attention_validates_temperature_and_empty_transcript() -> None:
    empty = PlazaTranscript(discussion_id="empty", topic="empty")
    assert build_keyword_attention(empty).shape == (len(FIELD_NAMES), 0)
    for temperature in (0.0, -0.1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite positive"):
            build_keyword_attention(empty, temperature=temperature)


def test_attention_distribution_metrics_cover_boundaries() -> None:
    uniform = attention_distribution_metrics(np.full(4, 0.25))
    focused = attention_distribution_metrics(np.array([0.97, 0.01, 0.01, 0.01]))
    singleton = attention_distribution_metrics(np.array([1.0]))
    empty = attention_distribution_metrics(np.array([]))

    assert uniform["normalized_entropy"] == pytest.approx(1.0)
    assert uniform["concentration"] == pytest.approx(1.0)
    assert focused["normalized_entropy"] < uniform["normalized_entropy"]
    assert focused["concentration"] > uniform["concentration"]
    assert singleton["normalized_entropy"] == pytest.approx(1.0)
    assert singleton["concentration"] == pytest.approx(1.0)
    assert empty == {
        "count": 0,
        "range": [None, None],
        "span": 0.0,
        "std": 0.0,
        "normalized_entropy": 0.0,
        "concentration": 0.0,
        "concentration_max_over_mean": 0.0,
    }
    with pytest.raises(ValueError, match="field dimension mismatch"):
        attention_distribution_metrics(np.ones((2, 3)))
    with pytest.raises(ValueError, match="non-negative"):
        attention_distribution_metrics(np.array([1.0, -0.1]))


def test_local_benchmark_covers_local_synthesis_and_stage_statistics() -> None:
    transcript = load_experiment_samples(LATENCY_FIXTURE)[0]
    report = benchmark_local_extraction(
        [transcript], runs=2, warmups=1, config=_tiny_config(), input_sha256="fixture-hash"
    )

    assert report["runs_per_sample"] == 2
    assert report["warmups_per_sample"] == 1
    assert report["input_sha256"] == "fixture-hash"
    assert report["tse_config"]["theoretical_receptive_field_utterances"] == 15
    sample = report["samples"][0]
    assert len(sample["measurements"]) == 2
    assert sample["focus_utterance_count"] > 0
    assert sample["skill_count"] > 0
    assert set(sample["stage_timings_ms"]) == set(STAGE_KEYS)
    assert sum(stage["share"] for stage in sample["stage_timings_ms"].values()) == pytest.approx(1.0)
    for measurement in sample["measurements"]:
        assert set(measurement["stage_timings_ms"]) == set(STAGE_KEYS)
        assert measurement["stage_timings_ms"]["stage4_local_synthesis_ms"] > 0
        assert measurement["total_ms"] == pytest.approx(
            sum(measurement["stage_timings_ms"].values())
        )


def test_attention_comparison_requires_epoch_30_checkpoint(tmp_path: Path) -> None:
    config = _tiny_config()
    pipeline = TSEPipeline(config)
    checkpoint = tmp_path / "epoch30.npz"
    save_checkpoint(checkpoint, pipeline, pipeline.heads, meta={"epoch": 30})
    sample = load_experiment_samples(ATTENTION_FIXTURE)[0]

    report = compare_attention_baseline(
        [sample],
        checkpoint=checkpoint,
        config=config,
        temperature=0.15,
        input_sha256="attention-hash",
    )
    assert report["sample_count"] == 1
    assert report["utterance_count"] == 5
    assert report["input_sha256"] == "attention-hash"
    assert report["algorithm_version"] == KEYWORD_ATTENTION_ALGORITHM_VERSION
    assert report["checkpoint"]["epoch"] == 30
    assert set(report["fields"]) == set(FIELD_NAMES)

    with pytest.raises(FileNotFoundError, match="checkpoint not found"):
        compare_attention_baseline([sample], checkpoint=tmp_path / "missing.npz", config=config)

    epoch29 = tmp_path / "epoch29.npz"
    save_checkpoint(epoch29, pipeline, pipeline.heads, meta={"epoch": 29})
    with pytest.raises(ValueError, match="epoch must be 30"):
        compare_attention_baseline([sample], checkpoint=epoch29, config=config)


def test_attention_comparison_rejects_checkpoint_shape_mismatch(tmp_path: Path) -> None:
    config = _tiny_config()
    pipeline = TSEPipeline(config)
    state = collect_state(pipeline, pipeline.heads)
    state["att.query_vectors"] = state["att.query_vectors"][:-1]
    checkpoint = tmp_path / "bad-shape.npz"
    np.savez_compressed(checkpoint, **state)
    checkpoint.with_name("bad-shape.meta.json").write_text(
        json.dumps({"epoch": 30}), encoding="utf-8"
    )

    sample = load_experiment_samples(ATTENTION_FIXTURE)[0]
    with pytest.raises(ValueError, match="incompatible shapes"):
        compare_attention_baseline([sample], checkpoint=checkpoint, config=config)


def test_attention_cli_requires_checkpoint_and_writes_complete_report(tmp_path: Path) -> None:
    missing = subprocess.run(
        [sys.executable, str(CLI), "attention"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing.returncode != 0
    assert "--checkpoint" in missing.stderr

    pipeline = TSEPipeline(TSEConfig())
    checkpoint = tmp_path / "epoch30.npz"
    save_checkpoint(checkpoint, pipeline, pipeline.heads, meta={"epoch": 30})
    output = tmp_path / "attention-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "attention",
            "--checkpoint",
            str(checkpoint),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema_version"] == "tse-paper-experiments/v1"
    assert report["input"]["sample_count"] == 12
    assert report["input"]["utterance_count"] == 53
    assert report["input"]["sha256"] == sha256_file(ATTENTION_FIXTURE)
    assert report["result"]["algorithm_version"] == KEYWORD_ATTENTION_ALGORITHM_VERSION
    assert report["result"]["checkpoint"]["epoch"] == 30
    env = report["environment"]
    assert env["python"]
    assert env["numpy"]
    assert env["platform"]
    assert "processor" in env
    assert "tse_config" in env
    assert env.get("temperature") == pytest.approx(0.15)
    assert "Report:" in completed.stdout


def test_latency_cli_smoke_writes_environment_and_stage_timings(tmp_path: Path) -> None:
    output = tmp_path / "latency-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "latency",
            "--runs",
            "2",
            "--warmups",
            "1",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["command"] == "latency"
    assert report["environment"]["runs"] == 2
    assert report["environment"]["warmups"] == 1
    assert report["environment"]["python"]
    assert report["environment"]["numpy"]
    assert report["input"]["sample_count"] == 5
    assert report["input"]["utterance_count"] == 25
    assert report["input"]["sha256"] == sha256_file(LATENCY_FIXTURE)
    result = report["result"]
    assert result["sample_count"] == 5
    assert result["runs_per_sample"] == 2
    for sample in result["samples"]:
        for measurement in sample["measurements"]:
            stages = measurement["stage_timings_ms"]
            assert set(stages) == set(STAGE_KEYS)
            assert all(stages[key] > 0 for key in STAGE_KEYS)
    assert "Report:" in completed.stdout
    assert "9.3 complete" in completed.stdout
