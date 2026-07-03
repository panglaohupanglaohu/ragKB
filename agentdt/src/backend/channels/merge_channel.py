# -*- coding: utf-8 -*-
"""Merge Channel — MarineChannel wrapper for the Similarity Merge Plugin.

Provides an independent, optionally-enabled Channel that wraps the MergeEngine.
Users can submit merge rules and items via the Channel's process_event() method,
or via the dedicated FastAPI routes registered by this plugin.

The Channel is designed for independent deployment:
  - Can be enabled/disabled via configuration
  - Uses asyncio.Queue for non-blocking processing
  - Integrates with the existing ChannelRegistry

Implements the MarineChannel interface:
  - initialize() → starts the MergeEngine workers
  - process_event(event) → accepts merge commands
  - get_status() → reports engine statistics
  - shutdown() → gracefully stops workers
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set

from channels.marine_base import (
    ChannelHealth,
    ChannelMetrics,
    ChannelPriority,
    ChannelStatus,
    MarineChannel,
)
from agents.merge_engine import MergeEngine
from agents.merge_models import (
    MergeAction,
    MergeItem,
    MergeJob,
    MergeResult,
    MergeRule,
    MergeStrategy,
)
from agents.similarity_engine import SimilarityEngine

logger = logging.getLogger("MergeChannel")

# ── Built-in preset rules ─────────────────────────────────────

PRESET_RULES: Dict[str, dict] = {
    "dedup_exact": {
        "rule_id": "preset-dedup-exact",
        "name": "Deduplicate by Exact Match",
        "strategy": "exact",
        "threshold": 1.0,
        "action": "keep_longest",
        "enabled": True,
        "config": {},
    },
    "dedup_jaccard": {
        "rule_id": "preset-dedup-jaccard",
        "name": "Deduplicate by Jaccard (0.85)",
        "strategy": "jaccard",
        "threshold": 0.85,
        "action": "keep_longest",
        "enabled": True,
        "config": {},
    },
    "concat_similar": {
        "rule_id": "preset-concat-similar",
        "name": "Concatenate Similar Items (0.75)",
        "strategy": "jaccard",
        "threshold": 0.75,
        "action": "concatenate",
        "enabled": True,
        "config": {},
    },
    "best_score": {
        "rule_id": "preset-best-score",
        "name": "Pick Best Score (0.60)",
        "strategy": "cosine",
        "threshold": 0.60,
        "action": "pick_best_score",
        "enabled": True,
        "config": {},
    },
}


class MergeChannel(MarineChannel):
    """Async Similarity Merge Plugin — Marine Channel implementation.

    Args:
        max_concurrency: Number of background workers (default 3).
        max_queue_size: Max items in processing queue (default 500).
        enable_presets: Whether to load built-in preset rules (default True).
        **kwargs: Additional config passed to MarineChannel base.
    """

    name = "merge_plugin"
    description = "异步相似度归并插件 — 支持用户自定义合并规则，独立部署"
    version = "1.0.0"
    priority = ChannelPriority.P2
    dependencies: List[str] = []

    def __init__(
        self,
        max_concurrency: int = 3,
        max_queue_size: int = 500,
        enable_presets: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._max_concurrency = max_concurrency
        self._max_queue_size = max_queue_size
        self._enable_presets = enable_presets

        # Internal state
        self._engine: Optional[MergeEngine] = None
        self._sim_engine: Optional[SimilarityEngine] = None
        self._custom_rules: Dict[str, MergeRule] = {}
        self._completed_jobs: Dict[str, MergeJob] = {}

        # Register presets
        if self._enable_presets:
            for _preset_key, rule_dict in PRESET_RULES.items():
                rule = MergeRule.from_dict(rule_dict)
                self._custom_rules[_preset_key] = rule

    # ── MarineChannel Interface ─────────────────────────────────

    def initialize(self) -> bool:
        """Initialize the Merge Channel.

        Creates the SimilarityEngine and MergeEngine, then starts workers.
        Called by the ChannelRegistry at startup.
        """
        try:
            self._sim_engine = SimilarityEngine()
            self._engine = MergeEngine(
                max_concurrency=self._max_concurrency,
                similarity_engine=self._sim_engine,
            )
            # Start workers in the running event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._engine.start())
            else:
                loop.run_until_complete(self._engine.start())

            self._initialized = True
            self._health = ChannelHealth(
                status=ChannelStatus.OK,
                message=f"MergeEngine started with {self._max_concurrency} workers, "
                        f"{len(self._custom_rules)} rules loaded",
            )
            logger.info(f"[MergeChannel] Initialized — {self._health.message}")
            return True
        except Exception as e:
            self._health = ChannelHealth(
                status=ChannelStatus.ERROR,
                message=f"Initialize failed: {e}",
            )
            logger.exception("[MergeChannel] Initialize failed")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Return current Channel status including engine statistics."""
        base = {
            "name": self.name,
            "version": self.version,
            "priority": self.priority.name,
            "initialized": self._initialized,
            "custom_rules_count": len(self._custom_rules),
            "preset_rules_count": len(PRESET_RULES) if self._enable_presets else 0,
            "completed_jobs": len(self._completed_jobs),
        }
        if self._engine:
            base["engine"] = self._engine.stats()
        else:
            base["engine"] = {"running": False}
        return base

    def shutdown(self) -> bool:
        """Gracefully shutdown the MergeEngine workers."""
        try:
            if self._engine:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._engine.stop())
                else:
                    loop.run_until_complete(self._engine.stop())
            self._initialized = False
            self._health = ChannelHealth(
                status=ChannelStatus.OFF,
                message="Shutdown complete",
            )
            logger.info("[MergeChannel] Shutdown complete")
            return True
        except Exception as e:
            logger.exception("[MergeChannel] Shutdown failed")
            return False

    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process an event from the Channel system.

        Supported event types:
            'merge_submit': Submit a merge job (sync or async).
            'merge_rule_add': Add a custom merge rule.
            'merge_rule_remove': Remove a merge rule.
            'merge_rule_list': List all rules.
            'merge_result_get': Get a completed job result.
            'merge_stats': Get engine statistics.

        Args:
            event: Dict with at least {'type': str, ...}.

        Returns:
            Dict with {'ok': bool, ...} and type-specific fields.
        """
        event_type = event.get("type", "")
        handler_map = {
            "merge_submit": self._handle_submit,
            "merge_submit_async": self._handle_submit_async,
            "merge_rule_add": self._handle_rule_add,
            "merge_rule_remove": self._handle_rule_remove,
            "merge_rule_list": self._handle_rule_list,
            "merge_result_get": self._handle_result_get,
            "merge_stats": self._handle_stats,
        }

        handler = handler_map.get(event_type)
        if handler is None:
            return {
                "ok": False,
                "error": f"Unknown event type: {event_type}. "
                         f"Supported: {list(handler_map.keys())}",
            }
        return handler(event)

    # ── Event Handlers ──────────────────────────────────────────

    def _handle_submit(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously submit a merge job (blocks until done)."""
        if not self._engine:
            return {"ok": False, "error": "MergeEngine not initialized"}

        rules = self._resolve_rules(event.get("rule_ids", []))
        if not rules:
            rules = list(self._custom_rules.values())

        items_data = event.get("items", [])
        items = [MergeItem.from_dict(it) if isinstance(it, dict)
                 else MergeItem(content=str(it)) for it in items_data]

        job = MergeJob(rules=rules, items=items)

        try:
            loop = asyncio.get_event_loop()
            result_job = loop.run_until_complete(self._engine.submit(job))
            self._completed_jobs[result_job.job_id] = result_job
            return {
                "ok": True,
                "job": result_job.to_dict(),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _handle_submit_async(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Fire-and-forget submit. Returns job_id immediately."""
        if not self._engine:
            return {"ok": False, "error": "MergeEngine not initialized"}

        rules = self._resolve_rules(event.get("rule_ids", []))
        if not rules:
            rules = list(self._custom_rules.values())

        items_data = event.get("items", [])
        items = [MergeItem.from_dict(it) if isinstance(it, dict)
                 else MergeItem(content=str(it)) for it in items_data]

        job = MergeJob(rules=rules, items=items)

        try:
            loop = asyncio.get_event_loop()
            job_id = loop.run_until_complete(
                self._engine.submit_fire_and_forget(job)
            )
            self._completed_jobs[job_id] = job
            return {"ok": True, "job_id": job_id}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _handle_rule_add(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Add a custom merge rule."""
        rule_dict = event.get("rule", {})
        if not rule_dict:
            return {"ok": False, "error": "Missing 'rule' field"}

        rule = MergeRule.from_dict(rule_dict)
        self._custom_rules[rule.rule_id] = rule
        logger.info(f"[MergeChannel] Rule added: {rule.rule_id} — {rule.name}")
        return {"ok": True, "rule": rule.to_dict()}

    def _handle_rule_remove(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a custom merge rule."""
        rule_id = event.get("rule_id", "")
        if not rule_id:
            return {"ok": False, "error": "Missing 'rule_id'"}

        removed = self._custom_rules.pop(rule_id, None)
        if removed is None:
            return {"ok": False, "error": f"Rule not found: {rule_id}"}
        return {"ok": True, "rule_id": rule_id}

    def _handle_rule_list(self, _event: Dict[str, Any]) -> Dict[str, Any]:
        """List all registered rules."""
        return {
            "ok": True,
            "rules": [r.to_dict() for r in self._custom_rules.values()],
        }

    def _handle_result_get(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Get a completed job result."""
        job_id = event.get("job_id", "")
        if not job_id:
            return {"ok": False, "error": "Missing 'job_id'"}

        # Check local cache first
        job = self._completed_jobs.get(job_id)
        if job is None and self._engine:
            job = self._engine.get_result(job_id)

        if job is None:
            return {"ok": False, "error": f"Job not found or not yet completed: {job_id}"}
        return {"ok": True, "job": job.to_dict()}

    def _handle_stats(self, _event: Dict[str, Any]) -> Dict[str, Any]:
        """Return engine statistics."""
        return {"ok": True, "stats": self.stats()}

    # ── Helpers ─────────────────────────────────────────────────

    def _resolve_rules(self, rule_ids: List[str]) -> List[MergeRule]:
        """Resolve rule_ids to MergeRule objects."""
        rules = []
        for rid in rule_ids:
            if rid in self._custom_rules:
                rules.append(self._custom_rules[rid])
        return rules

    def stats(self) -> Dict[str, Any]:
        """Return combined channel and engine stats."""
        base = self.get_status()
        if self._engine:
            base["engine"] = self._engine.stats()
        return base

    def add_rule(self, rule: MergeRule) -> None:
        """Programmatically add a merge rule."""
        self._custom_rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str) -> bool:
        """Programmatically remove a merge rule."""
        return self._custom_rules.pop(rule_id, None) is not None

    def get_rule(self, rule_id: str) -> Optional[MergeRule]:
        """Get a rule by ID."""
        return self._custom_rules.get(rule_id)

    def list_rules(self) -> List[MergeRule]:
        """List all registered rules."""
        return list(self._custom_rules.values())
