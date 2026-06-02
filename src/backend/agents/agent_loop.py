"""Deprecated compatibility shim over the shared tool-loop runtime."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .runtime import run_tool_loop_sync_with_provider

logger = logging.getLogger("AgentLoop")

DEFAULT_MAX_ITERATIONS = 25
DEFAULT_MAX_TOKENS = 65536
DEFAULT_TEMPERATURE = 0.2


class AgentLoop:
    """Thin compatibility wrapper for callers that still import ``AgentLoop``."""

    def __init__(
        self,
        *,
        api_key: str,
        api_base_url: str,
        model: str,
        role: str,
        system_prompt: str,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        on_event: Optional[Any] = None,
    ):
        self.api_key = api_key
        self.api_base_url = api_base_url.rstrip("/")
        self.model = model
        self.role = role
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.on_event = on_event
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        self.files_changed: List[str] = []
        self.summary: str = ""
        self.tool_call_log: List[Dict[str, Any]] = []

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """Run the agent loop via the shared runtime compatibility entrypoint."""
        result = run_tool_loop_sync_with_provider(
            prompt=user_prompt,
            api_key=self.api_key,
            api_base_url=self.api_base_url,
            model=self.model,
            role=self.role,
            system_prompt=self.system_prompt,
            max_iterations=self.max_iterations,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            on_event=self.on_event,
        )
        self.files_changed = list(result.get("files_changed", []))
        self.summary = result.get("summary", "")
        self.tool_call_log = list(result.get("log", []))
        return result
