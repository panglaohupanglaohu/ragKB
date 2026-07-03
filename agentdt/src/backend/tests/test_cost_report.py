# -*- coding: utf-8 -*-
"""Regression tests for cost report aggregation."""

from __future__ import annotations

from types import SimpleNamespace

from agents import cost_report


class _FakeLedger:
    def by_phase(self, window, team_id=None):
        if team_id:
            return {"task": {"total": 30}}
        return {"task": {"total": 30}, "plaza": {"total": 20}}

    def by_team(self, window, include_unattributed=False):
        if include_unattributed:
            return [
                {"team_id": "team-1", "total": 30},
                {"team_id": "", "total": 20},
            ]
        return [{"team_id": "team-1", "total": 30}]

    def by_skill(self, window):
        return [{"skill_id": "skill-1", "total": 12}]

    def lever_split(self, team_id, window):
        return {"team_id": team_id, "window": window}


class _FakeTargetStore:
    def list_targets(self):
        return [SimpleNamespace(id="target-1")]

    def get_progress(self, target_id):
        return {"id": target_id, "progress": 0.5}


class _FakeRatchetLedger:
    def list_metrics(self, prefix):
        return [{"metric": f"{prefix}team-1", "value": 0.9}]


def test_generate_cost_report_reconciles_unattributed_tokens(monkeypatch, tmp_path):
    from agents import token_ledger, cost_targets, ratchet_ledger

    monkeypatch.setattr(token_ledger, "LEDGER", _FakeLedger())
    monkeypatch.setattr(cost_targets, "get_target_store", lambda: _FakeTargetStore())
    monkeypatch.setattr(ratchet_ledger, "get_ratchet_ledger", lambda: _FakeRatchetLedger())
    monkeypatch.setattr(cost_report, "_REPORTS_DIR", tmp_path)

    report = cost_report.generate_cost_report(window="24h")

    assert report["window"] == "24h"
    assert report["team"] == ""
    assert report["totals"]["total_tokens"] == 50
    assert report["unattributed_tokens"] == 20
    assert report["reconciliation"] == {
        "phase_sum": 50,
        "team_sum": 50,
        "unattributed": 20,
        "consistent": True,
    }
    assert report["by_team"] == [{"team_id": "team-1", "total": 30}]
    assert report["by_skill"] == [{"skill_id": "skill-1", "total": 12}]
    assert report["targets"] == [{"id": "target-1", "progress": 0.5}]
    assert report["ratchet_locked"] == [{"metric": "cost_efficiency:team-1", "value": 0.9}]
    assert list(tmp_path.glob("*.json"))


def test_generate_cost_report_filters_team_scope(monkeypatch, tmp_path):
    from agents import token_ledger, cost_targets, ratchet_ledger

    monkeypatch.setattr(token_ledger, "LEDGER", _FakeLedger())
    monkeypatch.setattr(cost_targets, "get_target_store", lambda: _FakeTargetStore())
    monkeypatch.setattr(ratchet_ledger, "get_ratchet_ledger", lambda: _FakeRatchetLedger())
    monkeypatch.setattr(cost_report, "_REPORTS_DIR", tmp_path)

    report = cost_report.generate_cost_report(window="7d", team="team-1")

    assert report["team"] == "team-1"
    assert report["totals"]["total_tokens"] == 30
    assert report["unattributed_tokens"] == 0
    assert report["reconciliation"]["phase_sum"] == 30
    assert report["reconciliation"]["team_sum"] == 30
