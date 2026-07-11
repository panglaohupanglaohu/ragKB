"""deploy_executor.py — XC-3.2: 受控部署执行工具

deploy_exec(command, dry_run=True) 设计:
1. 白名单: 仅允许 config/deploy_allowlist.json 注册的命令模板
2. 默认 dry_run: 真实执行需 task.metadata.approve_deploy == true
3. 演练门禁: metadata.twin_drill_passed == true 时才允许真实执行
4. 审计: 每次调用写 steps/deploy/exec_audit.jsonl
5. 复用 subprocess 执行通道
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("DeployExecutor")

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ALLOWLIST_PATH = _PROJECT_ROOT / "config" / "deploy_allowlist.json"
_PIPELINE_RUNS = _PROJECT_ROOT / "storage" / "pipeline_runs"


def _load_allowlist() -> Dict[str, Any]:
    """热加载白名单配置."""
    try:
        with open(_ALLOWLIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("[DeployExec] allowlist load failed: %s", e)
        return {"commands": []}


def _match_allowlist(command: str, allowlist: Dict[str, Any]) -> Optional[str]:
    """检查命令是否匹配白名单模板。返回匹配的模板名或 None."""
    for entry in allowlist.get("commands", []):
        pattern = entry.get("pattern", "")
        # 简单前缀匹配 + 通配符支持
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            if command.startswith(prefix):
                return entry["name"]
        elif command.strip() == pattern.strip():
            return entry["name"]
        # 带参数的模板：检查命令是否以模板前缀开头
        elif "{" in pattern:
            # 提取模板前缀（第一个 { 之前的部分）
            prefix = pattern.split("{")[0].strip()
            if prefix and command.startswith(prefix):
                return entry["name"]
    return None


def _audit_log(task_id: str, entry: Dict[str, Any]) -> None:
    """写审计日志到 steps/deploy/exec_audit.jsonl."""
    try:
        deploy_dir = _PIPELINE_RUNS / task_id.replace("/", "_")[:60] / "steps" / "deploy"
        deploy_dir.mkdir(parents=True, exist_ok=True)
        audit_path = deploy_dir / "exec_audit.jsonl"
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("[DeployExec] audit log failed: %s", e)


def deploy_exec(
    command: str,
    dry_run: bool = True,
    task_id: str = "",
    task_metadata: Optional[Dict[str, Any]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """受控部署执行——白名单 + dry-run + 演练门禁 + 审计.

    Args:
        command: 要执行的命令字符串
        dry_run: True 时只预演不执行（默认）
        task_id: 任务 ID（用于审计日志路径）
        task_metadata: 任务元数据（检查 approve_deploy / twin_drill_passed）
        timeout: 执行超时秒数

    Returns:
        {ok, command, dry_run, exit_code, stdout, stderr, reason}
    """
    ts = datetime.now(timezone.utc).isoformat()
    task_metadata = task_metadata or {}

    # 1. 白名单检查
    allowlist = _load_allowlist()
    matched = _match_allowlist(command, allowlist)
    if not matched:
        result = {
            "ok": False,
            "command": command,
            "dry_run": dry_run,
            "reason": f"命令不在白名单中: {command}",
            "ts": ts,
        }
        _audit_log(task_id, result)
        return result

    # 2. dry_run 模式——只预演
    if dry_run:
        result = {
            "ok": True,
            "command": command,
            "dry_run": True,
            "matched_allowlist": matched,
            "reason": "dry-run 预演（未执行）",
            "ts": ts,
        }
        _audit_log(task_id, result)
        return result

    # 3. 真实执行门禁检查
    if not task_metadata.get("approve_deploy"):
        result = {
            "ok": False,
            "command": command,
            "dry_run": False,
            "reason": "未批准真实执行（metadata.approve_deploy != true）",
            "ts": ts,
        }
        _audit_log(task_id, result)
        return result

    if not task_metadata.get("twin_drill_passed"):
        result = {
            "ok": False,
            "command": command,
            "dry_run": False,
            "reason": "数字孪生演练未通过（metadata.twin_drill_passed != true）",
            "ts": ts,
        }
        _audit_log(task_id, result)
        return result

    # 4. 真实执行
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result = {
            "ok": proc.returncode == 0,
            "command": command,
            "dry_run": False,
            "matched_allowlist": matched,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[:4096],
            "stderr": proc.stderr[:2048],
            "ts": ts,
        }
    except subprocess.TimeoutExpired:
        result = {
            "ok": False,
            "command": command,
            "dry_run": False,
            "reason": f"执行超时 ({timeout}s)",
            "ts": ts,
        }
    except Exception as e:
        result = {
            "ok": False,
            "command": command,
            "dry_run": False,
            "reason": f"执行异常: {e}",
            "ts": ts,
        }

    _audit_log(task_id, result)
    return result
