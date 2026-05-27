# -*- coding: utf-8 -*-
"""LLM 驱动的 Agent Twin 决策引擎.

将 Qwen API 接入沙箱仿真，让 Agent Twin 用真实 LLM 推理代替规则引擎。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .models import AgentTwin, WorldStateSnapshot

logger = logging.getLogger("sandbox.llm_decision")

# ── 系统提示词模板 ──────────────────────────────────────────────

DECISION_SYSTEM_PROMPT = """你是一个智能体仿真系统中的 Agent Twin，在协同沙箱中做决策。

## 你的身份
- 角色: {role}
- 技能: {skills}
- 当前状态: {state}
- 当前任务: {current_task}

## 世界状态
- 待处理任务: {pending_tasks}
- 其他智能体: {other_agents}
- 资源: {resources}
- 约束: {constraints}

## 决策要求
根据当前世界状态，选择最优行动。你的目标是:
1. 高效完成任务
2. 与其他智能体协作
3. 避免资源冲突
4. 尽快收敛到全局最优

## 输出格式 (严格 JSON)
{{
  "action": "claim_task|work_on_task|offer_help|delegate|idle|communicate",
  "task": "task_id 或 null",
  "next_state": "working|waiting|idle|communicating",
  "message": "要广播的消息或 null",
  "target": "目标智能体 ID 或 broadcast 或 null",
  "reasoning": "简短决策理由"
}}"""


async def llm_decision(
    twin: AgentTwin,
    world: WorldStateSnapshot,
    all_twins: List[AgentTwin],
    chat_harness=None,
) -> Dict[str, Any]:
    """使用 LLM 为 Agent Twin 生成决策.

    Args:
        twin: 当前决策的智能体副本
        world: 世界状态快照
        all_twins: 所有智能体副本
        chat_harness: LLM 调用接口 (可选，自动获取)

    Returns:
        决策字典 {action, task, next_state, message, target, reasoning}
    """
    if chat_harness is None:
        try:
            from agents.chat_harness import get_chat_harness
            chat_harness = get_chat_harness()
        except Exception as e:
            logger.warning("无法获取 chat_harness，回退到规则引擎: %s", e)
            return _fallback_decision(twin, world, all_twins)

    # 构建提示词上下文
    other_agents_desc = [
        f"{t.twin_id}({t.role}, state={t.state}, task={t.current_task})"
        for t in all_twins if t.twin_id != twin.twin_id
    ]

    pending_desc = [
        f"{t.get('id','?')}:{t.get('title','?')}(roles={t.get('required_roles',[])})"
        for t in world.pending_tasks[:5]  # 限制上下文长度
    ]

    system = DECISION_SYSTEM_PROMPT.format(
        role=twin.role,
        skills=", ".join(twin.skills) if twin.skills else "通用",
        state=twin.state,
        current_task=twin.current_task or "无",
        pending_tasks="; ".join(pending_desc) if pending_desc else "无",
        other_agents="; ".join(other_agents_desc) if other_agents_desc else "无",
        resources=f"{len(world.resources)} 项资源" if world.resources else "无",
        constraints=f"{len(world.constraints)} 项约束" if world.constraints else "无",
    )

    prompt = f"当前是仿真第 {world.snapshot_count + 1} 步，请做出你的决策。"

    try:
        result = await chat_harness.chat(
            prompt=prompt,
            system_prompt=system,
            agent_id=f"twin_{twin.twin_id}",
        )

        if result and getattr(result, "response", None):
            decision = _parse_decision(result.response)
            if decision:
                logger.debug("LLM 决策 [%s]: %s", twin.twin_id, decision.get("action"))
                return decision

    except Exception as e:
        logger.warning("LLM 决策失败 [%s]: %s", twin.twin_id, e)

    # 回退到规则引擎
    return _fallback_decision(twin, world, all_twins)


def _parse_decision(response: str) -> Optional[Dict[str, Any]]:
    """从 LLM 响应中解析 JSON 决策."""
    # 尝试提取 JSON 块
    text = response.strip()

    # 尝试从 markdown 代码块中提取
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    # 尝试找 JSON 对象
    if "{" in text:
        start = text.index("{")
        end = text.rindex("}") + 1
        text = text[start:end]

    try:
        data = json.loads(text)
        # 验证必需字段
        if "action" not in data:
            return None
        # 规范化
        return {
            "action": data.get("action", "idle"),
            "task": data.get("task"),
            "next_state": data.get("next_state", "idle"),
            "message": data.get("message"),
            "target": data.get("target"),
            "reasoning": data.get("reasoning", ""),
        }
    except (json.JSONDecodeError, ValueError):
        return None


def _fallback_decision(
    twin: AgentTwin,
    world: WorldStateSnapshot,
    all_twins: List[AgentTwin],
) -> Dict[str, Any]:
    """规则引擎回退决策 (与原 _default_decision 相同逻辑)."""
    if twin.current_task:
        return {
            "action": "work_on_task",
            "task": twin.current_task,
            "next_state": "working",
            "message": None,
        }

    available_tasks = [
        t for t in world.pending_tasks
        if t.get("assigned_to") is None and twin.role in t.get("required_roles", [twin.role])
    ]

    if available_tasks:
        task = available_tasks[0]
        return {
            "action": "claim_task",
            "task": task.get("id", "unknown"),
            "next_state": "working",
            "message": f"认领任务: {task.get('title', 'unknown')}",
            "message_type": "claim",
            "target": "broadcast",
        }

    busy_twins = [t for t in all_twins if t.state == "working" and t.twin_id != twin.twin_id]
    if busy_twins:
        return {
            "action": "offer_help",
            "next_state": "waiting",
            "message": f"可协助: {busy_twins[0].role}",
            "target": busy_twins[0].twin_id,
        }

    return {"action": "idle", "next_state": "idle", "message": None}
