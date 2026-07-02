from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agents.agent_triggers import AgentTrigger, TriggerDaemon, TriggerStore, is_url_safe, validate_trigger


def test_trigger_daemon_skips_event_driven_triggers(tmp_path):
    store = TriggerStore(store_dir=tmp_path / "triggers")
    store.add(
        AgentTrigger(
            trigger_id="msg-trigger",
            agent_id="agent-1",
            team_id="team-1",
            trigger_type="on_message",
            focus_item="",
            config={"from_user": "user-1"},
        )
    )
    daemon = TriggerDaemon(store=store, wake_log=tmp_path / "wake.jsonl")

    events = daemon.tick(datetime(2026, 1, 1, tzinfo=timezone.utc))

    assert events == []


def test_trigger_daemon_deduplicates_agent_wakeups(tmp_path):
    store = TriggerStore(store_dir=tmp_path / "triggers")
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    store.add(
        AgentTrigger(
            trigger_id="interval-trigger",
            agent_id="agent-1",
            team_id="team-1",
            trigger_type="interval",
            focus_item="Check focus",
            config={"every_minutes": 1},
            last_fired_at=(now - timedelta(minutes=2)).isoformat(),
        )
    )
    daemon = TriggerDaemon(store=store, wake_log=tmp_path / "wake.jsonl")

    first = daemon.tick(now)
    second = daemon.tick(now + timedelta(seconds=10))

    assert len(first) == 1
    assert second == []


def test_trigger_daemon_checks_heartbeats_every_fourth_tick(tmp_path):
    calls = []

    def heartbeat_config():
        calls.append("called")
        return [
            {
                "agent_id": "agent-heartbeat",
                "team_id": "team-1",
                "enabled": True,
                "interval_min": 1,
            }
        ]

    daemon = TriggerDaemon(
        store=TriggerStore(store_dir=tmp_path / "triggers"),
        wake_log=tmp_path / "wake.jsonl",
        heartbeat_config_fn=heartbeat_config,
    )
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    assert daemon.tick(now) == []
    assert daemon.tick(now + timedelta(seconds=15)) == []
    assert daemon.tick(now + timedelta(seconds=30)) == []
    fourth = daemon.tick(now + timedelta(seconds=45))

    assert calls == ["called"]
    assert fourth[0]["reason"] == "heartbeat"
    assert fourth[0]["agent_id"] == "agent-heartbeat"


def test_validate_trigger_requires_focus_for_task_triggers():
    errors = validate_trigger(
        AgentTrigger(
            agent_id="agent-1",
            team_id="team-1",
            trigger_type="interval",
            focus_item="",
            config={"every_minutes": 10},
        )
    )

    assert errors == ["focus_item: 任务型 Trigger 必须绑定 focus.md 条目（杜绝无目的闹钟）"]


def test_validate_trigger_reports_missing_focus_item_from_checker():
    errors = validate_trigger(
        AgentTrigger(
            agent_id="agent-1",
            team_id="team-1",
            trigger_type="cron",
            focus_item="Review backlog",
            config={"expr": "*/5 * * * *"},
        ),
        focus_checker=lambda agent_id, focus_item: False,
    )

    assert errors == ["focus_item: 'Review backlog' 不在该 Agent 的 focus.md 中，请先添加"]


def test_is_url_safe_rejects_private_and_local_hosts():
    assert is_url_safe("ftp://example.com") == {"safe": False, "reason": "仅允许 http/https (got ftp)"}
    assert is_url_safe("https://localhost/status") == {"safe": False, "reason": "拒绝 localhost"}
    assert is_url_safe("http://127.0.0.1/status") == {"safe": False, "reason": "拒绝私网/保留地址 127.0.0.1"}


def test_is_url_safe_allows_public_domain_without_dns_resolution():
    assert is_url_safe("https://example.com/status") == {"safe": True, "reason": ""}
