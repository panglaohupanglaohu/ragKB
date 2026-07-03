# -*- coding: utf-8 -*-
"""Lightweight datacenter ratchet API used by the self-evolving frontend."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/datacenter", tags=["datacenter"])
ws_router = APIRouter()

BASELINE_PUE = 1.85
TARGET_PUE = 1.30


@dataclass
class Policy:
    policy_id: str
    title: str
    kind: str
    rationale: str
    score: float
    expected_saving_kwh_day: float
    expected_saving_cny_year: float
    delta_pue: float
    applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "title": self.title,
            "kind": self.kind,
            "rationale": self.rationale,
            "score": self.score,
            "expected_saving_kwh_day": self.expected_saving_kwh_day,
            "expected_saving_cny_year": self.expected_saving_cny_year,
        }


class EvolveRequest(BaseModel):
    title: str
    category: str = "general"
    delta_pue: float = Field(default=-0.005)
    delta_kwh_day: float = Field(default=8.0)


class PolicyApplyRequest(BaseModel):
    policy_id: str
    fitness: float = 0.88


class DatacenterRatchetService:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._clients: Set[WebSocket] = set()
        self.reset()

    def reset(self) -> None:
        self.current_pue = BASELINE_PUE
        self.evolution_round = 0
        self.skill_count = 12
        self._heritage: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []
        now = time.time()
        self._pue_history: List[Dict[str, Any]] = [{"ts": now, "pue": self.current_pue}]
        self._policies = [
            Policy("pol-freecooling", "夜间自由冷却切换", "save_outgo", "利用夜间低温外气减少压缩机制冷时长。", 9.6, 18.0, 15800.0, 0.012),
            Policy("pol-airflow", "冷热通道风量重平衡", "save_outgo", "重排送风优先级并压缩过冷区浪费。", 9.2, 13.5, 12400.0, 0.009),
            Policy("pol-plc", "CRAC 变频细粒度调节", "open_source", "按热岛波动动态调节 PLC 风机频率。", 8.8, 11.4, 9800.0, 0.007),
            Policy("pol-loadshift", "低优先级任务移峰", "open_source", "把非关键批任务移到夜间低价低温时段。", 8.1, 9.6, 8600.0, 0.006),
            Policy("pol-rackseal", "机柜封堵与缝隙治理", "save_outgo", "减少冷热空气短路，提升送风利用率。", 7.8, 7.5, 6200.0, 0.005),
        ]

    def _ts(self) -> float:
        return time.time()

    def _status(self) -> Dict[str, Any]:
        saving = sum(item.get("delta_kwh_day", 0.0) for item in self._heritage)
        return {
            "current_pue": self.current_pue,
            "evolution_round": self.evolution_round,
            "heritage_count": len(self._heritage),
            "saving_kwh_day": saving,
            "co2_saved_ton_year": saving * 365 * 0.00042,
            "skill_count": self.skill_count,
            "policy_count": len(self._policies),
            "policies_applied": sum(1 for policy in self._policies if policy.applied),
        }

    def _append_event(self, kind: str, data: Dict[str, Any]) -> Dict[str, Any]:
        event = {"ts": self._ts(), "kind": kind, "data": data}
        self._events.append(event)
        self._events = self._events[-120:]
        return event

    def _append_history(self) -> None:
        self._pue_history.append({"ts": self._ts(), "pue": self.current_pue})
        self._pue_history = self._pue_history[-400:]

    async def _broadcast_tick(self, new_events: List[Dict[str, Any]]) -> None:
        if not self._clients:
            return
        payload = {"type": "tick", "status": self._status(), "new_events": new_events}
        stale: List[WebSocket] = []
        for client in self._clients:
            try:
                await client.send_json(payload)
            except Exception:
                stale.append(client)
        for client in stale:
            self._clients.discard(client)

    async def register(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def unregister(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def get_status(self) -> Dict[str, Any]:
        async with self._lock:
            return self._status()

    async def get_recommendations(self, top_n: int) -> List[Dict[str, Any]]:
        async with self._lock:
            policies = [policy.to_dict() for policy in self._policies if not policy.applied]
            return policies[:top_n]

    async def get_heritage(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self._heritage)

    async def get_events(self, limit: int) -> List[Dict[str, Any]]:
        async with self._lock:
            return self._events[-limit:]

    async def get_pue_history(self, limit: int) -> List[Dict[str, Any]]:
        async with self._lock:
            return self._pue_history[-limit:]

    async def apply_policy(self, policy_id: str, fitness: float) -> Dict[str, Any]:
        async with self._lock:
            for policy in self._policies:
                if policy.policy_id != policy_id:
                    continue
                policy.applied = True
                event = self._append_event(
                    "policy_applied",
                    {"policy_id": policy_id, "fitness": fitness},
                )
                status = self._status()
                break
            else:
                event = self._append_event("policy_applied", {"policy_id": policy_id, "fitness": fitness})
                status = self._status()
        await self._broadcast_tick([event])
        return {"ok": True, "status": status}

    async def loop_tick(self) -> Dict[str, Any]:
        async with self._lock:
            baseline_pue = self.current_pue
            decided = next((policy for policy in self._policies if not policy.applied), None)
            if decided is None:
                result = {
                    "snapshot": {"thermal": 1, "power": 1, "flow": 1, "capacity": 1},
                    "decided_policy": "",
                    "adjustment": None,
                    "current_pue": self.current_pue,
                    "baseline_pue": baseline_pue,
                    "verified": False,
                }
                event = self._append_event(
                    "closed_loop_tick",
                    {"decided_policy": "", "current_pue": self.current_pue, "verified": False},
                )
            else:
                decided.applied = True
                self.evolution_round += 1
                self.current_pue = max(TARGET_PUE, round(self.current_pue - decided.delta_pue, 4))
                self._append_history()
                result = {
                    "snapshot": {"thermal": 1, "power": 1, "flow": 1, "capacity": 1},
                    "decided_policy": decided.policy_id,
                    "adjustment": {"current_pue": self.current_pue},
                    "current_pue": self.current_pue,
                    "baseline_pue": baseline_pue,
                    "verified": self.current_pue < baseline_pue,
                }
                event = self._append_event(
                    "closed_loop_tick",
                    {
                        "decided_policy": decided.policy_id,
                        "current_pue": self.current_pue,
                        "baseline_pue": baseline_pue,
                        "verified": result["verified"],
                    },
                )
        await self._broadcast_tick([event])
        return result

    async def evolve(self, req: EvolveRequest) -> Dict[str, Any]:
        async with self._lock:
            heritage_id = f"h-{len(self._heritage) + 1}"
            item = {
                "heritage_id": heritage_id,
                "title": req.title,
                "category": req.category,
                "delta_pue": req.delta_pue,
                "delta_kwh_day": req.delta_kwh_day,
                "locked_at": self._ts(),
            }
            self._heritage.append(item)
            event = self._append_event(
                "darwin_evolve",
                {"heritage_id": heritage_id, "delta_pue": req.delta_pue},
            )
            status = self._status()
        await self._broadcast_tick([event])
        return {"ok": True, "heritage": item, "status": status}


_service = DatacenterRatchetService()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    return await _service.get_status()


@router.get("/recommend")
async def get_recommendations(top_n: int = 9) -> Dict[str, Any]:
    return {"recommendations": await _service.get_recommendations(top_n)}


@router.get("/heritage")
async def get_heritage() -> Dict[str, Any]:
    return {"heritage": await _service.get_heritage()}


@router.get("/events")
async def get_events(limit: int = 30) -> Dict[str, Any]:
    return {"events": await _service.get_events(limit)}


@router.get("/pue-history")
async def get_pue_history(limit: int = 240) -> Dict[str, Any]:
    return {"history": await _service.get_pue_history(limit)}


@router.post("/loop/tick")
async def post_loop_tick() -> Dict[str, Any]:
    return await _service.loop_tick()


@router.post("/evolve")
async def post_evolve(req: EvolveRequest) -> Dict[str, Any]:
    return await _service.evolve(req)


@router.post("/policies/apply")
async def post_apply_policy(req: PolicyApplyRequest) -> Dict[str, Any]:
    return await _service.apply_policy(req.policy_id, req.fitness)


@ws_router.websocket("/ws/datacenter")
async def datacenter_events_ws(websocket: WebSocket) -> None:
    await _service.register(websocket)
    try:
        await websocket.send_json({"type": "tick", "status": await _service.get_status(), "new_events": []})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _service.unregister(websocket)
