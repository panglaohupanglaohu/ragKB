# -*- coding: utf-8 -*-
"""
可观测性监控 API 路由 — 为前端面板提供数据端点.

端点:
  GET /api/v1/agent-config/monitoring/dashboard     — 总览仪表盘
  GET /api/v1/agent-config/monitoring/fingerprints   — 指纹遥测数据
  GET /api/v1/agent-config/monitoring/traces         — 聚合链路 Trace 关联
  GET /api/v1/agent-config/monitoring/topology        — Trace 拓扑图
  GET /api/v1/agent-config/monitoring/channels/status — 监控 Channel 状态
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Monitoring Dashboard"])


# ── 辅助函数：获取全局监控组件 ──────────────────────────────────────────

def _get_fingerprint_channel():
    """安全获取 FingerprintTelemetryChannel."""
    try:
        from monitoring.fingerprint_bypass import get_fingerprint_channel
        return get_fingerprint_channel()
    except Exception as e:
        logger.debug(f"Fingerprint channel not available: {e}")
        return None


def _get_trace_bridge_channel():
    """安全获取 TraceBridgeChannel."""
    try:
        from monitoring.trace_bridge import get_trace_bridge_channel
        return get_trace_bridge_channel()
    except Exception as e:
        logger.debug(f"Trace bridge not available: {e}")
        return None


def _get_plaza_monitor():
    """安全获取 PlazaMonitorChannel."""
    try:
        from monitoring.plaza_monitor import get_plaza_monitor
        return get_plaza_monitor()
    except Exception as e:
        logger.debug(f"Plaza monitor not available: {e}")
        return None


def _get_collector():
    """安全获取 TraceCollector."""
    try:
        from monitoring.collector import get_collector
        return get_collector()
    except Exception as e:
        logger.debug(f"TraceCollector not available: {e}")
        return None


# ── Dashboard ─────────────────────────────────────────────────────────────


@router.get("/dashboard")
async def get_dashboard():
    """获取监控总览仪表盘数据.

    Returns:
        {
            "fingerprints": {...},       # 指纹遥测摘要
            "traces": {...},             # 链路追踪摘要
            "plaza_status": {...},       # 广场运行状态
            "alerts": [...],             # 实时告警
            "anomaly_detected": bool,    # 是否检测到异常
        }
    """
    alert_list: List[Dict[str, Any]] = []
    anomaly_detected = False

    # 指纹遥测摘要
    fp_summary: Dict[str, Any] = {"available": False}
    fp_ch = _get_fingerprint_channel()
    if fp_ch:
        try:
            fp_stats = await fp_ch.get_stats()
            fp_summary = {
                "available": True,
                "total_collected": fp_stats.get("total_collected", 0),
                "buffer_size": fp_stats.get("buffer_size", 0),
                "anomaly_detected": fp_stats.get("anomaly_detected", False),
            }
            if fp_stats.get("anomaly_detected"):
                anomaly_detected = True
                alert_list.append({
                    "priority": "p0",
                    "type": "ewma_breach",
                    "message": "EWMA 阈值突破 — 指纹遥测已切换全量采集模式",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
        except Exception as e:
            logger.debug(f"Fingerprint stats error: {e}")

    # 链路追踪摘要
    trace_summary: Dict[str, Any] = {"available": False}
    trace_ch = _get_trace_bridge_channel()
    if trace_ch:
        try:
            trace_stats = await trace_ch.get_stats()
            trace_summary = {
                "available": True,
                "total_links": trace_stats.get("total_links", 0),
                "total_traces": trace_stats.get("total_traces", 0),
                "total_nodes": trace_stats.get("total_nodes", 0),
            }
        except Exception as e:
            logger.debug(f"Trace stats error: {e}")

    # Plaza 状态
    plaza_summary: Dict[str, Any] = {"available": False}
    plaza_mon = _get_plaza_monitor()
    if plaza_mon:
        try:
            plaza_summary = {
                "available": True,
                "status": plaza_mon.get_status(),
            }
        except Exception as e:
            logger.debug(f"Plaza status error: {e}")

    return {
        "fingerprints": fp_summary,
        "traces": trace_summary,
        "plaza_status": plaza_summary,
        "alerts": alert_list,
        "anomaly_detected": anomaly_detected,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Fingerprints ──────────────────────────────────────────────────────────


@router.get("/fingerprints")
async def get_fingerprints(limit: int = Query(default=10, ge=1, le=100)):
    """获取最近的行为指纹遥测数据.

    Args:
        limit: 返回条数 (1-100)
    """
    fp_ch = _get_fingerprint_channel()
    if not fp_ch:
        return {
            "fingerprints": [],
            "stats": {"total_collected": 0, "error": "FingerprintTelemetryChannel not available"},
        }

    try:
        fps = await fp_ch.get_recent_fingerprints(limit=limit)
        stats = await fp_ch.get_stats()
        return {
            "fingerprints": fps,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fingerprints: {str(e)}",
        )


# ── Traces ────────────────────────────────────────────────────────────────


@router.get("/traces")
async def get_traces(limit: int = Query(default=30, ge=1, le=200)):
    """获取最近的聚合链路 Trace 关联.

    Args:
        limit: 返回条数 (1-200)
    """
    trace_ch = _get_trace_bridge_channel()
    if not trace_ch:
        return {
            "links": [],
            "stats": {"total_links": 0, "error": "TraceBridgeChannel not available"},
        }

    try:
        links = await trace_ch.get_recent_links(limit=limit)
        stats = await trace_ch.get_stats()
        return {
            "links": links,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch traces: {str(e)}",
        )


@router.get("/topology")
async def get_topology():
    """获取当前 Trace 拓扑图数据."""
    trace_ch = _get_trace_bridge_channel()
    if not trace_ch:
        return {"nodes": [], "links": [], "total_traces": 0}

    try:
        return await trace_ch.get_topology()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch topology: {str(e)}",
        )


@router.get("/traces/{trace_id}")
async def get_trace_chain(trace_id: str):
    """获取某条 Trace 的完整因果链.

    Args:
        trace_id: Trace ID (32 位 hex)
    """
    trace_ch = _get_trace_bridge_channel()
    if not trace_ch:
        return {"chain": [], "error": "TraceBridgeChannel not available"}

    try:
        chain = await trace_ch.get_trace_chain(trace_id)
        return {"trace_id": trace_id, "chain": chain}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trace chain: {str(e)}",
        )


# ── Channel Status ────────────────────────────────────────────────────────


@router.get("/channels/status")
async def get_channels_status():
    """获取所有监控 Channel 的运行状态."""
    channels_status = []

    # Fingerprint Telemetry
    fp_ch = _get_fingerprint_channel()
    if fp_ch:
        try:
            channels_status.append(fp_ch.get_status())
        except Exception as e:
            channels_status.append({"channel": "fingerprint_telemetry", "status": "error", "error": str(e)})
    else:
        channels_status.append({"channel": "fingerprint_telemetry", "status": "not_initialized"})

    # Trace Bridge
    trace_ch = _get_trace_bridge_channel()
    if trace_ch:
        try:
            channels_status.append(trace_ch.get_status())
        except Exception as e:
            channels_status.append({"channel": "trace_bridge", "status": "error", "error": str(e)})
    else:
        channels_status.append({"channel": "trace_bridge", "status": "not_initialized"})

    # Plaza Monitor
    plaza_mon = _get_plaza_monitor()
    if plaza_mon:
        try:
            channels_status.append(plaza_mon.get_status())
        except Exception as e:
            channels_status.append({"channel": "plaza_monitor", "status": "error", "error": str(e)})
    else:
        channels_status.append({"channel": "plaza_monitor", "status": "not_initialized"})

    return {
        "channels": channels_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
