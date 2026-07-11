# -*- coding: utf-8 -*-
"""XB-8: 小虎 Mei Ling 断链根治 单测

覆盖：
  XB-8.1 cat_speak 凭据三级回退
  XB-8.2 _sync_default_model_to_harness 用 get_resolved_api_key
  XB-8.3 bug-045 兜底文案
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))


# ═══════════════════════════════════════════════════════════════
# XB-8.2: _sync_default_model_to_harness uses get_resolved_api_key
# ═══════════════════════════════════════════════════════════════

class TestSyncDefaultModelToHarness:
    def test_uses_resolved_api_key(self):
        """_sync_default_model_to_harness 应调用 get_resolved_api_key() 而非直接用 api_key."""
        from agents.api import _sync_default_model_to_harness

        # Mock team with a default model that has env: reference
        mock_model = MagicMock()
        mock_model.is_default = True
        mock_model.provider = "deepseek"
        mock_model.api_key = "env:FAKE_KEY_VAR"
        mock_model.api_base_url = "https://api.deepseek.com"
        mock_model.name = "deepseek-chat"
        mock_model.max_tokens = 65536
        mock_model.temperature = 0.2
        mock_model.get_resolved_api_key.return_value = "resolved_real_key_123"

        mock_team = MagicMock()
        mock_team.models = {"m1": mock_model}

        mock_harness = MagicMock()
        mock_harness.get_provider_config.return_value = MagicMock(
            max_tokens=65536, temperature=0.2
        )

        with patch("agents.api.get_chat_harness", return_value=mock_harness):
            _sync_default_model_to_harness(mock_team)

        # Verify get_resolved_api_key was called
        mock_model.get_resolved_api_key.assert_called_once()
        # Verify harness got the resolved key, not the env reference
        call_args = mock_harness.update_default_provider.call_args
        assert call_args.kwargs["api_key"] == "resolved_real_key_123"
        assert call_args.kwargs["api_key"] != "env:FAKE_KEY_VAR"


# ═══════════════════════════════════════════════════════════════
# XB-8.1: cat_speak 凭据三级回退
# ═══════════════════════════════════════════════════════════════

class TestCatSpeakCredentialFallback:
    def test_team_model_key_used_when_default_empty(self):
        """当 harness 默认无 key 但 pet_squad 团队模型有 key 时，应使用团队模型 key."""
        from agents.api import CatSpeakRequest
        from agents.chat_harness import ProviderConfig

        # Mock harness with no default key
        mock_harness = MagicMock()
        mock_default_cfg = MagicMock()
        mock_default_cfg.api_key = ""  # 空——模拟未配全局默认
        mock_default_cfg.provider.value = "deepseek"
        mock_default_cfg.api_base_url = ""
        mock_default_cfg.model = "deepseek-chat"
        mock_default_cfg.max_tokens = 65536
        mock_default_cfg.temperature = 0.2
        mock_harness.get_provider_config.return_value = mock_default_cfg

        # Mock pet_squad team with default model that has resolved key
        mock_model = MagicMock()
        mock_model.is_default = True
        mock_model.provider = "deepseek"
        mock_model.api_base_url = "https://api.deepseek.com"
        mock_model.name = "deepseek-chat"
        mock_model.max_tokens = 65536
        mock_model.temperature = 0.2
        mock_model.get_resolved_api_key.return_value = "team_model_key_abc"

        mock_team = MagicMock()
        mock_team.skills = {}
        mock_team.models = {"m1": mock_model}

        mock_tm = MagicMock()
        mock_tm.get_team.return_value = mock_team

        # Mock harness.chat to capture config_override
        mock_result = MagicMock()
        mock_result.response = "A proverb a day keeps the wolf away."
        mock_result.error = None
        mock_harness.chat = AsyncMock(return_value=mock_result)

        with patch("agents.api.get_chat_harness", return_value=mock_harness):
            with patch("agents.api._tm", return_value=mock_tm):
                from agents.api import cat_speak
                req = CatSpeakRequest(context="test")
                result = asyncio.run(cat_speak(req))

        # Verify harness.chat was called with config_override containing team key
        chat_kwargs = mock_harness.chat.call_args.kwargs
        assert "config_override" in chat_kwargs
        cfg_override = chat_kwargs["config_override"]
        assert cfg_override is not None
        assert cfg_override.api_key == "team_model_key_abc"

    def test_falls_back_to_default_when_team_has_no_key(self):
        """当 pet_squad 团队模型也没有 key 时，config_override 应为 None（走默认）."""
        from agents.api import CatSpeakRequest

        mock_harness = MagicMock()
        mock_default_cfg = MagicMock()
        mock_default_cfg.api_key = "default_key_123"
        mock_default_cfg.provider.value = "deepseek"
        mock_harness.get_provider_config.return_value = mock_default_cfg

        mock_model = MagicMock()
        mock_model.is_default = True
        mock_model.get_resolved_api_key.return_value = ""  # 团队模型也没 key

        mock_team = MagicMock()
        mock_team.skills = {}
        mock_team.models = {"m1": mock_model}

        mock_tm = MagicMock()
        mock_tm.get_team.return_value = mock_team

        mock_result = MagicMock()
        mock_result.response = "Some proverb."
        mock_result.error = None
        mock_harness.chat = AsyncMock(return_value=mock_result)

        with patch("agents.api.get_chat_harness", return_value=mock_harness):
            with patch("agents.api._tm", return_value=mock_tm):
                from agents.api import cat_speak
                req = CatSpeakRequest(context="test")
                asyncio.run(cat_speak(req))

        chat_kwargs = mock_harness.chat.call_args.kwargs
        # Default has key, so config_override should be None (use default)
        assert chat_kwargs.get("config_override") is None


# ═══════════════════════════════════════════════════════════════
# XB-8.3: bug-045 兜底文案
# ═══════════════════════════════════════════════════════════════

class TestBug045Fallback:
    def test_llm_unavailable_returns_english_proverb(self):
        """LLM 不可用时应返回英文谚语，而非中文降级文案."""
        from agents.api import CatSpeakRequest

        mock_harness = MagicMock()
        mock_default_cfg = MagicMock()
        mock_default_cfg.api_key = "some_key"
        mock_default_cfg.provider.value = "deepseek"
        mock_harness.get_provider_config.return_value = mock_default_cfg

        # Simulate LLM unavailable
        mock_result = MagicMock()
        mock_result.response = "我是 AgentsGroup2026 智能体…LLM 未连接"
        mock_result.error = "connection_refused"
        mock_harness.chat = AsyncMock(return_value=mock_result)

        mock_tm = MagicMock()
        mock_tm.get_team.return_value = None

        with patch("agents.api.get_chat_harness", return_value=mock_harness):
            with patch("agents.api._tm", return_value=mock_tm):
                from agents.api import cat_speak
                req = CatSpeakRequest()
                result = asyncio.run(cat_speak(req))

        assert result["success"] is False
        # Reply should be an English proverb, not Chinese
        reply = result["reply"]
        assert len(reply) > 10
        assert "智能体" not in reply
        assert "LLM" not in reply
        # Should be ASCII English
        assert all(ord(c) < 128 for c in reply)
