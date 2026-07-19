"""TokenLedger — 从 usage.db 聚合 Token 成本，单一读出端。

不另建 token_probe 模块；直接复用 UsageStore 的 SQLite 库。
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .budget.store import get_usage_store

logger = logging.getLogger(__name__)


class TokenLedger:
    """聚合 Token 成本，按团队/技能/阶段/run_id 维度读出。"""

    def __init__(self, store=None):
        self._store = store

    @property
    def store(self):
        if self._store is None:
            self._store = get_usage_store()
        return self._store

    def _window_start(self, window: str) -> str:
        """将 '24h'/'7d'/'30d'/'all' 转为 UTC date 边界字符串。"""
        if window == "all" or not window:
            return "1970-01-01"
        now = datetime.now(timezone.utc)
        # 解析 window 格式
        if window.endswith("h"):
            hours = int(window[:-1])
            start = now - timedelta(hours=hours)
        elif window.endswith("d"):
            days = int(window[:-1])
            start = now - timedelta(days=days)
        else:
            start = now - timedelta(hours=24)
        return start.date().isoformat()

    def _query(self, sql: str, params: list) -> List[Dict]:
        with self.store._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in (self._row_to_dict(conn, r) for r in rows) if row]

    def _row_to_dict(self, conn, row):
        """将 sqlite3.Row 转为 dict（如果已配置 row_factory）。"""
        try:
            return dict(row)
        except (TypeError, ValueError):
            return None

    def by_team(self, window: str = "24h", include_unattributed: bool = False) -> List[Dict]:
        """按团队聚合 Token 成本。

        P10.2: 默认排除 team_id='' 的历史未归因数据，避免「(未归因)」顶在最贵团队首位。
        """
        ws = self._window_start(window)
        where = "date >= ? AND total_tokens > 0"
        if not include_unattributed:
            where += " AND team_id != ''"
        with self.store._connect() as conn:
            conn.row_factory = None
            rows = conn.execute(
                f"""
                SELECT
                    COALESCE(team_id, '') AS team_id,
                    COALESCE(SUM(total_tokens), 0) AS total,
                    COALESCE(SUM(input_tokens), 0) AS input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens,
                    COUNT(*) AS calls
                FROM usage_log
                WHERE {where}
                GROUP BY team_id
                ORDER BY total DESC
                """,
                (ws,),
            ).fetchall()
        return [
            {
                "team_id": r[0] or "",
                "total": int(r[1] or 0),
                "input_tokens": int(r[2] or 0),
                "output_tokens": int(r[3] or 0),
                "calls": int(r[4] or 0),
            }
            for r in rows
        ]

    def by_skill(self, window: str = "24h") -> List[Dict]:
        """按技能聚合 Token 成本（过滤空 skill_id）。"""
        ws = self._window_start(window)
        with self.store._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    skill_id,
                    COALESCE(SUM(total_tokens), 0) AS total,
                    COALESCE(SUM(input_tokens), 0) AS input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens,
                    COUNT(*) AS calls
                FROM usage_log
                WHERE date >= ? AND total_tokens > 0 AND skill_id != ''
                GROUP BY skill_id
                ORDER BY total DESC
                """,
                (ws,),
            ).fetchall()
        return [
            {
                "skill_id": r[0] or "",
                "total": int(r[1] or 0),
                "input_tokens": int(r[2] or 0),
                "output_tokens": int(r[3] or 0),
                "calls": int(r[4] or 0),
            }
            for r in rows
        ]

    def by_task(
        self,
        window: str = "24h",
        team_id: str = "",
        limit: int = 50,
    ) -> List[Dict]:
        """按任务维聚合 Token（TG-2：scenario_id 优先，否则 run_id）.

        task_key = COALESCE(NULLIF(scenario_id,''), NULLIF(run_id,''), '(unscoped)')
        北极星：任务上耗费的 token。
        """
        ws = self._window_start(window)
        where = "date >= ? AND total_tokens > 0"
        params: list = [ws]
        if team_id:
            where += " AND team_id = ?"
            params.append(team_id)
        lim = max(1, min(int(limit or 50), 200))
        sql = f"""
            SELECT
                COALESCE(NULLIF(scenario_id, ''), NULLIF(run_id, ''), '(unscoped)') AS task_key,
                COALESCE(MAX(team_id), '') AS team_id,
                COALESCE(SUM(total_tokens), 0) AS total,
                COALESCE(SUM(input_tokens), 0) AS input_tokens,
                COALESCE(SUM(output_tokens), 0) AS output_tokens,
                COUNT(*) AS calls,
                MAX(timestamp) AS last_ts
            FROM usage_log
            WHERE {where}
            GROUP BY task_key
            ORDER BY total DESC
            LIMIT ?
        """
        params.append(lim)
        with self.store._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            {
                "task_key": r[0] or "(unscoped)",
                "team_id": r[1] or "",
                "total": int(r[2] or 0),
                "input_tokens": int(r[3] or 0),
                "output_tokens": int(r[4] or 0),
                "calls": int(r[5] or 0),
                "last_ts": r[6],
            }
            for r in rows
        ]

    def by_phase(self, window: str = "24h", team_id: str = "") -> Dict[str, Dict]:
        """按阶段聚合 Token 成本。可选 team_id 过滤。"""
        ws = self._window_start(window)
        where = "date >= ? AND total_tokens > 0"
        params: list = [ws]
        if team_id:
            where += " AND team_id = ?"
            params.append(team_id)
        with self.store._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    COALESCE(phase, 'task') AS phase,
                    COALESCE(SUM(total_tokens), 0) AS total,
                    COALESCE(SUM(input_tokens), 0) AS input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens,
                    COUNT(*) AS calls
                FROM usage_log
                    WHERE {where}
                GROUP BY phase
                """,
                params,
            ).fetchall()
        return {
            r[0]: {
                "total": int(r[1] or 0),
                "input_tokens": int(r[2] or 0),
                "output_tokens": int(r[3] or 0),
                "calls": int(r[4] or 0),
            }
            for r in rows
        }

    def run(self, run_id: str) -> Dict:
        """按 run_id 聚合（包含 by_phase / by_agent 子聚合）。"""
        if not run_id:
            return {"run_id": "", "total": 0, "input": 0, "output": 0, "calls": 0,
                    "by_phase": {}, "by_agent": {}}
        with self.store._connect() as conn:
            # 总计
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(total_tokens), 0),
                    COALESCE(SUM(input_tokens), 0),
                    COALESCE(SUM(output_tokens), 0),
                    COUNT(*)
                FROM usage_log WHERE run_id = ? AND total_tokens > 0
                """,
                (run_id,),
            ).fetchone()
            total = int(row[0] or 0)

            # by_phase
            phase_rows = conn.execute(
                """
                SELECT COALESCE(phase, 'task'), COALESCE(SUM(total_tokens), 0)
                FROM usage_log WHERE run_id = ? AND total_tokens > 0
                GROUP BY phase
                """,
                (run_id,),
            ).fetchall()
            by_phase = {r[0]: int(r[1] or 0) for r in phase_rows}

            # by_agent
            agent_rows = conn.execute(
                """
                SELECT COALESCE(agent_id, ''), COALESCE(SUM(total_tokens), 0)
                FROM usage_log WHERE run_id = ? AND total_tokens > 0
                GROUP BY agent_id
                """,
                (run_id,),
            ).fetchall()
            by_agent = {r[0]: int(r[1] or 0) for r in agent_rows}

        return {
            "run_id": run_id,
            "total": total,
            "input": int(row[1] or 0),
            "output": int(row[2] or 0),
            "calls": int(row[3] or 0),
            "by_phase": by_phase,
            "by_agent": by_agent,
        }

    def summary(self, window: str = "24h") -> Dict:
        """全局汇总。"""
        ws = self._window_start(window)
        with self.store._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(total_tokens), 0),
                    COALESCE(SUM(input_tokens), 0),
                    COALESCE(SUM(output_tokens), 0),
                    COUNT(*)
                FROM usage_log WHERE date >= ? AND total_tokens > 0
                """,
                (ws,),
            ).fetchone()
        return {
            "window": window,
            "total": int(row[0] or 0),
            "input_tokens": int(row[1] or 0),
            "output_tokens": int(row[2] or 0),
            "calls": int(row[3] or 0),
        }

    # ── Phase 8 新增聚合方法 ──────────────────────────────

    def breakdown(self, window: str = "24h", dim: str = "team", team_id: str = "") -> List[Dict]:
        """统一成本构成读出：dim ∈ team|skill|phase。返回 [{key,total,input,output,calls}] 倒序。

        P10.1: team_id 可选过滤（dim=team 时忽略）。
        """
        if dim == "skill":
            rows = self.by_skill(window); keyf = "skill_id"
        elif dim == "phase":
            rows = [{"phase": k, **v} for k, v in self.by_phase(window, team_id=team_id).items()]; keyf = "phase"
        else:
            rows = self.by_team(window); keyf = "team_id"
        out = [{"key": r.get(keyf) or "(未归因)", "total": r.get("total", 0),
                "input": r.get("input_tokens", 0), "output": r.get("output_tokens", 0),
                "calls": r.get("calls", 0)} for r in rows]
        return sorted(out, key=lambda x: x["total"], reverse=True)

    def trend(self, window: str = "7d", bucket: str = "day", dim: str = "", key: str = "", team_id: str = "") -> Dict:
        """返回 {points:[{t, total, calls}], total, dimension, value, bucket}。

        bucket: day（按 date 列分组）| hour（按 strftime 分组）。
        dim/key 可选：限定某团队/技能/阶段的趋势（dim ∈ team|skill|phase）。
        P10.1: team_id 可选过滤。
        """
        ws = self._window_start(window)
        if bucket == "hour":
            tcol = "strftime('%Y-%m-%dT%H', datetime(timestamp,'unixepoch'))"
        else:
            tcol = "date"
        where_parts = ["date >= ?", "total_tokens > 0"]
        params: list = [ws]
        if dim and key:
            colmap = {"team": "team_id", "skill": "skill_id", "phase": "phase"}
            col = colmap.get(dim, dim)
            where_parts.append(f"{col} = ?")
            params.append(key)
        elif team_id:
            where_parts.append("team_id = ?")
            params.append(team_id)
        sql = (f"SELECT {tcol} AS t, COALESCE(SUM(total_tokens),0) AS total, COUNT(*) AS calls "
               f"FROM usage_log WHERE {' AND '.join(where_parts)} GROUP BY t ORDER BY t ASC")
        with self.store._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        points = [{"t": r[0], "total": int(r[1] or 0), "calls": int(r[2] or 0)} for r in rows]
        return {"points": points, "total": sum(p["total"] for p in points),
                "dimension": dim or "all", "value": key or "全部", "bucket": bucket}

    def recent_runs(self, window: str = "24h", limit: int = 100, team_id: str = "") -> List[Dict]:
        """按 run_id 聚合最近的 run（明细行）。P10.1: team_id 可选过滤。"""
        ws = self._window_start(window)
        where = "date>=? AND total_tokens>0 AND run_id<>''"
        params: list = [ws]
        if team_id:
            where += " AND team_id=?"
            params.append(team_id)
        sql = (f"SELECT run_id, MAX(phase) phase, MAX(team_id) team_id, MAX(skill_id) skill_id, "
               f"       COALESCE(SUM(total_tokens),0) total, COUNT(*) calls, MAX(timestamp) ts "
               f"FROM usage_log WHERE {where} "
               f"GROUP BY run_id ORDER BY ts DESC LIMIT ?")
        params.append(limit)
        with self.store._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [{"run_id": r[0], "phase": r[1], "team_id": r[2], "skill_id": r[3],
                 "total": int(r[4] or 0), "calls": int(r[5] or 0), "ts": r[6]} for r in rows]

    def recent_calls(self, window: str = "24h", limit: int = 200, team_id: str = "") -> List[Dict]:
        """逐条 LLM 调用明细。P10.1: team_id 可选过滤。"""
        ws = self._window_start(window)
        where = "date>=? AND total_tokens>0"
        params: list = [ws]
        if team_id:
            where += " AND team_id=?"
            params.append(team_id)
        sql = (f"SELECT timestamp, phase, team_id, agent_id, skill_id, run_id, model, "
               f"       input_tokens, output_tokens, total_tokens "
               f"FROM usage_log WHERE {where} ORDER BY timestamp DESC LIMIT ?")
        params.append(limit)
        with self.store._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        cols = ["ts", "phase", "team_id", "agent_id", "skill_id", "run_id", "model",
                "input", "output", "total"]
        return [dict(zip(cols, r)) for r in rows]

    # ── 杠杆拆分（Phase 8.6）──

    SKILL_LEVER_PHASES = {"extract", "skill_verify"}
    COLLAB_LEVER_PHASES = {"plaza", "drill", "task"}

    def lever_split(self, team_id: str = "", window: str = "7d") -> Dict:
        """把 by_phase 归并为 Skill 杠杆 vs 协作杠杆 vs other。"""
        bp = self.by_phase(window, team_id=team_id) if team_id else self.by_phase(window)
        skill = sum(int(bp.get(k, {}).get("total", 0)) for k in self.SKILL_LEVER_PHASES)
        collab = sum(int(bp.get(k, {}).get("total", 0)) for k in self.COLLAB_LEVER_PHASES)
        # P8R.8: 未映射 phase 兜底
        mapped = self.SKILL_LEVER_PHASES | self.COLLAB_LEVER_PHASES
        other = sum(int(v.get("total", 0)) for k, v in bp.items() if k not in mapped)
        grand_total = skill + collab + other
        return {"skill": skill, "collab": collab, "other": other,
                "total": skill + collab, "grand_total": grand_total,
                "skill_pct": round(skill / grand_total, 4) if grand_total else 0.0,
                "collab_pct": round(collab / grand_total, 4) if grand_total else 0.0}


LEDGER = TokenLedger()
