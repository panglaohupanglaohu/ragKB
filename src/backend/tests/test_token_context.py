# -*- coding: utf-8 -*-
"""Regression tests for token attribution context helpers."""

from __future__ import annotations

import re

from agents.token_context import get_token_ctx, new_run_id, token_scope


def test_new_run_id_uses_prefix_and_short_uuid_suffix():
    run_id = new_run_id("skill_verify")

    assert re.fullmatch(r"skill_verify_[0-9a-f]{12}", run_id)


def test_token_scope_sets_context_and_restores_parent():
    assert get_token_ctx() == {}

    with token_scope(run_id="outer", phase="plaza", team_id="team-1"):
        assert get_token_ctx() == {
            "run_id": "outer",
            "phase": "plaza",
            "team_id": "team-1",
        }

        with token_scope(phase="extract", skill_id="skill-1"):
            assert get_token_ctx() == {
                "run_id": "outer",
                "phase": "extract",
                "team_id": "team-1",
                "skill_id": "skill-1",
            }

        assert get_token_ctx() == {
            "run_id": "outer",
            "phase": "plaza",
            "team_id": "team-1",
        }

    assert get_token_ctx() == {}


def test_token_scope_none_values_do_not_overwrite_parent_values():
    with token_scope(run_id="run-1", phase="drill", team_id="team-1"):
        with token_scope(run_id=None, team_id=None, agent_id="agent-1"):
            assert get_token_ctx() == {
                "run_id": "run-1",
                "phase": "drill",
                "team_id": "team-1",
                "agent_id": "agent-1",
            }


def test_get_token_ctx_returns_copy():
    with token_scope(run_id="run-1"):
        snapshot = get_token_ctx()
        snapshot["run_id"] = "mutated"

        assert get_token_ctx()["run_id"] == "run-1"
