<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:38:23Z" -->

# Plaza Final Summary Fallback Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-final-summary-fallback-flow-before.md`
- `docs/refactor-logs/plaza-final-summary-fallback-flow.md`

## Reason For Changes

- Separated deterministic final-summary fallback from `run_discussion`.
- Added `_apply_deterministic_summary_fallback` for summary replacement and default conclusions.
- Added focused coverage for actionable plan output, fallback reason text, plan table contract, and default key conclusions.

## Behavior Preservation Notes

- `_has_actionable_plan` still controls whether fallback runs.
- Deterministic plan generation still receives moderator plus speakers.
- Fallback reason and default key conclusions are unchanged.
- Plan payload, `plan_updated` broadcast, closing, persistence, and auto-extract were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_apply_deterministic_summary_fallback_sets_plan_ready_summary src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_final_summary_prompt_uses_history_and_plan_contract`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Closing message creation and discussion-end broadcast remain inline in `run_discussion`.
- Persistence and auto-extract remain inline after closing.
