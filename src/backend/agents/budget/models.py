from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict


@dataclass
class TokenBudget:
    per_session_max: int = 200_000
    per_agent_daily_max: int = 2_000_000
    per_team_daily_max: int = 10_000_000
    on_exceed: str = "halt"  # halt | warn
    alert_threshold: float = 0.8

    def to_dict(self) -> Dict[str, object]:
        return {
            "per_session_max": self.per_session_max,
            "per_agent_daily_max": self.per_agent_daily_max,
            "per_team_daily_max": self.per_team_daily_max,
            "on_exceed": self.on_exceed,
            "alert_threshold": self.alert_threshold,
        }


@dataclass
class UsageRecord:
    session_id: str = ""
    agent_id: str = ""
    team_id: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

    @property
    def date(self) -> str:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).date().isoformat()


@dataclass
class BudgetEvent:
    scope: str = ""   # session | agent | team
    scope_id: str = ""
    level: str = "warn"  # warn | halt
    value: int = 0
    limit: int = 0
    message: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

    @property
    def date(self) -> str:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).date().isoformat()
