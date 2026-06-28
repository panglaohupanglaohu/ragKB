<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:21:51Z" -->

# Cost Aggregator Summary Flow - Before

## Scope

Core flow: `get_summary`, `_aggregate`, and `_compute_trends` in `src/backend/agents/cost_aggregator.py`.

## Current Flow

`get_summary`:

1. Reads cached pod items and window metadata.
2. Returns empty `CostSummary` when no pods exist.
3. Computes total CPU/RAM/PV/network/GPU costs inline.
4. Builds service/environment/team aggregations.
5. Computes trends for the requested aggregation.
6. Builds a `CostSummary` with top 10 aggregations.

`_aggregate`:

1. Resolves a bucket value from labels, then object attribute, then `(unknown)`.
2. Accumulates cost totals, pods, and containers.
3. Converts each bucket into `AggregatedCostItem`.
4. Sorts by total cost descending.

`_compute_trends`:

1. Parses window days, defaulting invalid windows to 7.
2. Groups pods by aggregation label.
3. For each group, distributes costs over simulated daily points.
4. Sorts series by total and returns the top 10.

## Behavior To Preserve

- Empty cache still returns an empty `CostSummary` with window metadata.
- Cost totals and rounding are unchanged.
- Aggregation fallback order is unchanged.
- Summary includes only top 10 service/environment/team aggregations.
- Trend series still simulate daily distribution and return top 10.

## Smallest Safe Refactor Slice

Extract helper functions for cost totals, summary counts, aggregation bucket value, bucket item creation, trend grouping, trend points, and summary construction without changing public return shapes.
