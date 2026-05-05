# -*- coding: utf-8 -*-
"""
Bridge Chat Channel - 驾驶台智能对话模块

实现驾驶台自然语言交互接口:
- 中英文双语意图识别
- 多 Channel 数据路由与整合
- 模板化智能回复生成
- 会话上下文管理
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .marine_base import MarineChannel, ChannelStatus, ChannelPriority

logger = logging.getLogger(__name__)


# ==================== 意图定义 ====================

_INTENT_RULES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("navigation", (
        "航向", "航速", "位置", "经纬度", "导航",
        "heading", "course", "speed", "sog", "cog", "position", "navigate", "gps",
    )),
    ("colregs", (
        "避碰", "碰撞", "会遇", "让路",
        "colregs", "collision", "cpa", "tcpa", "encounter",
    )),
    ("route", (
        "航线", "路线", "航程", "计划",
        "route", "voyage", "waypoint", "eta",
    )),
    ("engine", (
        "主机", "引擎", "机舱", "转速", "燃油",
        "engine", "rpm", "fuel",
    )),
    ("weather", (
        "天气", "风速", "风向", "浪高", "气压", "台风", "气象", "能见度",
        "weather", "wind", "wave", "sea state",
    )),
    ("ais", (
        "目标船", "周围船舶", "船舶识别", "附近",
        "ais", "target", "vessel", "mmsi",
    )),
    ("alarm", (
        "报警", "告警", "警报", "消音", "确认报警",
        "alarm", "alert", "acknowledge",
    )),
    ("autopilot", (
        "自动舵", "舵角", "转向", "航向保持", "偏航",
        "autopilot", "rudder", "heading hold",
    )),
    ("attitude", (
        "姿态", "横摇", "纵摇", "升沉", "减摇", "稳定",
        "roll", "pitch", "heave", "rcs", "foil", "trim tab",
    )),
    ("safety", (
        "安全", "消防", "水密", "进水", "灭火", "烟雾",
        "safety", "fire", "watertight", "temperature",
    )),
    ("energy", (
        "能效", "排放", "碳排放", "油耗优化",
        "energy", "eexi", "cii", "eedi", "emission", "co2",
    )),
    ("mob", (
        "落水", "人员落水", "搜救", "救援",
        "mob", "man overboard", "overboard",
    )),
)


# ==================== 回复模板 ====================

_REPLY_TEMPLATES: Dict[str, str] = {
    "navigation": "当前航向 {course}°T, 航速 {speed} kn, 位置 {lat}°N / {lon}°E。",
    "colregs": "碰撞风险评估: {risk_count} 个目标在监控中, 最高风险等别: {max_risk}。{detail}",
    "route": "当前航线: {route_name}, 距下一航路点 {dist_wp} nm, ETA {eta}。",
    "engine": "主机状态: {engine_status}, 转速 {rpm} RPM, 功率 {power} kW, 油耗 {fuel_rate} L/h。",
    "weather": "天气概况: 风 {wind_dir}° / {wind_speed} kn, 浪高 {wave_height} m, 气压 {pressure} hPa。",
    "ais": "AIS 监控范围内共 {target_count} 个目标, 最近目标 MMSI {nearest_mmsi}, 距离 {nearest_range} nm。",
    "alarm": "当前活跃报警 {active_count} 条。 {alarm_summary}",
    "autopilot": "自动舵状态: {ap_mode}, 设定航向 {set_heading}°, 偏差 {deviation}°, 舵角 {rudder}°。",
    "attitude": "姿态数据: 横摇 {roll}°, 纵摇 {pitch}°, 升沉 {heave} m。减摇系统: {rcs_status}。",
    "safety": "安全系统状态: {safety_status}。消防分区 {fire_zones} 正常, {safety_detail}",
    "energy": "能效评级: EEXI {eexi}, CII {cii}。当前碳排放强度 {co2_intensity} gCO₂/t·nm。",
    "mob": "MOB 状态: {mob_status}。{mob_detail}",
    "general": "系统综合状态: {channel_ok}/{channel_total} 模块正常运行。{summary}",
}

_SUGGESTIONS: Dict[str, List[str]] = {
    "navigation": ['查看周围AIS目标', '显示当前航线', '检查避碰态势'],
    "colregs": ['显示CPA/TCPA详情', '查看目标船信息', '检查航向建议'],
    "route": ['查看天气预报', '优化航线能效', '显示航路点列表'],
    "engine": ['检查机舱报警', '查看油耗趋势', '维护计划'],
    "weather": ['查看航线天气', '检查台风路径', '更新气象信息'],
    "ais": ['查看碰撞风险', '显示目标详情', '导航态势概览'],
    "alarm": ['确认/消音报警', '查看报警历史', '安全系统状态'],
    "autopilot": ['切换手动/自动', '调整航向', '检查舵机状态'],
    "attitude": ['减摇系统详情', '调整舒适模式', '查看运动统计'],
    "safety": ['消防分区详情', '水密舱状态', '应急预案'],
    "energy": ['CII改善方案', '燃油消耗统计', '排放合规文档'],
    "mob": ['搜救圈范围', '漂流估算', '通知岸基'],
    "general": ['导航状态', '机舱概览', '安全报警汇总'],
}

_INTENT_CHANNEL_MAP: Dict[str, str] = {
    "navigation": "intelligent_navigation",
    "colregs": "colregs_brain",
    "route": "route_optimizer",
    "engine": "intelligent_engine",
    "weather": "weather_routing",
    "ais": "ais_processor",
    "alarm": "alarm_management",
    "autopilot": "autopilot_monitor",
    "attitude": "wpc_attitude_control",
    "safety": "safety_system_monitor",
    "energy": "energy_efficiency_channel",
    "mob": "man_overboard",
}


# ==================== 单条对话消息 ====================

@dataclass
class ChatMessage:
    """单条对话消息."""
    role: str              # "user" | "assistant"
    content: str
    intent: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# ==================== Channel ====================

class BridgeChatChannel(MarineChannel):
    """驾驶台智能对话 Channel.

    实现驾驶台自然语言交互接口,
    模板化智能回复生成.
    """

    name = "bridge_chat"
    description = "驾驶台智能对话 (Bridge Chat)"
    version = "1.0.0"
    priority = ChannelPriority.P1
    dependencies: List[str] = []

    MAX_HISTORY = 100

    def __init__(self, channel_registry: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(**kwargs)
        self._channel_registry: Dict[str, Any] = channel_registry or {}
        self._sessions: Dict[str, deque] = {}
        self._total_messages: int = 0
        self._intent_stats: Dict[str, int] = {}

    # -- MarineChannel interface --

    def initialize(self) -> bool:
        self._set_health(ChannelStatus.OK, "Bridge Chat ready")
        self._initialized = True
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self._health.status.value,
            "sessions": len(self._sessions),
            "total_messages": self._total_messages,
            "intent_stats": dict(self._intent_stats),
            "registry_channels": list(self._channel_registry.keys()),
        }

    def shutdown(self) -> bool:
        self._sessions.clear()
        self._set_health(ChannelStatus.OFF, "Shutdown")
        return True

    # -- process_event --

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.monotonic()
        msg = (event.get("message") or "").strip()
        session_id = event.get("session_id") or "default"
        lang = event.get("lang") or self._detect_lang(msg)

        if not msg:
            return self._empty_reply(lang)

        intent = self._classify_intent(msg, session_id)
        self._intent_stats[intent] = self._intent_stats.get(intent, 0) + 1

        self._append_history(session_id, ChatMessage(role="user", content=msg, intent=intent))

        channel_data, sources = self._fetch_channel_data(intent)
        reply_text = self._build_reply(intent, channel_data, lang)
        urgency = self._assess_urgency(intent, channel_data)
        suggestions = self._get_suggestions(intent, lang)

        self._append_history(session_id, ChatMessage(role="assistant", content=reply_text, intent=intent))
        self._total_messages += 1

        elapsed_ms = (time.monotonic() - t0) * 1000
        self._record_call(True, elapsed_ms)

        return {
            "reply": reply_text,
            "intent": intent,
            "sources": sources,
            "suggestions": suggestions,
            "urgency": urgency,
            "session_id": session_id,
            "elapsed_ms": round(elapsed_ms, 1),
        }

    # -- Intent classification --

    def _classify_intent(self, message: str, session_id: str = "default") -> str:
        lower = message.lower()
        best_intent = "general"
        best_score = 0
        for intent, keywords in _INTENT_RULES:
            score = sum(1 for kw in keywords if kw in lower)
            if score > best_score:
                best_score = score
                best_intent = intent
        if best_score == 0:
            best_intent = self._context_intent(session_id)
        return best_intent

    def _context_intent(self, session_id: str) -> str:
        history = self._sessions.get(session_id)
        if not history:
            return "general"
        for msg in reversed(history):
            if msg.role == "user" and msg.intent and msg.intent != "general":
                return msg.intent
        return "general"

    # -- Channel data fetch --

    def _fetch_channel_data(self, intent: str) -> Tuple[Dict[str, Any], List[str]]:
        sources: List[str] = []
        data: Dict[str, Any] = {}
        channel_name = _INTENT_CHANNEL_MAP.get(intent)
        if channel_name and channel_name in self._channel_registry:
            ch = self._channel_registry[channel_name]
            try:
                status = ch.get_status() if hasattr(ch, "get_status") else {}
                data.update(status)
                # Flatten nested dicts so template fillers can find keys like wind_speed
                for v in list(status.values()):
                    if isinstance(v, dict):
                        data.update(v)
                sources.append(channel_name)
            except Exception as exc:
                logger.warning("Failed to get status from %s: %s", channel_name, exc)
                data["_error"] = str(exc)
        if intent == "general":
            data, sources = self._fetch_overview()
        return data, sources

    def _fetch_overview(self) -> Tuple[Dict[str, Any], List[str]]:
        sources: List[str] = []
        overview: Dict[str, Any] = {"channel_ok": 0, "channel_total": 0}
        for ch_name, ch in self._channel_registry.items():
            overview["channel_total"] += 1
            try:
                st = ch.get_status() if hasattr(ch, "get_status") else {}
                status_val = st.get("status", "unknown")
                if status_val in ("ok", "running", ChannelStatus.OK):
                    overview["channel_ok"] += 1
                sources.append(ch_name)
            except Exception:
                pass
        overview["summary"] = f"{overview['channel_ok']}/{overview['channel_total']} channels healthy."
        return overview, sources

    # -- Reply generation --

    def _build_reply(self, intent: str, data: Dict[str, Any], lang: str = "zh") -> str:
        fillers = self._extract_fillers(intent, data)
        template = _REPLY_TEMPLATES.get(intent, _REPLY_TEMPLATES["general"])
        try:
            reply = template.format_map(_SafeFormatDict(fillers))
        except Exception:
            reply = template
        if lang == "en":
            reply = self._translate_key_terms(reply)
        return reply

    def _extract_fillers(self, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        d = _SafeFormatDict(data)
        extractors = {
            "navigation": lambda: {
                "course": d.get("course", d.get("heading", "--")),
                "speed": d.get("speed", d.get("sog", "--")),
                "lat": d.get("latitude", d.get("lat", "--")),
                "lon": d.get("longitude", d.get("lon", "--")),
            },
            "colregs": lambda: {
                "risk_count": len(d.get("collision_risks", d.get("risks", []))),
                "max_risk": d.get("max_risk_level", d.get("risk_level", "safe")),
                "detail": d.get("detail", ""),
            },
            "route": lambda: {
                "route_name": d.get("route_name", d.get("active_route", "--")),
                "dist_wp": d.get("distance_to_wp", d.get("dist_wp", "--")),
                "eta": d.get("eta", "--"),
            },
            "engine": lambda: {
                "engine_status": d.get("engine_status", d.get("status", "--")),
                "rpm": d.get("rpm", d.get("engine_rpm", "--")),
                "power": d.get("power", d.get("power_kw", "--")),
                "fuel_rate": d.get("fuel_rate", d.get("fuel_consumption", "--")),
            },
            "weather": lambda: {
                "wind_dir": d.get("wind_direction", d.get("wind_dir", "--")),
                "wind_speed": d.get("wind_speed", "--"),
                "wave_height": d.get("wave_height", d.get("significant_wave_height", "--")),
                "pressure": d.get("pressure", d.get("barometric_pressure", "--")),
            },
            "ais": lambda: {
                "target_count": d.get("target_count", len(d.get("targets", []))),
                "nearest_mmsi": d.get("nearest_mmsi", "--"),
                "nearest_range": d.get("nearest_range", "--"),
            },
            "alarm": lambda: {
                "active_count": d.get("active_count", len(d.get("active_alarms", []))),
                "alarm_summary": d.get("alarm_summary", ""),
            },
            "autopilot": lambda: {
                "ap_mode": d.get("mode", d.get("ap_mode", "--")),
                "set_heading": d.get("set_heading", d.get("target_heading", "--")),
                "deviation": d.get("deviation", d.get("heading_error", "--")),
                "rudder": d.get("rudder_angle", d.get("rudder", "--")),
            },
            "attitude": lambda: {
                "roll": d.get("roll", d.get("roll_deg", "--")),
                "pitch": d.get("pitch", d.get("pitch_deg", "--")),
                "heave": d.get("heave", d.get("heave_m", "--")),
                "rcs_status": d.get("rcs_status", d.get("stabilizer_status", "--")),
            },
            "safety": lambda: {
                "safety_status": d.get("safety_status", d.get("status", "正常")),
                "fire_zones": d.get("fire_zones_ok", d.get("fire_zones", "--")),
                "safety_detail": d.get("safety_detail", ""),
            },
            "energy": lambda: {
                "eexi": d.get("eexi_rating", d.get("eexi", "--")),
                "cii": d.get("cii_rating", d.get("cii", "--")),
                "co2_intensity": d.get("co2_intensity", d.get("carbon_intensity", "--")),
            },
            "mob": lambda: {
                "mob_status": d.get("mob_status", d.get("status", "未触发")),
                "mob_detail": d.get("mob_detail", d.get("detail", "")),
            },
            "general": lambda: {
                "channel_ok": d.get("channel_ok", "--"),
                "channel_total": d.get("channel_total", "--"),
                "summary": d.get("summary", ""),
            },
        }
        extractor = extractors.get(intent, extractors["general"])
        return extractor()

    def _assess_urgency(self, intent: str, data: Dict[str, Any]) -> str:
        status = data.get("status", "")
        if isinstance(status, ChannelStatus):
            status = status.value
        if intent in ("colregs", "mob", "safety"):
            risk = data.get("max_risk_level", data.get("risk_level", ""))
            mob_active = data.get("mob_active", data.get("alert_active", False))
            if risk in ("danger", "critical") or mob_active:
                return "critical"
            if risk in ("warning", "caution") or status in ("warn", "warning"):
                return "elevated"
        if intent == "alarm":
            count = data.get("active_count", len(data.get("active_alarms", [])))
            if count > 5:
                return "critical"
            if count > 0:
                return "elevated"
        if status in ("error", "critical"):
            return "critical"
        if status in ("warn", "warning"):
            return "elevated"
        return "normal"

    # -- Suggestions --

    def _get_suggestions(self, intent: str, lang: str = "zh") -> List[str]:
        suggestions = list(_SUGGESTIONS.get(intent, _SUGGESTIONS["general"]))
        if lang == "en":
            suggestions = [self._translate_key_terms(s) for s in suggestions]
        return suggestions

    # -- Session management --

    def _append_history(self, session_id: str, msg: ChatMessage) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = deque(maxlen=self.MAX_HISTORY)
        self._sessions[session_id].append(msg)

    def get_session_history(self, session_id: str = "default",
                            limit: int = 20) -> List[Dict[str, Any]]:
        history = self._sessions.get(session_id)
        if not history:
            return []
        items = list(history)[-limit:]
        return [
            {
                "role": m.role,
                "content": m.content,
                "intent": m.intent,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in items
        ]

    def clear_session(self, session_id: str = "default") -> None:
        self._sessions.pop(session_id, None)

    # -- Registry --

    def register_channel(self, name: str, channel: Any) -> None:
        self._channel_registry[name] = channel

    def unregister_channel(self, name: str) -> None:
        self._channel_registry.pop(name, None)

    # -- Language utils --

    @staticmethod
    def _detect_lang(text: str) -> str:
        if any("\u4e00" <= ch <= "\u9fff" for ch in text):
            return "zh"
        return "en"

    @staticmethod
    def _translate_key_terms(text: str) -> str:
        _map = (
            ("当前航向", "Current heading"),
            ("航速", "speed"),
            ("位置", "position"),
            ("碰撞风险评估", "Collision risk assessment"),
            ("个目标在监控中", "targets monitored"),
            ("最高风险等别", "max risk level"),
            ("主机状态", "Main engine status"),
            ("转速", "RPM"),
            ("功率", "power"),
            ("油耗", "fuel consumption"),
            ("天气概况", "Weather overview"),
            ("自动舵状态", "Autopilot status"),
            ("设定航向", "set heading"),
            ("偏差", "deviation"),
            ("舵角", "rudder angle"),
            ("姿态数据", "Attitude data"),
            ("横摇", "roll"),
            ("纵摇", "pitch"),
            ("升沉", "heave"),
            ("减摇系统", "Stabilizer"),
            ("安全系统状态", "Safety system status"),
            ("正常", "normal"),
            ("报警", "alarm"),
            ("能效评级", "Energy rating"),
            ("系统综合状态", "System overview"),
            ("模块正常运行", "modules running normally"),
            ("查看", "View"),
            ("显示", "Show"),
            ("检查", "Check"),
            ("当前", "Current"),
            ("未触发", "inactive"),
        )
        for zh, en in _map:
            text = text.replace(zh, en)
        return text

    @staticmethod
    def _empty_reply(lang: str = "zh") -> Dict[str, Any]:
        if lang == "en":
            reply = "Please enter your question or command."
        else:
            reply = "请输入您的问题或指令。"
        return {
            "reply": reply,
            "intent": "general",
            "sources": [],
            "suggestions": [],
            "urgency": "normal",
        }


class _SafeFormatDict(dict):
    """format_map fallback: returns '--' for missing keys."""

    def __missing__(self, key: str) -> str:
        return "--"
