<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:58:49Z" -->

# Plaza Interjection Revised Plan Prompt Flow - Before

## Scope

LLM-backed revised-plan prompt construction inside `PlazaEngine.handle_live_interjection`.

## Current Flow

1. After nominated and supplementary replies, the flow collects response text inline.
2. It builds `responses_text` from the nominated speaker and extra replies, defaulting to `无回应`.
3. It builds the revised-plan prompt inline from topic, optional goal, user interjection, responses, existing plan JSON, and table contract.
4. `_generate_agent_content` produces `plan_text`.
5. Plan payload, revised-plan message, broadcasts, save, and return happen afterward.

## Behavior To Preserve

- Response formatting remains `agent_name: content`.
- Empty responses still become `无回应`.
- Existing plan is still rendered with `json.dumps(..., ensure_ascii=False)`.
- Revised plan format requirements remain unchanged.
- Plan generation, publishing, broadcasts, save, and return shape remain unchanged.

## Smallest Safe Slice

Extract response formatting and revised-plan prompt construction. Leave LLM call, plan payload, publish, broadcasts, save, and return behavior unchanged.
