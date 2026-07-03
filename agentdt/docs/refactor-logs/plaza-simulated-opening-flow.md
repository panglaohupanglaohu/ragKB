<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:41:22Z" -->

# Plaza Simulated Opening Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-simulated-opening-flow-before.md`
- `docs/refactor-logs/plaza-simulated-opening-flow.md`

## Reason For Changes

- Moved simulated opening message construction and broadcast into `_publish_simulated_opening`.
- Added focused coverage for message content, moderator metadata, sequence assignment, and broadcast payload.

## Behavior Preservation Notes

- `_run_simulated` still only publishes the opening when a moderator exists.
- Opening text, round number, seq handling, and SSE message event are unchanged.
- Simulated round, plan, close, and save behavior are untouched in this slice.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_simulated_opening_appends_moderator_message_and_broadcasts src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_regenerated_plan_updates_message_broadcast_and_save` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- Simulated round messages and simulated final plan/close remain inline.
