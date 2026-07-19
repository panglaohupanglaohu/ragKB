# -*- coding: utf-8 -*-
"""Ponytail (YAGNI ladder) + Caveman/Flowork terse-output injectors.

Research:
  - https://skillsllm.com/skill/ponytail  (MIT skill in repo ponytail/)
  - Flowork Router "Caveman mode" — terse output instruction
  - OpenWolf — budget-capped digest of preferences (imitate, AGPL not copied)

These primarily cut *output* tokens and reduce follow-up tool thrash.
Inject is tiny (≤ ~180 tokens) and only once per conversation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..prompt_cache import estimate_messages_tokens

_PONYTAIL_TAG = "[TG_PONYTAIL]"
_CAVEMAN_TAG = "[TG_CAVEMAN]"

_PONYTAIL_FULL = (
    f"{_PONYTAIL_TAG} Lazy senior ladder (stop at first rung that holds):\n"
    "1) Need exist? else skip. 2) Stdlib/native? 3) Existing dep?\n"
    "4) One line? 5) Else minimum that works. No unrequested abstractions.\n"
    "Never skip: validation at trust boundary, data-loss handling, security, a11y.\n"
    "Output: code/result first; ≤3 short lines on what was skipped."
)

_PONYTAIL_LITE = (
    f"{_PONYTAIL_TAG} Prefer simplest working path; name lazier alternative in one line."
)

_PONYTAIL_ULTRA = (
    f"{_PONYTAIL_TAG} ULTRA YAGNI: delete before add; ship one-liner; challenge extra requirements."
)

_CAVEMAN = {
    "lite": f"{_CAVEMAN_TAG} Reply concise. Keep code/paths/commands exact.",
    "full": (
        f"{_CAVEMAN_TAG} Reply terse: short sentences, no essays. "
        "Code/paths/commands exact. Skip filler."
    ),
    "ultra": (
        f"{_CAVEMAN_TAG} ULTRA terse: bullets only when needed; zero fluff; "
        "code/paths exact."
    ),
}


def _ponytail_text(level: str) -> str:
    lv = (level or "full").lower()
    if lv == "off":
        return ""
    if lv == "lite":
        return _PONYTAIL_LITE
    if lv == "ultra":
        return _PONYTAIL_ULTRA
    return _PONYTAIL_FULL


def _caveman_text(level: str) -> str:
    lv = (level or "full").lower()
    if lv == "off":
        return ""
    return _CAVEMAN.get(lv, _CAVEMAN["full"])


def inject_behavior(
    messages: List[Dict[str, Any]],
    *,
    ponytail: str = "full",
    caveman: str = "full",
) -> Dict[str, Any]:
    """Append compact behavior rules to first system message (idempotent)."""
    before = estimate_messages_tokens(messages)
    work = [dict(m) for m in (messages or []) if isinstance(m, dict)]
    if not work:
        return {
            "messages": work,
            "before_tokens": before,
            "after_tokens": before,
            "saved_tokens_est": 0,
            "injected": [],
        }

    chunks: List[str] = []
    injected: List[str] = []
    p = _ponytail_text(ponytail)
    c = _caveman_text(caveman)

    # find system
    sys_idx = next((i for i, m in enumerate(work) if m.get("role") == "system"), None)
    if sys_idx is None:
        work.insert(0, {"role": "system", "content": ""})
        sys_idx = 0
    sys0 = str(work[sys_idx].get("content") or "")

    if p and _PONYTAIL_TAG not in sys0:
        chunks.append(p)
        injected.append("ponytail")
    if c and _CAVEMAN_TAG not in sys0:
        chunks.append(c)
        injected.append("caveman")

    if chunks:
        add = "\n".join(chunks)
        work[sys_idx] = {
            **work[sys_idx],
            "content": (sys0 + "\n" + add).strip(),
        }

    after = estimate_messages_tokens(work)
    # Inject adds input tokens; report delta (may be negative = growth)
    return {
        "messages": work,
        "before_tokens": before,
        "after_tokens": after,
        "saved_tokens_est": max(0, before - after),  # usually 0
        "input_delta": after - before,
        "injected": injected,
        # Heuristic output-token savings estimate for KPI (not added to input saved)
        "output_save_est": 80 * len(injected) if injected else 0,
    }
