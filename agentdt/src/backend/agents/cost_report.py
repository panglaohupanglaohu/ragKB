# -*- coding: utf-8 -*-
"""Cost Report — 汇总 Token 消耗 + targets + ratchet，供 demo case 核对。

P5.3: 只读聚合，不落新表。可选把每次生成的快照追加到 storage/cost_reports/{ts}.json。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_REPORTS_DIR = Path(__file__).resolve().parents[3] / "storage" / "cost_reports"
_SNAPSHOT_KEEP_COUNT = 20


def generate_cost_report(window: str = "24h", team: Optional[str] = None) -> Dict[str, Any]:
    """生成 Token 成本报告。

    汇总: by_phase / by_team / by_skill / targets 进度 / ratchet 锁定节省。
    含 reconciliation 恒等式自查: phase_sum == team_sum。
    """
    from .token_ledger import LEDGER

    # P8.7: by_phase 也按 team 过滤，保证 phase_sum 与 team_sum 同口径
    by_phase = LEDGER.by_phase(window, team_id=team) if team else LEDGER.by_phase(window)
    by_team_all = LEDGER.by_team(window, include_unattributed=True)
    by_team = _display_team_rows(LEDGER.by_team(window), team)
    by_skill = LEDGER.by_skill(window)

    phase_sum = sum(int(p.get("total", 0)) for p in by_phase.values())
    team_sum = _team_sum_for_reconciliation(by_team, by_team_all, bool(team))
    unattributed = _unattributed_tokens(by_team_all, bool(team))

    # P8.6: 杠杆拆分
    lever_split = LEDGER.lever_split(team or "", window)

    # targets 进度
    targets_with_progress = _load_targets_with_progress()

    # ratchet 锁定节省
    ratchet_locked = _load_ratchet_locked()

    report = {
        "window": window,
        "team": team or "",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "total_tokens": team_sum,
            "by_phase": by_phase,
        },
        "by_team": by_team,
        "by_skill": by_skill,
        "targets": targets_with_progress,
        "ratchet_locked": ratchet_locked,
        "lever_split": lever_split,
        "unattributed_tokens": unattributed,
        "reconciliation": {
            "phase_sum": phase_sum,
            "team_sum": team_sum,
            "unattributed": unattributed,
            "consistent": phase_sum == team_sum,
        },
    }

    _write_snapshot(report)

    return report


def _display_team_rows(rows: List[Dict[str, Any]], team: Optional[str]) -> List[Dict[str, Any]]:
    if not team:
        return rows
    return [row for row in rows if row.get("team_id") == team]


def _team_sum_for_reconciliation(
    displayed_rows: List[Dict[str, Any]],
    all_rows: List[Dict[str, Any]],
    has_team_filter: bool,
) -> int:
    if has_team_filter:
        return sum(int(row.get("total", 0)) for row in displayed_rows)
    return sum(int(row.get("total", 0)) for row in all_rows)


def _unattributed_tokens(rows: List[Dict[str, Any]], has_team_filter: bool) -> int:
    if has_team_filter:
        return 0
    return next(
        (
            int(row.get("total", 0))
            for row in rows
            if not (row.get("team_id") or "").strip()
        ),
        0,
    )


def _load_targets_with_progress() -> List[Dict[str, Any]]:
    targets_with_progress: List[Dict[str, Any]] = []
    try:
        from .cost_targets import get_target_store
        store = get_target_store()
        for target in store.list_targets():
            targets_with_progress.append(store.get_progress(target.id))
    except Exception as e:
        logger.debug("targets 加载失败: %s", e)
    return targets_with_progress


def _load_ratchet_locked() -> List[Dict[str, Any]]:
    try:
        from .ratchet_ledger import get_ratchet_ledger
        return get_ratchet_ledger().list_metrics("cost_efficiency:")
    except Exception as e:
        logger.debug("ratchet 加载失败: %s", e)
    return []


def _write_snapshot(report: Dict[str, Any]) -> None:
    try:
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap = _REPORTS_DIR / f"{ts}.json"
        snap.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        # 保留最近 20 份
        old = sorted(_REPORTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
        for p in old[:-_SNAPSHOT_KEEP_COUNT]:
            p.unlink(missing_ok=True)
    except Exception as e:
        logger.debug("报告快照写入失败（非致命）: %s", e)
