# -*- coding: utf-8 -*-
"""AgentsGroup2026 Tool Executor — Actually runs tools when agents invoke them.

Inspired by Clawith's Tools Engine: when the LLM returns a function call
matching a bound tool, this executor dispatches it to the correct handler.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from executing a tool."""
    tool_id: str = ""
    tool_name: str = ""
    success: bool = True
    output: str = ""
    error: str = ""
    execution_ms: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "output": self.output[:4000],
            "error": self.error,
            "execution_ms": self.execution_ms,
            "timestamp": self.timestamp,
        }


class ToolExecutor:
    """Dispatches tool calls to handler functions.

    Each handler receives the tool arguments dict and returns a ToolResult.
    Handlers are registered by tool name.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Any] = {}
        self._history: List[ToolResult] = []
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in tool handlers."""
        self._handlers.update({
            # Browser
            "web_search": self._web_search,
            "navigate_url": self._navigate_url,
            "screenshot": self._screenshot,
            "click_element": self._click_element,
            "fill_form": self._fill_form,
            "extract_content": self._extract_content,
            "web_extract": self._extract_content,
            # Code Execution
            "run_python": self._run_python,
            "run_shell": self._run_shell,
            "run_javascript": self._run_javascript,
            "execute_code": self._execute_code,
            # File Operation
            "read_file": self._read_file,
            "write_file": self._write_file,
            "edit_file": self._edit_file,
            "delete_file": self._delete_file,
            "list_files": self._list_directory,
            "list_directory": self._list_directory,
            "search_files": self._search_files,
            "find_files": self._find_files,
            "read_document": self._read_document,
            # Communication
            "send_message": self._send_message,
            "broadcast": self._broadcast,
            "subscribe_channel": self._subscribe_channel,
            "publish_event": self._publish_event,
            # Maritime
            "ais_query": self._ais_query,
            "ais_vessel_track": self._ais_vessel_track,
            "weather_fetch": self._weather_fetch,
            "weather_marine_forecast": self._weather_fetch,
            "route_calculate": self._route_calculate,
            "colregs_check": self._colregs_check,
            "engine_status": self._engine_status,
            "engine_diagnostic_scan": self._engine_status,
            "engine_monitor": self._engine_monitor,
            "cargo_status": self._cargo_status,
            "chart_ecdis_query": self._chart_query,
            "chart_lookup": self._chart_query,
            # Memory
            "memory_save": self._memory_save,
            "memory_read": self._memory_read,
            "session_search": self._session_search,
            # Skills
            "skill_list": self._skill_list,
            "skill_view": self._skill_view,
            "skill_manage": self._skill_manage,
            # Delegation
            "delegate_task": self._delegate_task,
            "mixture_of_agents": self._mixture_of_agents,
            # Discovery
            "list_agents": self._list_agents,
            "list_capabilities": self._list_capabilities,
            # Digital Twin
            "dt_camera_move": self._dt_camera_move,
            "dt_model_load": self._dt_model_load,
            "dt_model_transform": self._dt_model_transform,
            "dt_material_set": self._dt_material_set,
            "dt_physics_toggle": self._dt_physics_toggle,
            "dt_light_adjust": self._dt_light_adjust,
            "dt_render_mode": self._dt_render_mode,
            "dt_inspection_path": self._dt_inspection_path,
            # Triggers
            "schedule_task": self._schedule_task,
            "set_alarm": self._set_alarm,
            "watch_file": self._watch_file,
            "cron_trigger": self._cron_trigger,
            # Vision
            "vision_analyze": self._vision_analyze,
        })

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any],
        *, agent_id: str = "", requires_approval: bool = False,
    ) -> ToolResult:
        """Execute a tool by name with arguments."""
        handler = self._handlers.get(tool_name)
        if handler is None:
            result = ToolResult(
                tool_name=tool_name, success=False,
                error=f"Unknown tool: {tool_name}",
            )
            self._history.append(result)
            return result

        if requires_approval:
            result = ToolResult(
                tool_name=tool_name, success=False,
                error="Tool requires human approval (not yet approved)",
            )
            self._history.append(result)
            return result

        t0 = time.monotonic()
        try:
            result = await handler(arguments)
            result.tool_name = tool_name
            result.execution_ms = (time.monotonic() - t0) * 1000
        except Exception as exc:
            result = ToolResult(
                tool_name=tool_name, success=False,
                error=str(exc)[:500],
                execution_ms=(time.monotonic() - t0) * 1000,
            )
        self._history.append(result)
        if len(self._history) > 500:
            self._history = self._history[-300:]
        return result

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._history[-limit:]]

    # ═══════════════════════════════════════════════════════════════
    # Browser Handlers
    # ═══════════════════════════════════════════════════════════════

    async def _web_search(self, args: Dict[str, Any]) -> ToolResult:
        query = args.get("query", "")
        max_results = args.get("max_results", 5)
        if not query:
            return ToolResult(success=False, error="query is required")
        try:
            import aiohttp
            import re
            from urllib.parse import quote_plus
        except ImportError:
            return ToolResult(output=f"[web_search] 搜索 \"{query}\" — aiohttp 未安装，无法执行网络搜索")

        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        errors = []

        # Strategy 1: Google (通过本机 proxy 访问)
        try:
            google_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            async with aiohttp.ClientSession() as session:
                async with session.get(google_url, headers=headers, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        results = []
                        # Google result: <h3 ...>title</h3> inside <a href="/url?q=real_url&...">
                        blocks = re.findall(r'<a[^>]*href="/url\?q=(https?://[^&"]+)[^"]*"[^>]*>.*?<h3[^>]*>(.*?)</h3>', text, re.DOTALL)
                        if not blocks:
                            blocks = re.findall(r'<a[^>]*href="(https?://(?!google\.com|accounts\.google)[^"]*)"[^>]*>.*?<h3[^>]*>(.*?)</h3>', text, re.DOTALL)
                        for link, raw_title in blocks[:max_results]:
                            title = re.sub(r'<[^>]+>', '', raw_title).strip()
                            if title and "google.com" not in link:
                                results.append(f"[{len(results)+1}] {title}\n    URL: {link}")
                                if len(results) >= max_results:
                                    break
                        if results:
                            return ToolResult(output=f"搜索 \"{query}\" 结果 (Google):\n\n" + "\n\n".join(results))
        except Exception as e:
            errors.append(f"Google: {str(e)[:80]}")

        # Strategy 2: Sogou (搜狗 — 国内最稳定, 返回标准 h3 结构)
        try:
            sogou_url = f"https://www.sogou.com/web?query={quote_plus(query)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(sogou_url, headers=headers, timeout=aiohttp.ClientTimeout(total=12), ssl=False) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        results = []
                        h3_blocks = re.findall(r'<h3[^>]*>(.*?)</h3>', text, re.DOTALL)
                        for h3 in h3_blocks[:max_results * 2]:
                            title = re.sub(r'<[^>]+>', '', h3).strip()
                            links = re.findall(r'href="([^"]+)"', h3)
                            if title and len(title) > 5 and links:
                                link = links[0]
                                if link.startswith('/'):
                                    link = f"https://www.sogou.com{link}"
                                results.append(f"[{len(results)+1}] {title}\n    URL: {link}")
                                if len(results) >= max_results:
                                    break
                        if results:
                            return ToolResult(output=f"搜索 \"{query}\" 结果 (Sogou):\n\n" + "\n\n".join(results))
        except Exception as e:
            errors.append(f"Sogou: {str(e)[:80]}")

        # Strategy 3: DuckDuckGo Instant Answer JSON API
        try:
            api_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        results = []
                        if data.get("AbstractText"):
                            results.append(f"[1] {data.get('Heading', query)}\n    URL: {data.get('AbstractURL', '')}\n    {data['AbstractText'][:300]}")
                        for topic in data.get("RelatedTopics", [])[:max_results]:
                            if isinstance(topic, dict) and topic.get("Text"):
                                results.append(f"[{len(results)+1}] {topic['Text'][:200]}\n    URL: {topic.get('FirstURL', '')}")
                        if results:
                            return ToolResult(output=f"搜索 \"{query}\" 结果:\n\n" + "\n\n".join(results))
        except Exception as e:
            errors.append(f"DDG: {str(e)[:80]}")

        err_detail = "; ".join(errors) if errors else "所有搜索引擎均不可达"
        return ToolResult(success=False, error=f"Search error: {err_detail}")

    def _html_to_text(self, html: str, max_chars: int = 4000) -> str:
        """Clean HTML to readable text (Clawith jina_read style)."""
        import re
        text = html
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        text = re.sub(r'<(br|hr)[^>]*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</(p|div|li|tr|h[1-6]|blockquote|pre)>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<(p|div|li|tr|h[1-6]|blockquote|pre)[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#\d+;', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... [截断，共 {len(text)} 字符]"
        return text

    async def _navigate_url(self, args: Dict[str, Any]) -> ToolResult:
        """Navigate to URL and extract readable content (like Clawith jina_read)."""
        url = args.get("url", "")
        if not url:
            return ToolResult(success=False, error="url is required")
        if not url.startswith("http"):
            url = "https://" + url
        try:
            import aiohttp, re
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    html = await resp.text()
                    title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()[:200] if title_m else ""
                    max_chars = min(args.get("max_chars", 6000), 10000)
                    text = self._html_to_text(html, max_chars)
                    header = f"📄 **{title}**\nURL: {url} | Status: {resp.status} | Content-Length: {len(html)}\n\n"
                    return ToolResult(output=header + text)
        except Exception as e:
            return ToolResult(success=False, error=str(e)[:300])

    async def _screenshot(self, args: Dict[str, Any]) -> ToolResult:
        """Screenshot — requires browser environment (like Clawith AgentBay)."""
        save = args.get("save_to_workspace", False)
        return ToolResult(
            success=False,
            error=(
                "截图工具需要浏览器环境 (Browser Environment)。\n\n"
                "可选方案:\n"
                "1. 通过数字孪生界面 (Digital Twin) 直接截图\n"
                "2. 使用 extract_content 工具提取网页文本内容\n"
                "3. 使用 navigate_url 工具获取页面源码"
            )
        )

    async def _click_element(self, args: Dict[str, Any]) -> ToolResult:
        """Click element — requires browser environment (like Clawith AgentBay)."""
        selector = args.get("selector", "")
        return ToolResult(
            success=False,
            error=(
                f"点击工具需要浏览器环境。目标: {selector}\n\n"
                "可选方案:\n"
                "1. 使用 navigate_url 直接访问目标链接\n"
                "2. 通过数字孪生界面操作"
            )
        )

    async def _fill_form(self, args: Dict[str, Any]) -> ToolResult:
        """Fill form — requires browser environment (like Clawith AgentBay)."""
        selector = args.get("selector", "")
        value = args.get("value", args.get("text", ""))
        return ToolResult(
            success=False,
            error=(
                f"表单填写工具需要浏览器环境。目标: {selector}, 值: {value[:100]}\n\n"
                "可选方案:\n"
                "1. 使用 run_python 通过 aiohttp/requests 提交表单数据\n"
                "2. 通过数字孪生界面手动操作"
            )
        )

    async def _extract_content(self, args: Dict[str, Any]) -> ToolResult:
        """Extract content from URL (like Clawith jina_read with Markdown output)."""
        url = args.get("url", "")
        selector = args.get("selector", "body")
        fmt = args.get("format", "text")
        max_chars = min(args.get("max_chars", 6000), 15000)
        if url:
            if not url.startswith("http"):
                url = "https://" + url
            try:
                import aiohttp, re
                headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        html = await resp.text()
                        title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                        title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()[:200] if title_m else url
                        # Extract meta description
                        meta_m = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\'>]*)', html, re.IGNORECASE)
                        description = meta_m.group(1).strip()[:300] if meta_m else ""
                        text = self._html_to_text(html, max_chars)
                        parts = [f"📄 **{title}**", f"URL: {url}"]
                        if description:
                            parts.append(f"Description: {description}")
                        parts.append(f"\n{text}")
                        return ToolResult(output="\n".join(parts))
            except Exception as e:
                return ToolResult(success=False, error=str(e)[:300])
        return ToolResult(output=f"[extract_content] 请提供 url 参数。selector={selector}, format={fmt}")

    # ═══════════════════════════════════════════════════════════════
    # Code Execution Handlers
    # ═══════════════════════════════════════════════════════════════

    async def _run_python(self, args: Dict[str, Any]) -> ToolResult:
        code = args.get("code", "")
        timeout = min(args.get("timeout", 30), 60)
        if not code:
            return ToolResult(success=False, error="code is required")
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", "-c", code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out = stdout.decode("utf-8", errors="replace")[:3000]
            err = stderr.decode("utf-8", errors="replace")[:1000]
            if proc.returncode == 0:
                return ToolResult(output=out or "(no output)")
            return ToolResult(success=False, output=out, error=err)
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Python execution timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e)[:300])

    async def _run_shell(self, args: Dict[str, Any]) -> ToolResult:
        command = args.get("command", "")
        cwd = args.get("cwd", "")
        timeout = min(args.get("timeout", 30), 60)
        if not command:
            return ToolResult(success=False, error="command is required")
        # Security: block dangerous commands
        dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/", ":(){ :|:& };:"]
        for d in dangerous:
            if d in command:
                return ToolResult(success=False, error=f"Blocked dangerous command pattern: {d}")
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or None,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out = stdout.decode("utf-8", errors="replace")[:3000]
            err = stderr.decode("utf-8", errors="replace")[:1000]
            if proc.returncode == 0:
                return ToolResult(output=out or "(no output)")
            return ToolResult(success=False, output=out, error=err)
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Shell execution timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e)[:300])

    async def _run_javascript(self, args: Dict[str, Any]) -> ToolResult:
        code = args.get("code", "")
        context = args.get("context", "node")
        if context == "node":
            try:
                proc = await asyncio.create_subprocess_exec(
                    "node", "-e", code,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
                out = stdout.decode("utf-8", errors="replace")[:3000]
                err = stderr.decode("utf-8", errors="replace")[:1000]
                if proc.returncode == 0:
                    return ToolResult(output=out or "(no output)")
                return ToolResult(success=False, output=out, error=err)
            except Exception as e:
                return ToolResult(success=False, error=str(e)[:300])
        return ToolResult(output=f"[run_javascript] Browser context execution requires browser environment")

    async def _execute_code(self, args: Dict[str, Any]) -> ToolResult:
        """Execute code in Python/Bash/Node (like Clawith execute_code)."""
        language = args.get("language", "python")
        code = args.get("code", "")
        timeout = min(int(args.get("timeout", 30)), 60)
        if not code.strip():
            return ToolResult(success=False, error="❌ No code provided")
        if language not in ("python", "bash", "node"):
            return ToolResult(success=False, error=f"❌ Unsupported language: {language}. Use: python, bash, or node")
        # Security check
        dangerous = {
            "python": ["subprocess", "shutil.rmtree", "os.system", "os.popen", "__import__", "importlib"],
            "bash": ["rm -rf /", "rm -rf ~", "sudo ", "mkfs", "dd if=", ":(){ :"],
            "node": ["child_process", "fs.rmSync", "process.exit"],
        }
        code_lower = code.lower()
        for pattern in dangerous.get(language, []):
            if pattern.lower() in code_lower:
                return ToolResult(success=False, error=f"❌ Blocked: unsafe operation ({pattern})")
        # Map language to command
        cmds = {"python": ["python3", "-c", code], "bash": ["bash", "-c", code], "node": ["node", "-e", code]}
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmds[language],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out = stdout.decode("utf-8", errors="replace")[:5000]
            err = stderr.decode("utf-8", errors="replace")[:2000]
            parts = []
            if out.strip():
                parts.append(f"📤 Output:\n{out}")
            if err.strip():
                parts.append(f"⚠️ Stderr:\n{err}")
            if proc.returncode != 0:
                parts.append(f"Exit code: {proc.returncode}")
            if not parts:
                return ToolResult(output="✅ Code executed successfully (no output)")
            return ToolResult(output="\n\n".join(parts))
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"❌ Code execution timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e)[:300])

    # ═══════════════════════════════════════════════════════════════
    # File Operation Handlers
    # ═══════════════════════════════════════════════════════════════

    async def _read_file(self, args: Dict[str, Any]) -> ToolResult:
        """Read file with line numbers and offset/limit (like Clawith)."""
        path = args.get("path", "")
        encoding = args.get("encoding", "utf-8")
        offset = int(args.get("offset", 0))
        limit = int(args.get("limit", 2000))
        if not path:
            return ToolResult(success=False, error="path is required")
        try:
            abs_path = os.path.abspath(path)
            with open(abs_path, encoding=encoding, errors="replace") as f:
                content = f.read(100000)
            lines = content.splitlines()
            total = len(lines)
            start = max(0, offset)
            end = min(total, start + limit)
            if start >= total:
                return ToolResult(output=f"Offset {offset} exceeds file length ({total} lines)")
            numbered = []
            for i, line in enumerate(lines[start:end], start=start):
                numbered.append(f"{i+1:6}\t{line}")
            result = "\n".join(numbered)
            header = f"\U0001f4c4 {path} (lines {start+1}-{end} of {total})\n"
            if total > end:
                result += f"\n\n... [{total - end} more lines, lines {end+1}-{total}]"
            return ToolResult(output=header + result)
        except Exception as e:
            return ToolResult(success=False, error=str(e)[:300])

    async def _write_file(self, args: Dict[str, Any]) -> ToolResult:
        """Write file with directory auto-creation (like Clawith)."""
        path = args.get("path", "")
        content = args.get("content", "")
        mode = args.get("mode", "w")
        if not path:
            return ToolResult(success=False, error="path is required")
        try:
            abs_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            existed = os.path.exists(abs_path)
            with open(abs_path, mode, encoding="utf-8") as f:
                f.write(content)
            action = "✅ Updated" if existed else "✅ Created"
            return ToolResult(output=f"{action} {path} ({len(content)} chars)")
        except Exception as e:
            return ToolResult(success=False, error=str(e)[:300])

    async def _list_directory(self, args: Dict[str, Any]) -> ToolResult:
        """List directory with file sizes (like Clawith list_files)."""
        path = args.get("path", ".")
        recursive = args.get("recursive", False)
        pattern = args.get("pattern", "*")
        try:
            import glob
            abs_path = os.path.abspath(path)
            if not os.path.isdir(abs_path):
                return ToolResult(success=False, error=f"Directory not found: {path}")
            items = []
            dir_count = 0
            file_count = 0
            if recursive:
                entries = sorted(glob.glob(os.path.join(abs_path, "**", pattern), recursive=True))[:200]
            else:
                entries = sorted(glob.glob(os.path.join(abs_path, pattern)))[:200]
            for entry in entries:
                if os.path.basename(entry).startswith("."):
                    continue
                if os.path.isdir(entry):
                    dir_count += 1
                    child_count = len([c for c in os.listdir(entry) if not c.startswith(".")])
                    items.append(f"  \U0001f4c1 {os.path.relpath(entry, abs_path)}/ ({child_count} items)")
                else:
                    file_count += 1
                    try:
                        size = os.path.getsize(entry)
                        size_str = f"{size}B" if size < 1024 else f"{size/1024:.1f}KB"
                    except Exception:
                        size_str = "?"
                    items.append(f"  \U0001f4c4 {os.path.relpath(entry, abs_path)} ({size_str})")
            header = f"\U0001f4c2 {path}: {dir_count} folder(s), {file_count} file(s)\n"
            return ToolResult(output=header + "\n".join(items[:100]))
        except Exception as e:
            return ToolResult(success=False, error=str(e)[:300])

    async def _search_files(self, args: Dict[str, Any]) -> ToolResult:
        """Search files by content regex with line numbers (like Clawith search_files)."""
        pattern = args.get("pattern", "")
        directory = args.get("directory", args.get("path", "."))
        file_pattern = args.get("file_pattern", "*")
        ignore_case = args.get("ignore_case", False)
        if not pattern:
            return ToolResult(success=False, error="pattern is required")
        try:
            import glob, re
            flags = re.IGNORECASE if ignore_case else 0
            regex = re.compile(pattern, flags)
            abs_dir = os.path.abspath(directory)
            files = glob.glob(os.path.join(abs_dir, "**", file_pattern), recursive=True)
            results = []
            files_searched = 0
            skip_exts = {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz"}
            for fp in files:
                if os.path.isdir(fp) or os.path.basename(fp).startswith("."):
                    continue
                if os.path.splitext(fp)[1].lower() in skip_exts:
                    continue
                files_searched += 1
                try:
                    with open(fp, encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                rel = os.path.relpath(fp, abs_dir)
                                results.append(f"{rel}:{i}: {line.strip()[:100]}")
                                if len(results) >= 50:
                                    break
                except Exception:
                    continue
                if len(results) >= 50:
                    break
            if not results:
                return ToolResult(output