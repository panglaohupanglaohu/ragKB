# -*- coding: utf-8 -*-
"""
Startup Check Middleware - 启动时自动执行验证

在 FastAPI 应用启动后自动运行验证检查，
将结果记录到日志和 /api/v1/startup-check 端点。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter

from startup_validator import StartupValidator, ValidationReport

logger = logging.getLogger("startup_check")

# 全局验证报告
_last_report: Optional[Dict[str, Any]] = None
_check_router = APIRouter(prefix="/api/v1", tags=["Startup Check"])


@_check_router.get("/startup-check")
async def get_startup_check():
    """获取最近一次启动验证结果"""
    return _startup_check_response(_last_report)


async def run_startup_check(base_url: str = "http://localhost:8080"):
    """在应用启动后运行验证"""
    global _last_report

    logger.info("🔍 执行启动验证...")
    validator = StartupValidator(base_url)
    try:
        report = await validator.run_all()
        _last_report = report.to_dict()

        _log_validation_report(report)

        return report
    finally:
        await validator.close()


def get_startup_check_router() -> APIRouter:
    """获取启动检查路由"""
    return _check_router


def _startup_check_response(report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if report is None:
        return {
            "status": "not_run",
            "message": "启动验证尚未执行",
        }
    return {
        "status": "completed",
        "report": report,
    }


def _log_validation_report(report: ValidationReport) -> None:
    if report.failed > 0:
        logger.warning(
            f"⚠️ 启动验证完成: {report.failed}/{report.total_checks} 项失败"
        )
        for check in report.checks:
            if check.status.value == "fail":
                logger.warning(f"  ❌ {check.name}: {check.error}")
        return

    if report.warnings > 0:
        logger.info(
            f"⚠️ 启动验证完成: {report.warnings} 项警告"
        )
        return

    logger.info(f"✅ 启动验证通过: 全部 {report.total_checks} 项检查通过")


__all__ = ["run_startup_check", "get_startup_check_router", "get_startup_check"]
