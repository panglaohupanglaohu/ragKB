<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:00:05Z" -->

# Plaza Interjection Revised Plan Prompt Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-revised-plan-prompt-flow-before.md`
- `docs/refactor-logs/plaza-interjection-revised-plan-prompt-flow.md`

## Reason For Changes

- Reduced inline response aggregation and prompt construction in the revised-plan branch.
- Added `_format_interjection_responses` for deterministic response text.
- Added `_build_interjection_revised_plan_prompt` for direct prompt contract testing.
- Added coverage for topic, goal, user interjection, responses, existing plan JSON, table contract, and empty response fallback.

## Behavior Preservation Notes

- LLM plan generation call is unchanged.
- Plan payload, revised-plan message, `plan_updated`, resumed state, store save, and return shape are unchanged.
- Existing plan JSON rendering still uses `ensure_ascii=False`.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_interjection_revised_plan_prompt_uses_responses_and_existing_plan src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_format_interjection_responses_defaults_when_empty`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Interjection branch still has inline publish/broadcast/save tail.
- Full end-to-end interjection behavior still relies on existing route-level behavior rather than a complete new integration test.
