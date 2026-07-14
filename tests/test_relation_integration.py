# -*- coding: utf-8 -*-
"""物竞 → 关系边 suggest/apply（XF-7.1 / XF-7.3）."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def _sample_result():
    return {
        "final_ranking": [
            {
                "agent_id": "aws_mon",
                "population": "aws-ops",
                "survival_ticks": 100,
                "collab_genome": {
                    "share_tendency": 0.8,
                    "signal_tendency": 0.9,
                    "follow_tendency": 0.3,
                    "mate_choosiness": 0.5,
                },
            },
            {
                "agent_id": "aws_ops",
                "population": "aws-ops",
                "survival_ticks": 80,
                "collab_genome": {
                    "share_tendency": 0.7,
                    "signal_tendency": 0.6,
                    "follow_tendency": 0.9,
                    "mate_choosiness": 0.1,
                },
            },
            {
                "agent_id": "aws_lonely",
                "population": "other",
                "survival_ticks": 10,
                "collab_genome": {
                    "share_tendency": 0.1,
                    "signal_tendency": 0.1,
                    "follow_tendency": 0.1,
                    "mate_choosiness": 0.9,
                },
            },
        ],
        "timeline": {
            "steps": [
                {
                    "actions": {
                        "aws_mon": {
                            "signals": ["FOOD@es"],
                            "shared_to": "aws_ops",
                            "followed": False,
                        },
                        "aws_ops": {
                            "signals": [],
                            "followed": True,
                            "shared_to": None,
                        },
                        "aws_lonely": {
                            "signals": ["COURT"],
                            "followed": False,
                            "shared_to": None,
                        },
                    }
                }
            ]
        },
    }


def test_build_relation_suggestions_share_and_follow():
    from sandbox.relation_integration import build_relation_suggestions

    rep = build_relation_suggestions(_sample_result(), team_id="aws-ops", top_k=24)
    assert rep["count"] >= 2
    pairs = {(s["source_agent_id"], s["target_id"]) for s in rep["suggestions"]}
    # share 双向
    assert ("aws_mon", "aws_ops") in pairs
    assert ("aws_ops", "aws_mon") in pairs
    # follow: mon 发 FOOD，ops followed → mon→ops
    mon_ops = next(
        s for s in rep["suggestions"]
        if s["source_agent_id"] == "aws_mon" and s["target_id"] == "aws_ops"
    )
    assert mon_ops["weight"] >= 2.0
    assert "share" in mon_ops["reasons"] or "follow_food" in mon_ops["reasons"]
    # COURT 不产生 lonely 边
    lonely_edges = [
        s for s in rep["suggestions"]
        if s["source_agent_id"] == "aws_lonely" or s["target_id"] == "aws_lonely"
    ]
    assert not any("mate" in (s.get("note") or "") for s in lonely_edges)


def test_already_exists_marked():
    from sandbox.relation_integration import build_relation_suggestions

    existing = [
        {
            "source_agent_id": "aws_mon",
            "target_id": "aws_ops",
            "kind": "agent_agent",
        }
    ]
    rep = build_relation_suggestions(
        _sample_result(),
        team_id="aws-ops",
        existing_edges=existing,
    )
    mon_ops = next(
        s for s in rep["suggestions"]
        if s["source_agent_id"] == "aws_mon" and s["target_id"] == "aws_ops"
    )
    assert mon_ops["already_exists"] is True
    assert mon_ops["default_checked"] is False
    # before 真边快照
    assert rep["before_store_count"] == 1
    assert rep["before_store"][0]["source_agent_id"] == "aws_mon"
    assert rep["before_store"][0]["status"] == "existing"
    assert rep["before_source"] == "store"


def test_aws_ops_channel_soft_before_when_store_empty():
    """aws-ops 全员 aws_ops_bus：RelationshipStore 空时 Before 应有通道软边."""
    from sandbox.relation_integration import build_relation_suggestions

    agent_channels = {
        "aws_lead": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": True}],
        "aws_mon": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": True}],
        "aws_oper": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": False}],
        "aws_arch": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": True}],
        "aws_cost": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": True}],
        "aws_region": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": True}],
    }
    rep = build_relation_suggestions(
        {"final_ranking": [], "timeline": {"steps": []}},
        team_id="aws-ops",
        existing_edges=[],
        agent_channels=agent_channels,
        agent_ids=list(agent_channels.keys()),
    )
    assert rep["before_store_count"] == 0
    assert rep["before_source"] == "channel"
    # C(6,2)=15 无向通道边
    assert rep["before_channel_count"] == 15
    assert rep["before_count"] == 15
    assert all(e["status"] == "channel" for e in rep["before"])


def test_apply_confirm_false_zero_write():
    """模拟 apply 层逻辑：confirm=false 不碰 store（单元测 pure materialize + store 手工）."""
    from agents.agent_relationships import AgentRelationship, RelationshipStore
    from sandbox.relation_integration import materialize_relation

    with tempfile.TemporaryDirectory() as tmp:
        store = RelationshipStore(store_dir=Path(tmp))
        sug = {
            "source_agent_id": "a1",
            "target_id": "a2",
            "note": "eco:share",
        }
        # confirm=false 路径：只 materialize，不 add
        payload = materialize_relation(sug, team_id="t1", fingerprint="fp1234567890ab")
        assert payload["created_by"] == "human_via_eco_feedback"
        assert "fp:" in payload["note"]
        assert len(store.list_team("t1")) == 0


def test_apply_confirm_true_writes_and_dedup():
    from agents.agent_relationships import AgentRelationship, RelationshipStore
    from sandbox.relation_integration import materialize_relation

    with tempfile.TemporaryDirectory() as tmp:
        store = RelationshipStore(store_dir=Path(tmp))
        payload = materialize_relation(
            {"source_agent_id": "a1", "target_id": "a2", "note": "eco:share"},
            team_id="t1",
            fingerprint="eco_fp_test",
        )
        rel = AgentRelationship(**payload)
        r1 = store.add(rel)
        assert r1["ok"]
        # 同 source/target 去重
        r2 = store.add(AgentRelationship(**payload))
        assert not r2["ok"] and r2["error"] == "duplicate"
        rels = store.list_team("t1")
        assert len(rels) == 1
        assert rels[0].created_by == "human_via_eco_feedback"
        assert "eco:share" in rels[0].note
