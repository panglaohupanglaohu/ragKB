# -*- coding: utf-8 -*-
"""Tests for plaza consensus measurement."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from agents.plaza_consensus import measure_consensus, highlight_dissent, ConsensusResult


def _msg(agent_id: str, content: str, round_number: int = 1) -> dict:
    return {"agent_id": agent_id, "agent_name": agent_id, "content": content, "round_number": round_number}


class TestMeasureConsensus:
    def test_all_agreement(self):
        msgs = [
            _msg("a1", "我同意这个方案，确实可行"),
            _msg("a2", "赞同，我也认为这是正确方向"),
            _msg("a3", "支持这个提议，好主意"),
        ]
        result = measure_consensus(msgs)
        assert result.score > 0.8
        assert result.agreement_count == 3
        assert result.disagreement_count == 0
        assert result.can_early_exit is True

    def test_all_disagreement(self):
        msgs = [
            _msg("a1", "我不同意，存在很大风险，需要注意问题"),
            _msg("a2", "反对这个方案，不可行，有担忧"),
            _msg("a3", "但是然而我有顾虑，不太合适"),
        ]
        result = measure_consensus(msgs)
        assert result.score < 0.3
        assert result.disagreement_count == 3
        assert result.can_early_exit is False
        assert len(result.dissenting_agents) == 3

    def test_mixed_opinions(self):
        msgs = [
            _msg("a1", "同意这个方向"),
            _msg("a2", "不同意，风险太大，反对"),
            _msg("a3", "这是一个有趣的想法"),  # neutral
        ]
        result = measure_consensus(msgs)
        assert 0.3 < result.score < 0.8
        assert result.can_early_exit is False

    def test_empty_messages(self):
        result = measure_consensus([])
        assert result.score == 0.5
        assert result.can_early_exit is False

    def test_round_filter(self):
        msgs = [
            _msg("a1", "同意", round_number=1),
            _msg("a2", "不同意，反对", round_number=2),
        ]
        r1 = measure_consensus(msgs, round_number=1)
        assert r1.agreement_count == 1
        assert r1.disagreement_count == 0

        r2 = measure_consensus(msgs, round_number=2)
        assert r2.agreement_count == 0
        assert r2.disagreement_count == 1

    def test_convergence_trend_rising(self):
        msgs = [
            _msg("a1", "不同意，反对这个方案", round_number=1),
            _msg("a2", "有顾虑和风险", round_number=1),
            _msg("a1", "同意，支持这个改进方案", round_number=2),
            _msg("a2", "赞同，确实可行", round_number=2),
        ]
        result = measure_consensus(msgs, round_number=2)
        assert result.convergence_trend == "rising"


class TestHighlightDissent:
    def test_detects_strong_dissent(self):
        msgs = [
            _msg("a1", "同意这个方案"),
            _msg("a2", "不同意，反对，有风险，存在问题"),  # strong dissent
        ]
        dissents = highlight_dissent(msgs)
        assert len(dissents) == 1
        assert dissents[0]["agent_id"] == "a2"

    def test_ignores_mild_disagreement(self):
        msgs = [
            _msg("a1", "但是我觉得可以"),  # only 1 disagree keyword
        ]
        dissents = highlight_dissent(msgs)
        assert len(dissents) == 0

    def test_round_filter(self):
        msgs = [
            _msg("a1", "不同意，反对，风险大，有问题", round_number=1),
            _msg("a2", "不同意，反对，不可行，担忧", round_number=2),
        ]
        dissents = highlight_dissent(msgs, round_number=2)
        assert len(dissents) == 1
        assert dissents[0]["agent_id"] == "a2"
