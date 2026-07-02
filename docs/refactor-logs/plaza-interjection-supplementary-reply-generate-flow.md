<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:21:18Z" -->

# Plaza Interjection Supplementary Reply Generate Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-interjection-supplementary-reply-generate-flow-before.md`
- `docs/refactor-logs/plaza-interjection-supplementary-reply-generate-flow.md`

## Reason For Changes

- Moved LLM-backed supplementary reply generation and metadata attachment into `_generate_interjection_supplementary_reply`.
- Added focused coverage for `_agent_speak` arguments, reply target, and metadata.

## Behavior Preservation Notes

- `_agent_speak` remains the message-generation path.
- Reply target fallback and metadata values are unchanged.
- The caller still decides whether to append the returned message to `extra_replies`.
- Revised plan, broadcasts, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_generate_interjection_supplementary_reply_sets_link_metadata src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_generate_interjection_nominated_reply_sets_link_metadata`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- LLM-backed interjection branch can still be extracted as a single orchestration helper.
