"""SkillEvolver evolve→apply version flow regressions.

Covers the 演化 Tab backend contract:
- evolve_skill returns original/improved instructions + new_version
- apply_evolution increments version and persists
"""

from __future__ import annotations

import pytest

from agents.models import SkillDefinition
from agents.skill_evolver import SkillEvolver


class FakeLibrary:
    def __init__(self, skill: SkillDefinition):
        self.skill = skill
        self.snapshots = 0
        self.persisted = 0

    def _find_skill(self, team_id: str, skill_id: str):
        if self.skill and (self.skill.skill_id == skill_id or self.skill.slug == skill_id):
            return self.skill
        return None

    def create_version_snapshot(self, skill):
        self.snapshots += 1
        return {"ok": True, "version": skill.version}

    def _persist_skill(self, skill, team_id):
        self.persisted += 1
        self.skill = skill


def _mk_skill():
    return SkillDefinition(
        skill_id="sk-x",
        slug="es-rescale",
        name="ElasticSearch 实例扩缩容",
        instructions="旧指令：执行扩容步骤。",
        version=1,
    )


@pytest.mark.asyncio
async def test_evolve_skill_returns_draft_contract(monkeypatch):
    lib = FakeLibrary(_mk_skill())
    evolver = SkillEvolver(skill_library=lib, chat_harness=None)
    # 禁止回退到全局 harness（本机可能已有配置，会误打真 LLM）
    monkeypatch.setattr(
        "agents.chat_harness.get_chat_harness",
        lambda: None,
    )
    res = await evolver.evolve_skill("team", "sk-x")
    assert res.get("status") == "evolved_draft"
    assert res.get("error") == "llm_degraded"
    assert res.get("llm_degraded") is True
    assert "original_instructions" in res
    assert res.get("improved_instructions") is None
    assert "error_detail" in res


@pytest.mark.asyncio
async def test_evolve_skill_resolves_by_slug(monkeypatch):
    lib = FakeLibrary(_mk_skill())
    evolver = SkillEvolver(skill_library=lib, chat_harness=None)
    monkeypatch.setattr(
        "agents.chat_harness.get_chat_harness",
        lambda: None,
    )
    res = await evolver.evolve_skill("team", "es-rescale")  # slug 回退
    assert res.get("status") == "evolved_draft"
    assert res.get("error") == "llm_degraded"


def test_apply_evolution_increments_version_and_persists():
    lib = FakeLibrary(_mk_skill())
    evolver = SkillEvolver(skill_library=lib)
    res = evolver.apply_evolution(
        "team",
        "sk-x",
        "新指令：增加健康观察与回滚。",
        changelog=["补回滚", "补验收"],
    )
    assert res["status"] == "evolved"
    assert res["old_version"] == 1
    assert res["version"] == 2
    assert res.get("next_step") == "verify"
    assert res.get("changelog") == ["补回滚", "补验收"]
    assert lib.skill.instructions.startswith("新指令")
    assert lib.snapshots == 1  # 演化前自动快照
    assert lib.persisted == 1
    le = (lib.skill.config or {}).get("last_evolution") or {}
    assert le.get("from_version") == 1
    assert le.get("to_version") == 2
    assert le.get("changelog") == ["补回滚", "补验收"]


def test_apply_evolution_missing_skill():
    lib = FakeLibrary(_mk_skill())
    evolver = SkillEvolver(skill_library=lib)
    res = evolver.apply_evolution("team", "does-not-exist", "x")
    assert res.get("error") == "skill_not_found"


def test_gather_evidence_includes_last_verify_and_usage():
    skill = _mk_skill()
    skill.usage_count = 7
    skill.success_count = 3
    skill.fail_count = 4
    skill.effectiveness = 0.43
    skill.required_tools = ["python_boto3", "cloudwatch_api"]
    skill.config = {
        "last_verify": {
            "status": "failed",
            "pass_rate": 0.4,
            "passed": 2,
            "failed": 3,
            "error_detail": "通过率 40% 低于 70% 阈值",
            "failed_checks": [
                {"name": "steps_present", "message": "缺少回滚步骤", "layer": "semantic"},
            ],
            "twin_ab": {
                "status": "ok",
                "passed": False,
                "baseline_rate": 0.5,
                "treatment_rate": 0.52,
                "target_gain_pp": 2.0,
                "gain_threshold": 0.05,
            },
        },
        "last_evolution": {
            "from_version": 1,
            "to_version": 2,
            "changelog": ["补验收"],
        },
        "twin_compare": {
            "before": {"target_gain_pp": 1.0, "treatment_rate": 0.5},
            "after": {"target_gain_pp": 6.0, "treatment_rate": 0.6},
            "delta_gain_pp": 5.0,
            "improved": True,
        },
    }
    evolver = SkillEvolver(skill_library=FakeLibrary(skill))
    ev = evolver._gather_evidence(skill, user_feedback="请补齐回滚")
    assert ev["usage_count"] == 7
    assert ev["success_count"] == 3
    assert ev["fail_count"] == 4
    assert ev["task_usage"]["usage_count"] == 7
    assert "router_affinity" in ev
    assert ev["required_tools"] == ["python_boto3", "cloudwatch_api"]
    assert ev["user_feedback"] == "请补齐回滚"
    assert ev["last_verify"]["status"] == "failed"
    assert ev["last_evolution"]["to_version"] == 2
    assert ev["twin_compare"]["improved"] is True
    lines = SkillEvolver._format_verify_evidence_lines(ev["last_verify"])
    blob = "\n".join(lines)
    assert "上次验证结果" in blob
    assert "通过率 40%" in blob or "40%" in blob
    assert "Twin A/B" in blob
    assert "FAIL" in blob
    usage_blob = "\n".join(SkillEvolver._format_task_usage_lines(ev["task_usage"]))
    assert "任务 usage" in usage_blob
    twin_blob = "\n".join(SkillEvolver._format_twin_compare_lines(ev["twin_compare"]))
    assert "演化前后" in twin_blob or "Twin A/B" in twin_blob


def test_apply_evolution_snapshots_twin_before():
    skill = _mk_skill()
    skill.config = {
        "last_verify": {
            "status": "failed",
            "twin_ab": {
                "status": "ok",
                "passed": False,
                "target_gain_pp": 1.5,
                "treatment_rate": 0.51,
                "baseline_rate": 0.5,
            },
        }
    }
    lib = FakeLibrary(skill)
    evolver = SkillEvolver(skill_library=lib)
    res = evolver.apply_evolution("team", "sk-x", "新指令：补齐回滚与验收。", changelog=["补回滚"])
    assert res["status"] == "evolved"
    before = (lib.skill.config or {}).get("twin_before_evolve") or {}
    assert before.get("target_gain_pp") == 1.5
    assert before.get("skill_version") == 1


@pytest.mark.asyncio
async def test_evolve_payload_includes_evidence_summary(monkeypatch):
    skill = _mk_skill()
    skill.config = {"last_verify": {"status": "failed", "pass_rate": 0.2, "passed": 0, "failed": 1}}
    lib = FakeLibrary(skill)
    evolver = SkillEvolver(skill_library=lib, chat_harness=None)
    monkeypatch.setattr("agents.chat_harness.get_chat_harness", lambda: None)
    res = await evolver.evolve_skill("team", "sk-x", user_feedback="修失败项")
    assert res.get("status") == "evolved_draft"
    summary = res.get("evidence_summary") or {}
    assert summary.get("has_last_verify") is True
    assert summary.get("last_verify_status") == "failed"
    assert summary.get("has_user_feedback") is True
