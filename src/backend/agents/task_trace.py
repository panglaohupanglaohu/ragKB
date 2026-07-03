"""Task artifact and trace helpers shared by agent API routes."""

from __future__ import annotations

import difflib
import json
import os
from typing import Any, Dict, List, Optional


def project_root_path(current_file: str) -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(current_file)))))


def global_trace_events_path(project_root: str) -> str:
    return os.path.join(project_root, "storage", "trace_events.jsonl")


def build_trace_context(task) -> Dict[str, Any]:
    meta = task.metadata or {}
    trace_context = dict(meta.get("trace_context") or {})
    trace_context.update({
        "source": meta.get("source", "manual"),
        "discussion_id": meta.get("discussion_id", ""),
        "plaza_id": meta.get("plaza_id", ""),
        "pipeline_dir": meta.get("pipeline_dir", ""),
        "task_id": task.task_id,
        "team_id": task.team_id,
    })
    if meta.get("discussion_topic"):
        trace_context["discussion_topic"] = meta.get("discussion_topic")
    if meta.get("plan_revision") is not None:
        trace_context["plan_revision"] = meta.get("plan_revision")
    if meta.get("plan_item_index") is not None:
        trace_context["plan_item_index"] = meta.get("plan_item_index")
    if meta.get("evolution_item_ids"):
        trace_context["evolution_item_ids"] = list(meta.get("evolution_item_ids") or [])
    return trace_context


def append_jsonl(path: str, payload: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def trace_event_payload(task_id: str, event: Dict[str, Any], task=None) -> Dict[str, Any]:
    if task is None:
        return {"task_id": task_id, **event}
    return {
        "task_id": task_id,
        "team_id": task.team_id,
        "title": task.title,
        "source": (task.metadata or {}).get("source", "manual"),
        "trace_context": build_trace_context(task),
        **event,
    }


def persist_trace_event(
    task_id: str,
    event: Dict[str, Any],
    *,
    task=None,
    global_path: str,
) -> None:
    payload = trace_event_payload(task_id, event, task)
    pipeline_dir = (task.metadata or {}).get("pipeline_dir", "") if task else ""
    if pipeline_dir:
        append_jsonl(os.path.join(pipeline_dir, "trace_events.jsonl"), payload)
    append_jsonl(global_path, payload)


def workflow_summary(workflow: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "completed_steps": [s.get("key", "") for s in workflow if s.get("status") == "completed"],
        "failed_steps": [s.get("key", "") for s in workflow if s.get("status") == "failed"],
        "step_count": len(workflow),
    }


def collect_changed_files(workflow: List[Dict[str, Any]]) -> List[str]:
    files: List[str] = []
    for step in workflow:
        summary = step.get("_summary") or {}
        files.extend(summary.get("files_changed") or [])
        files.extend(step.get("deliverable_paths") or [])
        deploy_result = step.get("deploy_result") or {}
        for role_result in deploy_result.values():
            for item in role_result.get("applied", []) or []:
                if item.get("path"):
                    files.append(item["path"])
    return list(dict.fromkeys(files))


def extract_test_result(workflow: List[Dict[str, Any]]) -> Dict[str, Any]:
    for step in workflow:
        if step.get("key") == "test":
            summary = dict(step.get("_summary") or {})
            summary.setdefault("status", step.get("status", ""))
            return summary
    return {}


def build_diff_preview(workflow: List[Dict[str, Any]], *, repo_root: str) -> tuple[Dict[str, List[str]], str]:
    diff_by_file: Dict[str, List[str]] = {}
    preview_lines: List[str] = []
    for step in workflow:
        deploy_result = step.get("deploy_result") or {}
        for role_result in deploy_result.values():
            backups = {
                item.get("path"): item.get("backup")
                for item in role_result.get("backup", []) or []
                if item.get("path") and item.get("backup")
            }
            for item in role_result.get("applied", []) or []:
                rel_path = item.get("path", "")
                backup = backups.get(rel_path)
                if not rel_path or not backup:
                    continue
                current = os.path.join(repo_root, rel_path)
                if not os.path.isfile(current) or not os.path.isfile(backup):
                    continue
                try:
                    with open(backup, "r", encoding="utf-8", errors="replace") as f:
                        before = f.read().splitlines()
                    with open(current, "r", encoding="utf-8", errors="replace") as f:
                        after = f.read().splitlines()
                    diff_lines = list(difflib.unified_diff(
                        before,
                        after,
                        fromfile=f"a/{rel_path}",
                        tofile=f"b/{rel_path}",
                        lineterm="",
                    ))
                    diff_by_file[str(rel_path)] = diff_lines
                    preview_lines.extend(diff_lines[:80])
                except Exception:
                    continue
    return diff_by_file, "\n".join(preview_lines[:300])


def attach_task_execution_artifacts(
    task,
    *,
    artifact_dir: str,
    repo_root: str,
) -> Dict[str, Any]:
    meta = task.metadata or {}
    workflow = list(meta.get("workflow") or [])
    changed_files = collect_changed_files(workflow)
    test_result = extract_test_result(workflow)
    failed_steps = [s for s in workflow if s.get("status") == "failed"]
    build_outcome = "failed" if failed_steps else "completed"
    diff_by_file, patch_preview = build_diff_preview(workflow, repo_root=repo_root)
    artifacts = {
        "artifact_dir": artifact_dir,
        "changed_files": changed_files,
        "test_result": test_result,
        "workflow_summary": workflow_summary(workflow),
        "build_outcome": build_outcome,
        "trace_context": build_trace_context(task),
        "diff_by_file": diff_by_file,
        "patch_preview": patch_preview,
    }
    meta["execution_artifacts"] = artifacts
    meta["changed_files"] = changed_files
    meta["test_result"] = test_result
    meta["build_outcome"] = build_outcome
    if patch_preview:
        meta["patch_preview"] = patch_preview
    task.metadata = meta
    try:
        os.makedirs(artifact_dir, exist_ok=True)
        with open(os.path.join(artifact_dir, "trace_summary.json"), "w", encoding="utf-8") as f:
            json.dump(artifacts, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass
    return artifacts


def terminal_sync_state(artifacts: Dict[str, Any]) -> Dict[str, str]:
    failed_steps = artifacts["workflow_summary"]["failed_steps"]
    if failed_steps:
        return {
            "task_status": "failed",
            "task_error": f"workflow_failed:{failed_steps[0]}",
            "sync_status": "failed",
        }
    return {
        "task_status": "completed",
        "task_error": "",
        "sync_status": "completed",
    }


def evolution_sync_kwargs(task, artifacts: Dict[str, Any], *, sync_status: str) -> Dict[str, Any]:
    return {
        "task_id": task.task_id,
        "status": sync_status,
        "code_changes": artifacts["changed_files"],
        "artifact_dir": artifacts["artifact_dir"],
        "build_artifacts": artifacts,
        "error": task.error,
    }


def task_trace_summary(task, events: List[Dict[str, Any]], linked_evolution_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "task_id": task.task_id,
        "team_id": task.team_id,
        "title": task.title,
        "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        "source": (task.metadata or {}).get("source", "manual"),
        "trace_context": build_trace_context(task),
        "trace_event_count": len(events),
        "recent_trace_events": events[-10:],
        "linked_evolution_items": linked_evolution_items,
    }


def task_trace_events_payload(task, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"task_id": task.task_id, "count": len(events), "events": events}


def discussion_trace_summary_payload(
    *,
    team_id: str,
    discussion_id: str,
    task_summaries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "team_id": team_id,
        "discussion_id": discussion_id,
        "count": len(task_summaries),
        "tasks": task_summaries,
    }


def filter_trace_tasks(tasks: List[Any], *, team_id: str = "", source: str = "") -> List[Any]:
    filtered = []
    for task in tasks:
        if team_id and task.team_id != team_id:
            continue
        meta = task.metadata or {}
        if source and meta.get("source", "manual") != source:
            continue
        filtered.append(task)
    return filtered


def recent_trace_summaries(tasks: List[Any], *, limit: int, team_id: str = "", source: str = "") -> Dict[str, Any]:
    filtered = filter_trace_tasks(tasks, team_id=team_id, source=source)
    filtered.sort(key=lambda task: getattr(task, "created_at", ""), reverse=True)
    traces = []
    for task in filtered[:limit]:
        meta = task.metadata or {}
        workflow = meta.get("workflow", [])
        completed = sum(1 for step in workflow if step.get("status") == "completed")
        failed = sum(1 for step in workflow if step.get("status") == "failed")
        traces.append({
            "task_id": task.task_id,
            "team_id": task.team_id,
            "title": task.title,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
            "source": meta.get("source", "manual"),
            "trace_context": build_trace_context(task),
            "workflow_steps": len(workflow),
            "completed_steps": completed,
            "failed_steps": failed,
            "created_at": getattr(task, "created_at", ""),
        })
    return {"count": len(traces), "traces": traces}


def recent_trace_events(
    pipeline_events: Dict[str, List[Dict[str, Any]]],
    task_lookup,
    *,
    limit: int,
    team_id: str = "",
    source: str = "",
    event_type: str = "",
) -> Dict[str, Any]:
    events = []
    for task_id, task_events in pipeline_events.items():
        task = task_lookup(task_id)
        if task is None:
            continue
        meta = task.metadata or {}
        if team_id and task.team_id != team_id:
            continue
        if source and meta.get("source", "manual") != source:
            continue
        for event in task_events:
            if event_type and event.get("type") != event_type:
                continue
            events.append(trace_event_payload(task_id, event, task))
    events.sort(key=lambda event: event.get("ts", 0), reverse=True)
    return {"count": len(events[:limit]), "events": events[:limit]}


def trace_log_tail(path: str, *, limit: int, event_type: str = "") -> Dict[str, Any]:
    events: List[Dict[str, Any]] = []
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                    except Exception:
                        continue
                    if event_type and event.get("type") != event_type:
                        continue
                    events.append(event)
        except Exception:
            events = []
    events = events[-limit:]
    return {"count": len(events), "events": events}


def iter_trace_export_lines(summaries: Dict[str, Any], events: Dict[str, Any]):
    for trace in summaries["traces"]:
        yield json.dumps({"kind": "summary", **trace}, ensure_ascii=False) + "\n"
    for event in events["events"]:
        yield json.dumps({"kind": "event", **event}, ensure_ascii=False) + "\n"


def iter_trace_event_export_lines(events: Dict[str, Any]):
    for event in events["events"]:
        yield json.dumps(event, ensure_ascii=False) + "\n"
