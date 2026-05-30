# -*- coding: utf-8 -*-
"""Shared sandbox facade for Python and pytest execution."""

from __future__ import annotations

import json
import logging
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
        file_size_limit_kb=int(sandbox.get("file_size_limit_kb", 512) or 512),
        network_enabled=bool(sandbox.get("network_enabled", False)),
        docker_image=str(sandbox.get("docker_image", "agentsgroup-sandbox:python3.11") or "agentsgroup-sandbox:python3.11"),
    )


_sandbox_instance: Optional[Any] = None
_sandbox_signature: Optional[tuple] = None


def get_sandbox() -> Any:
    global _sandbox_instance, _sandbox_signature
    config = load_sandbox_config()
    signature = (
        config.mode,
        config.memory_limit_mb,
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
