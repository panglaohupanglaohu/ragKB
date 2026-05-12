# -*- coding: utf-8 -*-
"""
AgentsGroup2026 — Skill Extraction WebSocket Channel.

Provides real-time WebSocket push for the skill extraction timeline UI:
- Timeline operation log nodes (extraction steps)
- Completion cards with real-time records + review annotations
- Phase step progress with lock states
- Card status updates (pending → recording → reviewing → done)

WebSocket protocol:
  Client → Server: {"type": "subscribe", "team_id": "<id>", "extraction_id": "<id>"}
  Server → Client: {"type": "log_node", ...}
  Server → Client: {"type": "card_update", ...}
  Server → Client: {"type": "phase_progress", ...}
  Server → Client: {"type": "extraction_completed", ...}
  Server → Client: {"type": "error", "message": "..."}
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════


class TimelinePhase:
    """Phase of the skill extraction pipeline."""

    EXTRACT = "extract"
    LLM_PREFILL = "llm_prefill"
    REVIEW = "review"
    APPROVE = "approve"
    INDEX = "index"
    VERIFY = "verify"
    COMPLETE = "complete"

    ORDER = [EXTRACT, LLM_PREFILL, REVIEW, APPROVE, INDEX, VERIFY, COMPLETE]

    @classmethod
    def index_of(cls, phase: str) -> int:
        try:
            return cls.ORDER.index(phase)
        except ValueError:
            return -1


class CardStatus:
    """Completion card lifecycle status."""

    PENDING = "pending"
    RECORDING = "recording"
    RECORDED = "recorded"
    REVIEWING = "reviewing"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"


class LockReason:
    """Reasons a phase step card can be locked."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    WAITING_REVIEW = "waiting_review"
    WAITING_APPROVAL = "waiting_approval"
    DEPENDENCY_BLOCKED = "dependency_blocked"
    COMPLETED = "completed"


# ═══════════════════════════════════════════════════════════════════
# WebSocket Connection Manager
# ═══════════════════════════════════════════════════════════════════


class SkillExtractWSManager:
    """Manages WebSocket connections for skill extraction timeline."""

    def __init__(self):
        # team_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        # extraction_id -> extraction state cache
        self._extractions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, team_id: str):
        """Register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            if team_id not in self._connections:
                self._connections[team_id] = set()
            self._connections[team_id].add(websocket)
        logger.info(f"🔌 SkillExtractWS: connected team={team_id} (total={len(self._connections.get(team_id, set()))})")

    async def disconnect(self, websocket: WebSocket, team_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if team_id in self._connections:
                self._connections[team_id].discard(websocket)
                if not self._connections[team_id]:
                    del self._connections[team_id]
        logger.info(f"🔌 SkillExtractWS: disconnected team={team_id}")

    async def broadcast_to_team(self, team_id: str, message: Dict[str, Any]):
        """Send a message to all connections for a team."""
        dead: List[WebSocket] = []
        async with self._lock:
            connections = list(self._connections.get(team_id, set()))
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.get(team_id, set()).discard(ws)

    async def push_log_node(
        self,
        team_id: str,
        extraction_id: str,
        node_id: str,
        phase: str,
        title: str,
        description: str = "",
        status: str = CardStatus.PENDING,
        agent_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Push a new operation log node to the timeline."""
        msg = {
            "type": "log_node",
            "extraction_id": extraction_id,
            "node_id": node_id,
            "phase": phase,
            "phase_order": TimelinePhase.index_of(phase),
            "title": title,
            "description": description,
            "status": status,
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        await self.broadcast_to_team(team_id, msg)

    async def push_card_update(
        self,
        team_id: str,
        extraction_id: str,
        node_id: str,
        card_type: str,
        status: str,
        realtime_record: str = "",
        review_annotation: str = "",
        reviewer: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Push a completion card status update."""
        msg = {
            "type": "card_update",
            "extraction_id": extraction_id,
            "node_id": node_id,
            "card_type": card_type,
            "status": status,
            "realtime_record": realtime_record,
            "review_annotation": review_annotation,
            "reviewer": reviewer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        await self.broadcast_to_team(team_id, msg)

    async def push_phase_progress(
        self,
        team_id: str,
        extraction_id: str,
        phase: str,
        progress_pct: float,
        is_locked: bool = False,
        lock_reason: str = "",
        step_label: str = "",
        step_detail: str = "",
    ):
        """Push phase step progress with lock state."""
        msg = {
            "type": "phase_progress",
            "extraction_id": extraction_id,
            "phase": phase,
            "phase_order": TimelinePhase.index_of(phase),
            "progress_pct": round(progress_pct, 1),
            "is_locked": is_locked,
            "lock_reason": lock_reason,
            "step_label": step_label,
            "step_detail": step_detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_to_team(team_id, msg)

    async def push_extraction_completed(self, team_id: str, extraction_id: str, summary: Dict[str, Any]):
        """Push extraction completion event."""
        msg = {
            "type": "extraction_completed",
            "extraction_id": extraction_id,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_to_team(team_id, msg)

    async def push_error(self, team_id: str, extraction_id: str, message: str, detail: str = ""):
        """Push error event."""
        msg = {
            "type": "error",
            "extraction_id": extraction_id,
            "message": message,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_to_team(team_id, msg)

    def get_extraction_state(self, extraction_id: str) -> Optional[Dict[str, Any]]:
        return self._extractions.get(extraction_id)

    def set_extraction_state(self, extraction_id: str, state: Dict[str, Any]):
        self._extractions[extraction_id] = state


# ═══════════════════════════════════════════════════════════════════
# Singleton + WebSocket Route Handler
# ═══════════════════════════════════════════════════════════════════

_ws_manager: Optional[SkillExtractWSManager] = None
_lock = asyncio.Lock()


def get_ws_manager() -> SkillExtractWSManager:
    """Get or create the singleton WebSocket manager."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = SkillExtractWSManager()
    return _ws_manager


async def skill_extract_ws_endpoint(websocket: WebSocket, team_id: str = "default"):
    """FastAPI WebSocket endpoint for skill extraction timeline.

    Client sends:
      {"type": "subscribe", "extraction_id": "<id>"}

    Server pushes events as they occur.
    """
    manager = get_ws_manager()
    await manager.connect(websocket, team_id)

    # Send initial connection ack
    try:
        await websocket.send_json({
            "type": "connected",
            "team_id": team_id,
            "message": "技能萃取时间轴 WebSocket 已连接",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        await manager.disconnect(websocket, team_id)
        return

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

            msg_type = data.get("type", "")
            extraction_id = data.get("extraction_id", "")

            if msg_type == "subscribe":
                if extraction_id:
                    state = manager.get_extraction_state(extraction_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "extraction_id": extraction_id,
                        "current_state": state,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            elif msg_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected: team={team_id}")
    except Exception as e:
        logger.error(f"WebSocket error team={team_id}: {e}")
    finally:
        await manager.disconnect(websocket, team_id)
