from __future__ import annotations

import pytest
from fastapi import HTTPException

from agents import cost_gate_routes


class _FakeReport:
    report_id = "report-1"
    is_blocked = False
    critical_count = 0
    high_count = 0

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "decision": "pass",
            "project_id": "project-a",
        }


class _FakeGate:
    def __init__(self):
        self.last_plan = None
        self.last_project_id = None
        self.last_budget = None
        self.last_metadata = None

    def get_status(self):
        return {
            "name": "cost_gate",
            "version": "1.0",
            "policies": {"resource_types_count": 3},
            "stats": {"total_evaluations": 2},
            "uptime_seconds": 12.5,
        }

    def get_stats(self):
        return {"total_evaluations": 2, "blocked": 1}

    def evaluate_plan(self, plan, *, project_id, budget, metadata):
        self.last_plan = plan
        self.last_project_id = project_id
        self.last_budget = budget
        self.last_metadata = metadata
        return _FakeReport()


@pytest.mark.asyncio
async def test_cost_gate_health_combines_token_and_terraform(monkeypatch):
    monkeypatch.setattr(cost_gate_routes, "_token_gate_stats", lambda: {"evaluations": 4})
    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", lambda: _FakeGate())

    payload = await cost_gate_routes.cost_gate_health()

    assert payload["status"] == "healthy"
    assert payload["default_semantics"] == "token"
    assert payload["token"] == {
        "status": "healthy",
        "engine": "token_budget",
        "token_stats": {"evaluations": 4},
    }
    assert payload["terraform"]["status"] == "healthy"
    assert payload["terraform"]["policies_count"] == 3


@pytest.mark.asyncio
async def test_cost_gate_stats_combines_token_and_terraform(monkeypatch):
    monkeypatch.setattr(cost_gate_routes, "_token_gate_stats", lambda: {"evaluations": 4})
    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", lambda: _FakeGate())

    payload = await cost_gate_routes.get_stats()

    assert payload == {
        "default_semantics": "token",
        "token": {"evaluations": 4},
        "terraform": {"total_evaluations": 2, "blocked": 1},
    }


@pytest.mark.asyncio
async def test_cost_gate_health_uses_unavailable_terraform_fallback(monkeypatch):
    monkeypatch.setattr(cost_gate_routes, "_token_gate_stats", lambda: {})

    def unavailable_gate():
        raise RuntimeError("terraform unavailable")

    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", unavailable_gate)

    payload = await cost_gate_routes.cost_gate_health()

    assert payload["token"] == {"status": "healthy", "engine": "token_budget"}
    assert payload["terraform"] == {
        "status": "unavailable",
        "reason": "terraform unavailable",
    }


@pytest.mark.asyncio
async def test_evaluate_terraform_plan_parses_json_and_attaches_evidence(monkeypatch):
    gate = _FakeGate()
    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", lambda: gate)

    async def fake_record_evidence(report, request, result):
        return "evidence-1"

    monkeypatch.setattr(cost_gate_routes, "_record_cost_gate_evidence", fake_record_evidence)

    payload = await cost_gate_routes.evaluate_terraform_plan(
        cost_gate_routes.TerraformPlanEvaluationRequest(
            plan_json='{"resource_changes": []}',
            project_id="project-a",
            budget={"monthly_budget_usd": 100},
            metadata={"task_id": "task-1"},
        )
    )

    assert gate.last_plan == {"resource_changes": []}
    assert gate.last_project_id == "project-a"
    assert gate.last_budget.monthly_budget_usd == 100
    assert gate.last_metadata == {"task_id": "task-1"}
    assert payload["evidence_run_id"] == "evidence-1"


@pytest.mark.asyncio
async def test_evaluate_terraform_plan_rejects_missing_plan(monkeypatch):
    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", lambda: _FakeGate())

    with pytest.raises(HTTPException) as exc_info:
        await cost_gate_routes.evaluate_terraform_plan(
            cost_gate_routes.TerraformPlanEvaluationRequest()
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Either 'plan' or 'plan_json' is required"


@pytest.mark.asyncio
async def test_evaluate_terraform_plan_rejects_invalid_plan_json(monkeypatch):
    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", lambda: _FakeGate())

    with pytest.raises(HTTPException) as exc_info:
        await cost_gate_routes.evaluate_terraform_plan(
            cost_gate_routes.TerraformPlanEvaluationRequest(plan_json="{bad")
        )

    assert exc_info.value.status_code == 422
    assert str(exc_info.value.detail).startswith("Invalid JSON in plan_json:")
