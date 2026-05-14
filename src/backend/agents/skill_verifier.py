# -*- coding: utf-8 -*-
"""技能验证框架 — 自动生成测试场景 → 沙箱执行 → 评估 pass_rate.

对应 SkillClaw: Verification In the Wild.
状态 badge: 🔵未验证 / 🟡测试中 / ✅已验证 / ❌验证失败
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import SkillDefinition, SkillLifecycleStage
from .domain_events import DomainEvent, EventType, SkillSnapshot
from .event_bus import get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """单次验证结果."""
    skill_id: str = ""
    pass_rate: float = 0.0
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    test_details: List[Dict[str, Any]] = field(default_factory=list)
    verified_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "pending"  # pending / testing / verified / failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "pass_rate": self.pass_rate,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "test_details": self.test_details,
            "verified_at": self.verified_at,
            "status": self.status,
        }


class SkillVerifier:
    """技能验证器 — 构造测试 → 执行 → 评估."""

    def __init__(self, skill_library=None, chat_harness=None):
        self._skill_library = skill_library
        self._chat_harness = chat_harness
        self._results: Dict[str, VerificationResult] = {}

    async def verify_skill(self, team_id: str, skill_id: str) -> VerificationResult:
        """验证技能: 生成测试场景 → LLM执行 → 评估 pass_rate."""
        result = VerificationResult(skill_id=skill_id, status="testing")

        if not self._skill_library:
            result.status = "failed"
            return result

        skill = self._skill_library._find_skill(team_id, skill_id)
        if not skill:
            result.status = "failed"
            return result

        # Generate test scenarios via LLM
        test_scenarios = await self._generate_tests(skill)
        result.total_tests = len(test_scenarios)

        # Execute each test
        for test in test_scenarios:
            passed = await self._execute_test(skill, test)
            if passed:
                result.passed += 1
            else:
                result.failed += 1
            result.test_details.append({
                "scenario": test.get("scenario", ""),
                "passed": passed,
            })

        # Calculate pass_rate
        if result.total_tests > 0:
            result.pass_rate = result.passed / result.total_tests

        # Determine status
        if result.pass_rate >= 0.7:
            result.status = "verified"
            # Update skill lifecycle
            skill.lifecycle_stage = SkillLifecycleStage.VERIFIED
            skill.quality_score = result.pass_rate
            self._skill_library._persist_skill(skill, team_id)
        else:
            result.status = "failed"

        # Store result
        self._results[skill_id] = result

        # Emit event
        bus = get_event_bus()
        event = DomainEvent.create(
            event_type=EventType.SKILL_UPDATED,
            payload=SkillSnapshot.from_skill_definition(skill),
            source="skill_verifier",
            correlation_id=f"verify:{skill_id}",
        )
        bus.publish(event)

        logger.info("Skill %s verification: %s (pass_rate=%.2f)",
                     skill_id, result.status, result.pass_rate)
        return result

    async def _generate_tests(self, skill: SkillDefinition) -> List[Dict[str, str]]:
        """通过 LLM 生成测试场景."""
        if not self._chat_harness:
            # Fallback: simple structural test
            return [
                {"scenario": "structural_check", "prompt": f"验证技能 {skill.name} 的指令是否完整且可操作"},
            ]

        try:
            result = await self._chat_harness.chat(
                prompt=f"为以下技能生成3个测试场景:\n\n名称: {skill.name}\n描述: {skill.description}\n指令: {skill.instructions[:2000]}",
                system_prompt=VERIFY_PROMPT,
                agent_id="skill_verifier",
            )
            # chat() returns TurnResult object with .response attribute
            response_text = getattr(result, 'response', '') if result else ''
            if response_text:
                import json
                try:
                    tests = json.loads(response_text)
                    if isinstance(tests, list):
                        return tests[:5]
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            logger.error("Test generation failed: %s", e)

        return [{"scenario": "basic_validation", "prompt": f"使用技能「{skill.name}」完成一个基本任务"}]

    async def _execute_test(self, skill: SkillDefinition, test: Dict[str, str]) -> bool:
        """执行单个测试场景 — 通过 LLM 评估."""
        if not self._chat_harness:
            # Structural validation: check skill has instructions
            return bool(skill.instructions and len(skill.instructions) > 20)

        try:
            result = await self._chat_harness.chat(
                prompt=f"使用以下技能指令处理测试场景:\n\n技能指令: {skill.instructions[:2000]}\n\n测试场景: {test.get('prompt', test.get('scenario', ''))}",
                system_prompt="你是一个技能测试执行器。执行给定的技能指令，输出 PASS 或 FAIL。",
                agent_id="skill_verifier",
            )
            # chat() returns TurnResult object with .response attribute
            response_text = getattr(result, 'response', '') if result else ''
            if response_text:
                return "PASS" in response_text.strip().upper()
        except Exception as e:
            logger.error("Test execution failed: %s", e)

        return False

    def get_result(self, skill_id: str) -> Optional[VerificationResult]:
        """获取验证结果."""
        return self._results.get(skill_id)

    def get_all_results(self) -> Dict[str, Dict[str, Any]]:
        """获取所有验证结果."""
        return {k: v.to_dict() for k, v in self._results.items()}


VERIFY_PROMPT = """为给定技能生成3个测试场景，以JSON数组格式输出:
[
  {"scenario": "场景描述", "prompt": "测试任务描述", "expected": "期望输出特征"}
]

测试场景应覆盖:
1. 正常情况 (happy path)
2. 边界情况 (edge case)
3. 异常处理 (error handling)

只输出JSON数组，不要其他文字。"""


# ── Singleton ────────────────────────────────────────────────────

_verifier: Optional[SkillVerifier] = None


def get_skill_verifier() -> SkillVerifier:
    global _verifier
    if _verifier is None:
        _verifier = SkillVerifier()
    return _verifier


def init_skill_verifier(skill_library=None, chat_harness=None) -> SkillVerifier:
    global _verifier
    _verifier = SkillVerifier(skill_library=skill_library, chat_harness=chat_harness)
    logger.info("SkillVerifier initialized")
    return _verifier
