# -*- coding: utf-8 -*-
"""Token 治理开关 + 可调参数（settings.json → token_governance）."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from .lever_params import (
    default_params,
    normalize_budget_params,
    normalize_params,
)

_SETTINGS_PATH = Path(__file__).resolve().parents[4] / "config" / "settings.json"
_lock = threading.Lock()

_DEFAULTS: Dict[str, Any] = {
    "compress": True,
    "simplify_prompt": True,
    "cache_mode": "observe",  # observe | serve | off
    "model_route": True,
    "skill_route_hint": True,
    "budget_enforce_submit": True,
    "budget_enforce_turn": True,
    # R9 research-inspired levers (real algorithms, not page copy)
    "rtk_tool_compress": True,
    "progressive_memory": True,
    "codegraph_context": True,
    "ponytail_level": "full",  # off|lite|full|ultra
    "caveman_level": "full",
    "cost_tier_route": True,
    # R10: tunable algorithm knobs
    "params": default_params(),
}

_BOOL_KEYS = {
    "compress",
    "simplify_prompt",
    "model_route",
    "skill_route_hint",
    "budget_enforce_submit",
    "budget_enforce_turn",
    "rtk_tool_compress",
    "progressive_memory",
    "codegraph_context",
    "cost_tier_route",
}


def load_tg_settings() -> Dict[str, Any]:
    data = dict(_DEFAULTS)
    data["params"] = default_params()
    # env overrides
    if os.environ.get("AG_PROMPT_COMPRESS") in ("0", "false", "False"):
        data["compress"] = False
    if os.environ.get("AG_TG_CACHE_MODE"):
        data["cache_mode"] = os.environ["AG_TG_CACHE_MODE"]
    try:
        raw = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        block = raw.get("token_governance") or {}
        if isinstance(block, dict):
            for k in _DEFAULTS:
                if k == "params":
                    continue
                if k in block:
                    data[k] = block[k]
            data["params"] = normalize_params(block.get("params") or {})
    except Exception:
        pass
    if data.get("cache_mode") not in ("observe", "serve", "off"):
        data["cache_mode"] = "observe"
    for level_key in ("ponytail_level", "caveman_level"):
        if data.get(level_key) not in ("off", "lite", "full", "ultra"):
            data[level_key] = "full"
    return data


def save_tg_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge switches + params. Budget keys in updates['params'] or top-level budget_* handled by caller routes."""
    with _lock:
        cur = load_tg_settings()
        for k, v in (updates or {}).items():
            if k == "params":
                continue
            if k not in _DEFAULTS:
                continue
            if v is None:
                continue
            if k in _BOOL_KEYS:
                cur[k] = bool(v)
            else:
                cur[k] = v
        if "params" in (updates or {}) and isinstance(updates.get("params"), dict):
            # merge with existing then normalize
            merged = dict(cur.get("params") or {})
            merged.update(updates["params"])
            cur["params"] = normalize_params(merged)
        if cur.get("cache_mode") not in ("observe", "serve", "off"):
            cur["cache_mode"] = "observe"
        for level_key in ("ponytail_level", "caveman_level"):
            if cur.get(level_key) not in ("off", "lite", "full", "ultra"):
                cur[level_key] = "full"
        # ensure params always present
        cur["params"] = normalize_params(cur.get("params") or {})
        try:
            raw: Dict[str, Any] = {}
            if _SETTINGS_PATH.exists():
                raw = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
            # drop budget keys accidentally nested under tg params before write
            tg_block = {k: v for k, v in cur.items() if k != "params"}
            tg_block["params"] = dict(cur["params"])
            raw["token_governance"] = tg_block
            _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            _SETTINGS_PATH.write_text(
                json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8",
            )
        except Exception:
            pass
        return cur


def load_budget_knobs() -> Dict[str, Any]:
    """Read budget segment with clamp (for levers GET)."""
    raw: Dict[str, Any] = {}
    try:
        data = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        raw = data.get("budget") or {}
    except Exception:
        pass
    return normalize_budget_params(raw if isinstance(raw, dict) else {})


def apply_budget_knobs_from_params(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """If params contain budget keys, write budget settings and refresh guard. Returns budget dict or None."""
    if not params:
        return None
    budget_keys = {
        "alert_threshold",
        "on_exceed",
        "per_session_max",
        "per_agent_daily_max",
        "per_team_daily_max",
    }
    subset = {k: v for k, v in params.items() if k in budget_keys}
    if not subset:
        return None
    try:
        from ..budget.guard import get_budget_guard, save_budget_settings
        from ..budget.models import TokenBudget

        current = load_budget_knobs()
        current.update(subset)
        norm = normalize_budget_params(current)
        tb = TokenBudget(
            per_session_max=int(norm["per_session_max"]),
            per_agent_daily_max=int(norm["per_agent_daily_max"]),
            per_team_daily_max=int(norm["per_team_daily_max"]),
            on_exceed=str(norm["on_exceed"]),
            alert_threshold=float(norm["alert_threshold"]),
        )
        save_budget_settings(tb)
        get_budget_guard().update_budget(tb)
        return tb.to_dict()
    except Exception:
        return None
