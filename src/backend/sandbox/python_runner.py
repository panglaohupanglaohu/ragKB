# -*- coding: utf-8 -*-
"""Shared sandbox facade for Python and pytest execution."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .python_runner_docker import DockerSandbox
from .python_runner_lite import LiteSandbox

logger = logging.getLogger(__name__)

_SETTINGS_PATH = Path(__file__).resolve().parents[3] / "config" / "settings.json"


@dataclass
class SandboxConfig:
    mode: str = "lite"
    memory_limit_mb: int = 256
    cpu_limit: float = 0.5
    pids_limit: int = 64
    tmpfs_tmp_mb: int = 64
    tmpfs_run_mb: int = 16
    nofile_limit: int = 256
    nproc_limit: int = 64
    file_size_limit_kb: int = 512
    network_enabled: bool = False
    docker_image: str = "agentsgroup-sandbox:python3.11"


def load_sandbox_config() -> SandboxConfig:
    if not _SETTINGS_PATH.exists():
        return SandboxConfig()
    try:
        raw = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to read sandbox config: %s", exc)
        return SandboxConfig()

    sandbox = raw.get("sandbox", {}) if isinstance(raw, dict) else {}
    return SandboxConfig(
        mode=str(sandbox.get("mode", "lite") or "lite"),
        memory_limit_mb=int(sandbox.get("memory_limit_mb", 256) or 256),
        cpu_limit=float(sandbox.get("cpu_limit", 0.5) or 0.5),
        pids_limit=int(sandbox.get("pids_limit", 64) or 64),
        tmpfs_tmp_mb=int(sandbox.get("tmpfs_tmp_mb", 64) or 64),
        tmpfs_run_mb=int(sandbox.get("tmpfs_run_mb", 16) or 16),
        nofile_limit=int(sandbox.get("nofile_limit", 256) or 256),
        nproc_limit=int(sandbox.get("nproc_limit", 64) or 64),
        file_size_limit_kb=int(sandbox.get("file_size_limit_kb", 512) or 512),
        network_enabled=bool(sandbox.get("network_enabled", False)),
        docker_image=str(sandbox.get("docker_image", "agentsgroup-sandbox:python3.11") or "agentsgroup-sandbox:python3.11"),
    )


_sandbox_instance: Optional[Any] = None
_sandbox_signature: Optional[tuple] = None
_last_self_check: Optional[dict] = None


def record_sandbox_self_check(result: dict) -> None:
    global _last_self_check
    _last_self_check = dict(result)


def describe_sandbox_runtime() -> dict:
    """Return the current sandbox runtime readiness and config summary."""
    config = load_sandbox_config()
    payload = {
        "mode": config.mode,
        "memory_limit_mb": config.memory_limit_mb,
        "file_size_limit_kb": config.file_size_limit_kb,
        "network_enabled": config.network_enabled,
        "docker_image": config.docker_image,
        "resource_limits": {
            "memory_limit_mb": config.memory_limit_mb,
            "cpu_limit": config.cpu_limit,
            "pids_limit": config.pids_limit,
            "tmpfs_tmp_mb": config.tmpfs_tmp_mb,
            "tmpfs_run_mb": config.tmpfs_run_mb,
            "nofile_limit": config.nofile_limit,
            "nproc_limit": config.nproc_limit,
            "file_size_limit_kb": config.file_size_limit_kb,
            "network_enabled": config.network_enabled,
        },
        "ready": True,
    }
    if config.mode != "docker":
        payload.update(
            {
                "docker_available": False,
                "image_available": False,
                "build_command": "./scripts/build_sandbox_image.sh",
                "last_self_check": dict(_last_self_check or {}),
            }
        )
        return payload

    docker_available = bool(shutil.which("docker"))
    image_available = False
    if docker_available:
        sandbox = DockerSandbox(
            image=config.docker_image,
            memory_limit_mb=config.memory_limit_mb,
            cpu_limit=config.cpu_limit,
            pids_limit=config.pids_limit,
            tmpfs_tmp_mb=config.tmpfs_tmp_mb,
            tmpfs_run_mb=config.tmpfs_run_mb,
            nofile_limit=config.nofile_limit,
            nproc_limit=config.nproc_limit,
            file_size_limit_kb=config.file_size_limit_kb,
            network_enabled=config.network_enabled,
        )
        image_available = sandbox._docker_image_available()
        payload["resource_limits"] = sandbox.describe_limits()

    payload.update(
        {
            "docker_available": docker_available,
            "image_available": image_available,
            "build_command": "./scripts/build_sandbox_image.sh",
            "ready": docker_available and image_available,
            "last_self_check": dict(_last_self_check or {}),
        }
    )
    return payload


def get_sandbox() -> Any:
    global _sandbox_instance, _sandbox_signature
    config = load_sandbox_config()
    signature = (
        config.mode,
        config.memory_limit_mb,
        config.cpu_limit,
        config.pids_limit,
        config.tmpfs_tmp_mb,
        config.tmpfs_run_mb,
        config.nofile_limit,
        config.nproc_limit,
        config.file_size_limit_kb,
        config.network_enabled,
        config.docker_image,
    )
    if _sandbox_instance is not None and _sandbox_signature == signature:
        return _sandbox_instance

    if config.mode == "docker":
        _sandbox_instance = DockerSandbox(
            image=config.docker_image,
            memory_limit_mb=config.memory_limit_mb,
            cpu_limit=config.cpu_limit,
            pids_limit=config.pids_limit,
            tmpfs_tmp_mb=config.tmpfs_tmp_mb,
            tmpfs_run_mb=config.tmpfs_run_mb,
            nofile_limit=config.nofile_limit,
            nproc_limit=config.nproc_limit,
            file_size_limit_kb=config.file_size_limit_kb,
            network_enabled=config.network_enabled,
        )
    else:
        if config.mode != "lite":
            logger.warning("Sandbox mode '%s' not implemented, falling back to lite", config.mode)
        _sandbox_instance = LiteSandbox(
            memory_limit_mb=config.memory_limit_mb,
            file_size_limit_kb=config.file_size_limit_kb,
            network_enabled=config.network_enabled,
        )
    _sandbox_signature = signature
    return _sandbox_instance
