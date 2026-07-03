<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:54:57Z" -->

# Plaza Stream SSE Format Flow Refactor

## Files Changed

- `src/backend/agents/plaza_routes.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-stream-sse-format-flow-before.md`
- `docs/refactor-logs/plaza-stream-sse-format-flow.md`

## Reason For Changes

- Moved repeated SSE `id`/`data` frame formatting into `_format_sse_event`.
- Added focused coverage for id-less heartbeat frames, id-bearing frames, and Unicode serialization.

## Behavior Preservation Notes

- `stream_discussion` replay, status, closed-discussion, live event, heartbeat, and cleanup control flow are unchanged.
- JSON serialization still uses `ensure_ascii=False`.
- Event ids still use the same values as before.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_format_sse_event_preserves_optional_id_and_unicode_payload src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_start_discussion_resets_closed_discussion_before_scheduling` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `stream_discussion` still has inline replay/status/closed/live event control flow.
