# -*- coding: utf-8 -*-
"""物竞/SECS 静态冒烟：无需浏览器，校验关键入口与模块可导入.

覆盖 todos XR-1.5 / XV-8.3 中可自动化部分。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src" / "backend"
sys.path.insert(0, str(BACKEND))


def test_digital_twin_html_has_secs_and_office_modes():
    html = (ROOT / "src/frontend/Agent-digital-twin.html").read_text(encoding="utf-8")
    assert "rp-secs" in html
    assert "rp-eco" in html
    assert "office3d" in html or "office-mode" in html
    assert "eco2-run-launch" in html
    assert "eco2-run-task-wrap" in html  # 已挂接任务区


def test_secs_core_and_eco_console_parse():
    for rel in (
        "src/frontend/js/digital-twin/secs-core.js",
        "src/frontend/js/digital-twin/eco-console.js",
        "src/frontend/js/office/office-state.js",
        "src/frontend/js/office/eco-replay.js",
    ):
        p = ROOT / rel
        assert p.is_file(), rel
        text = p.read_text(encoding="utf-8")
        assert len(text) > 100


def test_eco_modules_import():
    from sandbox.eco_drill import EcoDrill, Creature  # noqa: F401
    from sandbox.survival_decompose import decompose_survival_from_timeline  # noqa: F401
    from sandbox.plan_eco_bridge import compile_plan_to_habitat_contract  # noqa: F401
    from sandbox.skill_identity import canonicalize  # noqa: F401
    from sandbox.skill_integration import build_integration_report  # noqa: F401


def test_eco_runtime_config_has_habitat_era_task_coupling():
    from agents.runtime.eco_runtime_config import get_eco_runtime_config
    cfg = get_eco_runtime_config().get_config()
    assert "habitat" in cfg
    assert "era" in cfg
    assert "task_coupling" in cfg
    assert "abundance" in cfg["habitat"]
    assert "predator_pressure" in cfg["habitat"]
    assert "drift_prob" in cfg["habitat"]


def test_pet_config_has_slider_meta():
    html = (ROOT / "src/frontend/pet-config.html").read_text(encoding="utf-8")
    assert "RUNTIME_FIELD_CTRL" in html
    assert "runtimeRangeSync" in html
    assert "type=\"range\"" in html or "type='range'" in html or "type=range" in html or "input type=\"range\"" in html


def test_office_state_eco_env_reducer():
    # office-state is ES module — check source contract
    src = (ROOT / "src/frontend/js/office/office-state.js").read_text(encoding="utf-8")
    assert "case 'eco_env'" in src
    assert "ecoEnv" in src
    assert "forage_hits" in src


def test_office_scene_habitat_layer():
    src = (ROOT / "src/frontend/js/office/office-scene.js").read_text(encoding="utf-8")
    assert "habitatLayer" in src
    assert "ensureNicheTotem" in src
    assert "spawnForageSpark" in src


def test_pet_config_search_and_collapse():
    html = (ROOT / "src/frontend/pet-config.html").read_text(encoding="utf-8")
    assert "runtimeSearchFilter" in html
    assert "runtimeToggleSection" in html
    assert "runtime-search" in html
