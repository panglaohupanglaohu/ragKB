# -*- coding: utf-8 -*-
"""RTK-inspired tool-output compression (algorithmic, Apache-2.0 ideas).

Research source: https://github.com/rtk-ai/rtk
Strategies ported deterministically (no LLM):
  1. Smart filtering — strip noise lines (progress bars, empty, pure separators)
  2. Grouping — aggregate similar lines / path prefixes
  3. Truncation — keep head+tail with size budget
  4. Deduplication — collapse repeated log lines with counts

Applied to tool/function/assistant tool-result style messages only.
Zero external binary dependency (in-process Python).
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Tuple

from ..prompt_cache import estimate_messages_tokens, estimate_tokens

# Roles that carry tool / command dumps into the next LLM turn
_TOOL_ROLES = frozenset({"tool", "function"})
_ASSISTANT_TOOLISH = re.compile(
    r"(^|\n)(exit_code|stdout|stderr|Command output|Tool result|"
    r"pytest |FAILED |PASSED |Error:|Traceback|===+|---+\s*$)",
    re.I | re.M,
)

_PROGRESS_RE = re.compile(
    r"^\s*(\d+%|Downloading|Enumerating|Counting objects|Compressing objects|"
    r"Writing objects|Resolving deltas|Installing|Building wheel).*$",
    re.I,
)
_BLANKISH_RE = re.compile(r"^\s*[-_=.*#]{3,}\s*$")
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_TEST_PASS_LINE = re.compile(
    r"^(test_|tests/|\.\/).*?\s+(ok|PASSED|passed|✓|✔)\s*$", re.I
)
_GIT_STATUS_PREFIX = re.compile(r"^(M|A|D|R|C|\?\?|!!|\s[MADRC])\s+")


def _is_toolish(role: str, content: str) -> bool:
    if role in _TOOL_ROLES:
        return True
    if role == "assistant" and len(content) > 400 and _ASSISTANT_TOOLISH.search(content):
        return True
    return False


def _dedupe_lines(lines: List[str]) -> Tuple[List[str], int]:
    """Collapse exact consecutive repeats; also global high-frequency noise lines."""
    out: List[str] = []
    collapsed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        j = i + 1
        while j < len(lines) and lines[j] == line:
            j += 1
        n = j - i
        if n > 1 and line.strip():
            out.append(f"{line}  ×{n}")
            collapsed += n - 1
        else:
            out.append(line)
        i = j
    # Global: drop pure-pass test lines beyond first few when many
    pass_lines = [ln for ln in out if _TEST_PASS_LINE.match(ln.strip())]
    if len(pass_lines) > 8:
        kept = 0
        new_out: List[str] = []
        for ln in out:
            if _TEST_PASS_LINE.match(ln.strip()):
                kept += 1
                if kept <= 3:
                    new_out.append(ln)
                continue
            new_out.append(ln)
        if kept > 3:
            new_out.append(f"…[rtk: {kept - 3} more passed tests omitted]")
            collapsed += kept - 3
        out = new_out
    return out, collapsed


def _filter_noise(lines: List[str]) -> Tuple[List[str], int]:
    removed = 0
    out: List[str] = []
    for ln in lines:
        raw = _ANSI_RE.sub("", ln)
        if not raw.strip():
            removed += 1
            continue
        if _PROGRESS_RE.match(raw):
            removed += 1
            continue
        if _BLANKISH_RE.match(raw):
            removed += 1
            continue
        out.append(raw.rstrip())
    return out, removed


def _group_paths(lines: List[str]) -> Tuple[List[str], int]:
    """Group git-status / ls-like path lines by top directory."""
    status_like = [ln for ln in lines if _GIT_STATUS_PREFIX.match(ln) or ln.startswith("./")]
    if len(status_like) < 12:
        return lines, 0
    buckets: Dict[str, List[str]] = {}
    other: List[str] = []
    for ln in lines:
        if _GIT_STATUS_PREFIX.match(ln):
            path = _GIT_STATUS_PREFIX.sub("", ln).strip()
            top = path.split("/")[0] if path else "?"
            buckets.setdefault(top, []).append(ln)
        else:
            other.append(ln)
    if not buckets:
        return lines, 0
    grouped: List[str] = []
    saved = 0
    for top, items in sorted(buckets.items(), key=lambda x: -len(x[1])):
        if len(items) <= 4:
            grouped.extend(items)
        else:
            sample = items[:3]
            grouped.extend(sample)
            grouped.append(f"…[rtk: {top}/ +{len(items) - 3} more]")
            saved += len(items) - 3
    return other + grouped, saved


def _truncate_budget(text: str, max_chars: int) -> Tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    head = max_chars * 2 // 3
    tail = max_chars // 4
    mid = len(text) - head - tail
    return (
        text[:head]
        + f"\n…[rtk truncated {mid} chars]…\n"
        + text[-tail:],
        True,
    )


def compress_tool_content(content: str, *, max_chars: int = 2200) -> Dict[str, Any]:
    """Compress a single tool/result blob. Returns {content, actions, saved_chars}."""
    if not content or len(content) < 80:
        return {"content": content, "actions": [], "saved_chars": 0}
    original = content
    actions: List[str] = []
    text = _ANSI_RE.sub("", content)
    lines = text.splitlines()
    lines, n_noise = _filter_noise(lines)
    if n_noise:
        actions.append(f"filter_noise:{n_noise}")
    lines, n_dedupe = _dedupe_lines(lines)
    if n_dedupe:
        actions.append(f"dedupe:{n_dedupe}")
    lines, n_group = _group_paths(lines)
    if n_group:
        actions.append(f"group_paths:{n_group}")
    text = "\n".join(lines)
    text, truncated = _truncate_budget(text, max_chars)
    if truncated:
        actions.append("truncate")
    saved = max(0, len(original) - len(text))
    return {"content": text, "actions": actions, "saved_chars": saved}


def rtk_compress_messages(
    messages: List[Dict[str, Any]],
    *,
    max_tool_chars: int = 2200,
) -> Dict[str, Any]:
    """Walk messages; compress toolish contents. Deterministic."""
    before = estimate_messages_tokens(messages)
    out: List[Dict[str, Any]] = []
    actions_all: List[str] = []
    touched = 0
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "user")
        content = m.get("content")
        if not isinstance(content, str):
            content = str(content or "")
        if _is_toolish(role, content) and len(content) > 120:
            r = compress_tool_content(content, max_chars=max_tool_chars)
            if r["saved_chars"] > 0:
                content = r["content"]
                actions_all.extend(r["actions"])
                touched += 1
            out.append({**m, "role": role, "content": content})
        else:
            out.append({**m, "role": role, "content": content})
    after = estimate_messages_tokens(out)
    return {
        "messages": out,
        "before_tokens": before,
        "after_tokens": after,
        "saved_tokens_est": max(0, before - after),
        "actions": actions_all,
        "tool_msgs_touched": touched,
    }
