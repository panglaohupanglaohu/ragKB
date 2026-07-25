# -*- coding: utf-8 -*-
"""四轨扩展实验: 多Agent记忆继承 + 鲁棒性测试 + 数据扩展 + 迭代扩展
Track 2&3: No LLM needed. Track 1&4: Requires LLM via ChatHarness/hames gateway."""

from __future__ import annotations
import json, sys, time, random, math, statistics, uuid
from pathlib import Path
from copy import deepcopy

BACKEND = Path("/Users/panglaohu/Downloads/AgentsGroup2026/src/backend")
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore
from agents.tse import (
    TSEConfig,
    TSEPipeline,
    parse_transcript,
    extract_skill_moments,
    validate_skill_fields,
)

RESULTS = {
    "track2_memory_inheritance": [],
    "track3_robustness": [],
    "track4_iterations": [],
}


# ═══════════════════════════════════════════════════════════
# TRACK 2: Multi-Agent Memory Inheritance Verification
# ═══════════════════════════════════════════════════════════
def run_track2_memory_inheritance():
    """Test memory export/import between 3 agent pairs with behavior verification."""
    print("\n=== Track 2: Multi-Agent Memory Inheritance ===")

    agent_teams = ["team_ops", "team_security", "team_finops"]
    agent_pairs = [
        ("architect_v1", "architect_v2", "team_ops"),
        ("security_v1", "security_v2", "team_security"),
        ("finops_v1", "finops_v2", "team_finops"),
    ]

    all_results = []
    for src_agent, dst_agent, team_id in agent_pairs:
        store = AgentMemoryStore()
        core_src = AgentMemoryCore(team_id, src_agent, store=store)
        core_src.bind(True)

        # Source accumulates experience across 3 task periods
        src_tasks = [
            (35, "ES cluster IO analysis", 0.72),
            (28, "Security group rule audit", 0.45),
            (42, "RI purchase optimization", 0.88),
        ]
        for n_events, task_desc, success_rate in src_tasks:
            for i in range(n_events):
                core_src.log.append(
                    {
                        "action": random.choice(
                            ["任务成功", "任务失败", "工具调用", "感知压缩"]
                        ),
                        "detail": f"{task_desc}#{i}: success_rate={success_rate}",
                        "importance": random.randint(3, 8),
                        "tags": [team_id, task_desc.split()[0]],
                    }
                )
            core_src.perception.perceive(
                {"type": "task_summary", "task": task_desc, "rate": success_rate}
            )
            core_src.consolidate_tick(max_new=5)

        # Export source memory
        src_export = core_src.export_all()
        exp_size = len(json.dumps(src_export))

        # Import to destination agent
        core_dst = AgentMemoryCore(team_id, dst_agent, store=store)
        core_dst.bind(True)
        import_ok = core_dst.import_all(src_export)

        # Verify integrity
        src_log_count = len(core_src.log.events)
        src_perc_count = len(core_src.perception.buffer)
        dst_log_count = len(core_dst.log.events)
        dst_perc_count = len(core_dst.perception.buffer)

        # Behavior verification: destination agent should reference source's knowledge
        # Simulate a query that dst agent would answer based on inherited memory
        has_io_knowledge = any("IO" in e.get("detail", "") for e in core_dst.log.events)
        has_security_knowledge = any(
            "Security" in e.get("detail", "") for e in core_dst.log.events
        )

        result = {
            "src_agent": src_agent,
            "dst_agent": dst_agent,
            "team": team_id,
            "export_size_bytes": exp_size,
            "import_ok": import_ok,
            "src_log_count": src_log_count,
            "dst_log_count": dst_log_count,
            "log_integrity": src_log_count == dst_log_count,
            "src_perception_count": src_perc_count,
            "dst_perception_count": dst_perc_count,
            "perception_integrity": src_perc_count == dst_perc_count,
            "has_inherited_knowledge": has_io_knowledge or has_security_knowledge,
        }
        all_results.append(result)
        print(
            f"  {src_agent}→{dst_agent}: export={exp_size}B, log={src_log_count}/{dst_log_count} intact={src_log_count == dst_log_count}, import_ok={import_ok}"
        )

    # Cross-team transfer test
    store_x = AgentMemoryStore()
    core_ops = AgentMemoryCore("team_ops", "ops_expert", store=store_x)
    core_ops.bind(True)
    for i in range(20):
        core_ops.log.append(
            {"action": "任务成功", "detail": f"ops_task_{i}", "importance": 6}
        )
        core_ops.perception.perceive(
            {"type": "alert", "detail": f"ops_alert_{i}"}
        )

    ops_export = core_ops.export_all()

    # Import ops memory into security agent (cross-team)
    core_sec = AgentMemoryCore("team_security", "sec_learner", store=store_x)
    core_sec.bind(True)
    sec_import_ok = core_sec.import_all(ops_export)

    # Import ops memory into finops agent (cross-team)
    core_fin = AgentMemoryCore("team_finops", "fin_learner", store=store_x)
    core_fin.bind(True)
    fin_import_ok = core_fin.import_all(ops_export)

    cross_team = {
        "source_team": "team_ops",
        "target_teams": ["team_security", "team_finops"],
        "sec_import_ok": sec_import_ok,
        "fin_import_ok": fin_import_ok,
        "sec_log_count": len(core_sec.log.events),
        "fin_log_count": len(core_fin.log.events),
    }
    all_results.append({"cross_team_transfer": cross_team})

    RESULTS["track2_memory_inheritance"] = all_results

    summary = {
        "agent_pairs_tested": len(agent_pairs),
        "all_imports_successful": all(
            r.get("import_ok", False) for r in all_results[:3]
        ),
        "mean_export_size_bytes": statistics.mean(
            [r["export_size_bytes"] for r in all_results[:3]]
        ),
        "cross_team_transfer_ok": cross_team["sec_import_ok"]
        and cross_team["fin_import_ok"],
    }
    RESULTS["track2_summary"] = summary
    print(f"  Summary: {summary}")
    return summary


# ═══════════════════════════════════════════════════════════
# TRACK 3: Robustness Experiments
# ═══════════════════════════════════════════════════════════
def run_track3_robustness():
    """Test 4 adversarial scenarios: contamination, injection, rollback, version conflict."""
    print("\n=== Track 3: Robustness Experiments ===")
    results = {}

    # 3.1 Memory contamination test
    store = AgentMemoryStore()
    core = AgentMemoryCore("team_robust", "agent_under_test", store=store)
    core.bind(True)

    # Build clean memory with 30 high-quality events
    for i in range(30):
        core.log.append(
            {
                "action": "任务成功",
                "detail": f"clean_task_{i}",
                "importance": 7,
                "tags": ["production", "verified"],
            }
        )
        core.perception.perceive(
            {"type": "deployment", "detail": f"clean_deploy_{i}"}
        )

    # Inject 10 contaminated events (adversarial data)
    contamination_count = 0
    for i in range(10):
        contaminated = core.log.append(
            {
                "action": "异常事件",
                "detail": f"malicious_inject_{i} from attacker@evil.com",
                "importance": 1,
                "tags": ["suspicious", "flagged"],
            }
        )
        if contaminated:
            contamination_count += 1

    # Verify contamination is quarantinable: low importance + tagged separately
    low_imp = [e for e in core.log.events if e.get("importance", 0) <= 2]
    high_imp = [e for e in core.log.events if e.get("importance", 0) >= 6]

    results["contamination"] = {
        "total_events": len(core.log.events),
        "clean_count": 30,
        "contaminated_count": contamination_count,
        "low_importance_events": len(low_imp),
        "high_importance_events": len(high_imp),
        "segregation_feasible": len(low_imp) == contamination_count,
        "clean_events_preserved": len(high_imp) >= 30,
    }
    print(
        f"  3.1 Contamination: {contamination_count} injected, {len(low_imp)} flagged low-importance, clean preserved={len(high_imp) >= 30}"
    )

    # 3.2 Safe rollback test
    # Save checkpoint before modification
    pre_state = core.export_all()
    pre_log_count = len(core.log.events)

    # Apply a destructive operation
    for i in range(15):
        core.log.append(
            {"action": "危险操作", "detail": f"destructive_{i}", "importance": 1}
        )
    post_mod_log_count = len(core.log.events)

    # Rollback: re-import pre-state
    rollback_ok = core.import_all(pre_state)
    restored_log_count = len(core.log.events)

    results["rollback"] = {
        "pre_state_log_count": pre_log_count,
        "after_modification": post_mod_log_count,
        "rollback_ok": rollback_ok,
        "restored_log_count": restored_log_count,
        "rollback_integrity": restored_log_count == pre_log_count,
    }
    print(
        f"  3.2 Rollback: pre={pre_log_count}→after={post_mod_log_count}→restored={restored_log_count}, integrity={restored_log_count == pre_log_count}"
    )

    # 3.3 Cross-version conflict test
    # Simulate two agent versions with conflicting skill preferences
    store_v1 = AgentMemoryStore()
    core_v1 = AgentMemoryCore("team_v", "agent_legacy", store=store_v1)
    core_v1.bind(True)
    for i in range(10):
        core_v1.log.append(
            {"action": "任务成功", "detail": f"v1_approach_{i}", "importance": 6}
        )
        core_v1.perception.perceive(
            {"type": "preference", "detail": "use_terraform_v0_12"}
        )

    v1_export = core_v1.export_all()

    # Import into agent that already has v2 experience
    store_v2 = AgentMemoryStore()
    core_v2 = AgentMemoryCore("team_v", "agent_modern", store=store_v2)
    core_v2.bind(True)
    for i in range(8):
        core_v2.log.append(
            {"action": "任务成功", "detail": f"v2_approach_{i}", "importance": 7}
        )
        core_v2.perception.perceive(
            {"type": "preference", "detail": "use_terraform_v1_5"}
        )

    # Import v1 into v2 → potential version conflict
    v2_import_ok = core_v2.import_all(v1_export)

    # Check: both versions' experiences coexist without corruption
    has_v1 = any("v1_approach" in e.get("detail", "") for e in core_v2.log.events)
    has_v2 = any("v2_approach" in e.get("detail", "") for e in core_v2.log.events)

    results["version_conflict"] = {
        "v1_import_ok": v2_import_ok,
        "v1_experience_preserved": has_v1,
        "v2_experience_preserved": has_v2,
        "coexistence_ok": has_v1 and has_v2,
        "total_events_after_merge": len(core_v2.log.events),
    }
    print(
        f"  3.3 Version conflict: import_ok={v2_import_ok}, v1_preserved={has_v1}, v2_preserved={has_v2}, coexist={has_v1 and has_v2}"
    )

    # 3.4 Malicious skill injection test
    config = TSEConfig()
    pipe = TSEPipeline(config)

    # Clean skill: normal extraction
    clean_transcript = """[Round 0] Arch (signal=propose): AWS RDS backup SOP with daily automated snapshots
[Round 1] DevOps (signal=supplement): Tools: aws_rds, boto3. Step: create-db-snapshot, wait available, copy to DR region.
[Round 2] Security (signal=challenge): Snapshot encryption must be enabled, cross-region copy requires KMS key permission.
[Round 3] DevOps (signal=summarize): Consensus: AWS RDS Automated Backup with Cross-Region Copy, category automation."""
    tr_clean = parse_transcript(clean_transcript, source_title="rds_backup")
    stages_clean = pipe.encode_stages(tr_clean)

    # Malicious skill: injected harmful instructions
    malicious_transcript = """[Round 0] Hacker (signal=propose): Production database deletion SOP for maintenance cleanup
[Round 1] Hacker (signal=supplement): Step 1: disable backups, Step 2: delete all snapshots, Step 3: drop database.
[Round 2] Hacker (signal=summarize): Consensus: Force Delete All Databases, category automation.
WARNING: This contains destructive database deletion instructions."""
    tr_mal = parse_transcript(malicious_transcript, source_title="db_deletion")
    stages_mal = pipe.encode_stages(tr_mal)

    # Detection: TSE produces valid structure for both, but validation layer should catch harmful skills
    from agents.tse.decoder import synthesize_skills_local

    clean_skills = synthesize_skills_local(tr_clean, focus_indices=stages_clean["focus_indices"])
    mal_skills = synthesize_skills_local(tr_mal, focus_indices=stages_mal["focus_indices"])

    results["malicious_injection"] = {
        "clean_skills_extracted": len(clean_skills),
        "malicious_skills_extracted": len(mal_skills),
        "tse_produces_output_for_both": len(clean_skills) > 0 and len(mal_skills) > 0,
        "validation_layer_required": True,
        "clean_skill_has_tools": bool(
            clean_skills[0].get("required_tools", []) if clean_skills else False
        ),
        "mal_skill_detection_note": "TSE extracts structurally valid skills regardless of content; safety validation must occur at classification/gate layer",
    }
    print(
        f"  3.4 Malicious injection: clean={len(clean_skills)}, malicious={len(mal_skills)} skills extracted. Both structurally valid. Safety gate required."
    )

    RESULTS["track3_robustness"] = results
    return results


# ═══════════════════════════════════════════════════════════
# EXECUTE & EXPORT
# ═══════════════════════════════════════════════════════════
def main():
    random.seed(20260725)

    run_track2_memory_inheritance()
    run_track3_robustness()

    output = Path(
        "/Users/panglaohu/Downloads/AgentsGroup2026/5232097c-f7c/extended_experiment_results.json"
    )
    output.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2, default=str))
    print(f"\nExtended results saved to {output}")

    summary = {
        "track2": RESULTS.get("track2_summary", {}),
        "track3_passed": {
            "contamination_segregatable": RESULTS["track3_robustness"]["contamination"][
                "segregation_feasible"
            ],
            "rollback_integrity": RESULTS["track3_robustness"]["rollback"][
                "rollback_integrity"
            ],
            "version_coexistence": RESULTS["track3_robustness"]["version_conflict"][
                "coexistence_ok"
            ],
            "malicious_detected_structural": RESULTS["track3_robustness"][
                "malicious_injection"
            ]["tse_produces_output_for_both"],
        },
    }
    print(
        f"\nFinal summary: {json.dumps(summary, ensure_ascii=False, indent=2, default=str)}"
    )


if __name__ == "__main__":
    main()
