# -*- coding: utf-8 -*-
"""写回建议只含未绑定 skill；优先 reserve / plan_demand."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from sandbox.skill_integration import build_integration_report  # noqa: E402


def test_recommendations_exclude_already_bound():
    result = {
        "final_ranking": [
            {
                "agent_id": "aws_mon",
                "alive": True,
                "survival_ticks": 90,
                "skill_genome": ["monitor_alarms_setup"],
            },
            {
                "agent_id": "aws_cost",
                "alive": True,
                "survival_ticks": 50,
                "skill_genome": ["cost_ri_advisor"],
            },
        ]
    }
    contract = {
        "plan_id": "p1",
        "niches": [
            {"demanded_skills": ["monitor_alarms_setup", "cost_ri_advisor", "aws_es_scaling_orchestration"]},
        ],
        "provenance": {"fingerprint": "fp"},
    }
    rep = build_integration_report(
        result,
        contract,
        agent_bound_skills={"aws_mon": ["monitor_alarms_setup"]},
        reserve_skill_ids=["reserve_skill_x", "cost_ri_advisor"],
        team_skill_ids=["monitor_alarms_setup", "cost_ri_advisor", "aws_es_scaling_orchestration", "reserve_skill_x"],
    )
    mon = next(b for b in rep["recommended_bindings"] if b["agent_id"] == "aws_mon")
    assert "monitor_alarms_setup" not in mon["add_skills"]
    # 契约 demand / reserve 中未绑定的应出现
    assert "cost_ri_advisor" in mon["add_skills"] or "aws_es_scaling_orchestration" in mon["add_skills"]
    assert "reserve_skill_x" in mon["add_skills"] or mon["skill_sources"].get("cost_ri_advisor") in (
        "plan_demand", "dominant", "reserve", "team_library"
    )


def test_no_fallback_to_bound_when_nothing_missing():
    result = {
        "final_ranking": [
            {
                "agent_id": "aws_mon",
                "alive": True,
                "survival_ticks": 10,
                "skill_genome": ["only_one"],
            }
        ]
    }
    contract = {"niches": [{"demanded_skills": ["only_one"]}]}
    rep = build_integration_report(
        result,
        contract,
        agent_bound_skills={"aws_mon": ["only_one"]},
        reserve_skill_ids=[],
        team_skill_ids=["only_one"],
    )
    mon = next(b for b in rep["recommended_bindings"] if b["agent_id"] == "aws_mon")
    assert mon["add_skills"] == []
    assert mon["reason"] == "no_unbound_candidates"
