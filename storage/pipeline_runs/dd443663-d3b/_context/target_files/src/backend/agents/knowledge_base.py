# -*- coding: utf-8 -*-
"""AgentsGroup2026 Agent Knowledge Base — Document store with RAG search.

Stores agent deliverables and workspace files persistently,
provides keyword + TF-IDF search for retrieval.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── Storage root ──
_KB_ROOT: Optional[Path] = None


def _get_kb_root() -> Path:
    global _KB_ROOT
    if _KB_ROOT is None:
        base = Path(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))))
        _KB_ROOT = base / "storage" / "knowledge_base"
        _KB_ROOT.mkdir(parents=True, exist_ok=True)
    return _KB_ROOT


# ── Data Models ──


@dataclass
class KBDocument:
    """A document in the knowledge base."""
    doc_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    content: str = ""
    source_agent: str = ""
    source_team: str = ""
    category: str = "deliverable"  # deliverable | workspace | knowledge | archived
    tags: List[str] = field(default_factory=list)
    path: str = ""  # virtual folder path, e.g. "workspace/archived/xxx.md"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "source_agent": self.source_agent,
            "source_team": self.source_team,
            "category": self.category,
            "tags": self.tags,
            "path": self.path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "size": len(self.content),
        }

    def to_summary(self) -> Dict[str, Any]:
        """Return summary without full content."""
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "source_agent": self.source_agent,
            "source_team": self.source_team,
            "category": self.category,
            "tags": self.tags,
            "path": self.path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "size": len(self.content),
            "preview": self.content[:200] + ("..." if len(self.content) > 200 else ""),
        }


# ── TF-IDF Tokenizer & Search ──

_STOPWORDS_ZH = set("的了是在我有和人这中大为上个国以说也时一二三")
_STOPWORDS_EN = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "to", "of", "in", "for", "on", "with", "at", "by", "from",
                 "it", "this", "that", "and", "or", "not", "no", "but"}


def _tokenize(text: str) -> List[str]:
    """Simple bilingual tokenizer — CJK chars + latin words."""
    tokens = []
    # Extract CJK characters individually and latin words
    for m in re.finditer(r'[\u4e00-\u9fff]|[a-zA-Z0-9_]+', text.lower()):
        tok = m.group()
        if tok in _STOPWORDS_EN or tok in _STOPWORDS_ZH:
            continue
        if len(tok) >= 1:
            tokens.append(tok)
    return tokens


def _compute_tf(tokens: List[str]) -> Dict[str, float]:
    counts = Counter(tokens)
    total = len(tokens) or 1
    return {t: c / total for t, c in counts.items()}


class KnowledgeBase:
    """In-memory knowledge base with file-system persistence and TF-IDF search."""

    def __init__(self):
        self._docs: Dict[str, KBDocument] = {}
        self._idf_cache: Dict[str, float] = {}
        self._idf_dirty = True
        self._load_from_disk()

    def _load_from_disk(self):
        """Load all docs from storage/knowledge_base/*.json."""
        root = _get_kb_root()
        for f in root.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                doc = KBDocument(**{k: v for k, v in data.items()
                                   if k in KBDocument.__dataclass_fields__})
                self._docs[doc.doc_id] = doc
            except Exception:
                pass
        self._idf_dirty = True

    def _save_doc(self, doc: KBDocument):
        """Persist a single document to disk."""
        root = _get_kb_root()
        path = root / f"{doc.doc_id}.json"
        path.write_text(json.dumps(doc.to_dict(), ensure_ascii=False, indent=2),
                        encoding="utf-8")

    def _delete_doc_file(self, doc_id: str):
        root = _get_kb_root()
        path = root / f"{doc_id}.json"
        if path.exists():
            path.unlink()

    def _rebuild_idf(self):
        if not self._idf_dirty:
            return
        n = len(self._docs) or 1
        df: Dict[str, int] = Counter()
        for doc in self._docs.values():
            tokens = set(_tokenize(doc.title + " " + doc.content + " " + " ".join(doc.tags)))
            for t in tokens:
                df[t] += 1
        self._idf_cache = {t: math.log(n / (c + 1)) + 1 for t, c in df.items()}
        self._idf_dirty = False

    # ── CRUD ──

    def add(self, doc: KBDocument) -> KBDocument:
        self._docs[doc.doc_id] = doc
        self._idf_dirty = True
        self._save_doc(doc)
        return doc

    def get(self, doc_id: str) -> Optional[KBDocument]:
        return self._docs.get(doc_id)

    def update(self, doc_id: str, **kwargs) -> Optional[KBDocument]:
        doc = self._docs.get(doc_id)
        if not doc:
            return None
        for k, v in kwargs.items():
            if hasattr(doc, k):
                setattr(doc, k, v)
        doc.updated_at = datetime.now(timezone.utc).isoformat()
        self._idf_dirty = True
        self._save_doc(doc)
        return doc

    def delete(self, doc_id: str) -> bool:
        if doc_id in self._docs:
            del self._docs[doc_id]
            self._idf_dirty = True
            self._delete_doc_file(doc_id)
            return True
        return False

    def list_all(self, category: str = "", agent_id: str = "",
                 team_id: str = "") -> List[KBDocument]:
        docs = list(self._docs.values())
        if category:
            docs = [d for d in docs if d.category == category]
        if agent_id:
            docs = [d for d in docs if d.source_agent == agent_id]
        if team_id:
            docs = [d for d in docs if d.source_team == team_id]
        docs.sort(key=lambda d: d.created_at, reverse=True)
        return docs

    def list_by_path(self, path_prefix: str) -> List[KBDocument]:
        return sorted(
            [d for d in self._docs.values() if d.path.startswith(path_prefix)],
            key=lambda d: d.path
        )

    def stats(self) -> Dict[str, Any]:
        cats = Counter(d.category for d in self._docs.values())
        agents = Counter(d.source_agent for d in self._docs.values() if d.source_agent)
        total_size = sum(len(d.content) for d in self._docs.values())
        return {
            "total_documents": len(self._docs),
            "total_size": total_size,
            "by_category": dict(cats),
            "by_agent": dict(agents),
        }

    # ── Search (TF-IDF) ──

    def search(self, query: str, max_results: int = 10,
               category: str = "", agent_id: str = "") -> List[Dict[str, Any]]:
        """TF-IDF keyword search across all documents."""
        self._rebuild_idf()
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        query_tf = _compute_tf(query_tokens)
        results: List[Tuple[float, KBDocument]] = []

        for doc in self._docs.values():
            if category and doc.category != category:
                continue
            if agent_id and doc.source_agent != agent_id:
                continue

            doc_tokens = _tokenize(doc.title + " " + doc.content + " " + " ".join(doc.tags))
            doc_tf = _compute_tf(doc_tokens)

            # Cosine-like TF-IDF score
            score = 0.0
            for token, q_tf in query_tf.items():
                if token in doc_tf:
                    idf = self._idf_cache.get(token, 1.0)
                    score += q_tf * idf * doc_tf[token] * idf

            # Title boost
            title_tokens = set(_tokenize(doc.title))
            title_hits = sum(1 for t in query_tokens if t in title_tokens)
            score += title_hits * 2.0

            # Tag boost
            tag_tokens = set()
            for tag in doc.tags:
                tag_tokens.update(_tokenize(tag))
            tag_hits = sum(1 for t in query_tokens if t in tag_tokens)
            score += tag_hits * 1.5

            if score > 0:
                results.append((score, doc))

        results.sort(key=lambda x: -x[0])
        return [
            {**doc.to_summary(), "score": round(score, 4)}
            for score, doc in results[:max_results]
        ]


# ── Singleton ──

_kb_instance: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
