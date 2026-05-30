# -*- coding: utf-8 -*-
"""Docker-backed sandbox for stronger Python / pytest isolation."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from .python_runner_lite import LiteSandbox, SandboxResult


class DockerSandbox(LiteSandbox):
    """Execute Python and pytest inside an ephemeral Docker container."""

    def __init__(
        self,
        *,
        image: str = "agentsgroup-sandbox:python3.11",
        docker_executable: str = "docker",
        max_output_bytes: int = 32 * 1024,
        memory_limit_mb: int = 256,
        cpu_limit: float = 0.5,
        file_size_limit_kb: int = 512,
        network_enabled: bool = False,
    ) -> None:
        super().__init__(
            python_executable="python3",
            max_output_bytes=max_output_bytes,
            memory_limit_mb=memory_limit_mb,
            file_size_limit_kb=file_size_limit_kb,
            network_enabled=network_enabled,
        )
        self.image = image
        self.docker_executable = docker_executable
        self.cpu_limit = cpu_limit

    def run_python(self, code: str, *, cwd: Path, timeout: int = 30) -> SandboxResult:
        try:
            self._validate_python_code(code)
        except Exception as exc:
            return SandboxResult(ok=False, error=str(exc))

        if not shutil.which(self.docker_executable):
            return SandboxResult(ok=False, error=f"{self.docker_executable} executable not found")
        if not self._docker_image_available():
            return SandboxResult(
                ok=False,
                error=(
                    f"Docker image '{self.image}' not found; "
                    "build it with ./scripts/build_sandbox_image.sh"
                ),
            )

        with tempfile.TemporaryDirectory(prefix="agentsgroup-sbx-") as tmpdir:
            script_path = Path(tmpdir) / "user_code.py"
            script_path.write_text(code, encoding="utf-8")
            cmd = self._build_docker_command(
                cwd=cwd,
                extra_mounts=[f"{script_path}:/sandbox/user_code.py:ro"],
                allow_network=self.network_enabled,
                inner_cmd=["python3", "/sandbox/user_code.py"],
            )
            return self._run_subprocess(cmd, cwd=cwd, timeout=timeout)

    def run_pytest(self, target: str = "", *, cwd: Path, timeout: int = 120) -> SandboxResult:
        try:
            extra_args = self._normalize_pytest_target(target)
        except Exception as exc:
            return SandboxResult(ok=False, error=str(exc))

        if not shutil.which(self.docker_executable):
            return SandboxResult(ok=False, error=f"{self.docker_executable} executable not found")
        if not self._docker_image_available():
            return SandboxResult(
                ok=False,
                error=(
                    f"Docker image '{self.image}' not found; "
                    "build it with ./scripts/build_sandbox_image.sh"
                ),
            )

        inner_cmd = [
            "python3",
            "-m",
            "pytest",
            "-q",
            "--tb=short",
            "--maxfail=5",
            "-p",
            "no:cacheprovider",
            *extra_args,
        ]
        cmd = self._build_docker_command(
            cwd=cwd,
            extra_mounts=[],
            allow_network=False,
            inner_cmd=inner_cmd,
        )
        return self._run_subprocess(cmd, cwd=cwd, timeout=timeout)

    def _build_docker_command(
        self,
        *,
        cwd: Path,
        extra_mounts: List[str],
        allow_network: bool,
        inner_cmd: List[str],
    ) -> List[str]:
        cmd = [
            self.docker_executable,
            "run",
            "--rm",
            "--memory",
            f"{self.memory_limit_mb}m",
            "--cpus",
            str(self.cpu_limit),
            "--read-only",
            "--tmpfs",
            "/tmp:size=64m,noexec,nosuid,nodev",
            "--tmpfs",
            "/run:size=16m,noexec,nosuid,nodev",
            "--pids-limit",
            "64",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--user",
            "65534:65534",
            "--network",
            "bridge" if allow_network else "none",
            "-e",
            "HOME=/tmp",
            "-e",
            "PYTHONUNBUFFERED=1",
            "-e",
            "PYTHONPATH=/workspace",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            "-e",
            "PYTHONNOUSERSITE=1",
            "-e",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
            "-v",
            f"{cwd}:/workspace:ro",
            "-w",
            "/workspace",
        ]
        for mount in extra_mounts:
            cmd.extend(["-v", mount])
        cmd.append(self.image)
        cmd.extend(inner_cmd)
        return cmd

    def describe_command(self, *, cwd: Path, target: str = "") -> str:
        """Testing helper: render the docker command for a pytest run."""
        cmd = self._build_docker_command(
            cwd=cwd,
            extra_mounts=[],
            allow_network=False,
            inner_cmd=[
                "python3",
                "-m",
                "pytest",
                "-q",
                "--tb=short",
                "--maxfail=5",
                "-p",
                "no:cacheprovider",
                *self._normalize_pytest_target(target),
            ],
        )
        return shlex.join(cmd)

    def _docker_image_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.docker_executable, "image", "inspect", self.image],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            return False
        return result.returncode == 0
