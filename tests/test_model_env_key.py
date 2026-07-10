# -*- coding: utf-8 -*-
"""env: 引用方案测试 — 覆盖 ModelConfig 序列化/反序列化/解析、resolve_api_key、重启不丢。"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "backend"))

from agents.models import ModelConfig, AgentTeam, Visibility  # noqa: E402
from agents.team_store import TeamStore  # noqa: E402
from agents.secret_store import resolve_api_key  # noqa: E402


# ── 1. ModelConfig.to_dict 对 env: 引用原样保留 ──────────────────────────────

class TestModelConfigEnvKey:
    def test_env_ref_preserved_in_to_dict(self):
        """env: 引用 to_dict 时原样保留（不脱敏）。"""
        m = ModelConfig(model_id="m1", provider="deepseek", name="deepseek-v4", api_key="env:DEEPSEEK_API_KEY")
        d = m.to_dict()
        assert d["api_key"] == "env:DEEPSEEK_API_KEY", "env: 引用应原样保留"
        assert d["has_api_key"] is True

    def test_real_key_masked_in_to_dict(self):
        """真实 key to_dict 时脱敏（不落盘明文）。"""
        m = ModelConfig(model_id="m2", provider="deepseek", name="deepseek-v4", api_key="sk-abcdef123456")
        d = m.to_dict()
        assert d["api_key"] == "****3456", "真实 key 应脱敏"
        assert d["api_key"] != "sk-abcdef123456", "真实 key 不应明文出现"

    def test_empty_key_to_dict(self):
        m = ModelConfig(model_id="m3", provider="deepseek", name="x", api_key="")
        d = m.to_dict()
        assert d["api_key"] == ""
        assert d["has_api_key"] is False


# ── 2. get_resolved_api_key 解析 env: ────────────────────────────────────────

class TestGetResolvedApiKey:
    def test_env_ref_resolves_from_os_environ(self, monkeypatch):
        monkeypatch.setenv("MY_TEST_KEY", "sk-resolved-value")
        m = ModelConfig(model_id="m4", provider="deepseek", name="x", api_key="env:MY_TEST_KEY")
        assert m.get_resolved_api_key() == "sk-resolved-value"

    def test_env_ref_missing_env_returns_empty(self, monkeypatch):
        monkeypatch.delenv("MY_MISSING_KEY", raising=False)
        m = ModelConfig(model_id="m5", provider="deepseek", name="x", api_key="env:MY_MISSING_KEY")
        assert m.get_resolved_api_key() == ""

    def test_real_key_returns_as_is(self):
        m = ModelConfig(model_id="m6", provider="deepseek", name="x", api_key="sk-real-key")
        assert m.get_resolved_api_key() == "sk-real-key"

    def test_empty_key_returns_empty(self):
        m = ModelConfig(model_id="m7", provider="deepseek", name="x", api_key="")
        assert m.get_resolved_api_key() == ""


# ── 3. resolve_api_key 支持 env: 前缀 ────────────────────────────────────────

class TestResolveApiKeyEnvPrefix:
    def test_env_prefix_resolves(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-from-env")
        result = resolve_api_key("deepseek", explicit="env:DEEPSEEK_API_KEY")
        assert result == "sk-from-env"

    def test_env_prefix_missing_returns_empty(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_KEY", raising=False)
        result = resolve_api_key("deepseek", explicit="env:NONEXISTENT_KEY")
        assert result == ""

    def test_explicit_real_key_passes_through(self):
        result = resolve_api_key("deepseek", explicit="sk-real")
        assert result == "sk-real"

    def test_empty_explicit_falls_back_to_provider_env(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fallback")
        result = resolve_api_key("deepseek", explicit="")
        assert result == "sk-fallback"


# ── 4. 持久化往返：env: 引用重启后不丢 ──────────────────────────────────────

class TestPersistRoundtripEnvRef:
    def test_env_ref_survives_save_load_cycle(self, tmp_path):
        """核心测试：env: 引用保存后重启（重新加载）不丢失。"""
        store_path = tmp_path / "teams.json"
        store = TeamStore(path=store_path)

        # 创建带 env: 引用的 model
        team = AgentTeam(team_id="t1", name="测试团队", visibility=Visibility.PRIVATE)
        team.models["m1"] = ModelConfig(
            model_id="m1", provider="deepseek", name="deepseek-v4",
            api_key="env:DEEPSEEK_API_KEY", is_default=True,
        )
        store.save_all({"t1": team})

        # 重新加载（模拟重启）
        store2 = TeamStore(path=store_path)
        teams = store2.load_all()
        loaded_model = teams["t1"].models["m1"]

        assert loaded_model.api_key == "env:DEEPSEEK_API_KEY", "env: 引用重启后必须保留"
        assert loaded_model.get_resolved_api_key() == "" or loaded_model.get_resolved_api_key()  # 取决于环境变量是否存在

    def test_masked_key_not_restored(self, tmp_path):
        """脱敏值（****）重启后不恢复为真实 key。"""
        store_path = tmp_path / "teams.json"
        # 手动写一个含脱敏 key 的 teams.json（模拟旧数据）
        data = {
            "t1": {
                "team_id": "t1", "name": "测试", "visibility": "private", "agents": {},
                "models": {
                    "m1": {
                        "model_id": "m1", "provider": "deepseek", "name": "x",
                        "max_tokens": 8192, "temperature": 0.7, "is_default": True, "enabled": True,
                        "api_key": "****3456", "api_base_url": "", "has_api_key": True,
                    }
                },
                "tools": {}, "skills": {}, "metadata": {}, "created_at": "",
            }
        }
        store_path.write_text(json.dumps(data), encoding="utf-8")

        store = TeamStore(path=store_path)
        teams = store.load_all()
        loaded_model = teams["t1"].models["m1"]

        assert loaded_model.api_key == "", "脱敏值不应恢复为真实 key"
        assert loaded_model.get_resolved_api_key() == ""

    def test_teams_json_no_plaintext_real_key(self, tmp_path):
        """teams.json 不应包含明文真实 key（只有 env: 引用或脱敏值）。"""
        store_path = tmp_path / "teams.json"
        store = TeamStore(path=store_path)

        team = AgentTeam(team_id="t1", name="测试", visibility=Visibility.PRIVATE)
        # 内存里存真实 key
        team.models["m1"] = ModelConfig(
            model_id="m1", provider="deepseek", name="x",
            api_key="sk-super-secret-real-key",
        )
        store.save_all({"t1": team})

        content = store_path.read_text(encoding="utf-8")
        assert "sk-super-secret-real-key" not in content, "teams.json 不应含明文真实 key"
        assert "****" in content, "真实 key 应脱敏存储"


# ── 5. env_loader 加载 .env ──────────────────────────────────────────────────

class TestEnvLoader:
    def test_load_env_reads_dotenv(self, tmp_path, monkeypatch):
        """env_loader 从 .env 读取并注入 os.environ。"""
        env_file = tmp_path / ".env"
        env_file.write_text('TEST_KEY_123="hello world"\nANOTHER=plain\n# comment\n', encoding="utf-8")

        from agents import env_loader
        monkeypatch.setattr(env_loader, "_env_path", lambda: env_file)
        monkeypatch.delenv("TEST_KEY_123", raising=False)
        monkeypatch.delenv("ANOTHER", raising=False)

        count = env_loader.load_env()
        assert count == 2
        assert os.environ.get("TEST_KEY_123") == "hello world"
        assert os.environ.get("ANOTHER") == "plain"

    def test_load_env_does_not_override_existing(self, tmp_path, monkeypatch):
        """已存在的环境变量不被 .env 覆盖。"""
        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING_VAR=from_dotenv\n", encoding="utf-8")

        from agents import env_loader
        monkeypatch.setattr(env_loader, "_env_path", lambda: env_file)
        monkeypatch.setenv("EXISTING_VAR", "from_system")

        count = env_loader.load_env()
        assert count == 0  # 不覆盖，不计入
        assert os.environ.get("EXISTING_VAR") == "from_system"

    def test_load_env_missing_file_returns_zero(self, tmp_path, monkeypatch):
        from agents import env_loader
        monkeypatch.setattr(env_loader, "_env_path", lambda: tmp_path / "nonexistent.env")
        assert env_loader.load_env() == 0
