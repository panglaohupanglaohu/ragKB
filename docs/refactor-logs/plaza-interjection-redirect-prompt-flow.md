<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:53:23Z" -->

# Plaza Interjection Redirect Prompt Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-redirect-prompt-flow-before.md`
- `docs/refactor-logs/plaza-interjection-redirect-prompt-flow.md`

## Reason For Changes

- Reduced inline prompt construction in the LLM-backed interjection redirect branch.
- Added `_build_interjection_redirect_prompt` so the moderator redirect contract can be tested directly.
- Added focused coverage for topic, round number, recent context, user interjection, candidate list, and `REPLY`/`NEXT` output contract.

## Behavior Preservation Notes

- Candidate selection remains unchanged.
- Candidate list still uses the first eight speakers.
- Recent context still uses `_format_recent(disc, limit=8)`.
- LLM invocation, decision parsing, message publishing, replies, plan revision, broadcasts, and persistence were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_interjection_redirect_prompt_lists_candidates src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_simulated_interjection_plan_content_uses_chosen_agent`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed after rerun. The first parallel run overlapped with `npm run lint` and hit a transient Windows `__pycache__` rename `PermissionError`.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Nominated reply, supplementary reply, and revised-plan prompts remain inline.
- Interjection branch still mixes orchestration and persistence after prompt generation.
