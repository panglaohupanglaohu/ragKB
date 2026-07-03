# -*- coding: utf-8 -*-
"""约束验证器 — 确保演化变体在安全边界内.

照搬 Hermes constraints.py:
- 长度约束 (不超过原始 150%)
- 语言一致性
- 格式保持 (编号步骤等)
- 语义保持 (不漂移)
"""
from __future__ import annotations

import re
import logging
from typing import Dict, Any

logger = logging.getLogger("evolution.constraints")

DEFAULT_EMPTY_ORIGINAL_MAX_LENGTH = 5000
DEFAULT_MIN_EVOLVED_LENGTH = 20
TARGET_MAX_LENGTH_RATIOS = {
    "skill": 1.5,
    "rule": 1.3,
    "prompt": 1.2,
}
NUMBERED_STEP_RE = re.compile(r'^\s*\d+[\.\)、]', re.MULTILINE)
META_COMMENTARY_PATTERNS = [
    re.compile(r'^(以下是|这是|下面是).*(改进|优化|更新|修改)', re.MULTILINE),
    re.compile(r'^(改进|优化)后的', re.MULTILINE),
    re.compile(r'^(注意|说明)[:：]', re.MULTILINE),
    re.compile(r'(如上所述|以上就是)', re.MULTILINE),
]


def check_length(original: str, evolved: str, max_ratio: float = 1.5) -> bool:
    """演化后文本不超过原始的 max_ratio 倍."""
    if not original:
        return len(evolved) < DEFAULT_EMPTY_ORIGINAL_MAX_LENGTH
    return len(evolved) <= len(original) * max_ratio


def check_not_empty(evolved: str, min_length: int = DEFAULT_MIN_EVOLVED_LENGTH) -> bool:
    """演化后文本不能为空或过短."""
    return len(evolved.strip()) >= min_length


def _chinese_ratio(text: str) -> float:
    if not text:
        return 0
    cn = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    return cn / len(text)


def check_language_consistency(original: str, evolved: str) -> bool:
    """如果原始是中文为主，演化后也应该是中文为主."""
    orig_cn = _chinese_ratio(original)
    evol_cn = _chinese_ratio(evolved)
    # If original is >20% Chinese, evolved should be at least 10% Chinese
    if orig_cn > 0.2 and evol_cn < 0.1:
        return False
    # If original is <5% Chinese (English), evolved shouldn't suddenly be >30% Chinese
    if orig_cn < 0.05 and evol_cn > 0.3:
        return False
    return True


def check_format_preservation(original: str, evolved: str) -> bool:
    """如果原始有编号步骤，演化后也应该有."""
    orig_has_numbered = bool(NUMBERED_STEP_RE.search(original))
    evol_has_numbered = bool(NUMBERED_STEP_RE.search(evolved))
    if orig_has_numbered and not evol_has_numbered:
        return False
    return True


def check_no_meta_commentary(evolved: str) -> bool:
    """演化后文本不应包含元评论（如"以下是改进版"之类）."""
    sample = evolved[:200]
    for pattern in META_COMMENTARY_PATTERNS:
        if pattern.search(sample):
            return False
    return True


def _max_ratio_for_target(target_type: str) -> float:
    return TARGET_MAX_LENGTH_RATIOS.get(target_type, TARGET_MAX_LENGTH_RATIOS["skill"])


def validate_all(original: str, evolved: str, target_type: str = "skill") -> Dict[str, Any]:
    """运行所有约束检查，返回结果.

    Returns:
        {"passed": bool, "violations": [...], "checks": {...}}
    """
    max_ratio = _max_ratio_for_target(target_type)

    checks = {
        "length": check_length(original, evolved, max_ratio),
        "not_empty": check_not_empty(evolved),
        "language": check_language_consistency(original, evolved),
        "format": check_format_preservation(original, evolved),
        "no_meta": check_no_meta_commentary(evolved),
    }

    violations = [name for name, passed in checks.items() if not passed]

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "checks": checks,
        "original_length": len(original),
        "evolved_length": len(evolved),
        "length_ratio": len(evolved) / max(len(original), 1),
    }
