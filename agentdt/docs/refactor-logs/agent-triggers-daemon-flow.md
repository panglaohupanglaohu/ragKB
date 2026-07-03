<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:58:22Z" -->

# Agent Triggers Daemon Flow Refactor

## Files Changed

- `src/backend/agents/agent_triggers.py`
- `src/backend/tests/test_agent_triggers.py`
- `docs/refactor-logs/agent-triggers-daemon-flow-before.md`
- `docs/refactor-logs/agent-triggers-daemon-flow.md`

## Reason For Changes

- Clarified `TriggerDaemon.tick` by separating periodic-trigger filtering, dedup checks, due-trigger collection, and heartbeat cadence checks.
- Added focused coverage for event-driven trigger skipping, per-agent deduplication, and fourth-tick heartbeat checks.
- Replaced `Path.rename` with `Path.replace` in `TriggerStore._save` so updates overwrite existing JSON files on Windows as intended.

## Behavior Preservation Notes

- `on_message` and `webhook` triggers are still skipped by periodic ticks.
- Dedup still uses `DEDUP_WINDOW_SEC` and remains per-agent.
- Heartbeat events are still appended only every fourth tick.
- Returned event order remains due trigger events before heartbeat events.
- `_fire` mutation, wake logging, and event shape are unchanged.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_agent_triggers.py`: passed, `3 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- Trigger validation and SSRF URL checks remain separate flows and were not changed.
- The daemon async loop still catches broad exceptions; a later operations slice can refine loop error reporting without changing trigger firing behavior.
