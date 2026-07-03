# -*- coding: utf-8 -*-
"""AgentsGroupConfig E-A/E-D 测试 — 四件套档案 + 组织上下文 + 治理校验 (EA-6/ED-4)."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def _store(tmp):
    from agents.employee_profile import EmployeeProfileStore
    return EmployeeProfileStore(base_dir=Path(tmp))


# ── EA-1: 四件套默认模板 ────────────────────────────────────

def test_ensure_defaults_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        profile = {"name": "小析", "role": "分析师", "system_prompt": "严谨求证",
                   "personality": {"tone": "冷静"}}
        created = s.ensure_defaults("a1", profile)
        assert set(created) == {"soul", "memory", "focus", "heartbeat"}
        # 幂等: 第二次不再创建
        assert s.ensure_defaults("a1", profile) == {}
        soul = s.read_file("a1", "soul")
        assert "小析" in soul["content"] and "分析师" in soul["content"] and "严谨求证" in soul["content"]
        hb = s.read_file("a1", "heartbeat")
        assert "阶段一" in hb["content"] and "HEARTBEAT_OK" in hb["content"]


def test_kind_whitelist():
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        try:
            s.read_file("a1", "passwd")
            assert False, "应抛 KeyError"
        except KeyError:
            pass


def test_write_and_read_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        r = s.write_file("a1", "soul", "# 新灵魂")
        assert r["ok"]
        assert s.read_file("a1", "soul")["content"] == "# 新灵魂"


# ── EA-3: memory append-only ───────────────────────────────

def test_memory_append_only():
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        # 整写被拒
        r = s.write_file("a1", "memory", "覆盖")
        assert not r["ok"] and r["error"] == "memory_is_append_only"
        # 追加成功且累计
        assert s.append_memory("a1", "教训一: 不要在周五发布", "trial")["entries"] == 1
        assert s.append_memory("a1", "教训二: 评审先行", "human")["entries"] == 2
        content = s.read_file("a1", "memory")["content"]
        assert "教训一" in content and "教训二" in content and "append-only" in content
        # 空条目拒绝 / 超长截断
        assert not s.append_memory("a1", "  ")["ok"]
        s.append_memory("a1", "x" * 3000)
        assert "…(截断)" in s.read_file("a1", "memory")["content"]


# ── EA-2: focus 解析 ────────────────────────────────────────

def test_focus_parse_and_exists():
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        s.write_file("a1", "focus", "# 聚焦\n\n- [ ] 跟进进化\n- [x] 完成评审\n普通行\n- [ ]  带空格的项  \n")
        items = s.parse_focus_items("a1")
        assert len(items) == 3
        assert items[0] == {"text": "跟进进化", "done": False}
        assert items[1] == {"text": "完成评审", "done": True}
        assert s.focus_item_exists("a1", "跟进进化")
        assert s.focus_item_exists("a1", " 带空格的项 ")
        assert not s.focus_item_exists("a1", "不存在的项")
        assert not s.focus_item_exists("a1", "")


# ── EA-5: 组织上下文 ────────────────────────────────────────

def test_build_organizational_context_sections():
    from agents.employee_profile import build_organizational_context
    with tempfile.TemporaryDirectory() as tmp:
        s = _store(tmp)
        s.ensure_defaults("a1", {"name": "N", "role": "R"})
        s.write_file("a1", "focus", "- [ ] 关键事项X")
        ctx = build_organizational_context("ghost_team", "a1", store=s)
        assert set(ctx["sections"]) == {"soul", "focus", "relationships", "team_context"}
        sp = ctx["system_prefix"]
        for header in ("灵魂锚定", "当前聚焦", "我能联系谁", "团队共享认知"):
            assert header in sp
        assert "关键事项X" in sp
        assert len(sp) <= 8100  # 截断上限


# ── ED-2: L1-L4 判定矩阵 ────────────────────────────────────

def test_autonomy_matrix():
    from agents.employee_profile import check_action_allowed
    cases = [
        # (level, risk, allowed, needs_approval)
        (1, 1, True, False), (1, 2, False, True), (1, 3, False, False), (1, 4, False, False),
        (2, 2, True, False), (2, 3, False, True), (2, 4, False, False),
        (3, 3, True, False), (3, 4, False, True),
        (4, 4, True, False), (4, 1, True, False),
    ]
    for level, risk, allowed, approval in cases:
        r = check_action_allowed({"autonomy_level": level}, risk)
        assert r["allowed"] == allowed and r["needs_approval"] == approval, (level, risk, r)


# ── ED-3: Token 预算 ────────────────────────────────────────

def test_token_budget_unlimited_and_exceeded():
    from agents.employee_profile import check_token_budget

    class FakeUsage:
        def __init__(self, used): self._u = used
        def get_agent_daily_total(self, agent_id, date): return self._u

    # 0 = 不限
    r0 = check_token_budget({"agent_id": "a1", "token_budget": 0}, usage_store=FakeUsage(999999))
    assert r0["within"] and r0["budget"] == 0
    # 限额内
    r1 = check_token_budget({"agent_id": "a1", "token_budget": 1000}, usage_store=FakeUsage(500))
    assert r1["within"] and r1["used_today"] == 500
    # 超限
    r2 = check_token_budget({"agent_id": "a1", "token_budget": 1000}, usage_store=FakeUsage(1500))
    assert not r2["within"]


# ── ED-1: 旧数据反序列化兼容 ────────────────────────────────

def test_agent_profile_backward_compat():
    from agents.models import AgentProfile
    p = AgentProfile(name="x", role="r")
    assert p.autonomy_level == 2 and p.token_budget == 0 and p.fallback_model_id == ""
    d = p.to_dict()
    assert d["autonomy_level"] == 2 and "token_budget" in d and "fallback_model_id" in d
    # team_store 反序列化旧 dict（无新字段）不崩
    from agents.team_store import TeamStore
    old_dict = {k: v for k, v in d.items()
                if k not in ("autonomy_level", "token_budget", "fallback_model_id")}
    agent = TeamStore._deserialize_agent(old_dict) if hasattr(TeamStore, "_deserialize_agent") else None
    if agent is not None:
        assert agent.autonomy_level == 2
