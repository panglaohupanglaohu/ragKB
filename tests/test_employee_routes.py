# -*- coding: utf-8 -*-
"""AgentsGroupConfig E-E API smoke tests."""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")


def _client(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from agents.agent_relationships import reset_relationship_store
    from agents.agent_triggers import (
        get_trigger_store,
        reset_trigger_daemon,
        reset_trigger_store,
    )
    from agents.api import init_agent_config
    from agents.employee_profile import reset_employee_store
    from agents.employee_routes import router
    from agents.models import AgentProfile
    from agents.team_manager import TeamManager
    from agents.team_store import TeamStore

    manager = TeamManager(store=TeamStore(path=tmp_path / "teams.json"))
    team = manager.create_team(name="Route Team", description="route smoke")
    manager.add_agent_to_team(
        team.team_id,
        AgentProfile(agent_id="agent_a", name="Agent A", role="analyst"),
    )
    manager.add_agent_to_team(
        team.team_id,
        AgentProfile(agent_id="agent_b", name="Agent B", role="reviewer"),
    )
    init_agent_config(manager)

    reset_employee_store(base_dir=tmp_path / "employees")
    reset_trigger_store(store_dir=tmp_path / "triggers")
    reset_trigger_daemon(store=get_trigger_store(), wake_log=tmp_path / "wake.jsonl")
    reset_relationship_store(store_dir=tmp_path / "relationships")

    app = FastAPI()
    app.include_router(router)
    return TestClient(app), team.team_id


def test_employee_file_context_trigger_relationship_governance_routes(tmp_path):
    client, team_id = _client(tmp_path)

    # EE-1: four-file profile API, including memory append-only semantics.
    soul = client.get("/api/v1/agent-employee/agents/agent_a/files/soul")
    assert soul.status_code == 200
    assert soul.json()["exists"] is True

    put_focus = client.put(
        "/api/v1/agent-employee/agents/agent_a/files/focus",
        json={"content": "- [ ] 每日复盘\n- [x] 已完成项"},
    )
    assert put_focus.status_code == 200
    assert client.put(
        "/api/v1/agent-employee/agents/agent_a/files/memory",
        json={"content": "overwrite"},
    ).status_code == 405
    appended = client.post(
        "/api/v1/agent-employee/agents/agent_a/files/memory/append",
        json={"entry": "路由测试经验", "source": "pytest"},
    )
    assert appended.status_code == 200
    assert appended.json()["entries"] == 1
    assert client.post(
        "/api/v1/agent-employee/agents/agent_a/files/heartbeat/reset"
    ).status_code == 200
    focus_items = client.get("/api/v1/agent-employee/agents/agent_a/focus-items")
    assert focus_items.status_code == 200
    assert focus_items.json()["items"][0]["text"] == "每日复盘"

    # EE-2: organizational context preview.
    context = client.get(
        f"/api/v1/agent-employee/teams/{team_id}/agents/agent_a/context"
    )
    assert context.status_code == 200
    assert {"soul", "focus", "relationships", "team_context"} <= set(
        context.json()["sections"]
    )

    # EE-3: Trigger CRUD plus focus-bound 422.
    invalid_trigger = client.post(
        f"/api/v1/agent-employee/teams/{team_id}/agents/agent_a/triggers",
        json={"trigger_type": "interval", "focus_item": "", "config": {"every_minutes": 10}},
    )
    assert invalid_trigger.status_code == 422
    trigger = client.post(
        f"/api/v1/agent-employee/teams/{team_id}/agents/agent_a/triggers",
        json={
            "trigger_type": "interval",
            "enabled": True,
            "focus_item": "每日复盘",
            "config": {"every_minutes": 10},
        },
    )
    assert trigger.status_code == 200
    trigger_id = trigger.json()["trigger_id"]
    assert client.get(
        f"/api/v1/agent-employee/teams/{team_id}/agents/agent_a/triggers"
    ).json()["total"] == 1
    toggled = client.post(
        f"/api/v1/agent-employee/teams/{team_id}/triggers/{trigger_id}/toggle"
    )
    assert toggled.status_code == 200
    updated = client.put(
        f"/api/v1/agent-employee/teams/{team_id}/triggers/{trigger_id}",
        json={
            "trigger_type": "interval",
            "enabled": True,
            "focus_item": "每日复盘",
            "config": {"every_minutes": 15},
        },
    )
    assert updated.status_code == 200

    # EE-6: wake log after a manual daemon tick.
    from agents.agent_triggers import get_trigger_daemon

    events = get_trigger_daemon().tick(datetime.now(timezone.utc) + timedelta(seconds=1))
    assert len(events) == 1
    wake = client.get(
        f"/api/v1/agent-employee/teams/{team_id}/agents/agent_a/wake-log?limit=5"
    )
    assert wake.status_code == 200
    assert wake.json()["events"][0]["trigger_id"] == trigger_id

    assert client.delete(
        f"/api/v1/agent-employee/teams/{team_id}/triggers/{trigger_id}"
    ).status_code == 200

    # EE-4: relationship CRUD and can-communicate.
    rel = client.post(
        f"/api/v1/agent-employee/teams/{team_id}/relationships",
        json={
            "kind": "agent_agent",
            "source_agent_id": "agent_a",
            "target_id": "agent_b",
            "rel_type": "reviewer",
            "note": "route smoke",
        },
    )
    assert rel.status_code == 200
    rel_id = rel.json()["rel_id"]
    rels_payload = client.get(
        f"/api/v1/agent-employee/teams/{team_id}/relationships"
    ).json()
    assert rels_payload["total"] == 1
    assert rels_payload["gate_mode"] in {"soft", "hard"}
    can = client.get(
        f"/api/v1/agent-employee/teams/{team_id}/agents/agent_a/can-communicate"
        "?target=agent_b"
    )
    assert can.status_code == 200
    assert can.json()["allowed"] is True
    assert client.delete(
        f"/api/v1/agent-employee/teams/{team_id}/relationships/{rel_id}"
    ).status_code == 200

    # EE-5: governance round trip.
    gov = client.get(
        f"/api/v1/agent-employee/teams/{team_id}/agents/agent_a/governance"
    )
    assert gov.status_code == 200
    assert gov.json()["autonomy_level"] == 2
    updated_gov = client.put(
        f"/api/v1/agent-employee/teams/{team_id}/agents/agent_a/governance",
        json={"autonomy_level": 3, "token_budget": 2048, "fallback_model_id": "cheap-model"},
    )
    assert updated_gov.status_code == 200
    body = updated_gov.json()
    assert body["autonomy_level"] == 3
    assert body["token_budget"] == 2048
    assert body["fallback_model_id"] == "cheap-model"
