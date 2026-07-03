<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:47:00Z" -->

# Task Trace Terminal Sync Flow Refactor

## Files Changed

- `src/backend/agents/task_trace.py`
- `src/backend/agents/api.py`
- `docs/refactor-logs/task-trace-terminal-sync-flow-before.md`
- `docs/refactor-logs/task-trace-terminal-sync-flow.md`

## Reason For Changes

- Moved terminal-state calculation into `task_trace.terminal_sync_state`.
- Moved evolution sync argument construction into `task_trace.evolution_sync_kwargs`.
- Kept `api.py` responsible for enum assignment, evolution engine lookup, event emission, broadcast, and persistence.

## Behavior Preservation Notes

- Completed and failed task outcomes keep the same status and error strings.
- `SystemEvolutionChannel.sync_task_outcome` receives the same effective arguments as before.
- Existing private `api.py._finalize_task_terminal_state` remains the compatibility seam.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 16 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 88 passed.

## Remaining Risks

- `api.py` still owns task finalization orchestration and broadcast side effects.
- Historical unsigned `docs/` plan/todos files still block strict docs signoff across the full docs tree.
