<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:41:08Z" -->

# Plaza Closing Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-closing-flow-before.md`
- `docs/refactor-logs/plaza-closing-flow.md`

## Reason For Changes

- Separated closing message construction and closing side effects from `run_discussion`.
- Added `_build_closing_message` for the final moderator message.
- Added `_close_discussion_with_summary` for message append, close state, end timestamp, and `discussion_end` broadcast.
- Added focused coverage for message fields, sequence, status, end timestamp, and broadcast order.

## Behavior Preservation Notes

- Closing message content still uses `_build_closing_brief`.
- Closing message still broadcasts before `discussion_end`.
- `discussion_end` payload is unchanged.
- Store persistence and auto-extract were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_close_discussion_with_summary_broadcasts_closing_events src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_apply_deterministic_summary_fallback_sets_plan_ready_summary`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Store persistence and auto-extract still remain inline in `run_discussion`.
- `_auto_extract_on_consensus` itself remains a separate high-risk hook to refactor later.
