<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:39:04Z" -->

# Plaza Regenerate Plan Publish Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-regenerate-plan-publish-flow-before.md`
- `docs/refactor-logs/plaza-regenerate-plan-publish-flow.md`

## Reason For Changes

- Moved regenerate-plan publish, broadcast, save, and return tail into `_publish_regenerated_plan`.
- Added focused coverage for revision metadata, message metadata, broadcast order, save behavior, and return shape.

## Behavior Preservation Notes

- Plan text generation, fallback selection, and moderator resolution are unchanged.
- Revision reason and message metadata are unchanged.
- The helper still publishes the message before broadcasting `plan_updated`.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_publish_regenerated_plan_updates_message_broadcast_and_save src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_build_regenerate_plan_fallback_returns_actionable_plan src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_resolve_regenerate_plan_moderator_falls_back_to_niche` passed.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `git diff --check` passed with existing CRLF conversion warnings for touched Python files.
- `node scripts/check-docs-signoff.cjs --strict` still fails on 27 historical unsigned plan/todos files, not on this slice's new logs.

## Remaining Risks

- `_run_simulated` remains a separate inline core flow.
