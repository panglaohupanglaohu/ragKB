<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:17:17Z" -->

# System Evolution Dispatch Item Flow - Before

## Scope

Core flow: `SystemEvolutionChannel.dispatch_item` in `src/backend/channels/system_evolution.py`.

## Current Flow

1. Look up an evolution item by ID.
2. Return `None` when the item is missing.
3. Normalize enum/string status.
4. If the item is `discovered`, move it to `dispatched`.
5. Stamp `dispatched_at`.
6. Increment `total_dispatched`.
7. Record a dispatch audit trail entry.
8. Return the item.

## Behavior To Preserve

- Missing item returns `None`.
- Non-discovered items are returned unchanged.
- Enum and string statuses are both accepted.
- Single-item dispatch does not assign a build agent or call Build manager.
- Audit trail recording remains part of this compatibility path.

## Smallest Safe Refactor Slice

Extract helpers for item lookup, discovered-status detection, single-item dispatch mutation, and audit trail recording without changing side effects.
