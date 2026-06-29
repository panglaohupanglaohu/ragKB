<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:03:18Z" -->

# Plaza Interjection Plan Update Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-plan-update-flow-before.md`
- `docs/refactor-logs/plaza-interjection-plan-update-flow.md`

## Reason For Changes

- Removed duplicated plan-update tail logic from no-LLM and LLM-backed interjection branches.
- Added `_publish_interjection_plan_update` to centralize plan payload, revised-plan message publication, broadcasts, and store save.
- Added focused coverage for revision reason, message metadata, round number, broadcast order, and persistence.

## Behavior Preservation Notes

- Branch-specific plan text and reply target are still passed in by the caller.
- Return shapes from `handle_live_interjection` are unchanged.
- `plan_updated` still broadcasts before `interjection_state=resumed`.
- Store save still occurs after broadcasts.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_interjection_plan_update_saves_and_resumes src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_interjection_revised_plan_prompt_uses_responses_and_existing_plan`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `handle_live_interjection` still orchestrates pause state, redirect decision, reply generation, and return assembly inline.
- Full end-to-end interjection behavior remains covered by targeted helper tests rather than a broad integration test.
