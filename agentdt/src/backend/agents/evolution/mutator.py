# -*- coding: utf-8 -*-
"""反思式变异器 — Qwen3 驱动 (类GEPA).

照搬 Hermes GEPA 的核心理念:
- 不是随机变异，而是先分析 WHY 失败，再定向改进
- 每轮生成 2-3 个候选变体
- 支持多种变异策略: refine, restructure, elaborate, simplify
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("evolution.mutator")


# ── 反思式分析 Prompt (类GEPA reflective analysis) ────────────────

REFLECT_SYSTEM_PROMPT = """你是一个技能优化分析专家。你需要分析一个Agent技能在测试中失败的原因。

分析要求:
1. 找出技能指令中导致失败的具体缺陷
2. 指出缺陷的根本原因（模糊？遗漏？逻辑错误？）
3. 提出具体的改进方向

严格按JSON格式输出:
{"root_causes": ["原因1", "原因2"], "specific_defects": ["缺陷1", "缺陷2"], "improvement_directions": ["方向1", "方向2"]}"""

REFLECT_USER_TEMPLATE = """## 当前技能指令
{instructions}

## 失败案例 (共{failure_count}个)
{failures_text}

请分析失败的根本原因和改进方向:"""


# ── 变异 Prompt ────────────────────────────────────────────────

MUTATE_SYSTEM_PROMPT = """你是一个技能指令优化专家。根据失败分析和指定策略，生成改进后的技能指令。

要求:
1. 保持技能的核心意图和功能不变
2. 只修改需要改进的部分
3. 不添加无关内容或元评论
4. 直接输出改进后的完整指令文本，不要包裹在代码块中
5. 不要输出"以下是改进版"之类的前言"""

MUTATE_USER_TEMPLATE_REFINE = """## 失败分析
根本原因: {root_causes}
具体缺陷: {defects}

## 当前指令
{instructions}

## 策略: 局部精修 (refine)
请针对上述缺陷，只修改必要的部分。保持其他部分不变。输出完整的改进后指令:"""

MUTATE_USER_TEMPLATE_RESTRUCTURE = """## 失败分析
根本原因: {root_causes}
具体缺陷: {defects}

## 当前指令
{instructions}

## 策略: 重新组织 (restructure)
请重新组织指令的结构和流程顺序，使其更清晰合理。保持核心内容不变。输出完整的改进后指令:"""

MUTATE_USER_TEMPLATE_ELABORATE = """## 失败分析
根本原因: {root_causes}
具体缺陷: {defects}

## 当前指令
{instructions}

## 策略: 补充细化 (elaborate)
请补充缺失的边界条件、异常处理、示例等内容。不要删除现有内容。输出完整的改进后指令:"""

MUTATE_USER_TEMPLATE_SIMPLIFY = """## 失败分析
根本原因: {root_causes}
具体缺陷: {defects}

## 当前指令
{instructions}

## 策略: 精简 (simplify)
请删除冗余和不必要的内容，使指令更简洁直接。保留所有关键步骤。输出完整的改进后指令:"""

STRATEGY_TEMPLATES = {
    "refine": MUTATE_USER_TEMPLATE_REFINE,
    "restructure": MUTATE_USER_TEMPLATE_RESTRUCTURE,
    "elaborate": MUTATE_USER_TEMPLATE_ELABORATE,
    "simplify": MUTATE_USER_TEMPLATE_SIMPLIFY,
}


class ReflectionResult:
    """反思分析结果."""

    def __init__(self):
        self.root_causes: List[str] = []
        self.specific_defects: List[str] = []
        self.improvement_directions: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_causes": self.root_causes,
            "specific_defects": self.specific_defects,
            "improvement_directions": self.improvement_directions,
        }


class MutationCandidate:
    """一个变异候选."""

    def __init__(self, strategy: str, instructions: str):
        self.strategy = strategy
        self.instructions = instructions
        self.score: Optional[float] = None
        self.constraint_passed: bool = True
        self.constraint_violations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "instructions": self.instructions[:500] + ("..." if len(self.instructions) > 500 else ""),
            "score": self.score,
            "constraint_passed": self.constraint_passed,
            "violations": self.constraint_violations,
        }


async def reflect_on_failures(
    instructions: str,
    failures: List[Dict[str, Any]],
    chat_harness=None,
) -> ReflectionResult:
    """反思式分析 — 为什么当前指令在这些测试上失败了？

    照搬 Hermes GEPA: reads execution traces to understand WHY things fail.
    """
    if chat_harness is None:
        from ..chat_harness import get_chat_harness
        chat_harness = get_chat_harness()

    rr = ReflectionResult()

    # Format failures for prompt
    failures_text = ""
    for i, f in enumerate(failures[:5]):  # Cap at 5 failures
        failures_text += f"\n### 失败案例 {i + 1}\n"
        failures_text += f"任务: {f.get('task_input', '')[:200]}\n"
        failures_text += f"Agent输出: {f.get('agent_output', '')[:300]}\n"
        failures_text += f"评分标准: {f.get('rubric', '')[:200]}\n"
        failures_text += f"得分: {f.get('composite', 0):.2f}\n"
        failures_text += f"评分理由: {f.get('reasoning', '')}\n"

    prompt = REFLECT_USER_TEMPLATE.format(
        instructions=instructions[:2000],
        failure_count=len(failures),
        failures_text=failures_text,
    )

    try:
        result = await chat_harness.chat(
            prompt=prompt,
            system_prompt=REFLECT_SYSTEM_PROMPT,
            agent_id="evolution_reflector",
        )
        if result and getattr(result, "response", None):
            resp = result.response.strip()
            if resp.startswith("```"):
                resp = resp.split("\n", 1)[1]
                if resp.endswith("```"):
                    resp = resp[:-3]
                resp = resp.strip()

            data = json.loads(resp)
            rr.root_causes = data.get("root_causes", [])[:5]
            rr.specific_defects = data.get("specific_defects", [])[:5]
            rr.improvement_directions = data.get("improvement_directions", [])[:5]
        else:
            logger.warning("Reflection returned empty response")
            rr.root_causes = ["反思模型返回空"]
            rr.improvement_directions = ["尝试通用改进"]
    except json.JSONDecodeError as e:
        logger.warning("Reflection JSON parse failed: %s | raw: %s", e, resp[:200] if 'resp' in dir() else '?')
        rr.root_causes = ["分析JSON解析失败"]
        rr.improvement_directions = ["尝试通用改进"]
    except Exception as e:
        logger.error("Reflection call failed (type=%s): %s", type(e).__name__, e)
        rr.root_causes = [f"反思调用失败: {type(e).__name__}"]
        rr.improvement_directions = ["尝试通用改进"]

    return rr


async def generate_candidates(
    instructions: str,
    reflection: ReflectionResult,
    strategies: Optional[List[str]] = None,
    chat_harness=None,
) -> List[MutationCandidate]:
    """基于反思结果生成 2-3 个候选变体.

    照搬 Hermes: GEPA proposes mutations based on failure analysis.
    """
    if chat_harness is None:
        from ..chat_harness import get_chat_harness
        chat_harness = get_chat_harness()

    if strategies is None:
        # Default: pick 2-3 strategies based on reflection
        strategies = _select_strategies(reflection)

    candidates = []
    root_causes = "; ".join(reflection.root_causes) or "未知"
    defects = "; ".join(reflection.specific_defects) or "未知"

    for strategy in strategies:
        template = STRATEGY_TEMPLATES.get(strategy, MUTATE_USER_TEMPLATE_REFINE)
        prompt = template.format(
            root_causes=root_causes,
            defects=defects,
            instructions=instructions,
        )

        try:
            result = await chat_harness.chat(
                prompt=prompt,
                system_prompt=MUTATE_SYSTEM_PROMPT,
                agent_id="evolution_mutator",
            )
            if result and getattr(result, "response", None):
                evolved = result.response.strip()
                # Clean up: remove code blocks if LLM wrapped it
                if evolved.startswith("```"):
                    evolved = evolved.split("\n", 1)[1]
                    if evolved.endswith("```"):
                        evolved = evolved[:-3]
                    evolved = evolved.strip()

                # Validate: must be non-trivial and actually different from input
                if len(evolved) < 20:
                    logger.warning("Mutation too short for strategy %s: %d chars", strategy, len(evolved))
                elif evolved == instructions.strip():
                    logger.warning("Mutation identical to original for strategy %s", strategy)
                else:
                    candidates.append(MutationCandidate(strategy=strategy, instructions=evolved))
            else:
                logger.warning("Mutation returned empty for strategy %s", strategy)
        except Exception as e:
            logger.warning("Mutation failed for strategy %s (type=%s): %s", strategy, type(e).__name__, e)

    logger.info("Generated %d candidates (strategies: %s)", len(candidates), strategies)
    return candidates


def _select_strategies(reflection: ReflectionResult) -> List[str]:
    """根据反思结果智能选择变异策略."""
    strategies = ["refine"]  # Always try refine

    causes_text = " ".join(reflection.root_causes + reflection.specific_defects).lower()

    if any(kw in causes_text for kw in ["遗漏", "缺失", "没有处理", "边界", "异常"]):
        strategies.append("elaborate")
    elif any(kw in causes_text for kw in ["冗余", "重复", "过长", "啰嗦"]):
        strategies.append("simplify")
    elif any(kw in causes_text for kw in ["顺序", "结构", "混乱", "不清晰"]):
        strategies.append("restructure")
    else:
        strategies.append("elaborate")  # Default fallback

    # Cap at 3
    return strategies[:3]
