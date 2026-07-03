<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:50:37Z" -->

# System Evolution Cycle Flow Refactor

## Files Changed

- `src/backend/channels/system_evolution.py`
- `src/backend/tests/test_plaza_evolution_bridge.py`
- `docs/refactor-logs/system-evolution-cycle-flow-before.md`
- `docs/refactor-logs/system-evolution-cycle-flow.md`

## Reason For Changes

- Clarified `run_evolution_cycle` by separating cycle step execution from response payload construction.
- Strengthened regression coverage for the cycle result shape and the existing guard that newly dispatched items are not auto-verified in the same cycle.

## Behavior Preservation Notes

- Audit, dispatch, verify, and close still run in the same order.
- The returned payload keeps the same keys: `cycle`, `audit`, `dispatch`, `verify`, `closed`, and `summary`.
- Dispatch-only items still remain `dispatched` after the cycle and do not move to verification automatically.
- Audit rules, dispatch implementation, verification implementation, and close logic were not changed.
- Public APIs, data models, database schema, and request/response formats were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_evolution_bridge.py::TestEvolutionCycleGuards::test_run_evolution_cycle_does_not_auto_verify_dispatched_items`: passed, `1 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `run_full_audit`, `dispatch_all_pending`, `verify_all_pending`, and `close_verified_items` remain larger flows and should be handled as separate slices.
- `SystemEvolutionChannel` still mixes audit, compliance, verification, escalation, and monitoring concerns in one class.
- HTTP endpoint behavior is covered indirectly by broader integration tests, not by this focused unit slice.
