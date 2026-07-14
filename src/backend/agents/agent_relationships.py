# -*- coding: utf-8 -*-
"""Agent Relationships — 显式关系网络 (AgentsGroupConfig E-C).

参考 Clawith 白皮书 Chapter 5:
- 双关系表: agent_agent (A2A 前置) / agent_human (IM 人类前置)
- 关系只能人工建立，Agent 不能自己加
- 无关系 → 通信拒绝，只返回已授权联系人名单
- render_relationships_md: "我能联系谁" 注入组织上下文
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
REL_DIR = _ROOT / "storage" / "agent_relationships"

REL_KINDS = ("agent_agent", "agent_human")
REL_TYPES = ("collaborator", "supervisor", "subordinate", "reviewer")


@dataclass
class AgentRelationship:
    """显式关系 (EC-1)."""
    rel_id: str = field(default_factory=lambda: f"rel_{uuid.uuid4().hex[:8]}")
    team_id: str = ""
    kind: str = "agent_agent"     # agent_agent | agent_human
    source_agent_id: str = ""
    target_id: str = ""           # agent_id 或 human id
    rel_type: str = "collaborator"
    note: str = ""
    created_by: str = "human"     # 关系只能人工建立
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {"rel_id": self.rel_id, "team_id": self.team_id, "kind": self.kind,
                "source_agent_id": self.source_agent_id, "target_id": self.target_id,
                "rel_type": self.rel_type, "note": self.note,
                "created_by": self.created_by, "created_at": self.created_at}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentRelationship":
        return cls(rel_id=d.get("rel_id") or f"rel_{uuid.uuid4().hex[:8]}",
                   team_id=d.get("team_id", ""), kind=d.get("kind", "agent_agent"),
                   source_agent_id=d.get("source_agent_id", ""),
                   target_id=d.get("target_id", ""),
                   rel_type=d.get("rel_type", "collaborator"),
                   note=d.get("note", ""), created_by=d.get("created_by", "human"),
                   created_at=d.get("created_at", datetime.now(timezone.utc).isoformat()))


class RelationshipStore:
    """关系持久化 (EC-2) — storage/agent_relationships/{team_id}.json."""

    def __init__(self, store_dir: Optional[Path] = None):
        self._dir = store_dir or REL_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, team_id: str) -> Path:
        safe = "".join(c for c in (team_id or "default") if c.isalnum() or c in "-_") or "default"
        return self._dir / f"{safe}.json"

    def _load(self, team_id: str) -> Dict[str, Dict[str, Any]]:
        p = self._path(team_id)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"RelationshipStore 读取失败 ({team_id}): {e}")
            return {}

    def _save(self, team_id: str, data: Dict[str, Dict[str, Any]]) -> None:
        p = self._path(team_id)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)

    def add(self, rel: AgentRelationship) -> Dict[str, Any]:
        if rel.kind not in REL_KINDS:
            return {"ok": False, "error": f"kind 非法: {rel.kind}"}
        if rel.rel_type not in REL_TYPES:
            return {"ok": False, "error": f"rel_type 非法: {rel.rel_type} (允许 {REL_TYPES})"}
        if not rel.source_agent_id or not rel.target_id:
            return {"ok": False, "error": "source_agent_id / target_id 必填"}
        if rel.kind == "agent_agent" and rel.source_agent_id == rel.target_id:
            return {"ok": False, "error": "不能与自己建关系"}
        data = self._load(rel.team_id)
        # 去重 (EC-2)
        for d in data.values():
            if (d.get("kind") == rel.kind
                    and d.get("source_agent_id") == rel.source_agent_id
                    and d.get("target_id") == rel.target_id):
                return {"ok": False, "error": "duplicate", "existing_rel_id": d.get("rel_id")}
        data[rel.rel_id] = rel.to_dict()
        self._save(rel.team_id, data)
        return {"ok": True, "rel_id": rel.rel_id}

    def remove(self, team_id: str, rel_id: str) -> bool:
        data = self._load(team_id)
        if rel_id not in data:
            return False
        del data[rel_id]
        self._save(team_id, data)
        return True

    def list_team(self, team_id: str) -> List[AgentRelationship]:
        return [AgentRelationship.from_dict(d) for d in self._load(team_id).values()]

    def list_for_agent(self, team_id: str, agent_id: str) -> List[AgentRelationship]:
        """双向: 该 agent 作为 source 或 target 的全部关系."""
        result = []
        for d in self._load(team_id).values():
            if d.get("source_agent_id") == agent_id or d.get("target_id") == agent_id:
                result.append(AgentRelationship.from_dict(d))
        return result


# ── 协作拓扑（三层：门禁边 / 同队编制 / 通道协作）──────────

def _channel_names_of(agent: Any) -> List[str]:
    names: List[str] = []
    for c in getattr(agent, "channels", None) or []:
        if hasattr(c, "to_dict"):
            d = c.to_dict()
        elif isinstance(c, dict):
            d = c
        else:
            continue
        name = str(d.get("channel_name") or d.get("channel") or "").strip()
        if not name:
            continue
        if d.get("subscribe") or d.get("publish") or d.get("enabled", True):
            names.append(name)
    return names


def load_team_collab_context(team_id: str) -> Dict[str, Any]:
    """从 team_manager 加载队员 id 与通道绑定（懒导入，避免环依赖）."""
    agent_ids: List[str] = []
    channels_by_agent: Dict[str, List[str]] = {}
    names_by_agent: Dict[str, str] = {}
    roles_by_agent: Dict[str, str] = {}
    try:
        from agents.api import _team_manager  # lazy
        if _team_manager is None:
            return {
                "agent_ids": agent_ids,
                "channels_by_agent": channels_by_agent,
                "names_by_agent": names_by_agent,
                "roles_by_agent": roles_by_agent,
            }
        team = _team_manager.get_team(team_id)
        if team is None:
            return {
                "agent_ids": agent_ids,
                "channels_by_agent": channels_by_agent,
                "names_by_agent": names_by_agent,
                "roles_by_agent": roles_by_agent,
            }
        agents = team.agents.values() if hasattr(team, "agents") and hasattr(team.agents, "values") else []
        for a in agents:
            aid = str(getattr(a, "agent_id", "") or "")
            if not aid:
                continue
            agent_ids.append(aid)
            channels_by_agent[aid] = _channel_names_of(a)
            names_by_agent[aid] = str(getattr(a, "name", "") or aid)
            roles_by_agent[aid] = str(getattr(a, "role", "") or "")
    except Exception as e:
        logger.debug("load_team_collab_context: %s", e)
    return {
        "agent_ids": agent_ids,
        "channels_by_agent": channels_by_agent,
        "names_by_agent": names_by_agent,
        "roles_by_agent": roles_by_agent,
    }


def resolve_collab_path(
    team_id: str,
    from_agent_id: str,
    to_agent_id: str,
    *,
    store: Optional[RelationshipStore] = None,
    team_ctx: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """解析 A→B 是否存在协作路径（三层任一即可）.

    返回 allowed + layers 命中列表 + reason + allowed_contacts。
    """
    if from_agent_id == to_agent_id:
        return {
            "allowed": True,
            "reason": "self",
            "layers": ["self"],
            "allowed_contacts": [],
            "contact_layers": {},
        }

    store = store or get_relationship_store()
    ctx = team_ctx if team_ctx is not None else load_team_collab_context(team_id)
    team_ids = set(ctx.get("agent_ids") or [])
    ch_map: Dict[str, List[str]] = ctx.get("channels_by_agent") or {}

    contact_layers: Dict[str, List[str]] = {}  # contact -> [layer, ...]

    def _add_contact(cid: str, layer: str) -> None:
        if not cid or cid == from_agent_id:
            return
        contact_layers.setdefault(cid, [])
        if layer not in contact_layers[cid]:
            contact_layers[cid].append(layer)

    # Layer 1: RelationshipStore 门禁边
    rels = store.list_for_agent(team_id, from_agent_id)
    for r in rels:
        if r.kind != "agent_agent":
            continue
        other = r.target_id if r.source_agent_id == from_agent_id else r.source_agent_id
        _add_contact(other, f"store:{r.rel_type}")

    # Layer 2: 同队编制 peer
    for aid in team_ids:
        if aid != from_agent_id:
            _add_contact(aid, "team_peer")

    # Layer 3: 共总线通道协作
    my_ch = set(ch_map.get(from_agent_id) or [])
    if my_ch:
        for aid, chs in ch_map.items():
            if aid == from_agent_id:
                continue
            shared = my_ch.intersection(chs or [])
            if shared:
                bus = sorted(shared)[0]
                _add_contact(aid, f"channel:{bus}")

    allowed_contacts = sorted(contact_layers.keys())
    layers_hit: List[str] = list(contact_layers.get(to_agent_id) or [])

    if layers_hit:
        # 优先 reason 用 store > channel > peer
        primary = layers_hit[0]
        for pref in ("store:", "channel:", "team_peer"):
            matched = [x for x in layers_hit if x.startswith(pref) or x == pref]
            if matched:
                primary = matched[0]
                break
        return {
            "allowed": True,
            "reason": primary,
            "layers": layers_hit,
            "allowed_contacts": allowed_contacts,
            "contact_layers": contact_layers,
        }

    return {
        "allowed": False,
        "reason": "no_collab_path: 无门禁边/同队/共总线",
        "layers": [],
        "allowed_contacts": allowed_contacts,
        "contact_layers": contact_layers,
    }


# ── EC-3: 通信门禁 ─────────────────────────────────────────

def check_can_communicate(team_id: str, from_agent_id: str, to_agent_id: str,
                          store: Optional[RelationshipStore] = None,
                          **kwargs: Any) -> Dict[str, Any]:
    """A2A 通信检查：协作三层任一命中则允许（门禁边 / 同队 / 共总线）."""
    path = resolve_collab_path(
        team_id, from_agent_id, to_agent_id,
        store=store,
        team_ctx=kwargs.get("team_ctx"),
    )
    return {
        "allowed": path["allowed"],
        "reason": path["reason"],
        "layers": path.get("layers") or [],
        "allowed_contacts": path.get("allowed_contacts") or [],
        "contact_layers": path.get("contact_layers") or {},
    }


# ── EC-4: 软/硬门禁 ────────────────────────────────────────

def relationship_gate_mode() -> str:
    try:
        settings_path = _ROOT / "config" / "settings.json"
        if settings_path.exists():
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            if data.get("enforce_relationship_gate", False):
                return "hard"
    except Exception:
        pass
    return "soft"


def _gate_mode() -> str:
    return relationship_gate_mode()


def gate_delegate(team_id: str, from_agent_id: str, to_agent_id: str,
                  **kwargs: Any) -> Dict[str, Any]:
    """委派/消息/交接门禁: soft=记警告放行 / hard=拒绝 (EC-4).

    允许路径：门禁边 OR 同队编制 OR 共总线。
    """
    check = check_can_communicate(team_id, from_agent_id, to_agent_id, **kwargs)
    mode = _gate_mode()
    if check["allowed"]:
        return {
            "allowed": True,
            "mode": mode,
            "reason": check["reason"],
            "layers": check.get("layers") or [],
        }
    if mode == "hard":
        return {
            "allowed": False,
            "mode": "hard",
            "reason": check["reason"],
            "allowed_contacts": check.get("allowed_contacts") or [],
            "layers": [],
        }
    logger.warning(
        "⚠️ 软门禁放行无协作路径委派: %s → %s (team=%s)",
        from_agent_id, to_agent_id, team_id,
    )
    return {
        "allowed": True,
        "mode": "soft",
        "warning": (
            f"无协作路径 ({from_agent_id} → {to_agent_id})："
            f"非同队、无共总线、无门禁边。settings.enforce_relationship_gate=true 时将拒绝"
        ),
        "reason": check["reason"],
        "layers": [],
    }


def gate_workflow_handoff(
    team_id: str,
    from_agent_id: str,
    to_agent_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """工作流步骤交接门禁（同 gate_delegate，语义=step handoff）."""
    result = gate_delegate(team_id, from_agent_id, to_agent_id, **kwargs)
    result["kind"] = "workflow_handoff"
    return result


# ── EC-5: relationships.md 渲染 ────────────────────────────

def render_relationships_md(team_id: str, agent_id: str,
                            store: Optional[RelationshipStore] = None) -> str:
    """生成"我能联系谁"清单（协作三层），注入组织上下文 / 任务 prompt."""
    store = store or get_relationship_store()
    ctx = load_team_collab_context(team_id)
    # to 用哨兵 id，只取 contact_layers 全量通讯录
    path = resolve_collab_path(
        team_id, agent_id, "__none__", store=store, team_ctx=ctx,
    )
    contact_layers: Dict[str, List[str]] = path.get("contact_layers") or {}
    names = ctx.get("names_by_agent") or {}
    roles = ctx.get("roles_by_agent") or {}

    if not contact_layers:
        return (
            "（协作拓扑为空：无同队成员、无通道绑定、无门禁边。"
            "同队/共总线/门禁边任一建立后即可协作通信。）"
        )

    type_label = {
        "collaborator": "协作者", "supervisor": "上级",
        "subordinate": "下属", "reviewer": "评审人", "peer": "同队编制",
    }
    groups: Dict[str, List[str]] = {}
    for other, layers in sorted(contact_layers.items()):
        label_bits = []
        for ly in layers:
            if ly.startswith("store:"):
                rt = ly.split(":", 1)[1]
                label_bits.append(type_label.get(rt, rt))
            elif ly.startswith("channel:"):
                label_bits.append(f"通道:{ly.split(':', 1)[1]}")
            elif ly == "team_peer":
                label_bits.append("同队编制")
            else:
                label_bits.append(ly)
        nm = names.get(other) or other
        role = roles.get(other) or ""
        role_s = f" · {role}" if role else ""
        line = f"- 🤖 {nm} (`{other}`{role_s}) — {', '.join(label_bits)}"
        # 归组：优先门禁类型
        gkey = "协作联系人"
        for ly in layers:
            if ly.startswith("store:"):
                gkey = type_label.get(ly.split(":", 1)[1], "协作者")
                break
            if ly.startswith("channel:"):
                gkey = "通道协作"
                break
            if ly == "team_peer":
                gkey = "同队编制"
        groups.setdefault(gkey, []).append(line)

    # 门禁边备注
    for r in store.list_for_agent(team_id, agent_id):
        if r.kind == "agent_human":
            groups.setdefault("人类联系人", []).append(
                f"- 👤 {r.target_id} — {type_label.get(r.rel_type, r.rel_type)}"
                + (f"（{r.note}）" if r.note else "")
            )

    out = ["## 协作拓扑（任务执行生效）", ""]
    for label, lines in groups.items():
        out.append(f"### {label}")
        out.extend(lines)
        out.append("")
    out.append(
        "规则：可委派/交接/发消息的对象须在上述名单内（同队编制、共总线、门禁边任一即可）。"
        " hard 门禁下名单外对象会被拒绝。"
    )
    return "\n".join(out)


def collab_topology_for_prompt(team_id: str, agent_id: str) -> str:
    """供任务 step prompt 注入的短协作拓扑块."""
    return render_relationships_md(team_id, agent_id)


# ── 单例 ──────────────────────────────────────────────────

_store: Optional[RelationshipStore] = None


def get_relationship_store() -> RelationshipStore:
    global _store
    if _store is None:
        _store = RelationshipStore()
    return _store


def reset_relationship_store(**kwargs) -> RelationshipStore:
    global _store
    _store = RelationshipStore(**kwargs)
    return _store
