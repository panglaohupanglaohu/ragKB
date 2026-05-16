# -*- coding: utf-8 -*-
"""评估数据集生成器 — 多来源构建 train/val/holdout.

照搬 Hermes dataset_builder.py:
- 来源A: Qwen合成 (主要, 冷启动)
- 来源B: knowledge_base 挖掘 (真实使用)
- 来源C: 人工标注 (golden set)
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("evolution.dataset_builder")

# Storage path for generated datasets
DATASETS_DIR = Path(__file__).resolve().parents[3] / "storage" / "evolution_datasets"


DATASET_GEN_SYSTEM_PROMPT = """你是一个评估数据集生成专家。你的任务是为一个Agent技能生成测试用例。

每个测试用例包含:
1. task_input: 一个具体的用户任务/请求，该技能应该能处理
2. rubric: 评分标准（不是精确答案），描述好的执行应该包含什么

生成的测试用例应该:
- 覆盖技能的主要功能
- 包含简单和复杂场景
- 包含边界情况
- 彼此不重复

严格按JSON数组格式输出，不要添加其他内容。"""

DATASET_GEN_USER_TEMPLATE = """请为以下技能生成 {count} 个测试用例:

技能名称: {name}
技能标签: {tags}
技能指令:
---
{instructions}
---

输出格式 (严格JSON数组):
[
  {{"task_input": "...", "rubric": "好的执行应该: 1) ... 2) ... 3) ..."}},
  ...
]"""


class EvalDataset:
    """评估数据集容器."""

    def __init__(self, skill_id: str, skill_name: str):
        self.id = str(uuid4())[:12]
        self.skill_id = skill_id
        self.skill_name = skill_name
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.examples: List[Dict[str, str]] = []  # [{task_input, rubric}]
        self.train: List[Dict[str, str]] = []
        self.val: List[Dict[str, str]] = []
        self.holdout: List[Dict[str, str]] = []

    def split(self, train_ratio: float = 0.6, val_ratio: float = 0.2):
        """划分 train/val/holdout."""
        n = len(self.examples)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        self.train = self.examples[:train_end]
        self.val = self.examples[train_end:val_end]
        self.holdout = self.examples[val_end:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "created_at": self.created_at,
            "total_examples": len(self.examples),
            "split": {
                "train": len(self.train),
                "val": len(self.val),
                "holdout": len(self.holdout),
            },
            "examples": self.examples,
            "train": self.train,
            "val": self.val,
            "holdout": self.holdout,
        }

    def save(self, target_type: str = "skills"):
        """持久化到 storage/evolution_datasets/."""
        dir_path = DATASETS_DIR / target_type
        dir_path.mkdir(parents=True, exist_ok=True)
        filepath = dir_path / f"{self.skill_id}_{self.id}.json"
        filepath.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2))
        logger.info("Dataset saved: %s (%d examples)", filepath.name, len(self.examples))
        return str(filepath)

    @classmethod
    def load(cls, filepath: str) -> "EvalDataset":
        data = json.loads(Path(filepath).read_text())
        ds = cls(data["skill_id"], data["skill_name"])
        ds.id = data["id"]
        ds.created_at = data["created_at"]
        ds.examples = data["examples"]
        ds.train = data.get("train", [])
        ds.val = data.get("val", [])
        ds.holdout = data.get("holdout", [])
        return ds


async def generate_synthetic_dataset(
    skill_name: str,
    skill_id: str,
    instructions: str,
    tags: List[str],
    count: int = 15,
    chat_harness=None,
) -> EvalDataset:
    """来源A: 用 Qwen 合成评估数据集.

    照搬 Hermes Source A — LLM reads skill → generates test cases.
    """
    if chat_harness is None:
        from ..chat_harness import get_chat_harness
        chat_harness = get_chat_harness()

    dataset = EvalDataset(skill_id=skill_id, skill_name=skill_name)

    prompt = DATASET_GEN_USER_TEMPLATE.format(
        count=count,
        name=skill_name,
        tags=", ".join(tags) if tags else "无",
        instructions=instructions[:3000],  # Truncate very long instructions
    )

    try:
        result = await chat_harness.chat(
            prompt=prompt,
            system_prompt=DATASET_GEN_SYSTEM_PROMPT,
            agent_id="evolution_dataset_builder",
        )
        if result and getattr(result, "response", None):
            # Parse JSON array from response
            response_text = result.response.strip()
            # Handle markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

            examples = json.loads(response_text)
            if isinstance(examples, list):
                for ex in examples:
                    if isinstance(ex, dict) and "task_input" in ex and "rubric" in ex:
                        dataset.examples.append({
                            "task_input": str(ex["task_input"]),
                            "rubric": str(ex["rubric"]),
                        })
    except json.JSONDecodeError as e:
        raw_preview = response_text[:200] if 'response_text' in dir() else '(empty)'
        logger.warning("Failed to parse dataset JSON: %s | raw: %s", e, raw_preview)
    except Exception as e:
        logger.error("Dataset generation failed (type=%s): %s", type(e).__name__, e)

    # Ensure minimum examples
    if len(dataset.examples) < 3:
        logger.warning("Only generated %d examples for %s (need >=3 for meaningful eval)", len(dataset.examples), skill_name)

    dataset.split()
    return dataset


def mine_knowledge_base(skill_id: str, skill_name: str, max_examples: int = 20) -> List[Dict[str, str]]:
    """来源B: 从 knowledge_base/ 挖掘真实使用案例.

    照搬 Hermes Source B — SessionDB mining.
    """
    kb_dir = Path(__file__).resolve().parents[3] / "storage" / "knowledge_base"
    if not kb_dir.exists():
        logger.info("Knowledge base dir not found for mining: %s", kb_dir)
        return []

    mined = []
    for fp in sorted(kb_dir.glob("*.json"))[:200]:  # Cap scanning
        try:
            data = json.loads(fp.read_text())
            # Look for skill references in the knowledge base entry
            content = json.dumps(data, ensure_ascii=False)
            if skill_name.lower() in content.lower() or skill_id in content:
                # Extract task-like content
                title = data.get("title", "")
                description = data.get("description", data.get("content", ""))
                if title and description:
                    mined.append({
                        "task_input": title[:500],
                        "rubric": f"基于知识库记录，应该处理: {description[:300]}",
                        "source": "knowledge_base",
                        "source_file": fp.name,
                    })
        except (json.JSONDecodeError, OSError):
            continue

        if len(mined) >= max_examples:
            break

    return mined


def load_golden_set(skill_id: str) -> List[Dict[str, str]]:
    """来源C: 加载人工标注的 golden set.

    照搬 Hermes Source C — Hand-curated golden sets.
    """
    golden_path = DATASETS_DIR / "skills" / f"{skill_id}_golden.json"
    if not golden_path.exists():
        return []
    try:
        data = json.loads(golden_path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


async def build_full_dataset(
    skill_name: str,
    skill_id: str,
    instructions: str,
    tags: List[str],
    synthetic_count: int = 15,
    chat_harness=None,
) -> EvalDataset:
    """组合所有来源构建完整评估数据集.

    Priority: golden > knowledge_base > synthetic
    """
    # Generate synthetic (always, as baseline)
    dataset = await generate_synthetic_dataset(
        skill_name=skill_name,
        skill_id=skill_id,
        instructions=instructions,
        tags=tags,
        count=synthetic_count,
        chat_harness=chat_harness,
    )

    # Merge knowledge_base mined examples
    kb_examples = mine_knowledge_base(skill_id, skill_name)
    for ex in kb_examples[:5]:  # Cap at 5 from KB
        dataset.examples.append({"task_input": ex["task_input"], "rubric": ex["rubric"]})

    # Merge golden set (highest priority)
    golden = load_golden_set(skill_id)
    for ex in golden[:10]:
        dataset.examples.insert(0, ex)  # Golden goes to front (train set)

    # Re-split after merging
    dataset.split()
    return dataset
