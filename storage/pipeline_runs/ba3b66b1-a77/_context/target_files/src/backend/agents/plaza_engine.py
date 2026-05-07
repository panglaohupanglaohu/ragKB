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
_EXCHANGES_PER_ROUND = 3  # 每轮内交锋次数 — 模拟辩论短交锋
_SPEAKERS_PER_EXCHANGE = 2  # 每次交锋参与人数
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
            key=lambda p: (
                tier_order.get(p.seat_tier, 1),
                self._role_priority(p),
                p.niche_index,
            ),
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
            f"请开场，像技术辩论赛主持人一样推进讨论:\n"
            f"- 只用 2-3 句，短句表达，不要长篇铺陈\n"
            f"- 先点明主问题，再抛出第一个最关键的技术追问\n"
            f"- 问题要直接指向可执行方案、风险或约束，而不是泛泛而谈"
        )
        opening = await self._agent_speak(
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
                        f"你正在参与关于「{disc.topic}」的快速辩论。\n"
                        f"你是 {speaker.agent_name}（{speaker.role}）。"
                        f"第 {round_num} 轮，第 {ex_idx+1} 次交锋。\n\n"
                        f"刚才的交锋:\n{recent}\n\n"
                        f"规则——像苏格拉底辩论+伯里克利演说:\n"
                        f"- 只说 1-2 句话，30-60 字，一次只推进一个论点\n"
                        f"- 必须回应上一条的关键词或判断，然后补你的核心依据\n"
                        f"- 不要复述背景、不要客套、不要写标题或列表\n"
                        f"- 追求深度和锋利，给出可落地的指标、约束或机制\n"
                        f"- 像在辩论赛里被限时 15 秒，有哲思但极度凝练"
                    )
                    await self._agent_speak(
                        disc, speaker, speak_prompt, round_number=round_num,
                        niche_role=speaker.niche_role.value,
                    )

            # Moderator 收束本轮 (非最后一轮时)
            if round_num < disc.max_rounds:
                summary_prompt = (
                    f"你是主持人。第 {round_num} 轮 {exchanges} 次交锋已结束。\n\n"
                    f"本轮讨论:\n{self._format_round_messages(disc, round_num)}\n\n"
                    f"请像辩论赛主持人一样收束:\n"
                    f"- 1 句话点出本轮最有价值的共识或分歧\n"
                    f"- 1 个尖锐追问推动下一轮收敛到可执行方案\n"
                    f"- 总共不超过 2 句，40 字以内"
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

    async def _generate_agent_content(
        self,
        participant: Participant,
        prompt: str,
    ) -> str:
        try:
            result = await self._chat_fn(
                prompt,
                agent_id=participant.agent_id,
                system_prompt=(
                    f"你是 {participant.agent_name}，角色: {participant.role}。"
                    f"你在智能体广场辩论中发言。规则: 每次只说1-2句，30-60字，"
                    f"像苏格拉底的追问加伯里克利的演说——有深度但极度凝练。"
                    f"禁止列表、标题、客套、背景复述。直接输出观点。"
                ),
            )
            return result.response if result else "[无响应]"
        except Exception as e:
            logger.warning(f"Agent {participant.agent_id} 发言失败: {e}")
            return f"[{participant.agent_name} 暂时离线]"

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

    def _format_recent(self, disc: Discussion, limit: int = 5) -> str:
        """格式化最近N条消息 — 短窗口促进针锋相对."""
        recent = disc.messages[-limit:] if disc.messages else []
        lines = []
        for m in recent:
            prefix = "【主持人】" if m.niche_role == "moderator" else f"【{m.agent_name}】"
            lines.append(f"{prefix}: {m.content[:150]}")
        return "\n".join(lines)

    def _pick_exchange_speakers(
        self,
        round_speakers: List[Participant],
        exchange_idx: int,
        count: int,
    ) -> List[Participant]:
        """为每次交锋轮转选出参与者子集，确保覆盖面."""
        n = len(round_speakers)
        if n <= count:
            return round_speakers
        start = (exchange_idx * count) % n
        picked = []
        for i in range(count):
            picked.append(round_speakers[(start + i) % n])
        return picked

    def _role_priority(self, participant: Participant) -> int:
        return _CORE_ROLE_PRIORITY.get((participant.role or "").lower(), 99)

    def _select_round_speakers(
        self,
        speakers: List[Participant],
        round_num: int,
    ) -> List[Participant]:
        if len(speakers) <= _ROUND_SPEAKER_LIMIT:
            return speakers

        core_pool = [
            speaker for speaker in speakers
            if self._role_priority(speaker) < 5
        ]
        selected = core_pool[:4]
        selected_ids = {speaker.agent_id for speaker in selected}

        wildcard_pool = [
            speaker for speaker in speakers
            if speaker.agent_id not in selected_ids
        ]
        if wildcard_pool:
            wildcard = wildcard_pool[(round_num - 1) % len(wildcard_pool)]
            selected.append(wildcard)
            selected_ids.add(wildcard.agent_id)

        if len(selected) < _ROUND_SPEAKER_LIMIT:
            for speaker in speakers:
                if speaker.agent_id in selected_ids:
                    continue
                selected.append(speaker)
                selected_ids.add(speaker.agent_id)
                if len(selected) >= _ROUND_SPEAKER_LIMIT:
                    break

        return selected

    def _build_closing_brief(self, summary: str) -> str:
        lines = [line.strip() for line in summary.splitlines() if line.strip()]
        cleaned_lines = [self._strip_markdown(line) for line in lines]

        overview = next(
            (
                self._first_sentence(line)
                for line in cleaned_lines
                if self._is_summary_sentence(line)
            ),
            "核心方案与执行顺序已经收束。",
        )
        action = next(
            (
                self._first_sentence(line)
                for line in cleaned_lines
                if line.startswith("P0") or "任务名称" in line
            ),
            "先从 P0 任务切入实现接入基座。",
        )
        return f"本场收束：{overview}\n立即执行：{action}"

    def _strip_markdown(self, text: str) -> str:
        text = re.sub(r"[`*_#]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip(" -")

    def _first_sentence(self, text: str, limit: int = 72) -> str:
        chunks = re.split(r"(?<=[。！？])|\n", text)
        for chunk in chunks:
            candidate = chunk.strip()
            if candidate:
                return candidate[:limit].rstrip()
        return text[:limit].rstrip()

    def _is_summary_sentence(self, text: str) -> bool:
        if not text:
            return False
        if text.startswith("P") or "任务名称" in text or text.startswith("负责角色"):
            return False
        if re.match(r"^\d+[.、]\s*(技术概要|加权结论|执行计划|补充观察)$", text):
            return False
        normalized = text.strip(" :：.-")
        return normalized not in {
            "1 技术概要",
            "2 加权结论",
            "3 执行计划",
            "4 补充观察",
            "技术概要",
            "加权结论",
            "执行计划",
            "补充观察",
        }

    def _shape_debate_message(self, text: str, is_moderator: bool) -> str:
        text = re.sub(r"\s+", " ", (text or "").strip())
        if not text:
            return "[无响应]"

        max_chars = 48 if is_moderator else 88
        max_sentences = 2
        sentences = [
            part.strip()
            for part in re.split(r"(?<=[。！？!?；;])\s*", text)
            if part.strip()
        ]
        if not sentences:
            sentences = [text]

        shortened = "".join(sentences[:max_sentences]).strip()
        if len(shortened) <= max_chars:
            return shortened

        truncated = shortened[:max_chars].rstrip("，,;；:： ")
        if truncated and truncated[-1] not in "。！？!?":
            truncated += "。"
        return truncated


# ── 单例 ──────────────────────────────────────────────────

_engine: Optional[PlazaEngine] = None


def get_plaza_engine() -> PlazaEngine:
    global _engine
    if _engine is None:
        _engine = PlazaEngine()
    return _engine
