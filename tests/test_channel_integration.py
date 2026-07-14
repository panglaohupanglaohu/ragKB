# -*- coding: utf-8 -*-
"""通道绑定能力：总线权限、合并写回、物竞 suggest."""

from agents.agent_channel_bus import (
    agent_can_publish,
    agent_can_subscribe,
    apply_bindings_to_agent,
    clear_bus,
    list_channel_bindings,
    merge_channel_bindings,
    publish_message,
    read_subscribed,
)
from sandbox.channel_integration import build_channel_suggestions, default_team_bus


class _A:
    def __init__(self, channels=None):
        self.channels = channels or []
        self.agent_id = "a1"


def test_default_bus_name():
    assert default_team_bus("aws-ops") == "aws-ops_bus"


def test_resolve_team_bus_prefers_existing_binding():
    """真身 aws_ops_bus 优先于 default aws-ops_bus，避免写回分叉."""
    from sandbox.channel_integration import resolve_team_bus
    bus = resolve_team_bus(
        "aws-ops",
        {
            "aws_mon": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": True}],
            "aws_lead": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": False}],
        },
    )
    assert bus == "aws_ops_bus"
    # 无已有绑定时才 fallback
    assert resolve_team_bus("aws-ops", {}) == "aws-ops_bus"


def test_merge_and_permissions():
    existing = [
        {"channel_name": "t_bus", "subscribe": True, "publish": False, "priority": 0},
    ]
    merged = merge_channel_bindings(existing, [
        {"channel_name": "t_bus", "publish": True, "priority": 5, "source": "eco_drill"},
        {"channel_name": "help_bus", "subscribe": True, "publish": True},
    ])
    names = {c["channel_name"] for c in merged}
    assert "t_bus" in names and "help_bus" in names
    t = next(c for c in merged if c["channel_name"] == "t_bus")
    assert t["publish"] is True and t["priority"] == 5

    agent = _A()
    apply_bindings_to_agent(agent, merged)
    assert agent_can_publish(agent, "t_bus")[0] is True
    assert agent_can_subscribe(agent, "t_bus")[0] is True
    assert agent_can_publish(agent, "unknown")[0] is False


def test_legacy_empty_bindings_allow():
    agent = _A([])
    assert agent_can_publish(agent, "any")[0] is True
    assert agent_can_subscribe(agent, "any")[0] is True


def test_bus_publish_read():
    clear_bus("teamX")
    agent = _A()
    apply_bindings_to_agent(agent, [
        {"channel_name": "teamX_bus", "subscribe": True, "publish": True},
    ])
    publish_message("teamX", "teamX_bus", from_agent_id="a1", content="hello")
    msgs = read_subscribed("teamX", agent)
    assert any(m.get("content") == "hello" for m in msgs)
    clear_bus("teamX")


def test_build_channel_suggestions_from_genome_and_timeline():
    result = {
        "final_ranking": [
            {
                "agent_id": "aws_mon",
                "survival_ticks": 100,
                "collab_genome": {
                    "share_tendency": 0.8,
                    "signal_tendency": 0.9,
                    "follow_tendency": 0.3,
                    "mate_choosiness": 0.5,
                },
            },
            {
                "agent_id": "aws_ops",
                "survival_ticks": 80,
                "collab_genome": {
                    "share_tendency": 0.2,
                    "signal_tendency": 0.2,
                    "follow_tendency": 0.9,
                    "mate_choosiness": 0.1,
                },
            },
        ],
        "timeline": {
            "steps": [
                {
                    "actions": {
                        "aws_mon": {"signals": ["FOOD@es"], "shared_to": "aws_ops", "followed": False},
                        "aws_ops": {"signals": [], "followed": True, "shared_to": None},
                    }
                }
            ]
        },
    }
    # 有真身绑定 → bus 用已有名
    rep = build_channel_suggestions(
        result,
        team_id="aws-ops",
        top_k=12,
        agent_channels={
            "aws_mon": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": False}],
            "aws_ops": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": False}],
        },
    )
    assert rep["count"] >= 1
    assert rep["bus_name"] == "aws_ops_bus"
    mon = next(s for s in rep["suggestions"] if s["agent_id"] == "aws_mon")
    d0 = mon["channel_diffs"][0]
    assert d0["channel_name"] == "aws_ops_bus"
    assert d0["publish"] is True  # high signal
    assert d0["subscribe"] is True  # share
    ops = next(s for s in rep["suggestions"] if s["agent_id"] == "aws_ops")
    assert ops["channel_diffs"][0]["subscribe"] is True

    # merge 后仍是单通道（不分叉）
    from agents.agent_channel_bus import merge_channel_bindings, apply_bindings_to_agent, list_channel_bindings, agent_can_publish
    class _A:
        def __init__(self):
            self.channels = [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": False}]
            self.agent_id = "aws_mon"
    agent = _A()
    merged = merge_channel_bindings(list_channel_bindings(agent), mon["channel_diffs"])
    apply_bindings_to_agent(agent, merged)
    names = [c["channel_name"] for c in list_channel_bindings(agent)]
    assert names == ["aws_ops_bus"]
    assert agent_can_publish(agent, "aws_ops_bus")[0] is True
