<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:18:37Z" -->

# API Budget Endpoint Flow - Before

## Scope

Core flow: token usage budget API surface in `src/backend/agents/api.py`.

## Current Flow

The budget storage and guard layers exist:

1. `agents.budget.store.UsageStore` records usage and exposes `summarize_usage`.
2. `agents.budget.guard.BudgetGuard` owns current `TokenBudget` and exposes `update_budget`.
3. `agents.budget.guard.save_budget_settings` persists budget settings to `config/settings.json`.

The API module no longer exposes the historical thin functions used by tests:

- `UsageBudgetUpdateRequest`
- `update_usage_budget`
- `get_usage_summary`
- `get_usage_store`

## Existing Failure

`src/backend/tests/test_token_budget.py::TestTokenBudget::test_update_usage_budget_persists_settings_and_summary_endpoint` fails because `agents.api` has no `get_usage_store` attribute to monkeypatch.

## Intended Boundary

- API layer should validate request fields and adapt them to budget/store services.
- Budget persistence remains in `save_budget_settings`.
- Usage aggregation remains in `UsageStore.summarize_usage`.
- Runtime budget state remains in `BudgetGuard.update_budget`.

## Smallest Safe Refactor Slice

Restore a thin API compatibility boundary:

1. Import budget service functions into `agents.api`.
2. Add `UsageBudgetUpdateRequest`.
3. Add `update_usage_budget` to persist settings and update the active guard.
4. Add `get_usage_summary` to return store summary plus filter metadata.

No production budget logic, database schema, or request/response contract should change beyond restoring the missing API surface.
