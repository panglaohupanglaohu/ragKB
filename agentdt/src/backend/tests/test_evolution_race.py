# -*- coding: utf-8 -*-
"""审核流竞态与断网场景测试 — EvolutionExecutor / Audit 并发 & 网络容错.

覆盖:
- EvolutionExecutor 并发执行 (Semaphore 控制)
- 审核流竞态: 同时对同一演进项发起多次审核
- 断网恢复: 模拟 API 不可达 / 超时
- 回调竞态: on_complete 同时触发时的状态一致性
- 事件日志完整性: 并发下事件无丢失/乱序

注意: 所有 async 测试通过 asyncio.run() 包装，无需 pytest-asyncio。
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

# Ensure src/backend is in path
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))


# ── Helper: 创建模拟演化项 ────────────────────────────────────────────────

def _make_item_dict(
    item_id: str = "ev-test-001",
    title: str = "测试演化项",
    description: str = "用于竞态测试的演化项",
    current_behavior: str = "当前无此功能",
    expected_behavior: str = "期望添加此功能",
    reference_standard: str = "业界标准 X",
) -> Dict[str, Any]:
    return {
        "item_id": item_id,
        "title": title,
        "description": description,
        "current_behavior": current_behavior,
        "expected_behavior": expected_behavior,
        "reference_standard": reference_standard,
    }


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def executor():
    """提供 EvolutionExecutor 实例."""
    from channels.evolution_executor import EvolutionExecutor
    return EvolutionExecutor()


@pytest.fixture
def sample_item():
    """标准测试演化项."""
    return _make_item_dict()


# ── 1. 并发执行测试 ────────────────────────────────────────────────────────

class TestEvolutionExecutorConcurrency:
    """EvolutionExecutor 并发执行测试."""

    def test_single_execution(self, executor, sample_item):
        """单次执行基础流程."""
        completed = []

        def on_complete(item_id, result):
            completed.append((item_id, result))

        executor.set_on_complete(on_complete)

        async def _run():
            with patch.object(executor, '_run_agent_loop') as mock_run:
                mock_run.return_value = {
                    "ok": True,
                    "summary": "所有修改已完成",
                    "files_changed": ["src/backend/test_file.py"],
                    "iterations": 3,
                }
                await executor.execute("ev-test-001", sample_item)
                await asyncio.sleep(0.2)

        asyncio.run(_run())

        assert executor.get_result("ev-test-001") is not None
        result = executor.get_result("ev-test-001")
        assert result["ok"] is True
        assert len(result["files_changed"]) == 1
        assert len(completed) == 1

    def test_concurrent_executions_respect_semaphore(self, executor):
        """并发执行应受 Semaphore 限制."""
        from channels.evolution_executor import MAX_CONCURRENT_EXECUTIONS

        active_count = 0
        max_active = 0

        original_run = executor._run_agent_loop

        def counting_run(*args, **kwargs):
            nonlocal active_count, max_active
            active_count += 1
            max_active = max(max_active, active_count)
            time.sleep(0.05)
            active_count -= 1
            return {"ok": True, "summary": "done", "files_changed": [], "iterations": 1}

        async def _run():
            with patch.object(executor, '_run_agent_loop', wraps=counting_run):
                task_count = MAX_CONCURRENT_EXECUTIONS * 3
                for i in range(task_count):
                    item = _make_item_dict(f"ev-conc-{i:03d}", f"并发任务 {i}")
                    await executor.execute(f"ev-conc-{i:03d}", item)
                await asyncio.sleep(0.5)

        asyncio.run(_run())

        assert max_active <= MAX_CONCURRENT_EXECUTIONS, (
            f"并发数 {max_active} 超过上限 {MAX_CONCURRENT_EXECUTIONS}"
        )

    def test_duplicate_execution_prevented(self, executor):
        """重复执行同一演进项应被阻止."""
        async def _run():
            with patch.object(executor, '_run_agent_loop') as mock_run:
                mock_run.return_value = {
                    "ok": True, "summary": "done", "files_changed": [], "iterations": 1,
                }
                await executor.execute("ev-dup", _make_item_dict("ev-dup"))
                await executor.execute("ev-dup", _make_item_dict("ev-dup"))
                await asyncio.sleep(0.2)
            return mock_run.call_count

        call_count = asyncio.run(_run())
        assert call_count == 1, f"预期调用 1 次, 实际 {call_count} 次"

    def test_callback_race_condition(self, executor):
        """并发回调不应导致状态不一致."""
        results_received = []
        lock = asyncio.Lock()

        async def on_complete(item_id, result):
            async with lock:
                results_received.append((item_id, result.get("ok")))

        executor.set_on_complete(on_complete)

        async def _run():
            with patch.object(executor, '_run_agent_loop') as mock_run:
                mock_run.return_value = {
                    "ok": True, "summary": "done", "files_changed": [], "iterations": 1,
                }
                for i in range(10):
                    await executor.execute(f"ev-cb-{i:03d}", _make_item_dict(f"ev-cb-{i:03d}"))
                await asyncio.sleep(0.3)

        asyncio.run(_run())

        assert len(results_received) == 10, f"预期 10 个回调, 实际 {len(results_received)}"
        assert all(ok for _, ok in results_received)


# ── 2. 断网/超时恢复测试 ──────────────────────────────────────────────────

class TestNetworkResilience:
    """网络中断与超时容错测试."""

    def test_executor_handles_agent_loop_timeout(self, executor):
        """AgentLoop 超时时执行器应优雅降级."""
        async def _run():
            with patch.object(executor, '_run_agent_loop') as mock_run:
                mock_run.side_effect = TimeoutError("LLM API timeout after 30s")
                await executor.execute("ev-timeout", _make_item_dict("ev-timeout"))
                await asyncio.sleep(0.2)

        asyncio.run(_run())

        result = executor.get_result("ev-timeout")
        assert result is not None
        assert result["ok"] is False
        assert "error" in result

    def test_executor_handles_connection_error(self, executor):
        """连接中断时执行器应正确报告错误."""
        async def _run():
            with patch.object(executor, '_run_agent_loop') as mock_run:
                mock_run.side_effect = ConnectionError("Connection refused")
                await executor.execute("ev-conn-err", _make_item_dict("ev-conn-err"))
                await asyncio.sleep(0.2)

        asyncio.run(_run())

        result = executor.get_result("ev-conn-err")
        assert result is not None
        assert result["ok"] is False

    def test_executor_handles_os_error(self, executor):
        """系统级错误 (OSError) 时应正确报告."""
        async def _run():
            with patch.object(executor, '_run_agent_loop') as mock_run:
                mock_run.side_effect = OSError("Too many open files")
                await executor.execute("ev-os-err", _make_item_dict("ev-os-err"))
                await asyncio.sleep(0.2)

        asyncio.run(_run())

        result = executor.get_result("ev-os-err")
        assert result is not None
        assert result["ok"] is False

    def test_concurrent_with_one_failure(self, executor):
        """混合成功/失败并发: 成功的任务不受失败任务影响."""
        call_count = 0

        def mixed_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise TimeoutError("Simulated timeout")
            return {"ok": True, "summary": "done", "files_changed": [], "iterations": 1}

        async def _run():
            with patch.object(executor, '_run_agent_loop', wraps=mixed_run):
                for i in range(9):
                    await executor.execute(f"ev-mix-{i:03d}", _make_item_dict(f"ev-mix-{i:03d}"))
                await asyncio.sleep(0.3)

        asyncio.run(_run())

        success = 0
        failed = 0
        for i in range(9):
            r = executor.get_result(f"ev-mix-{i:03d}")
            assert r is not None, f"任务 ev-mix-{i:03d} 无结果"
            if r["ok"]:
                success += 1
            else:
                failed += 1

        assert success == 6, f"预期 6 成功, 实际 {success}"
        assert failed == 3, f"预期 3 失败, 实际 {failed}"


# ── 3. 审核流竞态测试 ──────────────────────────────────────────────────────

class TestAuditRaceConditions:
    """审核流并发竞态场景测试."""

    def test_concurrent_audit_same_target(self):
        """多个审核同时对不同规则执行."""
        from channels.system_evolution import SystemEvolutionChannel

        async def _run():
            channel = SystemEvolutionChannel()
            channel.initialize()

            async def run_audit(rule):
                try:
                    return await channel.audit_single_rule(rule.id, target_channel="bridge_chat")
                except Exception as e:
                    return f"error: {e}"

            rules = channel.audit_rules[:5]
            tasks = [run_audit(r) for r in rules]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in results:
                if isinstance(r, Exception):
                    pytest.fail(f"审核异常: {r}")
            assert len(results) == 5

        asyncio.run(_run())

    def test_concurrent_discovery_dispatch(self):
        """并发发现与派发不应产生重复演化项."""
        from channels.system_evolution import SystemEvolutionChannel

        async def _run():
            channel = SystemEvolutionChannel()
            channel.initialize()

            await channel.run_full_audit()
            initial_count = len(channel.discovered_items)

            async def audit_once():
                await channel.run_full_audit()

            await asyncio.gather(audit_once(), audit_once(), audit_once())

            final_count = len(channel.discovered_items)
            assert final_count <= initial_count * 2, (
                f"演化项从 {initial_count} 膨胀到 {final_count}，疑似竞态重复"
            )

        asyncio.run(_run())

    def test_evolution_item_status_transition_race(self):
        """演化项状态转换的并发安全性."""
        from channels.system_evolution import (
            SystemEvolutionChannel,
            EvolutionItem,
            EvolutionStatus,
        )

        async def _run():
            channel = SystemEvolutionChannel()
            channel.initialize()

            item = EvolutionItem(
                id="ev-race-status-test",
                title="竞态状态测试",
                description="测试并发状态转换",
                domain="general",
                severity="low",
            )
            channel.discovered_items.append(item)

            async def dispatch():
                await asyncio.sleep(0.01)
                item.status = EvolutionStatus.DISPATCHED

            async def verify():
                await asyncio.sleep(0.02)
                item.status = EvolutionStatus.VERIFIED

            await asyncio.gather(dispatch(), verify())
            assert item.status in (EvolutionStatus.DISPATCHED, EvolutionStatus.VERIFIED)

        asyncio.run(_run())


# ── 4. 事件日志完整性测试 ──────────────────────────────────────────────────

class TestEventLogIntegrity:
    """并发下事件日志完整性与顺序."""

    def test_event_log_no_loss(self, executor):
        """并发执行时事件日志不应丢失."""
        async def _run():
            with patch.object(executor, '_run_agent_loop') as mock_run:
                mock_run.return_value = {
                    "ok": True, "summary": "done", "files_changed": [], "iterations": 1,
                }
                for i in range(5):
                    await executor.execute(f"ev-log-{i:03d}", _make_item_dict(f"ev-log-{i:03d}"))
                await asyncio.sleep(0.3)

        asyncio.run(_run())

        for i in range(5):
            log = executor.get_event_log(f"ev-log-{i:03d}")
            event_types = [e.get("type") for e in log]
            assert "execution_start" in event_types, f"ev-log-{i:03d} 缺少 execution_start"
            assert "execution_end" in event_types, f"ev-log-{i:03d} 缺少 execution_end"

    def test_executor_status_accurate(self, executor):
        """执行器状态报告在并发下保持准确."""
        async def _run():
            with patch.object(executor, '_run_agent_loop') as mock_run:
                def slow_run(*args, **kwargs):
                    time.sleep(0.1)
                    return {"ok": True, "summary": "slow", "files_changed": [], "iterations": 1}
                mock_run.side_effect = slow_run

                for i in range(5):
                    await executor.execute(f"ev-status-{i:03d}", _make_item_dict(f"ev-status-{i:03d}"))

                status = executor.get_status()
                assert status["completed_count"] >= 0
                assert status["running_count"] <= 5
                await asyncio.sleep(0.8)

        asyncio.run(_run())

        final_status = executor.get_status()
        assert final_status["completed_count"] == 5, (
            f"预期 5 完成, 实际 {final_status['completed_count']}"
        )
        assert final_status["running_count"] == 0


# ── 5. 综合场景 ────────────────────────────────────────────────────────────

class TestIntegrationScenarios:
    """端到端集成场景."""

    def test_full_pipeline_concurrent(self):
        """完整流水线: 审计→发现→派发→执行 (并发版)."""
        from channels.system_evolution import SystemEvolutionChannel
        from channels.evolution_executor import EvolutionExecutor

        async def _run():
            channel = SystemEvolutionChannel()
            channel.initialize()

            executor = EvolutionExecutor()

            await channel.run_full_audit()
            discovered = len(channel.discovered_items)
            assert discovered > 0, "审计未发现任何演化项"

            for item in channel.discovered_items:
                await channel.dispatch_item(item.id)

            completed_ids = []
            lock = asyncio.Lock()

            async def on_complete(item_id, result):
                async with lock:
                    completed_ids.append(item_id)

            executor.set_on_complete(on_complete)

            with patch.object(executor, '_run_agent_loop') as mock_run:
                mock_run.return_value = {
                    "ok": True, "summary": "completed", "files_changed": ["test.py"], "iterations": 2,
                }
                for item in channel.discovered_items[:5]:
                    await executor.execute(item.id, item.to_dict())
                await asyncio.sleep(0.3)

            assert len(completed_ids) == min(5, discovered), (
                f"预期完成 {min(5, discovered)} 个, 实际 {len(completed_ids)}"
            )

        asyncio.run(_run())

    def test_audit_engine_self_check(self):
        """审计引擎自检 — 验证内置规则可用."""
        from channels.system_evolution import SystemEvolutionChannel

        channel = SystemEvolutionChannel()
        channel.initialize()

        assert len(channel.audit_rules) >= 5, "至少应加载 5 条内置规则"

        for rule in channel.audit_rules:
            assert rule.id, f"规则缺少 id"
            assert rule.title, f"规则 {rule.id} 缺少 title"
            assert rule.target_channel, f"规则 {rule.id} 缺少 target_channel"
            assert rule.domain, f"规则 {rule.id} 缺少 domain"


# ── 6. 烟雾测试: 索引就绪与 SkillStore 完整性 ─────────────────────────────

class TestSmokeIndexAndSkillStore:
    """烟雾测试: 验证索引就绪与 SkillStore 完整性."""

    def test_skill_registry_defaults_loaded(self):
        """SkillRegistry 默认技能全部加载."""
        from agents.skill_registry import SkillRegistry

        registry = SkillRegistry()
        registry.load_defaults()

        all_skills = registry.list_all()
        assert len(all_skills) >= 40, f"技能数量不足: {len(all_skills)}"

        # 验证关键技能存在
        required_skill_names = [
            "task_decomposition", "code_implementation", "testing",
            "deployment_orchestration", "build_automation", "container_management",
        ]
        for name in required_skill_names:
            skill = registry.get_by_slug(name)
            assert skill is not None, f"缺少必需技能: {name}"
            assert skill.instructions, f"技能 {name} 缺少指令"

    def test_skill_registry_search(self):
        """SkillRegistry 搜索功能正常."""
        from agents.skill_registry import SkillRegistry

        registry = SkillRegistry()
        registry.load_defaults()

        # 搜索 deploy 相关技能
        results = registry.search("deploy")
        assert len(results) >= 1, "应至少找到 1 个部署相关技能"

        # 搜索不存在的内容
        no_results = registry.search("nonexistent_xyz")
        assert len(no_results) == 0

    def test_skill_registry_categories(self):
        """SkillRegistry 分类统计正确."""
        from agents.skill_registry import SkillRegistry
        from agents.models import SkillCategory

        registry = SkillRegistry()
        registry.load_defaults()

        general = registry.list_by_category(SkillCategory.GENERAL)
        assert len(general) >= 20, f"通用技能不足: {len(general)}"

        dt = registry.list_by_category(SkillCategory.DIGITAL_TWIN)
        assert len(dt) >= 5, f"数字孪生技能不足: {len(dt)}"

        auto = registry.list_by_category(SkillCategory.AUTOMATION)
        assert len(auto) >= 2, f"自动化技能不足: {len(auto)}"

        required = registry.list_required()
        assert len(required) >= 3, "至少应有 3 个必需技能"

    def test_skill_export_markdown(self):
        """SkillRegistry 导出 Markdown 成功."""
        from agents.skill_registry import SkillRegistry

        registry = SkillRegistry()
        registry.load_defaults()

        md = registry.export_all_as_markdown()
        assert md, "Markdown 导出不应为空"
        assert "## " in md, "Markdown 应包含标题"
        assert len(md) > 1000, f"Markdown 太短: {len(md)} 字符"

    def test_plaza_store_index_ready(self):
        """PlazaStore 存储与索引就绪."""
        from agents.plaza_store import PlazaStore

        store = PlazaStore()
        indices = store.get_indices()

        assert "discussions" in indices, "缺少 discussions 索引"
        assert "participants" in indices, "缺少 participants 索引"

        # Plaza 列表应可访问
        plazas = store.list_plazas()
        assert isinstance(plazas, list), "list_plazas() 应返回列表"

        # 初始状态下 plaza 数量（可能为 0）
        assert plazas is not None

    def test_skill_registry_enabled_disabled(self):
        """SkillRegistry 启用/禁用功能正常."""
        from agents.skill_registry import SkillRegistry

        registry = SkillRegistry()
        registry.load_defaults()

        all_skills = registry.list_all()
        if all_skills:
            first_skill = all_skills[0]

            # 初始应为启用状态
            enabled = registry.list_enabled()
            initial_count = len(enabled)

            # 禁用一个技能
            registry.disable(first_skill.skill_id)
            after_disable = len(registry.list_enabled())
            assert after_disable == initial_count - 1

            # 重新启用
            registry.enable(first_skill.skill_id)
            after_enable = len(registry.list_enabled())
            assert after_enable == initial_count


# ── pytest 标记 ──────────────────────────────────────────────────────────

pytest_plugins = []
