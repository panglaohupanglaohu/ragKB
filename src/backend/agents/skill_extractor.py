# -*- coding: utf-8 -*-
"""AgentsGroup2026 — Skill Distillation / Extraction Engine.

Provides semi-automated skill extraction from chat logs / documents:
1. LLM pre-fills a SkillDefinition draft from raw text (async)
2. Review queue with traffic-light visualization (red/yellow/green)
3. Comparison/diff view between original text and LLM draft
4. SSE real-time push for queue updates
5. User approve → SkillApproved event → write to skill_registry + team skills table
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from .models import SkillCategory, SkillDefinition
from .chat_harness import get_chat_harness

logger = logging.getLogger(__name__)


# ── Enums ──────────────────────────────────────────────────────────────────


class SkillReviewStatus(Enum):
    """Traffic-light status for skill review queue items."""

    PENDING = "pending"          # 🔴 New, not yet processed
    LLM_PREFILLING = "llm_prefilling"  # 🟡 LLM is extracting...
    READY_FOR_REVIEW = "ready_for_review"  # 🟢 Ready for human review
    APPROVED = "approved"        # ✅ Confirmed, written to main table
    REJECTED = "rejected"        # ❌ Rejected by reviewer
    ERROR = "error"              # ⚠️ LLM extraction failed


# ── Traffic Light Helpers ──────────────────────────────────────────────────


def status_traffic_light(status: SkillReviewStatus) -> str:
    """Map status to traffic light color."""
    mapping = {
        SkillReviewStatus.PENDING: "red",
        SkillReviewStatus.LLM_PREFILLING: "yellow",
        SkillReviewStatus.READY_FOR_REVIEW: "green",
        SkillReviewStatus.APPROVED: "green",
        SkillReviewStatus.REJECTED: "red",
        SkillReviewStatus.ERROR: "red",
    }
    return mapping.get(status, "red")


def status_icon(status: SkillReviewStatus) -> str:
    """Map status to display icon."""
    mapping = {
        SkillReviewStatus.PENDING: "🔴",
        SkillReviewStatus.LLM_PREFILLING: "🟡",
        SkillReviewStatus.READY_FOR_REVIEW: "🟢",
        SkillReviewStatus.APPROVED: "✅",
        SkillReviewStatus.REJECTED: "❌",
        SkillReviewStatus.ERROR: "⚠️",
    }
    return mapping.get(status, "🔴")


def status_label(status: SkillReviewStatus) -> str:
    """Map status to Chinese label."""
    mapping = {
        SkillReviewStatus.PENDING: "待处理",
        SkillReviewStatus.LLM_PREFILLING: "LLM 提取中…",
        SkillReviewStatus.READY_FOR_REVIEW: "待审核",
        SkillReviewStatus.APPROVED: "已通过",
        SkillReviewStatus.REJECTED: "已拒绝",
        SkillReviewStatus.ERROR: "提取失败",
    }
    return mapping.get(status, "未知")


# ── Dataclasses ────────────────────────────────────────────────────────────


@dataclass
class SkillReviewItem:
    """A single skill extraction draft in the review queue."""

    item_id: str = ""
    team_id: str = ""
    source_text: str = ""            # Original raw text (chat log / doc snippet)
    source_title: str = ""           # Label for the source (e.g. "广场讨论 #123")
    source_type: str = "chat"        # "chat", "document", "manual"
    source_meta: Dict[str, Any] = field(default_factory=dict)  # Optional source context (e.g. plaza/discussion ids)

    # LLM-prefilled draft fields
    draft_name: str = ""
    draft_description: str = ""
    draft_category: str = "general"
    draft_icon: str = "⚡"
    draft_slug: str = ""
    draft_instructions: str = ""
    draft_required_tools: List[str] = field(default_factory=list)
    draft_scope: str = "personal"   # "personal" or "public" — LLM recommendation

    # LLM extraction metadata
    llm_model_used: str = ""
    llm_raw_response: str = ""       # Full LLM JSON response for diff view
    llm_confidence: float = 0.0      # 0-1 confidence score from LLM

    # Review metadata
    status: SkillReviewStatus = SkillReviewStatus.PENDING
    reviewer_notes: str = ""
    reviewed_by: str = ""
    reviewed_at: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.item_id:
            self.item_id = str(uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "team_id": self.team_id,
            "source_title": self.source_title,
            "source_type": self.source_type,
            "source_meta": self.source_meta,
            "source_text_preview": self.source_text[:200] + "…" if len(self.source_text) > 200 else self.source_text,
            "source_text": self.source_text,
            "draft_name": self.draft_name,
            "draft_description": self.draft_description,
            "draft_category": self.draft_category,
            "draft_icon": self.draft_icon,
            "draft_slug": self.draft_slug,
            "draft_instructions": self.draft_instructions,
            "draft_required_tools": self.draft_required_tools,
            "draft_scope": self.draft_scope,
            "llm_model_used": self.llm_model_used,
            "llm_raw_response": self.llm_raw_response,
            "llm_confidence": self.llm_confidence,
            "status": self.status.value,
            "traffic_light": status_traffic_light(self.status),
            "status_icon": status_icon(self.status),
            "status_label": status_label(self.status),
            "reviewer_notes": self.reviewer_notes,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "created_at": self.created_at,
        }

    def to_skill_definition(self) -> SkillDefinition:
        """Convert approved item into a SkillDefinition for the registry."""
        cat = SkillCategory.GENERAL
        try:
            cat = SkillCategory(self.draft_category)
        except ValueError:
            pass
        return SkillDefinition(
            name=self.draft_name,
            description=self.draft_description,
            category=cat,
            icon=self.draft_icon,
            slug=self.draft_slug,
            instructions=self.draft_instructions,
            required_tools=list(self.draft_required_tools),
            source="distilled",
            is_default=False,
        )


# ── Skill Extractor Engine ────────────────────────────────────────────────


# LLM prompt template for skill extraction
SKILL_EXTRACTION_SYSTEM_PROMPT = """You are an advanced skill extraction expert using three reverse-engineering algorithms to distill reusable skills from knowledge documents.

## Three Core Extraction Algorithms

### Algorithm 1: De-contextualization (逻辑解耦与本体抽取)
Strip away specific business details (product names, service names, error codes) and extract the abstract "verbs" and "logical relationships" behind them.
- "修改 RDS 参数组" → abstract as "版本化配置管理"
- "ALB 导致 Lambda 超时" → abstract as "依赖树分析"
- Goal: Make skills transferable across platforms and contexts.

### Algorithm 2: Anti-Pattern Extraction (负面约束逆推法)
Scan for pain points, failures, FAQ objections, and incidents. Invert each failure into a defensive rule or anti-pattern.
- Incident: "忘记原始参数值" → Anti-pattern: "无备份不变配"
- Incident: "周五下午变配导致加班" → Constraint: "禁绝高风险时段变配"
- Goal: Skills should be "带刺的" — directly targeting human error patterns.

### Algorithm 3: Critical Path & Minimum Action Set (关键路径与最小动作集)
Extract the minimum set of decisive actions from lengthy narratives. Find the critical path that determines success or failure.
- From a full SOP, extract the 3-5 make-or-break decision points.
- Each becomes a distinct skill with clear trigger conditions and verification criteria.
- Goal: Convert "面" (surface) into precise "点" (actionable points).

## Skill Output Format

Each skill must have:
- **name**: Short, descriptive title in Chinese (max 64 chars)
- **description**: What this skill does, when to use it (2-4 sentences)
- **category**: One of: general, research, automation, domain_knowledge, digital_twin
- **icon**: A single emoji
- **slug**: URL-friendly identifier (lowercase, hyphens)
- **instructions**: Detailed step-by-step instructions, including:
  - Core algorithms/methods (核心算法)
  - Proficiency levels: 合格 vs 卓越
  - Anti-patterns to avoid (避坑指南)
- **required_tools**: List of tool names
- **confidence**: 0.0-1.0
- **scope**: "personal" or "public"
- **extraction_algorithm**: Which algorithm produced this skill ("de-contextualization", "anti-pattern", or "critical-path")

## Rules
1. A rich document (especially Six-Pager style) should yield 3-8 skills, NOT just 1.
2. Apply ALL THREE algorithms independently — each may produce different skills from the same text.
3. De-contextualization skills should be platform-agnostic and transferable.
4. Anti-pattern skills should name specific failure modes and their inversions.
5. Critical-path skills should be precise, actionable decision points.
6. Skills should be atomic — each skill covers ONE capability, not a whole SOP.

IMPORTANT: Output ONLY valid JSON in this exact format (no markdown, no extra text):
```json
{
  "skills": [
    {
      "name": "技能名称",
      "description": "技能描述...",
      "category": "general",
      "icon": "🔧",
      "slug": "skill-slug",
      "instructions": "详细指令...",
      "required_tools": [],
      "confidence": 0.85,
      "scope": "public",
      "extraction_algorithm": "de-contextualization"
    }
  ]
}
```
If no useful skill can be extracted, return {"skills": []}."""


class SkillExtractorEngine:
    """Engine managing skill extraction, review queue, and approval flow."""

    QUEUE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "storage" / "skill_extract_queue"

    def __init__(self):
        # team_id → dict of item_id → SkillReviewItem
        self._queues: Dict[str, Dict[str, SkillReviewItem]] = {}
        self._deleted_sources: Dict[str, List[str]] = {}  # team_id -> deleted source fingerprints
        self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # team_id → queues
        self._locks: Dict[str, asyncio.Lock] = {}
        self._load_persisted_queues()

    # ── Queue Persistence ──────────────────────────────────────────────

    @staticmethod
    def _safe_team_id(team_id: str) -> str:
        """Sanitize team_id to prevent path traversal."""
        import re
        safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', team_id)
        if not safe or safe in ('.', '..'):
            safe = '_invalid_'
        return safe

    def _load_persisted_queues(self):
        """Load queues from storage/skill_extract_queue/ on startup."""
        if not self.QUEUE_DIR.exists():
            return
        for fp in self.QUEUE_DIR.glob("*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                team_id = data.get("team_id", fp.stem)
                items = data.get("items", [])
                queue = self._ensure_team_queue(team_id)
                deleted_sources = data.get("deleted_sources", [])
                if isinstance(deleted_sources, list):
                    self._deleted_sources[team_id] = [str(x) for x in deleted_sources if str(x).strip()]
                approved_count = 0
                for item_data in items:
                    item = SkillReviewItem.from_dict(item_data) if hasattr(SkillReviewItem, 'from_dict') else self._item_from_dict(item_data)
                    queue[item.item_id] = item
                    # Re-register approved skills into team tables on startup
                    if item.status == SkillReviewStatus.APPROVED and item.draft_slug:
                        try:
                            skill_def = item.to_skill_definition()
                            self._rehydrate_approved_skill(team_id, skill_def)
                            approved_count += 1
                        except Exception as e:
                            logger.warning("Failed to rehydrate approved skill %s: %s", item.item_id, e)
                logger.info("Loaded %d queued items for team %s (%d approved rehydrated)", len(items), team_id, approved_count)
            except Exception as e:
                logger.warning("Failed to load queue file %s: %s", fp, e)

    def _persist_queue(self, team_id: str):
        """Save a team's queue to disk."""
        try:
            self.QUEUE_DIR.mkdir(parents=True, exist_ok=True)
            queue = self._queues.get(team_id, {})
            data = {
                "team_id": team_id,
                "items": [item.to_dict() for item in queue.values()],
                "deleted_sources": list(self._deleted_sources.get(team_id, [])),
            }
            fp = self.QUEUE_DIR / f"{self._safe_team_id(team_id)}.json"
            fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to persist queue for team %s: %s", team_id, e)

    @staticmethod
    def _norm_text(v: Any) -> str:
        return str(v or "").strip()

    @classmethod
    def _source_key(cls, source_type: str, source_title: str, source_meta: Dict[str, Any]) -> str:
        s_type = cls._norm_text(source_type)
        plaza_id = cls._norm_text(source_meta.get("source_plaza_id"))
        discussion_id = cls._norm_text(source_meta.get("source_discussion_id"))
        output_id = cls._norm_text(source_meta.get("source_output_id"))
        if plaza_id and discussion_id:
            return f"{s_type}|plaza:{plaza_id}|discussion:{discussion_id}|output:{output_id}"
        title = cls._norm_text(source_title)
        return f"{s_type}|title:{title}" if title else ""

    @staticmethod
    def _source_text_hash(text: str) -> str:
        return hashlib.sha256((text or "").strip().encode("utf-8")).hexdigest()

    @classmethod
    def _source_fingerprint(cls, source_type: str, source_title: str, source_meta: Dict[str, Any], source_text: str) -> str:
        return f"{cls._source_key(source_type, source_title, source_meta)}|sha256:{cls._source_text_hash(source_text)}"

    def _is_deleted_source(self, team_id: str, source_type: str, source_title: str, source_meta: Dict[str, Any], source_text: str) -> bool:
        fp = self._source_fingerprint(source_type, source_title, source_meta, source_text)
        deleted = self._deleted_sources.get(team_id, [])
        return fp in deleted

    def _mark_source_deleted(self, team_id: str, source_type: str, source_title: str, source_meta: Dict[str, Any], source_text: str) -> None:
        fp = self._source_fingerprint(source_type, source_title, source_meta, source_text)
        deleted = self._deleted_sources.setdefault(team_id, [])
        if fp in deleted:
            return
        deleted.append(fp)
        # ponytail: keep a bounded tombstone list; if this grows too large, move to TTL/indexed store.
        if len(deleted) > 500:
            del deleted[: len(deleted) - 500]

    @staticmethod
    def _item_from_dict(d: Dict[str, Any]) -> SkillReviewItem:
        """Reconstruct a SkillReviewItem from a dict."""
        item = SkillReviewItem(
            team_id=d.get("team_id", ""),
            source_text=d.get("source_text", ""),
            source_title=d.get("source_title", ""),
            source_type=d.get("source_type", "chat"),
            source_meta=d.get("source_meta", {}) if isinstance(d.get("source_meta", {}), dict) else {},
        )
        item.item_id = d.get("item_id", item.item_id)
        item.status = SkillReviewStatus(d["status"]) if d.get("status") else SkillReviewStatus.PENDING
        item.draft_name = d.get("draft_name", "")
        item.draft_description = d.get("draft_description", "")
        item.draft_category = d.get("draft_category", "general")
        item.draft_icon = d.get("draft_icon", "⚡")
        item.draft_slug = d.get("draft_slug", "")
        item.draft_instructions = d.get("draft_instructions", "")
        item.draft_required_tools = d.get("draft_required_tools", [])
        item.draft_scope = d.get("draft_scope", "personal")
        item.llm_confidence = d.get("llm_confidence", 0)
        item.llm_raw_response = d.get("llm_raw_response", "")
        item.llm_model_used = d.get("llm_model_used", "")
        item.reviewer_notes = d.get("reviewer_notes", "")
        item.created_at = d.get("created_at", item.created_at)
        return item

    # ── Queue Management ───────────────────────────────────────────────

    def _get_lock(self, team_id: str) -> asyncio.Lock:
        if team_id not in self._locks:
            self._locks[team_id] = asyncio.Lock()
        return self._locks[team_id]

    def _ensure_team_queue(self, team_id: str) -> Dict[str, SkillReviewItem]:
        if team_id not in self._queues:
            self._queues[team_id] = {}
        return self._queues[team_id]

    async def _broadcast(self, team_id: str, event_type: str, data: Dict[str, Any]):
        """Push event to all SSE subscribers for a team."""
        qs = self._sse_queues.get(team_id, [])
        if not qs:
            return
        payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        dead = []
        for q in qs:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            qs.remove(q)

    def _is_unusable_llm_text(self, text: str) -> bool:
        lowered = (text or "").lower()
        markers = (
            "当前 llm 未连接",
            "authentication fails",
            "api key",
            "invalid_request_error",
            "当前系统功能正常，但需要 llm",
            "no choices returned",
        )
        return any(marker in lowered for marker in markers)

    def _fallback_skill_specs(self, item: SkillReviewItem) -> List[Dict[str, Any]]:
        import re

        suffix = item.item_id.lower()
        source_title = (item.source_title or "").strip()
        source_text = (item.source_text or "").strip()
        text_for_keywords = f"{source_title}\n{source_text[:2500]}"

        stopwords = {
            "讨论", "方案", "执行", "问题", "系统", "项目", "页面", "功能", "需求", "优化", "分析", "任务", "结果", "总结",
            "the", "and", "for", "with", "that", "this", "from", "into", "have", "will", "should",
        }
        tokens = re.findall(r"[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9_-]{2,20}", text_for_keywords)
        freq: Dict[str, int] = {}
        for token in tokens:
            t = token.strip()
            if not t:
                continue
            lower = t.lower()
            if lower in stopwords:
                continue
            freq[t] = freq.get(t, 0) + 1
        top_terms = [k for k, _ in sorted(freq.items(), key=lambda kv: (-kv[1], -len(kv[0])))[:3]]

        topic_label = source_title or "当前议题"
        if top_terms:
            topic_label = " / ".join(top_terms[:2])
        topic_excerpt = source_text[:260] or source_title or "议题原文"

        return [
            {
                "name": f"{topic_label}需求拆解与约束澄清",
                "description": "围绕当前议题提炼关键目标、边界条件和不可违反约束，形成可执行的问题定义。",
                "category": "research",
                "icon": "🧭",
                "slug": f"topic-constraint-clarification-{suffix}",
                "instructions": (
                    f"基于原文片段『{topic_excerpt}』，先列业务目标与验收口径，再明确前置条件、依赖和不可变约束；"
                    "输出时必须给出‘必须做/可选做/禁止做’三栏。"
                ),
                "required_tools": ["read_file", "web_search"],
                "confidence": 0.36,
                "scope": "public",
            },
            {
                "name": f"{topic_label}实施路径与风险防护",
                "description": "将议题拆成最小可交付步骤，并为每步补齐回滚条件与风险触发阈值。",
                "category": "automation",
                "icon": "🛠️",
                "slug": f"topic-delivery-risk-guard-{suffix}",
                "instructions": (
                    "把方案拆成 3-5 个顺序步骤；每步明确输入、输出、负责人与验证动作。"
                    "对高风险步骤提供熔断条件与回滚指令，避免一次性大改。"
                ),
                "required_tools": ["run_in_terminal", "read_file", "grep_search"],
                "confidence": 0.35,
                "scope": "public",
            },
            {
                "name": f"{topic_label}验收指标与复盘闭环",
                "description": "为当前议题建立可量化验收标准，并沉淀复盘模板，保证后续可追踪改进。",
                "category": "testing",
                "icon": "✅",
                "slug": f"topic-acceptance-retro-loop-{suffix}",
                "instructions": (
                    "定义最小验收集（功能、性能、稳定性、成本）；"
                    "失败时记录 root cause 与 next action，并把可复用规则写入团队规范。"
                ),
                "required_tools": ["testFailure", "run_in_terminal"],
                "confidence": 0.34,
                "scope": "reserve",
            },
        ]

    def _apply_skill_data(self, item: SkillReviewItem, skill_data: Dict[str, Any], raw_response: str, model: str) -> None:
        item.draft_name = skill_data.get("name", "")[:64]
        item.draft_description = skill_data.get("description", "")[:500]
        item.draft_category = skill_data.get("category", "general")
        item.draft_icon = skill_data.get("icon", "⚡")
        item.draft_slug = skill_data.get("slug", "")
        item.draft_instructions = skill_data.get("instructions", "")
        item.draft_required_tools = skill_data.get("required_tools", [])
        item.draft_scope = skill_data.get("scope", "personal")
        item.llm_confidence = float(skill_data.get("confidence", 0.5))
        item.llm_raw_response = raw_response
        item.llm_model_used = model
        item.status = SkillReviewStatus.READY_FOR_REVIEW

    async def _create_fallback_candidates(
        self,
        item: SkillReviewItem,
        raw_response: str = "",
        reason: str = "llm_unavailable",
    ) -> None:
        """Create deterministic review candidates so the demo path can continue."""
        queue = self._ensure_team_queue(item.team_id)
        specs = self._fallback_skill_specs(item)
        payload = {"skills": specs, "source": "deterministic_fallback", "reason": reason}
        raw = raw_response or json.dumps(payload, ensure_ascii=False)
        self._apply_skill_data(item, specs[0], raw, "deterministic-fallback")
        item.reviewer_notes = f"LLM 不可用，系统已生成演示兜底候选: {reason}"
        known_slugs = self._collect_known_slugs(item.team_id)
        for spec in specs[1:]:
            if spec.get("slug") in known_slugs:
                continue
            extra_item = SkillReviewItem(
                team_id=item.team_id,
                source_text=item.source_text,
                source_title=item.source_title,
                source_type=item.source_type,
                status=SkillReviewStatus.READY_FOR_REVIEW,
            )
            self._apply_skill_data(extra_item, spec, raw, "deterministic-fallback")
            extra_item.reviewer_notes = item.reviewer_notes
            queue[extra_item.item_id] = extra_item
            await self._broadcast(item.team_id, "item_created", {"item": extra_item.to_dict()})
            await self._broadcast(item.team_id, "item_status_changed", {
                "item_id": extra_item.item_id,
                "status": extra_item.status.value,
                "traffic_light": status_traffic_light(extra_item.status),
                "status_icon": status_icon(extra_item.status),
                "status_label": status_label(extra_item.status),
                "llm_confidence": extra_item.llm_confidence,
                "draft_name": extra_item.draft_name,
                "draft_scope": extra_item.draft_scope,
            })

    # ── SSE Subscription ──────────────────────────────────────────────

    def subscribe(self, team_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._sse_queues.setdefault(team_id, []).append(q)
        return q

    def unsubscribe(self, team_id: str, q: asyncio.Queue):
        qs = self._sse_queues.get(team_id, [])
        if q in qs:
            qs.remove(q)

    # ── Core Operations ───────────────────────────────────────────────

    async def start_extraction(
        self,
        team_id: str,
        source_text: str,
        source_title: str = "",
        source_type: str = "chat",
        source_meta: Optional[Dict[str, Any]] = None,
    ) -> SkillReviewItem:
        """Create a queue item and start async LLM pre-filling."""
        queue = self._ensure_team_queue(team_id)

        incoming_meta: Dict[str, Any] = source_meta if isinstance(source_meta, dict) else {}

        if self._is_deleted_source(team_id, source_type, source_title, incoming_meta, source_text):
            logger.info("⏭️ 删除墓碑拦截: 来源已被手动删除，跳过自动萃取")
            await self._broadcast(team_id, "dedup_skipped", {
                "existing_item_id": "",
                "existing_name": source_title or "已删除来源",
                "existing_status": SkillReviewStatus.REJECTED.value,
                "message": "该来源已手动删除，默认不再自动萃取",
            })
            blocked = SkillReviewItem(
                team_id=team_id,
                source_text=source_text,
                source_title=source_title,
                source_type=source_type,
                source_meta=incoming_meta,
                status=SkillReviewStatus.REJECTED,
            )
            blocked.reviewer_notes = "source_deleted_tombstone"
            return blocked

        incoming_key = self._source_key(source_type, source_title, incoming_meta)
        incoming_hash = self._source_text_hash(source_text)

        # ── Dedup: same source context + same full text hash ──
        # ponytail: this keeps dedup simple and deterministic; if we need near-duplicate matching later, upgrade to fuzzy hash.
        for existing in queue.values():
            existing_meta = existing.source_meta if isinstance(existing.source_meta, dict) else {}
            existing_key = self._source_key(existing.source_type, existing.source_title, existing_meta)
            existing_hash = self._source_text_hash(existing.source_text)
            if incoming_hash != existing_hash:
                continue

            has_both_keys = bool(incoming_key and existing_key)
            if has_both_keys and incoming_key != existing_key:
                continue

            if (not has_both_keys) and (
                self._norm_text(source_type) != self._norm_text(existing.source_type)
                or self._norm_text(source_title) != self._norm_text(existing.source_title)
            ):
                continue

                # Same source text already in queue
                logger.info(f"⏭️ 去重跳过: 相同来源文本已在队列中 (item={existing.item_id})")
                await self._broadcast(team_id, "dedup_skipped", {
                    "existing_item_id": existing.item_id,
                    "existing_name": existing.draft_name or existing.source_title,
                    "existing_status": existing.status.value,
                    "message": f"该文本已萃取过「{existing.draft_name or existing.source_title}」",
                })
                return existing

        item = SkillReviewItem(
            team_id=team_id,
            source_text=source_text,
            source_title=source_title or f"来源 {len(queue) + 1}",
            source_type=source_type,
            source_meta=incoming_meta,
            status=SkillReviewStatus.PENDING,
        )
        queue[item.item_id] = item
        self._persist_queue(team_id)

        await self._broadcast(team_id, "item_created", {
            "item": item.to_dict(),
        })

        # Fire async LLM pre-fill (non-blocking)
        # P7: 包裹 token_scope，使萃取 LLM token 归因到 run_id
        from .token_context import token_scope, new_run_id
        extract_run_id = new_run_id("extract")
        item.source_meta = {**(item.source_meta or {}), "token_run_id": extract_run_id}
        self._persist_queue(team_id)

        async def _prefill_with_scope():
            with token_scope(run_id=extract_run_id, phase="extract",
                             team_id=team_id, skill_id=item.draft_slug or ""):
                await self._llm_prefill(item)

        task = asyncio.create_task(_prefill_with_scope())
        def _on_prefill_done(t):
            if t.cancelled():
                return
            exc = t.exception()
            if exc:
                logger.error("LLM prefill task error for %s: %s", item.item_id, exc)
        task.add_done_callback(_on_prefill_done)

        return item

    async def _llm_prefill(self, item: SkillReviewItem) -> None:
        """Async LLM call to pre-fill skill fields from source text."""
        item.status = SkillReviewStatus.LLM_PREFILLING
        await self._broadcast(item.team_id, "item_status_changed", {
            "item_id": item.item_id,
            "status": item.status.value,
            "traffic_light": status_traffic_light(item.status),
            "status_icon": status_icon(item.status),
            "status_label": status_label(item.status),
        })

        try:
            harness = get_chat_harness()

            # Preprocess: identify knowledge clusters
            clusters = preprocess_knowledge_clusters(item.source_text)
            cluster_summary = "\n".join(
                f"  Cluster {i+1}: 「{cl['title']}」({len(cl['content'])} chars)"
                for i, cl in enumerate(clusters)
            )

            prompt = f"""Analyze the following text using the three reverse-engineering algorithms (De-contextualization, Anti-Pattern Extraction, Critical Path) to extract multiple reusable skills.

Source title: {item.source_title}
Source type: {item.source_type}

Knowledge clusters identified ({len(clusters)} clusters):
{cluster_summary}

--- BEGIN SOURCE TEXT ---
{item.source_text[:12000]}
--- END SOURCE TEXT ---

The text has been segmented into {len(clusters)} knowledge clusters.

EXTRACTION INSTRUCTIONS:
1. Apply Algorithm 1 (De-contextualization): Strip specific product/service names, extract abstract capabilities that are platform-agnostic. Each abstract pattern = 1 skill.
2. Apply Algorithm 2 (Anti-Pattern Extraction): Find every pain point, failure case, FAQ objection. Invert each into a defensive skill with clear anti-patterns.
3. Apply Algorithm 3 (Critical Path): Identify the 3-5 make-or-break decision points from any SOP/procedure described. Each decision point = 1 skill.

Target: Extract {max(3, min(len(clusters) + 2, 8))} skills total. Each skill should be atomic (one capability), not a summary of the whole document.
For each skill, set "extraction_algorithm" to indicate which algorithm produced it.
Output ONLY valid JSON."""

            result = await harness.chat(
                prompt=prompt,
                system_prompt=SKILL_EXTRACTION_SYSTEM_PROMPT,
                agent_id="skill_extractor",
            )

            # Parse LLM response
            response_text = result.response if hasattr(result, 'response') else (result.content if hasattr(result, 'content') else str(result))
            item.llm_raw_response = response_text
            item.llm_model_used = result.model if hasattr(result, 'model') else "unknown"

            # Extract JSON from response
            parsed = None if self._is_unusable_llm_text(response_text) else self._parse_llm_json(response_text)
            if self._is_unusable_llm_text(response_text):
                await self._create_fallback_candidates(item, response_text, "provider_fallback")
            elif parsed and parsed.get("skills"):
                all_skills = parsed["skills"]

                # ── Slug-level dedup: filter out skills that already exist ──
                known_slugs = self._collect_known_slugs(item.team_id)
                dedup_skills = []
                for sd in all_skills:
                    slug = sd.get("slug", "")
                    if slug and slug in known_slugs:
                        logger.info(f"⏭️ slug 去重: 「{sd.get('name', slug)}」已存在，跳过")
                        await self._broadcast(item.team_id, "dedup_slug_skipped", {
                            "item_id": item.item_id,
                            "skipped_slug": slug,
                            "skipped_name": sd.get("name", slug),
                            "message": f"技能「{sd.get('name', slug)}」已存在，跳过重复萃取",
                        })
                    else:
                        dedup_skills.append(sd)
                all_skills = dedup_skills if dedup_skills else []  # Empty if all duplicates

                if not all_skills:
                    # ALL skills were duplicates — mark item as duplicate, don't enqueue
                    item.status = SkillReviewStatus.REJECTED
                    item.reviewer_notes = "所有萃取结果均为已有技能，自动跳过"
                    item.draft_name = parsed["skills"][0].get("name", "")[:64] if parsed["skills"] else ""
                    await self._broadcast(item.team_id, "dedup_all_skipped", {
                        "item_id": item.item_id,
                        "skipped_names": [s.get("name", s.get("slug", "")) for s in parsed["skills"]],
                        "message": f"萃取的 {len(parsed['skills'])} 个技能均已存在，已自动跳过",
                    })
                    self._persist_queue(item.team_id)
                    return

                # Fill primary item with first skill
                skill_data = all_skills[0]
                item.draft_name = skill_data.get("name", "")[:64]
                item.draft_description = skill_data.get("description", "")[:500]
                item.draft_category = skill_data.get("category", "general")
                item.draft_icon = skill_data.get("icon", "⚡")
                item.draft_slug = skill_data.get("slug", "")
                item.draft_instructions = skill_data.get("instructions", "")
                item.draft_required_tools = skill_data.get("required_tools", [])
                item.draft_scope = skill_data.get("scope", "personal")
                item.llm_confidence = float(skill_data.get("confidence", 0.5))
                item.status = SkillReviewStatus.READY_FOR_REVIEW

                # Create additional items for skills 2+ (multi-skill extraction)
                for extra_skill in all_skills[1:]:
                    extra_item = SkillReviewItem(
                        team_id=item.team_id,
                        source_text=item.source_text,
                        source_title=item.source_title,
                        source_type=item.source_type,
                        source_meta=dict(item.source_meta or {}),
                        status=SkillReviewStatus.READY_FOR_REVIEW,
                    )
                    extra_item.draft_name = extra_skill.get("name", "")[:64]
                    extra_item.draft_description = extra_skill.get("description", "")[:500]
                    extra_item.draft_category = extra_skill.get("category", "general")
                    extra_item.draft_icon = extra_skill.get("icon", "⚡")
                    extra_item.draft_slug = extra_skill.get("slug", "")
                    extra_item.draft_instructions = extra_skill.get("instructions", "")
                    extra_item.draft_required_tools = extra_skill.get("required_tools", [])
                    extra_item.draft_scope = extra_skill.get("scope", "personal")
                    extra_item.llm_confidence = float(extra_skill.get("confidence", 0.5))
                    extra_item.llm_raw_response = response_text
                    extra_item.llm_model_used = item.llm_model_used
                    queue = self._ensure_team_queue(item.team_id)
                    queue[extra_item.item_id] = extra_item
                    await self._broadcast(item.team_id, "item_created", {
                        "item": extra_item.to_dict(),
                    })
                    await self._broadcast(item.team_id, "item_status_changed", {
                        "item_id": extra_item.item_id,
                        "status": extra_item.status.value,
                        "traffic_light": status_traffic_light(extra_item.status),
                        "status_icon": status_icon(extra_item.status),
                        "status_label": status_label(extra_item.status),
                        "llm_confidence": extra_item.llm_confidence,
                        "draft_name": extra_item.draft_name,
                        "draft_scope": extra_item.draft_scope,
                    })
            else:
                await self._create_fallback_candidates(item, response_text, "json_parse_empty")

        except Exception as e:
            logger.error(f"LLM pre-fill failed for {item.item_id}: {e}")
            await self._create_fallback_candidates(item, str(e), f"exception:{str(e)[:80]}")

        await self._broadcast(item.team_id, "item_status_changed", {
            "item_id": item.item_id,
            "status": item.status.value,
            "traffic_light": status_traffic_light(item.status),
            "status_icon": status_icon(item.status),
            "status_label": status_label(item.status),
            "llm_confidence": item.llm_confidence,
            "draft_name": item.draft_name,
            "draft_scope": item.draft_scope,
        })
        self._persist_queue(item.team_id)

    def _parse_llm_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from LLM response, handling markdown fences."""
        import re
        # Try to find JSON in markdown code block
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # Try parsing raw text
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        # Try finding first { ... } block
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return None

    # ── Queue Operations ──────────────────────────────────────────────

    def get_queue(self, team_id: str, status_filter: str = "") -> List[Dict[str, Any]]:
        """Get review queue items, optionally filtered by status."""
        queue = self._queues.get(team_id, {})
        items = list(queue.values())
        if status_filter:
            items = [i for i in items if i.status.value == status_filter]
        # Sort: newest first
        items.sort(key=lambda i: i.created_at, reverse=True)
        return [i.to_dict() for i in items]

    def get_item(self, team_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a single review item with full detail for diff view."""
        queue = self._queues.get(team_id, {})
        item = queue.get(item_id)
        if item is None:
            return None
        d = item.to_dict()
        # Add diff-compatible fields
        d["source_text"] = item.source_text
        d["llm_raw_response"] = item.llm_raw_response
        return d

    async def approve_item(
        self,
        team_id: str,
        item_id: str,
        reviewer: str = "",
        edited_fields: Optional[Dict[str, Any]] = None,
        skill_type: str = "reserve",
        target_agent_id: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Approve a skill item with type: trait (assign to one agent), public (all agents), reserve (store only)."""
        queue = self._queues.get(team_id, {})
        item = queue.get(item_id)
        if item is None:
            return None

        # Apply any user edits before approval
        if edited_fields:
            for field, value in edited_fields.items():
                if hasattr(item, f"draft_{field}"):
                    setattr(item, f"draft_{field}", value)

        item.status = SkillReviewStatus.APPROVED
        item.reviewed_by = reviewer
        item.reviewed_at = datetime.now(timezone.utc).isoformat()

        # Write to skill_registry + team skills table (skip if slug already registered)
        skill_def = item.to_skill_definition()
        already_registered = False
        try:
            from .api import _skill_registry
            if _skill_registry and skill_def.slug:
                existing = _skill_registry.get_by_slug(skill_def.slug)
                if existing:
                    already_registered = True
                    logger.info(f"⏭️ approve 去重: slug={skill_def.slug} 已注册，跳过写入")
        except Exception:
            pass
        if not already_registered:
            await self._write_skill_to_tables(team_id, skill_def)

        # G1-2: 萃取完成后默认写入三池分类为 reserve，后续由验证/周期重算决定毕业。
        try:
            from .skill_classifier import get_classification_store
            get_classification_store().seed_reserve_from_extraction(
                team_id=team_id,
                skill={
                    "skill_id": skill_def.skill_id or skill_def.slug,
                    "slug": skill_def.slug,
                    "name": skill_def.name,
                    "effectiveness": skill_def.effectiveness,
                },
                source="skill_extract_approve",
            )
        except Exception as e:
            logger.warning(f"Could not seed reserve classification for extracted skill: {e}")

        # Assign skill to agents based on skill_type
        try:
            from .api import _team_manager
            if _team_manager:
                team = _team_manager.get_team(team_id)
                if team:
                    skill_id = skill_def.skill_id or skill_def.slug
                    if skill_type == "trait" and target_agent_id:
                        agent = team.agents.get(target_agent_id)
                        if agent and skill_id not in agent.skills:
                            agent.skills.append(skill_id)
                            logger.info(f"🎯 特质技能 {skill_id} 已赋予智能体 {target_agent_id}")
                    elif skill_type == "public":
                        for agent in team.agents.values():
                            if skill_id not in agent.skills:
                                agent.skills.append(skill_id)
                        logger.info(f"🌍 公共技能 {skill_id} 已赋予团队 {team_id} 全部 {len(team.agents)} 个智能体")
                    else:
                        logger.info(f"📦 储备技能 {skill_id} 已入库，未赋予任何智能体")
        except Exception as e:
            logger.warning(f"Could not assign skill to agents: {e}")

        # Fire SkillApproved event
        await self._broadcast(team_id, "skill_approved", {
            "item_id": item_id,
            "skill_id": skill_def.skill_id,
            "skill_name": skill_def.name,
            "approved_by": reviewer,
            "skill_type": skill_type,
            "target_agent_id": target_agent_id,
            "skill": skill_def.to_dict(),
        })
        self._persist_queue(team_id)

        result = item.to_dict()
        result["skill_type"] = skill_type
        result["target_agent_id"] = target_agent_id
        return result

    async def reject_item(
        self,
        team_id: str,
        item_id: str,
        reviewer: str = "",
        reason: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Reject a skill item with reason."""
        queue = self._queues.get(team_id, {})
        item = queue.get(item_id)
        if item is None:
            return None

        item.status = SkillReviewStatus.REJECTED
        item.reviewed_by = reviewer
        item.reviewer_notes = reason
        item.reviewed_at = datetime.now(timezone.utc).isoformat()

        await self._broadcast(team_id, "skill_rejected", {
            "item_id": item_id,
            "reason": reason,
            "reviewer": reviewer,
        })
        self._persist_queue(team_id)

        return item.to_dict()

    async def edit_item(
        self,
        team_id: str,
        item_id: str,
        field_updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Edit a draft item's fields before approval."""
        queue = self._queues.get(team_id, {})
        item = queue.get(item_id)
        if item is None:
            return None

        field_mapping = {
            "name": "draft_name",
            "description": "draft_description",
            "category": "draft_category",
            "icon": "draft_icon",
            "slug": "draft_slug",
            "instructions": "draft_instructions",
            "required_tools": "draft_required_tools",
        }

        for field, value in field_updates.items():
            attr = field_mapping.get(field)
            if attr and hasattr(item, attr):
                setattr(item, attr, value)

        await self._broadcast(team_id, "item_edited", {
            "item_id": item_id,
            "updates": field_updates,
        })
        self._persist_queue(team_id)

        return item.to_dict()

    async def delete_item(self, team_id: str, item_id: str) -> bool:
        """Remove an item from the queue."""
        queue = self._queues.get(team_id, {})
        if item_id in queue:
            item = queue[item_id]
            source_meta = item.source_meta if isinstance(item.source_meta, dict) else {}
            self._mark_source_deleted(team_id, item.source_type, item.source_title, source_meta, item.source_text)
            del queue[item_id]
            await self._broadcast(team_id, "item_deleted", {"item_id": item_id})
            self._persist_queue(team_id)
            return True
        return False

    # ── Dedup Helpers ──────────────────────────────────────────────

    def _collect_known_slugs(self, team_id: str) -> set:
        """Collect all known slugs from queue + registry for dedup."""
        slugs = set()
        # From queue
        for item in self._queues.get(team_id, {}).values():
            if item.draft_slug:
                slugs.add(item.draft_slug)
        # From registry
        try:
            from .api import _skill_registry
            if _skill_registry:
                for s in _skill_registry.list_all():
                    if s.slug:
                        slugs.add(s.slug)
        except Exception:
            pass
        # From team skills
        try:
            from .api import _team_manager
            if _team_manager:
                team = _team_manager.get_team(team_id)
                if team:
                    for s in team.skills.values():
                        if s.slug:
                            slugs.add(s.slug)
        except Exception:
            pass
        return slugs

    # ── Skill Table Writing ──────────────────────────────────────────

    async def _write_skill_to_tables(self, team_id: str, skill_def: SkillDefinition) -> None:
        """Write approved skill to both SkillRegistry and team skills table."""
        try:
            from .api import _skill_registry
            if _skill_registry:
                _skill_registry.register(skill_def)
        except (ImportError, Exception) as e:
            logger.warning(f"Could not write skill to registry: {e}")

        try:
            from .api import _team_manager
            if _team_manager:
                team = _team_manager.get_team(team_id)
                if team:
                    team.add_skill(skill_def)
                    _team_manager._persist()  # 持久化 team，确保技能不丢失
        except (ImportError, Exception) as e:
            logger.warning(f"Could not write skill to team: {e}")

    def _rehydrate_approved_skill(self, team_id: str, skill_def: SkillDefinition) -> None:
        """Re-register an approved skill into in-memory tables on startup (sync, no broadcast)."""
        try:
            from .api import _skill_registry
            if _skill_registry:
                _skill_registry.register(skill_def)
        except (ImportError, Exception) as e:
            logger.warning(f"Could not rehydrate skill to registry: {e}")

        try:
            from .api import _team_manager
            if _team_manager:
                team = _team_manager.get_team(team_id)
                if team:
                    team.add_skill(skill_def)
        except (ImportError, Exception) as e:
            logger.warning(f"Could not rehydrate skill to team: {e}")


# ── Global Singleton ──────────────────────────────────────────────────────


# ── Knowledge Cluster Preprocessing ───────────────────────────────────────


def _chunk_by_structure(text: str) -> List[str]:
    """Split text into semantic chunks by headings, blank-line blocks, or fixed size."""
    import re
    # Try splitting by markdown headings (##, ###, etc.)
    heading_pattern = re.compile(r'^#{1,4}\s+.+', re.MULTILINE)
    positions = [m.start() for m in heading_pattern.finditer(text)]

    if len(positions) >= 2:
        chunks = []
        for i, pos in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            chunk = text[pos:end].strip()
            if len(chunk) > 30:
                chunks.append(chunk)
        return chunks if chunks else [text]

    # Fallback: split by double newlines (paragraph blocks)
    blocks = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if len(current) + len(block) > 1500:
            if current:
                chunks.append(current)
            current = block
        else:
            current = (current + "\n\n" + block).strip()
    if current:
        chunks.append(current)
    return chunks if chunks else [text]


def _cluster_chunks(chunks: List[str], max_clusters: int = 5) -> List[List[str]]:
    """Group similar chunks together using TF-IDF cosine similarity."""
    if len(chunks) <= max_clusters:
        return [[c] for c in chunks]

    try:
        import re
        from collections import Counter
        import math

        # Simple TF-IDF
        def tokenize(t):
            return re.findall(r'[a-zA-Z\u4e00-\u9fff]{2,}', t.lower())

        doc_tokens = [tokenize(c) for c in chunks]
        # IDF
        n = len(chunks)
        df = Counter()
        for tokens in doc_tokens:
            for w in set(tokens):
                df[w] += 1
        idf = {w: math.log(n / (1 + v)) for w, v in df.items()}

        # TF-IDF vectors
        def tfidf_vec(tokens):
            tf = Counter(tokens)
            total = len(tokens) or 1
            return {w: (c / total) * idf.get(w, 0) for w, c in tf.items()}

        vecs = [tfidf_vec(t) for t in doc_tokens]

        def cosine_sim(v1, v2):
            common = set(v1) & set(v2)
            if not common:
                return 0.0
            dot = sum(v1[w] * v2[w] for w in common)
            m1 = math.sqrt(sum(x * x for x in v1.values()))
            m2 = math.sqrt(sum(x * x for x in v2.values()))
            return dot / (m1 * m2 + 1e-9)

        # Agglomerative clustering (simple greedy)
        clusters: List[List[int]] = [[i] for i in range(len(chunks))]
        while len(clusters) > max_clusters:
            best_sim, best_pair = -1, (0, 1)
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Average linkage
                    sims = [cosine_sim(vecs[a], vecs[b]) for a in clusters[i] for b in clusters[j]]
                    avg = sum(sims) / len(sims)
                    if avg > best_sim:
                        best_sim = avg
                        best_pair = (i, j)
            i, j = best_pair
            clusters[i].extend(clusters[j])
            clusters.pop(j)

        return [[chunks[idx] for idx in cl] for cl in clusters]
    except Exception as e:
        logger.warning("Clustering failed, falling back to sequential: %s", e)
        return [[c] for c in chunks[:max_clusters]]


def preprocess_knowledge_clusters(text: str) -> List[Dict[str, str]]:
    """Split text into knowledge clusters with titles and content.

    Returns list of {title, content} dicts, each representing a coherent knowledge cluster.
    """
    chunks = _chunk_by_structure(text)
    if len(chunks) <= 1:
        return [{"title": "全文", "content": text}]

    clusters = _cluster_chunks(chunks)
    result = []
    for cl_chunks in clusters:
        combined = "\n\n".join(cl_chunks)
        # Extract title from first heading or first line
        import re
        heading = re.match(r'^#{1,4}\s+(.+)', combined)
        title = heading.group(1).strip() if heading else combined[:40].strip()
        result.append({"title": title, "content": combined})

    logger.info("Preprocessed %d chunks into %d knowledge clusters", len(chunks), len(result))
    return result


_skill_extractor_engine: Optional[SkillExtractorEngine] = None


def get_skill_extractor_engine() -> SkillExtractorEngine:
    """Get or create the global SkillExtractorEngine singleton."""
    global _skill_extractor_engine
    if _skill_extractor_engine is None:
        _skill_extractor_engine = SkillExtractorEngine()
    return _skill_extractor_engine


def init_skill_extractor() -> SkillExtractorEngine:
    """Initialize the skill extractor engine at startup."""
    global _skill_extractor_engine
    _skill_extractor_engine = SkillExtractorEngine()
    return _skill_extractor_engine
