# -*- coding: utf-8 -*-
"""Final extraction experiment on completed Plaza discussion."""

import asyncio, json, re, sys, time, os

os.chdir("/Users/panglaohu/Downloads/AgentsGroup2026/src/backend")
sys.path.insert(0, ".")

from agents.api import _harness_provider_credentials
from agents.chat_harness import get_chat_harness
from agents.tse import get_tse_pipeline
from agents.tse.transcript import parse_transcript
from agents.tse.decoder import synthesize_skills_local
from agents.tse.heads import MultiTaskHeads
from agents.tse.config import TSEConfig

DISC_TEXT = """Topic: AWS RDS MySQL慢查询优化方案

[Round 1] 上云架构师 (supplement): 从架构角度看，当前RDS MySQL 8.0实例部署在db.r6g.2xlarge上，CPU稳定在45-55%、内存使用率72%。慢查询主要来源：SELECT COUNT(*) FROM orders（全表扫描）、多表JOIN未正确使用索引、LIKE模糊查询无法使用索引。建议三种方案并行：方案A索引优化（复合索引、覆盖索引），方案B查询重写（分页优化、避免SELECT *），方案C读写分离（只读副本分担报表查询）。

[Round 1] 运维操作员 (supplement): Performance Insights显示Top 5慢查询占执行时间的42%。第1和第3条慢查询来自凌晨3点ETL作业，平均执行从2.1秒恶化到8.7秒。第2条是前端搜索全表LIKE扫描。添加索引风险：gh-ost Online DDL避免锁表但高峰IO增10-15%；索引占用存储：当前40GB索引，新增可能增15-20GB。

[Round 1] 巡检监控员 (supplement): CloudWatch数据显示：ReadIOPS高峰12,000/14,000上限，slow_query_log记录4,872条慢查询中4,112条(84%)来自固定8条SQL模式。数据库连接高峰期85/120。建议每个索引部署后24小时观察窗口。

[Round 1] 成本优化成员 (supplement): 当前RDS月$1,420。方案A(加索引)：存储+$8/月。方案B(查询重写)：开发24工时=$1,920一次性。方案C(读写分离+只读副本)：+$1,080/月。方案B+A ROI约13个月。

[Round 2] 上云架构师 (supplement): 推荐三阶段实施：(1)立即方案A——8条高频慢SQL加索引；(2)中期方案B——重写报表SQL；(3)方案C可选。优先级：P0=加索引(零风险快速见效)，P1=查询重写(需开发测试)，P2=读写分离。

[Round 2] 运维操作员 (challenge): 对方案A质疑：(1)gh-ost Online DDL高峰期仍增IO 10-15%影响现有慢查询；(2)复合索引设计不当浪费存储且不被优化器使用。建议先EXPLAIN每个目标查询确认索引可用性。

[Round 2] 巡检监控员 (agree): 同意。验收标准：目标慢查询恢复<3秒且全表扫描消除90%。每个索引部署间隔24小时观察。

[Round 4] 运维Leader: 五指表决——上云架构师5指(全力支持)，运维操作员4指，巡检监控员4指，成本优化成员4指。均值4.25指，无人1指，团队达成共识。
"""


async def main():
    api_key, base_url, model, provider = _harness_provider_credentials()
    print(f"Provider: {provider} | Model: {model} | Base: {base_url}")

    # TSE extraction
    print("\n=== TSE Extraction ===")
    config = TSEConfig()
    pipe = get_tse_pipeline(config)
    pipe.try_load_latest_checkpoint()

    tr = parse_transcript(DISC_TEXT, source_title="AWS RDS MySQL慢查询优化方案")
    t0 = time.perf_counter()
    stages = pipe.encode_stages(tr)
    tse_ms = (time.perf_counter() - t0) * 1000

    heads = MultiTaskHeads(hidden_dim=256, seed=20260716 + 3)
    try:
        head_pred = heads.predict(stages["skill_repr"])
    except:
        head_pred = {"category": "general", "required_tools": []}

    tse_skills = synthesize_skills_local(
        tr,
        focus_indices=stages["focus_indices"],
        category_hint=str(head_pred.get("category", "general")),
        tools_hint=list(head_pred.get("required_tools", [])),
    )

    print(
        f"TSE: {len(tse_skills)} skills in {tse_ms:.1f}ms | Focus: {stages['focus_indices']}"
    )
    for s in tse_skills:
        desc = s.get("description", "")[:100]
        print(f"  {s['name'][:50]}: {desc}")

    # LLM extraction
    print("\n=== LLM Extraction ===")
    harness = get_chat_harness()

    extract_system = 'Extract structured skills from discussion as JSON. Output: {"skills":[{"name":"...","description":"...","category":"...","instructions":"step by step","required_tools":["..."]}]}'

    extract_prompt = f"""Discussion: AWS RDS MySQL slow query optimization

{DISC_TEXT}

Extract ALL reusable operational skills from this discussion. Each skill must have specific actionable steps. Output ONLY valid JSON."""

    t0 = time.perf_counter()
    result = await harness.chat(
        prompt=extract_prompt,
        system_prompt=extract_system,
        agent_id="__test__",
    )
    llm_s = time.perf_counter() - t0

    raw = (
        getattr(result, "response", None)
        or getattr(result, "content", "")
        or str(result)
    )
    print(f"LLM: {llm_s:.1f}s | raw_len={len(raw)}")

    try:
        m = re.search(r"\{[\s\S]*\}", raw)
        parsed = json.loads(m.group(0) if m else raw)
        llm_skills = parsed.get("skills", parsed if isinstance(parsed, list) else [])
    except:
        llm_skills = []
        print(f"Parse failed: {raw[:200]}")

    print(f"LLM skills: {len(llm_skills)}")
    for s in llm_skills:
        desc = s.get("description", "")[:100]
        print(f"  {s.get('name', '?')[:50]}: {desc}")

    # Summary
    print(f"\n{'=' * 50}")
    print("RESULTS")
    print(f"{'=' * 50}")
    print(f"Plaza: 4-round ORID completed, 28 messages")
    print(f"TSE: {len(tse_skills)} skills in {tse_ms:.1f}ms")
    print(f"LLM: {len(llm_skills)} skills in {llm_s:.1f}s")
    print(f"Model: {model} @ {base_url}")

    os.makedirs("/Users/panglaohu/Downloads/AgentsGroup2026/data", exist_ok=True)
    with open(
        "/Users/panglaohu/Downloads/AgentsGroup2026/data/experiment_final.json", "w"
    ) as f:
        json.dump(
            {
                "tse_skills": tse_skills,
                "llm_skills": llm_skills,
                "latency": {"tse_ms": tse_ms, "llm_s": llm_s},
            },
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    print(f"\nSaved to data/experiment_final.json")


asyncio.run(main())
