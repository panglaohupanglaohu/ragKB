# -*- coding: utf-8 -*-
"""Security regression tests for lightweight sandboxed execution."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agents.agent_toolbox import tool_run_python, tool_run_pytest
from sandbox import api as sandbox_api_module
from sandbox.python_runner import (
    describe_sandbox_runtime,
    get_sandbox,
    load_sandbox_config,
    record_sandbox_self_check,
)
from sandbox.python_runner_lite import SandboxResult
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
                        "cpu_limit": 0.75,
                        "pids_limit": 32,
                        "tmpfs_tmp_mb": 48,
                        "tmpfs_run_mb": 12,
                        "nofile_limit": 128,
                        "nproc_limit": 32,
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
        assert config.cpu_limit == 0.75
        assert config.pids_limit == 32
        assert config.nofile_limit == 128

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

    def test_docker_pytest_command_includes_resource_limits(self, tmp_path):
        sandbox = DockerSandbox(
            image="sandbox:test",
            memory_limit_mb=384,
            cpu_limit=1.25,
            pids_limit=24,
            tmpfs_tmp_mb=96,
            tmpfs_run_mb=24,
            nofile_limit=96,
            nproc_limit=24,
        )

        command = sandbox.describe_command(cwd=Path(tmp_path), target="tests/test_models.py --co")

        assert "--memory 384m" in command
        assert "--cpus 1.25" in command
        assert "--pids-limit 24" in command
        assert "--ulimit nofile=96:96" in command
        assert "--ulimit nproc=24:24" in command
        assert "/tmp:size=96m,noexec,nosuid,nodev" in command
        assert "/run:size=24m,noexec,nosuid,nodev" in command
        assert "--ipc none" in command

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
        assert status["last_self_check"] == {}
        assert status["resource_limits"]["memory_limit_mb"] == 256
        assert status["resource_limits"]["pids_limit"] == 64

    def test_describe_sandbox_runtime_includes_last_self_check(self, monkeypatch, tmp_path):
        from sandbox import python_runner as runner_module

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"sandbox": {"mode": "lite"}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner_module, "_SETTINGS_PATH", settings_path)
        monkeypatch.setattr(runner_module, "_last_self_check", None)
        record_sandbox_self_check({"ok": True, "checks": {"python": {"ok": True}}})

        status = describe_sandbox_runtime()

        assert status["last_self_check"]["ok"] is True

    @pytest.mark.asyncio
    async def test_runtime_self_check_reports_python_and_pytest(self, monkeypatch):
        recorded = {}

        class StubSandbox:
            def run_python(self, code, *, cwd, timeout):
                assert "sandbox-ok" in code
                return SandboxResult(ok=True, exit_code=0, stdout="sandbox-ok\n")

            def run_pytest(self, target="", *, cwd, timeout):
                assert "test_main_health.py --co" in target
                return SandboxResult(ok=True, exit_code=0, stdout="collected 1 item\n")

        monkeypatch.setattr(sandbox_api_module, "get_sandbox", lambda: StubSandbox())
        monkeypatch.setattr(
            sandbox_api_module,
            "describe_sandbox_runtime",
            lambda: {"mode": "lite", "ready": True},
        )
        monkeypatch.setattr(
            sandbox_api_module,
            "record_sandbox_self_check",
            lambda payload: recorded.update(payload),
        )

        payload = await sandbox_api_module.run_runtime_self_check()

        assert payload["ok"] is True
        assert payload["runtime"]["mode"] == "lite"
        assert payload["checks"]["python"]["stdout"] == "sandbox-ok\n"
        assert payload["checks"]["pytest_collect"]["exit_code"] == 0
        assert recorded["ok"] is True
