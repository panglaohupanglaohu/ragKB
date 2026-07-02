<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:12:24Z" -->

# System Evolution Close Flow - Before

## Scope

Core flow: `SystemEvolutionChannel.close_verified` and `close_verified_items` in `src/backend/channels/system_evolution.py`.

## Current Flow

1. `close_verified` delegates to `close_verified_items`.
2. Build an optional item ID filter.
3. Iterate all evolution items.
4. Only process items with status `verified`.
5. Optionally filter by item ID, source plaza ID, and source discussion ID.
6. Move matching items to `closed`.
7. Stamp `closed_at`.
8. Store `close_reason`, defaulting to `verified improvement accepted`.
9. Store `close_verify_conclusion`, defaulting to `verify_detail`, then `verify_result`, then empty string.
10. Increment `total_closed`.
11. Return the closed item IDs.

## Behavior To Preserve

- `close_verified` remains a compatibility wrapper.
- Only verified items can be closed.
- Item ID, plaza ID, and discussion ID filters are unchanged.
- Default close reason and conclusion fallback order are unchanged.
- `total_closed` increments once per closed item.
- Return shape remains a list of closed item IDs.

## Smallest Safe Refactor Slice

Extract helpers for candidate filtering, item close mutation, and close conclusion fallback without changing public behavior.
