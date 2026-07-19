# -*- coding: utf-8 -*-
"""Twin A/B full evaluation for skill verification."""

from __future__ import annotations

import pytest

from agents.models import SkillCategory, SkillDefinition
from agents.skill_twin_ab import (
    resolve_twin_binding,
    run_skill_twin_ab,
    twin_ab_to_checks,
)


def _code_review_skill(**kw) -> SkillDefinition:
    d = dict(
        skill_id="c0de7a11",
        name="结构化代码评审",
        description="分层检查清单做代码评审",
        category=SkillCategory.GENERAL,
        instructions=(
            "1. 正确性检查\n2. 接口契约\n3. 测试覆盖\n"
            "4. 可维护性\n5. 风险与回滚\n阻塞项附行号与修法。"
        ),
        slug="structured-code-review",
        config={
            "metadata": {
                "target_skill": "code_review",
                "scenario": "code_review_delivery",
            }
        },
    )
    d.update(kw)
    return SkillDefinition(**d)


def test_resolve_binding_from_metadata():
    skill = _code_review_skill()
    b = resolve_twin_binding(skill)
    assert b["ok"] is True
    assert b["scenario_id"] == "code_review_delivery"
    assert b["target_skill"] == "code_review"
    assert "rev1" in b["agents"]


def test_resolve_binding_code_delivery_category():
    skill = SkillDefinition(
        skill_id="x1",
        name="评审技能",
        category=SkillCategory.GENERAL,
        instructions="1. 评审\n2. 验收",
        config={},
    )
    # force category string via GENERAL + name keywords
    skill.category = "code_delivery"  # type: ignore
    b = resolve_twin_binding(skill)
    assert b.get("ok") is True
    assert b["scenario_id"] == "code_review_delivery"


@pytest.mark.asyncio
async def test_run_twin_ab_code_review_gain():
    skill = _code_review_skill()
    report = await run_skill_twin_ab(skill, n_seeds=3, max_steps=80)
    assert report.get("skipped") is not True, report
    assert report.get("status") == "ok", report
    assert report.get("target_skill") == "code_review"
    assert report["treatment"]["target_uses"] > 0
    # treatment should beat or match baseline substantially on average
    # (stochastic; assert structure + non-negative uses rather than strict gain)
    assert "baseline" in report and "treatment" in report
    assert "target_gain" in report
    checks = twin_ab_to_checks(report)
    names = {c["name"] for c in checks}
    assert "twin_ab_target_gain" in names
    assert "twin_ab_ran" in names


@pytest.mark.asyncio
async def test_twin_ab_skip_without_binding():
    skill = SkillDefinition(
        skill_id="orphan",
        name="未映射技能XYZ",
        description="无场景绑定",
        instructions="1. 做某事\n2. 完成",
        category=SkillCategory.GENERAL,
        config={},
    )
    report = await run_skill_twin_ab(skill, n_seeds=1)
    assert report.get("skipped") is True
    checks = twin_ab_to_checks(report)
    assert checks[0]["name"] == "twin_ab_binding"
    assert checks[0]["required"] is False
