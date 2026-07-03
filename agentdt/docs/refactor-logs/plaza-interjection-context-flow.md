<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:46:14Z" -->

# Plaza Interjection Context Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-context-flow-before.md`
- `docs/refactor-logs/plaza-interjection-context-flow.md`

## Reason For Changes

- Separated interjection context lookup from the large correction flow.
- Added `_prepare_interjection_context` to centralize plaza, discussion, moderator, and speaker resolution.
- Added focused coverage for successful resolution and missing-moderator error behavior.

## Behavior Preservation Notes

- Existing `ValueError` messages are preserved.
- Moderator and speaker resolution still use existing helpers.
- The discussion lock, simulated branch, LLM branch, plan update, broadcasts, and persistence were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_prepare_interjection_context_resolves_moderator_and_speakers src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_prepare_interjection_context_rejects_missing_moderator`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `handle_live_interjection` still contains large simulated and LLM-backed correction branches.
- Prompt construction for redirect, nominated reply, supplementary replies, and revised plan remains inline.
