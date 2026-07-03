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
        assert result["error"] == "unknown tool: unknown_tool"

    def test_dispatch_bad_json_args(self):
        result = dispatch_tool_call("read_file", "not json")
        assert result["ok"] is False
        assert result["error"].startswith("bad arguments JSON:")

    def test_dispatch_bad_kwargs(self):
        result = dispatch_tool_call(
            "read_file",
            json.dumps({"path": "tests/__init__.py", "extra_bad_kwarg": True}),
        )
        assert result["ok"] is False
        assert result["error"].startswith("bad arguments:")


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
