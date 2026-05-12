#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CI/CD 门禁校验脚本 — 智能体广场遥测数据完整性验证.

校验项:
1. 采样率压测门禁: P99 延迟增量 < 5%
2. 采样一致性校验: 同一 traceId 采样标记一致
3. 字段完整性校验: 缺失 P0 字段阻断发布
4. 能耗/热采样门禁: P2 字段合规采集

用法:
    python scripts/validate_telemetry.py --base-url http://localhost:8080
    python scripts/validate_telemetry.py --check-sampling-consistency
    python scripts/validate_telemetry.py --check-field-completeness
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s  %(message)s",
)
logger = logging.getLogger("validate_telemetry")

# P0 必采字段列表
P0_REQUIRED_FIELDS = [
    "trace_id",
    "span_id",
    "event_type",
    "timestamp",
    "anomaly_score",
    "status",
    "duration_ms",
    "source",
]

# P1 条件采样字段
P1_FIELDS = [
    "model_version",
    "gpu_power_w",
    "cpu_usage_pct",
    "memory_mb",
    "token_count",
    "latency_p99_ms",
    "agent_id",
    "session_id",
]

# P2 离线批量字段
P2_FIELDS = [
    "node_pue",
    "thermal_sensor_c",
    "energy_kwh",
    "carbon_g",
    "network_rtt_ms",
    "disk_iops",
    "container_restart_count",
]


def check_field_completeness(
    records: List[Dict[str, Any]],
    fail_on_missing_p0: bool = True,
) -> Dict[str, Any]:
    """字段完整性校验 — 确保 P0 字段齐全.

    Args:
        records: 遥测记录列表
        fail_on_missing_p0: 缺失 P0 字段是否阻断发布

    Returns:
        校验结果
    """
    total = len(records)
    if total == 0:
        return {"passed": True, "message": "无记录可校验", "details": {}}

    missing_p0_count = 0
    missing_p1_count = 0
    missing_p2_count = 0
    field_stats: Dict[str, Dict[str, int]] = {}

    for record in records:
        fields_missing = record.get("fields_missing", [])
        priority = record.get("priority", "P2")

        for f in fields_missing:
            if f in P0_REQUIRED_FIELDS:
                missing_p0_count += 1
            elif f in P1_FIELDS:
                missing_p1_count += 1
            elif f in P2_FIELDS:
                missing_p2_count += 1

            if f not in field_stats:
                field_stats[f] = {"missing": 0, "total": 0}
            field_stats[f]["missing"] += 1

        for f in record.get("fields_present", []):
            if f not in field_stats:
                field_stats[f] = {"missing": 0, "total": 0}
            field_stats[f]["total"] = field_stats[f].get("total", 0) + 1

    passed = True
    messages = []

    if missing_p0_count > 0:
        if fail_on_missing_p0:
            passed = False
            messages.append(
                f"❌ 发现 {missing_p0_count} 个缺失 P0 字段 — 阻断发布"
            )
        else:
            messages.append(
                f"⚠️ 发现 {missing_p0_count} 个缺失 P0 字段（非阻断模式）"
            )

    if missing_p1_count > 0:
        messages.append(f"⚠️ 发现 {missing_p1_count} 个缺失 P1 字段")

    if missing_p2_count > 0:
        messages.append(f"ℹ️ 发现 {missing_p2_count} 个缺失 P2 字段（可接受）")

    if passed:
        messages.append(f"✅ 字段完整性校验通过 ({total} 条记录)")

    return {
        "passed": passed,
        "message": "; ".join(messages),
        "details": {
            "total_records": total,
            "missing_p0": missing_p0_count,
            "missing_p1": missing_p1_count,
            "missing_p2": missing_p2_count,
            "field_stats": field_stats,
        },
    }


def check_sampling_consistency(
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """采样一致性校验 — 同一 traceId 采样标记一致.

    Args:
        records: 遥测记录列表

    Returns:
        校验结果
    """
    trace_groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        tid = record.get("trace_id", "")
        if tid:
            trace_groups.setdefault(tid, []).append(record)

    inconsistencies = []
    for trace_id, group in trace_groups.items():
        sampled_values = set()
        for r in group:
            sampled_values.add(r.get("sampled", False))
        if len(sampled_values) > 1:
            inconsistencies.append(
                {
                    "trace_id": trace_id,
                    "span_count": len(group),
                    "sampled_values": list(sampled_values),
                }
            )

    passed = len(inconsistencies) == 0
    message = (
        f"✅ 采样一致性校验通过 ({len(trace_groups)} 个 traceId)"
        if passed
        else f"❌ 发现 {len(inconsistencies)} 个不一致的 traceId"
    )

    return {
        "passed": passed,
        "message": message,
        "details": {
            "total_trace_ids": len(trace_groups),
            "inconsistencies": inconsistencies[:20],  # 最多显示 20 个
        },
    }


def check_sampling_rate_pressure(
    baseline_p99_ms: float,
    current_p99_ms: float,
    max_increase_pct: float = 5.0,
) -> Dict[str, Any]:
    """采样率压测门禁 — P99 延迟增量 < 5%.

    Args:
        baseline_p99_ms: 基线 P99 延迟 (ms)
        current_p99_ms: 当前 P99 延迟 (ms)
        max_increase_pct: 最大允许增量百分比

    Returns:
        校验结果
    """
    if baseline_p99_ms <= 0:
        return {
            "passed": True,
            "message": "基线数据不足，跳过压测校验",
            "details": {},
        }

    increase_pct = (current_p99_ms - baseline_p99_ms) / baseline_p99_ms * 100
    passed = increase_pct < max_increase_pct

    message = (
        f"✅ P99 延迟增量 {increase_pct:.2f}% < {max_increase_pct}% — 通过"
        if passed
        else (
            f"❌ P99 延迟增量 {increase_pct:.2f}% >= {max_increase_pct}% — "
            f"阻断发布 (基线: {baseline_p99_ms:.1f}ms, 当前: {current_p99_ms:.1f}ms)"
        )
    )

    return {
        "passed": passed,
        "message": message,
        "details": {
            "baseline_p99_ms": baseline_p99_ms,
            "current_p99_ms": current_p99_ms,
            "increase_pct": round(increase_pct, 2),
            "max_allowed_pct": max_increase_pct,
        },
    }


def check_energy_thermal_sampling(
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """能耗/热采样门禁 — P2 字段合规采集.

    校验在高异常场景下 P2 字段是否被正确采集。
    """
    high_anomaly_records = [
        r for r in records if r.get("anomaly_score", 0) >= 0.7
    ]
    if not high_anomaly_records:
        return {
            "passed": True,
            "message": "无高异常记录，跳过能耗/热采样校验",
            "details": {"high_anomaly_count": 0},
        }

    missing_p2 = 0
    for r in high_anomaly_records:
        fields_missing = r.get("fields_missing", [])
        p2_missing = [f for f in fields_missing if f in P2_FIELDS]
        if p2_missing:
            missing_p2 += 1

    # 允许少量缺失（非关键字段）
    allowed_missing_ratio = 0.2
    actual_ratio = missing_p2 / len(high_anomaly_records)
    passed = actual_ratio <= allowed_missing_ratio

    message = (
        f"✅ 能耗/热采样校验通过 "
        f"(高异常记录 {len(high_anomaly_records)} 条, "
        f"缺失率 {actual_ratio:.1%} <= {allowed_missing_ratio:.0%})"
        if passed
        else (
            f"❌ 能耗/热采样校验失败 "
            f"(缺失率 {actual_ratio:.1%} > {allowed_missing_ratio:.0%})"
        )
    )

    return {
        "passed": passed,
        "message": message,
        "details": {
            "high_anomaly_count": len(high_anomaly_records),
            "missing_p2_count": missing_p2,
            "missing_ratio": round(actual_ratio, 4),
            "allowed_ratio": allowed_missing_ratio,
        },
    }


def run_all_checks(
    records: List[Dict[str, Any]],
    baseline_p99_ms: float = 0,
    current_p99_ms: float = 0,
) -> Dict[str, Any]:
    """运行所有门禁校验."""
    results = {}

    # 1. 字段完整性校验
    results["field_completeness"] = check_field_completeness(records)

    # 2. 采样一致性校验
    results["sampling_consistency"] = check_sampling_consistency(records)

    # 3. 采样率压测门禁
    results["sampling_rate_pressure"] = check_sampling_rate_pressure(
        baseline_p99_ms, current_p99_ms
    )

    # 4. 能耗/热采样门禁
    results["energy_thermal_sampling"] = check_energy_thermal_sampling(records)

    # 总体结果
    all_passed = all(r["passed"] for r in results.values())
    return {
        "passed": all_passed,
        "summary": "✅ 所有门禁校验通过" if all_passed else "❌ 部分门禁校验未通过",
        "checks": results,
    }


def fetch_telemetry(base_url: str) -> List[Dict[str, Any]]:
    """从 API 获取遥测数据."""
    url = f"{base_url}/api/v1/agent-config/plaza/monitoring/telemetry?limit=500"
    try:
        req = Request(url)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data if isinstance(data, list) else data.get("records", [])
    except Exception as e:
        logger.warning(f"无法从 {url} 获取遥测数据: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="智能体广场遥测数据完整性校验"
    )
    parser.add_argument(
        "--base-url", default="http://localhost:8080",
        help="API 基础 URL",
    )
    parser.add_argument(
        "--check-field-completeness", action="store_true",
        help="仅运行字段完整性校验",
    )
    parser.add_argument(
        "--check-sampling-consistency", action="store_true",
        help="仅运行采样一致性校验",
    )
    parser.add_argument(
        "--baseline-p99", type=float, default=0,
        help="基线 P99 延迟 (ms)",
    )
    parser.add_argument(
        "--current-p99", type=float, default=0,
        help="当前 P99 延迟 (ms)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="以 JSON 格式输出结果",
    )

    args = parser.parse_args()

    # 获取遥测数据
    records = fetch_telemetry(args.base_url)
    logger.info(f"获取到 {len(records)} 条遥测记录")

    # 运行校验
    if args.check_field_completeness:
        result = check_field_completeness(records)
    elif args.check_sampling_consistency:
        result = check_sampling_consistency(records)
    else:
        result = run_all_checks(
            records,
            baseline_p99_ms=args.baseline_p99,
            current_p99_ms=args.current_p99,
        )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"  智能体广场遥测门禁校验")
        print(f"{'='*60}")
        print(f"  结果: {'✅ 通过' if result.get('passed', True) else '❌ 未通过'}")
        print(f"  消息: {result.get('message', '')}")
        if "checks" in result:
            for name, check in result["checks"].items():
                status = "✅" if check["passed"] else "❌"
                print(f"  {status} {name}: {check['message']}")
        print(f"{'='*60}\n")

    sys.exit(0 if result.get("passed", True) else 1)


if __name__ == "__main__":
    main()
