<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:53:09Z" -->

# System Evolution Full Audit Flow - Before

## Scope

Core flow: `SystemEvolutionChannel.run_full_audit` in `src/backend/channels/system_evolution.py`.

## Current Flow

1. Resolve the global channel registry.
2. Increment `total_audits`.
3. Iterate all audit rules.
4. Resolve the target channel for each rule.
5. Record skipped results when the target channel or check function is missing.
6. Execute the rule check function and convert exceptions into failed audit details.
7. Track escalation state for executed rules.
8. For failed rules, avoid duplicate open evolution items.
9. Create a new `EvolutionItem` for failed rules without an existing open item.
10. Build the audit result payload with counts and details.
11. Calculate compliance rating and attach rating/escalation data.
12. Record an audit trail entry, update monitoring time, append audit history, trim history to 50 entries, and return the result.

## Behavior To Preserve

- Result keys and count semantics remain unchanged.
- Missing target channels and missing check functions still produce skipped details.
- Exceptions in check functions still become failed details instead of raising.
- Escalation tracking still runs only for executed checks.
- Failed rules do not create duplicate open evolution items.
- Closed or failed prior items still allow rediscovery.
- Audit trail, monitoring timestamp, compliance rating, and audit history updates remain unchanged.

## Smallest Safe Refactor Slice

Extract helper functions for per-rule execution, skipped result construction, new item creation, aggregate result construction, compliance enrichment, and audit bookkeeping. Keep the public method and returned payload unchanged.
