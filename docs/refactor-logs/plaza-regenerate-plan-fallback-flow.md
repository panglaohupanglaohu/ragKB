<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:35:00Z" -->

# Plaza Regenerate Plan Fallback Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-regenerate-plan-fallback-flow-before.md`
- `docs/refactor-logs/plaza-regenerate-plan-fallback-flow.md`

## Reason For Changes

- Moved regenerate-plan deterministic fallback into `_build_regenerate_plan_fallback`.
- Added focused coverage for actionable fallback output, reason text, and execution-plan table contract.

## Behavior Preservation Notes

- The fallback trigger remains `_has_actionable_plan(plan_text)`.
- Participant source and fallback reason are unchanged.
- Plan payload, publish, broadcast, save, and return shape were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_regenerate_plan_fallback_returns_actionable_plan src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_resolve_regenerate_plan_moderator_falls_back_to_niche` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- Regenerate-plan publish/broadcast/save tail remains inline.
