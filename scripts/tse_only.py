# -*- coding: utf-8 -*-
"""TSE extraction only (no LLM needed)."""

import json, os, sys, time

os.chdir("/Users/panglaohu/Downloads/AgentsGroup2026/src/backend")
sys.path.insert(0, ".")

from agents.tse import get_tse_pipeline
from agents.tse.transcript import parse_transcript
from agents.tse.decoder import synthesize_skills_local
from agents.tse.heads import MultiTaskHeads
from agents.tse.config import TSEConfig

DISC = """Topic: AWS RDS MySQL慢查询优化方案

[Round 1] 上云架构师 (supplement): RDS MySQL 8.0 db.r6g.2xlarge, CPU 45-55%, 慢查询来源: SELECT COUNT(*)全表扫描, 多表JOIN缺索引, LIKE模糊查询。三种方案: A索引优化, B查询重写, C读写分离。

[Round 1] 运维操作员 (supplement): Top 5慢查询占42%执行时间, ETL从2.1秒恶化到8.7秒。加索引风险: gh-ost Online DDL避免锁表但高峰IO增10-15%, 索引额外15-20GB存储。

[Round 1] 巡检监控员 (supplement): ReadIOPS高峰12K/14K上限, 4872条慢查询中84%来自8条SQL。验收标准: 每个索引部署24h观察窗口, 慢查询恢复<3秒, 全表扫描消除90%。

[Round 1] 成本优化成员 (supplement): 月成本$1,420。方案A存储+$8/月, 方案B开发$1,920, 方案C只读副本+$1,080/月。方案B+A ROI 13个月。

[Round 2] 上云架构师 (supplement): 三阶段: P0加索引, P1查询重写, P2读写分离可选。

[Round 2] 运维操作员 (challenge): 质疑:(1)gh-ost高峰IO增10-15%, (2)复合索引设计不当浪费存储。建议先EXPLAIN验证。

[Round 2] 巡检监控员 (agree): 验收标准: 慢查询恢复<3秒, 全表扫描消除90%, 每索引24h观察。

[Round 4] 运维Leader: 五指表决: 架构师5指, 操作员4指, 监控员4指, 成本员4指。均值4.25指, 共识达成。
"""

config = TSEConfig()
pipe = get_tse_pipeline(config)
loaded = pipe.try_load_latest_checkpoint()
print(
    f"Checkpoint: {'loaded (epoch ' + str(pipe.checkpoint_meta.get('epoch', '?')) + ')' if loaded else 'cold start'}"
)

tr = parse_transcript(DISC, source_title="AWS RDS MySQL慢查询优化方案")
t0 = time.perf_counter()
stages = pipe.encode_stages(tr)
tse_ms = (time.perf_counter() - t0) * 1000

heads = MultiTaskHeads(hidden_dim=256, seed=20260716 + 3)
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

print(f"TSE: {len(skills)} skills in {tse_ms:.1f}ms | focus={stages['focus_indices']}")
for s in skills:
    print(f"  - {s['name'][:55]}")
    print(f"    desc: {s.get('description', '')[:100]}")
    print(f"    cat: {s.get('category', '')}")
    print(f"    tools: {s.get('required_tools', [])}")

os.makedirs("/Users/panglaohu/Downloads/AgentsGroup2026/data", exist_ok=True)
with open("/Users/panglaohu/Downloads/AgentsGroup2026/data/tse_results.json", "w") as f:
    json.dump(
        {"skills": skills, "latency_ms": tse_ms, "focus": stages["focus_indices"]},
        f,
        ensure_ascii=False,
        indent=2,
        default=str,
    )
print(f"\nSaved to data/tse_results.json")
