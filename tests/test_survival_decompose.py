# -*- coding: utf-8 -*-
"""T_i 根上的 skill/协作/残差分解单测."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from sandbox.survival_decompose import (  # noqa: E402
    attach_attribution_to_ranking,
    decompose_survival_from_timeline,
)
from sandbox.eco_drill import Creature, EcoDrill  # noqa: E402


def test_shares_sum_to_one():
    timeline = {
        "steps": [
            {
                "actions": {
                    "a1": {
                        "can_serve": True, "outcome": "success",
                        "followed": False, "shared_to": None,
                        "survival_ticks": 1,
                    },
                    "a2": {
                        "can_serve": False, "outcome": "idle",
                        "followed": False, "shared_to": "a1",
                        "survival_ticks": 1,
                    },
                }
            },
            {
                "actions": {
                    "a1": {
                        "can_serve": True, "outcome": "success",
                        "followed": False, "shared_to": None,
                        "survival_ticks": 2,
                    },
                    "a2": {
                        "can_serve": False, "outcome": "miss",
                        "followed": True, "shared_to": None,
                        "survival_ticks": 2,
                    },
                }
            },
        ]
    }
    ranking = [
        {"agent_id": "a1", "survival_ticks": 2, "population": "t1"},
        {"agent_id": "a2", "survival_ticks": 2, "population": "t1"},
    ]
    att = decompose_survival_from_timeline(timeline, ranking)
    for aid in ("a1", "a2"):
        s = att[aid]["skill_share"] + att[aid]["collab_share"] + att[aid]["residual_share"]
        assert abs(s - 1.0) < 1e-6
        assert att[aid]["T_i"] == 2
    # a1 帧1 收到分享→collab；帧2 skill 成功 → 约 50/50
    assert att["a1"]["skill_share"] == 0.5
    assert att["a1"]["collab_share"] == 0.5
    # a2 帧1 给出分享(不计入 recv)、帧2 follow soft → collab 至少一半
    assert att["a2"]["collab_share"] >= 0.5


def test_receive_share_is_collab():
    timeline = {
        "steps": [{
            "actions": {
                "giver": {"can_serve": True, "outcome": "success", "shared_to": "recv", "followed": False},
                "recv": {"can_serve": False, "outcome": "idle", "shared_to": None, "followed": False},
            }
        }]
    }
    ranking = [
        {"agent_id": "recv", "survival_ticks": 1},
        {"agent_id": "giver", "survival_ticks": 1},
    ]
    att = decompose_survival_from_timeline(timeline, ranking)
    assert att["recv"]["collab_share"] == 1.0
    assert att["recv"]["counts"]["collab_recv"] == 1


def test_attach_to_ranking():
    att = {
        "x": {
            "skill_share": 0.5, "collab_share": 0.3, "residual_share": 0.2,
            "explain": "test",
        }
    }
    rows = attach_attribution_to_ranking(
        [{"agent_id": "x", "survival_ticks": 10}], att
    )
    assert rows[0]["attr_skill_share"] == 0.5
    assert rows[0]["attr_collab_share"] == 0.3


def test_end_to_end_drill_has_attribution():
    """小生境跑几步，结果可分解且份额和为 1."""
    creatures = [
        Creature(agent_id="s1", role="dev", population="A",
                 skill_genome=["coding"], skill_proficiency={"coding": 0.9}),
        Creature(agent_id="s2", role="dev", population="A",
                 skill_genome=["coding"], skill_proficiency={"coding": 0.8}),
        Creature(agent_id="c1", role="ops", population="B",
                 skill_genome=["other"], skill_proficiency={"other": 0.9}),
    ]
    drill = EcoDrill(
        creatures=creatures,
        demanded_skills=["coding"],
        seed=7,
        abundance=1.2,
        predator_pressure=0,
        drift_prob=0,
        niche_capacity=0,
        blind_learning_rate=0.05,
        genome_carry_cost=0,
        record_timeline=True,
    )
    for _ in range(30):
        if drill.is_extinct():
            break
        drill.step()
    ranking = drill.survival_ranking()
    att = decompose_survival_from_timeline(drill.timeline, ranking)
    assert len(att) == len(ranking)
    for aid, row in att.items():
        if row["T_i"] > 0:
            assert abs(row["skill_share"] + row["collab_share"] + row["residual_share"] - 1.0) < 1e-3
