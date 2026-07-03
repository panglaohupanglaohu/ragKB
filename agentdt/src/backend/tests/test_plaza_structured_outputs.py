"""Plaza structured output metadata regressions."""

from __future__ import annotations

from agents.plaza import Discussion, Participant, Plaza
from agents.plaza_routes import _ALLOWED_DISCUSSION_OUTPUT_TYPES, _record_discussion_output


def test_record_discussion_output_preserves_source_and_targets():
    plaza = Plaza(id="plaza-1", name="公有云xOPs")
    plaza.participants["agent-a"] = Participant(
        agent_id="agent-a",
        agent_name="Ops",
        team_id="public_cloud_ops",
    )
    plaza.participants["agent-b"] = Participant(
        agent_id="agent-b",
        agent_name="Build",
        team_id="build_system",
    )
    disc = Discussion(
        id="disc-1",
        plaza_id=plaza.id,
        topic="成本异常治理",
        summary="需要拆成任务并进入验证",
    )

    output = _record_discussion_output(
        plaza,
        disc,
        output_type="task",
        target_ids=["task-1", "task-2"],
        team_id="public_cloud_ops",
        status_value="dispatched",
    )
    duplicate = _record_discussion_output(
        plaza,
        disc,
        output_type="task",
        target_ids=["task-1", "task-2"],
        team_id="public_cloud_ops",
        status_value="dispatched",
    )

    assert output["type"] == "task"
    assert output["status"] == "dispatched"
    assert output["team_id"] == "public_cloud_ops"
    assert output["target_ids"] == ["task-1", "task-2"]
    assert output["source"]["type"] == "plaza_discussion"
    assert output["source"]["plaza_id"] == "plaza-1"
    assert output["source"]["discussion_id"] == "disc-1"
    assert output["source"]["topic"] == "成本异常治理"
    assert output["source"]["summary"] == "需要拆成任务并进入验证"
    assert output["source"]["participant_team_ids"] == ["public_cloud_ops", "build_system"]
    assert duplicate["id"] == output["id"]
    assert len(disc.plan["outputs"]) == 1


def test_structured_output_types_cover_plaza_downstream_choices():
    assert {
        "task",
        "task_execution",
        "evolution_item",
        "skill_candidate",
        "cost_governance",
    }.issubset(_ALLOWED_DISCUSSION_OUTPUT_TYPES)


def test_record_skill_candidate_output_without_target_ids_uses_team_anchor():
    plaza = Plaza(id="plaza-2", name="技能萃取广场")
    plaza.participants["agent-a"] = Participant(
        agent_id="agent-a",
        agent_name="Ops",
        team_id="public_cloud_ops",
    )
    disc = Discussion(
        id="disc-2",
        plaza_id=plaza.id,
        topic="公有云运维复盘",
        plan={"content": "将复盘沉淀成技能"},
    )

    output = _record_discussion_output(
        plaza,
        disc,
        output_type="skill_candidate",
        target_ids=[],
        team_id="public_cloud_ops",
        status_value="prepared",
    )

    assert output["id"] == "disc-2:skill_candidate:public_cloud_ops"
    assert output["type"] == "skill_candidate"
    assert output["status"] == "prepared"
    assert output["target_ids"] == []
    assert output["team_id"] == "public_cloud_ops"
    assert output["source"]["summary"] == "将复盘沉淀成技能"
