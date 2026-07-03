# -*- coding: utf-8 -*-
"""Docker-backed sandbox integration tests."""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from sandbox.python_runner_docker import DockerSandbox

ROOT_DIR = Path(__file__).resolve().parents[3]
_DOCKER_TESTS_ENABLED = os.getenv("AG_SANDBOX_DOCKER_TESTS", "").lower() in {"1", "true", "yes"}

pytestmark = pytest.mark.skipif(
    not _DOCKER_TESTS_ENABLED,
    reason="set AG_SANDBOX_DOCKER_TESTS=1 to run docker sandbox integration tests",
)


def _docker_ready() -> bool:
    if not shutil.which("docker"):
        return False
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


@pytest.fixture(scope="module")
def sandbox_image_tag() -> str:
    if not _docker_ready():
        pytest.skip("docker executable or daemon is not available")

    tag = os.getenv("AG_SANDBOX_DOCKER_IMAGE", f"agentsgroup-sandbox:test-{uuid.uuid4().hex[:8]}")
    subprocess.run(
        ["bash", str(ROOT_DIR / "scripts" / "build_sandbox_image.sh"), tag],
        cwd=ROOT_DIR,
        check=True,
    )
    yield tag
    subprocess.run(
        ["docker", "image", "rm", "-f", tag],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def test_build_script_self_check_passes(sandbox_image_tag: str):
    result = subprocess.run(
        [
            "bash",
            str(ROOT_DIR / "scripts" / "build_sandbox_image.sh"),
            sandbox_image_tag,
            "--self-check",
        ],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_docker_sandbox_runs_python_code(sandbox_image_tag: str):
    sandbox = DockerSandbox(image=sandbox_image_tag)

    result = sandbox.run_python("print('sandbox-ok')", cwd=ROOT_DIR, timeout=10)

    assert result.ok is True
    assert result.exit_code == 0
    assert "sandbox-ok" in result.stdout


def test_docker_sandbox_runs_pytest_smoke(sandbox_image_tag: str):
    sandbox = DockerSandbox(image=sandbox_image_tag)

    result = sandbox.run_pytest("src/backend/tests/test_sandbox_smoke.py", cwd=ROOT_DIR, timeout=30)

    assert result.ok is True
    assert result.exit_code == 0
    assert "1 passed" in result.stdout
