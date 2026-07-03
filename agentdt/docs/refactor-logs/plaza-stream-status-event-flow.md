<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-07-01T00:00:00Z" -->

# Plaza Stream Status Event Flow Refactor

## Files Changed

- `src/backend/agents/plaza_routes.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-stream-status-event-flow-before.md`
- `docs/refactor-logs/plaza-stream-status-event-flow.md`

## Reason For Changes

- Moved status sequence calculation and SSE status event formatting into `_build_stream_status_event`.
- Added focused coverage for empty discussions and next-message sequence behavior.

## Behavior Preservation Notes

- Replay, closed-discussion, live event, heartbeat, and cleanup control flow are unchanged.
- Status event payload and id calculation are unchanged.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py -q` -> 50 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 88 passed.
- `git diff --check` -> passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `stream_discussion` still owns the top-level async generator control flow.
- `agents.api` remains a large route module; trace helper seams are restored, but route-level wrappers still live there for compatibility.
