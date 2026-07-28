# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "experiment_agent_memory_adaptation.py"


def _load_exp():
    import sys

    name = "exp_mem_adapt"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod  # required for dataclasses annotation lookup
    spec.loader.exec_module(mod)
    return mod


def test_adaptation_experiment_isolated_and_reports(tmp_path: Path):
    mod = _load_exp()
    report = mod.run_experiment(seeds=[7, 42], max_rounds=2, out_dir=tmp_path)
    assert report["n_runs"] == 2 * 3 * len(mod.GROUPS)
    assert set(report["summary"]["by_group"].keys()) == set(mod.GROUPS)
    jp = tmp_path / "agent-memory-adaptation-report.json"
    mp = tmp_path / "agent-memory-adaptation-report.md"
    assert jp.is_file() and mp.is_file()
    data = json.loads(jp.read_text(encoding="utf-8"))
    assert data["storage"].startswith("isolated")
    assert data["experiment_type"] == "deterministic_memory_mechanism"
    assert "不调用真实 LLM" in data["claim_boundary"]
    assert "stale_definition" in data
    cont = data["summary"]["by_group"]["contaminated_memory"]
    assert "precision_mean" in cont
    assert data["summary"]["by_group"]["full_inheritance"]["first_task_success_mean"] == 1.0
    assert data["summary"]["by_group"]["selective_inheritance"]["first_task_success_mean"] == 1.0
    assert data["summary"]["by_group"]["stale_memory"]["first_task_success_mean"] == 0.0
    assert cont["first_task_success_mean"] == 0.0
    assert cont["negative_transfer_rate"] == 1.0
    assert cont["false_positive_rate_mean"] == 1.0
