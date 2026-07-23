# -*- coding: utf-8 -*-
"""Tests for plaza Fist-to-Five consensus (ORID 决策层)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from agents.plaza_consensus import (
    FistToFiveVote,
    collect_fist_to_five,
    format_fist_to_five_summary,
    generate_blocking_resolution_prompt,
)


def _vote(agent_id: str, fingers: int, reason: str = "") -> FistToFiveVote:
    return FistToFiveVote(agent_id=agent_id, agent_name=agent_id, fingers=fingers, reason=reason)


class TestCollectFistToFive:
    def test_strong_consensus(self):
        votes = [_vote("a1", 5), _vote("a2", 4), _vote("a3", 4)]
        result = collect_fist_to_five(votes)
        assert result.consensus_reached is True
        assert result.consensus_level == "strong"
        assert result.blocking_agents == []
        assert result.mean_fingers > 4.0

    def test_weak_consensus(self):
        votes = [_vote("a1", 3), _vote("a2", 3), _vote("a3", 4)]
        result = collect_fist_to_five(votes)
        assert result.consensus_reached is True
        assert result.consensus_level == "weak"

    def test_blocking_vote_prevents_consensus(self):
        votes = [_vote("a1", 5), _vote("a2", 4), _vote("a3", 1, "无法接受成本")]
        result = collect_fist_to_five(votes)
        assert result.consensus_reached is False
        assert result.consensus_level == "blocked"
        assert "a3" in result.blocking_agents

    def test_no_majority_accept(self):
        votes = [_vote("a1", 2), _vote("a2", 2), _vote("a3", 3)]
        result = collect_fist_to_five(votes)
        assert result.consensus_reached is False

    def test_empty_votes(self):
        result = collect_fist_to_five([])
        assert result.consensus_reached is False
        assert result.votes == []

    def test_median_computed(self):
        votes = [_vote("a1", 1), _vote("a2", 3), _vote("a3", 5)]
        result = collect_fist_to_five(votes)
        assert result.median_fingers == 3


class TestFormatting:
    def test_summary_contains_blocking_warning(self):
        votes = [_vote("a1", 4), _vote("a2", 1, "反对")]
        result = collect_fist_to_five(votes)
        summary = format_fist_to_five_summary(result)
        assert "根本性反对" in summary
        assert "a2" in summary

    def test_summary_empty(self):
        assert format_fist_to_five_summary(collect_fist_to_five([])) == "无投票记录"

    def test_blocking_resolution_prompt(self):
        prompt = generate_blocking_resolution_prompt(["a2"], "方案摘要文本")
        assert "a2" in prompt
        assert "方案摘要文本" in prompt


class TestVoteFlags:
    def test_is_blocking(self):
        assert _vote("a", 1).is_blocking is True
        assert _vote("a", 2).is_blocking is False

    def test_is_supportive(self):
        assert _vote("a", 4).is_supportive is True
        assert _vote("a", 3).is_supportive is False

    def test_is_accepting(self):
        assert _vote("a", 3).is_accepting is True
        assert _vote("a", 2).is_accepting is False

