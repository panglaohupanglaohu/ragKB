# -*- coding: utf-8 -*-
"""Prepare 节省事件落盘 — 按 task 可查（JSONL，无外部依赖）."""
from __future__ import annotations

import json
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parents[4]
_PATH = _ROOT / "storage" / "token_governance" / "savings_events.jsonl"
_lock = threading.Lock()
_MAX_LINES = 5000


def _ensure_parent() -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)


def append_event(event: Dict[str, Any], path: Optional[Path] = None) -> None:
    p = path or _PATH
    row = dict(event)
    row.setdefault("at", time.time())
    with _lock:
        _ensure_parent() if p == _PATH else p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        # 简易裁剪：超过上限时保留尾部
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
            if len(lines) > _MAX_LINES:
                p.write_text("\n".join(lines[-(_MAX_LINES // 2) :]) + "\n", encoding="utf-8")
        except Exception:
            pass


def recent_events(
    *,
    limit: int = 50,
    task_id: str = "",
    team_id: str = "",
    path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    p = path or _PATH
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if task_id and str(row.get("task_id") or "") != str(task_id):
            continue
        if team_id and str(row.get("team_id") or "") != str(team_id):
            continue
        out.append(row)
        if len(out) >= max(1, limit):
            break
    return out


def aggregate_by_task(
    *,
    limit_tasks: int = 20,
    team_id: str = "",
    path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """按 task_id 汇总节省（最近文件内全部事件）."""
    p = path or _PATH
    if not p.exists():
        return []
    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "task_id": "",
            "team_id": "",
            "events": 0,
            "saved_tokens_est": 0,
            "by_kind": defaultdict(int),
            "last_at": 0.0,
        }
    )
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if team_id and str(row.get("team_id") or "") != str(team_id):
            continue
        tid = str(row.get("task_id") or "").strip() or "(no_task)"
        b = buckets[tid]
        b["task_id"] = tid
        b["team_id"] = str(row.get("team_id") or b["team_id"] or "")
        b["events"] += 1
        b["saved_tokens_est"] += int(row.get("saved_tokens_est") or 0)
        for k in row.get("lever_kinds") or []:
            b["by_kind"][str(k)] += 1
        at = float(row.get("at") or 0)
        if at > b["last_at"]:
            b["last_at"] = at
    items = []
    for b in buckets.values():
        items.append({
            "task_id": b["task_id"],
            "team_id": b["team_id"],
            "events": b["events"],
            "saved_tokens_est": b["saved_tokens_est"],
            "by_kind": dict(b["by_kind"]),
            "last_at": b["last_at"],
        })
    items.sort(key=lambda x: (x["saved_tokens_est"], x["last_at"]), reverse=True)
    return items[: max(1, limit_tasks)]
