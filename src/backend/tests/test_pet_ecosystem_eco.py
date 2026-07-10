# -*- coding: utf-8 -*-
"""PetEcosystem × eco_loop 接入验证测试.

对应 docs/Agent仿生生态运行时todos.md P1-2。

验证目标：PetIntentionAgent（基于 IntentionAgent 基类）在相同输入下，
与前端 pet-behavior.js 的 computeHunger/computeFear 纯函数公式数值一致——
证明 eco_loop 的感知→生理状态→意图仲裁骨架足够通用，能承载宠物场景既有的
"时间驱动饥饿 + 距离驱动恐惧"公式，而不需要改动前端或基类结构。
"""

from __future__ import annotations

import pytest

from agents.pet_ecosystem import (
    PetIntentionAgent,
    _PET_DEFAULTS,
    compute_pet_fear,
    compute_pet_hunger,
)
from agents.runtime.eco_loop import IntentionType


# ── 与 pet-behavior.js computeHunger/computeFear 的固定测试向量比对 ──
# JS: computeHunger(elapsedSec, fullSec) = min(1, max(0, elapsedSec/fullSec))
# JS: computeFear(dist, D0)              = min(1, D0/dist)  (dist<=0 → 1)

HUNGER_VECTORS = [
    (0.0, 20.0, 0.0),
    (10.0, 20.0, 0.5),
    (20.0, 20.0, 1.0),
    (30.0, 20.0, 1.0),   # 超过 full_sec 应 clamp 到 1
    (5.0, 0.0, 1.0),     # full_sec<=0 → 恒 1
]

FEAR_VECTORS = [
    (6.0, 6.0, 1.0),
    (12.0, 6.0, 0.5),
    (3.0, 6.0, 1.0),      # D0/dist > 1 → clamp 到 1
    (0.0, 6.0, 1.0),      # dist<=0 → 恒 1
    (60.0, 6.0, 0.1),
]


class TestFormulaEquivalenceWithFrontend:
    @pytest.mark.parametrize("elapsed,full,expected", HUNGER_VECTORS)
    def test_hunger_matches_frontend_formula(self, elapsed, full, expected):
        assert compute_pet_hunger(elapsed, full) == pytest.approx(expected)

    @pytest.mark.parametrize("dist,d0,expected", FEAR_VECTORS)
    def test_fear_matches_frontend_formula(self, dist, d0, expected):
        assert compute_pet_fear(dist, d0) == pytest.approx(expected)


class TestPetIntentionAgent:
    def _cat_config(self):
        # 复用 _PET_DEFAULTS 与 xiaohu_cat 的真实生产参数
        return {
            "mental_state": {
                "hunger_full_sec": 20,
                "hunt_hunger_threshold": 0.3,
                "fear_scale_D0": 6.0,
                "f_escape": 0.55,
                "f_calm": 0.35,
            }
        }

    def test_uses_pet_defaults_when_config_matches(self):
        """确认 PetIntentionAgent 用的默认参数与 _PET_DEFAULTS 一致（不会漂移出两套配置）."""
        cat_ms = self._cat_config()["mental_state"]
        default_ms = _PET_DEFAULTS["mental_state"]
        assert cat_ms == default_ms

    def test_pet_tick_hunger_drives_forage(self):
        agent = PetIntentionAgent("xiaohu_cat", self._cat_config())
        # elapsed=20, full=20 → hunger=1.0（远超 hunt_hunger_threshold=0.3），无威胁 → forage
        intention = agent.pet_tick(elapsed_sec=20.0, nearest_threat_dist=100.0)
        assert intention.type == IntentionType.FORAGE
        assert agent.mental_state.hunger == pytest.approx(1.0)

    def test_pet_tick_fear_overrides_hunger(self):
        agent = PetIntentionAgent("squeak_mouse", self._cat_config())
        # 饿（hunger 高）但威胁很近（fear 高）→ avoid 应压制 forage
        intention = agent.pet_tick(elapsed_sec=20.0, nearest_threat_dist=1.0)
        assert agent.mental_state.fear == pytest.approx(1.0)
        assert intention.type == IntentionType.AVOID

    def test_pet_tick_low_hunger_low_fear_rests(self):
        agent = PetIntentionAgent("xiaohu_cat", self._cat_config())
        intention = agent.pet_tick(elapsed_sec=1.0, nearest_threat_dist=100.0)
        assert agent.mental_state.hunger < 0.3
        assert intention.type == IntentionType.REST_EXPLORE

    def test_thresholds_loaded_from_pet_config(self):
        custom_config = {
            "mental_state": {
                "hunger_full_sec": 10,
                "hunt_hunger_threshold": 0.9,   # 故意设高阈值
                "fear_scale_D0": 6.0,
                "f_escape": 0.55,
                "f_calm": 0.35,
            }
        }
        agent = PetIntentionAgent("xiaohu_cat", custom_config)
        assert agent.thresholds.hunger_threshold == pytest.approx(0.9)
        # elapsed=10/full=10 → hunger=1.0，仍然超过阈值 0.9 → forage
        intention = agent.pet_tick(elapsed_sec=10.0, nearest_threat_dist=100.0)
        assert intention.type == IntentionType.FORAGE
