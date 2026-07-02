<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-07-01T00:00:00Z" -->

# Plaza Stream Closed Event Flow Refactor

## Files Changed

- `src/backend/agents/plaza_routes.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-stream-closed-event-flow-before.md`
- `docs/refactor-logs/plaza-stream-closed-event-flow.md`

## Reason For Changes

- Moved closed-discussion synthetic SSE event generation into `_iter_closed_discussion_events`.
- Added focused coverage for end-only and plan-before-end sequence behavior.

## Behavior Preservation Notes

- Replay and status emission remain before closed-discussion handling.
- `plan_updated` payload, `discussion_end` payload, and id increments are unchanged.
- Live event, heartbeat, and cleanup control flow are unchanged.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py -q` -> 52 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 88 passed.
- `git diff --check` -> passed with existing CRLF conversion warnings for touched Python files.
- `node scripts/check-docs-signoff.cjs --strict` -> failed on pre-existing unsigned `docs/` plans/todos; new refactor logs were not listed as failures.

## Remaining Risks

- `stream_discussion` still owns the top-level async generator control flow.
- `agents.api` remains a large route module; trace helper seams are restored, but route-level wrappers still live there for compatibility.
