# -*- coding: utf-8 -*-
"""Health endpoint regression tests."""

from __future__ import annotations

import pytest

import main as main_module


class _FakeRegistry:
    def __init__(self, entries):
        self._entries = dict(entries)

    def get(self, name):
        return self._entries.get(name)


@pytest.mark.asyncio
async def test_health_includes_sandbox_runtime_details(monkeypatch):
    from channels import marine_base as marine_base_module
    from sandbox import python_runner as runner_module

    monkeypatch.setattr(
        marine_base_module,
        "get_default_registry",
        lambda: _FakeRegistry({"system_evolution": object(), "bridge_chat": object()}),
    )
    monkeypatch.setattr(
        runner_module,
        "describe_sandbox_runtime",
        lambda: {"mode": "docker", "ready": True, "docker_available": True, "image_available": True},
    )
    monkeypatch.setattr(main_module, "_team_manager", object())

    payload = await main_module.health()

    assert payload.services["evolution"] is True
    assert payload.services["bridge_chat"] is True
    assert payload.services["agent_config"] is True
    assert payload.services["sandbox_runtime_ready"] is True
    assert payload.details["sandbox_runtime"]["mode"] == "docker"
