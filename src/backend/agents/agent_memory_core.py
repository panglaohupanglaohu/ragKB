# -*- coding: utf-8 -*-
"""Agent 四层记忆核心 — 移植自 TigerInBamboo 画中生物记忆模块.

绑定键: team_id + agent_id（记忆与智能体解耦存储，可导出/封存/导入）
四层: log(运行日志) / perception(感知流) / intentions(未发送队列) / affect(情绪残留)
存储: storage/agent_memory/<team_id>/<agent_id>/{log,perception,intentions,affect,legacy,meta}.json

设计原则对齐 TigerInBamboo docs/memory-architecture.md:
- 记忆是遗体不是数据库；共享时间轴；封存是仪式不是删除；回放不是对话
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
    return score


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


class AffectResidue:
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
    """一只智能体的记忆核心：四层 + 共享时间轴 + 绑定元数据."""

    def __init__(self, team_id: str, agent_id: str, store: Optional[AgentMemoryStore] = None):
        if not team_id or not agent_id:
            raise ValueError("team_id and agent_id required")
        self.team_id = team_id
        self.agent_id = agent_id
        self.store = store or get_memory_store()
        self.log = EpisodicLog(self.store, team_id, agent_id)
        self.perception = PerceptionStream(self.store, team_id, agent_id)
        self.intentions = IntentionQueue(self.store, team_id, agent_id)
        self.affect = AffectResidue(self.store, team_id, agent_id)

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
        }

    def at(self, t: int, window_ms: int = 60_000) -> Dict[str, Any]:
        return {
            "t": t,
            "log": self.log.at(t, window_ms),
            "perception": self.perception.perceive_at(t, window_ms),
            "intentions": self.intentions.at(t),
            "affect": self.affect.at(t),
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
            },
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
        if isinstance(data.get("meta"), dict):
            meta = self.store.load(self.team_id, self.agent_id, "meta", {})
            if not isinstance(meta, dict):
                meta = {}
            meta.update(data["meta"])
            meta["bound"] = True
            meta["imported_at"] = _now_ms()
            self.store.save(self.team_id, self.agent_id, "meta", meta)
        return True

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
        return {
            **self.meta(),
            "log": self.log.replay()[-80:],
            "perception": self.perception.to_json()[-40:],
            "perception_summary": self.perception.summarize(),
            "intentions": self.intentions.pending(),
            "intentions_all": self.intentions.all()[-40:],
            "affect": self.affect.residue(),
            "tone_hint": self.affect.tone_hint(),
            "memorial": self.memorial() if sealed else None,
            "disclosure": "这是回放，不是本人" if sealed else None,
        }
