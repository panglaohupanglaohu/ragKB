# -*- coding: utf-8 -*-
"""Run single-agent skill lifecycle experiments using real project code paths.

Produces structured experiment data for the rewritten paper.
"""
from __future__ import annotations
import json, sys, time, csv, math, tempfile, random, statistics, asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

BACKEND = Path("/Users/panglaohu/Downloads/AgentsGroup2026/src/backend")
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agents.tse import (
    TSEConfig, TSEPipeline, extract_skill_moments, parse_transcript,
    validate_skill_fields, parse_skills_payload,
)
from agents.tse.tcn import TCNTemporalModule
from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore

RESULTS = {}

# ── Sample deliberation transcripts ──────────────────────────

DISCUSSIONS = [
    ("aws_es_scaling",
     """[Round 0] 架构师 (architect, signal=propose): 今天评估AWS Elasticsearch集群的自动扩缩容策略。需要产出可复用的技能定义。
[Round 1] 运维工程师 (devops, signal=supplement): 目前集群3主节点+6数据节点，高峰CPU持续85%+，IO等待明显。工具清单: aws_cli, cloudwatch, boto3, terraform。
[Round 2] 运维工程师 (devops, signal=propose): 技能步骤: 1) 配置CloudWatch告警CPU≥70%保持5分钟 2) 调用ES UpdateDomainConfig增加数据节点 3) 等待集群状态变绿 4) 记录变更日志。
[Round 3] 安全架构师 (security, signal=challenge): 扩容要注意IAM最小权限、禁止周五16:00后变配、必须保留回滚快照。建议增加审批门禁。
[Round 4] 架构师 (architect, signal=summarize): 达成共识——技能名 AWS ES Auto-Scaling with Safety Gate，类别 automation，核心步骤已确认。"""),

    ("centos_rocky_migration",
     """[Round 0] 系统管理员 (admin, signal=propose): 讨论CentOS 7到Rocky Linux 8的批量迁移方案，需要形成标准化SOP技能。
[Round 1] 安全工程师 (security, signal=supplement): OpenSSL从1.1升级到3.0需要注意兼容性。NetworkManager配置迁移是另一个风险点。工具: leapp, ansible, rsync, dnf。
[Round 2] 运维工程师 (devops, signal=propose): 分批策略: 先10%低风险节点→验证48h→30%→验证24h→80%→全量。每批需回滚方案和健康检查。
[Round 3] DBA (dba, signal=challenge): 数据库节点迁移需要额外注意：先在只读副本验证、确保数据目录独立备份、迁移窗口至少4小时。
[Round 4] 系统管理员 (admin, signal=summarize): 共识: 技能名 CentOS→Rocky分批迁移SOP，类别 automation，分批比例与验证窗口如上。"""),

    ("cost_ri_governance",
     """[Round 0] 财务分析师 (finops, signal=propose): AWS Reserved Instance购买与治理缺乏标准流程，需要形成可复用技能。
[Round 1] 云架构师 (architect, signal=supplement): 当前覆盖EC2/RDS/ES/OpenSearch四类资源。RI购买分标准RI和可转换RI。工具: aws_ce, python_boto3, terraform。
[Round 2] 云架构师 (architect, signal=propose): 技能流程: 1) 拉取上月按需用量 2) 计算RI覆盖缺口 3) 对比1年/3年/标准/可转换的TCO 4) 生成购买建议 5) 审批后通过Terraform执行。
[Round 3] 安全架构师 (security, signal=challenge): RI治理需考虑: 禁止跨账号共享RI信息、购买审批需双签、月度RI利用率<80%需自动告警并建议转售。
[Round 4] 财务分析师 (finops, signal=summarize): 共识技能名 Cloud RI Governance & Purchase，类别 automation+domain_knowledge。"""),

    ("monitoring_rollback",
     """[Round 0] SRE (sre, signal=propose): 需要建立统一的监控告警回滚演练技能——不是每次手动操作。
[Round 1] 运维工程师 (devops, signal=supplement): 监控栈: CloudWatch+Prometheus+Grafana。回滚涉及: 代码回滚(git revert)、配置回滚(terraform state rm)、数据库回滚(快照恢复)。
[Round 2] SRE (sre, signal=propose): 演练流程: 1) 注入故障(CPU拉高/磁盘满/网络分区) 2) 验证告警触发 3) 执行对应runbook 4) 验证恢复 5) 记录RTO/RPO。
[Round 3] 安全工程师 (security, signal=challenge): 演练不能影响生产——使用独立演练环境或shadow traffic。演练后必须清理环境，严格权限回收。
[Round 4] SRE (sre, signal=summarize): 共识技能名 Monitoring Rollback Drill，类别 automation+monitoring，每季度至少一次。"""),

    ("terraform_change_gate",
     """[Round 0] 平台工程师 (platform, signal=propose): Terraform变更目前缺少前置检查门禁，需要标准化变更风险评估技能。
[Round 1] 安全工程师 (security, signal=supplement): 变更前检查: IAM policy变更影响评估、安全组规则变更分析、敏感资源(DB/密钥)的额外审批。工具: terraform plan, iamlint, tfsec, checkov。
[Round 2] 平台工程师 (platform, signal=propose): 门禁流程: 1) terraform plan生成变更diff 2) iamlint+tfsec+checkov扫描 3) 变更影响矩阵(资源删除/替换/原地更新) 4) 高风险变更额外审批 5) 通过后apply。
[Round 3] DBA (dba, signal=challenge): 数据库相关变更额外要求: RDS参数组变更需先在只读副本验证、禁止直接删除RDS实例、存储加密不能降级。
[Round 4] 平台工程师 (platform, signal=summarize): 共识技能名 Terraform Change Gate，类别 automation+security，纳入CI/CD流水线。"""),
]

# ── Experiment 1: TSE Extraction Latency & Stage Breakdown ──

def run_tse_latency_experiment():
    print("\n=== Experiment 1: TSE Extraction Latency ===")
    config = TSEConfig()
    pipe = TSEPipeline(config)
    results = []
    for disc_id, transcript in DISCUSSIONS:
        # warm-up
        for _ in range(5):
            extract_skill_moments(transcript, source_title=disc_id)
        # measurement: 10 runs
        latencies = []
        stage_timings = {"encoder": [], "tcn": [], "attention": []}
        for _ in range(10):
            t0 = time.perf_counter()
            tr = parse_transcript(transcript, source_title=disc_id)
            stages = pipe.encode_stages(tr)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)
            stage_timings["encoder"].append(stages.get("stage_timings", {}).get("encoder_ms", 0))
            stage_timings["tcn"].append(stages.get("stage_timings", {}).get("tcn_ms", 0))
            stage_timings["attention"].append(stages.get("stage_timings", {}).get("attention_ms", 0))
        utt_count = stages["embeddings"].shape[0]
        focus = len(stages["focus_indices"])
        results.append({
            "discussion": disc_id,
            "utterances": utt_count,
            "focus_utterances": focus,
            "latency_ms_mean": round(statistics.mean(latencies), 2),
            "latency_ms_std": round(statistics.stdev(latencies), 3),
            "encoder_ms": round(statistics.mean(stage_timings["encoder"]), 2),
            "tcn_ms": round(statistics.mean(stage_timings["tcn"]), 2),
            "attention_ms": round(statistics.mean(stage_timings["attention"]), 2),
            "receptive_field": TCNTemporalModule.receptive_field(3, 3),
        })
    RESULTS["tse_latency"] = results
    for r in results:
        print(f"  {r['discussion']:25s}: {r['utterances']}utt→{r['focus_utterances']}focus "
              f"| total {r['latency_ms_mean']}ms "
              f"(enc {r['encoder_ms']} tcn {r['tcn_ms']} attn {r['attention_ms']})")

# ── Experiment 2: Attention Weight Distribution ──

def run_attention_experiment():
    print("\n=== Experiment 2: Cross-Attention Weight Analysis ===")
    config = TSEConfig(top_k_utterances=8)
    pipe = TSEPipeline(config)
    results = []
    for disc_id, transcript in DISCUSSIONS:
        tr = parse_transcript(transcript, source_title=disc_id)
        stages = pipe.encode_stages(tr)
        attn = stages["attn_weights"]  # (5, n)
        n = attn.shape[1]
        # Compute entropy and max-concentration
        field_entropy = {}
        field_max = {}
        fields = ["name", "description", "category", "tools", "instructions"]
        for fi, field in enumerate(fields):
            row = attn[fi]
            row = row / (row.sum() + 1e-9)
            ent = -sum(p * math.log(max(p, 1e-9)) for p in row)
            max_ent = math.log(n)
            field_entropy[field] = round(ent / max_ent, 3)  # normalized
            field_max[field] = round(float(row.max()), 3)
        # concentration = 1 - normalized_entropy
        concentration = {f: round(1 - field_entropy[f], 3) for f in fields}
        results.append({
            "discussion": disc_id,
            "utterances": n,
            "normalized_entropy": field_entropy,
            "max_weight": field_max,
            "concentration": concentration,
        })
    RESULTS["attention"] = results
    for r in results:
        conc = r["concentration"]
        avg_c = round(statistics.mean(conc.values()), 3)
        print(f"  {r['discussion']:25s}: avg_conc={avg_c} "
              f"top_field={max(conc,key=conc.get)}={conc[max(conc,key=conc.get)]}")

# ── Experiment 3: Skill Classification Lifecycle ──

def run_classification_experiment():
    print("\n=== Experiment 3: Skill Classification & Graduation ===")
    from agents.skill_classifier import classify, classify_with_history, Classification, ClassificationStore
    import tempfile

    # Simulate 5 skills through lifecycle stages
    skills_data = [
        {"id": "sk_new_extracted", "name": "AWS ES Auto-Scaling", "effectiveness": 0.0, "usage": 0, "lifecycle": "draft"},
        {"id": "sk_verified_ops",   "name": "CentOS→Rocky Migration", "effectiveness": 0.72, "usage": 45, "lifecycle": "verified", "adopted": ["team_ops", "team_db"]},
        {"id": "sk_team_specific",  "name": "Cost RI Advisor",       "effectiveness": 0.68, "usage": 120, "lifecycle": "verified", "adopted": ["team_finops"]},
        {"id": "sk_degrading",      "name": "Old Monitoring Setup",  "effectiveness": 0.28, "usage": 8, "lifecycle": "published"},
        {"id": "sk_stale",          "name": "Legacy Terraform 0.12", "effectiveness": 0.55, "usage": 0, "lifecycle": "degraded", "stale_days": 120},
    ]
    now_dt = __import__('datetime').datetime(2026, 6, 12, tzinfo=__import__('datetime').timezone.utc)

    results = []
    for sk in skills_data:
        sk_dict = {
            "skill_id": sk["id"], "name": sk["name"],
            "effectiveness": sk["effectiveness"],
            "lifecycle_stage": sk["lifecycle"],
            "adopted_by": sk.get("adopted", []),
            "origin_team_id": "team_ops",
            "usage_count": sk["usage"],
            "last_used_at": (now_dt - __import__('datetime').timedelta(days=sk.get("stale_days", 5))).isoformat() if sk.get("stale_days") else now_dt.isoformat(),
        }
        usage_ev = {}
        if sk["usage"] > 0:
            if sk.get("adopted"):
                # distribute usage across teams
                n_teams = len(sk["adopted"])
                usage_ev = {"team_usage": {t: sk["usage"] // n_teams for t in sk["adopted"]}}
            else:
                usage_ev = {"team_usage": {"team_ops": sk["usage"]}}
        trial = {"meets_rubric": sk["effectiveness"] >= 0.6, "gate_ok": sk["lifecycle"] == "verified"}

        instant = classify(sk_dict, usage_ev, trial, now=now_dt)
        # Simulate 3 cycle graduation (each cycle re-classifies with history)
        hist = None
        for cycle in range(3):
            hist = classify_with_history(hist, sk_dict, usage_ev, trial, now=now_dt)
            if hist.get("event"):
                break
        results.append({
            "skill": sk["name"],
            "instant": instant["classification"],
            "after_cycles": hist["classification"],
            "streak": hist["streak"],
            "grace": hist["grace"],
            "event": (hist.get("event") or {}).get("type"),
            "reasons": instant["reasons"][:2],
        })
    RESULTS["classification"] = results
    for r in results:
        evt = r["event"] or "—"
        print(f"  {r['skill'][:30]:30s}: {r['instant']:>10s}→{r['after_cycles']:<10s} (event: {evt})")

# ── Experiment 4: Memory Consolidation & Forget Cycles ──

def run_memory_consolidation_experiment():
    print("\n=== Experiment 4: Memory Consolidation & Forgetting ===")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        store = AgentMemoryStore(Path(tmp))
        core = AgentMemoryCore("team_mem", "agent_test", store=store)
        core.bind(True)

        # Seed 40 events with varying importance
        events_data = []
        for i in range(40):
            imp = random.randint(3, 9)
            core.log.append({
                "action": random.choice(["任务成功","任务失败","对话","工具调用","反思固化","感知压缩"]),
                "detail": f"实验事件#{i}: 重要性{imp}",
                "importance": imp,
                "tags": [random.choice(["扩容","迁移","治理","监控","安全"])],
            })
            events_data.append({"i": i, "importance": imp})

        # Consolidation cycle × 5
        consol_cycles = []
        for cycle in range(5):
            cr = core.consolidate_tick(max_new=4)
            fr = core.forget_tick()
            consol_cycles.append({
                "cycle": cycle + 1,
                "consolidated": cr["consolidated"],
                "forgotten": fr["forgotten"],
                "semantic_count": len(core.semantic.active()),
                "live_events": len([e for e in core.log.events if not e.get("forgotten_at")]),
                "tone": core.affect.tone_hint()[:40],
            })
            # Inject fitness feedback
            core.apply_fitness(success=(cycle % 2 == 0), magnitude=0.3 + cycle * 0.1, drift=True)

        RESULTS["memory_cycles"] = consol_cycles
        for c in consol_cycles:
            print(f"  cycle {c['cycle']}: +{c['consolidated']} consolidate "
                  f"-{c['forgotten']} forget | semantic={c['semantic_count']} "
                  f"live={c['live_events']} | {c['tone']}")

# ── Experiment 5: SkillRouter routing quality ──

def run_router_experiment():
    print("\n=== Experiment 5: SkillRouter Retrieval Quality ===")
    # Use the skill library test data patterns
    # We'll benchmark the _stage1_retrieve and _stage2_rerank scoring on synthetic skill pools
    from agents.skill_router import SkillRouter

    router = SkillRouter()
    queries = [
        ("AWS ES自动扩缩容", "automation"),
        ("CentOS系统迁移到Rocky", "automation"),
        ("RI购买和成本优化", "domain_knowledge"),
        ("监控告警回滚演练", "monitoring"),
        ("Terraform变更安全检查", "security"),
    ]
    # Build a synthetic pool of 30 skills
    pool = []
    pool_skills = [
        ("AWS ES Auto-Scaling", "自动化调整ES节点数", "automation"),
        ("CentOS→Rocky分批迁移", "分批迁移SOP与回滚", "automation"),
        ("Cloud RI Governance", "RI购买与利用率治理", "domain_knowledge"),
        ("Monitoring Rollback Drill", "监控告警回滚演练", "monitoring"),
        ("Terraform Change Gate", "变更风险门禁检查", "automation"),
        ("Cost Analysis Dashboard", "多维度成本分析面板", "domain_knowledge"),
        ("IAM Policy Auditor", "IAM策略合规审计", "security"),
        ("Database Backup SOP", "数据库备份标准流程", "domain_knowledge"),
        ("CI/CD Pipeline Debug", "流水线排障与修复", "development"),
        ("Log Aggregation Setup", "日志聚合与检索配置", "monitoring"),
        ("Network ACL Review", "网络ACL规则审查", "security"),
        ("Container Image Scan", "容器镜像安全扫描", "security"),
        ("Incident Response Runbook", "故障响应标准流程", "general"),
        ("SSL Certificate Renewal", "SSL证书自动续期", "automation"),
        ("Data Migration Toolkit", "数据迁移工具集", "domain_knowledge"),
        ("Performance Benchmark Suite", "性能基准测试套件", "development"),
        ("Alert Noise Reduction", "告警降噪与聚合", "monitoring"),
        ("Secret Rotation Automation", "密钥轮转自动化", "security"),
        ("Capacity Planning Model", "容量规划模型", "domain_knowledge"),
        ("Deployment Rollback SOP", "部署回滚标准流程", "general"),
        ("Compliance Audit Trail", "合规审计追踪", "security"),
        ("API Gateway Config", "API网关配置管理", "development"),
        ("Redis Cluster Ops", "Redis集群运维", "domain_knowledge"),
        ("GitOps Workflow Setup", "GitOps工作流配置", "development"),
        ("Chaos Engineering Drill", "混沌工程演练", "general"),
        ("Resource Tagging Policy", "资源标签策略", "domain_knowledge"),
        ("VPC Peering Setup", "VPC互联配置", "development"),
        ("WAF Rules Management", "WAF规则管理", "security"),
        ("Backup Restore Test", "备份恢复测试", "general"),
        ("Service Quota Monitor", "服务配额监控", "monitoring"),
    ]
    for name, desc, cat in pool_skills:
        pool.append({
            "skill_id": name.lower().replace(" ", "_")[:40],
            "name": name, "description": desc, "category": cat,
            "instructions": f"步骤1 步骤2 步骤3 关于{name}的操作步骤",
            "required_tools": ["aws_cli", "terraform"][:random.randint(1,2)],
            "lifecycle_stage": random.choice(["verified", "published", "draft", "solidified"]),
        })

    # Monkey-patch the pool into router
    router._skill_library = type("obj", (object,), {"browse": lambda self, team_id="": pool})()

    results = []
    for query, expected_cat in queries:
        # Run routing
        t0 = time.perf_counter()
        session = router.route(query, team_id="team_test", agent_id="test_agent", top_k=5)
        elapsed = (time.perf_counter() - t0) * 1000
        top1 = session.results[0] if session.results else None
        top1_cat = top1.category if top1 else "none"
        top1_score = top1.score if top1 else 0
        # Check if expected category in top 5
        cats_in_top5 = [r.category for r in session.results]
        hit = expected_cat in cats_in_top5
        results.append({
            "query": query,
            "expected_category": expected_cat,
            "top1_name": top1.name if top1 else "?",
            "top1_category": top1_cat,
            "top1_score": round(top1_score, 3),
            "expected_in_top5": hit,
            "latency_ms": round(elapsed, 1),
            "stage1_ms": session.stage1_ms,
            "stage2_ms": session.stage2_ms,
        })
    RESULTS["router"] = results
    hits = sum(1 for r in results if r["expected_in_top5"])
    print(f"  Top-5 relevance: {hits}/{len(results)}")
    for r in results:
        print(f"  {r['query'][:30]:30s}: top1={r['top1_name'][:25]:25s} "
              f"cat={r['top1_category']:>15s} score={r['top1_score']:.3f} "
              f"hit={r['expected_in_top5']} | {r['latency_ms']:.1f}ms")

# ── Export & Print Summary ──

def main():
    random.seed(20260724)
    run_tse_latency_experiment()
    run_attention_experiment()
    run_classification_experiment()
    run_memory_consolidation_experiment()
    run_router_experiment()

    output = Path("/Users/panglaohu/OpenWorker/5232097c-f7c/experiment_results.json")
    output.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2, default=str))
    print(f"\nResults saved to {output}")
    print(f"\nSummary statistics:")
    tse_lat = [r["latency_ms_mean"] for r in RESULTS["tse_latency"]]
    print(f"  TSE mean latency: {statistics.mean(tse_lat):.1f}ms (±{statistics.stdev(tse_lat):.1f}) across {len(tse_lat)} discussions")
    attn_conc = []
    for r in RESULTS["attention"]:
        attn_conc.extend(r["concentration"].values())
    print(f"  Attention concentration: {statistics.mean(attn_conc):.3f} (uniform=0.0, focused=1.0)")
    cls_events = [r["event"] for r in RESULTS["classification"] if r["event"]]
    print(f"  Classification events: {len(cls_events)}/{len(RESULTS['classification'])} skills had graduation/demotion")
    mem_final = RESULTS["memory_cycles"][-1]
    print(f"  Memory final: {mem_final['semantic_count']} semantic claims, {mem_final['live_events']} live events, forgot {mem_final['forgotten']}")
    router_hits = sum(1 for r in RESULTS["router"] if r["expected_in_top5"])
    print(f"  Router Top-5 relevance: {router_hits}/{len(RESULTS['router'])}")
    router_lat = [r["latency_ms"] for r in RESULTS["router"]]
    print(f"  Router mean latency: {statistics.mean(router_lat):.1f}ms")

if __name__ == "__main__":
    main()
