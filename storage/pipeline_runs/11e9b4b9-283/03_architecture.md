# 架构设计 — architect

任务: 开发可选的异步相似度归并插件：支持用户自定义合并规则，独立部署
步骤: architecture
Agent: build_architect

---

📋 任务: 11e9b4b9-283
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
  开发可选的异步相似度归并插件：支持用户自定义合并规则，独立部署
  Developer
  
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
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
  ... (共 506 个 src/ 文件)
  
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
                  # treat as a graceful early stop instead of hard failure.
                  if self.files_changed or self.summary:
                      logger.info(
                          "[AgentLoop] Partial progress (%d files, %d chars summary) — "
                          "returning partial success",
                          len(self.files_changed), len(self.summary),
                      )
                      self._emit("loop_end", {"reason": "network_error_partial", "iteration": it})
                      return {
                          "ok": True, "error": str(e),
                          "summary": self.summary or f"(network error after {it} turns)",
                          "files_changed": self.files_changed,
                          "iterations": it, "log": self.tool_call_log,
                      }
                  return {
                      "ok": False, "error": str(e),
                      "summary": self.summary, "files_changed": self.files_changed,
                      "iterations": it, "log": self.tool_call_log,
                  }
  
              choice = (resp.get("choices") or [{}])[0]
              msg = choice.get("message", {}) or {}
              content = msg.get("content") or ""
              reasoning_content = msg.get("reasoning_content")
              tool_calls = msg.get("tool_calls") or []
              finish_reason = choice.get("finish_reason", "")
  
              self._emit("model_turn", {
                  "iteration": it,
                  "elapsed": round(time.time() - t0, 2),
                  "content_chars": len(content),
                  "tool_call_count": len(tool_calls),
                  "finish_reason": finish_reason,
              })
  
              # Append assistant turn (preserve reasoning_content for DeepSeek thinking mode)
              assistant_msg: Dict[str, Any] = {"role": "assistant", "content": content}
              if reasoning_content is not None:
                  assistant_msg["reasoning_content"] = reasoning_content
              if tool_calls:
                  assistant_msg["tool_calls"] = tool_calls
              self.messages.append(assistant_msg)
  
              # No tool calls → model is done talking
              if not tool_calls:
                  if not self.summary and content:
                      self.summary = content[:1000]
                  self._emit("loop_end", {"reason": "no_tool_call", "iteration": it})
                  return {
                      "ok": True, "summary": self.summary,
                      "files_changed": self.files_changed,
                      "iterations": it + 1, "log": self.tool_call_log,
                      "final_message": content,
                  }
  
              # Process each tool call
              finished = False
              for tc in tool_calls:
                  tc_id = tc.get("id", "")
                  fn = tc.get("function", {}) or {}
                  name = fn.get("name", "")
                  args_raw = fn.get("arguments", "") or "{}"
                  self._emit("tool_call", {"name": name, "args": args_raw[:500]})
  
                  if name == "finish":
                      try:
                          a = json.loads(args_raw or "{}")
                          self.summary = a.get("summary", "")
                          for fc in a.get("files_changed") or []:
                              if fc not in self.files_changed:
                                  self.files_changed.append(fc)
                      except Exception:
                          self.summary = args_raw[:500]
                      self.messages.append({
                          "role": "tool", "tool_call_id": tc_id, "name": name,
                          "content": json.dumps({"ok": True, "ack": "finished"}),
                      })
                      self.tool_call_log.append({"name": name, "args": args_raw, "ok": True})
                      finished = True
                      continue
  
                  result = dispatch_tool_call(name, args_raw)
                  # Track writes
                  if name in ("write_file", "patch_file") and result.get("ok"):
                      try:
                          a = json.loads(args_raw or "{}")
                          path = a.get("path", "")
                          if path and path not in self.files_changed:
                              self.files_changed.append(path)
                      except Exception:
                          pass
  
                  self.tool_call_log.append({
                      "name": name, "args": args_raw[:1000],
                      "ok": bool(result.get("ok")),
                      "summary": self._summarize_result(name, result),
                  })
                  self._emit("tool_result", {
                      "name": name, "ok": bool(result.get("ok")),
                      "summary": self.tool_call_log[-1]["summary"],
                  })
                  self.messages.append({
                      "role": "tool", "tool_call_id": tc_id, "name": name,
                      "content": json.dumps(result, ensure_ascii=False)[:32_000],
                  })
  
              if finished:
                  self._emit("loop_end", {"reason": "finish_called", "iteration": it})
                  return {
                      "ok": True, "summary": self.summary,
                      "files_changed": self.files_changed,
                      "iterations": it + 1, "log": self.tool_call_log,
                  }
  
          # Hit iteration cap
          # ── Safeguard 3: partial success if agent produced useful work ──
          # For QA/review agents that don't write files, check tool_call_log too
          has_work = (
              self.files_changed
              or self.summary
              or len(self.tool_call_log) >= 3  # agent did meaningful tool exploration
          )
          if has_work:
              # Auto-generate summary from tool log if agent didn't provide one
              if not self.summary and self.tool_call_log:
                  tool_names = [t["name"] for t in self.tool_call_log]
                  self.summary = (
                      f"(auto) 在 {self.max_iterations} 轮内完成了 {len(self.tool_call_log)} 个工具调用 "
                      f"({', '.join(set(tool_names))}), 修改 {len(self.files_changed)} 个文件。"
                      f" 验证结论: PASS (迭代上限自动通过)"
                  )
              logger.info(
                  "[AgentLoop] Iteration cap hit but agent produced work "
                  "(%d files, %d chars summary) — treating as partial success",
                  len(self.files_changed), len(self.summary),
              )
              self._emit("loop_end", {"reason": "iteration_cap_partial", "iteration": self.max_iterations})
              return {
                  "ok": True,
                  "error": f"iteration cap hit ({self.max_iterations}) — partial result",
                  "summary": self.summary or f"(completed {len(self.files_changed)} file changes before cap)",
                  "files_changed": self.files_changed,
                  "iterations": self.max_iterations, "log": self.tool_call_log,
              }
          self._emit("loop_end", {"reason": "iteration_cap", "iteration": self.max_iterations})
          return {
              "ok": False, "error": f"iteration cap hit ({self.max_iterations})",
              "summary": self.summary, "files_changed": self.files_changed,
              "iterations": self.max_iterations, "log": self.tool_call_log,
          }
  
      def _summarize_result(self, name: str, result: Dict[str, Any]) -> str:
          if not result.get("ok"):
              return f"FAIL: {result.get('error','')[:120]}"
          if name == "read_file":
              return f"{result.get('total_lines', '?')} lines, {len(result.get('content',''))} chars"
          if name == "grep":
              return f"{len(result.get('hits', []))} hits"
          if name == "list_files":
              return f"{len(result.get('files', []))} files"
          if name in ("write_file", "patch_file"):
              return f"{result.get('bytes', result.get('new_bytes', 0))} bytes"
          if name in ("run_python", "run_pytest"):
      
  ```
  
  ### 文件: `src/backend/agents/agent_toolbox.py`
  ```py
  """AgentToolbox — function-calling tools for code-aware agents.
  
  Gives Developer / QA agents the ability to read, grep, write, and execute code
  in the project so they don't have to hallucinate file contents.
  
  All tool calls are scoped to the project root and write operations are
  restricted to a safe allowlist (src/, tests/, docs/, config/, public/).
  
  Each tool returns a JSON-serializable dict suitable for OpenAI/DeepSeek
  function-calling protocol.
  """
  from __future__ import annotations
  
  import json
  import logging
  import os
  import re
  import shlex
  import subprocess
  import time
  from pathlib import Path
  from typing import Any, Dict, List, Optional, Tuple
  
  logger = logging.getLogger("AgentToolbox")
  
  PROJECT_ROOT = Path(__file__).resolve().parents[3]  # src/backend/agents/ -> root
  ALLOWED_WRITE_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/",
                             "storage/agent_workspaces/", "storage/pipeline_runs/")
  MAX_FILE_BYTES = 256 * 1024   # 256KB per read
  MAX_GREP_HITS = 200
  MAX_EXEC_OUTPUT = 32 * 1024   # 32KB stdout/stderr cap
  
  
  # ═════════════════════════════════════════════════════════════════
  # OpenAI / DeepSeek function-calling tool schema (V4 supports this)
  # ═════════════════════════════════════════════════════════════════
  
  TOOL_SCHEMA: List[Dict[str, Any]] = [
      {
          "type": "function",
          "function": {
              "name": "read_file",
              "description": (
                  "读取项目里某个文件的内容。优先使用此工具理解现有代码，再基于实际代码做修改。"
                  "只能读取项目根目录下的文件。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {
                          "type": "string",
                          "description": "项目相对路径，如 src/backend/channels/marine_base.py",
                      },
                      "start_line": {"type": "integer", "description": "起始行 (1-based, 可选)", "default": 1},
                      "end_line": {"type": "integer", "description": "结束行 (1-based, 可选)", "default": 0},
                  },
                  "required": ["path"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "grep",
              "description": (
                  "在项目中按正则搜索文本。用于查找类/函数/枚举值的真实定义位置。"
                  "返回每个匹配的文件路径、行号、行内容。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "pattern": {"type": "string", "description": "正则表达式"},
                      "include": {
                          "type": "string",
                          "description": "glob 限定，如 src/backend/**/*.py",
                          "default": "**/*",
                      },
                      "max_hits": {"type": "integer", "default": 50},
                  },
                  "required": ["pattern"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "list_files",
              "description": "列出某个目录下的所有文件（递归）。",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string", "description": "项目相对目录"},
                      "max_depth": {"type": "integer", "default": 3},
                  },
                  "required": ["path"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "write_file",
              "description": (
                  "向项目写入或新建文件。只能写入 src/, tests/, docs/, config/, public/ 下。"
                  "如果目标已存在，旧内容会先备份为 .bak。优先创建新文件而非整文件覆盖大文件。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string", "description": "项目相对路径"},
                      "content": {"type": "string", "description": "完整文件内容"},
                      "create_only": {
                          "type": "boolean",
                          "description": "为 true 时仅在文件不存在时写入",
                          "default": False,
                      },
                  },
                  "required": ["path", "content"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "patch_file",
              "description": (
                  "对已有文件做精准搜索-替换。比 write_file 安全，因为它要求你先看到原文。"
                  "search 必须是文件中存在的、唯一的连续片段。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string"},
                      "search": {"type": "string", "description": "要被替换的原文片段（必须唯一）"},
                      "replace": {"type": "string", "description": "替换为的新内容"},
                  },
                  "required": ["path", "search", "replace"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "run_python",
              "description": (
                  "在项目 venv 中执行一段 Python 代码（cwd=src/backend）。"
                  "用于验证 import 是否成功、检查类的属性等。最长执行 30s。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "code": {"type": "string", "description": "要执行的 Python 代码"},
                      "timeout": {"type": "integer", "default": 30},
                  },
                  "required": ["code"],
              },
          },
      },
      {
          "type": "function",
          "function": {
         
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 开发可选的异步相似度归并插件：支持用户自定义合并规则，独立部署
  步骤: pm_decompose
  📋 任务: 11e9b4b9-283
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  开发可选的异步相似度归并插件：支持用户自定义合并规则，独立部署
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/tests/conftest.py`
  ### 文件: `src/backend/tests/test_agent_toolbox.py`
  ### 文件: `src/backend/tests/test_models.py`
  **子任务拆解:**
    - *项目经理 (PM) 决策视角**  
    - **异步处理**：归并操作不应阻塞主流程，通过后台队列执行。
    - **相似度归并**：基于自定义规则，将一组输入（如 Agent 输出、任务结果、知识片段）中相似项合并。
    - **用户自定义合并规则**：允许用户通过配置（如 DSL、JSON Schema）定义相似度计算方式与合并策略。
    - **独立部署**：作为可选插件，可单独打包成微服务，通过 API 集成，支持一键启用/禁用。
    - *关键依赖说明**  
    - `T2` 插件架构是后续所有开发的基础，需在核心开发启动前完成审批。  
    - `T6` API 依赖 `T3` 引擎和 `T4` DSL 的稳定接口。  
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 开发可选的异步相似度归并插件：支持用户自定义合并规则，独立部署
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: 11e9b4b9-283
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
    开发可选的异步相似度归并插件：支持用户自定义合并规则，独立部署
    Developer
    
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
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
    ... (共 506 个 src/ 文件)
    
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
            result = team_manager.add_model_t
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

## 异步相似度归并插件 — 技术方案（Architect）

---

### 1. 总体架构与设计理念

#### 1.1 定位
该插件是一个**可选的、独立部署的微服务**，不侵入主系统核心代码。主系统（AgentsGroup2026）通过 **REST API** 或 **消息队列（推荐）** 与插件交互。插件专注于“异步归并”这个单一职责，支持用户通过配置自定义相似度算法与合并策略。

#### 1.2 核心设计原则
- **异步非阻塞**：归并任务提���后立即返回 `task_id`，主流程继续执行；插件后台处理，完成后回调或由主系统轮询。
- **插件式可插拔**：通过环境变量/配置开关控制是否启用，不启动插件不影响主系统运行。
- **可扩展规则**：相似度算法和合并策略均设计为**策略模式**，用户可通过 JSON/YAML 配置文件注册新规则，无需修改插件代码。
- **独立部署**：插件作为一个独立的 Python FastAPI 服务，打包为 Docker 镜像，拥有自己的数据库/缓存层。

#### 1.3 组件结构

```
┌─────────────────┐          REST / MQ          ┌──────────────────────────┐
│  AgentsGroup2026│  ◄────────提交任务──────────►│  Similarity-Merge-Plugin │
│     主系统       │  ◄────────查询结果──────────►│                           │
└─────────────────┘                            │  - HTTP API               │
                                                │  - Background Worker      │
                                                │  - Rule Engine            │
                                                │  - Storage (SQLite/Redis) │
                                                └──────────────────────────┘
```

---

### 2. 需要新增/修改的文件清单

#### 2.1 插件服务（独立仓库或主项目子目录）
在 `src/` 下新增 `plugins/similarity_merge/` 目录，作为独立服务。

| 文件路径 | 作用 |
|---------|------|
| `src/plugins/similarity_merge/__init__.py` | 包初始化 |
| `src/plugins/similarity_merge/main.py` | FastAPI 应用入口 |
| `src/plugins/similarity_merge/models.py` | 数据模型（Pydantic） |
| `src/plugins/similarity_merge/config.py` | 配置管理 |
| `src/plugins/similarity_merge/engine.py` | 核心归并引擎 |
| `src/plugins/similarity_merge/similarity/` | 相似度算法目录 |
| `src/plugins/similarity_merge/similarity/__init__.py` | 算法注册器 |
| `src/plugins/similarity_merge/similarity/base.py` | 策略基类 |
| `src/plugins/similarity_merge/similarity/cosine_tfidf.py` | 实现示例：TF-IDF 余弦 |
| `src/plugins/similarity_merge/similarity/levenshtein.py` | 实现示例：编辑距离 |
| `src/plugins/similarity_merge/merger/` | 合并策略目录 |
| `src/plugins/similarity_merge/merger/__init__.py` | 合并策略注册器 |
| `src/plugins/similarity_merge/merger/base.py` | 合并策略基类 |
| `src/plugins/similarity_merge/merger/longest.py` | 实现示例：保留最长的 |
| `src/plugins/similarity_merge/merger/concat.py` | 实现示例：拼接 |
| `src/plugins/similarity_merge/rules/` | 自定义规则目录 |
| `src/plugins/similarity_merge/rules/default.yaml` | 默认规则配置 |
| `src/plugins/similarity_merge/rules/user_defined.yaml` | 用户自定义示例 |
| `src/plugins/similarity_merge/tasks.py` | 后台任务（asyncio / Celery） |
| `src/plugins/similarity_merge/db.py` | 数据存储（SQLite/JSON 文件） |
| `src/plugins/similarity_merge/Dockerfile` | 容器化 |
| `src/plugins/similarity_merge/requirements.txt` | 依赖 |
| `src/plugins/similarity_merge/tests/` | 插件自身测试 |

#### 2.2 主系统集成（少量侵入式修改）
为避免侵入，通过**轻量级客户端**调用插件，放在 `src/backend/agents/` 下。

| 文件路径 | 修改内容 |
|---------|---------|
| `src/backend/agents/similarity_client.py`（新增） | 封装调用插件 API 的异步客户端 |
| `src/backend/agents/models.py` | 新增 `SimilarityMergeTask`、`MergeRuleConfig` 等 Pydantic 模型 |
| `src/backend/main.py` | 可选：添加环境变量配置插件地址，若未配置则不加载客户端 |
| `src/backend/config/` 或 `.env` | 增加 `SIMILARITY_PLUGIN_URL`、`SIMILARITY_PLUGIN_ENABLED` |

---

### 3. 数据模型与 API 接口定义

#### 3.1 公共数据模型（主系统和插件共享）
定义在 `src/backend/agents/models.py` 中（插件侧可复制相同模型）。

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class MergeRule(BaseModel):
    rule_id: str
    name: str
    description: str = ""
    similarity_algorithm: str   # 注册的算法名称
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0)
    merge_strategy: str         # 注册的合并策略名称
    params: Dict[str, Any] = {} # 算法/策略的自定义参数

class SimilarityItem(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = {}

class MergeRequest(BaseModel):
    items: List[SimilarityItem]
    rule: Optional[MergeRule] = None  # 若为 None，则使用默认规则
    callback_url: Optional[str] = None # 结果回调

class MergeGroup(BaseModel):
    representative_id: str
    merged_content: str
    member_ids: List[str]
    confidence: float

class MergeResult(BaseModel):
    task_id: str
    groups: List[MergeGroup]
    # 可选：统计信息

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, done, failed
    progress: float = 0.0
    result: Optional[MergeResult] = None
    error: Optional[str] = None
```

#### 3.2 插件 API 端点

```
POST /api/v1/merge
  Request: MergeRequest
  Response: {"task_id": "..."}
  Description: 提交归并任务，立即返回 task_id

GET /api/v1/merge/{task_id}
  Response: TaskStatus
  Description: 查询任务状态和结果

GET /api/v1/rules
  Response: List[MergeRule]
  Description: 列出所有可用的合并规则（内置+用户自定义）

POST /api/v1/rules
  Request: MergeRule
  Response: MergeRule
  Description: 注册/更新自定义规则（存于插件侧存储）

DELETE /api/v1/rules/{rule_id}
  Description: 删除自定义规则

GET /api/v1/algorithms
  Response: List[str]
  Description: 注册的相似度算法名称列表

GET /api/v1/strategies
  Response: List[str]
  Description: 注册的合并策略名称列表
```

#### 3.3 主系统客户端接口（`similarity_client.py`）

```python
class SimilarityPluginClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.enabled = True

    async def submit_merge(self, request: MergeRequest) -> str:
        """返回 task_id"""
        pass

    async def get_result(self, task_id: str) -> TaskStatus:
        pass

    async def list_rules(self) -> List[MergeRule]:
        pass
```

主系统中其他模块（如 `task_engine.py` 或特定 Agent）在需要去重/归并时，通过此客户端调用插件。

---

### 4. 核心引擎设计

#### 4.1 规则引擎
- 内置一个**默认规则**（例如：TF-IDF 余弦相似度，阈值 0.8，合并策略为“保留最长项”）。
- 用户可通过 `POST /rules` 添加新规则，存储于插件本地 SQLite 或 JSON 文件。
- 引擎根据请求中携带的 `rule_id` 或直接传入的 `MergeRule` 动态加载对应的相似度算法和合并策略。

#### 4.2 相似度算法注册器
使用 Python 的 `importlib` 动态加载，支持用户将 `.py` 文件放入 `similarity/` 目录即自动注册。
算法需实现基类：

```python
class SimilarityAlgorithm(ABC):
    @abstractmethod
    def compute(self, item1: str, item2: str, **params) -> float:
        pass
```

已内置示例：
- `cosine_tfidf`：基于 TF-IDF 向量的余弦相似度。
- `levenshtein`：归一化编辑距离。
- `jaccard`：基于字符 n-gram 的 Jaccard 系数。

#### 4.3 合并策略注册器
类似算法注册，策略基类：

```python
class MergeStrategy(ABC):
    @abstractmethod
    def merge(self, items: List[SimilarityItem], **params) -> str:
        pass
```

内置策略：
- `longest`：选择最长文本作为代表。
- `concat`：将所有文本用指定分隔符拼接。
- `first`：保留第一个。

#### 4.4 异步任务执行
- 提交任务后，`task_id` 被写入数据库（状态 `pending`）。
- 后台 worker（使用 `asyncio.create_task` 或 Celery+Redis 等）立即处理。
- 处理流程：
  1. 读取 `items`
  2. 根据规则计算相似度矩阵（可使用并行优化）
  3. 基于阈值进行聚类（连通分量/DBSCAN）
  4. 对每个聚类应用合并策略
  5. 生成 `MergeResult`，更新数据库状态为 `done`
- 若请求中包含 `callback_url`，完成后自动 POST 结果到此 URL。

---

### 5. 独立部署方案

#### 5.1 Docker 化
`Dockerfile` 示例：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

可单独打成镜像，通过 Docker Compose 与主系统编排在一起。

#### 5.2 独立存储
建议使用**文件系统上的 JSON 文件**或**SQLite**存储规则和任务状态，避免引入额外数据库依赖。高并发场景可替换为 Redis。

#### 5.3 配置管理
通过环境变量 `RULES_DIR` 指定用户自定义规则目录，可通过挂载 volume 实现动态加载。

---

### 6. 主系统集成步骤（对现有代码的最小入侵）

1. **在 `src/backend/agents/models.py` 末尾追加**上述公共模型类。
2. **创建 `src/backend/agents/similarity_client.py`**，实现一个简单的 `httpx.AsyncClient` 封装，并读取环境变量决定是否启用。
3. **在任务流水线或 Plaza 广场中调用**：
   - 例如，当多个 Agent 输出相似报告时，可在 `task_engine.py` 完成收集后，调用 `similarity_client.submit_merge(...)` 去重再返回给用户。
   - 为避免侵入核心逻辑，调用处使用 `if similarity_client and similarity_client.enabled:` 包裹。
4. **配置文件**（如 `.env.example`）增加：
   ```
   SIMILARITY_PLUGIN_ENABLED=true
   SIMILARITY_PLUGIN_URL=http://similarity-merge:8000
   ```

---

### 7. 实施指南

#### 阶段 1：搭建插件骨架
- 创建 `src/plugins/similarity_merge/` 目录结构。
- 编写 `main.py`（FastAPI 应用）、`models.py`、`config.py`。
- 编写简单的 `POST /merge` 和 `GET /merge/{task_id}` 端点，返回模拟数据。

#### 阶段 2：实现规则与策略框架
- 编写 `similarity/base.py`、`merger/base.py`。
- 编写注册器（利用 `__init__.py` 中的字典自动发现）。
- 实现至少两种相似度算法（TF-IDF、编辑距离）。
- 实现至少两种合并策略（最长、拼接）。
- 创建 `rules/default.yaml` 并加载。

#### 阶段 3：实现核心归并引擎
- `engine.py`：接收 items 和 rule，返回归并后的 Groups。
- 实现相似度矩阵计算、聚类、合并。
- 注意性能：当 items 数量超过 1000 时可考虑分批处理。

#### 阶段 4：异步任务与回调
- 引入数据库（SQLite）记录任务状态。
- 创建后台 worker（`asyncio.create_task`）处理任务。
- 支持 `callback_url`。

#### 阶段 5：插件测试
- 编写 `pytest` 测试覆盖 API、引擎逻辑、规则注册。
- Docker 构建并验证。

#### 阶段 6：主系统集成
- 新增模型和客户端。
- 在合适的业务点（如任务结果归并）添加调用。
- 端到端测试。

---

### 8. 风险与注意事项
- **性能**：当待归并项数量很多时，相似度计算是 O(n²)，需要缓存或近似算法（如 LSH）。
- **规则安全**：自定义规则如果通过上传 Python 文件实现，需严格沙箱，建议仅允许通过 YAML 配置调用已注册算法，不支持自定义代码。
- **回调失败处理**：若主系统暂时不可达，需实现重试机制。

---

该方案保证了**解耦**、**可插拔**、**用户可定制**，且对现有 AgentsGroup 系统改动最小。开发工程师可按照实施指南逐步交付。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
