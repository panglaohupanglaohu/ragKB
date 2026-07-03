<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-07-01T00:10:00Z" -->

# Task Trace Export Flow - Before

## Scope

NDJSON trace export line generation inside `agents.api`.

## Current Flow

1. `export_traces` gathers recent summaries and events.
2. It formats summary rows with `kind="summary"` inline.
3. It formats event rows with `kind="event"` inline.
4. `export_trace_events` formats event rows inline.

## Behavior To Preserve

- Export routes still return `application/x-ndjson`.
- Summary export rows still include `kind: summary`.
- Event export rows still include `kind: event` in combined trace export.
- Event-only export rows remain raw event payloads.

## Smallest Safe Slice

Move NDJSON line generation into `agents.task_trace`; keep `StreamingResponse` construction in `agents.api`.
