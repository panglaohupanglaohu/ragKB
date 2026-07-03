<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:05:32Z" -->

# Plaza Interjection Pause State Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-pause-state-flow-before.md`
- `docs/refactor-logs/plaza-interjection-pause-state-flow.md`

## Reason For Changes

- Moved the fixed paused-state broadcast payload out of `handle_live_interjection`.
- Added `_broadcast_interjection_paused` to clarify the beginning of the interjection correction lifecycle.
- Added focused coverage for the stable SSE payload.

## Behavior Preservation Notes

- The helper is still called inside the discussion lock.
- The `interjection_state` payload is unchanged.
- No branch logic, plan update, broadcasts, save, or return shape was changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_broadcast_interjection_paused_uses_stable_payload src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_interjection_plan_update_saves_and_resumes`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `handle_live_interjection` still contains the no-LLM and LLM-backed correction branches.
- Resumed-state broadcast remains in the plan-update helper.
