<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:25:05Z" -->

# System Evolution Verification Query Flow Refactor

## Files Changed

- `src/backend/channels/system_evolution.py`
- `src/backend/tests/test_system_evolution_audit.py`
- `docs/refactor-logs/system-evolution-verification-query-flow-before.md`
- `docs/refactor-logs/system-evolution-verification-query-flow.md`

## Reason For Changes

- Clarified verification query paths by extracting shared source filtering, alert sort keys, queue item payload construction, and queue sort keys.
- Added focused coverage for source filtering and priority sorting in both verification queue and alerts.

## Behavior Preservation Notes

- Source plaza and discussion filters are unchanged.
- Alert payload fields and queue payload fields are unchanged.
- Alert sorting still prioritizes critical alerts, then verification-pending alerts, then item ID.
- Queue sorting still prioritizes manual verification items, then verification-pending items, then item ID.
- Items without alert state remain excluded from alerts.
- Public route response shapes that consume these methods were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_system_evolution_audit.py src/backend/tests/test_plaza_evolution_bridge.py::TestPlazaEvolutionBridge::test_discussion_verification_queue_surfaces_manual_verify_items src/backend/tests/test_plaza_evolution_bridge.py::TestPlazaEvolutionBridge::test_discussion_verification_alerts_surface_retry_and_manual_verify`: passed, `11 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `SystemEvolutionChannel` still contains compliance rating, zone, escalation, and monitoring logic in the same class.
- Broader HTTP pagination/envelope behavior remains covered by existing integration tests, not this focused unit slice.
