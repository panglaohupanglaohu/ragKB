# -*- coding: utf-8 -*-
"""关系边集成 — 物竞 timeline 协作证据 → RelationshipStore 建议.

真正的协作拓扑之一：团队页「关系」边（agent_agent / collaborator）。
默认 suggest_only；apply 由 API confirm 后写入，created_by=human_via_eco_feedback。
mate / COURT 不映射为业务协作边。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


CREATED_BY_ECO = "human_via_eco_feedback"
DEFAULT_REL_TYPE = "collaborator"
DEFAULT_KIND = "agent_agent"


def _signals_of(action: Dict[str, Any]) -> List[str]:
    sigs = action.get("signals") or []
    if isinstance(sigs, str):
        return [sigs]
    return [str(s) for s in sigs]


def _is_food_signal(s: str) -> bool:
    su = (s or "").upper()
    return su.startswith("FOOD") or "FOOD@" in su


def _edge_key(src: str, tgt: str) -> Tuple[str, str]:
    return (str(src), str(tgt))


def _existing_set(
    existing_edges: Optional[Iterable[Dict[str, Any]]],
) -> Set[Tuple[str, str, str]]:
    """(source, target, kind) 已存在集合。"""
    out: Set[Tuple[str, str, str]] = set()
    for e in existing_edges or []:
        if not isinstance(e, dict):
            continue
        src = str(e.get("source_agent_id") or e.get("source") or "")
        tgt = str(e.get("target_id") or e.get("target") or "")
        kind = str(e.get("kind") or DEFAULT_KIND)
        if src and tgt:
            out.add((src, tgt, kind))
    return out


def build_channel_collab_edges(
    agent_channels: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    """从 agent.channels 共总线推导「通道协作」边 — 这是真实协作拓扑的一层.

    同一 channel 上 subscribe/publish 的 agent 两两连边（canonical a<b），status=channel。
    与门禁边（RelationshipStore）并列：通道=总线通信能力；门禁=点对点授权。
    二者都是协作关系，只是运行时 enforce 点不同。
    """
    agent_channels = agent_channels or {}
    bus_members: Dict[str, List[str]] = defaultdict(list)
    for aid, chs in agent_channels.items():
        aid = str(aid or "")
        if not aid:
            continue
        seen_names: Set[str] = set()
        for c in chs or []:
            if not isinstance(c, dict):
                continue
            name = str(c.get("channel_name") or c.get("channel") or "").strip()
            if not name or name in seen_names:
                continue
            if not (c.get("subscribe") or c.get("publish") or c.get("enabled", True)):
                continue
            seen_names.add(name)
            bus_members[name].append(aid)

    edges: List[Dict[str, Any]] = []
    seen_pair: Set[Tuple[str, str]] = set()
    for bus, members in bus_members.items():
        members = sorted(set(members))
        if len(members) < 2:
            continue
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                key = (a, b)
                if key in seen_pair:
                    continue
                seen_pair.add(key)
                edges.append({
                    "source_agent_id": a,
                    "target_id": b,
                    "kind": DEFAULT_KIND,
                    "rel_type": DEFAULT_REL_TYPE,
                    "note": f"channel:{bus}",
                    "created_by": "channel_collab",
                    "status": "channel",
                    "layer": "channel",
                    "undirected": True,
                })
    edges.sort(key=lambda x: (x["source_agent_id"], x["target_id"]))
    return edges


# 兼容旧名
build_channel_soft_edges = build_channel_collab_edges


def build_team_collab_edges(
    agent_ids: Optional[List[str]] = None,
    *,
    max_agents: int = 12,
) -> List[Dict[str, Any]]:
    """同队编制协作 mesh — 同队即协作单元（与旧 peer 列表同源）.

    不是「假关系」：组织上同种群/同队 = 协作默认场。
    与门禁边区别：默认编制不自动写 RelationshipStore，避免静默建门禁；
    但 Before 图必须把它当协作关系展示。
    """
    ids = sorted({str(a) for a in (agent_ids or []) if a})
    if len(ids) > max_agents:
        ids = ids[:max_agents]
    edges: List[Dict[str, Any]] = []
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            edges.append({
                "source_agent_id": a,
                "target_id": b,
                "kind": DEFAULT_KIND,
                "rel_type": "peer",
                "note": "team_collab",
                "created_by": "team_collab",
                "status": "peer",
                "layer": "peer",
                "undirected": True,
            })
    return edges


# 兼容旧名
build_peer_soft_edges = build_team_collab_edges


def build_relation_suggestions(
    result: Dict[str, Any],
    *,
    team_id: str = "",
    timeline: Optional[Dict[str, Any]] = None,
    existing_edges: Optional[List[Dict[str, Any]]] = None,
    agent_channels: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    agent_ids: Optional[List[str]] = None,
    top_k: int = 24,
    min_weight: float = 1.0,
    bidirectional_share: bool = True,
    include_soft_before: bool = True,  # 历史参数名；语义=纳入通道/同队协作层
) -> Dict[str, Any]:
    """从 ranking + timeline 生成关系边建议（纯函数）.

    规则（plan §3.5.3）：
    - A shared_to B → A↔B collaborator（默认双向），note=eco:share
    - A 发 FOOD、B followed 同 tick → A→B collaborator，note=eco:follow_food
    - 同 population 且双方高 share+signal 且存活 Top → 弱证据互为 collaborator（默认不勾）
    - mate/COURT 不进关系

    协作关系三层（都是协作，enforce 点不同）：
    - store / 门禁边：RelationshipStore → A2A 点对点门禁
    - channel / 通道协作：共总线 publish/subscribe → 总线通信
    - peer / 同队编制：同 team 即协作单元 → 组织默认场
    """
    ranking = list(result.get("final_ranking") or [])
    ranking = sorted(ranking, key=lambda r: int(r.get("survival_ticks") or 0), reverse=True)
    timeline = timeline or result.get("timeline") or {}
    existing = _existing_set(existing_edges)

    # edge_key -> {weight, reasons:set, evidence counts}
    weights: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(
        lambda: {"weight": 0.0, "reasons": set(), "share_n": 0, "follow_n": 0}
    )

    def _bump(src: str, tgt: str, w: float, reason: str, *, share: bool = False, follow: bool = False) -> None:
        if not src or not tgt or src == tgt:
            return
        # 跳过 COURT-only 伪边：caller 保证不传
        st = weights[_edge_key(src, tgt)]
        st["weight"] += float(w)
        st["reasons"].add(reason)
        if share:
            st["share_n"] += 1
        if follow:
            st["follow_n"] += 1

    for step in timeline.get("steps") or []:
        actions = step.get("actions") or {}
        if not isinstance(actions, dict):
            continue
        # FOOD 信号源（本 tick）
        food_sources: List[str] = []
        for aid, act in actions.items():
            if not isinstance(act, dict):
                continue
            for s in _signals_of(act):
                if _is_food_signal(s):
                    food_sources.append(str(aid))
                    break
        # 分享边
        for aid, act in actions.items():
            if not isinstance(act, dict):
                continue
            shared_to = act.get("shared_to")
            if shared_to:
                src, tgt = str(aid), str(shared_to)
                _bump(src, tgt, 2.0, "share", share=True)
                if bidirectional_share:
                    _bump(tgt, src, 2.0, "share", share=True)
            # 跟随边：follower → 各 FOOD 源 的反向：源→跟随者
            if act.get("followed") and food_sources:
                follower = str(aid)
                for src in food_sources:
                    if src != follower:
                        _bump(src, follower, 1.0, "follow_food", follow=True)

    # 弱证据：同 population 存活 Top + 双方高 share/signal
    top_survivors = [r for r in ranking if int(r.get("survival_ticks") or 0) > 0][:8]
    for i, a in enumerate(top_survivors):
        aid = str(a.get("agent_id") or "")
        if not aid:
            continue
        cg_a = a.get("collab_genome") if isinstance(a.get("collab_genome"), dict) else {}
        share_a = float(cg_a.get("share_tendency") or 0)
        signal_a = float(cg_a.get("signal_tendency") or 0)
        if share_a < 0.65 or signal_a < 0.55:
            continue
        pop_a = str(a.get("population") or "")
        for b in top_survivors[i + 1 :]:
            bid = str(b.get("agent_id") or "")
            if not bid or bid == aid:
                continue
            if pop_a and str(b.get("population") or "") != pop_a:
                continue
            cg_b = b.get("collab_genome") if isinstance(b.get("collab_genome"), dict) else {}
            share_b = float(cg_b.get("share_tendency") or 0)
            signal_b = float(cg_b.get("signal_tendency") or 0)
            if share_b < 0.65 or signal_b < 0.55:
                continue
            # 弱证据：0.5 权重，默认不勾
            _bump(aid, bid, 0.5, "co_survive_genome")
            _bump(bid, aid, 0.5, "co_survive_genome")

    suggestions: List[Dict[str, Any]] = []
    for (src, tgt), st in weights.items():
        w = float(st["weight"])
        if w < float(min_weight) and "co_survive_genome" not in st["reasons"]:
            continue
        # 弱证据单独放行但 default_checked=false；强证据需 weight>=min_weight
        strong = w >= float(min_weight) and (
            "share" in st["reasons"] or "follow_food" in st["reasons"]
        )
        weak_only = not strong and "co_survive_genome" in st["reasons"]
        if not strong and not weak_only:
            continue
        kind = DEFAULT_KIND
        already = (src, tgt, kind) in existing
        reasons = sorted(st["reasons"])
        note = "eco:" + "+".join(reasons)
        default_checked = bool(strong and not already)
        suggestions.append({
            "source_agent_id": src,
            "target_id": tgt,
            "kind": kind,
            "rel_type": DEFAULT_REL_TYPE,
            "note": note,
            "weight": round(w, 2),
            "share_n": int(st["share_n"]),
            "follow_n": int(st["follow_n"]),
            "reasons": reasons,
            "already_exists": already,
            "default_checked": default_checked,
            "created_by": CREATED_BY_ECO,
            "reason": "eco_relation:" + "+".join(reasons),
        })

    suggestions.sort(key=lambda s: (-float(s["weight"]), s["source_agent_id"], s["target_id"]))
    suggestions = suggestions[: max(1, int(top_k))] if suggestions else []

    # Before 分层快照
    before_store: List[Dict[str, Any]] = []
    seen_store: Set[Tuple[str, str, str]] = set()
    for e in existing_edges or []:
        if not isinstance(e, dict):
            continue
        src = str(e.get("source_agent_id") or e.get("source") or "")
        tgt = str(e.get("target_id") or e.get("target") or "")
        kind = str(e.get("kind") or DEFAULT_KIND)
        if not src or not tgt:
            continue
        key = (src, tgt, kind)
        if key in seen_store:
            continue
        seen_store.add(key)
        before_store.append({
            "source_agent_id": src,
            "target_id": tgt,
            "kind": kind,
            "rel_type": str(e.get("rel_type") or DEFAULT_REL_TYPE),
            "note": str(e.get("note") or ""),
            "created_by": str(e.get("created_by") or ""),
            "status": "existing",
            "layer": "store",
        })
    before_store.sort(key=lambda x: (x["source_agent_id"], x["target_id"]))

    # agent_ids 回退：ranking + channels keys
    ids = list(agent_ids or [])
    if not ids:
        ids = [str(r.get("agent_id") or "") for r in ranking if r.get("agent_id")]
        for aid in (agent_channels or {}):
            if aid not in ids:
                ids.append(str(aid))
    before_channel = build_channel_collab_edges(agent_channels) if include_soft_before else []
    # 通道边去掉已在 store 的对（双向任一方向算覆盖）
    store_undirected = {
        tuple(sorted((s, t)))
        for (s, t, _k) in existing
    }
    before_channel = [
        e for e in before_channel
        if tuple(sorted((e["source_agent_id"], e["target_id"]))) not in store_undirected
    ]
    before_peer: List[Dict[str, Any]] = []
    # 同队编制始终是协作关系；若已有通道网则通道优先展示（避免双层全 mesh 糊成一片）
    if include_soft_before and not before_store and not before_channel:
        before_peer = build_team_collab_edges(ids)

    # UI Before：三层协作关系叠加（门禁优先，再通道，再编制）
    before = list(before_store) + list(before_channel) + list(before_peer)
    before_source = (
        "store" if before_store
        else ("channel" if before_channel else ("peer" if before_peer else "empty"))
    )
    note_bits = [
        f"门禁边={len(before_store)}",
        f"通道协作={len(before_channel)}",
        f"同队编制={len(before_peer)}",
        "三层都是协作关系（enforce 点不同）",
    ]
    if before_source == "channel":
        note_bits.append("当前以通道共总线为主协作拓扑（如 aws_ops_bus）")
    elif before_source == "peer":
        note_bits.append("当前以同队编制为主协作拓扑")
    elif before_source == "store":
        note_bits.append("含点对点门禁边")

    return {
        "write_policy": "suggest_only",
        "team_id": team_id,
        "suggestions": suggestions,
        "count": len(suggestions),
        "before": before,
        "before_count": len(before),
        "before_store": before_store,
        "before_store_count": len(before_store),
        "before_channel": before_channel,
        "before_channel_count": len(before_channel),
        "before_peer": before_peer,
        "before_peer_count": len(before_peer),
        "before_source": before_source,
        "before_note": " · ".join(note_bits),
        "policy_note": (
            "协作三层：门禁边(RelationshipStore) + 通道协作(channels) + 同队编制；"
            "物竞写回仅升格/新增门禁边（confirm）；通道写回走 channel-integration；"
            "mate/COURT 不映射业务 collaborator"
        ),
    }


def materialize_relation(
    suggestion: Dict[str, Any],
    *,
    team_id: str = "",
    fingerprint: str = "",
) -> Dict[str, Any]:
    """生成 RelationshipStore.add 用的字段 dict（非 dataclass，便于 API 层组装）."""
    note = str(suggestion.get("note") or suggestion.get("reason") or "eco:feedback")
    if fingerprint:
        note = (note + f" fp:{str(fingerprint)[:12]}").strip()
    return {
        "team_id": team_id or str(suggestion.get("team_id") or ""),
        "kind": str(suggestion.get("kind") or DEFAULT_KIND),
        "source_agent_id": str(suggestion.get("source_agent_id") or ""),
        "target_id": str(suggestion.get("target_id") or ""),
        "rel_type": str(suggestion.get("rel_type") or DEFAULT_REL_TYPE),
        "note": note,
        "created_by": str(suggestion.get("created_by") or CREATED_BY_ECO),
    }
