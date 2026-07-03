<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:52:03Z" -->

# Plaza Start Discussion Flow Refactor

## Files Changed

- `src/backend/agents/plaza_routes.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-start-discussion-flow-before.md`
- `docs/refactor-logs/plaza-start-discussion-flow.md`

## Reason For Changes

- Separated start-discussion state validation/reset from background task scheduling.
- Added focused coverage for closed discussion reset and background scheduling.

## Behavior Preservation Notes

- Route URL, request shape, response shape, and HTTP errors are unchanged.
- Closed discussion reset still uses `engine.reset_discussion`.
- Background execution still schedules `engine.run_discussion` through `asyncio.create_task`.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_start_discussion_resets_closed_discussion_before_scheduling src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_start_discussion_rejects_non_open_non_closed_state src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_resolve_startable_discussion_resets_closed_state src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_schedule_discussion_run_uses_background_task` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `stream_discussion` still contains inline SSE replay, status, heartbeat, and cleanup logic.
