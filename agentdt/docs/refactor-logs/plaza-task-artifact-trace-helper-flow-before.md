<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:14:00Z" -->

# Plaza Task Artifact Trace Helper Flow - Before

## Scope

Plaza-origin task artifact collection, terminal-state sync, and trace API helpers in `agents.api`.

## Current Flow

1. Plaza tests still expect task artifact helpers and terminal sync helpers on `agents.api`.
2. Recent API refactors left public trace list/export endpoints in place but removed several helper seams.
3. Missing helpers break task artifact aggregation, evolution item sync, task trace summaries, trace event persistence, and NDJSON export.

## Behavior To Preserve

- Completed plaza tasks still collect changed files, test result, workflow summary, trace context, and patch previews.
- Completed plaza tasks still sync linked evolution items to closed or verify-pending depending on explicit verify tests.
- Failed plaza tasks still mark linked evolution items failed.
- Trace events remain available from memory, per-task JSONL, and global JSONL.
- Existing public trace endpoints keep their response shapes.

## Smallest Safe Slice

Restore the missing helper seam using existing `TaskEngine`, `_pipeline_events`, and `SystemEvolutionChannel.sync_task_outcome`.
