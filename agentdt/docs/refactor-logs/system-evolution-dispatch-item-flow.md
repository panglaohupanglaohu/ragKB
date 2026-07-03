<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:19:50Z" -->

# System Evolution Dispatch Item Flow Refactor

## Files Changed

- `src/backend/channels/system_evolution.py`
- `src/backend/tests/test_system_evolution_audit.py`
- `docs/refactor-logs/system-evolution-dispatch-item-flow-before.md`
- `docs/refactor-logs/system-evolution-dispatch-item-flow.md`

## Reason For Changes

- Clarified `dispatch_item` by separating status normalization, discovered-state detection, single-item dispatch mutation, and audit trail recording.
- Added focused coverage for missing items, non-discovered item preservation, discovered item dispatch, audit trail recording, and the compatibility behavior that single-item dispatch does not assign a build agent.

## Behavior Preservation Notes

- Missing item IDs still return `None`.
- Non-discovered items are still returned unchanged.
- Enum and string statuses are still accepted.
- Discovered items still move to `dispatched`, get `dispatched_at`, increment `total_dispatched`, and record a dispatch trail entry.
- Single-item dispatch still does not assign a build agent or call Build manager.
- Public APIs, data models, database schema, and request/response formats were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_system_evolution_audit.py`: passed, `8 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `get_verification_queue` and `get_verification_alerts` still contain inline filtering and sorting logic.
- Single-item dispatch remains intentionally different from `dispatch_all_pending`; any future behavior alignment should be handled as a compatibility change, not a refactor.
