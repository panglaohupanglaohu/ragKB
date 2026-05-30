# -*- coding: utf-8 -*-
"""Security regression tests for lightweight sandboxed execution."""

from __future__ import annotations

from agents.agent_toolbox import tool_run_python, tool_run_pytest


class TestRunPythonSandbox:
    def test_blocks_os_system(self):
        result = tool_run_python("import os\nos.system('echo nope')")
        assert result["ok"] is False
        assert "blocked" in result["error"].lower()

    def test_blocks_socket_import(self):
        result = tool_run_python("import socket\nprint('nope')")
        assert result["ok"] is False
        assert "blocked dangerous import" in result["error"]

    def test_blocks_file_write(self):
        result = tool_run_python("open('sandbox_canary.txt', 'w').write('x')")
        assert result["ok"] is False
        assert "file writes" in result["error"].lower()

    def test_kills_infinite_loop_on_timeout(self):
        result = tool_run_python("while True:\n    pass", timeout=1)
        assert result["ok"] is False
        assert "timeout" in result["error"].lower()


class TestRunPytestSandbox:
    def test_blocks_path_escape(self):
        result = tool_run_pytest("../tests/test_models.py")
        assert result["ok"] is False
        assert "blocked pytest target path" in result["error"]

    def test_collect_only_still_works(self):
        result = tool_run_pytest("tests/test_models.py --co")
        assert result["ok"] is True
