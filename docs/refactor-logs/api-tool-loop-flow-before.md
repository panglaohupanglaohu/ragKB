# API Tool Loop Flow Before Refactor

Last updated: 2026-06-28

## Scope

Core flow: `agents.api._run_tool_loop`.

Files traced:

| File | Role |
| --- | --- |
| `src/backend/agents/api.py` | API-layer session wrapper for tool-loop execution. |
| `src/backend/agents/agent_loop.py` | Legacy compatibility wrapper currently used by `_run_tool_loop`. |
| `src/backend/agents/runtime/tool_loop.py` | Shared runtime that should own model/tool-loop behavior. |
| `src/backend/tests/test_unified_tool_loop.py` | Existing tests covering delegation to the shared runtime. |

## Current Flow

1. `_run_tool_loop(session, prompt, role, ...)` is called by API task/session code.
2. The function appends API/model/role header lines to `session["lines"]`.
3. It defines `on_event(...)`, translating runtime events into human-readable session lines:
   - `loop_start`
   - `model_turn`
   - `tool_call`
   - `tool_result`
   - `loop_end`
   - `error`
4. It builds an API-layer system prompt instructing the agent to inspect files, patch files, run validation, and call `finish`.
5. It constructs `AgentLoop(...)` with raw provider config and the event callback.
6. It calls `loop.run(prompt)`.
7. It copies result fields into `session`:
   - `tool_loop_log`
   - `files_changed`
   - `loop_summary`
   - `loop_ok`
   - `loop_iterations`
8. If result is ok, it appends a success summary and sets:
   - `status = "completed"`
   - `exit_code = 0`
9. If result is not ok, it appends a failure summary and sets:
   - `status = "failed"`
   - `exit_code = 1`
   - `error = result.error`

## Existing Weakness

- `_run_tool_loop` depends on `AgentLoop`, while other callers have migrated to `agents.runtime.run_tool_loop_sync_with_provider`.
- This creates an extra wrapper boundary and caused existing delegation tests to fail.
- The API layer should only translate API session state and events; shared runtime should own tool-loop execution.

## Smallest Safe Refactor Slice

Replace the `AgentLoop` construction and `loop.run(prompt)` call with a direct call to `run_tool_loop_sync_with_provider(...)`.

Do not change:

- `_run_tool_loop` signature.
- Session field names or success/failure semantics.
- System prompt text.
- `on_event` output formatting.
- Runtime provider parameters.
- API request/response contracts.
