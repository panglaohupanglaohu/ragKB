<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:08:59Z" -->

# Cost Gate Evaluate Flow Refactor

## Files Changed

- `src/backend/agents/cost_gate_routes.py`
- `src/backend/tests/test_cost_gate_routes.py`
- `docs/refactor-logs/cost-gate-evaluate-flow-before.md`
- `docs/refactor-logs/cost-gate-evaluate-flow.md`

## Reason For Changes

- Clarified terraform evaluate orchestration by separating request validation, plan parsing, budget conversion, gate execution, evidence attachment, and blocked-report logging.
- Added route-level tests for JSON plan parsing, budget conversion, metadata forwarding, evidence id attachment, missing plan rejection, and invalid JSON rejection.

## Behavior Preservation Notes

- Route aliases `/evaluate` and `/terraform/evaluate` are unchanged.
- Missing plan input still returns HTTP 422 with the same detail.
- Invalid `plan_json` still returns HTTP 422 with the same prefix.
- Blocked reports still return a normal payload and only log warning.
- Evidence id is still added only when `_record_cost_gate_evidence` returns a non-empty value.
- Budget conversion still uses `BudgetProfile.from_dict`.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_cost_gate_routes.py`: passed, `6 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- Policy, budget, history, and stats reset routes remain separate flows.
- The route still wraps unexpected errors as HTTP 500, matching existing behavior.
