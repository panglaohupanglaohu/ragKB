# -*- coding: utf-8 -*-
"""统一技能库 — 桥接 SkillRegistry + SkillStore + Team-local 三套存储.

核心服务：跨团队技能发现、发布、引入、去重、演化流水线。
实现 SkillClaw 的 Filter→Improve→Verify→Solidify 四阶段流水线。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .domain_events import DomainEvent, EventType, SkillSnapshot
from .event_bus import get_event_bus
from .models import SkillCategory, SkillDefinition, SkillLifecycleStage

logger = logging.getLogger(__name__)


class SkillLibrary:
    """统一技能库 — 跨团队技能的中央枢纽.

    桥接三套存储:
    - SkillRegistry (内存全局默认技能)
    - SkillStore (持久化 JSON 文件)
    - Team-local (team.skills dict)
    - _version_snapshots (版本快照，支持回滚)
    """

    def __init__(self, team_manager=None, skill_registry=None, skill_store=None):
        self._team_manager = team_manager
        self._skill_registry = skill_registry
        self._skill_store = skill_store
        self._version_snapshots: Dict[str, List[Dict[str, Any]]] = {}  # skill_id -> [{version, name, instructions, desc, ...}]
        self._load_snapshots()

    # ── Browse: 统一搜索 ─────────────────────────────────────────

    def browse(
        self,
        team_id: str = "",
        query: str = "",
        visibility_filter: str = "",
        category_filter: str = "",
        lifecycle_filter: str = "",
    ) -> List[Dict[str, Any]]:
        """统一搜索: 自己的 + public + shared_with包含自己的."""
        results = []
        seen_ids = set()

        # Layer 1: Team-local skills
        if team_id and self._team_manager:
            team = self._team_manager.get_team(team_id)
            if team:
                for sid, skill in team.skills.items():
                    if sid not in seen_ids:
                        seen_ids.add(sid)
                        d = skill.to_dict()
                        d["_source_layer"] = "team_local"
                        d["_is_own"] = True
                        results.append(d)

        # Layer 2: SkillStore (persistent, all teams)
        if self._skill_store:
            for record in self._skill_store.list_all():
                sid = record.skill_id
                if sid in seen_ids:
                    continue
                # Include if: public, or shared_with includes team_id
                d = record.to_dict()
                vis = d.get("visibility", "private")
                adopted = d.get("adopted_by", [])
                origin = d.get("origin_team_id", "")
                if vis == "public" or team_id in adopted or origin == team_id:
                    seen_ids.add(sid)
                    d["_source_layer"] = "skill_store"
                    d["_is_own"] = (origin == team_id)
                    results.append(d)

        # Layer 3: SkillRegistry (in-memory defaults)
        if self._skill_registry:
            for skill in self._skill_registry.list_all():
                sid = skill.skill_id
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    d = skill.to_dict()
                    d["_source_layer"] = "registry"
                    d["_is_own"] = False
                    d["visibility"] = "builtin"
                    results.append(d)

        # Filters
        if query:
            q = query.lower()
            results = [r for r in results if q in (r.get("name", "") + r.get("description", "")).lower()]
        if visibility_filter:
            results = [r for r in results if r.get("visibility", "") == visibility_filter]
        if category_filter:
            results = [r for r in results if r.get("category", "") == category_filter]
        if lifecycle_filter:
            results = [r for r in results if r.get("lifecycle_stage", "") == lifecycle_filter]

        return results

    # ── Publish: private → public ────────────────────────────────

    def publish(self, team_id: str, skill_id: str) -> Dict[str, Any]:
        """发布技能到公共库. 生产发布必须通过最近一次 EvidenceRun 验证."""
        skill = self._find_skill(team_id, skill_id)
        if not skill:
            return {"error": "skill_not_found"}

        publish_gate = self.evaluate_publish_gate(team_id, skill_id)
        if not publish_gate.get("ok"):
            return {
                "error": "publish_gate_blocked",
                "skill_id": skill_id,
                "gate": publish_gate,
            }

        # Filter gate — skip for skills from distillation (source=distilled) which have LLM confidence
        if skill.source != "distilled" and skill.quality_score < 0.4 and skill.usage_count < 1:
            return {"error": "quality_too_low", "quality_score": skill.quality_score}

        skill.visibility = "public"
        skill.lifecycle_stage = SkillLifecycleStage.PUBLISHED
        self._persist_skill(skill, team_id)

        # Emit event
        bus = get_event_bus()
        event = DomainEvent.create(
            event_type=EventType.SKILL_UPDATED,
            payload=SkillSnapshot.from_skill_definition(skill),
            source="skill_library",
            correlation_id=f"publish:{skill_id}",
        )
        bus.publish(event)
        logger.info("Skill %s published to public library by team %s", skill_id, team_id)
        return {"status": "published", "skill_id": skill_id, "gate": publish_gate}

    def evaluate_publish_gate(self, team_id: str, skill_id: str) -> Dict[str, Any]:
        """Return whether a skill is allowed to enter public/production publish."""
        skill = self._find_skill(team_id, skill_id)
        if not skill:
            return {"ok": False, "reason": "skill_not_found", "checks": []}

        latest = self._latest_skill_verification(team_id, skill_id)
        checks: List[Dict[str, Any]] = []

        def add_check(name: str, passed: bool, detail: str) -> None:
            checks.append({"name": name, "passed": passed, "detail": detail})

        if not latest:
            add_check("recent_verification", False, "no skill_verify EvidenceRun found")
            return {
                "ok": False,
                "reason": "missing_verification_evidence",
                "checks": checks,
                "required": {
                    "evidence_type": "skill_verify",
                    "status": ["verified", "passed"],
                    "pass_rate_min": 0.7,
                    "exit_code": 0,
                },
            }

        latest_dict = latest.to_dict()
        metrics = latest.metrics_after or {}
        runtime = latest.runtime or {}
        status_value = str(latest.status or "").lower()
        pass_rate = float(metrics.get("pass_rate") or skill.quality_score or 0)
        lifecycle = skill.lifecycle_stage.value if hasattr(skill.lifecycle_stage, "value") else str(skill.lifecycle_stage)

        add_check(
            "verification_status",
            status_value in {"verified", "passed"},
            f"latest status={latest.status}",
        )
        add_check(
            "pass_rate",
            pass_rate >= 0.7,
            f"pass_rate={pass_rate:.2f}",
        )
        add_check(
            "runtime_ready",
            bool(runtime.get("ready", False)),
            f"runtime mode={runtime.get('mode', 'unknown')} ready={runtime.get('ready', False)}",
        )
        add_check(
            "exit_code",
            latest.exit_code == 0,
            f"exit_code={latest.exit_code}",
        )
        add_check(
            "lifecycle_verified",
            lifecycle == SkillLifecycleStage.VERIFIED.value or status_value in {"verified", "passed"},
            f"lifecycle_stage={lifecycle}",
        )

        ok = all(c["passed"] for c in checks)
        return {
            "ok": ok,
            "reason": "" if ok else "latest_verification_not_publishable",
            "checks": checks,
            "latest_evidence": {
                "evidence_id": latest.evidence_id,
                "created_at": latest.created_at,
                "status": latest.status,
                "runtime": runtime,
                "command": latest.command,
                "exit_code": latest.exit_code,
                "artifact_dir": latest.artifact_dir,
                "request_id": latest.request_id,
                "metrics_after": metrics,
            },
            "skill": {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "quality_score": skill.quality_score,
                "lifecycle_stage": lifecycle,
            },
        }

    def _latest_skill_verification(self, team_id: str, skill_id: str):
        try:
            from .evidence_store import EvidenceQuery, get_evidence_store
            results = get_evidence_store().query_evidence_sync(
                EvidenceQuery(
                    evidence_type="skill_verify",
                    team_id=team_id,
                    skill_id=skill_id,
                    limit=1,
                )
            )
            return results[0] if results else None
        except Exception as exc:
            logger.warning("Skill publish gate failed to load EvidenceRun: %s", exc)
            return None

    # ── Import: 从公共库引入到自己团队 ───────────────────────────

    def import_skill(self, target_team_id: str, skill_id: str) -> Dict[str, Any]:
        """引入公共技能到指定团队. 创建 adopted_by 关系."""
        # Find skill in public library
        skill = self._find_public_skill(skill_id)
        if not skill:
            return {"error": "skill_not_found_or_not_public"}

        if target_team_id in skill.adopted_by:
            return {"error": "already_adopted"}

        # Add to adopted_by
        skill.adopted_by.append(target_team_id)
        self._persist_skill(skill, skill.origin_team_id)

        # Copy to target team
        if self._team_manager:
            team = self._team_manager.get_team(target_team_id)
            if team:
                imported = SkillDefinition(
                    skill_id=skill.skill_id,
                    name=skill.name,
                    description=skill.description,
                    category=skill.category,
                    icon=skill.icon,
                    slug=skill.slug,
                    instructions=skill.instructions,
                    required_tools=skill.required_tools,
                    source="imported",
                    origin_team_id=skill.origin_team_id,
                    visibility="imported",
                    lifecycle_stage=skill.lifecycle_stage,
                    lineage=skill.skill_id,
                    schema_version=skill.schema_version,
                )
                team.add_skill(imported)
                self._team_manager.save()

        logger.info("Skill %s imported by team %s", skill_id, target_team_id)
        return {"status": "imported", "skill_id": skill_id, "target_team_id": target_team_id}

    # ── Overview: 全局总览 ───────────────────────────────────────

    def get_overview(self) -> Dict[str, Any]:
        """全局技能库总览: N团队, M技能, 共享率."""
        teams = []
        total_skills = 0
        public_skills = 0
        total_adopted = 0

        if self._team_manager:
            for team in self._team_manager.list_teams():
                tid = team.team_id
                team_skills = len(team.skills)
                team_public = sum(1 for s in team.skills.values() if s.visibility == "public")
                teams.append({
                    "team_id": tid,
                    "name": team.name,
                    "skill_count": team_skills,
                    "public_count": team_public,
                })
                total_skills += team_skills
                public_skills += team_public
                total_adopted += sum(len(s.adopted_by) for s in team.skills.values())

        return {
            "teams": teams,
            "total_teams": len(teams),
            "total_skills": total_skills,
            "public_skills": public_skills,
            "total_adoptions": total_adopted,
            "sharing_rate": public_skills / max(total_skills, 1),
        }

    # ── Find Duplicates: 跨团队去重 ─────────────────────────────

    def find_duplicates(self, threshold: float = 0.85) -> List[Dict[str, Any]]:
        """利用简单文本相似度检测跨团队重复技能."""
        all_skills = self.browse()
        duplicates = []

        for i, s1 in enumerate(all_skills):
            for s2 in all_skills[i + 1:]:
                sim = self._text_similarity(
                    (s1.get("name", "") + " " + s1.get("description", "")).lower(),
                    (s2.get("name", "") + " " + s2.get("description", "")).lower(),
                )
                if sim >= threshold:
                    duplicates.append({
                        "skill_a": {"skill_id": s1["skill_id"], "name": s1["name"], "team": s1.get("origin_team_id", "")},
                        "skill_b": {"skill_id": s2["skill_id"], "name": s2["name"], "team": s2.get("origin_team_id", "")},
                        "similarity": round(sim, 3),
                    })

        return duplicates

    # ── Lineage: 演化谱系树 ──────────────────────────────────────

    def get_lineage(self, skill_id: str) -> Dict[str, Any]:
        """获取技能的演化谱系 (parent→child chain)."""
        all_skills = self.browse()
        by_id = {s["skill_id"]: s for s in all_skills}

        lineage = []
        current_id = skill_id
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            if current_id in by_id:
                lineage.append(by_id[current_id])
            parent_id = by_id.get(current_id, {}).get("lineage", "")
            current_id = parent_id

        # Find children
        children = [s for s in all_skills if s.get("lineage", "") == skill_id]

        return {
            "skill_id": skill_id,
            "ancestors": list(reversed(lineage[1:])),  # oldest first
            "current": by_id.get(skill_id),
            "children": children,
        }

    # ── Lifecycle transitions ────────────────────────────────────

    def solidify(self, team_id: str, skill_id: str) -> Dict[str, Any]:
        """固化技能: 锁定版本 → 推送到所有 adopted_by 团队."""
        skill = self._find_skill(team_id, skill_id)
        if not skill:
            return {"error": "skill_not_found"}

        skill.lifecycle_stage = SkillLifecycleStage.SOLIDIFIED
        self._persist_skill(skill, team_id)

        # Push update to all adopted_by teams
        pushed = []
        if self._team_manager:
            for adopted_tid in skill.adopted_by:
                team = self._team_manager.get_team(adopted_tid)
                if team and skill_id in team.skills:
                    team.skills[skill_id].instructions = skill.instructions
                    team.skills[skill_id].lifecycle_stage = SkillLifecycleStage.SOLIDIFIED
                    team.skills[skill_id].version = skill.version
                    pushed.append(adopted_tid)
            if pushed:
                self._team_manager.save()

        logger.info("Skill %s solidified, pushed to %d teams", skill_id, len(pushed))
        return {"status": "solidified", "pushed_to": pushed}

    # ── Helpers ──────────────────────────────────────────────────

    def _find_skill(self, team_id: str, skill_id: str) -> Optional[SkillDefinition]:
        """Find skill in team-local first, then skill store, then registry. Matches by skill_id or slug."""
        if self._team_manager:
            team = self._team_manager.get_team(team_id)
            if team:
                if skill_id in team.skills:
                    return team.skills[skill_id]
                # Fallback: match by slug
                for s in team.skills.values():
                    if s.slug == skill_id:
                        return s
        # Layer 2: SkillStore (persistent JSON files)
        if self._skill_store:
            record = self._skill_store.get(skill_id)
            if record and record.snapshot:
                snap = record.snapshot
                # Convert string category to SkillCategory enum
                try:
                    cat = SkillCategory(snap.category) if isinstance(snap.category, str) else snap.category
                except (ValueError, KeyError):
                    cat = SkillCategory.GENERAL
                return SkillDefinition(
                    skill_id=snap.skill_id,
                    name=snap.name,
                    description=snap.description,
                    category=cat,
                    instructions=snap.instructions,
                    slug=snap.slug,
                    source=snap.source,
                    icon=snap.icon,
                    required_tools=list(snap.required_tools) if snap.required_tools else [],
                    enabled=snap.enabled,
                    required=snap.required,
                    is_default=snap.is_default,
                )
        if self._skill_registry:
            found = self._skill_registry.get(skill_id)
            if found:
                return found
            # Fallback: match by slug in registry
            for s in self._skill_registry.list_all():
                if s.slug == skill_id:
                    return s
        return None

    def _find_public_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """Find a public skill across all teams."""
        if self._team_manager:
            for team in self._team_manager.list_teams():
                if skill_id in team.skills:
                    s = team.skills[skill_id]
                    if s.visibility == "public":
                        return s
        return None

    def _persist_skill(self, skill: SkillDefinition, team_id: str) -> None:
        """Write skill back to team + store."""
        if self._team_manager:
            team = self._team_manager.get_team(team_id)
            if team:
                team.skills[skill.skill_id] = skill
                # Persist via TeamManager's internal method
                try:
                    if hasattr(self._team_manager, '_persist'):
                        self._team_manager._persist()
                except Exception as e:
                    logger.error("TeamManager._persist() failed: %s", e)
        if self._skill_store:
            try:
                from .skill_store import SkillRecord
                from .domain_events import SkillSnapshot
                snapshot = SkillSnapshot.from_skill_definition(skill)
                record = SkillRecord(skill_id=skill.skill_id, snapshot=snapshot)
                self._skill_store.upsert(record)
            except Exception as e:
                logger.error("SkillStore.upsert() failed for %s: %s", skill.skill_id, e)

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """Simple Jaccard token similarity."""
        if not a or not b:
            return 0.0
        tokens_a = set(a.split())
        tokens_b = set(b.split())
        if not tokens_a or not tokens_b:
            return 0.0
        return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)

    # ── Version Snapshots (回滚支持) ──────────────────────────────

    def _snapshot_path(self) -> Path:
        from pathlib import Path as _Path
        return _Path(__file__).resolve().parents[3] / "storage" / "skill_versions.json"

    def _load_snapshots(self) -> None:
        try:
            p = self._snapshot_path()
            if p.exists():
                import json
                self._version_snapshots = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            self._version_snapshots = {}

    def _save_snapshots(self) -> None:
        try:
            import json
            p = self._snapshot_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self._version_snapshots, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save skill version snapshots: {e}")

    def create_version_snapshot(self, skill: Any) -> Dict[str, Any]:
        """保存技能当前状态为版本快照."""
        sid = getattr(skill, "skill_id", "") or getattr(skill, "slug", "")
        if not sid:
            return {"error": "invalid skill"}
        ver = getattr(skill, "version", 1)
        snap = {
            "version": ver,
            "name": getattr(skill, "name", ""),
            "description": getattr(skill, "description", ""),
            "instructions": getattr(skill, "instructions", ""),
            "category": getattr(skill, "category", "general"),
            "icon": getattr(skill, "icon", "⚡"),
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }
        self._version_snapshots.setdefault(sid, []).append(snap)
        # Keep last 10 versions
        if len(self._version_snapshots[sid]) > 10:
            self._version_snapshots[sid] = self._version_snapshots[sid][-10:]
        self._save_snapshots()
        return {"skill_id": sid, "version": ver, "ok": True}

    def list_versions(self, skill_id: str) -> List[Dict[str, Any]]:
        """列出技能的所有版本快照."""
        return self._version_snapshots.get(skill_id, [])

    def rollback_version(self, team_id: str, skill_id: str, target_version: int) -> Dict[str, Any]:
        """回滚技能到指定版本."""
        versions = self._version_snapshots.get(skill_id, [])
        target = next((v for v in versions if v.get("version") == target_version), None)
        if not target:
            return {"error": f"版本 {target_version} 不存在", "available_versions": [v.get("version") for v in versions]}

        skill = self._find_skill(team_id, skill_id)
        if not skill:
            return {"error": f"技能 {skill_id} 未找到"}

        # Save current state as snapshot before rollback
        self.create_version_snapshot(skill)

        # Apply target version
        skill.name = target.get("name", skill.name)
        skill.description = target.get("description", skill.description)
        skill.instructions = target.get("instructions", skill.instructions)
        skill.category = target.get("category", skill.category)
        skill.icon = target.get("icon", skill.icon)
        skill.version = getattr(skill, "version", 1) + 1

        self._persist_skill(skill, team_id)
        return {"skill_id": skill_id, "rolled_back_to": target_version, "new_version": skill.version, "ok": True}


# ── Singleton ────────────────────────────────────────────────────

_skill_library: Optional[SkillLibrary] = None


def get_skill_library() -> SkillLibrary:
    global _skill_library
    if _skill_library is None:
        _skill_library = SkillLibrary()
    return _skill_library


def init_skill_library(team_manager=None, skill_registry=None, skill_store=None) -> SkillLibrary:
    global _skill_library
    _skill_library = SkillLibrary(
        team_manager=team_manager,
        skill_registry=skill_registry,
        skill_store=skill_store,
    )
    logger.info("SkillLibrary initialized (team_manager=%s, registry=%s, store=%s)",
                bool(team_manager), bool(skill_registry), bool(skill_store))
    return _skill_library
