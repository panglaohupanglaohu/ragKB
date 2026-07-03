<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:15:06Z" -->

# Cost Aggregator Parse Flow - Before

## Scope

Core flow: `_parse_allocation_response` in `src/backend/agents/cost_aggregator.py`.

## Current Flow

1. Accept OpenCost allocation response as a list or dict.
2. Read `data` when the response is a dict.
3. Convert dict `data` to values.
4. Iterate each entry.
5. Skip non-dict entries.
6. If all entry values are dicts, treat the entry as wrapped/multi-pod allocation and parse every value.
7. Otherwise parse the entry directly.
8. Swallow per-entry parse exceptions and continue.
9. Sort parsed pods by `total_cost` descending.
10. Return at most `MAX_POD_ITEMS`.

## Behavior To Preserve

- List and dict response formats are both accepted.
- Dict `data` values are iterated.
- Wrapped allocation entries are unwrapped when all values are dictionaries.
- Invalid entries are skipped.
- Per-entry parse failures are ignored.
- Sorting and `MAX_POD_ITEMS` truncation are unchanged.

## Smallest Safe Refactor Slice

Extract response item normalization, wrapped-entry detection, candidate iteration, safe pod parsing, and final sort/limit helpers. Leave `_pod_from_entry` cost extraction behavior unchanged.
