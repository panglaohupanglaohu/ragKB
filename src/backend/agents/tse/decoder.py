# -*- coding: utf-8 -*-
"""Stage 4: Constrained JSON decoder.

Methodology uses CodeLLaMA-7B + QLoRA + grammar constraints. In production
we project skill-query focus into a structured prompt and decode via the
existing ChatHarness (system LLM). JSON is post-validated against schema;
one grammar retry on failure.

Optional torch CodeLLaMA path is not loaded by default (heavy deps).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from .config import TSEConfig
from .schema import SKILL_JSON_GRAMMAR_HINT, parse_skills_payload
from .transcript import PlazaTranscript

logger = logging.getLogger(__name__)

TSE_SYSTEM_PROMPT = """You are the Stage-4 Constrained JSON Decoder of TSE (TCN-Skill-Extractor).
You receive: (1) discussion topic, (2) skill-moment utterances selected by temporal
cross-attention over a multi-agent Plaza discussion, (3) field-focus hints.

Extract ONLY task-specific reusable skills explicitly discussed or strongly implied.
Do NOT invent generic soft skills (communication, teamwork).
Instructions must be actionable step lists.

""" + SKILL_JSON_GRAMMAR_HINT


def build_decoder_prompt(
    transcript: PlazaTranscript,
    *,
    focus_indices: Sequence[int],
    field_focus: Optional[Dict[str, List[Dict]]] = None,
    category_hint: str = "",
    tools_hint: Optional[List[str]] = None,
    max_chars: int = 10000,
    min_skills: int = 1,
    max_skills: int = 8,
) -> str:
    """Build constrained generation prompt from TCN+Attention outputs."""
    focused = transcript.format_for_prompt(list(focus_indices))
    if len(focused) > max_chars:
        focused = focused[:max_chars] + "\n...[truncated]"

    focus_lines = []
    if field_focus:
        for field, rows in field_focus.items():
            if not rows:
                continue
            tops = ", ".join(f"#{r['index']}({r['weight']:.2f})" for r in rows[:3])
            focus_lines.append(f"  - {field}: utterances {tops}")

    tools_s = ", ".join(tools_hint or []) or "(infer from discussion)"
    cat_s = category_hint or "(infer)"

    return f"""基于以下多智能体讨论中的「技能时刻」(Skill Query Cross-Attention 选中片段)，生成结构化技能定义 JSON。

讨论话题: {transcript.topic}
讨论 ID: {transcript.discussion_id}
候选技能数: {min_skills}–{max_skills}

辅助头提示 (multi-task prior):
- category_hint: {cat_s}
- tools_hint: {tools_s}

字段关注点 (Stage 3 attention):
{chr(10).join(focus_lines) if focus_lines else "  (uniform)"}

── Skill-moment transcript ──
{focused}
── End ──

CRITICAL:
1. Only skills grounded in the transcript above.
2. Each skill needs name, description, category, instructions (steps), required_tools.
3. Output pure JSON object with key "skills" only — no markdown.
"""


class ConstrainedSkillDecoder:
    """Grammar-constrained skill JSON generation via ChatHarness."""

    def __init__(self, config: TSEConfig | None = None):
        self.config = config or TSEConfig()

    async def generate(
        self,
        transcript: PlazaTranscript,
        *,
        focus_indices: Sequence[int],
        field_focus: Optional[Dict[str, List[Dict]]] = None,
        category_hint: str = "",
        tools_hint: Optional[List[str]] = None,
        chat_fn=None,
        harness=None,
    ) -> Dict[str, Any]:
        """
        Returns:
          {
            "skills": [...],
            "raw_response": str,
            "model": str,
            "parse_error": str|None,
            "prompt": str,
          }
        """
        cfg = self.config
        prompt = build_decoder_prompt(
            transcript,
            focus_indices=focus_indices,
            field_focus=field_focus,
            category_hint=category_hint,
            tools_hint=tools_hint,
            max_chars=cfg.max_source_chars_in_prompt,
            min_skills=cfg.min_skills,
            max_skills=cfg.max_skills,
        )

        raw = ""
        model = "unknown"
        if chat_fn is not None:
            raw = await _call_chat_fn(chat_fn, prompt)
            model = "chat_fn"
        elif harness is not None:
            model_override = _harness_model_name(harness)
            result = await harness.chat(
                prompt=prompt,
                system_prompt=TSE_SYSTEM_PROMPT,
                agent_id="tse_skill_extractor",
                model_override=model_override or None,
            )
            raw = _result_text(result)
            model = getattr(result, "model", None) or model_override or "harness"
        else:
            # Offline: local constrained synthesizer (no LLM)
            skills = synthesize_skills_local(
                transcript,
                focus_indices=focus_indices,
                category_hint=category_hint,
                tools_hint=tools_hint,
            )
            return {
                "skills": skills[: cfg.max_skills],
                "raw_response": json.dumps({"skills": skills}, ensure_ascii=False),
                "model": "tse+local",
                "parse_error": None if skills else "no decoder backend",
                "prompt": prompt,
            }

        skills, err = parse_skills_payload(raw, strict=False)
        if _is_unusable_llm_text(raw):
            skills, err = [], "llm_offline_or_provider_fallback"

        retries = 0
        while err and retries < cfg.grammar_retry and harness is not None and not _is_unusable_llm_text(raw):
            retries += 1
            repair = (
                prompt
                + "\n\nYour previous output failed schema validation: "
                + err
                + "\nRegenerate ONLY valid JSON matching the grammar. No markdown."
            )
            model_override = _harness_model_name(harness)
            result = await harness.chat(
                prompt=repair,
                system_prompt=TSE_SYSTEM_PROMPT,
                agent_id="tse_skill_extractor",
                model_override=model_override or None,
            )
            raw = _result_text(result)
            model = getattr(result, "model", None) or model
            if _is_unusable_llm_text(raw):
                skills, err = [], "llm_offline_or_provider_fallback"
                break
            skills, err = parse_skills_payload(raw, strict=False)

        # LLM dead → still produce real skills from TCN skill-moments (not generic 回退草稿)
        if (not skills) and (err or _is_unusable_llm_text(raw)):
            local = synthesize_skills_local(
                transcript,
                focus_indices=focus_indices,
                category_hint=category_hint,
                tools_hint=tools_hint,
            )
            if local:
                return {
                    "skills": local[: cfg.max_skills],
                    "raw_response": raw or json.dumps({"skills": local}, ensure_ascii=False),
                    "model": f"tse+local({model})",
                    "parse_error": None,
                    "prompt": prompt,
                }

        # Cap
        skills = skills[: cfg.max_skills]
        return {
            "skills": skills,
            "raw_response": raw,
            "model": f"tse+{model}",
            "parse_error": err,
            "prompt": prompt,
        }


def _result_text(result: Any) -> str:
    if result is None:
        return ""
    if hasattr(result, "response") and result.response:
        return str(result.response)
    if hasattr(result, "content") and result.content:
        return str(result.content)
    return str(result)


def _harness_model_name(harness) -> str:
    """Prefer configured provider model (e.g. qwen-36), never TG routed names."""
    try:
        cfg = harness.get_provider_config()
        name = getattr(cfg, "model", None) or ""
        return str(name).strip()
    except Exception:
        return ""


def _is_unusable_llm_text(text: str) -> bool:
    if not text or not str(text).strip():
        return True
    t = str(text)
    markers = (
        "LLM 未连接",
        "LLM 状态: ⚠️",
        "is not supported",
        "Model \"",
        "需要 LLM 连接",
        "当前 LLM 未连接",
        "配置方式:",
        "export DEEPSEEK_API_KEY",
        "智能体管理面板",
    )
    hits = sum(1 for m in markers if m in t)
    return hits >= 1 and ("{" not in t or '"skills"' not in t)


def synthesize_skills_local(
    transcript: PlazaTranscript,
    *,
    focus_indices: Sequence[int],
    category_hint: str = "",
    tools_hint: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Grammar-constrained local decoder when ChatHarness/LLM is unavailable.

    Builds 1–3 skills from skill-moment utterances (Stage 3 attention focus),
    grounded in discussion content — not generic 回退草稿 templates.
    """
    from .schema import validate_skill_fields

    msgs = transcript.messages
    if not msgs:
        return []
    idxs = [i for i in (focus_indices or list(range(len(msgs)))) if 0 <= i < len(msgs)]
    if not idxs:
        idxs = list(range(min(5, len(msgs))))

    focus_texts = [msgs[i].content.strip() for i in idxs if msgs[i].content.strip()]
    body = "\n".join(focus_texts)
    topic = (transcript.topic or "讨论技能").strip()
    cat = (category_hint or "general").strip() or "general"
    tools = list(tools_hint or [])[:8]

    # Prefer explicit “技能名/步骤” lines if present
    name = topic[:48]
    for line in focus_texts:
        for key in ("技能名", "技能名称", "共识技能", "skill", "Skill"):
            if key in line:
                # take rest after key
                part = line.split(key, 1)[-1]
                part = part.lstrip("：:是为 ").strip()
                if part:
                    name = part[:48]
                    break

    steps = []
    for line in focus_texts:
        if any(x in line for x in ("步骤", "1.", "2.", "3.", "首先", "然后", "配置", "验证", "执行")):
            steps.append(line[:200])
    if not steps:
        steps = focus_texts[:4]

    instr_lines = []
    for i, s in enumerate(steps[:8], 1):
        # strip speaker chrome already done; number steps
        s2 = s
        for prefix in ("步骤：", "步骤:", "步骤"):
            if s2.startswith(prefix):
                s2 = s2[len(prefix):].strip()
        instr_lines.append(f"{i}. {s2}")
    instructions = "\n".join(instr_lines) if instr_lines else (
        f"1. 确认「{topic}」的触发条件与约束\n"
        f"2. 按讨论共识执行核心动作\n"
        f"3. 验证结果并记录工具与回滚点"
    )

    skills: List[Dict[str, Any]] = []
    try:
        skills.append(validate_skill_fields({
            "name": name if name else f"{topic} 技能",
            "description": (
                f"从广场讨论「{topic}」的技能时刻萃取："
                f"{(focus_texts[0][:120] if focus_texts else body[:120])}"
            ),
            "category": cat,
            "icon": "⚡",
            "instructions": instructions,
            "required_tools": tools,
            "confidence": 0.62,
            "scope": "public",
            "extraction_algorithm": "tse-local-decoder",
        }))
    except Exception:
        pass

    # Secondary: anti-pattern / constraint skill if discussion has challenges
    challenge_lines = [
        msgs[i].content for i in idxs
        if msgs[i].ritual_signal in ("challenge", "objection") or "禁止" in msgs[i].content or "注意" in msgs[i].content
    ]
    if challenge_lines:
        try:
            skills.append(validate_skill_fields({
                "name": f"{topic[:20]} · 约束与避坑"[:48],
                "description": "从讨论中的挑战/约束信号萃取的防御性技能。",
                "category": cat if cat != "general" else "automation",
                "icon": "🛡️",
                "instructions": "\n".join(
                    f"{i+1}. {c[:180]}" for i, c in enumerate(challenge_lines[:5])
                ) or "1. 识别约束 2. 写入检查清单 3. 发布前复核",
                "required_tools": tools,
                "confidence": 0.58,
                "scope": "public",
                "extraction_algorithm": "tse-local-decoder",
            }))
        except Exception:
            pass

    return skills


async def _call_chat_fn(chat_fn, prompt: str) -> str:
    """Support sync or async chat callables."""
    import asyncio
    import inspect

    if inspect.iscoroutinefunction(chat_fn):
        out = await chat_fn(prompt, TSE_SYSTEM_PROMPT)
    else:
        out = chat_fn(prompt, TSE_SYSTEM_PROMPT)
        if inspect.isawaitable(out):
            out = await out
    if isinstance(out, str):
        return out
    return _result_text(out)


def heuristic_category_hint(transcript: PlazaTranscript) -> str:
    """Lightweight multi-task category prior (no trained head)."""
    text = (transcript.topic + " " + " ".join(m.content for m in transcript.messages[:20])).lower()
    rules = [
        (("monitor", "告警", "metric", "cloudwatch", "prometheus"), "monitoring"),
        (("auto", "scale", "pipeline", "ci/cd", "自动化", "扩缩"), "automation"),
        (("research", "调研", "论文", "分析", "analysis"), "research"),
        (("code", "开发", "refactor", "api", "sdk"), "development"),
        (("twin", "孪生", "仿真"), "digital_twin"),
    ]
    for keys, cat in rules:
        if any(k in text for k in keys):
            return cat
    return "general"


def heuristic_tools_hint(transcript: PlazaTranscript) -> List[str]:
    text = " ".join(m.content for m in transcript.messages).lower()
    catalog = [
        ("aws", "aws_cli"), ("boto", "python_boto3"), ("cloudwatch", "cloudwatch_api"),
        ("kubectl", "kubectl"), ("k8s", "kubectl"), ("terraform", "terraform"),
        ("docker", "docker"), ("python", "python"), ("curl", "curl"),
        ("prometheus", "prometheus"), ("grafana", "grafana"),
        ("git", "git"), ("sql", "sql"),
    ]
    found = []
    for key, tool in catalog:
        if key in text and tool not in found:
            found.append(tool)
    return found[:12]
