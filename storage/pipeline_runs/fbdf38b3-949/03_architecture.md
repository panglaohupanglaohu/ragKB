# 架构设计 — architect

任务: 搭建领域事件管道与 SkillStore：事件携带完整上下文而非 ID，SkillStore 主表幂等写入并带 schema_version，异步 Indexing Worker 消费事件构建向量索引，检索与衰减策略通过 SkillQuer
步骤: architecture
Agent: build_architect

---

📋 任务: fbdf38b3-949
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
  搭建领域事件管道与 SkillStore：事件携带完整上下文而非 ID，SkillStore 主表幂等写入并带 schema_version，异步 Indexing Worker 消费事件构建向量索引，检索与衰减策略通过 SkillQuer
  Architect, Developer, Deployer
  
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
  src/docs/agent_handoffs/11e9b4b9-283_pm_decompose_20260509T075116.md
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
  src/docs/agent_handoffs/21ef94ba-2b6_executor_started_20260509T074916.md
  src/docs/agent_handoffs/21ef94ba-2b6_pm_decompose_20260509T075106.md
  src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/2da416d2-cdf_executor_started_20260509T074916.md
  src/docs/agent_handoffs/2da416d2-cdf_pm_decompose_20260509T075121.md
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
  src/docs/agent_handoffs/3f9494e1-96d_pm_decompose_20260509T075056.md
  src/docs/agent_handoffs/3f9494e1-96d_research_20260509T075256.md
  src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
  src/docs/agent_handoffs/4601c322-51d_executor_started_20260509T075153.md
  src/docs/agent_handoffs/4601c322-51d_pipeline_complete_20260509T075233.md
  ... (共 530 个 src/ 文件)
  
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
              f"- [P0] 结论 | 主要支持角色 | 为什么重要\n"
              f"- [P1] ...\n"
              f"- [P2] 仅保留 1 条最相关的低权重建议\n\n"
              f"## 执行计划\n"
              f"| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
              f"|---|---|---|---|---|---|\n"
              f"列出 3-5 个任务，按优先级排序\n\n"
              f"## 补充观察\n"
              f"1 句话带过能耗/外围建议即可\n\n"
              f"请用 Markdown 输出，简洁有力，能直接作为任务单下发。"
          )
          disc.summary = await self._generate_agent_content(
              moderator,
              final_prompt,
          )
          # 将最终总结中的执行计划提取到 disc.plan，供前端和派发使用
          disc.plan = {
              "revision_reason": "讨论收敛",
              "revised_at": datetime.now(timezone.utc).isoformat(),
              "content": disc.summary,
          }
          await self._broadcast(disc.id, {"type": "plan_updated", "plan": disc.plan})
  
          closing_msg = PlazaMessage(
              discussion_id=disc.id,
              agent_id=moderator.agent_id,
              agent_name=moderator.agent_name or moderator.agent_id,
              role=moderator.role,
              niche_role="moderator",
              content=self._build_closing_brief(disc.summary),
              r
  ```
  
  ### 文件: `src/backend/agents/skill_registry.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Agent Team Framework — Skill Registry.
  
  Provides default skill definitions across general, digital-twin, and automation
  categories, plus a registry class for runtime skill management.
  """
  
  from __future__ import annotations
  
  from typing import Any, Dict, List, Optional
  
  from .models import SkillCategory, SkillDefinition
  
  
  def get_default_skills() -> List[SkillDefinition]:
      """Return the default catalog of skill definitions."""
  
      SC = SkillCategory
      SD = SkillDefinition
      return [
          # ── General skills ─────────────────────────────────────────────
          SD(
              name="competitive_analysis",
              description="Analyze competitors and market positioning",
              category=SC.GENERAL,
              required_tools=['web_search', 'extract_content'],
              instructions="## 竞品分析\n\n1. 使用 web_search 搜索竞品信息\n2. 提取关键数据：市场份额、产品特性、定价策略\n3. 生成 SWOT 对比矩阵\n4. 输出结构化分析报告"),
          SD(
              name="complex_task_executor",
              description="Break down and execute complex multi-step tasks",
              category=SC.GENERAL,
              required=True,
              required_tools=['run_python', 'run_shell', 'send_message'],
              instructions="## 复杂任务执行\n\n1. 将任务分解为可执行子步骤\n2. 评估每步所需工具和依赖\n3. 按序执行，遇错时回退重试\n4. 汇总结果并报告进度"),
          SD(
              name="content_research_writer",
              description="Research topics and produce written content",
              category=SC.GENERAL,
              required_tools=['web_search', 'extract_content', 'write_file'],
              instructions="## 内容研究与写作\n\n1. 确认主题和目标受众\n2. 使用 web_search 收集资料\n3. 提取关键信息并整理大纲\n4. 撰写结构化内容\n5. 保存到工作区文件"),
          SD(
              name="content_writing",
              description="Write and edit documentation and reports",
              category=SC.GENERAL,
              required_tools=['write_file', 'read_file'],
              instructions="## 文档写作\n\n1. 读取现有文档了解上下文\n2. 根据需求撰写/修改内容\n3. 确保格式规范、语言专业\n4. 保存并通知相关人员"),
          SD(
              name="data_analysis",
              description="Analyze datasets and produce insights",
              category=SC.GENERAL,
              required_tools=['run_python', 'read_file'],
              instructions="## 数据分析\n\n1. 读取数据文件\n2. 使用 Python 进行统计分析\n3. 生成可视化图表\n4. 总结关键发现和趋势\n5. 给出数据驱动的建议"),
          SD(
              name="mcp_installer",
              description="Install and configure MCP server integrations",
              category=SC.GENERAL,
              required=True,
              required_tools=['run_shell', 'write_file', 'read_file'],
              instructions="## MCP 服务器安装\n\n1. 检查目标 MCP 服务器兼容性\n2. 执行安装命令\n3. 配置连接参数\n4. 验证连接状态\n5. 注册到工具目录"),
          SD(
              name="meeting_notes",
              description="Capture and summarize meeting notes",
              category=SC.GENERAL,
              required_tools=['write_file'],
              instructions="## 会议记录\n\n1. 记录参会人员和议题\n2. 按时间线记录讨论要点\n3. 标记决策事项和待办\n4. 生成结构化会议纪要\n5. 分发给相关人员"),
          SD(
              name="skill_creator",
              description="Create new custom skills from descriptions",
              category=SC.GENERAL,
              required=True,
              required_tools=['write_file', 'read_file'],
              instructions="## 技能创建\n\n1. 分析技能需求描述\n2. 确定所需工具和流程\n3. 编写技能指令模板\n4. 创建技能定义文件\n5. 注册到技能目录"),
          SD(
              name="web_research",
              description="Conduct web research and summarize findings",
              category=SC.GENERAL,
              required_tools=['web_search', 'navigate_url', 'extract_content'],
              instructions="## 网络研究\n\n1. 制定搜索策略和关键词\n2. 多轮搜索收集信息\n3. 访问并提取相关页面内容\n4. 交叉验证信息准确性\n5. 生成研究报告"),
          # ── Digital Twin skills ────────────────────────────────────────
          SD(name="dt_camera_control", description="Control digital twin camera views and animations",
              category=SC.DIGITAL_TWIN, required_tools=['dt_camera_move'],
              instructions="## 数字孪生相机控制\n\n使用 dt_camera_move 控制相机位置、目标点和过渡动画。支持预设视角（top/front/side/iso）和自定义坐标。"),
          SD(name="dt_coordinate_system", description="Manage coordinate system transformations",
              category=SC.DIGITAL_TWIN, required_tools=['dt_model_transform'],
              instructions="## 坐标系管理\n\n1. 理解场景坐标系（Y-up，单位:米）\n2. 使用 dt_model_transform 进行平移/旋转/缩放\n3. 处理世界坐标与局部坐标转换"),
          SD(name="dt_model_layout", description="Arrange and layout 3D models in the scene",
              category=SC.DIGITAL_TWIN, required_tools=['dt_model_load', 'dt_model_transform'],
              instructions="## 3D模型布局\n\n1. 加载模型到场景\n2. 调整位置/旋转/缩放\n3. 确保各模型间距和对齐\n4. 设置碰撞体积"),
          SD(name="dt_model_import", description="Import 3D models from various formats",
              category=SC.DIGITAL_TWIN, required_tools=['dt_model_load'],
              instructions="## 模型导入\n\n支持格式: GLB/GLTF/OBJ/FBX。加载模型并设置初始变换。"),
          SD(name="dt_interaction_actions", description="Define interactive inspection paths and actions",
              category=SC.DIGITAL_TWIN, required_tools=['dt_inspection_path', 'dt_camera_move'],
              instructions="## 交互巡检\n\n1. 定义巡检路径航路点\n2. 设置相机飞行速度和模式\n3. 在关键点添加标注和检查项"),
          SD(name="dt_material_change", description="Change materials and textures on models",
              category=SC.DIGITAL_TWIN, required_tools=['dt_material_set'],
              instructions="## 材质修改\n\n使用 dt_material_set 修改颜色/金属度/粗糙度。支持PBR材质参数。"),
          SD(name="dt_physics_simulation", description="Configure and run physics simulations",
              category=SC.DIGITAL_TWIN, required_tools=['dt_physics_toggle'],
              instructions="## 物理模拟\n\n控制重力、碰撞检测和刚体动力学。用于物理模拟和系统分析。"),
          SD(name="dt_lighting_control", description="Control scene lighting and shadows",
              category=SC.DIGITAL_TWIN, required_tools=['dt_light_adjust'],
              instructions="## 灯光控制\n\n调整环境光/方向光/点光源的强度、颜色和位置。支持昼夜模拟。"),
          SD(name="dt_rendering_control", description="Control rendering pipeline and effects",
              category=SC.DIGITAL_TWIN, required_tools=['dt_render_mode'],
              instructions="## 渲染控制\n\n切换实体/线框/X光/热力图模式。用于不同分析场景。"),
  
          # ── Automation skills ──────────────────────────────────────────
          SD(name="auto_report", description="定时生成工作报告",
              category=SC.AUTOMATION, icon="📊", required_tools=['write_file'],
              instructions="## 自动报告\n\n1. 收集系统运行数据\n2. 统计关键指标\n3. 生成结构化报告\n4. 按时发送给相关人员"),
          SD(name="auto_monitor", description="监控系统状态并报警",
              category=SC.AUTOMATION, icon="🔔", required_tools=['schedule_task', 'send_message'],
              instructions="## 自动监控\n\n1. 定期检查系统健康状态\n2. 对比阈值判断异常\n3. 触发告警通知\n4. 记录监控日志"),
          SD(name="workflow_runner", description="运行预定义工作流",
              category=SC.AUTOMATION, icon="▶️", required_tools=['run_python', 'run_shell'],
              instructions="## 工作流执行\n\n1. 解析工作流定义\n2. 按步骤执行任务\n3. 处理条件分支\n4. 汇报执行结果"),
          # ── Research skills ─────────────────────────────
          SD(name="cross_session_recall", description="跨会话研究回溯",
              category=SC.RESEARCH, icon="🔍", required_tools=['session_search', 'memory_read'],
              instructions="## 跨会话回溯\n\n1. 搜索历史会话\n2. 提取相关研究发现\n3. 整理知识脉络\n4. 避免重复研究"),
  
          # ── Build Team / PM skills ─────────────────────────────────────
          SD(name="task_decomposition", description="将复杂任务分解为可执行子任务并分配给团队成员",
              category=SC.GENERAL, icon="📋",
              required_tools=['send_message'],
              config_schema={
                  "max_subtasks": {"type": "integer", "default": 10, "description": "最大子任务数"},
                  "auto_assign": {"type": "boolean", "default": True, "description": "自动分配给最佳Agent"},
              },
              instructions="## 任务分解\n\n1. 分析任务目标和范围\n2. 识别关键交付物和里程碑\n3. 将任务分解为 3-10 个可执行子任务\n4. 为每个子任务指定负责Agent和优先级\n5. 设置依赖关系和完成标准\n6. 通过 TaskEngine 提交子任务"),
          SD(name="progress_tracking", description="跟踪项目进度、识别风险和阻塞点",
              category=SC.GENERAL, icon="📊",
              required_tools=['read_file', 'send_message'],
              instructions="## 进度跟踪\n\n1. 查询 TaskEngine 获取任务状态\n2. 计算完成率和延迟风险\n3. 识别阻塞任务和依赖链\n4. 生成进度报告\n5. 向相关Agent发送更新"),
          SD(name="blocker_resolution", description="识别和解决项目阻塞问题",
              category=SC.GENERAL, icon="🔓",
              required_tools=['send_message'],
              instructions="## 阻塞解决\n\n1. 分析阻塞原因\n2. 确定解决方案\n3. 协调相关Agent\n4. 重新分配资源\n5. 更新任务状态"),
          # ── Build Team / Researcher skills ─────────────────────────────
          SD(name="requirements_analysis", description="分析需求文档，提取功能和非功能需求",
              category=SC.GENERAL, icon="📝",
              required_tools=['read_file', 'web_search'],
              instructions="## 需求分析\n\n1. 阅读需求文档\n2. 提取功能需求清单\n3. 识别非功能需求\n4. 标记歧义和缺失项\n5. 生成需求矩阵"),
          # ── Build Team / Architect skills ──────────────────────────────
          SD(name="architecture_design", description="设计系统架构，定义分层和模块边界",
              category=SC.GENERAL, icon="🏗",
              required_tools=['read_file', 'write_file'],
              instructions="## 架构设计\n\n1. 分析需求和约束\n2. 选择架构风格\n3. 定义模块边界和接口\n4. 绘制架构图\n5. 编写 ADR 文档"),
          SD(name="interface_definition", description="定义模块间API接口和数据契约",
              category=SC.GENERAL, icon="🔌",
              required_tools=['write_file', 'read_file'],
              instructions="## 接口定义\n\n1. 确定通信协议\n2. 定义请求/响应模型\n3. 编写 OpenAPI/JSON Schema\n4. 生成接口文档"),
          SD(name="pattern_selection", description="选择适合的设计模式和技术方案",
              category=SC.GENERAL, icon="🧩",
              required_tools=['web_search', 'read_file'],
              instructions="## 模式选择\n\n1. 分析问题场景\n2. 匹配候选设计模式\n3. 评估优劣权衡\n4. 记录选型理由"),
          # ── Build Team / Developer skills ──────────────────────────────
          SD(name="code_implementation", description="编写功能代码，实现需求规格",
              category=SC.GENERAL, icon="💻",
              required_tools=['run_shell', 'write_file', 'read_file'],
              config_schema={
                  "executor": {"type": "string", "default": "claude_code",
                      "enum": ["claude_code", "llm_chat", "manual"],
                      "description": "执行器: claude_code=本地Claude Code, llm_chat=LLM生成, manual=手动编码"},
                  "claude_code_path": {"type": "string", "default": "claude",
                      "description": "Claude Code CLI 路径"},
                  "working_directory": {"type": "string", "default": "",
                      "description": "工作目录 (空=项目根)"},
                  "auto_test": {"type": "boolean", "default": True,
                      "description": "实现后自动运行测试"},
                  "language": {"type": "string", "default": "python",
                      "enum": ["python", "javascript", "typescript"],
                      "description": "主要编程语言"},
              },
              config={
                  "executor": "claude_code",
                  "claude_code_path": "claude",
                  "working_directory": "",
                  "auto_test": True,
                  "language": "python",
              },
              instructions="## 代码实现\n\n1. 阅读任务描述和架构设计\n2. 确定要修改的文件和模块\n3. 编写实现代码\n4. 运行相关测试确保无回归\n5. 提交代码变更\n\n### 执行器模式\n- **claude_code**: 调用本地 Claude Code CLI 执行编码任务\n- **llm_chat**: 通过 LLM API 生成代码\n- **manual**: 生成任务描述供人工编码"),
          SD(name="debugging", description="诊断和修复代码缺陷",
              category=SC.GENERAL, icon="🐛",
              required_tools=['run_shell', 'read_file', 'write_file'],
              instructions="## 调试\n\n1. 复现问题\n2. 分析日志和堆栈\n3. 定位 root cause\n4. 编写修复代码\n5. 验证修复并添加回归测试"),
          SD(name="refactoring", description="重构代码提升可维护性和性能",
              category=SC.GENERAL, icon="♻️",
              required_tools=['read_file', 'write_file', 'run_shell'],
              instructions="## 代码重构\n\n1. 识别代码坏味道\n2. 选择重构策略\n3. 小步修改，保持测试绿色\n4. 验证功能无变化"),
          SD(name="testing", description="编写和执行单元测试",
              category=SC.GENERAL, icon="✅",
              required_tools=['run_shell', 'write_file', 'read_file'],
              instructions="## 测试编写\n\n1. 分析待测代码\n2. 设计测试用例\n3. 编写 pytest 测试\n4. 运行并确认通过"),
          # ── Build Team / Tester skills ─────────────────────────────────
          SD(name="test_design", description="设计测试策略和测试用例",
              category=SC.GENERAL, icon="📐",
              required_tools=['read_file', 'write_file'],
              instructions="## 测试设计\n\n1. 分析功能规格\n2. 设计边界值和等价类\n3. 编写测试矩阵\n4. 确定自动化优先级"),
          SD(name="test_execution", description="执行测试套件并分析结果",
              category=SC.GENERAL, icon="▶️",
              required_tools=['run_shell', 'read_file'],
              instructions="## 测试执行\n\n1. 运行 pytest 测试套件\n2. 收集测试结果\n3. 分析失败用例\n4. 生成测试报告"),
          SD(name="coverage_analysis", description="分析代码覆盖率并识别盲区",
              category=SC.GENERAL, icon="📈",
              required_tools=['run_shell', 'read_file'],
              instructions="## 覆盖率分析\n\n1. 运行 pytest --cov\n2. 分析行覆盖和分支覆盖\n3. 识别未覆盖代码\n4. 建议补充测试"),
          SD(name="regression_testing", description="回归测试确保修改未引入新缺陷",
              category=SC.GENERAL, icon="🔄",
              required_tools=['run_shell'],
              instructions="## 回归测试\n\n1. 确定修改影响范围\n2. 运行相关测试子集\n3. 全量测试验证\n4. 对比前后结果"),
          # ── Build Team / Deployer skills ───────────────────────────────
          SD(name="build_automation", description="自动化构建和打包流程",
              category=SC.GENERAL, icon="🔨",
              required_tools=['run_shell', 'write_file'],
              instructions="## 构建自动化\n\n1. 配置构建脚本\n2. 执行构建命令\n3. 验证产物完整性\n4. 生成构建报告"),
          SD(name="container_management",
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 搭建领域事件管道与 SkillStore：事件携带完整上下文而非 ID，SkillStore 主表幂等写入并带 schema_version，异步 Indexing Worker 消费事件构建向量索引，检索与衰减策略通过 SkillQuer
  步骤: pm_decompose
  📋 任务: fbdf38b3-949
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  搭建领域事件管道与 SkillStore：事件携带完整上下文而非 ID，SkillStore 主表幂等写入并带 schema_version，异步 Indexing Worker 消费事件构建向量索引，检索与衰减策略通过 SkillQuer
  Architect, Developer, Deployer
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/tests/test_agent_toolbox.py`
  ### 文件: `src/backend/agents/models.py`
  **子任务拆解:**
    - `models.py` 中的 `SkillDefinition` 数据类 —— 需扩展字段
    - `skill_registry.py` 默认技能定义和注册器 —— 将适配为 SkillStore 的上层接口
    - `plaza_store.py` / `task_store.py` 等文件存储范例 —— 可参考其 JSON 持久化方式
    - 尚无事件总线、异步 Worker、向量索引等基础设施 —— 本次任务需要新建
    - *产出物**：公共接口 / 数据模型约定、Schema 版本规范、目录结构
    - *产出物**：带版本管理和幂等能力的技能持久化存储
    - *产出物**：轻量级事件总线，支持发布 / 订阅，保证事件携带完整上下文
    - *产出物**：异步 Worker 消费事件并构建向量索引
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 搭建领域事件管道与 SkillStore：事件携带完整上下文而非 ID，SkillStore 主表幂等写入并带 schema_version，异步 Indexing Worker 消费事件构建向量索引，检索与衰减策略通过 SkillQuer
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: fbdf38b3-949
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
    搭建领域事件管道与 SkillStore：事件携带完整上下文而非 ID，SkillStore 主表幂等写入并带 schema_version，异步 Indexing Worker 消费事件构建向量索引，检索与衰减策略通过 SkillQuer
    Architect, Developer, Deployer
    
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
    src/docs/agent_handoffs/11e9b4b9-283_pm_decompose_20260509T075116.md
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
    src/docs/agent_handoffs/21ef94ba-2b6_executor_started_20260509T074916.md
    src/docs/agent_handoffs/21ef94ba-2b6_pm_decompose_20260509T075106.md
    src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
    src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
    src/docs/agent_handoffs/2da416d2-cdf_executor_started_20260509T074916.md
    src/docs/agent_handoffs/2da416d2-cdf_pm_decompose_20260509T075121.md
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
    src/docs/agent_handoffs/3f9494e1-96d_pm_decompose_20260509T075056.md
    src/docs/agent_handoffs/3f9494e1-96d_research_20260509T075256.md
    src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
    src/docs/agent_handoffs/4601c322-51d_executor_started_20260509T075153.md
    src/docs/agent_handoffs/4601c322-51d_pipeline_complete_20260509T075233.md
    ... (共 530 个 src/ 文件)
    
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

# 领域事件管道与 SkillStore — 架构设计方案

## 1. 架构概览

```text
┌─────────────┐    DomainEvent     ┌──────────────────┐
│  Skill 操作  │ ─────────────────▶│   EventBus        │
│  (创建/更新/ │                   │  (asyncio.Queue)  │
│   删除/访问) │                   └────────┬─────────┘
└─────────────┘                            │
                                           ▼
                                    ┌──────────────────┐
                                    │  SkillStore       │
                                    │  (JSON 持久化)    │
                                    │  - 幂等写入       │
                                    │  - schema_version │
                                    └──────────────────┘
                                           │
                                           ▼
                                    ┌──────────────────┐
                                    │  Indexing Worker  │
                                    │  (asyncio task)   │
                                    │  - 向量化         │
                                    │  - 更新索引       │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  VectorIndex      │
                                    │  (InMemory)       │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  SkillQuerier     │
                                    │  - 语义检索       │
                                    │  - 衰减策略       │
                                    └──────────────────┘
```

- **EventBus**: 全局异步事件管道，发布领域事件（携带完整 Skill 快照）。
- **SkillStore**: 新的持久化存储，基于 `skill_id` upsert，带 `schema_version` 和去重机制。
- **Indexing Worker**: 长期运行的异步任务，消费事件，调用向量化器更新内存索引。
- **SkillQuerier**: 提供统一的检索入口，组合语义相似度与衰减权重，返回最终排序结果。

## 2. 新增/修改文件清单

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| `src/backend/agents/skill_pipeline/__init__.py` | 新增 | 包初始化，导出核心类 |
| `src/backend/agents/skill_pipeline/domain_events.py` | 新增 | 定义领域事件模型 |
| `src/backend/agents/skill_pipeline/event_bus.py` | 新增 | 异步事件总线（发布/订阅） |
| `src/backend/agents/skill_pipeline/skill_store.py` | 新增 | 幂等、带版本的 SkillStore |
| `src/backend/agents/skill_pipeline/skill_querier.py` | 新增 | 检索 + 衰减策略 |
| `src/backend/agents/skill_pipeline/vector_index.py` | 新增 | 内存向量索引（可插拔） |
| `src/backend/agents/skill_pipeline/indexing_worker.py` | 新增 | 异步 Worker，消费事件更新索引 |
| `src/backend/agents/models.py` | 修改 | 扩展 `SkillDefinition` → `SkillRecord`（或新建） |
| `src/backend/agents/skill_registry.py` | 修改 | 适配新管道（发布事件） |
| `src/backend/tests/test_skill_pipeline.py` | 新增 | 管道集成测试 |

> 注：所有管道代码集中在 `agents/skill_pipeline/` 中，避免污染现有扁平结构。

## 3. 数据模型设计

### 3.1 技能记录 `SkillRecord` (扩展自 `SkillDefinition`)

在 `models.py` 中新增或直接定义在 `skill_pipeline/domain_events.py`：

```python
@dataclass
class SkillRecord:
    """持久化技能记录，包含版本与事件控制字段。"""
    skill_id: str
    name: str
    description: str
    category: SkillCategory
    required: bool
    enabled: bool
    icon: str
    config_schema: Dict[str, Any]
    config: Dict[str, Any]
    is_default: bool
    source: str
    slug: str
    required_tools: List[str]
    instructions: str

    # ── 新增字段 ──
    schema_version: str = "1.0"          # 记录当前版本
    created_at: str = ""                 # ISO 8601
    updated_at: str = ""
    last_event_id: str = ""              # 最后处理的事件ID（用于幂等）
```

### 3.2 领域事件 `DomainEvent`

```python
@dataclass
class DomainEvent:
    event_id: str                        # UUID，全局唯一
    event_type: str                      # "skill.created" | "skill.updated" | "skill.deleted" | "skill.accessed"
    aggregate_id: str                    # skill_id
    payload: SkillRecord                 # 完整技能快照
    timestamp: str                       # ISO 8601
    meta: Dict[str, Any] = field(default_factory=dict)
```

**关键设计**：事件携带完整 `payload`，消费者无需回查数据库。

## 4. 事件管道 (`EventBus`)

- 基于 `asyncio.Queue` 的内置总线，无外部依赖。
- 全局单例 `skill_event_bus`，提供 `publish(event)` 和 `subscribe()` 方法。
- 订阅者以异步生成器形式消费事件。

```python
class SkillEventBus:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._processed_ids: Set[str] = set()  # 简单去重

    async def publish(self, event: DomainEvent):
        if event.event_id in self._processed_ids:
            return
        self._processed_ids.add(event.event_id)
        await self._queue.put(event)

    async def subscribe(self) -> AsyncIterator[DomainEvent]:
        while True:
            event = await self._queue.get()
            yield event
```

> 对于生产环境，未来可替换为 Redis Streams 或 Kafka，接口不变。

## 5. SkillStore (幂等写入 + schema_version)

**持久化方案**：沿用项目已有的 JSON 文件存储 (`data/skills_v2.json`)。

```python
class SkillStore:
    def __init__(self, filepath: str = "data/skills_v2.json"):
        self._filepath = filepath
        self._records: Dict[str, SkillRecord] = load_json(filepath)

    async def upsert(self, event: DomainEvent) -> SkillRecord:
        """幂等写入：
        1. 如果 event_id <= last_event_id → 跳过
        2. 如果 schema_version < 当前版本 → 可配置拒绝更新
        3. 否则覆盖写入
        """
        skill_id = event.aggregate_id
        existing = self._records.get(skill_id)
        if existing and event.event_id <= existing.last_event_id:
            return existing  # 旧事件忽略
        if existing and _version_compare(event.payload.schema_version, existing.schema_version) < 0:
            # 日志警告，但继续（可根据策略决定）
            pass
        self._records[skill_id] = event.payload
        self._records[skill_id].last_event_id = event.event_id
        self._records[skill_id].updated_at = event.timestamp
        self._flush()
        return self._records[skill_id]

    async def delete(self, skill_id: str):
        # 标记为 disabled 或物理删除
        ...

    async def get(self, skill_id: str) -> Optional[SkillRecord]:
        return self._records.get(skill_id)

    async def list_all(self) -> List[SkillRecord]:
        return list(self._records.values())
```

**幂等保证**：通过 `last_event_id` 严格递增检查。`event_id` 建议格式：`"{timestamp}-{random}"`。

## 6. 向量索引与 Indexing Worker

### 6.1 向量化抽象 (`Vectorizer`)

为保持轻量，初期提供可插拔接口，默认使用句向量模型（需额外安装，但设计成懒加载）。若未安装，使用 **TF-IDF 加权词袋 + 空向量**（仅提供结构，语义近似依靠关键词匹配）。

```python
class BaseVectorizer:
    async def encode(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError

# 默认实现 (zero vector)
class PassthroughVectorizer(BaseVectorizer):
    async def encode(self, texts):
        return np.zeros((len(texts), 768))  # 维度假定为768
```

建议开发者引入 `sentence-transformers` 作为可选依赖，实现 `SentenceTransformersVectorizer`。

### 6.2 内存向量索引 (`InMemoryVectorIndex`)

```python
class InMemoryVectorIndex:
    def __init__(self, dim: int = 768):
        self._dim = dim
        self._vectors: Dict[str, np.ndarray] = {}
        self._lock = asyncio.Lock()

    async def upsert(self, skill_id: str, vector: np.ndarray):
        async with self._lock:
            self._vectors[skill_id] = vector

    async def remove(self, skill_id: str):
        async with self._lock:
            self._vectors.pop(skill_id, None)

    async def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """余弦相似度检索"""
        async with self._lock:
            if not self._vectors:
                return []
            ids = list(self._vectors.keys())
            matrix = np.stack([self._vectors[id_] for id_ in ids])
            # 归一化
            matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
            q = query_vector / np.linalg.norm(query_vector)
            scores = np.dot(matrix, q)
            top_indices = np.argsort(scores)[-k:][::-1]
            return [(ids[i], float(scores[i])) for i in top_indices]
```

### 6.3 Indexing Worker

```python
async def indexing_worker(
    bus: SkillEventBus,
    store: SkillStore,
    vectorizer: BaseVectorizer,
    index: InMemoryVectorIndex
):
    async for event in bus.subscribe():
        if event.event_type == "skill.deleted":
            await index.remove(event.aggregate_id)
        else:
            # 生成向量：拼接 name + description + instructions
            text = f"{event.payload.name} {event.payload.description} {event.payload.instructions}"
            vec = await vectorizer.encode([text])
            await index.upsert(event.aggregate_id, vec[0])
        # 同时保持 SkillStore 与事件同步（已在发布事件前写入？协作方式见下文）
```

> **启动方式**：在 FastAPI `startup` 事件中 `asyncio.create_task(indexing_worker(...))`。

## 7. SkillQuerier — 检索与衰减策略

提供高层查询接口，调用向量索引并应用衰减因子。

```python
class SkillQuerier:
    def __init__(self, index: InMemoryVectorIndex, store: SkillStore,
                 vectorizer: BaseVectorizer,
                 decay_strategy: DecayStrategy = None):
        ...

    async def search(self, query: str, top_k: int = 5) -> List[Tuple[SkillRecord, float]]:
        # 1. 向量化查询
        q_vec = await self._vectorizer.encode([query])
        # 2. 向量检索
        candidates = await self._index.search(q_vec[0], top_k * 3)  # 获取更多候选
        # 3. 从 store 获取完整 record，应用衰减
        results = []
        now = datetime.now(tz=timezone.utc)
        for skill_id, sim_score in candidates:
            record = await self._store.get(skill_id)
            if not record or not record.enabled:
                continue
            final_score = self._decay.compute(record, sim_score, now)
            results.append((record, final_score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
```

### 衰减策略 (接口)

```python
class DecayStrategy:
    def compute(self, record: SkillRecord, similarity: float, now: datetime) -> float:
        raise NotImplementedError

@dataclass
class TimeDecayStrategy(DecayStrategy):
    """时间衰减：最近更新/创建的技能获得更高权重。"""
    half_life_days: float = 30.0

    def compute(self, record, similarity, now):
        updated = datetime.fromisoformat(record.updated_at or record.created_at)
        age_days = (now - updated).days
        time_weight = 0.5 ** (age_days / self.half_life_days)
        return similarity * 0.8 + time_weight * 0.2  # 混合权重
```

支持通过配置切换不同策略。

## 8. 与现有代码集成

### 8.1 改造 `skill_registry.py`

保留原有 `get_default_skills()` 返回 `SkillDefinition`，但新增适配函数：

```python
# skill_registry.py
from .skill_pipeline.event_bus import skill_event_bus
from .skill_pipeline.domain_events import DomainEvent, SkillRecord

async def register_skill(record: SkillRecord):
    """新版注册：写入 SkillStore 并发布事件"""
    await skill_store.upsert(event)
    await skill_event_bus.publish(DomainEvent(
        event_id=generate_event_id(),
        event_type="skill.created",
        aggregate_id=record.skill_id,
        payload=record,
        timestamp=utcnow()
    ))
```

原 `TeamManager.add_skill()` 等方法可逐步迁移至调用此新函数。

### 8.2 启动引导

在 `main.py` 的 `startup` 中：

```python
from agents.skill_pipeline import initialize_skill_pipeline

@app.on_event("startup")
async def startup():
    skill_pipeline = await initialize_skill_pipeline()
    app.state.skill_querier = skill_pipeline.querier
```

`initialize_skill_pipeline` 创建所有组件并启动 Worker。

## 9. 接口规范

### 9.1 SkillQuerier 公共 API

```python
class SkillQuerier:
    async def search(self, query: str, top_k: int = 5, filter_category: SkillCategory = None) -> List[SkillRecord]:
        """主检索接口，返回带衰减加权的技能列表（按分数降序）"""
        ...
    async def get_by_id(self, skill_id: str) -> Optional[SkillRecord]:
        ...
```

### 9.2 REST 接口（可选，建议由 Developer 按需添加）

```http
GET /api/skills/search?q=...&top_k=5&category=general
POST /api/skills/reindex   (手动触发全量重建索引)
```

## 10. 分步实施指南（Developer）

### 步骤 1: 建立基础结构
1. 创建目录 `agents/skill_pipeline/` 及空 `__init__.py`。
2. 在 `models.py` 中新增 `SkillRecord` 数据类（或直接在 `domain_events.py` 中定义）。
3. 实现 `DomainEvent` 和 `SkillRecord`。

### 步骤 2: 实现 EventBus
1. 编写 `event_bus.py` → `SkillEventBus` 类。
2. 单元测试：发布事件，订阅者能否收到。

### 步骤 3: 实现 SkillStore
1. 创建 `skill_store.py`，实现 JSON 持久化 + 幂等 `upsert`。
2. 通过 `skill_id` + `last_event_id` 保证幂等。
3. 测试并发写入与版本检查。

### 步骤 4: 向量索引与 Indexing Worker
1. 创建 `vector_index.py`，实现 `InMemoryVectorIndex`（基于 numpy）。
2. 创建 `vectorizer.py`（可选），默认使用零向量实现。
3. 创建 `indexing_worker.py`，实现 `indexing_worker` 协程。
4. 写测试：向 EventBus 发布事件，检查索引是否更新。

### 步骤 5: SkillQuerier + 衰减策略
1. 写 `skill_querier.py`，组合向量索引、store、衰减策略。
2. 实现基础 `TimeDecayStrategy`。
3. 端到端测试：注册技能 → 发布事件 → 索引更新 → 检索返回排序结果。

### 步骤 6: 与旧系统整合
1. 修改 `skill_registry.py`，在创建/更新技能时调用新管道。
2. 修改 `main.py` 启动流程，初始化管道组件和 Worker。
3. 编写集成测试，确保旧 API 仍可用。

### 步骤 7: 性能与扩展（可选）
1. 引入 `sentence-transformers`，实现真正的语义向量化。
2. 增加索引持久化（周期性保存索引快照）。
3. 添加 OpenAPI 端点供外部调用。

## 11. 依赖与注意事项

- **强制依赖**: `numpy`（已在 `requirements.txt` 中？检查），保持轻量。
- **可选依赖**: `sentence-transformers`（用于语义检索），默认回退策略不影响核心流程。
- **数据位置**: `data/skills_v2.json` 与现有 `data/skills.json` 分离，互不干扰。
- **Worker 异常处理**: Indexing Worker 必须捕获 `asyncio.CancelledError` 并优雅关闭；向量化失败时记录日志并跳过该事件，避免阻塞整个管道。
- **幂等性依赖事件ID生成**：推荐使用 `{unix_timestamp}-{random_6chars}` 格式，如 `1715000000-a1b2c3`。

---

该方案完全基于现有代码风格，渐进式引入事件管道，不破坏已有功能，并为未来的语义检索和事件溯源打下基础。如有疑问请随时提出，我将进一步细化。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
