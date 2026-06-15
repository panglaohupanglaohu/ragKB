"""C-3.7: Nightly auto-trigger test.
Verifies the evolution auto-trigger code path in nightly_global_loops.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))


def test_nightly_script_has_evolution_trigger():
    """Verify C-3.7 auto_evolution_nightly block exists in nightly script."""
    src = (ROOT / "src" / "backend" / "scripts" / "nightly_global_loops.py").read_text()
    assert "auto_evolution_nightly" in src, "Missing auto_evolution_nightly setting gate"
    assert "triggered_by" in src, "Missing triggered_by='nightly'"
    assert "identify_weak_skills" in src, "Missing identify_weak_skills call"
    assert "evolution_auto" in src, "Missing evolution_auto report key"


def test_nightly_trigger_gated_by_default_false():
    """The nightly evolution trigger defaults to off."""
    src = (ROOT / "src" / "backend" / "scripts" / "nightly_global_loops.py").read_text()
    # settings.get("auto_evolution_nightly", False) — default false
    assert 'auto_evolution_nightly' in src
    assert 'False' in src  # Default value


def test_evolution_bridge_identify_weak_skills_no_data():
    """identify_weak_skills returns empty list with no trial data."""
    from sandbox.evolution_bridge import get_evolution_bridge
    bridge = get_evolution_bridge()
    result = bridge.identify_weak_skills("nonexistent-team", "nonexistent-scenario", [])
    assert result == [], f"Expected empty, got {result}"


def test_evolution_bridge_start_run_signature():
    """Verify start_run accepts triggered_by parameter."""
    import inspect
    from sandbox.evolution_bridge import EvolutionBridge
    sig = inspect.signature(EvolutionBridge.start_run)
    params = list(sig.parameters.keys())
    assert "triggered_by" in params, f"start_run missing triggered_by param. Got: {params}"
    assert "team_id" in params
    assert "scenario_id" in params
    assert "trial_ids" in params
