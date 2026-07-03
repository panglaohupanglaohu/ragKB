# -*- coding: utf-8 -*-
"""SkillStore — 技能主表持久化，支持幂等写入与 schema_version。

核心设计:
1. **幂等写入**: 通过 idempotency_key (skill_id + version) 去重
2. **schema_version**: 每条记录携带结构版本，支持跨版本兼容和迁移
3. **主表结构**: SkillRecord 是存储单元，包含完整 SkillDefinition 快照
4. **持久化**: JSON 文件存储 (遵循 plaza_store / task_store 模式)
5. **事件发布**: 写入成功后通过 EventBus 发布领域事件
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .domain_events import DomainEvent, EventType, SkillSnapshot
from .event_bus import get_event_bus

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════════════

STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "skills"
CURRENT_SCHEMA_VERSION = 1  # 当前技能记录 schema 版本

# schema migration 注册表: version → upgrade function
# 未来版本升级时在这里注册迁移函数
_SCHEMA_MIGRATIONS: Dict[int, callable] = {}


# ══════════════════════════════════════════════════════════════════════
# SkillRecord — 存储单元
# ══════════════════════════════════════════════════════════════════════

class SkillRecord:
    """技能主表记录 — 持久化单元.

    字段:
        skill_id: 技能唯一标识
        schema_version: 记录结构版本号 (用于迁移)
        idempotency_key: 幂等键 = f"{skill_id}:{version}"
        snapshot: SkillSnapshot (完整技能快照)
        created_at: 首次写入时间
        updated_at: 最后更新时间
        version: 乐观锁版本号 (每次更新 +1)
        is_deleted: 软删除标记
    """

    def __init__(
        self,
        skill_id: str,
        schema_version: int = CURRENT_SCHEMA_VERSION,
        snapshot: Optional[SkillSnapshot] = None,
        idempotency_key: str = "",
        created_at: str = "",
        updated_at: str = "",
        version: int = 1,
        is_deleted: bool = False,
    ):
        self.skill_id = skill_id
        self.schema_version = schema_version
        self.snapshot = snapshot or SkillSnapshot(skill_id=skill_id, name="", description="", category="general")
        self.idempotency_key = idempotency_key or f"{skill_id}:v{version}"
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at
        self.version = version
        self.is_deleted = is_deleted

    def touch(self) -> None:
        """更新时间戳和版本号."""
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.version += 1
        self.idempotency_key = f"{self.skill_id}:v{self.version}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "schema_version": self.schema_version,
            "idempotency_key": self.idempotency_key,
            "snapshot": self.snapshot.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "is_deleted": self.is_deleted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillRecord":
        snapshot_data = data.get("snapshot", {})
        snapshot = SkillSnapshot(
            skill_id=snapshot_data.get("skill_id", data.get("skill_id", "")),
            name=snapshot_data.get("name", ""),
            description=snapshot_data.get("description", ""),
            category=snapshot_data.get("category", "general"),
            required=snapshot_data.get("required", False),
            enabled=snapshot_data.get("enabled", True),
            icon=snapshot_data.get("icon", "⚡"),
            slug=snapshot_data.get("slug", ""),
            source=snapshot_data.get("source", "builtin"),
            required_tools=snapshot_data.get("required_tools", []),
            instructions=snapshot_data.get("instructions", ""),
            config_schema=snapshot_data.get("config_schema", {}),
            config=snapshot_data.get("config", {}),
            is_default=snapshot_data.get("is_default", False),
            metadata=snapshot_data.get("metadata", {}),
        )
        return cls(
            skill_id=data.get("skill_id", ""),
            schema_version=data.get("schema_version", CURRENT_SCHEMA_VERSION),
            snapshot=snapshot,
            idempotency_key=data.get("idempotency_key", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            version=data.get("version", 1),
            is_deleted=data.get("is_deleted", False),
        )


# ══════════════════════════════════════════════════════════════════════
# SkillStore
# ══════════════════════════════════════════════════════════════════════

class SkillStore:
    """技能主表 — JSON 文件持久化，幂等写入。

    用法:
        store = SkillStore()

        # 幂等写入 (相同 idempotency_key 会跳过)
        record, created = store.upsert(skill_record)
        if created:
            print("New skill written")

        # 查询
        rec = store.get("skill_001")
        all_recs = store.list_all()
    """

    def __init__(self, emit_events: bool = True):
        self._store_dir = STORAGE_DIR
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._records: Dict[str, SkillRecord] = {}
        self._idempotency_index: Dict[str, str] = {}  # idempotency_key → skill_id
        self._emit_events = emit_events
        self._load_all()

    # ── 持久化 IO ──────────────────────────────────────────────────

    def _file_path(self, skill_id: str) -> Path:
        return self._store_dir / f"{skill_id}.json"

    def _load_all(self) -> None:
        """从磁盘加载所有技能记录."""
        loaded = 0
        for fpath in self._store_dir.glob("*.json"):
            try:
                data = json.loads(fpath.read_text("utf-8"))
                # schema migration on load
                sv = data.get("schema_version", 0)
                if sv < CURRENT_SCHEMA_VERSION:
                    data = self._migrate_record(data, sv, CURRENT_SCHEMA_VERSION)
                record = SkillRecord.from_dict(data)
                self._records[record.skill_id] = record
                self._idempotency_index[record.idempotency_key] = record.skill_id
                loaded += 1
            except Exception as exc:
                logger.error(f"❌ 加载技能文件失败 [{fpath.name}]: {exc}")
        logger.info(f"📦 SkillStore 加载完成: {loaded} 条记录")

    def _save_one(self, record: SkillRecord) -> None:
        """保存单条记录到磁盘."""
        fpath = self._file_path(record.skill_id)
        fpath.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), "utf-8")

    def _delete_file(self, skill_id: str) -> None:
        """删除磁盘文件."""
        fpath = self._file_path(skill_id)
        if fpath.exists():
            fpath.unlink()

    # ── Schema Migration ───────────────────────────────────────────

    def _migrate_record(self, data: Dict[str, Any], from_version: int, to_version: int) -> Dict[str, Any]:
        """对单条记录执行 schema 迁移."""
        for v in range(from_version, to_version):
            migrator = _SCHEMA_MIGRATIONS.get(v)
            if migrator:
                data = migrator(data)
        data["schema_version"] = to_version
        return data

    @classmethod
    def register_migration(cls, from_version: int, migrator: callable) -> None:
        """注册 schema 迁移函数.

        Args:
            from_version: 从哪个版本开始迁移
            migrator: 迁移函数 (data: dict) -> dict
        """
        _SCHEMA_MIGRATIONS[from_version] = migrator
        logger.info(f"🔧 Schema migration registered: v{from_version} → v{from_version + 1}")

    # ── CRUD ───────────────────────────────────────────────────────

    def upsert(self, record: SkillRecord, idempotency_key: str = "") -> Tuple[SkillRecord, bool]:
        """幂等写入 — 如果 idempotency_key 已处理过则跳过.

        Args:
            record: 要写入的 SkillRecord
            idempotency_key: 幂等键 (默认使用 record.idempotency_key)

        Returns:
            (record, created): 最终记录和是否为新创建
        """
        key = idempotency_key or record.idempotency_key

        # 幂等检查
        if key in self._idempotency_index:
            existing_id = self._idempotency_index[key]
            if existing_id in self._records:
                logger.debug(f"⏭️ 幂等跳过: {key} (skill={existing_id})")
                return self._records[existing_id], False

        # 写入或更新
        existing = self._records.get(record.skill_id)
        if existing:
            # 更新已有记录
            existing.snapshot = record.snapshot
            existing.schema_version = record.schema_version
            existing.touch()
            existing.is_deleted = record.is_deleted
            self._idempotency_index[key] = existing.skill_id
            self._save_one(existing)
            logger.info(f"🔄 SkillStore 更新: {existing.skill_id} v{existing.version}")
            self._emit_event(
                EventType.SKILL_UPDATED if not existing.is_deleted else EventType.SKILL_DELETED,
                existing,
            )
            return existing, False
        else:
            # 新记录
            record.touch()
            record.idempotency_key = key
            self._records[record.skill_id] = record
            self._idempotency_index[key] = record.skill_id
            self._save_one(record)
            logger.info(f"✅ SkillStore 创建: {record.skill_id} schema=v{record.schema_version}")
            self._emit_event(EventType.SKILL_CREATED, record)
            return record, True

    def get(self, skill_id: str, include_deleted: bool = False) -> Optional[SkillRecord]:
        """按 skill_id 查询."""
        record = self._records.get(skill_id)
        if record and (include_deleted or not record.is_deleted):
            return record
        return None

    def list_all(self, include_deleted: bool = False) -> List[SkillRecord]:
        """列出所有技能记录."""
        if include_deleted:
            return list(self._records.values())
        return [r for r in self._records.values() if not r.is_deleted]

    def list_by_category(self, category: str) -> List[SkillRecord]:
        """按类别筛选."""
        return [
            r for r in self._records.values()
            if not r.is_deleted and r.snapshot.category == category
        ]

    def delete(self, skill_id: str, soft: bool = True) -> bool:
        """删除技能记录.

        Args:
            skill_id: 技能ID
            soft: True=软删除 (标记 is_deleted), False=硬删除 (删除文件)
        """
        record = self._records.get(skill_id)
        if not record:
            return False
        if soft:
            record.is_deleted = True
            record.touch()
            self._save_one(record)
            logger.info(f"🗑️ SkillStore 软删除: {skill_id}")
            self._emit_event(EventType.SKILL_DELETED, record)
        else:
            del self._records[skill_id]
            # 清理幂等索引
            keys_to_remove = [k for k, v in self._idempotency_index.items() if v == skill_id]
            for k in keys_to_remove:
                del self._idempotency_index[k]
            self._delete_file(skill_id)
            logger.info(f"💥 SkillStore 硬删除: {skill_id}")
        return True

    def count(self, include_deleted: bool = False) -> int:
        """记录总数."""
        if include_deleted:
            return len(self._records)
        return sum(1 for r in self._records.values() if not r.is_deleted)

    # ── 事件发布 ──────────────────────────────────────────────────

    def _emit_event(self, event_type: EventType, record: SkillRecord) -> None:
        """发布领域事件."""
        if not self._emit_events:
            return
        try:
            bus = get_event_bus()
            event = DomainEvent.create(
                event_type=event_type,
                payload=record.snapshot,
                schema_version=record.schema_version,
                source="skill_store",
            )
            bus.publish(event)
        except Exception as exc:
            logger.error(f"❌ 发布事件失败 [{event_type.value}]: {exc}")
