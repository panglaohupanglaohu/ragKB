<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:31:18Z" -->

# API Task Submit Flow - Before

## Scope

Core flow: `submit_task` in `src/backend/agents/api.py`.

## Entrypoint

`POST /api/v1/agent-config/teams/{team_id}/tasks` calls `submit_task(team_id, req)`.

## Current Flow

1. Validate that the team exists.
2. If `req.agent_id` is provided, validate that the agent exists in the team.
3. Get the task engine with `_te()`.
4. Start the task engine if it is not running.
5. Check Token Factory readiness.
6. Create an `AgentTask` from request fields.
7. Generate workflow steps with `_generate_workflow`.
8. Store workflow in `task.metadata["workflow"]` when present.
9. Seed project context into the task pipeline directory.
10. Write a `task_init` handoff file.
11. Submit the task to `TaskEngine`.
12. If Token Factory is not ready, check direct DeepSeek credentials.
13. If neither backend is available, mark `task.metadata["token_factory_error"]` and return the queued task.
14. If workflow exists, start the first active workflow step:
    - resolve `code_implementation` skill config
    - resolve the assigned agent
    - create a session id
    - build step prompt
    - start Claude session
    - emit `step_started`
15. Mark the task running and start the harness monitor.
16. Return `task.to_dict()`.

## Existing Boundaries

- `TaskEngine` owns task storage and status transitions.
- API layer owns request validation, workflow initialization, handoff writing, and first-step auto-start.
- Token Factory and DeepSeek credential checks are runtime preflight concerns inside the API flow.

## Behavior To Preserve

- The endpoint still returns `201`.
- Returned task payload shape stays `task.to_dict()`.
- A missing LLM backend still creates/queues the task and returns it with `metadata["token_factory_error"]`.
- Direct DeepSeek credentials still allow execution when Token Factory is unavailable.
- Workflow generation, context seeding, handoff writing, first-step session launch, pipeline event emission, and harness monitor startup keep the same order relative to task submission.

## Smallest Safe Refactor Slice

Extract helper functions around the existing steps without changing public request/response contracts or task-engine behavior.
