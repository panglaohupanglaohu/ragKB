"""Tests for ModelRouter — 三档路由决策."""
import pytest
from agents.runtime.model_router import ModelRouter, ModelTier, RouteDecision


class TestModelRouter:
    def test_default_starts_at_standard(self):
        r = ModelRouter()
        d = r.route()
        assert d.tier == ModelTier.STANDARD

    def test_budget_exhausted_downgrades_to_economy(self):
        r = ModelRouter(total_budget=10000)
        r.state.used_budget = 9000  # 90% used
        d = r.route()
        assert d.tier == ModelTier.ECONOMY

    def test_budget_recovered_upgrades_back(self):
        r = ModelRouter(total_budget=10000)
        r.state.used_budget = 9500
        r.route()  # → economy
        # Simulate budget recovery
        r.state.used_budget = 3000
        r.state.sticky_remaining = 0
        d = r.route()
        assert d.tier == ModelTier.STANDARD

    def test_consecutive_failures_escalate_tier(self):
        r = ModelRouter(initial_tier=ModelTier.ECONOMY)
        r.record_failure()
        r.record_failure()
        d = r.route()
        assert d.tier == ModelTier.STANDARD

    def test_consecutive_successes_downgrade_tier(self):
        r = ModelRouter(initial_tier=ModelTier.FRONTIER)
        for _ in range(5):
            r.record_success()
        r.state.sticky_remaining = 0
        d = r.route()
        assert d.tier == ModelTier.STANDARD

    def test_sticky_prevents_frequent_switching(self):
        r = ModelRouter(initial_tier=ModelTier.FRONTIER, )
        r.state.sticky_remaining = 3
        # Even with 5 successes, sticky prevents downgrade
        for _ in range(5):
            r.record_success()
        d = r.route()
        assert d.tier == ModelTier.FRONTIER

    def test_failure_resets_success_count(self):
        r = ModelRouter(initial_tier=ModelTier.FRONTIER)
        for _ in range(4):
            r.record_success()
        r.record_failure()
        # Only 4 successes before failure, not enough for downgrade
        assert r.state.consecutive_successes == 0
        assert r.state.consecutive_failures == 1

    def test_success_resets_failure_count(self):
        r = ModelRouter(initial_tier=ModelTier.ECONOMY)
        r.record_failure()
        r.record_success()
        assert r.state.consecutive_failures == 0

    def test_custom_tier_configs(self):
        from agents.runtime.model_router import TierConfig
        tiers = {
            ModelTier.ECONOMY: TierConfig(tier=ModelTier.ECONOMY, model="cheap-model"),
            ModelTier.STANDARD: TierConfig(tier=ModelTier.STANDARD, model="std-model"),
            ModelTier.FRONTIER: TierConfig(tier=ModelTier.FRONTIER, model="premium-model"),
        }
        r = ModelRouter(tiers=tiers, initial_tier=ModelTier.FRONTIER)
        d = r.route()
        assert d.model == "premium-model"

    def test_record_success_accumulates_budget(self):
        r = ModelRouter()
        r.record_success(tokens_used=500)
        assert r.state.used_budget == 500

    def test_get_state_dict(self):
        r = ModelRouter(initial_tier=ModelTier.ECONOMY)
        r.record_failure()
        state = r.get_state_dict()
        assert state["current_tier"] == "economy"
        assert state["consecutive_failures"] == 1

    def test_escalation_chain_economy_to_frontier(self):
        """2 failures → economy to standard, 2 more → standard to frontier."""
        r = ModelRouter(initial_tier=ModelTier.ECONOMY)
        r.record_failure()
        r.record_failure()
        d1 = r.route()
        assert d1.tier == ModelTier.STANDARD
        # Sticky prevents immediate re-evaluation
        r.state.sticky_remaining = 0
        r.record_failure()
        r.record_failure()
        d2 = r.route()
        assert d2.tier == ModelTier.FRONTIER
