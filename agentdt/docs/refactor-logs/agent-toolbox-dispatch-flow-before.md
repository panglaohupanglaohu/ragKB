<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:50:34Z" -->

# Agent Toolbox Dispatch Flow - Before

## Scope

Core flow: `dispatch_tool_call` in `src/backend/agents/agent_toolbox.py`.

## Current Flow

1. Look up the tool name in `_DISPATCH`.
2. Special-case `finish` and return `{"ok": True, "_finished": True}`.
3. Return an unknown-tool error when the name is not registered.
4. Parse `args_json` as JSON, defaulting empty input to `{}`.
5. Call the resolved tool function with parsed keyword arguments.
6. Convert `JSONDecodeError`, `TypeError`, and unexpected exceptions into JSON-safe error dictionaries.
7. Return the tool result directly.

## Existing Boundaries

- Individual `tool_*` functions own filesystem/process behavior.
- `_DISPATCH` maps public tool names to implementations.
- `dispatch_tool_call` owns argument parsing, special commands, error normalization, and final return.

## Behavior To Preserve

- `finish` returns `{"ok": True, "_finished": True}`.
- Unknown tool returns `ok=False`.
- Invalid JSON returns `ok=False` with the same bad-JSON prefix.
- Bad keyword arguments return `ok=False` with the same bad-arguments prefix.
- Tool crashes are logged and returned as `ok=False`.
- Tool implementation behavior is unchanged.

## Smallest Safe Refactor Slice

Extract dispatcher helpers for finish detection, argument parsing, tool invocation, and error payload formatting. Leave all tool implementations untouched.
