# -*- coding: utf-8 -*-
"""Fingerprint 模块单元测试 — 模板提取、动态剔除、哈希、自检、稳定性监控."""

from __future__ import annotations

import time

import pytest

from agents.fingerprint import (
    FingerprintConfig,
    FingerprintEngine,
    FingerprintResult,
    SelfCheckResult,
    StabilityRecord,
    _is_uuid,
    _is_iso_timestamp,
    _is_counter_field,
    _is_timestamp_field,
    _is_session_id_like,
    _dict_depth,
    diff_fingerprints,
    fingerprint,
    get_fingerprint_engine,
    reset_fingerprint_engine,
)


# ══════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════


@pytest.fixture
def engine():
    """提供一个全新的 FingerprintEngine 实例."""
    reset_fingerprint_engine()
    return FingerprintEngine()


@pytest.fixture
def sample_agent_dict():
    """示例 Agent 配置字典 (含动态字段)."""
    return {
        "agent_id": "agent-001",
        "name": "TestAgent",
        "role": "developer",
        "state": "idle",
        "timestamp": 1715000000.0,
        "request_id": "req-abc-def-ghi-jkl",
        "session_id": "sess-xyz-123-456-789",
        "counter": 42,
        "config": {
            "temperature": 0.7,
            "max_tokens": 8192,
            "created_at": "2024-05-01T00:00:00Z",
        },
    }


@pytest.fixture
def sample_team_dict():
    """示例团队配置字典."""
    return {
        "team_id": "test-team",
        "name": "测试团队",
        "description": "自动化测试团队",
        "agents": [
            {"agent_id": "agent-1", "role": "developer", "timestamp": 1000.0},
            {"agent_id": "agent-2", "role": "researcher", "timestamp": 2000.0},
        ],
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "version": 2,
        },
    }


# ══════════════════════════════════════════════════════════════════
# 动态字段检测工具测试
# ══════════════════════════════════════════════════════════════════


class TestUUIDDetection:
    """UUID 检测."""

    def test_valid_uuid(self):
        assert _is_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_invalid_uuid_short(self):
        assert _is_uuid("550e8400-e29b-41d4") is False

    def test_invalid_uuid_no_dashes(self):
        assert _is_uuid("550e8400e29b41d4a716446655440000") is False

    def test_empty_string(self):
        assert _is_uuid("") is False


class TestISOTimestampDetection:
    """ISO 时间戳检测."""

    def test_valid_iso_timestamp(self):
        assert _is_iso_timestamp("2024-05-01T12:30:00") is True
        assert _is_iso_timestamp("2024-05-01 12:30:00") is True

    def test_date_only(self):
        """仅有日期不含时间 → 不匹配 ISO timestamp (需要时间部分)."""
        assert _is_iso_timestamp("2024-05-01") is False

    def test_invalid_timestamp(self):
        assert _is_iso_timestamp("not-a-timestamp") is False

    def test_empty_string(self):
        assert _is_iso_timestamp("") is False


class TestCounterFieldDetection:
    """计数器字段检测."""

    def test_counter_fields(self):
        assert _is_counter_field("counter") is True
        assert _is_counter_field("msg_counter") is True
        assert _is_counter_field("count_total") is True
        assert _is_counter_field("tick_count") is True
        assert _is_counter_field("sequence_number") is True
        assert _is_counter_field("seq_id") is True

    def test_non_counter_fields(self):
        assert _is_counter_field("name") is False
        assert _is_counter_field("temperature") is False
        assert _is_counter_field("description") is False


class TestTimestampFieldDetection:
    """时间戳字段名检测."""

    def test_timestamp_fields(self):
        assert _is_timestamp_field("timestamp") is True
        assert _is_timestamp_field("created_at") is True
        assert _is_timestamp_field("updated_at") is True
        assert _is_timestamp_field("last_seen") is True
        assert _is_timestamp_field("computed_at") is True
        assert _is_timestamp_field("last_modified") is True
        assert _is_timestamp_field("expires_at") is True

    def test_non_timestamp_fields(self):
        assert _is_timestamp_field("name") is False
        assert _is_timestamp_field("team_id") is False


class TestSessionIDDetection:
    """Session ID 检测."""

    def test_hex_session_id(self):
        assert _is_session_id_like("a" * 32) is True

    def test_dashed_session_id(self):
        """虚线分隔的类 session ID, 每段 >=4 字符."""
        assert _is_session_id_like("abcd-efgh-ijkl-mnop") is True

    def test_short_string(self):
        assert _is_session_id_like("short") is False

    def test_normal_id(self):
        assert _is_session_id_like("agent-001") is False


class TestDictDepth:
    """字典深度计算."""

    def test_flat_dict(self):
        assert _dict_depth({"a": 1, "b": 2}) == 1

    def test_nested_dict(self):
        assert _dict_depth({"a": {"b": {"c": 1}}}) == 3

    def test_empty_dict(self):
        assert _dict_depth({}) == 0

    def test_list_of_dicts(self):
        assert _dict_depth({"a": [{"b": 1}, {"c": 2}]}) == 2


# ══════════════════════════════════════════════════════════════════
# FingerprintConfig 测试
# ══════════════════════════════════════════════════════════════════


class TestFingerprintConfig:
    """FingerprintConfig 测试."""

    def test_default_config(self):
        cfg = FingerprintConfig()
        assert cfg.hash_algorithm == "sha256"
        assert cfg.canonical_sort_keys is True
        assert cfg.strip_uuids is True
        assert cfg.strip_timestamps is True
        assert cfg.strip_counters is True
        assert cfg.stability_window_size == 100
        assert cfg.mutation_alert_threshold == 0.05

    def test_to_dict(self):
        cfg = FingerprintConfig()
        d = cfg.to_dict()
        assert d["hash_algorithm"] == "sha256"
        assert "dynamic_field_patterns" in d

    def test_from_dict(self):
        d = {"hash_algorithm": "md5", "strip_uuids": False}
        cfg = FingerprintConfig.from_dict(d)
        assert cfg.hash_algorithm == "md5"
        assert cfg.strip_uuids is False
        # 未指定的使用默认值
        assert cfg.canonical_sort_keys is True


# ══════════════════════════════════════════════════════════════════
# FingerprintEngine 自检测试
# ══════════════════════════════════════════════════════════════════


class TestSelfCheck:
    """自检功能测试."""

    def test_self_check_passes(self, engine):
        result = engine.self_check()
        assert result.passed is True
        assert len(result.checks) >= 5
        assert len(result.issues) == 0
        assert result.duration_ms > 0

    def test_self_check_on_init(self):
        cfg = FingerprintConfig(self_check_on_init=True)
        engine = FingerprintEngine(config=cfg)
        assert engine._self_check_result is not None
        assert engine._self_check_result.passed is True

    def test_self_check_disabled(self):
        cfg = FingerprintConfig(self_check_on_init=False)
        engine = FingerprintEngine(config=cfg)
        assert engine._self_check_result is None


# ══════════════════════════════════════════════════════════════════
# 模板提取测试
# ══════════════════════════════════════════════════════════════════


class TestTemplateExtraction:
    """模板提取测试."""

    def test_strips_timestamp(self, engine):
        result = engine.fingerprint({"name": "test", "timestamp": 99999.0})
        assert "timestamp" not in result.template
        assert "timestamp" in result.dynamic_fields_removed

    def test_strips_request_id(self, engine):
        result = engine.fingerprint({"name": "test", "request_id": "req-abc-def"})
        assert "request_id" not in result.template

    def test_strips_session_id(self, engine):
        result = engine.fingerprint({"name": "test", "session_id": "sess-xyz"})
        assert "session_id" not in result.template

    def test_strips_counter(self, engine):
        result = engine.fingerprint({"name": "test", "counter": 100})
        assert "counter" not in result.template

    def test_strips_lamport_clock(self, engine):
        result = engine.fingerprint({"name": "test", "lamport_clock": 5})
        assert "lamport_clock" not in result.template

    def test_strips_nonce(self, engine):
        result = engine.fingerprint({"name": "test", "nonce": "abc123"})
        assert "nonce" not in result.template

    def test_strips_nested_dynamic_fields(self, engine, sample_agent_dict):
        result = engine.fingerprint(sample_agent_dict)
        removed = result.dynamic_fields_removed
        # timestamp, request_id, session_id, counter 应被剔除
        assert any("timestamp" in f for f in removed)
        assert any("request_id" in f for f in removed)
        assert any("session_id" in f for f in removed)
        assert any("counter" in f for f in removed)

    def test_preserves_static_fields(self, engine):
        result = engine.fingerprint({"name": "test", "role": "developer", "config": {"temperature": 0.7}})
        assert result.template == {"name": "test", "role": "developer", "config": {"temperature": 0.7}}

    def test_keeps_max_tokens_not_token(self, engine):
        """max_tokens 不应被 token 模式误匹配."""
        result = engine.fingerprint({"max_tokens": 4096, "token": "secret"})
        assert "max_tokens" in result.template
        assert "token" not in result.template  # 独立 "token" 应被剔除

    def test_keeps_tokenizer(self, engine):
        """tokenizer 不应被 token 模式误匹配."""
        result = engine.fingerprint({"tokenizer": "gpt", "token": "secret"})
        assert "tokenizer" in result.template
        assert "token" not in result.template

    def test_removes_access_token(self, engine):
        """access_token 应被剔除 (token 作为独立词段)."""
        result = engine.fingerprint({"access_token": "abc123"})
        assert "access_token" not in result.template

    def test_handles_nested_team(self, engine, sample_team_dict):
        result = engine.fingerprint(sample_team_dict)
        # 顶层字段应保留
        assert "team_id" in result.template
        assert "name" in result.template
        assert "agents" in result.template
        # 嵌套时间戳应被剔除
        removed = result.dynamic_fields_removed
        assert any("agents[0].timestamp" in f for f in removed)
        assert any("agents[1].timestamp" in f for f in removed)
        assert any("metadata.created_at" in f for f in removed)

    def test_handles_list_of_dicts(self, engine):
        data = {
            "items": [
                {"id": "a", "timestamp": 1.0},
                {"id": "b", "timestamp": 2.0},
                {"id": "c", "timestamp": 3.0},
            ]
        }
        result = engine.fingerprint(data)
        assert len(result.template["items"]) == 3
        for item in result.template["items"]:
            assert "timestamp" not in item
            assert "id" in item

    def test_handles_empty_dict(self, engine):
        result = engine.fingerprint({})
        assert result.fingerprint_hash is not None
        assert len(result.fingerprint_hash) == 64
        assert result.template == {}

    def test_handles_none_values(self, engine):
        result = engine.fingerprint({"name": "test", "optional": None})
        assert result.template["optional"] is None


# ══════════════════════════════════════════════════════════════════
# 精确哈希测试
# ══════════════════════════════════════════════════════════════════


class TestExactHashing:
    """精确哈希测试."""

    def test_hash_is_hex_string(self, engine):
        result = engine.fingerprint({"a": 1})
        assert len(result.fingerprint_hash) == 64
        assert all(c in "0123456789abcdef" for c in result.fingerprint_hash)

    def test_determinism(self, engine):
        """相同输入 → 相同哈希."""
        obj = {"name": "test", "value": 42, "items": [1, 2, 3]}
        h1 = engine.fingerprint(obj).fingerprint_hash
        h2 = engine.fingerprint(obj).fingerprint_hash
        assert h1 == h2

    def test_determinism_across_engines(self):
        """不同引擎实例, 相同配置, 相同输入 → 相同哈希."""
        cfg = FingerprintConfig()
        e1 = FingerprintEngine(config=cfg)
        e2 = FingerprintEngine(config=cfg)
        obj = {"a": 1, "b": 2}
        h1 = e1.fingerprint(obj).fingerprint_hash
        h2 = e2.fingerprint(obj).fingerprint_hash
        assert h1 == h2

    def test_different_inputs_different_hashes(self, engine):
        """不同输入 → 不同哈希."""
        h_a = engine.fingerprint({"x": 1}).fingerprint_hash
        h_b = engine.fingerprint({"x": 2}).fingerprint_hash
        assert h_a != h_b

    def test_key_order_does_not_matter(self, engine):
        """字典 key 顺序不影响哈希 (canonical sort_keys)."""
        h1 = engine.fingerprint({"a": 1, "b": 2}).fingerprint_hash
        h2 = engine.fingerprint({"b": 2, "a": 1}).fingerprint_hash
        assert h1 == h2

    def test_dynamic_stripping_gives_same_hash(self, engine):
        """仅动态字段不同 → 相同哈希."""
        base = {"name": "test", "timestamp": 1000.0, "request_id": "req-a"}
        modified = {"name": "test", "timestamp": 9999.0, "request_id": "req-b"}
        assert engine.fingerprint(base).fingerprint_hash == engine.fingerprint(modified).fingerprint_hash

    def test_hash_prefix_format(self, engine):
        result = engine.fingerprint({"test": 1})
        assert len(result.hash_prefix) == 12

    def test_md5_algorithm(self):
        cfg = FingerprintConfig(hash_algorithm="md5")
        engine = FingerprintEngine(config=cfg)
        result = engine.fingerprint({"test": 1})
        assert len(result.fingerprint_hash) == 32  # MD5 hex is 32 chars


# ══════════════════════════════════════════════════════════════════
# 指纹比对 (diff) 测试
# ══════════════════════════════════════════════════════════════════


class TestFingerprintDiff:
    """指纹比对测试."""

    def test_identical_objects(self, engine):
        fp1 = engine.fingerprint({"a": 1, "b": 2})
        fp2 = engine.fingerprint({"a": 1, "b": 2})
        diff = engine.diff(fp1, fp2)
        assert diff["identical"] is True
        assert diff["hash_match"] is True
        assert diff["only_in_first"] == []
        assert diff["only_in_second"] == []

    def test_different_objects(self, engine):
        fp1 = engine.fingerprint({"a": 1})
        fp2 = engine.fingerprint({"b": 2})
        diff = engine.diff(fp1, fp2)
        assert diff["identical"] is False
        assert diff["only_in_first"] == ["a"]
        assert diff["only_in_second"] == ["b"]

    def test_overlapping_keys(self, engine):
        fp1 = engine.fingerprint({"a": 1, "c": 3})
        fp2 = engine.fingerprint({"b": 2, "c": 3})
        diff = engine.diff(fp1, fp2)
        assert diff["common_keys"] == ["c"]

    def test_diff_convenience_function(self):
        result = diff_fingerprints({"a": 1}, {"b": 2})
        assert result["identical"] is False


# ══════════════════════════════════════════════════════════════════
# 稳定性监控测试
# ══════════════════════════════════════════════════════════════════


class TestStabilityMonitoring:
    """稳定性监控测试."""

    def test_initial_mutation_rate_zero(self, engine):
        """初始变异率为 0."""
        assert engine.mutation_rate == 0.0

    def test_initial_is_stable(self, engine):
        """初始状态为稳定."""
        assert engine.is_stable is True

    def test_mutation_rate_with_stable_input(self, engine):
        """相同输入多次 → 变异率为 0."""
        for _ in range(10):
            engine.fingerprint({"name": "stable", "timestamp": 1.0})
        assert engine.mutation_rate == 0.0
        assert engine.is_stable is True

    def test_mutation_rate_with_changes(self, engine):
        """交替不同输入 → 变异率 > 0."""
        for i in range(10):
            engine.fingerprint({"name": f"item-{i % 2}"})
        # Two alternating hashes → high mutation rate
        assert engine.mutation_rate > 0.0

    def test_stability_report(self, engine):
        engine.fingerprint({"test": 1})
        report = engine.get_stability_report()
        assert "mutation_rate" in report
        assert "is_stable" in report
        assert "total_fingerprints" in report
        assert "self_check_passed" in report
        assert report["total_fingerprints"] == 1

    def test_reset_stability(self, engine):
        engine.fingerprint({"a": 1})
        engine.fingerprint({"b": 2})
        engine.reset_stability()
        assert engine._total_fingerprints == 0
        assert engine._mutation_count == 0
        assert len(engine._stability_window) == 0
        assert engine.mutation_rate == 0.0

    def test_window_size_limit(self, engine):
        """验证窗口大小限制."""
        cfg = FingerprintConfig(stability_window_size=10)
        e = FingerprintEngine(config=cfg)
        for i in range(30):
            e.fingerprint({"n": i})
        assert len(e._stability_window) <= 20  # 2x window max

    def test_stability_report_after_self_check_failure(self):
        """自检失败时报告中包含相关信息."""
        cfg = FingerprintConfig(dynamic_field_patterns=[])  # 空模式可能导致某些检查失败
        engine = FingerprintEngine(config=cfg)
        report = engine.get_stability_report()
        assert "self_check_passed" in report


# ══════════════════════════════════════════════════════════════════
# FingerprintResult 测试
# ══════════════════════════════════════════════════════════════════


class TestFingerprintResult:
    """FingerprintResult 数据类测试."""

    def test_hash_prefix(self):
        result = FingerprintResult(
            fingerprint_hash="a" * 64,
        )
        assert result.hash_prefix == "a" * 12

    def test_to_dict(self):
        result = FingerprintResult(
            fingerprint_hash="b" * 64,
            template={"test": 1},
            input_type="test_type",
        )
        d = result.to_dict()
        assert d["fingerprint_hash"] == "b" * 64
        assert "template_summary" in d
        assert d["input_type"] == "test_type"


# ══════════════════════════════════════════════════════════════════
# 便捷函数测试
# ══════════════════════════════════════════════════════════════════


class TestConvenienceFunctions:
    """便捷函数测试."""

    def test_fingerprint_function(self):
        reset_fingerprint_engine()
        result = fingerprint({"test": 1}, "my_type")
        assert isinstance(result, FingerprintResult)
        assert result.input_type == "my_type"

    def test_get_fingerprint_engine_singleton(self):
        reset_fingerprint_engine()
        e1 = get_fingerprint_engine()
        e2 = get_fingerprint_engine()
        assert e1 is e2

    def test_get_fingerprint_engine_with_config(self):
        reset_fingerprint_engine()
        cfg = FingerprintConfig(hash_algorithm="md5")
        e = get_fingerprint_engine(cfg)
        assert e.config.hash_algorithm == "md5"

    def test_reset_engine(self):
        e1 = get_fingerprint_engine()
        reset_fingerprint_engine()
        e2 = get_fingerprint_engine()
        assert e1 is not e2

    def test_diff_fingerprints_function(self):
        reset_fingerprint_engine()
        result = diff_fingerprints({"a": 1}, {"b": 2})
        assert "identical" in result
        assert result["identical"] is False


# ══════════════════════════════════════════════════════════════════
# 集成测试: Agent/Team 配置指纹
# ══════════════════════════════════════════════════════════════════


class TestAgentFingerprintIntegration:
    """Agent 配置指纹集成测试."""

    def test_agent_profile_fingerprint(self, engine):
        """对 AgentProfile 风格的 dict 计算指纹."""
        agent = {
            "agent_id": "coding_developer",
            "name": "全栈开发",
            "role": "developer",
            "template_type": "DEVELOPER",
            "model_id": "deepseek",
            "system_prompt": "你是一个全栈开发工程师...",
            "timestamp": 1715000000.0,
            "session_id": "sess-abc-123",
        }
        result = engine.fingerprint(agent, "AgentProfile")
        assert "agent_id" in result.template
        assert "system_prompt" in result.template
        assert "timestamp" not in result.template
        assert "session_id" not in result.template
        assert result.input_type == "AgentProfile"

    def test_team_config_fingerprint(self, engine):
        """对 AgentTeam 风格的 dict 计算指纹."""
        team = {
            "team_id": "ai_coding",
            "name": "AI 编程团队",
            "visibility": "internal",
            "agents": [
                {"agent_id": "coding_pm", "role": "project_manager"},
                {"agent_id": "coding_developer", "role": "developer"},
            ],
            "created_at": "2024-05-01T00:00:00Z",
            "updated_at": "2024-05-02T00:00:00Z",
        }
        result = engine.fingerprint(team, "AgentTeam")
        assert "team_id" in result.template
        assert "agents" in result.template
        assert "created_at" not in result.template
        assert "updated_at" not in result.template

    def test_same_team_different_timestamps(self, engine):
        """仅 timestamp 不同的团队产生相同指纹."""
        team_base = {
            "team_id": "test",
            "name": "Test",
            "agents": [{"id": "a", "role": "dev"}],
            "timestamp": 1000.0,
        }
        team_modified = {
            "team_id": "test",
            "name": "Test",
            "agents": [{"id": "a", "role": "dev"}],
            "timestamp": 9999.0,
        }
        fp1 = engine.fingerprint(team_base)
        fp2 = engine.fingerprint(team_modified)
        assert fp1.fingerprint_hash == fp2.fingerprint_hash

    def test_different_teams_different_fingerprints(self, engine):
        """不同团队产生不同指纹."""
        team_a = {"team_id": "team-a", "name": "Alpha", "agents": []}
        team_b = {"team_id": "team-b", "name": "Beta", "agents": [{"id": "x"}]}
        fp_a = engine.fingerprint(team_a)
        fp_b = engine.fingerprint(team_b)
        assert fp_a.fingerprint_hash != fp_b.fingerprint_hash


# ══════════════════════════════════════════════════════════════════
# 边界/异常测试
# ══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """边界与异常测试."""

    def test_very_large_dict(self, engine):
        """大字典不应崩溃."""
        large = {"key_" + str(i): i for i in range(1000)}
        result = engine.fingerprint(large)
        assert len(result.fingerprint_hash) == 64

    def test_deeply_nested(self, engine):
        """深层嵌套不应崩溃."""
        obj = {}
        cur = obj
        for i in range(20):
            cur["child"] = {}
            cur = cur["child"]
        cur["value"] = 42
        result = engine.fingerprint(obj)
        assert len(result.fingerprint_hash) == 64

    def test_non_json_values(self, engine):
        """非 JSON 值 (如 bytes) 应优雅处理."""
        obj = {"name": "test", "blob": b"binary data"}
        result = engine.fingerprint(obj)
        assert len(result.fingerprint_hash) == 64

    def test_custom_object_with_dict(self, engine):
        """带 __dict__ 的对象."""

        class CustomObj:
            def __init__(self):
                self.name = "custom"
                self.value = 42
                self.timestamp = 1000.0

        result = engine.fingerprint(CustomObj())
        assert "name" in result.template
        assert "value" in result.template
        assert "timestamp" not in result.template

    def test_custom_object_with_to_dict(self, engine):
        """带 to_dict() 的对象."""

        class CustomObj:
            def to_dict(self):
                return {"name": "custom", "timestamp": 2000.0}

        result = engine.fingerprint(CustomObj())
        assert result.template == {"name": "custom"}
