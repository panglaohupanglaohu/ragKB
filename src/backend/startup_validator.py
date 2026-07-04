# -*- coding: utf-8 -*-
"""
Startup Validator - 系统启动完整性验证器

提供:
1. 后端服务启动检查
2. API 端点可用性验证
3. 核心模块初始化状态确认
4. 结构化验证报告生成
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger("startup_validator")


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class CheckResult:
    """单个检查项结果"""
    name: str
    status: CheckStatus
    detail: str = ""
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """完整验证报告"""
    timestamp: float = field(default_factory=time.time)
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    skipped: int = 0
    checks: List[CheckResult] = field(default_factory=list)
    summary: str = ""

    def add(self, result: CheckResult):
        self.checks.append(result)
        self.total_checks += 1
        if result.status == CheckStatus.PASS:
            self.passed += 1
        elif result.status == CheckStatus.FAIL:
            self.failed += 1
        elif result.status == CheckStatus.WARN:
            self.warnings += 1
        elif result.status == CheckStatus.SKIP:
            self.skipped += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_checks": self.total_checks,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "skipped": self.skipped,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "detail": c.detail,
                    "duration_ms": round(c.duration_ms, 1),
                    "error": c.error,
                    "metadata": c.metadata,
                }
                for c in self.checks
            ],
            "summary": self.summary or self._generate_summary(),
        }

    def _generate_summary(self) -> str:
        if self.failed > 0:
            return f"❌ {self.failed}/{self.total_checks} checks FAILED"
        if self.warnings > 0:
            return f"⚠️ {self.warnings}/{self.total_checks} checks have warnings"
        return f"✅ All {self.total_checks} checks passed"


class StartupValidator:
    """系统启动验证器"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        # trust_env=False: 自检目标是本机服务，不应被环境代理(HTTP(S)_PROXY/ALL_PROXY)劫持。
        self.client = httpx.AsyncClient(timeout=10.0, trust_env=False)
        self._results: List[CheckResult] = []

    async def close(self):
        await self.client.aclose()

    async def _health_services(self) -> Dict[str, Any]:
        """Fetch public health services for auth-protected startup probes."""
        resp = await self.client.get(f"{self.base_url}/api/v1/health")
        if resp.status_code != 200:
            return {}
        data = resp.json()
        services = data.get("services", {})
        return services if isinstance(services, dict) else {}

    async def _protected_module_check(
        self,
        *,
        name: str,
        service_key: str,
        detail: str,
    ) -> CheckResult:
        services = await self._health_services()
        if services.get(service_key) is True:
            return CheckResult(
                name=name,
                status=CheckStatus.PASS,
                detail=detail,
                metadata={"auth_protected": True, "service": service_key},
            )
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            error=f"HTTP 401 and health service offline: {service_key}",
            metadata={"auth_protected": True, "services": services},
        )

    async def _check(
        self,
        name: str,
        check_fn: Callable,
        timeout: float = 10.0,
    ) -> CheckResult:
        """执行单个检查项"""
        start = time.time()
        try:
            result = await asyncio.wait_for(check_fn(), timeout=timeout)
            if isinstance(result, CheckResult):
                result.duration_ms = (time.time() - start) * 1000
                return result
            return CheckResult(
                name=name,
                status=CheckStatus.PASS if result else CheckStatus.FAIL,
                detail=str(result) if isinstance(result, str) else "",
                duration_ms=(time.time() - start) * 1000,
            )
        except asyncio.TimeoutError:
            return CheckResult(
                name=name,
                status=CheckStatus.FAIL,
                error=f"Timeout after {timeout}s",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return CheckResult(
                name=name,
                status=CheckStatus.FAIL,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def run_all(self) -> ValidationReport:
        """运行所有验证检查"""
        report = ValidationReport()

        # Run all checks in parallel for faster startup
        results = await asyncio.gather(
            self._check_health(),
            self._check_info(),
            self._check_api_endpoints(),
            self._check_evolution_engine(),
            self._check_agent_config(),
            self._check_bridge_chat(),
            self._check_auth(),
            self._check_frontend_pages(),
            return_exceptions=True,
        )

        for r in results:
            if isinstance(r, Exception):
                report.add(CheckResult(
                    name="unknown",
                    status=CheckStatus.FAIL,
                    error=str(r),
                ))
            elif isinstance(r, CheckResult):
                report.add(r)

        return report

    async def _check_health(self) -> CheckResult:
        """检查健康端点"""
        async def check():
            resp = await self.client.get(f"{self.base_url}/api/v1/health")
            data = resp.json()
            if resp.status_code != 200:
                return CheckResult(
                    name="health_endpoint",
                    status=CheckStatus.FAIL,
                    error=f"HTTP {resp.status_code}",
                )
            services = data.get("services", {})
            offline = [k for k, v in services.items() if not v]
            if offline:
                return CheckResult(
                    name="health_endpoint",
                    status=CheckStatus.WARN,
                    detail=f"Services offline: {', '.join(offline)}",
                    metadata={"services": services},
                )
            return CheckResult(
                name="health_endpoint",
                status=CheckStatus.PASS,
                detail=f"All services online: {list(services.keys())}",
                metadata={"services": services},
            )
        return await self._check("health_endpoint", check)

    async def _check_info(self) -> CheckResult:
        """检查系统信息端点"""
        async def check():
            resp = await self.client.get(f"{self.base_url}/api/v1/info")
            if resp.status_code != 200:
                return CheckResult(
                    name="info_endpoint",
                    status=CheckStatus.FAIL,
                    error=f"HTTP {resp.status_code}",
                )
            data = resp.json()
            required_keys = ["name", "version", "capabilities", "endpoints"]
            missing = [k for k in required_keys if k not in data]
            if missing:
                return CheckResult(
                    name="info_endpoint",
                    status=CheckStatus.FAIL,
                    error=f"Missing keys: {missing}",
                )
            return CheckResult(
                name="info_endpoint",
                status=CheckStatus.PASS,
                detail=f"System: {data.get('name')} v{data.get('version')}",
                metadata=data,
            )
        return await self._check("info_endpoint", check)

    async def _check_api_endpoints(self) -> CheckResult:
        """检查关键 API 端点"""
        endpoints = [
            ("agent_teams_overview", "/api/v1/agent-teams/overview"),
            ("evolution_status", "/api/v1/agent-teams/evolution/status"),
            ("evolution_summary", "/api/v1/agent-teams/evolution/summary"),
            ("agent_config_teams", "/api/v1/agent-config/teams"),
            ("agent_config_agents", "/api/v1/agent-config/agents"),
        ]

        async def check():
            results = []
            for name, path in endpoints:
                try:
                    resp = await self.client.get(f"{self.base_url}{path}")
                    if resp.status_code in (200, 404):
                        results.append(f"{name}: HTTP {resp.status_code}")
                    elif resp.status_code == 401:
                        results.append(f"{name}: HTTP 401 (auth protected)")
                    else:
                        results.append(f"{name}: HTTP {resp.status_code} (unexpected)")
                except Exception as e:
                    results.append(f"{name}: ERROR - {str(e)[:50]}")

            failed = [r for r in results if "ERROR" in r or "unexpected" in r]
            if failed:
                return CheckResult(
                    name="api_endpoints",
                    status=CheckStatus.WARN if len(failed) < len(endpoints) else CheckStatus.FAIL,
                    detail="; ".join(results),
                    metadata={"endpoints_checked": len(endpoints), "failed": len(failed)},
                )
            return CheckResult(
                name="api_endpoints",
                status=CheckStatus.PASS,
                detail=f"All {len(endpoints)} endpoints reachable",
                metadata={"endpoints": [e[0] for e in endpoints]},
            )
        return await self._check("api_endpoints", check)

    async def _check_evolution_engine(self) -> CheckResult:
        """检查演进引擎状态"""
        async def check():
            resp = await self.client.get(
                f"{self.base_url}/api/v1/agent-teams/evolution/status"
            )
            if resp.status_code == 401:
                return await self._protected_module_check(
                    name="evolution_engine",
                    service_key="evolution",
                    detail="Evolution engine route is auth-protected and service is online",
                )
            if resp.status_code == 404:
                return CheckResult(
                    name="evolution_engine",
                    status=CheckStatus.FAIL,
                    error="Evolution engine not registered (HTTP 404)",
                )
            data = resp.json()
            if data.get("status") == "initialized":
                return CheckResult(
                    name="evolution_engine",
                    status=CheckStatus.PASS,
                    detail=f"Engine initialized with {data.get('audit_rules_count', 0)} rules",
                    metadata=data,
                )
            return CheckResult(
                name="evolution_engine",
                status=CheckStatus.WARN,
                detail=f"Engine status: {data.get('status', 'unknown')}",
                metadata=data,
            )
        return await self._check("evolution_engine", check)

    async def _check_agent_config(self) -> CheckResult:
        """检查 Agent 配置 API"""
        async def check():
            resp = await self.client.get(f"{self.base_url}/api/v1/agent-config/teams")
            if resp.status_code == 401:
                return await self._protected_module_check(
                    name="agent_config",
                    service_key="agent_config",
                    detail="Agent config route is auth-protected and service is online",
                )
            if resp.status_code != 200:
                return CheckResult(
                    name="agent_config",
                    status=CheckStatus.FAIL,
                    error=f"HTTP {resp.status_code}",
                )
            data = resp.json()
            teams = data if isinstance(data, list) else data.get("teams", [])
            return CheckResult(
                name="agent_config",
                status=CheckStatus.PASS,
                detail=f"{len(teams)} teams configured",
                metadata={"teams_count": len(teams)},
            )
        return await self._check("agent_config", check)

    async def _check_bridge_chat(self) -> CheckResult:
        """检查聊天通道"""
        async def check():
            resp = await self.client.get(f"{self.base_url}/api/v1/bridge-chat/status")
            if resp.status_code == 401:
                return await self._protected_module_check(
                    name="bridge_chat",
                    service_key="bridge_chat",
                    detail="Bridge chat route is auth-protected and service is online",
                )
            if resp.status_code != 200:
                return CheckResult(
                    name="bridge_chat",
                    status=CheckStatus.FAIL,
                    error=f"HTTP {resp.status_code}",
                )
            data = resp.json()
            if data:
                return CheckResult(
                    name="bridge_chat",
                    status=CheckStatus.PASS,
                    detail="Chat channel status endpoint responsive",
                    metadata=data,
                )
            return CheckResult(
                name="bridge_chat",
                status=CheckStatus.WARN,
                detail="Chat channel responded but no reply content",
                metadata=data,
            )
        return await self._check("bridge_chat", check)

    async def _check_auth(self) -> CheckResult:
        """检查认证系统"""
        async def check():
            # 检查未认证状态
            resp = await self.client.get(
                f"{self.base_url}/api/v1/auth/me",
                headers={"Authorization": ""},
            )
            if resp.status_code != 200:
                return CheckResult(
                    name="auth_system",
                    status=CheckStatus.FAIL,
                    error=f"Auth me endpoint: HTTP {resp.status_code}",
                )
            data = resp.json()
            if data.get("authenticated") is False:
                return CheckResult(
                    name="auth_system",
                    status=CheckStatus.PASS,
                    detail="Auth system working (guest mode)",
                    metadata=data,
                )
            return CheckResult(
                name="auth_system",
                status=CheckStatus.WARN,
                detail=f"Unexpected auth state: {data}",
                metadata=data,
            )
        return await self._check("auth_system", check)

    async def _check_frontend_pages(self) -> CheckResult:
        """检查前端页面可访问性"""
        pages = [
            ("index", "/"),
            ("login", "/login.html"),
            ("plaza", "/plaza.html"),
            ("system_evolution", "/system-evolution.html"),
            ("agent_team_config", "/agent-team-config.html"),
        ]

        async def check():
            results = []
            for name, path in pages:
                try:
                    resp = await self.client.get(f"{self.base_url}{path}")
                    if resp.status_code == 200:
                        content_type = resp.headers.get("content-type", "")
                        if "text/html" in content_type or "text/plain" in content_type:
                            results.append(f"{name}: OK")
                        else:
                            results.append(f"{name}: HTTP 200 but content-type={content_type}")
                    else:
                        results.append(f"{name}: HTTP {resp.status_code}")
                except Exception as e:
                    results.append(f"{name}: ERROR - {str(e)[:50]}")

            failed = [r for r in results if "ERROR" in r or "HTTP 4" in r or "HTTP 5" in r]
            if failed:
                return CheckResult(
                    name="frontend_pages",
                    status=CheckStatus.WARN if len(failed) < len(pages) else CheckStatus.FAIL,
                    detail="; ".join(results),
                    metadata={"pages_checked": len(pages), "failed": len(failed)},
                )
            return CheckResult(
                name="frontend_pages",
                status=CheckStatus.PASS,
                detail=f"All {len(pages)} frontend pages accessible",
                metadata={"pages": [p[0] for p in pages]},
            )
        return await self._check("frontend_pages", check)


# ── 便捷函数 ──

async def validate_startup(
    base_url: str = "http://localhost:8080",
    verbose: bool = True,
) -> ValidationReport:
    """执行完整的启动验证"""
    validator = StartupValidator(base_url)
    try:
        report = await validator.run_all()
        if verbose:
            _print_report(report)
        return report
    finally:
        await validator.close()


def _print_report(report: ValidationReport):
    """打印验证报告到控制台"""
    print("\n" + "=" * 60)
    print("  AgentsGroup2026 - 启动验证报告")
    print("=" * 60)
    print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}")
    print(f"  总计: {report.total_checks} 项检查")
    print(f"  ✅ 通过: {report.passed}")
    print(f"  ❌ 失败: {report.failed}")
    print(f"  ⚠️  警告: {report.warnings}")
    print(f"  ⏭️  跳过: {report.skipped}")
    print("-" * 60)

    for check in report.checks:
        icon = {
            CheckStatus.PASS: "✅",
            CheckStatus.FAIL: "❌",
            CheckStatus.WARN: "⚠️",
            CheckStatus.SKIP: "⏭️",
        }.get(check.status, "❓")

        print(f"  {icon} {check.name}")
        if check.detail:
            print(f"     {check.detail}")
        if check.error:
            print(f"     Error: {check.error}")
        if check.duration_ms > 0:
            print(f"     Duration: {check.duration_ms:.0f}ms")

    print("=" * 60)
    print(f"  {report.summary}")
    print("=" * 60)


__all__ = [
    "CheckStatus", "CheckResult", "ValidationReport",
    "StartupValidator", "validate_startup",
]
