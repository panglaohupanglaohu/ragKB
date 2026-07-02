# -*- coding: utf-8 -*-
"""Agent Triggers — Aware 自主唤醒系统 (AgentsGroupConfig E-B).

参考 Clawith 白皮书 Chapter 3: Trigger(何时醒) + Focus(醒来看什么) + Heartbeat(周期探索)。
六类 trigger: cron / once / interval / poll / on_message / webhook
核心约束: 任务型 Trigger 必须绑定 focus.md 中的条目（无目的闹钟禁止）。
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
TRIGGER_DIR = _ROOT / "storage" / "agent_triggers"
WAKE_LOG = TRIGGER_DIR / "wake_log.jsonl"

TRIGGER_TYPES = ("cron", "once", "interval", "poll", "on_message", "webhook")
TASK_TYPES = ("cron", "once", "interval")  # 任务型 → 必须绑定 focus
DEDUP_WINDOW_SEC = 30
HEARTBEAT_DEFAULT_INTERVAL_MIN = 240
TICK_SECONDS = 15


@dataclass
class AgentTrigger:
    """唤醒触发器 (EB-1)."""
    trigger_id: str = field(default_factory=lambda: f"trg_{uuid.uuid4().hex[:8]}")
    agent_id: str = ""
    team_id: str = ""
    trigger_type: str = "cron"
    enabled: bool = True
    focus_item: str = ""           # 任务型必填，绑定 focus.md 条目
    config: Dict[str, Any] = field(default_factory=dict)
    last_fired_at: Optional[str] = None
    next_fire_at: Optional[str] = None
    fire_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id, "agent_id": self.agent_id,
            "team_id": self.team_id, "trigger_type": self.trigger_type,
            "enabled": self.enabled, "focus_item": self.focus_item,
            "config": self.config, "last_fired_at": self.last_fired_at,
            "next_fire_at": self.next_fire_at, "fire_count": self.fire_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentTrigger":
        return cls(
            trigger_id=d.get("trigger_id") or f"trg_{uuid.uuid4().hex[:8]}",
            agent_id=d.get("agent_id", ""), team_id=d.get("team_id", ""),
            trigger_type=d.get("trigger_type", "cron"),
            enabled=bool(d.get("enabled", True)),
            focus_item=d.get("focus_item", ""), config=d.get("config", {}),
            last_fired_at=d.get("last_fired_at"), next_fire_at=d.get("next_fire_at"),
            fire_count=int(d.get("fire_count", 0)),
            created_at=d.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


# ── EB-3: cron 解析（5 字段子集: * 数字 , - */n）───────────

def _parse_cron_field(expr: str, lo: int, hi: int) -> set:
    values = set()
    for part in expr.split(","):
        part = part.strip()
        m = re.match(r"^\*/(\d+)$", part)
        if m:
            step = int(m.group(1))
            if step <= 0:
                raise ValueError(f"非法步长: {part}")
            values.update(range(lo, hi + 1, step))
            continue
        if part == "*":
            values.update(range(lo, hi + 1))
            continue
        m = re.match(r"^(\d+)-(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if not (lo <= a <= b <= hi):
                raise ValueError(f"区间越界: {part}")
            values.update(range(a, b + 1))
            continue
        if re.match(r"^\d+$", part):
            v = int(part)
            if not (lo <= v <= hi):
                raise ValueError(f"值越界: {part} (允许 {lo}-{hi})")
            values.add(v)
            continue
        raise ValueError(f"无法解析 cron 字段: {part}")
    return values


def parse_cron(expr: str) -> Dict[str, set]:
    fields = (expr or "").split()
    if len(fields) != 5:
        raise ValueError(f"cron 必须 5 字段（分 时 日 月 周），收到: {expr!r}")
    return {
        "minute": _parse_cron_field(fields[0], 0, 59),
        "hour": _parse_cron_field(fields[1], 0, 23),
        "day": _parse_cron_field(fields[2], 1, 31),
        "month": _parse_cron_field(fields[3], 1, 12),
        "weekday": _parse_cron_field(fields[4], 0, 6),  # 0=周一? 采用 cron 惯例 0=周日; python weekday() 0=周一 → 转换
    }


def _cron_matches(parsed: Dict[str, set], dt: datetime) -> bool:
    # cron 惯例 0=周日…6=周六；python dt.weekday() 0=周一…6=周日
    cron_wd = (dt.weekday() + 1) % 7
    return (dt.minute in parsed["minute"] and dt.hour in parsed["hour"]
            and dt.day in parsed["day"] and dt.month in parsed["month"]
            and cron_wd in parsed["weekday"])


def next_cron_fire(expr: str, now: datetime, tz_offset_min: int = 0) -> Optional[datetime]:
    """未来 24h 内下一个匹配分钟（按 tz_offset 本地时间匹配）."""
    parsed = parse_cron(expr)
    base = now.replace(second=0, microsecond=0)
    offset = timedelta(minutes=tz_offset_min)
    for i in range(1, 24 * 60 + 1):
        candidate = base + timedelta(minutes=i)
        if _cron_matches(parsed, candidate + offset):
            return candidate
    return None


def compute_next_fire(trigger: AgentTrigger, now: Optional[datetime] = None) -> Optional[datetime]:
    """EB-3: 各类型 next fire 计算."""
    now = now or datetime.now(timezone.utc)
    cfg = trigger.config or {}
    t = trigger.trigger_type
    if t == "cron":
        return next_cron_fire(cfg.get("expr", ""), now, int(cfg.get("tz_offset_min", 0)))
    if t == "once":
        if trigger.fire_count > 0:
            return None
        try:
            fire_at = datetime.fromisoformat(str(cfg.get("fire_at", "")).replace("Z", "+00:00"))
            if fire_at.tzinfo is None:
                fire_at = fire_at.replace(tzinfo=timezone.utc)
            return fire_at
        except ValueError:
            return None
    if t in ("interval", "poll"):
        every = int(cfg.get("every_minutes", 30) or 30)
        if trigger.last_fired_at:
            try:
                last = datetime.fromisoformat(trigger.last_fired_at)
                return last + timedelta(minutes=every)
            except ValueError:
                pass
        return now  # 从未触发过 → 立即到期
    return None  # on_message / webhook 由事件驱动，无定时


def is_due(trigger: AgentTrigger, now: Optional[datetime] = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if not trigger.enabled:
        return False
    # cron 守卫: 同一匹配分钟内不重复触发（15s tick 会在一分钟内命中多次）
    if trigger.last_fired_at:
        try:
            last = datetime.fromisoformat(trigger.last_fired_at)
            if trigger.trigger_type == "cron" and (now - last).total_seconds() < 60:
                return False
        except ValueError:
            pass
    nxt = compute_next_fire(trigger, now - timedelta(minutes=1))
    return nxt is not None and nxt <= now


# ── EB-4: Focus 绑定约束 ───────────────────────────────────

def _validate_trigger_config(trigger: AgentTrigger) -> List[str]:
    errors: List[str] = []
    cfg = trigger.config or {}
    if trigger.trigger_type == "cron":
        try:
            parse_cron(cfg.get("expr", ""))
        except ValueError as e:
            errors.append(f"config.expr: {e}")
    if trigger.trigger_type == "once" and not cfg.get("fire_at"):
        errors.append("config.fire_at: 必填 (ISO 时间)")
    if trigger.trigger_type in ("interval", "poll"):
        if int(cfg.get("every_minutes", 0) or 0) < 1:
            errors.append("config.every_minutes: 必须 >= 1")
    if trigger.trigger_type == "poll":
        safe = is_url_safe(cfg.get("url", ""))
        if not safe["safe"]:
            errors.append(f"config.url: {safe['reason']}")
    if trigger.trigger_type == "on_message":
        if not cfg.get("from_agent") and not cfg.get("from_user"):
            errors.append("config.from_agent/from_user: 至少填一个")
    return errors


def _validate_trigger_focus(trigger: AgentTrigger, focus_checker=None) -> List[str]:
    if trigger.trigger_type not in TASK_TYPES:
        return []
    if not trigger.focus_item.strip():
        return ["focus_item: 任务型 Trigger 必须绑定 focus.md 条目（杜绝无目的闹钟）"]
    if focus_checker is None:
        return []
    try:
        if not focus_checker(trigger.agent_id, trigger.focus_item):
            return [f"focus_item: '{trigger.focus_item}' 不在该 Agent 的 focus.md 中，请先添加"]
    except Exception as e:
        logger.debug(f"focus 校验降级跳过: {e}")
    return []


def validate_trigger(trigger: AgentTrigger, focus_checker=None) -> List[str]:
    """返回字段级错误列表，空 = 通过."""
    errors: List[str] = []
    if trigger.trigger_type not in TRIGGER_TYPES:
        errors.append(f"trigger_type: 非法 ({trigger.trigger_type})，允许 {TRIGGER_TYPES}")
        return errors
    errors.extend(_validate_trigger_config(trigger))
    errors.extend(_validate_trigger_focus(trigger, focus_checker))
    return errors


# ── EB-6: SSRF 防护 ────────────────────────────────────────

def _url_safety_error(reason: str) -> Dict[str, Any]:
    return {"safe": False, "reason": reason}


def _url_safety_ok() -> Dict[str, Any]:
    return {"safe": True, "reason": ""}


def _is_safe_url_scheme(scheme: str) -> bool:
    return scheme in ("http", "https")


def _is_blocked_host(host: str) -> Optional[str]:
    if not host:
        return "缺少 host"
    if host.lower() in ("localhost",):
        return "拒绝 localhost"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return None
    if (ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_unspecified):
        return f"拒绝私网/保留地址 {host}"
    return None


def is_url_safe(url: str) -> Dict[str, Any]:
    """poll URL 安全检查：仅 http/https，拒绝私网/环回/链路本地."""
    try:
        parsed = urlparse(url or "")
        if not _is_safe_url_scheme(parsed.scheme):
            return _url_safety_error(f"仅允许 http/https (got {parsed.scheme or '空'})")
        host = parsed.hostname or ""
        blocked_reason = _is_blocked_host(host)
        if blocked_reason:
            return _url_safety_error(blocked_reason)
        return _url_safety_ok()
    except Exception as e:
        return _url_safety_error(f"URL 解析失败: {e}")


# ── EB-2: TriggerStore ─────────────────────────────────────

class TriggerStore:
    def __init__(self, store_dir: Optional[Path] = None):
        self._dir = store_dir or TRIGGER_DIR
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
            logger.warning(f"TriggerStore 读取失败 ({team_id}): {e}")
            return {}

    def _save(self, team_id: str, data: Dict[str, Dict[str, Any]]) -> None:
        p = self._path(team_id)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)

    def add(self, trigger: AgentTrigger) -> AgentTrigger:
        data = self._load(trigger.team_id)
        nxt = compute_next_fire(trigger)
        trigger.next_fire_at = nxt.isoformat() if nxt else None
        data[trigger.trigger_id] = trigger.to_dict()
        self._save(trigger.team_id, data)
        return trigger

    def get(self, team_id: str, trigger_id: str) -> Optional[AgentTrigger]:
        d = self._load(team_id).get(trigger_id)
        return AgentTrigger.from_dict(d) if d else None

    def list_for_agent(self, team_id: str, agent_id: str) -> List[AgentTrigger]:
        return [AgentTrigger.from_dict(d) for d in self._load(team_id).values()
                if d.get("agent_id") == agent_id]

    def list_enabled(self, team_id: str) -> List[AgentTrigger]:
        return [AgentTrigger.from_dict(d) for d in self._load(team_id).values()
                if d.get("enabled")]

    def update(self, trigger: AgentTrigger) -> bool:
        data = self._load(trigger.team_id)
        if trigger.trigger_id not in data:
            return False
        data[trigger.trigger_id] = trigger.to_dict()
        self._save(trigger.team_id, data)
        return True

    def delete(self, team_id: str, trigger_id: str) -> bool:
        data = self._load(team_id)
        if trigger_id not in data:
            return False
        del data[trigger_id]
        self._save(team_id, data)
        return True

    def list_teams(self) -> List[str]:
        return [p.stem for p in self._dir.glob("*.json")]


# ── EB-5: TriggerDaemon ────────────────────────────────────

class TriggerDaemon:
    """15s tick 唤醒守护 — 测试用手动 tick()，生产 start() 挂 asyncio."""

    def __init__(self, store: Optional[TriggerStore] = None,
                 wake_log: Optional[Path] = None,
                 heartbeat_config_fn=None):
        self._store = store or get_trigger_store()
        self._wake_log = wake_log or WAKE_LOG
        self._last_wake: Dict[str, datetime] = {}   # agent_id -> 上次唤醒（去重）
        self._last_heartbeat: Dict[str, datetime] = {}
        self._tick_count = 0
        self._task: Optional[asyncio.Task] = None
        self._running = False
        # heartbeat_config_fn(team_id) -> [{agent_id, active_hours, interval_min}]
        self._heartbeat_config_fn = heartbeat_config_fn

    def tick(self, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """单次扫描，返回唤醒事件列表 (EB-5)."""
        now = now or datetime.now(timezone.utc)
        self._tick_count += 1
        events = self._collect_due_trigger_events(now)

        # 心跳: 每 4 tick 检查
        if self._should_check_heartbeats():
            events.extend(self._check_heartbeats(now))
        return events

    @staticmethod
    def _is_periodic_trigger(trg: AgentTrigger) -> bool:
        return trg.trigger_type not in ("on_message", "webhook")

    def _is_deduped(self, trg: AgentTrigger, now: datetime) -> bool:
        last = self._last_wake.get(trg.agent_id)
        return bool(last and (now - last).total_seconds() < DEDUP_WINDOW_SEC)

    def _should_fire_trigger(self, trg: AgentTrigger, now: datetime) -> bool:
        return self._is_periodic_trigger(trg) and is_due(trg, now) and not self._is_deduped(trg, now)

    def _collect_due_trigger_events(self, now: datetime) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for team_id in self._store.list_teams():
            for trg in self._store.list_enabled(team_id):
                if self._should_fire_trigger(trg, now):
                    events.append(self._fire(trg, now, reason=trg.trigger_type))
        return events

    def _should_check_heartbeats(self) -> bool:
        return self._tick_count % 4 == 0 and bool(self._heartbeat_config_fn)

    def _fire(self, trg: AgentTrigger, now: datetime, reason: str) -> Dict[str, Any]:
        trg.last_fired_at = now.isoformat()
        trg.fire_count += 1
        if trg.trigger_type == "once":
            trg.enabled = False  # 一次性自停
        nxt = compute_next_fire(trg, now)
        trg.next_fire_at = nxt.isoformat() if nxt else None
        self._store.update(trg)
        self._last_wake[trg.agent_id] = now
        event = {"agent_id": trg.agent_id, "team_id": trg.team_id,
                 "trigger_id": trg.trigger_id, "reason": reason,
                 "focus_item": trg.focus_item, "fired_at": now.isoformat()}
        self._log_wake(event)
        logger.info(f"⏰ 唤醒: {trg.agent_id} ← {reason} ({trg.trigger_id})")
        return event

    def _check_heartbeats(self, now: datetime) -> List[Dict[str, Any]]:
        events = []
        try:
            configs = self._heartbeat_config_fn() or []
        except Exception as e:
            logger.debug(f"心跳配置获取失败: {e}")
            return events
        for cfg in configs:
            agent_id = cfg.get("agent_id", "")
            if not agent_id or not cfg.get("enabled", True):
                continue
            # 活跃时段（按 tz_offset 本地时间）
            hours = cfg.get("active_hours", "")
            if hours:
                try:
                    start_s, end_s = hours.split("-")
                    local = now + timedelta(minutes=int(cfg.get("tz_offset_min", 0)))
                    cur = local.hour * 60 + local.minute
                    h1, m1 = map(int, start_s.split(":"))
                    h2, m2 = map(int, end_s.split(":"))
                    if not (h1 * 60 + m1 <= cur <= h2 * 60 + m2):
                        continue
                except (ValueError, AttributeError):
                    pass
            interval = int(cfg.get("interval_min", HEARTBEAT_DEFAULT_INTERVAL_MIN))
            last = self._last_heartbeat.get(agent_id)
            if last and (now - last).total_seconds() < interval * 60:
                continue
            self._last_heartbeat[agent_id] = now
            event = {"agent_id": agent_id, "team_id": cfg.get("team_id", ""),
                     "trigger_id": "heartbeat", "reason": "heartbeat",
                     "focus_item": "", "fired_at": now.isoformat()}
            self._log_wake(event)
            events.append(event)
        return events

    def _log_wake(self, event: Dict[str, Any]) -> None:
        try:
            self._wake_log.parent.mkdir(parents=True, exist_ok=True)
            with self._wake_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"唤醒日志写入失败: {e}")

    def read_wake_log(self, agent_id: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        if not self._wake_log.exists():
            return []
        lines = self._wake_log.read_text(encoding="utf-8").splitlines()
        events = []
        for line in reversed(lines):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if agent_id and e.get("agent_id") != agent_id:
                continue
            events.append(e)
            if len(events) >= limit:
                break
        return events

    async def _loop(self):
        while self._running:
            try:
                self.tick()
            except Exception as e:
                logger.error(f"TriggerDaemon tick 异常: {e}")
            await asyncio.sleep(TICK_SECONDS)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.get_event_loop().create_task(self._loop())
        logger.info("⏰ TriggerDaemon 启动 (15s tick)")

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None


# ── 单例 ──────────────────────────────────────────────────

_store: Optional[TriggerStore] = None
_daemon: Optional[TriggerDaemon] = None


def get_trigger_store() -> TriggerStore:
    global _store
    if _store is None:
        _store = TriggerStore()
    return _store


def reset_trigger_store(**kwargs) -> TriggerStore:
    global _store
    _store = TriggerStore(**kwargs)
    return _store


def get_trigger_daemon() -> TriggerDaemon:
    global _daemon
    if _daemon is None:
        _daemon = TriggerDaemon()
    return _daemon


def reset_trigger_daemon(**kwargs) -> TriggerDaemon:
    global _daemon
    _daemon = TriggerDaemon(**kwargs)
    return _daemon
