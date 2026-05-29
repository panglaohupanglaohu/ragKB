# -*- coding: utf-8 -*-
"""广场持久化存储 — 将广场、参与者、讨论及消息序列化到 JSON 文件."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .plaza import (
    Discussion, DiscussionStatus, NicheRole, Participant,
    Plaza, PlazaMessage, SeatTier,
)

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "discussions"


class PlazaStore:
    """JSON 文件持久化: storage/discussions/{plaza_id}.json"""

    def __init__(self, base_dir: Optional[Path] = None):
        self._dir = base_dir or STORAGE_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    # ── 保存 ─────────────────────────────────────────────

    def save_plaza(self, plaza: Plaza):
        """将广场完整状态写入 JSON 文件."""
        data = {
            "id": plaza.id,
            "name": plaza.name,
            "description": plaza.description,
            "diameter": plaza.diameter,
            "height": plaza.height,
            "oculus_diameter": plaza.oculus_diameter,
            "niche_count": plaza.niche_count,
            "seat_tiers": plaza.seat_tiers,
            "visual_mode": plaza.visual_mode,
            "created_at": plaza.created_at,
            "metadata": plaza.metadata,
            "participants": {
                pid: self._serialize_participant(p)
                for pid, p in plaza.participants.items()
            },
            "discussions": {
                did: self._serialize_discussion(d)
                for did, d in plaza.discussions.items()
            },
        }
        path = self._dir / f"{plaza.id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.debug(f"💾 广场已保存: {plaza.name} → {path.name}")

    def save_discussion(self, plaza: Plaza, discussion: Discussion):
        """仅更新广场中某个讨论（增量保存，实际仍全量写入）."""
        self.save_plaza(plaza)

    # ── 加载 ─────────────────────────────────────────────

    def load_all(self) -> Dict[str, Plaza]:
        """加载所有广场."""
        plazas: Dict[str, Plaza] = {}
        for path in self._dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                plaza = self._deserialize_plaza(data)
                plazas[plaza.id] = plaza
                logger.info(f"📂 广场加载: {plaza.name} ({len(plaza.discussions)} 讨论)")
            except Exception as e:
                logger.warning(f"加载广场失败 {path.name}: {e}")
        return plazas

    def list_plazas(self) -> List[Plaza]:
        """返回所有广场列表."""
        return list(self.load_all().values())

    def get_indices(self) -> Dict[str, Dict[str, str]]:
        """返回轻量索引，供路由和测试快速定位广场内容."""
        plazas = self.load_all()
        return {
            "plazas": {pid: plaza.name for pid, plaza in plazas.items()},
            "participants": {
                participant_id: plaza_id
                for plaza_id, plaza in plazas.items()
                for participant_id in plaza.participants
            },
            "discussions": {
                discussion_id: plaza_id
                for plaza_id, plaza in plazas.items()
                for discussion_id in plaza.discussions
            },
        }

    def delete_plaza(self, plaza_id: str):
        path = self._dir / f"{plaza_id}.json"
        if path.exists():
            path.unlink()

    # ── 序列化 ────────────────────────────────────────────

    @staticmethod
    def _serialize_participant(p: Participant) -> dict:
        return {
            "agent_id": p.agent_id,
            "agent_name": p.agent_name,
            "role": p.role,
            "team_id": p.team_id,
            "seat_tier": p.seat_tier.value,
            "niche_role": p.niche_role.value,
            "niche_index": p.niche_index,
            "joined_at": p.joined_at,
        }

    @staticmethod
    def _serialize_discussion(d: Discussion) -> dict:
        return {
            "id": d.id,
            "plaza_id": d.plaza_id,
            "topic": d.topic,
            "description": d.description,
            "status": d.status.value,
            "moderator_agent_id": d.moderator_agent_id,
            "max_rounds": d.max_rounds,
            "current_round": d.current_round,
            "goal": d.goal,
            "summary": d.summary,
            "key_conclusions": d.key_conclusions,
            "plan": d.plan,
            "assigned_team_id": d.assigned_team_id,
            "created_at": d.created_at,
            "started_at": d.started_at,
            "ended_at": d.ended_at,
            "metadata": d.metadata,
            "messages": [
                {
                    "id": m.id,
                    "discussion_id": m.discussion_id,
                    "agent_id": m.agent_id,
                    "agent_name": m.agent_name,
                    "role": m.role,
                    "niche_role": m.niche_role,
                    "content": m.content,
                    "round_number": m.round_number,
                    "reply_to": m.reply_to,
                    "created_at": m.created_at,
                    "metadata": m.metadata,
                }
                for m in d.messages
            ],
        }

    # ── 反序列化 ──────────────────────────────────────────

    @staticmethod
    def _deserialize_plaza(data: dict) -> Plaza:
        plaza = Plaza(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            diameter=data.get("diameter", 60.0),
            height=data.get("height", 30.0),
            oculus_diameter=data.get("oculus_diameter", 9.0),
            niche_count=data.get("niche_count", 12),
            seat_tiers=data.get("seat_tiers", 3),
            visual_mode=data.get("visual_mode", "modern"),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {}),
        )
        # 参与者
        for pid, pdata in data.get("participants", {}).items():
            plaza.participants[pid] = Participant(
                agent_id=pdata["agent_id"],
                agent_name=pdata.get("agent_name", ""),
                role=pdata.get("role", ""),
                team_id=pdata.get("team_id", ""),
                seat_tier=SeatTier(pdata.get("seat_tier", "middle")),
                niche_role=NicheRole(pdata.get("niche_role", "observer")),
                niche_index=pdata.get("niche_index", -1),
                joined_at=pdata.get("joined_at", ""),
            )
        # 讨论
        for did, ddata in data.get("discussions", {}).items():
            disc = Discussion(
                id=ddata["id"],
                plaza_id=ddata.get("plaza_id", plaza.id),
                topic=ddata.get("topic", ""),
                description=ddata.get("description", ""),
                status=DiscussionStatus(ddata.get("status", "open")),
                moderator_agent_id=ddata.get("moderator_agent_id", ""),
                max_rounds=ddata.get("max_rounds", 5),
                current_round=ddata.get("current_round", 0),
                goal=ddata.get("goal", ""),
                summary=ddata.get("summary", ""),
                key_conclusions=ddata.get("key_conclusions", []),
                plan=ddata.get("plan", {}),
                assigned_team_id=ddata.get("assigned_team_id", ""),
                created_at=ddata.get("created_at", ""),
                started_at=ddata.get("started_at"),
                ended_at=ddata.get("ended_at"),
                metadata=ddata.get("metadata", {}),
            )
            # 消息
            for mdata in ddata.get("messages", []):
                disc.messages.append(PlazaMessage(
                    id=mdata.get("id", ""),
                    discussion_id=mdata.get("discussion_id", disc.id),
                    agent_id=mdata.get("agent_id", ""),
                    agent_name=mdata.get("agent_name", ""),
                    role=mdata.get("role", ""),
                    niche_role=mdata.get("niche_role", ""),
                    content=mdata.get("content", ""),
                    round_number=mdata.get("round_number", 0),
                    reply_to=mdata.get("reply_to"),
                    created_at=mdata.get("created_at", ""),
                    metadata=mdata.get("metadata", {}),
                ))
            plaza.discussions[did] = disc
        return plaza
