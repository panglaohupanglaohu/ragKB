"""AgentToolbox — function-calling tools for code-aware agents.

Gives Developer / QA agents the ability to read, grep, write, and execute code
in the project so they don't have to hallucinate file contents.

All tool calls are scoped to the project root and write operations are
restricted to a safe allowlist (src/, tests/, docs/, config/, public/).

Each tool returns a JSON-serializable dict suitable for OpenAI/DeepSeek
function-calling protocol.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sandbox.python_runner import get_sandbox

logger = logging.getLogger("AgentToolbox")

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # src/backend/agents/ -> root
ALLOWED_WRITE_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/",
                           "storage/agent_workspaces/", "storage/pipeline_runs/")
MAX_FILE_BYTES = 256 * 1024   # 256KB per read
MAX_GREP_HITS = 200
MAX_EXEC_OUTPUT = 32 * 1024   # 32KB stdout/stderr cap


# ═════════════════════════════════════════════════════════════════
# OpenAI / DeepSeek function-calling tool schema (V4 supports this)
# ═════════════════════════════════════════════════════════════════

TOOL_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "读取项目里某个文件的内容。优先使用此工具理解现有代码，再基于实际代码做修改。"
                "只能读取项目根目录下的文件。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "项目相对路径，如 src/backend/channels/marine_base.py",
                    },
                    "start_line": {"type": "integer", "description": "起始行 (1-based, 可选)", "default": 1},
                    "end_line": {"type": "integer", "description": "结束行 (1-based, 可选)", "default": 0},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": (
                "在项目中按正则搜索文本。用于查找类/函数/枚举值的真实定义位置。"
                "返回每个匹配的文件路径、行号、行内容。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "正则表达式"},
                    "include": {
                        "type": "string",
                        "description": "glob 限定，如 src/backend/**/*.py",
                        "default": "**/*",
                    },
                    "max_hits": {"type": "integer", "default": 50},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出某个目录下的所有文件（递归）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "项目相对目录"},
                    "max_depth": {"type": "integer", "default": 3},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "向项目写入或新建文件。只能写入 src/, tests/, docs/, config/, public/ 下。"
                "如果目标已存在，旧内容会先备份为 .bak。优先创建新文件而非整文件覆盖大文件。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "项目相对路径"},
                    "content": {"type": "string", "description": "完整文件内容"},
                    "create_only": {
                        "type": "boolean",
                        "description": "为 true 时仅在文件不存在时写入",
                        "default": False,
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "patch_file",
            "description": (
                "对已有文件做精准搜索-替换。比 write_file 安全，因为它要求你先看到原文。"
                "search 必须是文件中存在的、唯一的连续片段。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "search": {"type": "string", "description": "要被替换的原文片段（必须唯一）"},
                    "replace": {"type": "string", "description": "替换为的新内容"},
                },
                "required": ["path", "search", "replace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": (
                "在项目 venv 中执行一段 Python 代码（cwd=src/backend）。"
                "用于验证 import 是否成功、检查类的属性等。最长执行 30s。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                    "timeout": {"type": "integer", "default": 30},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_pytest",
            "description": (
                "运行 pytest，可指定路径或 -k 表达式。仅 QA agent 使用。"
                "返回最后 60 行输出。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "测试路径或 -k 表达式", "default": ""},
                    "timeout": {"type": "integer", "default": 120},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": (
                "声明任务完成。Agent 调用此工具表示完成本步骤的所有工作，并附上简短总结。"
                "调用后循环终止。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "本步骤完成情况的简短总结"},
                    "files_changed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "本步骤修改/新建的文件路径列表",
                        "default": [],
                    },
                },
                "required": ["summary"],
            },
        },
    },
]


def _safe_path(rel: str) -> Path:
    """Resolve a project-relative path, refusing escapes."""
    if not rel:
        raise ValueError("empty path")
    p = (PROJECT_ROOT / rel).resolve()
    try:
        p.relative_to(PROJECT_ROOT)
    except ValueError:
        raise PermissionError(f"path escapes project root: {rel}")
    return p


def _is_allowed_write(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    return any(rel.startswith(p) for p in ALLOWED_WRITE_PREFIXES)


# ═════════════════════════════════════════════════════════════════
# Tool implementations
# ═════════════════════════════════════════════════════════════════

def tool_read_file(path: str, start_line: int = 1, end_line: int = 0) -> Dict[str, Any]:
    try:
        p = _safe_path(path)
        if not p.is_file():
            return {"ok": False, "error": f"not a file: {path}"}
        size = p.stat().st_size
        if size > MAX_FILE_BYTES * 4:
            return {
                "ok": False,
                "error": f"file too large ({size}B). Use grep to find the relevant section first.",
            }
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        total = len(lines)
        if end_line and end_line > 0:
            lines = lines[max(0, start_line - 1):end_line]
        elif start_line > 1:
            lines = lines[start_line - 1:]
        out = "\n".join(lines)
        if len(out) > MAX_FILE_BYTES:
            out = out[:MAX_FILE_BYTES] + "\n…(truncated)"
        return {"ok": True, "path": path, "total_lines": total, "content": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_grep(pattern: str, include: str = "**/*", max_hits: int = 50) -> Dict[str, Any]:
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return {"ok": False, "error": f"bad regex: {e}"}
    max_hits = min(max_hits, MAX_GREP_HITS)
    hits: List[Dict[str, Any]] = []
    for fp in PROJECT_ROOT.glob(include):
        if not fp.is_file():
            continue
        # Skip irrelevant
        rel = str(fp.relative_to(PROJECT_ROOT))
        if any(seg in rel for seg in ("/node_modules/", "/.git/", "/__pycache__/", "/venv/", ".bak")):
            continue
        try:
            with fp.open("r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        if "tool_grep(" in line and pattern in line:
                            continue
                        hits.append({"path": rel, "line": i, "text": line.rstrip()[:200]})
                        if len(hits) >= max_hits:
                            return {"ok": True, "hits": hits, "truncated": True}
        except Exception:
            continue
    return {"ok": True, "hits": hits, "truncated": False}


def tool_list_files(path: str, max_depth: int = 3) -> Dict[str, Any]:
    try:
        p = _safe_path(path)
        if not p.is_dir():
            return {"ok": False, "error": f"not a directory: {path}"}
        out: List[str] = []
        base_depth = len(p.parts)
        for root, dirs, files in os.walk(p):
            depth = len(Path(root).parts) - base_depth
            if depth >= max_depth:
                dirs[:] = []
                if depth > 0:
                    files = []
            elif depth > max_depth:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs
                       if not d.startswith(".")
                       and d not in ("node_modules", "__pycache__", "venv")]
            for f in files:
                if f.endswith((".pyc", ".bak")):
                    continue
                rel = str((Path(root) / f).relative_to(PROJECT_ROOT))
                out.append(rel)
                if len(out) >= 500:
                    return {"ok": True, "files": out, "truncated": True}
        return {"ok": True, "files": out, "truncated": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_write_file(path: str, content: str, create_only: bool = False) -> Dict[str, Any]:
    try:
        if not _is_allowed_write(path):
            return {"ok": False, "error": f"write denied (outside allowed dirs): {path}"}
        p = _safe_path(path)
        if p.exists() and create_only:
            return {"ok": False, "error": f"file exists and create_only=True: {path}"}
        # Shrink-replace guard
        if p.is_file():
            old_size = p.stat().st_size
            if old_size > 2048 and len(content) < old_size * 0.5:
                return {
                    "ok": False,
                    "error": (
                        f"shrink-replace blocked: new {len(content)}B "
                        f"< 50% of existing {old_size}B. "
                        f"Use patch_file for incremental edits, or write a new file."
                    ),
                }
            # Backup
            bak = p.with_suffix(p.suffix + ".bak")
            try:
                bak.write_bytes(p.read_bytes())
            except Exception:
                pass
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": path, "bytes": len(content), "created": not p.exists()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_patch_file(path: str, search: str, replace: str) -> Dict[str, Any]:
    try:
        if not _is_allowed_write(path):
            return {"ok": False, "error": f"write denied: {path}"}
        p = _safe_path(path)
        if not p.is_file():
            return {"ok": False, "error": f"file not found: {path}"}
        text = p.read_text(encoding="utf-8")
        cnt = text.count(search)
        if cnt == 0:
            return {"ok": False, "error": "search pattern not found in file"}
        if cnt > 1:
            return {
                "ok": False,
                "error": f"search pattern matches {cnt} times — must be unique. Add more context.",
            }
        new_text = text.replace(search, replace, 1)
        bak = p.with_suffix(p.suffix + ".bak")
        try:
            bak.write_text(text, encoding="utf-8")
        except Exception:
            pass
        p.write_text(new_text, encoding="utf-8")
        return {"ok": True, "path": path, "old_bytes": len(text), "new_bytes": len(new_text)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_run_python(code: str, timeout: int = 30) -> Dict[str, Any]:
    cwd = PROJECT_ROOT / "src" / "backend"
    return get_sandbox().run_python(code, cwd=cwd, timeout=timeout).to_dict()


def tool_run_pytest(target: str = "", timeout: int = 120) -> Dict[str, Any]:
    return get_sandbox().run_pytest(target=target, cwd=PROJECT_ROOT, timeout=timeout).to_dict()


# ═════════════════════════════════════════════════════════════════
# Dispatcher
# ═════════════════════════════════════════════════════════════════

_DISPATCH = {
    "read_file": lambda **kw: tool_read_file(**kw),
    "grep": lambda **kw: tool_grep(**kw),
    "list_files": lambda **kw: tool_list_files(**kw),
    "write_file": lambda **kw: tool_write_file(**kw),
    "patch_file": lambda **kw: tool_patch_file(**kw),
    "run_python": lambda **kw: tool_run_python(**kw),
    "run_pytest": lambda **kw: tool_run_pytest(**kw),
}


def dispatch_tool_call(name: str, args_json: str) -> Dict[str, Any]:
    """Execute a tool by name with JSON-encoded arguments. Returns JSON-safe dict."""
    fn = _DISPATCH.get(name)
    if name == "finish":
        return {"ok": True, "_finished": True}
    if not fn:
        return {"ok": False, "error": f"unknown tool: {name}"}
    try:
        args = json.loads(args_json) if args_json else {}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"bad arguments JSON: {e}"}
    try:
        result = fn(**args)
    except TypeError as e:
        return {"ok": False, "error": f"bad arguments: {e}"}
    except Exception as e:
        logger.exception("[Toolbox] tool %s crashed", name)
        return {"ok": False, "error": str(e)}
    # Truncate giant fields for transport
    return result


def get_tools_for_role(role: str) -> List[Dict[str, Any]]:
    """Return tool subset appropriate for a given agent role."""
    role = (role or "").lower()
    base = ["read_file", "grep", "list_files", "finish"]
    if role in ("developer", "build_developer", "code_writer", "deploy", "devops",
                "build_deployer"):
        base += ["write_file", "patch_file", "run_python"]
    if role in ("qa", "test", "qa_engineer", "build_tester"):
        base += ["run_python", "run_pytest"]
    if role in ("architect", "system_architect", "build_architect"):
        # Architect can read but not write code; still gets python eval for spec checks
        base += ["run_python"]

    return [t for t in TOOL_SCHEMA if t["function"]["name"] in base]
