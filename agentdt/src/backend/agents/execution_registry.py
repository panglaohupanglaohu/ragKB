# -*- coding: utf-8 -*-
"""AgentsGroup2026 Execution Registry — Unified command/tool routing & execution.

Mirrors claw-code-parity execution_registry.py + runtime.py + tool_pool.py:
- ExecutionRegistry: Centralized command & tool dispatcher
- ToolPool: Assembled subset with permission context
- ToolPermissionContext: deny_names + deny_prefixes for safety
- PortRuntime: route_prompt → bootstrap_session → run_turn_loop
- HistoryLog: Session event tracking
- RoutedMatch: Scored prompt-to-tool/command mapping
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .session_store import TranscriptStore


# ── Permission Context ────────────────────────────────────────


@dataclass(frozen=True)
class ToolPermissionContext:
    """Permission gating for tool access — Clawith / claw-code style.

    deny_names: exact tool names to block
    deny_prefixes: name prefixes to block (e.g. "run_" blocks run_shell, run_python)
    """

    deny_names: frozenset = field(default_factory=frozenset)
    deny_prefixes: tuple = ()

    @classmethod
    def from_lists(
        cls,
        deny_names: Optional[List[str]] = None,
        deny_prefixes: Optional[List[str]] = None,
    ) -> "ToolPermissionContext":
        return cls(
            deny_names=frozenset(n.lower() for n in (deny_names or [])),
            deny_prefixes=tuple(p.lower() for p in (deny_prefixes or [])),
        )

    def blocks(self, tool_name: str) -> bool:
        lowered = tool_name.lower()
        if lowered in self.deny_names:
            return True
        return any(lowered.startswith(p) for p in self.deny_prefixes)


# ── Permission Denial ─────────────────────────────────────────


@dataclass(frozen=True)
class PermissionDenial:
    """Record of a denied tool invocation."""
    tool_name: str
    reason: str


# ── Routed Match ──────────────────────────────────────────────


@dataclass(frozen=True)
class RoutedMatch:
    """A prompt → tool/command match with relevance score."""
    kind: str       # "tool" or "command"
    name: str       # tool/command name
    source_hint: str  # category or source module
    score: int      # match relevance (higher = better)


# ── History Log ───────────────────────────────────────────────


@dataclass(frozen=True)
class HistoryEvent:
    """A single event in the session history."""
    title: str
    detail: str
    timestamp: float = 0.0


@dataclass
class HistoryLog:
    """Ordered log of session events — mirrors claw-code HistoryLog."""

    events: List[HistoryEvent] = field(default_factory=list)

    def add(self, title: str, detail: str) -> None:
        self.events.append(HistoryEvent(
            title=title, detail=detail, timestamp=time.time()
        ))

    def as_markdown(self) -> str:
        lines = ["# Session History", ""]
        lines.extend(
            f"- {e.title}: {e.detail}" for e in self.events
        )
        return "\n".join(lines)

    def to_list(self) -> List[Dict[str, Any]]:
        return [
            {"title": e.title, "detail": e.detail, "timestamp": e.timestamp}
            for e in self.events
        ]


# ── Tool Pool ─────────────────────────────────────────────────


@dataclass
class ToolPool:
    """Assembled subset of tools with permission filtering.

    Mirrors claw-code-parity ToolPool — a frozen snapshot of available
    tools for a single session/invocation.
    """

    tool_names: List[str] = field(default_factory=list)
    tool_count: int = 0
    simple_mode: bool = False
    include_mcp: bool = True
    permission_context: Optional[ToolPermissionContext] = None

    def as_markdown(self) -> str:
        lines = [
            "# Tool Pool",
            "",
            f"Simple mode: {self.simple_mode}",
            f"Include MCP: {self.include_mcp}",
            f"Tool count: {self.tool_count}",
            "",
        ]
        lines.extend(f"- {name}" for name in self.tool_names[:30])
        if self.tool_count > 30:
            lines.append(f"... and {self.tool_count - 30} more")
        return "\n".join(lines)


def assemble_tool_pool(
    simple_mode: bool = False,
    include_mcp: bool = True,
    permission_context: Optional[ToolPermissionContext] = None,
    all_tool_names: Optional[List[str]] = None,
) -> ToolPool:
    """Assemble a ToolPool from available tools with permission filtering."""
    from .tool_registry import ToolRegistry

    registry = ToolRegistry()
    registry.load_defaults()

    names = all_tool_names or [t.name for t in registry.list_enabled()]

    if simple_mode:
        # Simple mode: only core tools
        core = {"read_file", "write_file", "run_shell", "run_python", "web_search"}
        names = [n for n in names if n in core]

    if not include_mcp:
        names = [n for n in names if "mcp" not in n.lower()]

    if permission_context:
        names = [n for n in names if not permission_context.blocks(n)]

    return ToolPool(
        tool_names=names,
        tool_count=len(names),
        simple_mode=simple_mode,
        include_mcp=include_mcp,
        permission_context=permission_context,
    )


# ── Execution Registry ───────────────────────────────────────


@dataclass(frozen=True)
class ExecutionResult:
    """Result of executing a mirrored command or tool."""
    name: str
    kind: str       # "command" or "tool"
    handled: bool
    output: str
    error: str = ""
    duration_ms: float = 0.0


class ExecutionRegistry:
    """Centralized registry that dispatches tool/command execution.

    Mirrors claw-code-parity ExecutionRegistry — provides a unified
    execute interface for both commands and tools.
    """

    def __init__(self) -> None:
        self._tool_names: List[str] = []
        self._command_names: List[str] = []

    def load_from_registry(self) -> None:
        """Populate from the ToolRegistry defaults."""
        from .tool_registry import ToolRegistry

        registry = ToolRegistry()
        registry.load_defaults()
        self._tool_names = [t.name for t in registry.list_all()]
        # Commands are agent-framework level actions
        self._command_names = [
            "help", "status", "config", "clear", "history",
            "plan", "execute", "search", "delegate", "report",
            "test", "deploy", "monitor", "analyze", "export",
        ]

    def tool(self, name: str) -> Optional[str]:
        """Check if a tool exists by name."""
        lowered = name.lower()
        for t in self._tool_names:
            if t.lower() == lowered:
                return t
        return None

    def command(self, name: str) -> Optional[str]:
        """Check if a command exists by name."""
        lowered = name.lower()
        for c in self._command_names:
            if c.lower() == lowered:
                return c
        return None

    async def execute_tool(
        self,
        name: str,
        args: Optional[Dict[str, Any]] = None,
        agent_id: str = "",
        permission_context: Optional[ToolPermissionContext] = None,
    ) -> ExecutionResult:
        """Execute a tool via the ToolExecutor."""
        from .tool_executor import get_tool_executor

        t0 = time.monotonic()
        executor = get_tool_executor()
        result = await executor.execute(
            name,
            args or {},
            agent_id=agent_id,
            permission_context=permission_context,
        )
        elapsed = (time.monotonic() - t0) * 1000

        return ExecutionResult(
            name=name,
            kind="tool",
            handled=result.success,
            output=result.output,
            error=result.error,
            duration_ms=elapsed,
        )

    def execute_command(self, name: str, prompt: str = "") -> ExecutionResult:
        """Execute a built-in command (synchronous)."""
        cmd = self.command(name)
        if not cmd:
            return ExecutionResult(
                name=name,
                kind="command",
                handled=False,
                output="",
                error=f"Unknown command: {name}",
            )
        # Built-in command handlers
        return ExecutionResult(
            name=cmd,
            kind="command",
            handled=True,
            output=f"Command '{cmd}' executed for prompt: {prompt[:200]}",
        )


def build_execution_registry() -> ExecutionRegistry:
    """Build and return a populated ExecutionRegistry."""
    registry = ExecutionRegistry()
    registry.load_from_registry()
    return registry


# ── Port Runtime ──────────────────────────────────────────────


@dataclass
class RuntimeSession:
    """Full session snapshot from a runtime bootstrap.

    Mirrors claw-code-parity RuntimeSession — captures the complete
    state of a single interaction cycle.
    """

    prompt: str = ""
    history: HistoryLog = field(default_factory=HistoryLog)
    routed_matches: List[RoutedMatch] = field(default_factory=list)
    tool_pool: Optional[ToolPool] = None
    tool_results: List[ExecutionResult] = field(default_factory=list)
    command_results: List[ExecutionResult] = field(default_factory=list)
    permission_denials: List[PermissionDenial] = field(default_factory=list)
    transcript: TranscriptStore = field(default_factory=TranscriptStore)

    def as_markdown(self) -> str:
        lines = [
            "# Runtime Session",
            "",
            f"Prompt: {self.prompt}",
            "",
            "## Routed Matches",
        ]
        if self.routed_matches:
            lines.extend(
                f"- [{m.kind}] {m.name} (score={m.score}) — {m.source_hint}"
                for m in self.routed_matches
            )
        else:
            lines.append("- none")

        if self.tool_pool:
            lines.extend(["", self.tool_pool.as_markdown()])

        lines.extend(["", "## Tool Results"])
        for r in self.tool_results:
            status = "✅" if r.handled else "❌"
            lines.append(f"- {status} {r.name}: {r.output[:200]}")

        lines.extend(["", "## Command Results"])
        for r in self.command_results:
            lines.append(f"- {r.name}: {r.output[:200]}")

        if self.permission_denials:
            lines.extend(["", "## Permission Denials"])
            for d in self.permission_denials:
                lines.append(f"- {d.tool_name}: {d.reason}")

        lines.extend(["", self.history.as_markdown()])
        return "\n".join(lines)


class PortRuntime:
    """Maritime agent runtime — routes prompts, bootstraps sessions, runs turn loops.

    Mirrors claw-code-parity PortRuntime adapted for maritime CPS domain.
    """

    def __init__(
        self,
        permission_context: Optional[ToolPermissionContext] = None,
    ) -> None:
        self._permission = permission_context or ToolPermissionContext()
        self._registry = build_execution_registry()

    def route_prompt(
        self,
        prompt: str,
        limit: int = 5,
    ) -> List[RoutedMatch]:
        """Route a prompt to matching tools and commands by keyword scoring."""
        tokens = {
            t.lower()
            for t in prompt.replace("/", " ").replace("-", " ").split()
            if len(t) >= 2
        }

        matches: List[RoutedMatch] = []

        # Score tools
        for tool_name in self._registry._tool_names:
            score = self._score_name(tokens, tool_name)
            if score > 0 and not self._permission.blocks(tool_name):
                matches.append(RoutedMatch(
                    kind="tool",
                    name=tool_name,
                    source_hint="tool_registry",
                    score=score,
                ))

        # Score commands
        for cmd_name in self._registry._command_names:
            score = self._score_name(tokens, cmd_name)
            if score > 0:
                matches.append(RoutedMatch(
                    kind="command",
                    name=cmd_name,
                    source_hint="command_registry",
                    score=score,
                ))

        # Sort by score descending, then by name
        matches.sort(key=lambda m: (-m.score, m.name))
        return matches[:limit]

    async def bootstrap_session(
        self,
        prompt: str,
        limit: int = 5,
    ) -> RuntimeSession:
        """Bootstrap a full session: route → assemble tools → execute matches."""
        history = HistoryLog()
        matches = self.route_prompt(prompt, limit=limit)
        history.add("routing", f"matches={len(matches)} for prompt={prompt[:100]!r}")

        pool = assemble_tool_pool(permission_context=self._permission)
        history.add("tool_pool", f"tools={pool.tool_count}")

        # Execute matched tools
        tool_results: List[ExecutionResult] = []
        command_results: List[ExecutionResult] = []
        denials: List[PermissionDenial] = []

        for match in matches:
            if match.kind == "tool":
                if self._permission.blocks(match.name):
                    denials.append(PermissionDenial(
                        tool_name=match.name,
                        reason="Blocked by permission context",
                    ))
                    continue
                result = await self._registry.execute_tool(
                    match.name,
                    permission_context=self._permission,
                )
                tool_results.append(result)
            elif match.kind == "command":
                result = self._registry.execute_command(match.name, prompt)
                command_results.append(result)

        history.add(
            "execution",
            f"tools={len(tool_results)} commands={len(command_results)} denials={len(denials)}"
        )

        transcript = TranscriptStore()
        transcript.append(prompt)

        return RuntimeSession(
            prompt=prompt,
            history=history,
            routed_matches=matches,
            tool_pool=pool,
            tool_results=tool_results,
            command_results=command_results,
            permission_denials=denials,
            transcript=transcript,
        )

    async def run_turn_loop(
        self,
        prompt: str,
        limit: int = 5,
        max_turns: int = 3,
    ) -> List[RuntimeSession]:
        """Run a multi-turn loop, each turn routing and executing."""
        results: List[RuntimeSession] = []
        for turn in range(max_turns):
            turn_prompt = prompt if turn == 0 else f"{prompt} [turn {turn + 1}]"
            session = await self.bootstrap_session(turn_prompt, limit=limit)
            results.append(session)
            # Stop if no matches found
            if not session.routed_matches:
                break
        return results

    @staticmethod
    def _score_name(tokens: set, name: str) -> int:
        """Score how well a set of tokens matches a tool/command name."""
        # Split name by underscore for multi-word matching
        name_parts = set(name.lower().replace("-", "_").split("_"))
        score = 0
        for token in tokens:
            if token in name_parts:
                score += 2  # exact part match
            elif any(token in part for part in name_parts):
                score += 1  # substring match
        return score


# ── Module exports ────────────────────────────────────────────

__all__ = [
    "ExecutionRegistry",
    "ExecutionResult",
    "HistoryEvent",
    "HistoryLog",
    "PermissionDenial",
    "PortRuntime",
    "RoutedMatch",
    "RuntimeSession",
    "ToolPermissionContext",
    "ToolPool",
    "assemble_tool_pool",
    "build_execution_registry",
]
