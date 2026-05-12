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
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Dict, List, Optional
from uuid import uuid4

from .plaza import (
    Discussion, DiscussionStatus, NicheRole, Participant,
    Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
)
from .plaza_store import PlazaStore

logger = logging.getLogger(__name__)

_ROUND_SPEAKER_LIMIT = 5
_EXCHANGES_PER_ROUND = 2  # 每轮内交锋次数
_SPEAKERS_PER_EXCHANGE = 3  # 每次交锋参与人数
_CORE_ROLE_PRIORITY = {
    "architect": 0,
    "researcher": 1,
    "developer": 2,
    "qa_engineer": 3,
    "qa": 3,
    "tester": 3,
    "devops": 4,
    "project_manager": 5,
    "documentation": 6,
}


class PlazaEngine:
    """广场引擎 — 管理广场、参与者和讨论编排."""

    def __init__(self):
        self._store = PlazaStore()
        self._plazas: Dict[str, Plaza] = self._store.load_all()
        self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
        self._discussion_locks: Dict[str, asyncio.Lock] = {}
        self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference

    def set_chat_fn(self, fn: Callable):
        """注入 ChatHarness.chat 异步函数."""
        self._chat_fn = fn

    def _get_agent_profile(self, agent_id: str):
        """从 TeamManager 获取完整 AgentProfile，用于注入个性."""
        try:
            from agents.api import _team_manager
            if _team_manager:
                for team in _team_manager.list_teams():
                    agent = team.get_agent(agent_id)
                    if agent:
                        return agent
        except Exception:
            pass
        return None

    def _build_agent_system_prompt(self, participant: Participant) -> str:
        """根据 AgentProfile 构建有个性的 system prompt."""
        profile = self._get_agent_profile(participant.agent_id)
        if profile:
            expertise = "、".join(profile.personality.expertise_areas) if profile.personality.expertise_areas else ""
            traits = "、".join(profile.metadata.get("traits", [])) if profile.metadata else ""
            parts = [
                f"你是 {profile.name}，职责: {profile.role}。",
                f"专长: {expertise}。" if expertise else "",
                f"性格特质: {traits}。" if traits else "",
                f"你的工作方式: {profile.system_prompt}" if profile.system_prompt else "",
                f"\n你正在一个智能体广场的讨论中发言。",
                f"请用自然的方式说话，像一个真实的专业人士在开会讨论。",
                f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。",
                f"不需要客套寒暄，但要说人话，不要像电报一样压缩。",
            ]
            return "".join(p for p in parts if p)
        # 回退到基础信息
        return (
            f"你是 {participant.agent_name}，职责: {participant.role}。"
            f"你正在一个智能体广场的讨论中发言。"
            f"请用自然的方式说话，像一个真实的专业人士在开会讨论。"
            f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。"
        )

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

        moderator = self._resolve_moderator(plaza, disc, participants)
        speakers = self._sort_speakers(participants, moderator)

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
            f"请开场:\n"
            f"- 用 2-4 句话点明讨论的核心问题\n"
            f"- 直接围绕用户提出的话题展开，不要自行转换或重新解读话题\n"
            f"- 然后向参与者提出第一个需要讨论的具体问题\n"
            f"- 说人话，像一个项目经理在主持会议"
        )
        opening = await self._speak_with_lock(
            disc, moderator, opening_prompt, round_number=0,
            niche_role="moderator",
        )

        # ── 多轮讨论 (辩论式交锋) ──
        for round_num in range(1, disc.max_rounds + 1):
            disc.current_round = round_num
            await self._broadcast(disc.id, {
                "type": "round_start", "round": round_num,
                "max_rounds": disc.max_rounds,
            })

            round_speakers = self._select_round_speakers(speakers, round_num)
            # 每轮多次短交锋，模拟辩论赛节奏
            exchanges = _EXCHANGES_PER_ROUND if disc.max_rounds <= 2 else 2
            for ex_idx in range(exchanges):
                # 轮转选人: 每次交锋选不同子集
                ex_speakers = self._pick_exchange_speakers(
                    round_speakers, ex_idx, _SPEAKERS_PER_EXCHANGE,
                )
                for speaker in ex_speakers:
                    # 获取最近 5 条作为即时上下文 (短窗口促进针锋相对)
                    recent = self._format_recent(disc, limit=5)
                    speak_prompt = (
                        f"你正在参与关于「{disc.topic}」的团队讨论。\n"
                        f"你是 {speaker.agent_name}（{speaker.role}）。"
                        f"第 {round_num} 轮，第 {ex_idx+1} 次发言。\n\n"
                        f"刚才的讨论:\n{recent}\n\n"
                        f"发言要求:\n"
                        f"- 结合你的专业背景，给出有实质内容的观点或建议\n"
                        f"- 回应上面讨论中你认为重要的点，然后补充你的看法\n"
                        f"- 可以提出具体的方案、步骤、注意事项\n"
                        f"- 说 3-5 句话，100-200 字左右，不要太短也不要写论文\n"
                        f"- 像在开会发言一样自然表达，不要用列表和标题"
                    )
                    await self._speak_with_lock(
                        disc, speaker, speak_prompt, round_number=round_num,
                        niche_role=speaker.niche_role.value,
                    )

            # Moderator 收束本轮 (非最后一轮时)
            if round_num < disc.max_rounds:
                summary_prompt = (
                    f"你是主持人。第 {round_num} 轮讨论已结束。\n\n"
                    f"本轮讨论:\n{self._format_round_messages(disc, round_num)}\n\n"
                    f"请小结本轮要点:\n"
                    f"- 总结大家达成的共识和仍有分歧的地方\n"
                    f"- 提出下一轮需要重点讨论的问题\n"
                    f"- 用 2-3 句话，自然表达"
                )
                await self._speak_with_lock(
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
            f"请生成可直接派发任务的技术型概要。核心原则——有取舍、有权重:\n"
            f"- build/构建/开发/架构/部署相关发言 = 权重最高(P0级)，这些人要真正动手执行\n"
            f"- 测试/QA/安全相关 = 中等权重(P1级)，是质量门禁\n"
            f"- 能耗/外围优化/观察类 = 低权重(P2级)，仅作为补充参考，绝不挤占主篇幅\n"
            f"- 如果能耗建议不影响主目标上线，就放到最后1行带过\n\n"
            f"输出结构 (严格按此格式，不要自由发挥):\n"
            f"## 技术概要\n"
            f"4-6 句写清: 主目标、核心方案、关键约束、最大风险、首要动作\n"
            f"必须是接到这份概要的人能直接开工的技术描述\n\n"
            f"## 加权结论 (P0→P1→P2)\n"
            f"- [P0] 结论 | 主要支持角色 | 为什么重要\n"
            f"- [P1] ...\n"
            f"- [P2] 仅保留 1 条最相关的低权重建议\n\n"
            f"## 执行计划\n"
            f"| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
            f"|---|---|---|---|---|---|\n"
            f"列出 3-5 个任务，按优先级排序\n\n"
            f"## 补充观察\n"
            f"1 句话带过能耗/外围建议即可\n\n"
            f"请用 Markdown 输出，简洁有力，能直接作为任务单下发。"
        )
        disc.summary = await self._generate_agent_content(
            moderator,
            final_prompt,
        )
        # 将最终总结中的执行计划提取到 disc.plan，供前端和派发使用
        disc.plan = {
            "revision_reason": "讨论收敛",
            "revised_at": datetime.now(timezone.utc).isoformat(),
            "content": disc.summary,
        }
        await self._broadcast(disc.id, {"type": "plan_updated", "plan": disc.plan})

        closing_msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id=moderator.agent_id,
            agent_name=moderator.agent_name or moderator.agent_id,
            role=moderator.role,
            niche_role="moderator",
            content=self._build_closing_brief(disc.summary),
            round_number=disc.max_rounds + 1,
            metadata={"summary_kind": "closing_brief"},
        )
        disc.messages.append(closing_msg)
        await self._broadcast(disc.id, {
            "type": "message",
            "message": closing_msg.to_dict(),
        })
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
        content = await self._generate_agent_content(participant, prompt)
        content = self._shape_debate_message(
            content,
            is_moderator=(niche_role == "moderator"),
        )

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

    async def _speak_with_lock(
        self, disc: Discussion, participant: Participant,
        prompt: str, round_number: int, niche_role: str = "",
    ) -> Optional[PlazaMessage]:
        async with self._get_discussion_lock(disc.id):
            return await self._agent_speak(
                disc, participant, prompt, round_number, niche_role,
            )

    async def publish_message(
        self,
        disc: Discussion,
        participant: Participant,
        content: str,
        round_number: int,
        niche_role: str = "",
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PlazaMessage:
        msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id=participant.agent_id,
            agent_name=participant.agent_name or participant.agent_id,
            role=participant.role,
            niche_role=niche_role or participant.niche_role.value,
            content=self._shape_debate_message(
                content,
                is_moderator=(niche_role == "moderator"),
            ),
            round_number=round_number,
            reply_to=reply_to,
            metadata=metadata or {},
        )
        disc.messages.append(msg)
        await self._broadcast(disc.id, {
            "type": "message",
            "message": msg.to_dict(),
        })
        return msg

    async def handle_live_interjection(
        self,
        plaza_id: str,
        discussion_id: str,
        user_message: str,
        user_msg_id: str,
    ) -> Dict[str, Optional[PlazaMessage]]:
        plaza = self._plazas.get(plaza_id)
        if not plaza:
            raise ValueError("广场不存在")
        disc = plaza.discussions.get(discussion_id)
        if not disc:
            raise ValueError("讨论不存在")

        participants = list(plaza.participants.values())
        moderator = self._resolve_moderator(plaza, disc, participants)
        if not moderator:
            raise ValueError("广场没有议事长")
        speakers = self._sort_speakers(participants, moderator)

        async with self._get_discussion_lock(disc.id):
            await self._broadcast(disc.id, {
                "type": "interjection_state",
                "state": "paused",
                "message": "议事长正在纠偏当前讨论节奏",
            })

            if not self._chat_fn:
                chosen = speakers[0] if speakers else None
                moderator_text = "这个追问有效，我先把当前节奏拧回主线上。"
                if chosen:
                    moderator_text += f"请 {chosen.agent_name} 先正面回应。"
                moderator_msg = await self.publish_message(
                    disc,
                    moderator,
                    moderator_text,
                    round_number=disc.current_round,
                    niche_role="moderator",
                    reply_to=user_msg_id,
                    metadata={"interjection_kind": "moderator_redirect", "nominated_agent_id": chosen.agent_id if chosen else ""},
                )
                speaker_msg = None
                if chosen:
                    speaker_msg = await self.publish_message(
                        disc,
                        chosen,
                        f"我先回应这个插话：{user_message[:60]}。当前更关键的是把它落到本轮的约束与方案上。",
                        round_number=disc.current_round,
                        niche_role=chosen.niche_role.value,
                        reply_to=moderator_msg.id,
                        metadata={"interjection_kind": "nominated_reply", "prompted_by": moderator.agent_id},
                    )
                # 模拟模式也生成执行计划
                plan_content = (
                    f"## 修订说明\n针对用户问题「{user_message[:40]}」修订\n\n"
                    f"## 执行计划\n"
                    f"| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
                    f"|---|---|---|---|---|---|\n"
                    f"| 1 | 回应用户问题 | {chosen.agent_name if chosen else '待定'} | P0 | 无 | 方案落地 |\n"
                )
                disc.plan = {
                    "revision_reason": user_message,
                    "revised_at": datetime.now(timezone.utc).isoformat(),
                    "content": plan_content,
                }
                wrap_msg = await self.publish_message(
                    disc,
                    moderator,
                    plan_content,
                    round_number=disc.current_round,
                    niche_role="moderator",
                    reply_to=speaker_msg.id if speaker_msg else moderator_msg.id,
                    metadata={"interjection_kind": "revised_plan"},
                )
                await self._broadcast(disc.id, {"type": "plan_updated", "plan": disc.plan})
                await self._broadcast(disc.id, {"type": "interjection_state", "state": "resumed"})
                self._store.save_plaza(plaza)
                return {"moderator_reply": moderator_msg, "nominated_reply": speaker_msg, "extra_replies": [], "moderator_resume": wrap_msg}

            chosen = self._pick_interjection_speaker(disc, speakers, user_message)
            candidate_lines = "\n".join(
                f"- {speaker.agent_id} | {speaker.agent_name} | {speaker.role}"
                for speaker in speakers[:8]
            )
            redirect_prompt = (
                f"你是本场讨论的议事长，当前讨论正在进行中，需要立刻纠偏。\n"
                f"讨论话题: 「{disc.topic}」\n"
                f"当前轮次: {disc.current_round}\n"
                f"最近讨论: \n{self._format_recent(disc, limit=8)}\n\n"
                f"用户插话: 「{user_message}」\n\n"
                f"候选回应者（必须从这里选一个 agent_id）:\n{candidate_lines}\n\n"
                f"严格输出：\n"
                f"REPLY: 你给用户和全场的纠偏回应，最后一句必须明确点名下一位回应者\n"
                f"NEXT: 候选中的 agent_id\n"
                f"只输出这两行。"
            )
            decision_text = await self._generate_agent_content(moderator, redirect_prompt)
            moderator_reply_text, chosen = self._parse_interjection_decision(
                decision_text,
                speakers,
                chosen,
            )
            if chosen:
                nomination_prefix = f"请 {chosen.agent_name} 先回应。"
                if not moderator_reply_text.startswith(nomination_prefix):
                    moderator_reply_text = f"{nomination_prefix}{moderator_reply_text}"
            moderator_msg = await self.publish_message(
                disc,
                moderator,
                moderator_reply_text,
                round_number=disc.current_round,
                niche_role="moderator",
                reply_to=user_msg_id,
                metadata={"interjection_kind": "moderator_redirect", "nominated_agent_id": chosen.agent_id if chosen else ""},
            )

            speaker_msg = None
            if chosen:
                speaker_prompt = (
                    f"你是 {chosen.agent_name}（{chosen.role}）。主持人刚刚点名你，要求你优先回应一次插话纠偏。\n"
                    f"讨论话题: 「{disc.topic}」\n"
                    f"用户插话: 「{user_message}」\n"
                    f"主持人刚才的话: 「{moderator_reply_text}」\n"
                    f"最近讨论: \n{self._format_recent(disc, limit=8)}\n\n"
                    f"请用 2-4 句直接回应，必须回答用户的具体问题，给出可落地的方案或约束，不要泛泛而谈。"
                )
                speaker_msg = await self._agent_speak(
                    disc,
                    chosen,
                    speaker_prompt,
                    round_number=disc.current_round,
                    niche_role=chosen.niche_role.value,
                )
                if speaker_msg:
                    speaker_msg.reply_to = moderator_msg.id
                    speaker_msg.metadata.update({
                        "interjection_kind": "nominated_reply",
                        "prompted_by": moderator.agent_id,
                    })

            # ── 追加 1-2 位相关智能体讨论用户问题 ──
            extra_replies: List[PlazaMessage] = []
            remaining_speakers = [s for s in speakers if s != chosen][:2]
            for extra_speaker in remaining_speakers:
                extra_prompt = (
                    f"你是 {extra_speaker.agent_name}（{extra_speaker.role}）。\n"
                    f"讨论话题: 「{disc.topic}」\n"
                    f"用户刚才提出了问题/建议: 「{user_message}」\n"
                    f"主持人点名的 {chosen.agent_name if chosen else '无'} 已回应: 「{speaker_msg.content if speaker_msg else '无'}」\n"
                    f"最近讨论: \n{self._format_recent(disc, limit=6)}\n\n"
                    f"请从你的专业角度补充 1-2 句，针对用户问题给出你的判断或补充方案。不要重复已有观点。"
                )
                extra_msg = await self._agent_speak(
                    disc,
                    extra_speaker,
                    extra_prompt,
                    round_number=disc.current_round,
                    niche_role=extra_speaker.niche_role.value,
                )
                if extra_msg:
                    extra_msg.reply_to = speaker_msg.id if speaker_msg else moderator_msg.id
                    extra_msg.metadata.update({
                        "interjection_kind": "supplementary_reply",
                        "prompted_by": moderator.agent_id,
                    })
                    extra_replies.append(extra_msg)

            # ── 议事长生成修订后的执行计划 ──
            all_responses = []
            if speaker_msg:
                all_responses.append(f"{chosen.agent_name}: {speaker_msg.content}")
            for er in extra_replies:
                all_responses.append(f"{er.agent_name}: {er.content}")
            responses_text = "\n".join(all_responses) if all_responses else "无回应"

            plan_prompt = (
                f"你是议事长。你刚刚针对用户的插话完成了一次纠偏讨论。\n"
                f"讨论话题: 「{disc.topic}」\n"
                f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n"
                f"用户插话: 「{user_message}」\n"
                f"各位回应:\n{responses_text}\n\n"
                f"现有执行计划:\n{json.dumps(disc.plan, ensure_ascii=False) if disc.plan else '无'}\n\n"
                f"请根据以上讨论结果，输出修订后的执行计划。严格按以下格式:\n"
                f"## 修订说明\n"
                f"1 句话说明本次修订的原因和变更要点\n\n"
                f"## 执行计划\n"
                f"| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
                f"|---|---|---|---|---|---|\n"
                f"列出 3-6 个任务，按优先级排序。必须体现用户刚提出的问题/建议的处理方式。\n\n"
                f"只输出以上内容，不要客套。"
            )
            plan_text = await self._generate_agent_content(moderator, plan_prompt)

            # 存储修订计划
            disc.plan = {
                "revision_reason": user_message,
                "revised_at": datetime.now(timezone.utc).isoformat(),
                "content": plan_text,
            }

            # 议事长发出修订后的执行计划作为消息
            wrap_msg = await self.publish_message(
                disc,
                moderator,
                plan_text,
                round_number=disc.current_round,
                niche_role="moderator",
                reply_to=extra_replies[-1].id if extra_replies else (speaker_msg.id if speaker_msg else moderator_msg.id),
                metadata={"interjection_kind": "revised_plan"},
            )

            # 广播计划更新事件，前端可即时刷新
            await self._broadcast(disc.id, {
                "type": "plan_updated",
                "plan": disc.plan,
            })

            await self._broadcast(disc.id, {"type": "interjection_state", "state": "resumed"})
            self._store.save_plaza(plaza)
            return {
                "moderator_reply": moderator_msg,
                "nominated_reply": speaker_msg,
                "extra_replies": extra_replies,
                "moderator_resume": wrap_msg,
            }

    async def _generate_agent_content(
        self,
        participant: Participant,
        prompt: str,
    ) -> str:
        try:
            result = await self._chat_fn(
                prompt,
                agent_id=participant.agent_id,
                system_prompt=self._build_agent_system_prompt(participant),
            )
            return result.response if result else "[无响应]"
        except Exception as e:
            logger.warning(f"Agent {participant.agent_id} 发言失败: {e}")
            return f"[{participant.agent_name} 暂时离线]"

    async def regenerate_plan(self, plaza_id: str, disc_id: str) -> dict:
        """议事长根据全部对话重新生成执行计划."""
        plaza = self.get_plaza(plaza_id)
        if not plaza:
            return {"error": "广场不存在"}
        disc = self.get_discussion(plaza_id, disc_id)
        if not disc:
            return {"error": "讨论不存在"}

        moderator = next(
            (p for p in disc.participants if p.niche_role == "moderator"), None
        )
        if not moderator:
            return {"error": "无议事长"}

        # 收集全部对话（含用户插话）
        recent = "\n".join(
            f"[{m.agent_name}] {m.content[:200]}"
            for m in disc.messages[-30:]
        )

        plan_prompt = (
            f"你是议事长。请根据以下全部对话记录，重新生成一份完整的执行计划。\n"
            f"讨论话题: 「{disc.topic}」\n"
            f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n\n"
            f"全部对话:\n{recent}\n\n"
            f"现有执行计划:\n{json.dumps(disc.plan, ensure_ascii=False) if disc.plan else '无'}\n\n"
            f"请根据对话中所有观点（特别是用户的提问和建议），输出修订后的执行计划。严格按以下格式:\n"
            f"## 修订说明\n"
            f"1 句话说明本次修订的原因和变更要点\n\n"
            f"## 执行计划\n"
            f"| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
            f"|---|---|---|---|---|---|\n"
            f"列出 3-6 个任务，按优先级排序。\n\n"
            f"只输出以上内容，不要客套。"
        )
        plan_text = await self._generate_agent_content(moderator, plan_prompt)

        disc.plan = {
            "revision_reason": "用户请求刷新执行计划",
            "revised_at": datetime.now(timezone.utc).isoformat(),
            "content": plan_text,
        }

        # 议事长发出修订计划作为消息
        plan_msg = await self.publish_message(
            disc,
            moderator,
            plan_text,
            round_number=disc.current_round or 1,
            niche_role="moderator",
            metadata={"interjection_kind": "revised_plan"},
        )

        await self._broadcast(disc.id, {"type": "plan_updated", "plan": disc.plan})
        self._store.save_plaza(plaza)