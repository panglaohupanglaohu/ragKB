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
    draft_scope: str = "personal"   # "personal" or "public" — LLM recommendation only

    # Approval disposition (set on approve; not the same as draft_scope)
    # trait = assign one agent · public = all agents · reserve = store only
    skill_type: str = ""
    target_agent_id: str = ""

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
            "skill_type": self.skill_type or "",
            "target_agent_id": self.target_agent_id or "",
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
        # team_id → tombstone keys (skill_id / slug / name) so delete 后不会 rehydrate 复活
        self._deleted_skill_keys: Dict[str, List[str]] = {}
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
        # global skill tombstones (prevent rehydrate after delete)
        try:
            tomb_fp = self.QUEUE_DIR / "_skill_tombstones.json"
            if tomb_fp.exists():
                td = json.loads(tomb_fp.read_text(encoding="utf-8"))
                keys = td.get("deleted_skill_keys") or []
                if isinstance(keys, list):
                    self._deleted_skill_keys["*"] = [str(x) for x in keys if str(x).strip()]
        except Exception as e:
            logger.warning("Failed to load skill tombstones: %s", e)
        for fp in self.QUEUE_DIR.glob("*.json"):
            if fp.name.startswith("_"):
                continue
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                team_id = data.get("team_id", fp.stem)
                items = data.get("items", [])
                queue = self._ensure_team_queue(team_id)
                deleted_sources = data.get("deleted_sources", [])
                if isinstance(deleted_sources, list):
                    self._deleted_sources[team_id] = [str(x) for x in deleted_sources if str(x).strip()]
                deleted_skills = data.get("deleted_skill_keys", [])
                if isinstance(deleted_skills, list):
                    self._deleted_skill_keys[team_id] = [str(x) for x in deleted_skills if str(x).strip()]
                approved_count = 0
                skipped_tombstone = 0
                for item_data in items:
                    item = SkillReviewItem.from_dict(item_data) if hasattr(SkillReviewItem, 'from_dict') else self._item_from_dict(item_data)
                    queue[item.item_id] = item
                    # Re-register approved skills into team tables on startup
                    if item.status == SkillReviewStatus.APPROVED and item.draft_slug:
                        if self._is_skill_tombstoned(team_id, skill_id="", slug=item.draft_slug, name=item.draft_name):
                            skipped_tombstone += 1
                            continue
                        try:
                            skill_def = item.to_skill_definition()
                            self._rehydrate_approved_skill(team_id, skill_def)
                            approved_count += 1
                        except Exception as e:
                            logger.warning("Failed to rehydrate approved skill %s: %s", item.item_id, e)
                logger.info(
                    "Loaded %d queued items for team %s (%d approved rehydrated, %d tombstone-skipped)",
                    len(items), team_id, approved_count, skipped_tombstone,
                )
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
                "deleted_skill_keys": list(self._deleted_skill_keys.get(team_id, [])),
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

    def _clear_source_deleted(
        self,
        team_id: str,
        source_type: str,
        source_title: str,
        source_meta: Dict[str, Any],
        source_text: str,
    ) -> bool:
        """Remove tombstone so user can re-extract after cleaning test data."""
        fp = self._source_fingerprint(source_type, source_title, source_meta, source_text)
        deleted = self._deleted_sources.get(team_id, [])
        if fp not in deleted:
            return False
        self._deleted_sources[team_id] = [x for x in deleted if x != fp]
        return True

    def _same_source_item(
        self,
        item: SkillReviewItem,
        *,
        source_type: str,
        source_title: str,
        source_meta: Dict[str, Any],
        source_text: str,
        incoming_key: str,
        incoming_hash: str,
    ) -> bool:
        """Whether queue item is the same discussion/text source."""
        if self._source_text_hash(item.source_text) != incoming_hash:
            return False
        existing_meta = item.source_meta if isinstance(item.source_meta, dict) else {}
        existing_key = self._source_key(item.source_type, item.source_title, existing_meta)
        if incoming_key and existing_key:
            return incoming_key == existing_key
        return (
            self._norm_text(item.source_type) == self._norm_text(source_type)
            and self._norm_text(item.source_title) == self._norm_text(source_title)
        )

    def _purge_same_source_queue(
        self,
        team_id: str,
        *,
        source_type: str,
        source_title: str,
        source_meta: Dict[str, Any],
        source_text: str,
        keep_statuses: Optional[set] = None,
    ) -> List[str]:
        """Remove non-approved queue items from the same source (force re-extract cleanup).

        Keeps APPROVED by default so history isn't wiped; purges pending/review/rejected/error.
        """
        queue = self._ensure_team_queue(team_id)
        incoming_key = self._source_key(source_type, source_title, source_meta)
        incoming_hash = self._source_text_hash(source_text)
        keep = keep_statuses or {SkillReviewStatus.APPROVED}
        removed: List[str] = []
        for iid, it in list(queue.items()):
            if it.status in keep:
                continue
            if not self._same_source_item(
                it,
                source_type=source_type,
                source_title=source_title,
                source_meta=source_meta,
                source_text=source_text,
                incoming_key=incoming_key,
                incoming_hash=incoming_hash,
            ):
                continue
            del queue[iid]
            removed.append(iid)
        return removed

    def _is_skill_tombstoned(
        self,
        team_id: str,
        *,
        skill_id: str = "",
        slug: str = "",
        name: str = "",
    ) -> bool:
        keys = set(self._deleted_skill_keys.get(team_id, []) or [])
        # also check global-ish tombstones under "*" for cross-team registry deletes
        keys |= set(self._deleted_skill_keys.get("*", []) or [])
        for k in (skill_id, slug, name):
            kk = str(k or "").strip()
            if kk and kk in keys:
                return True
        return False

    def tombstone_skill_keys(
        self,
        team_id: str,
        *,
        skill_ids: Any = None,
        slugs: Any = None,
        names: Any = None,
    ) -> None:
        """Record deleted skill ids/slugs/names so rehydrate will not resurrect them."""
        bucket = self._deleted_skill_keys.setdefault(team_id or "*", [])
        global_bucket = self._deleted_skill_keys.setdefault("*", [])
        for collection in (skill_ids, slugs, names):
            if not collection:
                continue
            for raw in collection:
                k = str(raw or "").strip()
                if not k:
                    continue
                if k not in bucket:
                    bucket.append(k)
                if k not in global_bucket:
                    global_bucket.append(k)
        if len(bucket) > 800:
            del bucket[: len(bucket) - 800]
        if len(global_bucket) > 1200:
            del global_bucket[: len(global_bucket) - 1200]
        try:
            self._persist_queue(team_id or list(self._queues.keys())[0] if self._queues else "default")
        except Exception:
            pass
        # persist global tombstones into a dedicated file if team_id is *
        if team_id == "*" or True:
            try:
                self.QUEUE_DIR.mkdir(parents=True, exist_ok=True)
                tomb_fp = self.QUEUE_DIR / "_skill_tombstones.json"
                tomb_fp.write_text(
                    json.dumps(
                        {"deleted_skill_keys": list(self._deleted_skill_keys.get("*", []))},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except Exception:
                pass

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
        item.skill_type = str(d.get("skill_type") or "")
        item.target_agent_id = str(d.get("target_agent_id") or "")
        item.llm_confidence = d.get("llm_confidence", 0)
        item.llm_raw_response = d.get("llm_raw_response", "")
        item.llm_model_used = d.get("llm_model_used", "")
        item.reviewer_notes = d.get("reviewer_notes", "")
        item.reviewed_by = d.get("reviewed_by", "")
        item.reviewed_at = d.get("reviewed_at", "")
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

    def _topic_label_from_item(self, item: SkillReviewItem) -> str:
        """Short display topic from source title/text (no template prefix)."""
        import re

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

        # 标题优先；关键词过滤表格列名等噪声（「方案文档/执行记录」常来自执行计划表头）
        noise = {
            "方案文档", "执行记录", "验收结论", "负责人", "优先级", "依赖", "预期产出",
            "序号", "任务", "输出", "输入", "步骤", "阶段",
        }
        clean_terms = [t for t in top_terms if t not in noise and t.lower() not in noise]
        topic_label = source_title.strip() if source_title else ""
        if not topic_label and clean_terms:
            topic_label = " / ".join(clean_terms[:2])
        if not topic_label:
            topic_label = "当前议题"
        # 截断过长标题，避免「方案文档 / 执行记录需求拆解…」式噪声名
        if len(topic_label) > 28:
            topic_label = topic_label[:28].rstrip() + "…"
        # 剥离历史前缀，避免「【回退草稿】【回退草稿】…」叠写
        for prefix in ("【回退草稿】", "[回退草稿]", "回退草稿·", "回退草稿:"):
            if topic_label.startswith(prefix):
                topic_label = topic_label[len(prefix):].strip()
        return topic_label or "当前议题"

    def _fallback_skill_specs(self, item: SkillReviewItem) -> List[Dict[str, Any]]:
        """Last-resort offline placeholder when TSE local decode also fails.

        Naming rule (user-facing): **never** put 「【回退草稿】」 in draft_name.
        Mark offline status via description + llm_model_used=deterministic-fallback.
        Prefer a single source-grounded skill (not 3 generic templates).
        """
        suffix = item.item_id.lower()[:8]
        topic_label = self._topic_label_from_item(item)
        source_text = (item.source_text or "").strip()
        topic_excerpt = source_text[:260] or (item.source_title or "") or "议题原文"
        name = topic_label[:48] if topic_label else "讨论技能草案"

        return [
            {
                "name": name,
                "description": (
                    "离线占位草案（TSE/LLM 解码未成功，非正式技能名）。"
                    "请编辑指令后审核，或修好模型后强制重萃。"
                ),
                "category": "research",
                "icon": "🧭",
                "slug": f"offline-placeholder-{suffix}",
                "instructions": (
                    f"基于原文片段『{topic_excerpt}』：\n"
                    "1. 列出业务目标与验收口径\n"
                    "2. 明确前置条件、依赖与不可变约束\n"
                    "3. 输出「必须做 / 可选做 / 禁止做」三栏\n"
                    "4. 补最小验证步骤与回滚点"
                ),
                "required_tools": ["read_file", "web_search"],
                "confidence": 0.32,
                "scope": "public",
                "extraction_algorithm": "deterministic-offline",
            },
        ]

    def _try_tse_local_skills(
        self,
        item: SkillReviewItem,
        *,
        focus_indices: Optional[List[int]] = None,
        category_hint: str = "",
        tools_hint: Optional[List[str]] = None,
        transcript=None,
    ) -> List[Dict[str, Any]]:
        """Build discussion-grounded skills without ChatHarness (no 【回退草稿】 titles)."""
        try:
            from .tse.decoder import synthesize_skills_local
            from .tse.transcript import parse_transcript

            tr = transcript
            if tr is None:
                meta = item.source_meta if isinstance(item.source_meta, dict) else {}
                tr = parse_transcript(
                    item.source_text or "",
                    source_title=item.source_title or "",
                    source_meta=meta,
                )
            if not tr or not getattr(tr, "messages", None):
                return []
            idxs = list(focus_indices or [])
            if not idxs:
                idxs = list(range(min(8, len(tr.messages))))
            skills = synthesize_skills_local(
                tr,
                focus_indices=idxs,
                category_hint=category_hint or "",
                tools_hint=list(tools_hint or []),
            )
            cleaned: List[Dict[str, Any]] = []
            for s in skills or []:
                if not isinstance(s, dict):
                    continue
                name = str(s.get("name") or "").strip()
                # Guard: never surface legacy prefix even if upstream regresses
                for prefix in ("【回退草稿】", "[回退草稿]"):
                    if name.startswith(prefix):
                        name = name[len(prefix):].strip()
                if name:
                    s = dict(s)
                    s["name"] = name[:64]
                cleaned.append(s)
            return cleaned
        except Exception as e:
            logger.warning("TSE local synthesize failed: %s", e)
            return []

    def _apply_skill_data(self, item: SkillReviewItem, skill_data: Dict[str, Any], raw_response: str, model: str) -> None:
        name = str(skill_data.get("name", "") or "")
        for p in ("【回退草稿】", "[回退草稿]"):
            if name.startswith(p):
                name = name[len(p):].strip()
        item.draft_name = name[:64]
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
        *,
        tse_result=None,
    ) -> None:
        """Create review candidates when Stage4 LLM path fails.

        Order:
          1) TSE local synthesize (discussion-grounded, real names) if possible
          2) single offline placeholder (topic name, no 「【回退草稿】」 prefix)

        Only ONE set per source: collapse same-source pending drafts first.
        """
        queue = self._ensure_team_queue(item.team_id)
        meta = item.source_meta if isinstance(item.source_meta, dict) else {}
        key = self._source_key(item.source_type, item.source_title, meta)
        h = self._source_text_hash(item.source_text)

        # Collapse existing same-source non-approved drafts before writing
        for iid, it in list(queue.items()):
            if iid == item.item_id:
                continue
            if it.status == SkillReviewStatus.APPROVED:
                continue
            if not self._same_source_item(
                it,
                source_type=item.source_type,
                source_title=item.source_title,
                source_meta=meta,
                source_text=item.source_text,
                incoming_key=key,
                incoming_hash=h,
            ):
                continue
            model_used = (it.llm_model_used or "")
            if model_used.startswith("deterministic") or model_used.startswith("tse+local") or it.status in (
                SkillReviewStatus.READY_FOR_REVIEW,
                SkillReviewStatus.ERROR,
                SkillReviewStatus.REJECTED,
                SkillReviewStatus.PENDING,
                SkillReviewStatus.LLM_PREFILLING,
            ):
                del queue[iid]
                try:
                    await self._broadcast(item.team_id, "item_deleted", {"item_id": iid, "reason": "fallback_dedupe"})
                except Exception:
                    pass

        # Prefer TSE local grounded skills over generic offline templates
        focus = []
        cat = ""
        tools: List[str] = []
        transcript = None
        if tse_result is not None:
            focus = list(getattr(tse_result, "focus_indices", None) or [])
            cat = str(getattr(tse_result, "category_hint", "") or "")
            tools = list(getattr(tse_result, "tools_hint", None) or [])
            transcript = getattr(tse_result, "transcript", None)
        if not focus and isinstance(meta.get("tse"), dict):
            focus = list(meta["tse"].get("focus_indices") or [])
            cat = cat or str(meta["tse"].get("category_hint") or "")
            tools = tools or list(meta["tse"].get("tools_hint") or [])

        local_skills = self._try_tse_local_skills(
            item,
            focus_indices=focus,
            category_hint=cat,
            tools_hint=tools,
            transcript=transcript,
        )
        if local_skills:
            raw = raw_response or json.dumps(
                {"skills": local_skills, "source": "tse_local", "reason": reason},
                ensure_ascii=False,
            )
            model_tag = "tse+local(offline)"
            item.llm_model_used = model_tag
            item.reviewer_notes = f"LLM 解码失败，已用 TSE 本地合成（讨论锚定）: {reason}"
            await self._ingest_extracted_skills(item, local_skills, response_text=raw)
            # ensure model tag survives ingest (ingest doesn't always set it)
            item.llm_model_used = model_tag
            item.llm_raw_response = raw
            return

        specs = self._fallback_skill_specs(item)
        payload = {"skills": specs, "source": "deterministic_fallback", "reason": reason}
        raw = raw_response or json.dumps(payload, ensure_ascii=False)

        self._apply_skill_data(item, specs[0], raw, "deterministic-fallback")
        item.reviewer_notes = f"TSE/LLM 均不可用，已生成单条离线占位草案: {reason}"
        # Only primary offline placeholder (no multi-template stack)
        return

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
        *,
        force: bool = False,
    ) -> SkillReviewItem:
        """Create a queue item and start async LLM pre-filling.

        force=True（用户点「开始萃取」）: 清除来源墓碑，允许删测数据后重新萃取。
        force=False（自动萃取）: 仍尊重 deleted_sources，避免删了又自动冒出来。
        """
        queue = self._ensure_team_queue(team_id)

        incoming_meta: Dict[str, Any] = source_meta if isinstance(source_meta, dict) else {}
        # 显式 force 或 meta 标记（技能萃取页始终带 force / force_reextract）
        force = bool(force) or bool(incoming_meta.get("force") or incoming_meta.get("force_reextract"))

        if self._is_deleted_source(team_id, source_type, source_title, incoming_meta, source_text):
            if force:
                cleared = self._clear_source_deleted(
                    team_id, source_type, source_title, incoming_meta, source_text
                )
                logger.info(
                    "🔓 强制重萃: 已清除来源墓碑 team=%s cleared=%s title=%s",
                    team_id, cleared, source_title,
                )
            else:
                logger.info("⏭️ 删除墓碑拦截: 来源已被手动删除，跳过自动萃取")
                await self._broadcast(team_id, "dedup_skipped", {
                    "existing_item_id": "",
                    "existing_name": source_title or "已删除来源",
                    "existing_status": SkillReviewStatus.REJECTED.value,
                    "message": "该来源已手动删除，默认不再自动萃取（手动点「开始萃取」可强制重萃）",
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

        # ── force：先清同来源旧草稿，避免回退草稿叠 6 份 ──
        if force:
            purged = self._purge_same_source_queue(
                team_id,
                source_type=source_type,
                source_title=source_title,
                source_meta=incoming_meta,
                source_text=source_text,
            )
            if purged:
                logger.info("🧹 force 重萃清同来源旧项 team=%s n=%d ids=%s", team_id, len(purged), purged[:12])
                self._persist_queue(team_id)
                for pid in purged:
                    try:
                        await self._broadcast(team_id, "item_deleted", {"item_id": pid, "reason": "force_reextract_purge"})
                    except Exception:
                        pass

        # ── Dedup: same source + same full text，仅对「仍在处理/待审」生效 ──
        _ACTIVE = {
            SkillReviewStatus.PENDING,
            SkillReviewStatus.LLM_PREFILLING,
            SkillReviewStatus.READY_FOR_REVIEW,
        }
        for existing in list(queue.values()):
            if existing.status not in _ACTIVE:
                continue
            if not self._same_source_item(
                existing,
                source_type=source_type,
                source_title=source_title,
                source_meta=incoming_meta,
                source_text=source_text,
                incoming_key=incoming_key,
                incoming_hash=incoming_hash,
            ):
                continue
            # Same source already actively in queue (non-force path, or leftover after purge)
            logger.info(f"⏭️ 去重跳过: 相同来源文本已在队列中 (item={existing.item_id})")
            await self._broadcast(team_id, "dedup_skipped", {
                "existing_item_id": existing.item_id,
                "existing_name": existing.draft_name or existing.source_title,
                "existing_status": existing.status.value,
                "message": f"该文本已在队列中「{existing.draft_name or existing.source_title}」({existing.status.value})，可删除后重萃或打开该项继续审核",
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
        """Async pre-fill via TSE (TCN-Skill-Extractor) then review queue.

        Pipeline: transcript → hash/Longformer encode → TCN → skill-query
        cross-attention → constrained JSON decoder (ChatHarness).
        """
        item.status = SkillReviewStatus.LLM_PREFILLING
        await self._broadcast(item.team_id, "item_status_changed", {
            "item_id": item.item_id,
            "status": item.status.value,
            "traffic_light": status_traffic_light(item.status),
            "status_icon": status_icon(item.status),
            "status_label": status_label(item.status),
            # 进度条：主路径固定 TSE（TCN-Skill-Extractor）
            "engine": "TSE",
            "llm_model_used": item.llm_model_used or "tse",
        })

        try:
            harness = get_chat_harness()
            from .tse import extract_skills as tse_extract_skills

            meta = dict(item.source_meta or {})
            meta.setdefault("topic", item.source_title)
            tse_result = await tse_extract_skills(
                item.source_text,
                source_title=item.source_title,
                source_meta=meta,
                harness=harness,
            )

            # Telemetry for skill-extract UI / debugging
            item.source_meta = {
                **meta,
                "tse": {
                    "focus_indices": list(tse_result.focus_indices or []),
                    "category_hint": tse_result.category_hint,
                    "tools_hint": list(tse_result.tools_hint or []),
                    "latency_ms": round(float(tse_result.latency_ms or 0.0), 2),
                    "backend": tse_result.backend,
                    "stage_timings": dict(tse_result.stage_timings or {}),
                    "utterance_count": (
                        len(tse_result.transcript.messages)
                        if tse_result.transcript else 0
                    ),
                    "parse_error": tse_result.parse_error,
                },
            }

            response_text = tse_result.raw_response or ""
            item.llm_raw_response = response_text
            item.llm_model_used = tse_result.model or "tse"

            await self._broadcast(item.team_id, "tse_extract_done", {
                "item_id": item.item_id,
                "focus_indices": item.source_meta["tse"]["focus_indices"],
                "utterance_count": item.source_meta["tse"]["utterance_count"],
                "skill_count": len(tse_result.skills or []),
                "latency_ms": item.source_meta["tse"]["latency_ms"],
                "model": item.llm_model_used,
                "engine": "TSE",
                "backend": item.source_meta["tse"].get("backend"),
                "parse_error": item.source_meta["tse"].get("parse_error"),
            })

            if tse_result.skills:
                # Strip legacy prefix if any model ever emits it
                skills = []
                for s in list(tse_result.skills):
                    if isinstance(s, dict):
                        n = str(s.get("name") or "")
                        for p in ("【回退草稿】", "[回退草稿]"):
                            if n.startswith(p):
                                n = n[len(p):].strip()
                                s = dict(s)
                                s["name"] = n[:64]
                        skills.append(s)
                    else:
                        skills.append(s)
                await self._ingest_extracted_skills(
                    item,
                    skills,
                    response_text=response_text,
                )
            else:
                # Prefer TSE local again inside fallback; last resort = topic placeholder
                if self._is_unusable_llm_text(response_text):
                    reason = "provider_fallback"
                else:
                    pe = tse_result.parse_error or "tse_empty"
                    reason = pe if str(pe).startswith("tse:") else f"tse:{pe}"
                await self._create_fallback_candidates(
                    item, response_text, reason, tse_result=tse_result
                )

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
            "engine": "TSE",
            "llm_model_used": item.llm_model_used or "",
        })
        self._persist_queue(item.team_id)

    async def _ingest_extracted_skills(
        self,
        item: SkillReviewItem,
        all_skills: List[Dict[str, Any]],
        *,
        response_text: str,
    ) -> None:
        """Dedup + write primary/extra review items from extracted skill dicts."""
        known_slugs = self._collect_known_slugs(item.team_id)
        original_skills = list(all_skills)
        dedup_skills: List[Dict[str, Any]] = []
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
        all_skills = dedup_skills

        if not all_skills:
            item.status = SkillReviewStatus.REJECTED
            item.reviewer_notes = "所有萃取结果均为已有技能，自动跳过"
            item.draft_name = (original_skills[0].get("name", "")[:64] if original_skills else "")
            await self._broadcast(item.team_id, "dedup_all_skipped", {
                "item_id": item.item_id,
                "skipped_names": [s.get("name", s.get("slug", "")) for s in original_skills],
                "message": f"萃取的 {len(original_skills)} 个技能均已存在，已自动跳过",
            })
            self._persist_queue(item.team_id)
            return

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
        # Persist disposition so taxonomy tabs (特质/储备/公共) match approve choice
        st = (skill_type or "reserve").strip().lower()
        if st not in ("trait", "public", "reserve"):
            st = "reserve"
        item.skill_type = st
        item.target_agent_id = (target_agent_id or "").strip()
        # Align visibility hint with disposition (draft_scope is still LLM-era field)
        if st == "public":
            item.draft_scope = "public"
        elif st in ("trait", "reserve") and item.draft_scope == "public":
            # approving as non-public overrides a mistaken public draft hint
            item.draft_scope = "personal"

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
                    if st == "trait" and item.target_agent_id:
                        agent = team.agents.get(item.target_agent_id)
                        if agent and skill_id not in agent.skills:
                            agent.skills.append(skill_id)
                            logger.info(f"🎯 特质技能 {skill_id} 已赋予智能体 {item.target_agent_id}")
                    elif st == "public":
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
            "skill_type": st,
            "target_agent_id": item.target_agent_id,
            "skill": skill_def.to_dict(),
        })
        self._persist_queue(team_id)

        result = item.to_dict()
        result["skill_type"] = st
        result["target_agent_id"] = item.target_agent_id
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
        if self._is_skill_tombstoned(
            team_id,
            skill_id=getattr(skill_def, "skill_id", "") or "",
            slug=getattr(skill_def, "slug", "") or "",
            name=getattr(skill_def, "name", "") or "",
        ):
            logger.info(
                "Skip rehydrate tombstoned skill %s / %s",
                getattr(skill_def, "slug", ""),
                getattr(skill_def, "name", ""),
            )
            return
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
