# Task Engine Flow Before Refactor

Last updated: 2026-06-26

## Scope

Core flow: `TaskEngine` task lifecycle and execution flow.

Files traced:

| File | Role |
| --- | --- |
| `src/backend/agents/task_engine.py` | Core task lifecycle, dependency checks, queue worker, executor handoff, evidence and event side effects. |
| `src/backend/agents/task_store.py` | JSON persistence used by `TaskEngine`. |
| `src/backend/agents/domain_events.py` | Event payload classes and task event enum values. |
| `src/backend/agents/event_bus.py` | In-process event delivery used by `_publish_event`. |
| `src/backend/tests/test_task_engine.py` | Existing task lifecycle and event tests. |

## Current Flow

1. `TaskEngine.__init__`
   - Loads persisted tasks from `TaskStore.load_all()`.
   - Creates in-memory task map, queue, callback list, lock, optional executor.

2. Submit path
   - `submit_task(task)` stores the task in `_tasks` under lock.
   - Persists task via `_store.save_task(task)`.
   - Publishes `TASK_CREATED`.
   - If an executor is registered and `_engine_auto_execute` metadata is not `False`, calls `_enqueue_if_ready(task_id)`.

3. Batch submit path
   - `submit_batch(tasks)` stores all tasks under one lock.
   - Then loops through each task and performs the same persist/event/enqueue logic as `submit_task`.

4. Queue path
   - `_enqueue_if_ready(task_id)` only queues pending tasks whose dependencies are all completed.
   - `_worker(name)` pulls task ids while `_running` is true.
   - Worker ignores empty sentinel ids, missing tasks, and non-pending tasks.
   - If dependencies are no longer met, task is marked failed, evidence is recorded, `TASK_FAILED` is published, and dependents are cascaded.
   - Otherwise worker runs `_execute(task)` inside the semaphore.

5. Executor path
   - `_execute(task)` marks task running, sets `started_at`, fires callbacks, and publishes `TASK_STARTED`.
   - If `_executor` exists, it awaits `_executor(task)`.
   - Non-`None` executor result replaces `task.result`; if result is `None` and no previous result exists, a default success message is assigned.
   - On success, task is marked completed, `completed_at` set, callbacks fired, task persisted, evidence recorded, and `TASK_COMPLETED` published.
   - On executor exception, task is marked failed, `error` and `completed_at` set, callbacks fired, task persisted, evidence recorded, `TASK_FAILED` published, and dependents cascaded.
   - If no executor exists, status is reverted from running to pending, `started_at` cleared, a no-executor result message set, callbacks fired, task persisted, and no lifecycle event is emitted for the revert.

6. Manual lifecycle path
   - `start_task(task_id)` transitions pending to running, persists, and publishes `TASK_STARTED`.
   - `complete_task(task_id, result=None)` transitions pending/running to completed, sets default result when needed, persists, records evidence, publishes `TASK_COMPLETED`, and cascades ready dependents.
   - `fail_task(task_id, error="")` transitions pending/running to failed, persists, records evidence, and publishes `TASK_FAILED`.
   - `cancel_task(task_id)` transitions pending/running to cancelled, persists, records evidence, and publishes `TASK_CANCELLED`.
   - All manual methods return `None` when the task id is unknown and otherwise return the task object.

7. Side effects
   - Persistence is direct JSON writes through `TaskStore`.
   - Lifecycle events are created in `_publish_event(kind, task)` and delivered through `get_event_bus().publish(event)`.
   - Terminal task states call `_record_task_evidence(task)` except delete.
   - Dependency cascade only queues dependents when an executor is registered.

## Existing Weaknesses

- Status mutation, timestamp assignment, callback firing, persistence, evidence, and event publication are interleaved in several methods.
- Manual terminal paths duplicate the same state-change pattern.
- `_execute` has distinct success, no-executor, and exception branches, making side-effect ordering easy to disturb.
- Event kind to `EventType` mapping is inline inside `_publish_event`.

## Smallest Safe Refactor Slice

Only extract internal helpers for timestamp generation, callback-aware status mutation, terminal status checks, and event type lookup.

Do not change:

- Public `TaskEngine`/`AgentTask` APIs.
- JSON task format.
- Event names or payloads.
- EvidenceRun payload.
- Queue/dependency behavior.
- Executor invocation behavior.
