<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:31:42Z" -->

# Plaza Fallback Abort Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-fallback-abort-flow-before.md`
- `docs/refactor-logs/plaza-fallback-abort-flow.md`

## Reason For Changes

- Separated fallback abort side effects from the nested debate loop.
- Added `_abort_discussion_for_fallback` for logging, message append, broadcast, and max-round truncation.
- Added `_build_fallback_abort_message` for the user-facing abort message payload.
- Added focused coverage for abort message identity, sequence, broadcast payload, and max-round truncation.

## Behavior Preservation Notes

- Fallback threshold and counter logic are unchanged.
- Abort content is unchanged.
- Moderator identity is still used when present.
- The debate loop still breaks after abort handling and proceeds to final summary.
- Final summary, plan generation, closing, persistence, and auto-extract were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_abort_discussion_for_fallback_records_message src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_round_speaker_prompt_uses_recent_context`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- The round loop still owns fallback counter state and nested break control flow.
- Round summary and final summary prompt construction remain inline.
