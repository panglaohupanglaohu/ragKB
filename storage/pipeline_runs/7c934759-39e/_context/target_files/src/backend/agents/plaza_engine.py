# -*- coding: utf-8 -*-
"""智能体广场引擎 — 讨论编排与多 Agent 协同.

核心编排逻辑:
1. Moderator（主持人壁龛）提出子话题，引导讨论方向
2. 每轮: 各参与者按座席层级依次发言（内圈→中圈→外圈）
3. Moderator 总结本轮关键观点
4. 最终轮: Moderator 生成全局总结 + 关键结论

消息通过 asyncio.Queue 实时推送给 SSE 订阅者。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Dict, List, Optional
from uuid import uuid4

from .plaza import (
    Discussion, DiscussionStatus, NicheRole, Participant,
    Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
)
from .plaza_store import PlazaStore

logger = logging.getLogger(__name__)


class PlazaEngine:
    """广场引擎 — 管理广场、参与者和讨论编排."""

    def __init__(self):
        self._store = PlazaStore()
        self._plazas: Dict[str, Plaza] = self._store.load_all()
        self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
        self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference

    def set_chat_fn(self, fn: Callable):
        """注入 ChatHarness.chat 异步函数."""
        self._chat_fn = fn

    # ── 广场 CRUD ──────────────────────────────────────────

    def create_plaza(self, name: str, description: str = "") -> Plaza:
        plaza = Plaza(name=name, description=description)
        self._plazas[plaza.id] = plaza
        self._store.save_plaza(plaza)
        logger.info(f"🏛️ 广场创建: {name} ({plaza.id})")
        return plaza

    def get_plaza(self, plaza_id: str) -> Optional[Plaza]:
        return self._plazas.get(plaza_id)

    def list_plazas(self) -> List[Plaza]:
        return list(self._plazas.values())

    def delete_plaza(self, plaza_id: str) -> bool:
        if plaza_id in self._plazas:
            del self._plazas[plaza_id]
            self._store.delete_plaza(plaza_id)
            return True
        return False

    # ── 参与者管理 ──────────────────────────────────────────

    def add_participant(
        self, plaza_id: str, agent_id: str, agent_name: str = "",
        role: str = "", team_id: str = "",
        seat_tier: SeatTier = SeatTier.MIDDLE,
        niche_role: NicheRole = NicheRole.OBSERVER,
    ) -> Optional[Participant]:
        plaza = self._plazas.get(plaza_id)
        if not plaza:
            return None
        # 分配壁龛编号 (动态扩展)
        used_niches = {p.niche_index for p in plaza.participants.values() if p.niche_index >= 0}
        niche_index = len(used_niches)
        # 自动扩展壁龛数
        if niche_index >= plaza.niche_count:
            plaza.niche_count = niche_index + 1
        p = Participant(
            agent_id=agent_id, agent_name=agent_name, role=role,
            team_id=team_id, seat_tier=seat_tier, niche_role=niche_role,
            niche_index=niche_index,
        )
        plaza.participants[agent_id] = p
        self._store.save_plaza(plaza)
        logger.info(f"🪑 参与者加入广场 {plaza_id}: {agent_name} (壁龛 #{niche_index})")
        return p

    def remove_participant(self, plaza_id: str, agent_id: str) -> bool:
        plaza = self._plazas.get(plaza_id)
        if plaza and agent_id in plaza.participants:
            del plaza.participants[agent_id]
            self._store.save_plaza(plaza)
            return True
        return False

    # ── 讨论管理 ──────────────────────────────────────────

    def create_discussion(
        self, plaza_id: str, topic: str, description: str = "",
        moderator_agent_id: str = "", max_rounds: int = 5,
    ) -> Optional[Discussion]:
        plaza = self._plazas.get(plaza_id)
        if not plaza:
            return None
        disc = Discussion(
            plaza_id=plaza_id, topic=topic, description=description,
            moderator_agent_id=moderator_agent_id, max_rounds=max_rounds,
        )
        plaza.discussions[disc.id] = disc
        self._store.save_plaza(plaza)
        logger.info(f"💬 讨论创建: {topic[:40]} ({disc.id})")
        return disc

    def get_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
        plaza = self._plazas.get(plaza_id)
        if not plaza:
            return None
        return plaza.discussions.get(discussion_id)

    def list_discussions(self, plaza_id: str) -> List[Discussion]:
        plaza = self._plazas.get(plaza_id)
        if not plaza:
            return []
        return list(plaza.discussions.values())

    def delete_discussion(self, plaza_id: str, discussion_id: str) -> bool:
        plaza = self._plazas.get(plaza_id)
        if not plaza or discussion_id not in plaza.discussions:
            return False
        del plaza.discussions[discussion_id]
        self._sse_queues.pop(discussion_id, None)
        self._store.save_plaza(plaza)
        return True

    def reset_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
        """重置已结束讨论，保留话题本身以便重新讨论。"""
        disc = self.get_discussion(plaza_id, discussion_id)
        if not disc:
            return None
        disc.status = DiscussionStatus.OPEN
        disc.current_round = 0
        disc.messages.clear()
        disc.summary = ""
        disc.key_conclusions.clear()
        disc.plan.clear()
        disc.assigned_team_id = ""
        disc.started_at = None
        disc.ended_at = None
        plaza = self._plazas.get(plaza_id)
        if plaza:
            self._store.save_plaza(plaza)
        return disc

    # ── SSE 订阅管理 ──────────────────────────────────────

    def subscribe(self, discussion_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._sse_queues.setdefault(discussion_id, []).append(q)
        return q

    def unsubscribe(self, discussion_id: str, q: asyncio.Queue):
        qs = self._sse_queues.get(discussion_id, [])
        if q in qs:
            qs.remove(q)

    async def _broadcast(self, discussion_id: str, event: Dict[str, Any]):
        """向所有 SSE 订阅者推送事件."""
        for q in self._sse_queues.get(discussion_id, []):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    # ── 核心讨论编排 ──────────────────────────────────────

    async def run_discussion(
        self, plaza_id: str, discussion_id: str,
    ) -> Optional[Discussion]:
        """运行一场完整的广场讨论.

        编排流程 (向心结构):
        1. Moderator 开场: 阐述话题，提出第一轮子问题
        2. 每轮:
           a. 各参与者按座席层级依次发言 (内→中→外)
           b. Moderator 总结本轮观点
        3. 最终轮: Moderator 生成全局总结 + 关键结论
        """
        plaza = self._plazas.get(plaza_id)
        if not plaza:
            return None
        disc = plaza.discussions.get(discussion_id)
        if not disc:
            return None
        if disc.status not in (DiscussionStatus.OPEN,):
            return disc

        disc.status = DiscussionStatus.IN_PROGRESS
        disc.started_at = datetime.now(timezone.utc).isoformat()

        # Give event loop a chance to process SSE client connections
        await asyncio.sleep(0.1)

        await self._broadcast(disc.id, {
            "type": "discussion_start",
            "discussion_id": disc.id,
            "topic": disc.topic,
        })

        participants = list(plaza.participants.values())
        moderator = None
        speakers = []

        # 找到 moderator
        if disc.moderator_agent_id:
            moderator = plaza.participants.get(disc.moderator_agent_id)
        if not moderator and participants:
            moderator = participants[0]
            disc.moderator_agent_id = moderator.agent_id

        # 按座席层级排序发言者 (内→中→外)
        tier_order = {SeatTier.INNER: 0, SeatTier.MIDDLE: 1, SeatTier.OUTER: 2}
        speakers = sorted(
            [p for p in participants if p.agent_id != moderator.agent_id],
            key=lambda p: tier_order.get(p.seat_tier, 1),
        ) if moderator else participants

        if not self._chat_fn:
            # 无 LLM 时使用模拟回复
            await self._run_simulated(disc, moderator, speakers)
            return disc

        # ── 开场: Moderator 引导话题 ──
        opening_prompt = (
            f"你是本场讨论的议事长（主持人）。\n"
            f"讨论话题: 「{disc.topic}」\n"
            f"{f'话题描述: {disc.description}' if disc.description else ''}\n"
            f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n"
            f"参与者: {', '.join(p.agent_name or p.agent_id for p in speakers)}\n\n"
            f"请开场: 简要阐述话题的背景和意义，明确讨论目标，然后提出第一个引导性问题。"
        )
        opening = await self._agent_speak(
            disc, moderator, opening_prompt, round_number=0,
            niche_role="moderator",
        )

        # ── 多轮讨论 ──
        for round_num in range(1, disc.max_rounds + 1):
            disc.current_round = round_num
            await self._broadcast(disc.id, {
                "type": "round_start", "round": round_num,
                "max_rounds": disc.max_rounds,
            })

            # 每个参与者发言
            prev_messages = self._format_history(disc)
            for speaker in speakers:
                speak_prompt = (
                    f"你正在参与一场关于「{disc.topic}」的讨论。\n"
                    f"你的角色: {speaker.agent_name} ({speaker.role})\n"
                    f"当前是第 {round_num}/{disc.max_rounds} 轮。\n\n"
                    f"之前的讨论内容:\n{prev_messages}\n\n"
                    f"请根据你的专业背景发表观点。注意:\n"
                    f"- 回应之前的讨论内容，可以赞同、补充或提出不同见解\n"
                    f"- 言之有物，提供具体的技术细节或实践经验\n"
                    f"- 控制在 200 字以内"
                )
                await self._agent_speak(
                    disc, speaker, speak_prompt, round_number=round_num,
                    niche_role=speaker.niche_role.value,
                )
                prev_messages = self._format_history(disc)

            # Moderator 总结本轮
            if round_num < disc.max_rounds:
                summary_prompt = (
                    f"你是主持人。第 {round_num} 轮讨论已结束。\n\n"
                    f"本轮讨论内容:\n{self._format_round_messages(disc, round_num)}\n\n"
                    f"请简要总结本轮的关键观点 (3 句以内)，"
                    f"然后提出下一轮的引导性问题。"
                )
                await self._agent_speak(
                    disc, moderator, summary_prompt, round_number=round_num,
                    niche_role="moderator",
                )

        # ── 最终总结 ──
        disc.status = DiscussionStatus.SUMMARIZING
        await self._broadcast(disc.id, {"type": "summarizing"})

        final_prompt = (
            f"你是议事长。关于「{disc.topic}」的讨论已经完成 {disc.max_rounds} 轮。\n"
            f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n\n"
            f"完整讨论记录:\n{self._format_history(disc)}\n\n"
            f"请生成最终总结和执行计划:\n"
            f"1. 讨论概要 (3-5 句)\n"
            f"2. 关键结论 (列出 3-5 个要点)\n"
            f"3. 执行计划:\n"
            f"   - 列出 2-4 个具体可执行的任务步骤\n"
            f"   - 每个步骤包含: 任务名称、负责角色、预期产出\n"
            f"4. 建议指派给哪个团队执行\n\n"
            f"请用结构化格式输出。"
        )
        summary_msg = await self._agent_speak(
            disc, moderator, final_prompt, round_number=disc.max_rounds + 1,
            niche_role="moderator",
        )
        disc.summary = summary_msg.content if summary_msg else ""
        disc.status = DiscussionStatus.CLOSED
        disc.ended_at = datetime.now(timezone.utc).isoformat()

        await self._broadcast(disc.id, {
            "type": "discussion_end",
            "summary": disc.summary,
        })

        # 持久化讨论结果
        self._store.save_plaza(plaza)

        logger.info(
            f"✅ 讨论完成: {disc.topic[:30]} — "
            f"{len(disc.messages)} 条消息, {disc.max_rounds} 轮"
        )
        return disc

    async def _agent_speak(
        self, disc: Discussion, participant: Participant,
        prompt: str, round_number: int, niche_role: str = "",
    ) -> Optional[PlazaMessage]:
        """让一个 Agent 在广场中发言."""
        try:
            result = await self._chat_fn(
                prompt,
                agent_id=participant.agent_id,
                system_prompt=(
                    f"你是 {participant.agent_name}，角色: {participant.role}。"
                    f"你正在智能体广场中参与讨论。请用中文回答，专业且简洁。"
                ),
            )
            content = result.response if result else "[无响应]"
        except Exception as e:
            logger.warning(f"Agent {participant.agent_id} 发言失败: {e}")
            content = f"[{participant.agent_name} 暂时离线]"

        msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id=participant.agent_id,
            agent_name=participant.agent_name or participant.agent_id,
            role=participant.role,
            niche_role=niche_role or participant.niche_role.value,
            content=content,
            round_number=round_number,
        )
        disc.messages.append(msg)

        await self._broadcast(disc.id, {
            "type": "message",
            "message": msg.to_dict(),
        })
        return msg

    async def _run_simulated(
        self, disc: Discussion, moderator: Optional[Participant],
        speakers: List[Participant],
    ):
        """无 LLM 时的模拟讨论."""
        sim_responses = [
            "这是一个很好的话题。从技术角度来看，我认为关键在于系统的可扩展性和模块化设计。",
            "我同意前面的观点，同时想补充：在实际实施中，我们还需要考虑性能瓶颈和容错机制。",
            "从测试的角度，我建议我们在设计阶段就规划好测试策略，包括单元测试和集成测试的覆盖范围。",
            "关于这个问题，业界已经有一些成熟的方案可以参考。我们可以结合自身需求进行适配。",
        ]

        if moderator:
            msg = PlazaMessage(
                discussion_id=disc.id, agent_id=moderator.agent_id,
                agent_name=moderator.agent_name, role=moderator.role,
                niche_role="moderator", content=f"欢迎各位参与「{disc.topic}」的讨论。让我们开始吧。",
                round_number=0,
            )
            disc.messages.append(msg)
            await self._broadcast(disc.id, {"type": "message", "message": msg.to_dict()})

        for round_num in range(1, min(disc.max_rounds + 1, 3)):
            disc.current_round = round_num
            await self._broadcast(disc.id, {"type": "round_start", "round": round_num, "max_rounds": disc.max_rounds})
            for i, speaker in enumerate(speakers):
                content = sim_responses[i % len(sim_responses)]
                msg = PlazaMessage(
                    discussion_id=disc.id, agent_id=speaker.agent_id,
                    agent_name=speaker.agent_name, role=speaker.role,
                    niche_role=speaker.niche_role.value, content=content,
                    round_number=round_num,
                )
                disc.messages.append(msg)
                await self._broadcast(disc.id, {"type": "message", "message": msg.to_dict()})
                await asyncio.sleep(0.1)

        disc.summary = f"关于「{disc.topic}」的讨论已完成。（模拟模式 — 配置 LLM API Key 后可获得真实 AI 讨论）"
        disc.status = DiscussionStatus.CLOSED
        disc.ended_at = datetime.now(timezone.utc).isoformat()
        await self._broadcast(disc.id, {"type": "discussion_end", "summary": disc.summary})

    def _format_history(self, disc: Discussion) -> str:
        """格式化讨论历史为 prompt 可用的文本."""
        lines = []
        for m in disc.messages[-20:]:  # 最近 20 条
            prefix = "【主持人】" if m.niche_role == "moderator" else f"【{m.agent_name}】"
            lines.append(f"{prefix}: {m.content[:300]}")
        return "\n\n".join(lines)

    def _format_round_messages(self, disc: Discussion, round_num: int) -> str:
        """格式化某一轮的消息."""
        lines = []
        for m in disc.messages:
            if m.round_number == round_num:
                prefix = "【主持人】" if m.niche_role == "moderator" else f"【{m.agent_name}】"
                lines.append(f"{prefix}: {m.content[:300]}")
        return "\n\n".join(lines)


# ── 单例 ──────────────────────────────────────────────────

_engine: Optional[PlazaEngine] = None


def get_plaza_engine() -> PlazaEngine:
    global _engine
    if _engine is None:
        _engine = PlazaEngine()
    return _engine
