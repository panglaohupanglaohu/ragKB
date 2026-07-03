# -*- coding: utf-8 -*-
"""Similarity Engine — pluggable similarity computation strategies.

Provides:
  - Tokenization helpers
  - Cosine similarity (TF-IDF weighted)
  - Jaccard similarity
  - Normalized Levenshtein similarity
  - Exact match
  - Custom callable support

All strategies return a float in [0.0, 1.0] where 1.0 = identical.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Callable, Dict, List, Optional, Set

from .merge_models import MergeItem, MergeStrategy


# ── Tokenization ────────────────────────────────────────────────

_WORD_RE = re.compile(r"\w+")

def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase word tokens."""
    return _WORD_RE.findall(text.lower())


def token_set(text: str) -> Set[str]:
    """Return set of unique word tokens."""
    return set(tokenize(text))


def token_counter(text: str) -> Counter:
    """Return Counter of word tokens (for TF-IDF weighting)."""
    return Counter(tokenize(text))


# ── Cosine Similarity (TF-IDF weighted) ─────────────────────────

def _cosine_similarity(items: List[MergeItem]) -> List[float]:
    """Compute pairwise cosine similarity between consecutive items in cluster."""
    if len(items) < 2:
        return [1.0]

    scores: List[float] = []
    for i in range(len(items) - 1):
        a_tokens = token_counter(items[i].content)
        b_tokens = token_counter(items[i + 1].content)

        all_keys = set(a_tokens.keys()) | set(b_tokens.keys())
        if not all_keys:
            scores.append(1.0)
            continue

        dot = sum(a_tokens.get(k, 0) * b_tokens.get(k, 0) for k in all_keys)
        norm_a = math.sqrt(sum(v ** 2 for v in a_tokens.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in b_tokens.values()))

        if norm_a == 0 and norm_b == 0:
            scores.append(1.0)
        elif norm_a == 0 or norm_b == 0:
            scores.append(0.0)
        else:
            scores.append(dot / (norm_a * norm_b))
    return scores


# ── Jaccard Similarity ──────────────────────────────────────────

def _jaccard_similarity(items: List[MergeItem]) -> List[float]:
    """Compute pairwise Jaccard similarity between consecutive items."""
    if len(items) < 2:
        return [1.0]

    scores: List[float] = []
    for i in range(len(items) - 1):
        a_set = token_set(items[i].content)
        b_set = token_set(items[i + 1].content)

        union = a_set | b_set
        if not union:
            scores.append(1.0)
            continue

        intersection = a_set & b_set
        scores.append(len(intersection) / len(union))
    return scores


# ── Levenshtein Similarity (normalized) ─────────────────────────

def _levenshtein_distance(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        a, b = b, a

    if len(b) == 0:
        return len(a)

    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr_row = [i]
        for j, cb in enumerate(b, 1):
            insertions = prev_row[j] + 1
            deletions = curr_row[j - 1] + 1
            substitutions = prev_row[j - 1] + (0 if ca == cb else 1)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def _levenshtein_similarity(items: List[MergeItem]) -> List[float]:
    """Compute normalized Levenshtein similarity (1 - norm_dist)."""
    if len(items) < 2:
        return [1.0]

    scores: List[float] = []
    for i in range(len(items) - 1):
        a = items[i].content
        b = items[i + 1].content
        max_len = max(len(a), len(b))
        if max_len == 0:
            scores.append(1.0)
            continue
        dist = _levenshtein_distance(a, b)
        scores.append(1.0 - dist / max_len)
    return scores


# ── Exact Match ─────────────────────────────────────────────────

def _exact_similarity(items: List[MergeItem]) -> List[float]:
    """Exact string match — 1.0 if identical, 0.0 otherwise."""
    if len(items) < 2:
        return [1.0]

    scores: List[float] = []
    for i in range(len(items) - 1):
        scores.append(1.0 if items[i].content == items[i + 1].content else 0.0)
    return scores


# ── Strategy Dispatch ───────────────────────────────────────────

_SIMILARITY_FNS: Dict[MergeStrategy, Callable] = {
    MergeStrategy.COSINE: _cosine_similarity,
    MergeStrategy.JACCARD: _jaccard_similarity,
    MergeStrategy.LEVENSHTEIN: _levenshtein_similarity,
    MergeStrategy.EXACT: _exact_similarity,
}


# ── Main Engine Class ───────────────────────────────────────────

class SimilarityEngine:
    """Computes similarity between MergeItems using pluggable strategies.

    Usage:
        engine = SimilarityEngine()
        score = engine.pair_score(item_a, item_b, strategy=MergeStrategy.JACCARD)
        cluster_scores = engine.cluster_scores(items, strategy=MergeStrategy.COSINE)

        # Custom strategy
        def my_sim(a: MergeItem, b: MergeItem) -> float:
            return 0.5
        engine.register_custom_strategy("my_sim", my_sim)
    """

    def __init__(self):
        self._custom_strategies: Dict[str, Callable[[MergeItem, MergeItem], float]] = {}

    def register_custom_strategy(
        self, name: str, fn: Callable[[MergeItem, MergeItem], float]
    ) -> None:
        """Register a custom similarity function.

        Args:
            name: Strategy name (used with MergeStrategy.CUSTOM + config['custom_name']).
            fn: Callable that takes two MergeItems and returns float in [0.0, 1.0].
        """
        self._custom_strategies[name] = fn

    def pair_score(
        self,
        a: MergeItem,
        b: MergeItem,
        strategy: MergeStrategy = MergeStrategy.JACCARD,
        custom_fn: Optional[Callable[[MergeItem, MergeItem], float]] = None,
        config: Optional[Dict] = None,
    ) -> float:
        """Compute similarity score between two items.

        Args:
            a, b: Items to compare.
            strategy: Which built-in strategy to use.
            custom_fn: Direct custom callable (takes priority over registered ones).
            config: Optional config dict (e.g., {'custom_name': 'my_strategy'}).

        Returns:
            Float in [0.0, 1.0].
        """
        if strategy == MergeStrategy.CUSTOM:
            if custom_fn is not None:
                return max(0.0, min(1.0, custom_fn(a, b)))
            if config:
                name = config.get("custom_name", "")
                if name in self._custom_strategies:
                    return max(0.0, min(1.0, self._custom_strategies[name](a, b)))
            # Fallback to jaccard if no custom fn provided
            return max(0.0, min(1.0, _jaccard_similarity([a, b])[0]))

        fn = _SIMILARITY_FNS.get(strategy)
        if fn is None:
            fn = _SIMILARITY_FNS[MergeStrategy.JACCARD]
        return max(0.0, min(1.0, fn([a, b])[0]))

    def cluster_scores(
        self,
        items: List[MergeItem],
        strategy: MergeStrategy = MergeStrategy.JACCARD,
        custom_fn: Optional[Callable[[MergeItem, MergeItem], float]] = None,
        config: Optional[Dict] = None,
    ) -> List[float]:
        """Compute pairwise similarity scores for a cluster of items.

        For items [A, B, C], returns [sim(A,B), sim(B,C)].
        Returns [1.0] for single-item clusters.

        Args:
            items: Ordered list of items in the cluster.
            strategy: Similarity strategy.
            custom_fn: Custom callable (for CUSTOM strategy).
            config: Optional config dict.

        Returns:
            List of similarity scores.
        """
        if strategy == MergeStrategy.CUSTOM:
            if len(items) < 2:
                return [1.0]
            scores = []
            for i in range(len(items) - 1):
                s = self.pair_score(
                    items[i], items[i + 1],
                    strategy=strategy, custom_fn=custom_fn, config=config,
                )
                scores.append(s)
            return scores

        fn = _SIMILARITY_FNS.get(strategy, _SIMILARITY_FNS[MergeStrategy.JACCARD])
        return fn(items)

    @staticmethod
    def cluster_avg_similarity(items: List[MergeItem], scores: List[float]) -> float:
        """Compute average similarity across a cluster."""
        if not scores:
            return 1.0
        return sum(scores) / len(scores)
