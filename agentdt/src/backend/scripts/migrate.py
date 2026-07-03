# -*- coding: utf-8 -*-
"""
Schema Migration Script — 部署 Job 自动执行的幂等迁移脚本

用法:
    python scripts/migrate.py                     # 迁移到 latest
    python scripts/migrate.py --target v2         # 迁移到指定版本
    python scripts/migrate.py --dry-run           # 预览变更
    python scripts/migrate.py --status            # 查看当前版本
    python scripts/migrate.py --rollback v1       # 回滚到指定版本

特性:
    - 幂等: 重复执行安全，已应用的迁移自动跳过
    - 版本追踪: 通过 .schema_version 文件记录当前版本
    - 回滚支持: 每个迁移需提供 forward/backward 函数
    - 部署友好: 退出码 0=成功, 1=需要人工介入, 2=预览模式无变更
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("schema_migrate")

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STORAGE_DIR = PROJECT_ROOT / "storage"
VERSION_FILE = STORAGE_DIR / ".schema_version"
BACKUP_DIR = STORAGE_DIR / "_migration_backups"

# All known data directories that migrations may touch
DATA_DIRS = {
    "discussions": STORAGE_DIR / "discussions",
    "tasks": STORAGE_DIR / "tasks",
    "teams": STORAGE_DIR / "teams",
    "sessions": STORAGE_DIR / "sessions",
}


# ── Data Types ────────────────────────────────────────────────────────────────

@dataclass
class MigrationStep:
    """单个迁移步骤."""
    version: str
    description: str
    forward: Callable[[], bool]       # 返回 True 表示成功
    backward: Callable[[], bool]      # 回滚函数


@dataclass
class MigrationReport:
    """迁移执行报告."""
    started_at: str = ""
    finished_at: str = ""
    from_version: str = "unknown"
    to_version: str = "unknown"
    steps_executed: List[str] = field(default_factory=list)
    steps_skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "steps_executed": self.steps_executed,
            "steps_skipped": self.steps_skipped,
            "errors": self.errors,
            "dry_run": self.dry_run,
            "success": self.ok,
        }


# ── Version Management ───────────────────────────────────────────────────────

def _read_current_version() -> str:
    """读取当前 schema 版本."""
    if not VERSION_FILE.exists():
        return "v0"
    try:
        data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
        return data.get("version", "v0")
    except Exception:
        return "v0"


def _write_version(version: str):
    """写入当前 schema 版本."""
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(
        json.dumps({
            "version": version,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _backup_file(path: Path) -> Path:
    """备份文件到备份目录."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    backup_path = BACKUP_DIR / f"{path.name}.{ts}.bak"
    backup_path.write_bytes(path.read_bytes())
    logger.debug(f"  📦 已备份: {path.name} → {backup_path.name}")
    return backup_path


# ── Migration Definitions ────────────────────────────────────────────────────

def _migrate_v0_to_v1() -> bool:
    """v0 → v1: 初始化存储目录结构，确保所有数据目录存在."""
    logger.info("  执行 v0→v1: 初始化存储目录结构...")
    for name, dir_path in DATA_DIRS.items():
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"    已确保目录: {dir_path}")
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return True


def _rollback_v1_to_v0() -> bool:
    """v1 → v0: 清理空目录（不含数据的）."""
    logger.info("  回滚 v1→v0: 清理空目录...")
    for name, dir_path in reversed(list(DATA_DIRS.items())):
        if dir_path.exists() and not any(dir_path.iterdir()):
            dir_path.rmdir()
            logger.debug(f"    已删除空目录: {dir_path}")
    return True


def _migrate_v1_to_v2() -> bool:
    """v1 → v2: 在 TeamStore JSON 中添加 version 字段."""
    logger.info("  执行 v1→v2: 更新 TeamStore 格式...")
    teams_dir = DATA_DIRS["teams"]
    if not teams_dir.exists():
        logger.info("    无团队数据，跳过")
        return True

    updated = 0
    for team_file in teams_dir.glob("*.json"):
        try:
            data = json.loads(team_file.read_text(encoding="utf-8"))
            if "schema_version" not in data:
                _backup_file(team_file)
                data["schema_version"] = "v2"
                team_file.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                updated += 1
        except Exception as e:
            logger.error(f"    处理 {team_file.name} 失败: {e}")
            return False
    logger.info(f"    已更新 {updated} 个团队文件")
    return True


def _rollback_v2_to_v1() -> bool:
    """v2 → v1: 移除 schema_version 字段."""
    logger.info("  回滚 v2→v1: 移除 schema_version 字段...")
    teams_dir = DATA_DIRS["teams"]
    if not teams_dir.exists():
        return True

    updated = 0
    for team_file in teams_dir.glob("*.json"):
        try:
            data = json.loads(team_file.read_text(encoding="utf-8"))
            if "schema_version" in data:
                _backup_file(team_file)
                del data["schema_version"]
                team_file.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                updated += 1
        except Exception as e:
            logger.error(f"    处理 {team_file.name} 失败: {e}")
            return False
    logger.info(f"    已回滚 {updated} 个团队文件")
    return True


def _migrate_v2_to_v3() -> bool:
    """v2 → v3: 为 TaskStore 任务添加 created_at / updated_at 时间戳."""
    logger.info("  执行 v2→v3: 添加任务时间戳...")
    tasks_dir = DATA_DIRS["tasks"]
    if not tasks_dir.exists():
        logger.info("    无任务数据，跳过")
        return True

    now = datetime.now(timezone.utc).isoformat()
    updated = 0
    for task_file in tasks_dir.glob("*.json"):
        try:
            data = json.loads(task_file.read_text(encoding="utf-8"))
            changed = False
            if "created_at" not in data:
                data["created_at"] = now
                changed = True
            if "updated_at" not in data:
                data["updated_at"] = now
                changed = True
            if changed:
                _backup_file(task_file)
                task_file.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                updated += 1
        except Exception as e:
            logger.error(f"    处理 {task_file.name} 失败: {e}")
            return False
    logger.info(f"    已更新 {updated} 个任务文件")
    return True


def _rollback_v3_to_v2() -> bool:
    """v3 → v2: 移除 created_at / updated_at 字段."""
    logger.info("  回滚 v3→v2: 移除时间戳字段...")
    tasks_dir = DATA_DIRS["tasks"]
    if not tasks_dir.exists():
        return True

    updated = 0
    for task_file in tasks_dir.glob("*.json"):
        try:
            data = json.loads(task_file.read_text(encoding="utf-8"))
            changed = False
            for key in ("created_at", "updated_at"):
                if key in data:
                    del data[key]
                    changed = True
            if changed:
                _backup_file(task_file)
                task_file.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                updated += 1
        except Exception as e:
            logger.error(f"    处理 {task_file.name} 失败: {e}")
            return False
    logger.info(f"    已回滚 {updated} 个任务文件")
    return True


# ── Migration Registry ────────────────────────────────────────────────────────

MIGRATIONS: List[MigrationStep] = [
    MigrationStep(
        version="v1",
        description="初始化存储目录结构",
        forward=_migrate_v0_to_v1,
        backward=_rollback_v1_to_v0,
    ),
    MigrationStep(
        version="v2",
        description="TeamStore 添加 schema_version 字段",
        forward=_migrate_v1_to_v2,
        backward=_rollback_v2_to_v1,
    ),
    MigrationStep(
        version="v3",
        description="TaskStore 添加 created_at/updated_at 时间戳",
        forward=_migrate_v2_to_v3,
        backward=_rollback_v3_to_v2,
    ),
]

LATEST_VERSION = MIGRATIONS[-1].version


# ── Core Engine ───────────────────────────────────────────────────────────────

def _version_index(version: str) -> int:
    """将 vN 转为数字索引."""
    try:
        return int(version.lstrip("v"))
    except ValueError:
        return 0


def _get_pending_migrations(
    from_version: str,
    to_version: Optional[str] = None,
) -> List[MigrationStep]:
    """获取待执行的迁移列表."""
    from_idx = _version_index(from_version)
    to_ver = to_version or LATEST_VERSION
    to_idx = _version_index(to_ver)

    if to_idx <= from_idx:
        return []

    return [
        m for m in MIGRATIONS
        if from_idx < _version_index(m.version) <= to_idx
    ]


def _get_rollback_migrations(
    from_version: str,
    to_version: str,
) -> List[MigrationStep]:
    """获取待回滚的迁移列表（逆序）."""
    from_idx = _version_index(from_version)
    to_idx = _version_index(to_version)

    if to_idx >= from_idx:
        return []

    return [
        m for m in reversed(MIGRATIONS)
        if to_idx < _version_index(m.version) <= from_idx
    ]


def run_migrations(
    target: Optional[str] = None,
    dry_run: bool = False,
) -> MigrationReport:
    """执行 schema 迁移（幂等）."""
    report = MigrationReport(dry_run=dry_run)
    report.started_at = datetime.now(timezone.utc).isoformat()
    report.from_version = _read_current_version()

    target = target or LATEST_VERSION
    report.to_version = target

    if report.from_version == target:
        logger.info(f"✅ 已是目标版本 {target}，无需迁移")
        report.finished_at = datetime.now(timezone.utc).isoformat()
        return report

    pending = _get_pending_migrations(report.from_version, target)

    if not pending:
        logger.warning(f"⚠️ 无从 {report.from_version} 到 {target} 的迁移路径")
        report.errors.append(f"No migration path from {report.from_version} to {target}")
        report.finished_at = datetime.now(timezone.utc).isoformat()
        return report

    logger.info(f"🔧 从 {report.from_version} 迁移到 {target} ({len(pending)} 步骤)")
    if dry_run:
        logger.info("🏴 预览模式: 不会实际执行任何变更")

    for step in pending:
        logger.info(f"  → {step.version}: {step.description}")
        if dry_run:
            report.steps_executed.append(f"[DRY-RUN] {step.version}: {step.description}")
            continue

        try:
            if step.forward():
                report.steps_executed.append(step.version)
                _write_version(step.version)
                logger.info(f"    ✅ {step.version} 完成")
            else:
                report.errors.append(f"{step.version}: forward() returned False")
                logger.error(f"    ❌ {step.version} 失败")
                break
        except Exception as e:
            report.errors.append(f"{step.version}: {e}")
            logger.exception(f"    ❌ {step.version} 异常")
            break

    report.finished_at = datetime.now(timezone.utc).isoformat()

    if report.ok and not dry_run:
        logger.info(f"🎉 迁移完成: {report.from_version} → {_read_current_version()}")
    elif report.errors:
        logger.error(f"💥 迁移失败: {len(report.errors)} 个错误")

    return report


def rollback_migrations(
    target: str,
    dry_run: bool = False,
) -> MigrationReport:
    """回滚 schema 到指定版本."""
    report = MigrationReport(dry_run=dry_run)
    report.started_at = datetime.now(timezone.utc).isoformat()
    report.from_version = _read_current_version()
    report.to_version = target

    if report.from_version == target:
        logger.info(f"✅ 已是目标版本 {target}，无需回滚")
        report.finished_at = datetime.now(timezone.utc).isoformat()
        return report

    steps = _get_rollback_migrations(report.from_version, target)

    if not steps:
        logger.warning(f"⚠️ 无从 {report.from_version} 回滚到 {target} 的路径")
        report.errors.append(f"No rollback path from {report.from_version} to {target}")
        report.finished_at = datetime.now(timezone.utc).isoformat()
        return report

    logger.info(f"⏪ 从 {report.from_version} 回滚到 {target} ({len(steps)} 步骤)")
    if dry_run:
        logger.info("🏴 预览模式: 不会实际执行任何变更")

    for step in steps:
        prev_version = f"v{_version_index(step.version) - 1}"
        logger.info(f"  ← {step.version}→{prev_version}: {step.description}")
        if dry_run:
            report.steps_executed.append(f"[DRY-RUN] rollback {step.version}")
            continue

        try:
            if step.backward():
                report.steps_executed.append(f"rollback {step.version}")
                _write_version(prev_version)
                logger.info(f"    ✅ 回滚 {step.version} 完成")
            else:
                report.errors.append(f"rollback {step.version}: backward() returned False")
                logger.error(f"    ❌ 回滚 {step.version} 失败")
                break
        except Exception as e:
            report.errors.append(f"rollback {step.version}: {e}")
            logger.exception(f"    ❌ 回滚 {step.version} 异常")
            break

    report.finished_at = datetime.now(timezone.utc).isoformat()
    return report


def show_status() -> Dict[str, Any]:
    """显示当前 schema 状态."""
    current = _read_current_version()
    applied = [m.version for m in MIGRATIONS if _version_index(m.version) <= _version_index(current)]
    pending = [m.version for m in MIGRATIONS if _version_index(m.version) > _version_index(current)]

    return {
        "current_version": current,
        "latest_version": LATEST_VERSION,
        "migrations_applied": applied,
        "migrations_pending": pending,
        "is_up_to_date": len(pending) == 0,
        "version_file": str(VERSION_FILE),
        "storage_dir": str(STORAGE_DIR),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AgentsGroup2026 Schema Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 迁移到最新版本
  %(prog)s --target v2        # 迁移到 v2
  %(prog)s --dry-run          # 预览迁移
  %(prog)s --status           # 查看当前版本
  %(prog)s --rollback v1      # 回滚到 v1
        """,
    )
    parser.add_argument(
        "--target", "-t",
        help="目标版本 (默认: latest)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="预览模式，不实际执行变更",
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="显示当前 schema 状态",
    )
    parser.add_argument(
        "--rollback", "-r",
        metavar="VERSION",
        help="回滚到指定版本",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果",
    )

    args = parser.parse_args()

    if args.status:
        status = show_status()
        if args.json:
            print(json.dumps(status, ensure_ascii=False, indent=2))
        else:
            print(f"📊 Schema 状态:")
            print(f"   当前版本: {status['current_version']}")
            print(f"   最新版本: {status['latest_version']}")
            print(f"   已应用:   {', '.join(status['migrations_applied']) or '(无)'}")
            print(f"   待应用:   {', '.join(status['migrations_pending']) or '(无)'}")
            print(f"   是否最新: {'✅ 是' if status['is_up_to_date'] else '❌ 否'}")
        return 0

    if args.rollback:
        report = rollback_migrations(args.rollback, dry_run=args.dry_run)
    else:
        report = run_migrations(args.target, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    elif report.errors:
        print(f"\n❌ 失败: {len(report.errors)} 个错误", file=sys.stderr)
        for err in report.errors:
            print(f"   - {err}", file=sys.stderr)

    if report.ok:
        return 0
    elif report.dry_run:
        return 2
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
