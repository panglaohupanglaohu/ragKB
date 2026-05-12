# 架构设计 — architect

任务: 可观测性集成：指纹遥测旁路、聚合链路trace ID关联、面板监控
步骤: architecture
Agent: build_architect

---

📋 任务: 21ef94ba-2b6
🤖 Agent: Architect (architect)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 Architect (architect)。
  请执行以下开发任务:
  
  你是系统架构师。请为以下任务设计技术方案:
  
  ## 任务
  可观测性集成：指纹遥测旁路、聚合链路trace ID关联、面板监控
  Architect, Developer
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/plaza-dark.html
  src/frontend/plaza-old.html
  src/frontend/plaza-wabisabi-v2.html
  src/frontend/plaza-wabisabi.html
  src/frontend/plaza.html
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
  src/backend/tests/test_models.py
  src/backend/tests/test_models.py.bak
  src/backend/tests/test_task_engine.py
  src/backend/tests/test_task_engine.py.bak
  src/backend/tests/test_team_manager.py
  src/backend/tests/test_team_manager.py.bak
  src/backend/agents/__init__.py
  src/backend/agents/ab_testing.py
  src/backend/agents/agent_loop.py
  src/backend/agents/agent_toolbox.py
  src/backend/agents/api.py
  src/backend/agents/chat_harness.py
  src/backend/agents/execution_registry.py
  src/backend/agents/hermes_research.py
  src/backend/agents/knowledge_base.py
  src/backend/agents/models.py
  src/backend/agents/plaza.py
  src/backend/agents/plaza_engine.py
  src/backend/agents/plaza_routes.py
  src/backend/agents/plaza_routes.py.bak
  src/backend/agents/plaza_store.py
  src/backend/agents/session_store.py
  src/backend/agents/skill_registry.py
  src/backend/agents/task_engine.py
  src/backend/agents/task_store.py
  src/backend/agents/team_manager.py
  src/backend/agents/team_store.py
  src/backend/agents/tool_executor.py
  src/backend/agents/tool_registry.py
  src/backend/agents/tts_routes.py
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/greeting.py
  src/backend/agents/skills/hello.py
  src/backend/scripts/__init__.py
  src/backend/scripts/validate_startup.py
  src/backend/scripts/validate_telemetry.py
  src/backend/monitoring/__init__.py
  src/backend/monitoring/collector.py
  src/backend/monitoring/models.py
  src/backend/monitoring/plaza_monitor.py
  src/backend/monitoring/plaza_monitor.py.bak
  src/backend/monitoring/sampler.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/evolution_executor.py
  src/backend/channels/marine_base.py
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
  src/docs/agent_handoffs/11e9b4b9-283_executor_started_20260509T074916.md
  src/docs/agent_handoffs/1356f045-d02_executor_started_20260509T073232.md
  src/docs/agent_handoffs/15554439-6aa_executor_started_20260509T073231.md
  src/docs/agent_handoffs/15a7e2eb-cd1_executor_started_20260509T073232.md
  src/docs/agent_handoffs/18d4b20f-c33_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1aed56ed-eda_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1cc2c0fb-90b_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
  src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
  src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
  src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
  src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
  src/docs/agent_handoffs/1d2d7607-8a3_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1e04fc38-6e9_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1f835c25-c0f_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1fd87e2e-962_executor_started_20260509T073232.md
  src/docs/agent_handoffs/21750a9a-2ff_executor_started_20260509T073231.md
  src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/2da416d2-cdf_executor_started_20260509T074916.md
  src/docs/agent_handoffs/32a3b057-166_executor_started_20260509T073232.md
  src/docs/agent_handoffs/34efc37e-3a1_executor_started_20260509T073231.md
  src/docs/agent_handoffs/35b91517-bfb_executor_started_20260509T073231.md
  src/docs/agent_handoffs/35f5eb68-2b7_executor_started_20260509T073232.md
  src/docs/agent_handoffs/38c98cf4-15b_executor_started_20260509T073231.md
  src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
  src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
  src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
  src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
  src/docs/agent_handoffs/39c0911d-173_executor_started_20260509T073232.md
  src/docs/agent_handoffs/3bde709e-2fe_architecture_20260507T031839.md
  src/docs/agent_handoffs/3bde709e-2fe_deploy_FAILED_20260507T033021.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T031910.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032452.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032630.md
  src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
  src/docs/agent_handoffs/3bde709e-2fe_pm_decompose_20260507T031529.md
  src/docs/agent_handoffs/3bde709e-2fe_research_20260507T031614.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T031936.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032523.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032706.md
  src/docs/agent_handoffs/3f9494e1-96d_executor_started_20260509T074916.md
  src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
  src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
  src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
  src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
  src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
  ... (共 508 个 src/ 文件)
  
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
  
  ### 文件: `src/backend/agents/models.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Agent Team Framework — Core Data Models.
  
  Inspired by Clawith platform architecture:
  - AgentTeam = Company (team-level resource sharing)
  - AgentProfile = Employee (individual agent with personality/skills/permissions)
  - ModelConfig = Model Pool entry
  - ToolDefinition = Tool catalog entry
  - SkillDefinition = Skill catalog entry
  """
  
  from __future__ import annotations
  
  import uuid
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from enum import Enum
  from typing import Any, Dict, List, Optional
  
  
  # ── Enums ──────────────────────────────────────────────────────────────────
  
  
  class AgentState(Enum):
      """Agent lifecycle states."""
  
      IDLE = "idle"
      WORKING = "working"
      PAUSED = "paused"
      ERROR = "error"
      STOPPED = "stopped"
  
  
  class ToolCategory(Enum):
      """Tool classification categories."""
  
      GENERAL = "general"
      BROWSER = "browser"
      CODE_EXECUTION = "code_execution"
      COMMUNICATION = "communication"
      FILE_OPERATION = "file_operation"
      TRIGGERS = "triggers"
      DISCOVERY = "discovery"
      DIGITAL_TWIN = "digital_twin"
      # Hermes-style tool categories
      WEB = "web"
      VISION = "vision"
      MEMORY = "memory"
      SKILLS = "skills"
      DELEGATION = "delegation"
  
  
  class SkillCategory(Enum):
      """Skill classification categories."""
  
      GENERAL = "general"
      DIGITAL_TWIN = "digital_twin"
      AUTOMATION = "automation"
      # Hermes-style skill categories
      RESEARCH = "research"
      DOMAIN_KNOWLEDGE = "domain_knowledge"
  
  
  class Visibility(Enum):
      """Visibility level for teams/agents."""
  
      PUBLIC = "public"
      PRIVATE = "private"
      INTERNAL = "internal"
  
  
  class AccessLevel(Enum):
      """Permission access levels."""
  
      READ = "read"
      WRITE = "write"
      ADMIN = "admin"
  
  
  class AgentTemplateType(Enum):
      """Predefined agent template types."""
  
      RESEARCHER = "researcher"
      DEVELOPER = "developer"
      ANALYST = "analyst"
      ENGINEER = "engineer"
      COORDINATOR = "coordinator"
      CUSTOM = "custom"
      # Hermes-style agent types
      HERMES_RESEARCHER = "hermes_researcher"
      HERMES_DEVELOPER = "hermes_developer"
      HERMES_CREATIVE = "hermes_creative"
  
  
  # ── Dataclasses ────────────────────────────────────────────────────────────
  
  
  @dataclass
  class ModelConfig:
      """LLM model configuration entry."""
  
      model_id: str = ""
      provider: str = "anthropic"
      name: str = "claude-sonnet-4-20250514"
      max_tokens: int = 65536
      temperature: float = 0.7
      is_default: bool = False
      enabled: bool = True
      api_key: str = ""
      api_base_url: str = ""
  
      def __post_init__(self) -> None:
          if not self.model_id:
              self.model_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "model_id": self.model_id,
              "provider": self.provider,
              "name": self.name,
              "max_tokens": self.max_tokens,
              "temperature": self.temperature,
              "is_default": self.is_default,
              "enabled": self.enabled,
              "api_key": ("****" + self.api_key[-4:]) if len(self.api_key) >= 4 else ("****" if self.api_key else ""),
              "api_base_url": self.api_base_url,
              "has_api_key": bool(self.api_key),
          }
  
  
  @dataclass
  class ToolDefinition:
      """Tool catalog entry."""
  
      tool_id: str = ""
      name: str = ""
      description: str = ""
      category: ToolCategory = ToolCategory.BROWSER
      enabled: bool = True
      requires_approval: bool = False
      parameters: Dict[str, Any] = field(default_factory=dict)
      icon: str = "🔧"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
  
      def __post_init__(self) -> None:
          if not self.tool_id:
              self.tool_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tool_id": self.tool_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "enabled": self.enabled,
              "requires_approval": self.requires_approval,
              "parameters": self.parameters,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
          }
  
  
  @dataclass
  class SkillDefinition:
      """Skill catalog entry."""
  
      skill_id: str = ""
      name: str = ""
      description: str = ""
      category: SkillCategory = SkillCategory.GENERAL
      required: bool = False
      enabled: bool = True
      icon: str = "⚡"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
      slug: str = ""
      required_tools: List[str] = field(default_factory=list)
      instructions: str = ""
  
      def __post_init__(self) -> None:
          if not self.skill_id:
              self.skill_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "skill_id": self.skill_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "required": self.required,
              "enabled": self.enabled,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
              "slug": self.slug,
              "required_tools": self.required_tools,
              "has_instructions": bool(self.instructions),
          }
  
  
  @dataclass
  class AgentPersonality:
      """Agent personality and behavior configuration."""
  
      tone: str = "professional"
      language: str = "zh-CN"
      expertise_areas: List[str] = field(default_factory=list)
      response_style: str = "concise"
      creativity: float = 0.5
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tone": self.tone,
              "language": self.language,
              "expertise_areas": self.expertise_areas,
              "response_style": self.response_style,
              "creativity": self.creativity,
          }
  
  
  @dataclass
  class ToolsetDistribution:
      """Hermes-style probabilistic toolset distribution.
  
      Each toolset has a % probability of being available per turn.
      Inspired by NousResearch/hermes-agent toolset_distributions.py.
      """
  
      name: str = "default"
      description: str = ""
      toolsets: Dict[str, int] = field(default_factory=dict)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "name": self.name,
              "description": self.description,
              "toolsets": self.toolsets,
          }
  
  
  @dataclass
  class HermesAgentConfig:
      """Hermes-style agent configuration — extends AgentProfile with
      learning loop, memory, skills, toolsets, and context management.
  
      Inspired by NousResearch/hermes-agent architecture:
      - Closed learning loop (skills from experience)
      - Persistent memory across sessions
      - Toolset distributions for probabilistic tool access
      - SOUL.md persona
      - Context files (AGENTS.md, HERMES.md)
      - Session search (cross-session recall)
      - Delegate/subagent parallelization
      """
  
      # Agent loop parameters
      max_iterations: int = 90
      iteration_budget: int = 90
  
      # Toolset distribution (Hermes-style probabilistic tool selection)
      toolset_distribution: ToolsetDistribution = field(
          default_factory=lambda: ToolsetDistribution(name="default")
      )
      enabled_toolsets: List[str] = field(default_factory=list)
      disabled_toolsets: List[str] = field(default_factory=list)
  
      # Memory & learning
      memory_enabled: bool = True
      session_search_enabled: bool = True
      skill_auto_create: bool = True
      soul_md: str = ""
      context_files: List[str] = field(default_factory=list)
  
      # Delegation
      can_delegate: bool = False
      max_subagents: int = 3
  
      # Platform
      platform: str = "cli"
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "max_iterations": self.max_iterations,
              "iteration_budget": self.iteration_budget,
              "toolset_distribution": self.toolset_distribution.to_dict(),
              "enabled_toolsets": self.enabled_toolsets,
              "disabled_toolsets": self.disabled_toolsets,
              "memory_enabled": self.memory_enabled,
              "session_search_enabled": self.session_search_enabled,
              "skill_auto_create": self.skill_auto_create,
              "soul_md": self.soul_md,
              "context_files": self.context_files,
              "can_delegate": self.can_delegate,
              "max_subagents": self.max_subagents,
              "platform": self.platform,
          }
  
  
  @dataclass
  class AgentPermission:
      """Agent access permission."""
  
      resource: str = ""
      access_level: AccessLevel = AccessLevel.READ
      channels: List[str] = field(default_factory=list)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "resource": self.resource,
              "access_level": self.access_level.value,
              "channels": self.channels,
          }
  
  
  @dataclass
  class AgentChannelConfig:
      """Channel subscription configuration for an agent."""
  
      channel_name: str = ""
      subscribe: bool = True
      publish: bool = False
      priority: int = 0
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "channel_name": self.channel_name,
              "subscribe": self.subscribe,
              "publish": self.publish,
              "priority": self.priority,
          }
  
  
  @dataclass
  class AgentProfile:
      """Individual agent profile — the Employee equivalent."""
  
      agent_id: str = ""
      name: str = ""
      role: str = ""
      description: str = ""
      template_type: AgentTemplateType = AgentTemplateType.CUSTOM
      state: AgentState = AgentState.IDLE
      model_id: str = ""
      system_prompt: str = ""
      personality: AgentPersonality = field(default_factory=AgentPersonality)
      permissions: List[AgentPermission] = field(default_factory=list)
      channels: List[AgentChannelConfig] = field(default_factory=list)
      tools: List[str] = field(default_factory=list)
      skills: List[str] = field(default_factory=list)
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
      # Hermes-style agent config (optional — non-None means Hermes mode)
      hermes_config: Optional[HermesAgentConfig] = None
  
      def __post_init__(self) -> None:
          if not self.agent_id:
              self.agent_id = str(uuid.uuid4())[:8]
  
      @property
      def is_hermes_agent(self) -> bool:
          return self.hermes_config is not None
  
      def to_dict(self) -> Dict[str, Any]:
          d = {
              "agent_id": self.agent_id,
              "name": self.name,
              "role": self.role,
              "description": self.description,
              "template_type": self.template_type.value,
              "state": self.state.value,
              "model_id": self.model_id,
              "system_prompt": self.system_prompt,
              "personality": self.personality.to_dict(),
              "permissions": [p.to_dict() for p in self.permissions],
              "channels": [c.to_dict() for c in self.channels],
              "tools": self.tools,
              "skills": self.skills,
              "metadata": self.metadata,
              "created_at": self.created_at,
              "is_hermes_agent": self.is_hermes_agent,
          }
          if self.hermes_config is not None:
              d["hermes_config"] = self.hermes_config.to_dict()
          return d
  
  
  @dataclass
  class AgentTeam:
      """Agent team — the Company equivalent. Holds shared resources."""
  
      team_id: str = ""
      name: str = ""
      description: str = ""
      visibility: Visibility = Visibility.PRIVATE
      agents: Dict[str, AgentProfile] = field(default_factory=dict)
      models: Dict[str, ModelConfig] = field(default_factory=dict)
      tools: Dict[str, ToolDefinition] = field(default_factory=dict)
      skills: Dict[str, SkillDefinition] = field(default_factory=dict)
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
  
      def __post_init__(self) -> None:
          if not self.team_id:
              self.team_id = str(uuid.uuid4())[:8]
  
      def add_agent(self, agent: AgentProfile) -> None:
          self.agents[agent.agent_id] = agent
  
      def remove_agent(self, agent_id: str) -> Optional[AgentProfile]:
          return self.agents.pop(agent_id, None)
  
      def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
          return self.agents.get(agent_id)
  
      def add_model(self, model: ModelConfig) -> None:
          self.models[model.model_id] = model
  
      def remove_model(self, model_id: str) -> Optional[ModelConfig]:
          return self.models.pop(model_id, None)
  
      def get_model(self, model_id: str) -> Optional[ModelConfig]:
          return self.models.get(model_id)
  
      def add_tool(self, tool: ToolDefinition) -> None:
          self.tools[tool.tool_id] = tool
  
      def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
          return self.tools.get(tool_id)
  
      def add_skill(self, skill: SkillDefinition) -> None:
          self.skills[skill.skill_id] = skill
  
      def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
          return self.skills.get(skill_id)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "team_id": self.team_id,
              "name": self.name,
              "description": self.description,
              "visibility": self.visibility.value,
              "agents": {k: v.to_dict() for k, v in self.agents.items()},
              "models": {k: v.to_dict() for k, v in self.models.items()},
              "tools": {k: v.to_dict() for k, v in self.tools.items()},
              "skills": {k: v.to_dict() for k, v in self.skills.items()},
              "metadata": self.metadata,
              "created_at": self.created_at,
          }
  
  ```
  
  ### 文件: `src/backend/agents/plaza_engine.py`
  ```py
  # -*- coding: utf-8 -*-
  """智能体广场引擎 — 讨论编排与多 Agent 协同.
  
  核心编排逻辑:
  1. Moderator（主持人壁龛）提出子话题，引导讨论方向
  2. 每轮: 各参与者按座席层级依次发言（内圈→中圈→外圈）
  3. Moderator 总结本轮关键观点
  4. 最终轮: Moderator 生成全局总结 + 关键结论
  
  消息通过 asyncio.Queue 实时推送给 SSE 订阅者。
  """
  
  from __future__ import annotations
  
  import asyncio
  import json
  import logging
  import re
  from datetime import datetime, timezone
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional
  from uuid import uuid4
  
  from .plaza import (
      Discussion, DiscussionStatus, NicheRole, Participant,
      Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
  )
  from .plaza_store import PlazaStore
  
  logger = logging.getLogger(__name__)
  
  _ROUND_SPEAKER_LIMIT = 5
  _EXCHANGES_PER_ROUND = 2  # 每轮内交锋次数
  _SPEAKERS_PER_EXCHANGE = 3  # 每次交锋参与人数
  _CORE_ROLE_PRIORITY = {
      "architect": 0,
      "researcher": 1,
      "developer": 2,
      "qa_engineer": 3,
      "qa": 3,
      "tester": 3,
      "devops": 4,
      "project_manager": 5,
      "documentation": 6,
  }
  
  
  class PlazaEngine:
      """广场引擎 — 管理广场、参与者和讨论编排."""
  
      def __init__(self):
          self._store = PlazaStore()
          self._plazas: Dict[str, Plaza] = self._store.load_all()
          self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
          self._discussion_locks: Dict[str, asyncio.Lock] = {}
          self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference
  
      def set_chat_fn(self, fn: Callable):
          """注入 ChatHarness.chat 异步函数."""
          self._chat_fn = fn
  
      def _get_agent_profile(self, agent_id: str):
          """从 TeamManager 获取完整 AgentProfile，用于注入个性."""
          try:
              from agents.api import _team_manager
              if _team_manager:
                  for team in _team_manager.list_teams():
                      agent = team.get_agent(agent_id)
                      if agent:
                          return agent
          except Exception:
              pass
          return None
  
      def _build_agent_system_prompt(self, participant: Participant) -> str:
          """根据 AgentProfile 构建有个性的 system prompt."""
          profile = self._get_agent_profile(participant.agent_id)
          if profile:
              expertise = "、".join(profile.personality.expertise_areas) if profile.personality.expertise_areas else ""
              traits = "、".join(profile.metadata.get("traits", [])) if profile.metadata else ""
              parts = [
                  f"你是 {profile.name}，职责: {profile.role}。",
                  f"专长: {expertise}。" if expertise else "",
                  f"性格特质: {traits}。" if traits else "",
                  f"你的工作方式: {profile.system_prompt}" if profile.system_prompt else "",
                  f"\n你正在一个智能体广场的讨论中发言。",
                  f"请用自然的方式说话，像一个真实的专业人士在开会讨论。",
                  f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。",
                  f"不需要客套寒暄，但要说人话，不要像电报一样压缩。",
              ]
              return "".join(p for p in parts if p)
          # 回退到基础信息
          return (
              f"你是 {participant.agent_name}，职责: {participant.role}。"
              f"你正在一个智能体广场的讨论中发言。"
              f"请用自然的方式说话，像一个真实的专业人士在开会讨论。"
              f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。"
          )
  
      # ── 广场 CRUD ──────────────────────────────────────────
  
      def create_plaza(self, name: str, description: str = "") -> Plaza:
          plaza = Plaza(name=name, description=description)
          self._plazas[plaza.id] = plaza
          self._store.save_plaza(plaza)
          logger.info(f"🏛️ 广场创建: {name} ({plaza.id})")
          return plaza
  
      def get_plaza(self, plaza_id: str) -> Optional[Plaza]:
          return self._plazas.get(plaza_id)
  
      def list_plazas(self) -> List[Plaza]:
          return list(self._plazas.values())
  
      def delete_plaza(self, plaza_id: str) -> bool:
          if plaza_id in self._plazas:
              del self._plazas[plaza_id]
              self._store.delete_plaza(plaza_id)
              return True
          return False
  
      # ── 参与者管理 ──────────────────────────────────────────
  
      def add_participant(
          self, plaza_id: str, agent_id: str, agent_name: str = "",
          role: str = "", team_id: str = "",
          seat_tier: SeatTier = SeatTier.MIDDLE,
          niche_role: NicheRole = NicheRole.OBSERVER,
      ) -> Optional[Participant]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          # 分配壁龛编号 (动态扩展)
          used_niches = {p.niche_index for p in plaza.participants.values() if p.niche_index >= 0}
          niche_index = len(used_niches)
          # 自动扩展壁龛数
          if niche_index >= plaza.niche_count:
              plaza.niche_count = niche_index + 1
          p = Participant(
              agent_id=agent_id, agent_name=agent_name, role=role,
              team_id=team_id, seat_tier=seat_tier, niche_role=niche_role,
              niche_index=niche_index,
          )
          plaza.participants[agent_id] = p
          self._store.save_plaza(plaza)
          logger.info(f"🪑 参与者加入广场 {plaza_id}: {agent_name} (壁龛 #{niche_index})")
          return p
  
      def remove_participant(self, plaza_id: str, agent_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if plaza and agent_id in plaza.participants:
              del plaza.participants[agent_id]
              self._store.save_plaza(plaza)
              return True
          return False
  
      # ── 讨论管理 ──────────────────────────────────────────
  
      def create_discussion(
          self, plaza_id: str, topic: str, description: str = "",
          moderator_agent_id: str = "", max_rounds: int = 5,
      ) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          disc = Discussion(
              plaza_id=plaza_id, topic=topic, description=description,
              moderator_agent_id=moderator_agent_id, max_rounds=max_rounds,
          )
          plaza.discussions[disc.id] = disc
          self._store.save_plaza(plaza)
          logger.info(f"💬 讨论创建: {topic[:40]} ({disc.id})")
          return disc
  
      def get_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          return plaza.discussions.get(discussion_id)
  
      def list_discussions(self, plaza_id: str) -> List[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return []
          return list(plaza.discussions.values())
  
      def delete_discussion(self, plaza_id: str, discussion_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if not plaza or discussion_id not in plaza.discussions:
              return False
          del plaza.discussions[discussion_id]
          self._sse_queues.pop(discussion_id, None)
          self._store.save_plaza(plaza)
          return True
  
      def reset_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          """重置已结束讨论，保留话题本身以便重新讨论。"""
          disc = self.get_discussion(plaza_id, discussion_id)
          if not disc:
              return None
          disc.status = DiscussionStatus.OPEN
          disc.current_round = 0
          disc.messages.clear()
          disc.summary = ""
          disc.key_conclusions.clear()
          disc.plan.clear()
          disc.assigned_team_id = ""
          disc.started_at = None
          disc.ended_at = None
          plaza = self._plazas.get(plaza_id)
          if plaza:
              self._store.save_plaza(plaza)
          return disc
  
      # ── SSE 订阅管理 ──────────────────────────────────────
  
      def subscribe(self, discussion_id: str) -> asyncio.Queue:
          q: asyncio.Queue = asyncio.Queue()
          self._sse_queues.setdefault(discussion_id, []).append(q)
          return q
  
      def unsubscribe(self, discussion_id: str, q: asyncio.Queue):
          qs = self._sse_queues.get(discussion_id, [])
          if q in qs:
              qs.remove(q)
  
      async def _broadcast(self, discussion_id: str, event: Dict[str, Any]):
          """向所有 SSE 订阅者推送事件."""
          for q in self._sse_queues.get(discussion_id, []):
              try:
                  q.put_nowait(event)
              except asyncio.QueueFull:
                  pass
  
      # ── 核心讨论编排 ──────────────────────────────────────
  
      async def run_discussion(
          self, plaza_id: str, discussion_id: str,
      ) -> Optional[Discussion]:
          """运行一场完整的广场讨论.
  
          编排流程 (向心结构):
          1. Moderator 开场: 阐述话题，提出第一轮子问题
          2. 每轮:
             a. 各参与者按座席层级依次发言 (内→中→外)
             b. Moderator 总结本轮观点
          3. 最终轮: Moderator 生成全局总结 + 关键结论
          """
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          disc = plaza.discussions.get(discussion_id)
          if not disc:
              return None
          if disc.status not in (DiscussionStatus.OPEN,):
              return disc
  
          disc.status = DiscussionStatus.IN_PROGRESS
          disc.started_at = datetime.now(timezone.utc).isoformat()
  
          # Give event loop a chance to process SSE client connections
          await asyncio.sleep(0.1)
  
          try:
              return await self._run_discussion_inner(plaza, disc)
          except Exception as e:
              logger.error(f"❌ 讨论运行失败 [{disc.id}]: {e}", exc_info=True)
              disc.status = DiscussionStatus.OPEN
              disc.started_at = None
              disc.current_round = 0
              await self._broadcast(disc.id, {
                  "type": "discussion_error",
                  "error": str(e),
              })
              self._store.save_plaza(plaza)
              return disc
  
      async def _run_discussion_inner(
          self, plaza: Plaza, disc: Discussion,
      ) -> Discussion:
          """讨论编排核心逻辑（由 run_discussion 包装调用）."""
          await self._broadcast(disc.id, {
              "type": "discussion_start",
              "discussion_id": disc.id,
              "topic": disc.topic,
          })
  
          participants = list(plaza.participants.values())
          moderator = None
          speakers = []
  
          moderator = self._resolve_moderator(plaza, disc, participants)
          speakers = self._sort_speakers(participants, moderator)
  
          if not self._chat_fn:
              # 无 LLM 时使用模拟回复
              await self._run_simulated(disc, moderator, speakers)
              return disc
  
          # ── 开场: Moderator 引导话题 ──
          opening_prompt = (
              f"你是本场讨论的议事长（主持人）。\n"
              f"讨论话题: 「{disc.topic}」\n"
              f"{f'话题描述: {disc.description}' if disc.description else ''}\n"
              f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n"
              f"参与者: {', '.join(p.agent_name or p.agent_id for p in speakers)}\n\n"
              f"请开场:\n"
              f"- 用 2-4 句话点明讨论的核心问题\n"
              f"- 直接围绕用户提出的话题展开，不要自行转换或重新解读话题\n"
              f"- 然后向参与者提出第一个需要讨论的具体问题\n"
              f"- 说人话，像一个项目经理在主持会议"
          )
          opening = await self._speak_with_lock(
              disc, moderator, opening_prompt, round_number=0,
              niche_role="moderator",
          )
  
          # ── 多轮讨论 (辩论式交锋) ──
          for round_num in range(1, disc.max_rounds + 1):
              disc.current_round = round_num
              await self._broadcast(disc.id, {
                  "type": "round_start", "round": round_num,
                  "max_rounds": disc.max_rounds,
              })
  
              round_speakers = self._select_round_speakers(speakers, round_num)
              # 每轮多次短交锋，模拟辩论赛节奏
              exchanges = _EXCHANGES_PER_ROUND if disc.max_rounds <= 2 else 2
              for ex_idx in range(exchanges):
                  # 轮转选人: 每次交锋选不同子集
                  ex_speakers = self._pick_exchange_speakers(
                      round_speakers, ex_idx, _SPEAKERS_PER_EXCHANGE,
                  )
                  for speaker in ex_speakers:
                      # 获取最近 5 条作为即时上下文 (短窗口促进针锋相对)
                      recent = self._format_recent(disc, limit=5)
                      speak_prompt = (
                          f"你正在参与关于「{disc.topic}」的团队讨论。\n"
                          f"你是 {speaker.agent_name}（{speaker.role}）。"
                          f"第 {round_num} 轮，第 {ex_idx+1} 次发言。\n\n"
                          f"刚才的讨论:\n{recent}\n\n"
                          f"发言要求:\n"
                          f"- 结合你的专业背景，给出有实质内容的观点或建议\n"
                          f"- 回应上面讨论中你认为重要的点，然后补充你的看法\n"
                          f"- 可以提出具体的方案、步骤、注意事项\n"
                          f"- 说 3-5 句话，100-200 字左右，不要太短也不要写论文\n"
                          f"- 像在开会发言一样自然表达，不要用列表和标题"
                      )
                      await self._speak_with_lock(
                          disc, speaker, speak_prompt, round_number=round_num,
                          niche_role=speaker.niche_role.value,
                      )
  
              # Moderator 收束本轮 (非最后一轮时)
              if round_num < disc.max_rounds:
                  summary_prompt = (
                      f"你是主持人。第 {round_num} 轮讨论已结束。\n\n"
                      f"本轮讨论:\n{self._format_round_messages(disc, round_num)}\n\n"
                      f"请小结本轮要点:\n"
                      f"- 总结大家达成的共识和仍有分歧的地方\n"
                      f"- 提出下一轮需要重点讨论的问题\n"
                      f"- 用 2-3 句话，自然表达"
                  )
                  await self._speak_with_lock(
                      disc, moderator, summary_prompt, round_number=round_num,
                      niche_role="moderator",
                  )
  
          # ── 最终总结 ──
          disc.status = DiscussionStatus.SUMMARIZING
          await self._broadcast(disc.id, {"type": "summarizing"})
  
          final_prompt = (
              f"你是议事长。关于「{disc.topic}」的讨论已经完成 {disc.max_rounds} 轮。\n"
              f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n\n"
              f"完整讨论记录:\n{self._format_history(disc)}\n\n"
              f"请生成可直接派发任务的技术型概要。核心原则——有取舍、有权重:\n"
              f"- build/构建/开发/架构/部署相关发言 = 权重最高(P0级)，这些人要真正动手执行\n"
              f"- 测试/QA/安全相关 = 中等权重(P1级)，是质量门禁\n"
              f"- 能耗/外围优化/观察类 = 低权重(P2级)，仅作为补充参考，绝不挤占主篇幅\n"
              f"- 如果能耗建议不影响主目标上线，就放到最后1行带过\n\n"
              f"输出结构 (严格按此格式，不要自由发挥):\n"
              f"## 技术概要\n"
              f"4-6 句写清: 主目标、核心方案、关键约束、最大风险、首要动作\n"
              f"必须是接到这份概要的人能直接开工的技术描述\n\n"
              f"## 加权结论 (P0→P1→P2)\n"
              f"- [P0] 结论 |
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 可观测性集成：指纹遥测旁路、聚合链路trace ID关联、面板监控
  步骤: pm_decompose
  📋 任务: 21ef94ba-2b6
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  可观测性集成：指纹遥测旁路、聚合链路trace ID关联、面板监控
  Architect, Developer
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/tests/conftest.py`
  ### 文件: `src/backend/tests/test_agent_toolbox.py`
  **变更文件 (3):**
    - `src/backend/agents/agent_loop.py`
    - `src/backend/agents/team_manager.py`
    - `src/backend/agents/ab_testing.py`
  **子任务拆解:**
    - *任务**：可观测性集成——指纹遥测旁路、聚合链路 trace ID 关联、面板监控  
    - *角色**：Architect, Developer  
    - *日期**：2026-05-09  
    - *状态**：已规划  
    - **指纹遥测旁路**：在不干扰主业务流程的前提下，异步采集 Agent 行为指纹（突变率、升级异常等），用于事后分析与 A/B 测试反馈。
    - **聚合链路 Trace ID 关联**：为多 Agent 协作（Plaza 讨论、Handoff、Team 调度）统一注入 Trace ID，实现全链路追踪与因果关系梳理。
    - **面板监控**：为前端提供实时指标看板，展示遥测指标与 Trace 拓扑。
    - `src/backend/monitoring/` 目录：
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 可观测性集成：指纹遥测旁路、聚合链路trace ID关联、面板监控
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: 21ef94ba-2b6
  🤖 Agent: Researcher (researcher)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 Researcher (researcher)。
    请执行以下开发任务:
    
    你是技术研究员。请对以下任务进行技术调研:
    
    ## 任务
    可观测性集成：指纹遥测旁路、聚合链路trace ID关联、面板监控
    Architect, Developer
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
    src/frontend/index.html
    src/frontend/login.html
    src/frontend/plaza-dark.html
    src/frontend/plaza-old.html
    src/frontend/plaza-wabisabi-v2.html
    src/frontend/plaza-wabisabi.html
    src/frontend/plaza.html
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
    src/backend/tests/test_models.py
    src/backend/tests/test_models.py.bak
    src/backend/tests/test_task_engine.py
    src/backend/tests/test_task_engine.py.bak
    src/backend/tests/test_team_manager.py
    src/backend/tests/test_team_manager.py.bak
    src/backend/agents/__init__.py
    src/backend/agents/ab_testing.py
    src/backend/agents/agent_loop.py
    src/backend/agents/agent_toolbox.py
    src/backend/agents/api.py
    src/backend/agents/chat_harness.py
    src/backend/agents/execution_registry.py
    src/backend/agents/hermes_research.py
    src/backend/agents/knowledge_base.py
    src/backend/agents/models.py
    src/backend/agents/plaza.py
    src/backend/agents/plaza_engine.py
    src/backend/agents/plaza_routes.py
    src/backend/agents/plaza_routes.py.bak
    src/backend/agents/plaza_store.py
    src/backend/agents/session_store.py
    src/backend/agents/skill_registry.py
    src/backend/agents/task_engine.py
    src/backend/agents/task_store.py
    src/backend/agents/team_manager.py
    src/backend/agents/team_store.py
    src/backend/agents/tool_executor.py
    src/backend/agents/tool_registry.py
    src/backend/agents/tts_routes.py
    src/backend/agents/teams/__init__.py
    src/backend/agents/teams/ai_coding_team.py
    src/backend/agents/teams/build_team.py
    src/backend/agents/teams/energy_team.py
    src/backend/agents/skills/__init__.py
    src/backend/agents/skills/greeting.py
    src/backend/agents/skills/hello.py
    src/backend/scripts/__init__.py
    src/backend/scripts/validate_startup.py
    src/backend/scripts/validate_telemetry.py
    src/backend/monitoring/__init__.py
    src/backend/monitoring/collector.py
    src/backend/monitoring/models.py
    src/backend/monitoring/plaza_monitor.py
    src/backend/monitoring/plaza_monitor.py.bak
    src/backend/monitoring/sampler.py
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/evolution_executor.py
    src/backend/channels/marine_base.py
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
    src/docs/agent_handoffs/11e9b4b9-283_executor_started_20260509T074916.md
    src/docs/agent_handoffs/1356f045-d02_executor_started_20260509T073232.md
    src/docs/agent_handoffs/15554439-6aa_executor_started_20260509T073231.md
    src/docs/agent_handoffs/15a7e2eb-cd1_executor_started_20260509T073232.md
    src/docs/agent_handoffs/18d4b20f-c33_executor_started_20260509T073231.md
    src/docs/agent_handoffs/1aed56ed-eda_executor_started_20260509T073232.md
    src/docs/agent_handoffs/1cc2c0fb-90b_executor_started_20260509T073232.md
    src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
    src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
    src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
    src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
    src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
    src/docs/agent_handoffs/1d2d7607-8a3_executor_started_20260509T073231.md
    src/docs/agent_handoffs/1e04fc38-6e9_executor_started_20260509T073231.md
    src/docs/agent_handoffs/1f835c25-c0f_executor_started_20260509T073232.md
    src/docs/agent_handoffs/1fd87e2e-962_executor_started_20260509T073232.md
    src/docs/agent_handoffs/21750a9a-2ff_executor_started_20260509T073231.md
    src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
    src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
    src/docs/agent_handoffs/2da416d2-cdf_executor_started_20260509T074916.md
    src/docs/agent_handoffs/32a3b057-166_executor_started_20260509T073232.md
    src/docs/agent_handoffs/34efc37e-3a1_executor_started_20260509T073231.md
    src/docs/agent_handoffs/35b91517-bfb_executor_started_20260509T073231.md
    src/docs/agent_handoffs/35f5eb68-2b7_executor_started_20260509T073232.md
    src/docs/agent_handoffs/38c98cf4-15b_executor_started_20260509T073231.md
    src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
    src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
    src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
    src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
    src/docs/agent_handoffs/39c0911d-173_executor_started_20260509T073232.md
    src/docs/agent_handoffs/3bde709e-2fe_architecture_20260507T031839.md
    src/docs/agent_handoffs/3bde709e-2fe_deploy_FAILED_20260507T033021.md
    src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T031910.md
    src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032452.md
    src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032630.md
    src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
    src/docs/agent_handoffs/3bde709e-2fe_pm_decompose_20260507T031529.md
    src/docs/agent_handoffs/3bde709e-2fe_research_20260507T031614.md
    src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T031936.md
    src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032523.md
    src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032706.md
    src/docs/agent_handoffs/3f9494e1-96d_executor_started_20260509T074916.md
    src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
    src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
    src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
    src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
    src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
    ... (共 508 个 src/ 文件)
    
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
    
    ### 文件: `src/backend/agents/models.py`
    ```py
    # -*- coding: utf-8 -*-
    """AgentsGroup2026 Agent Team Framework — Core Data Models.
    
    Inspired by Clawith platform architecture:
    - AgentTeam = Company (team-level resource sharing)
    - AgentProfile = Employee (individual agent with personality/skills/permissions)
    - ModelConfig = Model Pool entry
    - ToolDefinition = Tool catalog entry
    - SkillDefinition = Skill catalog entry
    """
    
    from __future__ import annotations
    
    import uuid
    from dataclasses import dataclass, field
    from datetime import datetime, timezone
    from enum import Enum
    from typing import Any, Dict, List, Optional
    
    
    # ── Enums ──────────────────────────────────────────────────────────────────
    
    
    class AgentState(Enum):
        """Agent lifecycle states."""
    
        IDLE = "idle"
        WORKING = "working"
        PAUSED = "paused"
        ERROR = "error"
        STOPPED = "stopped"
    
    
    class ToolCategory(Enum):
        """Tool classification categories."""
    
        GENERAL = "general"
        BROWSER = "browser"
        CODE_EXECUTION = "code_execution"
        COMMUNICATION = "communication"
        FILE_OPERATION = "file_operation"
        TRIGGERS = "triggers"
        DISCOVERY = "discovery"
        DIGITAL_TWIN = "digital_twin"
        # Hermes-style tool categories
        WEB = "web"
        VISION = "vision"
        MEMORY = "memory"
        SKILLS = "skills"
        DELEGATION = "delegation"
    
    
    class SkillCategory(Enum):
        """Skill classification categories."""
    
        GENERAL = "general"
        DIGITAL_TWIN = "digital_twin"
        AUTOMATION = "automation"
        # Hermes-style skill categories
        RESEARCH = "research"
        DOMAIN_KNOWLEDGE = "domain_knowledge"
    
    
    class Visibility(Enum):
        """Visibility level for teams/agents."""
    
        PUBLIC = "public"
        PRIVATE = "private"
        INTERNAL = "internal"
    
    
    class AccessLevel(Enum):
        """Permission access levels."""
    
        READ = "read"
        WRITE = "write"
        ADMIN = "admin"
    
    
    class AgentTemplateType(Enum):
        """Predefined agent template types."""
    
        RESEARCHER = "researcher"
        DEVELOPER = "developer"
        ANALYST = "analyst"
        ENGINEER = "engineer"
        COORDINATOR = "coordinator"
        CUSTOM = "custom"
        # Hermes-style agent types
        HERMES_RESEARCHER = "hermes_researcher"
        HERMES_DEVELOPER = "hermes_developer"
        HERMES_CREATIVE = "hermes_creative"
    
    
    # ── Dataclasses ────────────────────────────────────────────────────────────
    
    
    @dataclass
    class ModelConfig:
        """LLM model configuration entry."""
    
        model_id: str = ""
        provider: str = "anthropic"
        name: str = "claude-sonnet-4-20250514"
        max_tokens: int = 65536
        temperature: float = 0.7
        is_default: bool = False
        enabled: bool = True
        api_key: str = ""
        api_base_url: str = ""
    
        def __post_init__(self) -> None:
            if not self.model_id:
                self.model_id = str(uuid.uuid4())[:8]
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "model_id": self.model_id,
                "provider": self.provider,
                "name": self.name,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "is_default": self.is_default,
                "enabled": self.enabled,
                "api_key": ("****" + self.api_key[-4:]) if len(self.api_key) >= 4 else ("****" if self.api_key else ""),
                "api_base_url": self.api_base_url,
                "has_api_key": bool(self.api_key),
            }
    
    
    @dataclass
    class ToolDefinition:
        """Tool catalog entry."""
    
        tool_id: str = ""
        name: str = ""
        description: str = ""
        category: ToolCategory = ToolCategory.BROWSER
        enabled: bool = True
        requires_approval: bool = False
        parameters: Dict[str, Any] = field(default_factory=dict)
        icon: str = "🔧"
        config_schema: Dict[str, Any] = field(default_factory=dict)
        config: Dict[str, Any] = field(default_factory=dict)
        is_default: bool = False
        source: str = "builtin"
    
        def __post_init__(self) -> None:
            if not self.tool_id:
                self.tool_id = str(uuid.uuid4())[:8]
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "tool_id": self.tool_id,
                "name": self.name,
                "description": self.description,
                "category": self.category.value,
                "enabled": self.enabled,
                "requires_approval": self.requires_approval,
                "parameters": self.parameters,
                "icon": self.icon,
                "config_schema": self.config_schema,
                "config": self.config,
                "is_default": self.is_default,
                "source": self.source,
            }
    
    
    @dataclass
    class SkillDefinition:
        """Skill catalog entry."""
    
        skill_id: str = ""
        name: str = ""
        description: str = ""
        category: SkillCategory = SkillCategory.GENERAL
        required: bool = False
        enabled: bool = True
        icon: str = "⚡"
        config_schema: Dict[str, Any] = field(default_factory=dict)
        config: Dict[str, Any] = field(default_factory=dict)
        is_default: bool = False
        source: str = "builtin"
        slug: str = ""
        required_tools: List[str] = field(default_factory=list)
        instructions: str = ""
    
        def __post_init__(self) -> None:
            if not self.skill_id:
                self.skill_id = str(uuid.uuid4())[:8]
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "skill_id": self.skill_id,
                "name": self.name,
                "description": self.description,
                "category": self.category.value,
                "required": self.required,
       
  ...(截断)
  
  ## ⚠️ 重要提示
  上方 📂 项目上下文 包含了任务相关的实际源文件。
  请基于这些文件设计方案，不要引用不存在的文件。
  
  ## 要求
  1. 基于调研结果和实际源码，设计详细技术方案
  2. 明确指出需要修改的文件和具体修改内容
  3. 定义接口规范（如有新增 API）
  4. 为开发工程师提供逐步实施指南
  
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

# 可观测性集成：技术架构设计方案

## 1. 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     前端监控面板 (Frontend)                     │
│  monitors.html / plaza-wabisabi-v2.html 嵌入                   │
│  ├─ 实时指标卡片 (指纹遥测)                                    │
│  ├─ Trace 拓扑图 (vis-network)                                 │
│  └─ SSE/WS 数据流                                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │ SSE / REST
┌──────────────────────▼──────────────────────────────────────────┐
│                  FastAPI 主应用 (main.py)                       │
│  /api/monitoring/*    /api/traces/*    /api/telemetry/stream   │
└──────┬───────────────────────────────┬──────────────────────────┘
       │                               │
┌──────▼──────┐                 ┌──────▼──────────────────────────┐
│ Trace 引擎   │                 │ 遥测收集器 (Telemetry Collector) │
│ - TraceContext│◄────────────────┤  - 周期性采样 AB 指标           │
│ - Span 管理  │ 异步注入         │  - 旁路指纹突变率等             │
│ - 存储/查询  │                 │  - 写入 monitoring/models 存储   │
└──────┬──────┘                 └─────────────────────────────────┘
       │ 传播 (ContextVar / 参数)
┌──────▼──────────────────────────────────────────────────────────┐
│                  Agent 核心执行层                               │
│  agent_loop.py    team_manager.py   plaza_engine.py            │
│  - 入口注入 trace_id / span                                    │
│  - LLM 调用、工具调用自动埋点                                  │
│  - 异常/状态变更记录                                           │
└─────────────────────────────────────────────────────────────────┘
```

设计原则：
- **低侵入**：通过 `contextvars.ContextVar` 传播 trace 上下文，避免大规模函数签名改动。
- **异步旁路**：遥测采集使用独立线程/任务，通过现有 `monitoring/` 模块的队列写入，不阻塞 Agent 主流程。
- **复用现有基础设施**：`monitoring/collector.py`、`monitoring/models.py`、`monitoring/sampler.py` 已有框架，直接扩展。

## 2. 详细部件设计

### 2.1 指纹遥测旁路

**目标**：采集 Agent 行为指纹（突变率、升级异常、EWMA 指标等），供 A/B 测试分析和告警。

**采集点**：
- `agent_loop.py` 每次迭代结束
- `team_manager.py` 任务下发/完成
- `ab_testing.py` 中 ABTestMetrics 计算时主动推送
- `plaza_engine.py` 讨论结束

**设计**：
- 扩展 `src/backend/monitoring/models.py`，新增 `TelemetryRecord` 和 `FingerprintSnapshot` 数据类。
- 扩展 `src/backend/monitoring/collector.py`，增加异步推送方法 `push_telemetry(record)`。
- 在关键代码位置调用 `collector.push_telemetry()`（旁路调用，异常不会影响主流程）。

### 2.2 聚合链路 Trace ID 关联

**目标**：为多 Agent 协作（任务、Handoff、Plaza 讨论）统一注入 Trace ID，实现全链路追踪。

**设计**：
- 新增 `src/backend/monitoring/trace.py`，提供 `TraceContext` 和 `Span` 类。
- 使用 Python `contextvars.ContextVar` 存储当前 trace_id 和 span_id。
- 在 `agent_loop.py` 任务入口、`team_manager.py` 任务委托、`plaza_engine.py` 讨论入口创建根 Span。
- 在 LLM 调用（`chat_harness.py`）、工具调用（`agent_toolbox.py` 各工具）自动创建子 Span。
- 所有 Span ��过队列写入内存存储或日志文件（可配置），供查询。

### 2.3 面板监控

**目标**：前端实时展示遥测指标、Trace 拓扑、Agent 状态。

**设计**：
- 新增 FastAPI 路由 `src/backend/agents/monitor_routes.py`，提供 REST 和 SSE 端点。
- 前端在现有 `plaza-wabisabi-v2.html` 中增加“监控”标签页，或创建独立 `monitors.html`。
- 使用 `vis-network` 库绘制 Trace 拓扑图。
- 指标卡片展示指纹突变率、EWMA 阈值突破次数等。

## 3. 数据模型扩展

### 3.1 新增 Trace 模型 (`src/backend/monitoring/trace_models.py`)

```python
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

@dataclass
class Span:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str          # e.g. "agent_loop", "llm_call", "tool_run"
    agent_id: Optional[str]
    team_id: Optional[str]
    start_time: str
    end_time: Optional[str]
    tags: Dict[str, Any]         # e.g. {"model": "deepseek-v4", "tool": "read_file"}
    logs: List[Dict[str, Any]]

@dataclass
class Trace:
    trace_id: str
    root_span_id: str
    spans: Dict[str, Span] = field(default_factory=dict)
```

### 3.2 遥测记录模型

在 `monitoring/models.py` 中增加：

```python
@dataclass
class TelemetryRecord:
    """一次遥测采样"""
    agent_id: str
    timestamp: str
    # 指纹指标
    fingerprint_mutation_rate: float
    anomaly_propagation_depth: float
    false_upgrade_rate: float
    # EWMA 状态
    ewma_breached: bool
    ewma_current_zscore: float
    # 系统指标
    active_threads: int
    memory_usage_mb: float
    # 关联 trace
    trace_id: str
```

## 4. 接口规范

### 4.1 REST API

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/monitoring/telemetry/recent?agent_id=...&limit=20` | 获取最近的遥测记录 |
| `GET` | `/api/monitoring/traces/recent?limit=10` | 获取最近的 Trace 列表 |
| `GET` | `/api/monitoring/traces/{trace_id}` | 获取完整 Trace（含所有 Span） |
| `GET` | `/api/monitoring/telemetry/stream` | SSE 流，推送实时遥测事件 |

### 4.2 SSE 事件格式

```json
{
  "event": "telemetry",
  "data": {
    "agent_id": "...",
    "fingerprint_mutation_rate": 0.02,
    "trace_id": "..."
  }
}
```

## 5. 需要修改/新增的文件

### 后端（Python）

| 文件 | 修改内容 |
|------|----------|
| `src/backend/monitoring/__init__.py` | 导出新模块 |
| `src/backend/monitoring/trace.py` | **新增** — TraceContext、Span 管理、存储 |
| `src/backend/monitoring/trace_models.py` | **新增** — Span/Trace 数据类 |
| `src/backend/monitoring/models.py` | 增加 `TelemetryRecord` 等 |
| `src/backend/monitoring/collector.py` | 增加 `push_telemetry` 方法，集成队列 |
| `src/backend/monitoring/plaza_monitor.py` | 增加讨论 Trace 注入 |
| `src/backend/agents/monitor_routes.py` | **新增** — 遥测/Trace API 路由 |
| `src/backend/agents/agent_loop.py` | 入口创建 Trace/Span，采集遥测 |
| `src/backend/agents/team_manager.py` | 任务委派时传播 Trace |
| `src/backend/agents/plaza_engine.py` | 讨论入口/发言创建 Span |
| `src/backend/agents/chat_harness.py` | LLM 调用埋点子 Span |
| `src/backend/agents/agent_toolbox.py` | 工具调用埋点子 Span |
| `src/backend/main.py` | 注册 `/api/monitoring` 路由 |

### 前端（HTML/JS）

| 文件 | 修改内容 |
|------|----------|
| `src/frontend/monitors.html` | **新增** — 独立监控面板 |
| `src/frontend/plaza-wabisabi-v2.html` | 增加“监控”标签页（可选） |
| `src/frontend/js/monitoring.js` | **新增** — 监控前端逻辑（SSE、图表） |
| `src/frontend/css/ws-theme-bridge.css` | 增加监控面板样式 |

## 6. 逐步实施指南

### 步骤 1: 基础设施

1. 创建 `src/backend/monitoring/trace_models.py`，定义 `Span`, `Trace` 数据类。
2. 创建 `src/backend/monitoring/trace.py`：
   - 实现 `TraceContext`：使用 `contextvars.ContextVar`。
   - 实现 `SpanManager`：内存存储最近 1000 个 Trace，提供 `start_span()`, `end_span()`, `get_trace()`。
   - 提供快捷函数 `get_current_trace_context()`。
3. 扩展 `monitoring/models.py`：添加 `TelemetryRecord`。

### 步骤 2: 埋点注入

1. **agent_loop.py**：
   - 在 `run_task()` 入口调用 `SpanManager.start_span()` 创建根 Span。
   - 在每次迭代结束时调用 `collector.push_telemetry()` 采集指标。
   - 使用 `try-finally` 确保 Span 结束。
2. **chat_harness.py**：
   - 在 `call_llm()` 内创建子 Span（名称 `"llm_call"`），并记录 model、token 数。
3. **agent_toolbox.py**：
   - 增加装饰器 `@traced_span(name="tool_read_file")`，自动创建子 Span。
   - 或者手动在 `dispatch_tool_call()` 内包裹上下文。
4. **team_manager.py**：
   - 任务委派时，将当前 trace_id 作为参数传递给子 Agent。
5. **plaza_engine.py**：
   - `create_discussion()` 时启动一个 Trace。
   - 每条发言创建子 Span。

### 步骤 3: 遥测采集激活

1. 扩展 `monitoring/collector.py`：
   - 添加内存环形缓冲区（collections.deque）存储遥测。
   - `push_telemetry(record)` 写入缓冲区。
2. 在 `agent_loop.py`、`team_manager.py` 中调用该推送方法。
3. 确保所有推送都是 try-catch 包装，异常只记录日志。

### 步骤 4: API 路由

1. 创建 `src/backend/agents/monitor_routes.py`：
   - 注册路由 `GET /api/monitoring/telemetry/recent`
   - `GET /api/monitoring/traces/recent`
   - `GET /api/monitoring/traces/{trace_id}`
   - `GET /api/monitoring/telemetry/stream` (SSE)
2. 在 `main.py` 引入并挂载路由。

### 步骤 5: 前端面板

1. 创建 `src/frontend/monitors.html`，基于 Bootstrap + vis.js。
2. 布局：
   - 顶部指标卡片（指纹突变率、EWMA 状态）。
   - 中间 Trace 时间线/拓扑图。
3. 使用 EventSource 连接 `/api/monitoring/telemetry/stream`。
4. 可选：在 plaza-wabisabi-v2.html 中通过 iframe 或 tab 集成。

### 步骤 6: 测试与验证

1. 编写单元测试 `test_monitoring.py`：
   - 验证 Trace 创建、传播、存储。
   - 验证遥测记录推送。
2. 启动系统，模拟 Agent 任务，检查 `/api/monitoring/telemetry/recent` 返回数据。
3. 前端页面连接查看。

## 7. 关键注意事项

- **性能**：Span 存储使用内存映射或固定大小缓冲区，避免无限增长；遥测推送异步。
- **兼容性**：所有修改保持向后兼容，原有 `monitoring/` 模块接口不变。
- **安全性**：监控 API 不暴露敏感信息（API key 等）。
- **前端依赖**：建议使用 CDN 引入 `vis-network`（或本地打包），避免额外构建步骤。

---

该方案基于现有代码基础，改动最小，风险可控。下一步请 Developer 按步骤执行。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
