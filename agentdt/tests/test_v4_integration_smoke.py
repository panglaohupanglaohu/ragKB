"""Integration smoke test: v4 scenario -> trial -> evaluation pipeline."""
import sys
sys.path.insert(0, "src/backend")


def test_scenario_seeds_loadable():
    """All 5 seed scenarios load without errors."""
    from sandbox.scenario_store import get_scenario_store
    store = get_scenario_store()
    scenarios = store.list()
    assert len(scenarios) >= 5, f"Expected >=5 seed scenarios, got {len(scenarios)}"
    for sc in scenarios:
        spec = store.get(sc.scenario_id)
        assert spec is not None, f"Failed to load {sc.scenario_id}"


def test_seed_scenarios_have_required_fields():
    """Each seed scenario has rooms, tasks, chaos phases, and rubric."""
    from sandbox.scenario_store import get_scenario_store
    store = get_scenario_store()
    for sc in store.list():
        spec = store.get(sc.scenario_id)
        assert len(spec.world.rooms) >= 4, f"{sc.scenario_id}: <4 rooms ({len(spec.world.rooms)})"
        assert len(spec.taskflow) >= 6, f"{sc.scenario_id}: <6 tasks ({len(spec.taskflow)})"
        assert len(spec.chaos_script) >= 2, f"{sc.scenario_id}: <2 chaos phases ({len(spec.chaos_script)})"
        assert spec.rubric is not None, f"{sc.scenario_id}: missing rubric"


def test_evolution_run_model():
    """EvolutionRun model creates with all required fields."""
    from sandbox.models import EvolutionRun, EvolutionRunStatus
    run = EvolutionRun(
        team_id="test-team", scenario_id="cs_ticket_surge",
        baseline_trial_id="test-trial", triggered_by="manual",
    )
    assert run.run_id
    assert run.status == EvolutionRunStatus.IDENTIFYING
    assert run.triggered_by == "manual"


def test_ratchet_ledger_blocks_regression():
    """Ratchet ledger: advance works, regression blocked."""
    from agents.ratchet_ledger import get_ratchet_ledger
    ledger = get_ratchet_ledger()
    key = "test:smoke:" + str(abs(hash("ratchet-test")) % 100000)
    ledger.force_reset(key, "test setup")
    r1 = ledger.advance(key, 80.0, evidence={"trial": "t1"}, min_delta=1.0)
    assert r1["advanced"] is True
    r2 = ledger.advance(key, 50.0, evidence={"trial": "t2"}, min_delta=1.0)
    assert r2["advanced"] is False
