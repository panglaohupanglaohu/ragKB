# -*- coding: utf-8 -*-
"""技能效果追踪器 — 订阅 EventBus 的 TASK_COMPLETED 事件，更新技能使用指标.

对应 SkillClaw: "Successfully deal" / "partially solves" / "fails" 反馈循环。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .domain_events import DomainEvent, EventType
from .event_bus import get_event_bus

logger = logging.getLogger(__name__)


class SkillEffectivenessTracker:
    """订阅 TASK_COMPLETED/TASK_FAILED 事件，更新 SkillDefinition 的效果指标.

    指标:
    - usage_count: 被调用的总次数
    - success_count / fail_count: 成功/失败次数
    - effectiveness: success_count / usage_count
    - last_used_at: 最近使用时间
    """

    def __init__(self, skill_library=None):
        self._skill_library = skill_library
        self._bus = get_event_bus()
        self._subscribed = False

    def start(self) -> None:
        """订阅 EventBus 开始追踪."""
        if self._subscribed:
            return
        self._bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self._bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)
        self._subscribed = True
        logger.info("SkillEffectivenessTracker started")

    def stop(self) -> None:
        """取消订阅."""
        self._bus.unsubscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self._bus.unsubscribe(EventType.TASK_FAILED, self._on_task_failed)
        self._subscribed = False

    async def _on_task_completed(self, event: DomainEvent) -> None:
        """处理任务完成事件 — 提取使用的技能并更新计数."""
        payload = event.payload
        metadata = payload.metadata if hasattr(payload, 'metadata') else {}
        skills_used = metadata.get("skills_used", [])
        team_id = metadata.get("team_id", "")
        session_id = metadata.get("session_id", "")

        for skill_id in skills_used:
            self._record_usage(team_id, skill_id, success=True, session_id=session_id)

    async def _on_task_failed(self, event: DomainEvent) -> None:
        """处理任务失败事件."""
        payload = event.payload
        metadata = payload.metadata if hasattr(payload, 'metadata') else {}
        skills_used = metadata.get("skills_used", [])
        team_id = metadata.get("team_id", "")

        for skill_id in skills_used:
            self._record_usage(team_id, skill_id, success=False)

    def _record_usage(self, team_id: str, skill_id: str, success: bool, session_id: str = "") -> None:
        """更新单个技能的效果指标."""
        if not self._skill_library:
            return

        skill = self._skill_library._find_skill(team_id, skill_id)
        if not skill:
            return

        skill.usage_count += 1
        if success:
            skill.success_count += 1
        else:
            skill.fail_count += 1

        # Recalculate effectiveness
        if skill.usage_count > 0:
            skill.effectiveness = skill.success_count / skill.usage_count

        skill.last_used_at = datetime.now(timezone.utc).isoformat()

        # Add evidence session
        if session_id and session_id not in skill.evidence_sessions:
            skill.evidence_sessions.append(session_id)
            # Keep only last 50 sessions
            if len(skill.evidence_sessions) > 50:
                skill.evidence_sessions = skill.evidence_sessions[-50:]

        # Check for degradation
        if skill.usage_count >= 5 and skill.effectiveness < 0.4:
            from .models import SkillLifecycleStage
            if skill.lifecycle_stage not in (SkillLifecycleStage.DRAFT, SkillLifecycleStage.DEGRADED):
                skill.lifecycle_stage = SkillLifecycleStage.DEGRADED
                logger.warning("Skill %s degraded (effectiveness=%.2f, usage=%d)",
                               skill_id, skill.effectiveness, skill.usage_count)

        # Persist
        self._skill_library._persist_skill(skill, team_id)
        logger.debug("Skill %s usage recorded: success=%s, effectiveness=%.2f",
                      skill_id, success, skill.effectiveness)

    def get_suggestions(self, team_id: str) -> List[Dict]:
        """生成演化建议 — 基于效果指标."""
        if not self._skill_library:
            return []

        suggestions = []
        all_skills = self._skill_library.browse(team_id=team_id)

        for s in all_skills:
            eff = s.get("effectiveness", 0)
            usage = s.get("usage_count", 0)

            if usage >= 5 and eff < 0.4:
                suggestions.append({
                    "type": "improve",
                    "skill_id": s["skill_id"],
                    "name": s["name"],
                    "reason": f"成功率{eff * 100:.0f}%，已使用{usage}次，建议改进",
                    "priority": "high",
                })

        # Check for duplicates
        duplicates = self._skill_library.find_duplicates(threshold=0.85)
        for dup in duplicates:
            suggestions.append({
                "type": "merge",
                "skill_a": dup["skill_a"],
                "skill_b": dup["skill_b"],
                "reason": f"相似度{dup['similarity'] * 100:.0f}%，建议合并",
                "priority": "medium",
            })

        return suggestions


# ── Singleton ────────────────────────────────────────────────────

_tracker: Optional[SkillEffectivenessTracker] = None


def get_skill_tracker() -> SkillEffectivenessTracker:
    global _tracker
    if _tracker is None:
        _tracker = SkillEffectivenessTracker()
    return _tracker


def init_skill_tracker(skill_library=None) -> SkillEffectivenessTracker:
    global _tracker
    _tracker = SkillEffectivenessTracker(skill_library=skill_library)
    _tracker.start()
    return _tracker
