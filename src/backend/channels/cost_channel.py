# -*- coding: utf-8 -*-
"""Cost Monitoring Channel — MarineChannel for OpenCost integration.

Monitors cost data from OpenCost, tracks budget thresholds, and emits
alerts when costs exceed configured limits.

Inherits from MarineChannel base class.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .marine_base import (
    ChannelPriority,
    ChannelStatus,
    MarineChannel,
)

logger = logging.getLogger(__name__)


class CostMonitoringChannel(MarineChannel):
    """Marine channel for real-time cost monitoring via OpenCost.

    Priority: P1 (continuous monitoring, not critical path)
    Status: OK when OpenCost is reachable, WARN on threshold breach, ERROR on disconnect

    Features:
      - Polls cost data from CostAggregator
      - Tracks budget thresholds per team/environment
      - Emits alerts on threshold breach
      - Provides cost health status for dashboard
    """

    def __init__(
        self,
        name: str = "cost_monitoring",
        description: str = "OpenCost real-time cost monitoring channel",
        budget_thresholds: Optional[Dict[str, float]] = None,
        alert_threshold_pct: float = 80.0,
    ):
        super().__init__(name=name, description=description)
        self._priority = ChannelPriority.P1
        self._status = ChannelStatus.OK
        self._budget_thresholds: Dict[str, float] = budget_thresholds or {
            "default": 1000.0,  # USD/month
            "production": 2000.0,
            "staging": 500.0,
            "development": 300.0,
        }
        self._alert_threshold_pct = alert_threshold_pct
        self._active_alerts: List[Dict[str, Any]] = []
        self._last_check: Optional[str] = None
        self._cost_summary: Dict[str, Any] = {}

    # ── MarineChannel Interface ──────────────────────────

    def get_priority(self) -> ChannelPriority:
        return self._priority

    def get_status(self) -> ChannelStatus:
        return self._status

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a cost monitoring event.

        Event types:
          - "check": Run a cost health check
          - "set_threshold": Update a budget threshold
          - "get_alerts": Return active alerts
          - "reset": Reset all alerts
        """
        event_type = event.get("type", "check")

        if event_type == "check":
            return await self._run_health_check()
        elif event_type == "set_threshold":
            return self._set_threshold(event)
        elif event_type == "get_alerts":
            return self._get_alerts()
        elif event_type == "reset":
            return self._reset_alerts()
        else:
            return {"status": "unknown_event", "type": event_type}

    # ── Health Check ─────────────────────────────────────

    async def _run_health_check(self) -> Dict[str, Any]:
        """Run a cost health check against current data."""
        try:
            from agents.cost_aggregator import get_cost_aggregator
            agg = get_cost_aggregator()

            if not agg.opencost_healthy and agg.cache_age_seconds > 1800:
                self._status = ChannelStatus.ERROR
                return {
                    "status": "error",
                    "message": "OpenCost unreachable, cache stale > 30min",
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }

            # Get summary
            from agents.cost_models import CostQueryParams
            summary = await agg.get_summary(CostQueryParams(window="30d"))

            self._cost_summary = {
                "total_cost": summary.total_cost,
                "service_count": summary.service_count,
                "pod_count": summary.pod_count,
                "top_services": [
                    {"name": s.value, "cost": s.total_cost, "pct": s.percentage}
                    for s in summary.by_service[:5]
                ],
            }

            # Check budget thresholds
            self._active_alerts = []
            for env_item in summary.by_environment:
                env_name = env_item.value
                threshold = self._budget_thresholds.get(
                    env_name, self._budget_thresholds["default"]
                )
                monthly_est = env_item.total_cost  # 30-day cost
                pct = (monthly_est / threshold * 100) if threshold > 0 else 0

                if pct >= self._alert_threshold_pct:
                    alert = {
                        "type": "budget_threshold",
                        "environment": env_name,
                        "current_cost": round(monthly_est, 2),
                        "threshold": threshold,
                        "percentage": round(pct, 1),
                        "severity": "critical" if pct >= 95 else "warning",
                        "raised_at": datetime.now(timezone.utc).isoformat(),
                    }
                    self._active_alerts.append(alert)

            self._last_check = datetime.now(timezone.utc).isoformat()

            if self._active_alerts:
                self._status = ChannelStatus.WARN
            else:
                self._status = ChannelStatus.OK

            return {
                "status": self._status.value,
                "checked_at": self._last_check,
                "summary": self._cost_summary,
                "alerts": len(self._active_alerts),
                "budget_status": "over_budget" if self._active_alerts else "within_budget",
            }

        except Exception as exc:
            logger.error("Cost health check failed: %s", exc, exc_info=True)
            self._status = ChannelStatus.ERROR
            return {
                "status": "error",
                "message": str(exc),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }

    # ── Alert Management ─────────────────────────────────

    def _set_threshold(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Update a budget threshold."""
        env = event.get("environment", "default")
        amount = float(event.get("amount", 0))
        self._budget_thresholds[env] = amount
        logger.info("Budget threshold updated: %s = $%.2f", env, amount)
        return {"status": "ok", "environment": env, "threshold": amount}

    def _get_alerts(self) -> Dict[str, Any]:
        """Get active alerts."""
        return {
            "count": len(self._active_alerts),
            "alerts": self._active_alerts,
            "checked_at": self._last_check,
        }

    def _reset_alerts(self) -> Dict[str, Any]:
        """Reset all active alerts."""
        count = len(self._active_alerts)
        self._active_alerts = []
        self._status = ChannelStatus.OK
        return {"status": "ok", "cleared": count}

    # ── Additional API ───────────────────────────────────

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status for external consumers."""
        return {
            "channel": self.name,
            "priority": self._priority.value,
            "status": self._status.value,
            "alerts_count": len(self._active_alerts),
            "alerts": self._active_alerts,
            "last_check": self._last_check,
            "budget_thresholds": dict(self._budget_thresholds),
        }
