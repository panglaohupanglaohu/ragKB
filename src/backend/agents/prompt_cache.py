# -*- coding: utf-8 -*-
"""Prompt 上下文缓存 + 确定性内容压缩（任务 Token 治理）.

选型：
- 缓存：进程内 LRU，键 = 规范化消息指纹（SHA-256）
- 压缩：去重相邻同角色消息、折叠重复 tool 结果、截断超长 system/user
- 不调用 LLM 做摘要（避免递归烧 token）
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

# 默认：system 最多 6k 字符；单条 user/tool 最多 4k；缓存 256 条
_DEFAULT_SYSTEM_MAX = 6000
_DEFAULT_MSG_MAX = 4000
_DEFAULT_CACHE_SIZE = 256


def _utc() -> float:
    return time.time()


def normalize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """只保留 role/content，content 转 str，便于指纹与压缩."""
    out: List[Dict[str, str]] = []
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "user")
        content = m.get("content")
        if content is None:
            content = m.get("text") or ""
        if not isinstance(content, str):
            try:
                content = json.dumps(content, ensure_ascii=False, sort_keys=True)
            except Exception:
                content = str(content)
        out.append({"role": role, "content": content})
    return out


def fingerprint_messages(messages: List[Dict[str, Any]]) -> str:
    """规范化后 SHA-256（确定性）."""
    norm = normalize_messages(messages)
    payload = json.dumps(norm, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    """粗估 token：中英混排约 2 字符 ≈ 1 token（保守偏高）."""
    if not text:
        return 0
    return max(1, (len(text) + 1) // 2)


def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    total = 0
    for m in normalize_messages(messages):
        total += estimate_tokens(m.get("content") or "") + 4  # 角色开销
    return total


def compress_messages(
    messages: List[Dict[str, Any]],
    *,
    system_max_chars: int = _DEFAULT_SYSTEM_MAX,
    msg_max_chars: int = _DEFAULT_MSG_MAX,
) -> Dict[str, Any]:
    """确定性压缩。返回 {messages, before_tokens, after_tokens, actions[]}."""
    norm = normalize_messages(messages)
    before = estimate_messages_tokens(norm)
    actions: List[str] = []
    compressed: List[Dict[str, str]] = []

    for m in norm:
        role = m["role"]
        content = m["content"]
        limit = system_max_chars if role == "system" else msg_max_chars

        # 相邻同 role + 同 content 去重
        if compressed and compressed[-1]["role"] == role and compressed[-1]["content"] == content:
            actions.append("dedupe_adjacent")
            continue

        # 重复 tool / assistant 长结果折叠标记
        if role in ("tool", "function", "assistant") and len(content) > limit:
            head = content[: max(200, limit // 3)]
            tail = content[-max(100, limit // 6) :]
            content = (
                head
                + f"\n…[compressed {len(m['content'])} chars]…\n"
                + tail
            )
            actions.append("fold_long_" + role)

        if len(content) > limit:
            content = content[:limit] + f"…[+{len(m['content']) - limit} chars truncated]"
            actions.append("truncate_" + role)

        compressed.append({"role": role, "content": content})

    after = estimate_messages_tokens(compressed)
    return {
        "messages": compressed,
        "before_tokens": before,
        "after_tokens": after,
        "saved_tokens_est": max(0, before - after),
        "actions": actions,
        "action_counts": _count_actions(actions),
    }


def _count_actions(actions: List[str]) -> Dict[str, int]:
    c: Dict[str, int] = {}
    for a in actions:
        c[a] = c.get(a, 0) + 1
    return c


class PromptCache:
    """进程内 LRU 提示词/上下文缓存."""

    def __init__(self, max_size: int = _DEFAULT_CACHE_SIZE) -> None:
        self.max_size = max(8, int(max_size or _DEFAULT_CACHE_SIZE))
        self._lock = threading.Lock()
        self._store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.writes = 0
        self.tokens_saved_est = 0

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if key not in self._store:
                self.misses += 1
                return None
            self._store.move_to_end(key)
            self.hits += 1
            entry = self._store[key]
            saved = int(entry.get("tokens_est") or 0)
            self.tokens_saved_est += saved
            return dict(entry)

    def put(
        self,
        key: str,
        *,
        value: Any = None,
        tokens_est: int = 0,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = {
                "value": value,
                "tokens_est": int(tokens_est or 0),
                "meta": dict(meta or {}),
                "at": _utc(),
            }
            self.writes += 1
            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def lookup_messages(
        self,
        messages: List[Dict[str, Any]],
        *,
        compress: bool = True,
    ) -> Dict[str, Any]:
        """查缓存；可选先 compress 再指纹."""
        work = messages
        compress_info = None
        if compress:
            compress_info = compress_messages(messages)
            work = compress_info["messages"]
        key = fingerprint_messages(work)
        hit = self.get(key)
        return {
            "key": key,
            "hit": hit is not None,
            "entry": hit,
            "compress": compress_info,
            "tokens_est": estimate_messages_tokens(work),
        }

    def store_messages(
        self,
        messages: List[Dict[str, Any]],
        *,
        value: Any = "cached",
        compress: bool = True,
    ) -> str:
        work = messages
        if compress:
            work = compress_messages(messages)["messages"]
        key = fingerprint_messages(work)
        self.put(key, value=value, tokens_est=estimate_messages_tokens(work))
        return key

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            return {
                "size": len(self._store),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "writes": self.writes,
                "hit_rate": round(self.hits / total, 4) if total else 0.0,
                "tokens_saved_est": self.tokens_saved_est,
            }

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self.hits = self.misses = self.writes = 0
            self.tokens_saved_est = 0


_GLOBAL_CACHE: Optional[PromptCache] = None
_GLOBAL_LOCK = threading.Lock()


def get_prompt_cache() -> PromptCache:
    global _GLOBAL_CACHE
    with _GLOBAL_LOCK:
        if _GLOBAL_CACHE is None:
            _GLOBAL_CACHE = PromptCache()
        return _GLOBAL_CACHE


def resize_prompt_cache(max_size: int) -> PromptCache:
    """Apply cache_max_size from token_governance params (keeps entries when shrinking)."""
    global _GLOBAL_CACHE
    size = max(8, int(max_size or _DEFAULT_CACHE_SIZE))
    with _GLOBAL_LOCK:
        if _GLOBAL_CACHE is None:
            _GLOBAL_CACHE = PromptCache(max_size=size)
        else:
            _GLOBAL_CACHE.max_size = size
            # trim if over
            while len(_GLOBAL_CACHE._store) > _GLOBAL_CACHE.max_size:
                _GLOBAL_CACHE._store.popitem(last=False)
        return _GLOBAL_CACHE
