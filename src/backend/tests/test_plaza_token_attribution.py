# -*- coding: utf-8 -*-
"""议事广场 LLM 调用 Token 归因回归测试.

回归根因：`PlazaEngine._generate_agent_content` 调用 `chat_fn` 时未包裹
`token_scope`，导致广场讨论的 LLM token 全部归到默认 `phase="task"`，
`by_phase.plaza` 恒为 0。这会让两杠杆拆分（Skill vs 协作）失真、
成本页成本构成缺失 plaza 段。

本测试用 mock `chat_fn` 直接验证：调用 plaza 引擎发言后，记账漏斗里
必须有 `phase="plaza"` 的记录。
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from agents.budget.models import UsageRecord
from agents.budget.store import UsageStore
from agents.plaza import Participant, SeatTier
from agents.plaza_engine import PlazaEngine
from agents.token_context import get_token_ctx


@pytest.fixture
def temp_usage_store(monkeypatch, tmp_path):
    """隔离的 UsageStore + 重置全局单例。"""
    from agents.budget import store as store_module

    db_path = tmp_path / "usage.db"
    monkeypatch.setattr(store_module, "_DB_PATH", db_path)
    monkeypatch.setattr(store_module, "_usage_store", None)
    return UsageStore(db_path)


def _make_participant(agent_id: str = "build_architect") -> Participant:
    return Participant(
        agent_id=agent_id,
        agent_name="架构师",
        role="architect",
        seat_tier=SeatTier.INNER,
    )


class TestPlazaTokenAttribution:
    """广场发言的 LLM token 必须归因到 phase=plaza。"""

    @pytest.mark.asyncio
    async def test_plaza_speech_attributed_to_plaza_phase(
        self, temp_usage_store, monkeypatch
    ):
        """广场发言产生的 LLM 调用，记账漏斗里 phase 必须是 'plaza'。

        复现路径：plaza_engine._generate_agent_content → chat_fn（mock）。
        mock 的 chat_fn 直接调用 budget_guard.record_usage（模拟真实记账漏斗
        在 chat_harness 中的行为：读 get_token_ctx() 落 phase 字段）。
        """
        recorded_phases: list[str] = []

        async def fake_chat_fn(prompt, *, agent_id="", system_prompt=None):
            # 模拟 chat_harness 记账漏斗：读当前 token 归因上下文落库
            ctx = get_token_ctx()
            recorded_phases.append(ctx.get("phase", "task"))
            temp_usage_store.record_usage(
                UsageRecord(
                    session_id="plaza-sess-1",
                    agent_id=agent_id,
                    team_id=ctx.get("team_id", ""),
                    model="deepseek-v4-pro",
                    input_tokens=100,
                    output_tokens=50,
                    total_tokens=150,
                    phase=ctx.get("phase", "task"),
                    run_id=ctx.get("run_id", ""),
                )
            )
            return SimpleNamespace(response="这是一条广场发言。")

        engine = PlazaEngine()
        engine.set_chat_fn(fake_chat_fn)

        # 调用广场发言（不走降级路径）
        monkeypatch.setattr(engine, "_llm_degraded_until", 0.0)
        monkeypatch.setattr(
            engine, "_is_unusable_llm_text", lambda text: False
        )

        content = await engine._generate_agent_content(
            _make_participant(),
            "请就 API 设计发表观点",
            plaza_id="plaza-1",
            discussion_id="disc-1",
            discussion_topic="API 设计评审",
            round_number=1,
        )

        # 发言成功
        assert content == "这是一条广场发言。"
        # 关键断言：phase 必须是 plaza，不能回退到 task
        assert "plaza" in recorded_phases, (
            f"广场发言的 LLM 调用未归因到 phase=plaza，实际: {recorded_phases}"
        )
        # 落库记录验证
        import sqlite3
        conn = sqlite3.connect(str(temp_usage_store.path))
        rows = conn.execute(
            "SELECT phase FROM usage_log WHERE session_id='plaza-sess-1'"
        ).fetchall()
        conn.close()
        assert any(r[0] == "plaza" for r in rows), (
            f"usage_log 里没有 phase=plaza 的记录，实际 phases: {[r[0] for r in rows]}"
        )
