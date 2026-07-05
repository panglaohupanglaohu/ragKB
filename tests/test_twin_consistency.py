# -*- coding: utf-8 -*-
"""M5-2 孪生一致性评测 + M2-4/M2-5 世界快照透出 回归测试."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))

from sandbox.twin_consistency import compare_decision, consistency_report


def test_identical_decisions_are_trustworthy():
    pairs = [
        {"situation_id": "s1", "twin": {"action": "claim_task", "target": "t1"},
         "real": {"action": "claim_task", "target": "t1"}},
        {"situation_id": "s2", "twin": {"action": "offer_help", "target": "b", "skill_used": "code_review"},
         "real": {"action": "offer_help", "target": "b", "skill_used": "code_review"}},
    ]
    r = consistency_report(pairs)
    assert r["overall_rate"] == 1.0
    assert r["trustworthy"] is True
    assert r["verdict"] == "trustworthy"
    assert r["mismatches"] == []


def test_diverged_decisions_flagged_untrustworthy():
    pairs = [
        {"situation_id": "s1", "twin": {"action": "idle"}, "real": {"action": "work_on_task"}},
        {"situation_id": "s2", "twin": {"action": "delegate", "target": "x"},
         "real": {"action": "delegate", "target": "y"}},
    ]
    r = consistency_report(pairs)
    assert r["overall_rate"] == 0.0
    assert r["trustworthy"] is False
    assert r["verdict"] == "diverged"
    assert set(r["mismatches"]) == {"s1", "s2"}


def test_partial_consistency_rate_and_threshold():
    pairs = [
        {"situation_id": "a", "twin": {"action": "work_on_task"}, "real": {"action": "work_on_task"}},
        {"situation_id": "b", "twin": {"action": "work_on_task"}, "real": {"action": "work_on_task"}},
        {"situation_id": "c", "twin": {"action": "work_on_task"}, "real": {"action": "work_on_task"}},
        {"situation_id": "d", "twin": {"action": "idle"}, "real": {"action": "communicate"}},
    ]
    r = consistency_report(pairs, threshold=0.8)
    assert r["overall_rate"] == 0.75          # 3/4
    assert r["trustworthy"] is False          # 0.75 < 0.8
    assert r["mismatches"] == ["d"]
    # 放宽阈值即可信
    assert consistency_report(pairs, threshold=0.7)["trustworthy"] is True


def test_empty_pairs_is_no_data():
    r = consistency_report([])
    assert r["verdict"] == "no_data"
    assert r["trustworthy"] is False


def test_compare_decision_dimensions():
    cmp = compare_decision(
        {"action": "offer_help", "target": "b", "skill_used": "x"},
        {"action": "offer_help", "to": "b", "skill": "y"},
    )
    assert cmp["action_match"] is True
    assert cmp["target_match"] is True        # target 与 to 归一比较
    assert cmp["skill_match"] is False        # x != y
    assert cmp["full_match"] is False


def test_world_state_exposes_workflow_edges_and_room_stages():
    from sandbox.world_state import WorldStateManager
    ws = WorldStateManager()
    ws.sync_workflow([
        {"source": "pm", "target": "dev", "channel": "task", "message_type": "delegate"},
        {"source": "dev", "target": "qa", "channel": "artifact", "message_type": "request"},
    ])
    ws.set_room_stages({"research": 0, "build": 1, "review": 2})
    d = ws.to_dict()
    # M2-4: 明细透出（源→目标 + 传递语义）
    assert d["workflow_edges"] == 2
    detail = d["workflow_edges_detail"]
    assert detail[0]["source"] == "pm" and detail[0]["target"] == "dev"
    assert detail[0]["message_type"] == "delegate" and detail[0]["channel"] == "task"
    # M2-5: 房间阶段映射透出
    assert d["room_stages"] == {"research": 0, "build": 1, "review": 2}
