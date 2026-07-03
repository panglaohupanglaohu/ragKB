<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:14:54Z" -->

# System Evolution Close Flow Refactor

## Files Changed

- `src/backend/channels/system_evolution.py`
- `src/backend/tests/test_system_evolution_audit.py`
- `docs/refactor-logs/system-evolution-close-flow-before.md`
- `docs/refactor-logs/system-evolution-close-flow.md`

## Reason For Changes

- Clarified `close_verified_items` by separating verified item filtering, single-item close mutation, and close conclusion fallback.
- Added focused coverage for filtered close behavior, default close reason, conclusion fallback from `verify_detail`, `closed_at`, counter increments, and preserving non-matching/non-verified items.

## Behavior Preservation Notes

- `close_verified` remains a compatibility wrapper.
- Only `verified` items can be closed.
- Item ID, source plaza ID, and source discussion ID filters are unchanged.
- Default close reason remains `verified improvement accepted`.
- Close conclusion still falls back to `verify_detail`, then `verify_result`, then empty string.
- `total_closed` still increments once per closed item.
- Public APIs, data models, database schema, and request/response formats were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_system_evolution_audit.py src/backend/tests/test_evolution_evidence_detail.py::test_evolution_close_item_records_reason_and_conclusion`: passed, `7 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `dispatch_item` remains a separate single-item dispatch compatibility flow and should be handled next.
- `get_verification_queue` and `get_verification_alerts` still contain inline filtering and sorting logic.
- `SystemEvolutionChannel` still combines several responsibilities in one class.
