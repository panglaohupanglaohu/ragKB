<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:58:02Z" -->

# Plaza Interjection Supplementary Reply Prompt Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-supplementary-reply-prompt-flow-before.md`
- `docs/refactor-logs/plaza-interjection-supplementary-reply-prompt-flow.md`

## Reason For Changes

- Reduced inline prompt construction in the supplementary interjection branch.
- Added `_build_interjection_supplementary_reply_prompt` for direct testing.
- Added coverage for extra speaker identity, topic, user interjection, prior nominated reply, recent context, and no-repeat requirement.

## Behavior Preservation Notes

- Remaining-speaker selection is unchanged.
- Recent context still uses `_format_recent(disc, limit=6)`.
- `_agent_speak`, reply-to assignment, metadata updates, and extra reply collection are unchanged.
- Revised plan, broadcasts, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_interjection_supplementary_reply_prompt_uses_prior_reply src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_interjection_nominated_reply_prompt_uses_context`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Revised-plan prompt and interjection persistence tail remain inline.
- The branch still combines reply orchestration and plan update behavior.
