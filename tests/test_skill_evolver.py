# -*- coding: utf-8 -*-
"""Unit tests for SkillEvolver rewrite: language guard + JSON draft parse."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from agents.skill_evolver import (
    SkillEvolver,
    _detect_language_code,
    _instruction_language_hint,
    _is_language_flip,
)
from agents.models import SkillDefinition


def _parse(raw: str):
    return SkillEvolver._parse_evolution_json(raw)


ZH_INSTR = """基于原文片段：
1. 列出业务目标与验收口径
2. 明确前置条件、依赖与不可变约束
3. 输出「必须做 / 可选做 / 禁止做」三栏
4. 补最小验证步骤与回滚点
"""

EN_SOP = """1) Goal & acceptance: define measurable KPIs and SLAs
2) Preconditions & constraints: list required inputs
3) RACI & handoffs: assign roles and escalation
4) Task/context passing: message schemas and auth
5) Completion criteria: validation checks and sign-off
6) Blocking & fallback: retry backoff circuit breakers
7) Traceability: logging and audit fields
8) Validation & rollback: recovery procedures
9) Review cadence: versioning and approvals
10) Output: structured SOP document with checklists
"""


def test_language_hint_and_code_zh():
    assert "中文" in _instruction_language_hint(ZH_INSTR)
    assert _detect_language_code(ZH_INSTR) == "zh"


def test_language_flip_zh_to_en():
    assert _is_language_flip(ZH_INSTR, EN_SOP) is True
    assert _is_language_flip(ZH_INSTR, ZH_INSTR + "\n5. 补充验收") is False


def test_parse_evolution_json_fenced():
    raw = """```json
{
  "language": "zh",
  "improved_instructions": "1. 确认目标\\n2. 执行步骤",
  "changelog": ["补验收"],
  "preserved_intent": "协作 SOP",
  "risks": []
}
```"""
    obj = _parse(raw)
    assert obj is not None
    assert obj["language"] == "zh"
    assert "确认目标" in obj["improved_instructions"]


def test_parse_evolution_json_prose_wrapper():
    raw = 'Here is the result:\n{"improved_instructions":"步骤一 验证\\n步骤二 回滚","changelog":["a"],"language":"zh"}\nThanks'
    obj = _parse(raw)
    assert obj is not None
    assert "步骤一" in obj["improved_instructions"]


class _FakeLib:
    def __init__(self, skill: SkillDefinition):
        self._skill = skill
        self.snapshots: List[Any] = []

    def _find_skill(self, team_id: str, skill_id: str):
        if skill_id == self._skill.skill_id or skill_id == self._skill.slug:
            return self._skill
        return None

    def create_version_snapshot(self, skill):
        self.snapshots.append(skill.version)

    def _persist_skill(self, skill, team_id):
        self._skill = skill


class _FakeHarness:
    def __init__(self, responses: List[str], errors: Optional[List[str]] = None):
        self.responses = list(responses)
        self.errors = list(errors or [])
        self.calls: List[Dict[str, Any]] = []

    async def chat(self, prompt="", **kwargs):
        # support both positional prompt and kwargs from evolver
        kw = dict(kwargs)
        if prompt and "prompt" not in kw:
            kw["prompt"] = prompt
        self.calls.append(kw)
        err = self.errors.pop(0) if self.errors else ""
        text = self.responses.pop(0) if self.responses else ""
        return SimpleNamespace(response=text, error=err)


def _zh_skill() -> SkillDefinition:
    return SkillDefinition(
        skill_id="sk_zh_1",
        name="协作SOP",
        description="如何构建Agents协作SOP",
        instructions=ZH_INSTR,
        slug="collab-sop",
        version=1,
        usage_count=2,
        effectiveness=0.4,
    )


@pytest.mark.asyncio
async def test_evolve_success_json_zh():
    skill = _zh_skill()
    lib = _FakeLib(skill)
    good = json_dumps_zh()
    harness = _FakeHarness([good])
    ev = SkillEvolver(skill_library=lib, chat_harness=harness)
    # inject fake live config
    live = SimpleNamespace(api_key="k", model="test-model", api_base_url="")
    out = await ev.evolve_skill("t1", "sk_zh_1", provider_config=live)
    assert out.get("llm_degraded") is False
    assert not out.get("error")
    assert out.get("improved_instructions")
    assert "中文" in (out.get("improved_instructions") or "") or "步骤" in (out.get("improved_instructions") or "")
    assert isinstance(out.get("changelog"), list)
    assert out.get("language") in ("zh", "mixed")


def json_dumps_zh() -> str:
    import json
    return json.dumps({
        "language": "zh",
        "improved_instructions": (
            "1. 列出业务目标与可量化验收口径\n"
            "2. 明确前置条件、依赖与不可变约束\n"
            "3. 输出必须做/可选做/禁止做三栏\n"
            "4. 补最小验证步骤、超时与回滚点\n"
            "5. 记录协作交接与责任人"
        ),
        "changelog": ["补验收口径", "补回滚与超时"],
        "preserved_intent": "建立可预测可追责的 Agent 协作 SOP",
        "risks": [],
    }, ensure_ascii=False)


@pytest.mark.asyncio
async def test_evolve_language_flip_no_second_llm_repair():
    """English draft → language_flip; no endless repair chain; partial body returned."""
    skill = _zh_skill()
    lib = _FakeLib(skill)
    import json
    en_json = json.dumps({
        "language": "en",
        "improved_instructions": EN_SOP,
        "changelog": ["expanded SOP"],
        "preserved_intent": "SOP",
        "risks": [],
    })
    # Only one response — if evolver tried 2nd language-repair LLM it would hang waiting
    harness = _FakeHarness([en_json])
    ev = SkillEvolver(skill_library=lib, chat_harness=harness)
    live = SimpleNamespace(api_key="k", model="test-model", api_base_url="")
    out = await ev.evolve_skill("t1", "sk_zh_1", provider_config=live)
    assert out.get("error") == "language_flip"
    assert out.get("language_flip") is True
    # partial draft still exposed for manual edit; apply will still reject flip
    assert out.get("improved_instructions")
    assert len(harness.calls) == 1  # no second LLM call


@pytest.mark.asyncio
async def test_evolve_uses_fresh_session_each_call():
    skill = _zh_skill()
    lib = _FakeLib(skill)
    harness = _FakeHarness([json_dumps_zh(), json_dumps_zh()])
    ev = SkillEvolver(skill_library=lib, chat_harness=harness)
    live = SimpleNamespace(api_key="k", model="test-model", api_base_url="")
    await ev.evolve_skill("t1", "sk_zh_1", provider_config=live)
    await ev.evolve_skill("t1", "sk_zh_1", provider_config=live)
    sids = [c.get("session_id") for c in harness.calls]
    assert all(sids)
    assert sids[0] != sids[1]
    assert all(str(s).startswith("evolve-") for s in sids)


def test_apply_rejects_language_flip():
    skill = _zh_skill()
    lib = _FakeLib(skill)
    ev = SkillEvolver(skill_library=lib)
    out = ev.apply_evolution("t1", "sk_zh_1", EN_SOP)
    assert out.get("error") == "language_flip"


def test_apply_accepts_zh():
    skill = _zh_skill()
    lib = _FakeLib(skill)
    ev = SkillEvolver(skill_library=lib)
    new_text = ZH_INSTR + "\n5. 补充责任人与超时阈值"
    out = ev.apply_evolution("t1", "sk_zh_1", new_text)
    assert out.get("status") == "evolved"
    assert out.get("version") == 2
    assert lib._skill.instructions == new_text


def test_strip_language_meta_from_instructions():
    leaked = (
        "【要求】\n"
        "- 语言：中文（术语可保留英文缩写如 SOP/Agent/SLA）\n"
        "\n"
        "1. 明确协作目标与验收口径\n"
        "2. 定义任务传递与阻塞升级\n"
    )
    cleaned = SkillEvolver._strip_generation_meta_from_instructions(leaked)
    assert "【要求】" not in cleaned
    assert "语言：中文" not in cleaned
    assert "明确协作目标" in cleaned
    assert "阻塞升级" in cleaned


def test_normalize_draft_strips_meta():
    skill = _zh_skill()
    draft = SkillEvolver(skill_library=_FakeLib(skill))._normalize_draft(skill, {
        "language": "zh",
        "improved_instructions": "【要求】\n语言：中文\n\n1. 做评审\n2. 写结论",
        "changelog": ["补步骤"],
        "preserved_intent": "评审",
        "risks": [],
    })
    assert "语言：中文" not in draft["improved_instructions"]
    assert "做评审" in draft["improved_instructions"]
