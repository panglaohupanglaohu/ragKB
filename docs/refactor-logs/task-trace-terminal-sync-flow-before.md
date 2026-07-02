<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:47:00Z" -->

# Task Trace Terminal Sync Flow - Before

## Scope

Terminal task state calculation and evolution sync argument construction inside `agents.api._finalize_task_terminal_state`.

## Current Flow

1. `api.py` reads failed workflow steps from the artifact payload.
2. It chooses completed or failed task status.
3. It derives task error and evolution sync status inline.
4. It constructs the `sync_task_outcome` argument list inline.

## Behavior To Preserve

- Failed workflow steps still produce `workflow_failed:<step>`.
- Passing workflows still complete the task with an empty error.
- Evolution sync still receives the same status, changed files, artifact dir, build artifacts, and error.
- `api.py._finalize_task_terminal_state` remains callable.

## Smallest Safe Slice

Move terminal-state calculation and evolution sync argument construction into `agents.task_trace`.
