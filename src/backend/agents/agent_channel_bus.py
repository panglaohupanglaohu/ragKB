# -*- coding: utf-8 -*-
"""Agent 通道绑定运行时 — 真正消费 AgentProfile.channels.

提供：
- 权限判定（subscribe / publish / enabled）
- 进程内消息总线（按 team_id × channel_name）
- 合并写回 helper（eco / 团队配置编辑共用）

与 src/backend/channels/*（MarineChannel 系统模块）无关。
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

_lock = threading.RLock()
# team_id -> channel_name -> list[message]
_BUS: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
_BUS_MAX_PER_CHANNEL = 200


def _ch_name(cfg: Any) -> str:
    if cfg is None:
        return ""
    if isinstance(cfg, dict):
        return str(cfg.get("channel_name") or cfg.get("channel") or "").strip()
    return str(getattr(cfg, "channel_name", None) or getattr(cfg, "channel", None) or "").strip()


def _as_dict(cfg: Any) -> Dict[str, Any]:
    if cfg is None:
        return {}
    if isinstance(cfg, dict):
        d = dict(cfg)
    elif hasattr(cfg, "to_dict"):
        d = cfg.to_dict()
    else:
        d = {
            "channel": getattr(cfg, "channel", ""),
            "channel_name": getattr(cfg, "channel_name", ""),
            "endpoint": getattr(cfg, "endpoint", ""),
            "enabled": getattr(cfg, "enabled", True),
            "sync_interval_seconds": getattr(cfg, "sync_interval_seconds", 60),
            "subscribe": getattr(cfg, "subscribe", True),
            "publish": getattr(cfg, "publish", False),
            "priority": getattr(cfg, "priority", 0),
            "source": getattr(cfg, "source", "") or "",
            "note": getattr(cfg, "note", "") or "",
        }
    name = str(d.get("channel_name") or d.get("channel") or "").strip()
    d["channel_name"] = name
    d["channel"] = name or str(d.get("channel") or "")
    d["enabled"] = bool(d.get("enabled", True))
    d["subscribe"] = bool(d.get("subscribe", True))
    d["publish"] = bool(d.get("publish", False))
    try:
        d["priority"] = int(d.get("priority") or 0)
    except (TypeError, ValueError):
        d["priority"] = 0
    return d


def list_channel_bindings(agent: Any) -> List[Dict[str, Any]]:
    raw = getattr(agent, "channels", None) or []
    out = []
    for c in raw:
        d = _as_dict(c)
        if d.get("channel_name"):
            out.append(d)
    return out


def find_binding(agent: Any, channel_name: str) -> Optional[Dict[str, Any]]:
    want = str(channel_name or "").strip()
    if not want:
        return None
    for d in list_channel_bindings(agent):
        if d["channel_name"] == want:
            return d
    return None


def agent_can_publish(agent: Any, channel_name: str) -> Tuple[bool, str]:
    """无任何绑定 → 兼容放行（legacy）；有绑定则必须 publish+enabled."""
    bindings = list_channel_bindings(agent)
    if not bindings:
        return True, "no_bindings_legacy_allow"
    b = find_binding(agent, channel_name)
    if b is None:
        return False, f"not_bound:{channel_name}"
    if not b.get("enabled", True):
        return False, "disabled"
    if not b.get("publish"):
        return False, "publish_denied"
    return True, "ok"


def agent_can_subscribe(agent: Any, channel_name: str) -> Tuple[bool, str]:
    bindings = list_channel_bindings(agent)
    if not bindings:
        return True, "no_bindings_legacy_allow"
    b = find_binding(agent, channel_name)
    if b is None:
        return False, f"not_bound:{channel_name}"
    if not b.get("enabled", True):
        return False, "disabled"
    if not b.get("subscribe"):
        return False, "subscribe_denied"
    return True, "ok"


def merge_channel_bindings(
    existing: List[Any],
    diffs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """按 channel_name 合并 diff；diff 可设 remove=true 删除."""
    by_name: Dict[str, Dict[str, Any]] = {}
    for c in existing or []:
        d = _as_dict(c)
        if d.get("channel_name"):
            by_name[d["channel_name"]] = d
    for raw in diffs or []:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("channel_name") or raw.get("channel") or "").strip()
        if not name:
            continue
        if raw.get("remove"):
            by_name.pop(name, None)
            continue
        prev = by_name.get(name, {
            "channel": name,
            "channel_name": name,
            "endpoint": "",
            "enabled": True,
            "sync_interval_seconds": 60,
            "subscribe": True,
            "publish": False,
            "priority": 0,
        })
        if "subscribe" in raw:
            prev["subscribe"] = bool(raw["subscribe"])
        if "publish" in raw:
            prev["publish"] = bool(raw["publish"])
        if "enabled" in raw:
            prev["enabled"] = bool(raw["enabled"])
        if "priority" in raw:
            try:
                prev["priority"] = int(raw["priority"])
            except (TypeError, ValueError):
                pass
        if "endpoint" in raw and raw["endpoint"] is not None:
            prev["endpoint"] = str(raw["endpoint"])
        if raw.get("source"):
            prev["source"] = str(raw["source"])
        if raw.get("note"):
            prev["note"] = str(raw["note"])
        prev["channel"] = name
        prev["channel_name"] = name
        by_name[name] = prev
    # priority 降序
    return sorted(by_name.values(), key=lambda x: (-int(x.get("priority") or 0), x["channel_name"]))


def apply_bindings_to_agent(agent: Any, bindings: List[Dict[str, Any]]) -> None:
    """写入 agent.channels（优先构造 AgentChannelConfig）."""
    try:
        from agents.models import AgentChannelConfig
        agent.channels = [
            AgentChannelConfig(
                channel=b.get("channel") or b.get("channel_name") or "",
                channel_name=b.get("channel_name") or b.get("channel") or "",
                endpoint=str(b.get("endpoint") or ""),
                enabled=bool(b.get("enabled", True)),
                sync_interval_seconds=int(b.get("sync_interval_seconds") or 60),
                subscribe=bool(b.get("subscribe", True)),
                publish=bool(b.get("publish", False)),
                priority=int(b.get("priority") or 0),
                source=str(b.get("source") or ""),
                note=str(b.get("note") or ""),
            )
            for b in bindings
            if (b.get("channel_name") or b.get("channel"))
        ]
    except Exception:
        agent.channels = list(bindings)


def publish_message(
    team_id: str,
    channel_name: str,
    *,
    from_agent_id: str,
    content: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    team_id = str(team_id or "default")
    channel_name = str(channel_name or "default").strip() or "default"
    msg = {
        "msg_id": f"cm_{uuid.uuid4().hex[:10]}",
        "team_id": team_id,
        "channel": channel_name,
        "from": from_agent_id,
        "content": str(content or "")[:4000],
        "payload": payload or {},
        "ts": time.time(),
    }
    with _lock:
        team_bus = _BUS.setdefault(team_id, {})
        bucket = team_bus.setdefault(channel_name, [])
        bucket.append(msg)
        if len(bucket) > _BUS_MAX_PER_CHANNEL:
            del bucket[: len(bucket) - _BUS_MAX_PER_CHANNEL]
    return msg


def read_channel(
    team_id: str,
    channel_name: str,
    *,
    limit: int = 20,
    since_ts: float = 0.0,
) -> List[Dict[str, Any]]:
    team_id = str(team_id or "default")
    channel_name = str(channel_name or "").strip()
    with _lock:
        bucket = list((_BUS.get(team_id) or {}).get(channel_name) or [])
    if since_ts:
        bucket = [m for m in bucket if float(m.get("ts") or 0) > since_ts]
    return bucket[-max(1, min(limit, 100)):]


def read_subscribed(
    team_id: str,
    agent: Any,
    *,
    limit_per_channel: int = 10,
) -> List[Dict[str, Any]]:
    """读取 agent 已订阅且 enabled 的通道消息."""
    bindings = list_channel_bindings(agent)
    if not bindings:
        # legacy：可读 default
        return read_channel(team_id, "default", limit=limit_per_channel)
    out: List[Dict[str, Any]] = []
    for b in bindings:
        if not b.get("enabled", True) or not b.get("subscribe"):
            continue
        out.extend(read_channel(team_id, b["channel_name"], limit=limit_per_channel))
    out.sort(key=lambda m: float(m.get("ts") or 0))
    return out[-100:]


def clear_bus(team_id: Optional[str] = None) -> None:
    with _lock:
        if team_id is None:
            _BUS.clear()
        else:
            _BUS.pop(str(team_id), None)


def bus_stats(team_id: Optional[str] = None) -> Dict[str, Any]:
    with _lock:
        if team_id:
            t = _BUS.get(str(team_id)) or {}
            return {
                "team_id": team_id,
                "channels": {k: len(v) for k, v in t.items()},
                "total": sum(len(v) for v in t.values()),
            }
        return {
            "teams": list(_BUS.keys()),
            "total": sum(len(v) for t in _BUS.values() for v in t.values()),
        }
