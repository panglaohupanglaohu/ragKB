<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T04:53:11Z" -->

# Budget Guard Flow Refactor

## Files Changed

- `src/backend/agents/budget/guard.py`
- `src/backend/tests/test_token_budget.py`
- `docs/refactor-logs/budget-guard-flow-before.md`
- `docs/refactor-logs/budget-guard-flow.md`

## Reason For Changes

- Clarified `BudgetGuard.check` by separating flow orchestration from date lookup, usage-total reads, event persistence, and halt detection.
- Kept `_check_limit` as the single per-scope budget decision point.
- Added focused regression coverage for budget guard behavior that must stay stable during later core-flow refactors.

## Behavior Preservation Notes

- Event order remains session, agent, team.
- Threshold warnings still allow execution.
- `on_exceed="warn"` still records warnings and allows execution.
- Missing scope IDs and non-positive limits still skip event creation.
- Overage and threshold event messages are unchanged.
- Public APIs, request/response formats, and database schema were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_budget_models.py src/backend/tests/test_token_budget.py -k "not update_usage_budget_persists_settings_and_summary_endpoint"`: passed, `12 passed, 1 deselected`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Known Legacy Failure

- `src/backend/tests/test_token_budget.py::TestTokenBudget::test_update_usage_budget_persists_settings_and_summary_endpoint` remains excluded for this slice. It fails because `agents.api` no longer exposes `get_usage_store`; this is API budget endpoint drift, not part of the `BudgetGuard.check` refactor.

## Remaining Risks

- `_utc_today` still reads real system time, so tests that depend on daily aggregation should keep using isolated stores.
- API-level budget endpoint behavior still needs a separate high-risk flow pass.
