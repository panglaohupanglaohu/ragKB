# -*- coding: utf-8 -*-
"""对比器 — baseline vs evolved 并排对比.

照搬 Hermes comparator/pr_builder:
- 展示 diff
- 分数对比 (baseline/evolved/holdout)
- 统计显著性判断
"""
from __future__ import annotations

import difflib
from typing import Any, Dict, List

SIGNIFICANT_SCORE_DELTA = 0.05
DIFF_LINE_LIMIT = 100


def compute_diff(original: str, evolved: str) -> List[str]:
    """生成 unified diff."""
    orig_lines = original.splitlines(keepends=True)
    evol_lines = evolved.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        orig_lines, evol_lines,
        fromfile="baseline", tofile="evolved",
        lineterm=""
    ))
    return diff


def compute_diff_html(original: str, evolved: str) -> str:
    """生成 HTML 格式的 diff，用于前端展示."""
    orig_lines = original.splitlines()
    evol_lines = evolved.splitlines()

    html_lines = []
    for line in difflib.ndiff(orig_lines, evol_lines):
        if line.startswith("+ "):
            html_lines.append(f'<div class="diff-add">+ {_esc(line[2:])}</div>')
        elif line.startswith("- "):
            html_lines.append(f'<div class="diff-del">- {_esc(line[2:])}</div>')
        elif line.startswith("? "):
            continue  # Skip hint lines
        else:
            html_lines.append(f'<div class="diff-ctx">  {_esc(line[2:])}</div>')

    return "\n".join(html_lines)


def compare_results(
    original_instructions: str,
    evolved_instructions: str,
    baseline_score: float,
    evolved_score: float,
    iteration_log: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """生成完整的对比报告.

    照搬 Hermes PR builder — shows diff, metrics, comparison.
    """
    diff_lines = compute_diff(original_instructions, evolved_instructions)
    diff_html = compute_diff_html(original_instructions, evolved_instructions)

    score_stats = _score_stats(baseline_score, evolved_score)
    length_stats = _length_stats(original_instructions, evolved_instructions)

    return {
        "baseline_score": round(baseline_score, 3),
        "evolved_score": round(evolved_score, 3),
        "score_delta": score_stats["delta"],
        "score_delta_pct": score_stats["delta_pct"],
        "significant": score_stats["significant"],
        "improved": score_stats["improved"],
        "original_length": length_stats["original"],
        "evolved_length": length_stats["evolved"],
        "length_delta": length_stats["delta"],
        "length_delta_pct": length_stats["delta_pct"],
        "diff_lines": diff_lines[:DIFF_LINE_LIMIT],
        "diff_html": diff_html,
        "diff_summary": _summarize_diff(diff_lines),
        "iteration_count": len(iteration_log) if iteration_log else 0,
    }


def _score_stats(baseline_score: float, evolved_score: float) -> Dict[str, Any]:
    delta = evolved_score - baseline_score
    delta_pct = (delta / max(baseline_score, 0.001)) * 100
    return {
        "delta": round(delta, 3),
        "delta_pct": round(delta_pct, 1),
        "significant": abs(delta) > SIGNIFICANT_SCORE_DELTA,
        "improved": delta > SIGNIFICANT_SCORE_DELTA,
    }


def _length_stats(original: str, evolved: str) -> Dict[str, Any]:
    original_len = len(original)
    evolved_len = len(evolved)
    delta = evolved_len - original_len
    return {
        "original": original_len,
        "evolved": evolved_len,
        "delta": delta,
        "delta_pct": round((delta / max(original_len, 1)) * 100, 1),
    }


def _summarize_diff(diff_lines: List[str]) -> str:
    """生成 diff 摘要."""
    added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    return f"+{added} 行, -{removed} 行"


def _esc(s: str) -> str:
    """HTML escape."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
