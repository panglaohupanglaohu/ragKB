"""SkillLibrary._find_skill identity resolution regressions.

Covers the frontend resolveSkillId ↔ backend _find_skill contract:
both skill_id and slug must resolve to the same registered skill, so the
演化/验证/版本 Tabs work whether the queue item carries skill_id or slug.
"""

from __future__ import annotations

from agents.models import SkillDefinition
from agents.skill_library import SkillLibrary


class _FakeTeam:
    def __init__(self, skills):
        self.skills = skills


class _FakeTeamManager:
    def __init__(self, team):
        self._team = team

    def get_team(self, team_id):
        return self._team


def _build_library():
    skill = SkillDefinition(
        skill_id="sk-es-1",
        slug="es-rescale",
        name="ElasticSearch 实例扩缩容",
        instructions="步骤...",
        version=1,
    )
    team = _FakeTeam({skill.skill_id: skill})
    lib = SkillLibrary(team_manager=_FakeTeamManager(team))
    return lib, skill


def test_find_skill_by_skill_id():
    lib, skill = _build_library()
    assert lib._find_skill("team", "sk-es-1") is skill


def test_find_skill_by_slug_fallback():
    lib, skill = _build_library()
    # 前端在 allSkills 未就绪时回退用 slug 作 skill_id，后端必须命中同一技能
    assert lib._find_skill("team", "es-rescale") is skill


def test_find_skill_unknown_returns_none():
    lib, _ = _build_library()
    assert lib._find_skill("team", "nope") is None
