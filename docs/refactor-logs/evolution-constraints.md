# Evolution Constraints Refactor Log

Last updated: 2026-06-26

## Files Changed

| File | Reason |
| --- | --- |
| `src/backend/agents/evolution/constraints.py` | Extracted magic values, regexes, Chinese-ratio calculation, and target ratio lookup into named constants/helpers. |
| `src/backend/tests/test_evolution_constraints.py` | Added direct regression coverage for each constraint and aggregate validation output. |
| `docs/refactor-logs/evolution-constraints.md` | Recorded behavior preservation notes, validation, and residual risk. |

## Behavior Preservation Notes

- Public functions remain unchanged: `check_length`, `check_not_empty`, `check_language_consistency`, `check_format_preservation`, `check_no_meta_commentary`, and `validate_all`.
- Target type max ratios remain unchanged: `skill=1.5`, `rule=1.3`, `prompt=1.2`, unknown target defaults to `skill`.
- Empty-original length limit remains strict `< 5000`.
- Violation order in `validate_all` remains `length`, `not_empty`, `language`, `format`, `no_meta`.
- Output shape from `validate_all` is unchanged.

## Validation Result

Run from repository root on Windows PowerShell:

| Command | Status | Result |
| --- | --- | --- |
| `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_evolution_constraints.py` | Pass | `6 passed`. |
| `npm run lint` | Pass | Python `compileall` completed. |
| `npm run typecheck` | Pass | Current compile-only typecheck baseline completed. |

Full validation was not rerun for this module pass because `docs/VALIDATION.md` records unrelated existing build/test failures. The closest relevant subset was run.

## Remaining Risks

- Constraint thresholds are still heuristic by design; this refactor only names the existing values.
- No request/response formats, database schema, or business flows were changed.
