# -*- coding: utf-8 -*-
"""Lightweight Python / pytest sandbox for local development.

This is not a full OS-level sandbox. It provides three practical guards:
1. AST validation for obviously dangerous user code
2. Runtime monkeypatching to block common file/network/process escape hatches
3. Resource and timeout limits via subprocess execution
"""

from __future__ import annotations

import ast
import json
import logging
import os
import shlex
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SandboxResult:
    ok: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    elapsed_sec: float = 0.0
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "ok": self.ok,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "elapsed_sec": round(self.elapsed_sec, 2),
        }
        if self.error:
            data["error"] = self.error
        return data


class LiteSandbox:
    """Subprocess-based sandbox with conservative static and runtime guards."""

    BLOCKED_IMPORT_PREFIXES = (
        "socket",
        "subprocess",
        "multiprocessing",
        "requests",
        "httpx",
        "aiohttp",
        "ftplib",
        "telnetlib",
    )
    BLOCKED_CALLS = {
        ("os", "system"),
        ("os", "popen"),
        ("os", "remove"),
        ("os", "unlink"),
        ("os", "replace"),
        ("os", "rename"),
        ("shutil", "rmtree"),
        ("subprocess", "run"),
        ("subprocess", "Popen"),
        ("subprocess", "call"),
        ("subprocess", "check_call"),
        ("subprocess", "check_output"),
        ("socket", "socket"),
        ("socket", "create_connection"),
    }
    BLOCKED_NAMES = {"__import__", "eval", "exec", "compile", "breakpoint"}
    ALLOWED_PYTEST_FLAGS = {"--co"}

    def __init__(
        self,
        *,
        python_executable: Optional[str] = None,
        max_output_bytes: int = 32 * 1024,
        memory_limit_mb: int = 256,
        file_size_limit_kb: int = 512,
        network_enabled: bool = False,
    ) -> None:
        self.python_executable = python_executable or sys.executable or "python3"
        self.max_output_bytes = max_output_bytes
        self.memory_limit_mb = memory_limit_mb
        self.file_size_limit_kb = file_size_limit_kb
        self.network_enabled = network_enabled

    def run_python(self, code: str, *, cwd: Path, timeout: int = 30) -> SandboxResult:
        try:
            self._validate_python_code(code)
        except Exception as exc:
            return SandboxResult(ok=False, error=str(exc))

        wrapper = self._build_wrapper(code, cwd)
        return self._run_subprocess([self.python_executable, "-c", wrapper], cwd=cwd, timeout=timeout)

    def run_pytest(self, target: str = "", *, cwd: Path, timeout: int = 120) -> SandboxResult:
        try:
            extra_args = self._normalize_pytest_target(target)
        except Exception as exc:
            return SandboxResult(ok=False, error=str(exc))

        args = [
            self.python_executable,
            "-m",
            "pytest",
            "-q",
            "--tb=short",
            "--maxfail=5",
            *extra_args,
        ]
        return self._run_subprocess(args, cwd=cwd, timeout=timeout)

    def _run_subprocess(self, cmd: List[str], *, cwd: Path, timeout: int) -> SandboxResult:
        start = time.time()
        env = {
            **os.environ,
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONUNBUFFERED": "1",
        }
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            elapsed = time.time() - start
            stdout = self._truncate(proc.stdout or "")
            stderr = self._truncate(proc.stderr or "")
            return SandboxResult(
                ok=True,
                exit_code=proc.returncode,
                stdout=stdout,
                stderr=stderr,
                elapsed_sec=elapsed,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(ok=False, error=f"timeout after {timeout}s", elapsed_sec=time.time() - start)
        except Exception as exc:
            return SandboxResult(ok=False, error=str(exc), elapsed_sec=time.time() - start)

    def _truncate(self, text: str) -> str:
        if len(text) <= self.max_output_bytes:
            return text
        return "…(truncated)\n" + text[-self.max_output_bytes :]

    def _validate_python_code(self, code: str) -> None:
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._check_import_name(alias.name)
            elif isinstance(node, ast.ImportFrom):
                self._check_import_name(node.module or "")
            elif isinstance(node, ast.Call):
                full_name = self._resolve_call_name(node.func)
                if full_name and full_name in self.BLOCKED_CALLS:
                    raise PermissionError(f"blocked dangerous call: {full_name[0]}.{full_name[1]}")
                if isinstance(node.func, ast.Name) and node.func.id in self.BLOCKED_NAMES:
                    raise PermissionError(f"blocked dangerous builtin: {node.func.id}")
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                        mode = str(node.args[1].value)
                        if any(flag in mode for flag in ("w", "a", "x", "+")):
                            raise PermissionError("sandbox blocks file writes")

    def _check_import_name(self, module_name: str) -> None:
        normalized = (module_name or "").strip()
        for prefix in self.BLOCKED_IMPORT_PREFIXES:
            if normalized == prefix or normalized.startswith(prefix + "."):
                raise PermissionError(f"blocked dangerous import: {normalized}")

    def _resolve_call_name(self, func: ast.AST) -> Optional[tuple[str, str]]:
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return func.value.id, func.attr
        return None

    def _normalize_pytest_target(self, target: str) -> List[str]:
        target = (target or "").strip()
        if not target:
            return []

        tokens = shlex.split(target)
        normalized: List[str] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == "-k":
                if i + 1 >= len(tokens):
                    raise ValueError("pytest target '-k' requires an expression")
                normalized.extend([token, tokens[i + 1]])
                i += 2
                continue

            if token.startswith("-"):
                if token not in self.ALLOWED_PYTEST_FLAGS:
                    raise PermissionError(f"blocked pytest flag: {token}")
                normalized.append(token)
                i += 1
                continue

            if token.startswith("../") or token.startswith("/") or "/../" in token:
                raise PermissionError(f"blocked pytest target path: {token}")
            if token.endswith(".py") or "::" in token:
                normalized.append(token)
            else:
                normalized.extend(["-k", token])
            i += 1

        return normalized

    def _build_wrapper(self, code: str, cwd: Path) -> str:
        blocked_import_prefixes = json.dumps(list(self.BLOCKED_IMPORT_PREFIXES))
        return textwrap.dedent(
            f"""
            import builtins
            import os
            import pathlib
            import resource
            import socket
            import subprocess
            import sys
            import traceback

            _BLOCKED_IMPORT_PREFIXES = {blocked_import_prefixes}
            _USER_CODE = {code!r}
            _CWD = {str(cwd)!r}
            _MEMORY_LIMIT = {int(self.memory_limit_mb)} * 1024 * 1024
            _FILE_LIMIT = {int(self.file_size_limit_kb)} * 1024
            _NETWORK_ENABLED = {bool(self.network_enabled)!r}

            os.chdir(_CWD)
            sys.path.insert(0, _CWD)

            try:
                resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
            except Exception:
                pass
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (_FILE_LIMIT, _FILE_LIMIT))
            except Exception:
                pass
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
            except Exception:
                pass
            try:
                if hasattr(resource, "RLIMIT_AS"):
                    resource.setrlimit(resource.RLIMIT_AS, (_MEMORY_LIMIT, _MEMORY_LIMIT))
            except Exception:
                pass

            def _blocked(message):
                raise PermissionError(message)

            _original_open = builtins.open
            def _safe_open(file, mode="r", *args, **kwargs):
                if any(flag in str(mode) for flag in ("w", "a", "x", "+")):
                    _blocked("sandbox blocks file writes")
                return _original_open(file, mode, *args, **kwargs)
            builtins.open = _safe_open

            _original_import = builtins.__import__
            def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
                for prefix in _BLOCKED_IMPORT_PREFIXES:
                    if name == prefix or name.startswith(prefix + "."):
                        # 已在 sys.modules 中的模块(如被本沙箱中和过的 subprocess)允许透传，
                        # 否则 stdlib 传递依赖(platform→subprocess、uuid→platform)会被误杀；
                        # 用户代码的显式危险导入仍由 AST 静态检查拦截。
                        if name in sys.modules:
                            break
                        _blocked(f"blocked dangerous import: {{name}}")
                return _original_import(name, globals, locals, fromlist, level)
            builtins.__import__ = _safe_import

            os.system = lambda *a, **k: _blocked("blocked os.system")
            os.popen = lambda *a, **k: _blocked("blocked os.popen")
            os.remove = lambda *a, **k: _blocked("blocked os.remove")
            os.unlink = lambda *a, **k: _blocked("blocked os.unlink")
            os.rename = lambda *a, **k: _blocked("blocked os.rename")
            os.replace = lambda *a, **k: _blocked("blocked os.replace")

            subprocess.Popen = lambda *a, **k: _blocked("blocked subprocess.Popen")
            subprocess.run = lambda *a, **k: _blocked("blocked subprocess.run")
            subprocess.call = lambda *a, **k: _blocked("blocked subprocess.call")
            subprocess.check_call = lambda *a, **k: _blocked("blocked subprocess.check_call")
            subprocess.check_output = lambda *a, **k: _blocked("blocked subprocess.check_output")

            if not _NETWORK_ENABLED:
                socket.socket = lambda *a, **k: _blocked("blocked socket.socket")
                socket.create_connection = lambda *a, **k: _blocked("blocked socket.create_connection")

            pathlib.Path.write_text = lambda *a, **k: _blocked("blocked Path.write_text")
            pathlib.Path.write_bytes = lambda *a, **k: _blocked("blocked Path.write_bytes")
            pathlib.Path.unlink = lambda *a, **k: _blocked("blocked Path.unlink")
            pathlib.Path.rename = lambda *a, **k: _blocked("blocked Path.rename")
            pathlib.Path.replace = lambda *a, **k: _blocked("blocked Path.replace")
            pathlib.Path.mkdir = lambda *a, **k: _blocked("blocked Path.mkdir")
            pathlib.Path.rmdir = lambda *a, **k: _blocked("blocked Path.rmdir")
            pathlib.Path.touch = lambda *a, **k: _blocked("blocked Path.touch")

            namespace = {{"__name__": "__main__"}}
            try:
                exec(compile(_USER_CODE, "<sandbox>", "exec"), namespace, namespace)
            except BaseException:
                traceback.print_exc()
                sys.exit(1)
            """
        ).strip()
