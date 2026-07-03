# -*- coding: utf-8 -*-
"""操作事件 & 情境切片存储 单元测试.

测试覆盖:
  - OperationEvent 创建和完整性验证
  - ContextSlice 创建和完整性验证
  - OperationStore append / query / trace / chain
  - 幂等去重
  - 完整性验证
  - 统计
  - OperationTrace 聚合
  - Query 过滤器匹配
  - 不可变性 (frozen dataclass)
  - JSON 序列化往返
"""

from __future__ import annotations

import asyncio
import json
import pytest
import tempfile
from pathlib import Path

from agents.operation_models import (
    OperationEvent,
    OperationType,
    OperationQuery,
    OperationTrace,
    ContextQuery,
    ContextSlice,
    ContextType,
)
from agents.operation_store import (
    OperationStore,
    get_operation_store,
    reset_operation_store,
)


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def store():
    """创建独立的临时存储实例."""
    reset_operation_store()
    with tempfile.TemporaryDirectory() as tmpdir:
        s = OperationStore(base_dir=tmpdir)
        yield s


@pytest.fixture
def sample_event():
    """创建示例操作事件."""
    return OperationEvent.create(
        operation_type=OperationType.TOOL_CALL,
        agent_id="agent-001",
        team_id="build-team",
        summary="Read file src/main.py",
        detail={"tool": "read_file", "path": "src/main.py"},
        session_id="sess-001",
        task_id="task-001",
    )


@pytest.fixture
def sample_slice(sample_event):
    """创建示例情境切片."""
    return ContextSlice.create(
        operation_id=sample_event.operation_id,
        context_type=ContextType.SESSION_STATE,
        payload={"messages": 3, "tokens_used": 500},
        summary="Session state before tool call",
        entity_id="agent-001",
        entity_type="agent",
    )


# ═══════════════════════════════════════════════════════════════
# OperationEvent 测试
# ═══════════════════════════════════════════════════════════════


class TestOperationEvent:
    """OperationEvent 数据模型测试."""

    def test_create_event(self, sample_event):
        """创建操作事件."""
        assert sample_event.operation_id.startswith("OP-")
        assert sample_event.operation_type == OperationType.TOOL_CALL
        assert sample_event.agent_id == "agent-001"
        assert sample_event.team_id == "build-team"
        assert sample_event.summary == "Read file src/main.py"
        assert sample_event.detail["tool"] == "read_file"
        assert sample_event.session_id == "sess-001"
        assert sample_event.task_id == "task-001"

    def test_hash_generated(self, sample_event):
        """自动生成操作哈希."""
        assert len(sample_event.operation_hash) == 16
        assert sample_event.operation_hash == sample_event._compute_hash()

    def test_integrity_ok(self, sample_event):
        """完整性验证通过."""
        assert sample_event.verify_integrity() is True

    def test_integrity_tampered(self, sample_event):
        """篡改后完整性验证失败."""
        # frozen 无法直接修改，但从字典重建一个篡改版本
        d = sample_event.to_dict()
        d["summary"] = "TAMPERED SUMMARY"
        # 不重新计算 hash，直接传给 from_dict（from_dict 会保留已有 hash）
        tampered = OperationEvent.from_dict(d)
        # hash 是基于旧内容计算的，内容已变 → 验证失败
        assert tampered.verify_integrity() is False

    def test_frozen_immutable(self, sample_event):
        """Frozen dataclass 不可修改."""
        with pytest.raises(Exception):
            sample_event.summary = "modified"  # type: ignore

    def test_to_dict_roundtrip(self, sample_event):
        """序列化往返."""
        d = sample_event.to_dict()
        restored = OperationEvent.from_dict(d)
        assert restored.operation_id == sample_event.operation_id
        assert restored.operation_type == sample_event.operation_type
        assert restored.operation_hash == sample_event.operation_hash
        assert restored.verify_integrity() is True

    def test_json_roundtrip(self, sample_event):
        """JSON 序列化往返."""
        d = sample_event.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        restored = OperationEvent.from_dict(parsed)
        assert restored.operation_id == sample_event.operation_id
        assert restored.verify_integrity() is True

    def test_parent_operation_id(self):
        """父操作 ID."""
        parent = OperationEvent.create(
            operation_type=OperationType.TASK_STARTED,
            agent_id="agent-001",
            team_id="build-team",
            summary="Parent task",
        )
        child = OperationEvent.create(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
            summary="Child tool call",
            parent_operation_id=parent.operation_id,
        )
        assert child.parent_operation_id == parent.operation_id

    def test_idempotency_key(self):
        """幂等键."""
        evt = OperationEvent.create(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
            summary="Test",
            idempotency_key="key-12345",
        )
        assert evt.idempotency_key == "key-12345"

    def test_all_operation_types(self):
        """所有操作类型都能创建."""
        for op_type in OperationType:
            evt = OperationEvent.create(
                operation_type=op_type,
                agent_id="agent-001",
                team_id="test",
                summary=f"Test {op_type.value}",
            )
            assert evt.operation_type == op_type
            assert evt.verify_integrity() is True

    def test_unknown_type_fallback(self):
        """未知类型回退为 UNKNOWN."""
        data = {
            "operation_id": "OP-test",
            "operation_type": "some_future_type",
            "agent_id": "agent-001",
            "team_id": "test",
            "timestamp": "2026-01-01T00:00:00Z",
            "summary": "test",
            "detail": {},
            "operation_hash": "",
            "schema_version": 1,
        }
        evt = OperationEvent.from_dict(data)
        assert evt.operation_type == OperationType.UNKNOWN


# ═══════════════════════════════════════════════════════════════
# ContextSlice 测试
# ═══════════════════════════════════════════════════════════════


class TestContextSlice:
    """ContextSlice 数据模型测试."""

    def test_create_slice(self, sample_slice, sample_event):
        """创建情境切片."""
        assert sample_slice.slice_id.startswith("CS-")
        assert sample_slice.operation_id == sample_event.operation_id
        assert sample_slice.context_type == ContextType.SESSION_STATE
        assert sample_slice.payload["messages"] == 3
        assert sample_slice.entity_id == "agent-001"

    def test_hash_generated(self, sample_slice):
        """自动生成切片哈希."""
        assert len(sample_slice.context_hash) == 16

    def test_integrity_ok(self, sample_slice):
        """完整性验证通过."""
        assert sample_slice.verify_integrity() is True

    def test_integrity_tampered(self, sample_slice):
        """篡改后验证失败."""
        d = sample_slice.to_dict()
        d["payload"] = {"tampered": True}
        tampered = ContextSlice.from_dict(d)
        assert tampered.verify_integrity() is False

    def test_frozen_immutable(self, sample_slice):
        """Frozen 不可变."""
        with pytest.raises(Exception):
            sample_slice.payload = {}  # type: ignore

    def test_to_dict_roundtrip(self, sample_slice):
        """序列化往返."""
        d = sample_slice.to_dict()
        restored = ContextSlice.from_dict(d)
        assert restored.slice_id == sample_slice.slice_id
        assert restored.context_hash == sample_slice.context_hash
        assert restored.verify_integrity() is True

    def test_all_context_types(self, sample_event):
        """所有情境类型都能创建."""
        for ctx_type in ContextType:
            cs = ContextSlice.create(
                operation_id=sample_event.operation_id,
                context_type=ctx_type,
                payload={"test": True},
                summary=f"Test {ctx_type.value}",
            )
            assert cs.context_type == ctx_type
            assert cs.verify_integrity() is True

    def test_unknown_context_type_fallback(self):
        """未知情境类型回退为 CUSTOM."""
        data = {
            "slice_id": "CS-test",
            "operation_id": "OP-test",
            "context_type": "future_type",
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {},
            "summary": "",
            "context_hash": "",
            "schema_version": 1,
        }
        cs = ContextSlice.from_dict(data)
        assert cs.context_type == ContextType.CUSTOM


# ═══════════════════════════════════════════════════════════════
# OperationTrace 测试
# ═══════════════════════════════════════════════════════════════


class TestOperationTrace:
    """OperationTrace 聚合视图测试."""

    def test_trace_integrity(self, sample_event, sample_slice):
        """追溯完整性."""
        trace = OperationTrace(
            operation=sample_event,
            context_slices=[sample_slice],
        )
        assert trace.is_integrity_ok is True

    def test_trace_integrity_corrupt_op(self, sample_event, sample_slice):
        """操作被篡改时追溯不完整."""
        d = sample_event.to_dict()
        d["summary"] = "TAMPERED"
        corrupt_op = OperationEvent.from_dict(d)
        trace = OperationTrace(operation=corrupt_op, context_slices=[sample_slice])
        assert trace.is_integrity_ok is False

    def test_trace_integrity_corrupt_slice(self, sample_event, sample_slice):
        """切片被篡改时追溯不完整."""
        d = sample_slice.to_dict()
        d["payload"] = {"tampered": True}
        corrupt_slice = ContextSlice.from_dict(d)
        trace = OperationTrace(operation=sample_event, context_slices=[corrupt_slice])
        assert trace.is_integrity_ok is False

    def test_trace_to_dict(self, sample_event, sample_slice):
        """追溯序列化."""
        trace = OperationTrace(operation=sample_event, context_slices=[sample_slice])
        d = trace.to_dict()
        assert "operation" in d
        assert "context_slices" in d
        assert "integrity_ok" in d
        assert len(d["context_slices"]) == 1
        assert d["integrity_ok"] is True


# ═══════════════════════════════════════════════════════════════
# OperationQuery 测试
# ═══════════════════════════════════════════════════════════════


class TestOperationQuery:
    """OperationQuery 过滤器测试."""

    def test_match_by_type(self, sample_event):
        """按类型过滤."""
        q = OperationQuery(operation_type=OperationType.TOOL_CALL)
        assert q.matches(sample_event) is True

        q2 = OperationQuery(operation_type=OperationType.TASK_STARTED)
        assert q2.matches(sample_event) is False

    def test_match_by_agent(self, sample_event):
        """按 Agent 过滤."""
        q = OperationQuery(agent_id="agent-001")
        assert q.matches(sample_event) is True

        q2 = OperationQuery(agent_id="agent-999")
        assert q2.matches(sample_event) is False

    def test_match_by_team(self, sample_event):
        """按团队过滤."""
        q = OperationQuery(team_id="build-team")
        assert q.matches(sample_event) is True

        q2 = OperationQuery(team_id="other-team")
        assert q2.matches(sample_event) is False

    def test_match_by_session(self, sample_event):
        """按会话过滤."""
        q = OperationQuery(session_id="sess-001")
        assert q.matches(sample_event) is True

        q2 = OperationQuery(session_id="sess-999")
        assert q2.matches(sample_event) is False

    def test_match_by_time_range(self, sample_event):
        """按时间范围过滤."""
        # sample_event 在当前时间附近
        q_future = OperationQuery(start_time="2099-01-01T00:00:00Z")
        assert q_future.matches(sample_event) is False

        q_past = OperationQuery(end_time="2020-01-01T00:00:00Z")
        assert q_past.matches(sample_event) is False

        q_wide = OperationQuery(
            start_time="2020-01-01T00:00:00Z",
            end_time="2099-01-01T00:00:00Z",
        )
        assert q_wide.matches(sample_event) is True

    def test_match_combined(self, sample_event):
        """组合过滤."""
        q = OperationQuery(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
        )
        assert q.matches(sample_event) is True

        q2 = OperationQuery(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-999",
        )
        assert q2.matches(sample_event) is False


# ═══════════════════════════════════════════════════════════════
# ContextQuery 测试
# ═══════════════════════════════════════════════════════════════


class TestContextQuery:
    """ContextQuery 过滤器测试."""

    def test_match_by_operation_id(self, sample_slice, sample_event):
        """按操作 ID 过滤."""
        q = ContextQuery(operation_id=sample_event.operation_id)
        assert q.matches(sample_slice) is True

        q2 = ContextQuery(operation_id="OP-nonexistent")
        assert q2.matches(sample_slice) is False

    def test_match_by_context_type(self, sample_slice):
        """按情境类型过滤."""
        q = ContextQuery(context_type=ContextType.SESSION_STATE)
        assert q.matches(sample_slice) is True

        q2 = ContextQuery(context_type=ContextType.ENVIRONMENT)
        assert q2.matches(sample_slice) is False

    def test_match_by_entity(self, sample_slice):
        """按实体过滤."""
        q = ContextQuery(entity_id="agent-001", entity_type="agent")
        assert q.matches(sample_slice) is True

        q2 = ContextQuery(entity_id="agent-999")
        assert q2.matches(sample_slice) is False


# ═══════════════════════════════════════════════════════════════
# OperationStore 测试
# ═══════════════════════════════════════════════════════════════


class TestOperationStoreAppend:
    """OperationStore 写入测试."""

    @pytest.mark.asyncio
    async def test_append_operation(self, store, sample_event):
        """追加操作事件."""
        ok = await store.append_operation(sample_event)
        assert ok is True

    @pytest.mark.asyncio
    async def test_append_slice(self, store, sample_slice):
        """追加情境切片."""
        # 需要先有对应的操作
        event = OperationEvent.create(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
            summary="Test",
            operation_id=sample_slice.operation_id  # reuse same id
        )
        await store.append_operation(event)
        ok = await store.append_slice(sample_slice)
        assert ok is True

    @pytest.mark.asyncio
    async def test_record_with_context(self, store):
        """原子写入操作+切片."""
        event = OperationEvent.create(
            operation_type=OperationType.TASK_STARTED,
            agent_id="agent-001",
            team_id="build-team",
            summary="Task with context",
        )
        slices = [
            ContextSlice.create(event.operation_id, ContextType.AGENT_CONFIG, {"role": "dev"}),
            ContextSlice.create(event.operation_id, ContextType.ENVIRONMENT, {"python": "3.11"}),
        ]
        ok = await store.record_operation_with_context(event, slices)
        assert ok is True

        # 验证
        trace = await store.get_trace(event.operation_id)
        assert trace is not None
        assert len(trace.context_slices) == 2

    @pytest.mark.asyncio
    async def test_idempotent_duplicate(self, store):
        """幂等去重."""
        event = OperationEvent.create(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
            summary="First write",
            idempotency_key="idem-key-001",
        )
        ok1 = await store.append_operation(event)
        assert ok1 is True

        # 第二次写入相同幂等键
        event2 = OperationEvent.create(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
            summary="Duplicate write",
            idempotency_key="idem-key-001",
        )
        ok2 = await store.append_operation(event2)
        assert ok2 is False  # 幂等跳过

    @pytest.mark.asyncio
    async def test_record_with_context_idempotent(self, store):
        """原子写入幂等."""
        event = OperationEvent.create(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
            summary="First",
            idempotency_key="atomic-idem-001",
        )
        ok1 = await store.record_operation_with_context(event, [])
        assert ok1 is True

        event2 = OperationEvent.create(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
            summary="Second",
            idempotency_key="atomic-idem-001",
        )
        ok2 = await store.record_operation_with_context(event2, [])
        assert ok2 is False


class TestOperationStoreQuery:
    """OperationStore 查询测试."""

    @pytest.mark.asyncio
    async def test_get_operation(self, store, sample_event):
        """按 ID 获取."""
        await store.append_operation(sample_event)
        found = await store.get_operation(sample_event.operation_id)
        assert found is not None
        assert found.operation_id == sample_event.operation_id
        assert found.verify_integrity() is True

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        """获取不存在."""
        found = await store.get_operation("OP-nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_slice(self, store, sample_event, sample_slice):
        """按 ID 获取切片."""
        await store.append_operation(sample_event)
        await store.append_slice(sample_slice)
        found = await store.get_slice(sample_slice.slice_id)
        assert found is not None
        assert found.slice_id == sample_slice.slice_id

    @pytest.mark.asyncio
    async def test_query_by_type(self, store):
        """按类型查询."""
        events = [
            OperationEvent.create(OperationType.TOOL_CALL, agent_id="a1", team_id="t1", summary="tc1"),
            OperationEvent.create(OperationType.TOOL_CALL, agent_id="a1", team_id="t1", summary="tc2"),
            OperationEvent.create(OperationType.TASK_STARTED, agent_id="a1", team_id="t1", summary="ts1"),
        ]
        for e in events:
            await store.append_operation(e)

        q = OperationQuery(operation_type=OperationType.TOOL_CALL)
        results = await store.query_operations(q)
        assert len(results) == 2
        assert all(r.operation_type == OperationType.TOOL_CALL for r in results)

    @pytest.mark.asyncio
    async def test_query_by_agent(self, store):
        """按 Agent 查询."""
        for i in range(3):
            evt = OperationEvent.create(OperationType.TOOL_CALL, agent_id=f"agent-{i}", team_id="t1", summary=f"evt{i}")
            await store.append_operation(evt)

        q = OperationQuery(agent_id="agent-1")
        results = await store.query_operations(q)
        assert len(results) == 1
        assert results[0].agent_id == "agent-1"

    @pytest.mark.asyncio
    async def test_query_limit_offset(self, store):
        """分页查询."""
        for i in range(10):
            evt = OperationEvent.create(OperationType.TOOL_CALL, agent_id="a1", team_id="t1", summary=f"evt{i}")
            await store.append_operation(evt)

        q = OperationQuery(limit=3)
        results = await store.query_operations(q)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_query_slices_for_operation(self, store, sample_event):
        """查询某操作的所有切片."""
        await store.append_operation(sample_event)
        slices = [
            ContextSlice.create(sample_event.operation_id, ContextType.SESSION_STATE, {"msg": 1}),
            ContextSlice.create(sample_event.operation_id, ContextType.AGENT_CONFIG, {"role": "dev"}),
        ]
        for cs in slices:
            await store.append_slice(cs)

        found = await store.get_slices_for_operation(sample_event.operation_id)
        assert len(found) == 2

    @pytest.mark.asyncio
    async def test_get_trace(self, store, sample_event):
        """获取追溯."""
        await store.append_operation(sample_event)
        cs = ContextSlice.create(sample_event.operation_id, ContextType.SESSION_STATE, {"msg": 1})
        await store.append_slice(cs)

        trace = await store.get_trace(sample_event.operation_id)
        assert trace is not None
        assert trace.operation.operation_id == sample_event.operation_id
        assert len(trace.context_slices) == 1
        assert trace.is_integrity_ok is True

    @pytest.mark.asyncio
    async def test_get_trace_nonexistent(self, store):
        """获取不存在操作的追溯."""
        trace = await store.get_trace("OP-nonexistent")
        assert trace is None

    @pytest.mark.asyncio
    async def test_query_traces(self, store):
        """查询追溯列表."""
        for i in range(3):
            evt = OperationEvent.create(OperationType.TOOL_CALL, agent_id="a1", team_id="t1", summary=f"evt{i}")
            await store.append_operation(evt)
            cs = ContextSlice.create(evt.operation_id, ContextType.SESSION_STATE, {"idx": i})
            await store.append_slice(cs)

        q = OperationQuery(agent_id="a1")
        traces = await store.query_traces(q)
        assert len(traces) == 3
        for t in traces:
            assert t.is_integrity_ok is True
            assert len(t.context_slices) == 1

    @pytest.mark.asyncio
    async def test_causal_chain(self, store):
        """因果链追溯."""
        root = OperationEvent.create(OperationType.TASK_STARTED, agent_id="a1", team_id="t1", summary="root")
        await store.append_operation(root)

        child = OperationEvent.create(
            OperationType.TOOL_CALL, agent_id="a1", team_id="t1",
            summary="child", parent_operation_id=root.operation_id
        )
        await store.append_operation(child)

        grandchild = OperationEvent.create(
            OperationType.TOOL_CALL, agent_id="a1", team_id="t1",
            summary="grandchild", parent_operation_id=child.operation_id
        )
        await store.append_operation(grandchild)

        chain = await store.get_causal_chain(grandchild.operation_id)
        assert len(chain) == 3
        # 顺序: grandchild → child → root
        assert chain[0].operation_id == grandchild.operation_id
        assert chain[1].operation_id == child.operation_id
        assert chain[2].operation_id == root.operation_id

    @pytest.mark.asyncio
    async def test_causal_chain_max_depth(self, store):
        """因果链最大深度限制."""
        prev_id = None
        created_ids = []
        for i in range(30):
            evt = OperationEvent.create(
                OperationType.TOOL_CALL, agent_id="a1", team_id="t1",
                summary=f"step-{i}", parent_operation_id=prev_id
            )
            await store.append_operation(evt)
            created_ids.append(evt.operation_id)
            prev_id = evt.operation_id

        chain = await store.get_causal_chain(created_ids[-1], max_depth=5)
        assert len(chain) == 5


class TestOperationStoreStats:
    """OperationStore 统计测试."""

    @pytest.mark.asyncio
    async def test_get_stats(self, store):
        """获取统计."""
        for i in range(5):
            evt = OperationEvent.create(
                OperationType.TOOL_CALL if i % 2 == 0 else OperationType.TASK_STARTED,
                agent_id=f"agent-{i % 3}",
                team_id="t1",
                summary=f"evt{i}",
            )
            await store.append_operation(evt)
            cs = ContextSlice.create(evt.operation_id, ContextType.SESSION_STATE, {"idx": i})
            await store.append_slice(cs)

        stats = await store.get_stats()
        assert stats["total_operations"] == 5
        assert stats["total_slices"] == 5
        assert "tool_call" in stats["by_type"]
        assert "task_started" in stats["by_type"]
        assert stats["oldest_timestamp"] is not None
        assert stats["newest_timestamp"] is not None

    @pytest.mark.asyncio
    async def test_stats_empty(self, store):
        """空存储统计."""
        stats = await store.get_stats()
        assert stats["total_operations"] == 0
        assert stats["total_slices"] == 0


class TestOperationStoreVerify:
    """OperationStore 完整性验证测试."""

    @pytest.mark.asyncio
    async def test_verify_all_clean(self, store):
        """全部完整."""
        evt = OperationEvent.create(OperationType.TOOL_CALL, agent_id="a1", team_id="t1", summary="test")
        await store.append_operation(evt)
        cs = ContextSlice.create(evt.operation_id, ContextType.SESSION_STATE, {"msg": 1})
        await store.append_slice(cs)

        v = await store.verify_all()
        assert v["total_ops"] == 1
        assert v["corrupt_ops"] == 0
        assert v["total_slices"] == 1
        assert v["corrupt_slices"] == 0

    @pytest.mark.asyncio
    async def test_verify_empty(self, store):
        """空存储验证."""
        v = await store.verify_all()
        assert v["total_ops"] == 0
        assert v["corrupt_ops"] == 0


# ═══════════════════════════════════════════════════════════════
# 全局单例测试
# ═══════════════════════════════════════════════════════════════


class TestGlobalSingleton:
    """全局单例测试."""

    def test_get_operation_store(self):
        """获取全局单例."""
        reset_operation_store()
        s1 = get_operation_store()
        s2 = get_operation_store()
        assert s1 is s2

    def test_reset_operation_store(self):
        """重置全局单例."""
        s1 = get_operation_store()
        reset_operation_store()
        s2 = get_operation_store()
        assert s1 is not s2


# ═══════════════════════════════════════════════════════════════
# 不变性保证测试
# ═══════════════════════════════════════════════════════════════


class TestImmutabilityGuarantees:
    """不可变性保证测试."""

    def test_operation_event_no_update_methods(self):
        """OperationEvent 没有 update/delete 方法."""
        evt = OperationEvent.create(
            operation_type=OperationType.TOOL_CALL,
            agent_id="agent-001",
            team_id="build-team",
            summary="Test",
        )
        # frozen dataclass → __setattr__ 会 raise
        with pytest.raises(Exception):
            evt.summary = "new summary"

        # 没有 update / delete 方法
        assert not hasattr(evt, "update")
        assert not hasattr(evt, "delete")

    def test_context_slice_no_update_methods(self):
        """ContextSlice 没有 update/delete 方法."""
        cs = ContextSlice.create(
            operation_id="OP-test",
            context_type=ContextType.SESSION_STATE,
            payload={"test": True},
        )
        with pytest.raises(Exception):
            cs.payload = {"new": True}

        assert not hasattr(cs, "update")
        assert not hasattr(cs, "delete")

    def test_store_only_appends(self, store):
        """Store 只有 append 方法，没有 update/delete."""
        assert hasattr(store, "append_operation")
        assert hasattr(store, "append_slice")
        assert not hasattr(store, "update_operation")
        assert not hasattr(store, "delete_operation")
        assert not hasattr(store, "update_slice")
        assert not hasattr(store, "delete_slice")


# ═══════════════════════════════════════════════════════════════
# 追溯完整性测试
# ═══════════════════════════════════════════════════════════════


class TestTraceability:
    """情境切片可追溯性测试."""

    @pytest.mark.asyncio
    async def test_slice_always_linked_to_operation(self, store):
        """每个切片都关联到某个操作."""
        evt = OperationEvent.create(OperationType.TOOL_CALL, agent_id="a1", team_id="t1", summary="test")
        await store.append_operation(evt)

        cs1 = ContextSlice.create(evt.operation_id, ContextType.SESSION_STATE, {"msg": 1})
        cs2 = ContextSlice.create(evt.operation_id, ContextType.ENVIRONMENT, {"env": "prod"})
        await store.append_slice(cs1)
        await store.append_slice(cs2)

        # 通过 operation_id 能查到所有切片
        slices = await store.get_slices_for_operation(evt.operation_id)
        assert len(slices) == 2
        for s in slices:
            assert s.operation_id == evt.operation_id

    @pytest.mark.asyncio
    async def test_cross_reference(self, store):
        """操作和切片双向可查."""
        evt = OperationEvent.create(OperationType.TOOL_CALL, agent_id="a1", team_id="t1", summary="test")
        await store.append_operation(evt)

        cs = ContextSlice.create(evt.operation_id, ContextType.SESSION_STATE, {"msg": 1})
        await store.append_slice(cs)

        # 操作 → 切片
        trace = await store.get_trace(evt.operation_id)
        assert len(trace.context_slices) == 1
        assert trace.context_slices[0].slice_id == cs.slice_id

        # 切片 → 操作
        found_cs = await store.get_slice(cs.slice_id)
        assert found_cs is not None
        found_op = await store.get_operation(found_cs.operation_id)
        assert found_op is not None
        assert found_op.operation_id == evt.operation_id

    @pytest.mark.asyncio
    async def test_multi_type_context(self, store):
        """一个操作关联多种类型的情境切片."""
        evt = OperationEvent.create(OperationType.TASK_STARTED, agent_id="a1", team_id="t1",
                                     summary="Multi-context operation")
        await store.append_operation(evt)

        types = [
            ContextType.SESSION_STATE,
            ContextType.AGENT_CONFIG,
            ContextType.TEAM_CONFIG,
            ContextType.ENVIRONMENT,
            ContextType.USER_REQUEST,
        ]
        for t in types:
            cs = ContextSlice.create(evt.operation_id, t, {"type": t.value})
            await store.append_slice(cs)

        trace = await store.get_trace(evt.operation_id)
        assert len(trace.context_slices) == len(types)
        actual_types = {s.context_type for s in trace.context_slices}
        assert actual_types == set(types)
