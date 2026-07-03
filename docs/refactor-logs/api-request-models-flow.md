<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:38:16Z" -->

# API Request Models Flow Refactor

## Files Changed

- `src/backend/agents/api.py`
- `docs/refactor-logs/api-request-models-flow-before.md`
- `docs/refactor-logs/api-request-models-flow.md`

## Reason For Changes

- Restored explicit request models that route tests and callers expect from `agents.api`.
- Converted handlers from loose request dictionaries to typed Pydantic request boundaries while preserving the existing internal update logic.
- Resolved the request-model drift that blocked `src/backend/tests/test_request_models.py`.

## Behavior Preservation Notes

- Tool edit still updates only `name`, `description`, `icon`, `requires_approval`, `category`, and `parameters`.
- Skill edit still updates only `name`, `description`, `icon`, `instructions`, `slug`, `category`, and `required_tools`.
- Skill version still increments only when `instructions` is provided.
- Digital twin move still requires both `agent_id` and `room_id`.
- Digital twin interact still accepts the `from` alias and returns the same interaction shape.
- No database schema, route path, or response format changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_request_models.py`: passed, `9 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- `src/backend/agents/api.py` still contains several unrelated route families in one file. This pass only restored request model boundaries.
- Some endpoints still accept loose dictionaries; those should be handled only when their tests or route family is the active slice.
