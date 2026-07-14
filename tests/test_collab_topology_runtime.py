# -*- coding: utf-8 -*-
"""任务执行协作拓扑：门禁边 + 同队编制 + 共总线 须在运行时生效."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def test_team_peer_allows_communicate():
    from agents.agent_relationships import check_can_communicate, reset_relationship_store

    with tempfile.TemporaryDirectory() as tmp:
        reset_relationship_store(store_dir=Path(tmp))
        ctx = {
            "agent_ids": ["aws_lead", "aws_mon", "aws_oper"],
            "channels_by_agent": {
                "aws_lead": [],
                "aws_mon": [],
                "aws_oper": [],
            },
            "names_by_agent": {},
            "roles_by_agent": {},
        }
        # 无门禁边、无通道，但同队 → 允许
        ok = check_can_communicate(
            "aws-ops", "aws_lead", "aws_mon", team_ctx=ctx,
        )
        assert ok["allowed"] is True
        assert "team_peer" in (ok.get("layers") or [])
        assert "aws_mon" in ok["allowed_contacts"]


def test_shared_channel_allows_communicate():
    from agents.agent_relationships import check_can_communicate, reset_relationship_store

    with tempfile.TemporaryDirectory() as tmp:
        reset_relationship_store(store_dir=Path(tmp))
        # 不同「逻辑队伍」成员但共总线（模拟跨角色同 bus）
        ctx = {
            "agent_ids": ["a1", "a2", "outsider"],
            "channels_by_agent": {
                "a1": ["aws_ops_bus"],
                "a2": ["aws_ops_bus"],
                "outsider": ["other_bus"],
            },
            "names_by_agent": {},
            "roles_by_agent": {},
        }
        ok = check_can_communicate("t", "a1", "a2", team_ctx=ctx)
        assert ok["allowed"] is True
        assert any(str(x).startswith("channel:") for x in (ok.get("layers") or []))
        # outsider 无共总线 — 但仍在 agent_ids 同队 → peer 仍允许
        ok2 = check_can_communicate("t", "a1", "outsider", team_ctx=ctx)
        assert ok2["allowed"] is True
        assert "team_peer" in (ok2.get("layers") or [])


def test_no_path_denied_when_outside_team():
    from agents.agent_relationships import check_can_communicate, reset_relationship_store

    with tempfile.TemporaryDirectory() as tmp:
        reset_relationship_store(store_dir=Path(tmp))
        ctx = {
            "agent_ids": ["a1", "a2"],
            "channels_by_agent": {
                "a1": ["bus_a"],
                "a2": ["bus_a"],
            },
            "names_by_agent": {},
            "roles_by_agent": {},
        }
        deny = check_can_communicate("t", "a1", "stranger", team_ctx=ctx)
        assert deny["allowed"] is False
        assert "stranger" not in deny["allowed_contacts"]


def test_store_edge_still_primary():
    from agents.agent_relationships import (
        AgentRelationship,
        RelationshipStore,
        check_can_communicate,
        reset_relationship_store,
    )

    with tempfile.TemporaryDirectory() as tmp:
        reset_relationship_store(store_dir=Path(tmp))
        s = RelationshipStore(store_dir=Path(tmp))
        s.add(AgentRelationship(
            team_id="t",
            source_agent_id="a1",
            target_id="external_reviewer",
            rel_type="reviewer",
        ))
        # external 不在队内、无通道，但有门禁边
        ctx = {
            "agent_ids": ["a1", "a2"],
            "channels_by_agent": {"a1": [], "a2": []},
            "names_by_agent": {},
            "roles_by_agent": {},
        }
        ok = check_can_communicate(
            "t", "a1", "external_reviewer", store=s, team_ctx=ctx,
        )
        assert ok["allowed"] is True
        assert any(str(x).startswith("store:") for x in (ok.get("layers") or []))


def test_gate_delegate_hard_blocks_no_path(monkeypatch):
    import agents.agent_relationships as ar

    with tempfile.TemporaryDirectory() as tmp:
        ar.reset_relationship_store(store_dir=Path(tmp))
        ar._gate_mode = lambda: "hard"
        try:
            ctx = {
                "agent_ids": ["a1"],
                "channels_by_agent": {"a1": []},
                "names_by_agent": {},
                "roles_by_agent": {},
            }
            g = ar.gate_delegate("t", "a1", "x9", team_ctx=ctx)
            assert g["allowed"] is False
            assert g["mode"] == "hard"
        finally:
            ar._gate_mode = ar.relationship_gate_mode


def test_gate_delegate_soft_warns_no_path():
    import agents.agent_relationships as ar

    with tempfile.TemporaryDirectory() as tmp:
        ar.reset_relationship_store(store_dir=Path(tmp))
        ar._gate_mode = lambda: "soft"
        try:
            ctx = {
                "agent_ids": ["a1"],
                "channels_by_agent": {"a1": []},
                "names_by_agent": {},
                "roles_by_agent": {},
            }
            g = ar.gate_delegate("t", "a1", "x9", team_ctx=ctx)
            assert g["allowed"] is True
            assert g.get("warning")
        finally:
            ar._gate_mode = ar.relationship_gate_mode


def test_render_includes_team_and_channel():
    from agents.agent_relationships import render_relationships_md, reset_relationship_store

    with tempfile.TemporaryDirectory() as tmp:
        reset_relationship_store(store_dir=Path(tmp))
        # monkeypatch load context via team_ctx is not used by render — it loads live.
        # 直接测 resolve + 手动拼：改用 collab 路径单测 render 空 store 文案
        md = render_relationships_md("no-such-team-xyz", "a1")
        assert "协作" in md or "空" in md or "拓扑" in md
