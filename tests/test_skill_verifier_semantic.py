# -*- coding: utf-8 -*-
"""Semantic verification layer for SkillVerifier."""

from __future__ import annotations

from agents.models import SkillDefinition
from agents.skill_verifier import SkillVerifier


def _skill(**kwargs) -> SkillDefinition:
    defaults = dict(
        skill_id="sv1",
        name="协作 SOP",
        description="Agent 协作流程",
        instructions=(
            "1. 明确业务目标与验收口径\n"
            "2. 传递任务上下文与依赖\n"
            "3. 阻塞时升级并设定超时\n"
            "4. 失败时回滚并记录原因\n"
            "使用 read_file 读取规范，run_in_terminal 跑检查。"
        ),
        required_tools=["read_file", "run_in_terminal"],
        slug="collab-sop",
    )
    defaults.update(kwargs)
    return SkillDefinition(**defaults)


def test_semantic_passes_good_skill():
    v = SkillVerifier()
    skill = _skill()
    scenarios = [
        {"scenario": "协作验收", "prompt": "按 SOP 做任务传递与验收"},
        {"scenario": "阻塞回滚", "prompt": "超时后回滚并记录"},
    ]
    checks = v._semantic_checks(skill, scenarios)
    by_name = {c["name"]: c for c in checks}
    assert by_name["not_offline_placeholder"]["passed"] is True
    assert by_name["has_procedure_steps"]["passed"] is True
    assert by_name["tools_grounded_in_instructions"]["passed"] is True
    assert by_name["mock_tools_execute"]["passed"] is True
    assert by_name["scenarios_mostly_aligned"]["passed"] is True


def test_semantic_hard_fails_offline_placeholder():
    v = SkillVerifier()
    skill = _skill(
        name="【回退草稿】议题",
        description="离线占位草案（非正式技能名）",
        instructions="1. 列出业务目标\n2. 明确约束",
        required_tools=[],
    )
    checks = v._semantic_checks(skill, [{"scenario": "x", "prompt": "y"}])
    offline = next(c for c in checks if c["name"] == "not_offline_placeholder")
    assert offline["passed"] is False
    assert offline.get("hard_fail") is True


def test_semantic_tools_ungrounded():
    v = SkillVerifier()
    skill = _skill(
        instructions="1. 做计划\n2. 交付结果并验收",
        required_tools=["read_file", "web_search"],
    )
    checks = v._semantic_checks(skill, [{"scenario": "计划验收", "prompt": "交付"}])
    grounded = next(c for c in checks if c["name"] == "tools_grounded_in_instructions")
    assert grounded["passed"] is False
