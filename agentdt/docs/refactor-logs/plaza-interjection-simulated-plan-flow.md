<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:49:21Z" -->

# Plaza Interjection Simulated Plan Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-simulated-plan-flow-before.md`
- `docs/refactor-logs/plaza-interjection-simulated-plan-flow.md`

## Reason For Changes

- Reduced inline string construction in the no-LLM interjection branch.
- Added `_build_simulated_interjection_plan_content` for direct testing of the simulated plan contract.
- Added focused coverage for user-message truncation, chosen agent assignment, and execution-plan structure.

## Behavior Preservation Notes

- The no-LLM branch still publishes the same moderator, nominated reply, revised plan, plan update, resumed state, and save operations.
- Plan payload construction is unchanged.
- Return shape is unchanged.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_simulated_interjection_plan_content_uses_chosen_agent src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_prepare_interjection_context_resolves_moderator_and_speakers`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- The rest of the simulated interjection branch remains inline.
- LLM-backed redirect, nominated reply, supplementary reply, and revised-plan prompts remain inline.
