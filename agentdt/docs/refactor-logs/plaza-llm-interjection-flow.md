<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:24:29Z" -->

# Plaza LLM Interjection Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-llm-interjection-flow-before.md`
- `docs/refactor-logs/plaza-llm-interjection-flow.md`

## Reason For Changes

- Moved LLM-backed interjection orchestration out of `handle_live_interjection`.
- Kept `handle_live_interjection` focused on context, lock, pause broadcast, and branch selection.
- Added an orchestration test with fixed helper outputs to verify message bundle, plan-update reason, and reply target.

## Behavior Preservation Notes

- Existing helper calls and their order are preserved.
- Return shape remains `moderator_reply`, `nominated_reply`, `extra_replies`, and `moderator_resume`.
- Plan update still replies to the last extra reply when present, otherwise nominated reply, otherwise moderator redirect.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_handle_llm_interjection_orchestrates_replies_and_plan src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_generate_interjection_supplementary_reply_sets_link_metadata`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- The next likely refactor target is plan refresh/regeneration or `_generate_agent_content` retry/fallback flow.
