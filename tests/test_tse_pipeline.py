# -*- coding: utf-8 -*-
"""Unit tests for TSE (TCN-Skill-Extractor) stages 1–4."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "src" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agents.tse import (  # noqa: E402
    TSEConfig,
    TSEPipeline,
    extract_skill_moments,
    parse_skills_payload,
    parse_transcript,
    validate_skill_fields,
)
from agents.tse.tcn import TCNTemporalModule  # noqa: E402


SAMPLE_TRANSCRIPT = """
[Round 0] 架构师Alpha (architect, signal=propose): 今天讨论AWS ES集群的扩缩容策略。需要定义可复用的自动扩缩技能。
[Round 1] 运维专家Gamma (devops, signal=supplement): 从运维角度，高峰期CPU到85%应触发扩容。工具用 aws_cli 和 cloudwatch。
[Round 2] 运维专家Gamma (devops, signal=propose): 技能步骤：1. 配置CloudWatch告警 CPU>70% 持续5min 2. 调用ES UpdateDomainConfig 增加节点 3. 验证集群健康。
[Round 3] 安全官Beta (security, signal=challenge): 扩容时注意IAM权限最小原则，禁止周五下午变配。
[Round 4] 架构师Alpha (architect, signal=summarize): 共识技能名称 AWS ES Auto-Scaling，类别 automation，指令如上。
"""


def test_parse_transcript_round_format():
    tr = parse_transcript(SAMPLE_TRANSCRIPT, source_title="ES扩缩容")
    assert tr.topic == "ES扩缩容"
    assert len(tr.messages) >= 4
    assert tr.messages[0].role == "architect"
    assert "扩缩" in tr.messages[0].content or "ES" in tr.messages[0].content


def test_parse_transcript_paragraph_fallback():
    text = "第一段讲监控告警配置。\n\n第二段讲自动扩缩容步骤与验证。\n\n第三段讲回滚预案。"
    tr = parse_transcript(text, source_title="doc")
    assert len(tr.messages) >= 2
    assert tr.messages[0].role == "document"


def test_tcn_receptive_field():
    assert TCNTemporalModule.receptive_field(3, 3) == 15  # 1+2*(1+2+4)


def test_encode_stages_shapes_and_focus():
    pipe = TSEPipeline(TSEConfig(top_k_utterances=4))
    tr = parse_transcript(SAMPLE_TRANSCRIPT, source_title="ES扩缩容")
    stages = pipe.encode_stages(tr)
    n = len(tr.messages)
    assert stages["embeddings"].shape[0] == n
    assert stages["temporal"].shape == (n, pipe.config.tcn_hidden_dim)
    assert stages["attn_weights"].shape[0] == 5  # five field queries
    assert stages["attn_weights"].shape[1] == n
    assert stages["focus_indices"]
    assert set(stages["focus_indices"]).issubset(set(range(n)))
    for field in ("name", "description", "category", "tools", "instructions"):
        assert field in stages["field_focus"]
        assert field in stages["skill_repr"]


def test_extract_skill_moments_sync_api():
    out = extract_skill_moments(SAMPLE_TRANSCRIPT, source_title="ES")
    assert out["utterance_count"] >= 4
    assert isinstance(out["focus_indices"], list)
    assert "transcript_preview" in out


def test_schema_validate_and_parse():
    skill = validate_skill_fields({
        "name": "AWS ES Auto-Scaling",
        "description": "基于指标自动调整节点数",
        "category": "automation",
        "instructions": "1. 告警\n2. 扩容\n3. 验证健康状态并记录",
        "required_tools": ["aws_cli", "cloudwatch_api"],
        "confidence": 0.9,
    })
    assert skill["slug"]
    assert skill["category"] == "automation"

    payload = json.dumps({"skills": [skill]}, ensure_ascii=False)
    skills, err = parse_skills_payload(payload)
    assert err is None
    assert len(skills) == 1

    fenced = "```json\n" + payload + "\n```"
    skills2, err2 = parse_skills_payload(fenced)
    assert err2 is None
    assert len(skills2) == 1


@pytest.mark.asyncio
async def test_pipeline_extract_with_mock_decoder():
    fixed = {
        "skills": [
            {
                "name": "AWS ES 自动扩缩",
                "description": "根据 CloudWatch CPU 指标自动调整 ES 节点数",
                "category": "automation",
                "icon": "📈",
                "slug": "aws-es-auto-scaling",
                "instructions": "1. 配置 CPU>70% 告警\n2. UpdateDomainConfig 扩容\n3. 检查集群绿状态",
                "required_tools": ["aws_cli", "cloudwatch_api"],
                "confidence": 0.88,
                "scope": "public",
                "extraction_algorithm": "tse-temporal",
            }
        ]
    }

    async def fake_chat(prompt, system_prompt):
        assert "Skill-moment" in prompt or "技能时刻" in prompt
        return json.dumps(fixed, ensure_ascii=False)

    pipe = TSEPipeline()
    result = await pipe.extract(
        SAMPLE_TRANSCRIPT,
        source_title="ES扩缩容讨论",
        chat_fn=fake_chat,
    )
    assert result.parse_error is None
    assert len(result.skills) == 1
    assert "ES" in result.skills[0]["name"] or "扩" in result.skills[0]["name"]
    assert result.focus_indices
    assert result.latency_ms >= 0
    assert "stage1_encoder_ms" in result.stage_timings
    assert "stage4_decoder_ms" in result.stage_timings
    assert result.model.startswith("tse+") or result.model == "chat_fn" or "tse" in result.model


@pytest.mark.asyncio
async def test_pipeline_empty_source():
    pipe = TSEPipeline()
    result = await pipe.extract("", source_title="empty")
    assert result.skills == []
    assert result.parse_error == "empty transcript"
