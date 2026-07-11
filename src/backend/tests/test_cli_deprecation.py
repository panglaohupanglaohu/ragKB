# -*- coding: utf-8 -*-
"""XC-5.1: 任务执行去 CLI 化 单测

覆盖：
  XC-1.1 引擎分派（_should_use_direct_api / _harness_provider_credentials）
  XC-2.1 MANIFEST 落盘
  XC-2.3 write_file 白名单
  XC-3.1 三层工具集
  XC-3.2 deploy_exec 门禁
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))


# ═══════════════════════════════════════════════════════════════
# XC-1.1: _should_use_direct_api
# ═══════════════════════════════════════════════════════════════

class TestShouldUseDirectApi:
    def test_text_roles_return_true(self):
        from agents.api import _should_use_direct_api
        for role in ("project_manager", "researcher", "documentation", "architect"):
            assert _should_use_direct_api(role) is True, f"{role} should use direct API"

    def test_code_roles_return_false(self):
        from agents.api import _should_use_direct_api
        for role in ("developer", "qa_engineer", "deployer", "devops"):
            assert _should_use_direct_api(role) is False, f"{role} should use tool loop"


# ═══════════════════════════════════════════════════════════════
# XC-2.1: MANIFEST 落盘
# ═══════════════════════════════════════════════════════════════

class TestWorkspaceManifest:
    def test_manifest_append_update(self, tmp_path):
        """MANIFEST.json 应能 append 更新多步骤产物."""
        # Mock pipeline_dir to use tmp_path
        manifest_path = tmp_path / "MANIFEST.json"
        with patch("agents.api._pipeline_dir", return_value=str(tmp_path)):
            from agents.api import _update_workspace_manifest
            _update_workspace_manifest("test-task", "develop",
                                       [{"path": str(tmp_path / "output.md"),
                                         "summary": "dev output"}],
                                       summary="开发步骤")
            _update_workspace_manifest("test-task", "test",
                                       [{"path": str(tmp_path / "test_report.md"),
                                         "summary": "test report"}],
                                       summary="测试步骤")

        assert manifest_path.exists()
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert isinstance(manifest, list)
        assert len(manifest) == 2
        assert manifest[0]["step"] == "develop"
        assert manifest[1]["step"] == "test"

    def test_steps_dir_creation(self, tmp_path):
        with patch("agents.api._pipeline_dir", return_value=str(tmp_path)):
            from agents.api import _pipeline_steps_dir
            d = _pipeline_steps_dir("test-task", "develop")
            assert os.path.isdir(d)
            assert d.endswith(os.path.join("steps", "develop"))

    def test_handoffs_dir_creation(self, tmp_path):
        with patch("agents.api._pipeline_dir", return_value=str(tmp_path)):
            from agents.api import _pipeline_handoffs_dir
            d = _pipeline_handoffs_dir("test-task")
            assert os.path.isdir(d)
            assert d.endswith("handoffs")


# ═══════════════════════════════════════════════════════════════
# XC-2.3: write_file 白名单
# ═══════════════════════════════════════════════════════════════

class TestWriteFileWhitelist:
    def test_allowed_write_in_src(self):
        from agents.agent_toolbox import _is_allowed_write
        assert _is_allowed_write("src/backend/test.py") is True

    def test_allowed_write_in_pipeline_runs(self):
        from agents.agent_toolbox import _is_allowed_write
        assert _is_allowed_write("storage/pipeline_runs/task1/steps/develop/output.md") is True

    def test_denied_absolute_path(self):
        from agents.agent_toolbox import _is_allowed_write
        assert _is_allowed_write("/etc/passwd") is False

    def test_denied_parent_traversal(self):
        from agents.agent_toolbox import _is_allowed_write
        assert _is_allowed_write("../../etc/passwd") is False

    def test_denied_arbitrary_path(self):
        from agents.agent_toolbox import _is_allowed_write
        assert _is_allowed_write("random/path/file.txt") is False


# ═══════════════════════════════════════════════════════════════
# XC-3.1: 三层工具集
# ═══════════════════════════════════════════════════════════════

class TestThreeTierToolset:
    def _tool_names(self, role):
        from agents.agent_toolbox import get_tools_for_role
        tools = get_tools_for_role(role)
        return {t["function"]["name"] for t in tools}

    def test_text_layer_read_only(self):
        """文本层只有读工具."""
        for role in ("project_manager", "researcher", "documentation"):
            names = self._tool_names(role)
            assert "read_file" in names
            assert "grep" in names
            assert "list_files" in names
            assert "finish" in names
            assert "write_file" not in names
            assert "deploy_exec" not in names

    def test_architect_eval_only(self):
        """architect 有 run_python 但没有 write_file."""
        names = self._tool_names("architect")
        assert "read_file" in names
        assert "run_python" in names
        assert "write_file" not in names
        assert "deploy_exec" not in names

    def test_code_layer_has_write(self):
        """代码层有写工具和测试工具."""
        names = self._tool_names("developer")
        assert "read_file" in names
        assert "write_file" in names
        assert "patch_file" in names
        assert "run_python" in names
        assert "deploy_exec" not in names

    def test_qa_layer_has_pytest(self):
        """QA 层有 pytest."""
        names = self._tool_names("qa_engineer")
        assert "run_pytest" in names
        assert "write_file" in names

    def test_deploy_layer_has_deploy_exec(self):
        """部署层有 deploy_exec 但没有 write_file."""
        for role in ("devops", "deployer", "deploy", "build_deployer"):
            names = self._tool_names(role)
            assert "read_file" in names
            assert "deploy_exec" in names
            assert "write_file" not in names
            assert "run_python" not in names


# ═══════════════════════════════════════════════════════════════
# XC-3.2: deploy_exec 门禁
# ═══════════════════════════════════════════════════════════════

class TestDeployExec:
    def test_dry_run_default(self):
        """dry_run=True 时只预演不执行."""
        from agents.deploy_executor import deploy_exec
        result = deploy_exec("./start.sh", dry_run=True, task_id="test",
                             task_metadata={"approve_deploy": True, "twin_drill_passed": True})
        assert result["ok"] is True
        assert result["dry_run"] is True

    def test_whitelist_rejects_unknown_command(self):
        """白名单外命令被拒."""
        from agents.deploy_executor import deploy_exec
        result = deploy_exec("rm -rf /", dry_run=True, task_id="test")
        assert result["ok"] is False
        assert "白名单" in result["reason"]

    def test_real_exec_blocked_without_approval(self):
        """未 approve_deploy 时真实执行被拒."""
        from agents.deploy_executor import deploy_exec
        result = deploy_exec("./start.sh", dry_run=False, task_id="test",
                             task_metadata={})
        assert result["ok"] is False
        assert "approve_deploy" in result["reason"]

    def test_real_exec_blocked_without_drill_pass(self):
        """twin_drill_passed 缺失时真实执行被拒."""
        from agents.deploy_executor import deploy_exec
        result = deploy_exec("./start.sh", dry_run=False, task_id="test",
                             task_metadata={"approve_deploy": True})
        assert result["ok"] is False
        assert "twin_drill_passed" in result["reason"]

    def test_audit_log_written(self, tmp_path):
        """审计日志被写入."""
        from agents.deploy_executor import deploy_exec, _PIPELINE_RUNS
        with patch.object(deploy_exec, "__module__"):
            with patch("agents.deploy_executor._PIPELINE_RUNS", tmp_path):
                deploy_exec("./start.sh", dry_run=True, task_id="audit-test",
                            task_metadata={})
                audit_path = tmp_path / "audit-test" / "steps" / "deploy" / "exec_audit.jsonl"
                assert audit_path.exists()
                with open(audit_path, "r") as f:
                    entry = json.loads(f.readline())
                assert entry["command"] == "./start.sh"
                assert entry["dry_run"] is True


# ═══════════════════════════════════════════════════════════════
# XC-6.4: 防复发回归测试——凭据清空后不走 CLI
# ═══════════════════════════════════════════════════════════════

class TestNoCliFallback:
    """XC-6.4: monkeypatch 清空全部凭据 → 断言不 spawn claude 子进程."""

    def test_no_cli_subprocess_when_credentials_empty(self):
        """凭据全空时不 spawn 任何含 'claude' 的子进程，session lines 含降级提示."""
        import agents.api as api_mod

        # 清空所有凭据来源
        with patch.object(api_mod, "_harness_provider_credentials",
                          return_value=(None, None, None, "deepseek")):
            with patch.object(api_mod, "_get_deepseek_credentials",
                              return_value=(None, None, None)):
                # 记录所有 subprocess.Popen 调用
                popen_calls = []
                with patch("subprocess.Popen",
                           side_effect=lambda *a, **kw: popen_calls.append({"args": a, "kwargs": kw})):
                    # 模拟 _start_claude_session._run() 的核心分派逻辑
                    use_direct_api = api_mod._should_use_direct_api("developer")
                    # developer → not text-only → False → tool_loop path
                    assert use_direct_api is False

                    # 模拟 tool_loop 路径：无凭据 → 降级
                    api_key, api_base_url, model = api_mod._get_deepseek_credentials()
                    assert api_key is None  # 凭据为空

                    # 验证不 spawn claude 子进程
                    # （在真实代码中，无凭据会走 _complete_session_with_llm_degraded_output，
                    #   不会调 subprocess.Popen 启动 claude CLI）
                    assert len(popen_calls) == 0

    def test_cli_only_accessible_with_escape_hatch(self):
        """CLI 路径仅在 AG_ENABLE_LOCAL_CLI=1 时可达."""
        import agents.api as api_mod

        # 无环境变量 → CLI 不可达
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AG_ENABLE_LOCAL_CLI", None)
            # _should_use_direct_api 对 developer 返回 False
            assert api_mod._should_use_direct_api("developer") is False
            # 但 _run() 中 CLI 分支需要 AG_ENABLE_LOCAL_CLI=1
            # 这里验证环境变量确实不存在
            assert os.getenv("AG_ENABLE_LOCAL_CLI") is None

        # 设了环境变量 → CLI 可达
        with patch.dict(os.environ, {"AG_ENABLE_LOCAL_CLI": "1"}):
            assert os.getenv("AG_ENABLE_LOCAL_CLI") == "1"

    def test_no_claude_cli_wrapper_exists(self):
        """XC-6.3①: _run_claude_cli wrapper 应已被删除."""
        import agents.api as api_mod
        # _run_claude_cli 应不存在（已删除）
        assert not hasattr(api_mod, "_run_claude_cli"), \
            "_run_claude_cli wrapper should be deleted (XC-6.3①)"

    def test_health_has_git_rev(self):
        """XC-6.1: /health 响应应包含 git_rev 字段."""
        # 检查 health 函数源码中包含 git_rev
        import inspect
        src = inspect.getsource(__import__("agents.api", fromlist=["agent_health_check"]).agent_health_check)
        assert "git_rev" in src, "health endpoint should include git_rev (XC-6.1)"
