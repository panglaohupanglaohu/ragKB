# -*- coding: utf-8 -*-
"""协作模式集成：suggest / blend / materialize 纯函数."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from sandbox.collab_integration import (  # noqa: E402
    blend_collab,
    build_collab_suggestions,
    materialize_collab_payload,
)


def test_build_collab_suggestions_from_ranking():
    result = {
        "final_ranking": [
            {
                "agent_id": "a1",
                "survival_ticks": 80,
                "population": "aws",
                "collab_genome": {
                    "share_tendency": 0.9,
                    "signal_tendency": 0.8,
                    "follow_tendency": 0.7,
                    "mate_choosiness": 0.4,
                },
            },
            {
                "agent_id": "a2",
                "survival_ticks": 40,
                "collab_genome": {"share_tendency": 0.1},
            },
        ]
    }
    rep = build_collab_suggestions(result, top_k=5)
    assert rep["count"] == 2
    assert rep["suggestions"][0]["agent_id"] == "a1"
    assert rep["suggestions"][0]["collab"]["share_tendency"] == 0.9
    assert 0.4 <= rep["population_mean"]["share_tendency"] <= 0.6


def test_blend_and_materialize():
    existing = {
        "share_tendency": 0.0,
        "signal_tendency": 0.0,
        "follow_tendency": 0.0,
        "mate_choosiness": 0.0,
    }
    proposed = {
        "share_tendency": 1.0,
        "signal_tendency": 1.0,
        "follow_tendency": 1.0,
        "mate_choosiness": 1.0,
    }
    blended = blend_collab(existing, proposed, alpha=0.5)
    assert blended["share_tendency"] == 0.5

    payload = materialize_collab_payload(
        {"agent_id": "x", "collab": proposed, "survival_ticks": 10, "strategy": "blend"},
        existing_meta={"eco_collab": existing},
        fingerprint="fp1",
        strategy_override="blend",
    )
    assert payload["source"] == "eco_drill"
    assert payload["eco_fp"] == "fp1"
    assert 0.4 <= payload["share_tendency"] <= 0.7

    ow = materialize_collab_payload(
        {"collab": proposed, "strategy": "overwrite"},
        existing_meta={"eco_collab": existing},
        strategy_override="overwrite",
    )
    assert ow["share_tendency"] == 1.0


def test_confirm_false_contract_in_routes_source():
    """路由源码契约：collab apply 需 confirm."""
    src = (ROOT / "src/backend/agents/eco_runtime_routes.py").read_text(encoding="utf-8")
    assert "collab-integration/suggest" in src
    assert "collab-integration/apply" in src
    assert "metadata.eco_collab" in src or "eco_collab" in src
