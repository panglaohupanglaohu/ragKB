<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:57:28Z" -->

# Plaza Stream Last-Event-ID Flow Refactor

## Files Changed

- `src/backend/agents/plaza_routes.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-stream-last-event-id-flow-before.md`
- `docs/refactor-logs/plaza-stream-last-event-id-flow.md`

## Reason For Changes

- Moved digit-only `Last-Event-ID` parsing into `_parse_last_event_id`.
- Added focused coverage for empty, non-digit, negative-text, and digit-only values.

## Behavior Preservation Notes

- The stream route still reads the same request header.
- Parsing behavior is unchanged from the previous inline `isdigit()` check.
- SSE replay and live streaming control flow are unchanged.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_parse_last_event_id_matches_existing_digit_only_behavior src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_format_sse_event_preserves_optional_id_and_unicode_payload` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `stream_discussion` still has inline replay/status/closed/live event control flow.
