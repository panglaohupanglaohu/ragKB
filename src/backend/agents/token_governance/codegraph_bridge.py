# -*- coding: utf-8 -*-
"""CodeGraph integration (MIT) — surgical context instead of full-file dumps.

Package: @colbymchenry/codegraph (https://github.com/colbymchenry/codegraph)
License: MIT — we call the installed CLI; no AGPL contamination.

When available:
  - `codegraph explore <query>` for coding tasks (inject compact result)
  - Lightweight local symbol slice for large source tool dumps (always on)

When CLI missing or project not indexed: local regex symbol extraction only.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..prompt_cache import estimate_messages_tokens, estimate_tokens

logger = logging.getLogger(__name__)

_FN_PY = re.compile(
    r"^(async\s+def|def)\s+(\w+)\s*\(", re.M,
)
_FN_JS = re.compile(
    r"^(export\s+)?(async\s+)?function\s+(\w+)|^(export\s+)?const\s+(\w+)\s*=\s*(async\s*)?\(",
    re.M,
)
_CLASS = re.compile(r"^(export\s+)?(class|interface|type)\s+(\w+)", re.M)
_SOURCE_HINT = re.compile(
    r"(\.py|\.js|\.ts|\.tsx|\.jsx|\.go|\.rs|\.java)\b|^(#!/usr/bin|from |import |package |func )",
    re.M,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]


def find_codegraph_bin() -> Optional[str]:
    env = os.environ.get("CODEGRAPH_BIN") or os.environ.get("AG_CODEGRAPH_BIN")
    if env and Path(env).exists():
        return env
    which = shutil.which("codegraph")
    if which:
        return which
    # common npm global
    home = Path.home()
    candidates = [
        home / ".local/node/bin/codegraph",
        home / ".npm-global/bin/codegraph",
        Path("/usr/local/bin/codegraph"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def project_has_index(root: Optional[Path] = None) -> bool:
    base = root or _REPO_ROOT
    return (base / ".codegraph").is_dir()


def _extract_symbol_digest(content: str, *, max_symbols: int = 24) -> str:
    """Local surgical digest: keep signatures + line ranges, drop bodies."""
    lines = content.splitlines()
    hits: List[Tuple[int, str]] = []
    for i, ln in enumerate(lines, 1):
        m = _FN_PY.match(ln) or _CLASS.match(ln)
        if m:
            name = m.group(m.lastindex) if m.lastindex else ln.strip()[:40]
            hits.append((i, f"L{i}: {ln.strip()[:100]}"))
            continue
        m2 = _FN_JS.match(ln)
        if m2:
            hits.append((i, f"L{i}: {ln.strip()[:100]}"))
    if not hits:
        # fallback: first 30 + last 15 lines with total size note
        head = "\n".join(lines[:30])
        tail = "\n".join(lines[-15:]) if len(lines) > 45 else ""
        return (
            f"[TG_CODEGRAPH local-slice chars={len(content)} lines={len(lines)}]\n"
            f"{head}\n…\n{tail}"
        )
    body = "\n".join(h[1] for h in hits[:max_symbols])
    more = f"\n…(+{len(hits) - max_symbols} symbols)" if len(hits) > max_symbols else ""
    return (
        f"[TG_CODEGRAPH local-symbols n={len(hits)} lines={len(lines)} chars={len(content)}]\n"
        f"{body}{more}\n"
        f"(full body omitted — use offset/limit or codegraph explore for one symbol)"
    )


def compress_source_blobs(
    messages: List[Dict[str, Any]],
    *,
    min_chars: int = 2500,
) -> Dict[str, Any]:
    """Replace huge source-like tool/user dumps with symbol digests."""
    before = estimate_messages_tokens(messages)
    out: List[Dict[str, Any]] = []
    replaced = 0
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "user")
        content = m.get("content")
        if not isinstance(content, str):
            content = str(content or "")
        if (
            role in ("tool", "function", "assistant", "user")
            and len(content) >= min_chars
            and _SOURCE_HINT.search(content[:2000] + content[-500:])
        ):
            dig = _extract_symbol_digest(content)
            if estimate_tokens(dig) < estimate_tokens(content):
                content = dig
                replaced += 1
        out.append({**m, "role": role, "content": content})
    after = estimate_messages_tokens(out)
    return {
        "messages": out,
        "before_tokens": before,
        "after_tokens": after,
        "saved_tokens_est": max(0, before - after),
        "replaced": replaced,
        "mode": "local_symbols",
    }


def explore_via_cli(
    query: str,
    *,
    project_path: Optional[str] = None,
    timeout_sec: float = 8.0,
    max_chars: int = 3500,
) -> Dict[str, Any]:
    """Call `codegraph explore` if binary + index exist."""
    bin_path = find_codegraph_bin()
    root = Path(project_path or str(_REPO_ROOT))
    if not bin_path:
        return {"ok": False, "error": "codegraph_bin_missing", "text": ""}
    if not (root / ".codegraph").is_dir():
        return {"ok": False, "error": "no_index", "text": "", "hint": "run: codegraph init"}
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "empty_query", "text": ""}
    try:
        proc = subprocess.run(
            [bin_path, "explore", q, "--path", str(root)],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=str(root),
        )
        text = (proc.stdout or "") + (("\n" + proc.stderr) if proc.returncode else "")
        text = text.strip()
        if len(text) > max_chars:
            text = text[: max_chars - 20] + "\n…[codegraph truncated]"
        return {
            "ok": proc.returncode == 0 and bool(text),
            "text": text,
            "returncode": proc.returncode,
            "bin": bin_path,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "text": ""}
    except Exception as e:
        logger.debug("codegraph explore: %s", e)
        return {"ok": False, "error": str(e), "text": ""}


def apply_codegraph(
    messages: List[Dict[str, Any]],
    *,
    query: str = "",
    project_path: Optional[str] = None,
    use_cli: bool = True,
    min_blob_chars: int = 2500,
) -> Dict[str, Any]:
    """Local surgical compress + optional CLI explore inject into system."""
    local = compress_source_blobs(messages, min_chars=int(min_blob_chars or 2500))
    work = local["messages"]
    cli_info: Dict[str, Any] = {"ok": False}
    injected_cli = False
    if use_cli and query:
        cli_info = explore_via_cli(query, project_path=project_path)
        if cli_info.get("ok") and cli_info.get("text"):
            # inject compact explore as system note
            tag = "[TG_CODEGRAPH_EXPLORE]"
            note = f"{tag}\n{cli_info['text']}"
            # avoid duplicating
            has = any(
                isinstance(m, dict)
                and m.get("role") == "system"
                and tag in str(m.get("content") or "")
                for m in work
            )
            if not has:
                # Prefer appending to first system
                for i, m in enumerate(work):
                    if m.get("role") == "system":
                        work[i] = {
                            **m,
                            "content": str(m.get("content") or "") + "\n" + note,
                        }
                        injected_cli = True
                        break
                if not injected_cli:
                    work = [{"role": "system", "content": note}] + work
                    injected_cli = True

    after = estimate_messages_tokens(work)
    before = local["before_tokens"]
    return {
        "messages": work,
        "before_tokens": before,
        "after_tokens": after,
        "saved_tokens_est": max(0, before - after),
        "replaced": local.get("replaced", 0),
        "cli": {
            "ok": bool(cli_info.get("ok")),
            "error": cli_info.get("error"),
            "hint": cli_info.get("hint"),
            "bin": cli_info.get("bin"),
        },
        "cli_injected": injected_cli,
        "bin": find_codegraph_bin(),
        "indexed": project_has_index(Path(project_path) if project_path else None),
    }
