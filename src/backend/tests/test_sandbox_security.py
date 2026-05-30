# -*- coding: utf-8 -*-
"""Security regression tests for lightweight sandboxed execution."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agents.agent_toolbox import tool_run_python, tool_run_pytest
from sandbox.python_runner import describe_sandbox_runtime, get_sandbox, load_sandbox_config
from sandbox.python_runner_docker import DockerSandbox


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


class TestSandboxModeSelection:
    def test_loads_docker_mode_from_settings(self, monkeypatch, tmp_path):
        from sandbox import python_runner as runner_module

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "sandbox": {
                        "mode": "docker",
                        "docker_image": "custom-sandbox:latest",
                        "memory_limit_mb": 128,
                        "file_size_limit_kb": 256,
                        "network_enabled": False,
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner_module, "_SETTINGS_PATH", settings_path)

        config = load_sandbox_config()

        assert config.mode == "docker"
        assert config.docker_image == "custom-sandbox:latest"

    def test_get_sandbox_returns_docker_instance(self, monkeypatch, tmp_path):
        from sandbox import python_runner as runner_module

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"sandbox": {"mode": "docker"}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner_module, "_SETTINGS_PATH", settings_path)
        monkeypatch.setattr(runner_module, "_sandbox_instance", None)
        monkeypatch.setattr(runner_module, "_sandbox_signature", None)

        sandbox = get_sandbox()

        assert isinstance(sandbox, DockerSandbox)

    def test_docker_mode_fails_closed_when_docker_missing(self, monkeypatch, tmp_path):
        sandbox = DockerSandbox()
        monkeypatch.setattr("shutil.which", lambda name: None)

        result = sandbox.run_python("print('hi')", cwd=Path(tmp_path), timeout=1)

        assert result.ok is False
        assert "not found" in result.error.lower()

    def test_docker_mode_fails_closed_when_image_missing(self, monkeypatch, tmp_path):
        sandbox = DockerSandbox(image="sandbox:missing")
        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/docker")
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1),
        )

        result = sandbox.run_python("print('hi')", cwd=Path(tmp_path), timeout=1)

        assert result.ok is False
        assert "build_sandbox_image.sh" in result.error

    def test_docker_pytest_command_uses_read_only_mount_and_no_network(self, tmp_path):
        sandbox = DockerSandbox(image="sandbox:test")

        command = sandbox.describe_command(cwd=Path(tmp_path), target="tests/test_models.py --co")

        assert "--read-only" in command
        assert "--network none" in command
        assert "--cap-drop ALL" in command
        assert "--security-opt no-new-privileges" in command
        assert "--user 65534:65534" in command
        assert "sandbox:test" in command

    def test_describe_sandbox_runtime_reports_docker_readiness(self, monkeypatch, tmp_path):
        from sandbox import python_runner as runner_module

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"sandbox": {"mode": "docker", "docker_image": "sandbox:test"}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner_module, "_SETTINGS_PATH", settings_path)
        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/docker")
        monkeypatch.setattr(DockerSandbox, "_docker_image_available", lambda self: True)

        status = describe_sandbox_runtime()

        assert status["mode"] == "docker"
        assert status["docker_available"] is True
        assert status["image_available"] is True
        assert status["ready"] is True
        assert status["build_command"] == "./scripts/build_sandbox_image.sh"
