# -*- coding: utf-8 -*-
"""v4 进化桥测试 — mock LLM 全流程状态机 (C-3.8)."""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


def _make_store_with_weak_skill(tmp: str, team="teamA", trial="t1"):
    """构造一个含弱 skill (coding 20%) 和强 skill (testing 90%) 的 usage 存储."""
    from sandbox.proficiency_store import ProficiencyStore
    from sandbox.models import SkillUsageRecord
    store = ProficiencyStore(usage_dir=Path(tmp) / "u", prof_dir=Path(tmp) / "p")
    records = []
    for i in range(10):
        records.append(SkillUsageRecord(
            agent_id="a1", agent_role="dev", skill_name="coding", step_index=i,
            outcome="success" if i < 2 else "failure", reward_delta=0.1,
            failure_reason="" if i < 2 else "low_proficiency: coding 熟练度不足"))
    for i in range(10):
        records.append(SkillUsageRecord(
            agent_id="a2", agent_role="qa", skill_name="testing", step_index=i,
            outcome="success" if i < 9 else "failure", reward_delta=0.3,
            failure_reason="" if i < 9 else "execution_miss"))
    store.append_usages(trial, records)
    store.update_from_trial(team, trial)
    return store


def _isolate_ratchet(tmp):
    """G4-3 接线后 apply_winner 会写棘轮账本 — 测试重定向到临时目录."""
    from agents.ratchet_ledger import reset_ratchet_ledger
    return reset_ratchet_ledger(ledger_file=Path(tmp) / "ratchet_ledger.json")


def _make_bridge(store, ab_results=None, budget=200000, tmp=None):
    """构造全 mock 的 EvolutionBridge（持久化重定向到 tmp）."""
    from sandbox.evolution_bridge import EvolutionBridge

    async def mock_reflect(instructions, failures):
        return {"root_causes": ["指令太模糊"], "specific_defects": ["缺少步骤"],
                "improvement_directions": ["增加检查清单"]}

    async def mock_mutate(instructions, reflection):
        return [
            {"strategy": "refine", "instructions": instructions + "\n[v2-refine] 增加检查清单"},
            {"strategy": "restructure", "instructions": instructions + "\n[v2-restructure] 分步执行"},
        ]

    results = ab_results or {"baseline": 0.50, "refine": 0.62, "restructure": 0.55}

    async def mock_ab(run, candidate):
        key = "baseline" if candidate is None else candidate["strategy"]
        f = results[key]
        return {"fitness": f, "dims": {"task_completion": f, "resilience": f},
                "trial_id": f"ab-{key}"}

    class FakeSkill:
        skill_id = "sk-coding"
        name = "coding"
        slug = "coding"
        instructions = "原始 coding 指令"
        version = 1

    class FakeLib:
        snapshots = []
        def _find_skill(self, team_id, sid):
            return FakeSkill() if sid in ("coding", "sk-coding") else None
        def browse(self, team_id=""):
            return [{"skill_id": "sk-coding", "name": "coding", "slug": "coding"}]
        def create_version_snapshot(self, skill, reason="", metadata=None):
            self.snapshots.append({"reason": reason, "metadata": metadata})
            return {"skill_id": skill.skill_id, "version": skill.version, "ok": True}
        def evaluate_publish_gate(self, team_id, skill_id):
            return {"ok": True, "reason": ""}

    class FakeEvolver:
        applied = []
        def apply_evolution(self, team_id, skill_id, new_instructions):
            self.applied.append({"skill_id": skill_id, "instructions": new_instructions})
            return {"status": "evolved", "skill_id": skill_id, "version": 2}

    return EvolutionBridge(
        proficiency_store=store, reflect_fn=mock_reflect, mutate_fn=mock_mutate,
        ab_runner=mock_ab, skill_library=FakeLib(), skill_evolver=FakeEvolver(),
        budget_tokens=budget, persist_dir=tmp,
    )


def test_identify_weak_skills():
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store_with_weak_skill(tmp)
        bridge = _make_bridge(store, tmp=tmp)
        weak = bridge.identify_weak_skills("teamA", "scn", ["t1"],
                                           {"coding": 0.6, "testing": 0.6})
        names = [w["skill_name"] for w in weak]
        assert "coding" in names
        assert "testing" not in names
        coding = next(w for w in weak if w["skill_name"] == "coding")
        assert coding["baseline_success_rate"] == 0.2
        assert coding["failure_samples"]


def test_full_run_reaches_gating_then_approve():
    """C-3.8/E-3 核心: identify→reflect→mutate→ab→gating→approve→applied."""
    from sandbox.models import EvolutionRunStatus
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store_with_weak_skill(tmp)
        _isolate_ratchet(tmp)
        bridge = _make_bridge(store, tmp=tmp)
        run = asyncio.run(bridge.start_run(
            team_id="teamA", scenario_id="scn", trial_ids=["t1"],
            skill_expectations={"coding": 0.6}, auto_apply=False))
        assert run.status == EvolutionRunStatus.GATING, run.error
        assert run.target_skills[0]["skill_name"] == "coding"
        assert run.reflection["root_causes"]
        assert len(run.candidates) == 2
        assert run.winner["strategy"] == "refine"  # fitness 最高
        assert run.winner["improvement"] >= 0.05
        # 人工批准
        result = bridge.approve(run.run_id)
        assert result["ok"], result
        assert run.status == EvolutionRunStatus.APPLIED
        assert bridge._skill_evolver.applied[0]["skill_id"] == "sk-coding"
        assert any("evolution_run" in s["reason"] for s in bridge._skill_library.snapshots)


def test_auto_apply_path():
    from sandbox.models import EvolutionRunStatus
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store_with_weak_skill(tmp)
        _isolate_ratchet(tmp)
        bridge = _make_bridge(store, tmp=tmp)
        run = asyncio.run(bridge.start_run(
            team_id="teamA", scenario_id="scn", trial_ids=["t1"],
            skill_expectations={"coding": 0.6}, auto_apply=True))
        assert run.status == EvolutionRunStatus.APPLIED, run.error


def test_rejected_when_no_improvement():
    """晋升判定: 提升不足 5% → REJECTED."""
    from sandbox.models import EvolutionRunStatus
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store_with_weak_skill(tmp)
        bridge = _make_bridge(store, tmp=tmp, ab_results={"baseline": 0.60, "refine": 0.61, "restructure": 0.58})
        run = asyncio.run(bridge.start_run(
            team_id="teamA", scenario_id="scn", trial_ids=["t1"],
            skill_expectations={"coding": 0.6}))
        assert run.status == EvolutionRunStatus.REJECTED
        assert "improvement" in run.error


def test_rejected_when_no_weak_skills():
    from sandbox.models import EvolutionRunStatus
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store_with_weak_skill(tmp)
        bridge = _make_bridge(store, tmp=tmp)
        run = asyncio.run(bridge.start_run(
            team_id="teamA", scenario_id="scn", trial_ids=["t1"],
            skill_expectations={"coding": 0.1, "testing": 0.1}))  # 阈值极低 → 无弱 skill
        assert run.status == EvolutionRunStatus.REJECTED
        assert run.error == "no_weak_skills_identified"


def test_budget_abort():
    """C-3.6: 超预算中止."""
    from sandbox.models import EvolutionRunStatus
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store_with_weak_skill(tmp)
        bridge = _make_bridge(store, tmp=tmp, budget=100)

        async def costly_reflect(instructions, failures):
            for r in bridge._runs.values():
                r.cost_tokens += 99999
            return {"root_causes": ["x"], "specific_defects": [], "improvement_directions": []}

        bridge._reflect_fn = costly_reflect
        run = asyncio.run(bridge.start_run(
            team_id="teamA", scenario_id="scn", trial_ids=["t1"],
            skill_expectations={"coding": 0.6}))
        assert run.status == EvolutionRunStatus.FAILED
        assert "budget_exceeded" in run.error


def test_manual_reject():
    from sandbox.models import EvolutionRunStatus
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store_with_weak_skill(tmp)
        bridge = _make_bridge(store, tmp=tmp)
        run = asyncio.run(bridge.start_run(
            team_id="teamA", scenario_id="scn", trial_ids=["t1"],
            skill_expectations={"coding": 0.6}))
        assert run.status == EvolutionRunStatus.GATING
        r = bridge.reject(run.run_id, "人工拒绝测试")
        assert r["ok"]
        assert run.status == EvolutionRunStatus.REJECTED
        # 拒绝后不可再批准
        assert not bridge.approve(run.run_id)["ok"]
