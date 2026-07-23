# -*- coding: utf-8 -*-
"""TSE extraction test on Plaza discussion transcripts."""

import asyncio, json, sys, time

sys.path.insert(0, "/Users/panglaohu/Downloads/AgentsGroup2026/src/backend/agents")

from tse import get_tse_pipeline, extract_skill_moments


async def test_extraction():
    """Test TSE pipeline on Plaza discussion source text."""

    # Sample Plaza discussion text (from the AWS ES scaling discussion)
    discussion_text = """Topic: 实现 AWS ES 实例缩放的 shell+aws-cli 运维脚本

[Round 0] 运维 Leader (moderator, signal=supplement): 本场讨论采用 ORID 四层结构：①客观事实 ②风险直觉 ③方案对立辩论 ④五指决策。今天讨论 AWS ES 集群的扩缩容策略。请各位从各自专业角度分析当前ES集群的状态和扩缩容的最佳路径。

[Round 1] 上云架构师 (architect, signal=supplement): 从架构角度看，当前ES集群部署在us-east-1的三个可用区，采用i3en.2xlarge实例类型。单节点存储容量3.5TB，数据总量约20TB分布在6个数据节点上。扩缩容路径有两条：纵向(升配实例类型到i3en.4xlarge)和横向(增加数据节点)。纵向升配简单快速但单节点容量上限固定；横向扩容需要手动平衡分片迁移，可能导致热分片问题。

[Round 1] 运维操作员 (devops, signal=supplement): 从运维角度，当前ES集群在高峰期的CPU使用率达到85%，JVM heap压力超过75%，segment count在部分索引上达到2000+。扩缩容的运维操作风险包括：索引迁移期间的IO压力、节点下线时replica lag导致的数据一致性风险、以及变更窗口内的监控盲点。建议扩容前先执行dry-run脚本模拟，并建立回滚窗口。

[Round 1] 巡检监控员 (monitoring, signal=supplement): 监控数据显示，ES集群的_search和_bulk延迟在高峰期分别达到350ms和80ms，超过SLO阈值200ms和50ms。CloudWatch告警已经触发3次CPU高负载告警。扩容后的监控验证需要覆盖：node-level CPU/memory、index-level search rate、shard-level doc count分布。特别是跨可用区的流量成本增加需要单独监控。

[Round 1] 成本优化成员 (cost-optimizer, signal=supplement): 当前ES集群月度成本约为$8,400，其中EC2实例$5,200、EBS存储$2,100、数据传输$1,100。横向扩容到9节点月度成本将增至约$12,600；纵向升配到i3en.4xlarge(6节点)约$10,200。考虑RI/Savings Plan折扣(三年R15约30%off)，横向扩容实际增加约40%，纵向约25%。建议在模拟演练后选择成本最低且能满足未来12个月增长需求的方案。

[Round 2] 上云架构师 (architect, signal=supplement): 基于第一轮的事实盘点，我建议采用横向扩容+分片预分配策略。具体方案：扩容到9节点后，使用ilm policy将索引预先分配到新增节点，通过index.routing.allocation.require._name控制分片路由。同时将replica数调整为2（当前为1），确保至少2个副本。

[Round 2] 运维操作员 (devops, signal=challenge): 横向扩容存在三个风险需要讨论：第一，分片分配后再平衡会触发大量IO，可能导致搜索延迟飙升；第二，新增节点后旧节点不会自动卸载分片，需要主动执行reroute；第三，跨可用区数据同步在扩容期间的带宽压力。我们需要先在非生产环境演练。

[Round 2] 巡检监控员 (monitoring, signal=agree): 同意运维操作员的观点。建议在扩容前设置CloudWatch Dashboard专门监控：cpu_utilization > 70%触发告警、JVMMemoryPressure > 75%、ClusterStatus(Red/Yellow)实时告警。并配置OpenSearch的slow log记录扩容期间的慢查询，用于验收。

[Round 3] 运维 Leader (moderator, signal=supplement): 经过两轮讨论，共识方向是横向扩容+预分配策略。Build System团队将生成可审计可回滚的Terraform/运维脚本，AWS运维团队负责容量评估和变更执行。最大风险是扩容后索引迁移和热分片导致的性能抖动，因此所有动作必须有指标门禁和回滚窗口。本计划由系统生成并可派发任务进入数字孪生演练。

[Round 4] 成本优化成员 (cost-optimizer, signal=agree): 建议在当前方案的基础上，增加一个成本门禁：扩容后月度成本增幅不超过35%，且每季度review一次RI/Savings Plan的使用率，低于80%时触发成本报警。

[Round 4] 运维 Leader (moderator, signal=supplement): 五指表决结果：上云架构师5指(全力支持)、运维操作员4指(支持，有扩容IO顾虑)、巡检监控员4指(支持)、成本优化成员4指(支持)、Build System代表未到场(默认3指)。团队达成可执行共识。执行计划已生成，共6个任务按P0→P1→P2排序。讨论结束。
"""

    # Test 1: Sync stages 1-3 (no LLM needed)
    print("=" * 60)
    print("Test 1: TSE Stages 1-3 (no LLM) — extract_skill_moments")
    print("=" * 60)
    t0 = time.perf_counter()
    moments = extract_skill_moments(
        discussion_text,
        source_title="AWS ES 实例缩放运维脚本",
        source_meta={"plaza_id": "53a9a7d9cbb6", "discussion_id": "da033f90e526"},
    )
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"Total latency: {elapsed:.1f}ms")
    print(f"Utterances: {moments['utterance_count']}")
    print(f"Topic: {moments['topic']}")
    print(f"Focus indices (top skill moments): {moments['focus_indices']}")
    print(f"Timings: {json.dumps(moments['timings'], indent=2)}")
    print(f"Repr norms: {json.dumps(moments['skill_repr_norms'], indent=2)}")

    print("\n--- Field Focus Summary ---")
    for field, rows in moments.get("field_focus", {}).items():
        print(f"  {field}:")
        for r in rows[:2]:
            print(
                f"    #{r['index']} (w={r['weight']:.3f}) [{r['round']}] {r['speaker']}: {r['preview']}"
            )

    print(f"\n--- Focus transcript preview ---")
    print(moments["transcript_preview"][:1000])

    # Test 2: Full pipeline with decoder (needs LLM/harness)
    print("\n" + "=" * 60)
    print("Test 2: TSE Full Pipeline (with LLM decoder)")
    print("=" * 60)
    print("Note: Stage 4 requires ChatHarness/LLM. Testing encoder-only path.")
    print("Loading pipeline...")

    pipe = get_tse_pipeline()
    loaded = pipe.try_load_latest_checkpoint()
    print(f"Checkpoint loaded: {loaded}")

    if loaded:
        print(
            f"Checkpoint meta: epoch={pipe.checkpoint_meta.get('epoch', '?')} "
            f"train_loss={pipe.checkpoint_meta.get('train_loss', '?')} "
            f"val_cat_acc={pipe.checkpoint_meta.get('val_cat_acc', '?')}"
        )

    from tse.transcript import parse_transcript

    tr = parse_transcript(discussion_text, source_title="AWS ES 实例缩放运维脚本")

    t0 = time.perf_counter()
    stages = pipe.encode_stages(tr)
    elapsed = (time.perf_counter() - t0) * 1000

    print(f"\nStage 1-3 timing: {elapsed:.1f}ms")
    print(f"  Encoder: {stages['timings']['stage1_encoder_ms']:.1f}ms")
    print(f"  TCN: {stages['timings']['stage2_tcn_ms']:.1f}ms")
    print(f"  Attention: {stages['timings']['stage3_attention_ms']:.1f}ms")
    print(f"Focus indices: {stages['focus_indices']}")
    print(f"Attn shape: {stages['attn_weights'].shape}")
    print(f"Skill repr norms: {json.dumps(stages['skill_repr_norms'], indent=2)}")

    # Print attention heatmap summary
    attn = stages["attn_weights"]  # (5, N)
    fields = ["name", "description", "category", "tools", "instructions"]
    N = attn.shape[1]
    print(f"\nAttention weights (field × utterance):")
    print(f"  {'':>14s}", end="")
    for j in range(N):
        print(f"  u{j:2d}", end="")
    print()
    for qi, field in enumerate(fields):
        print(f"  {field:>14s}", end="")
        for j in range(N):
            print(f" {attn[qi, j]:4.2f}", end="")
        print()

    # Head predictions
    from tse.heads import MultiTaskHeads

    heads = MultiTaskHeads(
        hidden_dim=pipe.config.tcn_hidden_dim, seed=pipe.config.hash_seed + 3
    )
    try:
        head_pred = heads.predict(stages["skill_repr"])
        print(f"\nMulti-task head predictions:")
        print(f"  Category: {head_pred.get('category', '?')}")
        print(f"  Tools: {head_pred.get('required_tools', [])}")
    except Exception as e:
        print(f"Head prediction failed: {e}")

    return moments, stages, tr


moments, stages, tr = asyncio.run(test_extraction())
