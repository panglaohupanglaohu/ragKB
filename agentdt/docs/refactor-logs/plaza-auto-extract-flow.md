<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:44:02Z" -->

# Plaza Auto Extract Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-auto-extract-flow-before.md`
- `docs/refactor-logs/plaza-auto-extract-flow.md`

## Reason For Changes

- Separated auto-extract configuration checking from pipeline creation.
- Added `_auto_extract_enabled` for settings handling.
- Added `_build_auto_extract_description` for the pipeline description payload.
- Added focused coverage for description topic, summary, and plan content.

## Behavior Preservation Notes

- Settings read failures still default to enabled.
- `auto_extract_on_consensus=false` still returns before store lookup.
- Pipeline creation arguments are unchanged except that description is now produced by a helper.
- Store resolution and logging were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_auto_extract_description_uses_summary_and_plan src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_close_discussion_with_summary_broadcasts_closing_events`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- The actual extraction store integration is still covered only indirectly.
- A later slice can add a monkeypatched integration test for `_auto_extract_on_consensus` without touching production behavior.
