#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M-3.3b：恢复历史 20/40 证据或按协议重跑跨团队迁移计数。

策略：
1) 扫描生产 storage/agent_memory 只读定位 log=20 / sum=40 与 log=40 样本；
2) 对候选样本 build_export_v2 并记录 manifest 哈希；
3) 在隔离目录按协议重跑 ops→security/finops merge 迁移；
4) 输出可复现报告（原始路径 + 哈希 + 精确计数 + 差异解释）。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore  # noqa: E402
from agents.agent_memory_migration import (  # noqa: E402
    build_export_v2,
    count_each_layer,
    import_transaction,
    load_inherited,
    recompute_manifest_hash,
    sha256_json,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def scan_production(root: Path) -> List[Dict[str, Any]]:
    store = AgentMemoryStore(root)
    rows = []
    if not root.is_dir():
        return rows
    for team_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        for agent_dir in sorted(p for p in team_dir.iterdir() if p.is_dir()):
            team_id, agent_id = team_dir.name, agent_dir.name
            try:
                core = AgentMemoryCore(team_id, agent_id, store=store)
                exp = build_export_v2(core)
            except Exception as e:
                rows.append(
                    {
                        "team_id": team_id,
                        "agent_id": agent_id,
                        "error": str(e),
                        "paths": {n: str(agent_dir / f"{n}.json") for n in ("log", "perception", "semantic", "meta")},
                    }
                )
                continue
            counts = exp["record_counts"]
            total = sum(counts.values())
            rows.append(
                {
                    "team_id": team_id,
                    "agent_id": agent_id,
                    "record_counts": counts,
                    "sum_counts": total,
                    "export_id": exp["export_id"],
                    "manifest_sha256": exp["content_hashes"]["manifest_sha256"],
                    "layer_hashes": exp["content_hashes"]["layers"],
                    "paths": {
                        n: str(agent_dir / f"{n}.json")
                        for n in ("log", "perception", "intentions", "affect", "semantic", "meta", "inherited")
                        if (agent_dir / f"{n}.json").is_file()
                    },
                    "matches_old_claim_20": counts.get("log") == 20 or total == 20,
                    "matches_old_claim_40": counts.get("log") == 40 or total == 40,
                    "matches_20_and_40_pair": counts.get("log") == 20 and total == 40,
                }
            )
    return rows


def protocol_rerun(seed: int = 20260728) -> Dict[str, Any]:
    """精确协议：ops 生成固定记录 → export v2 → merge 到 security/finops。"""
    with tempfile.TemporaryDirectory(prefix="ag_mem_count_protocol_") as tmp:
        store = AgentMemoryStore(Path(tmp))
        # deterministic content from seed
        ops = AgentMemoryCore("ops", "ops_expert", store=store)
        ops.bind(True)
        # Protocol A: 20 episodic + 20 perception → total 40 (解释 old 20/40 口径)
        for i in range(20):
            ops.log.append(
                {
                    "action": "ops_event",
                    "detail": f"ops-protocol-{seed}-{i:02d}",
                    "importance": 6 + (i % 3),
                    "tags": ["ops", "protocol", f"s{seed}"],
                }
            )
            ops.perception.perceive(
                {
                    "modality": "system",
                    "payload": {"i": i, "seed": seed, "kind": "ops_metric"},
                }
            )
        # also produce a 40-log variant export for comparison
        ops40 = AgentMemoryCore("ops", "ops_expert_40", store=store)
        ops40.bind(True)
        for i in range(40):
            ops40.log.append(
                {
                    "action": "ops_event40",
                    "detail": f"ops40-protocol-{seed}-{i:02d}",
                    "importance": 5,
                    "tags": ["ops", "protocol40"],
                }
            )
            ops40.perception.perceive({"modality": "system", "payload": {"i": i, "seed": seed}})

        exp20 = build_export_v2(ops)
        exp40 = build_export_v2(ops40)
        assert count_each_layer(exp20["layers"]) == exp20["record_counts"]
        assert recompute_manifest_hash(exp20) == exp20["content_hashes"]["manifest_sha256"]

        sec = AgentMemoryCore("security", "sec_learner", store=store)
        fin = AgentMemoryCore("finops", "fin_learner", store=store)
        sec.bind(True)
        fin.bind(True)
        # local noise must survive merge
        sec.log.append({"action": "local", "detail": "sec-local-keep", "importance": 5})
        fin.log.append({"action": "local", "detail": "fin-local-keep", "importance": 5})

        r_sec = import_transaction(
            sec, exp20, strategy="merge", transfer_id=f"tx_ops_sec_{seed}"
        )
        r_fin = import_transaction(
            fin, exp20, strategy="merge", transfer_id=f"tx_ops_fin_{seed}"
        )
        part_sec = load_inherited(store, "security", "sec_learner")["partitions"][0]
        part_fin = load_inherited(store, "finops", "fin_learner")["partitions"][0]

        # optional also import 40-export to different beneficiaries
        sec2 = AgentMemoryCore("security", "sec_from40", store=store)
        sec2.bind(True)
        r_sec40 = import_transaction(
            sec2, exp40, strategy="merge", transfer_id=f"tx_ops40_sec_{seed}"
        )
        part_sec40 = load_inherited(store, "security", "sec_from40")["partitions"][0]

        return {
            "seed": seed,
            "protocol": {
                "source_team": "ops",
                "targets": ["security", "finops"],
                "strategy": "merge",
                "record_generation_rule": "20 log + 20 perception deterministic details ops-protocol-{seed}-{i}",
                "variant_40_rule": "40 log + 40 perception",
            },
            "export_20": {
                "export_id": exp20["export_id"],
                "record_counts": exp20["record_counts"],
                "sum": sum(exp20["record_counts"].values()),
                "manifest_sha256": exp20["content_hashes"]["manifest_sha256"],
                "layer_hashes": exp20["content_hashes"]["layers"],
            },
            "export_40": {
                "export_id": exp40["export_id"],
                "record_counts": exp40["record_counts"],
                "sum": sum(exp40["record_counts"].values()),
                "manifest_sha256": exp40["content_hashes"]["manifest_sha256"],
            },
            "import_security": {
                "tx_id": r_sec.get("tx_id"),
                "state": r_sec.get("state"),
                "partition_record_counts": part_sec.get("record_counts"),
                "partition_hashes": part_sec.get("hashes"),
                "local_log_preserved": any(
                    e.get("detail") == "sec-local-keep"
                    for e in AgentMemoryCore("security", "sec_learner", store=store).log.events
                ),
            },
            "import_finops": {
                "tx_id": r_fin.get("tx_id"),
                "state": r_fin.get("state"),
                "partition_record_counts": part_fin.get("record_counts"),
                "partition_hashes": part_fin.get("hashes"),
                "local_log_preserved": any(
                    e.get("detail") == "fin-local-keep"
                    for e in AgentMemoryCore("finops", "fin_learner", store=store).log.events
                ),
            },
            "import_security_from40": {
                "tx_id": r_sec40.get("tx_id"),
                "partition_record_counts": part_sec40.get("record_counts"),
            },
            "assertions": {
                "export20_log_is_20": exp20["record_counts"]["log"] == 20,
                "export20_sum_is_40": sum(exp20["record_counts"].values()) == 40,
                "export40_log_is_40": exp40["record_counts"]["log"] == 40,
                "import_counts_match_export20": part_sec.get("record_counts") == exp20["record_counts"]
                and part_fin.get("record_counts") == exp20["record_counts"],
            },
        }


def build_report(prod_root: Path, seed: int) -> Dict[str, Any]:
    prod_rows = scan_production(prod_root)
    pair_20_40 = [r for r in prod_rows if r.get("matches_20_and_40_pair")]
    claim20 = [r for r in prod_rows if r.get("matches_old_claim_20")]
    claim40 = [r for r in prod_rows if r.get("matches_old_claim_40")]
    protocol = protocol_rerun(seed=seed)

    # discrepancy diagnosis
    cause_parts = []
    if pair_20_40:
        cause_parts.append(
            "生产库存在 log=20 且 layers 合计=40 的样本（如 team_v/*），"
            "旧文档可能把「log 计数 20」与「层合计 40」混称为 20/40。"
        )
    if claim40 and not pair_20_40:
        cause_parts.append("生产库存在 log=40 样本，可能被单独记为 40。")
    if not pair_20_40 and not claim20 and not claim40:
        cause_parts.append("生产库未找到与 20/40 直接匹配的样本；以协议重跑为准。")
    cause_parts.append(
        "v2 信封以 layers 重新计数+哈希为准；无旧 export 哈希时不能断言历史声明哪一个错误。"
    )

    report = {
        "schema": "ag.memory.count_audit/v2",
        "generated_at": _now(),
        "old_claims": [20, 40],
        "production_root": str(prod_root.resolve()),
        "production_scan": {
            "n_agents": len(prod_rows),
            "matches_20_and_40_pair": pair_20_40,
            "matches_20": claim20,
            "matches_40": claim40,
        },
        "protocol_rerun": protocol,
        "discrepancy_cause": " ".join(cause_parts),
        "conclusion": {
            "can_adjudicate_historical_20_or_40_as_ground_truth": False
            if not pair_20_40
            else "partial_with_path_evidence",
            "authoritative_today": "v2 record_counts + manifest_sha256 from layers",
            "protocol_export20": protocol["export_20"]["record_counts"],
            "protocol_export40": protocol["export_40"]["record_counts"],
            "protocol_import_security_counts": protocol["import_security"]["partition_record_counts"],
            "protocol_import_finops_counts": protocol["import_finops"]["partition_record_counts"],
        },
        "raw_artifact_paths": {
            "production_matches": [
                {"team": r.get("team_id"), "agent": r.get("agent_id"), "paths": r.get("paths"), "manifest": r.get("manifest_sha256")}
                for r in (pair_20_40 or claim20 or claim40)[:20]
            ],
            "protocol": "ephemeral tempfile; hashes recorded in protocol_rerun section",
        },
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--production-root",
        default=str(ROOT / "storage" / "agent_memory"),
    )
    ap.add_argument("--seed", type=int, default=20260728)
    ap.add_argument(
        "--output",
        default=str(ROOT / "docs" / "reports" / "agent-memory-migration-count-audit.json"),
    )
    ap.add_argument(
        "--md-output",
        default=str(ROOT / "docs" / "reports" / "agent-memory-migration-count-audit.md"),
    )
    args = ap.parse_args()
    report = build_report(Path(args.production_root), seed=args.seed)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = Path(args.md_output)
    pairs = report["production_scan"]["matches_20_and_40_pair"]
    lines = [
        "# Agent 记忆迁移计数审计（M-3.3b）",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- old_claims: {report['old_claims']}",
        f"- production_root: `{report['production_root']}`",
        "",
        "## 生产库命中",
        f"- n_agents_scanned: {report['production_scan']['n_agents']}",
        f"- log=20 & sum=40 样本数: {len(pairs)}",
    ]
    for r in pairs[:10]:
        lines.append(
            f"  - `{r['team_id']}/{r['agent_id']}` counts={r['record_counts']} "
            f"manifest=`{r['manifest_sha256'][:16]}…` paths={list((r.get('paths') or {}).keys())}"
        )
    lines += [
        "",
        "## 协议重跑（隔离）",
        f"- seed: {report['protocol_rerun']['seed']}",
        f"- export20: {report['protocol_rerun']['export_20']['record_counts']} "
        f"sum={report['protocol_rerun']['export_20']['sum']}",
        f"- export40: {report['protocol_rerun']['export_40']['record_counts']}",
        f"- import security partition: {report['protocol_rerun']['import_security']['partition_record_counts']}",
        f"- import finops partition: {report['protocol_rerun']['import_finops']['partition_record_counts']}",
        f"- assertions: {report['protocol_rerun']['assertions']}",
        "",
        "## 差异原因",
        report["discrepancy_cause"],
        "",
        "## 结论",
        json.dumps(report["conclusion"], ensure_ascii=False, indent=2),
        "",
        f"JSON 产物: `{out}`",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "json": str(out),
                "md": str(md),
                "pair_hits": len(pairs),
                "protocol_assertions": report["protocol_rerun"]["assertions"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
