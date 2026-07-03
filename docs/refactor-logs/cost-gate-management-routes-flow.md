<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:12:52Z" -->

# Cost Gate Management Routes Flow Refactor

## Files Changed

- `src/backend/agents/cost_gate_routes.py`
- `src/backend/tests/test_cost_gate_routes.py`
- `docs/refactor-logs/cost-gate-management-routes-flow-before.md`
- `docs/refactor-logs/cost-gate-management-routes-flow.md`

## Reason For Changes

- Clarified policy, budget, and history route adapters by extracting policy conversion, single-policy lookup, required-budget retrieval, and history summary mapping.
- Added route-level tests for policy list/update/delete, budget get/set/missing behavior, history summaries, report lookup, and missing report 404.

## Behavior Preservation Notes

- Public route paths and status codes are unchanged.
- Single policy lookup still uses `gate._engine.get_resource_config`.
- Missing policy, missing budget, and missing report still return HTTP 404 with the same detail text.
- History response shape remains `{"count": int, "reports": [...]}` with the same summary fields.
- `set_budget` still forwards `request.model_dump()` and returns `budget.to_dict()`.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_cost_gate_routes.py`: passed, `10 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- `reset_stats` still only covers legacy terraform stats and remains a separate compatibility slice.
- Cost gate channel internals were not changed.
