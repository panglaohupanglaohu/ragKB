# Documentation Audit

Last updated: 2026-06-26

## Summary

The repository previously had no single trustworthy documentation entrypoint. The root `README.md` was a long product narrative that claimed broad platform behavior while the current validation baseline shows build and test failures. Multiple root-level planning documents duplicated docs under `docs/` and mixed historical plans with current instructions.

The new entrypoints are:

- [../README.md](../README.md) for quick orientation.
- [README.md](README.md) for documentation navigation.
- [VALIDATION.md](VALIDATION.md) for runnable commands and current pass/fail status.

## Findings

| Area | Finding | Action |
| --- | --- | --- |
| Root README | The old README described many capabilities as if fully supported, but [VALIDATION.md](VALIDATION.md) records failing build and test baselines. | Replaced with a short entrypoint and archived the old file. |
| Root planning docs | Root `OptimizePlan*`, `FrontBackEnd*`, `SECSOptimize.md`, and related files duplicated or overlapped with docs under `docs/`. | Moved to `docs/archive/root-legacy`. |
| HTML README | `README.html` was a generated/static variant of the old README and can drift from source docs. | Archived. |
| README backup | `README.backup-20260618T235918Z.md` is historical backup content. | Archived. |
| docs plan/todos collection | Many plan/todos files describe prior feature work and may contradict current code behavior. | Left in place but marked as `needs verification` through [docs/README.md](README.md). |
| Setup and validation | Setup commands were spread across README/start scripts and some old docs still mention `rtk`; local validation now uses npm scripts and `scripts/run-python.cjs`. | Entrypoints point to [VALIDATION.md](VALIDATION.md). |
| Sign-off compliance | Existing historical plan/todos files under `docs/` include unsigned files; strict sign-off validation currently fails on legacy documents. | Documented in [VALIDATION.md](VALIDATION.md); not mass-fixed in this cleanup. |

## Archived Documents

Moved to `docs/archive/root-legacy`:

- `README.legacy-20260626.md`
- `README.html`
- `README.backup-20260618T235918Z.md`
- `OptimizePlan.md`
- `OptimizePlan1.md`
- `OptimizePlanTodos.md`
- `OptimizePlan1Todos.md`
- `AgentDigitalTwinPlan.md`
- `AgentCostContainerTodo.md`
- `SECSOptimize.md`
- `FrontBackEndOptimize.md`
- `FrontBackEndTodos.md`
- `SandboxTwinFrontendTodos.md`

Status: archived, needs verification before reuse.

## Needs Verification

These documents remain in `docs/` because they may still be useful for project history or future refactor planning, but they should not be treated as current behavior without code and validation checks:

- `Agent数字孪生*.md`
- `AgentsGroupConfig优化*.md`
- `EVOLUTION_PLAN.md`
- `NIGHTLY_0000_4H_PLAN.md`
- `awsOpsE2E*.md`
- `frontendBigChange*.md`
- `plaza优化*.md`
- `skill-extract*.md`
- `system-evolution优化*.md`
- `任务执行*.md`
- `全局优化*.md`
- `联动优化*.md`
- `试炼页优化*.md`

## Current Documentation Rule

For setup, build, lint, typecheck, and test commands, [VALIDATION.md](VALIDATION.md) is authoritative. Any other document that conflicts with it is historical until updated and revalidated.
