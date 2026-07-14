# -*- coding: utf-8 -*-
"""AgentsGroupConfig E-C 测试 — 关系网络与通信门禁 (EC-7) + EG-2 端到端串联."""

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def _store(tmp):
    from agents.agent_relationships import RelationshipStore
    return RelationshipStore(store_dir=Path(tmp))


def _rel(**kw):
    from agents.agent_relationships import AgentRelationship
    base = dict(team_id="teamA", kind="agent_agent", source_agent_id="a1",
                target_id="a2", rel_type="collaborator", note="测试")
    base.update(kw)
    return AgentRelationship(**base)


# ── EC-2: CRUD + 去重 ──────────────────────────────────────

def test_add_dedup_and_validation():
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        assert s.add(_rel())["ok"]
        dup = s.add(_rel())
        assert not dup["ok"] and dup["error"] == "duplicate"
        assert not s.add(_rel(rel_type="boss"))["ok"]            # 非法 rel_type → 但先撞去重? source/target相同 → duplicate; 换 target
        assert not s.add(_rel(target_id="a3", rel_type="boss"))["ok"]
        assert not s.add(_rel(target_id="a1"))["ok"]             # 自关系
        assert not s.add(_rel(source_agent_id=""))["ok"]         # 缺字段


def test_bidirectional_list_and_reload():
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        s.add(_rel())                                  # a1 → a2
        s.add(_rel(source_agent_id="a3", target_id="a1", rel_type="supervisor"))  # a3 → a1
        rels_a1 = s.list_for_agent("teamA", "a1")
        assert len(rels_a1) == 2                       # 双向
        assert len(s.list_for_agent("teamA", "a2")) == 1
        assert len(s.list_team("teamA")) == 2
        # 持久化重载
        s2 = _store(tmp)
        assert len(s2.list_team("teamA")) == 2
        rid = rels_a1[0].rel_id
        assert s2.remove("teamA", rid)
        assert not s2.remove("teamA", rid)


# ── EC-3: 通信门禁 ─────────────────────────────────────────

def test_can_communicate_allowed_and_denied():
    from agents.agent_relationships import check_can_communicate
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        s.add(_rel())  # a1 ↔ a2
        # 空队上下文：只靠门禁边
        empty_ctx = {
            "agent_ids": [],
            "channels_by_agent": {},
            "names_by_agent": {},
            "roles_by_agent": {},
        }
        ok = check_can_communicate("teamA", "a1", "a2", store=s, team_ctx=empty_ctx)
        assert ok["allowed"] and ("collaborator" in ok["reason"] or "store" in ok["reason"])
        # 反向也允许（关系是无向通信授权）
        assert check_can_communicate("teamA", "a2", "a1", store=s, team_ctx=empty_ctx)["allowed"]
        # 无关系 → 拒绝且只给授权名单
        deny = check_can_communicate("teamA", "a1", "a9", store=s, team_ctx=empty_ctx)
        assert not deny["allowed"]
        assert deny["allowed_contacts"] == ["a2"]
        # 自通信放行
        assert check_can_communicate("teamA", "a1", "a1", store=s, team_ctx=empty_ctx)["allowed"]


def test_render_relationships_md():
    from agents.agent_relationships import render_relationships_md, reset_relationship_store
    with tempfile.TemporaryDirectory() as tmp:
        reset_relationship_store(store_dir=Path(tmp))
        s = _store(tmp)
        # 空拓扑提示
        md0 = render_relationships_md("teamA", "a1", store=s)
        assert "协作" in md0 or "空" in md0 or "拓扑" in md0
        s.add(_rel(note="共建场景"))
        s.add(_rel(kind="agent_human", target_id="user_wu", rel_type="supervisor"))
        md = render_relationships_md("teamA", "a1", store=s)
        assert "协作者" in md or "a2" in md
        assert "user_wu" in md or "人类" in md
        assert "共建场景" in md or "a2" in md


# ── EC-4: 软/硬门禁 ────────────────────────────────────────

def test_gate_delegate_soft_and_hard(monkeypatch=None):
    import agents.agent_relationships as ar
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        ar.reset_relationship_store(store_dir=Path(tmp))
        try:
            s.add(_rel())
            # 软门禁（默认）: 无关系放行但带 warning
            orig = ar._gate_mode
            ar._gate_mode = lambda: "soft"
            soft = ar.gate_delegate("teamA", "a1", "a9")
            assert soft["allowed"] and "warning" in soft
            # 有关系: 无 warning
            ok = ar.gate_delegate("teamA", "a1", "a2")
            assert ok["allowed"] and "warning" not in ok
            # 硬门禁: 拒绝
            ar._gate_mode = lambda: "hard"
            hard = ar.gate_delegate("teamA", "a1", "a9")
            assert not hard["allowed"] and hard["mode"] == "hard"
            assert hard["allowed_contacts"] == ["a2"]
        finally:
            ar._gate_mode = orig
            ar.reset_relationship_store()


# ── EG-2: 端到端串联 ────────────────────────────────────────

def test_e2e_employee_chain():
    """建关系 → focus 条目 → cron trigger(绑定) → tick 唤醒 → 组织上下文齐全 → 门禁拒绝陌生人."""
    from agents.employee_profile import EmployeeProfileStore, build_organizational_context
    from agents.agent_triggers import AgentTrigger, TriggerStore, TriggerDaemon, validate_trigger
    from agents.agent_relationships import RelationshipStore, AgentRelationship, check_can_communicate
    import agents.agent_relationships as ar

    NOW = datetime(2026, 6, 12, 1, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as tmp:
        emp = EmployeeProfileStore(base_dir=Path(tmp) / "emp")
        rels = RelationshipStore(store_dir=Path(tmp) / "rel")
        trgs = TriggerStore(store_dir=Path(tmp) / "trg")
        daemon = TriggerDaemon(store=trgs, wake_log=Path(tmp) / "wake.jsonl")
        ar.reset_relationship_store(store_dir=Path(tmp) / "rel")
        try:
            # 1) 档案 + focus 条目
            emp.ensure_defaults("analyst", {"name": "分析师", "role": "市场分析"})
            emp.write_file("analyst", "focus", "- [ ] 每日竞品快报")
            # 2) 关系: analyst ↔ director
            rels.add(AgentRelationship(team_id="teamA", source_agent_id="analyst",
                                       target_id="director", rel_type="supervisor"))
            # 3) cron trigger 绑定 focus（北京 9 点 = UTC 1 点）
            trg = AgentTrigger(agent_id="analyst", team_id="teamA", trigger_type="cron",
                               focus_item="每日竞品快报",
                               config={"expr": "0 9 * * *", "tz_offset_min": 480})
            assert validate_trigger(trg, focus_checker=emp.focus_item_exists) == []
            trgs.add(trg)
            # 4) daemon tick 在 UTC 01:00 唤醒
            events = daemon.tick(NOW)
            assert len(events) == 1 and events[0]["focus_item"] == "每日竞品快报"
            # 5) 组织上下文四节齐全且含关系
            ctx = build_organizational_context("teamA", "analyst", store=emp)
            assert "每日竞品快报" in ctx["system_prefix"]
            assert "director" in ctx["sections"]["relationships"]
            # 6) 门禁: 找 director 放行，找陌生人拒绝
            assert check_can_communicate("teamA", "analyst", "director", store=rels)["allowed"]
            deny = check_can_communicate("teamA", "analyst", "stranger", store=rels)
            assert not deny["allowed"] and deny["allowed_contacts"] == ["director"]
        finally:
            ar.reset_relationship_store()
