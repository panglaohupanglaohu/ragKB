# Token Policy Refactor Log

Last updated: 2026-06-26

## Files Changed

| File | Reason |
| --- | --- |
| `src/backend/agents/token_policy.py` | Extracted token-efficiency calculation, violation appending, and final decision selection into private helpers. Removed unused imports. |
| `src/backend/tests/test_token_policy.py` | Added direct regression coverage for pass, warn, block, violation order, and zero-token efficiency behavior. |
| `docs/refactor-logs/token-policy.md` | Recorded behavior preservation notes, validation, and residual risk. |

## Behavior Preservation Notes

- Public classes and objects remain unchanged: `TokenViolationType`, `TokenBudget`, `TokenBudgetEngine`, and `ENGINE`.
- `TokenBudgetEngine.evaluate(...)` keeps the same input and output shape.
- Decision semantics are unchanged:
  - `critical` or `high` violations produce `block`.
  - medium-only violations produce `warn`.
  - no violations produces `pass`.
- Violation order is preserved: over budget, low efficiency, redundant calls, skill routing miss, token burst.
- Efficiency rounding remains `round(eff, 4)`.

## Validation Result

Run from repository root on Windows PowerShell:

| Command | Status | Result |
| --- | --- | --- |
| `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_token_policy.py` | Pass | `4 passed`. |
| `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_token_policy.py src/backend/tests/test_plan_loop_runtime.py` | Pass | `7 passed`. |
| `npm run lint` | Pass after rerun | First run hit a transient Windows `__pycache__` `PermissionError`; rerun passed. |
| `npm run typecheck` | Pass | Current compile-only typecheck baseline completed. |

Full validation was not rerun for this module pass because `docs/VALIDATION.md` records unrelated existing build/test failures. The closest relevant subset was run.

## Remaining Risks

- The engine still accepts loosely typed `dict` run input because callers already use plain dictionaries. Tightening this would be a public contract change and was avoided.
- No request/response formats, database schema, or business flows were changed.
