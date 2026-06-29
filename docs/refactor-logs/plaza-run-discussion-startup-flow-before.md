<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:27:43Z" -->

# Plaza Run Discussion Startup Flow - Before

## Scope

First slice of `PlazaEngine.run_discussion` in `src/backend/agents/plaza_engine.py`.

## Current Flow

1. Look up plaza by ID.
2. Return `None` when plaza is missing.
3. Look up discussion by ID.
4. Return `None` when discussion is missing.
5. Return the discussion unchanged when status is not `open`.
6. Move the discussion to `in_progress` and stamp `started_at`.
7. Sleep briefly so SSE subscribers can connect.
8. Broadcast `discussion_start`.
9. Resolve participants, moderator, and sorted speakers.
10. If no chat function is configured, run the simulated discussion, save the plaza, and return.
11. Otherwise continue into LLM-backed opening, debate, summary, and closing flow.

## Behavior To Preserve

- Missing plaza/discussion return behavior is unchanged.
- Non-open discussions are returned unchanged.
- Status/timestamp setup happens before broadcasting and simulated execution.
- `discussion_start` payload is unchanged.
- Moderator and speaker resolution are unchanged.
- No-LLM path still delegates to `_run_simulated`, saves the plaza, and returns the discussion.
- LLM-backed debate and final summary logic are not changed in this slice.

## Smallest Safe Refactor Slice

Extract helpers for loading runnable discussion state, marking discussion started, broadcasting start, resolving discussion roles, and no-LLM simulated execution. Leave the rest of `run_discussion` intact.
