<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:17:35Z" -->

# Plaza Interjection Nominated Reply Generate Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-nominated-reply-generate-flow-before.md`
- `docs/refactor-logs/plaza-interjection-nominated-reply-generate-flow.md`

## Reason For Changes

- Moved LLM-backed nominated reply generation and metadata attachment into `_generate_interjection_nominated_reply`.
- Added focused coverage for `_agent_speak` arguments, reply target, and metadata.

## Behavior Preservation Notes

- `_agent_speak` remains the message-generation path.
- Reply-to and metadata values are unchanged.
- Supplementary replies, plan update, broadcasts, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_generate_interjection_nominated_reply_sets_link_metadata src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_simulated_interjection_speaker_reply_uses_stable_metadata`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Supplementary reply generation still attaches metadata inline.
- LLM-backed interjection branch can still be reduced further once reply-generation helpers are complete.
