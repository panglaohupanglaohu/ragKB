# -*- coding: utf-8 -*-
"""Claude-Mem-inspired progressive disclosure for multi-turn history.

Research: https://github.com/thedotmack/claude-mem
Key idea: ~10x token savings via index → timeline → full details only on demand.
Here (in-process, zero LLM):
  - Keep system + last N user/assistant/tool turns full
  - Older middle turns collapse to one-line index (~50–100 tokens each)
  - Never drop the first user task statement (goal anchor)
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..prompt_cache import estimate_messages_tokens, estimate_tokens


def _one_line(content: str, max_len: int = 120) -> str:
    s = " ".join((content or "").split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def progressive_collapse(
    messages: List[Dict[str, Any]],
    *,
    keep_recent: int = 6,
    min_total_for_collapse: int = 10,
    index_max_chars: int = 140,
) -> Dict[str, Any]:
    """Collapse old turns to index lines when conversation is long."""
    before = estimate_messages_tokens(messages)
    msgs = [dict(m) for m in (messages or []) if isinstance(m, dict)]
    if len(msgs) < min_total_for_collapse:
        return {
            "messages": msgs,
            "before_tokens": before,
            "after_tokens": before,
            "saved_tokens_est": 0,
            "collapsed": 0,
        }

    # Partition: leading systems stay; first non-system is goal anchor
    systems: List[Dict[str, Any]] = []
    rest: List[Dict[str, Any]] = []
    for m in msgs:
        if m.get("role") == "system" and not rest:
            systems.append(m)
        else:
            rest.append(m)

    if len(rest) <= keep_recent + 1:
        return {
            "messages": msgs,
            "before_tokens": before,
            "after_tokens": before,
            "saved_tokens_est": 0,
            "collapsed": 0,
        }

    anchor = rest[0]
    middle = rest[1: -keep_recent]
    recent = rest[-keep_recent:]
    if not middle:
        return {
            "messages": msgs,
            "before_tokens": before,
            "after_tokens": before,
            "saved_tokens_est": 0,
            "collapsed": 0,
        }

    index_lines = []
    for i, m in enumerate(middle, 1):
        role = str(m.get("role") or "?")
        content = m.get("content")
        if not isinstance(content, str):
            content = str(content or "")
        # Skip already-tiny messages (no gain)
        if estimate_tokens(content) <= 40:
            index_lines.append(f"#{i} [{role}] {_one_line(content, index_max_chars)}")
            continue
        index_lines.append(f"#{i} [{role}] {_one_line(content, index_max_chars)}")

    index_msg = {
        "role": "system",
        "content": (
            "[TG_MEM_INDEX] progressive disclosure (claude-mem style)\n"
            f"Collapsed {len(middle)} older turns to index. Full detail was dropped to save tokens.\n"
            + "\n".join(index_lines[:40])
            + (f"\n…(+{len(index_lines) - 40} more)" if len(index_lines) > 40 else "")
        ),
    }

    out = systems + [anchor, index_msg] + recent
    after = estimate_messages_tokens(out)
    return {
        "messages": out,
        "before_tokens": before,
        "after_tokens": after,
        "saved_tokens_est": max(0, before - after),
        "collapsed": len(middle),
    }
