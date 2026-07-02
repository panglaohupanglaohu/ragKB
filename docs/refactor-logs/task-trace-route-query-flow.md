<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:56:00Z" -->

# Task Trace Route Query Flow Refactor

## Files Changed

- `src/backend/agents/task_trace.py`
- `src/backend/agents/api.py`
- `docs/refactor-logs/task-trace-route-query-flow-before.md`
- `docs/refactor-logs/task-trace-route-query-flow.md`

## Reason For Changes

- Moved trace route response construction and filtering into `task_trace`.
- Kept `api.py` focused on route definitions, TaskEngine access, and HTTP error handling.

## Behavior Preservation Notes

- `get_task_trace_summary`, `get_task_trace_events`, `get_discussion_trace_summary`, `get_recent_trace_summaries`, `get_recent_trace_events`, and `get_trace_log_tail` keep their payload shapes.
- Export routes continue to call existing route helpers.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 16 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 88 passed.

## Remaining Risks

- `api.py` still owns route-level streaming export functions.
- Historical unsigned `docs/` plan/todos files still block strict docs signoff across the full docs tree.
