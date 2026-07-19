# -*- coding: utf-8 -*-
"""Flowork-Router-inspired cost-tier classifier for model routing.

Research: https://github.com/flowork-os/flowork_Router
Heuristic (no LLM): char count + code + tool_use + multi-turn → economy|standard|frontier.
Pairs with ModelRouter tiers to pick cheaper models on simple turns.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

_CODE_FENCE = re.compile(r"```")
_CODE_HINT = re.compile(
    r"\b(def |class |function |import |from |const |let |var |public |private |"
    r"async |await |SELECT |INSERT |CREATE TABLE)\b",
    re.I,
)
_COMPLEX_HINT = re.compile(
    r"\b(refactor|architecture|design|migrate|security audit|race condition|"
    r"distributed|consensus|prove|formal|multi-step plan|根因|架构|重构)\b",
    re.I,
)
_SIMPLE_HINT = re.compile(
    r"\b(what is|who is|yes|no|ok|thanks|ping|status|你好|是什么|列出|list )\b",
    re.I,
)


def classify_complexity(
    messages: List[Dict[str, Any]],
    *,
    has_tools: bool = False,
) -> Dict[str, Any]:
    """Return {tier_hint, score, reasons[]} where tier_hint is economy|standard|frontier."""
    texts: List[str] = []
    n_turns = 0
    n_tools = 0
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "")
        content = m.get("content")
        if not isinstance(content, str):
            content = str(content or "")
        if role in ("user", "assistant", "system"):
            texts.append(content)
            if role in ("user", "assistant"):
                n_turns += 1
        if role in ("tool", "function"):
            n_tools += 1
            texts.append(content[:2000])

    blob = "\n".join(texts)
    chars = len(blob)
    score = 0
    reasons: List[str] = []

    if chars < 400:
        score -= 2
        reasons.append("short_context")
    elif chars > 12000:
        score += 2
        reasons.append("long_context")
    elif chars > 4000:
        score += 1
        reasons.append("medium_context")

    if _CODE_FENCE.search(blob) or _CODE_HINT.search(blob):
        score += 1
        reasons.append("code")
    if _COMPLEX_HINT.search(blob):
        score += 2
        reasons.append("complex_keywords")
    if _SIMPLE_HINT.search(blob) and chars < 800:
        score -= 2
        reasons.append("simple_keywords")
    if n_tools > 0 or has_tools:
        score += 1
        reasons.append("tool_use")
    if n_turns >= 8:
        score += 1
        reasons.append("multi_turn")
    if n_turns <= 2 and chars < 600:
        score -= 1
        reasons.append("few_turns")

    if score <= -1:
        tier = "economy"
    elif score >= 3:
        tier = "frontier"
    else:
        tier = "standard"

    return {
        "tier_hint": tier,
        "score": score,
        "reasons": reasons,
        "chars": chars,
        "turns": n_turns,
        "tool_msgs": n_tools,
    }


def map_hint_to_model_tier(hint: str) -> str:
    h = (hint or "standard").lower()
    if h in ("economy", "standard", "frontier"):
        return h
    return "standard"
