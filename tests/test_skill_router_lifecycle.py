# -*- coding: utf-8 -*-
"""SkillRouter lifecycle reweight + affinity state persistence."""

from __future__ import annotations

import json
from pathlib import Path

from agents.skill_router import SkillRouter, _ROUTER_STATE_PATH


def test_lifecycle_multiplier_verified_gt_draft():
    v, _ = SkillRouter._lifecycle_multiplier({"lifecycle_stage": "verified"})
    d, _ = SkillRouter._lifecycle_multiplier({"lifecycle_stage": "draft"})
    g, _ = SkillRouter._lifecycle_multiplier({"lifecycle_stage": "degraded"})
    assert v > 1.0
    assert d < 1.0
    assert g < d


def test_route_prefers_verified_over_draft_when_text_similar(tmp_path, monkeypatch):
    # isolate state file
    state = tmp_path / "skill_router_state.json"
    monkeypatch.setattr("agents.skill_router._ROUTER_STATE_PATH", state)

    # Identical text; only lifecycle differs → verified must win after reweight
    base = {
        "name": "协作 SOP",
        "description": "Agent 协作流程标准化",
        "category": "research",
        "instructions": "步骤一 传递任务 步骤二 验收 步骤三 回滚",
        "icon": "⚡",
        "required_tools": [],
    }

    class Lib:
        def browse(self, team_id=""):
            return [
                {**base, "skill_id": "s_draft", "lifecycle_stage": "draft"},
                {**base, "skill_id": "s_verified", "lifecycle_stage": "verified"},
            ]

    router = SkillRouter(skill_library=Lib())
    session = router.route(query="Agent 协作 SOP 流程", team_id="t1", top_k=2)
    assert session.results
    assert session.results[0].skill_id == "s_verified"
    assert session.results[0].score >= session.results[1].score
    reasons = " ".join(session.results[0].match_reasons or [])
    assert "生命周期" in reasons


def test_affinity_persists_across_instances(tmp_path, monkeypatch):
    state = tmp_path / "skill_router_state.json"
    monkeypatch.setattr("agents.skill_router._ROUTER_STATE_PATH", state)

    class Lib:
        def browse(self, team_id=""):
            return [{
                "skill_id": "sk1",
                "name": "code review",
                "description": "代码评审",
                "category": "development",
                "instructions": "检查接口与测试",
                "lifecycle_stage": "team_local",
            }]

    r1 = SkillRouter(skill_library=Lib())
    r1._affinity_boosts[("agent_a", "development")] = 0.2
    r1._save_state()
    assert state.is_file()

    r2 = SkillRouter(skill_library=Lib())
    assert r2._affinity_boosts.get(("agent_a", "development")) == 0.2
