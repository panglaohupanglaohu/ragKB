from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .models import BudgetEvent, TokenBudget, UsageRecord
from .store import UsageStore, get_usage_store


_SETTINGS_PATH = Path(__file__).resolve().parents[4] / "config" / "settings.json"
_budget_guard: Optional["BudgetGuard"] = None


class BudgetExceededError(RuntimeError):
    pass


@dataclass
class BudgetCheckResult:
    allowed: bool = True
    events: List[BudgetEvent] = field(default_factory=list)


def _load_settings_budget() -> TokenBudget:
    try:
        with _SETTINGS_PATH.open("r", encoding="utf-8") as handle:
            settings = json.load(handle)
    except Exception:
        settings = {}
    raw = settings.get("budget", {})
    return TokenBudget(
        per_session_max=int(os.getenv("AG_BUDGET_SESSION_MAX", raw.get("per_session_max", 200_000))),
        per_agent_daily_max=int(os.getenv("AG_BUDGET_AGENT_DAILY_MAX", raw.get("per_agent_daily_max", 2_000_000))),
        per_team_daily_max=int(os.getenv("AG_BUDGET_TEAM_DAILY_MAX", raw.get("per_team_daily_max", 10_000_000))),
        on_exceed=os.getenv("AG_BUDGET_ON_EXCEED", raw.get("on_exceed", "halt")),
        alert_threshold=float(os.getenv("AG_BUDGET_ALERT_THRESHOLD", raw.get("alert_threshold", 0.8))),
    )


def save_budget_settings(budget: TokenBudget) -> TokenBudget:
    try:
        with _SETTINGS_PATH.open("r", encoding="utf-8") as handle:
            settings = json.load(handle)
    except Exception:
        settings = {}
    settings["budget"] = budget.to_dict()
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, ensure_ascii=False, indent=2)
    return budget


@dataclass(frozen=True)
class _UsageTotals:
    session: int
    agent: int
    team: int


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _read_usage_totals(
    store: UsageStore,
    *,
    session_id: str,
    agent_id: str,
    team_id: str,
    today: str,
) -> _UsageTotals:
    return _UsageTotals(
        session=store.get_session_total(session_id),
        agent=store.get_agent_daily_total(agent_id, today),
        team=store.get_team_daily_total(team_id, today),
    )


def _record_events(store: UsageStore, events: List[BudgetEvent]) -> None:
    for event in events:
        store.record_event(event)


def _has_halt_event(events: List[BudgetEvent]) -> bool:
    return any(event.level == "halt" for event in events)


class BudgetGuard:
    def __init__(self, budget: TokenBudget, store: Optional[UsageStore] = None) -> None:
        self.budget = budget
        self.store = store or get_usage_store()

    def update_budget(self, budget: TokenBudget) -> None:
        self.budget = budget

    def check(
        self,
        *,
        session_id: str,
        agent_id: str,
        team_id: str,
        estimated_tokens: int,
    ) -> BudgetCheckResult:
        events: List[BudgetEvent] = []
        totals = _read_usage_totals(
            self.store,
            session_id=session_id,
            agent_id=agent_id,
            team_id=team_id,
            today=_utc_today(),
        )

        self._check_limit(
            events,
            scope="session",
            scope_id=session_id,
            current_total=totals.session,
            incoming=estimated_tokens,
            limit=self.budget.per_session_max,
        )
        self._check_limit(
            events,
            scope="agent",
            scope_id=agent_id,
            current_total=totals.agent,
            incoming=estimated_tokens,
            limit=self.budget.per_agent_daily_max,
        )
        self._check_limit(
            events,
            scope="team",
            scope_id=team_id,
            current_total=totals.team,
            incoming=estimated_tokens,
            limit=self.budget.per_team_daily_max,
        )

        _record_events(self.store, events)
        return BudgetCheckResult(allowed=not _has_halt_event(events), events=events)

    def record_usage(self, record: UsageRecord) -> None:
        self.store.record_usage(record)

    def alerts(self) -> Dict[str, object]:
        return {
            "budget": self.budget.to_dict(),
            "events": self.store.recent_events(limit=100),
        }

    def _check_limit(
        self,
        events: List[BudgetEvent],
        *,
        scope: str,
        scope_id: str,
        current_total: int,
        incoming: int,
        limit: int,
    ) -> None:
        if not scope_id or limit <= 0:
            return
        projected = current_total + incoming
        if projected > limit:
            level = "halt" if self.budget.on_exceed == "halt" else "warn"
            events.append(
                BudgetEvent(
                    scope=scope,
                    scope_id=scope_id,
                    level=level,
                    value=projected,
                    limit=limit,
                    message=f"{scope} token budget exceeded: {projected} > {limit}",
                )
            )
            return
        threshold = int(limit * self.budget.alert_threshold)
        if threshold and projected >= threshold:
            events.append(
                BudgetEvent(
                    scope=scope,
                    scope_id=scope_id,
                    level="warn",
                    value=projected,
                    limit=limit,
                    message=f"{scope} token budget nearing limit: {projected} / {limit}",
                )
            )


def get_budget_guard() -> BudgetGuard:
    global _budget_guard
    if _budget_guard is None:
        _budget_guard = BudgetGuard(_load_settings_budget())
    return _budget_guard
