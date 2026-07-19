# -*- coding: utf-8 -*-
"""Skill JSON schema validation for constrained decoding (Stage 4)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .config import CATEGORY_ALIASES, VALID_CATEGORIES


class SkillSchemaError(ValueError):
    """Raised when a skill object fails schema validation."""


def extract_json_from_text(text: str) -> str:
    """Extract JSON from markdown fences or first array/object span."""
    if not text:
        return ""
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", text)
    if m:
        return m.group(1).strip()
    return text.strip()


def _norm_category(cat: str) -> str:
    c = (cat or "general").strip().lower().replace(" ", "_").replace("-", "_")
    if c in VALID_CATEGORIES:
        return CATEGORY_ALIASES.get(c, c) if c in CATEGORY_ALIASES else c
    # product-facing aliases
    aliases = {
        "ops": "automation",
        "devops": "automation",
        "infra": "automation",
        "sre": "monitoring",
        "ml": "research",
        "data": "analysis",
        "coding": "development",
        "domain": "domain_knowledge",
        "twin": "digital_twin",
    }
    return aliases.get(c, "general")


def _slugify(name: str) -> str:
    s = (name or "").strip().lower()
    s = re.sub(r"[\s_/]+", "-", s)
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff\-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "skill"
    return s[:64]


def validate_skill_fields(skill: Dict[str, Any], *, strict: bool = False) -> Dict[str, Any]:
    """Normalize and validate one skill dict. Returns cleaned skill."""
    if not isinstance(skill, dict):
        raise SkillSchemaError("skill must be an object")

    name = str(skill.get("name") or "").strip()
    if not name:
        raise SkillSchemaError("missing name")
    if len(name) > 64:
        name = name[:64]

    description = str(skill.get("description") or "").strip()
    if strict and len(description) < 8:
        raise SkillSchemaError("description too short")

    instructions = str(skill.get("instructions") or "").strip()
    if strict and len(instructions) < 20:
        raise SkillSchemaError("instructions too short")

    category = _norm_category(str(skill.get("category") or "general"))

    tools_raw = skill.get("required_tools") or skill.get("tools") or []
    if isinstance(tools_raw, str):
        tools = [t.strip() for t in re.split(r"[,;|]", tools_raw) if t.strip()]
    elif isinstance(tools_raw, list):
        tools = [str(t).strip() for t in tools_raw if str(t).strip()]
    else:
        tools = []

    slug = str(skill.get("slug") or "").strip() or _slugify(name)
    icon = str(skill.get("icon") or "⚡").strip() or "⚡"
    try:
        confidence = float(skill.get("confidence", 0.7))
    except (TypeError, ValueError):
        confidence = 0.7
    confidence = max(0.0, min(1.0, confidence))
    scope = str(skill.get("scope") or "public").strip().lower()
    if scope not in ("personal", "public"):
        scope = "public"
    algo = str(skill.get("extraction_algorithm") or "tse-temporal").strip()

    return {
        "name": name,
        "description": description or f"从讨论中萃取的技能：{name}",
        "category": category,
        "icon": icon[:4],
        "slug": slug,
        "instructions": instructions or f"1. 明确触发条件\n2. 执行与「{name}」相关的核心步骤\n3. 验证结果并记录",
        "required_tools": tools[:20],
        "confidence": confidence,
        "scope": scope,
        "extraction_algorithm": algo,
    }


def parse_skills_payload(text: str, *, strict: bool = False) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Parse decoder text into a list of validated skill dicts.

    Accepts:
      {"skills": [...]}
      [...]
      {...single skill...}

    Returns (skills, error_message).
    """
    raw = extract_json_from_text(text)
    if not raw:
        return [], "empty response"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return [], f"json decode: {e}"

    if isinstance(data, dict) and "skills" in data:
        items = data["skills"]
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = [data]
    else:
        return [], "unexpected JSON root type"

    if not isinstance(items, list):
        return [], "skills is not a list"

    out: List[Dict[str, Any]] = []
    errors: List[str] = []
    for i, item in enumerate(items):
        try:
            out.append(validate_skill_fields(item, strict=strict))
        except SkillSchemaError as e:
            errors.append(f"[{i}] {e}")

    if not out and errors:
        return [], "; ".join(errors[:5])
    return out, None


# Grammar sketch used in decoder prompts (not a full CFG engine)
SKILL_JSON_GRAMMAR_HINT = """
Output MUST be a single JSON object (no markdown fences, no commentary):
{
  "skills": [
    {
      "name": string (max 64 chars, Chinese preferred),
      "description": string (1-4 sentences),
      "category": one of [automation, research, general, analysis, monitoring, development, domain_knowledge, digital_twin],
      "icon": single emoji,
      "slug": lowercase-hyphen-id,
      "instructions": string (step-by-step, >= 3 steps),
      "required_tools": string[],
      "confidence": number 0..1,
      "scope": "personal" | "public",
      "extraction_algorithm": "tse-temporal"
    }
  ]
}
If no task-specific skill is present, return {"skills": []}.
""".strip()
