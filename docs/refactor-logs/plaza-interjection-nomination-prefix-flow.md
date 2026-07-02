<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:10:11Z" -->

# Plaza Interjection Nomination Prefix Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-nomination-prefix-flow-before.md`
- `docs/refactor-logs/plaza-interjection-nomination-prefix-flow.md`

## Reason For Changes

- Moved nomination-prefix normalization out of the LLM-backed interjection branch.
- Added `_ensure_interjection_nomination_prefix` for direct testing.
- Added coverage for missing prefix, existing prefix, and missing chosen speaker.

## Behavior Preservation Notes

- Prefix text is unchanged.
- Existing prefix is still not duplicated.
- No chosen speaker still leaves moderator reply text unchanged.
- Downstream publish, replies, plan update, broadcasts, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_ensure_interjection_nomination_prefix_adds_missing_prefix src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_ensure_interjection_nomination_prefix_keeps_existing_prefix src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_ensure_interjection_nomination_prefix_ignores_missing_choice`: passed, `3 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- LLM-backed interjection branch still orchestrates decision generation, message publication, reply generation, plan update, and return assembly inline.
