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
        tmp.rename(p)

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


# ── EC-3: 通信门禁 ─────────────────────────────────────────

def check_can_communicate(team_id: str, from_agent_id: str, to_agent_id: str,
                          store: Optional[RelationshipStore] = None) -> Dict[str, Any]:
    """A2A 通信检查：无关系 → 拒绝并只返回已授权联系人（白皮书受限提示）."""
    if from_agent_id == to_agent_id:
        return {"allowed": True, "reason": "self", "allowed_contacts": []}
    store = store or get_relationship_store()
    rels = store.list_for_agent(team_id, from_agent_id)
    allowed_contacts = sorted({
        (r.target_id if r.source_agent_id == from_agent_id else r.source_agent_id)
        for r in rels if r.kind == "agent_agent"
    })
    for r in rels:
        if r.kind != "agent_agent":
            continue
        pair = {r.source_agent_id, r.target_id}
        if {from_agent_id, to_agent_id} == pair:
            return {"allowed": True, "reason": f"relationship:{r.rel_type}",
                    "allowed_contacts": allowed_contacts}
    return {"allowed": False,
            "reason": "no_relationship: 关系只能由人工在配置页建立",
            "allowed_contacts": allowed_contacts}


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


def gate_delegate(team_id: str, from_agent_id: str, to_agent_id: str) -> Dict[str, Any]:
    """委派门禁: soft=记警告放行 / hard=拒绝 (EC-4)."""
    check = check_can_communicate(team_id, from_agent_id, to_agent_id)
    mode = _gate_mode()
    if check["allowed"]:
        return {"allowed": True, "mode": mode, "reason": check["reason"]}
    if mode == "hard":
        return {"allowed": False, "mode": "hard", "reason": check["reason"],
                "allowed_contacts": check["allowed_contacts"]}
    logger.warning(f"⚠️ 软门禁放行无关系委派: {from_agent_id} → {to_agent_id} (team={team_id})")
    return {"allowed": True, "mode": "soft",
            "warning": f"无显式关系 ({from_agent_id} → {to_agent_id})，建议在配置页建立关系。"
                       f"settings.enforce_relationship_gate=true 时此委派将被拒绝",
            "reason": check["reason"]}


# ── EC-5: relationships.md 渲染 ────────────────────────────

def render_relationships_md(team_id: str, agent_id: str,
                            store: Optional[RelationshipStore] = None) -> str:
    """生成"我能联系谁"清单，注入组织上下文."""
    store = store or get_relationship_store()
    rels = store.list_for_agent(team_id, agent_id)
    if not rels:
        return "（尚未建立任何关系——所有关系需人工在团队配置页建立；无关系时不能主动联系其他 Agent）"
    groups: Dict[str, List[str]] = {}
    type_label = {"collaborator": "协作者", "supervisor": "上级",
                  "subordinate": "下属", "reviewer": "评审人"}
    for r in rels:
        other = r.target_id if r.source_agent_id == agent_id else r.source_agent_id
        direction = "→" if r.source_agent_id == agent_id else "←"
        kind_tag = "👤人类" if r.kind == "agent_human" else "🤖Agent"
        line = f"- {kind_tag} {other} {direction} {type_label.get(r.rel_type, r.rel_type)}"
        if r.note:
            line += f"（{r.note}）"
        groups.setdefault(type_label.get(r.rel_type, r.rel_type), []).append(line)
    out = []
    for label, lines in groups.items():
        out.append(f"### {label}")
        out.extend(lines)
    out.append("\n规则：只能联系上述名单；联系名单外对象会被拒绝。")
    return "\n".join(out)


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
