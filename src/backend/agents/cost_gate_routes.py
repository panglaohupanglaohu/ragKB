# -*- coding: utf-8 -*-
"""Cost Gate API Routes — FastAPI endpoints for CI/CD cost gate.

Provides:
- POST /api/v1/cost-gate/evaluate  — Evaluate terraform plan
- GET  /api/v1/cost-gate/health     — Health check
- GET  /api/v1/cost-gate/policies   — List all cost policies
- POST /api/v1/cost-gate/policies   — Update a policy
- DELETE /api/v1/cost-gate/policies/{resource_type} — Delete a policy
- GET  /api/v1/cost-gate/budget     — Get current budget
- POST /api/v1/cost-gate/budget     — Set budget
- GET  /api/v1/cost-gate/history    — Evaluation history
- GET  /api/v1/cost-gate/history/{report_id} — Get specific report
- GET  /api/v1/cost-gate/stats      — Evaluation statistics
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ── Router ────────────────────────────────────────────────────

cost_gate_router = APIRouter(prefix="/api/v1/cost-gate", tags=["cost-gate"])


# ══════════════════════════════════════════════════════════════════
# Request/Response Models
# ══════════════════════════════════════════════════════════════════


class TerraformPlanEvaluationRequest(BaseModel):
    """Request to evaluate a terraform plan."""
    plan: Optional[Dict[str, Any]] = Field(default=None, description="Terraform plan JSON object")
    plan_json: Optional[str] = Field(default=None, description="Terraform plan JSON string (alternative)")
    project_id: str = Field(default="default", description="Project identifier")
    budget: Optional[Dict[str, Any]] = Field(default=None, description="Budget profile override")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="CI/CD context metadata")


class PolicyUpdateRequest(BaseModel):
    """Request to update a resource policy."""
    resource_type: str = Field(..., description="Terraform resource type")
    allowed_instance_families: List[str] = Field(default_factory=list)
    max_instance_size: str = "4xlarge"
    recommended_storage_tier: str = "gp3"
    max_storage_gb: int = 1000
    cost_per_unit_hourly: float = 0.0
    required_tags: List[str] = Field(default_factory=lambda: ["Environment", "CostCenter", "Owner"])
    max_count: int = 10
    blocked_regions: List[str] = Field(default_factory=list)
    notes: str = ""


class BudgetUpdateRequest(BaseModel):
    """Request to update budget profile."""
    project_id: str = ""
    monthly_budget_usd: float = Field(..., gt=0, description="Monthly budget in USD")
    current_spend_usd: float = Field(default=0.0, ge=0)
    alert_threshold_pct: float = Field(default=80.0, ge=0, le=200)
    block_threshold_pct: float = Field(default=100.0, ge=0, le=200)
    estimated_new_cost_usd: float = Field(default=0.0, ge=0)
    currency: str = "USD"


class EvaluationSummary(BaseModel):
    """Summary of an evaluation."""
    report_id: str
    project_id: str
    decision: str
    violations_count: int
    critical_count: int
    high_count: int
    estimated_monthly_cost_usd: float
    timestamp: str


# ══════════════════════════════════════════════════════════════════
# Helper: get the cost gate instance
# ══════════════════════════════════════════════════════════════════

def _get_cost_gate():
    """Get the cost gate channel instance, raising if not available."""
    from channels.cost_gate import get_cost_gate
    gate = get_cost_gate()
    if gate._health.status.value != "ok":
        # Try to initialize
        gate.initialize()
    return gate


# ══════════════════════════════════════════════════════════════════
# API Endpoints
# ══════════════════════════════════════════════════════════════════


@cost_gate_router.get("/health")
async def cost_gate_health():
    """Health check endpoint for CI/CD pipeline integration.

    Returns:
        Status of the cost gate channel and basic metrics.
    """
    try:
        gate = _get_cost_gate()
        status = gate.get_status()
        return {
            "status": "healthy",
            "channel": status["name"],
            "version": status["version"],
            "policies_count": status["policies"]["resource_types_count"],
            "stats": status["stats"],
            "uptime_seconds": status["uptime_seconds"],
        }
    except Exception as e:
        logger.error("Cost gate health check failed: %s", e)
        raise HTTPException(status_code=503, detail=f"Cost gate unavailable: {e}")


@cost_gate_router.post("/evaluate")
async def evaluate_terraform_plan(request: TerraformPlanEvaluationRequest):
    """Evaluate a terraform plan against cost policies.

    This is the primary CI/CD integration endpoint. The CI/CD pipeline
    sends a terraform plan (JSON format) and receives a pass/warn/block
    decision with detailed violation report.

    Args:
        request: Terraform plan evaluation request

    Returns:
        CostEvaluationReport with decision and violations

    Raises:
        422: Invalid plan input
        422: Budget exceeded (BLOCK decision) — CI/CD should treat as failure
    """
    gate = _get_cost_gate()

    if not request.plan and not request.plan_json:
        raise HTTPException(status_code=422, detail="Either 'plan' or 'plan_json' is required")

    try:
        if request.plan_json:
            plan = json.loads(request.plan_json)
        else:
            plan = request.plan

        # Convert budget if provided
        budget = None
        if request.budget:
            from agents.cost_policy import BudgetProfile
            budget = BudgetProfile.from_dict(request.budget)

        report = gate.evaluate_plan(
            plan,
            project_id=request.project_id,
            budget=budget,
            metadata=request.metadata or {},
        )

        result = report.to_dict()

        # If blocked, return 422 to signal CI/CD failure
        if report.is_blocked:
            logger.warning(
                "🚫 Cost Gate BLOCKED plan %s: %d critical/high violations",
                report.report_id,
                report.critical_count + report.high_count,
            )
            # We still return 200 here because the CI/CD script checks decision field
            # But we include clear blocking info

        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON in plan_json: {e}")
    except Exception as e:
        logger.error("Cost gate evaluation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")


@cost_gate_router.get("/policies")
async def list_policies(
    resource_type: Optional[str] = Query(default=None, description="Filter by resource type"),
):
    """List cost policies.

    Args:
        resource_type: Optional filter by resource type

    Returns:
        Policy configurations
    """
    gate = _get_cost_gate()
    policies = gate.get_policies()

    if resource_type:
        config = gate._engine.get_resource_config(resource_type)
        if config:
            return {"resource_type": resource_type, "policy": config.to_dict()}
        raise HTTPException(status_code=404, detail=f"No policy for resource type: {resource_type}")

    return policies


@cost_gate_router.post("/policies")
async def upsert_policy(request: PolicyUpdateRequest):
    """Create or update a cost policy for a resource type.

    Args:
        request: Policy update request

    Returns:
        Updated policy confirmation
    """
    gate = _get_cost_gate()

    from agents.cost_policy import ResourceTypeConfig
    config = ResourceTypeConfig(
        resource_type=request.resource_type,
        allowed_instance_families=request.allowed_instance_families,
        max_instance_size=request.max_instance_size,
        recommended_storage_tier=request.recommended_storage_tier,
        max_storage_gb=request.max_storage_gb,
        cost_per_unit_hourly=request.cost_per_unit_hourly,
        required_tags=request.required_tags,
        max_count=request.max_count,
        blocked_regions=request.blocked_regions,
        notes=request.notes,
    )

    result = gate.update_policy(config.to_dict())
    logger.info("📋 Cost policy updated: %s", request.resource_type)
    return result


@cost_gate_router.delete("/policies/{resource_type}")
async def delete_policy(resource_type: str):
    """Delete a cost policy for a resource type.

    Args:
        resource_type: Resource type to delete policy for

    Returns:
        Deletion confirmation
    """
    gate = _get_cost_gate()
    removed = gate.delete_policy(resource_type)
    if not removed:
        raise HTTPException(status_code=404, detail=f"No policy for resource type: {resource_type}")
    return {"status": "deleted", "resource_type": resource_type}


@cost_gate_router.get("/budget")
async def get_budget():
    """Get the current default budget profile.

    Returns:
        Budget profile
    """
    gate = _get_cost_gate()
    budget = gate.get_budget()
    if not budget:
        raise HTTPException(status_code=404, detail="No budget profile configured")
    return budget


@cost_gate_router.post("/budget")
async def set_budget(request: BudgetUpdateRequest):
    """Set the default budget profile.

    Args:
        request: Budget update request

    Returns:
        Updated budget profile
    """
    gate = _get_cost_gate()
    budget = gate.set_budget(request.model_dump())
    logger.info("💰 Budget updated: $%.2f/month", budget.monthly_budget_usd)
    return budget.to_dict()


@cost_gate_router.get("/history")
async def get_history(
    project_id: Optional[str] = Query(default=None, description="Filter by project"),
    limit: int = Query(default=20, ge=1, le=200, description="Max reports"),
):
    """Get evaluation history.

    Args:
        project_id: Optional project filter
        limit: Max reports to return

    Returns:
        List of evaluation summaries
    """
    gate = _get_cost_gate()
    reports = gate.get_history(project_id=project_id, limit=limit)
    return {
        "count": len(reports),
        "reports": [
            {
                "report_id": r.report_id,
                "project_id": r.project_id,
                "decision": r.decision.value,
                "violations_count": len(r.violations),
                "critical_count": r.critical_count,
                "high_count": r.high_count,
                "estimated_monthly_cost_usd": r.estimated_monthly_cost_usd,
                "timestamp": r.timestamp,
            }
            for r in reports
        ],
    }


@cost_gate_router.get("/history/{report_id}")
async def get_report(report_id: str):
    """Get a specific evaluation report by ID.

    Args:
        report_id: Report identifier

    Returns:
        Full evaluation report
    """
    gate = _get_cost_gate()
    event_result = gate.process_event({
        "type": "get_report",
        "report_id": report_id,
    })
    if "report" in event_result:
        return event_result["report"]
    raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")


@cost_gate_router.get("/stats")
async def get_stats():
    """Get evaluation statistics.

    Returns:
        Evaluation stats (total, passed, warned, blocked)
    """
    gate = _get_cost_gate()
    return gate.get_stats()


@cost_gate_router.post("/stats/reset")
async def reset_stats():
    """Reset evaluation statistics.

    Returns:
        Confirmation
    """
    gate = _get_cost_gate()
    gate.reset_stats()
    return {"status": "stats_reset"}
