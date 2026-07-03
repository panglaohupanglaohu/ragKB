<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:48:25Z" -->

# System Evolution Cycle Flow - Before

## Scope

Core flow: `SystemEvolutionChannel.run_evolution_cycle` in `src/backend/channels/system_evolution.py`.

## Current Flow

1. Run a full audit through `run_full_audit`.
2. Dispatch all pending discovered items through `dispatch_all_pending`.
3. Verify all pending verification items through `verify_all_pending`.
4. Close verified items through `close_verified`.
5. Return the cycle number, each step result, closed item IDs, and the current evolution summary.

## Behavior To Preserve

- Audit always runs before dispatch.
- Dispatch always runs before verify.
- Verify still does not auto-verify newly dispatched items unless their status already permits verification.
- Closing still runs after verification.
- Return keys remain `cycle`, `audit`, `dispatch`, `verify`, `closed`, and `summary`.
- Public APIs and data models remain unchanged.

## Smallest Safe Refactor Slice

Extract a named helper for running the cycle steps and a named helper for building the response payload. Keep the orchestration order and public result shape unchanged.
