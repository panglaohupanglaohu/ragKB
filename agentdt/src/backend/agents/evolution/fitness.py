# -*- coding: utf-8 -*-
"""Fitness 评分函数 — LLM-as-Judge.

照搬 Hermes fitness.py:
- 指令遵循度 (0-1)
- 输出质量/正确性 (0-1)
- 简洁度 (0-1)
- 复合加权分

评分用 Qwen3 做 Judge，每个案例独立评分。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("evolution.fitness")


JUDGE_SYSTEM_PROMPT = """你是一个严格的质量评估专家。你需要评估一个Agent按照给定技能指令执行任务的质量。

评分维度 (每项 0.0-1.0):
1. instruction_following: 是否忠实遵循了技能指令的流程和要求？
2. output_quality: 输出是否正确、完整、对用户有帮助？
3. conciseness: 是否简洁高效，没有冗余废话？

严格按JSON格式输出评分，不要添加其他内容:
{"instruction_following": 0.0-1.0, "output_quality": 0.0-1.0, "conciseness": 0.0-1.0, "reasoning": "一句话解释"}"""

JUDGE_USER_TEMPLATE = """## 技能指令
{instructions}

## 用户任务
{task_input}

## Agent 执行结果
{agent_output}

## 评分标准 (rubric)
{rubric}

请严格按JSON格式评分:"""

SIMULATE_SYSTEM_PROMPT = """你是一个Agent，严格按照以下技能指令执行任务。只输出执行结果，不要解释你在做什么。

技能指令:
{instructions}"""


class FitnessResult:
    """单个评估案例的 fitness 结果."""

    def __init__(self):
        self.instruction_following: float = 0.0
        self.output_quality: float = 0.0
        self.conciseness: float = 0.0
        self.reasoning: str = ""
        self.composite: float = 0.0
        self.raw_output: str = ""

    def calculate_composite(
        self,
        w_follow: float = 0.4,
        w_quality: float = 0.4,
        w_concise: float = 0.2,
    ):
        """计算加权复合分."""
        self.composite = (
            self.instruction_following * w_follow
            + self.output_quality * w_quality
            + self.conciseness * w_concise
        )
        return self.composite

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instruction_following": self.instruction_following,
            "output_quality": self.output_quality,
            "conciseness": self.conciseness,
            "composite": self.composite,
            "reasoning": self.reasoning,
        }


class SkillFitnessReport:
    """一个技能在完整数据集上的 fitness 报告."""

    def __init__(self, skill_id: str, skill_name: str):
        self.skill_id = skill_id
        self.skill_name = skill_name
        self.results: List[Dict[str, Any]] = []  # per-example results
        self.mean_composite: float = 0.0
        self.mean_following: float = 0.0
        self.mean_quality: float = 0.0
        self.mean_conciseness: float = 0.0
        self.failures: List[Dict[str, Any]] = []  # examples with score < 0.5

    def calculate_means(self):
        if not self.results:
            return
        n = len(self.results)
        self.mean_composite = sum(r["composite"] for r in self.results) / n
        self.mean_following = sum(r["instruction_following"] for r in self.results) / n
        self.mean_quality = sum(r["output_quality"] for r in self.results) / n
        self.mean_conciseness = sum(r["conciseness"] for r in self.results) / n
        self.failures = [r for r in self.results if r["composite"] < 0.5]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "mean_composite": round(self.mean_composite, 3),
            "mean_instruction_following": round(self.mean_following, 3),
            "mean_output_quality": round(self.mean_quality, 3),
            "mean_conciseness": round(self.mean_conciseness, 3),
            "total_examples": len(self.results),
            "failure_count": len(self.failures),
            "results": self.results,
            "failures": self.failures,
        }


async def simulate_execution(
    instructions: str,
    task_input: str,
    chat_harness=None,
) -> str:
    """模拟 Agent 按技能指令执行任务.

    返回 Agent 的输出文本。
    """
    if chat_harness is None:
        from ..chat_harness import get_chat_harness
        chat_harness = get_chat_harness()

    system = SIMULATE_SYSTEM_PROMPT.format(instructions=instructions[:3000])
    try:
        result = await chat_harness.chat(
            prompt=task_input,
            system_prompt=system,
            agent_id="evolution_simulator",
        )
        if result and getattr(result, "response", None):
            return result.response
        logger.warning("Simulation returned empty response for task: %s", task_input[:80])
    except Exception as e:
        logger.error("Simulation failed (type=%s): %s", type(e).__name__, e)

    return "[模拟执行失败]"


async def judge_execution(
    instructions: str,
    task_input: str,
    agent_output: str,
    rubric: str,
    chat_harness=None,
) -> FitnessResult:
    """用 LLM-as-Judge 评分一次执行.

    照搬 Hermes: LLM judge scores on a rubric.
    """
    if chat_harness is None:
        from ..chat_harness import get_chat_harness
        chat_harness = get_chat_harness()

    fr = FitnessResult()
    fr.raw_output = agent_output

    prompt = JUDGE_USER_TEMPLATE.format(
        instructions=instructions[:2000],
        task_input=task_input[:500],
        agent_output=agent_output[:2000],
        rubric=rubric[:500],
    )

    try:
        result = await chat_harness.chat(
            prompt=prompt,
            system_prompt=JUDGE_SYSTEM_PROMPT,
            agent_id="evolution_judge",
        )
        if result and getattr(result, "response", None):
            resp = result.response.strip()
            # Parse JSON from response
            if resp.startswith("```"):
                resp = resp.split("\n", 1)[1]
                if resp.endswith("```"):
                    resp = resp[:-3]
                resp = resp.strip()

            scores = json.loads(resp)
            fr.instruction_following = max(0, min(1, float(scores.get("instruction_following", 0.5))))
            fr.output_quality = max(0, min(1, float(scores.get("output_quality", 0.5))))
            fr.conciseness = max(0, min(1, float(scores.get("conciseness", 0.5))))
            fr.reasoning = str(scores.get("reasoning", ""))
        else:
            logger.warning("Judge returned empty response")
            fr.instruction_following = 0.5
            fr.output_quality = 0.5
            fr.conciseness = 0.5
            fr.reasoning = "评分调用返回空"
    except json.JSONDecodeError as e:
        logger.warning("Judge JSON parse failed: %s | raw: %s", e, resp[:200] if 'resp' in dir() else '?')
        fr.instruction_following = 0.5
        fr.output_quality = 0.5
        fr.conciseness = 0.5
        fr.reasoning = f"评分JSON解析失败: {e}"
    except (ValueError, TypeError) as e:
        logger.warning("Judge score conversion failed: %s", e)
        fr.instruction_following = 0.5
        fr.output_quality = 0.5
        fr.conciseness = 0.5
        fr.reasoning = f"评分数值转换失败: {e}"
    except Exception as e:
        logger.error("Judge call failed (type=%s): %s", type(e).__name__, e)
        fr.instruction_following = 0.5
        fr.output_quality = 0.5
        fr.conciseness = 0.5
        fr.reasoning = f"评分调用失败: {type(e).__name__}: {e}"

    fr.calculate_composite()
    return fr


async def evaluate_skill(
    skill_id: str,
    skill_name: str,
    instructions: str,
    eval_examples: List[Dict[str, str]],
    chat_harness=None,
) -> SkillFitnessReport:
    """在一组测试用例上评估技能的 fitness.

    流程 (照搬 Hermes):
    1. For each example: simulate execution with the skill instructions
    2. Judge the execution result against the rubric
    3. Aggregate scores into a report
    """
    report = SkillFitnessReport(skill_id=skill_id, skill_name=skill_name)

    for i, example in enumerate(eval_examples):
        task_input = example.get("task_input", "")
        rubric = example.get("rubric", "")

        if not task_input:
            continue

        # Step 1: Simulate execution
        agent_output = await simulate_execution(instructions, task_input, chat_harness)

        # Step 2: Judge (skip if simulation failed — don't score placeholder text)
        if agent_output == "[模拟执行失败]":
            fr = FitnessResult()
            fr.raw_output = agent_output
            fr.instruction_following = 0.0
            fr.output_quality = 0.0
            fr.conciseness = 0.5
            fr.reasoning = "模拟执行失败，无法评分"
            fr.calculate_composite()
            report.failures.append({
                "task_input": task_input[:200],
                "rubric": rubric[:200],
                "composite": fr.composite,
                "reasoning": "模拟执行失败",
            })
        else:
            fr = await judge_execution(instructions, task_input, agent_output, rubric, chat_harness)

        report.results.append({
            "example_idx": i,
            "task_input": task_input[:200],
            "rubric": rubric[:200],
            "agent_output": agent_output[:500],
            **fr.to_dict(),
        })

        logger.debug("Example %d/%d: composite=%.2f", i + 1, len(eval_examples), fr.composite)

    report.calculate_means()
    return report


# ── Length penalty (照搬 Hermes) ────────────────────────────────

def apply_length_penalty(score: float, original_len: int, evolved_len: int, max_ratio: float = 1.5) -> float:
    """对接近长度限制的变体施加惩罚."""
    if original_len == 0:
        return score
    ratio = evolved_len / original_len
    if ratio <= 1.0:
        return score  # Shorter is fine
    if ratio > max_ratio:
        return 0.0  # Over limit
    # Linear penalty from ratio 1.0 to max_ratio
    penalty = (ratio - 1.0) / (max_ratio - 1.0) * 0.2  # Max 20% penalty
    return max(0, score - penalty)
