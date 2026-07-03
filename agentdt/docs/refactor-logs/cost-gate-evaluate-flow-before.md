<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:07:31Z" -->

# Cost Gate Evaluate Flow - Before

## Scope

Core flow: `evaluate_terraform_plan` in `src/backend/agents/cost_gate_routes.py`.

## Current Flow

1. Resolve the legacy terraform cost gate via `_get_cost_gate`.
2. Reject requests without `plan` or `plan_json` with HTTP 422.
3. Parse `plan_json` when provided, otherwise use `plan`.
4. Convert optional budget dict to `BudgetProfile`.
5. Call `gate.evaluate_plan`.
6. Convert report to dict.
7. Record unified evidence through `_record_cost_gate_evidence`.
8. Add `evidence_run_id` when present.
9. Log a warning when the report is blocked.
10. Return the result.
11. Convert JSON parse failures to HTTP 422.
12. Convert other failures to HTTP 500.

## Behavior To Preserve

- Route aliases `/evaluate` and `/terraform/evaluate` remain unchanged.
- Missing plan input still returns HTTP 422 with the same detail.
- Invalid `plan_json` still returns HTTP 422 with the same prefix.
- Blocked reports still return HTTP 200 payload and only log warning.
- Evidence id is still added only when non-empty.
- Budget conversion still uses `BudgetProfile.from_dict`.

## Smallest Safe Refactor Slice

Extract request validation, plan parsing, budget conversion, report execution, evidence attachment, and blocked logging helpers while preserving status codes and payload shape.
