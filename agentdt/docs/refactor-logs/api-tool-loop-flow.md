# API Tool Loop Flow Refactor Log

Last updated: 2026-06-28

## Files Changed

| File | Reason |
| --- | --- |
| `docs/refactor-logs/api-tool-loop-flow-before.md` | Documented the current API-layer tool-loop flow before editing. |
| `src/backend/agents/api.py` | Replaced the legacy `AgentLoop` wrapper inside `_run_tool_loop` with direct delegation to `run_tool_loop_sync_with_provider(...)`. |
| `docs/refactor-logs/api-tool-loop-flow.md` | Recorded behavior preservation notes, validation, and residual risk. |

## Smallest Safe Slice

Only the execution delegate inside `_run_tool_loop(...)` changed.

Unchanged:

- `_run_tool_loop` function signature.
- Session line formatting.
- `on_event` event-to-line translation.
- System prompt text.
- Session output fields.
- Success/failure status and exit-code handling.

## Behavior Preservation Notes

- API layer still writes:
  - `tool_loop_log`
  - `files_changed`
  - `loop_summary`
  - `loop_ok`
  - `loop_iterations`
  - `status`
  - `exit_code`
  - `error` on failure
- Provider values are passed through unchanged:
  - `api_key`
  - `api_base_url`
  - `model`
  - `max_iterations`
  - `max_tokens`
  - `temperature`
- Runtime event handling remains unchanged.
- Tool-loop execution now shares the same runtime path as `AgentLoop` and `EvolutionExecutor`.

## Validation Result

Run from repository root on Windows PowerShell:

| Command | Status | Result |
| --- | --- | --- |
| `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_unified_tool_loop.py` | Pass | `7 passed`. |
| `npm run lint` | Pass | Python `compileall` completed. |
| `npm run typecheck` | Pass | Current compile-only typecheck baseline completed. |

Full validation was not rerun because `docs/VALIDATION.md` records unrelated existing build/test failures. The relevant API/tool-loop subset and compile baseline were run.

## Remaining Risks

- `_run_tool_loop` still lives inside a large API module. Extracting the API session presenter would be a separate slice.
- No request/response formats, database schema, or public APIs were changed.
