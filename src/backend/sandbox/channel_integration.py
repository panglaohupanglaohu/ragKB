# -*- coding: utf-8 -*-
"""通道绑定集成 — 物竞协作证据 → agent.channels diff.

真正的协作拓扑之一：团队页「通道绑定」。
默认 suggest_only；apply 由 API confirm 后合并写回。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional


def _clamp01(x: Any) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        v = 0.5
    return max(0.0, min(1.0, v))


def default_team_bus(team_id: str) -> str:
    safe = "".join(c for c in (team_id or "team") if c.isalnum() or c in "-_") or "team"
    return f"{safe}_bus"


def resolve_team_bus(
    team_id: str,
    agent_channels: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    bus_name: str = "",
) -> str:
    """解析团队主总线名：显式 bus_name > 已有绑定中出现最多的 channel_name > default_team_bus.

    关键：aws-ops 真身用 aws_ops_bus，而 default_team_bus('aws-ops')=aws-ops_bus（连字符），
    若写回新建总线，运行时 publish/subscribe 仍打旧名 → 写回等于没生效。
    """
    if (bus_name or "").strip():
        return str(bus_name).strip()
    counts: Dict[str, int] = defaultdict(int)
    for chs in (agent_channels or {}).values():
        for c in chs or []:
            if not isinstance(c, dict):
                name = str(getattr(c, "channel_name", None) or getattr(c, "channel", None) or "").strip()
            else:
                name = str(c.get("channel_name") or c.get("channel") or "").strip()
            if name:
                counts[name] += 1
    if counts:
        # 优先 *_bus / *bus 名
        ranked = sorted(
            counts.items(),
            key=lambda kv: (
                0 if kv[0].endswith("_bus") or kv[0].endswith("bus") else 1,
                -kv[1],
                kv[0],
            ),
        )
        return ranked[0][0]
    return default_team_bus(team_id)


def _signals_of(action: Dict[str, Any]) -> List[str]:
    sigs = action.get("signals") or []
    if isinstance(sigs, str):
        return [sigs]
    return [str(s) for s in sigs]


def build_channel_suggestions(
    result: Dict[str, Any],
    *,
    team_id: str = "",
    timeline: Optional[Dict[str, Any]] = None,
    agent_channels: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    top_k: int = 12,
    bus_name: str = "",
) -> Dict[str, Any]:
    """从 ranking collab_genome + timeline 动作生成通道 diff 建议.

    规则：
    - 高 signal / 多次 FOOD|HELP 信号 → bus publish
    - 高 follow / followed → bus subscribe
    - 高 share / shared_to → bus subscribe+publish，priority+
    - mate 不进通道
    """
    ranking = list(result.get("final_ranking") or [])
    ranking = sorted(ranking, key=lambda r: int(r.get("survival_ticks") or 0), reverse=True)
    timeline = timeline or result.get("timeline") or {}
    agent_channels = agent_channels or {}
    bus = resolve_team_bus(team_id, agent_channels, bus_name=bus_name)

    # 从 timeline 统计表达型
    stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
        "food_signals": 0, "help_signals": 0, "followed": 0, "shared": 0,
    })
    for step in timeline.get("steps") or []:
        actions = step.get("actions") or {}
        if not isinstance(actions, dict):
            continue
        for aid, act in actions.items():
            if not isinstance(act, dict):
                continue
            st = stats[str(aid)]
            for s in _signals_of(act):
                su = s.upper()
                if su.startswith("FOOD") or "FOOD@" in su:
                    st["food_signals"] += 1
                if su == "HELP" or su.startswith("HELP"):
                    st["help_signals"] += 1
            if act.get("followed"):
                st["followed"] += 1
            if act.get("shared_to"):
                st["shared"] += 1

    suggestions: List[Dict[str, Any]] = []
    for r in ranking[: max(1, top_k)]:
        aid = str(r.get("agent_id") or "")
        if not aid:
            continue
        cg = r.get("collab_genome") if isinstance(r.get("collab_genome"), dict) else {}
        share = _clamp01(cg.get("share_tendency", 0.5))
        signal = _clamp01(cg.get("signal_tendency", 0.5))
        follow = _clamp01(cg.get("follow_tendency", 0.5))
        st = stats.get(aid) or stats.get(aid.split("@")[0]) or {
            "food_signals": 0, "help_signals": 0, "followed": 0, "shared": 0,
        }
        # 模糊匹配 timeline id
        if st["food_signals"] == 0 and st["followed"] == 0 and st["shared"] == 0:
            for k, v in stats.items():
                if aid.startswith(k) or k.startswith(aid[:8]) or k in aid or aid in k:
                    st = v
                    break

        want_pub = signal >= 0.55 or st["food_signals"] + st["help_signals"] >= 1
        want_sub = follow >= 0.55 or st["followed"] >= 1 or share >= 0.55 or st["shared"] >= 1
        if share >= 0.6 or st["shared"] >= 1:
            want_pub = True
            want_sub = True
        if not want_pub and not want_sub:
            # 存活适者至少给 subscribe，避免空建议
            if int(r.get("survival_ticks") or 0) > 0:
                want_sub = True
            else:
                continue

        priority = 0
        if st["shared"] or share >= 0.7:
            priority = max(priority, 6)
        if st["food_signals"] or signal >= 0.7:
            priority = max(priority, 5)
        if st["followed"] or follow >= 0.7:
            priority = max(priority, 4)

        existing = list(agent_channels.get(aid) or [])
        # 模糊 existing
        if not existing:
            for k, chs in agent_channels.items():
                if aid.startswith(k) or k.startswith(aid[:8]):
                    existing = list(chs)
                    break
        cur = None
        for c in existing:
            name = str((c or {}).get("channel_name") or (c or {}).get("channel") or "")
            if name == bus:
                cur = c
                break

        already_ok = False
        if cur:
            already_ok = (
                bool(cur.get("subscribe")) == want_sub
                and bool(cur.get("publish")) == want_pub
                and bool(cur.get("enabled", True))
            )

        reasons = []
        if signal >= 0.55 or st["food_signals"] or st["help_signals"]:
            reasons.append("signal")
        if follow >= 0.55 or st["followed"]:
            reasons.append("follow")
        if share >= 0.55 or st["shared"]:
            reasons.append("share")
        if not reasons:
            reasons.append("survivor_default_sub")

        diff = {
            "channel_name": bus,
            "subscribe": want_sub,
            "publish": want_pub,
            "enabled": True,
            "priority": priority,
            "source": "eco_drill",
            "note": "eco:" + "+".join(reasons),
        }
        suggestions.append({
            "agent_id": aid,
            "population": r.get("population") or "",
            "survival_ticks": int(r.get("survival_ticks") or 0),
            "channel_diffs": [diff],
            "already_satisfied": already_ok,
            "stats": dict(st),
            "collab_snapshot": {
                "share_tendency": share,
                "signal_tendency": signal,
                "follow_tendency": follow,
            },
            "reason": "eco_channel:" + "+".join(reasons),
        })

    return {
        "write_policy": "suggest_only",
        "team_id": team_id,
        "bus_name": bus,
        "suggestions": suggestions,
        "count": len(suggestions),
        "policy_note": "通道 diff 合并写 agent.channels；confirm 后持久化；运行时 agent_channel_bus 强制 publish/subscribe",
    }
