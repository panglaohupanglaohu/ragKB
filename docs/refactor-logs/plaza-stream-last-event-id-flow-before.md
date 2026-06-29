<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:57:28Z" -->

# Plaza Stream Last-Event-ID Flow - Before

## Scope

`Last-Event-ID` parsing inside `plaza_routes.stream_discussion`.

## Current Flow

1. The route reads `request.headers.get("Last-Event-ID", "")`.
2. It defaults `last_seq` to `-1`.
3. It accepts only non-empty digit strings.
4. It converts accepted values with `int`.

## Behavior To Preserve

- Empty header returns `-1`.
- Non-digit header returns `-1`.
- Negative text like `-1` still returns `-1` because it is not digit-only.
- Digit-only values convert with `int`.

## Smallest Safe Slice

Extract only header value parsing.
