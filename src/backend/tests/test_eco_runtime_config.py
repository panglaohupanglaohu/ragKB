# -*- coding: utf-8 -*-
"""Eco Runtime Config 测试 — 存储/默认补全/部分更新/恢复默认 + 模块 from_config 读取."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agents.runtime.eco_runtime_config import EcoRuntimeConfig, reset_eco_runtime_config


@pytest.fixture
def tmp_cfg():
    with tempfile.TemporaryDirectory() as d:
        yield EcoRuntimeConfig(config_path=str(Path(d) / "eco_runtime_config.json"))


class TestDefaultsAndMerge:
    def test_get_config_fills_defaults(self, tmp_cfg):
        cfg = tmp_cfg.get_config()
        assert cfg["mental_state"]["fear_escape"] == 0.55
        assert cfg["metabolism"]["health_max"] == 100.0
        assert cfg["learning"]["exploration_half_life"] == 50
        assert cfg["selection"]["dominant_min_streak"] == 3
        assert cfg["mating"]["saturation_threshold"] == 0.7

    def test_all_sections_present(self, tmp_cfg):
        cfg = tmp_cfg.get_config()
        # 核心节 + 生境/经济学/纪元/任务耦合（v2~v4 扩展）
        required = {
            "mental_state", "metabolism", "learning", "selection", "mating",
            "habitat", "drill_economics", "era", "task_coupling",
        }
        assert required.issubset(set(cfg.keys()))


class TestUpdate:
    def test_partial_update_overrides_only_given(self, tmp_cfg):
        tmp_cfg.update({"mental_state": {"fear_escape": 0.8}})
        cfg = tmp_cfg.get_config()
        assert cfg["mental_state"]["fear_escape"] == 0.8
        assert cfg["mental_state"]["fear_calm"] == 0.35  # 未改的保持默认

    def test_unknown_section_ignored(self, tmp_cfg):
        tmp_cfg.update({"bogus_section": {"x": 1}})
        assert "bogus_section" not in tmp_cfg.get_config()

    def test_unknown_key_in_known_section_ignored(self, tmp_cfg):
        tmp_cfg.update({"mating": {"bogus_key": 99, "saturation_threshold": 0.9}})
        cfg = tmp_cfg.get_config()
        assert cfg["mating"]["saturation_threshold"] == 0.9
        assert "bogus_key" not in cfg["mating"]

    def test_update_persists_across_reload(self, tmp_cfg):
        tmp_cfg.update({"metabolism": {"metabolic_rate": 2.5}})
        reloaded = EcoRuntimeConfig(config_path=tmp_cfg._path)
        assert reloaded.get_config()["metabolism"]["metabolic_rate"] == 2.5


class TestReset:
    def test_reset_clears_overrides(self, tmp_cfg):
        tmp_cfg.update({"mental_state": {"fear_escape": 0.99}})
        tmp_cfg.reset()
        assert tmp_cfg.get_config()["mental_state"]["fear_escape"] == 0.55


class TestModuleFromConfigReads:
    def test_intention_thresholds_from_config(self, tmp_path):
        cfg = reset_eco_runtime_config(config_path=str(tmp_path / "c.json"))
        cfg.update({"mental_state": {"hunger_threshold": 0.25}})
        from agents.runtime.eco_loop import IntentionThresholds
        t = IntentionThresholds.from_config()
        assert t.hunger_threshold == 0.25
        reset_eco_runtime_config()  # 还原全局单例，避免影响其它测试

    def test_should_solidify_from_config(self, tmp_path):
        cfg = reset_eco_runtime_config(config_path=str(tmp_path / "c.json"))
        cfg.update({"learning": {"solidify_min_uses": 2}})
        from agents.runtime.health_ledger import should_solidify_from_config
        assert should_solidify_from_config(net_gain=1.0, usage_count=2) is True
        assert should_solidify_from_config(net_gain=1.0, usage_count=1) is False
        reset_eco_runtime_config()

    def test_exploration_rate_from_config(self, tmp_path):
        cfg = reset_eco_runtime_config(config_path=str(tmp_path / "c.json"))
        cfg.update({"learning": {"exploration_base_rate": 0.5}})
        from sandbox.twin_loop import compute_exploration_rate_from_config
        assert compute_exploration_rate_from_config(0) == pytest.approx(0.5)
        reset_eco_runtime_config()
