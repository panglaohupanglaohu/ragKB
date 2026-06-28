<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:19:47Z" -->

# API Budget Endpoint Flow Refactor

## Files Changed

- `src/backend/agents/api.py`
- `docs/refactor-logs/api-budget-endpoint-flow-before.md`
- `docs/refactor-logs/api-budget-endpoint-flow.md`

## Reason For Changes

- Restored the missing API-layer boundary for token usage budget settings and usage summaries.
- Kept budget persistence, active guard update, and usage aggregation delegated to existing budget services.
- Removed the legacy test drift where `agents.api` no longer exposed `get_usage_store` for dependency injection.

## Behavior Preservation Notes

- `UsageStore.summarize_usage` still owns aggregation.
- `save_budget_settings` still owns settings persistence.
- `BudgetGuard.update_budget` still owns active runtime budget replacement.
- No database schema, public model names, or budget decision behavior changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_token_budget.py`: passed, `10 passed`.
- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_budget_models.py src/backend/tests/test_token_budget.py`: passed, `13 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- The restored route paths are thin API entrypoints under the existing `agent-config` router prefix. Frontend callers, if any, should be verified in a separate UI/API integration pass.
- `on_exceed` remains a free string matching the existing `TokenBudget` model behavior; stricter enum validation would be a behavior change and was not included.
