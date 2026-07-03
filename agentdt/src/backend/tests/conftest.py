# -*- coding: utf-8 -*-
"""pytest 共享 Fixtures — 测试流水线基础设施."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure src/backend is in path
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))


@pytest.fixture
def sample_lamport_clock():
    """提供一个标准的 Lamport 时钟实例."""
    from agents.ab_testing import LamportClock
    return LamportClock(node_id="test-node-1")


@pytest.fixture
def default_ewma_config():
    """提供默认 EWMA 配置."""
    from agents.ab_testing import EWMAConfig
    return EWMAConfig()


@pytest.fixture
def default_ewma_engine(default_ewma_config):
    """提供默认 EWMA 阈值引擎."""
    from agents.ab_testing import EWMAThresholdEngine
    return EWMAThresholdEngine(config=default_ewma_config)


@pytest.fixture
def sample_ab_metrics():
    """提供示例 A/B 测试指标."""
    from agents.ab_testing import ABTestMetrics
    return ABTestMetrics(
        false_upgrade_rate=0.05,
        resource_increase_pct=12.0,
        behavior_fingerprint_mutation_rate=0.02,
        anomaly_propagation_depth=1.5,
        prediction_error_rate=0.08,
        energy_increase_pct=3.0,
        temperature_slope=0.01,
        policy_evaluation_latency_ms=45.0,
        evolution_stagnation_rate=0.03,
    )


@pytest.fixture
def temp_team_store():
    """使用临时文件的 TeamStore (测试后自动清理)."""
    from agents.team_store import TeamStore

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{}")
        tmp_path = Path(f.name)

    store = TeamStore(path=tmp_path)
    yield store

    # 清理
    if tmp_path.exists():
        tmp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_task_store():
    """使用临时目录的 TaskStore."""
    from agents.task_store import TaskStore

    with tempfile.TemporaryDirectory() as tmpdir:
        store = TaskStore(base_dir=Path(tmpdir))
        yield store


@pytest.fixture
def team_manager(temp_team_store):
    """提供 TeamManager 实例 (使用临时存储)."""
    from agents.team_manager import TeamManager
    return TeamManager(store=temp_team_store)


@pytest.fixture
def sample_team_dict():
    """示例团队字典."""
    return {
        "team_id": "test-team-001",
        "name": "测试团队",
        "description": "自动化测试团队",
    }


@pytest.fixture
def sample_agent_dict():
    """示例 AgentProfile 字典."""
    return {
        "agent_id": "agent-001",
        "name": "TestAgent",
        "role": "developer",
        "state": "idle",
    }


@pytest.fixture
def sample_model_dict():
    """示例 ModelConfig 字典."""
    return {
        "model_id": "model-001",
        "name": "deepseek-v4-test",
        "provider": "deepseek",
        "max_tokens": 65536,
        "temperature": 0.7,
        "is_default": True,
    }


@pytest.fixture
def task_engine():
    """提供 TaskEngine 实例."""
    from agents.task_engine import TaskEngine
    from agents.task_store import TaskStore
    with tempfile.TemporaryDirectory() as tmpdir:
        yield TaskEngine(max_concurrency=4, store=TaskStore(base_dir=Path(tmpdir)))


@pytest.fixture
def fastapi_client() -> TestClient:
    """提供 FastAPI TestClient (自动设置环境变量)."""
    # 确保测试时不连真实 LLM
    os.environ.setdefault("DEEPSEEK_API_KEY", "test-key-not-real")
    os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")

    # Mock 掉 LLM 相关依赖，避免真实请求
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_llm_call():
    """Mock LLM 调用，返回固定响应."""
    with patch("agents.chat_harness.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = "这是模拟的 LLM 回复"
        yield mock


@pytest.fixture
def sample_task_dict():
    """示例任务字典."""
    return {
        "task_id": "task-001",
        "title": "测试任务",
        "description": "一个用于测试的任务",
        "agent_id": "agent-001",
        "priority": 2,
        "dependencies": [],
    }


# ── pytest 配置 ─────────────────────────────────────────────

pytest_plugins = []  # 可在此添加 pytest 插件
