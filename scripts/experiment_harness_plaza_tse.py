# -*- coding: utf-8 -*-
"""Full experiment: Plaza ORID discussion → LLM extraction → TSE extraction.
Runs via backend ChatHarness (which has the configured LLM)."""

import asyncio, json, re, sys, time, os

os.chdir("/Users/panglaohu/Downloads/AgentsGroup2026/src/backend")
sys.path.insert(0, ".")

from agents.api import _harness_provider_credentials
from agents.chat_harness import get_chat_harness
from agents.tse import get_tse_pipeline, extract_skill_moments
from agents.tse.transcript import parse_transcript
from agents.tse.decoder import synthesize_skills_local
from agents.tse.heads import MultiTaskHeads


async def call_harness_llm(prompt: str, system: str = "") -> str:
    harness = get_chat_harness()
    result = await harness.chat(
        prompt=prompt,
        system_prompt=system,
        agent_id="experiment_runner",
    )
    if hasattr(result, "response"):
        return result.response
    elif hasattr(result, "content"):
        return result.content
    return str(result)


async def run_plaza_orid(topic: str, description: str, goal: str) -> dict:
    """Run ORID Plaza discussion."""
    speakers = [
        {
            "name": "运维Leader",
            "role": "moderator/Facilitator",
            "expertise": "协调、任务派发、风险升级",
        },
        {
            "name": "上云架构师",
            "role": "architect",
            "expertise": "AWS资源规划、容量建模、架构设计",
        },
        {
            "name": "运维操作员",
            "role": "devops",
            "expertise": "运维执行、变更管理、故障处理",
        },
        {
            "name": "巡检监控员",
            "role": "monitoring",
            "expertise": "监控告警、性能分析、验收验证",
        },
        {
            "name": "成本优化成员",
            "role": "cost-optimizer",
            "expertise": "成本分析、RI/Savings Plan、预算控制",
        },
    ]

    orid_system = f"""你是议事长 (Facilitator)，主持ORID四层讨论。过程要自然、专业。
规则: ①每层严格推进 ②不引导内容只控流程 ③每个参与者以【名字】开头发言 ④发言要实质不要空话 ⑤Round信息标注[Round N]"""

    orid_prompt = f"""讨论话题: {topic}
讨论目标: {goal}
描述: {description}
参与者: {", ".join(s["name"] for s in speakers)}
请按ORID四层结构主持: ①客观事实(O) ②风险直觉(R) ③方案对立辩论(I) ④五指决策(D)"""

    print(f"\n{'=' * 60}")
    print(f"[Plaza] {topic}")
    t0 = time.perf_counter()
    text = await call_harness_llm(orid_prompt, system=orid_system)
    elapsed = time.perf_counter() - t0
    print(f"[Plaza] Done in {elapsed:.1f}s, {len(text)} chars")
    return {"topic": topic, "text": text, "latency_s": elapsed}


async def extract_skills_llm(disc: dict) -> dict:
    """LLM-based skill extraction."""
    extract_system = """萃取讨论中可复用的结构化技能(纯JSON输出)。格式: {"skills":[{"name":"...","description":"...","category":"...","instructions":"步骤列表","required_tools":["..."]}]}"""
    prompt = f"讨论话题: {disc['topic']}\n{disc['text']}\n\n从以上提取技能(JSON):"

    t0 = time.perf_counter()
    raw = await call_harness_llm(prompt, system=extract_system)
    elapsed = time.perf_counter() - t0

    try:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
        parsed = json.loads(m.group(1) if m else raw)
        skills = parsed.get("skills", parsed if isinstance(parsed, list) else [])
    except:
        skills = []
        print(f"[LLM extract] Parse failed: {raw[:100]}")

    print(f"[LLM extract] {len(skills)} skills in {elapsed:.1f}s")
    for s in skills:
        print(f"  - {s.get('name', '?'):40s} [{s.get('category', '?')}]")
    return {"skills": skills, "latency_s": elapsed}


def run_tse_extraction(disc: dict) -> dict:
    """TSE pipeline extraction."""
    from agents.tse.config import TSEConfig

    pipe = get_tse_pipeline(TSEConfig())
    pipe.try_load_latest_checkpoint()

    tr = parse_transcript(disc["text"], source_title=disc["topic"])
    t0 = time.perf_counter()
    stages = pipe.encode_stages(tr)
    tse_time = (time.perf_counter() - t0) * 1000

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

    print(f"[TSE] {len(skills)} skills in {tse_time:.1f}ms")
    for s in skills:
        print(f"  - {s.get('name', '?')[:40]} [{s.get('category', '?')}]")

    # Get the skill moments for telemetry
    moments = extract_skill_moments(disc["text"], source_title=disc["topic"])
    return {
        "skills": skills,
        "latency_ms": tse_time,
        "focus_indices": stages["focus_indices"],
    }


async def main():
    # Check LLM is available
    api_key, base_url, model, provider = _harness_provider_credentials()
    print(f"LLM provider: {provider}, model: {model}, base: {base_url}")
    if not api_key:
        print("ERROR: No API key configured in ChatHarness. Exiting.")
        return

    # ── Experiment 1: RDS MySQL ──
    d1 = await run_plaza_orid(
        "AWS RDS MySQL慢查询优化方案",
        "RDS MySQL生产环境慢查询: 分析slow_log、识别高频慢SQL模式、评估索引优化vs查询重写vs读写分离",
        "产出3步慢查询优化执行计划",
    )
    e1_llm = await extract_skills_llm(d1)
    e1_tse = run_tse_extraction(d1)

    # ── Experiment 2: S3 Lifecycle ──
    d2 = await run_plaza_orid(
        "AWS S3存储生命周期策略优化",
        "S3 bucket数据量快速增长，需设计分层存储策略(Standard→IA→Glacier→Deep Archive)和自动清理规则",
        "产出S3生命周期配置方案，目标月度成本降低30%",
    )
    e2_llm = await extract_skills_llm(d2)
    e2_tse = run_tse_extraction(d2)

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 60}")
    print(f"Discussions: 2")
    print(f"Total Plaza time: {d1['latency_s'] + d2['latency_s']:.1f}s")
    print(f"")
    print(f"LLM Extraction:")
    print(f"  RDS MySQL: {len(e1_llm['skills'])} skills ({e1_llm['latency_s']:.1f}s)")
    print(
        f"  S3 Lifecycle: {len(e2_llm['skills'])} skills ({e2_llm['latency_s']:.1f}s)"
    )
    print(f"  Total: {len(e1_llm['skills']) + len(e2_llm['skills'])} skills")
    print(f"")
    print(f"TSE Extraction:")
    print(f"  RDS MySQL: {len(e1_tse['skills'])} skills ({e1_tse['latency_ms']:.1f}ms)")
    print(
        f"  S3 Lifecycle: {len(e2_tse['skills'])} skills ({e2_tse['latency_ms']:.1f}ms)"
    )
    print(f"  Total: {len(e1_tse['skills']) + len(e2_tse['skills'])} skills")

    # Save
    results = {
        "discussions": [
            {
                "topic": d1["topic"],
                "latency_s": d1["latency_s"],
                "chars": len(d1["text"]),
            },
            {
                "topic": d2["topic"],
                "latency_s": d2["latency_s"],
                "chars": len(d2["text"]),
            },
        ],
        "llm_extraction": [
            {
                "topic": d1["topic"],
                "skills": e1_llm["skills"],
                "latency_s": e1_llm["latency_s"],
            },
            {
                "topic": d2["topic"],
                "skills": e2_llm["skills"],
                "latency_s": e2_llm["latency_s"],
            },
        ],
        "tse_extraction": [
            {
                "topic": d1["topic"],
                "skills": e1_tse["skills"],
                "latency_ms": e1_tse["latency_ms"],
                "focus": e1_tse["focus_indices"],
            },
            {
                "topic": d2["topic"],
                "skills": e2_tse["skills"],
                "latency_ms": e2_tse["latency_ms"],
                "focus": e2_tse["focus_indices"],
            },
        ],
    }
    with open(
        "/Users/panglaohu/Downloads/AgentsGroup2026/data/experiment_plaza_llm_tse.json",
        "w",
    ) as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nResults → data/experiment_plaza_llm_tse.json")
    return results


asyncio.run(main())
