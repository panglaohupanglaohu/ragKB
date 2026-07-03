# -*- coding: utf-8 -*-
"""Ratchet API — 全局正向棘轮账本 (全局优化 G4-4)."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .ratchet_ledger import get_ratchet_ledger

router = APIRouter(prefix="/api/v1/ratchet", tags=["ratchet"])


class ForceResetRequest(BaseModel):
    reason: str = ""


@router.get("/metrics")
async def list_metrics(prefix: str = Query(default="")) -> Dict[str, Any]:
    """全部棘轮指标（系统演进史数据源）."""
    metrics = get_ratchet_ledger().list_metrics(prefix)
    return {"metrics": metrics, "total": len(metrics)}


@router.get("/metrics/{metric_key:path}/history")
async def metric_history(metric_key: str) -> Dict[str, Any]:
    ledger = get_ratchet_ledger()
    if not ledger.get(metric_key):
        raise HTTPException(status_code=404, detail=f"metric {metric_key} not found")
    return {"metric_key": metric_key, "history": ledger.history(metric_key)}


@router.post("/metrics/{metric_key:path}/force-reset")
async def force_reset(metric_key: str, req: ForceResetRequest) -> Dict[str, Any]:
    """人工重置（留痕逃生门）."""
    if not req.reason.strip():
        raise HTTPException(status_code=400, detail="reason 必填（重置必须留痕）")
    result = get_ratchet_ledger().force_reset(metric_key, req.reason)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result
