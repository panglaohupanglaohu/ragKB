<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:44:02Z" -->

# Plaza Simulated Round Message Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-simulated-round-message-flow-before.md`
- `docs/refactor-logs/plaza-simulated-round-message-flow.md`

## Reason For Changes

- Moved simulated speaker fallback content, message construction, append, and broadcast into `_publish_simulated_round_message`.
- Added focused coverage for fallback topic content, speaker metadata, sequence assignment, and broadcast payload.

## Behavior Preservation Notes

- `_run_simulated` still loops over the same speakers and keeps the same sleep after each message.
- Fallback content source and message fields are unchanged.
- Simulated final plan and close remain untouched in this slice.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_simulated_round_message_uses_fallback_content_and_broadcasts src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_simulated_opening_appends_moderator_message_and_broadcasts` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- Simulated final plan and close remain inline.
