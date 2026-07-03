<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:56:08Z" -->

# Plaza Interjection Nominated Reply Prompt Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-nominated-reply-prompt-flow-before.md`
- `docs/refactor-logs/plaza-interjection-nominated-reply-prompt-flow.md`

## Reason For Changes

- Reduced inline prompt construction in the nominated reply branch.
- Added `_build_interjection_nominated_reply_prompt` for direct test coverage.
- Added coverage for speaker identity, topic, user interjection, moderator reply, recent context, and direct-answer requirement.

## Behavior Preservation Notes

- `_agent_speak` invocation is unchanged.
- Reply-to assignment and metadata updates are unchanged.
- Supplementary replies, revised plan, broadcasts, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_interjection_nominated_reply_prompt_uses_context src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_interjection_redirect_prompt_lists_candidates`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Supplementary reply and revised-plan prompts remain inline.
- Interjection branch still contains the orchestration and persistence tail.
