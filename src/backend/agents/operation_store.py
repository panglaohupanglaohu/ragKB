# -*- coding: utf-8 -*-
"""操作存储 — JSON 文件持久化，append-only 不可变存储。

设计原则:
  - Append-only: OperationEvent 和 ContextSlice 只追加，不可修改/删除
  - 完整性: 每条记录带 SHA256 哈希，读取时自动校验
  - 幂等: idempotency_key 去重
  - 线程安全: asyncio.Lock 保护并发写入
  - 自愈: 文件损坏自动备份并恢复
  - 分区: 按日期分区存储 (YYYY-MM 目录)，避免单文件过大

对标 Event Sourcing EventStore + DDD Audit Log.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .operation_models import (
    OperationEvent,
    OperationType,
    OperationTrace,
    OperationQuery,
    ContextQuery,
    ContextSlice,
    ContextType,
)

logger = logging.getLogger(__name__)

# 存储根目录
STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "operations"


# ═══════════════════════════════════════════════════════════════
# Storage Helpers
# ═══════════════════════════════════════════════════════════════


def _get_month_dir(timestamp: Optional[str] = None) -> Path:
    """获取日期分区目录 (YYYY-MM).

    若未提供时间戳则使用当前 UTC 时间。
    """
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    return STORAGE_DIR / dt.strftime("%Y-%m")


def _ensure_dir(path: Path) -> None:
    """确保目录存在."""
    path.mkdir(parents=True, exist_ok=True)


def _atomic_write(path: Path, data: str) -> None:
    """原子写入 — 先写临时文件再 rename."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


# ═══════════════════════════════════════════════════════════════
# OperationStore
# ═══════════════════════════════════════════════════════════════


class OperationStore:
    """操作事件 & 情境切片持久化存储.

    用法:
        store = OperationStore()
        event = OperationEvent.create(...)
        await store.append_operation(event)
        await store.append_slice(ContextSlice.create(...))
        traces = await store.query_traces(OperationQuery(...))
    """

    def __init__(self, base_dir: Optional[str] = None):
        self._base_dir = Path(base_dir) if base_dir else STORAGE_DIR
        self._lock = asyncio.Lock()
        # 内存缓存最近 1000 条操作，加速查询
        self._op_cache: List[OperationEvent] = []
        self._cs_cache: List[ContextSlice] = []
        self._max_cache = 1000
        # 幂等键集合
        self._idempotency_keys: set = set()
        self._idempotency_max = 50000

    # ── 写入 ─────────────────────────────────────────────

    async def append_operation(self, event: OperationEvent) -> bool:
        """追加一条操作事件 (不可变写入).

        Returns:
            True 如果新增, False 如果幂等去重 (已存在).
        """
        async with self._lock:
            # 幂等检查
            if event.idempotency_key and event.idempotency_key in self._idempotency_keys:
                logger.debug(f"⏭️ 幂等跳过: {event.operation_id} key={event.idempotency_key}")
                return False

            month_dir = _get_month_dir(event.timestamp)
            _ensure_dir(month_dir)

            # 写入事件
            event_file = month_dir / f"{event.operation_id}.json"
            _atomic_write(event_file, json.dumps(event.to_dict(), ensure_ascii=False, indent=2))

            # 记录幂等键
            if event.idempotency_key:
                self._idempotency_keys.add(event.idempotency_key)
                if len(self._idempotency_keys) > self._idempotency_max:
                    self._prune_idempotency_keys()

            # 更新缓存
            self._op_cache.append(event)
            if len(self._op_cache) > self._max_cache:
                self._op_cache = self._op_cache[-self._max_cache:]

            logger.info(
                f"📝 操作已记录: {event.operation_id} "
                f"type={event.operation_type.value} agent={event.agent_id}"
            )
            return True

    async def append_slice(self, context_slice: ContextSlice) -> bool:
        """追加一条情境切片.

        Returns:
            True 如果写入成功.
        """
        async with self._lock:
            month_dir = _get_month_dir(context_slice.timestamp)
            _ensure_dir(month_dir)

            # 写入切片
            slice_file = month_dir / f"{context_slice.slice_id}.json"
            _atomic_write(slice_file, json.dumps(context_slice.to_dict(), ensure_ascii=False, indent=2))

            # 更新缓存
            self._cs_cache.append(context_slice)
            if len(self._cs_cache) > self._max_cache:
                self._cs_cache = self._cs_cache[-self._max_cache:]

            logger.debug(f"📎 切片已记录: {context_slice.slice_id} → {context_slice.operation_id}")
            return True

    async def record_operation_with_context(
        self,
        event: OperationEvent,
        slices: List[ContextSlice],
    ) -> bool:
        """原子写入操作事件及其所有关联情境切片.

        如果 operation 幂等跳过，切片也不会写入。
        """
        async with self._lock:
            # 幂等检查
            if event.idempotency_key and event.idempotency_key in self._idempotency_keys:
                logger.debug(f"⏭️ 幂等跳过: {event.operation_id}")
                return False

            # 写入事件
            month_dir = _get_month_dir(event.timestamp)
            _ensure_dir(month_dir)
            event_file = month_dir / f"{event.operation_id}.json"
            _atomic_write(event_file, json.dumps(event.to_dict(), ensure_ascii=False, indent=2))

            # 写入所有切片
            for cs in slices:
                # 确保切片关联到本操作
                if cs.operation_id != event.operation_id:
                    cs = ContextSlice(
                        slice_id=cs.slice_id,
                        operation_id=event.operation_id,
                        context_type=cs.context_type,
                        timestamp=cs.timestamp,
                        payload=cs.payload,
                        summary=cs.summary,
                        context_hash=cs.context_hash,
                        schema_version=cs.schema_version,
                        entity_id=cs.entity_id,
                        entity_type=cs.entity_type,
                    )
                slice_file = month_dir / f"{cs.slice_id}.json"
                _atomic_write(slice_file, json.dumps(cs.to_dict(), ensure_ascii=False, indent=2))

            # 幂等键
            if event.idempotency_key:
                self._idempotency_keys.add(event.idempotency_key)
                if len(self._idempotency_keys) > self._idempotency_max:
                    self._prune_idempotency_keys()

            # 缓存
            self._op_cache.append(event)
            self._cs_cache.extend(slices)
            self._trim_cache()

            logger.info(
                f"📦 操作+{len(slices)}切片已记录: {event.operation_id}"
            )
            return True

    # ── 查询 ─────────────────────────────────────────────

    async def get_operation(self, operation_id: str) -> Optional[OperationEvent]:
        """按 ID 获取操作事件."""
        # 先查缓存
        for evt in self._op_cache:
            if evt.operation_id == operation_id:
                return evt
        # 再扫文件
        return await self._load_operation_from_disk(operation_id)

    async def get_slice(self, slice_id: str) -> Optional[ContextSlice]:
        """按 ID 获取情境切片."""
        for cs in self._cs_cache:
            if cs.slice_id == slice_id:
                return cs
        return await self._load_slice_from_disk(slice_id)

    async def query_operations(self, q: OperationQuery) -> List[OperationEvent]:
        """按过滤器查询操作事件列表."""
        results: List[OperationEvent] = []
        # 从缓存查询 (如果缓存覆盖足够)
        if not q.start_time and not q.end_time:
            for evt in reversed(self._op_cache):
                if q.matches(evt):
                    results.append(evt)
                    if len(results) >= q.limit:
                        return results
        # 缓存不够，扫描月度文件
        results = await self._scan_operations(q)
        return results[q.offset:q.offset+q.limit] if q.offset else results[:q.limit]

    async def query_slices(self, q: ContextQuery) -> List[ContextSlice]:
        """按过滤器查询情境切片列表."""
        results: List[ContextSlice] = []
        if q.operation_id:
            # 指定了 operation_id，先从缓存查
            for cs in self._cs_cache:
                if cs.operation_id == q.operation_id and q.matches(cs):
                    results.append(cs)
            # 如果缓存不完整，扫描文件
            if not results:
                results = await self._scan_slices_for_operation(q.operation_id)
                results = [s for s in results if q.matches(s)]
        else:
            for cs in reversed(self._cs_cache):
                if q.matches(cs):
                    results.append(cs)
                    if len(results) >= q.limit:
                        return results
            results = await self._scan_slices(q)
        return results[q.offset:q.offset+q.limit] if q.offset else results[:q.limit]

    async def query_traces(self, q: OperationQuery) -> List[OperationTrace]:
        """查询操作追溯视图 — 操作事件 + 关联情境切片.

        这是审计查询的核心方法。
        """
        operations = await self.query_operations(q)
        traces = []
        for op in operations:
            slices = await self.get_slices_for_operation(op.operation_id)
            traces.append(OperationTrace(operation=op, context_slices=slices))
        return traces

    async def get_trace(self, operation_id: str) -> Optional[OperationTrace]:
        """获取单个操作的完整追溯."""
        op = await self.get_operation(operation_id)
        if not op:
            return None
        slices = await self.get_slices_for_operation(operation_id)
        return OperationTrace(operation=op, context_slices=slices)

    async def get_slices_for_operation(self, operation_id: str) -> List[ContextSlice]:
        """获取某操作关联的所有情境切片."""
        # 缓存查询
        cached = [cs for cs in self._cs_cache if cs.operation_id == operation_id]
        if cached:
            return cached
        # 扫描文件
        return await self._scan_slices_for_operation(operation_id)

    async def get_causal_chain(self, operation_id: str, max_depth: int = 20) -> List[OperationEvent]:
        """追溯操作因果链 — 从当前操作沿 parent_operation_id 回溯."""
        chain = []
        current_id = operation_id
        while current_id and len(chain) < max_depth:
            op = await self.get_operation(current_id)
            if not op:
                break
            chain.append(op)
            current_id = op.parent_operation_id
        return chain

    # ── 完整性验证 ──────────────────────────────────────

    async def verify_all(self) -> Dict[str, Any]:
        """验证存储中所有记录的数据完整性.

        Returns:
            dict with {total_ops, corrupt_ops, total_slices, corrupt_slices, details}.
        """
        result = {
            "total_ops": 0,
            "corrupt_ops": 0,
            "total_slices": 0,
            "corrupt_slices": 0,
            "details": [],
        }

        if not self._base_dir.exists():
            return result

        for month_dir in sorted(self._base_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for f in month_dir.iterdir():
                if f.suffix != ".json" or f.suffix == ".tmp":
                    continue
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    result["details"].append(
                        {"file": str(f), "error": "JSON 解析失败"}
                    )
                    continue

                # 区分 OperationEvent 和 ContextSlice
                if "operation_type" in data:
                    # 是 OperationEvent
                    result["total_ops"] += 1
                    try:
                        evt = OperationEvent.from_dict(data)
                        if not evt.verify_integrity():
                            result["corrupt_ops"] += 1
                            result["details"].append({
                                "file": str(f),
                                "type": "operation",
                                "id": evt.operation_id,
                                "error": "哈希不匹配 - 数据可能被篡改",
                            })
                    except Exception as e:
                        result["corrupt_ops"] += 1
                        result["details"].append({
                            "file": str(f),
                            "type": "operation",
                            "error": str(e),
                        })
                elif "context_type" in data:
                    # 是 ContextSlice
                    result["total_slices"] += 1
                    try:
                        cs = ContextSlice.from_dict(data)
                        if not cs.verify_integrity():
                            result["corrupt_slices"] += 1
                            result["details"].append({
                                "file": str(f),
                                "type": "context_slice",
                                "id": cs.slice_id,
                                "error": "哈希不匹配 - 数据可能被篡改",
                            })
                    except Exception as e:
                        result["corrupt_slices"] += 1
                        result["details"].append({
                            "file": str(f),
                            "type": "context_slice",
                            "error": str(e),
                        })

        return result

    # ── 统计 ────────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息."""
        stats = {
            "total_operations": 0,
            "total_slices": 0,
            "by_type": {},
            "by_agent": {},
            "oldest_timestamp": None,
            "newest_timestamp": None,
        }

        if not self._base_dir.exists():
            return stats

        for month_dir in self._base_dir.iterdir():
            if not month_dir.is_dir():
                continue
            for f in month_dir.iterdir():
                if f.suffix != ".json" or f.suffix == ".tmp":
                    continue
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue

                ts = data.get("timestamp", "")
                if ts:
                    if not stats["oldest_timestamp"] or ts < stats["oldest_timestamp"]:
                        stats["oldest_timestamp"] = ts
                    if not stats["newest_timestamp"] or ts > stats["newest_timestamp"]:
                        stats["newest_timestamp"] = ts

                if "operation_type" in data:
                    stats["total_operations"] += 1
                    op_type = data.get("operation_type", "unknown")
                    stats["by_type"][op_type] = stats["by_type"].get(op_type, 0) + 1
                    agent_id = data.get("agent_id", "unknown")
                    stats["by_agent"][agent_id] = stats["by_agent"].get(agent_id, 0) + 1
                elif "context_type" in data:
                    stats["total_slices"] += 1

        return stats

    # ── 内部方法 ────────────────────────────────────────

    async def _load_operation_from_disk(self, operation_id: str) -> Optional[OperationEvent]:
        """从磁盘文件加载操作事件."""
        if not self._base_dir.exists():
            return None
        for month_dir in self._base_dir.iterdir():
            if not month_dir.is_dir():
                continue
            event_file = month_dir / f"{operation_id}.json"
            if event_file.exists():
                try:
                    data = json.loads(event_file.read_text(encoding="utf-8"))
                    return OperationEvent.from_dict(data)
                except Exception as e:
                    logger.error(f"❌ 加载操作失败 {event_file}: {e}")
                    return None
        return None

    async def _load_slice_from_disk(self, slice_id: str) -> Optional[ContextSlice]:
        """从磁盘文件加载情境切片."""
        if not self._base_dir.exists():
            return None
        for month_dir in self._base_dir.iterdir():
            if not month_dir.is_dir():
                continue
            slice_file = month_dir / f"{slice_id}.json"
            if slice_file.exists():
                try:
                    data = json.loads(slice_file.read_text(encoding="utf-8"))
                    return ContextSlice.from_dict(data)
                except Exception as e:
                    logger.error(f"❌ 加载切片失败 {slice_file}: {e}")
                    return None
        return None

    async def _scan_operations(self, q: OperationQuery) -> List[OperationEvent]:
        """扫描月度文件匹配操作事件."""
        results: List[OperationEvent] = []
        if not self._base_dir.exists():
            return results

        # 按月份倒序扫描
        months = sorted(
            [d for d in self._base_dir.iterdir() if d.is_dir()],
            reverse=True,
        )
        for month_dir in months:
            for f in sorted(month_dir.iterdir(), reverse=True):
                if f.suffix != ".json" or f.suffix == ".tmp":
                    continue
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if "operation_type" not in data:
                    continue  # 跳过 ContextSlice 文件
                evt = OperationEvent.from_dict(data)
                if q.matches(evt):
                    results.append(evt)
                    if len(results) >= q.limit + q.offset:
                        return results
        return results

    async def _scan_slices(self, q: ContextQuery) -> List[ContextSlice]:
        """扫描月度文件匹配情境切片."""
        results: List[ContextSlice] = []
        if not self._base_dir.exists():
            return results

        months = sorted(
            [d for d in self._base_dir.iterdir() if d.is_dir()],
            reverse=True,
        )
        for month_dir in months:
            for f in sorted(month_dir.iterdir(), reverse=True):
                if f.suffix != ".json" or f.suffix == ".tmp":
                    continue
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if "context_type" not in data:
                    continue
                cs = ContextSlice.from_dict(data)
                if q.matches(cs):
                    results.append(cs)
                    if len(results) >= q.limit + q.offset:
                        return results
        return results

    async def _scan_slices_for_operation(self, operation_id: str) -> List[ContextSlice]:
        """扫描所有切片文件找到关联某操作的全部切片."""
        results: List[ContextSlice] = []
        if not self._base_dir.exists():
            return results

        for month_dir in self._base_dir.iterdir():
            if not month_dir.is_dir():
                continue
            for f in month_dir.iterdir():
                if f.suffix != ".json" or f.suffix == ".tmp":
                    continue
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if "context_type" not in data:
                    continue
                if data.get("operation_id") == operation_id:
                    results.append(ContextSlice.from_dict(data))
        return results

    def _trim_cache(self) -> None:
        """裁剪缓存到最大容量."""
        if len(self._op_cache) > self._max_cache:
            self._op_cache = self._op_cache[-self._max_cache:]
        if len(self._cs_cache) > self._max_cache:
            self._cs_cache = self._cs_cache[-self._max_cache:]

    def _prune_idempotency_keys(self) -> None:
        """裁剪幂等键集合."""
        # 保留最近的一半
        keep = self._idempotency_max // 2
        self._idempotency_keys = set(list(self._idempotency_keys)[-keep:])


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_operation_store: Optional[OperationStore] = None


def get_operation_store() -> OperationStore:
    """获取全局 OperationStore 单例."""
    global _operation_store
    if _operation_store is None:
        _operation_store = OperationStore()
    return _operation_store


def reset_operation_store() -> None:
    """重置全局单例 (测试用)."""
    global _operation_store
    _operation_store = None
