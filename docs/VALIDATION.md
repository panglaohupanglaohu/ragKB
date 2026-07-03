# Validation Baseline

Last updated: 2026-06-26

## Environment Assumptions

- Windows PowerShell from repository root `D:\zhaotaoworkspace\agentdt`.
- Node.js `v22.14.0`, npm `10.9.2`.
- Python uses the repository local virtual environment when present: `venv\Scripts\python.exe`.
- Python version observed in `venv`: `Python 3.13.1`.
- The legacy `rtk` command is not installed locally. Package scripts now use local npm binaries and `scripts/run-python.cjs`, which prefers `.venv`, then `venv`, then system Python.

## Commands

| Purpose | Command |
| --- | --- |
| Install | `npm install`; `venv\Scripts\python.exe -m pip install -e ".[dev]"` |
| Build | `npm run build` |
| Lint | `npm run lint` |
| Typecheck | `npm run typecheck` |
| Test | `npm test` |
| Frontend tests | `npm run test:frontend` |
| Backend tests | `npm run test:backend` |
| Root tests | `npm run test:root` |

## Current Status

| Command | Status | Result |
| --- | --- | --- |
| `npm ci` | Fail | Local Windows cleanup failed with `EPERM` while unlinking `node_modules\@esbuild\win32-x64\esbuild.exe`. |
| `npm install` | Pass with cleanup warnings | Installed npm dependencies. npm warned it could not remove stale esbuild/rollup temporary native binaries because of `EPERM`. |
| `venv\Scripts\python.exe -m pip install -e ".[dev]"` | Pass | Installed the Python project and dev extras into `venv`. |
| `npm run build` | Fail | Vite starts, then fails resolving `/vendor/three/build/three.module.js` from `src/frontend/js/sandbox-twin-3d.js?v=20260616`. It also warns many HTML scripts are not `type="module"`. |
| `npm run lint` | Pass | `python -m compileall -q src/backend` completed. |
| `npm run typecheck` | Pass | Same compile baseline as lint; no dedicated static type checker is configured. |
| `npm test` | Fail | `96 failed, 1156 passed, 7 skipped, 2 warnings` in about 3m16s. |
| `npm run test:frontend` | Fail | `12 failed, 159 passed` across 40 Vitest files. |
| `npm run test:backend` | Fail | `66 failed, 952 passed, 5 skipped, 2 warnings` in about 2m44s. |
| `npm run test:root` | Fail | `30 failed, 204 passed, 2 skipped` in about 43s. |
| `node scripts/check-docs-signoff.cjs --strict` | Fail | Existing docs history has 27 unsigned plan/todos files. `docs/VALIDATION.md` is not a plan/todos file and is not part of that failure set. |

## Known Legacy Failures

- Build fails on the frontend Three.js vendor import path: `/vendor/three/build/three.module.js` is not resolved by Vite from `sandbox-twin-3d.js`.
- Frontend tests have existing contract drift in login redirect handling, digital-twin state/session expectations, scenario card markup, and cost dashboard rendering/API behavior.
- Backend tests have existing API contract drift around skill binding, pagination envelopes, auth guards, request model validation, runtime/tool loop entrypoints, token budget helpers, and Plaza trace/task behavior.
- Root tests include Windows-specific `Path.rename` failures when overwriting existing files, `config/settings.json` default-encoding `UnicodeDecodeError` under GBK locale, digital-twin trial/state expectations, settings-key checks, and v4 trial API expectations.
- Docs sign-off strict mode currently fails on existing unsigned plan/todos documents. This was observed but not fixed because the task only required creating the validation baseline.

## Recommended Refactor Gate

Before every future refactor, run:

```powershell
npm run lint
npm run typecheck
npm run build
npm test
```

Treat `npm run lint` and `npm run typecheck` as the current hard baseline. Keep the documented `build` and test failures visible until each legacy failure group is intentionally repaired.

## Minimal Fixes Made

- Replaced unavailable `rtk` wrappers in `package.json` scripts with local npm binaries and `scripts/run-python.cjs`.
- Added `npm run typecheck` as the current Python compile-only typecheck baseline because no mypy/pyright/tsc configuration exists.
- Added `scripts/run-python.cjs` so npm scripts prefer local `.venv`/`venv` Python consistently.
