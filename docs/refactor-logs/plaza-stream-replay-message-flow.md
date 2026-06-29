<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T03:00:25Z" -->

# Plaza Stream Replay Message Flow Refactor

## Files Changed

- `src/backend/agents/plaza_routes.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-stream-replay-message-flow-before.md`
- `docs/refactor-logs/plaza-stream-replay-message-flow.md`

## Reason For Changes

- Moved historical SSE message replay generation into `_iter_replay_message_events`.
- Added focused coverage for received-message skipping and replay of negative/current sequence messages.

## Behavior Preservation Notes

- `stream_discussion` still runs replay before status emission.
- Skip condition and payload shape are unchanged.
- Status, closed-discussion, live event, heartbeat, and cleanup logic are unchanged.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_iter_replay_message_events_skips_received_non_negative_seq src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_parse_last_event_id_matches_existing_digit_only_behavior` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `stream_discussion` still has inline status, closed-discussion, live event, and cleanup logic.
