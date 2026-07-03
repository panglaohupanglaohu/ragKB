<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-07-01T00:00:00Z" -->

# Plaza Stream Helper Module Refactor

## Files Changed

- `src/backend/agents/plaza_stream.py`
- `src/backend/agents/plaza_routes.py`
- `docs/refactor-logs/plaza-stream-helper-module-flow-before.md`
- `docs/refactor-logs/plaza-stream-helper-module-flow.md`

## Reason For Changes

- Reduced `plaza_routes.py` responsibility by moving pure SSE stream helper logic into `plaza_stream.py`.
- Kept underscore-prefixed imports in `plaza_routes.py` so existing focused tests and compatibility seams continue to work.
- Pointed stream helper tests at `plaza_stream.py` directly so the new module boundary has explicit coverage.

## Behavior Preservation Notes

- SSE payload formatting is unchanged.
- Replay, status, closed-discussion synthetic events, live events, heartbeat, and subscribe/unsubscribe behavior are unchanged.
- `stream_discussion` still owns the async generator control flow and HTTP response construction.
- `plaza_routes.py` still re-exports the helper names with leading underscores for compatibility.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py -q` -> 55 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 88 passed.
- `git diff --check` -> passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `stream_discussion` still lives in a large route module.
- The next cleaner split would move route orchestration behind a stream adapter, but that is larger than this slice.
