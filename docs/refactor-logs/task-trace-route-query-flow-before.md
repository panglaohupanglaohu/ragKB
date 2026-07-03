<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:56:00Z" -->

# Task Trace Route Query Flow - Before

## Scope

Trace route response construction and filtering inside `agents.api`.

## Current Flow

1. `api.py` builds task trace summaries inline.
2. `api.py` builds task trace event payloads inline.
3. Recent trace summary and recent trace event routes filter tasks and events inline.
4. Trace log tail parsing is implemented inline in the route function.

## Behavior To Preserve

- Public trace route response shapes remain unchanged.
- Recent trace summaries still filter by team and source.
- Recent trace events still filter by team, source, and event type.
- Trace log tail still reads global JSONL and filters by event type.

## Smallest Safe Slice

Move pure response construction and filtering helpers to `agents.task_trace`; keep route ownership in `agents.api`.
