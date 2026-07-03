<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:55:37Z" -->

# System Evolution Full Audit Flow Refactor

## Files Changed

- `src/backend/channels/system_evolution.py`
- `src/backend/tests/test_system_evolution_audit.py`
- `docs/refactor-logs/system-evolution-full-audit-flow-before.md`
- `docs/refactor-logs/system-evolution-full-audit-flow.md`

## Reason For Changes

- Clarified `run_full_audit` by separating per-rule execution, skipped result construction, failed-rule item creation, aggregate result construction, compliance enrichment, and audit completion bookkeeping.
- Added focused tests for pass/fail/skip counts, failed-rule item creation, duplicate prevention for open items, and rediscovery after a prior item is closed.

## Behavior Preservation Notes

- `run_full_audit` keeps the same public method name and returned payload keys.
- Missing target channels and missing check functions still produce skipped audit details.
- Check exceptions still become failed audit details.
- Escalation tracking still runs only for executed checks.
- Open failed-rule items still prevent duplicate discovery.
- Closed or failed prior items still allow rediscovery.
- Audit trail, monitoring timestamp, compliance rating, and audit history updates remain in the same flow.
- Public APIs, data models, database schema, and request/response formats were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_system_evolution_audit.py src/backend/tests/test_plaza_evolution_bridge.py::TestEvolutionCycleGuards::test_run_evolution_cycle_does_not_auto_verify_dispatched_items`: passed, `4 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `dispatch_all_pending`, `verify_all_pending`, and `close_verified_items` remain larger flows and should be handled separately.
- Legacy `test_evolution_race.py` references `audit_single_rule`, which is not present in `SystemEvolutionChannel`; that pre-existing drift was intentionally left untouched.
- `SystemEvolutionChannel` still mixes audit, compliance, verification, escalation, and monitoring responsibilities in one class.
