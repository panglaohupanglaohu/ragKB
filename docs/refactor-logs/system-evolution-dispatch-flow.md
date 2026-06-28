<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:01:03Z" -->

# System Evolution Dispatch Flow Refactor

## Files Changed

- `src/backend/channels/system_evolution.py`
- `src/backend/tests/test_system_evolution_audit.py`
- `docs/refactor-logs/system-evolution-dispatch-flow-before.md`
- `docs/refactor-logs/system-evolution-dispatch-flow.md`

## Reason For Changes

- Clarified `dispatch_all_pending` by separating pending item selection, dispatch mutation, assigned-agent resolution, optional Build manager assignment, and task description construction.
- Added focused coverage for dispatch result shape, status transition, assignment priority, skipped item preservation, counter increments, and Build manager task dispatch.

## Behavior Preservation Notes

- Only `discovered` items are dispatched.
- Status, `dispatched_at`, `total_dispatched`, and `assigned_agent` still update before optional Build manager assignment.
- Critical severity still maps to `chief_director`.
- General domain still maps to `dev_lead`; datacenter and unknown fallback still map to `code_writer`.
- Build manager assignment remains best-effort and uses `evolution_fix:{build_task_id}:{title}`.
- Return shape remains `{"dispatched": ids, "count": len(ids)}`.
- Public APIs, data models, database schema, and request/response formats were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_system_evolution_audit.py src/backend/tests/test_plaza_evolution_bridge.py::TestEvolutionCycleGuards::test_run_evolution_cycle_does_not_auto_verify_dispatched_items`: passed, `5 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `dispatch_item` still has a separate single-item dispatch path with slightly different side effects; that should be handled as a separate compatibility slice.
- `verify_all_pending` and `close_verified_items` remain larger flows and should be handled next.
- Build manager integration is covered with a fake manager only; broader integration remains in existing API tests.
