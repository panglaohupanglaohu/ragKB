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
async def test_evolve_skill_returns_draft_contract():
    lib = FakeLibrary(_mk_skill())
    evolver = SkillEvolver(skill_library=lib)
    # 无 chat_harness：应返回 llm_degraded 错误，不静默回退原指令
    res = await evolver.evolve_skill("team", "sk-x")
    assert res.get("status") == "evolved_draft"
    assert res.get("error") == "llm_degraded"
    assert res.get("llm_degraded") is True
    assert "original_instructions" in res
    assert res.get("improved_instructions") is None
    assert "error_detail" in res


@pytest.mark.asyncio
async def test_evolve_skill_resolves_by_slug():
    lib = FakeLibrary(_mk_skill())
    evolver = SkillEvolver(skill_library=lib)
    res = await evolver.evolve_skill("team", "es-rescale")  # slug 回退
    assert res.get("status") == "evolved_draft"


def test_apply_evolution_increments_version_and_persists():
    lib = FakeLibrary(_mk_skill())
    evolver = SkillEvolver(skill_library=lib)
    res = evolver.apply_evolution("team", "sk-x", "新指令：增加健康观察与回滚。")
    assert res["status"] == "evolved"
    assert res["old_version"] == 1
    assert res["version"] == 2
    assert lib.skill.instructions.startswith("新指令")
    assert lib.snapshots == 1  # 演化前自动快照
    assert lib.persisted == 1


def test_apply_evolution_missing_skill():
    lib = FakeLibrary(_mk_skill())
    evolver = SkillEvolver(skill_library=lib)
    res = evolver.apply_evolution("team", "does-not-exist", "x")
    assert res.get("error") == "skill_not_found"
