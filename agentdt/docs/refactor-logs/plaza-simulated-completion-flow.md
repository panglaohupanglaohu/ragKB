<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:46:18Z" -->

# Plaza Simulated Completion Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-simulated-completion-flow-before.md`
- `docs/refactor-logs/plaza-simulated-completion-flow.md`

## Reason For Changes

- Moved simulated summary, plan payload, closed status, and final broadcasts into `_complete_simulated_discussion`.
- Added focused coverage for actionable summary, conclusions, plan metadata, closed status, and event order.

## Behavior Preservation Notes

- Simulated message publication and round looping are unchanged.
- Summary and plan reasons are unchanged.
- `plan_updated` still broadcasts before `discussion_end`.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_complete_simulated_discussion_updates_plan_and_end_events src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_simulated_round_message_uses_fallback_content_and_broadcasts src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_simulated_opening_appends_moderator_message_and_broadcasts` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `_run_simulated` still owns round loop control and sleep timing.
