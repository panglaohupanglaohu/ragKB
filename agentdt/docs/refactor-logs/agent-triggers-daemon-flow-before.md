<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:56:29Z" -->

# Agent Triggers Daemon Flow - Before

## Scope

Core flow: `TriggerDaemon.tick` in `src/backend/agents/agent_triggers.py`.

## Current Flow

1. Resolve `now` to current UTC time when omitted.
2. Increment `_tick_count`.
3. Iterate all teams from `TriggerStore.list_teams`.
4. Iterate enabled triggers for each team.
5. Skip event-driven triggers: `on_message` and `webhook`.
6. Skip triggers that are not due.
7. Apply a 30 second per-agent deduplication window.
8. Fire due triggers via `_fire`.
9. Every fourth tick, check heartbeat config and append heartbeat events.
10. Return all wake events.

## Existing Boundaries

- `TriggerStore` owns persisted trigger loading and updates.
- `is_due` and `compute_next_fire` own time matching.
- `_fire` owns trigger mutation, persistence, wake logging, and event creation.
- `_check_heartbeats` owns heartbeat generation.

## Behavior To Preserve

- Event-driven trigger types are not evaluated by periodic ticks.
- Dedup remains per-agent and uses `DEDUP_WINDOW_SEC`.
- Heartbeats are checked only every fourth tick.
- Returned event order remains due trigger events followed by heartbeat events.
- `_fire` behavior is unchanged.

## Smallest Safe Refactor Slice

Extract `TriggerDaemon` helpers for periodic-trigger filtering, dedup checks, trigger scanning, and heartbeat cadence while preserving the existing tick order and return shape.
