<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:30:04Z" -->

# Plaza Round Speaker Prompt Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-round-speaker-prompt-flow-before.md`
- `docs/refactor-logs/plaza-round-speaker-prompt-flow.md`

## Reason For Changes

- Reduced inline prompt construction inside the nested discussion round loop.
- Added `_build_round_speaker_prompt` so the round loop focuses on orchestration.
- Added focused coverage for topic, optional context, speaker identity, round/exchange numbering, recent context, and speaking constraints.

## Behavior Preservation Notes

- The recent context window remains `limit=5`.
- Optional description and goal text are still included only when present.
- Exchange numbering remains one-based for user-facing prompt text.
- Speaker execution, fallback counting, abort handling, round summaries, final summary, plan generation, and persistence were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_round_speaker_prompt_uses_recent_context src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_run_discussion_opening_uses_moderator_prompt`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `run_discussion` still contains the nested debate loop, fallback abort branch, round summary prompt, final summary, plan, and closing flows.
- Fallback abort behavior is intentionally still inline and should be refactored separately with dedicated tests.
