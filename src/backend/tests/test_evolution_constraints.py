# -*- coding: utf-8 -*-
"""Regression tests for evolution constraint checks."""

from __future__ import annotations

from agents.evolution.constraints import (
    check_format_preservation,
    check_language_consistency,
    check_length,
    check_no_meta_commentary,
    check_not_empty,
    validate_all,
)


def test_length_constraint_uses_ratio_and_empty_original_limit():
    assert check_length("abcd", "abcdef", max_ratio=1.5) is True
    assert check_length("abcd", "abcdefg", max_ratio=1.5) is False
    assert check_length("", "x" * 4999) is True
    assert check_length("", "x" * 5000) is False


def test_not_empty_uses_trimmed_minimum_length():
    assert check_not_empty("  abc  ", min_length=3) is True
    assert check_not_empty("  ab  ", min_length=3) is False


def test_language_consistency_preserves_chinese_or_english_bias():
    assert check_language_consistency("这是一个中文技能说明，需要保持中文。", "Keep this mostly English.") is False
    assert check_language_consistency("Use English instructions only.", "这是一个突然变成中文的版本。") is False
    assert check_language_consistency("这是一个中文技能说明。", "这是一个改写后的中文说明。") is True


def test_format_preservation_requires_numbered_steps_when_original_has_them():
    original = "1. 读取文件\n2. 修改文件"

    assert check_format_preservation(original, "1. Read file\n2. Update file") is True
    assert check_format_preservation(original, "Read file, then update file") is False


def test_no_meta_commentary_rejects_introductory_explanations():
    assert check_no_meta_commentary("以下是优化后的版本：\n执行任务") is False
    assert check_no_meta_commentary("执行任务并记录结果") is True


def test_validate_all_preserves_output_shape_and_violation_order():
    original = "1. 处理请求\n2. 返回结果"
    evolved = "以下是优化后的 " + ("English only response " * 8)

    result = validate_all(
        original,
        evolved,
        target_type="prompt",
    )

    assert result["passed"] is False
    assert result["violations"] == ["length", "language", "format", "no_meta"]
    assert result["checks"]["not_empty"] is True
    assert result["original_length"] == len(original)
    assert result["evolved_length"] == len(evolved)
    assert result["length_ratio"] == len(evolved) / len(original)
