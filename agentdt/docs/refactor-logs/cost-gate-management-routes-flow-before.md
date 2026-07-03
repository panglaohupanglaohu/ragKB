<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:10:46Z" -->

# Cost Gate Management Routes Flow - Before

## Scope

Core flow: policy, budget, and history route adapters in `src/backend/agents/cost_gate_routes.py`.

## Current Flow

Policy routes:

1. `list_policies` gets the gate, optionally resolves one resource policy, otherwise returns all policies.
2. `upsert_policy` converts `PolicyUpdateRequest` to `ResourceTypeConfig`, updates the gate, logs, and returns result.
3. `delete_policy` deletes from the gate and returns 404 if absent.

Budget routes:

1. `get_budget` reads the default budget and returns 404 if missing.
2. `set_budget` forwards request data to the gate, logs, and returns budget dict.

History routes:

1. `get_history` reads reports and maps them to compact summaries.
2. `get_report` calls `gate.process_event({"type": "get_report", ...})` and returns 404 if absent.

## Behavior To Preserve

- Public route paths and status codes remain unchanged.
- Policy single-resource lookup still uses `gate._engine.get_resource_config`.
- Missing policies, missing budget, and missing reports still return HTTP 404 with the same detail text.
- History summary fields and shape remain unchanged.
- `set_budget` still returns `budget.to_dict()`.

## Smallest Safe Refactor Slice

Extract request-to-policy conversion, policy lookup, budget retrieval/update, and history summary mapping helpers while keeping gate calls and response shapes unchanged.
