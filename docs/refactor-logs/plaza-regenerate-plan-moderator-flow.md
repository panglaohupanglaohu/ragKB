<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:32:30Z" -->

# Plaza Regenerate Plan Moderator Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-regenerate-plan-moderator-flow-before.md`
- `docs/refactor-logs/plaza-regenerate-plan-moderator-flow.md`

## Reason For Changes

- Moved regenerate-plan moderator lookup into `_resolve_regenerate_plan_moderator`.
- Added focused coverage for explicit moderator preference and niche-role fallback.

## Behavior Preservation Notes

- Lookup order is unchanged.
- Missing moderator error handling remains in `regenerate_plan`.
- LLM call, deterministic fallback, plan payload, publish, broadcast, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_resolve_regenerate_plan_moderator_prefers_discussion_moderator src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_resolve_regenerate_plan_moderator_falls_back_to_niche`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Regenerate-plan fallback and publish tail remain inline.
