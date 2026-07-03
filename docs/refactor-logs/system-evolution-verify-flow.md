<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:08:30Z" -->

# System Evolution Verify Flow Refactor

## Files Changed

- `src/backend/channels/system_evolution.py`
- `src/backend/tests/test_system_evolution_audit.py`
- `docs/refactor-logs/system-evolution-verify-flow-before.md`
- `docs/refactor-logs/system-evolution-verify-flow.md`

## Reason For Changes

- Clarified `verify_pending_items` by separating candidate filtering, verify test resolution, missing-test skip handling, verify execution, outcome application, and result payload construction.
- Added focused coverage for missing verify tests staying `verify_pending` while returning a skipped verification result.

## Behavior Preservation Notes

- `verify_all_pending` remains a compatibility wrapper over `verify_pending_items`.
- Item ID, plaza ID, and discussion ID filters are unchanged.
- Registered verify functions and audit-rule fallback resolution are unchanged.
- Missing verify tests still record blocked evidence and return skipped results.
- Verify exceptions still become failed details.
- Passed, retry-queued, and max-retry exhausted state transitions are unchanged.
- Escalation updates and evidence recording remain in the verification flow.
- Public APIs, data models, database schema, and request/response formats were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_system_evolution_audit.py src/backend/tests/test_plaza_task_artifact_bridge.py::TestPlazaEvolutionSync::test_verify_all_pending_requeues_with_alert_detail src/backend/tests/test_plaza_task_artifact_bridge.py::TestPlazaEvolutionSync::test_verify_all_pending_marks_failed_after_max_retries src/backend/tests/test_plaza_task_artifact_bridge.py::TestPlazaEvolutionSync::test_verify_all_pending_updates_item_escalation_tier`: passed, `8 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `close_verified_items` remains a larger flow and should be handled next.
- Evidence storage failures are still best-effort and only logged by `_record_evolution_verify_evidence`.
- `dispatch_item` remains a separate single-item dispatch path with different side effects and was intentionally left untouched.
