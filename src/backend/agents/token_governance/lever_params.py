# -*- coding: utf-8 -*-
"""治理杠杆可调参数 schema — UI 旋钮与 prepare 共用权威源."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# 每个参数：key 扁平存在 settings.token_governance.params 下
# type: int | float | enum | bool
PARAM_SPECS: List[Dict[str, Any]] = [
    # compress
    {
        "key": "system_max_chars",
        "lever_id": "compress",
        "label": "system 上限",
        "type": "int",
        "default": 6000,
        "min": 1000,
        "max": 20000,
        "step": 500,
        "unit": "字",
    },
    {
        "key": "msg_max_chars",
        "lever_id": "compress",
        "label": "其它消息上限",
        "type": "int",
        "default": 4000,
        "min": 500,
        "max": 12000,
        "step": 250,
        "unit": "字",
    },
    # rtk
    {
        "key": "max_tool_chars",
        "lever_id": "rtk_tool_compress",
        "label": "tool 截断",
        "type": "int",
        "default": 2200,
        "min": 500,
        "max": 8000,
        "step": 100,
        "unit": "字",
    },
    # progressive
    {
        "key": "keep_recent",
        "lever_id": "progressive_memory",
        "label": "保留近轮",
        "type": "int",
        "default": 6,
        "min": 2,
        "max": 20,
        "step": 1,
        "unit": "轮",
    },
    {
        "key": "min_total_for_collapse",
        "lever_id": "progressive_memory",
        "label": "折叠门槛",
        "type": "int",
        "default": 10,
        "min": 4,
        "max": 40,
        "step": 1,
        "unit": "条",
    },
    {
        "key": "index_max_chars",
        "lever_id": "progressive_memory",
        "label": "索引行长",
        "type": "int",
        "default": 140,
        "min": 40,
        "max": 400,
        "step": 10,
        "unit": "字",
    },
    # codegraph
    {
        "key": "min_blob_chars",
        "lever_id": "codegraph_context",
        "label": "切片阈值",
        "type": "int",
        "default": 2500,
        "min": 800,
        "max": 12000,
        "step": 100,
        "unit": "字",
    },
    # cache
    {
        "key": "cache_max_size",
        "lever_id": "cache",
        "label": "LRU 容量",
        "type": "int",
        "default": 256,
        "min": 32,
        "max": 2048,
        "step": 32,
        "unit": "条",
    },
    # skill
    {
        "key": "skill_system_max_chars",
        "lever_id": "skill_route",
        "label": "system 裁切",
        "type": "int",
        "default": 3500,
        "min": 1000,
        "max": 8000,
        "step": 250,
        "unit": "字",
    },
    # budget (stored in settings.budget; mirrored for UI)
    {
        "key": "alert_threshold",
        "lever_id": "budget",
        "label": "告警阈值",
        "type": "float",
        "default": 0.8,
        "min": 0.5,
        "max": 0.99,
        "step": 0.05,
        "unit": "",
        "store": "budget",
    },
    {
        "key": "on_exceed",
        "lever_id": "budget",
        "label": "超限策略",
        "type": "enum",
        "default": "halt",
        "enum_values": ["halt", "warn"],
        "store": "budget",
    },
    {
        "key": "per_session_max",
        "lever_id": "budget",
        "label": "会话上限",
        "type": "int",
        "default": 200_000,
        "min": 10_000,
        "max": 5_000_000,
        "step": 10_000,
        "unit": "tok",
        "store": "budget",
    },
    {
        "key": "per_agent_daily_max",
        "lever_id": "budget",
        "label": "智能体日限",
        "type": "int",
        "default": 2_000_000,
        "min": 50_000,
        "max": 50_000_000,
        "step": 50_000,
        "unit": "tok",
        "store": "budget",
    },
    {
        "key": "per_team_daily_max",
        "lever_id": "budget",
        "label": "团队日限",
        "type": "int",
        "default": 10_000_000,
        "min": 100_000,
        "max": 200_000_000,
        "step": 100_000,
        "unit": "tok",
        "store": "budget",
    },
]


def param_spec_map() -> Dict[str, Dict[str, Any]]:
    return {s["key"]: s for s in PARAM_SPECS}


def params_for_lever(lever_id: str) -> List[Dict[str, Any]]:
    return [dict(s) for s in PARAM_SPECS if s.get("lever_id") == lever_id]


def default_params() -> Dict[str, Any]:
    return {s["key"]: s["default"] for s in PARAM_SPECS if s.get("store") != "budget"}


def default_budget_params() -> Dict[str, Any]:
    return {s["key"]: s["default"] for s in PARAM_SPECS if s.get("store") == "budget"}


def clamp_param(key: str, value: Any) -> Any:
    """Clamp / coerce one param; unknown keys dropped by caller."""
    spec = param_spec_map().get(key)
    if not spec:
        return None
    t = spec.get("type")
    if t == "enum":
        allowed = list(spec.get("enum_values") or [])
        v = str(value)
        return v if v in allowed else spec["default"]
    if t == "bool":
        return bool(value)
    if t == "float":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return float(spec["default"])
        lo = float(spec.get("min", v))
        hi = float(spec.get("max", v))
        return max(lo, min(hi, v))
    # int
    try:
        v = int(float(value))
    except (TypeError, ValueError):
        return int(spec["default"])
    lo = int(spec.get("min", v))
    hi = int(spec.get("max", v))
    return max(lo, min(hi, v))


def normalize_params(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge defaults + clamp known keys (tg params only, not budget store)."""
    out = default_params()
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        spec = param_spec_map().get(k)
        if not spec or spec.get("store") == "budget":
            continue
        clamped = clamp_param(k, v)
        if clamped is not None:
            out[k] = clamped
    return out


def normalize_budget_params(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = default_budget_params()
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        spec = param_spec_map().get(k)
        if not spec or spec.get("store") != "budget":
            continue
        clamped = clamp_param(k, v)
        if clamped is not None:
            out[k] = clamped
    return out


def attach_params_to_catalog_row(
    lever_id: str,
    tg_params: Dict[str, Any],
    budget_params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Return params list with current value for one lever."""
    budget_params = budget_params or {}
    rows = []
    for s in params_for_lever(lever_id):
        row = dict(s)
        key = s["key"]
        if s.get("store") == "budget":
            row["value"] = budget_params.get(key, s["default"])
        else:
            row["value"] = tg_params.get(key, s["default"])
        rows.append(row)
    return rows
