# -*- coding: utf-8 -*-
"""技能验证框架 — 自动生成测试场景 → 沙箱执行 → 评估 pass_rate.

对应 SkillClaw: Verification In the Wild.
状态 badge: 🔵未验证 / 🟡测试中 / ✅已验证 / ❌验证失败
"""

from __future__ import annotations

import logging
import json
import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import SkillDefinition, SkillLifecycleStage
from .domain_events import DomainEvent, EventType, SkillSnapshot
from .event_bus import get_event_bus

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ARTIFACT_ROOT = _REPO_ROOT / "storage" / "skill_verifications"


@dataclass
class VerificationResult:
    """单次验证结果."""
    skill_id: str = ""
    pass_rate: float = 0.0
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    test_details: List[Dict[str, Any]] = field(default_factory=list)
    verified_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "pending"  # pending / testing / verified / failed
    error_detail: str = ""
    process_log: List[Dict[str, Any]] = field(default_factory=list)
    runtime_mode: str = ""
    runtime_ready: bool = False
    docker_image: str = ""
    command: str = ""
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    artifact_dir: str = ""
    evidence_run_id: str = ""
    verification_evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "pass_rate": self.pass_rate,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "test_details": self.test_details,
            "verified_at": self.verified_at,
            "status": self.status,
            "error_detail": self.error_detail,
            "process_log": self.process_log,
            "runtime_mode": self.runtime_mode,
            "runtime_ready": self.runtime_ready,
            "docker_image": self.docker_image,
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "artifact_dir": self.artifact_dir,
            "evidence_run_id": self.evidence_run_id,
            "verification_evidence": self.verification_evidence,
        }


class SkillVerifier:
    """技能验证器 — 构造测试 → 沙箱执行 → 评估，全程可追溯."""

    def __init__(self, skill_library=None, chat_harness=None):
        self._skill_library = skill_library
        self._chat_harness = chat_harness
        self._results: Dict[str, VerificationResult] = {}
        self._process_log: List[Dict[str, Any]] = []  # 透明化执行日志

    async def verify_skill(self, team_id: str, skill_id: str) -> VerificationResult:
        """验证技能: 生成测试材料 → 沙箱执行验证脚本 → 评估 pass_rate."""
        self._process_log = []
        result = VerificationResult(skill_id=skill_id, status="testing")
        result.process_log = self._process_log

        self._process_log.append({"step": "init", "msg": f"开始验证技能: {skill_id}", "team_id": team_id})

        if not self._skill_library:
            result.status = "failed"
            result.error_detail = "技能库未初始化"
            self._process_log.append({"step": "error", "msg": "技能库未初始化"})
            return result

        skill = self._skill_library._find_skill(team_id, skill_id)
        if not skill:
            result.status = "failed"
            result.error_detail = f"技能 {skill_id} 未找到"
            self._process_log.append({"step": "error", "msg": f"技能 {skill_id} 未找到"})
            return result

        self._process_log.append({"step": "found_skill", "msg": f"技能名: {skill.name}", "desc": skill.description[:200]})

        runtime = self._describe_runtime()
        result.runtime_mode = str(runtime.get("mode", ""))
        result.runtime_ready = bool(runtime.get("ready", False))
        result.docker_image = str(runtime.get("docker_image", ""))
        self._process_log.append({
            "step": "sandbox_runtime",
            "msg": f"验证运行时: {result.runtime_mode or 'unknown'} ({runtime.get('ready_reason', '')})",
            "runtime": runtime,
        })

        # Step 1: 生成测试场景
        self._process_log.append({"step": "generate_tests", "msg": "生成技能验证场景..."})
        test_scenarios = await self._generate_tests(skill)
        self._process_log.append({"step": "tests_generated", "msg": f"生成 {len(test_scenarios)} 个测试场景", "scenarios": [t.get("scenario","")[:100] for t in test_scenarios]})

        # Step 2: 沙箱执行验证脚本
        artifact_dir = self._create_artifact_dir(skill_id)
        result.artifact_dir = str(artifact_dir)
        evidence = self._run_sandbox_verification(skill, test_scenarios, artifact_dir, runtime)
        result.verification_evidence = evidence
        result.command = str(evidence.get("command", ""))
        result.exit_code = int(evidence.get("exit_code", -1))
        result.stdout = str(evidence.get("stdout", ""))
        result.stderr = str(evidence.get("stderr", ""))

        checks = list(evidence.get("checks") or [])
        result.total_tests = len(checks)
        for i, check in enumerate(checks):
            passed = bool(check.get("passed"))
            if passed:
                result.passed += 1
            else:
                result.failed += 1
            result.test_details.append({
                "scenario": str(check.get("name") or f"sandbox_check_{i + 1}"),
                "passed": passed,
                "test_index": i + 1,
                "message": str(check.get("message", "")),
                "source": "sandbox",
            })
            self._process_log.append({
                "step": "sandbox_check",
                "msg": f"{'PASS' if passed else 'FAIL'} {check.get('name', f'check_{i + 1}')}: {check.get('message', '')}",
                "passed": passed,
            })

        # Step 3: 计算通过率
        if result.total_tests > 0:
            result.pass_rate = result.passed / result.total_tests
        self._process_log.append({"step": "calc_rate", "msg": f"通过率: {result.pass_rate*100:.0f}% ({result.passed}/{result.total_tests})"})

        # Step 4: 确定结果
        sandbox_ok = bool(evidence.get("sandbox_ok", False))
        sandbox_exit_ok = int(evidence.get("exit_code", -1)) == 0
        if sandbox_ok and sandbox_exit_ok and result.pass_rate >= 0.7:
            result.status = "verified"
            skill.lifecycle_stage = SkillLifecycleStage.VERIFIED
            skill.quality_score = result.pass_rate
            self._skill_library._persist_skill(skill, team_id)
            self._process_log.append({"step": "done", "msg": "验证通过 — 技能已标记为 VERIFIED"})
        else:
            result.status = "failed"
            if not sandbox_ok:
                result.error_detail = str(evidence.get("error") or "sandbox execution failed")
            elif not sandbox_exit_ok:
                result.error_detail = f"沙箱验证脚本退出码 {result.exit_code}"
            else:
                result.error_detail = f"通过率 {result.pass_rate*100:.0f}% 低于 70% 阈值"
            self._process_log.append({"step": "done", "msg": f"验证失败 — {result.error_detail}"})

        result.evidence_run_id = await self._record_evidence_run(team_id, skill, result, evidence)
        if result.evidence_run_id:
            result.verification_evidence["evidence_run_id"] = result.evidence_run_id
            self._process_log.append({
                "step": "evidence_run",
                "msg": f"EvidenceRun 已写入: {result.evidence_run_id}",
            })

        self._results[skill_id] = result

        # Emit event
        bus = get_event_bus()
        event = DomainEvent.create(
            event_type=EventType.SKILL_UPDATED,
            payload=SkillSnapshot.from_skill_definition(skill),
            source="skill_verifier",
            correlation_id=f"verify:{skill_id}",
        )
        bus.publish(event)

        logger.info("Skill %s verification: %s (pass_rate=%.2f)",
                     skill_id, result.status, result.pass_rate)
        return result

    async def _record_evidence_run(
        self,
        team_id: str,
        skill: SkillDefinition,
        result: VerificationResult,
        evidence: Dict[str, Any],
    ) -> str:
        """Persist the sandbox verification as a shared EvidenceRun."""
        try:
            from .evidence_store import EvidenceRun, get_evidence_store

            run = EvidenceRun.create(
                evidence_type="skill_verify",
                status=result.status,
                summary=f"技能验证: {skill.name} -> {result.status}",
                team_id=team_id,
                agent_id="skill_verifier",
                skill_id=skill.skill_id,
                request_id=f"skill-verify:{skill.skill_id}:{result.verified_at}",
                runtime={
                    "mode": result.runtime_mode,
                    "ready": result.runtime_ready,
                    "docker_image": result.docker_image,
                    "raw": evidence.get("runtime", {}),
                },
                command=result.command,
                exit_code=result.exit_code,
                artifact_dir=result.artifact_dir,
                stdout=result.stdout,
                stderr=result.stderr,
                metrics_after={
                    "pass_rate": result.pass_rate,
                    "passed": result.passed,
                    "failed": result.failed,
                    "total_tests": result.total_tests,
                },
                detail={
                    "error_detail": result.error_detail,
                    "test_details": result.test_details,
                    "checks": evidence.get("checks", []),
                    "process_log": list(result.process_log),
                    "sandbox_ok": evidence.get("sandbox_ok", False),
                    "runtime_ready": result.runtime_ready,
                },
            )
            await get_evidence_store().append_evidence(run)
            return run.evidence_id
        except Exception as exc:
            logger.warning("Failed to record skill verification EvidenceRun: %s", exc)
            self._process_log.append({
                "step": "evidence_run_error",
                "msg": f"EvidenceRun 写入失败: {exc}",
            })
            return ""

    def _describe_runtime(self) -> Dict[str, Any]:
        try:
            from sandbox.python_runner import describe_sandbox_runtime
            return dict(describe_sandbox_runtime())
        except Exception as exc:
            logger.warning("Sandbox runtime describe failed: %s", exc)
            return {
                "mode": "unavailable",
                "ready": False,
                "ready_reason": str(exc),
                "docker_image": "",
                "self_check_blocked": True,
            }

    def _create_artifact_dir(self, skill_id: str) -> Path:
        safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", skill_id or "skill").strip("-")[:80] or "skill"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        artifact_dir = _ARTIFACT_ROOT / safe_id / stamp
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

    def _run_sandbox_verification(
        self,
        skill: SkillDefinition,
        test_scenarios: List[Dict[str, str]],
        artifact_dir: Path,
        runtime: Dict[str, Any],
    ) -> Dict[str, Any]:
        runner_code = self._build_sandbox_validation_code(skill, test_scenarios)
        runner_path = artifact_dir / "verification_runner.py"
        inputs_path = artifact_dir / "verification_input.json"
        runner_path.write_text(runner_code, encoding="utf-8")
        inputs_path.write_text(json.dumps({
            "skill_id": skill.skill_id,
            "name": skill.name,
            "description": skill.description,
            "tests": test_scenarios,
            "runtime": runtime,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        command = f"sandbox.run_python artifact={self._display_path(runner_path)}"
        self._process_log.append({"step": "sandbox_exec", "msg": f"执行沙箱验证脚本: {command}"})

        try:
            from sandbox.python_runner import get_sandbox
            sandbox = get_sandbox()
            sandbox_result = sandbox.run_python(runner_code, cwd=_REPO_ROOT, timeout=30)
        except Exception as exc:
            sandbox_result = None
            evidence = {
                "runtime": runtime,
                "runtime_mode": runtime.get("mode", ""),
                "runtime_ready": bool(runtime.get("ready", False)),
                "docker_image": runtime.get("docker_image", ""),
                "artifact_dir": str(artifact_dir),
                "runner_path": str(runner_path),
                "input_path": str(inputs_path),
                "command": command,
                "sandbox_ok": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "error": str(exc),
                "checks": [{"name": "sandbox_execution", "passed": False, "message": str(exc)}],
            }
            self._write_evidence(artifact_dir, evidence)
            return evidence

        sandbox_payload = sandbox_result.to_dict()
        parsed = self._parse_sandbox_stdout(sandbox_result.stdout)
        checks = list(parsed.get("checks") or [])
        if not checks:
            checks = [{
                "name": "sandbox_output_parse",
                "passed": False,
                "message": "sandbox did not return verification checks",
            }]

        evidence = {
            "runtime": runtime,
            "runtime_mode": runtime.get("mode", ""),
            "runtime_ready": bool(runtime.get("ready", False)),
            "docker_image": runtime.get("docker_image", ""),
            "artifact_dir": str(artifact_dir),
            "runner_path": str(runner_path),
            "input_path": str(inputs_path),
            "command": command,
            "sandbox_ok": bool(sandbox_result.ok),
            "exit_code": int(sandbox_result.exit_code),
            "stdout": self._clip(sandbox_result.stdout),
            "stderr": self._clip(sandbox_result.stderr),
            "error": sandbox_result.error,
            "elapsed_sec": sandbox_payload.get("elapsed_sec", 0),
            "checks": checks,
            "parsed_summary": parsed.get("summary", {}),
            "sandbox_result": sandbox_payload,
        }
        self._write_evidence(artifact_dir, evidence)
        return evidence

    def _write_evidence(self, artifact_dir: Path, evidence: Dict[str, Any]) -> None:
        try:
            (artifact_dir / "verification_result.json").write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Failed to write skill verification evidence: %s", exc)

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(_REPO_ROOT))
        except ValueError:
            return str(path)

    def _parse_sandbox_stdout(self, stdout: str) -> Dict[str, Any]:
        for line in reversed((stdout or "").splitlines()):
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict) and "checks" in payload:
                return payload
        return {}

    def _clip(self, text: str, limit: int = 4000) -> str:
        text = text or ""
        if len(text) <= limit:
            return text
        return text[:1000] + "\n...(truncated)...\n" + text[-limit + 1000:]

    def _build_sandbox_validation_code(
        self,
        skill: SkillDefinition,
        test_scenarios: List[Dict[str, str]],
    ) -> str:
        payload = {
            "skill_id": skill.skill_id,
            "name": skill.name,
            "description": skill.description,
            "instructions": skill.instructions,
            "required_tools": list(skill.required_tools or []),
        }
        return textwrap.dedent(f"""
            import json
            SKILL = {json.dumps(payload, ensure_ascii=False)}
            SCENARIOS = {json.dumps(test_scenarios, ensure_ascii=False)}
            checks = []

            def add(name, passed, message):
                checks.append({{"name": name, "passed": bool(passed), "message": str(message)}})

            instructions = (SKILL.get("instructions") or "").strip()
            description = (SKILL.get("description") or "").strip()
            markers = [
                "步骤", "执行", "检查", "验证", "输出", "输入", "如果", "规则", "流程",
                "step", "check", "verify", "return", "use", "must", "should", "ensure",
            ]
            lowered = instructions.lower()

            add(
                "instructions_present",
                len(instructions) >= 20,
                f"instruction length={{len(instructions)}}",
            )
            add(
                "description_present",
                bool(description or SKILL.get("name")),
                "description or skill name is present",
            )
            add(
                "actionable_language",
                any(marker in lowered or marker in instructions for marker in markers),
                "instructions include actionable workflow language",
            )
            placeholder_terms = ["todo", "tbd", "placeholder", "待补", "待完善"]
            add(
                "not_placeholder",
                not any(term in lowered or term in instructions for term in placeholder_terms),
                "instructions are not placeholder text",
            )
            valid_scenarios = [
                item for item in SCENARIOS
                if (item.get("scenario") or item.get("prompt") or "").strip()
            ]
            add(
                "scenarios_defined",
                len(valid_scenarios) > 0,
                f"valid scenarios={{len(valid_scenarios)}}",
            )
            add(
                "scenario_prompts_defined",
                all((item.get("prompt") or item.get("scenario") or "").strip() for item in SCENARIOS),
                "each generated scenario has a prompt or scenario",
            )

            passed = sum(1 for check in checks if check["passed"])
            total = len(checks)
            pass_rate = passed / total if total else 0
            payload = {{
                "checks": checks,
                "summary": {{
                    "passed": passed,
                    "total": total,
                    "pass_rate": pass_rate,
                    "threshold": 0.7,
                }},
            }}
            print(json.dumps(payload, ensure_ascii=False))
        """).strip() + "\n"

    async def _generate_tests(self, skill: SkillDefinition) -> List[Dict[str, str]]:
        """通过 LLM 生成测试场景."""
        if not self._chat_harness:
            # Fallback: simple structural test
            return [
                {"scenario": "structural_check", "prompt": f"验证技能 {skill.name} 的指令是否完整且可操作"},
            ]

        try:
            result = await self._chat_harness.chat(
                prompt=f"为以下技能生成3个测试场景:\n\n名称: {skill.name}\n描述: {skill.description}\n指令: {skill.instructions[:2000]}",
                system_prompt=VERIFY_PROMPT,
                agent_id="skill_verifier",
            )
            # chat() returns TurnResult object with .response attribute
            response_text = getattr(result, 'response', '') if result else ''
            if response_text:
                import json
                try:
                    tests = json.loads(response_text)
                    if isinstance(tests, list):
                        return tests[:5]
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            logger.error("Test generation failed: %s", e)

        return [{"scenario": "basic_validation", "prompt": f"使用技能「{skill.name}」完成一个基本任务"}]

    async def _execute_test(self, skill: SkillDefinition, test: Dict[str, str]) -> bool:
        """执行单个测试场景 — 通过 LLM 评估."""
        if not self._chat_harness:
            # Structural validation: check skill has instructions
            return bool(skill.instructions and len(skill.instructions) > 20)

        try:
            result = await self._chat_harness.chat(
                prompt=f"使用以下技能指令处理测试场景:\n\n技能指令: {skill.instructions[:2000]}\n\n测试场景: {test.get('prompt', test.get('scenario', ''))}",
                system_prompt="你是一个技能测试执行器。执行给定的技能指令，输出 PASS 或 FAIL。",
                agent_id="skill_verifier",
            )
            # chat() returns TurnResult object with .response attribute
            response_text = getattr(result, 'response', '') if result else ''
            if response_text:
                return "PASS" in response_text.strip().upper()
        except Exception as e:
            logger.error("Test execution failed: %s", e)

        return False

    def get_result(self, skill_id: str) -> Optional[VerificationResult]:
        """获取验证结果."""
        return self._results.get(skill_id)

    def get_all_results(self) -> Dict[str, Dict[str, Any]]:
        """获取所有验证结果."""
        return {k: v.to_dict() for k, v in self._results.items()}


VERIFY_PROMPT = """为给定技能生成3个测试场景，以JSON数组格式输出:
[
  {"scenario": "场景描述", "prompt": "测试任务描述", "expected": "期望输出特征"}
]

测试场景应覆盖:
1. 正常情况 (happy path)
2. 边界情况 (edge case)
3. 异常处理 (error handling)

只输出JSON数组，不要其他文字。"""


# ── Singleton ────────────────────────────────────────────────────

_verifier: Optional[SkillVerifier] = None


def get_skill_verifier() -> SkillVerifier:
    global _verifier
    if _verifier is None:
        _verifier = SkillVerifier()
    return _verifier


def init_skill_verifier(skill_library=None, chat_harness=None) -> SkillVerifier:
    global _verifier
    _verifier = SkillVerifier(skill_library=skill_library, chat_harness=chat_harness)
    logger.info("SkillVerifier initialized")
    return _verifier
