<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:58:07Z" -->

# System Evolution Dispatch Flow - Before

## Scope

Core flow: `SystemEvolutionChannel.dispatch_all_pending` in `src/backend/channels/system_evolution.py`.

## Current Flow

1. Resolve the global registry and optional `build_team_manager`.
2. Define local agent assignment maps for audit domain, severity, and per-rule override.
3. Iterate all evolution items.
4. Skip items that are not `discovered`.
5. Move discovered items to `dispatched`.
6. Stamp `dispatched_at` and increment `total_dispatched`.
7. Assign an agent using per-rule override, then critical severity override, then audit-domain map, then `code_writer`.
8. If the Build manager exists and has `assign_task`, send `evolution_fix:{build_task_id}:{title}` to the assigned agent.
9. Collect dispatched item IDs and return `{"dispatched": ids, "count": len(ids)}`.

## Behavior To Preserve

- Only `discovered` items are dispatched.
- Status, timestamp, total counter, and assigned agent are updated before optional Build manager dispatch.
- Critical severity still maps to `chief_director`.
- Datacenter domain still maps to `code_writer`; general domain still maps to `dev_lead`.
- Unknown domains still fall back to `code_writer`.
- Optional Build manager assignment remains best-effort and skipped when unavailable.
- Return shape remains unchanged.

## Smallest Safe Refactor Slice

Extract helpers for pending item filtering, item dispatch mutation, assigned-agent resolution, optional Build manager assignment, and task description construction without changing public behavior.
