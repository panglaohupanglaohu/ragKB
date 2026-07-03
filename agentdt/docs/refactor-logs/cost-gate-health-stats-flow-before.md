<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:03:46Z" -->

# Cost Gate Health Stats Flow - Before

## Scope

Core flow: `/health` and `/stats` in `src/backend/agents/cost_gate_routes.py`.

## Current Flow

`cost_gate_health` currently:

1. Builds token health inline with `{"status": "healthy", "engine": "token_budget"}`.
2. Best-effort imports token gate `_stats`.
3. Best-effort loads legacy terraform cost gate status.
4. Returns a combined payload with token semantics as default.

`get_stats` currently:

1. Best-effort imports token gate `_stats`.
2. Best-effort loads terraform gate stats.
3. Returns a combined token + terraform payload.

## Existing Boundaries

- Token gate stats live in `token_gate_routes._stats`.
- Legacy terraform gate state lives behind `_get_cost_gate`.
- Route functions currently own fallback payload construction.

## Behavior To Preserve

- Health returns `status`, `default_semantics`, `token`, and `terraform`.
- Token health status remains `healthy`.
- Terraform health fallback remains `{"status": "unavailable", "reason": ...}`.
- Stats returns `default_semantics`, `token`, and `terraform`.
- Terraform stats fallback remains `{"error": ...}`.

## Smallest Safe Refactor Slice

Extract token stats, token health, terraform health, and terraform stats helper functions while preserving payload shape and fallback behavior.
