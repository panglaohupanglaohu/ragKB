<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:40:26Z" -->

# API Task Workflow Start Flow - Before

## Scope

Core flow: workflow step session launch boundaries in `src/backend/agents/api.py`.

## Entrypoints

- `advance_workflow`
- `run_claude_for_task`
- `resume_blocked_task`

## Current Flow

The API module repeats the same session-start sequence in multiple places:

1. Find the active or resume workflow step.
2. Resolve the `code_implementation` skill config.
3. Resolve the assigned agent from the team.
4. Generate a short session id.
5. Build the step prompt.
6. Call `_start_claude_session`.
7. Write `session_id` back to the workflow step.
8. Persist `task.metadata["workflow"]`.
9. Start the harness monitor.

## Behavior To Preserve

- `run_claude_for_task` still returns `already_running` when the active step already has a `session_id`.
- Missing active step still returns HTTP 400.
- Missing assigned agent in `run_claude_for_task` still returns HTTP 400.
- `resume_blocked_task` still clears `token_factory_error`, starts/resumes the first pending/active/blocked step, starts the monitor, writes `pipeline_resumed`, and returns the same response shape.
- Workflow status semantics are unchanged.

## Smallest Safe Refactor Slice

Extract helpers for active-step lookup, skill config lookup, session launch, and monitor persistence. Apply them to `run_claude_for_task`, `resume_blocked_task`, and the adjacent workflow advancement path without changing route contracts.
