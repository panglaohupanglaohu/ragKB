# Low-Risk Cleanup Log

Last updated: 2026-06-26

## Scope

This cleanup only removed tracked temporary artifacts already identified in `docs/全仓库分阶段重构路线.md` Phase 2. No business logic, public API, database schema, request format, or response format was changed.

## Deleted Files

| File | Action | Reference check | Reason |
| --- | --- | --- | --- |
| `.perm_test_5` | Deleted | `rg` found no references outside cleanup documentation and generated anatomy metadata. | Empty permission-test artifact. |
| `src/backend/0tfuaiyp` | Deleted | `rg` found no imports, scripts, tests, docs entrypoints, or runtime references outside cleanup documentation and generated anatomy metadata. | Four-byte accidental file containing `blat`. |
| `tests/_test_write_temp.txt` | Deleted | Only referenced by `src/backend/tests/test_agent_toolbox.py` as a generated output path. | Stale test run artifact; not a source fixture. |
| `tests/_test_patch_temp.py` | Deleted | Only referenced by `src/backend/tests/test_agent_toolbox.py` as a generated output path. | Stale test run artifact; not a source fixture. |

## Preventive Ignore Rules

Added ignore rules for future local remnants:

```gitignore
/.perm_test_*
/tests/_test_*_temp.*
```

## Not Deleted

| Candidate | Status | Reason |
| --- | --- | --- |
| `_temp/design-demos/*.html` | Left in place | `docs/全仓库分阶段重构路线.md` marks these as possible design-process evidence, and `.huashu-skills/huashu-design/SKILL.md` documents `_temp/design-demos/` as the expected demo output directory. |
| `docs/archive/root-legacy/README.html` | Left in archive | Already archived as legacy documentation; no active cleanup benefit from deleting it now. |
| `docs/archive/root-legacy/README.backup-20260618T235918Z.md` | Left in archive | Already archived as legacy documentation; no active cleanup benefit from deleting it now. |

## Validation

Commands were rerun from `docs/VALIDATION.md` on Windows PowerShell:

| Command | Status | Notes |
| --- | --- | --- |
| `npm install` | Pass | Dependencies already up to date. |
| `venv\Scripts\python.exe -m pip install -e ".[dev]"` | Pass | Editable Python install completed. |
| `npm run lint` | Pass | Python `compileall` completed. |
| `npm run typecheck` | Pass | Current compile-only typecheck baseline completed. |
| `npm run build` | Fail, legacy | Same Vite failure as `docs/VALIDATION.md`: unresolved `/vendor/three/build/three.module.js`; non-module script warnings remain. |
| `npm test` | Fail, legacy | `96 failed, 1156 passed, 7 skipped, 2 warnings`; failure groups match the existing validation baseline. |
| `npm run test:frontend` | Fail, legacy | `12 failed, 159 passed`; same frontend drift groups as the baseline. |
| `npm run test:backend` | Fail, legacy | `66 failed, 952 passed, 5 skipped, 2 warnings`; same backend drift groups as the baseline. |
| `npm run test:root` | Fail, legacy | `31 failed, 203 passed, 2 skipped`; mostly the same root failures as the baseline, with one observed `test_openclaw_sync` failure in this run. |
| `node scripts/check-docs-signoff.cjs --strict` | Fail, legacy | Still reports 27 unsigned existing plan/todos documents. |

The validation run regenerated `tests/_test_write_temp.txt`, `tests/_test_patch_temp.py`, and `.bak` variants; these were removed again after validation.
