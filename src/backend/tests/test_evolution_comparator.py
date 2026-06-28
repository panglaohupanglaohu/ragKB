# -*- coding: utf-8 -*-
"""Regression tests for evolution comparison helpers."""

from __future__ import annotations

from agents.evolution.comparator import compute_diff, compute_diff_html, compare_results


def test_compute_diff_uses_baseline_and_evolved_headers():
    diff = compute_diff("line 1\nold\n", "line 1\nnew\n")

    assert diff[0] == "--- baseline"
    assert diff[1] == "+++ evolved"
    assert any(line.startswith("-old") for line in diff)
    assert any(line.startswith("+new") for line in diff)


def test_compute_diff_html_escapes_content_and_marks_changes():
    html = compute_diff_html("<old>", "<new>&")

    assert '<div class="diff-del">- &lt;old&gt;</div>' in html
    assert '<div class="diff-add">+ &lt;new&gt;&amp;</div>' in html


def test_compare_results_preserves_score_length_and_iteration_fields():
    report = compare_results(
        "alpha\nold",
        "alpha\nnew value",
        baseline_score=0.5,
        evolved_score=0.58,
        iteration_log=[{"iteration": 1}, {"iteration": 2}],
    )

    assert report["baseline_score"] == 0.5
    assert report["evolved_score"] == 0.58
    assert report["score_delta"] == 0.08
    assert report["score_delta_pct"] == 16.0
    assert report["significant"] is True
    assert report["improved"] is True
    assert report["original_length"] == len("alpha\nold")
    assert report["evolved_length"] == len("alpha\nnew value")
    assert report["length_delta"] == len("alpha\nnew value") - len("alpha\nold")
    assert report["iteration_count"] == 2
    assert report["diff_summary"] == "+1 行, -1 行"


def test_compare_results_keeps_significance_threshold_behavior():
    below = compare_results("a", "a", baseline_score=0.5, evolved_score=0.54)
    above = compare_results("a", "a", baseline_score=0.5, evolved_score=0.56)

    assert below["score_delta"] == 0.04
    assert below["significant"] is False
    assert below["improved"] is False
    assert above["score_delta"] == 0.06
    assert above["significant"] is True
    assert above["improved"] is True


def test_compare_results_caps_diff_lines():
    original = "\n".join(f"old {i}" for i in range(150))
    evolved = "\n".join(f"new {i}" for i in range(150))

    report = compare_results(original, evolved, 0.1, 0.2)

    assert len(report["diff_lines"]) == 100
