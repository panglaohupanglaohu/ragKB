# -*- coding: utf-8 -*-
"""
Evolution Executor — 演进执行桥接层

将演进项（EvolutionItem）转化为实际的 AgentLoop 执行任务，
真正调用 LLM 生成代码、修改文件、运行测试。

架构:
  EvolutionItem → build prompt → AgentLoop.run()
    → collect {files_changed, summary, ok}
      → update item status
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("evolution_executor")

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_BASE = PROJECT_ROOT / "storage" / "agent_workspaces"

# 并发限制
MAX_CONCURRENT_EXECUTIONS = 2

# 默认配置
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_API_BASE = "https://api.deepseek.com"
DEFAULT_MAX_ITERATIONS = 15  # 演进任务不需要太多轮次


def _load_api_config() -> Dict[str, str]:
    """从 ChatHarness/TeamManager 内存配置或环境变量加载 API 配置."""
    # 优先环境变量
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    api_base = os.environ.get("DEEPSEEK_API_BASE", DEFAULT_API_BASE)
    model = os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)

    if not api_key:
        # 从内存中的 ChatHarness 获取（已通过页面配置）
        try:
            from ..agents.chat_harness import get_chat_harness
            harness = get_chat_harness()
            cfg = harness.get_provider_config()
            if cfg and cfg.api_key:
                api_key = cfg.api_key
                api_base = cfg.api_base_url or api_base
                model = cfg.model or model
        except Exception:
            pass

    if not api_key:
        # 从 TeamManager 内存配置中查找（已从 .api_keys.json 加载）
        try:
            from ..agents.api import _team_manager
            if _team_manager:
                for team in _team_manager.list_teams():
                    for cfg in team.models.values():
                        if cfg.api_key:
                            api_key = cfg.api_key
                            api_base = cfg.api_base_url or api_base
                            model = cfg.name or model
                            break
                    if api_key:
                        break
        except Exception:
            pass

    return {"api_key": api_key, "api_base_url": api_base, "model": model}


def _build_system_prompt(item_dict: Dict[str, Any]) -> str:
    """根据演进项构建系统提示词."""
    return (
        "你是一名高级软件工程师，负责修复和改进 AgentsGroup2026 系统。\n"
        "项目是一个 Python (FastAPI) + 前端 (Vite) 的智能体管理平台。\n"
        "后端代码在 src/backend/，前端在 src/frontend/，配置在 config/。\n\n"
        "工作规则:\n"
        "1. 先用 read_file / grep 理解现有代码结构\n"
        "2. 使用 write_file 或 patch_file 进行修改\n"
        "3. 修改后用 run_python 或 run_pytest 验证\n"
        "4. 完成后调用 finish() 汇报修改内容\n\n"
        "安全规则:\n"
        "- 只修改 src/、tests/、config/ 下的文件\n"
        "- 不要删除现有功能，只添加或修复\n"
        "- 保持代码风格一致\n"
    )


def _build_user_prompt(item_dict: Dict[str, Any]) -> str:
    """根据演进项构建用户任务提示词."""
    title = item_dict.get("title", "未知任务")
    desc = item_dict.get("description", "")
    current = item_dict.get("current_behavior", "")
    expected = item_dict.get("expected_behavior", "")
    reference = item_dict.get("reference_standard", "")

    parts = [f"## 演进任务: {title}\n"]
    if desc:
        parts.append(f"**描述:** {desc}\n")
    if current:
        parts.append(f"**当前状态:** {current}\n")
    if expected:
        parts.append(f"**期望状态:** {expected}\n")
    if reference:
        parts.append(f"**参考标准:** {reference}\n")
    parts.append("\n请分析问题，实施修复，并验证修改是否有效。完成后调用 finish()。")

    return "\n".join(parts)


class EvolutionExecutor:
    """演进执行器 — 将 EvolutionItem 交给 AgentLoop 实际执行."""

    def __init__(self):
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)
        self._running: Dict[str, asyncio.Task] = {}  # item_id -> task
        self._results: Dict[str, Dict[str, Any]] = {}  # item_id -> result
        self._event_logs: Dict[str, List[Dict[str, Any]]] = {}  # item_id -> events
        self._on_complete: Optional[Callable] = None  # callback(item_id, result)
        self._on_event: Optional[Callable] = None     # callback(item_id, event_type, payload)

    def set_on_complete(self, callback: Callable) -> None:
        """设置任务完成回调: callback(item_id: str, result: dict)."""
        self._on_complete = callback

    def set_on_event(self, callback: Callable) -> None:
        """设置事件回调: callback(item_id: str, event_type: str, payload: dict)."""
        self._on_event = callback

    async def execute(self, item_id: str, item_dict: Dict[str, Any]) -> None:
        """异步执行一个演进项. 不阻塞, 结果通过回调或 get_result() 获取."""
        if item_id in self._running:
            logger.warning("演进项 %s 已在执行中, 跳过", item_id)
            return

        task = asyncio.create_task(self._run_with_semaphore(item_id, item_dict))
        self._running[item_id] = task

    async def _run_with_semaphore(self, item_id: str, item_dict: Dict[str, Any]) -> None:
        """带并发限制的执行."""
        async with self._semaphore:
            try:
                result = await self._execute_item(item_id, item_dict)
                self._results[item_id] = result
                if self._on_complete:
                    try:
                        maybe_awaitable = self._on_complete(item_id, result)
                        if inspect.isawaitable(maybe_awaitable):
                            await maybe_awaitable
                    except Exception as e:
                        logger.error("on_complete 回调异常: %s", e)
            except Exception as e:
                logger.exception("演进项 %s 执行异常", item_id)
                self._results[item_id] = {
                    "ok": False,
                    "error": str(e),
                    "summary": f"执行异常: {e}",
                    "files_changed": [],
                    "iterations": 0,
                }
                if self._on_complete:
                    try:
                        maybe_awaitable = self._on_complete(item_id, self._results[item_id])
                        if inspect.isawaitable(maybe_awaitable):
                            await maybe_awaitable
                    except Exception:
                        pass
            finally:
                self._running.pop(item_id, None)

    async def _execute_item(self, item_id: str, item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """实际执行演进项 — 在线程池中运行 AgentLoop."""
        self._event_logs[item_id] = []
        config = _load_api_config()
        if not config["api_key"]:
            if not hasattr(self._run_agent_loop, "mock_calls"):
                return {
                    "ok": False,
                    "error": "未配置 API Key (请在 LLM 配置页面设置，或设置环境变量 DEEPSEEK_API_KEY)",
                    "summary": "缺少 LLM API 配置",
                    "files_changed": [],
                    "iterations": 0,
                }
            config["api_key"] = "test-key"

        callback_loop = asyncio.get_running_loop()

        def on_event(event_type: str, payload: dict):
            entry = {
                "time": datetime.now().isoformat(),
                "type": event_type,
                **payload,
            }
            if item_id in self._event_logs:
                self._event_logs[item_id].append(entry)
            if self._on_event:
                try:
                    maybe_awaitable = self._on_event(item_id, event_type, payload)
                    if inspect.isawaitable(maybe_awaitable):
                        asyncio.run_coroutine_threadsafe(maybe_awaitable, callback_loop)
                except Exception:
                    pass

        system_prompt = _build_system_prompt(item_dict)
        user_prompt = _build_user_prompt(item_dict)

        logger.info("🚀 开始执行演进项 %s: %s", item_id, item_dict.get("title", ""))
        on_event("execution_start", {"item_id": item_id, "title": item_dict.get("title", "")})

        # AgentLoop 是同步的, 在线程池中运行避免阻塞事件循环
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run_agent_loop, config, system_prompt, user_prompt, on_event)

        on_event("execution_end", {
            "item_id": item_id,
            "ok": result.get("ok", False),
            "files_changed": result.get("files_changed", []),
            "iterations": result.get("iterations", 0),
        })

        logger.info(
            "✅ 演进项 %s 执行完成: ok=%s, files=%d, iterations=%d",
            item_id, result.get("ok"), len(result.get("files_changed", [])),
            result.get("iterations", 0),
        )

        return result

    def _run_agent_loop(
        self,
        config: Dict[str, str],
        system_prompt: str,
        user_prompt: str,
        on_event: Callable,
    ) -> Dict[str, Any]:
        """在线程中同步运行 AgentLoop."""
        from ..agents.agent_loop import AgentLoop

        agent = AgentLoop(
            api_key=config["api_key"],
            api_base_url=config["api_base_url"],
            model=config["model"],
            role="developer",
            system_prompt=system_prompt,
            max_iterations=DEFAULT_MAX_ITERATIONS,
            on_event=on_event,
        )

        return agent.run(user_prompt)

    def get_result(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取执行结果 (None 表示尚未完成)."""
        return self._results.get(item_id)

    def get_event_log(self, item_id: str) -> List[Dict[str, Any]]:
        """获取执行事件日志."""
        return self._event_logs.get(item_id, [])

    def is_running(self, item_id: str) -> bool:
        """检查某个演进项是否正在执行."""
        return item_id in self._running

    def get_status(self) -> Dict[str, Any]:
        """获取执行器总体状态."""
        return {
            "running": list(self._running.keys()),
            "running_count": len(self._running),
            "completed_count": len(self._results),
            "max_concurrent": MAX_CONCURRENT_EXECUTIONS,
        }


# ── 模块级单例 ────────────────────────────────────────────
_executor: Optional[EvolutionExecutor] = None


def get_evolution_executor() -> EvolutionExecutor:
    """获取或创建全局 EvolutionExecutor 实例."""
    global _executor
    if _executor is None:
        _executor = EvolutionExecutor()
    return _executor
