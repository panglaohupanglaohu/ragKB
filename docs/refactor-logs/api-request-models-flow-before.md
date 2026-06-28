<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:37:12Z" -->

# API Request Models Flow - Before

## Scope

Core flow: request model boundaries in `src/backend/agents/api.py` for tool editing, skill editing, and digital twin actions.

## Current Flow

The route handlers exist and still implement behavior, but several historical request model names are no longer exported:

- `EditToolRequest`
- `EditSkillRequest`
- `DigitalTwinMoveRequest`
- `DigitalTwinInteractRequest`

Affected handlers currently accept loose dictionaries:

- `edit_tool(team_id, tool_id, req: Dict[str, Any])`
- `edit_skill(team_id, skill_id, req: Dict[str, Any])`
- `dt_move_agent(req: Dict[str, Any])`
- `dt_interact(req: Dict[str, Any])`

## Existing Failure

`src/backend/tests/test_request_models.py` fails because tests and API callers expect those request models to be importable from `agents.api`.

## Behavior To Preserve

- Tool edit updates only the existing allowed fields.
- Skill edit updates only the existing allowed fields and still bumps version when `instructions` is provided.
- Digital twin move still requires both `agent_id` and `room_id`.
- Digital twin interact still accepts input alias `from`.
- Route response shapes stay unchanged.

## Smallest Safe Refactor Slice

Restore explicit Pydantic request models and have handlers convert them back to dictionaries before running the existing logic. This restores the request boundary without changing internal behavior.
