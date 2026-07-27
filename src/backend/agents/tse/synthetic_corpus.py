# -*- coding: utf-8 -*-
"""Versioned synthetic training corpora for attention scale sweeps.

Generates deterministic (topic, skill, evidence) samples without importing
anything under ``scripts/``. Sample sizes 12/24/48/96 are built from a
canonical definition list expanded with seeded paraphrases.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import FIELD_NAMES, TSEConfig
from .dataset import ExtractionExample, PlazaExtractionDataset
from .transcript import parse_transcript

CORPUS_VERSION = "tse-synthetic-corpus/v1"

# (topic, skill_name, category, tools, field_evidence_indices)
# Indices refer to the 5-slot transcript layout used by _render_transcript.
_BASE_DEFS: List[Tuple[str, str, str, List[str], Dict[str, List[int]]]] = [
    (
        "ES Instances Scaling",
        "ES Instances Scaling",
        "automation",
        ["monitor_api", "api_client", "scaling_tool"],
        {"name": [0, 4], "description": [0, 1], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "K8s Rolling Update",
        "K8s Rolling Update",
        "automation",
        ["kubectl", "helm"],
        {"name": [0, 3], "description": [0, 1], "category": [3], "tools": [1], "instructions": [1, 2]},
    ),
    (
        "Resource Cost Governance",
        "Resource Cost Governance",
        "domain_knowledge",
        ["cost_explorer", "tag_inspector", "report_generator"],
        {"name": [0, 3], "description": [0, 1], "category": [3], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "Alert Noise Reduction",
        "Alert Noise Reduction",
        "monitoring",
        ["prometheus", "alertmanager", "grafana"],
        {"name": [0, 3], "description": [0, 1], "category": [3], "tools": [1, 2], "instructions": [2]},
    ),
    (
        "OS Migration Strategy",
        "OS Migration Strategy",
        "automation",
        ["migration_toolkit", "test_runner", "rollback_script"],
        {"name": [0, 4], "description": [1], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "CI Pipeline Optimization",
        "CI Pipeline Optimization",
        "automation",
        ["build_cache", "parallel_runner", "artifact_store"],
        {"name": [0, 3], "description": [0], "category": [3], "tools": [1], "instructions": [1, 2]},
    ),
    (
        "Container Image Scanning",
        "Container Image Scanning",
        "monitoring",
        ["trivy", "clair", "grype"],
        {"name": [0, 3], "description": [0], "category": [3], "tools": [1], "instructions": [1, 2, 3]},
    ),
    (
        "Database Backup Automation",
        "Database Backup Automation",
        "automation",
        ["pg_dump", "mysqldump", "s3_sync", "encrypt_tool"],
        {"name": [0, 3], "description": [0, 1], "category": [3], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "Network Traffic Analysis",
        "Network Traffic Analysis",
        "monitoring",
        ["flow_dumper", "anomaly_detector", "siem_connector"],
        {"name": [0, 4], "description": [0, 1], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "Secret Rotation Automation",
        "Secret Rotation Automation",
        "automation",
        ["vault_cli", "lambda_rotator", "audit_logger"],
        {"name": [0, 4], "description": [0], "category": [4], "tools": [1, 3], "instructions": [2, 3]},
    ),
    (
        "Multi-Region DR Failover",
        "Multi-Region DR Failover",
        "domain_knowledge",
        ["dns_switcher", "replication_monitor", "failover_script", "rollback_tool"],
        {"name": [0, 4], "description": [0, 1], "category": [4], "tools": [1, 2], "instructions": [2, 3, 4]},
    ),
    (
        "API Rate Limiting",
        "API Rate Limiting Strategy",
        "automation",
        ["redis", "gateway_config", "monitoring_dash"],
        {"name": [0, 4], "description": [0], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "Log Aggregation Pipeline",
        "Log Aggregation Pipeline",
        "monitoring",
        ["fluentd", "elasticsearch", "kibana"],
        {"name": [0, 3], "description": [0], "category": [3], "tools": [0, 1], "instructions": [1, 2, 3]},
    ),
    (
        "Service Mesh Deployment",
        "Service Mesh Deployment",
        "automation",
        ["istioctl", "kubectl", "jaeger"],
        {"name": [0, 4], "description": [1], "category": [4], "tools": [1], "instructions": [1, 2, 3]},
    ),
    (
        "Configuration Drift Detection",
        "Config Drift Detection",
        "monitoring",
        ["terraform", "drift_detector", "remediation_script"],
        {"name": [0, 4], "description": [0, 1], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "Certificate Lifecycle Management",
        "Certificate Lifecycle Management",
        "automation",
        ["certbot", "acme_client", "notification_hook"],
        {"name": [0, 4], "description": [0], "category": [4], "tools": [0, 1], "instructions": [1, 2, 3]},
    ),
    (
        "Capacity Planning Forecast",
        "Capacity Planning Forecast",
        "domain_knowledge",
        ["forecast_model", "resource_tracker", "budget_allocator"],
        {"name": [0, 4], "description": [0, 1], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "Incident Response Playbook",
        "Incident Response Playbook",
        "domain_knowledge",
        ["pagerduty", "runbook_executor", "postmortem_tool"],
        {"name": [0, 4], "description": [0, 1], "category": [4], "tools": [0, 1], "instructions": [2, 3]},
    ),
    (
        "Infrastructure as Code Review",
        "Infra as Code Review",
        "automation",
        ["terraform", "opa_policy", "plan_analyzer"],
        {"name": [0, 4], "description": [0], "category": [4], "tools": [1], "instructions": [1, 2, 3]},
    ),
    (
        "Database Migration Toolkit",
        "DB Migration Toolkit",
        "automation",
        ["flyway", "liquibase", "schema_diff"],
        {"name": [0, 3], "description": [0], "category": [3], "tools": [0, 1], "instructions": [1, 2, 3]},
    ),
    # Extended bases toward 96
    (
        "Canary Release Control",
        "Canary Release Control",
        "automation",
        ["flag_service", "traffic_splitter", "metrics_probe"],
        {"name": [0, 4], "description": [0, 1], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "Queue Backlog Autoscale",
        "Queue Backlog Autoscale",
        "automation",
        ["sqs_client", "worker_scaler", "latency_probe"],
        {"name": [0, 4], "description": [1], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
    (
        "Feature Flag Cleanup",
        "Feature Flag Cleanup",
        "domain_knowledge",
        ["flag_inventory", "usage_scanner", "pr_bot"],
        {"name": [0, 3], "description": [0, 1], "category": [3], "tools": [1], "instructions": [2, 3]},
    ),
    (
        "Cold Storage Lifecycle",
        "Cold Storage Lifecycle",
        "automation",
        ["s3_lifecycle", "inventory_tool", "cost_report"],
        {"name": [0, 4], "description": [0], "category": [4], "tools": [1, 2], "instructions": [2, 3]},
    ),
]


def _clamp_evidence(
    evidence: Dict[str, List[int]], n_messages: int
) -> Dict[str, List[int]]:
    out: Dict[str, List[int]] = {}
    for field in FIELD_NAMES:
        idxs = []
        for i in evidence.get(field) or []:
            ii = int(i)
            if 0 <= ii < n_messages and ii not in idxs:
                idxs.append(ii)
        if not idxs:
            # ensure non-empty gold for training diagnostics when possible
            idxs = [0] if n_messages > 0 else []
        out[field] = idxs
    return out


def _render_transcript(
    topic: str,
    skill_name: str,
    category: str,
    tools: Sequence[str],
    evidence: Dict[str, List[int]],
    *,
    variant: int = 0,
) -> Tuple[str, int]:
    """Build a 4- or 5-utterance transcript; return (text, n_messages)."""
    tool_list = ", ".join(tools)
    # variant 0 → 5 messages; odd variants → 4 messages (drop last)
    n_messages = 4 if (variant % 2 == 1) else 5
    evidence = _clamp_evidence(evidence, n_messages)

    def has(field: str, idx: int) -> bool:
        return idx in (evidence.get(field) or [])

    lines: List[str] = []
    # u0
    parts = [f"架构师Alpha (architect, signal=propose): 讨论{topic}方案"]
    if has("name", 0):
        parts.append(f"技能名：{skill_name}")
    if has("description", 0):
        parts.append(f"用于解决{topic}相关场景的可复用流程")
    lines.append(" ".join(parts))

    # u1
    parts = [f"运维Gamma (devops, signal=supplement):"]
    if has("description", 1):
        parts.append(f"背景是{topic}在峰值与低峰负载下的治理需求。")
    if has("tools", 1):
        parts.append(f"核心工具：{tool_list}。")
    if has("instructions", 1):
        parts.append("先读取当前状态再做变更。")
    if len(parts) == 1:
        parts.append(f"补充{topic}上下文。")
    lines.append(" ".join(parts))

    # u2
    parts = [f"运维Gamma (devops, signal=propose):"]
    if has("tools", 2):
        parts.append(f"使用工具 {tool_list}。")
    if has("instructions", 2):
        parts.append(
            f"步骤：1. 检查状态 2. 制定{topic}方案 3. 执行 4. 验证 5. 记录。"
        )
    if len(parts) == 1:
        parts.append(f"提出{topic}操作步骤。")
    lines.append(" ".join(parts))

    # u3
    parts = [f"安全Beta (security, signal=challenge):"]
    if has("instructions", 3):
        parts.append("补充：权限最小化、禁止高危时段、准备回滚。")
    if has("name", 3) or has("category", 3):
        parts.append(f"确认能力 {skill_name} 与类别 {category}。")
    if len(parts) == 1:
        parts.append(f"需要关注{topic}安全约束。")
    lines.append(" ".join(parts))

    if n_messages == 5:
        parts = [f"架构师Alpha (architect, signal=summarize):"]
        if has("name", 4):
            parts.append(f"技能名 {skill_name}。")
        if has("category", 4):
            parts.append(f"类别 {category}。")
        if has("instructions", 4):
            parts.append("最终检查清单必须可审计。")
        if len(parts) == 1:
            parts.append(f"{skill_name}属于{category}类别。")
        lines.append(" ".join(parts))

    text = "\n".join(f"[Round {i}] {line}" for i, line in enumerate(lines))
    return text, n_messages


def _example_from_def(
    topic: str,
    skill_name: str,
    category: str,
    tools: Sequence[str],
    evidence: Dict[str, List[int]],
    *,
    sample_id: str,
    variant: int = 0,
) -> ExtractionExample:
    text, n_msg = _render_transcript(
        topic, skill_name, category, tools, evidence, variant=variant
    )
    tr = parse_transcript(text, source_title=topic)
    tr.discussion_id = sample_id
    gold = _clamp_evidence(evidence, n_msg)
    tr.meta = {
        "sample_id": sample_id,
        "field_evidence_indices": gold,
        "corpus_version": CORPUS_VERSION,
    }
    skill = {
        "name": skill_name,
        "description": f"从{topic}讨论中萃取的可复用能力",
        "category": category,
        "instructions": f"1. 确认{topic}触发条件\n2. 执行核心操作\n3. 验证结果",
        "required_tools": list(tools),
    }
    return ExtractionExample(
        discussion_id=sample_id,
        transcript=tr,
        skills=[skill],
        source="synthetic_corpus",
        verified=True,
        meta={"field_evidence_indices": gold, "corpus_version": CORPUS_VERSION},
    )


def build_synthetic_dataset(
    n: int,
    *,
    config: Optional[TSEConfig] = None,
    seed: int = 0,
) -> PlazaExtractionDataset:
    """Build first-n deterministic synthetic examples (n in 1..96+)."""
    if n <= 0:
        raise ValueError("n must be positive")
    examples: List[ExtractionExample] = []
    # Cycle bases with increasing variant for expansion beyond len(_BASE_DEFS)
    i = 0
    while len(examples) < n:
        base = _BASE_DEFS[i % len(_BASE_DEFS)]
        variant = i // len(_BASE_DEFS)
        topic, skill_name, category, tools, evidence = base
        # variant paraphrase: append suffix to skill for uniqueness
        if variant > 0:
            skill_name = f"{skill_name} v{variant + 1}"
            topic = f"{topic} #{variant + 1}"
        sample_id = f"synth-{len(examples):03d}"
        examples.append(
            _example_from_def(
                topic,
                skill_name,
                category,
                tools,
                evidence,
                sample_id=sample_id,
                variant=variant + seed,
            )
        )
        i += 1
    return PlazaExtractionDataset(examples, config=config)


def write_scale_fixtures(
    output_dir: str | Path,
    sizes: Sequence[int] = (12, 24, 48, 96),
) -> Dict[int, Path]:
    """Write versioned train JSONL files for each sample size. Returns size→path."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[int, Path] = {}
    for n in sizes:
        ds = build_synthetic_dataset(int(n))
        path = out_dir / f"train_scale_{int(n)}.jsonl"
        # custom line format with evidence for experiments loader compatibility
        lines = []
        for ex in ds.examples:
            gold = (ex.meta or {}).get("field_evidence_indices") or {}
            row = {
                "sample_id": ex.discussion_id,
                "topic": ex.transcript.topic,
                "messages": [
                    {
                        "speaker_name": m.speaker_name,
                        "role": m.role,
                        "ritual_signal": m.ritual_signal,
                        "round_number": m.round_number,
                        "content": m.content,
                    }
                    for m in ex.transcript.messages
                ],
                "field_evidence_indices": gold,
                "skills": ex.skills,
                "corpus_version": CORPUS_VERSION,
            }
            lines.append(json.dumps(row, ensure_ascii=False))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        paths[int(n)] = path
    # write manifest
    manifest = {
        "version": CORPUS_VERSION,
        "sizes": list(sizes),
        "files": {str(k): str(v.name) for k, v in paths.items()},
        "sha256": {
            str(k): hashlib.sha256(v.read_bytes()).hexdigest() for k, v in paths.items()
        },
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return paths
