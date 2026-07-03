<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:35:41Z" -->

# Plaza Final Summary Prompt Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-final-summary-prompt-flow-before.md`
- `docs/refactor-logs/plaza-final-summary-prompt-flow.md`

## Reason For Changes

- Reduced inline prompt construction in the final summary section.
- Added `_build_final_summary_prompt` so the final summary contract can be tested directly.
- Added coverage for history inclusion, topic metadata, weighted conclusion requirements, execution plan table, and Markdown output instruction.

## Behavior Preservation Notes

- The summarizing status transition and broadcast are unchanged.
- `_generate_agent_content` is still called with `bypass_degraded=True`.
- Fallback deterministic plan generation is unchanged.
- Plan payload, closing message, persistence, and auto-extract were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_final_summary_prompt_uses_history_and_plan_contract src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_round_summary_prompt_uses_round_messages`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- The final summary fallback, plan update, closing message, persistence, and auto-extract still live inline in `run_discussion`.
- The nested debate loop still owns exchange iteration and fallback counter state.
