# -*- coding: utf-8 -*-
"""Run Plaza-style ORID discussion + TSE extraction using real LLM."""

import asyncio, os, json, time
import sys

sys.path.insert(0, "/Users/panglaohu/Downloads/AgentsGroup2026/src/backend/agents")

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_KEY:
    print("ERROR: No DeepSeek key. Set DEEPSEEK_API_KEY.")
    sys.exit(1)

import httpx

# Use SJTU GLM-5.1 endpoint as configured by user
API_BASE = "https://models.sjtu.edu.cn/api/v1"
MODEL = "glm-5.1"


async def call_llm(prompt: str, system: str = "", model: str = MODEL) -> str:
    """Call SJTU GLM-5.1 API."""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{API_BASE}/chat/completions",
            json={"model": model, "messages": messages, "temperature": 0.3},
            headers=headers,
        )
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def run_plaza_orid(topic: str, description: str, goal: str) -> dict:
    """Run a full ORID Plaza discussion using real LLM for each speaker."""

    speakers = [
        {
            "name": "运维Leader",
            "role": "moderator/Facilitator",
            "expertise": "整体协调、任务派发、风险升级",
            "team": "AWS运维",
        },
        {
            "name": "上云架构师",
            "role": "architect",
            "expertise": "AWS资源规划、容量建模、架构设计",
            "team": "AWS运维",
        },
        {
            "name": "运维操作员",
            "role": "devops",
            "expertise": "运维执行、变更管理、故障处理",
            "team": "AWS运维",
        },
        {
            "name": "巡检监控员",
            "role": "monitoring",
            "expertise": "监控告警、性能分析、验收验证",
            "team": "AWS运维",
        },
        {
            "name": "成本优化成员",
            "role": "cost-optimizer",
            "expertise": "成本分析、RI/Savings Plan、预算控制",
            "team": "AWS运维",
        },
    ]

    orid_system = """你是议事长 (Facilitator)。你主持一场采用 ORID 四层结构的团队讨论：
①客观事实(O) — 每个参与者陈述已知事实，禁止解释和判断
②风险直觉(R) — 每个参与者表达直觉担忧，感受无需证据
③方案对立辩论(I) — 两位主要方案代表进行3轮针锋相对辩论
④五指决策(D) — 全体用五指量表表态，1指=根本性反对，5指=全力支持

规则：
- 每层严格5分钟时间盒
- 不引导内容，只控制流程
- 发言要像项目经理主持真实会议"""

    orid_user_prompt = f"""讨论话题: {topic}
话题描述: {description}
讨论目标: {goal}

参与者: {", ".join(s["name"] for s in speakers)}

请以议事长身份按照ORID四层结构推进讨论。每层结束后明确标注进入下一层。格式要求：每个参与者发言以【名字】开头。请开始。"""

    print(f"\n{'=' * 60}")
    print(f"Topic: {topic}")
    print(f"{'=' * 60}")

    t0 = time.perf_counter()
    discussion_text = await call_llm(orid_user_prompt, system=orid_system)
    elapsed = time.perf_counter() - t0

    print(f"Discussion complete ({elapsed:.1f}s)")
    print(f"Length: {len(discussion_text)} chars")
    print(f"\n--- Discussion Transcript ---\n{discussion_text[:1500]}...\n")

    return {
        "topic": topic,
        "description": description,
        "goal": goal,
        "text": discussion_text,
        "latency_s": elapsed,
        "model": "gpt-4o-mini",
    }


async def extract_skills(discussion: dict) -> dict:
    """Extract skills from discussion using LLM."""
    extract_system = """你是技能萃取专家。从多智能体讨论记录中提炼结构化技能。

一条可复用的技能必须包含：
- name: 简短技能名称(50字以内)
- description: 这个技能解决什么问题(1-3句话)
- category: automation/research/analysis/monitoring/general
- instructions: 分步骤的可执行操作指令(3-8步)
- required_tools: 所需工具列表

规则：
1. 只萃取讨论中明确出现或被充分讨论的技能
2. 不发明"communication"、"teamwork"等通用软技能
3. 操作指令必须能让一个技术人员直接执行

输出严格JSON格式：{"skills": [...]}"""

    prompt = f"""讨论话题: {discussion["topic"]}
讨论目标: {discussion["goal"]}

完整讨论记录:
{discussion["text"]}

请从以上讨论中萃取所有可发现的技能。"""

    t0 = time.perf_counter()
    result = await call_llm(prompt, system=extract_system)
    elapsed = time.perf_counter() - t0
    print(f"Extraction complete ({elapsed:.1f}s)")

    # Parse JSON
    try:
        import re

        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", result)
        json_str = match.group(1) if match else result
        parsed = json.loads(json_str)
        skills = parsed.get("skills", parsed if isinstance(parsed, list) else [])
    except Exception as e:
        print(f"Parse error: {e}, raw: {result[:200]}")
        skills = []

    print(f"Skills extracted: {len(skills)}")
    for s in skills:
        print(f"  - {s.get('name', '?')}: {s.get('description', '?')[:80]}")

    return {"raw": result, "skills": skills, "latency_s": elapsed}


async def run_tse_extraction(discussion: dict) -> dict:
    """Run TSE pipeline on the real discussion transcript."""
    from tse import get_tse_pipeline
    from tse.transcript import parse_transcript
    from tse.decoder import synthesize_skills_local
    from tse.heads import MultiTaskHeads
    from tse.config import TSEConfig

    print(f"\n--- TSE Pipeline Extraction ---")
    config = TSEConfig()
    pipe = get_tse_pipeline(config)
    pipe.try_load_latest_checkpoint()

    tr = parse_transcript(
        discussion["text"],
        source_title=discussion["topic"],
        source_meta={"plaza_id": "53a9a7d9cbb6"},
    )

    t0 = time.perf_counter()
    stages = pipe.encode_stages(tr)
    tse_time = (time.perf_counter() - t0) * 1000

    heads = MultiTaskHeads(hidden_dim=config.tcn_hidden_dim, seed=config.hash_seed + 3)
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

    print(f"TSE latency: {tse_time:.1f}ms")
    print(f"Focus indices: {stages['focus_indices']}")
    print(f"TSE skills: {len(skills)}")
    for s in skills:
        print(f"  - {s.get('name', '?')} [{s.get('category', '?')}]")

    return {"tse_skills": skills, "latency_ms": tse_time, "stages": stages}


async def main():
    # ── Discussion 1: RDS MySQL ──
    disc1 = await run_plaza_orid(
        topic="AWS RDS MySQL 慢查询优化方案",
        description="RDS MySQL在生产环境慢查询频率上升，需要系统分析slow_log、识别高频慢SQL模式，评估索引优化、查询重写和读写分离三种方案",
        goal="产出一个3步慢查询优化执行计划，含监控验证指标",
    )
    ext1 = await extract_skills(disc1)
    tse1 = await run_tse_extraction(disc1)

    # ── Discussion 2: S3生命周期管理 ──
    disc2 = await run_plaza_orid(
        topic="AWS S3 存储生命周期策略优化",
        description="当前S3 bucket存储量快速增长，需设计分层存储策略(Standard→IA→Glacier)和自动清理策略来降低成本",
        goal="产出S3生命周期策略配置方案，预期月度成本降低30%",
    )
    ext2 = await extract_skills(disc2)
    tse2 = await run_tse_extraction(disc2)

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print("Experiment Summary")
    print(f"{'=' * 60}")
    print(f"Total discussions: 2")
    print(
        f"LLM extraction skills: {len(ext1['skills'])} + {len(ext2['skills'])} = {len(ext1['skills']) + len(ext2['skills'])}"
    )
    print(
        f"TSE local skills: {len(tse1['tse_skills'])} + {len(tse2['tse_skills'])} = {len(tse1['tse_skills']) + len(tse2['tse_skills'])}"
    )
    print(
        f"Total Plaza latency: {disc1['latency_s']:.1f}s + {disc2['latency_s']:.1f}s = {disc1['latency_s'] + disc2['latency_s']:.1f}s"
    )
    print(
        f"Total LLM extract latency: {ext1['latency_s']:.1f}s + {ext2['latency_s']:.1f}s"
    )

    # Save results
    results = {
        "discussion1": {k: v for k, v in disc1.items() if k != "text"},
        "discussion2": {k: v for k, v in disc2.items() if k != "text"},
        "extraction1": ext1,
        "extraction2": ext2,
        "tse1": {k: str(v)[:200] for k, v in tse1.items() if k != "stages"},
        "tse2": {k: str(v)[:200] for k, v in tse2.items() if k != "stages"},
    }
    with open(
        "/Users/panglaohu/Downloads/AgentsGroup2026/data/experiment_results.json", "w"
    ) as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nResults saved to data/experiment_results.json")


asyncio.run(main())
