<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:39:00Z" -->

# Task Trace Helper Module Flow - Before

## Scope

Task artifact and trace helper logic restored inside `agents.api`.

## Current Flow

1. `agents.api` owns trace context building, JSONL writes, workflow summaries, changed-file extraction, test result extraction, diff preview generation, and artifact attachment.
2. API tests call private `agents.api._...` seams directly.
3. Public trace routes also depend on those private helpers.

## Behavior To Preserve

- Existing private `agents.api._...` helper names remain callable.
- Artifact and trace payloads remain unchanged.
- Existing trace routes keep their response shapes.
- Plaza artifact/trace tests continue to pass.

## Smallest Safe Slice

Move pure helper implementations into `agents.task_trace` while keeping `agents.api` compatibility wrappers.
