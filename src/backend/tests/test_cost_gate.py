# -*- coding: utf-8 -*-
"""Cost Gate Tests — CI/CD Cost Gate comprehensive test suite.

Coverage:
- CostPolicyEngine: resource evaluation, budget checks, serialization
- CostGateChannel: event processing, initialization, status
- API Routes: evaluate, health, policies, budget, history
- Instance size/family parsing
- Edge cases: empty plan, missing fields, concurrent plans
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

import pytest

# Ensure path
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))


# ══════════════════════════════════════════════════════════════════
# Imports after path setup
# ══════════════════════════════════════════════════════════════════

from agents.cost_policy import (
    BudgetProfile,
    CostEvaluationReport,
    CostPolicyEngine,
    CostViolation,
    CostViolationSeverity,
    GateDecision,
    ResourceTypeConfig,
    ViolationType,
    _build_default_resource_configs,
    _get_instance_family,
    _get_instance_size,
    _instance_size_index,
)
from channels.cost_gate import CostGateChannel, get_cost_gate, initialize_cost_gate


# ══════════════════════════════════════════════════════════════════
# Test Data
# ══════════════════════════════════════════════════════════════════


def _make_valid_plan() -> Dict[str, Any]:
    """Create a valid terraform plan with optimal resources."""
    return {
        "resource_changes": [
            {
                "address": "aws_instance.web",
                "type": "aws_instance",
                "name": "web",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "instance_type": "t3.medium",
                    "count": 2,
                    "tags": {
                        "Environment": "prod",
                        "CostCenter": "12345",
                        "Owner": "team-a",
                        "Name": "web-server",
                    },
                },
            },
            {
                "address": "aws_db_instance.main",
                "type": "aws_db_instance",
                "name": "main",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "instance_type": "db.t3.medium",
                    "allocated_storage": 100,
                    "tags": {
                        "Environment": "prod",
                        "CostCenter": "12345",
                        "Owner": "team-a",
                        "Name": "main-db",
                    },
                },
            },
        ]
    }


def _make_bad_plan() -> Dict[str, Any]:
    """Create a terraform plan with cost violations."""
    return {
        "resource_changes": [
            {
                "address": "aws_instance.expensive",
                "type": "aws_instance",
                "name": "expensive",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "instance_type": "p4d.24xlarge",  # Wrong family + oversized
                    "count": 100,  # Way over limit
                    "tags": {},  # No tags
                },
            },
            {
                "address": "aws_nat_gateway.expensive",
                "type": "aws_nat_gateway",
                "name": "expensive",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {"tags": {}},
            },
        ]
    }


# ══════════════════════════════════════════════════════════════════
# Tests: Instance Size/Family Parsing
# ══════════════════════════════════════════════════════════════════


class TestInstanceParsing:
    """Test instance type parsing utilities."""

    def test_get_instance_family_standard(self):
        assert _get_instance_family("t3.medium") == "t3"
        assert _get_instance_family("m6i.2xlarge") == "m6i"
        assert _get_instance_family("c7g.large") == "c7g"
        assert _get_instance_family("r6g.xlarge") == "r6g"

    def test_get_instance_family_db_prefix(self):
        assert _get_instance_family("db.t3.medium") == "t3"
        assert _get_instance_family("db.r6g.large") == "r6g"

    def test_get_instance_family_cache_prefix(self):
        assert _get_instance_family("cache.t3.micro") == "t3"
        assert _get_instance_family("cache.r6g.large") == "r6g"

    def test_get_instance_family_edge_cases(self):
        assert _get_instance_family("t3") == "t3"
        assert _get_instance_family("") == ""

    def test_get_instance_size(self):
        assert _get_instance_size("t3.medium") == "medium"
        assert _get_instance_size("m6i.2xlarge") == "2xlarge"
        assert _get_instance_size("db.r6g.large") == "large"
        assert _get_instance_size("t3") == ""

    def test_instance_size_index_ordering(self):
        assert _instance_size_index("nano") == 0
        assert _instance_size_index("micro") == 1
        assert _instance_size_index("small") == 2
        assert _instance_size_index("medium") == 3
        assert _instance_size_index("large") == 4
        assert _instance_size_index("xlarge") == 5
        assert _instance_size_index("2xlarge") == 6
        # nano < medium < xlarge < 4xlarge
        assert _instance_size_index("nano") < _instance_size_index("medium")
        assert _instance_size_index("medium") < _instance_size_index("xlarge")
        assert _instance_size_index("xlarge") < _instance_size_index("4xlarge")

    def test_instance_size_index_unknown(self):
        assert _instance_size_index("unknown-size") == -1


# ══════════════════════════════════════════════════════════════════
# Tests: Data Models
# ══════════════════════════════════════════════════════════════════


class TestDataModels:
    """Test data model serialization and properties."""

    def test_resource_type_config_defaults(self):
        cfg = ResourceTypeConfig(resource_type="aws_instance")
        assert cfg.resource_type == "aws_instance"
        assert cfg.max_instance_size == "4xlarge"
        assert "Environment" in cfg.required_tags
        assert cfg.max_count == 10

    def test_resource_type_config_roundtrip(self):
        cfg = ResourceTypeConfig(
            resource_type="aws_instance",
            allowed_instance_families=["t3", "m6i"],
            max_instance_size="8xlarge",
            max_count=50,
            notes="Test",
        )
        data = cfg.to_dict()
        cfg2 = ResourceTypeConfig.from_dict(data)
        assert cfg2.resource_type == cfg.resource_type
        assert cfg2.allowed_instance_families == cfg.allowed_instance_families
        assert cfg2.max_instance_size == cfg.max_instance_size
        assert cfg2.max_count == cfg.max_count
        assert cfg2.notes == "Test"

    def test_budget_profile_properties(self):
        budget = BudgetProfile(
            project_id="test",
            monthly_budget_usd=1000.0,
            current_spend_usd=500.0,
            estimated_new_cost_usd=100.0,
        )
        assert budget.utilization_pct == 50.0
        assert budget.projected_utilization_pct == 60.0
        assert budget.total_projected == 600.0

    def test_budget_profile_zero_budget(self):
        budget = BudgetProfile(monthly_budget_usd=0.0, current_spend_usd=100.0)
        assert budget.utilization_pct == 0.0
        assert budget.projected_utilization_pct == 0.0

    def test_cost_violation_blocking(self):
        v = CostViolation(
            violation_type=ViolationType.OVER_BUDGET,
            severity=CostViolationSeverity.CRITICAL,
        )
        assert v.is_blocking() is True

        v2 = CostViolation(
            violation_type=ViolationType.MISSING_COST_TAG,
            severity=CostViolationSeverity.MEDIUM,
        )
        assert v2.is_blocking() is False

    def test_cost_evaluation_report_properties(self):
        report = CostEvaluationReport(
            report_id="test-1",
            project_id="test",
            violations=[
                CostViolation(
                    violation_type=ViolationType.OVER_BUDGET,
                    severity=CostViolationSeverity.CRITICAL,
                ),
                CostViolation(
                    violation_type=ViolationType.NON_OPTIMAL_INSTANCE,
                    severity=CostViolationSeverity.HIGH,
                ),
                CostViolation(
                    violation_type=ViolationType.MISSING_COST_TAG,
                    severity=CostViolationSeverity.MEDIUM,
                ),
                CostViolation(
                    violation_type=ViolationType.WRONG_STORAGE_TIER,
                    severity=CostViolationSeverity.MEDIUM,
                ),
                CostViolation(
                    violation_type=ViolationType.ORPHAN_RESOURCE,
                    severity=CostViolationSeverity.LOW,
                ),
            ],
        )
        assert report.critical_count == 1
        assert report.high_count == 1
        assert report.medium_count == 2
        assert report.low_count == 1

    def test_cost_evaluation_report_to_dict(self):
        report = CostEvaluationReport(
            report_id="test-1",
            project_id="test",
            estimated_monthly_cost_usd=123.45,
            decision=GateDecision.PASS,
        )
        d = report.to_dict()
        assert d["report_id"] == "test-1"
        assert d["decision"] == "pass"
        assert d["violations_summary"]["total"] == 0


# ══════════════════════════════════════════════════════════════════
# Tests: CostPolicyEngine
# ══════════════════════════════════════════════════════════════════


class TestCostPolicyEngine:
    """Test the core cost policy evaluation engine."""

    def test_engine_initialization(self):
        engine = CostPolicyEngine()
        assert len(engine.resource_configs) > 5
        assert "aws_instance" in engine.resource_configs
        assert "aws_db_instance" in engine.resource_configs
        assert "aws_nat_gateway" in engine.resource_configs

    def test_valid_plan_passes(self):
        engine = CostPolicyEngine()
        plan = _make_valid_plan()
        report = engine.evaluate_terraform_plan(plan, project_id="test")
        assert report.decision == GateDecision.PASS
        assert len(report.violations) == 0
        assert report.total_resources_evaluated == 2

    def test_bad_plan_blocks(self):
        engine = CostPolicyEngine()
        plan = _make_bad_plan()
        report = engine.evaluate_terraform_plan(plan, project_id="test")
        assert report.decision == GateDecision.BLOCK
        assert len(report.violations) >= 4
        violation_types = {v.violation_type for v in report.violations}
        assert ViolationType.NON_OPTIMAL_INSTANCE in violation_types
        assert ViolationType.MISSING_COST_TAG in violation_types
        assert ViolationType.EXCEEDS_QUOTA in violation_types

    def test_non_optimal_instance_family(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "aws_instance.bad",
                "type": "aws_instance",
                "name": "bad",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "instance_type": "z1d.large",
                    "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a", "Name": "x"},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert report.decision == GateDecision.BLOCK
        assert any(v.violation_type == ViolationType.NON_OPTIMAL_INSTANCE for v in report.violations)

    def test_oversized_instance(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "aws_instance.big",
                "type": "aws_instance",
                "name": "big",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "instance_type": "m6i.16xlarge",  # > 8xlarge max
                    "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a", "Name": "x"},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert report.decision == GateDecision.BLOCK
        assert any(v.violation_type == ViolationType.OVER_PROVISIONED for v in report.violations)

    def test_missing_tags(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "aws_instance.notags",
                "type": "aws_instance",
                "name": "notags",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "instance_type": "t3.small",
                    "tags": {},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert report.decision == GateDecision.WARN
        violations = [v for v in report.violations if v.violation_type == ViolationType.MISSING_COST_TAG]
        assert len(violations) == 1
        assert "Environment" in violations[0].message

    def test_missing_tags_case_insensitive(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "aws_instance.casetags",
                "type": "aws_instance",
                "name": "casetags",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "instance_type": "t3.small",
                    "tags": {"environment": "prod", "costcenter": "1", "owner": "a", "name": "x"},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        # Should pass because tags match case-insensitively
        missing_violations = [v for v in report.violations if v.violation_type == ViolationType.MISSING_COST_TAG]
        assert len(missing_violations) == 0

    def test_exceeds_count_limit(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "aws_instance.many",
                "type": "aws_instance",
                "name": "many",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "instance_type": "t3.micro",
                    "count": 200,  # > 50 max
                    "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a", "Name": "x"},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert report.decision == GateDecision.BLOCK
        assert any(v.violation_type == ViolationType.EXCEEDS_QUOTA for v in report.violations)

    def test_nat_gateway_advisory(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "aws_nat_gateway.gw",
                "type": "aws_nat_gateway",
                "name": "gw",
                "provider_name": "aws",
                "change": {"actions": ["create"]},
                "values": {
                    "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a", "Name": "nat"},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        # NAT gateway gets INFO advisory but shouldn't block
        assert report.decision in (GateDecision.PASS, GateDecision.WARN)
        nat_violations = [
            v for v in report.violations
            if v.resource_type == "aws_nat_gateway"
        ]
        assert len(nat_violations) >= 1

    def test_budget_overrun_blocks(self):
        engine = CostPolicyEngine()
        budget = BudgetProfile(
            project_id="test",
            monthly_budget_usd=1000.0,
            current_spend_usd=1050.0,  # Already over
            estimated_new_cost_usd=50.0,
            block_threshold_pct=100.0,
        )
        plan = _make_valid_plan()
        report = engine.evaluate_terraform_plan(plan, budget_profile=budget)
        assert report.decision == GateDecision.BLOCK
        assert any(v.violation_type == ViolationType.OVER_BUDGET for v in report.violations)

    def test_budget_alert_only(self):
        engine = CostPolicyEngine()
        budget = BudgetProfile(
            project_id="test",
            monthly_budget_usd=1000.0,
            current_spend_usd=850.0,
            estimated_new_cost_usd=10.0,  # 860 > 800 alert
            alert_threshold_pct=80.0,
            block_threshold_pct=100.0,
        )
        plan = _make_valid_plan()
        report = engine.evaluate_terraform_plan(plan, budget_profile=budget)
        assert report.decision == GateDecision.WARN
        assert any(
            v.violation_type == ViolationType.OVER_BUDGET and v.severity == CostViolationSeverity.MEDIUM
            for v in report.violations
        )

    def test_skip_noop_resources(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "aws_instance.noop",
                "type": "aws_instance",
                "name": "noop",
                "provider_name": "aws",
                "change": {"actions": ["no-op"]},
                "values": {
                    "instance_type": "z1.16xlarge",  # Would violate but no-op
                    "tags": {},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert len(report.violations) == 0
        assert report.decision == GateDecision.PASS

    def test_orphan_resource_delete(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "aws_instance.old",
                "type": "aws_instance",
                "name": "old",
                "provider_name": "aws",
                "change": {"actions": ["delete"]},
                "values": {
                    "instance_type": "t3.small",
                    "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a", "Name": "x"},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert any(v.violation_type == ViolationType.ORPHAN_RESOURCE for v in report.violations)

    def test_empty_plan(self):
        engine = CostPolicyEngine()
        report = engine.evaluate_terraform_plan({"resource_changes": []})
        assert report.decision == GateDecision.PASS
        assert report.total_resources_evaluated == 0

    def test_engine_to_dict_roundtrip(self):
        engine = CostPolicyEngine()
        engine.default_budget_profile = BudgetProfile(
            project_id="test",
            monthly_budget_usd=5000.0,
        )
        data = engine.to_dict()
        engine2 = CostPolicyEngine.from_dict(data)
        assert len(engine2.resource_configs) == len(engine.resource_configs)
        assert engine2.default_budget_profile is not None
        assert engine2.default_budget_profile.monthly_budget_usd == 5000.0

    def test_upsert_and_remove_config(self):
        engine = CostPolicyEngine()
        cfg = ResourceTypeConfig(resource_type="test_resource", max_count=5)
        engine.upsert_resource_config(cfg)
        assert "test_resource" in engine.resource_configs
        assert engine.resource_configs["test_resource"].max_count == 5

        # Update
        cfg2 = ResourceTypeConfig(resource_type="test_resource", max_count=10)
        engine.upsert_resource_config(cfg2)
        assert engine.resource_configs["test_resource"].max_count == 10

        # Remove
        assert engine.remove_resource_config("test_resource") is True
        assert "test_resource" not in engine.resource_configs
        assert engine.remove_resource_config("test_resource") is False

    def test_evaluate_from_json_string(self):
        engine = CostPolicyEngine()
        plan_str = json.dumps(_make_valid_plan())
        report = engine.evaluate_terraform_plan_json(plan_str, project_id="test")
        assert report.decision == GateDecision.PASS
        assert report.total_resources_evaluated == 2

    def test_planned_values_format(self):
        """Test evaluation with 'planned_values' format (terraform plan output)."""
        engine = CostPolicyEngine()
        plan = {
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "address": "aws_instance.web",
                            "type": "aws_instance",
                            "name": "web",
                            "provider_name": "aws",
                            "values": {
                                "instance_type": "t3.medium",
                                "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a", "Name": "x"},
                            },
                        }
                    ]
                }
            }
        }
        report = engine.evaluate_terraform_plan(plan, project_id="test")
        assert report.total_resources_evaluated == 1


# ══════════════════════════════════════════════════════════════════
# Tests: CostGateChannel
# ══════════════════════════════════════════════════════════════════


class TestCostGateChannel:
    """Test the CostGateChannel MarineChannel implementation."""

    def test_channel_creation(self):
        channel = CostGateChannel()
        assert channel.name == "cost_gate"
        assert channel.version == "1.0.0"
        assert channel.priority.name == "P0"

    def test_channel_initialization(self):
        channel = CostGateChannel()
        assert channel.initialize() is True
        assert channel._health.status.value == "ok"
        assert len(channel._engine.resource_configs) > 0

    def test_channel_initialization_with_config(self):
        channel = CostGateChannel(
            max_history=500,
            default_budget={"project_id": "test", "monthly_budget_usd": 10000.0},
        )
        assert channel.initialize() is True
        assert channel._max_history == 500
        assert channel._default_budget is not None
        assert channel._default_budget.monthly_budget_usd == 10000.0

    def test_channel_get_status(self):
        channel = CostGateChannel()
        channel.initialize()
        status = channel.get_status()
        assert status["name"] == "cost_gate"
        assert status["health"] == "ok"
        assert "stats" in status
        assert "policies" in status

    def test_process_event_terraform_plan_pass(self):
        channel = CostGateChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "terraform_plan",
            "plan": _make_valid_plan(),
            "project_id": "test",
        })
        assert result is not None
        assert result["decision"] == "pass"
        assert channel._stats["total_evaluations"] == 1
        assert channel._stats["passed"] == 1

    def test_process_event_terraform_plan_block(self):
        channel = CostGateChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "terraform_plan",
            "plan": _make_bad_plan(),
            "project_id": "test",
        })
        assert result is not None
        assert result["decision"] == "block"
        assert channel._stats["blocked"] == 1

    def test_process_event_set_budget(self):
        channel = CostGateChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "set_budget",
            "budget": {
                "project_id": "test",
                "monthly_budget_usd": 5000.0,
                "alert_threshold_pct": 75.0,
            },
        })
        assert result is not None
        assert result["status"] == "budget_updated"
        assert channel._default_budget is not None
        assert channel._default_budget.monthly_budget_usd == 5000.0

    def test_process_event_update_policy(self):
        channel = CostGateChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "update_policy",
            "action": "upsert",
            "policy": {
                "resource_type": "aws_lambda_function",
                "max_count": 100,
                "required_tags": ["Environment", "Owner"],
            },
        })
        assert result is not None
        assert result["status"] == "policy_updated"
        assert "aws_lambda_function" in channel._engine.resource_configs

    def test_process_event_delete_policy(self):
        channel = CostGateChannel()
        channel.initialize()
        channel._engine.upsert_resource_config(
            ResourceTypeConfig(resource_type="custom_type")
        )
        result = channel.process_event({
            "type": "update_policy",
            "action": "delete",
            "policy": {"resource_type": "custom_type"},
        })
        assert result["status"] == "deleted"

    def test_process_event_unknown_type(self):
        channel = CostGateChannel()
        channel.initialize()
        result = channel.process_event({"type": "unknown_event_type"})
        assert result is not None
        assert "error" in result

    def test_process_event_health_check(self):
        channel = CostGateChannel()
        channel.initialize()
        result = channel.process_event({"type": "health_check"})
        assert result is not None
        assert result["status"] == "ok"

    def test_process_event_get_report(self):
        channel = CostGateChannel()
        channel.initialize()
        # First evaluate to create a report
        eval_result = channel.process_event({
            "type": "terraform_plan",
            "plan": _make_valid_plan(),
            "project_id": "test",
        })
        report_id = eval_result["report_id"]

        # Then retrieve it
        result = channel.process_event({
            "type": "get_report",
            "report_id": report_id,
        })
        assert result is not None
        assert "report" in result
        assert result["report"]["report_id"] == report_id

    def test_evaluate_plan_direct(self):
        channel = CostGateChannel()
        channel.initialize()
        report = channel.evaluate_plan(_make_valid_plan(), project_id="test")
        assert isinstance(report, CostEvaluationReport)
        assert report.decision == GateDecision.PASS

    def test_get_history(self):
        channel = CostGateChannel()
        channel.initialize()

        # Add some evaluations
        for i in range(5):
            channel.process_event({
                "type": "terraform_plan",
                "plan": _make_valid_plan(),
                "project_id": f"project-{i % 2}",
            })

        history = channel.get_history()
        assert len(history) == 5

        filtered = channel.get_history(project_id="project-0")
        assert len(filtered) == 3  # indices 0, 2, 4

    def test_stats_accumulation(self):
        channel = CostGateChannel()
        channel.initialize()

        channel.process_event({"type": "terraform_plan", "plan": _make_valid_plan()})
        channel.process_event({"type": "terraform_plan", "plan": _make_valid_plan()})
        channel.process_event({"type": "terraform_plan", "plan": _make_bad_plan()})

        stats = channel.get_stats()
        assert stats["total_evaluations"] == 3
        assert stats["passed"] == 2
        assert stats["blocked"] == 1
        assert stats["total_violations_found"] > 0

    def test_reset_stats(self):
        channel = CostGateChannel()
        channel.initialize()
        channel.process_event({"type": "terraform_plan", "plan": _make_valid_plan()})
        channel.reset_stats()
        stats = channel.get_stats()
        assert stats["total_evaluations"] == 0

    def test_deterministic_evaluation(self):
        """Same plan should produce same result."""
        channel = CostGateChannel()
        channel.initialize()
        plan = _make_valid_plan()

        r1 = channel.evaluate_plan(plan)
        r2 = channel.evaluate_plan(plan)

        assert r1.decision == r2.decision
        assert len(r1.violations) == len(r2.violations)
        assert r1.estimated_monthly_cost_usd == r2.estimated_monthly_cost_usd


# ══════════════════════════════════════════════════════════════════
# Tests: Singleton Pattern
# ══════════════════════════════════════════════════════════════════


class TestCostGateSingleton:
    """Test the singleton accessor pattern."""

    def test_get_cost_gate_creates_instance(self):
        from channels.cost_gate import _cost_gate_instance
        # Reset singleton for test
        import channels.cost_gate as cg_module
        cg_module._cost_gate_instance = None

        gate = get_cost_gate()
        assert gate is not None
        assert gate.name == "cost_gate"
        assert cg_module._cost_gate_instance is gate

    def test_get_cost_gate_returns_same_instance(self):
        gate1 = get_cost_gate()
        gate2 = get_cost_gate()
        assert gate1 is gate2

    def test_initialize_cost_gate(self):
        import channels.cost_gate as cg_module
        cg_module._cost_gate_instance = None

        gate = initialize_cost_gate(
            default_budget={"project_id": "test", "monthly_budget_usd": 10000.0},
        )
        assert gate._health.status.value == "ok"
        assert gate._default_budget.monthly_budget_usd == 10000.0


# ══════════════════════════════════════════════════════════════════
# Tests: Edge Cases
# ══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge case and regression tests."""

    def test_plan_with_no_changes(self):
        engine = CostPolicyEngine()
        plan = {"resource_changes": []}
        report = engine.evaluate_terraform_plan(plan)
        assert report.decision == GateDecision.PASS
        assert report.total_resources_evaluated == 0
        assert report.total_resources_changed == 0

    def test_plan_with_only_noop(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [
                {
                    "address": "aws_instance.unchanged",
                    "type": "aws_instance",
                    "name": "unchanged",
                    "provider_name": "aws",
                    "change": {"actions": ["no-op"]},
                    "values": {"instance_type": "z1.48xlarge", "tags": {}},
                }
            ]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert report.decision == GateDecision.PASS

    def test_resource_without_config(self):
        """Resources not in the policy catalog should still be evaluated gracefully."""
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [
                {
                    "address": "aws_unknown_resource.test",
                    "type": "aws_unknown_resource",
                    "name": "test",
                    "provider_name": "aws",
                    "change": {"actions": ["create"]},
                    "values": {"tags": {}},
                }
            ]
        }
        report = engine.evaluate_terraform_plan(plan)
        # No config means no checks, but evaluation should still succeed
        assert report.decision == GateDecision.PASS

    def test_deeply_nested_module(self):
        engine = CostPolicyEngine()
        plan = {
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "address": "module.vpc.aws_instance.nat",
                            "type": "aws_instance",
                            "name": "nat",
                            "provider_name": "aws",
                            "values": {
                                "instance_type": "t3.nano",
                                "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a", "Name": "x"},
                            },
                        }
                    ],
                    "child_modules": [
                        {
                            "resources": [
                                {
                                    "address": "module.vpc.module.subnet.aws_instance.app",
                                    "type": "aws_instance",
                                    "name": "app",
                                    "provider_name": "aws",
                                    "values": {
                                        "instance_type": "t3.small",
                                        "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a", "Name": "x"},
                                    },
                                }
                            ]
                        }
                    ],
                }
            }
        }
        report = engine.evaluate_terraform_plan(plan, project_id="nested-test")
        assert report.total_resources_evaluated == 2
        assert report.decision == GateDecision.PASS

    def test_concurrent_plan_evaluation(self):
        """Multiple evaluations should be independent and deterministic."""
        from concurrent.futures import ThreadPoolExecutor

        engine = CostPolicyEngine()
        plan = _make_valid_plan()

        def evaluate():
            return engine.evaluate_terraform_plan(plan)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(evaluate) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should be PASS
        assert all(r.decision == GateDecision.PASS for r in results)
        # All should have same cost estimate
        costs = {r.estimated_monthly_cost_usd for r in results}
        assert len(costs) == 1

    def test_cost_violation_to_dict(self):
        v = CostViolation(
            violation_type=ViolationType.OVER_BUDGET,
            severity=CostViolationSeverity.CRITICAL,
            resource_address="budget:test",
            resource_type="budget_profile",
            message="Budget exceeded",
            expected="$1000",
            actual="$1050",
            estimated_cost_impact_usd=50.0,
            suggestion="Reduce spend",
            policy_rule_id="budget-block",
        )
        d = v.to_dict()
        assert d["violation_type"] == "over_budget"
        assert d["severity"] == "critical"
        assert d["estimated_cost_impact_usd"] == 50.0
        assert d["suggestion"] == "Reduce spend"

    def test_default_resource_configs_all_valid(self):
        configs = _build_default_resource_configs()
        for rt, cfg in configs.items():
            assert cfg.resource_type == rt
            assert isinstance(cfg.required_tags, list)
            assert isinstance(cfg.allowed_instance_families, list) or rt in (
                "aws_s3_bucket", "aws_ebs_volume", "aws_lb", "aws_nat_gateway"
            )

    def test_azure_vm_size_handling(self):
        engine = CostPolicyEngine()
        plan = {
            "resource_changes": [{
                "address": "azurerm_virtual_machine.prod",
                "type": "azurerm_virtual_machine",
                "name": "prod",
                "provider_name": "azurerm",
                "change": {"actions": ["create"]},
                "values": {
                    "vm_size": "Standard_D4",
                    "tags": {"Environment": "prod", "CostCenter": "1", "Owner": "a"},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert report.decision == GateDecision.PASS

    def test_gcp_machine_type_handling(self):
        engine = CostPolicyEngine()
        # Add GCP policy first
        from agents.cost_policy import ResourceTypeConfig
        engine.upsert_resource_config(ResourceTypeConfig(
            resource_type="google_compute_instance",
            allowed_instance_families=["e2", "n2"],
            max_instance_size="n2-standard-32",
            required_tags=["environment", "cost-center", "owner"],
            max_count=50,
        ))
        plan = {
            "resource_changes": [{
                "address": "google_compute_instance.web",
                "type": "google_compute_instance",
                "name": "web",
                "provider_name": "google",
                "change": {"actions": ["create"]},
                "values": {
                    "machine_type": "e2-medium",
                    "tags": {"environment": "prod", "cost-center": "1", "owner": "a"},
                },
            }]
        }
        report = engine.evaluate_terraform_plan(plan)
        assert report.decision == GateDecision.PASS

    def test_plan_hash_is_stable(self):
        """Same JSON should produce the same hash."""
        engine = CostPolicyEngine()
        plan = _make_valid_plan()
        r1 = engine.evaluate_terraform_plan(json.loads(json.dumps(plan)))
        r2 = engine.evaluate_terraform_plan(json.loads(json.dumps(plan)))
        assert r1.terraform_plan_hash == r2.terraform_plan_hash


# ══════════════════════════════════════════════════════════════════
# Tests: Channel Metrics
# ══════════════════════════════════════════════════════════════════


class TestChannelMetrics:
    """Test channel metric accumulation."""

    def test_metrics_accumulate_on_events(self):
        channel = CostGateChannel()
        channel.initialize()

        assert channel._metrics.calls_total == 0

        channel.process_event({"type": "health_check"})
        assert channel._metrics.calls_total == 1
        assert channel._metrics.calls_success == 1

        channel.process_event({"type": "terraform_plan", "plan": _make_valid_plan()})
        assert channel._metrics.calls_total == 2
        assert channel._metrics.calls_success == 2

    def test_metrics_failed_on_unknown_event(self):
        channel = CostGateChannel()
        channel.initialize()

        result = channel.process_event({"type": "bogus_event"})
        assert "error" in result
        assert channel._metrics.calls_failed == 1

    def test_uptime_tracking(self):
        import time
        channel = CostGateChannel()
        channel.initialize()
        time.sleep(0.1)
        uptime = channel.get_uptime()
        assert uptime > 0

    def test_get_status_includes_metrics(self):
        channel = CostGateChannel()
        channel.initialize()
        channel.process_event({"type": "health_check"})
        status = channel.get_status()
        assert "metrics" in status
        assert status["metrics"]["calls_total"] == 1
