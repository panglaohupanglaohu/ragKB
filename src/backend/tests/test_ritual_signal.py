# -*- coding: utf-8 -*-
"""信号仪式化测试 — RitualSignal 枚举 + declare_signal 粗判规则.

对应 docs/Agent仿生生态运行时todos.md P5-1。
"""

from __future__ import annotations

from agents.plaza import Participant
from agents.plaza_engine import PlazaEngine, RitualSignal


class TestDeclareSignal:
    def _engine(self):
        return PlazaEngine()

    def _participant(self):
        return Participant(agent_id="a1", agent_name="测试员", role="developer")

    def test_empty_text_defaults_to_supplement(self):
        engine = self._engine()
        signal = engine.declare_signal(self._participant(), "")
        assert signal == RitualSignal.SUPPLEMENT

    def test_question_mark_triggers_challenge(self):
        engine = self._engine()
        signal = engine.declare_signal(self._participant(), "这个方案真的可行吗？")
        assert signal == RitualSignal.CHALLENGE

    def test_agree_keyword_triggers_agree(self):
        engine = self._engine()
        signal = engine.declare_signal(self._participant(), "我同意这个方案，没错。")
        assert signal == RitualSignal.AGREE

    def test_digress_keyword_triggers_digress(self):
        engine = self._engine()
        signal = engine.declare_signal(self._participant(), "我们好像扯远了，回到主题吧。")
        assert signal == RitualSignal.DIGRESS

    def test_neutral_text_defaults_to_supplement(self):
        engine = self._engine()
        signal = engine.declare_signal(self._participant(), "我建议先梳理一下现状。")
        assert signal == RitualSignal.SUPPLEMENT

    def test_digress_takes_priority_over_challenge(self):
        """优先级：digress > challenge —— 同时命中时应判 digress."""
        engine = self._engine()
        signal = engine.declare_signal(self._participant(), "这样扯远了吧？回到主题。")
        assert signal == RitualSignal.DIGRESS

    def test_digress_signal_does_not_break_role_priority_sorting(self):
        """验证 digress 判定命中后，后续 _role_priority 排序不报错（管道打通性检查）."""
        engine = self._engine()
        participants = [
            Participant(agent_id="a1", role="architect"),
            Participant(agent_id="a2", role="developer"),
            Participant(agent_id="a3", role="unknown_role"),
        ]
        signal = engine.declare_signal(participants[2], "这个跑题了")
        assert signal == RitualSignal.DIGRESS
        # 排序不应因为出现过 digress 信号而报错
        sorted_participants = sorted(participants, key=lambda p: engine._role_priority(p))
        assert sorted_participants[0].role == "architect"


class TestRitualSignalEnum:
    def test_enum_values_are_fixed_set(self):
        values = {s.value for s in RitualSignal}
        assert values == {"supplement", "challenge", "agree", "court", "digress"}

    def test_enum_is_str_subclass_for_json_serialization(self):
        assert isinstance(RitualSignal.COURT, str)
        assert RitualSignal.COURT == "court"
