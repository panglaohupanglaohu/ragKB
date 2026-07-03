<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:33:22Z" -->

# Plaza Round Summary Prompt Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-round-summary-prompt-flow-before.md`
- `docs/refactor-logs/plaza-round-summary-prompt-flow.md`

## Reason For Changes

- Reduced inline prompt construction in the debate round loop.
- Added `_build_round_summary_prompt` so summary prompt generation can be tested directly.
- Added coverage for round number, round messages, and moderator summary requirements.

## Behavior Preservation Notes

- Final-round summary skipping is unchanged.
- The prompt still uses `_format_round_messages(disc, round_num)`.
- Moderator speaking still delegates to `_speak_with_lock`.
- Fallback handling, final summary, plan generation, closing, persistence, and auto-extract were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_round_summary_prompt_uses_round_messages src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_abort_discussion_for_fallback_records_message`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- The final summary and closing flow remain inline inside `run_discussion`.
- The nested round loop still controls exchange iteration and fallback counter state.
