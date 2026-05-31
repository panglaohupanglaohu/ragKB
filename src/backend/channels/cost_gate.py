# -*- coding: utf-8 -*-
"""Cost Gate Channel — CI/CD Cost Gate based on Terraform Policy.

Automatically intercepts non-optimal resource configurations and
over-budget deployments in CI/CD pipelines.

Inherits from MarineChannel for unified channel management.
Integrates with SystemEvolutionChannel for audit/dispatch/verify lifecycle.

Features:
- Terraform plan evaluation against cost policies
- Budget threshold enforcement (alert + block)
- Auto-blocking for CRITICAL/HIGH violations
- Audit trail and evolution integration
- ConfigMap-style hot-reload of policies
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from channels.marine_base import (
    ChannelPriority,
    ChannelStatus,
    MarineChannel,
)
from agents.cost_policy import (
    BudgetProfile,
    CostEvaluationReport,
    CostPolicyEngine,
    CostViolation,
    CostViolationSeverity,
    GateDecision,
    ResourceTypeConfig,
    ViolationType,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# Cost Gate Channel
# ══════════════════════════════════════════════════════════════════


class CostGateChannel(MarineChannel):
    """CI/CD Cost Gate Channel.

    Evaluates terraform plans against cost policies and budget constraints.
    Automatically blocks deployments with CRITICAL/HIGH violations.

    Class Attributes:
        name: "cost_gate"
        description: "CI/CD Cost Gate — Terraform Policy-based resource cost evaluation"
        version: "1.0.0"
        priority: P0 (core CI/CD function)
        dependencies: ["system_evolution"] (for audit trail)
    """

    name: str = "cost_gate"
    description: str = "CI/CD Cost Gate — Terraform Policy-based resource cost evaluation"
    version: str = "1.0.0"
    priority: ChannelPriority = ChannelPriority.P0
    dependencies: List[str] = ["system_evolution"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine: CostPolicyEngine = CostPolicyEngine()
        self._evaluation_history: List[CostEvaluationReport] = []
        self._max_history: int = kwargs.get("max_history", 200)
        self._default_budget: Optional[BudgetProfile] = None
        self._stats: Dict[str, int] = {
            "total_evaluations": 0,
            "passed": 0,
            "warned": 0,
            "blocked": 0,
            "total_violations_found": 0,
        }

    # ── MarineChannel Interface ────────────────────────────────

    def initialize(self) -> bool:
        """Initialize the Cost Gate Channel.

        Loads default policies and prepares the evaluation engine.

        Returns:
            True if initialization succeeded.
        """
        try:
            # Apply any configuration from self._config
            if "default_budget" in self._config:
                budget_data = self._config["default_budget"]
                if isinstance(budget_data, BudgetProfile):
                    self._default_budget = budget_data
                elif isinstance(budget_data, dict):
                    self._default_budget = BudgetProfile.from_dict(budget_data)

            if "resource_configs" in self._config:
                for rc_data in self._config["resource_configs"]:
                    config = ResourceTypeConfig.from_dict(rc_data)
                    self._engine.upsert_resource_config(config)

            if "max_history" in self._config:
                self._max_history = self._config["max_history"]

            self._health.status = ChannelStatus.OK
            self._health.message = f"Cost Gate initialized with {len(self._engine.resource_configs)} resource policies"
            logger.info("✅ Cost Gate Channel initialized: %d resource policies", len(self._engine.resource_configs))
            return True

        except Exception as e:
            self._health.status = ChannelStatus.ERROR
            self._health.message = f"Initialization failed: {e}"
            logger.error("❌ Cost Gate initialization failed: %s", e)
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current channel status.

        Returns:
            Status dict with health, stats, and policy summary.
        """
        return {
            "name": self.name,
            "version": self.version,
            "priority": self.priority.name,
            "health": self._health.status.value,
            "health_message": self._health.message,
            "uptime_seconds": self.get_uptime(),
            "stats": self._stats,
            "policies": {
                "resource_types_count": len(self._engine.resource_configs),
                "resource_types": self._engine.get_all_resource_types()[:20],
            },
            "history_count": len(self._evaluation_history),
            "default_budget": self._default_budget.to_dict() if self._default_budget else None,
            "metrics": {
                "calls_total": self._metrics.calls_total,
                "calls_success": self._metrics.calls_success,
                "calls_failed": self._metrics.calls_failed,
                "avg_latency_ms": self._metrics.avg_latency_ms,
            },
        }

    def process_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process an inbound CI/CD pipeline event.

        Expected event types:
        - "terraform_plan": Evaluate a terraform plan
        - "set_budget": Update budget profile
        - "update_policy": Update a resource type policy
        - "get_report": Retrieve a previous evaluation report
        - "health_check": Simple health ping

        Args:
            event: Event dict with at least "type" key.

        Returns:
            Response dict or None if event type is unknown.
        """
        start_time = time.time()
        self._metrics.calls_total += 1
        event_type = event.get("type", "")

        try:
            result: Optional[Dict[str, Any]] = None

            if event_type == "terraform_plan":
                result = self._handle_terraform_plan(event)
            elif event_type == "set_budget":
                result = self._handle_set_budget(event)
            elif event_type == "update_policy":
                result = self._handle_update_policy(event)
            elif event_type == "get_report":
                result = self._handle_get_report(event)
            elif event_type == "health_check":
                result = {"status": "ok", "channel": self.name, "version": self.version}
            else:
                self._metrics.calls_failed += 1
                return {"error": f"Unknown event type: {event_type}", "status": "unknown_event"}

            self._metrics.calls_success += 1
            latency = (time.time() - start_time) * 1000
            self._update_metrics(latency)
            return result

        except Exception as e:
            self._metrics.calls_failed += 1
            latency = (time.time() - start_time) * 1000
            self._update_metrics(latency)
            logger.error("❌ Cost Gate event processing failed: %s", e)
            return {"error": str(e), "status": "error", "event_type": event_type}

    # ── Event Handlers ────────────────────────────────────────

    def _handle_terraform_plan(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a terraform_plan evaluation event.

        event format:
        {
            "type": "terraform_plan",
            "plan": { ... terraform plan JSON ... },
            "plan_json": "...",  # Alternative: JSON string
            "project_id": "...",
            "budget": { ... },    # Optional: override default budget
            "metadata": { ... },  # Optional: CI/CD context
        }
        """
        plan = event.get("plan")
        if plan is None and "plan_json" in event:
            plan = json.loads(event["plan_json"])

        if plan is None:
            return {"error": "Missing 'plan' or 'plan_json' in event", "status": "invalid_input"}

        project_id = event.get("project_id", "default")
        metadata = event.get("metadata", {})

        # Determine budget
        budget = None
        if "budget" in event and event["budget"]:
            budget = BudgetProfile.from_dict(event["budget"])
        elif self._default_budget:
            budget = self._default_budget

        # Evaluate
        report = self._engine.evaluate_terraform_plan(plan, budget_profile=budget, project_id=project_id)
        report.metadata = metadata

        # Update stats
        self._stats["total_evaluations"] += 1
        if report.decision == GateDecision.PASS:
            self._stats["passed"] += 1
        elif report.decision == GateDecision.WARN:
            self._stats["warned"] += 1
        else:
            self._stats["blocked"] += 1
        self._stats["total_violations_found"] += len(report.violations)

        # Store in history
        self._evaluation_history.append(report)
        if len(self._evaluation_history) > self._max_history:
            self._evaluation_history = self._evaluation_history[-self._max_history:]

        logger.info(
            "📊 Cost Gate evaluated plan %s: decision=%s, violations=%d, cost=$%.2f",
            report.report_id, report.decision.value, len(report.violations),
            report.estimated_monthly_cost_usd,
        )

        return report.to_dict()

    def _handle_set_budget(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a set_budget event."""
        budget_data = event.get("budget", {})
        self._default_budget = BudgetProfile.from_dict(budget_data)
        logger.info("💰 Cost Gate budget updated: $%.2f/month", self._default_budget.monthly_budget_usd)
        return {
            "status": "budget_updated",
            "budget": self._default_budget.to_dict(),
        }

    def _handle_update_policy(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an update_policy event."""
        policy_data = event.get("policy", {})
        action = event.get("action", "upsert")

        if action == "delete":
            resource_type = policy_data.get("resource_type", "")
            removed = self._engine.remove_resource_config(resource_type)
            return {"status": "deleted" if removed else "not_found", "resource_type": resource_type}

        config = ResourceTypeConfig.from_dict(policy_data)
        self._engine.upsert_resource_config(config)
        logger.info("📋 Cost Gate policy updated: %s", config.resource_type)
        return {"status": "policy_updated", "resource_type": config.resource_type}

    def _handle_get_report(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a get_report event."""
        report_id = event.get("report_id", "")
        project_id = event.get("project_id", "")

        matches = [
            r for r in self._evaluation_history
            if (report_id and r.report_id == report_id) or
               (project_id and r.project_id == project_id)
        ]

        if report_id and matches:
            return {"report": matches[0].to_dict()}

        return {
            "reports": [r.to_dict() for r in matches[-10:]],  # Last 10
            "count": len(matches),
        }

    # ── Public API Methods ────────────────────────────────────

    def evaluate_plan(
        self,
        plan: Dict[str, Any],
        project_id: str = "",
        budget: Optional[BudgetProfile] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEvaluationReport:
        """Evaluate a terraform plan directly (synchronous API).

        Args:
            plan: Terraform plan dictionary
            project_id: Project identifier
            budget: Optional budget profile override
            metadata: Optional metadata

        Returns:
            CostEvaluationReport
        """
        return self._engine.evaluate_terraform_plan(
            plan,
            budget_profile=budget or self._default_budget,
            project_id=project_id,
        )

    def evaluate_plan_json(
        self,
        plan_json: str,
        project_id: str = "",
        budget: Optional[BudgetProfile] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEvaluationReport:
        """Evaluate a terraform plan from JSON string.

        Args:
            plan_json: Terraform plan JSON string
            project_id: Project identifier
            budget: Optional budget profile
            metadata: Optional metadata

        Returns:
            CostEvaluationReport
        """
        plan = json.loads(plan_json)
        return self.evaluate_plan(plan, project_id, budget, metadata)

    def get_history(
        self,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[CostEvaluationReport]:
        """Get evaluation history, optionally filtered by project.

        Args:
            project_id: Filter by project ID
            limit: Max reports to return

        Returns:
            List of CostEvaluationReport
        """
        if project_id:
            matches = [r for r in self._evaluation_history if r.project_id == project_id]
        else:
            matches = list(self._evaluation_history)
        return matches[-limit:]

    def get_policies(self) -> Dict[str, Any]:
        """Get all current cost policies."""
        return self._engine.to_dict()

    def update_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a single resource policy.

        Args:
            policy_data: ResourceTypeConfig as dict

        Returns:
            Status dict
        """
        config = ResourceTypeConfig.from_dict(policy_data)
        self._engine.upsert_resource_config(config)
        return {"status": "updated", "resource_type": config.resource_type}

    def delete_policy(self, resource_type: str) -> bool:
        """Delete a resource policy.

        Args:
            resource_type: Resource type to remove

        Returns:
            True if deleted
        """
        return self._engine.remove_resource_config(resource_type)

    def set_budget(self, budget_data: Dict[str, Any]) -> BudgetProfile:
        """Update the default budget profile.

        Args:
            budget_data: BudgetProfile as dict

        Returns:
            Updated BudgetProfile
        """
        self._default_budget = BudgetProfile.from_dict(budget_data)
        return self._default_budget

    def get_budget(self) -> Optional[Dict[str, Any]]:
        """Get the current default budget profile."""
        if self._default_budget:
            return self._default_budget.to_dict()
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics."""
        return dict(self._stats)

    def reset_stats(self) -> None:
        """Reset evaluation statistics."""
        self._stats = {
            "total_evaluations": 0,
            "passed": 0,
            "warned": 0,
            "blocked": 0,
            "total_violations_found": 0,
        }

    # ── Helpers ───────────────────────────────────────────────

    def shutdown(self) -> bool:
        """Shutdown the Cost Gate Channel, releasing resources.

        Returns:
            True if shutdown succeeded.
        """
        logger.info("🔻 Cost Gate Channel shutting down")
        self._health.status = ChannelStatus.OFF
        self._health.message = "Channel shut down"
        self._initialized = False
        return True

    def _update_metrics(self, latency_ms: float) -> None:
        """Update channel metrics with a new latency measurement."""
        self._metrics.avg_latency_ms = (
            (self._metrics.avg_latency_ms * (self._metrics.calls_total - 1) + latency_ms)
            / self._metrics.calls_total
        )
        if latency_ms > self._metrics.max_latency_ms:
            self._metrics.max_latency_ms = latency_ms
        if latency_ms < self._metrics.min_latency_ms:
            self._metrics.min_latency_ms = latency_ms


# ══════════════════════════════════════════════════════════════════
# Singleton accessor (for main.py integration)
# ══════════════════════════════════════════════════════════════════

_cost_gate_instance: Optional[CostGateChannel] = None


def get_cost_gate() -> CostGateChannel:
    """Get or create the singleton CostGateChannel instance."""
    global _cost_gate_instance
    if _cost_gate_instance is None:
        _cost_gate_instance = CostGateChannel()
    return _cost_gate_instance


def initialize_cost_gate(**kwargs) -> CostGateChannel:
    """Initialize the singleton CostGateChannel."""
    global _cost_gate_instance
    _cost_gate_instance = CostGateChannel(**kwargs)
    _cost_gate_instance.initialize()
    return _cost_gate_instance
