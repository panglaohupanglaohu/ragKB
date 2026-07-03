<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:05:28Z" -->

# System Evolution Verify Flow - Before

## Scope

Core flow: `SystemEvolutionChannel.verify_all_pending` and its implementation `verify_pending_items` in `src/backend/channels/system_evolution.py`.

## Current Flow

1. `verify_all_pending` delegates to `verify_pending_items`.
2. Iterate evolution items and filter to `verify_pending`.
3. Optionally filter by item IDs, source plaza ID, and source discussion ID.
4. Resolve a registered verify function by `verify_test_name`.
5. If no registered function exists, fall back to the audit rule check function when the rule and target channel exist.
6. If no verify function is available, record blocked evidence and return a skipped result.
7. Execute the verify function and convert exceptions into failed verification details.
8. Store `verify_result`, `verify_detail`, and item escalation state.
9. On pass, move the item to `verified`, stamp `completed_at`, and increment `total_verified`.
10. On fail, increment retry count; exhausted retries move to `failed` and increment `total_failed`, otherwise move back to `dispatched`.
11. Record verification evidence and append the result payload.
12. Return `{"verified": results, "count": len(results)}`.

## Behavior To Preserve

- `verify_all_pending` remains a compatibility wrapper.
- Filters by item ID, plaza ID, and discussion ID are unchanged.
- Missing verify tests still produce skipped results with blocked evidence.
- Verify exceptions still become failed verification details.
- Retry queue and max-retry exhausted behavior are unchanged.
- Escalation state and evidence recording remain in the flow.
- Return shape remains unchanged.

## Smallest Safe Refactor Slice

Extract helpers for candidate filtering, verify function resolution, unavailable-test handling, verify execution, item state update, and result payload construction without changing behavior.
