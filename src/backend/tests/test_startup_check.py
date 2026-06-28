# -*- coding: utf-8 -*-
"""Regression tests for startup check helpers."""

from __future__ import annotations

import pytest

import startup_check
from startup_check import _startup_check_response, run_startup_check
from startup_validator import CheckResult, CheckStatus, ValidationReport


def test_startup_check_response_preserves_not_run_and_completed_shapes():
    assert _startup_check_response(None) == {
        "status": "not_run",
        "message": "启动验证尚未执行",
    }
    assert _startup_check_response({"ok": True}) == {
        "status": "completed",
        "report": {"ok": True},
    }


@pytest.mark.asyncio
async def test_run_startup_check_caches_report_and_closes_validator(monkeypatch):
    report = ValidationReport()
    report.add(CheckResult(name="health", status=CheckStatus.PASS))
    closed = {"value": False}

    class FakeValidator:
        def __init__(self, base_url):
            self.base_url = base_url

        async def run_all(self):
            return report

        async def close(self):
            closed["value"] = True

    monkeypatch.setattr(startup_check, "StartupValidator", FakeValidator)
    monkeypatch.setattr(startup_check, "_last_report", None)

    result = await run_startup_check("http://example.test")

    assert result is report
    assert closed["value"] is True
    assert startup_check._last_report["total_checks"] == 1
    assert startup_check._last_report["passed"] == 1
