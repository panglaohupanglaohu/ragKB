# Tool Loop Flow Refactor Log

Last updated: 2026-06-28

## Files Changed

| File | Reason |
| --- | --- |
| `docs/refactor-logs/tool-loop-flow-before.md` | Documented current `run_tool_loop` flow before editing. |
| `src/backend/agents/runtime/tool_loop.py` | Extracted finish handling, JSON argument parsing, changed-file tracking, permission-gated tool dispatch, and tool result message/log construction into private helpers. |
| `src/backend/tests/test_unified_tool_loop.py` | Added regression coverage for finish handling, duplicate file suppression, and invalid finish JSON fallback. |
| `docs/refactor-logs/tool-loop-flow.md` | Recorded behavior preservation notes, validation, and residual risk. |

## Smallest Safe Slice

Only the per-tool-call section inside `run_tool_loop(...)` was refactored.

New private helpers:

- `_parse_json_args(...)`
- `_append_unique(...)`
- `_record_finish_call(...)`
- `_dispatch_runtime_tool(...)`
- `_record_changed_file_from_tool(...)`
- `_append_regular_tool_result(...)`

## Behavior Preservation Notes

- Public functions remain unchanged: `run_tool_loop`, `run_tool_loop_sync`, and `run_tool_loop_sync_with_provider`.
- `ToolLoopResult.to_dict()` output shape is unchanged.
- Event names and payload fields are unchanged.
- `finish` still:
  - parses JSON args when possible,
  - falls back to raw args as summary when JSON is invalid,
  - acknowledges with `{"ok": true, "ack": "finished"}`,
  - returns with `loop_end.reason == "finish_called"`.
- Regular tools still pass the original raw JSON argument string to `dispatch_tool_call(...)`.
- Unknown or denied tools still produce `tool blocked by runtime permissions: {name}`.
- Successful `write_file` and `patch_file` calls still record the `path` argument once.
- Tool result message content remains JSON and capped at 32000 chars.

## Validation Result

Run from repository root on Windows PowerShell:

| Command | Status | Result |
| --- | --- | --- |
| `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_unified_tool_loop.py` | Fail, legacy API slice | `5 passed, 2 failed`; failures are existing `agents.api._run_tool_loop` delegation assertions, outside this runtime slice. |
| `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_unified_tool_loop.py -k "not api_tool_loop_uses_shared_runtime and not runtime_entrypoints_delegate_to_shared_runtimes"` | Pass | `5 passed, 2 deselected`. |
| `npm run lint` | Pass | Python `compileall` completed. |
| `npm run typecheck` | Pass | Current compile-only typecheck baseline completed. |

Full validation was not rerun because `docs/VALIDATION.md` records unrelated existing build/test failures. The relevant runtime subset and compile baseline were run.

## Remaining Risks

- `agents.api._run_tool_loop` still has legacy delegation drift. That is an API-layer core flow and should be handled in a separate slice.
- `run_tool_loop` still owns model turn orchestration, budget checks, usage recording, and result construction. This slice only separated the per-tool-call boundary.
- No request/response formats, database schema, or public APIs were changed.
