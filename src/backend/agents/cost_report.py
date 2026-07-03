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


def generate_cost_report(window: str = "24h", team: Optional[str] = None) -> Dict[str, Any]:
    """生成 Token 成本报告。

    汇总: by_phase / by_team / by_skill / targets 进度 / ratchet 锁定节省。
    含 reconciliation 恒等式自查: phase_sum == team_sum。
    """
    from .token_ledger import LEDGER

    # P8.7: by_phase 也按 team 过滤，保证 phase_sum 与 team_sum 同口径
    by_phase = LEDGER.by_phase(window, team_id=team) if team else LEDGER.by_phase(window)
    # 展示用 by_team 默认排除未归因（P10.2）；对账用必须含未归因，否则与 by_phase 口径不一致
    by_team = LEDGER.by_team(window)
    by_skill = LEDGER.by_skill(window)

    # team 过滤
    if team:
        by_team = [t for t in by_team if t.get("team_id") == team]

    phase_sum = sum(int(p.get("total", 0)) for p in by_phase.values())
    # P10.2 对账修正：by_team 默认剔除未归因(team_id='')，但 by_phase 含全部 →
    # 对账必须同口径：team 维度用「含未归因」的全量求和，否则恒不一致。
    if team:
        team_sum = sum(int(t.get("total", 0)) for t in by_team)
    else:
        team_sum = sum(int(t.get("total", 0)) for t in LEDGER.by_team(window, include_unattributed=True))
    # 未归因金额单列，便于治理（历史空 team_id 的 token）
    unattributed = next((int(t.get("total", 0))
                         for t in LEDGER.by_team(window, include_unattributed=True)
                         if not (t.get("team_id") or "").strip()), 0) if not team else 0

    # P8.6: 杠杆拆分
    lever_split = LEDGER.lever_split(team or "", window)

    # targets 进度
    targets_with_progress: List[Dict[str, Any]] = []
    try:
        from .cost_targets import get_target_store
        store = get_target_store()
        for t in store.list_targets():
            progress = store.get_progress(t.id)
            targets_with_progress.append(progress)
    except Exception as e:
        logger.debug("targets 加载失败: %s", e)

    # ratchet 锁定节省
    ratchet_locked: List[Dict[str, Any]] = []
    try:
        from .ratchet_ledger import get_ratchet_ledger
        ratchet_locked = get_ratchet_ledger().list_metrics("cost_efficiency:")
    except Exception as e:
        logger.debug("ratchet 加载失败: %s", e)

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

    # 可选：快照追加到 storage/cost_reports/{ts}.json
    try:
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap = _REPORTS_DIR / f"{ts}.json"
        snap.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        # 保留最近 20 份
        old = sorted(_REPORTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
        for p in old[:-20]:
            p.unlink(missing_ok=True)
    except Exception as e:
        logger.debug("报告快照写入失败（非致命）: %s", e)

    return report
