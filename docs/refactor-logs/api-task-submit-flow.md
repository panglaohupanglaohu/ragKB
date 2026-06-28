<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:35:20Z" -->

# API Task Submit Flow Refactor

## Files Changed

- `src/backend/agents/api.py`
- `src/backend/tests/test_request_models.py`
- `docs/refactor-logs/api-task-submit-flow-before.md`
- `docs/refactor-logs/api-task-submit-flow.md`

## Reason For Changes

- Clarified the `submit_task` endpoint by extracting request-to-task construction, task-engine startup, Token Factory preflight, backend fallback, workflow initialization, pipeline seeding, handoff writing, and first-step launch into named helpers.
- Kept the endpoint as the orchestration boundary while leaving `TaskEngine` status and storage behavior unchanged.
- Added focused regression coverage for the existing behavior where tasks are still created when no execution backend is available.

## Behavior Preservation Notes

- Public route path and status code are unchanged.
- Response remains `task.to_dict()`.
- Missing Token Factory plus missing direct DeepSeek credentials still returns a queued task with `metadata["token_factory_error"]`.
- Direct DeepSeek credentials still allow execution when Token Factory is not ready.
- Workflow generation, context seeding, task submission, first-step session launch, task start, and harness monitor startup remain in the same order.
- No database schema, request/response formats, or public API names were changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_request_models.py::TestAgentConfigRequestModels::test_submit_task_returns_queued_task_when_backend_unavailable src/backend/tests/test_task_engine.py`: passed, `33 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Known Legacy Failures

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_request_models.py src/backend/tests/test_task_engine.py` currently fails in four pre-existing request-model drift tests:
  - `EditToolRequest` missing from `agents.api`
  - `EditSkillRequest` missing from `agents.api`
  - `DigitalTwinMoveRequest` missing from `agents.api`
  - `DigitalTwinInteractRequest` missing from `agents.api`

## Remaining Risks

- `src/backend/agents/api.py` remains large and still mixes unrelated route families. Future slices should keep extracting one route family at a time.
- The first-step session launch still depends on global skill/team registries and should be isolated in a later workflow-execution pass.
