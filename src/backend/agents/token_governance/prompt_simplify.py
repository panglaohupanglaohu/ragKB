# -*- coding: utf-8 -*-
"""确定性提示词简化 — 不调用 LLM."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from ..prompt_cache import estimate_messages_tokens, normalize_messages

_MULTI_NL = re.compile(r"\n{3,}")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
# 重复「你是」「请务必」类套话行去重
_BOILER_PREFIXES = (
    "你是",
    "you are",
    "please",
    "请务必",
    "重要：",
    "注意：",
    "important:",
)


def _simplify_text(text: str) -> str:
    if not text:
        return text
    t = text.replace("\r\n", "\n").strip()
    t = _MULTI_NL.sub("\n\n", t)
    lines = []
    seen = set()
    for line in t.split("\n"):
        s = _MULTI_SPACE.sub(" ", line).strip()
        if not s:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        key = s.lower()
        # 短套话重复行折叠
        is_boiler = any(key.startswith(p) for p in _BOILER_PREFIXES) and len(s) < 120
        if is_boiler and key in seen:
            continue
        if is_boiler:
            seen.add(key)
        lines.append(s)
    return "\n".join(lines).strip()


def simplify_messages(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """简化 system/user 文本；tool 结果不动（由 compress 处理）."""
    norm = normalize_messages(messages)
    before = estimate_messages_tokens(norm)
    out: List[Dict[str, str]] = []
    actions = 0
    for m in norm:
        role = m["role"]
        content = m["content"]
        if role in ("system", "user", "assistant") and content:
            new_c = _simplify_text(content)
            if new_c != content:
                actions += 1
            content = new_c
        out.append({"role": role, "content": content})
    after = estimate_messages_tokens(out)
    return {
        "messages": out,
        "before_tokens": before,
        "after_tokens": after,
        "saved_tokens_est": max(0, before - after),
        "actions": actions,
    }
