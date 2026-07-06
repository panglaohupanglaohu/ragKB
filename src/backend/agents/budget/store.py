from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from .models import BudgetEvent, UsageRecord


_DB_PATH = Path(__file__).resolve().parents[4] / "storage" / "usage.db"
_usage_store: Optional["UsageStore"] = None


class UsageStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path or _DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    session_id TEXT,
                    agent_id TEXT,
                    team_id TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    total_tokens INTEGER,
                    model TEXT,
                    cost_usd REAL,
                    date TEXT,
                    phase TEXT DEFAULT 'task',
                    skill_id TEXT DEFAULT '',
                    scenario_id TEXT DEFAULT '',
                    run_id TEXT DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_usage_session ON usage_log(session_id);
                CREATE INDEX IF NOT EXISTS idx_usage_agent_date ON usage_log(agent_id, date);
                CREATE INDEX IF NOT EXISTS idx_usage_team_date ON usage_log(team_id, date);

                CREATE TABLE IF NOT EXISTS budget_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    scope TEXT,
                    scope_id TEXT,
                    level TEXT,
                    value INTEGER,
                    limit_value INTEGER,
                    message TEXT,
                    date TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_budget_events_date ON budget_events(date);
                """
            )
            self._migrate(conn)

    def _migrate(self, conn) -> None:
        """幂等迁移：旧库补归因列 + 索引。"""
        cols = {r[1] for r in conn.execute("PRAGMA table_info(usage_log)")}
        for col in ("phase", "skill_id", "scenario_id", "run_id"):
            if col not in cols:
                conn.execute(f"ALTER TABLE usage_log ADD COLUMN {col} TEXT DEFAULT ''")
        if "phase" not in cols:
            conn.execute("UPDATE usage_log SET phase = 'task' WHERE phase IS NULL OR phase = ''")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_run ON usage_log(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_phase_date ON usage_log(phase, date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_skill_date ON usage_log(skill_id, date)")

    def record_usage(self, record: UsageRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_log (
                    timestamp, session_id, agent_id, team_id,
                    input_tokens, output_tokens, total_tokens, model, cost_usd, date,
                    phase, skill_id, scenario_id, run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.timestamp,
                    record.session_id,
                    record.agent_id,
                    record.team_id,
                    record.input_tokens,
                    record.output_tokens,
                    record.total_tokens,
                    record.model,
                    record.cost_usd,
                    record.date,
                    record.phase,
                    record.skill_id,
                    record.scenario_id,
                    record.run_id,
                ),
            )

    def record_event(self, event: BudgetEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO budget_events (
                    timestamp, scope, scope_id, level, value, limit_value, message, date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.timestamp,
                    event.scope,
                    event.scope_id,
                    event.level,
                    event.value,
                    event.limit,
                    event.message,
                    event.date,
                ),
            )

    def get_session_total(self, session_id: str) -> int:
        if not session_id:
            return 0
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(total_tokens), 0) FROM usage_log WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return int(row[0] or 0)

    def get_agent_daily_total(self, agent_id: str, date: str) -> int:
        if not agent_id:
            return 0
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(total_tokens), 0) FROM usage_log WHERE agent_id = ? AND date = ?",
                (agent_id, date),
            ).fetchone()
        return int(row[0] or 0)

    def get_team_daily_total(self, team_id: str, date: str) -> int:
        if not team_id:
            return 0
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(total_tokens), 0) FROM usage_log WHERE team_id = ? AND date = ?",
                (team_id, date),
            ).fetchone()
        return int(row[0] or 0)

    def summarize_usage(
        self,
        *,
        agent_id: str = "",
        team_id: str = "",
        from_date: str = "",
        to_date: str = "",
    ) -> Dict[str, object]:
        clauses = []
        params: List[object] = []
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if team_id:
            clauses.append("team_id = ?")
            params.append(team_id)
        if from_date:
            clauses.append("date >= ?")
            params.append(from_date)
        if to_date:
            clauses.append("date <= ?")
            params.append(to_date)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            total = conn.execute(
                f"""
                SELECT
                    COUNT(*),
                    COALESCE(SUM(input_tokens), 0),
                    COALESCE(SUM(output_tokens), 0),
                    COALESCE(SUM(total_tokens), 0),
                    COALESCE(SUM(cost_usd), 0)
                FROM usage_log {where}
                """,
                params,
            ).fetchone()
            daily_rows = conn.execute(
                f"""
                SELECT date, COALESCE(SUM(total_tokens), 0) AS total_tokens
                FROM usage_log {where}
                GROUP BY date
                ORDER BY date DESC
                """,
                params,
            ).fetchall()

        return {
            "record_count": int(total[0] or 0),
            "input_tokens": int(total[1] or 0),
            "output_tokens": int(total[2] or 0),
            "total_tokens": int(total[3] or 0),
            "cost_usd": float(total[4] or 0.0),
            "daily": [
                {"date": row[0], "total_tokens": int(row[1] or 0)}
                for row in daily_rows
            ],
            # P1-6/P6-7: 按 phase 分列（task=生产 / drill=simulation / plaza=deliberation）
            "by_phase": self._phase_breakdown(conn, where, params) if False else self._phase_breakdown(where, params),
        }

    def _phase_breakdown(self, where: str, params: List[object]) -> List[Dict[str, object]]:
        """按 phase 分列 token 用量."""
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT phase, COUNT(*), COALESCE(SUM(total_tokens), 0), COALESCE(SUM(cost_usd), 0)
                FROM usage_log {where}
                GROUP BY phase
                ORDER BY phase
                """,
                params,
            ).fetchall()
        return [
            {"phase": row[0] or "task", "count": int(row[1] or 0),
             "total_tokens": int(row[2] or 0), "cost_usd": float(row[3] or 0.0)}
            for row in rows
        ]

    def recent_events(self, *, limit: int = 50, level: str = "") -> List[Dict[str, object]]:
        clauses = []
        params: List[object] = []
        if level:
            clauses.append("level = ?")
            params.append(level)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT timestamp, scope, scope_id, level, value, limit_value, message, date
                FROM budget_events
                {where}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                [*params, limit],
            ).fetchall()
        return [
            {
                "timestamp": float(row[0]),
                "scope": row[1],
                "scope_id": row[2],
                "level": row[3],
                "value": int(row[4] or 0),
                "limit": int(row[5] or 0),
                "message": row[6],
                "date": row[7],
            }
            for row in rows
        ]


def get_usage_store() -> UsageStore:
    global _usage_store
    if _usage_store is None:
        _usage_store = UsageStore()
    return _usage_store
