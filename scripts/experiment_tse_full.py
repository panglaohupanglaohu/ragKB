# -*- coding: utf-8 -*-
"""Complete experiment: TSE extraction → classification → report."""

import asyncio, json, sys, time

sys.path.insert(0, "/Users/panglaohu/Downloads/AgentsGroup2026/src/backend/agents")

from tse import get_tse_pipeline
from tse.transcript import parse_transcript
from tse.config import TSEConfig


async def run_experiments():
    results = []

    # ── Discussion 1: AWS ES scaling ──
    disc1 = """Topic: 实现 AWS ES 实例缩放的 shell+aws-cli 运维脚本

[Round 0] 运维 Leader (moderator, signal=supplement): 本场讨论采用 ORID 四层结构：①客观事实 ②风险直觉 ③方案对立辩论 ④五指决策。今天讨论 AWS ES 集群的扩缩容策略。请各位从各自专业角度分析当前ES集群的状态和扩缩容的最佳路径。

[Round 1] 上云架构师 (architect, signal=supplement): 从架构角度看，当前ES集群部署在us-east-1的三个可用区，采用i3en.2xlarge实例类型。单节点存储容量3.5TB，数据总量约20TB分布在6个数据节点上。扩缩容路径有两条：纵向(升配实例类型到i3en.4xlarge)和横向(增加数据节点)。纵向升配简单快速但单节点容量上限固定；横向扩容需要手动平衡分片迁移，可能导致热分片问题。

[Round 1] 运维操作员 (devops, signal=supplement): 从运维角度，当前ES集群在高峰期的CPU使用率达到85%，JVM heap压力超过75%，segment count在部分索引上达到2000+。扩缩容的运维操作风险包括：索引迁移期间的IO压力、节点下线时replica lag导致的数据一致性风险、以及变更窗口内的监控盲点。建议扩容前先执行dry-run脚本模拟，并建立回滚窗口。

[Round 1] 巡检监控员 (monitoring, signal=supplement): 监控数据显示，ES集群的_search和_bulk延迟在高峰期分别达到350ms和80ms，超过SLO阈值200ms和50ms。CloudWatch告警已经触发3次CPU高负载告警。扩容后的监控验证需要覆盖：node-level CPU/memory、index-level search rate、shard-level doc count分布。特别是跨可用区的流量成本增加需要单独监控。

[Round 1] 成本优化成员 (cost-optimizer, signal=supplement): 当前ES集群月度成本约为$8,400，其中EC2实例$5,200、EBS存储$2,100、数据传输$1,100。横向扩容到9节点月度成本将增至约$12,600；纵向升配到i3en.4xlarge(6节点)约$10,200。考虑RI/Savings Plan折扣(三年R15约30%off)，横向扩容实际增加约40%，纵向约25%。建议在模拟演练后选择成本最低且能满足未来12个月增长需求的方案。

[Round 2] 上云架构师 (architect, signal=supplement): 基于第一轮的事实盘点，我建议采用横向扩容+分片预分配策略。具体方案：扩容到9节点后，使用ilm policy将索引预先分配到新增节点，通过index.routing.allocation.require._name控制分片路由。同时将replica数调整为2（当前为1），确保至少2个副本。

[Round 2] 运维操作员 (devops, signal=challenge): 横向扩容存在三个风险需要讨论：第一，分片分配后再平衡会触发大量IO，可能导致搜索延迟飙升；第二，新增节点后旧节点不会自动卸载分片，需要主动执行reroute；第三，跨可用区数据同步在扩容期间的带宽压力。我们需要先在非生产环境演练。

[Round 2] 巡检监控员 (monitoring, signal=agree): 同意运维操作员的观点。建议在扩容前设置CloudWatch Dashboard专门监控：cpu_utilization > 70%触发告警、JVMMemoryPressure > 75%、ClusterStatus(Red/Yellow)实时告警。并配置OpenSearch的slow log记录扩容期间的慢查询，用于验收。
"""

    # ── Discussion 2: CentOS to Rocky migration ──
    disc2 = """Topic: 如何将OS从CentOS升级到Rocky合适版本

[Round 0] 运维 Leader (moderator, signal=supplement): 今天讨论如何将生产环境OS从CentOS升级到Rocky Linux。当前有约120台CentOS 7实例分布在fleet中，CentOS 7已于2024年6月EOL。迁移到Rocky Linux 9是最佳替代方案，但也有Rocky 8的保守选项。

[Round 1] 上云架构师 (architect, signal=supplement): 从兼容性角度，Rocky Linux 9是RHEL 9的下游，内核版本5.14+，gcc 11，Python 3.9为默认。但部分老旧应用（特别是基于Python 2的遗留代码和基于CentOS 7特定glibc 2.17编译的二进制文件）可能需要额外适配。建议先对应用清单做兼容性审计，按应用依赖关系分组迁移。

[Round 1] 运维操作员 (devops, signal=supplement): 运维角度最担心两个问题：一是原地升级(Leapp工具)的可靠性——历史上CentOS 7→Rocky 8的Leapp迁移成功率约85%，15%出现了yum源残留、内核模块不兼容、或selinux策略冲突。二是迁移窗口——120台机器一次全部迁移的话，故障域太大。建议分批迁移：第1批10台非核心服务（验证流程）→第2批30台→第3批80台。

[Round 1] 巡检监控员 (monitoring, signal=supplement): 迁移期间的监控需要三种模式：迁移前基线（当前CentOS 7的正常指标）、迁移中实时监控（cpu/iowait/磁盘使用率/服务健康check）、迁移后对比验证（确认新OS下性能不低于旧OS的95%）。特别关注：systemd服务启动顺序变化、selinux denials、和新的firewalld规则。

[Round 2] 上云架构师 (architect, signal=supplement): 我建议采用Rocky Linux 9作为目标版本，原因：1) 内核5.14+对NVMe和XFS做了大量性能优化；2) systemd 252+的启动并行度提升约30%；3) 安全支持周期到2032年(vs Rocky 8到2029年)。但需要处理：cgroup v2迁移（原CentOS 7使用cgroup v1），以及某些Java应用对较新glibc的兼容性。

[Round 2] 运维操作员 (devops, signal=challenge): Rocky 9有两个风险需要特别关注：OpenSSL 3.0的API变更可能导致某些TLS证书链验证失败（特别是内部自签名CA）；以及NetworkManager替代了传统network-scripts，静态IP和bonding配置需要重写。建议先在staging环境用Packer构建Rocky 9的AMI模板，自动化整个迁移流程。

[Round 2] 成本优化成员 (cost-optimizer, signal=supplement): 迁移成本估算：120台×平均1h运维工时=$4,800（按$40/h），加上staging测试环境EC2成本约$300/月×3月=$900。如果使用AWS Systems Manager Automation来批量迁移，可以将运维工时降低60%。构建Packer+Ansible自动化流水线的前期开发成本约$1,200，但后续可复用。

[Round 3] 运维 Leader (moderator, signal=supplement): 经过两轮讨论，共识方向明确：采用Rocky Linux 9作为目标版本，通过Packer+Ansible自动化构建AMI，分3批迁移（10→30→80），每批间隔2周。运维团队负责Leapp升级脚本和rollback方案。成本控制在$7,000以内。
"""

    config = TSEConfig()
    pipe = get_tse_pipeline(config)
    loaded = pipe.try_load_latest_checkpoint()

    print("=" * 70)
    print("TSE Skill Extraction Experiment Report")
    print("=" * 70)
    print(
        f"Config: embed_dim={config.embed_dim}, tcn_hidden={config.tcn_hidden_dim}, dilations={config.dilations}"
    )
    print(
        f"Checkpoint: {'loaded (epoch ' + str(pipe.checkpoint_meta.get('epoch', '?')) + ')' if loaded else 'NOT FOUND (cold start)'}"
    )
    if loaded:
        print(
            f"  train_loss={pipe.checkpoint_meta.get('train_loss', '?')} "
            f"val_cat_acc={pipe.checkpoint_meta.get('val_cat_acc', '?')} "
            f"val_tools_f1={pipe.checkpoint_meta.get('val_tools_f1', '?')}"
        )

    for idx, (title, text) in enumerate(
        [
            ("AWS ES 实例缩放", disc1),
            ("CentOS→Rocky迁移", disc2),
        ]
    ):
        print(f"\n{'─' * 70}")
        print(f"Experiment {idx + 1}: {title}")
        print(f"{'─' * 70}")

        t0 = time.perf_counter()
        tr = parse_transcript(text, source_title=title)
        stages = pipe.encode_stages(tr)
        stage_time = (time.perf_counter() - t0) * 1000

        from tse.decoder import synthesize_skills_local
        from tse.heads import MultiTaskHeads

        heads = MultiTaskHeads(
            hidden_dim=config.tcn_hidden_dim, seed=config.hash_seed + 3
        )
        try:
            head_pred = heads.predict(stages["skill_repr"])
        except:
            head_pred = {"category": "general", "required_tools": []}

        skills = synthesize_skills_local(
            tr,
            focus_indices=stages["focus_indices"],
            category_hint=str(head_pred.get("category", "general")),
            tools_hint=list(head_pred.get("required_tools", [])),
        )

        print(f"Pipeline latency: {stage_time:.1f}ms")
        print(f"  Stage1 (encoder): {stages['timings']['stage1_encoder_ms']:.1f}ms")
        print(f"  Stage2 (TCN):     {stages['timings']['stage2_tcn_ms']:.1f}ms")
        print(f"  Stage3 (attn):    {stages['timings']['stage3_attention_ms']:.1f}ms")
        print(
            f"Utterances: {len(tr.messages)}, Focus indices: {stages['focus_indices']}"
        )
        print(f"Skills extracted: {len(skills)}")

        for si, skill in enumerate(skills):
            print(f"\n  Skill {si + 1}:")
            for field in [
                "name",
                "description",
                "category",
                "instructions",
                "required_tools",
            ]:
                val = skill.get(field, "")
                if field == "instructions":
                    val = val[:200] + ("..." if len(val) > 200 else "")
                print(f"    {field}: {val}")

        results.append(
            {
                "topic": title,
                "utterances": len(tr.messages),
                "focus_indices": stages["focus_indices"],
                "skills": skills,
                "latency_ms": stage_time,
                "timings": stages["timings"],
            }
        )

    # ── Summary ──
    print(f"\n{'=' * 70}")
    print("Summary")
    print(f"{'=' * 70}")
    total_skills = sum(len(r["skills"]) for r in results)
    print(f"Discussions processed: {len(results)}")
    print(f"Total skills extracted: {total_skills}")
    print(f"Avg latency: {sum(r['latency_ms'] for r in results) / len(results):.1f}ms")
    print(f"Avg skills/discussion: {total_skills / len(results):.1f}")

    return results


results = asyncio.run(run_experiments())
