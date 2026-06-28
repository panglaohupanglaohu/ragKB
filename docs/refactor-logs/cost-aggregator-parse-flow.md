<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:16:20Z" -->

# Cost Aggregator Parse Flow Refactor

## Files Changed

- `src/backend/agents/cost_aggregator.py`
- `src/backend/tests/test_cost_aggregator.py`
- `docs/refactor-logs/cost-aggregator-parse-flow-before.md`
- `docs/refactor-logs/cost-aggregator-parse-flow.md`

## Reason For Changes

- Clarified OpenCost allocation response parsing by separating response item normalization, wrapped-entry detection, candidate extraction, safe pod parsing, and final sorting/limiting.
- Added focused tests for direct list responses, dict `data` responses, wrapped multi-pod entries, invalid entry skipping, and cost sorting.

## Behavior Preservation Notes

- List and dict response formats are still accepted.
- Dict `data` values are still iterated.
- Wrapped allocation entries are still unwrapped when all values are dictionaries.
- Invalid entries and per-entry parse failures are still skipped.
- Sorting by `total_cost` descending and `MAX_POD_ITEMS` truncation are unchanged.
- `_pod_from_entry` cost and label extraction behavior was not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_cost_aggregator.py`: passed, `3 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- `_pod_from_entry` still mixes label fallback, team derivation, and cost extraction; that should be a separate slice.
- Polling and cache update behavior were intentionally left untouched.
