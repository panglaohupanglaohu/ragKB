# -*- coding: utf-8 -*-
"""Skill publish quality gate — quantified thresholds before public release.

门槛（可用环境变量覆盖）:
  - AG_SKILL_PUBLISH_PASS_RATE_MIN   默认 0.70  验证通过率
  - AG_SKILL_PUBLISH_TWIN_GAIN_MIN   默认 0.05  孪生 A/B 增益（仅 twin 实际跑过时强制）
  - AG_SKILL_PUBLISH_MIN_SAMPLES     默认 3     样本/用例数下限（total_tests 或 passed+failed）
  - AG_SKILL_PUBLISH_MIN_USAGE       默认 0     可选 usage_count 下限（默认不强制）

不达标技能保持 candidate（private + 非 published），不得进公共库。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return float(default)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(default)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return int(default)
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return int(default)


def gate_thresholds() -> Dict[str, Any]:
    """Current publish-gate thresholds (env-overridable)."""
    return {
        "pass_rate_min": _env_float("AG_SKILL_PUBLISH_PASS_RATE_MIN", 0.70),
        "twin_gain_min": _env_float("AG_SKILL_PUBLISH_TWIN_GAIN_MIN", 0.05),
        "min_samples": _env_int("AG_SKILL_PUBLISH_MIN_SAMPLES", 3),
        "min_usage": _env_int("AG_SKILL_PUBLISH_MIN_USAGE", 0),
        "evidence_type": "skill_verify",
        "status_ok": ["verified", "passed"],
    }


def _lifecycle_str(skill: Any) -> str:
    stage = getattr(skill, "lifecycle_stage", "") or ""
    if hasattr(stage, "value"):
        stage = stage.value
    return str(stage or "")


def _as_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            d = to_dict()
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}
    return {}


def _sample_count(metrics: Dict[str, Any], last_verify: Dict[str, Any]) -> int:
    """Resolve verification sample count from evidence metrics or last_verify."""
    for key in ("total_tests", "n_samples", "sample_count"):
        if key in metrics and metrics.get(key) is not None:
            try:
                return int(metrics.get(key) or 0)
            except (TypeError, ValueError):
                pass
    passed = metrics.get("passed")
    failed = metrics.get("failed")
    if passed is not None or failed is not None:
        try:
            return int(passed or 0) + int(failed or 0)
        except (TypeError, ValueError):
            pass
    if last_verify:
        try:
            p = int(last_verify.get("passed") or 0)
            f = int(last_verify.get("failed") or 0)
            if p or f:
                return p + f
        except (TypeError, ValueError):
            pass
        try:
            if last_verify.get("pass_rate") is not None and last_verify.get("total_tests") is not None:
                return int(last_verify.get("total_tests") or 0)
        except (TypeError, ValueError):
            pass
    return 0


def _from_flat_twin_metrics(src: Dict[str, Any]) -> Dict[str, Any]:
    """Build twin dict from EvidenceRun flat twin_* metrics."""
    if not isinstance(src, dict):
        return {}
    if not (
        src.get("twin_ran")
        or src.get("twin_target_gain") is not None
        or src.get("twin_status")
        or src.get("twin_passed") is not None
    ):
        return {}
    return {
        "status": src.get("twin_status") or ("ok" if src.get("twin_ran") else ""),
        "skipped": bool(src.get("twin_skipped", False)),
        "passed": src.get("twin_passed"),
        "target_gain": src.get("twin_target_gain"),
        "target_gain_pp": src.get("twin_target_gain_pp"),
        "gain_threshold": src.get("twin_gain_threshold"),
        "n_seeds": src.get("twin_n_seeds"),
        "twin_ran": bool(src.get("twin_ran")),
    }


def _from_nested_twin(src: Dict[str, Any]) -> Dict[str, Any]:
    """Build twin dict from nested twin_ab / last_verify.twin_ab."""
    if not isinstance(src, dict) or not src:
        return {}
    looks = (
        "target_gain" in src
        or "target_gain_pp" in src
        or "gain_threshold" in src
        or "baseline" in src
        or "treatment" in src
        or src.get("status") in ("ok", "error")
        or (src.get("passed") is not None and src.get("skipped") is not None)
    )
    if not looks:
        return {}
    out = dict(src)
    if out.get("target_gain") is None and out.get("twin_target_gain") is not None:
        out["target_gain"] = out.get("twin_target_gain")
    if out.get("passed") is None and out.get("twin_passed") is not None:
        out["passed"] = out.get("twin_passed")
    return out


def _twin_payload(
    metrics: Dict[str, Any],
    detail: Dict[str, Any],
    last_verify: Dict[str, Any],
) -> Dict[str, Any]:
    """Collect twin A/B summary if verification actually ran twin."""
    for src in (
        metrics.get("twin_ab") if isinstance(metrics.get("twin_ab"), dict) else None,
        detail.get("twin_ab") if isinstance(detail.get("twin_ab"), dict) else None,
        detail.get("twin_summary") if isinstance(detail.get("twin_summary"), dict) else None,
        (last_verify or {}).get("twin_ab") if isinstance((last_verify or {}).get("twin_ab"), dict) else None,
    ):
        twin = _from_nested_twin(src or {})
        if twin:
            return twin
    # Prefer explicit flat twin_* on metrics (do not treat whole metrics as nested twin)
    return _from_flat_twin_metrics(metrics)


def _twin_actually_ran(twin: Dict[str, Any]) -> bool:
    if not twin:
        return False
    if twin.get("skipped") or twin.get("twin_skipped"):
        return False
    if twin.get("twin_ran") is True:
        return True
    status = str(twin.get("status") or "").lower()
    if status in ("skipped", "skip"):
        return False
    if status in ("ok", "error"):
        return True
    return twin.get("target_gain") is not None or twin.get("target_gain_pp") is not None


def evaluate_publish_gate(
    skill: Any,
    latest_evidence: Any = None,
    *,
    last_verify: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate whether a skill may enter public/production publish.

    Returns dict with ok/reason/checks/required/latest_evidence/skill.
    """
    thr = gate_thresholds()
    checks: List[Dict[str, Any]] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    if skill is None:
        return {
            "ok": False,
            "reason": "skill_not_found",
            "checks": [{"name": "skill_exists", "passed": False, "detail": "skill missing"}],
            "required": thr,
            "candidate_held": True,
            "twin": {"ran": False},
        }

    cfg = getattr(skill, "config", None) or {}
    if not isinstance(cfg, dict):
        cfg = {}
    lv = last_verify if isinstance(last_verify, dict) else (cfg.get("last_verify") or {})
    if not isinstance(lv, dict):
        lv = {}

    if not latest_evidence:
        add_check("recent_verification", False, "no skill_verify EvidenceRun found")
        return {
            "ok": False,
            "reason": "missing_verification_evidence",
            "checks": checks,
            "required": {
                "evidence_type": thr["evidence_type"],
                "status": thr["status_ok"],
                "pass_rate_min": thr["pass_rate_min"],
                "twin_gain_min": thr["twin_gain_min"],
                "min_samples": thr["min_samples"],
                "min_usage": thr["min_usage"],
                "exit_code": 0,
            },
            "skill": {
                "skill_id": getattr(skill, "skill_id", ""),
                "name": getattr(skill, "name", ""),
                "quality_score": getattr(skill, "quality_score", 0),
                "lifecycle_stage": _lifecycle_str(skill),
            },
            "candidate_held": True,
            "twin": {"ran": False},
        }

    latest_dict = _as_dict(latest_evidence)
    metrics = dict(getattr(latest_evidence, "metrics_after", None) or latest_dict.get("metrics_after") or {})
    runtime = dict(getattr(latest_evidence, "runtime", None) or latest_dict.get("runtime") or {})
    detail = dict(getattr(latest_evidence, "detail", None) or latest_dict.get("detail") or {})
    status_value = str(getattr(latest_evidence, "status", None) or latest_dict.get("status") or "").lower()
    exit_code = getattr(latest_evidence, "exit_code", None)
    if exit_code is None:
        exit_code = latest_dict.get("exit_code")
    try:
        exit_code_i = int(exit_code) if exit_code is not None else -1
    except (TypeError, ValueError):
        exit_code_i = -1

    quality = float(getattr(skill, "quality_score", 0) or 0)
    pass_rate = float(metrics.get("pass_rate") if metrics.get("pass_rate") is not None else (lv.get("pass_rate") if lv.get("pass_rate") is not None else quality) or 0)
    lifecycle = _lifecycle_str(skill)
    samples = _sample_count(metrics, lv)
    usage = int(getattr(skill, "usage_count", 0) or 0)

    add_check(
        "verification_status",
        status_value in set(thr["status_ok"]),
        f"latest status={status_value or getattr(latest_evidence, 'status', '')}",
    )
    add_check(
        "pass_rate",
        pass_rate >= float(thr["pass_rate_min"]),
        f"pass_rate={pass_rate:.2f} (min {thr['pass_rate_min']})",
    )
    add_check(
        "runtime_ready",
        bool(runtime.get("ready", False)),
        f"runtime mode={runtime.get('mode', 'unknown')} ready={runtime.get('ready', False)}",
    )
    add_check(
        "exit_code",
        exit_code_i == 0,
        f"exit_code={exit_code_i}",
    )
    add_check(
        "lifecycle_verified",
        lifecycle == "verified" or status_value in set(thr["status_ok"]),
        f"lifecycle_stage={lifecycle}",
    )
    add_check(
        "min_samples",
        samples >= int(thr["min_samples"]),
        f"samples={samples} (min {thr['min_samples']})",
    )
    if int(thr["min_usage"]) > 0:
        add_check(
            "min_usage",
            usage >= int(thr["min_usage"]),
            f"usage_count={usage} (min {thr['min_usage']})",
        )

    twin = _twin_payload(metrics, detail, lv)
    twin_ran = _twin_actually_ran(twin)
    if twin_ran:
        gain = twin.get("target_gain")
        if gain is None and twin.get("target_gain_pp") is not None:
            try:
                gain = float(twin.get("target_gain_pp")) / 100.0
            except (TypeError, ValueError):
                gain = None
        try:
            gain_f = float(gain) if gain is not None else None
        except (TypeError, ValueError):
            gain_f = None
        thr_gain = float(twin.get("gain_threshold") if twin.get("gain_threshold") is not None else thr["twin_gain_min"])
        twin_passed = twin.get("passed")
        if twin_passed is None and gain_f is not None:
            twin_passed = gain_f >= thr_gain
        gain_ok = bool(twin_passed) and (gain_f is None or gain_f >= thr_gain)
        add_check(
            "twin_ab_gain",
            gain_ok,
            (
                f"twin gain={gain_f if gain_f is not None else 'n/a'} "
                f"(min {thr_gain}); passed={twin_passed}"
            ),
        )
    else:
        add_check(
            "twin_ab_gain",
            True,
            "twin A/B not required (not run / skipped)",
        )

    ok = all(c["passed"] for c in checks)
    failed_names = [c["name"] for c in checks if not c["passed"]]
    if ok:
        reason = ""
    elif "verification_status" in failed_names or "pass_rate" in failed_names:
        reason = "latest_verification_not_publishable"
    elif "min_samples" in failed_names:
        reason = "insufficient_samples"
    elif "twin_ab_gain" in failed_names:
        reason = "twin_ab_gain_below_threshold"
    elif "min_usage" in failed_names:
        reason = "insufficient_usage"
    else:
        reason = "latest_verification_not_publishable"

    return {
        "ok": ok,
        "reason": reason,
        "checks": checks,
        "required": {
            "evidence_type": thr["evidence_type"],
            "status": thr["status_ok"],
            "pass_rate_min": thr["pass_rate_min"],
            "twin_gain_min": thr["twin_gain_min"],
            "min_samples": thr["min_samples"],
            "min_usage": thr["min_usage"],
            "exit_code": 0,
        },
        "latest_evidence": {
            "evidence_id": getattr(latest_evidence, "evidence_id", None) or latest_dict.get("evidence_id"),
            "created_at": getattr(latest_evidence, "created_at", None) or latest_dict.get("created_at"),
            "status": getattr(latest_evidence, "status", None) or latest_dict.get("status"),
            "runtime": runtime,
            "command": getattr(latest_evidence, "command", None) or latest_dict.get("command"),
            "exit_code": exit_code_i,
            "artifact_dir": getattr(latest_evidence, "artifact_dir", None) or latest_dict.get("artifact_dir"),
            "request_id": getattr(latest_evidence, "request_id", None) or latest_dict.get("request_id"),
            "metrics_after": metrics,
        },
        "skill": {
            "skill_id": getattr(skill, "skill_id", ""),
            "name": getattr(skill, "name", ""),
            "quality_score": quality,
            "lifecycle_stage": lifecycle,
            "usage_count": usage,
            "sample_count": samples,
        },
        "twin": twin if twin_ran else {"ran": False},
        "candidate_held": not ok,
    }
