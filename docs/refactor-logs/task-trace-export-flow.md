<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-07-01T00:10:00Z" -->

# Task Trace Export Flow Refactor

## Files Changed

- `src/backend/agents/task_trace.py`
- `src/backend/agents/api.py`
- `docs/refactor-logs/task-trace-export-flow-before.md`
- `docs/refactor-logs/task-trace-export-flow.md`

## Reason For Changes

- Moved trace NDJSON line generation into `task_trace`.
- Left `api.py` responsible for route parameters and `StreamingResponse`.

## Behavior Preservation Notes

- Combined trace export still emits summary rows before event rows.
- Event-only export still emits raw event payload rows.
- Media type and content-disposition header behavior are unchanged.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 16 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 88 passed.

## Remaining Risks

- `api.py` still owns route-level streaming response setup.
- Historical unsigned `docs/` plan/todos files still block strict docs signoff across the full docs tree.
