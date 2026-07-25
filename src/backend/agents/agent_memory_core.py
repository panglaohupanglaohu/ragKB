# -*- coding: utf-8 -*-
"""Agent 拟生记忆核心 — 痕迹 / 电荷场 / 过程（兼容原四文件存储）.

绑定键: team_id + agent_id
存储: storage/agent_memory/<team_id>/<agent_id>/{log,perception,intentions,affect,semantic,legacy,meta}.json

拟生分区（层 / 场 / 过程）:
  · 层 layers:   sensory(perception) · episodic(log) · semantic(semantic.json)
  · 场 field:    affective(affect) — 调制巩固与检索，不存事实
  · 过程 process: prospective(intentions) — 前瞻意图，**不是记忆层**
                  working — 轻量工作台（meta.working）

动态过程: encode → consolidate → reconsolidate → retrieve → forget
感情 = 痕迹上的选择压（fitness / 成败 → 电荷 → 巩固概率）
"""

from __future__ import annotations

import json
import math
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MEMORY_SCHEMA = "ag.memory/v1"
LEGACY_SCHEMA = "ag.legacy/v1"
PERCEPTION_CAPACITY = 500
RECENCY_DECAY_PER_HOUR = 0.995
AFFECT_ETA_MS = 72 * 3_600_000  # 72h
AFFECT_FLOOR = 0.01
SEMANTIC_MAX = 200
EPISODIC_SOFT_CAP = 400  # forget_tick 压力线
WORKING_SLOTS_DEFAULT = 5

# 拟生系统 taxonomy（API systems 视图）
SYSTEM_KIND = {
    "sensory": "layer",
    "episodic": "layer",
    "semantic": "layer",
    "working": "layer",
    "affective": "field",
    "prospective": "process",
}
# 旧文件/API 名 → 拟生名
LEGACY_TO_SYSTEM = {
    "log": "episodic",
    "perception": "sensory",
    "intentions": "prospective",
    "affect": "affective",
    "semantic": "semantic",
}
SYSTEM_TO_LEGACY = {v: k for k, v in LEGACY_TO_SYSTEM.items()}
SYSTEM_LABELS = {
    "sensory": "感觉痕迹",
    "episodic": "情节痕迹",
    "semantic": "自传语义",
    "working": "工作台",
    "affective": "情绪选择场",
    "prospective": "前瞻意图",
}
HUMAN_MEMORY_MAP = {
    "sensory": {"human_analogy": "sensory memory", "role": "极短暂输入痕迹，等待注意选择"},
    "working": {"human_analogy": "working memory", "role": "当前任务的容量受限工作空间"},
    "episodic": {"human_analogy": "episodic/autobiographical memory", "role": "带时间、地点和自我来源的经历"},
    "semantic": {"human_analogy": "semantic memory", "role": "从经历巩固出的概念、规律与自我叙事"},
    "prospective": {"human_analogy": "prospective memory", "role": "未来触发时要完成的行动；是过程，不是存储层"},
    "affective": {"human_analogy": "emotion-memory modulation", "role": "用价值、唤醒和身体式信号调制注意、巩固、检索与遗忘"},
    "procedural": {"human_analogy": "procedural memory", "role": "由技能库、熟练度和执行轨迹承载，不复制为文本层"},
}
MEMORY_STYLE_SCHEMA = "ag.memory.style/v1"
# 兼容旧 LAYERS 四元组（share ACL 等）
LEGACY_LAYERS = ("log", "perception", "intentions", "affect")


def systems_catalog() -> Dict[str, Any]:
    """Public catalog: which names are layers vs field vs process."""
    return {
        "schema": "ag.memory.systems/v1",
        "kinds": dict(SYSTEM_KIND),
        "labels": dict(SYSTEM_LABELS),
        "legacy_map": dict(LEGACY_TO_SYSTEM),
        "human_memory_map": dict(HUMAN_MEMORY_MAP),
        "note": "三类保存痕迹：sensory / episodic / semantic；working 与 prospective 是过程，affective 是选择场，procedural 由技能系统承载。",
    }


def map_layer_name(name: str) -> str:
    """legacy or system name → system name."""
    n = (name or "").strip()
    if n in SYSTEM_KIND:
        return n
    return LEGACY_TO_SYSTEM.get(n, n)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ROOT = _REPO_ROOT / "storage" / "agent_memory"

TIMEOUT_POLICIES = ("drop", "escalate", "keep")
CONFIDENCE_LEVELS = ("normal", "unclear")
INTENTION_STATUS = ("pending", "confirmed", "dropped")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _uid(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000):x}_{uuid.uuid4().hex[:6]}"


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _safe_team_agent(team_id: str, agent_id: str) -> Tuple[str, str]:
    def clean(s: str) -> str:
        s = re.sub(r"[^\w\-.@]+", "_", str(s or "").strip())
        return s[:120] or "unknown"

    return clean(team_id), clean(agent_id)


class AgentMemoryStore:
    """JSON file store under storage/agent_memory."""

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else _DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def agent_dir(self, team_id: str, agent_id: str) -> Path:
        t, a = _safe_team_agent(team_id, agent_id)
        d = self.root / t / a
        d.mkdir(parents=True, exist_ok=True)
        return d

    def path(self, team_id: str, agent_id: str, name: str) -> Path:
        return self.agent_dir(team_id, agent_id) / f"{name}.json"

    def load(self, team_id: str, agent_id: str, name: str, default: Any) -> Any:
        p = self.path(team_id, agent_id, name)
        if not p.is_file():
            return default
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return default

    def save(self, team_id: str, agent_id: str, name: str, data: Any) -> None:
        p = self.path(team_id, agent_id, name)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)

    def exists_layer(self, team_id: str, agent_id: str, name: str) -> bool:
        return self.path(team_id, agent_id, name).is_file()


_store: Optional[AgentMemoryStore] = None


def get_memory_store() -> AgentMemoryStore:
    global _store
    if _store is None:
        _store = AgentMemoryStore()
    return _store


# ── Layers ──────────────────────────────────────────────────────


def _bigrams(s: str) -> set:
    return {s[i : i + 2] for i in range(max(0, len(s) - 1))}


def _relevance(query: str, e: Dict[str, Any]) -> float:
    q = (query or "").strip().lower()
    if not q:
        return 0.0
    text = " ".join(
        str(x)
        for x in [
            e.get("subject"),
            e.get("action"),
            e.get("detail"),
            e.get("place"),
            " ".join(e.get("tags") or []),
        ]
        if x
    ).lower()
    score = 0.0
    if q in text:
        score += 1.0
    if len(q) >= 2:
        qb, tb = _bigrams(q), _bigrams(text)
        score += (sum(1 for b in qb if b in tb) / len(qb)) if qb else 0.0
    elif q in text:
        score += 0.5
    if any(str(tag).lower() == q for tag in (e.get("tags") or [])):
        score += 0.5
    # 可选「向量-lite」：字符哈希袋余弦（无外部依赖；AG_MEMORY_VECTOR_LITE=1 或默认开）
    if _vector_lite_enabled():
        score += 0.65 * _hash_cosine(q, text)
    return score


def _vector_lite_enabled() -> bool:
    import os

    v = (os.environ.get("AG_MEMORY_VECTOR_LITE") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _hash_bag(text: str, dim: int = 64) -> List[float]:
    """Deterministic character n-gram hashing trick → dense bag (stable across runs)."""
    import hashlib

    vec = [0.0] * dim
    t = (text or "").lower()
    if not t:
        return vec
    grams = [t[i : i + 2] for i in range(max(0, len(t) - 1))] or list(t)
    for g in grams:
        h = int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16) % dim
        vec[h] += 1.0
    # L2 norm
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / n for x in vec]


def _hash_cosine(a: str, b: str) -> float:
    va, vb = _hash_bag(a), _hash_bag(b)
    return sum(x * y for x, y in zip(va, vb))


class EpisodicLog:
    def __init__(self, store: AgentMemoryStore, team_id: str, agent_id: str):
        self.store, self.team_id, self.agent_id = store, team_id, agent_id
        data = store.load(team_id, agent_id, "log", [])
        self.events: List[Dict[str, Any]] = data if isinstance(data, list) else []

    def _save(self) -> None:
        self.store.save(self.team_id, self.agent_id, "log", self.events)

    def append(self, event: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        event = event or {}
        e = {
            "id": event.get("id") or _uid("ev"),
            "t": int(event["t"]) if event.get("t") is not None else _now_ms(),
            "subject": event.get("subject") or self.agent_id,
            "action": event.get("action") or "",
            "detail": event.get("detail") or "",
            "place": event.get("place") or "",
            "importance": max(1, min(10, int(round(float(event.get("importance") or 5))))),
            "tags": [str(t) for t in (event.get("tags") or [])],
            "lastAccessAt": event.get("lastAccessAt"),
        }
        self.events.append(e)
        self._save()
        return e

    def replay(self, t_start: float = float("-inf"), t_end: float = float("inf")) -> List[Dict]:
        return sorted(
            [e for e in self.events if t_start <= e.get("t", 0) <= t_end],
            key=lambda e: e.get("t", 0),
        )

    def recall(self, query: str = "", k: int = 5, now: Optional[int] = None) -> List[Dict]:
        now = now if now is not None else _now_ms()
        scored = []
        for e in self.events:
            if e.get("forgotten_at"):
                continue  # 已遗忘的情节不参与检索（语义核另取）
            anchor = e.get("lastAccessAt") or e.get("t") or now
            hours = max(0.0, (now - float(anchor)) / 3_600_000)
            recency = RECENCY_DECAY_PER_HOUR ** hours
            importance = (e.get("importance") or 5) / 10.0
            relevance = _relevance(query, e)
            scored.append(
                {
                    "event": e,
                    "score": recency + importance + relevance,
                    "parts": {
                        "recency": round(recency, 4),
                        "importance": round(importance, 4),
                        "relevance": round(relevance, 4),
                    },
                }
            )
        if query and str(query).strip():
            scored = [s for s in scored if s["parts"]["relevance"] > 0]
        scored.sort(key=lambda s: s["score"], reverse=True)
        hits = scored[: max(1, int(k))]
        if hits:
            for h in hits:
                h["event"]["lastAccessAt"] = now
            self._save()
        return hits

    def at(self, t: int, window_ms: int = 60_000) -> List[Dict]:
        return sorted(
            [e for e in self.events if abs(e.get("t", 0) - t) <= window_ms],
            key=lambda e: e.get("t", 0),
        )

    def to_json(self) -> List[Dict]:
        return list(self.events)

    def replace(self, events: Any) -> None:
        self.events = list(events) if isinstance(events, list) else []
        self._save()


class PerceptionStream:
    def __init__(self, store: AgentMemoryStore, team_id: str, agent_id: str):
        self.store, self.team_id, self.agent_id = store, team_id, agent_id
        data = store.load(team_id, agent_id, "perception", [])
        self.buffer: List[Dict[str, Any]] = data if isinstance(data, list) else []

    def _save(self) -> None:
        self.store.save(self.team_id, self.agent_id, "perception", self.buffer)

    def perceive(self, entry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = entry or {}
        item = {
            "t": int(entry["t"]) if entry.get("t") is not None else _now_ms(),
            "modality": entry.get("modality") or "vision",
            "payload": entry.get("payload"),
        }
        self.buffer.append(item)
        if len(self.buffer) > PERCEPTION_CAPACITY:
            self.buffer = self.buffer[-PERCEPTION_CAPACITY:]
        self._save()
        return item

    def perceive_at(self, t: int, window_ms: int = 60_000) -> List[Dict]:
        return sorted(
            [i for i in self.buffer if abs(i.get("t", 0) - t) <= window_ms],
            key=lambda i: i.get("t", 0),
        )

    def summarize(self) -> Dict[str, Any]:
        by_mod: Dict[str, int] = {}
        fear_sum = fear_n = 0
        t_start = t_end = None
        for i in self.buffer:
            m = i.get("modality") or "unknown"
            by_mod[m] = by_mod.get(m, 0) + 1
            payload = i.get("payload")
            fear = payload.get("fear") if isinstance(payload, dict) else None
            if fear is not None:
                try:
                    fear_sum += float(fear)
                    fear_n += 1
                except (TypeError, ValueError):
                    pass
            tt = i.get("t")
            if tt is not None:
                t_start = tt if t_start is None else min(t_start, tt)
                t_end = tt if t_end is None else max(t_end, tt)
        return {
            "count": len(self.buffer),
            "tStart": t_start,
            "tEnd": t_end,
            "byModality": by_mod,
            "fearMean": round(fear_sum / fear_n, 3) if fear_n else None,
        }

    def compress(self, log: Optional[EpisodicLog] = None) -> Optional[Dict[str, Any]]:
        if not self.buffer:
            return None
        summary = self.summarize()
        modality_text = "、".join(f"{m} {n} 次" for m, n in summary["byModality"].items())
        fear_text = "" if summary["fearMean"] is None else f"；fear 均值 {summary['fearMean']}"
        detail = f"这段时间感知到 {summary['count']} 次刺激：{modality_text}{fear_text}"
        event = None
        if log is not None:
            event = log.append(
                {
                    "t": summary["tEnd"] or _now_ms(),
                    "subject": self.agent_id,
                    "action": "感知压缩",
                    "detail": detail,
                    "importance": 5,
                    "tags": ["感知", "压缩", *list(summary["byModality"].keys())],
                }
            )
        self.buffer = []
        self._save()
        return {"summary": summary, "event": event, "detail": detail}

    def to_json(self) -> List[Dict]:
        return list(self.buffer)

    def replace(self, buffer: Any) -> None:
        self.buffer = list(buffer)[-PERCEPTION_CAPACITY:] if isinstance(buffer, list) else []
        self._save()


class IntentionQueue:
    """前瞻缓冲 (prospective process) — 不是记忆层；记的是「以后要做」."""

    kind = "process"
    system_name = "prospective"

    def __init__(self, store: AgentMemoryStore, team_id: str, agent_id: str):
        self.store, self.team_id, self.agent_id = store, team_id, agent_id
        data = store.load(team_id, agent_id, "intentions", [])
        self.items: List[Dict[str, Any]] = data if isinstance(data, list) else []

    def _save(self) -> None:
        self.store.save(self.team_id, self.agent_id, "intentions", self.items)

    def add(self, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        input_data = input_data or {}
        now = _now_ms()
        prov = input_data.get("provenance") or {}
        conf = prov.get("confidence") if isinstance(prov, dict) else "normal"
        if conf not in CONFIDENCE_LEVELS:
            conf = "normal"
        tp = input_data.get("timeoutPolicy") or "drop"
        if tp not in TIMEOUT_POLICIES:
            tp = "drop"
        due = input_data.get("dueAt")
        it = {
            "id": input_data.get("id") or _uid("in"),
            "tCreated": int(input_data.get("tCreated") or now),
            "creator": input_data.get("creator") or "",
            "instruction": input_data.get("instruction") or "",
            "trigger": input_data.get("trigger") or "",
            "dueAt": int(due) if due not in (None, "",) else None,
            "countdown": (
                float(input_data["countdown"])
                if input_data.get("countdown") not in (None, "")
                else None
            ),
            "status": "pending",
            "timeoutPolicy": tp,
            "provenance": {
                "saidAt": int(prov.get("saidAt") or now) if isinstance(prov, dict) else now,
                "context": (prov.get("context") if isinstance(prov, dict) else "") or "",
                "confidence": conf,
            },
            "handover": input_data.get("handover"),
        }
        self.items.append(it)
        self._save()
        return it

    def pending(self, now: Optional[int] = None) -> List[Dict]:
        now = now if now is not None else _now_ms()
        day_ms = 86_400_000
        rows = [i for i in self.items if i.get("status") == "pending"]

        def sort_key(i):
            d = i.get("dueAt")
            return (1 if d is None else 0, d if d is not None else i.get("tCreated", 0))

        out = []
        for i in sorted(rows, key=sort_key):
            due = i.get("dueAt")
            days_left = None if due is None else math.ceil((due - now) / day_ms)
            if days_left is None:
                due_label = "无期限"
            elif days_left >= 0:
                due_label = f"还有 {days_left} 天"
            else:
                due_label = f"已逾期 {-days_left} 天"
            out.append({**i, "daysLeft": days_left, "dueLabel": due_label})
        return out

    def all(self) -> List[Dict]:
        return sorted(self.items, key=lambda i: i.get("tCreated", 0))

    def confirm(self, intention_id: str, now: Optional[int] = None) -> Optional[Dict]:
        now = now if now is not None else _now_ms()
        for it in self.items:
            if it.get("id") == intention_id and it.get("status") == "pending":
                it["status"] = "confirmed"
                it["confirmedAt"] = now
                self._save()
                return it
        return None

    def drop(self, intention_id: str, now: Optional[int] = None) -> Optional[Dict]:
        now = now if now is not None else _now_ms()
        for it in self.items:
            if it.get("id") == intention_id and it.get("status") == "pending":
                it["status"] = "dropped"
                it["droppedAt"] = now
                self._save()
                return it
        return None

    def at(self, t: int) -> List[Dict]:
        return [i for i in self.items if i.get("tCreated", 0) <= t and i.get("status") == "pending"]

    def to_json(self) -> List[Dict]:
        return list(self.items)

    def replace(self, items: Any) -> None:
        self.items = list(items) if isinstance(items, list) else []
        self._save()


class SemanticCore:
    """语义核：由情节巩固而来的可泛化 claim；细节可忘、主张可留."""

    def __init__(self, store: AgentMemoryStore, team_id: str, agent_id: str):
        self.store, self.team_id, self.agent_id = store, team_id, agent_id
        data = store.load(team_id, agent_id, "semantic", [])
        self.claims: List[Dict[str, Any]] = data if isinstance(data, list) else []

    def _save(self) -> None:
        self.store.save(self.team_id, self.agent_id, "semantic", self.claims)

    def add(
        self,
        claim: str,
        *,
        source_event_ids: Optional[List[str]] = None,
        strength: float = 0.5,
        tags: Optional[List[str]] = None,
        t: Optional[int] = None,
    ) -> Dict[str, Any]:
        claim = (claim or "").strip()
        if not claim:
            raise ValueError("empty claim")
        # 去重：相同 claim 文本则加强
        for c in self.claims:
            if (c.get("claim") or "").strip() == claim:
                c["strength"] = min(1.0, float(c.get("strength") or 0.5) + 0.15)
                c["lastAccessAt"] = _now_ms()
                src = list(c.get("source_event_ids") or [])
                for sid in source_event_ids or []:
                    if sid and sid not in src:
                        src.append(sid)
                c["source_event_ids"] = src[-20:]
                self._save()
                return c
        row = {
            "id": _uid("sem"),
            "t": int(t) if t is not None else _now_ms(),
            "claim": claim[:500],
            "source_event_ids": list(source_event_ids or [])[:20],
            "strength": _clamp(float(strength), 0.05, 1.0),
            "tags": [str(x) for x in (tags or [])][:12],
            "lastAccessAt": None,
        }
        self.claims.append(row)
        if len(self.claims) > SEMANTIC_MAX:
            # 丢最弱最旧
            self.claims.sort(
                key=lambda c: (float(c.get("strength") or 0), c.get("lastAccessAt") or c.get("t") or 0)
            )
            self.claims = self.claims[-(SEMANTIC_MAX):]
        self._save()
        return row

    def recall(self, query: str = "", k: int = 5, now: Optional[int] = None) -> List[Dict]:
        now = now if now is not None else _now_ms()
        q = (query or "").strip().lower()
        scored = []
        for c in self.claims:
            if c.get("forgotten_at"):
                continue
            text = f"{c.get('claim') or ''} {' '.join(c.get('tags') or [])}".lower()
            rel = 0.0
            if not q:
                rel = 0.3
            elif q in text:
                rel = 1.0
            elif len(q) >= 2:
                qb, tb = _bigrams(q), _bigrams(text)
                rel = (sum(1 for b in qb if b in tb) / len(qb)) if qb else 0.0
            if _vector_lite_enabled() and q:
                rel = max(rel, 0.65 * _hash_cosine(q, text))
            if q and rel <= 0:
                continue
            anchor = c.get("lastAccessAt") or c.get("t") or now
            hours = max(0.0, (now - float(anchor)) / 3_600_000)
            recency = RECENCY_DECAY_PER_HOUR ** hours
            strength = float(c.get("strength") or 0.5)
            score = recency + strength + rel
            scored.append({"claim": c, "score": score})
        scored.sort(key=lambda s: s["score"], reverse=True)
        hits = scored[: max(1, int(k))]
        for h in hits:
            h["claim"]["lastAccessAt"] = now
        if hits:
            self._save()
        return hits

    def active(self) -> List[Dict]:
        return [c for c in self.claims if not c.get("forgotten_at")]

    def to_json(self) -> List[Dict]:
        return list(self.claims)

    def replace(self, claims: Any) -> None:
        self.claims = list(claims) if isinstance(claims, list) else []
        self._save()


class AffectResidue:
    """情绪电荷场：调制巩固与检索；不是事实内容层."""

    def __init__(self, store: AgentMemoryStore, team_id: str, agent_id: str):
        self.store, self.team_id, self.agent_id = store, team_id, agent_id
        data = store.load(team_id, agent_id, "affect", None)
        self.state = self._empty()
        if isinstance(data, dict):
            self.state.update(data)
            if not isinstance(self.state.get("labels"), dict):
                self.state["labels"] = {}

    @staticmethod
    def _empty() -> Dict[str, Any]:
        return {"valence": 0.0, "arousal": 0.0, "labels": {}, "updatedAt": _now_ms()}

    def _save(self) -> None:
        self.store.save(self.team_id, self.agent_id, "affect", self.state)

    def _decay_to(self, now: int) -> None:
        s = self.state
        dt = now - int(s.get("updatedAt") or now)
        if dt <= 0:
            return
        f = math.exp(-dt / AFFECT_ETA_MS)
        s["valence"] = float(s.get("valence") or 0) * f
        s["arousal"] = float(s.get("arousal") or 0) * f
        labels = dict(s.get("labels") or {})
        for lab, intensity in list(labels.items()):
            v = float(intensity) * f
            if v < AFFECT_FLOOR:
                del labels[lab]
            else:
                labels[lab] = v
        s["labels"] = labels
        s["updatedAt"] = now

    def feel(
        self,
        label: str,
        intensity: float = 0.5,
        valence: float = 0.0,
        arousal: float = 0.5,
        now: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not label:
            return self.residue(now)
        now = now if now is not None else _now_ms()
        self._decay_to(now)
        s = self.state
        key = str(label)
        cur = s["labels"].get(key)
        inten = _clamp(float(intensity), 0, 1)
        if cur is None:
            s["labels"][key] = inten
        else:
            s["labels"][key] = min(1.0, max(float(cur) * 1.2, inten))
        s["valence"] = _clamp(float(s.get("valence") or 0) * 0.5 + _clamp(float(valence), -1, 1) * 0.5, -1, 1)
        s["arousal"] = _clamp(float(s.get("arousal") or 0) * 0.5 + _clamp(float(arousal), 0, 1) * 0.5, 0, 1)
        s["updatedAt"] = now
        self._save()
        return self.residue(now)

    def residue(self, now: Optional[int] = None) -> Dict[str, Any]:
        now = now if now is not None else _now_ms()
        self._decay_to(now)
        self._save()
        return {
            "valence": round(float(self.state.get("valence") or 0), 4),
            "arousal": round(float(self.state.get("arousal") or 0), 4),
            "labels": {
                k: round(float(v), 4) for k, v in (self.state.get("labels") or {}).items()
            },
            "updatedAt": self.state.get("updatedAt"),
        }

    def tone_hint(self, now: Optional[int] = None) -> str:
        r = self.residue(now)
        entries = sorted(r["labels"].items(), key=lambda x: x[1], reverse=True)
        if not entries:
            return "语气平静，没有明显的情绪残留。"
        label, intensity = entries[0]
        degree = "浓浓的" if intensity >= 0.6 else ("一丝" if intensity >= 0.3 else "一点未散的")
        hint = f"语气里带着{degree}{label}"
        if r["arousal"] >= 0.7:
            hint += "，语速不自觉地快了些"
        elif r["arousal"] <= 0.2 and intensity >= 0.3:
            hint += "，说得又轻又慢"
        if r["valence"] <= -0.4:
            hint += "，尾音微微发沉"
        elif r["valence"] >= 0.4:
            hint += "，尾音里透出暖意"
        return hint + "。"

    def at(self, t: int) -> Dict[str, Any]:
        s = self.state
        dt = t - int(s.get("updatedAt") or t)
        f = math.exp(-dt / AFFECT_ETA_MS) if dt > 0 else 1.0
        labels = {}
        for k, v in (s.get("labels") or {}).items():
            decayed = float(v) * f
            if decayed >= AFFECT_FLOOR:
                labels[k] = round(decayed, 4)
        return {
            "valence": round(float(s.get("valence") or 0) * f, 4),
            "arousal": round(float(s.get("arousal") or 0) * f, 4),
            "labels": labels,
        }

    def to_json(self) -> Dict[str, Any]:
        return dict(self.state)

    def replace(self, state: Any) -> None:
        self.state = self._empty()
        if isinstance(state, dict):
            self.state.update(state)
            if not isinstance(self.state.get("labels"), dict):
                self.state["labels"] = {}
        self._save()


class AgentMemoryCore:
    """一只智能体的记忆有机体：层(感觉/情节/语义) + 电荷场 + 前瞻过程 + 共享时间轴."""

    def __init__(self, team_id: str, agent_id: str, store: Optional[AgentMemoryStore] = None):
        if not team_id or not agent_id:
            raise ValueError("team_id and agent_id required")
        self.team_id = team_id
        self.agent_id = agent_id
        self.store = store or get_memory_store()
        self.log = EpisodicLog(self.store, team_id, agent_id)  # episodic
        self.perception = PerceptionStream(self.store, team_id, agent_id)  # sensory
        self.intentions = IntentionQueue(self.store, team_id, agent_id)  # prospective process
        self.affect = AffectResidue(self.store, team_id, agent_id)  # affective field
        self.semantic = SemanticCore(self.store, team_id, agent_id)  # semantic core

    # ── bind meta ──
    def meta(self) -> Dict[str, Any]:
        data = self.store.load(self.team_id, self.agent_id, "meta", {})
        if not isinstance(data, dict):
            data = {}
        # lifecycle 状态（若可用）
        state = data.get("state")
        persona = data.get("persona") or "hybrid"
        try:
            from .agent_memory_lifecycle import get_memory_lifecycle

            lc = get_memory_lifecycle()
            # 使用同一 store 根，避免测试隔离问题：仅读 tombstone/state
            if hasattr(lc, "store") and lc.store is not self.store:
                # 临时用本 store 解析
                from .agent_memory_lifecycle import AgentMemoryLifecycle

                lc = AgentMemoryLifecycle(store=self.store)
            st = lc.get_status(self.team_id, self.agent_id)
            state = st.get("state")
            persona = st.get("persona") or persona
        except Exception:
            if not state:
                if self.is_sealed() or data.get("sealed"):
                    state = "sealed"
                elif data.get("bound") is False:
                    state = "unbound"
                else:
                    state = "active"
        bound = state not in ("unbound", "destroyed")
        return {
            "team_id": self.team_id,
            "agent_id": self.agent_id,
            "bound": bound,
            "bound_at": data.get("bound_at"),
            "state": state or "active",
            "persona": persona,
            "autonomy": data.get("autonomy") or {},
            "sealed": state in ("sealed", "archived") or self.is_sealed(),
            "schema": MEMORY_SCHEMA,
            "counts": self.counts() if state != "destroyed" else {},
            "tone_hint": self.affect.tone_hint() if bound and state != "destroyed" else "",
        }

    def bind(self, enabled: bool = True) -> Dict[str, Any]:
        try:
            from .agent_memory_lifecycle import AgentMemoryLifecycle, get_memory_lifecycle

            lc = get_memory_lifecycle()
            if lc.store is not self.store:
                lc = AgentMemoryLifecycle(store=self.store)
            return lc.transition(
                self.team_id, self.agent_id, "bind" if enabled else "unbind"
            ).get("status") or self.meta()
        except Exception:
            data = self.store.load(self.team_id, self.agent_id, "meta", {})
            if not isinstance(data, dict):
                data = {}
            data["bound"] = bool(enabled)
            data["state"] = "active" if enabled else "unbound"
            if enabled and not data.get("bound_at"):
                data["bound_at"] = _now_ms()
            if not enabled:
                data["unbound_at"] = _now_ms()
            self.store.save(self.team_id, self.agent_id, "meta", data)
            return self.meta()

    def counts(self) -> Dict[str, int]:
        return {
            "log": len(self.log.events),
            "perception": len(self.perception.buffer),
            "intentions": len(self.intentions.items),
            "intentions_pending": len([i for i in self.intentions.items if i.get("status") == "pending"]),
            "affect_labels": len((self.affect.state.get("labels") or {})),
            "semantic": len(self.semantic.active()),
            "forgotten": len([e for e in self.log.events if e.get("forgotten_at")]),
        }

    def systems_view(self) -> Dict[str, Any]:
        """拟生 systems 视图（层/场/过程），供 UI 与 API."""
        c = self.counts()
        return {
            **systems_catalog(),
            "systems": {
                "sensory": {
                    "kind": "layer",
                    "label": SYSTEM_LABELS["sensory"],
                    "legacy": "perception",
                    "count": c["perception"],
                },
                "episodic": {
                    "kind": "layer",
                    "label": SYSTEM_LABELS["episodic"],
                    "legacy": "log",
                    "count": c["log"],
                    "forgotten": c["forgotten"],
                },
                "semantic": {
                    "kind": "layer",
                    "label": SYSTEM_LABELS["semantic"],
                    "legacy": "semantic",
                    "count": c["semantic"],
                },
                "working": {
                    "kind": "layer",
                    "label": SYSTEM_LABELS["working"],
                    "slots": self._working_slots(),
                },
                "affective": {
                    "kind": "field",
                    "label": SYSTEM_LABELS["affective"],
                    "legacy": "affect",
                    "count": c["affect_labels"],
                    "note": "电荷场：调制巩固/检索，不存事实",
                },
                "prospective": {
                    "kind": "process",
                    "label": SYSTEM_LABELS["prospective"],
                    "legacy": "intentions",
                    "count": c["intentions_pending"],
                    "note": "前瞻意图过程缓冲，不是记忆层",
                },
            },
            "topology": self.topology(),
            "memory_style": self.memory_style(),
            "dynamic_state": self.dynamic_state(),
        }

    def memory_style(self) -> Dict[str, Any]:
        """Agent 独有的记忆方式。旧 persona 只作为不可见的初始化原型。"""
        meta = self._load_meta()
        style = meta.get("memory_style")
        if not isinstance(style, dict):
            prototype = str(meta.get("persona") or "hybrid")
            topo = dict(meta.get("topology") or self._default_topology(prototype))
            style = {
                "schema": MEMORY_STYLE_SCHEMA,
                "name": f"{self.agent_id}的记忆方式",
                "prototype": prototype,
                "created_at": int(meta.get("bound_at") or _now_ms()),
                "updated_at": _now_ms(),
                "version": 1,
                "continuity": 0.65 if prototype == "xiaoman" else (0.35 if prototype == "shenmian" else 0.5),
                "restraint": 0.35 if prototype == "xiaoman" else (0.8 if prototype == "shenmian" else 0.55),
                "plasticity": 0.7 if prototype == "xiaoman" else (0.35 if prototype == "shenmian" else 0.55),
                "affective_permeability": 0.65 if prototype == "xiaoman" else (0.15 if prototype == "shenmian" else 0.4),
                "topology": topo,
                "history": [{"t": _now_ms(), "reason": "prototype_seed", "prototype": prototype}],
            }
            meta["memory_style"] = style
            self._save_meta(meta)
        return json.loads(json.dumps(style))

    def set_memory_style(self, patch: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        patch = patch or {}
        meta = self._load_meta()
        style = self.memory_style()
        for key in ("continuity", "restraint", "plasticity", "affective_permeability"):
            if key in patch:
                style[key] = round(_clamp(float(patch[key]), 0.0, 1.0), 3)
        if patch.get("name"):
            style["name"] = str(patch["name"]).strip()[:48]
        topo_patch = patch.get("topology")
        if isinstance(topo_patch, dict):
            topo = dict(style.get("topology") or self.topology())
            allowed = {
                "sensory_capacity", "episodic_soft_cap", "semantic_max", "working_slots",
                "consolidate_min_importance", "forget_aggressiveness", "charge_transfer",
            }
            for key, value in topo_patch.items():
                if key in allowed:
                    topo[key] = value
            style["topology"] = topo
            meta["topology"] = topo
        style["version"] = int(style.get("version") or 1) + 1
        style["updated_at"] = _now_ms()
        history = list(style.get("history") or [])
        history.append({"t": style["updated_at"], "reason": str(patch.get("reason") or "manual_tuning")[:80]})
        style["history"] = history[-50:]
        meta["memory_style"] = style
        self._save_meta(meta)
        return self.memory_style()

    def dynamic_state(self) -> Dict[str, Any]:
        """随时间变化的记忆有机体状态，不把原始计数误当作静态容量。"""
        now = _now_ms()
        style = self.memory_style()
        live_events = [e for e in self.log.events if not e.get("forgotten_at")]
        strengths = []
        for e in live_events:
            anchor = e.get("lastAccessAt") or e.get("t") or now
            hours = max(0.0, (now - float(anchor)) / 3_600_000)
            strengths.append((RECENCY_DECAY_PER_HOUR ** hours) * (float(e.get("importance") or 5) / 10.0))
        semantic_strength = sum(float(c.get("strength") or 0.5) for c in self.semantic.active())
        charge = self.affect.residue(now)
        charge_energy = min(1.0, sum(float(v) for v in (charge.get("labels") or {}).values()))
        continuity = float(style.get("continuity") or 0.5)
        active_mass = sum(strengths) + semantic_strength
        forgotten = len([e for e in self.log.events if e.get("forgotten_at")])
        continuity_index = _clamp(
            0.45 * continuity + 0.25 * min(1.0, semantic_strength / 10.0)
            + 0.2 * min(1.0, len(self._working_slots()) / max(1, int(self.topology().get("working_slots") or 5)))
            + 0.1 * (1.0 if self.is_sealed() else 0.5), 0.0, 1.0,
        )
        return {
            "t": now,
            "active_memory_mass": round(active_mass, 3),
            "charge_energy": round(charge_energy, 3),
            "continuity_index": round(continuity_index, 3),
            "forgetting_ratio": round(forgotten / max(1, len(self.log.events)), 3),
            "plasticity": style.get("plasticity"),
            "restraint": style.get("restraint"),
            "style_name": style.get("name"),
        }

    def topology(self) -> Dict[str, Any]:
        meta = self.store.load(self.team_id, self.agent_id, "meta", {})
        if not isinstance(meta, dict):
            meta = {}
        topo = meta.get("topology")
        style = meta.get("memory_style")
        if not isinstance(topo, dict) and isinstance(style, dict):
            topo = style.get("topology")
        if not isinstance(topo, dict):
            topo = self._default_topology(meta.get("persona") or "hybrid")
        return topo

    @staticmethod
    def _default_topology(persona: str) -> Dict[str, Any]:
        if persona == "xiaoman":
            return {
                "sensory_capacity": 500,
                "episodic_soft_cap": 500,
                "semantic_max": 200,
                "working_slots": 7,
                "consolidate_min_importance": 4,
                "forget_aggressiveness": 0.35,
                "charge_transfer": "soft",
            }
        if persona == "shenmian":
            return {
                "sensory_capacity": 200,
                "episodic_soft_cap": 250,
                "semantic_max": 120,
                "working_slots": 3,
                "consolidate_min_importance": 7,
                "forget_aggressiveness": 0.75,
                "charge_transfer": "never",
            }
        return {
            "sensory_capacity": 500,
            "episodic_soft_cap": EPISODIC_SOFT_CAP,
            "semantic_max": SEMANTIC_MAX,
            "working_slots": WORKING_SLOTS_DEFAULT,
            "consolidate_min_importance": 5,
            "forget_aggressiveness": 0.5,
            "charge_transfer": "ask",
        }

    def _working_slots(self) -> List[Dict[str, Any]]:
        meta = self.store.load(self.team_id, self.agent_id, "meta", {})
        if not isinstance(meta, dict):
            return []
        w = meta.get("working")
        return list(w) if isinstance(w, list) else []

    def _load_meta(self) -> Dict[str, Any]:
        meta = self.store.load(self.team_id, self.agent_id, "meta", {})
        return meta if isinstance(meta, dict) else {}

    def _save_meta(self, meta: Dict[str, Any]) -> None:
        self.store.save(self.team_id, self.agent_id, "meta", meta)

    def push_working(self, item: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """工作台：容量极小的当前关注槽位（跨轮次）。"""
        item = item or {}
        meta = self._load_meta()
        topo = self.topology()
        n = max(1, int(topo.get("working_slots") or WORKING_SLOTS_DEFAULT))
        slots: List[Dict[str, Any]] = list(meta.get("working") or [])
        row = {
            "id": item.get("id") or _uid("wk"),
            "t": int(item.get("t") or _now_ms()),
            "text": str(item.get("text") or item.get("content") or "")[:300],
            "source": item.get("source") or "manual",
            "ref": item.get("ref") or "",
        }
        if not row["text"]:
            return slots
        # 同 text 顶到前
        slots = [s for s in slots if s.get("text") != row["text"]]
        slots.insert(0, row)
        slots = slots[:n]
        meta["working"] = slots
        self._save_meta(meta)
        return slots

    def clear_working(self) -> None:
        meta = self._load_meta()
        meta["working"] = []
        self._save_meta(meta)

    def forgotten_audit(self, limit: int = 30) -> List[Dict[str, Any]]:
        rows = [e for e in self.log.events if e.get("forgotten_at")]
        rows.sort(key=lambda e: e.get("forgotten_at") or 0, reverse=True)
        return rows[: max(1, int(limit))]

    def drift_topology(
        self,
        *,
        fitness_delta: float = 0.0,
        survival_ticks: Optional[float] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """架构动态：容量/遗忘/巩固门槛随时间与适应度慢漂移（有 clamp）."""
        meta = self._load_meta()
        persona = meta.get("persona") or "hybrid"
        base = self._default_topology(persona)
        topo = dict(meta.get("topology") or base)
        now = _now_ms()
        last = int(topo.get("last_drift_at") or 0)
        # 默认至少间隔 1h 才漂移（测试可 force）
        if not force and last and (now - last) < 3_600_000:
            return topo

        age_h = 0.0
        if meta.get("bound_at"):
            try:
                age_h = max(0.0, (now - float(meta["bound_at"])) / 3_600_000)
            except (TypeError, ValueError):
                age_h = 0.0
        # 存活时长 → 略放宽情节 cap（经验丰富）
        surv = float(survival_ticks) if survival_ticks is not None else float(
            topo.get("last_survival_ticks") or 0
        )
        if survival_ticks is not None:
            topo["last_survival_ticks"] = surv

        fd = _clamp(float(fitness_delta), -1.0, 1.0)
        style = self.memory_style()
        plasticity = float(style.get("plasticity") or 0.5)
        restraint = float(style.get("restraint") or 0.5)
        continuity = float(style.get("continuity") or 0.5)
        # 失败多 → 遗忘更激进、巩固门槛升高；变化幅度由该 Agent 的可塑性控制
        # 成功多 → 容量略升、遗忘略缓（小满式连续）
        forget = float(topo.get("forget_aggressiveness") or base["forget_aggressiveness"])
        forget = _clamp(forget - fd * (0.02 + 0.06 * plasticity) + 0.025 * restraint + (0.01 if age_h > 168 else 0), 0.15, 0.95)
        min_imp = int(topo.get("consolidate_min_importance") or base["consolidate_min_importance"])
        min_imp = int(_clamp(min_imp - fd * plasticity + restraint * 0.7 + (0.2 if age_h > 336 else 0), 3, 9))
        soft_cap = int(topo.get("episodic_soft_cap") or base["episodic_soft_cap"])
        soft_cap = int(
            _clamp(
                soft_cap + fd * (6 + 16 * plasticity) + min(40, surv / 50.0) + 12 * continuity,
                80,
                800,
            )
        )
        sensory = int(topo.get("sensory_capacity") or base["sensory_capacity"])
        sensory = int(_clamp(sensory + fd * 5, 50, 800))
        slots = int(topo.get("working_slots") or base["working_slots"])
        slots = int(_clamp(slots + (1 if fd > 0.3 else 0) - (1 if fd < -0.3 else 0), 2, 9))

        topo.update(
            {
                "forget_aggressiveness": round(forget, 3),
                "consolidate_min_importance": min_imp,
                "episodic_soft_cap": soft_cap,
                "sensory_capacity": sensory,
                "working_slots": slots,
                "semantic_max": int(topo.get("semantic_max") or base["semantic_max"]),
                "charge_transfer": topo.get("charge_transfer") or base.get("charge_transfer"),
                "last_drift_at": now,
                "last_fitness_delta": fd,
                "age_hours_est": round(age_h, 2),
            }
        )
        meta["topology"] = topo
        style = self.memory_style()
        style["topology"] = dict(topo)
        style["updated_at"] = now
        history = list(style.get("history") or [])
        history.append({"t": now, "reason": "fitness_drift", "fitness_delta": fd})
        style["history"] = history[-50:]
        meta["memory_style"] = style
        self._save_meta(meta)
        # 感知容量即时生效
        if len(self.perception.buffer) > sensory:
            self.perception.buffer = self.perception.buffer[-sensory:]
            self.perception._save()
        return topo

    def transfer_narrative(
        self,
        *,
        persona: str = "hybrid",
        to_agent_id: str = "",
        copied: Optional[Dict[str, Any]] = None,
        keep_memorial: bool = True,
    ) -> Dict[str, str]:
        """小满连续叙事 / 沈弥安凭吊清单 — 传递可读摘要."""
        copied = copied or {}
        live = [e for e in self.log.events if not e.get("forgotten_at")]
        top = sorted(live, key=lambda e: int(e.get("importance") or 0), reverse=True)[:5]
        claims = self.semantic.active()[:5]
        tone = self.affect.tone_hint()
        p = (persona or "hybrid").lower()

        if p == "xiaoman":
            beats = []
            for e in top:
                beats.append(
                    f"还记得{e.get('action') or '那次'}——"
                    f"{(e.get('detail') or '')[:60]}"
                )
            for c in claims:
                beats.append(f"渐渐明白：{c.get('claim') or ''}"[:80])
            body = "；".join(beats) if beats else "记忆尚轻，但线索还在。"
            title = f"致 {to_agent_id or '后来者'} · 一段未断的连续"
            narrative = (
                f"{title}\n"
                f"我把还能连上的日子交给你。{body}\n"
                f"余温：{tone}\n"
                f"（情节{copied.get('log', 0)} · 语义{copied.get('semantic', 0)} · "
                f"感觉{copied.get('perception', 0)}）"
            )
            style = "continuous"
        elif p == "shenmian":
            lines = ["【凭吊清单 · 这是回放，不是本人】"]
            for e in top:
                lines.append(
                    f"· [{e.get('importance', 5)}] {e.get('action') or ''} — "
                    f"{(e.get('detail') or '')[:50]}"
                )
            if claims:
                lines.append("【骨架主张】")
                for c in claims:
                    lines.append(f"· {c.get('claim') or ''}"[:80])
            if keep_memorial:
                lines.append("原件已封存可凭吊；电荷不随行。")
            narrative = "\n".join(lines)
            title = f"交接予 {to_agent_id or '受益者'} · 克制清单"
            style = "memorial"
        else:
            narrative = (
                f"记忆传递 → {to_agent_id or '?'}\n"
                f"情节 {copied.get('log', 0)} · 语义 {copied.get('semantic', 0)} · "
                f"前瞻 {copied.get('intentions', 0)}\n"
                f"{tone}"
            )
            title = "混合交接摘要"
            style = "hybrid"
        return {"title": title, "narrative": narrative, "style": style}

    def at(self, t: int, window_ms: int = 60_000) -> Dict[str, Any]:
        return {
            "t": t,
            "log": self.log.at(t, window_ms),
            "perception": self.perception.perceive_at(t, window_ms),
            "intentions": self.intentions.at(t),
            "affect": self.affect.at(t),
            "semantic": [
                c for c in self.semantic.active()
                if abs((c.get("t") or 0) - t) <= window_ms
            ],
            # 拟生别名
            "episodic": self.log.at(t, window_ms),
            "sensory": self.perception.perceive_at(t, window_ms),
            "prospective": self.intentions.at(t),
            "affective": self.affect.at(t),
        }

    def export_all(self) -> Dict[str, Any]:
        return {
            "schema": MEMORY_SCHEMA,
            "team_id": self.team_id,
            "agent_id": self.agent_id,
            "exportedAt": _now_ms(),
            "layers": {
                "log": self.log.to_json(),
                "perception": self.perception.to_json(),
                "intentions": self.intentions.to_json(),
                "affect": self.affect.to_json(),
                "semantic": self.semantic.to_json(),
            },
            "systems": self.systems_view().get("systems"),
            "meta": self.store.load(self.team_id, self.agent_id, "meta", {}),
        }

    def import_all(self, data: Any) -> bool:
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return False
        if not isinstance(data, dict) or data.get("schema") != MEMORY_SCHEMA:
            return False
        layers = data.get("layers") or {}
        if not isinstance(layers, dict):
            return False
        self.log.replace(layers.get("log"))
        self.perception.replace(layers.get("perception"))
        self.intentions.replace(layers.get("intentions"))
        self.affect.replace(layers.get("affect"))
        if "semantic" in layers:
            self.semantic.replace(layers.get("semantic"))
        if isinstance(data.get("meta"), dict):
            meta = self.store.load(self.team_id, self.agent_id, "meta", {})
            if not isinstance(meta, dict):
                meta = {}
            meta.update(data["meta"])
            meta["bound"] = True
            meta["imported_at"] = _now_ms()
            self.store.save(self.team_id, self.agent_id, "meta", meta)
        return True

    def consolidate_tick(self, *, max_new: int = 5) -> Dict[str, Any]:
        """情节 → 语义核巩固（确定性规则，不依赖 LLM）."""
        topo = self.topology()
        min_imp = int(topo.get("consolidate_min_importance") or 5)
        created = []
        candidates = [
            e
            for e in self.log.events
            if not e.get("forgotten_at")
            and not e.get("consolidated_at")
            and int(e.get("importance") or 0) >= min_imp
        ]
        # 优先重要且较新
        candidates.sort(key=lambda e: (int(e.get("importance") or 0), e.get("t") or 0), reverse=True)
        for e in candidates[: max(1, int(max_new))]:
            action = (e.get("action") or "").strip()
            detail = (e.get("detail") or "").strip()
            if not action and not detail:
                continue
            claim = f"{action}：{detail}" if action and detail else (action or detail)
            claim = claim[:240]
            row = self.semantic.add(
                claim,
                source_event_ids=[e.get("id")] if e.get("id") else [],
                strength=min(1.0, (int(e.get("importance") or 5)) / 10.0),
                tags=list(e.get("tags") or [])[:8],
                t=e.get("t"),
            )
            e["consolidated_at"] = _now_ms()
            created.append(row.get("id"))
        if created:
            self.log._save()
        return {"ok": True, "consolidated": len(created), "claim_ids": created}

    def forget_tick(self, *, hard_cap: Optional[int] = None) -> Dict[str, Any]:
        """可遗忘：低分情节 soft-forget（标记 forgotten_at，不物理抹除以便审计）."""
        topo = self.topology()
        cap = int(hard_cap or topo.get("episodic_soft_cap") or EPISODIC_SOFT_CAP)
        agg = float(topo.get("forget_aggressiveness") or 0.5)
        now = _now_ms()
        live = [e for e in self.log.events if not e.get("forgotten_at")]
        if len(live) <= cap and agg < 0.9:
            # 仍可按极弱分数偶尔遗忘
            pass
        # 电荷总强度作保护
        charge = 0.0
        try:
            r = self.affect.residue(now)
            charge = sum(float(v) for v in (r.get("labels") or {}).values())
        except Exception:
            charge = 0.0
        charge_boost = min(1.0, charge)

        def score(e: Dict[str, Any]) -> float:
            anchor = e.get("lastAccessAt") or e.get("t") or now
            hours = max(0.0, (now - float(anchor)) / 3_600_000)
            recency = RECENCY_DECAY_PER_HOUR ** hours
            imp = (int(e.get("importance") or 5)) / 10.0
            # 已巩固的细节更容易忘（语义核已留）
            consol = 0.85 if e.get("consolidated_at") else 1.0
            return (recency + imp + 0.2 * charge_boost) * consol

        scored = sorted(live, key=score)
        forgotten_ids = []
        # 超出 cap 的部分必须忘；再按 aggressiveness 多忘一点弱痕迹
        overflow = max(0, len(live) - cap)
        extra = int(len(live) * 0.05 * agg) if len(live) > 20 else 0
        n_forget = overflow + extra
        for e in scored[:n_forget]:
            if int(e.get("importance") or 0) >= 9 and not e.get("consolidated_at"):
                continue  # 极重要且未巩固：暂留
            e["forgotten_at"] = now
            forgotten_ids.append(e.get("id"))
        if forgotten_ids:
            self.log._save()
        return {
            "ok": True,
            "forgotten": len(forgotten_ids),
            "ids": forgotten_ids[:50],
            "live_remaining": len([e for e in self.log.events if not e.get("forgotten_at")]),
        }

    def apply_fitness(
        self,
        *,
        success: bool,
        magnitude: float = 0.4,
        label_success: str = "稳妥",
        label_fail: str = "警惕",
        survival_ticks: Optional[float] = None,
        drift: bool = True,
    ) -> Dict[str, Any]:
        """物竞/任务适应度 → 电荷选择压 + 可选拓扑漂移（感情闭环入口）."""
        mag = _clamp(float(magnitude), 0.05, 1.0)
        if success:
            felt = self.affect.feel(label_success, mag * 0.6, valence=0.2 + mag * 0.3, arousal=0.25 + mag * 0.2)
            fd = mag
        else:
            felt = self.affect.feel(label_fail, mag * 0.8, valence=-0.2 - mag * 0.4, arousal=0.4 + mag * 0.3)
            fd = -mag
        topo = None
        if drift:
            try:
                topo = self.drift_topology(fitness_delta=fd, survival_ticks=survival_ticks)
            except Exception:
                topo = None
        return {"ok": True, "affect": felt, "fitness_delta": fd, "topology": topo}

    def is_sealed(self) -> bool:
        return self.store.exists_layer(self.team_id, self.agent_id, "legacy")

    def seal(self, now: Optional[int] = None) -> Dict[str, Any]:
        existing = self.store.load(self.team_id, self.agent_id, "legacy", None)
        if isinstance(existing, dict) and existing.get("schema") == LEGACY_SCHEMA:
            return existing
        now = now if now is not None else _now_ms()
        snapshot = {
            "schema": LEGACY_SCHEMA,
            "team_id": self.team_id,
            "agent_id": self.agent_id,
            "sealedAt": now,
            "log": self.log.to_json(),
            "perceptionSummary": self.perception.summarize(),
            "intentions": self.intentions.to_json(),
            "affectSnapshot": self.affect.residue(now),
            "semantic": self.semantic.to_json(),
        }
        self.store.save(self.team_id, self.agent_id, "legacy", snapshot)
        meta = self.store.load(self.team_id, self.agent_id, "meta", {})
        if not isinstance(meta, dict):
            meta = {}
        meta["sealed"] = True
        meta["sealed_at"] = now
        self.store.save(self.team_id, self.agent_id, "meta", meta)
        return snapshot

    def memorial(self) -> Optional[Dict[str, Any]]:
        snap = self.store.load(self.team_id, self.agent_id, "legacy", None)
        if not isinstance(snap, dict):
            return None
        # deep copy so callers cannot mutate disk state via shared refs
        return json.loads(json.dumps(snap))

    def draft_will(self, now: Optional[int] = None) -> Dict[str, Any]:
        now = now if now is not None else _now_ms()
        return {
            "will": {
                "testator": self.agent_id,
                "team_id": self.team_id,
                "beneficiary": "",
                "migrate_preferences": [],
                "handover_intentions": "ask_new_owner",
                "keep_memorial": True,
            },
            "draftedAt": now,
            "note": "协议已定，迁移未实现 —— 本草稿仅声明意图。",
        }

    def overview(self) -> Dict[str, Any]:
        """Full panel payload for agent-config UI."""
        sealed = self.is_sealed()
        live_log = [e for e in self.log.replay() if not e.get("forgotten_at")]
        return {
            **self.meta(),
            "log": live_log[-80:],
            "perception": self.perception.to_json()[-40:],
            "perception_summary": self.perception.summarize(),
            "intentions": self.intentions.pending(),
            "intentions_all": self.intentions.all()[-40:],
            "affect": self.affect.residue(),
            "tone_hint": self.affect.tone_hint(),
            "semantic": self.semantic.active()[-40:],
            "working": self._working_slots(),
            "forgotten_recent": self.forgotten_audit(12),
            "systems": self.systems_view(),
            "topology": self.topology(),
            "memory_style": self.memory_style(),
            "dynamic_state": self.dynamic_state(),
            "memorial": self.memorial() if sealed else None,
            "disclosure": "这是回放，不是本人" if sealed else None,
            # 拟生 UI 提示
            "ui_labels": {
                "log": "情节",
                "perception": "感觉痕迹",
                "intentions": "前瞻意图（过程·非记忆层）",
                "affect": "情绪电荷（场·非事实层）",
                "semantic": "自传语义",
                "working": "工作台（过程）",
            },
        }
