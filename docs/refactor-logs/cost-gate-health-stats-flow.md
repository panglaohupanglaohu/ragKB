<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:05:20Z" -->

# Cost Gate Health Stats Flow Refactor

## Files Changed

- `src/backend/agents/cost_gate_routes.py`
- `src/backend/tests/test_cost_gate_routes.py`
- `docs/refactor-logs/cost-gate-health-stats-flow-before.md`
- `docs/refactor-logs/cost-gate-health-stats-flow.md`

## Reason For Changes

- Clarified token-first cost gate health and stats payload construction.
- Extracted token stats, token health, terraform health, and terraform stats helpers.
- Added route-level tests for combined token/terraform payloads and terraform unavailable fallback.

## Behavior Preservation Notes

- `/health` still returns `status`, `default_semantics`, `token`, and `terraform`.
- Token health still reports `status="healthy"` and `engine="token_budget"`.
- Terraform health still falls back to `{"status": "unavailable", "reason": ...}`.
- `/stats` still returns `default_semantics`, `token`, and `terraform`.
- Terraform stats still falls back to `{"error": ...}`.
- Terraform evaluate, policies, budget, and history routes were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_cost_gate_routes.py`: passed, `3 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- `reset_stats` still resets only legacy terraform stats; token stats reset behavior should be considered in a separate compatibility pass.
- Terraform evaluate remains a larger legacy flow and was intentionally left untouched.
