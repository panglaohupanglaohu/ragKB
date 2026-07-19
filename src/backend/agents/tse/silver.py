# -*- coding: utf-8 -*-
"""Silver-label generation for TSE training (LLM bootstrap).

Flow: plaza transcripts → constrained extract prompt → JSON skills → JSONL dataset.
Matches methodology §1.2 GPT-4 bootstrapping; uses ChatHarness in-product.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Union

from .dataset import ExtractionExample, PlazaExtractionDataset
from .schema import parse_skills_payload, validate_skill_fields
from .transcript import PlazaTranscript, parse_transcript

logger = logging.getLogger(__name__)

SILVER_SYSTEM = """You are a skill extraction expert creating silver training labels.
Given a multi-agent discussion transcript, extract ALL discoverable task-specific skills.

Each skill JSON fields (exact):
- name (max 50 chars)
- description (1-3 sentences)
- category: one of [automation, research, general, analysis, monitoring, development, domain_knowledge, digital_twin]
- instructions: step-by-step (3-10 steps, imperative)
- required_tools: list of tool names

Rules:
1. Only skills explicitly discussed or strongly implied.
2. No generic soft skills (communication, teamwork).
3. Instructions must be actionable.
4. If none, return {"skills": []}.
Output ONLY JSON: {"skills": [...]}"""


ChatFn = Callable[[str, str], Union[str, Awaitable[str]]]


def _format_transcript(tr: PlazaTranscript) -> str:
    return tr.format_for_prompt()


async def generate_silver_for_transcript(
    transcript: PlazaTranscript,
    *,
    harness=None,
    chat_fn: Optional[ChatFn] = None,
    source: str = "silver",
) -> ExtractionExample:
    """Call LLM to label one transcript."""
    text = _format_transcript(transcript)
    prompt = f"Transcript:\n{text}\n\nOutput skill JSON only."

    raw = ""
    if chat_fn is not None:
        import inspect
        out = chat_fn(prompt, SILVER_SYSTEM)
        if inspect.isawaitable(out):
            out = await out
        raw = out if isinstance(out, str) else str(getattr(out, "response", out))
    elif harness is not None:
        result = await harness.chat(
            prompt=prompt,
            system_prompt=SILVER_SYSTEM,
            agent_id="tse_silver",
        )
        raw = str(getattr(result, "response", None) or getattr(result, "content", None) or result)
    else:
        # Offline deterministic seed labels from heuristic topic keywords
        skills = _heuristic_silver(transcript)
        return ExtractionExample(
            discussion_id=transcript.discussion_id,
            transcript=transcript,
            skills=skills,
            source="heuristic_silver",
            verified=False,
        )

    skills, err = parse_skills_payload(raw, strict=False)
    if err:
        logger.warning("silver parse fail %s: %s", transcript.discussion_id, err)
        skills = _heuristic_silver(transcript)
        source = "heuristic_silver"
    return ExtractionExample(
        discussion_id=transcript.discussion_id,
        transcript=transcript,
        skills=skills,
        source=source,
        verified=False,
        meta={"raw_preview": (raw or "")[:500]},
    )


def _heuristic_silver(transcript: PlazaTranscript) -> List[Dict[str, Any]]:
    """Bootstrap labels without LLM (for offline train smoke)."""
    topic = transcript.topic or "讨论技能"
    body = " ".join(m.content for m in transcript.messages[:12])
    tools = []
    for key, tool in (
        ("aws", "aws_cli"), ("cloudwatch", "cloudwatch_api"), ("kubectl", "kubectl"),
        ("terraform", "terraform"), ("python", "python"), ("docker", "docker"),
    ):
        if key in body.lower() or key in topic.lower():
            tools.append(tool)
    cat = "automation"
    if any(k in (topic + body).lower() for k in ("research", "调研", "分析")):
        cat = "research"
    if any(k in (topic + body).lower() for k in ("monitor", "监控", "告警")):
        cat = "monitoring"
    name = (topic[:40] + " 技能") if topic else "讨论衍生技能"
    try:
        return [validate_skill_fields({
            "name": name[:50],
            "description": f"从讨论「{topic}」中萃取的可复用能力。",
            "category": cat,
            "instructions": (
                "1. 确认讨论中的触发条件与约束\n"
                "2. 按共识步骤执行核心动作\n"
                "3. 验证结果并记录工具与回滚点"
            ),
            "required_tools": tools,
            "confidence": 0.55,
            "scope": "public",
            "extraction_algorithm": "heuristic-silver",
        })]
    except Exception:
        return []


async def generate_silver_dataset(
    transcripts: Sequence[Union[PlazaTranscript, Dict[str, Any], str]],
    *,
    harness=None,
    chat_fn: Optional[ChatFn] = None,
    out_path: Optional[str | Path] = None,
) -> PlazaExtractionDataset:
    """Bootstrap silver dataset from many transcripts; optional JSONL write."""
    examples: List[ExtractionExample] = []
    for i, item in enumerate(transcripts):
        if isinstance(item, PlazaTranscript):
            tr = item
        elif isinstance(item, dict):
            if item.get("messages") or (item.get("transcript") or {}).get("messages"):
                tr_dict = item.get("transcript") or item
                tr = parse_transcript(
                    "",
                    source_title=str(tr_dict.get("topic") or item.get("topic") or f"disc-{i}"),
                    source_meta={
                        "messages": tr_dict.get("messages"),
                        "topic": tr_dict.get("topic"),
                        "source_discussion_id": item.get("discussion_id") or tr_dict.get("discussion_id") or f"d{i}",
                    },
                )
            else:
                tr = parse_transcript(
                    str(item.get("source_text") or item.get("text") or ""),
                    source_title=str(item.get("topic") or item.get("source_title") or f"disc-{i}"),
                    source_meta=item.get("source_meta") if isinstance(item.get("source_meta"), dict) else {},
                )
        else:
            tr = parse_transcript(str(item), source_title=f"disc-{i}")
        if not tr.discussion_id or tr.discussion_id == "unknown":
            tr.discussion_id = f"d{i}"
        ex = await generate_silver_for_transcript(tr, harness=harness, chat_fn=chat_fn)
        if ex.skills:
            examples.append(ex)
    ds = PlazaExtractionDataset(examples)
    if out_path:
        ds.save_jsonl(out_path)
        logger.info("wrote silver dataset %s n=%d", out_path, len(ds))
    return ds


def seed_demo_transcripts() -> List[PlazaTranscript]:
    """Built-in mini corpus for offline train demos."""
    samples = [
        (
            "AWS ES 扩缩容",
            """
[Round 0] 架构师Alpha (architect, signal=propose): 讨论 AWS ES 集群扩缩容，需要可复用自动扩缩技能。
[Round 1] 运维Gamma (devops, signal=supplement): 高峰 CPU 85% 触发扩容，工具 aws_cli 与 cloudwatch。
[Round 2] 运维Gamma (devops, signal=propose): 步骤：1. CloudWatch CPU>70% 5min 2. UpdateDomainConfig 增节点 3. 验证集群健康。
[Round 3] 安全Beta (security, signal=challenge): IAM 最小权限，禁止周五下午变配。
[Round 4] 架构师Alpha (architect, signal=summarize): 技能名 AWS ES Auto-Scaling，类别 automation。
""",
        ),
        (
            "K8s 滚动发布",
            """
[Round 0] 开发Dev (developer, signal=propose): 需要 Kubernetes 滚动发布与回滚技能。
[Round 1] 运维Ops (devops, signal=supplement): 使用 kubectl set image 与 rollout status，失败 rollout undo。
[Round 2] 运维Ops (devops, signal=propose): 步骤：1. 更新镜像 2. 观察 ready 3. 错误则 undo 4. 检查探针。
[Round 3] SRE (devops, signal=summarize): 类别 automation，工具 kubectl。
""",
        ),
        (
            "成本异常排查",
            """
[Round 0] 分析师 (data, signal=propose): 云成本突增如何定位？
[Round 1] 架构师 (architect, signal=supplement): 查 Cost Explorer 与标签缺口，再看 ES/EC2 闲置。
[Round 2] 分析师 (data, signal=propose): 步骤：1. 按服务拆分 2. 找无标签资源 3. 给出缩容或预留建议。
[Round 3] 产品 (pm, signal=summarize): 技能 云成本异常定位，类别 analysis。
""",
        ),
        (
            "日志告警降噪",
            """
[Round 0] SRE (devops, signal=propose): 告警太多需要降噪 runbook。
[Round 1] 运维 (devops, signal=supplement): Prometheus + Alertmanager 抑制与分组。
[Round 2] SRE (devops, signal=propose): 1. 定义 severity 2. 抑制连锁 3. 周回顾误报。
[Round 3] 架构师 (architect, signal=summarize): 技能 告警降噪，monitoring，工具 prometheus grafana。
""",
        ),
    ]
    out = []
    for i, (topic, text) in enumerate(samples):
        tr = parse_transcript(text, source_title=topic, source_meta={"source_discussion_id": f"seed-{i}"})
        tr.discussion_id = f"seed-{i}"
        out.append(tr)
    return out
