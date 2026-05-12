# PM分解 — project_manager

任务: 实现交叉复核硬阻塞逻辑：验证阶段后端校验标注者非上下文补全者且切片满足最低复核人数，前端将提交按钮锁定直至条件满足
步骤: pm_decompose
Agent: build_pm

---

📋 任务: 05a62056-3a9
🤖 Agent: PM (project_manager)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  请执行以下开发任务:
  
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  
  ## 任务
  实现交叉复核硬阻塞逻辑：验证阶段后端校验标注者非上下文补全者且切片满足最低复核人数，前端将提交按钮锁定直至条件满足
  Developer
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/demo-fieldio-particles.html
  src/frontend/demo-lupi-data-humanism.html
  src/frontend/demo-takram-biosynthetic.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/monitoring.html
  src/frontend/plaza-dark.html
  src/frontend/plaza-old.html
  src/frontend/plaza-wabisabi-v2.html
  src/frontend/plaza-wabisabi.html
  src/frontend/plaza.html
  src/frontend/skill-extract.html
  src/frontend/system-evolution.html
  src/frontend/tasks.html
  src/frontend/css/agent-team-config.css
  src/frontend/css/openbridge-theme.css
  src/frontend/css/ws-theme-bridge.css
  src/frontend/js/agent-team-config.js
  src/frontend/js/i18n.js
  src/frontend/js/nav-sidebar.js
  src/backend/__init__.py
  src/backend/agent_team_api.py
  src/backend/main.py
  src/backend/main.py.bak
  src/backend/startup_check.py
  src/backend/startup_validator.py
  src/backend/tests/__init__.py
  src/backend/tests/conftest.py
  src/backend/tests/conftest.py.bak
  src/backend/tests/test_ab_testing.py
  src/backend/tests/test_agent_toolbox.py
  src/backend/tests/test_evolution_race.py
  src/backend/tests/test_evolution_race.py.bak
  src/backend/tests/test_fingerprint.py
  src/backend/tests/test_fingerprint.py.bak
  src/backend/tests/test_gate_evaluator.py
  src/backend/tests/test_gate_evaluator.py.bak
  src/backend/tests/test_merge_plugin.py
  src/backend/tests/test_merge_plugin.py.bak
  src/backend/tests/test_models.py
  src/backend/tests/test_models.py.bak
  src/backend/tests/test_qa_gate_pipeline.py
  src/backend/tests/test_qa_gate_pipeline.py.bak
  src/backend/tests/test_task_engine.py
  src/backend/tests/test_task_engine.py.bak
  src/backend/tests/test_team_manager.py
  src/backend/tests/test_team_manager.py.bak
  src/backend/tests/test_template_variants.py
  src/backend/tests/test_template_variants.py.bak
  src/backend/agents/__init__.py
  src/backend/agents/ab_testing.py
  src/backend/agents/agent_loop.py
  src/backend/agents/agent_toolbox.py
  src/backend/agents/api.py
  src/backend/agents/api.py.bak
  src/backend/agents/audit_store.py
  src/backend/agents/chat_harness.py
  src/backend/agents/domain_events.py
  src/backend/agents/domain_events.py.bak
  src/backend/agents/event_bus.py
  src/backend/agents/execution_registry.py
  src/backend/agents/fingerprint.py
  src/backend/agents/fingerprint.py.bak
  src/backend/agents/gate_evaluator.py
  src/backend/agents/hermes_research.py
  src/backend/agents/knowledge_base.py
  src/backend/agents/merge_engine.py
  src/backend/agents/merge_models.py
  src/backend/agents/models.py
  src/backend/agents/models.py.bak
  src/backend/agents/plaza.py
  src/backend/agents/plaza_engine.py
  src/backend/agents/plaza_routes.py
  src/backend/agents/plaza_routes.py.bak
  src/backend/agents/plaza_store.py
  src/backend/agents/review_models.py
  src/backend/agents/review_routes.py
  src/backend/agents/review_service.py
  src/backend/agents/session_store.py
  src/backend/agents/similarity_engine.py
  src/backend/agents/skill_evolver.py
  src/backend/agents/skill_extractor.py
  src/backend/agents/skill_indexer.py
  src/backend/agents/skill_library.py
  src/backend/agents/skill_querier.py
  src/backend/agents/skill_registry.py
  src/backend/agents/skill_store.py
  src/backend/agents/skill_tracker.py
  src/backend/agents/skill_verifier.py
  src/backend/agents/task_engine.py
  src/backend/agents/task_engine.py.bak
  src/backend/agents/task_store.py
  src/backend/agents/team_manager.py
  src/backend/agents/team_manager.py.bak
  src/backend/agents/team_store.py
  src/backend/agents/tool_executor.py
  src/backend/agents/tool_registry.py
  src/backend/agents/trajectory_analyzer.py
  src/backend/agents/tts_routes.py
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/greeting.py
  src/backend/agents/skills/hello.py
  src/backend/scripts/__init__.py
  src/backend/scripts/migrate.py
  src/backend/scripts/validate_startup.py
  src/backend/scripts/validate_telemetry.py
  src/backend/monitoring/__init__.py
  src/backend/monitoring/__init__.py.bak
  src/backend/monitoring/aggregation_window.py
  src/backend/monitoring/aggregation_window.py.bak
  src/backend/monitoring/collector.py
  src/backend/monitoring/collector.py.bak
  src/backend/monitoring/fingerprint_bypass.py
  src/backend/monitoring/models.py
  src/backend/monitoring/models.py.bak
  src/backend/monitoring/monitoring_routes.py
  src/backend/monitoring/plaza_monitor.py
  src/backend/monitoring/plaza_monitor.py.bak
  src/backend/monitoring/sampler.py
  src/backend/monitoring/trace_bridge.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/evolution_executor.py
  src/backend/channels/marine_base.py
  src/backend/channels/merge_channel.py
  src/backend/channels/openclaw_sync.py
  src/backend/channels/openclaw_sync.py.bak
  src/backend/channels/system_evolution.py
  src/docs/agent_handoffs/01d37305-090_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0261754d-288_executor_started_20260509T073231.md
  src/docs/agent_handoffs/05014547-ce8_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0597d622-ad4_executor_started_20260509T073232.md
  src/docs/agent_handoffs/06d3f2a5-82c_executor_started_20260509T073231.md
  src/docs/agent_handoffs/073864e5-58b_executor_started_20260509T073231.md
  src/docs/agent_handoffs/073a3fe7-4d5_executor_started_20260509T073232.md
  src/docs/agent_handoffs/09ff3a16-710_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0a242acf-f52_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0af6e1cb-61c_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0c263083-1c8_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0f6d4e48-ea3_executor_started_20260509T073232.md
  src/docs/agent_handoffs/10857dbb-a51_executor_started_20260509T073231.md
  src/docs/agent_handoffs/11e9b4b9-283_architecture_20260509T075556.md
  src/docs/agent_handoffs/11e9b4b9-283_deploy_20260509T081242.md
  src/docs/agent_handoffs/11e9b4b9-283_develop_20260509T080722.md
  src/docs/agent_handoffs/11e9b4b9-283_document_20260509T081332.md
  ... (共 728 个 src/ 文件)
  
  ```
  
  ### 文件: `src/backend/tests/conftest.py`
  ```py
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
      # TeamManager() 不接受 store 参数，内部自行创建 TeamStore
      return TeamManager()
  
  
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
      return TaskEngine(max_concurrency=4)
  
  
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
  
  ```
  
  ### 文件: `src/backend/tests/test_agent_toolbox.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentToolbox 单元测试 — 工具函数 (read_file, grep, list_files, dispatch)."""
  
  from __future__ import annotations
  
  import json
  import os
  import tempfile
  from pathlib import Path
  
  import pytest
  
  from agents.agent_toolbox import (
      TOOL_SCHEMA,
      dispatch_tool_call,
      get_tools_for_role,
      tool_grep,
      tool_list_files,
      tool_patch_file,
      tool_read_file,
      tool_run_python,
      tool_run_pytest,
      tool_write_file,
  )
  
  
  # ═══════════════════════════════════════════════════
  # read_file 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolReadFile:
      """tool_read_file 单元测试."""
  
      def test_read_existing_file(self):
          result = tool_read_file("src/backend/tests/__init__.py")
          assert result["ok"] is True
          assert "Test Pipeline" in result["content"]
  
      def test_read_with_line_range(self):
          result = tool_read_file(
              "src/backend/tests/__init__.py",
              start_line=1,
              end_line=3,
          )
          assert result["ok"] is True
          assert result["total_lines"] > 0
  
      def test_read_nonexistent_file(self):
          result = tool_read_file("nonexistent/file.txt")
          assert result["ok"] is False
  
      def test_read_empty_path_raises(self):
          result = tool_read_file("")
          assert result["ok"] is False
  
  
  # ═══════════════════════════════════════════════════
  # grep 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolGrep:
      """tool_grep 单元测试."""
  
      def test_grep_finds_matches(self):
          result = tool_grep(r"class.*Test", include="src/backend/tests/*.py")
          assert result["ok"] is True
          assert len(result["hits"]) > 0
          for hit in result["hits"]:
              assert "path" in hit
              assert "line" in hit
              assert "text" in hit
  
      def test_grep_no_matches(self):
          result = tool_grep(r"XYZZY_NOT_FOUND_12345", include="src/backend/tests/*.py")
          assert result["ok"] is True
          assert len(result["hits"]) == 0
  
      def test_grep_bad_regex(self):
          result = tool_grep(r"[invalid")
          assert result["ok"] is False
          assert "bad regex" in result["error"]
  
      def test_grep_max_hits(self):
          result = tool_grep(r"def ", include="src/backend/agents/*.py", max_hits=3)
          assert result["ok"] is True
          assert len(result["hits"]) <= 3
  
  
  # ═══════════════════════════════════════════════════
  # list_files 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolListFiles:
      """tool_list_files 单元测试."""
  
      def test_list_tests_directory(self):
          result = tool_list_files("src/backend/tests")
          assert result["ok"] is True
          files = result["files"]
          assert any("__init__.py" in f for f in files)
          assert any("conftest.py" in f for f in files)
  
      def test_list_nonexistent_directory(self):
          result = tool_list_files("nonexistent/dir")
          assert result["ok"] is False
  
      def test_list_with_depth(self):
          result = tool_list_files("src/backend", max_depth=1)
          assert result["ok"] is True
          # 不应深入到 agents/ 子目录
          for f in result["files"]:
              assert "/agents/" not in f or f.count("/") <= 2
  
  
  # ═══════════════════════════════════════════════════
  # write_file / patch_file 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolWriteFile:
      """tool_write_file 单元测试."""
  
      def test_write_new_file(self):
          result = tool_write_file(
              "tests/_test_write_temp.txt",
              "hello world",
          )
          assert result["ok"] is True
          assert result["path"] == "tests/_test_write_temp.txt"
          # 清理
          Path("src/backend/tests/_test_write_temp.txt").unlink(missing_ok=True)
  
      def test_write_outside_allowed_fails(self):
          result = tool_write_file(
              "../outside.txt",
              "should fail",
          )
          assert result["ok"] is False
  
      def test_create_only_existing(self):
          # conftest.py 已存在
          result = tool_write_file(
              "tests/conftest.py",
              "new content",
              create_only=True,
          )
          assert result["ok"] is False
          assert "create_only" in result["error"]
  
  
  class TestToolPatchFile:
      """tool_patch_file 单元测试."""
  
      def test_patch_unique_match(self):
          # 先创建临时文件
          tmp_path = "tests/_test_patch_temp.py"
          tool_write_file(tmp_path, "original line\nother line\n")
  
          result = tool_patch_file(
              tmp_path,
              search="original line",
              replace="patched line",
          )
          assert result["ok"] is True
  
          # 验证修改
          read_back = tool_read_file(tmp_path)
          assert "patched line" in read_back["content"]
  
          # 清理
          Path("src/backend/tests/_test_patch_temp.py").unlink(missing_ok=True)
  
      def test_patch_not_found(self):
          result = tool_patch_file(
              "tests/conftest.py",
              search="NOT_IN_THIS_FILE_XYZ",
              replace="whatever",
          )
          assert result["ok"] is False
  
      def test_patch_outside_allowed(self):
          result = tool_patch_file(
              "../outside.txt",
              search="x",
              replace="y",
          )
          assert result["ok"] is False
  
  
  # ═══════════════════════════════════════════════════
  # run_python 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolRunPython:
      """tool_run_python 单元测试."""
  
      def test_simple_expression(self):
          result = tool_run_python("print(1+1)")
          assert result["ok"] is True
          assert result["exit_code"] == 0
          assert "2" in result["stdout"]
  
      def test_import_check(self):
          result = tool_run_python("from agents.models import AgentProfile; print('OK')")
          assert result["ok"] is True
          assert "OK" in result["stdout"]
  
      def test_syntax_error(self):
          result = tool_run_python("def broken(")
          assert result["ok"] is True  # subprocess 成功执行
          assert result["exit_code"] != 0
  
  
  # ═══════════════════════════════════════════════════
  # run_pytest 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolRunPytest:
      """tool_run_pytest 单元测试."""
  
      def test_run_pytest_collect_only(self):
          result = tool_run_pytest("tests/test_models.py --co")
          assert result["ok"] is True
  
  
  # ═══════════════════════════════════════════════════
  # dispatch_tool_call 测试
  # ═══════════════════════════════════════════════════
  
  class TestDispatchToolCall:
      """dispatch_tool_call 单元测试."""
  
      def test_dispatch_read_file(self):
          result = dispatch_tool_call(
              "read_file",
              json.dumps({"path": "src/backend/tests/__init__.py"}),
          )
          assert result["ok"] is True
  
      def test_dispatch_finish(self):
          result = dispatch_tool_call("finish", "{}")
          assert result["ok"] is True
          assert result["_finished"] is True
  
      def test_dispatch_unknown_tool(self):
          result = dispatch_tool_call("unknown_tool", "{}")
          assert result["ok"] is False
  
      def test_dispatch_bad_json_args(self):
          result = dispatch_tool_call("read_file", "not json")
          assert result["ok"] is False
  
      def test_dispatch_bad_kwargs(self):
          result = dispatch_tool_call(
              "read_file",
              json.dumps({"path": "tests/__init__.py", "extra_bad_kwarg": True}),
          )
          # Either ok=False due to TypeError, or ok=True (if extra kwarg ignored)
          assert "ok" in result  # 至少返回了有效结构
  
  
  # ═══════════════════════════════════════════════════
  # get_tools_for_role 测试
  # ═══════════════════════════════════════════════════
  
  class TestGetToolsForRole:
      """get_tools_for_role 单元测试."""
  
      def test_developer_has_write_tools(self):
          tools = get_tools_for_role("developer")
          names = {t["function"]["name"] for t in tools}
          assert "write_file" in names
          assert "patch_file" in names
          assert "run_python" in names
  
      def test_qa_has_pytest(self):
          tools = get_tools_for_role("qa")
          names = {t["function"]["name"] for t in tools}
          assert "run_pytest" in names
  
      def test_architect_has_readonly(self):
          tools = get_tools_for_role("architect")
          names = {t["function"]["name"] for t in tools}
          assert "write_file" not in names
          assert "run_python" in names
  
      def test_all_roles_have_read_grep_list(self):
          for role in ("developer", "qa", "architect", "researcher", "unknown"):
              tools = get_tools_for_role(role)
              names = {t["function"]["name"] for t in tools}
              assert "read_file" in names
              assert "grep" in names
              assert "list_files" in names
              assert "finish" in names
  
  
  # ═══════════════════════════════════════════════════
  # TOOL_SCHEMA 结构测试
  # ═══════════════════════════════════════════════════
  
  class TestToolSchema:
      """TOOL_SCHEMA 常量测试."""
  
      def test_all_tools_have_function_name(self):
          for tool in TOOL_SCHEMA:
              assert "function" in tool
              assert "name" in tool["function"]
  
      def test_known_tools_present(self):
          names = {t["function"]["name"] for t in TOOL_SCHEMA}
          expected = {"read_file", "grep", "list_files", "write_file",
                      "patch_file", "run_python", "run_pytest", "finish"}
          assert expected.issubset(names)
  
  ```
  
  ### 文件: `src/backend/tests/test_fingerprint.py`
  ```py
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
          assert engine.mutation_rate =
  ```
  
  ### 文件: `src/backend/tests/test_models.py`
  ```py
  # -*- coding: utf-8 -*-
  """数据模型单元测试 — AgentProfile, AgentTeam, ModelConfig 等."""
  
  from __future__ import annotations
  
  import json
  
  from agents.models import (
      AccessLevel,
      AgentChannelConfig,
      AgentPermission,
      AgentPersonality,
      AgentProfile,
      AgentState,
      AgentTeam,
      AgentTemplateType,
      ModelConfig,
      SkillCategory,
      SkillDefinition,
      ToolCategory,
      ToolDefinition,
      Visibility,
  )
  
  
  # ═══════════════════════════════════════════════════
  # AgentState 枚举测试
  # ═══════════════════════════════════════════════════
  
  class TestAgentState:
      """AgentState 枚举测试."""
  
      def test_all_states_exist(self):
          states = set(s.value for s in AgentState)
          assert "idle" in states
          assert "working" in states
          assert "paused" in states
          assert "error" in states
          assert "stopped" in states
  
      def test_state_count(self):
          assert len(list(AgentState)) == 5
  
  
  # ═══════════════════════════════════════════════════
  # AgentProfile 测试
  # ═══════════════════════════════════════════════════
  
  class TestAgentProfile:
      """AgentProfile 数据类测试."""
  
      def test_minimal_creation(self):
          agent = AgentProfile(
              agent_id="agent-001",
              name="TestAgent",
              role="developer",
          )
          assert agent.agent_id == "agent-001"
          assert agent.name == "TestAgent"
          assert agent.role == "developer"
          assert agent.state == AgentState.IDLE
          assert agent.template_type == AgentTemplateType.CUSTOM
  
      def test_full_creation(self):
          personality = AgentPersonality(
              tone="friendly",
              language="en-US",
              expertise_areas=["python", "testing"],
              response_style="verbose",
              creativity=0.8,
          )
          agent = AgentProfile(
              agent_id="agent-002",
              name="FullAgent",
              role="engineer",
              description="A fully configured test agent",
              template_type=AgentTemplateType.DEVELOPER,
              state=AgentState.WORKING,
              model_id="model-deepseek-v4",
              system_prompt="You are a test agent.",
              personality=personality,
          )
          assert agent.agent_id == "agent-002"
          assert agent.personality.tone == "friendly"
          assert agent.personality.creativity == 0.8
          assert agent.personality.response_style == "verbose"
  
      def test_to_dict_roundtrip(self):
          agent = AgentProfile(
              agent_id="agent-003",
              name="Roundtrip",
              role="analyst",
          )
          d = agent.to_dict()
          assert d["agent_id"] == "agent-003"
          assert d["name"] == "Roundtrip"
          assert d["role"] == "analyst"
          assert d["state"] == "idle"
  
      def test_to_dict_is_json_serializable(self):
          agent = AgentProfile(
              agent_id="agent-004",
              name="Serializable",
              role="coordinator",
          )
          d = agent.to_dict()
          json_str = json.dumps(d)
          restored = json.loads(json_str)
          assert restored["agent_id"] == "agent-004"
  
  
  # ═══════════════════════════════════════════════════
  # AgentTeam 测试
  # ═══════════════════════════════════════════════════
  
  class TestAgentTeam:
      """AgentTeam 数据类测试."""
  
      def test_create_team(self):
          team = AgentTeam(
              team_id="team-001",
              name="Test Team",
              description="A test team",
          )
          assert team.team_id == "team-001"
          assert team.name == "Test Team"
          assert team.visibility == Visibility.PRIVATE
  
      def test_add_agent_to_team(self):
          agent = AgentProfile(
              agent_id="agent-005",
              name="Member",
              role="engineer",
          )
          team = AgentTeam(
              team_id="team-002",
              name="MemberTeam",
          )
          team.agents.append(agent)
          assert len(team.agents) == 1
          assert team.agents[0].agent_id == "agent-005"
  
      def test_to_dict(self):
          team = AgentTeam(
              team_id="team-003",
              name="DictTeam",
              description="Testing to_dict",
          )
          d = team.to_dict()
          assert d["team_id"] == "team-003"
          assert d["name"] == "DictTeam"
          assert "agents" in d
  
      def test_to_dict_is_json_serializable(self):
          team = AgentTeam(
              team_id="team-004",
              name="JsonTeam",
          )
          d = team.to_dict()
          json_str = json.dumps(d)
          restored = json.loads(json_str)
          assert restored["team_id"] == "team-004"
  
  
  # ═══════════════════════════════════════════════════
  # ModelConfig 测试
  # ═══════════════════════════════════════════════════
  
  class TestModelConfig:
      """ModelConfig 数据类测试."""
  
      def test_default_creation(self):
          model = ModelConfig(
              model_id="model-deepseek-v4",
              provider="deepseek",
              name="deepseek-v4-flash",
          )
          assert model.model_id == "model-deepseek-v4"
          assert model.provider == "deepseek"
          assert model.max_tokens == 65536
          assert model.temperature == 0.7
          assert model.is_default is False
          assert model.enabled is True
  
      def test_custom_config(self):
          model = ModelConfig(
              model_id="model-custom",
              provider="openai",
              name="gpt-4o-mini",
              max_tokens=128000,
              temperature=0.3,
              is_default=True,
              api_key="sk-test",
              api_base_url="https://api.openai.com/v1",
          )
          assert model.max_tokens == 128000
          assert model.temperature == 0.3
          assert model.is_default is True
          assert model.api_key == "sk-test"
  
      def test_to_dict(self):
          model = ModelConfig(
              model_id="model-dict",
              provider="anthropic",
              name="claude-sonnet",
          )
          d = model.to_dict()
          assert d["model_id"] == "model-dict"
          assert d["provider"] == "anthropic"
          assert d["is_default"] is False
  
  
  # ═══════════════════════════════════════════════════
  # ToolDefinition 测试
  # ═══════════════════════════════════════════════════
  
  class TestToolDefinition:
      """ToolDefinition 测试."""
  
      def test_create_tool(self):
          tool = ToolDefinition(
              tool_id="tool-read-file",
              name="Read File",
              description="Read file contents",
              category=ToolCategory.GENERAL,
          )
          assert tool.tool_id == "tool-read-file"
          assert tool.name == "Read File"
          assert tool.category == ToolCategory.GENERAL
          assert tool.enabled is True
  
      def test_tool_with_config(self):
          tool = ToolDefinition(
              tool_id="tool-web-search",
              name="Web Search",
              description="Search the web",
              category=ToolCategory.GENERAL,
              requires_approval=True,
              config={"api_endpoint": "https://search.example.com"},
          )
          assert tool.requires_approval is True
          assert tool.config["api_endpoint"] == "https://search.example.com"
  
      def test_to_dict(self):
          tool = ToolDefinition(
              tool_id="tool-dict",
              name="Dict Tool",
              description="A dict test",
              category=ToolCategory.GENERAL,
          )
          d = tool.to_dict()
          assert d["tool_id"] == "tool-dict"
          assert d["name"] == "Dict Tool"
  
  
  # ═══════════════════════════════════════════════════
  # SkillDefinition 测试
  # ═══════════════════════════════════════════════════
  
  class TestSkillDefinition:
      """SkillDefinition 测试."""
  
      def test_create_skill(self):
          skill = SkillDefinition(
              skill_id="skill-greeting",
              name="Greeting",
              description="Greet users",
              category=SkillCategory.GENERAL,
          )
          assert skill.skill_id == "skill-greeting"
          assert skill.name == "Greeting"
          assert skill.category == SkillCategory.GENERAL
  
      def test_skill_with_instructions(self):
          skill = SkillDefinition(
              skill_id="skill-code-review",
              name="Code Review",
              description="Review code changes",
              category=SkillCategory.RESEARCH,
              instructions="Analyze the code diff carefully.",
              required=True,
          )
          assert skill.instructions == "Analyze the code diff carefully."
          assert skill.required is True
  
      def test_to_dict(self):
          skill = SkillDefinition(
              skill_id="skill-dict",
              name="DictSkill",
              description="A dict skill",
              category=SkillCategory.GENERAL,
          )
          d = skill.to_dict()
          assert d["skill_id"] == "skill-dict"
          assert d["name"] == "DictSkill"
  
  
  # ═══════════════════════════════════════════════════
  # AgentPermission 测试
  # ═══════════════════════════════════════════════════
  
  class TestAgentPermission:
      """AgentPermission 测试."""
  
      def test_create_permission(self):
          perm = AgentPermission(
              agent_id="agent-001",
              access_level=AccessLevel.READ,
              allowed_tools=["tool-read-file", "tool-grep"],
          )
          assert perm.agent_id == "agent-001"
          assert perm.access_level == AccessLevel.READ
          assert "tool-read-file" in perm.allowed_tools
  
      def test_defaults(self):
          perm = AgentPermission(agent_id="agent-002")
          assert perm.access_level == AccessLevel.READ
          assert perm.allowed_tools == []
  
  
  # ═══════════════════════════════════════════════════
  # ChannelConfig 测试
  # ═══════════════════════════════════════════════════
  
  class TestAgentChannelConfig:
      """AgentChannelConfig 测试."""
  
      def test_create_channel_config(self):
          cfg = AgentChannelConfig(
              channel="openclaw",
              endpoint="https://sync.example.com",
              sync_interval_seconds=30,
          )
          assert cfg.channel == "openclaw"
          assert cfg.sync_interval_seconds == 30
          assert cfg.enabled is True
  
      def test_to_dict(self):
          cfg = AgentChannelConfig(
              channel="bridge",
              endpoint="wss://bridge.example.com",
          )
          d = cfg.to_dict()
          assert d["channel"] == "bridge"
          assert d["enabled"] is True
  
  ```
  
  ### 文件: `src/backend/tests/test_team_manager.py`
  ```py
  # -*- coding: utf-8 -*-
  """团队管理器单元测试 — TeamManager CRUD 操作."""
  
  from __future__ import annotations
  
  import pytest
  
  from agents.models import (
      AgentProfile,
      AgentTeam,
      ModelConfig,
  )
  
  
  class TestTeamManagerCreate:
      """TeamManager 创建操作测试."""
  
      def test_create_team(self, team_manager):
          team = team_manager.create_team(
              name="测试团队",
              team_id="team-001",
              description="自动化测试",
          )
          assert team is not None
          assert team.team_id == "team-001"
          assert team.name == "测试团队"
          assert team.description == "自动化测试"
  
      def test_create_duplicate_team_raises(self, team_manager):
          team_manager.create_team(name="A", team_id="team-001")
          with pytest.raises(ValueError):
              team_manager.create_team(name="B", team_id="team-001")
  
  
  class TestTeamManagerRead:
      """TeamManager 读取操作测试."""
  
      def test_get_team(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          team = team_manager.get_team("t1")
          assert team is not None
          assert team.name == "T1"
  
      def test_get_nonexistent_team(self, team_manager):
          team = team_manager.get_team("nonexistent")
          assert team is None
  
      def test_list_teams(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          team_manager.create_team(name="T2", team_id="t2")
          teams = team_manager.list_teams()
          assert len(teams) == 2
          names = {t.name for t in teams}
          assert names == {"T1", "T2"}
  
  
  class TestTeamManagerUpdate:
      """TeamManager 更新操作测试."""
  
      def test_update_team(self, team_manager):
          team_manager.create_team(name="Old", team_id="t1")
          updated = team_manager.update_team("t1", name="New", description="Updated")
          assert updated is not None
          assert updated.name == "New"
          assert updated.description == "Updated"
  
      def test_update_team_ignores_immutable(self, team_manager):
          team_manager.create_team(name="OK", team_id="t1")
          # team_id 不在 AgentTeam dataclass 中当作可变字段
          updated = team_manager.update_team("t1", name="StillOK")
          assert updated is not None
          assert updated.team_id == "t1"  # team_id 不可变
  
      def test_update_nonexistent_team(self, team_manager):
          result = team_manager.update_team("noop", name="X")
          assert result is None
  
  
  class TestTeamManagerDelete:
      """TeamManager 删除操作测试."""
  
      def test_delete_team(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          deleted = team_manager.delete_team("t1")
          assert deleted is not None
          assert team_manager.get_team("t1") is None
  
      def test_delete_nonexistent_team(self, team_manager):
          result = team_manager.delete_team("noop")
          assert result is None
  
  
  class TestAgentManagement:
      """Agent 管理操作测试."""
  
      def test_add_agent(self, team_manager, sample_agent_dict):
          team_manager.create_team(name="T1", team_id="t1")
          agent = AgentProfile(
              agent_id="agent-001",
              name="TestAgent",
              role="developer",
              state="idle",
          )
          result = team_manager.add_agent_to_team("t1", agent)
          assert result is True
  
      def test_get_agent(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          agent = AgentProfile(agent_id="a1", name="A1", role="developer")
          team_manager.add_agent_to_team("t1", agent)
  
          found = team_manager.get_agent("t1", "a1")
          assert found is not None
          assert found.name == "A1"
  
      def test_get_agent_nonexistent_team(self, team_manager):
          result = team_manager.get_agent("no-team", "any-agent")
          assert result is None
  
      def test_list_agents(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a1", name="A1", role="dev"))
          team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a2", name="A2", role="qa"))
  
          agents = team_manager.list_agents("t1")
          assert len(agents) == 2
  
      def test_list_agents_empty_team(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          agents = team_manager.list_agents("t1")
          assert agents == []
  
      def test_list_agents_nonexistent_team(self, team_manager):
          agents = team_manager.list_agents("no-team")
          assert agents == []
  
      def test_remove_agent(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          agent = AgentProfile(agent_id="a1", name="A1", role="developer")
          team_manager.add_agent_to_team("t1", agent)
  
          removed = team_manager.remove_agent_from_team("t1", "a1")
          assert removed is not None
          assert removed.name == "A1"
          assert team_manager.get_agent("t1", "a1") is None
  
  
  class TestModelManagement:
      """Model 管理操作测试."""
  
      def test_add_model(self, team_manager, sample_model_dict):
          team_manager.create_team(name="T1", team_id="t1")
          model = ModelConfig(
              model_id="model-001",
              name="deepseek-v4",
              provider="deepseek",
          )
          result = team_manager.add_model_to_team("t1", model)
          assert result is True
  
      def test_add_model_to_nonexistent_team(self, team_manager):
          model = ModelConfig(model_id="m1", name="M1", provider="openai")
          result = team_manager.add_model_to_team("no-team", model)
          assert result is False
  
      def test_remove_model(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          model = ModelConfig(model_id="m1", name="M1", provider="deepseek")
          team_manager.add_model_to_team("t1", model)
  
          removed = team_manager.remove_model_from_team("t1", "m1")
          assert removed is not None
          assert removed.name == "M1"
  
  
  class TestTeamOverview:
      """Team overview 操作测试."""
  
      def test_get_team_overview(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a1", name="A1", role="developer"))
  
          overview = team_manager.get_team_overview("t1")
          assert overview is not None
          assert overview["team_id"] == "t1"
          assert overview["name"] == "T1"
          assert overview["agent_count"] == 1
  
      def test_get_team_overview_nonexistent(self, team_manager):
          overview = team_manager.get_team_overview("no-team")
          assert overview is None
  
  
  class TestDuplicateAgent:
      """Agent 复制功能测试."""
  
      def test_duplicate_agent(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          original = AgentProfile(agent_id="a1", name="Original", role="developer")
          team_manager.add_agent_to_team("t1", original)
  
          clone = team_manager.duplicate_agent("t1", "a1")
          assert clone is not None
          assert "副本" in clone.name
          assert clone.agent_id != original.agent_id
          # 验证克隆已在 team 中
          agents = team_manager.list_agents("t1")
          assert len(agents) == 2
  
      def test_duplicate_nonexistent_agent(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          result = team_manager.duplicate_agent("t1", "nonexistent")
          assert result is None
  
  
  class TestSerialization:
      """序列化操作测试."""
  
      def test_to_dict(self, team_manager):
          team_manager.create_team(name="T1", team_id="t1")
          d = team_manager.to_dict()
          assert "t1" in d
          assert d["t1"]["name"] == "T1"
  
  ```
  
  ### 文件: `src/backend/agents/agent_loop.py`
  ```py
  """Function-calling loop for Developer/QA agents.
  
  Drives a multi-turn conversation with DeepSeek V4 where each turn the model can
  call tools (read_file, grep, write_file, patch_file, run_python, run_pytest) to
  inspect and modify the codebase, then finishes with a `finish` tool call.
  
  This replaces the single-shot "emit a markdown blob with code fences" approach
  that produced hallucinated imports and truncated files.
  """
  from __future__ import annotations
  
  import http.client
  import json
  import logging
  import ssl
  import time
  from typing import Any, Dict, List, Optional
  from urllib.parse import urlparse
  
  from .agent_toolbox import (
      TOOL_SCHEMA,
      dispatch_tool_call,
      get_tools_for_role,
  )
  
  logger = logging.getLogger("AgentLoop")
  
  DEFAULT_MAX_ITERATIONS = 25
  DEFAULT_MAX_TOKENS = 65536
  DEFAULT_TEMPERATURE = 0.2
  
  # ── Safeguard constants ──
  # Safeguard 1: auto-finish nudge when approaching iteration cap
  _ITERATION_NUDGE_RATIO = 0.80  # at 80% of max_iterations, inject nudge
  # Safeguard 2: context budget — compress old tool results when messages grow
  _CONTEXT_BUDGET_CHARS = 100_000  # max combined chars in messages
  _TOOL_RESULT_TRUNC = 500  # truncate old tool results to this when over budget
  
  
  class AgentLoop:
      """Multi-turn function-calling driver against an OpenAI-compatible endpoint."""
  
      def __init__(
          self,
          *,
          api_key: str,
          api_base_url: str,
          model: str,
          role: str,
          system_prompt: str,
          max_iterations: int = DEFAULT_MAX_ITERATIONS,
          max_tokens: int = DEFAULT_MAX_TOKENS,
          temperature: float = DEFAULT_TEMPERATURE,
          on_event: Optional[Any] = None,
      ):
          self.api_key = api_key
          self.api_base_url = api_base_url.rstrip("/")
          self.model = model
          self.role = role
          self.max_iterations = max_iterations
          self.max_tokens = max_tokens
          self.temperature = temperature
          self.tools = get_tools_for_role(role)
          self.messages: List[Dict[str, Any]] = [
              {"role": "system", "content": system_prompt},
          ]
          self.on_event = on_event   # callable(event_type:str, payload:dict)
          self.files_changed: List[str] = []
          self.summary: str = ""
          self.tool_call_log: List[Dict[str, Any]] = []
          # QA/test roles get an earlier nudge (50%) to converge faster
          _role_lower = (role or "").lower()
          self._is_qa_role = _role_lower in ("qa_engineer", "qa", "test", "build_tester")
          self._nudge_ratio = 0.50 if self._is_qa_role else _ITERATION_NUDGE_RATIO
  
      # ────────────────────────────────────────────────
      # HTTP plumbing
      # ────────────────────────────────────────────────
      _API_MAX_RETRIES = 3
      _API_RETRY_BACKOFF = [2, 5, 10]  # seconds between retries
      # Transient errors worth retrying
      _RETRYABLE = (
          ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError,
          BrokenPipeError, TimeoutError, OSError,
          http.client.RemoteDisconnected, http.client.IncompleteRead,
      )
  
      def _post_chat(self) -> Dict[str, Any]:
          parsed = urlparse(self.api_base_url)
          host = parsed.hostname or "api.deepseek.com"
          port = parsed.port or (443 if parsed.scheme == "https" else 80)
          path = (parsed.path or "").rstrip("/") + "/chat/completions"
          ctx = ssl.create_default_context() if parsed.scheme == "https" else None
          conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
  
          payload: Dict[str, Any] = {
              "model": self.model,
              "messages": self.messages,
              "tools": self.tools,
              "tool_choice": "auto",
              "max_tokens": self.max_tokens,
              "temperature": self.temperature,
              "stream": False,
              "thinking": {"type": "enabled"},
              "reasoning_effort": "high",
          }
          body_str = json.dumps(payload)
          headers = {
              "Authorization": f"Bearer {self.api_key}",
              "Content-Type": "application/json",
          }
  
          last_err: Optional[Exception] = None
          for attempt in range(self._API_MAX_RETRIES):
              try:
                  conn = conn_cls(host, port, context=ctx, timeout=300) if ctx \
                      else conn_cls(host, port, timeout=300)
                  conn.request("POST", path, body=body_str, headers=headers)
                  resp = conn.getresponse()
                  raw = resp.read().decode("utf-8", errors="replace")
                  conn.close()
                  if resp.status == 429 or resp.status >= 500:
                      # Server-side error — retryable
                      raise RuntimeError(f"LLM HTTP {resp.status}: {raw[:300]}")
                  if resp.status >= 400:
                      raise RuntimeError(f"LLM HTTP {resp.status}: {raw[:500]}")
                  return json.loads(raw)
              except self._RETRYABLE as e:
                  last_err = e
                  wait = self._API_RETRY_BACKOFF[min(attempt, len(self._API_RETRY_BACKOFF) - 1)]
                  logger.warning(
                      "[AgentLoop] Transient error on attempt %d/%d: %s — retrying in %ds",
                      attempt + 1, self._API_MAX_RETRIES, e, wait,
                  )
                  time.sleep(wait)
              except RuntimeError as e:
                  # HTTP 429 / 5xx — retry with backoff
                  if "HTTP 4" in str(e) and "HTTP 429" not in str(e):
                      raise  # 4xx (non-429) is not retryable
                  last_err = e
                  wait = self._API_RETRY_BACKOFF[min(attempt, len(self._API_RETRY_BACKOFF) - 1)]
                  logger.warning(
                      "[AgentLoop] Server error on attempt %d/%d: %s — retrying in %ds",
                      attempt + 1, self._API_MAX_RETRIES, e, wait,
                  )
                  time.sleep(wait)
          raise last_err or RuntimeError("_post_chat failed after retries")
  
      # ────────────────────────────────────────────────
      # Loop
      # ────────────────────────────────────────────────
      def run(self, user_prompt: str) -> Dict[str, Any]:
          """Run the agent loop. Returns {ok, summary, files_changed, iterations, log}."""
          self.messages.append({"role": "user", "content": user_prompt})
          self._emit("loop_start", {"role": self.role, "tools": [t["function"]["name"] for t in self.tools]})
  
          for it in range(self.max_iterations):
              # ── Safeguard 1: nudge agent when approaching iteration cap ──
              self._maybe_inject_nudge(it)
              # ── Safeguard 2: compact old tool results when context too large ──
              self._compact_old_tool_results()
  
              t0 = time.time()
              try:
                  resp = self._post_chat()
              except Exception as e:
                  logger.exception("[AgentLoop] HTTP error on iteration %d (after retries)", it)
                  self._emit("error", {"iteration": it, "error": str(e)})
                  # If we have already done useful work, don't discard it —
                  # treat as a graceful e
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  ## 要求
  1. 分析任务需求，拆解为可执行的子步骤
  2. 识别技术风险和依赖关系
  3. 为后续研究人员、架构师、开发者提供清晰的指导
  4. 输出一份结构化的任务分解文档 (Markdown 格式)
  
  ## ⚠️ 重要提示
  系统已自动预加载项目文件结构和相关源文件（见下方 📂 项目上下文）。
  请基于**实际存在的文件**进行分析，不要猜测文件名。
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
⚡ 使用 DeepSeek V4 直连 (64K 输出, 流式)...

🔗 API: api.deepseek.com | 模型: deepseek-v4-pro
────────────────────────────────────────────────────────────

## 任务分解：交叉复核硬阻塞逻辑

### 一、需求澄清（供架构师 / 开发者参考）
当前需求要求实现一条硬性约束，应用在标注复核（Review）的提交环节：

- **后端硬校验**
  1. 提交复核的用户不能是该数据切片的上下文补全者（Context Completer）。
  2. 该数据切片已完成的有效复核数必须达到配置的最低复核人数（如 3 人）。
- **前端提交锁定**
  3. 提交按钮在前端动态检测条件是否满足，不满足时保持锁定（disabled + tooltip 提示原因），直至后端通过校验。

目标：从根源上杜绝“自己复核自己”以及复核人数不足即提交的情况。

---

### 二、前置调研（需要研究人员 / 资深开发先行确认）

| 调研项 | 涉及文件 | 关键点 |
|--------|----------|--------|
| 现有 Review 流程与数据模型 | `src/backend/agents/review_models.py`<br>`src/backend/agents/review_service.py`<br>`src/backend/agents/review_routes.py` | 确认 `ReviewSession`、`Slice`、`ReviewerAssignment` 等模型字段；核实是否存在“上下文补全者”、“标注者”等角色记录 |
| 提交复核的 API 端点 | `src/backend/agents/review_routes.py` | 找到提交复核的端点（如 `POST /api/review/submit`），分析其现有校验逻辑 |
| 前端提交界面 | `src/frontend/tasks.html` 及其关联 JS | 定位当前提交按钮的实现、状态管理方式 |
| 最低复核人数配置来源 | 可能是 `ReviewConfig` 或 `ProjectSettings` 中的字段（如 `min_reviewers`） | 确认配置位置 |
| 前端 API 调用方式 | 前端 JS 中是否已有状态轮询 / WebSocket，或可通过提交前预检接口获得满足条件的状态 | 决定前端是轮询检查还是提交前实时调用检测接口 |

> ⚠️ **注意**：不要依据猜测直接编码，必须依据实际代码调研结果。

---

### 三、任务拆解（分四个可并行/串行的工作包）

#### 1. 后端 — 数据模型 & 配置层梳理
**负责人：架构师 / 高级后端**

- [ ] 1.1 审查 `review_models.py`，确认如下字段是否存在，若无则新增：
  - `Slice.context_completer_id` （或等价字段，标识上下文补全者用户 ID）
  - `Slice.min_reviewers` 或 `Project.min_reviewers`
  - `ReviewSession.submitted_by` 记录提交者
- [ ] 1.2 明确“标注者”和“上下文补全者”的角色定义，确保两者身份唯一且可追溯。
- [ ] 1.3 设计校验状态结构体（如 `ReviewValidation`），包含 `passed: bool`、`blocked_reasons: list[str]`。

#### 2. 后端 — 硬校验逻辑实现
**负责人：后端开发**

- [ ] 2.1 在 `review_service.py` 中新增函数 `validate_cross_review(slice_id, submitter_id) -> ReviewValidation`：
  - 判断 `submitter_id == slice.context_completer_id` → 若相等，记录 `blocked_reasons: "您是当前切片的上下文补全者，不能自我复核"`
  - 统计该切片已完成的有效复核数（`ReviewSession` 中 `status=completed` 的数目，并去重用户），若少于 `slice.min_reviewers` → 记录 `"复核人数不足，至少需要 {min} 人复核"`
  - 返回综合状态。
- [ ] 2.2 修改提交复核的 API 端点（如 `POST /api/review/submit`），在处理主业务逻辑前调用 `validate_cross_review`，若 `passed=False` 则返回 `409 Conflict` 或 `422 Unprocessable Entity`，附带阻断原因列表。
- [ ] 2.3 新增一个轻量级预检接口 `GET /api/review/check-submit/{slice_id}?user_id=...`，返回 `ReviewValidation`，供前端提交前实时检查。

#### 3. 前端 — 提交按钮动态锁定
**负责人：前端开发**

- [ ] 3.1 定位 `tasks.html`（或对应任务详情页）中复核提交按钮 ID / class。
- [ ] 3.2 增加前端逻辑：
  - 页面加载时、切片选择变化时、复核列表更新时，调用 `GET /api/review/check-submit/{slice_id}` 接口。
  - 根据返回的 `passed` 和 `blocked_reasons`：
    - 若 `passed=false` → 按钮置灰（`disabled`），并在按钮旁显示 tooltip 或红色提示文本，内容为第一个阻断原因。
    - 若 `passed=true` → 按钮可点击。
- [ ] 3.3 点击提交时，后端仍会再次校验（双重保险），前端必须处理 409/422 异常，弹出对应错误提示。

#### 4. 测试与集成
**负责人：QA / 测试开发**

- [ ] 4.1 编写后端单元测试（`test_review_service.py` 或 `test_review_routes.py`）：
  - 上下文补全者尝试提交自己被分配复核的切片，期望返回冲突。
  - 复核人数不足时提交，期望返回冲突。
  - 条件满足时提交成功。
- [ ] 4.2 编写前端集成测试（若有 e2e 框架）或进行手动测试验收。
- [ ] 4.3 回归测试：确保原有复核流程不受影响。

---

### 四、技术风险与依赖

| 风险 | 缓解措施 |
|------|----------|
| 现有数据模型缺少 `context_completer_id` 字段 | 需与数据团队确认历史数据如何回溯填充，或者允许 NULL（若为 NULL 则跳过“自我复核”检查） |
| 前端可能存在多页面复用，按钮锁定逻辑可能在不同位置需要同步 | 封装成一个通用组件/函数，确保一致性 |
| 最低复核人数配置可能项目级/任务级不一致 | 在调研阶段明确配置继承规则，并在 1.1 中设计清晰接口 |
| 预检接口被频繁调用造成的性能压力 | 预热缓存（如 Redis）或限制调用频率，但初期可简单返回实时计算 |

---

### 五、交付物清单

1. **后端**  
   - `review_models.py` 的数据模型变更（如需要）  
   - `review_service.py` 中 `validate_cross_review` 函数  
   - `review_routes.py` 中修改的提交接口和新增的预检接口  
   - 单元测试文件（如 `tests/test_cross_review_block.py`）

2. **前端**  
   - 修改后的 `tasks.html` 静态页面  
   - 新增/修改的 JS 逻辑（负责状态检测、按钮锁定、错误提示）  

3. **文档**  
   - API 接口文档更新（Swagger）  
   - 简要的功能说明（置于项目 Wiki 或注释中）

---

### 六、计划排期建议

| 阶段 | 内容 | 估计工时 |
|------|------|----------|
| 调研 | 数据结构与流程确认 | 0.5 人日 |
| 后端开发 | 模型调整 + 校验 + 接口 | 1.5 人日 |
| 前端开发 | 按钮锁定 + 状态提示 | 1.0 人日 |
| 测试 | 单元+集成测试 | 1.0 人日 |
| 联调 & 验收 | 前后端联调，修 Bug | 0.5 人日 |
| **合计** | | **4.5 人日** |

> 该任务分解已充分考虑现有模块（`review_models/ service/routes`）的可扩展性，开发时请严格遵循现有代码风格和错误处理规范。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
