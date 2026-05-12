# -*- coding: utf-8 -*-
"""Merge Engine — asynchronous similarity-based merge processor.

Core engine that:
  1. Accepts MergeItems via an asyncio queue
  2. Groups items by group_key, then by similarity (using a pluggable SimilarityEngine)
  3. Applies MergeActions to each cluster of similar items
  4. Emits MergeResults

Fully async — does not block the main event loop. Designed for independent
deployment as a plugin (wrapped by MergeChannel).
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .merge_models import (
    MergeAction,
    MergeItem,
    MergeJob,
    MergeResult,
    MergeRule,
    MergeStrategy,
)
from .similarity_engine import SimilarityEngine

logger = logging.getLogger("MergeEngine")

# ── Default merge action implementations ──────────────────────

def _merge_keep_longest(items: List[MergeItem]) -> str:
    """Keep the item with the longest content."""
    return max(items, key=lambda it: len(it.content)).content


def _merge_keep_shortest(items: List[MergeItem]) -> str:
    """Keep the item with the shortest content."""
    return min(items, key=lambda it: len(it.content)).content


def _merge_concatenate(items: List[MergeItem]) -> str:
    """Concatenate all items with deduplication."""
    seen: set = set()
    parts = []
    for it in items:
        stripped = it.content.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            parts.append(stripped)
    return "\n---\n".join(parts)


def _merge_pick_first(items: List[MergeItem]) -> str:
    """Keep the first item by arrival order."""
    return items[0].content if items else ""


def _merge_pick_best_score(items: List[MergeItem]) -> str:
    """Keep item with highest confidence/score in metadata."""
    best = max(
        items,
        key=lambda it: float(it.metadata.get("score", it.metadata.get("confidence", 0.0))),
    )
    return best.content


_MERGE_FNS: Dict[MergeAction, Callable] = {
    MergeAction.KEEP_LONGEST: _merge_keep_longest,
    MergeAction.KEEP_SHORTEST: _merge_keep_shortest,
    MergeAction.CONCATENATE: _merge_concatenate,
    MergeAction.PICK_FIRST: _merge_pick_first,
    MergeAction.PICK_BEST_SCORE: _merge_pick_best_score,
}


# ── Clustering logic ──────────────────────────────────────────

def _cluster_items(
    items: List[MergeItem],
    rule: MergeRule,
    sim_engine: SimilarityEngine,
) -> List[List[MergeItem]]:
    """Group items into clusters of similar items (above threshold).

    Uses a transitive-closure approach: if A≈B and B≈C, {A,B,C} form one cluster.
    """
    n = len(items)
    if n <= 1:
        return [list(items)] if items else []

    # Compute all pairwise similarities
    similar_pairs: List[tuple] = []  # (i, j, score)
    for i in range(n):
        for j in range(i + 1, n):
            score = sim_engine.pair_score(
                items[i], items[j],
                strategy=rule.strategy,
                custom_fn=rule.custom_similarity_fn,
                config=rule.config,
            )
            if score >= rule.threshold:
                similar_pairs.append((i, j, score))

    # Union-Find to build clusters
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i, j, _score in similar_pairs:
        union(i, j)

    # Collect clusters
    clusters: Dict[int, List[int]] = {}
    for i in range(n):
        root = find(i)
        clusters.setdefault(root, []).append(i)

    return [[items[i] for i in indices] for indices in clusters.values()]


# ── Main Engine ───────────────────────────────────────────────

class MergeEngine:
    """Asynchronous similarity merge processor.

    Characteristics:
      - Non-blocking: uses asyncio.Queue for item submission
      - Pluggable: SimilarityEngine can be injected or use defaults
      - Observable: produces MergeResults consumable by callers
      - Stateless between jobs: each job is processed independently

    Usage:
        engine = MergeEngine()
        job = MergeJob(rules=[my_rule], items=[item1, item2, item3])
        result_job = await engine.submit(job)
    """

    def __init__(
        self,
        *,
        max_concurrency: int = 5,
        similarity_engine: Optional[SimilarityEngine] = None,
    ):
        self._queue: asyncio.Queue[MergeJob] = asyncio.Queue(maxsize=1000)
        self._sim_engine = similarity_engine or SimilarityEngine()
        self._max_concurrency = max_concurrency
        self._running = False
        self._workers: List[asyncio.Task] = []
        self._results: Dict[str, MergeJob] = {}  # job_id -> completed job
        self._pending: Dict[str, asyncio.Future] = {}  # job_id -> future for awaiting
        self._total_processed = 0
        self._total_results = 0
        self._started_at: Optional[float] = None

    # ── Public API ─────────────────────────────────────────────

    async def submit(self, job: MergeJob) -> MergeJob:
        """Submit a merge job and wait for completion.

        Args:
            job: MergeJob with rules and items populated.

        Returns:
            The same job with status='completed' and results populated.
        """
        job.status = "pending"
        job.created_at = datetime.now(timezone.utc).isoformat()
        self._pending[job.job_id] = asyncio.get_event_loop().create_future()
        await self._queue.put(job)
        logger.info(
            f"[MergeEngine] Job {job.job_id} enqueued "
            f"({len(job.items)} items, {len(job.rules)} rules)"
        )
        result: MergeJob = await self._pending[job.job_id]
        return result

    async def submit_fire_and_forget(self, job: MergeJob) -> str:
        """Submit a job without waiting. Returns job_id immediately.

        Results are stored in self._results and can be retrieved via get_result().
        """
        job.status = "pending"
        job.created_at = datetime.now(timezone.utc).isoformat()
        fut = asyncio.get_event_loop().create_future()
        self._pending[job.job_id] = fut
        await self._queue.put(job)
        return job.job_id

    def get_result(self, job_id: str) -> Optional[MergeJob]:
        """Retrieve a completed job result."""
        return self._results.get(job_id)

    async def start(self) -> None:
        """Start the background workers."""
        if self._running:
            return
        self._running = True
        self._started_at = time.time()
        for i in range(self._max_concurrency):
            task = asyncio.create_task(self._worker(i))
            self._workers.append(task)
        logger.info(f"[MergeEngine] Started {self._max_concurrency} workers")

    async def stop(self) -> None:
        """Stop the background workers gracefully."""
        self._running = False
        # Drain queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        # Cancel workers
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("[MergeEngine] Stopped all workers")

    def stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        uptime = time.time() - self._started_at if self._started_at else 0.0
        return {
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "workers": self._max_concurrency,
            "total_processed": self._total_processed,
            "total_results": self._total_results,
            "results_cached": len(self._results),
            "uptime_seconds": round(uptime, 2),
        }

    # ── Worker ─────────────────────────────────────────────────

    async def _worker(self, worker_id: int) -> None:
        """Background worker that processes jobs from the queue."""
        logger.debug(f"[MergeEngine] Worker {worker_id} started")
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            try:
                job.status = "processing"
                job.results = await self._process_job(job)
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc).isoformat()
                self._total_processed += 1
                self._total_results += len(job.results)
                self._results[job.job_id] = job
                logger.info(
                    f"[MergeEngine] Job {job.job_id} completed — "
                    f"{len(job.results)} results from {len(job.items)} items"
                )
            except Exception as e:
                logger.exception(f"[MergeEngine] Job {job.job_id} failed: {e}")
                job.status = "failed"
                job.error = str(e)

            # Resolve the pending future
            fut = self._pending.pop(job.job_id, None)
            if fut and not fut.done():
                fut.set_result(job)
            self._queue.task_done()

    async def _process_job(self, job: MergeJob) -> List[MergeResult]:
        """Core merge logic for a single job (runs in worker)."""
        results: List[MergeResult] = []

        for rule in job.rules:
            if not rule.enabled:
                continue

            # Partition items by group_key
            groups: Dict[str, List[MergeItem]] = {}
            for item in job.items:
                gk = item.group_key or "__default__"
                groups.setdefault(gk, []).append(item)

            # Process each group independently
            for _gk, group_items in groups.items():
                clusters = _cluster_items(group_items, rule, self._sim_engine)

                for cluster in clusters:
                    if len(cluster) == 0:
                        continue

                    # Compute pairwise similarity scores within cluster
                    scores = self._sim_engine.cluster_scores(
                        cluster,
                        strategy=rule.strategy,
                        custom_fn=rule.custom_similarity_fn,
                        config=rule.config,
                    )
                    avg_sim = self._sim_engine.cluster_avg_similarity(cluster, scores)

                    # Apply merge action
                    merged_content = self._apply_action(cluster, rule)

                    result = MergeResult(
                        rule_id=rule.rule_id,
                        merged_content=merged_content,
                        source_items=cluster,
                        similarity_scores=scores,
                        cluster_avg_similarity=avg_sim,
                        action=rule.action.value,
                    )
                    results.append(result)

        return results

    def _apply_action(self, cluster: List[MergeItem], rule: MergeRule) -> str:
        """Apply the merge action to a cluster of items."""
        if rule.action == MergeAction.CUSTOM and rule.custom_merge_fn is not None:
            return rule.custom_merge_fn(cluster)

        merge_fn = _MERGE_FNS.get(rule.action)
        if merge_fn is None:
            merge_fn = _MERGE_FNS[MergeAction.KEEP_LONGEST]
        return merge_fn(cluster)
