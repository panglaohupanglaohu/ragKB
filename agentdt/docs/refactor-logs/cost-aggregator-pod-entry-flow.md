<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:19:50Z" -->

# Cost Aggregator Pod Entry Flow Refactor

## Files Changed

- `src/backend/agents/cost_aggregator.py`
- `src/backend/tests/test_cost_aggregator.py`
- `docs/refactor-logs/cost-aggregator-pod-entry-flow-before.md`
- `docs/refactor-logs/cost-aggregator-pod-entry-flow.md`

## Reason For Changes

- Clarified `_pod_from_entry` by separating label lookup, namespace fallback, team fallback, cost lookup, RAM conversion, and window extraction.
- Added tests for namespace-derived labels, pod-name team derivation, summed total cost, RAM byte-hour conversion, and window fields.

## Behavior Preservation Notes

- Top-level cost fields still take precedence over properties.
- Missing `totalCost` still sums component costs.
- `ramByteHours` still converts with `1024 ** 3`.
- Namespace fallback labels are unchanged.
- Team derivation from `agentsgroup-{team}-...` pod names is unchanged.
- `PodCostItem` rounding and field names are unchanged.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_cost_aggregator.py`: passed, `5 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- Summary aggregation and trend computation remain separate flows.
- OpenCost polling error handling was intentionally left unchanged.
