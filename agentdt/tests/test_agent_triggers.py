# -*- coding: utf-8 -*-
"""AgentsGroupConfig E-B 测试 — Aware 唤醒系统 (EB-7)."""

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

NOW = datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc)  # 周五 08:00 UTC


def _trigger(**kw):
    from agents.agent_triggers import AgentTrigger
    base = dict(agent_id="a1", team_id="teamA", trigger_type="interval",
                focus_item="跟进X", config={"every_minutes": 30})
    base.update(kw)
    return AgentTrigger(**base)


# ── EB-3: cron 解析 ─────────────────────────────────────────

def test_cron_parse_weekday_morning():
    from agents.agent_triggers import parse_cron, next_cron_fire
    p = parse_cron("0 9 * * 1-5")
    assert p["minute"] == {0} and p["hour"] == {9}
    assert p["weekday"] == {1, 2, 3, 4, 5}
    # 2026-06-12 是周五，08:00 → 当天 09:00
    nxt = next_cron_fire("0 9 * * 1-5", NOW)
    assert nxt == NOW.replace(hour=9, minute=0)


def test_cron_parse_every_30min_and_steps():
    from agents.agent_triggers import parse_cron, next_cron_fire
    p = parse_cron("*/30 * * * *")
    assert p["minute"] == {0, 30}
    nxt = next_cron_fire("*/30 * * * *", NOW.replace(minute=10))
    assert nxt.minute == 30


def test_cron_invalid_expressions():
    from agents.agent_triggers import parse_cron
    for bad in ("0 9 * *", "61 * * * *", "* 25 * * *", "abc * * * *", "*/0 * * * *"):
        try:
            parse_cron(bad)
            assert False, f"应拒绝: {bad}"
        except ValueError:
            pass


def test_cron_tz_offset():
    from agents.agent_triggers import next_cron_fire
    # 北京时间(+480) 9点 = UTC 1 点
    nxt = next_cron_fire("0 9 * * *", NOW.replace(hour=0, minute=0), tz_offset_min=480)
    assert nxt.hour == 1 and nxt.minute == 0


# ── EB-3: once / interval ──────────────────────────────────

def test_once_due_and_auto_disable():
    from agents.agent_triggers import compute_next_fire, is_due
    trg = _trigger(trigger_type="once",
                   config={"fire_at": (NOW - timedelta(minutes=5)).isoformat()})
    assert is_due(trg, NOW)
    trg.fire_count = 1  # 已触发
    assert compute_next_fire(trg, NOW) is None


def test_interval_due_after_elapsed():
    from agents.agent_triggers import is_due
    trg = _trigger(config={"every_minutes": 30})
    trg.last_fired_at = (NOW - timedelta(minutes=31)).isoformat()
    assert is_due(trg, NOW)
    trg.last_fired_at = (NOW - timedelta(minutes=10)).isoformat()
    assert not is_due(trg, NOW)
    # 从未触发 → 立即到期
    trg.last_fired_at = None
    assert is_due(trg, NOW)


def test_disabled_never_due():
    from agents.agent_triggers import is_due
    trg = _trigger(enabled=False)
    assert not is_due(trg, NOW)


# ── EB-4: Focus 绑定约束 ────────────────────────────────────

def test_task_trigger_requires_focus_item():
    from agents.agent_triggers import validate_trigger
    errors = validate_trigger(_trigger(focus_item=""))
    assert any("focus_item" in e and "无目的闹钟" in e for e in errors)
    # 事件型不要求
    assert not any("focus_item" in e for e in validate_trigger(
        _trigger(trigger_type="on_message", focus_item="", config={"from_agent": "a2"})))


def test_focus_checker_rejects_unknown_item():
    from agents.agent_triggers import validate_trigger
    checker = lambda aid, text: text == "存在的项"  # noqa: E731
    assert validate_trigger(_trigger(focus_item="存在的项"), focus_checker=checker) == []
    errors = validate_trigger(_trigger(focus_item="幽灵项"), focus_checker=checker)
    assert any("不在该 Agent 的 focus.md" in e for e in errors)


def test_validate_config_errors():
    from agents.agent_triggers import validate_trigger
    assert any("expr" in e for e in validate_trigger(
        _trigger(trigger_type="cron", config={"expr": "bad"})))
    assert any("fire_at" in e for e in validate_trigger(
        _trigger(trigger_type="once", config={})))
    assert any("every_minutes" in e for e in validate_trigger(
        _trigger(trigger_type="interval", config={"every_minutes": 0})))
    assert any("from_agent" in e for e in validate_trigger(
        _trigger(trigger_type="on_message", config={})))


# ── EB-6: SSRF ─────────────────────────────────────────────

def test_ssrf_protection():
    from agents.agent_triggers import is_url_safe
    for bad in ("http://127.0.0.1/x", "http://10.0.0.5/", "http://172.16.1.1/",
                "http://192.168.1.1/", "http://169.254.169.254/meta",
                "http://localhost/x", "ftp://example.com/", "http://0.0.0.0/"):
        assert not is_url_safe(bad)["safe"], bad
    assert is_url_safe("https://api.github.com/repos")["safe"]
    assert is_url_safe("http://8.8.8.8/health")["safe"]


# ── EB-2/EB-5: store + daemon ──────────────────────────────

def test_store_crud_and_reload():
    from agents.agent_triggers import TriggerStore
    with tempfile.TemporaryDirectory() as tmp:
        store = TriggerStore(store_dir=Path(tmp))
        trg = _trigger()
        store.add(trg)
        assert trg.next_fire_at is not None  # add 时计算
        assert store.get("teamA", trg.trigger_id).agent_id == "a1"
        assert len(store.list_for_agent("teamA", "a1")) == 1
        # 重载
        store2 = TriggerStore(store_dir=Path(tmp))
        assert len(store2.list_enabled("teamA")) == 1
        assert store2.delete("teamA", trg.trigger_id)
        assert not store2.delete("teamA", "ghost")


def test_daemon_tick_fires_and_dedups():
    from agents.agent_triggers import TriggerStore, TriggerDaemon
    with tempfile.TemporaryDirectory() as tmp:
        store = TriggerStore(store_dir=Path(tmp))
        daemon = TriggerDaemon(store=store, wake_log=Path(tmp) / "wake.jsonl")
        trg = _trigger(config={"every_minutes": 30})  # 从未触发 → 立即到期
        store.add(trg)

        events = daemon.tick(NOW)
        assert len(events) == 1
        assert events[0]["agent_id"] == "a1" and events[0]["reason"] == "interval"
        assert events[0]["focus_item"] == "跟进X"
        # 去重: 15s 后同 agent 不再唤醒
        assert daemon.tick(NOW + timedelta(seconds=15)) == []
        # fire_count 与 last_fired_at 已更新
        again = store.get("teamA", trg.trigger_id)
        assert again.fire_count == 1 and again.last_fired_at is not None
        # 唤醒日志可读
        log = daemon.read_wake_log(agent_id="a1")
        assert len(log) == 1 and log[0]["trigger_id"] == trg.trigger_id


def test_daemon_once_self_disables():
    from agents.agent_triggers import TriggerStore, TriggerDaemon
    with tempfile.TemporaryDirectory() as tmp:
        store = TriggerStore(store_dir=Path(tmp))
        daemon = TriggerDaemon(store=store, wake_log=Path(tmp) / "wake.jsonl")
        trg = _trigger(trigger_type="once",
                       config={"fire_at": (NOW - timedelta(minutes=1)).isoformat()})
        store.add(trg)
        assert len(daemon.tick(NOW)) == 1
        assert store.get("teamA", trg.trigger_id).enabled is False  # 自停
        assert daemon.tick(NOW + timedelta(minutes=5)) == []


def test_daemon_heartbeat_active_hours_and_interval():
    from agents.agent_triggers import TriggerStore, TriggerDaemon
    with tempfile.TemporaryDirectory() as tmp:
        configs = [{"agent_id": "hb1", "team_id": "teamA", "enabled": True,
                    "active_hours": "09:00-18:00", "interval_min": 240, "tz_offset_min": 0}]
        daemon = TriggerDaemon(store=TriggerStore(store_dir=Path(tmp)),
                               wake_log=Path(tmp) / "wake.jsonl",
                               heartbeat_config_fn=lambda: configs)
        # 心跳每 4 tick 检查; 08:00 不在活跃时段
        for i in range(4):
            events = daemon.tick(NOW + timedelta(seconds=15 * i))
        assert events == []
        # 10:00 在时段内 → 第 8 个 tick 触发
        t2 = NOW.replace(hour=10)
        for i in range(4):
            events = daemon.tick(t2 + timedelta(seconds=15 * i))
        assert len(events) == 1 and events[0]["reason"] == "heartbeat"
        # 间隔未到 → 不再触发
        t3 = t2 + timedelta(minutes=60)
        for i in range(4):
            events = daemon.tick(t3 + timedelta(seconds=15 * i))
        assert events == []
