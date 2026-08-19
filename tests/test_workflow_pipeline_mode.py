# -*- coding: utf-8 -*-
"""Verification check for team workflow pipeline mode & multi-agent division of labor."""

import sys
import types
from pathlib import Path

# Ensure src/backend is in sys.path
backend_path = Path(__file__).resolve().parent.parent / "src" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from agents.models import AgentTeam, AgentProfile
from agents.team_store import TeamStore
import agents.api as api


def test_agent_team_model_workflow_mode():
    # Default is single
    t1 = AgentTeam(name="Team1")
    assert t1.workflow_mode == "single"
    assert t1.to_dict()["workflow_mode"] == "single"

    # Explicit full
    t2 = AgentTeam(name="Team2", workflow_mode="full")
    assert t2.workflow_mode == "full"
    assert t2.to_dict()["workflow_mode"] == "full"

    # Invalid fallback
    t3 = AgentTeam(name="Team3", workflow_mode="invalid_mode")
    assert t3.workflow_mode == "single"


def test_team_store_roundtrip_and_backward_compat():
    # Backward compatibility: old data missing workflow_mode defaults to single
    old_data = {"team_id": "old_1", "name": "Old Team"}
    t_old = TeamStore._deserialize_team(old_data)
    assert t_old.workflow_mode == "single"

    # Full mode roundtrip
    full_data = {"team_id": "full_1", "name": "Full Team", "workflow_mode": "full"}
    t_full = TeamStore._deserialize_team(full_data)
    assert t_full.workflow_mode == "full"
    assert t_full.to_dict()["workflow_mode"] == "full"


def test_generate_workflow_single_vs_full():
    team_single = AgentTeam(team_id="t_single", name="Single Team", workflow_mode="single")
    team_full = AgentTeam(team_id="t_full", name="Full Team", workflow_mode="dev")
    team_xops = AgentTeam(team_id="t_xops", name="公有云xOPs", workflow_mode="xops")
    team_star = AgentTeam(team_id="t_star", name="星型团队", workflow_mode="star")
    team_custom = AgentTeam(
        team_id="t_custom",
        name="自定义连线团队",
        workflow_mode="custom",
        metadata={"custom_topology": [
            {"source": "a_owner", "target": "a_sre"},
            {"source": "a_sre", "target": "a_auto"},
        ]}
    )

    # Add agents with ops roles (mimicking 公有云xOPs)
    agents = [
        AgentProfile(agent_id="a_owner", name="云平台负责人", role="cloud_ops_finops_owner"),
        AgentProfile(agent_id="a_finops", name="FinOps分析师", role="finops_analyst"),
        AgentProfile(agent_id="a_sre", name="SRE架构师", role="platform_sre_architect"),
        AgentProfile(agent_id="a_auto", name="自动化工程师", role="automation_platform_engineer"),
        AgentProfile(agent_id="a_sec", name="安全合规工程师", role="security_compliance_engineer"),
        AgentProfile(agent_id="a_aws", name="AWS负责人", role="aws_service_owner"),
        AgentProfile(agent_id="a_doc", name="文档治理", role="domestic_cloud_service_owner"),
    ]
    for a in agents:
        team_single.add_agent(a)
        team_full.add_agent(a)
        team_xops.add_agent(a)
        team_star.add_agent(a)
        team_custom.add_agent(a)

    class MockTM:
        def __init__(self, teams_map):
            self.teams_map = teams_map
        def get_team(self, tid):
            return self.teams_map.get(tid)
        def get_agent(self, tid, aid):
            t = self.teams_map.get(tid)
            return t.agents.get(aid) if t else None

    api._team_manager = MockTM({
        "t_single": team_single,
        "t_full": team_full,
        "t_xops": team_xops,
        "t_star": team_star,
        "t_custom": team_custom,
    })

    # 1. Single mode -> 1 step
    task_single = types.SimpleNamespace(agent_id="a_owner", metadata={}, status=types.SimpleNamespace(value="pending"))
    steps_s = api._generate_workflow(task_single, "t_single")
    assert len(steps_s) == 1
    assert steps_s[0]["key"] == "execute"

    # 2. Dev mode -> 7 steps
    task_full = types.SimpleNamespace(agent_id="a_owner", metadata={}, status=types.SimpleNamespace(value="pending"))
    steps_f = api._generate_workflow(task_full, "t_full")
    assert len(steps_f) == 7
    step_keys = [s["key"] for s in steps_f]
    assert step_keys == [
        "pm_decompose", "research", "architecture", "develop", "test", "deploy", "document"
    ]

    # 3. xOPs mode -> 7 specialized ops steps
    steps_x = api._generate_workflow(task_full, "t_xops")
    assert len(steps_x) == 7
    assert [s["key"] for s in steps_x] == [
        "ops_triage", "sre_design", "automation_exec", "cloud_delivery", "security_audit", "finops_review", "sop_postmortem"
    ]
    assert steps_x[0]["agent_id"] == "a_owner"   # 事件响应 -> 负责人
    assert steps_x[1]["agent_id"] == "a_sre"     # SRE设计 -> SRE架构师
    assert steps_x[2]["agent_id"] == "a_auto"    # 自动化实施 -> 自动化工程师
    assert steps_x[3]["agent_id"] == "a_aws"     # 多云落地 -> AWS负责人
    assert steps_x[4]["agent_id"] == "a_sec"     # 安全合规 -> 安全合规工程师
    assert steps_x[5]["agent_id"] == "a_finops"  # FinOps复盘 -> FinOps分析师
    assert steps_x[6]["agent_id"] == "a_doc"     # 运营SOP -> 文档治理

    # 4. Custom mode -> steps generated from user's custom topology links
    steps_c = api._generate_workflow(task_full, "t_custom")
    assert len(steps_c) == 3
    assert steps_c[0]["agent_id"] == "a_owner"
    assert steps_c[1]["agent_id"] == "a_sre"
    assert steps_c[2]["agent_id"] == "a_auto"


if __name__ == "__main__":
    test_agent_team_model_workflow_mode()
    test_team_store_roundtrip_and_backward_compat()
    test_generate_workflow_single_vs_full()
    print("All workflow pipeline mode verification tests passed successfully!")
    test_team_store_roundtrip_and_backward_compat()
    test_generate_workflow_single_vs_full()
    print("All workflow pipeline mode verification tests passed successfully!")
