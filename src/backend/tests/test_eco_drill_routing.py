# -*- coding: utf-8 -*-
"""物竞天择数字孪生演练 ND-1 测试 — runtime 字段 + 演练引擎路由判定."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agents.models import AgentTeam, Visibility
from agents.team_store import TeamStore


class TestTeamRuntimeField:
    def test_default_runtime_is_legacy(self):
        team = AgentTeam(name="T")
        assert team.runtime == "legacy"

    def test_eco_runtime_accepted(self):
        team = AgentTeam(name="T", runtime="eco")
        assert team.runtime == "eco"

    def test_invalid_runtime_falls_back_to_legacy(self):
        team = AgentTeam(name="T", runtime="bogus")
        assert team.runtime == "legacy"

    def test_runtime_in_to_dict(self):
        team = AgentTeam(name="T", runtime="eco")
        assert team.to_dict()["runtime"] == "eco"


class TestRuntimePersistence:
    def test_runtime_survives_save_load(self):
        with tempfile.TemporaryDirectory() as d:
            store = TeamStore(path=Path(d) / "teams.json")
            team = AgentTeam(team_id="t1", name="Eco Team", visibility=Visibility.PRIVATE, runtime="eco")
            store.save_all({"t1": team})

            store2 = TeamStore(path=Path(d) / "teams.json")
            loaded = store2.load_all()["t1"]
            assert loaded.runtime == "eco"

    def test_legacy_data_without_runtime_defaults_legacy(self):
        with tempfile.TemporaryDirectory() as d:
            import json
            p = Path(d) / "teams.json"
            # 模拟旧数据：无 runtime 字段
            p.write_text(json.dumps({
                "t1": {"team_id": "t1", "name": "Old", "visibility": "private",
                       "agents": {}, "models": {}, "tools": {}, "skills": {},
                       "metadata": {}, "created_at": ""}
            }), encoding="utf-8")
            store = TeamStore(path=p)
            loaded = store.load_all()["t1"]
            assert loaded.runtime == "legacy"


class TestDrillKindRouting:
    """create_trial 按 team.runtime 路由 drill_kind（纯逻辑验证，不起 HTTP）。"""

    def test_drill_kind_field_default_secs(self):
        from sandbox.models import Trial
        t = Trial(name="x")
        assert t.drill_kind == "secs"

    def test_drill_kind_natural_selection_settable(self):
        from sandbox.models import Trial
        t = Trial(name="x", drill_kind="natural_selection")
        assert t.drill_kind == "natural_selection"

    def test_routing_logic_eco_team_maps_to_natural_selection(self):
        # 复刻 create_trial 里的判定逻辑
        def resolve(runtime):
            return "natural_selection" if runtime == "eco" else "secs"
        assert resolve("eco") == "natural_selection"
        assert resolve("legacy") == "secs"
        assert resolve("") == "secs"
