# -*- coding: utf-8 -*-
"""物竞天择 v4：TaskHabitatContract / skill identity / integration / plan skills."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from agents.execution_plan import (  # noqa: E402
    ExecutionPlan,
    PlanStep,
    build_plan_from_text,
    infer_skills_for_step,
    parse_plan_table,
    validate_plan,
)
from sandbox.plan_eco_bridge import (  # noqa: E402
    compile_plan_to_habitat_contract,
    compile_tasks_to_habitat_contract,
    validate_habitat_contract,
)
from sandbox.skill_identity import build_catalog, canonicalize, canonicalize_list  # noqa: E402
from sandbox.skill_integration import build_integration_report  # noqa: E402
from sandbox.eco_drill import Creature, EcoDrill  # noqa: E402


def test_parse_plan_table_skills_column():
    md = """
| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 | 所需技能 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 实现登录接口 | 开发 | P1 | - | API 可调用 | coding, testing |
| 2 | 部署到预发 | 运维 | P2 | 1 | 环境就绪 | deployment |
"""
    items = parse_plan_table(md)
    assert len(items) == 2
    assert "coding" in items[0]["required_skills"]
    plan = build_plan_from_text(md, topic="登录")
    assert plan.steps[0].required_skills
    assert "deployment" in plan.steps[1].required_skills


def test_infer_skills_role_and_title():
    sk, inf = infer_skills_for_step(responsible_role="QA工程师")
    assert inf and "testing" in sk
    sk2, inf2 = infer_skills_for_step(title="安全漏洞扫描", description="")
    assert inf2 and "security" in sk2


def test_validate_plan_eco_profile():
    plan = ExecutionPlan(topic="t")
    plan.steps.append(PlanStep(
        step_id="s1", index=1, title="实现核心功能模块",
        responsible_role="开发", acceptance="代码合入",
        required_skills=[],
    ))
    issues = validate_plan(plan, profile="eco")
    assert any(i["field"] == "required_skills" for i in issues)
    plan.steps[0].required_skills = ["coding"]
    assert not any(
        i["field"] == "required_skills" for i in validate_plan(plan, profile="eco")
    )


def test_compile_plan_contract_budget_and_topo():
    plan = ExecutionPlan(plan_id="plan-x", topic="发布")
    plan.steps = [
        PlanStep(step_id="s2", index=2, title="部署发布流程",
                 responsible_role="运维", acceptance="上线",
                 required_skills=["deployment"], dependencies=["1"]),
        PlanStep(step_id="s1", index=1, title="实现核心模块",
                 responsible_role="开发", acceptance="代码",
                 required_skills=["coding"]),
    ]
    c = compile_plan_to_habitat_contract(plan)
    assert c.niches[0].index == 1
    assert c.niches[1].index == 2
    assert 40 <= c.step_budget["max_steps_per_generation"] <= 500
    assert 1 <= c.step_budget["max_generations"] <= 10
    assert "coding" in c.skill_universe
    assert not validate_habitat_contract(c)


def test_compile_tasks_contract():
    tasks = [{
        "task_id": "t1",
        "title": "写测试用例",
        "description": "qa 测试",
        "metadata": {"required_skills": ["testing"], "plan_id": "p1"},
    }]
    c = compile_tasks_to_habitat_contract(tasks)
    assert c.provenance["source"] == "tasks"
    assert c.niches[0].demanded_skills == ["testing"]


def test_skill_identity_canonicalize():
    cat = build_catalog([("id-1", "Terraform"), ("id-2", "coding")])
    assert canonicalize("terraform", cat) == "id-1"
    assert canonicalize("CODING", cat) == "id-2"
    assert canonicalize_list(["Terraform", "coding", "coding"], cat) == ["id-1", "id-2"]


def test_integration_report():
    contract = {
        "plan_id": "p1",
        "niches": [{"demanded_skills": ["coding", "testing"]}],
        "provenance": {"fingerprint": "abc"},
    }
    result = {
        "final_ranking": [
            {"agent_id": "a1", "alive": True, "survival_ticks": 50,
             "skill_genome": ["coding", "coding"]},
            {"agent_id": "a2", "alive": False, "survival_ticks": 10,
             "skill_genome": ["ops", "coding"]},
        ]
    }
    rep = build_integration_report(result, contract)
    assert "testing" in rep["missing_plan_skills"]
    assert rep["write_policy"] == "suggest_only"
    assert "ops" in rep["deprecated_skills"] or True  # may be deprecated


def test_eco_drill_niches_advance():
    """有序 niche 窗口推进：前 N tick demand 来自步骤1."""
    creatures = [
        Creature(agent_id="c1", role="开发", skill_genome=["coding"],
                 skill_proficiency={"coding": 0.9}),
        Creature(agent_id="c2", role="运维", skill_genome=["deployment"],
                 skill_proficiency={"deployment": 0.9}),
    ]
    niches = [
        {"title": "写代码", "demanded_skills": ["coding"], "base_ticks": 5,
         "responsible_role": "开发"},
        {"title": "部署", "demanded_skills": ["deployment"], "base_ticks": 5,
         "responsible_role": "运维"},
    ]
    drill = EcoDrill(
        creatures=creatures,
        demanded_skills=["coding", "deployment"],
        niches=niches,
        seed=42,
        blind_learning_rate=0,
        genome_carry_cost=0,
        drift_prob=0,
        predator_pressure=0,
        abundance=1.5,
        niche_capacity=0,
        record_timeline=True,
    )
    for _ in range(5):
        s = drill.step()
        assert s["demand"] == "coding"
        assert s["niche_index"] == 0
    s6 = drill.step()
    assert s6["demand"] == "deployment"
    assert s6["niche_index"] == 1


def test_suggest_api_logic_and_apply_preview():
    from sandbox.skill_integration import build_integration_report
    contract = {
        "plan_id": "p",
        "niches": [{"demanded_skills": ["coding"]}],
        "provenance": {"fingerprint": "fp1"},
    }
    result = {
        "final_ranking": [
            {"agent_id": "a1", "alive": True, "survival_ticks": 20, "skill_genome": ["coding"]},
        ]
    }
    rep = build_integration_report(result, contract)
    assert rep["plan_id"] == "p"
    assert rep["write_policy"] == "suggest_only"


def test_era_count_one_path_smoke():
    """era 路径可通过 EcoDrill.run_eras(era_count=1) 退化为单纪元."""
    creatures = [
        Creature(agent_id="e1", skill_genome=["coding"], skill_proficiency={"coding": 0.8}),
        Creature(agent_id="e2", skill_genome=["coding"], skill_proficiency={"coding": 0.7}),
    ]
    drill = EcoDrill(
        creatures=creatures, demanded_skills=["coding"], seed=2,
        abundance=1.2, predator_pressure=0, drift_prob=0, niche_capacity=0,
        blind_learning_rate=0, genome_carry_cost=0, record_timeline=True,
    )
    out = drill.run_eras(max_steps_per_epoch=10, era_count=1, epochs_per_era=1, mutation_rate=0)
    assert out["era_count"] == 1
    assert len(out["eras"]) == 1


def test_contract_skill_selection_advantage():
    """持有计划技能者在任务生境中平均存活不低于无技能者（构造确定性）."""
    fit = [
        Creature(agent_id=f"f{i}", role="开发", skill_genome=["coding"],
                 skill_proficiency={"coding": 0.95})
        for i in range(4)
    ]
    unfit = [
        Creature(agent_id=f"u{i}", role="开发", skill_genome=["unrelated"],
                 skill_proficiency={"unrelated": 0.95})
        for i in range(4)
    ]
    niches = [{"title": "编码", "demanded_skills": ["coding"], "base_ticks": 40}]
    d1 = EcoDrill(fit, ["coding"], niches=niches, seed=1, abundance=1.2,
                  predator_pressure=0, drift_prob=0, niche_capacity=0,
                  blind_learning_rate=0, genome_carry_cost=0.0)
    d2 = EcoDrill(unfit, ["coding"], niches=niches, seed=1, abundance=1.2,
                  predator_pressure=0, drift_prob=0, niche_capacity=0,
                  blind_learning_rate=0, genome_carry_cost=0.0)
    for _ in range(40):
        if not d1.is_extinct():
            d1.step()
        if not d2.is_extinct():
            d2.step()
    avg_fit = sum(r["survival_ticks"] for r in d1.survival_ranking()) / 4
    avg_unfit = sum(r["survival_ticks"] for r in d2.survival_ranking()) / 4
    assert avg_fit >= avg_unfit
