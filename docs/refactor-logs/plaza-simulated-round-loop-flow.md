<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:49:02Z" -->

# Plaza Simulated Round Loop Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-simulated-round-loop-flow-before.md`
- `docs/refactor-logs/plaza-simulated-round-loop-flow.md`

## Reason For Changes

- Moved one simulated round's state update, round-start broadcast, speaker publications, and pacing into `_run_simulated_round`.
- Added focused coverage for event order, speaker order, round numbers, and sleep pacing.

## Behavior Preservation Notes

- `_run_simulated` still controls the same round range.
- Opening and completion helpers are unchanged.
- Each speaker still publishes through `_publish_simulated_round_message` and then sleeps for `0.1`.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_run_simulated_round_broadcasts_start_and_speaker_messages src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_simulated_round_message_uses_fallback_content_and_broadcasts src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_complete_simulated_discussion_updates_plan_and_end_events` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.
- `node scripts/check-docs-signoff.cjs --strict` still fails on 27 historical unsigned plan/todos files, not on this slice's new logs.

## Remaining Risks

- `_run_simulated` is now small; next higher-risk work should move to `plaza_routes.py`.
