<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:12:53Z" -->

# Plaza Interjection Moderator Redirect Publish Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-moderator-redirect-publish-flow-before.md`
- `docs/refactor-logs/plaza-interjection-moderator-redirect-publish-flow.md`

## Reason For Changes

- Removed duplicated moderator redirect publication arguments from both interjection branches.
- Added `_publish_interjection_moderator_redirect` for stable message metadata and reply targeting.
- Added focused coverage for content, round number, niche role, reply target, and metadata.

## Behavior Preservation Notes

- `publish_message` still owns append, content shaping, and broadcast.
- Metadata keys and values are unchanged.
- Simulated and LLM-backed branch return shapes are unchanged.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_interjection_moderator_redirect_uses_stable_metadata src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_ensure_interjection_nomination_prefix_adds_missing_prefix`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Nominated reply publication still has branch-specific inline logic.
- LLM-backed interjection orchestration remains inline.
