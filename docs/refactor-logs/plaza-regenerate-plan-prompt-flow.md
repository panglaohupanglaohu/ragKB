<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:30:07Z" -->

# Plaza Regenerate Plan Prompt Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-regenerate-plan-prompt-flow-before.md`
- `docs/refactor-logs/plaza-regenerate-plan-prompt-flow.md`

## Reason For Changes

- Moved regenerate-plan prompt construction into `_build_regenerate_plan_prompt`.
- Added `_format_recent_plan_context` for the last-30-message context window.
- Added focused coverage for topic, goal, last-30 filtering, 200-character truncation, existing plan JSON, and output table contract.

## Behavior Preservation Notes

- `regenerate_plan` still calls `_generate_agent_content` with `bypass_degraded=True`.
- Fallback deterministic plan, plan payload, revised-plan message, broadcast, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_regenerate_plan_prompt_uses_recent_context_and_plan src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_handle_llm_interjection_orchestrates_replies_and_plan`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Moderator resolution and regenerate-plan publishing tail remain inline and can be split later.
