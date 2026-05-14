# -*- coding: utf-8 -*-
"""技能演化引擎 — Evidence→Attribution→Evolution.

对应 SkillClaw: evolve_skill / merge_skills / create_from_sessions.
触发模式: 自动建议 + 人工确认（不自动执行）。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .models import SkillDefinition, SkillLifecycleStage

logger = logging.getLogger(__name__)


class SkillEvolver:
    """技能演化引擎 — 收集证据 → LLM改进 → 版本递增."""

    def __init__(self, skill_library=None, chat_harness=None):
        self._skill_library = skill_library
        self._chat_harness = chat_harness

    # ── Evolve: 改进现有技能 ─────────────────────────────────────

    async def evolve_skill(
        self,
        team_id: str,
        skill_id: str,
        evidence_sessions: Optional[List[str]] = None,
        user_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """收集证据 → LLM改进 instructions → version+1.

        Returns the evolved skill draft for review.
        """
        if not self._skill_library:
            return {"error": "skill_library_not_initialized"}

        skill = self._skill_library._find_skill(team_id, skill_id)
        if not skill:
            return {"error": "skill_not_found"}

        # Gather evidence
        evidence = evidence_sessions or skill.evidence_sessions
        evidence_text = f"技能名称: {skill.name}\n当前指令:\n{skill.instructions}\n\n"
        evidence_text += f"使用次数: {skill.usage_count}, 成功率: {skill.effectiveness * 100:.0f}%\n"
        if evidence:
            evidence_text += f"\n关联会话ID: {', '.join(evidence[:10])}\n"
        if user_feedback:
            evidence_text += f"\n用户反馈: {user_feedback}\n"

        # LLM improve
        improved_instructions = skill.instructions  # fallback
        prompt_text = f"请改进以下技能指令，使其更有效。\n\n{evidence_text}"
        if user_feedback:
            prompt_text = f"请根据以下用户反馈改进技能指令：\n\n用户反馈: {user_feedback}\n\n{evidence_text}"
        if self._chat_harness:
            try:
                result = await self._chat_harness.chat(
                    prompt=prompt_text,
                    system_prompt=EVOLVE_SYSTEM_PROMPT,
                    agent_id="skill_evolver",
                )
                # chat() returns TurnResult object with .response attribute
                if result and getattr(result, 'response', None):
                    improved_instructions = result.response
            except Exception as e:
                logger.error("LLM evolve failed: %s", e)
                return {"error": f"llm_failed: {e}"}

        # Create evolved version (as draft for review)
        return {
            "status": "evolved_draft",
            "skill_id": skill_id,
            "original_version": skill.version,
            "new_version": skill.version + 1,
            "original_instructions": skill.instructions,
            "improved_instructions": improved_instructions,
            "evidence_count": len(evidence),
        }

    def apply_evolution(self, team_id: str, skill_id: str, new_instructions: str) -> Dict[str, Any]:
        """应用演化结果（用户确认后调用）."""
        if not self._skill_library:
            return {"error": "skill_library_not_initialized"}

        skill = self._skill_library._find_skill(team_id, skill_id)
        if not skill:
            return {"error": "skill_not_found"}

        old_version = skill.version
        skill.instructions = new_instructions
        skill.version += 1
        skill.lifecycle_stage = SkillLifecycleStage.TEAM_LOCAL  # Reset to team_local after evolution
        self._skill_library._persist_skill(skill, team_id)

        logger.info("Skill %s evolved v%d → v%d", skill_id, old_version, skill.version)
        return {
            "status": "evolved",
            "skill_id": skill_id,
            "version": skill.version,
        }

    # ── Merge: 合并重复技能 ──────────────────────────────────────

    def merge_skills(self, team_id: str, skill_ids: List[str], strategy: str = "keep_longest") -> Dict[str, Any]:
        """合并多个重复技能为一个. 保留最长/最优的 instructions."""
        if not self._skill_library or len(skill_ids) < 2:
            return {"error": "invalid_merge_request"}

        skills = []
        for sid in skill_ids:
            s = self._skill_library._find_skill(team_id, sid)
            if s:
                skills.append(s)

        if len(skills) < 2:
            return {"error": "not_enough_skills_found"}

        # Select primary based on strategy
        if strategy == "keep_longest":
            primary = max(skills, key=lambda s: len(s.instructions))
        elif strategy == "pick_best_score":
            primary = max(skills, key=lambda s: s.effectiveness)
        else:
            primary = skills[0]

        # Create merged skill
        merged = SkillDefinition(
            skill_id=str(uuid4())[:8],
            name=primary.name,
            description=primary.description + " (合并版)",
            category=primary.category,
            icon=primary.icon,
            slug=primary.slug + "_merged",
            instructions=primary.instructions,
            required_tools=list(set(t for s in skills for t in s.required_tools)),
            source="merged",
            origin_team_id=team_id,
            lifecycle_stage=SkillLifecycleStage.TEAM_LOCAL,
            lineage=primary.skill_id,
            version=1,
            usage_count=sum(s.usage_count for s in skills),
            success_count=sum(s.success_count for s in skills),
            fail_count=sum(s.fail_count for s in skills),
        )
        # Recalculate effectiveness
        if merged.usage_count > 0:
            merged.effectiveness = merged.success_count / merged.usage_count

        # Persist merged skill
        self._skill_library._persist_skill(merged, team_id)
        if self._skill_library._team_manager:
            team = self._skill_library._team_manager.get_team(team_id)
            if team:
                team.add_skill(merged)
                self._skill_library._team_manager.save()

        logger.info("Merged %d skills into %s", len(skills), merged.skill_id)
        return {
            "status": "merged",
            "merged_skill_id": merged.skill_id,
            "merged_from": skill_ids,
            "strategy": strategy,
        }

    # ── Suggest: 演化建议 ────────────────────────────────────────

    def suggest_evolution(self, team_id: str) -> List[Dict[str, Any]]:
        """生成演化建议列表."""
        if not self._skill_library:
            return []

        suggestions = []
        all_skills = self._skill_library.browse(team_id=team_id)

        for s in all_skills:
            eff = s.get("effectiveness", 0)
            usage = s.get("usage_count", 0)
            stage = s.get("lifecycle_stage", "")

            # Low effectiveness + high usage → improve
            if usage >= 5 and eff < 0.4:
                suggestions.append({
                    "action": "improve",
                    "skill_id": s["skill_id"],
                    "name": s["name"],
                    "reason": f"💡 成功率{eff * 100:.0f}%，已使用{usage}次",
                    "priority": 1,
                })

            # High effectiveness + not published → publish
            if usage >= 3 and eff > 0.7 and s.get("visibility") == "private":
                suggestions.append({
                    "action": "publish",
                    "skill_id": s["skill_id"],
                    "name": s["name"],
                    "reason": f"🌐 成功率{eff * 100:.0f}%，建议分享到公共库",
                    "priority": 2,
                })

        # Check duplicates
        duplicates = self._skill_library.find_duplicates(threshold=0.85)
        for dup in duplicates:
            suggestions.append({
                "action": "merge",
                "skill_a": dup["skill_a"],
                "skill_b": dup["skill_b"],
                "reason": f"🔀 相似度{dup['similarity'] * 100:.0f}%",
                "priority": 3,
            })

        # Sort by priority
        suggestions.sort(key=lambda x: x.get("priority", 99))
        return suggestions

    # ── Evolution History ────────────────────────────────────────

    def get_evolution_history(self, team_id: str, skill_id: str) -> Dict[str, Any]:
        """获取技能的演化历史."""
        lineage = self._skill_library.get_lineage(skill_id) if self._skill_library else {}
        return {
            "skill_id": skill_id,
            "lineage": lineage,
        }


# ── System Prompt for Evolution ──────────────────────────────────

EVOLVE_SYSTEM_PROMPT = """你是一个技能优化专家。根据提供的技能指令和效果数据，改进技能指令使其更有效。

改进原则:
1. 保持指令的核心意图不变
2. 使指令更具体、更可操作
3. 修正可能导致失败的模糊表述
4. 添加边界条件和异常处理指导
5. 基于使用效果数据调整策略

直接输出改进后的指令文本，不要添加额外解释。"""


# ── Singleton ────────────────────────────────────────────────────

_evolver: Optional[SkillEvolver] = None


def get_skill_evolver() -> SkillEvolver:
    global _evolver
    if _evolver is None:
        _evolver = SkillEvolver()
    return _evolver


def init_skill_evolver(skill_library=None, chat_harness=None) -> SkillEvolver:
    global _evolver
    _evolver = SkillEvolver(skill_library=skill_library, chat_harness=chat_harness)
    logger.info("SkillEvolver initialized")
    return _evolver
