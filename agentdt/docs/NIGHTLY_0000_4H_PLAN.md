# Nightly 00:00-04:00 Optimization Plan

## Objective
Keep the repository green while increasing the nightly automation depth.

## Current Baseline (2026-05-26)
- `pytest -q`: 71 passed
- `/api/v1/startup-check`: 8/8 passed
- Nightly script now produces:
  - full pytest baseline
  - failure cluster extraction
  - priority suite verification for `tests/test_ab_testing.py` and `tests/test_openclaw_sync.py`
  - bounded repair queue + orchestration status artifacts
  - startup smoke artifact
  - dynamic `summary.md`
- Main remaining gap:
  - `scripts/nightly_4h_optimize.sh` can now queue top failing suites and optionally invoke a repo-local repair hook, but no `scripts/nightly_repair_slice.sh` hook exists yet.

## 4-Hour Execution Window

### 00:00-00:20 | Baseline and Artifact Pack
- Run full pytest baseline.
- Capture failure clusters and priority suite results.
- Capture startup smoke result.
- Produce the run artifact pack in `storage/operations/nightly_logs/<timestamp>/`.

Exit criteria:
- `summary.md`, `priority_suites.txt`, and `startup_check.json` generated.

### 00:20-01:20 | Automation Slice A
Target file:
- `scripts/nightly_4h_optimize.sh`

Target outcomes:
- Consume top failure clusters into a bounded repair queue instead of only reporting them.
- Optionally invoke a repo-local repair hook when `scripts/nightly_repair_slice.sh` is present and executable.
- Keep the script non-destructive and time-bounded.
- Preserve green-path behavior when baseline already passes.

Exit criteria:
- Script remains successful on a green repo and emits `repair_queue.txt` / `repair_orchestration.txt` artifacts beyond baseline-only mode.

### 01:20-02:30 | Automation Slice B
Target surfaces:
- `docs/NIGHTLY_0000_4H_PLAN.md`
- `storage/operations/nightly_logs/<timestamp>/summary.md`

Target outcomes:
- Keep the nightly plan, artifacts, and actual script behavior aligned.
- Surface actionable next-night guidance from generated summaries, including whether the repair hook is still missing.

Exit criteria:
- Human-readable summary matches the real validation outputs and queue state.

### 02:30-03:30 | Runtime Validation
- Run full pytest.
- Run startup smoke validation.
- Confirm frontend/backend compatibility checks remain green.

Exit criteria:
- `pytest -q` green and startup-check green.

### 03:40-04:00 | Closeout
- Produce nightly summary:
  - changed files
  - validation results
  - remaining gaps + root causes
  - next-night top tasks

Exit criteria:
- `summary.md` written under the nightly run folder.

## Guardrails
- Do not touch archive/historical snapshot folders for functional fixes.
- Keep changes surgical and reversible.
- Prefer bounded validation and bounded repair over open-ended automation.
- If a broad refactor is needed, split into additive compatibility or orchestration layers first.

## Next-Night Strategy Trigger
If nightly baseline stays green for 3 consecutive runs:
- Freeze contract-repair work.
- Spend the next run on product TODOs, user-visible polish, or implementing `scripts/nightly_repair_slice.sh` only if failure-driven automation becomes necessary again.
