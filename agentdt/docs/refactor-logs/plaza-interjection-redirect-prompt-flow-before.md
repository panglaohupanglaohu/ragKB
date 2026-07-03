<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:51:28Z" -->

# Plaza Interjection Redirect Prompt Flow - Before

## Scope

LLM-backed moderator redirect prompt construction inside `PlazaEngine.handle_live_interjection`.

## Current Flow

1. The LLM-backed branch picks a candidate speaker.
2. It builds candidate lines inline from up to eight speakers.
3. It builds the redirect prompt inline with topic, current round, recent discussion, user interjection, candidate list, and strict `REPLY`/`NEXT` output contract.
4. It sends that prompt to `_generate_agent_content`.
5. Parsing, nomination prefix, message publishing, follow-up replies, plan revision, broadcasts, save, and return happen afterward.

## Behavior To Preserve

- Candidate list still includes at most eight speakers.
- Recent discussion still uses `_format_recent(disc, limit=8)`.
- Prompt still requires exactly `REPLY` and `NEXT` lines.
- Downstream parsing and message publication remain unchanged.

## Smallest Safe Slice

Extract only redirect prompt construction. Leave candidate selection, LLM call, parsing, message publication, replies, plan revision, broadcasts, and persistence unchanged.
