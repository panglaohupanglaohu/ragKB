<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:15:15Z" -->

# Plaza Simulated Interjection Speaker Reply Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-simulated-interjection-speaker-reply-flow-before.md`
- `docs/refactor-logs/plaza-simulated-interjection-speaker-reply-flow.md`

## Reason For Changes

- Moved simulated nominated speaker reply publication into `_publish_simulated_interjection_speaker_reply`.
- Added focused coverage for reply target, metadata, round number, niche role, and message content.

## Behavior Preservation Notes

- User-message truncation remains `user_message[:60]`.
- Metadata and reply-to behavior are unchanged.
- Plan update, resumed broadcast, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_simulated_interjection_speaker_reply_uses_stable_metadata src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_handle_simulated_interjection_publishes_reply_plan_and_saves`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- LLM-backed nominated and supplementary reply publication still update reply metadata inline.
- The LLM-backed branch still has multiple orchestration steps in one method.
