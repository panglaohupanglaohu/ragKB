# -*- coding: utf-8 -*-
"""Similarity Merge Plugin — Core Data Models.

Defines the data structures for the asynchronous similarity merge plugin:
  - MergeRule: User-defined merge rule (strategy, threshold, action)
  - MergeItem: An item to be compared and potentially merged
  - MergeResult: The result of merging a group of similar items
  - MergeStrategy: Enum of built-in similarity strategies
  - MergeAction: Enum of built-in merge actions
  - MergeJob: A batch job submitted for async merging
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class MergeStrategy(str, Enum):
    """Built-in similarity computation strategies."""
    COSINE = "cosine"             # Cosine similarity (TF-IDF weighted)
    JACCARD = "jaccard"           # Jaccard similarity on token sets
    LEVENSHTEIN = "levenshtein"   # Normalized Levenshtein distance
    EXACT = "exact"               # Exact string match
    CUSTOM = "custom"             # User-provided callable


class MergeAction(str, Enum):
    """Built-in merge actions that define how to combine similar items."""
    KEEP_LONGEST = "keep_longest"         # Keep the longest item, discard rest
    KEEP_SHORTEST = "keep_shortest"       # Keep the shortest item, discard rest
    CONCATENATE = "concatenate"           # Concatenate all items (dedup)
    PICK_FIRST = "pick_first"             # Keep first item by arrival order
    PICK_BEST_SCORE = "pick_best_score"   # Keep item with highest confidence/score
    CUSTOM = "custom"                     # User-provided callable


# ── Core Data Classes ──────────────────────────────────────────


@dataclass
class MergeItem:
    """A single item submitted for similarity-based merging.

    Attributes:
        item_id: Unique identifier (auto-generated if not provided).
        content: The text content to compare.
        metadata: Arbitrary key-value metadata (e.g., confidence, source).
        group_key: Optional grouping key — items with different group_keys
                   are never merged together.
    """
    content: str
    item_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)
    group_key: Optional[str] = None

    def __getitem__(self, index: int) -> "MergeItem":
        """Legacy compatibility for tests that unwrap singleton clusters."""
        if index == 0:
            return self
        raise IndexError(index)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "content": self.content,
            "metadata": self.metadata,
            "group_key": self.group_key,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MergeItem":
        return cls(
            item_id=d.get("item_id", str(uuid.uuid4())[:8]),
            content=d["content"],
            metadata=d.get("metadata", {}),
            group_key=d.get("group_key"),
        )


@dataclass
class MergeRule:
    """A user-defined rule for how to merge similar items.

    Attributes:
        rule_id: Unique rule identifier.
        name: Human-readable name.
        strategy: Similarity strategy to use.
        threshold: Similarity threshold (0.0–1.0). Items with similarity
                   >= threshold are considered "similar" and will be merged.
        action: Merge action to apply to similar items.
        custom_similarity_fn: Optional callable(item_a, item_b) -> float
                              used when strategy=CUSTOM.
        custom_merge_fn: Optional callable(items: List[MergeItem]) -> str
                         used when action=CUSTOM.
        enabled: Whether this rule is active.
        config: Additional strategy/action-specific configuration.
    """
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Default Merge Rule"
    strategy: MergeStrategy = MergeStrategy.JACCARD
    threshold: float = 0.75
    action: MergeAction = MergeAction.KEEP_LONGEST
    custom_similarity_fn: Optional[Callable[[MergeItem, MergeItem], float]] = None
    custom_merge_fn: Optional[Callable[[List[MergeItem]], str]] = None
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "strategy": self.strategy.value,
            "threshold": self.threshold,
            "action": self.action.value,
            "enabled": self.enabled,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MergeRule":
        return cls(
            rule_id=d.get("rule_id", str(uuid.uuid4())[:8]),
            name=d.get("name", "Default Merge Rule"),
            strategy=MergeStrategy(d.get("strategy", "jaccard")),
            threshold=float(d.get("threshold", 0.75)),
            action=MergeAction(d.get("action", "keep_longest")),
            enabled=d.get("enabled", True),
            config=d.get("config", {}),
        )


@dataclass
class MergeResult:
    """The result of merging a cluster of similar items.

    Attributes:
        result_id: Unique result identifier.
        rule_id: The rule that produced this result.
        merged_content: The merged output text.
        source_items: The items that were merged together.
        similarity_scores: Pairwise similarity scores within the cluster.
        cluster_avg_similarity: Average similarity across the cluster.
        action: The action that was applied.
    """
    result_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    rule_id: str = ""
    merged_content: str = ""
    source_items: List[MergeItem] = field(default_factory=list)
    similarity_scores: List[float] = field(default_factory=list)
    cluster_avg_similarity: float = 0.0
    action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "rule_id": self.rule_id,
            "merged_content": self.merged_content,
            "source_count": len(self.source_items),
            "source_items": [it.to_dict() for it in self.source_items],
            "cluster_avg_similarity": round(self.cluster_avg_similarity, 4),
            "action": self.action,
        }


@dataclass
class MergeJob:
    """A batch job submitted for asynchronous merge processing.

    Attributes:
        job_id: Unique job identifier.
        rules: List of rules to apply (in order).
        items: Items to merge.
        status: Current job status.
        results: Results populated after processing.
        created_at: ISO timestamp of creation.
        completed_at: ISO timestamp of completion.
    """
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    rules: List[MergeRule] = field(default_factory=list)
    items: List[MergeItem] = field(default_factory=list)
    status: str = "pending"  # pending | processing | completed | failed
    results: List[MergeResult] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "rules": [r.to_dict() for r in self.rules],
            "item_count": len(self.items),
            "status": self.status,
            "result_count": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }
