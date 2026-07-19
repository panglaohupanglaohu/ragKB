# -*- coding: utf-8 -*-
"""从真实 task_id 取「最近一轮」LLM 消息，供 prepare 试跑（非 _simFixture）。

来源优先级：
  1. pipeline_runs/{task}/last_prepare_messages.json  — tool_loop/harness 落盘的原始 messages
  2. 最新 *_tool_trace.json  + 步骤 output.md / artifact
  3. 任务 title/description + 上下文摘要（最少可用）
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[4]
_PIPELINE = _REPO / "storage" / "pipeline_runs"
_TASKS = _REPO / "storage" / "tasks"
_SNAPSHOT_NAME = "last_prepare_messages.json"
_MAX_MSG_CHARS = 120_000  # 单轮总字符上限，避免试跑请求爆炸


def _pipeline_dir(task_id: str) -> Path:
    safe = (task_id or "").replace("/", "_")[:60]
    return _PIPELINE / safe


def snapshot_path(task_id: str) -> Path:
    return _pipeline_dir(task_id) / _SNAPSHOT_NAME


def save_prepare_messages(
    task_id: str,
    messages: List[Dict[str, Any]],
    *,
    team_id: str = "",
    agent_id: str = "",
    phase: str = "task",
    source: str = "tool_loop",
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """落盘 prepare 前的原始 messages（真省量对照源）."""
    tid = (task_id or "").strip()
    if not tid or not messages:
        return None
    try:
        pdir = _pipeline_dir(tid)
        pdir.mkdir(parents=True, exist_ok=True)
        # 轻量规范化 + 可选截断超长 content
        cleaned: List[Dict[str, Any]] = []
        total = 0
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "user")
            content = m.get("content")
            if not isinstance(content, str):
                content = str(content or "")
            # 保留 tool_call 等字段的浅拷贝
            row = {k: v for k, v in m.items() if k not in ("content",)}
            row["role"] = role
            if total + len(content) > _MAX_MSG_CHARS:
                remain = max(0, _MAX_MSG_CHARS - total)
                content = content[:remain] + f"\n…[snapshot truncated total>{_MAX_MSG_CHARS}]"
            row["content"] = content
            cleaned.append(row)
            total += len(content)
            if total >= _MAX_MSG_CHARS:
                break
        payload = {
            "task_id": tid,
            "team_id": team_id or "",
            "agent_id": agent_id or "",
            "phase": phase,
            "source": source,
            "saved_at": time.time(),
            "message_count": len(cleaned),
            "chars": total,
            "messages": cleaned,
            "extra": extra or {},
        }
        path = pdir / _SNAPSHOT_NAME
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)
    except Exception as e:
        logger.debug("save_prepare_messages: %s", e)
        return None


def _load_snapshot(task_id: str) -> Optional[Dict[str, Any]]:
    path = snapshot_path(task_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_task(task_id: str) -> Optional[Dict[str, Any]]:
    # exact / prefix match
    exact = _TASKS / f"{task_id}.json"
    if exact.is_file():
        try:
            return json.loads(exact.read_text(encoding="utf-8"))
        except Exception:
            pass
    # short ids like 8a5a38ee-85b
    for p in _TASKS.glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        tid = str(d.get("task_id") or p.stem)
        if tid == task_id or tid.startswith(task_id) or p.stem.startswith(task_id[:12]):
            return d
    return None


def _latest_tool_trace(task_id: str) -> Optional[Dict[str, Any]]:
    pdir = _pipeline_dir(task_id)
    if not pdir.is_dir():
        return None
    files = sorted(pdir.glob("*_tool_trace.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files:
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def _latest_step_output(task_id: str) -> Tuple[str, str]:
    """Return (label, text) from newest step output.md or root *.md artifact."""
    pdir = _pipeline_dir(task_id)
    candidates: List[Path] = []
    steps = pdir / "steps"
    if steps.is_dir():
        candidates.extend(steps.rglob("output.md"))
    candidates.extend(pdir.glob("*.md"))
    candidates = [c for c in candidates if c.is_file()]
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for c in candidates[:3]:
        try:
            text = c.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                return (c.name, text)
        except Exception:
            continue
    return ("", "")


def _live_session_lines(session_id: str) -> str:
    if not session_id:
        return ""
    try:
        from .. import api as agents_api
        sess = getattr(agents_api, "_claude_sessions", {}).get(session_id)
        if sess and sess.get("lines"):
            return "".join(list(sess.get("lines") or []))
    except Exception:
        pass
    return ""


def reconstruct_messages_from_task(task_id: str) -> Dict[str, Any]:
    """从落盘产物拼一套近似的 chat messages（无 snapshot 时用）."""
    task = _load_task(task_id) or {}
    title = str(task.get("title") or "")
    desc = str(task.get("description") or "")
    team_id = str(task.get("team_id") or "")
    agent_id = str(task.get("agent_id") or "")
    meta = task.get("metadata") or {}
    wf = meta.get("workflow") or []

    # 最近一步 session
    last_step: Dict[str, Any] = {}
    for s in reversed(wf if isinstance(wf, list) else []):
        if isinstance(s, dict) and (s.get("session_id") or s.get("status") in ("active", "completed", "done")):
            last_step = s
            if s.get("session_id"):
                break

    system = (
        f"你是任务执行 Agent。team={team_id or '—'} agent={agent_id or last_step.get('agent_id') or '—'}。"
        f"按任务目标交付，输出可验证结果。"
    )
    user = f"任务: {title or task_id}\n\n{desc}".strip()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    # tool_trace → 多轮 tool 结果
    trace = _latest_tool_trace(task_id)
    if trace:
        for i, entry in enumerate(trace.get("log") or []):
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or "tool"
            args = entry.get("args") or ""
            summary = entry.get("summary") or ""
            ok = entry.get("ok")
            messages.append({
                "role": "assistant",
                "content": f"[tool_call] {name}({args})"[:2000],
            })
            messages.append({
                "role": "tool",
                "content": (
                    f"tool={name} ok={ok}\n{summary}\n{args}"
                )[:8000],
            })
        if trace.get("summary"):
            messages.append({
                "role": "assistant",
                "content": str(trace.get("summary"))[:4000],
            })

    # 步骤产出 / session 日志
    label, out_text = _latest_step_output(task_id)
    if out_text:
        messages.append({
            "role": "tool",
            "content": f"[step_output:{label}]\n{out_text[:20000]}",
        })
    else:
        live = _live_session_lines(str(last_step.get("session_id") or ""))
        if live:
            messages.append({
                "role": "tool",
                "content": f"[session_lines]\n{live[:20000]}",
            })

    # 上下文 manifest 提示（短）
    pdir = _pipeline_dir(task_id)
    man = pdir / "_context" / "_manifest.md"
    if man.is_file():
        try:
            messages.append({
                "role": "system",
                "content": "[pipeline_context]\n" + man.read_text(encoding="utf-8", errors="replace")[:3000],
            })
        except Exception:
            pass

    return {
        "ok": True,
        "source": "reconstructed",
        "task_id": task.get("task_id") or task_id,
        "team_id": team_id,
        "agent_id": agent_id or str(last_step.get("agent_id") or ""),
        "title": title,
        "message_count": len(messages),
        "chars": sum(len(str(m.get("content") or "")) for m in messages),
        "messages": messages,
        "hints": {
            "has_tool_trace": bool(trace),
            "has_step_output": bool(out_text),
            "last_step": {
                "key": last_step.get("key") or last_step.get("step"),
                "session_id": last_step.get("session_id"),
                "status": last_step.get("status"),
            },
        },
    }


def load_task_messages(task_id: str) -> Dict[str, Any]:
    """优先 snapshot，否则 reconstruct。"""
    tid = (task_id or "").strip()
    if not tid:
        return {"ok": False, "error": "task_id required", "messages": []}

    snap = _load_snapshot(tid)
    if snap and snap.get("messages"):
        return {
            "ok": True,
            "source": "snapshot",
            "task_id": snap.get("task_id") or tid,
            "team_id": snap.get("team_id") or "",
            "agent_id": snap.get("agent_id") or "",
            "title": "",
            "message_count": len(snap["messages"]),
            "chars": int(snap.get("chars") or 0),
            "saved_at": snap.get("saved_at"),
            "snapshot_source": snap.get("source"),
            "messages": snap["messages"],
            "hints": {"path": str(snapshot_path(tid))},
        }

    # try resolve full task_id from short prefix
    task = _load_task(tid)
    full_id = str((task or {}).get("task_id") or tid)
    if full_id != tid:
        snap = _load_snapshot(full_id)
        if snap and snap.get("messages"):
            return {
                "ok": True,
                "source": "snapshot",
                "task_id": full_id,
                "team_id": snap.get("team_id") or "",
                "agent_id": snap.get("agent_id") or "",
                "message_count": len(snap["messages"]),
                "chars": int(snap.get("chars") or 0),
                "saved_at": snap.get("saved_at"),
                "snapshot_source": snap.get("source"),
                "messages": snap["messages"],
                "hints": {"path": str(snapshot_path(full_id))},
            }

    rec = reconstruct_messages_from_task(full_id)
    if not rec.get("messages"):
        rec["ok"] = False
        rec["error"] = "no_messages_for_task"
    return rec


def list_recent_tasks(limit: int = 20, team_id: str = "") -> List[Dict[str, Any]]:
    """任务列表（带是否有 snapshot / pipeline）."""
    items: List[Dict[str, Any]] = []
    files = sorted(_TASKS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files:
        if len(items) >= limit:
            break
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        tid = str(d.get("task_id") or p.stem)
        if team_id and str(d.get("team_id") or "") != team_id:
            continue
        has_snap = snapshot_path(tid).is_file()
        pdir = _pipeline_dir(tid)
        has_trace = any(pdir.glob("*_tool_trace.json")) if pdir.is_dir() else False
        items.append({
            "task_id": tid,
            "team_id": d.get("team_id") or "",
            "title": (d.get("title") or "")[:80],
            "status": d.get("status") or "",
            "updated_at": p.stat().st_mtime,
            "has_snapshot": has_snap,
            "has_pipeline": pdir.is_dir(),
            "has_tool_trace": has_trace,
            "preferred": has_snap or has_trace,
        })
    # preferred first
    items.sort(key=lambda x: (not x["preferred"], -float(x["updated_at"] or 0)))
    return items[:limit]
