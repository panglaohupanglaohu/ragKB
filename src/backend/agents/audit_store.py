# -*- coding: utf-8 -*-
"""审核存储 — JSON 文件持久化，幂等写入.

设计原则:
  - 轻量级: 单 JSON 文件，无需外部数据库
  - 线程安全: asyncio.Lock 保护并发写入
  - 幂等: idempotency_key 去重
  - 自愈: 文件损坏自动恢复
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .review_models import ReviewEntry, ReviewQueue, ReviewStatus

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "reviews"
STORAGE_FILE = STORAGE_DIR / "review_entries.json"
BACKUP_FILE = STORAGE_DIR / "review_entries.json.bak"


class AuditStore:
    """审核条目 JSON 文件持久化存储.

    用法:
        store = AuditStore()
        await store.initialize()
        entry = await store.upsert(entry)
        queue = await store.get_queue()
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._idempotency_keys: Dict[str, str] = {}  # key → entry_id
        self._initialized = False

    # ── 生命周期 ──────────────────────────────────────────

    async def initialize(self) -> bool:
        """初始化存储 — 确保目录存在 & 加载已有数据."""
        try:
            STORAGE_DIR.mkdir(parents=True, exist_ok=True)

            if STORAGE_FILE.exists():
                await self._load()
            else:
                await self._save()

            self._initialized = True
            logger.info(f"📁 AuditStore 初始化完成: {len(self._entries)} 条记录")
            return True
        except Exception as e:
            logger.error(f"❌ AuditStore 初始化失败: {e}")
            # 尝试从备份恢复
            if BACKUP_FILE.exists():
                try:
                    await self._load_from_backup()
                    self._initialized = True
                    logger.warning("⚠️ 从备份恢复 AuditStore")
                    return True
                except Exception as be:
                    logger.error(f"❌ 备份恢复也失败: {be}")
            return False

    async def _load(self) -> None:
        """从主文件加载数据."""
        content = STORAGE_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        self._entries = data.get("entries", {})
        self._idempotency_keys = data.get("idempotency_keys", {})
        logger.debug(f"📖 加载 {len(self._entries)} 条审核记录")

    async def _load_from_backup(self) -> None:
        """从备份文件恢复."""
        content = BACKUP_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        self._entries = data.get("entries", {})
        self._idempotency_keys = data.get("idempotency_keys", {})

    async def _save(self) -> None:
        """保存数据到文件 (先写回备份)."""
        data = {
            "entries": self._entries,
            "idempotency_keys": self._idempotency_keys,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        json_text = json.dumps(data, ensure_ascii=False, indent=2)

        # 先备份旧文件
        if STORAGE_FILE.exists():
            try:
                STORAGE_FILE.replace(BACKUP_FILE)
            except OSError:
                pass

        # 原子写入
        tmp_file = STORAGE_FILE.with_suffix(".tmp")
        tmp_file.write_text(json_text, encoding="utf-8")
        tmp_file.replace(STORAGE_FILE)

    # ── CRUD ───────────────────────────────────────────────

    async def upsert(self, entry: ReviewEntry) -> ReviewEntry:
        """插入或更新审核条目（幂等）.

        幂等逻辑:
          1. 如果 entry.id 已存在 → 仅更新 version > 旧 version 时写入
          2. 如果 idempotency_key 已存在 → 返回已有条目 (不重复创建)
          3. 否则 → 创建新条目

        Returns:
            最终存储的 ReviewEntry (可能是已有的或新创建的)
        """
        async with self._lock:
            # 幂等检查: idempotency_key
            if entry.idempotency_key:
                existing_id = self._idempotency_keys.get(entry.idempotency_key)
                if existing_id and existing_id != entry.id:
                    # 相同幂等键已存在不同 ID → 返回已有
                    existing_data = self._entries.get(existing_id)
                    if existing_data:
                        logger.info(f"🔄 幂等命中: key={entry.idempotency_key} → {existing_id}")
                        return ReviewEntry(**existing_data)

            # 版本检查: 如果条目已存在且 version 不高于已有版本，不更新
            if entry.id in self._entries:
                existing = self._entries[entry.id]
                if entry.version <= existing.get("version", 0):
                    logger.debug(f"⏭️ 版本跳过: {entry.id} v{entry.version} ≤ v{existing.get('version', 0)}")
                    return ReviewEntry(**existing)

            # 写入
            entry_data = entry.model_dump()
            self._entries[entry.id] = entry_data

            if entry.idempotency_key:
                self._idempotency_keys[entry.idempotency_key] = entry.id

            await self._save()
            logger.info(f"💾 保存审核条目: {entry.id} v{entry.version}")
            return entry

    async def get(self, entry_id: str) -> Optional[ReviewEntry]:
        """根据 ID 获取条目."""
        async with self._lock:
            data = self._entries.get(entry_id)
            if data:
                return ReviewEntry(**data)
            return None

    async def list_entries(
        self,
        status: Optional[ReviewStatus] = None,
        entity_id: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ReviewEntry]:
        """列出审核条目，支持按状态/实体/领域过滤."""
        async with self._lock:
            entries = []
            for data in self._entries.values():
                if status and data.get("status") != status.value:
                    continue
                if entity_id and data.get("entity_id") != entity_id:
                    continue
                if domain and data.get("domain") != domain:
                    continue
                entries.append(ReviewEntry(**data))

            # 按创建时间倒序
            entries.sort(key=lambda e: e.created_at, reverse=True)
            return entries[offset:offset + limit]

    async def get_queue(self) -> ReviewQueue:
        """获取审核队列聚合."""
        async with self._lock:
            entries = [ReviewEntry(**data) for data in self._entries.values()]
            queue = ReviewQueue(entries=entries)
            queue.refresh_stats()
            return queue

    async def count_by_status(self) -> Dict[str, int]:
        """按状态统计."""
        async with self._lock:
            counts = {}
            for data in self._entries.values():
                s = data.get("status", "pending")
                counts[s] = counts.get(s, 0) + 1
            return counts

    async def delete(self, entry_id: str) -> bool:
        """删除条目（同时清理幂等键）."""
        async with self._lock:
            if entry_id not in self._entries:
                return False
            # 清理幂等键
            entry_data = self._entries[entry_id]
            key = entry_data.get("idempotency_key")
            if key and key in self._idempotency_keys:
                del self._idempotency_keys[key]
            del self._entries[entry_id]
            await self._save()
            return True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def entry_count(self) -> int:
        return len(self._entries)


# ── 全局单例 ───────────────────────────────────────────────

_global_audit_store: Optional[AuditStore] = None


async def get_audit_store() -> AuditStore:
    """获取全局 AuditStore 单例."""
    global _global_audit_store
    if _global_audit_store is None:
        _global_audit_store = AuditStore()
        await _global_audit_store.initialize()
    return _global_audit_store


async def reset_audit_store() -> AuditStore:
    """重置全局单例 (测试用)."""
    global _global_audit_store
    _global_audit_store = AuditStore()
    await _global_audit_store.initialize()
    return _global_audit_store
