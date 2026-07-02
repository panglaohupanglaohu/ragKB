<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:08:04Z" -->

# Plaza Simulated Interjection Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-simulated-interjection-flow-before.md`
- `docs/refactor-logs/plaza-simulated-interjection-flow.md`

## Reason For Changes

- Moved the no-LLM interjection branch into `_handle_simulated_interjection`.
- Kept `handle_live_interjection` focused on choosing between simulated and LLM-backed correction paths.
- Added focused coverage for redirect message, nominated reply, revised-plan update, resumed broadcast, save, and return shape.

## Behavior Preservation Notes

- Message text and metadata are unchanged.
- The first speaker is still used as the simulated nominated responder.
- Shared plan update still flows through `_publish_interjection_plan_update`.
- Return shape remains unchanged.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_handle_simulated_interjection_publishes_reply_plan_and_saves src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_broadcast_interjection_paused_uses_stable_payload`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- The LLM-backed interjection branch still handles redirect, replies, revised plan generation, and return assembly inline.
- A later slice can extract the LLM-backed branch orchestration once enough prompt/publish helpers are in place.
