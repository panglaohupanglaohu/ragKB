# -*- coding: utf-8 -*-
"""Eco Runtime Config REST API — 仿生生态运行时可配置参数管理.

GET   /api/v1/eco-runtime/config     — 获取全量配置（默认补全后）
GET   /api/v1/eco-runtime/defaults   — 获取内置默认（供"恢复默认"）
PUT   /api/v1/eco-runtime/config     — 部分更新（只覆盖已知 section/键）
POST  /api/v1/eco-runtime/reset      — 恢复全部默认
POST  /api/v1/eco-runtime/analyze    — LLM 分析锦标赛/演练结果，给出洞察
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from .runtime.eco_runtime_config import get_eco_runtime_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/eco-runtime", tags=["eco-runtime"])


class EcoRuntimeUpdateRequest(BaseModel):
    """部分更新请求：{section: {key: value}}，未知 section/键会被后端忽略。"""
    model_config = {"extra": "allow"}
    mental_state: Dict[str, Any] = {}
    metabolism: Dict[str, Any] = {}
    learning: Dict[str, Any] = {}
    selection: Dict[str, Any] = {}
    mating: Dict[str, Any] = {}


@router.get("/config", summary="获取仿生生态运行时全量参数")
def get_config() -> Dict[str, Any]:
    return get_eco_runtime_config().get_config()


@router.get("/defaults", summary="获取内置默认参数")
def get_defaults() -> Dict[str, Any]:
    return get_eco_runtime_config().get_defaults()


@router.put("/config", summary="部分更新仿生生态运行时参数")
def update_config(req: EcoRuntimeUpdateRequest) -> Dict[str, Any]:
    updates = {k: v for k, v in req.model_dump(exclude_none=True).items() if v}
    return get_eco_runtime_config().update(updates)


@router.post("/reset", summary="恢复全部默认参数")
def reset_config() -> Dict[str, Any]:
    return get_eco_runtime_config().reset()


class EcoAnalysisRequest(BaseModel):
    """锦标赛/演练结果分析请求。"""
    entries: List[Dict[str, Any]] = []     # 锦标赛各队摘要
    env: Dict[str, Any] = {}               # 环境参数
    single_result: Dict[str, Any] = {}     # 单场演练完整结果（非锦标赛时用）


@router.post("/analyze", summary="LLM 分析演练结果，给出洞察型报告")
async def analyze_drill(req: EcoAnalysisRequest) -> Dict[str, Any]:
    """用 LLM 分析物竞天择演练结果，给出有洞察力的分析报告。"""
    import json

    # 构建数据摘要（控制 token 量）
    if req.entries:
        summary = "锦标赛结果：\n"
        for i, e in enumerate(req.entries):
            champ = e.get("champ", {})
            summary += (
                f"  第{i+1}名 {e.get('name','?')}：平均生存 {e.get('avg',0)}t，"
                f"最长 {e.get('best',0)}t，存活 {e.get('alive',0)}/{e.get('total',0)}，"
                f"世代 {e.get('gens',0)}，黄金适者 {champ.get('agent_id','?')}({champ.get('survival_ticks',0)}t)\n"
            )
            cg = champ.get("collab_genome", {})
            if cg:
                summary += f"    协作基因：分享{cg.get('share_tendency','?')} 信号{cg.get('signal_tendency','?')} 跟随{cg.get('follow_tendency','?')}\n"
            sg = champ.get("skill_genome", [])
            if sg:
                summary += f"    技能基因：{', '.join(sg[:5])}\n"
    else:
        r = req.single_result
        gens = r.get("generations", [])
        ranking = (r.get("final_ranking") or [])[:5]
        summary = f"单场演练：{len(gens)}代，最长生存{r.get('best_survival_ticks',0)}t\n"
        for g in gens:
            summary += f"  G{g.get('generation')}: 存活{g.get('living',0)} 最长{g.get('best_survival_ticks',0)}t 平均{g.get('avg_survival_ticks',0)}t 新生{g.get('births',0)}\n"
        summary += "排行榜：\n"
        for x in ranking:
            summary += f"  {x.get('agent_id','?')}({x.get('population','?')}) {x.get('survival_ticks',0)}t {'存活' if x.get('alive') else '淘汰'}\n"

    env = req.env or {}
    summary += f"\n环境：生态位{env.get('demanded_skills',['?'])[:4]} 丰饶{env.get('abundance','?')} 捕食{env.get('predator_pressure','?')} 漂移{env.get('drift_prob','?')} 名额{env.get('niche_capacity','?')}\n"

    prompt = (
        "你是数字孪生实验室的首席进化分析师。分析以下物竞天择演练结果，给出**洞察型报告**。\n"
        "不要复述数据——数据用户已经看到了。要给出数据背后的**为什么**：\n"
        "1. 为什么冠军赢了？（基因/技能/协作策略的因果分析，不要说「因为活得久」）\n"
        "2. 关键转折点在哪一代？环境漂移或棘轮推进如何改变了格局？\n"
        "3. 哪些技能被环境淘汰了？为什么它们在这个生态位是负担？\n"
        "4. 协作基因（分享/信号/跟随）的自然选择方向说明了什么？\n"
        "5. 如果是锦标赛：两个种群的基因差异如何导致了不同的命运？\n"
        "6. 一句话总结：这个环境在选择什么样的团队？\n\n"
        "用中文，简洁有力，不要罗列数据，直接给洞察。最多 300 字。\n\n"
        + summary
    )

    try:
        from .chat_harness import get_chat_harness
        harness = get_chat_harness()
        result = await asyncio.wait_for(harness.chat(prompt), timeout=60.0)
        # harness.chat() 返回结果对象，不是字符串——用 .response 取文本
        text = ""
        if hasattr(result, 'response'):
            text = (result.response or "").strip()
        elif isinstance(result, str):
            text = result.strip()
        # 检测降级文案
        if hasattr(result, 'error') and result.error:
            return {"analysis": f"（LLM 错误：{result.error}）", "ok": False}
        if text and "LLM 未连接" not in text and "收到您的消息" not in text:
            return {"analysis": text, "ok": True}
        return {"analysis": "（LLM 未连接——请在设置页配置 LLM API Key 后重试）", "ok": False}
    except asyncio.TimeoutError:
        return {"analysis": "（LLM 分析超时 60s——以下为数据摘要）\n\n" + summary, "ok": False}
    except Exception as e:
        logger.warning("eco analyze failed: %s", e)
        return {"analysis": f"（LLM 分析失败：{e}）", "ok": False}
